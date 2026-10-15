# -*- coding: utf-8 -*-
"""가르고 길 ↔ 카카오 길 「엉뚱한 길」 대조(2026-10-15 소유자 「가르고는 신호값·실시간 교통량만이라 엉뚱하게 알려 줄 수 있다 · 대조도 해 보고」 · 「계속 진행」)

고정 짝 12개(서초 교차로 사이 · 실사건 좌표 아님)마다
  ① 가르고 길 = 머리 없는 크롬으로 가르고(gargo/index.html)를 열어 GARGO.findRoute(일반 모드 · 지금 시각)
  ② 카카오 길 = 같은 출발점(가르고 길 첫머리 + 진행각)·도착점으로 지금 한 번 묻기(priority TIME)
  ③ 겹침 = 카카오 길 길이 가운데 가르고 길 30m 안에 드는 몫 · 거꾸로도 · 거리·시간 나란히
화면에 찍는다 — 카카오 결과(길 모양·이름·거리·시간)는 저장하지 않는다(카카오 운영정책 제5조) · --save 면 비율·겹침만 묶음 칸에(compare_acc.py · 07_API키/out/compare/acc-YYYYMMDD.json · 시각·우리 값 없이 · 보고는 3건 이상 칸만 — 소유자 2026-10-15 「묶은 값만」) · 그 밖에 쓰는 것은 하루 호출 수(day.json)
열쇠 = 07_API키/keys.json 「kakao_navi」(출력하지 않는다) · 하루 9,000 넘으면 안 부름 · 401/403/429 면 멈춤
  py -3.12 -X utf8 tools/signal/route-spot.py [짝 번호 …] [-d] [--save]      (-d = 길 이름별 거리·시간을 양쪽 나란히 — 같은 길인데 시간이 어긋날 때 어느 길에서인지)
"""
import sys, os, json, math, time, socket, threading, functools, http.server, urllib.request, urllib.parse, urllib.error, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
sys.path.insert(0, os.path.join(ROOT, 'tools', 'check'))
from cdp import Chrome

DAY = os.path.join(RAW, 'out', 'kakao_eta', 'day.json')
CAP = 9000
URL = 'https://apis-navi.kakaomobility.com/v1/directions'
KST = dt.timezone(dt.timedelta(hours=9))
PAIRS = [('서초역사거리', '양재역사거리'), ('양재역사거리', '서초역사거리'), ('방배역사거리', '강남역사거리'), ('강남역사거리', '방배역사거리'),
         ('사당역사거리', '서초역사거리'), ('서울성모병원앞교차로', '뱅뱅사거리'), ('이수역앞교차로', '남부터미널역앞교차로'), ('신사역사거리', '예술의전당앞교차로'),
         ('염곡동사거리', '내방역앞교차로'), ('교보타워사거리', '사당역사거리'), ('남부터미널역앞교차로', '서울성모병원앞교차로'), ('내방역앞교차로', '양재역사거리')]
LON0, LAT0, KX, KY = 127.01, 37.49, 88800, 111000   # gargo.js 와 같은 평면


def day_book(add=0):
    today = dt.datetime.now(KST).strftime('%Y-%m-%d')
    try:
        b = json.load(open(DAY, encoding='utf-8'))
    except Exception:
        b = {}
    if b.get('date') != today:
        b = {'date': today, 'calls': 0}
    b['calls'] += add
    os.makedirs(os.path.dirname(DAY), exist_ok=True)
    json.dump(b, open(DAY, 'w', encoding='utf-8'))
    return b['calls']


def xy(lon, lat):
    return ((lon - LON0) * KX, (LAT0 - lat) * KY)


def near_frac(A, B, tol=30.0):
    """A 선 길이 가운데 B 선 tol m 안에 드는 몫(10m 간격 표본)"""
    if len(A) < 2 or len(B) < 2:
        return 0.0
    def dseg(p, a, b):
        vx, vy = b[0] - a[0], b[1] - a[1]; l2 = vx * vx + vy * vy
        t = 0 if not l2 else max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2))
        return math.hypot(a[0] + vx * t - p[0], a[1] + vy * t - p[1])
    tot = ok = 0.0
    for i in range(1, len(A)):
        a, b = A[i - 1], A[i]; L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, int(L // 10))
        for k in range(n):
            p = (a[0] + (b[0] - a[0]) * (k + .5) / n, a[1] + (b[1] - a[1]) * (k + .5) / n)
            tot += L / n
            if min(dseg(p, B[j - 1], B[j]) for j in range(1, len(B))) <= tol:
                ok += L / n
    return ok / tot if tot else 0.0


def save_row(kind, row):
    """대조 한 번 → 묶음 칸에 비율만(compare_acc.py · 시각·우리 값은 안 남김 · 소유자 결정 2026-10-15 「묶은 값만」)"""
    if '--save' not in sys.argv:
        return
    import importlib.util as iu
    sp = iu.spec_from_file_location('compare_acc', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compare_acc.py')); A = iu.module_from_spec(sp); sp.loader.exec_module(A)
    try:
        hol = set(json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'eta-cal.json'), encoding='utf-8')).get('holidays', []))
    except Exception:
        hol = set()
    t = dt.datetime.fromisoformat(row['t'])
    if kind == 'route':
        same = min(row['ov_k'], row['ov_g']) >= 0.7
        A.add('route', t, row['pair'], {'rt': row['rt'], 'rd': row['rd'], 'ovk': row['ov_k'], 'ovg': row['ov_g'], 'rts': row['rt'] if same else None, 'far': bool(row['far']), 'same': same}, hol)
    else:
        A.add('seg', t, row['id'], {'rk': row['rk'], 'rkc': row.get('rkc')}, hol)

def main():
    key = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig')).get('kakao_navi')
    if not key:
        print('keys.json 에 kakao_navi 가 없다'); return 1
    nodes = json.load(open(os.path.join(RAW, 'kakao_eta_segments.json'), encoding='utf-8'))['nodes']
    pick = [int(a) for a in sys.argv[1:] if a.isdigit()]
    pairs = [(i + 1, p) for i, p in enumerate(PAIRS) if not pick or i + 1 in pick]
    if day_book() + len(pairs) > CAP:
        print('오늘 카카오 호출이 한도의 90% 에 닿았다'); return 1
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    c = Chrome(width=412, height=915)
    try:
        B = 'http://127.0.0.1:%d/gargo/' % port
        c.go(B + 'index.html', 1.0); c.ev("localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1')")
        c.go(B + 'index.html?rs=1', 1.0)
        for _ in range(90):
            time.sleep(1)
            if c.ev("!!(window.GARGO && GARGO.state().G && GARGO.state().G.S.length)"):
                break
        time.sleep(4)   # 신호값·소통 받기
        c.ev("GARGO.pkAll && GARGO.pkAll()"); time.sleep(6)
        now = dt.datetime.now(KST)
        print('가르고 ↔ 카카오 길 대조 %s · 겹침 = 그 길 길이 가운데 다른 쪽 길 30m 안 몫 · 카카오 값은 저장하지 않는다' % now.strftime('%Y-%m-%d %H:%M'))
        print('%-3s %-26s %13s %13s %7s %7s' % ('짝', '출발 → 도착', '가르고', '카카오', '카→가', '가→카'))
        low = []
        for no, (a, b) in pairs:
            A, Bn = nodes[a], nodes[b]
            js = "(function(){var g=GARGO, s=g.P(%f,%f), t=g.P(%f,%f), r=g.findRoute(s[0],s[1],t[0],t[1],Date.now()/1000,null); if(!r) return null; var by={}; for (var ii=0; ii<r.lims.length; ii++){ var a0=Math.min(r.lims[ii][0],r.dist), a1=Math.min(ii+1<r.lims.length?r.lims[ii+1][0]:r.dist,r.dist), nm=r.lims[ii][2]||'(이름 없는 길)'; by[nm]=by[nm]||[0,0]; by[nm][0]+=a1-a0; by[nm][1]+=g.tAt(r,a1)-g.tAt(r,a0); } var seq=[], last=''; r.lims.forEach(function(q){ var nm=q[2]||'(이름 없는 길)'; if(nm!==last){ seq.push(nm); last=nm; } }); return JSON.stringify({pts:r.pts, dist:r.dist, time:r.time, seq:seq.join(' › '), by:by});})()" % (A['lon'], A['lat'], Bn['lon'], Bn['lat'])
            rj = c.ev(js)
            if not rj:
                print('%-3d %-26s  가르고 길 없음' % (no, (a + '→' + b)[:26])); continue
            r = json.loads(rj); P = [(r['pts'][i], r['pts'][i + 1]) for i in range(0, len(r['pts']) - 1, 2)]
            ll = lambda p: (p[0] / KX + LON0, LAT0 - p[1] / KY)
            k = 1
            while k < len(P) - 1 and math.hypot(P[k][0] - P[0][0], P[k][1] - P[0][1]) < 15:
                k += 1
            ang = (math.degrees(math.atan2(P[k][0] - P[0][0], -(P[k][1] - P[0][1]))) + 360) % 360
            o, d = ll(P[0]), ll(P[-1])
            qs = urllib.parse.urlencode({'origin': '%.6f,%.6f,angle=%d' % (o[0], o[1], round(ang)), 'destination': '%.6f,%.6f' % d, 'priority': 'TIME'}, safe=',=')
            try:
                with urllib.request.urlopen(urllib.request.Request(URL + '?' + qs, headers={'Authorization': 'KakaoAK ' + key}), timeout=20) as rr:
                    kj = json.loads(rr.read().decode('utf-8'))
                day_book(1)
            except urllib.error.HTTPError as e:
                day_book(1); print('카카오 오류 %s — 멈춤' % e.code)
                if e.code in (401, 403, 429):
                    return 1
                continue
            except Exception as e:
                print('통신 오류 —', str(e)[:80]); continue
            x = (kj.get('routes') or [{}])[0]
            if x.get('result_code') != 0:
                print('%-3d %-26s  카카오 길 없음(%s)' % (no, (a + '→' + b)[:26], x.get('result_msg'))); continue
            K = []
            for rd in x['sections'][0]['roads']:
                v = rd.get('vertexes') or []
                K += [xy(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)]
            f1, f2 = near_frac(K, P), near_frac(P, K)
            sm = x['summary']
            far = r['dist'] > sm['distance'] * 1.3 + 300
            flag = '  ⚠ 엉뚱(가르고가 30% 넘게 돈다)' if far else '  · 다른 길(거리 비슷)' if min(f1, f2) < 0.7 else ''
            if far:
                low.append(no)
            if '-d' in sys.argv:
                kb = {}
                for rd in x['sections'][0]['roads']:
                    nm = rd.get('name') or '(이름 없는 길)'; kb.setdefault(nm, [0, 0]); kb[nm][0] += rd['distance']; kb[nm][1] += rd['duration']
                for nm in list(dict.fromkeys(list(r.get('by', {}).keys()) + list(kb.keys()))):
                    a9, b9 = r.get('by', {}).get(nm), kb.get(nm)
                    print('      %-14s 가르고 %s · 카카오 %s' % (nm[:14], '%5dm %4d초' % (a9[0], a9[1]) if a9 else '      -      ', '%5dm %4d초' % (b9[0], b9[1]) if b9 else '-'))
            if flag:
                kseq, last = [], ''
                for rd in x['sections'][0]['roads']:
                    nm = rd.get('name') or '(이름 없는 길)'
                    if nm != last:
                        kseq.append(nm); last = nm
                print('      가르고: ' + r.get('seq', '')); print('      카카오: ' + ' › '.join(kseq))
            save_row('route', {'t': now.isoformat(timespec='seconds'), 'pair': no, 'from': a, 'to': b, 'g_m': round(r['dist']), 'g_s': round(r['time']), 'rt': round(r['time'] / max(1, sm['duration']), 3), 'rd': round(r['dist'] / max(1, sm['distance']), 3), 'ov_k': round(f1, 3), 'ov_g': round(f2, 3), 'far': bool(far)})
            print('%-3d %-26s %5.1fkm %5.1f분 %5.1fkm %5.1f분 %6d%% %6d%%%s' % (no, (a + '→' + b)[:26], r['dist'] / 1000, r['time'] / 60, sm['distance'] / 1000, sm['duration'] / 60, round(f1 * 100), round(f2 * 100), flag))
            time.sleep(0.3)
        print('엉뚱한 길(가르고 거리 > 카카오 × 1.3) 짝: %s · 오늘 카카오 호출 %d건 · 「다른 길(거리 비슷)」은 대안 길이라 틀린 것이 아니다' % (', '.join(map(str, low)) or '없음', day_book()))
    finally:
        c.close(); srv.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
