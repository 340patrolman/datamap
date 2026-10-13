# -*- coding: utf-8 -*-
"""머리 없는 크롬을 직접 부린다(브라우저 페인이 숨어 멈출 때 · 라이브 사이트 확인용 · 표준 라이브러리만).

    from cdp import Chrome
    c = Chrome(width=420, height=860)
    c.go('https://…');  c.ev("localStorage.setItem('k','1')");  print(c.ev('document.title'));  c.shot('a.png');  c.close()

ev(식) 은 값을 JSON 으로 돌려준다(Promise 면 기다린다). 열쇠·비밀번호를 넣는 데 쓰지 않는다.
"""
import os, json, time, base64, socket, struct, subprocess, tempfile, shutil, urllib.request

CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
          r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe']


class Chrome:
    def __init__(self, width=420, height=860, port=0):
        exe = next(c for c in CHROME if os.path.exists(c))
        if not port:
            s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
        self.prof = tempfile.mkdtemp(prefix='cdp_')
        self.p = subprocess.Popen([exe, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--user-data-dir=' + self.prof,
                                   '--remote-debugging-port=%d' % port, '--window-size=%d,%d' % (width, height), 'about:blank'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws = None
        for _ in range(60):
            try:
                tabs = json.loads(urllib.request.urlopen('http://127.0.0.1:%d/json' % port, timeout=2).read().decode('utf-8'))
                ws = next(t['webSocketDebuggerUrl'] for t in tabs if t.get('type') == 'page')
                break
            except Exception:
                time.sleep(0.25)
        if not ws:
            self.close(); raise SystemExit('크롬 디버그 포트가 안 열렸다')
        host, path = ws[5:].split('/', 1)
        h, pt = host.split(':')
        self.s = socket.create_connection((h, int(pt)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(('GET /%s HTTP/1.1\r\nHost: %s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n' % (path, host, key)).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.s.recv(4096)
        self.buf = buf.split(b'\r\n\r\n', 1)[1]
        self.n = 0
        self.cmd('Page.enable'); self.cmd('Runtime.enable')

    def _send(self, text):
        d = text.encode('utf-8'); m = os.urandom(4); n = len(d)
        hd = b'\x81' + (bytes([0x80 | n]) if n < 126 else b'\xfe' + struct.pack('>H', n) if n < 65536 else b'\xff' + struct.pack('>Q', n)) + m
        self.s.sendall(hd + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def _need(self, k):
        while len(self.buf) < k:
            c = self.s.recv(65536)
            if not c:
                raise ConnectionError('크롬과 끊겼다')
            self.buf += c
        out, self.buf = self.buf[:k], self.buf[k:]
        return out

    def _recv(self):
        data = b''
        while True:
            b0, b1 = self._need(2)
            n = b1 & 0x7f
            if n == 126:
                n = struct.unpack('>H', self._need(2))[0]
            elif n == 127:
                n = struct.unpack('>Q', self._need(8))[0]
            data += self._need(n)
            if b0 & 0x80:
                if (b0 & 0x0f) in (1, 0, 2):
                    return data.decode('utf-8', 'replace')
                data = b''

    def cmd(self, method, **params):
        self.n += 1
        me = self.n
        self._send(json.dumps({'id': me, 'method': method, 'params': params}))
        while True:
            j = json.loads(self._recv())
            if j.get('id') == me:
                if 'error' in j:
                    raise RuntimeError(method + ': ' + json.dumps(j['error'], ensure_ascii=False))
                return j.get('result', {})

    def go(self, url, wait=2.0):
        self.cmd('Page.navigate', url=url)
        time.sleep(wait)

    def ev(self, expr):
        r = self.cmd('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=True)
        if r.get('exceptionDetails'):
            return 'ERR ' + str(r['exceptionDetails'].get('exception', {}).get('description') or r['exceptionDetails'].get('text'))
        return r.get('result', {}).get('value')

    def phone(self, width=375, height=812):
        self.cmd('Emulation.setDeviceMetricsOverride', width=width, height=height, deviceScaleFactor=2, mobile=True)

    def shot(self, path):
        r = self.cmd('Page.captureScreenshot', format='png')
        open(path, 'wb').write(base64.b64decode(r['data']))
        return path

    def close(self):
        try:
            self.s.close()
        except Exception:
            pass
        try:
            self.p.terminate(); self.p.wait(timeout=10)
        except Exception:
            try:
                self.p.kill()
            except Exception:
                pass
        shutil.rmtree(self.prof, ignore_errors=True)
