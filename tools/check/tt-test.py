# -*- coding: utf-8 -*-
"""주행시간 계산 모듈(js/travel-time.js) 단위 시험 — 작업지시서 v1.0 1장 기준값 + 규칙.
  머리 없는 크롬에서 모듈을 그대로 돌린다(Node 없음). 정답은 이 파일이 손으로 센 값.
  쓰기: py -3.12 -X utf8 tools/check/tt-test.py   (끝 코드 1 = 실패)
"""
import json, os, sys, time, socket, threading, http.server, functools
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from cdp import Chrome
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
JS = r'''(function(){ localStorage.removeItem('tg_tt_cfg'); localStorage.removeItem('tg_tt_cal'); var R={}, T=window.TT, seg=[{m:10000}];
  [60,70,90,100].forEach(function(v){ R['v'+v]=T.fmt(T.run(seg,{v:v,pure:true}).sec); });
  var C=T.cfg(); R.def=C;
  /* 신호 무시해도 감속은 유지 — 회전 2 · 진출입 1 · 터널 1km · 신호 기다림 40초(서는 곳) */
  var S=[{m:3000,turn:1,sig:40,stop:1,cp:'가'},{m:1000,tunnel:1},{m:2000,ramp:1,turn:1,cp:'나'}];
  var on=T.run(S,{v:60,cal:false}), off=T.run(S,{v:60,sig:false,cal:false});
  R.on=on.sec; R.off=off.sec; R.cps=off.cps.map(function(c){return [c.nm,Math.round(c.t*10)/10]});
  R.need=Math.round(T.need(10000,600+2*C.accS)*10)/10;
  /* 중요업무 두 줄 — 직접 입력 없음(100 기준) · 80 입력 · 범위 밖 130 · 29 */
  var a=T.vipTwo(seg,{}), b=T.vipTwo(seg,{fast:80}), c=T.vipTwo(seg,{fast:130}), d=T.vipTwo(seg,{fast:29});
  R.vip=[a.base.v, a.fast.v, a.fastV, a.typed, b.fastV, b.typed, !!c.err, !!d.err, Math.round(a.base.sec), Math.round(a.fast.sec)];
  /* 설정 — 범위 밖 거부 · 저장 · 항목 되돌리기 · 전체 되돌리기 */
  R.set=[T.set('fwd',3000), T.set('fwd',99999), T.cfg().fwd, (T.reset('fwd'), T.cfg().fwd), T.set('sz',2.5), (T.reset(), T.cfg().sz)];
  /* 보정 — 실측이 계산보다 10% 길면 다음 계산 ×1.1 · 짧은 주행은 안 쌓음 */
  R.cal=[T.calAdd(100,90), T.calAdd(660,600), Math.round(T.calK()*1000)/1000, Math.round(T.run(seg,{v:60}).sec), (T.calReset(), T.calK())];
  R.keys=Object.keys(localStorage).filter(function(k){return /^tg_tt/.test(k)});
  return JSON.stringify(R); })()'''
C = []
def ck(n, ok, got=''): C.append((n, bool(ok), str(got)[:200]))
c = Chrome()
try:
    open(os.path.join(ROOT, 'tools', 'check', '__tt.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><script src="/js/travel-time.js"></script>')
    c.go('http://127.0.0.1:%d/tools/check/__tt.html' % port, 1.0)
    R = json.loads(c.ev(JS))
finally:
    c.close(); srv.shutdown()
    try: os.remove(os.path.join(ROOT, 'tools', 'check', '__tt.html'))
    except OSError: pass
for v, want in ((60, '10분 00초'), (70, '8분 34초'), (90, '6분 40초'), (100, '6분 00초')):
    ck('기준값 10km / %dkm/h = %s' % (v, want), R['v%d' % v] == want, R['v%d' % v])
D = R['def']; ck('기본값 — 전방 2,000m · 후방 1,000m · 남은 초 2배 · 중요업무 60 · 가장 이른 100 · 허용 30~120', (D['fwd'], D['back'], D['sz'], D['vipV'], D['vipFast'], D['vMin'], D['vMax']) == (2000, 1000, 2, 60, 100, 30, 120), D)
acc, turn, ramp, tk = D['accS'], D['turnS'], D['rampS'], D['tunK']
mv = 3000 / (60 / 3.6) + 1000 / (60 * tk / 3.6) + 2000 / (60 / 3.6)
want_off = mv + 2 * turn + ramp + 2 * acc; want_on = want_off + 40 + acc
ck('신호 무시 = 신호 기다림(과 신호 가감속)만 0 · 회전·진출입·터널 감속은 그대로', abs(R['off'] - want_off) < 0.01 and abs(R['on'] - want_on) < 0.01, '%.2f / %.2f (정답 %.2f / %.2f)' % (R['off'], R['on'], want_off, want_on))
cp1 = acc + 3000 / (60 / 3.6) + turn
ck('체크포인트별 통과 예정(출발 기준 초)', abs(R['cps'][0][1] - cp1) < 0.1 and R['cps'][1][0] == '나' and abs(R['cps'][1][1] - (want_off - acc)) < 0.1, R['cps'])
ck('역산 — 10km 를 10분(+가감속) 안에 = 평균 60km/h', R['need'] == 60.0, R['need'])
V = R['vip']; ck('중요업무 두 줄 — 입력 없으면 가장 이른 = 100km/h · 80 입력이면 80 · 130·29 는 거부', V[:8] == [60, 100, 100, False, 80, True, True, True], V)
ck('중요업무 — 10km 예상(60) 10분 08초 · 가장 이른(100) 6분 08초(가감속 포함)', V[8] == 600 + 2 * acc and V[9] == 360 + 2 * acc, V[8:])
S = R['set']; ck('설정 — 범위 밖 거부 · 저장 · 항목 되돌리기 · 전체 되돌리기', S == [True, False, 3000, 2000, True, 2], S)
L = R['cal']; ck('보정 — 짧은 주행 안 쌓음 · 실측 ÷ 계산 1.1 을 다음 계산에 곱함', L[0] is False and L[1] is True and L[2] == 1.1 and L[3] == round((600 + 2 * acc) * 1.1) and L[4] == 1, L)
ck('이 기기에 남는 것은 설정·보정 숫자 열쇠 둘뿐', set(R['keys']) <= {'tg_tt_cfg', 'tg_tt_cal'}, R['keys'])
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got if got and not ok else ''))
print(('✅ 주행시간 모듈 시험 통과 %d/%d' if n == len(C) else '❌ 주행시간 모듈 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
