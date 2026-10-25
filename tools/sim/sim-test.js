// 반포 블록 시뮬레이터 엔진 검사 본문 — tools/sim/sim-check.py 가 머리 없는 크롬에서 돌린다
(function () {
  var M = window.__M, S = window.tgSim, out = [], bad = 0;
  function ck(name, ok, v) { out.push((ok ? '✅ ' : '❌ ') + name + (v != null ? ' — ' + (typeof v === 'string' ? v : JSON.stringify(v)) : '')); if (!ok) bad++; }
  try {
    // ① 4031 토 패턴 15 — 현시 길이와 순서
    var n = M.nodes['4031'], p15 = n.plan.pat['15'];
    ck('4031 토 패턴 15 = 주기 180 · 현시 49·43·48·40', p15.c === 180 && p15.a.join(',') === '49,43,48,40', p15);
    var P = S.planAt(M, '4031', 14 * 3600, 6);   // 토 14시 → 패턴 15
    ck('토 14시 계획 = 패턴 15', P.pat === '15', P.pat);
    var W = S.phasesToWin(P.ph), dir = n.plan.dir['15'], same = dir.every(function (r) { var w = W.win.filter(function (x) { return x[0] === r[0]; })[0]; return w && w[1] === r[1] && w[3] === r[3]; });
    ck('현시(49·43·48·40 · 황색·전적색) → 이동류 녹색 창이 현시도 dir 줄과 1초 단위로 같다(패턴 15)', same && W.c === 180, W.win.map(function (x) { return x[0] + ' ' + x[1] + '초@' + x[3]; }).join(' | '));
    ck('현시 순서 = 동서 양직진 → 서직좌 → 북직좌 → 남직좌', JSON.stringify(P.ph.map(function (q) { return q.mv.slice().sort(); })) === JSON.stringify([['et.St', 'wt.St'], ['wt.Lt', 'wt.St'], ['nt.Lt', 'nt.St'], ['st.Lt', 'st.St']]), P.ph.map(function (q) { return q.mv.join('+'); }).join(' → '));
    ck('서→동 직진이 1·2현시 두 번(끊기지 않고 87초)', dir.filter(function (r) { return r[0] === 'wt.St'; })[0][1] === 87);
    ['14', '7', '8', '3'].forEach(function (pt) { var pa = n.plan.pat[pt], w = S.phasesToWin(n.plan.ph.map(function (mv, i) { return { d: pa.a[i], y: n.plan.Y[i], ar: n.plan.AR[i], mv: mv }; })), ok = n.plan.dir[pt].every(function (r) { var x = w.win.filter(function (q) { return q[0] === r[0]; })[0]; return x && x[1] === r[1] && x[3] === r[3]; }); ck('4031 패턴 ' + pt + ' 녹색 창 = dir 줄', ok); });
    ['4028', '4034'].forEach(function (id) { var nd = M.nodes[id], P2 = S.planAt(M, id, 17 * 3600, 0); ck(id + ' 일 17시 계획 패턴 ' + P2.pat + ' 주기 ' + P2.c, P2.c > 0 && P2.win.length >= 4); });
    // 1초 단위 녹색 — 시뮬 안에서 4031 서→동 직진 녹색 초를 한 주기 센다(출발 손실 2초 · 황색 마지막 1초 뺀 유효 녹색)
    var Z = S.create(M, { date: '2026-10-24', from: 14 * 3600, to: 14 * 3600 + 400, att: { shin: { off: 1 }, fount: { off: 1 } } });
    // ② 일요일 10/18 16~22시 — 차 보존 · 걸린 시간
    var t0 = performance.now(), A = S.run(M, { date: '2026-10-18', seed: 7 }), ms = Math.round(performance.now() - t0);
    var inNet = A.inNet();
    var R = A.result();
    ck('길을 못 찾은 차 0', A.log.length === 0, A.log.slice(0, 3));
    var heldF = A.A.fount.held, mkF = A.V.filter(function (v) { return v.k === 'bg' && v.p[0] === '4032>4031' && v.t0 >= 21 * 3600; }).length;
    ck('차 보존 — 만든 차 = 끝난 차 + 망 안·망 밖·출차 대기', A.V.length === A.done + inNet, { made: A.V.length, done: A.done, inNet: inNet, 공원에남음: heldF });
    ck('16~22시 한 판 계산 시간(PC)', ms < 8000, ms + 'ms');
    ck('결과 지표 — 총 지체·최대 대기·블록 갇힘·막힘 시작·해소', R.delayVh >= 0 && R.peak > 0 && R.maxQm['4031.wt'] >= 0, { 지체_대시: R.delayVh, 막힘시작: hh(R.jamStart), 해소: hh(R.clearT), 막힌접근로최대: R.jamMax, 블록갇힘최대: R.trappedMax, 꼬리물기: R.box });
    out.push('   시간별(1시간마다) 대기 합 · 망 밖 · 신세계 문 앞 · 블록 출차 대기 · 공원 앞:');
    A.samp.filter(function (s) { return s.t % 1800 === 0; }).forEach(function (s) { out.push('   ' + hh(s.t) + '  대기 ' + s.q + ' · 망밖 ' + s.back + ' · 문앞 ' + s.att.shin.door + ' · 출차대기 ' + s.att.shin.out + ' · 공원앞 ' + s.att.fount.door + ' · 4031[' + ['wt', 'nt', 'st', 'et'].map(function (l) { return l + ' ' + (s.ap['4031.' + l] || 0); }).join(' ') + ']'); });
    // ③ 평시(신세계·분수 끔) 대비 — 수요를 넣으면 대기가 커져야 한다
    var B = S.run(M, { date: '2026-10-18', seed: 7, att: { shin: { off: 1 }, fount: { off: 1 } } }).result();
    ck('신세계·분수를 끄면 정점 대기가 작다(넘침이 수요에서 온다)', B.peak < R.peak, { 평시정점: B.peak, 둘다정점: R.peak });
    // ⑤ 재현 — 설계값 막대(신세계·분수)만 맞춘 설정 · 실측 속도와 맞대 본 결과
    var c18 = __cmp('1018'), c11 = __cmp('1011');
    ck('10/18 설정 — 블록 둘레 접근로가 막혔다가(3곳 넘게) 20:30~22:30 사이에 풀린다(실측 해소 21~22시대)', c18.R.jamStart != null && c18.R.clearT != null && c18.R.clearT >= 20.5 * 3600 && c18.R.clearT <= 22.5 * 3600, { 막힘시작: hh(c18.R.jamStart), 해소: hh(c18.R.clearT), 최대: c18.R.jamMax });
    ck('10/11 설정(평소 일요일) — 막히지 않는다(3곳 넘게 막힌 때 없음)', c11.R.jamStart == null, { 최대: c11.R.jamMax });
    ck('실측과 맞대 봄(접근로 11 × 16~22시) — 10/18 맞음 60% 넘게 · 10/11 맞음 90% 넘게', c18.hit / c18.n > 0.6 && c11.hit / c11.n > 0.9, '10/18 ' + c18.hit + '/' + c18.n + ' (둘 다 막힘 ' + c18.tp + ' · 시뮬만 ' + c18.fp + ' · 실측만 ' + c18.fn + ') · 10/11 ' + c11.hit + '/' + c11.n);
    // ④ 같은 씨앗이면 같은 차
    var C1 = S.run(M, { date: '2026-10-18', seed: 9, to: 17 * 3600 }), C2 = S.run(M, { date: '2026-10-18', seed: 9, to: 17 * 3600 }, { '4031': { ph: P.ph } });
    var nA = function (X) { return X.V.filter(function (v) { return v.k !== 'ao' && v.k !== 'fo'; }); }, c1 = nA(C1), c2 = nA(C2);
    ck('두 판이 같은 차를 쓴다(들어오는 차 수·첫 100대 길 · 주차장에서 나오는 차는 판마다 달라도 됨 — 들어간 때가 다르니까)', c1.length === c2.length && c1.slice(0, 100).every(function (v, i) { return v.p.join() === c2[i].p.join(); }), c1.length + ' / ' + c2.length);
    // 23시까지 끝까지 돌려도 배경 차가 같다(공원에서 나오는 차가 판마다 다른 때 나와도 배경 차 길이 흔들리지 않는다 — 독립 검수 지적)
    var F1 = S.run(M, { date: '2026-10-18', seed: 11, to: 23 * 3600 }), F2 = S.run(M, { date: '2026-10-18', seed: 11, to: 23 * 3600 }, { '4031': { ph: P.ph.map(function (q, i) { return { d: q.d + (i === 1 ? -15 : i === 3 ? 15 : 0), y: q.y, ar: q.ar, mv: q.mv }; }), off: 170, t0: 16 * 3600, t1: 21 * 3600 } }), bgA = F1.V.filter(function (v) { return v.k === 'bg'; }), bgB = F2.V.filter(function (v) { return v.k === 'bg'; });
    ck('끝까지(23시) 두 판의 배경 차 수·마지막 100대 길이 같다', bgA.length === bgB.length && bgA.slice(-100).every(function (v, i) { return v.p.join() === bgB[bgB.length - 100 + i].p.join(); }), bgA.length + ' / ' + bgB.length);
    var occMax = 0; [F1, F2].forEach(function (X) { X.samp.forEach(function (s9) { var a9 = s9.att.shin; if (a9 && a9.occ > occMax) occMax = a9.occ; }); });
    ck('주차장 자리를 넘지 않는다(2,435면 · 문 넷이 한 초에 함께 받아도)', occMax <= 2435, occMax);
    // 수동 조작 — 넘기기·지정
    var D = S.create(M, { date: '2026-10-18', from: 17 * 3600, to: 17 * 3600 + 600 }); D.runTo(17 * 3600 + 30); D.manual('4031', true); var i0 = D.N['4031'].manual.i; D.go('4031'); D.runTo(17 * 3600 + 60); var i1 = D.N['4031'].manual.i; D.go('4031', 2); D.runTo(17 * 3600 + 90);
    ck('수동 — 넘기기 뒤 다음 현시 · 지정하면 그 현시(황색·전적색 지난 뒤)', i1 === (i0 + 1) % 4 && D.N['4031'].manual.i === 2, [i0, i1, D.N['4031'].manual.i]);
    // ⑦ 게임 현장 사례 — 4034 시차제(현시도 tw) · 학원·고속버스 수요 · 라바콘 원거리 차로 축소
    var Pw = S.planAt(M, '4034', 17 * 3600, 3), Pn = S.planAt(M, '4034', 17 * 3600, 3, null, true), wS = Pw.win.filter(function (r) { return r[0] === 'wt.St'; })[0], nS = Pn.win.filter(function (r) { return r[0] === 'wt.St'; })[0], Pu = S.planAt(M, '4034', 17 * 3600, 0);
    ck('4034 시차제 — 평일 17시 서→동 직진 녹색 19초(황색 포함 23초 · 현시도 tw) · 끄면 원래 값 · 일요일은 안 걸림', wS[1] === 19 && nS[1] !== 19 && Pu.win.filter(function (r) { return r[0] === 'wt.St'; })[0][4] !== 'tw', { 평일: wS[1], 끄면: nS[1] });
    var wd = { date: '2026-10-21', seed: 4, from: 15 * 3600, to: 20 * 3600 }, Wa = S.run(M, Object.assign({}, wd)).result(), Wb = S.run(M, Object.assign({ att: { academy: { off: 1 } } }, wd)).result(), Wc = S.run(M, Object.assign({ act: ['noTw4034'] }, wd)).result();
    ck('평일 — 학원 수요를 켜면 4034 서쪽 대기가 길다 · 시차제 끄고 보기도 돈다', (Wa.maxQm['4034.wt'] || 0) >= (Wb.maxQm['4034.wt'] || 0), { 학원켬_4034서쪽최대m: Wa.maxQm['4034.wt'], 학원끔: Wb.maxQm['4034.wt'], 시차제켬_지체: Wa.delayVh, 시차제끔_지체: Wc.delayVh, 시차제끔_4028서쪽m: Wc.maxQm['4028.wt'], 시차제켬_4028서쪽m: Wa.maxQm['4028.wt'] });
    var sat = { date: '2026-10-24', seed: 4, att: { fount: { inPeak: 1200 } } }, Fa = S.run(M, sat).result(), Fb = S.run(M, Object.assign({ act: ['coneLaneDrop'] }, sat)).result();
    ck('토 분수 1,200대/시 — 라바콘 원거리 차로 축소를 하면 4031 북쪽(반포대교남단 쪽) 대기·지체가 줄거나 같다', Fb.delayVh <= Fa.delayVh, { 축소전_지체: Fa.delayVh, 축소후: Fb.delayVh, 축소전_4031북쪽m: Fa.maxQm['4031.nt'], 축소후_4031북쪽m: Fb.maxQm['4031.nt'] });
    // ⑧ 출입구 4곳 · 고속버스 시간표(요일 갈래 월~목·금·토·일)
    var sh = M.att.filter(function (a9) { return a9.id === 'shin'; })[0], tb = M.tbl && M.tbl.bus && M.tbl.bus.t;
    ck('신세계 출입구 4곳(북 신반포로·동 잠원로·남 사평대로·서 반포대로) · 고속버스 시간표 네 갈래(금 17시 경부·영동 출발 ' + (tb ? tb.fr.gb.out[17] : '-') + '대)', sh && sh.doors.length === 4 && tb && tb.mt && tb.fr && tb.sa && tb.su && tb.fr.gb.out[17] > 0, sh ? sh.doors.map(function (d) { return d.id; }).join('') : null);
    var Fr = S.run(M, { date: '2026-10-23', seed: 5, to: 19 * 3600 }), Mo = S.run(M, { date: '2026-10-21', seed: 5, to: 19 * 3600 }), nb = function (X) { return X.V.filter(function (v) { return v.att === 'busGB' || v.att === 'busCT'; }).length; };
    ck('요일 갈래가 수요에 들어간다 — 금요일 고속버스가 월~목보다 많다(TAGO 금 17시 출발 195 · 목 158)', nb(Fr) > nb(Mo), { 금: nb(Fr), 월목: nb(Mo) });
    // ⑥ 자동으로 엮은 구역들
    Object.keys(window.__AREAS || {}).forEach(function (nm) {
      var AM = __AREAS[nm], t1 = performance.now(), X = S.run(AM, { date: '2026-10-18', seed: 3 }), rx = X.result(), ns = Object.keys(AM.nodes), np = ns.filter(function (id) { var p = AM.nodes[id].plan; return p && (p.tod || (p.recs && p.recs.length) || (p.win && p.win.length)); }).length;
      ck('자동 구역 ' + nm + ' — 신호 ' + ns.length + '곳(계획 있음 ' + np + ') · 차 보존 · 길 못 찾은 차 0', X.V.length === X.done + X.inNet() && X.log.length === 0 && np >= 1, { 만든차: X.V.length, 지체_대시: rx.delayVh, 막힌접근로최대: rx.jamMax, ms: Math.round(performance.now() - t1), log: X.log.slice(0, 2) });
    });
    if ((window.__AREAS || {})['banpo-auto']) { var BA = __AREAS['banpo-auto'], same = ['4031', '4019', '4028', '4034'].every(function (id) { return BA.nodes[id] && Object.keys(BA.nodes[id].legs).length === 4; }); ck('반포 자동 구역 = 손으로 짠 구역의 네 교차로(다리 넷씩)를 찾는다', same, Object.keys(BA.nodes)); }
    function hh(t) { if (t == null) return '-'; var h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60); return (h < 10 ? '0' : '') + h + ':' + (m < 10 ? '0' : '') + m; }
  } catch (e) { ck('예외', false, String(e && e.stack || e)); }
  out.push(bad ? '❌ 실패 ' + bad : 'ALL_OK');
  document.getElementById('out').textContent = out.join('\n');
})();
