# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.8.0 — OSM 경찰 시설(amenity=police) 이름·자리 → 07_API키/out/police/osm_police.json
#   지구대·파출소 주소를 브이월드로 좌표화하다 하루 한도에 걸린 곳을 이름으로 채우는 데 쓴다(police-bake.py) · © OpenStreetMap contributors (ODbL)
import json, os, osmium
from shapely import wkb as swkb
PBF = r'C:\Users\knpth\osmwork\kr.pbf'
OUT = r'C:\Users\knpth\Desktop\지식베이스\07_API키\out\police\osm_police.json'
class H(osmium.SimpleHandler):
    def __init__(self): super().__init__(); self.o = []; self.f = osmium.geom.WKBFactory()
    def node(self, n):
        t = n.tags
        if t.get('amenity') == 'police' and t.get('name'): self.o.append([t.get('name'), round(n.location.lat, 6), round(n.location.lon, 6)])
    def area(self, a):
        t = a.tags
        if t.get('amenity') == 'police' and t.get('name'):
            try: c = swkb.loads(self.f.create_multipolygon(a), hex=True).representative_point(); self.o.append([t.get('name'), round(c.y, 6), round(c.x, 6)])
            except Exception: pass
h = H(); h.apply_file(PBF, locations=True)
json.dump(h.o, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
print('OSM 경찰 시설', len(h.o), sum(1 for x in h.o if '지구대' in x[0] or '파출소' in x[0]))
