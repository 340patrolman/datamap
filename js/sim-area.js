/* 🧪 시뮬 — 서울 여러 구역(2026-10-25 · 소유자 「잘 작동되면 서울시 전역으로 확대」)
   반포 터미널 블록(js/sim-ui.js · 손으로 짠 구역)과 따로 — 자동으로 엮은 구역(tools/sim/area-bake.py · 목록 data/sim-areas.json)을 같은 꼴 하나로 연다.
   지도(map2d.js)는 고치지 않는다 — 카드(#m2dCard)를 지켜보다 구역 교차로 카드에 단추를 붙이고, 지도 가운데가 구역 둘레면 떠 있는 단추를 띄운다(TGMap2D.view·LL 만 읽음).
   고를 것 = 요일 · 시간대 · 수요(평소 속도로 맞춘 배율에 곱함) · 들어오는 길 막기 · 신호 현시 길이(±5초) → 현행과 바꾼 안을 같은 날·같은 차로 두 판 견준다.
   계산은 js/sim.js(window.tgSim) · 개념 시연이다 — 예측·보증이 아니다(판 아래에 늘 적는다). */
(function () {
  'use strict';
  var IDX = null, AR = null, M = null, ST = null, A = null, B = null, RUN = 0, SPD = 600, LAST = 0, PANEL = null, CH = null, RES = null;
  var DAYS = [['mt', '평일(월~목)', '2026-10-21'], ['fr', '금요일', '2026-10-23'], ['sa', '토요일', '2026-10-24'], ['su', '일요일', '2026-10-25']];
  var WINS = [['am', '아침 7~10시', 7, 10], ['md', '낮 12~15시', 12, 15], ['pm', '저녁 16~22시', 16, 22]];
  var LEGA = { nt: 0, ne: 45, et: 90, se: 135, st: 180, sw: 225, wt: 270, nw: 315 }, LEGK = { nt: '북', et: '동', st: '남', wt: '서', ne: '북동', se: '남동', sw: '남서', nw: '북서' };
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function hh(t) { if (t == null) return '-'; var h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60); return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m; }
  function css() {
    if ($('simACss')) return; var s = document.createElement('style'); s.id = 'simACss';
    s.textContent = '#m2dSimAChip{position:fixed;left:50%;transform:translateX(-50%);top:calc(var(--toph,110px) + 10px);z-index:7;border:0;border-radius:22px;padding:10px 16px;font:800 14px/1.2 inherit;background:#7c3aed;color:#fff;box-shadow:0 6px 18px rgba(0,0,0,.3);cursor:pointer;display:none}' +
      '#m2dSimA{position:fixed;left:0;right:0;bottom:0;z-index:25;max-height:90%;overflow:auto;display:none;background:var(--panel,#fff);color:var(--ink,#111);border-radius:18px 18px 0 0;box-shadow:0 -8px 30px rgba(0,0,0,.35);padding:10px 10px calc(14px + env(safe-area-inset-bottom));font-size:13px}' +
      '@media (min-width:900px){#m2dSimA{left:auto;right:12px;bottom:12px;width:760px;max-height:calc(100% - 90px);border-radius:16px}}' +
      '#m2dSimA.on{display:block}#m2dSimA h3{margin:0 0 2px;font-size:16px;display:flex;align-items:center;gap:6px}#m2dSimA h3 button{margin-left:auto}' +
      '#m2dSimA .sn{color:var(--ink2,#555);font-size:12px;line-height:1.4;margin:2px 0 6px}#m2dSimA .sg{font-weight:800;font-size:12px;color:var(--ink2,#555);margin:8px 0 3px}' +
      '#m2dSimA button,#m2dSimA select{font:inherit;border:1px solid rgba(120,130,150,.45);background:transparent;color:inherit;border-radius:14px;padding:6px 10px;min-height:34px;cursor:pointer}#m2dSimA button.on{background:#7c3aed;border-color:#7c3aed;color:#fff}' +
      '#m2dSimA .row{display:flex;flex-wrap:wrap;gap:5px;align-items:center}#m2dSimA label.sl{display:flex;align-items:center;gap:6px;width:100%;margin:2px 0}#m2dSimA label.sl input{flex:1}#m2dSimA label.sl b{min-width:90px;font-size:12px}#m2dSimA label.sl em{font-style:normal;min-width:52px;text-align:right;font-variant-numeric:tabular-nums}' +
      '#m2dSimA .two{display:grid;grid-template-columns:1fr 1fr;gap:6px}#m2dSimA .pv{border:1px solid rgba(120,130,150,.35);border-radius:12px;padding:4px}#m2dSimA .pv .pt{font-weight:800;font-size:13px;text-align:center}#m2dSimA .pv svg{width:100%;height:auto;display:block}' +
      '#m2dSimA .pv .pi{font-size:11.5px;line-height:1.45;font-variant-numeric:tabular-nums}#m2dSimA table{border-collapse:collapse;width:100%;font-size:12.5px}#m2dSimA td,#m2dSimA th{border-bottom:1px solid rgba(120,130,150,.25);padding:4px 3px;text-align:right}#m2dSimA td:first-child,#m2dSimA th:first-child{text-align:left}' +
      '#m2dSimA .ph{display:flex;align-items:center;gap:4px;margin:2px 0;font-size:12px}#m2dSimA .ph span{flex:1}#m2dSimA .ph button{min-height:28px;padding:2px 8px}#m2dSimA .warn{background:rgba(234,179,8,.15);border-radius:10px;padding:6px 8px;font-size:12px;line-height:1.45;margin:6px 0}' +
      '#m2dSimA details summary{cursor:pointer;font-weight:700;font-size:12px;color:var(--ink2,#555);margin-top:6px}#m2dSimA .clock{font-size:20px;font-weight:900;font-variant-numeric:tabular-nums}';
    document.head.appendChild(s);
  }
  // ---- 어디서 보일까 ----
  function mpu(T, c) { var c0 = T.LL(c[1], c[0]), e0 = T.LL(c[1] + 0.01, c[0]); return [c0, 883 / Math.max(1e-9, Math.abs(e0[0] - c0[0]))]; }   /* 경도 0.01° ≈ 883m(위도 37.5) */
  function nearArea() {
    var T = window.TGMap2D; if (!IDX || !T || !T.view || !T.LL || T.view.s <= 0.12) return null;
    if (window.tgSimUI && window.tgSimUI.near && window.tgSimUI.near()) return null;   /* 반포 블록이 먼저 */
    var best = null, bd = 1e9; IDX.areas.forEach(function (a) { var q = mpu(T, a.c), d = Math.hypot(T.view.cx - q[0][0], T.view.cy - q[0][1]) * q[1]; if (d < a.r + 250 && d < bd) { bd = d; best = a; } }); return best;
  }
  function areaOfName(t) { if (!IDX) return null; var hit = null; IDX.areas.forEach(function (a) { if (hit) return; a.sig.forEach(function (s) { if (!hit && s[1] && t.indexOf(s[1]) >= 0 && !/\(연등\)/.test(s[1])) hit = a; }); }); return hit; }
  function cardHook() {
    var c = $('m2dCard'); if (!c || !window.MutationObserver) return;
    new MutationObserver(function () {
      if (!c.classList.contains('on') || c.querySelector('[data-simarea]') || c.querySelector('[data-simblk]')) return;
      var h = c.querySelector('h3'), a = h && areaOfName(h.textContent || ''); if (!a) return;
      var bx = c.querySelector('.lg-btns') || c.querySelector('.dhb'), b = document.createElement('button'); b.setAttribute('data-simarea', a.id);
      b.title = '만약 신호·수요·길 막기를 바꾸면? — ' + a.nm + '(신호 교차로 ' + a.sig.length + ')를 두 판으로 견준다 · 개념 시연';
      b.textContent = '🧪 시뮬 — ' + a.nm; b.style.cssText = 'background:#7c3aed;color:#fff;border-color:#7c3aed';
      b.onclick = function (e) { e.preventDefault(); e.stopPropagation(); open(a.id); };
      if (bx) bx.appendChild(b); else h.insertAdjacentElement('afterend', b);
    }).observe(c, { childList: true, subtree: false, attributes: true, attributeFilter: ['class'] });
  }
  function chip() {
    CH = document.createElement('button'); CH.id = 'm2dSimAChip'; CH.title = '신호·수요·길 막기를 바꿔 두 판으로 견준다(개념 시연)'; document.body.appendChild(CH);
    CH.onclick = function () { var a = nearArea(); if (a) open(a.id); };
    setInterval(function () {
      var cd = $('m2dCard'), a = nearArea(), v = a && !(PANEL && PANEL.classList.contains('on')) && !($('m2dSim') && $('m2dSim').classList.contains('on')) && !(cd && cd.classList.contains('on') && cd.querySelector('[data-simarea],[data-simblk]'));
      if (a) CH.textContent = '🧪 시뮬 — ' + a.nm; CH.style.display = v ? 'block' : 'none';
    }, 800);
  }
  // ---- 자료 ----
  function need(id, cb) {
    var go = function () {
      if (M && AR && AR.id === id) return cb();
      AR = IDX.areas.filter(function (a) { return a.id === id; })[0];
      window.tgSim.load(id, IDX.made).then(function (j) {
        M = j; M.actions = Object.keys(M.entry).map(function (e) { return { id: 'x:' + e, nm: '막기 — ' + (M.links[e].nm || e), closeEntry: [e] }; });   /* 들어오는 길 막기 = 화면이 만든 조치 */
        ST = null; RES = null; geo(); cb();
      }).catch(function () { alert('시뮬 자료를 받지 못했다 — 통신을 확인하고 다시'); });
    };
    if (window.tgSim) return go();
    var s = document.createElement('script'); s.src = 'js/sim.js?v=19'; s.onload = go; s.onerror = function () { alert('시뮬 계산기(sim.js)를 받지 못했다'); }; document.head.appendChild(s);
  }
  function defState() { var d = new Date(), h = d.getHours(); return { day: ['su', 'mt', 'mt', 'mt', 'mt', 'fr', 'sa'][d.getDay()], win: h >= 7 && h < 11 ? 'am' : h >= 11 && h < 16 ? 'md' : 'pm', k: 100, shut: {}, edit: {}, sel: Object.keys(M.nodes).filter(function (k) { return M.nodes[k].ty === 'sig'; })[0] }; }
  function wOf() { return WINS.filter(function (w) { return w[0] === ST.win; })[0]; }
  function dOf() { return DAYS.filter(function (d) { return d[0] === ST.day; })[0]; }
  function scen(withAct) {
    var w = wOf(), c = M.cal || {};
    return { date: dOf()[2], seed: 7, from: w[2] * 3600, to: w[3] * 3600, bgAll: (c.all || 1) * ST.k / 100, act: withAct ? Object.keys(ST.shut).map(function (e) { return 'x:' + e; }) : [] };
  }
  function basePlan(id) { var w = wOf(), t = Math.round((w[2] + w[3]) / 2 * 3600); return window.tgSim.planAt(M, id, t, window.tgSim.dowOf(dOf()[2]), null); }
  /* 신호를 바꾼 교차로는 두 판 모두 그 시간대 가운데 계획 하나로 고정한다(현행 = 고친 것 없이 · 바꾼 안 = 고친 것) — 시간대 안 계획 바뀜이 차이에 섞이지 않게 */
  function alt(edited) { var o = null; Object.keys(ST.edit).forEach(function (id) { var d = ST.edit[id], P = basePlan(id); if (!d.some(function (x) { return x; })) return; o = o || {}; o[id] = { off: P.off, ph: P.ph.map(function (p, i) { return { d: Math.max(5, p.d + (edited ? d[i] || 0 : 0)), y: p.y, ar: p.ar, mv: p.mv }; }) }; }); return o; }
  /* 신호 기록에 녹색이 한 번도 없는 접근로 — T-Data 가 그 방향을 못 읽은 기록이면 그 길은 시뮬에서 늘 적색이라 줄이 길게 나온다(실제와 다름) · 화면에 밝힌다 */
  function noGreen(gap) { var L = []; Object.keys(M.nodes).forEach(function (id) { var n = M.nodes[id]; if (n.ty !== 'sig') return; var P = basePlan(id), G = {}, F = {}; (P.win || []).forEach(function (w) { var lg = String(w[0]).split('.')[0]; if (w[4] === 'gap') F[lg] = 1; else G[lg] = 1; });
    Object.keys(n.legs).forEach(function (lg) { if (n.legs[lg].in && !G[lg] && (gap ? F[lg] : !F[lg])) L.push(n.nm + ' ' + (LEGK[lg] || lg) + '쪽에서'); }); }); return L; }
  function changed() { return Object.keys(ST.shut).length > 0 || !!alt(1); }
  // ---- 구역 그림(두 판 같은 꼴) — 길 색 = 점유(대수 ÷ 길이×차로÷간격) ----
  var GEO = null;
  function geo() {
    var c = AR.c, P = {}, xs = [], ys = [], R = AR.r * 0.55;
    Object.keys(M.nodes).forEach(function (k) { var n = M.nodes[k]; P[k] = [(n.ll[1] - c[1]) * 88200, -(n.ll[0] - c[0]) * 111000]; });
    var segs = [];
    Object.keys(M.links).forEach(function (k) {
      var l = M.links[k], a, b;
      if (l.fr && l.to && P[l.fr] && P[l.to]) { a = P[l.fr]; b = P[l.to]; }
      else if (!l.fr && l.to && P[l.to]) { var g = (LEGA[l.oto] || 0) * Math.PI / 180, L = Math.min(R, Math.max(90, l.len * 0.5)); b = P[l.to]; a = [b[0] + Math.sin(g) * L, b[1] - Math.cos(g) * L]; }
      else if (l.fr && !l.to && P[l.fr] && l.sink) { var g2 = (LEGA[l.ofr] || 0) * Math.PI / 180, L2 = R * 0.6; a = P[l.fr]; b = [a[0] + Math.sin(g2) * L2, a[1] - Math.cos(g2) * L2]; }
      else return;
      var dx = b[0] - a[0], dy = b[1] - a[1], d = Math.hypot(dx, dy) || 1, ox = -dy / d * 9, oy = dx / d * 9;   /* 오른쪽 통행 — 방향마다 오른쪽으로 비킴 */
      segs.push({ k: k, a: [a[0] + ox, a[1] + oy], b: [b[0] + ox, b[1] + oy], sink: !!l.sink }); xs.push(a[0], b[0]); ys.push(a[1], b[1]);
    });
    Object.keys(P).forEach(function (k) { xs.push(P[k][0]); ys.push(P[k][1]); });
    var x0 = Math.min.apply(null, xs) - 40, x1 = Math.max.apply(null, xs) + 40, y0 = Math.min.apply(null, ys) - 30, y1 = Math.max.apply(null, ys) + 30;
    GEO = { P: P, segs: segs, vb: [x0, y0, x1 - x0, y1 - y0] };
  }
  function col(r) { return r >= 0.8 ? '#dc2626' : r >= 0.6 ? '#f97316' : r >= 0.3 ? '#eab308' : '#22c55e'; }
  function svg(S) {
    var G = GEO, k9 = G.vb[2] / 320, h = '<svg viewBox="' + G.vb.map(function (v) { return v.toFixed(0); }).join(' ') + '" role="img" aria-label="구역 길 막힘 그림">';
    G.segs.forEach(function (g) { var L = S.L[g.k], r = g.sink ? 0 : L.n / L.cap; h += '<line x1="' + g.a[0].toFixed(0) + '" y1="' + g.a[1].toFixed(0) + '" x2="' + g.b[0].toFixed(0) + '" y2="' + g.b[1].toFixed(0) + '" stroke="' + (g.sink ? 'rgba(120,130,150,.35)' : col(r)) + '" stroke-width="' + (g.sink ? 3 : 7) * k9 + '" stroke-linecap="round"/>'; });
    Object.keys(G.P).forEach(function (k) { var n = M.nodes[k], p = G.P[k], sig = n.ty === 'sig'; h += '<circle cx="' + p[0].toFixed(0) + '" cy="' + p[1].toFixed(0) + '" r="' + (sig ? 9 : 5) * k9 + '" fill="' + (sig ? '#1e3a8a' : '#94a3b8') + '" stroke="#fff" stroke-width="' + 2 * k9 + '"/>';
      if (sig && !/\(연등\)/.test(n.nm || '')) h += '<text x="' + p[0].toFixed(0) + '" y="' + (p[1] - 13 * k9).toFixed(0) + '" font-size="' + (11 * k9).toFixed(1) + '" font-weight="800" text-anchor="middle" fill="#111" stroke="#fff" stroke-width="' + 3 * k9 + '" paint-order="stroke">' + esc(n.nm) + '</text>'; });
    return h + '</svg>';
  }
  function info(S) { var s = S.samp[S.samp.length - 1]; if (!s) return '몸풀기 중…'; return '접근로 기다림 <b>' + s.q + '</b>대 · 들어오지 못한 차 <b>' + s.back + '</b> · 막힌 접근로 <b>' + s.jam.length + '</b>'; }
  function paintRun() {
    var el = $('simARun'); if (!el || !A) return;
    el.innerHTML = '<div class="row"><span class="clock">' + hh(Math.max(A.t, A.from)) + '</span><span class="sn" style="margin:0">' + esc(dOf()[1]) + ' · ' + esc(wOf()[1]) + (A.t < A.from ? ' · 몸풀기(빈 길에서 시작하지 않으려고 두 시간 먼저 돌림)' : '') + '</span></div>' +
      '<div class="two"><div class="pv"><div class="pt">현행</div>' + svg(A) + '<div class="pi">' + info(A) + '</div></div><div class="pv"><div class="pt">바꾼 안' + (changed() ? '' : ' <small>(바꾼 것 없음)</small>') + '</div>' + svg(B) + '<div class="pi">' + info(B) + '</div></div></div>' +
      '<div class="sn">길 색 = 그 길에 찬 차의 몫(초록 30% 아래 · 노랑 · 주황 60%↑ · 빨강 80%↑ 막힘) · 오른쪽 통행이라 방향마다 오른쪽 줄</div>';
  }
  function paintRes() {
    var el = $('simARes'); if (!el) return; if (!A || A.t < A.end) { el.innerHTML = ''; return; }
    var a = A.result(), b = B.result(), dv = function (x, y) { if (!x || x === y) return ''; var p = Math.round((y - x) / x * 100); return ' <small style="color:' + (p < 0 ? '#16a34a' : '#dc2626') + '">' + (p > 0 ? '+' : '') + p + '%</small>'; };
    var jm = function (r) { return r.jamStart != null ? hh(r.jamStart) + '→' + (r.clearT != null ? hh(r.clearT) : '끝까지') : '없음'; };
    var ks = Object.keys(a.maxQm).concat(Object.keys(b.maxQm)).filter(function (k, i, z) { return z.indexOf(k) === i; }).sort(function (x, y) { return Math.max(b.maxQm[y] || 0, a.maxQm[y] || 0) - Math.max(b.maxQm[x] || 0, a.maxQm[x] || 0); }).slice(0, 8);
    var apNm = function (k) { var p = k.split('.'), n = M.nodes[p[0]]; return (n ? n.nm : p[0]) + ' ' + (LEGK[p[1]] || p[1]) + '쪽에서'; };
    el.innerHTML = '<div class="sg">결과(' + esc(dOf()[1]) + ' · ' + esc(wOf()[1]) + ')</div><table><tr><th></th><th>현행</th><th>바꾼 안</th></tr>' +
      '<tr><td>총 지체(대·시)</td><td>' + a.delayVh.toLocaleString() + '</td><td>' + b.delayVh.toLocaleString() + dv(a.delayVh, b.delayVh) + '</td></tr>' +
      '<tr><td>막힘 시작→풀림</td><td>' + jm(a) + '</td><td>' + jm(b) + '</td></tr>' +
      '<tr><td>한꺼번에 막힌 접근로(가장 많을 때)</td><td>' + a.jamMax + '</td><td>' + b.jamMax + '</td></tr>' +
      '<tr><td>꼬리물기(교차로 안에 선 차)</td><td>' + a.box + '</td><td>' + b.box + '</td></tr></table>' +
      '<div class="sg">접근로별 가장 긴 줄(m)</div><table><tr><th>접근로</th><th>현행</th><th>바꾼 안</th></tr>' + ks.map(function (k) { return '<tr><td>' + esc(apNm(k)) + '</td><td>' + (a.maxQm[k] || 0) + '</td><td>' + (b.maxQm[k] || 0) + dv(a.maxQm[k] || 0, b.maxQm[k] || 0) + '</td></tr>'; }).join('') + '</table>' +
      (function () { var g = noGreen(), f = noGreen(1); return (f.length ? '<div class="warn">✎ 신호 기록에 녹색이 없어 <b>빈 시간으로 채운</b> 접근로 — ' + esc(f.join(' · ')) + ' · 서울시 T-Data 가 그 방향을 못 읽어, 주기 안에서 읽힌 녹색이 없는 가장 긴 시간을 그 길 녹색으로 줌(설계값 — 실제는 보행 현시 등으로 더 짧을 수 있다)</div>' : '') +
        (g.length ? '<div class="warn">⚠ 신호 기록에 녹색이 없는 접근로 — ' + esc(g.join(' · ')) + ' · 시뮬에서는 늘 적색(우회전만 빠짐) → 그 줄은 실제보다 길게 나온다</div>' : ''); })() +
      '<div class="sn">같은 날·같은 수요·같은 차(같은 씨앗)라 두 판의 차이는 바꾼 것에서만 온다 · 줄 길이 = 기다리는 차 × 차 간격 ÷ 차로 · 개념 시연(예측 아님)</div>';
  }
  function paintCtl() {
    var el = $('simACtl'); if (!el) return;
    var chips = function (L, cur, k) { return L.map(function (d) { return '<button data-sa="' + k + ':' + d[0] + '"' + (d[0] === cur ? ' class="on"' : '') + '>' + esc(d[1]) + '</button>'; }).join(''); };
    var sigs = Object.keys(M.nodes).filter(function (k) { return M.nodes[k].ty === 'sig'; });
    var P = basePlan(ST.sel), d = ST.edit[ST.sel] || [];
    var phs = P.ph.map(function (p, i) { var mv = p.mv.map(function (m) { var q = m.split('.'); return (LEGK[q[0]] || q[0]) + ({ St: '직진', Lt: '좌회전', Rt: '우회전', Ut: '유턴', S: '직진', L: '좌회전', R: '우회전', U: '유턴' }[q[1]] || q[1]); }).join('·'); var v = Math.max(5, p.d + (d[i] || 0));
      return '<div class="ph"><span>' + (i + 1) + '현시 <b>' + v + '초</b>' + (d[i] ? ' <small>(원래 ' + p.d + ')</small>' : '') + ' — ' + esc(mv || '-') + '</span><button data-sa="ph:' + i + ':-5">−5</button><button data-sa="ph:' + i + ':5">+5</button></div>'; }).join('');
    el.innerHTML = '<div class="sg">요일</div><div class="row">' + chips(DAYS, ST.day, 'day') + '</div>' +
      '<div class="sg">시간대</div><div class="row">' + chips(WINS, ST.win, 'win') + '</div>' +
      '<label class="sl"><b>수요(평소 = 100%)</b><input type="range" min="50" max="160" step="5" value="' + ST.k + '" data-sa="k"><em>' + ST.k + '%</em></label>' +
      '<div class="sg">바꾼 안 — 신호 현시 길이</div><div class="row"><select data-sa="sel">' + sigs.map(function (k) { return '<option value="' + esc(k) + '"' + (k === ST.sel ? ' selected' : '') + '>' + esc(M.nodes[k].nm) + ' (' + esc(k) + ')' + (ST.edit[k] && ST.edit[k].some(function (x) { return x; }) ? ' ✎' : '') + '</option>'; }).join('') + '</select><button data-sa="reset">↺ 신호 원래대로</button></div>' +
      '<div class="sn">' + esc(wOf()[1]) + ' 가운데 시각의 계획 · 주기 ' + P.c + '초 · 출처 ' + esc(P.src || '') + (P.day ? ' ' + esc(P.day) : '') + ' · 현시를 늘리면 주기도 늘어난다 · 고친 교차로는 두 판 모두 이 계획 하나로 고정(시간대 안 계획 바뀜을 빼고 견줌)</div>' + phs +
      '<div class="sg">바꾼 안 — 들어오는 길 막기(라바콘·통제)</div><div class="row">' + Object.keys(M.entry).map(function (e) { return '<button data-sa="shut:' + esc(e) + '"' + (ST.shut[e] ? ' class="on"' : '') + '>⛔ ' + esc((M.links[e].nm || e).replace(' — 들어옴', '')) + ' (' + esc(M.nodes[M.links[e].to] ? M.nodes[M.links[e].to].nm : '') + ')</button>'; }).join('') + '</div>' +
      '<div class="row" style="margin-top:8px"><button data-sa="play" class="on">▶ 두 판 시연</button><button data-sa="end">⏩ 끝까지 · 결과</button><button data-sa="spd">속도 ×' + (SPD / 600) + '</button></div>';
  }
  function srcList() {
    var L = ['<li>구역 = ' + esc(M.about || '') + '</li>', '<li>신호 = 교통과 현시도(있으면) → 서울시 T-Data 방향별 실측 기록(요일·시각마다 한 기록 · 빠진 이동류는 가까운 기록에서 채움)</li>',
      '<li>수요 = 서울시 교통량 조사(같은 길 이름 1.2km 안) · 없으면 차로 × 차로당 대수(설계값) × 평소 속도로 맞춘 배율(' + esc((M.cal && M.cal.src) || '') + ')</li>',
      '<li>맞음 = 평소 속도(ITS 가운데값)와 맞대 본 접근로·시간 칸 ' + AR.mh + '/' + AR.mn + ' · 실측 막힘(6km/h 이하) 칸 가운데 시뮬도 막힘 ' + AR.jh + '/' + AR.jn + ' · 실측 없는 들어오는 길까지 「막히지 않음」으로 세면 ' + AR.hit + '/' + AR.n + ' (' + esc(AR.calDay || '') + ' 평일 16~21시 · 수요 배율은 이 칸이 가장 잘 맞는 값으로 맞춤)</li>'];
    (M.log || []).slice(0, 12).forEach(function (x) { L.push('<li>' + esc(typeof x === 'string' ? x : JSON.stringify(x)) + '</li>'); });
    return '<details><summary>값의 출처 · 한계</summary><ul style="margin:4px 0;padding-left:18px;font-size:11.5px;line-height:1.5">' + L.join('') + '</ul></details>';
  }
  // ---- 📡 지금 실측(ITS) — data/live-spd-six.json(이 PC 가 약 11분마다 받아 올림 · 20분 넘으면 판정 안 함) · 평소 = 그 링크의 평소 속도(nsp · 요일 갈래-시) ----
  var LIVE = null, LOOP = null, APRS = null;
  function liveGet() {
    fetch('data/live-spd-six.json?t=' + Math.floor(Date.now() / 300000)).then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { LIVE = j; paintLive(); }).catch(function () {});
    /* 막힘 고리(data/onto-loops.json · sim 칸이 이 구역인 고리) — 네 변 = 「APR-교차로-들어오는 쪽」 · ITS 링크는 data/sig-approach-seocho.json 에서(엮임 보기·반포 sim-ui 와 같은 곳) */
    fetch('data/onto-loops.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { LOOP = j && (j.loops || []).filter(function (x) { return x.sim === AR.id; })[0] || null; paintLive(); }).catch(function () {});
    fetch('data/sig-approach-seocho.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { APRS = j; paintLive(); }).catch(function () {});
  }
  function legLinks(g) {
    if (g.links && g.links.length) return g.links.map(function (x) { return [x, 1]; });
    if (g.apr && APRS) { var q = g.apr.split('-'), sp = APRS.spots && APRS.spots[q[1]], r = sp && sp.in && sp.in[q[2]] && sp.in[q[2]][0]; if (r && r[4]) return r[4]; }
    return [];
  }
  function legSpd(g, M9) { var L = legLinks(g), w = 0, sm = 0, first = null; L.forEach(function (x) { var v = M9[x[0]]; if (v == null) return; if (first == null) first = v; sm += v * x[1]; w += x[1]; }); return g.links ? first : w ? Math.round(sm / w) : null; }
  function legSim(g) { var q = (g.apr || '').split('-'); if (q.length < 3) return null; var hit = null; Object.keys(M.links).forEach(function (k) { var l = M.links[k]; if (l.to === q[1] && l.oto === q[2]) hit = k; }); return hit; }
  function loopRow(sm, age) {
    if (!LOOP || !LOOP.legs) return ''; var jr = 0, nr = 0, hit = 0, nn = 0;
    var cells = LOOP.legs.map(function (g) { var v = legSpd(g, LIVE.m), k = legSim(g), mk = ''; if (v != null) { nr++; if (v <= 6) jr++; }
      if (!k) mk = ' <small>(시뮬 구역 밖)</small>'; else if (sm && v != null && age <= 20) { var sj = (sm.occ[k] || 0) >= 0.8 * A.L[k].cap; nn++; if (sj === (v <= 6)) { hit++; mk = ' ✓'; } else mk = ' ✗'; }
      return '<span style="white-space:nowrap">' + esc((g.nm || '').split(' — ')[0]) + ' <b style="color:' + (v == null ? 'inherit' : v <= 6 ? '#dc2626' : v <= 12 ? '#ca8a04' : '#16a34a') + '">' + (v == null ? '값 없음' : v) + '</b>' + mk + '</span>'; });
    return '<br>🔁 <b>' + esc(LOOP.nm || LOOP.id) + '</b> 네 변: ' + cells.join(' · ') + (nr ? ' — 막힌 변 ' + jr + '/' + nr : '') + (nn ? ' · 시뮬과 ' + hit + '/' + nn + ' 맞음' : '');
  }
  function paintLive() {
    var el = $('simALive'); if (!el) return; if (!LIVE || !LIVE.m) { el.innerHTML = ''; return; }
    var age = (Date.now() / 1000 - LIVE.at) / 60, now = new Date(), dk = [3, 0, 0, 0, 0, 1, 2][now.getDay()], hk = dk + '-' + now.getHours(), t9 = now.getHours() * 3600 + now.getMinutes() * 60;
    var sm = null, today = A && [3, 0, 0, 0, 0, 1, 2][window.tgSim.dowOf(dOf()[2])] === dk; if (A && today) A.samp.forEach(function (x) { if (Math.abs(x.t - t9) < 60) sm = x; });
    var hit = 0, nn = 0, cells = Object.keys(M.links).filter(function (k) { var l = M.links[k]; return l.its && !l.sink && LIVE.m[l.its] != null; }).map(function (k) {
      var l = M.links[k], v = LIVE.m[l.its], nv = l.nsp && l.nsp[hk], mk = '';
      if (sm && age <= 20) { var sj = (sm.occ[k] || 0) >= 0.8 * A.L[k].cap, rj = v <= 6; nn++; if (sj === rj) hit++; mk = sj === rj ? ' ✓' : ' ✗'; }
      return '<span style="white-space:nowrap">' + esc((l.nm || k).replace(' — 들어옴', '')) + ' <b style="color:' + (v <= 6 ? '#dc2626' : v <= 12 ? '#ca8a04' : '#16a34a') + '">' + v + '</b>' + (nv != null ? '<small>(평소 ' + nv + ')</small>' : '') + mk + '</span>'; });
    if (!cells.length && !LOOP) { el.innerHTML = ''; return; }
    var at = new Date(LIVE.at * 1000), cmp = !A ? '' : age > 20 ? '' : !today ? '<br><small>오늘 요일을 고르면 시뮬 현행 판과 지금 시각으로 맞대 본다</small>' : sm ? '<br>지금 시각(' + hh(t9) + ') 시뮬 현행 판과 맞대 봄 — <b>' + hit + '/' + nn + '</b> 맞음(막힘 = 실측 6km/h 이하 · 시뮬 80% 넘게 참 · ✓ 맞음 ✗ 틀림)' : '<br><small>시뮬 시계가 지금 시각(' + hh(t9) + ')을 지나면 맞대 본다 — 지금 시각이 든 시간대를 고를 것</small>';
    el.innerHTML = '<div class="sn" style="color:inherit;background:rgba(14,165,233,.08);border-radius:10px;padding:6px 8px">📡 <b>지금 실측</b>(ITS 통행속도 km/h · ' + hh(at.getHours() * 3600 + at.getMinutes() * 60) + (age > 20 ? ' · <b style="color:#dc2626">' + Math.round(age) + '분 지남 — 판정 안 함</b>' : '') + '): ' + cells.join(' · ') + cmp + loopRow(sm, age) + '</div>';
  }
  // ---- 돌리기 ----
  function start() { stop(); A = window.tgSim.create(M, scen(false), alt(0)); B = window.tgSim.create(M, scen(true), alt(1)); A.runTo(A.from - 1); B.runTo(B.from - 1); paintRun(); paintRes(); RUN = 1; LAST = 0; requestAnimationFrame(tick); }
  function stop() { RUN = 0; }
  function tick(ts) {
    if (!RUN || !A) return; if (!LAST) LAST = ts; var dt = Math.min(0.25, (ts - LAST) / 1000); LAST = ts;
    var n = Math.min(1200, Math.round(dt * SPD)); for (var i = 0; i < n && A.t < A.end; i++) { A.step(); B.step(); }
    paintRun(); if (A.t % 600 < n + 1) paintLive(); if (A.t >= A.end) { RUN = 0; paintRes(); paintLive(); return; } requestAnimationFrame(tick);
  }
  function toEnd() { if (!A) start(); stop(); A.runTo(A.end); B.runTo(B.end); paintRun(); paintRes(); paintLive(); }
  function reset() { stop(); A = B = null; $('simARun').innerHTML = '<div class="sn">고른 뒤 ▶ 시연 또는 ⏩ 끝까지</div>'; paintRes(); paintCtl(); }
  function onClick(e) {
    var t = e.target.closest('[data-sa],[data-simx]'); if (!t) return;
    if (t.hasAttribute('data-simx')) return close();
    var k = t.getAttribute('data-sa').split(':');
    if (k[0] === 'lnk') { close(); if (window.tgLink) window.tgLink.open({ id: k[1] }); return; }
    if (k[0] === 'day') { ST.day = k[1]; reset(); } else if (k[0] === 'win') { ST.win = k[1]; ST.edit = {}; reset(); }
    else if (k[0] === 'ph') { var d = ST.edit[ST.sel] || (ST.edit[ST.sel] = []), i = +k[1], P = basePlan(ST.sel); d[i] = Math.max(5 - P.ph[i].d, (d[i] || 0) + (+k[2])); reset(); }
    else if (k[0] === 'reset') { ST.edit = {}; reset(); } else if (k[0] === 'shut') { var e9 = k.slice(1).join(':'); if (ST.shut[e9]) delete ST.shut[e9]; else ST.shut[e9] = 1; reset(); }
    else if (k[0] === 'play') { start(); paintCtl(); } else if (k[0] === 'end') { toEnd(); } else if (k[0] === 'spd') { SPD = SPD >= 2400 ? 300 : SPD * 2; paintCtl(); }
  }
  function onInput(e) { var t = e.target; if (t.getAttribute('data-sa') === 'k') { ST.k = +t.value; var em = t.parentNode.querySelector('em'); if (em) em.textContent = ST.k + '%'; } }
  function onChange(e) { var t = e.target, k = t.getAttribute('data-sa'); if (k === 'k') reset(); else if (k === 'sel') { ST.sel = t.value; paintCtl(); } }
  function open(id) {
    css(); if (window.tgSimUI && window.tgSimUI.close) window.tgSimUI.close();
    need(id, function () {
      if (!ST) ST = defState();
      if (!PANEL) { PANEL = document.createElement('div'); PANEL.id = 'm2dSimA'; document.body.appendChild(PANEL); PANEL.addEventListener('click', onClick); PANEL.addEventListener('input', onInput); PANEL.addEventListener('change', onChange); }
      var nm = Object.keys(M.nodes).filter(function (k) { return M.nodes[k].ty === 'sig' && !/\(연등\)/.test(M.nodes[k].nm || ''); }).map(function (k) { return M.nodes[k].nm; });
      PANEL.innerHTML = '<h3>🧪 시뮬 — ' + esc(AR.nm) + '<button data-simx="1" aria-label="닫기">✕ 닫기</button></h3>' +
        '<div class="sn">신호 교차로 ' + nm.length + '곳(' + esc(nm.join(' · ')) + ')과 그 사이 길 · 자동으로 엮은 구역 · <b>개념 시연 — 예측·보증이 아니다</b></div>' +
        '<div class="warn">평소 속도(ITS 실측 · 평일 16~21시)와 맞대 본 맞음 <b>' + AR.mh + '/' + AR.mn + '</b>칸 · 실제로 막히는 칸 가운데 시뮬도 막힌 것 <b>' + AR.jh + '/' + AR.jn + '</b>' + (AR.jn && AR.jh / AR.jn < 0.5 ? ' — <b>막힘을 잘 못 낸다</b>(실제보다 덜 막히게 나온다)' : '') + ' · 반포 블록(손으로 짠 구역)보다 거칠다 · 신호 없는 교차로는 그냥 지나가고 회전 금지는 아직 안 넣었다 · 구역 밖에서 밀려 들어오는 막힘은 못 낸다(나가는 길은 늘 비어 있다고 봄) · 🏁 현장 결과가 이김(현장에서 본 것과 다르면 시뮬이 틀린 것)</div>' +
        lnkRow() + '<div id="simALive"></div><div id="simARun"></div><div id="simARes"></div><div id="simACtl"></div>' + srcList();
      PANEL.classList.add('on'); if (CH) CH.style.display = 'none'; paintCtl(); start(); liveGet();
    });
  }
  /* 🧩 엮임 보기 — 시뮬 교차로마다 온톨로지 번호(int · INT-<T-GIS 코드>)로 연결 그림을 연다(근거·이유·결과 · 이 교차로에서 시험해 본 대책 SCN) */
  function lnkRow() { if (!window.tgLink) return ''; var L = Object.keys(M.nodes).filter(function (k) { var n = M.nodes[k]; return n.ty === 'sig' && n.int && !/\(연등\)/.test(n.nm || ''); }); if (!L.length) return '';
    return '<div class="row" style="margin:2px 0 4px"><span class="sn" style="margin:0">🧩 엮임 보기</span>' + L.map(function (k) { return '<button data-sa="lnk:' + esc(M.nodes[k].int) + '">' + esc(M.nodes[k].nm) + '</button>'; }).join('') + '</div>'; }
  function close() { stop(); if (PANEL) PANEL.classList.remove('on'); }
  window.tgSimArea = { open: open, close: close, near: nearArea, areas: function () { return IDX; }, state: function () { return ST; }, sims: function () { return [A, B]; } };
  function boot() {
    css(); fetch('data/sim-areas.json?v=1').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { if (!j) return; IDX = j; cardHook(); chip(); }).catch(function () {});
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && PANEL && PANEL.classList.contains('on')) close(); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
