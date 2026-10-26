# -*- coding: utf-8 -*-
# 시뮬 시나리오 → 온톨로지(2026-10-26 · 소유자 「권하는 차례대로 진행」 1번 — 시뮬 결과를 온톨로지 대상으로 남기기)
#   반포 터미널 블록(손으로 짠 구역)의 대책을 머리 없는 크롬에서 같은 날·같은 차(씨앗 7)로 돌려 현행과 견준 결과를 data/sim-scenarios.json 에 적는다.
#   자동 구역(서초역 등)은 돌리지 않고 「평소 재현」 한 줄 — 평소 속도와 맞대 본 맞음(data/sim-areas.json)만 옮긴다.
#   ontology-core/build.py 가 이 파일을 읽어 SCN 객체(시나리오)를 만들고 교차로(INT · C-ITS 번호)·현장 판단(FK)에 잇는다 — 등급 D(추정 · 개념 시연).
#   값은 모두 이 실행에서 나온 것 · 수요(신세계·고속버스 증차 몫)는 설계값 · 예측·보증 아님.
# 쓰기: py -3.12 -X utf8 tools/sim/scenario-bake.py   (js/sim.js · data/sim-banpo.json 을 고치면 다시)
import os, re, json, subprocess, tempfile, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
CH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
js = open(os.path.join(ROOT, 'js', 'sim.js'), encoding='utf-8').read()
dg = open(os.path.join(ROOT, 'tools', 'sim', 'sim-diag.js'), encoding='utf-8').read()
M = open(os.path.join(D, 'sim-banpo.json'), encoding='utf-8').read()
VER = re.search(r'sim\.js\?v=(\d+)', open(os.path.join(ROOT, 'js', 'sim-ui.js'), encoding='utf-8').read()).group(1)

T = r'''
var out = [], P18 = __M.preset['1018'].att, D18 = '2026-10-18', NODES = ['4031', '4019', '4028', '4034'];
function res(r) { return { delayVh: r.delayVh, trappedMax: r.trappedMax, box: r.box, jamStart: r.jamStart, clearT: r.clearT, jamMax: r.jamMax }; }
function runS(m, sc, alt, drop, from) { var S = tgSim.create(m, sc, alt); S.runTo(S.from); var dd = false; while (S.t < S.end) { if (drop && !dd && S.t >= from) { S.drop['4031'] = drop; dd = true; } S.step(); } return S.result(); }
function base(date, att, extra) { return Object.assign({ date: date, seed: 7, att: att, from: 16 * 3600, to: 23 * 3600 }, extra || {}); }
function A2(f) { var a = JSON.parse(JSON.stringify(P18)); f(a); return a; }
var dow = 0, offF = tgSim.planAt(__M, '4031', 17 * 3600, dow).off;
var F = [{ d: 40, y: 4, ar: 1, mv: ['wt.St', 'et.St'] }, { d: 26, y: 4, ar: 1, mv: ['et.St'] }, { d: 26, y: 4, ar: 1, mv: ['wt.Lt'] }, { d: 28, y: 3, ar: 1, mv: ['nt.St', 'nt.Lt'] }, { d: 32, y: 3, ar: 1, mv: ['nt.St', 'st.St'] }, { d: 28, y: 3, ar: 1, mv: ['st.St', 'st.Lt'] }];
function altExit(sec) { var o = {}; [['4019', 'wt'], ['4028', 'nt'], ['4034', 'et'], ['4031', 'st']].forEach(function (x) { var Pl = tgSim.planAt(__M, x[0], 18 * 3600, dow), ph = Pl.ph.map(function (p) { return { d: p.d, y: p.y, ar: p.ar, mv: p.mv.slice() }; });
  var i = -1, j = -1, bd = 0; ph.forEach(function (p, k) { var has = p.mv.some(function (m) { return m.indexOf(x[1] + '.') === 0; }); if (has && i < 0) i = k; if (!has && p.d > bd) { bd = p.d; j = k; } }); if (i < 0 || j < 0) return; ph[i].d += sec; ph[j].d -= sec; o[x[0]] = { ph: ph, off: Pl.off, t0: 16 * 3600, t1: 21 * 3600 }; }); return o; }
function ph4(a, b, c, d) { return [{ d: a, y: 4, ar: 1, mv: ['wt.St', 'et.St'] }, { d: b, y: 4, ar: 1, mv: ['wt.St', 'wt.Lt'] }, { d: c, y: 3, ar: 1, mv: ['nt.St', 'nt.Lt'] }, { d: d, y: 3, ar: 1, mv: ['st.St', 'st.Lt'] }]; }
var offR = tgSim.planAt(__M, '4031', 19 * 3600, dow).off, REAL = { '4031': [{ t0: 19 * 3600, t1: 20 * 3600, ph: ph4(90, 46, 42, 95), off: offR }, { t0: 20 * 3600, t1: 21 * 3600, ph: ph4(50, 54, 33, 101.5), off: offR }, { t0: 21 * 3600, t1: 22 * 3600, ph: ph4(57, 40, 57.5, 119), off: offR }] };
var b0 = runS(__M, base(D18, P18), null), c0 = __cmp('1018');
function scn(id, nm, how, fk, r, extra) { out.push(Object.assign({ id: id, area: 'banpo', date: D18, nm: nm, how: how, nodes: NODES, fk: fk, base: res(b0), res: res(r) }, extra || {})); }
out.push({ id: 'SCN-banpo-1018-replay', area: 'banpo', date: D18, nm: '10/18(일) 재현 — 계획 신호', how: '신세계 입·출 1,200대/시 · 분수 600대/시 · 고속버스 시간표 × 1.15(설계값) · 교통과 현시도·T-Data 계획 신호', nodes: NODES, fk: ['FK-BLOCK-GATE4', 'FK-BLOCK-PARK', 'FK-BLOCK-WEAVE', 'FK-BLOCK-WGATE', 'FK-BLOCK-SGATE'], res: res(b0), match: { hit: c0.hit, n: c0.n, what: 'ITS 실측 속도 — 접근로 11 × 16~22시 · 막힘 = 5km/h 이하 · 시뮬 80% 넘게 참' } });
var cR = __cmp('1018', REAL); out.push({ id: 'SCN-banpo-1018-realsig', area: 'banpo', date: D18, nm: '10/18(일) 재현 — 실제 돈 신호(T-Data 19~22시)', how: '4031 주기 273·238.5·273.5초(T-Data 기록 · se = 남쪽으로 읽음 · 21시 북쪽 녹색은 남는 시간으로 가정) — 소유자 수동 조작의 흔적으로 보임(날짜 확인 전)', nodes: NODES, fk: [], base: res(b0), res: res(cR.R), match: { hit: cR.hit, n: cR.n, what: 'ITS 실측 속도 — 접근로 11 × 16~22시' } });
scn('SCN-banpo-1018-ltcut', '🤖 좌회전(반포대교→신세계)만 막기 — 점유 85% 넘으면', '4031 북→동 좌회전만 적색 · 차례는 그대로 · 60% 아래면 풀기(설계값)', ['FK-BLOCK-LTCUT'], runS(__M, base(D18, P18, { autoCut: { node: '4031', link: '4031>G', hi: 0.85, lo: 0.6, every: 5, cut: ['nt.Lt'], mode: 'drop' } }), null));
scn('SCN-banpo-1018-twocut', '두 진입 끊기(반포대교→좌 + 신반포로 서→동) 16시부터', '4031 북→동 좌회전·서→동 직진 적색 · 차례 그대로 — 소유자 「끊었는데 5시간 서 있었다」의 재현', ['FK-BLOCK-INFLOW'], runS(__M, base(D18, P18), null, ['nt.Lt', 'wt.St'], 16 * 3600));
scn('SCN-banpo-1018-planF', 'F 형님 안 — 4031 여섯 현시(16~21시)', '주기 180 · 양직 40 → 동 직진 26 → 서 좌 26 → 북 직좌 28 → 남북 양직 32 → 남 직좌 28(초는 설계값)', ['FK-BLOCK-INFLOW'], runS(__M, base(D18, P18), { '4031': { ph: F, off: offF, t0: 16 * 3600, t1: 21 * 3600 } }));
scn('SCN-banpo-1018-exit10', '출구 녹색 +10초(4019 서·4028 북·4034 동·4031 남)', '그 접근로 현시 +10초 · 가장 긴 다른 현시 −10초 · 16~21시', [], runS(__M, base(D18, P18), altExit(10)));
scn('SCN-banpo-1018-shin70', '신세계 입·출 30% 줄임', '신세계 1,200 → 840대/시(설계값)', ['FK-BLOCK-INFLOW'], runS(__M, base(D18, A2(function (a) { a.shin.inPeak *= 0.7; a.shin.outPeak *= 0.7; })), null));
scn('SCN-banpo-1018-nobus', '고속버스 증차 없음', '고속버스 시간표 × 1.0(재현은 × 1.15)', ['FK-BLOCK-INFLOW'], runS(__M, base(D18, A2(function (a) { a.busGB.scale = 1; a.busCT.scale = 1; })), null));
var wd = base('2026-10-21', undefined, { from: 15 * 3600, to: 20 * 3600 }), w0 = runS(__M, wd, null), w1 = runS(__M, Object.assign({ act: ['noTw4034'] }, wd), null);
out.push({ id: 'SCN-banpo-wd-notw4034', area: 'banpo', date: '2026-10-21', nm: '평일 서울성모병원 시차제 끄고 보기', how: '4034 평일 16~20시 서→동 직진 23초(현시도 tw) 끄기 — ⚠ 현장은 시차제로 「많이 개선」(FK-4034-METER) · 이 시뮬은 반대로 나와 시뮬이 틀린 것으로 본다', nodes: ['4034', '4028'], fk: ['FK-4034-METER'], base: res(w0), res: res(w1), conflict: '현장 결과와 반대' });
document.getElementById('out').textContent = JSON.stringify(out);'''

html = '<!doctype html><meta charset="utf-8"><pre id="out">x</pre><script>window.__DIAG=0;window.__M=' + M.replace('</', '<' + chr(92) + '/') + ';</script><script>' + js + '</script><script>' + dg + '</script><script>' + T + '</script>'
d = tempfile.mkdtemp(); p = os.path.join(d, 'x.html'); open(p, 'w', encoding='utf-8').write(html)
r = subprocess.run([CH, '--headless=new', '--disable-gpu', '--virtual-time-budget=1200000', '--user-data-dir=' + os.path.join(d, 'u'), '--dump-dom', 'file:///' + p.replace(os.sep, '/')], capture_output=True, timeout=1500)
raw = re.search(r'<pre id="out">(.*?)</pre>', r.stdout.decode('utf-8', 'replace'), re.S).group(1)
raw = raw.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
S = json.loads(raw)
for a in json.load(open(os.path.join(D, 'sim-areas.json'), encoding='utf-8'))['areas']:
    S.append({'id': 'SCN-%s-usual' % a['id'], 'area': a['id'], 'date': a.get('calDay'), 'nm': a['nm'] + ' — 평소(평일 16~21시) 재현', 'how': '자동으로 엮은 구역(tools/sim/area-bake.py) · 수요는 평소 속도로 맞춘 배율(설계값)', 'nodes': [s[0] for s in a['sig']], 'fk': [],
              'match': {'hit': a.get('mh'), 'n': a.get('mn'), 'jam_hit': a.get('jh'), 'jam_n': a.get('jn'), 'what': '평소 속도(ITS 가운데값)와 맞대 본 접근로·시간 칸 · 실측 막힘 칸 가운데 시뮬도 막힘'}})
J = {'schema': 'tg-sim-scn/1', 'made': datetime.datetime.now().isoformat(timespec='seconds'), 'engine': 'js/sim.js?v=' + VER,
     'source': 'tools/sim/scenario-bake.py ← js/sim.js · data/sim-banpo.json · data/sim-areas.json (머리 없는 크롬 · 씨앗 7 · 같은 날 같은 차)',
     'fields': {'id': 'SCN-<구역>-<날>-<대책>', 'nodes': '시뮬 교차로 번호(C-ITS·T-Data 번호 = 온톨로지 INT 의 cits)', 'fk': '근거가 된 소유자 현장 판단(onto-rules field id)', 'base': '같은 날 현행(계획 신호) 결과', 'res': '그 대책 결과',
                'delayVh': '총 지체(대·시)', 'trappedMax': '블록 안에 갇힌 차 최대(대)', 'box': '꼬리물기(교차로 안에 선 차 누적)', 'jamStart/clearT': '막힘 시작·풀림(자정부터 초 · 막힘 = 신호 접근로 가운데 80% 넘게 찬 곳 3곳 이상)', 'match': '실측과 맞대 본 맞음'},
     'note': '개념 시연 — 예측·보증 아님 · 수요(신세계·고속버스 증차 몫)는 설계값 · 현장 결과가 이긴다(conflict 칸)', 'scenarios': S}
json.dump(J, open(os.path.join(D, 'sim-scenarios.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
for s in S:
    r9 = s.get('res') or {}; b9 = s.get('base') or {}
    print(s['id'], '| 지체', b9.get('delayVh'), '→', r9.get('delayVh'), '| 꼬리', b9.get('box'), '→', r9.get('box'), '| 맞음', (s.get('match') or {}).get('hit'), '/', (s.get('match') or {}).get('n'))
