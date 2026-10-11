# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌙 밤에 지하철을 타는 사람의 몫이 해마다 어떻게 변했나(소유자 마스터 문서 7.8 「세대는 느린 변수, 사건은 빠른 변수」 · 회식·음주 문화 → 밤 유동) → data/night-ride-seoul.json
#   재료 = ../07_API키/out/subway_month/<연월>.json — 서울 열린데이터광장 「서울시 지하철 호선별 역별 시간대별 승하차 인원 정보」(CardSubwayTime · 교통카드 · 달마다 · 2019-01~)
#   역마다(호선을 더해) · 해마다: 승차 가운데 밤 22~03시의 몫 · 21시대의 몫 · 저녁 18~20시의 몫 · 한 달 평균 승차
#   밤에 **타는** 사람 = 그 둘레에서 밤까지 머물다 돌아가는 사람(술자리·야근·심야 영업)의 어림이다 — 까닭은 이 자료에 없다
#   원자료가 한 달치를 두 번 싣는 달이 있어 (호선, 역)으로 겹침을 뺀다 · 민자 노선(신분당선·GTX)은 없다
#   py -3.12 -X utf8 tools/region/nightride-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subway_month')
LATE = (22, 23, 0, 1, 2, 3)
def main():
    Y = collections.defaultdict(lambda: [0] * 24); ST = collections.defaultdict(lambda: collections.defaultdict(lambda: [0] * 24)); M = collections.Counter(); LN = collections.defaultdict(set); yms = []
    for f in sorted(glob.glob(os.path.join(SRC, '*.json'))):
        ym = os.path.basename(f)[:6]; y = ym[:4]; yms.append(ym); M[y] += 1; seen = set()
        for r in json.load(open(f, encoding='utf-8')):
            k = (r['SBWY_ROUT_LN_NM'], r['STTN'])
            if k in seen: continue
            seen.add(k); LN[r['STTN']].add(r['SBWY_ROUT_LN_NM'])
            for h in range(24):
                v = r.get('HR_%d_GET_ON_NOPE' % h) or 0; Y[y][h] += v; ST[r['STTN']][y][h] += v
    ys = sorted(Y)
    def row(a, y):
        t = sum(a)
        return [round(sum(a[h] for h in LATE) / t * 100, 2), round(a[21] / t * 100, 2), round(sum(a[18:21]) / t * 100, 1), round(t / M[y])] if t else None
    seoul = [[y] + row(Y[y], y) for y in ys]; items = []
    for st, d in ST.items():
        r = [row(d[y], y) if y in d else None for y in ys]
        if not r[0] or not r[-1] or r[-1][3] < 30000: continue   # 2019년과 마지막 해에 다 있고 한 달 승차 3만 넘는 역만(작은 역은 비율이 흔들린다)
        items.append([st, sorted(LN[st]), [x[0] if x else None for x in r], [x[3] if x else None for x in r], round(r[-1][0] - r[0][0], 2), round(r[-1][0] / r[0][0] * 100 - 100) if r[0][0] else None])
    items.sort(key=lambda x: -x[2][0])
    doc = {'schema': 'tg-night-ride/1', 'made': datetime.date.today().isoformat(), 'months': [yms[0], yms[-1]], 'years': ys, 'late_hours': '22~03시(22 · 23 · 0 · 1 · 2 · 3시대)',
           'source': '서울 열린데이터광장 「서울시 지하철 호선별 역별 시간대별 승하차 인원 정보」(CardSubwayTime · 교통카드 · 달마다)',
           'chain': '바깥 충격(빠른 변수 — 2020~2021 영업시간 제한) · 세대·회식 문화(느린 변수) → 밤까지 머무는 사람 → 밤 상권 · 밤 사고 · 단속의 전제 — ONTOLOGY.md §0 「느린 변수와 빠른 변수」 · 짝: data/night-trend-seoul.json(주점·밤 매출) · data/gen-trend.json(음주·음주운전)',
           'note': ['**밤에 타는 사람의 몫이다 — 까닭은 이 자료에 없다**(회식·음주 문화 · 재택근무 · 심야 영업 · 막차 시간 · 택시·대리운전이 같이 움직였다). 방향과 크기만 본다',
                    '몫 = 그 해 그 역의 승차 가운데 22~03시에 탄 사람 % — 승차 수가 아니라 비율이라 손님이 준 것과 밤 손님만 준 것을 가른다(한 달 평균 승차는 따로 실었다)',
                    '2020~2021년은 영업시간·모임 제한으로 눌려 있다 · 마지막 해는 그 해에 받은 달까지만의 값이다(months 의 끝 달) — 달 수가 달라 계절이 조금 섞인다',
                    '민자 노선(신분당선 · GTX)은 없다 · 호선을 더한 값이다(같은 이름의 역) · 한 달 승차 3만 미만 역은 뺐다',
                    '밤에 지하철을 덜 탄다고 술을 덜 마신다는 뜻은 아니다(다른 수단으로 돌아갈 수 있다) — 여러 자료를 같이 본다'],
           'fields': 'seoul[[해, 밤 22~03시 승차 몫 %, 21시대 %, 저녁 18~20시 %, 한 달 평균 승차]…] · items[[역 이름, [호선…], [해마다 밤 승차 몫 %](years 차례), [해마다 한 달 평균 승차], 첫 해 → 마지막 해 %p, 그 변화율 %]] — 첫 해의 밤 몫이 큰 차례',
           'seoul': seoul, 'items': items}
    p = os.path.join(ROOT, 'data', 'night-ride-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('역', len(items), '· 바이트', os.path.getsize(p)); [print('  ', r) for r in seoul]
    print('밤 몫이 컸던 역(2019 → 마지막 해):', [(x[0], x[2][0], x[2][-1], x[5]) for x in items[:14]])
    print('가장 많이 준 역(변화율):', [(x[0], x[2][0], x[2][-1], x[5]) for x in sorted((i for i in items if i[2][0] >= 6), key=lambda x: x[5])[:10]])
    print('늘거나 덜 준 역:', [(x[0], x[2][0], x[2][-1], x[5]) for x in sorted((i for i in items if i[2][0] >= 6), key=lambda x: -x[5])[:8]])
if __name__ == '__main__': main()
