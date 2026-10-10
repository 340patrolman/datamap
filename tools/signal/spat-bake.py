# -*- coding: utf-8 -*-
# 🚦 방향별 신호 — 서울 교통빅데이터(T-Data) V2X 신호 잔여시간(v2xSignalPhaseTimingInformation)에서
#    「어느 방향 · 무슨 신호 · 몇 초」를 읽어 data/sigdir-seoul.json 으로 굽는다.
#
#   py -3.12 -X utf8 tools/signal/spat-bake.py fetch 4034 4039 …   교차로 번호(C-ITS itstId)마다 한 번 받아 줄여 둔다
#   py -3.12 -X utf8 tools/signal/spat-bake.py fetch --list 파일     한 줄에 번호 하나
#   py -3.12 -X utf8 tools/signal/spat-bake.py build                 줄여 둔 것 → data/sigdir-seoul.json
#
# ⚠ 이 API 는 같은 키로 5분에 한 번만 불린다(V2X_REPEAT_CALL_LIMIT) · 하루 1,000건 — fetch 는 번호 사이에 305초를 쉰다.
# 키는 ../07_API키/keys.json 의 t_data_seoul 에서만 읽는다(찍지 않는다). 원자료·줄인 것은 저장소 밖 ../07_API키/out/tdata/ 에 둔다.
#
# 읽는 법(자료에 「지금 무슨 색」은 없다 — 그 API 는 따로 신청해야 한다):
#   · 한 이동류의 잔여시간은 1초마다 줄다가 상태가 바뀌면 새 값으로 뛴다 → 뛴 자리 사이가 한 구간.
#   · 차량 신호(직진·좌회전·유턴·버스)는 황색이 3~6초다 → 「황색 바로 앞 구간 = 녹색 · 바로 뒤 = 적색」으로 읽는다(추정이라고 화면에 밝힌다).
#   · 보행 신호는 황색이 없어 이 방법으로 색을 가릴 수 없다 → 구간 길이만 싣고 색은 비워 둔다.
#   · 36000(= 3600초)은 「모름」 · 5초 넘게 끊긴 자리(통신 끊김)에 걸친 구간은 버린다.
import sys, os, json, time, gzip, glob, datetime, statistics, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'tdata')
BASE = 'https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/v2xSignalPhaseTimingInformation/1.0'
BASEP = 'https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/v2xSignalPhaseInformation/1.0'   # 신호 상태(지금 무슨 색) — 잔여시간 API 와 5분 제한이 따로라 둘을 번갈아 받으면 두 배
DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw']
MVS = ['St', 'Lt', 'Ut', 'Bs', 'Bc', 'Pd']
GAP = 305
DENS0 = 0.998   # 교차로 하나가 1초에 쌓는 줄 수(2026-10-10 13시대 실측 0.997~0.998) — sweep 이 받은 쪽에서 다시 잰다


def key():
    return json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['t_data_seoul']


def call(itst, rows=1500):
    u = BASE + '?apikey=' + key() + '&pageNo=1&numOfRows=%d&itstId=%s' % (rows, itst)
    req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        r = urllib.request.urlopen(req, timeout=180)
        return r.status, r.read().decode('utf-8', 'ignore'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore'), dict(e.headers)


def cits():
    """서울 C-ITS 교차로 지도정보(v2xCrossroadMapInformation · 2026-09-10 받은 2,779곳) — 번호 → [위도, 경도, 이름]"""
    out = {}
    f = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱', 'data', 'cits_cross_2779_20260910.txt')
    if os.path.exists(f):
        for ln in open(f, encoding='utf-8'):
            a = ln.strip().split('|')
            if len(a) >= 4:
                try: out[a[0]] = [round(float(a[2]), 6), round(float(a[3]), 6), a[1]]
                except ValueError: pass
    return out


def scan():
    """정각 직후 한 번 — 그 시각에 값을 보내는 교차로 번호를 모두 센다(교차로마다 몇 줄뿐일 때 3만 줄을 한 번에)."""
    now = datetime.datetime.now()
    tgt = (now + datetime.timedelta(hours=1)).replace(minute=0, second=7, microsecond=0)
    time.sleep(max(0, (tgt - now).total_seconds()))
    u = BASE + '?apikey=' + key() + '&pageNo=1&numOfRows=30000'
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=300); st = r.status; b = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        st = e.code; b = e.read().decode('utf-8', 'ignore')
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M')
    if st != 200:
        print(stamp, 'scan HTTP', st, b[:200].replace(key(), '***'), flush=True); return []
    J = json.loads(b); ids = {}; comp = {}
    for x in J:
        i = str(x['itstId']); ids[i] = ids.get(i, 0) + 1
        comp.setdefault(i, set()).update(kk[:4] for kk, v in x.items() if kk.endswith('RmdrCs') and v is not None)
    json.dump({'at': stamp, 'rows': len(J), 'ids': ids, 'comp': {i: sorted(v) for i, v in comp.items()}}, open(os.path.join(RAW, 'ids_%s.json' % stamp), 'w', encoding='utf-8'))
    print(stamp, 'scan 줄', len(J), '교차로', len(ids), '(3만 줄에 걸렸으면 더 있다)' if len(J) >= 30000 else '', flush=True)
    return list(ids)


def auto(lat=37.4917, lon=127.0077):
    """다음 정각에 목록을 세고, 서초역에서 가까운 교차로부터 5분에 하나씩 받아 굽는다(끝날 때까지 돈다)."""
    ids = scan()
    C = cits(); done = set(os.path.basename(f).split('_')[0] for f in glob.glob(os.path.join(RAW, 'red', '*.json')))
    dist = lambda i: ((C[i][0] - lat) * 111000) ** 2 + ((C[i][1] - lon) * 88800) ** 2 if i in C else 9e18
    todo = sorted([i for i in ids if i not in done], key=dist)
    print('받을 교차로', len(todo), '가까운 것부터', [(i, C.get(i, [0, 0, '?'])[2], round(dist(i) ** 0.5)) for i in todo[:8]], flush=True)
    time.sleep(GAP)
    for n in range(0, len(todo), 6):
        fetch(todo[n:n + 6]); build(); time.sleep(GAP)


VGAP = 40 * 60      # 검증 = 40분 넘게 띄운 두 번의 닻이 같은 주기로 맞물리는가
FRESH = 75 * 60     # 닻이 이보다 낡으면 다시 받는다
_AC = {}


def anchors():
    """교차로마다 닻을 받은 시각들(epoch) — red 파일을 한 번만 읽어 둔다."""
    out = {}
    for f in glob.glob(os.path.join(RAW, 'red', '*.json')):
        if f not in _AC:
            try:
                r = json.load(open(f, encoding='utf-8')); _AC[f] = (r['id'], r.get('a'))
            except Exception:
                _AC[f] = (None, None)
        i, a = _AC[f]
        if i and a:
            out.setdefault(i, []).append(a)
    return out


def publish():
    """data/sigdir-seoul.json 만 올린다(다른 파일은 건드리지 않는다) — 열쇠 검사에 걸리면 올리지 않는다."""
    import subprocess
    run = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    try:
        if not run('git', 'status', '--porcelain', '--', 'data/sigdir-seoul.json').stdout.strip():
            return
        if run(sys.executable, '-X', 'utf8', os.path.join('tools', 'keycheck.py')).returncode != 0:
            print('열쇠 검사에 걸려 올리지 않았다', flush=True); return
        run('git', 'pull', '-q', '--ff-only', 'origin', 'main')
        c = run('git', 'commit', '-q', '-m', 'sigdir: 방향별 신호 자동 갱신\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', '--', 'data/sigdir-seoul.json')
        p2 = run('git', 'push', '-q', 'origin', 'main')
        print(datetime.datetime.now().strftime('%H:%M:%S'), '올림' if c.returncode == 0 and p2.returncode == 0 else '올리기 실패 ' + (c.stderr or p2.stderr)[:120], flush=True)
    except Exception as e:
        print('올리기 실패', str(e)[:120], flush=True)


def sweep(prefer=None, api='t', cap=None):
    """쪽(page)으로 훑기 — 거르지 않고 3만 줄을 받으면 서버 순서로 이어진 교차로 수십 곳의 그 시각 0분부터의 줄이 한 번에 온다.
    (itstId 로 거르면 뒤쪽 교차로는 HTTP 500 이 난다 · 2026-10-10 4031·4034) 서버 순서는 정각 목록(ids_*.json)의 차례이고,
    쪽 번호 = 앞선 교차로 수 × 교차로마다 쌓인 줄 수 ÷ 30000 — 줄 밀도(dens)는 받은 쪽에서 다시 잰다."""
    f = sorted(glob.glob(os.path.join(RAW, 'ids_*.json')))
    order = list(json.load(open(f[-1], encoding='utf-8'))['ids'].keys())
    pos = {k: i for i, k in enumerate(order)}
    pref = [x for x in (prefer or []) if x in pos]
    tried_f = os.path.join(RAW, 'tried_p.json' if api == 'p' else 'tried.json')
    tried = set(json.load(open(tried_f))) if os.path.exists(tried_f) else set()
    dens, miss, last, stuck, ncall = DENS0, 0, None, {}, 0
    capoff, caphr, capat = cap, datetime.datetime.now().hour, time.time()   # --cap N = 처음부터 이 깊이(줄)보다 얕은 쪽만(서버가 깊은 쪽을 막을 때)
    os.makedirs(os.path.join(RAW, 'red'), exist_ok=True)
    while True:
        A = anchors()
        nowt = time.time()
        need1 = lambda i: i not in tried and not A.get(i)                                   # 닻이 아직 없는 곳
        need2 = lambda i: i not in tried and A.get(i) and nowt - max(A[i]) >= VGAP and max(A[i]) - min(A[i]) < VGAP   # 닻은 있는데 40분 넘게 띄운 두 번째가 없는 곳(검증)
        need3 = lambda i: i not in tried and A.get(i) and nowt - max(A[i]) >= FRESH        # 닻이 낡은 곳(다시 받아 새로)
        todo = [i for i in pref if need1(i)] or [i for i in pref if need2(i)] or [i for i in pref if need3(i)] or [i for i in order if need1(i)]
        if not todo:
            print(datetime.datetime.now().strftime('%H:%M:%S'), '지금 받을 곳이 없다 — 5분 뒤 다시 본다', flush=True); time.sleep(GAP); continue
        now = datetime.datetime.now()
        if now.minute < 11:
            time.sleep((11 - now.minute) * 60 - now.second + 1); continue
        t = now.minute * 60 + now.second
        if last is None:
            dens = (t + 66.0) / t   # 첫 호출 — 교차로마다 앞 시각에서 넘어온 줄이 60여 줄 더 있어(2026-10-10 실측) 정각 가까울수록 밀도가 1 을 넘는다
        if capoff and (caphr != now.hour or time.time() - capat > 1800):
            capoff = None                                   # 깊은 쪽 막힘은 그 시각대·30분만 믿는다(풀렸는지 다시 본다)
        if capoff:
            # 2026-10-10 16시대 — 서버가 깊은 쪽(앞선 줄이 많은 쪽)에 HTTP 500 을 줬다(얕은 쪽은 됨) → 막힌 깊이보다 얕게 닿는 교차로만 고른다
            lim = capoff * 0.92 / (t + 66.0)
            reach = lambda L: [i for i in L if pos[i] < lim]
            todo = reach([i for i in pref if need1(i)]) or reach([i for i in pref if need2(i)]) or reach([i for i in order if need1(i)]) or reach([i for i in order if need3(i)])
            if not todo:
                print(now.strftime('%H:%M:%S'), '깊은 쪽이 막혀 닿는 곳이 없다(막힌 깊이', capoff, '줄) — 5분 뒤 다시', flush=True); time.sleep(GAP); continue
        K = (max if api == 'p' else min)(pos[i] for i in todo)   # 신호 상태 훑기는 뒤에서부터(두 훑기가 같은 쪽을 받지 않게)
        off = None
        if last and last['t'] < t and last['a'] <= K <= last['b'] + 1:
            off = last['base'] + sum(n for q, n in last['rows'] if q < K)   # 지난 쪽에서 센 K 앞의 줄 수(정확) — 지금 시각으로 늘린다
            off = off * t / float(last['t'])
        if off is None and last and last['t'] < t and abs(K - last['a']) < 300:
            blk = 30000.0 / max(1, len(last['rows']))   # 지난 쪽 둘레는 그 쪽의 교차로당 줄 수로 가늠(전체 평균 밀도보다 정확 — 쪽 하나 차이로 빗나가던 것)
            off = (last['base'] + (K - last['a']) * blk) * t / float(last['t'])
        if off is None:
            off = K * dens * t
        page = int((off + dens * t / 2) // 30000) + 1   # K 의 줄 가운데가 드는 쪽 — K 가 쪽 끝에 걸려 되풀이되던 것을 막는다
        u = (BASEP if api == 'p' else BASE) + '?apikey=' + key() + '&pageNo=%d&numOfRows=30000' % page
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=400); st = r.status; body = r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            st = e.code; body = e.read().decode('utf-8', 'ignore')
        except Exception as e:
            st = 0; body = str(e)
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if st != 200:
            print(stamp, '쪽', page, 'HTTP', st, body[:160].replace(key(), '***'), flush=True)
            wait = GAP
            if st == 500 and page > 1:
                capoff = min(capoff or 10 ** 12, (page - 1) * 30000); caphr = now.hour; capat = time.time(); last = None
            if st == 429:
                try: wait = int(json.loads(body).get('retryAfterSeconds', GAP)) + 5
                except Exception: pass
            time.sleep(wait); continue
        J = json.loads(body); by = {}; seq = []
        for x in J:
            i = str(x['itstId'])
            if i not in by: by[i] = []; seq.append(i)
            by[i].append(x)
        idx = [pos[i] for i in seq if i in pos]
        if not idx:
            print(stamp, '[상태]' if api == 'p' else '[잔여]', '쪽', page, '줄', len(J), '— 아는 교차로가 없다(밀도', round(dens, 3), ')', flush=True)
            dens *= 0.8; time.sleep(GAP); continue
        a, b = min(idx), max(idx)
        if page > 1 and a > 0:
            dens = (page - 1) * 30000.0 / (a * t)   # 앞선 a 곳이 (쪽-1)×3만 줄을 채웠다
        saved = 0
        for n, i in enumerate(seq):
            edge = n == 0 or n == len(seq) - 1   # 쪽 끝에 걸린 교차로는 줄이 잘렸을 수 있다
            red = (reduce_phase(i, by[i]) if api == 'p' else reduce_one(i, by[i])) if len(by[i]) >= 240 else None
            if red and red.get('cyc'):
                json.dump(red, open(os.path.join(RAW, 'red', '%s_%s%s.json' % (i, stamp, 'p' if api == 'p' else '')), 'w', encoding='utf-8'), ensure_ascii=False); saved += 1
            elif not edge:
                tried.add(i)   # 다 받았는데 주기를 못 읽은 곳(값이 멈춤·점멸) — 다시 받지 않는다
        json.dump(sorted(tried), open(tried_f, 'w'))
        last = {'t': t, 'a': a, 'b': b, 'base': (page - 1) * 30000, 'rows': [(pos[i], len(by[i])) for i in seq if i in pos]}
        hit = a <= K <= b
        A2 = anchors()
        if hit and order[K] not in tried and not (A2.get(order[K]) and len(A2[order[K]]) > len(A.get(order[K], []))):
            stuck[K] = stuck.get(K, 0) + 1
            if stuck[K] >= 2:
                tried.add(order[K]); json.dump(sorted(tried), open(tried_f, 'w'))   # 두 번 받고도 주기를 못 읽은 곳은 건너뛴다
        miss = 0 if hit else miss + 1
        print(stamp, '[상태]' if api == 'p' else '[잔여]', '쪽', page, '줄', len(J), '교차로', len(seq), '자리', a, '~', b, '(찾던 자리', K, '맞음' if hit else '빗나감', ') 구움', saved, '밀도', round(dens, 3), '우선 목록 — 닻 없음', len([i for i in pref if need1(i)]), '· 검증 남음', len([i for i in pref if need2(i)]), flush=True)
        if miss >= 4:
            tried.add(order[K]); miss = 0   # 네 번 빗나가면 그 교차로는 건너뛴다
        if api != 'p':
            build()
            ncall += 1
            if ncall % 3 == 0:
                publish()
            if ncall % 12 == 0:
                prune()
        time.sleep(GAP)


def segments(rows, k):
    """한 이동류의 구간 목록 [(시작 시각, 길이, 시작 때 잔여)] — 끊긴 자리·모름 값에 걸친 구간은 뺀다."""
    out, prev_v, prev_t, start, start_v, bad = [], None, None, None, None, False
    for r in rows:
        v = r.get(k)
        t = r['trsmUtcTime'] / 1000.0
        if v is None:
            continue
        v = v / 10.0
        if prev_t is not None and t - prev_t > 5:
            bad = True
        if v >= 3000:
            bad = True
        if prev_v is None or v > prev_v + 1.5:
            if start is not None and not bad:
                out.append((start, t - start, start_v))
            start, start_v = t, v
            bad = v >= 3000
        prev_v, prev_t = v, t
    return out[1:] if out else []   # 첫 구간은 앞이 잘렸을 수 있다


def med(a):
    return round(statistics.median(a), 1) if a else None


PH_G = ('protected-Movement-Allowed', 'permissive-Movement-Allowed')
PH_Y = ('protected-clearance', 'permissive-clearance')
PH_R = ('stop-And-Remain', 'stop-Then-Proceed')


def phase_runs(rows, k, ped):
    """한 이동류의 상태 구간 [(시작 시각, 길이 초, g|y|r|?, 앞뒤가 온전한가)] — 마지막(끝이 잘린) 구간은 넣지 않는다.
    보행(ped)은 protected = 녹색 · permissive = 녹색 점멸(y 자리)로 읽는다."""
    out, cur, start, prev_t, bad = [], None, None, None, False
    for r in rows:
        v = r.get(k)
        if v is None:
            continue
        t = r['trsmUtcTime'] / 1000.0
        if ped:
            c = 'g' if v == 'protected-Movement-Allowed' else 'y' if v in ('permissive-Movement-Allowed',) + PH_Y else 'r' if v in PH_R else '?'
        else:
            c = 'g' if v in PH_G else 'y' if v in PH_Y else 'r' if v in PH_R else '?'
        gap = prev_t is not None and t - prev_t > 5
        if cur is None:
            cur, start, bad = c, t, True          # 첫 구간은 앞이 잘렸다
        elif c != cur or gap:
            out.append((start, (prev_t if gap else t) - start, cur, not bad and not gap))
            cur, start, bad = c, t, gap
        prev_t = t
    return out


def reduce_phase(itst, J):
    """신호 상태 줄 → reduce_one 과 같은 꼴(주기 · 이동류마다 녹·황·적 초 · 녹색 시작 자리 · 닻) + 보행 신호(pd)."""
    rows = [x for x in J if str(x.get('itstId')) == str(itst)]
    rows.sort(key=lambda x: x['trsmUtcTime'])
    if len(rows) < 120:
        return None
    t0, t1 = rows[0]['trsmUtcTime'] / 1000.0, rows[-1]['trsmUtcTime'] / 1000.0
    mv, pd, cyc_all = [], [], []
    for d in DIRS:
        for m in MVS:
            k = d + m + 'sgStatNm'
            if not any(r.get(k) is not None for r in rows):
                continue
            R = phase_runs(rows, k, m == 'Pd')
            G, Y, Rd, gs = [], [], [], []
            for i, (st, du, c, ok) in enumerate(R):
                if not ok or c == '?':
                    continue
                if c == 'g': G.append(du); gs.append(st)
                elif c == 'y': Y.append(du)
                elif c == 'r': Rd.append(du)
            if len(G) < 2 or not Rd or any(c == '?' for _, _, c, _ in R):
                (pd if m == 'Pd' else mv).append({'d': d, 'm': m, 'n': len(G)})      # 색을 못 읽은 이동류(점멸 운영 · 받은 동안 한 바퀴가 안 됨)
                continue
            x = {'d': d, 'm': m, 'g': med(G), 'y': med(Y) if Y else 0.0, 'r': med(Rd), 'n': len(G), 'gs': gs}
            (pd if m == 'Pd' else mv).append(x)
            if m != 'Pd':
                cyc_all.append(x['g'] + x['y'] + x['r'])
    if not cyc_all:
        return None
    cyc = med(cyc_all)
    ok = [x for x in mv if 'g' in x]
    ref = max(ok, key=lambda x: (x['g'], -DIRS.index(x['d'])))
    rs = sorted(ref['gs'])
    for x in ok + [q for q in pd if 'g' in q]:
        offs = []
        for s0 in x['gs']:
            prev = [r for r in rs if r <= s0 + 1]
            if prev and s0 - prev[-1] < cyc + 2:
                offs.append(max(0, s0 - prev[-1]))
        x['o'] = int(round(statistics.median(offs))) % int(round(cyc)) if offs else None
    ncy = round((rs[-1] - rs[0]) / cyc) if len(rs) > 1 else 0
    cx = (rs[-1] - rs[0]) / ncy if ncy >= 2 else cyc
    ci = int(round(cx)) if abs(cx - round(cx)) <= 0.25 else round(cx, 1)
    for x in mv + pd:
        x.pop('gs', None)
    hh = lambda t: datetime.datetime.fromtimestamp(t).strftime('%H:%M')
    return {'id': str(itst), 'day': datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d'), 'dow': datetime.datetime.fromtimestamp(t0).isoweekday() % 7, 'from': hh(t0), 'to': hh(t1), 'rows': len(rows),
            'cyc': cyc, 'mv': mv, 'ped': [{'d': q['d'], 'seg': [], 'n': q['n']} for q in pd], 'pd': pd, 'a': (round(rs[-1], 1) if abs(ci - cyc) <= 2 else None), 'ci': ci, 'end': round(t1, 1), 'ncy': ncy, 'src': 'p'}


def reduce_one(itst, J):
    rows = [x for x in J if str(x.get('itstId')) == str(itst)]
    rows.sort(key=lambda x: x['trsmUtcTime'])
    if len(rows) < 120:
        return None
    t0, t1 = rows[0]['trsmUtcTime'] / 1000.0, rows[-1]['trsmUtcTime'] / 1000.0
    mv, ped, cyc_all = [], [], []
    for d in DIRS:
        for m in MVS:
            k = d + m + 'sgRmdrCs'
            if not any(r.get(k) is not None for r in rows):
                continue
            sg = segments(rows, k)
            sg = [s for s in sg if abs(s[1] - s[2]) <= 3.5]   # 구간 길이 ≈ 시작 때 잔여(끊김·튐 거르기)
            if m == 'Pd':
                ped.append({'d': d, 'seg': [round(s[1]) for s in sg[:12]], 'n': len(sg)})
                continue
            G, Y, R, gs = [], [], [], []
            for i in range(1, len(sg) - 1):
                if 2.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and sg[i + 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2 and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2:
                    G.append(sg[i - 1][1]); Y.append(sg[i][1]); R.append(sg[i + 1][1]); gs.append(sg[i - 1][0])
            if len(G) < 2:
                mv.append({'d': d, 'm': m, 'n': len(G), 'seg': [round(s[1]) for s in sg[:10]]})   # 색을 못 가린 이동류(점멸 운영 등)
                continue
            g, y, r = med(G), med(Y), med(R)
            mv.append({'d': d, 'm': m, 'g': g, 'y': y, 'r': r, 'n': len(G), 'gs': gs})
            cyc_all.append(g + y + r)
    if not mv and not ped:
        return None
    cyc = med(cyc_all)
    ok = [x for x in mv if 'g' in x]
    # 녹색 시작 자리(주기 안) — 녹색이 가장 긴 이동류의 시작을 0 으로
    if ok and cyc:
        ref = max(ok, key=lambda x: (x['g'], -DIRS.index(x['d'])))
        rs = sorted(ref['gs'])
        for x in ok:
            offs = []
            for s0 in x['gs']:
                prev = [r for r in rs if r <= s0 + 1]   # 이 녹색 바로 앞의 기준 녹색 시작(주기마다 따로 재서 통신 끊김 뒤 어긋남을 피한다)
                if prev and s0 - prev[-1] < cyc + 2:
                    offs.append(max(0, s0 - prev[-1]))
            x['o'] = int(round(statistics.median(offs))) % int(round(cyc)) if offs else None
    anchor = None
    if ok and cyc:
        # 닻 = 기준 이동류(녹색이 가장 긴 것)의 마지막 녹색이 켜진 실제 시각(epoch 초) — 지도가 이 시각에서 주기로 이어 센다
        # 주기는 기준 녹색 시작들 사이를 주기 수로 나눠 다시 잰다(중앙값보다 정밀) — 정수 초에 가까우면 정수로
        ncy = round((rs[-1] - rs[0]) / cyc) if len(rs) > 1 else 0
        cx = (rs[-1] - rs[0]) / ncy if ncy >= 2 else cyc
        ci = int(round(cx)) if abs(cx - round(cx)) <= 0.25 else round(cx, 1)
        anchor = {'a': (round(rs[-1], 1) if abs(ci - cyc) <= 2 else None), 'ci': ci, 'end': round(t1, 1), 'ncy': ncy}
    for x in mv:
        x.pop('gs', None)
    hh = lambda t: datetime.datetime.fromtimestamp(t).strftime('%H:%M')
    if anchor:
        return dict({'id': str(itst), 'day': datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d'), 'dow': datetime.datetime.fromtimestamp(t0).isoweekday() % 7, 'from': hh(t0), 'to': hh(t1), 'rows': len(rows), 'cyc': cyc, 'mv': mv, 'ped': ped}, **anchor)
    return {'id': str(itst), 'day': datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d'), 'dow': datetime.datetime.fromtimestamp(t0).isoweekday() % 7, 'from': hh(t0), 'to': hh(t1), 'rows': len(rows), 'cyc': cyc, 'mv': mv, 'ped': ped}


def fetch(ids):
    os.makedirs(os.path.join(RAW, 'red'), exist_ok=True)
    for n, itst in enumerate(ids):
        if n:
            time.sleep(GAP)
        # 이 API 는 「그 시각의 0분부터」 쌓인 줄을 앞에서부터 준다 — 정각 직후에는 줄이 모자라 주기를 못 읽는다 → 14분까지 기다린다
        mm = datetime.datetime.now().minute
        if mm < 14:
            time.sleep((14 - mm) * 60)
        st, body, h = call(itst)
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if st != 200:
            print(stamp, itst, 'HTTP', st, body[:160].replace(key(), '***'), flush=True)
            if st == 429:
                try: time.sleep(max(0, int(json.loads(body).get('retryAfterSeconds', 0))) + 5)
                except Exception: pass
            continue
        try:
            J = json.loads(body)
        except Exception:
            print(stamp, itst, '응답이 JSON 이 아님', body[:120], flush=True); continue
        got = sorted(set(str(x.get('itstId')) for x in J))
        red = reduce_one(itst, J)
        if red is None:
            print(stamp, itst, '줄 수', len(J), '받은 교차로', got[:5], '— 줄일 것이 없다', flush=True)
            continue
        json.dump(red, open(os.path.join(RAW, 'red', '%s_%s.json' % (itst, stamp)), 'w', encoding='utf-8'), ensure_ascii=False)
        with gzip.open(os.path.join(RAW, 'raw_%s_%s.json.gz' % (itst, stamp)), 'wt', encoding='utf-8') as f:
            f.write(body)
        print(stamp, itst, '줄', red['rows'], red['from'], '~', red['to'], '주기', red['cyc'], '차량 이동류', len([x for x in red['mv'] if 'g' in x]), '/', len(red['mv']), '보행', len(red['ped']), '남은 호출', h.get('X-RateLimit-Remaining'), flush=True)


def mvrow(x, cyc):
    """지도에 싣는 한 줄 — 한 주기에 두 번 켜지는 이동류(녹+황+적 ≠ 주기)는 한 막대로 그리면 틀리므로 초를 비우고 끝에 2 를 단다."""
    if x.get('g') is not None and abs(x['g'] + x['y'] + x['r'] - cyc) > 3.5:
        return [x['d'], x['m'], None, None, None, None, x['n'], 2]
    return [x['d'], x['m'], x.get('g'), x.get('y'), x.get('r'), x.get('o'), x['n']]


def cls_of(dow):
    """요일 갈래 — 0 월~목 · 1 금 · 2 토 · 3 일(교통과 계획의 TOD 갈래와 같게)"""
    return 2 if dow == 6 else 3 if dow == 0 else 1 if dow == 5 else 0


def prune():
    """red 폴더 정리 — (교차로, 요일 갈래, 시, 받은 길)마다 최신 둘만 남기고 이틀 지난 것은 지운다(하루 1만 개씩 쌓인다)."""
    G = {}
    now = time.time()
    for f in glob.glob(os.path.join(RAW, 'red', '*.json')):
        b = os.path.basename(f)[:-5]
        try:
            i, d, hm = b.split('_')[:3]
            dt = datetime.datetime.strptime(d + hm[:6], '%Y%m%d%H%M%S')
        except Exception:
            continue
        G.setdefault((i, cls_of(dt.isoweekday() % 7), dt.hour, b.endswith('p')), []).append((dt, f))
    n = 0
    for L in G.values():
        L.sort()
        for dt, f in L[:-2]:
            if now - dt.timestamp() > 2 * 86400:
                try: os.remove(f); _AC.pop(f, None); n += 1
                except Exception: pass
    return n


def build():
    out = {}
    for f in sorted(glob.glob(os.path.join(RAW, 'red', '*.json'))):
        r = json.load(open(f, encoding='utf-8'))
        if not r.get('cyc'):
            continue
        out.setdefault(r['id'], []).append(r)
    its, nver, nbad, tod, pl = {}, 0, 0, {}, {}
    for k, v in out.items():
        v.sort(key=lambda r: (r['day'], r['to']))
        keep, plan = {}, {}
        for r in v:
            ci0 = r.get('ci') or int(round(r['cyc']))
            kk = (cls_of(r['dow']), int(round(ci0)))
            if r.get('pd') or not (keep.get(kk) and keep[kk].get('pd')) or r.get('a'):
                if keep.get(kk) and keep[kk].get('pd') and not r.get('pd'):
                    r = dict(r, pd=keep[kk]['pd'], src=keep[kk].get('src'))   # 보행 신호 색은 신호 상태 API 로 읽은 것을 이어 쓴다(같은 요일 갈래·같은 주기)
                keep[kk] = r                                    # (요일 갈래, 주기)마다 나중 것 한 장
            if r.get('a'):
                hh = datetime.datetime.fromtimestamp(r['a']).hour
                sod = (r['a'] + 9 * 3600) % 86400               # 한국 시각 하루 초
                plan[(cls_of(r['dow']), hh)] = [cls_of(r['dow']), hh, ci0, int(round(sod % ci0)) % int(round(ci0)) if ci0 == int(ci0) else round(sod % ci0, 1), r['day'][5:]]
        vv = sorted(keep.values(), key=lambda r: (r['day'], r['to']))[-12:]
        if plan:
            pl[k] = [plan[q] for q in sorted(plan)]
        L = []
        for r in vv:
            o = {'day': r['day'], 'dow': r['dow'], 'cl': cls_of(r['dow']), 'from': r['from'], 'to': r['to'], 'cyc': r['cyc'],
                 'mv': [mvrow(x, r['cyc']) for x in r['mv']],
                 'ped': [[p['d'], p['seg'][:8]] for p in r['ped']]}
            if r.get('src') == 'p':
                o['src'] = 'p'   # 신호 상태 API 로 읽은 기록(색이 추정이 아니라 상태 값 그대로)
            if r.get('pd'):
                o['pd'] = [[q['d'], q.get('g'), q.get('y'), q.get('r'), q.get('o'), q['n']] for q in r['pd'] if q.get('g') is not None and abs(q['g'] + q['y'] + q['r'] - r['cyc']) <= 3.5]   # 보행 신호 [방위, 녹색, 점멸, 적색, 녹색 시작, 본 횟수] — 주기와 맞는 것만
            if r.get('a'):
                o['a'] = int(round(r['a'])); o['ci'] = r['ci']
                # 검증 — 같은 주기로 받은 다른 닻(40분 넘게 떨어진 것)과 주기의 정수배로 맞물리는가(±3초)
                best, bad = None, None
                for q in v:
                    if not q.get('a') or abs(q.get('ci', 0) - r['ci']) > 0.3 or abs(q['a'] - r['a']) < VGAP:
                        continue
                    gap = abs(q['a'] - r['a']); res = gap % r['ci']; res = min(res, r['ci'] - res)
                    if res <= 3:
                        if not best or gap > best[0]: best = (gap, res)
                    elif not bad or gap < bad[0]: bad = (gap, res)
                if best: o['v'] = [int(best[0] // 60), round(best[1], 1)]
                if bad: o['x'] = [int(bad[0] // 60), round(bad[1], 1)]
            L.append(o)
        its[k] = L
        td = {}
        for r in v:   # 시간대별 주기(받은 것만) — [요일 갈래(0 평일 · 1 토 · 2 일), 시, 주기 초]
            td[(1 if r['dow'] == 6 else 2 if r['dow'] == 0 else 0, int(r['from'][:2]))] = int(round(r['cyc']))
        tod[k] = [[a, b, c] for (a, b), c in sorted(td.items())]
        if L and L[-1].get('v'): nver += 1
        if L and L[-1].get('x') and not L[-1].get('v'): nbad += 1
    # 교차로 자리 — 서울 C-ITS 교차로 지도정보(받아 둔 xmap_*.json 이 있으면 그것, 없으면 지도 저장소의 서초 둘레 목록)
    pts = {}
    for k, v in cits().items():
        if k in its:
            pts[k] = v
    try:
        for x in json.load(open(os.path.join(ROOT, 'data', 'pubdata-seocho.json'), encoding='utf-8'))['sigx']['items']:
            if str(x['no']) in its and str(x['no']) not in pts:
                pts[str(x['no'])] = [x['lat'], x['lon'], x['name']]
    except Exception:
        pass
    doc = {'schema': 'tg-sigdir/1',
           'source': '서울특별시 교통빅데이터플랫폼(T-Data) V2X 신호 잔여시간 정보(v2xSignalPhaseTimingInformation) — 교차로 신호제어기가 1초마다 보낸 방위별·이동류별 잔여시간',
           'how': '잔여시간이 새 값으로 뛰는 자리 사이를 한 구간으로 보고, 차량 신호는 3~6초 구간을 황색으로 보아 그 앞을 녹색·뒤를 적색으로 읽었다(추정). 받은 시간대의 실제 운영값이며 다른 시간대·요일은 다르다. 보행 신호는 색을 가릴 수 없어 구간 길이만 싣는다.',
           'mvcols': ['방위(nt 북 · et 동 · st 남 · wt 서 · ne·se·sw·nw)', '이동류(St 직진 · Lt 좌회전 · Ut 유턴 · Bs 버스 · Bc 자전거)', '녹색 초', '황색 초', '적색 초', '녹색 시작(주기 안 · 가장 긴 녹색 = 0)', '본 주기 수'],
           'fields': 'pts{교차로 번호: [위도, 경도, 이름]} · its{교차로 번호: [기록…]} 기록 = {day 받은 날, dow 요일(0 일), from~to 받은 시각, cyc 주기 초, mv[[방위, 이동류, 녹색, 황색, 적색, 녹색 시작(주기 안), 본 횟수(, 2 = 한 주기에 두 번)]], pd[[방위, 보행 녹색, 점멸, 적색, 녹색 시작, 본 횟수]](신호 상태 API 로 받은 기록만), ped[[방위, …]](보행 신호가 있는 쪽), a 기준 이동류 녹색이 켜진 실제 시각(epoch 초), ci 주기(이어 세기용), v[띄운 분, 어긋난 초](두 번 대조 통과), x[…](대조 실패), src p = 신호 상태 API} · tod{교차로 번호: [[요일 갈래 0 평일·1 토·2 일, 시, 주기 초]]} · pl{교차로 번호: [[요일 갈래(0 월~목 · 1 금 · 2 토 · 3 일), 시, 주기, 자정 기준 옵셋(기준 이동류 녹색이 켜지는 하루 초 mod 주기), 받은 달-날]]}(시계로 이어 세는 표 — 기록의 cl·ci 가 같은 것이 그 계획의 방향별 초)',
           'note': '받은 시간대에 실제로 돈 값이다(하루 계획표가 아니다) · 방위 = 그 신호를 받는 차가 들어오는 쪽 · 잔여시간 API 로 읽은 기록의 색은 황색 3~6초 앞뒤로 읽은 추정이고 src p 기록은 상태 값 그대로 · 이어 센 「지금 몇 초」는 a·ci 로 지도가 계산한 추정',
           'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'pts': pts, 'its': its, 'tod': tod, 'pl': pl}
    p = os.path.join(ROOT, 'data', 'sigdir-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(its), '· 닻', sum(1 for L in its.values() if L[-1].get('a')), '· 검증됨', nver, '· 안 맞음', nbad, '->', p, os.path.getsize(p), 'B')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'fetch':
        ids = a[1:]
        if ids and ids[0] == '--list':
            ids = [x.strip() for x in open(ids[1], encoding='utf-8') if x.strip() and not x.startswith('#')]
        fetch(ids)
    elif a and a[0] == 'build':
        build()
    elif a and a[0] == 'auto':
        auto()
    elif a and a[0] == 'sweep':
        pf = [x.strip() for x in open(a[2], encoding='utf-8') if x.strip() and not x.startswith('#')] if len(a) > 2 and a[1] == '--list' else None
        sweep(pf, 'p' if '--api' in a and a[a.index('--api') + 1] == 'p' else 't', int(a[a.index('--cap') + 1]) if '--cap' in a else None)
    elif a and a[0] == 'testp':
        J = json.load(open(a[1], encoding='utf-8'))
        for i in sorted(set(str(x['itstId']) for x in J)):
            print(json.dumps(reduce_phase(i, J), ensure_ascii=False))
    elif a and a[0] == 'test':
        J = json.load(open(a[1], encoding='utf-8'))
        for i in sorted(set(str(x['itstId']) for x in J)):
            print(json.dumps(reduce_one(i, J), ensure_ascii=False))
    else:
        print(__doc__ or 'fetch <번호…> | build')
