/* 데이터 압축지도 — 🎬 그림으로 보는 「이 지도로 할 수 있는 것」(2026-11-22 · 소유자 「설정 칸에 할 수 있는 것을 이미지와 모션으로 — 모르는 사람은 아예 모른다 · 어떻게 쓰는지 시각적으로」 · 움직이는 그림으로 고름)
   ⚙ 설정 판(#m2dSet · map2d.js setPaint) 맨 위에 「🎬 그림으로 보기」 칸을 끼운다 — map2d.js 는 고치지 않는다(판을 다시 그릴 때마다 MutationObserver 로 다시 끼움)
   장면마다 = 무엇을 하나 한 줄 · 움직이는 그림(SVG + CSS) · 어디서 여나(메뉴 길)
   그림 속 숫자·이름은 모두 「그림 예시」다 — 실제 자료를 읽지 않는다(통신 0 · 저장 0) · 움직임 줄이기를 켠 기기는 멈춘 그림 · 판이 닫혀 있으면 초 세기 멈춤
   열기: 설정 판 칸 · 주소 #show=1 · window.tgShow.open()
   v2(같은 날 · 소유자 「더 구체적으로 모든 항목을 · 빠진 부분을 찾아서 꼭」) = 장면 60 — 홈·경찰 전용 · 기본 조작(위 단추) · 누르면 나오는 카드 · 도구 전부 · 레이어 묶음 13 · 숨은 기능 · 설정 칸
     장면마다 단계 ①②③(누르면 그 때로 멈춤 · ▶ 다시) · 「▶ 실제로 열어 보기」(map2d.js 의 단추를 그대로 누름) · 찾기 칸 · 화면 밖 장면은 멈춤(폰 부담)
     ⚠ 메뉴를 더하거나 이름을 바꾸면 여기 장면(cov)도 같이 — pagecheck.py 의 show_cover 가 도구·상황·근무별 묶음·레이어 판 중분류·경찰 전용·설정 칸·위 단추를 맞대 빠진 것을 실패로 낸다 */
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
    '#m2dSet.paused .shw *{animation-play-state:paused!important}',
    '@media (prefers-reduced-motion: reduce){#m2dSet .shw *{animation-play-state:paused!important}}',
    '#m2dShow .wh small{font-size:12px;font-weight:700;color:var(--ink2,#4b5563)}',
    '#m2dShow .wf small{opacity:.75;font-weight:600}',
    '#m2dShow .wq{width:100%;box-sizing:border-box;margin:4px 0 2px;border:1px solid var(--line,#e2e7ee);border-radius:12px;padding:10px 12px;font-size:15px;background:transparent;color:inherit}',
    '#m2dShow .wn0{display:none;text-align:center;color:var(--ink2,#4b5563);padding:24px 0}',
    '#m2dShow .stp{display:flex;flex-wrap:wrap;gap:4px;padding:9px 12px 4px}',
    '#m2dShow .stp button{flex:1 1 100%;display:flex;align-items:center;gap:6px;text-align:left;border:2px solid transparent;border-radius:10px;padding:6px 7px;font-size:12.5px;line-height:1.35;background:rgba(29,78,216,0);color:inherit;cursor:pointer;min-height:38px;animation-timing-function:steps(1)!important}',
    '#m2dShow .stp button i{flex:none;font-style:normal;font-weight:800;width:20px;height:20px;border-radius:10px;background:#1d4ed8;color:#fff;display:inline-flex;align-items:center;justify-content:center;font-size:12px}',
    '#m2dShow .stp button.on{border-color:#1d4ed8!important;background:rgba(29,78,216,.16)!important}',
    '#m2dShow .stp .pl{justify-content:center;font-size:13px;font-weight:700;border:1px solid var(--line,#e2e7ee)}',
    '#m2dShow .sc .go{display:block;margin-top:8px;border:0;border-radius:12px;background:#1d4ed8;color:#fff;font-weight:800;font-size:14px;padding:10px 12px;min-height:44px;width:100%;cursor:pointer}',
    'html.dark #m2dShow .sc .go{background:#2f5fe0}',
    '#m2dShow .wqs{margin:8px 0 6px;padding:10px 12px;border-radius:14px;background:rgba(29,78,216,.07);border:1px solid rgba(29,78,216,.18)}',
    '#m2dShow .wqs>b{font-size:16px}',
    '#m2dShow .wqs small{color:var(--ink2,#4a5568)}',
    '#m2dShow .wqs div{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}',
    '#m2dShow .wqs button,#m2dUse .tq button{border:1px solid rgba(29,78,216,.35);background:var(--panel,#fff);color:inherit;border-radius:18px;padding:8px 12px;font-size:14px;font-weight:700;cursor:pointer;min-height:40px}',
    '#m2dShow .wqs button.on{background:#1d4ed8;border-color:#1d4ed8;color:#fff}',
    '#m2dShow .wqp{margin:8px 0 0;font-size:14px}',
    '#m2dShow .wqp:empty{display:none}',
    '#m2dShow .qn{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:12px;background:#1d4ed8;color:#fff;font-size:13px;margin-right:6px;vertical-align:2px}',
    '#m2dShow .sc.hit{box-shadow:0 0 0 3px #1d4ed8;transition:box-shadow .2s}',
    '#m2dUse{position:fixed;left:8px;right:8px;bottom:calc(10px + env(safe-area-inset-bottom));z-index:2780;max-width:440px;margin:0 auto;background:var(--panel,#fff);color:var(--ink,#111827);border:1px solid var(--line,#e2e7ee);border-radius:18px;box-shadow:0 10px 30px rgba(0,0,0,.25);padding:10px 12px 8px;max-height:78vh;overflow-y:auto;animation:tipIn .2s ease-out}',
    '#m2dUse.out{opacity:0;transform:translateY(12px);transition:opacity .25s,transform .25s}',
    '@keyframes tipIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}',
    '@media (prefers-reduced-motion:reduce){#m2dUse{animation:none}#m2dUse.out{transition:none}}',
    '#m2dUse .th{display:flex;justify-content:space-between;align-items:center}',
    '#m2dUse .th b{font-size:15px}',
    '#m2dUse .th button{border:0;background:transparent;color:inherit;font-size:18px;min-width:44px;min-height:40px;cursor:pointer}',
    '#m2dUse h5{margin:2px 0 6px;font-size:16px}',
    '#m2dUse svg{display:block;width:100%;height:auto;max-height:24vh;border-radius:12px;background:#eef2f7}',
    'html.dark #m2dUse svg{background:#0f1a2c}',
    '#m2dUse .tst{display:flex;flex-direction:column;gap:2px;margin:5px 0;font-size:14px}',
    '#m2dUse .tst i{display:inline-flex;width:20px;height:20px;border-radius:10px;background:#1d4ed8;color:#fff;font-style:normal;font-size:12px;align-items:center;justify-content:center;margin-right:6px}',
    '#m2dUse .tb{display:flex;gap:8px;margin:4px 0 8px}',
    '#m2dUse .tb button{flex:1;min-height:44px;border-radius:12px;border:0;font-size:15px;font-weight:800;cursor:pointer;background:#1d4ed8;color:#fff}',
    '#m2dUse .tb button+button{background:transparent;color:inherit;border:1px solid var(--line,#e2e7ee)}',
    '#m2dUse .tq>b{font-size:14px}',
    '#m2dUse .tq div{display:flex;flex-wrap:nowrap;overflow-x:auto;gap:6px;margin-top:6px;padding-bottom:4px;scrollbar-width:none}', '#m2dUse .tq button{flex:none}',
    '#m2dUse .toff{display:flex;align-items:center;gap:6px;min-height:36px;margin-top:2px;font-size:13px;color:var(--ink2,#4a5568)}'
  ].join('\n');
  CSS += '\n' + CSS.split('\n').filter(function (r) { return /^(html\.dark )?#m2dShow \./.test(r) && !/\.(wqs|wf|wq|wg|wh|wd|wn0|stp|wy|go|qn|hit|sc)\b/.test(r); }).map(function (r) { return r.split('#m2dShow ').join('#m2dUse '); }).join('\n');   /* 장면 그림 규칙을 오늘의 사용법 카드에도 */

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

  /* ---------- v2(2026-11-22 둘째 · 소유자 「더 구체적으로 모든 항목을 이렇게도 해낼 수 있다는 것을 자세히 · 빠진 부분이 있는지 찾아서 꼭 사용설명을」) ----------
     장면 = { k 키, c 갈래, cov 덮는 메뉴, t 제목, d 하는 일, st 단계 셋, w 단계가 바뀌는 때(%), wy 어디서, go 실제로 열기, a 그림 글, g 그림 }
     cov 는 관문(tools/check/pagecheck.py show_cover)이 지도의 실제 메뉴(도구·상황·빠른 묶음·레이어 주제·경찰 전용·설정 칸·위 단추)와 맞댄다 — 메뉴가 늘었는데 장면이 없으면 커밋 전에 걸린다 */
  function K(n, b) { if (!PK[n]) PK[n] = '@keyframes ' + n + '{' + b + '}'; return n; }
  function wv(a, b) { a = Math.round(a); b = Math.round(b); return K('wv' + a + '_' + b, (a > 0 ? '0%,' + (a - 1) + '%{opacity:0}' : '') + a + '%,' + b + '%{opacity:1}' + (b < 100 ? (b + 1) + '%,100%{opacity:0}' : '')); }
  function tp(x, y, d, r) { d = Math.round(d); var n = K('tp' + d, '0%,' + d + '%{opacity:0;transform:scale(.4)}' + (d + 3) + '%{opacity:1;transform:scale(1)}' + (d + 12) + '%,100%{opacity:0;transform:scale(1.8)}');
    return '<circle class="tpr" cx="' + x + '" cy="' + y + '" r="' + (r || 12) + '" fill="none" stroke="#1d4ed8" stroke-width="3" style="animation-name:' + n + '"/>'; }
  function gb(d) { d = Math.round(d); return K('gb' + d, '0%,' + d + '%{transform:scaleX(0)}' + Math.min(99, d + 10) + '%,100%{transform:scaleX(1)}'); }
  function hs(a, b) { a = Math.round(a); b = Math.round(b); var on = '{background-color:rgba(29,78,216,.16);border-color:#1d4ed8}', of = '{background-color:rgba(29,78,216,0);border-color:transparent}';
    return K('hs' + a + '_' + b, (a > 0 ? '0%,' + (a - 1) + '%' + of : '') + a + '%,' + (b - 1) + '%' + on + (b < 100 ? b + '%,100%' + of : '')); }
  function tx(x, y, s, o) { o = o || {}; return '<text class="' + (o.c || 't') + '" x="' + x + '" y="' + y + '"' + (o.a ? ' text-anchor="' + o.a + '"' : '') + (o.st ? ' style="' + o.st + '"' : '') + '>' + s + '</text>'; }
  function box(x, y, w, h, r) { return '<rect class="wn" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (r == null ? 9 : r) + '"/>'; }
  function btnH(x, y, w, s) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="24" rx="12" fill="#1d4ed8"/>' + tx(x + w / 2, y + 16, s, { a: 'middle', st: 'fill:#fff' }); }
  function btnL(x, y, w, s) { return box(x, y, w, 24, 12) + tx(x + w / 2, y + 16, s, { a: 'middle' }); }
  function bgMap() { return '<rect class="bk" x="0" y="0" width="300" height="170"/><rect class="rd" x="0" y="104" width="300" height="10"/><rect class="rd" x="118" y="0" width="10" height="170"/>' +
    '<path d="M14 40 L108 32 L112 98 L20 96 Z M136 36 L286 44 L282 98 L138 96 Z M14 122 L108 120 L110 164 L16 164 Z M136 122 L284 120 L286 164 L138 164 Z" fill="none" stroke="#94a3b8" stroke-width="1.2" stroke-dasharray="4 3"/>'; }
  function list(x, y, w, items, pick) { var s = box(x, y, w, 10 + items.length * 22);
    items.forEach(function (it, i) { var yy = y + 5 + i * 22; if (i === pick) s += '<rect x="' + (x + 4) + '" y="' + yy + '" width="' + (w - 8) + '" height="20" rx="6" fill="rgba(29,78,216,.18)"/>'; s += tx(x + 10, yy + 14, it); }); return s; }
  function bars(x, y, w, rows, d) { return rows.map(function (r, i) { var yy = y + i * 19; return tx(x, yy + 10, r[0], { c: 'ex', a: 'start' }) + '<rect x="' + (x + 74) + '" y="' + yy + '" width="' + Math.round((w - 76) * r[1]) + '" height="11" rx="5" fill="' + r[2] + '" style="animation-name:' + gb(d + i * 4) + ';transform-origin:left"/>'; }).join(''); }
  function pop(inner, d) { return '<g style="animation-name:' + pk(d) + '">' + inner + '</g>'; }
  function res(t, inner) { return box(8, 36, 284, 128, 12) + tx(20, 56, t) + inner + ex(284, 158); }
  /* 세 장 — 장마다 보이는 때가 따로(w = 바뀌는 때 %) · 바탕(bg)은 늘 보임 */
  function stg(bg, a, b, c, w) { w = w || [0, 33, 66]; return bg + '<g style="animation-name:' + wv(w[0], w[1] + 1) + '">' + a + '</g><g style="animation-name:' + wv(w[1], w[2] + 1) + '">' + b + '</g><g style="animation-name:' + wv(w[2], 100) + '">' + c + '</g>'; }
  /* 단추 누르기 → 목록에서 고르기 → 결과 카드 */
  function flow(o) { var bx = o.bx == null ? 210 : o.bx, bw = o.bw || 82, pw = o.pw || 168, px = 300 - pw - 8, py = 38;
    return stg((o.bg || bgMap()) + btnH(bx, 6, bw, o.btn), tp(bx + bw / 2, 18, 6, 14),
      list(px, py, pw, o.list, o.pick) + tp(px + pw / 2, py + 15 + o.pick * 22, 45, 11), o.res, [0, 30, 64]); }
  var W3 = [0, 30, 64];
  /* 레이어 주제 — 🗂 → 주제 고르기 → 그 주제 층이 지도에 뜸 */
  function lay(chip, nm, sm, ic, line) { var P = [[60, 66], [196, 62], [62, 146], [214, 144], [168, 78], [86, 132]];
    var fin = bgMap() + ic.map(function (c, i) { var p = P[i % P.length]; return pop('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="15" fill="rgba(29,78,216,.14)" stroke="#1d4ed8" stroke-width="1.5"/><text x="' + p[0] + '" y="' + (p[1] + 6) + '" text-anchor="middle" style="font:16px system-ui">' + c + '</text>', 66 + i * 6); }).join('') + box(8, 8, 284, 26, 9) + tx(150, 26, line, { a: 'middle' }) + ex(296, 166);
    if (!chip) return flow({ btn: '🗂 레이어', list: [nm].concat(sm.slice(0, 4)), pick: 0, res: fin });
    return stg(bgMap() + box(4, 4, 292, 28, 9) + btnL(10, 6, 86, chip) + tx(108, 23, '다른 칩 …', { c: 'ex', a: 'start' }), tp(53, 18, 5, 14),
      btnH(10, 6, 86, chip) + list(8, 40, 200, sm.slice(0, 4), -1) + tx(214, 60, '이 묶음의', { c: 'ex', a: 'start' }) + tx(214, 76, '기본 레이어', { c: 'ex', a: 'start' }), fin, W3); }

  var NEW = [
    /* ── 🌟 기본 조작 */
    { k: 'move', c: 'b', cov: 'top:m2dRegB top:m2dFindB top:m2dHereB top:m2dIn', t: '🧭 원하는 자리로 가기',
      d: '맨 위 「📍 지역」으로 시도·시군구·동을 고르거나, 🔍 로 교차로·역·길·정류장 이름을 찾는다. 오른쪽 📍 는 지금 내 위치, ＋ － 는 크게·작게.',
      st: ['📍 지역 → 시도·구·동 고르기', '🔍 이름으로 찾기', '그 자리로 옮김 · ＋－ 확대'], wy: '맨 위 <b>📍 지역</b> · <b>🔍</b> · 오른쪽 <b>📍</b>', go: 'btn:m2dRegB', a: '지역을 고르고 이름을 찾으면 지도가 그 자리로 옮겨 감',
      g: stg(bgMap() + box(4, 4, 292, 26, 9) + tx(16, 22, '📍 지역') + tx(96, 22, '🔍') + tx(270, 22, '📍'),
        tp(36, 17, 4, 14) + list(8, 36, 150, ['서울특별시', '서초구', '○○동'], 2),
        box(60, 36, 220, 26, 9) + tx(72, 54, '🔍 ○○사거리') + tp(96, 17, 36, 12) + list(60, 66, 220, ['○○사거리 · 교차로', '○○사거리역 · 지하철'], 0) + tp(170, 82, 52, 11),
        '<circle cx="123" cy="109" r="8" fill="#dc2626"/><circle cx="123" cy="109" r="4" fill="none" stroke="#dc2626" stroke-width="3" style="animation-name:ring;animation-duration:2s"/>' + pop(box(134, 66, 120, 26, 9) + tx(144, 84, '여기로 옮김'), 70) + btnL(262, 122, 30, '＋') + btnL(262, 148, 30, '－') + ex(250, 166)) },
    { k: 'layer', c: 'b', cov: 'top:m2dFold top:m2dChipT', t: '🗂 레이어 켜고 끄기',
      d: '「🗂 레이어」를 열어 보고 싶은 층을 켠다. 층은 큰 묶음(👥 인구·생활 · 🚓 경찰업무 · 💳 상권·부동산 · ⛅ 날씨·실시간 · 🗺 바탕) 안에 나뉘어 있고, 이름 옆 ❓ 는 그 층이 무엇을 보여 주는지·출처·한계, ☆ 는 즐겨찾기다. 맨 위 칩(👥 인구 · 🚦 교통 …)은 「접기 ▴」로 접는다.',
      st: ['🗂 레이어 누르기', '층 이름 눌러 켜기', '지도에 뜸 · ❓ 로 뜻 보기'], w: W3, wy: '맨 위 <b>🗂</b>', go: 'btn:m2dFold', a: '레이어 판에서 층을 켜면 지도에 점이 뜨고 물음표로 뜻을 봄',
      g: flow({ btn: '🗂 레이어', list: ['☐ 🏪 상권분석  ❓ ☆', '☑ 🚗 교차로 사고  ❓ ☆', '☐ 🚦 신호  ❓ ☆'], pick: 1, pw: 176,
        res: bgMap() + [[40, 60], [150, 108], [200, 70], [90, 140], [240, 132]].map(function (p, i) { return pop('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6" fill="#dc2626"/>', 66 + i * 4); }).join('') +
          pop(box(130, 8, 162, 46, 9) + tx(140, 26, '❓ 무엇을 보여 주나') + tx(140, 44, '출처 · 기준일 · 한계', { c: 'ex', a: 'start' }), 86) + ex(296, 166) }) },
    { k: 'time', c: 'b', cov: 'top:m2dTimeB', t: '📅 다른 날·시각으로 보기',
      d: '위 「📅 오늘 · 지금」을 누르면 다른 날·시각을 고른다. 그때의 신호·인파·흐름으로 바뀌고, 지금이 아니면 단추가 붉은 바탕이 된다. 「지금」으로 돌아온다.',
      st: ['📅 오늘 · 지금 누르기', '날짜 · ◀ ▶ 한 시간씩', '그 시각 모습 · 단추가 붉게'], wy: '맨 위 <b>📅 오늘 · 지금</b>', go: 'btn:m2dTimeB', a: '날짜 시각을 바꾸면 길 색이 바뀌고 단추가 붉어짐',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/><path d="M10 140 C 80 120, 120 60, 290 40" class="rdl" stroke-width="14" fill="none"/>',
        btnL(8, 6, 120, '📅 오늘 · 지금') + tp(68, 18, 4, 14) + '<path d="M10 140 C 80 120, 120 60, 290 40" stroke="#16a34a" stroke-width="8" fill="none" stroke-linecap="round"/>',
        box(8, 36, 200, 30, 9) + tx(22, 56, '◀') + tx(108, 56, '11/23(월) 08시', { a: 'middle' }) + tx(192, 56, '▶', { a: 'end' }) + tp(186, 51, 40, 11) + tp(186, 51, 52, 11) + '<path d="M10 140 C 80 120, 120 60, 290 40" stroke="#16a34a" stroke-width="8" fill="none" stroke-linecap="round"/>',
        '<rect x="8" y="6" width="140" height="24" rx="12" fill="#dc2626"/>' + tx(78, 22, '📅 11/23 08시', { a: 'middle', st: 'fill:#fff' }) + '<path d="M10 140 C 80 120, 120 60, 290 40" stroke="#dc2626" stroke-width="8" fill="none" stroke-linecap="round"/>' + pop(box(150, 96, 140, 44, 9) + tx(160, 114, '그 시각 신호·흐름') + tx(160, 132, '지금이 아니면 붉은 단추', { c: 'ex', a: 'start' }), 70) + ex(296, 166)) },
    { k: 'chips', c: 'b', cov: 'chip:basic chip:traffic chip:fac chip:night chip:shop chip:acc10 chip:crowd chip:jur chip:kids chip:gov chip:acc chip:estate chip:rain', t: '⚡ 근무별 한 번에',
      d: '레이어 판 맨 위 「⚡ 근무별 한 번에」에서 묶음을 누르면 그 일에 볼 층이 한 번에 켜진다 — 지역 기본 파악 · 교통근무 · 교통시설 · 야간순찰 · 상권분석 · 사고 10년 · 행사·인파 · 관할·관서 · 어린이 · 관공서 · 사고·응급 · 부동산·상권 · 큰비.',
      st: ['🗂 → ⚡ 근무별 한 번에 펼치기', '묶음 하나 누르기(예: 🌙 야간순찰)', '그 근무에 볼 층만 켜짐'], w: W3, wy: '🗂 → <b>⚡ 근무별 한 번에</b> · 「📋 묶음마다 켜는 레이어」에 짜임', go: 'btn:m2dFold', a: '묶음 하나를 누르면 여러 층이 한 번에 켜짐',
      g: flow({ btn: '🗂 레이어', list: ['🔎 지역 기본 파악', '🚦 교통근무', '🌙 야간순찰', '🚗 사고 10년', '🌧 큰비'], pick: 2,
        res: bgMap() + ['🏪', '🍺', '🎤', '🏨', '🏥', '👮'].map(function (c, i) { var p = [[50, 60], [90, 76], [170, 64], [230, 80], [70, 140], [220, 142]][i]; return pop('<text x="' + p[0] + '" y="' + p[1] + '" text-anchor="middle" style="font:18px system-ui">' + c + '</text>', 66 + i * 4); }).join('') + box(8, 8, 284, 26, 9) + tx(150, 26, '🌙 야간순찰 — 층 10개 켜짐', { a: 'middle' }) + ex(296, 166) }) },
    { k: 'dark', c: 'b', cov: 'top:m2dDN top:m2dFsB tool:fs', t: '🌓 밤 화면 · ⛶ 넓게 보기',
      d: '🌓 로 낮·밤 화면을 바꾼다(설정에서 「자동」도 고른다). 🧰 도구의 ⛶ 전체화면은 주소 줄을 가려 지도를 넓게 쓴다.',
      st: ['🌓 누르기', '밤 화면 — 눈부심 줄이기', '⛶ 전체화면'], wy: '맨 위 <b>🌓</b> · 🧰 도구 → <b>⛶ 전체화면</b>', go: 'btn:m2dDN', a: '낮 화면이 밤 화면으로 바뀌고 전체화면으로 넓어짐',
      g: stg(bgMap(), btnH(240, 6, 52, '🌓') + tp(266, 18, 4, 14),
        '<rect x="0" y="0" width="300" height="170" fill="#0b1220"/><rect x="0" y="104" width="300" height="10" fill="#33435e"/><rect x="118" y="0" width="10" height="170" fill="#33435e"/>' + tx(150, 60, '🌙 밤 화면', { a: 'middle', st: 'fill:#e5ebf3' }),
        '<rect x="0" y="0" width="300" height="170" fill="#0b1220"/><rect x="0" y="104" width="300" height="10" fill="#33435e"/><rect x="118" y="0" width="10" height="170" fill="#33435e"/>' +
          pop('<path d="M20 40 L20 20 L40 20 M260 20 L280 20 L280 40 M280 130 L280 150 L260 150 M40 150 L20 150 L20 130" stroke="#8fb3ff" stroke-width="4" fill="none"/>', 70) + tx(150, 92, '⛶ 주소 줄 없이 넓게', { a: 'middle', st: 'fill:#e5ebf3' })) },
    { k: 'leg', c: 'b', cov: 'top:m2dLegB top:m2dFit tool:leg tool:fit', t: '📖 범례 · 🗺 전체 보기',
      d: '「범례」는 지금 켠 층의 색과 표시가 무엇을 뜻하는지 보여 준다. 「전체」는 구 전체를 한 화면에 넣고, 다시 누르면 교차로 구역(격자) 보기로 돌아온다.',
      st: ['오른쪽 범례 누르기', '색 · 표시 뜻 읽기', '전체 ↔ 격자 보기'], wy: '오른쪽 <b>범례</b> · <b>전체</b> · 🧰 도구', go: 'btn:m2dLegB', a: '범례 판에 색의 뜻이 나오고 전체 보기로 구 전체가 보임',
      g: stg(bgMap(), btnH(226, 120, 66, '범례') + tp(259, 132, 4, 14),
        box(120, 20, 172, 96, 10) + [['#16a34a', '시속 30km 넘음'], ['#f59e0b', '10~30km'], ['#dc2626', '10km 아래']].map(function (r, i) { return '<rect x="132" y="' + (34 + i * 26) + '" width="22" height="10" rx="4" fill="' + r[0] + '"/>' + tx(162, 44 + i * 26, r[1]); }).join(''),
        '<rect class="bk" x="0" y="0" width="300" height="170"/>' + pop('<path d="M40 30 L120 20 L170 40 L250 30 L270 90 L240 150 L140 156 L60 140 L30 90 Z" fill="rgba(29,78,216,.10)" stroke="#1d4ed8" stroke-width="2"/>', 66) + tx(150, 94, '구 전체를 한 화면에', { a: 'middle' }) + btnH(226, 6, 66, '전체') + ex(296, 166)) },
    { k: 'guide', c: 'b', cov: 'top:m2dGuideB tool:guide set:정보', t: '📖 사용설명서 — 글로 읽기',
      d: '레이어마다 무엇을 알 수 있나, 생활 장면별(이사·학교·밤길·큰비…) 어디를 누르나, 자료 출처와 한계를 글로 읽는다. 설정 맨 아래 「정보」에 지도 판 번호와 함께 있다.',
      st: ['맨 위 📖 누르기', '알고 싶은 장면 고르기', '어디를 누르나 · 출처 · 한계'], w: W3, wy: '맨 위 <b>📖</b> · 🧰 도구 → <b>📖 사용설명서</b> · 설정 → 정보', go: 'btn:m2dGuideB', a: '사용설명서가 열리고 장면별 쓰는 법이 나옴',
      g: flow({ btn: '📖', bx: 240, bw: 52, list: ['🏡 이사할 집을 고를 때', '🎒 아이 학교·학원', '🌙 밤길이 걱정될 때'], pick: 2,
        res: res('🌙 밤길이 걱정될 때', '<rect x="20" y="66" width="250" height="8" rx="4" fill="#cbd5e1"/><rect x="20" y="82" width="220" height="8" rx="4" fill="#cbd5e1"/>' + tx(20, 112, '어디서: 🗂 → 🛡 생활안전', { c: 'ex', a: 'start' }) + tx(20, 132, '출처 · 기준일 · 한계', { c: 'ex', a: 'start' })) }) },
    { k: 'first', c: 'b', cov: 'top:m2dHomeB2', t: '🏠 처음 세팅으로 돌아가기',
      d: '위 🏠 단추를 누르면 자리·확대·켠 레이어·시각이 처음 세팅대로 돌아오고 열린 카드·판도 닫힌다. 저장한 보기를 「🏠 처음 보기」로 정해 두면 그 보기로 돌아온다.',
      st: ['이것저것 켜고 옮긴 뒤', '위 🏠 누르기', '처음 세팅 그대로'], wy: '맨 위 <b>🏠</b>', go: 'btn:m2dHomeB2', a: '여러 층과 카드가 열린 지도가 처음 모습으로 돌아감',
      g: stg(bgMap(), [[40, 60], [150, 120], [220, 70], [80, 140], [250, 140], [190, 40]].map(function (p) { return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6" fill="#7c3aed"/>'; }).join('') + box(150, 90, 140, 60, 9) + tx(160, 110, '열린 카드'),
        [[40, 60], [150, 120], [220, 70], [80, 140], [250, 140], [190, 40]].map(function (p) { return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6" fill="#7c3aed"/>'; }).join('') + btnH(8, 6, 44, '🏠') + tp(30, 18, 40, 14),
        btnL(8, 6, 44, '🏠') + pop(box(70, 60, 160, 44, 10) + tx(150, 80, '처음 세팅으로', { a: 'middle' }) + tx(150, 96, '자리 · 레이어 · 시각', { c: 'ex', a: 'middle' }), 68) + ex(296, 166)) },

    /* ── 🏠 홈 */
    { k: 'home', c: 'h', cov: 'top:m2dHomeB home:links', t: '← 홈 목록 — 한곳에 다 있다',
      d: '맨 왼쪽 ← (폰의 뒤로 단추도) 를 누르면 홈 목록이 열린다. 상황 보기·경찰 전용·저장한 보기·자주 쓰는 도구와 T-Book·네비 가르고·게임 바로가기가 한곳에. 「🗺 지도로 돌아가기」는 켠 레이어를 그대로 둔다.',
      st: ['맨 왼쪽 ← 누르기', '상황 · 경찰 전용 · 도구 목록', '고르면 그 화면으로 · 지도는 그대로'], wy: '맨 왼쪽 <b>←</b> · 폰 뒤로 단추', go: 'home', a: '왼쪽 화살표를 누르면 홈 목록이 올라옴',
      g: stg(bgMap(), btnH(8, 6, 40, '←') + tp(28, 18, 4, 14),
        box(8, 8, 284, 154, 12) + tx(20, 30, '🗺 데이터 압축지도') + btnH(20, 40, 260, '🗺 지도로 돌아가기 · 레이어 그대로') + tx(20, 88, '🎯 지금 상황으로 보기') + tx(20, 110, '👮 경찰 전용') + tx(20, 132, '🧰 자주 쓰는 도구') + tx(20, 154, '📕 T-Book · 🧭 가르고 · 🎮 게임', { c: 'ex', a: 'start' }),
        box(8, 8, 284, 154, 12) + tx(20, 30, '🗺 데이터 압축지도') + '<rect x="16" y="76" width="268" height="18" rx="6" fill="rgba(29,78,216,.18)"/>' + tx(20, 88, '🎯 지금 상황으로 보기') + tx(20, 110, '👮 경찰 전용') + tx(20, 132, '🧰 자주 쓰는 도구') + tp(150, 86, 70, 12) + ex(284, 158)) },
    { k: 'sit', c: 'h', cov: 'sit:traffic sit:night sit:crowd sit:rain sit:kids', t: '🎯 지금 상황으로 보기',
      d: '교통근무 · 야간 · 행사·집회 · 큰비 · 학교 둘레 — 그 상황에 볼 층만 한 번에 켠다. 다시 누르면 되돌린다. 레이어 판 맨 위 한 줄에도 같은 묶음이 있다.',
      st: ['← 홈 → 🎯 지금 상황으로 보기', '상황 하나 고르기(예: 🏫 학교 둘레)', '그 상황 층만 켜짐 · 다시 누르면 되돌림'], w: W3, wy: '← 홈 → <b>🎯 지금 상황으로 보기</b>', go: 'home', a: '상황 단추를 누르면 그 상황에 맞는 층만 켜짐',
      g: flow({ btn: '← 홈', bx: 8, bw: 66, list: ['🚦 교통근무', '🌙 야간', '🎪 행사·집회', '🌧 큰비', '🏫 학교 둘레'], pick: 4,
        res: bgMap() + ['🏫', '🚸', '🧒', '📚', '📹'].map(function (c, i) { var p = [[60, 66], [96, 92], [200, 66], [230, 140], [70, 142]][i]; return pop('<text x="' + p[0] + '" y="' + p[1] + '" text-anchor="middle" style="font:18px system-ui">' + c + '</text>', 66 + i * 5); }).join('') + box(8, 8, 284, 26, 9) + tx(150, 26, '🏫 학교 둘레 — 이 상황 층만', { a: 'middle' }) + ex(296, 166) }) },
    { k: 'dui', c: 'h', cov: 'dec:d2', t: '🍺 음주단속 장소 고르기',
      d: '서초 시범. 한 주를 시간대 칸으로 나눠 때를 고르면, 밤(20~6시) 사고로 동·교차로 순위를 세우고 주점 수·심야 결제는 곁들여 보인다. 적발 수는 「단속한 만큼 나온 수」라 경찰서 단위로만 밝힌다. T-Book 음주 단속 절차·서식으로 바로 간다.',
      st: ['홈 → 👮 경찰 전용 → 🍺 음주단속', '한 주 시간대 칸에서 때 고르기', '동 · 교차로 후보와 근거'], wy: '← 홈 → 👮 경찰 전용 → <b>🍺 음주단속 장소 고르기</b>', go: 'dec:d2', a: '한 주 시간대 칸에서 고르면 후보 동과 근거가 나옴',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>',
        tx(12, 22, '한 주 × 시간대') + [0, 1, 2, 3, 4, 5, 6].map(function (r) { return [0, 1, 2, 3, 4, 5].map(function (c) { var v = ((r * 7 + c * 3) % 5) / 5 + (c > 3 ? .3 : 0); return '<rect x="' + (12 + c * 30) + '" y="' + (30 + r * 18) + '" width="27" height="15" rx="3" fill="rgba(220,38,38,' + Math.min(.9, .12 + v * .6).toFixed(2) + ')"/>'; }).join(''); }).join('') + tx(200, 50, '진할수록', { c: 'ex', a: 'start' }) + tx(200, 66, '밤 사고 많음', { c: 'ex', a: 'start' }),
        [0, 1, 2, 3, 4, 5, 6].map(function (r) { return [0, 1, 2, 3, 4, 5].map(function (c) { var v = ((r * 7 + c * 3) % 5) / 5 + (c > 3 ? .3 : 0); return '<rect x="' + (12 + c * 30) + '" y="' + (30 + r * 18) + '" width="27" height="15" rx="3" fill="rgba(220,38,38,' + Math.min(.9, .12 + v * .6).toFixed(2) + ')"/>'; }).join(''); }).join('') + '<rect x="161" y="118" width="31" height="19" rx="4" fill="none" stroke="#1d4ed8" stroke-width="3"/>' + tp(177, 127, 40, 12) + tx(200, 130, '금 0~2시', { a: 'start' }),
        res('금 0~2시 후보', [['① ○○동', '밤 사고 · 주점'], ['② △△동', '호프 심야 결제'], ['③ □□교차로', '밤 사고']].map(function (r, i) { return pop(tx(20, 80 + i * 24, r[0]) + tx(130, 80 + i * 24, r[1], { c: 'ex', a: 'start' }), 66 + i * 6); }).join('') + tx(20, 152, '적발 수 = 단속한 만큼(경찰서 단위)', { c: 'ex', a: 'start' }))) },
    { k: 'rally', c: 'h', cov: 'dec:d3', t: '📢 집회·행사 둘레',
      d: '오늘의 주요 집회(서울경찰청 공개 글)·큰 공연 자리 둘레 교차로를 그 시각대 사고(10년)로 늘어놓고, 길 따라 바로 앞 「상류」 교차로도 함께 보인다 — 상류에서 먼저 끊는다 · 분기점 앞에서.',
      st: ['홈 → 👮 경찰 전용 → 📢 집회·행사', '오늘 집회 · 공연 하나 고르기', '둘레 교차로 · 상류 교차로'], wy: '← 홈 → 👮 경찰 전용 → <b>📢 집회·행사 둘레</b>', go: 'dec:d3', a: '집회 자리 둘레 교차로와 상류 교차로가 표시됨',
      g: stg(bgMap(), list(8, 8, 200, ['📢 ○○ 앞 집회 14시', '🎵 △△홀 공연 19시'], 0) + tp(108, 24, 8, 11),
        '<circle cx="123" cy="109" r="10" fill="#dc2626"/>' + tx(140, 96, '📢 집회 자리') + '<circle cx="123" cy="109" r="10" fill="none" stroke="#dc2626" stroke-width="3" style="animation-name:ring;animation-duration:2.5s"/>',
        '<circle cx="123" cy="109" r="10" fill="#dc2626"/>' + [[123, 60], [180, 109], [60, 109]].map(function (p, i) { return pop('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="8" fill="#f59e0b" stroke="#fff" stroke-width="2"/>', 66 + i * 5); }).join('') +
          pop('<circle cx="268" cy="109" r="9" fill="#1d4ed8" stroke="#fff" stroke-width="2"/><path d="M256 109 L196 109" stroke="#1d4ed8" stroke-width="3" stroke-dasharray="5 4"/>' + box(196, 120, 98, 42, 9) + tx(206, 138, '상류 교차로') + tx(206, 154, '먼저 끊는 자리', { c: 'ex', a: 'start' }), 84) + ex(110, 166)) },
    { k: 'log', c: 'h', cov: 'dec:d5', t: '📒 한 일 기록',
      d: '후보에서 「✋ 여기 섰다」를 누르면 교차로 번호·한 일·까닭만 이 기기에 남는다(좌표·사람·차량번호는 남기지 않는다). 순위가 아닌 곳을 고른 까닭은 현장 판단으로 따로 모이고, 「📋 CSV 복사」로 가져간다.',
      st: ['후보에서 ✋ 여기 섰다', '한 일 · 까닭 적기', '📒 기록에 쌓임 · CSV 복사'], wy: '← 홈 → 👮 경찰 전용 → <b>📒 한 일 기록</b>', go: 'dec:d5', a: '여기 섰다를 누르면 기록이 쌓이고 표로 복사됨',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>', list(8, 10, 284, ['① ○○사거리', '② △△역 앞'], 0) + btnH(196, 14, 90, '✋ 여기 섰다') + tp(241, 26, 8, 13),
        box(8, 10, 284, 96, 10) + tx(20, 32, '① ○○사거리 · 18시') + tx(20, 56, '한 일: 음주 단속', { c: 'ex', a: 'start' }) + tx(20, 78, '까닭: 밤 사고 + 길목', { c: 'ex', a: 'start' }) + '<rect x="20" y="86" width="4" height="12" fill="#1d4ed8" style="animation:blink 1s steps(1) infinite"/>',
        box(8, 10, 284, 150, 10) + tx(20, 32, '📒 기록 3건') + [0, 1, 2].map(function (i) { return pop('<rect x="20" y="' + (44 + i * 26) + '" width="260" height="20" rx="6" fill="rgba(29,78,216,.10)"/>' + tx(28, 58 + i * 26, ['11/20 ○○사거리 · 단속', '11/21 △△역 · 교통', '11/22 ○○사거리 · 단속'][i], { c: 'ex', a: 'start' }), 66 + i * 5); }).join('') + btnH(176, 128, 108, '📋 CSV 복사') + ex(160, 152)) },

    /* ── 🧰 도구 */
    { k: 'live', c: 't', cov: 'tool:live', t: '🏡 여기 살면 얼마',
      d: '문답으로 가진 돈·소득을 넣으면 매매·전세·월세로 각각 얼마까지 되는지, 달마다 내는 금융비용, 금리가 바뀌면 얼마나 달라지는지, 출퇴근·자동차 비용까지 처음/매달/해마다로 견준다. 넣은 값은 저장·전송하지 않는다(참고 어림 · 상담·심사 아님).',
      st: ['🧰 도구 → 🏡 여기 살면 얼마', '문답에 가진 돈 · 소득 넣기', '매매 · 전세 · 월세 견주기'], w: W3, wy: '🧰 도구 → <b>🏡 여기 살면 얼마</b>', go: 'tool:live', a: '문답에 답하면 매매 전세 월세 막대가 나옴',
      g: flow({ btn: '🧰 도구', list: ['🧭 오늘의 결정', '🏡 여기 살면 얼마', '🏷 최근 거래 찾기'], pick: 1,
        res: res('○○동에 산다면', bars(20, 70, 270, [['매매', .5, '#2563eb'], ['전세', .78, '#16a34a'], ['월세', .95, '#f59e0b']], 66) + tx(20, 140, '처음 · 매달 · 해마다 비용', { c: 'ex', a: 'start' })) }) },
    { k: 'pidx', c: 't', cov: 'tool:pidx', t: '📊 경찰서·시도청 지표표',
      d: '사건·사고·범죄를 주민·학생·자동차·주행·넓이·경찰관 수로 나눈 숫자로 견주고 검거율도 본다. 표는 「복사」로 엑셀에 붙인다.',
      st: ['🧰 도구 → 📊 지표표', '잣대 고르기(주민 · 자동차 · 경찰관 …)', '관서끼리 견주기 · 엑셀로 복사'], w: W3, wy: '🧰 도구 → <b>📊 경찰서·시도청 지표표</b> · 홈 자주 쓰는 도구', go: 'tool:pidx', a: '잣대를 고르면 관서별 숫자 표가 나오고 복사 단추가 있음',
      g: flow({ btn: '🧰 도구', list: ['👥 주민 1만 명당', '🚗 자동차 1만 대당', '👮 경찰관 1명당'], pick: 0,
        res: res('주민 1만 명당', tx(20, 78, '관서', { c: 'ex', a: 'start' }) + tx(140, 78, '사고', { c: 'ex', a: 'start' }) + tx(210, 78, '검거율', { c: 'ex', a: 'start' }) +
          [['ㄱ경찰서', '31', '82%'], ['ㄴ경찰서', '24', '77%'], ['ㄷ경찰서', '19', '85%']].map(function (r, i) { return pop(tx(20, 100 + i * 20, r[0]) + tx(140, 100 + i * 20, r[1]) + tx(210, 100 + i * 20, r[2]), 66 + i * 5); }).join('') + btnH(208, 42, 76, '📋 복사')) }) },
    { k: 'orc', c: 't', cov: 'tool:orc', t: '🧩 엮어서 답 찾기',
      d: '질문을 고르면 흩어진 공개 자료를 ① ② ③ 차례로 엮어 답의 재료를 보여 준다. 온톨로지를 몰라도 되고, 판단은 사람이 한다. 적어 둔 것은 「📒 내가 적은 기록」에 모인다.',
      st: ['🧰 도구 → 🧩 엮어서 답 찾기', '질문 하나 고르기', '자료가 차례로 엮여 답의 재료'], w: W3, wy: '🧰 도구 → <b>🧩 엮어서 답 찾기</b> · 홈 자주 쓰는 도구', go: 'tool:orc', a: '질문을 고르면 자료 상자가 화살표로 차례로 이어짐',
      g: flow({ btn: '🧰 도구', list: ['이 교차로는 왜 막히나?', '밤에 어디가 위험한가?', '이 동은 어떤 곳인가?'], pick: 1, pw: 190,
        res: res('밤에 어디가 위험한가?', [['💥 밤 사고', 24], ['🍺 주점', 112], ['👥 밤 인파', 200]].map(function (n, i) { return pop(box(n[1], 80, 76, 30, 8) + tx(n[1] + 38, 100, n[0], { a: 'middle' }) + (i < 2 ? '<path d="M' + (n[1] + 78) + ' 95 L' + (n[1] + 86) + ' 95" stroke="#64748b" stroke-width="3"/>' : ''), 66 + i * 8); }).join('') + tx(20, 134, '→ 답의 재료 · 판단은 사람이', { c: 'ex', a: 'start' })) }) },
    { k: 'mrg', c: 't', cov: 'tool:mrg', t: '🔀 합류부 — 끼어들기가 어디서 나나',
      d: 'IC·연결로가 본선에 붙는 곳에서 차를 한 대씩 움직여 억지 끼어들기·아슬아슬·급제동이 어디서 나는지 보고, 실제 사고 자리와 나란히 본다. 반응 시간 같은 계수 일부는 설계값이다.',
      st: ['🧰 도구 → 🔀 합류부', '합류부 하나 고르기', '끼어드는 자리 · 실제 사고 나란히'], wy: '🧰 도구 → <b>🔀 합류부 — IC·합류 사고 원인 시뮬</b>', go: 'tool:mrg', a: '연결로 차가 본선에 끼어들고 경고가 뜸',
      g: '<rect class="bk" x="0" y="0" width="300" height="170"/><rect class="rd" x="0" y="40" width="300" height="50"/><line x1="0" y1="65" x2="300" y2="65" stroke="#fff" stroke-width="2" stroke-dasharray="10 8"/>' +
        '<path d="M0 160 L150 92 L210 92" class="rdl" stroke-width="18" fill="none"/>' +
        [0, 1, 2].map(function (i) { return '<g style="animation-name:sgCar;animation-timing-function:linear;animation-delay:-' + (i * 2.6) + 's"><rect x="-30" y="' + (i % 2 ? 46 : 70) + '" width="24" height="12" rx="3" fill="' + ['#2563eb', '#0891b2', '#7c3aed'][i] + '"/></g>'; }).join('') +
        '<g style="offset-path:path(\'M0 160 L150 90 L230 74\');animation-name:drive;animation-timing-function:linear"><rect x="-11" y="-6" width="22" height="12" rx="3" fill="#ea580c"/></g>' +
        '<g style="animation-name:' + pk(70) + '"><rect x="170" y="104" width="124" height="44" rx="9" class="wn"/><text class="t" x="180" y="122">⚠ 억지 끼어들기</text><text class="ex" x="180" y="140" text-anchor="start">실제 사고와 나란히</text></g>' +
        '<circle cx="214" cy="86" r="6" fill="#dc2626" stroke="#fff" stroke-width="2"/>' + ex(296, 166) },
    { k: 'pstat', c: 't', cov: 'tool:pstat', t: '👮 경찰 통계 모음',
      d: '경찰관 1명당 주민, 시도청 검거율, 사건 처리 기간, 송치·불송치, 수사관 1인당 사건(보도 자료)을 한곳에서 견준다.',
      st: ['🧰 도구 → 👮 경찰 통계 모음', '보고 싶은 통계 고르기', '시도청끼리 견주기'], w: W3, wy: '🧰 도구 → <b>👮 경찰 통계 모음</b>', go: 'tool:pstat', a: '통계를 고르면 시도청별 막대가 나옴',
      g: flow({ btn: '🧰 도구', list: ['👮 1명당 주민', '✅ 시도청 검거율', '⏱ 사건 처리 기간'], pick: 1,
        res: res('시도청 검거율', bars(20, 70, 270, [['ㄱ청', .84, '#2563eb'], ['ㄴ청', .76, '#2563eb'], ['ㄷ청', .69, '#2563eb'], ['ㄹ청', .8, '#2563eb']], 66)) }) },
    { k: 'rad', c: 't', cov: 'tool:rad', t: '📐 반경 분석 — 이 자리 둘레',
      d: '한 자리를 찍으면 둘레 몇 백 m 안의 사람·가게·사고를 센다. 판에서 바로 「💰 손익 계산」으로 넘어간다.',
      st: ['🧰 도구 → 📐 반경 분석', '지도에 자리 찍기', '원 안의 사람 · 가게 · 사고'], wy: '🧰 도구 → <b>📐 반경 분석</b>', go: 'tool:rad', a: '자리를 찍으면 원이 퍼지고 그 안의 수를 셈',
      g: stg(bgMap(), btnH(210, 6, 82, '🧰 도구') + tp(251, 18, 4, 14) + list(124, 38, 168, ['📐 반경 분석', '🏪 창업 자리 찾기'], 0) + tp(208, 53, 20, 11),
        tp(150, 80, 40, 10) + '<circle cx="150" cy="80" r="5" fill="#1d4ed8"/>',
        '<circle cx="150" cy="80" r="56" fill="rgba(29,78,216,.12)" stroke="#1d4ed8" stroke-width="2" style="animation-name:' + pk(64) + '"/><circle cx="150" cy="80" r="5" fill="#1d4ed8"/>' +
          [[120, 60, '#16a34a'], [176, 70, '#16a34a'], [140, 110, '#dc2626'], [186, 98, '#16a34a'], [118, 92, '#dc2626']].map(function (p, i) { return pop('<circle cx="' + p[0] + '" cy="' + p[1] + '" r="4" fill="' + p[2] + '"/>', 70 + i * 3); }).join('') +
          pop(box(8, 138, 284, 26, 9) + tx(150, 156, '500m 안 👥 1.2만 · 🏪 86 · 💥 14', { a: 'middle' }), 84) + ex(296, 132)) },
    { k: 'biz', c: 't', cov: 'tool:biz card:pnl', t: '🏪 창업 자리 찾기 · 💰 손익 계산',
      d: '업종을 고르면 자리마다 유동인구·경쟁 가게·매출 흐름을 견준다. 「💰 손익 계산」(업종 19가지)에 매출·임대료 같은 숫자를 넣으면 공개 자료(실태조사·국세청·고시 요율)를 바탕으로 손익을 어림하고 표를 엑셀로 가져간다.',
      st: ['🧰 도구 → 🏪 창업 자리 찾기', '업종 고르기(예: ☕ 카페)', '자리 견주기 → 💰 손익 계산'], w: W3, wy: '🧰 도구 → <b>🏪 창업 자리 찾기</b> · 📐 반경 분석 판의 <b>💰 손익 계산</b>', go: 'tool:biz', a: '업종을 고르면 후보 자리마다 유동 경쟁 매출 막대가 나옴',
      g: flow({ btn: '🧰 도구', list: ['☕ 카페', '🍗 치킨', '🥐 빵집'], pick: 0,
        res: res('☕ 카페 — 자리 견주기', ['① ○○역', '② △△길', '③ □□동'].map(function (n, i) { var y = 72 + i * 26; return tx(20, y + 10, n, { c: 'ex', a: 'start' }) + [[.9, .6, .7], [.6, .3, .5], [.5, .8, .4]][i].map(function (v, j) { return '<rect x="' + (84 + j * 66) + '" y="' + y + '" width="' + Math.round(60 * v) + '" height="11" rx="4" fill="' + ['#2563eb', '#dc2626', '#16a34a'][j] + '" style="animation-name:' + gb(66 + i * 4) + ';transform-origin:left"/>'; }).join(''); }).join('') +
          tx(84, 66, '유동', { c: 'ex', a: 'start' }) + tx(150, 66, '경쟁', { c: 'ex', a: 'start' }) + tx(216, 66, '매출', { c: 'ex', a: 'start' }) + btnH(20, 140, 120, '💰 손익 계산')) }) },
    { k: 'gdr', c: 't', cov: 'tool:gdr', t: '🍺 음주운전 — 무엇이 바뀌었나',
      d: '음주운전 경험률(나이대별)·음주 사고의 가해 나이대·시간대 몫·단속이 해마다 어떻게 바뀌었는지 그래프로 견준다. 왜 바뀌었는지는 자료에 없다 — 여러 해 흐름으로 보고 사람이 판단한다.',
      st: ['🧰 도구 → 🍺 음주운전 흐름', '해마다 쌓인 줄 보기', '함께 바뀐 것 견주기'], w: W3, wy: '🧰 도구 → <b>🍺 음주운전 흐름</b>', go: 'tool:gdr', a: '해마다 바뀐 선 그래프가 그려짐',
      g: flow({ btn: '🧰 도구', list: ['🚨 신고 차량 예측', '🍺 음주운전 흐름', '🧾 세금 계산'], pick: 1,
        res: res('해마다 바뀐 것', '<line x1="24" y1="140" x2="280" y2="140" stroke="#94a3b8"/>' +
          '<path d="M24 80 L80 86 L136 98 L192 112 L248 120 L280 126" fill="none" stroke="#dc2626" stroke-width="3" stroke-dasharray="420" style="animation-name:' + K('dr64', '0%,64%{stroke-dashoffset:420}90%,100%{stroke-dashoffset:0}') + '"/>' +
          '<path d="M24 120 L80 112 L136 100 L192 96 L248 84 L280 80" fill="none" stroke="#2563eb" stroke-width="3" stroke-dasharray="420" style="animation-name:dr64"/>' +
          tx(200, 72, '— 음주 사고', { c: 'ex', a: 'start', st: 'fill:#dc2626' }) + tx(200, 92, '— 단속', { c: 'ex', a: 'start', st: 'fill:#2563eb' })) }) },
    { k: 'tax', c: 't', cov: 'tool:tax', t: '🧾 세금 계산',
      d: '집·땅 값을 넣으면 보유세·양도세(취득세 포함)를 어림한다. 참고용이고 신고는 세무서·세무사에게.',
      st: ['🧰 도구 → 🧾 세금 계산', '값 · 보유 기간 넣기', '세금 어림 보기'], w: W3, wy: '🧰 도구 → <b>🧾 세금 계산</b> · 위 빠른 메뉴 <b>🧾 세금</b>', go: 'tool:tax', a: '값을 넣으면 세금 어림 표가 나옴',
      g: flow({ btn: '🧰 도구', list: ['🍺 음주운전 흐름', '🧾 세금 계산', '🧭 네비 가르고'], pick: 1,
        res: res('🧾 세금 어림', [['취득세', '○○○만 원'], ['보유세(해마다)', '○○○만 원'], ['양도세', '○○○만 원']].map(function (r, i) { return pop(tx(20, 84 + i * 24, r[0]) + tx(270, 84 + i * 24, r[1], { a: 'end' }), 66 + i * 6); }).join('') + tx(20, 152, '참고용 — 신고는 세무서·세무사', { c: 'ex', a: 'start' })) }) },
    { k: 'ui', c: 't', cov: 'tool:ui', t: '⚙ 화면 설정 — 메뉴가 자꾸 접히면',
      d: '폰에서 지도를 만질 때 위 빠른 메뉴·레이어 판을 접을지(유동) 그대로 둘지(고정) 고른다. 이 기기에만 남는다. PC 넓은 화면은 메뉴가 한 줄이라 늘 보인다.',
      st: ['🧰 도구 → ⚙ 화면 설정', '빠른 메뉴 · 레이어 판 고르기', '유동(접기) ↔ 고정'], w: W3, wy: '🧰 도구 → <b>⚙ 화면 설정</b> · 설정 → 화면', go: 'tool:ui', a: '유동과 고정 중에 고르는 판',
      g: flow({ btn: '🧰 도구', list: ['📥 지역 받기', '⛶ 전체화면', '⚙ 화면 설정'], pick: 2,
        res: res('⚙ 화면 설정', tx(20, 80, '위 빠른 메뉴', { c: 'ex', a: 'start' }) + btnH(20, 88, 124, '유동 — 접기') + btnL(152, 88, 124, '고정 — 늘') + tx(20, 132, '레이어 판', { c: 'ex', a: 'start' }) + btnL(20, 136, 124, '유동 — 닫기') + btnH(152, 136, 124, '고정 — 열어 둠')) }) },

    /* ── 🗂 레이어 — 맨 위 빠른 칩(QCHIP 8) · 레이어 판 묶음(CATS 중분류 13) */
    { k: 'm_pop', c: 'l', cov: 'mid:pop', t: '👥 인구 구성', d: '어느 동에 누가 사는지(나이·가구·외국인), 낮과 밤에 사람이 얼마나 달라지는지(그 시각 머무는 사람 · 250m 칸). 작은 묶음: 주민·가구 · 그 시각 머무는 사람 · 외국인.', st: ['맨 위 칩 「👥 인구」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 주민·가구 · 그 시각 머무는 사람 · 외국인 더 켜기'], w: W3, wy: '맨 위 칩 <b>👥 인구</b> · 🗂 → 👥 인구·생활 → <b>👥 인구 구성</b>', go: 'qc:people|pop', a: '👥 인구 구성 레이어를 켜면 지도에 표시가 뜸', g: lay('👥 인구', '👥 인구 구성', ['주민·가구', '그 시각 머무는 사람', '외국인'], ['👥', '👶', '👴', '🌏'], '누가 살고 · 언제 붐비나') },
    { k: 'm_move', c: 'l', cov: 'mid:move', t: '🚶 이동·동선', d: '사람이 어디서 타고 내리는지, 어느 역·정류장·길목이 언제 붐비는지 — 지하철·버스·따릉이·걷는 사람·행사. 작은 묶음: 대중교통 · 사람 흐름.', st: ['맨 위 칩 「🚶 이동」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 대중교통 · 사람 흐름 더 켜기'], w: W3, wy: '맨 위 칩 <b>🚶 이동</b> · 🗂 → 👥 인구·생활 → <b>🚶 이동·동선</b>', go: 'qc:people|move', a: '🚶 이동·동선 레이어를 켜면 지도에 표시가 뜸', g: lay('🚶 이동', '🚶 이동·동선', ['대중교통', '사람 흐름'], ['🚇', '🚌', '🚲', '🚶'], '어디서 타고 · 언제 붐비나') },
    { k: 'm_life', c: 'l', cov: 'mid:life', t: '🏥 생활시설', d: '병의원·약국·응급실·AED·관공서·우체국·도서관·공원·화장실·쉼터·주유소·충전소·주차장 — 급할 때 가까운 곳. 작은 묶음: 의료 · 반려동물 · 관공서 · 편의 · 차·연료.', st: ['🗂 레이어 열기', '「👥 인구·생활 → 🏥 생활시설」', '의료· 반려동물· 관공서 켜기'], w: W3, wy: '🗂 → 👥 인구·생활 → <b>🏥 생활시설</b>', go: 'btn:m2dFold', a: '🏥 생활시설 레이어를 켜면 지도에 표시가 뜸', g: lay('', '🏥 생활시설', ['의료', '반려동물', '관공서', '편의'], ['🏥', '💊', '🏛', '🚻'], '급할 때 가까운 곳') },
    { k: 'm_care', c: 'l', cov: 'mid:care', t: '🎒 교육·돌봄', d: '학교·학원·어린이집·유치원·놀이터·보호구역이 어디 몰려 있는지 — 등하교 시간에 볼 곳. 작은 묶음: 학교 · 어린이.', st: ['🗂 레이어 열기', '「👥 인구·생활 → 🎒 교육·돌봄」', '학교· 어린이 켜기'], w: W3, wy: '🗂 → 👥 인구·생활 → <b>🎒 교육·돌봄</b>', go: 'btn:m2dFold', a: '🎒 교육·돌봄 레이어를 켜면 지도에 표시가 뜸', g: lay('', '🎒 교육·돌봄', ['학교', '어린이'], ['🏫', '🧒', '📚', '🚸'], '학교 · 학원 · 보호구역') },
    { k: 'm_traf', c: 'l', cov: 'mid:traf', t: '🚦 교통', d: '사고가 어디서·언제 잦은지(교차로 사고 · 10년 · 사망 · 음주), 신호가 몇 초로 도는지, 단속 카메라·견인·주차 단속 자리. 작은 묶음: 교통사고 · 신호·교차로 · 단속·시설.', st: ['맨 위 칩 「🚦 교통」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 교통사고 · 신호·교차로 · 단속·시설 더 켜기'], w: W3, wy: '맨 위 칩 <b>🚦 교통</b> · 🗂 → 🚓 경찰업무 → <b>🚦 교통</b>', go: 'qc:police|traf', a: '🚦 교통 레이어를 켜면 지도에 표시가 뜸', g: lay('🚦 교통', '🚦 교통', ['교통사고', '신호·교차로', '단속·시설'], ['💥', '🚦', '📷', '🅿'], '사고 · 신호 · 단속 장비') },
    { k: 'm_local', c: 'l', cov: 'mid:local', t: '👮 지역경찰', d: '이 자리가 어느 경찰서·지구대 몫인지, 밤에 주점·노래방·숙박이 몰리는 곳, 행사·인파가 모이는 자리. 작은 묶음: 관할·관서 · 야간 순찰 · 행사·인파.', st: ['맨 위 칩 「👮 지역경찰」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 관할·관서 · 야간 순찰 · 행사·인파 더 켜기'], w: W3, wy: '맨 위 칩 <b>👮 지역경찰</b> · 🗂 → 🚓 경찰업무 → <b>👮 지역경찰</b>', go: 'qc:police|local', a: '👮 지역경찰 레이어를 켜면 지도에 표시가 뜸', g: lay('👮 지역경찰', '👮 지역경찰', ['관할·관서', '야간 순찰', '행사·인파'], ['🚓', '👮', '🍺', '🎪'], '관할 · 밤 순찰 · 인파') },
    { k: 'm_safety', c: 'l', cov: 'mid:safety', t: '🛡 생활안전', d: 'CCTV·안심벨·보안등·안심 서비스 가게, 실종 신고 자리, 어린이·노인이 많은 곳, 큰비·눈 때 먼저 볼 길. 작은 묶음: 안심 귀갓길 · 실종·가출 · 어린이·노인 · 재난·계절.', st: ['맨 위 칩 「🛡 생활안전」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 안심 귀갓길 · 실종·가출 · 어린이·노인 더 켜기'], w: W3, wy: '맨 위 칩 <b>🛡 생활안전</b> · 🗂 → 🚓 경찰업무 → <b>🛡 생활안전</b>', go: 'qc:police|safety', a: '🛡 생활안전 레이어를 켜면 지도에 표시가 뜸', g: lay('🛡 생활안전', '🛡 생활안전', ['안심 귀갓길', '실종·가출', '어린이·노인', '재난·계절'], ['📹', '🔔', '💡', '🧒'], '안심 귀갓길 · 약자 · 재난') },
    { k: 'm_spend', c: 'l', cov: 'mid:spend', t: '💳 소비·상권', d: '어디서 언제 돈을 쓰는지(카드 매출), 상권이 커지는지 줄어드는지, 임대료·가게 구성. 작은 묶음: 카드·매출 · 상권 · 가게.', st: ['맨 위 칩 「💳 상권」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 카드·매출 · 상권 · 가게 더 켜기'], w: W3, wy: '맨 위 칩 <b>💳 상권</b> · 🗂 → 💳 상권·부동산 → <b>💳 소비·상권</b>', go: 'qc:biz|spend', a: '💳 소비·상권 레이어를 켜면 지도에 표시가 뜸', g: lay('💳 상권', '💳 소비·상권', ['카드·매출', '상권', '가게'], ['💳', '🏪', '🍺', '🏦'], '어디서 언제 돈을 쓰나') },
    { k: 'm_estate', c: 'l', cov: 'mid:estate', t: '🏠 주거·부동산', d: '땅값·집값·실거래·전월세·세금 통계 — 그 동네의 형편과 바뀌는 흐름. 작은 묶음: 토지 · 공시지가 · 실거래 · 집값 흐름 · 세금 통계(시군구) · 집·건물.', st: ['맨 위 칩 「🏠 부동산」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 토지 · 공시지가 · 실거래 · 집값 흐름 더 켜기'], w: W3, wy: '맨 위 칩 <b>🏠 부동산</b> · 🗂 → 💳 상권·부동산 → <b>🏠 주거·부동산</b>', go: 'qc:biz|estate', a: '🏠 주거·부동산 레이어를 켜면 지도에 표시가 뜸', g: lay('🏠 부동산', '🏠 주거·부동산', ['토지 · 공시지가', '실거래', '집값 흐름', '세금 통계(시군구)'], ['🏠', '🏢', '🏷', '💰'], '땅값 · 집값 · 실거래') },
    { k: 'm_now', c: 'l', cov: 'mid:now', t: '🌦 지금 날씨', d: '지금 날씨(격자)·비구름 레이더·미세먼지 측정소·특보. 작은 묶음: 날씨.', st: ['맨 위 칩 「🌦 날씨」 누르기', '그 묶음 기본 레이어만 켜짐 · 다시 누르면 꺼짐', '🗂 에서 날씨 더 켜기'], w: W3, wy: '맨 위 칩 <b>🌦 날씨</b> · 🗂 → ⛅ 날씨·실시간 → <b>🌦 지금 날씨</b>', go: 'qc:wx|now', a: '🌦 지금 날씨 레이어를 켜면 지도에 표시가 뜸', g: lay('🌦 날씨', '🌦 지금 날씨', ['날씨'], ['🌦', '🌧', '🟢', '☀️'], '지금 날씨 · 비구름 · 미세먼지') },
    { k: 'm_season', c: 'l', cov: 'mid:season', t: '⛅ 계절 위험', d: '침수 흔적·지하차도·결빙 우려 자리·제설함·무더위·한파 쉼터 — 계절마다 위험한 곳. 작은 묶음: 비·침수 · 눈·결빙 · 더위·추위.', st: ['🗂 레이어 열기', '「⛅ 날씨·실시간 → ⛅ 계절 위험」', '비·침수· 눈·결빙· 더위·추위 켜기'], w: W3, wy: '🗂 → ⛅ 날씨·실시간 → <b>⛅ 계절 위험</b>', go: 'btn:m2dFold', a: '⛅ 계절 위험 레이어를 켜면 지도에 표시가 뜸', g: lay('', '⛅ 계절 위험', ['비·침수', '눈·결빙', '더위·추위'], ['🌊', '🧊', '☀️', '❄️'], '침수 · 결빙 · 쉼터') },
    { k: 'm_live', c: 'l', cov: 'mid:live', t: '📡 실시간 교통', d: '지금 막히는 길, 돌발·공사·통제, 교통 CCTV, 버스·따릉이·주차 현황. 일부는 기기마다 열쇠를 넣거나 「🎟 맛보기」를 켰을 때만 받고, 받은 값은 저장하지 않는다. 작은 묶음: 도로 · 서울시 · 인파.', st: ['🗂 레이어 열기', '「⛅ 날씨·실시간 → 📡 실시간 교통」', '도로· 서울시· 인파 켜기'], w: W3, wy: '🗂 → ⛅ 날씨·실시간 → <b>📡 실시간 교통</b>', go: 'btn:m2dFold', a: '📡 실시간 교통 레이어를 켜면 지도에 표시가 뜸', g: lay('', '📡 실시간 교통', ['도로', '서울시', '인파'], ['🚧', '📹', '🚌', '🅿'], '지금 막힘 · 돌발 · CCTV') },
    { k: 'm_map', c: 'l', cov: 'mid:map', t: '🗺 바탕 지도', d: '행정동·도로·건물, 시군구·관할·지구대·리 경계(나눠 보기), 250m 격자, 위성 배경(🛰 브이월드 · 열쇠 필요), 땅의 역사·이야기. 작은 묶음: 바탕 · 나눠 보기 경계 · 격자 · 역사·이야기.', st: ['🗂 레이어 열기', '「🗺 바탕 → 🗺 바탕 지도」', '바탕· 나눠 보기 경계· 격자 켜기'], w: W3, wy: '🗂 → 🗺 바탕 → <b>🗺 바탕 지도</b>', go: 'btn:m2dFold', a: '🗺 바탕 지도 레이어를 켜면 지도에 표시가 뜸', g: lay('', '🗺 바탕 지도', ['바탕', '나눠 보기 경계', '격자', '역사·이야기'], ['🏘', '🛣', '🏢', '🛰'], '동 · 길 · 경계 · 250m 칸') },

    /* ── 👆 누르면(카드) */
    { k: 'explain', c: 'c', cov: 'card:explain', t: '📝 이 지역 설명 — 숫자를 글로',
      d: '동 카드의 「📝 이 지역 설명」을 누르면 그 동의 숫자(사람·가게·사고·집값…)를 문단 글로 풀어 준다.',
      st: ['지도에서 동 누르기', '카드의 📝 이 지역 설명', '숫자가 글로 풀림'], wy: '동 누르기 → 카드 <b>📝 이 지역 설명</b>', go: 'map', a: '막대 카드가 글 문단으로 바뀜',
      g: stg(bgMap(), tp(64, 66, 4, 14) + box(8, 74, 284, 90, 12) + tx(20, 94, '○○동 한눈에') + bars(20, 104, 270, [['👥 사람', .8, '#2563eb'], ['🏪 가게', .55, '#16a34a']], 8),
        box(8, 74, 284, 90, 12) + tx(20, 94, '○○동 한눈에') + btnH(20, 120, 150, '📝 이 지역 설명') + tp(95, 132, 40, 13),
        box(8, 30, 284, 134, 12) + tx(20, 52, '📝 ○○동은') + [0, 1, 2, 3].map(function (i) { return '<rect x="20" y="' + (64 + i * 20) + '" width="' + [250, 230, 246, 160][i] + '" height="9" rx="4" fill="#94a3b8" style="animation-name:' + gb(66 + i * 6) + ';transform-origin:left"/>'; }).join('') + tx(20, 152, '숫자를 문단 글로', { c: 'ex', a: 'start' })) },
    { k: 'cell', c: 'c', cov: 'card:cell', t: '🔲 이 칸 한눈에 — 250m 칸',
      d: '250m 격자를 켜고 칸을 누르면 걸친 행정동·사람·사고·가게·시설·대중교통·집값을 한 카드에 모아 본다. 전국 어디서나 같은 단위로 견준다.',
      st: ['🗂 → 🗺 바탕 → 격자 켜기', '칸 하나 누르기', '그 칸 한눈에'], wy: '🗂 → 🗺 바탕 → 격자 → 칸 <b>누르기</b>', go: 'btn:m2dFold', a: '격자 칸을 누르면 그 칸 카드가 올라옴',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>' + [1, 2, 3, 4, 5, 6, 7].map(function (i) { return '<line x1="' + i * 37.5 + '" y1="0" x2="' + i * 37.5 + '" y2="170" stroke="#94a3b8" stroke-width="1"/>'; }).join('') + [1, 2, 3, 4].map(function (i) { return '<line x1="0" y1="' + i * 34 + '" x2="300" y2="' + i * 34 + '" stroke="#94a3b8" stroke-width="1"/>'; }).join(''),
        tx(150, 20, '250m 칸', { a: 'middle' }),
        '<rect x="112.5" y="34" width="37.5" height="34" fill="rgba(29,78,216,.25)" stroke="#1d4ed8" stroke-width="2"/>' + tp(131, 51, 40, 13),
        '<rect x="112.5" y="34" width="37.5" height="34" fill="rgba(29,78,216,.25)" stroke="#1d4ed8" stroke-width="2"/>' + box(8, 76, 284, 88, 12) + tx(20, 96, '이 칸 한눈에 · ○○동') + ['👥', '💥', '🏪', '🚇', '🏠'].map(function (c, i) { return pop('<text x="' + (34 + i * 52) + '" y="134" text-anchor="middle" style="font:20px system-ui">' + c + '</text>', 66 + i * 4); }).join('') + ex(284, 158)) },
    { k: 'brief', c: 'c', cov: 'card:brief', t: '📋 이 자리 진단 — 교차로',
      d: '교차로 카드의 「📋 이 자리 진단」은 여섯 구 사고 교차로마다 그 구 안 사고 건수 순위(교통량은 반영 안 됨)·주된 위반·시간대 넷을 보이고, 위반이 T-Book 항목과 이어지면 ⚖ 단추로 그 법령을 연다.',
      st: ['맨 위 🚦 교통 칩 → 교차로 누르기', '카드의 📋 이 자리 진단', '순위 · 위반 · 시간대 · ⚖ T-Book'], wy: '교차로 <b>누르기</b> → 카드 <b>📋 이 자리 진단</b>', go: 'qc:police|traf', a: '교차로를 누르면 순위 위반 시간대가 나오고 법령 단추가 있음',
      g: stg(bgMap(), tp(123, 109, 4, 14) + '<circle cx="123" cy="109" r="7" fill="#f59e0b"/>',
        box(8, 36, 284, 128, 12) + tx(20, 56, '○○사거리') + btnH(20, 66, 150, '📋 이 자리 진단') + tp(95, 78, 40, 13),
        res('📋 ○○사거리 · 구 안 3위', tx(20, 78, '주된 위반: 신호위반', { c: 'ex', a: 'start' }) + bars(20, 88, 200, [['0~6시', .3, '#64748b'], ['6~12시', .55, '#64748b'], ['12~18시', .7, '#64748b']], 66) + btnH(222, 88, 62, '⚖ 법령'))) },
    { k: 'watch', c: 'c', cov: 'card:loopwatch', t: '🔔 고리 지켜보기 — 막힘이 번지면',
      d: '엮임 보기의 막힘 고리 카드에서 「🔔 고리 지켜보기 켜기」를 누르면, 화면이 보일 때 3분마다 지금 속도를 받아 고리 네 변이 막히기 시작하면 위에 한 줄로 알리고 먼저 막힌 변을 적는다. 켠 기기에서만 돈다(예측이 아니라 지금 실측).',
      st: ['🧩 엮임 보기 → 🔁 막힘 고리', '🔔 고리 지켜보기 켜기', '막히기 시작하면 한 줄 알림'], wy: '🧰 도구 → 🧩 엮임 보기 → 고리 → <b>🔔 고리 지켜보기</b>', go: 'tool:lnk', a: '네모 고리의 변이 차례로 빨개지고 알림이 뜸',
      g: '<rect class="bk" x="0" y="0" width="300" height="170"/>' +
        [['M70 40 L230 40', 10], ['M230 40 L230 140', 30], ['M230 140 L70 140', 50], ['M70 140 L70 40', 70]].map(function (e) { return '<path d="' + e[0] + '" class="rdl" stroke-width="12" stroke-linecap="round" fill="none"/><path d="' + e[0] + '" stroke-width="8" stroke-linecap="round" fill="none" style="animation-name:' + K('lw' + e[1], '0%,' + e[1] + '%{stroke:#16a34a}' + (e[1] + 6) + '%,94%{stroke:#dc2626}100%{stroke:#16a34a}') + '"/>'; }).join('') +
        [[70, 40], [230, 40], [230, 140], [70, 140]].map(function (p) { return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="7" fill="#1f2937"/>'; }).join('') +
        '<g style="animation-name:' + pk(34) + '">' + box(86, 66, 128, 48, 9) + tx(96, 86, '🔔 고리 막힘 시작') + tx(96, 104, '먼저 막힌 변: 위', { c: 'ex', a: 'start' }) + '</g>' + ex(296, 166) },
    { k: 'esig', c: 'c', cov: 'card:esig', t: '📶 업종 조기 신호',
      d: '동 카드 접이 「📶 업종 조기 신호」 — 업종마다 개업 흐름·폐업이 개업보다 많음·1년 생존을 따로 표시한다(한 점수로 더하지 않고, 작은 수는 말하지 않는다). 단추를 눌러야 그 시도 자료만 받는다.',
      st: ['지도에서 동 누르기', '📶 업종 조기 신호 펼치기', '업종마다 따로 표시'], wy: '동 누르기 → 카드 접이 <b>📶 업종 조기 신호</b>', go: 'map', a: '업종마다 개업 폐업 생존 표시가 나옴',
      g: stg(bgMap(), tp(64, 66, 4, 14),
        box(8, 36, 284, 128, 12) + tx(20, 56, '○○동') + btnH(20, 68, 170, '📶 업종 조기 신호 ▼') + tp(105, 80, 40, 13),
        res('📶 업종 조기 신호', [['☕ 카페', '▲ 개업 흐름', '#16a34a'], ['🍺 호프', '▼ 폐업 > 개업', '#dc2626'], ['💇 미용', '1년 생존 ○', '#2563eb']].map(function (r, i) { return pop(tx(20, 84 + i * 24, r[0]) + tx(120, 84 + i * 24, r[1], { st: 'fill:' + r[2] }), 66 + i * 6); }).join(''))) },
    { k: 'apt', c: 'c', cov: 'card:apt', t: '🏢 단지 카드 — 값 흐름',
      d: '「🏠 부동산」을 켜고 가까이 보면 단지마다 가장 최근 매매가 표지가 뜬다. 단지를 누르면 24개월 가격 흐름 그림, 면적별 표(건수·최근·최고~최저), 최근 거래, 전월세와 전세가율(어림)이 나온다.',
      st: ['맨 위 🏠 부동산 칩 켜고 가까이', '단지 표지 누르기', '24개월 흐름 · 면적별 표'], wy: '맨 위 <b>🏠 부동산</b> → 단지 <b>누르기</b>', go: 'qc:biz|estate', a: '단지 가격 표지를 누르면 24개월 그래프가 나옴',
      g: stg(bgMap(), [[60, 60, '9.8억'], [210, 56, '12.4억'], [80, 142, '7.1억']].map(function (p) { return '<rect x="' + (p[0] - 28) + '" y="' + (p[1] - 18) + '" width="56" height="20" rx="8" fill="#1d4ed8"/>' + tx(p[0], p[1] - 4, p[2], { a: 'middle', st: 'fill:#fff' }); }).join(''),
        [[60, 60, '9.8억'], [210, 56, '12.4억'], [80, 142, '7.1억']].map(function (p) { return '<rect x="' + (p[0] - 28) + '" y="' + (p[1] - 18) + '" width="56" height="20" rx="8" fill="#1d4ed8"/>' + tx(p[0], p[1] - 4, p[2], { a: 'middle', st: 'fill:#fff' }); }).join('') + tp(210, 48, 40, 14),
        res('○○단지 · 24개월', '<line x1="24" y1="140" x2="280" y2="140" stroke="#94a3b8"/><path d="M24 120 L60 116 L96 118 L132 104 L168 100 L204 92 L240 84 L280 78" fill="none" stroke="#1d4ed8" stroke-width="3" stroke-dasharray="420" style="animation-name:dr64"/>' + tx(280, 72, '12.4억', { a: 'end' }))) },

    /* ── 💡 숨은 기능 */
    { k: 'try', c: 'x', cov: 'x:try', t: '🎟 맛보기 — 열쇠 없이 실시간',
      d: '실시간 층(막힘·돌발 등)은 원래 기기마다 열쇠가 필요하다. 「🎟 맛보기 켜기」를 누르면 이 지도 운영자의 열쇠로 기기마다 하루 정해진 분만큼 잠깐 본다.',
      st: ['🗂 → 📡 실시간 교통 층 켜기', '범례의 🎟 맛보기 켜기', '남은 분만큼 지금 상황'], wy: '🗂 → ⛅ 날씨·실시간 → 📡 실시간 교통 → 범례 <b>🎟 맛보기 켜기</b>', go: 'btn:m2dFold', a: '맛보기를 켜면 남은 분이 줄며 실시간 길이 보임',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/><path d="M10 140 C 80 120, 120 60, 290 40" class="rdl" stroke-width="14" fill="none"/>', box(60, 50, 180, 50, 10) + tx(150, 72, '🔑 열쇠가 없습니다', { a: 'middle' }) + tx(150, 90, '실시간은 기기마다 열쇠', { c: 'ex', a: 'middle' }),
        btnH(50, 60, 200, '🎟 맛보기 켜기 · 키 없이') + tp(150, 72, 40, 14),
        '<path d="M10 140 C 80 120, 120 60, 290 40" stroke="#dc2626" stroke-width="8" fill="none" stroke-linecap="round"/>' + pop(box(150, 96, 140, 44, 9) + tx(160, 114, '🎟 맛보기 중') + tx(160, 132, '오늘 ○분 남음', { c: 'ex', a: 'start' }), 68) + ex(296, 166)) },
    { k: 'fav', c: 'x', cov: 'set:레이어_구성 home:my', t: '⭐ 즐겨찾기 · 저장한 보기',
      d: '레이어 이름 옆 ☆ 로 자주 쓰는 층을 모으고, 「＋ 이 구성 저장」으로 지금 켠 층 묶음을 이름 붙여 둔다. 홈의 「⭐ 저장한 보기」에서 한 번에 다시 열고, 설정에서 고치거나 처음대로 되돌린다.',
      st: ['층을 켜고 ＋ 이 구성 저장', '이름 붙이기(예: 금요일 야간)', '홈 ⭐ 에서 한 번에 다시'], wy: '설정 → 레이어 구성 <b>＋ 이 구성 저장</b> · ← 홈 <b>⭐ 저장한 보기</b>', go: 'set', a: '지금 켠 층을 저장하고 홈에서 다시 엶',
      g: stg(bgMap() + [[40, 60], [150, 120], [220, 70]].map(function (p) { return '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6" fill="#7c3aed"/>'; }).join(''), btnH(150, 6, 142, '＋ 이 구성 저장') + tp(221, 18, 4, 14),
        box(40, 50, 220, 60, 10) + tx(52, 72, '이름') + '<rect x="52" y="80" width="196" height="22" rx="6" fill="rgba(29,78,216,.10)"/>' + tx(60, 96, '금요일 야간'),
        box(8, 8, 284, 154, 12) + tx(20, 30, '⭐ 저장한 보기') + pop(list(20, 40, 260, ['⭐ 금요일 야간 · 레이어 3개', '⭐ 큰비 대비 · 레이어 5개'], 0), 66) + tp(150, 56, 80, 12) + ex(284, 158)) },
    { k: 'ai', c: 'x', cov: 'x:ai x:findit', t: '🤖 AI 에게 알려 주기 · 🔎 없는 자료',
      d: '지도 맨 아래 「🤖 AI에게 이 지도 알려 주기」의 글을 복사해 쓰는 AI 에 붙이면 그 AI 가 이 공개 자료를 찾아 읽는다. 「🔎 없는 자료 찾는 법」은 여기 없는 자료를 어느 공식 창구에 물으면 되는지 알려 준다.',
      st: ['지도 맨 아래 줄', '🤖 글 복사', '쓰는 AI 에 붙여 묻기'], wy: '지도 맨 아래 <b>🤖 AI에게 이 지도 알려 주기</b> · <b>🔎 없는 자료 찾는 법</b>', go: 'map', a: '글을 복사해 AI 대화창에 붙이면 AI 가 자료를 읽음',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>', box(8, 130, 284, 32, 9) + tx(20, 151, '🤖 AI에게 이 지도 알려 주기') + tp(110, 146, 6, 13),
        box(8, 20, 284, 110, 10) + [0, 1, 2, 3].map(function (i) { return '<rect x="20" y="' + (36 + i * 18) + '" width="' + [240, 200, 250, 180][i] + '" height="8" rx="4" fill="#94a3b8"/>'; }).join('') + btnH(184, 100, 100, '📋 복사') + tp(234, 112, 44, 12),
        box(8, 14, 284, 60, 12) + tx(20, 36, '💬 (붙여 넣음) 이 지도에서') + tx(20, 56, '서초 밤 사고 자료 찾아 줘', { c: 'ex', a: 'start' }) + pop(box(40, 88, 252, 60, 12) + tx(52, 110, '🤖 data/ai.json 을 보니…') + tx(52, 130, '자료 파일 · 출처 · 읽는 차례', { c: 'ex', a: 'start' }), 74) + ex(296, 166)) },
    { k: 'win', c: 'x', cov: 'x:win', t: '🪟 겹친 창 고르기',
      d: '창이 여러 개 겹치면 방금 연 창·만진 창이 맨 위로 온다. 둘 넘게 겹치면 위에 「겹친 창」 칩이 떠서 고른 창을 맨 위로 올린다.',
      st: ['창 여럿 열기', '겹친 창 칩이 뜸', '고른 창이 맨 위로'], wy: '창이 겹치면 위 막대 아래 <b>겹친 창</b> 칩', go: 'map', a: '겹친 창 중 고른 것이 맨 위로 올라옴',
      g: stg(bgMap(), box(20, 40, 170, 110, 10) + tx(32, 60, '레이어') + box(60, 54, 170, 100, 10) + tx(72, 74, '반경 분석') + box(110, 66, 170, 96, 10) + tx(122, 86, '정보 카드'),
        box(20, 40, 170, 110, 10) + box(60, 54, 170, 100, 10) + box(110, 66, 170, 96, 10) + tx(122, 86, '정보 카드') + box(8, 6, 284, 26, 9) + tx(20, 24, '겹친 창:') + btnL(84, 7, 70, '레이어') + btnL(160, 7, 80, '반경 분석') + tp(200, 19, 40, 12),
        box(20, 40, 170, 110, 10) + box(110, 66, 170, 96, 10) + pop(box(60, 54, 170, 100, 10) + tx(72, 74, '📐 반경 분석') + tx(72, 94, '맨 위로', { c: 'ex', a: 'start' }), 66) + ex(296, 166)) },

    /* ── ⚙ 설정 */
    { k: 'sstart', c: 's', cov: 'set:시작', t: '⚙ 앱을 열면 · 처음 자리',
      d: '앱을 열면 지도부터 또는 홈부터 열지, 처음 자리를 마지막 본 곳·지금 위치·기본 중 어디로 할지 고른다. 저장한 보기를 「🏠 처음 보기」로 정해 두면 그 보기가 먼저 열린다.',
      st: ['⚙ 설정 → 시작', '앱을 열면: 지도 · 홈', '처음 자리: 마지막 · 지금 위치 · 기본'], wy: '홈 ⚙ → <b>설정 → 시작</b>', go: 'set', a: '설정의 시작 칸에서 고름',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>' + box(8, 8, 284, 154, 12) + tx(20, 30, '⚙ 설정 · 시작'),
        tx(20, 60, '앱을 열면') + btnH(120, 46, 70, '지도') + btnL(196, 46, 70, '홈') + tp(231, 58, 14, 12),
        tx(20, 60, '앱을 열면') + btnL(120, 46, 70, '지도') + btnH(196, 46, 70, '홈') + tx(20, 100, '처음 자리') + btnL(100, 86, 86, '마지막 본 곳') + btnH(192, 86, 86, '지금 위치') + tp(235, 98, 44, 12),
        tx(20, 60, '앱을 열면') + btnL(120, 46, 70, '지도') + btnH(196, 46, 70, '홈') + tx(20, 100, '처음 자리') + btnL(100, 86, 86, '마지막 본 곳') + btnH(192, 86, 86, '지금 위치') + pop(tx(20, 142, '이 기기에만 남는다', { c: 'ex', a: 'start' }), 70)) },
    { k: 'sview', c: 's', cov: 'set:화면', t: '🔠 밝기 · 글씨 크기 · 메뉴 접기',
      d: '밝기(자동·낮·밤), 글씨 크기(가− 가+), 위 빠른 메뉴와 레이어 판을 지도를 만지면 접을지·늘 펼칠지 고른다. 밤 근무 중에는 「밤」, 눈이 피곤하면 「가+」.',
      st: ['⚙ 설정 → 화면', '가+ 로 글씨 키우기', '메뉴 · 레이어 판 접기 고르기'], wy: '홈 ⚙ → <b>설정 → 화면</b>', go: 'set', a: '글씨 크기 단추를 누르면 글자가 커짐',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>' + box(8, 8, 284, 154, 12) + tx(20, 30, '⚙ 설정 · 화면'),
        tx(20, 60, '밝기') + btnL(90, 46, 60, '자동') + btnL(156, 46, 60, '낮') + btnH(222, 46, 60, '밤') + tp(252, 58, 8, 12),
        tx(20, 60, '글씨 크기 100%') + btnL(160, 46, 56, '가−') + btnH(222, 46, 56, '가+') + tp(250, 58, 40, 12) + tx(20, 110, '가나다 지도 글씨', { st: 'font-size:12px' }),
        tx(20, 60, '글씨 크기 130%') + btnL(160, 46, 56, '가−') + btnH(222, 46, 56, '가+') + tx(20, 112, '가나다 지도 글씨', { st: 'font-size:17px' }) + tx(20, 146, '빠른 메뉴: 지도 만지면 접기 · 늘 펼침', { c: 'ex', a: 'start' })) },
    { k: 'skey', c: 's', cov: 'set:자료·기기', t: '🔑 열쇠 · 설정 파일로 옮기기',
      d: '국가교통정보센터(ITS)·공공데이터포털·홍수위험지도 열쇠를 이 기기에만 넣는다. 설정과 저장한 보기는 파일로 내보내 다른 기기에서 되살린다(열쇠는 파일에 안 들어간다). 받아 둔 자료만 비울 수도 있다(레이어·설정은 그대로).',
      st: ['⚙ 설정 → 자료·기기', '🔑 넣기 · 내보내기', '다른 기기에서 되살리기'], wy: '홈 ⚙ → <b>설정 → 자료·기기</b>', go: 'set', a: '설정 파일을 내보내 다른 폰에서 되살림',
      g: stg('<rect class="bk" x="0" y="0" width="300" height="170"/>', box(8, 8, 284, 154, 12) + tx(20, 30, '⚙ 자료·기기') + tx(20, 60, '🔑 ITS') + btnH(200, 46, 80, '넣기') + tp(240, 58, 6, 12) + tx(20, 92, '🔑 공공데이터포털') + btnL(200, 78, 80, '넣기'),
        box(8, 8, 284, 154, 12) + tx(20, 30, '⚙ 자료·기기') + tx(20, 60, '설정·저장한 보기') + btnH(170, 46, 110, '내보내기') + tp(225, 58, 40, 12) + pop('<rect x="120" y="96" width="60" height="50" rx="6" fill="#e2e8f0" stroke="#64748b"/><text x="150" y="128" text-anchor="middle" style="font:800 12px system-ui;fill:#334155">.json</text>', 44),
        '<rect class="wn" x="20" y="20" width="90" height="140" rx="14"/><rect class="wn" x="190" y="20" width="90" height="140" rx="14"/>' + '<g style="offset-path:path(\'M70 90 L230 90\');animation-name:drive;animation-timing-function:linear"><rect x="-16" y="-12" width="32" height="24" rx="4" fill="#e2e8f0" stroke="#64748b"/></g>' + pop(tx(235, 140, '되살림 ✓', { a: 'middle', st: 'fill:#16a34a' }), 84) + tx(150, 60, '열쇠는 안 들어감', { c: 'ex', a: 'middle' })) }
  ];
  /* 옛 장면(배열 꼴)에 갈래·덮는 메뉴·단계·실제로 열기를 붙인다 */
  var OLDX = {
    sig: { c: 'c', cov: 'card:sig', st: ['맨 위 🚦 교통 칩(신호 레이어)', '교차로 누르기', '방향마다 녹색·적색 · 남은 초'], go: 'qc:police|traf' },
    spd: { c: 'l', cov: 'card:spd', st: ['🗂 → 📡 실시간 교통 → 소통', '길 색 보기(초록·노랑·빨강)', '누르면 지금 · 평소 속도'], go: 'btn:m2dFold' },
    sim: { c: 't', cov: 'tool:sim', st: ['🧰 도구 → 🧪 시뮬', '막히는 교차로 고르기', '지금 판 · 바꾼 판 견주기'], go: 'tool:sim' },
    lnk: { c: 't', cov: 'tool:lnk', st: ['🧰 도구 → 🧩 엮임 보기', '가운데 교차로 · 동 고르기', '이어진 것 · 이유 · 근거(A~E)'], go: 'tool:lnk' },
    dong: { c: 'c', cov: 'card:dong', st: ['지도에서 동 누르기', '아래에서 카드가 올라옴', '사람 · 가게 · 사고 · 집값 막대'], go: 'map' },
    deal: { c: 't', cov: 'tool:deal', st: ['🧰 도구 → 🏷 최근 거래 찾기', '목적 고르기(농지·상가·아파트 …)', '그 리 · 읍면 · 구의 최근 거래'], go: 'tool:deal' },
    dec: { c: 'h', cov: 'tool:dec dec:d1', st: ['홈 → 👮 → 🚓 어디 설까', '날짜 · 시간대 · 목적 고르기', '후보 ①②③과 근거'], go: 'dec:d1' },
    rain: { c: 'h', cov: 'dec:d4', st: ['홈 → 👮 → 🌧 큰비', '잠겼던 길 · 지하차도 후보', '둘레 길 · 근거 보기'], go: 'dec:d4' },
    prd: { c: 't', cov: 'tool:prd', st: ['🧰 도구 → 🚨 신고 차량 예측', '신고 시각 · 달아난 방향 넣기', '몇 분 뒤 닿을 수 있는 길'], go: 'tool:prd' },
    nav: { c: 't', cov: 'tool:nav', st: ['🧰 도구 → 🧭 네비 가르고', '지도를 두 번 톡 → 목적지', '신호 대기를 셈한 길'], go: 'tool:nav' },
    get: { c: 't', cov: 'tool:get', st: ['🧰 도구 → 📥 지역 받기', '다니는 구 고르고 받기', '통신이 끊겨도 열림'], go: 'tool:get' }
  };
  /* 보여 줄 차례 — 갈래 안에서 */
  var ORDER = ['home', 'sit', 'dec', 'dui', 'rally', 'rain', 'log',
    'move', 'layer', 'chips', 'time', 'leg', 'first', 'dark', 'guide',
    'sig', 'dong', 'explain', 'cell', 'brief', 'apt', 'esig', 'watch',
    'sim', 'lnk', 'orc', 'prd', 'nav', 'deal', 'live', 'biz', 'rad', 'pidx', 'pstat', 'mrg', 'gdr', 'tax', 'get', 'ui',
    'spd', 'm_pop', 'm_move', 'm_life', 'm_care', 'm_traf', 'm_local', 'm_safety', 'm_spend', 'm_estate', 'm_now', 'm_season', 'm_live', 'm_map',
    'try', 'fav', 'ai', 'win', 'sstart', 'sview', 'skey'];
  SC = SC.map(function (s) { var x = OLDX[s[0]] || {}; return { k: s[0], c: x.c || 'x', cov: x.cov || '', t: s[2], d: s[3], wy: s[4], a: s[5], g: s[6], st: x.st || [], go: x.go || '' }; }).concat(NEW);
  SC.sort(function (a, b) { var i = ORDER.indexOf(a.k), j = ORDER.indexOf(b.k); return (i < 0 ? 999 : i) - (j < 0 ? 999 : j); });
  var CAT = [['all', '전부'], ['h', '🏠 홈·경찰 전용'], ['b', '🌟 기본 조작'], ['c', '👆 누르면'], ['t', '🧰 도구'], ['l', '🗂 레이어'], ['x', '💡 숨은 기능'], ['s', '⚙ 설정']], CUR = 'all', Q = '';
  var CATN = {}; CAT.forEach(function (c) { CATN[c[0]] = c[1]; });

  /* v3 (2026-11-22 소유자 「뭐가 궁금한지를 따라서 가는 것」) 궁금한 것 → 차례대로 볼 장면 */
  var QS = [['work', '👮 오늘 어디에 서나', ['home', 'dec', 'sit', 'dui', 'rally', 'log']],
    ['sig', '🚦 신호가 몇 초 남았나', ['sig', 'brief', 'watch', 'sim']],
    ['risk', '🚗 여기 사고·위험은', ['m_traf', 'brief', 'm_season', 'rain', 'mrg']],
    ['jam', '🚥 지금 어디가 막히나', ['spd', 'm_live', 'prd', 'nav']],
    ['town', '👥 이 동네는 어떤 곳', ['dong', 'explain', 'cell', 'm_pop', 'm_life']],
    ['home9', '🏠 집값·전세·세금', ['deal', 'apt', 'live', 'tax', 'm_estate']],
    ['shop', '🏪 가게를 차리면', ['biz', 'esig', 'm_spend', 'rad']],
    ['kid', '🎒 아이 학교·밤길', ['m_care', 'm_safety', 'orc']],
    ['start', '🌟 처음이라 기본부터', ['move', 'layer', 'chips', 'time', 'leg', 'first']],
    ['more', '💡 숨은 기능·AI', ['try', 'fav', 'ai', 'get', 'ui']]];
  /* 글(설명서 카드 제목 등) → 가장 맞는 장면 — 앞줄이 먼저 */
  var PICK = [[/관내 브리핑|경찰서 카드|엑셀로/, 'pidx'], [/사다리/, 'm_local'], [/업무 시각표/, 'prd'], [/도구 쓰기/, 'rad'], [/^\s*🧩|그래서 무엇을|해 보고 다시|무엇이 있나|무엇과 이어지나/, 'orc'], [/관내 학교/, 'm_care'], [/행정동에서 시작|이 동네 한눈에/, 'dong'], [/상권 · 부동산/, 'm_spend'], [/언제 막히나|얼마나 걸리나/, 'spd'], [/지역경찰|여청|여성청소년|형사|수사\(|외사|안보|만족도·인력/, 'pstat'], [/실측 신호|신호/, 'sig'], [/음주운전 흐름|음주운전 —/, 'gdr'], [/음주/, 'dui'], [/집회|행사/, 'rally'], [/반경/, 'rad'], [/창업|가게|손익|엑셀/, 'biz'], [/세금/, 'tax'],
    [/이사/, 'live'], [/땅|상가|시골집|집값|전세|실거래|사고팔/, 'deal'], [/도주|신고 차량/, 'prd'], [/어디에 먼저 서야|업무 시각표/, 'dec'], [/언제 막히나|얼마나 걸리나|막히는 교차로|시뮬/, 'sim'],
    [/학교|학원|아이/, 'm_care'], [/출퇴근|붐비|사람 · 차 흐름/, 'm_move'], [/운전할 때|사고/, 'm_traf'], [/카메라|CCTV/, 'm_traf'], [/밤길|야간|소방/, 'm_safety'],
    [/병원|약국|주차|따릉이|충전소|반려동물/, 'm_life'], [/큰비|폭염|더위|날씨가 바뀌면|눈 ·|눈·/, 'rain'], [/지금 교통|날씨/, 'm_live'], [/동네|어떤 곳|한눈에/, 'dong'],
    [/때를 바꿔|시각을 바꿔/, 'time'], [/즐겨찾기|저장한 보기/, 'fav'], [/처음 화면|처음 세팅/, 'first'], [/상황 한 번에/, 'sit'], [/층이 뭔지|레이어가 뭐지/, 'leg'], [/엮어서|겹쳐/, 'orc'],
    [/통신이 안|지역 받기/, 'get'], [/AI/, 'ai'], [/메뉴가 자꾸/, 'ui'], [/밤 화면|전체화면/, 'dark'], [/지표표/, 'pidx'], [/경찰 통계/, 'pstat'], [/관내 브리핑|관내 파악|들어오기/, 'home'],
    [/관할|관서|경찰서 카드/, 'm_local'], [/상권|부동산/, 'm_spend'], [/네비|가르고/, 'nav'], [/바뀌고 있는/, 'esig'], [/지역 고르기|찾기|자리 잡기/, 'move'], [/레이어 켜기|지도 층/, 'layer'], [/눌러서 읽기/, 'explain'], [/도구 쓰기/, 'live']];
  function pick(t) { t = String(t || ''); for (var i = 0; i < PICK.length; i++) if (PICK[i][0].test(t)) return PICK[i][1]; return ''; }
  var PATH = null;
  function card(s, i) { var w = s.w || [0, 33, 66];
    return '<div class="sc" data-c="' + s.c + '" data-i="' + i + '"><h5>' + s.t + '</h5><p>' + s.d + '</p>' + SV + s.a + '">' + s.g + '</svg>' +
      (s.st.length ? '<div class="stp an">' + s.st.map(function (x, j) { return '<button data-st="' + j + '" style="animation-name:' + hs(w[j], j < 2 ? w[j + 1] : 100) + '"><i>' + (j + 1) + '</i>' + x + '</button>'; }).join('') + '<button data-st="p" class="pl">▶ 다시 움직이기</button></div>' : '') +
      '<div class="wy">📍 어디서: ' + s.wy + (s.go ? '<button class="go" data-go="' + s.go + '">▶ 실제로 열어 보기</button>' : '') + '</div></div>'; }
  function css() { var st = document.getElementById('m2dShowCss'); if (!st) { st = document.createElement('style'); st.id = 'm2dShowCss'; document.head.appendChild(st); } var t = CSS + ' ' + Object.keys(PK).map(function (k) { return PK[k]; }).join(' '); if (st.textContent !== t) st.textContent = t; }
  function el() { var e = document.getElementById('m2dShow'); if (e) return e;
    var html = SC.map(card).join('');   /* 그림을 먼저 만들어야 움직임(PK)이 다 모인다 */
    css();
    var cnt = {}; SC.forEach(function (s) { cnt[s.c] = (cnt[s.c] || 0) + 1; });
    e = document.createElement('div'); e.id = 'm2dShow'; e.setAttribute('role', 'dialog'); e.setAttribute('aria-label', '그림으로 보는 할 수 있는 것');
    e.innerHTML = '<div class="wh"><b>🎬 이 지도로 할 수 있는 것 <small>' + SC.length + '가지</small></b><button class="wx" data-w="x">✕ 닫기</button></div>' +
      '<p class="wd">그림이 저절로 움직입니다. 그림 밑 <b>① ② ③</b> 을 누르면 그 장면에서 멈추고 ▶ 로 다시 움직입니다. <b>「▶ 실제로 열어 보기」</b>는 그 화면을 바로 엽니다. 그림 속 숫자·이름은 모두 <b>예시</b>입니다.' + (RM ? ' (이 기기는 움직임 줄이기가 켜져 있어 마지막 장면으로 멈춰 둡니다 — ① ② ③ 으로 넘겨 보세요.)' : '') + '</p>' +
      '<div class="wqs"><b>🙋 무엇이 궁금하세요?</b> <small>고르면 그것을 알아내는 차례대로 장면이 나옵니다</small><div>' + QS.map(function (q) { return '<button data-q="' + q[0] + '">' + q[1] + '</button>'; }).join('') + '</div><p class="wqp"></p></div>' +
      '<input class="wq" type="search" placeholder="🔍 찾기 — 예: 음주 · 학교 · 집값 · 신호" aria-label="장면 찾기">' +
      '<div class="wf">' + CAT.map(function (c) { return '<button data-f="' + c[0] + '"' + (c[0] === CUR ? ' class="on"' : '') + '>' + c[1] + ' <small>' + (c[0] === 'all' ? SC.length : (cnt[c[0]] || 0)) + '</small></button>'; }).join('') + '</div>' +
      '<div class="wg">' + html + '</div><p class="wn0">찾는 장면이 없습니다 — 다른 낱말로 찾거나 「전부」를 누르세요.</p>';
    document.body.appendChild(e);
    e.addEventListener('click', function (ev) { var b = ev.target.closest('[data-w],[data-f],[data-st],[data-go],[data-q]'); if (!b) return;
      if (b.getAttribute('data-w') === 'x') { close(); return; }
      if (b.hasAttribute('data-q')) { var qk = b.getAttribute('data-q'); setQ(PATH && PATH.k === qk ? null : qk); return; }
      if (b.hasAttribute('data-go')) { go(b.getAttribute('data-go')); return; }
      if (b.hasAttribute('data-st')) { var c = b.closest('.sc'), v = b.getAttribute('data-st'); if (v === 'p') play(c); else jump(c, +v); return; }
      PATH = null; paintQ(); CUR = b.getAttribute('data-f'); e.querySelectorAll('.wf button').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-f') === CUR); }); filt(); e.scrollTop = 0; });
    e.querySelector('.wq').addEventListener('input', function (ev) { Q = String(ev.target.value || '').trim(); filt(); });
    document.addEventListener('keydown', function (ev) { if (ev.key === 'Escape' && isOn()) close(); });
    if (window.IntersectionObserver) { IO = new IntersectionObserver(function (es) { es.forEach(function (x) { var c = x.target; c.__vis = x.isIntersecting; if (!c.__hold) run(c, x.isIntersecting && isOn() && !RM); }); }, { root: e, rootMargin: '80px' });
      e.querySelectorAll('.sc').forEach(function (c) { IO.observe(c); }); }
    return e; }
  function filt() { var e = document.getElementById('m2dShow'), n = 0, q = Q.toLowerCase();
    e.querySelectorAll('.wg .sc').forEach(function (x) { var s = SC[+x.getAttribute('data-i')], pi = PATH ? PATH.ks.indexOf(s.k) : 0, ok = pi >= 0 && (PATH || CUR === 'all' || s.c === CUR) && (!q || (s.t + ' ' + s.d + ' ' + s.wy + ' ' + s.st.join(' ')).toLowerCase().indexOf(q) >= 0);
      x.style.display = ok ? '' : 'none'; x.style.order = PATH ? pi : ''; var nb = x.querySelector('.qn'); if (nb) nb.parentNode.removeChild(nb); if (PATH && ok) { var h5 = x.querySelector('h5'); if (h5) h5.insertAdjacentHTML('afterbegin', '<span class="qn">' + (pi + 1) + '</span>'); } n += ok ? 1 : 0; });
    e.querySelector('.wn0').style.display = n ? 'none' : 'block';
    if (RM) setTimeout(function () { e.querySelectorAll('.sc').forEach(function (c) { if (c.style.display !== 'none' && !c.__hold) jump(c, 2, true); }); }, 0); }
  function paintQ() { var e = document.getElementById('m2dShow'); if (!e) return; e.querySelectorAll('.wqs [data-q]').forEach(function (x) { x.classList.toggle('on', !!PATH && x.getAttribute('data-q') === PATH.k); });
    var p = e.querySelector('.wqp'); if (p) p.innerHTML = PATH ? '<b>' + PATH.t + '</b> — 이 차례대로 보면 됩니다(' + PATH.ks.length + '장면) · 같은 단추를 다시 누르면 전부 보기' : ''; }
  function setQ(k) { var q = null; QS.forEach(function (x) { if (x[0] === k) q = x; }); var e = el();
    PATH = q ? { k: q[0], t: q[1], ks: q[2].filter(function (z) { return SC.some(function (s) { return s.k === z; }); }) } : null; Q = ''; var qi = e.querySelector('.wq'); if (qi) qi.value = '';
    if (PATH) { CUR = 'all'; e.querySelectorAll('.wf button').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-f') === 'all'); }); }
    paintQ(); filt(); var w = e.querySelector('.wqs'); if (w && PATH) { try { e.scrollTop = w.offsetTop - 8; } catch (er) {} } }
  function isOn() { var e = document.getElementById('m2dShow'); return !!(e && e.classList.contains('on')); }

  /* 움직임 다루기 — 화면에 보이는 장면만 돈다(폰이 무거워지지 않게) · ①②③ 은 그 때로 옮겨 멈춤 · ▶ 다시 */
  var IO = null;
  function anims(c) { try { return c.getAnimations ? c.getAnimations({ subtree: true }) : []; } catch (er) { return []; } }
  function run(c, on) { anims(c).forEach(function (a) { try { if (on) a.play(); else a.pause(); } catch (er) {} }); }
  function jump(c, j, auto) { var s = SC[+c.getAttribute('data-i')], w = s.w || [0, 33, 66], b = j < 2 ? w[j + 1] : 100, t = ((w[j] + b) / 2 + (j === 2 ? 8 : 0)) / 100 * 8000;
    anims(c).forEach(function (a) { try { var d = a.effect && a.effect.getTiming ? a.effect.getTiming().duration : 8000; a.pause(); a.currentTime = (typeof d === 'number' && d < 8000) ? d * 0.4 : t; } catch (er) {} });
    c.__hold = !auto || RM; c.querySelectorAll('.stp button').forEach(function (x) { x.classList.toggle('on', x.getAttribute('data-st') === String(j)); }); tick(); }
  function play(c) { c.__hold = false; c.querySelectorAll('.stp button').forEach(function (x) { x.classList.remove('on'); }); run(c, true); }

  /* 남은 초 — 장면 한 바퀴 8초 중 녹색 0~3.9초(그림 예시) · 등 색과 같은 시계(CSS 애니메이션)를 읽는다 */
  var T0 = Date.now(), TK = null;
  function tick() { var t = ((Date.now() - T0) / 1000) % 8, gl = document.querySelector('#m2dShow [data-sg]'), an = gl && gl.getAnimations ? gl.getAnimations()[0] : null;
    if (an && an.currentTime != null) t = (an.currentTime / 1000) % 8;
    var g = t < 3.9, y = !g && t < 4.7, n = g ? Math.ceil((3.9 - t) * 10) : y ? Math.ceil((4.7 - t) * 4) : Math.ceil((8 - t) * 10);
    document.querySelectorAll('#m2dShow [data-cd="sig"]').forEach(function (x) { x.textContent = n; x.style.fill = g ? '#16a34a' : y ? '#ca8a04' : '#dc2626'; }); }
  function open(k) { var e = el(); e.classList.add('on'); T0 = Date.now();
    if (typeof k === 'string' && k.indexOf('q:') === 0) setQ(k.slice(2));
    else if (typeof k === 'string' && k) { PATH = null; CUR = 'all'; Q = ''; paintQ(); filt(); var i = -1; SC.forEach(function (s, j) { if (s.k === k) i = j; }); var c = i >= 0 ? e.querySelector('.wg .sc[data-i="' + i + '"]') : null;
      var sc9 = function () { try { e.scrollTop += c.getBoundingClientRect().top - e.getBoundingClientRect().top - 14 - ((e.querySelector('.wh') || {}).offsetHeight || 0); } catch (er) {} };
      if (c) setTimeout(function () { sc9(); setTimeout(sc9, 350); c.classList.add('hit'); setTimeout(function () { c.classList.remove('hit'); }, 2600); if (!RM) play(c); }, 60); }
    e.querySelectorAll('.sc').forEach(function (c) { if (RM) { if (!c.__hold) jump(c, 2, true); } else if (!c.__hold) run(c, c.__vis !== false); });
    tick(); if (!TK) TK = setInterval(tick, 250);
    try { if (!(history.state || {}).m2dw) history.pushState({ m2dw: 1 }, '', location.href); } catch (er) {} }
  function close(fromPop) { var e = document.getElementById('m2dShow'); if (!e || !e.classList.contains('on')) return; e.classList.remove('on'); run(e, false); if (TK) { clearInterval(TK); TK = null; }
    if (!fromPop) { try { if ((history.state || {}).m2dw) history.back(); } catch (er) {} } }
  window.addEventListener('popstate', function () { if (isOn()) close(true); });
  document.addEventListener('visibilitychange', function () { var e = document.getElementById('m2dShow'); if (!e || !isOn() || RM) return; e.querySelectorAll('.sc').forEach(function (c) { if (!c.__hold) run(c, !document.hidden && c.__vis !== false); }); });

  /* ▶ 실제로 열어 보기 — 그림판·설정·홈을 차례로 닫고 그 화면을 연다(map2d.js 의 단추를 그대로 누른다 · 고치지 않음) */
  function $i(i) { return document.getElementById(i); }
  function go(a) { var p = a.split(':'), k = p[0], v = p.slice(1).join(':');
    if (!document.getElementById('m2dToolB')) { location.href = './#go=' + encodeURIComponent(a); return; }   /* 설명서 등 지도 밖 쪽 → 지도를 열고 그 화면으로 */
    close();
    if (k === 'set') return;
    setTimeout(function () { var sx = document.querySelector('#m2dSet.on [data-sk="x"]'); if (sx) sx.click();
      setTimeout(function () { var hm = document.querySelector('#m2dHome.on');
        if (k === 'home') { if (!hm && $i('m2dHomeB')) $i('m2dHomeB').click(); return; }
        if (hm) { var mb = hm.querySelector('[data-hm="map"]'); if (mb) mb.click(); }
        setTimeout(function () { act(k, v); }, 350); }, 350); }, 300); }
  function act(k, v) {
    if (k === 'tool') { var tb = $i('m2dToolB'), tl = $i('m2dTool'); if (!tb || !tl) return; if (!tl.classList.contains('on')) tb.click(); setTimeout(function () { var b = tl.querySelector('[data-tool="' + v + '"]'); if (b) b.click(); }, 80); }
    else if (k === 'dec') { if (window.tgDecide) window.tgDecide.open(v); }
    else if (k === 'btn') { var b = $i(v); if (b) b.click(); }
    else if (k === 'qc') { var q = document.querySelector('#m2dQC [data-qc="' + v + '"]'); if (q && !q.classList.contains('on')) q.click(); else if (!q && $i('m2dFold')) $i('m2dFold').click(); } }

  /* 설정 판에 칸 끼우기 — 작은 움직이는 그림(신호 셋) + 한 줄 */
  var MINI = '<svg viewBox="0 0 92 46" aria-hidden="true" class="an"><rect x="6" y="8" width="16" height="30" rx="4" fill="#111827"/>' +
    '<circle cx="14" cy="15" r="4" fill="#22c55e" style="animation:sgG 8s steps(1) infinite"/><circle cx="14" cy="23" r="4" fill="#facc15" style="animation:sgY 8s steps(1) infinite"/><circle cx="14" cy="31" r="4" fill="#ef4444" style="animation:sgR 8s steps(1) infinite"/>' +
    '<path d="M30 34 C 45 30, 55 14, 86 12" stroke="#fff" stroke-width="5" fill="none" opacity=".35"/><circle cx="60" cy="24" r="5" fill="#fff" style="animation:blink 1.6s infinite"/></svg>';
  function inject() { var s = document.getElementById('m2dSet'); if (!s || s.querySelector('.shw')) return; var sd = s.querySelector('.sd'); if (!sd) return;
    css();
    var b = document.createElement('button'); b.className = 'shw'; b.type = 'button'; b.innerHTML = MINI + '<span><b>🎬 그림으로 보기 — 이 지도로 할 수 있는 것 ' + SC.length + '가지</b><small>홈·경찰 전용 · 기본 조작 · 누르면 나오는 카드 · 도구 · 레이어 · 숨은 기능 · 설정 — 단계마다 그림으로, 바로 열어 보기까지</small></span>';
    b.addEventListener('click', function (ev) { ev.stopPropagation(); open(); });
    sd.parentNode.insertBefore(b, sd.nextSibling); }
  function watch() { var s = document.getElementById('m2dSet'); if (!s) { setTimeout(watch, 800); return; } inject();
    if (window.MutationObserver) new MutationObserver(function () { inject(); s.classList.toggle('paused', !s.classList.contains('on')); }).observe(s, { childList: true, attributes: true, attributeFilter: ['class'] }); }
  /* 설정 판은 처음 열 때 만들어진다 — 몸에 붙는 것을 지켜보다가 붙으면 그 판을 지켜본다 */
  function boot() { if (document.getElementById('m2dSet')) { watch(); return; }
    if (!window.MutationObserver) { setTimeout(boot, 1000); return; }
    var mo = new MutationObserver(function () { if (document.getElementById('m2dSet')) { mo.disconnect(); watch(); } }); mo.observe(document.body, { childList: true }); }
  window.tgShow = { open: open, close: close, pick: pick, qs: QS.map(function (q) { return [q[0], q[1]]; }), scenes: SC.map(function (s) { return s.k; }), title: function (k) { var t = ''; SC.forEach(function (s) { if (s.k === k) t = s.t; }); return t; }, cov: SC.map(function (s) { return s.cov; }).join(' ') };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
  (function () { var h = location.hash, m = /[#&]show=([^&]+)/.exec(h), g = /[#&]go=([^&]+)/.exec(h);
    if (m) { var v = decodeURIComponent(m[1]); setTimeout(function () { open(v === '1' ? '' : v); }, 600); }
    if (g && document.getElementById('m2dToolB')) { try { history.replaceState(history.state, '', location.href.replace(/[#&]go=[^&]*/, '').replace(/#$/, '')); } catch (er) {} setTimeout(function () { go(decodeURIComponent(g[1])); }, 1500); } })();
  /* v3 「💡 오늘의 사용법」 — 지도를 열면 아래에 작은 움직이는 그림 한 장 + 「무엇이 궁금하세요?」(처음 30일 · 하루 한 번 · 손대지 않으면 15초 뒤 접힘 · T-Book 「오늘의 사용법」과 같은 결)
     현장 주소(T-Book·가르고가 여는 #lat= · #ly= · #here= 등)로 열면 안 띄운다 · 저장 tg_map2d_tip_v1 = {f 처음 때, l 마지막 날, off 1} */
  var TIPN = 0;
  function tip() { if (!document.getElementById('m2dToolB') || /[#&](lat|lon|ly|here|gps|show|go|lnk|dec|sim)=/.test(location.hash)) return;
    if (isOn() || document.querySelector('#m2dOnb.on,#m2dSet.on,#m2dGate.on')) { if (++TIPN < 60) setTimeout(function () { try { tip(); } catch (er) {} }, 3000); return; }   /* 처음 차리기·설정·그림판이 떠 있으면 닫힐 때까지 기다린다(겹치지 않게) */
    var S = {}, td = new Date(), dk = td.getFullYear() + '-' + (td.getMonth() + 1) + '-' + td.getDate(); try { S = JSON.parse(localStorage.getItem('tg_map2d_tip_v1') || '{}') || {}; } catch (er) { S = {}; }
    if (S.off || S.l === dk) return; if (!S.f) S.f = Date.now(); if (Date.now() - S.f > 30 * 864e5) return; S.l = dk; try { localStorage.setItem('tg_map2d_tip_v1', JSON.stringify(S)); } catch (er) {}
    css(); var day = Math.floor(Date.now() / 864e5), pool = SC.filter(function (z) { return z.st.length && z.go; }), s = pool[day % pool.length], i = SC.indexOf(s);
    var e = document.createElement('div'); e.id = 'm2dUse'; e.setAttribute('role', 'dialog'); e.setAttribute('aria-label', '오늘의 사용법');
    e.innerHTML = '<div class="th"><b>💡 오늘의 사용법</b><button data-t="x" aria-label="닫기">✕</button></div><div class="tsc" data-i="' + i + '"><h5>' + s.t + '</h5>' + SV + s.a + '">' + s.g + '</svg><p class="tst">' + s.st.map(function (x, j) { return '<span><i>' + (j + 1) + '</i>' + x + '</span>'; }).join('') + '</p></div>'
      + '<div class="tb"><button data-t="go">▶ 실제로 열어 보기</button><button data-t="more">🎬 자세히</button></div><div class="tq"><b>🙋 무엇이 궁금하세요?</b><div>' + QS.slice(0, 6).map(function (q) { return '<button data-tq="' + q[0] + '">' + q[1] + '</button>'; }).join('') + '<button data-tq="">더 보기 ›</button></div></div>'
      + '<label class="toff"><input type="checkbox"> 다시 보지 않기</label>';
    document.body.appendChild(e); var hold = 0, tm = setTimeout(function () { if (!hold) shut(); }, 15000);
    function shut() { clearTimeout(tm); var cb = e.querySelector('.toff input'); if (cb && cb.checked) { S.off = 1; try { localStorage.setItem('tg_map2d_tip_v1', JSON.stringify(S)); } catch (er) {} } e.classList.add('out'); setTimeout(function () { if (e.parentNode) e.parentNode.removeChild(e); }, 300); }
    e.addEventListener('pointerdown', function () { hold = 1; clearTimeout(tm); });
    e.addEventListener('change', function () { hold = 1; clearTimeout(tm); });
    e.addEventListener('click', function (ev) { var b = ev.target.closest('[data-t],[data-tq]'); if (!b) return; var t = b.getAttribute('data-t');
      if (t === 'x') { shut(); return; } if (t === 'go') { shut(); go(s.go); return; } if (t === 'more') { shut(); open(s.k); return; }
      if (b.hasAttribute('data-tq')) { shut(); open(b.getAttribute('data-tq') ? 'q:' + b.getAttribute('data-tq') : ''); } });
    if (RM) setTimeout(function () { anims(e).forEach(function (a) { try { a.pause(); a.currentTime = 6000; } catch (er) {} }); }, 0); }
  setTimeout(function () { try { tip(); } catch (er) {} }, 2500);
})();
