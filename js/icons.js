/* 데이터 압축지도 아이콘 한 벌 (v2.330.0 · 2026-11-16 형님 「디자인·시각·색채 전권」)
   그림 문자(📍🔍🏠🗂…)는 갤럭시·아이폰·PC 마다 생김새·색·크기가 달라 같은 화면이 기기마다 다르게 보였고,
   색이 든 그림 문자가 위 막대에 스무 개 넘게 모여 지도 위 자료 색과 다퉜다.
   · 네비 가르고(gargo/icons.js)와 같은 그림 말투 — 24칸 · 굵기 2 · 끝 둥글게 · 색 = 글자색(currentColor). 이 파일에서 직접 그렸다(남의 아이콘 묶음 아님).
   · 범위는 「틀」만: 위 막대 첫 줄 · 날짜·빠른 묶음 줄 · 오른쪽 단추 기둥 · 시뮬 알약. 카드·레이어 판·지도 캔버스의 그림 문자는 그대로(자료의 뜻 표시라 손대지 않는다).
   · 그림 문자는 지우지 않고 아이콘 안에 숨겨 둔다(.de) — textContent 로 읽는 코드·검사(📅 …시)가 그대로 돈다. 화면 읽기는 단추의 aria-label 이 맡는다.
   · 같은 그림 문자라도 자리에 따라 뜻이 다르면 다른 그림 — 🏠 홈 ≠ 🏠 부동산(빌딩) · 📍 지역 고르기(핀) ≠ 📍 내 위치(조준).
   · 바꾸면 안 되는 자리는 조상에 class="noicon". */
(function () {
  var P = {
    pin: '<path d="M12 21.5s6.5-6.3 6.5-11.5a6.5 6.5 0 0 0-13 0c0 5.2 6.5 11.5 6.5 11.5z"/><circle cx="12" cy="10" r="2.4"/>',
    loc: '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2.2" class="f"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
    search: '<circle cx="10.5" cy="10.5" r="6"/><path d="M15 15l5.5 5.5"/>',
    home: '<path d="M3.5 11 12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5.5h4V20"/>',
    half: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" class="f"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
    moon: '<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
    layers: '<path d="M12 3.5 21 8.5l-9 5-9-5z"/><path d="M3 12.5l9 5 9-5"/><path d="M3 16.5l9 5 9-5"/>',
    book: '<path d="M12 6.5C10 5 7 4.5 3.5 4.8V19c3.5-.3 6.5.2 8.5 1.7 2-1.5 5-2 8.5-1.7V4.8C17 4.5 14 5 12 6.5z"/><path d="M12 6.5v14"/>',
    cal: '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/><circle cx="8.5" cy="14.5" r="1" class="f"/><circle cx="12" cy="14.5" r="1" class="f"/>',
    people: '<circle cx="9" cy="8.5" r="3"/><path d="M3.5 19.5a5.5 5.5 0 0 1 11 0"/><circle cx="16.5" cy="9.5" r="2.5"/><path d="M15.8 14.1a4.6 4.6 0 0 1 5.2 5.4"/>',
    signal: '<rect x="7.5" y="2" width="9" height="20" rx="3"/><circle cx="12" cy="7" r="2" style="fill:#ef4444;stroke:none"/><circle cx="12" cy="12" r="2" style="fill:#f59e0b;stroke:none"/><circle cx="12" cy="17" r="2" style="fill:#22c55e;stroke:none"/>',   /* 신호등만 세 불 색을 남긴다(가르고와 같음) */
    officer: '<path d="M5.5 8.5h13l-1.4-3.4a1.4 1.4 0 0 0-1.5-.8L12 5 8.4 4.3a1.4 1.4 0 0 0-1.5.8z"/><path d="M7.5 10a4.5 4.5 0 0 0 9 0"/><path d="M4.5 21a7.5 7.5 0 0 1 15 0"/><path d="M12 16.5v2.5"/>',
    shield: '<path d="M12 3 19.5 6v5.5c0 4.6-3.2 8.2-7.5 9.5-4.3-1.3-7.5-4.9-7.5-9.5V6z"/><path d="M9 12l2.2 2.2L15.5 10"/>',
    walk: '<circle cx="13.5" cy="4.5" r="1.8"/><path d="M9.5 21l2.8-6.3L15 17v4"/><path d="M12.3 14.7 11.5 9 8 11v3.5"/><path d="M11.5 9l3 1.6 2.6 2.4"/>',
    card: '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3 9.5h18M6.5 15h4"/>',
    apt: '<rect x="4.5" y="3.5" width="9.5" height="17" rx="1"/><path d="M14 9.5h5.5v11H14"/><path d="M7.5 7.5h3.5M7.5 11h3.5M7.5 14.5h3.5M9.25 20.5v-2.5M16.5 13h1M16.5 16.5h1"/>',
    wx: '<path d="M7 19h9.5a3.5 3.5 0 0 0 0-7 5 5 0 0 0-9.6 1.4A2.8 2.8 0 0 0 7 19z"/><path d="M8.5 6.5V4.5M4.3 8.3 2.9 6.9M12.7 8.3l1.4-1.4"/>',
    receipt: '<path d="M6 3h12v18l-2-1.4-2 1.4-2-1.4-2 1.4-2-1.4L6 21z"/><path d="M9 8h6M9 11.5h6M9 15h4"/>',
    star: '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z"/>',
    tool: '<rect x="3" y="8" width="18" height="12" rx="2"/><path d="M9 8V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V8M3 13h18M10.5 13v2h3v-2"/>',
    flask: '<path d="M9.5 3h5M10.5 3v6L5 18.5A1.7 1.7 0 0 0 6.5 21h11a1.7 1.7 0 0 0 1.5-2.5L13.5 9V3"/><path d="M7.5 15h9"/>'
  };
  var E = { '📍': 'pin', '🔍': 'search', '🏠': 'home', '🌓': 'half', '☀': 'sun', '🌙': 'moon', '🗂': 'layers', '📖': 'book', '📅': 'cal', '👥': 'people', '🚦': 'signal', '👮': 'officer', '🛡': 'shield', '🚶': 'walk', '💳': 'card', '🌦': 'wx', '🧾': 'receipt', '⭐': 'star', '🧰': 'tool', '🧪': 'flask' };
  var CTX = [['#m2dQC', { '🏠': 'apt' }], ['#m2dZoom', { '📍': 'loc' }]];   /* 자리마다 뜻이 다른 그림 문자 */
  var SCOPE = ['#m2dTop .row1', '#m2dChips', '#m2dZoom', '#m2dSimChip', '#m2dSimAChip'];
  var RX = new RegExp('^(\\s*)(' + Object.keys(E).join('|') + ')\\uFE0F?');
  function gi(n) { return P[n] ? '<i class="di di-' + n + '" aria-hidden="true"><svg viewBox="0 0 24 24">' + P[n] + '</svg></i>' : ''; }
  function fixNode(tn) {
    var el = tn.parentNode; if (!el || !el.closest || el.closest('.di,.noicon,input,select,textarea')) return;
    var m = RX.exec(tn.nodeValue || ''); if (!m) return;
    var n = E[m[2]]; for (var i = 0; i < CTX.length; i++) if (el.closest(CTX[i][0]) && CTX[i][1][m[2]]) n = CTX[i][1][m[2]];
    var w = document.createElement('i'); w.className = 'di di-' + n; w.setAttribute('aria-hidden', 'true');
    w.innerHTML = '<svg viewBox="0 0 24 24">' + P[n] + '</svg><span class="de">' + m[2] + '</span>';
    tn.nodeValue = m[1] + tn.nodeValue.slice(m[0].length); el.insertBefore(w, tn);
  }
  function scan() {
    SCOPE.forEach(function (sel) { [].forEach.call(document.querySelectorAll(sel), function (root) {
      var tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), L = [], t; while ((t = tw.nextNode())) L.push(t); L.forEach(fixNode); }); });
  }
  var st = document.createElement('style');
  st.textContent = '.di{display:inline-block;position:relative;width:1.18em;height:1.18em;vertical-align:-.22em;flex:0 0 auto}' +
    '.di svg{display:block;width:100%;height:100%;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}' +
    '.di svg .f{fill:currentColor;stroke:none}' +
    '.di .de{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '#m2dTop .row1>button>.di:only-child,#m2dZoom .di,#m2dTop .row1 #m2dFold>.di{width:1.3em;height:1.3em}' +
    '#m2dToolB .ti .di{width:22px;height:22px}';
  document.head.appendChild(st);
  var due = 0;
  function later() { if (due) return; due = 1; (window.requestAnimationFrame || setTimeout)(function () { due = 0; scan(); }); }
  scan();
  if (window.MutationObserver) {
    var mo = new MutationObserver(later);
    ['m2dTop', 'm2dZoom', 'm2dSimChip', 'm2dSimAChip'].forEach(function (id) { var e = document.getElementById(id); if (e) mo.observe(e, { childList: true, subtree: true, characterData: true }); });
    new MutationObserver(function (ms) { for (var i = 0; i < ms.length; i++) for (var j = 0; j < ms[i].addedNodes.length; j++) { var a = ms[i].addedNodes[j]; if (a.id === 'm2dSimChip' || a.id === 'm2dSimAChip') { mo.observe(a, { childList: true, subtree: true, characterData: true }); later(); } } }).observe(document.body, { childList: true });
  }
  window.TGIcon = { gi: gi, scan: scan, names: Object.keys(P) };
})();
