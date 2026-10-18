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
NG = R['negative']; ck('validate 가 결함을 잡는다(망가뜨린 사본 — 고아·타입 위반·필수 속성·ID 중복 · 차량번호 꼴 경고)', NG['nErrors'] >= 4 and any('고아' in e for e in NG['errors']) and any('타입 위반' in e for e in NG['errors']) and any('필수' in e for e in NG['errors']) and any('중복' in e for e in NG['errors']) and any('차량번호' in w for w in NG['warnings']) and any('RULE-X-9.title' in e for e in NG['errors']) and any('뒷받침' in e and '타입 위반' in e for e in NG['errors']), '오류 %d · %s' % (NG['nErrors'], [e[:30] for e in NG['errors'][:4]]))
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got if got else ''))
print(('✅ 온톨로지 코어 시험 통과 %d/%d' if n == len(C) else '❌ 온톨로지 코어 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
