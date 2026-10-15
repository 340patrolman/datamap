# -*- coding: utf-8 -*-
# 주행시간 대조 — 처음 보는 길에서도 맞나(구간 하나씩 빼고 나머지로 ITS 배율을 만들어 그 구간을 맞혀 봄 · 2026-10-15 소유자 「보정이 필요 · 대조도 해 보고」)
#   원자료 = etacal-its.py 가 만드는 줄(ITS 실측 · 제한속도 · 신호 기다림) · 결과는 화면에만 · 카카오 값 안 씀
#   py -3.12 -X utf8 tools/signal/eta-holdout.py
import sys, importlib.util, statistics as st, collections
sys.argv = ['etacal-its.py', '--bake']
spec = importlib.util.spec_from_file_location('E', __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "etacal-its.py"))
E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
CAP = {}
E.bake = lambda rows, days, hol: CAP.update(rows=rows)
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    E.main()
R = [r for r in CAP['rows'] if r.get('its') and r.get('lim')]
segs = sorted(set(r['id'] for r in R))
def drive(r): return max(1.0, r['its'] - (r['sig'] - r['lim']) - 8)
def err(p, a): return abs(p / a - 1)
E0, E1, E2, W = [], [], [], collections.defaultdict(list)
for s in segs:
    tr = [r for r in R if r['id'] != s]; te = [r for r in R if r['id'] == s]
    f = {}
    for k in set((r['kind'], r['band']) for r in tr):
        f[k] = st.median([drive(r) / r['lim'] for r in tr if (r['kind'], r['band']) == k])
    for r in te:
        fk = f.get((r['kind'], r['band']))
        if not fk: continue
        p0 = r['sig']; p1 = r['lim'] * fk + (r['sig'] - r['lim']) + 8
        E0.append(err(r['lim'], r['its'])); E1.append(err(p0, r['its'])); E2.append(err(p1, r['its']))
        W[s].append((err(p0, r['its']), err(p1, r['its']), p1 / r['its']))
q = lambda v, p: sorted(v)[int(p * (len(v) - 1))]
print('맞댄 줄', len(E2), '· 구간', len(W))
for nm, v in (('제한속도만', E0), ('제한속도+신호', E1), ('+ITS 배율(그 구간 빼고 보정)', E2)):
    print('%-28s 오차 가운데 %.0f%% · 80%% 안 %.0f%% · 30%% 넘게 틀림 %.0f%%' % (nm, 100 * q(v, .5), 100 * q(v, .8), 100 * sum(x > .3 for x in v) / len(v)))
print('구간별(보정 뒤 예측÷실측 가운데):', ' '.join('%s %.2f' % (s, st.median(x[2] for x in W[s])) for s in sorted(W)))
