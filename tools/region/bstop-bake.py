# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.14.0 — 🚏 전국 버스정류장 자리(OpenStreetMap highway=bus_stop · © OpenStreetMap contributors · ODbL) → data/r/<구>/bstop.json
#   승하차 인원은 없다(서울·경기는 교통카드 승하차가 있는 「🚌 버스 승차·하차」 층) · 국토부 TAGO 정류소 API 는 활용신청 대기(403)
#   py -3.12 -X utf8 tools/region/bstop-bake.py
import json, os, collections, osmium
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PBF = r'C:\Users\knpth\osmwork\kr.pbf'
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
R = os.path.join(ROOT, 'data', 'r')

class H(osmium.SimpleHandler):
    def __init__(self): super().__init__(); self.o = []
    def node(self, n):
        t = n.tags
        if t.get('highway') == 'bus_stop' or (t.get('public_transport') == 'platform' and t.get('bus') == 'yes'):
            self.o.append([round(n.location.lat, 6), round(n.location.lon, 6), t.get('name') or t.get('name:ko') or '', t.get('ref') or ''])

def main():
    h = H(); h.apply_file(PBF); print('OSM 정류장', len(h.o), flush=True)
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['sgg']) for f in g['features']]; tr = STRtree([x[0] for x in F])
    G = collections.defaultdict(list); seen = set()
    for la, lo, nm, ref in h.o:
        k = (round(la, 5), round(lo, 5))
        if k in seen: continue
        seen.add(k); p = Point(lo, la)
        for i in tr.query(p):
            if F[i][0].contains(p): G[F[i][1]].append([la, lo, nm, ref]); break
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}; tot = 0
    for gu, pts in G.items():
        if gu not in known: continue
        p = os.path.join(R, gu, 'bstop.json')
        json.dump({'schema': 'tg-bstop/1', 'gu': gu, 'source': 'OpenStreetMap highway=bus_stop(© OpenStreetMap contributors · ODbL) — 자리·이름만', 'fields': '[위도, 경도, 이름, 정류장 번호(OSM ref · 있으면)]',
                   'note': '승하차 인원 없음 · OSM 은 자원봉사 지도라 빠진 정류장이 있을 수 있다', 'pts': pts}, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        known[gu].setdefault('bytes', {})['bstop'] = os.path.getsize(p); tot += len(pts)
    IX['layers']['bstop'] = '🚏 버스정류장 자리(OSM · 전국)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('정류장', tot, '구', len(G))

if __name__ == '__main__': main()
