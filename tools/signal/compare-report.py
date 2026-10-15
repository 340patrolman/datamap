# -*- coding: utf-8 -*-
"""쌓인 대조 결과 보기(07_API키/out/compare/*.jsonl) — 시간대별로 가르고가 카카오보다 얼마나 짧게/길게 잡는지 · 엉뚱한 길 몫 · 같은 길 몫

  py -3.12 -X utf8 tools/signal/compare-report.py [며칠(기본 7)]
화면에만 찍는다 · 비율만 다룬다(카카오 원래 값은 쌓여 있지 않다)
"""
import os, sys, json, glob, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'compare')


def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p; a = int(k); b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)


def band(h):
    return '출근 07~09' if 7 <= h < 10 else '낮 10~16' if 10 <= h < 17 else '퇴근 17~19' if 17 <= h < 20 else '저녁 20~22' if 20 <= h < 23 else '밤'


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 7
    t0 = (dt.datetime.now() - dt.timedelta(days=days)).strftime('%Y%m%d')
    R, S = [], []
    for f in sorted(glob.glob(os.path.join(OUT, '*-*.jsonl'))):
        b = os.path.basename(f); kind, d = b.split('-')[0], b.split('-')[1][:8]
        if d < t0:
            continue
        for ln in open(f, encoding='utf-8'):
            try:
                j = json.loads(ln)
            except Exception:
                continue
            (R if kind == 'route' else S).append(j)
    if not R and not S:
        print('쌓인 대조가 없다 —', OUT); return 1
    f2 = lambda x: '-' if x is None else '%.2f' % x
    print('대조 결과(최근 %d일) — 길 짝 %d줄 · 구간 %d줄' % (days, len(R), len(S)))
    print()
    print('■ 같은 길을 고른 짝(겹침 70% 넘게)의 시간 = 가르고 ÷ 카카오 (1 아래 = 가르고가 짧게 잡음)')
    print('%-10s %5s %6s %6s %6s %8s %8s' % ('시간대', '줄', '25%', '가운데', '75%', '같은 길', '엉뚱'))
    for bd in ('출근 07~09', '낮 10~16', '퇴근 17~19', '저녁 20~22', '밤'):
        rr = [j for j in R if band(int(j['t'][11:13])) == bd]
        if not rr:
            continue
        same = [j['rt'] for j in rr if min(j['ov_k'], j['ov_g']) >= 0.7]
        print('%-10s %5d %6s %6s %6s %7d%% %7d%%' % (bd, len(rr), f2(q(same, .25)), f2(q(same, .5)), f2(q(same, .75)), round(100 * len(same) / len(rr)), round(100 * sum(1 for j in rr if j.get('far')) / len(rr))))
    far = [j for j in R if j.get('far')]
    if far:
        print()
        print('■ 엉뚱한 길(가르고 거리 > 카카오 × 1.3) — 짝별 횟수')
        c = {}
        for j in far:
            c[(j['pair'], j['from'], j['to'])] = c.get((j['pair'], j['from'], j['to']), 0) + 1
        for (p, a, b), n in sorted(c.items(), key=lambda x: -x[1]):
            print('  %2d %s → %s : %d번' % (p, a, b, n))
    if S:
        print()
        print('■ 고정 구간(교차로 사이) — 카카오 ÷ 우리 계산(제한속도+신호) · 배율 전 / 막힘 배율 곱한 뒤')
        print('%-10s %5s %6s %6s %6s %10s %10s' % ('시간대', '줄', '25%', '가운데', '75%', '배율 뒤 가운데', '막힘 배율'))
        for bd in ('출근 07~09', '낮 10~16', '퇴근 17~19', '저녁 20~22', '밤'):
            ss = [j for j in S if band(int(j['t'][11:13])) == bd]
            if ss:
                print('%-10s %5d %6s %6s %6s %10s %10s' % (bd, len(ss), f2(q([j['rk'] for j in ss], .25)), f2(q([j['rk'] for j in ss], .5)), f2(q([j['rk'] for j in ss], .75)), f2(q([j['rkc'] for j in ss if j.get('rkc')], .5)), f2(q([j.get('calF', 1) for j in ss], .5))))
        print('  읽는 법: 「배율 뒤 가운데」가 1 근처면 실시간 없는 길의 지도·가르고 시간(제한속도 ÷ 배율 + 신호)이 카카오와 맞는다 · 1 보다 크면 아직 짧게 잡는다')
    return 0


if __name__ == '__main__':
    sys.exit(main())
