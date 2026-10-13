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
    var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
    send();
  }
})();
