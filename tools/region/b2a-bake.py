# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 법정동 → 행정동 매핑(전국 확장 설계서 2장 구현 규칙 · Phase 1)
#   실거래·건축물대장은 법정동(예: 방배동)으로만 온다 → 행정동(방배1~4동)으로 보려면 지번 좌표가 제일 좋고(rtms-bake 가 그렇게 한다),
#   좌표가 없을 때(일반건물 지번 가림 등) 이 표로 「넓이 비율」 근사를 쓴다 — 근사라고 밝힌다
#   법정동 경계 = 브이월드 데이터 API LT_C_ADEMD_INFO(국토교통부 · 키 기기마다 아님: 굽는 PC 의 keys.json "vworld") · 행정동 경계 = SGIS/admdongkor hjd 2026-07
#   py -3.12 -X utf8 tools/region/b2a-bake.py → 07_API키/out/b2a/<구>.json(원자료) · data/b2a.json
import json, os, sys, time, urllib.request, urllib.parse, importlib.util
from shapely.geometry import shape
from shapely.ops import transform as stf
from shapely.strtree import STRtree
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'b2a')
to5179 = Transformer.from_crs('EPSG:4326', 'EPSG:5179', always_xy=True).transform

def fetch(gu, box, key):
    fn = os.path.join(OUT, gu + '.json')
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    feats = []; page = 1
    while True:
        q = {'service': 'data', 'request': 'GetFeature', 'data': 'LT_C_ADEMD_INFO', 'key': key, 'domain': '340patrolman.github.io', 'attrFilter': 'emd_cd:LIKE:' + gu,
             'size': '1000', 'page': str(page), 'format': 'json', 'geometry': 'true', 'geomFilter': 'BOX(%f,%f,%f,%f)' % (box[0] - 0.02, box[1] - 0.02, box[2] + 0.02, box[3] + 0.02), 'crs': 'EPSG:4326'}
        r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/data?' + urllib.parse.urlencode(q), headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read().decode('utf-8'))['response']
        if r.get('status') == 'NOT_FOUND': break
        if r.get('status') != 'OK': raise RuntimeError('%s %s' % (gu, r))
        feats += r['result']['featureCollection']['features']
        if int(r['record']['current']) < 1000 or page * 1000 >= int(r['record']['total']): break
        page += 1
    os.makedirs(OUT, exist_ok=True); json.dump(feats, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); time.sleep(0.3); return feats

def main():
    key = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    hf, _ = DB.seoul_gus(); H = [(f['properties']['adm_cd2'][:8], f['properties']['adm_nm'].split(' ')[-1], stf(to5179, shape(f['geometry']))) for f in hf]
    tree = STRtree([h[2] for h in H]); IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    T = {}; nb = 0
    for g in IX['gus']:
        fs = fetch(g['gu'], g['box'], key); print(g['gu'], g['name'], len(fs), flush=True)
        for f in fs:
            pr = f['properties']; b = stf(to5179, shape(f['geometry'])).buffer(0); A = b.area or 1; parts = []
            for i in tree.query(b):
                a = H[i][2].intersection(b).area
                if a / A >= 0.02: parts.append([H[i][0], H[i][1], round(a / A * 100, 1)])
            parts.sort(key=lambda p: -p[2]); T[pr['emd_cd']] = {'n': pr['emd_kor_nm'], 'gu': g['gu'], 'a': parts}; nb += 1
    doc = {'schema': 'tg-b2a/1', 'source': '법정동 경계 = 국토교통부 브이월드 LT_C_ADEMD_INFO(%s 받음) · 행정동 경계 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0)' % time.strftime('%Y-%m-%d'),
           'fields': '{법정동 8자리: {n 이름, gu 구, a: [[행정동 8자리, 이름, 그 법정동 넓이 중 %], …(넓은 순 · 2% 미만은 두 경계 자료의 어긋남으로 보고 버림)]}}',
           'note': '넓이 비율은 근사다 — 실거래처럼 지번이 있으면 지번 좌표로 판정하는 것이 맞다(이 표는 좌표가 없을 때만)', 'b2a': T}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'b2a.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    one = sum(1 for v in T.values() if v['a'] and v['a'][0][2] >= 95)
    print('법정동', nb, '한 행정동에 95%↑ 든 법정동', one, '여러 동에 나뉜 법정동', nb - one, 'bytes', os.path.getsize(os.path.join(ROOT, 'data', 'b2a.json')))

if __name__ == '__main__': main()
