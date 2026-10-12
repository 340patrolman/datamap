# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🦉 올빼미버스(서울 심야 N 노선) 정류장별 시간대별 승하차 → data/night-bus-seoul.json
#   소유자 2026-10-12 「서로가 서로에게 영향을 미치며 사니 · 오만가지 자료」 → 지하철이 끊긴 뒤 밤 사람이 어디서 타고 어디서 내리나
#   택시 승하차(동 × 시)는 공개 자료가 없다(more-sources.json) — 그 자리를 메우는 것 가운데 하나가 심야버스다(택시·대리·자가용은 여전히 안 보인다)
#   원자료: 서울 열린데이터광장 「서울시 버스노선별 정류장별 시간대별 승하차 인원 정보」(CardBusTimeNew · 달마다 · 키 seoul · http) 에서 노선번호가 N 으로 시작하는 줄만
#     → 07_API키/out/nightbus/N_<연월>.json (받는 법: 주소 끝에 <연월>/ · 1000줄씩 넘기며 N 노선만 남긴다)
#   정류장 자리 = 07_API키/out/seoul_busstop_all.json(STOPS_NO = 표준버스정류장ID)
#   py -3.12 -X utf8 tools/region/nightbus-bake.py   (새 달을 받으면 MONTHS 에 더하고 다시)
import json, os, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키', 'out')
MONTHS = ['201909', '202309', '202509', '202609']; HRS = [23, 0, 1, 2, 3, 4, 5]
def val(r, h, on):
    for k in ('HR_%d_GET_%s_TNOPE' % (h, 'ON' if on else 'OFF'), 'HR_%d_GET_%s_NOPE' % (h, 'ON' if on else 'OFF')):
        if k in r: return r[k] or 0
    return 0
def main():
    XY = {s['STOPS_NO']: s for s in json.load(open(os.path.join(KB, 'seoul_busstop_all.json'), encoding='utf-8-sig'))}
    ST = collections.defaultdict(lambda: {m: [[0] * 7, [0] * 7] for m in MONTHS}); NM = {}; RT = collections.defaultdict(lambda: collections.defaultdict(set)); TOT = {m: [[0] * 7, [0] * 7] for m in MONTHS}; ROUTES = {}; BYR = {m: collections.Counter() for m in MONTHS}
    for m in MONTHS:
        rows = json.load(open(os.path.join(KB, 'nightbus', 'N_%s.json' % m), encoding='utf-8')); ROUTES[m] = sorted(set(r['RTE_NO'] for r in rows))
        for r in rows:
            sid = r['STOPS_ID']; NM[sid] = r['SBWY_STNS_NM'].split('(0')[0]; RT[sid][m].add(r['RTE_NO'])
            for i, h in enumerate(HRS):
                a = val(r, h, 1); b = val(r, h, 0); ST[sid][m][0][i] += a; ST[sid][m][1][i] += b; TOT[m][0][i] += a; TOT[m][1][i] += b; BYR[m][r['RTE_NO']] += a
    items = []; miss = 0
    for sid, d in ST.items():
        s = XY.get(sid)
        if not s or not s.get('XCRD'): miss += 1; continue
        last = MONTHS[-1]
        items.append([sid, NM[sid], round(float(s['XCRD']), 5), round(float(s['YCRD']), 5)] + [[round(sum(d[m][0])), round(sum(d[m][1]))] for m in MONTHS] + [[round(x) for x in d[last][0]], [round(x) for x in d[last][1]], sorted(RT[sid][last])])
    items.sort(key=lambda r: -(r[4 + len(MONTHS) - 1][0] + r[4 + len(MONTHS) - 1][1]))
    doc = {'schema': 'tg-night-bus/1', 'made': datetime.date.today().isoformat(),
           'source': '서울 열린데이터광장 「서울시 버스노선별 정류장별 시간대별 승하차 인원 정보」(CardBusTimeNew · 교통카드 · 달마다) 가운데 노선번호 N(올빼미버스) · 정류장 자리 = 서울시 버스정류소 위치정보',
           'note': ['값은 **그 달 한 달 합계**(하루 평균이 아니다 — 하루로 보려면 그 달 날수로 나눈다) · 교통카드로 찍은 것만(현금·무임 없음)',
                    '노선이 늘었다: 2019-09 9개 → 2023-09 부터 14개 — 해끼리 견줄 때 「사람이 늘었다」와 「노선이 생겼다」를 가르지 못한다(routes 를 같이 본다)',
                    '택시·대리운전·자가용으로 돌아가는 사람은 여기에 없다 — 밤 이동의 한 조각일 뿐이다(지하철 밤 승차는 night-ride-seoul.json)',
                    '하차를 안 찍고 내리는 사람이 있어 하차는 승차보다 적게 잡힌다',
                    '정류장 자리를 못 찾은 %d곳(가상 정류장·차고지 등)은 뺐다' % miss],
           'fields': {'months': '견준 달(연월)', 'hours': '시간대 차례 — 23시대 · 0 · 1 · 2 · 3 · 4 · 5시대', 'routes': '{연월: [그 달 다닌 N 노선]}',
                      'total': '{연월: [[시간대별 승차 합], [시간대별 하차 합]]}(서울 N 노선 전부)', 'by_route': '{연월: {노선: 승차 합}} — 같은 노선끼리 견줄 때',
                      'items': '[[정류장 ID, 이름, 경도, 위도, 달마다 [승차 합, 하차 합] … (months 차례), 마지막 달 시간대별 승차[7], 마지막 달 시간대별 하차[7], 마지막 달 서는 N 노선]] — 마지막 달 승하차 많은 차례'},
           'months': MONTHS, 'hours': HRS, 'routes': ROUTES, 'by_route': {m: {k: round(v) for k, v in sorted(BYR[m].items())} for m in MONTHS}, 'total': {m: [[round(x) for x in TOT[m][0]], [round(x) for x in TOT[m][1]]] for m in MONTHS}, 'items': items}
    p = os.path.join(ROOT, 'data', 'night-bus-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '정류장', len(items), '자리 없음', miss)
    for m in MONTHS: print(m, '노선', len(ROUTES[m]), '승차', round(sum(TOT[m][0])), '하차', round(sum(TOT[m][1])), '시간대 승차', [round(x) for x in TOT[m][0]])
    L = len(MONTHS) - 1; same = ROUTES[MONTHS[0]]; print('2019 에도 있던 노선끼리', {m: round(sum(BYR[m][k] for k in same)) for m in MONTHS})
    print('많이 타는 곳', [(r[1], r[4 + L][0]) for r in sorted(items, key=lambda r: -r[4 + L][0])[:15]])
    print('많이 내리는 곳', [(r[1], r[4 + L][1]) for r in sorted(items, key=lambda r: -r[4 + L][1])[:15]])
if __name__ == '__main__': main()
