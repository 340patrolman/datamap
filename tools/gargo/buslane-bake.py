# -*- coding: utf-8 -*-
"""가르고 긴급 출동 「버스전용차로」 자리 — gargo/buslane-seoul.json (2026-10-15 · 소유자 「경찰모드로는 진행방향으로 가장 빨리 갈 수 있는 차선 · 긴급 출동 시 위반을 하면서라도」)

긴급자동차는 전용차로로 통행할 수 있다(도로교통법 §15③ 단서 — 「긴급자동차가 그 본래의 긴급한 용도로 운행되고 있는 경우 등 대통령령으로 정하는 경우」 · DRF 원문 대조 2026-10-15).
원자료 = OpenStreetMap(© OpenStreetMap contributors · ODbL) Geofabrik south-korea-latest.osm.pbf — 서울 상자 안의 길 가운데
  highway=busway(버스만 다니는 길 — 서울 중앙버스전용차로가 흔히 이렇게 따로 그려짐) 또는 busway·busway:left/right/both·lanes:bus·bus:lanes 꼬리표가 있는 길
OSM 은 자원봉사 지도라 빠진 구간·시간제 전용차로(가로변 07~10·17~21시) 구분이 없을 수 있다 — 가르고는 「있을 수 있음」으로만 말한다.
  py -3.12 -X utf8 tools/gargo/buslane-bake.py [pbf]
"""
import os, sys, json, datetime
import osmium

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PBF = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/osm/south-korea-latest.osm.pbf'
OUT = os.path.join(ROOT, 'gargo', 'buslane-seoul.json')
BOX = (126.76, 37.41, 127.19, 37.72)   # 서울 상자(경도·위도)
KEYS = ('busway', 'busway:left', 'busway:right', 'busway:both', 'lanes:bus', 'bus:lanes', 'lanes:bus:forward', 'lanes:bus:backward', 'bus:lanes:forward', 'bus:lanes:backward')


class H(osmium.SimpleHandler):
    def __init__(self):
        super().__init__(); self.out = []

    def way(self, w):
        t = w.tags; hw = t.get('highway')
        if not hw:
            return
        kind = 'busway' if hw == 'busway' else None
        if not kind:
            for k in KEYS:
                v = t.get(k)
                if v and v not in ('no', 'none') and ('designated' in v or v in ('lane', 'yes', 'opposite_lane') or k.startswith('lanes:bus') and v.strip('0|') != ''):
                    kind = 'lane'; break
        if not kind:
            return
        try:
            pts = [(n.lon, n.lat) for n in w.nodes]
        except Exception:
            return
        if not any(BOX[0] <= x <= BOX[2] and BOX[1] <= y <= BOX[3] for x, y in pts) or len(pts) < 2:
            return
        flat = []
        for x, y in pts:
            flat += [round(x * 1e5), round(y * 1e5)]
        self.out.append([t.get('name') or '', kind, flat])


def main():
    h = H(); h.apply_file(PBF, locations=True)
    doc = {'schema': 'tg-gargo-buslane/1', 'made': datetime.date.today().isoformat(),
           'source': 'OpenStreetMap contributors(ODbL) · Geofabrik south-korea-latest.osm.pbf — highway=busway 또는 busway·lanes:bus·bus:lanes 꼬리표가 있는 서울 길 · 굽는 도구 tools/gargo/buslane-bake.py',
           'fields': 'l[[길 이름, busway(버스만 다니는 길 · 흔히 중앙버스전용차로)|lane(길 안 버스 차로), [경도×1e5, 위도×1e5, …]]]',
           'note': 'OSM 은 자원봉사 지도 — 빠진 구간이 있을 수 있고 시간제 가로변 전용차로를 가리지 않는다 · 긴급자동차 전용차로 통행 = 도로교통법 §15③ 단서', 'l': h.out}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    c = {}
    for x in h.out:
        c[x[1]] = c.get(x[1], 0) + 1
    print('→', OUT, len(h.out), '길', c, os.path.getsize(OUT), 'B')


if __name__ == '__main__':
    main()
