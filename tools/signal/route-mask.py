# -*- coding: utf-8 -*-
"""가르고 길 고르기 — 실측을 가리고 고르게 한 뒤 가린 값으로 채점(선택 편향 재기 · 불확실 몫 배수 고르기)

까닭(2026-11-13 신호 세션 · NEXT.md 「오전 같은 길인데 시간 25~30% 낙관」): 실측 없는 줄은 「그 순간 같은 등급 실측/제한 가운데값(LIVER)」으로 메운다.
평균은 맞아도 줄마다 크게 틀려(|log| 오차 0.33~0.46), 길 찾기가 「메움 값이 빠르게 나온 줄」을 골라 가면 고른 길 시간이 낙관이 된다.
이 도구는 카카오 없이 ITS 기록만으로 그 몫을 잰다:
  ① 지난 소통 한 장에서 실측 링크의 일부(기본 40%)를 가린 장을 가르고에 넣고 길을 고르게 한다(가르고에게 그 링크는 「실측 없음」)
  ② 고른 길을 **가리지 않은 값**으로 다시 잰다(가린 링크는 진짜 값 · 원래 실측 없는 줄은 고를 때의 메움 값 그대로)
  ③ 길 고르기 비용에 「실측 아닌 줄 × K」를 걸어(시간 표시는 그대로) K 마다 ②의 진짜 시간이 어떻게 바뀌는지 본다
찍는 것: K 마다 — 가린 줄에서의 낙관(진짜 ÷ 고를 때 시간) · 길 전체 진짜 시간(K=1 대비) · 거리 · 실측 아닌 줄 몫. 소통 기록은 읽기만.

  py -3.12 -X utf8 tools/signal/route-mask.py [--day 20261112] [--times 08:30,09:30,11:00,14:00,17:30,18:30] [--hide 40] [--k 1,1.1,1.2,1.35] [역 이름 …]

가르고 코드는 서버가 내줄 때만 시험 창구(__unc·__edges)를 끼운다 — gargo.js 에 창구가 들어 있으면(v0.52.1~) 그대로 쓴다.
한계: 가리는 링크는 고르게 뽑는다 — 실제로 값이 안 오는 링크는 특정 길에 몰려 있어 성질이 다를 수 있다.
"""
import sys, os, json, gzip, time, socket, threading, functools, http.server, importlib.util, hashlib, statistics, datetime as dt
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
    day = opt('--day', (dt.datetime.now(KST) - dt.timedelta(days=1)).strftime('%Y%m%d'))
    times = opt('--times', '08:30,09:30,11:00,14:00,17:30,18:30').split(',')
    hide = int(opt('--hide', '40')); KS = [float(x) for x in opt('--k', '1,1.1,1.2,1.35').split(',')]; VAR = opt('--var', 'base')
    skip = {opt('--day', ''), opt('--times', ''), opt('--hide', ''), opt('--k', ''), opt('--var', '')}
    ARG = [a for a in sys.argv[1:] if not a.startswith('-') and a not in skip]
    fn = os.path.join(RS.RAW, 'out', 'livespd', day + '.jsonl.gz')
    if not os.path.exists(fn):
        print('소통 기록 없음', fn); return 1
    FIL = json.load(open(os.path.join(ROOT, 'data', 'live-spd-filler.json'), encoding='utf-8')); FIL = FIL.get('m', FIL)
    hm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    allsn = []
    with gzip.open(fn, 'rt', encoding='utf-8') as f:
        for ln in f:
            try:
                j = json.loads(ln)
            except Exception:
                continue
            if j.get('m'):
                t = dt.datetime.fromtimestamp(j['at'], KST); allsn.append((t.hour * 60 + t.minute, j))
    snaps = []
    for tm in times:
        if not allsn:
            break
        q = min(allsn, key=lambda z: abs(z[0] - hm(tm)))
        if abs(q[0] - hm(tm)) <= 20:
            j = q[1]; full = {k: v for k, v in j['m'].items() if v and v > 0 and not (k in FIL and FIL[k] == v)}   # 채움 값은 livespd-bake 처럼 뺀다
            hid = set(k for k in full if int(hashlib.md5((k + '|' + tm).encode()).hexdigest()[:6], 16) % 100 < hide)
            snaps.append({'tm': '%02d:%02d' % (q[0] // 60, q[0] % 60), 'at': j['at'], 'full': full, 'hid': hid, 'm': {k: v for k, v in full.items() if k not in hid}})
    if not snaps:
        print('그 시각 소통 기록 없음'); return 1
    pairs = [p for p in PAIRS if not ARG or any(x in p for x in ARG)]
    CUR = {'m': snaps[0]['m'], 'tm': snaps[0]['tm'], 'n': 0}
    GJS = os.path.join(ROOT, 'gargo', 'gargo.js')

    class H(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            p0 = self.path.split('?')[0]
            if p0.endswith('/data/live-spd-six.json'):
                b = json.dumps({'schema': 'tg-live-spd/1', 'at': int(time.time()), 'made': '가림 ' + CUR['tm'], 'm': CUR['m']}).encode('utf-8')
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(b))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b)
                CUR['n'] += 1; return
            if p0.endswith('/gargo/gargo.js'):
                src = open(GJS, encoding='utf-8').read()
                if '__edges:' not in src:
                    c0, g0, v0 = "* accK(e) * (PEN && PEN[G.eS[e]] ? (PEN.k || 1.6) : 1); }", 'window.GARGO = {', '  var PEN = null;'
                    if src.count(c0) != 1 or src.count(g0) != 1 or src.count(v0) != 1:
                        self.send_error(500); return
                    src = src.replace(v0, '  var UNC_K = 1;' + v0).replace(c0, "* accK(e) * (PEN && PEN[G.eS[e]] ? (PEN.k || 1.6) : 1) * (UNC_K > 1 && LIVE.m && !eLive(e) && !lrnSpeed(e) ? UNC_K : 1); }")
                    src = src.replace(g0, g0 + " __unc: function (k) { if (k != null) UNC_K = k; return UNC_K; }, __edges: function (r) { return r.es.map(function (e) { var q = G.S[G.eS[e]], li = q[G.eR[e] ? 14 : 13]; return [q[2], q[3] || 30, li != null && li >= 0 ? G.j.links[li] : '', Math.round(eV(e) * 10) / 10, eLive(e) ? 1 : 0, q[4], Math.round(eVt(e) * 10) / 10]; }); },")
                if VAR in ('liver', 'both'):   # 실측 없는 줄 메움을 속도 가운데값 → 시간 기준(조화평균)으로 바꿔 본다
                    m0 = "var by = {}, all = [], med = function (v) { v.sort(function (a, b) { return a - b; }); return v[v.length >> 1]; };"
                    l0 = "LIVER = { all: med(all) }; Object.keys(by).forEach(function (c) { if (by[c].length >= 20) LIVER[c] = med(by[c]); });"
                    if src.count(m0) == 1 and src.count(l0) == 1:
                        src = src.replace(m0, m0 + " var har = function (v) { var s9 = 0; v.forEach(function (x) { s9 += 1 / Math.max(0.03, x); }); return v.length / s9; };").replace(l0, l0.replace('med(', 'har('))
                if VAR == 'both':
                    f0 = "F[e] = ((A ? A[0] * w1 : 0) + (B ? B[0] * w2 : 0)) / (w1 + w2);"
                    if src.count(f0) == 1:
                        src = src.replace(f0, "F[e] = (w1 + w2) / ((A ? w1 / A[0] : 0) + (B ? w2 / B[0] : 0));")
                b = src.encode('utf-8'); self.send_response(200); self.send_header('Content-Type', 'application/javascript'); self.send_header('Content-Length', str(len(b))); self.send_header('Cache-Control', 'no-store'); self.end_headers(); self.wfile.write(b); return
            return super().do_GET()
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(H, directory=ROOT)); threading.Thread(target=srv.serve_forever, daemon=True).start()
    c = RS.Chrome(width=412, height=915)
    ROWS = {k: [] for k in KS}; HID = []
    try:
        c.cmd('Page.addScriptToEvaluateOnNewDocument', source="(function(){var si=window.setInterval;window.setInterval=function(f,ms){if(ms===300000)window.__T5=f;return si.apply(this,arguments);};})();")
        B = 'http://127.0.0.1:%d/gargo/' % port
        c.go(B + 'index.html', 1.0); c.ev("localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1')")
        c.go(B + 'index.html?rs=1', 1.0)
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
        if not c.ev("!!(window.__T5 && GARGO.__unc && GARGO.__edges)"):
            print('시험 창구를 못 붙임'); return 1
        for si, S in enumerate(snaps):
            CUR['m'] = S['m']; CUR['tm'] = S['tm']; n0 = CUR['n']; c.ev("window.__T5() || 1")
            for _ in range(60):
                time.sleep(0.5)
                if CUR['n'] > n0:
                    break
            time.sleep(4)
            for a, b in pairs:
                A, Bn = ST[a], ST[b]
                per = {}
                for K in KS:
                    js = ("(function(){var g=GARGO,s=g.P(%f,%f),t=g.P(%f,%f); g.__unc(%f); var r; try{ r=g.findRoute(s[0],s[1],t[0],t[1],%d,null); } finally { g.__unc(1); } if(!r) return null;"
                          "return JSON.stringify({d:r.dist,t:r.time,e:g.__edges(r)});})()") % (A[0], A[1], Bn[0], Bn[1], K, S['at'])
                    rj = c.ev(js)
                    if not rj:
                        per = None; break
                    per[K] = json.loads(rj)
                if not per:
                    continue
                for K in KS:
                    r = per[K]; tt = tp = ht = hp = nl = hl = 0.0
                    for ln, lim, lk, v, lv, g, vt in r['e']:
                        pv = max(4.0, v)
                        if lk and lk in S['hid']:
                            tv = max(4.0, min(lim, S['full'][lk])); ht += ln / tv; hp += ln / pv; hl += ln
                            if K == KS[0]:
                                HID.append((si, ln, lim, g, tv, pv, max(3.0, vt)))
                        else:
                            tv = pv
                        tt += ln / tv; tp += ln / pv
                        if not lv:
                            nl += ln
                    ROWS[K].append({'p': a + '→' + b, 'tm': S['tm'], 'tt': tt, 'tp': tp, 'ht': ht, 'hp': hp, 'd': r['d'], 'nl': nl, 'hl': hl})
            print('  %s 장 %d/%d' % (S['tm'], si + 1, len(snaps)), flush=True)
    finally:
        c.close(); srv.shutdown()
    base = {(x['p'], x['tm']): x for x in ROWS[KS[0]]}
    print('가르고 실측 가리고 길 고르기 · %s · %s · 실측 링크 %d%% 가림 · 짝 %d · 메움 %s' % (day, ' '.join(s['tm'] for s in snaps), hide, len(pairs), VAR))
    print('고른 길 진짜 시간 합 %.1f시간 · 화면 시간 합 %.1f시간' % (sum(x['tt'] for x in ROWS[KS[0]]) / 3600 * 3.6, sum(x['tp'] for x in ROWS[KS[0]]) / 3600 * 3.6))
    print('%-5s %10s %12s %12s %10s %10s %8s' % ('K', '가린 줄 낙관', '진짜 시간/K=1', '(나빠진 길)', '거리/K=1', '실측 아닌 몫', '가린 몫'))
    for K in KS:
        X = ROWS[K]
        if not X:
            continue
        ho = sum(x['ht'] for x in X) / max(1e-9, sum(x['hp'] for x in X))
        rt = [x['tt'] / base[(x['p'], x['tm'])]['tt'] for x in X if (x['p'], x['tm']) in base]
        rd = [x['d'] / base[(x['p'], x['tm'])]['d'] for x in X if (x['p'], x['tm']) in base]
        print('%-5s %10.3f %12.4f %12s %10.4f %9.1f%% %7.1f%%' % (('%g' % K), ho, sum(rt) / len(rt), '%d/%d' % (sum(1 for v in rt if v > 1.02), len(rt)), sum(rd) / len(rd),
                                                              100 * sum(x['nl'] for x in X) / sum(x['d'] for x in X), 100 * sum(x['hl'] for x in X) / sum(x['d'] for x in X)))
    # 화면 시간(eVt = 이웃 메움 포함)과 메움 통계 바꿔 보기 — 가르고 liveStat 을 흉내(줄·방향마다 실측/제한 · 등급마다 20개 넘으면 그 등급)
    P = json.load(open(os.path.join(ROOT, 'gargo', 'pack-six.json'), encoding='utf-8')); LK = P['links']
    segl = [(LK[q[k]], q[4], q[3] or 30, q[2]) for q in P['seg'] for k in (13, 14) if q[k] is not None and q[k] >= 0]
    ST9 = []
    for S in snaps:
        by = {}
        for lk, g, lim, ln in segl:
            v = S['m'].get(lk)
            if v:
                by.setdefault(g, []).append((min(1.0, v / lim), ln))
        allr = [x for L9 in by.values() for x in L9]
        def stat(L9):
            r = sorted(x[0] for x in L9)
            return {'med': r[len(r) // 2], 'har': len(r) / sum(1 / max(0.03, x) for x in r), 'lhar': sum(x[1] for x in L9) / sum(x[1] / max(0.03, x[0]) for x in L9), 'q35': r[int(len(r) * 0.35)]}
        A = stat(allr); ST9.append({g: (stat(L9) if len(L9) >= 20 else A) for g, L9 in by.items()} | {'all': A})
    def opt9(sel, vf):
        X = [h for h in HID if sel(h)]
        return (sum(h[1] / h[4] for h in X) / max(1e-9, sum(h[1] / vf(h) for h in X)), sum(h[1] for h in X) / 1000) if X else (0, 0)
    isL = lambda h: abs(h[6] - max(4.0, h[2] * ST9[h[0]].get(h[3], ST9[h[0]]['all'])['med'])) < 0.11   # 화면 시간이 등급 가운데값(LIVER)으로 메운 줄
    print('가린 줄(K=1 길) 화면 시간 기준 — 낙관(진짜 ÷ 본 시간) · km')
    print('  전체 %.3f(%.0fkm) · 이웃 메움 줄 %.3f(%.0fkm) · 등급 가운데값 줄 %.3f(%.0fkm)' % (opt9(lambda h: 1, lambda h: h[6]) + opt9(lambda h: not isL(h), lambda h: h[6]) + opt9(isL, lambda h: h[6])))
    for nm9, ko in (('har', '조화평균'), ('lhar', '길이 무게 조화평균'), ('q35', '아래 35%째')):
        f9 = lambda h, nm9=nm9: max(4.0, h[2] * ST9[h[0]].get(h[3], ST9[h[0]]['all'])[nm9]) if isL(h) else h[6]
        print('  가운데값 대신 %s: 등급 가운데값 줄 %.3f · 전체 %.3f' % (ko, opt9(isL, f9)[0], opt9(lambda h: 1, f9)[0]))
    print('  등급별 가운데값/조화평균/길이 조화: ' + ' · '.join('%s %.2f/%.2f/%.2f' % (g, v['med'], v['har'], v['lhar']) for g, v in sorted(ST9[-1].items(), key=str)))
    print('가린 줄 낙관 = 가린 줄의 진짜 걸린 시간 ÷ 고를 때 본 시간(1 보다 크면 낙관) · 진짜 시간 = 고른 길을 가리지 않은 값으로 다시 잰 것의 평균 비(작을수록 좋은 길)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
