/* 신호·수요 시뮬레이터 — 계산 엔진(2026-10-25 · 첫 구역 = 반포 터미널 블록 · intent/20261025-banpo-block-sim.md)
   개념 시연이다 — 예측·보증이 아니다. 값은 구역 자료(data/sim-<구역>.json · tools/sim/*-bake.py)에서만 읽고 코드에 숫자를 적지 않는다
   (자료가 없는 값은 그 파일 design 칸 = 「설계값」 · 화면에서 막대로 바꾼다).
   방법 = 접근로·이동류 대기열(대기열 축약 모형): 1초마다 녹색인 이동류에서 포화교통류율 × 차로만큼 빠지되 하류 길에 자리가 있을 때만 —
   자리가 없으면 대기열이 상류로 차오른다(넘침). 하류가 찼는데도 교차로에 들어간 차(꼬리물기)는 교차로를 막는다.
   구역마다 다른 것은 자료로 준다(schema tg-sim/2): 신호 교차로 · 길 · 신호 없는 갈림(mvx) · 끌어들이는 곳(att — 백화점·공원 같은 수요) · 조치(actions — 라바콘·입차 중단 등)
   두 판 비교가 공정하도록 차(언제·어디서·어디로)는 씨앗(seed)으로 미리 정해 두 판이 같은 차를 쓴다.
   지도 화면(map2d.js)과 따로 돈다 — window.tgSim 만 내놓는다. */
(function () {
  'use strict';
  var TURN = { nt: { St: 'st', Lt: 'et', Rt: 'wt' }, et: { St: 'wt', Lt: 'st', Rt: 'nt' }, st: { St: 'nt', Lt: 'wt', Rt: 'et' }, wt: { St: 'et', Lt: 'nt', Rt: 'st' } };
  var TODK = [4, 1, 1, 1, 1, 2, 3];   // 요일 → 현시도 요일 계획(1 월~목 · 2 금 · 3 토 · 4 일·공휴일)
  var VOLK = ['su', 'wd', 'wd', 'wd', 'wd', 'wd', 'sa'];
  var DAYK = ['su', 'mt', 'mt', 'mt', 'mt', 'fr', 'sa'];   // 요일 갈래(소유자 2026-10-25 「평일·금·토·일도 변수로」) — 월~목 · 금 · 토 · 일(신호 계획 TOD 1·2·3·4 · 평소 속도 갈래 0·1·2·3 과 같다)
  var NOBOX = { box: [] };
  function rng(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function hm(s) { return +s.slice(0, 2) * 3600 + +s.slice(2) * 60; }
  function dowOf(d) { var p = String(d).split('-'); return new Date(+p[0], +p[1] - 1, +p[2]).getDay(); }

  /* 현시 → 이동류별 녹색 창 [이동류, 녹색 초, 황색 초, 녹색 시작]
     이웃 현시에도 켜져 있는 이동류는 끊기지 않고 이어지며, 끝나는 현시의 황색·전적색만 뺀다(현시도 dir 줄과 같은 셈 — 4031 패턴 14 로 맞대 봄) */
  function phasesToWin(ph) {
    var t = 0, st = {}, W = [];
    ph.forEach(function (p, i) {
      var nx = ph[i + 1] ? ph[i + 1].mv : [];
      p.mv.forEach(function (m) { if (st[m] == null) st[m] = t; if (nx.indexOf(m) < 0) { W.push([m, t + p.d - p.y - p.ar - st[m], p.y, st[m]]); delete st[m]; } });
      t += p.d;
    });
    return { c: t, win: W.sort(function (a, b) { return a[3] - b[3]; }) };
  }
  /* 그 기록에 빠진 이동류 채우기(planAt 에서 떼어 냄 · 2026-11-03) — 처음엔 시뮬이 돌다가 그 기록을 처음 쓸 때 채웠는데, 이동류(길)는 create 때
     「어느 기록에든 녹색이 있는 이동류」로만 만들어서 처음 돌린 판만 채운 이동류가 빠져 두 번째 판부터 결과가 달랐다(서초역 구역 지체 1,156 → 2,408 대·시) → create 앞에서 모두 채운다(prefill) */
  function fillRec(M, n, p, best) {
    var have = {}, W = best.win.slice(); best.win.forEach(function (r) { have[r[0]] = 1; });
        p.recs.forEach(function (r) { r.win.forEach(function (w) { if (w[4] || have[w[0]]) return; var dn = null, dv = 1e9; p.recs.forEach(function (q) { if (!q.win.some(function (x) { return x[0] === w[0] && !x[4]; })) return;   /* 원래 기록 값만 빌린다(채운 값·빈 시간 값을 다시 빌리면 먼저 돌린 시간대에 따라 달라졌다) */ var dd = (q.cyc === best.cyc ? 0 : 1e5) + Math.abs(q.t - best.t); if (dd < dv) { dv = dd; dn = q; } });
          var x = dn.win.filter(function (z) { return z[0] === w[0] && !z[4]; })[0], k = best.cyc / dn.cyc; W.push([x[0], Math.round(x[1] * k), x[2], Math.round(x[3] * k) % best.cyc, 'fill']); have[w[0]] = 1; }); });
        if (M.auto) gapFill(n, W, best.cyc);
        best.win = W.sort(function (a9, b9) { return a9[3] - b9[3]; }); best.full = 1; 
  }
  /* 이 판이 쓸 기록(그 요일 · 몸풀기부터 끝까지 1분마다 고른 기록)만 미리 채우고 그 기록들을 돌려준다 — 이동류는 「빈 시간 채움(gap)」을 이 기록들 것만 센다(다른 시간대를 먼저 돌려 본 기록이 섞이지 않게) */
  function prefill(M, dow, t0, t1) { var U = {}; Object.keys(M.nodes).forEach(function (id) { var n = M.nodes[id]; if (n.ty !== 'sig' || !n.plan || !n.plan.recs) return; var u = U[id] = []; for (var t = t0; t <= t1; t += 60) { var P = planAt(M, id, t, dow, null), r = n.plan.recs.filter(function (x) { return x.win === P.win; })[0]; if (r && u.indexOf(r) < 0) u.push(r); } }); return U; }
  function winUsed(p, u) { if (!p.recs || !u) return allWin(p); var o = []; p.recs.forEach(function (r) { var mine = u.indexOf(r) >= 0; r.win.forEach(function (w) { if (w[4] !== 'gap' || mine) o.push(w); }); }); return o; }
  /* 녹색 창 → 현시(수동 조작용) — 녹색이 새로 켜지는 때마다 한 현시 */
  function winToPhases(w, c, Y, AR) {
    var S = []; w.forEach(function (r) { if (S.indexOf(r[3]) < 0) S.push(r[3]); }); S.sort(function (a, b) { return a - b; });
    return S.map(function (s, i) { var e = S[i + 1] != null ? S[i + 1] : c; return { d: e - s, y: (Y && Y[i]) || 3, ar: (AR && AR[i]) || 1, mv: w.filter(function (r) { return s >= r[3] && s < r[3] + r[1]; }).map(function (r) { return r[0]; }) }; });
  }
  /* 그 시각(자정부터 초)의 신호 계획 { c 주기, off 옵셋, win 녹색 창, pat 패턴 번호, src, ph 현시 }
     현시도(tod·pat·dir) · T-Data 기록(recs — 요일 갈래·시각마다 한 기록 · 맞는 갈래가 없으면 가장 가까운 시각) · 재편안(alt — 현시 목록) */
  function planAt(M, id, t, dow, alt, noTw) {
    var n = M.nodes[id], P = alt && alt[id]; if (P && P.length) P = P.filter(function (x) { return t >= x.t0 && t < x.t1; })[0];   /* 시간대마다 다른 안(배열) — 실제 돈 신호(T-Data 시간별) 재현 등 */
    if (P && (P.t0 == null || (t >= P.t0 && t < P.t1))) { var w0 = phasesToWin(P.ph); return { c: w0.c, off: P.off || 0, win: w0.win, src: '재편안', ph: P.ph }; }
    var p = n.plan;
    if (p.recs) {
      var best = null, bs = 1e9;
      p.recs.forEach(function (r) { var dsc = r.dk.indexOf(dow) >= 0 ? 0 : 1e6, h = Math.abs(r.t - t); if (dsc + h < bs) { bs = dsc + h; best = r; } });
      // 그 기록에 빠진 이동류(T-Data 가 몇 개만 읽힌 기록)는 그 이동류가 있는 가장 가까운 기록에서 채운다(주기 비율로 늘이거나 줄임 · 지도 신호 카드의 「채움」과 같은 생각)
      if (!best.full) fillRec(M, n, p, best);
      return { c: best.cyc, off: best.off || 0, win: best.win, src: p.src, day: best.day, ph: winToPhases(best.win, best.cyc) };
    }
    if (p.win) return { c: p.cyc, off: 0, win: p.win, src: p.src, ph: winToPhases(p.win, p.cyc) };
    var L = p.tod[String(TODK[dow])], cur = L[L.length - 1];
    L.forEach(function (r) { if (hm(r[0]) <= t) cur = r; });
    var pt = String(cur[2]), pa = p.pat[pt], W = p.dir[pt];
    // 시차제(현시도 tw — 그 요일 계획·시간대에는 그 이동류 녹색만 짧게 · 녹색 시작은 그대로) · 4034 평일 16~20시 서→동 직진 23초(형님 「삼호가든 방향 차가 너무 많아 직진 시간을 줄였다」 = 게임 ms.stMaryMetering)
    if (!noTw && p.tw) p.tw.forEach(function (x) { if (x.tod.indexOf(String(TODK[dow])) < 0 || t < hm(x.from) || t >= hm(x.to)) return; var k = x.dir + '.' + x.mv; W = W.map(function (r) { return r[0] === k ? [r[0], x.g, x.y, r[3], 'tw'] : r; }); });
    return { c: pa.c, off: pa.off, win: W, pat: pt, src: p.src, ph: p.ph.map(function (mv, i) { return { d: pa.a[i], y: p.Y[i], ar: p.AR[i], mv: mv }; }) };
  }
  /* 빈 시간 채움(자동 구역만 · 2026-10-25) — T-Data 기록이 큰길 직진만 읽고 옆길 방향을 하나도 못 읽은 교차로는 그 옆길이 시뮬에서 늘 적색이 된다(서초3동우체국 서쪽 · 이수역(연등) 등).
     주기 안에서 읽힌 녹색(+황색 · 전적색 1초)이 하나도 없는 가장 긴 빈 시간을 그 옆길의 녹색으로 준다(직진·좌회전 · 황색 4초 · 설계값 — 실제 신호는 보행 현시가 끼어 더 짧을 수 있다) · 서로 직각인 두 갈래가 비면 반씩 나눈다 · 표시 'gap' */
  function gapFill(n, W, C) {
    var cov = {}; W.forEach(function (r) { cov[String(r[0]).split('.')[0]] = 1; });
    var miss = Object.keys(n.legs).filter(function (lg) { return n.legs[lg].in && !cov[lg]; }); if (!miss.length) return;
    var iv = []; W.forEach(function (r) { var a = ((r[3] % C) + C) % C, b = a + r[1] + (r[2] || 4) + 1; if (b > C) { iv.push([a, C]); iv.push([0, b - C]); } else iv.push([a, b]); });
    iv.sort(function (x, y) { return x[0] - y[0]; }); var mg = []; iv.forEach(function (x) { var l = mg[mg.length - 1]; if (l && x[0] <= l[1]) l[1] = Math.max(l[1], x[1]); else mg.push([x[0], x[1]]); });
    if (!mg.length) return; var bs = 0, bl = 0; for (var i = 0; i < mg.length; i++) { var e = mg[i][1], nx = i + 1 < mg.length ? mg[i + 1][0] : mg[0][0] + C, L = nx - e; if (L > bl) { bl = L; bs = e; } }
    var g = bl - 5; if (g < 5) return;
    var ax = { ns: miss.filter(function (lg) { return lg === 'nt' || lg === 'st'; }), ew: miss.filter(function (lg) { return lg === 'et' || lg === 'wt'; }) }, grp = [ax.ns, ax.ew].filter(function (x) { return x.length; });
    var gl = grp.length > 1 ? Math.floor((bl - 10) / 2) : g, st = bs;
    grp.forEach(function (G) { if (gl >= 5) G.forEach(function (lg) { ['St', 'Lt'].forEach(function (tu) { W.push([lg + '.' + tu, gl, 4, Math.round(st) % C, 'gap']); }); }); st += gl + 5; });
  }
  function allWin(p) { return p.recs ? [].concat.apply([], p.recs.map(function (r) { return r.win; })) : p.win || [].concat.apply([], Object.keys(p.dir).map(function (k) { return p.dir[k]; })); }

  function create(M, scen, alt) {
    scen = scen || {}; var DS = M.design, dow = dowOf(scen.date || M.date0 || '2026-10-18'), VK = VOLK[dow];
    var JAM = 0.8, sp = M.spacing.v, satS = M.sat.v / 3600, vf = (scen.freeV || DS.freeV.v) / 3.6, lost = DS.lostStart.v, rtRed = scen.rtRed != null ? scen.rtRed : DS.rtRed.v;
    var boxP = scen.box != null ? scen.box : DS.box.v, R = rng(scen.seed || 7), RB = rng((scen.seed || 7) + 101), RD = rng((scen.seed || 7) + 202), RO = rng((scen.seed || 7) + 303);   // 길(R) · 꼬리물기(RB) · 머무는 시간(RD) · 나가는 차의 길(RO) — 판마다 달라지는 것은 R 을 쓰지 않아 두 판이 같은 차를 쓴다
    /* 구역 밖 막힘(자동 구역 · 2026-10-25) — 나가는 길(sink)에 그 너머 1.5km 평소 속도(onsp · 요일 갈래-시 · 가장 느린 링크)가 있으면 빠지는 속도를 줄인다: 18km/h↑ 그대로 · 6km/h 면 0.2배 · 아래로 0.15배(설계값) — 끄기 scen.noOut */
    var DKO = [3, 0, 0, 0, 0, 1, 2][dow], OUTK = {}, NOOUT = scen.noOut != null ? scen.noOut : (!scen.noCal && M.cal && M.cal.noOut); if (!NOOUT) Object.keys(M.links).forEach(function (k) { if (M.links[k].sink && M.links[k].onsp) OUTK[k] = M.links[k].onsp; });
    function outFac(k, t) { var v = OUTK[k][DKO + '-' + Math.min(23, Math.floor(t / 3600))]; return v == null ? 1 : Math.max(0.15, Math.min(1, (v - 3) / 15)); }
    var FROM = scen.from != null ? scen.from : 16 * 3600, WARM = scen.warm != null ? scen.warm : 7200, USED = prefill(M, dow, FROM - WARM, scen.to != null ? scen.to : 22 * 3600);   // 몸풀기 2시간 — 빈 길에서 시작하면 16시에 이미 쌓여 있던 차가 없다
    // 조치(라바콘·입차 중단 …) 모으기
    var ACT = { closeEntry: {}, mvp: {}, attOff: {}, attInStop: {}, attOutFirst: {}, noTw: {}, attInCap: {}, doorShare: {}, boxGuard: {} };
    (scen.act || []).forEach(function (aid) { var a = (M.actions || []).filter(function (x) { return x.id === aid; })[0]; if (!a) return;
      (a.closeEntry || []).forEach(function (e) { ACT.closeEntry[e] = 1; }); Object.keys(a.mvp || {}).forEach(function (k) { ACT.mvp[k] = a.mvp[k]; });
      ['attOff', 'attInStop', 'attOutFirst', 'noTw'].forEach(function (f) { (a[f] || []).forEach(function (x) { ACT[f][x] = 1; }); }); Object.keys(a.attInCap || {}).forEach(function (k) { ACT.attInCap[k] = a.attInCap[k]; }); Object.keys(a.boxGuard || {}).forEach(function (k) { ACT.boxGuard[k] = a.boxGuard[k]; });
      Object.keys(a.doorShare || {}).forEach(function (k) { ACT.doorShare[k] = Object.assign(ACT.doorShare[k] || {}, a.doorShare[k]); }); });   /* 출차 우회 — 문마다 나오는 몫을 바꿈 */
    var S = { M: M, from: FROM, t: FROM - WARM, end: scen.to != null ? scen.to : 22 * 3600, L: {}, mv: {}, N: {}, V: [], done: 0, delay: 0, boxN: 0, back: {}, samp: [], pre: [], log: [], rtBlk: {}, A: {} };
    /* 🚧 도로 위 일(scen.ev · 2026-11-03 · intent/20261102-road-sim-anywhere.md 3단계) — [{link, kind 'acc' 사고·'work' 공사·'bus' 버스 정차·'park' 불법 주정차·'ctrl' 통제, k 막힌 차로(0 = 갓길·가장자리), nb 버스 대/시, cars 주정차 대수, len 공사 m, t0·t1 자정부터 초}]
       그 길에서 빠지는 힘(f)과 설 자리(cf)를 줄이고 · 통제·모든 차로 막힘은 닫는다(못 들어감 · 그 앞에서 다른 길로 돌린다 · 꼬리물기로 들어가지도 않는다) · 계수 = evFactor */
    var EVS = (scen.ev || []).filter(function (e) { return M.links[e.link] && !M.links[e.link].sink; }), EVN = {}, RE = rng((scen.seed || 7) + 404); S.evDiv = 0;
    function evTick(t) { EVN = {}; EVS.forEach(function (e) { if (t < e.t0 || t >= e.t1) return; var l = M.links[e.link], x = evFactor(e, l.lanes, l.len), o = EVN[e.link] || (EVN[e.link] = { f: 1, cf: 1, shut: false }); o.f *= x.f; o.cf *= x.cf; if (x.shut) o.shut = true; }); }
    Object.keys(M.links).forEach(function (k) { var l = M.links[k]; S.L[k] = { id: k, l: l, n: 0, cap: l.sink ? 1e9 : Math.max(2, l.len * l.lanes / sp), tt: l.sink ? 0 : l.len / vf }; });
    function addMv(node, key, fr, to, la, kind, cap, p) { var id = fr + '>' + to; S.mv[id] = { id: id, node: node, key: key, fr: fr, to: to, la: la, kind: kind, cap: cap, p: p == null ? 1 : p, q: [], acc: 0, served: 0, gs: 0 }; return S.mv[id]; }
    // 신호 교차로 이동류 — 다리(legs)와 현시에서
    Object.keys(M.nodes).forEach(function (id) {
      var n = M.nodes[id]; S.N[id] = { id: id, n: n, box: [], manual: null };
      if (n.ty !== 'sig') return;
      var any = {}; winUsed(n.plan, USED[id]).forEach(function (r) { any[r[0]] = 1; }); (n.free || []).forEach(function (k) { any[k] = 1; });
      Object.keys(n.legs).forEach(function (lg) {
        var I = n.legs[lg].in; if (!I || !TURN[lg]) return; var ln = M.links[I].lanes;
        ['St', 'Lt', 'Rt'].forEach(function (tu) {
          var key = lg + '.' + tu, O = n.legs[TURN[lg][tu]] && n.legs[TURN[lg][tu]].out;
          if (!O || (tu !== 'Rt' && !any[key]) || (n.ban || []).indexOf(key) >= 0) return;
          var hasL = any[lg + '.Lt'] ? 1 : 0, rl = (n.rtLane || {})[lg], la = tu === 'St' ? Math.max(1, ln - hasL - (rl ? 0 : 0.5)) : tu === 'Lt' ? (ln >= 2 ? 1 : 0.5) : (rl || 0.5);   /* rtLane = 라바콘 등으로 가른 우회전 전용 차로(그만큼 · 직진과 나눠 쓰지 않음) */   // 차로 나눔(설계값): 좌회전 1 · 우회전은 바깥 차로를 직진과 나눠 반 · 나머지 직진
          addMv(id, key, I, O, la, (n.free || []).indexOf(key) >= 0 ? 'free' : tu === 'Rt' ? 'rt' : 'sig');
        });
        /* 유턴(n.uturn — 그 접근로 1차로 · 그 접근로 좌회전 녹색에 같이 · 좌회전 차로를 나눠 씀 · 설계값 반 차로) — 2026-10-30 소유자 확인(FK-BLOCK-WEST) */
        if ((n.uturn || []).indexOf(lg) >= 0 && n.legs[lg].out && any[lg + '.Lt']) { var mu = addMv(id, lg + '.Ut', I, n.legs[lg].out, 0.5, 'sig'); mu.gkey = lg + '.Lt'; }
      });
    });
    // 신호 없는 갈림·합류(mvx · 자료가 준다)
    (M.mvx || []).forEach(function (x) { var m = addMv(x.node, x.key, x.fr, x.to, x.la, x.kind || 'free', x.cap, x.p); if (ACT.mvp[m.id] != null) m.p = ACT.mvp[m.id]; });
    // 끌어들이는 곳(att) — 들어가는 문(이동류 kind cap)과 나오는 길
    (M.att || []).forEach(function (a0) {
      var a = Object.assign({}, a0, (scen.att || {})[a0.id] || {}); a.off = ACT.attOff[a.id] || (scen.att && scen.att[a.id] && scen.att[a.id].off); a.inStop = ACT.attInStop[a.id]; a.outFirst = ACT.attOutFirst[a.id];
      S.L['att:' + a.id] = { id: 'att:' + a.id, l: { nm: a.nm, att: a.id }, n: 0, cap: 1e9, tt: 0, sinkA: 1 };
      // 문(doors) — 문마다 들어가는 길(ins · 그 길에서 오른쪽으로 들어감)·받는 속도(cap)·나오는 길(out)·나오는 몫(share) · 문이 없던 옛 자료는 문 하나로
      if (a.mode !== 'flow') { a.doors = (a.doors || [{ id: 'd', nm: a.nm, node: a.node, ins: [a.inFrom9], cap: a.inCap, out: a.outLink, share: 1 }]).map(function (d0) { var d = Object.assign({}, d0); if (ACT.doorShare[a.id] && ACT.doorShare[a.id][d.id] != null) d.share = ACT.doorShare[a.id][d.id]; d.mv = (d.ins || []).map(function (L) { return addMv(d.node || 'door', 'att', L, 'att:' + a.id, 1, 'cap', a.inStop ? 0 : (d.cap != null ? d.cap : a.inCap)); }); d.q9 = []; d.mAcc = 0; return d; }); a.outLink = a.doors[0].out; }
      // 주차장 자리(capacity) — 소유자 「신세계·메리어트 주차장은 하나 · 평일도 만차가 잦다 · 주차장 차가 나가야 정체가 풀린다」 → 가득 차면 문이 닫혀 들어가려는 차가 길에서 기다리고, 나가는 차만큼 자리가 난다 · 시작 때 차 있는 몫 occ0(설계값)
      S.A[a.id] = { a: a, held: 0, acc: 0, occ: a.capacity != null ? Math.round(a.capacity * (a.occ0 != null ? a.occ0 : 0.5)) : null, ex: {} };
      // 머무는 시간(dwell 분 · 설계값)이 있으면 들어간 차가 그만큼 머문 뒤 나간다(나가는 차 = 들어온 차의 뒤따름) · 시작 때 있던 차는 그 시간 안에 고르게 나간다
      if (a.dwell && S.A[a.id].occ) { var X0 = S.A[a.id], t00 = FROM - WARM; for (var q0 = 0; q0 < X0.occ; q0++) { var te0 = t00 + Math.floor((q0 + 0.5) / X0.occ * a.dwell * 60 * 1.2); X0.ex[te0] = (X0.ex[te0] || 0) + 1; } }
      (a.doors || []).forEach(function (d, i) { d.i = i; d.mv.forEach(function (m) { m.att9 = S.A[a.id]; m.door9 = d; }); });
    });
    // 길 찾기(차를 만들 때 한 번) — 들어온 길에서 이동류를 차례로 고른다
    var outOf = {}; Object.keys(S.mv).forEach(function (k) { var m = S.mv[k]; (outOf[m.fr] = outOf[m.fr] || []).push(m); });
    var TS = { Lt: (scen.turn || DS.turn).Lt, Rt: (scen.turn || DS.turn).Rt };
    /* 길 고르기 시험판(route2 · 2026-11-03 · 기본 끔) — ① T자 교차로에서 없는 회전 몫을 있는 회전끼리 다시 나눔 ② 신호 셋을 지나면 곧장 나가는 길이 있을 때만 나가고 다섯이면 어디로든
       datamap 세션 길별 진단(서초역 법원후문 서쪽·서초대로 헛막힘)에서 나옴 · 짝수 날 그림자 판정: 헛막힘은 줄지만 실제 막힘도 덜 잡아(4구역 트윈 막힘 95→51/146 · 나가는 길 너머 막힘을 함께 끄면 66) 균형 점수가 나빠져 기본으로 안 켬
       켜기 = scen.route2 또는 구역 cal.route2(sim-cal.py SIMCAL_ROUTE2=1) */
    var R2 = scen.route2 != null ? scen.route2 : !!(M.cal && M.cal.route2);
    function isAtt(m) { return m.to.slice(0, 4) === 'att:'; }
    function wander(start, r) {
      var p = [start], cur = start, sig = 0;
      for (var g = 0; g < 14; g++) {
        var L = M.links[cur]; if (!L || L.sink) return p;
        var O = (outOf[cur] || []).filter(function (m) { return !isAtt(m) && m.p > 0; });
        if (EVS.length) { var O2 = O.filter(function (m) { return !(EVN[m.to] && EVN[m.to].shut); }); if (O2.length) O = O2; }   /* 닫힌 길(통제)은 피해 간다 */
        if (!O.length) return p;
        var nx;
        if (M.nodes[L.to].ty === 'sig') {
          sig++;
          var sinks = O.filter(function (m) { return M.links[m.to].sink; });
          if (!R2 && sig >= 3 && sinks.length) nx = sinks[Math.floor(r() * sinks.length)];   /* 종전 — 신호 셋을 지나면 아무 나가는 길로 */
          else { var x = r(), up = M.nodes[L.to].uturnP || 0, ut = up && O.filter(function (m) { return m.key.split('.')[1] === 'Ut'; })[0];   /* 유턴 몫(uturnP · 설계값) — 그 몫이면 유턴 · 아니면 남은 몫을 좌·우·직으로 다시 나눔 */
            if (ut && x < up) nx = ut; else { if (ut) x = (x - up) / (1 - up); var tu = x < TS.Lt ? 'Lt' : x < TS.Lt + TS.Rt ? 'Rt' : 'St'; nx = O.filter(function (m) { return m.key.split('.')[1] === tu; })[0];
            if (!nx && R2) { var W9 = O.filter(function (m) { return m.key.split('.')[1] !== 'Ut'; }).map(function (m) { var q = m.key.split('.')[1]; return [m, q === 'Lt' ? TS.Lt : q === 'Rt' ? TS.Rt : 1 - TS.Lt - TS.Rt]; }), tw = W9.reduce(function (a9, w) { return a9 + w[1]; }, 0), y9 = r() * tw;
              for (var j9 = 0; j9 < W9.length; j9++) { y9 -= W9[j9][1]; if (y9 < 0) { nx = W9[j9][0]; break; } } }   /* 그 회전이 없는 교차로(T자 · 직진 없음) — 있는 회전끼리 몫을 다시 나눔(종전엔 모자란 몫이 첫 이동류(좌회전)로 몰려 법원후문 서쪽 좌회전 19초에 줄이 늘 찼다 · 2026-11-03) */
            nx = nx || O.filter(function (m) { return m.key.split('.')[1] === 'St'; })[0] || O[0];
            if (R2 && sig >= 3 && sinks.length && !M.links[nx.to].sink) { var sSt = sinks.filter(function (m) { return m.key.split('.')[1] === 'St'; })[0]; if (sSt) nx = sSt; else if (sig >= 5) nx = sinks[Math.floor(r() * sinks.length)]; }   /* 자동 구역 — 신호 셋을 지나면 곧장 나가는 길이 있을 때만 나가고 · 다섯을 지나면 어디로든 나감(종전엔 셋째부터 아무 나가는 길로 → 법원정문에서 서초대로 직진 차가 모두 우회전 한 차로로 몰려 서초역·대법원까지 늘 막힘) */
          } }
        } else { var tot = O.reduce(function (s9, m) { return s9 + m.p; }, 0), y = r() * tot; nx = O[O.length - 1]; for (var j = 0; j < O.length; j++) { y -= O[j].p; if (y < 0) { nx = O[j]; break; } } }
        if (!nx) { S.log.push('길 없음 ' + cur); return p; }
        p.push(nx.to); cur = nx.to;
      }
      return p;
    }
    function route(start, goal) {   // 가장 적은 이동류로 goal 길까지(너비 우선)
      var Q = [[start]], seen = {}; seen[start] = 1;
      while (Q.length) { var p = Q.shift(), c = p[p.length - 1]; if (c === goal) return p; (outOf[c] || []).forEach(function (m) { if (isAtt(m) || m.p <= 0) return; if (!seen[m.to] && !(M.links[m.to] || {}).sink || m.to === goal) { seen[m.to] = 1; Q.push(p.concat([m.to])); } }); }
      return null;
    }
    // 수요(대/시) — 들어오는 길마다 그 시각 값
    function bgRate(e, t) {
      var E = M.entry[e], h = Math.min(23, Math.floor(t / 3600)), CL = !scen.noCal && M.cal, sc = (scen.bg && scen.bg[e] != null ? scen.bg[e] : CL && CL.scale[e] != null ? CL.scale[e] : 1) * (scen.bgAll || (CL ? CL.all : 1));
      if (ACT.closeEntry[e]) return 0;
      if (E.wdx != null && dow >= 1 && dow <= 5) sc *= E.wdx;   /* 평일(월~금)에만 곱하는 배율 — 평일 실측과 맞대 고른 설계값(일요일 재현은 그대로) */
      if (E.spot) { var v = M.vol[E.spot][VK][h]; return (v[0] + v[1]) / 2 * (scen.share && scen.share[e] != null ? scen.share[e] : E.share) * sc; }
      return (E.perLane * M.links[e].lanes) * sc;
    }
    function win(t, a, b, pk) { var h = t / 3600; return h >= a && h < b ? pk : 0; }
    var dem = [];
    Object.keys(M.entry).forEach(function (e) { dem.push({ k: 'bg', e: e, f: function (t) { return bgRate(e, t); }, acc: 0 }); });
    Object.keys(S.A).forEach(function (id) {
      var a = S.A[id].a; if (a.off || (a.days && a.days.indexOf(dow) < 0) || (a.months && a.months.indexOf(+String(scen.date || M.date0 || '2026-10-18').split('-')[1]) < 0)) return;
      if (ACT.attInCap[id] != null) a.inPeak = Math.min(a.inPeak, ACT.attInCap[id]);   // 라바콘 원거리 차로 축소 — 받을 수 있는 만큼만 들여보낸다(나머지는 이 구역에 안 들어옴)
      if (a.mode === 'flow') { Object.keys(a.from).forEach(function (e) { dem.push({ k: a.to ? 'fl' : 'bg', att: a.to ? id : null, e: e, f: function (t) { var pm = a.pulse && a.pulse[String(Math.floor(t % 3600 / 60 / 10) * 10)] || 1; return win(t, a.inT0, a.inT1, a.inPeak) * a.from[e] * pm; }, acc: 0 }); }); return; }
      if (a.mode === 'table') {   // 시간표(고속버스 — 요일 갈래 월~목·금·토·일 × 시각 · 도착 = 들어감 · 출발 = 나옴) × 승용차 환산(pcu)
        var TB = (M.tbl || {})[a.table], tk = DAYK[dow], rowOf = function (t, w) { var r = TB && TB.t[tk] && TB.t[tk][a.term]; return r ? r[w][Math.min(23, Math.floor(t / 3600))] * (a.pcu || 1) * (a.scale != null ? a.scale : 1) : 0; };
        if (!a.inStop) Object.keys(a.from).forEach(function (e) { dem.push({ k: 'ai', e: e, att: id, f: function (t) { return rowOf(t, 'in') * a.from[e]; }, acc: 0 }); });
        dem.push({ k: 'ao', e: null, att: id, f: function (t) { return rowOf(t, 'out'); }, acc: 0 }); return;
      }
      if (!a.inStop) Object.keys(a.from).forEach(function (e) { dem.push({ k: 'ai', e: e, att: id, f: function (t) { return win(t, a.inT0, a.inT1, a.inPeak) * a.from[e]; }, acc: 0 }); });
      if (a.mode === 'store' && !a.dwell) dem.push({ k: 'ao', e: null, att: id, f: function (t) { return win(t, a.outT0, a.outT1, a.outPeak); }, acc: 0 });
    });
    var RT = {}; function cached(a, b) { var k = a + '|' + b; return RT[k] || (RT[k] = route(a, b)); }
    function makeV(k, e, t, att) {
      var p, a = att && S.A[att].a;
      if (k === 'bg') p = wander(e, R);
      else if (k === 'ini') p = wander(e, RI);   /* 지금 상태에서 출발(scen.init)로 길에 미리 올린 차 — 따로 굴린 주사위라 다른 차의 길은 그대로 */
      else if (k === 'fl') { p = cached(e, a.to) || wander(e, R); }   // 가는 곳이 정해진 지나가는 수요(학원 → 궁전·삼호가든 학원가 등)
      else if (k === 'fo') p = wander(e, RO);
      else if (k === 'ai') {   // 가장 가까운 문(이동류가 가장 적은 길)으로
        var best = null; a.doors.forEach(function (d) { d.ins.forEach(function (L) { var q = cached(e, L); if (q && (!best || q.length < best.length)) best = q; }); });
        p = best ? best.concat(['att:' + att]) : wander(e, R);
      }
      else if (k === 'ao') { var tot = 0, x = RO(), dd = a.doors[a.doors.length - 1]; a.doors.forEach(function (d) { tot += d.share != null ? d.share : 1; }); x *= tot; for (var j = 0; j < a.doors.length; j++) { x -= a.doors[j].share != null ? a.doors[j].share : 1; if (x < 0) { dd = a.doors[j]; break; } }
        var fx = a.outTo && cached(dd.out, a.outTo); p = fx ? ['att:' + att].concat(fx) : ['att:' + att, dd.out].concat(wander(dd.out, RO).slice(1)); var v0   /* outTo = 나가는 차가 가는 곳이 정해진 경우(예: 호남선 버스 → 잠원IC · 소유자 현장 지식) */ = { k: k, att: att, p: p, i: 0, t0: t, ff: 0, rd: 0, door: dd }; S.V.push(v0); return v0; }
      var v = { k: k, att: att, p: p, i: 0, t0: t, ff: 0, rd: 0 }; S.V.push(v); return v;
    }
    function enter(v, lk, t) {   // 길에 올림
      var L = S.L[lk]; v.i = v.p.indexOf(lk, v.i); L.n++; v.ff += L.tt; v.rd = t + L.tt;
      if (L.sinkA) { L.n--; var X9 = S.A[L.l.att]; if (X9.a.mode === 'hold') X9.held++; if (X9.occ != null) X9.occ++; if (X9.a.dwell) { var te = t + Math.round(X9.a.dwell * 60 * (0.5 + RD())); X9.ex[te] = (X9.ex[te] || 0) + 1; } finish(v, t); return; }
      if (L.l.sink || v.i >= v.p.length - 1) { L.n--; finish(v, t); return; }
      var m = S.mv[lk + '>' + v.p[v.i + 1]]; if (!m) { L.n--; finish(v, t); return; }
      S.inn[lk] = (S.inn[lk] || 0) + 1;
      m.q.push(v);
    }
    function divert(m, t) {   /* 닫힌 길 앞(정지선)에 닿은 차 — 경찰이 다른 이동류로 돌린다(돌린 뒤 길은 따로 굴린 주사위 RE · 끌어들이는 곳으로 가던 차도 그냥 돌아다님) */
      var alt = (outOf[m.fr] || []).filter(function (x) { return x !== m && !isAtt(x) && x.p > 0 && !(EVN[x.to] && EVN[x.to].shut); }); if (!alt.length) return;
      var nW = waiting(m.q); for (var j = 0; j < nW; j++) { var v = m.q.shift(), a = alt[Math.floor(RE() * alt.length)]; v.p = v.p.slice(0, v.i + 1).concat([a.to]).concat(wander(a.to, RE).slice(1)); var ix = 0; while (ix < a.q.length && a.q[ix].rd <= v.rd) ix++; a.q.splice(ix, 0, v); S.evDiv++; }
    }
    function finish(v, t) { S.done++; v.te = t; if (v.t0 >= FROM) S.delay += Math.max(0, t - v.t0 - v.ff); }
    function room(lk) { var L = S.L[lk], E = EVN[lk]; if (E && E.shut) return false; return L.l && L.l.sink || L.sinkA || L.n < L.cap * (E ? E.cf : 1); }
    // 신호
    function greenSet(id, t) {
      var N = S.N[id], G = {};
      if (N.manual) { var ma = N.manual; (ma.clr > 0 ? ma.keep : ma.ph[ma.i].mv).forEach(function (m) { G[m] = 1; }); return G; }
      var P = planAt(M, id, t, dow, alt, ACT.noTw[id]), c = P.c, x = ((t - P.off) % c + c) % c;
      P.win.forEach(function (r) { var a = (x - r[3] + c) % c; if (a >= lost && a < r[1] + r[2] - 1) G[r[0]] = 1; });
      if (AC && AC.mode === 'drop' && S.ac.on && id === AC.node) (AC.cut || []).forEach(function (m) { delete G[m]; });
      (S.drop[id] || []).forEach(function (m) { delete G[m]; });   /* 손으로 빼기(⛔) — 그 이동류만 적색 */   /* 자동 끊기 「빼기」 — 차례는 그대로 돌고 그 이동류만 적색 */
      N.cur = P; return G;
    }
    S.inn = {};
    S.step = function () {
      var t = S.t; S.inn = {};
      if (EVS.length) { evTick(t); Object.keys(EVN).forEach(function (lk) { if (EVN[lk].shut) Object.keys(S.mv).forEach(function (k9) { var m9 = S.mv[k9]; if (m9.to === lk) divert(m9, t); }); }); }
      if (AC && t >= S.from - 600 && t % (AC.every || 5) === 0) autoCut(t);
      if (INI && t === INI.at) Object.keys(INI.fill).forEach(function (lk) { var L = S.L[lk]; if (!L || L.l.sink) return; var add = Math.round(Math.min(1, INI.fill[lk]) * L.cap) - L.n; for (var q = 0; q < add; q++) { var vi = makeV('ini', lk, t); enter(vi, lk, t); } if (add < 0 && INI.trim !== false) { var ex = -add; Object.keys(S.mv).forEach(function (mk) { var m9 = S.mv[mk]; if (m9.fr !== lk) return; while (ex > 0 && m9.q.length) { var vg = m9.q.pop(); vg.te = t; vg.gone = 1; L.n--; ex--; S.iniOut = (S.iniOut || 0) + 1; } }); }   /* 빼기(2026-11-03 · datamap 그림자 운행 채점 제안) — 실측상 뚫린 길에 시뮬이 쌓아 둔 차는 늦게 들어온 차부터 뺀다(셈에서 빠짐 · gone) · 끄기 init.trim:false */ S.iniN = (S.iniN || 0) + Math.max(0, add); });
      Object.keys(S.N).forEach(function (id) { var ma = S.N[id].manual; if (ma && ma.clr > 0) { ma.clr--; if (!ma.clr) { ma.i = ma.next; ma.keep = []; } } });
      // 1 차 만들기 → 들어오는 길(자리가 없으면 망 밖에서 기다림)
      dem.forEach(function (d) {
        d.acc += d.f(t) / 3600;
        while (d.acc >= 1) { d.acc -= 1; if (d.k === 'ao') { var XA = S.A[d.att]; if (XA.occ != null) { if (XA.occ <= 0) continue; XA.occ--; } var vo = makeV('ao', null, t, d.att); vo.door.q9.push(vo); continue; } (S.back[d.e] = S.back[d.e] || []).push(makeV(d.k, d.e, t, d.att)); }
      });
      Object.keys(S.A).forEach(function (id) { var X = S.A[id], n9 = X.ex[t]; if (!n9) return; delete X.ex[t]; for (var q = 0; q < n9; q++) { if (X.occ != null) X.occ--; var vo = makeV('ao', null, t, id); vo.door.q9.push(vo); } });   // 머문 시간이 다 된 차가 나가는 줄로
      Object.keys(S.A).forEach(function (id) {   // 머무는 곳(공원 등): 나가는 때가 되면 들어온 차만큼 내보냄
        var X = S.A[id], a = X.a, h = t / 3600; if (a.mode !== 'hold' || !X.held || a.off || h < a.outT0 || h >= a.outT1 + 1) return;
        X.acc += a.outRate / 3600; while (X.acc >= 1 && X.held > 0) { X.acc--; X.held--; var v = makeV('fo', a.outLink, t); (S.back[a.outLink] = S.back[a.outLink] || []).push(v); }
      });
      Object.keys(S.back).forEach(function (e) { var B = S.back[e]; while (B.length && room(e)) enter(B.shift(), e, t); });
      // 2 신호 교차로 — 녹색 이동류에서 빠짐
      var GS = {}; Object.keys(S.N).forEach(function (id) { if (M.nodes[id].ty === 'sig') GS[id] = greenSet(id, t); });
      // 꼬리물기로 교차로 안에 선 차 — 하류에 자리가 나면 먼저 빠진다
      Object.keys(S.N).forEach(function (id) { var N = S.N[id]; N.box = N.box.filter(function (b) { if (room(b.to)) { S.L[b.fr].n--; enter(b.v, b.to, t); return false; } return true; }); });
      // 끌어들이는 곳에서 나오는 차 — 나오는 길(합류)에 자리와 틈이 있을 때 · 출차 우선이면 본선보다 먼저
      /* 빙 도는 차(소유자 2026-10-25 「들어가려는 차와 나오는 차가 엉켜 · 고속버스터미널을 크게 한 바퀴 도는 차」) — 만차라 문 앞에 닿은 차는 서지 않고 지나가 블록을 돌아 다음 문(시계 방향)에서 다시 · 두 바퀴 돌고도 못 들어가면 포기하고 떠난다(설계값) */
      function circleOut(m, t) {
        var X = m.att9, D9 = X.a.doors, q = m.q;
        while (q.length && q[0].rd <= t) {
          var v = q.shift(), nd = D9[(m.door9.i + 1) % D9.length], tail = (v.circ || 0) < (X.a.circleMax || 2) ? cached(m.fr, nd.ins[0]) : null;
          tail = tail ? tail.concat(['att:' + X.a.id]) : wander(m.fr, RO);
          v.p = v.p.slice(0, v.i).concat(tail); v.circ = (v.circ || 0) + 1; if (v.circ === 1) X.circ = (X.circ || 0) + 1; X.circNow = (X.circNow || 0) + 1;
          var m2 = S.mv[m.fr + '>' + v.p[v.i + 1]]; if (!m2) { S.L[m.fr].n--; finish(v, t); continue; }
          var lo = 0, hi = m2.q.length; while (lo < hi) { var md = (lo + hi) >> 1; if (m2.q[md].rd <= v.rd) lo = md + 1; else hi = md; } m2.q.splice(lo, 0, v);   // 닿는 때 차례 지킴
        }
      }
      function attExit(d, lim) { var k = 0; while (d.q9.length && k < lim && room(d.out)) { var v = d.q9.shift(); v.i = 1; enter(v, d.out, t); k++; } return k; }
      /* 꼬리물기 차가 막는 흐름(2026-10-30) — 가로지르는 접근로는 모두 막고 · 맞은편은 둘 중 하나가 좌회전(유턴)일 때만 · 같은 접근로는 안 막는다.
         종전엔 교차로 전체를 세워 교차로 사이가 짧은 곳(언주로 110~180m)에서 두 교차로가 서로를 기다리며 영원히 안 풀렸다 · scen.boxAll = 종전 규칙 */
      var OPP = { nt: 'st', st: 'nt', et: 'wt', wt: 'et' }, BOXT = scen.boxT != null ? scen.boxT : 120;   /* BOXT = 꼬리물기 차가 가로지르는 흐름을 막는 가장 긴 시간(초 · 설계값) — 그 뒤엔 비켜 선 것으로 본다(두 교차로가 서로를 영원히 기다리는 엉킴을 풀려고 · 들어갈 자리가 날 때까지 기다리는 것은 그대로) */
      function boxHit(bk, mk) { if (scen.boxAll || !bk || !mk) return true; var a = bk.split('.'), b = mk.split('.'); if (a[0] === b[0]) return false; if (OPP[a[0]] !== b[0]) return true; return a[1] === 'Lt' || a[1] === 'Ut' || b[1] === 'Lt' || b[1] === 'Ut'; }
      function wv(X, d) { return d.weave != null ? d.weave : (X.a.weave || 0); }   /* 문마다 엉킴 몫 — 들어가는 곳·나오는 곳이 떨어진 문(반포대로 호남선 45%·20%)은 0 */
      function eachDoor(f) { Object.keys(S.A).forEach(function (id) { var X = S.A[id]; if (X.a.mode !== 'store' && X.a.mode !== 'table') return; X.a.doors.forEach(function (d) { f(X, d); }); }); }
      eachDoor(function (X, d) { var c9 = M.links[d.out].lanes * satS * (wv(X, d) && d.mv.some(function (m) { return m.q.length && m.q[0].rd <= t; }) ? 1 - wv(X, d) : 1); d.mAcc = Math.min(d.mAcc + c9, 2 * c9 + 1); if (X.a.outFirst) d.mAcc -= attExit(d, Math.floor(d.mAcc)); });
      Object.keys(S.mv).forEach(function (k) {
        var m = S.mv[k], q = m.q, on;
        if (m.kind === 'sig') on = GS[m.node] && GS[m.node][m.gkey || m.key]; else on = true;
        var box = (S.N[m.node] || NOBOX).box; var GD = ACT.boxGuard[m.node], BT = GD && GD.t != null ? GD.t : BOXT; if (box.length && box.some(function (b) { return b.to !== m.to && t - b.t0 < BT && boxHit(b.key, m.key); })) on = false;   /* 사거리 공간 확보(라바콘·경찰관 · 소유자 2026-10-30) — 사거리 안에 남은 차는 경찰관이 GD.t 초 안에 빼낸다 */
        var la = m.la - (m.key.slice(-2) === 'St' && S.rtBlk[m.fr] >= t - 1 ? 0.5 : 0);   // 우회전 차가 막혀 서 있으면 나눠 쓰는 바깥 차로가 직진에도 막힌다
        if (m.att9 && m.att9.occ != null && m.att9.occ >= m.att9.a.capacity) { on = false; if (m.att9.a.circle) circleOut(m, t); }   // 만차 — 문 닫힘 · 빙 도는 곳이면 다음 문으로
        if (m.door9 && m.door9.q9.length && wv(m.att9, m.door9)) la *= 1 - wv(m.att9, m.door9);   // 같은 문에서 나오는 차와 엉킴(들어가는 쪽이 그만큼 느림)
        if (EVN[m.fr]) la *= EVN[m.fr].f;   /* 도로 위 일 — 그 길에서 덜 빠진다(막힌 차로·버스·주정차) */
        if (OUTK[m.to]) la *= outFac(m.to, t);   /* 나가는 길 너머가 평소 막히는 시간 — 덜 빠진다(자동 구역 · onsp) */
        var rate = m.kind === 'cap' ? m.cap / 3600 * (m.door9 && m.door9.q9.length && wv(m.att9, m.door9) ? 1 - wv(m.att9, m.door9) : 1) : la * satS * (m.kind === 'rt' && !(GS[m.node] && GS[m.node][m.key]) ? rtRed : 1);
        if (!on || !q.length) { m.acc = 0; return; }
        m.gs++; m.acc = Math.min(m.acc + rate, Math.max(1, rate * 2));
        while (m.acc >= 1 && q.length && q[0].rd <= t) {
          if (m.att9 && m.att9.occ != null && m.att9.occ >= m.att9.a.capacity) break;
          var v = q[0];
          if (!room(m.to)) {
            if (m.kind === 'rt') S.rtBlk[m.fr] = t;
            if ((M.nodes[m.node] || {}).ty === 'sig' && box.length < 2 && !(EVN[m.to] && EVN[m.to].shut) && RB() < (scen.box === 0 ? 0 : ((M.nodes[m.node].boxMv || {})[m.key] != null ? M.nodes[m.node].boxMv[m.key] : boxP) * (GD ? (GD.p != null ? GD.p : 0) : 1))) {   /* GD.p = 경찰관이 정지선에서 세워도 남는 꼬리물기 몫(설계값) */   /* boxMv = 그 이동류만 꼬리물기 몫을 달리(현장 지식 · 설계값) */ q.shift(); m.acc -= 1; box.push({ v: v, fr: m.fr, to: m.to, key: m.key, t0: t }); S.boxN++; }
            break;
          }
          q.shift(); m.acc -= 1; S.L[m.fr].n--; m.served++;
          enter(v, m.to, t);
        }
      });
      eachDoor(function (X, d) { if (X.a.outFirst) return; d.mAcc -= S.inn[d.out] || 0; if (d.mAcc >= 1) d.mAcc -= attExit(d, Math.floor(d.mAcc)); if (d.mAcc < 0) d.mAcc = 0; });   // 본선이 먼저 쓰고 남은 틈으로
      if (t % 60 === 0) { if (t >= FROM) S.samp.push(sample()); else if (scen.keepWarm) S.pre.push(sample()); }   /* keepWarm — 몸풀기(빈 길 → 16시) 동안도 1분 표본을 따로(S.pre) · 「왜 밀리나」 차례를 몸풀기부터 */
      S.t++;
    };
    function waiting(q) { var lo = 0, hi = q.length; while (lo < hi) { var md = (lo + hi) >> 1; if (q[md].rd <= S.t) lo = md + 1; else hi = md; } return lo; }   // 닿는 때(rd)가 차례대로라 반으로 갈라 센다
    var SIDEK = {};
    function sample() {
      var ap = {}, tot = 0;
      Object.keys(S.mv).forEach(function (k) { var m = S.mv[k]; if ((M.nodes[m.node] || {}).ty !== 'sig') return; var a = m.node + '.' + m.key.split('.')[0], w = waiting(m.q); ap[a] = (ap[a] || 0) + w; tot += w; });
      var back = 0, bk = {}; Object.keys(S.back).forEach(function (e) { var n9 = S.back[e].length; back += n9; if (n9) bk[e] = n9; });
      var occ = {}; Object.keys(S.L).forEach(function (k) { var L = S.L[k]; if (!L.l.sink && !L.sinkA) occ[k] = Math.round(L.n); });
      var jam = []; Object.keys(S.N).forEach(function (id) { var n = M.nodes[id]; if (n.ty !== 'sig') return; Object.keys(n.legs).forEach(function (lg) { var I = n.legs[lg].in; if (!I) return; var SL = SIDEK[I] || (SIDEK[I] = side(M, I)), nn = 0, cc = 0; SL.forEach(function (k9) { if (S.L[k9]) { nn += S.L[k9].n; cc += S.L[k9].cap; } }); if (nn >= JAM * cc) jam.push(id + '.' + lg); });   /* 막힘 = 그 접근로 한 변 전체(앞 신호·갈림부터 정지선까지 · side)가 80% 넘게 참 — 마지막 짧은 토막만 보면 출구 차 몇 대에도 막힘으로 셌다(2026-10-30) */ });
      var att = {}; Object.keys(S.A).forEach(function (id) { var X = S.A[id]; if (!X.a.doors) return; var dq = 0, oq = 0, by = {}; X.a.doors.forEach(function (d) { var a9 = d.mv.reduce(function (s9, m) { return s9 + waiting(m.q); }, 0); dq += a9; oq += d.q9.length; by[d.id] = [a9, d.q9.length]; }); att[id] = { door: dq, out: oq, held: X.held, by: by, occ: X.occ, cap: X.a.capacity, circ: X.circ || 0 }; });
      return { t: S.t, jam: jam, ap: ap, q: tot, back: back, bk: bk, att: att, box: S.boxN, occ: occ };
    }
    // 수동 조작(넘기기 · 현시 지정) — 지금 계획의 현시를 이어받는다 · 실제 신호를 바꾸는 기능이 아니다
    /* 자동 끊기(2026-10-25 · 게임 세션 「진행상황」 제안 · 소유자 현장 조작 「⛔ 들어오는 차만 끊기」를 규칙으로) — scen.autoCut = { node, link, hi, lo, every }:
       every 초마다 link(블록 안 길) 점유가 hi 를 넘으면 그 교차로를 블록으로 들어가는 이동류(cut — 기본 서→동 직진·북→동 좌회전)가 없는 현시로 붙잡고(나오는 이동류 keep 이 있는 현시 먼저 · 황색·전적색 지나서),
       lo 아래로 내려가면 원래 계획으로 돌려보낸다 · 실제 신호를 바꾸는 기능이 아니다 — 견주기용 · 값은 설계값 */
    /* 지금 상태에서 출발(2026-10-30 · 소유자 「정확한 통행량이 없어도 신반포로가 시계 방향으로 꽉 찰 정도면 어느 정도 예측이 된다」) — scen.init = { at: 초, fill: { 길: 0~1 } }
       그 시각에 그 길을 그만큼 채운다(더 차 있으면 늦게 들어온 차부터 뺀다 · trim:false 면 그대로) · 꽉 참 = 길이 × 차로 ÷ 정지 차량 한 대 자리 · 그 뒤는 평소대로 굴러감 — 「지금 본 모습」이 몇 대인지를 대신한다 */
    var INI = scen.init && scen.init.fill ? scen.init : null, RI = rng((scen.seed || 7) + 404);
    var AC = scen.autoCut || null; S.ac = { n: 0, sec: 0, on: false }; S.drop = {};
    function autoCut(t) {
      var L = S.L[AC.link], r = L ? L.n / L.cap : 0, N = S.N[AC.node]; if (!N) return;
      if (S.ac.on) S.ac.sec += AC.every || 5;
      if (AC.mode === 'drop') { if (!S.ac.on && r >= (AC.hi || 0.85)) { S.ac.on = true; S.ac.n++; } else if (S.ac.on && r <= (AC.lo || 0.6)) S.ac.on = false; return; }   /* 빼기 — 형님 「좌회전으로 신세계 들어가는 차들이 너무 많아져 그걸 줄여야 할 때」: 신반포로 양방향은 그대로 보내고 북→동 좌회전만 막는다 */
      if (!S.ac.on && r >= (AC.hi || 0.85)) {
        if (!N.manual) S.manual(AC.node, true, AC.ph); var ma = N.manual, cut = AC.cut || ['wt.St', 'nt.Lt'], keep = AC.keep || 'et.St', j = -1;
        ma.ph.forEach(function (p, i) { if (j < 0 && !cut.some(function (c) { return p.mv.indexOf(c) >= 0; }) && p.mv.indexOf(keep) >= 0) j = i; });
        if (j < 0) ma.ph.forEach(function (p, i) { if (j < 0 && !cut.some(function (c) { return p.mv.indexOf(c) >= 0; })) j = i; });
        if (j < 0) { S.manual(AC.node, false); return; }
        S.go(AC.node, j); S.ac.on = true; S.ac.n++;
      } else if (S.ac.on && r <= (AC.lo || 0.6)) { S.manual(AC.node, false); S.ac.on = false; }
    }
    /* 수동 조작 — 지금 계획의 현시를 이어받는다 · ph 를 주면 수동일 때만 그 현시 목록(세분화)으로 고른다(자동 운영은 그대로 · 형님 건의 「수동 조작 때 고를 수 있는 현시 세분화」 · 2026-10-25) */
    S.manual = function (id, on, ph) { var N = S.N[id]; if (!on) { N.manual = null; return; } var P = ph ? { ph: ph } : planAt(M, id, S.t, dow, alt); var G = greenSet(id, S.t), best = 0, sc = -1; P.ph.forEach(function (p, i) { var s = p.mv.filter(function (m) { return G[m]; }).length; if (s > sc) { sc = s; best = i; } }); N.manual = { ph: P.ph, i: best, clr: 0, keep: [] }; };
    S.go = function (id, k) { var ma = S.N[id].manual; if (!ma) return; var j = k == null ? (ma.i + 1) % ma.ph.length : k; if (j === ma.i) return; var nx = ma.ph[j].mv, cu = ma.ph[ma.i]; ma.keep = cu.mv.filter(function (m) { return nx.indexOf(m) >= 0; }); ma.clr = cu.y + cu.ar + 1; ma.next = j; };
    S.runTo = function (t1) { while (S.t < Math.min(t1, S.end)) S.step(); return S; };
    S.result = function () {
      // 막힘 = 신호 교차로 접근로 가운데 점유 80% 넘는 곳이 3곳 이상(실측 ≤5km/h 와 맞대 보는 기준과 같다) · 해소 = 그 뒤 마지막으로 3곳 아래로 내려간 때
      var peak = 0, pkT = null, clr = null, st = null, A = S.samp, attW = function (s) { var w = 0; Object.keys(s.att).forEach(function (k) { w += s.att[k].out + s.att[k].door; }); return w; };
      A.forEach(function (s) { var v = s.q + s.back + attW(s); if (v > peak) { peak = v; pkT = s.t; } if (st == null && s.jam.length >= 3) st = s.t; });
      if (st != null) { for (var i = A.length - 1; i >= 0; i--) { if (A[i].jam.length >= 3) { clr = A[i + 1] ? A[i + 1].t : null; break; } } }
      var inNet = S.V.filter(function (v) { return v.te == null && v.t0 >= FROM; }), dl = S.delay + inNet.reduce(function (a, v) { return a + Math.max(0, S.t - v.t0 - v.ff); }, 0);
      var maxQ = {}; A.forEach(function (s) { Object.keys(s.ap).forEach(function (a) { var nd = a.split('.')[0], lg = a.split('.')[1], I = M.nodes[nd].legs[lg].in, m = s.ap[a] * M.spacing.v / M.links[I].lanes; if (!maxQ[a] || m > maxQ[a]) maxQ[a] = Math.round(m); }); });
      return { evDiv: S.evDiv || 0, delayVh: Math.round(dl / 3600), maxQm: maxQ, trappedMax: Math.max.apply(null, A.map(attW).concat([0])), jamStart: st, clearT: clr, jamMax: Math.max.apply(null, A.map(function (s) { return s.jam.length; }).concat([0])), acN: S.ac.n, acSec: S.ac.sec, peak: peak, peakT: pkT, box: S.boxN, made: S.V.length, done: S.done };
    };
    S.inNet = function () { var n = 0; Object.keys(S.L).forEach(function (k) { n += S.L[k].n; }); Object.keys(S.A).forEach(function (k) { (S.A[k].a.doors || []).forEach(function (d) { n += d.q9.length; }); }); Object.keys(S.back).forEach(function (e) { n += S.back[e].length; }); return n; };
    return S;
  }
  /* 한 변(접근로) = 정지선 길에서 거슬러 올라가 앞 신호·갈림까지 이어진 토막 전체(2026-10-30) — ITS 실측은 신호에서 신호까지 길 전체를 재는데,
     시뮬은 마지막 짧은 토막(반포대로 호남선 출구→정지선 30m · 차 12대 자리)만 재서 출구 차 몇 대에도 「꽉 참」이 되었다.
     거슬러 오르는 조건: 그 길이 시작하는 마디가 신호가 아니고 · 그 마디로 들어오는 길이 하나 · 나가는 길이 하나(갈림 앞에서 멈춤) */
  function side(M, k) {
    var out = [k], cur = k, inn = {}, outn = {};
    Object.keys(M.links).forEach(function (id) { var l = M.links[id]; if (l.sink) return; (inn[l.to] = inn[l.to] || []).push(id); (outn[l.fr] = outn[l.fr] || []).push(id); });
    for (var g = 0; g < 8; g++) { var fr = M.links[cur].fr, N = M.nodes[fr]; if (!N || N.ty === 'sig' || (inn[fr] || []).length !== 1 || (outn[fr] || []).length !== 1) break; cur = inn[fr][0]; if (out.indexOf(cur) >= 0) break; out.unshift(cur); }
    return out;
  }
  function sideOcc(S, s9, L) { var n = 0, c = 0; L.forEach(function (k) { if (!S.L[k]) return; n += s9.occ[k] || 0; c += S.L[k].cap; }); return c ? n / c : 0; }
  function run(M, scen, alt) { var S = create(M, scen, alt); S.runTo(S.end); return S; }
  /* 평소 속도로 맞추기(자동 구역) — 접근로 정지선 링크의 평소 속도(ITS 가운데값 · links[].nsp 「요일 갈래-시」)가 6km/h 넘는데 시뮬이 막히면(점유 80%↑) 그 들어오는 길 수요를 줄이고,
     평소에도 막히는데(6 이하 두 시간↑) 시뮬이 안 막히면 늘린다 · 안쪽 길이 어긋나면 전체를 조금씩 · 10번 되풀이 · 결과는 대수가 아니라 「설계값 배율」(tools/sim/sim-cal.py 가 구역 자료 cal 칸에) */
  /* 그림자 판(2026-11-03 · datamap 세션이 정한 잣대 · tools/sim/twin-shadow.py RUNNER 와 같은 셈) — 디지털 트윈이 「지금 모습에서 출발해 30분 뒤」를 맞히는지
     cases = [{ d 날짜, t0 자정부터 초, v { ITS 링크: 그 시각 실측 km/h }, w { ITS 링크: 30분 뒤 실측 km/h } }] (sim-cal.py 가 07_API키/out/livespd 를 되감아 넘긴다 · 폰에서는 실측이 없어 못 셈)
     그 시각 실측으로 길을 채우고(Greenshields 채움 1 − 속도 ÷ 자유 속도 · 자유 속도 = 그 길 평소 속도 가운데 가장 빠른 값 · 없으면 50 · 한 변 전체 · 설계값) 빼기까지(init.trim)
     30분 뒤 ±5분 평균 점유 0.8 이상 = 막힘 ↔ 실측 6km/h 이하 · 돌려줌 = 트윈(sim)·그대로(keep · 지금 상태가 이어짐)·섞음(mix · 지금 실측 상태에서 시뮬이 「바뀐다」 할 때만 바꿈) 칸 수
     sel2 = (실측 막힘 칸 맞힘 몫 + 실측 안 막힘 칸 맞힘 몫) ÷ 2 · 「지금과 30분 뒤가 다른 칸」(cn/ch)은 기록만 */
  function shadowScore(M, cases, extra) {
    var H = 1800, ITS = Object.keys(M.links).filter(function (k) { var l = M.links[k]; return l.its && !l.sink; }), O = {};
    ['sim', 'keep', 'mix'].forEach(function (k) { O[k] = { n: 0, hit: 0, jn: 0, jh: 0, fn: 0, fh: 0, cn: 0, ch: 0 }; });
    function tal(o, sj, rj, chg) { o.n++; if (sj === rj) o.hit++; if (rj) { o.jn++; if (sj) o.jh++; } else { o.fn++; if (!sj) o.fh++; } if (chg) { o.cn++; if (sj === rj) o.ch++; } }
    function vf(l) { var a = l.nsp ? Object.keys(l.nsp).map(function (k) { return l.nsp[k]; }) : []; return a.length ? Math.max.apply(null, a) : 50; }
    function occ(S9, k, a, b) { var n = 0, c = 0; S9.samp.forEach(function (x) { if (x.t >= a && x.t <= b) { n += x.occ[k] || 0; c++; } }); return c ? n / c / S9.L[k].cap : null; }
    (cases || []).forEach(function (cs) {
      var fill = {}; ITS.forEach(function (k) { var v = cs.v[M.links[k].its]; if (v == null) return; var f = Math.max(0, Math.min(1, 1 - v / vf(M.links[k]))); side(M, k).forEach(function (k2) { fill[k2] = Math.max(fill[k2] || 0, f); }); });
      var S9 = run(M, Object.assign({ date: cs.d, seed: 5, from: 16 * 3600, to: cs.t0 + H + 300, init: { at: cs.t0, fill: fill } }, extra || {}));
      ITS.forEach(function (k) { var il = M.links[k].its, v0 = cs.v[il], v1 = (cs.w || {})[il]; if (v0 == null || v1 == null) return; var ot = occ(S9, k, cs.t0 + H - 300, cs.t0 + H + 300), ob = occ(S9, k, cs.t0 + 60, cs.t0 + 360); if (ot == null) return;
        var rj = v1 <= 6, j0 = v0 <= 6, sj = ot >= 0.8, mx = ob == null || (ob >= 0.8) === sj ? j0 : sj;
        tal(O.sim, sj, rj, rj !== j0); tal(O.keep, j0, rj, rj !== j0); tal(O.mix, mx, rj, rj !== j0); });
    });
    Object.keys(O).forEach(function (k) { var o = O[k]; o.sel2 = o.jn ? (o.jh / o.jn + o.fh / Math.max(1, o.fn)) / 2 : o.fh / Math.max(1, o.fn); });
    O.cases = (cases || []).length; return O;
  }
  var DKC = [3, 0, 0, 0, 0, 1, 2];
  function calibrate(M, opt) {
    opt = opt || {}; var date = opt.date || '2026-10-21', dk = DKC[dowOf(date)], H0 = opt.h0 || 16, H1 = opt.h1 || 21, sc = {}, all = 1, hist = [], BEST = null, BEST0 = null, stp = 1, prevSel = -1, NIT = opt.iter || 16;
    /* stp = 고치는 폭 — 고른 값이 나빠지면 폭을 반으로(막힘이 문턱에서 한꺼번에 생겨 판이 오락가락하던 것 · 2026-10-30) */
    Object.keys(M.entry).forEach(function (e) { sc[e] = opt.start && opt.start.scale && opt.start.scale[e] != null ? opt.start.scale[e] : 1; }); if (opt.start && opt.start.all) all = opt.start.all;   /* opt.start = 지난 맞춤에서 출발(sim-cal.py 가 처음부터 맞춘 판과 견줘 실측 칸이 더 맞는 쪽을 남긴다) */
    /* 평소 속도가 없는 들어오는 길은 같은 길 맞은편으로 곧장 이어 나가는 망 안 길의 평소 속도를 빌려 맞춤에만 쓴다(실측 칸 수 mn·jn 에는 안 넣음) — 「막히지 않는다」로만 보면 실제로 막히는 큰길(언주로 북쪽 → 르네상스)의 수요까지 깎였다 · 2026-10-30 */
    var OPPL = { nt: 'st', st: 'nt', et: 'wt', wt: 'et' }, PRX = {};
    Object.keys(M.nodes).forEach(function (id) { var n = M.nodes[id]; Object.keys(n.legs || {}).forEach(function (lg) { var I = n.legs[lg].in, o = n.legs[OPPL[lg]]; if (I && M.entry[I] && !M.links[I].nsp && o && o.out && M.links[o.out] && M.links[o.out].nsp) PRX[I] = M.links[o.out].nsp; }); });
    function score(S) { var r = { hit: 0, n: 0, mh: 0, mn: 0, jh: 0, jn: 0, fp: {}, fn: {}, inner: 0 };
      Object.keys(M.links).forEach(function (k) { var l = M.links[k], E = M.entry[k]; if ((!l.nsp && !E) || l.sink) return; for (var h = H0; h <= H1; h++) { var v = l.nsp ? l.nsp[dk + '-' + h] : null; if (v == null && !E) continue;
        var L = S.samp.filter(function (s9) { return s9.t >= h * 3600 && s9.t < (h + 1) * 3600; }), o = L.length ? L.reduce(function (a, s9) { return a + (s9.occ[k] || 0); }, 0) / L.length / S.L[k].cap : 0,
          bq = E && L.length ? L.reduce(function (a, s9) { return a + ((s9.bk || {})[k] || 0); }, 0) / L.length : 0, sj = o >= 0.8 || bq > 15, pv = v == null && PRX[k] ? PRX[k][dk + '-' + h] : null, rj = v != null ? v <= 6 : pv != null && pv <= 6;
        /* 들어오는 길은 망 밖에서 못 들어온 차(bk)도 막힘으로 센다 — 평소 속도가 없는 들어오는 길은 「막히지 않는다」로 본다(조사 자료가 없을 때 차로당 대수 설계값이 길이 받아낼 수 있는 것보다 많아 그물 전체가 엉키던 것 · 2026-10-25) */
        if (v != null) { r.mn++; if (sj === rj) r.mh++; if (rj) { r.jn++; if (sj) r.jh++; } }   /* 실측이 있는 칸만 · 실측 막힘 칸 가운데 시뮬도 막힘 */
        r.n++; if (sj === rj) r.hit++; else if (sj) r.fp[k] = (r.fp[k] || 0) + 1; else r.fn[k] = (r.fn[k] || 0) + 1; } }); return r; }
    for (var it = 0; it <= NIT; it++) {
      var S = run(M, { date: date, seed: 5, from: H0 * 3600, to: (H1 + 1) * 3600, bg: sc, bgAll: all, noCal: 1, noOut: opt.noOut }), r = score(S); hist.push({ it: it, hit: r.hit, n: r.n, mh: r.mh, mn: r.mn, jh: r.jh, jn: r.jn, all: Math.round(all * 100) / 100 });
      r.bal = r.jn ? (r.jh / r.jn + (r.hit - r.jh) / Math.max(1, r.n - r.jn)) / 2 : r.hit / Math.max(1, r.n);   /* 막힘 칸 맞힘과 안 막힘 칸 맞힘의 평균 — 안 막힘 칸이 훨씬 많아 그냥 맞힌 수로 고르면 「아무 데도 안 막힘」 판이 뽑힌다 */
      r.sel = (r.bal + r.hit / Math.max(1, r.n)) / 2;   /* 고르는 값 = 그 평균과 맞힌 몫의 평균(한쪽 끝 — 다 막힘·다 안 막힘 — 으로 쏠리지 않게) */
      if (!BEST0 || r.sel > BEST0.sel) BEST0 = { sel: r.sel, tgt: r.sel, bal: r.bal, hit: r.hit, n: r.n, mh: r.mh, mn: r.mn, jh: r.jh, jn: r.jn, it: it, all: all, sc: JSON.parse(JSON.stringify(sc)) };
      /* 그림자 판(opt.shadow · 2026-11-03 datamap 세션 잣대) — 고르는 값 = (평소 속도 sel + 그림자 sel2) ÷ 2 · 평소 속도 맞음(mh/mn)이 opt.mhFloor 아래면 그 판은 안 고름 */
      var sh = opt.shadow && opt.shadow.length ? shadowScore(M, opt.shadow, { bg: sc, bgAll: all, noCal: 1, noOut: opt.noOut }) : null; r.tgt = sh ? (r.sel + sh.sim.sel2) / 2 : r.sel; if (sh) { hist[hist.length - 1].sel2 = Math.round(sh.sim.sel2 * 1000) / 1000; }
      var okMh = opt.mhFloor == null || !r.mn || r.mh / r.mn >= opt.mhFloor;
      if (okMh && (!BEST || r.tgt > BEST.tgt)) BEST = { sel: r.sel, tgt: r.tgt, sh: sh, bal: r.bal, hit: r.hit, n: r.n, mh: r.mh, mn: r.mn, jh: r.jh, jn: r.jn, it: it, all: all, sc: JSON.parse(JSON.stringify(sc)) };   /* 가장 잘 맞은 판을 남긴다(마지막 판이 더 나쁠 수 있다) */
      if (it === NIT) break;
      if (r.sel < prevSel) stp /= 2; prevSel = r.sel; var dn = 1 - 0.25 * stp, up = 1 + 0.15 * stp, ad = 1 - 0.1 * stp, au = 1 + 0.05 * stp;
      var innerFp = 0, innerFn = 0;
      Object.keys(r.fp).forEach(function (k) { if (M.entry[k]) sc[k] *= dn; else innerFp++; });
      Object.keys(r.fn).forEach(function (k) { if (r.fn[k] < 2) return; if (M.entry[k]) sc[k] = Math.min(sc[k] * up, 3); else innerFn++; });
      if (innerFp > innerFn) all *= ad; else if (innerFn > innerFp) all = Math.min(all * au, 2);
    }
    if (!BEST) BEST = BEST0;   /* 하한을 넘는 판이 없으면 평소 속도로 가장 잘 맞은 판 */
    sc = BEST.sc; all = BEST.all; Object.keys(sc).forEach(function (e) { sc[e] = Math.round(sc[e] * 100) / 100; });
    return { date: date, dk: dk, best: { hit: BEST.hit, n: BEST.n, mh: BEST.mh, mn: BEST.mn, jh: BEST.jh, jn: BEST.jn, it: BEST.it, sel: Math.round(BEST.sel * 1000) / 1000, tgt: Math.round(BEST.tgt * 1000) / 1000, shadow: BEST.sh || null }, scale: sc, all: Math.round(all * 100) / 100, hist: hist, src: '평소 속도(ITS 가운데값 · spd-normal-six · 요일 갈래 ' + dk + ' · ' + H0 + '~' + H1 + '시)로 맞춘 설계값 배율 — 대수 자료가 아니다' };
  }
  function load(area, v) { return fetch('data/sim-' + (area || 'banpo') + '.json' + (v ? '?v=' + v : '')).then(function (r) { return r.json(); }); }
  /* 도로 위 일 계수(2026-11-03) — f = 그 길에서 빠지는 힘의 몫 · cf = 설 자리의 몫 · shut = 닫힘
     사고: HCM 7판 사고 구간 용량 조정계수(남은 차로에 곱함 · 고속도로 값을 빌림 · TxDOT Roadway Design Manual 15.4.4.3 표 15-7 = FHWA-HOP-13-042 부록 C 표 41)
     공사·불법 주정차: 막힌 차로만큼만(공사 구간 감속·합류 손실은 자료 미확인이라 안 넣음 · 설계값) · 버스 정차: HCM 2000 버스 막힘 식 (N − 14.4·NB/3600)/N, 0.05 아래로 안 내림(2차 출처로 확인 · 원문 미대조)
     한 차로 길의 주정차 = 마주 오는 차를 피해 비켜 가는 것으로 0.5(설계값) */
  var EV_CAF = { 2: [0.81, 0.70], 3: [0.83, 0.74, 0.51], 4: [0.85, 0.77, 0.50, 0.52], 5: [0.87, 0.81, 0.67, 0.50, 0.50], 6: [0.89, 0.85, 0.75, 0.52, 0.52], 7: [0.91, 0.88, 0.80, 0.63, 0.63], 8: [0.93, 0.89, 0.84, 0.66, 0.66] };   /* [갓길만, 1차로, 2차로, 3차로, 4차로 막힘] */
  function evFactor(e, N, len) {
    N = Math.max(1, N || 1); len = len || 100; var k = Math.max(0, Math.min(N, e.k || 0)), part = function (m) { return Math.min(1, m / len); };
    if (e.kind === 'ctrl') return { f: 1, cf: 0, shut: true, src: '통제 — 길을 닫음(그 앞 교차로에서 다른 길로 돌림 · 이미 들어간 차는 빠져나간다)' };
    if ((e.kind === 'acc' || e.kind === 'work') && k >= N) return { f: 0, cf: 0, shut: true, src: '모든 차로 막힘 — 길을 닫음(이미 들어간 차는 갇힌다)' };
    if (e.kind === 'acc') { var row = EV_CAF[Math.min(8, Math.max(2, N))], c = row[Math.min(k, row.length - 1)]; return { f: (N - k) / N * c, cf: 1 - k / N * part(40), shut: false, src: 'HCM 7판 사고 구간 용량 조정계수 ' + c + (N < 2 ? '(2차로 줄 값을 빌림)' : '') + ' × 남은 차로 ' + (N - k) + '/' + N }; }
    if (e.kind === 'work') return { f: (N - k) / N, cf: 1 - k / N * part(e.len || 150), shut: false, src: '막힌 차로만큼 ' + (N - k) + '/' + N + '(설계값 — 공사 구간 감속·합류 손실은 안 넣음)' };
    if (e.kind === 'bus') { var nb = e.nb || 0, fb = Math.max(0.05, (N - 14.4 * nb / 3600) / N); return { f: fb, cf: 1, shut: false, src: 'HCM 2000 버스 막힘 식 (N − 14.4×' + nb + '/3600)/N = ' + fb.toFixed(2) + '(정류장이 정지선 75m 안일 때의 식)' }; }
    if (e.kind === 'park') { var pf = N > 1 ? (N - 1) / N : 0.5; return { f: pf, cf: 1 - 1 / N * part((e.cars || 1) * 7), shut: false, src: N > 1 ? '바깥 차로 하나가 막힘 ' + (N - 1) + '/' + N + '(설계값)' : '한 차로 길 — 비켜 가는 것으로 0.5(설계값)' }; }
    return { f: 1, cf: 1, shut: false, src: '' };
  }
  window.tgSim = { shadowScore: shadowScore, evFactor: evFactor, load: load, create: create, run: run, calibrate: calibrate, side: side, sideOcc: sideOcc, planAt: planAt, phasesToWin: phasesToWin, winToPhases: winToPhases, dowOf: dowOf };
})();
