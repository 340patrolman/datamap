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
CAP_SAFE = 26 * 30000   # 2026-10-10 16:14 부터 — 27쪽까지는 받아지고 32쪽부터 HTTP 500(앞선 줄 수 기준으로 보인다) → 막히면 이보다 얕게만
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
    """data/sigdir-seoul.json 과 맞대 본 결과 data/sig-audit.json 만 올린다(다른 파일은 건드리지 않는다) — 열쇠 검사에 걸리면 올리지 않는다."""
    import subprocess
    run = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    try:
        if not run('git', 'status', '--porcelain', '--', 'data/sigdir-seoul.json').stdout.strip():
            return
        run(sys.executable, '-X', 'utf8', os.path.join('tools', 'signal', 'sig-audit.py'))   # 맞대 본 결과(data/sig-audit.json)도 같이 다시 만든다
        run('git', 'add', '--', 'data/sigdir-seoul.json', 'data/sig-audit.json')            # 열쇠 검사는 올릴 준비가 된 변경만 본다 — 먼저 올릴 준비를 한다
        if run(sys.executable, '-X', 'utf8', os.path.join('tools', 'keycheck.py')).returncode != 0:
            print('열쇠 검사에 걸려 올리지 않았다', flush=True); return
        run('git', 'pull', '-q', '--ff-only', 'origin', 'main')
        c = run('git', 'commit', '-q', '-m', 'sigdir: 방향별 신호 자동 갱신\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', '--', 'data/sigdir-seoul.json', 'data/sig-audit.json')
        p2 = run('git', 'push', '-q', 'origin', 'main')
        print(datetime.datetime.now().strftime('%H:%M:%S'), '올림' if c.returncode == 0 and p2.returncode == 0 else '올리기 실패 ' + (c.stderr or p2.stderr)[:120], flush=True)
    except Exception as e:
        print('올리기 실패', str(e)[:120], flush=True)


def pick_todo(tiers, order, need1, need2, need3, ok=lambda i: True):
    """받을 곳 고르기 — ① 묶음 차례로 닻 없는 곳 ② 묶음 차례로 검증할 곳 ③ 그 밖 서울의 닻 없는 곳 ④ 묶음 차례로 낡은 곳(시각대 표 채우기) ⑤ 그 밖 낡은 곳"""
    for f in (need1, need2):
        for T in tiers:
            c = [i for i in T if f(i) and ok(i)]
            if c: return c
    c = [i for i in order if need1(i) and ok(i)]
    if c: return c
    for T in tiers:
        c = [i for i in T if need3(i) and ok(i)]
        if c: return c
    return [i for i in order if need3(i) and ok(i)]


def read_list(path):
    """수집 차례 파일 — 「## 」 줄마다 새 묶음 · 「#」 줄은 설명"""
    tiers, cur = [], []
    for ln in open(path, encoding='utf-8'):
        ln = ln.strip()
        if ln.startswith('## '):
            if cur: tiers.append(cur)
            cur = []
        elif ln and not ln.startswith('#'):
            cur.append(ln)
    if cur: tiers.append(cur)
    return tiers


def sweep(prefer=None, api='t', cap=None):
    """쪽(page)으로 훑기 — 거르지 않고 3만 줄을 받으면 서버 순서로 이어진 교차로 수십 곳의 그 시각 0분부터의 줄이 한 번에 온다.
    (itstId 로 거르면 뒤쪽 교차로는 HTTP 500 이 난다 · 2026-10-10 4031·4034) 서버 순서는 정각 목록(ids_*.json)의 차례이고,
    쪽 번호 = 앞선 교차로 수 × 교차로마다 쌓인 줄 수 ÷ 30000 — 줄 밀도(dens)는 받은 쪽에서 다시 잰다."""
    f = sorted(glob.glob(os.path.join(RAW, 'ids_*.json')))
    order = list(json.load(open(f[-1], encoding='utf-8'))['ids'].keys())
    pos = {k: i for i, k in enumerate(order)}
    tiers = [[x for x in T if x in pos] for T in (prefer if prefer and isinstance(prefer[0], list) else [prefer or []])]   # 묶음(가까운 곳부터) — 앞 묶음이 끝나야 다음 묶음
    tiers = [T for T in tiers if T]
    pref = [x for T in tiers for x in T]
    tried_f = os.path.join(RAW, 'tried_p.json' if api == 'p' else 'tried.json')
    tried = set(json.load(open(tried_f))) if os.path.exists(tried_f) else set()
    dens, miss, last, stuck, ncall = DENS0, 0, None, {}, 0
    smiss_f = os.path.join(RAW, 'smiss_p.json' if api == 'p' else 'smiss_t.json')
    smiss = json.load(open(smiss_f)) if os.path.exists(smiss_f) else {}
    # 끝자리(pcap) — 그 시각대에 서버가 가진 자료의 끝이 서버 순서로 몇 번째 교차로쯤인가. HTTP 500 = 「그 쪽은 자료의 끝을 넘었다」로 읽는다
    # (2026-10-10 저녁: 190쪽은 되고 229쪽은 500 · 정각 창 23쪽이 500 — 깊이(줄 수)가 아니라 끝자리(살아 있는 교차로 수 × 지난 초)가 문턱이었다).
    pcap, pcat, seen, seen_slot, pok, pok_hr, nfail, avoid, plast = (float(cap) if cap else None), time.time(), {}, None, -1, -1, 0, None, None
    cap_f = os.path.join(RAW, 'pcap_p.json' if api == 'p' else 'pcap_t.json')   # 끝자리는 파일에 남겨 다시 띄워도 잇는다
    for cf in (cap_f, os.path.join(RAW, 'pcap_t.json' if api == 'p' else 'pcap_p.json')):
        if not pcap and os.path.exists(cf):
            try:
                c0 = json.load(open(cf))
                if c0.get('pos') and time.time() - c0['at'] < 1800:
                    pcap, pcat = c0['pos'], min(c0['at'], time.time())
            except Exception:
                pass
    if pcap:
        pok_hr = datetime.datetime.now().hour                 # 끝자리를 이어받았으면 띄우자마자 끝자리 너머를 찔러 보지 않는다(다음 정각에 찌른다)
    # 두 훑기가 같이 쓰는 끝자리 장부(pend.json) — 이 시각대에 받아진 맨 뒤 자리(ok)와 500 이 난 자리들(fails [자리, 때]). 한쪽이 찔러 본 것을 다른 쪽이 또 찌르지 않는다
    end_f, hist_f = os.path.join(RAW, 'pend.json'), os.path.join(RAW, 'sweep_hist.jsonl')
    def end_load():
        hr = datetime.datetime.now().strftime('%Y%m%d%H')
        try:
            e = json.load(open(end_f))
            if e.get('hr') == hr:
                return e
        except Exception:
            pass
        return {'hr': hr, 'ok': -1, 'fails': []}
    def end_note(k=None, b=None):
        e = end_load()
        if b is not None:
            e['ok'] = max(e['ok'], int(b)); e['fails'] = [q for q in e['fails'] if q[0] > b]   # 받아진 자리보다 앞의 500 은 우연이었다
        if k is not None:
            e['fails'].append([int(k), time.time()])
        try:
            json.dump(e, open(end_f, 'w'))
        except Exception:
            pass
    def hist(**kw):
        try:
            open(hist_f, 'a', encoding='utf-8').write(json.dumps(kw, ensure_ascii=False) + '\n')
        except Exception:
            pass
    W0 = 300 if api == 'p' else 285   # (2026-10-10 19:04 실측 — 줄 수 = 정각 뒤 초 − 8쯤 · 240초에는 234줄이라 문턱 240 에 못 미쳤다 → 285초)  # 정각 뒤 창 — 이때는 교차로마다 300줄쯤이라 한 쪽에 100곳 가까이 들고, 서울 뒤쪽(서초 1668~ · 강남 ~2248)도 20쪽 안이다
    os.makedirs(os.path.join(RAW, 'red'), exist_ok=True)
    while True:
        A = anchors()
        nowt = time.time()
        now = datetime.datetime.now()
        t = now.minute * 60 + now.second
        slot_of = lambda ts: (cls_of((datetime.datetime.fromtimestamp(ts).weekday() + 1) % 7), datetime.datetime.fromtimestamp(ts).hour)
        nslot = slot_of(nowt)
        if seen_slot != nslot:
            seen_slot, seen = nslot, {}                       # 시각대가 바뀌면 「이 시각대에 몇 번 받아 봤나」를 다시 센다
        need1 = lambda i: i not in tried and not A.get(i) and seen.get(i, 0) < 3                                   # 닻이 아직 없는 곳
        needS = lambda i: i not in tried and A.get(i) and seen.get(i, 0) < 2 and not any(slot_of(a) == nslot for a in A[i])   # 닻은 있는데 지금 요일 갈래·지금 시각대 값이 없는 곳(시각대 표 채우기 · 두 번 받아도 안 되면 이 시각대는 넘긴다)
        def pick(ok=lambda i: True):
            """받을 곳 — ① 앞 두 묶음(서초·강남) 닻 없는 곳 ② 앞 두 묶음의 이 시각대 빈 곳 ③ 나머지 묶음 닻 없는 곳 ④ 그 밖 서울 닻 없는 곳 ⑤ 나머지 묶음 이 시각대 빈 곳 ⑥ 그 밖 서울 이 시각대 빈 곳
            (2026-10-10 소유자 「우선 서초구 전 지역 후 강남구로 · 순서대로」「수집 가능한 모든 신호값을 모아서」)"""
            for f in (need1, needS):
                for T in tiers[:2]:
                    c = [i for i in T if f(i) and ok(i)]
                    if c: return c
            for T in tiers[2:]:
                c = [i for i in T if need1(i) and ok(i)]
                if c: return c
            c = [i for i in order if need1(i) and ok(i)]
            if c: return c
            for T in tiers[2:]:
                c = [i for i in T if needS(i) and ok(i)]
                if c: return c
            return [i for i in order if needS(i) and ok(i)]
        if t < W0:
            time.sleep(W0 - t + 1); continue      # 정각 뒤 4분 45초부터 — 그 전에는 교차로마다 줄이 모자라 주기를 못 읽는다(240줄 문턱)
        if t > 3600 + W0 - GAP - 5:
            time.sleep(3600 - t + W0 + 1); continue   # 다음 정각 창을 5분 제한으로 놓치지 않게 — 창 바로 앞 호출은 건너뛴다
        if last is None:
            dens = 1.0
        if pok_hr != now.hour:
            pok_hr, pok = now.hour, -1                        # 이 시각대에 실제로 받은 맨 뒤 자리
            plast, pcap, nfail, avoid = (pcap or plast), None, 0, None   # 시각대가 바뀌면 끝자리를 풀고 한 번 찔러 본다(안 되면 앞 시각대 끝자리로 바로 되돌린다)
        if pcap and time.time() - pcat > 1200:
            plast, pcap = pcap, None                          # 끝자리는 20분만 믿는다 — 풀고 한 번 찔러 본다(안 되면 바로 되돌린다)
        E = end_load()
        fl = sorted(q[0] for q in E['fails'] if q[0] > max(E['ok'], pok) and time.time() - q[1] < 1500)   # 25분 안에 500 이 난 자리(받아진 자리 너머 것만)
        if pcap and E['ok'] >= pcap:
            pcap = None                                       # 다른 훑기가 끝자리로 본 곳보다 뒤를 받았다
        if len(fl) >= 2:
            sc = max(E['ok'] + 1, pok + 1, fl[1] - 30)        # 두 번 500 이 난 자리 = 끝자리로 본다(어느 훑기가 낸 것이든)
            if not pcap or sc < pcap:
                pcap, pcat = sc, time.time()
        if not pcap and plast and fl and fl[0] >= plast * 0.97:
            pcap, pcat, plast = plast, time.time() + 1200, None   # 다른 훑기가 방금 끝자리 너머를 찔러 봤다 — 또 찌르지 않고 되는 곳만 받는다
        av = avoid; avoid = None
        okf = lambda i: (not pcap or pos[i] < pcap * 0.97) and (av is None or abs(pos[i] - av) > 60)
        todo = pick(okf) or pick((lambda i: pos[i] < pcap * 0.97) if pcap else (lambda i: True))
        if not todo:
            print(now.strftime('%H:%M:%S'), '지금 받을 곳이 없다' + ('(끝자리 %d 안쪽에는)' % pcap if pcap else '') + ' — 5분 뒤 다시 본다', flush=True); time.sleep(GAP); continue
        ps = sorted(pos[i] for i in todo)
        per = int(30000 / max(dens * t, 1.0))                 # 한 쪽에 드는 교차로 수(정각 창에서는 100곳 안팎)
        if len(ps) > 2 and per >= 20:
            # 받을 곳이 가장 많이 몰린 자리를 고른다(2026-10-10 21:04 — 맨 앞 자리만 골라 같은 쪽을 시간마다 다시 받았다) · 잔여는 앞 절반, 상태는 뒤 절반에서(두 훑기가 같은 쪽을 받지 않게)
            mid = ps[len(ps) // 2]
            cand = [q for q in ps if (q >= mid if api == 'p' else q <= mid)] or ps
            K = max(cand, key=lambda q: (sum(1 for z in ps if abs(z - q) <= per * 0.45), q if api == 'p' else -q))
        else:
            K = (max if api == 'p' else min)(ps)   # 신호 상태 훑기는 뒤에서부터(두 훑기가 같은 쪽을 받지 않게)
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
            hist(at=stamp, api=api, t=t, page=page, K=K, st=st)
            wait = GAP
            if st == 500 and page > 1:
                # 끝자리 = 찾던 자리(K) 바로 앞 — 줄 수로 되짚으면(쪽 ÷ 밀도 × 초) 자료가 늦게 쌓일 때 너무 앞으로 잡힌다(22:25 — 1667 까지 받아 놓고 끝자리를 1617 로 봤다). 이 시각대에 실제로 받은 맨 뒤 자리(pok)보다 앞으로는 안 당긴다
                # 한 번 실패로는 끝자리를 당기지 않는다 — 있는 쪽도 가끔 500 이 난다(22:39 에 1514~1527 을 받았는데 22:45 에 같은 둘레가 500). 한 번이면 그 둘레만 다음 한 번 비켜 가고, 잇달아 두 번이면 끝자리로 본다(20분)
                nfail += 1; avoid = K; last = None
                end_note(k=K)
                if plast and K >= plast * 0.97:
                    # 소유자 2026-10-10 밤 「안 되는 곳보다는 되는 곳 위주로」 — 방금 풀어 준 끝자리 너머를 찔러 봤는데 또 안 된다 → 바로 되돌리고 40분은 되는 곳만 받는다(종전엔 20분마다 두 번씩 헛받았다)
                    pcap = max(pok + 1, min(plast, K - max(1, per // 2))); pcat = time.time() + 1200; plast = None
                elif nfail >= 2:
                    pcap = max(pok + 1, min(pcap or 1e9, K - max(1, per // 2))); pcat = time.time()
                json.dump({'pos': pcap, 'at': pcat}, open(cap_f, 'w'))
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
        pok = max(pok, b); nfail = 0
        end_note(b=b); hist(at=stamp, api=api, t=t, page=page, K=K, st=200, a=a, b=b, n=len(seq))
        if plast and b >= plast * 0.97:
            plast = None                                      # 끝자리 너머가 받아졌다 — 옛 끝자리는 잊는다
        if pcap and b >= pcap:
            pcap = None                                       # 끝자리로 본 곳보다 뒤가 받아졌다 — 다시 재게 둔다
        if page > 1 and a > 0:
            dens = (page - 1) * 30000.0 / (a * t)   # 앞선 a 곳이 (쪽-1)×3만 줄을 채웠다
        saved = 0
        for n, i in enumerate(seq):
            edge = n == 0 or n == len(seq) - 1   # 쪽 끝에 걸린 교차로는 줄이 잘렸을 수 있다
            if not edge:
                seen[i] = seen.get(i, 0) + 1
            red = (reduce_phase(i, by[i]) if api == 'p' else reduce_one(i, by[i])) if len(by[i]) >= 240 else None
            if red and red.get('cyc'):
                json.dump(red, open(os.path.join(RAW, 'red', '%s_%s%s.json' % (i, stamp, 'p' if api == 'p' else '')), 'w', encoding='utf-8'), ensure_ascii=False); saved += 1
            elif not edge and len(by[i]) >= 420:
                tried.add(i)
            elif not edge and len(by[i]) >= 240:
                smiss[i] = smiss.get(i, 0) + 1                  # 정각 창(짧은 줄)에서 주기를 못 읽은 횟수 — 세 번이면 그만 받는다(안 그러면 그 구가 끝나지 않아 다음 구로 못 넘어간다)
                if smiss[i] >= 3:
                    tried.add(i)   # 7분 넘게 받았는데 주기를 못 읽은 곳(값이 멈춤·점멸) — 다시 받지 않는다 · 줄이 짧은 정각 창에서는 넣지 않는다(19:04 에 100곳 넘게 잘못 들어갔다)
        json.dump(sorted(tried), open(tried_f, 'w')); json.dump(smiss, open(smiss_f, 'w'))
        last = {'t': t, 'a': a, 'b': b, 'base': (page - 1) * 30000, 'rows': [(pos[i], len(by[i])) for i in seq if i in pos]}
        hit = a <= K <= b
        A2 = anchors()
        if hit and order[K] not in tried and not (A2.get(order[K]) and len(A2[order[K]]) > len(A.get(order[K], []))):
            stuck[K] = stuck.get(K, 0) + 1
            if stuck[K] >= 3:
                tried.add(order[K]); json.dump(sorted(tried), open(tried_f, 'w'))   # 두 번 받고도 주기를 못 읽은 곳은 건너뛴다
        miss = 0 if hit else miss + 1
        print(stamp, '[상태]' if api == 'p' else '[잔여]', '쪽', page, '줄', len(J), '교차로', len(seq), '자리', a, '~', b, '(찾던 자리', K, '맞음' if hit else '빗나감', ') 구움', saved, '밀도', round(dens, 3), '우선 목록 — 닻 없음', len([i for i in pref if need1(i)]), '· 이 시각대 빈 곳', len([i for i in pref if needS(i)]), ('· 끝자리 %d' % pcap) if pcap else '', flush=True)
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


def segments(rows, k, tail=False):
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
    res = out[1:] if out else []   # 첫 구간은 앞이 잘렸을 수 있다
    if tail and out and start is not None and not bad and start_v < 3000 and prev_t - start <= start_v + 2:
        res.append((start, start_v, start_v))   # 받은 줄 끝에 걸린 마지막 구간 — 시작을 봤으므로 시작 때 잔여가 곧 그 구간 길이(정각 창처럼 줄이 짧을 때 적색을 살린다)
    return res


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
    ci = plan_ci(cyc, int(round(cx)) if abs(cx - round(cx)) <= 0.25 else round(cx, 1))
    for x in mv + pd:
        x.pop('gs', None)
    hh = lambda t: datetime.datetime.fromtimestamp(t).strftime('%H:%M')
    return {'id': str(itst), 'day': datetime.datetime.fromtimestamp(t0).strftime('%Y-%m-%d'), 'dow': datetime.datetime.fromtimestamp(t0).isoweekday() % 7, 'from': hh(t0), 'to': hh(t1), 'rows': len(rows),
            'cyc': cyc, 'mv': mv, 'ped': [{'d': q['d'], 'seg': [], 'n': q['n']} for q in pd], 'pd': pd, 'a': (round(rs[-1], 1) if abs(ci - cyc) <= 2 else None), 'ci': ci, 'end': round(t1, 1), 'ncy': ncy, 'src': 'p'}


def dir_bad(mvrows, cyc):
    # 방위 표기 점검 — 네 방향 직진이 다 있을 때, 직각 방향 직진끼리 녹색이 겹치는 초가 마주 보는 방향끼리보다 많으면 True
    # (2026-10-10 교대역 4045: 동·남이 함께, 북·서가 함께 녹색 — 실제로는 있을 수 없다 → 원자료 방위 이름이 틀림)
    S = {m[0]: m for m in mvrows if m[1] == 'St' and m[2] is not None and m[5] is not None}
    if not all(d in S for d in ('nt', 'et', 'st', 'wt')) or not cyc:
        return False
    c = int(round(cyc))
    def ov(a, b):
        return sum(1 for t in range(c) if ((t - a[5]) % c) < a[2] and ((t - b[5]) % c) < b[2])
    opp = ov(S['nt'], S['st']) + ov(S['et'], S['wt'])
    per = ov(S['nt'], S['et']) + ov(S['nt'], S['wt']) + ov(S['st'], S['et']) + ov(S['st'], S['wt'])
    return per > opp


def plan_ci(cyc, ci):
    # 이어 세는 주기 — 계획 주기(녹+황+적 합의 중앙값)가 정수 초에 가깝고 다시 잰 값이 그 ±2.5초 안이면 계획 주기를 쓴다.
    # 2026-10-10 교대역(4045): 계획 170초인데 녹색 시작 간격(주기 2~3개)으로 다시 잰 값이 172 → 주기마다 2초씩 밀려 2시간 뒤 100초 어긋났다(소유자 현장 확인).
    if cyc and abs(cyc - round(cyc)) <= 0.25 and ci and abs(ci - round(cyc)) <= 2.5:
        return int(round(cyc))
    return ci


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
            sg = segments(rows, k, tail=True)
            sg = [s for s in sg if abs(s[1] - s[2]) <= 3.5]   # 구간 길이 ≈ 시작 때 잔여(끊김·튐 거르기)
            if m == 'Pd':
                ped.append({'d': d, 'seg': [round(s[1]) for s in sg[:12]], 'n': len(sg)})
                continue
            G, Y, R, gs = [], [], [], []
            for i in range(1, len(sg) - 1):
                if 2.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and sg[i + 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2 and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2:
                    G.append(sg[i - 1][1]); Y.append(sg[i][1]); R.append(sg[i + 1][1]); gs.append(sg[i - 1][0])
            if len(G) < (2 if t1 - t0 > 430 else 1):   # 7분 넘게 받았으면 두 번 본 것만 · 정각 창(5분 안팎)은 한 번 본 것도 쓴다(2026-10-10 20:04 — 290줄에 103곳 중 15곳만 구워졌다)
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
        ci = plan_ci(cyc, int(round(cx)) if abs(cx - round(cx)) <= 0.25 else round(cx, 1))
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
        for r in v:
            if r.get('ci'):
                r['ci'] = plan_ci(r['cyc'], r['ci'])
                if abs(r['ci'] - r['cyc']) > 2.5:
                    r['a'] = None   # 다시 잰 주기가 계획 주기와 2.5초 넘게 다르면(계획이 바뀌는 중 등) 이어 세지 않는다 — 길이만 보인다
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
            if dir_bad(o['mv'], r['cyc']):
                o['dq'] = 'dir'   # 방위 이름이 실제와 다르다(직각 방향이 함께 녹색) — 지도는 경고를 붙인다
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
           'fields': 'pts{교차로 번호: [위도, 경도, 이름]} · its{교차로 번호: [기록…]} 기록 = {day 받은 날, dow 요일(0 일), from~to 받은 시각, cyc 주기 초, mv[[방위, 이동류, 녹색, 황색, 적색, 녹색 시작(주기 안), 본 횟수(, 2 = 한 주기에 두 번)]], pd[[방위, 보행 녹색, 점멸, 적색, 녹색 시작, 본 횟수]](신호 상태 API 로 받은 기록만), ped[[방위, …]](보행 신호가 있는 쪽), a 기준 이동류 녹색이 켜진 실제 시각(epoch 초), ci 주기(이어 세기용), v[띄운 분, 어긋난 초](두 번 대조 통과), x[…](대조 실패), src p = 신호 상태 API, dq dir = 원자료의 방위 이름이 실제와 다름(직각 방향 직진이 함께 녹색 — 초는 쓸 수 있어도 어느 쪽인지는 현장 확인)} · tod{교차로 번호: [[요일 갈래 0 평일·1 토·2 일, 시, 주기 초]]} · pl{교차로 번호: [[요일 갈래(0 월~목 · 1 금 · 2 토 · 3 일), 시, 주기, 자정 기준 옵셋(기준 이동류 녹색이 켜지는 하루 초 mod 주기), 받은 달-날]]}(시계로 이어 세는 표 — 기록의 cl·ci 가 같은 것이 그 계획의 방향별 초)',
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
        pf = read_list(a[2]) if len(a) > 2 and a[1] == '--list' else None
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
