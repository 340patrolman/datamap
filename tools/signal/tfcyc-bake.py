# -*- coding: utf-8 -*-
# 🚦 tfcyc-bake — T-Data 신호 하루치 파일(10382 · NAS datamap-raw/tdata_file) 여러 날 → (교차로, 요일 갈래, 시) 주기 어림 → 수집기 시각대 표(sigdir pl)와 맞대기
#   (2026-11-21 · 파일은 교차로마다 「8분마다 1분 창」이라 수집기 reduce_one 이 거의 못 읽는다 → 다른 길)
#   창마다 이동류 색이 바뀐 순간의 잔여 = 그 색 전체 길이 → 녹+황+적 = 주기(이동류마다) · 같은 갈래 여러 날을 모아 가운데값
#   → 그 근처(±6초 · 0.5초 걸음)에서 「바뀌는 때」 사건들이 주기로 한 점에 가장 잘 모이는 값으로 다듬는다(합성 길이)
#   받아들이는 조건: 이동류 NAG 개 이상이 ±TOL 안에서 같은 주기 · 40~250초 · 사건이 다듬은 주기로 모임 R ≥ RMIN
#   시험(11-12·16·17·19 월~목 4일): 기본값(RMIN 0.995 · NAG 3) 어림 12,811칸 · 수집기 칸과 대조 10,709 · 맞음 96.9% · 수집기에 없는 칸 2,102
#     (RMIN 0.99 · NAG 2 면 21,444칸 · 95.7% · 새 칸 3,514) — 어긋남은 대개 수집기 칸이 옛 날짜 계획인 곳(1·2시 140 ↔ 120 등) 이거나 +3~4초 치우침
#   ⚠ 이것은 주기만이다 — 지도·가르고 신호값(red/sigdir)에는 아직 넣지 않는다(녹색 자리 o·닻 a 를 이 꼴로 만들면 build 의 시각대 표와 섞여 위험 · 독립 검수 뒤)
#   결과: 07_API키/out/tdata/file_cyc/file_cyc.json(저장소 밖) · 날마다 모은 사건 <날짜>.pkl(다시 돌릴 때 빠름)
#   py -3.12 -X utf8 tools/signal/tfcyc-bake.py [YYYYMMDD …]   (없으면 NAS 의 날 전부 · 하루 약 3분)
import zipfile, io, collections, os, json, sys, math, datetime, pickle
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NAS = r'\\NAS-baranno815\home\datamap-raw\tdata_file'
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'tdata', 'file_cyc')
G_ = ('protected-Movement-Allowed', 'permissive-Movement-Allowed')
TOL = 2
RMIN = float(os.environ.get('RMIN', '0.995'))
NAG = int(os.environ.get('NAG', '3'))


def cls_of(d):
    w = d.isoweekday() % 7   # 0 일 … 6 토 → 갈래 0 월~목 · 1 금 · 2 토 · 3 일 (spat-bake cls_of 와 같게 · 특수일은 아래에서 뺀다)
    return 3 if w == 0 else 2 if w == 6 else 1 if w == 5 else 0


def one(day):
    pk = os.path.join(OUT, day + '.pkl')
    if os.path.exists(pk):
        return pickle.load(open(pk, 'rb'))
    z = zipfile.ZipFile(os.path.join(NAS, 'signalPhaseTimeFusion_%s.zip' % day)); f = io.TextIOWrapper(z.open(z.infolist()[0]), encoding='utf-8', errors='replace')
    H = f.readline().rstrip('\n').split(','); iU, iI, iH = H.index('TRSM_UTC_TIME'), H.index('ITST_ID'), H.index('TRSM_HR')
    mv = [(H.index(c), H.index(c.replace('RMDR_CS', 'STAT_NM')), c[:7]) for c in H if c.endswith('_RMDR_CS') and 'PDSG' not in c]
    dur = collections.defaultdict(list); ev = collections.defaultdict(list); prev = {}
    for line in f:
        q = line.rstrip('\n').split(',')
        if len(q) < 60:
            continue
        try:
            t = int(q[iU]) / 1000.0; h = int(q[iH])
        except ValueError:
            continue
        i = q[iI]
        for jr, js, m in mv:
            r = q[jr]; s = q[js]
            if not r or not s:
                continue
            c = 'G' if s in G_ else ('R' if s[0] == 's' else 'Y')
            k = (i, m); pv = prev.get(k)
            if pv and pv[1] != c and t - pv[0] <= 3.0:
                dur[(i, h, m, c)].append(int(r) / 10.0 + (t - pv[0]) / 2)   # 바뀐 순간의 잔여 + 앞 줄과의 틈 절반
            prev[k] = (t, c)
            if c != 'Y':
                L = ev[(i, h, m, c)]; nx = t + int(r) / 10.0
                if not L or abs(L[-1] - nx) > 1.5:
                    L.append(round(nx, 1))
    res = (dict(dur), dict(ev)); pickle.dump(res, open(pk, 'wb')); print(day, '읽음', len(dur), flush=True)
    return res


def med(a):
    a = sorted(a); return a[len(a) // 2]


def main(days):
    os.makedirs(OUT, exist_ok=True)
    days = days or sorted(f[22:30] for f in os.listdir(NAS) if f.startswith('signalPhaseTimeFusion_') and f.endswith('.zip'))
    hol = set()
    try:
        import importlib.util
        sp = importlib.util.spec_from_file_location('spat', os.path.join(ROOT, 'tools', 'signal', 'spat-bake.py')); SP = importlib.util.module_from_spec(sp); sp.loader.exec_module(SP)
        hol = SP.holidays()
    except Exception:
        pass
    acc = collections.defaultdict(lambda: collections.defaultdict(list)); evd = collections.defaultdict(list)
    for d in days:
        dt = datetime.datetime.strptime(d, '%Y%m%d')
        cl = 3 if dt.strftime('%Y-%m-%d') in hol else cls_of(dt)
        dur, ev = one(d)
        for (i, h, m, c), L in dur.items():
            acc[(i, cl, h)][(m, c)] += L
        for (i, h, m, c), L in ev.items():
            evd[(i, cl, h, d)].append(L)
    est = {}
    for key, D in acc.items():
        cs = [med(L) + med(D[(m, 'Y')]) + med(D[(m, 'R')]) for (m, c), L in D.items() if c == 'G' and D.get((m, 'Y')) and D.get((m, 'R'))]
        if len(cs) < 2:
            continue
        C = med(cs)
        if not 40 <= C <= 250 or sum(1 for x in cs if abs(x - C) <= TOL) < NAG:
            continue
        LL = [L for d in days for L in evd.get(key + (d,), []) if len(L) >= 2]
        if not LL:
            continue

        def Rof(C):
            t = n = 0
            for L in LL:
                t += math.hypot(sum(math.cos(2 * math.pi * x / C) for x in L), sum(math.sin(2 * math.pi * x / C) for x in L)); n += len(L)
            return t / n if n else 0
        C = max((c2 / 2.0 for c2 in range(max(80, int(2 * C) - 12), int(2 * C) + 13)), key=Rof)
        if Rof(C) < RMIN:
            continue
        est[key] = round(C)
    pl = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))['pl']
    n = ok = new = 0; bad = []
    for (i, cl, h), C in est.items():
        rows = [x for x in pl.get(i, []) if x[0] == cl and x[1] == h]
        if not rows:
            new += 1; continue
        n += 1; g = abs(rows[0][2] - C) <= TOL; ok += g
        if not g and len(bad) < 12:
            bad.append((i, cl, h, C, rows[0][2]))
    print('날', len(days), '어림', len(est), '수집기 칸과 대조', n, '맞음', ok, round(100.0 * ok / max(1, n), 1), '%', '수집기에 없는 칸', new, flush=True)
    print('어긋난 보기(교차로, 갈래, 시, 파일 주기, 수집기 주기)', bad)
    json.dump({'schema': 'tg-tfile-cyc/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'days': days, 'rule': 'TOL %s RMIN %s NAG %s' % (TOL, RMIN, NAG),
               'agree_pct': round(100.0 * ok / max(1, n), 1), 'n_cmp': n, 'n_new': new,
               'fields': 'est = {"교차로|요일 갈래(0 월~목·1 금·2 토·3 일·공휴일)|시": 주기(초)}', 'est': {'%s|%d|%d' % k: v for k, v in est.items()}},
              open(os.path.join(OUT, 'file_cyc.json'), 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main(sys.argv[1:])
