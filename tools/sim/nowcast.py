# -*- coding: utf-8 -*-
# 실측 어림(nowcast) — 쌓인 ITS 실측만으로 「30·60분 뒤 이 길이 막혀 있을까」(2026-11-07 · 트윈 채점에서 갈라져 나옴)
#   까닭: 대기열 시뮬 트윈은 「그대로(지금 막힌 곳은 그 뒤에도 막힘)」 어림을 못 이겼다(twin-shadow · 30분 79.4% vs 84.8%).
#     같은 칸에서 지금 속도·30분 추세·그 길의 평소 막힘 비율(같은 날 종류·15분 칸)을 묶은 로지스틱 회귀는 그대로를 이긴다 —
#     시뮬 값(ob·ot·op)을 더해도 오르지 않았다(시뮬 구역 11곳 16:30~19:30 칸) → 「앞을 내다봄」은 이 실측 어림이 맡고 시뮬은 「바꿔 보면」에 쓴다.
#   쓰는 것: ../07_API키/out/livespd/<날짜>.jsonl.gz(약 11분마다 ITS 통행속도 · 길 약 9천) · data/holidays.json(공휴일 = 주말로)
#   판정: 홀수 날로 배우고 짝수 날로 판정(--swap 이면 반대) · 평소 막힘 비율은 배우는 날에서만, 배우는 날 자신의 값은 빼고 셈(새는 값 없음) · 막힘 = 6km/h 이하(트윈 채점과 같은 잣대)
#   t0 = 짝수 시 정각 · 내다보는 폭 30·60분 · 무게는 배우는 날에서 150만 칸 뽑아 경사 하강 400번
#   결과: data/nowcast-score.json(모은 칸 수만 · 길·시각별 실측 값은 안 담음) · 쓰기: py -3.12 -X utf8 tools/sim/nowcast.py [--swap]
#   ⚠ 개념 시연 — 예측·보증 아님 · 막힘이 드문 길이 대부분이라 「맞음 %」는 높게 나온다 → 틀린 칸이 얼마나 줄었나·바뀐 칸·헛막힘을 같이 본다
import os, sys, json, gzip, glob, datetime, math
import warnings
import numpy as np
warnings.filterwarnings('ignore', category=RuntimeWarning)
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
SPD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'livespd')
SWAP = '--swap' in sys.argv
BAKE = '--bake' in sys.argv   # 지도에 싣는 판 — 모든 날로 배워 data/nowcast.json(평소 막힘 비율 표 · 무게) 을 쓰고 끝(판정은 안 함 · 성적은 nowcast-score.json)
JAMV, NEAR, HZ = 6.0, 8 * 60, (1800, 3600)
HOLF = os.path.join(ROOT, 'data', 'holidays.json')
HOL = set()
if os.path.exists(HOLF):
    hj = json.load(open(HOLF, encoding='utf-8'))
    HOL = set(hj['days'].keys()) if isinstance(hj.get('days'), dict) else set(hj.get('days') or [])
D = {}
LID = {}
for f in sorted(glob.glob(os.path.join(SPD, '*.jsonl.gz'))):
    d = os.path.basename(f)[:8]; day = d[:4] + '-' + d[4:6] + '-' + d[6:]; rows = []
    for ln in gzip.open(f, 'rt', encoding='utf-8'):
        try: j = json.loads(ln)
        except ValueError: continue
        t = datetime.datetime.fromtimestamp(j['at']); rows.append((t.hour * 3600 + t.minute * 60 + t.second, j['m']))
        for k in j['m']:
            if k not in LID: LID[k] = len(LID)
    D[day] = sorted(rows, key=lambda r: r[0])
NL = len(LID); DAYS = sorted(D)
print('날', len(DAYS), '길', NL, flush=True)
S = {}
for d in DAYS:
    ts = np.array([t for t, _ in D[d]], float); V = np.full((len(ts), NL), np.nan, np.float32)
    for i, (_, m) in enumerate(D[d]):
        idx = [LID[k] for k in m]; V[i, idx] = [float(v) for v in m.values()]
    S[d] = (ts, V); D[d] = None
def wk(d): return 1 if datetime.date.fromisoformat(d).weekday() >= 5 or d in HOL else 0
def at(d, T):
    ts, V = S[d]
    if not len(ts): return None
    i = int(np.argmin(np.abs(ts - T)))
    return V[i] if abs(ts[i] - T) <= NEAR else None
train = (lambda d: True) if BAKE else (lambda d: (int(d[-2:]) % 2 == 1) != SWAP)
# 날마다 15분 칸 막힘 표(96 × 길) · 평소 = 배우는 날 합
FL = {}
for d in DAYS:
    ts, V = S[d]; F = np.full((96, NL), np.nan, np.float32); b = (ts // 900).astype(int)
    for k in range(96):
        sel = b == k
        if sel.any():
            with np.errstate(invalid='ignore'):
                jm = np.nanmean((V[sel] <= JAMV).astype(np.float32) + np.where(np.isnan(V[sel]), np.nan, 0), axis=0)
            F[k] = np.where(np.isnan(jm), np.nan, (jm >= .5).astype(np.float32))
    FL[d] = F
HS = np.zeros((2, 96, NL), np.float32); HN = np.zeros((2, 96, NL), np.float32)
for d in DAYS:
    if not train(d): continue
    F = FL[d]; ok = ~np.isnan(F); HS[wk(d)] += np.where(ok, F, 0); HN[wk(d)] += ok
# 길마다 자유 속도 = 배우는 날 90번째 백분위
allv = np.concatenate([S[d][1] for d in DAYS if train(d)], 0)
VF = np.nanpercentile(allv, 90, axis=0); VF = np.where(np.isnan(VF) | (VF < 10), 50, VF).astype(np.float32); del allv
def hist(d, b):
    w = wk(d); s, n = HS[w, b].copy(), HN[w, b].copy()
    if train(d):
        own = FL[d][b]; ok = ~np.isnan(own); s -= np.where(ok, own, 0); n -= ok
    return (s + .5) / (n + 1)
lg = lambda p: np.log(p / (1 - p))
X, Y, K, TR, HH, TT = [], [], [], [], [], []
for d in DAYS:
    for hr in range(0, 24, 2):
        t0 = hr * 3600
        v0 = at(d, t0)
        if v0 is None: continue
        vp = at(d, t0 - 1800) if t0 >= 1800 else None
        for h in HZ:
            if t0 + h >= 86400: continue
            v1 = at(d, t0 + h)
            if v1 is None: continue
            ok = ~np.isnan(v0) & ~np.isnan(v1)
            if not ok.any(): continue
            hf, h0 = hist(d, (t0 + h) // 900), hist(d, t0 // 900)
            j0 = (v0 <= JAMV).astype(np.float32); vpp = np.where(np.isnan(vp), v0, vp) if vp is not None else v0
            tr = (v0 - vpp) / VF; hv = (~np.isnan(vp)).astype(np.float32) if vp is not None else np.zeros(NL, np.float32)
            F = np.stack([j0, np.minimum(v0, 60) / 60, v0 / VF, tr, hv, lg(hf), lg(h0), lg(hf) - lg(h0), np.full(NL, wk(d)), np.full(NL, math.sin(2 * math.pi * hr / 24)), np.full(NL, math.cos(2 * math.pi * hr / 24)),
                          np.full(NL, h / 3600), ((v0 <= 10) & (v0 > JAMV)).astype(np.float32), ((v0 > JAMV) & (v0 <= 15)).astype(np.float32)], 1)[ok]
            X.append(F.astype(np.float32)); Y.append((v1[ok] <= JAMV).astype(np.int8)); K.append(j0[ok].astype(np.int8))
            TR.append(np.full(ok.sum(), train(d))); HH.append(np.full(ok.sum(), h, np.int32)); TT.append(np.full(ok.sum(), hr, np.int8))
X, Y, K, TR, HH, TT = (np.concatenate(a) for a in (X, Y, K, TR, HH, TT))
print('칸', len(Y), '막힘 비율', round(float(Y.mean()), 4), '바뀜 비율', round(float((Y != K).mean()), 4), flush=True)
names = ['j0', 'v0', 'v0/vf', '추세', '추세있음', '평소(h)', '평소(지금)', '평소차', '주말', 'sin', 'cos', '폭', '느림', '애매']

AL = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'   # 평소 막힘 비율 → 로짓 −5~+5 를 62칸으로(한 칸 약 0.16)
def enc(p):
    q = np.clip(np.round((np.log(p / (1 - p)) + 5) / 10 * 61), 0, 61).astype(int); return ''.join(AL[i] for i in q)
def bake():
    inv = {i: k for k, i in LID.items()}; P96 = (HS + .5) / (HN + 1); nev = HS.sum((0, 1)) == 0; dflt = [float(np.median(P96[w][:, nev])) if nev.any() else .03 for w in (0, 1)]
    Ptr = (f(X) >= th).astype(np.int8); gate = []
    for b in ((0, 6), (6, 10), (10, 16), (16, 20), (20, 24)):
        mt = (HH == 1800) & (TT >= b[0]) & (TT < b[1])
        if mt.sum() and (K[mt] == Y[mt]).sum() >= (Ptr[mt] == Y[mt]).sum(): gate.append(list(b))
    L = {}
    for i in range(NL):
        if HS[:, :, i].sum() == 0: continue   # 한 번도 막힌 적 없는 길 = 기본값(dflt)
        L[inv[i]] = [int(round(float(VF[i]))), enc(P96[0, :, i]), enc(P96[1, :, i])]
    vf0 = {}
    for i in range(NL):
        if inv[i] not in L and abs(float(VF[i]) - 50) > .5: vf0[inv[i]] = int(round(float(VF[i])))
    O = {'schema': 'tg-nowcast/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'days': [DAYS[0], DAYS[-1]], 'n_days': len(DAYS),
         'note': '30분 뒤 막힘(6km/h 이하) 어림 — 지금 ITS 속도·30분 추세·이 길 평소 막힘 비율(같은 날 종류 · 15분 칸)·시각 로지스틱 회귀 · 쌓인 ITS 실측으로 배움(tools/sim/nowcast.py --bake) · 개념 시연 — 예측·보증 아님 · 성적 = data/nowcast-score.json',
         'jam': JAMV, 'th': round(float(th), 3), 'gate': gate, 'feat': names, 'mu': [round(float(x), 5) for x in fit.mu], 'sd': [round(float(x), 5) for x in fit.sd], 'w': [round(float(x), 5) for x in w],
         'enc': 'links{ITS 링크: [자유 속도 km/h, 평일 96칸, 주말·공휴일 96칸]} · 칸 글자 = AL 의 자리 i → 로짓 = i/61×10−5 · 없는 길 = dflt(평일·주말) · vf0 = 표에 없는 길의 자유 속도(없으면 50)', 'AL': AL, 'dflt': [round(x, 4) for x in dflt], 'links': L, 'vf0': vf0}
    # 시험 사례(지도 관문이 js/nowcast.js 의 값과 맞대 봄) — 표에서 막힌 적 많은 길·처음 길 · 평일·주말 · 낮·저녁 · 지금 속도 여럿 · 30분 앞 값 없음
    def dec(id_, w_, b_):
        Lx = L.get(id_)
        if not Lx or b_ < 0 or b_ > 95: return O['dflt'][w_]
        return 1 / (1 + math.exp(-(AL.index(Lx[1 + w_][b_]) / 61 * 10 - 5)))
    def pyp(id_, v0, ymd, sec):
        dt = datetime.date.fromisoformat(ymd); w_ = 1 if dt.weekday() >= 5 or ymd in HOL else 0; hr = sec / 3600
        if any(g[0] <= int(hr) < g[1] for g in gate) or sec + 1800 >= 86400: return None
        vf = L[id_][0] if id_ in L else vf0.get(id_, 50); hf, h0 = dec(id_, w_, (sec + 1800) // 900), dec(id_, w_, sec // 900); lgx = lambda q: math.log(q / (1 - q))
        x = [1 if v0 <= JAMV else 0, min(v0, 60) / 60, v0 / vf, 0.0, 0, lgx(hf), lgx(h0), lgx(hf) - lgx(h0), w_, math.sin(2 * math.pi * hr / 24), math.cos(2 * math.pi * hr / 24), 0.5, 1 if JAMV < v0 <= 10 else 0, 1 if JAMV < v0 <= 15 else 0]
        z = O['w'][0] + sum((x[i] - O['mu'][i]) / O['sd'][i] * O['w'][i + 1] for i in range(len(x))); return 1 / (1 + math.exp(-z))
    top = sorted(L, key=lambda k: -float(HS[:, :, LID[k]].sum()))[:3]
    O['probe'] = []
    for id_ in top + [next(iter(vf0), top[0])]:
        for ymd, sec, v0 in (('2026-11-04', 18 * 3600 + 600, 9), ('2026-11-04', 8 * 3600 + 1200, 25), ('2026-11-08', 15 * 3600, 4), ('2026-11-04', 3 * 3600, 20)):
            pv = pyp(id_, v0, ymd, sec); O['probe'].append([id_, v0, ymd, sec, None if pv is None else round(pv, 6)])
    dst = os.path.join(ROOT, 'data', 'nowcast.json'); json.dump(O, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('→', dst, len(L), '길(막힌 적 있음) ·', os.path.getsize(dst), 'B · 문턱', O['th'], '· 그대로 띠', gate)
def fit(Xt, yt, l2=1e-3, it=400, lr=1.0):
    mu, sd = Xt.mean(0), Xt.std(0) + 1e-6; w = np.zeros(Xt.shape[1] + 1); Z = ((Xt - mu) / sd).astype(np.float64)
    for _ in range(it):
        z = Z @ w[1:] + w[0]; p = 1 / (1 + np.exp(-z)); e = p - yt
        g = np.r_[e.mean(), Z.T @ e / len(yt)] + l2 * np.r_[0, w[1:]]; w -= lr * g
    fit.mu, fit.sd = mu, sd
    return lambda Xs: 1 / (1 + np.exp(-(((Xs - mu) / sd) @ w[1:] + w[0]))), w
rng = np.random.default_rng(1); itr = np.where(TR)[0]; sub = rng.choice(itr, min(len(itr), 1500000), replace=False)
f, w = fit(X[sub], Y[sub].astype(np.float64))
ptr = f(X[sub]); th = max(np.arange(.2, .81, .02), key=lambda t: ((ptr >= t) == Y[sub]).mean())
if BAKE: bake(); sys.exit(0)
te = ~TR; P = (f(X[te]) >= th).astype(np.int8); Yt, Kt, Ht, Tt = Y[te], K[te], HH[te], TT[te]
# 시간 띠마다 고르기 — 배우는 날에서 그 띠·그 폭에 「그대로」가 어림보다 나으면 판정 날에도 그 띠는 그대로(밤 0~6시가 그랬다) · 판정 날 값은 안 봄
BANDS = ((0, 6), (6, 10), (10, 16), (16, 20), (20, 24)); GATE = {}
Ptr = (f(X[TR]) >= th).astype(np.int8); Ytr, Ktr, Htr, Ttr = Y[TR], K[TR], HH[TR], TT[TR]
for h in HZ:
    for b in BANDS:
        mt = (Htr == h) & (Ttr >= b[0]) & (Ttr < b[1])
        GATE[(h, b)] = 'keep' if mt.sum() and (Ktr[mt] == Ytr[mt]).sum() >= (Ptr[mt] == Ytr[mt]).sum() else 'now'
        if GATE[(h, b)] == 'keep': P[(Ht == h) & (Tt >= b[0]) & (Tt < b[1])] = Kt[(Ht == h) & (Tt >= b[0]) & (Tt < b[1])]
print('띠 고르기:', {'%d분 %02d-%02d' % (h // 60, b[0], b[1]): g for (h, b), g in GATE.items() if g == 'keep'})
del Ptr, Ytr, Ktr, Htr, Ttr
H0 = (X[te][:, 5] > 0).astype(np.int8)   # 평소만(그 시각 평소 막힘 비율 50%↑)
print('문턱 %.2f · 판정 날 %s' % (th, '홀수' if SWAP else '짝수'))
for h in HZ:
    m = Ht == h; ch = m & (Yt != Kt); jm = m & (Yt == 1)
    def sc(p): return '%.2f%% · 바뀐 칸 %d/%d · 막힘 맞힘 %d/%d · 헛막힘 %d' % (100 * (p[m] == Yt[m]).mean(), (p[ch] == Yt[ch]).sum(), ch.sum(), p[jm].sum(), jm.sum(), (p[m] & (1 - Yt[m])).sum())
    print('%d분 %d칸 | 그대로 %s\n        | 평소만 %s\n        | 어림 %s' % (h // 60, m.sum(), sc(Kt), sc(H0), sc(P)))
    for band in ((6, 10), (16, 20), (22, 24)):
        mb = m & (Tt >= band[0]) & (Tt < band[1])
        if mb.sum(): print('   %02d~%02d시 그대로 %.2f%% · 어림 %.2f%% (%d칸)' % (band[0], band[1], 100 * (Kt[mb] == Yt[mb]).mean(), 100 * (P[mb] == Yt[mb]).mean(), mb.sum()))
print('무게:', ' '.join('%s %+.2f' % z for z in sorted(zip(names, w[1:]), key=lambda z: -abs(z[1]))))

OUT = {'schema': 'tg-nowcast-score/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'days': [DAYS[0], DAYS[-1]], 'n_days': len(DAYS), 'links': NL,
       'judge': '홀수 날' if SWAP else '짝수 날', 'th': round(float(th), 2), 'gate': {'%d|%02d-%02d' % (h // 60, b[0], b[1]): g for (h, b), g in GATE.items()}, 'weights': {n: round(float(x), 3) for n, x in zip(names, w[1:])},
       'note': '실측 어림 = 지금 속도·30분 추세·평소 막힘 비율(배우는 날만 · 자기 날 뺌) 로지스틱 회귀 · 그대로 = 지금 상태가 이어진다 · 평소만 = 그 시각 평소 막힘 비율 50%↑ · 막힘 = 6km/h 이하 · 개념 시연 — 예측·보증 아님',
       'fields': {'n': '맞대 본 칸(길 × 시각)', 'hit': '맞은 칸', 'cn/ch': '지금과 그 뒤가 달라진 칸 / 맞힘', 'jn/jh': '실제 막힘 칸 / 맞힘', 'fa': '헛막힘(막힌다 했는데 안 막힘)'}, 'score': {}}
for h in HZ:
    m = Ht == h; ch = m & (Yt != Kt); jm = m & (Yt == 1); o = {}
    for nm_, p in (('keep', Kt), ('usual', H0), ('now', P)):
        o[nm_] = {'n': int(m.sum()), 'hit': int((p[m] == Yt[m]).sum()), 'cn': int(ch.sum()), 'ch': int((p[ch] == Yt[ch]).sum()), 'jn': int(jm.sum()), 'jh': int(p[jm].sum()), 'fa': int((p[m] & (1 - Yt[m])).sum())}
    bands = {}
    for band in ((6, 10), (10, 16), (16, 20), (20, 24), (0, 6)):
        mb = m & (Tt >= band[0]) & (Tt < band[1])
        if mb.sum(): bands['%02d-%02d' % band] = {'n': int(mb.sum()), 'keep': int((Kt[mb] == Yt[mb]).sum()), 'now': int((P[mb] == Yt[mb]).sum())}
    o['bands'] = bands
    OUT['score'][str(h // 60)] = o
import tempfile
dst = os.path.join(ROOT, 'data', 'nowcast-score.json') if not SWAP else os.path.join(tempfile.gettempdir(), 'nowcast-score-swap.json')   # 맞바꾼 판은 확인용(저장소에 안 씀)
json.dump(OUT, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('→', dst)
