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
      + '#gSpdoV>*{flex-shrink:0}#gSpdoV .hd{display:flex;align-items:center;gap:10px}#gSpdoV .hd b{font-size:18px;font-weight:900;flex:1}#gSpdoV .hd button{min-width:44px;min-height:44px;border-radius:12px;border:1px solid #253044;background:#111827;color:#eef2f7;font-size:18px}'
      + '#gSpdoV .big{margin:18px 0 2px;text-align:center}#gSpdoV .big .n{font-size:min(28vw,132px);font-weight:900;line-height:1;letter-spacing:-2px;font-variant-numeric:tabular-nums}#gSpdoV .big .u{font-size:20px;font-weight:800;color:#a3aec2;margin-left:6px}'
      + '#gSpdoV .k{text-align:center;font-size:16px;font-weight:800;color:#93c5fd;min-height:22px}#gSpdoV .sub{text-align:center;font-size:14px;color:#a3aec2;margin-top:4px;font-variant-numeric:tabular-nums}'
      + '#gSpdoV .gr{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:18px}#gSpdoV .c{background:#111827;border:1px solid #253044;border-radius:14px;padding:12px}#gSpdoV .c span{display:block;font-size:12.5px;color:#a3aec2;font-weight:700}#gSpdoV .c b{display:block;font-size:24px;font-weight:900;margin-top:4px;font-variant-numeric:tabular-nums}#gSpdoV .c i{font-style:normal;font-size:13px;color:#a3aec2;font-weight:700;margin-left:4px}'
      + '#gSpdoV .st{margin-top:14px;padding:10px 12px;border-radius:12px;font-size:13.5px;line-height:1.5;background:#111827;border:1px solid #253044}#gSpdoV .st.w{border-color:#b45309;color:#fde68a}#gSpdoV .st.ok{border-color:#15803d}'
      + '#gSpdoV .nt{margin-top:12px;font-size:12.5px;line-height:1.6;color:#a3aec2}#gSpdoV .rs{margin-top:12px;min-height:44px;border-radius:12px;border:1px solid #253044;background:#111827;color:#eef2f7;font-weight:800;font-size:15px}'
      + '#gSpdoV .mp{margin-top:16px;background:#0f1a33;border:1px solid #253044;border-radius:14px;overflow:hidden}#gSpdoV .mp canvas{display:block;width:100%;height:220px;touch-action:none}#gSpdoV .mz{display:flex;gap:6px;padding:8px}#gSpdoV .mz button{flex:1;min-height:38px;border-radius:10px;border:1px solid #253044;background:#111827;color:#a3aec2;font-weight:800;font-size:13.5px}#gSpdoV .mz button.on{background:#1b54d6;border-color:#1b54d6;color:#fff}'
      + '#gSpdoV .wh{padding:0 12px 12px;font-size:14px;line-height:1.6}#gSpdoV .wh b{color:#fff}#gSpdoV .wh em{font-style:normal;color:#a3aec2}'
      + '#gSpNews{position:fixed;left:12px;right:12px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:55;max-width:420px;margin:0 auto;background:#111827;color:#eef2f7;border:1px solid #2f6bff;border-radius:16px;padding:14px 14px 12px;box-shadow:0 10px 30px rgba(0,0,0,.45);font-family:system-ui,sans-serif;overflow:hidden}#gSpNews b{font-size:16px;font-weight:900}#gSpNews p{margin:6px 0 10px;font-size:13.5px;line-height:1.55;color:#cbd5e1}#gSpNews .bt{display:flex;gap:8px}#gSpNews button{flex:1;min-height:44px;border-radius:12px;border:1px solid #253044;background:#1f2937;color:#eef2f7;font-weight:800;font-size:15px}#gSpNews button.go{background:#2f6bff;border-color:#2f6bff}#gSpNews .bar{position:absolute;left:0;bottom:0;height:3px;background:#2f6bff;width:100%;transition:width linear}'
      + '#gOv #gSpdoB{white-space:nowrap}#gOv #gSpdoB::after{display:none!important}';
    document.head.appendChild(c);
  }
  /* ---- 세계지도(통신 없이 · world.json = Natural Earth 공공 영역 · 나라 110m · 도시 50m 한글 이름) ---- */
  var WD = null, WDP = null, ZM = 2;   /* 0 세계 · 1 지역(약 3,000km) · 2 가까이(약 600km) */
  var ZW = [360, 30, 6];   /* 화면 가로에 담는 경도 폭(도) */
  function wLoad() { if (WD || WDP) return WDP; WDP = fetch('world.json').then(function (r) { return r.ok ? r.json() : null; }).then(function (j) { WD = j && j.c ? j : null; return WD; }).catch(function () { WDP = null; return null; }); return WDP; }
  function inRing(r, x, y) { var o = false; for (var i = 0, j = r.length - 2; i < r.length; j = i, i += 2) { var xi = r[i] / 10, yi = r[i + 1] / 10, xj = r[j] / 10, yj = r[j + 1] / 10; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) o = !o; } return o; }
  function where(la, lo) { if (!WD) return null; for (var i = 0; i < WD.c.length; i++) { var rs = WD.c[i][1]; for (var k = 0; k < rs.length; k++) if (inRing(rs[k], lo, la)) return WD.c[i][0]; } return ''; }
  function bear(a, b) { var r = Math.PI / 180, y = Math.sin((b.lo - a.lo) * r) * Math.cos(b.la * r), x = Math.cos(a.la * r) * Math.sin(b.la * r) - Math.sin(a.la * r) * Math.cos(b.la * r) * Math.cos((b.lo - a.lo) * r); return (Math.atan2(y, x) / r + 360) % 360; }
  function cities(p) {   /* 가까운 큰 도시 · 가는 쪽 앞 도시 */
    if (!WD) return null; var near = null, ahead = null; WD.p.forEach(function (c) { var q = { la: c[1] / 100, lo: c[0] / 100 }, d = hav(p, q); if (!near || d < near.d) near = { c: c, d: d, b: bear(p, q) };
      if (st.hd != null && (st.v || 0) > 5 && d > 5000 && d < 2500000) { var df = Math.abs(((bear(p, q) - st.hd) + 540) % 360 - 180); if (df < 25 && (!ahead || d < ahead.d)) ahead = { c: c, d: d }; } }); return { near: near, ahead: ahead }; }
  function km(d) { return d >= 10000 ? Math.round(d / 1000).toLocaleString() + 'km' : (d / 1000).toFixed(1) + 'km'; }
  function drawMap() {
    var cv = document.getElementById('gSpMap'); if (!cv || !W) return; var dpr = Math.min(2, window.devicePixelRatio || 1), w = cv.clientWidth, h = cv.clientHeight; if (!w) return; if (cv.width !== w * dpr) { cv.width = w * dpr; cv.height = h * dpr; }
    var x = cv.getContext('2d'); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.fillStyle = '#0f1a33'; x.fillRect(0, 0, w, h);
    var p = st && (st.good || st.last), cla = ZM === 0 ? 20 : p ? p.la : 36, clo = ZM === 0 ? (p ? p.lo : 127) : p ? p.lo : 127, kx = w / ZW[ZM], ky = kx / (ZM === 0 ? 1 : Math.max(.2, Math.cos(cla * Math.PI / 180)));
    function X(lo) { var d = lo - clo; if (d > 180) d -= 360; if (d < -180) d += 360; return w / 2 + d * kx; } function Y(la) { return h / 2 - (la - cla) * ky; }
    if (!WD) { x.fillStyle = '#a3aec2'; x.font = '700 13px system-ui'; x.textAlign = 'center'; x.fillText(WDP ? '세계지도 읽는 중…' : '세계지도를 아직 못 받았다 — 통신 될 때 한 번 열면 기기에 남는다', w / 2, h / 2); return; }
    x.lineJoin = 'round'; WD.c.forEach(function (cc) { cc[1].forEach(function (r) { x.beginPath(); var px = null; for (var i = 0; i < r.length; i += 2) { var sx = X(r[i] / 10), sy = Y(r[i + 1] / 10); if (px != null && Math.abs(sx - px) > w * .5) x.moveTo(sx, sy); else if (i) x.lineTo(sx, sy); else x.moveTo(sx, sy); px = sx; } x.closePath(); x.fillStyle = '#2a3a52'; x.fill(); x.strokeStyle = '#46597a'; x.lineWidth = 1; x.stroke(); }); });
    var lim = ZM === 0 ? 4000 : ZM === 1 ? 1500 : 500, boxes = []; x.font = '700 12px system-ui'; x.textAlign = 'left'; x.textBaseline = 'middle';
    WD.p.forEach(function (c) { if (c[3] < lim && !(ZM === 0 && c[4] && c[3] > 2000)) return; var sx = X(c[0] / 100), sy = Y(c[1] / 100); if (sx < -10 || sx > w + 10 || sy < -10 || sy > h + 10) return; var tw = x.measureText(c[2]).width; if (boxes.some(function (b) { return Math.abs(b[0] - sx) < (tw + b[2]) / 2 + 10 && Math.abs(b[1] - sy) < 14; })) return; boxes.push([sx + tw / 2, sy, tw]);
      x.beginPath(); x.arc(sx, sy, 2.5, 0, Math.PI * 2); x.fillStyle = '#cbd5e1'; x.fill(); x.fillStyle = '#cbd5e1'; x.fillText(c[2], sx + 5, sy); });
    if (st && st.trk && st.trk.length > 1) { x.beginPath(); st.trk.forEach(function (q, i) { var sx = X(q[1]), sy = Y(q[0]); if (i) x.lineTo(sx, sy); else x.moveTo(sx, sy); }); x.strokeStyle = '#60a5fa'; x.lineWidth = 2.5; x.stroke(); }
    if (p) { var mx = X(p.lo), my = Y(p.la); x.save(); x.translate(mx, my); x.rotate(((st.hd || 0)) * Math.PI / 180); x.beginPath(); x.moveTo(0, -11); x.lineTo(7, 8); x.lineTo(0, 4); x.lineTo(-7, 8); x.closePath(); x.fillStyle = '#facc15'; x.fill(); x.lineWidth = 2; x.strokeStyle = '#0b1220'; x.stroke(); x.restore(); }
    x.fillStyle = 'rgba(163,174,194,.8)'; x.font = '600 10px system-ui'; x.textAlign = 'right'; x.fillText('Natural Earth', w - 6, h - 8); }
  function paintWhere() { var el = document.getElementById('gSpWh'); if (!el) return; var p = st && (st.good || st.last); if (!p) { el.innerHTML = '<em>자리를 잡으면 지금 위 나라·가까운 도시가 나온다</em>'; return; } if (!WD) { el.innerHTML = '<em>세계지도 읽는 중</em>'; return; }
    var cn = where(p.la, p.lo), cs = cities(p), h = '지금 위: <b>' + (cn ? cn : '바다 위') + '</b>';
    if (cs && cs.near) h += '<br>가까운 큰 도시: <b>' + cs.near.c[2] + '</b> ' + km(cs.near.d) + ' <em>' + DIR[Math.round(cs.near.b / 22.5) % 16] + '쪽</em>';
    if (cs && cs.ahead) { var v = st.v || 0, sec = v > 5 ? cs.ahead.d / v : 0; h += '<br>가는 쪽 앞 도시: <b>' + cs.ahead.c[2] + '</b> ' + km(cs.ahead.d) + (sec ? ' <em>· 이 빠르기로 ' + fmtT(sec).replace(/ \d+초$/, '') + '</em>' : ''); }
    el.innerHTML = h; }
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
    drawMap(); paintWhere();
  }
  function onPos(pos) {
    var c = pos.coords, t = pos.timestamp || Date.now(), p = { la: c.latitude, lo: c.longitude, acc: c.accuracy || 9999, alt: c.altitude, t: t };
    st.err = null; if (!st.t0) st.t0 = Date.now();
    var good = p.acc < 150, prev = st.good;
    if (c.speed != null && !isNaN(c.speed) && c.speed >= 0) st.v = c.speed;
    else if (good && prev && t > prev.t) { var d = hav(prev, p), dt = (t - prev.t) / 1000; if (dt >= 1) { var v = d / dt; st.v = st.v == null ? v : st.v * 0.5 + v * 0.5; } }
    if (c.heading != null && !isNaN(c.heading) && (st.v || 0) > 1) st.hd = c.heading;
    else if (good && prev && hav(prev, p) > 20) { var r = Math.PI / 180, y = Math.sin((p.lo - prev.lo) * r) * Math.cos(p.la * r), x = Math.cos(prev.la * r) * Math.sin(p.la * r) - Math.sin(prev.la * r) * Math.cos(p.la * r) * Math.cos((p.lo - prev.lo) * r); st.hd = (Math.atan2(y, x) / r + 360) % 360; }
    if (good) { if (prev && t > prev.t) { var dd = hav(prev, p); if (dd > Math.max(3, p.acc * 0.3) && dd / ((t - prev.t) / 1000) < 400) { st.dist += dd; st.mt += (t - prev.t) / 1000; } } st.good = p; var tl = st.trk[st.trk.length - 1]; if (!tl || hav({ la: tl[0], lo: tl[1] }, p) > 200) { st.trk.push([p.la, p.lo]); if (st.trk.length > 3000) st.trk.splice(0, 1000); } }
    if (st.v != null && st.v < 400 && st.v > st.max && p.acc < 100) st.max = st.v;   /* 시속 1,440km 넘는 값은 튐으로 보고 최고에 안 넣는다 */
    st.last = p; paint();
  }
  function onErr(e) { st.err = e && e.code === 1 ? '위치 권한이 꺼져 있다 — 폰 설정에서 이 브라우저(또는 가르고)의 위치를 「허용」으로. 비행기 모드여도 위치 서비스는 켜 둔다.' : e && e.code === 3 ? '아직 위치를 못 잡았다 — 창가에서 조금 더 기다린다(통신 없이 처음 잡을 때는 몇 분).' : '위치를 받을 수 없다 — ' + ((e && e.message) || '알 수 없음'); paint(); }
  function wake() { try { if (navigator.wakeLock) navigator.wakeLock.request('screen').then(function (l) { wl = l; }).catch(function () {}); } catch (e) {} }
  function open() {
    css(); if (W) return; st = { v: null, max: 0, dist: 0, mt: 0, t0: 0, last: null, good: null, hd: null, err: null, trk: [] }; wLoad().then(function () { if (W) { drawMap(); paintWhere(); } });
    W = document.createElement('div'); W.id = 'gSpdoV'; W.className = 'noicon'; W.setAttribute('role', 'dialog'); W.setAttribute('aria-label', '이동 속도');
    W.innerHTML = '<div class="hd"><b>이동 속도 — 비행기·기차·배</b><button id="gSpX" aria-label="닫기">✕</button></div>'
      + '<div class="big"><span class="n" id="gSpN">--</span><span class="u">km/h</span></div><div class="k" id="gSpK">GPS 기다리는 중</div><div class="sub" id="gSpS"></div>'
      + '<div class="gr"><div class="c"><span>최고 속도</span><b><em id="gSpMx" style="font-style:normal">--</em><i>km/h</i></b></div><div class="c"><span>평균(움직인 동안)</span><b><em id="gSpA" style="font-style:normal">--</em><i>km/h</i></b></div>'
      + '<div class="c"><span>고도</span><b><em id="gSpAl" style="font-style:normal">--</em><i>m</i></b><span id="gSpAf" style="margin-top:2px"></span></div><div class="c"><span>가는 쪽</span><b><em id="gSpH" style="font-style:normal">--</em><i id="gSpHd"></i></b></div>'
      + '<div class="c"><span>움직인 거리</span><b><em id="gSpD" style="font-style:normal">0</em><i id="gSpDu">m</i></b></div><div class="c"><span>잰 시간</span><b id="gSpT" style="font-size:20px">--</b></div></div>'
      + '<div class="mp"><canvas id="gSpMap" aria-label="세계지도 위 내 자리"></canvas><div class="mz"><button data-z="0">세계</button><button data-z="1">지역</button><button data-z="2" class="on">가까이</button></div><div class="wh" id="gSpWh"></div></div>'
      + '<div class="st w" id="gSpSt">위성을 찾는 중</div><button class="rs" id="gSpR">최고·거리 다시 재기</button>'
      + '<div class="nt">· 비행기 모드에서도 GPS 는 받는다(위치 서비스 켬 · 창가 자리가 잘 잡힌다). 이 화면은 통신을 쓰지 않는다 — 한 번이라도 통신 될 때 가르고를 열어 두면 비행기 안에서도 열린다.<br>· 기내에서 기기 사용은 항공사·승무원 안내를 따른다(이착륙 때는 특히).<br>· 속도는 땅 위를 지나는 빠르기다 — 비행기 계기의 「대기속도」와는 바람만큼 다르다. 탈것 이름은 속도만 보고 짐작한 것이다.<br>· 받은 위치는 저장하지 않는다 — 닫으면 사라진다(지나온 길도).<br>· 세계지도 = Natural Earth(공공 영역) 나라 경계·큰 도시 — 통신 없이 그린다 · 축척이 거칠어 나라 경계 가까이에서는 「지금 위」가 틀릴 수 있다.</div>';
    document.body.appendChild(W);
    [].forEach.call(W.querySelectorAll('.mz button'), function (b) { b.onclick = function () { ZM = +b.getAttribute('data-z'); [].forEach.call(W.querySelectorAll('.mz button'), function (o) { o.classList.toggle('on', o === b); }); drawMap(); }; });
    $('gSpX').onclick = close; $('gSpR').onclick = function () { st.max = 0; st.dist = 0; st.mt = 0; st.trk = []; st.t0 = Date.now(); paint(); };
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
  window.gargoSpeedo = { open: open, close: close, kind: kind, hav: hav, where: function (la, lo) { return wLoad().then(function () { return where(la, lo); }); } };
  function news() {   /* 새 기능 알림 — 하루 한 번 · 세 번까지 · 8초 뒤 저절로 닫힘 · 「다시 안 봄」 */
    var K = 'tg_gargo_news_spd', o; try { o = JSON.parse(localStorage.getItem(K) || '{}'); } catch (e) { return; } var d = new Date(), dk = d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate();
    if (o.off || (o.n || 0) >= 3 || o.d === dk || dk > 20261231 || /(^|[#&])(to|spd|q)=/.test(location.hash)) return;
    var tries = 0; (function wait() { var busy = [].some.call(document.querySelectorAll('#gIntro,#gGate,#gCfg,#gList'), function (e) { return e.offsetParent || getComputedStyle(e).display !== 'none' && e.offsetHeight; }); if (busy || document.body.classList.contains('guiding')) { if (++tries < 60) setTimeout(wait, 2000); return; }
      css(); var N = document.createElement('div'); N.id = 'gSpNews'; N.setAttribute('role', 'dialog'); N.innerHTML = '<b>' + (window.gi ? gi('plane') : '✈') + ' 새 기능 — 이동 속도</b><p>비행기 모드에서도 GPS 만으로 <b>비행기·기차 속도·고도</b>를 보고, <b>세계지도</b> 위에서 지금 지나는 나라·가까운 도시를 본다. 통신·저장 없음 — 저가항공·해외여행 때.</p><div class="bt"><button class="go">열어 보기</button><button class="no">다시 안 봄</button></div><i class="bar"></i>';
      document.body.appendChild(N); o.n = (o.n || 0) + 1; o.d = dk; try { localStorage.setItem(K, JSON.stringify(o)); } catch (e) {}
      var t = setTimeout(done, 8000), bar = N.querySelector('.bar'); requestAnimationFrame(function () { bar.style.transitionDuration = '8s'; bar.style.width = '0'; });
      function done() { clearTimeout(t); if (N.parentNode) N.parentNode.removeChild(N); }
      N.querySelector('.go').onclick = function () { done(); open(); }; N.querySelector('.no').onclick = function () { o.off = 1; try { localStorage.setItem(K, JSON.stringify(o)); } catch (e) {} done(); }; })(); }
  function start() { css(); addBtn(); setTimeout(function () { wLoad(); news(); }, 2500); if (/(^|[#&])spd=1(&|$)/.test(location.hash)) setTimeout(open, 300); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
