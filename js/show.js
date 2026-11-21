/* 데이터 압축지도 — 🎬 그림으로 보는 「이 지도로 할 수 있는 것」(2026-11-22 · 소유자 「설정 칸에 할 수 있는 것을 이미지와 모션으로 — 모르는 사람은 아예 모른다 · 어떻게 쓰는지 시각적으로」 · 움직이는 그림으로 고름)
   ⚙ 설정 판(#m2dSet · map2d.js setPaint) 맨 위에 「🎬 그림으로 보기」 칸을 끼운다 — map2d.js 는 고치지 않는다(판을 다시 그릴 때마다 MutationObserver 로 다시 끼움)
   장면마다 = 무엇을 하나 한 줄 · 움직이는 그림(SVG + CSS) · 어디서 여나(메뉴 길)
   그림 속 숫자·이름은 모두 「그림 예시」다 — 실제 자료를 읽지 않는다(통신 0 · 저장 0) · 움직임 줄이기를 켠 기기는 멈춘 그림 · 판이 닫혀 있으면 초 세기 멈춤
   열기: 설정 판 칸 · 주소 #show=1 · window.tgShow.open() */
(function () {
  'use strict';
  var RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  var CSS = [
    '#m2dShow{display:none;position:fixed;inset:0;z-index:2790;background:var(--panel,#fff);color:var(--ink,#111827);overflow-y:auto;padding:12px 14px calc(24px + env(safe-area-inset-bottom))}',
    '#m2dShow.on{display:block}',
    '#m2dShow .wh{position:sticky;top:-12px;z-index:2;display:flex;align-items:center;gap:8px;background:var(--panel,#fff);padding:10px 0 8px;margin-top:-12px;border-bottom:1px solid var(--line,#e2e7ee)}',
    '#m2dShow .wh b{font-size:18px}',
    '#m2dShow .wx{margin-left:auto;border:0;background:#dc2626;color:#fff;border-radius:16px;padding:7px 13px;font-weight:800;font-size:14px;cursor:pointer}',
    '#m2dShow .wd{font-size:13px;color:var(--ink2,#4b5563);margin:8px 0 4px;line-height:1.5}',
    '#m2dShow .wf{display:flex;gap:6px;overflow-x:auto;padding:6px 0 4px;scrollbar-width:none}',
    '#m2dShow .wf button{flex:none;border:1px solid var(--line,#e2e7ee);background:transparent;color:inherit;border-radius:16px;padding:6px 11px;font-size:13px;font-weight:700;cursor:pointer}',
    '#m2dShow .wf button.on{background:#1d4ed8;border-color:#1d4ed8;color:#fff}',
    '#m2dShow .wg{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin-top:8px}',
    '#m2dShow .sc{border:1px solid var(--line,#e2e7ee);border-radius:16px;overflow:hidden;background:var(--panel,#fff)}',
    '#m2dShow .sc h5{margin:0;padding:11px 12px 2px;font-size:16px}',
    '#m2dShow .sc p{margin:0;padding:0 12px 8px;font-size:13px;line-height:1.5;color:var(--ink2,#4b5563)}',
    '#m2dShow .sc svg{display:block;width:100%;height:auto;background:#eef2f7}',
    'html.dark #m2dShow .sc svg{background:#0f1a2c}',
    '#m2dShow .sc .wy{padding:8px 12px 11px;font-size:12.5px;border-top:1px dashed var(--line,#e2e7ee)}',
    '#m2dShow .sc .wy b{color:#1d4ed8}',
    'html.dark #m2dShow .sc .wy b{color:#8fb3ff}',
    '#m2dShow .ex{font-size:11px;fill:#64748b}',
    '#m2dShow .t{font:700 12px system-ui,sans-serif;fill:#1f2937}',
    'html.dark #m2dShow .t{fill:#e5ebf3}',
    '#m2dShow .rd{fill:#cbd5e1}',
    'html.dark #m2dShow .rd{fill:#33435e}',
    '#m2dShow .rdl{stroke:#cbd5e1}',
    'html.dark #m2dShow .rdl{stroke:#33435e}',
    '#m2dShow .bk{fill:#dbe3ee}',
    'html.dark #m2dShow .bk{fill:#1b2940}',
    '#m2dShow .wn{fill:#fff;stroke:#cbd5e1}',
    'html.dark #m2dShow .wn{fill:#172033;stroke:#33435e}',
    '#m2dSet .shw{margin-top:12px;border:0;width:100%;text-align:left;cursor:pointer;border-radius:14px;padding:12px;background:linear-gradient(135deg,#1d4ed8,#7c3aed);color:#fff;display:flex;align-items:center;gap:10px}',
    '#m2dSet .shw svg{flex:none;width:92px;height:46px;border-radius:9px;background:rgba(255,255,255,.14)}',
    '#m2dSet .shw b{display:block;font-size:15px}',
    '#m2dSet .shw small{display:block;font-size:12px;opacity:.9;margin-top:2px;line-height:1.4}',
    /* 움직임 — 장면마다 8초 한 바퀴 */
    '@keyframes sgG{0%,48%{opacity:1}50%,100%{opacity:.15}}',
    '@keyframes sgY{0%,48%{opacity:.15}50%,58%{opacity:1}60%,100%{opacity:.15}}',
    '@keyframes sgR{0%,58%{opacity:.15}60%,100%{opacity:1}}',
    '@keyframes sgCar{0%{transform:translateX(0)}48%{transform:translateX(330px)}48.1%,100%{transform:translateX(-40px)}}',
    '@keyframes sgCarV{0%,60%{transform:translateY(-60px)}100%{transform:translateY(220px)}}',
    '@keyframes spd{0%,20%{stroke:#16a34a}35%,55%{stroke:#f59e0b}70%,90%{stroke:#dc2626}100%{stroke:#16a34a}}',
    '@keyframes spd2{0%,30%{stroke:#16a34a}50%,100%{stroke:#f59e0b}}',
    '@keyframes spdT{0%,20%{opacity:0}30%,90%{opacity:1}100%{opacity:0}}',
    '@keyframes qIn{0%{transform:translateX(-120px)}40%,60%{transform:translateX(0)}100%{transform:translateX(320px)}}',
    '@keyframes sqR{0%,58%{opacity:1}60%,100%{opacity:.15}}',
    '@keyframes sqG{0%,58%{opacity:.15}60%,100%{opacity:1}}',
    '@keyframes lnk{0%,10%{stroke-dashoffset:120}40%,100%{stroke-dashoffset:0}}',
    '@keyframes popA{0%{transform:scale(0)}12%,100%{transform:scale(1)}}',
    '@keyframes tap{0%,8%{opacity:0;transform:scale(.4)}12%{opacity:1;transform:scale(1)}22%,100%{opacity:0;transform:scale(1.8)}}',
    '@keyframes card{0%,18%{transform:translateY(160px)}30%,90%{transform:translateY(0)}100%{transform:translateY(160px)}}',
    '@keyframes bar{0%,30%{transform:scaleX(0)}45%,90%{transform:scaleX(1)}100%{transform:scaleX(0)}}',
    '@keyframes rain{0%{transform:translateY(-30px)}100%{transform:translateY(170px)}}',
    '@keyframes wat{0%,15%{transform:translateY(46px)}60%,90%{transform:translateY(0)}100%{transform:translateY(46px)}}',
    '@keyframes wroad{0%,45%{fill:#94a3b8}60%,90%{fill:#2563eb}100%{fill:#94a3b8}}',
    '@keyframes ring{0%{r:4;opacity:.9}100%{r:110;opacity:0}}',
    '@keyframes drive{0%,10%{offset-distance:0%}90%,100%{offset-distance:100%}}',
    '@keyframes draw{0%,35%{stroke-dashoffset:420}75%,100%{stroke-dashoffset:0}}',
    '@keyframes ask{0%,14%{opacity:0;transform:translateY(8px)}18%,34%{opacity:1;transform:translateY(0)}38%,100%{opacity:0}}',
    '@keyframes fin{0%,34%{opacity:0}40%,100%{opacity:1}}',
    '@keyframes dl{0%{transform:translateY(-30px);opacity:0}30%{opacity:1}60%,100%{transform:translateY(10px);opacity:0}}',
    '@keyframes fill{0%,10%{transform:scaleX(0)}55%,100%{transform:scaleX(1)}}',
    '@keyframes off{0%,60%{opacity:0}66%,100%{opacity:1}}',
    '@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}',
    '#m2dShow .an *{animation-duration:8s;animation-iteration-count:infinite;animation-timing-function:ease-in-out;transform-box:fill-box;transform-origin:center}',
    '#m2dShow.paused .an *,#m2dSet.paused .shw *{animation-play-state:paused!important}',
    '@media (prefers-reduced-motion: reduce){#m2dShow .an *,#m2dSet .shw *{animation:none!important}}'
  ].join('\n');

  var PK = {};
  function pk(d) { d = Math.round(d); if (!PK[d]) PK[d] = '@keyframes pp' + d + '{0%,' + d + '%{transform:scale(0)}' + Math.min(99, d + 8) + '%,100%{transform:scale(1)}}'; return 'pp' + d; }
  function ex(x, y) { return '<text class="ex" x="' + (x || 296) + '" y="' + (y || 166) + '" text-anchor="end">그림 예시</text>'; }
  var SV = '<svg viewBox="0 0 300 170" role="img" class="an" aria-label="';

  /* 장면: [키, 갈래, 제목, 하는 일, 어디서, 그림(aria 글, svg 안쪽)] — 갈래 w 일 · p 경찰 · l 생활 */
  var SC = [
    ['sig', 'w', '🚦 신호가 몇 초 남았나', '교차로를 누르면 방향마다 녹색·적색 길이와 지금 몇 초 남았는지(값을 받은 교차로) 본다. 차가 녹색에 지나고 적색에 선다.', '레이어 판 → <b>🚦 신호 주기</b> 켜고 교차로 누르기',
      '신호가 녹색에서 황색, 적색으로 바뀌는 교차로',
      '<rect class="rd" x="0" y="66" width="300" height="38"/><rect class="rd" x="131" y="0" width="38" height="170"/>' +
      '<rect class="bk" x="8" y="8" width="112" height="50" rx="6"/><rect class="bk" x="180" y="112" width="112" height="50" rx="6"/>' +
      '<g style="animation-name:sgCar;animation-timing-function:linear"><rect x="-30" y="72" width="26" height="12" rx="3" fill="#2563eb"/></g>' +
      '<g style="animation-name:sgCarV;animation-timing-function:linear"><rect x="152" y="0" width="12" height="24" rx="3" fill="#7c3aed"/></g>' +
      '<rect x="182" y="12" width="26" height="70" rx="6" fill="#111827"/>' +
      '<circle data-sg="1" cx="195" cy="26" r="8" fill="#22c55e" style="animation-name:sgG;animation-timing-function:steps(1)"/>' +
      '<circle cx="195" cy="47" r="8" fill="#facc15" style="animation-name:sgY;animation-timing-function:steps(1)"/>' +
      '<circle cx="195" cy="68" r="8" fill="#ef4444" style="animation-name:sgR;animation-timing-function:steps(1)"/>' +
      '<rect class="wn" x="216" y="12" width="78" height="46" rx="8"/><text class="t" x="255" y="30" text-anchor="middle">남은 초</text><text x="255" y="51" text-anchor="middle" style="font:800 18px system-ui;fill:#16a34a" data-cd="sig">32</text>' + ex()],
    ['spd', 'w', '🚗 지금 어디가 막히나', '길이 초록 → 노랑 → 빨강으로 바뀐다. 지금 실제 속도(10분마다)와 평소 이 시각 속도(여섯 구)를 나란히 본다.', '레이어 판 → <b>🚦 지금 도로 소통(ITS)</b>',
      '도로 색이 시간에 따라 초록에서 빨강으로 바뀜',
      '<rect class="bk" x="0" y="0" width="300" height="170"/>' +
      '<path d="M10 140 C 80 120, 120 60, 290 40" class="rdl" stroke-width="16" fill="none"/>' +
      '<g stroke-width="10" stroke-linecap="round" fill="none"><line x1="14" y1="138" x2="80" y2="123" style="animation-name:spd2"/><line x1="92" y1="116" x2="150" y2="76" style="animation-name:spd"/><line x1="164" y1="68" x2="286" y2="42" style="animation-name:spd2"/></g>' +
      '<g style="animation-name:spdT"><rect class="wn" x="150" y="96" width="140" height="48" rx="9"/><text class="t" x="160" y="115">지금 시속 12km</text><text class="ex" x="160" y="134" text-anchor="start">평소 이 시각 31km</text></g>' + ex(296, 18)],
    ['sim', 'w', '🧪 신호를 바꾸면 어떻게 될까', '막히는 교차로를 골라 신호 길이·막는 차로를 바꿔 본다. 지금 신호와 바꾼 신호를 같은 차로 돌려 견준다.', '🧰 도구 → <b>🧪 시뮬 — 막히는 교차로 고르기</b>',
      '차들이 적색에 줄 서고 녹색에 빠져나감',
      '<rect class="rd" x="0" y="60" width="300" height="50"/><line x1="200" y1="60" x2="200" y2="110" stroke="#fff" stroke-width="3"/>' +
      [0, 1, 2, 3, 4].map(function (i) { return '<g style="animation-name:qIn"><rect x="' + (170 - i * 32) + '" y="' + (i % 2 ? 88 : 66) + '" width="26" height="14" rx="3" fill="' + ['#2563eb', '#0891b2', '#7c3aed', '#db2777', '#ea580c'][i] + '"/></g>'; }).join('') +
      '<rect x="206" y="112" width="14" height="32" rx="4" fill="#111827"/><circle cx="213" cy="120" r="5" fill="#ef4444" style="animation-name:sqR;animation-timing-function:steps(1)"/><circle cx="213" cy="136" r="5" fill="#22c55e" style="animation-name:sqG;animation-timing-function:steps(1)"/>' +
      '<rect x="210" y="8" width="84" height="44" rx="8" class="wn"/><text class="t" x="252" y="26" text-anchor="middle">지금 판 ⏳ 14대</text><text class="t" x="252" y="44" text-anchor="middle" style="fill:#16a34a">바꾼 판 ⏳ 6대</text>' +
      '<text class="t" x="10" y="140">적색 → 줄 · 녹색 → 빠짐</text>' + ex()],
    ['lnk', 'w', '🧩 무엇이 무엇과 이어졌나', '교차로 하나에서 사고·상권·지하철역·지구대가 왜 이어졌는지(자리·때·코드)와 그 근거·확실한 정도(A~E)를 줄로 본다.', '🧰 도구 → <b>🧩 엮임 보기</b> · 교차로 카드의 🧩 단추',
      '가운데 교차로에서 사고, 상권, 역, 지구대로 줄이 뻗어 나감',
      '<g stroke="#64748b" stroke-width="2.5" fill="none" stroke-dasharray="120" style="animation-name:lnk">' +
      '<line x1="150" y1="85" x2="50" y2="35"/><line x1="150" y1="85" x2="250" y2="35"/><line x1="150" y1="85" x2="50" y2="138"/><line x1="150" y1="85" x2="250" y2="138"/></g>' +
      '<circle cx="150" cy="85" r="26" fill="#1d4ed8"/><text x="150" y="90" text-anchor="middle" style="font:800 13px system-ui;fill:#fff">교차로</text>' +
      [[50, 35, '💥 사고', 'A', 20], [250, 35, '🏪 상권', 'B', 30], [50, 138, '🚇 역', 'C', 40], [250, 138, '👮 지구대', 'B', 50]].map(function (n) { return '<g style="animation-name:' + pk(n[4]) + '"><rect class="wn" x="' + (n[0] - 46) + '" y="' + (n[1] - 15) + '" width="92" height="30" rx="15"/><text class="t" x="' + (n[0] - 10) + '" y="' + (n[1] + 5) + '" text-anchor="middle">' + n[2] + '</text><circle cx="' + (n[0] + 34) + '" cy="' + n[1] + '" r="9" fill="#f59e0b"/><text x="' + (n[0] + 34) + '" y="' + (n[1] + 4) + '" text-anchor="middle" style="font:800 11px system-ui;fill:#fff">' + n[3] + '</text></g>'; }).join('') + ex(296, 166)],
    ['dong', 'l', '📍 이 동네는 어떤 곳인가', '지도를 누르면 그 동의 사람(지금 머무는 수)·가게·사고·집값이 카드로 올라온다. 막대로 한눈에 본다.', '지도에서 아무 동이나 <b>누르기</b>',
      '지도를 누르면 아래에서 막대 카드가 올라옴',
      '<rect class="bk" x="0" y="0" width="300" height="170"/><path d="M20 20 L140 10 L160 80 L60 95 Z M170 15 L285 30 L270 95 L175 85 Z" fill="none" stroke="#94a3b8" stroke-width="1.5"/>' +
      '<circle cx="100" cy="52" r="14" fill="none" stroke="#1d4ed8" stroke-width="3" style="animation-name:tap"/>' +
      '<g style="animation-name:card"><rect class="wn" x="10" y="74" width="280" height="92" rx="12"/><text class="t" x="22" y="94">○○동 한눈에</text>' +
      [['👥 지금 사람', 0.8, '#2563eb'], ['🏪 가게', 0.55, '#16a34a'], ['💥 사고', 0.35, '#dc2626']].map(function (b, i) { var y = 104 + i * 19; return '<text class="ex" x="22" y="' + (y + 10) + '" text-anchor="start">' + b[0] + '</text><rect x="100" y="' + y + '" width="170" height="11" rx="5" fill="#e2e8f0"/><rect x="100" y="' + y + '" width="' + Math.round(170 * b[1]) + '" height="11" rx="5" fill="' + b[2] + '" style="animation-name:bar;transform-origin:left"/>'; }).join('') + '</g>' + ex(296, 14)],
    ['deal', 'l', '🏷 최근에 얼마에 팔렸나', '아파트·땅·상가·전월세 실거래가 지도 위에 뜬다. 누르면 그 단지·그 리의 최근 거래를 본다.', '🧰 도구 → <b>🏷 최근 거래 찾기</b> · 레이어 <b>🏠 집·땅</b>',
      '지도 위에 거래 가격 말풍선이 차례로 뜸',
      '<rect class="bk" x="0" y="0" width="300" height="170"/><rect class="rd" x="0" y="100" width="300" height="10"/><rect class="rd" x="120" y="0" width="10" height="170"/>' +
      [[60, 60, '9.8억', 10], [210, 50, '전세 5억', 25], [80, 145, '땅 3건', 40], [230, 138, '12.4억', 55]].map(function (p) { return '<g style="animation-name:' + pk(p[3]) + ';transform-origin:center bottom"><rect x="' + (p[0] - 36) + '" y="' + (p[1] - 30) + '" width="72" height="24" rx="12" fill="#1d4ed8"/><text x="' + p[0] + '" y="' + (p[1] - 13) + '" text-anchor="middle" style="font:800 12px system-ui;fill:#fff">' + p[2] + '</text><path d="M' + (p[0] - 5) + ' ' + (p[1] - 7) + ' L' + p[0] + ' ' + p[1] + ' L' + (p[0] + 5) + ' ' + (p[1] - 7) + 'Z" fill="#1d4ed8"/></g>'; }).join('') + ex(296, 14)],
    ['dec', 'p', '🧭 오늘 어디에 설까', '음주단속·교통근무 자리 후보를 사고·주점·시간대 근거와 함께 늘어놓는다. 점수로 섞지 않고 판단은 사람이 한다.', '홈 → <b>👮 경찰 전용</b> · 🧰 도구 → <b>🧭 오늘의 결정</b>',
      '후보 자리 세 곳 옆에 근거 쪽지가 차례로 붙음',
      '<rect class="bk" x="0" y="0" width="300" height="170"/>' +
      [[40, '①', '○○사거리', ['💥 밤 사고', '🍺 주점']], [90, '②', '△△역 앞', ['🕙 22시 몰림']], [140, '③', '□□로', ['💥 사고']]].map(function (r, i) { return '<g style="animation-name:' + pk(10 + i * 12) + ';transform-origin:left center"><circle cx="24" cy="' + (r[0] - 4) + '" r="12" fill="#dc2626"/><text x="24" y="' + r[0] + '" text-anchor="middle" style="font:800 12px system-ui;fill:#fff">' + r[1] + '</text><text class="t" x="44" y="' + r[0] + '">' + r[2] + '</text></g>' + r[3].map(function (c, j) { return '<g style="animation-name:' + pk(40 + i * 10 + j * 6) + '"><rect x="' + (128 + j * 82) + '" y="' + (r[0] - 17) + '" width="76" height="22" rx="11" fill="#fef3c7" stroke="#f59e0b"/><text x="' + (166 + j * 82) + '" y="' + (r[0] - 2) + '" text-anchor="middle" style="font:700 11px system-ui;fill:#92400e">' + c + '</text></g>'; }).join(''); }).join('') +
      '<text class="ex" x="10" y="164" text-anchor="start">판단은 사람이 — 근거만 모아 보여 준다</text>'],
    ['rain', 'p', '🌧 큰비에 어디가 잠기나', '비가 많이 오면 예전에 잠겼던 길·침수 흔적·지하차도를 먼저 보여 준다.', '홈 → <b>🎯 지금 상황으로 보기 → 🌧 큰비</b>',
      '비가 내리고 물이 차오르며 길이 파랗게 바뀜',
      '<defs><clipPath id="shwC"><rect x="0" y="0" width="300" height="170"/></clipPath></defs><g clip-path="url(#shwC)">' +
      '<rect x="0" y="118" width="300" height="20" style="animation-name:wroad"/>' +
      [20, 60, 100, 140, 180, 220, 260].map(function (x, i) { return '<line x1="' + x + '" y1="0" x2="' + (x - 6) + '" y2="16" stroke="#60a5fa" stroke-width="2" style="animation-name:rain;animation-duration:' + (0.8 + (i % 3) * 0.15) + 's;animation-timing-function:linear;animation-delay:' + (-i * 0.2) + 's"/>'; }).join('') +
      '<rect x="0" y="124" width="300" height="60" fill="rgba(37,99,235,.35)" style="animation-name:wat"/></g>' +
      '<rect class="wn" x="150" y="12" width="140" height="44" rx="9"/><text class="t" x="160" y="30">⚠ 잠겼던 길</text><text class="ex" x="160" y="48" text-anchor="start">지하차도 · 침수 흔적</text>' + ex(296, 166)],
    ['prd', 'p', '🚨 신고된 차는 지금 어디쯤', '신고 시각과 달아난 방향을 넣으면 그 뒤 몇 분 동안 갈 수 있는 길이 넓어지는 모양으로 보인다.', '🧰 도구 → <b>🚨 신고 차량 예측</b>',
      '신고 자리에서 퍼지는 원과 길을 따라 움직이는 차',
      '<rect class="bk" x="0" y="0" width="300" height="170"/><rect class="rd" x="0" y="80" width="300" height="12"/><rect class="rd" x="80" y="0" width="12" height="170"/><rect class="rd" x="210" y="0" width="12" height="170"/>' +
      '<circle cx="86" cy="86" r="4" fill="none" stroke="#dc2626" stroke-width="3" style="animation-name:ring;animation-duration:3s"/><circle cx="86" cy="86" r="4" fill="none" stroke="#dc2626" stroke-width="3" style="animation-name:ring;animation-duration:3s;animation-delay:-1.5s"/>' +
      '<circle cx="86" cy="86" r="7" fill="#dc2626"/><text class="t" x="96" y="72">신고 자리</text>' +
      '<g style="offset-path:path(\'M86 86 L216 86 L216 10\');animation-name:drive;animation-timing-function:linear"><rect x="-9" y="-5" width="18" height="10" rx="3" fill="#111827"/></g>' +
      '<text class="t" x="230" y="120">5분 뒤</text><text class="t" x="230" y="138">이쯤?</text>' + ex()],
    ['nav', 'w', '🧭 신호를 아는 길 안내', '지도를 두 번 톡 하면 「여기를 목적지로 할까요?」를 묻고, 신호 대기를 셈한 길을 그린다.', '🧰 도구 → <b>🧭 네비 가르고</b>(서초 시험판)',
      '두 번 톡 하면 목적지 확인이 뜨고 길이 그려짐',
      '<rect class="bk" x="0" y="0" width="300" height="170"/><rect class="rd" x="0" y="120" width="300" height="10"/><rect class="rd" x="230" y="0" width="10" height="170"/><rect class="rd" x="40" y="0" width="10" height="170"/>' +
      '<circle cx="235" cy="30" r="12" fill="none" stroke="#1d4ed8" stroke-width="3" style="animation-name:tap"/><circle cx="235" cy="30" r="12" fill="none" stroke="#1d4ed8" stroke-width="3" style="animation-name:tap;animation-delay:.25s"/>' +
      '<g style="animation-name:ask"><rect class="wn" x="80" y="20" width="140" height="56" rx="10"/><text class="t" x="150" y="40" text-anchor="middle">목적지로 할까요?</text><rect x="100" y="50" width="100" height="18" rx="9" fill="#1d4ed8"/><text x="150" y="63" text-anchor="middle" style="font:800 11px system-ui;fill:#fff">✔ 목적지로</text></g>' +
      '<path d="M45 160 L45 125 L235 125 L235 30" fill="none" stroke="#1d4ed8" stroke-width="5" stroke-linecap="round" stroke-dasharray="420" style="animation-name:draw"/>' +
      '<g style="animation-name:fin"><circle cx="45" cy="160" r="6" fill="#16a34a"/><text class="t" x="56" y="112">🚦 신호 대기 셈 · 7분</text></g>' + ex(296, 166)],
    ['get', 'l', '📥 통신이 안 되는 곳에서도', '다니는 구를 미리 받아 두면 지하·산속처럼 통신이 끊긴 곳에서도 지도가 열린다.', '🧰 도구 → <b>📥 지역 받기</b>',
      '내려받기 화살표가 내려오고 통신이 끊겨도 지도가 열림',
      '<rect class="wn" x="90" y="10" width="120" height="150" rx="16"/><rect class="bk" x="100" y="28" width="100" height="100" rx="6"/>' +
      '<g style="animation-name:dl;animation-duration:2s"><path d="M150 40 L150 70 M138 60 L150 72 L162 60" stroke="#1d4ed8" stroke-width="5" fill="none" stroke-linecap="round"/></g>' +
      '<rect x="105" y="136" width="90" height="10" rx="5" fill="#e2e8f0"/><rect x="105" y="136" width="90" height="10" rx="5" fill="#16a34a" style="animation-name:fill;transform-origin:left"/>' +
      '<g style="animation-name:off"><text x="240" y="60" text-anchor="middle" style="font:800 26px system-ui">📵</text><text class="t" x="240" y="86" text-anchor="middle">통신 끊김</text><text class="t" x="240" y="104" text-anchor="middle" style="fill:#16a34a">그래도 열림</text></g>']
  ];
  var CAT = [['all', '전부'], ['w', '🚦 길·신호'], ['p', '👮 경찰 일'], ['l', '🏠 생활·동네']], CUR = 'all';

  function card(s) { return '<div class="sc" data-c="' + s[1] + '"><h5>' + s[2] + '</h5><p>' + s[3] + '</p>' + SV + s[5] + '">' + s[6] + '</svg><div class="wy">📍 어디서: ' + s[4] + '</div></div>'; }
  function css() { if (document.getElementById('m2dShowCss')) return; var st = document.createElement('style'); st.id = 'm2dShowCss'; st.textContent = CSS + ' ' + Object.keys(PK).map(function (k) { return PK[k]; }).join(' '); document.head.appendChild(st); }
  function el() { var e = document.getElementById('m2dShow'); if (e) return e;
    css();
    e = document.createElement('div'); e.id = 'm2dShow'; e.setAttribute('role', 'dialog'); e.setAttribute('aria-label', '그림으로 보는 할 수 있는 것');
    e.innerHTML = '<div class="wh"><b>🎬 이 지도로 할 수 있는 것</b><button class="wx" data-w="x">✕ 닫기</button></div>' +
      '<p class="wd">그림이 저절로 움직입니다. 그림 속 숫자·이름은 <b>예시</b>이고, 아래 「어디서」를 따라가면 실제 화면이 열립니다.' + (RM ? ' (이 기기는 움직임 줄이기가 켜져 있어 멈춘 그림으로 보입니다)' : '') + '</p>' +
      '<div class="wf">' + CAT.map(function (c) { return '<button data-f="' + c[0] + '"' + (c[0] === CUR ? ' class="on"' : '') + '>' + c[1] + '</button>'; }).join('') + '</div>' +
      '<div class="wg">' + SC.map(card).join('') + '</div>';
    document.body.appendChild(e);
    e.addEventListener('click', function (ev) { var b = ev.target.closest('[data-w],[data-f]'); if (!b) return;
      if (b.getAttribute('data-w') === 'x') { close(); return; }
      CUR = b.getAttribute('data-f'); e.querySelectorAll('.wf button').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-f') === CUR); });
      e.querySelectorAll('.sc').forEach(function (x) { x.style.display = CUR === 'all' || x.getAttribute('data-c') === CUR ? '' : 'none'; }); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && isOn()) close(); });
    return e; }
  function isOn() { var e = document.getElementById('m2dShow'); return !!(e && e.classList.contains('on')); }
  /* 남은 초 — 장면 한 바퀴 8초 중 녹색 0~4초(40초 → 0 · 그림 예시) */
  var T0 = Date.now(), TK = null;
  function tick() { var t = ((Date.now() - T0) / 1000) % 8, gl = document.querySelector('#m2dShow [data-sg]'), an = gl && gl.getAnimations ? gl.getAnimations()[0] : null;
    if (an && an.currentTime != null) t = (an.currentTime / 1000) % 8;   /* 등 색과 같은 시계(CSS 애니메이션)를 읽는다 — 따로 세면 녹색 등에 붉은 숫자가 뜬다 */
    var g = t < 3.9, y = !g && t < 4.7, n = g ? Math.ceil((3.9 - t) * 10) : y ? Math.ceil((4.7 - t) * 4) : Math.ceil((8 - t) * 10);
    document.querySelectorAll('#m2dShow [data-cd="sig"]').forEach(function (x) { x.textContent = n; x.style.fill = g ? '#16a34a' : y ? '#ca8a04' : '#dc2626'; }); }
  function open() { var e = el(); e.classList.add('on'); e.classList.remove('paused'); T0 = Date.now(); tick(); if (!RM && !TK) TK = setInterval(tick, 250);
    try { if (!(history.state || {}).m2dw) history.pushState({ m2dw: 1 }, '', location.href); } catch (er) {} }
  function close(fromPop) { var e = document.getElementById('m2dShow'); if (!e || !e.classList.contains('on')) return; e.classList.remove('on'); e.classList.add('paused'); if (TK) { clearInterval(TK); TK = null; }
    if (!fromPop) { try { if ((history.state || {}).m2dw) history.back(); } catch (er) {} } }
  window.addEventListener('popstate', function () { if (isOn()) close(true); });
  document.addEventListener('visibilitychange', function () { var e = document.getElementById('m2dShow'); if (e) e.classList.toggle('paused', document.hidden || !isOn()); });

  /* 설정 판에 칸 끼우기 — 작은 움직이는 그림(신호 셋) + 한 줄 */
  var MINI = '<svg viewBox="0 0 92 46" aria-hidden="true" class="an"><rect x="6" y="8" width="16" height="30" rx="4" fill="#111827"/>' +
    '<circle cx="14" cy="15" r="4" fill="#22c55e" style="animation:sgG 8s steps(1) infinite"/><circle cx="14" cy="23" r="4" fill="#facc15" style="animation:sgY 8s steps(1) infinite"/><circle cx="14" cy="31" r="4" fill="#ef4444" style="animation:sgR 8s steps(1) infinite"/>' +
    '<path d="M30 34 C 45 30, 55 14, 86 12" stroke="#fff" stroke-width="5" fill="none" opacity=".35"/><circle cx="60" cy="24" r="5" fill="#fff" style="animation:blink 1.6s infinite"/></svg>';
  function inject() { var s = document.getElementById('m2dSet'); if (!s || s.querySelector('.shw')) return; var sd = s.querySelector('.sd'); if (!sd) return;
    css();
    var b = document.createElement('button'); b.className = 'shw'; b.type = 'button'; b.innerHTML = MINI + '<span><b>🎬 그림으로 보기 — 이 지도로 할 수 있는 것</b><small>신호 남은 초 · 막힘 · 시뮬 · 엮임 · 동네 · 거래 · 단속 자리 · 큰비 · 신고 차량 · 길 안내 · 지역 받기</small></span>';
    b.addEventListener('click', function (ev) { ev.stopPropagation(); open(); });
    sd.parentNode.insertBefore(b, sd.nextSibling); }
  function watch() { var s = document.getElementById('m2dSet'); if (!s) { setTimeout(watch, 800); return; } inject();
    if (window.MutationObserver) new MutationObserver(function () { inject(); s.classList.toggle('paused', !s.classList.contains('on')); }).observe(s, { childList: true, attributes: true, attributeFilter: ['class'] }); }
  /* 설정 판은 처음 열 때 만들어진다 — 몸에 붙는 것을 지켜보다가 붙으면 그 판을 지켜본다 */
  function boot() { if (document.getElementById('m2dSet')) { watch(); return; }
    if (!window.MutationObserver) { setTimeout(boot, 1000); return; }
    var mo = new MutationObserver(function () { if (document.getElementById('m2dSet')) { mo.disconnect(); watch(); } }); mo.observe(document.body, { childList: true }); }
  window.tgShow = { open: open, close: close, scenes: SC.map(function (s) { return s[0]; }) };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  if (/[#&]show=1/.test(location.hash)) setTimeout(open, 600);
})();
