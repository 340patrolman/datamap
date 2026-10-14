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
    /* 레이어 판 — 새 기기에서는 켜진 것이 없는 묶음이 접혀 있다 */
    try { document.getElementById('m2dFold').click(); var gs = [].map.call(document.querySelectorAll('#m2dPanel .gc'), function (b) { return b.getAttribute('aria-expanded'); }), nOpen = gs.filter(function (x) { return x === 'true'; }).length; ck('레이어 판 묶음이 접힌 채로 열린다(켜진 것이 든 묶음만 펼침)', gs.length > 8 && nOpen < gs.length, '묶음 ' + gs.length + ' · 펼침 ' + nOpen + ' · 판 높이 ' + document.getElementById('m2dPanel').scrollHeight + 'px'); } catch (e) { ck('레이어 판이 열린다', false, e.message); }
    var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
    send();
  }
})();
