# -*- coding: utf-8 -*-
"""가르고 — 넓게 볼 때(배율 0.05 아래 · 큰길만 그리는 보기) 자리 잡는 데 쓰는 작은 자료 gargo/far-seoul.json
  · 물: data/base/ov.json(OpenStreetMap) 의 물 고리 가운데 서울 상자에 걸치고 상자 넓이 2km² 넘는 것(한강·중랑천·탄천·안양천 …)
  · 구 이름: data/base/sgg.json(통계청 SGIS 가공 · 공공누리 1유형) 서울 25구의 가운데 자리
쓰는 법: py -3.12 -X utf8 tools/gargo/far-bake.py
"""
import json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ov = json.load(open(os.path.join(R, 'data', 'base', 'ov.json'), encoding='utf-8'))
sg = json.load(open(os.path.join(R, 'data', 'base', 'sgg.json'), encoding='utf-8'))
BOX = (126.72, 127.23, 37.40, 37.72)   # 서울과 둘레
KX, KZ, LON0, LAT0 = 88800.0, 111000.0, 127.01, 37.49
def ll(x, z): return (x / KX + LON0, LAT0 - z / KZ)
water = []
for w in ov['water']:
    nm = ov['names'][w[0]] if w[0] >= 0 else ''
    for r in w[1]:
        x, z = r[0], r[1]; pts = [(x, z)]
        for i in range(2, len(r), 2):
            x += r[i]; z += r[i + 1]; pts.append((x, z))
        L = [ll(*p) for p in pts]
        lo = [p[0] for p in L]; la = [p[1] for p in L]
        if max(lo) < BOX[0] or min(lo) > BOX[1] or max(la) < BOX[2] or min(la) > BOX[3]: continue
        xs = [p[0] for p in pts]; zs = [p[1] for p in pts]
        if (max(xs) - min(xs)) * (max(zs) - min(zs)) < 2e6: continue
        flat = []
        for p in L: flat += [round(p[0] * 1e5), round(p[1] * 1e5)]
        water.append([nm, flat])
gu = [[s['name'], round(s['c'][0] * 1e5), round(s['c'][1] * 1e5)] for s in sg['sgg'] if s['sido'] == '서울특별시']
assert len(gu) == 25, len(gu)
out = {'schema': 'tg-gargo-far/1', 'made': '2026-11-11',
       'source': '물 = © OpenStreetMap contributors(ODbL · data/base/ov.json) · 구 이름 자리 = 통계청 SGIS 행정동 경계 가공(vuski/admdongkor · 공공누리 1유형 · data/base/sgg.json)',
       'fields': 'w[[이름, [경도×1e5, 위도×1e5 …] 고리]] · gu[[구 이름, 경도×1e5, 위도×1e5]]', 'w': water, 'gu': gu}
p = os.path.join(R, 'gargo', 'far-seoul.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('물 고리', len(water), [w[0] for w in water], '· 구', len(gu), '·', os.path.getsize(p), 'B')
