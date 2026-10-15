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
  var LIVE = { m: null, at: 0 }, MODE = 'n', CF = (window.TT ? TT.cfg() : { fwd: 1000, back: 500, sz: 1, fz: 1 }), VIPB = 0, VIPF = null, GSTART = null;   /* v0.11.0 CF = 설정(../js/travel-time.js · 이 기기) · VIPB/VIPF = 중요업무 기본·직접 속도(메모리에만) */
  function NOSIG() { return MODE === 'e' || MODE === 'v'; }   /* LIVE = 통행속도 한 장(약 11분마다 · 20분 넘으면 안 쓴다) · MODE n 일반(신호를 지킨다) · e 긴급 출동(길 계산에서 신호 기다림을 뺀다) */
  var view = { cx: 0, cy: 0, s: 0.25, rot: 0 }, me = null, dest = null, route = null, guide = false, follow = true, voiceOn = false, sim = null, lastSay = {};
  var DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw'], DIRKO = { nt: '북', ne: '북동', et: '동', se: '남동', st: '남', sw: '남서', wt: '서', nw: '북서' };

  /* ---------- 자료 ---------- */
  function getJ(u) { return fetch(u).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
  function load() {
    msg('길 자료를 읽는 중…');
    /* v0.7.0 — 소유자 2026-10-14 「서초·강남·송파·동작·관악·용산」 여섯 구 묶음(마디 81,049 · 신호 680 · 9.5MB/전송 2.6MB) · 못 읽으면 서초 묶음 */
    /* v0.8.0 — 칸 묶음(pk-<PKA>/core.json)이 있으면 큰길만 먼저 · 없으면 종전 한 장 */
    return getJ('pk-' + PKA + '/core.json').then(function (c) { if (c && c.segs && c.tiles && c.cell) { PK = c; return pkMerge(); } return getJ('pack-six.json').then(function (j) { if (j && j.seg) return j; AREA_KO = '서초구'; return getJ('pack-seocho.json'); }); }).then(function (j) { if (!j || !j.seg) { msg('길 자료를 읽지 못했다 — 새로 고쳐 본다'); return; } build(j); msg(''); fitAll(); draw(); hashGo(); sigLoad(); xsLoad(); baseLoad(); ['s', 't'].forEach(function (k) { var b = document.querySelector('[data-ov=' + k + ']'); if (b) b.classList.toggle('on', !!OV[k]); }); });
  }
  /* ---------- v0.8.0 칸 묶음 — 소유자 2026-10-14 「한강 이남이 완성되면 서울 전체로」 · 서울 한 장은 약 40MB 라 폰에 못 싣는다 ----------
     core = 등급 1~5 길 줄 · 칸 = 2km 골목 줄(tools/gargo/pack-tile.py) · 번호는 전체 번호 → 받은 것끼리 다시 매겨(pkMerge) 종전 build 로 */
  var PKF = {};   /* 받기에 실패한 칸 → 시각(30초 동안 다시 안 부른다 — 끊긴 곳에서 받기·다시 짓기를 끝없이 되풀이하지 않게) */
  var PKA = (/[?&]pk=(seoul|six)(?![a-z])/.exec(location.search) || [0, 'six'])[1], PK = null,   /* 범위 — 지금 여섯 구 · 이남이 차면 'seoul' · 시험은 주소 뒤 ?pk=seoul */
   PKT = {}, PKL = {}, PKRT = 0, PKW = false;
  function pkMerge() { var C = PK, nl = {}, nx = [], ny = [], seg = [], geo = [], sl = {}, turns = [], F = [C].concat(Object.keys(PKT).map(function (k) { return PKT[k]; }));
    F.forEach(function (f) { f.nodes.forEach(function (r) { if (nl[r[0]] == null) { nl[r[0]] = nx.length; nx.push(r[1]); ny.push(r[2]); } }); });
    /* v0.15.1 칸의 길 줄을 복사하지 않고 그대로 쓴다 — 받은 칸 줄을 한 번 「합친 꼴」로 바꿔 두고(앞 칸 = 길 줄 번호를 뒤 17~20 칸으로 · 원래 마디·모양 번호 보관) 합칠 때마다 0·1·8 칸만 고쳐 쓴다(종전 r.slice(1) 복사본이 칸 원본과 두 벌로 남았다) */
    F.forEach(function (f) { if (f._a) return; var n = f.segs.length, A = new Float64Array(n), B = new Float64Array(n), I = new Float64Array(n), Q = new Int32Array(n); f.segs.forEach(function (r, i) { I[i] = r.shift(); A[i] = r[0]; B[i] = r[1]; Q[i] = r[8]; }); f._a = A; f._b = B; f._id = I; f._g = Q; });   /* 덧붙일 값은 배열 뒤가 아니라 칸마다 숫자 배열에(배열을 늘리면 자리를 크게 다시 잡아 절약분을 먹었다) */
    F.forEach(function (f) { f.segs.forEach(function (r, i) { if (sl[f._id[i]] != null) return; var a = nl[f._a[i]], b = nl[f._b[i]]; if (a == null || b == null) return; r[0] = a; r[1] = b; if (f._g[i] >= 0) { geo.push(f.geo[f._g[i]]); r[8] = geo.length - 1; } else r[8] = f._g[i]; sl[f._id[i]] = seg.length; seg.push(r); }); });
    var tk = {}; F.forEach(function (f) { f.turns.forEach(function (t) { var v = nl[t[0]]; if (v == null) return; var k = t[0] + '|' + t[1] + '|' + t[2] + '|' + t[3]; if (tk[k]) return; tk[k] = 1; turns.push([v, t[1], t[2], t[3]]); }); });   /* v0.9.2 — t[1]·t[2] 는 길(way) 번호다(길 줄 번호가 아니다) — v0.8.0~0.9.1 은 길 줄 번호로 바꿔 회전 제한이 모두 무효였다(독립 검수) */
    var sig = C.sig.map(function (g) { return [g[0], g[1], g[2], g[3], g[4], g[5], g[6].map(function (n) { return nl[n]; }).filter(function (n) { return n != null; })]; });
    return { base: C.base, nx: nx, ny: ny, names: C.names, ways: C.ways, seg: seg, links: C.links, tl: C.tl, geo: geo, turns: turns, sig: sig, area: C.area, made: C.made }; }
  function pkKeys(pts, r) { if (!PK) return []; var c = PK.cell, out = {}; pts.forEach(function (q) { if (!q) return; for (var ix = Math.floor((q[0] - r) / c); ix <= Math.floor((q[0] + r) / c); ix++) for (var iz = Math.floor((q[1] - r) / c); iz <= Math.floor((q[1] + r) / c); iz++) { var k = ix + '_' + iz; if (PK.tiles[k] != null && !PKT[k] && !PKL[k] && !(PKF[k] && Date.now() - PKF[k] < 30000)) out[k] = 1; } }); return Object.keys(out); }
  var PKVIP = 0, PKVIPALL = false;
  function pkLoad(keys) { if (MODE === 'v' && !PKVIP) return Promise.resolve(0); var n = 0; keys.forEach(function (k) { PKL[k] = 1; }); return Promise.all(keys.map(function (k) { return getJ('pk-' + PKA + '/t/' + k + '.json' + (PK.bake ? '?b=' + PK.bake : '')).then(function (t) { delete PKL[k];
      if (t && t.segs && (!PK.bake || t.bake === PK.bake)) { PKT[k] = t; n++; } else PKF[k] = Date.now(); }); })).then(function () { return n; }); }   /* 구운 판(bake)이 core 와 다른 칸은 버린다(옛 칸이 새 core 와 섞이면 마디가 엉뚱하게 이어진다) */
  /* 다시 짓기 — 길 번호가 바뀌므로 길이 있으면 다시 찾는다(안내 중에는 plan 이 부를 때만) · 칸이 80 넘게 쌓이면 지금 자리·화면에서 먼 칸부터 비운다 */
  function pkRebuild(noPlan, keepAll, keep) { if (!PK) return; var ks = Object.keys(PKT); if (!keepAll && !PKALL && MODE !== 'v' && !route && !guide && ks.length > 80) { var cx = cruise && me ? me.x : view.cx, cy = cruise && me ? me.y : view.cy, c = PK.cell, kp = {}; (keep || []).forEach(function (k) { kp[k] = 1; }); pkVis().forEach(function (k) { kp[k] = 1; });
      ks.filter(function (k) { return !kp[k]; }).map(function (k) { var a = k.split('_'); return [k, Math.hypot((+a[0] + 0.5) * c - cx, (+a[1] + 0.5) * c - cy)]; }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, ks.length - 60).forEach(function (x) { delete PKT[x[0]]; }); }
    build(pkMerge()); TRAF = null; SSTAT = null; CRA = null; liveStat(); if (XSJ) xsBuild(XSJ); else xsLoad(); if (!noPlan && route && dest && me) plan(true); paint(); draw(); }
  function pkVis() { if (!PK || !cv) return []; var W = cv.clientWidth, H = cv.clientHeight, a = S2W(0, 0), b = S2W(W, H), c = S2W(W, 0), d = S2W(0, H), x0 = Math.min(a[0], b[0], c[0], d[0]), x1 = Math.max(a[0], b[0], c[0], d[0]), y0 = Math.min(a[1], b[1], c[1], d[1]), y1 = Math.max(a[1], b[1], c[1], d[1]), out = [], C = PK.cell;
    for (var ix = Math.floor(x0 / C); ix <= Math.floor(x1 / C); ix++) for (var iz = Math.floor(y0 / C); iz <= Math.floor(y1 / C); iz++) out.push(ix + '_' + iz); return out; }
  var PKALL = 0;   /* v0.11.0 칸을 모두 받는 중(pkAll)에는 비우지 않는다 — 미뤄 둔 다시 짓기가 끼어들어 받은 칸을 지우던 경합 */
  function pkSoon(n) { if (n === 0) return; clearTimeout(PKRT); PKRT = setTimeout(function () { pkRebuild(); }, 500); }   /* 늘어난 칸이 없으면 다시 짓지 않는다 */
  function pkEnsure(pts, r) { var m = pkKeys(pts, r || 2200); if (!m.length) return Promise.resolve(false); return pkLoad(m).then(function (n) { if (n) pkRebuild(true, false, m); return n > 0; }); }
  function build(j) {
    var n = j.nx.length, X = new Float32Array(n), Y = new Float32Array(n), bx = j.base[0], by = j.base[1], i;
    for (i = 0; i < n; i++) { X[i] = PX((bx + j.nx[i]) / 1e6); Y[i] = PY((by + j.ny[i]) / 1e6); }
    var S = j.seg, ns = S.length, SP = new Array(ns), ne = 0, tot = 0, off = 0;
    for (i = 0; i < ns; i++) { var g0 = S[i][8] >= 0 ? j.geo[S[i][8]] : null; tot += ((g0 ? g0.length / 2 : 0) + 2) * 2; }
    var BIG = new Float32Array(tot);   /* v0.14.3 길 모양을 한 덩어리에 — 길 줄마다 따로 만들던 배열(서울 26만 줄 · 약 39MB)을 한 버퍼의 조각(subarray)으로 */
    for (i = 0; i < ns; i++) { var s = S[i], a = s[0], b = s[1], g = s[8] >= 0 ? j.geo[s[8]] : null, m = g ? g.length / 2 : 0, P = BIG.subarray(off, off + (m + 2) * 2); off += (m + 2) * 2;
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
    if (all.length < 30) return; LIVER = { all: med(all) }; Object.keys(by).forEach(function (c) { if (by[c].length >= 20) LIVER[c] = med(by[c]); }); liveFill(); }
  /* v0.14.2 이웃 메움 — 실시간 값이 없는 줄(이름 있는 길 · 등급 5 까지)은 같은 이름으로 곧게(45° 안) 이어지는 앞뒤 줄을 700m·여섯 걸음까지 따라가 처음 만난 실시간 값을 거리 반비례로 쓴다 · 없으면 종전대로 등급 비율 */
  var FILL = null;
  function liveFill() { FILL = null; if (!LIVE.m || !G) return; var ne = G.ne, F = new Float32Array(ne), inH, inL, i, e;
    var cnt = new Int32Array(G.n + 1); for (e = 0; e < ne; e++) cnt[G.eB[e] + 1]++; for (i = 0; i < G.n; i++) cnt[i + 1] += cnt[i]; inH = cnt.slice(); inL = new Int32Array(ne); var pos = cnt.slice(); for (e = 0; e < ne; e++) inL[pos[G.eB[e]]++] = e;
    function nmOf(x) { return G.S[G.eS[x]][5]; }
    function walk(e0, fwd) { var cur = e0, d = eLen(e0) * 0.5, nm = nmOf(e0); for (var k = 0; k < 6; k++) {   /* d = 메울 줄 가운데에서 잰 거리 — 긴 줄(우면산터널 1,964m)은 첫 걸음에 벌써 700m 를 넘어 메우지 않는다 */ var best = -1, ba = 46, a0, a1, j;
        if (fwd) { a0 = G.oHead[G.eB[cur]]; a1 = G.oHead[G.eB[cur] + 1]; } else { a0 = inH[G.eA[cur]]; a1 = inH[G.eA[cur] + 1]; }
        for (j = a0; j < a1; j++) { var f = fwd ? G.oList[j] : inL[j]; if (G.eS[f] === G.eS[cur] || nmOf(f) !== nm) continue; var ad = Math.abs(fwd ? angDiff(eBrgIn(cur), eBrgOut(f)) : angDiff(eBrgIn(f), eBrgOut(cur))); if (ad < ba) { ba = ad; best = f; } }
        if (best < 0 || d > 700) return null; var v = eLive(best); if (v) return [v, d + eLen(best) * 0.5]; d += eLen(best); cur = best; } return null; }
    for (e = 0; e < ne; e++) { var q = G.S[G.eS[e]]; if (q[5] == null || q[5] < 0 || q[4] > 5 || eLive(e)) continue; var A = walk(e, true), B = walk(e, false); if (!A && !B) continue; var w1 = A ? 1 / Math.max(50, A[1]) : 0, w2 = B ? 1 / Math.max(50, B[1]) : 0; F[e] = ((A ? A[0] * w1 : 0) + (B ? B[0] * w2 : 0)) / (w1 + w2); }
    FILL = F; }
  var AREA_KO = /[?&]pk=seoul(?![a-z])/.test(location.search) ? '서울 25구' : '서초·강남·송파·동작·관악·용산';
  function liveFresh(x) { return !!(x && x.m && x.at && Date.now() / 1000 - x.at < 1200); }
  function liveLoad() { return getJ('../data/live-spd-six.json').then(function (j) { return liveFresh(j) ? j : getJ('../data/live-spd-seocho.json').then(function (k) { return liveFresh(k) ? k : (j && j.m ? j : k); }); }).then(function (j) { var ok = j && j.m && j.at && Date.now() / 1000 - j.at < 1200; LIVE = ok ? { m: j.m, at: j.at, made: j.made } : { m: null, at: j && j.at || 0 }; liveStat(); }); }
  function sigLoad() { accLoad(); getJ('../data/eta-cal.json').then(function (j) { if (window.TT && TT.calTab) { TT.calTab(j); GCF.t = 0; } }); liveLoad().then(function () { if (dest && me && !guide) plan(); else paint(); }); getJ('../data/sig-special.json').then(function (j) { if (j && j.days) SIG.hol = j.days; });
    return getJ('../data/sigdir/index.json').then(function (j) { if (!j || !j.fl) { note('신호 자료를 읽지 못했다 — 길 안내는 제한속도 기준으로만 한다'); return; } SIG.idx = j; SIG.pl = j.pl || {}; SIG.cell = j.cell; var need = {};
      G.sig.forEach(function (s) { if (j.fl[s.no] == null) return; var q = j.pts[s.no]; if (q) need[Math.floor(q[0] / j.cell[0]) + '_' + Math.floor(q[1] / j.cell[1])] = 1; });
      return Promise.all(Object.keys(need).map(function (k) { return getJ('../data/sigdir/c/' + k + '.json').then(function (c) { if (c && c.its) Object.keys(c.its).forEach(function (no) { SIG.its[no] = c.its[no]; }); }); })).then(function () {
        var v = []; Object.keys(SIG.its).forEach(function (no) { SIG.its[no].forEach(function (r) { if (!recOk(r)) return; var C = r.ci || r.cyc; if (!C) return; r.mv.forEach(function (m) { if (m[1] === 'St' && m[2] != null && m[2] < C) v.push((C - m[2]) * (C - m[2]) / (2 * C)); }); }); });
        v.sort(function (a, b) { return a - b; }); if (v.length) SIG.typ = v[v.length >> 1]; SIG.ready = 1; SIG.at = Date.now(); if (dest && me) plan(); draw(); paint(); }); });
  }
  /* v0.5.0 값 없는 신호 — 서울 모든 신호 교차로(T-GIS · data/tgis-seoul.json) 가운데 신호값을 못 받은 곳. 길 마디에 붙여 두고 「신호가 있다」고만 친다(기다림은 받은 값의 가운데값에 견준 어림).
     종전에는 값 있는 189곳만 신호로 쳐서, 그 신호를 피하려고 값 없는 신호가 줄지어 선 길이나 골목으로 돌았다 */
  var XS = [];
  var XSJ = null, XSP = null;
  function xsLoad() { if (!XSP) XSP = getJ('../data/tgis-seoul.json').then(function (j) { if (j && j.items) XSJ = j; else XSP = null; return j; }); return XSP.then(function (j) { if (!j || !j.items || !G) return; xsBuild(j); if (dest && me && !guide) plan(); else draw(); }); }
  function xsBuild(j) { if (!j || !j.items || !G) return; var C = 60, ng = {}, i, k; for (i = 0; i < G.n; i++) { k = Math.floor(G.X[i] / C) + ',' + Math.floor(G.Y[i] / C); (ng[k] || (ng[k] = [])).push(i); }
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
      XS = list; G.nxs = nxs; G.XS = list; }
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
  /* v0.12.0 막힘 배율 — 실시간 소통이 하나도 없을 때 제한속도 ÷ f(ITS 실측 · ../data/eta-cal.json · 요일 갈래 × 시간대 · 1분마다) · 신호 기다림은 따로 셈 · ⚙ 에서 끔 */
  var GCF = { t: 0, f: 1 };
  function gCalF() { var n = Date.now(); if (n - GCF.t > 60000) GCF = { t: n, f: window.TT && TT.calF ? TT.calF(n) : 1 }; return GCF.f; }
  /* 시간 셈에만 — 이웃 메움(FILL)을 쓴다 · 길 고르기(eV·eCost)에는 안 쓴다(막힘을 너무 멀리 퍼뜨려 고속터미널 → 방배역이 2.5배 돌았다 · 관문 「에움」) */
  function eVt(e) { var v = eLive(e), k = accK(e), base; if (!v && !lrnSpeed(e) && FILL && FILL[e] > 0) base = Math.max(4, Math.min(eSpd(e), FILL[e])); else base = eV(e); return Math.max(3, base / (k > 1 ? Math.min(k, 5) : 1)); }   /* 공사·통제는 시간도(차로 ×1.5 · 전면 ×5) */
  function eV(e) { var lim = eSpd(e), v = eLive(e); if (v) return Math.max(4, Math.min(lim, v)); var lv8 = lrnSpeed(e); if (lv8) return Math.max(3, Math.min(lim, lv8)); if (LIVER) {   /* v0.23.0 다녀 본 길 — 실시간 다음 */ var k = LIVER[G.S[G.eS[e]][4]]; return Math.max(4, lim * (k != null ? k : LIVER.all)); } return Math.max(4, lim / gCalF()); }
  /* 길 고르기에만 쓰는 무게(가정 — 시간 표시에는 안 넣는다): 골목(등급 6)은 2배 · 생활도로·진입로(7·8)는 3배 느리게 치고, 신호 없는 곳에서 꺾으면 좌 15초·우 6초를 얹는다.
     넣지 않으면 신호 한두 개를 피하려고 골목을 지그재그로 도는 길이 나온다(시험: 서초역 → 양재역이 열다섯 번 꺾였다) */
  /* ---------- v0.23.0 다녀 본 길 기억(이 기기 tg_gg_learn) ---------- */
  var LRN = null, LRNE = null, LRNB = '', LRNG = null, LT = null, LKEY = 'tg_gg_learn';
  var LRNON = null, LRNT = 0;
  function lrnOn() { if (LRNON === null) { try { LRNON = localStorage.getItem('tg_gargo_lrnoff') !== '1'; } catch (e) { LRNON = false; } } return LRNON; }   /* 길 고르기 안쪽에서 아주 자주 불린다 — 한 번 읽어 둔다 */
  function lrnLoad() { if (LRN) return LRN; try { LRN = JSON.parse(localStorage.getItem(LKEY) || 'null'); } catch (e) { LRN = null; } if (!LRN || !LRN.e || typeof LRN.e !== 'object' || Array.isArray(LRN.e)) LRN = { v: 1, e: {} }; Object.keys(LRN.e).forEach(function (k) { var o = LRN.e[k]; if (!o || typeof o !== 'object') { delete LRN.e[k]; return; } Object.keys(o).forEach(function (b) { if (!Array.isArray(o[b])) delete o[b]; else o[b] = o[b].filter(function (x) { return Array.isArray(x) && x[0] > 0; }); }); }); return LRN; }   /* 깨진 저장값이 길 계산을 멈추지 않게 */
  function lrnSave() { try { localStorage.setItem(LKEY, JSON.stringify(LRN)); } catch (e) { var ks = Object.keys(LRN.e); ks.slice(0, ks.length >> 2).forEach(function (k) { delete LRN.e[k]; }); try { localStorage.setItem(LKEY, JSON.stringify(LRN)); } catch (x) {} } }
  function lrnBucket(ms) { var d = new Date(ms), w = d.getDay(), h = d.getHours(); return (w === 0 || (window.TT && TT.isHol && TT.isHol(ms)) ? 'h' : w === 6 ? 's' : 'w') + (h >= 7 && h < 10 ? 'a' : h >= 10 && h < 17 ? 'd' : h >= 17 && h < 20 ? 'p' : h >= 20 && h < 23 ? 'n' : 'z'); }
  function eKey(e) { var a = G.eA[e], b = G.eB[e]; return Math.round(G.X[a]) + ',' + Math.round(G.Y[a]) + '>' + Math.round(G.X[b]) + ',' + Math.round(G.Y[b]); }
  var LDIRTY = 0, LSAVET = 0;
  function lrnAdd(e, sec, ms) { lrnLoad(); var k = eKey(e), b = lrnBucket(ms || Date.now()), o = LRN.e[k] || {}, A = o[b] || (o[b] = []); delete LRN.e[k]; LRN.e[k] = o; A.push([Math.round(sec * 10) / 10, Math.floor((ms || Date.now()) / 864e5)]); if (A.length > 6) A.shift();
    var ks = Object.keys(LRN.e); if (ks.length > 4000) delete LRN.e[ks[0]]; LDIRTY = 1; if (Date.now() - LSAVET > 45000) lrnFlush();
    if (LRNE && LRNG === G) { var sp = lrnPick(o, LRNB, Math.floor(Date.now() / 864e5)); LRNE[e] = sp > 0 ? lrnClamp(e, eLen(e) / sp * 3.6) : 0; } }
  function lrnFlush() { if (!LDIRTY || !LRN) return; LDIRTY = 0; LSAVET = Date.now(); lrnSave(); }   /* 45초마다 · 안내 끝 · 화면을 떠날 때 */
  function lrnClamp(e, v) { var lim = eSpd(e); return v >= Math.max(3, lim * 0.25) && v <= 130 ? v : 0; }   /* 제한속도의 25% 밑(줄 하나 내내 섰던 값 등)은 안 쓴다 */
  function lrnPick(o, b, today) { var A = o[b], all = []; if (!A || A.length < 2) { Object.keys(o).forEach(function (k) { all = all.concat(o[k]); }); if (all.length < 4) return null; A = all; } var rec = A.filter(function (x) { return today - x[1] <= 60; }); if (rec.length >= 2) A = rec; var v = A.map(function (x) { return x[0]; }).sort(function (p, q) { return p - q; }); return v.length === 2 ? v[0] : v[v.length >> 1]; }   /* 표본 둘이면 빠른 쪽(느린 이상치 하나가 그대로 쓰이지 않게) */
  function lrnBuild() { LRNB = lrnBucket(Date.now()); LRNG = G; LRNE = new Float32Array(G.ne); lrnLoad(); var ks = Object.keys(LRN.e); if (!ks.length) return; var nm = {}, i, today = Math.floor(Date.now() / 864e5);
    for (i = 0; i < G.n; i++) nm[Math.round(G.X[i]) + ',' + Math.round(G.Y[i])] = i;
    ks.forEach(function (k) { var p = k.split('>'), a = nm[p[0]], b = nm[p[1]]; if (a == null || b == null) return; var sec = lrnPick(LRN.e[k], LRNB, today); if (!(sec > 0)) return;
      for (var j = G.oHead[a]; j < G.oHead[a + 1]; j++) { var e = G.oList[j]; if (G.eB[e] === b) { var v = lrnClamp(e, eLen(e) / sec * 3.6); if (v) LRNE[e] = v; } } }); }
  function lrnSpeed(e) { if (!G || !lrnOn()) return 0; if (LRNE && LRNG === G) { var n = Date.now(); if (n - LRNT < 60000) return LRNE[e] || 0; LRNT = n; if (LRNB === lrnBucket(n)) return LRNE[e] || 0; } try { lrnBuild(); } catch (x) { LRNE = new Float32Array(G.ne); LRNG = G; } LRNT = Date.now(); return LRNE[e] || 0; }
  function lrnPurge(x, y) { try { lrnLoad(); var n0 = Object.keys(LRN.e).length; Object.keys(LRN.e).forEach(function (k) { var p = k.split(/[>,]/).map(Number); if (Math.hypot(p[0] - x, p[1] - y) < 300 || Math.hypot(p[2] - x, p[3] - y) < 300) delete LRN.e[k]; }); if (Object.keys(LRN.e).length !== n0) { lrnSave(); LRNE = null; } } catch (e) {} }   /* 중요업무 목적지 300m 안 */
  function lrnCount() { return LRN ? Object.keys(LRN.e).length : (lrnLoad(), Object.keys(LRN.e).length); }
  /* 길 줄에 맞대기 — 25m 안 · 진행 방위 60° 안 · 줄을 20% 안에서 들어와 80% 넘게 지나 다음 줄로 이어지면 한 번 */
  function lrnTrack() { if (!G || !me || sim || MODE !== 'n' || (dest && dest.vip) || !lrnOn()) { LT = null; return; }   /* 일반 모드만(긴급 출동·중요업무·모의 주행 아님) */
    if (LT && LT.g !== G) LT = null;   /* 길 묶음을 다시 지으면 줄 번호가 바뀐다 */
    if (!me.hk || !(me.spd > 1)) { if (LT) LT.tl = Date.now(); return; }   /* 신호·정체로 서 있어도 그 줄의 시간은 이어 센다 */
    var C = nearSegs(me.x, me.y, 25, 8), pick = null, onR = route && guide ? {} : null; if (onR) route.es.forEach(function (x) { onR[G.eS[x]] = 1; }); if (onR) C.sort(function (p, q) { return (onR[q.seg] ? 1 : 0) - (onR[p.seg] ? 1 : 0) || p.d - q.d; });   /* 안내 중이면 지금 길 위 줄 먼저(고가·밑길) */
    for (var i = 0; i < C.length && !pick; i++) { var c = C[i], d = Math.abs(angDiff(me.hd, c.brg)), dir = d < 60 ? 0 : d > 120 ? 1 : -1; if (dir < 0) continue;
      var s0 = G.S[c.seg], nd = dir ? s0[1] : s0[0], e = -1; for (var j = G.oHead[nd]; j < G.oHead[nd + 1]; j++) if (G.eS[G.oList[j]] === c.seg && G.eR[G.oList[j]] === dir) { e = G.oList[j]; break; } if (e < 0) continue;
      var p = G.SP[c.seg], al = 0, tot = 0; for (var u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < c.u) al += l; else if (u === c.u) al += l * c.t; tot += l; } var fr = tot ? al / tot : 0; pick = { e: e, f: dir ? 1 - fr : fr }; }
    var now = Date.now(); if (!pick) { LT = null; return; }
    if (LT && LT.e === pick.e) { LT.last = pick.f; LT.tl = now; return; }
    if (LT && LT.fin <= 0.2 && LT.last >= 0.8 && G.eB[LT.e] === G.eA[pick.e] && G.eS[LT.e] !== G.eS[pick.e] && eLen(LT.e) >= 40) { var sec = (LT.tl - LT.tin) / 1000 / Math.max(0.6, LT.last - LT.fin); if (sec > 0.5 && eLen(LT.e) / sec * 3.6 <= 130 && eLen(LT.e) / sec * 3.6 >= 2) lrnAdd(LT.e, sec, now); }
    LT = { e: pick.e, tin: now, tl: now, fin: pick.f, last: pick.f, g: G }; }
  /* v0.22.0 공사·통제(../data/live-acc-seoul.json · 서울 열린데이터 TOPIS 돌발 · 큰길만) — ITS 링크 ID → {nm, full, txt} · 지금 시각 안인 것만 */
  var ACC = null, ACCAT = 0;
  function accLoad() { return getJ('../data/live-acc-seoul.json').then(function (j) { if (!j || !j.items) return; var n = new Date(), ts = n.getFullYear() * 1e8 + (n.getMonth() + 1) * 1e6 + n.getDate() * 1e4 + n.getHours() * 100 + n.getMinutes(), A = {};
      j.items.forEach(function (q) { if (!(+q[7] <= ts && ts <= +q[8])) return; var tx = String(q[9] || ''), o = { nm: q[2] || '돌발', full: /전면\s*통제|전면통제/.test(tx), both: /양방향/.test(tx), txt: tx.split(/[\r\n]/)[0].replace(/\s+/g, ' ').trim().slice(0, 40) }; A[q[4]] = o; }); ACC = A; ACCAT = Date.now(); if (route) { route.mk = null; } }); }
  function accOf(e) { if (!ACC || !G) return null; var q = G.S[G.eS[e]], a = q[G.eR[e] ? 14 : 13], b = q[G.eR[e] ? 13 : 14], A = a != null && a >= 0 ? ACC[G.j.links[a]] : null; if (A) return A; var B = b != null && b >= 0 ? ACC[G.j.links[b]] : null; return B && B.both ? B : null; }
  function accK(e) { var a = accOf(e); return !a ? 1 : a.full ? 50 : 1.5; }
  function eCost(e) { var c = G.S[G.eS[e]][4]; return eLen(e) / (eV(e) / 3.6) * (c >= 7 ? 3 : c === 6 ? 2 : 1) * accK(e); }   /* v0.5.0 골목 1.7→2 · 생활도로·진입로 2.2→3(가정) */
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
    function cands(x, y, maxD, n0, mix) { var s0 = G.S[n0.seg]; var out = nearSegs(x, y, maxD, 24).filter(function (o) { if (o.seg === n0.seg) return true; var q = G.S[o.seg]; if (o.d > Math.max(n0.d, 40)) return false; if (q[0] === s0[0] || q[0] === s0[1] || q[1] === s0[0] || q[1] === s0[1]) return false; if (!mix && (q[4] <= 2) !== (s0[4] <= 2)) return false; var dd = Math.abs(angDiff(o.brg, n0.brg)); if (dd > 90) dd = 180 - dd; return dd <= 30; }); return out.length ? out : [n0]; }
    function along(a) { var p = G.SP[a.seg], al = 0, tot = 0, u; for (u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < a.u) al += l; else if (u === a.u) al += l * a.t; tot += l; } return tot ? al / tot : 0; }
    /* 떠나는 자리 — 가장 가까운 길과, 그보다 24m 안으로 더 먼 나란한 길들(고가 밑·맞은편 차로). 더 먼 길은 1m 에 1초씩 불리하게 · 달리는 중이면 진행 방향과 반대인 쪽에 30초 */
    cands(sx, sy, 400, a0).forEach(function (a) { var fr = along(a); edgesOf(a.seg).forEach(function (se) { var frac = G.eR[se] ? fr : 1 - fr, c = eLen(se) * frac / (eV(se) / 3.6) + (a.d - a0.d) * 1; if (sbrg != null) { var eb = G.eR[se] ? (a.brg + 180) % 360 : a.brg; if (Math.abs(angDiff(sbrg, eb)) > 110) c += 30; } if (c < D[se]) { D[se] = c; heapPush(h, c, se); SA[a.seg] = a; } }); });
    /* 닿는 자리 — 같은 방식(더 먼 길은 1m 에 1초씩 불리하게) */
    /* v0.14.1 닿는 자리는 자동차전용·일반 길을 섞어 후보로 — 예술의전당 교차로 한가운데에서 우면산로(전용) 3m · 남부순환로 3m 인데 전용 길만 후보라 신사역 → 예술의전당이 양재IC 를 돌아 12.3km(카카오 5.5km · route-spot 대조 2026-10-15) · 떠나는 자리는 그대로(고가 위에서 밑길로 잘못 잡지 않게) */
    cands(tx, ty, 600, b0, true).forEach(function (b) { SB[b.seg] = b; edgesOf(b.seg).forEach(function (ge) { goal[ge] = (b.d - b0.d) * 1; }); });
    var end = -1, bestC = Infinity;
    while (h.length) { var top = heapPop(h), d = top[0]; e = top[1]; if (d > D[e]) continue; if (d >= bestC) break; if (goal[e] != null) { var tc = d + goal[e]; if (tc < bestC) { bestC = tc; end = e; } }
      var nd = G.eB[e], key = nd + '|' + eWay(e), bn = G.ban[key], on = G.only[key];
      for (i = G.oHead[nd]; i < G.oHead[nd + 1]; i++) { var f = G.oList[i], w2 = eWay(f); if ((bn && bn[w2]) || (on && !on[w2])) continue;
        var w = eCost(f); if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) w += 30; var sc = sigCost(e, f, T0 + d); if (sc && !NOSIG()) w += LIVER ? turnAdd(sc.mv) : sc.c; if (!sc || NOSIG()) w += turnPen(e, f);
        if (d + w < D[f]) { D[f] = d + w; PR[f] = e; heapPush(h, d + w, f); } } }
    if (end < 0) return null; var es = [end]; while (PR[es[es.length - 1]] >= 0) es.push(PR[es[es.length - 1]]); es.reverse();
    return shape(es, SA[G.eS[es[0]]] || a0, SB[G.eS[end]] || b0, T0); }
  /* 길 꼴 — 선 · 거리 · 꺾는 곳 · 지나는 신호 */
  function shape(es, a, b, T0) {
    var accs = [], kn = [], pts = [], cum = [0], mans = [], sigs = [], t = 0, dist = 0, i, k, liveLen = 0, cong = [], free = 0, tc = [[0, 0]];
    function add(x, y) { if (pts.length) { var d = Math.hypot(x - pts[pts.length - 2], y - pts[pts.length - 1]); if (d < 0.05) return; dist += d; cum.push(dist); } pts.push(x, y); }
    for (i = 0; i < es.length; i++) { var e = es[i], p = G.SP[G.eS[e]], n = p.length / 2, rev = G.eR[e], q = [];
      for (k = 0; k < n; k++) { var u = (rev ? n - 1 - k : k) * 2; q.push(p[u], p[u + 1]); }
      if (i === 0) { var cut = [a.x, a.y], st = false; for (k = 0; k < n - 1; k++) { var u0 = rev ? (n - 2 - k) * 2 : k * 2; if (!st && u0 === a.u) { st = true; cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } else if (st) cut.push(q[(k + 1) * 2], q[(k + 1) * 2 + 1]); } if (cut.length >= 4) q = cut; }
      if (i === es.length - 1) { var c2 = [], done = false; for (k = 0; k < q.length / 2 && !done; k++) { c2.push(q[k * 2], q[k * 2 + 1]); if (k + 1 < q.length / 2) { var ax = q[k * 2], ay = q[k * 2 + 1], bx = q[k * 2 + 2], by = q[k * 2 + 3], l2 = (bx - ax) * (bx - ax) + (by - ay) * (by - ay), tt = l2 ? ((b.x - ax) * (bx - ax) + (b.y - ay) * (by - ay)) / l2 : 0; if (tt >= 0 && tt <= 1 && Math.hypot(ax + (bx - ax) * tt - b.x, ay + (by - ay) * tt - b.y) < 3) { c2.push(b.x, b.y); done = true; } } } q = c2; }
      var d0 = dist; for (k = 0; k < q.length; k += 2) add(q[k], q[k + 1]);
      var len = dist - d0, spd = eSpd(e), lv = eLive(e); t += len / (eVt(e) / 3.6); var ak9 = accOf(e); if (ak9 && (!accs.length || accs[accs.length - 1][1] !== ak9.txt)) accs.push([d0, ak9.txt, ak9.full]); free += len / (spd / 3.6); tc.push([dist, t]); if (lv) { liveLen += len; var cl0 = spdLv(lv, G.S[G.eS[e]][4], spd); if (cl0) cong.push([d0, dist, cl0]); var kl = kn[kn.length - 1]; if (kl && d0 - kl[1] < 1) kl[1] = dist; else kn.push([d0, dist]); }
      if (i + 1 < es.length) { var f = es[i + 1], dA = angDiff(eBrgIn(e), eBrgOut(f)), tk = turnKind(dA), outs = G.oHead[G.eB[e] + 1] - G.oHead[G.eB[e]], nm = G.S[G.eS[f]][5] >= 0 ? G.j.names[G.S[G.eS[f]][5]] : '';
        if (G.eB[f] === G.eA[e] && G.eS[f] === G.eS[e]) { tk = 'U'; t += 30; }
        var sc = sigCost(e, f, T0 + t); if (sc) { var sg = sc.si >= 0 ? G.sig[sc.si] : { no: '', nm: XS[sc.xi - 1].nm, x: XS[sc.xi - 1].x, y: XS[sc.xi - 1].y }; sigs.push({ si: sc.si, no: sg.no, nm: sg.nm, x: sg.x, y: sg.y, d: dist, side: sc.side, mv: sc.mv, t: t, w: sc.w, s: sc.s, lim: spd, unk: sc.unk || 0, tw: NOSIG() ? 0 : LIVER ? turnAdd(sc.mv) : sc.w }); if (!NOSIG()) t += LIVER ? turnAdd(sc.mv) : sc.w; }
        var cn = G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '';   /* 같은 이름의 길에서 살짝 휘는 것(갈래 차로·굽은 길)은 안내하지 않는다 */
        if (tk !== 'S' && outs > 1 && !((tk === 'r' || tk === 'l') && nm && nm === cn)) { var last = mans[mans.length - 1]; if (last && dist - last.d < 18 && last.k === tk) { last.nm = nm || last.nm; } else mans.push({ d: dist, k: tk, nm: nm, sig: sc ? (sc.si >= 0 ? G.sig[sc.si].nm : XS[sc.xi - 1].nm) : '', e: e }); } }
    }
    mans.push({ d: dist, k: 'E', nm: dest && dest.nm || '목적지' });
    var lims = []; var dd = 0; es.forEach(function (e, i2) { lims.push([dd, eSpd(e), G.S[G.eS[e]][5] >= 0 ? G.j.names[G.S[G.eS[e]][5]] : '', G.S[G.eS[e]][9]]); dd += eLen(e); });
    return { es: es, pts: pts, cum: cum, dist: dist, time: t, tc: tc, free: free, mans: mans, sigs: sigs, lims: lims, T0: T0, a: a, b: b, live: dist ? liveLen / dist : 0, cong: cong, kn: kn, accs: accs, mode: MODE, viaLive: !!LIVER };
  }
  function plan(noFit) { if (!G || !dest || !me) return; if (PK && !PKW) { var mk = pkKeys([[me.x, me.y], [dest.x, dest.y]], 2200); if (mk.length) { PKW = true; note('골목 길을 받는 중…'); pkLoad(mk).then(function (n) { PKW = false; if (n) pkRebuild(true, false, mk); plan(noFit); }); return; } }
    var T0 = Date.now() / 1000, r = findRoute(me.x, me.y, dest.x, dest.y, T0, me.spd > 2 ? me.hd : null);
    if (!r) { route = null; note('길을 찾지 못했다 — 목적지나 내 자리가 길에서 너무 멀다(' + AREA_KO + '과 둘레 2km 안에서만 된다)'); paint(); draw(); return; }
    if (guide && DLOG) (DLOG.re = DLOG.re || []).push([Date.now(), Math.round(r.time), Math.round(r.dist)]);   /* 주행 기록 — 다시 찾은 때(그 뒤 예측은 바뀐 길) */
    if (guide && route && MODE !== 'v') { lastSay.man = null; setTimeout(function () { if (guide && route) say('새 경로입니다. ' + etaWords(route), 1); }, 1500); }
    route = r; route.pos = 0; note(''); paint(); if (!guide && !noFit) fitRoute(); draw(); }

  /* ---------- 내 자리 ---------- */
  var watchId = null;
  function gpsStart() { if (!navigator.geolocation) { note('이 기기는 위치를 알려주지 않는다 — 지도를 길게 눌러 떠나는 곳을 정한다'); return; } if (watchId != null) return;
    watchId = navigator.geolocation.watchPosition(function (pos) { var c = pos.coords; if (sim) return; drvPt(c); setMe(PX(c.longitude), PY(c.latitude), c.accuracy || 0, c.heading, c.speed); },
      function (e) { note(e && e.code === 1 ? '위치 권한이 꺼져 있다 — 아이폰: 설정 › 개인정보 보호 및 보안 › 위치 서비스 › Safari 웹사이트 › 「앱을 사용하는 동안」 · 지도를 길게 눌러 떠나는 곳을 정할 수도 있다' : '위치를 잡지 못했다 — 하늘이 보이는 곳에서 잠시 기다린다'); }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 20000 }); }
  function setMe(x, y, acc, hd, spd) { var prev = me, hk0 = true, h = hd != null && !isNaN(hd) && hd >= 0 && (spd == null || spd > 1) ? hd : null; if (h == null && prev) { var mv = Math.hypot(x - prev.x, y - prev.y), still = spd != null && !isNaN(spd) && spd <= 1, fp = still || mv <= 4; h = fp ? prev.hd : brg(prev.x, prev.y, x, y); if (fp && !prev.hk) hk0 = false; }
    me = { x: x, y: y, acc: acc, hk: h != null && hk0, hd: h == null ? 0 : h, spd: spd == null || isNaN(spd) ? (prev && prev.t ? Math.hypot(x - prev.x, y - prev.y) / Math.max(0.5, (Date.now() - prev.t) / 1000) : 0) : spd, t: Date.now(), out: !G || x < G.box[0] - 300 || x > G.box[1] + 300 || y < G.box[2] - 300 || y > G.box[3] + 300 };
    if ((guide || cruise) && prev) { try { lrnTrack(); } catch (e) {} }   /* v0.23.0 다녀 본 길 */
    if (dest && !route && G) plan(); if (route) track(); if (follow) { view.cx = me.x; view.cy = me.y; if (guide || cruise) view.rot = me.hd; } if (PK && cruise && !route) { var ck2 = pkKeys([[me.x, me.y]], 1600); if (ck2.length) pkLoad(ck2).then(pkSoon); } paint(); draw(); }
  /* 길 위의 내 자리(진행 거리) · 벗어나면 다시 계산 */
  function track() { var r = route, best = 1e9, bd = r.pos || 0, lo = 0, i; for (i = 0; i + 3 < r.pts.length; i += 2) { var k = i / 2; if (r.cum[k + 1] < (r.pos || 0) - 60) continue; if (r.cum[k] > (r.pos || 0) + 400) break; var ax = r.pts[i], ay = r.pts[i + 1], bx = r.pts[i + 2], by = r.pts[i + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((me.x - ax) * vx + (me.y - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - me.x, ay + vy * t - me.y); if (d < best) { best = d; bd = r.cum[k] + Math.sqrt(l2) * t; lo = i; } }
    r.off = best; if (best < 45) { r.pos = bd; r.offN = 0; r.sx = null; var ax2 = r.pts[lo], ay2 = r.pts[lo + 1], bx2 = r.pts[lo + 2], by2 = r.pts[lo + 3], l = Math.hypot(bx2 - ax2, by2 - ay2) || 1, tt = (bd - r.cum[lo / 2]) / l; r.sx = [ax2 + (bx2 - ax2) * tt, ay2 + (by2 - ay2) * tt, brg(ax2, ay2, bx2, by2)]; }
    else { r.offN = (r.offN || 0) + 1; if (guide && r.offN >= 3 && Date.now() - (r.reT || 0) > 6000) { r.reT = Date.now(); say('경로를 벗어났습니다. 다시 찾습니다'); plan(); return; } }
    if (guide && r.dist - r.pos < 25) { say('목적지 부근입니다. 안내를 마칩니다'); try { if (GSTART && GSTART.mode === 'n' && !GSTART.sim && !sim && !(dest && dest.vip) && window.TT) TT.calAdd((Date.now() - GSTART.t) / 1000, GSTART.pred); } catch (e) {} arrAdd(GSTART, (Date.now() - (GSTART ? GSTART.t : 0)) / 1000); GSTART = null; guideStop(true); } }


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
  function needTiles() { if (!BASE.idx || view.s < 0.03 || MODE === 'v') return; var T = BASE.idx.size, W = cv.clientWidth, H = cv.clientHeight, c = [S2W(0, 0), S2W(W, 0), S2W(0, H), S2W(W, H)], x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12; c.forEach(function (q) { x0 = Math.min(x0, q[0]); x1 = Math.max(x1, q[0]); y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); });
    var n = 0; for (var ix = Math.floor(x0 / T); ix <= Math.floor(x1 / T); ix++) for (var iz = Math.floor(y0 / T); iz <= Math.floor(y1 / T); iz++) { var k = ix + '_' + iz; if (++n > 12) return; if (!BASE.set[k] || BASE.T[k] || BASE.ld[k] || BASE.q >= 2) continue; BASE.ld[k] = 1; BASE.q++;
      (function (k) { getJ(tileUrl(k)).then(function (j) { BASE.q--; if (j) { BASE.T[k] = tilePrep(j, k); drawSoon(); } }); })(k); } }
  function drawBase(dark, s) { needTiles(); var ks = Object.keys(BASE.T); if (!ks.length) return; var col = dark ? { park: '#173426', wood: '#142f21', pitch: '#1b3a29', cem: '#213228', w: '#17324f' } : { park: '#d3ecc6', wood: '#c1e2b0', pitch: '#c9e8bc', cem: '#dde8d6', w: '#a9d4f5' };
    ['park', 'wood', 'pitch', 'cem'].forEach(function (kd) { ctx.fillStyle = col[kd]; ks.forEach(function (k) { (BASE.T[k].g[kd] || []).forEach(function (c) { ctx.fill(c.p, 'evenodd'); }); }); });
    ctx.fillStyle = col.w; ks.forEach(function (k) { BASE.T[k].w.forEach(function (c) { ctx.fill(c.p, 'evenodd'); }); });
    ctx.strokeStyle = col.w; ctx.lineWidth = Math.max(5, 2 / s); ks.forEach(function (k) { ctx.stroke(BASE.T[k].ww); });
    if (s > 0.08) { ctx.strokeStyle = dark ? '#475569' : '#9aa3af'; ctx.lineWidth = Math.max(3, 1.6 / s); ks.forEach(function (k) { ctx.stroke(BASE.T[k].rail); }); ctx.strokeStyle = dark ? '#111827' : '#eef1f4'; ctx.lineWidth = Math.max(1.4, 0.8 / s); ctx.setLineDash([9, 9]); ks.forEach(function (k) { ctx.stroke(BASE.T[k].rail); }); ctx.setLineDash([]); } }
  /* v0.7.1 — 여섯 구 건물(12만 9천 동 · 한 장이면 16MB)은 2km 칸으로 나눠(data/maps/bld6 · tools/gargo/bld-cut.py) 화면에 보이는 칸(+200m)만 받는다 · 칸 자료가 없으면 종전 서초 한 장 */
  var BIDX = null, BTL = {}, BT = {}, BVIS = [], BNM = null, BNMP = null;
  function bOff() { return [-2438 - (LON0 - 127.0077) * KX, -1743 - (37.4917 - LAT0) * KY]; }
  function bmap(b) { var o = bOff(), dx = o[0], dy = o[1], n = b.p.length, P = new Float32Array(n * 2), x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, sx = 0, sy = 0; for (var i = 0; i < n; i++) { var x = b.p[i][0] + dx, y = b.p[i][1] + dy; P[i * 2] = x; P[i * 2 + 1] = y; sx += x; sy += y; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; } return { p: P, b: [x0, x1, y0, y1], n: b.n || '', x: sx / n, y: sy / n, a: (x1 - x0) * (y1 - y0) }; }
  function bldLoad() { if (BLDP) return; BLDP = getJ('../data/maps/bld6/index.json').then(function (j) { if (j && j.tiles && j.cell) { BIDX = j; BLD = []; drawSoon(); return; }
      return getJ('../data/maps/seocho-full-buildings.json').then(function (j2) { if (!j2 || !j2.buildings) return; BLD = j2.buildings.filter(function (b) { return b.p && b.p.length > 2; }).map(bmap); BVIS = [BLD]; drawSoon(); }); }); }
  /* v0.7.2 독립 검수 — 건물은 칸마다 따로(BT) 두고 그릴 때는 화면에 보이는 칸(BVIS)만 돈다 · 30칸 넘게 쌓이면 화면 밖 칸은 비운다(다시 오면 캐시에서) · 못 받은 칸은 30초 뒤 다시 */
  function bldNeed(x0, x1, y0, y1) { if (!BIDX || MODE === 'v') return; var o = bOff(), c = BIDX.cell, vis = [], want = {};
    for (var ix = Math.floor((x0 - 200 - o[0]) / c); ix <= Math.floor((x1 + 200 - o[0]) / c); ix++) for (var iz = Math.floor((y0 - 200 - o[1]) / c); iz <= Math.floor((y1 + 200 - o[1]) / c); iz++) { var k = ix + '_' + iz; if (!BIDX.tiles[k]) continue; want[k] = 1; if (BT[k]) { vis.push(BT[k]); continue; } if (BTL[k] && Date.now() - BTL[k] < 30000) continue; BTL[k] = Date.now();
      (function (k) { getJ('../data/maps/bld6/c/' + k + '.json').then(function (t) { if (!t || !t.buildings) return; BT[k] = t.buildings.filter(function (b) { return b.p && b.p.length > 2; }).map(bmap); drawSoon(); }); })(k); }
    BVIS = vis; var ks = Object.keys(BT); if (ks.length > 30) ks.forEach(function (k) { if (!want[k]) { delete BT[k]; delete BTL[k]; } }); }
  /* 건물 이름 찾기 — 이름 있는 건물만 한 파일(bld6/names.json · [이름, x, z]) · 칸을 띄우지 않아도 찾힌다 */
  function bnmLoad() { if (BNMP || !BIDX) return; BNMP = getJ('../data/maps/bld6/names.json').then(function (j) { if (!j || !j.n) { BNMP = null; return; } var o = bOff(); BNM = j.n.map(function (r) { return { n: r[0], x: r[1] + o[0], y: r[2] + o[1] }; }); }); }
  function drawBld(dark, s) { if (s < 0.4) return; if (!BLD) { bldLoad(); return; } var W = cv.clientWidth, H = cv.clientHeight, c = [S2W(0, 0), S2W(W, 0), S2W(0, H), S2W(W, H)], x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12; c.forEach(function (q) { x0 = Math.min(x0, q[0]); x1 = Math.max(x1, q[0]); y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); }); bldNeed(x0, x1, y0, y1);
    ctx.fillStyle = dark ? '#1b2434' : '#e7e2d9'; ctx.strokeStyle = dark ? '#2a3547' : '#d6cfc3'; ctx.lineWidth = 0.6 / s; var n = 0; ctx.beginPath();
    for (var t = 0; t < BVIS.length; t++) for (var i = 0, L = BVIS[t]; i < L.length; i++) { var b = L[i]; if (b.b[1] < x0 || b.b[0] > x1 || b.b[3] < y0 || b.b[2] > y1) continue; var p = b.p; ctx.moveTo(p[0], p[1]); for (var u = 2; u < p.length; u += 2) ctx.lineTo(p[u], p[u + 1]); ctx.closePath(); if (++n >= 16) { ctx.fill(); if (s > 0.8) ctx.stroke(); ctx.beginPath(); n = 0; } } if (n) { ctx.fill(); if (s > 0.8) ctx.stroke(); } }
  /* 소통 색 — 값이 온 길만 · 갈래는 spdLv(앱 기준). 큰길(갈래 1~5)은 늘, 생활도로는 가까이 볼 때만(멀리서 다 그리면 지도가 온통 빨갛다) */
  function drawTraf(s) { if (!LIVE.m) return; if (!TRAF || TRAFAT !== LIVE.at) { TRAF = [new Path2D(), new Path2D(), new Path2D(), new Path2D(), new Path2D(), new Path2D()]; TRAFAT = LIVE.at; for (var i = 0; i < G.S.length; i++) { var q = G.S[i], lim = q[3] || 30, p = G.SP[i]; for (var d = 0; d < 2; d++) { var li = q[13 + d]; if (li == null || li < 0) continue; var v = LIVE.m[G.j.links[li]]; if (!(v > 0)) continue; var pa = TRAF[spdLv(v, q[4], lim) + (q[4] <= 5 ? 0 : 3)], off = (d ? -1 : 1) * 3.2;
          /* 두 방향을 길 가운데에서 조금씩 벌려 그린다 */ for (var u = 0; u + 3 < p.length; u += 2) { var ax = p[u], ay = p[u + 1], bx = p[u + 2], by = p[u + 3], l = Math.hypot(bx - ax, by - ay) || 1, nx = -(by - ay) / l * off, ny = (bx - ax) / l * off; if (!u) pa.moveTo(ax + nx, ay + ny); pa.lineTo(bx + nx, by + ny); } } } }
    /* 멀리서 보면 큰길의 서행·정체만 가늘게 · 가까이 보면 원활까지 · 더 가까이(0.9 배율부터) 생활도로도 */
    var far = s < 0.3, col = ['#22c55e', '#f59e0b', '#dc2626']; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.globalAlpha = far ? 0.85 : 0.92; ctx.lineWidth = far ? 2.4 / s : Math.max(3.2, 2.6 / s); col.forEach(function (c, i) { if (far && !i) return; ctx.strokeStyle = c; ctx.stroke(TRAF[i]); });
    if (s >= 0.9) { ctx.globalAlpha = 0.8; ctx.lineWidth = Math.max(2.2, 1.8 / s); col.forEach(function (c, i) { ctx.strokeStyle = c; ctx.stroke(TRAF[i + 3]); }); } ctx.globalAlpha = 1; }
  /* 이름 — 교차로·신호 교차로·역·공원·큰 건물 */
  var PLBOX = [];   /* v0.15.2 이번 그림의 이름 칸 [가운데 x, y, 폭] — 신호 남은 초가 피해 간다 */
  function plFree(x, y, w, h) { for (var i = 0; i < PLBOX.length; i++) { var b = PLBOX[i]; if (Math.abs(b[0] - x) < (b[2] + w) / 2 + 3 && Math.abs(b[1] - y) < (14 + h) / 2 + 2) return false; } return true; }
  function drawPlaces(dark, s, W, H) { PLBOX = []; if (s < 0.03) return; var boxes = PLBOX, seen = {}, n = 0, far = s < 0.22;
    function put(nm, x, y, font, col, dy, max) { if (n >= max) return; var q = W2S(x, y); if (q[0] < 24 || q[0] > W - 24 || q[1] < 80 || q[1] > H - 110) return; var key = nm.replace(/\s+/g, ''); if (seen[key]) return; ctx.font = font; var tw = ctx.measureText(nm).width, cx = q[0], cy = q[1] + dy; for (var i = 0; i < boxes.length; i++) { var b = boxes[i]; if (Math.abs(b[0] - cx) < (b[2] + tw) / 2 + 5 && Math.abs(b[1] - cy) < 15) return; } boxes.push([cx, cy, tw]); seen[key] = 1; n++;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(17,24,39,.92)' : 'rgba(255,255,255,.95)'; ctx.strokeText(nm, cx, cy); ctx.fillStyle = col; ctx.fillText(nm, cx, cy); return q; }
    STN.forEach(function (o) { var q = put(o.n, o.x, o.y, '800 12.5px system-ui, sans-serif', dark ? '#93c5fd' : '#1d4ed8', -13, far ? 12 : 60); if (q) { ctx.beginPath(); ctx.arc(q[0], q[1], 4.5, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); ctx.lineWidth = 2.2; ctx.strokeStyle = '#1d4ed8'; ctx.stroke(); } });
    if (s > 1.1) STN.forEach(function (o) { o.ex.forEach(function (e) { var q = W2S(e[0], e[1]); if (q[0] < 0 || q[0] > W || q[1] < 70 || q[1] > H - 100) return; ctx.beginPath(); ctx.arc(q[0], q[1], 7, 0, Math.PI * 2); ctx.fillStyle = '#facc15'; ctx.fill(); ctx.font = '800 9.5px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#111'; ctx.fillText(e[2], q[0], q[1] + 0.5); }); });
    if (s > 0.3) G.sig.forEach(function (g) { put(g.nm, g.x, g.y, '700 11px system-ui, sans-serif', dark ? '#fde68a' : '#7c2d12', -14, 60); });
    if (s <= 0.45) Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { if (j.k === 'g' && /산$|숲$|대공원$|한강공원$/.test(j.n)) put(j.n, j.x, j.y, 'italic 700 11.5px system-ui, sans-serif', dark ? '#86efac' : '#166534', 0, far ? 20 : 66); }); });
    if (s > 0.45) Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { put(j.n, j.x, j.y, j.k === 'g' ? 'italic 700 11.5px system-ui, sans-serif' : '600 10.5px system-ui, sans-serif', j.k === 'g' ? (dark ? '#86efac' : '#166534') : (dark ? '#cbd5e1' : '#475569'), j.k === 'g' ? 0 : -12, 70); }); });
    if (s > 0.75 && BLD) { var c = [S2W(0, 0), S2W(W, H)]; BVIS.forEach(function (L) { L.forEach(function (b) { if (!b.n || b.a < (s > 1.4 ? 300 : 1500)) return; put(b.n, b.x, b.y, '600 10.5px system-ui, sans-serif', dark ? '#d1d5db' : '#57534e', 0, 90); }); }); } }
  /* 평상시 신호 — 방위마다 직진 신호의 지금 색(아는 곳만). 가운데 점에서 그 차가 들어오는 쪽으로 짧은 막대 · 가까이 보면 남은 초 */
  var SIDEV = { nt: [0, -1], ne: [0.7, -0.7], et: [1, 0], se: [0.7, 0.7], st: [0, 1], sw: [-0.7, 0.7], wt: [-1, 0], nw: [-0.7, -0.7] };
  function sigSides(no) { var out = {}, recs = (SIG.its[no] || []).filter(recOk); recs.forEach(function (r) { r.mv.forEach(function (m) { if ((m[1] === 'St' || m[1] === 'Lt') && m[2] != null && DIRS.indexOf(m[0]) >= 0) (out[m[0]] = out[m[0]] || {})[m[1]] = 1; }); }); return out; }
  function inZone(x, y) { if (!me) return false; if (!me.hk) return Math.hypot(x - me.x, y - me.y) <= 500; var dx = x - me.x, dy = y - me.y, hr = me.hd * Math.PI / 180, f = dx * Math.sin(hr) - dy * Math.cos(hr), d = Math.hypot(dx, dy); return f >= 0 ? d <= CF.fwd : d <= CF.back; }
  function drawSigs(dark, s, W, H, onR, now) { if (s <= 0.1) return; var live = OV.s && SIG.ready && s > 0.28, zone = guide || cruise, cr = Math.cos(-view.rot * Math.PI / 180), sr = Math.sin(-view.rot * Math.PI / 180), nd = 0;
    G.sig.forEach(function (sg, si) { if (onR[si]) return; var q = W2S(sg.x, sg.y); if (q[0] < -20 || q[0] > W + 20 || q[1] < -20 || q[1] > H + 20) return;
      if (live && nd < 70 && (!zone || inZone(sg.x, sg.y))) { var sd = sg._sd || (sg._sd = sigSides(sg.no)), ks = Object.keys(sd), any = false; ks.forEach(function (k) { if (!sd[k].St) return; var st = sigAt(sg.no, now, k, 'St'); if (!st || st.kind === 'avg') return; any = true; var v = SIDEV[k], vx = v[0] * cr - v[1] * sr, vy = v[0] * sr + v[1] * cr, L = s > 0.6 ? 17 : 12;
          ctx.beginPath(); ctx.moveTo(q[0] + vx * 5, q[1] + vy * 5); ctx.lineTo(q[0] + vx * L, q[1] + vy * L); ctx.lineCap = 'round'; ctx.lineWidth = 6.5; ctx.strokeStyle = '#111827'; ctx.stroke(); ctx.lineWidth = 4; ctx.strokeStyle = st.green ? '#22c55e' : '#ef4444'; ctx.stroke();
          if (s > 0.75 || cruise) { ctx.font = '900 21px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; var tx = Math.ceil(st.remain) + '', tw = ctx.measureText(tx).width, Dd = L + 15, k9; for (k9 = 0; k9 < 3 && !plFree(q[0] + vx * Dd, q[1] + vy * Dd, tw, 20); k9++) Dd += 12; var X9 = q[0] + vx * Dd, Y9 = q[1] + vy * Dd; PLBOX.push([X9, Y9, tw]); ctx.lineWidth = 4.5; ctx.lineJoin = 'round'; ctx.strokeStyle = dark ? '#111827' : '#fff'; ctx.strokeText(tx, X9, Y9); ctx.fillStyle = st.green ? '#15803d' : '#b91c1c'; ctx.fillText(tx, X9, Y9); } });
        if (any) nd++; ctx.beginPath(); ctx.arc(q[0], q[1], 4.2, 0, Math.PI * 2); ctx.fillStyle = any ? '#111827' : (dark ? '#64748b' : '#94a3b8'); ctx.fill(); return; }
      ctx.beginPath(); ctx.arc(q[0], q[1], 3.2, 0, Math.PI * 2); ctx.fillStyle = dark ? '#64748b' : '#94a3b8'; ctx.fill(); }); }
  /* v0.6.2 — 소유자 「눌러 보니 신호값이 없다고 나온다」. 서울시 신호 자료(T-Data)는 5분에 한 번 · 한 번에 교차로 20~40곳씩만 와서 서초 한 곳을 다시 받기까지 몇 시간 걸린다.
     「지금 색」은 ① 12분 안에 받은 값(확인된 기록은 2시간) ② 그 시각대 계획을 이미 익힌 곳만 낼 수 있다 — 나머지는 평균 기다림. 그 까닭과 지금 몇 곳인지를 화면에 밝힌다 */
  function lastSeen(no) { var m = 0; (SIG.its[no] || []).forEach(function (r) { if (r.a && r.a > m) m = r.a; }); return m; }
  function ago(t) { var d = Date.now() / 1000 - t; return d < 3600 ? Math.max(1, Math.round(d / 60)) + '분 전' : d < 172800 ? Math.round(d / 3600) + '시간 전' : Math.round(d / 86400) + '일 전'; }
  var SSTAT = null;
  function sigStat() { if (!G || !SIG.ready) return ''; var now = Date.now() / 1000; if (!SSTAT || now - SSTAT.t > 60) { var k = 0, n = 0; G.sig.forEach(function (sg) { if (!(SIG.its[sg.no] || []).length) return; n++; for (var i = 0; i < DIRS.length; i++) { var st = sigAt(sg.no, now, DIRS[i], 'St'); if (st && st.kind !== 'avg') { k++; break; } } }); SSTAT = { t: now, k: k, n: n }; }
    return '<div class="hint" style="margin-top:8px;font-size:12.5px">🚦 지금 색·남은 초를 아는 신호 <b>' + SSTAT.k + '곳</b> / 자료 있는 ' + SSTAT.n + '곳 — 서울시 자료가 5분에 교차로 20~40곳씩만 와서 모으는 중이다(나머지는 평균 기다림)</div>'; }
  /* v0.7.0 — T-Data 값이 없는 교차로(예: 인재개발원 3971 — 장비는 줄을 보내지만 방향별 남은 초가 비어 있다)는 경찰청 공개 계획(../data/signal-tod-seoul.json · 요일 1 일 … 7 토 · 특수일은 일요일)이라도 보인다.
     계획에는 「어느 현시가 어느 방향인지」와 「지금 몇 초인지」가 없다 — 주기·현시 길이만. 누를 때 처음 한 번 받는다(573KB) */
  var TOD = null, TODP = null, TODM = '';
  function dKey(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function dwOf(d) { return SIG.hol && SIG.hol[dKey(d)] ? 1 : d.getDay() + 1; }   /* 1 일 … 7 토 · 특수일 = 일요일 계획(서초 교통과 현시도 15종에서 본 규칙을 서울 경찰청 계획에 넓혀 씀 — 추정) */
  /* v0.7.2 독립 검수 — 받기는 한 번만(TODP) · 못 받으면 cb('fail')(「없다」가 아니다) · 그날 첫 줄보다 이르면 **실제 어제**의 요일 갈래(어제가 특수일이면 일요일)의 마지막 줄 */
  function todFor(no, cb, at) {   /* at = 시험용 시각(ms) · 받아 둔 뒤에는 바로 셈한다 */
    if (TOD) return todCalc(TOD, no, cb, at);
    if (!TODP) TODP = getJ('../data/signal-tod-seoul.json').then(function (j) { if (!j || !j.spots) { TODP = null; return null; } TOD = {}; TODM = String(j.made || '').slice(0, 10); j.spots.forEach(function (x) { TOD[String(x.no)] = x; }); return TOD; });
    TODP.then(function (T) { todCalc(T, no, cb, at); }); }
  function todCalc(T, no, cb, at) { if (!T) return cb('fail'); var sp = T[no]; if (!sp) return cb(null); var d = at ? new Date(at) : new Date(), dw = dwOf(d), hm0 = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2), row = null, prev = false, hol = dw === 1 && d.getDay() !== 0;
      (sp.plans[sp.dow[dw]] || []).forEach(function (r) { if (r[0] <= hm0) row = r; });
      if (!row) { var y = new Date(d.getTime() - 864e5), yw = dwOf(y), pr = sp.plans[sp.dow[yw]] || []; row = pr[pr.length - 1] || null; prev = true; hol = yw === 1 && y.getDay() !== 0; }
      cb(row ? { at: row[0], C: row[1], a: String(row[3] || '').trim(), b: String(row[4] || '').trim(), hol: hol, prev: prev } : null); }
  /* 짧게 누름 — 신호 교차로면 방향마다 지금 색을 글로 */
  function tapAt(px, py) { if (!G || guide) return; var el = $('gPick'); if (el.style.display === 'flex') { el.style.display = 'none'; return; } var best = null, bd = 28; G.sig.forEach(function (sg) { var q = W2S(sg.x, sg.y), d = Math.hypot(q[0] - px, q[1] - py); if (d < bd) { bd = d; best = sg; } }); if (!best) return;
    var now = Date.now() / 1000, sd = sigSides(best.no), rows = []; DIRS.forEach(function (k) { if (!sd[k]) return; ['St', 'Lt'].forEach(function (mv) { if (!sd[k][mv]) return; var st = sigAt(best.no, now, k, mv); rows.push('<div class="si"><span>' + DIRKO[k] + '쪽에서 ' + (mv === 'St' ? '직진' : '좌회전') + '</span>' + (!st ? '<em>모름</em>' : st.kind === 'avg' ? '<em>지금 색 모름 · 주기 ' + Math.round(st.C) + '초</em>' : '<b class="' + (st.green ? 'g' : 'r') + '">' + (st.green ? '녹색' : '적색') + ' ' + Math.ceil(st.remain) + '초</b>') + '</div>'); }); });
    var ns = nearSeg(best.x, best.y, 200); el.style.display = 'flex'; el.style.left = Math.max(8, Math.min(cv.clientWidth - 248, px - 120)) + 'px'; el.style.top = Math.max(70, Math.min(cv.clientHeight - 330, py + 14)) + 'px'; el.style.width = '240px';
    el.innerHTML = '<b>🚦 ' + esc(best.nm) + '</b>' + (rows.length ? rows.join('') + (rows.join('').indexOf('지금 색 모름') >= 0 && lastSeen(best.no) ? '<div class="si"><em>이 교차로 값을 마지막으로 받은 때 ' + ago(lastSeen(best.no)) + ' — 서울시 자료가 5분에 20~40곳씩만 와서 다시 받기까지 몇 시간 걸린다 · 그 사이엔 평균 기다림만</em></div>' : '') + '<div class="si"><em>계획값 — 수동 조작·감응이면 다르다</em></div>' : '<div class="si"><em>이 교차로는 서울시 신호 값(T-Data)이 없다 — 장비가 방향별 남은 초를 안 보내는 곳</em></div><div class="si" id="gTod" data-no="' + esc(best.no) + '"><em>경찰청 계획을 찾는 중…</em></div>') + '<button data-p="to">여기로 안내</button><button data-p="x">닫기</button>'; el._w = [ns ? ns.x : best.x, ns ? ns.y : best.y, best.nm];
    if (!rows.length) todFor(best.no, function (t) { var x = document.getElementById('gTod'); if (!x || x.getAttribute('data-no') !== String(best.no)) return;   /* 그 사이 다른 교차로 카드로 바뀌었으면 쓰지 않는다 */
      x.innerHTML = t === 'fail' ? '<em>경찰청 계획을 받지 못했다(통신) — 다시 눌러 본다</em>' : t ? '<span>경찰청 공개 계획' + (TODM ? '(' + esc(TODM) + ' 받음)' : '') + (t.prev ? ' · 전날 계획이 이어짐' : '') + (t.hol ? ' · 특수일이라 일요일 계획으로 봄(추정)' : '') + '</span><b>' + esc(t.at) + '부터 주기 ' + t.C + '초</b><em>현시 ' + esc(t.a.split(/\s+/).join(' · ')) + '초' + (t.b && t.b !== t.a ? ' (B링 ' + esc(t.b.split(/\s+/).join(' · ')) + ')' : '') + ' — 어느 현시가 어느 방향인지 · 지금 몇 초인지는 계획에 없다 · 눈으로</em>' : '<em>경찰청 공개 계획에도 없다 — 눈으로 본다</em>'; }); }
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
    STN.forEach(function (o) { if (has(o.n)) add('🚇', o.n, o.x, o.y); }); G.sig.forEach(function (g) { if (has(g.nm)) add('🚦', g.nm, g.x, g.y); }); (BNM || (BIDX ? [] : BLD || [])).forEach(function (b) { if (b.n && has(b.n)) add('🏢', b.n, b.x, b.y); });
    Object.keys(BASE.T).forEach(function (k) { BASE.T[k].jn.forEach(function (j) { if (has(j.n)) add(j.k === 'g' ? '🌳' : '✚', j.n, j.x, j.y); }); }); G.LAB.forEach(function (L) { if (has(L.n)) add('🛣', L.n, L.x, L.y); }); return out; }
  var FSEQ = 0, FEXT = false;
  var FNT = 0;
  function findRun(raw, auto, vq) { vq = vq || MODE === 'v'; var q = String(raw || '').replace(/\s+/g, '');   /* vq = 처음 부를 때 중요업무였나 — 이름 목록을 받은 뒤 다시 돌 때도 그대로(그사이 모드가 바뀌어도 밖으로 묻지 않는다) */ clearTimeout(FNT); if (!G || q.length < 2) { fl.style.display = 'none'; return; } if (!BLD) bldLoad(); else bnmLoad(); if (!BNM && BLDP) BLDP.then(function () { bnmLoad(); if (BNMP) BNMP.then(function () { if (seq === FSEQ && BNM) findRun(raw, auto, vq); }); }); var seq = ++FSEQ, out = localFind(q), gs = addrGuess(raw), txt = String(raw).replace(/\s+/g, ' ').trim(), net = txt.length >= 2 && navigator.onLine !== false && !vq, st = net ? '🔎 주소·장소를 찾는 중…' : (navigator.onLine === false ? '통신이 끊겨 있다 — 이 기기 안의 이름만 찾는다' : ''), wait = net;
    function show(extra, exact) { if (seq !== FSEQ) return; var all = out.concat(extra || []); if (gs && !exact) all.push(gs); fl._o = all;
      fl.innerHTML = all.slice(0, 16).map(function (o, i) { return '<button data-i="' + i + '">' + o[0] + ' ' + esc(o[1]) + (o[4] ? ' <small>' + esc(o[4]) + '</small>' : '') + '</button>'; }).join('') + (all.length || wait ? '' : '<div class="no">찾지 못했다 — 「반포대로 179」「서초동 1726-1」처럼 주소를 적거나, 지도를 길게 눌러 목적지를 정한다</div>') + (st ? '<div class="no">' + esc(st) + '</div>' : '');
      fl.style.display = 'block'; if (auto && !wait && all.length === 1) pickFound(0); }
    show(null, false); if (!net) return;
    FNT = setTimeout(function () { if (seq !== FSEQ) return; vwSearch(txt).then(function (r) { if (seq !== FSEQ) return; wait = false; var ex = r && r.list || [], hit = ex.some(function (o) { return o[0] === '🏠'; });
      st = ex.length ? '' : (r && r.err ? '주소 검색에 닿지 못했다 — ' + r.err + (gs ? ' · 아래는 도로명 번호로 셈한 어림 자리' : '') : '');
      /* 엔터·음성: 적은 글과 딱 맞는 것이 하나뿐이면 그것으로(「사임당로 143」 ↔ 「사임당로17길 143」을 가른다 · 장소는 이름이 같을 때) */
      var pickI = -1; if (auto) { var n0 = out.length, hits = []; ex.forEach(function (o, i) { var nm = ' ' + o[1].replace(/\(.*?\)/g, ' ') + ' '; if (o[0] === '🏠' ? nm.indexOf(' ' + txt + ' ') >= 0 : o[1].replace(/\s+/g, '') === q) hits.push(n0 + i); }); if (hits.length === 1 && !out.some(function (o) { return o[1].replace(/\s+/g, '') === q; })) pickI = hits[0]; }
      show(ex, hit); if (pickI >= 0 && fl.style.display !== 'none') pickFound(pickI); }); }, auto ? 0 : 700); }
  function pickFound(i) { var o = fl._o && fl._o[i]; if (!o) return; var vq1 = MODE === 'v'; FEXT = o[0] === '🏠' || o[0] === '📍'; fl.style.display = 'none'; if (o[0] === '📐') note(o[4]); fi.value = o[1]; fi.blur(); var tk1 = ++PICKSEQ; pkEnsure([[o[2], o[3]]], 800).then(function () { if (tk1 !== PICKSEQ) return; var ns = nearSeg(o[2], o[3], 400); setDest(ns ? ns.x : o[2], ns ? ns.y : o[3], o[1], vq1); }); if (!route) { view.cx = o[2]; view.cy = o[3]; if (view.s < 0.5) view.s = 0.7; follow = false; } draw(); }
  /* 음성으로 목적지 — 브라우저의 받아쓰기(webkitSpeechRecognition · 크롬·사파리는 소리를 그 회사 서버로 보낸다 · 티북의 음성 입력과 같은 길) */
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition, rec = null;
  function micGo() { var b = $('gMic'); if (MODE === 'v') { note('🔒 중요업무 중에는 음성 받아쓰기를 쓰지 않는다(소리가 그 회사 서버로 간다) — 손으로 적거나 지도를 길게 누른다'); return; } if (!SR) { note('이 브라우저는 음성 받아쓰기를 지원하지 않는다 — 자판의 마이크 단추로 말한다'); fi.focus(); return; } if (rec) { try { rec.stop(); } catch (e) {} return; }
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
    if (PK && !route && !guide && s > 0.25) { var vw = [S2W(0, 0), S2W(W, H), S2W(W, 0), S2W(0, H)], vcx = (vw[0][0] + vw[1][0]) / 2, vcy = (vw[0][1] + vw[1][1]) / 2, vk = pkKeys([[vcx, vcy]], Math.max(Math.abs(vw[0][0] - vw[1][0]), Math.abs(vw[2][1] - vw[3][1]), 600) / 2).sort(function (a, b) { var A = a.split('_'), B = b.split('_'), C = PK.cell; return Math.hypot((+A[0] + 0.5) * C - vcx, (+A[1] + 0.5) * C - vcy) - Math.hypot((+B[0] + 0.5) * C - vcx, (+B[1] + 0.5) * C - vcy); }).slice(0, 9); if (vk.length) pkLoad(vk).then(pkSoon); }
    drawBld(dark, s); if (OV.t) drawTraf(s);
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
    if (MODE === 'e' && BUSL && s > 0.2) { ctx.save(); ctx.setLineDash([7, 5]); ctx.lineWidth = 3; ctx.strokeStyle = 'rgba(37,99,235,.75)'; BUSL.forEach(function (b) { var o = b.p; ctx.beginPath(); for (var k = 0; k < o.length; k += 2) { var q = W2S(o[k], o[k + 1]); if (k) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]); } ctx.stroke(); }); ctx.restore(); }   /* v0.20.0 긴급 출동 — 버스전용차로 파란 점선 */
    drawSigs(dark, s, W, H, onR, now); if (cruise && !route) drawAhead(dark, now);
    if (route) route.sigs.forEach(function (g) { var sg = g.si >= 0 ? G.sig[g.si] : g, q = W2S(sg.x, sg.y); if (q[0] < -20 || q[0] > W + 20 || q[1] < -20 || q[1] > H + 20) return; var st = g.mv === 'St' || g.mv === 'Lt' ? sigAt(g.no, now, g.side, g.mv) : null, col = !st || st.kind === 'avg' ? '#94a3b8' : st.green ? '#16a34a' : '#dc2626';
      ctx.beginPath(); ctx.arc(q[0], q[1], 9, 0, Math.PI * 2); ctx.fillStyle = '#111827'; ctx.fill(); ctx.beginPath(); ctx.arc(q[0], q[1], 6.5, 0, Math.PI * 2); ctx.fillStyle = col; ctx.fill();
      if (st && st.kind !== 'avg' && s > 0.25) { var tx = Math.ceil(st.remain) + ''; ctx.font = '900 22px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; var tw = ctx.measureText(tx).width, Y9 = q[1] + 26; if (!plFree(q[0], Y9, tw, 22)) Y9 += 14; PLBOX.push([q[0], Y9, tw]); ctx.lineWidth = 4.5; ctx.lineJoin = 'round'; ctx.strokeStyle = '#fff'; ctx.strokeText(tx, q[0], Y9); ctx.fillStyle = col; ctx.fillText(tx, q[0], Y9); } });   /* 이름은 점 위(−14) · 남은 초는 점 아래 */
    if (!guide && DCARS.length) DCARS.forEach(function (c) { var q = W2S(c.x, c.y); ctx.beginPath(); ctx.arc(q[0], q[1], 12, 0, Math.PI * 2); ctx.fillStyle = '#1d4ed8'; ctx.fill(); ctx.lineWidth = 2.5; ctx.strokeStyle = '#fff'; ctx.stroke(); ctx.fillStyle = '#fff'; ctx.font = '800 12px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(c.nm === '내 차' ? '나' : String(c.n), q[0], q[1] + 0.5); });   /* v0.26.0 비교하는 순찰차 */
    if (dest) { var dq = W2S(dest.x, dest.y); ctx.beginPath(); ctx.moveTo(dq[0], dq[1]); ctx.lineTo(dq[0] - 9, dq[1] - 22); ctx.arc(dq[0], dq[1] - 26, 10, Math.PI * 0.85, Math.PI * 0.15); ctx.closePath(); ctx.fillStyle = '#e11d48'; ctx.fill(); ctx.beginPath(); ctx.arc(dq[0], dq[1] - 26, 4, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill(); }
    if (me) { var mp = route && route.sx && route.off < 45 ? route.sx : [me.x, me.y, me.hd], mq = W2S(mp[0], mp[1]); if (me.acc > 30) { ctx.beginPath(); ctx.arc(mq[0], mq[1], Math.max(14, me.acc * s), 0, Math.PI * 2); ctx.fillStyle = 'rgba(37,99,235,.12)'; ctx.fill(); }
      ctx.save(); ctx.translate(mq[0], mq[1]); ctx.beginPath(); ctx.arc(0, 2, 19, 0, Math.PI * 2); ctx.fillStyle = 'rgba(15,23,42,.18)'; ctx.fill(); ctx.beginPath(); ctx.arc(0, 0, 18, 0, Math.PI * 2); ctx.fillStyle = '#ffffff'; ctx.fill(); ctx.lineWidth = 1; ctx.strokeStyle = 'rgba(15,23,42,.12)'; ctx.stroke();
      ctx.rotate(((guide ? mp[2] : me.hd) - view.rot) * Math.PI / 180); ctx.beginPath(); ctx.moveTo(0, -12.5); ctx.lineTo(9.5, 9); ctx.lineTo(0, 4.2); ctx.lineTo(-9.5, 9); ctx.closePath(); ctx.fillStyle = '#1b54d6'; ctx.fill(); ctx.restore();
      if (guide || cruise) { var ht = hereText(); if (ht) { ctx.font = '800 13px system-ui, sans-serif'; var hw2 = ctx.measureText(ht).width + 22, hx = mq[0] - hw2 / 2, hy = mq[1] + 28; ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(hx, hy, hw2, 26, 13); else ctx.rect(hx, hy, hw2, 26); ctx.fillStyle = dark ? 'rgba(241,245,249,.92)' : 'rgba(15,23,42,.86)'; ctx.fill(); ctx.fillStyle = dark ? '#0f172a' : '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(ht, mq[0], hy + 13.5); } } }   /* v0.18.0 내 차 밑 지금 위치 알약 */
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
  /* ---------- v0.26.0 🚓 여러 순찰차 — 누가 먼저 닿나(참고용 예측) ----------
     가까운 순서가 아니라 빨리 닿는 순서 · 차 자리는 이 화면 메모리에만(저장·전송 없음 · 지도 그리기와 길 계산만) · 가까운데 늦으면 까닭 한 줄(돌아가는 길 / 신호 기다림 / 막힘) */
  var DCARS = [], DRES = null, DKEY = '', DN = 0;
  function ms2(s) { s = Math.max(0, Math.round(s)); var m = Math.floor(s / 60), x = s % 60; return m ? m + '분' + (x ? ' ' + x + '초' : '') : x + '초'; }
  function dispRun() { if (!G || !dest || !DCARS.length) return null; var k = DCARS.map(function (c) { return Math.round(c.x) + ',' + Math.round(c.y); }).join('|') + '>' + Math.round(dest.x) + ',' + Math.round(dest.y) + '@' + MODE + ':' + Math.floor(Date.now() / 60000);
    if (DRES && DKEY === k) return DRES; var T0 = Date.now() / 1000;
    var R = DCARS.map(function (c, i) { var r = null, st = Math.hypot(c.x - dest.x, c.y - dest.y); try { r = findRoute(c.x, c.y, dest.x, dest.y, T0, null); } catch (e) {} if (!r) return { c: c, i: i, st: st, err: 1 };
      var sw = r.sigs.reduce(function (a, g) { return a + (g.tw || 0); }, 0), cg = Math.max(0, r.time - sw - r.free), RG = rngOf(r, r.time), le = r.es[r.es.length - 1], ni = le != null ? G.S[G.eS[le]][5] : -1;
      return { c: c, i: i, st: st, t: r.time, pm: RG ? (RG[1] - RG[0]) / 2 : Math.max(20, r.time * 0.12), est: !RG, dist: r.dist, sw: sw, cg: cg, det: st > 50 ? r.dist / st : 1, nsig: r.sigs.length, road: ni >= 0 ? G.j.names[ni] : '' }; });
    var ok = R.filter(function (q) { return !q.err; }).sort(function (a, b) { return a.t - b.t; }), bySt = ok.slice().sort(function (a, b) { return a.st - b.st; });
    ok.forEach(function (q, j) { q.rk = j; q.srk = bySt.indexOf(q); if (q.srk < q.rk) q.why = '더 가깝지만 늦음 — ' + (q.det >= 1.6 ? '길이 돌아감(직선의 ' + q.det.toFixed(1) + '배 — 유턴·일방통행·건너는 길)' : q.sw >= q.cg ? '신호 ' + q.nsig + '곳 기다림 ' + ms2(q.sw) : '막힘 +' + ms2(q.cg)); });
    DKEY = k; DRES = { ok: ok, bad: R.filter(function (q) { return q.err; }) }; return DRES; }
  function dispOrder(q) { return q.c.nm + ' 예상 ' + ms2(q.t) + '(±' + ms2(q.pm) + ')' + (q.road ? ', ' + q.road + ' 쪽 정차' : ''); }
  function dispHtml() { var h = '<details class="disp"' + (DCARS.length ? ' open' : '') + '><summary>🚓 여러 순찰차 — 누가 먼저 닿나 <small>(참고용 예측)</small></summary><div class="dbtn"><button data-dc="mid">＋ 지도 가운데</button>' + (me ? '<button data-dc="me">＋ 내 자리</button>' : '') + (DCARS.length ? '<button data-dc="clr">모두 지우기</button>' : '') + '</div>';
    if (!DCARS.length) return h + '<p class="dnt">지도를 옮겨 순찰차 자리를 가운데에 두고 ＋ 를 누른다(최대 6대 · 이 화면에만 · 저장·전송 없음). 가까운 순서가 아니라 <b>빨리 닿는 순서</b>로 줄 세운다.</p></details>';
    var R = dispRun(); if (!R) return h + '</details>';
    h += R.ok.map(function (q, j) { return '<div class="dcar' + (j === 0 ? ' top' : '') + '"><div><b>' + (j + 1) + '. ' + esc(q.c.nm) + '</b> <span>예상 <em>' + ms2(q.t) + '</em> ±' + ms2(q.pm) + (q.est ? '(어림)' : '') + ' · ' + km(q.dist) + ' · 직선 ' + km(q.st) + '</span></div>' + (q.why ? '<i>' + esc(q.why) + '</i>' : '') + '<div class="dln">📻 「' + esc(dispOrder(q)) + '」<button data-dcp="' + j + '">복사</button><button data-dc="x' + q.i + '" aria-label="이 차 빼기">✕</button></div></div>'; }).join('');
    h += R.bad.map(function (q) { return '<div class="dcar"><div><b>' + esc(q.c.nm) + '</b> <span>길에 닿지 않는 자리 — 길 위로 옮겨 주십시오</span><button data-dc="x' + q.i + '">✕</button></div></div>'; }).join('');
    return h + '<p class="dnt">참고용 예측 — 상황실 시스템을 대체하지 않는다 · 최종 판단은 현장 경찰관. ±는 실측 없는 길의 시간 폭(「어림」 = 폭 자료가 없어 ±12%). 차 자리는 기기 안에서만 셈하고 어디에도 보내지 않는다.</p></details>'; }
  function dispClick(a) { if (a === 'clr') DCARS = []; else if (a === 'mid' || a === 'me') { if (DCARS.length >= 6) { note('최대 6대'); return; } var x = a === 'me' && me ? me.x : view.cx, y = a === 'me' && me ? me.y : view.cy; DN++; DCARS.push({ x: x, y: y, n: DN, nm: a === 'me' ? '내 차' : DN + '호' }); } else if (a.charAt(0) === 'x') DCARS.splice(+a.slice(1), 1); DRES = null; paint(); draw(); }
  /* ⏱ 예상·실제 도착 기록(tg_gg_arr) — 안내를 끝까지 마친 것만 · 좌표·목적지 이름 없이 날짜·시·요일 갈래·모드·거리·예상(폭)·실제 초 · 중요업무·모의 주행 안 남김 · 최근 200 */
  function arrAll() { try { var A = JSON.parse(localStorage.getItem('tg_gg_arr') || 'null'); return A && Array.isArray(A.l) ? A : { v: 1, l: [] }; } catch (e) { return { v: 1, l: [] }; } }
  function arrAdd(g, act) { try { if (!g || g.sim || sim || g.mode === 'v' || (dest && dest.vip) || !(act > 30) || !(g.pred > 30)) return; var A = arrAll(), d = new Date(g.t), w = d.getDay();
      A.l.push([d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2), d.getHours(), w === 0 || (window.TT && TT.isHol && TT.isHol(g.t)) ? 'h' : w === 6 ? 's' : 'w', g.mode, Math.round((g.dist || 0) / 100) / 10, Math.round(g.pred), g.lo ? Math.round(g.lo) : null, g.hi ? Math.round(g.hi) : null, Math.round(act)]);
      while (A.l.length > 200) A.l.shift(); localStorage.setItem('tg_gg_arr', JSON.stringify(A)); } catch (e) {} }
  function arrSum() { var L = arrAll().l, R = L.map(function (q) { return q[8] / q[5]; }).sort(function (a, b) { return a - b; }), inR = L.filter(function (q) { return q[6] != null && q[8] >= q[6] && q[8] <= q[7]; }).length, wr = L.filter(function (q) { return q[6] != null; }).length;
    return { n: L.length, med: R.length ? R[R.length >> 1] : null, inR: inR, wr: wr }; }
  /* ---------- v0.27.0 🚇 열차 안 신고 — 먼저 닿을 역(도착 예측 2단계 · ../js/station-reach.js · ../data/train-run-seoul.json) ----------
     관측(노선·마지막 역·방향·출발/정차 중·몇 초 전)과 순찰차 자리(GPS · 없으면 지도 가운데)는 이 화면 메모리에만 — 저장·전송 없음 · 역까지 길은 기기 안에서 셈
     결과는 후보·예상 · 열차는 시간표 기준 — v0.28.0 부터 📡 실시간 열차 위치에서 사람이 고른 열차가 있으면 그 관측(역·상태·수신 시각)으로 셈 */
  var SRD = null, SRP = null, SRS = { ln: null, i: -1, nx: -1, st: null, t0: null, unk: false, sel: null, all: 0, rt: null, tr: null, no: '', rtMsg: '' }, SRR = null, SRC = null, SRT = null;   /* t0 = 관측 시각(ms) — 「몇 초 전」을 고른 순간에서 거꾸로 · 지나는 시간을 계속 더한다 */
  var SRL = ['1호선', '2호선', '3호선', '4호선', '5호선', '6호선', '7호선', '8호선', '9호선', '신분당', '수인분당', '경의중앙', '공항', '우이신설', '신림선', '경춘', '서해선'];
  var SRE = null;   /* 역 둘레 큰 행사(공연 객석 500석↑ 끝 · 집회 신고 300명↑) — 사람 수 × 0.4(역으로 그 시간에 드는 몫 · 가정) ÷ 그 역 한 시간 평균 = 혼잡 몫 가산(0~1.5) */
  function srLoad() { if (SRP) return SRP; SRP = Promise.all([getJ('../data/train-run-seoul.json'), getJ('../data/station-events.json')]).then(function (a) { var j = a[0]; SRE = a[1]; if (j && window.SREACH) { SREACH.load(j); SRD = j; } return SRD; }); return SRP; }
  function srDT() { var d = new Date(), w = d.getDay(); return w === 0 || w === 6 || (window.TT && TT.isHol && TT.isHol(d.getTime())) ? 'we' : 'wd'; }   /* 토·일·공휴일 = 주말 배수 */
  function srEvents(path) { var out = [], ds = new Date(), d0 = ds.getFullYear() + '-' + ('0' + (ds.getMonth() + 1)).slice(-2) + '-' + ('0' + ds.getDate()).slice(-2); if (!SRE || !SRE.ev) return { list: out, date: d0 };
    var hh = function (t) { var q = String(t || '').split(':'); return +q[0] + (+q[1] || 0) / 60; };
    path.forEach(function (p) { var st0 = SRD.st[p.i], b = st0[1].replace(/\(.*?\)/, ''), L = SRE.ev[b] || [], per = st0[6] ? st0[6] / 19 : 0; if (!per) return;
      L.forEach(function (e) { if (e[0] !== d0) return; var a = e[1] === 'p' ? hh(e[3]) - 1 / 6 : hh(e[2]), z = e[1] === 'p' ? hh(e[3]) + 2 / 3 : hh(e[3]) + 0.5, add = Math.max(0, Math.min(1.5, 0.4 * e[4] / per));
        if (add >= 0.05) out.push({ st: b, date: d0, h0: Math.floor(a), h1: Math.floor(z) + 1, add: Math.round(add * 100) / 100, nm: e[5], kind: e[1], t: e[1] === 'p' ? e[3] : e[2] + '~' + e[3], ppl: e[4] }); }); });
    return { list: out, date: d0 }; }
  function srOpen(on) { var el = $('gSR'); if (!el) { el = document.createElement('div'); el.id = 'gSR'; el.setAttribute('role', 'dialog'); document.body.appendChild(el); el.addEventListener('input', function (e) { if (e.target && e.target.id === 'gSRno') { SRS.no = e.target.value.replace(/\D/g, '').slice(0, 6); SRS.tr = null; if (SRS.sel === 'rt') { SRS.st = null; SRS.t0 = null; SRS.sel = null; } clearTimeout(SRS.nt); SRS.nt = setTimeout(srPaint, 400); } }); } el.style.display = on ? 'block' : 'none'; document.body.classList.toggle('sr-on', !!on); clearInterval(SRT); SRT = null; if (on) { srPaint(); srLoad().then(srPaint); SRT = setInterval(function () { if (SRS.t0 && SRS.st) srPaint(true); }, 5000); } }
  function srHere() { return me ? { x: me.x, y: me.y, gps: 1 } : { x: view.cx, y: view.cy, gps: 0 }; }
  function srXY(s) { return [PX(s[4]), PY(s[3])]; }
  function srNb(i) { var ln = SRD.st[i][2], A = SRD.lk.filter(function (l) { return l[0] === i && SRD.st[l[1]][2] === ln; }), ok = A.filter(function (l) { return l[3]; }), o = []; (ok.length ? ok : A).forEach(function (l) { if (o.indexOf(l[1]) < 0) o.push(l[1]); }); return o; }   /* 같은 노선 이웃 — 역간거리와 맞은 이음 먼저 */
  function srMeas() { try { return JSON.parse(localStorage.getItem('tg_gg_meas') || 'null'); } catch (e) { return null; } }
  function srCalK() { try { var L = JSON.parse(localStorage.getItem('tg_gg_arr') || 'null'), m = MODE === 'e' ? 'e' : 'n', P2 = L && L.l ? L.l.filter(function (q) { return q[3] === m; }).map(function (q) { return [q[5], q[8]]; }) : []; return SREACH.calibrate(P2); } catch (e) { return { k: 1, n: 0, assumed: true }; } }
  function srCalc() { if (!SRD || !G || SRS.i < 0 || SRS.nx < 0 || !SRS.st || !SRS.t0) return null; var H0 = srHere(), path = SREACH.path(SRS.i, SRS.nx, 6), ck = srCalK(), key = Math.round(H0.x / 30) + ',' + Math.round(H0.y / 30) + ':' + path.map(function (p) { return p.i; }).join(',') + ':' + MODE + ':' + Math.floor(Date.now() / 60000);
    if (!SRC || SRC.key !== key) { var T0 = Date.now() / 1000, drives = {}, ex = {};
      path.forEach(function (p) { var st0 = SRD.st[p.i]; if (!st0[3]) return; var E = (st0[7] || []).map(function (e) { return { n: e[0], x: PX(e[2]), y: PY(e[1]) }; }), tgt = E.length ? E.slice().sort(function (a, b) { return Math.hypot(a.x - H0.x, a.y - H0.y) - Math.hypot(b.x - H0.x, b.y - H0.y); })[0] : { n: '', x: srXY(st0)[0], y: srXY(st0)[1] }, r = null;
        try { r = findRoute(H0.x, H0.y, tgt.x, tgt.y, T0, null); } catch (e) {} if (!r) return; var RG = rngOf(r, r.time), t = r.time * ck.k, sd = RG ? (RG[1] - r.time) * ck.k / 0.674 : t * 0.12; drives[p.i] = { sec: t, sd: Math.max(t * 0.06, Math.min(t * 0.35, sd)), dist: r.dist, est: !RG }; ex[p.i] = tgt; });
      SRC = { key: key, drives: drives, ex: ex }; }
    var EXN = {}; Object.keys(SRC.ex).forEach(function (k) { EXN[k] = SRC.ex[k].n; });
    var EV = srEvents(path), pl = SREACH.plan({ i: SRS.i, nx: SRS.nx, st: SRS.st, ago: (Date.now() - SRS.t0) / 1000, unk: SRS.unk }, SRC.drives, new Date().getHours(), { meas: srMeas(), n: 6, exits: EXN, events: EV.list, date: EV.date, dayType: srDT() }); pl.ev = EV.list; pl.drives = SRC.drives; pl.ex = SRC.ex; pl.here = H0; pl.cal = ck; SRR = pl; return pl; }
  /* ---------- v0.28.0 📡 실시간 열차 위치(중계 /swpos · 서울 열린데이터 realtimePosition) ----------
     부르는 것은 노선 이름 하나뿐(역·자리·관측은 보내지 않는다) · 「불러오기」를 눌렀을 때만 · 중계가 같은 호선을 60초 나눠 줌(열쇠 하루 1,000건을 역 도착 /swsub 와 나눠 씀)
     노선 위치만으로는 신고자 열차가 하나로 안 정해진다 → ②③(직전 역·방향) 또는 열차번호로 후보 2~3대를 보이고 사람이 고른다 · 저절로 정하지 않는다
     받은 값은 「역 + 진입/도착/출발/전역출발」 단위 — 역 사이 위치와 그 뒤 운행은 시간표 어림 · 못 받거나 고르지 않으면 ④ 시간표 어림(실시간 아님) */
  var SRAPI = { '신분당': '신분당선', '수인분당': '수인분당선', '경의중앙': '경의중앙선', '공항': '공항철도', '우이신설': '우이신설선', '경춘': '경춘선' }, SRTS = { 0: '진입', 1: '도착', 2: '출발', 3: '전 역 출발' };
  function srNbA(i) { var ln = SRD.st[i][2], o = []; SRD.lk.forEach(function (l) { if (l[0] === i && SRD.st[l[1]][2] === ln && o.indexOf(l[1]) < 0) o.push(l[1]); }); return o; }   /* 같은 노선 이웃 모두(역간거리가 안 맞은 이음도) — 방향 가리기용 */
  function srB(s) { return String(s || '').replace(/\(.*?\)/g, '').trim().replace(/종착$/, '').replace(/역$/, '').trim(); }   /* 종착역 표기에 「성수종착」처럼 붙는 것도 떼고 맞춘다 */
  function srFind(nm) { var b = srB(nm); for (var i = 0; i < SRD.st.length; i++) { var s = SRD.st[i]; if (s[2] === SRS.ln && s[3] && srB(s[1]) === b) return i; } return -1; }
  function srRTms(t) { var m = /^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d):(\d\d)/.exec(t.recptnDt || ''); return m ? Date.parse(m[1] + '-' + m[2] + '-' + m[3] + 'T' + m[4] + ':' + m[5] + ':' + m[6] + '+09:00') : NaN; }
  function srRTget() { if (!SRS.ln || (SRS.rt && SRS.rt.busy)) return; var ln = SRS.ln; SRS.rt = { busy: 1, ln: ln }; srPaint();
    getJ('../data/relay.json').then(function (r) { if (!r || !r.url) throw new Error('중계 주소를 못 읽었다'); return fetch(r.url + '/swpos/' + encodeURIComponent(SRAPI[ln] || ln), { cache: 'no-store' }); })
      .then(function (res) { return res.json().then(function (j) { return [res.status, j]; }); })
      .then(function (a) { var j = a[1] || {}, L = j.realtimePositionList, em = j.errorMessage || {}; if (SRS.ln !== ln) return;
        if (!Array.isArray(L)) throw new Error(j.err || em.message || j.message || ('HTTP ' + a[0]));
        var now = Date.now(); SRS.rt = { t: now, ln: ln, L: L.filter(function (t) { var ms = srRTms(t); return ms > 0 && now - ms < 600000; }) }; srPaint(); })
      .catch(function (e) { if (SRS.ln !== ln) return; SRS.rt = { t: Date.now(), ln: ln, err: String(e && e.message || e) }; srPaint(); }); }
  /* 관측한 직전 역 i · 다음 역 nx 가 있으면 그 줄(뒤 3역 + i + 앞 80역)이 방향의 기준 · 없으면 종착역이 있는 쪽 이웃 */
  function srSeq() { if (SRS.i < 0 || SRS.nx < 0) return null; var back = [], nb = srNbA(SRS.i).filter(function (n) { return n !== SRS.nx; }); if (nb.length === 1) back = SREACH.path(SRS.i, nb[0], 3).map(function (p) { return p.i; }).reverse();
    return back.concat([SRS.i, SRS.nx], SREACH.path(SRS.i, SRS.nx, 80).slice(1).map(function (p) { return p.i; })); }
  function srToward(S, tn, ud) { if (SRS.ln === '2호선' && (ud === '0' || ud === '1')) { var LP = srLoop(), q = LP.indexOf(S); if (q >= 0 && LP.length) return LP[(q + (ud === '0' ? 1 : LP.length - 1)) % LP.length]; } var b = srB(tn), out = srNbA(S).filter(function (n) { return n === S ? false : (srB(SRD.st[n][1]) === b || SREACH.path(S, n, 80).some(function (p) { return srB(SRD.st[p.i][1]) === b; })); }); return out.length === 1 ? out[0] : -1; }
  /* 2호선 본선은 고리라 종착역이 앞뒤 어디에나 있다 → 자료의 본선 차례(시청 201 → 을지로입구 202 …)가 updnLine 0 쪽이라는 것으로 가린다
     (2026-10-15 21:38→21:40 실측 · 같은 열차 두 번 받아 움직인 16대: 번호 커지는 쪽 8대 모두 0 · 작아지는 쪽 8대 모두 1 — v0.28.0~0.28.1 은 1 로 적어 방향이 뒤집혀 있었다) */
  function srLoop() { if (SRS.lp) return SRS.lp; var L = []; for (var i = 0; i < SRD.st.length; i++) if (SRD.st[i][2] === '2호선') L.push(i); for (var k = 2; k < L.length; k++) if (srNbA(L[k]).indexOf(L[0]) >= 0) { SRS.lp = L.slice(0, k + 1); return SRS.lp; } SRS.lp = []; return SRS.lp; }
  function srDir(t, back) { var tb = srB(t.statnTnm), fw = SREACH.path(SRS.i, SRS.nx, 80).some(function (p) { return srB(SRD.st[p.i][1]) === tb; }) || srB(SRD.st[SRS.nx][1]) === tb, bk = srB(SRD.st[SRS.i][1]) === tb || back.some(function (b) { return SREACH.path(SRS.i, b, 80).some(function (p) { return srB(SRD.st[p.i][1]) === tb; }) || srB(SRD.st[b][1]) === tb; });
    if (fw !== bk) return fw; if (SRS.ln === '2호선') { var L = srLoop(), a = L.indexOf(SRS.i), b = L.indexOf(SRS.nx); if (a >= 0 && b >= 0 && (t.updnLine === '0' || t.updnLine === '1')) return ((b - a + L.length) % L.length === 1) === (t.updnLine === '0'); } return null; }
  function srCand(all) { var R = SRS.rt; if (!R || !R.L || R.ln !== SRS.ln) return null; var no = String(SRS.no || '').replace(/\D/g, ''), seq = srSeq(), back = SRS.i >= 0 ? srNbA(SRS.i).filter(function (n) { return n !== SRS.nx; }) : [], out = [];
    R.L.forEach(function (t) { var S = srFind(t.statnNm); if (S < 0) return; var tn = String(t.trainNo || ''), d = null, dir = null;
      if (no) { if (tn.slice(-no.length) !== no) return; }
      else { if (!seq) return; var k = seq.indexOf(S), ki = seq.indexOf(SRS.i); if (k < 0 || k > ki + 1 || ki - k > 3) return; d = ki - k;
        dir = srDir(t, back); if (dir === false) return; }
      out.push({ t: t, S: S, d: d, dir: dir, ms: srRTms(t) }); });
    out.sort(function (a, b) { return (a.dir === true ? 0 : 1) - (b.dir === true ? 0 : 1) || Math.abs(a.d || 0) - Math.abs(b.d || 0) || b.ms - a.ms; }); return all ? out : out.slice(0, 3); }
  /* 고른 열차 → 관측(직전 역·다음 역·떠남/서 있음·관측 시각) — 진입은 「곧 선다」라 서 있음으로 어림 · 전 역 출발은 그 앞 역을 떠난 것으로 */
  function srPick(no) { var C = (srCand(1) || []).filter(function (c) { return String(c.t.trainNo) === no; })[0]; if (!C) return; var t = C.t, S = C.S, seq = srSeq(), k = seq ? seq.indexOf(S) : -1, nxS = k >= 0 && k + 1 < seq.length ? seq[k + 1] : srToward(S, t.statnTnm, t.updnLine), st = +t.trainSttus, i = S, nx = nxS, ob = st === 2 ? 'dep' : 'arr', note = '';
    if (nxS < 0) { SRS.rtMsg = '열차 ' + no + ' — 가는 쪽을 정하지 못했다(종착 ' + (t.statnTnm || '?') + ') · ②③을 골라 달라'; return; }
    if (st === 3) { var pv = k > 0 ? seq[k - 1] : -1; if (pv < 0) { var P = srNbA(S).filter(function (n) { return n !== nxS; }); pv = P.length === 1 ? P[0] : -1; } if (pv >= 0) { i = pv; nx = S; ob = 'dep'; } else note = '앞 역을 몰라 이 역에 서 있음으로 어림'; }
    if (st === 0) note = '진입 — 이 역에 서 있음으로 어림';
    SRS.i = i; SRS.nx = nx; SRS.st = ob; SRS.t0 = C.ms > 0 ? Math.min(Date.now(), C.ms) : Date.now(); SRS.unk = false; SRS.sel = 'rt'; SRS.tr = { no: no, nm: srB(t.statnNm), s: SRTS[st] || '', tn: t.statnTnm || '', at: String(t.recptnDt || '').slice(11, 19), note: note, ln: SRS.ln }; SRS.rtMsg = ''; }
  function srRTbox() { var R = SRS.rt, h = '<div class="srq srt"><p>📡 실시간 열차 위치 <small>노선 이름만 보낸다 · 누를 때만 · 같은 호선은 60초 나눠 받음</small></p>';
    h += '<div class="srk"><button data-sr="rt|get"' + (R && R.busy ? ' disabled' : '') + '>' + (R && R.busy ? '받는 중…' : R && R.L ? '다시 불러오기' : '불러오기') + '</button><input id="gSRno" inputmode="numeric" autocomplete="off" placeholder="열차번호(아는 때만)" value="' + esc(SRS.no || '') + '"></div>';
    if (R && R.err) h += '<p class="srn" style="margin-top:4px">받지 못했다(' + esc(R.err) + ') — 아래 ④ 시간표 어림으로(<b>실시간 아님</b>)</p>';
    if (R && R.L) { var C = srCand();
      if (!SRS.no && SRS.nx < 0) h += '<p class="srn" style="margin-top:4px">' + R.L.length + '대 받음 · ②③(열차가 마지막으로 선 역·가는 쪽)을 고르거나 열차번호를 넣으면 후보를 보인다</p>';
      else if (!C || !C.length) h += '<p class="srn" style="margin-top:4px">맞는 열차가 없다(' + R.L.length + '대 받음 · ' + Math.round((Date.now() - R.t) / 1000) + '초 전) — ④ 시간표 어림으로(<b>실시간 아님</b>)</p>';
      else h += '<div class="srk">' + C.map(function (c) { var t = c.t, on = SRS.tr && SRS.tr.no === String(t.trainNo), ago = c.ms > 0 ? Math.round((Date.now() - c.ms) / 1000) : null;
        return '<button data-sr="rt|' + esc(String(t.trainNo)) + '"' + (on ? ' class="on"' : '') + '>열차 ' + esc(String(t.trainNo)) + ' · ' + esc(srB(t.statnNm)) + ' ' + (SRTS[t.trainSttus] || '') + ' · ' + esc(srB(t.statnTnm)) + (/종착$/.test(String(t.statnTnm || '')) ? ' 종착' : '행') + (t.directAt === '1' || t.directAt === '7' ? ' · 급행' : '') + (t.lstcarAt === '1' ? ' · 막차' : '') + (c.dir === null && !SRS.no ? ' · <u>방향 확인</u>' : '') + (ago != null ? ' <u>' + ago + '초 전 수신</u>' : '') + '</button>'; }).join('') + '</div><p class="srn" style="margin-top:2px"><b>신고자가 탄 열차를 골라야 쓴다</b> — 저절로 정하지 않는다 · 고르지 않으면 ④ 시간표 어림</p>'; }
    if (SRS.rtMsg) h += '<p class="srn" style="margin-top:2px;font-weight:800">' + esc(SRS.rtMsg) + '</p>';
    return h + '</div>'; }
  function mmS(s) { var neg = s < 0; s = Math.abs(Math.round(s)); return (neg ? '−' : '') + Math.floor(s / 60) + ':' + ('0' + s % 60).slice(-2); }
  function srPaint(tick) { var el = $('gSR'); if (!el || el.style.display === 'none') return; var sy = el.scrollTop; var h = '<div class="srh"><b>🚇 열차 안 신고 — 먼저 닿을 역</b><button data-sr="x|" aria-label="닫기">✕</button></div>';
    if (!window.SREACH) { el.innerHTML = h + '<p class="srn">계산 모듈을 읽지 못했다</p>'; return; } if (!SRD) { el.innerHTML = h + '<p class="srn">역 자료를 읽는 중…</p>'; return; }
    var H0 = srHere(); h += '<div class="srq"><p>① 노선</p><div class="srk">' + SRL.map(function (l) { return '<button data-sr="ln|' + l + '"' + (SRS.ln === l ? ' class="on"' : '') + '>' + l.replace('호선', '') + (/\d/.test(l) ? '호선' : '') + '</button>'; }).join('') + '</div></div>';
    if (SRS.ln) { var L = SRD.st.map(function (s, i) { return [i, s]; }).filter(function (q) { return q[1][2] === SRS.ln && q[1][3]; }).map(function (q) { var xy = srXY(q[1]); return [q[0], q[1], Math.hypot(xy[0] - H0.x, xy[1] - H0.y)]; }).sort(function (a, b) { return a[2] - b[2]; });
      h += '<div class="srq"><p>② 열차가 마지막으로 선(지난) 역 <small>' + (H0.gps ? '내 자리' : '지도 가운데') + '에서 가까운 차례</small></p><div class="srk">' + (SRS.all ? L : L.slice(0, 8)).map(function (q) { return '<button data-sr="st|' + q[0] + '"' + (SRS.i === q[0] ? ' class="on"' : '') + '>' + esc(q[1][1].replace(/\(.*?\)/, '')) + ' <u>' + km(q[2]) + '</u></button>'; }).join('') + (L.length > 8 && !SRS.all ? '<button data-sr="all|">더 보기 ' + L.length + '</button>' : '') + '</div></div>'; }
    if (SRS.i >= 0) { var NB = srNb(SRS.i); h += '<div class="srq"><p>③ 가는 쪽</p><div class="srk">' + NB.map(function (n) { var P3 = SREACH.path(SRS.i, n, 3), far = P3.length ? SRD.st[P3[P3.length - 1].i][1] : ''; return '<button data-sr="nx|' + n + '"' + (SRS.nx === n ? ' class="on"' : '') + '>' + esc(SRD.st[n][1].replace(/\(.*?\)/, '')) + (far && P3.length > 1 ? ' → ' + esc(far.replace(/\(.*?\)/, '')) : '') + ' 쪽</button>'; }).join('') + '</div></div>';
      h += '<div class="srq"><p>④ 그 역에서 열차가</p><div class="srk"><button data-sr="ob|dep"' + (SRS.st === 'dep' ? ' class="on"' : '') + '>떠났다</button><button data-sr="ob|arr"' + (SRS.st === 'arr' ? ' class="on"' : '') + '>서 있다</button></div><div class="srk">' + [[0, '방금'], [30, '30초 전'], [60, '1분 전'], [120, '2분 전'], [-1, '모름']].map(function (a) { var on = SRS.sel === a[0]; return '<button data-sr="ag|' + a[0] + '"' + (on ? ' class="on"' : '') + '>' + a[1] + '</button>'; }).join('') + '</div></div>'; }
    if (SRS.ln) h += srRTbox();
    var R = SRS.nx >= 0 ? srCalc() : null; if (SRS.nx >= 0 && (!SRS.st || !SRS.t0)) h += '<p class="srn" style="font-weight:800">④ 「떠났다/서 있다」와 「언제」를 고르면 셈한다(미리 골라 두지 않는다 — 열차를 늦게 잡으면 경찰이 먼저 닿는다고 잘못 나온다)</p>';
    if (R) { var best = R.best; h += '<div class="srr">' + (best == null ? '<p class="srn">역까지 길을 찾지 못했다(길 묶음 밖?)</p>' : '<p class="srb">' + (R.weak ? '⛔ 먼저 닿기 어렵다 — 가장 높은 역도 ' + Math.round(R.cards.filter(function (c) { return c.i === best; })[0].p * 100) + '%' : R.close ? '⚖ 경합 — 기준(' + Math.round(R.target * 100) + '%)을 넘는 역이 없다 · 가장 높은 역' : '✅ 권고 — 선착 ' + Math.round(R.target * 100) + '% 넘는 가장 가까운 역') + '</p><p class="srn" style="margin-top:0">관측한 지 <b>' + Math.round((Date.now() - SRS.t0) / 1000) + '초</b> 지남' + (SRS.unk ? '(그 전에 몇 초가 지났는지 몰라 한 구간의 가운데로 셈 · 오차 큼)' : '') + ' — 5초마다 다시 셈 · ' + (R.here.gps ? '내 자리(GPS)' : '<b>지도 가운데</b>') + ' 기준</p>');
      h += R.cards.map(function (c) { if (c.p == null) return '<div class="src"><div class="h"><b>' + esc(c.nm.replace(/\(.*?\)/, '')) + '</b> <small>' + c.k + '번째 역</small></div><p class="srn">이 역까지 길을 못 찾았다</p></div>'; var pc = Math.round(c.p * 100), ex = R.ex[c.i], asm = c.walk.assumed || c.park.assumed || c.crowd.noData, d = R.drives[c.i];
        return '<div class="src' + (c.i === best ? ' best' : '') + (c.late ? ' late' : '') + '"><div class="h"><b>' + esc(c.nm.replace(/\(.*?\)/, '')) + '</b> <small>' + c.k + '번째 역' + (c.branch ? ' · 갈래 — 다른 쪽일 수 있음' : '') + '</small>' + (c.i === best ? '<em class="bd">' + (R.weak ? '가장 높음' : R.close ? '경합' : '권고') + '</em>' : '') + (asm ? '<em class="as">가정값</em>' : '') + '</div>'
          + '<div class="pb"><i style="width:' + pc + '%"></i><span>선착 ' + pc + '%</span></div>'
          + '<div class="tt">🚇 열차 <b>' + mmS(c.T) + '</b> ±' + Math.round(c.sdT) + '초 · 🚓 경찰 <b>' + mmS(c.P) + '</b> ±' + Math.round(c.sdP) + '초</div>'
          + '<div class="sl">' + (c.passed ? '⛔ 열차가 이 역을 이미 지났을 수 있다(떠난 지 한 구간보다 오래)' : c.late ? (c.p >= 0.5 ? '⚠ ' + Math.round(R.target * 100) + '%에 못 미침 — ' + Math.round(-c.slack) + '초 모자람' : '⛔ 열차가 먼저 닿을 가능성이 크다 — ' + Math.round(-c.slack) + '초 모자람(' + Math.round(R.target * 100) + '% 기준)') : '⏱ 출발 미룰 수 있는 시간 <b>' + Math.round(c.slack) + '초</b>') + '</div>'
          + '<div class="ex">🅿 ' + (ex && ex.n ? esc(ex.n) + '번 출구 쪽 정차' : '역 앞 정차') + ' · 주행 ' + km(d.dist) + ' ' + mmS(d.sec) + (d.est ? '(폭 어림)' : '') + ' · 세운 자리→출입구 ' + Math.round(c.park.sec) + '초' + (c.park.assumed ? '(가정)' : '(실측 ' + c.park.n + '번' + (c.park.other ? ' · 다른 출구' : '') + ')') + ' · 출입구→승강장 ' + Math.round(c.walk.sec) + '초' + (c.walk.assumed ? '(가정)' : '(실측 ' + c.walk.n + '번' + (c.walk.other ? ' · 다른 출구 ' + esc(c.walk.exit) + '번' : '') + ')') + (R.here.gps ? '' : ' · 지도 가운데에서 셈') + ' · 혼잡 몫 ×' + c.crowd.r + (c.crowd.noData ? '(자료 없음)' : c.crowd.dt === 'we' ? '(주말·공휴일)' : c.crowd.dt === 'wd' ? '(평일)' : '') + '</div>'
          + (c.crowd.ev > 0 ? '<div class="ex">' + R.ev.filter(function (e) { var hN = new Date().getHours(); return e.st === c.nm.replace(/\(.*?\)/, '') && hN >= e.h0 && hN < e.h1; }).map(function (e) { return (e.kind === 'p' ? '🎭 ' + esc(e.nm) + ' — ' + e.t + ' 끝(객석 ' + e.ppl.toLocaleString() + ')' : '📢 ' + esc(e.nm) + ' ' + e.t + '(신고 ' + e.ppl.toLocaleString() + '명)') + ' · 혼잡 +' + e.add + '(가정)'; }).join('<br>') + '</div>' : '')
          + (c.crowd.warn ? '<div class="wn">⚠ 하차 인파로 대상 식별 어려움 — 출구·개찰구 쪽 배치 권장</div>' : '')
          + '<button class="go" data-sr="go|' + c.i + '">이 역으로 안내</button></div>'; }).join('') + '</div>'; }
    h += '<p class="srn"><b>후보·예상 — 최종 판단은 현장 경찰관.</b> ' + (SRS.tr ? '열차 = <b>실시간 위치</b>(서울 열린데이터 · 열차 ' + esc(SRS.tr.no) + ' · ' + esc(SRS.tr.nm) + ' ' + esc(SRS.tr.s) + ' · ' + esc(SRS.tr.at) + ' 수신' + (SRS.tr.note ? ' · ' + esc(SRS.tr.note) : '') + ') — 역 단위 상태라 역 사이 위치·그 뒤 운행은 시간표(TAGO 평일 · ' + esc(SRD.made || '') + ' 구움) 어림. ' : '열차는 <b>실시간 아님</b> — 시간표(TAGO 평일 · ' + esc(SRD.made || '') + ' 구움) 기준(📡 실시간 열차 위치에서 열차를 고르지 않음). ') + '도로는 ' + (LIVE.m ? '통행속도 ' + esc(String(LIVE.made || '').slice(-5)) + ' 받음' : '<b>실시간 아님</b> — 제한속도·막힘 배율') + (R && R.cal && R.cal.n ? ' · 주행 보정 ×' + R.cal.k.toFixed(2) + '(안내 마친 ' + R.cal.n + '번' + (R.cal.assumed ? ' · 가정' : '') + ')' : '') + '. 「가정값」 = 정차 30초 · 세운 자리→출입구 60초 · 출입구→승강장 90초 · 행사 가산(역 둘레 공연 끝·집회 사람 × 0.4 ÷ 그 역 한 시간 평균 · 공연 = KOPIS 객석 · 집회 = 경찰청 「오늘의 주요집회」 신고 인원) · 혼잡 배수(⚙ 🚇 역 실측으로 3번 이상 재면 그 역은 실측). 순찰차 자리·관측은 기기 안에서만 셈하고 어디에도 보내지 않는다 · 저장하지 않는다(「이 역으로 안내」도 최근 목적지에 남기지 않음 — 안내를 끝까지 마치면 ⏱ 도착 기록에 날짜·시·거리만).</p>';
    var fo = document.activeElement && document.activeElement.id === 'gSRno', cp = fo ? document.activeElement.selectionStart : 0; el.innerHTML = h; if (tick) el.scrollTop = sy; if (fo) { var ni = $('gSRno'); if (ni) { ni.focus(); try { ni.setSelectionRange(cp, cp); } catch (e) {} } } }
  function srClick(v) { var k = v.split('|')[0], a = v.slice(k.length + 1);
    if (k === 'x') { srOpen(false); return; } if (k === 'rt') { if (a === 'get') { srRTget(); return; } srPick(a); srPaint(); return; } if (k === 'ln') { if (SRS.ln !== a) { SRS.rt = null; SRS.no = ''; } SRS.ln = a; SRS.i = -1; SRS.nx = -1; SRS.all = 0; SRS.st = null; SRS.t0 = null; SRS.sel = null; SRS.tr = null; SRS.rtMsg = ''; } else if (k === 'st') { SRS.i = +a; SRS.nx = -1; SRS.st = null; SRS.t0 = null; SRS.sel = null; SRS.tr = null; } else if (k === 'nx') { SRS.nx = +a; SRS.tr = null; if (SRS.sel === 'rt') { SRS.st = null; SRS.t0 = null; SRS.sel = null; } } else if (k === 'ob') { SRS.st = a; SRS.tr = null; if (SRS.sel === 'rt') { SRS.t0 = null; SRS.sel = null; } } else if (k === 'ag') { SRS.sel = +a; SRS.unk = +a < 0; SRS.t0 = Date.now() - Math.max(0, +a) * 1000; SRS.tr = null; } else if (k === 'all') SRS.all = 1;
    else if (k === 'go' && SRR) { var i = +a, s = SRD.st[i], ex = SRR.ex[i]; srOpen(false); if (ex) setDest(ex.x, ex.y, s[1].replace(/\(.*?\)/, '') + '역' + (ex.n ? ' ' + ex.n + '번 출구' : ''), false, true); return; }
    srPaint(); }
  function km(m) { return m >= 1000 ? (m / 1000).toFixed(m >= 10000 ? 0 : 1) + 'km' : Math.max(10, Math.round(m / 10) * 10) + 'm'; }
  function mmss(s) { s = Math.max(0, Math.round(s)); var m = Math.floor(s / 60); return m >= 60 ? Math.floor(m / 60) + '시간 ' + (m % 60) + '분' : m ? m + '분' : s + '초'; }
  /* 시간 폭 — 실시간 통행속도가 없는 길 몫(1 − live)만큼 calR 폭을 준다 · 중요업무·폭 표 없음·길 전체 실시간이면 null */
  function rngOf(r, t) { if (MODE === 'v' || !window.TT || !TT.calR || !(t > 0)) return null; var L = Math.max(0, Math.min(1, r.live || 0)); if (L >= 0.999) return null; var q = TT.calR(Date.now()); if (!q) return null; return [t * (1 - (1 - q[0]) * (1 - L)), t * (1 + (q[1] - 1) * (1 - L)), 1 - L]; }
  function mmR(a, b) { var x = Math.round(a / 60), y = Math.round(b / 60); if (x === y || b < 90) return mmss((a + b) / 2); if (y >= 60) return mmss(a) + '~' + mmss(b); return Math.max(1, x) + '~' + y + '분'; }
  function hmR(T, a, b, short) { var A = hm(T + a), B = hm(T + b); return A === B ? A : A + '~' + (short && A.slice(0, 3) === B.slice(0, 3) ? B.slice(3) : B); }
  function hm(T) { var d = new Date(T * 1000); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  var ARW = { L: '⬅', l: '↖', R: '➡', r: '↗', U: '↩', E: '🏁', S: '⬆' }, MKO = { L: '좌회전', l: '왼쪽 방향', R: '우회전', r: '오른쪽 방향', U: '유턴', E: '목적지', S: '직진' };
  /* 차로 안내 — OSM 에 차로별 진행 방향이 적힌 곳(서초 둘레 141줄뿐)은 차로 번호로, 그 밖은 꺾는 쪽 규칙(좌회전·유턴 = 1차로 · 우회전 = 맨 오른쪽)으로. 차로마다의 속도 자료는 어디에도 없다 — 「어느 차로가 빠르다」는 말은 하지 않는다 */
  /* v0.17.0 차로 — 몇 차로 가운데 어느 차로(차로 표가 있으면 그것 · 없으면 좌회전·유턴 = 1차로 · 우회전 = 맨 오른쪽) */
  function laneSet(m) { if (!m || m.e == null || m.k === 'E' || m.k === 'S') return null; var q = G.S[G.eS[m.e]], ti = q[G.eR[m.e] ? 16 : 15], want = m.k === 'U' ? 'reverse' : m.k === 'L' || m.k === 'l' ? 'left' : 'right', nL = q[10] || 0, lt = m.k === 'L' || m.k === 'l' || m.k === 'U';
    if (ti != null && ti >= 0) { var L = String(G.j.tl[ti]).split('|'), ok = []; L.forEach(function (x, i) { if (x.split(';').some(function (y) { return y.indexOf(want) >= 0; })) ok.push(i + 1); }); if (ok.length) return { n: L.length, ok: ok, tl: 1 }; }
    return { n: nL, ok: nL ? [lt ? 1 : nL] : [], lt: lt }; }
  function laneWord(s) { if (!s || !s.ok.length) return ''; return s.ok.length === 1 ? (s.ok[0] === 1 ? '1차로' : s.ok[0] === s.n ? '맨 오른쪽 차로' : s.ok[0] + '차로') : s.ok.join(', ') + '차로'; }
  function laneStrip(m) { var s = laneSet(m); if (!s || s.n < 2 || s.n > 8 || !s.ok.length) return ''; var ar = m.k === 'L' || m.k === 'l' ? '←' : m.k === 'U' ? '↶' : '→', h = ''; for (var i = 1; i <= s.n; i++) h += '<i class="' + (s.ok.indexOf(i) >= 0 ? 'on' : '') + '">' + (s.ok.indexOf(i) >= 0 ? ar : '↑') + '</i>'; return '<span class="lanes" aria-label="' + s.n + '개 차로 가운데 ' + laneWord(s) + '">' + h + '</span>'; }
  /* v0.20.0 버스전용차로 — OSM(gargo/buslane-seoul.json) · 길과 25m 안에 나란한 구간을 길 위 거리로(길마다 한 번) */
  var BUSL = null, BUSP = null;
  function busLoad() { if (!BUSP) BUSP = getJ('buslane-seoul.json').then(function (j) { if (!j || !j.l) { BUSP = null; return; } var g = {}; BUSL = j.l.map(function (q, i) { var f = q[2], o = new Float32Array(f.length); for (var k = 0; k < f.length; k += 2) { o[k] = PX(f[k] / 1e5); o[k + 1] = PY(f[k + 1] / 1e5); var c = Math.floor(o[k] / 300) + '_' + Math.floor(o[k + 1] / 300); (g[c] || (g[c] = {}))[i] = 1; } return { nm: q[0], k: q[1], p: o }; }); BUSL.g = g; if (route) route.bus = null; drawSoon(); }); return BUSP; }
  function busOn(r) { if (r.bus) return r.bus; if (!BUSL) return null; var P = r.pts, out = [], cur = null;
    for (var u = 0; u + 3 < P.length; u += 2) { var L = r.cum[u / 2 + 1] - r.cum[u / 2], n = Math.max(1, Math.ceil(L / 20)); for (var k = 0; k < n; k++) { var t = (k + .5) / n, x = P[u] + (P[u + 2] - P[u]) * t, y = P[u + 1] + (P[u + 3] - P[u + 1]) * t, s = r.cum[u / 2] + L * t, cells = BUSL.g[Math.floor(x / 300) + '_' + Math.floor(y / 300)], hit = null;
        if (cells) for (var id in cells) { var o = BUSL[id].p; for (var m = 0; m + 3 < o.length && !hit; m += 2) { var ax = o[m], ay = o[m + 1], vx = o[m + 2] - ax, vy = o[m + 3] - ay, l2 = vx * vx + vy * vy, tt = l2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2)) : 0; if (Math.hypot(ax + vx * tt - x, ay + vy * tt - y) < 25) hit = BUSL[id].k; } if (hit) break; }
        if (hit) { if (cur && s - cur[1] < 45) { cur[1] = s; if (hit === 'busway') cur[2] = 'busway'; } else { cur = [s, s, hit]; out.push(cur); } } } }
    r.bus = out.filter(function (q) { return q[1] - q[0] >= 100; }); return r.bus; }
  function busAhead(r, pos) { var B = r && busOn(r); if (!B) return null; for (var i = 0; i < B.length; i++) { var a = Math.max(B[i][0], pos), b = B[i][1]; if (b - a >= 150 && a - pos < 600) return { d: a - pos, len: b - a, k: B[i][2] }; } return null; }
  function emLane(nx, pos, r) { var bz = busAhead(r || route, pos); if (bz && (!nx || nx.k === 'S' || nx.d - pos > 300)) return { w: bz.k === 'busway' ? '중앙버스전용차로' : '버스전용차로', why: (bz.d > 30 ? km(bz.d) + ' 앞부터 ' : '') + km(bz.len) + ' · 긴급 통행 가능(§15③)' };
    if (!nx || nx.k === 'E' || nx.k === 'S' || nx.d - pos > 500) return { w: '1차로', why: '막히면 중앙선 쪽(§29①)' }; var s = laneSet(nx), lt = nx.k === 'L' || nx.k === 'l' || nx.k === 'U'; return { w: lt ? '1차로' : (s && s.n ? '맨 오른쪽 차로' : '맨 오른쪽'), why: lt ? '좌회전 앞' : '우회전 앞' }; }
  function laneHint(m) { if (!m || m.e == null || m.k === 'E' || m.k === 'S') return ''; var q = G.S[G.eS[m.e]], ti = q[G.eR[m.e] ? 16 : 15], want = m.k === 'U' ? 'reverse' : m.k === 'L' || m.k === 'l' ? 'left' : 'right', nL = q[10];
    if (ti != null && ti >= 0) { var L = String(G.j.tl[ti]).split('|'), ok = []; L.forEach(function (x, i) { if (x.split(';').some(function (y) { return y.indexOf(want) >= 0; })) ok.push(i + 1); }); if (ok.length) return L.length + '개 차로 가운데 <b>' + ok.join('·') + '차로</b>'; }
    return (m.k === 'L' || m.k === 'l' || m.k === 'U' ? '<b>1차로</b>(맨 왼쪽)' : '<b>맨 오른쪽 차로</b>') + (nL ? ' <em>· 이 길 ' + nL + '차로</em>' : ''); }
  function night() { var h = new Date().getHours(); return h >= 22 || h < 6; }
  function paint() {
    var top = $('gTop'), bot = $('gBot'), sg = $('gSig'), spd = $('gSpd');
    if (!route && cruise) { paintCruise(); return; }
    if (!route) { top.style.display = 'none'; sg.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = guide ? 'none' : 'flex';
      setH(bot, '<div class="hint">' + (dest ? (me ? '길을 찾는 중…' : '내 자리를 기다리는 중 — 위치를 허락하거나, 지도를 <b>길게 눌러</b> 「여기서 떠나기」를 고른다') : '목적지를 정한다 — 지도를 <b>길게 누르거나</b> 위에서 이름을 찾는다') + '</div>' + (dest ? '' : sigStat() + '<div class="btns" style="margin-top:10px"><button id="gCruise" class="go">▶ 켜놓고 다니기 — 앞 신호·소통</button><button data-sr="open|">🚇 열차 안 신고</button></div>') + (me && me.out ? '<div class="hint warn">지금 자리가 길 묶음 밖이다 — 시험판은 ' + AREA_KO + '과 둘레 2km 안에서만 길을 찾는다.</div>' : '')); return; }
    var r = route, now = Date.now() / 1000, pos = r.pos || 0, left = Math.max(0, r.dist - pos), frac = r.dist ? left / r.dist : 0, tLeft = r.tc ? Math.max(0, r.time - tAt(r, pos)) : r.time * frac;
    var nx = null, n2 = null; for (var i = 0; i < r.mans.length; i++) if (r.mans[i].d > pos + 5) { nx = r.mans[i]; n2 = r.mans[i + 1] || null; break; }
    var known = r.sigs.filter(function (g) { return g.s && g.s.kind !== 'avg'; }).length, wsum = 0; r.sigs.forEach(function (g) { wsum += g.tw || 0; });
    if (guide) { $('gFind').style.display = 'none'; top.style.display = 'flex';
      top.innerHTML = nx ? '<div class="arwc"><div class="arw">' + ARW[nx.k] + '</div>' + (n2 && nx.k !== 'E' ? '<small class="nx2">그다음 ' + ARW[n2.k] + ' ' + km(n2.d - nx.d) + '</small>' : '') + '</div><div class="tx"><b>' + km(nx.d - pos) + '</b>' + (nx.d - pos <= 300 && nx.k !== 'E' ? '<i class="cd"><u style="width:' + Math.max(2, Math.round((nx.d - pos) / 3)) + '%"></u></i>' : '') + '<span>' + (nx.k === 'E' ? '목적지' : MKO[nx.k]) + (nx.nm ? ' · ' + esc(nx.nm) : '') + (nx.sig ? ' <em>(' + esc(nx.sig) + ')</em>' : '') + '</span>' + (function () { var win = limAt(r, pos) >= 70 ? 2000 : 1000, near = nx.d - pos < win, st9 = near ? laneStrip(nx) : '', lh = near && !st9 ? laneHint(nx) : '', o = st9 ? '<small class="ln3">' + st9 + '<em>' + laneWord(laneSet(nx)) + '</em></small>' : lh ? '<small class="ln2">차로 — ' + lh + '</small>' : ''; if (MODE === 'e') { var el9 = emLane(nx, pos, r); o += '<small class="em">🚨 빠른 차로 <b>' + el9.w + '</b> · ' + el9.why + ' · 안전 확인</small>'; } return o; })() + '' + icLine(r, pos) + '</div>' : '';
      barPaint(r, pos);
      var VN = MODE === 'v' ? vipNow(r, pos) : null, vc = VN && !VN.err ? VN.base.cps[0] : null, vf = VN && !VN.err ? VN.fast.cps[0] : null;
      setH(bot, VN && !VN.err ? '<div class="eta vipe"><div><b>' + TT.hm(VN.base.at) + '</b><span>예상 도착 · ' + TT.mmss(VN.base.sec) + '</span></div><div class="fast"><b>' + TT.hm(VN.fast.at) + '</b><span>가장 이른 · ' + VN.fastV + 'km/h</span></div><button id="gMenu" class="mnu" aria-label="메뉴 — 안내 끝">≡</button></div><div class="mpop" id="gMpop"><button id="gStop" class="stop">⏹ 안내 끝</button><button id="gReplan" class="rp2">⟳ 경로 다시 찾기</button></div>' + (vc ? '<div class="vnext">다음 지점 <b>' + esc(vc.nm) + '</b> ' + km(vc.m) + ' — 예상 ' + TT.hm(vc.at) + ' · 가장 이른 ' + TT.hm(vf.at) + '</div>' : '') + '<div class="vn">📌 교차로 통제 개시는 「가장 이른 도착」 시각 기준 · 🔒 기기 안에서만</div>'
        : (VN && VN.err ? '<div class="vn">🔒 중요업무 시각을 셈하지 못했다 — ' + esc(VN.err) + ' · ⚙ 에서 범위를 본다(아래는 일반 계산)</div>' : '') + (function () { var RG2 = rngOf(r, tLeft); return '<div class="eta' + (RG2 ? ' rg' : '') + '"><button id="gReplan" class="rp" aria-label="경로 다시 찾기">⟳</button><div><b>' + (RG2 ? hmR(now, RG2[0], RG2[1], true) : hm(now + tLeft)) + '</b><span>도착' + (RG2 ? ' · 추정' : '') + '</span></div><div><b>' + (RG2 ? mmR(RG2[0], RG2[1]) : mmss(tLeft)) + '</b><span>남은 시간</span></div>'; })() + '<div><b>' + km(left) + '</b><span>남은 거리</span></div><button id="gMenu" class="mnu" aria-label="메뉴 — 안내 끝">≡</button></div><div class="mpop" id="gMpop"><button id="gStop" class="stop">⏹ 안내 끝</button><button id="gReplan" class="rp2">⟳ 경로 다시 찾기</button></div>');
      var lim = 0, rn = ''; for (var k = 0; k < r.lims.length; k++) if (r.lims[k][0] <= pos + 1) { lim = r.lims[k][1]; rn = r.lims[k][2]; } spd.style.display = 'flex'; var v = Math.round((me && me.spd || 0) * 3.6);
      spd.innerHTML = '<div class="lim">' + lim + '</div><div class="cur' + (v > lim + 2 ? ' over' : '') + '"><b>' + v + '</b><span>km/h</span></div>' + (rn && !guide ? '<div class="rn">' + esc(rn) + '</div>' : '')   /* 안내 중에는 내 차 밑 「지금 위치」 알약이 길 이름을 말한다 */;
      alrLoad(); riskLoad(); etaRefresh(); try { alrShow(alrAhead(routePoly(r)), r, pos); } catch (e) {}
    } else { top.style.display = 'none'; spd.style.display = 'none'; $('gFind').style.display = 'flex';
      var opn = [].map.call(bot.querySelectorAll('details'), function (d) { return d.open ? d.className : ''; });   /* v0.10.0 위치가 바뀔 때마다 다시 그려도 펼친 칸은 펼친 채 */
      var RG = rngOf(r, r.time);
      bot.innerHTML = '<div class="sum"><div class="big"><b>' + (RG ? mmR(RG[0], RG[1]) : mmss(r.time)) + '</b> <span>' + km(r.dist) + ' · ' + (RG ? hmR(now, RG[0], RG[1]) : hm(now + r.time)) + ' 도착</span>' + (RG ? '<em class="est">실측 없는 길 ' + Math.round(RG[2] * 100) + '% · 추정 폭</em>' : '') + '</div>'
        + '<div class="mode"><button data-mode="n" class="' + (MODE === 'n' ? 'on' : '') + '">🚗 일반</button><button data-mode="e" class="' + (MODE === 'e' ? 'on' : '') + '">🚨 긴급 출동</button>' + (window.TT && TT.VIP_ON ? '<button data-mode="v" class="' + (MODE === 'v' ? 'on' : '') + '">🔒 중요업무</button>' : '') + '</div>' + (MODE === 'v' ? vipBox(r) : '')
        + '<div class="sub">신호 ' + r.sigs.length + '곳 · 지금 색을 아는 곳 ' + known + ' · 나머지 ' + (r.sigs.length - known) + '곳은 어림' + (NOSIG() ? ' · <b>신호 기다림을 셈에서 뺐다</b>(닿을 때 적색이면 알려 준다 — 통과는 운전자 판단)' : (LIVER ? ' · 신호에 서는 시간은 통행속도에 들어 있다(꺾는 데 ' + mmss(wsum) + ' 더함)' : ' · 신호 기다림 ' + mmss(wsum) + ' 포함')) + '<br>'
          + (LIVE.m ? '🚗 통행속도 반영(' + esc(LIVE.made || '') + ' 받음 · 길의 ' + Math.round(r.live * 100) + '%에 값' + (r.cong.length ? ' · <b class="r" title="큰길 25·15km/h · 자동차전용 50·30km/h 아래(앱 기준)">막히는 구간 ' + r.cong.length + '곳</b>' : ' · 막히는 구간 없음') + ')' : '🚗 통행속도 없음(받은 지 20분 넘음) — 제한속도로 셈') + ' · 신호·막힘이 없다면 ' + mmss(r.free) + '<br>🚦 신호값 ' + (SIG.idx ? esc(String(SIG.idx.made || '')) + ' 구움 · 5분마다 새 값을 확인한다' : '없음') + '</div>'
        + '<div class="btns"><button id="gGo" class="go">▶ 안내 시작</button><button id="gSim">모의 주행</button><button id="gClr">지우기</button></div>'
        + (MODE === 'v' || dest.vip ? '' : dispHtml())
        + (MODE === 'v' || dest.vip ? '' : '<div class="hand"><span>이 목적지를</span><button data-pl="h">🏠 집으로</button><button data-pl="o">🚓 근무지로</button><button data-pl="f">⭐ 즐겨찾기</button></div>')
        + (MODE === 'v' || dest.vip ? '' : '<div class="hand"><span>이 목적지를 다른 앱으로</span><button data-hand="map">🗺 데이터지도</button><button data-hand="tmap">티맵</button><button data-hand="kakao">카카오맵</button><button data-hand="naver">네이버지도</button></div>') + (window.TT && TT.calN() ? '<div class="cap">실측 보정 ×' + TT.calK().toFixed(2) + '(안내를 끝까지 마친 ' + TT.calN() + '번) 이면 ' + hm(now + r.time * TT.calK()) + ' 도착</div>' : '')
        + riskHtml(r) + '<details class="steps"><summary>가는 차례 ' + r.mans.length + '곳 · 신호 ' + r.sigs.length + '곳</summary>' + r.mans.map(function (m) { return '<div class="st"><i>' + ARW[m.k] + '</i><b>' + km(m.d) + '</b><span>' + MKO[m.k] + (m.nm ? ' · ' + esc(m.nm) : '') + (m.sig ? ' (' + esc(m.sig) + ')' : '') + '</span></div>'; }).join('')
        + '<div class="cap">지나는 신호(닿을 때의 예상 — 계획값)</div>' + r.sigs.map(function (g) { var s = g.s; return '<div class="st"><i>🚦</i><b>' + km(g.d) + '</b><span>' + esc(g.nm) + ' · ' + (g.mv === 'Rt' ? '우회전' : g.mv === 'Lt' ? '좌회전' : g.mv === 'U' ? '유턴' : '직진') + ' — ' + (g.mv === 'Rt' || g.mv === 'U' ? '신호 자료 없음(' + (g.mv === 'Rt' ? '우회전' : '유턴') + ' · 어림 ' + Math.round(g.w) + '초로 셈)' : !s ? '<em>모름</em>(자료 없음 · 어림 ' + Math.round(g.w) + '초로 셈)' : s.kind === 'avg' ? '<em>지금 색 모름</em> · 평균 기다림 ' + Math.round(s.wait) + '초' : s.green ? '<b class="g">녹색</b> 통과 예상' : '<b class="r">적색</b> ' + Math.round(s.wait) + '초 기다림 예상') + '</span></div>'; }).join('') + '</details></div>'; [].forEach.call(bot.querySelectorAll('details'), function (d) { if (opn.indexOf(d.className) >= 0) d.open = true; }); }
    document.body.classList.toggle('mode-e', MODE === 'e'); document.body.classList.toggle('mode-v', MODE === 'v');   /* v0.24.0 모드를 화면 색으로 */
    if (guide) voiceTick(r, pos, nx, n2);
    nextTab(guide && nx && n2 && nx.k !== 'E' ? n2 : null, nx);
    /* 다음 신호 판 — 핵심 */
    var ns = null; for (var q = 0; q < r.sigs.length; q++) if (r.sigs[q].d > pos - 5) { ns = r.sigs[q]; break; }
    if (!ns || !(guide || sim)) { sg.style.display = 'none'; return; }
    var dd = Math.max(0, ns.d - pos), st = ns.mv === 'St' || ns.mv === 'Lt' ? sigAt(ns.no, now, ns.side, ns.mv) : null, vNow = me && me.spd > 2 ? me.spd : ns.lim / 3.6, eta = dd / Math.max(1.5, Math.min(vNow, ns.lim / 3.6)), at = ns.mv === 'St' || ns.mv === 'Lt' ? sigAt(ns.no, now + eta, ns.side, ns.mv) : null, h = '';
    sg.style.display = 'block'; if (guide) { var tb = $('gTop').getBoundingClientRect(), tn = $('gNext'), tnb = tn && tn.style.display !== 'none' ? tn.getBoundingClientRect() : null; sg.style.top = Math.round((tnb && tnb.height ? tnb.bottom : tb.bottom) + 6) + 'px'; } sg.className = 'sig ' + (!st || st.kind === 'avg' ? 'unk' : st.green ? 'grn' : 'red');
    var MVA = { St: '⬆', Lt: '⬅', Rt: '➡', U: '↩' }, mvk = ns.mv === 'Lt' ? '좌회전' : ns.mv === 'Rt' ? '우회전' : ns.mv === 'U' ? '유턴' : '직진', nmh = '<div class="nm"><b>' + esc(ns.nm) + '</b><span>' + km(dd) + ' · ' + mvk + '</span></div>';
    sg.classList.add('cp'); if (!sg._tg) { sg._tg = 1; sg.addEventListener('click', function () { sg.classList.toggle('open'); clearTimeout(sg._tm); if (sg.classList.contains('open')) sg._tm = setTimeout(function () { sg.classList.remove('open'); }, 6000); }); }   /* v0.21.0 누르면 6초 펼침 */   /* v0.17.0 한 줄 꼴 — 화살표 · 남은 초 · 이름은 작게 오른쪽 */
    if (ns.mv === 'Rt' || ns.mv === 'U') h += '<div class="c1"><b class="ar">' + MVA[ns.mv] + '</b><span class="tx1">신호 없음 · 보행자·직진 차</span>' + nmh + '</div>';
    else if (!st) h += '<div class="c1"><b class="ar">' + MVA[ns.mv] + '</b><span class="tx1">신호 자료 없음 — 눈으로</span>' + nmh + '</div>';
    else if (st.kind === 'avg') h += '<div class="c1"><b class="ar">' + MVA[ns.mv] + '</b><span class="tx1">색 모름 · 평균 대기 ' + Math.round(st.wait) + '초</span>' + nmh + '</div>';
    else { h += '<div class="c1"><b class="ar">' + MVA[ns.mv] + '</b><div class="now"><i></i><b><small>' + (st.green ? '녹색' : '적색') + ' </small>' + Math.ceil(st.remain) + '<small>초</small></b></div>' + nmh + '</div>';
      if (at && at.kind !== 'avg') { h += '<div class="ln">닿으면(' + Math.round(eta) + '초 뒤) ' + (at.green ? '<b class="g">녹색</b> <em>(' + Math.floor(at.remain) + '초 남음)</em>' : '<b class="r">적색</b> · ' + Math.ceil(at.wait) + '초 기다림') + '</div>';
        if (!at.green && NOSIG()) h += '<div class="ln adv">🚨 닿을 때 <b class="r">적색</b> — 좌우 확인 · <b>' + emLane(nx, pos, r).w + '</b>로</div>';
        else if (!at.green && !night() && dd > 80) { var adv = advise(ns, dd, now); if (adv) h += '<div class="ln adv"><b>시속 ' + adv.v + 'km</b>쯤이면 녹색 <em>(제한 ' + ns.lim + ' 안 · 서두르지 않는다)</em></div>'; else h += '<div class="ln">이번 녹색엔 못 닿음 — 서두르지 않는다</div>'; }
        else if (!at.green && night()) h += '<div class="ln">밤 22~06시 속도 안내 없음</div>'; }
      h += '<div class="src">' + (st.kind === 'pl' ? '계획값' : '이어 셈') + ' · 눈으로 확인</div>'; }
    sg.innerHTML = h;
    if (guide && voiceOn && st && st.kind !== 'avg' && !st.green && st.remain <= 4 && st.remain > 0.5 && dd < 60 && me && !(me.spd > 1.5) && lastSay.gr !== ns.no + ':' + Math.floor(now / 30)) { lastSay.gr = ns.no + ':' + Math.floor(now / 30); say('곧 녹색', 1); }   /* v0.24.0 서 있을 때 녹색 4초 전 */
    if (guide && voiceOn && MODE === 'e' && at && at.kind !== 'avg' && !at.green && dd < 150 && dd > 40 && lastSay.er !== ns.no) { lastSay.er = ns.no; say('적색 교차로입니다. 좌우 확인', 2); }   /* v0.24.0 긴급 출동 — 닿을 때 적색 */
    if (guide && voiceOn && st && st.kind !== 'avg' && at && at.kind !== 'avg' && dd < 260 && dd > 120 && lastSay.sig !== ns.no) { lastSay.sig = ns.no; say('앞 ' + ns.nm + ' 신호, ' + (at.green ? '녹색 통과 예상' : '적색, ' + Math.ceil(at.wait) + '초 대기 예상'), 1); }
  }
  /* 제한속도 안에서 녹색에 닿는 속도(시속 20km 이상 · 5 단위로 내림) — 없으면 null. 지금 적색일 때만 묻는다 */
  /* v0.16.0 음성 안내 한 번 돌기 — 그림 그릴 때마다 부름(말은 단계마다 한 번) */
  var LASTSAY = '', OVS = 0;
  function turnWords(r, nx, n2, pos, stage) { if (nx.k === 'E') return '목적지'; var ic = (r.ics || []).filter(function (o) { return Math.abs(o.s - nx.d) < 300 && o.k !== '휴게소' && o.k !== '쉼터'; })[0], t = (ic ? ic.nm + '에서 ' : '') + MKO[nx.k] + (nx.nm ? ', ' + nx.nm + ' 방향' : '');
    if (stage === 0 || stage === 3) { var lw = MODE === 'e' ? emLane(nx, pos, r).w : laneWord(laneSet(nx)); if (lw) t += '. ' + lw + (stage === 3 ? '로 미리 이동' : ''); }   /* 3 = 1km·500m 미리 알림(차로가 셋 넘을 때) */
    if (n2 && n2.k !== 'E' && n2.d - nx.d < 150) t += '. 이어서 ' + MKO[n2.k]; return t; }
  function voiceTick(r, pos, nx, n2) { if (!voiceOn) return; var hw = limAt(r, pos) >= 70;
    if (nx) { var dm = nx.d - pos, ls9 = laneSet(nx), many = ls9 && ls9.n >= 3, ST = hw ? [[2100, 1700, '2킬로미터 앞 '], [1100, 800, '1킬로미터 앞 '], [550, 380, '500미터 앞 '], [150, 25, '곧 ']] : (many ? [[1100, 800, '1킬로미터 앞 ', 3], [550, 380, '500미터 앞 ', 3]] : []).concat([[320, 200, ''], [80, 25, '곧 ']]);
      for (var i = 0; i < ST.length; i++) { var a = ST[i]; if (dm <= a[0] && dm > a[1]) { var key = nx.d + ':' + i; if (lastSay.man !== key) { lastSay.man = key; var last = i === ST.length - 1; say((a[2] || Math.round(dm / 50) * 50 + '미터 앞 ') + turnWords(r, nx, n2, pos, a[3] || (i === 0 && !last ? 0 : 1)), last ? 2 : 1); } break; } } }
    (r.cong || []).forEach(function (c) { var ahead = c[0] - pos; if (c[2] >= 2 && ahead > 300 && ahead < 700 && !(lastSay.cg && lastSay.cg[c[0]])) { (lastSay.cg = lastSay.cg || {})[c[0]] = 1; say('약 ' + Math.round(ahead / 100) * 100 + '미터 앞부터 정체, 약 ' + (c[1] - c[0] >= 1000 ? (Math.round((c[1] - c[0]) / 100) / 10) + '킬로미터' : Math.round((c[1] - c[0]) / 50) * 50 + '미터'), 0); } });
    var L = limAt(r, pos), v = me && me.spd > 0 && !sim ? me.spd * 3.6 : 0;
    if (MODE === 'n' && !(dest && dest.vip) && L > 0 && v > L + 10) { if (!OVS) OVS = Date.now(); if (Date.now() - OVS > 5000 && Date.now() - (lastSay.ov || 0) > 30000) { lastSay.ov = Date.now(); say('제한속도 ' + L + '킬로미터 구간입니다', 0); } } else OVS = 0; }
  function etaWords(r) { var t = r.time, RG = rngOf(r, t); if (RG) t = (RG[0] + RG[1]) / 2; var d = new Date(Date.now() + t * 1000), h = d.getHours(), m = d.getMinutes(); return '도착 예정 ' + (h < 12 ? '오전 ' : '오후 ') + ((h % 12) || 12) + '시 ' + (m ? m + '분' : '') + ', 약 ' + Math.max(1, Math.round(t / 60)) + '분'; }
  function sayAgain() { if (!guide || !route) return; var r = route, pos = r.pos || 0, nx = null, n2 = null; for (var i = 0; i < r.mans.length; i++) if (r.mans[i].d > pos + 5) { nx = r.mans[i]; n2 = r.mans[i + 1] || null; break; } if (!nx) return; var was = voiceOn; voiceOn = true; say(km(nx.d - pos).replace('km', '킬로미터').replace('m', '미터') + ' 앞 ' + turnWords(r, nx, n2, pos, 0) + '. ' + etaWords(r), 2); voiceOn = was; }
  function advise(ns, dd, now) { for (var v = ns.lim; v >= 20; v -= 5) { var a = sigAt(ns.no, now + dd / (v / 3.6), ns.side, ns.mv); if (a && a.kind !== 'avg' && a.green && a.remain > 4) return { v: v }; } return null; }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function say(t) { if (!voiceOn || !window.speechSynthesis) return; var lv = null; if (MODE === 'v' || (dest && dest.vip)) { lv = (speechSynthesis.getVoices() || []).filter(function (v) { return /^ko/i.test(v.lang) && v.localService; })[0]; if (!lv) return; } try { var pr = arguments[1] == null ? 2 : arguments[1]; if (pr < 2 && speechSynthesis.speaking && (speechSynthesis.pending || pr < 1)) return; var u = new SpeechSynthesisUtterance(t); if (lv) u.voice = lv; u.lang = 'ko-KR'; u.rate = (CF && CF.vrate) || 1.05; if (pr >= 2) speechSynthesis.cancel(); speechSynthesis.speak(u); LASTSAY = t; } catch (e) {} }   /* pri 2 = 끊고 말함(곧 회전·경로 이탈·시작) · 1 = 줄 섬(신호·첫 회전 단계) · 0 = 하던 말이 있으면 버림(정체·제한속도) */

  /* ---------- 안내 ---------- */
  var wake = null;
  /* ---------- v0.6.0 켜놓고 다니기(목적지 없이) — 소유자 「평소에 교통상황·교차로 신호값을 기본으로 · 그냥 켜놓고 다니는 모드」 ----------
     내 자리를 따라가며(진행 방향이 위) 소통 색과 둘레 신호를 보이고, **내가 가는 길을 곧장 따라가면 처음 만나는 신호**를 내 진행 방향의 값으로 보인다.
     길을 따라가는 법: 지금 선 줄에서 진행 방향 쪽 줄을 잡고, 갈림길마다 가장 덜 꺾이는(40° 안) 줄로 900m 까지. 곧장 갈 줄이 없으면(막다른 길·꺾어야 하는 삼거리) 거기서 멈춘다 */
  var cruise = false;
  function segEdges(seg) { var out = [], k; for (k = G.oHead[G.S[seg][0]]; k < G.oHead[G.S[seg][0] + 1]; k++) if (G.eS[G.oList[k]] === seg) out.push(G.oList[k]); for (k = G.oHead[G.S[seg][1]]; k < G.oHead[G.S[seg][1] + 1]; k++) if (G.eS[G.oList[k]] === seg && out.indexOf(G.oList[k]) < 0) out.push(G.oList[k]); return out; }
  /* v0.6.1 독립 검수 반영 — 가까운 줄 여럿(맞은편 차로·교차로의 가로지르는 길) 중 내 진행 방향에 맞는 줄을 고른다 · 맞는 것이 없으면 이름·제한속도도 비운다(남의 길 값을 보이지 않는다) */
  /* ---------- v0.9.0 알림 — 소유자 「일상적으로 틀어 놓고 쓸 만큼」 · 자료 data/gargo-alerts-seoul.json(수집 쪽 세션 · 행정안전부 표준데이터) ----------
     카메라 = 관리기관이 경찰(cam[7] 'p')이고 제한속도가 적힌 것만(2,368대 · 구청 카메라 1,907대는 주정차 등 — 알리지 않는다) · 카메라 방향은 자료에 없어 「내 길 위 30m 안 · 앞」만 · 어린이보호구역 = 시설 점에서 250m 안(구역 경계가 아니다 — 표지를 본다)
     제한속도는 자료에 적힌 값 그대로 말한다(권고가 아니다 · 밤에도 같다) */
  var ALR = null, ALRP = null, ALS = {};
  function alrLoad() { if (ALRP) return; ALRP = getJ('../data/gargo-alerts-seoul.json').then(function (j) { if (!j || !j.cam) { ALRP = null; return; } var g = {}, put = function (o) { var k = Math.floor(o.x / 500) + '_' + Math.floor(o.y / 500); (g[k] || (g[k] = [])).push(o); };
      j.cam.forEach(function (c) { if (c[2] == null || !(c[2] > 0) || c[7] !== 'p') return;   /* 경찰청 관리(서울특별시경찰청 · 속도·신호 단속)이고 제한속도가 적힌 것만 — 구청 카메라(주정차 등 · 제한이 적힌 227대도 뜻 확인 전)는 뺀다 */ put({ t: 'c', x: PX(c[0]), y: PY(c[1]), lim: c[2], rd: c[5] || '', id: 'c' + c[0] + ',' + c[1] }); });
      (j.sz || []).forEach(function (z) { put({ t: 'z', x: PX(z[0]), y: PY(z[1]), kd: z[2] || '', nm: z[3] || '', id: 'z' + z[0] + ',' + z[1] }); }); ALR = g; }); }
  /* poly = [x, y, 앞으로 거리 m, …](내 자리에서 시작) → 앞의 카메라(길 위 30m 안 · 가장 가까운 것) · 250m 안의 보호구역 시설 */
  function alrAhead(poly) { if (!ALR || !poly || poly.length < 6) return null; var x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, i; for (i = 0; i < poly.length; i += 3) { x0 = Math.min(x0, poly[i]); x1 = Math.max(x1, poly[i]); y0 = Math.min(y0, poly[i + 1]); y1 = Math.max(y1, poly[i + 1]); }
    var cam = null, zone = null; for (var gx = Math.floor((x0 - 260) / 500); gx <= Math.floor((x1 + 260) / 500); gx++) for (var gy = Math.floor((y0 - 260) / 500); gy <= Math.floor((y1 + 260) / 500); gy++) (ALR[gx + '_' + gy] || []).forEach(function (o) {
      if (o.t === 'z') { var dz = Math.hypot(o.x - poly[0], o.y - poly[1]); if (dz < 250 && (!zone || dz < zone.dz)) zone = { nm: o.nm, kd: o.kd, dz: dz, id: o.id }; return; }
      for (var k = 0; k + 5 < poly.length; k += 3) { var ax = poly[k], ay = poly[k + 1], bx = poly[k + 3], by = poly[k + 4], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((o.x - ax) * vx + (o.y - ay) * vy) / l2)) : 0;
        if (Math.hypot(ax + vx * t - o.x, ay + vy * t - o.y) < 30) { var d = poly[k + 2] + t * (poly[k + 5] - poly[k + 2]); if (d > 5 && (!cam || d < cam.d)) cam = { d: d, lim: o.lim, rd: o.rd, id: o.id }; break; } } });
    return cam || zone ? { cam: cam, zone: zone } : null; }
  function alrShow(A, r, pos) { var el = $('gAlr'); if (!el) { el = document.createElement('div'); el.id = 'gAlr'; el.style.cssText = 'position:fixed;left:8px;z-index:4;bottom:calc(178px + env(safe-area-inset-bottom));display:none;flex-direction:column;gap:6px;max-width:70vw'; document.body.appendChild(el); }
    if (!(guide || cruise) || (!A && !(r && guide))) { el.style.display = 'none'; return; } A = A || {}; var h = '', CD = [];   /* 카드는 [거리, 그림] 으로 모았다가 가까운 둘만 */
    if (A.cam && A.cam.d < 800) { CD.push([A.cam.d, dcard('c', A.cam.d, '단속 카메라', '제한 ' + A.cam.lim)]);
      if (A.cam.d < 400 && !ALS[A.cam.id]) { ALS[A.cam.id] = Date.now(); say('앞에 단속 카메라가 있습니다. 제한속도 ' + A.cam.lim); } }
    if (r && guide) { var rk = (routeMarks(r) || []).filter(function (m) { return m.t === 'r' && m.s - pos > 0 && m.s - pos < 400; })[0]; if (rk) { CD.push([rk.s - pos, dcard('r', rk.s - pos, '사고 다발 교차로', rk.nm + ' · 10년 ' + rk.n + '건')]); if (!ALS[rk.id]) { ALS[rk.id] = Date.now(); say('앞 사고 다발 교차로, ' + rk.nm, 0); } } }
    if (r && guide) { var wk = (routeMarks(r) || []).filter(function (m) { return m.t === 'w' && m.s - pos > -30 && m.s - pos < 500; })[0]; if (wk) { CD.push([Math.max(0, wk.s - pos) - 1, dcard('w', wk.s - pos, wk.full ? '전면 통제' : '공사·통제', wk.nm)]); if (!ALS[wk.id]) { ALS[wk.id] = Date.now(); say('앞 ' + (wk.full ? '전면 통제' : '공사 구간') + '입니다', 0); } } }
    if (A.zone) { CD.push([A.zone.dz, dcard('z', A.zone.dz, '어린이보호구역', A.zone.nm || '표지 확인')]);
      if (!ALS[A.zone.id]) { ALS[A.zone.id] = Date.now(); say('어린이보호구역입니다'); } }
    h = CD.sort(function (a, b) { return a[0] - b[0]; }).slice(0, 2).map(function (x) { return x[1]; }).join('');
    el.innerHTML = h; el.style.display = h ? 'flex' : 'none'; }
  /* v0.19.0 위험 카드 = 표지 + 큰 남은 거리 + 이름 */
  function dcard(t, d, ttl, sub) { var ic = t === 'c' ? '<svg viewBox="0 0 24 24" width="26" height="26"><rect x="3" y="7" width="18" height="12" rx="2" fill="#fff"/><circle cx="12" cy="13" r="3.6" fill="#111827"/><rect x="8" y="4.5" width="8" height="3" rx="1" fill="#fff"/></svg>' : t === 'w' ? '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M12 1.5 22.5 12 12 22.5 1.5 12z" fill="#f97316" stroke="#111827" stroke-width="1.4"/><path d="M8 15.5h8M9.5 12.5h5M11 9.5h2" stroke="#111827" stroke-width="1.8"/></svg>' : t === 'z' ? '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M12 2 23 21H1z" fill="#facc15" stroke="#111827" stroke-width="1.6"/><circle cx="12" cy="11" r="2" fill="#111827"/><path d="M12 13v4M10 19l2-2 2 2" stroke="#111827" stroke-width="1.8" fill="none"/></svg>' : '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M12 2 23 21H1z" fill="#fff" stroke="#dc2626" stroke-width="2.4"/><path d="M12 8v6" stroke="#111827" stroke-width="2.6"/><circle cx="12" cy="17.3" r="1.4" fill="#111827"/></svg>';
    return '<div class="dk dk-' + t + '"><i>' + ic + '</i><b>' + km(Math.max(0, d)) + '</b><span><em>' + esc(ttl) + '</em>' + esc(sub || '') + '</span></div>'; }
  /* 안내 중 — 내 길 앞 800m 를 [x, y, 앞 거리] 로 */
  /* ---------- v0.10.0 ⚠ 이 길 주의 교차로 — 교통 온톨로지 코어 v1(datamap ontology-core) 질문 4 · 표 = risk-six.json(tools/gargo-risk.py 가 core-six.json 에서 값 그대로 뽑음) ----------
     경로가 교차로 가운데에서 35m 안을 지나면 그 교차로를 「지나는 교차로」로 본다(근사). 사고는 교차로 둘레 70m 안 100m 칸을 묶은 TAAS 2016~2025 · 앱이 정한 「위험 점수」는 없다 — 10년 사고가 많은 차례로만 보인다 */
  var RISK = null, RISKP = null, RISKJ = null;
  function riskLoad() { if (RISKP) return RISKP; RISKP = getJ('risk-six.json').then(function (j) { if (!j || !j.rows) { RISKP = null; return null; } var g = {}; j.rows.forEach(function (q) { var o = { x: PX(q[2]), y: PY(q[3]), q: q }, k = Math.floor(o.x / 300) + '_' + Math.floor(o.y / 300); (g[k] || (g[k] = [])).push(o); }); RISK = g; RISKJ = j; return j; }); return RISKP; }
  function riskOn(r) { if (!RISK || !r || !r.pts) return null; if (r.risk) return r.risk; var hit = {}, i;
    for (i = 0; i + 3 < r.pts.length; i += 2) { var ax = r.pts[i], ay = r.pts[i + 1], bx = r.pts[i + 2], by = r.pts[i + 3], vx = bx - ax, vy = by - ay, l2 = vx * vx + vy * vy, k0 = r.cum[i / 2];
      for (var gx = Math.floor((Math.min(ax, bx) - 35) / 300); gx <= Math.floor((Math.max(ax, bx) + 35) / 300); gx++) for (var gy = Math.floor((Math.min(ay, by) - 35) / 300); gy <= Math.floor((Math.max(ay, by) + 35) / 300); gy++) (RISK[gx + '_' + gy] || []).forEach(function (o) {
        var t = l2 ? Math.max(0, Math.min(1, ((o.x - ax) * vx + (o.y - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - o.x, ay + vy * t - o.y); if (d > 35) return;
        var h = hit[o.q[0]]; if (!h || d < h.off) hit[o.q[0]] = { q: o.q, off: d, d: k0 + Math.sqrt(l2) * t }; }); }
    r.risk = Object.keys(hit).map(function (k) { return hit[k]; }).sort(function (a, b) { return b.q[4] - a.q[4] || a.d - b.d; }); return r.risk; }
  function riskHtml(r) { var L = riskOn(r); if (!RISKJ) { riskLoad().then(function (j) { if (j && route === r && !guide) paint(); }); return ''; } if (!L) return '';
    var V = RISKJ.vio || {}, W = RISKJ.law || {};
    if (!L.length) return '<details class="steps rk"><summary>⚠ 이 길 주의 교차로 — 지나는 교차로 둘레에 사고 칸이 없다</summary><div class="cap">' + esc(RISKJ.note || '') + '</div></details>';
    var top = L.slice(0, 8), more = L.length - top.length;
    return '<details class="steps rk"><summary>⚠ 이 길 주의 교차로 ' + L.length + '곳 — 10년 사고 많은 차례: ' + top.slice(0, 2).map(function (h) { return esc(h.q[1]) + ' ' + h.q[4] + '건'; }).join(' · ') + '</summary>'
      + top.map(function (h) { var q = h.q, w = W[q[9]] && W[q[9]][0]; return '<div class="st"><i>⚠</i><b>' + km(h.d) + '</b><span><b class="nm">' + esc(q[1]) + '</b> · 10년 <b>' + q[4] + '</b>건(최근 3해 ' + q[13].join('·') + ')' + (q[5] ? ' · <b class="r">사망 ' + q[5] + '</b>' : '') + ' · 중상 ' + q[6] + ' · 보행자 ' + q[7] + ' · 밤 ' + Math.round(q[8] / q[4] * 100) + '%'
        + (q[9] ? '<br>주 위반 <b>' + esc(V[q[9]] || q[9]) + '</b>(' + q[10] + '건)' + (w ? ' — ' + esc(w[0]) + ' · ' + esc(w[1]) : '') : '') + (q[11] ? ' · 📷 카메라 ' + q[11] : '') + (q[12] ? ' · 교통과 조치 이력 ' + q[12] + '건' : '') + '</span></div>'; }).join('')
      + (more > 0 ? '<div class="cap">그 밖 ' + more + '곳(사고 적은 차례)</div>' : '') + '<div class="cap">' + esc(RISKJ.note || '') + ' · 경로가 교차로 가운데 35m 안을 지날 때만 넣었다 · 데이터지도에서 교차로를 누르면 「🧩 교차로 관계 보기」(서초)</div></details>'; }
  /* ---------- v0.11.0 🔒 중요업무 — 길(경로선) → 구간 목록 → 공통 모듈(TT.vipTwo) · 기기 안에서만 셈 · 저장 안 함 ----------
     구간 = 길 줄 하나 · 꺾임 = 그 줄 끝이 안내하는 꺾는 곳(mans) · 진출입로 = 자동차전용(등급 1~2)과 일반 길(3~) 사이를 넘을 때 · 터널 = 이름에 「터널·지하차도」(길 자료에 터널 표시가 따로 없어 이름으로 어림)
     지점(체크포인트) = 지나는 신호 교차로 + 목적지 · 지금 자리(pos)부터만 셈 */
  function vipSegs(r, pos) { if (!r || !r.es) return []; pos = pos || 0; var out = [], d = 0, mk = {}, sk = {}; r.mans.forEach(function (m) { if (m.k !== 'E' && m.k !== 'S') mk[Math.round(m.d)] = 1; }); r.sigs.forEach(function (g) { sk[Math.round(g.d)] = g.nm; });
    function near(o, x) { for (var j = -2; j <= 2; j++) if (o[Math.round(x) + j] != null) return o[Math.round(x) + j]; return null; }
    r.es.forEach(function (e, i) { var q = G.S[G.eS[e]], d0 = r.tc[i] ? r.tc[i][0] : d, d1 = r.tc[i + 1] ? r.tc[i + 1][0] : r.dist, m = Math.max(0, d1 - Math.max(d0, pos)); d = d1; if (m <= 0.5) return;   /* 줄 끝 거리 = 길 모양을 그대로 잰 tc(첫 줄은 내 자리에서 잘린 길이) */
      var nm = q[5] >= 0 ? G.j.names[q[5]] : '', nx = r.es[i + 1] != null ? G.S[G.eS[r.es[i + 1]]] : null, ramp = !!(nx && ((q[4] <= 2) !== (nx[4] <= 2)));
      out.push({ m: m, turn: !!near(mk, d1), ramp: ramp, tunnel: /터널|지하차도/.test(nm), cp: i === r.es.length - 1 ? (dest && dest.nm || '목적지') : near(sk, d1) }); });
    return out; }
  function vipNow(r, pos) { if (!window.TT) return null; var C = TT.cfg(); return TT.vipTwo(vipSegs(r, pos), { base: VIPB || C.vipV, fast: VIPF, t0: Date.now(), mid: pos > 5 }); }
  function vipBox(r) { var V = vipNow(r, 0), C = TT.cfg(); if (!V || V.err) return '<div class="vip"><b>계산하지 못했다</b>' + (V && V.err ? ' — ' + esc(V.err) : '') + '</div>';
    var nx = V.base.cps[0], bt = function (v) { return '<button data-vipb="' + v + '" class="' + ((VIPB || C.vipV) === v ? 'on' : '') + '">' + v + '</button>'; };
    return '<div class="vip"><div class="vh">🔒 중요업무 <span>신호 대기 0 · 회전·진출입 감속은 셈 · 기기 안에서만 셈하고 남기지 않는다</span></div>'
      + '<div class="vs"><span>속도</span>' + [60, 70, 80, 90, 100].map(bt).join('') + '<span>빨리 간다</span><button data-vipf="1" class="' + (VIPF ? 'on' : '') + '">' + (VIPF ? VIPF + 'km/h ✎' : '직접 입력') + '</button>' + (VIPF ? '<button data-vipf="x">✕</button>' : '') + '</div>'
      + '<div class="v2"><div><b>' + TT.hm(V.base.at) + '</b><span>예상 도착 · ' + TT.fmt(V.base.sec) + ' · ' + V.base.v + 'km/h</span></div><div class="fast"><b>' + TT.hm(V.fast.at) + '</b><span>가장 이른 도착 · ' + TT.fmt(V.fast.sec) + ' · ' + V.fastV + 'km/h' + (V.typed ? '' : '(직접 입력 없음 — 기준값)') + '</span></div></div>'
      + '<div class="vn">📌 교차로 통제 개시는 <b>「가장 이른 도착」</b> 시각 기준</div>'
      + (nx && V.base.cps.length > 1 ? '<details class="steps vcp"><summary>지점별 통과 예정 ' + V.base.cps.length + '곳</summary>' + V.base.cps.map(function (c, i) { var f = V.fast.cps[i]; return '<div class="st"><i>📍</i><b>' + km(c.m) + '</b><span>' + esc(c.nm) + ' — 예상 ' + TT.hm(c.at) + ' · 가장 이른 ' + TT.hm(f.at) + '</span></div>'; }).join('') + '</details>' : '')
      + '<div class="cap">계산 속도는 도착 시각을 내려는 값이지 주행 속도 안내가 아니다 · 회전 ' + C.turnS + '초 · 진출입 ' + C.rampS + '초 · 출발·정지 ' + C.accS + '초(앱 제안값 · ⚙ 에서 바꾼다)</div></div>'; }
  function routePoly(r) { var pos = r.pos || 0, out = [], i; for (i = 0; i + 1 < r.cum.length; i++) { if (r.cum[i + 1] < pos) continue; if (r.cum[i] > pos + 800) break; out.push(r.pts[i * 2], r.pts[i * 2 + 1], r.cum[i] - pos); } var j = Math.min(i, r.cum.length - 1); out.push(r.pts[j * 2], r.pts[j * 2 + 1], r.cum[j] - pos); if (me && out.length) { out[0] = me.x; out[1] = me.y; out[2] = 0; } return out; }
  /* 켜놓고 다니기 — ahead() 가 걸은 길 줄들(es)로 앞 800m */
  function aheadPoly(A) { if (!A || !A.es || !A.es.length || !me) return null; var out = [me.x, me.y, 0], d = 0, px = me.x, py = me.y;
    A.es.forEach(function (e, n) { var P = G.SP[G.eS[e]], m = P.length / 2, k, st = 0; if (n === 0) { var bd = 1e12; for (k = 0; k < m; k++) { var u = (G.eR[e] ? m - 1 - k : k) * 2, dd = Math.hypot(P[u] - me.x, P[u + 1] - me.y); if (dd < bd) { bd = dd; st = k; } } }
      for (k = st; k < m; k++) { var u2 = (G.eR[e] ? m - 1 - k : k) * 2, x = P[u2], y = P[u2 + 1]; d += Math.hypot(x - px, y - py); px = x; py = y; if (d > 820) return; out.push(x, y, d); } }); return out; }
  /* 안내 중 남은 시간 — 같은 길을 지금 소통·신호로 1분마다 다시 셈(길은 그대로 · 시간·신호 예측만 새로) */
  /* 경로 소통 막대(카카오내비 참고 · v0.13.0) — 남은 길 [pos, dist] 를 아래 → 위로 · 실시간 값 있는 곳(kn)은 초록, 그 안의 서행·정체(cong)는 주황·빨강, 값 없는 곳은 회색(막힘 배율로 셈) · 신호 = 흰 점 · 맨 위 🏁 */
  /* v0.15.0 고속도로 모드 — 나들목 목록(ic-capital.json · 처음 길을 찾을 때 한 번 받음) · 길에서 40m 안에 드는 나들목을 지나는 자리(m)로 */
  var ICJ = null, ICP = null;
  function icLoad() { if (!ICP) ICP = getJ('ic-capital.json').then(function (j) { if (j && j.pts) { ICJ = j.pts.map(function (q) { return { nm: q[0], k: q[1], p: q[2].map(function (a) { return [PX(a[0]), PY(a[1])]; }) }; }); if (route) { route.ics = null; paint(); } } return ICJ; }); return ICP; }
  function icOn(r) { if (!ICJ || !r || !r.pts) return null; var P = r.pts, x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, i, out = [];
    for (i = 0; i < P.length; i += 2) { if (P[i] < x0) x0 = P[i]; if (P[i] > x1) x1 = P[i]; if (P[i + 1] < y0) y0 = P[i + 1]; if (P[i + 1] > y1) y1 = P[i + 1]; }
    ICJ.forEach(function (g) { var best = null; g.p.forEach(function (q) { if (q[0] < x0 - 60 || q[0] > x1 + 60 || q[1] < y0 - 60 || q[1] > y1 + 60) return; for (var u = 0; u + 3 < P.length; u += 2) { var ax = P[u], ay = P[u + 1], vx = P[u + 2] - ax, vy = P[u + 3] - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((q[0] - ax) * vx + (q[1] - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - q[0], ay + vy * t - q[1]); if (d <= 40 && (!best || d < best.d)) best = { d: d, s: r.cum[u / 2] + t * (r.cum[u / 2 + 1] - r.cum[u / 2]) }; } });
      if (best) out.push({ nm: g.nm, k: g.k, s: best.s }); });
    out.sort(function (a, b) { return a.s - b.s; }); return out.filter(function (o, i) { return !i || o.nm !== out[i - 1].nm; }); }
  function limAt(r, pos) { var L = 0; (r.lims || []).forEach(function (q) { if (q[0] <= pos + 1) L = q[1]; }); return L; }
  function icLine(r, pos) { if (!r.ics) r.ics = icOn(r); if (!r.ics || limAt(r, pos) < 70) return ''; var t0 = tAt(r, pos), A = r.ics.filter(function (o) { return o.s > pos + 20 && o.s - pos < 15000; }).slice(0, window.innerWidth >= 560 ? 3 : 2);   /* 폰 폭은 둘(셋이면 잘렸다) */ if (!A.length) return '';
    return '<small class="ic">' + A.map(function (o) { return (o.k === '휴게소' || o.k === '쉼터' ? '☕ ' : '🛣 ') + '<b>' + esc(o.nm) + '</b> ' + km(o.s - pos) + ' · ' + mmss(Math.max(0, tAt(r, o.s) - t0)); }).join(' › ') + '</small>'; }
  /* v0.18.0 「그다음」 꼬리 칸 — 회전 칸 바로 밑 왼쪽(상용 내비 세 앱 공통) */
  function nextTab(n2, nx) { var el = $('gNext'); if (!el) return; el.style.display = 'none'; return;   /* v0.21.0 「그다음」은 회전 화살표 밑으로(공간) — 이 칸은 쓰지 않는다 */ var tb = $('gTop').getBoundingClientRect(); el.style.top = Math.round(tb.bottom - 2) + 'px'; el.style.display = 'flex'; el.innerHTML = '<span>그다음</span><b>' + ARW[n2.k] + '</b><em>' + km(n2.d - nx.d) + '</em>'; }
  /* v0.18.0 「지금 위치」 — 서울 행정동(dong-seoul.json · 안내·켜놓고 다니기 때 한 번 받음) · 내 자리가 30m 넘게 움직일 때만 다시 셈 */
  var DONG = null, DONGP = null, DONGC = { x: 1e12, y: 1e12, nm: '' };
  function dongLoad() { if (!DONGP) DONGP = getJ('dong-seoul.json').then(function (j) { if (!j || !j.d) { DONGP = null; return; } DONG = j.d.map(function (d) { var R = d[1].map(function (a) { var o = new Float32Array(a.length); for (var i = 0; i < a.length; i += 2) { o[i] = PX(a[i] / 1e5); o[i + 1] = PY(a[i + 1] / 1e5); } return o; }), bb = [1e12, -1e12, 1e12, -1e12]; R.forEach(function (o) { for (var i = 0; i < o.length; i += 2) { if (o[i] < bb[0]) bb[0] = o[i]; if (o[i] > bb[1]) bb[1] = o[i]; if (o[i + 1] < bb[2]) bb[2] = o[i + 1]; if (o[i + 1] > bb[3]) bb[3] = o[i + 1]; } }); return { nm: d[0], R: R, bb: bb }; }); DONGC.x = 1e12; drawSoon(); }); return DONGP; }
  function dongAt(x, y) { if (!DONG) return ''; if (Math.hypot(x - DONGC.x, y - DONGC.y) < 30) return DONGC.nm; var nm = ''; for (var k = 0; k < DONG.length && !nm; k++) { var d = DONG[k], b = d.bb; if (x < b[0] || x > b[1] || y < b[2] || y > b[3]) continue; for (var r = 0; r < d.R.length && !nm; r++) { var o = d.R[r], c = false; for (var i = 0, j = o.length - 2; i < o.length; j = i, i += 2) { if (((o[i + 1] > y) !== (o[j + 1] > y)) && (x < (o[j] - o[i]) * (y - o[i + 1]) / (o[j + 1] - o[i + 1]) + o[i])) c = !c; } if (c) nm = d.nm; } } DONGC = { x: x, y: y, nm: nm }; return nm; }
  function hereText() { if (!me) return ''; var dn = dongAt(me.x, me.y), rd = ''; if (route && guide) { var p = route.pos || 0; (route.lims || []).forEach(function (q) { if (q[0] <= p + 1 && q[2]) rd = q[2]; }); } return [dn, rd].filter(Boolean).join(' · '); }
  /* v0.19.0 길 위 표시(소통 막대·위험 카드) — 길마다 한 번 셈(자료가 다 와야 저장) */
  function routeMarks(r) { if (r.mk) return r.mk; if (!ALR || !RISK) return null; var P = r.pts, out = [], x0 = 1e12, x1 = -1e12, y0 = 1e12, y1 = -1e12, i;
    for (i = 0; i < P.length; i += 2) { if (P[i] < x0) x0 = P[i]; if (P[i] > x1) x1 = P[i]; if (P[i + 1] < y0) y0 = P[i + 1]; if (P[i + 1] > y1) y1 = P[i + 1]; }
    function proj(x, y, lim) { var best = null; for (var u = 0; u + 3 < P.length; u += 2) { var ax = P[u], ay = P[u + 1], vx = P[u + 2] - ax, vy = P[u + 3] - ay, l2 = vx * vx + vy * vy, t = l2 ? Math.max(0, Math.min(1, ((x - ax) * vx + (y - ay) * vy) / l2)) : 0, d = Math.hypot(ax + vx * t - x, ay + vy * t - y); if (d <= lim && (!best || d < best.d)) best = { d: d, s: r.cum[u / 2] + t * (r.cum[u / 2 + 1] - r.cum[u / 2]) }; } return best; }
    for (var gx = Math.floor((x0 - 100) / 500); gx <= Math.floor((x1 + 100) / 500); gx++) for (var gy = Math.floor((y0 - 100) / 500); gy <= Math.floor((y1 + 100) / 500); gy++) (ALR[gx + '_' + gy] || []).forEach(function (o) { var b = proj(o.x, o.y, o.t === 'z' ? 60 : 30); if (b) out.push(o.t === 'z' ? { s: b.s, t: 'z', nm: o.nm || '어린이보호구역', id: o.id } : { s: b.s, t: 'c', nm: '단속 카메라 · 제한 ' + o.lim, lim: o.lim, id: o.id }); });
    (riskOn(r) || []).forEach(function (h) { if (h.q[4] >= 50) out.push({ s: h.d, t: 'r', nm: h.q[1], n: h.q[4], id: 'r' + h.q[0] }); });
    (r.accs || []).forEach(function (a) { out.push({ s: a[0], t: 'w', nm: a[1], full: a[2], id: 'w' + a[0] + a[1] }); });
    out.sort(function (a, b) { return a.s - b.s; }); r.mk = out; return out; }
  function barPaint(r, pos) { var el = $('gBar'); if (!el) return; var left = r.dist - pos; if (!(left > 30)) { el.innerHTML = ''; return; }
    var Y = function (d) { return Math.max(0, Math.min(100, (d - pos) / left * 100)); }, h = '';
    (r.kn || []).forEach(function (q) { if (q[1] <= pos) return; h += '<i class="k0" style="bottom:' + Y(Math.max(pos, q[0])).toFixed(1) + '%;height:' + (Y(q[1]) - Y(Math.max(pos, q[0]))).toFixed(1) + '%"></i>'; });
    (r.cong || []).forEach(function (q) { if (q[1] <= pos) return; h += '<i class="k' + q[2] + '" style="bottom:' + Y(Math.max(pos, q[0])).toFixed(1) + '%;height:' + (Y(q[1]) - Y(Math.max(pos, q[0]))).toFixed(1) + '%"></i>'; });
    (r.sigs || []).forEach(function (g) { if (g.d <= pos || g.si < 0) return; h += '<b style="bottom:' + Y(g.d).toFixed(1) + '%"></b>'; });
    var mk = '', last = -99; (routeMarks(r) || []).forEach(function (m) { if (m.s <= pos) return; var y = Y(m.s); if (Math.abs(y - last) < 6) return; last = y; mk += '<u class="mk m-' + m.t + '" style="bottom:' + y.toFixed(1) + '%">' + (m.t === 'c' ? '📷' : m.t === 'z' ? '🏫' : m.t === 'w' ? '🚧' : '⚠') + '</u>'; });   /* v0.19.0 길 위 표시 · 6% 안에 겹치면 앞의 것만 */
    el.innerHTML = '<span class="fl">🏁</span><div class="tr">' + h + '</div>' + mk + '<span class="me"></span>';
    /* 자리 — 위 안내 판·신호 판 바로 밑(🏁 자리 30px)에서 속도 표지·카메라 줄 위까지 · 판 높이가 바뀌면 따라간다 */
    var y0 = 8, y1 = window.innerHeight * 0.7; [$('gTop'), $('gSig')].forEach(function (x) { if (!x) return; var b = x.getBoundingClientRect(); if (b.height > 0 && b.bottom > y0) y0 = b.bottom; });
    var sp = $('gSpd'); if (sp) { var bs = sp.getBoundingClientRect(); if (bs.height > 0) y1 = bs.top - 66; } var hh = y1 - (y0 + 30); if (hh < 60) { el.style.visibility = 'hidden'; return; } el.style.visibility = ''; el.style.top = Math.round(y0 + 30) + 'px'; el.style.height = Math.round(hh) + 'px'; el.setAttribute('aria-label', '남은 길 ' + km(left) + ' · 실시간 소통 ' + Math.round((r.live || 0) * 100) + '%'); }
  function tAt(r, pos) { var T = r.tc; if (!T || !T.length) return r.time * (r.dist ? pos / r.dist : 0); for (var i = 1; i < T.length; i++) if (T[i][0] >= pos) { var a = T[i - 1], b = T[i], f = b[0] > a[0] ? (pos - a[0]) / (b[0] - a[0]) : 0; return a[1] + f * (b[1] - a[1]); } return T[T.length - 1][1]; }
  var ETAT = 0;
  function etaRefresh() { if (!guide || sim || !route || !route.es || Date.now() - ETAT < 60000) return; ETAT = Date.now(); try { var r = route, done = tAt(r, r.pos || 0), n = shape(r.es, r.a, r.b, Date.now() / 1000 - done);
      if (n && n.dist > 0) { r.time = n.time; r.tc = n.tc; r.sigs = n.sigs; r.cong = n.cong; r.live = n.live; r.free = n.free; r.etaAt = Date.now(); } } catch (e) {} }
  function ahead() { if (!me || !G || me.out || !me.hk) return null; var C = nearSegs(me.x, me.y, 45, 24); if (!C.length) return null; var a = null, best = -1, k0 = 1e9;
    C.forEach(function (o) { segEdges(o.seg).forEach(function (e) { var eb = G.eR[e] ? (o.brg + 180) % 360 : o.brg, df = Math.abs(angDiff(me.hd, eb)); if (df > 60) return; var k = df + o.d * 1.5; if (k < k0) { k0 = k; best = e; a = o; } }); });
    if (best < 0) return { seg: -1, e: -1, nm: '', lim: 0, cls: 0, live: null, sig: null, sigs: [], off: 1 };
    var q = G.S[a.seg], out = { seg: a.seg, e: best, nm: q[5] >= 0 ? G.j.names[q[5]] : '', lim: q[3] || 30, cls: q[4], live: eLive(best), sig: null, sigs: [], es: [best] };
    var p = G.SP[a.seg], al = 0, tot = 0, u; for (u = 0; u + 3 < p.length; u += 2) { var l = Math.hypot(p[u + 2] - p[u], p[u + 3] - p[u + 1]); if (u < a.u) al += l; else if (u === a.u) al += l * a.t; tot += l; }
    /* 닿는 시각 = 줄마다 min(지금 속도, 그 줄 제한속도) — 제한속도를 넘는 속도로 닿는 것을 셈하지 않는다 */
    var fr = tot ? al / tot : 0, e = best, d0 = eLen(e) * (G.eR[e] ? fr : 1 - fr), dist = d0, now = Date.now() / 1000, v = me.spd > 2 ? me.spd : 0, vo = function (x) { return Math.max(3, Math.min(v || eSpd(x) / 3.6 * 0.6, eSpd(x) / 3.6)); }, eta = d0 / vo(e);
    function put(sc, x, more) { var known = sc.si >= 0, sg = known ? G.sig[sc.si] : XS[sc.xi - 1], one = { nm: sg.nm, no: known ? sg.no : '', x: sg.x, y: sg.y, d: dist, side: sc.side, unk: !known, mv: sc.mv, eta: eta }; for (var kk in more) one[kk] = more[kk]; out.sigs.push(one); if (!out.sig) out.sig = one; }
    for (var step = 0; step < 60 && dist < CF.fwd; step++) { var nd = G.eB[e], f = -1, fd = 40, f2 = -1, fd2 = 1e9, any = -1;
      for (var i = G.oHead[nd]; i < G.oHead[nd + 1]; i++) { var g = G.oList[i]; if (G.eB[g] === G.eA[e] && G.eS[g] === G.eS[e]) continue; if (any < 0) any = g; var d2 = Math.abs(angDiff(eBrgIn(e), eBrgOut(g))); if (d2 < fd) { if (f >= 0) { f2 = f; fd2 = fd; } fd = d2; f = g; } else if (d2 < fd2) { f2 = g; fd2 = d2; } }
      if (f < 0) { var sx = any >= 0 ? sigCost(e, any, now) : null; if (sx) put(sx, 0, { noSt: 1 }); break; }   /* 곧장 갈 줄이 없어도 신호가 있으면 알린다 */
      var amb = f2 >= 0 && fd2 - fd < 10 && G.S[G.eS[f2]][5] !== G.S[G.eS[f]][5], sc = sigCost(e, f, now); if (sc) put(sc, 0, amb ? { amb: 1 } : {}); if (amb) break;
      dist += eLen(f); eta += eLen(f) / vo(f); e = f; out.es.push(f); }
    return out; }
  function sigUse(g) { return !g.unk && !g.noSt && !g.amb && g.mv === 'St'; }   /* 「내 방향(직진) 값」으로 보여도 되는가 */
  function sigWhy(g) { return g.unk ? '이 신호는 <b>자료가 없다</b> — 눈으로 본다' : g.noSt ? '여기서 곧장 가는 길이 없다(꺾어야 한다) — 내 방향 값을 <b>가리지 못한다</b> · 눈으로' : g.amb ? '갈림이 비슷해 어느 길로 가는지 <b>못 가린다</b> — 눈으로' : '길이 꺾여 들어간다 — 직진 값을 <b>쓰지 않는다</b> · 눈으로'; }
  var CRA = null;
  function drawAhead(dark, now) { if (!CRA || !CRA.sigs) return; var k = Math.max(1, CF.sz || 1), boxes = [];
    CRA.sigs.slice().sort(function (a, b) { return a.d - b.d; }).forEach(function (g, i) { var q = W2S(g.x, g.y), st = sigUse(g) ? sigAt(g.no, now, g.side, 'St') : null, ok = st && st.kind !== 'avg', tx = ok ? String(Math.ceil(st.remain)) : '?', kk = i ? k * 0.85 : k, hh = 22 * kk, w = (ok ? (tx.length > 2 ? 38 : 30) : 22) * kk, x = q[0] + 12, y = q[1] - hh / 2;
      if (boxes.some(function (b) { return x < b[2] && x + w > b[0] && y < b[3] && y + hh > b[1]; })) return; boxes.push([x - 3, y - 3, x + w + 3, y + hh + 3]);   /* v0.11.0 가까운 것부터 그려 겹치면 먼 것을 뺀다 */
      ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(x, y, w, hh, hh / 2); else ctx.rect(x, y, w, hh); ctx.fillStyle = ok ? (st.green ? '#16a34a' : '#dc2626') : '#64748b'; ctx.fill(); ctx.lineWidth = i ? 2 : 3.5; ctx.strokeStyle = i ? '#fff' : '#facc15'; ctx.stroke();
      ctx.font = '900 ' + (12.5 * kk).toFixed(1) + 'px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = '#fff'; ctx.fillText(tx, x + w / 2, y + hh / 2 + 0.5); }); }
  function wakeOn() { try { if (navigator.wakeLock && !wake) navigator.wakeLock.request('screen').then(function (w) { if (guide || cruise) wake = w; else try { w.release(); } catch (e) {} }).catch(function () {}); } catch (e) {} }
  function cruiseStart() { if (!G) return; dongLoad(); if (watchId == null && !sim) gpsStart(); if (!me) note('내 자리를 기다리는 중 — 위치를 허락하면 따라가기 시작한다'); cruise = true; follow = true; document.body.classList.add('guiding'); view.s = Math.max(0.25, Math.min(0.9, cv.clientHeight * 0.68 / CF.fwd));   /* 앞 범위(설정 · 기본 2km)가 화면에 들게(내 자리는 화면 68% 높이) */
    if (me) { view.cx = me.x; view.cy = me.y; view.rot = me.hd; } wakeOn(); paint(); draw(); }
  function cruiseStop() { cruise = false; CRA = null; alrShow(null); document.body.classList.remove('guiding'); view.rot = 0; try { if (wake) wake.release(); } catch (e) {} wake = null; paint(); draw(); }
  /* 같은 글이면 다시 쓰지 않는다 — 누르는 도중 단추가 바뀌어 눌림이 사라지는 것을 막는다(다른 곳이 그 사이 고쳐 썼으면 다시 쓴다) */
  /* ---------- v0.11.0 ⚙ 설정 — 한 곳에서 바꾸면 화면 전체에 · 값은 ../js/travel-time.js(TT) 가 이 기기에 둔다(데이터 압축지도와 같은 값을 같이 쓴다) ---------- */
  var CFGSET = [['음성', [['vrate', '음성 빠르기', [[0.9, '느리게'], [1.05, '보통'], [1.2, '빠르게'], [1.35, '아주 빠르게']]]]], ['글씨', [['fz', '기본 글씨 크기', [[0.9, '작게'], [1, '보통(종전)'], [1.15, '크게'], [1.3, '아주 크게']]], ['sz', '진행방향 남은 초 글씨', [[1, '종전'], [1.5, '1.5배'], [2, '2배'], [2.5, '2.5배'], [3, '3배']]]]],
    ['안전운전(켜놓고 다니기)', [['fwd', '사거리 표시 — 앞', [[1000, '1km'], [1500, '1.5km'], [2000, '2km'], [3000, '3km']]], ['back', '사거리 표시 — 뒤', [[500, '500m'], [1000, '1km'], [1500, '1.5km']]]]],
    ['주행시간(중요업무 · 신고차량 예측)', [['vipV', '중요업무 기본 속도', [[60, '60'], [70, '70'], [80, '80'], [90, '90'], [100, '100']]], ['vipFast', '가장 이른 도착 기준(입력 없을 때)', [[80, '80'], [90, '90'], [100, '100'], [110, '110']]], ['vMin', '직접 입력 — 가장 느린', [[20, '20'], [30, '30'], [40, '40']]], ['vMax', '직접 입력 — 가장 빠른', [[100, '100'], [110, '110'], [120, '120']]], ['turnS', '회전 감속(초/번)', [[0, '0'], [3, '3'], [6, '6'], [10, '10']]], ['rampS', '진출입로 감속(초/번)', [[0, '0'], [5, '5'], [8, '8'], [12, '12']]], ['accS', '출발·정지 가감속(초/번)', [[0, '0'], [2, '2'], [4, '4'], [6, '6']]], ['tunK', '터널·지하차도 속도', [[0.8, '×0.8'], [0.9, '×0.9'], [1, '그대로']]], ['runK', '도주 차량 속도 배율', [[1.2, '×1.2'], [1.3, '×1.3'], [1.5, '×1.5']]], ['calOn', '막힘 배율 — 실시간 소통 없을 때 ITS 실측(요일·시간대)', [[1, '켬'], [0, '끔']]]]]];
  function cfgApply() { if (!window.TT) return; CF = TT.cfg(); var st = document.documentElement.style; st.setProperty('--fz', CF.fz); st.setProperty('--sz', CF.sz); }
  function cfgHtml() { var C = TT.cfg(), D = TT.DEF, h = '<div class="ch"><b>⚙ 설정</b><button data-cx="close" aria-label="닫기">✕</button></div><p class="cs">이 기기에만 둔다 · 데이터 압축지도와 같은 값을 쓴다 · 앱을 새로 받아도 남는다</p>';
    CFGSET.forEach(function (g) { h += '<div class="cg">' + g[0] + '</div>'; g[1].forEach(function (it) { var k = it[0], cur = C[k], dv = D[k], opts = it[2].slice(); if (!opts.some(function (o) { return o[0] === cur; })) opts.push([cur, String(cur)]);
      h += '<div class="ci"><div class="cl">' + it[1] + (k === 'calOn' && TT.calWhy ? ' · 지금 ' + TT.calWhy() : '') + (cur !== dv ? ' <button data-cr="' + k + '" class="cre">↺ 기본(' + (k === 'fz' || k === 'sz' || k === 'tunK' || k === 'runK' ? '×' + dv : dv) + ')</button>' : '') + '</div><div class="co">' + opts.map(function (o) { return '<button data-cs="' + k + ':' + o[0] + '" class="' + (o[0] === cur ? 'on' : '') + '">' + o[1] + (o[0] === dv ? '<i>기본</i>' : '') + '</button>'; }).join('') + '</div></div>'; }); });
    var n = TT.calN(); h += '<div class="cg">보정 · 기록</div><div class="ci"><div class="cl">실측 보정 ' + (n ? '×' + TT.calK().toFixed(2) + '(일반 주행 ' + n + '번)' : '아직 없음') + ' — 안내를 끝까지 마친 일반 주행의 「걸린 시간 ÷ 계산」만 숫자로 쌓는다</div><div class="co"><button data-cx="cal">보정 지우기</button><button data-cx="recent">최근 목적지 모두 지우기</button></div></div>';
    var AS = arrSum(); h += '<div class="ci"><div class="cl">⏱ 예상·실제 도착 기록 ' + AS.n + '번' + (AS.n ? ' · 실제 ÷ 예상 가운데 ×' + AS.med.toFixed(2) + (AS.wr ? ' · 예상 폭 안에 든 것 ' + AS.inR + '/' + AS.wr : '') : '') + ' — 안내를 끝까지 마친 것만 <b>이 기기에만</b>(좌표·목적지 없이 날짜·시·모드·거리·초 · 긴급 출동 포함 · 중요업무·모의 주행 빼고) · 보정과 90일 실증의 바탕</div><div class="co"><button data-cx="arrx">📤 내보내기</button><button data-cx="arrd">🗑 지우기</button></div></div>';
    h += '<div class="ci"><div class="cl">🚇 열차 안 신고 — 열차보다 먼저 닿을 역 · 선착 확률 · 출발 미룰 수 있는 시간(시간표 기준 · 후보·예상)</div><div class="co"><button data-sr="open|">열기</button></div></div>';
    h += '<div class="ci"><div class="cl">🚇 역 실측 — 출입구 → 승강장 · 순찰차 세운 자리 → 출입구를 스톱워치로 재 <b>이 기기에만</b> 남긴다(3번 이상 잰 값이 도착 예측의 가정값을 대신한다 · JSON 내보내기)</div><div class="co"><a href="./measure.html" style="display:inline-block;padding:8px 12px;border-radius:10px;background:#2f6bff;color:#fff;font-weight:800;text-decoration:none">🚇 역 실측 열기</a></div></div>';
    var DA = drvAll(); h += '<div class="ci"><div class="cl">🛰 주행 기록 ' + (drvOn() ? '<b>켬</b>' : '끔') + ' · 남은 것 ' + DA.length + '번 — 켜면 안내 중 GPS 자리를 2초마다 <b>이 기기에만</b> 남긴다(최근 10번 · 모의 주행·중요업무는 안 남김) · 내보낸 파일로 예측과 실제 걸린 시간을 맞대 본다</div><div class="co"><button data-cx="drv" class="' + (drvOn() ? 'on' : '') + '">' + (drvOn() ? '켬 — 끄기' : '켜기') + '</button><button data-cx="drvx">📤 내보내기(파일)</button><button data-cx="drvd">🗑 모두 지우기</button></div></div>';
    h += '<div class="ci"><div class="cl">🧠 다녀 본 길 기억 ' + (lrnOn() ? '<b>켬</b>' : '끔') + ' · ' + lrnCount() + '줄 — 안내 중·켜놓고 다니기 중 실제로 지난 길 줄의 걸린 시간을 <b>이 기기에만</b> 요일·시간대마다 모아, 같은 줄을 두 번 넘게 지나면 실시간 값 다음으로 쓴다(골목 지름길) · 중요업무·모의 주행은 안 모음</div><div class="co"><button data-cx="lrn" class="' + (lrnOn() ? 'on' : '') + '">' + (lrnOn() ? '켬 — 끄기' : '켜기') + '</button><button data-cx="lrnd">🗑 기억 지우기</button></div></div>';
    h += '<div class="ci"><div class="cl">🔒 중요업무는 경로·지점·시각을 저장하지 않는다 — 이 화면이 닫히면 사라진다</div></div><div class="cb"><button data-cx="all">전체 기본값으로</button><button data-cx="close" class="go">닫기</button></div>';
    return h; }
  function cfgOpen(on) { var el = $('gCfg'); if (!el || !window.TT) return; if (on) { el.innerHTML = cfgHtml(); el.style.display = 'block'; } else el.style.display = 'none'; }
  function cfgClick(t) { var a; if ((a = t.getAttribute('data-cs'))) { var i = a.indexOf(':'); TT.set(a.slice(0, i), +a.slice(i + 1)); GCF.t = 0; }
    else if ((a = t.getAttribute('data-cr'))) TT.reset(a);
    else if ((a = t.getAttribute('data-cx'))) { if (a === 'close') { cfgOpen(false); return; } if (a === 'all') { if (!confirm('설정을 모두 기본값으로 되돌릴까요?')) return; TT.reset(); } if (a === 'cal') TT.calReset(); if (a === 'drv') { try { localStorage.setItem('tg_gargo_drvon', drvOn() ? '0' : '1'); } catch (e) {} } if (a === 'drvx') drvExport(); if (a === 'arrx') { var AX = arrAll(); if (!AX.l.length) note('남긴 도착 기록이 없다'); else { var bx = new Blob([JSON.stringify({ schema: 'tg-arrive-log/1', made: new Date().toISOString().slice(0, 10), fields: 'l[[날짜, 시, 요일 갈래 w평일|s토|h일·공휴, 모드 n일반|e긴급 출동, 거리 km, 예상 초, 폭 아래 초|null, 폭 위 초|null, 실제 초]] · 좌표·목적지 없음', l: AX.l })], { type: 'application/json' }), ax = document.createElement('a'); ax.href = URL.createObjectURL(bx); ax.download = 'arrive-' + new Date().toISOString().slice(0, 10) + '.json'; document.body.appendChild(ax); ax.click(); setTimeout(function () { URL.revokeObjectURL(ax.href); ax.remove(); }, 500); } } if (a === 'arrd' && confirm('예상·실제 도착 기록을 모두 지울까요?')) { try { localStorage.removeItem('tg_gg_arr'); } catch (e) {} } if (a === 'lrn') { try { localStorage.setItem('tg_gargo_lrnoff', lrnOn() ? '1' : '0'); } catch (e) {} LRNON = null; LRNE = null; } if (a === 'lrnd' && confirm('다녀 본 길 기억을 모두 지울까요?')) { try { localStorage.removeItem(LKEY); } catch (e) {} LRN = null; LRNE = null; } if (a === 'drvd' && confirm('주행 기록을 모두 지울까요?')) { try { localStorage.removeItem(DKEY); } catch (e) {} DLOG = null; } if (a === 'recent') { var P = plLoad(); P.r = []; plSave(); note('최근 목적지를 지웠다'); } }
    var sc = $('gCfg').scrollTop; cfgApply(); cfgOpen(true); $('gCfg').scrollTop = sc; if (cruise && me) { cruiseStart(); } paint(); draw(); }
  /* 중요업무에 들어갈 때 — 미뤄 둔 주소 찾기를 끊고(목록도 닫음) · 음성 받아쓰기를 멈추고 · 이 목적지를 최근 목적지에서 지우고 · 길 조각을 모두 한 번 받아 둔다(그 뒤로는 화면 둘레만큼 받지 않는다 — 받기 기록으로 구역이 드러나지 않게) */
  function vipEnter() { DLOG = null; LT = null; if (dest) lrnPurge(dest.x, dest.y); if (dest) drvPurge(dest.x, dest.y); clearTimeout(FNT); FSEQ++; PICKSEQ++; if (fl) fl.style.display = 'none'; try { if (rec) rec.abort(); } catch (e) {} rec = null;
    if (dest) { dest.vip = 1; try { var P = plLoad(), ll = llOf(dest.x, dest.y); P.r = (P.r || []).filter(function (q) { return !(Math.abs(q.lon - ll[0]) < 3e-4 && Math.abs(q.lat - ll[1]) < 3e-4); }); plSave(); } catch (e) {} }
    if (PK && !PKVIPALL) { var ks = Object.keys(PK.tiles).filter(function (k) { return !PKT[k]; }); if (ks.length) { PKVIP++; note('🔒 중요업무 — 길 조각을 모두 한 번 받아 두는 중(약 2MB) · 그 뒤로는 화면 둘레만큼 따로 받지 않는다'); pkLoad(ks).then(function () { PKVIP--; PKVIPALL = true; pkRebuild(true, true); note(''); if (dest && me) plan(true); else { paint(); draw(); } }, function () { PKVIP--; }); } else PKVIPALL = true; } }
  function vipLock() { if (MODE === 'v') vipEnter(); var on = MODE === 'v', b = $('gVip'); document.body.classList.toggle('vip', on); if (b) b.classList.toggle('on', on); if (fi) fi.placeholder = on ? '🔒 중요업무 — 이 기기 안 이름·도로명 번호로만 찾는다' : '어디로? 주소·이름을 적거나 🎤 말한다'; }
  function setH(el, h) { if (el._h === h && el._hs === el.innerHTML) return; el._h = h; el.innerHTML = h; el._hs = el.innerHTML; }
  function paintCruise() { var top = $('gTop'), bot = $('gBot'), sg = $('gSig'), spd = $('gSpd'), now = Date.now() / 1000, age = me && !sim ? (Date.now() - me.t) / 1000 : 0, lost = age > 5, A = lost ? null : ahead(); CRA = A; $('gFind').style.display = 'none'; top.style.display = 'flex';
    var lv = A && A.live ? spdLv(A.live, A.cls, A.lim) : -1, flow = lv < 0 ? '' : '<small class="ln2">이 길 지금 — <b>' + ['원활', '서행', '정체'][lv] + '</b>' + (A.live <= A.lim ? ' · 시속 ' + Math.round(A.live) + 'km쯤' : '') + '</small>';
    var t1 = lost ? '📡 위치가 끊겼다' : A && A.nm ? esc(A.nm) : !me ? '내 자리 기다리는 중' : !me.hk ? '방향을 잡는 중' : me.out ? '가르고 지도 밖' : A && A.off ? '가는 쪽의 길을 못 찾았다' : '길 위가 아니다',
      t2 = lost ? Math.round(age) + '초 전 자리 — 다시 잡히면 이어서 보인다' : me && !me.hk ? '조금 움직이면 가는 쪽의 앞 신호를 보인다' : me && me.out ? AREA_KO + '과 둘레에서만 길을 안다' : '켜놓고 다니기 — 목적지 없음';
    setH(top, '<div class="arw">' + (lost ? '…' : '⬆') + '</div><div class="tx"><b>' + t1 + '</b><span>' + t2 + '</span>' + flow + '</div>');
    setH(bot, '<div class="eta"><div><b>' + hm(now) + '</b><span>지금</span></div><div><b>' + (LIVE.m ? esc(String(LIVE.made || '').slice(-5)) : '없음') + '</b><span>소통 받은 때</span></div><button id="gCruiseX" class="stop">끝</button></div>');
    if (A && !A.off && me) { var v = Math.round((me.spd || 0) * 3.6); spd.style.display = 'flex'; setH(spd, '<div class="lim">' + A.lim + '</div><div class="cur' + (v > A.lim + 2 ? ' over' : '') + '"><b>' + v + '</b><span>km/h</span></div>' + (A.nm ? '<div class="rn">' + esc(A.nm) + '</div>' : '')); } else spd.style.display = 'none';
    alrLoad(); try { alrShow(lost ? null : alrAhead(aheadPoly(A))); } catch (e) {}
    var ns = A && A.sig; if (!ns) { sg.style.display = 'none'; return; } var use = sigUse(ns), st = use ? sigAt(ns.no, now, ns.side, 'St') : null, kmh = (me.spd || 0) * 3.6,
      at = use && me.spd > 2 && kmh <= A.lim + 2 && !night() ? sigAt(ns.no, now + ns.eta, ns.side, 'St') : null, h = '';   /* 「닿으면」 — 움직일 때만 · 제한속도 넘게 달리는 중이면 안 보임 · 밤(22~06시) 안 보임 */
    sg.style.display = 'block'; var tb = top.getBoundingClientRect(); sg.style.top = Math.round(tb.bottom + 6) + 'px'; sg.className = 'sig ' + (!st || st.kind === 'avg' ? 'unk' : st.green ? 'grn' : 'red');
    h += '<div class="hd"><b>🚦 ' + esc(ns.nm) + '</b><span>' + km(ns.d) + ' 앞 · ' + (DIRKO[ns.side] || '') + '쪽에서 ' + (use ? '직진' : '들어감') + '</span></div>';
    if (!use) h += '<div class="ln">' + sigWhy(ns) + '</div>';
    else if (!st) h += '<div class="ln">이 신호는 <b>자료가 없다</b> — 눈으로 본다</div>';
    else if (st.kind === 'avg') h += '<div class="ln">지금 색은 <b>모른다</b>(이 시각대를 아직 못 받았다) · 평균 기다림 ' + Math.round(st.wait) + '초 · 주기 ' + Math.round(st.C) + '초</div>';
    else { h += '<div class="now"><i></i><b><small>' + (st.green ? '녹색' : '적색') + ' </small>' + Math.ceil(st.remain) + '<small>초</small></b><span>' + (st.green ? '뒤 꺼짐' : '뒤 녹색') + '</span></div>';
      if (at && at.kind !== 'avg') h += '<div class="ln">지금 속도(제한속도 안)로 닿으면(' + Math.round(ns.eta) + '초 뒤) → ' + (at.green ? '<b class="g">녹색일 때</b> <em>(남은 녹색 ' + Math.floor(at.remain) + '초)</em>' : '<b class="r">적색</b> · ' + Math.ceil(at.wait) + '초 기다림') + '</div>';
      h += '<div class="src">' + (st.kind === 'pl' ? '시각대 표(계획값)' : '방금 받은 값에서 이어 셈') + ' · 내 진행 방향(직진)의 값 · 수동 조작·감응 신호면 다르다 · 눈으로 확인</div>'; }
    setH(sg, h); }
  /* v0.14.0 주행 기록 — ⚙ 에서 켤 때만 · 이 기기 안(tg_gargo_drives · 최근 10번) · 모의 주행·중요업무는 남기지 않는다 · 내보내기 파일 = 예측과 실제를 맞대는 정답 자료 */
  var DLOG = null, DLT = 0, DKEY = 'tg_gargo_drives';
  function drvOn() { try { return localStorage.getItem('tg_gargo_drvon') === '1'; } catch (e) { return false; } }
  function drvAll() { try { var A = JSON.parse(localStorage.getItem(DKEY) || '[]'); return Array.isArray(A) ? A : []; } catch (e) { return []; } }
  function drvBasis(r, d) { if ((r.kn || []).some(function (q) { return d >= q[0] - 1 && d <= q[1] + 1; })) return 'its'; return LIVER ? 'liver' : window.TT && TT.calF && TT.calF(Date.now()) !== 1 ? 'cal' : 'lim'; }
  function drvBegin(r) { if (guide && DLOG) return; DLOG = null; if (!drvOn() || sim || MODE === 'v' || (dest && dest.vip)) return;   /* 안내 중 ▶ 를 다시 눌러도 이어 간다 */ var LL = function (x, y) { return [+(LAT0 - y / KY).toFixed(6), +(x / KX + LON0).toFixed(6)]; };
    DLOG = { schema: 'tg-drive-log/1', app: '가르고 0.14.0', mode: MODE, pts: [], plan: { at: Date.now(), dist: Math.round(r.dist), sec: Math.round(r.time), live: +(r.live || 0).toFixed(2), calF: window.TT && TT.calF ? TT.calF(Date.now()) : 1,
      rows: r.sigs.map(function (g) { return [g.no || g.nm || '', Math.round(g.t), drvBasis(r, g.d), Math.round(g.d)].concat(LL(g.x, g.y)); }) } }; }
  function drvPt(c) { try { if (!DLOG || !guide) return; if (sim || MODE === 'v' || (dest && dest.vip) || !drvOn()) { DLOG = null; return; } if (DLOG.pts.length >= 3600 || !(c.latitude > 0)) return; var n = Date.now(); if (n - DLT < 2000) return; DLT = n; DLOG.pts.push([n, +c.latitude.toFixed(6), +c.longitude.toFixed(6), Math.round(c.accuracy || 0), c.speed == null || isNaN(c.speed) ? null : +c.speed.toFixed(1)]); } catch (e) {} }
  function drvEnd(done) { var L = DLOG; DLOG = null; try { if (!L || L.pts.length < 5 || MODE === 'v' || (dest && dest.vip) || !drvOn()) return; L.end = Date.now(); L.done = !!done; var A = drvAll(); A.push(L); while (A.length > 10) A.shift();
      var js = JSON.stringify(A); while (A.length > 1 && js.length > 1000000) { A.shift(); js = JSON.stringify(A); } if (js.length > 1000000) return;   /* 같은 사이트의 T-Book·지도와 저장 칸을 나눠 쓴다 — 전체 1MB 넘게 안 둔다 */
      try { localStorage.setItem(DKEY, js); } catch (e) { note('주행 기록을 저장하지 못했다(기기 저장 칸 부족)'); } } catch (e) {} }
  /* 중요업무에 들어가면 — 그 목적지 300m 안에서 끝난 일반 주행 기록을 지운다(같은 길이 내보내기 파일에 남지 않게) */
  function drvPurge(x, y) { try { var lat = LAT0 - y / KY, lon = x / KX + LON0, A = drvAll(), B = A.filter(function (L) { var q = L.pts && L.pts[L.pts.length - 1]; return !(q && Math.hypot((q[1] - lat) * 111000, (q[2] - lon) * 88800) < 300); }); if (B.length !== A.length) localStorage.setItem(DKEY, JSON.stringify(B)); } catch (e) {} }
  function drvExport() { if (MODE === 'v' || (dest && dest.vip)) { note('🔒 중요업무 중에는 내보내지 않는다'); return; } var A = drvAll(); if (!A.length && !(drvOn() && lrnCount())) { note('남긴 주행 기록이 없다'); return; } var d = new Date(), nm = 'gargo-drive-' + d.getFullYear() + ('0' + (d.getMonth() + 1)).slice(-2) + ('0' + d.getDate()).slice(-2) + '.json', b = new Blob([JSON.stringify({ schema: 'tg-drive-export/1', made: d.toISOString(), logs: A, learn: drvOn() ? (function () { var L = lrnLoad(), o = {}; Object.keys(L.e).forEach(function (k) { o[k] = {}; Object.keys(L.e[k]).forEach(function (b) { o[k][b] = L.e[k][b].map(function (x) { return x[0]; }); }); }); return { v: 1, e: o }; })() : null })   /* 다녀 본 길은 주행 기록이 켜져 있을 때만 · 날짜 빼고 초만 */], { type: 'application/json' }), a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = nm; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000); note('📤 ' + nm + ' — ' + A.length + '번'); }
  function guideStart() { if (!route) return; icLoad(); dongLoad(); alrLoad(); riskLoad(); if (MODE === 'e') busLoad(); drvBegin(route); GSTART = { t: Date.now(), pred: route.time, mode: MODE, sim: !!sim, dist: route.dist }; (function () { var RG = rngOf(route, route.time); if (RG) { GSTART.lo = RG[0]; GSTART.hi = RG[1]; } })(); guide = true; follow = true; document.body.classList.add('guiding'); view.s = 1.1; if (me) { view.cx = me.x; view.cy = me.y; view.rot = me.hd; } lastSay = {}; wakeOn(); say('안내를 시작합니다. ' + (MODE === 'v' ? '' : etaWords(route)), 2); paint(); draw(); }
  function guideStop(done) { drvEnd(done); lrnFlush(); guide = false; alrShow(null); document.body.classList.remove('guiding'); view.rot = 0; try { if (wake) wake.release(); } catch (e) {} wake = null; if (sim) { clearInterval(sim.t); sim = null; } if (done) { route = null; dest = null; } paint(); draw(); }
  function simStart() { if (!route) return; var r = route, d = 0, last = Date.now(); voiceOn = false; $('gVoice').classList.remove('on'); guideStart(); note('모의 주행 — 제한속도로 길을 따라간다(신호에서는 예상대로 선다) · 실제 위치가 아니다');
    DLOG = null; sim = { t: setInterval(function () { var now = Date.now(), dt = (now - last) / 1000 * 4; last = now; var lim = 30, k; for (k = 0; k < r.lims.length; k++) if (r.lims[k][0] <= d + 1) lim = r.lims[k][1];
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
  var PICKSEQ = 0;
  function pick(px, py, w0) { if (!G || guide) return; var w = w0 || S2W(px, py); if (PK) { var pm = pkKeys([w], 400); if (pm.length) { var tk3 = ++PICKSEQ; pkLoad(pm).then(function (n) { if (n) pkRebuild(true, false, pm); if (tk3 !== PICKSEQ) return; var q = W2S(w[0], w[1]); pick(q[0], q[1], w); }); return; } } var ns = nearSeg(w[0], w[1], 250), el = $('gPick'); if (!ns) { note('여기는 길에서 멀다'); return; }
    var nm = G.S[ns.seg][5] >= 0 ? G.j.names[G.S[ns.seg][5]] : '이름 없는 길'; el.style.display = 'flex'; el.style.left = Math.max(8, Math.min(cv.clientWidth - 228, px - 110)) + 'px'; el.style.top = Math.max(70, py - 64) + 'px';
    el.innerHTML = '<b>' + esc(nm) + '</b><button data-p="to">여기로 안내</button><button data-p="from">여기서 떠나기</button><button data-p="x">닫기</button>'; el._w = [ns.x, ns.y, nm]; }
  $('gPick').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var w = this._w, k = b.getAttribute('data-p'); this.style.display = 'none'; if (k === 'to') setDest(w[0], w[1], w[2]); else if (k === 'from') { if (watchId != null) { navigator.geolocation.clearWatch(watchId); watchId = null; } sim = null; setMe(w[0], w[1], 5, null, 0); note('떠나는 곳을 손으로 정했다 — 실제 위치로 돌아가려면 ◎ 를 누른다'); } });
  function setDest(x, y, nm, vq, noRec) { var vip = !!(vq || MODE === 'v'); if (cruise) cruiseStop(); dest = { x: x, y: y, nm: nm || '목적지', ext: !!(FEXT && !vip), vip: vip ? 1 : 0 }; FEXT = false; if (!vip && !noRec) { try { plPut('r', dest); } catch (e) {} } route = null; if (!me) gpsStart(); if (me) plan(); else { paint(); draw(); } }
  document.addEventListener('click', function (e) { var t = e.target.closest('button'); if (!t) return; var id = t.id;
    var srk = t.getAttribute('data-sr'); if (srk) { if (srk === 'open|') srOpen(true); else srClick(srk); return; }
    var dck = t.getAttribute('data-dc'); if (dck) { dispClick(dck); return; } var dcp = t.getAttribute('data-dcp'); if (dcp != null && DRES && DRES.ok[+dcp]) { var tx9 = dispOrder(DRES.ok[+dcp]); try { navigator.clipboard.writeText(tx9).then(function () { note('📋 복사했다 — ' + tx9); }, function () { note(tx9); }); } catch (e) { note(tx9); } return; }
    var plk = t.getAttribute('data-pl'); if (plk && dest && (dest.vip || MODE === 'v')) { note('🔒 중요업무 목적지는 이 기기에 남기지 않는다'); return; } if (plk && dest) { plPut(plk, dest); note({ h: '🏠 집', o: '🚓 근무지', f: '⭐ 즐겨찾기' }[plk] + '으로 넣었다 — 찾기 칸을 누르면 나온다(이 기기에만)'); return; }
    if (id === 'gGo') { if (MODE !== 'v' && !(dest && dest.vip)) voiceAsk(); guideStart(); } else if (id === 'gSim') simStart(); else if (id === 'gClr') { route = null; dest = null; note(''); paint(); draw(); } else if (id === 'gStop') guideStop(false); else if (id === 'gMenu') { var mp = $('gMpop'); if (mp) mp.classList.toggle('on'); } else if (id === 'gReplan') { if (route && dest && me) { lastSay.man = null; plan(); note('경로를 다시 찾는다'); } } else if (id === 'gCruise') cruiseStart(); else if (id === 'gCruiseX') cruiseStop();
    else if (id === 'gCen') { follow = true; t.classList.remove('off'); if (watchId == null && !sim) gpsStart(); if (me) { view.cx = me.x; view.cy = me.y; if (guide || cruise) view.rot = me.hd; else if (view.s < 0.5) view.s = 0.9; } draw(); }
    else if (id === 'gVoice') { voiceOn = !voiceOn; t.classList.toggle('on', voiceOn); if (voiceOn) say('음성 안내를 켭니다'); else if (window.speechSynthesis) speechSynthesis.cancel(); }
    else if (id === 'gMic') micGo();
    else if (t.hasAttribute('data-ov')) { var k = t.getAttribute('data-ov'); OV[k] = OV[k] ? 0 : 1; t.classList.toggle('on', !!OV[k]); try { localStorage.setItem('tg_gargo_ov', JSON.stringify(OV)); } catch (x) {} draw(); }
    else if (id === 'gIn') { view.s = Math.min(4, view.s * 1.4); draw(); } else if (id === 'gOut') { view.s = Math.max(0.03, view.s / 1.4); draw(); }
    else if (t.hasAttribute('data-mode')) { MODE = t.getAttribute('data-mode'); if (MODE === 'e') busLoad(); if (MODE === 'v') { vipLock(); if (dest && dest.ext) note('🔒 이 목적지는 주소 찾기로 이미 브이월드에 물어 찾았다 — 다음에는 🔒 중요업무를 먼저 켜고 찾는다(그때는 밖으로 묻지 않는다)'); } else vipLock(); if (dest && me) plan(); else paint(); }
    else if (t.hasAttribute('data-vipb')) { VIPB = +t.getAttribute('data-vipb'); paint(); }
    else if (t.hasAttribute('data-vipf')) { if (t.getAttribute('data-vipf') === 'x') { VIPF = null; paint(); return; } var C0 = TT.cfg(), a = prompt('빨리 갈 때 속도(km/h · ' + C0.vMin + '~' + C0.vMax + ')', VIPF || ''); if (a == null || a === '') return; var v = +String(a).replace(/[^\d.]/g, ''); if (!(v >= C0.vMin && v <= C0.vMax)) { alert('받지 않았다 — ' + C0.vMin + '~' + C0.vMax + 'km/h 안에서만 넣는다'); return; } VIPF = Math.round(v); paint(); }
    else if (id === 'gVip') { MODE = MODE === 'v' ? 'n' : 'v'; vipLock(); if (dest && me) plan(); else paint(); }
    else if (id === 'gCfgB') cfgOpen(true); else if (t.closest('#gCfg')) cfgClick(t);
    else if (t.hasAttribute('data-hand')) handOff(t.getAttribute('data-hand'));
    else if (id === 'gDark') { document.documentElement.classList.toggle('dark'); try { localStorage.setItem('tg_gargo_dark', document.documentElement.classList.contains('dark') ? '1' : '0'); } catch (x) {} draw(); }
    else if (id === 'gOk') { $('gIntro').style.display = 'none'; try { localStorage.setItem('tg_gargo_intro', '1'); } catch (x) {} gpsStart(); } });
  /* 다른 내비로 넘기기 — 그 앱이 깔려 있어야 열린다(앱의 주소 규약으로 목적지 좌표와 이름만 넘긴다 · 누를 때만) */
  function handOff(k) { if (!dest) return; if (dest.vip || MODE === 'v') { note('🔒 중요업무 목적지는 다른 앱·화면으로 넘기지 않는다'); return; } var lon = (dest.x / KX + LON0).toFixed(6), lat = (LAT0 - dest.y / KY).toFixed(6), nm = encodeURIComponent(dest.nm || '목적지');
    if (k === 'map') { window.open('../#lat=' + (+lat).toFixed(5) + '&lon=' + (+lon).toFixed(5), '_blank', 'noopener'); return; }   /* 같은 사이트의 데이터 압축지도 — 그 자리의 사고·신호·시설 */
    var
      u = k === 'tmap' ? 'tmap://route?goalname=' + nm + '&goalx=' + lon + '&goaly=' + lat : k === 'kakao' ? 'kakaomap://route?ep=' + lat + ',' + lon + '&by=CAR' : 'nmap://navigation?dlat=' + lat + '&dlng=' + lon + '&dname=' + nm + '&appname=340patrolman.github.io';
    note((k === 'tmap' ? '티맵' : k === 'kakao' ? '카카오맵' : '네이버지도') + '을 연다 — 앱이 깔려 있지 않으면 아무 일도 일어나지 않는다'); location.href = u; }
  function voiceAsk() { if (!window.speechSynthesis) return; voiceOn = true; $('gVoice').classList.add('on'); }
  /* 이름으로 찾기 — 신호 교차로 이름 · 길 이름(이 묶음 안) */
  /* v0.9.0 집·근무지·즐겨찾기·최근 목적지 — 이 기기 localStorage(tg_gargo_places)에만 · 경도·위도로 둔다(길 묶음이 바뀌어도 그 자리) · 최근 8 · 즐겨찾기 12 */
  var PLC = null;
  function plLoad() { if (PLC) return PLC; try { PLC = JSON.parse(localStorage.getItem('tg_gargo_places') || '{}') || {}; } catch (e) { PLC = {}; } PLC.f = PLC.f || []; PLC.r = PLC.r || []; return PLC; }
  function plSave() { try { localStorage.setItem('tg_gargo_places', JSON.stringify(PLC)); } catch (e) {} }
  function llOf(x, y) { return [Math.round((x / KX + LON0) * 1e6) / 1e6, Math.round((LAT0 - y / KY) * 1e6) / 1e6]; }
  function plPut(kind, d) { if (!d || d.vip || MODE === 'v') return; var P = plLoad(), ll = llOf(d.x, d.y), o = { n: d.nm || '목적지', lon: ll[0], lat: ll[1], t: Date.now() };
    if (kind === 'h' || kind === 'o') P[kind] = o;
    else { var L = P[kind], same = function (q) { return Math.abs(q.lon - o.lon) < 0.0003 && Math.abs(q.lat - o.lat) < 0.0003; }; P[kind] = [o].concat(L.filter(function (q) { return !same(q); })).slice(0, kind === 'f' ? 12 : 8); }
    plSave(); }
  function plList() { var P = plLoad(), out = [], add = function (ic, q, note) { if (q && q.lon) out.push([ic, q.n, PX(q.lon), PY(q.lat), note]); };
    add('🏠', P.h, '집'); add('🚓', P.o, '근무지'); P.f.forEach(function (q) { add('⭐', q, '즐겨찾기'); }); P.r.forEach(function (q) { add('🕘', q, '최근'); }); return out; }
  var fi = $('gQ'), fl = $('gList');
  fi.addEventListener('focus', function () { if (String(fi.value || '').trim()) return; var L = plList(); if (!L.length) return; fl._o = L;
    fl.innerHTML = L.map(function (o, i) { return '<button data-i="' + i + '">' + o[0] + ' ' + esc(o[1]) + ' <small>' + esc(o[4]) + '</small></button>'; }).join('') + '<div class="no">길 요약 판의 🏠·🚓·⭐ 로 넣는다 · 이 기기에만 남는다</div>'; fl.style.display = 'block'; });
  var fT = 0; fi.addEventListener('input', function () { clearTimeout(fT); var v = fi.value; fT = setTimeout(function () { findRun(v, false); }, 250); });
  fi.addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); clearTimeout(fT); findRun(fi.value, true); } });
  fl.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; pickFound(+b.getAttribute('data-i')); });
  /* 주소로 받은 목적지 — #to=위도,경도&nm=이름 · #from=위도,경도(시험) · 주소에서 지운다(좌표가 남지 않게) */
  function hashGo() { var H = location.hash || '', t = /[#&]to=(-?[\d.]+),(-?[\d.]+)/.exec(H), f = /[#&]from=(-?[\d.]+),(-?[\d.]+)/.exec(H), n = /[#&]nm=([^&]*)/.exec(H);
    if (f) setMe(PX(+f[2]), PY(+f[1]), 5, null, 0); if (t) { var x = PX(+t[2]), y = PY(+t[1]), nmH = n ? decodeURIComponent(n[1]) : '받은 자리', tk2 = ++PICKSEQ, vq2 = MODE === 'v'; pkEnsure([[x, y]], 800).then(function () { if (tk2 !== PICKSEQ) return; var ns = nearSeg(x, y, 600); if (ns) setDest(ns.x, ns.y, nmH, vq2); else note('받은 자리가 길 묶음 밖이다 — 시험판은 ' + AREA_KO + '과 둘레 2km 안에서만 된다'); }); }
    /* #q=주소·이름 — 받은 글로 바로 찾는다(티북 같은 데서 주소를 넘길 때 · # 뒤라 서버로 가지 않는다 · 읽고 지운다) */
    var qq = /[#&]q=([^&]*)/.exec(H); if (qq) { var qv = ''; try { qv = decodeURIComponent(qq[1]); } catch (e) {} if (qv) { fi.value = qv; findRun(qv, true); } }
    if (t || f || qq) { try { history.replaceState(null, '', location.pathname); } catch (e) {} } }
  setInterval(function () { if (document.hidden) return; if (route && (guide || sim)) { paint(); draw(); } else if (cruise && !route) { paint(); draw(); } else if (route || (OV.s && SIG.ready && view.s > 0.28)) draw(); }, 1000);
  /* 5분마다 — 통행속도 한 장과 신호 색인을 다시 본다. 신호 수집기가 약 15분마다 새 값을 올리므로(색인의 made 가 바뀐다) 바뀌었으면 서초 둘레 칸을 다시 받아 그 자리에서 갈아 끼운다.
     소유자 2026-10-13 「신호값이 업데이트되는 대로 계속 추가 업데이트되게」 — 안내 중에도 받는다(지금 색·남은 초가 새 값으로 바뀐다 · 길은 다시 고르지 않는다) */
  function sigRefresh() { return getJ('../data/sigdir/index.json').then(function (j) { if (!j || !j.fl || !SIG.idx || j.made === SIG.idx.made) return false; var need = {}; G.sig.forEach(function (s) { if (j.fl[s.no] == null) return; var q = j.pts[s.no]; if (q) need[Math.floor(q[0] / j.cell[0]) + '_' + Math.floor(q[1] / j.cell[1])] = 1; });
    var its = {}; return Promise.all(Object.keys(need).map(function (k) { return getJ('../data/sigdir/c/' + k + '.json').then(function (c) { if (c && c.its) Object.keys(c.its).forEach(function (no) { its[no] = c.its[no]; }); }); })).then(function () { if (!Object.keys(its).length) return false; SIG.idx = j; SIG.pl = j.pl || {}; SIG.cell = j.cell; SIG.its = its; SIG.at = Date.now(); return true; }); }); }
  setInterval(function () { if (!G || document.hidden) return; Promise.all([liveLoad(), sigRefresh(), accLoad()]).then(function (r) { if (dest && me && !guide) plan(); else { paint(); draw(); } }); }, 300000);
  window.addEventListener('resize', function () { draw(); });
  document.addEventListener('visibilitychange', function () { if (!document.hidden && (guide || cruise) && navigator.wakeLock) { try { navigator.wakeLock.request('screen').then(function (w) { wake = w; }).catch(function () {}); } catch (e) {} } });
  try { var dk = localStorage.getItem('tg_gargo_dark'), hr = new Date().getHours(); if (dk === '1' || (dk == null && (hr >= 19 || hr < 6))) document.documentElement.classList.add('dark'); } catch (e) {}
  function boot() { cfgApply(); try { if (window.TT && TT.VIP_ON && $('gVip')) $('gVip').hidden = false; } catch (e) {}  if (document.documentElement.classList.contains('gated')) return; var seen = false; try { seen = localStorage.getItem('tg_gargo_intro') === '1'; } catch (e) {} if (seen) { $('gIntro').style.display = 'none'; if (!/[#&]from=/.test(location.hash)) gpsStart(); } load(); }
  window.addEventListener('tggate', boot); boot();
  (function () { var tp = document.getElementById('gTop'); if (tp) tp.addEventListener('click', function () { sayAgain(); }); })();
  window.addEventListener('pagehide', function () { try { lrnFlush(); } catch (e) {} }); document.addEventListener('visibilitychange', function () { if (document.hidden) { try { lrnFlush(); } catch (e) {} } });
  window.GARGO = { sr: { cand: function () { return srCand(1); }, toward: srToward, open: srOpen, load: srLoad, st: SRS, calc: srCalc, click: srClick, ev: function (o) { if (o !== undefined) { SRE = o; SRC = null; } return SRE; } }, disp: function (cars) { if (cars) { DCARS = cars.map(function (c, i) { return { x: c[0], y: c[1], n: i + 1, nm: c[2] || (i + 1) + '호' }; }); DN = DCARS.length; DRES = null; } return dispRun(); }, dispHtml: function () { return dispHtml(); }, dispOrder: dispOrder, arrAdd: arrAdd, arrAll: arrAll, lrnFlush: lrnFlush, lrnFeed: function (x, y, hd, spd) { var sv = me; me = { x: x, y: y, hd: hd, hk: true, spd: spd, t: Date.now() }; try { lrnTrack(); } finally { me = sv; } }, lrnAdd: function (e, s) { lrnAdd(e, s); lrnFlush(); }, lrnSpeed: lrnSpeed, lrnCount: lrnCount, lrnReset: function () { try { localStorage.removeItem(LKEY); } catch (e) {} LRN = null; LRNE = null; LT = null; }, eKey: eKey, accLoad: accLoad, accSet: function (A) { ACC = A; }, accOf: accOf, busLoad: busLoad, busOn: function (r) { return busOn(r || route); }, emLane: function (nx, pos, r) { return emLane(nx, pos, r); }, routeMarks: function (r) { return routeMarks(r || route); }, dcard: dcard, dongLoad: dongLoad, dongAt: function (lon, lat) { return dongAt(PX(lon), PY(lat)); }, hereText: hereText, voiceTick: function (pos) { var r = route; return r ? turnWords(r, r.mans.filter(function (m) { return m.d > (pos || 0) + 5; })[0], null, pos || 0, 0) : ''; }, etaWords: function () { return route ? etaWords(route) : ''; }, plBox: function () { return PLBOX; }, icLoad: icLoad, icOn: function (r) { return icOn(r || route); }, icLine: function (r, p) { return icLine(r || route, p || 0); }, fill: function (e) { return FILL ? FILL[e] : null; }, liveFill: liveFill, drv: function () { return { on: drvOn(), cur: DLOG, all: drvAll() }; }, drvPt: function (c) { drvPt(c); }, calF: function () { return gCalF(); }, cfg: function () { return CF; }, findRun: function (q, auto) { findRun(q, auto); }, micGo: function () { micGo(); }, vipBox: function (r) { return vipBox(r || route); }, cfgApply: cfgApply, cfgOpen: cfgOpen, vipNow: function (r, pos) { return vipNow(r || route, pos || 0); }, vipSegs: function (r) { return vipSegs(r || route, 0); }, mode: function (m) { if (m) { MODE = m; vipLock(); if (m === 'e') busLoad(); } return MODE; }, vipSet: function (b, f) { VIPB = b || 0; VIPF = f == null ? null : f; }, risk: function () { return riskLoad(); }, riskOn: function (r) { return riskOn(r || route); }, riskHtml: function (r) { return riskHtml(r || route); }, pkTurns: function () { return G ? G.j.turns.length : 0; }, pkCore: function () { return PK; }, alrLoad: function () { alrLoad(); return ALRP; }, alrAhead: alrAhead, routePoly: routePoly, aheadPoly: aheadPoly, tAt: tAt, places: function () { return plList(); }, plPut: plPut, pk: function () { return { on: !!PK, area: PKA, tiles: Object.keys(PKT).length, total: PK ? Object.keys(PK.tiles).length : 0, turnsTotal: PK ? PK.turns_total : 0, bake: PK ? PK.bake : '' }; }, pkAll: function () { if (!PK) return Promise.resolve(); PKALL++; return pkLoad(Object.keys(PK.tiles).filter(function (k) { return !PKT[k]; })).then(function () { PKALL--; pkRebuild(true, true); }, function () { PKALL--; }); }, pkEnsure: pkEnsure, todFor: todFor, localFind: function (q) { return localFind(q); }, bld: function () { return { idx: !!BIDX, tiles: Object.keys(BT).length, vis: BVIS.length, names: BNM ? BNM.length : 0 }; }, bnmLoad: function () { bldLoad(); return BLDP.then(function () { bnmLoad(); return BNMP; }); }, paint: function () { paint(); }, cruise: function (on) { if (on === false) cruiseStop(); else cruiseStart(); return cruise; }, ahead: ahead, mvOf: mvOf, liver: function () { return LIVER; }, view: view, state: function () { return { me: me, dest: dest, route: route, guide: guide, sig: SIG, G: G }; }, sigAt: sigAt, plan: plan, setDest: setDest, setMe: setMe, draw: draw, P: function (lon, lat) { return [PX(lon), PY(lat)]; }, findRoute: findRoute, simStart: simStart, guideStart: guideStart, guideStop: guideStop, advise: advise, spdLv: spdLv, night: night, addrGuess: addrGuess };
})();
