/* 가르고 값 검사 — tools/check/pagecheck.py 가 화면 끝에 끼워 넣는다(사이트에는 안 올라간다 · tools 는 _config.yml exclude).
   보는 것: 길 계산이 된다 · 길이 이어져 있다 · 회전 금지를 어기지 않는다 · 제한속도보다 빠르게 셈하지 않는다 ·
   속도 권고가 제한속도를 넘지 않는다 · 밤(22~06시)에는 속도 권고가 안 나온다 · 신호 값이 말이 되는 범위다 · 화면 오류 0 */
(function () {
  var C = [], t0 = Date.now();
  function ck(n, ok, got) { C.push([n, !!ok, got == null ? '' : String(got).slice(0, 160)]); }
  function send() { var o = { checks: C }, s = btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''), n = Math.ceil(s.length / 1500), id = String(Date.now());
    for (var i = 0; i < n; i++) (new Image()).src = '/__r?p=' + window.__PAGE + '&k=' + id + '&i=' + i + '&n=' + n + '&d=' + s.substr(i * 1500, 1500); }
  function fail(m) { ck('검사 스크립트가 끝까지 돌았다', false, m); send(); }
  function ready() { try { var g = window.GARGO, st = g && g.state(); return !!(st && st.G && st.G.S && st.G.S.length && st.G.XS); } catch (e) { return false; } }
  /* v0.8.0 칸 묶음 — 처음엔 큰길만(칸 0) 받는지 보고, 검사(길 찾기 여러 벌)는 칸을 모두 받은 뒤에 한다 */
  var poll = setInterval(function () { if (ready()) { clearInterval(poll); var P0 = window.GARGO.pk(); ck('칸 묶음 — 처음엔 큰길 한 장 + 받은 자리(#from·#to) 둘레 칸만(전체의 1/4 아래)', !P0.on || (P0.tiles > 0 && P0.tiles < P0.total / 4), JSON.stringify(P0));
      if (P0.on) ck('칸 묶음 — 큰길만·일부 칸만 받아도 큰길 마디의 회전 제한은 다 있다', window.GARGO.pkTurns() > P0.turnsTotal * 0.8, window.GARGO.pkTurns() + ' / 원본 ' + P0.turnsTotal);
      window.GARGO.pkAll().then(function () { var P1 = window.GARGO.pk(); if (P1.on) ck('칸 묶음 — 골목 칸을 모두 받아 합쳤다', P1.tiles === P1.total && window.GARGO.state().G.S.length > 60000, P1.tiles + '/' + P1.total + '칸 · 길 줄 ' + window.GARGO.state().G.S.length);
        /* 내용 맞대기 — 큰길 묶음(core)의 회전 제한 200개가 길 계산이 쓰는 표(G.ban·G.only · 열쇠 「마디|들어오는 길 번호」)에 그대로 있는가. core 마디는 합칠 때 맨 앞에 core.nodes 차례로 번호가 매겨진다 */
        if (P1.on) { var PKc = window.GARGO.pkCore(), Gs = window.GARGO.state().G, idx = {}, okT = 0, badT = []; PKc.nodes.forEach(function (r, i) { idx[r[0]] = i; });
          PKc.turns.slice(0, 200).forEach(function (t) { var tb = (t[3] ? Gs.only : Gs.ban)[idx[t[0]] + '|' + t[1]]; if (tb && tb[t[2]]) okT++; else if (badT.length < 3) badT.push(t.join(',')); });
          ck('칸 묶음 — 큰길 회전 제한 200개가 길 계산 표에 그대로(내용 맞대기)', okT === Math.min(200, PKc.turns.length), okT + '/' + Math.min(200, PKc.turns.length) + (badT.length ? ' · 빠짐 ' + badT.join(' | ') : '')); }
        if (P1.on) ck('칸 묶음 — 회전 금지·지정 방향이 원본 묶음과 같은 수(길 번호 그대로 · v0.8.0~0.9.1 은 모두 무효였다)', window.GARGO.pkTurns() === P1.turnsTotal && P1.turnsTotal > 1000, window.GARGO.pkTurns() + ' / 원본 ' + P1.turnsTotal);
        setTimeout(function () { try { run(); } catch (e) { fail(e && e.message); } }, 2500); }); } else if (Date.now() - t0 > 45000) { clearInterval(poll); fail('45초 안에 길 묶음이 안 읽혔다(문법 오류 · 파일 없음) ' + (window.__ERR || []).join(' | ')); } }, 300);

  function run() {
    var g = window.GARGO, st = g.state(), G = st.G, now = Date.now() / 1000;
    ck('가르고가 열린다(문법 · 길 묶음)', true, '길 ' + G.S.length + '줄 · 신호 교차로 ' + G.sig.length + '곳');
    ck('신호 교차로가 있다(서초 묶음 100곳 넘게)', G.sig.length > 100, G.sig.length);
    ck('값 없는 신호도 신호로 친다(T-GIS 800곳 넘게 붙음)', G.XS.length > 800, G.XS.length);
    /* v0.13.0 카카오내비 참고 — 일반 단추 한 줄 · 안내 중 왼쪽 경로 소통 막대(🏁 · 내 자리 · 신호 점) · 다음 회전 300m 안이면 줄어드는 막대 */
    if (st.route && !st.guide) { g.paint(); var mb = document.querySelector('#gBot [data-mode="n"]');
      ck('🚗 「일반」 단추가 한 줄(두 줄로 꺾이지 않음 · 글이 안 잘림)', !!mb && /일반/.test(mb.textContent) && mb.offsetHeight <= 46 && mb.scrollWidth <= mb.clientWidth + 1, mb ? mb.offsetWidth + '×' + mb.offsetHeight : '없음');
      g.guideStart(); g.paint(); g.paint(); var gb = document.getElementById('gBar'), gbr = gb.getBoundingClientRect(), gtp = document.getElementById('gTop').getBoundingClientRect(), r0 = g.state().route, m0 = r0.mans.filter(function (x) { return x.k !== 'E'; })[0];
      ck('📊 안내 중 경로 소통 막대 — 보임 · 🏁·내 자리 · 위 안내 판과 안 겹침', getComputedStyle(gb).display === 'block' && !!gb.querySelector('.tr') && !!gb.querySelector('.fl') && !!gb.querySelector('.me') && gbr.top > gtp.bottom, Math.round(gbr.top) + '~' + Math.round(gbr.bottom) + 'px · 신호 점 ' + gb.querySelectorAll('.tr b').length);
      var bt5 = document.getElementById('gBot'), mp5 = document.getElementById('gMpop'); ck('☰ 아래 막대 — 왼쪽 ⟳ 경로 다시 찾기 · 오른쪽 ≡ · 「안내 끝」은 메뉴 안(처음엔 감춤 · ≡ 누르면 보임)', !!bt5.querySelector('#gReplan.rp') && !!bt5.querySelector('#gMenu') && !!mp5 && getComputedStyle(mp5).display === 'none' && (function () { document.getElementById('gMenu').click(); var on = getComputedStyle(document.getElementById('gMpop')).display === 'flex'; return on && !!document.querySelector('#gMpop #gStop'); })(), '');
      var gn = document.querySelector('#gTop .nx2'); ck('⤵ 「그다음」 — 회전 화살표 밑 작은 줄(v0.21.0 공간 줄이기 · 따로 칸 없음) · 회전 칸 안 글 줄에는 없음', !!gn && /그다음/.test(gn.textContent) && getComputedStyle(document.getElementById('gNext')).display === 'none' && !/그다음/.test((document.querySelector('#gTop .tx') || {}).textContent || ''), gn ? gn.textContent : '없음');
      var tpb = document.getElementById('gTop').getBoundingClientRect(), sgb = document.getElementById('gSig').getBoundingClientRect(), topEnd = Math.max(tpb.bottom, sgb.height ? sgb.bottom : 0); ck('📐 안내 중 위쪽 상자(회전 칸 + 신호 판)가 화면 높이의 30% 아래(고치기 전 44%)', topEnd / innerHeight < 0.30, Math.round(topEnd) + 'px / ' + innerHeight + ' = ' + Math.round(100 * topEnd / innerHeight) + '%');
      var cd0 = !!document.querySelector('#gTop .cd'), p0 = r0.pos; if (m0) { r0.pos = m0.d - 150; g.paint(); } var cdu = document.querySelector('#gTop .cd u');
      ck('↘ 다음 회전 300m 안이면 남은 거리 막대(150m 앞 = 50%) · 그 밖에선 없음', !!m0 && (m0.d - p0 > 300 ? !cd0 : true) && !!cdu && cdu.style.width === '50%', cdu ? cdu.style.width : '없음');
      var eb = String(document.getElementById('gBot').innerText || ''), rq = TT.calR(Date.now());
      ck('⏳ 실측 없는 길이 섞이면 도착·남은 시간을 폭으로(「~」 · 「추정」) · 폭 표(eta-cal r) 읽음', !rq || (r0.live >= 0.999 ? !/추정/.test(eb) : (/~/.test(eb) && /추정/.test(eb))), (rq ? rq.join('~') : '표 없음') + ' · 실시간 ' + Math.round((r0.live || 0) * 100) + '% · ' + eb.replace(/\s+/g, ' ').slice(0, 60));
      r0.pos = p0; g.guideStop(false); }
    /* v0.14.1 닿는 자리 — 자동차전용(우면산로)과 일반 길(남부순환로)이 겹친 교차로에서 전용 길만 후보로 잡아 돌아가던 것(route-spot 대조 · 신사역 → 예술의전당 12.3km) */
    g.icLoad();   /* v0.15.0 나들목 목록을 미리 받아 둔다 — 검사는 맨 끝(4.2초 뒤) */
    var s9 = g.P(127.019517, 37.516137), t9 = g.P(127.013111, 37.480682), r9 = g.findRoute(s9[0], s9[1], t9[0], t9[1], Date.now() / 1000, null);
    ck('🎯 닿는 자리 — 신사역 → 예술의전당이 양재IC 로 돌지 않는다(9km 아래 · 우면산로로 들어가지 않음)', !!r9 && r9.dist < 9000 && !r9.lims.some(function (q) { return q[2] === '우면산로' || q[2] === '양재대로'; }), r9 ? Math.round(r9.dist) + 'm · ' + r9.lims.map(function (q) { return q[2]; }).filter(function (v, i, A) { return v && v !== A[i - 1]; }).join('›') : '길 없음');
    /* v0.16.0 음성 안내 — 말소리를 가로채 무엇을 말하는지 · 시작 때 도착 예정 · 회전 300m·곧 · 마지막 신호 뒤 회전(또는 목적지)도 말함(종전엔 앞에 신호가 없으면 말하지 않았다) */
    if (g.state().route && !g.state().guide && window.speechSynthesis) { var SAID = [], sp0 = speechSynthesis.speak, cn0 = speechSynthesis.cancel; speechSynthesis.speak = function (u) { SAID.push(u.text); }; speechSynthesis.cancel = function () {};
      try { var vb = document.getElementById('gVoice'); vb.click(); g.guideStart(); var rv9 = g.state().route, ms9 = rv9.mans.filter(function (m) { return m.k !== 'E'; }), m1 = ms9[0], lastSg = rv9.sigs.length ? rv9.sigs[rv9.sigs.length - 1].d : 0, mL = rv9.mans.filter(function (m) { return m.d > lastSg + 30; })[0];
        if (m1) { rv9.pos = m1.d - 250; g.paint(); rv9.pos = m1.d - 50; g.paint(); }
        var nL0 = SAID.length, sg9 = rv9.sigs, mE = rv9.mans[rv9.mans.length - 1]; rv9.sigs = []; mL = mE; rv9.pos = mE.d - 250; g.paint(); rv9.sigs = sg9; var saidL = SAID.slice(nL0).join(' | ');   /* 앞에 신호가 하나도 없을 때(마지막 신호 뒤와 같은 처지) 목적지 300m 앞을 말하는지 */
        var j9 = SAID.join(' | ');
        ck('🔊 음성 — 시작 때 「도착 예정 … 약 N분」 · 회전 300m 앞·「곧」 · 마지막 신호 뒤 회전·목적지도 말함', /안내를 시작합니다\. 도착 예정 (오전|오후) \d+시/.test(j9) && (!m1 || (/미터 앞 /.test(j9) && /곧 /.test(j9))) && /미터 앞/.test(saidL), j9.slice(0, 120) + ' … 마지막 신호 뒤: ' + (mL ? saidL : '없음'));
        rv9.pos = 0; g.guideStop(false); vb.click(); } catch (e) { ck('음성 안내 검사', false, e.message); } finally { speechSynthesis.speak = sp0; speechSynthesis.cancel = cn0; } }
    /* v0.14.2 이웃 메움 — 실시간 값이 붙은 길이면 같은 길 이웃 줄(값 없음)도 그 값으로(경부 반포IC~서초IC 13~16km/h 인데 옆 줄은 80 으로 셈하던 것) */
    var Gf = g.state().G, nf = 0, bad9 = 0; if (g.liver()) { for (var ef = 0; ef < Gf.ne; ef++) { var fv = g.fill(ef); if (fv > 0) { nf++; if (!(fv <= 200)) bad9++; } } }
    ck('🧩 실시간 값 없는 줄을 같은 길 이웃 값으로 메움(실시간이 있을 때 · 메운 줄 > 0 · 값 정상)', !g.liver() || (nf > 0 && bad9 === 0), g.liver() ? '메운 줄 ' + nf + ' / ' + Gf.ne : '실시간 없음 — 건너뜀');
    /* v0.22.0 공사·통제 — 길 위 한 링크를 「전면 통제」로 두면 그 줄을 피해 돌고 · 「차로 통제」면 그 길로 가되 시간이 늘고 🚧 표시 */
    try { var Ga = g.state().G, sa = g.P(127.0076, 37.4919), ta = g.P(127.0341, 37.4844), ra = g.findRoute(sa[0], sa[1], ta[0], ta[1], Date.now() / 1000, null), ea = null, lka = null;
      for (var ia9 = Math.floor(ra.es.length / 2); ia9 < ra.es.length; ia9++) { var qa = Ga.S[Ga.eS[ra.es[ia9]]], la = qa[Ga.eR[ra.es[ia9]] ? 14 : 13]; if (la != null && la >= 0 && qa[2] > 80) { ea = ra.es[ia9]; lka = Ga.j.links[la]; break; } }
      var A9 = {}; A9[lka] = { nm: '공사', full: true, both: false, txt: '시험 전면통제' }; g.accSet(A9); var rb = g.findRoute(sa[0], sa[1], ta[0], ta[1], Date.now() / 1000, null);
      A9[lka] = { nm: '공사', full: false, both: false, txt: '시험 차로 통제' }; g.accSet(A9); var rc9 = g.findRoute(sa[0], sa[1], ta[0], ta[1], Date.now() / 1000, null); g.accSet(null);
      ck('🚧 공사·통제 — 전면 통제 링크는 피해 간다 · 차로 통제는 그 길로 가되 시간 늘고 「🚧」 줄(live-acc-seoul.json)', !!ea && rb && rb.es.indexOf(ea) < 0 && rc9 && (rc9.es.indexOf(ea) < 0 || ((rc9.accs || []).length > 0 && rc9.time > ra.time)), [lka, rb && rb.es.indexOf(ea), rc9 && (rc9.accs || []).length, ra && Math.round(ra.time), rc9 && Math.round(rc9.time)].join(' · ')); } catch (e) { ck('공사·통제 검사', false, e.message); }
    /* v0.23.0 다녀 본 길 기억 — ① 길을 따라 움직이면 지난 줄의 시간을 모은다 ② 같은 줄 두 번 = 그 속도를 쓴다 ③ 느리게 기억한 줄은 길 고르기에서 피한다 ④ 시험 뒤 지움 */
    try { g.lrnReset(); var Gl = g.state().G, sl = g.P(127.0076, 37.4919), tl = g.P(127.0341, 37.4844), rl = g.findRoute(sl[0], sl[1], tl[0], tl[1], Date.now() / 1000, null), dnL = Date.now, tL = dnL();
      Date.now = function () { return tL; };   /* 화면·경로는 건드리지 않고 길 맞대기만(lrnFeed) */
      try { for (var dd = 5; dd < Math.min(rl.dist - 20, 1500); dd += 12) { var ii = 1; while (ii < rl.cum.length - 1 && rl.cum[ii] < dd) ii++; var x0 = rl.pts[(ii - 1) * 2], y0 = rl.pts[(ii - 1) * 2 + 1], x1 = rl.pts[ii * 2], y1 = rl.pts[ii * 2 + 1], fr = (dd - rl.cum[ii - 1]) / ((rl.cum[ii] - rl.cum[ii - 1]) || 1), hd = (Math.atan2(x1 - x0, -(y1 - y0)) * 180 / Math.PI + 360) % 360; tL += 1500; g.lrnFeed(x0 + (x1 - x0) * fr, y0 + (y1 - y0) * fr, hd, 8); } } finally { Date.now = dnL; }
      var nL1 = g.lrnCount();
      var eL = null; for (var k8 = 0; k8 < rl.es.length; k8++) { var qL = Gl.S[Gl.eS[rl.es[k8]]]; if (qL[2] > 120 && qL[4] <= 4) { eL = rl.es[k8]; break; } }
      var lenL = Gl.S[Gl.eS[eL]][2]; g.lrnAdd(eL, lenL / (15 / 3.6)); g.lrnAdd(eL, lenL / (15 / 3.6)); var vL = g.lrnSpeed(eL), rl2 = g.findRoute(sl[0], sl[1], tl[0], tl[1], Date.now() / 1000, null); g.lrnReset(); g.lrnAdd(eL, lenL / (40 / 3.6)); g.lrnAdd(eL, lenL / (40 / 3.6)); var rl3 = g.findRoute(sl[0], sl[1], tl[0], tl[1], Date.now() / 1000, null);   /* 시간대와 무관하게 — 15km/h 로 기억했을 때가 40km/h 로 기억했을 때보다 피하거나 느리다 */
      ck('🧠 다녀 본 길 — 길 따라 움직이면 지난 줄을 모은다 · 같은 줄 두 번이면 그 속도(15km/h)를 쓴다 · 느리게(15) 기억하면 빠르게(40) 기억했을 때보다 피하거나 시간이 는다', nL1 > 0 && Math.abs(vL - 15) < 1 && (rl2.es.indexOf(eL) < 0 || rl2.time > rl3.time + 3), '모은 줄 ' + nL1 + ' · 속도 ' + vL.toFixed(1) + ' · ' + (rl2.es.indexOf(eL) < 0 ? '피함' : Math.round(rl3.time) + '(40) → ' + Math.round(rl2.time) + '초(15)'));
      g.lrnReset(); } catch (e) { ck('다녀 본 길 검사', false, e.message); try { g.lrnReset(); } catch (x) {} }
    /* v0.27.0 열차 안 신고 — 방배(2호선) 떠남 · 서초 쪽 → 후보 6역 · 확률 0~1 · 권고 또는 경합 · 문구 · 밖으로 나간 요청 0 · 남기는 것 없음 */
    try { var ls9 = Object.keys(localStorage).sort().join(','), nr8 = performance.getEntriesByType('resource').length; g.sr.load().then(function (SD) { try {
        var bb9 = SREACH.find('방배', '2호선'), sc9 = SREACH.find('서초', '2호선'); g.sr.open(true); g.sr.click('ln|2호선'); g.sr.click('st|' + bb9); g.sr.click('nx|' + sc9); g.sr.click('ag|0'); var R9 = g.sr.calc(), hx9 = String(document.getElementById('gSR').innerText || '');
        var ext8 = performance.getEntriesByType('resource').slice(nr8).filter(function (e) { return e.name.indexOf(location.origin) !== 0; }).length;
        ck('🚇 열차 안 신고 — 방배 떠남·서초 쪽 → 후보 6역(서초·교대·강남…) · 확률 0~1 · 권고/경합 · 「최종 판단은 현장 경찰관」·「실시간 위치가 아니다」·「가정값」 · 밖으로 나간 요청 0 · 저장 0', R9 && R9.cards.length === 6 && R9.cards[0].nm === '서초' && R9.cards.every(function (c) { return c.p == null || (c.p >= 0 && c.p <= 1); }) && R9.best != null && /최종 판단은 현장 경찰관/.test(hx9) && /실시간 위치가 아니다/.test(hx9) && /가정값/.test(hx9) && ext8 === 0 && !Object.keys(localStorage).some(function (k) { return ls9.split(',').indexOf(k) < 0 && /sr|train|station/i.test(k); }),
          R9 ? R9.cards.map(function (c) { return c.nm.replace(/\(.*?\)/, '') + ' ' + (c.p == null ? '-' : Math.round(c.p * 100) + '%'); }).join(' · ') + ' · 권고 ' + (R9.best != null ? SD.st[R9.best][1] : '-') + (R9.close ? '(경합)' : '') + ' · 바깥 ' + ext8 : '없음'); g.sr.open(false); } catch (e) { ck('열차 안 신고 검사', false, e.message); } }); } catch (e) { ck('열차 안 신고 검사', false, e.message); }
    /* v0.26.0 여러 순찰차 — 빨리 닿는 순서 · 지령 문구 · 참고용 예측 · 밖으로 나가는 요청 없음 · 도착 기록 꼴(좌표 없음) */
    try { var tg9 = g.P(127.0341, 37.4844); g.setDest(tg9[0], tg9[1], '시험 출동지'); var nr0 = performance.getEntriesByType('resource').length;
      var c1 = g.P(127.0076, 37.4919), c2 = g.P(127.0262, 37.4936), c3 = g.P(127.0402, 37.4768), DR = g.disp([[c1[0], c1[1], '서초1'], [c2[0], c2[1], '서초2'], [c3[0], c3[1], '서초3']]);
      var srt = DR && DR.ok.length === 3 && DR.ok[0].t <= DR.ok[1].t && DR.ok[1].t <= DR.ok[2].t && DR.ok.every(function (q) { return q.pm > 0 && q.t > 0; }), od = DR ? g.dispOrder(DR.ok[0]) : '', hx = g.dispHtml(), ext9 = performance.getEntriesByType('resource').slice(nr0).filter(function (e) { return e.name.indexOf(location.origin) !== 0; }).length;
      ck('🚓 여러 순찰차 — 빨리 닿는 순서로 줄 세움 · 지령 문구 「○호 예상 N분 M초(±…), △△ 쪽 정차」 · 「참고용 예측」·「최종 판단은 현장 경찰관」 · 셈하는 동안 밖으로 나간 요청 0', srt && /^서초\d 예상 \d+(분|초)/.test(od) && /±/.test(od) && /참고용 예측/.test(hx) && /최종 판단은 현장 경찰관/.test(hx) && ext9 === 0, od + ' · ' + (DR ? DR.ok.map(function (q) { return q.c.nm + ' ' + Math.round(q.t) + '초 직선 ' + Math.round(q.st) + (q.why ? ' ' + q.why : ''); }).join(' / ') : '없음') + ' · 바깥 ' + ext9);
      var a0 = localStorage.getItem('tg_gg_arr'); g.arrAdd({ t: Date.now(), pred: 600, mode: 'e', sim: false, dist: 4230, lo: 500, hi: 720 }, 640); var la = g.arrAll().l, q9 = la[la.length - 1];
      ck('⏱ 예상·실제 도착 기록 — [날짜, 시, 요일 갈래, 모드, km, 예상, 폭 아래, 폭 위, 실제] · 좌표 없음', q9 && q9.length === 9 && q9[3] === 'e' && q9[4] === 4.2 && q9[5] === 600 && q9[8] === 640 && !/\d{2}\.\d{4,}/.test(JSON.stringify(la)), JSON.stringify(q9));
      if (a0 == null) localStorage.removeItem('tg_gg_arr'); else localStorage.setItem('tg_gg_arr', a0); g.disp([]); } catch (e) { ck('여러 순찰차 검사', false, e.message); }
    /* v0.24.1 키 작은 폰 규칙 */
    try { var mq = false; for (var si = 0; si < document.styleSheets.length; si++) { try { var rl = document.styleSheets[si].cssRules; for (var ri = 0; ri < rl.length; ri++) if (rl[ri].media && /max-height:\s*620px/.test(rl[ri].media.mediaText) && /#gTop/.test(rl[ri].cssText)) mq = true; } catch (x) {} }
      ck('📱 키 작은 폰(높이 620px 아래)에서 위 판을 줄이는 규칙', mq, String(mq)); } catch (e) { ck('키 작은 폰 규칙', false, e.message); }
    /* v0.24.0 모드 색 · 음성 빠르기 */
    try { g.mode('e'); g.paint(); var me1 = document.body.classList.contains('mode-e'); g.mode('n'); g.paint(); var me0 = !document.body.classList.contains('mode-e') && !document.body.classList.contains('mode-v');
      ck('🎨 긴급 출동이면 화면에 빨간 테(mode-e) · 일반으로 돌아오면 없음 · ⚙ 음성 빠르기 기본 1.05 · 공휴일 판정 함수', me1 && me0 && g.cfg().vrate === 1.05 && typeof TT.isHol === 'function', [me1, me0, g.cfg().vrate].join(' · ')); } catch (e) { ck('모드 색 검사', false, e.message); }
    /* v0.14.0 주행 기록 — 기본 끔 · 켜면 안내 중 2초마다 기기에 · 끝나면 최근 목록에 · 중요업무·모의 주행은 안 남김 · 시험 뒤 지움 */
    if (st.route && !g.state().guide) { var dv0 = g.drv(); g.guideStart(); var off0 = g.drv().cur; g.guideStop(false);
      localStorage.setItem('tg_gargo_drvon', '1'); g.guideStart(); var dn = Date.now, tt9 = dn(); Date.now = function () { return tt9 += 2500; };
      try { for (var di = 0; di < 7; di++) g.drvPt({ latitude: 37.4919 + di * 1e-4, longitude: 127.0076, accuracy: 6, speed: 11 }); } finally { Date.now = dn; }
      var cur = g.drv().cur; g.guideStop(false); var all = g.drv().all, L9 = all[all.length - 1];
      var od9 = g.state().dest, od9c = od9 ? { x: od9.x, y: od9.y, nm: od9.nm } : null; g.guideStart(); g.mode('v'); var vipCur = g.drv().cur; g.drvPt({ latitude: 37.5, longitude: 127.01, accuracy: 5, speed: 10 }); g.guideStop(false); var vipN = g.drv().all.length; g.mode('n'); if (od9c) g.setDest(od9c.x, od9c.y, od9c.nm); g.paint();   /* 기록 중 중요업무로 바뀌면 그 기록을 버린다 · 원래 목적지로 되돌림(81줄과 같은 방식) */
      localStorage.removeItem('tg_gargo_drvon'); localStorage.removeItem('tg_gargo_drives');
      ck('🛰 주행 기록 — 기본 끔 · 켜면 2초마다 7점 · 끝나면 기기에 1번(tg-drive-log/1 · 예측 줄 = [교차로, +초, 근거, m, 위도, 경도]) · 중요업무는 안 남김 · 시험 뒤 지움', !dv0.on && off0 === null && cur && cur.pts.length === 7 && all.length === 1 && L9.schema === 'tg-drive-log/1' && L9.plan.rows.length === r0.sigs.length && /^(its|liver|cal|lim)$/.test((L9.plan.rows[0] || [])[2] || 'lim') && vipCur === null && vipN === 1 && !localStorage.getItem('tg_gargo_drives'),
        [dv0.on, off0, cur && cur.pts.length, all.length, L9 && L9.plan.rows.length, (L9 && L9.plan.rows[0] || []).slice(0, 3).join('/'), vipCur, vipN].join(' · ')); }
    /* 1) 소통 갈래 — 앱 기준표 그대로 */
    var sp = [[60, 1, 100, 0], [40, 1, 100, 1], [20, 1, 100, 2], [30, 3, 50, 0], [20, 3, 50, 1], [10, 3, 50, 2], [22, 6, 30, 0], [13, 6, 30, 1], [8, 6, 30, 2]], bad = [];
    sp.forEach(function (q) { var v = g.spdLv(q[0], q[1], q[2]); if (v !== q[3]) bad.push(q.join('/') + '→' + v); });
    ck('소통 갈래 기준표(9칸)', !bad.length, bad.join(' '));
    /* 1-1) 방향 맞추기 — 내가 들어가는 쪽의 기록만 쓴다 · 비스듬해서 양옆 방위 기록이 둘이면 고르지 않는다(다른 방향의 초를 보이지 않는다) */
    var R2 = { mv: [['st', 'St', 50, 0, 0, 0], ['wt', 'St', 40, 0, 0, 10], ['st', 'Lt', 20, 0, 0, 60]] }, R1 = { mv: [['st', 'St', 50, 0, 0, 0]] }, m1 = g.mvOf(R2, 'st', 'St'), m2 = g.mvOf(R2, 'sw', 'St'), m3 = g.mvOf(R1, 'sw', 'St'), m4 = g.mvOf(R2, 'nt', 'St'), m5 = g.mvOf(R2, 'st', 'Lt');
    ck('방향 · 같은 쪽 기록을 쓴다(남쪽에서 직진 → 남 50초 · 좌회전 → 20초)', m1 && m1[0] === 'st' && m1[2] === 50 && m5 && m5[2] === 20);
    ck('방향 · 양옆에 기록이 둘이면 고르지 않는다(남서쪽에서 → 모름)', m2 === null, m2 ? m2[0] : '모름');
    ck('방향 · 옆 방위가 하나뿐이면 그것을 쓴다 · 반대쪽 기록은 안 쓴다', m3 && m3[0] === 'st' && m4 === null);
    /* v0.7.2 독립 검수 — 경찰청 계획(인재개발원 3971 · 평일 계획 마지막 줄 23:00 · 토·일 계획 22:00)의 날짜 셈: 그날 첫 줄보다 이르면 **실제 어제** · 특수일(2026-10-09 한글날 금)은 일요일 계획 */
    g.todFor('3971', function () {});   /* 경찰청 계획을 미리 받아 둔다 — 날짜 셈 검사는 밤 시험이 시계를 되돌린 뒤에 */
    try { g.bnmLoad(); } catch (e) {}
    try { g.alrLoad(); } catch (e) {}   /* 카메라·보호구역 알림 자료를 미리 받아 둔다 */   /* 건물 이름 목록을 미리 받아 둔다 — 찾기 검사는 밤 시험 뒤에 */
    /* v0.7.0 — 여섯 구 묶음(pack-six)이 실렸는지 · 서초 밖 길 셋을 같은 품질 기준으로 */
    ck('여섯 구 길 묶음이 실렸다(마디 6만 넘게 · 송파·용산까지)', (function () { var G0 = g.state().G, a = g.P(127.1059, 37.5145), b = g.P(126.9648, 37.5298); return G0 && G0.S.length > 60000 && a[0] <= G0.box[1] && b[1] >= G0.box[2]; })(), (g.state().G || {}).S ? g.state().G.S.length + '줄' : '없음');
    /* 2) 길 계산 세 벌 — 서초역→양재역 · 고속터미널→방배역 · 교대역→예술의전당 */
    var OD = [['사당역→서울대입구역(동작·관악 · v0.7.0 여섯 구)', 126.9816, 37.4766, 126.9527, 37.4812], ['용산역→노량진역(용산·동작)', 126.9648, 37.5298, 126.9425, 37.5137], ['인재개발원→송파구청(서초·강남·송파)', 127.0227, 37.4830, 127.1059, 37.5145], ['서초역→양재역', 127.0076, 37.4919, 127.0341, 37.4844], ['고속터미널→방배역', 127.0049, 37.5049, 126.9976, 37.4814], ['교대역→예술의전당', 127.0142, 37.4934, 127.0118, 37.4786], ['서초역→서초경찰서(짧은 길)', 127.0076, 37.4919, 127.005607, 37.495467], ['방배경찰서→서초경찰서', 126.9826, 37.4813, 127.0056, 37.4955], ['사당역→고속터미널', 126.9816, 37.4766, 127.0049, 37.5049]];
    OD.forEach(function (o) {
      var a = g.P(o[1], o[2]), b = g.P(o[3], o[4]), r = g.findRoute(a[0], a[1], b[0], b[1], now, null), line = Math.hypot(a[0] - b[0], a[1] - b[1]);
      if (!r) { ck(o[0] + ' · 길이 나온다', false, '길 없음'); return; }
      ck(o[0] + ' · 길이 나온다', r.es.length > 2 && isFinite(r.dist) && isFinite(r.time), Math.round(r.dist) + 'm · ' + Math.round(r.time) + '초 · 신호 ' + r.sigs.length + '곳');
      ck(o[0] + ' · 길이가 말이 된다(직선 이상 · 4배 이하)', r.dist >= line * 0.9 && r.dist <= line * 4, Math.round(r.dist) + 'm / 직선 ' + Math.round(line) + 'm');
      ck(o[0] + ' · 제한속도보다 빠르게 셈하지 않는다', r.time >= r.free * 0.999, '걸림 ' + Math.round(r.time) + '초 ≥ 제한속도로만 ' + Math.round(r.free) + '초');
      var brk = 0, ban = 0, i;
      for (i = 0; i + 1 < r.es.length; i++) { var e = r.es[i], f = r.es[i + 1]; if (G.eB[e] !== G.eA[f]) brk++;
        var key = G.eB[e] + '|' + G.S[G.eS[e]][6], w2 = G.S[G.eS[f]][6], bn = G.ban[key], on = G.only[key]; if ((bn && bn[w2]) || (on && !on[w2])) ban++; }
      ck(o[0] + ' · 줄이 끊기지 않는다', brk === 0, '끊긴 곳 ' + brk);
      /* v0.5.0 길 고르기 품질 — 골목으로 돌지 않는다(골목·생활도로 길이 몫 20% 아래) · 꺾는 곳이 적다(9번 아래) · 에움(길 ÷ 직선) 1.7 아래 */
      var al = 0, tot = 0; r.es.forEach(function (e2) { var q2 = G.S[G.eS[e2]]; tot += q2[2]; if (q2[4] >= 6) al += q2[2]; }); var alp = tot ? al / tot * 100 : 0, turns = r.mans.length - 1, det = r.dist / line;
      /* 2026-10-14 큰길로만 돌아가는 길(골목 5% 이하 · 꺾음 4번 이하)은 에움 2.0 까지 — 교대역→예술의전당이 12:10 소통 값에서 서초대로 › 반포대로 › 우면산로(2.9km · 꺾음 2 · 골목 0%)로 1.75 가 나왔다. v0.5.1 판도 같은 값 → 길 찾기 탓이 아니라 그 시각 소통 탓. 1.7 은 골목·지그재그를 잡으려는 기준이다 */
      /* 고속터미널→방배역은 떠나는 자리가 중앙분리된 큰길의 동쪽행 차로에 붙어 한 번 돌아야 하는 구간이다(큰길 유턴 자리가 길 자료에 없다 — 알려진 한계) → 에움은 2.0 까지 */
      ck(o[0] + ' · 골목으로 돌지 않는다(20% 아래) · 꺾음 9번 아래 · 에움 1.7 아래', line < 600 || (alp <= 20 && turns <= 9 && det <= (/고속터미널→방배역/.test(o[0]) || (alp <= 5 && turns <= 4) ? 2.0 : 1.7)), '골목 ' + Math.round(alp) + '% · 꺾음 ' + turns + ' · 에움 ' + det.toFixed(2));
      ck(o[0] + ' · 회전 금지·지정 방향을 어기지 않는다', ban === 0, '어긴 곳 ' + ban);
      var over = [], odd = [];
      r.sigs.forEach(function (s) { if (!(s.lim > 0)) odd.push(s.nm + ' 제한속도 없음');
        if (s.s) { if (['pl', 'anchor', 'avg'].indexOf(s.s.kind) < 0) odd.push(s.nm + ' 갈래 ' + s.s.kind); if (s.s.kind !== 'avg' && !(s.s.remain >= 0 && s.s.remain <= (s.s.C || 400) + 1)) odd.push(s.nm + ' 남은 초 ' + s.s.remain); if (!(s.w >= 0 && s.w < 400)) odd.push(s.nm + ' 기다림 ' + s.w); }
        [120, 300, 600].forEach(function (dd) { var ad = g.advise(s, dd, now); if (ad && !(ad.v <= s.lim && ad.v >= 20)) over.push(s.nm + ' ' + ad.v + '>' + s.lim); }); });
      ck(o[0] + ' · 속도 권고가 제한속도를 넘지 않는다', !over.length, over.join(' '));
      ck(o[0] + ' · 신호 값이 범위 안이다', !odd.length, odd.join(' '));
    });
    /* 2-1) 도로명 번호 어림(통신이 안 될 때만 쓰는 값) — 브이월드에서 받은 참값(2026-10-13)과 맞대 본다 · 묶음 밖에서 시작하는 길과 지번은 셈하지 않는다 */
    [['반포대로 179', 127.005607, 37.495467, 150], ['사임당로 143', 127.02512, 37.491773, 150], ['방배로 100', 126.996767, 37.483272, 150], ['서울 서초구 서초대로 74길 11', 127.026941, 37.496574, 150]].forEach(function (t) { var r = g.addrGuess(t[0]), p0 = g.P(t[1], t[2]), dd = r ? Math.hypot(r[2] - p0[0], r[3] - p0[1]) : -1; ck('주소 어림 · ' + t[0] + ' (참값에서 ' + t[3] + 'm 안)', r && dd <= t[3], r ? Math.round(dd) + 'm' : '못 셈'); });
    ck('주소 어림 · 묶음 밖에서 시작하는 길(남부순환로 2406)은 셈하지 않는다', g.addrGuess('남부순환로 2406') === null); ck('주소 어림 · 지번(서초동 1726-1)은 셈하지 않는다', g.addrGuess('서초동 1726-1') === null);
    /* 3) 화면 — 받은 주소(#from·to)로 길이 잡혔는가 · 그리기 · 모의 주행 */
    var rt = g.state().route; ck('주소의 #from·#to 로 길이 잡힌다', !!(rt && rt.es && rt.es.length), rt ? Math.round(rt.dist) + 'm' : '없음');
    try { g.draw(); ck('지도 그리기', true); } catch (e) { ck('지도 그리기', false, e.message); }
    /* v0.10.0 — 길 요약 판을 다시 그려도(위치가 올 때마다) 펼친 칸은 펼친 채 */
    var stp = document.querySelector('#gBot details.steps'); if (stp) { stp.open = true; g.paint(); } var stp2 = document.querySelector('#gBot details.steps'); ck('길 요약 판을 다시 그려도 펼친 「가는 차례」는 펼친 채', !!(stp2 && stp2.open)); if (stp2) stp2.open = false;
    g.risk();   /* ⚠ 이 길 주의 교차로 표(risk-six.json) — 받기만 걸어 두고 아래 4초 뒤에 잰다 */
    /* v0.11.0 🔒 중요업무 — 밖으로 나가는 요청을 모두 적어 둔다(fetch·XHR·sendBeacon·window.open) · 그 사이 주소 찾기·음성을 시도하고 4초 뒤에 잰다 */
    window.__NET = []; var of = window.fetch, ox = XMLHttpRequest.prototype.open, ob = navigator.sendBeacon, oo = window.open;
    window.fetch = function (u) { __NET.push(String(u && u.url || u)); return of.apply(this, arguments); }; XMLHttpRequest.prototype.open = function (m, u) { __NET.push(String(u)); return ox.apply(this, arguments); };
    if (ob) navigator.sendBeacon = function (u) { __NET.push('beacon ' + u); return false; }; window.open = function (u) { __NET.push('open ' + u); return null; };
    window.__NETX = function () { window.fetch = of; XMLHttpRequest.prototype.open = ox; if (ob) navigator.sendBeacon = ob; window.open = oo; };
    var pl0 = JSON.stringify(g.places()), od = g.state().dest, od0 = od ? { x: od.x, y: od.y, nm: od.nm } : null; g.mode('v'); g.findRun('반포대로 201', true); g.micGo(); var vp = g.P(127.0142, 37.4934); g.setDest(vp[0], vp[1], '시험 중요 지점');
    ck('🔒 중요업무 — 목적지를 최근 목적지에 남기지 않는다', JSON.stringify(g.places()) === pl0 || !/시험 중요 지점/.test(JSON.stringify(g.places())), '');
    g.mode('n'); if (od0) g.setDest(od0.x, od0.y, od0.nm); g.paint();   /* 아래 시험은 일반 모드·원래 목적지로 */
    /* 잇기 — 길 요약 판의 넘기기 단추 넷(데이터지도·티맵·카카오맵·네이버지도) · 데이터지도는 목적지 좌표로 같은 사이트의 지도를 연다 */
    var hb = document.querySelectorAll('#gBot [data-hand]'); ck('넘기기 단추 넷', hb.length === 4, [].map.call(hb, function (b) { return b.textContent; }).join(' · '));
    if (hb.length) { var op2 = [], wo2 = window.open; window.open = function (u) { op2.push(String(u)); return null; }; hb[0].click(); window.open = wo2; var m2 = /^\.\.\/#lat=(-?[\d.]+)&lon=(-?[\d.]+)$/.exec(op2[0] || ''); ck('「데이터지도」가 목적지(양재역 쪽)로 연다', !!m2 && Math.abs(+m2[1] - 37.4844) < 0.006 && Math.abs(+m2[2] - 127.0341) < 0.007, op2[0]); }
    ck('첫 안내는 세 줄 + 접어 둔 설명', document.querySelectorAll('#gIntro li').length === 3 && !!document.querySelector('#gIntro details'), document.querySelectorAll('#gIntro li').length + '줄');
    /* 4) 밤 — 시각을 23시로 바꿔 놓고 모의 주행 4초: 속도 권고 글이 한 번도 나오면 안 된다 */
    var gh = Date.prototype.getHours; Date.prototype.getHours = function () { return 23; };
    ck('밤 판정(23시 → 밤)', g.night() === true, g.night());
    var seen = 0, shown = 0; try { g.simStart(); } catch (e) { ck('모의 주행 시작', false, e.message); }
    var smp = setInterval(function () { var el = document.getElementById('gSig'), h = el ? el.innerHTML : ''; if (h) shown++; if (h.indexOf('시속') >= 0) seen++; }, 200);
    setTimeout(function () { clearInterval(smp); Date.prototype.getHours = gh;
      /* v0.7.2 독립 검수 — 경찰청 계획(인재개발원 3971 · 평일 계획 마지막 줄 23:00 · 토·일 계획 22:00)의 날짜 셈: 그날 첫 줄보다 이르면 **실제 어제** · 특수일(2026-10-09 한글날 금)은 일요일 계획 */
      [['화 03:00 → 월 계획 마지막 줄(23:00 · 전날)', '2026-10-13T03:00:00+09:00', function (t) { return t && t.prev && t.at === '23:00' && !t.hol; }],
       ['월 03:00 → 일 계획 마지막 줄(22:00 · 전날)', '2026-10-12T03:00:00+09:00', function (t) { return t && t.prev && t.at === '22:00'; }],
       ['한글날(금) 10:40 → 일요일 계획(특수일 · 추정 표시)', '2026-10-09T10:40:00+09:00', function (t) { return t && !t.prev && t.hol; }],
       ['한글날 다음 날(토) 03:00 → 전날 = 특수일 = 일 계획 마지막 줄(22:00 · 금요일 23:00 이 아님)', '2026-10-10T03:00:00+09:00', function (t) { return t && t.prev && t.at === '22:00' && t.hol; }]].forEach(function (c0) { var got = 'no'; g.todFor('3971', function (t) { got = t; }, new Date(c0[1]).getTime()); ck('경찰청 계획 날짜 · ' + c0[0], c0[2](got), JSON.stringify(got)); });
      /* v0.9.0 — 길 위 단속 카메라(경찰 · 제한속도 있음 · 길 위 30m 안 · 앞) · 거리마다 걸린 시간 표 · 집·즐겨찾기(이 기기) */
      try { var rc = g.findRoute.apply(null, (function () { var a = g.P(127.0076, 37.4919), b = g.P(127.0341, 37.4844); return [a[0], a[1], b[0], b[1], Date.now() / 1000, null]; })()), cams = [];
        for (var pp = 0; pp < rc.dist; pp += 700) { rc.pos = pp; var AA = g.alrAhead(g.routePoly(rc)); if (AA && AA.cam && cams.indexOf(AA.cam.rd + AA.cam.lim) < 0) cams.push(AA.cam.rd + AA.cam.lim); }
        ck('서초역→양재역 길 위 단속 카메라를 잡는다(경찰 · 제한속도 있는 것)', cams.length >= 2 && cams.every(function (x) { return /\d+$/.test(x); }), cams.join(' · '));
        var tl = rc.tc[rc.tc.length - 1]; ck('거리마다 걸린 시간 표 — 끝이 전체 거리·시간과 같다 · 가운데는 그 사이', Math.abs(tl[0] - rc.dist) < 1 && Math.abs(tl[1] - rc.time) < 1 && g.tAt(rc, rc.dist / 2) > 0 && g.tAt(rc, rc.dist / 2) < rc.time, Math.round(tl[0]) + 'm ' + Math.round(tl[1]) + '초 · 가운데 ' + Math.round(g.tAt(rc, rc.dist / 2)) + '초');
        var keepP = localStorage.getItem('tg_gargo_places'); g.plPut('h', { x: rc.a.x, y: rc.a.y, nm: '시험 집' }); var pl = g.places(); ck('집을 넣으면 찾기 목록 맨 앞에 🏠', pl.length && pl[0][0] === '🏠' && pl[0][1] === '시험 집', pl.slice(0, 2).map(function (x) { return x[0] + x[1]; }).join(' · ')); if (keepP == null) localStorage.removeItem('tg_gargo_places'); else localStorage.setItem('tg_gargo_places', keepP);
      } catch (e) { ck('v0.9.0 검사', false, e.message); }
      /* v0.10.0 ⚠ 이 길 주의 교차로(온톨로지 코어 v1 질문 4) — 서초역→양재역 · 지나는 교차로마다 표의 값 그대로 · 35m 안 · 사고 많은 차례 */
      try { var rk = g.findRoute.apply(null, (function () { var a = g.P(127.0076, 37.4919), b = g.P(127.0341, 37.4844); return [a[0], a[1], b[0], b[1], Date.now() / 1000, null]; })()), RL = g.riskOn(rk), RH = g.riskHtml(rk);
        ck('⚠ 이 길 주의 교차로 — 서초역→양재역에 3곳 넘게 · 모두 35m 안 · 길 위 거리 · 10년 사고 많은 차례', !!(RL && RL.length >= 3 && RL.every(function (h, i) { return h.off <= 35 && h.d >= 0 && h.d <= rk.dist + 1 && (!i || h.q[4] <= RL[i - 1].q[4]); })), RL ? RL.length + '곳 · ' + RL.slice(0, 3).map(function (h) { return h.q[1] + ' ' + h.q[4] + '건 ' + Math.round(h.off) + 'm'; }).join(' · ') : '표 없음');
        ck('⚠ 칸 글 — 이름·10년 건수·주 위반이 들어가고 근사라고 밝힌다', /⚠ 이 길 주의 교차로 \d+곳/.test(RH) && RL && RH.indexOf(RL[0].q[1]) >= 0 && /근사/.test(RH) && /주 위반/.test(RH), RH.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 90));
        var far = g.findRoute.apply(null, (function () { var a = g.P(127.0076, 37.4919), b = g.P(127.0090, 37.4925); return [a[0], a[1], b[0], b[1], Date.now() / 1000, null]; })()); ck('⚠ 짧은 길은 지나는 교차로만(전체 표를 쏟지 않는다)', !far || g.riskOn(far).length <= 3, far ? g.riskOn(far).length + '곳' : '길 없음');
      } catch (e) { ck('⚠ 이 길 주의 교차로 검사', false, e.message); }
      /* v0.11.0 🔒 중요업무 · ⚙ 설정 · 글씨 배율 */
      try { var NET = (window.__NET || []).slice(); window.__NETX && window.__NETX(); var bad = NET.filter(function (u) { return /^(open |beacon )/.test(u) || /^https?:/.test(u) && u.indexOf(location.origin) !== 0 || /vworld|relay|workers\.dev|반포대로/.test(decodeURIComponent(u)); });
        ck('🔒 중요업무 중 밖으로 나간 요청 0(주소 찾기·음성·중계·다른 앱 — 같은 사이트 자료 파일만)', bad.length === 0, bad.slice(0, 3).join(' | ') || NET.length + '건 모두 같은 사이트');
        var rv = g.findRoute.apply(null, (function () { var a = g.P(127.0076, 37.4919), b = g.P(127.0341, 37.4844); return [a[0], a[1], b[0], b[1], Date.now() / 1000, null]; })()); g.vipSet(0, null); var V0 = g.vipNow(rv, 0); g.vipSet(70, 90); var V1 = g.vipNow(rv, 0); g.vipSet(0, null);
        var sm = g.vipSegs(rv).reduce(function (a, x) { return a + x.m; }, 0);
        ck('🔒 중요업무 두 줄 — 기본 60 · 직접 입력 없으면 가장 이른 = 100 · 70/90 고르면 그 값 · 가장 이른 쪽이 더 빠름', V0 && V0.base.v === 60 && V0.fastV === 100 && !V0.typed && V1.base.v === 70 && V1.fastV === 90 && V1.typed && V0.fast.sec < V0.base.sec, V0 ? TT.fmt(V0.base.sec) + ' / ' + TT.fmt(V0.fast.sec) : '없음');
        ck('🔒 구간 합 = 길 거리 · 마지막 지점 = 목적지 · 신호 기다림 0(60km/h 순수 이동 + 회전·진출입·가감속만)', Math.abs(sm - rv.dist) < 3 && V0.base.cps.length >= 2 && Math.abs(V0.base.raw - (sm / (60 / 3.6) + V0.base.parts.turn + V0.base.parts.ramp + V0.base.parts.acc + (V0.base.parts.move - sm / (60 / 3.6)))) < 1 && V0.base.parts.sig === 0, Math.round(sm) + ' / ' + Math.round(rv.dist) + 'm · 지점 ' + (V0 && V0.base.cps.length));
        var bx = g.vipBox(rv); ck('🔒 요약 판 — 「교차로 통제 개시는 가장 이른 도착 시각 기준」 고정 · 「중요업무」 말만(행차·경호 낱말 없음)', /교차로 통제 개시는/.test(bx) && /가장 이른 도착/.test(bx) && !/행차|경호|VIP/.test(bx + document.body.innerHTML), '');
        g.mode('v'); g.paint(); var bb = document.getElementById('gBot'); ck('🔒 중요업무 요약 판 — 집·근무지·즐겨찾기·다른 앱으로 넘기기 단추가 없다', !bb.querySelector('[data-pl],[data-hand]'), bb.querySelectorAll('[data-pl],[data-hand]').length + '개');
        g.mode('n');
        var CF0 = g.cfg(), sig = document.getElementById('gSig'); ck('⚙ 기본값 — 앞 2,000m · 뒤 1,000m · 남은 초 2배 · 글씨 1.15', CF0.fwd === 2000 && CF0.back === 1000 && CF0.sz === 2 && CF0.fz === 1.15, JSON.stringify([CF0.fwd, CF0.back, CF0.sz, CF0.fz]));
        sig.insertAdjacentHTML('beforeend', '<div class="now" id="__nw"><i></i><b>녹색 12초</b></div>'); var px = function () { return parseFloat(getComputedStyle(document.querySelector('#__nw b')).fontSize); }, p1 = px();
        TT.set('sz', 1); g.cfgApply(); var p2 = px(); TT.set('fz', 1); g.cfgApply(); var p3 = px(); TT.reset(); g.cfgApply(); document.getElementById('__nw').remove();
        ck('⚙ 남은 초 글씨 = 종전(24px) × 글씨 1.15 × 2배 = 55px · 설정을 바꾸면 바로 바뀐다', Math.abs(p1 - 55.2) < 0.6 && Math.abs(p2 - 27.6) < 0.6 && Math.abs(p3 - 24) < 0.6, p1 + ' → ' + p2 + ' → ' + p3 + 'px');
        document.getElementById('gCfgB').click(); var cf = document.getElementById('gCfg'), op = cf.style.display === 'block' && cf.querySelectorAll('[data-cs]').length >= 30;
        var b1 = cf.querySelector('[data-cs="fwd:1000"]'); b1.click(); var f1 = g.cfg().fwd, rb = document.getElementById('gCfg').querySelector('[data-cr="fwd"]'); if (rb) rb.click(); var f2 = g.cfg().fwd; document.getElementById('gCfg').querySelector('[data-cx="close"]').click();
        ck('⚙ 설정 판 — 열림 · 앞 범위 1km 로 바꾸면 바로 반영 · ↺ 로 기본값 · 닫힘', op && f1 === 1000 && f2 === 2000 && cf.style.display === 'none', [op, f1, f2].join(' / '));
        /* v0.12.0 막힘 배율 — ../data/eta-cal.json 을 읽었고 · 평일 08:30 = 출근 칸 값 · 끄면 1 · 가르고가 쓰는 값 = TT.calF(지금) */
        var wk = new Date(2026, 9, 14, 8, 30).getTime(), f1c = TT.calF(wk), why = TT.calWhy(wk); var cf0 = localStorage.getItem('tg_tt_cfg'); TT.set('calOn', 0); var f0c = TT.calF(wk); if (cf0 == null) localStorage.removeItem('tg_tt_cfg'); else localStorage.setItem('tg_tt_cfg', cf0);   /* 시험 전 그대로 — 「남은 것 없음」 검사 */
        ck('⏱ 막힘 배율(ITS 실측) — 표를 읽음 · 평일 08:30 출근 칸 ×1~2.5 · 끄면 ×1 · 가르고가 지금 쓰는 값 = TT.calF(지금)', f1c > 1 && f1c <= 2.5 && /평일 출근/.test(why) && f0c === 1 && Math.abs(window.GARGO.calF() - TT.calF(Date.now())) < 1e-9, why + ' · 끔 ' + f0c + ' · 지금 ' + window.GARGO.calF());
      } catch (e) { ck('v0.11.0 검사', false, e.message); }
      /* 건물 이름 찾기 — 칸을 띄우지 않아도 이름 목록(bld6/names.json)으로 */
      /* 건물 이름 검사는 맨 끝으로 — 칸 151개를 한꺼번에 받는 시험과 겹치면 이름 목록(700KB) 받기가 늦다(2026-10-15 두 번 「이름 0」) */
      ck('밤 22~06시에는 속도 권고가 안 나온다(모의 주행 4초)', seen === 0, '신호 판 ' + shown + '번 봄 · 권고 글 ' + seen + '번');
      ck('안내 화면이 뜬다(위 띠)', (document.getElementById('gTop') || {}).offsetHeight > 0, String((document.getElementById('gTop') || {}).innerText || '').split(String.fromCharCode(10)).join(' · '));
      /* 켜놓고 다니기(v0.6.0) — 안내를 끝내고 길을 지운 뒤: 반포대로를 북쪽으로 가는 자리·속도를 넣으면 진행 방향이 위로 돌고, 내 길 앞의 신호가 「남쪽에서 직진」 값으로 잡힌다 */
      try { var b1 = document.getElementById('gStop'); if (b1) b1.click(); var b2 = document.getElementById('gClr'); if (b2) b2.click();
        ck('목적지가 없으면 「켜놓고 다니기」 단추가 있다', !!document.getElementById('gCruise'));
        var bt0 = String(document.getElementById('gBot').innerText || ''); ck('목적지가 없으면 지금 색을 아는 신호 수와 까닭을 보인다(v0.6.2)', /지금 색·남은 초를 아는 신호 \d+곳/.test(bt0), bt0.replace(/\s+/g, ' ').slice(0, 80));
        var pa = g.P(127.0113, 37.4835), pb = g.P(127.0076, 37.4925), rr = g.findRoute(pa[0], pa[1], pb[0], pb[1], Date.now() / 1000, null), ii = Math.floor(rr.pts.length / 2 / 3) * 2, hx = rr.pts[ii], hy = rr.pts[ii + 1], hd = (Math.atan2(rr.pts[ii + 2] - hx, -(rr.pts[ii + 3] - hy)) * 180 / Math.PI + 360) % 360;
        g.setMe(hx, hy, 5, hd, 11); var onC = g.cruise(), A = g.ahead(), top2 = String(document.getElementById('gTop').innerText || '');
        ck('켜놓고 다니기가 켜진다(위 띠 · 진행 방향이 위)', onC === true && /켜놓고 다니기/.test(top2) && Math.abs(g.view.rot - hd) < 1 && g.view.s >= 0.25 && g.view.s <= 0.9 && Math.abs(g.view.s - Math.max(0.25, Math.min(0.9, document.getElementById('gMap').clientHeight * 0.68 / g.cfg().fwd))) < 0.01, 'rot ' + Math.round(g.view.rot) + ' / 방위 ' + Math.round(hd) + ' · 배율 ' + g.view.s.toFixed(2));
        var asc = A && A.sigs.every(function (x, i2) { return x.d <= g.cfg().fwd && (!i2 || x.d >= A.sigs[i2 - 1].d); });
        ck('내 길 앞 신호가 잡힌다(앞 범위 = 설정 · 기본 2km 안 · 가까운 순 · 들어가는 쪽 = 남쪽 언저리)', !!(A && A.sig && asc && ['st', 'se', 'sw'].indexOf(A.sig.side) >= 0), A && A.sig ? A.nm + ' · ' + A.sig.nm + ' ' + Math.round(A.sig.d) + 'm · ' + A.sig.side + ' · 모두 ' + A.sigs.length + '곳' : '없음');
        /* v0.6.1 독립 검수 ① — 길을 따라 자리를 옮겨 가며 위 띠의 「시속 N」이 그 길 제한속도를 넘지 않는다(소통 값이 제한보다 높아도 숫자를 안 보임) */
        var overC = [], seenC = 0; for (var pi = 0; pi + 3 < rr.pts.length; pi += 6) { var x1 = rr.pts[pi], y1 = rr.pts[pi + 1], h1 = (Math.atan2(rr.pts[pi + 2] - x1, -(rr.pts[pi + 3] - y1)) * 180 / Math.PI + 360) % 360; g.setMe(x1, y1, 5, h1, 11); var A1 = g.ahead(), tt = String(document.getElementById('gTop').innerText || ''), mm1 = /시속 (\d+)/.exec(tt); if (mm1) { seenC++; if (!A1 || +mm1[1] > A1.lim) overC.push(mm1[1] + '>' + (A1 && A1.lim)); } }
        ck('켜놓고 다니기 · 소통 시속 숫자가 제한속도를 넘지 않는다', overC.length === 0, '숫자 본 곳 ' + seenC + ' · 넘은 곳 ' + overC.length + ' ' + overC.slice(0, 3).join(' '));
        /* ⑤ — 위치가 5초 넘게 안 오면 「끊겼다」 · 앞 신호 판을 감춘다 */
        g.setMe(hx, hy, 5, hd, 11); g.state().me.t = Date.now() - 8000; g.paint(); var top4 = String(document.getElementById('gTop').innerText || '');
        ck('위치가 끊기면 지난 자리 값을 「지금」처럼 보이지 않는다', /위치가 끊겼다/.test(top4) && document.getElementById('gSig').style.display === 'none', top4.replace(/\s+/g, ' ').slice(0, 40));
        g.setMe(hx, hy, 5, hd, 11);
        /* v0.6.1 — 방향을 모르면(멈춘 채 켬 · 기기가 방위를 안 줌) 앞 신호를 지어내지 않는다 */
        g.state().me.hk = false; g.setMe(hx, hy, 5, null, 0); var A0 = g.ahead(), top3 = String(document.getElementById('gTop').innerText || '');
        ck('방향을 모르면 앞 신호를 보이지 않는다(「방향을 잡는 중」)', A0 === null && /방향을 잡는 중/.test(top3) && document.getElementById('gSig').style.display === 'none', (A0 === null ? 'ahead 없음' : 'ahead 있음') + ' · ' + top3.replace(/\s+/g, ' ').slice(0, 40));
        g.setMe(hx, hy, 5, hd, 11); ck('다시 움직이면 앞 신호가 돌아온다', !!(g.ahead() && g.ahead().sig));
        ck('끝내면 지도가 북쪽 위로 돌아오고 찾기 칸이 다시 보인다', g.cruise(false) === false && g.view.rot === 0 && !document.body.classList.contains('guiding') && document.getElementById('gFind').style.display !== 'none');
      } catch (e) { ck('켜놓고 다니기 검사', false, e && e.message); }
      /* v0.15.0 고속도로 모드 — 신사역 → 예술의전당(경부) 길의 나들목 차례 · 경부(제한 70 이상)에서만 안내 판 줄 */
      try { var ic9 = r9 ? (g.icOn(r9) || []).map(function (o) { return o.nm; }) : [], ia = ['반포IC', '서초IC'].map(function (n) { return ic9.indexOf(n); })   /* 경부에 오르는 나들목은 그때 소통에 따라 한남·잠원·반포로 달라진다 — 반포IC → 서초IC 차례만 본다 */, e70 = r9 ? r9.lims.filter(function (q) { return q[1] >= 70; })[0] : null, ln = e70 ? g.icLine(r9, e70[0] + 30) : '', ln0 = g.icLine(r9, 10);
        ck('🛣 고속도로 모드 — 경부 길의 나들목이 반포IC → 서초IC 차례 · 경부 위에서만 「🛣 … km · 분」 줄', ia.every(function (x, i) { return x >= 0 && (!i || x > ia[i - 1]); }) && /🛣/.test(ln) && /km|m ·/.test(ln) && ln0 === '', ic9.join('›') + ' · ' + ln.replace(/<[^>]+>/g, '').slice(0, 60)); } catch (e) { ck('고속도로 모드 검사', false, e.message); }
      var dnF = function () { var d1 = g.dongAt(127.0076, 37.4919), d2 = g.dongAt(127.1000, 37.5133), d3 = g.dongAt(126.9784, 37.5666); ck('📍 지금 위치 — 행정동 찾기(서초역 = 서초구 · 잠실역 = 송파구 · 시청 = 중구)', /^서초구 /.test(d1) && /^송파구 /.test(d2) && /^중구 /.test(d3), [d1, d2, d3].join(' · ')); };
      var mkF = function () { var s5 = g.P(127.0076, 37.4919), t5 = g.P(127.0341, 37.4844), r5 = g.findRoute(s5[0], s5[1], t5[0], t5[1], Date.now() / 1000, null); if (!r5) { ck('길 위 표시 검사', false, '길 없음'); return; }   /* 앞 시험이 길을 지웠다 — 서초역 → 양재역을 새로 */ var M5 = g.routeMarks(r5) || [], ty = {}; M5.forEach(function (m) { ty[m.t] = (ty[m.t] || 0) + 1; }); var inc = M5.every(function (m, i, A) { return !i || m.s >= A[i - 1].s; });
        ck('⚠ 길 위 표시 — 서초역 → 양재역 길에 사고 다발 교차로(10년 50건 넘게)·카메라·보호구역이 지나는 차례로', !!ty.r && inc && /양재역/.test(M5.filter(function (m) { return m.t === 'r'; }).map(function (m) { return m.nm; }).join(',')), JSON.stringify(ty) + ' · ' + M5.slice(0, 4).map(function (m) { return m.t + ':' + m.nm + '@' + Math.round(m.s); }).join(' '));
        var dh = g.dcard('r', 300, '사고 다발 교차로', '양재역 · 10년 172건'); ck('🪧 위험 카드 = 표지(그림) + 큰 남은 거리 + 이름', /<svg/.test(dh) && /<b>300m<\/b>/.test(dh) && /양재역/.test(dh), dh.replace(/<svg[\s\S]*?<\/svg>/, '[표지]').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()); };
      var buF = function () { var s6 = g.P(127.0275, 37.4985), t6 = g.P(127.0333, 37.4870), r6 = g.findRoute(s6[0], s6[1], t6[0], t6[1], Date.now() / 1000, null); if (!r6) { ck('버스전용차로 검사', false, '길 없음'); return; } var B6 = g.busOn(r6) || [], e6 = g.emLane(null, 0, r6);
        ck('🚌 긴급 출동 빠른 차로 — 강남역 → 양재역(강남대로)은 중앙버스전용차로(OSM · §15③ 단서) · 반포대로(전용차로 없음)는 1차로', B6.some(function (q) { return q[2] === 'busway' && q[1] - q[0] >= 150; }) && /중앙버스전용차로/.test(e6.w) && /§15③/.test(e6.why) && (function () { var s7 = g.P(127.0075, 37.4918), t7 = g.P(127.0034, 37.5021), r7 = g.findRoute(s7[0], s7[1], t7[0], t7[1], Date.now() / 1000, null); return !r7 || g.emLane(null, 0, r7).w === '1차로'; })(), B6.map(function (q) { return Math.round(q[0]) + '~' + Math.round(q[1]) + q[2]; }).join(' ') + ' · ' + e6.w + ' ' + e6.why); };
      var bnF = function () { var rf = g.localFind('롯데월드몰').concat(g.localFind('송파구청')); ck('건물 이름 찾기(롯데월드몰·송파구청 · 칸을 안 띄워도)', rf.filter(function (x) { return x[0] === '🏢'; }).length >= 2, rf.slice(0, 3).map(function (x) { return x[0] + x[1]; }).join(' · ') + ' · 이름 ' + g.bld().names + ' · ' + JSON.stringify(g.bld())); };
      var bnP = g.bld().names ? Promise.resolve() : Promise.resolve(g.bnmLoad());
      var dnP = Promise.resolve(g.dongLoad()); bnP = Promise.all([bnP, dnP]); bnP = Promise.all([bnP, Promise.resolve(g.risk()), Promise.resolve(g.alrLoad()), Promise.resolve(g.busLoad())]).then(function () { return new Promise(function (ok) { setTimeout(ok, 600); }); });
      Promise.race([bnP, new Promise(function (ok) { setTimeout(ok, 10000); })]).then(function () { setTimeout(function () { try { bnF(); } catch (e) { ck('건물 이름 찾기', false, e.message); } try { buF(); } catch (e) { ck('버스전용차로 검사', false, e.message); } try { mkF(); } catch (e) { ck('길 위 표시 검사', false, e.message); } try { dnF(); } catch (e) { ck('지금 위치 검사', false, e.message); }
      var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
      send(); }, 50); }); }, 4200);
  }
})();
