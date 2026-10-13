/* 가르고 값 검사 — tools/check/pagecheck.py 가 화면 끝에 끼워 넣는다(사이트에는 안 올라간다 · tools 는 _config.yml exclude).
   보는 것: 길 계산이 된다 · 길이 이어져 있다 · 회전 금지를 어기지 않는다 · 제한속도보다 빠르게 셈하지 않는다 ·
   속도 권고가 제한속도를 넘지 않는다 · 밤(22~06시)에는 속도 권고가 안 나온다 · 신호 값이 말이 되는 범위다 · 화면 오류 0 */
(function () {
  var C = [], t0 = Date.now();
  function ck(n, ok, got) { C.push([n, !!ok, got == null ? '' : String(got).slice(0, 160)]); }
  function send() { var o = { checks: C }, s = btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, ''), n = Math.ceil(s.length / 1500), id = String(Date.now());
    for (var i = 0; i < n; i++) (new Image()).src = '/__r?p=' + window.__PAGE + '&k=' + id + '&i=' + i + '&n=' + n + '&d=' + s.substr(i * 1500, 1500); }
  function fail(m) { ck('검사 스크립트가 끝까지 돌았다', false, m); send(); }
  function ready() { try { var g = window.GARGO, st = g && g.state(); return !!(st && st.G && st.G.S && st.G.S.length); } catch (e) { return false; } }
  var poll = setInterval(function () { if (ready()) { clearInterval(poll); setTimeout(function () { try { run(); } catch (e) { fail(e && e.message); } }, 2500); } else if (Date.now() - t0 > 45000) { clearInterval(poll); fail('45초 안에 길 묶음이 안 읽혔다(문법 오류 · 파일 없음) ' + (window.__ERR || []).join(' | ')); } }, 300);

  function run() {
    var g = window.GARGO, st = g.state(), G = st.G, now = Date.now() / 1000;
    ck('가르고가 열린다(문법 · 길 묶음)', true, '길 ' + G.S.length + '줄 · 신호 교차로 ' + G.sig.length + '곳');
    ck('신호 교차로가 있다(서초 묶음 100곳 넘게)', G.sig.length > 100, G.sig.length);
    /* 1) 소통 갈래 — 앱 기준표 그대로 */
    var sp = [[60, 1, 100, 0], [40, 1, 100, 1], [20, 1, 100, 2], [30, 3, 50, 0], [20, 3, 50, 1], [10, 3, 50, 2], [22, 6, 30, 0], [13, 6, 30, 1], [8, 6, 30, 2]], bad = [];
    sp.forEach(function (q) { var v = g.spdLv(q[0], q[1], q[2]); if (v !== q[3]) bad.push(q.join('/') + '→' + v); });
    ck('소통 갈래 기준표(9칸)', !bad.length, bad.join(' '));
    /* 2) 길 계산 세 벌 — 서초역→양재역 · 고속터미널→방배역 · 교대역→예술의전당 */
    var OD = [['서초역→양재역', 127.0076, 37.4919, 127.0341, 37.4844], ['고속터미널→방배역', 127.0049, 37.5049, 126.9976, 37.4814], ['교대역→예술의전당', 127.0142, 37.4934, 127.0118, 37.4786]];
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
    /* 4) 밤 — 시각을 23시로 바꿔 놓고 모의 주행 4초: 속도 권고 글이 한 번도 나오면 안 된다 */
    var gh = Date.prototype.getHours; Date.prototype.getHours = function () { return 23; };
    ck('밤 판정(23시 → 밤)', g.night() === true, g.night());
    var seen = 0, shown = 0; try { g.simStart(); } catch (e) { ck('모의 주행 시작', false, e.message); }
    var smp = setInterval(function () { var el = document.getElementById('gSig'), h = el ? el.innerHTML : ''; if (h) shown++; if (h.indexOf('시속') >= 0) seen++; }, 200);
    setTimeout(function () { clearInterval(smp); Date.prototype.getHours = gh;
      ck('밤 22~06시에는 속도 권고가 안 나온다(모의 주행 4초)', seen === 0, '신호 판 ' + shown + '번 봄 · 권고 글 ' + seen + '번');
      ck('안내 화면이 뜬다(위 띠)', (document.getElementById('gTop') || {}).offsetHeight > 0, String((document.getElementById('gTop') || {}).innerText || '').split(String.fromCharCode(10)).join(' · '));
      var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
      send(); }, 4200);
  }
})();
