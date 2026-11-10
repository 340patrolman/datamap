# -*- coding: utf-8 -*-
"""가르고 길 품질 재기 — 여섯 구 역 40쌍(2026-11-10 형님 「가르고네비 고도화」) · route-spot.py(서초 12쌍)의 셈을 그대로 쓰고 짝만 넓혔다

역(서울시 역사마스터 data/r/stations.json · 공개 좌표 · 실사건 아님) 사이를
  ① 가르고 길(머리 없는 크롬 · 이 작업 트리의 gargo/ · 지금 시각 · 실시간 소통 포함) + 소통 뺀 길의 골목 몫·꺾음·에움
  ② 카카오 길(같은 출발점·진행각 · priority TIME · 지금 한 번) 과 맞대
시간비·거리비·겹침(30m 안 몫)을 화면에 찍는다 — 카카오 값은 저장하지 않는다(카카오 운영정책 · RULE-NAV-4) · 쓰는 것은 하루 호출 수(day.json)뿐
  py -3.12 -X utf8 tools/signal/route-bench.py [역 이름 …] [-d] [--seoul]     (-d = 길 이름별 거리·시간 나란히 · --seoul = 서울 묶음 ?pk=seoul)
첫 판(11-10 23시): 겹침 60% 아래 18/40 — ITS 채움 값(올림픽대로 시속 21km) 탓 → livefiller-bake.py 로 뺀 뒤 10/40
"""
import sys, os, json, math, time, socket, threading, functools, http.server, urllib.request, urllib.parse, urllib.error, importlib.util, statistics, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = importlib.util.spec_from_file_location('rs', os.path.join(ROOT, 'tools', 'signal', 'route-spot.py')); RS = importlib.util.module_from_spec(sp); sp.loader.exec_module(RS)
Chrome = RS.Chrome
ST = {}
for nm, ln, lon, lat in json.load(open(os.path.join(ROOT, 'data', 'r', 'stations.json'), encoding='utf-8'))['items']:
    ST.setdefault(nm, (lon, lat))
PAIRS = [('서초', '잠실'), ('잠실', '서초'), ('강남', '서울대입구'), ('서울대입구', '강남'), ('사당', '수서'), ('수서', '사당'), ('용산', '강남'), ('강남', '용산'),
         ('노량진', '삼성'), ('삼성', '노량진'), ('신림', '고속터미널'), ('고속터미널', '신림'), ('이태원', '양재'), ('양재', '이태원'), ('가락시장', '교대'), ('교대', '가락시장'),
         ('압구정', '낙성대'), ('낙성대', '압구정'), ('청담', '방배'), ('방배', '청담'), ('문정', '선릉'), ('선릉', '문정'), ('한남', '도곡'), ('도곡', '한남'),
         ('삼각지', '신사'), ('신사', '삼각지'), ('흑석', '역삼'), ('역삼', '흑석'), ('석촌', '대치'), ('대치', '석촌'), ('신대방', '내방'), ('내방', '신대방'),
         ('올림픽공원', '논현'), ('논현', '올림픽공원'), ('보라매', '이수'), ('녹사평', '잠실새내'), ('개포동', '상도'), ('서빙고', '남부터미널'), ('봉천', '학여울'), ('장지', '동작')]
ARG = [a for a in sys.argv[1:] if not a.startswith('-')]
PK = '?pk=seoul' if '--seoul' in sys.argv else ''


def main():
    if '--help' in sys.argv or '-h' in sys.argv:   # (2026-11-11) 도움말만 찍고 끝낸다 — 없을 때 --help 가 그대로 한 번 돌아 카카오를 불렀다
        print(__doc__); return 0
    key = json.load(open(os.path.join(RS.RAW, 'keys.json'), encoding='utf-8-sig')).get('kakao_navi')
    miss = [n for p in PAIRS for n in p if n not in ST]
    if miss:
        print('역 좌표 없음', set(miss)); return 1
    if RS.day_book() + len(PAIRS) > RS.CAP:
        print('카카오 한도'); return 1
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
    c = Chrome(width=412, height=915); rows = []
    try:
        B = 'http://127.0.0.1:%d/gargo/' % port
        c.go(B + 'index.html', 1.0); c.ev("localStorage.setItem('tg_map2d_gate','1');localStorage.setItem('tg_gargo_intro','1')")
        c.go(B + 'index.html' + (PK + '&rs=1' if PK else '?rs=1'), 1.0)
        for _ in range(120):
            time.sleep(1)
            if c.ev("!!(window.GARGO && GARGO.state().G && GARGO.state().G.S.length)"):
                break
        time.sleep(5); c.ev("GARGO.pkAll && GARGO.pkAll() && 1")
        for _ in range(90):
            time.sleep(1)
            if c.ev("(function(){var p=GARGO.pk(); return !p.on || p.tiles===p.total;})()"):
                break
        time.sleep(8)
        st = c.ev("JSON.stringify({S:GARGO.state().G.S.length, sig:GARGO.state().G.sig.length})")
        now = dt.datetime.now(RS.KST)
        print('가르고 여섯 구 길 품질 %s · %s' % (now.strftime('%Y-%m-%d %H:%M'), st))
        print('%-18s %12s %12s %5s %5s %5s %5s %4s %3s %5s' % ('짝', '가르고', '카카오', '시간비', '거리비', '카→가', '가→카', '골목', '꺾', '에움'))
        for a, b in PAIRS:
            if ARG and not any(x in (a, b) for x in ARG):
                continue
            A, Bn = ST[a], ST[b]
            js = ("(function(){var g=GARGO,G=g.state().G,s=g.P(%f,%f),t=g.P(%f,%f),now=Date.now()/1000,r=g.findRoute(s[0],s[1],t[0],t[1],now,null); if(!r) return null;"
                  "function q(x){var al=0,tot=0; x.es.forEach(function(e){var z=G.S[G.eS[e]]; tot+=z[2]; if(z[4]>=6) al+=z[2];}); return {dist:x.dist,time:x.time,free:x.free,alp:tot?al/tot*100:0,turns:x.mans.length-1,sigs:x.sigs.length};}"
                  "var n=g.noLive(function(){return g.findRoute(s[0],s[1],t[0],t[1],now,null);})||r, seq=[],last=''; r.lims.forEach(function(z){var nm=z[2]||'(이름 없는 길)'; if(nm!==last){seq.push(nm); last=nm;}});"
                  "var by={}; for(var ii=0;ii<r.lims.length;ii++){var a0=Math.min(r.lims[ii][0],r.dist),a1=Math.min(ii+1<r.lims.length?r.lims[ii+1][0]:r.dist,r.dist),nm=r.lims[ii][2]||'(이름 없는 길)'; by[nm]=by[nm]||[0,0]; by[nm][0]+=a1-a0; by[nm][1]+=g.tAt(r,a1)-g.tAt(r,a0);} var o=q(r); o.by=by; o.pts=r.pts; o.seq=seq.join(' › '); o.line=Math.hypot(s[0]-t[0],s[1]-t[1]); o.nl=q(n); return JSON.stringify(o);})()") % (A[0], A[1], Bn[0], Bn[1])
            rj = c.ev(js)
            if not rj:
                print('%-18s 가르고 길 없음' % (a + '→' + b)); rows.append((a, b, None)); continue
            r = json.loads(rj); P = [(r['pts'][i], r['pts'][i + 1]) for i in range(0, len(r['pts']) - 1, 2)]
            ll = lambda p: (p[0] / RS.KX + RS.LON0, RS.LAT0 - p[1] / RS.KY)
            k = 1
            while k < len(P) - 1 and math.hypot(P[k][0] - P[0][0], P[k][1] - P[0][1]) < 15:
                k += 1
            ang = (math.degrees(math.atan2(P[k][0] - P[0][0], -(P[k][1] - P[0][1]))) + 360) % 360
            o, d = ll(P[0]), ll(P[-1])
            qs = urllib.parse.urlencode({'origin': '%.6f,%.6f,angle=%d' % (o[0], o[1], round(ang)), 'destination': '%.6f,%.6f' % d, 'priority': 'TIME'}, safe=',=')
            try:
                with urllib.request.urlopen(urllib.request.Request(RS.URL + '?' + qs, headers={'Authorization': 'KakaoAK ' + key}), timeout=20) as rr:
                    kj = json.loads(rr.read().decode('utf-8'))
                RS.day_book(1)
            except urllib.error.HTTPError as e:
                RS.day_book(1); print('카카오 오류 %s' % e.code)
                if e.code in (401, 403, 429):
                    return 1
                continue
            except Exception as e:
                print('통신 오류', type(e).__name__); continue
            x = (kj.get('routes') or [{}])[0]
            if x.get('result_code') != 0:
                print('%-18s 카카오 길 없음' % (a + '→' + b)); continue
            K = []; kseq = []; last = ''
            for rd in x['sections'][0]['roads']:
                v = rd.get('vertexes') or []; K += [RS.xy(v[i], v[i + 1]) for i in range(0, len(v) - 1, 2)]
                nm = rd.get('name') or '(이름 없는 길)'
                if nm != last:
                    kseq.append(nm); last = nm
            f1, f2 = RS.near_frac(K, P), RS.near_frac(P, K); sm = x['summary']
            rt, rdd = r['time'] / max(1, sm['duration']), r['dist'] / max(1, sm['distance'])
            det = r['nl']['dist'] / max(1, r['line'])
            flag = ''
            if rdd > 1.3:
                flag += ' ⚠돈다'
            if abs(rt - 1) > 0.25:
                flag += ' ⏱시간'
            if r['nl']['alp'] > 20 or r['nl']['turns'] > 9:
                flag += ' 🏘골목·꺾음'
            print('%-18s %4.1fkm %4.1f분 %4.1fkm %4.1f분 %5.2f %5.2f %4d%% %4d%% %3d%% %3d %5.2f%s' % (a + '→' + b, r['dist'] / 1000, r['time'] / 60, sm['distance'] / 1000, sm['duration'] / 60, rt, rdd, round(f1 * 100), round(f2 * 100), round(r['nl']['alp']), r['nl']['turns'], det, flag))
            if '-d' in sys.argv:
                kb = {}
                for rd in x['sections'][0]['roads']:
                    nm = rd.get('name') or '(이름 없는 길)'; kb.setdefault(nm, [0, 0]); kb[nm][0] += rd['distance']; kb[nm][1] += rd['duration']
                for nm in list(dict.fromkeys(list(r.get('by', {}).keys()) + list(kb.keys()))):
                    a9, b9 = r.get('by', {}).get(nm), kb.get(nm)
                    if (a9 and a9[0] > 150) or (b9 and b9[0] > 150):
                        print('      %-14s 가르고 %s · 카카오 %s' % (nm[:14], '%5dm %4d초 %3dkm/h' % (a9[0], a9[1], a9[0] / max(1, a9[1]) * 3.6) if a9 else '        -          ', '%5dm %4d초 %3dkm/h' % (b9[0], b9[1], b9[0] / max(1, b9[1]) * 3.6) if b9 else '-'))
            if flag or min(f1, f2) < 0.6:
                print('     가르고: ' + r['seq'][:230]); print('     카카오: ' + ' › '.join(kseq)[:230])
            rows.append((a, b, rt, rdd, min(f1, f2), r['nl']['alp'], r['nl']['turns'], r['time'] / max(1, r['free'])))
            time.sleep(0.3)
        ok = [x for x in rows if x[2] is not None]
        if ok:
            rts = [x[2] for x in ok]; rds = [x[3] for x in ok]
            print('짝 %d · 시간비 가운데 %.2f(작은 %.2f · 큰 %.2f) · 시간비 0.75~1.25 밖 %d · 거리비 가운데 %.2f · 1.3 넘게 도는 길 %d · 겹침 60%% 아래 %d · 길 없음 %d' % (len(ok), statistics.median(rts), min(rts), max(rts), sum(1 for v in rts if abs(v - 1) > 0.25), statistics.median(rds), sum(1 for v in rds if v > 1.3), sum(1 for x in ok if x[4] < 0.6), len(rows) - len(ok)))
    finally:
        c.close(); srv.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
