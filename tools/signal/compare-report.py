# -*- coding: utf-8 -*-
"""쌓인 대조 묶음 보기(07_API키/out/compare/acc-*.json · compare_acc.py 가 쌓음) — 시간대별로 가르고가 카카오보다 얼마나 짧게/길게 잡는지 · 같은 길 몫 · 엉뚱한 길 몫

  py -3.12 -X utf8 tools/signal/compare-report.py [며칠(기본 7)]
화면에만 찍는다 · 칸 건수 3 미만은 보이지 않는다 · 지난 날 칸은 가운데값·사분위만 남아 날을 합친 사분위는 어림(소유자 2026-10-15 「묶은 값만」) · 비율만 다룬다(시각·우리 값·카카오 원래 값은 쌓여 있지 않다)
"""
import os, sys, json, glob, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'compare')
BANDS = ['출근', '낮', '퇴근', '저녁', '밤']


def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p; a = int(k); b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 7
    t0 = (dt.datetime.now() - dt.timedelta(days=days)).strftime('%Y%m%d')
    C = {}
    for f in sorted(glob.glob(os.path.join(OUT, 'acc-*.json'))):
        if os.path.basename(f)[4:12] < t0:
            continue
        try:
            A = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for k, v in A.get('cells', {}).items():
            if v.get('n', 0) < 3:
                continue   # 한 번의 값이 그대로 드러나는 작은 칸은 안 본다
            kind, kd, bd, key = k.split('|')
            g = C.setdefault((kind, kd, bd), {'n': 0, 'cells': 0})
            g['n'] += v['n']; g['cells'] += 1
            for nm, x in v.items():
                if isinstance(x, list):
                    g.setdefault(nm, []).extend(x)
                elif isinstance(x, dict) and 'q' in x:   # 지난 날 칸 = [가운데값, 25%, 75%, 건수] — 날을 합칠 때는 가운데값을 건수만큼 넣어 어림
                    g.setdefault(nm, []).extend([x['q'][0]] * int(x['q'][3]))
                elif nm != 'n':
                    g[nm] = g.get(nm, 0) + x
    if not C:
        print('보일 묶음이 없다(칸마다 3건이 넘어야 보인다) —', OUT); return 1
    f2 = lambda x: '-' if x is None else '%.2f' % x
    print('대조 묶음(최근 %d일 · 칸 3건 이상만)' % days)
    print()
    print('■ 길 짝 — 같은 길(겹침 70% 넘게)일 때 시간 = 가르고 ÷ 카카오 (1 아래 = 가르고가 짧게 잡음)')
    print('%-6s %-4s %5s %6s %6s %6s %8s %6s' % ('요일', '시간대', '건수', '25%', '가운데', '75%', '같은 길', '엉뚱'))
    for kd in ('평일', '토', '일·공휴'):
        for bd in BANDS:
            g = C.get(('route', kd, bd))
            if g:
                print('%-6s %-4s %5d %6s %6s %6s %7d%% %5d%%' % (kd, bd, g['n'], f2(q(g.get('rts', []), .25)), f2(q(g.get('rts', []), .5)), f2(q(g.get('rts', []), .75)), round(100 * g.get('same', 0) / g['n']), round(100 * g.get('far', 0) / g['n'])))
    print()
    print('■ 고정 구간 — 카카오 ÷ 우리 계산(제한속도+신호) · 배율 전 / 막힘 배율 곱한 뒤(1 근처면 맞음)')
    print('%-6s %-4s %5s %8s %10s' % ('요일', '시간대', '건수', '배율 전', '배율 뒤'))
    for kd in ('평일', '토', '일·공휴'):
        for bd in BANDS:
            g = C.get(('seg', kd, bd))
            if g:
                print('%-6s %-4s %5d %8s %10s' % (kd, bd, g['n'], f2(q(g.get('rk', []), .5)), f2(q(g.get('rkc', []), .5))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
