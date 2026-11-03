# -*- coding: utf-8 -*-
# 자동 구역을 평소 속도로 맞추기 — 머리 없는 크롬에서 tgSim.calibrate 를 돌려 결과(설계값 배율)를 구역 자료 cal 칸에 적는다
#   쓰기: py -3.12 -X utf8 tools/sim/sim-cal.py <이름>…   (area-bake.py 로 다시 구우면 다시 돌린다)
import os, sys, json, subprocess, tempfile, re, glob, gzip, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
js = open(os.path.join(ROOT, 'js', 'sim.js'), encoding='utf-8').read()
# 그림자 판(2026-11-03 · datamap 세션 잣대 · twin-shadow.py 와 같은 되감기) — 이 PC 가 쌓은 ITS 실측을 날짜·시각별로 읽어
#   홀수 날(가장 최근 6일)은 맞춤에(고르는 값 = 평소 속도 sel + 그림자 sel2 의 평균) · 짝수 날은 판정에만(섞음 맞음 ≥ 그대로 맞음 이어야 통과 · 넘침 막기)
#   실측 값은 구역 자료에 안 담는다(모은 칸 수만) · 끄기 --no-shadow
SPD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'livespd')
TIMES = [16 * 3600 + 1800, 17 * 3600 + 1800, 18 * 3600 + 1800, 19 * 3600 + 1800]
NOSH = '--no-shadow' in sys.argv
if NOSH: sys.argv.remove('--no-shadow')
SNAP = {}
if not NOSH:
    for fz in sorted(glob.glob(os.path.join(SPD, '*.jsonl.gz'))):
        dd = os.path.basename(fz)[:8]; rows = []
        for ln in gzip.open(fz, 'rt', encoding='utf-8'):
            try: jj = json.loads(ln)
            except ValueError: continue
            tt = datetime.datetime.fromtimestamp(jj['at']); rows.append((tt.hour * 3600 + tt.minute * 60 + tt.second, jj['m']))
        SNAP[dd[:4] + '-' + dd[4:6] + '-' + dd[6:]] = rows
def near(day, T):
    best = None
    for tt, mm in SNAP.get(day, []):
        if abs(tt - T) <= 480 and (best is None or abs(tt - T) < abs(best[0] - T)): best = (tt, mm)
    return best[1] if best else None
def cases_of(M, days):
    its = {l['its'] for l in M['links'].values() if l.get('its') and not l.get('sink')}; out = []
    for d in days:
        for t0 in TIMES:
            v0, v1 = near(d, t0), near(d, t0 + 1800)
            if v0 and v1: out.append({'d': d, 't0': t0, 'v': {k: v0[k] for k in its if k in v0}, 'w': {k: v1[k] for k in its if k in v1}})
    return out
ODD = sorted(d for d in SNAP if int(d[-2:]) % 2 == 1)[-6:]
EVEN = sorted(d for d in SNAP if int(d[-2:]) % 2 == 0)
for nm in sys.argv[1:]:
    f = os.path.join(ROOT, 'data', 'sim-' + nm + '.json')
    M = json.load(open(f, encoding='utf-8'))
    old = M.pop('cal', None)
    ob = (old or {}).get('best') or {}
    floor = (ob['mh'] / ob['mn'] - 0.05) if ob.get('mn') else None   # 평소 속도 맞음이 지금보다 5%p 넘게 떨어지는 판은 안 고름
    SH = {'cal': cases_of(M, ODD), 'judge': cases_of(M, EVEN)} if SNAP else {'cal': [], 'judge': []}
    o0 = {'shadow': SH['cal'], 'mhFloor': floor}
    if os.environ.get('SIMCAL_NOOUT'): o0['noOut'] = 1   # 시험 — 나가는 길 너머 막힘(onsp)을 끄고 맞춤·판정
    if os.environ.get('SIMCAL_ROUTE2') or os.environ.get('SIMCAL_TSG'): M['cal'] = {k: 1 for k, e in (('route2', 'SIMCAL_ROUTE2'), ('tsg', 'SIMCAL_TSG')) if os.environ.get(e)}   # 시험 스위치 — 맞춤 runs 는 noCal 이라 배율은 안 읽고 이 스위치만 본다
    st = json.dumps(dict(o0, start={'scale': old['scale'], 'all': old['all']})) if old and old.get('scale') else 'null'
    # 두 번 맞춘다 — 처음부터 · 지난 배율에서 출발 → 실측 칸(평소 속도 있는 칸) 맞음과 실측 막힘 잡음의 평균이 큰 쪽(2026-10-30 · 맞춤이 문턱에서 다른 답에 내려앉아 잘 맞던 구역이 나빠지던 것)
    html = ('<!doctype html><meta charset="utf-8"><pre id="out">x</pre><script>window.__M=' + json.dumps(M, ensure_ascii=False).replace('</', '<\\/') + ';</script><script>' + js +
            '</script><script>window.__SH=' + json.dumps(SH) + ';</script><script>try{var A=tgSim.calibrate(__M,' + json.dumps(o0) + '),W=' + st + ',B=W?tgSim.calibrate(__M,W):null;function ms(c){var b=c.best;if(b.tgt!=null&&b.shadow)return b.tgt;return b.mn?(b.mh/b.mn+(b.jn?b.jh/b.jn:b.mh/b.mn))/2:b.hit/b.n;}var C=B&&ms(B)>ms(A)?B:A;C.from=C===B?"warm":"fresh";if(__M.cal&&__M.cal.route2)C.route2=1;if(__M.cal&&__M.cal.tsg)C.tsg=1;if(__SH.judge.length){__M.cal=C;var J=tgSim.shadowScore(__M,__SH.judge,' + json.dumps({'noOut': 1} if os.environ.get('SIMCAL_NOOUT') else {}) + '),pc=function(o){return o.n?o.hit/o.n:0;};C.twin={days:"even",d0:__SH.judge[0].d,d1:__SH.judge[__SH.judge.length-1].d,cases:J.cases,calCases:__SH.cal.length,sim:J.sim,keep:J.keep,mix:J.mix,pass:pc(J.mix)>=pc(J.keep)};}document.getElementById("out").textContent=JSON.stringify(C);}catch(e){document.getElementById("out").textContent="ERR "+e.stack;}</script>')
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'cal.html')
    open(p, 'w', encoding='utf-8').write(html)
    exe = [c for c in CHROME if os.path.exists(c)][0]
    r = subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=300000', '--user-data-dir=' + os.path.join(d, 'u'),
                        '--dump-dom', 'file:///' + p.replace(os.sep, '/')], capture_output=True, timeout=5400)
    t = re.search(r'<pre id="out">(.*?)</pre>', r.stdout.decode('utf-8', 'replace'), re.S).group(1).replace('&quot;', '"').replace('&amp;', '&')
    if t.startswith('ERR'):
        print(nm, t)
        sys.exit(1)
    cal = json.loads(t)
    if os.environ.get('SIMCAL_NOOUT'): cal['noOut'] = 1   # 화면에서도 같은 조건으로 돌게(create 가 M.cal.noOut 을 본다)
    if os.environ.get('SIMCAL_ROUTE2'): cal['route2'] = 1
    if os.environ.get('SIMCAL_TSG'): cal['tsg'] = 1
    M['cal'] = cal
    json.dump(M, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    tw = cal.get('twin')
    print(nm, cal.get('from'), '맞춤', ' → '.join('%d/%d' % (h['hit'], h['n']) + ('·%s' % h['sel2'] if 'sel2' in h else '') for h in cal['hist']), '· 전체 배율', cal['all'],
          '· 고른 판 평소 %d/%d 막힘 %d/%d' % (cal['best']['mh'], cal['best']['mn'], cal['best']['jh'], cal['best']['jn']),
          ('· 짝수 날 %d판 트윈 %d/%d 섞음 %d/%d 그대로 %d/%d %s' % (tw['cases'], tw['sim']['hit'], tw['sim']['n'], tw['mix']['hit'], tw['mix']['n'], tw['keep']['hit'], tw['keep']['n'], '통과' if tw['pass'] else '그대로보다 못함')) if tw else '', flush=True)
