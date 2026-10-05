# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.13.0 — 🚙 서울 교통량 조사 지점 전부(서울시 교통량조사 SpotInfo · VolInfo · 서울 열린데이터광장 · 공공누리 1유형)
#   ⚠ 이 두 서비스는 xml 만 된다(json 이면 ERROR-301) · 지점 좌표 = GRS80 중부원점(EPSG:5181) → WGS84
#   날 = 생활인구 250m 와 같은 주: 평일 2026-09-08(화)·09(수) 평균 · 토 09-12 · 일 09-13(추석 2주 전)
#   시간마다 [방향1, 방향2] 대수(차로 합) · 키 = 07_API키/keys.json "seoul"(결과에 키 없음)
#   py -3.12 -X utf8 tools/region/vol-bake.py fetch → 07_API키/out/vol/ · build → data/traffic-vol-seoul.json
import json, os, sys, time, urllib.request, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'vol'); os.makedirs(OUT, exist_ok=True)
DAYS = {'wd': ['20260908', '20260909'], 'sa': ['20260912'], 'su': ['20260913']}

def X(path):
    sk = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['seoul'].strip()
    for i in range(4):
        try: return ET.fromstring(urllib.request.urlopen('http://openapi.seoul.go.kr:8088/%s/xml/%s' % (sk, path), timeout=40).read())
        except Exception: time.sleep(2 + i * 3)
    return None

def fetch():
    sp = X('SpotInfo/1/1000/'); spots = [{c.tag: c.text for c in r} for r in sp.findall('row')]
    json.dump(spots, open(os.path.join(OUT, 'spots.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    jobs = [(s['spot_num'], d, '%02d' % h) for s in spots for ds in DAYS.values() for d in ds for h in range(24)]
    def one(j):
        fn = os.path.join(OUT, '%s_%s_%s.json' % j)
        if os.path.exists(fn): return
        r = X('VolInfo/1/100/%s/%s/%s/' % j)
        if r is None: return
        code = r.findtext('RESULT/CODE') or ''
        rows = [{c.tag: c.text for c in x} for x in r.findall('row')]
        if rows or code.startswith('INFO-200'): json.dump(rows, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
    with ThreadPoolExecutor(6) as ex:
        for i, _ in enumerate(ex.map(one, jobs)):
            if i % 1000 == 0: print('받음', i, '/', len(jobs), flush=True)
    print('지점', len(spots), '요청', len(jobs))

def build():
    spots = json.load(open(os.path.join(OUT, 'spots.json'), encoding='utf-8'))
    tr = Transformer.from_crs('EPSG:5181', 'EPSG:4326', always_xy=True); out = []; miss = 0
    for s in spots:
        o = {'id': s['spot_num'], 'name': s['spot_nm']}
        lon, lat = tr.transform(float(s['grs80tm_x']), float(s['grs80tm_y'])); o['lat'] = round(lat, 6); o['lon'] = round(lon, 6); lanes = set()
        for key, ds in DAYS.items():
            arr = [[0, 0] for _ in range(24)]; got = 0
            for d in ds:
                for h in range(24):
                    fn = os.path.join(OUT, '%s_%s_%02d.json' % (s['spot_num'], d, h))
                    if not os.path.exists(fn): continue
                    rows = json.load(open(fn, encoding='utf-8'))
                    if rows: got += 1
                    for r in rows:
                        i = 0 if r.get('io_type') == '1' else 1; arr[h][i] += int(r.get('vol') or 0); lanes.add((r.get('io_type'), r.get('lane_num')))
            n = len(ds); o[key] = [[round(a / n), round(b / n)] for a, b in arr] if got else None
            if not got: miss += 1
        o['lanes'] = [sum(1 for l in lanes if l[0] == '1'), sum(1 for l in lanes if l[0] == '2')]
        if o['wd'] or o['sa'] or o['su']: out.append(o)
    doc = {'schema': 'tg-traffic-vol-seoul/1', 'source': '서울특별시 교통량조사(서울 열린데이터광장 SpotInfo · VolInfo) · 공공누리 1유형', 'days': '평일 = 2026-09-08(화)·09(수) 평균 · 토 = 09-12 · 일 = 09-13',
           'fields': 'spots = [{id, name, lat, lon, wd·sa·su = 0~23시 [방향1, 방향2] 시간당 대수(차로 합), lanes = [방향1 차로, 방향2 차로]}]', 'note': '조사 지점 값이다 — 지점 밖 도로는 이 값으로 추정하지 않는다(카드에 그렇게 밝힌다) · 방향 1·2 의 실제 방향(상행·하행)은 자료에 이름이 없다', 'spots': out}
    p = os.path.join(ROOT, 'data', 'traffic-vol-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('지점', len(out), '/', len(spots), '빈 날', miss, '바이트', os.path.getsize(p))

if __name__ == '__main__': fetch() if sys.argv[1:] == ['fetch'] else build()
