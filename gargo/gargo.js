/* 가르고 — 서초 출동 길 안내(시험판). 소유자 2026-10-13 「가르고 내비를 본격적으로 · 우선 서초구 한정 · T-Book 홈에서 · 티맵·네이버 내비 같은 양식 + 신호값을 이용한 차원이 다른 안내가 핵심」.
   자료(같은 사이트의 파일만 · 외부 통신 0): gargo/pack-seocho.json(길 계산 묶음 · tools/gargo/pack-bake.py) · ../data/sigdir/index.json + c/<칸>.json(방향별 신호 · 15분마다) · ../data/sig-special.json(특수일).
   지키는 것: 제한속도를 넘는 값은 어디에도 내지 않는다 · 밤 22~06시에는 속도 안내를 하지 않는다 · 신호는 계획값(수동 조작·감응이면 다르다)이라고 밝힌다 · 모르는 신호는 「모름」(0 으로 치지 않는다)
   · 지도는 OpenStreetMap 바탕의 시험용(일방통행·회전 제한이 현장과 다를 수 있다) · 위치·목적지는 이 기기 안에서만 쓰고 저장하지 않는다 · 판단과 주의는 운전자 몫.
   신호 계산식 = gargo/tools/sigwait.py(= datamap sdState·sdLive)와 같다. */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var cv = $('gMap'), ctx = cv.getContext('2d'), DPR = Math.min(window.devicePixelRatio || 1, 2);
  var LON0 = 127.02, LAT0 = 37.48, KX = 111320 * Math.cos(LAT0 * Math.PI / 180), KY = 110940;
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
    return getJ('pack-seocho.json').then(function (j) { if (!j || !j.seg) { msg('길 자료를 읽지 못했다 — 새로 고쳐 본다'); return; } build(j); msg(''); fitAll(); draw(); hashGo(); sigLoad(); });
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
  function nearSeg(x, y, maxD) { var gx = Math.floor(x / GC), gy = Math.floor(y / GC), best = null, bd = maxD || 300, seen = {};
    for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) { var L = GRID[(gx + dx) + ',' + (gy + dy)]; if (!L) continue; for (var q = 0; q < L.length; q++) { var i = L[q]; if (seen[i]) continue; seen[i] = 1; var p = G.SP[i];
      for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], bx = p[u + 2], by = p[u + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2)) : 0, px = ax + vx * t, py = ay + vy * t, d = Math.hypot(px - x, py - y);
        if (d < bd) { bd = d; best = { seg: i, u: u, t: t, x: px, y: py, d: d, brg: brg(ax, ay, bx, by) }; } } } }
    return best; }
  function brg(x1, y1, x2, y2) { return (Math.atan2(x2 - x1, -(y2 - y1)) * 180 / Math.PI + 360) % 360; }
  function angDiff(a, b) { return ((b - a + 540) % 360) - 180; }   /* +면 오른쪽으로 꺾음 */

  /* ---------- 신호 ---------- */
  function liveLoad() { return getJ('../data/live-spd-seocho.json').then(function (j) { var ok = j && j.m && j.at && Date.now() / 1000 - j.at < 1200; LIVE = ok ? { m: j.m, at: j.at, made: j.made } : { m: null, at: j && j.at || 0 }; }); }
  function sigLoad() { liveLoad().then(function () { if (dest && me && !guide) plan(); else paint(); }); getJ('../data/sig-special.json').then(function (j) { if (j && j.days) SIG.hol = j.days; });
    return getJ('../data/sigdir/index.json').then(function (j) { if (!j || !j.fl) { note('신호 자료를 읽지 못했다 — 길 안내는 제한속도 기준으로만 한다'); return; } SIG.idx = j; SIG.pl = j.pl || {}; SIG.cell = j.cell; var need = {};
      G.sig.forEach(function (s) { if (j.fl[s.no] == null) return; var q = j.pts[s.no]; if (q) need[Math.floor(q[0] / j.cell[0]) + '_' + Math.floor(q[1] / j.cell[1])] = 1; });
      return Promise.all(Object.keys(need).map(function (k) { return getJ('../data/sigdir/c/' + k + '.json').then(function (c) { if (c && c.its) Object.keys(c.its).forEach(function (no) { SIG.its[no] = c.its[no]; }); }); })).then(function () {
        var v = []; Object.keys(SIG.its).forEach(function (no) { SIG.its[no].forEach(function (r) { if (!recOk(r)) return; var C = r.ci || r.cyc; if (!C) return; r.mv.forEach(function (m) { if (m[1] === 'St' && m[2] != null && m[2] < C) v.push((C - m[2]) * (C - m[2]) / (2 * C)); }); }); });
        v.sort(function (a, b) { return a - b; }); if (v.length) SIG.typ = v[v.length >> 1]; SIG.ready = 1; if (dest && me) plan(); draw(); paint(); }); });
  }
  function recOk(r) { return r && r.mv && r.dq !== 'dir' && !(r.x && !r.v); }
  function mvOf(rec, side, mv) { var i = DIRS.indexOf(side), best = null; rec.mv.forEach(function (m) { if (m[1] !== mv || m[2] == null || m[5] == null) return; var k = DIRS.indexOf(m[0]); if (k < 0) return; var d = Math.min((k - i + 8) % 8, (i - k + 8) % 8); if (d <= 1 && (!best || d < best[0])) best = [d, m]; }); return best ? best[1] : null; }
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
  function eV(e) { var lim = eSpd(e), v = eLive(e); return v ? Math.max(4, Math.min(lim, v)) : lim; }
  /* 길 고르기에만 쓰는 무게(가정 — 시간 표시에는 안 넣는다): 골목·생활도로·진입로(등급 6)은 1.7배 · 생활도로·진입로(7·8)는 2.2배 느리게 치고, 신호 없는 곳에서 꺾으면 좌 12초·우 6초를 얹는다.
     넣지 않으면 신호 한두 개를 피하려고 골목을 지그재그로 도는 길이 나온다(시험: 서초역 → 양재역이 열다섯 번 꺾였다) */
  function eCost(e) { var c = G.S[G.eS[e]][4]; return eLen(e) / (eV(e) / 3.6) * (c >= 7 ? 2.2 : c === 6 ? 1.7 : 1); }
  function turnPen(e, f) { if (G.oHead[G.eB[e] + 1] - G.oHead[G.eB[e]] < 2) return 0; var k = turnKind(angDiff(eBrgIn(e), eBrgOut(f))); return k === 'L' ? 12 : k === 'R' ? 6 : k === 'U' ? 30 : 0; }
  function eBrgIn(e) { var p = G.SP[G.eS[e]], n = p.length; return G.eR[e] ? brg(p[2], p[3], p[0], p[1]) : brg(p[n - 4], p[n - 3], p[n - 2], p[n - 1]); }     /* 닿는 쪽 끝의 진행 방위 */
  function eBrgOut(e) { var p = G.SP[G.eS[e]], n = p.length; return G.eR[e] ? brg(p[n - 2], p[n - 1], p[n - 4], p[n - 3]) : brg(p[0], p[1], p[2], p[3]); }   /* 떠나는 쪽 첫머리의 진행 방위 */
  function turnKind(dA) { var a = Math.abs(dA); return a < 28 ? 'S' : a > 150 ? 'U' : dA > 0 ? (a < 60 ? 'r' : 'R') : (a < 60 ? 'l' : 'L'); }
  function heapPush(h, k, v) { h.push([k, v]); var i = h.length - 1; while (i > 0) { var p = (i - 1) >> 1; if (h[p][0] <= h[i][0]) break; var t = h[p]; h[p] = h[i]; h[i] = t; i = p; } }
  function heapPop(h) { var top = h[0], last = h.pop(); if (h.length) { h[0] = last; var i = 0; for (;;) { var l = i * 2 + 1, r = l + 1, m = i; if (l < h.length && h[l][0] < h[m][0]) m = l; if (r < h.length && h[r][0] < h[m][0]) m = r; if (m === i) break; var t = h[m]; h[m] = h[i]; h[i] = t; i = m; } } return top; }
  function sigCost(ei, ej, T) { var nd = G.eB[ei], si = G.n2s[nd]; if (si < 0 || G.n2s[G.eA[ei]] === si) return null;   /* 신호 넓이에 막 들어서는 줄만 */
    var tk = turnKind(angDiff(eBrgIn(ei), eBrgOut(ej))); var side = sideOf(eBrgIn(ei)); if (tk === 'R' || tk === 'r') return { w: 4, mv: 'Rt', si: si, side: side }; if (tk === 'U') return { w: 0, mv: 'U', si: si, side: side };
    var mv = tk === 'L' || tk === 'l' ? 'Lt' : 'St', s = SIG.ready ? sigAt(G.sig[si].no, T, side, mv) : null; return { w: s ? s.wait : SIG.typ, mv: mv, side: side, si: si, s: s }; }
  function findRoute(sx, sy, tx, ty, T0, sbrg) {
    var a = nearSeg(sx, sy, 400), b = nearSeg(tx, ty, 600); if (!a || !b) return null;
    var D = new Float64Array(G.ne).fill(Infinity), PR = new Int32Array(G.ne).fill(-1), h = [], i, e;
    /* 떠나는 줄 = 내가 있는 길의 두 방향(갈 수 있는 쪽) — 남은 길이만큼 · 진행 방향이 반대면 유턴 벌점 */
    var starts = []; for (e = 0; e < G.ne; e++) { if (G.eS[e] === a.seg) starts.push(e); if (starts.length === 2) break; }
    if (!starts.length) { for (i = G.oHead[G.S[a.seg][0]]; i < G.oHead[G.S[a.seg][0] + 1]; i++) starts.push(G.oList[i]); }
    var p = G.SP[a.seg], along = 0, tot = 0, u; for (u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < a.u) along += l; else if (u === a.u) along += l * a.t; tot += l; }
    starts.forEach(function (se) { var frac = tot ? (G.eR[se] ? along / tot : 1 - along / tot) : 1, c = eLen(se) * frac / (eV(se) / 3.6); if (sbrg != null && G.eS[se] === a.seg) { var eb = G.eR[se] ? (a.brg + 180) % 360 : a.brg; if (Math.abs(angDiff(sbrg, eb)) > 110) c += 30; } D[se] = c; heapPush(h, c, se); });
    var goal = {}; for (e = 0; e < G.ne; e++) if (G.eS[e] === b.seg) goal[e] = 1; var end = -1;
    while (h.length) { var top = heapPop(h), d = top[0]; e = top[1]; if (d > D[e]) continue; if (goal[e]) { end = e; break; }
      var nd = G.eB[e], key = nd + '|' + eWay(e), bn = G.ban[key], on = G.only[key];
      for (i = G.oHead[nd]; i < G.oHead[nd + 1]; i++) { var f = G.oList[i], w2 = eWay(f); if ((bn && bn[w2]) || (on && !on[w2])) continue;
        var w = eCost(f); if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) w += 30; var sc = sigCost(e, f, T0 + d); if (sc && MODE !== 'e') w += sc.w; if (!sc) w += turnPen(e, f);
        if (d + w < D[f]) { D[f] = d + w; PR[f] = e; heapPush(h, d + w, f); } } }
    if (end < 0) return null; var es = [end]; while (PR[es[es.length - 1]] >= 0) es.push(PR[es[es.length - 1]]); es.reverse();
    return shape(es, a, b, T0); }
  /* 길 꼴 — 선 · 거리 · 꺾는 곳 · 지나는 신호 */
  function shape(es, a, b, T0) {
    var pts = [], cum = [0], mans = [], sigs = [], t = 0, dist = 0, i, k, liveLen = 0, cong = [];
    function add(x, y) { if (pts.length) { var d = Math.hypot(x - pts[pts.length - 2], y - pts[pts.length - 1]); if (d < 0.05) return; dist += d; cum.push(dist); } pts.push(x, y); }
    for (i = 0; i < es.length; i++) { var e = es[i], p = G.SP[G.eS[e]], n = p.length / 2, rev = G.eR[e], q = [];
      for (k = 0; k < n; k++) { var u = (rev ? n - 1 - k : k) * 2; q.push(p[u], p[u + 1]); }
      if (i === 0) { var cut = [a.x, a.y], st = false; for (k = 0; k < n - 1; k++) { var u0 = rev ? (n - 2 - k) * 2 : k * 2; if (!st && u0 === a.u) { st = true; cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } else if (st) cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } if (cut.length >= 4) q = cut; }
      if (i === es.length - 1) { var c2 = [], done = false; for (k = 0; k < q.length / 2 && !done; k++) { c2.push(q[k * 2], q[k * 2 + 1]); if (k + 1 < q.length / 2) { var ax = q[k * 2], ay = q[k * 2 + 1], bx = q[k * 2 + 2], by = q[k * 2 + 3], l2 = (bx - ax) * (bx - ax) + (by - ay) * (by - ay), tt = l2 ? ((b.x - ax) * (bx - ax) + (b.y - ay) * (by - ay)) / l2 : 0; if (tt >= 0 && tt <= 1 && Math.hypot(ax + (bx - ax) * tt - b.x, ay + (by - ay) * tt - b.y) < 3) { c2.push(b.x, b.y); done = true; } } } q = c2; }
      var d0 = dist; for (k = 0; k < q.length; k += 2) add(q[k], q[k + 1]);
      var len = dist - d0, spd = eSpd(e), lv = eLive(e); t += len / (eV(e) / 3.6); if (lv) { liveLen += len; if (lv < spd * 0.6) cong.push([d0, dist, lv < spd * 0.35 ? 2 : 1]); }
      if (i + 1 < es.length) { var f = es[i + 1], dA = angDiff(eBrgIn(e), eBrgOut(f)), tk = turnKind(dA), outs = G.oHead[G.eB[e] + 1] - G.oHead[G.eB[e]], nm = G.S[G.eS[f]][5] >= 0 ? G.j.names[G.S[G.eS[f]][5]] : '';
        if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) { tk = 'U'; t += 30; }
        var sc = sigCost(e, f, T0 + t); if (sc) { var sg = G.sig[sc.si]; sigs.push({ si: sc.si, no: sg.no, nm: sg.nm, d: dist, side: sc.side, mv: sc.mv, t: t, w: sc.w, s: sc.s, lim: spd }); if (MODE !== 'e') t += sc.w; }
        var cn = G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '';   /* 같은 이름의 길에서 살짝 휘는 것(갈래 차로·굽은 길)은 안내하지 않는다 */
        if (tk !== 'S' && outs > 1 && !((tk === 'r' || tk === 'l') && nm && nm === cn)) { var last = mans[mans.length - 1]; if (last && dist - last.d < 18 && last.k === tk) { last.nm = nm || last.nm; } else mans.push({ d: dist, k: tk, nm: nm, sig: sc ? G.sig[sc.si].nm : '', e: e }); } }
    }
    mans.push({ d: dist, k: 'E', nm: dest && dest.nm || '목적지' });
    var lims = []; var dd = 0; es.forEach(function (e, i2) { lims.push([dd, eSpd(e), G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '', G.S[G.eS[e]][9]]); dd += eLen(e); });
    var free = 0; es.forEach(function (e) { free += eLen(e) / (eSpd(e) / 3.6); });
    return { es: es, pts: pts, cum: cum, dist: dist, time: t, free: free, mans: mans, sigs: sigs, lims: lims, T0: T0, a: a, b: b, live: dist ? liveLen / dist : 0, cong: cong, mode: MODE };
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
    if (dest && !route && G) plan(); if (route) track(); if (follow) { view.cx = me.x; view.cy = me.y; if (guide) view.rot = me.hd; } paint(); draw(); }
  /* 길 위의 내 자리(진행 거리) · 벗어나면 다시 계산 */
  function track() { var r = route, best = 1e9, bd = r.pos || 0, lo = 0, i; for (i = 0; i + 3 < r.pts.length; i += 2) { var k = i / 2; if (r.cum[k + 1] < (r.pos || 0) - 60) continue; if (r.cum[k] > (r.pos || 0) + 400) break; var ax = r.pts[i], ay = r.pts[i + 1], bx = r.pts[i + 2], by = r.pts[i + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((me.x - ax) * vx + (me.y - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - me.x, ay + vy * t - me.y); if (d < best) { best = d; bd = r.cum[k] + Math.sqrt(l2) * t; lo = i; } }
    r.off = best; if (best < 45) { r.pos = bd; r.offN = 0; r.sx = null; var ax2 = r.pts[lo], ay2 = r.pts[lo + 1], bx2 = r.pts[lo + 2], by2 = r.pts[lo + 3], l = Math.hypot(bx2 - ax2, by2 - ay2) || 1, tt = (bd - r.cum[lo / 2]) / l; r.sx = [ax2 + (bx2 - ax2) * tt, ay2 + (by2 - ay2) * tt, brg(ax2, ay2, bx2, by2)]; }
    else { r.offN = (r.offN || 0) + 1; if (guide && r.offN >= 3 && Date.now() - (r.reT || 0) > 6000) { r.reT = Date.now(); say('경로를 벗어났습니다. 다시 찾습니다'); plan(); return; } }
    if (guide && r.dist - r.pos < 25) { say('목적지 부근입니다. 안내를 마칩니다'); guideStop(true); } }

  /* ---------- 그리기 ---------- */
  var RS = { 1: [15, '#f2a65a', '#c2742a'], 2: [13, '#f6c667', '#c9962e'], 3: [11, '#fbe08f', '#cdb06a'], 4: [9, '#ffffff', '#b9c1cc'], 5: [7.5, '#ffffff', '#c3cad4'], 6: [5.5, '#ffffff', '#cfd5dd'], 7: [4, '#f8fafc', '#d9dee5'], 8: [3, '#f1f5f9', '#dfe4ea'] };
  function resize() { var w = cv.clientWidth, h = cv.clientHeight; if (!w || !h) return; if (cv.width !== Math.round(w * DPR) || cv.height !== Math.round(h * DPR)) { cv.width = Math.round(w * DPR); cv.height = Math.round(h * DPR); } }
  function anchorY() { return guide ? cv.clientHeight * 0.68 : cv.clientHeight * 0.5; }
  function W2S(x, y) { var c = Math.cos(-view.rot * Math.PI / 180), s = Math.sin(-view.rot * Math.PI / 180), dx = (x - view.cx) * view.s, dy = (y - view.cy) * view.s; return [cv.clientWidth / 2 + dx * c - dy * s, anchorY() + dx * s + dy * c]; }
  function S2W(px, py) { var c = Math.cos(view.rot * Math.PI / 180), s = Math.sin(view.rot * Math.PI / 180), dx = (px - cv.clientWidth / 2) / view.s, dy = (py - anchorY()) / view.s; return [view.cx + dx * c - dy * s, view.cy + dx * s + dy * c]; }
  var DQ = 0; function drawSoon() { if (DQ) return; DQ = 1; var f = function () { if (!DQ) return; DQ = 0; draw(); }; requestAnimationFrame(f); setTimeout(f, 150); }
  function draw() { resize(); var W = cv.clientWidth, H = cv.clientHeight; if (!W) return; var dark = document.documentElement.classList.contains('dark');
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.fillStyle = dark ? '#111827' : '#eef1f4'; ctx.fillRect(0, 0, W, H); if (!G) return;
    ctx.save(); ctx.translate(W / 2, anchorY()); ctx.rotate(-view.rot * Math.PI / 180); ctx.scale(view.s, view.s); ctx.translate(-view.cx, -view.cy); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    var s = view.s, show = function (c) { return c <= 3 || (c <= 5 && s > 0.05) || (c === 6 && s > 0.12) || (c === 7 && s > 0.2) || (c === 8 && s > 0.35); }, c;
    for (c = 8; c >= 1; c--) { if (!G.PATH[c] || !show(c)) continue; ctx.lineWidth = Math.max(RS[c][0], (c <= 3 ? 2.6 : 1.4) / s) + 2 / s; ctx.strokeStyle = dark ? '#0b1220' : RS[c][2]; ctx.stroke(G.PATH[c]); }
    for (c = 8; c >= 1; c--) { if (!G.PATH[c] || !show(c)) continue; ctx.lineWidth = Math.max(RS[c][0], (c <= 3 ? 2.6 : 1.4) / s); ctx.strokeStyle = dark ? (c <= 3 ? '#8a6d2f' : '#374151') : RS[c][1]; ctx.stroke(G.PATH[c]); }
    if (route) { var p = route.pts, i; ctx.beginPath(); ctx.moveTo(p[0], p[1]); for (i = 2; i < p.length; i += 2) ctx.lineTo(p[i], p[i + 1]); ctx.lineWidth = Math.max(11, 9 / s); ctx.strokeStyle = '#0b3d91'; ctx.stroke(); ctx.lineWidth = Math.max(7.5, 6 / s); ctx.strokeStyle = '#2f7bff'; ctx.stroke();
      route.cong.forEach(function (cg) { ctx.beginPath(); var on = false; for (var u = 0; u < p.length; u += 2) { var dd = route.cum[u / 2]; if (dd >= cg[0] - 0.5 && dd <= cg[1] + 0.5) { if (!on) { ctx.moveTo(p[u], p[u + 1]); on = true; } else ctx.lineTo(p[u], p[u + 1]); } } ctx.lineWidth = Math.max(7.5, 6 / s); ctx.strokeStyle = cg[2] === 2 ? '#dc2626' : '#f59e0b'; ctx.stroke(); }); }
    ctx.restore();
    /* 이름표 */
    if (s > 0.06) { var boxes = [], n = 0, seen = {}; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.font = '700 12px system-ui, sans-serif';
      for (var li = 0; li < G.LAB.length && n < 26; li++) { var L = G.LAB[li]; if ((L.c >= 5 && s < 0.3) || (L.c === 4 && s < 0.15)) continue; var q = W2S(L.x, L.y); if (q[0] < 30 || q[0] > W - 30 || q[1] < 90 || q[1] > H - 120) continue; var sl = seen[L.n]; if (sl && sl.some(function (o) { return Math.hypot(o[0] - q[0], o[1] - q[1]) < 240; })) continue;
        var tw = ctx.measureText(L.n).width; if (tw + 16 > L.L * s) continue; var hit = false; for (var bi = 0; bi < boxes.length; bi++) { var b = boxes[bi]; if (Math.abs(b[0] - q[0]) < (b[2] + tw) / 2 + 6 && Math.abs(b[1] - q[1]) < 18) { hit = true; break; } } if (hit) continue; boxes.push([q[0], q[1], tw]); (seen[L.n] = seen[L.n] || []).push(q); n++;
        var a = L.a - view.rot * Math.PI / 180; a = Math.atan2(Math.sin(a), Math.cos(a)); if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI; ctx.save(); ctx.translate(q[0], q[1]); ctx.rotate(a); ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(17,24,39,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(L.n, 0, 0); ctx.fillStyle = dark ? '#cbd5e1' : '#374151'; ctx.fillText(L.n, 0, 0); ctx.restore(); } }
    /* 신호 — 길 위의 신호는 지금 색(아는 곳만) · 그 밖은 작은 회색 점 */
    var now = Date.now() / 1000, onR = {}; if (route) route.sigs.forEach(function (g) { onR[g.si] = g; });
    if (s > 0.1) G.sig.forEach(function (sg, si) { if (onR[si]) return; var q = W2S(sg.x, sg.y); if (q[0] < -10 || q[0] > W + 10 || q[1] < -10 || q[1] > H + 10) return; ctx.beginPath(); ctx.arc(q[0], q[1], 3.2, 0, Math.PI * 2); ctx.fillStyle = dark ? '#64748b' : '#94a3b8'; ctx.fill(); });
    if (route) route.sigs.forEach(function (g) { var sg = G.sig[g.si], q = W2S(sg.x, sg.y); if (q[0] < -20 || q[0] > W + 20 || q[1] < -20 || q[1] > H + 20) return; var st = g.mv === 'St' || g.mv === 'Lt' ? sigAt(g.no, now, g.side, g.mv) : null, col = !st || st.kind === 'avg' ? '#94a3b8' : st.green ? '#16a34a' : '#dc2626';
      ctx.beginPath(); ctx.arc(q[0], q[1], 9, 0, Math.PI * 2); ctx.fillStyle = '#111827'; ctx.fill(); ctx.beginPath(); ctx.arc(q[0], q[1], 6.5, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill();
      if (st && st.kind !== 'avg' && s > 0.25) { var tx = Math.ceil(st.remain) + ''; ctx.font = '800 11px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = '#fff'; ctx.strokeText(tx, q[0], q[1] - 17); ctx.fillStyle = col; ctx.fillText(tx, q[0], q[1] - 17); } });
    if (dest) { var dq = W2S(dest.x, dest.y); ctx.beginPath(); ctx.moveTo(dq[0], dq[1]); ctx.lineTo(dq[0] - 9, dq[1] - 22); ctx.arc(dq[0], dq[1] - 26, 10, Math.PI * 0.85, Math.PI * 0.15); ctx.closePath(); ctx.fillStyle = '#e11d48'; ctx.fill(); ctx.beginPath(); ctx.arc(dq[0], dq[1] - 26, 4, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); }
    if (me) { var mp = route && route.sx && route.off < 45 ? route.sx : [me.x, me.y, me.hd], mq = W2S(mp[0], mp[1]); if (me.acc > 30) { ctx.beginPath(); ctx.arc(mq[0], mq[1], Math.max(14, me.acc * s), 0, Math.PI * 2); ctx.fillStyle = 'rgba(37,99,235,.12)'; ctx.fill(); }
      ctx.save(); ctx.translate(mq[0], mq[1]); ctx.rotate(((guide ? mp[2] : me.hd) - view.rot) * Math.PI / 180); ctx.beginPath(); ctx.moveTo(0, -15); ctx.lineTo(11, 11); ctx.lineTo(0, 5); ctx.lineTo(-11, 11); ctx.closePath(); ctx.fillStyle = '#1d4ed8'; ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke(); ctx.fill(); ctx.restore(); }
  }
  function fitAll() { var b = G.box; view.cx = (b[0] + b[1]) / 2; view.cy = (b[2] + b[3]) / 2; view.s = Math.min(cv.clientWidth / (b[1] - b[0]), cv.clientHeight / (b[3] - b[2])) * 1.9; view.rot = 0; }
  function fitRoute() { var p = route.pts, b = [1e9, -1e9, 1e9, -1e9]; for (var i = 0; i < p.length; i += 2) { if (p[i] < b[0]) b[0] = p[i]; if (p[i] > b[1]) b[1] = p[i]; if (p[i + 1] < b[2]) b[2] = p[i + 1]; if (p[i + 1] > b[3]) b[3] = p[i + 1]; }
    view.rot = 0; view.cx = (b[0] + b[1]) / 2; view.cy = (b[2] + b[3]) / 2 + (b[3] - b[2]) * 0.12; view.s = Math.min(3, Math.min(cv.clientWidth / ((b[1] - b[0]) * 1.25 + 80), cv.clientHeight * 0.55 / ((b[3] - b[2]) * 1.25 + 80))); follow = false; }

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
    if (!route) { top.style.display = 'none'; sg.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = guide ? 'none' : 'flex';
      bot.innerHTML = '<div class="hint">' + (dest ? (me ? '길을 찾는 중…' : '내 자리를 기다리는 중 — 위치를 허락하거나, 지도를 <b>길게 눌러</b> 「여기서 떠나기」를 고른다') : '목적지를 정한다 — 지도를 <b>길게 누르거나</b> 위에서 이름을 찾는다') + '</div>' + (me && me.out ? '<div class="hint warn">지금 자리가 서초구 둘레 밖이다 — 시험판은 서초구와 둘레 2km 안에서만 길을 찾는다.</div>' : ''); return; }
    var r = route, now = Date.now() / 1000, pos = r.pos || 0, left = Math.max(0, r.dist - pos), frac = r.dist ? left / r.dist : 0, tLeft = r.time * frac;
    var nx = null, n2 = null; for (var i = 0; i < r.mans.length; i++) if (r.mans[i].d > pos + 5) { nx = r.mans[i]; n2 = r.mans[i + 1] || null; break; }
    var known = r.sigs.filter(function (g) { return g.s && g.s.kind !== 'avg'; }).length, wsum = 0; r.sigs.forEach(function (g) { wsum += g.w || 0; });
    if (guide) { $('gFind').style.display = 'none'; top.style.display = 'flex';
      top.innerHTML = nx ? '<div class="arw">' + ARW[nx.k] + '</div><div class="tx"><b>' + km(nx.d - pos) + '</b><span>' + (nx.k === 'E' ? '목적지' : MKO[nx.k]) + (nx.nm ? ' · ' + esc(nx.nm) : '') + (nx.sig ? ' <em>(' + esc(nx.sig) + ')</em>' : '') + '</span>' + (function () { var lh = nx.d - pos < 700 ? laneHint(nx) : ''; return lh ? '<small class="ln2">차로 — ' + lh + '</small>' : ''; })() + (n2 ? '<small>그다음 ' + ARW[n2.k] + ' ' + km(n2.d - nx.d) + ' 뒤 ' + MKO[n2.k] + '</small>' : '') + '</div>' : '';
      bot.innerHTML = '<div class="eta"><div><b>' + hm(now + tLeft) + '</b><span>도착</span></div><div><b>' + mmss(tLeft) + '</b><span>남은 시간</span></div><div><b>' + km(left) + '</b><span>남은 거리</span></div><button id="gStop" class="stop">안내 끝</button></div>';
      var lim = 0, rn = ''; for (var k = 0; k < r.lims.length; k++) if (r.lims[k][0] <= pos + 1) { lim = r.lims[k][1]; rn = r.lims[k][2]; } spd.style.display = 'flex'; var v = Math.round((me && me.spd || 0) * 3.6);
      spd.innerHTML = '<div class="lim">' + lim + '</div><div class="cur' + (v > lim + 2 ? ' over' : '') + '"><b>' + v + '</b><span>km/h</span></div>' + (rn ? '<div class="rn">' + esc(rn) + '</div>' : '');
    } else { top.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = 'flex';
      bot.innerHTML = '<div class="sum"><div class="big"><b>' + mmss(r.time) + '</b> <span>' + km(r.dist) + ' · ' + hm(now + r.time) + ' 도착</span></div>'
        + '<div class="mode"><button data-mode="n" class="' + (MODE === 'n' ? 'on' : '') + '">일반 — 신호를 지킨다</button><button data-mode="e" class="' + (MODE === 'e' ? 'on' : '') + '">🚨 긴급 출동</button></div>'
        + '<div class="sub">신호 ' + r.sigs.length + '곳 · 그 가운데 지금 색을 아는 곳 ' + known + (MODE === 'e' ? ' · <b>신호 기다림을 셈에서 뺐다</b>(닿을 때 적색이면 알려 준다 — 통과는 운전자 판단)' : ' · 신호 기다림 ' + mmss(wsum) + ' 포함') + '<br>'
          + (LIVE.m ? '🚗 통행속도 반영(' + esc(LIVE.made || '') + ' 받음 · 길의 ' + Math.round(r.live * 100) + '%에 값' + (r.cong.length ? ' · <b class="r">막히는 구간 ' + r.cong.length + '곳</b>' : ' · 막히는 구간 없음') + ')' : '🚗 통행속도 없음(받은 지 20분 넘음) — 제한속도로 셈') + ' · 신호·막힘이 없다면 ' + mmss(r.free) + '</div>'
        + '<div class="btns"><button id="gGo" class="go">▶ 안내 시작</button><button id="gSim">모의 주행</button><button id="gClr">지우기</button></div>'
        + '<details class="steps"><summary>가는 차례 ' + r.mans.length + '곳 · 신호 ' + r.sigs.length + '곳</summary>' + r.mans.map(function (m) { return '<div class="st"><i>' + ARW[m.k] + '</i><b>' + km(m.d) + '</b><span>' + MKO[m.k] + (m.nm ? ' · ' + esc(m.nm) : '') + (m.sig ? ' (' + esc(m.sig) + ')' : '') + '</span></div>'; }).join('')
        + '<div class="cap">지나는 신호(닿을 때의 예상 — 계획값)</div>' + r.sigs.map(function (g) { var s = g.s; return '<div class="st"><i>🚦</i><b>' + km(g.d) + '</b><span>' + esc(g.nm) + ' · ' + (g.mv === 'Rt' ? '우회전' : g.mv === 'Lt' ? '좌회전' : g.mv === 'U' ? '유턴' : '직진') + ' — ' + (g.mv === 'Rt' || g.mv === 'U' ? '신호 자료 없음(우회전·유턴)' : !s ? '<em>모름</em>(자료 없음 · 보통 값 ' + Math.round(SIG.typ) + '초로 셈)' : s.kind === 'avg' ? '<em>지금 색 모름</em> · 평균 기다림 ' + Math.round(s.wait) + '초' : s.green ? '<b class="g">녹색</b> 통과 예상' : '<b class="r">적색</b> ' + Math.round(s.wait) + '초 기다림 예상') + '</span></div>'; }).join('') + '</details></div>'; }
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
    if (ks.length === 1) { drag = { x: e.offsetX, y: e.offsetY, cx: view.cx, cy: view.cy, moved: 0 }; lpAt = [e.offsetX, e.offsetY]; clearTimeout(lpT); lpT = setTimeout(function () { if (drag && drag.moved < 8 && lpAt) pick(lpAt[0], lpAt[1]); }, 550); }
    else if (ks.length === 2) { clearTimeout(lpT); var a = ptrs[ks[0]], b = ptrs[ks[1]]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]) || 1, s: view.s }; drag = null; } });
  cv.addEventListener('pointermove', function (e) { if (!ptrs[e.pointerId]) return; ptrs[e.pointerId] = [e.offsetX, e.offsetY]; var ks = Object.keys(ptrs);
    if (pinch && ks.length >= 2) { var a = ptrs[ks[0]], b = ptrs[ks[1]]; view.s = Math.max(0.03, Math.min(4, pinch.s * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch.d)); drawSoon(); return; }
    if (drag) { var dx = e.offsetX - drag.x, dy = e.offsetY - drag.y; drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy)); if (drag.moved > 8) { clearTimeout(lpT); follow = false; $('gCen').classList.add('off'); var c = Math.cos(view.rot * Math.PI / 180), s = Math.sin(view.rot * Math.PI / 180); view.cx = drag.cx - (dx * c - dy * s) / view.s; view.cy = drag.cy - (dx * s + dy * c) / view.s; drawSoon(); } } });
  function up(e) { delete ptrs[e.pointerId]; clearTimeout(lpT); if (Object.keys(ptrs).length < 2) pinch = null; if (!Object.keys(ptrs).length) drag = null; }
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', up);
  cv.addEventListener('wheel', function (e) { e.preventDefault(); view.s = Math.max(0.03, Math.min(4, view.s * (e.deltaY < 0 ? 1.2 : 1 / 1.2))); drawSoon(); }, { passive: false });
  cv.addEventListener('contextmenu', function (e) { e.preventDefault(); pick(e.offsetX, e.offsetY); });
  /* 길게 누름 → 여기로 / 여기서 */
  function pick(px, py) { if (!G || guide) return; var w = S2W(px, py), ns = nearSeg(w[0], w[1], 250), el = $('gPick'); if (!ns) { note('여기는 길에서 멀다'); return; }
    var nm = G.S[ns.seg][5] >= 0 ? G.j.names[G.S[ns.seg][5]] : '이름 없는 길'; el.style.display = 'flex'; el.style.left = Math.max(8, Math.min(cv.clientWidth - 228, px - 110)) + 'px'; el.style.top = Math.max(70, py - 64) + 'px';
    el.innerHTML = '<b>' + esc(nm) + '</b><button data-p="to">여기로 안내</button><button data-p="from">여기서 떠나기</button><button data-p="x">닫기</button>'; el._w = [ns.x, ns.y, nm]; }
  $('gPick').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var w = this._w, k = b.getAttribute('data-p'); this.style.display = 'none'; if (k === 'to') setDest(w[0], w[1], w[2]); else if (k === 'from') { if (watchId != null) { navigator.geolocation.clearWatch(watchId); watchId = null; } sim = null; setMe(w[0], w[1], 5, null, 0); note('떠나는 곳을 손으로 정했다 — 실제 위치로 돌아가려면 ◎ 를 누른다'); } });
  function setDest(x, y, nm) { dest = { x: x, y: y, nm: nm || '목적지' }; route = null; if (!me) gpsStart(); if (me) plan(); else { paint(); draw(); } }
  document.addEventListener('click', function (e) { var t = e.target.closest('button'); if (!t) return; var id = t.id;
    if (id === 'gGo') { voiceAsk(); guideStart(); } else if (id === 'gSim') simStart(); else if (id === 'gClr') { route = null; dest = null; note(''); paint(); draw(); } else if (id === 'gStop') guideStop(false);
    else if (id === 'gCen') { follow = true; t.classList.remove('off'); if (watchId == null && !sim) gpsStart(); if (me) { view.cx = me.x; view.cy = me.y; if (guide) view.rot = me.hd; else if (view.s < 0.5) view.s = 0.9; } draw(); }
    else if (id === 'gVoice') { voiceOn = !voiceOn; t.classList.toggle('on', voiceOn); if (voiceOn) say('음성 안내를 켭니다'); else if (window.speechSynthesis) speechSynthesis.cancel(); }
    else if (id === 'gIn') { view.s = Math.min(4, view.s * 1.4); draw(); } else if (id === 'gOut') { view.s = Math.max(0.03, view.s / 1.4); draw(); }
    else if (t.hasAttribute('data-mode')) { MODE = t.getAttribute('data-mode'); if (dest && me) plan(); }
    else if (id === 'gDark') { document.documentElement.classList.toggle('dark'); try { localStorage.setItem('tg_gargo_dark', document.documentElement.classList.contains('dark') ? '1' : '0'); } catch (x) {} draw(); }
    else if (id === 'gOk') { $('gIntro').style.display = 'none'; try { localStorage.setItem('tg_gargo_intro', '1'); } catch (x) {} gpsStart(); } });
  function voiceAsk() { if (!window.speechSynthesis) return; voiceOn = true; $('gVoice').classList.add('on'); }
  /* 이름으로 찾기 — 신호 교차로 이름 · 길 이름(이 묶음 안) */
  var fi = $('gQ'), fl = $('gList');
  fi.addEventListener('input', function () { var q = fi.value.replace(/\s+/g, ''); if (!G || q.length < 2) { fl.style.display = 'none'; return; } var out = [];
    G.sig.forEach(function (s) { if (s.nm.replace(/\s+/g, '').indexOf(q) >= 0) out.push(['🚦', s.nm, s.x, s.y]); });
    var seen = {}; G.LAB.forEach(function (L) { if (out.length > 30 || seen[L.n] || L.n.replace(/\s+/g, '').indexOf(q) < 0) return; seen[L.n] = 1; out.push(['🛣', L.n, L.x, L.y]); });
    fl.innerHTML = out.slice(0, 14).map(function (o, i) { return '<button data-i="' + i + '">' + o[0] + ' ' + esc(o[1]) + '</button>'; }).join('') || '<div class="no">서초구 둘레의 신호 교차로·큰길 이름만 찾는다 — 그 밖은 지도를 길게 누른다</div>'; fl._o = out; fl.style.display = 'block'; });
  fl.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var o = fl._o[+b.getAttribute('data-i')]; fl.style.display = 'none'; fi.value = o[1]; fi.blur(); var ns = nearSeg(o[2], o[3], 300); setDest(ns ? ns.x : o[2], ns ? ns.y : o[3], o[1]); view.cx = o[2]; view.cy = o[3]; if (view.s < 0.4) view.s = 0.6; follow = false; draw(); });
  /* 주소로 받은 목적지 — #to=위도,경도&nm=이름 · #from=위도,경도(시험) · 주소에서 지운다(좌표가 남지 않게) */
  function hashGo() { var H = location.hash || '', t = /[#&]to=(-?[\d.]+),(-?[\d.]+)/.exec(H), f = /[#&]from=(-?[\d.]+),(-?[\d.]+)/.exec(H), n = /[#&]nm=([^&]*)/.exec(H);
    if (f) setMe(PX(+f[2]), PY(+f[1]), 5, null, 0); if (t) { var x = PX(+t[2]), y = PY(+t[1]), ns = nearSeg(x, y, 600); if (ns) setDest(ns.x, ns.y, n ? decodeURIComponent(n[1]) : '받은 자리'); else note('받은 자리가 서초구 둘레 밖이다 — 시험판은 서초구와 둘레 2km 안에서만 된다'); }
    if (t || f) { try { history.replaceState(null, '', location.pathname); } catch (e) {} } }
  setInterval(function () { if (route && (guide || sim)) { paint(); draw(); } else if (route) draw(); }, 1000);
  setInterval(function () { if (G && !document.hidden) liveLoad().then(function () { if (dest && me && !guide) plan(); }); }, 300000);
  window.addEventListener('resize', function () { draw(); });
  document.addEventListener('visibilitychange', function () { if (!document.hidden && guide && navigator.wakeLock) { try { navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) {} } });
  try { if (localStorage.getItem('tg_gargo_dark') === '1') document.documentElement.classList.add('dark'); } catch (e) {}
  function boot() { if (document.documentElement.classList.contains('gated')) return; var seen = false; try { seen = localStorage.getItem('tg_gargo_intro') === '1'; } catch (e) {} if (seen) { $('gIntro').style.display = 'none'; if (!/[#&]from=/.test(location.hash)) gpsStart(); } load(); }
  window.addEventListener('tggate', boot); boot();
  window.GARGO = { view: view, state: function () { return { me: me, dest: dest, route: route, guide: guide, sig: SIG, G: G }; }, sigAt: sigAt, plan: plan, setDest: setDest, setMe: setMe, draw: draw, P: function (lon, lat) { return [PX(lon), PY(lat)]; }, findRoute: findRoute, simStart: simStart, guideStart: guideStart };
})();
