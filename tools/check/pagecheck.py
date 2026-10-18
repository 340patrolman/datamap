# -*- coding: utf-8 -*-
"""값 검사 관문 — 커밋 전에 돌린다(2026-10-13 소유자 승인 「검증 분리 · 근거 강제」).

    py -3.12 -X utf8 tools/check/pagecheck.py            가르고 + 지도
    py -3.12 -X utf8 tools/check/pagecheck.py gargo      가르고만
    py -3.12 -X utf8 tools/check/pagecheck.py map        지도만

하는 일: 이 폴더를 잠깐 서버로 띄우고 → 머리 없는 크롬으로 화면을 실제로 열어 →
화면 안에서 검사 스크립트(tools/check/<이름>-check.js)가 값을 재고 → 결과를 이 서버로 돌려보낸다.
하나라도 틀리면 끝 코드 1(뒤에 && git commit 을 붙이면 커밋이 안 나간다). 파이프로 넘기지 않는다.

「문법이 통과한다 · 화면이 열린다」만이 아니라 「정답을 아는 값이 그대로 나온다」를 본다.
규칙 문장(제한속도를 넘는 값은 안 낸다 · 밤 22~06시 속도 안내 없음)이 코드에 그대로 있는지도 본다.
"""
import sys, os, json, time, base64, threading, subprocess, tempfile, shutil, functools, urllib.parse, http.server

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
          r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']
PRE = ("<script>try{localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1');}catch(e){}"
       "window.__ERR=[];window.addEventListener('error',function(e){__ERR.push(String(e.message)+' @'+String(e.filename||'').split('/').pop()+':'+e.lineno);});"
       "window.addEventListener('unhandledrejection',function(e){__ERR.push('rej '+String(e.reason&&e.reason.message||e.reason));});</script>")
PAGES = {
    'gargo': {'src': 'gargo/index.html', 'url': '/gargo/__check.html#from=37.4919,127.0076&to=37.4844,127.0341&nm=check', 'js': '/tools/check/gargo-check.js', 'wait': 90},
    'meas': {'src': 'gargo/measure.html', 'url': '/gargo/__mcheck.html', 'js': '/tools/check/measure-check.js', 'wait': 40},
    'map': {'src': 'index.html', 'url': '/__check.html#lat=37.4919&lon=127.0076', 'js': '/tools/check/map-check.js', 'wait': 90},
}
PARTS, DONE = {}, {}


class H(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        if u.path == '/__r':
            q = dict(urllib.parse.parse_qsl(u.query, keep_blank_values=True))
            k, i, n = q.get('k', ''), int(q.get('i', 0)), int(q.get('n', 1))
            PARTS.setdefault(k, {})[i] = q.get('d', '')
            if len(PARTS[k]) == n:
                raw = ''.join(PARTS[k][j] for j in range(n))
                raw += '=' * (-len(raw) % 4)
                try:
                    DONE[q.get('p', '')] = json.loads(base64.urlsafe_b64decode(raw).decode('utf-8'))
                except Exception as e:
                    DONE[q.get('p', '')] = {'checks': [['결과 읽기', False, str(e)]]}
            return self._send(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', 'image/gif')
        for name, pg in PAGES.items():
            if u.path == pg['url'].split('#')[0]:
                s = open(os.path.join(ROOT, pg['src']), encoding='utf-8', newline='').read()
                i = s.index('<head>') + len('<head>')
                s = s[:i] + PRE + s[i:]
                j = s.rindex('</body>')
                s = s[:j] + '<script>window.__PAGE=' + json.dumps(name) + ';</script><script src="' + pg['js'] + '"></script>' + s[j:]
                return self._send(s.encode('utf-8'), 'text/html; charset=utf-8')
        return super().do_GET()


def static_rules():
    """규칙이 코드에 그대로 있는가 — 문장이 사라지면 값 검사보다 먼저 걸린다."""
    out = []
    g = open(os.path.join(ROOT, 'gargo', 'gargo.js'), encoding='utf-8').read()
    def has(name, needle, n=1):
        c = g.count(needle)
        out.append([name, c == n, '%d곳(바라는 수 %d)' % (c, n)])
    has('가르고 규칙 · 속도 권고는 제한속도에서 아래로만 찾는다', 'for (var v = ns.lim; v >= 20; v -= 5)')
    has('가르고 규칙 · 밤 22~06시에는 속도 권고를 안 낸다', "if (!NOSIG() && !(dest && dest.vip) && !night() && dd > 80 && !cg9)")   # v0.31.0 통과 가능 속도 줄(녹색·적색 모두) — 밤·긴급·중요업무에는 없음
    has('가르고 규칙 · 밤 판정 22시·6시', 'return h >= 22 || h < 6;')
    has('가르고 규칙 · 길 계산 속도는 제한속도를 넘지 않는다', 'Math.max(4, Math.min(lim, v))')
    has('가르고 규칙 · 속도 권고 글은 한 곳뿐', "🟢 통과 가능 <b>")
    has('가르고 규칙 · 일반 운행 권장 숫자는 제한 안(넘는 속도는 「제한 넘음 · 속도 확인」 사실만 · 제한+10 까지)', "vk9 > LC.lim + 2 && vk9 <= LC.lim + 10 ? sigAt(")   # v0.34.0
    has('가르고 규칙 · 긴급 운행 속도는 제한+10 까지(도로교통법 §30 1호)', "RE = spdRange(ns, dd, now, LE.lim + 10).run(vkE)")   # v0.34.0   # v0.31.0 spdRange 한 곳
    return out


def chrome():
    for c in CHROME:
        if os.path.exists(c):
            return c
    raise SystemExit('크롬을 못 찾았다')


def main():
    want = [a for a in sys.argv[1:] if a in PAGES] or list(PAGES)
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(H, directory=ROOT))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    bad = 0
    if 'gargo' in want:
        print('── 규칙 문장(코드)')
        for nm, ok, got in static_rules():
            print(('  ✅ ' if ok else '  ❌ ') + nm + ('' if ok else ' — ' + got))
            bad += 0 if ok else 1
    for name in want:
        pg = PAGES[name]
        prof = tempfile.mkdtemp(prefix='pagecheck_')
        url = 'http://127.0.0.1:%d%s' % (port, pg['url'])
        p = subprocess.Popen([chrome(), '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--user-data-dir=' + prof,
                              '--window-size=420,860', url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while name not in DONE and time.time() - t0 < pg['wait']:
            time.sleep(0.3)
        p.terminate()
        try:
            p.wait(timeout=10)
        except Exception:
            p.kill()
        shutil.rmtree(prof, ignore_errors=True)
        print('── ' + name + ' (%.0f초)' % (time.time() - t0))
        r = DONE.get(name)
        if not r:
            print('  ❌ 결과가 돌아오지 않았다(화면이 안 열렸거나 스크립트가 멈춤)')
            bad += 1
            continue
        for nm, ok, got in r.get('checks', []):
            print(('  ✅ ' if ok else '  ❌ ') + nm + ('' if (ok and not got) else ' — ' + str(got)))
            bad += 0 if ok else 1
    srv.shutdown()
    print(('❌ 값 검사 실패 %d건 — 커밋하지 않는다' % bad) if bad else '✅ 값 검사 통과')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
