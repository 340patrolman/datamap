// 시뮬레이션 쓸 만한가 — 날 6갈래 × 조치(없음·하나씩) × 개선안(현행·A~E) 을 섞어 돌려 오류·차 보존·숫자 이상을 본다(tools/sim/sim-check.py sweep)
(function () {
  var M = window.__M, S = window.tgSim, out = [], bad = 0, n = 0, worst = 0;
  var DAYS = ['2026-10-18', '2026-10-11', '2026-10-21', '2026-10-23', '2026-10-24', '2026-10-25'];
  var ACTS = [[]].concat((M.actions || []).map(function (a) { return [a.id]; }));
  var cur = function (date) { return S.planAt(M, '4031', 17 * 3600, S.dowOf(date)).ph.map(function (p) { return { d: p.d, y: p.y, ar: p.ar, mv: p.mv.slice() }; }); };
  var EX = [{ d: 40, y: 4, ar: 1, mv: ['wt.St', 'et.St'] }, { d: 30, y: 4, ar: 1, mv: ['et.St', 'wt.Lt'] }, { d: 45, y: 3, ar: 1, mv: ['nt.St', 'st.St'] }, { d: 30, y: 3, ar: 1, mv: ['nt.Lt'] }, { d: 35, y: 3, ar: 1, mv: ['st.Lt'] }];
  function plansFor(date) { var c = cur(date), K = function (f) { var q = JSON.parse(JSON.stringify(c)); f(q); return q; };
    return { cur: null, A: EX, C: K(function (q) { q[1].d -= 15; q[3].d += 15; }), D: K(function (q) { q[2].d -= 10; q[0].d += 10; }), E: K(function (q) { q.forEach(function (x) { x.d = Math.round(x.d * 1.2); }); }) }; }
  function one(date, act, pid, ph) {
    n++; var t0 = performance.now(), msg = date + ' ' + (act.join('+') || '조치 없음') + ' ' + pid;
    try {
      var off = S.planAt(M, '4031', 17 * 3600, S.dowOf(date)).off, X = S.run(M, { date: date, seed: 7, act: act, from: 16 * 3600, to: 23 * 3600 }, ph ? { '4031': { ph: ph, off: off } } : null), R = X.result(), ms = performance.now() - t0;
      worst = Math.max(worst, ms);
      var ok = X.V.length === X.done + X.inNet() && X.log.length === 0 && isFinite(R.delayVh) && R.delayVh >= 0 && R.trappedMax >= 0;
      Object.keys(X.A).forEach(function (k) { var o = X.A[k].occ; if (o != null && (o < 0 || o > X.A[k].a.capacity + 0)) ok = false; });
      if (!ok) { bad++; out.push('❌ ' + msg + ' — 보존 ' + X.V.length + '/' + (X.done + X.inNet()) + ' log ' + X.log.slice(0, 2).join('/')); }
      return R;
    } catch (e) { bad++; out.push('❌ ' + msg + ' — 예외 ' + String(e && e.stack || e).slice(0, 200)); return null; }
  }
  var tbl = [];
  DAYS.forEach(function (date) { var P = plansFor(date);
    ACTS.forEach(function (act) { ['cur', 'A'].forEach(function (pid) { one(date, act, pid, P[pid]); }); });
    var row = [date]; Object.keys(P).forEach(function (pid) { var R = one(date, [], pid, P[pid]); row.push(pid + ' ' + (R ? R.delayVh + '/' + R.trappedMax + '/' + (R.jamStart != null ? Math.round(R.jamStart / 360) / 10 + '→' + (R.clearT ? Math.round(R.clearT / 360) / 10 : '23↑') : '-') : 'ERR')); }); tbl.push(row.join(' · '));
  });
  // 수동 조작 — 들어오는 차만 끊기(재편안 A 의 출구 연장 현시로 지정) 뒤 1시간
  try { var Y = S.create(M, { date: '2026-10-18', seed: 7 }, { '4031': { ph: EX, off: 170 } }); Y.runTo(17 * 3600); Y.manual('4031', true); Y.go('4031', 1); Y.runTo(17 * 3600 + 3600); var g = Y.N['4031'].manual; n++;
    if (!(g.i === 1 && Y.V.length === Y.done + Y.inNet())) { bad++; out.push('❌ 수동 들어오는 차만 끊기 — 현시 ' + g.i); } } catch (e) { bad++; out.push('❌ 수동 예외 ' + e); }
  out.unshift((bad ? '❌ ' : '✅ ') + '섞어 돌림 ' + n + '판 · 실패 ' + bad + ' · 가장 오래 걸린 판 ' + Math.round(worst) + 'ms(PC)');
  out.push('날마다 안별 결과(총 지체 대·시 / 블록 갇힘 최대 / 막힘 시작→해소 시각):'); tbl.forEach(function (r) { out.push('  ' + r); });
  out.push(bad ? '❌ 실패 ' + bad : 'ALL_OK');
  document.getElementById('out').textContent = out.join('\n');
})();
