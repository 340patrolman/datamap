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
  /* 녹색 창 → 현시(수동 조작용) — 녹색이 새로 켜지는 때마다 한 현시 */
  function winToPhases(w, c, Y, AR) {
    var S = []; w.forEach(function (r) { if (S.indexOf(r[3]) < 0) S.push(r[3]); }); S.sort(function (a, b) { return a - b; });
    return S.map(function (s, i) { var e = S[i + 1] != null ? S[i + 1] : c; return { d: e - s, y: (Y && Y[i]) || 3, ar: (AR && AR[i]) || 1, mv: w.filter(function (r) { return s >= r[3] && s < r[3] + r[1]; }).map(function (r) { return r[0]; }) }; });
  }
  /* 그 시각(자정부터 초)의 신호 계획 { c 주기, off 옵셋, win 녹색 창, pat 패턴 번호, src, ph 현시 }
     현시도(tod·pat·dir) · T-Data 기록(recs — 요일 갈래·시각마다 한 기록 · 맞는 갈래가 없으면 가장 가까운 시각) · 재편안(alt — 현시 목록) */
  function planAt(M, id, t, dow, alt) {
    var n = M.nodes[id], P = alt && alt[id];
    if (P) { var w0 = phasesToWin(P.ph); return { c: w0.c, off: P.off || 0, win: w0.win, src: '재편안', ph: P.ph }; }
    var p = n.plan;
    if (p.recs) {
      var best = null, bs = 1e9;
      p.recs.forEach(function (r) { var dsc = r.dk.indexOf(dow) >= 0 ? 0 : 1e6, h = Math.abs(r.t - t); if (dsc + h < bs) { bs = dsc + h; best = r; } });
      return { c: best.cyc, off: best.off || 0, win: best.win, src: p.src, day: best.day, ph: winToPhases(best.win, best.cyc) };
    }
    if (p.win) return { c: p.cyc, off: 0, win: p.win, src: p.src, ph: winToPhases(p.win, p.cyc) };
    var L = p.tod[String(TODK[dow])], cur = L[L.length - 1];
    L.forEach(function (r) { if (hm(r[0]) <= t) cur = r; });
    var pt = String(cur[2]), pa = p.pat[pt];
    return { c: pa.c, off: pa.off, win: p.dir[pt], pat: pt, src: p.src, ph: p.ph.map(function (mv, i) { return { d: pa.a[i], y: p.Y[i], ar: p.AR[i], mv: mv }; }) };
  }
  function allWin(p) { return p.recs ? [].concat.apply([], p.recs.map(function (r) { return r.win; })) : p.win || [].concat.apply([], Object.keys(p.dir).map(function (k) { return p.dir[k]; })); }

  function create(M, scen, alt) {
    scen = scen || {}; var DS = M.design, dow = dowOf(scen.date || M.date0 || '2026-10-18'), VK = VOLK[dow];
    var JAM = 0.8, sp = M.spacing.v, satS = M.sat.v / 3600, vf = (scen.freeV || DS.freeV.v) / 3.6, lost = DS.lostStart.v, rtRed = scen.rtRed != null ? scen.rtRed : DS.rtRed.v;
    var boxP = scen.box != null ? scen.box : DS.box.v, R = rng(scen.seed || 7), RB = rng((scen.seed || 7) + 101);
    var FROM = scen.from != null ? scen.from : 16 * 3600, WARM = scen.warm != null ? scen.warm : 7200;   // 몸풀기 2시간 — 빈 길에서 시작하면 16시에 이미 쌓여 있던 차가 없다
    // 조치(라바콘·입차 중단 …) 모으기
    var ACT = { closeEntry: {}, mvp: {}, attOff: {}, attInStop: {}, attOutFirst: {} };
    (scen.act || []).forEach(function (aid) { var a = (M.actions || []).filter(function (x) { return x.id === aid; })[0]; if (!a) return;
      (a.closeEntry || []).forEach(function (e) { ACT.closeEntry[e] = 1; }); Object.keys(a.mvp || {}).forEach(function (k) { ACT.mvp[k] = a.mvp[k]; });
      ['attOff', 'attInStop', 'attOutFirst'].forEach(function (f) { (a[f] || []).forEach(function (x) { ACT[f][x] = 1; }); }); });
    var S = { M: M, from: FROM, t: FROM - WARM, end: scen.to != null ? scen.to : 22 * 3600, L: {}, mv: {}, N: {}, V: [], done: 0, delay: 0, boxN: 0, back: {}, samp: [], log: [], rtBlk: {}, A: {} };
    Object.keys(M.links).forEach(function (k) { var l = M.links[k]; S.L[k] = { id: k, l: l, n: 0, cap: l.sink ? 1e9 : Math.max(2, l.len * l.lanes / sp), tt: l.sink ? 0 : l.len / vf }; });
    function addMv(node, key, fr, to, la, kind, cap, p) { var id = fr + '>' + to; S.mv[id] = { id: id, node: node, key: key, fr: fr, to: to, la: la, kind: kind, cap: cap, p: p == null ? 1 : p, q: [], acc: 0, served: 0, gs: 0 }; return S.mv[id]; }
    // 신호 교차로 이동류 — 다리(legs)와 현시에서
    Object.keys(M.nodes).forEach(function (id) {
      var n = M.nodes[id]; S.N[id] = { id: id, n: n, box: [], manual: null };
      if (n.ty !== 'sig') return;
      var any = {}; allWin(n.plan).forEach(function (r) { any[r[0]] = 1; }); (n.free || []).forEach(function (k) { any[k] = 1; });
      Object.keys(n.legs).forEach(function (lg) {
        var I = n.legs[lg].in; if (!I || !TURN[lg]) return; var ln = M.links[I].lanes;
        ['St', 'Lt', 'Rt'].forEach(function (tu) {
          var key = lg + '.' + tu, O = n.legs[TURN[lg][tu]] && n.legs[TURN[lg][tu]].out;
          if (!O || (tu !== 'Rt' && !any[key]) || (n.ban || []).indexOf(key) >= 0) return;
          var hasL = any[lg + '.Lt'] ? 1 : 0, la = tu === 'St' ? Math.max(1, ln - hasL - 0.5) : tu === 'Lt' ? (ln >= 2 ? 1 : 0.5) : 0.5;   // 차로 나눔(설계값): 좌회전 1 · 우회전은 바깥 차로를 직진과 나눠 반 · 나머지 직진
          addMv(id, key, I, O, la, (n.free || []).indexOf(key) >= 0 ? 'free' : tu === 'Rt' ? 'rt' : 'sig');
        });
      });
    });
    // 신호 없는 갈림·합류(mvx · 자료가 준다)
    (M.mvx || []).forEach(function (x) { var m = addMv(x.node, x.key, x.fr, x.to, x.la, x.kind || 'free', x.cap, x.p); if (ACT.mvp[m.id] != null) m.p = ACT.mvp[m.id]; });
    // 끌어들이는 곳(att) — 들어가는 문(이동류 kind cap)과 나오는 길
    (M.att || []).forEach(function (a0) {
      var a = Object.assign({}, a0, (scen.att || {})[a0.id] || {}); a.off = ACT.attOff[a.id] || (scen.att && scen.att[a.id] && scen.att[a.id].off); a.inStop = ACT.attInStop[a.id]; a.outFirst = ACT.attOutFirst[a.id];
      S.L['att:' + a.id] = { id: 'att:' + a.id, l: { nm: a.nm, att: a.id }, n: 0, cap: 1e9, tt: 0, sinkA: 1 };
      a.mv = addMv(a.node, 'att', a.inFrom9, 'att:' + a.id, 1, 'cap', a.inStop ? 0 : a.inCap);
      S.A[a.id] = { a: a, held: 0, out: [], acc: 0 };
    });
    // 길 찾기(차를 만들 때 한 번) — 들어온 길에서 이동류를 차례로 고른다
    var outOf = {}; Object.keys(S.mv).forEach(function (k) { var m = S.mv[k]; (outOf[m.fr] = outOf[m.fr] || []).push(m); });
    var TS = { Lt: (scen.turn || DS.turn).Lt, Rt: (scen.turn || DS.turn).Rt };
    function isAtt(m) { return m.to.slice(0, 4) === 'att:'; }
    function wander(start, r) {
      var p = [start], cur = start, sig = 0;
      for (var g = 0; g < 14; g++) {
        var L = M.links[cur]; if (!L || L.sink) return p;
        var O = (outOf[cur] || []).filter(function (m) { return !isAtt(m) && m.p > 0; });
        if (!O.length) return p;
        var nx;
        if (M.nodes[L.to].ty === 'sig') {
          sig++;
          var sinks = O.filter(function (m) { return M.links[m.to].sink; });
          if (sig >= 3 && sinks.length) nx = sinks[Math.floor(r() * sinks.length)];
          else { var x = r(), tu = x < TS.Lt ? 'Lt' : x < TS.Lt + TS.Rt ? 'Rt' : 'St'; nx = O.filter(function (m) { return m.key.split('.')[1] === tu; })[0] || O.filter(function (m) { return m.key.split('.')[1] === 'St'; })[0] || O[0]; }
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
      var E = M.entry[e], h = Math.min(23, Math.floor(t / 3600)), sc = (scen.bg && scen.bg[e] != null ? scen.bg[e] : 1) * (scen.bgAll || 1);
      if (ACT.closeEntry[e]) return 0;
      if (E.spot) { var v = M.vol[E.spot][VK][h]; return (v[0] + v[1]) / 2 * (scen.share && scen.share[e] != null ? scen.share[e] : E.share) * sc; }
      return (E.perLane * M.links[e].lanes) * sc;
    }
    function win(t, a, b, pk) { var h = t / 3600; return h >= a && h < b ? pk : 0; }
    var dem = [];
    Object.keys(M.entry).forEach(function (e) { dem.push({ k: 'bg', e: e, f: function (t) { return bgRate(e, t); }, acc: 0 }); });
    Object.keys(S.A).forEach(function (id) {
      var a = S.A[id].a; if (a.off) return;
      if (!a.inStop) Object.keys(a.from).forEach(function (e) { dem.push({ k: 'ai', e: e, att: id, f: function (t) { return win(t, a.inT0, a.inT1, a.inPeak) * a.from[e]; }, acc: 0 }); });
      if (a.mode === 'store') dem.push({ k: 'ao', e: null, att: id, f: function (t) { return win(t, a.outT0, a.outT1, a.outPeak); }, acc: 0 });
    });
    var RT = {}; function cached(a, b) { var k = a + '|' + b; return RT[k] || (RT[k] = route(a, b)); }
    function makeV(k, e, t, att) {
      var p, a = att && S.A[att].a;
      if (k === 'bg') p = wander(e, R);
      else if (k === 'ai') { p = cached(e, a.inFrom9); p = p ? p.concat(['att:' + att]) : wander(e, R); }
      else if (k === 'ao') p = ['att:' + att, a.outLink].concat(wander(a.outLink, R).slice(1));
      var v = { k: k, att: att, p: p, i: 0, t0: t, ff: 0, rd: 0 }; S.V.push(v); return v;
    }
    function enter(v, lk, t) {   // 길에 올림
      var L = S.L[lk]; v.i = v.p.indexOf(lk, v.i); L.n++; v.ff += L.tt; v.rd = t + L.tt;
      if (L.sinkA) { L.n--; if (S.A[L.l.att].a.mode === 'hold') S.A[L.l.att].held++; finish(v, t); return; }
      if (L.l.sink || v.i >= v.p.length - 1) { L.n--; finish(v, t); return; }
      var m = S.mv[lk + '>' + v.p[v.i + 1]]; if (!m) { L.n--; finish(v, t); return; }
      S.inn[lk] = (S.inn[lk] || 0) + 1;
      m.q.push(v);
    }
    function finish(v, t) { S.done++; v.te = t; if (v.t0 >= FROM) S.delay += Math.max(0, t - v.t0 - v.ff); }
    function room(lk) { var L = S.L[lk]; return L.l && L.l.sink || L.sinkA || L.n < L.cap; }
    // 신호
    function greenSet(id, t) {
      var N = S.N[id], G = {};
      if (N.manual) { var ma = N.manual; (ma.clr > 0 ? ma.keep : ma.ph[ma.i].mv).forEach(function (m) { G[m] = 1; }); return G; }
      var P = planAt(M, id, t, dow, alt), c = P.c, x = ((t - P.off) % c + c) % c;
      P.win.forEach(function (r) { var a = (x - r[3] + c) % c; if (a >= lost && a < r[1] + r[2] - 1) G[r[0]] = 1; });
      N.cur = P; return G;
    }
    S.inn = {};
    S.step = function () {
      var t = S.t; S.inn = {};
      Object.keys(S.N).forEach(function (id) { var ma = S.N[id].manual; if (ma && ma.clr > 0) { ma.clr--; if (!ma.clr) { ma.i = ma.next; ma.keep = []; } } });
      // 1 차 만들기 → 들어오는 길(자리가 없으면 망 밖에서 기다림)
      dem.forEach(function (d) {
        d.acc += d.f(t) / 3600;
        while (d.acc >= 1) { d.acc -= 1; if (d.k === 'ao') { S.A[d.att].out.push(makeV('ao', null, t, d.att)); continue; } (S.back[d.e] = S.back[d.e] || []).push(makeV(d.k, d.e, t, d.att)); }
      });
      Object.keys(S.A).forEach(function (id) {   // 머무는 곳(공원 등): 나가는 때가 되면 들어온 차만큼 내보냄
        var X = S.A[id], a = X.a, h = t / 3600; if (a.mode !== 'hold' || !X.held || a.off || h < a.outT0 || h >= a.outT1 + 1) return;
        X.acc += a.outRate / 3600; while (X.acc >= 1 && X.held > 0) { X.acc--; X.held--; var v = makeV('bg', a.outLink, t); (S.back[a.outLink] = S.back[a.outLink] || []).push(v); }
      });
      Object.keys(S.back).forEach(function (e) { var B = S.back[e]; while (B.length && room(e)) enter(B.shift(), e, t); });
      // 2 신호 교차로 — 녹색 이동류에서 빠짐
      var GS = {}; Object.keys(S.N).forEach(function (id) { if (M.nodes[id].ty === 'sig') GS[id] = greenSet(id, t); });
      // 꼬리물기로 교차로 안에 선 차 — 하류에 자리가 나면 먼저 빠진다
      Object.keys(S.N).forEach(function (id) { var N = S.N[id]; N.box = N.box.filter(function (b) { if (room(b.to)) { S.L[b.fr].n--; enter(b.v, b.to, t); return false; } return true; }); });
      // 끌어들이는 곳에서 나오는 차 — 나오는 길(합류)에 자리와 틈이 있을 때 · 출차 우선이면 본선보다 먼저
      function attExit(X, lim) { var k = 0, a = X.a; while (X.out.length && k < lim && room(a.outLink)) { var v = X.out.shift(); v.i = 1; enter(v, a.outLink, t); k++; } return k; }
      Object.keys(S.A).forEach(function (id) { var X = S.A[id]; if (X.a.mode !== 'store') return; X.mAcc = Math.min((X.mAcc || 0) + M.links[X.a.outLink].lanes * satS, 2 * M.links[X.a.outLink].lanes * satS + 1); if (X.a.outFirst) X.mAcc -= attExit(X, Math.floor(X.mAcc)); });
      Object.keys(S.mv).forEach(function (k) {
        var m = S.mv[k], q = m.q, on;
        if (m.kind === 'sig') on = GS[m.node] && GS[m.node][m.key]; else on = true;
        var box = S.N[m.node].box; if (box.length && box.some(function (b) { return b.to !== m.to; })) on = false;
        var la = m.la - (m.key.slice(-2) === 'St' && S.rtBlk[m.fr] >= t - 1 ? 0.5 : 0);   // 우회전 차가 막혀 서 있으면 나눠 쓰는 바깥 차로가 직진에도 막힌다
        var rate = m.kind === 'cap' ? m.cap / 3600 : la * satS * (m.kind === 'rt' && !(GS[m.node] && GS[m.node][m.key]) ? rtRed : 1);
        if (!on || !q.length) { m.acc = 0; return; }
        m.gs++; m.acc = Math.min(m.acc + rate, Math.max(1, rate * 2));
        while (m.acc >= 1 && q.length && q[0].rd <= t) {
          var v = q[0];
          if (!room(m.to)) {
            if (m.kind === 'rt') S.rtBlk[m.fr] = t;
            if (M.nodes[m.node].ty === 'sig' && box.length < 2 && RB() < boxP) { q.shift(); m.acc -= 1; box.push({ v: v, fr: m.fr, to: m.to }); S.boxN++; }
            break;
          }
          q.shift(); m.acc -= 1; S.L[m.fr].n--; m.served++;
          enter(v, m.to, t);
        }
      });
      Object.keys(S.A).forEach(function (id) { var X = S.A[id]; if (X.a.mode !== 'store' || X.a.outFirst) return; X.mAcc -= S.inn[X.a.outLink] ? S.inn[X.a.outLink] : 0; if (X.mAcc >= 1) X.mAcc -= attExit(X, Math.floor(X.mAcc)); if (X.mAcc < 0) X.mAcc = 0; });
      if (t % 60 === 0 && t >= FROM) S.samp.push(sample());
      S.t++;
    };
    function sample() {
      var ap = {}, tot = 0;
      Object.keys(S.mv).forEach(function (k) { var m = S.mv[k]; if (M.nodes[m.node].ty !== 'sig') return; var a = m.node + '.' + m.key.split('.')[0]; ap[a] = (ap[a] || 0) + m.q.length; tot += m.q.length; });
      var back = 0; Object.keys(S.back).forEach(function (e) { back += S.back[e].length; });
      var occ = {}; Object.keys(S.L).forEach(function (k) { var L = S.L[k]; if (!L.l.sink && !L.sinkA) occ[k] = Math.round(L.n); });
      var jam = []; Object.keys(S.N).forEach(function (id) { var n = M.nodes[id]; if (n.ty !== 'sig') return; Object.keys(n.legs).forEach(function (lg) { var I = n.legs[lg].in; if (I && S.L[I].n >= JAM * S.L[I].cap) jam.push(id + '.' + lg); }); });
      var att = {}; Object.keys(S.A).forEach(function (id) { var X = S.A[id]; att[id] = { door: X.a.mv.q.length, out: X.out.length, held: X.held }; });
      return { t: S.t, jam: jam, ap: ap, q: tot, back: back, att: att, box: S.boxN, occ: occ };
    }
    // 수동 조작(넘기기 · 현시 지정) — 지금 계획의 현시를 이어받는다 · 실제 신호를 바꾸는 기능이 아니다
    S.manual = function (id, on) { var N = S.N[id]; if (!on) { N.manual = null; return; } var P = planAt(M, id, S.t, dow, alt); var G = greenSet(id, S.t), best = 0, sc = -1; P.ph.forEach(function (p, i) { var s = p.mv.filter(function (m) { return G[m]; }).length; if (s > sc) { sc = s; best = i; } }); N.manual = { ph: P.ph, i: best, clr: 0, keep: [] }; };
    S.go = function (id, k) { var ma = S.N[id].manual; if (!ma) return; var j = k == null ? (ma.i + 1) % ma.ph.length : k; if (j === ma.i) return; var nx = ma.ph[j].mv, cu = ma.ph[ma.i]; ma.keep = cu.mv.filter(function (m) { return nx.indexOf(m) >= 0; }); ma.clr = cu.y + cu.ar; ma.next = j; };
    S.runTo = function (t1) { while (S.t < Math.min(t1, S.end)) S.step(); return S; };
    S.result = function () {
      // 막힘 = 신호 교차로 접근로 가운데 점유 80% 넘는 곳이 3곳 이상(실측 ≤5km/h 와 맞대 보는 기준과 같다) · 해소 = 그 뒤 마지막으로 3곳 아래로 내려간 때
      var peak = 0, pkT = null, clr = null, st = null, A = S.samp, attW = function (s) { var w = 0; Object.keys(s.att).forEach(function (k) { w += s.att[k].out + s.att[k].door; }); return w; };
      A.forEach(function (s) { var v = s.q + s.back + attW(s); if (v > peak) { peak = v; pkT = s.t; } if (st == null && s.jam.length >= 3) st = s.t; });
      if (st != null) { for (var i = A.length - 1; i >= 0; i--) { if (A[i].jam.length >= 3) { clr = A[i + 1] ? A[i + 1].t : null; break; } } }
      var inNet = S.V.filter(function (v) { return v.te == null && v.t0 >= FROM; }), dl = S.delay + inNet.reduce(function (a, v) { return a + Math.max(0, S.t - v.t0 - v.ff); }, 0);
      var maxQ = {}; A.forEach(function (s) { Object.keys(s.ap).forEach(function (a) { var nd = a.split('.')[0], lg = a.split('.')[1], I = M.nodes[nd].legs[lg].in, m = s.ap[a] * M.spacing.v / M.links[I].lanes; if (!maxQ[a] || m > maxQ[a]) maxQ[a] = Math.round(m); }); });
      return { delayVh: Math.round(dl / 3600), maxQm: maxQ, trappedMax: Math.max.apply(null, A.map(attW).concat([0])), jamStart: st, clearT: clr, jamMax: Math.max.apply(null, A.map(function (s) { return s.jam.length; }).concat([0])), peak: peak, peakT: pkT, box: S.boxN, made: S.V.length, done: S.done };
    };
    S.inNet = function () { var n = 0; Object.keys(S.L).forEach(function (k) { n += S.L[k].n; }); Object.keys(S.A).forEach(function (k) { n += S.A[k].out.length; }); Object.keys(S.back).forEach(function (e) { n += S.back[e].length; }); return n; };
    return S;
  }
  function run(M, scen, alt) { var S = create(M, scen, alt); S.runTo(S.end); return S; }
  function load(area) { return fetch('data/sim-' + (area || 'banpo') + '.json').then(function (r) { return r.json(); }); }
  window.tgSim = { load: load, create: create, run: run, planAt: planAt, phasesToWin: phasesToWin, winToPhases: winToPhases, dowOf: dowOf };
})();
