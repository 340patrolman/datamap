# -*- coding: utf-8 -*-
"""서비스 워커(sw.js) 먹통 검사 — 저장소를 내주는 서버가 「좋음·느림·먹통·끊김」을 흉내 내고, 머리 없는 크롬으로 가르고를 다시 열어 길이 나올 때까지를 잰다.

    py -3.12 -X utf8 tools/check/swcheck.py            # 저장소의 sw.js · 실패하면 끝 코드 1
    py -3.12 -X utf8 tools/check/swcheck.py --old <파일>  # 그 파일을 /sw.js 로 내줌(앞뒤 비교 · 판정 안 함)

보는 것(2026-11-11 신호 세션 · 형님 「권고대로 계속 진행」 — 통신 끊긴 곳에서 다시 열기):
  ① 먹통(이어지기만 하고 답이 안 옴)·아주 느림(요청마다 6초)·끊김에서도 보관본으로 열린다(길이 LIMIT 초 안)
  ② 늦어서 보관본으로 답한 파일도 뒤에서 받아 보관함이 새것이 된다(다음에 열 때 새 값)
  ③ 망이 좋으면 늘 새 값(망 먼저)
  ⑤ 보관본으로 답한 판 표시 주소에 늦게 온 응답(다른 판 내용)을 넣지 않는다(둘째 검수 — 문서와 스크립트 판이 보관함 안에서 어긋남)
  ④ 판 표시(?v=)가 붙은 주소는 늦었다고 다른 판 내용으로 답하지 않는다 · 같은 판 보관본은 그 판 내용으로(독립 검수 지적 — 물음표 뒤를 떼고 찾으면 가장 먼저 넣은 옛 판이 나온다)
화면 쪽 통신 흉내(Network.emulateNetworkConditions)는 워커가 받는 요청에 안 먹는다 — 그래서 서버가 흉내 낸다. sw.js 는 실제 사이트에서 https 일 때만 등록되므로 여기서는 손으로 등록한다(127.0.0.1 은 안전한 출처).
"""
import sys, os, time, json, socket, threading, functools, http.server
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Chrome
OLD = sys.argv[sys.argv.index('--old') + 1] if '--old' in sys.argv else None
LIMIT = 15.0
MODE = {'m': 'pass', 'lat': 0.0, 'mark': 1, 'ver': 1}; HUNG = []; LK = threading.Lock(); BUSY = [0]
MARK = '/data/__swcheck.json'; VERF = '/data/__swver.json'


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _raw(self, b, ct):
        self.send_response(200); self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(b))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        with LK:
            BUSY[0] += 1
        try:
            self._get()
        finally:
            with LK:
                BUSY[0] -= 1

    def _get(self):
        m = dict(MODE)
        if m['m'] == 'refuse':
            try:
                self.connection.close()
            except Exception:
                pass
            return
        if m['m'] == 'stall':
            with LK:
                HUNG.append(self.connection)
            time.sleep(900); return
        if m['lat']:
            time.sleep(m['lat'])
        p = self.path.split('?')[0]
        if p == MARK:
            return self._raw(json.dumps({'v': m['mark']}).encode(), 'application/json')
        if p == VERF:   # 판 표시(?v=)가 붙는 파일 흉내 — 실제 사이트처럼 물음표 뒤와 상관없이 지금 내용을 준다
            return self._raw(json.dumps({'v': m['ver']}).encode(), 'application/json')
        if OLD and p == '/sw.js':
            return self._raw(open(OLD, 'rb').read(), 'application/javascript')
        return super().do_GET()


def mode(m, lat=0.0, mark=None, ver=None):
    MODE.update(m=m, lat=lat)
    if mark:
        MODE['mark'] = mark
    if ver:
        MODE['ver'] = ver
    with LK:
        for s in HUNG:
            try:
                s.shutdown(socket.SHUT_RDWR); s.close()
            except Exception:
                pass
        del HUNG[:]
    time.sleep(0.8)


def idle(limit=150):
    """서버가 받고 있는 요청이 없어질 때까지 기다린다(느린 조건에서 뒤에서 받는 것이 끝나야 보관함이 새것이 된다)."""
    t0 = time.time(); q = 0
    while time.time() - t0 < limit:
        time.sleep(0.5); q = q + 1 if BUSY[0] == 0 else 0
        if q >= 4:
            return time.time() - t0
    return -1


def main():
    s0 = socket.socket(); s0.bind(('127.0.0.1', 0)); port = s0.getsockname()[1]; s0.close()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=ROOT)); srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    U = 'http://127.0.0.1:%d/gargo/' % port; HS = '#from=37.4919,127.0076&to=37.4844,127.0341&nm=check'
    c = Chrome(width=500, height=900); n = [10]; res = []

    def reopen(limit):
        try:
            o = c.ev("performance.timeOrigin")
        except Exception:
            o = 0
        n[0] += 1; t0 = time.time(); doc = None
        try:
            c.go(U + 'index.html?a=%d' % n[0] + HS, 0.3)
        except Exception:
            return None, '새 문서가 안 뜸(탐색이 60초 넘게 안 끝남)'
        while time.time() - t0 < limit:
            time.sleep(0.25)
            try:
                a = json.loads(c.ev("JSON.stringify([performance.timeOrigin, !!(window.GARGO && GARGO.state().route), location.href.slice(0, 16)])"))
            except Exception:
                continue
            if a[0] != o and a[2].startswith('http://127'):
                if doc is None:
                    doc = time.time() - t0
                if a[1]:
                    return time.time() - t0, '새 문서 %.1f초 · 길 %.1f초' % (doc, time.time() - t0)
        return None, ('새 문서 %.1f초 · 길은 %d초 안에 안 나옴' % (doc, limit)) if doc is not None else '%d초 안에 새 문서가 안 뜸' % limit

    def mark(limit=40, url="'../data/__swcheck.json?t=' + Date.now()"):
        t0 = time.time()
        try:
            v = c.ev("Promise.race([fetch(" + url + ").then(function (r) { return r.json(); }).then(function (j) { return j.v; }).catch(function () { return -1; }), new Promise(function (ok) { setTimeout(function () { ok(-2); }, %d); })])" % (limit * 1000))
        except Exception:
            v = -3
        return v, time.time() - t0

    def ck(nm, ok, det):
        res.append(ok); print(('  ✅ ' if ok else '  ❌ ') + nm + ' — ' + det, flush=True)

    try:
        print('서비스 워커 먹통 검사 — ' + ('옛 워커 ' + os.path.basename(OLD) + '(비교 · 판정 안 함)' if OLD else '저장소의 sw.js'), flush=True)
        c.go(U + 'index.html', 3.0); c.ev("localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1')")
        st = c.ev("navigator.serviceWorker.register('../sw.js').then(function(){return navigator.serviceWorker.ready}).then(function(r){return r.active ? 'ok' : 'none'}).catch(function(e){return 'ERR '+e.message})")
        time.sleep(3); reopen(120); time.sleep(10); t, d = reopen(60); time.sleep(6)
        ck('워커가 화면을 잡고 통신 좋을 때 길이 나온다', st == 'ok' and t is not None and c.ev("!!navigator.serviceWorker.controller") is True, st + ' · ' + d)
        v, s = mark(); ck('좋음 — 표시 파일 값 1(망 먼저)', v == 1, '값 %s · %.1f초' % (v, s))
        V = lambda n, lim=40: mark(lim, "'../data/__swver.json?v=%d'" % n)
        a1 = V(1)[0]; mode('pass', 0.0, ver=2); a2 = V(2)[0]; ck('판 표시 파일 — ?v=1 때 내용 1 · 내용이 2 로 바뀐 뒤 ?v=2 는 2(둘 다 보관됨)', a1 == 1 and a2 == 2, '%s · %s' % (a1, a2))
        mode('pass', 1.0); t, d = reopen(60); ck('느림(요청마다 1초) — 열린다', t is not None and t < LIMIT, d)
        mode('pass', 6.0, mark=2, ver=3); t, d = reopen(90); ck('아주 느림(요청마다 6초) — %d초 안에 길' % LIMIT, t is not None and t < LIMIT, d)
        v, s = mark(); ck('아주 느림 — 표시 파일은 보관본(값 1)으로 6초보다 빨리 답', v == 1 and s < 5.5, '값 %s · %.1f초' % (v, s))
        v, s = V(2, 12); ck('아주 느림 — ?v=2 는 보관본(2)으로 6초보다 빨리 답(서버 내용은 3 으로 바뀐 뒤)', v == 2 and s < 5.5, '값 %s · %.1f초' % (v, s))
        w = idle(); print('    (뒤에서 받기 끝남을 기다림 %.0f초)' % w, flush=True); mode('stall'); t, d = reopen(60); ck('먹통(답이 안 옴) — %d초 안에 길' % LIMIT, t is not None and t < LIMIT, d)
        v, s = mark(); ck('먹통 — 뒤에서 받아 둔 새 값(2)이 보관함에서 나온다(늦어도 버리지 않고 갱신)', v == 2 and s < 5.5, '값 %s · %.1f초' % (v, s))
        v, s = V(2, 12); ck('먹통 — ?v=2 는 그 판 내용(2)으로 답한다(물음표 뒤를 떼고 찾으면 옛 1 이 나오던 것 · 보관본으로 답한 뒤 늦게 온 다른 판 내용 3 을 그 열쇠에 넣지 않는다)', v == 2 and s < 5.5, '값 %s · %.1f초' % (v, s))
        v, s = V(3, 9); ck('먹통 — 보관한 적 없는 새 판 주소(?v=3)는 다른 판 내용으로 답하지 않는다(망을 기다림)', v == -2, '값 %s(-2 = 9초 동안 답 없음) · %.1f초' % (v, s))
        mode('refuse'); t, d = reopen(40); ck('끊김(바로 실패) — 열린다', t is not None and t < LIMIT, d)
        v, s = V(3, 9); ck('끊김 — 받기가 실패하면 새 판 주소(?v=3)도 보관본 중 가장 나중 것(2)으로 답한다', v == 2, '값 %s · %.1f초' % (v, s))
        mode('pass', 0.0, mark=3); time.sleep(3); t, d = reopen(40); v, s = mark(); ck('다시 좋음 — 열리고 표시 파일은 새 값 3(망 먼저)', t is not None and v == 3, d + ' · 값 %s · %.1f초' % (v, s))
    finally:
        c.close(); srv.shutdown()
    if OLD:
        print('비교용 — 판정하지 않는다'); return 0
    bad = res.count(False)
    print('✅ 워커 먹통 검사 통과' if not bad else '❌ 워커 먹통 검사 실패 %d건 — 커밋하지 않는다' % bad)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
