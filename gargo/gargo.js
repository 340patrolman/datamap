/* 가르고 — 서초 출동 길 안내(시험판). 소유자 2026-10-13 「가르고 내비를 본격적으로 · 우선 서초구 한정 · T-Book 홈에서 · 티맵·네이버 내비 같은 양식 + 신호값을 이용한 차원이 다른 안내가 핵심」.
   자료(같은 사이트의 파일만 · 외부 통신 0): gargo/pack-seocho.json(길 계산 묶음 · tools/gargo/pack-bake.py) · ../data/sigdir/index.json + c/<칸>.json(방향별 신호 · 15분마다) · ../data/sig-special.json(특수일).
   지키는 것: 제한속도를 넘는 값은 어디에도 내지 않는다 · 밤 22~06시에는 속도 안내를 하지 않는다 · 신호는 계획값(수동 조작·감응이면 다르다)이라고 밝힌다 · 모르는 신호는 「모름」(0 으로 치지 않는다)
   · 지도는 OpenStreetMap 바탕의 시험용(일방통행·회전 제한이 현장과 다를 수 있다) · 위치·목적지는 이 기기 안에서만 쓰고 저장하지 않는다 · 판단과 주의는 운전자 몫.
   신호 계산식 = gargo/tools/sigwait.py(= datamap sdState·sdLive)와 같다. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var cv = $('gMap'), ctx = cv.getContext('2d'), DPR = Math.min(window.devicePixelRatio || 1, 2);
  var LON0 = 127.01, LAT0 = 37.49, KX = 88800, KY = 111000;   /* 데이터 압축지도(js/map2d.js)와 같은 평면 — 바탕 조각·건물 자료가 그대로 맞는다 */
  function PX(lon) { return (lon - LON0) * KX; } function PY(lat) { return (LAT0 - lat) * KY; }
  function LL(x, y) { return [LON0 + x / KX, LAT0 - y / KY]; }
  var G = null, SIG = { idx: null, its: {}, pl: {}, hol: {}, cell: null, st: {}, typ: 25 };
  var LIVE = { m: null, at: 0 }, MODE = 'n';   /* LIVE = 통행속도 한 장(약 11분마다 · 20분 넘으면 안 쓴다) · MODE n 일반(신호를 지킨다) · e 긴급 출동(길 계산에서 신호 기다림을 뺀다) */
  var view = { cx: 0, cy: 0, s: 0.25, rot: 0 }, me = null, dest = null, route = null, guide = false, follow = true, voiceOn = false, sim = null, lastSay = {};
  var DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw'], DIRKO = { nt: '북', ne: '북동', et: '동', se: '남동', st: '남', sw: '남서', wt: '서', nw: '북서' };

  /* ---------- 자료 ---------- */
  function getJ(u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  function load() {
    msg('길 자료를 읽는 중…');
    return getJ('pack-seocho.json').then(function (j) { if (!j || !j.seg) { msg('길 자료를 읽지 못했다 — 새로 고쳐 본다'); return; } build(j); msg(''); fitAll(); draw(); hashGo(); sigLoad(); xsLoad(); baseLoad(); ['s', 't'].forEach(function (k) { var b = document.querySelector('[data-ov=' + k + ']'); if (b) b.classList.toggle('on', !!OV[k]); }); });
  }
  function build(j) {
    var n = j.nx.length, X = new Float32Array(n), Y = new Float32Array(n), bx = j.base[0], by = j.base[1], i;
    for (i = 0; i < n; i++) { X[i] = PX((bx + j.nx[i]) / 1e6); Y[i] = PY((by + j.ny[i]) / 1e6); }
    var S = j.seg, ns = S.length, SP = new Array(ns), ne = 0;
    for (i = 0; i < ns; i++) { var s = S[i], a = s[0], b = s[1], g = s[8] >= 0 ? j.geo[s[8]] : null, m = g ? g.length / 2 : 0, P = new Float32Array((m + 2) * 2);
      P[0] = X[a]; P[1] = Y[a]; if (g) { var lx = bx + j.nx[a], ly = by + j.ny[a]; for (var k = 0; k < m; k++) { lx += g[k * 2]; ly += g[k * 2 + 1]; P[(k + 1) * 2] = PX(lx / 1e6); P[(k + 1) * 2 + 1] = PY(ly / 1e6); } }
      P[(m + 1) * 2] = X[b]; P[(m + 1) * 2 + 1] = Y[b]; SP[i] = P; ne += (s[7] & 1 ? 1 : 0) + (s[7] & 2 ? 1 : 0); }
    /* 방향 있는 줄(길 계산용) — eS 길 줄 번호 · eR 1 = 역방향 */
    var eA = new Int32Array(ne), eB = new Int32Array(ne), eS = new Int32Array(ne), eR = new Uint8Array(ne), deg = new Int32Array(n + 1), e = 0;
    for (i = 0; i < ns; i++) { var q = S[i]; if (q[7] & 1) { eA[e] = q[0]; eB[e] = q[1]; eS[e] = i; eR[e] = 0; e++; } if (q[7] & 2) { eA[e] = q[1]; eB[e] = q[0]; eS[e] = i; eR[e] = 1; e++; } }
    for (i = 0; i < ne; i++) deg[eA[i] + 1]++;
    for (i = 0; i < n; i++) deg[i + 1] += deg[i];
    var oHead = deg, oList = new Int32Array(ne), fill = new Int32Array(n);
    for (i = 0; i < ne; i++) { oList[oHead[eA[i]] + fill[eA[i]]++] = i; }
    var ban = {}, only = {};
    j.turns.forEach(function (t) { var k = t[0] + '|' + t[1]; (t[3] ? only : ban)[k] = (t[3] ? only : ban)[k] || {}; (t[3] ? only : ban)[k][t[2]] = 1; });
    var n2s = new Int16Array(n).fill(-1); j.sig.forEach(function (sg, si) { sg[6].forEach(function (nd) { n2s[nd] = si; }); });
    /* 그리기용 길(등급마다 한 길) */
    var PATH = {}; for (i = 0; i < ns; i++) { var c = S[i][4], pa = PATH[c] || (PATH[c] = new Path2D()), pp = SP[i]; pa.moveTo(pp[0], pp[1]); for (var u = 2; u < pp.length; u += 2) pa.lineTo(pp[u], pp[u + 1]); }
    /* 이름표 후보 — 큰길(등급 1~5)의 긴 줄 가운데 */
    var LAB = []; for (i = 0; i < ns; i++) { var z = S[i]; if (z[5] < 0 || z[4] > 6 || z[2] < 90) continue; var p2 = SP[i], mi = (p2.length >> 2) * 2, x1 = p2[Math.max(0, mi - 2)], y1 = p2[Math.max(1, mi - 1)], x2 = p2[Math.min(p2.length - 2, mi)], y2 = p2[Math.min(p2.length - 1, mi + 1)]; if (x1 === x2 && y1 === y2) { x1 = p2[0]; y1 = p2[1]; }
      LAB.push({ n: j.names[z[5]], c: z[4], x: (x1 + x2) / 2, y: (y1 + y2) / 2, a: Math.atan2(y2 - y1, x2 - x1), L: z[2] }); }
    LAB.sort(function (a, b) { return a.c - b.c || b.L - a.L; });
    var box = [1e9, -1e9, 1e9, -1e9]; for (i = 0; i < n; i++) { if (X[i] < box[0]) box[0] = X[i]; if (X[i] > box[1]) box[1] = X[i]; if (Y[i] < box[2]) box[2] = Y[i]; if (Y[i] > box[3]) box[3] = Y[i]; }
    G = { j: j, X: X, Y: Y, S: S, SP: SP, eA: eA, eB: eB, eS: eS, eR: eR, oHead: oHead, oList: oList, ban: ban, only: only, n2s: n2s, PATH: PATH, LAB: LAB, box: box, ne: ne, n: n,
      sig: j.sig.map(function (sg) { return { no: sg[0], nm: sg[1], x: PX(sg[2]), y: PY(sg[3]), lon: sg[2], lat: sg[3], r: sg[4], anchor: sg[5] }; }) };
    gridBuild();
  }
  /* 가까운 길 찾기용 칸(200m) */
  var GRID = null, GC = 200;
  function gridBuild() { GRID = {}; for (var i = 0; i < G.S.length; i++) { if (G.S[i][4] > 7) continue; var p = G.SP[i]; for (var u = 0; u < p.length; u += 2) { var k = Math.floor(p[u] / GC) + ',' + Math.floor(p[u + 1] / GC), L = GRID[k] || (GRID[k] = []); if (L[L.length - 1] !== i) L.push(i); } } }
  /* 가까운 길 여럿 — 가장 가까운 것보다 slack m 안으로 더 먼 것까지(길마다 가장 가까운 자리 하나씩 · 많아야 5). 고가 밑의 길·맞은편 차로처럼 나란한 길 가운데서 고르려고 */
  function nearSegs(x, y, maxD, slack) { var gx = Math.floor(x / GC), gy = Math.floor(y / GC), by = {}, list = [], bd = 1e9;
    for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) { var L = GRID[(gx + dx) + ',' + (gy + dy)]; if (!L) continue; for (var q = 0; q < L.length; q++) { var i = L[q]; if (by[i]) continue; var p = G.SP[i], best = null;
      for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], bx = p[u + 2], by2 = p[u + 3], vx = bx - ax, vy = by2 - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2)) : 0, px = ax + vx * t, py = ay + vy * t, d = Math.hypot(px - x, py - y);
        if (!best || d < best.d) best = { seg: i, u: u, t: t, x: px, y: py, d: d, brg: brg(ax, ay, bx, by2) }; }
      by[i] = 1; if (best && best.d <= (maxD || 300)) { list.push(best); if (best.d < bd) bd = best.d; } } }
    return list.filter(function (o) { return o.d <= bd + slack; }).sort(function (a, b) { return a.d - b.d; }).slice(0, 5); }
  function nearSeg(x, y, maxD) { var gx = Math.floor(x / GC), gy = Math.floor(y / GC), best = null, bd = maxD || 300, seen = {};
    for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) { var L = GRID[(gx + dx) + ',' + (gy + dy)]; if (!L) continue; for (var q = 0; q < L.length; q++) { var i = L[q]; if (seen[i]) continue; seen[i] = 1; var p = G.SP[i];
      for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], bx = p[u + 2], by = p[u + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2)) : 0, px = ax + vx * t, py = ay + vy * t, d = Math.hypot(px - x, py - y);
        if (d < bd) { bd = d; best = { seg: i, u: u, t: t, x: px, y: py, d: d, brg: brg(ax, ay, bx, by) }; } } } }
    return best; }
  function brg(x1, y1, x2, y2) { return (Math.atan2(x2 - x1, -(y2 - y1)) * 180 / Math.PI + 360) % 360; }
  function angDiff(a, b) { return ((b - a + 540) % 360) - 180; }   /* +면 오른쪽으로 꺾음 */

  /* ---------- 신호 ---------- */
  /* v0.5.0 통행속도 값이 없는 길 — 종전엔 제한속도로 달린다고 쳐서, 값이 있는(느리게 찍힌) 큰길을 버리고 값 없는 길로 돌았다. 같은 등급 길에서 받은 「통행속도 ÷ 제한속도」의 가운데값을 곱해 어림한다(1 을 넘지 않는다 — 제한속도보다 빠르게 셈하지 않는다) */
  var LIVER = null;
  function liveStat() { LIVER = null; if (!LIVE.m || !G) return; var by = {}, all = [], med = function (v) { v.sort(function (a, b) { return a - b; }); return v[v.length >> 1]; }; G.S.forEach(function (q) { var lim = q[3] || 30; for (var d = 13; d <= 14; d++) { var li = q[d]; if (li == null || li < 0) continue; var v = LIVE.m[G.j.links[li]]; if (!(v > 0)) continue; var r = Math.min(1, v / lim); (by[q[4]] || (by[q[4]] = [])).push(r); all.push(r); } });
    if (all.length < 30) return; LIVER = { all: med(all) }; Object.keys(by).forEach(function (c) { if (by[c].length >= 20) LIVER[c] = med(by[c]); }); }
  function liveLoad() { return getJ('../data/live-spd-seocho.json').then(function (j) { var ok = j && j.m && j.at && Date.now() / 1000 - j.at < 1200; LIVE = ok ? { m: j.m, at: j.at, made: j.made } : { m: null, at: j && j.at || 0 }; liveStat(); }); }
  function sigLoad() { liveLoad().then(function () { if (dest && me && !guide) plan(); else paint(); }); getJ('../data/sig-special.json').then(function (j) { if (j && j.days) SIG.hol = j.days; });
    return getJ('../data/sigdir/index.json').then(function (j) { if (!j || !j.fl) { note('신호 자료를 읽지 못했다 — 길 안내는 제한속도 기준으로만 한다'); return; } SIG.idx = j; SIG.pl = j.pl || {}; SIG.cell = j.cell; var need = {};
      G.sig.forEach(function (s) { if (j.fl[s.no] == null) return; var q = j.pts[s.no]; if (q) need[Math.floor(q[0] / j.cell[0]) + '_' + Math.floor(q[1] / j.cell[1])] = 1; });
      return Promise.all(Object.keys(need).map(function (k) { return getJ('../data/sigdir/c/' + k + '.json').then(function (c) { if (c && c.its) Object.keys(c.its).forEach(function (no) { SIG.its[no] = c.its[no]; }); }); })).then(function () {
        var v = []; Object.keys(SIG.its).forEach(function (no) { SIG.its[no].forEach(function (r) { if (!recOk(r)) return; var C = r.ci || r.cyc; if (!C) return; r.mv.forEach(function (m) { if (m[1] === 'St' && m[2] != null && m[2] < C) v.push((C - m[2]) * (C - m[2]) / (2 * C)); }); }); });
        v.sort(function (a, b) { return a - b; }); if (v.length) SIG.typ = v[v.length >> 1]; SIG.ready = 1; SIG.at = Date.now(); if (dest && me) plan(); draw(); paint(); }); });
  }
  /* v0.5.0 값 없는 신호 — 서울 모든 신호 교차로(T-GIS · data/tgis-seoul.json) 가운데 신호값을 못 받은 곳. 길 마디에 붙여 두고 「신호가 있다」고만 친다(기다림은 받은 값의 가운데값에 견준 어림).
     종전에는 값 있는 189곳만 신호로 쳐서, 그 신호를 피하려고 값 없는 신호가 줄지어 선 길이나 골목으로 돌았다 */
  var XS = [];
  function xsLoad() { return getJ('../data/tgis-seoul.json').then(function (j) { if (!j || !j.items || !G) return; var C = 60, ng = {}, i, k; for (i = 0; i < G.n; i++) { k = Math.floor(G.X[i] / C) + ',' + Math.floor(G.Y[i] / C); (ng[k] || (ng[k] = [])).push(i); }
      /* 마디마다 닿는 길의 가장 큰 길·가장 작은 길 등급 — 자동차전용 본선만 닿는 마디(신호가 없다)와 골목끼리 만나는 마디(큰길 신호를 건너지 않는다)는 신호로 치지 않는다 */
      var cmin = new Uint8Array(G.n).fill(9), cmax = new Uint8Array(G.n); G.S.forEach(function (q) { var c = q[4]; if (c < cmin[q[0]]) cmin[q[0]] = c; if (c < cmin[q[1]]) cmin[q[1]] = c; if (c > cmax[q[0]]) cmax[q[0]] = c; if (c > cmax[q[1]]) cmax[q[1]] = c; });
      function okNode(nd) { return G.n2s[nd] < 0 && cmin[nd] <= 5 && cmax[nd] >= 3; }
      var have = {}; G.sig.forEach(function (g) { have[String(g.no)] = 1; });
      var nxs = new Int32Array(G.n), list = [];
      j.items.forEach(function (it) { if (/\(경보\)/.test(it[1])) return;   /* 경보등(점멸)은 기다리는 신호가 아니라고 보고 뺀다 — 가정 */
        if (it[6] && have[String(it[6])]) return;   /* 값 있는 교차로와 같은 번호(C-ITS) — 이미 센다 */
        var x = PX(it[3]), y = PY(it[2]); if (x < G.box[0] - 60 || x > G.box[1] + 60 || y < G.box[2] - 60 || y > G.box[3] + 60) return; var gx = Math.floor(x / C), gy = Math.floor(y / C), near = [], known = false, bn = -1, bd = 50;
        for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) { var L = ng[(gx + dx) + ',' + (gy + dy)]; if (!L) continue; for (var q = 0; q < L.length; q++) { var nd = L[q], d = Math.hypot(G.X[nd] - x, G.Y[nd] - y); if (d <= 60 && G.n2s[nd] >= 0) known = true; if (!okNode(nd)) continue; if (d <= 32) near.push(nd); if (d < bd) { bd = d; bn = nd; } } }
        if (known) return;   /* 60m 안에 값 있는 신호 마디 — 두 자료의 좌표가 수십 m 어긋나 같은 교차로일 수 있다(두 번 세지 않는다) */
        if (!near.length && bn >= 0) near = [bn]; if (!near.length) return; list.push({ nm: it[1], x: x, y: y }); near.forEach(function (nd) { if (!nxs[nd]) nxs[nd] = list.length; }); });
      XS = list; G.nxs = nxs; G.XS = list; if (dest && me && !guide) plan(); else draw(); }); }
  function recOk(r) { return r && r.mv && r.dq !== 'dir' && !(r.x && !r.v); }
  /* 내가 들어가는 쪽의 기록 고르기 — 같은 방위가 있으면 그것. 없으면 바로 옆 방위(45°) 하나뿐일 때만 그것을 쓴다.
     옆 방위가 양쪽에 다 있으면(비스듬한 길: 남서쪽에서 들어가는데 기록은 남·서 둘) 어느 쪽인지 가릴 수 없으므로 「모름」으로 둔다 — v0.5.0 까지는 먼저 나온 쪽을 골라 다른 방향의 초를 보일 수 있었다 */
  function mvOf(rec, side, mv) { var i = DIRS.indexOf(side), same = null, nb = {}, nbm = null; rec.mv.forEach(function (m) { if (m[1] !== mv || m[2] == null || m[5] == null) return; var k = DIRS.indexOf(m[0]); if (k < 0) return; var d = Math.min((k - i + 8) % 8, (i - k + 8) % 8); if (d === 0) { if (!same) same = m; } else if (d === 1) { if (!nb[m[0]]) { nb[m[0]] = 1; if (!nbm) nbm = m; } } }); return same || (Object.keys(nb).length === 1 ? nbm : null); }
  function sideOf(bearing) { return DIRS[Math.floor((((bearing + 180) % 360) + 22.5) / 45) % 8]; }
  function clOf(d) { var k = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); if (SIG.hol[k]) return 3; var w = d.getDay(); return w >= 1 && w <= 4 ? 0 : w === 5 ? 1 : w === 6 ? 2 : 3; }
  /* T(초) 에 no 교차로로 side 쪽에서 들어와 mv(St·Lt) 하는 신호 — {kind 'pl'|'anchor'|'avg', green, remain(바뀔 때까지 초), wait(기다림 초), C, g} 또는 null(모름) */
  function sigAt(no, T, side, mv) { var recs = (SIG.its[no] || []).filter(recOk); if (!recs.length || (mv !== 'St' && mv !== 'Lt')) return null;
    var d = new Date(T * 1000), sod = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds() + (T % 1), cl = clOf(d), PL = SIG.pl[no] || [], row = null, i, r, m;
    for (i = 0; i < PL.length; i++) if (PL[i][0] === cl && PL[i][1] === d.getHours() && !PL[i][6]) { row = PL[i]; break; }
    function st(a, C, m, kind) { var g = m[2], t = (((T - a - m[5]) % C) + C) % C; return t < g ? { kind: kind, green: true, remain: g - t, wait: 0, C: C, g: g } : { kind: kind, green: false, remain: C - t, wait: C - t, C: C, g: g }; }
    if (row) { var c = row[2], off = row[3], cand = recs.filter(function (q) { return q.cl === cl && Math.abs((q.ci || q.cyc || 0) - c) < 0.6; }); if (!cand.length) cand = recs.filter(function (q) { return Math.abs((q.ci || q.cyc || 0) - c) < 0.6; });
      for (i = 0; i < cand.length; i++) { r = cand[i]; var o = off; if (row[5]) { var rf = row[5].split(':'), ref = null; r.mv.forEach(function (x) { if (!ref && x[0] === rf[0] && x[1] === rf[1] && x[5] != null) ref = x; }); if (!ref) continue; o = off - ref[5]; }
        m = mvOf(r, side, mv); if (m) return st(T - ((((sod - o) % c) + c) % c), c, m, 'pl'); } }
    var A = recs.filter(function (q) { return q.a; }).sort(function (a, b) { return b.a - a.a; });
    for (i = 0; i < A.length; i++) { r = A[i]; var age = T - r.a; if ((age >= 0 && age <= 720) || (r.v && age >= 0 && age <= 7200)) { m = mvOf(r, side, mv); if (m) return st(r.a, r.ci, m, 'anchor'); } }
    for (i = 0; i < recs.length; i++) { r = recs[i]; m = mvOf(r, side, mv); var C = r.ci || r.cyc; if (m && C) { var red = Math.max(0, C - m[2]); return { kind: 'avg', wait: red * red / (2 * C), C: C, g: m[2] }; } }
    return null; }

  /* ---------- 길 계산(시간이 가장 적은 길 · 줄 단위 · 회전 제한 · 유턴 벌점 30초 · 신호 기다림은 닿는 시각으로) ---------- */
  function eLen(e) { return G.S[G.eS[e]][2]; } function eSpd(e) { return G.S[G.eS[e]][3] || 30; } function eWay(e) { return G.S[G.eS[e]][6]; }
  /* 그 줄을 지금 달릴 수 있는 속도 = 제한속도와 실시간 통행속도 가운데 낮은 쪽(실시간 값이 없으면 제한속도 · 제한속도를 넘는 값은 쓰지 않는다) */
  function eLive(e) { if (!LIVE.m) return null; var q = G.S[G.eS[e]], li = q[G.eR[e] ? 14 : 13]; if (li == null || li < 0) return null; var v = LIVE.m[G.j.links[li]]; return v > 0 ? v : null; }
  /* 소통 갈래 0 원활 · 1 서행 · 2 정체 — 앱 기준: 자동차전용·고속(제한 70 이상)은 50·30km/h, 그 밖의 길은 25·15km/h(제한이 낮은 길은 제한의 0.7·0.4배로 낮춘다) */
  function spdLv(v, cls, lim) { if (cls <= 2 && lim >= 70) return v >= 50 ? 0 : v >= 30 ? 1 : 2; return v >= Math.min(25, lim * 0.7) ? 0 : v >= Math.min(15, lim * 0.4) ? 1 : 2; }
  function eV(e) { var lim = eSpd(e), v = eLive(e); if (v) return Math.max(4, Math.min(lim, v)); if (LIVER) { var k = LIVER[G.S[G.eS[e]][4]]; return Math.max(4, lim * (k != null ? k : LIVER.all)); } return lim; }
  /* 길 고르기에만 쓰는 무게(가정 — 시간 표시에는 안 넣는다): 골목(등급 6)은 2배 · 생활도로·진입로(7·8)는 3배 느리게 치고, 신호 없는 곳에서 꺾으면 좌 15초·우 6초를 얹는다.
     넣지 않으면 신호 한두 개를 피하려고 골목을 지그재그로 도는 길이 나온다(시험: 서초역 → 양재역이 열다섯 번 꺾였다) */
  function eCost(e) { var c = G.S[G.eS[e]][4]; return eLen(e) / (eV(e) / 3.6) * (c >= 7 ? 3 : c === 6 ? 2 : 1); }   /* v0.5.0 골목 1.7→2 · 생활도로·진입로 2.2→3(가정) */
  function turnPen(e, f) { if (G.oHead[G.eB[e] + 1] - G.oHead[G.eB[e]] < 2) return 0; var k = turnKind(angDiff(eBrgIn(e), eBrgOut(f))); return k === 'L' ? 15 : k === 'R' ? 6 : k === 'U' ? 30 : 0; }
  function eBrgIn(e) { var p = G.SP[G.eS[e]], n = p.length; return G.eR[e] ? brg(p[2], p[3], p[0], p[1]) : brg(p[n - 4], p[n - 3], p[n - 2], p[n - 1]); }     /* 닿는 쪽 끝의 진행 방위 */
  function eBrgOut(e) { var p = G.SP[G.eS[e]], n = p.length; return G.eR[e] ? brg(p[n - 2], p[n - 1], p[n - 4], p[n - 3]) : brg(p[0], p[1], p[2], p[3]); }   /* 떠나는 쪽 첫머리의 진행 방위 */
  function turnKind(dA) { var a = Math.abs(dA); return a < 28 ? 'S' : a > 150 ? 'U' : dA > 0 ? (a < 60 ? 'r' : 'R') : (a < 60 ? 'l' : 'L'); }
  function heapPush(h, k, v) { h.push([k, v]); var i = h.length - 1; while (i > 0) { var p = (i - 1) >> 1; if (h[p][0] <= h[i][0]) break; var t = h[p]; h[p] = h[i]; h[i] = t; i = p; } }
  function heapPop(h) { var top = h[0], last = h.pop(); if (h.length) { h[0] = last; var i = 0; for (;;) { var l = i * 2 + 1, r = l + 1, m = i; if (l < h.length && h[l][0] < h[m][0]) m = l; if (r < h.length && h[r][0] < h[m][0]) m = r; if (m === i) break; var t = h[m]; h[m] = h[i]; h[i] = t; i = m; } } return top; }
  /* 길을 고를 때 쓰는 기대 기다림 — 닿는 순간의 남은 초가 아니라 「아무 때나 닿았을 때의 평균」 = (주기 − 녹색)² ÷ (2 × 주기). 그 순간 값으로 고르면 신호 하나를 피하려고 골목으로 꺾는 길이 나온다(v0.4 까지) */
  function sigExp(s) { if (!s) return SIG.typ; if (s.kind === 'avg' || !(s.C > 0) || s.g == null) return s.wait != null && s.kind === 'avg' ? s.wait : SIG.typ; var red = Math.max(0, s.C - s.g); return red * red / (2 * s.C); }
  /* 값 없는 신호의 어림(가정) — 받은 신호값의 가운데값 SIG.typ 에 견준다: 큰길(등급 3까지) 그대로 · 중간 길 1.1배 · 골목에서 나올 때 1.5배 · 좌회전은 0.7배를 더 · 우회전 6초 */
  function xsExp(cls, tk) { var b = SIG.typ || 25; if (tk === 'R' || tk === 'r') return 6; if (tk === 'U') return b * 1.5; return (cls <= 3 ? b : cls <= 5 ? b * 1.1 : b * 1.5) + (tk === 'L' || tk === 'l' ? b * 0.7 : 0); }
  /* 꺾는 몫 — 통행속도(구간 평균 · 신호에 서는 시간이 들어 있다)를 쓸 때 신호에서 따로 더하는 값: 직진 0 · 좌회전 0.7×가운데값 · 우회전 6초 · 유턴 1.5×가운데값(가정) */
  function turnAdd(mv) { var b = SIG.typ || 25; return mv === 'Lt' ? b * 0.7 : mv === 'Rt' ? 6 : mv === 'U' ? b * 1.5 : 0; }
  /* 돌려주는 값: w = 화면에 보이는 기다림(값 아는 신호 = 닿을 때의 예상 · 모르는 신호 = 어림) · c = 길을 고를 때 쓰는 값(기대 기다림) */
  function sigCost(ei, ej, T) { var nd = G.eB[ei], si = G.n2s[nd], tk, side;
    if (si < 0) { var xi = G.nxs ? G.nxs[nd] : 0; if (!xi || G.nxs[G.eA[ei]] === xi) return null; if (G.S[G.eS[ei]][4] <= 2 && G.S[G.eS[ej]][4] <= 2) return null; tk = turnKind(angDiff(eBrgIn(ei), eBrgOut(ej))); var ex = xsExp(G.S[G.eS[ei]][4], tk); return { w: ex, c: ex, mv: tk === 'R' || tk === 'r' ? 'Rt' : tk === 'U' ? 'U' : tk === 'L' || tk === 'l' ? 'Lt' : 'St', side: sideOf(eBrgIn(ei)), si: -1, xi: xi, s: null, unk: 1 }; }
    if (G.n2s[G.eA[ei]] === si) return null;   /* 신호 넓이에 막 들어서는 줄만 */
    tk = turnKind(angDiff(eBrgIn(ei), eBrgOut(ej))); side = sideOf(eBrgIn(ei)); if (tk === 'R' || tk === 'r') return { w: 6, c: 6, mv: 'Rt', si: si, side: side }; if (tk === 'U') { var uw = (SIG.typ || 25) * 1.5; return { w: uw, c: uw, mv: 'U', si: si, side: side }; }
    var mv = tk === 'L' || tk === 'l' ? 'Lt' : 'St', s = SIG.ready ? sigAt(G.sig[si].no, T, side, mv) : null; return { w: s ? s.wait : SIG.typ, c: sigExp(s), mv: mv, side: side, si: si, s: s }; }
  function findRoute(sx, sy, tx, ty, T0, sbrg) {
    var a0 = nearSeg(sx, sy, 400), b0 = nearSeg(tx, ty, 600); if (!a0 || !b0) return null;
    var D = new Float64Array(G.ne).fill(Infinity), PR = new Int32Array(G.ne).fill(-1), h = [], i, e, SA = {}, SB = {}, goal = {};
    function edgesOf(seg) { var out = [], k; for (k = G.oHead[G.S[seg][0]]; k < G.oHead[G.S[seg][0] + 1]; k++) if (G.eS[G.oList[k]] === seg) out.push(G.oList[k]); for (k = G.oHead[G.S[seg][1]]; k < G.oHead[G.S[seg][1] + 1]; k++) if (G.eS[G.oList[k]] === seg) out.push(G.oList[k]); return out; }
    /* 후보 = 가장 가까운 길 + 그것과 나란한 길(맞은편 차로 · 고가 밑 길). 같은 마디에 물린 길은 뺀다(그 갈림길의 회전 제한·신호를 건너뛰게 된다) · 자동차전용과 일반 길은 서로 바꾸지 않는다 · 40m 넘게 먼 길은 뺀다 */
    function cands(x, y, maxD, n0) { var s0 = G.S[n0.seg]; var out = nearSegs(x, y, maxD, 24).filter(function (o) { if (o.seg === n0.seg) return true; var q = G.S[o.seg]; if (o.d > Math.max(n0.d, 40)) return false; if (q[0] === s0[0] || q[0] === s0[1] || q[1] === s0[0] || q[1] === s0[1]) return false; if ((q[4] <= 2) !== (s0[4] <= 2)) return false; var dd = Math.abs(angDiff(o.brg, n0.brg)); if (dd > 90) dd = 180 - dd; return dd <= 30; }); return out.length ? out : [n0]; }
    function along(a) { var p = G.SP[a.seg], al = 0, tot = 0, u; for (u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < a.u) al += l; else if (u === a.u) al += l * a.t; tot += l; } return tot ? al / tot : 0; }
    /* 떠나는 자리 — 가장 가까운 길과, 그보다 24m 안으로 더 먼 나란한 길들(고가 밑·맞은편 차로). 더 먼 길은 1m 에 1초씩 불리하게 · 달리는 중이면 진행 방향과 반대인 쪽에 30초 */
    cands(sx, sy, 400, a0).forEach(function (a) { var fr = along(a); edgesOf(a.seg).forEach(function (se) { var frac = G.eR[se] ? fr : 1 - fr, c = eLen(se) * frac / (eV(se) / 3.6) + (a.d - a0.d) * 1; if (sbrg != null) { var eb = G.eR[se] ? (a.brg + 180) % 360 : a.brg; if (Math.abs(angDiff(sbrg, eb)) > 110) c += 30; } if (c < D[se]) { D[se] = c; heapPush(h, c, se); SA[a.seg] = a; } }); });
    /* 닿는 자리 — 같은 방식(더 먼 길은 1m 에 1초씩 불리하게) */
    cands(tx, ty, 600, b0).forEach(function (b) { SB[b.seg] = b; edgesOf(b.seg).forEach(function (ge) { goal[ge] = (b.d - b0.d) * 1; }); });
    var end = -1, bestC = Infinity;
    while (h.length) { var top = heapPop(h), d = top[0]; e = top[1]; if (d > D[e]) continue; if (d >= bestC) break; if (goal[e] != null) { var tc = d + goal[e]; if (tc < bestC) { bestC = tc; end = e; } }
      var nd = G.eB[e], key = nd + '|' + eWay(e), bn = G.ban[key], on = G.only[key];
      for (i = G.oHead[nd]; i < G.oHead[nd + 1]; i++) { var f = G.oList[i], w2 = eWay(f); if ((bn && bn[w2]) || (on && !on[w2])) continue;
        var w = eCost(f); if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) w += 30; var sc = sigCost(e, f, T0 + d); if (sc && MODE !== 'e') w += LIVER ? turnAdd(sc.mv) : sc.c; if (!sc || MODE === 'e') w += turnPen(e, f);
        if (d + w < D[f]) { D[f] = d + w; PR[f] = e; heapPush(h, d + w, f); } } }
    if (end < 0) return null; var es = [end]; while (PR[es[es.length - 1]] >= 0) es.push(PR[es[es.length - 1]]); es.reverse();
    return shape(es, SA[G.eS[es[0]]] || a0, SB[G.eS[end]] || b0, T0); }
  /* 길 꼴 — 선 · 거리 · 꺾는 곳 · 지나는 신호 */
  function shape(es, a, b, T0) {
    var pts = [], cum = [0], mans = [], sigs = [], t = 0, dist = 0, i, k, liveLen = 0, cong = [], free = 0;
    function add(x, y) { if (pts.length) { var d = Math.hypot(x - pts[pts.length - 2], y - pts[pts.length - 1]); if (d < 0.05) return; dist += d; cum.push(dist); } pts.push(x, y); }
    for (i = 0; i < es.length; i++) { var e = es[i], p = G.SP[G.eS[e]], n = p.length / 2, rev = G.eR[e], q = [];
      for (k = 0; k < n; k++) { var u = (rev ? n - 1 - k : k) * 2; q.push(p[u], p[u + 1]); }
      if (i === 0) { var cut = [a.x, a.y], st = false; for (k = 0; k < n - 1; k++) { var u0 = rev ? (n - 2 - k) * 2 : k * 2; if (!st && u0 === a.u) { st = true; cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } else if (st) cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } if (cut.length >= 4) q = cut; }
      if (i === es.length - 1) { var c2 = [], done = false; for (k = 0; k < q.length / 2 && !done; k++) { c2.push(q[k * 2], q[k * 2 + 1]); if (k + 1 < q.length / 2) { var ax = q[k * 2], ay = q[k * 2 + 1], bx = q[k * 2 + 2], by = q[k * 2 + 3], l2 = (bx - ax) * (bx - ax) + (by - ay) * (by - ay), tt = l2 ? ((b.x - ax) * (bx - ax) + (b.y - ay) * (by - ay)) / l2 : 0; if (tt >= 0 && tt <= 1 && Math.hypot(ax + (bx - ax) * tt - b.x, ay + (by - ay) * tt - b.y) < 3) { c2.push(b.x, b.y); done = true; } } } q = c2; }
      var d0 = dist; for (k = 0; k < q.length; k += 2) add(q[k], q[k + 1]);
      var len = dist - d0, spd = eSpd(e), lv = eLive(e); t += len / (eV(e) / 3.6); free += len / (spd / 3.6); if (lv) { liveLen += len; var cl0 = spdLv(lv, G.S[G.eS[e]][4], spd); if (cl0) cong.push([d0, dist, cl0]); }
      if (i + 1 < es.length) { var f = es[i + 1], dA = angDiff(eBrgIn(e), eBrgOut(f)), tk = turnKind(dA), outs = G.oHead[G.eB[e] + 1] - G.oHead[G.eB[e]], nm = G.S[G.eS[f]][5] >= 0 ? G.j.names[G.S[G.eS[f]][5]] : '';
        if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) { tk = 'U'; t += 30; }
        var sc = sigCost(e, f, T0 + t); if (sc) { var sg = sc.si >= 0 ? G.sig[sc.si] : { no: '', nm: XS[sc.xi - 1].nm, x: XS[sc.xi - 1].x, y: XS[sc.xi - 1].y }; sigs.push({ si: sc.si, no: sg.no, nm: sg.nm, x: sg.x, y: sg.y, d: dist, side: sc.side, mv: sc.mv, t: t, w: sc.w, s: sc.s, lim: spd, unk: sc.unk || 0, tw: MODE === 'e' ? 0 : LIVER ? turnAdd(sc.mv) : sc.w }); if (MODE !== 'e') t += LIVER ? turnAdd(sc.mv) : sc.w; }
        var cn = G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '';   /* 같은 이름의 길에서 살짝 휘는 것(갈래 차로·굽은 길)은 안내하지 않는다 */
        if (tk !== 'S' && outs > 1 && !((tk === 'r' || tk === 'l') && nm && nm === cn)) { var last = mans[mans.length - 1]; if (last && dist - last.d < 18 && last.k === tk) { last.nm = nm || last.nm; } else mans.push({ d: dist, k: tk, nm: nm, sig: sc ? (sc.si >= 0 ? G.sig[sc.si].nm : XS[sc.xi - 1].nm) : '', e: e }); } }
    }
    mans.push({ d: dist, k: 'E', nm: dest && dest.nm || '목적지' });
    var lims = []; var dd = 0; es.forEach(function (e, i2) { lims.push([dd, eSpd(e), G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '', G.S[G.eS[e]][9]]); dd += eLen(e); });
    return { es: es, pts: pts, cum: cum, dist: dist, time: t, free: free, mans: mans, sigs: sigs, lims: lims, T0: T0, a: a, b: b, live: dist ? liveLen / dist : 0, cong: cong, mode: MODE, viaLive: !!LIVER };
  }
  function plan() { if (!G || !dest || !me) return; var T0 = Date.now() / 1000, r = findRoute(me.x, me.y, dest.x, dest.y, T0, me.spd > 2 ? me.hd : null);
    if (!r) { route = null; note('길을 찾지 못했다 — 목적지나 내 자리가 길에서 너무 멀다(서초구와 둘레 2km 안에서만 된다)'); paint(); draw(); return; }
    route = r; route.pos = 0; note(''); paint(); if (!guide) fitRoute(); draw(); }

  /* ---------- 내 자리 ---------- */
  var watchId = null;
  function gpsStart() { if (!navigator.geolocation) { note('이 기기는 위치를 알려주지 않는다 — 지도를 길게 눌러 떠나는 곳을 정한다'); return; } if (watchId != null) return;
    watchId = navigator.geolocation.watchPosition(function (pos) { var c = pos.coords; if (sim) return; setMe(PX(c.longitude), PY(c.latitude), c.accuracy || 0, c.heading, c.speed); },
      function (e) { note(e && e.code === 1 ? '위치 권한이 꺼져 있다 — 아이폰: 설정 › 개인정보 보호 및 보안 › 위치 서비스 › Safari 웹사이트 › 「앱을 사용하는 동안」 · 지도를 길게 눌러 떠나는 곳을 정할 수도 있다' : '위치를 잡지 못했다 — 하늘이 보이는 곳에서 잠시 기다린다'); }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 }); }
  function setMe(x, y, acc, hd, spd) { var prev = me, h = hd != null && !isNaN(hd) && (spd == null || spd > 1) ? hd : null; if (h == null && prev) { var mv = Math.hypot(x - prev.x, y - prev.y); h = mv > 4 ? brg(prev.x, prev.y, x, y) : prev.hd; }
    me = { x: x, y: y, acc: acc, hd: h == null ? 0 : h, spd: spd == null || isNaN(spd) ? (prev && prev.t ? Math.hypot(x - prev.x, y - prev.y) / Math.max(0.5, (Date.now() - prev.t) / 1000) : 0) : spd, t: Date.now(), out: !G || x < G.box[0] - 300 || x > G.box[1] + 300 || y < G.box[2] - 300 || y > G.box[3] + 300 };
    if (dest && !route && G) plan(); if (route) track(); if (follow) { view.cx = me.x; view.cy = me.y; if (guide || cruise) view.rot = me.hd; } paint(); draw(); }
  /* 길 위의 내 자리(진행 거리) · 벗어나면 다시 계산 */
  function track() { var r = route, best = 1e9, bd = r.pos || 0, lo = 0, i; for (i = 0; i + 3 < r.pts.length; i += 2) { var k = i / 2; if (r.cum[k + 1] < (r.pos || 0) - 60) continue; if (r.cum[k] > (r.pos || 0) + 400) break; var ax = r.pts[i], ay = r.pts[i + 1], bx = r.pts[i + 2], by = r.pts[i + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((me.x - ax) * vx + (me.y - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - me.x, ay + vy * t - me.y); if (d < best) { best = d; bd = r.cum[k] + Math.sqrt(l2) * t; lo = i; } }
    r.off = best; if (best < 45) { r.pos = bd; r.offN = 0; r.sx = null; var ax2 = r.pts[lo], ay2 = r.pts[lo + 1], bx2 = r.pts[lo + 2], by2 = r.pts[lo + 3], l = Math.hypot(bx2 - ax2, by2 - ay2) || 1, tt = (bd - r.cum[lo / 2]) / l; r.sx = [ax2 + (bx2 - ax2) * tt, ay2 + (by2 - ay2) * tt, brg(ax2, ay2, bx2, by2)]; }
    else { r.offN = (r.offN || 0) + 1; if (guide && r.offN >= 3 && Date.now() - (r.reT || 0) > 6000) { r.reT = Date.now(); say('경로를 벗어났습니다. 다시 찾습니다'); plan(); return; } }
    if (guide && r.dist - r.pos < 25) { say('목적지 부근입니다. 안내를 마칩니다'); guideStop(true); } }


  /* ---------- v0.3.0 지도 채우기 — 데이터 압축지도의 바탕 자료를 읽기만 한다(소유자 「지도를 좀 더 잘 만들어 주고」) ----------
     바탕 조각 ../data/base/index.json + t/<칸>.json(깃허브에서는 /datamap-tiles/t/ · OSM — 녹지·물·물길·철도 · 교차로 이름) · 서초 건물 ../data/maps/seocho-full-buildings.json(이름 있는 건물 974) · 역 출구 ../data/exits-kr.json.
     길 자체는 길 계산 묶음(pack)의 것을 그린다 — 안내하는 길과 보이는 길이 같아야 한다 */
  var BASE = { idx: null, T: {}, ld: {}, q: 0 }, BLD = null, BLDP = null, PL = [], STN = [], OV = { s: 1, t: 1 }, TRAF = null, TRAFAT = 0;
  try { var ov0 = JSON.parse(localStorage.getItem('tg_gargo_ov') || 'null'); if (ov0) { OV.s = ov0.s ? 1 : 0; OV.t = ov0.t ? 1 : 0; } } catch (e) {}
  var ONGH = /github\.io$/.test(location.hostname);
  function baseLoad() { getJ('../data/base/index.json').then(function (j) { if (!j || !j.tiles) return; BASE.idx = j; BASE.set = {}; j.tiles.forEach(function (t) { BASE.set[t[0] + '_' + t[1]] = 1; }); draw(); });
    getJ('../data/exits-kr.json').then(function (j) { if (!j || !j.pts || !G) return; var by = {}; j.pts.forEach(function (q) { var x = PX(q[1]), y = PY(q[0]); if (x < G.box[0] - 500 || x > G.box[1] + 500 || y < G.box[2] - 500 || y > G.box[3] + 500 || !q[3]) return; var o = by[q[3]] || (by[q[3]] = { n: q[3], x: 0, y: 0, c: 0, ex: [] }); o.x += x; o.y += y; o.c++; if (q[2]) o.ex.push([x, y, q[2]]); });
      STN = Object.keys(by).map(function (k) { var o = by[k]; o.x /= o.c; o.y /= o.c; o.n = /역$/.test(o.n) ? o.n : o.n + '역'; return o; }); draw(); }); }
  function tileUrl(k) { return (ONGH ? '/datamap-tiles/t/' : '../data/base/t/') + k + '.json?b=' + encodeURIComponent(String(BASE.idx.bake || '')); }
  function decAdd(pa, a, from) { var x = a[from], z = a[from + 1]; pa.moveTo(x, z); for (var i = from + 2; i < a.length; i += 2) { x += a[i]; z += a[i + 1]; pa.lineTo(x, z); } }
  function tilePrep(B, k) { var K = { g: {}, w: [], ww: new Path2D(), rail: new Path2D(), jn: [] }, GK = { forest: 'wood', wood: 'wood', scrub: 'wood', pitch: 'pitch', cemetery: 'cem' }, NM = B.names || [];
    function chunk(L) { var c = L[L.length - 1]; if (!c || c.n > 1200) { c = { p: new Path2D(), n: 0 }; L.push(c); } return c; }
    (B.green || []).forEach(function (g) { var kd = GK[g[1]] || 'park', L = K.g[kd] || (K.g[kd] = []), c = chunk(L); g[2].forEach(function (r) { decAdd(c.p, r, 0); c.p.closePath(); c.n += r.length >> 1; }); var nm = g[0] >= 0 ? NM[g[0]] : ''; if (nm && /공원|산$|숲/.test(nm) && g[2][0].length > 40) { var r0 = g[2][0], x = r0[0], z = r0[1], sx = x, sz = z, n = 1; for (var i = 2; i < r0.length; i += 2) { x += r0[i]; z += r0[i + 1]; sx += x; sz += z; n++; } K.jn.push({ n: nm, x: sx / n, y: sz / n, k: 'g' }); } });
    (B.water || []).forEach(function (w) { var c = chunk(K.w); w[1].forEach(function (r) { decAdd(c.p, r, 0); c.p.closePath(); c.n += r.length >> 1; }); });
    (B.waterways || []).forEach(function (w) { if (!(w[2] & 2)) decAdd(K.ww, w, 3); });
    (B.rail || []).forEach(function (r) { if (!(r[2] & 2)) decAdd(K.rail, r, 3); });
    (B.junctions || []).forEach(function (j) { K.jn.push({ n: j[0], x: j[1], y: j[2], k: 'j' }); });
    if (B.tile) { var T = B.size; K.box = [B.tile[0] * T, B.tile[1] * T, (B.tile[0] + 1) * T, (B.tile[1] + 1) * T]; } return K; }
  function needTiles() { if (!BASE.idx || view.s < 0.03) return; var T = BASE.idx.size, W = cv.clientWidth, H = cv.clientHeight, c = [S2W(0, 0), S2W(W, 0), S2W(0, H), S2W(W, H)], x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12; c.forEach(function (q) { x0 = Math.min(x0, q[0]); x1 = Math.max(x1, q[0]); y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); });
    var n = 0; for (var ix = Math.floor(x0 / T); ix <= Math.floor(x1 / T); ix++) for (var iz = Math.floor(y0 / T); iz <= Math.floor(y1 / T); iz++) { var k = ix + '_' + iz; if (++n > 12) return; if (!BASE.set[k] || BASE.T[k] || BASE.ld[k] || BASE.q >= 2) continue; BASE.ld[k] = 1; BASE.q++;
      (function (k) { getJ(tileUrl(k)).then(function (j) { BASE.q--; if (j) { BASE.T[k] = tilePrep(j, k); drawSoon(); } }); })(k); } }
  function drawBase(dark, s) { needTiles(); var ks = Object.keys(BASE.T); if (!ks.length) return; var col = dark ? { park: '#173426', wood: '#142f21', pitch: '#1b3a29', cem: '#213228', w: '#17324f' } : { park: '#d3ecc6', wood: '#c1e2b0', pitch: '#c9e8bc', cem: '#dde8d6', w: '#a9d4f5' };
    ['park', 'wood', 'pitch', 'cem'].forEach(function (kd) { ctx.fillStyle = col[kd]; ks.forEach(function (k) { (BASE.T[k].g[kd] || []).forEach(function (c) { ctx.fill(c.p, 'evenodd'); }); }); });
    ctx.fillStyle = col.w; ks.forEach(function (k) { BASE.T[k].w.forEach(function (c) { ctx.fill(c.p, 'evenodd'); }); });
    ctx.strokeStyle = col.w; ctx.lineWidth = Math.max(5, 2 / s); ks.forEach(function (k) { ctx.stroke(BASE.T[k].ww); });
    if (s > 0.08) { ctx.strokeStyle = dark ? '#475569' : '#9aa3af'; ctx.lineWidth = Math.max(3, 1.6 / s); ks.forEach(function (k) { ctx.stroke(BASE.T[k].rail); }); ctx.strokeStyle = dark ? '#111827' : '#eef1f4'; ctx.lineWidth = Math.max(1.4, 0.8 / s); ctx.setLineDash([9, 9]); ks.forEach(function (k) { ctx.stroke(BASE.T[k].rail); }); ctx.setLineDash([]); } }
  function bldLoad() { if (BLDP) return; BLDP = getJ('../data/maps/seocho-full-buildings.json').then(function (j) { if (!j || !j.buildings) return; var dx = -2438 - (LON0 - 127.0077) * KX, dy = -1743 - (37.4917 - LAT0) * KY;
      BLD = j.buildings.filter(function (b) { return b.p && b.p.length > 2; }).map(function (b) { var n = b.p.length, P = new Float32Array(n * 2), x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, sx = 0, sy = 0; for (var i = 0; i < n; i++) { var x = b.p[i][0] + dx, y = b.p[i][1] + dy; P[i * 2] = x; P[i * 2 + 1] = y; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } return { p: P, b: [x0, x1, y0, y1], n: b.n || '', x: sx / n, y: sy / n, a: (x1 - x0) * (y1 - y0) }; }); drawSoon(); }); }
  function drawBld(dark, s) { if (s < 0.4) return; if (!BLD) { bldLoad(); return; } var W = cv.clientWidth, H = cv.clientHeight, c = [S2W(0, 0), S2W(W, 0), S2W(0, H), S2W(W, H)], x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12; c.forEach(function (q) { x0 = Math.min(x0, q[0]); x1 = Math.max(x1, q[0]); y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); });
    ctx.fillStyle = dark ? '#1b2434' : '#e7e2d9'; ctx.strokeStyle = dark ? '#2a3547' : '#d6cfc3'; ctx.lineWidth = 0.6 / s; var n = 0; ctx.beginPath();
    for (var i = 0; i < BLD.length; i++) { var b = BLD[i]; if (b.b[1] < x0 || b.b[0] > x1 || b.b[3] < y0 || b.b[2] > y1) continue; var p = b.p; ctx.moveTo(p[0], p[1]); for (var u = 2; u < p.length; u += 2) ctx.lineTo(p[u], p[u + 1]); ctx.closePath(); if (++n >= 16) { ctx.fill(); if (s > 0.8) ctx.stroke(); ctx.beginPath(); n = 0; } } if (n) { ctx.fill(); if (s > 0.8) ctx.stroke(); } }
  /* 소통 색 — 값이 온 길만 · 갈래는 spdLv(앱 기준). 큰길(갈래 1~5)은 늘, 생활도로는 가까이 볼 때만(멀리서 다 그리면 지도가 온통 빨갛다) */
  function drawTraf(s) { if (!LIVE.m) return; if (!TRAF || TRAFAT !== LIVE.at) { TRAF = [new Path2D(), new Path2D(), new Path2D(), new Path2D(), new Path2D(), new Path2D()]; TRAFAT = LIVE.at; for (var i = 0; i < G.S.length; i++) { var q = G.S[i], lim = q[3] || 30, p = G.SP[i]; for (var d = 0; d < 2; d++) { var li = q[13 + d]; if (li == null || li < 0) continue; var v = LIVE.m[G.j.links[li]]; if (!(v > 0)) continue; var pa = TRAF[spdLv(v, q[4], lim) + (q[4] <= 5 ? 0 : 3)], off = (d ? -1 : 1) * 3.2;
          /* 두 방향을 길 가운데에서 조금씩 벌려 그린다 */ for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], bx = p[u + 2], by = p[u + 3], l = Math.hypot(bx - ax, by - ay) || 1, nx = -(by - ay) / l * off, ny = (bx - ax) / l * off; if (!u) pa.moveTo(ax + nx, ay + ny); pa.lineTo(bx + nx, by + ny); } } } }
    /* 멀리서 보면 큰길의 서행·정체만 가늘게 · 가까이 보면 원활까지 · 더 가까이(0.9 배율부터) 생활도로도 */
    var far = s < 0.3, col = ['#22c55e', '#f59e0b', '#dc2626']; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha = far ? 0.85 : 0.92; ctx.lineWidth = far ? 2.4 / s : Math.max(3.2, 2.6 / s); col.forEach(function (c, i) { if (far && !i) return; ctx.strokeStyle = c; ctx.stroke(TRAF[i]); });
    if (s >= 0.9) { ctx.globalAlpha = 0.8; ctx.lineWidth = Math.max(2.2, 1.8 / s); col.forEach(function (c, i) { ctx.strokeStyle = c; ctx.stroke(TRAF[i + 3]); }); } ctx.globalAlpha = 1; }
  /* 이름 — 교차로·신호 교차로·역·공원·큰 건물 */
  function drawPlaces(dark, s, W, H) { if (s < 0.03) return; var boxes = [], seen = {}, n = 0, far = s < 0.22;
    function put(nm, x, y, font, col, dy, max) { if (n >= max) return; var q = W2S(x, y); if (q[0] < 24 || q[0] > W - 24 || q[1] < 80 || q[1] > H - 110) return; var key = nm.replace(/\s+/g, ''); if (seen[key]) return; ctx.font = font; var tw = ctx.measureText(nm).width, cx = q[0], cy = q[1] + dy; for (var i = 0; i < boxes.length; i++) { var b = boxes[i]; if (Math.abs(b[0] - cx) < (b[2] + tw) / 2 + 5 && Math.abs(b[1] - cy) < 15) return; } boxes.push([cx, cy, tw]); seen[key] = 1; n++;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(17,24,39,.92)' : 'rgba(255,255,255,.95)'; ctx.strokeText(nm, cx, cy); ctx.fillStyle = col; ctx.fillText(nm, cx, cy); return q; }
    STN.forEach(function (o) { var q = put(o.n, o.x, o.y, '800 12.5px system-ui, sans-serif', dark ? '#93c5fd' : '#1d4ed8', -13, far ? 12 : 60); if (q) { ctx.beginPath(); ctx.arc(q[0], q[1], 4.5, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 2.2; ctx.strokeStyle = '#1d4ed8'; ctx.stroke(); } });
    if (s > 1.1) STN.forEach(function (o) { o.ex.forEach(function (e) { var q = W2S(e[0], e[1]); if (q[0] < 0 || q[0] > W || q[1] < 70 || q[1] > H - 100) return; ctx.beginPath(); ctx.arc(q[0], q[1], 7, 0, Math.PI * 2); ctx.fillStyle = '#facc15'; ctx.fill(); ctx.font = '800 9.5px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#111'; ctx.fillText(e[2], q[0], q[1] + 0.5); }); });
    if (s > 0.3) G.sig.forEach(function (g) { put(g.nm, g.x, g.y, '700 11px system-ui, sans-serif', dark ? '#fde68a' : '#7c2d12', -14, 60); });
    if (s <= 0.45) Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { if (j.k === 'g' && /산$|숲$|대공원$|한강공원$/.test(j.n)) put(j.n, j.x, j.y, 'italic 700 11.5px system-ui, sans-serif', dark ? '#86efac' : '#166534', 0, far ? 20 : 66); }); });
    if (s > 0.45) Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { put(j.n, j.x, j.y, j.k === 'g' ? 'italic 700 11.5px system-ui, sans-serif' : '600 10.5px system-ui, sans-serif', j.k === 'g' ? (dark ? '#86efac' : '#166534') : (dark ? '#cbd5e1' : '#475569'), j.k === 'g' ? 0 : -12, 70); }); });
    if (s > 0.75 && BLD) { var c = [S2W(0, 0), S2W(W, H)]; BLD.forEach(function (b) { if (!b.n || b.a < (s > 1.4 ? 300 : 1500)) return; put(b.n, b.x, b.y, '600 10.5px system-ui, sans-serif', dark ? '#d1d5db' : '#57534e', 0, 90); }); } }
  /* 평상시 신호 — 방위마다 직진 신호의 지금 색(아는 곳만). 가운데 점에서 그 차가 들어오는 쪽으로 짧은 막대 · 가까이 보면 남은 초 */
  var SIDEV = { nt: [0, -1], ne: [0.7, -0.7], et: [1, 0], se: [0.7, 0.7], st: [0, 1], sw: [-0.7, 0.7], wt: [-1, 0], nw: [-0.7, -0.7] };
  function sigSides(no) { var out = {}, recs = (SIG.its[no] || []).filter(recOk); recs.forEach(function (r) { r.mv.forEach(function (m) { if ((m[1] === 'St' || m[1] === 'Lt') && m[2] != null && DIRS.indexOf(m[0]) >= 0) (out[m[0]] = out[m[0]] || {})[m[1]] = 1; }); }); return out; }
  function inZone(x, y) { if (!me) return false; var dx = x - me.x, dy = y - me.y, hr = me.hd * Math.PI / 180, f = dx * Math.sin(hr) - dy * Math.cos(hr), d = Math.hypot(dx, dy); return f >= 0 ? d <= 1000 : d <= 500; }
  function drawSigs(dark, s, W, H, onR, now) { if (s <= 0.1) return; var live = OV.s && !guide && SIG.ready && s > 0.28, cr = Math.cos(-view.rot * Math.PI / 180), sr = Math.sin(-view.rot * Math.PI / 180), nd = 0;
    G.sig.forEach(function (sg, si) { if (onR[si]) return; var q = W2S(sg.x, sg.y); if (q[0] < -20 || q[0] > W + 20 || q[1] < -20 || q[1] > H + 20) return;
      if (live && nd < 70 && (!cruise || inZone(sg.x, sg.y))) { var sd = sg._sd || (sg._sd = sigSides(sg.no)), ks = Object.keys(sd), any = false; ks.forEach(function (k) { if (!sd[k].St) return; var st = sigAt(sg.no, now, k, 'St'); if (!st || st.kind === 'avg') return; any = true; var v = SIDEV[k], vx = v[0] * cr - v[1] * sr, vy = v[0] * sr + v[1] * cr, L = s > 0.6 ? 17 : 12;
          ctx.beginPath(); ctx.moveTo(q[0] + vx * 5, q[1] + vy * 5); ctx.lineTo(q[0] + vx * L, q[1] + vy * L); ctx.lineCap = 'round'; ctx.lineWidth = 6.5; ctx.strokeStyle = '#111827'; ctx.stroke(); ctx.lineWidth = 4; ctx.strokeStyle = st.green ? '#22c55e' : '#ef4444'; ctx.stroke();
          if (s > 0.75 || cruise) { ctx.font = '800 10.5px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; var tx = Math.ceil(st.remain) + ''; ctx.lineWidth = 3; ctx.strokeStyle = dark ? '#111827' : '#fff'; ctx.strokeText(tx, q[0] + vx * (L + 10), q[1] + vy * (L + 10)); ctx.fillStyle = st.green ? '#15803d' : '#b91c1c'; ctx.fillText(tx, q[0] + vx * (L + 10), q[1] + vy * (L + 10)); } });
        if (any) nd++; ctx.beginPath(); ctx.arc(q[0], q[1], 4.2, 0, Math.PI * 2); ctx.fillStyle = any ? '#111827' : (dark ? '#64748b' : '#94a3b8'); ctx.fill(); return; }
      ctx.beginPath(); ctx.arc(q[0], q[1], 3.2, 0, Math.PI * 2); ctx.fillStyle = dark ? '#64748b' : '#94a3b8'; ctx.fill(); }); }
  /* 짧게 누름 — 신호 교차로면 방향마다 지금 색을 글로 */
  function tapAt(px, py) { if (!G || guide) return; var el = $('gPick'); if (el.style.display === 'flex') { el.style.display = 'none'; return; } var best = null, bd = 28; G.sig.forEach(function (sg) { var q = W2S(sg.x, sg.y), d = Math.hypot(q[0] - px, q[1] - py); if (d < bd) { bd = d; best = sg; } }); if (!best) return;
    var now = Date.now() / 1000, sd = sigSides(best.no), rows = []; DIRS.forEach(function (k) { if (!sd[k]) return; ['St', 'Lt'].forEach(function (mv) { if (!sd[k][mv]) return; var st = sigAt(best.no, now, k, mv); rows.push('<div class="si"><span>' + DIRKO[k] + '쪽에서 ' + (mv === 'St' ? '직진' : '좌회전') + '</span>' + (!st ? '<em>모름</em>' : st.kind === 'avg' ? '<em>지금 색 모름 · 주기 ' + Math.round(st.C) + '초</em>' : '<b class="' + (st.green ? 'g' : 'r') + '">' + (st.green ? '녹색' : '적색') + ' ' + Math.ceil(st.remain) + '초</b>') + '</div>'); }); });
    var ns = nearSeg(best.x, best.y, 200); el.style.display = 'flex'; el.style.left = Math.max(8, Math.min(cv.clientWidth - 248, px - 120)) + 'px'; el.style.top = Math.max(70, Math.min(cv.clientHeight - 330, py + 14)) + 'px'; el.style.width = '240px';
    el.innerHTML = '<b>🚦 ' + esc(best.nm) + '</b>' + (rows.length ? rows.join('') + '<div class="si"><em>계획값 — 수동 조작·감응이면 다르다</em></div>' : '<div class="si"><em>이 교차로는 신호 자료가 없다</em></div>') + '<button data-p="to">여기로 안내</button><button data-p="x">닫기</button>'; el._w = [ns ? ns.x : best.x, ns ? ns.y : best.y, best.nm]; }
  /* 찾기 — 이 기기 안의 이름(신호 교차로 · 큰길 · 역 · 이름 있는 건물) + 브이월드 장소·주소(이 기기에 브이월드 키가 있을 때만 · 데이터 압축지도의 🔑 와 같은 값) */
  var VWN = 0;
  function vwJ(url) { return new Promise(function (ok, no) { var cb = '__gvw' + (++VWN) + 'x' + Date.now(), sc = document.createElement('script'), t = setTimeout(function () { fin(); no(new Error('응답 없음')); }, 12000); function fin() { clearTimeout(t); window[cb] = function () {}; if (sc.parentNode) sc.parentNode.removeChild(sc); } window[cb] = function (j) { fin(); ok(j); }; sc.onerror = function () { fin(); no(new Error('받기 실패')); }; sc.src = url + '&callback=' + cb; document.head.appendChild(sc); }); }
  function vwKey() { try { return localStorage.getItem('tg_map2d_vwkey') || ''; } catch (e) { return ''; } }
  /* 키 — 이 기기에 넣어 둔 것이 있으면 그것, 없으면 운영 중계(Cloudflare · data/relay.json)의 /vwkey 에서 받아 이 화면이 떠 있는 동안만 쓴다(저장하지 않는다 · 하루 한도는 중계가 센다) */
  var VWK = '', VWKP = null, VWWHY = '';
  function vwKeyGet() { var k = vwKey(); if (k) return Promise.resolve(k); if (VWK) return Promise.resolve(VWK); if (VWKP) return VWKP;
    VWKP = getJ('../data/relay.json').then(function (r) { if (!r || !r.url) throw new Error('중계 주소를 못 읽었다'); return fetch(r.url + '/vwkey', { cache: 'no-store' }); })
      .then(function (res) { return res.json().then(function (j) { if (!res.ok || !j || !j.key) throw new Error(res.status === 429 ? '오늘 찾기 한도를 다 썼다' : (j && j.err) || ('중계 응답 ' + res.status)); VWK = j.key; VWWHY = ''; return VWK; }); })
      .catch(function (e) { VWKP = null; VWWHY = String(e && e.message || e); if (/Failed to fetch|NetworkError|Load failed/i.test(VWWHY)) VWWHY = '주소 검색 중계에 닿지 못했다(통신)'; return ''; });
    return VWKP; }
  function vwSearch(q) { return vwKeyGet().then(function (key) { if (!key) return { list: [], err: VWWHY || '키를 받지 못했다' };
    var b = G.box, bb = [(b[0] - 300) / KX + LON0, LAT0 - (b[3] + 300) / KY, (b[1] + 300) / KX + LON0, LAT0 - (b[2] - 300) / KY].map(function (v) { return v.toFixed(5); }).join(',');
    var base = 'https://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:4326&size=8&page=1&format=json&errorformat=json&key=' + encodeURIComponent(key) + '&domain=340patrolman.github.io&bbox=' + bb + '&query=' + encodeURIComponent(q);
    return Promise.all([vwJ(base + '&type=address&category=road').catch(function () { return null; }), vwJ(base + '&type=address&category=parcel').catch(function () { return null; }), vwJ(base + '&type=place').catch(function () { return null; })]).then(function (R) { var out = [], seen = {}, err = '', miss = 0;
      R.forEach(function (j, i) { var rs = j && j.response; if (!rs) { miss++; return; } if (rs.status === 'ERROR') err = String(rs.error && (rs.error.text || rs.error.code) || '오류'); var it = rs.result && rs.result.items || [];
        it.forEach(function (o) { if (!o.point) return; var x = PX(+o.point.x), y = PY(+o.point.y); if (x < G.box[0] - 300 || x > G.box[1] + 300 || y < G.box[2] - 300 || y > G.box[3] + 300) return; var ad = o.address || {}, nm = String(i === 2 ? (o.title || q) : (i === 0 ? (ad.road || o.title || q) : (ad.parcel || o.title || q))).replace(/^서울특별시\s*/, ''), sub = i === 2 ? String(ad.road || ad.parcel || '').replace(/^서울특별시\s*/, '') : (i === 1 && ad.road ? String(ad.road).replace(/^서울특별시\s*/, '') : '');
          if (seen[nm]) return; seen[nm] = 1; out.push([i === 2 ? '📍' : '🏠', nm, x, y, sub]); }); });
      if (miss === 3) err = '브이월드에 닿지 못했다'; if (!/\d/.test(q)) out.sort(function (a, b) { return (a[0] === '📍' ? 0 : 1) - (b[0] === '📍' ? 0 : 1); });   /* 숫자 없는 말 = 이름 → 장소 먼저 */
      return { list: out, err: out.length ? '' : err }; }); }); }
  /* 통신이 안 될 때의 어림 — 도로명주소의 건물번호는 길 시작점(서쪽·남쪽 끝)에서 10m마다 1씩 는다. 이 묶음 안에서 시작하는 길만 · 건물 앞이 아니라 길 위의 자리다 */
  function roadNear(ids, x, y) { var bx = x, by = y, bd = 1e12; ids.forEach(function (i) { var p = G.SP[i]; for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], dx = p[u + 2] - ax, dy = p[u + 3] - ay, l2 = dx * dx + dy * dy, t = l2 ? Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2)) : 0, qx = ax + dx * t, qy = ay + dy * t, d = (qx - x) * (qx - x) + (qy - y) * (qy - y); if (d < bd) { bd = d; bx = qx; by = qy; } } }); return [bx, by, Math.sqrt(bd)]; }
  function addrGuess(raw) { if (!G) return null; var t = String(raw || '').replace(/\s+/g, ' ').trim().replace(/(대로|로)\s+(\d+[가-힣]?길)/, '$1$2'), m = /(?:^|\s)([가-힣0-9·]+(?:로|길))\s*(\d+)(?:-\d+)?\s*(?:번지|번)?$/.exec(t); if (!m) return null;
    var road = m[1], num = +m[2], ni = G.j.names.indexOf(road); if (ni < 0 || !(num > 0)) return null; var ids = []; for (var i = 0; i < G.S.length; i++) if (G.S[i][5] === ni) ids.push(i); if (!ids.length) return null;
    var x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, W = null, E = null, S = null, N = null; ids.forEach(function (i) { var p = G.SP[i]; for (var u = 0; u < p.length; u += 2) { var x = p[u], y = p[u + 1]; if (x < x0) { x0 = x; W = [x, y]; } if (x > x1) { x1 = x; E = [x, y]; } if (y > y1) { y1 = y; S = [x, y]; } if (y < y0) { y0 = y; N = [x, y]; } } });
    var ew = (x1 - x0) >= (y1 - y0), a = ew ? W : S, b = ew ? E : N, par = road.replace(/\d+[가-힣]?길$/, '');
    if (par !== road) { var pi = G.j.names.indexOf(par); if (pi >= 0) { var pids = []; for (i = 0; i < G.S.length; i++) if (G.S[i][5] === pi) pids.push(i); if (pids.length) { var da = roadNear(pids, a[0], a[1])[2], db = roadNear(pids, b[0], b[1])[2]; if (db < da) { var sw = a; a = b; b = sw; } } } }
    else if (a[0] < G.box[0] + 400 || a[0] > G.box[1] - 400 || a[1] < G.box[2] + 400 || a[1] > G.box[3] - 400) return null;   /* 길이 이 묶음 밖에서 시작한다 — 셈할 수 없다 */
    var L = Math.hypot(b[0] - a[0], b[1] - a[1]), d = num * 10; if (L < 30 || d > L + 60) return null; var q = roadNear(ids, a[0] + (b[0] - a[0]) / L * d, a[1] + (b[1] - a[1]) / L * d);
    return ['📐', road + ' ' + num + ' 쯤', q[0], q[1], '어림 자리 — 도로명 번호로 셈(시작점에서 ' + km(d) + ') · 길 위의 자리라 건물에서 100m 넘게 어긋날 수 있다']; }
  function localFind(q) { var out = [], seen = {}; function add(ic, nm, x, y) { if (out.length > 40 || seen[ic + nm]) return; seen[ic + nm] = 1; out.push([ic, nm, x, y, '']); } var has = function (t) { return String(t).replace(/\s+/g, '').indexOf(q) >= 0; };
    STN.forEach(function (o) { if (has(o.n)) add('🚇', o.n, o.x, o.y); }); G.sig.forEach(function (g) { if (has(g.nm)) add('🚦', g.nm, g.x, g.y); }); if (BLD) BLD.forEach(function (b) { if (b.n && has(b.n)) add('🏢', b.n, b.x, b.y); });
    Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { if (has(j.n)) add(j.k === 'g' ? '🌳' : '✚', j.n, j.x, j.y); }); }); G.LAB.forEach(function (L) { if (has(L.n)) add('🛣', L.n, L.x, L.y); }); return out; }
  var FSEQ = 0;
  var FNT = 0;
  function findRun(raw, auto) { var q = String(raw || '').replace(/\s+/g, ''); clearTimeout(FNT); if (!G || q.length < 2) { fl.style.display = 'none'; return; } if (!BLD) bldLoad(); var seq = ++FSEQ, out = localFind(q), gs = addrGuess(raw), txt = String(raw).replace(/\s+/g, ' ').trim(), net = txt.length >= 2 && navigator.onLine !== false, st = net ? '🔎 주소·장소를 찾는 중…' : (navigator.onLine === false ? '통신이 끊겨 있다 — 이 기기 안의 이름만 찾는다' : ''), wait = net;
    function show(extra, exact) { if (seq !== FSEQ) return; var all = out.concat(extra || []); if (gs && !exact) all.push(gs); fl._o = all;
      fl.innerHTML = all.slice(0, 16).map(function (o, i) { return '<button data-i="' + i + '">' + o[0] + ' ' + esc(o[1]) + (o[4] ? ' <small>' + esc(o[4]) + '</small>' : '') + '</button>'; }).join('') + (all.length || wait ? '' : '<div class="no">찾지 못했다 — 「반포대로 179」「서초동 1726-1」처럼 주소를 적거나, 지도를 길게 눌러 목적지를 정한다</div>') + (st ? '<div class="no">' + esc(st) + '</div>' : '');
      fl.style.display = 'block'; if (auto && !wait && all.length === 1) pickFound(0); }
    show(null, false); if (!net) return;
    FNT = setTimeout(function () { if (seq !== FSEQ) return; vwSearch(txt).then(function (r) { if (seq !== FSEQ) return; wait = false; var ex = r && r.list || [], hit = ex.some(function (o) { return o[0] === '🏠'; });
      st = ex.length ? '' : (r && r.err ? '주소 검색에 닿지 못했다 — ' + r.err + (gs ? ' · 아래는 도로명 번호로 셈한 어림 자리' : '') : '');
      /* 엔터·음성: 적은 글과 딱 맞는 것이 하나뿐이면 그것으로(「사임당로 143」 ↔ 「사임당로17길 143」을 가른다 · 장소는 이름이 같을 때) */
      var pickI = -1; if (auto) { var n0 = out.length, hits = []; ex.forEach(function (o, i) { var nm = ' ' + o[1].replace(/\(.*?\)/g, ' ') + ' '; if (o[0] === '🏠' ? nm.indexOf(' ' + txt + ' ') >= 0 : o[1].replace(/\s+/g, '') === q) hits.push(n0 + i); }); if (hits.length === 1 && !out.some(function (o) { return o[1].replace(/\s+/g, '') === q; })) pickI = hits[0]; }
      show(ex, hit); if (pickI >= 0 && fl.style.display !== 'none') pickFound(pickI); }); }, auto ? 0 : 700); }
  function pickFound(i) { var o = fl._o && fl._o[i]; if (!o) return; fl.style.display = 'none'; if (o[0] === '📐') note(o[4]); fi.value = o[1]; fi.blur(); var ns = nearSeg(o[2], o[3], 400); setDest(ns ? ns.x : o[2], ns ? ns.y : o[3], o[1]); if (!route) { view.cx = o[2]; view.cy = o[3]; if (view.s < 0.5) view.s = 0.7; follow = false; } draw(); }
  /* 음성으로 목적지 — 브라우저의 받아쓰기(webkitSpeechRecognition · 크롬·사파리는 소리를 그 회사 서버로 보낸다 · 티북의 음성 입력과 같은 길) */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition, rec = null;
  function micGo() { var b = $('gMic'); if (!SR) { note('이 브라우저는 음성 받아쓰기를 지원하지 않는다 — 자판의 마이크 단추로 말한다'); fi.focus(); return; } if (rec) { try { rec.stop(); } catch (e) {} return; }
    try { rec = new SR(); rec.lang = 'ko-KR'; rec.interimResults = true; rec.maxAlternatives = 1; } catch (e) { rec = null; note('음성 받아쓰기를 켜지 못했다'); return; }
    rec.onresult = function (e) { var t = '', fin = false; for (var i = 0; i < e.results.length; i++) { t += e.results[i][0].transcript; if (e.results[i].isFinal) fin = true; } fi.value = t; if (fin) findRun(t, true); };
    rec.onerror = function (e) { note(e && e.error === 'not-allowed' ? '마이크 권한이 꺼져 있다 — 브라우저 설정에서 이 사이트의 마이크를 허용한다' : '잘 듣지 못했다 — 다시 누르고 말한다'); };
    rec.onend = function () { rec = null; b.classList.remove('on'); }; b.classList.add('on'); note('말하십시오 — 예: 「서초구청」 「교대역」 「반포대로 201」'); try { rec.start(); } catch (e) { rec = null; b.classList.remove('on'); } }

  /* ---------- 그리기 ---------- */
  /* 등급: [폭 m, 낮 채움, 낮 테, 밤 채움] — 큰길은 따뜻한 노랑 · 그 밖은 흰 길에 옅은 테(땅 색과 건물 색을 가라앉혀 길과 안내선이 먼저 보이게) */
  var RS = { 1: [16, '#f7c16a', '#dc9a36', '#8a6420'], 2: [14, '#fbd583', '#e2b452', '#7c6126'], 3: [12, '#fde8ad', '#e4cc8a', '#6b5a30'], 4: [9.5, '#ffffff', '#d3d8df', '#3b4658'], 5: [8, '#ffffff', '#dbe0e6', '#364154'], 6: [6, '#ffffff', '#e1e5ea', '#323c4e'], 7: [4.2, '#fbfcfd', '#e5e8ec', '#2e3748'], 8: [3, '#f6f7f9', '#e8ebee', '#2b3444'] };
  function resize() { var w = cv.clientWidth, h = cv.clientHeight; if (!w || !h) return; if (cv.width !== Math.round(w * DPR) || cv.height !== Math.round(h * DPR)) { cv.width = Math.round(w * DPR); cv.height = Math.round(h * DPR); } }
  function anchorY() { return guide || cruise ? cv.clientHeight * 0.68 : cv.clientHeight * 0.5; }
  function W2S(x, y) { var c = Math.cos(-view.rot * Math.PI / 180), s = Math.sin(-view.rot * Math.PI / 180), dx = (x - view.cx) * view.s, dy = (y - view.cy) * view.s; return [cv.clientWidth / 2 + dx * c - dy * s, anchorY() + dx * s + dy * c]; }
  function S2W(px, py) { var c = Math.cos(view.rot * Math.PI / 180), s = Math.sin(view.rot * Math.PI / 180), dx = (px - cv.clientWidth / 2) / view.s, dy = (py - anchorY()) / view.s; return [view.cx + dx * c - dy * s, view.cy + dx * s + dy * c]; }
  var DQ = 0; function drawSoon() { if (DQ) return; DQ = 1; var f = function () { if (!DQ) return; DQ = 0; draw(); }; requestAnimationFrame(f); setTimeout(f, 150); }
  function draw() { resize(); var W = cv.clientWidth, H = cv.clientHeight; if (!W) return; var dark = document.documentElement.classList.contains('dark');
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = dark ? '#0f1726' : '#f2f0ea'; ctx.fillRect(0, 0, W, H); if (!G) return;
    ctx.save(); ctx.translate(W / 2, anchorY()); ctx.rotate(-view.rot * Math.PI / 180); ctx.scale(view.s, view.s); ctx.translate(-view.cx, -view.cy); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    var s = view.s, show = function (c) { return c <= 3 || (c <= 5 && s > 0.05) || (c === 6 && s > 0.12) || (c === 7 && s > 0.2) || (c === 8 && s > 0.35); }, c;
    drawBase(dark, s);
    for (c = 8; c >= 1; c--) { if (!G.PATH[c] || !show(c)) continue; ctx.lineWidth = Math.max(RS[c][0], (c <= 3 ? 2.6 : 1.4) / s) + 2 / s; ctx.strokeStyle = dark ? '#0a101c' : RS[c][2]; ctx.stroke(G.PATH[c]); }
    for (c = 8; c >= 1; c--) { if (!G.PATH[c] || !show(c)) continue; ctx.lineWidth = Math.max(RS[c][0], (c <= 3 ? 2.6 : 1.4) / s); ctx.strokeStyle = dark ? RS[c][3] : RS[c][1]; ctx.stroke(G.PATH[c]); }
    drawBld(dark, s); if (!guide && OV.t) drawTraf(s);
    if (route) { var p = route.pts, i; ctx.beginPath(); ctx.moveTo(p[0], p[1]); for (i = 2; i < p.length; i += 2) ctx.lineTo(p[i], p[i + 1]); ctx.lineWidth = Math.max(13, 11 / s); ctx.strokeStyle = dark ? '#0b1220' : '#ffffff'; ctx.stroke(); ctx.lineWidth = Math.max(10.5, 8.6 / s); ctx.strokeStyle = '#1b54d6'; ctx.stroke(); ctx.lineWidth = Math.max(7.5, 6 / s); ctx.strokeStyle = '#3d86ff'; ctx.stroke();
      route.cong.forEach(function (cg) { ctx.beginPath(); var on = false; for (var u = 0; u < p.length; u += 2) { var dd = route.cum[u / 2]; if (dd >= cg[0] - 0.5 && dd <= cg[1] + 0.5) { if (!on) { ctx.moveTo(p[u], p[u + 1]); on = true; } else ctx.lineTo(p[u], p[u + 1]); } } ctx.lineWidth = Math.max(7.5, 6 / s); ctx.strokeStyle = cg[2] === 2 ? '#dc2626' : '#f59e0b'; ctx.stroke(); }); }
    ctx.restore();
    /* 이름표 */
    if (s > 0.06) { var boxes = [], n = 0, seen = {}; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '700 12px system-ui, sans-serif';
      for (var li = 0; li < G.LAB.length && n < 26; li++) { var L = G.LAB[li]; if ((L.c >= 5 && s < 0.3) || (L.c === 4 && s < 0.15)) continue; var q = W2S(L.x, L.y); if (q[0] < 30 || q[0] > W - 30 || q[1] < 90 || q[1] > H - 120) continue; var sl = seen[L.n]; if (sl && sl.some(function (o) { return Math.hypot(o[0] - q[0], o[1] - q[1]) < 240; })) continue;
        var tw = ctx.measureText(L.n).width; if (tw + 16 > L.L * s) continue; var hit = false; for (var bi = 0; bi < boxes.length; bi++) { var b = boxes[bi]; if (Math.abs(b[0] - q[0]) < (b[2] + tw) / 2 + 6 && Math.abs(b[1] - q[1]) < 18) { hit = true; break; } } if (hit) continue; boxes.push([q[0], q[1], tw]); (seen[L.n] = seen[L.n] || []).push(q); n++;
        var a = L.a - view.rot * Math.PI / 180; a = Math.atan2(Math.sin(a), Math.cos(a)); if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI; ctx.save(); ctx.translate(q[0], q[1]); ctx.rotate(a); ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(17,24,39,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(L.n, 0, 0); ctx.fillStyle = dark ? '#cbd5e1' : '#374151'; ctx.fillText(L.n, 0, 0); ctx.restore(); } }
    drawPlaces(dark, s, W, H);
    /* 신호 — 길 위의 신호는 지금 색(아는 곳만) · 그 밖은 평상시 화면에서 방위마다 색(drawSigs) */
    var now = Date.now() / 1000, onR = {}; if (route) route.sigs.forEach(function (g) { if (g.si >= 0) onR[g.si] = g; });
    drawSigs(dark, s, W, H, onR, now); if (cruise && !route) drawAhead(dark, now);
    if (route) route.sigs.forEach(function (g) { var sg = g.si >= 0 ? G.sig[g.si] : g, q = W2S(sg.x, sg.y); if (q[0] < -20 || q[0] > W + 20 || q[1] < -20 || q[1] > H + 20) return; var st = g.mv === 'St' || g.mv === 'Lt' ? sigAt(g.no, now, g.side, g.mv) : null, col = !st || st.kind === 'avg' ? '#94a3b8' : st.green ? '#16a34a' : '#dc2626';
      ctx.beginPath(); ctx.arc(q[0], q[1], 9, 0, Math.PI * 2); ctx.fillStyle = '#111827'; ctx.fill(); ctx.beginPath(); ctx.arc(q[0], q[1], 6.5, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill();
      if (st && st.kind !== 'avg' && s > 0.25) { var tx = Math.ceil(st.remain) + ''; ctx.font = '800 11px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = '#fff'; ctx.strokeText(tx, q[0], q[1] - 17); ctx.fillStyle = col; ctx.fillText(tx, q[0], q[1] - 17); } });
    if (dest) { var dq = W2S(dest.x, dest.y); ctx.beginPath(); ctx.moveTo(dq[0], dq[1]); ctx.lineTo(dq[0] - 9, dq[1] - 22); ctx.arc(dq[0], dq[1] - 26, 10, Math.PI * 0.85, Math.PI * 0.15); ctx.closePath(); ctx.fillStyle = '#e11d48'; ctx.fill(); ctx.beginPath(); ctx.arc(dq[0], dq[1] - 26, 4, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); }
    if (me) { var mp = route && route.sx && route.off < 45 ? route.sx : [me.x, me.y, me.hd], mq = W2S(mp[0], mp[1]); if (me.acc > 30) { ctx.beginPath(); ctx.arc(mq[0], mq[1], Math.max(14, me.acc * s), 0, Math.PI * 2); ctx.fillStyle = 'rgba(37,99,235,.12)'; ctx.fill(); }
      ctx.save(); ctx.translate(mq[0], mq[1]); ctx.beginPath(); ctx.arc(0, 2, 19, 0, Math.PI * 2); ctx.fillStyle = 'rgba(15,23,42,.18)'; ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, 18, 0, Math.PI * 2); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(15,23,42,.12)'; ctx.stroke();
      ctx.rotate(((guide ? mp[2] : me.hd) - view.rot) * Math.PI / 180); ctx.beginPath(); ctx.moveTo(0, -12.5); ctx.lineTo(9.5, 9); ctx.lineTo(0, 4.2); ctx.lineTo(-9.5, 9); ctx.closePath(); ctx.fillStyle = '#1b54d6'; ctx.fill(); ctx.restore(); }
  }
  function fitAll() { var b = G.box; view.cx = (b[0] + b[1]) / 2; view.cy = (b[2] + b[3]) / 2; view.s = Math.min(cv.clientWidth / (b[1] - b[0]), cv.clientHeight / (b[3] - b[2])) * 1.9; view.rot = 0; }
  /* 화면에서 지도가 실제로 보이는 자리 — 위 찾기 칸·켜는 단추 줄, 아래 판, 오른쪽 단추 줄을 뺀다 */
  function fitBox() { var W = cv.clientWidth, H = cv.clientHeight, bot = $('gBot'), bh = bot && bot.offsetHeight ? Math.min(H * 0.62, bot.offsetHeight) : 0, top = 112; return [22, top, Math.max(120, W - 22 - 58), Math.max(top + 120, H - bh - 18)]; }
  function fitRoute() { var p = route.pts, b = [1e9, -1e9, 1e9, -1e9]; for (var i = 0; i < p.length; i += 2) { if (p[i] < b[0]) b[0] = p[i]; if (p[i] > b[1]) b[1] = p[i]; if (p[i + 1] < b[2]) b[2] = p[i + 1]; if (p[i + 1] > b[3]) b[3] = p[i + 1]; }
    var f = fitBox(), fw = f[2] - f[0], fh = f[3] - f[1]; view.rot = 0; view.s = Math.min(3, Math.min(fw / ((b[1] - b[0]) + 60), fh / ((b[3] - b[2]) + 60)));
    /* 길 묶음의 가운데가 보이는 자리의 가운데에 오게 */ view.cx = (b[0] + b[1]) / 2 - ((f[0] + f[2]) / 2 - cv.clientWidth / 2) / view.s; view.cy = (b[2] + b[3]) / 2 - ((f[1] + f[3]) / 2 - cv.clientHeight * 0.5) / view.s; follow = false; }

  /* ---------- 화면 글 ---------- */
  function msg(t) { var el = $('gMsg'); el.textContent = t; el.style.display = t ? 'block' : 'none'; }
  var noteT = 0; function note(t) { var el = $('gNote'); el.textContent = t; el.style.display = t ? 'block' : 'none'; clearTimeout(noteT); if (t) noteT = setTimeout(function () { el.style.display = 'none'; }, 7000); }
  function km(m) { return m >= 1000 ? (m / 1000).toFixed(m >= 10000 ? 0 : 1) + 'km' : Math.max(10, Math.round(m / 10) * 10) + 'm'; }
  function mmss(s) { s = Math.max(0, Math.round(s)); var m = Math.floor(s / 60); return m >= 60 ? Math.floor(m / 60) + '시간 ' + (m % 60) + '분' : m ? m + '분' : s + '초'; }
  function hm(T) { var d = new Date(T * 1000); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  var ARW = { L: '⬅', l: '↖', R: '➡', r: '↗', U: '↩', E: '🏁', S: '⬆' }, MKO = { L: '좌회전', l: '왼쪽 방향', R: '우회전', r: '오른쪽 방향', U: '유턴', E: '목적지', S: '직진' };
  /* 차로 안내 — OSM 에 차로별 진행 방향이 적힌 곳(서초 둘레 141줄뿐)은 차로 번호로, 그 밖은 꺾는 쪽 규칙(좌회전·유턴 = 1차로 · 우회전 = 맨 오른쪽)으로. 차로마다의 속도 자료는 어디에도 없다 — 「어느 차로가 빠르다」는 말은 하지 않는다 */
  function laneHint(m) { if (!m || m.e == null || m.k === 'E' || m.k === 'S') return ''; var q = G.S[G.eS[m.e]], ti = q[G.eR[m.e] ? 16 : 15], want = m.k === 'U' ? 'reverse' : m.k === 'L' || m.k === 'l' ? 'left' : 'right', nL = q[10];
    if (ti != null && ti >= 0) { var L = String(G.j.tl[ti]).split('|'), ok = []; L.forEach(function (x, i) { if (x.split(';').some(function (y) { return y.indexOf(want) >= 0; })) ok.push(i + 1); }); if (ok.length) return L.length + '개 차로 가운데 <b>' + ok.join('·') + '차로</b>'; }
    return (m.k === 'L' || m.k === 'l' || m.k === 'U' ? '<b>1차로</b>(맨 왼쪽)' : '<b>맨 오른쪽 차로</b>') + (nL ? ' <em>· 이 길 ' + nL + '차로</em>' : ''); }
  function night() { var h = new Date().getHours(); return h >= 22 || h < 6; }
  function paint() {
    var top = $('gTop'), bot = $('gBot'), sg = $('gSig'), spd = $('gSpd');
    if (!route && cruise) { paintCruise(); return; }
    if (!route) { top.style.display = 'none'; sg.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = guide ? 'none' : 'flex';
      bot.innerHTML = '<div class="hint">' + (dest ? (me ? '길을 찾는 중…' : '내 자리를 기다리는 중 — 위치를 허락하거나, 지도를 <b>길게 눌러</b> 「여기서 떠나기」를 고른다') : '목적지를 정한다 — 지도를 <b>길게 누르거나</b> 위에서 이름을 찾는다') + '</div>' + (dest ? '' : '<div class="btns" style="margin-top:10px"><button id="gCruise" class="go">▶ 켜놓고 다니기 — 앞 신호·소통</button></div>') + (me && me.out ? '<div class="hint warn">지금 자리가 서초구 둘레 밖이다 — 시험판은 서초구와 둘레 2km 안에서만 길을 찾는다.</div>' : ''); return; }
    var r = route, now = Date.now() / 1000, pos = r.pos || 0, left = Math.max(0, r.dist - pos), frac = r.dist ? left / r.dist : 0, tLeft = r.time * frac;
    var nx = null, n2 = null; for (var i = 0; i < r.mans.length; i++) if (r.mans[i].d > pos + 5) { nx = r.mans[i]; n2 = r.mans[i + 1] || null; break; }
    var known = r.sigs.filter(function (g) { return g.s && g.s.kind !== 'avg'; }).length, wsum = 0; r.sigs.forEach(function (g) { wsum += g.tw || 0; });
    if (guide) { $('gFind').style.display = 'none'; top.style.display = 'flex';
      top.innerHTML = nx ? '<div class="arw">' + ARW[nx.k] + '</div><div class="tx"><b>' + km(nx.d - pos) + '</b><span>' + (nx.k === 'E' ? '목적지' : MKO[nx.k]) + (nx.nm ? ' · ' + esc(nx.nm) : '') + (nx.sig ? ' <em>(' + esc(nx.sig) + ')</em>' : '') + '</span>' + (function () { var lh = nx.d - pos < 700 ? laneHint(nx) : ''; return lh ? '<small class="ln2">차로 — ' + lh + '</small>' : ''; })() + (n2 ? '<small>그다음 ' + ARW[n2.k] + ' ' + km(n2.d - nx.d) + ' 뒤 ' + MKO[n2.k] + '</small>' : '') + '</div>' : '';
      bot.innerHTML = '<div class="eta"><div><b>' + hm(now + tLeft) + '</b><span>도착</span></div><div><b>' + mmss(tLeft) + '</b><span>남은 시간</span></div><div><b>' + km(left) + '</b><span>남은 거리</span></div><button id="gStop" class="stop">안내 끝</button></div>';
      var lim = 0, rn = ''; for (var k = 0; k < r.lims.length; k++) if (r.lims[k][0] <= pos + 1) { lim = r.lims[k][1]; rn = r.lims[k][2]; } spd.style.display = 'flex'; var v = Math.round((me && me.spd || 0) * 3.6);
      spd.innerHTML = '<div class="lim">' + lim + '</div><div class="cur' + (v > lim + 2 ? ' over' : '') + '"><b>' + v + '</b><span>km/h</span></div>' + (rn ? '<div class="rn">' + esc(rn) + '</div>' : '');
    } else { top.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = 'flex';
      bot.innerHTML = '<div class="sum"><div class="big"><b>' + mmss(r.time) + '</b> <span>' + km(r.dist) + ' · ' + hm(now + r.time) + ' 도착</span></div>'
        + '<div class="mode"><button data-mode="n" class="' + (MODE === 'n' ? 'on' : '') + '">일반 — 신호를 지킨다</button><button data-mode="e" class="' + (MODE === 'e' ? 'on' : '') + '">🚨 긴급 출동</button></div>'
        + '<div class="sub">신호 ' + r.sigs.length + '곳 · 지금 색을 아는 곳 ' + known + ' · 나머지 ' + (r.sigs.length - known) + '곳은 어림' + (MODE === 'e' ? ' · <b>신호 기다림을 셈에서 뺐다</b>(닿을 때 적색이면 알려 준다 — 통과는 운전자 판단)' : (LIVER ? ' · 신호에 서는 시간은 통행속도에 들어 있다(꺾는 데 ' + mmss(wsum) + ' 더함)' : ' · 신호 기다림 ' + mmss(wsum) + ' 포함')) + '<br>'
          + (LIVE.m ? '🚗 통행속도 반영(' + esc(LIVE.made || '') + ' 받음 · 길의 ' + Math.round(r.live * 100) + '%에 값' + (r.cong.length ? ' · <b class="r" title="큰길 25·15km/h · 자동차전용 50·30km/h 아래(앱 기준)">막히는 구간 ' + r.cong.length + '곳</b>' : ' · 막히는 구간 없음') + ')' : '🚗 통행속도 없음(받은 지 20분 넘음) — 제한속도로 셈') + ' · 신호·막힘이 없다면 ' + mmss(r.free) + '<br>🚦 신호값 ' + (SIG.idx ? esc(String(SIG.idx.made || '')) + ' 구움 · 5분마다 새 값을 확인한다' : '없음') + '</div>'
        + '<div class="btns"><button id="gGo" class="go">▶ 안내 시작</button><button id="gSim">모의 주행</button><button id="gClr">지우기</button></div>'
        + '<div class="hand"><span>이 목적지를 다른 앱으로</span><button data-hand="map">🗺 데이터지도</button><button data-hand="tmap">티맵</button><button data-hand="kakao">카카오맵</button><button data-hand="naver">네이버지도</button></div>'
        + '<details class="steps"><summary>가는 차례 ' + r.mans.length + '곳 · 신호 ' + r.sigs.length + '곳</summary>' + r.mans.map(function (m) { return '<div class="st"><i>' + ARW[m.k] + '</i><b>' + km(m.d) + '</b><span>' + MKO[m.k] + (m.nm ? ' · ' + esc(m.nm) : '') + (m.sig ? ' (' + esc(m.sig) + ')' : '') + '</span></div>'; }).join('')
        + '<div class="cap">지나는 신호(닿을 때의 예상 — 계획값)</div>' + r.sigs.map(function (g) { var s = g.s; return '<div class="st"><i>🚦</i><b>' + km(g.d) + '</b><span>' + esc(g.nm) + ' · ' + (g.mv === 'Rt' ? '우회전' : g.mv === 'Lt' ? '좌회전' : g.mv === 'U' ? '유턴' : '직진') + ' — ' + (g.mv === 'Rt' || g.mv === 'U' ? '신호 자료 없음(' + (g.mv === 'Rt' ? '우회전' : '유턴') + ' · 어림 ' + Math.round(g.w) + '초로 셈)' : !s ? '<em>모름</em>(자료 없음 · 어림 ' + Math.round(g.w) + '초로 셈)' : s.kind === 'avg' ? '<em>지금 색 모름</em> · 평균 기다림 ' + Math.round(s.wait) + '초' : s.green ? '<b class="g">녹색</b> 통과 예상' : '<b class="r">적색</b> ' + Math.round(s.wait) + '초 기다림 예상') + '</span></div>'; }).join('') + '</details></div>'; }
    /* 다음 신호 판 — 핵심 */
    var ns = null; for (var q = 0; q < r.sigs.length; q++) if (r.sigs[q].d > pos - 5) { ns = r.sigs[q]; break; }
    if (!ns || !(guide || sim)) { sg.style.display = 'none'; return; }
    var dd = Math.max(0, ns.d - pos), st = ns.mv === 'St' || ns.mv === 'Lt' ? sigAt(ns.no, now, ns.side, ns.mv) : null, vNow = me && me.spd > 2 ? me.spd : ns.lim / 3.6, eta = dd / Math.max(1.5, Math.min(vNow, ns.lim / 3.6)), at = ns.mv === 'St' || ns.mv === 'Lt' ? sigAt(ns.no, now + eta, ns.side, ns.mv) : null, h = '';
    sg.style.display = 'block'; if (guide) { var tb = $('gTop').getBoundingClientRect(); sg.style.top = Math.round(tb.bottom + 6) + 'px'; } sg.className = 'sig ' + (!st || st.kind === 'avg' ? 'unk' : st.green ? 'grn' : 'red');
    h += '<div class="hd"><b>🚦 ' + esc(ns.nm) + '</b><span>' + km(dd) + ' 앞 · ' + (DIRKO[ns.side] || '') + '쪽에서 ' + (ns.mv === 'Lt' ? '좌회전' : ns.mv === 'Rt' ? '우회전' : ns.mv === 'U' ? '유턴' : '직진') + '</span></div>';
    if (ns.mv === 'Rt' || ns.mv === 'U') h += '<div class="ln">우회전·유턴은 신호 자료가 없다 — 보행자와 직진 차를 보고 간다</div>';
    else if (!st) h += '<div class="ln">이 신호는 <b>자료가 없다</b> — 눈으로 본다</div>';
    else if (st.kind === 'avg') h += '<div class="ln">지금 색은 <b>모른다</b>(이 시각대를 아직 못 받았다) · 평균 기다림 ' + Math.round(st.wait) + '초 · 주기 ' + Math.round(st.C) + '초</div>';
    else { h += '<div class="now"><i></i><b>' + (st.green ? '녹색' : '적색') + ' ' + Math.ceil(st.remain) + '초</b><span>' + (st.green ? '뒤 꺼짐' : '뒤 녹색') + '</span></div>';
      if (at && at.kind !== 'avg') { h += '<div class="ln">지금 속도로 닿으면(' + Math.round(eta) + '초 뒤) → ' + (at.green ? '<b class="g">녹색 통과</b> <em>(남은 녹색 ' + Math.floor(at.remain) + '초)</em>' : '<b class="r">적색</b> · ' + Math.ceil(at.wait) + '초 기다림') + '</div>';
        if (!at.green && MODE === 'e') h += '<div class="ln adv">🚨 닿을 때 <b class="r">적색</b> — 교차로 통과는 운전자 판단(사이렌·서행·좌우 확인) · 현장 기준: <b>1차로</b> 또는 <b>맨 가 차로</b>로 넘는다</div>';
        else if (!at.green && !night() && dd > 80) { var adv = advise(ns, dd, now); if (adv) h += '<div class="ln adv">제한속도 안에서 <b>시속 ' + adv.v + 'km</b>쯤이면 녹색에 닿는다 <em>(제한 ' + ns.lim + ' · 서두르라는 뜻이 아니다)</em></div>'; else h += '<div class="ln">제한속도 안에서는 이번 녹색에 못 닿는다 — 서두를 까닭이 없다</div>'; }
        else if (!at.green && night()) h += '<div class="ln">밤 22~06시에는 속도 안내를 하지 않는다</div>'; }
      h += '<div class="src">' + (st.kind === 'pl' ? '시각대 표(계획값)' : '방금 받은 값에서 이어 셈') + ' · 수동 조작·감응 신호면 다르다 · 눈으로 확인</div>'; }
    sg.innerHTML = h;
    if (guide && voiceOn && st && st.kind !== 'avg' && at && at.kind !== 'avg' && dd < 260 && dd > 120 && lastSay.sig !== ns.no) { lastSay.sig = ns.no; say('앞 ' + ns.nm + ' 신호, ' + (at.green ? '녹색 통과 예상' : '적색, ' + Math.ceil(at.wait) + '초 대기 예상')); }
    if (guide && voiceOn && nx) { var dm = nx.d - pos, key = nx.d + ':' + (dm < 80 ? 'b' : dm < 320 ? 'a' : ''); if ((dm < 320 && dm > 200 || dm < 80 && dm > 25) && lastSay.man !== key) { lastSay.man = key; say((dm < 80 ? '곧 ' : Math.round(dm / 50) * 50 + '미터 앞 ') + MKO[nx.k] + (nx.nm && nx.k !== 'E' ? ', ' + nx.nm + ' 방향' : '')); } }
  }
  /* 제한속도 안에서 녹색에 닿는 속도(시속 20km 이상 · 5 단위로 내림) — 없으면 null. 지금 적색일 때만 묻는다 */
  function advise(ns, dd, now) { for (var v = ns.lim; v >= 20; v -= 5) { var a = sigAt(ns.no, now + dd / (v / 3.6), ns.side, ns.mv); if (a && a.kind !== 'avg' && a.green && a.remain > 4) return { v: v }; } return null; }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function say(t) { if (!voiceOn || !window.speechSynthesis) return; try { var u = new SpeechSynthesisUtterance(t); u.lang = 'ko-KR'; u.rate = 1.05; speechSynthesis.cancel(); speechSynthesis.speak(u); } catch (e) {} }

  /* ---------- 안내 ---------- */
  var wake = null;
  /* ---------- v0.6.0 켜놓고 다니기(목적지 없이) — 소유자 「평소에 교통상황·교차로 신호값을 기본으로 · 그냥 켜놓고 다니는 모드」 ----------
     내 자리를 따라가며(진행 방향이 위) 소통 색과 둘레 신호를 보이고, **내가 가는 길을 곧장 따라가면 처음 만나는 신호**를 내 진행 방향의 값으로 보인다.
     길을 따라가는 법: 지금 선 줄에서 진행 방향 쪽 줄을 잡고, 갈림길마다 가장 덜 꺾이는(40° 안) 줄로 900m 까지. 곧장 갈 줄이 없으면(막다른 길·꺾어야 하는 삼거리) 거기서 멈춘다 */
  var cruise = false;
  function segEdges(seg) { var out = [], k; for (k = G.oHead[G.S[seg][0]]; k < G.oHead[G.S[seg][0] + 1]; k++) if (G.eS[G.oList[k]] === seg) out.push(G.oList[k]); for (k = G.oHead[G.S[seg][1]]; k < G.oHead[G.S[seg][1] + 1]; k++) if (G.eS[G.oList[k]] === seg && out.indexOf(G.oList[k]) < 0) out.push(G.oList[k]); return out; }
  function ahead() { if (!me || !G || me.out) return null; var a = nearSeg(me.x, me.y, 45); if (!a) return null; var best = -1, bdif = 61; segEdges(a.seg).forEach(function (e) { var eb = G.eR[e] ? (a.brg + 180) % 360 : a.brg, df = Math.abs(angDiff(me.hd, eb)); if (df < bdif) { bdif = df; best = e; } });
    var q = G.S[a.seg], out = { seg: a.seg, e: best, nm: q[5] >= 0 ? G.j.names[q[5]] : '', lim: q[3] || 30, cls: q[4], live: best >= 0 ? eLive(best) : null, sig: null, sigs: [] }; if (best < 0) return out;
    var p = G.SP[a.seg], al = 0, tot = 0, u; for (u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < a.u) al += l; else if (u === a.u) al += l * a.t; tot += l; }
    var fr = tot ? al / tot : 0, e = best, dist = eLen(e) * (G.eR[e] ? fr : 1 - fr), now = Date.now() / 1000, v = Math.max(3, me.spd > 2 ? me.spd : out.lim / 3.6 * 0.6);
    for (var step = 0; step < 24 && dist < 1000; step++) { var nd = G.eB[e], f = -1, fd = 40; for (var i = G.oHead[nd]; i < G.oHead[nd + 1]; i++) { var g = G.oList[i]; if (G.eB[g] === G.eA[e] && G.eS[g] === G.eS[e]) continue; var d2 = Math.abs(angDiff(eBrgIn(e), eBrgOut(g))); if (d2 < fd) { fd = d2; f = g; } }
      if (f < 0) break; var sc = sigCost(e, f, now + dist / v); if (sc) { var known = sc.si >= 0, sg = known ? G.sig[sc.si] : XS[sc.xi - 1]; var one = { nm: sg.nm, no: known ? sg.no : '', x: sg.x, y: sg.y, d: dist, side: sc.side, unk: !known, eta: dist / v }; out.sigs.push(one); if (!out.sig) out.sig = one; } dist += eLen(f); e = f; }
    return out; }
  var CRA = null;
  function drawAhead(dark, now) { if (!CRA || !CRA.sigs) return; CRA.sigs.forEach(function (g) { var q = W2S(g.x, g.y), st = g.unk ? null : sigAt(g.no, now, g.side, 'St'), ok = st && st.kind !== 'avg', tx = ok ? String(Math.ceil(st.remain)) : '?', w = ok ? 30 : 22, x = q[0] + 12, y = q[1] - 11;
      ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, 22, 11); else ctx.rect(x, y, w, 22); ctx.fillStyle = ok ? (st.green ? '#16a34a' : '#dc2626') : '#64748b'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
      ctx.font = '900 12.5px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#fff'; ctx.fillText(tx, x + w / 2, y + 11.5); }); }
  function cruiseStart() { if (!G) return; if (!me) { gpsStart(); note('내 자리를 기다리는 중 — 위치를 허락하면 따라가기 시작한다'); } cruise = true; follow = true; document.body.classList.add('guiding'); view.s = Math.max(0.5, Math.min(0.9, cv.clientHeight * 0.68 / 1000));   /* 앞으로 1km 가 화면에 들게(내 자리는 화면 68% 높이 → 뒤로는 약 470m) */
    if (me) { view.cx = me.x; view.cy = me.y; view.rot = me.hd; }
    try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) {} paint(); draw(); }
  function cruiseStop() { cruise = false; CRA = null; document.body.classList.remove('guiding'); view.rot = 0; try { if (wake) wake.release(); } catch (e) {} wake = null; paint(); draw(); }
  function paintCruise() { var top = $('gTop'), bot = $('gBot'), sg = $('gSig'), spd = $('gSpd'), now = Date.now() / 1000, A = ahead(); CRA = A; $('gFind').style.display = 'none'; top.style.display = 'flex';
    var lv = A && A.live ? spdLv(A.live, A.cls, A.lim) : -1, flow = lv < 0 ? '' : '<small class="ln2">이 길 지금 — <b>' + ['원활', '서행', '정체'][lv] + '</b> · 시속 ' + Math.round(A.live) + 'km쯤</small>';
    top.innerHTML = '<div class="arw">⬆</div><div class="tx"><b>' + (A && A.nm ? esc(A.nm) : (me ? '길 위가 아니다' : '내 자리 기다리는 중')) + '</b><span>켜놓고 다니기 — 목적지 없음</span>' + flow + '</div>';
    bot.innerHTML = '<div class="eta"><div><b>' + hm(now) + '</b><span>지금</span></div><div><b>' + (LIVE.m ? esc(String(LIVE.made || '').slice(-5)) : '없음') + '</b><span>소통 받은 때</span></div><button id="gCruiseX" class="stop">끝</button></div>';
    if (A && me) { var v = Math.round((me.spd || 0) * 3.6); spd.style.display = 'flex'; spd.innerHTML = '<div class="lim">' + A.lim + '</div><div class="cur' + (v > A.lim + 2 ? ' over' : '') + '"><b>' + v + '</b><span>km/h</span></div>' + (A.nm ? '<div class="rn">' + esc(A.nm) + '</div>' : ''); } else spd.style.display = 'none';
    var ns = A && A.sig; if (!ns) { sg.style.display = 'none'; return; } var st = ns.unk ? null : sigAt(ns.no, now, ns.side, 'St'), at = ns.unk || !(me && me.spd > 2) ? null : sigAt(ns.no, now + ns.eta, ns.side, 'St'), h = '';
    sg.style.display = 'block'; var tb = top.getBoundingClientRect(); sg.style.top = Math.round(tb.bottom + 6) + 'px'; sg.className = 'sig ' + (!st || st.kind === 'avg' ? 'unk' : st.green ? 'grn' : 'red');
    h += '<div class="hd"><b>🚦 ' + esc(ns.nm) + '</b><span>' + km(ns.d) + ' 앞 · ' + (DIRKO[ns.side] || '') + '쪽에서 직진</span></div>';
    if (!st) h += '<div class="ln">이 신호는 <b>자료가 없다</b> — 눈으로 본다</div>';
    else if (st.kind === 'avg') h += '<div class="ln">지금 색은 <b>모른다</b>(이 시각대를 아직 못 받았다) · 평균 기다림 ' + Math.round(st.wait) + '초 · 주기 ' + Math.round(st.C) + '초</div>';
    else { h += '<div class="now"><i></i><b>' + (st.green ? '녹색' : '적색') + ' ' + Math.ceil(st.remain) + '초</b><span>' + (st.green ? '뒤 꺼짐' : '뒤 녹색') + '</span></div>';
      if (at && at.kind !== 'avg') h += '<div class="ln">지금 속도로 닿으면(' + Math.round(ns.eta) + '초 뒤) → ' + (at.green ? '<b class="g">녹색 통과</b> <em>(남은 녹색 ' + Math.floor(at.remain) + '초)</em>' : '<b class="r">적색</b> · ' + Math.ceil(at.wait) + '초 기다림') + '</div>';
      h += '<div class="src">' + (st.kind === 'pl' ? '시각대 표(계획값)' : '방금 받은 값에서 이어 셈') + ' · 내 진행 방향(직진)의 값 · 수동 조작·감응 신호면 다르다 · 눈으로 확인</div>'; }
    sg.innerHTML = h; }
  function guideStart() { if (!route) return; guide = true; follow = true; document.body.classList.add('guiding'); view.s = 1.1; if (me) { view.cx = me.x; view.cy = me.y; view.rot = me.hd; } lastSay = {}; try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) {} say('안내를 시작합니다'); paint(); draw(); }
  function guideStop(done) { guide = false; document.body.classList.remove('guiding'); view.rot = 0; try { if (wake) wake.release(); } catch (e) {} wake = null; if (sim) { clearInterval(sim.t); sim = null; } if (done) { route = null; dest = null; } paint(); draw(); }
  function simStart() { if (!route) return; var r = route, d = 0, last = Date.now(); voiceOn = false; $('gVoice').classList.remove('on'); guideStart(); note('모의 주행 — 제한속도로 길을 따라간다(신호에서는 예상대로 선다) · 실제 위치가 아니다');
    sim = { t: setInterval(function () { var now = Date.now(), dt = (now - last) / 1000 * 4; last = now; var lim = 30, k; for (k = 0; k < r.lims.length; k++) if (r.lims[k][0] <= d + 1) lim = r.lims[k][1];
      var ns = null; for (k = 0; k < r.sigs.length; k++) if (r.sigs[k].d > d) { ns = r.sigs[k]; break; } var stop = false; if (ns && ns.d - d < 12 && (ns.mv === 'St' || ns.mv === 'Lt')) { var st = sigAt(ns.no, now / 1000, ns.side, ns.mv); if (st && st.kind !== 'avg' && !st.green) stop = true; }
      var v = stop ? 0 : lim / 3.6; d = Math.min(r.dist, d + v * dt / 4 * 4 / 4); var i = 0; while (i + 1 < r.cum.length && r.cum[i + 1] < d) i++; var l = (r.cum[i + 1] - r.cum[i]) || 1, t = (d - r.cum[i]) / l, ax = r.pts[i * 2], ay = r.pts[i * 2 + 1], bx = r.pts[i * 2 + 2] == null ? ax : r.pts[i * 2 + 2], by = r.pts[i * 2 + 3] == null ? ay : r.pts[i * 2 + 3];
      sim.on = 1; me = { x: ax + (bx - ax) * t, y: ay + (by - ay) * t, acc: 5, hd: brg(ax, ay, bx, by), spd: v, t: now }; if (route) track(); if (follow && me) { view.cx = me.x; view.cy = me.y; view.rot = me.hd; } paint(); draw(); if (d >= r.dist - 1 || !guide) { clearInterval(sim.t); sim = null; note(''); } }, 250) }; }

  /* ---------- 손가락 ---------- */
  var ptrs = {}, drag = null, pinch = null, lpT = 0, lpAt = null;
  cv.addEventListener('pointerdown', function (e) { try { cv.setPointerCapture(e.pointerId); } catch (x) {} ptrs[e.pointerId] = [e.offsetX, e.offsetY]; var ks = Object.keys(ptrs);
    if (ks.length === 1) { drag = { x: e.offsetX, y: e.offsetY, cx: view.cx, cy: view.cy, moved: 0, t0: Date.now() }; lpAt = [e.offsetX, e.offsetY]; clearTimeout(lpT); lpT = setTimeout(function () { if (drag && drag.moved < 8 && lpAt) pick(lpAt[0], lpAt[1]); }, 550); }
    else if (ks.length === 2) { clearTimeout(lpT); var a = ptrs[ks[0]], b = ptrs[ks[1]]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1, s: view.s }; drag = null; } });
  cv.addEventListener('pointermove', function (e) { if (!ptrs[e.pointerId]) return; ptrs[e.pointerId] = [e.offsetX, e.offsetY]; var ks = Object.keys(ptrs);
    if (pinch && ks.length >= 2) { var a = ptrs[ks[0]], b = ptrs[ks[1]]; view.s = Math.max(0.03, Math.min(4, pinch.s * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch.d)); drawSoon(); return; }
    if (drag) { var dx = e.offsetX - drag.x, dy = e.offsetY - drag.y; drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy)); if (drag.moved > 8) { clearTimeout(lpT); follow = false; $('gCen').classList.add('off'); var c = Math.cos(view.rot * Math.PI / 180), s = Math.sin(view.rot * Math.PI / 180); view.cx = drag.cx - (dx * c - dy * s) / view.s; view.cy = drag.cy - (dx * s + dy * c) / view.s; drawSoon(); } } });
  function up(e) { var tp = e.type === 'pointerup' && drag && drag.moved < 8 && Date.now() - drag.t0 < 380 ? [drag.x, drag.y] : null; if (tp) setTimeout(function () { tapAt(tp[0], tp[1]); }, 0); delete ptrs[e.pointerId]; clearTimeout(lpT); if (Object.keys(ptrs).length < 2) pinch = null; if (!Object.keys(ptrs).length) drag = null; }
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', function (e) { e.preventDefault(); view.s = Math.max(0.03, Math.min(4, view.s * (e.deltaY < 0 ? 1.2 : 1 / 1.2))); drawSoon(); }, { passive: false });
  cv.addEventListener('contextmenu', function (e) { e.preventDefault(); pick(e.offsetX, e.offsetY); });
  /* 길게 누름 → 여기로 / 여기서 */
  function pick(px, py) { if (!G || guide) return; var w = S2W(px, py), ns = nearSeg(w[0], w[1], 250), el = $('gPick'); if (!ns) { note('여기는 길에서 멀다'); return; }
    var nm = G.S[ns.seg][5] >= 0 ? G.j.names[G.S[ns.seg][5]] : '이름 없는 길'; el.style.display = 'flex'; el.style.left = Math.max(8, Math.min(cv.clientWidth - 228, px - 110)) + 'px'; el.style.top = Math.max(70, py - 64) + 'px';
    el.innerHTML = '<b>' + esc(nm) + '</b><button data-p="to">여기로 안내</button><button data-p="from">여기서 떠나기</button><button data-p="x">닫기</button>'; el._w = [ns.x, ns.y, nm]; }
  $('gPick').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var w = this._w, k = b.getAttribute('data-p'); this.style.display = 'none'; if (k === 'to') setDest(w[0], w[1], w[2]); else if (k === 'from') { if (watchId != null) { navigator.geolocation.clearWatch(watchId); watchId = null; } sim = null; setMe(w[0], w[1], 5, null, 0); note('떠나는 곳을 손으로 정했다 — 실제 위치로 돌아가려면 ◎ 를 누른다'); } });
  function setDest(x, y, nm) { if (cruise) cruiseStop(); dest = { x: x, y: y, nm: nm || '목적지' }; route = null; if (!me) gpsStart(); if (me) plan(); else { paint(); draw(); } }
  document.addEventListener('click', function (e) { var t = e.target.closest('button'); if (!t) return; var id = t.id;
    if (id === 'gGo') { voiceAsk(); guideStart(); } else if (id === 'gSim') simStart(); else if (id === 'gClr') { route = null; dest = null; note(''); paint(); draw(); } else if (id === 'gStop') guideStop(false); else if (id === 'gCruise') cruiseStart(); else if (id === 'gCruiseX') cruiseStop();
    else if (id === 'gCen') { follow = true; t.classList.remove('off'); if (watchId == null && !sim) gpsStart(); if (me) { view.cx = me.x; view.cy = me.y; if (guide) view.rot = me.hd; else if (view.s < 0.5) view.s = 0.9; } draw(); }
    else if (id === 'gVoice') { voiceOn = !voiceOn; t.classList.toggle('on', voiceOn); if (voiceOn) say('음성 안내를 켭니다'); else if (window.speechSynthesis) speechSynthesis.cancel(); }
    else if (id === 'gMic') micGo();
    else if (t.hasAttribute('data-ov')) { var k = t.getAttribute('data-ov'); OV[k] = OV[k] ? 0 : 1; t.classList.toggle('on', !!OV[k]); try { localStorage.setItem('tg_gargo_ov', JSON.stringify(OV)); } catch (x) {} draw(); }
    else if (id === 'gIn') { view.s = Math.min(4, view.s * 1.4); draw(); } else if (id === 'gOut') { view.s = Math.max(0.03, view.s / 1.4); draw(); }
    else if (t.hasAttribute('data-mode')) { MODE = t.getAttribute('data-mode'); if (dest && me) plan(); }
    else if (t.hasAttribute('data-hand')) handOff(t.getAttribute('data-hand'));
    else if (id === 'gDark') { document.documentElement.classList.toggle('dark'); try { localStorage.setItem('tg_gargo_dark', document.documentElement.classList.contains('dark') ? '1' : '0'); } catch (x) {} draw(); }
    else if (id === 'gOk') { $('gIntro').style.display = 'none'; try { localStorage.setItem('tg_gargo_intro', '1'); } catch (x) {} gpsStart(); } });
  /* 다른 내비로 넘기기 — 그 앱이 깔려 있어야 열린다(앱의 주소 규약으로 목적지 좌표와 이름만 넘긴다 · 누를 때만) */
  function handOff(k) { if (!dest) return; var lon = (dest.x / KX + LON0).toFixed(6), lat = (LAT0 - dest.y / KY).toFixed(6), nm = encodeURIComponent(dest.nm || '목적지');
    if (k === 'map') { window.open('../#lat=' + (+lat).toFixed(5) + '&lon=' + (+lon).toFixed(5), '_blank', 'noopener'); return; }   /* 같은 사이트의 데이터 압축지도 — 그 자리의 사고·신호·시설 */
    var
      u = k === 'tmap' ? 'tmap://route?goalname=' + nm + '&goalx=' + lon + '&goaly=' + lat : k === 'kakao' ? 'kakaomap://route?ep=' + lat + ',' + lon + '&by=CAR' : 'nmap://navigation?dlat=' + lat + '&dlng=' + lon + '&dname=' + nm + '&appname=340patrolman.github.io';
    note((k === 'tmap' ? '티맵' : k === 'kakao' ? '카카오맵' : '네이버지도') + '을 연다 — 앱이 깔려 있지 않으면 아무 일도 일어나지 않는다'); location.href = u; }
  function voiceAsk() { if (!window.speechSynthesis) return; voiceOn = true; $('gVoice').classList.add('on'); }
  /* 이름으로 찾기 — 신호 교차로 이름 · 길 이름(이 묶음 안) */
  var fi = $('gQ'), fl = $('gList');
  var fT = 0; fi.addEventListener('input', function () { clearTimeout(fT); var v = fi.value; fT = setTimeout(function () { findRun(v, false); }, 250); });
  fi.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); clearTimeout(fT); findRun(fi.value, true); } });
  fl.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; pickFound(+b.getAttribute('data-i')); });
  /* 주소로 받은 목적지 — #to=위도,경도&nm=이름 · #from=위도,경도(시험) · 주소에서 지운다(좌표가 남지 않게) */
  function hashGo() { var H = location.hash || '', t = /[#&]to=(-?[\d.]+),(-?[\d.]+)/.exec(H), f = /[#&]from=(-?[\d.]+),(-?[\d.]+)/.exec(H), n = /[#&]nm=([^&]*)/.exec(H);
    if (f) setMe(PX(+f[2]), PY(+f[1]), 5, null, 0); if (t) { var x = PX(+t[2]), y = PY(+t[1]), ns = nearSeg(x, y, 600); if (ns) setDest(ns.x, ns.y, n ? decodeURIComponent(n[1]) : '받은 자리'); else note('받은 자리가 서초구 둘레 밖이다 — 시험판은 서초구와 둘레 2km 안에서만 된다'); }
    /* #q=주소·이름 — 받은 글로 바로 찾는다(티북 같은 데서 주소를 넘길 때 · # 뒤라 서버로 가지 않는다 · 읽고 지운다) */
    var qq = /[#&]q=([^&]*)/.exec(H); if (qq) { var qv = ''; try { qv = decodeURIComponent(qq[1]); } catch (e) {} if (qv) { fi.value = qv; findRun(qv, true); } }
    if (t || f || qq) { try { history.replaceState(null, '', location.pathname); } catch (e) {} } }
  setInterval(function () { if (document.hidden) return; if (route && (guide || sim)) { paint(); draw(); } else if (cruise && !route) { paint(); draw(); } else if (route || (OV.s && SIG.ready && view.s > 0.28)) draw(); }, 1000);
  /* 5분마다 — 통행속도 한 장과 신호 색인을 다시 본다. 신호 수집기가 약 15분마다 새 값을 올리므로(색인의 made 가 바뀐다) 바뀌었으면 서초 둘레 칸을 다시 받아 그 자리에서 갈아 끼운다.
     소유자 2026-10-13 「신호값이 업데이트되는 대로 계속 추가 업데이트되게」 — 안내 중에도 받는다(지금 색·남은 초가 새 값으로 바뀐다 · 길은 다시 고르지 않는다) */
  function sigRefresh() { return getJ('../data/sigdir/index.json').then(function (j) { if (!j || !j.fl || !SIG.idx || j.made === SIG.idx.made) return false; var need = {}; G.sig.forEach(function (s) { if (j.fl[s.no] == null) return; var q = j.pts[s.no]; if (q) need[Math.floor(q[0] / j.cell[0]) + '_' + Math.floor(q[1] / j.cell[1])] = 1; });
    var its = {}; return Promise.all(Object.keys(need).map(function (k) { return getJ('../data/sigdir/c/' + k + '.json').then(function (c) { if (c && c.its) Object.keys(c.its).forEach(function (no) { its[no] = c.its[no]; }); }); })).then(function () { if (!Object.keys(its).length) return false; SIG.idx = j; SIG.pl = j.pl || {}; SIG.cell = j.cell; SIG.its = its; SIG.at = Date.now(); return true; }); }); }
  setInterval(function () { if (!G || document.hidden) return; Promise.all([liveLoad(), sigRefresh()]).then(function (r) { if (dest && me && !guide) plan(); else { paint(); draw(); } }); }, 300000);
  window.addEventListener('resize', function () { draw(); });
  document.addEventListener('visibilitychange', function () { if (!document.hidden && (guide || cruise) && navigator.wakeLock) { try { navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) {} } });
  try { var dk = localStorage.getItem('tg_gargo_dark'), hr = new Date().getHours(); if (dk === '1' || (dk == null && (hr >= 19 || hr < 6))) document.documentElement.classList.add('dark'); } catch (e) {}
  function boot() { if (document.documentElement.classList.contains('gated')) return; var seen = false; try { seen = localStorage.getItem('tg_gargo_intro') === '1'; } catch (e) {} if (seen) { $('gIntro').style.display = 'none'; if (!/[#&]from=/.test(location.hash)) gpsStart(); } load(); }
  window.addEventListener('tggate', boot); boot();
  window.GARGO = { cruise: function (on) { if (on === false) cruiseStop(); else cruiseStart(); return cruise; }, ahead: ahead, mvOf: mvOf, liver: function () { return LIVER; }, view: view, state: function () { return { me: me, dest: dest, route: route, guide: guide, sig: SIG, G: G }; }, sigAt: sigAt, plan: plan, setDest: setDest, setMe: setMe, draw: draw, P: function (lon, lat) { return [PX(lon), PY(lat)]; }, findRoute: findRoute, simStart: simStart, guideStart: guideStart, advise: advise, spdLv: spdLv, night: night, addrGuess: addrGuess };
})();
