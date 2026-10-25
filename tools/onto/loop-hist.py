# -*- coding: utf-8 -*-
# 🔁 막힘 고리 — 지난 막힘 실측(2026-10-25 · 소유자 「다 하나로 · 유기적으로」 — 형님 현장 말 「주말 저녁마다 반복」을 쌓인 속도로 맞대 본다)
#   07_API키/out/livespd/<날짜>.jsonl.gz(이 PC 가 약 11분마다 받은 ITS 통행속도) × data/onto-loops.json 의 네 변
#   → 네 변 중 셋 이상이 TH km/h 이하인 받은 때가 MIN_SNAPS 번 넘게 이어지면 「고리 막힘」 한 토막
#   → 토막마다 시작·끝·이어진 받은 때 수 · 변마다 가장 느린 값 · 먼저 막힌 변 차례(토막 시작 앞 60분 안에서 처음 TH 이하가 된 때)
#   → 날마다 저녁(15~22시) 받은 기록이 있었나(없으면 「기록 빔」 — 막힘이 없었다는 뜻이 아니다)
#   통행속도는 공개 자료(ITS) — 도달 시간·출동 지연이 아니다(공개 금지 자료 아님)
#   py -3.12 -X utf8 tools/onto/loop-hist.py   → data/onto-loop-hist.json
import os, json, datetime, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TH, MIN_SNAPS, GAP = 10, 2, 1500   # km/h · 이어진 받은 때 수 · 받은 때 사이가 25분 넘으면 끊김으로 본다
EVE = (15, 22)

spec = importlib.util.spec_from_file_location('ae', os.path.join(ROOT, 'tools', 'onto', 'act-effect.py'))
ae = importlib.util.module_from_spec(spec); spec.loader.exec_module(ae)   # 고리 변 링크·쌓인 기록 읽는 셈은 act-effect 와 한 곳


def legv(m, ls):
    v = [m[l] for l in dict.fromkeys(ls) if l in m][:2]
    return round(sum(v) / len(v), 1) if v else None


def main():
    S = ae.snaps(); LL = ae.leg_links()
    out = {'schema': 'tg-onto-loop-hist/1', 'made': datetime.date.today().isoformat(),
           'source': '국가교통정보센터(ITS) 실시간 소통정보를 이 PC 가 약 11분마다 받아 쌓은 것(07_API키/out/livespd) × data/onto-loops.json 네 변 — tools/onto/loop-hist.py',
           'fields': 'rule{th km/h, legs 몇 변 이상, snaps 이어진 받은 때 수} · from·to 쌓인 기록 처음·끝 · loops{고리 id: {ep[{d 날짜, w 요일, b 시작, e 끝, n 받은 때 수, min[변마다 가장 느린 km/h], first[먼저 막힌 변 번호 차례 · 0부터 = onto-loops legs 차례]}], days[{d, w, eve 저녁 15~22시 받은 때 수, ep 그날 막힘 토막 수}]}}',
           'note': ['「고리 막힘」 = 네 변 중 셋 이상이 %d km/h 이하인 받은 때가 %d 번 넘게 이어짐 — 앱이 정한 문턱(어림)이지 공식 기준이 아니다' % (TH, MIN_SNAPS - 1),
                    '받은 때 사이는 약 11분 — 시작·끝은 그 간격만큼 어긋날 수 있다',
                    '저녁 받은 기록이 없는 날(eve 0)은 막힘이 없었다는 뜻이 아니다(PC 가 꺼져 못 받음)'],
           'rule': {'th': TH, 'legs': 3, 'snaps': MIN_SNAPS},
           'from': datetime.datetime.fromtimestamp(S[0][0]).strftime('%Y-%m-%d %H:%M') if S else None,
           'to': datetime.datetime.fromtimestamp(S[-1][0]).strftime('%Y-%m-%d %H:%M') if S else None, 'loops': {}}
    W = '월화수목금토일'
    for lid, (L, legs) in LL.items():
        rows = [(a, [legv(m, ls) for ls in legs]) for a, m in S]
        hit = [sum(1 for x in v if x is not None) >= 3 and sum(1 for x in v if x is not None and x <= TH) >= 3 for a, v in rows]
        eps, i = [], 0
        while i < len(rows):
            if not hit[i]: i += 1; continue
            j = i
            while j + 1 < len(rows) and hit[j + 1] and rows[j + 1][0] - rows[j][0] <= GAP: j += 1
            if j - i + 1 >= MIN_SNAPS:
                a0, a1 = rows[i][0], rows[j][0]; t0 = datetime.datetime.fromtimestamp(a0)
                mins = [min((v[k] for a, v in rows[i:j + 1] if v[k] is not None), default=None) for k in range(len(legs))]
                fst = {}
                for a, v in rows:
                    if a0 - 3600 <= a <= a0:
                        for k, x in enumerate(v):
                            if x is not None and x <= TH and k not in fst: fst[k] = a
                out_ep = {'d': t0.strftime('%Y-%m-%d'), 'w': W[t0.weekday()], 'b': t0.strftime('%H:%M'), 'e': datetime.datetime.fromtimestamp(a1).strftime('%H:%M'),
                          'n': j - i + 1, 'min': mins, 'first': [k for k, a in sorted(fst.items(), key=lambda x: (x[1], x[0]))]}
                eps.append(out_ep)
            i = j + 1
        days = {}
        for a, v in rows:
            t = datetime.datetime.fromtimestamp(a); d = t.strftime('%Y-%m-%d')
            x = days.setdefault(d, {'d': d, 'w': W[t.weekday()], 'eve': 0, 'ep': 0})
            if EVE[0] <= t.hour < EVE[1]: x['eve'] += 1
        for e in eps: days[e['d']]['ep'] += 1
        out['loops'][lid] = {'ep': eps, 'days': [days[k] for k in sorted(days)]}
        print(lid, '토막', len(eps), '· 날', len(days), ' '.join('%s(%s) %s~%s' % (e['d'][5:], e['w'], e['b'], e['e']) for e in eps))
    p = os.path.join(ROOT, 'data', 'onto-loop-hist.json')
    json.dump(out, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('→', p, os.path.getsize(p), 'B')


if __name__ == '__main__':
    main()
