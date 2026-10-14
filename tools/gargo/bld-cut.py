# -*- coding: utf-8 -*-
"""네비 가르고 — 여섯 구(서초·강남·송파·동작·관악·용산) 건물 그림 data/maps/bld6/(index.json + c/<칸>.json · 2km 칸)을 굽는다.
  2026-10-14 소유자 「서초·강남·송파·동작·관악·용산」 · 가르고 v0.7.0 여섯 구 길 묶음과 같은 상자(37.405~37.570 · 126.875~127.190).
  꼴 = data/maps/seocho-full-buildings.json(tg-buildings/1 · 게임이 읽는 서초 한 장 — 그 파일은 건드리지 않는다)과 같다:
    buildings[{p 윤곽 [[x, z]…](미터), lv 층수(building:levels · 없으면 0), n 이름(없으면 null)}] · transform x=(lon-127.0077)*88800+2438 · z=-(lat-37.4917)*111000+1743
  원자료 = Geofabrik south-korea-latest.osm.pbf(../gargo/tools/osm-cut.py 와 같은 파일 · osmium 은 한글 경로를 못 열어 C:/Users/knpth/regionwork/osm/) · 닫힌 building 길(way)만(여러 조각 건물 relation 은 뺀다)
  가로·세로 모두 7m 미만은 뺀다(서초 한 장과 같은 규칙) · 윤곽은 0.5m 로 반올림. 출처: © OpenStreetMap contributors · ODbL
  쓰기: py -3.12 -X utf8 tools/gargo/bld-cut.py [pbf 경로]
"""
import json, os, sys, datetime, osmium
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PBF = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/osm/south-korea-latest.osm.pbf'
BOX = (37.405, 126.875, 37.570, 127.190); CELL = 2000
def X(lon): return round(((lon - 127.0077) * 88800 + 2438) * 2) / 2
def Z(lat): return round((-(lat - 37.4917) * 111000 + 1743) * 2) / 2
class H(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.B = []; s.tiny = 0
    def way(s, w):
        if 'building' not in w.tags or len(w.nodes) < 4 or w.nodes[0].ref != w.nodes[-1].ref: return
        try: pts = [(n.location.lon, n.location.lat) for n in w.nodes]
        except Exception: return
        cx = sum(p[0] for p in pts) / len(pts); cy = sum(p[1] for p in pts) / len(pts)
        if not (BOX[0] <= cy <= BOX[2] and BOX[1] <= cx <= BOX[3]): return
        P = [[X(a), Z(b)] for a, b in pts[:-1]]; xs = [p[0] for p in P]; zs = [p[1] for p in P]
        if max(xs) - min(xs) < 7 and max(zs) - min(zs) < 7: s.tiny += 1; return
        lv = w.tags.get('building:levels') or ''
        try: lv = int(float(lv.split(';')[0]))
        except Exception: lv = 0
        s.B.append({'p': P, 'lv': lv, 'n': w.tags.get('name') or None})
def main():
    h = H(); h.apply_file(PBF, locations=True)
    doc = {'schema': 'tg-buildings/1', 'map': 'six', 'source': 'OpenStreetMap contributors (ODbL) · Geofabrik south-korea-latest.osm.pbf %s' % datetime.date.fromtimestamp(os.path.getmtime(PBF)).isoformat(),
           'note': '네비 가르고 여섯 구(서초·강남·송파·동작·관악·용산 + 2km 상자) 건물 윤곽 — 닫힌 building 길만(여러 조각 건물 relation 은 빠짐) · 층수(lv)가 없으면 0 · 가로·세로 모두 7m 미만은 뺐다 · OSM 에 없는 건물은 없다(서울 OSM 건물 자료는 빠진 곳이 많다)',
           'transform': 'x=(lon-127.0077)*88800+2438 · z=-(lat-37.4917)*111000+1743',
           'counts': {'buildings': len(h.B), 'withLevels': sum(1 for b in h.B if b['lv']), 'named': sum(1 for b in h.B if b['n']), 'tinySkipped': h.tiny}, 'buildings': h.B}
    # 한 장이면 16MB(전송 3.9MB · 12만 동)라 폰에 무겁다 → 2km 칸으로 나눠 가르고가 화면에 보이는 칸만 받는다(건물은 크게 볼 때만 그린다)
    D = os.path.join(ROOT, 'data', 'maps', 'bld6'); os.makedirs(os.path.join(D, 'c'), exist_ok=True); T = {}
    for bd in h.B:
        cx = sum(q[0] for q in bd['p']) / len(bd['p']); cz = sum(q[1] for q in bd['p']) / len(bd['p']); T.setdefault('%d_%d' % (cx // CELL, cz // CELL), []).append(bd)
    for k, v in T.items(): json.dump({'schema': 'tg-buildings/1', 'cell': k, 'buildings': v}, open(os.path.join(D, 'c', k + '.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    del doc['buildings']; doc['schema'] = 'tg-buildings-tiles/1'; doc['cell'] = CELL; doc['tiles'] = {k: len(v) for k, v in sorted(T.items())}
    doc['fields'] = 'tiles{칸 이름 「ix_iz」(= floor(x / cell)_floor(z / cell) · 건물 가운데 점 기준): 건물 수} · 칸 파일 c/<칸>.json = {buildings[{p, lv, n}]}'
    json.dump(doc, open(os.path.join(D, 'index.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    sz = [os.path.getsize(os.path.join(D, 'c', k + '.json')) for k in T]
    print(doc['counts'], '칸', len(T), '· 가장 큰 칸', max(sz), 'B · 합', sum(sz), 'B')
if __name__ == '__main__': main()
