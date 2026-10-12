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


def key2():
    """둘째 열쇠(2026-10-11 소유자가 하나 더 받음 · keys.json 의 t_data_seoul2) — 없으면 None. 값은 찍지 않는다."""
    try:
        v = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig')).get('t_data_seoul2')
        return v if isinstance(v, str) and len(v) > 8 else None
    except Exception:
        return None


def mask(t):
    """기록에 찍기 전에 열쇠 값을 가린다(두 열쇠 모두)."""
    t = t.replace(key(), '***')
    k = key2()
    return t.replace(k, '***') if k else t


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


def anchors(strong=False):
    """교차로마다 닻을 받은 시각들(epoch) — red 파일을 한 번만 읽어 둔다.
    strong=True 면 8분 넘게 받은 창의 닻만(2026-10-11 — 정각 직후 5분 창은 계획이 바뀌는 사이의 값이 섞인다: 서울고교 일 13·14·15시가 모두 4~10분 창이라 주기 197·160·168 · 옵셋 122·83·153)."""
    out = {}
    for f in glob.glob(os.path.join(RAW, 'red', '*.json')):
        if f not in _AC:
            try:
                r = json.load(open(f, encoding='utf-8'))
                w9 = (int(r['to'][:2]) * 60 + int(r['to'][3:5])) - (int(r['from'][:2]) * 60 + int(r['from'][3:5]))
                _AC[f] = (r['id'], r.get('a'), w9 >= 8)
            except Exception:
                _AC[f] = (None, None, False)
        i, a, st9 = _AC[f]
        if i and a and (st9 or not strong):
            out.setdefault(i, []).append(a)
    return out


def split_write(doc):
    """지도(폰)가 읽는 꼴 — data/sigdir/index.json(기록 its 를 뺀 나머지 + fl 교차로마다 표시 · cell 칸 크기) + data/sigdir/c/<칸>.json(그 칸 교차로들의 its).
    칸 = floor(위도 / 0.03)_floor(경도 / 0.04) (약 3.3 × 3.5km) · 자리 없는 교차로는 'x'. fl 값: 1 = 다시 받아 맞은 기록(v)이 있다 · 2 = 닻(a)이 있다(더한 값).
    한 장짜리 data/sigdir-seoul.json 은 그대로 둔다. 조각은 내용이 바뀐 것만 다시 쓴다."""
    import math
    CELL = [0.03, 0.04]
    d = os.path.join(ROOT, 'data', 'sigdir')
    os.makedirs(os.path.join(d, 'c'), exist_ok=True)
    its, pts = doc['its'], doc['pts']
    cells, fl = {}, {}
    for k, L in its.items():
        q = pts.get(k)
        key = '%d_%d' % (math.floor(q[0] / CELL[0]), math.floor(q[1] / CELL[1])) if q else 'x'
        cells.setdefault(key, {})[k] = L
        fl[k] = (1 if any(o.get('v') for o in L) else 0) + (2 if any(o.get('a') for o in L) else 0)
    nw = 0
    for key, part in cells.items():
        t = json.dumps({'schema': 'tg-sigdir-cell/1', 'cell': key, 'its': part}, ensure_ascii=False, separators=(',', ':'))
        fp = os.path.join(d, 'c', key + '.json')
        try:
            old = open(fp, encoding='utf-8').read()
        except Exception:
            old = None
        if old != t:
            open(fp, 'w', encoding='utf-8').write(t); nw += 1
    idx = {k: v for k, v in doc.items() if k != 'its'}
    idx['schema'] = 'tg-sigdir-idx/1'
    idx['cell'] = CELL
    idx['cells'] = {k: len(v) for k, v in sorted(cells.items())}
    idx['fl'] = fl
    idx['fields'] = 'fl{교차로 번호: 표시(1 다시 받아 맞은 기록이 있다 + 2 닻이 있다)} · cell[위도 칸, 경도 칸] · cells{칸: 교차로 수} · 기록(its)은 c/<칸>.json 의 its{교차로 번호: [기록…]} — 칸 = floor(위도/cell[0])_floor(경도/cell[1]) · 자리 없는 교차로는 x · ' + doc.get('fields', '')
    ip = os.path.join(d, 'index.json')
    json.dump(idx, open(ip, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('나눠 쓰기: 색인', os.path.getsize(ip), 'B · 칸', len(cells), '· 바뀐 칸', nw)


def publish():
    """data/sigdir-seoul.json 과 맞대 본 결과 data/sig-audit.json 만 올린다(다른 파일은 건드리지 않는다) — 열쇠 검사에 걸리면 올리지 않는다."""
    import subprocess
    run = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    try:
        if not run('git', 'status', '--porcelain', '--', 'data/sigdir-seoul.json', 'data/live-spd-seocho.json').stdout.strip():
            return
        run(sys.executable, '-X', 'utf8', os.path.join('tools', 'signal', 'sig-audit.py'))   # 맞대 본 결과(data/sig-audit.json)도 같이 다시 만든다
        run('git', 'add', '--', 'data/sigdir-seoul.json', 'data/sigdir', 'data/sig-audit.json', 'data/live-spd-seocho.json')            # 열쇠 검사는 올릴 준비가 된 변경만 본다 — 먼저 올릴 준비를 한다
        if run(sys.executable, '-X', 'utf8', os.path.join('tools', 'keycheck.py')).returncode != 0:
            print('열쇠 검사에 걸려 올리지 않았다', flush=True); return
        run('git', 'pull', '-q', '--ff-only', 'origin', 'main')
        c = run('git', 'commit', '-q', '-m', 'sigdir: 방향별 신호 자동 갱신\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', '--', 'data/sigdir-seoul.json', 'data/sigdir', 'data/sig-audit.json', 'data/live-spd-seocho.json')
        p2 = run('git', 'push', '-q', 'origin', 'main')
        print(datetime.datetime.now().strftime('%H:%M:%S'), '올림' if c.returncode == 0 and p2.returncode == 0 else '올리기 실패 ' + (c.stderr or p2.stderr)[:120], flush=True)
    except Exception as e:
        print('올리기 실패', str(e)[:120], flush=True)


def livespd():
    """서초 둘레 지금 통행속도 한 장(data/live-spd-seocho.json) — 굽는 도구(tools/signal/livespd-bake.py · ITS trafficInfo 한 번)를 부른다. 열쇠 없는 기기가 맛보기 30분 동안 방향별 막힘을 보는 바탕(2026-10-11 소유자).
    ITS 월 한도 10,000건 — 10분에 한 번이면 4,320건. 실패해도 수집은 그대로 간다"""
    import subprocess
    try:
        r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'tools', 'signal', 'livespd-bake.py')], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=90)
        print(datetime.datetime.now().strftime('%H:%M:%S'), '[소통]', (r.stdout or r.stderr or '').strip()[:140], flush=True)
        return r.returncode == 0
    except Exception as e:
        print('[소통] 실패', type(e).__name__, flush=True); return False


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
    end_f, hist_f = os.path.join(RAW, 'pend_p.json' if api == 'p' else 'pend_t.json'), os.path.join(RAW, 'sweep_hist.jsonl')   # 장부는 API 마다 따로(2026-10-11 — 두 API 의 끝자리가 다르다)
    def end_load():
        try:
            e = json.load(open(end_f))
            if isinstance(e.get('oks'), list) and isinstance(e.get('fails'), list):
                return e
        except Exception:
            pass
        return {'oks': [], 'fails': []}
    def end_note(k=None, b=None):
        e = end_load(); nw = time.time()
        if b is not None:
            e['oks'].append([int(b), nw])
        if k is not None:
            e['fails'].append([int(k), nw])
        e['oks'] = [q for q in e['oks'] if nw - q[1] < 3600][-40:]; e['fails'] = [q for q in e['fails'] if nw - q[1] < 3600][-40:]
        try:
            json.dump(e, open(end_f, 'w'))
        except Exception:
            pass
    def hist(**kw):
        try:
            open(hist_f, 'a', encoding='utf-8').write(json.dumps(kw, ensure_ascii=False) + '\n')
        except Exception:
            pass
    # (2026-10-11) 다시 띄울 때의 헛호출 막기 — 호출할 때마다 시각을 lastcall_<api>.txt 에 남기고, 뜰 때 그 시각에서 GAP 이 안 지났으면 남은 만큼 기다린다.
    #  종전엔 뜨자마자 불러서, 멈추기 직전의 호출과 5분 안에 겹쳐 두 훑기가 한 번씩 429(V2X_REPEAT_CALL_LIMIT)를 받았다(19:50 · 19:52)
    stamp_f = os.path.join(RAW, 'lastcall_%s.txt' % api)
    try:
        w9 = GAP + 3 - (time.time() - float(open(stamp_f, encoding='utf-8').read().strip()))
        if 0 < w9 <= GAP + 3:
            print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), '직전 호출에서 5분이 안 지났다 — %d초 기다린 뒤 시작' % int(w9), flush=True)
            time.sleep(w9)
    except Exception:
        pass
    # 둘째 열쇠 — 살아 있으면(200 · 429 = 알아보는 열쇠) 두 열쇠를 번갈아 쓴다: 열쇠마다 GAP(5분 제한)을 지키고 호출 사이는 GAP ÷ 2.
    #  ⚠ 5분 제한이 열쇠마다 따로인지는 **확인되지 않았다**(계정이 같으면 같이 쓸 수도) — 번갈아 쓰기 시작한 뒤 429 가 세 번 나면 같이 쓰는 것으로 보고 둘째 열쇠를 여섯 시간 쉰다.
    #  발급 직후에는 404(「관리자에게 문의」 — 가짜 열쇠와 같은 응답)가 온다 → 30분마다 작은 요청(3줄)으로 다시 본다. 둘째 열쇠가 없거나 죽어도 수집은 첫 열쇠로 그대로 돈다
    k2 = {'ok': False, 'chk': 0.0, 'last': {1: 0.0, 2: 0.0}, 'n': 0, 'n200': 0, 'n429': 0, 'nemp': 0, 'rest': 0.0}
    def k2probe():
        kv = key2(); k2['chk'] = time.time()
        if not kv or time.time() < k2['rest']:
            return
        try:
            r9 = urllib.request.urlopen(urllib.request.Request((BASEP if api == 'p' else BASE) + '?apikey=' + kv + '&pageNo=1&numOfRows=3', headers={'User-Agent': 'Mozilla/5.0'}), timeout=60); st9 = r9.status; r9.read()
        except urllib.error.HTTPError as e9:
            st9 = e9.code
        except Exception:
            st9 = 0
        st8 = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if st9 in (200, 429):
            k2['ok'] = True; k2['last'][2] = time.time()
            print(st8, '둘째 열쇠가 살아 있다(HTTP %d) — 두 열쇠를 번갈아 쓴다(열쇠마다 %d초 · 호출 사이 %d초)' % (st9, GAP, GAP // 2), flush=True)
        else:
            print(st8, '둘째 열쇠 아직 안 됨(HTTP %d) — 30분 뒤 다시 본다 · 첫 열쇠로 그대로 돈다' % st9, flush=True)
        hist(at=st8, api=api, k=2, probe=1, st=st9)
    W0 = 300 if api == 'p' else 285   # (2026-10-10 19:04 실측 — 줄 수 = 정각 뒤 초 − 8쯤 · 240초에는 234줄이라 문턱 240 에 못 미쳤다 → 285초)  # 정각 뒤 창 — 이때는 교차로마다 300줄쯤이라 한 쪽에 100곳 가까이 들고, 서울 뒤쪽(서초 1668~ · 강남 ~2248)도 20쪽 안이다
    os.makedirs(os.path.join(RAW, 'red'), exist_ok=True)
    spd_at = 0
    while True:
        if api != 'p' and time.time() - spd_at >= 600:
            spd_at = time.time()                              # 10분에 한 번 통행속도 한 장 — 신호를 받았든 못 받았든(잔여시간 훑기 쪽에서만)
            if livespd(): publish()
        A = anchors(); AS = anchors(True)
        nowt = time.time()
        now = datetime.datetime.now()
        t = now.minute * 60 + now.second
        slot_of = lambda ts: (cls_of((datetime.datetime.fromtimestamp(ts).weekday() + 1) % 7, datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')), datetime.datetime.fromtimestamp(ts).hour)
        nslot = slot_of(nowt)
        if seen_slot != nslot:
            seen_slot, seen = nslot, {}                       # 시각대가 바뀌면 「이 시각대에 몇 번 받아 봤나」를 다시 센다
        need1 = lambda i: i not in tried and not A.get(i) and seen.get(i, 0) < 3                                   # 닻이 아직 없는 곳
        needS = lambda i: i not in tried and A.get(i) and seen.get(i, 0) < 2 and not any(slot_of(a) == nslot for a in AS.get(i, []))   # 닻은 있는데 지금 요일 갈래·지금 시각대 값이 없는 곳(시각대 표 채우기 · 두 번 받아도 안 되면 이 시각대는 넘긴다)
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
        fl = sorted(q[0] for q in E['fails'] if time.time() - q[1] < 1500 and not any(o[0] >= q[0] and o[1] > q[1] for o in E['oks']))   # 25분 안의 500 가운데 「그 뒤에 그 자리 이상을 받은 적이 없는」 것
        if len(fl) >= 2:
            sc = max(50, fl[0] - 30)                          # 유효한 실패가 둘 — 가장 앞 실패 자리 바로 앞을 끝자리로(되는 곳 위주로 · 끝자리는 시각대 안에서도 내려간다)
            if not pcap or sc < pcap:
                pcap, pcat = sc, time.time()
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
        if not k2['ok'] and time.time() - k2['chk'] > 1800:
            k2probe()
        kn = 1
        if k2['ok']:
            kn = 1 if k2['last'][1] <= k2['last'][2] else 2      # 더 오래 쉰 열쇠
            w9 = k2['last'][kn] + GAP - time.time()
            if w9 > 0:
                time.sleep(w9 + 1); continue                   # 그 열쇠의 5분이 안 찼다 — 기다렸다가 처음부터 다시 고른다(시각·쪽이 달라졌다)
        kv = key2() if kn == 2 else key()
        if not kv:
            k2['ok'] = False; kv, kn = key(), 1
        k2['last'][kn] = time.time()
        u = (BASEP if api == 'p' else BASE) + '?apikey=' + kv + '&pageNo=%d&numOfRows=30000' % page
        try:
            try:
                open(stamp_f, 'w', encoding='utf-8').write(str(time.time()))
            except Exception:
                pass
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=400); st = r.status; body = r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            st = e.code; body = e.read().decode('utf-8', 'ignore')
        except Exception as e:
            st = 0; body = str(e)
        stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        if st != 200:
            print(stamp, '쪽', page, 'HTTP', st, mask(body[:160]) + (' [열쇠 2]' if kn == 2 else ''), flush=True)
            hist(at=stamp, api=api, t=t, page=page, K=K, st=st, k=kn)
            wait = GAP // 2 if k2['ok'] else GAP
            if k2['ok']:
                k2['n'] += 1
                if st == 429:
                    k2['n429'] += 1
                    if k2['n429'] >= 3:
                        k2['ok'] = False; k2['rest'] = time.time() + 6 * 3600; k2['n429'] = 0
                        print(stamp, '번갈아 쓰는 동안 429 가 세 번 — 두 열쇠가 5분 제한을 같이 쓰는 것으로 본다 · 둘째 열쇠를 여섯 시간 쉰다(첫 열쇠로 그대로)', flush=True)
                elif kn == 2 and st in (401, 403, 404):
                    k2['ok'] = False; k2['chk'] = time.time()
                    print(stamp, '둘째 열쇠가 안 받아진다(HTTP %d) — 첫 열쇠로 돌아간다 · 30분 뒤 다시 본다' % st, flush=True)
            if st == 500 and page > 1:
                # 끝자리 = 찾던 자리(K) 바로 앞 — 줄 수로 되짚으면(쪽 ÷ 밀도 × 초) 자료가 늦게 쌓일 때 너무 앞으로 잡힌다(22:25 — 1667 까지 받아 놓고 끝자리를 1617 로 봤다). 이 시각대에 실제로 받은 맨 뒤 자리(pok)보다 앞으로는 안 당긴다
                # 한 번 실패로는 끝자리를 당기지 않는다 — 있는 쪽도 가끔 500 이 난다(22:39 에 1514~1527 을 받았는데 22:45 에 같은 둘레가 500). 한 번이면 그 둘레만 다음 한 번 비켜 가고, 잇달아 두 번이면 끝자리로 본다(20분)
                nfail += 1; avoid = K; last = None
                end_note(k=K)
                if plast and K >= plast * 0.97:
                    # 소유자 2026-10-10 밤 「안 되는 곳보다는 되는 곳 위주로」 — 방금 풀어 준 끝자리 너머를 찔러 봤는데 또 안 된다 → 바로 되돌리고 40분은 되는 곳만 받는다(종전엔 20분마다 두 번씩 헛받았다)
                    pcap = max(50, min(plast, K - max(1, per // 2))); pcat = time.time() + 1200; plast = None
                elif nfail >= 2:
                    pcap = max(50, min(pcap or 1e9, K - max(1, per // 2))); pcat = time.time()
                json.dump({'pos': pcap, 'at': pcat}, open(cap_f, 'w'))
            if st == 429:
                try: wait = int(json.loads(body).get('retryAfterSeconds', GAP)) + 5
                except Exception: pass
                if k2['ok']:
                    k2['last'][kn] = time.time() + wait - GAP        # 그 열쇠는 서버가 말한 때까지 쉰다 — 다른 열쇠는 제 차례에 그대로
                    wait = min(wait, GAP // 2)
            time.sleep(wait); continue
        J = json.loads(body); by = {}; seq = []
        for x in J:
            i = str(x['itstId'])
            if i not in by: by[i] = []; seq.append(i)
            by[i].append(x)
        idx = [pos[i] for i in seq if i in pos]
        if not idx:
            print(stamp, '[상태]' if api == 'p' else '[잔여]', '쪽', page, '줄', len(J), '— 아는 교차로가 없다(밀도', round(dens, 3), ')', flush=True)
            if k2['ok']:
                k2['n'] += 1; k2['nemp'] += 1
            dens *= 0.8; time.sleep(GAP // 2 if k2['ok'] else GAP); continue
        a, b = min(idx), max(idx)
        pok = max(pok, b); nfail = 0
        end_note(b=b); hist(at=stamp, api=api, t=t, page=page, K=K, st=200, a=a, b=b, n=len(seq), k=kn)
        if k2['ok']:
            k2['n'] += 1; k2['n200'] += 1
            if k2['n'] in (6, 24):
                print(stamp, '두 열쇠 번갈아 %d번 — 받음 %d · 429 %d · 빈 응답 %d' % (k2['n'], k2['n200'], k2['n429'], k2['nemp']), flush=True)
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
        time.sleep(GAP // 2 if k2['ok'] else GAP)


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
    # (2026-10-11) 창 앞쪽에 계획이 바뀌는 사이의 늘어난 주기가 섞이면 처음~끝을 주기 수로 나눈 값이 틀어져 닻을 버렸다(이수교차로 일 08:00~08:33 = 가운데값 160초 · 나눈 값 167.3초).
    #  닻은 **끝**에서 이어 세는 것이니 끝의 세 주기가 가운데값 주기와 같으면(±1.5초) 그 주기로 닻을 잡는다
    iv = [rs[i + 1] - rs[i] for i in range(len(rs) - 1)]
    if len(iv) >= 2 and all(abs(q - cyc) <= 1.5 for q in iv[-2:]) and abs(cyc - round(cyc)) <= 0.3:
        ci = plan_ci(cyc, int(round(cyc)))
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


def cyc_key(r):
    """build() 가 기록을 묶는 주기(정수 초) — 다시 잰 주기(ci)가 받은 주기(cyc)의 ±2.5초 안이면 ci, 아니면 받은 주기.
    (2026-10-11) 종전엔 늘 ci 였다: 영등포구청앞(139) 16시 = 받은 주기 100초인데 녹색 시작 간격으로 다시 잰 값이 80초 → 닻은 버리면서(build 앞머리) 묶는 열쇠는 80 으로 남아,
    ① 빈 구간을 80초 주기로 재서 보행 신호(30초)가 들어갈 33초 구간이 13초로 보였고 ② 주기가 다른 기록끼리 한 열쇠로 겹쳐 하나가 사라졌다(같은 곳 04시 70초 · 09시 75초)"""
    ci = r.get('ci')
    if ci and abs(ci - r['cyc']) <= 2.5:
        return int(round(ci))
    return int(round(r['cyc']))


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
                ped.append({'d': d, 'seg': [round(s[1]) for s in sg[:12]], 'n': len(sg), '_sg': sg})
                continue
            G, Y, R, gs = [], [], [], []
            for i in range(1, len(sg) - 1):
                if 2.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and sg[i + 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2 and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2:
                    G.append(sg[i - 1][1]); Y.append(sg[i][1]); R.append(sg[i + 1][1]); gs.append(sg[i - 1][0])
            if len(G) < (2 if t1 - t0 > 430 else 1):   # 7분 넘게 받았으면 두 번 본 것만 · 정각 창(5분 안팎)은 한 번 본 것도 쓴다(2026-10-10 20:04 — 290줄에 103곳 중 15곳만 구워졌다)
                mv.append({'d': d, 'm': m, 'n': len(G), 'seg': [round(s[1]) for s in sg[:10]], '_sg': sg})   # 색을 못 가린 이동류(점멸 운영 등)
                continue
            g, y, r = med(G), med(Y), med(R)
            mv.append({'d': d, 'm': m, 'g': g, 'y': y, 'r': r, 'n': len(G), 'gs': gs})
            cyc_all.append(g + y + r)
    if not mv and not ped:
        return None
    cyc = med(cyc_all)
    # (2026-10-11 소유자 「이수역 … 중간에 붕 뜬다 올레드 … 40초가 넘는다」) 적색 구간이 걸러진 이동류 살리기 —
    #  이수역(1552) 일 14시: 동쪽 직진 구간이 [46, 4, 46, 4 …] · 서쪽 [55, 4, 55, 4 …] = 녹색·황색은 읽혔는데 적색의 잔여시간이 모름 값이라 적색 구간이 통째로 빠져
    #  「긴 구간 — 황색 — 긴 구간」 규칙에 못 들었다(그 59초가 지도에서 올레드처럼 비었다). 다른 이동류로 주기를 알면:
    #  ① 긴 구간 바로 뒤에 황색(2.5~6.5초)이 붙고 ② 그 황색 뒤는 비어 있고(적색이 걸러진 자리 — 뒤가 붙어 있으면 짧은 녹색+황색일 수 있어 안 쓴다)
    #  ③ 그런 쌍이 두 번 이상 · 녹색 길이가 서로 2.5초 안 · 녹색 시작 간격이 주기의 정수배(±2.5초)면 녹색·황색을 그 값으로, 적색 = 주기 − 녹색 − 황색.
    if not cyc:
        # 온전한 「녹 — 황 — 적」 한 벌을 이동류마다 한 번씩만 본 긴 창(600줄에 주기 160초 = 세 주기 남짓인데 앞뒤가 잘림) — 여러 이동류의 한 벌 합이 서로 같으면(±2초 · 셋 이상) 그 값이 주기다
        sums = []
        for x in mv:
            sg = x.get('_sg') or []
            for i in range(1, len(sg) - 1):
                if 2.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and sg[i + 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2 and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2:
                    sums.append(sg[i - 1][1] + sg[i][1] + sg[i + 1][1])
        if len(sums) >= 3 and max(sums) - min(sums) <= 2:
            cyc = med(sums)
    if cyc:
        for x in mv:
            sg = x.get('_sg')
            if 'g' in x or not sg:
                continue
            # (같은 날) 둘째 규칙 — 「긴 구간 — 짧은 구간(1.5~6.5초) — 긴 구간」이 붙어 있고 **셋을 더하면 주기**(±2.5초)인 한 벌.
            #  황색이 2초쯤으로 읽히는 곳(3001 = [15, 2, 113] · 주기 130)과, 8분 넘는 창에서 온전한 한 벌을 한 번만 본 곳(1483 = [35, 5, 140] · 주기 180)이 여기서 산다.
            #  주기와 맞는다는 것이 「두 번 봤다」를 대신한다 — 여러 벌이면 녹색 길이가 서로 2.5초 안이어야 한다.
            G, Y, R, gs = [], [], [], []
            for i in range(1, len(sg) - 1):
                if (1.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and sg[i + 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2
                        and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2 and abs(sg[i - 1][1] + sg[i][1] + sg[i + 1][1] - cyc) <= 2.5):
                    G.append(sg[i - 1][1]); Y.append(sg[i][1]); R.append(sg[i + 1][1]); gs.append(sg[i - 1][0])
            if G and max(G) - min(G) <= 2.5:
                x.update({'g': med(G), 'y': med(Y), 'r': med(R), 'n': len(G), 'gs': gs, 'rx': 2})
                x.pop('seg', None)
                continue
            G, Y, gs = [], [], []
            for i in range(1, len(sg)):
                if not (2.5 <= sg[i][1] <= 6.5 and sg[i - 1][1] > 6.5 and abs(sg[i - 1][0] + sg[i - 1][1] - sg[i][0]) < 2):
                    continue
                if i + 1 < len(sg) and abs(sg[i][0] + sg[i][1] - sg[i + 1][0]) < 2:
                    continue
                G.append(sg[i - 1][1]); Y.append(sg[i][1]); gs.append(sg[i - 1][0])
            if len(G) < 2 or max(G) - min(G) > 2.5:
                continue
            sp = [gs[i + 1] - gs[i] for i in range(len(gs) - 1)]
            if not all(round(q / cyc) >= 1 and abs(q - round(q / cyc) * cyc) <= 2.5 for q in sp):
                continue
            g, y = med(G), med(Y)
            if cyc - g - y <= 6.5:
                continue
            x.update({'g': g, 'y': y, 'r': round(cyc - g - y, 1), 'n': len(G), 'gs': gs, 'rx': 1})
            x.pop('seg', None)
    ok = [x for x in mv if 'g' in x]
    # 녹색 시작 자리(주기 안) — 녹색이 가장 긴 이동류의 시작을 0 으로
    if ok and cyc:
        ref = max(ok, key=lambda x: (x['g'], -DIRS.index(x['d'])))   # 기준 이동류 = 녹색이 가장 긴 것(살린 이동류도 같은 규칙 — build() 의 기준 이동류 열쇠·지도의 plShift 와 한결같아야 한다)
        rs = sorted(ref['gs'])
        for x in ok:
            offs = []
            for s0 in x['gs']:
                prev = [r for r in rs if r <= s0 + 1]   # 이 녹색 바로 앞의 기준 녹색 시작(주기마다 따로 재서 통신 끊김 뒤 어긋남을 피한다)
                if prev and s0 - prev[-1] < cyc + 2:
                    offs.append(max(0, s0 - prev[-1]))
            if not offs:
                # (2026-10-11) 앞선 기준 녹색을 못 본 이동류(창이 짧아 이 녹색이 기준 녹색보다 먼저 한 번만 보인 것) — 바로 뒤 기준 녹색에서 거꾸로 센다(주기 − 간격). 없으면 지도가 자리를 0 으로 잘못 놓는다
                for s0 in x['gs']:
                    nxt = [r for r in rs if r > s0 + 1]
                    if nxt and nxt[0] - s0 < cyc + 2:
                        offs.append((cyc - (nxt[0] - s0)) % cyc)
            x['o'] = int(round(statistics.median(offs))) % int(round(cyc)) if offs else None
    # (2026-10-11 소유자 「빈자리를 없애야지」) 보행 신호 시간 — 잔여시간 기록에는 색이 없지만, 되풀이되는 구간 가운데 **같은 축 차량 직진의 녹색 안에 드는 것**이 보행 시간이다
    #  (서울 신호 상태 기록 1,036쌍 가운데 818쌍에서 보행 녹색이 같은 축 직진 녹색 안 · 직각 축은 7쌍). 같은 축 직진이 없으면(건널목만 있는 연등) 직각 축 직진의 녹색과 겹치지 않는 구간.
    #  녹색과 점멸을 나눠 읽지는 못한다 → 합(g)과 자리(o)만 · build 가 pd 줄 일곱째 칸 2 로 싣는다
    if ok and cyc:
        c7 = int(round(cyc)); ref7 = max(ok, key=lambda x: (x['g'], -DIRS.index(x['d']))); rs7 = sorted(ref7.get('gs') or [])
        gset = {}
        for x in ok:
            if x['m'] == 'St' and x.get('o') is not None:
                gset.setdefault(DIRS.index(x['d']) % 4, set()).update(t % c7 for t in range(int(x['o']), int(x['o'] + x['g'])))
        need7 = 2 if t1 - t0 > 430 else 1
        for q in ped:
            cl7 = []                                        # [길이 합, 자리들, 수]
            for s0, ln, sv in (q.get('_sg') or []):
                if not (6.5 < ln < 0.75 * cyc):
                    continue
                prev = [r for r in rs7 if r <= s0 + 1]
                nxt = [r for r in rs7 if r > s0 + 1]
                if prev and s0 - prev[-1] < cyc + 2:
                    of7 = (s0 - prev[-1]) % cyc
                elif nxt and nxt[0] - s0 < cyc + 2:
                    of7 = (cyc - (nxt[0] - s0)) % cyc
                else:
                    continue
                for c in cl7:
                    if abs(c[0] / c[2] - ln) <= 2 and min((c[1][0] - of7) % cyc, (of7 - c[1][0]) % cyc) <= 3:
                        c[0] += ln; c[1].append(of7); c[2] += 1; break
                else:
                    cl7.append([ln, [of7], 1])
            ax7 = DIRS.index(q['d']) % 4
            good = []
            for c in cl7:
                if c[2] < need7:
                    continue
                L7, o7 = c[0] / c[2], c[1][0]
                P7 = set(t % c7 for t in range(int(round(o7)), int(round(o7 + L7))))
                fs = len(P7 & gset[ax7]) / float(len(P7)) if gset.get(ax7) and P7 else None
                fp = len(P7 & gset[(ax7 + 2) % 4]) / float(len(P7)) if gset.get((ax7 + 2) % 4) and P7 else None
                if (fs is not None and fs >= 0.8 and (fp is None or fp <= 0.2)) or (fs is None and fp is not None and fp <= 0.1):
                    good.append((round(L7, 1), int(round(o7)) % c7, c[2]))
            if len(good) == 1:
                q['g'], q['o'], q['gn'] = good[0]
    for q in ped:
        q.pop('_sg', None)
    anchor = None
    if ok and cyc:
        # 닻 = 기준 이동류(녹색이 가장 긴 것)의 마지막 녹색이 켜진 실제 시각(epoch 초) — 지도가 이 시각에서 주기로 이어 센다
        # 주기는 기준 녹색 시작들 사이를 주기 수로 나눠 다시 잰다(중앙값보다 정밀) — 정수 초에 가까우면 정수로
        ncy = round((rs[-1] - rs[0]) / cyc) if len(rs) > 1 else 0
        cx = (rs[-1] - rs[0]) / ncy if ncy >= 2 else cyc
        ci = plan_ci(cyc, int(round(cx)) if abs(cx - round(cx)) <= 0.25 else round(cx, 1))
        # (2026-10-11) 창 앞쪽에 계획이 바뀌는 사이의 늘어난 주기가 섞이면 처음~끝을 주기 수로 나눈 값이 틀어져 닻을 버렸다(이수교차로 일 08:00~08:33 = 가운데값 160초 · 나눈 값 167.3초).
        #  닻은 **끝**에서 이어 세는 것이니 끝의 세 주기가 가운데값 주기와 같으면(±1.5초) 그 주기로 닻을 잡는다
        #  (2026-10-11 낮) 셋 → **둘**로 — 정각에 계획이 바뀌며 첫 주기만 길었던 20분 창(내방역 일 13:00~13:20 = 간격 194·170·170 · 가운데값 170)이 간격이 셋뿐이라 여전히 닻을 잃었다. 13시 뒤 813장 가운데 39장이 이렇게 빠졌다
        iv = [rs[i + 1] - rs[i] for i in range(len(rs) - 1)]
        if len(iv) >= 2 and all(abs(q - cyc) <= 1.5 for q in iv[-2:]) and abs(cyc - round(cyc)) <= 0.3:
            ci = plan_ci(cyc, int(round(cyc)))
        anchor = {'a': (round(rs[-1], 1) if abs(ci - cyc) <= 2 else None), 'ci': ci, 'end': round(t1, 1), 'ncy': ncy}
    for x in mv:
        x.pop('gs', None); x.pop('_sg', None)
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
    if x.get('fl'):
        return [x['d'], x['m'], x.get('g'), x.get('y'), x.get('r'), x.get('o'), x['n'], 4 if x['fl'] == 2 else 3]   # 3 = 같은 요일 갈래·같은 주기의 다른 기록에서 채운 줄(지도는 「채움」이라 적는다)
    return [x['d'], x['m'], x.get('g'), x.get('y'), x.get('r'), x.get('o'), x['n']]


_HOL = None


def holidays():
    """일요일 계획으로 도는 **특수일** 날짜 집합(data/sig-special.json 의 days — 교통과 현시도의 특수일 표 15종 · tools/signal/sigspecial-bake.py) — 없으면 빈 집합.
    쉬는 날 전부가 아니다: 대체공휴일·선거일·제헌절·노동절은 표에 없어 그 요일 계획으로 본다(소유자 「평일·금·토·일·특수일 해서 조금씩 달라」 · 2026-10-11 다른 세션이 현시도에서 읽음)"""
    global _HOL
    if _HOL is None:
        try:
            _HOL = set(json.load(open(os.path.join(ROOT, 'data', 'sig-special.json'), encoding='utf-8')).get('days', {}).keys())
        except Exception:
            _HOL = set()
    return _HOL


def cls_of(dow, day=None):
    """요일 갈래 — 0 월~목 · 1 금 · 2 토 · 3 일·공휴일(교통과 계획의 TOD 갈래와 같게).
    (2026-10-11 소유자 「신호값이 평일과 휴일이 달라 — 통행량이 다르니까」) day('YYYY-MM-DD')가 특수일 15종이면 요일과 상관없이 3 —
    종전엔 요일만 봐서 평일 공휴일에 받은 기록이 평일 표를 휴일 값으로 덮었고, 지도(sdCls = 공휴일 → 3)는 그날 그 값을 찾지 못했다"""
    if day and day in holidays():
        return 3
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
        G.setdefault((i, cls_of(dt.isoweekday() % 7, dt.strftime('%Y-%m-%d')), dt.hour, b.endswith('p')), []).append((dt, f))
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
            # (2026-10-11) 한 번만 본 이동류의 적색이 주기보다 길게 잡힌 것 — 받은 줄 끝에 걸린 적색은 「시작 때 잔여」를 길이로 쓰는데(segments tail) 그 잔여가 틀린 곳이 있다
            #  (이수역 동쪽 직진 46 + 4 + 170.7 = 220.7 · 주기 200). 녹+황+적이 주기를 넘으면 한 주기에 두 번 켜지는 것일 수 없으니 적색 = 주기 − 녹 − 황 으로 바로잡는다
            for x in r['mv']:
                if x.get('g') is not None and x.get('n') == 1 and x['g'] + x['y'] + x['r'] - r['cyc'] > 3.5 and r['cyc'] - x['g'] - x['y'] > 6.5:
                    x['r'] = round(r['cyc'] - x['g'] - x['y'], 1)
            if r.get('ci'):
                r['ci'] = plan_ci(r['cyc'], r['ci'])
                if abs(r['ci'] - r['cyc']) > 2.5:
                    r['a'] = None   # 다시 잰 주기가 계획 주기와 2.5초 넘게 다르면(계획이 바뀌는 중 등) 이어 세지 않는다 — 길이만 보인다
                elif abs(r['ci'] - round(r['ci'])) > 0.05:
                    r['a'] = None   # 주기가 정수 초로 안 떨어지면(149.5 · 169.6 …) 바뀌는 사이의 값이거나 덜 읽힌 것 — 닻으로 쓰지 않는다(2026-10-11)
        keep, plan, pinfo = {}, {}, {}
        for r in v:
            ci0 = r.get('ci') or int(round(r['cyc']))
            kk = (cls_of(r['dow'], r['day']), cyc_key(r))
            k9 = keep.get(kk)
            if k9 and k9.get('a') and k9.get('pd') and not r.get('a') and sum(1 for x in k9['mv'] if x.get('g') is not None) >= sum(1 for x in r['mv'] if x.get('g') is not None):
                pass                                            # (2026-10-11) 닻도 보행 색도 있는 기록을, 닻 없는 나중 기록이 덮지 않는다 — 열쇠를 받은 주기로 바로잡자 같은 주기의 기록이 한 열쇠로 모여 닻 16개가 사라졌다
            elif r.get('pd') or not (keep.get(kk) and keep[kk].get('pd')) or r.get('a'):
                if keep.get(kk) and keep[kk].get('pd') and not r.get('pd'):
                    # 보행 신호 색은 신호 상태 API 로 읽은 것을 이어 쓴다(같은 요일 갈래·같은 주기) —
                    # (2026-10-11) 보행 신호의 자리(o)는 **그 기록의 기준 이동류**에서 잰 것이라, 두 기록의 기준이 다르면(이수역: 상태 = 서쪽 직진 · 잔여 = 남쪽 직진) 그대로 옮기면 어긋난다.
                    #  함께 읽힌 이동류로 밀림을 구해 옮기고, 못 맞추면 옮기지 않는다. src 는 그 기록의 것을 그대로 둔다(차량 신호 색은 여전히 잔여시간에서 읽은 것)
                    q9, c8 = keep[kk], int(round(kk[1]))
                    hv = {(x['d'], x['m']): x for x in r['mv'] if x.get('g') is not None and x.get('o') is not None}
                    qv = {(x['d'], x['m']): x for x in q9['mv'] if x.get('g') is not None and x.get('o') is not None}
                    cm = [k2 for k2 in qv if k2 in hv and abs(hv[k2]['g'] - qv[k2]['g']) <= 2]
                    if cm and c8 >= 20:
                        b8 = max(cm, key=lambda k2: qv[k2]['g']); sh8 = (hv[b8]['o'] - qv[b8]['o']) % c8
                        if all(min(((qv[k2]['o'] + sh8) - hv[k2]['o']) % c8, (hv[k2]['o'] - (qv[k2]['o'] + sh8)) % c8) <= 3 for k2 in cm):
                            r = dict(r, pd=[dict(z, o=(int(round((z['o'] + sh8) % c8)) if z.get('o') is not None else None)) for z in q9['pd']])
                keep[kk] = r                                    # (요일 갈래, 주기)마다 나중 것 한 장
            if r.get('a'):
                hh = datetime.datetime.fromtimestamp(r['a']).hour
                sod = (r['a'] + 9 * 3600) % 86400               # 한국 시각 하루 초
                okm = [x for x in r['mv'] if x.get('g') is not None]
                rf = max(okm, key=lambda x: (x['g'], -DIRS.index(x['d']))) if okm else None      # 닻(a)의 기준 이동류 = 녹색이 가장 긴 이동류(reduce_one·reduce_phase 와 같은 규칙)
                pinfo[(cls_of(r['dow'], r['day']), hh)] = (r['day'], int(r['from'][:2]) * 60 + int(r['from'][3:5]), int(r['to'][:2]) * 60 + int(r['to'][3:5]))
                plan[(cls_of(r['dow'], r['day']), hh)] = [cls_of(r['dow'], r['day']), hh, ci0, int(round(sod % ci0)) % int(round(ci0)) if ci0 == int(ci0) else round(sod % ci0, 1), r['day'][5:], (rf['d'] + ':' + rf['m']) if rf else '']
        # (2026-10-11 소유자 「이수역사거리 비는 초는 북남 양직진이네」) 못 읽은 이동류를 **같은 요일 갈래·같은 주기의 다른 기록**에서 채운다 —
        #  이수역 일 15시: 신호 상태 기록(나중 것 · 보행 신호가 있어 남는다)은 북·남 직진을 못 읽고, 23초 앞서 받은 잔여시간 기록은 남쪽 직진 74초(0초)·동 46·서 55초(88초)를 읽었다.
        #  두 기록에 함께 읽힌 이동류(녹색 길이 ±2초)로 자리를 맞춘다: 밀림 = 남는 기록의 자리 − 주는 기록의 자리(녹색이 가장 긴 공통 이동류) · 다른 공통 이동류가 모두 ±3초 안으로 맞아야 쓴다.
        #  채운 줄은 끝에 3 을 단다(받은 기록 그대로가 아니라 겹쳐 맞춘 값) — 닻·기준 이동류·pl 줄은 건드리지 않는다
        for kk, r in list(keep.items()):
            c9 = int(round(kk[1]))
            if c9 < 20:
                continue
            have = {(x['d'], x['m']): x for x in r['mv']}
            isread = lambda x: x is not None and x.get('g') is not None and x.get('o') is not None and abs(x['g'] + x['y'] + x['r'] - r['cyc']) <= 3.5
            if not any(isread(x) for x in have.values()):
                continue
            add = {}
            # (2026-10-11 소유자 「빈자리를 없애야지 · 이수역처럼 신호값이 불완전하면 곤란해」) 같은 요일 갈래를 먼저 보고, 없으면 **다른 요일 갈래의 같은 주기** 기록도 본다 —
            #  그때는 함께 읽힌 이동류가 둘 이상이고 모두 녹색 ±2초·자리 ±3초로 맞아야 한다(같은 주기라도 요일마다 현시값이 다를 수 있다)
            for q in sorted(sorted(v, key=lambda z: (z['day'], z['to']), reverse=True), key=lambda z: 0 if cls_of(z['dow'], z['day']) == kk[0] else 1):
                if (q['day'], q['from'], q['to'], q.get('src')) == (r['day'], r['from'], r['to'], r.get('src')):
                    continue
                if cyc_key(q) != kk[1]:
                    continue
                xcl = cls_of(q['dow'], q['day']) != kk[0]
                qm = {(x['d'], x['m']): x for x in q['mv'] if x.get('g') is not None and x.get('o') is not None and abs(x['g'] + x['y'] + x['r'] - q['cyc']) <= 3.5}
                com = [k2 for k2 in qm if isread(have.get(k2)) and abs(have[k2]['g'] - qm[k2]['g']) <= 2]
                if not com or (xcl and len(com) < 2):
                    continue
                if xcl and any(isread(have.get(k2)) and abs(have[k2]['g'] - qm[k2]['g']) > 2 for k2 in qm):
                    continue                                   # 다른 요일 갈래 — 함께 읽힌 것 가운데 녹색이 다른 이동류가 하나라도 있으면 다른 계획으로 본다
                b9 = max(com, key=lambda k2: qm[k2]['g'])
                sh = (have[b9]['o'] - qm[b9]['o']) % c9
                cd = lambda a, b: min((a - b) % c9, (b - a) % c9)
                if any(cd((qm[k2]['o'] + sh) % c9, have[k2]['o']) > 3 for k2 in com):
                    continue
                for k2, x in qm.items():
                    if k2[1] in ('St', 'Lt') and not isread(have.get(k2)) and k2 not in add and not (have.get(k2) and have[k2].get('g') is not None):
                        add[k2] = {'d': x['d'], 'm': x['m'], 'g': x['g'], 'y': x['y'], 'r': x['r'], 'o': int(round((x['o'] + sh) % c9)), 'n': x['n'], 'fl': 1}
            if add:
                nm = [x for x in r['mv'] if (x['d'], x['m']) not in add] + list(add.values())
                nm.sort(key=lambda x: (DIRS.index(x['d']), MVS.index(x['m']) if x['m'] in MVS else 9))
                keep[kk] = dict(r, mv=nm)
        # (같은 날) 적색만 읽힌 직진 — 받은 구간이 전부 **마주 보는 직진의 적색 길이**(±2초)와 같으면 그 직진과 같이 켜지는 것으로 보고 같은 초·같은 자리로 채운다(끝에 3).
        #  이수역 북쪽 직진: 구간 [121] 뿐(녹색·황색 구간이 걸러진다) · 남쪽 직진 74 + 5 + 121 = 주기 200 → 소유자 현장 확인 「비는 초는 북남 양직진」과 같다.
        #  구간은 같은 요일 갈래·같은 주기의 기록들에서 모은다(신호 상태 기록에는 구간이 없다). 적색 길이가 같은 것이 근거라 좌회전에는 쓰지 않는다
        OPP9 = {'nt': 'st', 'st': 'nt', 'et': 'wt', 'wt': 'et', 'ne': 'sw', 'sw': 'ne', 'se': 'nw', 'nw': 'se'}
        for kk, r in list(keep.items()):
            cur = {(x['d'], x['m']): x for x in r['mv']}
            same = [q for q in v if (cls_of(q['dow'], q['day']), cyc_key(q)) == kk]
            add = {}
            for d in DIRS:
                x, o = cur.get((d, 'St')), cur.get((OPP9[d], 'St'))
                if (x is not None and x.get('g') is not None) or o is None or o.get('g') is None or o.get('o') is None or abs(o['g'] + o['y'] + o['r'] - r['cyc']) > 3.5:
                    continue
                segs = [t for q in same for z in q['mv'] if z['d'] == d and z['m'] == 'St' and z.get('g') is None for t in (z.get('seg') or [])]
                if segs and all(abs(t - o['r']) <= 2 for t in segs):
                    add[(d, 'St')] = {'d': d, 'm': 'St', 'g': o['g'], 'y': o['y'], 'r': o['r'], 'o': o['o'], 'n': (x or {}).get('n', 0), 'fl': 1}
            if add:
                nm = [x for x in r['mv'] if (x['d'], x['m']) not in add] + list(add.values())
                nm.sort(key=lambda x: (DIRS.index(x['d']), MVS.index(x['m']) if x['m'] in MVS else 9))
                keep[kk] = dict(r, mv=nm)
        # 보행 신호 색이 없는 기록(잔여시간 기록) — **같은 주기**의 다른 기록(요일 갈래가 달라도)에 신호 상태로 읽은 보행 신호가 있으면 자리를 맞춰 옮긴다.
        #  함께 읽힌 차량 이동류가 모두 녹색 ±2초·자리 ±3초로 맞아야 한다(같은 요일 갈래는 하나 이상 · 다른 갈래는 둘 이상). 옮긴 줄은 끝에 1 을 단다(pd 일곱째 칸)
        for kk, r in list(keep.items()):
            c8 = int(round(kk[1]))
            if r.get('pd') or c8 < 20:
                continue
            hv = {(x['d'], x['m']): x for x in r['mv'] if x.get('g') is not None and x.get('o') is not None and not x.get('fl')}
            for q9 in sorted(sorted(v, key=lambda z: (z['day'], z['to']), reverse=True), key=lambda z: 0 if cls_of(z['dow'], z['day']) == kk[0] else 1):
                if not q9.get('pd') or cyc_key(q9) != kk[1]:
                    continue
                qv = {(x['d'], x['m']): x for x in q9['mv'] if x.get('g') is not None and x.get('o') is not None and not x.get('fl')}
                cm = [k2 for k2 in qv if k2 in hv and abs(hv[k2]['g'] - qv[k2]['g']) <= 2]
                if len(cm) < (1 if cls_of(q9['dow'], q9['day']) == kk[0] else 2) or any(k2 in hv and abs(hv[k2]['g'] - qv[k2]['g']) > 2 for k2 in qv):
                    continue
                b8 = max(cm, key=lambda k2: qv[k2]['g']); sh8 = (hv[b8]['o'] - qv[b8]['o']) % c8
                if all(min(((qv[k2]['o'] + sh8) - hv[k2]['o']) % c8, (hv[k2]['o'] - (qv[k2]['o'] + sh8)) % c8) <= 3 for k2 in cm):
                    keep[kk] = dict(r, pd=[dict(z, o=(int(round((z['o'] + sh8) % c8)) if z.get('o') is not None else None), cx=1) for z in q9['pd']])
                    break
        # 그래도 보행 신호 색이 없는 기록 — 잔여시간에서 읽은 보행 시간(녹색+점멸 합 · reduce_one 의 ped g·o)이 있으면 그것으로(끝에 2)
        for kk, r in list(keep.items()):
            if r.get('pd'):
                continue
            pt = [{'d': z['d'], 'g': z['g'], 'y': 0.0, 'r': round(r['cyc'] - z['g'], 1), 'o': z['o'], 'n': z.get('gn', 1), 'cx': 2} for z in (r.get('ped') or []) if z.get('g') is not None and z.get('o') is not None]
            if pt:
                keep[kk] = dict(r, pd=pt)
        # 아직도 보행 신호가 없는 기록(구간 시각을 안 남긴 옛 잔여시간 기록) — 못 읽은 차량 이동류가 없고, 차량 신호가 없는 12초 넘는 구간에
        #  **길이가 맞는**(구간 − 12초 ~ 구간 + 2초) 보행 구간이 되풀이되면 그 보행 신호를 그 구간 가운데에 놓는다(끝에 3 — 길이는 받은 값 · 자리는 어림).
        #  같은 축 차량 직진이 읽힌 보행 신호는 그 직진과 함께 켜지므로(818쌍 대 7쌍) 빈 구간에 넣지 않는다 — 건널목만 있는 연등과 보행 전용 현시에만 맞는다
        for kk, r in list(keep.items()):
            c8 = int(round(kk[1]))
            if r.get('pd') or c8 < 20 or not r.get('ped'):
                continue
            rdv = [x for x in r['mv'] if x.get('g') is not None and x.get('o') is not None]
            if not rdv or any(x['m'] in ('St', 'Lt') and x.get('g') is None for x in r['mv']):
                continue
            cov = [0] * c8
            for x in rdv:
                for t in range(int(round(x['o'])), int(round(x['o'] + x['g'] + x['y']))):
                    cov[t % c8] = 1
            gaps, st8 = [], None
            for t in range(2 * c8):
                if not cov[t % c8] and st8 is None:
                    st8 = t
                if cov[t % c8] and st8 is not None:
                    if st8 < c8 and t - st8 >= 12:
                        gaps.append((st8 % c8, t - st8))
                    st8 = None
            if not gaps:
                continue
            axs = set(DIRS.index(x['d']) % 4 for x in rdv if x['m'] == 'St')
            pt, used = [], set()
            for z in r['ped']:
                sg8 = [v for v in (z.get('seg') or []) if v > 6]
                if not sg8 or (len(axs) > 1 and DIRS.index(z['d']) % 4 in axs):
                    continue                                   # 차량 축이 하나뿐인 곳(건널목만 있는 연등)은 보행 방위가 그 축과 같게 적혀 있어도 넣는다 — 이수교차로(연등): 차 북동·남서 131초 · 보행 「남서」 33초 = 빈 35초
                for g0, gl in gaps:
                    cand = sorted(((sum(1 for v in sg8 if abs(v - L) <= 2), L) for L in set(sg8) if gl - 12 <= L <= gl + 2), reverse=True)
                    if cand and (cand[0][0] >= 2 or len(sg8) <= 3):
                        L = float(cand[0][1])
                        pt.append({'d': z['d'], 'g': L, 'y': 0.0, 'r': round(r['cyc'] - L, 1), 'o': int(round(g0 + max(0.0, gl - L) / 2.0)) % c8, 'n': cand[0][0], 'cx': 3})
                        break
            if pt:
                keep[kk] = dict(r, pd=pt)
        # ── 추정으로 채우기(끝에 4 · 지도는 「추정」이라 적는다) — 위의 채움으로도 남은 것만 ──
        RD = lambda x, cyc: x is not None and x.get('g') is not None and x.get('o') is not None and abs(x['g'] + x['y'] + x['r'] - cyc) <= 3.5
        for kk, r in list(keep.items()):
            c9 = int(round(kk[1]))
            if c9 < 20:
                continue
            cd = lambda a, b: min((a - b) % c9, (b - a) % c9)
            cur = {(x['d'], x['m']): x for x in r['mv']}
            unk = [k2 for k2, x in cur.items() if k2[1] in ('St', 'Lt') and x.get('g') is None]
            if not unk or not any(RD(x, r['cyc']) for x in cur.values()):
                continue
            others = [q for q in v if (q['day'], q['from'], q['to'], q.get('src')) != (r['day'], r['from'], r['to'], r.get('src'))]
            add = {}
            # C. 늘 같이 켜지는 짝 — 다른 기록(받은 그대로 읽힌 것만)에서 이 이동류와 녹색 ±2초·자리 ±3초로 **늘** 같이 켜진 이동류가 이 기록에 읽혀 있으면 그 값으로
            #  (마주 보는 직진 · 직좌 동시 · 버스 신호 — 한 번이라도 어긋난 기록이 있으면 짝으로 보지 않는다 · 이수역 동·서 직진은 주기 200초에서 46·55초로 달라 짝이 아니다)
            for k2 in unk:
                votes = {}
                for q in others:
                    qc = int(round(q['cyc']))
                    qm = {(x['d'], x['m']): x for x in q['mv'] if RD(x, q['cyc']) and not x.get('fl')}
                    if k2 not in qm or qc < 20:
                        continue
                    for k3, y in qm.items():
                        if k3 == k2 or k3[1] not in ('St', 'Lt'):
                            continue
                        if k2[1] == 'St' and k3[1] == 'St' and (DIRS.index(k2[0]) - DIRS.index(k3[0])) % 8 in (2, 6):
                            continue                           # 직각 방향 직진은 함께 켜질 수 없다(을지로4가 — 방위 이름이 섞인 기록에서 서쪽 직진이 북쪽 직진과 「늘 같이」로 잡혔다)
                        same = abs(y['g'] - qm[k2]['g']) <= 2 and min((y['o'] - qm[k2]['o']) % qc, (qm[k2]['o'] - y['o']) % qc) <= 3
                        w = votes.setdefault(k3, [0, 0]); w[0 if same else 1] += 1
                cand = [k3 for k3, w in votes.items() if w[0] >= 1 and w[1] == 0 and RD(cur.get(k3), r['cyc']) and not cur[k3].get('fl')]
                if cand:
                    k3 = max(cand, key=lambda z: (votes[z][0], z[1] == k2[1]))
                    y = cur[k3]
                    add[k2] = {'d': k2[0], 'm': k2[1], 'g': y['g'], 'y': y['y'], 'r': y['r'], 'o': y['o'], 'n': 0, 'fl': 2}
            # B. 빈 자리에 차례로 맞춰 넣기 — 읽힌 녹색·황색이 하나도 없는 12초 넘는 구간이 있고, 못 읽은 이동류가 다른 기록에서 **같은 앞 신호 바로 뒤 ~ 같은 뒤 신호 바로 앞**(±4초)을 채웠으면
            #  그 구간 전체를 그 이동류로(녹색 = 구간 − 그 기록의 황색). 주기가 달라 초를 옮길 수 없을 때 쓴다(이수역 일 07시 주기 180 — 북·남 좌회전 뒤 87초가 비었고, 160초·200초 기록에서 그 자리는 북·남 직진)
            cov = [0] * c9
            for x in list(cur.values()) + list(add.values()):
                if RD(x, r['cyc']) or x.get('fl') == 2:
                    for t in range(int(round(x['o'])), int(round(x['o'] + x['g'] + x['y']))):
                        cov[t % c9] = 1
            gaps, st9 = [], None
            for t in range(2 * c9):
                if not cov[t % c9] and st9 is None:
                    st9 = t
                if cov[t % c9] and st9 is not None:
                    if st9 < c9 and t - st9 >= 12:
                        gaps.append((st9 % c9, t - st9))
                    st9 = None
            rdm = {k2: x for k2, x in cur.items() if RD(x, r['cyc'])}
            for g0, gl in gaps:
                pred = [k2 for k2, x in rdm.items() if cd((x['o'] + x['g'] + x['y']) % c9, g0) <= 4]
                succ = [k2 for k2, x in rdm.items() if cd(x['o'], (g0 + gl) % c9) <= 4]
                if not pred or not succ:
                    continue
                for k2 in unk:
                    if k2 in add:
                        continue
                    yy = None
                    for q in others:
                        qc = int(round(q['cyc']))
                        qm = {(x['d'], x['m']): x for x in q['mv'] if RD(x, q['cyc']) and not x.get('fl')}
                        x = qm.get(k2)
                        qp, qs = [qm[z] for z in pred if z in qm], [qm[z] for z in succ if z in qm]
                        if x is None or not qp or not qs or qc < 20:
                            continue
                        dq = lambda a, b: min((a - b) % qc, (b - a) % qc)
                        if all(dq((z['o'] + z['g'] + z['y']) % qc, x['o']) <= 4 for z in qp) and all(dq((x['o'] + x['g'] + x['y']) % qc, z['o']) <= 4 for z in qs):
                            yy = x['y']; break
                    if yy is not None and gl - yy > 6.5:
                        add[k2] = {'d': k2[0], 'm': k2[1], 'g': float(gl - yy), 'y': yy, 'r': float(c9 - gl), 'o': g0, 'n': 0, 'fl': 2}
            if add:
                nm = [x for x in r['mv'] if (x['d'], x['m']) not in add] + list(add.values())
                nm.sort(key=lambda x: (DIRS.index(x['d']), MVS.index(x['m']) if x['m'] in MVS else 9))
                keep[kk] = dict(r, mv=nm)
        for kk, r in list(keep.items()):
            c9 = int(round(kk[1]))
            if c9 < 20 or not any(x.get('fl') for x in r['mv']):
                continue
            span = lambda x: set(t % c9 for t in range(int(round(x['o'])) + 2, int(round(x['o'] + x['g'])) - 2))
            real = [x for x in r['mv'] if x['m'] == 'St' and x.get('g') is not None and x.get('o') is not None and not x.get('fl')]
            bad = [x for x in r['mv'] if x.get('fl') and x['m'] == 'St' and any((DIRS.index(x['d']) - DIRS.index(y['d'])) % 8 in (2, 6) and len(span(x) & span(y)) > 5 for y in real)]
            if bad:
                keep[kk] = dict(r, mv=[({'d': x['d'], 'm': x['m'], 'n': 0} if any(x is z for z in bad) else x) for x in r['mv']])   # 채운 직진이 받은 그대로의 직각 직진과 겹친다 — 채움을 물린다(못 읽음으로)
        vv = sorted(keep.values(), key=lambda r: (r['day'], r['to']))[-12:]
        # 약한 줄(일곱째 칸 1) — 정각 뒤 5분 안에 시작해 8분도 안 되는 창에서 받았고, 같은 날 바로 앞 시각대의 주기와 다르다 = 계획이 바뀌는 사이의 헛값일 수 있다(이수역 일 8시 237초 — 앞은 180 · 계획은 190).
        #  그 시각대를 뒤에 다시 받으면(창이 길어지면) 덮어써져 풀린다. 지도·맞대 보기는 약한 줄을 쓰지 않는다
        for (c9, h9), row in plan.items():
            inf, prev, pin = pinfo.get((c9, h9)), plan.get((c9, h9 - 1)), pinfo.get((c9, h9 - 1))
            if inf and prev and pin and pin[0] == inf[0] and abs(prev[2] - row[2]) > 0.6 and inf[1] % 60 <= 5 and 0 <= inf[2] - inf[1] < 8:
                row.append(1)
            elif inf and prev and pin and pin[0] == inf[0] and abs(prev[2] - row[2]) <= 0.6 and inf[1] % 60 <= 5 and 0 <= inf[2] - inf[1] < 8 and row[5] == prev[5] and pin[2] - pin[1] >= 8 \
                    and min((row[3] - prev[3]) % row[2], (prev[3] - row[3]) % row[2]) > 3:
                row.append(1)   # (2026-10-11) 앞 시각대(8분 넘게 받은 것)와 주기·기준 이동류는 같은데 옵셋이 3초 넘게 다른 짧은 창 — 옵셋을 옮기는 사이의 값으로 본다
            elif inf and not (prev and pin and pin[0] == inf[0]) and inf[1] % 60 <= 5 and 0 <= inf[2] - inf[1] < 8:
                # (2026-10-11) 앞 시각대를 못 받았을 때는 **뒤 시각대**와 견준다 — 사당역 일 01시: 정각 직후 5분 창에서 주기 180(00시 계획이 아직 도는 중) · 02시는 160 · 경찰청 계획도 01시 160.
                #  정각 직후의 짧은 창은 앞 시각대의 계획을 보고 있을 수 있다 → 뒤 시각대와 주기가 다르면 약한 줄(지도는 안 쓴다 · 다시 길게 받으면 풀린다)
                nxt, nin = plan.get((c9, h9 + 1)), pinfo.get((c9, h9 + 1))
                if nxt and nin and nin[0] == inf[0] and abs(nxt[2] - row[2]) > 0.6:
                    row.append(1)
        if plan:
            pl[k] = [plan[q] for q in sorted(plan)]
        L = []
        for r in vv:
            o = {'day': r['day'], 'dow': r['dow'], 'cl': cls_of(r['dow'], r['day']), 'from': r['from'], 'to': r['to'], 'cyc': r['cyc'],
                 'mv': [mvrow(x, r['cyc']) for x in r['mv']],
                 'ped': [[p['d'], p['seg'][:8]] for p in r['ped']]}
            if dir_bad(o['mv'], r['cyc']):
                o['dq'] = 'dir'   # 방위 이름이 실제와 다르다(직각 방향이 함께 녹색) — 지도는 경고를 붙인다
            if r.get('src') == 'p':
                o['src'] = 'p'   # 신호 상태 API 로 읽은 기록(색이 추정이 아니라 상태 값 그대로)
            if r.get('pd'):
                o['pd'] = [[q['d'], q.get('g'), q.get('y'), q.get('r'), q.get('o'), q['n']] + ([q['cx']] if q.get('cx') else []) for q in r['pd'] if q.get('g') is not None and abs(q['g'] + q['y'] + q['r'] - r['cyc']) <= 3.5]   # 보행 신호 [방위, 녹색, 점멸, 적색, 녹색 시작, 본 횟수] — 주기와 맞는 것만
            if r.get('a'):
                o['a'] = int(round(r['a'])); o['ci'] = r['ci']
                # 검증 — 같은 주기로 받은 다른 닻(40분 넘게 떨어진 것)과 **자정 기준 옵셋**(하루 초 mod 주기)이 맞는가(±3초).
                # (2026-10-11 고침: 종전엔 두 닻 사이 간격이 주기의 정수배인지를 봤다 — 같은 날에는 같은 셈이지만, 날이 다르면 주기가 하루(86,400초)를 나누지 않는 계획(170·140·130초…)에서
                #  자정마다 다시 맞춰지므로 틀린다. 실측: 다른 날·하루를 안 나누는 주기 154쌍 가운데 간격으로는 3쌍, 옵셋으로는 67쌍이 맞았다)
                # 안 맞음(x)은 **같은 요일 갈래·같은 시(時)** 끼리 견줬을 때만 적는다 — 시각대가 다르면 주기가 같아도 옵셋이 다른 계획일 수 있어(교통과 현시도의 패턴 1·2) 어긋남이 틀림의 증거가 아니다
                best, bad = None, None
                offr = ((r['a'] + 32400) % 86400) % r['ci']; hr_r = datetime.datetime.fromtimestamp(r['a']).hour
                for q in v:
                    if not q.get('a') or abs(q.get('ci', 0) - r['ci']) > 0.3 or abs(q['a'] - r['a']) < VGAP:
                        continue
                    gap = abs(q['a'] - r['a']); offq = ((q['a'] + 32400) % 86400) % r['ci']; res = abs(offq - offr); res = min(res, r['ci'] - res)
                    if res <= 3:
                        if not best or gap > best[0]: best = (gap, res)
                    elif cls_of(q['dow'], q['day']) == cls_of(r['dow'], r['day']) and datetime.datetime.fromtimestamp(q['a']).hour == hr_r and (not bad or gap < bad[0]): bad = (gap, res)
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
           'fields': 'pts{교차로 번호: [위도, 경도, 이름]} · its{교차로 번호: [기록…]} 기록 = {day 받은 날, dow 요일(0 일), from~to 받은 시각, cyc 주기 초, mv[[방위, 이동류, 녹색, 황색, 적색, 녹색 시작(주기 안), 본 횟수(, 2 = 한 주기에 두 번)]], pd[[방위, 보행 녹색, 점멸, 적색, 녹색 시작, 본 횟수]](신호 상태 API 로 받은 기록만), ped[[방위, …]](보행 신호가 있는 쪽), a 기준 이동류 녹색이 켜진 실제 시각(epoch 초), ci 주기(이어 세기용), v[띄운 분, 어긋난 초](두 번 대조 통과), x[…](대조 실패), src p = 신호 상태 API, dq dir = 원자료의 방위 이름이 실제와 다름(직각 방향 직진이 함께 녹색 — 초는 쓸 수 있어도 어느 쪽인지는 현장 확인)} · tod{교차로 번호: [[요일 갈래 0 평일·1 토·2 일, 시, 주기 초]]} · pl{교차로 번호: [[요일 갈래(0 월~목 · 1 금 · 2 토 · 3 일), 시, 주기, 자정 기준 옵셋(기준 이동류 녹색이 켜지는 하루 초 mod 주기), 받은 달-날, 그 옵셋의 기준 이동류 「방위:이동류」(기록마다 기준이 다를 수 있다 — 쓸 때 그 기록의 그 이동류 녹색 시작만큼 옮겨 맞춘다), 1 = 약한 줄(정각 직후 짧은 창에서 받았고 앞 시각대와 주기가 다름 — 바뀌는 사이의 값일 수 있어 쓰지 않는다)(있을 때만)]]}(시계로 이어 세는 표 — 기록의 cl·ci 가 같은 것이 그 계획의 방향별 초)',
           'note': '받은 시간대에 실제로 돈 값이다(하루 계획표가 아니다) · 방위 = 그 신호를 받는 차가 들어오는 쪽 · 잔여시간 API 로 읽은 기록의 색은 황색 3~6초 앞뒤로 읽은 추정이고 src p 기록은 상태 값 그대로 · 이어 센 「지금 몇 초」는 a·ci 로 지도가 계산한 추정',
           'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'pts': pts, 'its': its, 'tod': tod, 'pl': pl}
    p = os.path.join(ROOT, 'data', 'sigdir-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    try:
        split_write(doc)
    except Exception as e:
        print('나눠 쓰기 실패', str(e)[:120], flush=True)
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
