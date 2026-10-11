# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌙 「밤이 짧아졌다」: 서로 다른 자료 일곱 가지를 한 표에(소유자 2026-10-11 「지하철 이용자들이 줄어들었다니 매우 중요한 자료 · 내용 더 찾아 추가하고 합리적인 결과를 만들어내자」) → data/night-shift.json
#   한 자료만으로는 까닭을 모른다 → **출처가 다른 자료들이 같은 쪽을 가리키는가**를 본다:
#     ① 지하철 시간대별 승차(서울 열린데이터 · 달마다) ② 주점·유흥·밤 매출 비중(서울 상권분석 · night-trend) ③ 음주운전 사고의 시간대(TAAS · gen-trend) ④ 음주운전 적발의 시각(경찰청 · dui-catch)
#     ⑤ 음주율·폭음률(국민건강영양조사 · gen-trend) ⑥ 주류 출고량(국세청 · gen-trend) ⑦ 음주운전 경험률(gen-trend)
#   읽는 법: 「얼마나 마시나」(⑤⑥)는 조금 줄었고 「밤늦게 밖에 있나」(①②③④)는 많이 줄었다 → 덜 마신다기보다 **일찍 끝낸다**로 읽힌다(이 도구가 붙인 풀이 — 자료가 까닭을 말해 주지는 않는다)
#   py -3.12 -X utf8 tools/region/nightshift-bake.py   (night-ride · night-trend · gen-trend · dui-catch 를 다시 구우면 같이 다시)
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subway_month'); LATE = (22, 23, 0, 1, 2, 3)
def J(n): return json.load(open(os.path.join(ROOT, 'data', n), encoding='utf-8'))
def main():
    MON = collections.defaultdict(lambda: [0] * 24); SOFF = collections.defaultdict(lambda: collections.defaultdict(lambda: [0] * 24)); TOTS = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(os.path.join(SRC, '*.json'))):
        ym = os.path.basename(f)[:6]; seen = set()
        for r in json.load(open(f, encoding='utf-8')):
            k = (r['SBWY_ROUT_LN_NM'], r['STTN'])
            if k in seen: continue
            seen.add(k)
            for h in range(24):
                a = r.get('HR_%d_GET_ON_NOPE' % h) or 0; b = r.get('HR_%d_GET_OFF_NOPE' % h) or 0; MON[ym][h] += a; SOFF[r['STTN']][ym[:4]][h] += b; TOTS[r['STTN']][ym[:4]] += a + b
    yms = sorted(MON); months = [[ym, round(sum(MON[ym][h] for h in LATE) / sum(MON[ym]) * 100, 2), round(sum(MON[ym][h] for h in LATE))] for ym in yms]
    dec = [[y, round(sum(MON['%d12' % y][h] for h in LATE)), round(sum(MON['%d12' % y][h] for h in LATE) / sum(MON['%d12' % y]) * 100, 2), round(sum(MON['%d12' % y][h] for h in LATE) / sum(MON['%d11' % y][h] for h in LATE), 2)] for y in range(2019, 2027) if '%d12' % y in MON and '%d11' % y in MON]
    def chg(st, hs):   # 2019 → 2025 하차 변화 % — 그 역의 전체 승하차가 35% 넘게 줄었으면(노선 운영·집계 범위가 바뀐 역) 뺀다
        d = SOFF[st]
        if '2019' not in d or '2025' not in d or TOTS[st]['2025'] < TOTS[st]['2019'] * 0.65: return None
        a = sum(d['2019'][h] for h in hs) / 12; b = sum(d['2025'][h] for h in hs) / 12
        return [round(a), round(b), round(b / a * 100 - 100)] if a else None
    eve = sorted(([st] + chg(st, range(17, 21)) for st in SOFF if chg(st, range(17, 21)) and chg(st, range(17, 21))[0] > 150000), key=lambda r: -r[3])
    home = sorted(([st] + chg(st, LATE) for st in SOFF if chg(st, LATE) and chg(st, LATE)[0] > 60000), key=lambda r: r[3])
    G = J('gen-trend.json')['files']; H = {}
    for k, v in G['4_음주사고_시간대별']['series'].items():
        a = k.split('|')
        if a[0] == '음주운전 교통사고 건수': H[a[2].replace('시간대 ', '')] = {y: x for y, x in v}
    acc = []
    for y in sorted(set(yy for d in H.values() for yy in d)):
        t = sum(d.get(y, 0) for d in H.values())
        if t: acc.append([y, t, round(sum(H[b].get(y, 0) for b in ('18-20시', '20-22시')) / t * 100, 1), round(sum(H[b].get(y, 0) for b in ('22-24시', '0-2시', '2-4시')) / t * 100, 1), round(H['0-2시'].get(y, 0) / t * 100, 1), round(sum(H[b].get(y, 0) for b in ('6-8시', '8-10시')) / t * 100, 1)])
    C = J('dui-catch.json')['years']; catch = []
    for y in sorted(C):
        h = C[y]['hour']; n = sum(h)
        catch.append([int(y), n, round(sum(h[20:22]) / n * 100, 1), round(sum(h[22:24]) / n * 100, 1), round(sum(h[0:2]) / n * 100, 1), round(sum(h[2:6]) / n * 100, 1), round(sum(h[6:10]) / n * 100, 1), h.index(max(h))])
    NT = J('night-trend-seoul.json')['seoul']; NR = J('night-ride-seoul.json')
    def ser(fn, key): return [[r[0], r[1]] for k, v in G[fn]['series'].items() if all(x in k for x in key) for r in v][:60]
    doc = {'schema': 'tg-night-shift/1', 'made': datetime.date.today().isoformat(),
           'reading': '「얼마나 마시나」는 거의 그대로이고(월간음주율·폭음률 −2%p 안팎 · 고위험음주율은 12~13%대에서 제자리 · 출고량 −13%) 「밤늦게 밖에 있나」는 많이 줄었다 — 덜 마신다기보다 일찍 끝낸다로 읽힌다(이 지도가 붙인 풀이 · 자료가 까닭을 말해 주지는 않는다)',
           'source': '① 서울 열린데이터광장 지하철 호선별 역별 시간대별 승하차(CardSubwayTime) ② 서울시 상권분석서비스 추정매출(data/night-trend-seoul.json) ③ 도로교통공단 TAAS 음주운전 교통사고 요일별·시간대별 ④ 경찰청 음주운전 적발(공공데이터포털 15043308 · data/dui-catch.json) ⑤⑦ 질병관리청 국민건강영양조사 ⑥ 국세청 국세통계(③⑤⑥⑦ = data/gen-trend.json)',
           'note': ['**한 자료로는 까닭을 모른다 — 출처가 다른 자료가 같은 쪽을 가리키는지를 본다.** 지하철(교통카드) · 카드 매출 · 사고(경찰 DB) · 적발(경찰청) · 설문(질병청) · 출고(국세청)는 서로 무관하게 모인 자료다',
                    '같이 움직인 것들: 회식 문화 · 재택·유연근무 · 물가 · 심야 영업 축소 · 대리운전·택시 · 2019-06 단속 기준 강화(0.05 → 0.03%) · 2020~2021 영업시간 제한 — 어느 것이 얼마만큼인지 가르지 못한다',
                    '지하철: 민자 노선(신분당선·GTX) 없음 · 달 단위(평일·주말을 못 가름) · 심야 연장 운행이 2020년에 멈췄다 다시 시작된 때가 있다(0~1시 값에 영향 — 날짜는 확인하지 못했다) · 역 표에서는 전체 승하차가 35% 넘게 준 역(운영·집계 범위가 바뀐 역)을 뺐다',
                    '적발의 시각은 「언제 단속했나」에도 달려 있다(단속을 일찍 하면 일찍 걸린다) — 사고의 시각(③)과 같이 본다',
                    '고위험음주율은 줄지 않았다 — 19세 이상 12.1%(2019) → 12.7%(2024)로 12~13%대를 오간다(2019년이 낮은 해였다 · 남자 18.7 → 18.6 · 여자 5.6 → 6.7%). 「많이 마시는 사람」은 그대로라는 뜻이다',
                    '밤이 짧아졌다고 음주운전 위험이 없어진 것이 아니다 — 음주 사고의 41% 는 여전히 22~04시에 난다(2025)'],
           'fields': {'subway_hours': 'night-ride-seoul.json 의 hours 를 본다(해마다 0~23시 한 달 평균 승차)', 'subway_months': '[[연월, 밤 22~03시 승차 몫 %, 그 승차 수]…] 2019-01 ~',
                      'subway_dec': '[[해, 12월 밤 22~03시 승차 수, 그 몫 %, 12월 ÷ 11월(연말에 얼마나 더 타나)]]',
                      'subway_evening_in': '[[역, 2019 저녁 17~20시 하차 한 달 평균, 2025, 변화 %]] — 저녁에 모이는 곳(는 차례)', 'subway_night_home': '[[역, 2019 밤 22~03시 하차 한 달 평균, 2025, 변화 %]] — 밤늦게 돌아가는 곳(준 차례)',
                      'sales': '[[분기, 매출 억, 주점·유흥 비중 %, 밤 21~06시 비중 %]](서울 상권)', 'dui_acc': '[[해, 음주운전 사고 건수(전국), 18~22시 몫 %, 22~04시 몫 %, 0~2시 몫 %, 아침 6~10시 몫 %]]',
                      'dui_catch': '[[해, 적발 건수(전국), 20~22시 %, 22~24시 %, 0~2시 %, 2~6시 %, 아침 6~10시 %, 가장 많이 걸린 시]]', 'drink': '{지표: [[해, 값 %]]}(19세 이상 전체)', 'liquor': '[[해, 주류 출고량 ㎘]]', 'dui_exp': '[[해, 연간 음주운전 경험률 %]]'},
           'subway_months': months, 'subway_dec': dec, 'subway_evening_in': eve[:25] + eve[-15:], 'subway_night_home': home[:25] + home[-15:], 'subway_years': NR['seoul'],
           'sales': [[r[0], r[1], r[2], r[3]] for r in NT], 'dui_acc': acc, 'dui_catch': catch,
           'drink': {'월간음주율': ser('1_월간음주율', ['|전체|19세이상|']), '월간폭음률': ser('1_월간폭음률', ['|전체|19세이상|']), '고위험음주율': ser('1_고위험음주율', ['|전체|19세이상|'])},
           'liquor': [[r[0], r[1]] for k, v in G['7_주류출고량']['series'].items() if '합계' in k for r in v], 'dui_exp': ser('2_음주운전경험률', ['|전체|19세이상|'])}
    p = os.path.join(ROOT, 'data', 'night-shift.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('바이트', os.path.getsize(p))
    print('12월', dec); print('저녁에 모이는 곳(는)', eve[:8]); print('저녁에 모이는 곳(준)', eve[-8:]); print('밤늦게 돌아가는 곳(준)', home[:8]); print('사고', [a for a in acc if a[0] in (2010, 2019, 2025)]); print('적발', [c for c in catch if c[0] in (2010, 2019, 2024)])
if __name__ == '__main__': main()
