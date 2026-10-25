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
      { id: 'S', ic: '🏨', nm: '사평대로 — 메리어트 공유', ll: [37.50344, 127.006914] }, { id: 'W', ic: '🚌', nm: '반포대로 — 호남선 고속버스·백화점', ll: [37.503555, 127.002275] }] };
  var SHORT = { '4031': '고속터미널사거리', '4019': '고속터미널', '4028': '삼호가든', '4034': '서울성모병원', '4032': '반포대교남단' };
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
      '#m2dSim .two{display:grid;grid-template-columns:1fr 1fr;gap:6px}#m2dSim .pv{border:1px solid rgba(120,130,150,.35);border-radius:12px;padding:4px}#m2dSim .pv .pt{font-weight:800;font-size:13px;text-align:center}#m2dSim .pv svg{width:100%;height:auto;display:block}' +
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
  // ---- 받기 ----
  function need(cb) {
    if (M && window.tgSim) return cb();
    var go = function () { window.tgSim.load(AREA.id, '3').then(function (j) { M = j; cb(); }).catch(function () { alert('시뮬 자료를 받지 못했다 — 통신을 확인하고 다시'); }); };
    if (window.tgSim) return go();
    var s = document.createElement('script'); s.src = 'js/sim.js?v=3'; s.onload = go; s.onerror = function () { alert('시뮬 계산기(sim.js)를 받지 못했다'); }; document.head.appendChild(s);
  }
  // ---- 판 ----
  var DAYS = [['1018', '10/18(일) 재현', '2026-10-18'], ['1011', '10/11(일) 평소', '2026-10-11'], ['mt', '평일(월~목)', '2026-10-21'], ['fr', '금요일', '2026-10-23'], ['sa', '토요일', '2026-10-24'], ['su', '일요일', '2026-10-25']];   // 소유자 「평일·금·토·일도 변수로」 — 신호 계획·고속버스 시간표·평소 속도 모두 이 네 갈래
  function presetOf(k) { var P = M.preset || {}; return P[k] ? JSON.parse(JSON.stringify(P[k])) : null; }
  function att0(id) { return (M.att || []).filter(function (a) { return a.id === id; })[0] || {}; }
  function defState() {
    var p = presetOf('1018') || {};
    return { day: '1018', date: p.date || '2026-10-18', shin: (p.att && p.att.shin && p.att.shin.inPeak) || att0('shin').inPeak, fount: (p.att && p.att.fount && p.att.fount.inPeak) || att0('fount').inPeak,
      academy: att0('academy').inPeak || 0, bus: 1, act: {}, box: true, plan: 'A', ph: null, manual: false };
  }
  function exPhases() {   // 재편안 예시 — 의도 문서 「직진·좌회전 분리 · 측도 남북 양직진 · 출구 연장 현시」 · 주기는 현행(일 16~21시 패턴 14 · 180초)과 같게 · 초는 형님이 고친다
    return [{ d: 40, y: 4, ar: 1, mv: ['wt.St', 'et.St'], nm: '동서 양직진' }, { d: 30, y: 4, ar: 1, mv: ['et.St', 'wt.Lt'], nm: '출구 연장(동→서 직진 계속 · 서→북 좌회전) — 들어오는 차 끊김' },
      { d: 45, y: 3, ar: 1, mv: ['nt.St', 'st.St'], nm: '남북 양직진(측도)' }, { d: 30, y: 3, ar: 1, mv: ['nt.Lt'], nm: '북 좌회전(블록으로 들어감)' }, { d: 35, y: 3, ar: 1, mv: ['st.Lt'], nm: '남 좌회전' }];
  }
  function scen() {
    var act = Object.keys(ST.act).filter(function (k) { return ST.act[k]; });
    var a = { shin: { inPeak: ST.shin, outPeak: ST.shin }, fount: { inPeak: ST.fount }, academy: { inPeak: ST.academy }, busGB: { scale: ST.bus, off: ST.bus ? 0 : 1 }, busCT: { scale: ST.bus, off: ST.bus ? 0 : 1 } };
    return { date: ST.date, seed: 7, att: a, act: act, box: ST.box ? undefined : 0, from: 16 * 3600, to: 23 * 3600 };
  }
  /* 개선안 목록(4031 고속터미널사거리 · 소유자 「신호값별로 어떤 변화가 생길 수 있는지 — 개선안별로 시연」) — 현행은 그날 17시 현시도 계획 · 나머지는 그것을 고친 예시(초는 형님이 정한다) */
  function curPh() { return window.tgSim.planAt(M, '4031', 17 * 3600, window.tgSim.dowOf(ST.date)).ph.map(function (p) { return { d: p.d, y: p.y, ar: p.ar, mv: p.mv.slice(), nm: p.mv.join('+') }; }); }
  function plans() {
    var c = curPh(), K = function (f) { var q = JSON.parse(JSON.stringify(c)); f(q); return q; }, ex = exPhases(), exB = JSON.parse(JSON.stringify(ex)); exB[0].d -= 15; exB[1].d += 15;
    return [{ id: 'cur', nm: '현행', why: '그날 17시 교통과 현시도 계획 그대로', ph: null },
      { id: 'A', nm: 'A 재편안 예시', why: '직진·좌회전 분리 · 측도 남북 양직진 · 출구 연장(들어오는 차 끊김)', ph: ex },
      { id: 'B', nm: 'B 출구 연장 길게', why: 'A 에서 동서 양직진 −15초 → 출구 연장 +15초(나오는 차 더 · 들어오는 차 덜)', ph: exB },
      { id: 'C', nm: 'C 서직좌 줄이기', why: '현행 2현시(서직좌 — 블록으로 들어가는 서→동 직진) −15초 → 4현시 남직좌 +15초', ph: K(function (q) { if (q[1]) q[1].d -= 15; if (q[3]) q[3].d += 15; }) },
      { id: 'D', nm: 'D 북직좌 줄이기', why: '현행 3현시(북직좌 — 블록으로 들어가는 북→동 좌회전) −10초 → 1현시 동서 양직진 +10초', ph: K(function (q) { if (q[2]) q[2].d -= 10; if (q[0]) q[0].d += 10; }) },
      { id: 'E', nm: 'E 주기 늘리기', why: '현행 현시를 모두 1.2배(주기 늘려 한 번에 많이 보냄 — 대신 빨간불이 길다)', ph: K(function (q) { q.forEach(function (x) { x.d = Math.round(x.d * 1.2); }); }) }];
  }
  function planOf(id) { return plans().filter(function (p) { return p.id === id; })[0] || plans()[0]; }
  function altOf(ph) { if (!ph) return null; var P = window.tgSim.planAt(M, '4031', 17 * 3600, window.tgSim.dowOf(ST.date)); return { '4031': { ph: ph, off: P.off || 0 } }; }
  function alt() { var p = ST.ph || planOf(ST.plan).ph; return altOf(p); }
  // 개선안 모두 돌려 보기(같은 날·같은 수요·같은 차) — 결과 표에서 고르면 그 안으로 시연
  var CMP = null;
  function compare() {
    var L = plans(), i = 0, Rw = []; CMP = { busy: 1, rows: Rw }; paintCmp();
    (function next() { if (i >= L.length) { CMP.busy = 0; paintCmp(); return; } var p = L[i++], S = window.tgSim.create(M, scen(), altOf(p.ph)); S.runTo(S.end); var r = S.result(); r.id = p.id; r.nm = p.nm; r.why = p.why; Rw.push(r); paintCmp(); setTimeout(next, 30); })();
  }
  function paintCmp() {
    var el = $('simCmp'); if (!el) return; if (!CMP) { el.innerHTML = '<div class="row" style="margin-top:6px"><button data-sk="cmp" class="on">📊 개선안 모두 돌려 견주기</button><span class="sn" style="margin:0">현행·A~E 를 같은 날·같은 차로 16~23시 — 몇 초 걸림</span></div>'; return; }
    var Rw = CMP.rows.slice(), cur = Rw.filter(function (r) { return r.id === 'cur'; })[0];
    Rw.sort(function (a, b) { return a.delayVh - b.delayVh; });
    var dv = function (x, y) { if (!x || x === y) return ''; var p = Math.round((y - x) / x * 100); return ' <small style="color:' + (p < 0 ? '#16a34a' : '#dc2626') + '">' + (p > 0 ? '+' : '') + p + '%</small>'; };
    el.innerHTML = '<div class="sg">개선안별 결과(' + esc((DAYS.filter(function (d) { return d[0] === ST.day; })[0] || [])[1] || '') + ' · 16~23시 · 총 지체 적은 차례)' + (CMP.busy ? ' — 계산 중…' : '') + '</div><table><tr><th>안</th><th>총 지체</th><th>블록 갇힘</th><th>막힘→해소</th><th></th></tr>' +
      Rw.map(function (r) { return '<tr><td><b>' + esc(r.nm) + '</b><br><small>' + esc(r.why) + '</small></td><td>' + r.delayVh.toLocaleString() + (cur ? dv(cur.delayVh, r.delayVh) : '') + '</td><td>' + r.trappedMax + (cur ? dv(cur.trappedMax, r.trappedMax) : '') + '</td><td>' + (r.jamStart != null ? hh(r.jamStart) + '→' + (r.clearT != null ? hh(r.clearT) : '23시↑') : '없음') + '</td><td>' + (r.id === 'cur' ? '' : '<button data-sk="show:' + r.id + '">▶ 시연</button>') + '</td></tr>'; }).join('') + '</table>' +
      '<div class="sn">▶ 시연 = 왼쪽 현행 · 오른쪽 그 안으로 다시 돌림 · 같은 수요·같은 차라 차이는 신호에서만 온다 · 개념 시연(예측 아님)</div>';
  }
  function start() {
    stop(); A = window.tgSim.create(M, scen(), null); B = window.tgSim.create(M, scen(), alt());
    A.runTo(A.from); B.runTo(B.from); if (ST.manual) { B.manual('4031', true); }
    paintRun(); RUN = 1; LAST = 0; requestAnimationFrame(tick); paintCtl();
  }
  function stop() { RUN = 0; }
  function tick(ts) {
    if (!RUN || !A) return; if (!LAST) LAST = ts; var dt = Math.min(0.25, (ts - LAST) / 1000); LAST = ts;
    var n = Math.min(900, Math.round(dt * SPD)); for (var i = 0; i < n && A.t < A.end; i++) { A.step(); B.step(); }
    paintRun(); if (A.t >= A.end) { RUN = 0; paintCtl(); paintRes(); return; } requestAnimationFrame(tick);
  }
  function toEnd() { if (!A) start(); stop(); A.runTo(A.end); B.runTo(B.end); paintRun(); paintCtl(); paintRes(); }
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
    var sh = at.shin || {}, fo = at.fount || {};
    return '<div class="pi">막힌 접근로 <b>' + jam + '</b>곳 · 꼬리물기 ' + S.boxN + '번<br>신세계 문 앞 ' + (sh.door || 0) + '대 · 출차 대기 <b>' + (sh.out || 0) + '</b>대<br>공원 앞 ' + (fo.door || 0) + '대 · 지체 ' + R.delayVh.toLocaleString() + ' 대·시</div>';
  }
  function paintRun() {
    if (!A) return; var el = $('simRun'); if (!el) return;
    el.innerHTML = '<div class="row" style="justify-content:space-between"><span class="clock">' + hh(A.t) + '</span><span class="sn" style="margin:0">16:00 → 23:00 · 같은 차 · 같은 날</span></div><div class="two">' +
      '<div class="pv"><div class="pt">현행 신호</div>' + svg(A) + info(A) + '</div><div class="pv"><div class="pt">' + esc(ST.ph ? planOf(ST.plan).nm + '(고침)' : planOf(ST.plan).nm) + (B.N['4031'].manual ? ' · 🖐 수동' : '') + '</div>' + svg(B) + info(B) + '</div></div>' +
      '<div class="sn">길 색 = 그 길에 찬 정도(초록 40% 아래 · 노랑 · 빨강 80% 넘음 — 막힘) · 빨간 점 = 꼬리물기로 교차로가 막힘 · 보라 네모 = 출입구 4곳(숫자 = 문 앞·나가려고 기다리는 차) · 보라 화살표 = 블록 쪽 차로가 도는 방향(시계 방향)</div>';
  }
  function paintRes() {
    var el = $('simRes'); if (!el || !A) return; var a = A.result(), b = B.result();
    var mq = function (r) { var m = 0, k = ''; Object.keys(r.maxQm).forEach(function (x) { if (r.maxQm[x] > m) { m = r.maxQm[x]; k = x; } }); return m + 'm' + (k ? ' <small>(' + esc((SHORT[k.split('.')[0]] || k.split('.')[0]) + ' ' + ({ nt: '북', et: '동', st: '남', wt: '서' }[k.split('.')[1]] || '')) + ')</small>' : ''); };
    var dv = function (x, y) { if (!x) return ''; var p = Math.round((y - x) / x * 100); return '<small style="color:' + (p < 0 ? '#16a34a' : p > 0 ? '#dc2626' : 'inherit') + '">' + (p > 0 ? '+' : '') + p + '%</small>'; };
    el.innerHTML = '<div class="sg">결과(16~23시)</div><table><tr><th></th><th>현행</th><th>' + esc(planOf(ST.plan).nm) + '</th></tr>' +
      '<tr><td>총 지체</td><td>' + a.delayVh.toLocaleString() + ' 대·시</td><td>' + b.delayVh.toLocaleString() + ' ' + dv(a.delayVh, b.delayVh) + '</td></tr>' +
      '<tr><td>최대 대기 길이</td><td>' + mq(a) + '</td><td>' + mq(b) + '</td></tr>' +
      '<tr><td>블록 안에 갇힌 차(최대)</td><td>' + a.trappedMax + '대</td><td>' + b.trappedMax + '대 ' + dv(a.trappedMax, b.trappedMax) + '</td></tr>' +
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
      slider('shin', '신세계 입·출', ST.shin, 2000, 50, att0('shin').inT0 + '~' + att0('shin').inT1 + '시 들어옴 · ' + att0('shin').outT0 + '~' + att0('shin').outT1 + '시 나감') +
      slider('fount', '한강공원 분수', ST.fount, 1500, 50, '10월 분수 19:30~21:00 · 공원 주차장 받는 속도 ' + att0('fount').inCap + '대/시') +
      (wd ? slider('academy', '학원가(평일)', ST.academy, 1000, 50, '평일 15:30~19:00 · 지하차도 대신 위로(형님 현장 지식)') : '') +
      '<label class="sl"><b>🚌 고속버스(실측 × 배율)</b><input type="range" min="0" max="2" step="0.1" value="' + ST.bus + '" data-sv="bus"><em>× ' + ST.bus + '</em></label><div class="sn" style="margin:-2px 0 4px">TAGO 시간표 그날 갈래 그대로(×1) · 경부·영동 = 동 잠원로 출입구 · 호남 = 서 반포대로 출입구 · 0 = 끔</div>' +
      '<div class="row">' + chipB('box', '꼬리물기 있음', ST.box) + '</div>' +
      '<div class="sg">조치</div><div class="row">' + acts + '</div>' +
      '<div class="sg">개선안 — 4031 고속터미널사거리(오른쪽 판)</div><div class="row">' + plans().map(function (p) { return chipB('plan:' + p.id, p.nm, ST.plan === p.id); }).join('') + '</div><div class="sn">' + esc(planOf(ST.plan).why) + ' · 주기 ' + cyc + '초' + (ST.ph ? ' · 초를 고침' : '') + '</div>';
    if (ST.plan !== 'cur') h += ph.map(function (p, i) { return '<div class="ph"><b>' + (i + 1) + '</b><span>' + esc(p.nm || p.mv.join('+')) + '</span><button data-pd="' + i + ':-5">−5</button><b style="min-width:34px;text-align:center">' + p.d + '초</b><button data-pd="' + i + ':5">+5</button></div>'; }).join('');
    h += '<div class="sg">돌리기</div><div class="row">' + '<button data-sk="run" class="on">' + (RUN ? '⏸ 멈춤' : A ? '▶ 이어서' : '▶ 시작') + '</button>' + [300, 600, 1200].map(function (v) { return chipB('spd:' + v, '×' + v, SPD === v); }).join('') + '<button data-sk="end">⏩ 끝까지</button><button data-sk="re">↺ 처음부터</button></div>' +
      '<div class="sg">수동 조작 — 오른쪽 판 4031(실제 신호를 바꾸는 기능이 아니다)</div><div class="row">' + chipB('man', '🖐 수동', ST.manual) + '<button data-sk="next">다음 현시 ▶</button><button data-sk="cut">⛔ 들어오는 차만 끊기</button></div>' +
      (B && B.N['4031'].manual ? '<div class="sn">지금 현시 ' + (B.N['4031'].manual.i + 1) + ' — ' + esc(B.N['4031'].manual.ph[B.N['4031'].manual.i].mv.join(' + ')) + '</div>' : '');
    el.innerHTML = h;
  }
  function onClick(e) {
    var b = e.target.closest('[data-sk],[data-pd],[data-simx]'); if (!b) return;
    if (b.hasAttribute('data-simx')) { close(); return; }
    if (b.hasAttribute('data-pd')) { var q = b.getAttribute('data-pd').split(':'), ph = ST.ph || JSON.parse(JSON.stringify(planOf(ST.plan).ph || curPh())); ph[+q[0]].d = Math.max(8, ph[+q[0]].d + +q[1]); ST.ph = ph; A = null; stop(); paintCtl(); return; }
    var k = b.getAttribute('data-sk'), restart = false;
    if (k.indexOf('day:') === 0) { ST.day = k.slice(4); var d = DAYS.filter(function (x) { return x[0] === ST.day; })[0]; ST.date = d[2]; var p = presetOf(ST.day); if (p && p.att) { if (p.att.shin) ST.shin = p.att.shin.inPeak; if (p.att.fount) ST.fount = p.att.fount.inPeak; } restart = true; }
    else if (k.indexOf('act:') === 0) { var id = k.slice(4); ST.act[id] = !ST.act[id]; restart = true; }
    else if (k.indexOf('plan:') === 0) { ST.plan = k.slice(5); ST.ph = null; restart = true; }
    else if (k.indexOf('show:') === 0) { ST.plan = k.slice(5); ST.ph = null; restart = true; var rn = $('simRun'); if (rn) rn.scrollIntoView({ block: 'start', behavior: 'smooth' }); }
    else if (k === 'cmp') { compare(); return; }
    else if (k.indexOf('spd:') === 0) { SPD = +k.slice(4); }
    else if (k === 'box') { ST[k] = !ST[k]; restart = true; }
    else if (k === 'run') { if (RUN) stop(); else if (!A || A.t >= A.end) start(); else { RUN = 1; LAST = 0; requestAnimationFrame(tick); } }
    else if (k === 'end') toEnd();
    else if (k === 're') start();
    else if (k === 'man') { ST.manual = !ST.manual; if (B) B.manual('4031', ST.manual); }
    else if (k === 'next') { if (!B) start(); if (!B.N['4031'].manual) { ST.manual = true; B.manual('4031', true); } B.go('4031'); }
    else if (k === 'cut') { if (!B) start(); if (!B.N['4031'].manual) { ST.manual = true; B.manual('4031', true); } var ma = B.N['4031'].manual, j = -1;
      ma.ph.forEach(function (p, i) { if (j < 0 && p.mv.indexOf('wt.St') < 0 && p.mv.indexOf('nt.Lt') < 0 && p.mv.indexOf('et.St') >= 0) j = i; });
      if (j < 0) ma.ph.forEach(function (p, i) { if (j < 0 && p.mv.indexOf('wt.St') < 0 && p.mv.indexOf('nt.Lt') < 0) j = i; });
      if (j >= 0) B.go('4031', j); toastS(j >= 0 ? '⛔ 블록으로 들어가는 차(서→동 직진 · 북→동 좌회전)를 끊는 현시 ' + (j + 1) + '로' + (ma.ph[j].mv.indexOf('et.St') >= 0 ? ' — 나오는 차(동→서 직진)는 계속 간다' : ' — ⚠ 이 신호 계획에는 나오는 차를 함께 보내는 현시가 없다') : '이 계획에는 들어오는 차만 끊는 현시가 없다'); }
    if (restart) { A = null; B = null; stop(); if (k.indexOf('day:') === 0 || k.indexOf('act:') === 0 || k === 'box') { CMP = null; paintCmp(); } paintCtl(); start(); } else paintCtl();
  }
  function onInput(e) { var t = e.target; if (!t.hasAttribute || !t.hasAttribute('data-sv')) return; ST[t.getAttribute('data-sv')] = +t.value; var em = t.parentNode.querySelector('em'); if (em) em.textContent = t.getAttribute('data-sv') === 'bus' ? '× ' + t.value : (+t.value).toLocaleString() + ' 대/시'; }
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
        '<div class="sn">교차로 넷(고속터미널사거리·고속터미널·삼호가든·서울성모병원)과 블록 둘레 길 · 신호 = 교통과 현시도(4031·4028·4034) + T-Data(4019) · <b>개념 시연 — 예측·보증이 아니다</b></div>' +
        '<div class="warn">10/18 실측(ITS 속도)과 맞대 보면 막히는 모양·풀리는 시각은 맞고 일부 접근로는 틀린다(맞음 52/77) · 서울성모병원 시차제 효과는 형님 현장 결과(많이 개선)와 반대로 나온다 — 고치는 중</div>' +
        '<div id="simRun"></div><div id="simMsg" class="warn" style="display:none"></div><div id="simRes"></div><div id="simCmp"></div><div id="simCtl"></div>' + srcList();
      PANEL.classList.add('on'); if (CH) CH.style.display = 'none'; CMP = null; paintCmp(); paintCtl(); start();
    });
  }
  function close() { stop(); if (PANEL) PANEL.classList.remove('on'); }
  window.tgSimUI = { open: open, close: close, near: near, state: function () { return ST; }, sims: function () { return [A, B]; } };
  function boot() { css(); cardHook(); chip(); overlay(); document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && PANEL && PANEL.classList.contains('on')) close(); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
