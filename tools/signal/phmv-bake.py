# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 현시 → 이동류 표(게임 세션 요청 2026-10-10 「지금 2현시」에 방향을 붙이려고) → data/sig-phmv-seoul.json
#   경찰청 계획(data/signal-tod-seoul.json)에는 현시마다 몇 초인지만 있고 어느 방향인지는 없다. 서울 T-Data 로 받은 값(data/sigdir-seoul.json)에는
#   이동류마다 녹색이 켜진 실제 시각(a + 녹색 시작)과 길이가 있다 → 그 시각을 자정 기준 옵셋으로 주기 안 자리로 옮겨, 어느 현시가 시작할 때 켜져서 어느 현시가 끝날 때 꺼졌는지 맞댄다
#   맞는 기준: 켜진 자리가 어느 현시 시작과 ±TOL 초 · 녹색 + 황색이 끝난 자리가 어느 현시 끝과 ±TOL 초 · 둘 다 맞은 것만 싣는다(하나라도 안 맞으면 버린다 — 지어내지 않는다)
#   받은 주기가 그 시각 계획 주기와 같은 기록만 쓴다 · 재료는 이미 있는 두 파일뿐(새로 받는 것 없음)
#   py -3.12 -X utf8 tools/signal/phmv-bake.py   (sigdir 가 더 모이면 다시 — offset-check.py 와 같이)
import json, os, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KST = datetime.timezone(datetime.timedelta(hours=9)); TOL = 6
def near(x, C): return min(x % C, (-x) % C)
def span(ring, C, on, off):
    b = [0]
    for v in ring: b.append(b[-1] + v)
    n = len(ring); i = min(range(n), key=lambda k: near(on - b[k], C)); j = min(range(n), key=lambda k: near(off - b[k + 1], C))
    if near(on - b[i], C) > TOL or near(off - b[j + 1], C) > TOL: return None
    ph = []; k = i
    while True:
        ph.append(k + 1)
        if k == j: break
        k = (k + 1) % n
        if len(ph) > n: return None
    return ph, round(near(on - b[i], C) + near(off - b[j + 1], C), 1)
def main():
    s = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); t = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))
    SP = {str(e['no']): e for e in t['spots']}; out = {}; used = 0; tried = 0; fit = 0
    for no, recs in s['its'].items():
        e = SP.get(no)
        if not e: continue
        V = collections.defaultdict(collections.Counter); seen = collections.Counter(); nrec = 0; dq = 0; nph = 0
        for rec in recs:
            if 'a' not in rec: continue
            d = datetime.datetime.fromtimestamp(rec['a'], KST); sod = d.hour * 3600 + d.minute * 60 + d.second
            plan = e['plans'].get(e['dow'].get(str(d.isoweekday() % 7 + 1)))
            if not plan: continue
            cur = None
            for r in plan:
                if int(r[0][:2]) * 3600 + int(r[0][3:]) * 60 <= sod: cur = r
            cur = cur or plan[-1]; C, off = cur[1], cur[2]
            if rec.get('ci') != C: continue
            A = [int(v) for v in cur[3].split()]; B = [int(v) for v in cur[4].split()]
            if sum(A) != C or sum(B) != C: continue
            nrec += 1; dq += 1 if rec.get('dq') else 0; nph = max(nph, len(A), len(B))
            for m in rec.get('mv', []):
                if len(m) < 7 or (len(m) > 7 and m[7] == 2): continue   # 한 주기에 두 번 켜지는 이동류는 어느 현시인지 가를 수 없다
                g, y, st = m[2], m[3], m[5]
                if g is None or y is None or st is None: continue
                if g + y >= C - TOL: continue
                tried += 1; key = (m[0], m[1]); seen[key] += 1
                on = sod + st - off; end = on + g + y
                ra = span(A, C, on, end); rb = span(B, C, on, end) if B != A else ra
                if not ra and not rb: continue
                if ra and rb and ra[0] == rb[0]: pick, ring = ra, ''
                elif ra and rb: pick, ring = (ra, 'A') if ra[1] <= rb[1] else (rb, 'B')
                else: pick, ring = (ra, 'A') if ra else (rb, 'B')
                V[key][(tuple(pick[0]), ring)] += 1; fit += 1
        if not nrec: continue
        ph = collections.defaultdict(list); bad = []
        for key, c in V.items():
            (p, ring), n = c.most_common(1)[0]
            if n < sum(c.values()): bad.append([key[0], key[1], sum(c.values()) - n])   # 기록마다 답이 갈린 이동류 — 가장 많이 나온 것만 싣고 갈린 수를 적는다
            for k in p: ph[str(k)].append([key[0], key[1], ring, n, seen[key]])
        if not ph: continue
        for k in ph: ph[k].sort()
        out[no] = {'name': e['name'], 'n': nrec, 'nph': nph, 'ph': {k: ph[k] for k in sorted(ph, key=int)}}
        if bad: out[no]['mix'] = bad
        if dq: out[no]['dq'] = 'dir'
        if ph.get('1') and not any(m[1] == 'St' for m in ph['1']): out[no]['warn'] = 'p1'
        used += nrec
    doc = {'schema': 'tg-sig-phmv/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': 'data/sigdir-seoul.json(서울특별시 교통빅데이터플랫폼 T-Data V2X 신호 잔여시간 — 이동류마다 녹색이 실제로 켜진 시각과 길이) × data/signal-tod-seoul.json(경찰청 교차로계획정보서비스 — 현시별 초 · 공공데이터포털 15056569)',
           'how': '이동류 녹색이 켜진 실제 시각을 자정 기준 옵셋으로 주기 안 자리로 옮겨, 어느 현시가 시작할 때 켜졌고(±%d초) 녹색 + 황색이 어느 현시가 끝날 때 끝났는지(±%d초) 맞댔다. 둘 다 맞은 것만 실었다. 받은 주기가 그 시각 계획 주기와 같은 기록만 썼다.' % (TOL, TOL),
           'note': ['계획표에 적힌 것이 아니라 실제 신호 시각과 계획을 맞대어 읽은 **추정**이다 — 화면에 낼 때 「실제 신호와 맞대어 읽음」이라고 밝힌다',
                    '방위 = 그 신호를 받는 차가 들어오는 쪽(sigdir 과 같다) · St 직진 · Lt 좌회전 · Bs 버스 신호(이동류 이름은 sigdir 원문 그대로)',
                    '맞댄 기록 수(n)가 1~2 인 곳이 대부분이다 — 한 번 본 것이라 근거가 얇다. sigdir 가 더 모이면 다시 굽는다',
                    '링이 빈 글이면 A·B 링 어느 쪽으로 봐도 같은 현시다 · A 나 B 면 두 링의 현시 경계가 달라 그 링에만 맞은 것(겹침 현시)',
                    '한 이동류가 여러 현시에 걸쳐 켜져 있으면 그 현시마다 실었다 · 한 주기에 두 번 켜지는 이동류와 주기 내내 켜진 이동류는 뺐다',
                    '현시에 이동류가 하나도 없으면 그 현시는 받은 값으로 못 가린 것이다(보행 전용·받은 값에 없는 방향) — 비어 있다고 「차 신호 없음」이 아니다',
                    'mix = 기록마다 답이 갈린 이동류[방위, 이동류, 갈린 기록 수] — 시간대 계획에 따라 현시 구성이 다를 수 있다 · dq dir = 원자료의 방위 이름이 실제와 다른 교차로(초는 맞아도 어느 쪽인지는 현장 확인)',
                    'warn p1 = 1현시에 직진이 없고 좌회전만 읽힌 곳 — 보통 1현시는 통행이 많은 주도로 직진이다(소유자 현장 지식 2026-10-10). 좌회전이 먼저 나가는 곳인지 맞대기가 어긋난 것인지 이 자료로 못 가린다(회전 방향별 교통량 자료가 없다) → 방향을 붙이지 않는다',
                    '받은 시간대의 계획에서 읽은 것이다 — 다른 시간대 계획은 현시 수·순서가 다를 수 있다(nph = 맞댄 계획의 현시 수)'],
           'fields': 'spots{교차로 번호: {name, n 맞댄 기록 수, nph 현시 수, ph{현시 번호: [[방위, 이동류, 링(빈 글·A·B), 맞은 기록 수, 본 기록 수]…]}, mix, dq, warn}}',
           'result': {'교차로': len(out), '기록': used, '이동류 맞대기': tried, '맞음': fit}, 'spots': out}
    p = os.path.join(ROOT, 'data', 'sig-phmv-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(out), '· 기록', used, '· 이동류', tried, '· 맞음', fit, '· 바이트', os.path.getsize(p))
    full = sum(1 for v in out.values() if len(v['ph']) == v['nph']); print('모든 현시에 이동류가 붙은 곳', full, '· 갈린 곳', sum(1 for v in out.values() if 'mix' in v))
    for no in list(out)[:4] + [k for k, v in out.items() if '교보' in v['name'] or '화양' in v['name']]: print(no, json.dumps(out[no], ensure_ascii=False))
if __name__ == '__main__': main()
