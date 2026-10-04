# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.2.0 — 소상공인시장진흥공단 「주요상권」 영역(서울·경기)
#   받기: 공공데이터포털 소상공인 상가업소 정보서비스 storeZoneInAdmi(divId=ctprvnCd, key=11|41) → 07_API키/out/region/szone/szone_<시도>.json
#         (소상공인365 「개방·활용 › API 서비스 명세」의 공식 오픈 API · 데이터기준일자 2024-01-01 · 서울 176 · 경기 281)
#   굽기: py -3.12 -X utf8 tools/region/szone-bake.py → data/r/<구>/szone.json · r/index.json bytes.szone
#   영역마다 그 안의 등록 상가(같은 공단 상가정보 · r/<구>/stores.json)를 세어 업종 대분류·많은 소분류·1층 비율을 붙인다.
#   ⚠ 매출·유동인구 등 소상공인365 화면의 카드사·통신사 자료는 공개 API 가 아니라 넣지 않는다(robots.txt Disallow · 제공 계약 자료).
import json, os, glob, collections, importlib.util
import numpy as np
import shapely
from shapely import wkt
from shapely.geometry import Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region')

def main():
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shapely.geometry.shape(f['geometry']) for f in feats]; tr = STRtree(gs)
    def where(x, y):
        q = Point(x, y)
        for i in tr.query(q):
            if gs[i].contains(q): return feats[i]['properties']
        return None
    IDX = json.load(open(os.path.join(ROOT, 'data', 'r', 'stores-index.json'), encoding='utf-8')); CL = IDX['cls']
    xs, ys, cs, fs = [], [], [], []
    for fn in glob.glob(os.path.join(ROOT, 'data', 'r', '*', 'stores.json')):
        j = json.load(open(fn, encoding='utf-8')); O, K = j['o'], j['k']
        for q in j['pts']: xs.append(O[0] + q[0] / K[0]); ys.append(O[1] + q[1] / K[1]); cs.append(q[2]); fs.append(str(q[3] or ''))
    xs, ys, cs = np.array(xs), np.array(ys), np.array(cs); print('stores', len(xs))
    G = collections.defaultdict(list); miss = 0
    for sd in ('11', '41'):
        for z in json.load(open(os.path.join(REG, 'szone', 'szone_%s.json' % sd), encoding='utf-8')):
            g = wkt.loads(z['coords'])
            if not g.is_valid: g = g.buffer(0)
            c = g.representative_point(); p = where(c.x, c.y)
            if not p: miss += 1; continue
            b = g.bounds; m = (xs >= b[0]) & (xs <= b[2]) & (ys >= b[1]) & (ys <= b[3]); ii = np.nonzero(m)[0]
            inside = ii[shapely.contains_xy(g, xs[ii], ys[ii])] if len(ii) else ii
            L = collections.Counter(CL[cs[i]][1] for i in inside); Sm = collections.Counter(CL[cs[i]][4] for i in inside)
            f1 = sum(1 for i in inside if fs[i] == '1'); fk = sum(1 for i in inside if fs[i])
            gg = g.simplify(0.00002, preserve_topology=True); polys = [gg] if gg.geom_type == 'Polygon' else list(gg.geoms)
            G[p['sgg']].append({'no': z['trarNo'], 'n': z['mainTrarNm'], 'sgg': z['signguNm'], 'area': int(float(z['trarArea'] or 0)), 'dt': z['stdrDt'],
                                'lat': round(c.y, 6), 'lon': round(c.x, 6), 'dong': p['adm_nm'].split(' ')[-1],
                                'rings': [[[round(x, 6), round(y, 6)] for x, y in pg.exterior.coords][:-1] for pg in polys],
                                'st': len(inside), 'L': L.most_common(), 'S': Sm.most_common(8), 'f1': [f1, fk]})
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for gu, items in G.items():
        fn = os.path.join(ROOT, 'data', 'r', gu, 'szone.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        json.dump({'schema': 'tg-szone/1', 'gu': gu,
                   'source': '소상공인시장진흥공단 주요상권(공공데이터포털 「소상공인 상가업소 정보서비스」 storeZoneInAdmi · 데이터기준일자 2024-01-01) · 점포 = 같은 공단 상가(상권)정보 ' + IDX['stdrYm'],
                   'note': '소진공이 정한 주요상권의 경계다(2024년 1월 기준 · 그 뒤 변동 없음이라고 소상공인365 기준 데이터에 적혀 있다). 점포 수·업종은 영역 안에 등록된 상가를 이 지도가 센 것(영업 여부 모름). 소상공인365 화면의 매출·유동인구·소득은 카드사·통신사 제공 자료라 공개 API 가 아니어서 넣지 않았다.',
                   'items': items}, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[gu] = os.path.getsize(fn)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['szone'] = gb[g2['gu']]
    R['layers']['szone'] = '소진공 주요상권 영역(서울·경기) + 영역 안 등록 점포'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('items', sum(len(v) for v in G.values()), 'miss', miss, 'gus', len(gb), 'bytes', sum(gb.values()))

if __name__ == '__main__': main()
