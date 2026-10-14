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
  var poll = setInterval(function () { if (ready()) { clearInterval(poll); setTimeout(function () { try { run(); } catch (e) { fail(e && e.message); } }, 2500); } else if (Date.now() - t0 > 45000) { clearInterval(poll); fail('45초 안에 길 묶음이 안 읽혔다(문법 오류 · 파일 없음) ' + (window.__ERR || []).join(' | ')); } }, 300);

  function run() {
    var g = window.GARGO, st = g.state(), G = st.G, now = Date.now() / 1000;
    ck('가르고가 열린다(문법 · 길 묶음)', true, '길 ' + G.S.length + '줄 · 신호 교차로 ' + G.sig.length + '곳');
    ck('신호 교차로가 있다(서초 묶음 100곳 넘게)', G.sig.length > 100, G.sig.length);
    ck('값 없는 신호도 신호로 친다(T-GIS 800곳 넘게 붙음)', G.XS.length > 800, G.XS.length);
    /* 1) 소통 갈래 — 앱 기준표 그대로 */
    var sp = [[60, 1, 100, 0], [40, 1, 100, 1], [20, 1, 100, 2], [30, 3, 50, 0], [20, 3, 50, 1], [10, 3, 50, 2], [22, 6, 30, 0], [13, 6, 30, 1], [8, 6, 30, 2]], bad = [];
    sp.forEach(function (q) { var v = g.spdLv(q[0], q[1], q[2]); if (v !== q[3]) bad.push(q.join('/') + '→' + v); });
    ck('소통 갈래 기준표(9칸)', !bad.length, bad.join(' '));
    /* 1-1) 방향 맞추기 — 내가 들어가는 쪽의 기록만 쓴다 · 비스듬해서 양옆 방위 기록이 둘이면 고르지 않는다(다른 방향의 초를 보이지 않는다) */
    var R2 = { mv: [['st', 'St', 50, 0, 0, 0], ['wt', 'St', 40, 0, 0, 10], ['st', 'Lt', 20, 0, 0, 60]] }, R1 = { mv: [['st', 'St', 50, 0, 0, 0]] }, m1 = g.mvOf(R2, 'st', 'St'), m2 = g.mvOf(R2, 'sw', 'St'), m3 = g.mvOf(R1, 'sw', 'St'), m4 = g.mvOf(R2, 'nt', 'St'), m5 = g.mvOf(R2, 'st', 'Lt');
    ck('방향 · 같은 쪽 기록을 쓴다(남쪽에서 직진 → 남 50초 · 좌회전 → 20초)', m1 && m1[0] === 'st' && m1[2] === 50 && m5 && m5[2] === 20);
    ck('방향 · 양옆에 기록이 둘이면 고르지 않는다(남서쪽에서 → 모름)', m2 === null, m2 ? m2[0] : '모름');
    ck('방향 · 옆 방위가 하나뿐이면 그것을 쓴다 · 반대쪽 기록은 안 쓴다', m3 && m3[0] === 'st' && m4 === null);
    /* 2) 길 계산 세 벌 — 서초역→양재역 · 고속터미널→방배역 · 교대역→예술의전당 */
    var OD = [['서초역→양재역', 127.0076, 37.4919, 127.0341, 37.4844], ['고속터미널→방배역', 127.0049, 37.5049, 126.9976, 37.4814], ['교대역→예술의전당', 127.0142, 37.4934, 127.0118, 37.4786], ['서초역→서초경찰서(짧은 길)', 127.0076, 37.4919, 127.005607, 37.495467], ['방배경찰서→서초경찰서', 126.9826, 37.4813, 127.0056, 37.4955], ['사당역→고속터미널', 126.9816, 37.4766, 127.0049, 37.5049]];
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
      /* 고속터미널→방배역은 떠나는 자리가 중앙분리된 큰길의 동쪽행 차로에 붙어 한 번 돌아야 하는 구간이다(큰길 유턴 자리가 길 자료에 없다 — 알려진 한계) → 에움은 2.0 까지 */
      ck(o[0] + ' · 골목으로 돌지 않는다(20% 아래) · 꺾음 9번 아래 · 에움 1.7 아래', line < 600 || (alp <= 20 && turns <= 9 && det <= (/고속터미널→방배역/.test(o[0]) ? 2.0 : 1.7)), '골목 ' + Math.round(alp) + '% · 꺾음 ' + turns + ' · 에움 ' + det.toFixed(2));
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
      ck('밤 22~06시에는 속도 권고가 안 나온다(모의 주행 4초)', seen === 0, '신호 판 ' + shown + '번 봄 · 권고 글 ' + seen + '번');
      ck('안내 화면이 뜬다(위 띠)', (document.getElementById('gTop') || {}).offsetHeight > 0, String((document.getElementById('gTop') || {}).innerText || '').split(String.fromCharCode(10)).join(' · '));
      /* 켜놓고 다니기(v0.6.0) — 안내를 끝내고 길을 지운 뒤: 반포대로를 북쪽으로 가는 자리·속도를 넣으면 진행 방향이 위로 돌고, 내 길 앞의 신호가 「남쪽에서 직진」 값으로 잡힌다 */
      try { var b1 = document.getElementById('gStop'); if (b1) b1.click(); var b2 = document.getElementById('gClr'); if (b2) b2.click();
        ck('목적지가 없으면 「켜놓고 다니기」 단추가 있다', !!document.getElementById('gCruise'));
        var pa = g.P(127.0113, 37.4835), pb = g.P(127.0076, 37.4925), rr = g.findRoute(pa[0], pa[1], pb[0], pb[1], Date.now() / 1000, null), ii = Math.floor(rr.pts.length / 2 / 3) * 2, hx = rr.pts[ii], hy = rr.pts[ii + 1], hd = (Math.atan2(rr.pts[ii + 2] - hx, -(rr.pts[ii + 3] - hy)) * 180 / Math.PI + 360) % 360;
        g.setMe(hx, hy, 5, hd, 11); var onC = g.cruise(), A = g.ahead(), top2 = String(document.getElementById('gTop').innerText || '');
        ck('켜놓고 다니기가 켜진다(위 띠 · 진행 방향이 위)', onC === true && /켜놓고 다니기/.test(top2) && Math.abs(g.view.rot - hd) < 1 && g.view.s >= 0.5 && g.view.s <= 0.9, 'rot ' + Math.round(g.view.rot) + ' / 방위 ' + Math.round(hd) + ' · 배율 ' + g.view.s.toFixed(2));
        var asc = A && A.sigs.every(function (x, i2) { return x.d <= 1000 && (!i2 || x.d >= A.sigs[i2 - 1].d); });
        ck('내 길 앞 신호가 잡힌다(1km 안 · 가까운 순 · 들어가는 쪽 = 남쪽 언저리)', !!(A && A.sig && asc && ['st', 'se', 'sw'].indexOf(A.sig.side) >= 0), A && A.sig ? A.nm + ' · ' + A.sig.nm + ' ' + Math.round(A.sig.d) + 'm · ' + A.sig.side + ' · 모두 ' + A.sigs.length + '곳' : '없음');
        ck('끝내면 지도가 북쪽 위로 돌아오고 찾기 칸이 다시 보인다', g.cruise(false) === false && g.view.rot === 0 && !document.body.classList.contains('guiding') && document.getElementById('gFind').style.display !== 'none');
      } catch (e) { ck('켜놓고 다니기 검사', false, e && e.message); }
      var er = window.__ERR || []; ck('화면 오류 0', er.length === 0, er.slice(0, 3).join(' | '));
      send(); }, 4200);
  }
})();
