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
      var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
      setTimeout(send, 80); }, function (e) { ck('길 자료(nav) 읽기', false, String(e)); send(); }); }, 3500);
    }
  }
})();
