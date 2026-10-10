# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.103.0 — 🚪 전국 지하철·도시철도 출입구 번호(OpenStreetMap railway=subway_entrance · © OpenStreetMap contributors · ODbL) → data/exits-kr.json
#   소유자 2026-10-10 「버스정류장과 역 출구번호도 지도에 표시되면 좋겠어」 · 종전 출입구는 서초만(pubdata-seocho) 점으로 있었다
#   역 이름 = 출입구에 적힌 이름(OSM name) → 없으면 가장 가까운 역(이 지도의 역 자리 · 500m 안)
#   py -3.12 -X utf8 tools/region/exit-bake.py
import json, os, math, re, osmium
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PBF = r'C:\Users\knpth\osmwork\kr.pbf'
OUT = os.path.join(ROOT, 'data', 'exits-kr.json')


class H(osmium.SimpleHandler):
    def __init__(self): super().__init__(); self.o = []
    def node(self, n):
        t = n.tags
        if t.get('railway') == 'subway_entrance':
            self.o.append([round(n.location.lat, 6), round(n.location.lon, 6), (t.get('ref') or '').strip(), (t.get('name') or t.get('name:ko') or '').strip()])


def stations():
    S = []
    for f in ('data/r/stations.json', 'data/stations-kr.json'):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p): continue
        j = json.load(open(p, encoding='utf-8'))
        for x in (j if isinstance(j, list) else j.get('pts') or j.get('st') or j.get('items') or []):
            if isinstance(x, dict):
                nm, la, lo = x.get('nm') or x.get('name'), x.get('lat'), x.get('lon')
            else:
                nm = next((v for v in x if isinstance(v, str)), None); nums = [v for v in x if isinstance(v, (int, float))]
                la = next((v for v in nums if 33 < v < 39), None); lo = next((v for v in nums if 124 < v < 132), None)
            if nm and la and lo: S.append((nm, la, lo))
    return S


def main():
    h = H(); h.apply_file(PBF); print('OSM 출입구', len(h.o), flush=True)
    S = stations(); print('역 자리', len(S))
    G = {}
    for nm, la, lo in S: G.setdefault((int(la * 100), int(lo * 100)), []).append((nm, la, lo))
    out, seen, noref, nost = [], set(), 0, 0
    for la, lo, ref, nm in h.o:
        k = (round(la, 5), round(lo, 5))
        if k in seen: continue
        seen.add(k)
        best, bd = '', 500.0
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                for snm, sla, slo in G.get((int(la * 100) + dy, int(lo * 100) + dx), []):
                    d = math.hypot((la - sla) * 111000, (lo - slo) * 88400)
                    if d < bd: best, bd = snm, d
        st = best or re.sub(r'\s*\d+번\s*출구.*$', '', nm)
        st = re.sub(r'역$', '', st.strip())
        if not ref:
            m = re.search(r'(\d+(?:-\d+)?)\s*번', nm)
            if m: ref = m.group(1)
        if not ref: noref += 1
        if not st: nost += 1
        out.append([la, lo, ref, st])
    out.sort(key=lambda r: (r[3], r[2], r[0]))
    json.dump({'schema': 'tg-exit/1', 'source': 'OpenStreetMap railway=subway_entrance(© OpenStreetMap contributors · ODbL) — 출입구 자리·번호', 'fields': '[위도, 경도, 출구 번호(OSM ref · 없으면 빈칸), 역 이름(가장 가까운 역 500m 안 · 없으면 OSM 이름)]',
               'note': 'OSM 은 자원봉사 지도라 빠진 출입구·번호가 있을 수 있다 · 번호가 없는 출입구는 점으로만', 'osm': '2026-10-04 한국 추출본', 'pts': out},
              open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('출입구', len(out), '번호 없음', noref, '역 이름 없음', nost, os.path.getsize(OUT), 'B')


if __name__ == '__main__': main()
