/* 선착 역 계산(SREACH · 가르고 안 음성 받아쓰기 SR 과 겹치지 않게) — 열차 안 신고: 열차보다 먼저 닿을 수 있는 역 · 그 확률 · 언제까지 떠나야 하나 — 우리 판 ver.2.1(2026-10-15 · 독립 검수 지적 고침)
   소유자가 붙인 「도착 예측 ver.1」 프롬프트의 규격을 따른다(받기로 한 subway_intercept.js 가 이 PC 에 없어 직접 짰다 — 오면 같은 입력으로 맞대 본다).
   자료 = data/train-run-seoul.json(tools/region/trainrun-bake.py) · 계산은 모두 기기 안에서(이 파일은 바깥에 아무것도 부르지 않는다).
   결과는 「후보」·「예상」이다 — 최종 판단은 현장 경찰관. 가정값은 assumed:true 로 돌려주고 화면은 「가정값」 배지를 붙인다(실측 3번 이상 들어온 역만 뗀다).

   SREACH.load(json)                                 자료 넣기
   SREACH.find(이름, 노선)                            역 번호 · SREACH.lineOf(표기) = 승하차 자료 표기(경부선 등) → 노선(1호선 등)
   SREACH.path(역, 다음 역, n)                        진행 방향으로 n 역 [{i, sec(출발 → 그 역 출발 누적), branch(갈라진 뒤면 true)}]
   SREACH.crowd(역, 시, events, 날짜)                 {r 몫, walkF 도보 배수, dwellF 정차 배수, sdF, warn, assumed}
   SREACH.train(obs, 시, events, 날짜, n)              obs = {i 마지막 역, nx 다음 역, st 'dep'(떠남)|'arr'(서 있음), ago 관측한 지 몇 초(관측 시각부터 지금까지 포함), unk 몇 초 전인지 모름}
   SREACH.police(역, drive{sec, sd}, 시, meas, events, 날짜, 출구) → {P, sd, walk{…, assumed, other}, park{…}}
   SREACH.pWin(muT, sdT, muP, sdP)                    해석 계산 P(경찰이 먼저) · SREACH.mc(…, n, seed) 몬테카를로
   SREACH.plan(obs, drives{역: {sec, sd}}, 시, opt)   후보 역 카드 + 권고(기준 넘는 가장 가까운 역 · 없으면 가장 높은 역 — 50% 이상이면 close「경합」 · 아래면 weak)
   SREACH.calibrate([[예상, 실제], …])                 주행 보정 배수 */
(function (root) {
  'use strict';
  /* 가정값 — 모두 assumed:true 로 나간다 · 실측(역 실측 도구 tg_gg_meas)이 들어오면 그 역의 도보·세운 자리 값만 바뀐다 */
  var A = { dwell: 30, walk: 90, park: 60, alpha: 0.35, beta: 0.5, walkMin: 0.9, walkMax: 1.8, dwellMax: 2.0, sdT0: 20, sdTk: 8, sdWalk: 20, sdPark: 15, target: 0.8, warnK: 1.35, nMeas: 3 };
  /* 승하차 자료(OA-12252) 노선 표기 → 시간표 자료 노선 — 역 실측 도구는 승하차 자료 표기로 남긴다 */
  var LN = { '경부선': '1호선', '경인선': '1호선', '경원선': '1호선', '장항선': '1호선', '분당선': '수인분당', '수인선': '수인분당', '경의선': '경의중앙', '중앙선': '경의중앙', '과천선': '4호선', '안산선': '4호선', '일산선': '3호선', '9호선2~3단계': '9호선', '공항철도 1호선': '공항', '우이신설선': '우이신설', '경춘선': '경춘', '경강선': '경강' };
  function lineOf(l) { return LN[l] || l; }
  var D = null, NX = null;
  function load(j) { D = j; NX = {}; (j.lk || []).forEach(function (l) { (NX[l[0]] || (NX[l[0]] = [])).push(l); }); return D; }
  function base(s) { return String(s || '').replace(/\(.*?\)/g, '').trim(); }
  function find(nm, ln) { if (!D) return -1; var i, b = base(nm), L = ln ? lineOf(ln) : null, alt = -1; for (i = 0; i < D.st.length; i++) { var s = D.st[i]; if (s[1] === nm && (!L || s[2] === L)) return i; if (alt < 0 && base(s[1]) === b && (!L || s[2] === L)) alt = i; } return alt; }
  function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  /* 진행 방향으로 따라가기 — 앞 역으로 되돌아가지 않고 · 역간거리와 맞은 이음(ok=1)을 먼저 · 갈래(2호선 지선 등)를 만나면 첫 갈래로 가되 그 뒤 역은 모두 branch */
  function path(i, nx, n) { var out = [], prev = i, cur = nx, seen = {}, br = false, l0 = (NX[i] || []).filter(function (l) { return l[1] === nx; })[0]; if (!l0) return out; seen[i] = 1;
    var acc = l0[2]; out.push({ i: nx, sec: acc, branch: false });
    while (out.length < (n || 6)) { seen[cur] = 1; var C = (NX[cur] || []).filter(function (l) { return l[1] !== prev && !seen[l[1]] && D.st[l[1]][2] === D.st[cur][2]; }); if (!C.length) break;
      var ok = C.filter(function (l) { return l[3] === 1; }); if (ok.length) C = ok; var l = C[0]; if (C.length > 1) br = true; acc += l[2]; out.push({ i: l[1], sec: acc, branch: br }); prev = cur; cur = l[1]; }
    return out; }
  function evAdd(i, h, events, ds) { var s = D.st[i], a = 0; (events || []).forEach(function (e) { if ((!e.date || e.date === ds) && (base(e.st) === base(s[1])) && h >= e.h0 && h < e.h1) a += +e.add || 0; }); return a; }
  /* 혼잡 — 그 역 그 시 승하차 몫 r(그 역 보통 = 1) + 행사 가산 → 도보 배수 1 + α(r−1)(0.9~1.8) · 정차 배수 1 + β(r−1)(1~2) · 오차도 도보 배수만큼 */
  function crowd(i, h, events, ds) { var s = D.st[i], R = s && s[5], r = R ? R[((h % 24) + 24) % 24] : 1, ev = evAdd(i, h, events, ds); r += ev;
    var wf = clamp(1 + A.alpha * (r - 1), A.walkMin, A.walkMax), df = clamp(1 + A.beta * (r - 1), 1, A.dwellMax);
    return { r: Math.round(r * 100) / 100, walkF: wf, dwellF: df, sdF: wf, warn: wf >= A.warnK, ev: ev, noData: !R, assumed: true }; }
  /* 열차 — 앞 역 출발 → 그 역 출발(정차 포함) 누적에서 그 역 정차를 빼 도착 · 사이 역들의 혼잡 정차 늘어남을 더함
     dep0 = 마지막 역을 떠나는(떠난) 때(지금 기준 초) — 떠남: −(지난 초) · 서 있음: 남은 정차(0 아래로 안 내려감)
     모름(unk): 관측 때 이미 지난 시간이 0 ~ 한 구간(떠남) 또는 0 ~ 정차(서 있음) 사이 어딘가 — 가운데로 셈하고 고른 분포의 분산을 더한다 */
  function train(o, h, events, ds, n) { var P = path(o.i, o.nx, n || 6); if (!P.length) return [];
    var c0 = crowd(o.i, h, events, ds), ago = Math.max(0, o.ago || 0), dw0 = A.dwell * c0.dwellF, run0 = Math.max(10, P[0].sec - A.dwell), dep0, vU = 0;
    if (o.st === 'arr') { var u = o.unk ? dw0 / 2 : 0; vU = o.unk ? dw0 * dw0 / 12 : 0; dep0 = Math.max(0, dw0 - u - ago); }
    else { var u2 = o.unk ? run0 / 2 : 0; vU = o.unk ? run0 * run0 / 12 : 0; dep0 = -(u2 + ago); }
    var extra = 0, out = [];
    P.forEach(function (p, k) { var c = crowd(p.i, h, events, ds), T = dep0 + p.sec - A.dwell + extra; extra += A.dwell * (c.dwellF - 1);
      var sd = Math.sqrt(A.sdT0 * A.sdT0 + (A.sdTk * (k + 1)) * (A.sdTk * (k + 1)) + vU); out.push({ i: p.i, k: k + 1, T: T, sd: sd, branch: p.branch, crowd: c, passed: o.st !== 'arr' && !o.unk && ago > run0 && k === 0 }); });
    return out; }
  /* 실측 — 역 실측 도구(tg_gg_meas)에서 그 역(이름 · 노선 표기 맞춤) · 그 종류 3번 이상 잰 조합 · 세울 출구와 같은 출구 먼저 · 없으면 다른 출구들 가운데값(other) */
  function measOf(meas, i, kind, exit) { var s = D.st[i], L = []; ((meas && meas.rec) || []).forEach(function (r) { if (r.kind !== kind || base(r.st) !== base(s[1]) || lineOf(r.ln) !== s[2] || !r.t || r.t.length < A.nMeas) return;
      var v = r.t.map(function (x) { return x[0]; }), m = v.reduce(function (a, b) { return a + b; }, 0) / v.length, sd = Math.sqrt(v.reduce(function (a, b) { return a + (b - m) * (b - m); }, 0) / (v.length - 1)), hm = r.t.reduce(function (a, x) { return a + x[1]; }, 0) / r.t.length;
      L.push({ m: m, sd: Math.max(5, sd), n: v.length, h: Math.round(hm), exit: r.exit }); });
    if (!L.length) return null; var same = L.filter(function (q) { return exit != null && String(q.exit) === String(exit); })[0]; if (same) return same;
    L.sort(function (a, b) { return a.m - b.m; }); var q = L[L.length >> 1]; return { m: q.m, sd: q.sd, n: q.n, h: q.h, exit: q.exit, other: exit != null }; }
  function police(i, drive, h, meas, events, ds, exit) { var c = crowd(i, h, events, ds), mw = measOf(meas, i, 'walk', exit), mp = measOf(meas, i, 'stop', exit), walk, park;
    if (mw) { var ch = crowd(i, mw.h, events, null); walk = { sec: mw.m * c.walkF / ch.walkF, sd: mw.sd * c.sdF / ch.sdF, assumed: false, n: mw.n, exit: mw.exit, other: !!mw.other }; } else walk = { sec: A.walk * c.walkF, sd: A.sdWalk * c.sdF, assumed: true };
    park = mp ? { sec: mp.m, sd: mp.sd, assumed: false, n: mp.n, exit: mp.exit, other: !!mp.other } : { sec: A.park, sd: A.sdPark, assumed: true };
    var dr = drive || { sec: NaN, sd: 0 }; return { P: dr.sec + park.sec + walk.sec, sd: Math.sqrt(dr.sd * dr.sd + park.sd * park.sd + walk.sd * walk.sd), drive: dr, walk: walk, park: park, crowd: c }; }
  /* 표준정규 누적 — Abramowitz·Stegun 7.1.26(오차 1.5e-7) */
  function Phi(z) { var t = 1 / (1 + 0.3275911 * Math.abs(z) / Math.SQRT2), y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-z * z / 2); return z >= 0 ? (1 + y) / 2 : (1 - y) / 2; }
  function pWin(muT, sdT, muP, sdP) { var s = Math.sqrt(sdT * sdT + sdP * sdP); return s > 0 ? Phi((muT - muP) / s) : (muT > muP ? 1 : 0); }
  function rng(seed) { var a = seed >>> 0 || 1; return function () { a ^= a << 13; a >>>= 0; a ^= a >> 17; a ^= a << 5; a >>>= 0; return a / 4294967296; }; }
  function mc(muT, sdT, muP, sdP, n, seed) { var R = rng(seed || 12345), w = 0, k; n = n || 20000; function g() { var u = R() || 1e-12, v = R(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
    for (k = 0; k < n; k++) if (muP + sdP * g() < muT + sdT * g()) w++; return w / n; }
  function zOf(p) { var lo = -6, hi = 6, k; for (k = 0; k < 60; k++) { var m = (lo + hi) / 2; if (Phi(m) < p) lo = m; else hi = m; } return (lo + hi) / 2; }
  function plan(o, drives, h, opt) { opt = opt || {}; var T = train(o, h, opt.events, opt.date, opt.n || 6), tg = opt.target || A.target, z = zOf(tg), EX = opt.exits || {};
    var C = T.map(function (t) { var p = police(t.i, drives && drives[t.i], h, opt.meas, opt.events, opt.date, EX[t.i]), pr = isFinite(p.P) ? pWin(t.T, t.sd, p.P, p.sd) : null, s = Math.sqrt(t.sd * t.sd + p.sd * p.sd), st = D.st[t.i];
      return { i: t.i, nm: st[1], ln: st[2], k: t.k, T: t.T, sdT: t.sd, P: p.P, sdP: p.sd, p: pr, slack: isFinite(p.P) ? t.T - p.P - z * s : null, late: isFinite(p.P) && t.T - p.P - z * s < 0, crowd: t.crowd, walk: p.walk, park: p.park, branch: t.branch, passed: t.passed, exits: st[7] || [], assumed: true }; });
    var ok = C.filter(function (c) { return c.p != null && c.p >= tg && !c.passed; }), best = ok[0] || null, close = false, weak = false;
    if (!best) { var q = C.filter(function (c) { return c.p != null && !c.passed; }).sort(function (a, b) { return b.p - a.p; })[0]; if (q) { best = q; close = q.p >= 0.5; weak = q.p < 0.5; } }
    return { cards: C, best: best ? best.i : null, close: close, weak: weak, target: tg, assumed: A }; }
  function calibrate(P) { var r = (P || []).filter(function (x) { return x[0] > 30 && x[1] > 30; }).map(function (x) { return x[1] / x[0]; }).filter(function (v) { return v > 0.4 && v < 2.5; }).sort(function (a, b) { return a - b; });
    if (!r.length) return { k: 1, n: 0, assumed: true }; return { k: clamp(r[r.length >> 1], 0.7, 1.5), n: r.length, assumed: r.length < 5 }; }
  root.SREACH = { A: A, LN: LN, lineOf: lineOf, load: load, data: function () { return D; }, find: find, path: path, crowd: crowd, train: train, police: police, measOf: measOf, pWin: pWin, mc: mc, Phi: Phi, plan: plan, calibrate: calibrate, VER: '2.1-tg' };
})(typeof window !== 'undefined' ? window : this);
