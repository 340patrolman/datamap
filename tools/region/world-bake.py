# Natural Earth(공공 영역) → gargo/world.json  (나라 110m 경계 · 큰 도시 50m · 한글 이름)
import json, sys, os
D = sys.argv[1]; OUT = sys.argv[2]
c = json.load(open(os.path.join(D, 'ne_110m_admin_0_countries.geojson'), encoding='utf-8'))
def ring(r):
    o = []; last = None
    for x, y in r:
        p = (round(x * 10), round(y * 10))
        if p != last: o += [p[0], p[1]]; last = p
    return o if len(o) >= 6 else None
C = []
for f in c['features']:
    pr = f['properties']; g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    rs = [r for poly in polys for r in [ring(poly[0])] if r]
    if rs: C.append([pr.get('NAME_KO') or pr.get('NAME'), rs])
p = json.load(open(os.path.join(D, 'ne_50m_populated_places.geojson'), encoding='utf-8'))
P = []
for f in p['features']:
    pr = f['properties']; pop = pr.get('POP_MAX') or 0; cap = 1 if pr.get('ADM0CAP') else 0
    if pop < 500000 and not cap: continue
    x, y = f['geometry']['coordinates']
    P.append([round(x * 100), round(y * 100), pr.get('NAME_KO') or pr.get('NAME'), round(pop / 1000), cap])
P.sort(key=lambda r: -r[3])
J = {'schema': 'tg-world/1', 'source': 'Natural Earth(naturalearthdata.com · 공공 영역) — ne_110m_admin_0_countries · ne_50m_populated_places', 'made': '2026-11-16',
     'fields': 'c[[나라 한글 이름, [고리…]]] 고리 = [경도×10, 위도×10, …] · p[[경도×100, 위도×100, 한글 이름, 인구 천 명, 수도 1]] (인구 50만 이상 또는 수도)',
     'note': '비행기·기차 속도 화면(speedo.js)의 세계지도 — 통신 없이 그린다 · 나라 경계는 110m 축척이라 거칠다', 'c': C, 'p': P}
s = json.dumps(J, ensure_ascii=False, separators=(',', ':'))
open(OUT, 'w', encoding='utf-8').write(s)
print('나라', len(C), '도시', len(P), 'bytes', len(s.encode('utf-8')))
