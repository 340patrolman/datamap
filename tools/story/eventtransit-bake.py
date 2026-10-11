# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧩 완료된 사건을 **통행으로** 뒤돌아 보기: 개통 앞뒤 둘레 역의 승하차(소유자 2026-10-11 「완료 = 사후 검증」 · 아파트 값으로는 교통 사건이 가려지지 않아 통행으로 본다) → data/event-transit.json
#   재료 = ../07_API키/out/subway_month/<연월>.json — 서울 열린데이터광장 「서울시 지하철 호선별 역별 시간대별 승하차 인원 정보」(CardSubwayTime · 달마다 · 교통카드 · 키 keys.json seoul · http)
#   역마다 「그 달 승차+하차 ÷ 서울 전체 승차+하차」(전체가 오르내린 몫 — 감염병·계절 — 을 덜어 낸다)를 달마다, 사건 앞 열두 달 평균 → 뒤 열두 달 평균으로 견준다
#   **신분당선·GTX 는 이 자료에 없다**(민자 노선) — 새 노선 자체의 손님이 아니라 「둘레의 기존 노선 역이 어떻게 달라졌나」만 본다 · 환승은 개찰구를 안 지나 세어지지 않는다
#   「사건 때문」이라고 말하지 않는다 — 같은 때 다른 일(역세권 개발 · 버스 노선 · 다른 개통)이 겹칠 수 있다
#   py -3.12 -X utf8 tools/story/eventtransit-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subway_month')
EVS = [('EV-sinbundang-sinsa', '202205', [('3호선', '신사'), ('7호선', '논현'), ('9호선', '신논현'), ('2호선', '강남'), ('3호선', '양재(서초구청)'), ('2호선', '교대(법원.검찰청)'), ('3호선', '압구정'), ('7호선', '학동')]),
       ('EV-gtxa-suseo', '202403', [('분당선', '수서'), ('3호선', '수서'), ('3호선', '양재(서초구청)'), ('2호선', '강남'), ('3호선', '일원'), ('분당선', '대모산입구'), ('8호선', '가락시장'), ('분당선', '복정')])]
def ymadd(ym, n):
    y, m = int(ym[:4]), int(ym[4:]) + n
    while m > 12: y += 1; m -= 12
    while m < 1: y -= 1; m += 12
    return '%04d%02d' % (y, m)
def main():
    D = {}; TOT = collections.Counter()
    for f in sorted(glob.glob(os.path.join(SRC, '*.json'))):
        ym = os.path.basename(f)[:6]
        for r in json.load(open(f, encoding='utf-8')):
            t = sum(v for k, v in r.items() if k.startswith('HR_') and isinstance(v, (int, float))); D[(r['SBWY_ROUT_LN_NM'], r['STTN'], ym)] = t; TOT[ym] += t
    yms = sorted(TOT); EV = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'data', 'events-big.json'), encoding='utf-8'))['items']}; out = []
    for ev, ym0, sts in EVS:
        bef = [ymadd(ym0, -k) for k in range(12, 0, -1)]; aft = [ymadd(ym0, k) for k in range(1, 13)]; rows = []
        for line, st in sts:
            ser = [[ym, round(D[(line, st, ym)]), round(D[(line, st, ym)] / TOT[ym] * 1e4, 2)] for ym in yms if (line, st, ym) in D]
            if not ser: continue
            sh = {x[0]: x[2] for x in ser}; cn = {x[0]: x[1] for x in ser}; b = [sh[m] for m in bef if m in sh]; a = [sh[m] for m in aft if m in sh]; bc = [cn[m] for m in bef if m in cn]; ac = [cn[m] for m in aft if m in cn]
            if len(b) < 10 or len(a) < 10 or not sum(b) or not sum(bc): continue
            rows.append({'line': line, 'st': st, 'before': round(sum(bc) / len(bc)), 'after': round(sum(ac) / len(ac)), 'share_before': round(sum(b) / len(b), 2), 'share_after': round(sum(a) / len(a), 2),
                         'share_chg': round((sum(a) / len(a)) / (sum(b) / len(b)) * 100 - 100, 1), 'ser': [[x[0], x[2]] for x in ser if ymadd(ym0, -24) <= x[0] <= ymadd(ym0, 24)]})
        tb = sum(TOT[m] for m in bef) / 12; ta = sum(TOT[m] for m in aft) / 12
        out.append({'event': ev, 'nm': EV[ev]['nm'] if ev in EV else ev, 'ym': ym0, 'before': [bef[0], bef[-1]], 'after': [aft[0], aft[-1]], 'seoul_chg': round(ta / tb * 100 - 100, 1), 'stations': rows})
        print(EV[ev]['nm'] if ev in EV else ev, ym0, '· 서울 전체 %+.1f%%' % (ta / tb * 100 - 100)); [print('   %-5s %-12s 한 달 %7d → %7d · 서울 안 몫 %5.2f → %5.2f (%+.1f%%)' % (r['line'], r['st'], r['before'], r['after'], r['share_before'], r['share_after'], r['share_chg'])) for r in rows]
    doc = {'schema': 'tg-event-transit/1', 'made': datetime.date.today().isoformat(), 'months': [yms[0], yms[-1]],
           'source': '서울 열린데이터광장 「서울시 지하철 호선별 역별 시간대별 승하차 인원 정보」(CardSubwayTime · 교통카드 · 달마다) — 사건은 data/events-big.json',
           'note': ['**「개통 때문에 늘었다·줄었다」를 말하는 자료가 아니다** — 개통 앞 열두 달과 뒤 열두 달에 그 역의 승하차가 서울 전체에서 차지한 몫이 얼마나 달랐나만 보인다(같은 때 역세권 개발·버스 노선·다른 개통이 겹칠 수 있다)',
                    '몫 = 그 달 그 역(그 호선 개찰구)의 승차 + 하차 ÷ 서울 지하철 전체 × 10,000 — 전체가 같이 오르내린 것(감염병 회복 · 계절)을 덜어 낸 값이다',
                    '**새 노선(신분당선 · GTX-A)의 손님은 이 자료에 없다**(민자 노선은 빠져 있다) · 환승은 개찰구를 지나지 않아 세어지지 않는다 — 「새 노선으로 갈아타는 사람」은 안 보이고 「그 역 개찰구로 드나든 사람」만 보인다',
                    '2026-10-11 처음 본 것은 stations 의 share_chg(%) — 둘레 역과 견줄 다른 역을 같이 실었다'],
           'fields': 'events[{event, nm, ym 개통 연월, before[처음, 끝], after[처음, 끝], seoul_chg 서울 전체 승하차 변화 %, stations[{line, st, before·after 한 달 평균 승하차, share_before·share_after 서울 안 몫(만분율), share_chg 몫의 변화 %, ser[[연월, 몫]…](개통 앞뒤 두 해)}]}]',
           'events': out}
    p = os.path.join(ROOT, 'data', 'event-transit.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('바이트', os.path.getsize(p))
if __name__ == '__main__': main()
