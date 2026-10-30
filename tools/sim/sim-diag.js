// 재현 맞대 보기(검사가 아니라 보고) — tools/sim/sim-check.py diag 가 돌린다
//   실측 = ITS 소통 속도(07_API키/out/livespd · 블록 교차로로 들어오는 첫 링크 · 시간 평균 km/h · 2026-10-25 scratchpad spd_block.py 로 뽑음) — 5km/h 이하 = 막힘
//   시뮬 = 그 접근로 길 점유(대수 ÷ 길이×차로÷차 한 대 길이) 80% 이상 = 막힘
(function () {
  var M = window.__M, S = window.tgSim, out = [];
  var REAL = window.__REAL = { '2026-10-18': { '4019.et': [2, 3, 3, 3, 2, 7, 13], '4019.nt': [2, 2, 2, 2, 2, 6, 10], '4019.st': [5, 9, 10, 8, 10, 10, 13], '4028.et': [2, 2, 2, 2, 1, 2, 9], '4028.wt': [5, 6, 6, 4, 5, 6, 18], '4031.nt': [4, 5, 4, 4, 3, 9, 15], '4031.st': [9, 9, 8, 5, 6, 6, 16], '4031.wt': [4, 3, 2, 3, 7, 15, 23], '4034.et': [3, 3, 4, 3, 1, 6, 9], '4034.nt': [11, 6, 7, 8, 17, 25, 32], '4034.wt': [7, 5, 3, 5, 12, 18, 17] },
    '2026-10-11': { '4019.et': [6, 6, 6, 8, 10, 11, 12], '4019.nt': [6, 8, 4, 9, 11, 14, 9], '4019.st': [9, 12, 8, 10, 13, 15, 14], '4028.et': [12, 10, 11, 13, 18, 19, 19], '4028.wt': [10, 9, 8, 14, 14, 19, 13], '4031.nt': [13, 11, 11, 13, 15, 18, 17], '4031.st': [9, 9, 8, 7, 12, 20, 25], '4031.wt': [21, 18, 18, 17, 25, 19, 25], '4034.et': [10, 11, 12, 9, 16, 19, 18], '4034.nt': [14, 20, 17, 12, 18, 24, 22], '4034.wt': [18, 12, 18, 13, 17, 16, 16] } };
  var K = Object.keys(REAL['2026-10-18']);
  function occH(A, a, h) { var nd = a.split('.')[0], lg = a.split('.')[1], I = M.nodes[nd].legs[lg].in, SL = S.side ? S.side(M, I) : [I], L = A.samp.filter(function (s) { return s.t >= h * 3600 && s.t < (h + 1) * 3600; }); if (S.sideOcc) return L.length ? L.reduce(function (x, s) { return x + S.sideOcc(A, s, SL); }, 0) / L.length : 0; return L.length ? L.reduce(function (x, s) { return x + s.occ[I]; }, 0) / L.length / A.L[I].cap : 0; }
  function hh(t) { if (t == null) return '-'; var h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60); return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m; }
  window.__cmp = function (pk, alt) {
    var P = M.preset[pk], A = S.run(M, { date: P.date, seed: 7, att: P.att, to: 23 * 3600 }, alt || null), R = A.result(), RL = REAL[P.date], c = { hit: 0, n: 0, tp: 0, fp: 0, fn: 0, rows: [] };
    K.forEach(function (a) { var row = a + ' '; for (var h = 16; h <= 22; h++) { var sj = occH(A, a, h) >= 0.8, rj = RL[a][h - 16] <= 5; c.n++; if (sj === rj) c.hit++; if (sj && rj) c.tp++; if (sj && !rj) c.fp++; if (!sj && rj) c.fn++; row += (rj ? '■' : '·') + (sj ? '■' : '·') + ' '; } c.rows.push(row); });
    c.R = R; c.nm = P.nm; return c;
  };
  if (window.__DIAG) {
    ['1018', '1011'].forEach(function (pk) {
      var c = __cmp(pk), R = c.R;
      out.push('=== ' + c.nm + ' · 막힘 시작 ' + hh(R.jamStart) + ' · 해소 ' + hh(R.clearT) + ' · 지체 ' + R.delayVh + ' 대·시 · 꼬리물기 ' + R.box + ' · 블록 갇힘 최대 ' + R.trappedMax);
      out.push('  접근로   16 17 18 19 20 21 22시   (칸마다 앞 = 실측 ≤5km/h · 뒤 = 시뮬 점유 ≥80%)');
      c.rows.forEach(function (r) { out.push('  ' + r); });
      out.push('  맞음 ' + c.hit + '/' + c.n + ' · 둘 다 막힘 ' + c.tp + ' · 시뮬만 ' + c.fp + ' · 실측만 ' + c.fn);
    });
    out.push('ALL_OK'); document.getElementById('out').textContent = out.join('\n');
  }
})();
