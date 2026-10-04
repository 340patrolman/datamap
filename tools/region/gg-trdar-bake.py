# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.1.0 — 경기 상권(발달·골목) 영역 + 업종별 추정매출
#   영역: 경기데이터드림 「발달상권 현황」(858) · 「골목상권 현황」(834) — 경기도시장상권진흥원 · 다중지역정보(GeoJSON) · 시트(searchSheetData.do)로 받아
#         07_API키/out/region/ggtrd/poly.json([유형, 이름, 위도, 경도, 점포 수, 업종정보, GeoJSON])
#   매출: 경기데이터드림 「경기도 발달골목상권 추정매출 현황」 OpenAPI TBGGESTDEVALLSTM(기준연도·분기·상권ID·상권명·산업분류(10차)·매출금액·건수)
#         `tools/region/gg-card-fetch.py TBGGESTDEVALLSTM` → 07_API키/out/region/ggcard/TBGGESTDEVALLSTM_*.json · 공개분은 2025년 3분기 한 분기
#   ⚠ 영역 자료에 상권ID 가 없어 이름으로 잇는다 — 이름이 겹치는 상권(71)은 매출을 붙이지 않는다(어느 영역 것인지 모른다)
#   py -3.12 -X utf8 tools/region/gg-trdar-bake.py → data/r/<구>/ggtrd.json · r/index.json bytes.ggtrd
import json, os, glob, collections, importlib.util
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region')

def main():
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(f['geometry']) for f in feats]; tr = STRtree(gs)
    def where(lon, lat):
        q = Point(lon, lat)
        for i in tr.query(q):
            if gs[i].contains(q): return feats[i]['properties']
        return None
    poly = json.load(open(os.path.join(REG, 'ggtrd', 'poly.json'), encoding='utf-8'))
    ncount = collections.Counter(p[1] for p in poly)
    S = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0])); Q = None; ids = collections.defaultdict(set)
    for fn in glob.glob(os.path.join(REG, 'ggcard', 'TBGGESTDEVALLSTM_0*.json')):
        for yy, qu, dv, nm, cd, cn, amt, noc, adm, stc in json.load(open(fn, encoding='utf-8')):
            Q = Q or (yy + ' ' + qu); a = S[nm][cn]; a[0] += float(amt or 0); a[1] += int(noc or 0); ids[nm].add(dv)
    G = collections.defaultdict(list); nosale = dup = 0
    for kind, nm, lat, lon, stc, indtxt, gj in poly:
        p = where(lon, lat)
        if not p: continue
        g = shape(json.loads(gj)).simplify(0.00002, preserve_topology=True)
        polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
        rings = [[[round(x, 6), round(y, 6)] for x, y in pg.exterior.coords] for pg in polys]
        it = {'k': kind, 'n': nm, 'lat': round(lat, 6), 'lon': round(lon, 6), 'st': stc, 'dong': p['adm_nm'].split(' ')[-1], 'rings': rings, 'indt': indtxt.split('/')[:12]}
        if ncount[nm] > 1 or len(ids.get(nm, ())) > 1: dup += 1; it['dup'] = 1
        elif nm in S:
            rows = sorted(S[nm].items(), key=lambda x: -x[1][0]); tot = [sum(v[0] for _, v in rows), sum(v[1] for _, v in rows)]
            it['tot'] = [round(tot[0] / 10000), tot[1]]; it['ind'] = [[c, round(v[0] / 10000), v[1]] for c, v in rows[:15]]
        else: nosale += 1
        G[p['sgg']].append(it)
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for gu, items in G.items():
        doc = {'schema': 'tg-ggtrd/1', 'gu': gu, 'quarter': Q,
               'source': '경기데이터드림 — 발달상권 현황(2025-09-01)·골목상권 현황(2026-06-09)(경기도시장상권진흥원 · 영역 다각형) · 경기도 발달골목상권 추정매출 현황(TBGGESTDEVALLSTM · %s분기 · 산업분류 10차 업종별 매출·건수)' % Q,
               'note': '추정매출은 경기도 상권분석 시스템의 모델 추정값이다(실제 매출 아님) — 공개분은 한 분기뿐이라 추이는 볼 수 없다. 영역 자료에 상권 번호가 없어 이름으로 이었고, 이름이 겹치는 상권은 매출을 붙이지 않았다. 시간대·연령·요일 매출은 경기도가 이 자료로 공개하지 않는다.',
               'items': items}
        fn = os.path.join(ROOT, 'data', 'r', gu, 'ggtrd.json'); os.makedirs(os.path.dirname(fn), exist_ok=True)
        json.dump(doc, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(fn)
    for g in R['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['ggtrd'] = gb[g['gu']]
    R['layers']['ggtrd'] = '경기 상권(발달·골목 영역 + 업종별 추정매출 한 분기)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('quarter', Q, 'items', sum(len(v) for v in G.values()), 'dup', dup, 'nosale', nosale, 'gus', len(gb), 'bytes', sum(gb.values()))

if __name__ == '__main__': main()
