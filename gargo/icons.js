/* 가르고 아이콘 한 벌 (2026-11-16 · 형님 「디자인 전권 — 아이콘 한 벌부터」)
   그림 문자(🚗🔒🚦…)는 갤럭시·아이폰·PC 마다 생김새·색이 달라 같은 화면이 기기마다 다르게 보였다.
   여기 그린 선 아이콘(24칸 · 굵기 2 · 끝 둥글게 · 색 = 글자색 currentColor)으로 화면 글 속 그림 문자를 바꿔 낀다.
   · 아이콘은 이 파일에서 직접 그렸다(남의 아이콘 묶음을 옮기지 않음).
   · gargo.js 를 고치지 않고 화면에 그려진 글 마디만 바꾼다(MutationObserver) — 입력칸·고르기 목록·지도 캔버스·음성 글은 그대로.
   · 새 코드는 gi('car') 처럼 직접 불러 써도 된다. */
(function () {
  var P = {
    mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M9 21h6"/>',
    lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7.5a4 4 0 0 1 8 0V11"/>',
    signal: '<rect x="7.5" y="2" width="9" height="20" rx="3"/><circle cx="12" cy="7" r="2" style="fill:#ef4444;stroke:none"/><circle cx="12" cy="12" r="2" style="fill:#f59e0b;stroke:none"/><circle cx="12" cy="17" r="2" style="fill:#22c55e;stroke:none"/>',   /* 신호등만 세 불 색을 남긴다 — 「신호」를 한눈에 */
    car: '<path d="M3 16.5v-3.5l2.2-5A2 2 0 0 1 7 7h10a2 2 0 0 1 1.8 1l2.2 5v3.5z"/><path d="M3 13h18"/><circle cx="7.5" cy="17.5" r="1.8"/><circle cx="16.5" cy="17.5" r="1.8"/>',
    police: '<path d="M3 17.5v-3.5l2.2-5A2 2 0 0 1 7 8h10a2 2 0 0 1 1.8 1l2.2 5v3.5z"/><path d="M3 14h18"/><circle cx="7.5" cy="18.5" r="1.6"/><circle cx="16.5" cy="18.5" r="1.6"/><rect x="9.5" y="3" width="5" height="3" rx="1" class="f"/>',
    siren: '<path d="M7 18v-5a5 5 0 0 1 10 0v5"/><rect x="5" y="18" width="14" height="3" rx="1"/><path d="M12 3v2M4.5 6l1.5 1.5M19.5 6 18 7.5"/>',
    vol: '<path d="M4 9.5v5h3.5L12 18.5v-13L7.5 9.5z"/><path d="M15.5 9a4.5 4.5 0 0 1 0 6M18.5 6.5a8 8 0 0 1 0 11"/>',
    loc: '<circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2.2" class="f"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
    cog: '<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="7"/><path d="M12 2.5v2.5M12 19v2.5M2.5 12H5M19 12h2.5M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8"/>',
    half: '<circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" class="f"/>',
    train: '<rect x="5.5" y="3" width="13" height="14" rx="3"/><path d="M5.5 11h13"/><circle cx="9" cy="14" r="1" class="f"/><circle cx="15" cy="14" r="1" class="f"/><path d="M8.5 21l2-4M15.5 21l-2-4"/>',
    home: '<path d="M3.5 11 12 4l8.5 7"/><path d="M6 9.5V20h12V9.5"/><path d="M10 20v-5.5h4V20"/>',
    warn: '<path d="M12 3.5 21.5 20h-19z"/><path d="M12 10v4.5"/><circle cx="12" cy="17.3" r="1" class="f"/>',
    pin: '<path d="M12 21.5s6.5-6.3 6.5-11.5a6.5 6.5 0 0 0-13 0c0 5.2 6.5 11.5 6.5 11.5z"/><circle cx="12" cy="10" r="2.4"/>',
    star: '<path d="m12 3.5 2.6 5.4 5.9.8-4.3 4.1 1 5.8L12 16.8l-5.2 2.8 1-5.8-4.3-4.1 5.9-.8z"/>',
    trash: '<path d="M4 7h16M9.5 7V4.5h5V7M6.2 7l.9 13h9.8l.9-13M10 11v5.5M14 11v5.5"/>',
    cam: '<path d="M4 8.5h3l1.8-2.5h6.4L17 8.5h3V19H4z"/><circle cx="12" cy="13.5" r="3.3"/>',
    pen: '<path d="M4 20l1-4.2L15.8 5a2.1 2.1 0 0 1 3 3L8 18.8z"/><path d="m13.8 7 3 3"/>',
    radar: '<circle cx="12" cy="12" r="1.8" class="f"/><path d="M8.3 8.3a5.2 5.2 0 0 0 0 7.4M15.7 8.3a5.2 5.2 0 0 1 0 7.4M5.5 5.5a9.2 9.2 0 0 0 0 13M18.5 5.5a9.2 9.2 0 0 1 0 13"/>',
    road: '<path d="M8.5 3 4.5 21M15.5 3l4 18M12 4.5v2.5M12 10.5v3M12 17v3"/>',
    door: '<rect x="6" y="3" width="12" height="18" rx="1.5"/><circle cx="14.8" cy="12" r="1" class="f"/>',
    bldg: '<rect x="5" y="3" width="14" height="18" rx="1.5"/><path d="M9 7h1.5M13.5 7H15M9 11h1.5M13.5 11H15M9 15h1.5M13.5 15H15M11 21v-3h2v3"/>',
    tree: '<circle cx="12" cy="9.5" r="6"/><path d="M12 15.5V21M9 21h6"/>',
    hosp: '<rect x="4" y="4" width="16" height="16" rx="3.5"/><path d="M12 8v8M8 12h8"/>',
    share: '<path d="M12 15V3.5M8 7.5l4-4 4 4M5 12v8h14v-8"/>',
    timer: '<circle cx="12" cy="13.5" r="7.5"/><path d="M12 9.5v4l2.5 2M10 2.5h4"/>',
    cone: '<path d="M9.3 4h5.4l3.8 15.5h-13z"/><path d="M7.8 10h8.4M6.6 15h10.8M3.5 19.5h17"/>',
    noent: '<circle cx="12" cy="12" r="8.5"/><path d="M7.5 12h9"/>',
    flag: '<path d="M5.5 21V4M5.5 4.5h12l-2.5 4 2.5 4h-12"/>',
    map: '<path d="M3.5 6.5 9 4.5l6 2 5.5-2v13l-5.5 2-6-2-5.5 2z"/><path d="M9 4.5v13M15 6.5v13"/>',
    srch: '<circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 5 5"/>',
    ok: '<circle cx="12" cy="12" r="8.5"/><path d="m8 12.3 2.7 2.7L16.2 9.3"/>',
    tick: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    clock: '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l-3 2"/>',
    mega: '<path d="M4 10v4h3l8 4.5v-13L7 10z"/><path d="M7 14l1.5 5.5h2.5L10 15M18 9.5a3.5 3.5 0 0 1 0 5"/>',
    school: '<path d="M3 9.5 12 5l9 4.5-9 4.5z"/><path d="M7 11.5V16c1.5 1.3 3.2 2 5 2s3.5-.7 5-2v-4.5M21 9.5V15"/>',
    bolt: '<path d="M13.5 2.5 5.5 13.5h6l-1 8 8-11h-6z"/>',
    clip: '<rect x="5.5" y="4.5" width="13" height="16.5" rx="2"/><rect x="9" y="3" width="6" height="3.5" rx="1"/><path d="M9 11h6M9 15h4"/>',
    scale: '<path d="M12 4v16M7 20h10M5 7h14"/><path d="M5 7 2.5 13a2.8 2.8 0 0 0 5 0zM19 7l-2.5 6a2.8 2.8 0 0 0 5 0z"/>',
    ruler: '<path d="M3.5 16.5 16.5 3.5l4 4-13 13z"/><path d="M7 13l1.5 1.5M10 10l1.5 1.5M13 7l1.5 1.5"/>',
    radio: '<rect x="3.5" y="9" width="17" height="11" rx="2"/><path d="m7 9 10-5"/><circle cx="15.5" cy="14.5" r="2.5"/><path d="M7 13h3M7 16h3"/>',
    cup: '<path d="M4.5 9h12v5a5 5 0 0 1-5 5h-2a5 5 0 0 1-5-5z"/><path d="M16.5 10.5h1.5a2.5 2.5 0 0 1 0 5h-1.8M8 3.5v2.5M11.5 3.5v2.5"/>',
    puzzle: '<path d="M5 7h4a2 2 0 1 1 4 0h4v4a2 2 0 1 1 0 4v4h-4a2 2 0 1 0-4 0H5v-4a2 2 0 1 0 0-4z"/>',
    mask: '<path d="M4 6c5 2 11 2 16 0v5c0 5-3.6 8.5-8 8.5S4 16 4 11z"/><path d="M8.5 11h2M13.5 11h2M9.5 15c1.6 1 3.4 1 5 0"/>',
    brain: '<path d="M12 5.5a3 3 0 0 0-5.5 1A3 3 0 0 0 5 11.5a3 3 0 0 0 1.5 5 3 3 0 0 0 5.5 1.5zM12 5.5a3 3 0 0 1 5.5 1 3 3 0 0 1 1.5 5 3 3 0 0 1-1.5 5 3 3 0 0 1-5.5 1.5"/>',
    sat: '<path d="m7 7 4 4M5 9l4-4 4 4-4 4zM15 11l4 4-4 4-4-4z"/><path d="M11 13l2-2M16 5a4 4 0 0 1 3 3"/>',
    kids: '<circle cx="8" cy="5.5" r="2"/><circle cx="16" cy="7.5" r="1.8"/><path d="M8 8.5v6l-2 6M8 14.5l2 6M5 11h6M16 10.5v5l-1.5 5M16 15.5l1.5 5M13.5 12.5h5"/>',
    truck: '<path d="M3 17.5V8h11v9.5M14 11h4l3 3.5v3"/><path d="M3 17.5h18"/><circle cx="7" cy="18" r="1.7"/><circle cx="17" cy="18" r="1.7"/><path d="M6 11h5"/>',
    play: '<path d="M7 4.5v15l12-7.5z" class="f"/>',
    stop: '<rect x="6" y="6" width="12" height="12" rx="2" class="f"/>',
    dotY: '<circle cx="12" cy="12" r="7" class="f" style="fill:#f59e0b;stroke:none"/>',
    dotG: '<circle cx="12" cy="12" r="7" class="f" style="fill:#16a34a;stroke:none"/>'
  };
  var M = {
    '🎤': 'mic', '🔒': 'lock', '🚦': 'signal', '🚗': 'car', '🚓': 'police', '🚨': 'siren', '🔊': 'vol', '◎': 'loc', '⚙': 'cog', '◐': 'half',
    '🚇': 'train', '🏠': 'home', '⚠': 'warn', '📍': 'pin', '📌': 'pin', '⭐': 'star', '🗑': 'trash', '📷': 'cam', '✍': 'pen', '✎': 'pen',
    '📡': 'radar', '🛣': 'road', '🚪': 'door', '🏢': 'bldg', '🌳': 'tree', '✚': 'hosp', '📤': 'share', '⏱': 'timer', '🚧': 'cone', '⛔': 'noent',
    '🏁': 'flag', '🗺': 'map', '🔎': 'srch', '✅': 'ok', '✓': 'tick', '🕘': 'clock', '📢': 'mega', '🏫': 'school', '⚡': 'bolt', '📋': 'clip',
    '⚖': 'scale', '📐': 'ruler', '📻': 'radio', '☕': 'cup', '🧩': 'puzzle', '🎭': 'mask', '🧠': 'brain', '🛰': 'sat', '🚸': 'kids', '🚒': 'truck',
    '▶': 'play', '⏹': 'stop', '🟡': 'dotY', '🟢': 'dotG'
  };
  function svg(n) { return '<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">' + P[n] + '</svg>'; }
  window.gi = function (n) { return P[n] ? '<i class="gi gi-' + n + '">' + svg(n) + '</i>' : ''; };
  var keys = Object.keys(M).sort(function (a, b) { return b.length - a.length; }).map(function (k) { return k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); });
  var RX = new RegExp('(' + keys.join('|') + ')️?', 'g'), RX1 = new RegExp(RX.source);
  var SKIP = { SCRIPT: 1, STYLE: 1, TEXTAREA: 1, INPUT: 1, OPTION: 1, SELECT: 1, TITLE: 1, CANVAS: 1, NOSCRIPT: 1 };
  function skip(el) { for (var e = el; e && e !== document.body; e = e.parentNode) { if (e.nodeType !== 1) continue; if (SKIP[e.nodeName] || e.namespaceURI === 'http://www.w3.org/2000/svg' || e.isContentEditable || (e.classList && (e.classList.contains('gi') || e.classList.contains('noicon')))) return true; } return false; }
  function swap(t) {
    var s = t.nodeValue, f = document.createDocumentFragment(), last = 0, m; RX.lastIndex = 0;
    while ((m = RX.exec(s))) {
      if (m.index > last) f.appendChild(document.createTextNode(s.slice(last, m.index)));
      var i = document.createElement('i'); i.className = 'gi gi-' + M[m[1]]; i.setAttribute('aria-hidden', 'true'); i.innerHTML = svg(M[m[1]]); f.appendChild(i);
      last = m.index + m[0].length;
    }
    if (last < s.length) f.appendChild(document.createTextNode(s.slice(last)));
    if (t.parentNode) t.parentNode.replaceChild(f, t);
  }
  function scan(root) {
    if (!root) return;
    if (root.nodeType === 3) { if (RX1.test(root.nodeValue) && !skip(root.parentNode)) swap(root); return; }
    if (root.nodeType !== 1 || skip(root)) return;
    var w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, null), n, hit = [];
    while ((n = w.nextNode())) if (RX1.test(n.nodeValue) && !skip(n.parentNode)) hit.push(n);
    hit.forEach(swap);
  }
  var Q = [], due = false;
  function flush() { due = false; var q = Q; Q = []; q.forEach(scan); }
  function start() {
    scan(document.body);
    new MutationObserver(function (ms) {
      ms.forEach(function (m) { if (m.type === 'characterData') Q.push(m.target); else for (var i = 0; i < m.addedNodes.length; i++) Q.push(m.addedNodes[i]); });
      if (!due && Q.length) { due = true; (window.requestAnimationFrame || setTimeout)(flush); }
    }).observe(document.body, { childList: true, subtree: true, characterData: true });
  }
  window.giScan = scan;
  if (document.body) start(); else document.addEventListener('DOMContentLoaded', start);
})();
