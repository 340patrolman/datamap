# -*- coding: utf-8 -*-
"""선착 역 계산 모듈(js/station-reach.js) 단위 시험 — 머리 없는 크롬에서 모듈을 그대로 돌린다(Node 없음).
  쓰기: py -3.12 -X utf8 tools/check/sr-test.py   (끝 코드 1 = 실패) · 계산식을 고칠 때는 여기를 먼저 고치고 통과시킨 뒤 판을 올린다
"""
import json, os, sys, socket, threading, http.server, functools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from cdp import Chrome
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = r'''(async function(){ var j = await (await fetch('/data/train-run-seoul.json')).json(), S = window.SR; S.load(j); var R = {};
  /* ① 해석 계산 대 몬테카를로 — 2%p 안 */
  R.mc = [[300,40,280,60],[300,40,300,40],[200,30,260,50],[500,80,420,30],[120,20,180,90]].map(function(c){ return [Math.round(S.pWin(c[0],c[1],c[2],c[3])*1000)/1000, Math.round(S.mc(c[0],c[1],c[2],c[3],40000,7)*1000)/1000]; });
  /* ② 진행 방향 — 방배(2호선)에서 서초 쪽 */
  var bb = S.find('방배','2호선'), sc = S.find('서초','2호선'), P = S.path(bb, sc, 4); R.path = P.map(function(p){ return [j.st[p.i][1], p.sec]; });
  /* ③ 혼잡 — 몫을 바꿔 가며(같은 역) · 상·하한 */
  var gn = S.find('강남','2호선'), r0 = j.st[gn][5].slice(); function setR(v){ j.st[gn][5] = r0.map(function(){ return v; }); }
  setR(1); var c1 = S.crowd(gn, 8); setR(2.2); var c2 = S.crowd(gn, 8); setR(9); var c9 = S.crowd(gn, 8); setR(0.05); var c0 = S.crowd(gn, 8);
  R.crowd = [c1.walkF, c1.dwellF, c2.walkF > c1.walkF, c2.dwellF > c1.dwellF, c9.walkF, c9.dwellF, c0.walkF, c0.dwellF, c2.warn, c1.warn];
  /* ④ 혼잡이 커지면 경찰이 늦고(도보) 열차도 늦다(사이 역 정차) — 출퇴근처럼 노선 전체가 붐빌 때 · 둘을 같이 넣은 확률 > 도보만 늘린 확률 */
  var o = { i: bb, nx: sc, st: 'dep', ago: 0 }, P6 = S.path(bb, sc, 6), keep = P6.map(function(p){ return j.st[p.i][5]; }).concat([j.st[bb][5]]);
  function setAll(v){ P6.forEach(function(p){ j.st[p.i][5] = v == null ? keep[P6.indexOf(p)] : keep[0].map(function(){ return v; }); }); }
  var gi = S.find('강남','2호선'), dr = {}; setAll(1); var T1x = S.train(o, 8).filter(function(t){ return t.i === gi; })[0]; dr[gi] = { sec: T1x.T - 150, sd: 25 };
  var A1 = S.plan(o, dr, 8).cards.filter(function(c){ return c.i === gi; })[0]; setAll(2.2); var A2 = S.plan(o, dr, 8).cards.filter(function(c){ return c.i === gi; })[0]; setAll(null);
  var wOnly = S.pWin(A1.T, A1.sdT, A2.P, A2.sdP);
  R.both = [Math.round(A1.P), Math.round(A2.P), Math.round(A1.T), Math.round(A2.T), Math.round(A2.p*1000)/1000, Math.round(wOnly*1000)/1000];
  /* 사이 역 혼잡은 뒤 역 열차 도착을 늦춘다 */
  var o2 = { i: bb, nx: sc, st: 'dep', ago: 0 }, T1 = S.train(o2, 8), sv = j.st[sc][5].slice(); j.st[sc][5] = sv.map(function(){ return 2.5; }); var T2 = S.train(o2, 8); j.st[sc][5] = sv;
  R.mid = [Math.round(T1[0].T), Math.round(T2[0].T), Math.round(T1[1].T), Math.round(T2[1].T)];
  /* ⑤ 권고 규칙 — 기준(80%) 넘는 가장 가까운 역 · 없으면 가장 높은 역 「경합」 */
  var o2b = { i: bb, nx: sc, st: 'dep', ago: 0 }, ds = {}, dsec = [400, 60, 30, 30, 30, 30]; P6.forEach(function(p, k){ ds[p.i] = { sec: dsec[k], sd: 20 }; }); var pl = S.plan(o2b, ds, 14);
  var firstOk = pl.cards.filter(function(c){ return c.p >= 0.8; })[0]; R.rec = [!!firstOk && pl.best === firstOk.i && firstOk.k > 1, pl.close, pl.cards.map(function(c){ return [c.nm, Math.round(c.p*100), Math.round(c.slack), c.late]; })];
  var ds2 = {}; P6.forEach(function(p){ ds2[p.i] = { sec: 3000, sd: 30 }; }); var pl2 = S.plan(o2b, ds2, 14); var mx = pl2.cards.slice().sort(function(a,b){ return b.p - a.p; })[0];
  R.close = [pl2.close, pl2.best === mx.i, pl2.cards.length === 6 && pl2.cards.every(function(c){ return c.late; })];
  /* ⑥ 실측 3번 넘게 → 가정값 아님 · 2번이면 가정값 */
  var M3 = { rec: [{ st: '서초', ln: '2호선', kind: 'walk', exit: '4', t: [[50,14,'wd','x'],[60,14,'wd','x'],[55,14,'wd','x']] }] }, M2 = { rec: [{ st: '서초', ln: '2호선', kind: 'walk', exit: '4', t: [[50,14,'wd','x'],[60,14,'wd','x']] }] };
  var p3 = S.police(sc, { sec: 100, sd: 10 }, 14, M3), p2 = S.police(sc, { sec: 100, sd: 10 }, 14, M2); R.meas = [p3.walk.assumed, Math.round(p3.walk.sec), p3.walk.n, p2.walk.assumed];
  /* ⑦ 모름(몇 초 전인지 모름)이면 열차 오차가 커진다 · 도착(정차 중)이면 출발보다 늦게 닿는다 */
  var Tu = S.train({ i: bb, nx: sc, st: 'dep', ago: null }, 14), Tk = S.train({ i: bb, nx: sc, st: 'dep', ago: 0 }, 14), Ta = S.train({ i: bb, nx: sc, st: 'arr', ago: 0 }, 14);
  R.obs = [Math.round(Tu[0].sd), Math.round(Tk[0].sd), Math.round(Ta[0].T - Tk[0].T)];
  /* ⑧ 보정 — 실측 ÷ 예상 가운데 · 짧은 것·말 안 되는 비율 버림 · 0.7~1.5 */
  R.cal = [S.calibrate([[300,330],[600,660],[400,440],[20,100],[300,1500]]), S.calibrate([[300,600],[300,600],[300,600]])];
  /* ⑨ 행사 가산 — 그 날·그 역·그 시간만 */
  var e = [{ st: '강남', date: '2026-10-20', h0: 18, h1: 21, add: 1.5 }]; R.ev = [S.crowd(gn, 19, e, '2026-10-20').r - S.crowd(gn, 19, [], '2026-10-20').r, S.crowd(gn, 19, e, '2026-10-21').ev, S.crowd(gn, 22, e, '2026-10-20').ev];
  return JSON.stringify(R); })()'''
C = []
def ck(n, ok, got=''): C.append((n, bool(ok), str(got)[:220]))
c = Chrome()
try:
    open(os.path.join(ROOT, 'tools', 'check', '__sr.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><script src="/js/station-reach.js"></script>')
    c.go('http://127.0.0.1:%d/tools/check/__sr.html' % port, 1.0)
    R = json.loads(c.ev(JS))
finally:
    c.close(); srv.shutdown()
    try: os.remove(os.path.join(ROOT, 'tools', 'check', '__sr.html'))
    except OSError: pass
ck('① 해석 계산과 몬테카를로 차이 2%p 안(다섯 경우)', all(abs(a - b) <= 0.02 for a, b in R['mc']), R['mc'])
ck('② 방배(2호선) → 서초 쪽 = 서초 · 교대 · 강남 · 역삼 · 시간이 늘어난다', [p[0] for p in R['path']] == ['서초', '교대(법원.검찰청)', '강남', '역삼'] and all(R['path'][k][1] < R['path'][k + 1][1] for k in range(3)), R['path'])
X = R['crowd']; ck('③ 혼잡 배수 — 몫 1 = 도보·정차 ×1 · 몫이 크면 둘 다 늘고 · 상한 도보 1.8·정차 2 · 하한 도보 0.9·정차 1 · 붐비면 경고', X[0] == 1 and X[1] == 1 and X[2] and X[3] and X[4] == 1.8 and X[5] == 2 and X[6] == 0.9 and X[7] == 1 and X[8] and not X[9], X)
B = R['both']; ck('④ 혼잡이 커지면 경찰 도착이 늦어지고(도보) 열차 도착도 늦어진다(정차) — 같이 넣은 확률 > 도보만 늘린 확률', B[1] > B[0] and B[3] > B[2] and B[4] > B[5], B)
M = R['mid']; ck('④′ 사이 역(서초)이 붐비면 뒤 역(교대) 열차 도착이 늦어진다 · 그 역 도착은 그대로', M[0] == M[1] and M[3] > M[2], M)
ck('⑤ 권고 — 기준 80% 넘는 가장 가까운 역', R['rec'][0] and not R['rec'][1], R['rec'][2])
ck('⑤′ 넘는 역이 없으면 가장 높은 역을 「경합」 · 모두 「이미 늦음」', R['close'] == [True, True, True], R['close'])
ck('⑥ 실측 3번 → 가정값 아님(55초 · 3번) · 2번 → 가정값', R['meas'] == [False, 55, 3, True], R['meas'])
ck('⑦ 몇 초 전인지 모르면 열차 오차가 커지고 · 「정차 중」은 「출발」보다 정차만큼 늦게 닿는다', R['obs'][0] > R['obs'][1] + 30 and R['obs'][2] == 30, R['obs'])
K = R['cal']; ck('⑧ 보정 — 가운데 1.1 · 짧은 것·엉뚱한 비율 버림 · 5번 아래는 가정값 · 위 끝 1.5', abs(K[0]['k'] - 1.1) < 1e-9 and K[0]['n'] == 3 and K[0]['assumed'] and K[1]['k'] == 1.5, K)
E = R['ev']; ck('⑨ 행사 가산 — 그 날·그 역·그 시간에만 +1.5', abs(E[0] - 1.5) < 0.01 and E[1] == 0 and E[2] == 0, E)
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got))
print(('✅ 선착 역 모듈 시험 통과 %d/%d' if n == len(C) else '❌ 선착 역 모듈 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
