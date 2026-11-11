# -*- coding: utf-8 -*-
"""가르고 길 흔들림 재생 — 지난 소통 기록(07_API키/out/livespd/날짜.jsonl.gz)을 차례로 넣어 같은 짝의 길이 몇 번 바뀌는지 센다

까닭(2026-11-12 신호 세션): NEXT.md 「가르고 — 퇴근 시간 길 흔들림」 — 11분마다 오는 소통 값에 따라 비슷한 두 길을 오간다.
route-bench.py 는 그 시각 실측(카카오 대조)이라 17~19시에만 잴 수 있다 → 이것은 기록을 다시 흘려 아무 때나 같은 조건으로 잰다.
카카오를 부르지 않는다 · 소통 기록은 읽기만 · 화면에 비율·횟수만 찍는다.

  py -3.12 -X utf8 tools/signal/route-flip.py [--day 20261111] [--from 17:00] [--to 19:30] [--seoul] [역 이름 …]

셈: 짝마다 소통 한 장씩 길을 다시 고르고(그 장을 받은 시각 · 신호 계획도 그 시각), 앞 장 길과 겹친 길이 ÷ 둘 중 긴 길 < 0.7 이면 「바뀜」.
  바뀜 = 앞 장과 다른 길로 넘어간 횟수 · 갈래 = 서로 90% 넘게 겹치지 않는 길 가짓수 · 돔 = 소통 뺀 길보다 1.3배 넘게 긴 장 수
대조: --fix-t = 시각을 첫 장에 묶음(소통만 바뀜) · --fix-live = 소통을 첫 장에 묶음(신호 시각만 바뀜)
여섯 구 묶음 = gargo/ 기본 · --seoul = ?pk=seoul(골목 칸 전부 받음 · 느림)
"""
import sys, os, json, gzip, time, socket, threading, functools, http.server, importlib.util, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = importlib.util.spec_from_file_location('rb', os.path.join(ROOT, 'tools', 'signal', 'route-bench.py')); RB = importlib.util.module_from_spec(sp)
sys.argv, _a = sys.argv[:1], sys.argv
sp.loader.exec_module(RB)
sys.argv = _a
RS, ST, PAIRS = RB.RS, RB.ST, RB.PAIRS
KST = dt.timezone(dt.timedelta(hours=9))


def opt(k, d):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv and sys.argv.index(k) + 1 < len(sys.argv) else d


def main():
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__); return 0
    day, f0, f1 = opt('--day', (dt.datetime.now(KST) - dt.timedelta(days=1)).strftime('%Y%m%d')), opt('--from', '17:00'), opt('--to', '19:30')
    skip = {opt('--day', ''), opt('--from', ''), opt('--to', '')}
    ARG = [a for a in sys.argv[1:] if not a.startswith('-') and a not in skip]
    pk = '?pk=seoul' if '--seoul' in sys.argv else ''
    fn = os.path.join(RS.RAW, 'out', 'livespd', day + '.jsonl.gz')
    if not os.path.exists(fn):
        print('소통 기록 없음', fn); return 1
    hm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    snaps = []
    with gzip.open(fn, 'rt', encoding='utf-8') as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            j = json.loads(ln); t = dt.datetime.fromtimestamp(j['at'], KST)
            if hm(f0) <= t.hour * 60 + t.minute <= hm(f1) and j.get('m'):
                snaps.append(j)
    if len(snaps) < 2:
        print('그 시간 소통 기록이 두 장 아래', len(snaps)); return 1
    pairs = [p for p in PAIRS if not ARG or any(x in p for x in ARG)]
    CUR = {'j': None, 'n': 0}

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path.split('?')[0].endswith('/data/live-spd-six.json') and CUR['j'] is not None:
                b = json.dumps(dict(CUR['j'], at=int(time.time()), made='재생 ' + CUR['j']['made'])).encode('utf-8')
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)
                CUR['n'] += 1; return
            return super().do_GET()
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    for j in snaps:
        j['made'] = dt.datetime.fromtimestamp(j['at'], KST).strftime('%H:%M')
    CUR['j'] = snaps[0]
    c = RS.Chrome(width=412, height=915)
    try:
        # 5분마다 소통을 다시 받는 타이머를 붙잡아 둔다 — 재생은 이것을 불러 다음 장을 넣는다(가르고 코드는 안 건드림)
        c.cmd('Page.addScriptToEvaluateOnNewDocument', source="(function(){var si=window.setInterval;window.setInterval=function(f,ms){if(ms===300000)window.__T5=f;return si.apply(this,arguments);};})();")
        B = 'http://127.0.0.1:%d/gargo/' % port
        c.go(B + 'index.html', 1.0); c.ev("localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1')")
        c.go(B + 'index.html' + (pk + '&rs=1' if pk else '?rs=1'), 1.0)
        for _ in range(120):
            time.sleep(1)
            if c.ev("!!(window.GARGO && GARGO.state().G && GARGO.state().G.S.length && window.__T5)"):
                break
        time.sleep(5); c.ev("GARGO.pkAll && GARGO.pkAll() && 1")
        for _ in range(120):
            time.sleep(1)
            if c.ev("(function(){var p=GARGO.pk(); return !p.on || p.tiles===p.total;})()"):
                break
        time.sleep(8)
        if not c.ev("!!window.__T5"):
            print('5분 타이머를 못 잡음 — 가르고 갱신 방식이 바뀐 듯'); return 1
        R = {p: [] for p in pairs}
        for k, j in enumerate(snaps):
            if k and '--fix-live' not in sys.argv:
                CUR['j'] = j; n0 = CUR['n']; c.ev("window.__T5() || 1")
                for _ in range(60):
                    time.sleep(0.5)
                    if CUR['n'] > n0:
                        break
                time.sleep(3)
            for a, b in pairs:
                A, Bn = ST[a], ST[b]
                js = ("(function(){var g=GARGO,G=g.state().G,s=g.P(%f,%f),t=g.P(%f,%f),now=%d,r=g.findRoute(s[0],s[1],t[0],t[1],now,null); if(!r) return null;"
                      "var n=g.noLive(function(){return g.findRoute(s[0],s[1],t[0],t[1],now,null);})||r, m={}; r.es.forEach(function(e){var i=G.eS[e]; m[i]=(m[i]||0)+G.S[i][2];});"
                      "return JSON.stringify({d:r.dist,t:r.time,nd:n.dist,m:m});})()") % (A[0], A[1], Bn[0], Bn[1], snaps[0]['at'] if '--fix-t' in sys.argv else j['at'])
                rj = c.ev(js)
                R[(a, b)].append(json.loads(rj) if rj else None)
            print('  %s 장 %d/%d' % (j['made'], k + 1, len(snaps)), flush=True)
    finally:
        c.close(); srv.shutdown()

    def ov(x, y):
        sh = sum(min(v, y['m'].get(k, 0)) for k, v in x['m'].items())
        return sh / max(1, max(x['d'], y['d']))
    print('가르고 길 흔들림 재생 · %s %s~%s 소통 %d장 · %s%s' % (day, snaps[0]['made'], snaps[-1]['made'], len(snaps), '서울 묶음' if pk else '여섯 구', ''.join(' · ' + x for x in ('--fix-t', '--fix-live') if x in sys.argv)))
    print('%-18s %4s %4s %4s %6s %6s' % ('짝', '바뀜', '갈래', '돔', '시간폭', '거리폭'))
    tf = tg = td = moved = 0
    for p in pairs:
        L = [x for x in R[p] if x]
        if len(L) < 2:
            print('%-18s 길 없음' % ('→'.join(p))); continue
        fl = sum(1 for i in range(1, len(L)) if ov(L[i - 1], L[i]) < 0.7)
        kinds = []
        for x in L:
            if not any(ov(x, y) >= 0.9 for y in kinds):
                kinds.append(x)
        dt_ = sum(1 for x in L if x['d'] > 1.3 * max(1, x['nd']))
        ts, ds = [x['t'] for x in L], [x['d'] for x in L]
        tf += fl; tg += len(kinds); td += dt_; moved += 1 if fl else 0
        print('%-18s %4d %4d %4d %5.2f배 %5.2f배%s' % ('→'.join(p), fl, len(kinds), dt_, max(ts) / max(1, min(ts)), max(ds) / max(1, min(ds)), '  ⚠' if fl >= 2 else ''))
    print('짝 %d · 길이 한 번이라도 바뀐 짝 %d · 바뀜 합 %d · 갈래 합 %d · 1.3배 넘게 돈 장 합 %d' % (len(pairs), moved, tf, tg, td))
    return 0


if __name__ == '__main__':
    sys.exit(main())
