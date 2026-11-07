/* 🔮 30분 뒤 막힘 어림(실측 어림 · 2026-11-07 · 소유자 「도로 위 점선 표시」)
   · 지금 ITS 속도(🚦 소통 층이 받은 값) · 30분 앞 받은 값(이 화면을 열어 둔 동안 이 폰이 기억 · 없으면 추세 없이) · 이 길 평소 막힘 비율(같은 날 종류 · 15분 칸) · 시각
     → 로지스틱 회귀(data/nowcast.json · tools/sim/nowcast.py --bake 가 쌓인 ITS 실측으로 배움) · 막힘 = 6km/h 이하
   · 지금 막히지 않았는데 30분 뒤 막힐 듯한 길만 보라 점선 · 밤 0~6시는 「그대로」가 더 잘 맞아 안 그린다(gate)
   · 성적 = data/nowcast-score.json(홀수 날 배움 · 짝수 날 판정 · 그대로와 견줌) · 개념 시연 — 예측·보증 아님 · 서버·통신 없음(공개 파일 둘만 읽는다 · 받은 속도는 폰 메모리에만) */
(function () {
  var NC = null, SC = null, LD = null, HIS = [], CB = [];
  function load(cb) {
    if (cb) CB.push(cb);
    if (LD) return LD;
    LD = Promise.all([fetch('data/nowcast.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }), fetch('data/nowcast-score.json').then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })])
      .then(function (a) { NC = a[0]; SC = a[1]; CB.splice(0).forEach(function (f) { try { f(); } catch (e) {} }); }).catch(function () { NC = false; });
    return LD;
  }
  function feed(sp) {   /* 받은 소통을 시각째 기억(50분까지) — 30분 앞 값을 찾으려고 */
    if (!sp || !sp.m || sp.busy || sp.err) return;
    if (HIS.length && HIS[HIS.length - 1].at === sp.at) return;
    HIS.push({ at: sp.at, m: sp.m });
    while (HIS.length && sp.at - HIS[0].at > 50 * 60000) HIS.shift();
  }
  function past(id, at) {   /* 25~35분 앞(배울 때와 같은 8분 너비 근처) 가장 30분에 가까운 값 */
    var best = null;
    HIS.forEach(function (s) { var dt = at - s.at; if (dt >= 22 * 60000 && dt <= 38 * 60000 && s.m[id] && (!best || Math.abs(dt - 1800000) < Math.abs(at - best.at - 1800000))) best = s; });
    return best ? +best.m[id][0] : null;
  }
  function wkOf(d, hol) { var k = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); return d.getDay() === 0 || d.getDay() === 6 || (hol && hol[k]) ? 1 : 0; }
  function hist(id, wk, b) {
    var L = NC.links[id]; if (!L || b < 0 || b > 95) return NC.dflt[wk];
    var i = NC.AL.indexOf(L[1 + wk].charAt(b)), lg = i / 61 * 10 - 5; return 1 / (1 + Math.exp(-lg));
  }
  function lg(p) { return Math.log(p / (1 - p)); }
  function inGate(hr) { return (NC.gate || []).some(function (g) { return hr >= g[0] && hr < g[1]; }); }
  /* 한 길의 어림 — { p 막힐 확률(모형 값), jam 막힘 어림, j0 지금 막힘 } 또는 null(밤 · 자료 없음) */
  function prob(id, v0, at, hol, noPast) {   /* noPast = 30분 앞 값을 안 씀(관문 시험) */
    if (!NC || v0 == null || !isFinite(v0)) return null;
    var d = new Date(at), sec = d.getHours() * 3600 + d.getMinutes() * 60 + d.getSeconds(), hr = sec / 3600;
    if (inGate(Math.floor(hr)) || sec + 1800 >= 86400) return null;
    var L = NC.links[id], vf = L ? L[0] : (NC.vf0[id] || 50), wk = wkOf(d, hol), vp = noPast ? null : past(id, at), J = NC.jam;
    var hf = hist(id, wk, Math.floor((sec + 1800) / 900)), h0 = hist(id, wk, Math.floor(sec / 900)), vpp = vp == null ? v0 : vp;
    var x = [v0 <= J ? 1 : 0, Math.min(v0, 60) / 60, v0 / vf, (v0 - vpp) / vf, vp == null ? 0 : 1, lg(hf), lg(h0), lg(hf) - lg(h0), wk, Math.sin(2 * Math.PI * hr / 24), Math.cos(2 * Math.PI * hr / 24), 0.5, v0 <= 10 && v0 > J ? 1 : 0, v0 > J && v0 <= 15 ? 1 : 0];
    var z = NC.w[0]; for (var i = 0; i < x.length; i++) z += (x[i] - NC.mu[i]) / NC.sd[i] * NC.w[i + 1];
    var p = 1 / (1 + Math.exp(-z)); return { p: p, jam: p >= NC.th, j0: x[0] === 1, usual: hf, trend: vp != null };
  }
  /* 🚦 소통 층 위에 — 지금 안 막혔는데 30분 뒤 막힐 듯한 길만 보라 점선(소통 선과 같은 자리 · 같은 방향 오른쪽) */
  function draw(ctx, ITSL, sp, S, a, b, wd, hit, hol, redraw) {
    feed(sp); if (NC === null) { load(redraw); return; } if (!NC || !sp || !sp.m) return;
    var m = sp.m, off = wd * 0.8; ctx.save(); ctx.setLineDash([wd * 1.6, wd * 1.4]); ctx.lineWidth = Math.max(2, wd - 0.5); ctx.strokeStyle = '#7c3aed'; ctx.lineCap = 'butt';
    ITSL.forEach(function (L) { var v = m[L.id]; if (!v) return; var bb = L.bb; if (bb[2] < a[0] || bb[0] > b[0] || bb[3] < a[1] || bb[1] > b[1]) return;
      var r = prob(L.id, +v[0], sp.at, hol); if (!r || !r.jam || r.j0) return;
      var pt = L.pts.map(S), n = pt.length; ctx.beginPath();
      for (var i = 0; i < n; i++) { var p0 = pt[Math.max(0, i - 1)], p1 = pt[Math.min(n - 1, i + 1)], dx = p1[0] - p0[0], dy = p1[1] - p0[1], d = Math.hypot(dx, dy) || 1, ox = -dy / d * off, oy = dx / d * off;
        if (i) ctx.lineTo(pt[i][0] + ox, pt[i][1] + oy); else ctx.moveTo(pt[i][0] + ox, pt[i][1] + oy); }
      ctx.stroke(); });
    ctx.restore();
  }
  function card(id, v, at, hol) {   /* 소통 카드 한 줄 — 글(html) 또는 '' */
    if (!NC) return '';
    var r = prob(id, +v[0], at, hol); if (!r) return '<em>밤(0~6시)에는 어림을 안 낸다 — 지금 상태가 이어진다고 보는 쪽이 더 잘 맞았다</em>';
    return (r.jam ? '<b style="color:#7c3aed">막힐 듯</b>' : r.j0 ? '지금 막힘 — 풀릴 듯' : '안 막힐 듯') + ' · 모형 값 ' + Math.round(r.p * 100) + '% · 평소 이 시각 막힘 ' + Math.round(r.usual * 100) + '%' + (r.trend ? '' : ' · 30분 앞 값 없음(추세 빼고 셈)') + ' <em>(어림 — 예측·보증 아님)</em>';
  }
  function legend() {   /* 범례 한 줄 — 성적과 함께 */
    if (!NC) return NC === false ? '30분 뒤 어림 자료를 못 받았다' : '30분 뒤 어림 받는 중';
    var s = SC && SC.score && SC.score['30'], t = '';
    if (s) { var k = s.keep.n - s.keep.hit, w = s.now.n - s.now.hit; t = ' · 판정 날(짝수 날) 30분 뒤 틀린 칸이 「지금 그대로」보다 ' + Math.round(100 * (1 - w / k)) + '% 적음 · 헛막힘 ' + s.keep.fa.toLocaleString() + '→' + s.now.fa.toLocaleString(); }
    return '보라 점선 = 지금은 아니지만 30분 뒤 막힐 듯(6km/h 이하) · 밤 0~6시 안 그림 · 이 길 평소 막힘·지금 속도·30분 추세로 어림(ITS 실측 ' + NC.n_days + '일로 배움 · ' + NC.days[0] + '~' + NC.days[1] + ')' + t + ' · 개념 시연 — 예측·보증 아님';
  }
  window.tgNowcast = { load: load, prob: prob, draw: draw, card: card, legend: legend, feed: feed, ready: function () { return !!NC; } };
})();
