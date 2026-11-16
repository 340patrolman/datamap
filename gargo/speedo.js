/* 가르고 「이동 속도」 — 비행기·기차·배에서 지금 속도·고도·방향 (2026-11-16 형님 「비행기모드에서 비행기 속도나 기차속도 · 저가항공·외국여행」)
   · 통신 없이 돈다: 폰 GPS 만 쓴다(비행기 모드에서도 GPS 수신은 된다 — 위치 서비스가 켜져 있어야 한다).
   · 받은 위치는 저장하지 않는다(이 화면을 닫으면 사라진다 · 최고 속도·거리도 이번 측정만).
   · 속도 = GPS 가 준 속도(coords.speed) 먼저, 없으면 앞뒤 자리 거리 ÷ 시간(정확도가 나쁜 자리는 뺀다).
   · gargo.js 를 고치지 않는다 — 위 칩 줄에 단추 하나, 주소 #spd=1 로도 연다. */
(function () {
  var W = null, st = null, wl = null, tick = null;
  function $(id) { return document.getElementById(id); }
  function hav(a, b) { var R = 6371000, r = Math.PI / 180, dLa = (b.la - a.la) * r, dLo = (b.lo - a.lo) * r, s = Math.sin(dLa / 2) * Math.sin(dLa / 2) + Math.cos(a.la * r) * Math.cos(b.la * r) * Math.sin(dLo / 2) * Math.sin(dLo / 2); return 2 * R * Math.asin(Math.min(1, Math.sqrt(s))); }
  var DIR = ['북', '북북동', '북동', '동북동', '동', '동남동', '남동', '남남동', '남', '남남서', '남서', '서남서', '서', '서북서', '북서', '북북서'];
  function kind(k) {   /* 대략 — 탈것 이름은 속도만 보고 짐작한 것 */
    if (k < 2) return '멈춤';
    if (k < 8) return '걷는 빠르기';
    if (k < 130) return '자동차·버스 빠르기';
    if (k < 200) return '일반 열차 빠르기';
    if (k < 330) return 'KTX·SRT 빠르기(최고 시속 300 안팎)';
    if (k < 600) return '비행기(오르내리는 중)';
    if (k < 1100) return '비행기 순항(보통 시속 800~950)';
    return '아주 빠름 — GPS 값이 튈 수 있음';
  }
  function fmtT(s) { s = Math.max(0, Math.round(s)); var h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60; return (h ? h + '시간 ' : '') + (h || m ? m + '분 ' : '') + (h ? '' : x + '초'); }
  function css() {
    if ($('gSpdoCss')) return; var c = document.createElement('style'); c.id = 'gSpdoCss';
    c.textContent = '#gSpdoV{position:fixed;inset:0;z-index:60;background:#0b1220;color:#eef2f7;display:flex;flex-direction:column;padding:calc(14px + env(safe-area-inset-top)) 18px calc(16px + env(safe-area-inset-bottom));font-family:system-ui,sans-serif;overflow:auto}'
      + '#gSpdoV .hd{display:flex;align-items:center;gap:10px}#gSpdoV .hd b{font-size:18px;font-weight:900;flex:1}#gSpdoV .hd button{min-width:44px;min-height:44px;border-radius:12px;border:1px solid #253044;background:#111827;color:#eef2f7;font-size:18px}'
      + '#gSpdoV .big{margin:18px 0 2px;text-align:center}#gSpdoV .big .n{font-size:min(28vw,132px);font-weight:900;line-height:1;letter-spacing:-2px;font-variant-numeric:tabular-nums}#gSpdoV .big .u{font-size:20px;font-weight:800;color:#a3aec2;margin-left:6px}'
      + '#gSpdoV .k{text-align:center;font-size:16px;font-weight:800;color:#93c5fd;min-height:22px}#gSpdoV .sub{text-align:center;font-size:14px;color:#a3aec2;margin-top:4px;font-variant-numeric:tabular-nums}'
      + '#gSpdoV .gr{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}#gSpdoV .c{background:#111827;border:1px solid #253044;border-radius:14px;padding:12px}#gSpdoV .c span{display:block;font-size:12.5px;color:#a3aec2;font-weight:700}#gSpdoV .c b{display:block;font-size:24px;font-weight:900;margin-top:4px;font-variant-numeric:tabular-nums}#gSpdoV .c i{font-style:normal;font-size:13px;color:#a3aec2;font-weight:700;margin-left:4px}'
      + '#gSpdoV .st{margin-top:14px;padding:10px 12px;border-radius:12px;font-size:13.5px;line-height:1.5;background:#111827;border:1px solid #253044}#gSpdoV .st.w{border-color:#b45309;color:#fde68a}#gSpdoV .st.ok{border-color:#15803d}'
      + '#gSpdoV .nt{margin-top:12px;font-size:12.5px;line-height:1.6;color:#a3aec2}#gSpdoV .rs{margin-top:12px;min-height:44px;border-radius:12px;border:1px solid #253044;background:#111827;color:#eef2f7;font-weight:800;font-size:15px}'
      + '#gOv #gSpdoB{white-space:nowrap}#gOv #gSpdoB::after{display:none!important}';
    document.head.appendChild(c);
  }
  function paint() {
    if (!W || !st) return; var p = st.last, now = Date.now();
    var k = st.v == null ? null : st.v * 3.6;
    $('gSpN').textContent = k == null ? '--' : (k < 10 ? k.toFixed(1) : Math.round(k));
    $('gSpK').textContent = k == null ? 'GPS 기다리는 중' : kind(k);
    $('gSpS').textContent = k == null ? '' : '초속 ' + st.v.toFixed(1) + 'm · ' + Math.round(k / 1.852) + '노트 · ' + Math.round(k / 1.609) + 'mph';
    $('gSpMx').textContent = st.max ? Math.round(st.max * 3.6) : '--';
    $('gSpD').textContent = st.dist >= 1000 ? (st.dist / 1000).toFixed(st.dist < 1e5 ? 1 : 0) : Math.round(st.dist);
    $('gSpDu').textContent = st.dist >= 1000 ? 'km' : 'm';
    var el = st.t0 ? (now - st.t0) / 1000 : 0; $('gSpT').textContent = st.t0 ? fmtT(el) : '--';
    $('gSpA').textContent = st.dist > 50 && st.mt > 5 ? Math.round(st.dist / st.mt * 3.6) : '--';
    $('gSpAl').textContent = p && p.alt != null ? Math.round(p.alt).toLocaleString() : '--';
    $('gSpAf').textContent = p && p.alt != null ? Math.round(p.alt * 3.281).toLocaleString() + 'ft' : '';
    $('gSpH').textContent = st.hd == null ? '--' : DIR[Math.round(st.hd / 22.5) % 16];
    $('gSpHd').textContent = st.hd == null ? '' : Math.round(st.hd) + '°';
    var S = $('gSpSt'), ago = p ? (now - p.t) / 1000 : null;
    if (st.err) { S.className = 'st w'; S.textContent = st.err; }
    else if (!p) { S.className = 'st w'; S.textContent = '위성을 찾는 중 — 하늘이 보이는 창가에서 기다린다. 통신이 없으면 처음 잡는 데 몇 분 걸릴 수 있다.'; }
    else if (ago > 15) { S.className = 'st w'; S.textContent = 'GPS 신호가 ' + Math.round(ago) + '초째 안 온다 — 창가 쪽으로 · 객실 안쪽·터널에서는 끊긴다.'; }
    else { S.className = 'st ok'; S.textContent = 'GPS 받는 중 · 정확도 ±' + Math.round(p.acc) + 'm · ' + Math.max(0, Math.round(ago)) + '초 전 · 통신 쓰지 않음'; }
  }
  function onPos(pos) {
    var c = pos.coords, t = pos.timestamp || Date.now(), p = { la: c.latitude, lo: c.longitude, acc: c.accuracy || 9999, alt: c.altitude, t: t };
    st.err = null; if (!st.t0) st.t0 = Date.now();
    var good = p.acc < 150, prev = st.good;
    if (c.speed != null && !isNaN(c.speed) && c.speed >= 0) st.v = c.speed;
    else if (good && prev && t > prev.t) { var d = hav(prev, p), dt = (t - prev.t) / 1000; if (dt >= 1) { var v = d / dt; st.v = st.v == null ? v : st.v * 0.5 + v * 0.5; } }
    if (c.heading != null && !isNaN(c.heading) && (st.v || 0) > 1) st.hd = c.heading;
    else if (good && prev && hav(prev, p) > 20) { var r = Math.PI / 180, y = Math.sin((p.lo - prev.lo) * r) * Math.cos(p.la * r), x = Math.cos(prev.la * r) * Math.sin(p.la * r) - Math.sin(prev.la * r) * Math.cos(p.la * r) * Math.cos((p.lo - prev.lo) * r); st.hd = (Math.atan2(y, x) / r + 360) % 360; }
    if (good) { if (prev && t > prev.t) { var dd = hav(prev, p); if (dd > Math.max(3, p.acc * 0.3) && dd / ((t - prev.t) / 1000) < 400) { st.dist += dd; st.mt += (t - prev.t) / 1000; } } st.good = p; }
    if (st.v != null && st.v < 400 && st.v > st.max && p.acc < 100) st.max = st.v;   /* 시속 1,440km 넘는 값은 튐으로 보고 최고에 안 넣는다 */
    st.last = p; paint();
  }
  function onErr(e) { st.err = e && e.code === 1 ? '위치 권한이 꺼져 있다 — 폰 설정에서 이 브라우저(또는 가르고)의 위치를 「허용」으로. 비행기 모드여도 위치 서비스는 켜 둔다.' : e && e.code === 3 ? '아직 위치를 못 잡았다 — 창가에서 조금 더 기다린다(통신 없이 처음 잡을 때는 몇 분).' : '위치를 받을 수 없다 — ' + ((e && e.message) || '알 수 없음'); paint(); }
  function wake() { try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { wl = l; }).catch(function () {}); } catch (e) {} }
  function open() {
    css(); if (W) return; st = { v: null, max: 0, dist: 0, mt: 0, t0: 0, last: null, good: null, hd: null, err: null };
    W = document.createElement('div'); W.id = 'gSpdoV'; W.className = 'noicon'; W.setAttribute('role', 'dialog'); W.setAttribute('aria-label', '이동 속도');
    W.innerHTML = '<div class="hd"><b>이동 속도 — 비행기·기차·배</b><button id="gSpX" aria-label="닫기">✕</button></div>'
      + '<div class="big"><span class="n" id="gSpN">--</span><span class="u">km/h</span></div><div class="k" id="gSpK">GPS 기다리는 중</div><div class="sub" id="gSpS"></div>'
      + '<div class="gr"><div class="c"><span>최고 속도</span><b><em id="gSpMx" style="font-style:normal">--</em><i>km/h</i></b></div><div class="c"><span>평균(움직인 동안)</span><b><em id="gSpA" style="font-style:normal">--</em><i>km/h</i></b></div>'
      + '<div class="c"><span>고도</span><b><em id="gSpAl" style="font-style:normal">--</em><i>m</i></b><span id="gSpAf" style="margin-top:2px"></span></div><div class="c"><span>가는 쪽</span><b><em id="gSpH" style="font-style:normal">--</em><i id="gSpHd"></i></b></div>'
      + '<div class="c"><span>움직인 거리</span><b><em id="gSpD" style="font-style:normal">0</em><i id="gSpDu">m</i></b></div><div class="c"><span>잰 시간</span><b id="gSpT" style="font-size:20px">--</b></div></div>'
      + '<div class="st w" id="gSpSt">위성을 찾는 중</div><button class="rs" id="gSpR">최고·거리 다시 재기</button>'
      + '<div class="nt">· 비행기 모드에서도 GPS 는 받는다(위치 서비스 켬 · 창가 자리가 잘 잡힌다). 이 화면은 통신을 쓰지 않는다 — 한 번이라도 통신 될 때 가르고를 열어 두면 비행기 안에서도 열린다.<br>· 기내에서 기기 사용은 항공사·승무원 안내를 따른다(이착륙 때는 특히).<br>· 속도는 땅 위를 지나는 빠르기다 — 비행기 계기의 「대기속도」와는 바람만큼 다르다. 탈것 이름은 속도만 보고 짐작한 것이다.<br>· 받은 위치는 저장하지 않는다 — 닫으면 사라진다.</div>';
    document.body.appendChild(W);
    $('gSpX').onclick = close; $('gSpR').onclick = function () { st.max = 0; st.dist = 0; st.mt = 0; st.t0 = Date.now(); paint(); };
    if (!navigator.geolocation) { st.err = '이 기기는 위치를 알려주지 않는다.'; paint(); return; }
    st.id = navigator.geolocation.watchPosition(onPos, onErr, { enableHighAccuracy: true, maximumAge: 0, timeout: 120000 });
    tick = setInterval(paint, 1000); wake(); paint();
    try { history.pushState({ gspd: 1 }, ''); } catch (e) {}
  }
  function close(fromPop) {
    if (!W) return; try { if (st && st.id != null) navigator.geolocation.clearWatch(st.id); } catch (e) {} clearInterval(tick); try { if (wl) wl.release(); } catch (e) {} wl = null;
    W.parentNode.removeChild(W); W = null; st = null;
    if (fromPop !== true) { try { if (history.state && history.state.gspd) history.back(); } catch (e) {} }
  }
  window.addEventListener('popstate', function () { if (W) close(true); });
  document.addEventListener('visibilitychange', function () { if (W && document.visibilityState === 'visible') wake(); });
  function addBtn() {
    var ov = $('gOv'); if (!ov || $('gSpdoB')) return;
    var b = document.createElement('button'); b.id = 'gSpdoB'; b.type = 'button'; b.title = '비행기·기차에서 지금 속도·고도 — 통신 없이 GPS 만'; b.innerHTML = (window.gi ? gi('plane') : '✈') + ' 속도';
    b.addEventListener('click', function (e) { e.stopPropagation(); e.preventDefault(); open(); }, true);
    ov.appendChild(b);
  }
  window.gargoSpeedo = { open: open, close: close, kind: kind, hav: hav };
  function start() { css(); addBtn(); if (/(^|[#&])spd=1(&|$)/.test(location.hash)) setTimeout(open, 300); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
