# -*- coding: utf-8 -*-
"""교통 온톨로지 코어 v1 — 시험(Node 가 없는 PC 라 머리 없는 크롬에서 query.js·validate.js 를 그대로 돌린다).
  정답은 이 파일이 **원자료에서 따로 다시 센다**(build.py·core-seocho.json 을 정답으로 쓰지 않는다 — 검증 분리).
  표본: 서초역사거리(INT-521 · 4039) · 서울성모병원(INT-548 · 4034) · 서초경찰서(INT-1026 · 4036) · 위반유형 02 신호위반 · 05 과속 · 06 안전운전불이행
  쓰기: py -3.12 -X utf8 ontology-core/test/run.py   (끝 코드 1 = 실패)
"""
import json, os, sys, math, time, socket, threading, http.server, functools, collections
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE); ROOT = os.path.dirname(CORE); D = os.path.join(ROOT, 'data')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'check'))
from cdp import Chrome
def J(p): return json.load(open(p, encoding='utf-8'))
def m(la1, lo1, la2, lo2): return math.hypot((lo1 - lo2) * 88400.0, (la1 - la2) * 111000.0)
C = []
def ck(name, ok, got=''): C.append((name, bool(ok), str(got)[:160]))
# ---- 원자료에서 정답 ----
oi = {r[0]: r for r in J(os.path.join(D, 'onto-int.json'))['items']}
ta = J(os.path.join(D, 'taas10-seocho.json')); al = J(os.path.join(D, 'gargo-alerts-seoul.json')); ks = {x['no']: x for x in J(os.path.join(D, 'sig-ksc-seocho.json'))['items']}
tl = J(os.path.join(CORE, 'src', 'tbook-law.json'))
def truth(tg):
    r = oi[tg]; la, lo = r[2], r[3]; cs = [c for c in ta['cells'] if m(c[0], c[1], la, lo) <= 70]
    yrs = [sum(c[2 + k] for c in cs) for k in range(10)]; vc = collections.Counter()
    for c in cs: vc[c[23]] += c[24]
    cams = sum(1 for c in al['cam'] if c[2] and len(c) > 7 and c[7] == 'p' and m(c[1], c[0], la, lo) <= 100)
    zones = sum(1 for z in al['sz'] if m(z[1], z[0], la, lo) <= 300)
    return {'nm': r[1], 'cits': str(r[4]), 'years': yrs, 'total': sum(yrs), 'night': sum(c[18] for c in cs), 'mainv': vc.most_common(1)[0][0] if vc else None, 'cams': cams, 'zones': zones, 'hist': (ks.get(str(r[4])) or {}).get('hist') or []}
T = {'INT-%d' % k: truth(k) for k in (521, 548, 1026)}
# ---- 시험 페이지를 내준다 ----
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=CORE); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
c = Chrome()
try:
    c.go('http://127.0.0.1:%d/test/test.html?t=%d' % (port, int(time.time())), 1)
    R = None
    for i in range(80):
        v = c.ev("window.__R ? JSON.stringify(window.__R) : ''")
        if v: R = json.loads(v); break
        time.sleep(0.25)
finally:
    c.close(); srv.shutdown()
if not R or 'error' in R: print('❌ 시험 페이지가 답을 못 냈다', R and R.get('error')); sys.exit(1)
# ---- 검증 ----
V = R['validate']; ck('validate — 오류 0(ID 중복·고아 링크·타입 위반·필수 속성)', V['ok'], '오류 %d · 경고 %d · %s' % (V['nErrors'], V['nWarnings'], V['errors'][:2]))
ck('validate — 개인정보 꼴 경고 0', not any('개인정보' in w for w in V['warnings']), [w for w in V['warnings'] if '개인정보' in w][:2])
for i, t in T.items():
    q = R['q1'][i]
    ck('질문1 %s — 이름·신호 번호' % t['nm'], q and q['nm'] == t['nm'] and str(q['cits']) == t['cits'], q and (q['nm'], q['cits']))
    ck('질문1 %s — 해마다 사고(2016~2025)가 원자료와 같다' % t['nm'], q['acc'] and q['acc']['years'] == t['years'], '%s / 정답 %s' % (q['acc'] and q['acc']['years'], t['years']))
    ck('질문1 %s — 밤 사고·주 위반' % t['nm'], q['acc']['night'] == t['night'] and (q['mainViolations'][0]['id'] if q['mainViolations'] else None) == ('VIO-' + t['mainv'] if t['mainv'] else None), (q['acc']['night'], q['mainViolations'][:1]))
    ck('질문1 %s — 시설(경찰 카메라 100m · 보호구역 300m)' % t['nm'], len(q['cams']) == t['cams'] and len(q['zones']) == t['zones'], (len(q['cams']), t['cams'], len(q['zones']), t['zones']))
    ck('질문1 %s — 과거 조치 수 = 교통과 이력 줄 수' % t['nm'], len(q['actions']) == len(t['hist']), (len(q['actions']), len(t['hist'])))
    q2 = R['q2'][i]; ok2 = True; bad = []
    for a in q2['actions']:
        y = int(a['ym'][:4]) if a['ym'] else None
        if a['compare']:
            b = t['years'][y - 2 - 2016] + t['years'][y - 1 - 2016]; f = t['years'][y + 1 - 2016] + t['years'][y + 2 - 2016]
            if (a['compare']['beforeN'], a['compare']['afterN']) != (b, f): ok2 = False; bad.append((a['what'], a['compare'], b, f))
        elif y and 2018 <= y <= 2023: ok2 = False; bad.append(('비교가 있어야 하는데 없음', a['what']))
    ck('질문2 %s — 조치 앞뒤 사고(앞 2해 vs 뒤 2해)가 원자료와 같다' % t['nm'], ok2 and len(q2['actions']) == len(t['hist']), bad[:2] or '%d 조치' % len(q2['actions']))
q2 = R['q2']['INT-548']; last = [a for a in q2['actions'] if a['ym'] == '2025-11']
ck('질문2 서울성모병원 — 2025.11 시차제: 이유 「꼬리물기 해소」 · 뒤 두 해가 아직 없다고 밝힘', last and last[0]['reason'] == '꼬리물기 해소' and last[0]['compare'] is None and '아직' in (last[0]['noCompare'] or ''), last)
law = {l['title']: l for l in tl['laws']}
q3 = R['q3']['VIO-02']; L = q3['laws'][0] if q3['laws'] else None
ck('질문3 신호위반 — 근거 항목·조문·범칙금 글이 T-Book 범칙금 DB 와 글자까지 같다', L and L['title'] == '① 신호위반·안전표지 위반' and L['meta'] == law[L['title']]['meta'] and L['penalty'] == law[L['title']]['penalty'], L and (L['meta'], L['penalty']))
ck('질문3 신호위반 — 판례는 원문 대조된 것만(조회실패 2024도1195 는 잇지 않는다)', L and L['precedents'] and all(tl['precdoc'].get(p['no'], {}).get('c') and tl['precdoc'][p['no']].get('d') and tl['precdoc'][p['no']].get('nm') != '조회실패' for p in L['precedents']) and '2024도1195' not in [p['no'] for p in L['precedents']], L and [p['no'] for p in L['precedents']])
q35 = R['q3']['VIO-05']; ck('질문3 과속 — 판례 2022도13430 이 판결문 참조조문(도로교통법 제17조)으로 이어진다', any(p['no'] == '2022도13430' and p['arts'] == ['도로교통법 제17조'] for l in q35['laws'] for p in l['precedents']), [p['no'] for l in q35['laws'] for p in l['precedents']])
ck('질문3 안전운전불이행 — 범칙금 DB 에 같은 항목이 없다고 밝힌다(지어내지 않음)', not R['q3']['VIO-06']['laws'] and R['q3']['VIO-06']['none'], R['q3']['VIO-06']['none'])
for i, t in T.items():
    q5 = R['q5'][i]; dims = q5.get('dims') or {}
    ok = set(dims) == {'mainv', 'night', 'total', 'fac'} and all(len(d['list']) <= 5 and all(x['id'] != i for x in d['list']) for d in dims.values()) and 'score' not in json.dumps(q5)
    ck('질문5 %s — 항목 넷 따로(합친 점수 없음) · 자기 빼고 5곳까지' % t['nm'], ok, {k: [x['nm'] for x in d['list'][:3]] for k, d in dims.items()})
    mv = dims.get('mainv', {}).get('list') or []
    ck('질문5 %s — 「주 위반이 같다」 목록은 정말 주 위반이 같다' % t['nm'], len(mv) > 0 and all(x == R['q5mv'][i + '_me'] for x in R['q5mv'][i]), (R['q5mv'][i + '_me'], R['q5mv'][i]))
RL = J(os.path.join(D, 'onto-rules.json')); RR = {r['id']: r for r in RL['rules']}
ck('질문6 — 규칙 %d · 영역 「신호」 %d 가 장부와 같다' % (len(RL['rules']), sum(1 for r in RL['rules'] if r.get('area') == '신호')), [x['id'] for x in R['rules']] == sorted(RR) and len(R['rulesSig']) == sum(1 for r in RL['rules'] if r.get('area') == '신호'), [len(R['rules']), len(R['rulesSig'])])
bad6 = []
for rid, r in RR.items():
    w = R['why'][rid]; want = sorted([f for f in RL['field'] if rid in (f.get('use') or [])], key=lambda f: f['date'])
    if (w['title'], w['d'], w['g'], w['s'], w['o'], w['test']) != (r['title'], r['d'], r['g'], r.get('s') or [], r.get('o') or [], r.get('t')): bad6.append(rid + ' 규칙 글')
    if [(f['id'], f['said'], f['date']) for f in w['field']] != [(f['id'], f['said'], f['date']) for f in want]: bad6.append(rid + ' 현장 말')
ck('질문6 — 규칙마다 정의·출처·등급·주인 자리·시험값과 기댄 현장 말이 장부 글자 그대로', not bad6, bad6[:3])
ck('질문6 — 반포 관할 규칙(RULE-JUR-2)에 형님 말 「반포본동·반포2동은…」이 붙어 있다', any(f['id'] == 'FK-BANPO-1' and f['said'].startswith('반포본동·반포2동은') for f in R['why']['RULE-JUR-2']['field']), [f['id'] for f in R['why']['RULE-JUR-2']['field']])
ck('질문6 — 규칙이 아닌 것을 물으면 null', R['whyBad'] is None, R['whyBad'])
# ---- 질문 7 · 행정동(2026-10-23) — 원자료(house-dong · mig-dong · foreign-dong · econ-dong · dui-ref-seoul · police.json · onto-int)에서 따로 ----
hd = J(os.path.join(D, 'house-dong.json'))['dong']; mg = J(os.path.join(D, 'mig-dong.json'))['dong']; fg = J(os.path.join(D, 'foreign-dong.json'))['dong']
ec = J(os.path.join(D, 'econ-dong.json'))['dong']; drs = {x[0]: x for x in J(os.path.join(D, 'dui-ref-seoul.json'))['items']}; pol = J(os.path.join(D, 'police.json'))
stn = {str(s[0]): s[1] for s in pol['stations']}
for code, want_jur in (('11650530', ['서울서초경찰서']), ('11650590', ['서울방배경찰서', '서울서초경찰서(일부 번지)']), ('11650581', ['서울서초경찰서', '서울방배경찰서'])):
    q = R['q7']['DNG-' + code]; mine = [r for r in oi.values() if r[6] == '11650' and (r[7] or '')[:8] == code]
    ck('질문7 %s — 세대·1인·주민·외국인·사업장·가입자·주점·호프 0~6시가 원자료 그대로' % q['nm'], (q['people']['hh'], q['people']['one'], q['people']['res'], q['people']['fgn'], q['work']['biz'], q['work']['wk'], q['night']['bars'], q['night']['hof06']) ==
       (hd[code]['hh'][0], hd[code]['hh'][1], mg[code][2], (fg.get(code) or {}).get('t'), ec[code][0], ec[code][1], drs[code][4] if code in drs else None, drs[code][10] if code in drs else None), (q['people'], q['work'], q['night']))
    ck('질문7 %s — 관할 %s(police.json 별표2 꼴 그대로 읽음)' % (q['nm'], want_jur), q['jur'] == want_jur, q['jur'])
    ck('질문7 %s — 그 동 안 교차로 수 = onto-int 서초 행정동 코드로 센 수 · 사고 많은 순' % q['nm'], q['nInt'] == len(mine) and [x['total'] for x in q['ints']] == sorted([x['total'] for x in q['ints']], reverse=True), (q['nInt'], len(mine)))
ck('질문1 서초역사거리 — 속한 동 = 서초3동(onto-int 행정동 코드) · 등급 B', R['q1']['INT-521']['dng'] and R['q1']['INT-521']['dng']['nm'] == '서초3동' and R['q1']['INT-521']['dng']['grade'] == 'B', R['q1']['INT-521']['dng'])
ck('질문7 — 행정동이 아닌 것을 물으면 null', R['q7bad'] is None, R['q7bad'])
# ---- 질문 8 · 사건(2026-10-23) — 원자료(rally-seoul · venue-events-kopis · season-seocho · 07_API키/out 돌발 기록)에서 따로 ----
import gzip, glob, datetime as _dt
OUTX = os.path.join(os.path.dirname(ROOT), '07_API키', 'out'); td = _dt.date.today()
rl = J(os.path.join(D, 'rally-seoul.json'))['items']; kp = J(os.path.join(D, 'venue-events-kopis.json'))['venues']; ss = J(os.path.join(D, 'season-seocho.json'))['traces']
inc = {}
for sub, fs, I in (('T', 'liveacc', (0, 5, 6, 2)), ('U', 'utic/ims', (0, 4, 5, 1))):
    for f in sorted(glob.glob(os.path.join(OUTX, fs, '*.jsonl.gz'))):
        for L in gzip.open(f, 'rt', encoding='utf-8'):
            for it in json.loads(L)['items']: inc.setdefault(sub + str(it[I[0]]), (it[I[1]], it[I[2]], it[I[3]]))
lo_d = (td - _dt.timedelta(days=90)).isoformat(); hi_d = (td + _dt.timedelta(days=21)).isoformat()
for tg in (521, 324, 1159, 4612):
    i = 'INT-%d' % tg; r = oi[tg]; la, lo = r[2], r[3]; q = R['q8'][i]; c = collections.Counter()
    for x in rl:
        if 'lat' in x and (m(x['lat'], x['lon'], la, lo) <= 300 or (x.get('dest') and m(x['dest'][0], x['dest'][1], la, lo) <= 300)): c['집회'] += 1
    for v in kp:
        if v.get('lat') and m(v['lat'], v['lon'], la, lo) <= 500:
            for s_ in v.get('shows') or []:
                if (s_[7] or 0) >= 1000 and s_[3] >= lo_d and s_[2] <= hi_d: c['공연'] += 1
    for k_, (a, b, sub) in inc.items():
        if m(a, b, la, lo) <= 150: c['돌발·' + sub] += 1
    fl = collections.defaultdict(int)
    for t in ss:
        tlo = 127.01 + t[0] / 88800.0; tla = 37.49 - t[1] / 111000.0
        if m(tla, tlo, la, lo) <= 100: fl[t[2]] += t[3]
    ck('질문8 %s — 집회·공연·돌발 갈래별 수가 원자료 따로 셈과 같다' % q['nm'], dict(c) == q['counts'] and q['n'] == sum(c.values()), (dict(c), q['counts']))
    ck('질문8 %s — 침수 흔적 해·흔적 수가 침수흔적도 따로 셈과 같다' % q['nm'], [(f['year'], f['n']) for f in q['flood']] == sorted(fl.items()), ([(f['year'], f['n']) for f in q['flood']], sorted(fl.items())))
ck('질문8 서초역사거리 — 최근 먼저 · since(2026-10-01) 거르기', [e['d0'] for e in R['q8']['INT-521']['events']] == sorted([e['d0'] for e in R['q8']['INT-521']['events']], reverse=True) and all(e['d0'] >= '2026-10-01' for e in R['q8since']['events']) and R['q8since']['n'] == sum(1 for e in R['q8']['INT-521']['events'] if e['d0'] >= '2026-10-01'), R['q8since']['counts'])
ck('질문8 — 교차로가 아닌 것을 물으면 null', R['q8bad'] is None, R['q8bad'])
# ---- 질문 9·10 · 접근로·도로 구간(2026-10-23) — sig-approach · nav · spd-normal · flood-link · rd-cell 에서 따로 ----
SA = J(os.path.join(D, 'sig-approach-seocho.json'))['spots']; NVL = {l[0]: l for l in J(os.path.join(D, 'nav-seocho.json'))['links']}
SN = J(os.path.join(D, 'spd-normal-seocho.json'))['links']; FLK = {x[0]: x for x in J(os.path.join(D, 'flood-link-seocho.json'))['items']}; RCX = J(os.path.join(D, 'rd-cell-seocho.json'))
for tg in (521, 548, 1026, 324):
    i = 'INT-%d' % tg; q = R['q9'][i]; sp_ = SA.get(str(oi[tg][4])) or {'in': {}}
    want = {d: [l[0] for r in rs for l in r[4]] for d, rs in sp_['in'].items()}
    ck('질문9 %s — 들어오는 쪽과 쪽마다 링크 수가 sig-approach 와 같다' % q['nm'], {a['dir']: a['nLinks'] for a in q['approaches']} == {d: len(v) for d, v in want.items()}, ({a['dir']: a['nLinks'] for a in q['approaches']}, {d: len(v) for d, v in want.items()}))
    ok = True; got = []
    for a in q['approaches']:
        ls = want[a['dir']]
        for h in ('0-8', '0-18'):
            t = c_ = 0
            for lid in ls:
                v = (SN.get(lid) or {}).get(h); L = NVL.get(lid)
                if v and v[0] > 0: ln = L[3] if L else 0; t += ln / v[0] * 3.6; c_ += ln
            exp = round(c_ / t * 3.6) if c_ else None; g = a['speed'][h]['kmh'] if a['speed'][h] else None
            if exp != g: ok = False; got.append((a['dir'], h, exp, g))
        wet = [FLK[l] for l in ls if l in FLK]; f = a['flood']
        if (len(wet), max([w[5] for w in wet] or [0])) != ((f['links'], f['years']) if f else (0, 0)): ok = False; got.append((a['dir'], 'flood', len(wet), f))
        cs = sorted({'PLC-' + RCX['cells'][ci] for l in ls for ci in RCX['links'].get(l, [])})
        if cs != a['cells']: ok = False; got.append((a['dir'], 'cells', len(cs), len(a['cells'])))
    ck('질문9 %s — 쪽마다 평소 속도(월~목 8·18시 · 길이/시간) · 침수 링크 · 지나는 칸이 원자료 따로 셈과 같다' % q['nm'], ok, got[:3])
for rid in ('RD-1210020206', 'RD-1210019704'):
    lid = rid[3:]; q = R['q10'][rid]; feeds = sorted((no, d, rs[0][0] and [l[0] for r in rs for l in r[4]].index(lid)) for no, s_ in SA.items() for d, rs in s_['in'].items() if lid in [l[0] for r in rs for l in r[4]] and any(str(r_[4]) == no and r_[6] == '11650' for r_ in oi.values()))
    ck('질문10 %s — 들어가는 교차로·쪽·차례가 sig-approach 와 같다 · 길이·이름은 nav' % rid, sorted((f['apr'].split('-')[1], f['dir'], f['k']) for f in q['feeds']) == feeds and q['len'] == NVL[lid][3] and q['nm'] == NVL[lid][7], (q['feeds'], feeds))
# ---- 도로 구간 ↔ 사고 칸(2026-10-23) — 접근로 링크 선과 TAAS 칸에서 따로: 칸 가운데에서 가장 가까운 링크(50m 안) 하나 ----
cits_sc = {str(r_[4]) for r_ in oi.values() if r_[6] == '11650' and r_[4]}
LK = sorted({l[0] for no, s_ in SA.items() if no in cits_sc for rs in s_['in'].values() for r in rs for l in r[4]})
def pline(lid):
    g = NVL[lid][9]; out = [(g[0], g[1])]
    for k in range(2, len(g), 2): out.append((out[-1][0] + g[k], out[-1][1] + g[k + 1]))
    return [(x / 1e5, y / 1e5) for x, y in out]
def dseg(la, lo, a, b):
    ax, ay = (a[0] - lo) * 88400.0, (a[1] - la) * 111000.0; bx, by = (b[0] - lo) * 88400.0, (b[1] - la) * 111000.0
    vx, vy = bx - ax, by - ay; L2 = vx * vx + vy * vy; t = 0 if L2 == 0 else max(0.0, min(1.0, -(ax * vx + ay * vy) / L2)); return math.hypot(ax + t * vx, ay + t * vy)
PL = {l: pline(l) for l in LK if l in NVL}; OWN = collections.defaultdict(list)
for c_ in ta['cells']:
    bd = None
    for l, pts in PL.items():
        if abs(pts[0][1] - c_[0]) > 0.02 or abs(pts[0][0] - c_[1]) > 0.02: continue
        d = min(dseg(c_[0], c_[1], a, b) for a, b in zip(pts, pts[1:]))
        if d <= 50 and (bd is None or d < bd[1] or (d == bd[1] and 'RD-' + l < 'RD-' + bd[0])): bd = (l, d)
    if bd: OWN[bd[0]].append(c_)
ck('도로 구간 ↔ 사고 칸 — 이어진 칸 수가 따로 셈과 같다(서초)', sum(len(v) for v in OWN.values()) == R['nACL'], (sum(len(v) for v in OWN.values()), R['nACL']))
for tg in (521, 548, 1026, 324):
    i = 'INT-%d' % tg; q = R['q9'][i]; sp_ = SA.get(str(oi[tg][4])) or {'in': {}}; ok = True; got = []
    for a in q['approaches']:
        cs = [c_ for r in sp_['in'][a['dir']] for l in r[4] for c_ in OWN.get(l[0], [])]
        exp = (len(cs), sum(sum(c_[2:12]) for c_ in cs), sum(c_[12] for c_ in cs), sum(c_[14] for c_ in cs)) if cs else None
        g = (a['acc']['cells'], a['acc']['total'], a['acc']['dead'], a['acc']['ped']) if a['acc'] else None
        if exp != g: ok = False; got.append((a['dir'], exp, g))
    ck('질문9 %s — 쪽마다 길에 걸친 사고 칸·10년 건수·사망·보행자가 TAAS 따로 셈과 같다' % q['nm'], ok, got[:3] or [(a['dir'], a['acc'] and a['acc']['total']) for a in q['approaches']])
# ---- 질문 11 · 칸 ↔ 생활인구(2026-10-23) — data/r/<서울 구>/live250.json · onto-int 칸 · rd-cell 에서 따로 ----
LV = {}
for g_ in sorted(os.listdir(os.path.join(D, 'r'))):
    f_ = os.path.join(D, 'r', g_, 'live250.json')
    if g_.startswith('11') and os.path.exists(f_):
        for k_, v_ in J(f_)['cells'].items():
            o_ = LV.setdefault(k_, {'wd': [0] * 24, 'we': [0] * 24}); o_['wd'] = [a + b for a, b in zip(o_['wd'], v_['wd'])]; o_['we'] = [a + b for a, b in zip(o_['we'], v_['we'])]
for tg in (521, 548, 1026, 324):
    i = 'INT-%d' % tg; q = R['q11'][i]; cell = oi[tg][9]; sp_ = SA.get(str(oi[tg][4])) or {'in': {}}
    cs = {RCX['cells'][ci] for rs in sp_['in'].values() for r in rs for l in r[4] for ci in RCX['links'].get(l[0], [])} | {cell}
    wd = [sum(LV[c_]['wd'][h] for c_ in cs if c_ in LV) for h in range(24)]
    hb = [sum(LV[cell]['wd'][h] for h in range(6 * k, 6 * k + 6)) for k in range(4)]
    ok = q['here']['wd'] == LV[cell]['wd'] and q['here']['we'] == LV[cell]['we'] and q['around']['wd'] == wd and q['around']['cells'] == len(cs) and q['bins']['peopleWd'] == [round(v / sum(hb) * 1000) / 10 for v in hb]
    ck('질문11 %s — 교차로 칸·둘레 칸 합 시간대 사람과 6시간 몫이 생활인구 격자 따로 셈과 같다' % q['nm'], ok, (q['here']['peakWd'], q['around']['cells'], len(cs), q['bins']))
ck('질문11 — 교차로가 아닌 것을 물으면 null', R['q11bad'] is None)
# ---- 질문 12·13 · 관할서·지구대(2026-10-23) — jur-seocho 경계·police.json 에서 따로(서초 교차로는 모두 현장 기준 경계 안) ----
PJ = J(os.path.join(D, 'police.json')); JZ = J(os.path.join(D, 'jur-seocho.json'))['zones']
def inside(lo, la, ring):
    n_ = 0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > la) != (y2 > la) and lo < x1 + (x2 - x1) * (la - y1) / (y2 - y1): n_ += 1
    return n_ % 2 == 1
SNO = {s_[1]: s_[0] for s_ in PJ['stations']}; PBN = collections.defaultdict(list)
for k_, b_ in enumerate(PJ['pbox']): PBN[b_[6]].append((k_, b_))
def jur_of(tg):
    r = oi[tg]; z = [z_['name'] for z_ in JZ if any(inside(r[3], r[2], [tuple(p_) for p_ in rg]) for rg in z_['rings'])]
    no = SNO[z[0]]; kb = min(PBN[no], key=lambda x: (m(r[2], r[3], x[1][3], x[1][4]), x[0]))
    return no, 'PBX-%d' % kb[0], round(m(r[2], r[3], kb[1][3], kb[1][4]))
for tg in (521, 548, 1026, 324, 5928):
    q = R['q12']['INT-%d' % tg]; no, pb, d = jur_of(tg)
    ck('질문12 %s — 관할서(앞)·가장 가까운 지구대·거리가 경계·주소 현황 따로 셈과 같다' % q['nm'], q['stations'][0]['id'] == 'STA-%d' % no and q['pbox']['id'] == pb and q['pbox']['d'] == d, (q['stations'], q['pbox'], no, pb, d))
cnt = collections.Counter(jur_of(r_[0])[1] for r_ in oi.values() if r_[6] == '11650')
ck('질문13 — 지구대·파출소마다 묶인 교차로 수가 따로 셈과 같다(서초 %d곳)' % len(cnt), {k_: v_['nInt'] for k_, v_ in R['q13'].items() if v_['nInt']} == dict(cnt), sorted(cnt.items())[:4])
ck('질문12 서울성모병원 — 경계(방배)와 T-GIS(서초)가 달라 둘 다 C 로 적는다', [(x['id'], x['g'], x['kind']) for x in R['q12']['INT-548']['stations']] == [('STA-27', 'C', 'disagree'), ('STA-23', 'C', 'tgis')], R['q12']['INT-548']['stations'])
ck('질문12·13 — 다른 것을 물으면 null', R['q12bad'] is None and R['q13bad'] is None)
# ---- 질문 14·15 · 도착(2026-10-23) — nav-seocho 길에서 따로 다익스트라(제한속도 · 평일 8·18시 평소 속도 + eta-cal 배율) ----
import heapq
NVA = J(os.path.join(D, 'nav-seocho.json')); NN = NVA['nodes']; NL = NVA['links']; EF = J(os.path.join(D, 'eta-cal.json'))['f']
OUTL = collections.defaultdict(list); INN = set()
for i_, x_ in enumerate(NL): OUTL[x_[1]].append(i_); INN.add(x_[2])
def nearest(lo, la, ok, r):
    b_ = None
    for k_, v_ in NN.items():
        if k_ in ok:
            d_ = math.hypot((v_[0] - lo) * 88400.0, (v_[1] - la) * 111000.0)
            if d_ <= r and (b_ is None or (d_, k_) < b_): b_ = (d_, k_)
    return b_
def lt(i_, h):
    x_ = NL[i_]; t0 = x_[3] / (max(x_[4] or 0, 20) / 3.6)
    if h is None: return t0
    v_ = (SN.get(x_[0]) or {}).get('0-%d' % h)
    return x_[3] / (v_[0] / 3.6) if v_ and v_[0] > 0 else t0 * EF['평일|출근' if h == 8 else '평일|퇴근']
def sp_(k_, h, goal):
    b_ = PJ['pbox'][k_]; s_ = nearest(b_[4], b_[3], OUTL, 400); Dd = {s_[1]: s_[0] / (20 / 3.6)}; q_ = [(Dd[s_[1]], s_[1])]
    while q_:
        d_, u_ = heapq.heappop(q_)
        if u_ == goal: return round(d_)
        if d_ > Dd.get(u_, 1e18): continue
        for i_ in OUTL[u_]:
            nd = d_ + lt(i_, h); v_ = NL[i_][2]
            if nd < Dd.get(v_, 1e18): Dd[v_] = nd; heapq.heappush(q_, (nd, v_))
    return -1
for tg in (521, 548, 1026, 324):
    i = 'INT-%d' % tg; r = oi[tg]; goal = nearest(r[3], r[2], INN, 80)[1]; Q_ = R['q14'][i]; ok = True; got = []
    for x in Q_['a']['list'][:3]:
        k_ = int(x['id'][4:]); e_ = (sp_(k_, None, goal), sp_(k_, 8, goal), sp_(k_, 18, goal))
        if e_ != (x['s0'], x['s8'], x['s18']): ok = False; got.append((x['nm'], e_, (x['s0'], x['s8'], x['s18'])))
    ck('질문14 %s — 지구대 세 곳의 제한속도·8시·18시 초가 길에서 따로 찾은 값과 같다 · 시각마다 짧은 차례' % Q_['a']['nm'], ok and all([y[k] for y in Q_[c]['list']] == sorted(y[k] for y in Q_[c]['list']) for c, k in (('a', 's0'), ('b', 's8'), ('c', 's18'))), got[:2] or [(Q_['c']['fastest']['nm'], Q_['c']['fastest']['s18'], Q_['c']['nearestOwn'])])
RCH = {k_: v_ for k_, v_ in J(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto', 'onto-reach-seocho.json'))['items'].items() if v_}
ck('도착 — 공개 코어에는 「도착」 링크가 없고 비공개 전체 판에만 있다 · datamap/data 에 onto-reach 파일이 없다', R['priv']['has'] and R['priv']['pubArrive'] == 0 and not glob.glob(os.path.join(D, 'onto-reach-*.json')), R['priv'])
ck('질문14 — 도착은 교차로마다 다섯 이하 · 도착 자료가 있는 교차로 수가 onto-reach 와 같다(%d곳 · 길 노드에 못 붙은 작은 길 교차로·닿는 관서가 없는 곳은 빠짐)' % len(RCH), R['nArrInt'] == len(RCH) and R['nArrive'] == sum(len(v_) for v_ in RCH.values()), (R['nArrInt'], R['nArrive']))
ck('질문15 반포지구대 — 가장 빨리 닿는 교차로 수·자기 몫인데 다른 곳이 빠른 곳이 질문14 를 모은 것과 같다', R['q15']['nFirst'] == len(R['q15']['first']) and R['q15']['under3min'] <= R['q15']['nFirst'], (R['q15']['nFirst'], R['q15']['under3min'], len(R['q15']['slowerOwn'])))
ck('질문14·15 — 다른 것을 물으면 null', R['q14bad'] is None and R['q15bad'] is None)
ck('질문9·10 — 다른 것을 물으면 null', R['q9bad'] is None and R['q10bad'] is None)
ck('지도용 가벼운 판(core-seocho-map) — 모든 교차로 q1·q2 와 표본 q3·q5 가 전체 판과 같다 · 검증 오류 0', R['lite']['same'] and R['lite']['vbad'] == 0, R['lite'])
NG = R['negative']; ck('validate 가 결함을 잡는다(망가뜨린 사본 — 고아·타입 위반·필수 속성·ID 중복 · 차량번호 꼴 경고)', NG['nErrors'] >= 4 and any('고아' in e for e in NG['errors']) and any('타입 위반' in e for e in NG['errors']) and any('필수' in e for e in NG['errors']) and any('중복' in e for e in NG['errors']) and any('차량번호' in w for w in NG['warnings']) and any('RULE-X-9.title' in e for e in NG['errors']) and any('뒷받침' in e and '타입 위반' in e for e in NG['errors']), '오류 %d · %s' % (NG['nErrors'], [e[:30] for e in NG['errors'][:4]]))
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got if got else ''))
print(('✅ 온톨로지 코어 시험 통과 %d/%d' if n == len(C) else '❌ 온톨로지 코어 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
