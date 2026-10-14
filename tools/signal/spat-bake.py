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
import sys, os, json, time, gzip, glob, datetime, statistics, math, urllib.request, urllib.error

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


# ── 열쇠·API 짝 풀(2026-10-14 소유자 지시 「키-API 짝 풀 구조로」) ─────────────────────────────
#   T-Data 게이트웨이(apiman)는 열쇠를 API 단위로 묶는다 — 404 = 「이 열쇠에 이 API 계약 없음」.
#   2026-10-14 12:36 실측: KEY1 = 역사 API 둘(잔여 TimingInformation · 상태 PhaseInformation) 200 · CurrentInfo 404
#                          KEY2 = 역사 API 둘 404 · CurrentInfo · FusionCurrentInfo 200 → 지금은 두 열쇠가 함께 쓰는 API 가 없다
#   그래서 엔드포인트마다 열쇠 차례를 두고, 짝(열쇠, 엔드포인트)마다 살았나·죽었나·쉬나를 따로 센다.
#   · 404 → 그 짝만 죽음 · 30분마다 3줄짜리로 한 번 다시 본다 · 살아나면 저절로 끼운다(승인이 나면 처리량이 저절로 늘어난다)
#   · 401/403/429 → 그 열쇠를 쉰다(사유를 찍는다) · 429 는 서버가 말한 retryAfterSeconds 만큼
#   · 고르기 = 살아 있는 열쇠 가운데 그 API 에서 가장 오래 쉰 것 · 열쇠마다 5분 제한(GAP) · 호출 사이 = GAP ÷ 살아 있는 열쇠 수
#   · 둘 이상 번갈아 쓰는 동안 429 가 세 번 나면 「5분 제한을 같이 쓴다」로 보고 둘째 이후 열쇠를 여섯 시간 쉰다(아직 확인 안 된 것 · 종전 규칙 그대로)
#   열쇠 값은 keys.json 에서만 읽고 기록에는 KEY1/KEY2 라벨만 남긴다. 상태 = ../07_API키/out/tdata/pool_<엔드포인트>.json · 처리량 = throughput.log(매시)
BASEFH = 'https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/v2xSignalPhaseTimingFusionInformation/1.0'   # (2026-10-14 15:40 두 열쇠 승인) 잔여 초 + 상태 이름 **역사** — 잔여시간 역사와 같은 줄 꼴에 상태 칸이 더 붙음 · 5분 제한이 따로라 셋째 훑기로(api 'f')
BASEF = 'https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/v2xSignalPhaseTimingFusionCurrentInfo/1.0'   # 지금 한 줄(잔여 초 + 방향별 상태 이름) · itstId 또는 sggCd 필수
POOL_ORDER = {'timing': ['KEY1', 'KEY2'], 'phase': ['KEY1', 'KEY2'], 'fhist': ['KEY2', 'KEY1'], 'fusion': ['KEY2', 'KEY1']}
POOL_URL = {'timing': BASE, 'phase': BASEP, 'fhist': BASEFH, 'fusion': BASEF}
POOL_PROBE_Q = {'timing': '&pageNo=1&numOfRows=3', 'phase': '&pageNo=1&numOfRows=3', 'fhist': '&pageNo=1&numOfRows=3', 'fusion': '&pageNo=1&numOfRows=3&itstId=4036'}
RECHECK = 1800
DAYCAP_EP = {}   # 엔드포인트별 상한은 이제 안 쓴다(열쇠마다 합 KEYCAP) — 종전 'fusion': 400   # (2026-10-14 15:40) 두 열쇠가 신호 API 여섯 가지 모두 승인됨 → 역사 API 둘을 두 열쇠가 번갈아 쓴다(열쇠마다 하루 약 290 × 2 = 580).
                              #  T-Data 한도 「1일 1,000회」가 열쇠마다인지 API 마다인지 몰라, 열쇠마다 합이 1,000 을 넘지 않게 Fusion 은 열쇠마다 400(두 열쇠 800) — 종전 KEY2 홀로 970
KEYCAP = 999   # (2026-10-14 소유자 「하루에 키별 999회까지 하자」 · 앞서 960) 열쇠마다 하루(한국 날짜) 모든 API 합 — 세 수집(잔여·상태·Fusion)이 keyday.json 하나로 같이 센다
DAYCAP = 900   # (2026-10-14) 공식 안내 하루 1,000회 — 열쇠마다인지 API 마다인지 몰라 짝(열쇠, API)마다 세고 900 에서 멈춘다


def kd_path():
    return os.path.join(RAW, 'keyday.json')


def kd_today():
    return datetime.datetime.fromtimestamp(time.time() + 9 * 3600, datetime.timezone.utc).strftime('%Y-%m-%d')


def kd_get(label):
    try:
        d = json.load(open(kd_path(), encoding='utf-8'))
        return d.get(label, 0) if d.get('day') == kd_today() else 0
    except Exception:
        return 0


def kd_add(label):
    """열쇠의 오늘 호출 수 +1 — 세 수집이 같은 파일을 쓴다(읽고 고쳐 쓰기 사이가 짧아 겹침은 드물다 · 겹쳐도 하나 덜 셀 뿐)"""
    for _ in range(3):
        try:
            try:
                d = json.load(open(kd_path(), encoding='utf-8'))
            except Exception:
                d = {}
            if d.get('day') != kd_today():
                d = {'day': kd_today()}
            d[label] = d.get(label, 0) + 1
            t = kd_path() + '.%d.tmp' % os.getpid()
            json.dump(d, open(t, 'w', encoding='utf-8')); os.replace(t, kd_path())
            return d[label]
        except Exception:
            time.sleep(0.2)
    return None


def hist_reserve():
    """오늘 남은 시간 동안 역사 훑기(잔여·상태 둘)가 열쇠 하나로 더 부를 어림 — 열쇠마다 API 하나에 5분(GAP)에 한 번 꼴"""
    left = 86400 - (time.time() + 9 * 3600) % 86400
    return int(3 * left / GAP) + 5                         # 역사 훑기 셋(잔여·상태·잔여+상태)


def keyval(label):
    return key() if label == 'KEY1' else key2()


class KeyPool:
    def __init__(self, ep, gap=GAP):
        self.ep, self.gap0 = ep, gap
        self.order = [k for k in POOL_ORDER[ep] if keyval(k)]
        self.f = os.path.join(RAW, 'pool_%s.json' % ep)
        self.st = {k: {'state': 'alive' if i == 0 else 'unknown', 'next': 0.0, 'rest': 0.0, 'why': '', 'last': 0.0, 'dd': '', 'dn': 0} for i, k in enumerate(self.order)}   # 첫 열쇠는 살았다고 보고 시작한다(살펴보는 호출도 5분 제한을 먹는다)
        try:
            old = json.load(open(self.f, encoding='utf-8'))
            for k, v in old.get('st', {}).items():
                if k in self.st:
                    self.st[k].update({x: v[x] for x in ('state', 'next', 'rest', 'why', 'last', 'dd', 'dn') if x in v})
        except Exception:
            pass
        self.n429 = 0; self.hr = datetime.datetime.now().strftime('%Y%m%d_%H'); self.cnt = {}

    def save(self):
        try:
            json.dump({'ep': self.ep, 'at': time.time(), 'st': self.st}, open(self.f, 'w', encoding='utf-8'), ensure_ascii=False)
        except Exception:
            pass

    def say(self, *a):
        print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), '[풀 %s]' % self.ep, *a, flush=True)

    def today(self):
        return datetime.datetime.fromtimestamp(time.time() + 9 * 3600, datetime.timezone.utc).strftime('%Y-%m-%d')   # 한국 날짜

    def capped(self, k):
        S = self.st[k]
        if S.get('dd') == self.today() and S.get('dn', 0) >= DAYCAP_EP.get(self.ep, DAYCAP):
            return True
        used = kd_get(k)
        if self.ep == 'fusion':
            return used + hist_reserve() >= KEYCAP          # Fusion 은 역사 훑기가 오늘 더 쓸 몫을 남기고 그 나머지만
        return used >= KEYCAP

    def alive(self):
        nw = time.time()
        return [k for k in self.order if self.st[k]['state'] == 'alive' and self.st[k]['rest'] <= nw and not self.capped(k)]

    def gap(self):
        return max(30, self.gap0 // max(1, len(self.alive())))

    def probe(self, k):
        u = POOL_URL[self.ep] + '?apikey=' + keyval(k) + POOL_PROBE_Q[self.ep]
        kd_add(k)                                             # 살펴보는 호출도 하루 한도에 든다
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60); c = r.status; r.read()
        except urllib.error.HTTPError as e:
            c = e.code
        except Exception:
            c = 0
        S = self.st[k]
        if c in (200, 429):
            S.update(state='alive', why=''); S['last'] = time.time()
            self.say('%s 살아 있다(HTTP %d) — 끼운다 · 살아 있는 열쇠 %d개' % (k, c, len(self.alive())))
        elif c == 404:
            S.update(state='dead', next=time.time() + RECHECK, why='404 이 API 계약 없음')
            self.say('%s 아직 안 됨(HTTP 404 · 이 API 계약 없음) — %d분 뒤 다시 본다' % (k, RECHECK // 60))
        else:
            S.update(next=time.time() + RECHECK, why='HTTP %d' % c)
            if S['state'] == 'unknown':
                S['state'] = 'dead'
            self.say('%s 살펴보기 HTTP %d — %d분 뒤 다시 본다' % (k, c, RECHECK // 60))
        self.save()
        return c

    def refresh(self):
        nw = time.time()
        for k in self.order:
            S = self.st[k]
            if S['state'] in ('dead', 'unknown') and S['next'] <= nw:
                self.probe(k)

    def pick(self):
        """(열쇠 라벨, 기다릴 초) — 살아 있는 열쇠가 없으면 첫 열쇠로 그대로 간다(수집이 끊기지 않게)"""
        al = self.alive()
        if not al:
            k = self.order[0]
            if self.capped(k) and all(self.capped(x) for x in self.order if self.st[x]['state'] == 'alive'):
                nw = time.time(); mid = nw - (nw + 9 * 3600) % 86400 + 86400 + 5   # 다음 날 0시(한국) 5초 뒤
                return k, mid - nw
            return k, max(0.0, max(self.st[k]['last'] + self.gap0, self.st[k]['rest']) - time.time())
        k = min(al, key=lambda x: self.st[x]['last'])
        return k, max(0.0, self.st[k]['last'] + self.gap0 - time.time())

    def mark(self, k):
        S = self.st[k]; S['last'] = time.time(); d = self.today()
        if S.get('dd') != d:
            S['dd'], S['dn'] = d, 0
        S['dn'] = S.get('dn', 0) + 1
        tot = kd_add(k)
        if S['dn'] == DAYCAP_EP.get(self.ep, DAYCAP):
            self.say('%s 오늘 %d번 — 이 짝은 다음 날 0시까지 멈춘다' % (k, S['dn']))
        if tot == KEYCAP:
            self.say('%s 오늘 모든 API 합 %d번 — 이 열쇠는 다음 날 0시까지 멈춘다' % (k, tot))
        self.save()

    def tally(self, k, c):
        h = datetime.datetime.now().strftime('%Y%m%d_%H')
        if h != self.hr:
            self.flush()
            self.hr, self.cnt = h, {}
        b = self.cnt.setdefault(k, {'ok': 0, '404': 0, '429': 0, 'etc': 0})
        b['ok' if c == 200 else ('404' if c == 404 else ('429' if c == 429 else 'etc'))] += 1

    def flush(self):
        if not self.cnt:
            return
        try:
            line = '%s %s ' % (self.hr, self.ep) + ' · '.join('%s 성공 %d(분당 %.3f) 404 %d 429 %d 그밖 %d · 오늘 누적 %d' % (k, v['ok'], v['ok'] / 60.0, v['404'], v['429'], v['etc'], self.st.get(k, {}).get('dn', 0)) for k, v in sorted(self.cnt.items()))
            open(os.path.join(RAW, 'throughput.log'), 'a', encoding='utf-8').write(line + '\n')
        except Exception:
            pass

    def note(self, k, c, body=''):
        """응답을 받은 뒤 — 짝·열쇠 상태를 고친다. 돌려주는 값 = 서버가 말한 기다림(429) 또는 None"""
        self.tally(k, c)
        S = self.st[k]; multi = len(self.alive()) > 1
        if c == 200:
            S.update(state='alive', why='')
        elif c == 404:
            S.update(state='dead', next=time.time() + RECHECK, why='404 이 API 계약 없음')
            self.say('%s 이 API 에 계약이 없다(HTTP 404) — 이 짝만 쉰다 · %d분 뒤 다시 본다 · 남은 열쇠 %s' % (k, RECHECK // 60, ','.join(self.alive()) or '없음(첫 열쇠로 계속)'))
        elif c in (401, 403):
            S.update(rest=time.time() + RECHECK, why='HTTP %d 인증 거절' % c)
            self.say('%s 인증 거절(HTTP %d) — 이 열쇠를 %d분 쉰다' % (k, c, RECHECK // 60))
        elif c == 429 or (self.ep == 'fusion' and '"22"' in (body or '')[:200]):
            if self.ep == 'fusion' and ('LIMIT' in (body or '').upper() or '"22"' in (body or '')[:200]):
                S['dd'], S['dn'] = self.today(), DAYCAP_EP.get(self.ep, DAYCAP)   # 일일 한도 넘김 — 그날은 멈춘다(다음 날 0시에 다시)
                self.say('%s 일일 한도 넘김 응답 — 그날은 멈춘다' % k); self.save(); return 60
            try:
                w = int(json.loads(body).get('retryAfterSeconds', self.gap0)) + 5
            except Exception:
                w = self.gap0
            S.update(rest=time.time() + w, why='429 5분 제한')
            if multi:
                self.n429 += 1
                if self.n429 >= 3:
                    for x in self.order[1:]:
                        self.st[x].update(rest=time.time() + 6 * 3600, why='번갈아 쓰는 동안 429 세 번 — 5분 제한을 같이 쓰는 것으로 봄')
                    self.n429 = 0
                    self.say('번갈아 쓰는 동안 429 가 세 번 — 열쇠들이 5분 제한을 같이 쓰는 것으로 본다 · 둘째 이후 열쇠를 여섯 시간 쉰다')
            self.save()
            return w
        self.save()
        return None


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
        if not run('git', 'status', '--porcelain', '--', 'data/sigdir-seoul.json', 'data/live-spd-seocho.json', 'data/live-spd-six.json').stdout.strip():
            return
        run(sys.executable, '-X', 'utf8', os.path.join('tools', 'signal', 'sig-audit.py'))   # 맞대 본 결과(data/sig-audit.json)도 같이 다시 만든다
        run('git', 'add', '--', 'data/sigdir-seoul.json', 'data/sigdir', 'data/sig-audit.json', 'data/live-spd-seocho.json', 'data/live-spd-six.json')            # 열쇠 검사는 올릴 준비가 된 변경만 본다 — 먼저 올릴 준비를 한다
        if run(sys.executable, '-X', 'utf8', os.path.join('tools', 'keycheck.py')).returncode != 0:
            print('열쇠 검사에 걸려 올리지 않았다', flush=True); return
        run('git', 'pull', '-q', '--ff-only', 'origin', 'main')
        c = run('git', 'commit', '-q', '-m', 'sigdir: 방향별 신호 자동 갱신\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', '--', 'data/sigdir-seoul.json', 'data/sigdir', 'data/sig-audit.json', 'data/live-spd-seocho.json', 'data/live-spd-six.json')
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


# (2026-10-14 소유자) 수집 단계 — ① 여섯 구 ② 한강 이남 나머지 여섯 구 ③ 서울 전체. 앞 단계가 다 차면 다음 단계를 바구니에 더한다(「한강 이남이 완성되면 서울 전체로」)
STAGE_GU = [['서초구'], ['강남구', '동작구', '관악구', '용산구', '송파구'], ['영등포구', '구로구', '금천구', '강서구', '양천구', '강동구']]   # (2026-10-14 소유자 「우선 서초구부터 완성」) 서초 → 나머지 다섯 구 → 한강 이남 → 서울
TIER_NAMES = []   # read_list 가 채운다 — 묶음(## 줄)의 구 이름


def stage_done(keys, its, pl):
    """그 단계가 다 찼나 — 목록에 있는 교차로 가운데 기록 있음 ≥ 95% 이고, 기록 있는 곳의 평일(갈래 0) 07~22시 칸(15칸)이 80% 넘게 찼을 때
    (2026-10-14 게임 세션 제안 「기록 ≥ 95% · 평일 낮 시각대 칸이 대부분」 → 「대부분」= 80% 로 잡음)"""
    if not keys:
        return True
    rec = [k for k in keys if its.get(k)]
    if len(rec) < 0.95 * len(keys):
        return False
    cells = sum(len(set(x[1] for x in pl.get(k, []) if x[0] == 0 and 7 <= x[1] < 22 and not (len(x) > 6 and x[6]))) for k in rec)
    return cells >= 0.8 * 15 * len(rec)


def open_stages(members, its, pl):
    """members = 단계마다 교차로 번호 목록 → 지금 열 단계 수(앞에서부터 다 찬 단계 + 1 · 모두 찼으면 len+1 = 서울 전체)"""
    n = 0
    for ks in members:
        n += 1
        if not stage_done(ks, its, pl):
            return n
    return len(members) + 1


def read_list(path):
    """수집 차례 파일 — 「## 」 줄마다 새 묶음(이름 = ## 뒤 첫 낱말 → TIER_NAMES) · 「#」 줄은 설명"""
    tiers, cur = [], []
    del TIER_NAMES[:]
    for ln in open(path, encoding='utf-8'):
        ln = ln.strip()
        if ln.startswith('## '):
            if cur: tiers.append(cur)
            cur = []
            TIER_NAMES.append(ln[3:].split()[0] if ln[3:].split() else '')
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
    raw_t = prefer if prefer and isinstance(prefer[0], list) else [prefer or []]
    names = TIER_NAMES if len(TIER_NAMES) == len(raw_t) else [''] * len(raw_t)
    tn = [(n, [x for x in T if x in pos]) for n, T in zip(names, raw_t)]
    tn = [(n, T) for n, T in tn if T]
    tiers = [T for n, T in tn]; tnames = [n for n, T in tn]   # 묶음(가까운 곳부터) — 앞 묶음이 끝나야 다음 묶음
    stage = {'n': 0, 'at': 0.0, 'basket': [], 'rest': tiers}
    def restage():
        """바구니 다시 정하기(한 시간에 한 번) — 열린 단계의 구 묶음은 한 바구니, 나머지는 묶음 차례"""
        try:
            sd9 = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))
            its9, pl9 = sd9.get('its', {}), sd9.get('pl', {})
        except Exception:
            its9, pl9 = {}, {}
        mem = [[x for n, T in tn if n in G for x in T] for G in STAGE_GU]
        k = open_stages(mem, its9, pl9)
        gus = [g for G in STAGE_GU[:k] for g in G]
        allopen = k > len(STAGE_GU)
        b = [T for n, T in tn if allopen or n in gus] if any(tnames) else tiers[:6]
        r = [T for n, T in tn if not (allopen or n in gus)] if any(tnames) else tiers[6:]
        if k != stage['n']:
            print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), '[단계] %d단계까지 엶 — 바구니 %s' % (k, '서울 전체' if allopen else ' · '.join(gus)), flush=True)
        stage.update(n=k, at=time.time(), basket=b, rest=r)
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
    # 열쇠 고르기는 풀이 맡는다(KeyPool — 404 짝은 쉬고 30분마다 다시 보고, 살아나면 저절로 번갈아 쓴다)
    P = KeyPool({'p': 'phase', 'f': 'fhist'}.get(api, 'timing'))
    W0 = 300 if api == 'p' else 285   # (2026-10-10 19:04 실측 — 줄 수 = 정각 뒤 초 − 8쯤 · 240초에는 234줄이라 문턱 240 에 못 미쳤다 → 285초)  # 정각 뒤 창 — 이때는 교차로마다 300줄쯤이라 한 쪽에 100곳 가까이 들고, 서울 뒤쪽(서초 1668~ · 강남 ~2248)도 20쪽 안이다
    os.makedirs(os.path.join(RAW, 'red'), exist_ok=True)
    spd_at = 0
    while True:
        if api == 't' and time.time() - spd_at >= 600:
            spd_at = time.time()                              # 10분에 한 번 통행속도 한 장 — 신호를 받았든 못 받았든(잔여시간 훑기 쪽에서만)
            if livespd(): publish()
        if time.time() - stage['at'] > 3600:
            restage()
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
            # (2026-10-14 소유자 「서초 강남 동작 관악 용산 · 송파까지 · 다 받아야지」) 앞 여섯 묶음을 **한 바구니**로 — 종전엔 묶음마다 차례로 봐서
            #  서초·강남의 「이 시각대 빈 곳」(늘 1,300곳 넘게 남음)이 끝나지 않아 뒤 묶음이 한 번도 안 골렸다(송파 152곳 가운데 기록 58 · 송파 자리 2249~ 를 찾던 자리로 고른 적 0).
            #  한 바구니에 넣으면 받을 곳이 가장 몰린 자리(K)를 고르는 규칙이 저절로 여섯 구에 나눈다
            for f in (need1, needS):
                c = [i for T in stage['basket'] for i in T if f(i) and ok(i)]
                if c: return c
            for T in stage['rest']:
                c = [i for i in T if need1(i) and ok(i)]
                if c: return c
            c = [i for i in order if need1(i) and ok(i)]
            if c: return c
            for T in stage['rest']:
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
            q1, q2 = ps[len(ps) // 3], ps[2 * len(ps) // 3]   # (2026-10-14) 훑기 셋이 셋으로 나눈다 — 잔여 = 앞 1/3 · 잔여+상태 = 가운데 · 상태 = 뒤 1/3(같은 쪽을 겹쳐 받지 않게)
            cand = [q for q in ps if (q >= q2 if api == 'p' else (q1 <= q <= q2 if api == 'f' else q <= q1))] or ps
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
        P.refresh()
        kl, w9 = P.pick()
        if w9 > 0:
            time.sleep(w9 + 1); continue                       # 그 열쇠의 5분이 안 찼다 — 기다렸다가 처음부터 다시 고른다(시각·쪽이 달라졌다)
        kv, kn = keyval(kl), int(kl[-1])
        P.mark(kl)
        u = {'p': BASEP, 'f': BASEFH}.get(api, BASE) + '?apikey=' + kv + '&pageNo=%d&numOfRows=30000' % page
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
            print(stamp, '쪽', page, 'HTTP', st, mask(body[:160]) + ' [%s]' % kl, flush=True)
            hist(at=stamp, api=api, t=t, page=page, K=K, st=st, k=kn)
            srv = P.note(kl, st, body)
            wait = P.gap()
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
            if st == 429 and srv:
                wait = srv if len(P.alive()) <= 1 else min(srv, P.gap())   # 그 열쇠는 서버가 말한 때까지 쉰다(풀이 rest 로 셈) — 다른 열쇠는 제 차례에 그대로
            time.sleep(wait); continue
        J = json.loads(body); by = {}; seq = []
        for x in J:
            i = str(x['itstId'])
            if i not in by: by[i] = []; seq.append(i)
            by[i].append(x)
        idx = [pos[i] for i in seq if i in pos]
        if not idx:
            print(stamp, {'p': '[상태]', 'f': '[잔여+상태]'}.get(api, '[잔여]'), '쪽', page, '줄', len(J), '— 아는 교차로가 없다(밀도', round(dens, 3), ')', flush=True)
            P.note(kl, 200)
            dens *= 0.8; time.sleep(P.gap()); continue
        a, b = min(idx), max(idx)
        pok = max(pok, b); nfail = 0
        end_note(b=b); hist(at=stamp, api=api, t=t, page=page, K=K, st=200, a=a, b=b, n=len(seq), k=kn)
        P.note(kl, 200)
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
                json.dump(red, open(os.path.join(RAW, 'red', '%s_%s%s.json' % (i, stamp, {'p': 'p', 'f': 'x'}.get(api, ''))), 'w', encoding='utf-8'), ensure_ascii=False); saved += 1
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
        print(stamp, {'p': '[상태]', 'f': '[잔여+상태]'}.get(api, '[잔여]'), '쪽', page, '줄', len(J), '교차로', len(seq), '자리', a, '~', b, '(찾던 자리', K, '맞음' if hit else '빗나감', ') 구움', saved, '밀도', round(dens, 3), '우선 목록 — 닻 없음', len([i for i in pref if need1(i)]), '· 이 시각대 빈 곳', len([i for i in pref if needS(i)]), ('· 끝자리 %d' % pcap) if pcap else '', flush=True)
        if miss >= 4:
            tried.add(order[K]); miss = 0   # 네 번 빗나가면 그 교차로는 건너뛴다
        if api == 't':
            build()
            ncall += 1
            if ncall % 3 == 0:
                publish()
            if ncall % 12 == 0:
                prune()
        time.sleep(P.gap())


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
            elif r.get('src') == 'f':
                o['src'] = 'f'   # (2026-10-14) Fusion 지금 한 줄로 잡은 새 닻 — 녹색 길이·자리는 같은 교차로의 다른 기록(fz.base)에서 빌렸다
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


FZ_GREEN = ('protected-Movement-Allowed', 'permissive-Movement-Allowed')
FZ_RED = ('stop-And-Remain', 'stop-Then-Proceed')


def fz_anchor(itst, row):
    """Fusion 한 줄(그 교차로가 보낸 지금 잔여 초 + 상태)에서 새 닻 — 기준 이동류 녹색이 켜진 실제 시각(a).
    같은 교차로의 줄인 기록(red/)에서 이동류마다 녹색 길이 g·자리 o 를 빌려
      녹색이면 녹색 시작 = 보낸 시각 + 남은 초 − g · 적색이면 다음 녹색 시작 = 보낸 시각 + 남은 초 → 닻 = 녹색 시작 − o
    두 이동류 이상이 ±3초 안으로 같은 닻을 가리킬 때만 쓴다(지금 도는 계획이 그 기록의 계획과 같다는 확인). 남은 초 단위 = 0.1초.
    (2026-10-14 4036 확인: 북 직진 녹색 37.1초 · 북 좌회전 적색 44.1초 · 서 좌회전 적색 63.1초 → 셋 다 같은 닻 ±0.1초)"""
    T = (row.get('trsmUtcTime') or 0) / 1000.0
    if not T or time.time() - T > 600:
        return None                                         # 10분 넘게 묵은 줄은 쓰지 않는다(교차로가 그 뒤로 안 보냈다 — 계획이 바뀌었을 수 있다 · 2026-10-14 게임 세션 권고)
    obs = {}
    for d in DIRS:
        for m in MVS:
            st, R = row.get('%s%ssgStatNm' % (d, m)), row.get('%s%ssgRmdrCs' % (d, m))
            if st and R is not None and 0 <= R < 36000:
                obs[(d, m)] = (st, R / 10.0)
    if len(obs) < 2:
        return None
    now = datetime.datetime.fromtimestamp(T + 9 * 3600, datetime.timezone.utc); dow = (now.weekday() + 1) % 7; day = now.strftime('%Y-%m-%d'); cl = cls_of(dow, day)
    cands = []
    for f in glob.glob(os.path.join(RAW, 'red', '%s_*.json' % itst)):
        try:
            r = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        ci9 = plan_ci(r['cyc'], r['ci']) if r.get('ci') and r.get('cyc') else None
        if ci9 and abs(ci9 - r['cyc']) <= 2.5 and abs(ci9 - round(ci9)) <= 0.05 and not r.get('dq') and r.get('src') != 'f':   # build 가 닻으로 쓰는 기록만(주기가 계획과 맞고 정수 초)
            r = dict(r, ci=ci9)
            same = (cls_of(r['dow'], r['day']) == cl) * 2 + (int(r['from'][:2]) == now.hour)
            cands.append((same, r['day'] + r['to'], r))
    for _, _, r in sorted(cands, key=lambda z: (z[0], z[1]), reverse=True)[:6]:
        ci = float(r['ci']); S = []
        for x in r['mv']:
            if x.get('g') is None or x.get('o') is None or abs(x['g'] + x['y'] + x['r'] - r['cyc']) > 3.5:
                continue
            o = obs.get((x['d'], x['m']))
            if not o:
                continue
            if o[0] in FZ_GREEN and o[1] <= x['g'] + 0.5:
                S.append(T + o[1] - x['g'] - x['o'])
            elif o[0] in FZ_RED and o[1] <= x['r'] + 0.5:
                S.append(T + o[1] - x['o'])
        if len(S) < 2:
            continue
        rel = [((v - S[0] + ci / 2) % ci) - ci / 2 for v in S]
        if max(rel) - min(rel) > 3.0:
            continue
        a = S[0] + sum(rel) / len(rel)
        a -= math.ceil((a - T) / ci) * ci                   # 보낸 시각 바로 앞의 녹색 시작으로
        hm = now.strftime('%H:%M')
        out = dict(r, day=day, dow=dow, **{'from': hm, 'to': hm}, rows=0, a=round(a, 1), end=round(T, 1), src='f',
                   fz={'t': round(T, 1), 'n': len(S), 'sd': round(max(rel) - min(rel), 1), 'base': r['day'] + ' ' + r['from']})
        out.pop('v', None); out.pop('x', None)
        return out
    return None


def fusion(sample=False, ids=None):
    """지금 한 줄(FusionCurrentInfo) 수집 — 교차로(itstId)마다 최신 잔여 초 + 방향별 상태 이름. 원자료는 섞지 않고
    ../07_API키/out/tdata/fusion/<날짜>.jsonl.gz 에 교차로 한 번 = 한 줄({at, id, key, rows}) · sigdir 에는 넣지 않는다.
    ⚠ 2026-10-14 실측: sggCd 는 어느 꼴(11650 · 650 · 1165000000 · 「서초구」)로도 200 에 빈 배열 — 구 단위로는 안 온다 · itstId 하나씩만 온다(여러 번호를 쉼표로 이어도 빈 배열)
       교차로마다 「그 교차로가 마지막으로 보낸 한 줄」이라 오래된 것도 온다(4039 는 50분 전 값) — trsmTm 을 꼭 같이 본다 · 하루 호출 한도는 아직 모른다
    --sample = 4036 한 줄을 받아 CurrentInfo 와 칸을 견준 표를 찍고 멈춘다(2026-10-14 지시 — 보고 뒤 상시 수집)."""
    def fz_step():
        """남은 Fusion 몫(열쇠마다 KEYCAP − 오늘 쓴 수 − 역사 훑기 남길 몫)을 오늘 남은 시간에 고르게 — 두 열쇠면 약 2배로 촘촘"""
        left = 86400 - (time.time() + 9 * 3600) % 86400
        room = sum(max(0, KEYCAP - kd_get(k) - hist_reserve()) for k in P.order if P.st[k]['state'] == 'alive')
        return max(30.0, left / max(1, room))
    step = 30.0                                                 # 첫 값 — 풀(P)이 생긴 뒤 부를 때마다 fz_step() 으로 다시 셈
    P = KeyPool('fusion', gap=30); out = os.path.join(RAW, 'fusion'); os.makedirs(out, exist_ok=True)
    def get(itst, kl):
        u = BASEF + '?apikey=' + keyval(kl) + '&pageNo=1&numOfRows=10&itstId=%s' % itst
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60); return r.status, r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'ignore')
        except Exception as e:
            return 0, str(e)
    if sample:
        kl, w = P.pick(); P.mark(kl); c, b = get('4036', kl); P.note(kl, c, b)
        print('itstId 4036 · 열쇠', kl, '· HTTP', c, mask(b[:200]) if c != 200 else '')
        J = json.loads(b) if c == 200 else []
        if not J:
            print('빈 응답 — 멈춘다'); return
        one = J[0]; cf = os.path.join(RAW, 'probe_v2xSignalPhaseTimingCurrentInfo_KEY2.json')
        cur = (json.load(open(cf, encoding='utf-8')) or [{}])[0] if os.path.exists(cf) else {}
        fk, ck = set(one), set(cur)
        print('| | CurrentInfo | Fusion |'); print('|---|---|---|')
        print('| 칸 수 | %d | %d |' % (len(ck), len(fk))); print('| 공통 칸 | %d | %d |' % (len(ck & fk), len(ck & fk)))
        print('| 한쪽에만 | %s | 상태 이름(StatNm) %d칸 |' % (', '.join(sorted(ck - fk)) or '없음', len([x for x in fk - ck if x.endswith('StatNm')])))
        print('상태 이름 값', sorted(set(v for k2, v in one.items() if k2.endswith('StatNm') and v)), '· 보낸 시각', one.get('trsmTm'))
        return
    AXIS = ('반포대로', '서초대로', '강남대로', '남부순환로', '사평대로')   # 먼저 부르는 축(2026-10-14 게임 세션 권고 · 소유자 승인)
    try:
        FS = json.load(open(os.path.join(ROOT, 'data', 'fac-signal.json'), encoding='utf-8'))['spots']
    except Exception:
        FS = {}
    onaxis = lambda k: any(len(x) > 1 and x[1] in AXIS for x in FS.get(k, {}).get('in', []))
    while True:
        sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))
        its = sd.get('its', {})
        # 대상 = 여섯 구(2026-10-14 소유자 「서초 강남 동작 관악 용산 · 송파까지」) 신호 교차로 전부(fac-signal · 908곳) — 기록이 없는 곳도 하루 한 번은 불러 「T-Data 에 아예 없는 곳」을 가린다(fusion_none.json)
        nf = os.path.join(RAW, 'fusion_none.json')
        try:
            NONE = json.load(open(nf, encoding='utf-8'))
        except Exception:
            NONE = {}
        tday = P.today(); pl = sd.get('pl', {}); nowk = datetime.datetime.fromtimestamp(time.time() + 9 * 3600, datetime.timezone.utc)
        ck = (cls_of((nowk.weekday() + 1) % 7, nowk.strftime('%Y-%m-%d')), nowk.hour)
        try:
            IDS = set(json.load(open(sorted(glob.glob(os.path.join(RAW, 'ids_*.json')))[-1], encoding='utf-8'))['ids'])   # 단계 판정은 T-Data 역사 목록에 있는 교차로로만(목록 밖은 원래 못 받는다)
        except Exception:
            IDS = set(FS)
        mem = [[k for k, v in FS.items() if v.get('gu') in G and k in IDS] for G in STAGE_GU]
        kst = open_stages(mem, its, pl)
        GU6 = [g for G in STAGE_GU[:kst] for g in G] if kst <= len(STAGE_GU) else sorted(set(v.get('gu') for v in FS.values() if v.get('gu')))   # 열린 단계의 구(다 차면 다음 단계 · 모두 차면 서울 전체)
        L = ids or [k for k, v in FS.items() if v.get('gu') in GU6 and NONE.get(k) != tday]
        haveci = lambda k: any(r.get('ci') for r in its.get(k, []))
        L = sorted(L, key=lambda k: (GU6.index(FS.get(k, {}).get('gu', '')) if FS.get(k, {}).get('gu') in GU6 else 9,
                                     0 if haveci(k) else 1,                                                     # 닻을 잡을 수 있는 곳(주기를 아는 곳) 먼저
                                     0 if not any(x[0] == ck[0] and x[1] == ck[1] for x in pl.get(k, [])) else 1,   # 지금 요일 갈래·시각대 칸이 빈 곳 먼저(96칸 채우기)
                                     0 if onaxis(k) else 1,
                                     max([r.get('a') or 0 for r in its.get(k, [])] or [0])))
        nok = nanc = 0
        for itst in L:
            P.refresh(); kl, w = P.pick()
            if P.capped(kl):
                print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), '[fusion] 오늘 몫을 다 씀(열쇠마다 %d · 역사 훑기 몫 남김) — %d분 쉰다' % (KEYCAP, w // 60), flush=True)
                time.sleep(max(w, 600)); break
            if w > 0:
                time.sleep(w)
            P.mark(kl); c, b = get(itst, kl); srv = P.note(kl, c, b); stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            if c == 200:
                try:
                    J = json.loads(b)
                    if not J or not any(v is not None for x in J for k9, v in x.items() if k9.endswith('RmdrCs')):
                        # 빈 배열 = T-Data 에 한 줄도 없다 · 줄은 오는데 잔여 초가 모두 비었다 = 장비는 메시지를 보내지만 신호 값이 없다
                        #  (2026-10-14 인재개발원 3971·23971·33971 — 몇 분 전 보낸 줄인데 방향별 잔여가 전부 null · 역사 목록에도 없음) — 둘 다 그날은 다시 안 부른다
                        NONE[itst] = tday; json.dump(NONE, open(nf, 'w', encoding='utf-8'))
                        try:
                            WHY = json.load(open(nf.replace('.json', '_why.json'), encoding='utf-8'))
                        except Exception:
                            WHY = {}
                        WHY[itst] = [tday, '응답 없음' if not J else '줄은 오지만 잔여 초가 모두 비어 있음', str(J[0].get('trsmTm')) if J else '']
                        json.dump(WHY, open(nf.replace('.json', '_why.json'), 'w', encoding='utf-8'), ensure_ascii=False)
                    with gzip.open(os.path.join(out, stamp[:8] + '.jsonl.gz'), 'at', encoding='utf-8') as g:
                        g.write(json.dumps({'at': stamp, 'id': itst, 'key': kl, 'rows': J}, ensure_ascii=False) + chr(10))
                    nok += 1
                    an = fz_anchor(itst, J[0]) if J else None
                    if an:
                        json.dump(an, open(os.path.join(RAW, 'red', '%s_%sf.json' % (itst, stamp)), 'w', encoding='utf-8'), ensure_ascii=False); nanc += 1
                except Exception as e:
                    print(stamp, '[fusion] 처리 실패', itst, str(e)[:80], flush=True)
            else:
                print(stamp, '[fusion]', itst, kl, 'HTTP', c, mask(b[:120]), flush=True)
                if srv:
                    time.sleep(srv)
            step = fz_step(); time.sleep(step)
        print(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'), '[fusion] 한 바퀴 %d곳(축 %d) · 받음 %d · 새 닻 %d' % (len(L), sum(1 for k in L if onaxis(k)), nok, nanc), flush=True)



def pooltest():
    """풀 단위 시험(통신 없음) — 응답을 흉내 낸다"""
    global key2
    P = KeyPool('timing'); P.st = {k: {'state': 'alive', 'next': 0.0, 'rest': 0.0, 'why': '', 'last': 0.0} for k in P.order}; P.f = os.devnull; ok = True
    if 'KEY2' not in P.order:
        print('둘째 열쇠가 keys.json 에 없어 시험을 건너뛴다'); return
    P.note('KEY2', 404); a = P.alive(); r1 = a == ['KEY1']; ok &= r1; print('① KEY2 404 → 살아 있는 열쇠', a, '맞음' if r1 else '틀림')
    k, w = P.pick(); r2 = k == 'KEY1'; ok &= r2; print('   그다음 고른 열쇠', k, '맞음' if r2 else '틀림')
    P.st['KEY2']['next'] = 0; P.probe = lambda kk: P.st[kk].update(state='alive'); P.refresh(); a = P.alive(); r3 = sorted(a) == ['KEY1', 'KEY2']; ok &= r3; print('② 30분 뒤 재확인 200 → 살아 있는 열쇠', a, '맞음' if r3 else '틀림')
    P.note('KEY1', 429, '{"retryAfterSeconds": 120}'); a = P.alive(); r4 = a == ['KEY2']; ok &= r4; print('③ KEY1 429 → 쉬는 동안 살아 있는 열쇠', a, '맞음' if r4 else '틀림')
    P.st['KEY1']['rest'] = 0; P.st['KEY1']['last'] = time.time(); P.st['KEY2']['last'] = time.time() - 400; k, w = P.pick(); r5 = k == 'KEY2' and w == 0; ok &= r5; print('④ 라운드로빈 — 오래 쉰 열쇠', k, '기다림', round(w), '맞음' if r5 else '틀림')
    print('간격(살아 있는 열쇠 2개)', P.gap(), '초')
    print('모두 맞음' if ok else '틀린 것이 있다')


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
        sweep(pf, a[a.index('--api') + 1] if '--api' in a and a[a.index('--api') + 1] in ('p', 'f') else 't', int(a[a.index('--cap') + 1]) if '--cap' in a else None)
    elif a and a[0] == 'fusion':
        fusion('--sample' in a, [x for x in a[1:] if x.isdigit()] or None)
    elif a and a[0] == 'pooltest':
        pooltest()
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
