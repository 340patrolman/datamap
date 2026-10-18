/* 데이터 압축지도 값 검사 — tools/check/pagecheck.py 가 화면 끝에 끼워 넣는다(사이트에는 안 올라간다).
   보는 것: 지도가 열린다(문법) · 캔버스에 크기가 있다 · 받은 자리(#lat·lon)로 간다 · 다시 그리기 · 화면 오류 0 */
(function () {
  var C = [], t0 = Date.now();
  function ck(n, ok, got) { C.push([n, !!ok, got == null ? '' : String(got).slice(0, 160)]); }
  function send() { var s = btoa(unescape(encodeURIComponent(JSON.stringify({ checks: C })))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''), n = Math.ceil(s.length / 1500), id = String(Date.now());
    for (var i = 0; i < n; i++) (new Image()).src = '/__r?p=' + window.__PAGE + '&k=' + id + '&i=' + i + '&n=' + n + '&d=' + s.substr(i * 1500, 1500); }
  var poll = setInterval(function () {
    var m = window.TGMap2D;
    if (m && m.view) { clearInterval(poll); setTimeout(function () { try { run(m); } catch (e) { ck('검사 스크립트가 끝까지 돌았다', false, e && e.message); send(); } }, 7000); }
    else if (Date.now() - t0 > 40000) { clearInterval(poll); ck('지도가 열린다(문법)', false, (window.__ERR || []).join(' | ') || 'TGMap2D 없음'); send(); }
  }, 300);
  function run(m) {
    ck('지도가 열린다(문법)', true);
    var cv = document.querySelector('canvas'); ck('캔버스에 크기가 있다', !!cv && cv.width > 100 && cv.height > 100, cv ? cv.width + '×' + cv.height : '없음');
    var v = m.view; ck('보는 자리 값이 숫자다', v && isFinite(v.s) && v.s > 0, v ? JSON.stringify(v).slice(0, 120) : '');
    var t = performance.now(); try { m.draw(); ck('다시 그리기', true, Math.round(performance.now() - t) + 'ms'); } catch (e) { ck('다시 그리기', false, e.message); }
    try { var b = m.boot && m.boot(); ck('여는 시간 기록이 있다', !!b, b ? JSON.stringify(b).slice(0, 140) : ''); } catch (e) { ck('여는 시간 기록이 있다', false, e.message); }
    var gate = document.documentElement.className + ' ' + (document.body ? document.body.className : ''); ck('확인코드 칸에 막혀 있지 않다(저장값으로 통과)', !/gated/.test(gate), gate.trim());
    /* 잇기 — 받은 자리(서초역 37.4919, 127.0076)의 카드에 「네비 가르고」 단추가 있고, 누르면 그 자리로 가르고가 열린다 */
    var nb = document.querySelector('#m2dCard [data-nav]'); ck('카드에 「네비 가르고로 여기까지」 단추(서초 둘레)', !!nb, nb ? nb.textContent : '없음 — 카드: ' + String((document.querySelector('#m2dCard h3') || {}).textContent));
    if (nb) { var op = [], wo = window.open; window.open = function (u) { op.push(String(u)); return null; }; nb.click(); window.open = wo; var mm = /^gargo\/#to=(-?[\d.]+),(-?[\d.]+)/.exec(op[0] || '');
      ck('단추가 가르고를 그 자리로 연다(500m 안)', !!mm && Math.abs(+mm[1] - 37.4919) < 0.0045 && Math.abs(+mm[2] - 127.0076) < 0.0056, op[0]); }
    /* 도구 모음(v2.219.0) — 오른쪽 기둥은 넷 · 🧰 를 누르면 도구 열 가지 · 범례를 고르면 범례가 열리고 도구 판은 닫힌다 */
    var col = [].filter.call(document.querySelectorAll('#m2dZoom button'), function (b) { return b.offsetHeight > 0; }).map(function (b) { return b.id; }); ck('오른쪽 단추 기둥 = ＋ － 📍 🧰', col.join(',') === 'm2dIn,m2dOut,m2dHereB,m2dToolB', col.join(','));
    var tb = document.getElementById('m2dToolB'), tp = document.getElementById('m2dTool'); if (tb && tp) { tb.click(); var its = [].map.call(tp.querySelectorAll('button[data-tool]'), function (b) { return b.getAttribute('data-tool'); }); ck('도구 판이 열리고 도구가 다 있다', tp.classList.contains('on') && ['rad', 'biz', 'prd', 'gdr', 'tax', 'nav', 'fit', 'leg'].every(function (k) { return its.indexOf(k) >= 0; }), its.join(' '));
      ck('도구 판이 화면 밖으로 안 나간다', tp.getBoundingClientRect().left >= 0 && tp.scrollWidth <= tp.clientWidth + 1, Math.round(tp.getBoundingClientRect().left) + ' · ' + tp.scrollWidth + '/' + tp.clientWidth);
      var lg = tp.querySelector('[data-tool=leg]'); if (lg) lg.click(); ck('범례를 고르면 범례가 열리고 도구 판은 닫힌다', document.body.classList.contains('legon') && !tp.classList.contains('on')); if (document.body.classList.contains('legon')) document.getElementById('m2dLegB').click(); }
    /* 창 관리(v2.220.0) — 방금 연 창이 맨 위 · 겹친 창이 있으면 칩이 뜨고, 칩을 누르면 그 창이 맨 위로(레이어 판을 연 채 도구 판을 연다) */
    try { var z = function (id) { return +getComputedStyle(document.getElementById(id)).zIndex || 0; }; document.getElementById('m2dFold').click();
      setTimeout(function () { try { tb.click(); } catch (e0) {}
        setTimeout(function () { try { var ws = m.wins(), bar = document.getElementById('m2dWin'), chips = bar ? bar.querySelectorAll('[data-win]') : [];
            ck('방금 연 도구 판이 레이어 판보다 위다', ws[ws.length - 1] === 'm2dTool' && z('m2dTool') > z('m2dPanel'), ws.join('>') + ' · z ' + z('m2dTool') + '/' + z('m2dPanel'));
            ck('겹친 창 칩이 뜬다(도구 · 레이어)', bar.style.display === 'flex' && chips.length >= 2, [].map.call(chips, function (b) { return b.textContent; }).join(' · '));
            var cb = bar.querySelector('[data-win=m2dPanel]'); if (cb) { cb.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); var w2 = m.wins(); ck('칩을 누르면 그 창이 맨 위로 온다', w2[w2.length - 1] === 'm2dPanel' && z('m2dPanel') > z('m2dTool'), w2.join('>')); }
            if (tp.classList.contains('on')) tb.click(); var cx = document.querySelector('#m2dPanel [data-close]'); if (cx) cx.click(); } catch (e2) { ck('창 관리 검사', false, e2.message); }
          fin(); }, 400); }, 500); } catch (e) { ck('창 관리 검사', false, e.message); fin(); }
    function fin() {
    /* 레이어 판 — 새 기기에서는 켜진 것이 없는 묶음이 접혀 있다 */
    try { document.getElementById('m2dFold').click(); var gs = [].map.call(document.querySelectorAll('#m2dPanel .gc'), function (b) { return b.getAttribute('aria-expanded'); }), nOpen = gs.filter(function (x) { return x === 'true'; }).length; ck('레이어 판 묶음이 접힌 채로 열린다(켜진 것이 든 묶음만 펼침)', gs.length > 8 && nOpen < gs.length, '묶음 ' + gs.length + ' · 펼침 ' + nOpen + ' · 판 높이 ' + document.getElementById('m2dPanel').scrollHeight + 'px'); } catch (e) { ck('레이어 판이 열린다', false, e.message); }
    /* v2.222.0 🧩 교차로 관계(온톨로지 코어 v1 · Phase 2) — 서초역 카드의 「이 자리의 관계」 안 단추를 누르면 서초역사거리의 사고·주 위반·과거 조치가 펼쳐진다 · 누르기 전에는 코어를 받지 않는다 */
    var ob = document.querySelector('#m2dCard [data-onto]'); ck('카드에 「🧩 교차로 관계 보기」 단추(서초)', !!ob, ob ? '' : '없음'); ck('누르기 전에는 온톨로지 코어를 받지 않는다', !m.onto());
    if (ob) { var det = ob.closest('details'); if (det) det.open = true; ob.click(); }
    try { m.petGet(); m.uticGet(); m.sbhGet(); m.sigUGet(); m.pbzGet(); m.pbzSd('11'); } catch (e) {} try { m.econLoad && m.econLoad(); } catch (e) {}   /* v2.230.0 반려동물 — 아래 길 자료 검사 뒤에 본다 */
    setTimeout(function () { var bx = document.getElementById('m2dOnto'), tx = bx ? String(bx.innerText || '') : '';
      ck('관계 패널이 펼쳐진다 — 교차로 · 사고 해마다 · 주 위반 근거 · 과거 조치 · 비슷한 교차로', /서초역사거리/.test(tx) && /① 사고/.test(tx) && /② 주 위반/.test(tx) && /④ 과거 조치/.test(tx) && /⑤ 비슷한/.test(tx) && /반포대로 축개선/.test(tx), tx.replace(/\s+/g, ' ').slice(0, 120));
      /* v2.223.0 신고 차량 예측 — 설정 세트 셋이 서로 다른 결과 · 🔒 중요업무 두 줄 · 밖으로 나가는 요청 0 · 남기는 것 없음 */
      var P0 = m.prd(), V0 = m.vip(), ls0 = Object.keys(localStorage).sort().join(','), h0 = location.hash; window.__NET = []; var of = window.fetch, ox = XMLHttpRequest.prototype.open, oo = window.open;
      m.navGet().then(function () { try {
        P0.p = m.LL(127.0076, 37.4935); P0.hd = 'nt'; P0.base = Date.now(); P0.ago = 0; P0.wait = 0;
        function sum() { var R = P0.res; if (!R || R.err) return null; var n = 0; Object.keys(R.lab).forEach(function (ix) { if (R.lab[ix].b <= 120) n++; }); return { n2: n, tt: R.tt.slice(0, 3).map(function (q) { return Math.round(q.t); }).join(','), stops: Object.keys(R.stops).length }; }
        P0.set = 'n'; P0.sig = 1; P0.k = 1; m.prdRun(); var r1 = sum(); P0.set = 'r'; P0.sig = 0; P0.k = TT.cfg().runK; m.prdRun(); var r2 = sum();
        window.fetch = function (u) { __NET.push(String(u && u.url || u)); return of.apply(this, arguments); }; XMLHttpRequest.prototype.open = function (mm, u) { __NET.push(String(u)); return ox.apply(this, arguments); }; window.open = function (u) { __NET.push('open ' + u); return null; };
        P0.set = 'v'; V0.cp = [m.LL(127.0076, 37.4919), m.LL(127.0142, 37.4934), m.LL(127.0341, 37.4844)]; V0.base = 0; V0.fast = null; m.vipRun(); m.prdShow(); var R3 = V0.res && V0.res.V, card = String((document.getElementById('m2dCard') || {}).innerText || '');
        ck('신고 차량 예측 — 일반·도주 결과가 다르다(도주 = 신호 무시 · 평균 ×' + TT.cfg().runK + ' → 2분 안에 더 많은 길) · 일반은 적색에 서는 교차로를 낸다', r1 && r2 && r2.n2 > r1.n2 && r2.stops === 0, JSON.stringify([r1, r2]));
        ck('🔒 중요업무 — 서초역 → 교대역 → 양재역 지점 둘 · 기본 60 · 직접 입력 없으면 가장 이른 = 100 · 가장 이른 쪽이 빠르다', R3 && !R3.err && R3.base.cps.filter(function (c) { return /^(출발|지점|도착)/.test(c.nm); }).length === 2 && R3.base.v === 60 && R3.fastV === 100 && !R3.typed && R3.fast.sec < R3.base.sec && R3.base.parts.sig === 0, R3 ? TT.fmt(R3.base.sec) + ' / ' + TT.fmt(R3.fast.sec) + ' · ' + (V0.res.m / 1000).toFixed(1) + 'km' : (V0.res && V0.res.err) || '없음');
        ck('🔒 중요업무 카드 — 두 줄 · 「교차로 통제 개시는 가장 이른 도착 시각 기준」 · 지점별 표 · 「중요업무」 말만', /예상 도착/.test(card) && /가장 이른 도착/.test(card) && /교차로 통제 개시는/.test(card) && /도착 · /.test(card) && !/행차|경호|VIP/.test(card), card.replace(/\s+/g, ' ').slice(0, 90));
        var cd = document.getElementById('m2dCard'); ck('🔒 중요업무 카드에는 「의견·PC로 보내기」가 없다', !cd.querySelector('[data-pc],[data-fb]'), cd.querySelectorAll('[data-pc],[data-fb]').length + '개');
        var ix3 = R3 ? R3.base.cps.filter(function (c) { return /^🚦 /.test(c.nm); }) : [], inc = R3 && R3.base.cps.every(function (c, i, A) { return !i || c.t > A[i - 1].t; });
        ck('🔒 교차로마다 도착 — 신호 교차로 줄이 3곳 넘게 · 시각이 차례로 늘어난다 · 카드에 「정속 가정」', ix3.length >= 3 && inc && /정속 가정/.test(String((document.getElementById('m2dCard') || {}).innerText || '')), ix3.slice(0, 3).map(function (c) { return c.nm + ' +' + TT.mmss(c.t); }).join(' · '));
        /* v2.226.0 관내 밖 고속도로 기준점 — 판교IC → 한남대교남단(이름으로 고름) = 경부고속도로로 양재IC → 서초IC → 반포IC 차례 · 강남대로로 빠지지 않는다 */
        var cpS = V0.cp; V0.cp = []; ['판교IC', '한남대교남단'].forEach(function (q) { var f = m.vipFind(q); if (f) { var p9 = [f.p[0], f.p[1]]; p9.wide = 1; p9.nm = f.nm; V0.cp.push(p9); } }); V0.base = 90; m.vipRun();
        var RG = V0.res && V0.res.V, gN = RG ? RG.base.cps.map(function (c) { return c.nm; }) : [], gi = ['🛣 양재IC', '🛣 서초IC', '🛣 반포IC'].map(function (n) { return gN.indexOf(n); });
        ck('🔒 중요업무 관내 밖 — 판교IC → 한남대교남단 · 경부 양재IC → 서초IC → 반포IC 차례 · 강남역 안 지남 · 이름 「도착 · 한남대교」', V0.cp.length === 2 && gi.every(function (x) { return x >= 0; }) && gi[0] < gi[1] && gi[1] < gi[2] && !gN.some(function (n) { return /강남역/.test(n); }) && /^도착 · 한남대교/.test(gN[gN.length - 1]), gN.filter(function (n) { return /^🛣|^도착/.test(n); }).map(function (n, i) { var c = RG.base.cps[gN.indexOf(n)]; return n + ' +' + TT.mmss(c.t); }).join(' · '));
        V0.cp = []; ['여의하류IC', '청담대교남단'].forEach(function (q) { var f = m.vipFind(q); if (f) { var p9 = [f.p[0], f.p[1]]; p9.wide = 1; V0.cp.push(p9); } }); V0.base = 80; m.vipRun();   /* 이름 찾기는 앞 지점에서 가까운 것 — 하나씩 차례로 넣는다 */
        var RO = V0.res && V0.res.V, oN = RO ? RO.base.cps.map(function (c) { return c.nm; }) : [], oi = ['🛣 여의상류IC', '🌉 한강대교', '🌉 동작대교', '🌉 한남대교', '🌉 성수대교', '🌉 영동대교'].map(function (n) { return oN.indexOf(n); });
        ck('🔒 중요업무 올림픽대로 — 여의하류IC → 청담대교남단 · 여의상류IC·한강대교·동작대교·한남대교·성수대교·영동대교 차례(다리 밑을 지나는 자리)', oi.every(function (x, i) { return x >= 0 && (!i || x > oi[i - 1]); }), oi.join(',') + ' · ' + oN.filter(function (n) { return /^🌉/.test(n); }).join(' '));
        V0.cp = cpS; V0.base = 0; m.vipRun();
        var wk = new Date(2026, 9, 14, 17, 30).getTime(), fk = TT.calF(wk), whyk = TT.calWhy(wk); var cf0 = localStorage.getItem('tg_tt_cfg'); TT.set('calOn', 0); var fk0 = TT.calF(wk); if (cf0 == null) localStorage.removeItem('tg_tt_cfg'); else localStorage.setItem('tg_tt_cfg', cf0);   /* 시험 전 그대로 — 「남은 것 없음」 검사 */
        ck('⏱ 막힘 배율(ITS 실측) — 표를 읽음 · 평일 17:30 퇴근 칸 ×1~2.5 · 끄면 ×1 · 신고 예측이 쓰는 값 = TT.calF(지금)', fk > 1 && fk <= 2.5 && /평일 퇴근/.test(whyk) && fk0 === 1 && Math.abs(m.prdF() - TT.calF(Date.now())) < 1e-9, whyk + ' · 끔 ' + fk0 + ' · 지금 ' + m.prdF());
        /* v2.228.0 이웃 메움 — 같은 이름으로 곧게 이어지는 다음 링크에만 실시간 20km/h 를 주면 앞 링크도 20 으로 메운다 · 이름 다른 링크는 안 메운다 */
        var NG = m.navg(), o9 = null, q9 = null; NG.L.some(function (o) { if (!o.nm) return false; var nx = (NG.out[o.t] || []).filter(function (q) { return q.nm === o.nm && q.t !== o.f; }); if (nx.length === 1) { o9 = o; q9 = nx[0]; return true; } return false; });
        var MM = { m: {} }; if (q9) MM.m[q9.id] = 20; var FF = q9 ? m.prdFill(MM) : null, oth = NG.L.filter(function (o) { return o.nm && o.nm !== (o9 && o9.nm) && (NG.out[o.t] || []).length; })[0];
        ck('🧩 신고 예측 이웃 메움 — 같은 길 다음 링크 실시간 20km/h → 값 없는 앞 링크 20 · 다른 이름 길은 안 메움', !!FF && Math.abs(FF[o9.id] - 20) < 1e-6 && !(oth && FF[oth.id] > 0 && oth.nm !== q9.nm), o9 ? o9.nm + ' ' + (FF && FF[o9.id]) : '짝 없음'); m.prdFill(null);
        /* v2.229.0 🎥 교차로 CCTV(UTIC) — 카드에 출처 글 · TOPIS 누리집 단추 · 정차 중·동승자 · 영상 주소·열쇠 없음 */
        var uc = m.utcCard({ t: { id: 'L010003', nm: '63빌딩', gu: '11560', how: '이름 맞대기(C)' } }); ck('🎥 교차로 CCTV 카드 — 「경찰청 도시교통정보센터(UTIC) 제공」 · TOPIS 공식 누리집 · 정차 중·동승자만 · 영상 주소 없음', /경찰청 도시교통정보센터\(UTIC\) 제공/.test(uc) && /data-utcgo/.test(uc) && /정차 중이거나 동승자만/.test(uc) && !/https?:\/\/[^"']*(cctv|stream|m3u8)/i.test(uc), uc.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').slice(0, 90));
        V0.base = 80; m.vipRun(); var R8 = V0.res.V; V0.base = 0; V0.fast = 110; m.vipRun(); var R9 = V0.res.V; V0.fast = null;
        ck('🔒 속도 80 이면 예상이 더 빨라지고 · 「더 빠름」 110 이면 가장 이른 = 110', R8.base.v === 80 && R8.base.sec < R3.base.sec && R9.fastV === 110 && R9.typed, [TT.fmt(R8.base.sec), R9.fastV].join(' / '));
        V0.fast = 80; m.vipRun(); var R4 = V0.res.V; V0.fast = 130; m.vipRun(); var R5 = V0.res.V;
        ck('🔒 직접 입력 80 이면 가장 이른 = 80 · 130 은 받지 않는다(범위 30~120)', R4.fastV === 80 && R4.typed && !!R5.err, [R4.fastV, R5.err].join(' / '));
        var NET = __NET.slice(); window.fetch = of; XMLHttpRequest.prototype.open = ox; window.open = oo;
        var blocked = null; window.fetch('https://api.vworld.kr/req/x').then(function () { blocked = false; }, function (e) { blocked = /중요업무/.test(String(e && e.message)); });
        ck('🔒 중요업무 중 밖으로 나간 요청 0 · 이 기기에 남은 것 없음 · 주소창 그대로', NET.length === 0 && Object.keys(localStorage).sort().join(',') === ls0 && location.hash === h0, NET.slice(0, 3).join(' | ') || ('요청 0 · 저장 열쇠 그대로'));
        var x9 = document.getElementById('m2dX'); if (x9) x9.click(); ck('🔒 카드를 닫으면 중요업무 지점·시각이 지워진다', V0.cp.length === 0 && !V0.res && P0.set === 'n', V0.cp.length + ' · ' + P0.set);
        setTimeout(function () { ck('🔒 중요업무 카드가 열린 동안 바깥 서비스 요청은 막는다(브이월드 시험 요청 → 거부)', blocked === true, String(blocked)); }, 0);
        V0.cp = []; V0.res = null; V0.fast = null; P0.set = 'n'; P0.sig = 1; P0.k = 1; P0.p = null; P0.res = null;
      } catch (e) { ck('신고 차량 예측 v2.223.0 검사', false, e.message); }
      try { var nb0 = document.querySelectorAll('.m2d-stamp').length; m.stampAt(100, 100, '#dc2626'); var st1 = document.querySelectorAll('.m2d-stamp').length, sc = [].slice.call(document.styleSheets).some(function (ss) { try { return [].slice.call(ss.cssRules).some(function (r) { return /m2dBreathe/.test(r.cssText) && /prefers-reduced-motion/.test(r.cssText); }); } catch (e2) { return false; } });
        ck('👆 찍히는 느낌 — 지점 표시 「쿵」 요소가 생기고(1.1초 뒤 사라짐) · 숨 쉬는 단추·찍힘 움직임은 「움직임 줄이기」가 아닐 때만 · 되풀이 6번까지(끝없지 않음) (v2.239.0)', st1 === nb0 + 1 && sc, '찍힘 ' + nb0 + '→' + st1 + ' · 움직임 줄이기 규칙 ' + sc); } catch (e) { ck('찍히는 느낌 검사', false, e.message); }
      try { var nS = m.sggN(), iS = -1, iG = -1; for (var k = 0; k < nS; k++) { var gg = m.sggAt(k); if (gg.sido === '서울특별시' && gg.name === '서초구') iS = k; if (gg.sido === '경기도' && gg.name === '성남시') iG = k; }
        var vB = m.taxVal('b100g', iS), vW = m.taxVal('wagep', iS), vG = m.taxVal('wagep', iG), lg1 = (m.taxLegend('b100g') || [])[1] || '', lg2 = (m.taxLegend('wagep') || [])[1] || '';
        ck('💳 세금 통계 층 — 서초구 생활업종 합 증감 % · 서초구 1인당 총급여(만 원) · 성남시(일반구 셋)도 값 · 두 범례에 「시군구 단위 — 동네 차이는 반영 안 됨」 · 총급여·종합소득 따로 고름(더하지 않음) (v2.238.0)', vB && vB.v != null && vW && vW.v > 3000 && vG && vG.v > 2000 && /동네 차이는 반영 안 됨/.test(lg1) && /동네 차이는 반영 안 됨/.test(lg2) && /data-txw="inc"/.test(lg2) && /더하지 않는다/.test(lg2), (vB ? vB.v.toFixed(1) + '%' : '-') + ' · 서초 ' + (vW ? Math.round(vW.v) : '-') + '만 · 성남 ' + (vG ? Math.round(vG.v) : '-') + '만'); } catch (e) { ck('세금 통계 층 검사', false, e.message); }
      try { var PZ = m.pbz() || {}, dv15 = document.createElement('div'); dv15.innerHTML = m.pbzRows({ k: '11650510', gcd: '11650' }) || ''; var tx15 = dv15.innerText || '';
        ck('🐾 반려동물 산업 — 갈래 10 · 서초구 동물병원 있음 · 동 카드에 이 구 갈래별 수·「해마다 영업 중인 곳」 그래프·출처 · 상호·주소 칸 없음(v2.236.0)', PZ.kinds && PZ.kinds.length === 10 && PZ.gu && PZ.gu['11650'] && PZ.gu['11650'].n[0] > 0 && /반려동물 산업/.test(tx15) && /해마다 영업 중인 곳/.test(tx15) && /LOCALDATA/.test(tx15) && !/상호|사업장명/.test(JSON.stringify(PZ).replace(/상호·주소/g, '')), (PZ.kinds ? PZ.kinds.length : 0) + '갈래 · 서초 병원 ' + (PZ.gu && PZ.gu['11650'] ? PZ.gu['11650'].n[0] : '-') + ' · ' + tx15.replace(/\s+/g, ' ').slice(0, 90)); } catch (e) { ck('반려동물 산업 검사', false, e.message); }
      try { var lv14 = m.sdLive('1552'), dv14 = document.createElement('div'); dv14.innerHTML = m.sigDirHtml('1552') || ''; var tx14 = dv14.innerText || '', n14 = (tx14.match(/[①②③④⑤⑥⑦⑧] /g) || []).length;
        if (tx14) ck('🚦 이수역(1552) 신호 카드 — 계획 + 방향 표로 그리면 머리글이 「경찰청 계획」(받은 값이라 적지 않음) · 받은 값으로 그리면 방향 셋 넘게(지금 시각과 같은 계획 줄의 받은 값을 다른 요일 갈래에서도 씀 · v2.234.0)', lv14 && lv14.ok && (lv14.pd ? /경찰청 계획/.test(tx14) && !/실제로 돈 값/.test(tx14.split('\n')[0]) : n14 >= 3), (lv14 && (lv14.pd ? '계획+방향표' : lv14.xd ? '같은 계획 줄 ' + lv14.tod[0] + '/' + lv14.tod[1] + '시' : '받은 값')) + ' · 방향 ' + n14); } catch (e) { ck('이수역 신호 카드 검사', false, e.message); }
      try { var SU = m.sigu() || [], c0 = SU[0], sp0 = c0 && c0.spots[0], cdU = sp0 ? m.sigUCard(sp0, c0).replace(/<[^>]+>/g, ' ') : '';
        ck('🚦 신호 계획(인천·대구·대전) — 세 도시 읽힘 · 카드에 주기·현시 · 「지금 몇 초 남음」은 셈하지 않는다 · 요일 뜻 확인 안 됨 · 출처 「경찰청 도시교통정보센터(UTIC) 제공」', SU.length === 3 && SU.every(function (q) { return q.spots.length > 1000; }) && /주기/.test(cdU) && /셈하지 않는다/.test(cdU) && /어림/.test(cdU) && /7번\(토\)|1 일/.test(cdU) && /UTIC\) 제공/.test(cdU) && !/sigTick/.test(m.sigUCard(sp0, c0)), SU.map(function (q) { return q.cityKo + ' ' + q.spots.length; }).join(' · ')); } catch (e) { ck('신호 계획(UTIC) 검사', false, e.message); }
      try { var SB = m.sbh(), gn9 = SB ? SB.L.filter(function (x) { return x.n === '강남' && x.l === '2호선'; })[0] : null, cd9 = gn9 ? m.sbhCard(gn9).replace(/<[^>]+>/g, ' ') : '';
        ck('🚉 역 붐빔 — 서울 역 자리·0~23시 몫 · 강남(2호선) 18시가 평소의 1.5배 넘음(시간대 몫) · 오늘 요일 배수(평일/주말)를 곱함 · 카드에 「평일·주말이 섞인 값」·「열쇠 발급 대기」', SB && SB.L.length > 300 && gn9 && gn9.r.length === 24 && gn9.w && Math.abs(gn9.r[18] - gn9.r0[18] * gn9.k) < 0.02 && gn9.r0[18] > 1.5 && /평일·주말이 섞인/.test(cd9) && /열쇠 발급 대기/.test(cd9), SB ? SB.L.length + '역 · 강남 18시 ×' + (gn9 ? gn9.r0[18] + ' × ' + gn9.k + ' = ' + gn9.r[18] : '-') : '안 읽힘'); } catch (e) { ck('역 붐빔 검사', false, e.message); }
      try { var U9 = m.utic(), L9 = U9 ? U9.items.filter(function (r) { return r[13] === 'live-ims'; }) : [], O9 = U9 ? U9.items.filter(function (r) { return r[13] !== 'live-ims' && /^서울/.test(String(r[9] || '')); }) : [];
        ck('🚨 시내 돌발(UTIC) — 서울 10분 파일이 신선하면 서울 줄은 그 파일로(옛 한 장 서울 줄 빼고) · 시각 꼴 YYYY-MM-DD HH:MM · credit 「경찰청 도시교통정보센터(UTIC) 제공」', U9 && /UTIC\) 제공/.test(U9.credit) && (U9.seoul10 ? L9.length > 0 && O9.length === 0 && L9.every(function (r) { return /^\d{4}-\d\d-\d\d \d\d:\d\d$/.test(r[6]) && isFinite(r.p[0]); }) : true), U9 ? (U9.seoul10 ? '서울 10분 ' + L9.length + '건 · 옛 서울 ' + O9.length : '옛 한 장만(서울 10분 파일이 40분 넘음)') + ' · 전체 ' + U9.items.length : '안 읽힘'); } catch (e) { ck('UTIC 돌발 검사', false, e.message); }
      try { var pr = m.petRows({ k: '11650510', gcd: '11650' }), prx = pr.replace(/<[^>]+>/g, ' '), pc = m.petRows({ k: '41281000', gcd: '41281' }).replace(/<[^>]+>/g, ' ');
        ck('🐕 동 카드 반려동물 — 서초구 공식(개 23,515 · 고양이 271 · 가구 1천당 152) · 같은 시·도 순위 막대 · 동 어림은 「어림」 표시 · 고양이 최소값 · 고양시 구는 시 전체 값 · 추정(서초 개 3.9만~4.2만) 다른 색 · 시 단위 값에는 추정 없음', /23,515/.test(prx) && /271/.test(prx) && /152/.test(prx) && /어림/.test(prx) && /최소값/.test(prx) && /고양시 전체 값/.test(pc) && /실제로 기르는 수\(추정\)/.test(prx) && /3\.9만~4\.2만/.test(prx) && !/실제로 기르는/.test(pc), prx.replace(/\s+/g, ' ').slice(0, 160)); } catch (e) { ck('반려동물 카드 검사', false, e.message); }
      var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
      setTimeout(send, 80); }, function (e) { ck('길 자료(nav) 읽기', false, String(e)); send(); }); }, 3500);
    }
  }
})();
