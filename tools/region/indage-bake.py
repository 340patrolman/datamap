# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.80.0 — 👥→🏪 업종마다 「누가 돈을 쓰나」(나이대별 카드 매출 비중 · 서울 전체)
#   원자료: data/r/<서울 구>/trdar.json 의 ind = [업종, 한 달 매출, 건수, 시간대 6, 연령 매출 6(10·20·30·40·50·60+), …] — 서울시 상권분석서비스 추정매출(카드사 결제 추정 · 분기)
#   서울 모든 상권을 업종마다 더해 나이대 비중을 낸다 → data/ind-age.json
#   지도는 이 비중 × 그 동 나이대별 5·10년 인구 변화(추계)로 업종별 「손님 쪽 수요 변화」를 센다 — 1인당 씀씀이·구매력은 그대로라고 본 근사
#   py -3.12 -X utf8 tools/region/indage-bake.py
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = collections.defaultdict(lambda: [0.0] * 6); T = collections.Counter(); Q = set()
for f in glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'trdar.json')):
    j = json.load(open(f, encoding='utf-8')); Q.add(j.get('quarter'))
    for t in j['trdar']:
        for x in t.get('ind', []):
            a = x[9:15]
            if len(a) < 6: continue
            for i in range(6): A[x[0]][i] += a[i] or 0
            T[x[0]] += x[1] or 0
out = []
for k, a in A.items():
    s = sum(a)
    if s <= 0: continue
    out.append([k, round(T[k]), [round(v / s, 4) for v in a]])
out.sort(key=lambda r: -r[1])
doc = {'schema': 'tg-indage/1', 'source': '서울시 상권분석서비스 추정매출(서울 열린데이터광장 · 카드사 결제 추정 · ' + ', '.join(sorted(str(q) for q in Q if q)) + ') — 서울 모든 상권을 업종마다 더함',
       'ages': ['10대', '20대', '30대', '40대', '50대', '60대 이상'], 'fields': '[업종, 서울 한 달 매출 합(만 원), [나이대 매출 비중 6]]',
       'note': '카드 주인 나이 기준이다 — 아이 학원·키즈카페처럼 부모가 내는 업종은 30·40대로 잡힌다 · 현금 제외 · 서울 비중을 다른 지역에도 쓴다(근사)', 'inds': out}
p = os.path.join(ROOT, 'data', 'ind-age.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(len(out), '업종', os.path.getsize(p), 'B'); print(out[:3])
