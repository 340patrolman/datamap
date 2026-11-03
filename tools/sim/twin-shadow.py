# -*- coding: utf-8 -*-
# 디지털 트윈 그림자 운행(2026-11-03 · 소유자 「데이터지도의 온톨로지화 · 디지털 트윈이 되고 있는 중」)
#   트윈이 되려면 「지금 모습에서 출발해 앞을 내다본 것」이 실제와 맞는지 날마다 채점해야 한다.
#   이 PC 가 약 11분마다 쌓은 ITS 실측(07_API키/out/livespd/<날짜>.jsonl.gz)을 되감아
#     ① 트윈 = 그 시각 실측으로 길을 채우고(scen.init) 30·60분 앞을 돌린 시뮬
#     ② 평소 시뮬 = 실측 없이 평소 수요로만 돌린 같은 날 같은 시각
#     ③ 그대로 = 「지금 막힌 곳은 30·60분 뒤에도 막혀 있다」(아무것도 안 하는 어림 — 트윈이 이것보다 나아야 쓸모가 있다)
#   셋을 그 뒤 실제 실측과 맞대 칸 수로 센다(막힘 = 실측 6km/h 이하 · 시뮬 점유 80% 이상 — 맞춤·지금 실측과 같은 잣대).
#   실측 속도 → 길 채움 = Greenshields(1935) 밀도-속도 직선: 채움 = 1 − 속도 ÷ 자유 속도(그 길 평소 속도 가운데 가장 빠른 시각 값) — 설계값
#   개념 시연 — 예측·보증 아님 · 결과는 data/twin-shadow.json(모은 칸 수만 · 시각별 실측 값은 안 담음)
#   쓰기: py -3.12 -X utf8 tools/sim/twin-shadow.py [구역…] [--times 16:30,17:30,18:30,19:30] [--days 14] [--days-parity odd|even]
#   (TWIN_DRY=1 이면 결과를 임시 폴더에 — data/twin-shadow.json 을 안 덮음)
import os, sys, json, gzip, glob, subprocess, tempfile, re, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
KB = os.path.dirname(ROOT)
SPD = os.path.join(KB, '07_API키', 'out', 'livespd')
CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
JAMV, NEAR = 6, 8 * 60          # 실측 막힘 문턱 km/h · 실측 표본을 그 시각 앞뒤 몇 초 안에서 찾나
HZ = (1800, 3600)               # 내다보는 폭(초)

args = sys.argv[1:]
def opt(k, d):
    if k in args:
        i = args.index(k); v = args[i + 1]; del args[i:i + 2]; return v
    return d
TIMES = [int(x.split(':')[0]) * 3600 + int(x.split(':')[1]) * 60 for x in opt('--times', '16:30,17:30,18:30,19:30').split(',')]
NDAYS = int(opt('--days', '0'))
PAR = opt('--days-parity', '')   # odd | even — 맞춤(홀수 날)과 판정(짝수 날)을 나눌 때 · 날짜의 일(日)로 가름
AREAS = args or [a['id'] for a in json.load(open(os.path.join(ROOT, 'data', 'sim-areas.json'), encoding='utf-8'))['areas']]

# ---- 실측 되감기: 날짜 → [(초, {링크: 속도})] ----
SNAP = {}
for f in sorted(glob.glob(os.path.join(SPD, '*.jsonl.gz'))):
    d = os.path.basename(f)[:8]; day = d[:4] + '-' + d[4:6] + '-' + d[6:]
    rows = []
    for ln in gzip.open(f, 'rt', encoding='utf-8'):
        try: j = json.loads(ln)
        except ValueError: continue
        t = datetime.datetime.fromtimestamp(j['at']); rows.append((t.hour * 3600 + t.minute * 60 + t.second, j['m']))
    SNAP[day] = sorted(rows, key=lambda r: r[0])
DAYS = sorted(SNAP)[-NDAYS:] if NDAYS else sorted(SNAP)
if PAR: DAYS = [d for d in DAYS if int(d[-2:]) % 2 == (1 if PAR == 'odd' else 0)]

def near(day, T):
    best = None
    for t, m in SNAP.get(day, []):
        if abs(t - T) <= NEAR and (best is None or abs(t - T) < abs(best[0] - T)): best = (t, m)
    return best[1] if best else None

JS = open(os.path.join(ROOT, 'js', 'sim.js'), encoding='utf-8').read()
RUNNER = r'''
try{
var M=__M,C=__C,R={plain:{},twin:[]},ITS=Object.keys(M.links).filter(function(k){var l=M.links[k];return l.its&&!l.sink;});
function vf(l){var a=l.nsp?Object.keys(l.nsp).map(function(k){return l.nsp[k];}):[];return a.length?Math.max.apply(null,a):50;}
function occIn(S,k,a,b){var n=0,c=0;S.samp.forEach(function(s){if(s.t>=a&&s.t<=b){n+=(s.occ[k]||0);c++;}});return c?n/c/S.L[k].cap:null;}
function occAt(S,k,T){var n=0,c=0;S.samp.forEach(function(s){if(Math.abs(s.t-T)<=300){n+=(s.occ[k]||0);c++;}});return c?n/c/S.L[k].cap:null;}
C.days.forEach(function(d){var S=tgSim.run(M,{date:d,seed:5,from:16*3600,to:21*3600}),o={};
  ITS.forEach(function(k){o[k]={};C.Ts.forEach(function(T){o[k][T]=occAt(S,k,T);});});R.plain[d]=o;});
C.cases.forEach(function(c){var fill={};ITS.forEach(function(k){var v=c.v[M.links[k].its];if(v==null)return;var f=Math.max(0,Math.min(1,1-v/vf(M.links[k])));tgSim.side(M,k).forEach(function(k2){fill[k2]=Math.max(fill[k2]||0,f);});});
  var S=tgSim.run(M,{date:c.d,seed:5,from:16*3600,to:c.t0+3600+300,init:{at:c.t0,fill:fill}}),o={};
  ITS.forEach(function(k){o[k]={b:occIn(S,k,c.t0+60,c.t0+360)};C.hz.forEach(function(h){o[k][h]=occAt(S,k,c.t0+h);});});
  /* 트윈2 = 채움 + 빼기 — 실측으로 덜 찬 길은 그 길에 줄 선 차를 뒤에서부터 빼 실측 채움까지 낮춘다(엔진 밖에서 · 시험) */
  var S2=tgSim.create(M,{date:c.d,seed:5,from:16*3600,to:c.t0+3600+300,init:{at:c.t0,fill:fill}}),dr=0;S2.runTo(c.t0+1);
  Object.keys(fill).forEach(function(k2){var L=S2.L[k2];if(!L||L.l.sink)return;var ex=Math.round(L.n-fill[k2]*L.cap);if(ex<=0)return;
    Object.keys(S2.mv).forEach(function(mk){var m=S2.mv[mk];if(m.fr!==k2)return;while(ex>0&&m.q.length){var v=m.q.pop();v.te=S2.t;v.gone=1;L.n--;ex--;dr++;}});});
  S2.runTo(S2.end);var o2={};ITS.forEach(function(k){o2[k]={b:occIn(S2,k,c.t0+60,c.t0+360)};C.hz.forEach(function(h){o2[k][h]=occAt(S2,k,c.t0+h);});});
  R.twin.push({d:c.d,t0:c.t0,o:o,o2:o2,ini:S.iniN||0,dr:dr});});
document.getElementById('out').textContent=JSON.stringify(R);
}catch(e){document.getElementById('out').textContent='ERR '+e.stack;}
'''

def run_js(M, C):
    html = ('<!doctype html><meta charset="utf-8"><pre id="out">x</pre><script>window.__M=' + json.dumps(M, ensure_ascii=False).replace('</', '<\\/') +
            ';window.__C=' + json.dumps(C) + ';</script><script>' + JS + '</script><script>' + RUNNER + '</script>')
    d = tempfile.mkdtemp(); p = os.path.join(d, 'tw.html'); open(p, 'w', encoding='utf-8').write(html)
    exe = [c for c in CHROME if os.path.exists(c)][0]
    r = subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=900000', '--user-data-dir=' + os.path.join(d, 'u'),
                        '--dump-dom', 'file:///' + p.replace(os.sep, '/')], capture_output=True, timeout=3600)
    t = re.search(r'<pre id="out">(.*?)</pre>', r.stdout.decode('utf-8', 'replace'), re.S).group(1).replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    if t.startswith('ERR') or t == 'x': raise SystemExit('JS ' + t[:800])
    return json.loads(t)

def new(): return collections.Counter()
def tally(c, sim_j, real_j, chg):
    c['n'] += 1; c['hit'] += sim_j == real_j
    if real_j: c['jn'] += 1; c['jh'] += sim_j
    else: c['fn'] += 1; c['fh'] += not sim_j
    if chg: c['cn'] += 1; c['ch'] += sim_j == real_j

OUT = {'schema': 'tg-twin-shadow/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
       'note': '개념 시연 — 예측·보증 아님 · 트윈 = 그 시각 ITS 실측으로 길을 채우고(Greenshields 채움 · 설계값) 앞을 돌린 시뮬 · 평소 = 실측 없이 평소 수요 · 그대로 = 지금 상태가 이어진다는 어림 · 막힘 = 실측 6km/h 이하 / 시뮬 점유 80% 이상',
       'fields': {'n': '맞대 본 칸(길 × 시각 × 내다본 폭)', 'hit': '맞은 칸', 'jn/jh': '실제 막힘 칸 / 그 가운데 맞힘', 'fn/fh': '실제 안 막힘 칸 / 그 가운데 맞힘', 'cn/ch': '지금과 그 뒤가 달라진 칸 / 그 가운데 맞힘(그대로 어림은 늘 0)'},
       'times': TIMES, 'days': [DAYS[0], DAYS[-1]] if DAYS else [], 'areas': {}}
for nm in AREAS:
    f = os.path.join(ROOT, 'data', 'sim-' + nm + '.json')
    if not os.path.exists(f): print(nm, '구역 자료 없음'); continue
    M = json.load(open(f, encoding='utf-8'))
    its = {l['its'] for l in M['links'].values() if l.get('its') and not l.get('sink')}
    cases, days = [], set()
    for d in DAYS:
        for t0 in TIMES:
            v0 = near(d, t0)
            if not v0 or not any(near(d, t0 + h) for h in HZ): continue
            cases.append({'d': d, 't0': t0, 'v': {k: v0[k] for k in its if k in v0}}); days.add(d)
    if not cases: print(nm, '맞대 볼 실측 없음'); continue
    Ts = sorted({c['t0'] + h for c in cases for h in HZ})
    t_0 = datetime.datetime.now()
    R = run_js(M, {'days': sorted(days), 'Ts': Ts, 'cases': cases, 'hz': list(HZ)})
    S = {v: {h: new() for h in HZ} for v in ('twin', 'twin2', 'plain', 'keep', 'mix')}
    k2its = {k: M['links'][k]['its'] for k in M['links'] if M['links'][k].get('its') and not M['links'][k].get('sink')}
    for c, tw in zip(cases, R['twin']):
        for k, il in k2its.items():
            v0 = c['v'].get(il)
            if v0 is None: continue
            for h in HZ:
                m1 = near(c['d'], c['t0'] + h)
                if not m1 or m1.get(il) is None: continue
                rj, j0 = m1[il] <= JAMV, v0 <= JAMV
                ot, op = tw['o'][k][str(h)], R['plain'][c['d']][k][str(c['t0'] + h)]
                if ot is None or op is None: continue
                o2 = tw['o2'][k][str(h)]
                if o2 is not None: tally(S['twin2'][h], o2 >= 0.8, rj, rj != j0)
                ob = tw['o'][k]['b']
                mix = j0 if ob is None or (ob >= 0.8) == (ot >= 0.8) else ot >= 0.8   # 섞음 = 지금 실측 상태에서 출발해 시뮬이 「바뀐다」고 할 때만 바꿈
                tally(S['twin'][h], ot >= 0.8, rj, rj != j0); tally(S['plain'][h], op >= 0.8, rj, rj != j0); tally(S['keep'][h], j0, rj, rj != j0); tally(S['mix'][h], mix, rj, rj != j0)
    OUT['areas'][nm] = {'nm': M.get('nm'), 'cases': len(cases), 'sec': round((datetime.datetime.now() - t_0).total_seconds()),
                        'score': {v: {str(h // 60): dict(S[v][h]) for h in HZ} for v in S}}
    def pct(c): return '%d/%d' % (c['hit'], c['n']) + ('·막힘%d/%d' % (c['jh'], c['jn']) if c['jn'] else '') + ('·바뀜%d/%d' % (c['ch'], c['cn']) if c['cn'] else '')
    print(nm, len(cases), '판', OUT['areas'][nm]['sec'], '초 |', ' | '.join('%s %d분 %s' % (v, h // 60, pct(S[v][h])) for h in HZ for v in ('twin', 'twin2', 'plain', 'keep', 'mix')), flush=True)

tot = {v: {str(h // 60): sum((collections.Counter(a['score'][v][str(h // 60)]) for a in OUT['areas'].values()), collections.Counter()) for h in HZ} for v in ('twin', 'twin2', 'plain', 'keep', 'mix')}
OUT['total'] = {v: {h: dict(c) for h, c in d.items()} for v, d in tot.items()}
dst = os.path.join(ROOT, 'data', 'twin-shadow.json') if not os.environ.get('TWIN_DRY') else os.path.join(tempfile.gettempdir(), 'twin-shadow.json')
json.dump(OUT, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('→', dst); print(json.dumps(OUT['total'], ensure_ascii=False))
