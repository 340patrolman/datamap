/* 🧪 시뮬 — 블록 전체(2026-10-25 · intent/20261025-banpo-block-sim.md 3단계 · 소유자 「고속터미널 인근 성모병원·고속터미널·삼호가든 등 비슷한 위치가 되면 시뮬 메뉴가 보이게 · 잘 되면 서울 전역으로」)
   지도(map2d.js)는 고치지 않는다 — 카드(#m2dCard)를 지켜보다 블록 교차로 카드에 단추를 덧붙이고, 지도 가운데가 블록 둘레면 떠 있는 단추를 띄운다(TGMap2D.view·LL 만 읽음).
   계산은 js/sim.js(window.tgSim · 처음 열 때 받음) · 구역 자료 data/sim-banpo.json · 개념 시연이다 — 예측·보증이 아니다(판 아래에 늘 적는다).
   이름 = 「🧪 시뮬」(소유자 2026-10-25 · T-Book 홈 「시뮬레이션」·게임 「🧪 시뮬 — 한 교차로」와 한 갈래) */
(function () {
  'use strict';
  var AREA = { id: 'banpo', nm: '반포 터미널 블록', c: [37.5048, 127.0058], r: 900,
    names: /고속터미널|강남터미널고가밑|삼호가든|서울성모병원|반포대교남단|반포쇼핑타운|센트럴시티|신세계/,
    q4: [[37.504998, 127.001109], [37.507432, 127.009026], [37.504767, 127.010387], [37.502112, 127.003441]],   // 4031 → 4019 → 4028 → 4034(시계 방향)
    // 출입구 4곳 — 소유자 현장 지식(2026-10-25) · 자리는 변 가운데 근사 · 블록 쪽 차로에서 오른쪽으로 드나든다 → 사각형을 시계 방향으로 빙 돈다
    doors: [{ id: 'N', ic: '🅿', nm: '신반포로 — 백화점', ll: [37.506215, 127.005068] }, { id: 'E', ic: '🚌', nm: '잠원로 — 경부·영동선 고속버스·백화점', ll: [37.5061, 127.009707] },
      { id: 'S', ic: '🏨', nm: '사평대로 — 메리어트·백화점 들어가는 곳(3번 출구 쪽)', ll: [37.503094, 127.006011] },
      { id: 'So', ic: '⤴', nm: '사평대로 — 메리어트·백화점 나오는 곳(동그라미 건물 옆길)', ll: [37.502696, 127.004969] }, { id: 'W', ic: '🚌', nm: '반포대로 — 호남선·백화점 들어가는 곳', ll: [37.503699, 127.002158] },
      { id: 'Wo', ic: '⤴', nm: '반포대로 — 호남선 버스·백화점 나오는 곳', ll: [37.504421, 127.001575] }],   /* 서쪽 문 = 소유자 현장 지식(2026-10-25) — 반포사거리(4031)에서 나오는 곳 20% · 들어가는 곳 45% · 겹치지 않음 */
    // 막힘 고리 네 변(data/onto-loops.json LOOP-banpo-terminal 과 같은 차례) — 지금 ITS 속도를 받는 링크 · 시뮬 길 · 신반포로는 4031→4019 470m 링크(1210026104)가 ITS 에 안 와서 앞 224m 조각
    legs: [{ nm: '신반포로 →고속터미널', its: '1210026102', sim: '4031>G' }, { nm: '잠원로 →삼호가든', its: '1210026203', sim: '4019>4028' }, { nm: '사평대로 →서울성모병원', its: '1210024802', sim: 'SO>4034' }, { nm: '반포대로 →반포사거리', its: '1210025103', sim: 'WO>4031' }] };
  var SHORT = { '4031': '반포사거리', '4019': '고속터미널', '4028': '삼호가든', '4034': '서울성모병원', '4032': '반포대교남단' };
  var M = null, A = null, B = null, RUN = 0, SPD = 600, LAST = 0, PANEL = null, CH = null, ST = null;
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function hh(t) { if (t == null) return '-'; var h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60); return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m; }
  function css() {
    if ($('simCss')) return; var s = document.createElement('style'); s.id = 'simCss';
    s.textContent = '#m2dSimChip{position:fixed;left:50%;transform:translateX(-50%);top:calc(var(--toph,110px) + 10px);z-index:7;border:0;border-radius:22px;padding:10px 16px;font:800 14px/1.2 inherit;background:#7c3aed;color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.3);cursor:pointer;display:none}' +
            '#m2dSim{position:fixed;left:0;right:0;bottom:0;z-index:25;max-height:90%;overflow:auto;display:none;background:var(--panel,#fff);color:var(--ink,#111);border-radius:18px 18px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,.35);padding:10px 10px calc(14px + env(safe-area-inset-bottom));font-size:13px}' +
      '@media (min-width:900px){#m2dSim{left:auto;right:12px;bottom:12px;width:760px;max-height:calc(100% - 90px);border-radius:16px}}' +
      '#m2dSim.on{display:block}#m2dSim h3{margin:0 0 2px;font-size:16px;display:flex;align-items:center;gap:6px}#m2dSim h3 button{margin-left:auto}' +
      '#m2dSim .sn{color:var(--ink2,#555);font-size:12px;line-height:1.4;margin:2px 0 6px}#m2dSim .sg{font-weight:800;font-size:12px;color:var(--ink2,#555);margin:8px 0 3px}' +
      '#m2dSim button{font:inherit;border:1px solid rgba(120,130,150,.45);background:transparent;color:inherit;border-radius:14px;padding:6px 10px;min-height:34px;cursor:pointer}#m2dSim button.on{background:#7c3aed;border-color:#7c3aed;color:#fff}' +
      '#m2dSim .row{display:flex;flex-wrap:wrap;gap:5px;align-items:center}#m2dSim label.sl{display:flex;align-items:center;gap:6px;width:100%;margin:2px 0}#m2dSim label.sl input{flex:1}#m2dSim label.sl b{min-width:118px;font-size:12px}#m2dSim label.sl em{font-style:normal;min-width:62px;text-align:right;font-variant-numeric:tabular-nums}' +
      '#m2dSim .two{display:grid;grid-template-columns:1fr 1fr;gap:6px}#m2dSim .two.big{grid-template-columns:1fr}#m2dSim .pv{border:1px solid rgba(120,130,150,.35);border-radius:12px;padding:4px}#m2dSim .pv .pt{font-weight:800;font-size:13px;text-align:center}#m2dSim .pv svg{width:100%;height:auto;display:block}' +
      '#m2dSim .pv .pi{font-size:11.5px;line-height:1.45;font-variant-numeric:tabular-nums}#m2dSim table{border-collapse:collapse;width:100%;font-size:12.5px}#m2dSim td,#m2dSim th{border-bottom:1px solid rgba(120,130,150,.25);padding:4px 3px;text-align:right}#m2dSim td:first-child,#m2dSim th:first-child{text-align:left}' +
      '#m2dSim .ph{display:flex;align-items:center;gap:4px;margin:2px 0;font-size:12px}#m2dSim .ph span{flex:1}#m2dSim .ph button{min-height:28px;padding:2px 8px}#m2dSim .warn{background:rgba(234,179,8,.15);border-radius:10px;padding:6px 8px;font-size:12px;line-height:1.45;margin:6px 0}' +
      '#m2dSim details summary{cursor:pointer;font-weight:700;font-size:12px;color:var(--ink2,#555);margin-top:6px}#m2dSim .clock{font-size:20px;font-weight:900;font-variant-numeric:tabular-nums}';
    document.head.appendChild(s);
  }
  // ---- 어디서 보일까: 블록 교차로 카드 · 지도 가운데가 블록 둘레 ----
  function cardHook() {
    var c = $('m2dCard'); if (!c || !window.MutationObserver) return;
    new MutationObserver(function () {
      if (!c.classList.contains('on') || c.querySelector('[data-simblk]')) return;
      var h = c.querySelector('h3'); if (!h || !AREA.names.test(h.textContent || '')) return;
      var bx = c.querySelector('.lg-btns') || c.querySelector('.dhb');
      var b = document.createElement('button'); b.setAttribute('data-simblk', AREA.id); b.title = '만약 신호·수요·라바콘을 바꾸면? — ' + AREA.nm + '(교차로 넷)을 16~22시 두 판으로 견준다 · 개념 시연';
      b.textContent = '🧪 시뮬 — 블록 전체'; b.style.cssText = 'background:#7c3aed;color:#fff;border-color:#7c3aed';
      b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); open(); };
      if (bx) bx.appendChild(b); else h.insertAdjacentElement('afterend', b);
    }).observe(c, { childList: true, subtree: false, attributes: true, attributeFilter: ['class'] });
  }
  function near() {
    var T = window.TGMap2D; if (!T || !T.view || !T.LL) return false;
    var c0 = T.LL(AREA.c[1], AREA.c[0]), e0 = T.LL(AREA.c[1] + 0.01, AREA.c[0]), mpu = 883 / Math.max(1e-9, Math.abs(e0[0] - c0[0]));   // 경도 0.01° ≈ 883m(위도 37.5)
    var d = Math.hypot(T.view.cx - c0[0], T.view.cy - c0[1]) * mpu; return d < AREA.r && T.view.s > 0.12;
  }
  /* 지도 위 표시 — 블록 둘레를 보고 있으면 출입구 4곳과 블록 쪽 차로가 도는 방향(시계 방향)을 지도에 겹쳐 그린다(소유자 「지도상에 그렇게 있다고 표현해 주고」)
     map2d.js 는 안 고친다 — TGMap2D.S(지도 → 화면)·LL 로 자리만 받아 따로 띄운 SVG 에 그린다 · 출입구를 누르면 시뮬 판이 열린다 */
  var OV = null;
  function ovPaint() {
    var T = window.TGMap2D, cv = document.querySelector('#m2d canvas') || document.querySelector('canvas'); if (!OV || !T || !T.S || !cv) return;
    var show = near() && T.view.s > 0.2; OV.style.display = show ? 'block' : 'none'; if (!show) return;
    var r = cv.getBoundingClientRect(), xy = function (ll) { var q = T.S(T.LL(ll[1], ll[0])); return [r.left + q[0], r.top + q[1]]; }, Q = AREA.q4.map(xy), c = [Q.reduce(function (a, p) { return a + p[0]; }, 0) / 4, Q.reduce(function (a, p) { return a + p[1]; }, 0) / 4];
    var h = '<defs><marker id="simOvA" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#7c3aed"/></marker></defs>';
    var In = function (p, k) { return [p[0] + (c[0] - p[0]) * k, p[1] + (c[1] - p[1]) * k]; }, P2 = Q.map(function (p) { return In(p, 0.12); });
    h += '<polygon points="' + P2.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ') + '" fill="rgba(124,58,237,.07)" stroke="#7c3aed" stroke-width="2" stroke-dasharray="6 5"/>';
    for (var i = 0; i < 4; i++) { var a = P2[i], b = P2[(i + 1) % 4]; [0.22, 0.72].forEach(function (t) { var x1 = a[0] + (b[0] - a[0]) * t, y1 = a[1] + (b[1] - a[1]) * t, x2 = a[0] + (b[0] - a[0]) * (t + 0.08), y2 = a[1] + (b[1] - a[1]) * (t + 0.08); h += '<line x1="' + x1.toFixed(1) + '" y1="' + y1.toFixed(1) + '" x2="' + x2.toFixed(1) + '" y2="' + y2.toFixed(1) + '" stroke="#7c3aed" stroke-width="3" marker-end="url(#simOvA)"/>'; }); }
    AREA.doors.forEach(function (d) { var p = In(xy(d.ll), 0.12); h += '<g data-simdoor="' + d.id + '" style="pointer-events:auto;cursor:pointer"><circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="13" fill="#7c3aed" stroke="#fff" stroke-width="2"/><text x="' + p[0].toFixed(1) + '" y="' + (p[1] + 5).toFixed(1) + '" font-size="13" text-anchor="middle">' + d.ic + '</text><text x="' + p[0].toFixed(1) + '" y="' + (p[1] + 27).toFixed(1) + '" font-size="11" font-weight="800" text-anchor="middle" fill="#4c1d95" stroke="#fff" stroke-width="3" paint-order="stroke">출입구 · ' + esc(d.nm) + '</text></g>'; });
    h += '<text x="' + c[0].toFixed(1) + '" y="' + (c[1] + 4).toFixed(1) + '" font-size="12" font-weight="800" text-anchor="middle" fill="#4c1d95" stroke="#fff" stroke-width="3" paint-order="stroke">신세계·고속터미널 블록 — 출입구 4곳 · 시계 방향으로 빙 돈다</text>';
    OV.innerHTML = h;
  }
  function overlay() {
    OV = document.createElementNS('http://www.w3.org/2000/svg', 'svg'); OV.id = 'm2dSimOv'; OV.setAttribute('aria-label', '반포 터미널 블록 출입구 4곳'); OV.style.cssText = 'position:fixed;left:0;top:0;width:100%;height:100%;pointer-events:none;z-index:4;display:none';
    document.body.appendChild(OV); OV.addEventListener('click', function (e) { var g = e.target.closest && e.target.closest('[data-simdoor]'); if (g) open(); });
    var last = ''; (function loop() { var T = window.TGMap2D, k = T && T.view ? [T.view.cx.toFixed(1), T.view.cy.toFixed(1), T.view.s.toFixed(4), innerWidth, innerHeight].join() : ''; if (k !== last) { last = k; ovPaint(); } setTimeout(function () { requestAnimationFrame(loop); }, 120); })();
  }
  function chip() {
    CH = document.createElement('button'); CH.id = 'm2dSimChip'; CH.textContent = '🧪 시뮬 — ' + AREA.nm; CH.title = '신호·수요·라바콘을 바꿔 두 판으로 견준다(개념 시연)';
    CH.onclick = function () { open(); }; document.body.appendChild(CH);
    setInterval(function () { var cd = $('m2dCard'), v = near() && !(PANEL && PANEL.classList.contains('on')) && !(cd && cd.classList.contains('on') && cd.querySelector('[data-simblk]'));   /* 카드에 이미 단추가 있으면 떠 있는 단추는 숨김 */ CH.style.display = v ? 'block' : 'none'; }, 800);
  }
  // ---- 지금 ITS 실측(네 변) — data/live-spd-six.json(약 10분마다 · 20분 넘으면 판정 안 함) · 평소 = spd-normal-six 같은 요일 갈래·시각 가운데값 ----
  var LIVE = null, NORM = null, LOOP = null, APRS = null;
  // 네 변의 링크는 지도 엮임 보기와 같은 곳에서 — data/onto-loops.json legs(links 가 있으면 그것) → 없으면 apr(「APR-교차로-들어오는 쪽」)를 data/sig-approach-seocho.json 에서 풀어 그 길의 ITS 링크들(길이 가중) · 둘 다 못 읽으면 AREA.legs 의 링크 하나
  function legLinks(i) {
    var g = LOOP && LOOP.legs && LOOP.legs[i];
    if (g && g.links && g.links.length) return g.links.map(function (x) { return [x, 1]; });
    if (g && g.apr && APRS) { var q = g.apr.split('-'), sp = APRS.spots && APRS.spots[q[1]], r = sp && sp.in && sp.in[q[2]] && sp.in[q[2]][0]; if (r && r[4]) return r[4]; }
    return [[AREA.legs[i].its, 1]];
  }
  function legSpd(i, M9) { var L = legLinks(i), w = 0, sm = 0, first = null; L.forEach(function (x) { var v = M9[x[0]]; if (v == null) return; if (first == null) first = v; sm += v * x[1]; w += x[1]; }); return LOOP && LOOP.legs && LOOP.legs[i] && LOOP.legs[i].links ? first : w ? Math.round(sm / w) : null; }   // links 는 「있으면 먼저」 차례 · apr 길은 길이 가중
  function liveGet() {
    fetch('data/onto-loops.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { LOOP = j && (j.loops || []).filter(function (x) { return x.sim === AREA.id; })[0] || null; paintLive(); }).catch(function () {});
    fetch('data/sig-approach-seocho.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { APRS = j; paintLive(); }).catch(function () {});
    fetch('data/live-spd-six.json?t=' + Math.floor(Date.now() / 300000)).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { LIVE = j; paintLive(); }).catch(function () {});
    fetch('data/spd-normal-six/11650.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { NORM = j; paintLive(); }).catch(function () {});
  }
  function paintLive() {
    var el = $('simLive'); if (!el) return; if (!LIVE || !LIVE.m) { el.innerHTML = ''; return; }
    var age = (Date.now() / 1000 - LIVE.at) / 60, now = new Date(), dk = [3, 0, 0, 0, 0, 1, 2][now.getDay()], hk = dk + '-' + now.getHours(), jamR = 0, nR = 0;
    var cells = AREA.legs.map(function (g, i) { var v = legSpd(i, LIVE.m), NM = {}; if (NORM && NORM.links) legLinks(i).forEach(function (x) { var q = NORM.links[x[0]] && NORM.links[x[0]][hk]; if (q) NM[x[0]] = q[0]; }); var nv0 = legSpd(i, NM), nv = nv0 != null ? [nv0] : null; if (v != null) { nR++; if (v <= 5) jamR++; }
      return '<span style="white-space:nowrap">' + esc(g.nm) + ' <b style="color:' + (v == null ? 'inherit' : v <= 5 ? '#dc2626' : v <= 12 ? '#ca8a04' : '#16a34a') + '">' + (v == null ? '값 없음' : v + 'km/h') + '</b>' + (nv ? ' <small>(평소 ' + nv[0] + ')</small>' : '') + '</span>'; }).join(' · ');
    var cmp = '';
    if (A && age <= 20) { var t9 = now.getHours() * 3600 + now.getMinutes() * 60, sm = null; A.samp.forEach(function (x) { if (Math.abs(x.t - t9) < 60) sm = x; });
      var today = [3, 0, 0, 0, 0, 1, 2][window.tgSim.dowOf(ST.date)] === dk;
      if (sm && today) { var hit = 0, nn = 0; AREA.legs.forEach(function (g, i) { var v = legSpd(i, LIVE.m); if (v == null) return; nn++; var sj = sm.occ[g.sim] >= 0.8 * A.L[g.sim].cap; if (sj === (v <= 5)) hit++; }); cmp = '<br>지금 시각(' + hh(t9) + ') 시뮬 현행 판과 맞대 봄 — 네 변 가운데 <b>' + hit + '/' + nn + '</b> 맞음(막힘 = 실측 5km/h 이하 · 시뮬 80% 넘게 참)'; }
      else if (!today) cmp = '<br><small>지금 요일 갈래와 고른 날이 달라 시각별로 맞대 보지 않는다 — 오늘 요일을 고르면 맞대 본다</small>'; else cmp = '<br><small>시뮬 시계가 지금 시각(' + hh(t9) + ')에 닿으면 맞대 본다(16~23시)</small>'; }
    el.innerHTML = '<div class="sn" style="color:inherit;background:rgba(14,165,233,.08);border-radius:10px;padding:6px 8px">📡 <b>지금 실측</b>(ITS · ' + hh(new Date(LIVE.at * 1000).getHours() * 3600 + new Date(LIVE.at * 1000).getMinutes() * 60) + (age > 20 ? ' · <b style="color:#dc2626">' + Math.round(age) + '분 지남 — 판정 안 함</b>' : '') + ') 막힘 고리 네 변: ' + cells + (nR ? ' — 막힌 변 ' + jamR + '/' + nR : '') + cmp + '</div>';
  }
  // ---- 받기 ----
  function need(cb) {
    if (M && window.tgSim) return cb();
    var go = function () { window.tgSim.load(AREA.id, '7').then(function (j) { M = j; cb(); }).catch(function () { alert('시뮬 자료를 받지 못했다 — 통신을 확인하고 다시'); }); };
    if (window.tgSim) return go();
    var s = document.createElement('script'); s.src = 'js/sim.js?v=21'; s.onload = go; s.onerror = function () { alert('시뮬 계산기(sim.js)를 받지 못했다'); }; document.head.appendChild(s);
  }
  // ---- 판 ----
  var DAYS = [['1018', '10/18(일) 재현', '2026-10-18'], ['1011', '10/11(일) 평소', '2026-10-11'], ['mt', '평일(월~목)', '2026-10-21'], ['fr', '금요일', '2026-10-23'], ['sa', '토요일', '2026-10-24'], ['su', '일요일', '2026-10-25']];   // 소유자 「평일·금·토·일도 변수로」 — 신호 계획·고속버스 시간표·평소 속도 모두 이 네 갈래
  function presetOf(k) { var P = M.preset || {}; return P[k] ? JSON.parse(JSON.stringify(P[k])) : null; }
  function att0(id) { return (M.att || []).filter(function (a) { return a.id === id; })[0] || {}; }
  function defState() {
    var p = presetOf('1018') || {};
    return { day: '1018', date: p.date || '2026-10-18', shin: (p.att && p.att.shin && p.att.shin.inPeak) || att0('shin').inPeak, fount: (p.att && p.att.fount && p.att.fount.inPeak) || att0('fount').inPeak,
      academy: att0('academy').inPeak || 0, occ: Math.round((att0('shin').occ0 != null ? att0('shin').occ0 : 0.5) * 100), bus: 1, act: {}, box: true, plan: 'A', ph: null, manual: false, auto: false, manF: false };
  }
  function exPhases() {   // 재편안 예시 — 의도 문서 「직진·좌회전 분리 · 측도 남북 양직진 · 출구 연장 현시」 · 주기는 현행(일 16~21시 패턴 14 · 180초)과 같게 · 초는 형님이 고친다
    return [{ d: 40, y: 4, ar: 1, mv: ['wt.St', 'et.St'], nm: '동서 양직진' }, { d: 30, y: 4, ar: 1, mv: ['et.St', 'wt.Lt'], nm: '출구 연장(동→서 직진 계속 · 서→북 좌회전) — 들어오는 차 끊김' },
      { d: 45, y: 3, ar: 1, mv: ['nt.St', 'st.St'], nm: '남북 양직진(측도)' }, { d: 30, y: 3, ar: 1, mv: ['nt.Lt'], nm: '북 좌회전(블록으로 들어감)' }, { d: 35, y: 3, ar: 1, mv: ['st.Lt'], nm: '남 좌회전' }];
  }
  function scen() {
    var act = Object.keys(ST.act).filter(function (k) { return ST.act[k]; });
    var a = { shin: { inPeak: ST.shin, outPeak: ST.shin, occ0: ST.occ / 100 }, fount: { inPeak: ST.fount }, academy: { inPeak: ST.academy }, busGB: { scale: ST.bus, off: ST.bus ? 0 : 1 }, busCT: { scale: ST.bus, off: ST.bus ? 0 : 1 } };
    return { date: ST.date, seed: 7, att: a, act: act, box: ST.box ? undefined : 0, from: 16 * 3600, to: 23 * 3600, keepWarm: 1 };
  }
  /* 개선안 목록(4031 반포사거리 · 소유자 「신호값별로 어떤 변화가 생길 수 있는지 — 개선안별로 시연」) — 현행은 그날 17시 현시도 계획 · 나머지는 그것을 고친 예시(초는 형님이 정한다) */
  function curPh() { return window.tgSim.planAt(M, '4031', 17 * 3600, window.tgSim.dowOf(ST.date)).ph.map(function (p) { return { d: p.d, y: p.y, ar: p.ar, mv: p.mv.slice(), nm: p.mv.join('+') }; }); }
  function plans() {
    var c = curPh(), K = function (f) { var q = JSON.parse(JSON.stringify(c)); f(q); return q; }, ex = exPhases(), exB = JSON.parse(JSON.stringify(ex)); exB[0].d -= 15; exB[1].d += 15;
    return [{ id: 'cur', nm: '현행', why: '그날 17시 교통과 현시도 계획 그대로', ph: null },
      { id: 'A', kind: 'phase', nm: 'A 재편안 예시', why: '직진·좌회전 분리 · 측도 남북 양직진 · 출구 연장(들어오는 차 끊김)', ph: ex },
      { id: 'B', kind: 'phase', nm: 'B 출구 연장 길게', why: 'A 에서 동서 양직진 −15초 → 출구 연장 +15초(나오는 차 더 · 들어오는 차 덜)', ph: exB },
      { id: 'C', kind: 'time', nm: 'C 서직좌 줄이기', why: '현행 2현시(서직좌 — 블록으로 들어가는 서→동 직진) −15초 → 4현시 남직좌 +15초', ph: K(function (q) { if (q[1]) q[1].d -= 15; if (q[3]) q[3].d += 15; }) },
      { id: 'D', kind: 'time', nm: 'D 북직좌 줄이기', why: '현행 3현시(북직좌 — 블록으로 들어가는 북→동 좌회전) −10초 → 1현시 동서 양직진 +10초', ph: K(function (q) { if (q[2]) q[2].d -= 10; if (q[0]) q[0].d += 10; }) },
      { id: 'F', kind: 'phase', nm: 'F 형님 안 — 세분화', why: '주기 180 그대로 · 신반포로 양직→동직진(나오는 차)→서좌회전 · 반포대로 북직좌→남북 양직→남직좌 — 서→동 직진·북→동 좌회전(블록으로 들어감)을 줄인다', ph: [
        { d: 40, y: 4, ar: 1, mv: ['wt.St', 'et.St'], nm: '동서 양직진' }, { d: 26, y: 4, ar: 1, mv: ['et.St'], nm: '동 직진(블록에서 나옴)' }, { d: 26, y: 4, ar: 1, mv: ['wt.Lt'], nm: '서 좌회전(→반포대교)' },
        { d: 28, y: 3, ar: 1, mv: ['nt.St', 'nt.Lt'], nm: '북 직좌(반포대교에서)' }, { d: 32, y: 3, ar: 1, mv: ['nt.St', 'st.St'], nm: '남북 양직진' }, { d: 28, y: 3, ar: 1, mv: ['st.St', 'st.Lt'], nm: '남 직좌(도심 방향)' }] },
      { id: 'E', kind: 'time', nm: 'E 주기 늘리기', why: '현행 현시를 모두 1.2배(주기 늘려 한 번에 많이 보냄 — 대신 빨간불이 길다)', ph: K(function (q) { q.forEach(function (x) { x.d = Math.round(x.d * 1.2); }); }) }];
  }
  // 안마다 「무엇을 어떻게」 — 현장 차례·기대 효과·주의(초는 예시 · 바꾸는 권한은 교통과 시설 담당) — 자동 글(방향별 녹색 초 차이)은 아래 planCard 가 붙인다
  var HOW = {
    cur: { what: '지금 교통과 현시도 계획 그대로(비교 기준).', steps: ['손대지 않는다 — 다른 안의 효과를 재는 잣대.'], warn: [] },
    A: { what: '현시를 다섯으로 나눠 직진과 좌회전을 떼고, 블록에서 나오는 동→서 직진만 따로 더 보내는 「출구 연장」을 둔다. 측도(고가 아래 반포대로)는 남북 양직진으로 묶는다.',
      steps: ['① 동서 양직진 — 신반포로 양방향 직진', '② 출구 연장 — 동→서 직진(블록에서 나오는 차)은 계속, 서→동 직진(블록으로 들어가는 차)은 적색 · 서→북 좌회전 함께', '③ 남북 양직진 — 반포대로 측도', '④ 북 좌회전(→동, 블록으로 들어감)', '⑤ 남 좌회전(→서)',
        '현장 수동 조작: 블록이 차면 ② 에서 머문다 → 「⛔ 들어오는 차만 끊기」 한 번으로 들어가는 차만 멈추고 나오는 차는 흘려보낸다'],
      warn: ['측도 남북 양직진은 측도 좌회전 전용차로·고가 교각 때문에 되는지 현장 확인이 먼저(의도 문서 미결 질문)', '현시가 다섯이라 한 바퀴에 손실 시간이 늘어 바깥 지체가 커질 수 있다 — 시뮬에서도 그렇게 나온다', '현장 수동조작반이 「현시 지정」까지 되는지 확인 필요(넘기기만 되면 차례대로만 넘어간다)'] },
    B: { what: 'A 와 같은 틀에서 출구 연장을 15초 늘리고 동서 양직진을 15초 줄인다 — 나오는 차를 더 빼고 들어오는 차를 덜 받는다.',
      steps: ['A 의 ①을 15초 줄이고 ②(출구 연장)를 15초 늘린다', '나머지 현시·주기는 A 와 같다', '블록 안이 다 빠지면 A 로 되돌린다(출구만 길면 신반포로 서쪽에서 들어오는 차가 길게 선다)'],
      warn: ['신반포로 서쪽(신반포역 쪽)에서 동쪽으로 가는 차가 더 기다린다 — 그 길 대기를 같이 본다', 'A 의 주의 그대로'] },
    C: { what: '현행 네 현시 차례는 그대로 두고, 블록으로 들어가는 서→동 직진이 함께 켜지는 2현시(서직좌)를 15초 줄여 4현시(남직좌)에 준다.',
      steps: ['16~21시 계획(패턴 14 · 요일 공통) 2현시 43초 → 28초', '4현시 40초 → 55초(남쪽 측도 차 · 남→서 좌회전 더)', '주기 180초 그대로 → 이웃 교차로(4034·4019)와 연동이 안 깨진다', '수동 조작이면: 블록이 찰 때 2현시를 일찍 넘긴다(「다음 현시 ▶」)'],
      warn: ['서→북 좌회전(반포대교 쪽)도 15초 짧아진다 — 반포대교남단 쪽 대기를 같이 본다', '값 바꾸기는 교통과 시설 담당이 신호제어기 TOD 패턴을 고쳐야 한다 — 이 지도는 실제 신호를 바꾸지 않는다'] },
    D: { what: '블록으로 들어가는 북→동 좌회전이 켜지는 3현시(북직좌)를 10초 줄여 1현시(동서 양직진)에 준다.',
      steps: ['3현시 48초 → 38초', '1현시 49초 → 59초(동→서 직진 = 블록에서 나오는 차도 늘어남)', '주기 그대로'],
      warn: ['북→남 직진(반포대교에서 내려오는 측도 차)도 10초 짧아져 반포대교남단 쪽으로 대기가 늘 수 있다 — 분수 날 특히', '시뮬에서는 막힘이 늦게 시작하지만 총 지체는 늘었다'] },
    F: { what: '형님 안(2026-10-25) — 「신반포로 강남터미널고가밑과 고속터미널 사이에 너무 많은 차가 몰리는 것을 막는다 · 여기서 유입량을 충분히 줄여 주는 게 우선」. 주기 180초는 그대로 두고 현시를 여섯으로 나눈다.',
      steps: ['① 동서 양직진 40초 — 신반포로 양방향(서→동 직진은 이 현시에만 → 49+43 = 92초에서 40초로)', '② 동 직진 26초 — 블록에서 나오는 차만(현행 2현시 「서직좌」 자리)', '③ 서 좌회전 26초 — 구반포에서 반포대교 쪽', '④ 북 직좌 28초 — 반포대교에서 내려오는 차(북→동 좌회전 = 블록으로 들어감 48초 → 28초)', '⑤ 남북 양직진 32초', '⑥ 남 직좌 28초 — 도심 방향', '필요하면 「출차 우회」(조치)와 함께 — 신반포로 쪽 문으로 나오던 차를 다른 문으로'],
      warn: ['초는 이 시뮬이 정한 예시(설계값) — 현행 신반포로 92초·반포대로 88초 안에서 나눔', '현시가 여섯이라 한 바퀴에 황색·전적색이 늘어 바깥 지체는 커질 수 있다', '② 「동 직좌」의 동→남 좌회전은 지금 계획에 없는 이동류라 동 직진으로만 넣었다(그 좌회전이 실제로 있는지 형님 확인)', '구반포 쪽(신반포로 서쪽)에서 동쪽으로 가는 차는 더 기다린다 — 그 길 대기를 같이 본다'] },
    E: { what: '현시 비율은 그대로 두고 모두 1.2배(주기 180 → 216초) — 한 번에 많이 보내 출발 손실을 줄인다.',
      steps: ['모든 현시 초 × 1.2', '이웃 교차로(4034·4019·4028)도 같은 주기로 맞춰야 연동이 산다'],
      warn: ['주기가 길면 빨간불도 길어 보행·좌회전 대기가 늘어난다', '이웃 교차로와 주기가 다르면 연동이 깨진다 — 이 시뮬은 4031 만 바꿨다'] } };
  var MVK = { 'wt.St': ['서→동 직진', '블록으로 들어감'], 'nt.Lt': ['북→동 좌회전', '블록으로 들어감'], 'et.St': ['동→서 직진', '블록에서 나옴'], 'wt.Lt': ['서→북 좌회전', ''], 'nt.St': ['북→남 직진', ''], 'st.St': ['남→북 직진', ''], 'st.Lt': ['남→서 좌회전', ''] };
  var MVC = { 'wt.St': '#dc2626', 'nt.Lt': '#ea580c', 'et.St': '#16a34a', 'wt.Lt': '#2563eb', 'nt.St': '#0891b2', 'st.St': '#7c3aed', 'st.Lt': '#a21caf' };
  function grn(ph) { var w = window.tgSim.phasesToWin(ph), g = {}; w.win.forEach(function (r) { g[r[0]] = (g[r[0]] || 0) + r[1]; }); return { g: g, c: w.c }; }
  // 현시 하나 = 작은 교차로 그림(가는 방향 화살표)
  function pic(mv, sz) {
    var C = sz / 2, L = sz * 0.42, R9 = sz * 0.11, D = { nt: [0, -1], st: [0, 1], et: [1, 0], wt: [-1, 0] }, TO = { St: { nt: 'st', st: 'nt', et: 'wt', wt: 'et' }, Lt: { nt: 'et', et: 'st', st: 'wt', wt: 'nt' } };
    var h = '<svg viewBox="0 0 ' + sz + ' ' + sz + '" width="' + sz + '" height="' + sz + '"><rect x="' + (C - R9).toFixed(1) + '" y="0" width="' + (2 * R9).toFixed(1) + '" height="' + sz + '" fill="#cbd5e1"/><rect x="0" y="' + (C - R9).toFixed(1) + '" width="' + sz + '" height="' + (2 * R9).toFixed(1) + '" fill="#cbd5e1"/>';
    mv.forEach(function (k) { var a = k.split('.'), f = D[a[0]], to = TO[a[1]] && D[TO[a[1]][a[0]]]; if (!f || !to) return; var off = R9 * 0.5, rx = -f[1] * off, ry = f[0] * off;   // 들어오는 쪽 오른편 차로
      var x1 = C + f[0] * L + rx, y1 = C + f[1] * L + ry, x2 = C + to[0] * L - to[1] * off, y2 = C + to[1] * L + to[0] * off, cx = C + rx * (a[1] === 'Lt' ? -0.3 : 1) + (a[1] === 'Lt' ? (f[0] + to[0]) * R9 * 0.2 : 0), cy = C + ry * (a[1] === 'Lt' ? -0.3 : 1) + (a[1] === 'Lt' ? (f[1] + to[1]) * R9 * 0.2 : 0);
      h += '<path d="M' + x1.toFixed(1) + ',' + y1.toFixed(1) + ' Q' + cx.toFixed(1) + ',' + cy.toFixed(1) + ' ' + x2.toFixed(1) + ',' + y2.toFixed(1) + '" fill="none" stroke="' + (MVC[k] || '#334155') + '" stroke-width="2.6" marker-end="url(#pa' + sz + ')"/>'; });
    return h.replace('<rect', '<defs><marker id="pa' + sz + '" markerWidth="5" markerHeight="5" refX="4" refY="2.5" orient="auto"><path d="M0,0 L5,2.5 L0,5 z" fill="#334155"/></marker></defs><rect') + '</svg>';
  }
  // 현시 막대(한 주기) — 칸 = 현시 · 폭 = 초 · 칸 아래 작은 교차로 그림
  function bar(ph, W, ttl) {
    var c = ph.reduce(function (a, p) { return a + p.d; }, 0), x = 0, h = '<div style="margin:4px 0 2px;font-size:12px;font-weight:700">' + esc(ttl) + ' · 주기 ' + c + '초</div><div style="display:flex;width:100%;border-radius:8px;overflow:hidden;border:1px solid rgba(120,130,150,.4)">';
    ph.forEach(function (p, i) { var hasIn = p.mv.indexOf('wt.St') >= 0 || p.mv.indexOf('nt.Lt') >= 0, hasOut = p.mv.indexOf('et.St') >= 0;
      h += '<div style="flex:' + p.d + ' 1 0;min-width:0;padding:3px 2px;text-align:center;font-size:11px;background:' + (hasIn ? 'rgba(220,38,38,.13)' : hasOut ? 'rgba(22,163,74,.13)' : 'rgba(120,130,150,.08)') + ';border-right:1px solid rgba(120,130,150,.35)"><b>' + '①②③④⑤⑥⑦'.charAt(i) + ' ' + p.d + '초</b><div style="display:flex;justify-content:center">' + pic(p.mv, 44) + '</div></div>'; });
    return h + '</div>';
  }
  function planCard(p, res, curRes) {
    var cu = curPh(), ph = p.ph || cu, G0 = grn(cu), G1 = grn(ph), H = HOW[p.id] || { what: p.why, steps: [], warn: [] };
    var rows = Object.keys(MVK).filter(function (k) { return G0.g[k] != null || G1.g[k] != null; }).map(function (k) { var a = Math.round((G0.g[k] || 0) / G0.c * 3600), b = Math.round((G1.g[k] || 0) / G1.c * 3600), d0 = Math.round(G0.g[k] || 0), d1 = Math.round(G1.g[k] || 0), dd = d1 - d0;
      return '<tr><td><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:' + MVC[k] + ';margin-right:4px"></span>' + MVK[k][0] + (MVK[k][1] ? ' <small style="color:' + (MVK[k][1] === '블록으로 들어감' ? '#dc2626' : '#16a34a') + '">' + MVK[k][1] + '</small>' : '') + '</td><td>' + d0 + '초</td><td>' + d1 + '초</td><td style="color:' + (dd < 0 ? '#dc2626' : dd > 0 ? '#16a34a' : 'inherit') + '">' + (dd > 0 ? '+' : '') + dd + '</td><td><small>' + (a ? Math.round((b - a) / a * 100) + '%' : '-') + '</small></td></tr>'; }).join('');
    var eff = res ? '<div class="sg">시뮬 결과(같은 날·같은 차)</div><div class="row" style="gap:10px;font-size:12.5px"><span>총 지체 <b>' + res.delayVh.toLocaleString() + '</b> 대·시' + (curRes && p.id !== 'cur' && curRes.delayVh ? ' (' + (res.delayVh >= curRes.delayVh ? '+' : '') + Math.round((res.delayVh - curRes.delayVh) / curRes.delayVh * 100) + '%)' : '') + '</span><span>블록 갇힘 최대 <b>' + res.trappedMax + '</b>대' + (curRes && p.id !== 'cur' && curRes.trappedMax ? ' (' + (res.trappedMax >= curRes.trappedMax ? '+' : '') + Math.round((res.trappedMax - curRes.trappedMax) / curRes.trappedMax * 100) + '%)' : '') + '</span><span>막힘 ' + (res.jamStart != null ? hh(res.jamStart) + ' → ' + (res.clearT != null ? hh(res.clearT) : '23시↑') : '없음') + '</span></div>' : '';
    return '<div style="border:1px solid rgba(124,58,237,.4);border-radius:12px;padding:8px;margin:6px 0;background:rgba(124,58,237,.04)">' +
      '<div style="font-weight:800;font-size:14px">📖 ' + esc(p.nm) + ' — 조치 방법</div><div class="sn" style="font-size:12.5px;color:inherit">' + esc(H.what) + '</div>' +
      (p.id !== 'cur' ? bar(cu, 300, '현행') : '') + bar(ph, 300, p.id === 'cur' ? '현행' : p.nm) +
      '<div class="sn">현시별 초 — 현행 ' + cu.map(function (q, i) { return '①②③④⑤⑥⑦'.charAt(i) + q.d; }).join(' ') + (p.id !== 'cur' ? ' → 이 안 ' + ph.map(function (q, i) { return '①②③④⑤⑥⑦'.charAt(i) + q.d; }).join(' ') : '') + ' (그날 17시 계획 기준)</div>' +
      '<div class="sn">막대 칸 색 — 빨강 = 블록으로 들어가는 방향(서→동 직진·북→동 좌회전)이 켜지는 현시 · 초록 = 블록에서 나오는 동→서 직진만 · 회색 = 블록과 상관없는 현시 · 화살표 색은 아래 표 색과 같다</div>' +
      '<div class="sg">방향별 녹색(한 주기 · 황색·전적색 뺀 값)</div><table><tr><th>방향</th><th>현행</th><th>이 안</th><th>차이</th><th>시간당</th></tr>' + rows + '</table>' +
      '<div class="sg">현장 차례</div><ol style="margin:2px 0 4px;padding-left:20px;font-size:12.5px;line-height:1.55">' + H.steps.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ol>' +
      (H.warn.length ? '<div class="warn">⚠ ' + H.warn.map(esc).join('<br>⚠ ') + '</div>' : '') + eff +
      (p.id !== 'cur' ? '<div class="row" style="margin-top:4px"><button data-sk="show:' + p.id + '" class="on">▶ 이 안으로 시연</button></div>' : '') + '</div>';
  }
  function planOf(id) { return plans().filter(function (p) { return p.id === id; })[0] || plans()[0]; }
  function altOf(ph) { if (!ph) return null; var P = window.tgSim.planAt(M, '4031', 17 * 3600, window.tgSim.dowOf(ST.date)); return { '4031': { ph: ph, off: P.off || 0, t0: 16 * 3600, t1: 21 * 3600 } }; }   // 안은 16~21시(현행 17시 계획이 도는 때)에만 · 21시부터는 두 판 모두 현행 밤 계획
  function alt() { var p = ST.ph || planOf(ST.plan).ph; return altOf(p); }
  // 개선안 모두 돌려 보기(같은 날·같은 수요·같은 차) — 결과 표에서 고르면 그 안으로 시연
  var CMP = null;
  function compare() {
    var L = plans(), i = 0, Rw = [], sc = scen(), me = { busy: 1, rows: Rw }; CMP = me; paintCmp();
    (function next() { if (CMP !== me) return; if (i >= L.length) { me.busy = 0; paintCmp(); return; } var p = L[i++], S = window.tgSim.create(M, sc, altOf(p.ph)); S.runTo(S.end); var r = S.result(); r.id = p.id; r.nm = p.nm; r.why = p.why; Rw.push(r); paintCmp(); setTimeout(next, 30); })();
  }
  function paintCmp() {
    var el = $('simCmp'); if (!el) return; if (!CMP) { el.innerHTML = '<div class="row" style="margin-top:6px"><button data-sk="cmp" class="on">📊 개선안 모두 돌려 견주기</button><span class="sn" style="margin:0">현행·A~E 를 같은 날·같은 차로 16~23시 — 몇 초 걸림</span></div>'; return; }
    var Rw = CMP.rows.slice(), cur = Rw.filter(function (r) { return r.id === 'cur'; })[0];
    Rw.sort(function (a, b) { return a.delayVh - b.delayVh; });
    var dv = function (x, y) { if (!x || x === y) return ''; var p = Math.round((y - x) / x * 100); return ' <small style="color:' + (p < 0 ? '#16a34a' : '#dc2626') + '">' + (p > 0 ? '+' : '') + p + '%</small>'; };
    el.innerHTML = '<div class="sg">개선안별 결과(' + esc((DAYS.filter(function (d) { return d[0] === ST.day; })[0] || [])[1] || '') + ' · 16~23시 · 총 지체 적은 차례)' + (CMP.busy ? ' — 계산 중…' : '') + '</div><table><tr><th>안</th><th>총 지체</th><th>블록 갇힘</th><th>막힘→해소</th><th></th></tr>' +
      Rw.map(function (r) { return '<tr><td><b>' + esc(r.nm) + '</b><br><small>' + esc(r.why) + '</small></td><td>' + r.delayVh.toLocaleString() + (cur ? dv(cur.delayVh, r.delayVh) : '') + '</td><td>' + r.trappedMax + (cur ? dv(cur.trappedMax, r.trappedMax) : '') + '</td><td>' + (r.jamStart != null ? hh(r.jamStart) + '→' + (r.clearT != null ? hh(r.clearT) : '23시↑') : '없음') + '</td><td>' + (r.id === 'cur' ? '' : '<button data-sk="show:' + r.id + '">▶ 시연</button>') + ' <button data-sk="how:' + r.id + '">📖</button></td></tr>' + (CMP.open === r.id ? '<tr><td colspan="5" style="text-align:left">' + planCard(planOf(r.id), r, cur) + '</td></tr>' : ''); }).join('') + '</table>' +
      '<div class="sn">▶ 시연 = 왼쪽 현행 · 오른쪽 그 안으로 다시 돌림 · 같은 수요·같은 차라 차이는 신호에서만 온다 · 개념 시연(예측 아님)</div>';
  }
  function start() {
    stop(); A = window.tgSim.create(M, scen(), null); var sb = scen(); if (ST.auto) sb.autoCut = ST.manF ? Object.assign({}, AUTO, { ph: manPh() }) : AUTO; B = window.tgSim.create(M, sb, alt());
    A.runTo(A.from); B.runTo(B.from); if (ST.manual) { B.manual('4031', true, manPh()); }
    paintRun(); RUN = 1; LAST = 0; requestAnimationFrame(tick); paintCtl();
  }
  /* 🤖 4031 자동 끊기 — 5초마다 신반포로(4031→신세계 문 쪽) 점유 85% 넘으면 블록으로 들어가는 차(서→동 직진·북→동 좌회전)가 없는 현시로 · 60% 아래면 원래 계획(게임 세션 「진행상황」 10/18 재현: 꼬리물기 1,131→195 · 갇힘 338→143 · 지체 같음) */
  /* 형님(2026-10-25) 「보낼 수 있는 곳은 신반포로 하행(잠원IC 방향)·동→서 두 곳 · 외곽(반포대교) 쪽 직좌에서 좌회전으로 신세계 들어가는 차가 너무 많아져 그걸 줄여야 할 때가 있다」 → 끊는 것 = 북→동 좌회전만 · 차례는 그대로 돈다(빼기) */
  var AUTO = { node: '4031', link: '4031>G', hi: 0.85, lo: 0.6, every: 5, cut: ['nt.Lt'], mode: 'drop' };
  /* 수동 현시 = 세분화(F 형님 안 여섯 현시) — 자동(계획)은 현행 그대로 두고 수동·자동 끊기 때만 이 현시 목록에서 고른다 */
  function manPh() { if (!ST.manF) return null; return planOf('F').ph.map(function (p) { return { d: p.d, y: p.y, ar: p.ar, mv: p.mv.slice() }; }); }
  function stop() { RUN = 0; }
  function tick(ts) {
    if (!RUN || !A) return; if (!LAST) LAST = ts; var dt = Math.min(0.25, (ts - LAST) / 1000); LAST = ts;
    var n = Math.min(900, Math.round(dt * SPD)); for (var i = 0; i < n && A.t < A.end; i++) { A.step(); B.step(); }
    paintRun(); if (A.t % 600 < n + 1) paintLive(); if (A.t >= A.end) { RUN = 0; paintCtl(); paintRes(); paintHow(); paintLive(); return; } requestAnimationFrame(tick);
  }
  function toEnd() { if (!A) start(); stop(); A.runTo(A.end); B.runTo(B.end); paintRun(); paintCtl(); paintRes(); paintHow(); paintLive(); }
  // 블록 그림(두 판 같은 꼴) — 길 = 점유(대수 ÷ 길이×차로÷7.5m) 색 · 숫자 = 문 앞·출차 대기·공원 앞
  var GEO = null;
  function geo() {
    if (GEO) return GEO; var N = M.nodes, ks = Object.keys(N), xs = [], ys = [];
    ks.forEach(function (k) { xs.push(N[k].ll[1]); ys.push(N[k].ll[0]); });
    var x0 = Math.min.apply(null, xs), x1 = Math.max.apply(null, xs), y0 = Math.min.apply(null, ys), y1 = Math.max.apply(null, ys), W = 300, H = 260, pad = 46;
    var kx = (W - 2 * pad) / ((x1 - x0) * 0.79 || 1), ky = (H - 2 * pad) / ((y1 - y0) || 1), k = Math.min(kx, ky);
    var P = function (ll) { return [pad + (ll[1] - x0) * 0.79 * k, H - pad - (ll[0] - y0) * k]; }, XY = {}; ks.forEach(function (id) { XY[id] = P(N[id].ll); });
    var D = { nt: [0, -1], st: [0, 1], et: [1, 0], wt: [-1, 0] }, segs = [];
    Object.keys(M.links).forEach(function (id) { var l = M.links[id]; if (l.sink && !l.fr) return;
      var a, b;
      if (l.fr && l.to && XY[l.fr] && XY[l.to]) { a = XY[l.fr]; b = XY[l.to]; if (a[0] === b[0] && a[1] === b[1]) return; }
      else if (!l.fr && l.to && l.oto && XY[l.to]) { var d = D[l.oto]; b = XY[l.to]; a = [b[0] + d[0] * 40, b[1] + d[1] * 40]; }
      else return;
      var vx = b[0] - a[0], vy = b[1] - a[1], L = Math.hypot(vx, vy) || 1, ox = -vy / L * 3.2, oy = vx / L * 3.2;   // 오른쪽 통행 — 진행 방향 오른쪽으로 비켜 그림
      segs.push({ id: id, a: [a[0] + ox, a[1] + oy], b: [b[0] + ox, b[1] + oy] }); });
    var q4 = ['4031', '4019', '4028', '4034'].map(function (k) { return XY[k]; }).filter(Boolean), bc = [q4.reduce(function (s, p) { return s + p[0]; }, 0) / q4.length, q4.reduce(function (s, p) { return s + p[1]; }, 0) / q4.length];
    GEO = { W: W, H: H, XY: XY, segs: segs, bc: bc, q4: q4 }; return GEO;
  }
  function col(r) { return r >= 0.8 ? '#dc2626' : r >= 0.4 ? '#eab308' : '#16a34a'; }
  function svg(S) {
    var G = geo(), h = '<svg viewBox="0 0 ' + G.W + ' ' + G.H + '" role="img" aria-label="블록 길 점유">';
    h += '<polygon points="' + G.q4.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ') + '" fill="rgba(124,58,237,.08)" stroke="none"/>';
    h += '<text x="' + G.bc[0].toFixed(1) + '" y="' + (G.bc[1] + 4).toFixed(1) + '" font-size="10" text-anchor="middle" fill="#7c3aed" font-weight="700">신세계·터미널</text>';
    G.segs.forEach(function (s) { var L = S.L[s.id]; if (!L) return; var r = Math.min(1, L.n / L.cap); h += '<line x1="' + s.a[0].toFixed(1) + '" y1="' + s.a[1].toFixed(1) + '" x2="' + s.b[0].toFixed(1) + '" y2="' + s.b[1].toFixed(1) + '" stroke="' + col(r) + '" stroke-width="' + (2.5 + 4 * r).toFixed(1) + '" stroke-linecap="round"/>'; });
    Object.keys(G.XY).forEach(function (id) { var n = M.nodes[id]; if (n.ty !== 'sig' && id !== '4032') return; var p = G.XY[id], bx = S.N[id] && S.N[id].box.length;
      h += '<circle cx="' + p[0].toFixed(1) + '" cy="' + p[1].toFixed(1) + '" r="6" fill="' + (bx ? '#dc2626' : '#334155') + '"/><text x="' + (p[0] + 8).toFixed(1) + '" y="' + (p[1] - 7).toFixed(1) + '" font-size="9.5" fill="currentColor">' + esc(SHORT[id] || n.nm) + '</text>'; });
    // 출입구 4곳(변 가운데 근사) — 문 앞 줄·나가려고 기다리는 차 · 블록 쪽 차로 시계 방향 화살표
    var by = {}; ['shin', 'busGB', 'busCT'].forEach(function (k) { var a9 = S.samp.length && S.samp[S.samp.length - 1].att[k]; if (a9 && a9.by) Object.keys(a9.by).forEach(function (d) { by[d] = (by[d] || 0) + a9.by[d][0] + a9.by[d][1]; }); });
    var q = G.q4; [[0, 1, 'N'], [1, 2, 'E'], [2, 3, 'S'], [3, 0, 'W']].forEach(function (e) { var a = q[e[0]], b = q[e[1]], mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2, ix = (G.bc[0] - mx) * 0.22, iy = (G.bc[1] - my) * 0.22, d = AREA.doors.filter(function (x) { return x.id === e[2]; })[0], n = by[e[2]] || 0;
      var ax = a[0] + (b[0] - a[0]) * 0.18 + ix * 0.5, ay = a[1] + (b[1] - a[1]) * 0.18 + iy * 0.5, bx2 = a[0] + (b[0] - a[0]) * 0.32 + ix * 0.5, by2 = a[1] + (b[1] - a[1]) * 0.32 + iy * 0.5;
      h += '<line x1="' + ax.toFixed(1) + '" y1="' + ay.toFixed(1) + '" x2="' + bx2.toFixed(1) + '" y2="' + by2.toFixed(1) + '" stroke="#7c3aed" stroke-width="1.6" marker-end="url(#simArw)"/>';
      h += '<g><rect x="' + (mx + ix - 10).toFixed(1) + '" y="' + (my + iy - 8).toFixed(1) + '" width="20" height="16" rx="4" fill="' + (n > 150 ? '#dc2626' : n > 40 ? '#eab308' : '#7c3aed') + '"/><text x="' + (mx + ix).toFixed(1) + '" y="' + (my + iy + 4).toFixed(1) + '" font-size="9" text-anchor="middle" fill="#fff" font-weight="800">' + (n > 999 ? Math.round(n / 100) / 10 + 'k' : n) + '</text><title>출입구 ' + esc(d ? d.nm : e[2]) + ' — 들어가려고·나가려고 기다리는 차 ' + n + '대</title></g>'; });
    return h.replace('role="img" aria-label="블록 길 점유">', 'role="img" aria-label="블록 길 점유"><defs><marker id="simArw" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" fill="#7c3aed"/></marker></defs>') + '</svg>';
  }
  function info(S) {
    var sm = S.samp[S.samp.length - 1], jam = sm ? sm.jam.length : 0, at = sm ? sm.att : {}, R = S.result();
    var sh = at.shin || {}, fo = at.fount || {}, pk = sh.cap ? '<br>🅿 주차장 ' + (sh.occ || 0).toLocaleString() + '/' + sh.cap.toLocaleString() + '면' + (sh.occ >= sh.cap ? ' <b style="color:#dc2626">만차 — 문 닫힘</b>' : '') : '';
    return '<div class="pi">막힌 접근로 <b>' + jam + '</b>곳 · 꼬리물기 ' + S.boxN + '번<br>신세계 문 앞 ' + (sh.door || 0) + '대 · 출차 대기 <b>' + (sh.out || 0) + '</b>대 · 🔄 만차라 빙 돈 차 ' + (sh.circ || 0) + '대<br>공원 앞 ' + (fo.door || 0) + '대 · 지체 ' + R.delayVh.toLocaleString() + ' 대·시' + pk + '</div>';
  }
  /* 형님(2026-10-30) 「현행과 개선안을 각각 따로 크게 · 왜 밀릴 수밖에 없고 마비가 생길 수밖에 없는지 구체적으로 · 개선안은 신호값과 신호(현시 구성)를 나눠 신반포로로 가해지는 압박을 어떻게 줄이고
     신세계에서 나오는 차와 들어가는 차를 적절히 배분해 주변 통행과 어울리게 — 일시적인 정체는 생길 수 있지만 마비까지는 되지 않는 것이 목표」
     마비 = 막힘 고리 네 변(AREA.legs) 가운데 셋 이상이 80% 넘게 찬 분 · 일시 정체 = 막힌 접근로는 있으나 마비는 아닌 분(1분 표본 · 설계 기준) */
  var SIN = ['4031>G', 'G>4019'];   /* 신반포로 — 반포사거리~고속터미널 블록 쪽 차로 */
  function occR(S, s9, k) { var L = S.L[k]; return L ? (s9.occ[k] || 0) / L.cap : 0; }
  function legsSim() { return AREA.legs.map(function (g) { return g.sim; }).filter(function (k) { return M.links[k]; }); }
  function para(S) { var P = 0, T = 0, sm = 0, mx = 0, n = 0, cp = SIN.reduce(function (a, k) { return a + (S.L[k] ? S.L[k].cap : 0); }, 0);
    S.samp.forEach(function (s9) { var c = legsSim().filter(function (k) { return occR(S, s9, k) >= 0.8; }).length; if (c >= 3) P++; else if (s9.jam.length) T++;
      var o = cp ? SIN.reduce(function (a, k) { return a + (s9.occ[k] || 0); }, 0) / cp : 0; sm += o; n++; if (o > mx) mx = o; });
    return { para: P, temp: T, sinAvg: n ? sm / n : 0, sinMax: mx, sinNow: n ? (function (s9) { return cp ? SIN.reduce(function (a, k) { return a + (s9.occ[k] || 0); }, 0) / cp : 0; })(S.samp[n - 1]) : 0 }; }
  var NAMEK = { '4031>G': '신반포로(반포사거리 → 신세계 북문)', 'G>4019': '신반포로(신세계 북문 → 고속터미널)', '4019>4028': '잠원로(고속터미널 → 삼호가든)', '4028>SI': '사평대로(삼호가든 → 메리어트 들어가는 곳)', 'SO>4034': '사평대로(메리어트 나오는 곳 → 서울성모병원)',
    '4034>H': '반포대로(서울성모병원 → 고가 갈림)', 'WO>4031': '반포대로(호남선 나오는 곳 → 반포사거리)', '4032>4031': '반포대로(반포대교남단 → 반포사거리)', 'in.4031.wt': '신반포로 서쪽(신반포역 쪽) 들어오는 길', 'in.4019.et': '신반포로 동쪽(반포역 쪽) 들어오는 길',
    'in.4019.nt': '잠원로 북쪽 들어오는 길', 'in.4028.et': '사평대로 동쪽(사평역 쪽) 들어오는 길', 'in.4034.st': '반포대로 남쪽(서초역 쪽) 들어오는 길' };
  /* 왜 마비되나 — 그 판의 1분 표본에서 처음 넘은 일을 차례대로(엔진 samp 의 occ·box·att) */
  function chain(S) { var ev = [], seen = {}, b0 = 0, full = false, pd = false;
    (S.pre || []).concat(S.samp).forEach(function (s9) {
      Object.keys(NAMEK).forEach(function (k) { if (seen[k] || !S.L[k]) return; if (occR(S, s9, k) >= 0.8) { seen[k] = 1; ev.push([s9.t, '🟥 ' + NAMEK[k] + ' — 80% 넘게 참']); } });
      if (!b0 && s9.box > 0) { b0 = 1; ev.push([s9.t, '🔴 꼬리물기 시작 — 아래가 찬 줄 모르고 들어간 차가 교차로 안에 서서 다른 방향까지 막음']); }
      var sh = s9.att && s9.att.shin;
      if (!full && sh && sh.cap && sh.occ >= sh.cap) { full = true; ev.push([s9.t, '🅿 신세계·메리어트 주차장 만차 — 문이 닫혀 들어가려는 차가 길에 서고, 블록을 한 바퀴 돌아 다음 문으로']); }
      if (sh && !seen.out && sh.out >= 100) { seen.out = 1; ev.push([s9.t, '🚗 나가려는 차 100대 넘게 대기 — 본선이 차서 합류할 틈이 없음(나가야 자리가 나는데 못 나감)']); }
      var c = legsSim().filter(function (k) { return occR(S, s9, k) >= 0.8; }).length;
      if (!pd && c >= 3) { pd = true; ev.push([s9.t, '⛔ 마비 — 블록 둘레 네 변 가운데 ' + c + '곳이 막혀, 블록을 도는 차가 서로의 꼬리를 막는다']); }
    }); return ev; }
  function whyCard(S, nm) { var ev = chain(S), p = para(S);
    return '<div class="pv" style="padding:6px 8px"><div class="pt" style="text-align:left">🧩 ' + esc(nm) + ' — 왜 밀리나(시각 차례)</div>' + (ev.length ? '<ol style="margin:4px 0;padding-left:18px;font-size:12px;line-height:1.5">' + ev.slice(0, 12).map(function (e) { return '<li><b>' + hh(e[0]) + '</b> ' + esc(e[1]) + '</li>'; }).join('') + '</ol><div class="sn" style="margin:0">16시 앞은 몸풀기(14시 빈 길에서 시작해 쌓여 가는 모양) · 개선안은 16~21시에만 쓰므로 16시 앞은 두 판이 같다</div>' : '<div class="sn">막힌 곳 없이 흘렀다</div>') +
      '<div class="sn" style="margin:2px 0">마비 ' + p.para + '분 · 일시 정체 ' + p.temp + '분 · 신반포로(반포사거리~터미널) 평균 ' + Math.round(p.sinAvg * 100) + '% · 최대 ' + Math.round(p.sinMax * 100) + '%</div></div>'; }
  function paintRun() {
    if (!A) return; var el = $('simRun'); if (!el) return;
    var pa = para(A), pb = para(B), pstr = function (p) { return '<div class="sn" style="margin:2px 0;color:inherit">신반포로(반포사거리~터미널) 지금 <b style="color:' + (p.sinNow >= 0.8 ? '#dc2626' : p.sinNow >= 0.5 ? '#ca8a04' : '#16a34a') + '">' + Math.round(p.sinNow * 100) + '%</b> · 평균 ' + Math.round(p.sinAvg * 100) + '% · ⛔ 마비 <b>' + p.para + '분</b> · 일시 정체 ' + p.temp + '분</div>'; };
    el.innerHTML = '<div class="row" style="justify-content:space-between"><span class="clock">' + hh(A.t) + '</span><span class="sn" style="margin:0">16:00 → 23:00 · 같은 차 · 같은 날</span>' + chipB('big', ST.big === false ? '🔳 크게(위아래)' : '◫ 나란히', false) + '</div><div class="two' + (ST.big === false ? '' : ' big') + '">' +
      '<div class="pv"><div class="pt">현행 신호</div>' + pstr(pa) + svg(A) + info(A) + '</div><div class="pv"><div class="pt">' + esc(ST.ph ? planOf(ST.plan).nm + '(고침)' : planOf(ST.plan).nm) + (ST.auto ? ' + 🤖 자동 끊기' + (B.ac && B.ac.on ? ' <b style="color:#dc2626">끊는 중</b>' : '') : B.N['4031'].manual ? ' · 🖐 수동' : '') + '</div>' + pstr(pb) + svg(B) + info(B) + '</div></div>' +
      (A.t >= A.from + 1800 ? '<div class="two' + (ST.big === false ? '' : ' big') + '" style="margin-top:6px">' + whyCard(A, '현행') + whyCard(B, planOf(ST.plan).nm) + '</div>' : '') +
      '<div class="sn">길 색 = 그 길에 찬 정도(초록 40% 아래 · 노랑 · 빨강 80% 넘음 — 막힘) · 빨간 점 = 꼬리물기로 교차로가 막힘 · 보라 네모 = 출입구 4곳(숫자 = 문 앞·나가려고 기다리는 차) · 보라 화살표 = 블록 쪽 차로가 도는 방향(시계 방향)</div>';
  }
  var HOWO = null;
  function paintHow() { var el = $('simHow'); if (!el || !M) return; var p = planOf(ST.plan); el.innerHTML = HOWO === 'x' ? '<div class="row"><button data-sk="how:' + p.id + '">📖 「' + esc(p.nm) + '」 조치 방법 펼치기</button></div>' : planCard(ST.ph ? { id: p.id, nm: p.nm + '(초를 고침)', why: p.why, ph: ST.ph } : p, B && B.t >= B.end ? B.result() : null, A && A.t >= A.end ? A.result() : null) + '<div class="row"><button data-sk="how:x">접기</button></div>'; }
  function paintRes() {
    var el = $('simRes'); if (!el || !A) return; var a = A.result(), b = B.result();
    var mq = function (r) { var m = 0, k = ''; Object.keys(r.maxQm).forEach(function (x) { if (r.maxQm[x] > m) { m = r.maxQm[x]; k = x; } }); return m + 'm' + (k ? ' <small>(' + esc((SHORT[k.split('.')[0]] || k.split('.')[0]) + ' ' + ({ nt: '북', et: '동', st: '남', wt: '서' }[k.split('.')[1]] || '')) + ')</small>' : ''); };
    var dv = function (x, y) { if (!x) return ''; var p = Math.round((y - x) / x * 100); return '<small style="color:' + (p < 0 ? '#16a34a' : p > 0 ? '#dc2626' : 'inherit') + '">' + (p > 0 ? '+' : '') + p + '%</small>'; };
    el.innerHTML = '<div class="sg">결과(16~23시)</div><table><tr><th></th><th>현행</th><th>' + esc(planOf(ST.plan).nm) + (ST.auto ? ' + 🤖 자동 끊기' : '') + '</th></tr>' +
      '<tr><td>총 지체</td><td>' + a.delayVh.toLocaleString() + ' 대·시</td><td>' + b.delayVh.toLocaleString() + ' ' + dv(a.delayVh, b.delayVh) + '</td></tr>' +
      '<tr><td>최대 대기 길이</td><td>' + mq(a) + '</td><td>' + mq(b) + '</td></tr>' +
      '<tr><td>블록 안에 갇힌 차(최대)</td><td>' + a.trappedMax + '대</td><td>' + b.trappedMax + '대 ' + dv(a.trappedMax, b.trappedMax) + '</td></tr>' +
      '<tr><td>꼬리물기(교차로 안에 선 차 · 누적)</td><td>' + a.box + '</td><td>' + b.box + ' ' + dv(a.box, b.box) + '</td></tr>' +
      (ST.auto ? '<tr><td>🤖 자동 끊기</td><td>-</td><td>' + b.acN + '번 · ' + Math.round(b.acSec / 60) + '분 끊음</td></tr>' : '') +
      (function () { var pa = para(A), pb = para(B), ok = function (p) { return p.para === 0 ? '<b style="color:#16a34a">✓ 마비 없음</b>' : '<b style="color:#dc2626">✗ 마비 ' + p.para + '분</b>'; };
        return '<tr><td>신반포로(반포사거리~터미널) 찬 정도 평균 · 최대</td><td>' + Math.round(pa.sinAvg * 100) + '% · ' + Math.round(pa.sinMax * 100) + '%</td><td>' + Math.round(pb.sinAvg * 100) + '% · ' + Math.round(pb.sinMax * 100) + '% ' + dv(pa.sinAvg, pb.sinAvg) + '</td></tr>' +
          '<tr><td>⛔ 마비(블록 네 변 가운데 셋 이상 80%↑)</td><td>' + pa.para + '분</td><td>' + pb.para + '분 ' + dv(pa.para, pb.para) + '</td></tr>' +
          '<tr><td>일시 정체(막힌 곳은 있으나 마비 아님)</td><td>' + pa.temp + '분</td><td>' + pb.temp + '분</td></tr>' +
          '<tr><td><b>목표 — 일시 정체는 있어도 마비 없음</b></td><td>' + ok(pa) + '</td><td>' + ok(pb) + '</td></tr>'; })() +
      '<tr><td>막힘 시작 → 해소</td><td>' + (a.jamStart != null ? hh(a.jamStart) : '') + ' → ' + (a.jamStart != null ? (a.clearT != null ? hh(a.clearT) : '23시 넘김') : '막힘 없음') + '</td><td>' + (b.jamStart != null ? hh(b.jamStart) : '') + ' → ' + (b.jamStart != null ? (b.clearT != null ? hh(b.clearT) : '23시 넘김') : '막힘 없음') + '</td></tr></table>' +
      '<div class="sn">막힘 = 신호 교차로 접근로 가운데 80% 넘게 찬 곳이 3곳 이상 · 해소 = 그 뒤 3곳 아래로 내려간 때 · 지체 = 막히지 않았을 때보다 더 걸린 시간의 합</div>';
  }
  function chipB(k, nm, on) { return '<button data-sk="' + k + '" class="' + (on ? 'on' : '') + '">' + nm + '</button>'; }
  function slider(k, nm, v, mx, st, note) { return '<label class="sl"><b>' + nm + '</b><input type="range" min="0" max="' + mx + '" step="' + st + '" value="' + v + '" data-sv="' + k + '"><em>' + v.toLocaleString() + ' 대/시</em></label>' + (note ? '<div class="sn" style="margin:-2px 0 4px">' + note + '</div>' : ''); }
  function paintCtl() {
    var el = $('simCtl'); if (!el) return; var wd = [1, 2, 3, 4, 5].indexOf(window.tgSim.dowOf(ST.date)) >= 0, ph = ST.ph || planOf(ST.plan).ph || curPh(), cyc = ph.reduce(function (s, p) { return s + p.d; }, 0);
    var acts = (M.actions || []).map(function (a) { return chipB('act:' + a.id, a.nm, ST.act[a.id]); }).join('');
    var h = '<div class="sg">날</div><div class="row">' + DAYS.map(function (d) { return chipB('day:' + d[0], d[1], ST.day === d[0]); }).join('') + '</div>' +
      '<div class="sg">수요(설계값 — 대수 자료 없음 · 막대로 바꿈)</div>' +
      slider('shin', '신세계 들어오는 차', ST.shin, 2000, 50, att0('shin').inT0 + '~' + att0('shin').inT1 + '시 · 나가는 차는 머문 시간이 다 된 차(주차장 자리가 나야 들어감)') +
      '<label class="sl"><b>🅿 주차장 시작 때 차 있음</b><input type="range" min="0" max="100" step="5" value="' + ST.occ + '" data-sv="occ"><em>' + ST.occ + '%</em></label><div class="sn" style="margin:-2px 0 4px">신세계·메리어트 통합 주차장 ' + (att0('shin').capacity || 0).toLocaleString() + '면(건축물대장) · 가득 차면 문이 닫혀 들어가려는 차가 길에서 기다린다 · 머문 지 약 ' + (att0('shin').dwell || '-') + '분 뒤 나가야 자리가 난다(형님 현장 지식 · 머무는 시간은 설계값)</div>' +
      slider('fount', '한강공원 분수', ST.fount, 1500, 50, '10월 분수 19:30~21:00 · 공원 주차장 받는 속도 ' + att0('fount').inCap + '대/시') +
      (wd ? slider('academy', '학원가(평일)', ST.academy, 1000, 50, '평일 15:30~19:00 · 지하차도 대신 위로(형님 현장 지식)') : '') +
      '<label class="sl"><b>🚌 고속버스(실측 × 배율)</b><input type="range" min="0" max="2" step="0.1" value="' + ST.bus + '" data-sv="bus"><em>× ' + ST.bus + '</em></label><div class="sn" style="margin:-2px 0 4px">TAGO 시간표 그날 갈래 그대로(×1) · 경부·영동 = 동 잠원로 출입구 · 호남 = 서 반포대로 출입구 · 0 = 끔</div>' +
      '<div class="row">' + chipB('box', '꼬리물기 있음', ST.box) + '</div>' +
      '<div class="sg">조치</div><div class="row">' + acts + '</div>' +
      '<div class="sg">개선안 — 4031 반포사거리(오른쪽 판)</div><div class="row">' + chipB('plan:cur', '현행', ST.plan === 'cur') + '</div>' +
      '<div class="sn" style="margin:4px 0 2px;color:inherit"><b>① 신호값만 바꾸기</b> — 현시 차례는 그대로, 초만</div><div class="row">' + plans().filter(function (p) { return p.kind === 'time'; }).map(function (p) { return chipB('plan:' + p.id, p.nm, ST.plan === p.id); }).join('') + '</div>' +
      '<div class="sn" style="margin:4px 0 2px;color:inherit"><b>② 신호(현시 구성) 바꾸기</b> — 직진·좌회전을 떼거나 현시를 나눔</div><div class="row">' + plans().filter(function (p) { return p.kind === 'phase'; }).map(function (p) { return chipB('plan:' + p.id, p.nm, ST.plan === p.id); }).join('') + '</div><div class="sn">' + esc(planOf(ST.plan).why) + ' · 주기 ' + cyc + '초' + (ST.ph ? ' · 초를 고침' : '') + ' · 안은 16~21시(현행 17시 계획이 도는 때)에만 쓰고 21시부터는 두 판 모두 현행 밤 계획</div>';
    if (ST.plan !== 'cur') h += ph.map(function (p, i) { return '<div class="ph"><b>' + (i + 1) + '</b><span>' + esc(p.nm || p.mv.join('+')) + '</span><button data-pd="' + i + ':-5">−5</button><b style="min-width:34px;text-align:center">' + p.d + '초</b><button data-pd="' + i + ':5">+5</button></div>'; }).join('');
    h += '<div class="sg">돌리기</div><div class="row">' + '<button data-sk="run" class="on">' + (RUN ? '⏸ 멈춤' : A ? '▶ 이어서' : '▶ 시작') + '</button>' + [300, 600, 1200].map(function (v) { return chipB('spd:' + v, '×' + v, SPD === v); }).join('') + '<button data-sk="end">⏩ 끝까지</button><button data-sk="re">↺ 처음부터</button></div>' +
      '<div class="sg">수동 조작 — 오른쪽 판 4031(실제 신호를 바꾸는 기능이 아니다)</div><div class="row">' + chipB('man', '🖐 수동', ST.manual) + '<button data-sk="next">다음 현시 ▶</button><button data-sk="cut"' + (B && B.drop && B.drop['4031'] ? ' class="on"' : '') + '>⛔ 좌회전(→신세계)만 막기</button>' + chipB('auto', '🤖 자동 끊기', ST.auto) + chipB('manF', '🔀 수동 현시 = 세분화', ST.manF) + '</div>' +
      '<div class="sn">🔀 수동 현시 = 세분화 — 평소(계획)는 현행 그대로 두고, 🖐 수동·⛔ 끊기·🤖 자동 끊기 때만 F 형님 안의 여섯 현시(동 직진만 · 서 좌회전만 · 남북 양직 …)에서 고른다(형님 건의 「수동 조작 때 고를 수 있는 현시 세분화」)</div>' +
      '<div class="sn">⛔ = 오른쪽 판 4031 에서 북→동 좌회전(반포대교에서 신세계 쪽)만 적색 · 신반포로 하행(잠원IC 방향)·동→서는 그대로 보낸다(형님 「보낼 수 있는 곳은 그 두 곳 · 좌회전으로 신세계 들어가는 차를 줄여야 할 때」) · 🤖 자동 끊기 = 5초마다 신반포로(4031→신세계 문) 점유 85% 넘으면 같은 「좌회전만 막기」 · 60% 아래면 풀기(설계값 · 막은 횟수·시간은 결과에) · 10/18: 꼬리물기 1,175→141 · 블록 갇힘 610→480 · 풀림 21:52→21:24 · 대신 지체 +24%(좌회전 차가 반포대교 쪽에서 기다림)</div>' +
      (B && B.N['4031'].manual ? '<div class="sn">지금 현시 ' + (B.N['4031'].manual.i + 1) + ' — ' + esc(B.N['4031'].manual.ph[B.N['4031'].manual.i].mv.join(' + ')) + '</div>' : '');
    el.innerHTML = h;
  }
  function onClick(e) {
    var b = e.target.closest('[data-sk],[data-pd],[data-simx],[data-simlnk]'); if (!b) return;
    if (b.hasAttribute('data-simx')) { close(); return; }
    if (b.hasAttribute('data-simlnk')) { close(); if (window.tgLink) window.tgLink.open({ id: b.getAttribute('data-simlnk') }); return; }   /* 🧩 엮임 보기 — 그 교차로의 연결 그림 */
    if (b.hasAttribute('data-pd')) { var q = b.getAttribute('data-pd').split(':'), ph = ST.ph || JSON.parse(JSON.stringify(planOf(ST.plan).ph || curPh())); ph[+q[0]].d = Math.max(8, ph[+q[0]].d + +q[1]); ST.ph = ph; A = null; B = null; stop(); CMP = null; paintCmp(); paintCtl(); start(); paintHow(); return; }
    var k = b.getAttribute('data-sk'), restart = false;
    if (k === 'big') { ST.big = ST.big === false; paintRun(); return; }
    if (k.indexOf('day:') === 0) { ST.day = k.slice(4); var d = DAYS.filter(function (x) { return x[0] === ST.day; })[0]; ST.date = d[2]; var p = presetOf(ST.day); ST.shin = p && p.att && p.att.shin ? p.att.shin.inPeak : att0('shin').inPeak; ST.fount = p && p.att && p.att.fount ? p.att.fount.inPeak : att0('fount').inPeak; restart = true; toastS(p ? '「' + d[1] + '」 재현 설정 — 신세계 ' + ST.shin + ' · 분수 ' + ST.fount + '대/시(설계값)' : '「' + d[1] + '」 — 수요는 기본 설계값(신세계 ' + ST.shin + ' · 분수 ' + ST.fount + '대/시) · 신호·고속버스·평소 속도는 그 날 갈래'); }
    else if (k.indexOf('act:') === 0) { var id = k.slice(4); ST.act[id] = !ST.act[id]; restart = true; }
    else if (k.indexOf('plan:') === 0) { ST.plan = k.slice(5); ST.ph = null; restart = true; }
    else if (k.indexOf('show:') === 0) { ST.plan = k.slice(5); ST.ph = null; restart = true; var rn = $('simRun'); if (rn) rn.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
    else if (k === 'cmp') { compare(); return; }
    else if (k.indexOf('how:') === 0) { var hid = k.slice(4); if (CMP && b.closest('#simCmp')) { CMP.open = CMP.open === hid ? null : hid; paintCmp(); } else { HOWO = HOWO === hid ? null : hid; paintHow(); } return; }
    else if (k.indexOf('spd:') === 0) { SPD = +k.slice(4); }
    else if (k === 'box') { ST[k] = !ST[k]; restart = true; }
    else if (k === 'run') { if (RUN) stop(); else if (!A || A.t >= A.end) start(); else { RUN = 1; LAST = 0; requestAnimationFrame(tick); } }
    else if (k === 'end') toEnd();
    else if (k === 're') start();
    else if (k === 'man') { ST.manual = !ST.manual; if (B) B.manual('4031', ST.manual, manPh()); }
    else if (k === 'manF') { ST.manF = !ST.manF; restart = true; }
    else if (k === 'auto') { ST.auto = !ST.auto; if (ST.auto) { ST.manual = false; ST.plan = 'cur'; ST.ph = null; toastS('🤖 오른쪽 판 = 현행 신호 + 자동 끊기 — 왼쪽 현행과 견줌(다른 안과 함께 보려면 안을 다시 고르기)'); } restart = true; }
    else if (k === 'next') { if (!B) start(); if (!B.N['4031'].manual) { ST.manual = true; B.manual('4031', true, manPh()); } B.go('4031'); }
    else if (k === 'cut') { if (!B) start(); if (B.drop['4031']) { delete B.drop['4031']; toastS('⛔ 풀기 — 북→동 좌회전 다시 원래대로'); } else { B.drop['4031'] = ['nt.Lt']; toastS('⛔ 북→동 좌회전(반포대교에서 신세계 쪽)만 적색 — 신반포로 양방향(잠원IC 방향·동→서)과 다른 현시는 차례대로 간다 · 한 번 더 누르면 풀림'); } }
    if (restart) { A = null; B = null; stop(); setTimeout(paintHow, 0); if (k.indexOf('day:') === 0 || k.indexOf('act:') === 0 || k === 'box') { CMP = null; paintCmp(); } paintCtl(); start(); } else paintCtl();
  }
  function onInput(e) { var t = e.target; if (!t.hasAttribute || !t.hasAttribute('data-sv')) return; ST[t.getAttribute('data-sv')] = +t.value; var em = t.parentNode.querySelector('em'); if (em) em.textContent = t.getAttribute('data-sv') === 'bus' ? '× ' + t.value : t.getAttribute('data-sv') === 'occ' ? t.value + '%' : (+t.value).toLocaleString() + ' 대/시'; }
  function onChange(e) { var t = e.target; if (t.hasAttribute && t.hasAttribute('data-sv')) { stop(); CMP = null; paintCmp(); start(); } }
  function toastS(m) { var el = $('simMsg'); if (el) { el.textContent = m; el.style.display = 'block'; } }
  function srcList() {
    var L = (M.att || []).map(function (a) { return '<li><b>' + esc(a.nm) + '</b> — ' + esc(a.src || '') + '</li>'; }).concat((M.actions || []).map(function (a) { return '<li><b>' + esc(a.nm) + '</b> — ' + esc(a.src || '') + '</li>'; }));
    Object.keys(M.design || {}).forEach(function (k) { var d = M.design[k]; if (d && d.src) L.push('<li>' + esc(d.src) + '</li>'); });
    L.push('<li>' + esc(M.sat.quote) + ' · ' + esc(M.sat.note || '') + '</li><li>정지 차량 한 대 ' + M.spacing.v + 'm — ' + esc(M.spacing.note || '설계값') + '</li>');
    return '<details><summary>값의 출처 · 설계값 목록</summary><ul style="margin:4px 0;padding-left:18px;font-size:11.5px;line-height:1.5">' + L.join('') + '</ul></details>';
  }
  function open() {
    css(); need(function () {
      if (!ST) ST = defState();
      if (!PANEL) { PANEL = document.createElement('div'); PANEL.id = 'm2dSim'; document.body.appendChild(PANEL); PANEL.addEventListener('click', onClick); PANEL.addEventListener('input', onInput); PANEL.addEventListener('change', onChange); }
      PANEL.innerHTML = '<h3>🧪 시뮬 — ' + esc(AREA.nm) + '<button data-simx="1" aria-label="닫기">✕ 닫기</button></h3>' +
        '<div class="sn">교차로 넷(반포사거리·고속터미널·삼호가든·서울성모병원)과 블록 둘레 길 · 신호 = 교통과 현시도(4031·4028·4034) + T-Data(4019) · <b>개념 시연 — 예측·보증이 아니다</b></div>' +
        '<div class="warn">10/18 실측(ITS 속도)과 맞대 보면 막히는 모양·풀리는 시각은 맞고 일부 접근로는 틀린다(맞음 50/77) · <br>🏁 <b>현장 결과가 이김</b> — 서울성모병원 시차제(평일 16~20시 서→동 직진 23초 · 형님이 바꾼 것)는 현장에서 「많이 개선」(FK-4034-METER) · 이 시뮬은 반대로 나온다 → 시뮬이 틀린 것으로 본다(서쪽 접근로 수요가 설계값이라 늘 가득) · 다른 안도 현장 결과가 있으면 그것이 먼저</div>' +
        (window.tgLink ? '<div class="row" style="margin:2px 0 4px"><span class="sn" style="margin:0">🧩 엮임 보기</span>' + Object.keys(M.nodes).filter(function (k) { return M.nodes[k].int; }).map(function (k) { return '<button data-simlnk="' + esc(M.nodes[k].int) + '">' + esc(SHORT[k] || M.nodes[k].nm) + '</button>'; }).join('') + '</div>' : '') +
        '<div id="simLive"></div><div id="simRun"></div><div id="simMsg" class="warn" style="display:none"></div><div id="simRes"></div><div id="simHow"></div><div id="simCmp"></div><div id="simCtl"></div>' + srcList();
      PANEL.classList.add('on'); if (CH) CH.style.display = 'none'; CMP = null; paintCmp(); paintCtl(); start(); paintHow(); liveGet();
    });
  }
  function close() { stop(); if (PANEL) PANEL.classList.remove('on'); }
  window.tgSimUI = { open: open, close: close, near: near, state: function () { return ST; }, sims: function () { return [A, B]; } };
  function boot() { css(); cardHook(); chip(); overlay(); document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && PANEL && PANEL.classList.contains('on')) close(); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
