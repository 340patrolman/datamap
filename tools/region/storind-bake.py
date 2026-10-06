# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.54.0 — 🏪 업종별 개업·폐업·버티는 기간(소유자 「점포 개업·폐업 업종과 업종별 생존율·기간」) → data/r/<서울 구>/storind.json
#   원자료 07_API키/out/region/fac/VwsmAdstrdStorW.json = 서울시 상권분석서비스 점포-행정동(서비스 업종 100개 · 분기 · 점포·개업·폐업 수 · 2021~)
#   동마다 업종마다 [업종, 지금 점포, 최근 4분기 개업, 최근 4분기 폐업, 2021년부터 개업 합, 2021년부터 폐업 합, 처음 분기 점포, 프랜차이즈 점포]
#   「평균 버티는 기간(어림)」= 점포 수 ÷ 한 해 폐업 수(안정 상태 가정 · 년) — 화면에서 계산 · 설계값
#   py -3.12 -X utf8 tools/region/storind-bake.py
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region', 'fac', 'VwsmAdstrdStorW.json')
rows = json.load(open(SRC, encoding='utf-8'))
QS = sorted({r['STDR_YYQU_CD'] for r in rows}); last4 = set(QS[-4:]); q0, qL = QS[0], QS[-1]
A = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, 0]))
for r in rows:
    k = r['ADSTRD_CD']; nm = r['SVC_INDUTY_CD_NM']; q = r['STDR_YYQU_CD']; a = A[k][nm]
    st, op, cl, fr = r.get('STOR_CO') or 0, r.get('OPBIZ_STOR_CO') or 0, r.get('CLSBIZ_STOR_CO') or 0, r.get('FRC_STOR_CO') or 0
    if q == qL: a[0] = int(st); a[6] = int(fr)
    if q in last4: a[1] += int(op); a[2] += int(cl)
    a[3] += int(op); a[4] += int(cl)
    if q == q0: a[5] = int(st)
G = collections.defaultdict(dict)
for k, v in A.items():
    L = [[nm] + x for nm, x in v.items() if x[0] or x[1] or x[2]]
    L.sort(key=lambda x: -x[1]); G[k[:5]][k] = L
for gu, d in G.items():
    p = os.path.join(ROOT, 'data', 'r', gu)
    if not os.path.isdir(p): continue
    doc = {'schema': 'tg-storind/1', 'gu': gu, 'q0': q0, 'qL': qL, 'last4': sorted(last4), 'source': '서울시 상권분석서비스 점포-행정동(VwsmAdstrdStorW · 서비스 업종 100개 · 분기)',
           'fields': 'dong = {행정동 8자리: [[업종, 지금 점포, 최근 4분기 개업, 최근 4분기 폐업, %s부터 개업 합, %s부터 폐업 합, %s 점포, 프랜차이즈 점포]]}' % (q0, q0, q0), 'dong': d}
    json.dump(doc, open(os.path.join(p, 'storind.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', len(G), '동', sum(len(v) for v in G.values()), q0, qL)
