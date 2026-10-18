# -*- coding: utf-8 -*-
# 데이터 압축지도 — T-GIS 교차로의 관할 경찰서 코드(NW_PE_CDE · 110~410) → 경찰서 이름 → data/tgis-pe.json
#   원자료(T-GIS 교차로 A008_P)에는 코드만 있고 이름 표가 없다(서초 340 · 방배 380 만 확인돼 있었다)
#   방법: 교차로 자리 → 행정동(13_관할경계 hjd20260701 · 8자리) → 그 동을 맡는 경찰서(data/police-card.json — 경찰청 직제 시행규칙 별표2 × 행정동)
#         → 코드마다 가장 많이 나온 경찰서와 그 비율(맞음 %) · 두 서가 함께 맡는 동은 빼고 센다 · 80% 넘고 다른 코드와 겹치지 않을 때만 이름을 붙인다
#   py -3.12 -X utf8 tools/signal/tgis-pe-bake.py
import json, os, collections, datetime
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')


def main():
    T = json.load(open(os.path.join(ROOT, 'data', 'tgis-seoul.json'), encoding='utf-8'))
    PC = json.load(open(os.path.join(ROOT, 'data', 'police-card.json'), encoding='utf-8'))
    own = collections.defaultdict(set)
    for sid, st in PC['st'].items():
        for dg in st.get('dongs', []):
            if dg[4]: continue   # 여러 서가 나눠 맡는 동은 빼고 센다
            own[str(dg[0])[:8]].add(st['n'])
    G = json.load(open(HJD, encoding='utf-8'))['features']; geoms, codes = [], []
    for f in G:
        p = f['properties']; c = str(p.get('adm_cd2') or p.get('adm_cd8') or p.get('adm_cd') or '')[:8]
        if not c.startswith('11'): continue
        geoms.append(shape(f['geometry'])); codes.append(c)
    tree = STRtree(geoms); tally = collections.defaultdict(collections.Counter); nin = collections.Counter()
    for it in T['items']:
        pe, la, lo = it[5], it[2], it[3]; nin[pe] += 1; pt = Point(lo, la); d = None
        for i in tree.query(pt):
            if geoms[i].contains(pt): d = codes[i]; break
        if not d or len(own.get(d, ())) != 1: continue
        tally[pe][next(iter(own[d]))] += 1
    out = {}; used = collections.Counter()
    for pe, c in sorted(tally.items()):
        nm, n = c.most_common(1)[0]; tot = sum(c.values()); used[nm] += 1
        out[str(pe)] = [nm, round(n / tot, 3), tot, nin[pe]]
    for pe, v in out.items():
        v.append(1 if v[1] >= 0.8 and used[v[0]] == 1 else 0)
    res = {'schema': 'tg-tgis-pe/1', 'made': datetime.date.today().isoformat(),
           'source': 'T-GIS 교차로(data/tgis-seoul.json)의 관할 경찰서 코드 × 교차로가 든 행정동(통계청 SGIS 경계 · vuski/admdongkor 2026-07) × 그 동을 맡는 경찰서(data/police-card.json — 경찰청과 그 소속기관 직제 시행규칙 별표2)',
           'fields': 'pe{코드: [가장 많이 맞는 경찰서, 맞음 비율, 센 교차로(한 서만 맡는 동), 그 코드 교차로 전체, 이름 씀 1|0(80% 넘고 다른 코드와 안 겹침)]}',
           'note': '원자료에 이름 표가 없어 자리로 맞춘 것 — 「어림」 · 두 서가 함께 맡는 동의 교차로는 세지 않았다', 'pe': out}
    json.dump(res, open(os.path.join(ROOT, 'data', 'tgis-pe.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    for pe, v in out.items(): print(pe, v)
    print('이름 씀', sum(v[4] for v in out.values()), '/', len(out))


if __name__ == '__main__':
    main()
