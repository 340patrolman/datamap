/* 역 실측(gargo/measure.html) 값 검사 — tools/check/pagecheck.py 가 끼워 넣는다
   보는 것: 먼저 잴 역 칩 · 스톱워치 세 번 → 평균·편차·「3번 넘게」 · 3초 아래는 안 남김 · 저장 꼴 · 밖으로 나간 요청 0 · 화면 오류 0 */
(function () {
  var C = [];
  function ck(n, ok, got) { C.push([n, !!ok, got == null ? '' : String(got).slice(0, 160)]); }
  function send() { var s = btoa(unescape(encodeURIComponent(JSON.stringify({ checks: C })))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''), n = Math.ceil(s.length / 1500), id = String(Date.now());
    for (var i = 0; i < n; i++) (new Image()).src = '/__r?p=' + window.__PAGE + '&k=' + id + '&i=' + i + '&n=' + n + '&d=' + s.substr(i * 1500, 1500); }
  setTimeout(function () { try {
    var M = window.TGMEAS; ck('역 실측 화면이 열린다(확인코드 통과 · 창구 있음)', !!M && !document.documentElement.classList.contains('gated'));
    var chips = document.querySelectorAll('#mSt button'); ck('먼저 잴 역 13곳(2호선 방배·서초·교대·강남 · 3호선 남부터미널·양재·교대 · 7호선 내방·고속터미널·반포 · 9호선 셋)', chips.length === 13, chips.length);
    try { localStorage.removeItem(M.key); } catch (e) {}
    M.set('방배', '2호선', 'walk'); document.getElementById('mExit').value = '3'; document.getElementById('mDir').value = '서초 방면';
    var al = window.alert; window.alert = function () {};
    [40, 44, 48].forEach(function (s) { M.t0(Date.now() - s * 1000); M.go(); });
    M.t0(Date.now() - 1500); M.go();   /* 3초 아래 — 안 남김 */
    window.alert = al;
    var D = M.load(), r = D.rec[0], s = r ? M.stat(r.t) : null, st = String(document.getElementById('mStat').innerText || '');
    ck('세 번 재면 평균 44초 · 편차 ±4초 · 「3번 이상 — 계산에 씀」 · 3초 아래 값은 안 남김', D.rec.length === 1 && s && s.n === 3 && Math.abs(s.m - 44) < 0.3 && Math.abs(s.sd - 4) < 0.3 && /3번 이상/.test(st), s ? s.n + '번 · ' + s.m.toFixed(1) + ' ± ' + s.sd.toFixed(1) : '없음');
    ck('저장 꼴 — 역·노선·종류·출입구·방향 + [초, 시, 평일/주말, 날짜] · 좌표 없음', r && r.st === '방배' && r.ln === '2호선' && r.kind === 'walk' && r.exit === '3' && r.dir === '서초 방면' && r.t[0].length === 4 && !/lat|lon|좌표/.test(JSON.stringify(D)), r ? JSON.stringify(r).slice(0, 120) : '');
    ck('잰 역에 ✅ 표시', /✅/.test(document.querySelector('#mSt button').innerText), document.querySelector('#mSt button').innerText);
    try { localStorage.removeItem(M.key); } catch (e) {}
    var ext = performance.getEntriesByType('resource').filter(function (e) { return e.name.indexOf(location.origin) !== 0; }).map(function (e) { return e.name; });
    ck('🔒 밖으로 나간 요청 0(같은 사이트 자료만)', ext.length === 0, ext.slice(0, 3).join(' | ') || '0');
    var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
  } catch (e) { ck('검사 스크립트가 끝까지 돌았다', false, e.message); } setTimeout(send, 80); }, 2500);
})();
