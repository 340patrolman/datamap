/* 🔀 합류부 시뮬 — IC·합류 지점 사고 원인 찾기(2026-11-02 · 소유자 「ic 나 합류지점 등 사고다발지역 원인을 찾아볼 수 있게도 시뮬레이션 가능하게 · 도로상에 일어나는 일 다 해볼 수 있도록」)
   기존 🧪 시뮬(sim.js)은 「차가 줄을 서는」 대기열 모형이라 끼어들기·차로 바꾸기·추돌 위험을 못 낸다 → 차를 한 대씩 움직이는 합류부 전용 모형을 따로 둔다.
   · 앞차 따라가기 = IDM(Treiber·Hennecke·Helbing 2000) · 차로 바꾸기 = MOBIL(Kesting·Treiber·Helbing 2007) — 계수는 교과서 값을 설계값으로 썼다(아래 P).
   · 합류부 자리·본선 차로·연결로 차로·제한속도 = data/sim-merges.json(tools/sim/merge-bake.py 가 국가표준 노드링크 여섯 구 판에서 구움).
   · 본선 교통량 = 서울시 교통량 조사(같은 길 이름 2.5km 안 · 방향 구분이 자료에 없어 두 방향 평균) · 없으면 설계값 · 가속차로 길이·연결로 교통량·대형차 비율 = 설계값(막대로 바꾼다).
   · 그 자리 실제 사고(TAAS 10년 100m 칸 · 사망사고 한 건씩)는 화면에 나란히 보이기만 한다 — 시뮬 입력에 쓰지 않는다.
   · 현행과 바꾼 안을 같은 씨앗(같은 차들)으로 두 번 돌려 견준다. 개념 시연 — 예측·보증이 아니다. 서버·통신 없음(공개 파일만 읽는다). */
(function () {
  'use strict';
  var P = {   /* 설계값 — IDM·MOBIL 교과서 값(도시고속도로 쪽으로 차두시간만 조금 줄임) */
    car: { len: 4.6, a: 1.5, b: 2.0, T: 1.2, s0: 2.0 },
    truck: { len: 11.0, a: 0.7, b: 1.5, T: 1.6, s0: 3.0 },
    pol: 0.2, dth: 0.25, bsafe: 4.0, bsafeM: 5.0, bforce: 9.0, hard: 4.0, ttc: 1.5, endZ: 30, dt: 0.25, lcEvery: 0.5, react: 0.9,   /* react = 끼어든 차를 알아채기까지(초) — 설계값 */
    x0: -700, xr: -220, warm: 90, dur: 600, frameDt: 0.5
  };
  var MRG = null, RIDX = null, VOL = null, TAAS = {}, PANEL = null, CUR = null, ANIM = null, CARDSEQ = 0;
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function getJ(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }); }
  function dist(a, b) { return Math.hypot((a[1] - b[1]) * 88200, (a[0] - b[0]) * 111000); }   /* [lat, lon] */
  function rng(seed) { var s = seed >>> 0 || 1; return function () { s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0; return s / 4294967296; }; }

  /* ================= 엔진 ================= */
  function idm(v, v0, gap, vl, p) {   /* 앞차 따라가기 가속도 — gap 은 앞차 꽁무니까지(m) · 앞차 없으면 gap = Infinity */
    var sst = p.s0 + Math.max(0, v * p.T + v * (v - vl) / (2 * Math.sqrt(p.a * p.b)));
    var free = 1 - Math.pow(v / Math.max(v0, 0.1), 4);
    if (!(gap < 1e8)) return p.a * free;
    return p.a * (free - Math.pow(sst / Math.max(gap, 0.1), 2));
  }
  /* 🚧 도로 위 일(cfg.ev · 2026-11-03 · 3단계) — { kind 'acc' 사고·'work' 공사·'bus' 버스 정차·'park' 불법 주정차·'ctrl' 통제, lane 첫 막힌 차로(0 = 1차로 · 왼쪽), k 막힌 차로 수, x 합류점부터 m, len 공사 길이 m,
       when 'all' 처음부터 끝까지 · 'mid' 2분 뒤 생겨 5분 뒤 치움 · 'late' 3분 뒤 생겨 끝까지, warn 차로를 비우기 시작하는 거리 m(설계값), gawk 옆 차로 구경 감속 0~1(설계값), vz 공사 구간 속도 km/h, nb 버스 대/시, dwell 정차 초(설계값), cars 주정차 대수,
       fast 막힌 시간 절반, slow 그 앞 300m 감속 km/h } → 차로마다 멈춰 선 「막힘」(o) — 앞차처럼 보이고(가까워져야 본다) · 그 차로 차는 warn 안에서 옆으로 비킨다 */
  function obsOf(c) {
    var e = c.ev; if (!e || !e.kind) return [];
    var n = c.n, k = Math.max(1, Math.min(n, e.k || 1)), l0 = Math.max(0, Math.min(e.lane == null ? n - 1 : e.lane, n - k)), T = { all: [-1e9, 1e9], mid: [120, 420], late: [180, 1e9] }[e.when || 'all'] || [-1e9, 1e9], L = [], lanes = [];
    if (e.fast && T[1] < 1e8) T = [T[0], T[0] + (T[1] - T[0]) / 2];
    if (e.kind === 'bus' || e.kind === 'park') lanes = [n - 1]; else for (var i = 0; i < k; i++) lanes.push(l0 + i);
    var len = e.kind === 'acc' ? 20 : e.kind === 'work' ? (e.len || 200) : e.kind === 'bus' ? 12 : e.kind === 'park' ? (e.cars || 2) * 7 : 5000;
    var warn = e.warn || { acc: 150, work: 400, bus: 60, park: 100, ctrl: 300 }[e.kind];
    lanes.forEach(function (l) { L.push({ kind: e.kind, lane: l, x: e.x || 0, len: len, t0: e.kind === 'bus' || e.kind === 'park' ? -1e9 : T[0], t1: e.kind === 'bus' || e.kind === 'park' ? 1e9 : T[1],
      per: e.kind === 'bus' ? 3600 / Math.max(1, e.nb || 30) : 0, dwell: e.dwell || 20, ph: Math.abs(Math.round(e.x || 0)) % 37, warn: warn, gawk: e.kind === 'acc' ? (e.gawk != null ? e.gawk : 0.2) : 0,
      vz: e.kind === 'work' && e.vz ? e.vz : 0, zs: 150, slow: e.slow || 0 }); });
    return L;
  }
  function obOn(o, t, warm) { if (o.per) return ((t + o.ph) % o.per) < o.dwell; var tm = t - warm; return tm >= o.t0 && tm < o.t1; }
  /* cfg = { n 본선 차로, add 차로 더해짐(가속차로가 끝나지 않는다), La 가속차로 m, S 앞쪽 실선 m, qMain 대/시(본선 전 차로 합), qRamp 대/시, truck 0~1, lim km/h, rampLim km/h,
             W 다음 진출로까지 m(0 = 없음), exitP 본선 차 중 그곳으로 나갈 몫, meter 연결로 최소 간격 초(0 = 없음), courtesy 합류 구간 본선 바깥 차로 비켜 주기 0~1, dur, warm } */
  function run(cfg, seed) {
    var R = rng(seed), n = cfg.n, ACC = n, La = cfg.add ? 1e9 : cfg.La, S = Math.min(cfg.S || 0, cfg.add ? 1e9 : cfg.La - 10), W = cfg.W > 0 ? cfg.W : 0;
    var xE = Math.min(1600, Math.max(cfg.add ? 400 : cfg.La, W, cfg.ev && cfg.ev.kind ? (cfg.ev.x || 0) + Math.min(cfg.ev.kind === 'work' ? (cfg.ev.len || 200) : 40, 500) : 0) + 300), xr = P.xr, dt = P.dt, T = cfg.warm + cfg.dur;
    var V = [], idc = 0, t = 0, pend = [], lastSpawn = [], rampLast = -1e9;
    var M = { forced: 0, endM: 0, merges: 0, dvSum: 0, stall: 0, ttc: 0, hard: 0, near: 0, exits: 0, missed: 0, exitForced: 0, thru: 0, vSum: 0, vN: 0, rampQ: 0, pendMax: 0, spawned: 0, oForced: 0, oStall: 0, ttS: 0, ttN: 0, bins: {}, binsK: {} };
    var OB = obsOf(cfg), OBA = [];   /* 도로 위 일 — 지금 걸린 막힘 */
    var EV = [], FR = [], frT = 0;
    for (var k = 0; k <= n; k++) { pend[k] = 0; lastSpawn[k] = -1e9; }
    var limMs = cfg.lim / 3.6, rampMs = (cfg.rampLim || Math.min(cfg.lim, 60)) / 3.6;
    function meas() { return t >= cfg.warm; }
    function inZ(v) { return meas() && v.x >= P.x0 + 250; }
    function bin(x, kind) { if (!meas()) return; var b = Math.floor(x / 25) * 25; M.bins[b] = (M.bins[b] || 0) + 1; var o = M.binsK[b] = M.binsK[b] || {}; o[kind] = (o[kind] || 0) + 1; }
    function ev(kind, v, extra) { if (!meas() || v.x < P.x0 + 250) return;   /* 차가 생겨나는 입구 250m 는 세지 않는다 */ EV.push([t - cfg.warm, v.x, v.lane, kind, extra || 0]); bin(v.x, kind); }
    function mk(lane, x, ramp) {
      var tr = R() < cfg.truck, p = tr ? P.truck : P.car, f = 0.93 + R() * 0.14;
      var v = { id: ++idc, x: x, lane: lane, lat: lane, tr: tr, p: p, len: p.len, f: f, ramp: ramp, coop: R() < cfg.courtesy, exit: !ramp && W > 0 && R() < cfg.exitP, lcT: R() * P.lcEvery, ttcOn: false, hardT: -9, stallOn: false, merged: false, acc: 0 };
      v.v = Math.min(v0of(v), ramp ? rampMs : limMs * 0.9);
      return v;
    }
    function v0of(v) { var base = (v.lane === ACC && v.x < 0) ? rampMs : limMs; if (v.tr) base = Math.min(base, limMs * 0.88); var b = base * v.f;
      for (var i = 0; i < OBA.length; i++) { var o = OBA[i]; if (v.lane >= n) continue;
        if (o.vz && v.x > o.x - o.zs && v.x < o.x + o.len) b = Math.min(b, o.vz / 3.6 * v.f);   /* 공사 구간 속도 */
        if (o.slow && v.x > o.x - 300 && v.x < o.x) b = Math.min(b, Math.max(20, cfg.lim - o.slow) / 3.6 * v.f);   /* 그 앞 감속 안내 */
        if (o.gawk && v.lane !== o.lane && v.x > o.x - 80 && v.x < o.x + o.len + 40) b = Math.min(b, base * v.f * (1 - o.gawk)); }   /* 옆 차로 구경 감속(설계값) */
      return b; }
    function obAhead(l, x) { var b = null; for (var i = 0; i < OBA.length; i++) { var o = OBA[i]; if (o.lane === l && o.x > x - 0.5 && (!b || o.x < b.x)) b = o; } return b; }
    function obCover(l, x, len) { for (var i = 0; i < OBA.length; i++) { var o = OBA[i]; if (o.lane === l && x > o.x - 1 && x - len < o.x + o.len + 1) return true; } return false; }
    function openLane(cur, ob) {   /* 막힌 곳에서 가장 가까운 열린 차로 쪽(−1 왼쪽 · +1 오른쪽 · 0 없음) */
      var best = 0, bd = 99; for (var l = 0; l < (cfg.add ? n + 1 : n); l++) {   /* 차로가 더해진 합류면 더해진 차로(ACC)로도 비킨다 */ if (l === cur) continue; var o = obAhead(l, ob.x - 5); if (o && o.x < ob.x + ob.len) continue; if (Math.abs(l - cur) < bd) { bd = Math.abs(l - cur); best = l < cur ? -1 : 1; } } return best; }
    function laneOk(l, x) { if (l < 0) return false; if (l < n) return true; if (l === ACC) return x >= xr && x <= La; return false; }
    function spawn() {
      var lanesForTruck = [];
      for (var l = 0; l < n; l++) if (n < 3 || l >= Math.floor(n / 2)) lanesForTruck.push(l);   /* 대형차는 오른쪽 차로들(설계값 — 지정차로 흉내) */
      var pm = cfg.qMain / 3600 * dt;
      for (var l2 = 0; l2 < n; l2++) if (R() < pm / n) pend[l2]++;
      if (R() < cfg.qRamp / 3600 * dt) pend[ACC]++;
      for (var L = 0; L <= n; L++) {
        while (pend[L] > 0) {
          var x0 = L === ACC ? xr : P.x0, last = null;
          for (var i = 0; i < V.length; i++) { var u = V[i]; if (u.lane === L && u.x >= x0 && (!last || u.x < last.x)) last = u; }
          if (L === ACC && cfg.meter > 0 && t - rampLast < cfg.meter) break;
          var nv = mk(L, x0, L === ACC);
          if (nv.tr && L < n && lanesForTruck.indexOf(L) < 0) nv.lane = lanesForTruck[Math.floor(R() * lanesForTruck.length)], nv.lat = nv.lane;
          if (last) { var gap = last.x - last.len - x0; if (gap < nv.p.s0 + 2) break; if (gap < 160) nv.v = Math.min(nv.v, Math.max(0, (gap - nv.p.s0) / nv.p.T), last.v + 3); }   /* 입구에서는 앞차에 맞춘 속도로 들어온다 */
          V.push(nv); pend[L]--; if (meas()) M.spawned++; if (L === ACC) rampLast = t;
        }
        if (meas()) M.pendMax = Math.max(M.pendMax, pend[L]);
      }
    }
    function sortLanes() { var by = []; for (var l = 0; l <= n; l++) by[l] = []; V.forEach(function (v) { by[v.lane].push(v); }); by.forEach(function (a) { a.sort(function (p, q) { return p.x - q.x; }); }); return by; }
    function nbr(by, lane, x, self) {   /* 그 차로에서 x 앞의 차(leader)와 뒤의 차(follower) */
      var a = by[lane] || [], lo = 0, hi = a.length;
      while (lo < hi) { var m = (lo + hi) >> 1; if (a[m].x < x) lo = m + 1; else hi = m; }
      var L = null, F = null, i;
      for (i = lo; i < a.length; i++) if (a[i] !== self) { L = a[i]; break; }
      for (i = lo - 1; i >= 0; i--) if (a[i] !== self) { F = a[i]; break; }
      return [L, F];
    }
    function accFor(v, lane, L) {
      var gap = L ? L.x - L.len - v.x : Infinity, vl = L ? L.v : 0;
      if (lane === ACC && !cfg.add) { var ge = La - v.x; if (ge < gap && ge < Math.max(35, v.v * v.v / (2 * v.p.b) + 12)) { gap = ge; vl = 0; } }   /* 가속차로 끝 = 멈춘 벽(끝이 가까워져서야 본다 — 처음부터 보면 가속을 못 한다) */
      if (OBA.length && lane < n) { var ob = obAhead(lane, v.x); if (ob) { var go = ob.x - v.x; if (go < gap && go < Math.max(40, v.v * v.v / (2 * v.p.b) + 15)) { gap = go; vl = 0; } } }   /* 막힌 곳 = 멈춘 벽(가까워져야 본다) */
      if (v.exit && W > 0 && lane < n - 1 && v.x < W) { var gw = W + 15 - v.x; if (gw < 140 && gw < gap) { gap = gw; vl = 0; } }   /* 못 빠진 진출 차는 진출로 앞에서 속도를 줄인다 */
      var v0 = v0of({ lane: lane, x: v.x, tr: v.tr, f: v.f });
      if (lane === ACC && !cfg.add && v.x > 0 && v.side) v0 = Math.min(v0, Math.max(v.side.v + 2, 8));   /* 가속차로에서는 옆 차로 흐름에 속도를 맞춘다(틈 찾기) */
      return idm(v.v, v0, gap, vl, v.p);
    }
    function tryLc(v, by) {
      var cur = v.lane, x = v.x, opts = [], Lc = nbr(by, cur, x, v), aCur = accFor(v, cur, Lc[0]);
      var mand = 0, dir = 0, forcedOk = false, obM = cur < n && OBA.length ? obAhead(cur, x) : null; if (obM && obM.x - x > obM.warn) obM = null;
      if (cur === ACC) {
        if (x < 0 || x < S) return;   /* 연결로에서는 아직 본선 옆이 아니다 · 실선 구간은 차로 바꾸기 금지 */
        if (cfg.add) { mand = 0; }
        else { mand = 1; dir = -1; forcedOk = x > La - P.endZ || (v.v < 2 && x > La - 60); }
      } else if (obM) { dir = openLane(cur, obM); if (!dir) return; mand = 1; forcedOk = obM.x - x < 40 || (v.v < 2 && obM.x - x < 70); }   /* 막힌 차로 — 열린 쪽으로 비킨다 */
      else if (v.exit && W > 0 && x < W && x > W - 1000 && cur < n - 1) { mand = 1; dir = +1; forcedOk = x > W - 90; }
      [-1, 1].forEach(function (d) {
        var nl = cur + d; if (!laneOk(nl, x)) return; if (nl === ACC && !cfg.add) return;   /* 본선 차는 끝나는 가속차로로 들어가지 않는다 */
        if (cur < n && nl === ACC && !(cfg.add && obM && x >= 0)) return;
        if (mand && d !== dir) return;
        if (OBA.length && nl < n) { if (obCover(nl, x, v.len)) return; var o2 = obAhead(nl, x); if (o2 && o2.x - x < o2.warn && !(obM && o2.x >= obM.x - 5)) return; }   /* 앞이 막힌 차로로는 안 간다(같은 자리 막힘을 지나 열린 차로로 가는 길이면 됨) */
        var nb = nbr(by, nl, x, v), Ln = nb[0], Fn = nb[1];
        var gL = Ln ? Ln.x - Ln.len - x : 1e9, gF = Fn ? x - v.len - Fn.x : 1e9;
        if (gL < 0.6 || gF < 0.6) return;
        var aNew = accFor(v, nl, Ln), aFnNew = Fn ? accFor(Fn, nl, v) : 0, aFnOld = Fn ? accFor(Fn, nl, Ln) : 0;
        var Fo = Lc[1], aFoOld = Fo ? accFor(Fo, cur, v) : 0, aFoNew = Fo ? accFor(Fo, cur, Lc[0]) : 0;
        var safe = aFnNew >= -(mand ? P.bsafeM : P.bsafe), okForce = forcedOk && aFnNew >= -P.bforce && gF >= 2 && gL >= 1.5;   /* 억지로라도 차 들어갈 틈은 있어야 한다 */
        if (!safe && !okForce) return;
        var gain = aNew - aCur + P.pol * (aFnNew - aFnOld + aFoNew - aFoOld);
        var bias = 0;
        if (mand) bias = 3 + (cur === ACC ? 6 * Math.max(0, x / Math.max(La, 1)) : obM ? 6 * Math.max(0, 1 - (obM.x - x) / obM.warn) : 6 * Math.max(0, 1 - (W - x) / 1000));
        if (!mand && v.coop && cur === n - 1 && d === -1 && x > -250 && x < (cfg.add ? 150 : La)) bias += 2.5;   /* 협조하는 운전자는 합류 구간에서 본선 바깥 차로를 비워 준다 */
        if (!mand && d === 1 && v.exit) bias += 0.6;
        if (!mand && d === -1 && v.exit && W > 0 && x > W - 900) bias -= 2;
        if (gain + bias > P.dth) opts.push({ nl: nl, sc: gain + bias, aFn: aFnNew, Fn: Fn, Ln: Ln, forced: !safe || gF < 2 || gL < 2 });
      });
      if (!opts.length) return;
      opts.sort(function (p, q) { return q.sc - p.sc; });
      var o = opts[0];
      if (cur === ACC) {
        v.merged = true;
        if (meas()) { M.merges++; var vf = o.Fn ? o.Fn.v : v.v; M.dvSum += Math.abs(v.v - vf); }
        if (o.forced) { M.forced++; ev('forced', v, Math.round(-o.aFn * 10) / 10); }
        if (x > La - P.endZ) { if (meas()) M.endM++; }
      } else if (mand && o.forced && obM) { if (inZ(v)) M.oForced++; ev('oforce', v); }
      else if (mand && o.forced) { if (meas()) M.exitForced++; ev('xforce', v); }
      by[cur].splice(by[cur].indexOf(v), 1);
      v.lane = o.nl;
      var a = by[o.nl], i = 0; while (i < a.length && a[i].x < v.x) i++; a.splice(i, 0, v);
    }
    function step() {
      if (OB.length) OBA = OB.filter(function (o) { return obOn(o, t, cfg.warm); });
      spawn();
      var by = sortLanes(), i, v;
      for (i = 0; i < V.length; i++) { v = V[i]; v.lcT -= dt; if (v.lcT <= 0) { v.lcT += P.lcEvery; tryLc(v, by); } }
      for (i = 0; i < V.length; i++) {
        v = V[i]; var nb = nbr(by, v.lane, v.x, v), Lr = nb[0], Lp = Lr; if (v.lane === ACC && !cfg.add && v.x > 0) { var sd = nbr(by, n - 1, v.x, v); v.side = sd[0] || sd[1]; }
        if (Lr && v.lead !== Lr && v.lead && v.lead.lane === v.lane && v.lead.x > Lr.x && V.indexOf(v.lead) >= 0 && Lr.x - Lr.len - v.x < 40) { v.cutT = t; v.oldL = v.lead; }   /* 앞에 차가 끼어들었다 */
        if (v.cutT != null && t - v.cutT < P.react && v.oldL && v.oldL.lane === v.lane && v.oldL.x > v.x) Lp = v.oldL;   /* 알아채기 전에는 옛 앞차를 보고 달린다 */
        v.acc = accFor(v, v.lane, Lp); v.lead = Lr;
        if (v.coop && v.lane === n - 1 && !cfg.add) { var ab = nbr(by, ACC, v.x, v)[0]; if (ab && ab.v > 5 && ab.x > Math.max(0, S) && ab.x - v.x > 2 && ab.x - v.x < 40 && La - ab.x > 20) v.acc = Math.min(v.acc, Math.max(-1.5, idm(v.v, v0of(v), ab.x - ab.len - v.x + 12, ab.v, v.p))); }   /* 협조 — 옆 가속차로 차에게 틈을 열어 준다(살짝만) */
      }
      var keep = [];
      for (i = 0; i < V.length; i++) {
        v = V[i]; var a = Math.max(-P.bforce, v.acc), nvv = Math.max(0, v.v + a * dt);
        v.x += (v.v + nvv) / 2 * dt; v.v = nvv;
        if (v.lat !== v.lane) { var dl = v.lane - v.lat; v.lat += Math.sign(dl) * Math.min(Math.abs(dl), dt / 1.2); }
        if (a < -P.hard && t - v.hardT > 2.5) { v.hardT = t; if (inZ(v)) M.hard++; ev('hard', v, Math.round(-a * 10) / 10); }
        var L = v.lead;
        if (L && L.lane === v.lane) {
          var gap = L.x - L.len - v.x, dv = v.v - L.v;
          if (gap < 0.5) { if (!v.nearOn) { v.nearOn = true; if (inZ(v)) M.near++; ev('near', v); } if (gap < 0) { v.x = L.x - L.len - 0.05; v.v = Math.min(v.v, L.v); } } else if (gap > 2) v.nearOn = false;
          var ttc = dv > 0.1 ? gap / dv : 99;
          if (ttc < P.ttc && gap >= 0) { if (!v.ttcOn) { v.ttcOn = true; if (inZ(v)) M.ttc++; ev('ttc', v, Math.round(ttc * 10) / 10); } } else if (ttc > 3) v.ttcOn = false;
        }
        if (v.tIn == null && v.x >= P.x0 + 250) v.tIn = t;
        if (OBA.length && v.lane < n) { var ob3 = obAhead(v.lane, v.x); if (ob3 && ob3.x - v.x < 80 && v.v < 0.5) { if (!v.oStOn) { v.oStOn = true; if (inZ(v)) M.oStall++; ev('ostall', v); } } else if (v.v > 3) v.oStOn = false; }
        if (v.lane === ACC && !cfg.add && v.x > 0 && v.v < 0.5 && !v.stallOn) { v.stallOn = true; if (inZ(v)) M.stall++; ev('stall', v); }
        if (meas() && v.lane < n && v.x > -300 && v.x < (cfg.add ? 200 : La) + 200) { M.vSum += v.v; M.vN++; }
        if (meas() && v.lane === ACC && v.x < 0 && v.v < 2) M.rampQ = Math.max(M.rampQ, (function () { var c = 0; V.forEach(function (u) { if (u.lane === ACC && u.x < 0 && u.v < 2) c++; }); return c; })());
        if (W > 0 && v.exit && v.x >= W) {
          if (v.lane >= n - 1) { if (meas()) M.exits++; continue; }
          v.exit = false; if (meas()) M.missed++; ev('miss', v);
        }
        if (v.lane === ACC && !cfg.add && v.x > La + 1) { v.lane = n - 1; v.lat = n - 1; if (meas()) { M.forced++; M.merges++; } ev('forced', v, 0); }   /* 벽을 뚫었으면(없어야 한다) 본선으로 */
        if (v.x >= xE) { if (meas()) { M.thru++; if (!v.ramp && v.tIn != null && v.tIn >= cfg.warm) { M.ttS += t - v.tIn; M.ttN++; } } continue; }
        keep.push(v);
      }
      V = keep;
      if (meas() && t - cfg.warm >= frT) {
        frT += P.frameDt; var f = new Float32Array(V.length * 4);
        V.forEach(function (u, j) { f[j * 4] = u.x; f[j * 4 + 1] = u.lat; f[j * 4 + 2] = u.v / Math.max(1, v0of(u)); f[j * 4 + 3] = (u.tr ? 1 : 0) + (u.ramp ? 2 : 0) + (u.exit ? 4 : 0); });
        FR.push(f);
      }
      t += dt;
    }
    while (t < T) step();
    var hr = cfg.dur / 3600;
    return {
      cfg: cfg, xE: xE, frames: FR, ev: EV, obs: OB, warm: cfg.warm,
      m: { forced: M.forced, endM: M.endM, merges: M.merges, dv: M.merges ? M.dvSum / M.merges * 3.6 : 0, stall: M.stall, ttc: M.ttc, hard: M.hard, near: M.near,
           exits: M.exits, missed: M.missed, exitForced: M.exitForced, thru: M.thru / hr, vMain: M.vN ? M.vSum / M.vN * 3.6 : 0, rampQ: M.rampQ, pend: M.pendMax, oForced: M.oForced, oStall: M.oStall, delay: (function () { var s9 = M.ttS - M.ttN * (xE - P.x0 - 250) / limMs, n9 = M.ttN; V.forEach(function (u) { if (!u.ramp && u.tIn != null && u.tIn >= cfg.warm) { s9 += (t - u.tIn) - (u.x - P.x0 - 250) / limMs; n9++; } }); return n9 ? Math.max(0, s9 / n9) : 0; })(),   /* 아직 못 빠진 차도 지금까지 늦은 만큼 넣는다(다 막히면 0 으로 보이지 않게) */ bins: M.bins, binsK: M.binsK, hr: hr }
    };
  }

  /* ================= 자료 ================= */
  function mrgGet() { if (MRG) return Promise.resolve(MRG); return getJ('data/sim-merges.json').then(function (j) { MRG = j; return j; }); }
  function near(ll, R) { if (!MRG) return []; return MRG.items.map(function (m) { return { m: m, d: dist(ll, [m.lat, m.lon]) }; }).filter(function (o) { return o.d <= R; }).sort(function (a, b) { return a.d - b.d; }); }
  function volFor(m) {   /* 같은 길 이름 조사 지점 2.5km 안 — 지금 시각 · 두 방향 평균 */
    if (!VOL) return null; var d = new Date().getDay(), h = new Date().getHours(), best = null, bd = 2500;
    VOL.spots.forEach(function (s) { if (String(s.name).split('(')[0].trim() !== m.main) return; var dd = dist([m.lat, m.lon], [s.lat, s.lon]); if (dd < bd) { bd = dd; best = s; } });
    if (!best) return null; var arr = d === 0 ? best.su : d === 6 ? best.sa : best.wd, r = arr && arr[h]; if (!r) return null;
    return { spot: best, d: Math.round(bd), h: h, q: Math.round((r[0] + r[1]) / 2), both: r };
  }
  function taasFor(m) {
    if (!m.gu) return Promise.resolve(null);
    var u = m.gu === '11650' ? 'data/taas10-seocho.json' : 'data/r/' + m.gu + '/taas10.json';
    if (!TAAS[u]) TAAS[u] = getJ(u).catch(function () { return null; });
    return TAAS[u].then(function (j) {
      if (!j) return null; var R = 150, cells = [], fat = [], ty = {}, vi = {}, tot = 0, dead = 0, ser = 0;
      j.cells.forEach(function (c) { var dd = dist([m.lat, m.lon], [c[0], c[1]]); if (dd > R) return; var s = 0; for (var k = 2; k < 12; k++) s += c[k]; tot += s; dead += c[12]; ser += c[13]; cells.push(c);
        var tn = (j.dic.t[c[25]] || '기타').replace(/^차대차 - /, '').replace(/^차대사람 - .*/, '차대사람').replace(/^차량단독 - .*/, '차량단독'); ty[tn] = (ty[tn] || 0) + s;
        var vn = j.dic.v[c[23]] || '기타'; vi[vn] = (vi[vn] || 0) + c[24]; });
      j.fatal.forEach(function (f) { if (dist([m.lat, m.lon], [f[16], f[17]]) <= R) fat.push({ y: f[0], h: f[3], t: j.dic.t[f[5]] || f[5], v: j.dic.v[f[6]] || f[6], r: j.dic.r[f[7]] || f[7], k: j.dic.k[f[10]] || f[10], kk: j.dic.k[f[11]] || f[11] }); });
      return { n: cells.length, tot: tot, dead: dead, ser: ser, ty: ty, vi: vi, fat: fat, src: j.source };
    });
  }
  function cfgOf(m, vol) {
    var add = m.outL >= m.inL + m.ramp[1];
    return { n: Math.max(1, Math.min(6, m.inL)), add: add, La: 150, S: 0, qMain: vol ? Math.min(vol.q, m.inL * 2100) : m.inL * 1300, qRamp: 600 * Math.min(2, m.ramp[1]),
      truck: 0.1, lim: m.lim || 60, rampLim: m.ramp[2] || Math.min(m.lim || 60, 50), W: m.dn && m.dn[0] <= 900 ? m.dn[0] : 0, exitP: 0.12, meter: 0, courtesy: 0.3, warm: P.warm, dur: P.dur };
  }
  var CHG = [
    ['la', '가속차로 +100m', function (c) { c.La += 100; }],
    ['meter', '연결로 진입 신호(한 대씩 4초 간격)', function (c) { c.meter = 4; }],
    ['court', '본선 운전자가 모두 비켜 주고 틈을 열어 준다(안내 표지·계도 · 현행 30%)', function (c) { c.courtesy = 1; }],
    ['spd', '제한속도 −10km/h', function (c) { c.lim = Math.max(30, c.lim - 10); }],
    ['truck', '대형차 절반으로', function (c) { c.truck /= 2; }],
    ['solid', '가속차로 앞쪽 50m 실선(늦게 끼어들게)', function (c) { c.S = 50; }],
    ['nosolid', '실선 없애기', function (c) { c.S = 0; }],
    ['rampq', '연결로 교통량 −30%', function (c) { c.qRamp = Math.round(c.qRamp * 0.7); }],
    ['add', '합류 뒤 차로 하나 더(차로 더해짐)', function (c) { c.add = true; }],
    ['noexit', '다음 진출로 없음(엮임 구간 없애기)', function (c) { c.W = 0; }]
  ];

  var EVCHG = [   /* 도로 위 일이 걸려 있을 때 맨 앞에 */
    ['noev', '이 일이 없을 때(평소와 견주기 — 이 일이 얼마나 나쁘게 하나)', function (c) { c.ev = null; }],
    ['warn', '미리 알림 — 600m 앞에서 차로 비우기 안내(표지·경광등)', function (c) { c.ev.warn = 600; }],
    ['fast', '빨리 치움 — 막힌 시간 절반', function (c) { c.ev.fast = 1; }],
    ['buffer', '옆 차로 하나 더 막아 안전 공간(경찰 통제)', function (c) { c.ev.k = Math.min(c.n, (c.ev.k || 1) + 1); }],
    ['evspd', '그 앞 300m 감속 안내(제한속도 −20km/h)', function (c) { c.ev.slow = 20; }]
  ];
  function chgList() { return (CUR && CUR.cfg.ev && CUR.cfg.ev.kind ? EVCHG : []).concat(CHG); }
  var EVK = [['', '없음'], ['acc', '🚑 사고 — 차로 막힘'], ['work', '🚧 공사 — 차로 막힘'], ['bus', '🚌 버스 정차(바깥 차로)'], ['park', '🅿️ 불법 주정차(바깥 차로)'], ['ctrl', '⛔ 통제(집회·행진·경찰) — 그 자리부터 끝까지']];
  function evDef(kind, c) { var n = c.n; return { kind: kind, lane: n - 1, k: 1, x: kind === 'acc' ? Math.round(((c.add ? 150 : c.La) + 60) / 10) * 10 : kind === 'ctrl' ? 300 : 200, len: 200, when: kind === 'acc' ? 'mid' : kind === 'ctrl' ? 'late' : 'all', gawk: 0.2, vz: kind === 'work' ? Math.min(c.lim, 50) : 0, nb: 30, dwell: 20, cars: 2 }; }
  function evHtml() {
    var c = CUR.cfg, e = c.ev || { kind: '' }, n = c.n, opt = function (L, cur) { return L.map(function (x) { return '<option value="' + x[0] + '"' + (String(x[0]) === String(cur) ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join(''); };
    var h = '<h4>🚧 도로 위 일 — 두 판 모두에 건다</h4><select data-mc="ev.kind">' + opt(EVK, e.kind) + '</select>';
    if (!e.kind) return h + ' <span class="sn">사고·공사·버스 정차·불법 주정차·통제를 이 합류부에 놓고 돌려 본다</span>';
    var row = function (lab, ctl, src) { return '<div class="row"><span>' + lab + '</span>' + ctl + '<b></b></div>' + (src ? '<div class="sn" style="margin:-2px 0 4px 9.5em">' + src + '</div>' : ''); };
    var lanes = []; for (var l = 0; l < n; l++) lanes.push([l, (l + 1) + '차로' + (l === 0 ? '(중앙선 쪽)' : l === n - 1 ? '(바깥)' : '')]);
    if (e.kind === 'acc' || e.kind === 'work' || e.kind === 'ctrl') { var ks = []; for (var q = 1; q <= n; q++) ks.push([q, q === n ? q + '개(모든 차로 — 막힘)' : q + '개']);
      h += row('막힌 차로', '<span><select data-mc="ev.lane">' + opt(lanes, Math.min(e.lane, n - 1)) + '</select> 부터 <select data-mc="ev.k">' + opt(ks, e.k) + '</select></span>'); }
    var xLab = function (x) { return x < 0 ? '합류점 앞 ' + (-x) + 'm' : '합류점 뒤 ' + x + 'm'; };
    h += row('자리', '<input type="range" data-mc="ev.x" min="-400" max="900" step="10" value="' + e.x + '"><b id="m2dMrgV_ev_x">' + xLab(e.x) + '</b>', '').replace('<b></b></div>', '</div>');
    if (e.kind === 'work') { h += row('공사 길이', '<input type="range" data-mc="ev.len" min="50" max="500" step="10" value="' + e.len + '"><b id="m2dMrgV_ev_len">' + e.len + 'm</b>').replace('<b></b></div>', '</div>');
      h += row('공사 구간 속도', '<select data-mc="ev.vz">' + opt([[0, '그대로'], [30, '30km/h'], [40, '40km/h'], [50, '50km/h'], [60, '60km/h']], e.vz) + '</select>', '<span class="b d">설계값 — 현장 표지대로</span>'); }
    if (e.kind === 'bus') h += row('버스', '<span><select data-mc="ev.nb">' + opt([10, 20, 30, 45, 60].map(function (x) { return [x, x + '대/시']; }), e.nb) + '</select> 한 대 <select data-mc="ev.dwell">' + opt([10, 20, 30, 45].map(function (x) { return [x, x + '초']; }), e.dwell) + '</select> 섬</span>', '<span class="b d">설계값 — 정류장 노선·배차로 바꾼다</span>');
    if (e.kind === 'park') h += row('주정차', '<select data-mc="ev.cars">' + opt([1, 2, 3, 5, 8].map(function (x) { return [x, x + '대(약 ' + x * 7 + 'm)']; }), e.cars) + '</select>');
    if (e.kind === 'acc' || e.kind === 'work' || e.kind === 'ctrl') h += row('언제', '<select data-mc="ev.when">' + opt([['all', '처음부터 끝까지'], ['mid', '2분 뒤 생겨 5분 뒤 치움'], ['late', '3분 뒤 생겨 끝까지']], e.when) + '</select>');
    if (e.kind === 'acc') h += row('옆 차로 구경 감속', '<select data-mc="ev.gawk">' + opt([[0, '없음'], [0.1, '10%'], [0.2, '20%'], [0.3, '30%'], [0.4, '40%']], e.gawk) + '</select>', '<span class="b d">설계값 — 미국 도로용량편람도 값을 정하지 않았다(FHWA)</span>');
    h += '<div class="sn">막힌 차로의 차는 그 앞 <b>' + (e.warn || { acc: 150, work: 400, bus: 60, park: 100, ctrl: 300 }[e.kind]) + 'm</b>부터 옆으로 비키기 시작한다 <span class="b d">설계값</span> · 막힌 곳은 멈춘 차처럼 보이고 가까워져서야 선다 · 두 판 모두에 걸리므로 아래 「바꿔 볼 것」으로 대응(미리 알림·빨리 치움·안전 공간·감속 안내)이나 「이 일이 없을 때」를 견준다</div>';
    return h;
  }
  /* ================= 화면 ================= */
  function css() {
    if ($('m2dMrgCss')) return; var s = document.createElement('style'); s.id = 'm2dMrgCss';
    s.textContent = '#m2dMrg{position:fixed;left:6px;right:6px;top:6px;bottom:6px;max-width:640px;margin:0 auto;z-index:2600;background:#fff;color:#111;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.35);padding:10px 12px;overflow:auto;display:none;font-size:13px;line-height:1.45}' +
      '#m2dMrg.on{display:block}#m2dMrg h3{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;align-items:center;gap:8px}#m2dMrg h4{margin:10px 0 4px;font-size:13.5px}' +
      '#m2dMrg table{border-collapse:collapse;width:100%;font-size:12px}#m2dMrg td,#m2dMrg th{border-bottom:1px solid #e5e7eb;padding:3px 4px;text-align:left;vertical-align:top}#m2dMrg td.n,#m2dMrg th.n{text-align:right;font-variant-numeric:tabular-nums}' +
      '#m2dMrg .sn{color:#555;font-size:12px}#m2dMrg .warn{background:#fff7ed;border:1px solid #fdba74;border-radius:8px;padding:6px 8px;margin:6px 0;font-size:12px}#m2dMrg .ok{background:#ecfdf5;border:1px solid #6ee7b7;border-radius:8px;padding:6px 8px;margin:6px 0;font-size:12px}' +
      '#m2dMrg button{min-height:36px;border-radius:8px;border:1px solid #93c5fd;background:#eff6ff;padding:4px 10px;font-weight:700;cursor:pointer;color:inherit}#m2dMrg button.go{background:#1d4ed8;color:#fff;border-color:#1d4ed8}#m2dMrg button.on{background:#1e3a8a;color:#fff}' +
      '#m2dMrg .b{display:inline-block;padding:0 6px;border-radius:6px;font-size:11px;font-weight:700}#m2dMrg .b.k{background:#dcfce7;color:#166534}#m2dMrg .b.d{background:#fef3c7;color:#92400e}#m2dMrg .b.x{background:#f3f4f6;color:#6b7280}' +
      '#m2dMrg .row{display:grid;grid-template-columns:9.5em 1fr 4.6em;gap:6px;align-items:center;margin:3px 0}#m2dMrg .row input{width:100%}#m2dMrg select{min-height:34px;max-width:100%}' +
      '#m2dMrg canvas{width:100%;display:block;border-radius:8px;background:#1f2937;margin-top:6px}#m2dMrg .up{color:#b91c1c;font-weight:700}#m2dMrg .dn{color:#15803d;font-weight:700}' +
      '@media (prefers-color-scheme:dark){#m2dMrg{background:#111827;color:#e5e7eb}#m2dMrg td,#m2dMrg th{border-color:#374151}#m2dMrg .sn{color:#9ca3af}#m2dMrg button{background:#1f2937;border-color:#1e40af}#m2dMrg .warn{background:#3b2a12;border-color:#92400e}#m2dMrg .ok{background:#0f2f24;border-color:#065f46}#m2dMrg .up{color:#fca5a5}#m2dMrg .dn{color:#86efac}}';
    document.head.appendChild(s);
  }
  function panel() { css(); if (!PANEL) { PANEL = document.createElement('div'); PANEL.id = 'm2dMrg'; document.body.appendChild(PANEL); PANEL.addEventListener('click', onClick); PANEL.addEventListener('input', onInput); PANEL.addEventListener('change', onInput); } PANEL.classList.add('on'); return PANEL; }
  function close() { stopAnim(); if (PANEL) PANEL.classList.remove('on'); }
  function head(t) { return '<h3>🔀 ' + esc(t) + '<button data-mg="x" aria-label="닫기">✕ 닫기</button></h3>'; }
  function tyName(t) { return { '001': '고가', '002': '지하차도', '003': '교량', '004': '터널' }[t] || ''; }
  function title(m) { return (m.nm || m.main) + ' — ' + m.ramp[0] + ' → ' + m.main; }
  var SL = [   /* 막대 — 현행 값을 정한다(바꾼 안은 아래 고르기) */
    ['La', '가속차로 길이', 50, 400, 10, 'm', '설계값 — 자료에 없다 · 현장·항공사진으로 확인'],
    ['qMain', '본선 교통량', 300, 9000, 100, '대/시', ''],
    ['qRamp', '연결로 교통량', 100, 2400, 50, '대/시', '설계값 — 연결로 교통량 조사 자료 없음'],
    ['truck', '대형차 비율', 0, 0.4, 0.01, '%', '설계값'],
    ['lim', '본선 제한속도', 30, 110, 10, 'km/h', '표준노드링크 값'],
    ['S', '가속차로 앞 실선', 0, 200, 10, 'm', '설계값 — 실선 구간에서는 끼어들 수 없다'],
    ['W', '다음 진출로까지', 0, 900, 10, 'm', '표준노드링크 본선 거리 · 0 = 없음'],
    ['exitP', '그 진출로로 나갈 몫', 0, 0.4, 0.01, '%', '설계값']
  ];
  function fmt(k, v) { return (k === 'truck' || k === 'exitP') ? Math.round(v * 100) : (k === 'qMain' || k === 'qRamp') ? Math.round(v).toLocaleString() : Math.round(v); }
  function srcOf(k) {
    var C = CUR; if (k === 'qMain') return C.vol ? '<span class="b k">조사 ' + esc(C.vol.spot.id) + ' ' + esc(C.vol.spot.name) + ' · ' + C.vol.h + '시 · 두 방향 평균(' + C.vol.both.join('/') + ') · ' + C.vol.d + 'm</span>' : '<span class="b d">설계값 — 같은 길 이름 조사 지점 없음(차로당 1,300)</span>';
    if (k === 'lim') return '<span class="b k">표준노드링크</span>'; if (k === 'W') return C.m.dn ? '<span class="b k">표준노드링크 ' + C.m.dn[0] + 'm</span>' : '<span class="b x">1.5km 안 없음</span>';
    var s = SL.filter(function (x) { return x[0] === k; })[0]; return '<span class="b d">' + esc(s[6]) + '</span>';
  }
  function cfgHtml() {
    var c = CUR.cfg, m = CUR.m;
    var h = '<h4>⚙ 현행(지금 모습) — 막대로 바꿀 수 있다</h4>';
    h += '<div class="sn">본선 <b>' + m.inL + '차로</b> 들어옴 · 연결로 <b>' + m.ramp[1] + '차로</b>(' + esc(m.ramp[0]) + ', 제한 ' + (m.ramp[2] || '—') + ') · 본선 <b>' + m.outL + '차로</b> 나감 → ' +
      (c.add ? '<b>차로가 더해지는 합류</b>(가속차로가 끝나지 않는다)' : '<b>가속차로가 끝나는 합류</b>(끝까지 못 들어가면 멈춘다)') + ' <span class="b k">표준노드링크 차로 수 — 현장과 다를 수 있다</span> ' +
      '<label><input type="checkbox" data-mc="add"' + (c.add ? ' checked' : '') + '> 차로 더해짐</label></div>';
    SL.forEach(function (s) { if (c.add && (s[0] === 'La' || s[0] === 'S')) return;
      h += '<div class="row"><span>' + s[1] + '</span><input type="range" data-mc="' + s[0] + '" min="' + s[2] + '" max="' + s[3] + '" step="' + s[4] + '" value="' + c[s[0]] + '"><b id="m2dMrgV_' + s[0] + '">' + fmt(s[0], c[s[0]]) + s[5].replace('%', '%') + '</b></div><div class="sn" style="margin:-2px 0 4px 9.5em">' + srcOf(s[0]) + '</div>'; });
    h += evHtml();
    h += '<h4>🔁 바꿔 볼 것</h4><select data-mc="chg">' + chgList().map(function (x) { return '<option value="' + x[0] + '"' + (CUR.chg === x[0] ? ' selected' : '') + '>' + esc(x[1]) + '</option>'; }).join('') + '</select> ';
    h += '<button class="go" data-mg="run">▶ 10분 돌려 견주기</button> <span class="sn">같은 차들 세 벌(씨앗 ' + CUR.seed + '…)로 현행·바꾼 안 · 몇 초</span>';
    return h;
  }
  function taasHtml(t) {
    if (!t) return '<h4>🚑 이 자리 실제 사고</h4><div class="sn">이 구의 TAAS 10년 자료를 아직 못 받았다(또는 없음).</div>';
    var h = '<h4>🚑 이 자리 실제 사고 — 합류점 150m 안 · TAAS 2016~2025</h4>';
    if (!t.n) return h + '<div class="sn">150m 안 100m 칸에 사고 기록이 없다.</div>';
    var ty = Object.keys(t.ty).sort(function (a, b) { return t.ty[b] - t.ty[a]; }), vi = Object.keys(t.vi).sort(function (a, b) { return t.vi[b] - t.vi[a]; });
    h += '<div class="sn">100m 칸 ' + t.n + '개 · 사고 <b>' + t.tot.toLocaleString() + '건</b> · 사망 ' + t.dead + ' · 중상 ' + t.ser + '</div>';
    h += '<div class="sn">칸마다 「주된 사고유형」으로 묶은 건수: ' + ty.slice(0, 4).map(function (k) { return esc(k) + ' ' + t.ty[k]; }).join(' · ') + '</div>';
    h += '<div class="sn">주된 법규위반(칸마다 1위의 합): ' + vi.slice(0, 3).map(function (k) { return esc(k) + ' ' + t.vi[k]; }).join(' · ') + '</div>';
    if (t.fat.length) h += '<details><summary>사망사고 ' + t.fat.length + '건(한 건씩)</summary><ul style="margin:4px 0;padding-left:18px;font-size:11.5px">' + t.fat.map(function (f) { return '<li>' + f.y + '년 ' + f.h + '시 · ' + esc(f.t) + ' · ' + esc(f.r) + ' · ' + esc(f.v) + ' · ' + esc(f.k) + '→' + esc(f.kk) + '</li>'; }).join('') + '</ul></details>';
    return h + '<div class="sn">⚠ 100m 칸이라 <b>고가·교량 아래 일반도로 사고가 섞일 수 있다</b>(사망사고의 도로형태로 가려 본다) · 이 숫자는 <b>보이기만 하고 시뮬에 넣지 않는다</b> · 출처: ' + esc(t.src) + '</div>';
  }
  function openM(m) {
    var my = ++CARDSEQ, Pn = panel(); stopAnim();
    Pn.innerHTML = head(title(m)) + '<div class="sn">자료 받는 중…</div>';
    Promise.all([VOL ? VOL : getJ('data/traffic-vol-seoul.json').then(function (j) { VOL = j; return j; }).catch(function () { return null; }), taasFor(m)]).then(function (a) {
      if (my !== CARDSEQ) return;
      var vol = volFor(m), seed = 1 + (parseInt(String(m.id).slice(-6), 10) % 9973 || 7);
      CUR = { m: m, vol: vol, taas: a[1], cfg: cfgOf(m, vol), chg: m.dn && m.dn[0] < 600 ? 'noexit' : 'la', seed: seed, res: null, view: 1 };
      paint();
    });
  }
  function paint() {
    var m = CUR.m, h = head(title(m));
    h += '<div class="sn">' + esc(m.gnm || '') + ' · ' + esc(m.main) + (tyName(m.ty) ? ' (' + tyName(m.ty) + ')' : '') + ' · 등급 ' + m.gr + (m.dn ? ' · 아래쪽 다음 진출로 <b>' + m.dn[0] + 'm</b>' : '') + (m.up ? ' · 위쪽 앞 연결로 ' + m.up[0] + 'm' : '') + ' · <b>개념 시연 — 예측·보증이 아니다</b></div>';
    if (m.gr >= 3) h += '<div class="warn">본선(' + esc(m.main) + ')이 <b>일반도로</b>다 — 아래쪽 신호 교차로에서 서는 줄은 이 모형에 없다(합류부만 본다). 신호 대기는 🧪 「막히는 교차로」 시뮬로 함께 본다.</div>';
    if (m.dn && m.dn[0] < 600) h += '<div class="warn">합류하자마자 <b>' + m.dn[0] + 'm 뒤에 진출로</b>가 있다 — 들어오는 차(오른쪽 → 왼쪽)와 나가려는 차(왼쪽 → 오른쪽)가 같은 구간에서 엇갈리는 <b>엮임 구간</b>이다. 짧을수록 억지 차로 바꾸기가 늘어난다.</div>';
    h += taasHtml(CUR.taas) + cfgHtml() + '<div id="m2dMrgRes">' + (CUR.res ? resHtml() : '') + '</div>';
    h += '<div class="sn" style="margin-top:8px">모형: 앞차 따라가기 IDM(Treiber 외 2000) · 차로 바꾸기 MOBIL(Kesting 외 2007) — 계수는 교과서 값(설계값) · 억지 끼어들기 = 뒤차가 4m/s² 넘게 급제동해야 하는 끼어들기 · 아슬아슬 = 충돌까지 1.5초 미만 · 출처: 국가표준 노드링크 · 서울시 교통량 조사 · TAAS</div>';
    PANEL.innerHTML = h; if (CUR.res) startAnim();
  }
  function pct(a, b) { if (!a && !b) return '<span class="sn">0 → 0</span>'; var d = b - a, r = a ? Math.round(d / a * 100) : null; return (d === 0 ? '<span class="sn">같음</span>' : '<span class="' + (d > 0 ? 'up' : 'dn') + '">' + (d > 0 ? '+' : '') + (Math.abs(d) < 10 ? Math.round(d * 10) / 10 : Math.round(d)) + (r != null ? ' (' + (r > 0 ? '+' : '') + r + '%)' : '') + '</span>'); }
  function resHtml() {
    var A = CUR.res[0].m, B = CUR.res[1].m, ch = CUR.res.ch || chgList().filter(function (x) { return x[0] === CUR.chg; })[0], per = function (x, r) { return Math.round(x / r.hr); };
    var rows = [
      ['억지 끼어들기(측면 충돌형)', per(A.forced, A), per(B.forced, B), '/시', true],
      ['가속차로 끝 30m 에서 합류', per(A.endM, A), per(B.endM, B), '/시', true],
      ['가속차로 끝에서 멈춤', per(A.stall, A), per(B.stall, B), '/시', true],
      ['아슬아슬 — 충돌까지 1.5초 미만(추돌형)', per(A.ttc, A), per(B.ttc, B), '/시', true],
      ['급제동(4m/s² 넘게)', per(A.hard, A), per(B.hard, B), '/시', true],
      ['합류 때 뒤차와 속도 차', Math.round(A.dv), Math.round(B.dv), 'km/h', true],
      ['합류 구간 본선 평균 속도', Math.round(A.vMain), Math.round(B.vMain), 'km/h', false],
      ['빠져나간 차(처리량)', Math.round(A.thru), Math.round(B.thru), '대/시', false],
      ['연결로에 선 줄(최대)', Math.round(A.rampQ), Math.round(B.rampQ), '대', true]
    ];
    if (CUR.res[0].cfg.W > 0 || CUR.res[1].cfg.W > 0) rows.push(['진출 놓침(엮임)', per(A.missed, A), per(B.missed, B), '/시', true], ['진출하려 억지 차로 바꾸기', per(A.exitForced, A), per(B.exitForced, B), '/시', true]);
    if (CUR.res[0].obs.length || CUR.res[1].obs.length) rows.unshift(['이 구간을 지나는 데 더 걸린 시간(본선 차 평균)', Math.round(A.delay), Math.round(B.delay), '초', true], ['막힌 차로를 피해 억지 차로 바꾸기', per(A.oForced, A), per(B.oForced, B), '/시', true], ['막힌 곳 앞에서 멈춤', per(A.oStall, A), per(B.oStall, B), '/시', true]);
    if (A.pend >= 1 || B.pend >= 1) rows.push(['들어오지 못하고 밀린 차(최대)', Math.round(A.pend), Math.round(B.pend), '대', true]);
    var h = '<h4>📊 현행 ↔ 바꾼 안(' + esc(ch[1]) + ') — 10분 × 같은 차들 세 벌 평균</h4><table><tr><th>지표</th><th class="n">현행</th><th class="n">바꾼 안</th><th class="n">차이</th></tr>' +
      rows.map(function (r) { var cell = pct(r[1], r[2]); if (!r[4] && r[2] !== r[1]) cell = cell.replace('class="up"', 'class="dnX"').replace('class="dn"', 'class="up"').replace('class="dnX"', 'class="dn"'); return '<tr><td>' + r[0] + '</td><td class="n">' + r[1] + ' <small>' + r[3] + '</small></td><td class="n">' + r[2] + '</td><td class="n">' + cell + '</td></tr>'; }).join('') + '</table>';
    h += '<div class="sn">빨강 = 나빠짐 · 초록 = 좋아짐(속도·처리량은 늘면 좋아짐) · 세 벌 평균이어도 몇 건 차이는 우연일 수 있다 — 다른 차들로 다시 돌려 같은 쪽으로 움직이는지 본다 <button data-mg="seed">🎲 다른 차들로 다시</button></div>';
    h += causeHtml();
    h += '<h4>🎞 다시 보기</h4><div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center"><button data-mg="v0" class="' + (CUR.view === 0 ? 'on' : '') + '">현행</button><button data-mg="v1" class="' + (CUR.view === 1 ? 'on' : '') + '">바꾼 안</button><button data-mg="pp">⏯</button><span class="sn" id="m2dMrgT"></span></div>' +
      '<canvas id="m2dMrgC" height="240"></canvas><div class="sn">색 = 제 속도 대비(초록 빠름 → 빨강 멈춤) · 네모가 큰 것 = 대형차 · 하늘색 테 = 연결로에서 온 차 · 노란 점 = 다음 진출로로 나갈 차 · ✖ 억지 끼어들기 · ● 아슬아슬 · ▼ 급제동 · □ 막힌 곳 앞 멈춤 · 빨강 ✚ 사고 · 주황 ▲ 공사 · 파랑 B 버스 · 회색 P 주정차 · 보라 ⛔ 통제 · 아래 막대 = 25m 마다 위험 사건이 몰린 곳(현행 회색 · 바꾼 안 파랑)</div>';
    return h;
  }
  function causeHtml() {   /* 시뮬이 보인 위험이 어디서 왜 — 실제 사고 유형과 나란히(판단은 사람) */
    var A = CUR.res[0], m = A.m, c = A.cfg, t = CUR.taas, out = [], hr = m.hr;
    if (!c.add && m.forced / hr >= 3) out.push('가속차로(' + c.La + 'm) 안에서 틈을 못 찾은 차가 끝에서 <b>억지로 끼어든다(시간당 ' + Math.round(m.forced / hr) + '건)</b> — 측면 충돌·끼어들기 시비가 날 자리.');
    if (m.ttc / hr >= 5) { var bk = Object.keys(m.binsK).filter(function (b) { return m.binsK[b].ttc; }).sort(function (a, b) { return m.binsK[b].ttc - m.binsK[a].ttc; })[0]; out.push('합류점 ' + (bk != null ? (bk >= 0 ? '뒤 ' : '앞 ') + Math.abs(bk) + '~' + Math.abs(+bk + 25) + 'm' : '') + ' 에 <b>아슬아슬(충돌까지 1.5초 미만)</b>이 몰린다 — 끼어든 차 앞에서 뒤차가 급히 서는 <b>추돌형</b>.'); }
    if (m.dv >= 15) out.push('합류하는 차가 본선보다 <b>' + Math.round(m.dv) + 'km/h 느리게</b> 들어온다 — 가속이 덜 된 채 붙는다.');
    if (c.W > 0 && (m.missed + m.exitForced) / hr >= 2) out.push(c.W + 'm 엮임 구간에서 나가려는 차가 <b>마지막에 오른쪽으로 꺾는다</b> — 들어오는 차와 엇갈린다.');
    if (m.rampQ >= 5) out.push('연결로에 <b>' + m.rampQ + '대</b>까지 줄이 선다 — 연결로 꼬리가 아래 일반도로 교차로까지 닿는지 볼 것.');
    if (A.obs.length) { var e9 = c.ev, nm9 = EVK.filter(function (x) { return x[0] === e9.kind; })[0][1].split(' — ')[0];
      if (m.delay >= 20) out.push(nm9 + ' 때문에 본선 차가 이 구간을 지나는 데 <b>평균 ' + Math.round(m.delay) + '초 더</b> 걸린다' + (m.pend >= 5 ? ' · 입구 밖까지 <b>' + Math.round(m.pend) + '대</b> 밀린다(줄이 이 그림보다 길다)' : '') + '.');
      if (m.oForced / hr >= 3) out.push('막힌 차로에서 비키려는 차가 <b>억지로 옆 차로에 끼어든다(시간당 ' + Math.round(m.oForced / hr) + '건)</b> — 2차 사고(측면)가 날 자리.');
      if (m.oStall / hr >= 3) out.push('막힌 곳 바로 앞에서 <b>서 버리는 차(시간당 ' + Math.round(m.oStall / hr) + '대)</b> — 뒤에서 오는 차와의 추돌(2차 사고) 위험 · 미리 알림·감속 안내를 견줘 본다.'); }
    if (!out.length) out.push('이 조건에서는 두드러진 위험 사건이 적다 — 교통량·대형차·가속차로를 바꿔 어디서부터 나빠지는지 본다.');
    var h = '<h4>🔎 시뮬이 보인 원인 후보</h4><ul style="margin:4px 0;padding-left:18px">' + out.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul>';
    if (t && t.tot) { var side = t.ty['충돌'] || 0, rear = t.ty['추돌'] || 0; h += '<div class="ok">실제 사고(위)와 나란히: 칸마다 주된 유형이 <b>충돌 ' + side + '건 · 추돌 ' + rear + '건</b>이다 — 시뮬의 억지 끼어들기는 충돌(측면)형, 아슬아슬·급제동은 추돌형에 가깝다. <b>맞물리는지는 사람이 판단한다</b>(실제 사고 원인은 운전자 상태·날씨·노면도 섞인다).</div>'; }
    return h;
  }

  /* ---- 다시 보기(캔버스) ---- */
  function stopAnim() { if (ANIM) { cancelAnimationFrame(ANIM.raf); ANIM = null; } }
  function startAnim() {
    stopAnim(); var cv = $('m2dMrgC'); if (!cv || !CUR.res) return;
    ANIM = { k: 0, play: true, last: 0, raf: 0 };
    function frame(ts) {
      if (!ANIM) return; if (!document.body.contains(cv)) { ANIM = null; return; }
      if (ANIM.play && ts - ANIM.last > 1000 / 16) { ANIM.last = ts; ANIM.k = (ANIM.k + 1) % CUR.res[CUR.view].frames.length; }
      draw(cv, CUR.res[CUR.view], ANIM.k); ANIM.raf = requestAnimationFrame(frame);
    }
    ANIM.raf = requestAnimationFrame(frame);
  }
  function draw(cv, R, k) {
    var dpr = window.devicePixelRatio || 1, W = cv.clientWidth || 320, H = 240; if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = H * dpr; }
    var g = cv.getContext('2d'); g.setTransform(dpr, 0, 0, dpr, 0, 0); g.clearRect(0, 0, W, H);
    var c = R.cfg, n = c.n, ob0 = (R.obs || [])[0], xa = Math.min(-260, ob0 ? ob0.x - 60 : 0), xb = Math.min(R.xE, Math.max(c.add ? 260 : c.La + 160, c.W ? c.W + 60 : 0, ob0 ? ob0.x + Math.min(ob0.len, 400) + 80 : 0)), sx = (W - 16) / (xb - xa), LH = Math.min(16, 120 / (n + 1)), top = 22;
    function X(x) { return 8 + (x - xa) * sx; } function Y(l) { return top + l * LH + LH / 2; }
    g.fillStyle = '#374151'; g.fillRect(X(xa), top, X(xb) - X(xa), n * LH);
    g.fillRect(X(0), top + n * LH, X(c.add ? xb : c.La) - X(0), LH);
    g.beginPath(); g.moveTo(X(xa), top + n * LH + LH * 2.2); g.lineTo(X(0), top + n * LH + LH); g.lineTo(X(0), top + n * LH + LH * 0); g.lineTo(X(xa) + 0, top + n * LH + LH * 1.2); g.closePath(); g.fill();
    g.strokeStyle = 'rgba(255,255,255,.55)'; g.setLineDash([6, 8]); g.lineWidth = 1;
    for (var l = 1; l < n; l++) { g.beginPath(); g.moveTo(X(xa), top + l * LH); g.lineTo(X(xb), top + l * LH); g.stroke(); }
    g.beginPath(); g.moveTo(X(c.S || 0), top + n * LH); g.lineTo(X(c.add ? xb : c.La), top + n * LH); g.stroke(); g.setLineDash([]);
    if (c.S) { g.strokeStyle = '#fff'; g.lineWidth = 2; g.beginPath(); g.moveTo(X(0), top + n * LH); g.lineTo(X(c.S), top + n * LH); g.stroke(); }
    g.strokeStyle = '#facc15'; g.lineWidth = 2; g.beginPath(); g.moveTo(X(xa), top); g.lineTo(X(xb), top); g.stroke();
    if (!c.add) { g.fillStyle = '#f97316'; g.fillRect(X(c.La) - 2, top + n * LH, 3, LH); }
    if (c.W > 0) { g.fillStyle = '#fde047'; g.font = '10px sans-serif'; g.fillText('↘ 진출 ' + c.W + 'm', X(c.W) - 30, top + n * LH + LH * 2 + 10); g.fillRect(X(c.W), top + (n - 1) * LH, 2, LH); }
    g.fillStyle = '#e5e7eb'; g.font = '11px sans-serif'; g.fillText('본선 ' + n + '차로 →', 10, 14); g.fillText('합류점', X(0) - 16, 14);
    var f = R.frames[k] || [], t = k * P.frameDt;
    (R.obs || []).forEach(function (o) { if (!obOn(o, t + (R.warm || 0), R.warm || 0)) return; var x1 = X(Math.max(xa, o.x)), x2 = X(Math.min(xb, o.x + o.len)), yy = top + o.lane * LH;
      g.fillStyle = { acc: '#dc2626', work: '#f97316', bus: '#2563eb', park: '#6b7280', ctrl: '#7c3aed' }[o.kind] || '#dc2626'; g.fillRect(x1, yy + 1, Math.max(3, x2 - x1), LH - 2);
      g.fillStyle = '#fff'; g.font = Math.round(LH * 0.7) + 'px sans-serif'; if (x2 - x1 > 10) g.fillText({ acc: '✚', work: '▲', bus: 'B', park: 'P', ctrl: '⛔' }[o.kind] || '!', x1 + 2, yy + LH * 0.78); });
    for (var i = 0; i < f.length; i += 4) {
      var x = f[i]; if (x < xa || x > xb) continue; var lat = f[i + 1], r = Math.max(0, Math.min(1, f[i + 2])), fl = f[i + 3], tr = fl & 1;
      var col = r > 0.8 ? '#22c55e' : r > 0.55 ? '#a3e635' : r > 0.3 ? '#facc15' : r > 0.1 ? '#f97316' : '#ef4444';
      var ln = (tr ? 11 : 4.6) * sx, wd = LH * (tr ? 0.62 : 0.5), yy = lat >= n && x < 0 ? top + n * LH + LH * (1 + Math.min(1.2, -x / 220 * 1.2)) - LH / 2 + LH / 2 : Y(lat);
      ln = Math.max(tr ? 9 : 5, ln); g.fillStyle = col; g.fillRect(X(x) - ln, yy - wd / 2, ln, wd);
      if (fl & 2) { g.strokeStyle = '#38bdf8'; g.lineWidth = 1; g.strokeRect(X(x) - ln, yy - wd / 2, ln, wd); }
      if (fl & 4) { g.fillStyle = '#fde047'; g.fillRect(X(x) - 1, yy - 1, 2, 2); }
    }
    R.ev.forEach(function (e) { if (e[0] > t || e[0] < t - 2.5 || e[1] < xa || e[1] > xb) return; var xx = X(e[1]), yy = Y(Math.min(e[2], n)), a = 1 - (t - e[0]) / 2.5; g.globalAlpha = a;
      if (e[3] === 'ostall') { g.strokeStyle = '#fde047'; g.lineWidth = 2; g.strokeRect(xx - 5, yy - 5, 10, 10); }
      else if (e[3] === 'forced' || e[3] === 'xforce' || e[3] === 'oforce') { g.strokeStyle = '#f43f5e'; g.lineWidth = 2.5; g.beginPath(); g.moveTo(xx - 5, yy - 5); g.lineTo(xx + 5, yy + 5); g.moveTo(xx + 5, yy - 5); g.lineTo(xx - 5, yy + 5); g.stroke(); }
      else if (e[3] === 'ttc' || e[3] === 'near') { g.strokeStyle = '#fb7185'; g.lineWidth = 2; g.beginPath(); g.arc(xx, yy, 6, 0, 7); g.stroke(); }
      else if (e[3] === 'hard') { g.fillStyle = '#fbbf24'; g.beginPath(); g.moveTo(xx - 4, yy - 9); g.lineTo(xx + 4, yy - 9); g.lineTo(xx, yy - 3); g.fill(); }
      g.globalAlpha = 1; });
    var by = top + (n + 2.6) * LH + 8, bh = H - by - 16, mx = 1;
    [0, 1].forEach(function (j) { var b = CUR.res[j].m.bins; Object.keys(b).forEach(function (q) { mx = Math.max(mx, b[q]); }); });
    g.fillStyle = '#9ca3af'; g.font = '10px sans-serif'; g.fillText('위험 사건이 몰린 곳(25m)', 8, by - 2);
    [0, 1].forEach(function (j) { var b = CUR.res[j].m.bins; g.fillStyle = j ? '#60a5fa' : '#9ca3af';
      Object.keys(b).forEach(function (q) { var x0 = +q; if (x0 < xa || x0 > xb) return; var hh = b[q] / mx * bh; g.fillRect(X(x0) + (j ? sx * 12.5 : 1), by + bh - hh, Math.max(1, sx * 11.5), hh); }); });
    var te = $('m2dMrgT'); if (te) te.textContent = (CUR.view ? '바꾼 안' : '현행') + ' · ' + Math.floor(t / 60) + ':' + ('0' + Math.floor(t % 60)).slice(-2) + ' / 10:00 · 차 ' + (f.length / 4);
  }

  var NSEED = 3;   /* 같은 조건을 차 세 벌로 돌려 평균 — 한 번은 우연이 크다 */
  function avg(rs) {
    var m = {}, k0 = rs[0].m; Object.keys(k0).forEach(function (k) { if (typeof k0[k] === 'number') m[k] = rs.reduce(function (s, r) { return s + r.m[k]; }, 0) / rs.length; });
    m.bins = {}; m.binsK = {}; rs.forEach(function (r) { Object.keys(r.m.bins).forEach(function (b) { m.bins[b] = (m.bins[b] || 0) + r.m.bins[b] / rs.length; }); Object.keys(r.m.binsK).forEach(function (b) { var o = m.binsK[b] = m.binsK[b] || {}; Object.keys(r.m.binsK[b]).forEach(function (q) { o[q] = (o[q] || 0) + r.m.binsK[b][q] / rs.length; }); }); });
    return { cfg: rs[0].cfg, xE: rs[0].xE, frames: rs[0].frames, ev: rs[0].ev, obs: rs[0].obs, warm: rs[0].warm, m: m };
  }
  function runBoth(prog, done) {
    var a = JSON.parse(JSON.stringify(CUR.cfg)), b = JSON.parse(JSON.stringify(CUR.cfg)), ch = chgList().filter(function (x) { return x[0] === CUR.chg; })[0] || CHG[0], RA = [], RB = [], i = 0, my = CUR;
    ch[2](b);
    (function next() {
      if (CUR !== my) return;
      if (i >= NSEED * 2) { CUR.res = [avg(RA), avg(RB)]; CUR.res.ch = ch; return done(); }
      var sd = CUR.seed + Math.floor(i / 2) * 101, r = run(JSON.parse(JSON.stringify(i % 2 ? b : a)), sd); (i % 2 ? RB : RA).push(r); i++;
      prog(i, NSEED * 2); setTimeout(next, 0);
    })();
  }
  function onInput(e) {
    var k = e.target.getAttribute('data-mc'); if (!k || !CUR) return;
    if (k === 'chg') { CUR.chg = e.target.value; return; }
    if (k.indexOf('ev.') === 0) { var f = k.slice(3), val = e.target.value;
      if (f === 'kind') { CUR.cfg.ev = val ? evDef(val, CUR.cfg) : null; CUR.chg = val ? 'noev' : (CUR.m.dn && CUR.m.dn[0] < 600 ? 'noexit' : 'la'); CUR.res = null; paint(); return; }
      CUR.cfg.ev[f] = f === 'when' ? val : +val;
      if (f === 'x' || f === 'len') { var o9 = $('m2dMrgV_ev_' + f); if (o9) o9.textContent = f === 'len' ? val + 'm' : (+val < 0 ? '합류점 앞 ' + (-val) + 'm' : '합류점 뒤 ' + val + 'm'); return; }
      if (e.type === 'change') paint(); return; }
    if (k === 'add') { CUR.cfg.add = e.target.checked; CUR.res = null; paint(); return; }
    var v = +e.target.value; CUR.cfg[k] = v; var o = $('m2dMrgV_' + k), s = SL.filter(function (x) { return x[0] === k; })[0]; if (o) o.textContent = fmt(k, v) + s[5];
  }
  function onClick(e) {
    var t = e.target.closest('[data-mg]'); if (!t) return; var k = t.getAttribute('data-mg');
    if (k === 'x') return close();
    if (k.indexOf('pk:') === 0) { var r = LST[+k.slice(3)]; if (r) openM(r.m); return; }
    if (k === 'run' || k === 'seed') { if (k === 'seed') CUR.seed = (CUR.seed * 7919 + 13) % 99991 || 3; t.disabled = true; t.textContent = '돌리는 중…'; stopAnim(); setTimeout(function () { runBoth(function (j, nn) { t.textContent = '돌리는 중… ' + j + '/' + nn; }, function () { paint(); var r = $('m2dMrgRes'); if (r && r.scrollIntoView) r.scrollIntoView({ block: 'start', behavior: 'smooth' }); }); }, 30); return; }
    if (k === 'v0' || k === 'v1') { CUR.view = +k.slice(1); if (ANIM) ANIM.k = 0; Array.prototype.forEach.call(PANEL.querySelectorAll('[data-mg=v0],[data-mg=v1]'), function (b) { b.classList.toggle('on', b.getAttribute('data-mg') === k); }); return; }
    if (k === 'pp' && ANIM) { ANIM.play = !ANIM.play; return; }
  }

  /* ---- 고르기: 지도 가운데 둘레 합류부 목록 · 카드 단추 ---- */
  var LST = [];
  function viewLL() { var T = window.TGMap2D; if (!T || !T.view || !T.P) return null; var v = T.view, W = window.innerWidth, H = window.innerHeight; var a = T.P(127, 37.5), b = T.P(127.01, 37.5), c = T.P(127, 37.51);
    var mx = v.cx != null ? v.cx : null; if (mx == null) return null; return [37.5 + (v.cy - a[1]) / (c[1] - a[1]) * 0.01, 127 + (v.cx - a[0]) / (b[0] - a[0]) * 0.01]; }
  function list() {
    var Pn = panel(); stopAnim(); Pn.innerHTML = head('합류부 고르기 — IC·합류 사고 원인 시뮬') + '<div class="sn">자료 받는 중…</div>';
    mrgGet().then(function () {
      var c = viewLL() || [37.4919, 127.0076]; LST = near(c, 4000).slice(0, 18);
      if (!LST.length) LST = MRG.items.map(function (m) { return { m: m, d: dist(c, [m.lat, m.lon]) }; }).sort(function (a, b) { return a.d - b.d; }).slice(0, 18);
      return Promise.all(LST.map(function (o) { return taasFor(o.m).then(function (t) { o.t = t; }); }));
    }).then(function () {
      LST.sort(function (a, b) { return ((b.t && b.t.tot) || 0) - ((a.t && a.t.tot) || 0); });
      var h = head('합류부 고르기 — IC·합류 사고 원인 시뮬') + '<div class="sn">지도 가운데 4km 안 합류부(연결로가 본선에 붙는 곳 · 여섯 구 표준노드링크 ' + MRG.items.length + '곳 중) — 실제 사고가 많은 차례 · <b>개념 시연</b></div>';
      h += '<table><tr><th>합류부</th><th>본선 · 차로</th><th class="n">사고 10년(150m)</th><th class="n">거리</th></tr>' + LST.map(function (o, i) { var m = o.m, t = o.t;
        return '<tr><td><button data-mg="pk:' + i + '" style="min-height:30px;padding:2px 8px">' + esc(m.nm || m.main) + '</button><br><small>' + esc(m.ramp[0]) + ' → ' + esc(m.main) + '</small></td><td>' + esc(m.main) + ' ' + m.inL + '+' + m.ramp[1] + '→' + m.outL + (m.dn && m.dn[0] < 600 ? ' <span class="b d">엮임 ' + m.dn[0] + 'm</span>' : '') + '</td><td class="n">' + (t ? t.tot.toLocaleString() + (t.dead ? ' <small>사망 ' + t.dead + '</small>' : '') : '—') + '</td><td class="n">' + (o.d / 1000).toFixed(1) + 'km</td></tr>'; }).join('') + '</table>';
      h += '<div class="sn">사고 수는 합류점 150m 안 100m 칸 합(고가 아래 일반도로 사고가 섞일 수 있다) · 지도에서 합류부 근처를 누르면 카드에도 「🔀 이 합류부 시뮬」 단추가 생긴다</div>';
      PANEL.innerHTML = h;
    }).catch(function (er) { PANEL.innerHTML = head('합류부 고르기') + '<div class="warn">' + esc(er && er.message || er) + '</div>'; });
  }
  function cardHook() {
    var c = $('m2dCard'); if (!c || !window.MutationObserver) return;
    new MutationObserver(function () {
      if (!c.classList.contains('on') || c.querySelector('[data-mrgpick]')) return;
      var ll = window.tgSimPick && window.tgSimPick.tapLL ? window.tgSimPick.tapLL() : null; if (!ll) return;
      mrgGet().then(function () {
        if (!c.classList.contains('on') || c.querySelector('[data-mrgpick]')) return;
        var o = near(ll, 200)[0]; if (!o) return;
        var bx = c.querySelector('.lg-btns') || c.querySelector('.dhb') || c, b = document.createElement('button'); b.setAttribute('data-mrgpick', o.m.id);
        b.title = '이 합류부를 차 한 대씩 움직여 억지 끼어들기·아슬아슬·급제동이 어디서 나는지 본다 · 개념 시연';
        b.textContent = '🔀 이 합류부 시뮬 — ' + (o.m.nm || o.m.main); b.style.cssText = 'background:#1d4ed8;color:#fff;border-color:#1d4ed8';
        b.onclick = function (e) { e.stopPropagation(); openM(o.m); };
        if (bx === c) c.appendChild(b); else bx.appendChild(b);
      }).catch(function () {});
    }).observe(c, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  }
  window.tgSimMerge = { run: run, list: list, open: openM, close: close, load: mrgGet, near: function (lat, lon, R) { return near([lat, lon], R || 200); }, taas: taasFor, cfgOf: cfgOf, CHG: CHG, P: P };
  function boot() { cardHook(); document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && PANEL && PANEL.classList.contains('on')) close(); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
