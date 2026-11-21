/* 가르고 「그림으로 보기」 (2026-11-22 형님 「설정칸에 니가 할 수 있는 것을 이미지와 모션으로 — 모르는 사람은 아예 모른다 ·
   그려서 결과를 보여 줄 수도, 그냥 보여 줄 수도, 다르게 볼 수도 있게」)
   v2 (같은 날 형님 「더 구체적으로 모든 항목을 · 빠진 부분이 있는지 찾아서 꼭 사용설명을」) — gargo.js · speedo.js · sigladder.js 의 단추·말·설정을 하나씩 세어
   장면 6 → 31(갈래 8)로 늘리고, 모든 기능·설정 항목을 한 줄씩 적은 「☰ 항목별」을 더하고, 설정 판의 줄마다 그 그림으로 가는 🎬 를 붙였다.
   · 보는 길 넷 — ▶ 움직임(장면마다 그림이 움직인다) · ▦ 한 장(움직임 없이 결과만) · ☰ 항목별(모든 기능 · 어디서 · 어떻게) · 👆 실제 화면(진짜 단추를 차례로 짚는다).
   · 그림 속 말은 앱이 실제로 하는 말 그대로 쓴다(sigladder.js 「이대로」「발 떼기」「적색 진입 · 좌우」 · gargo.js 음성 「적색 교차로입니다. 좌우 확인」
     「경로를 벗어났습니다. 다시 찾습니다」「위치 신호가 약합니다. 경로를 따라 계속 안내합니다」「목적지 부근입니다. 목적지는 오른쪽입니다」 등).
     연비 몇 % · 도착 몇 분 같은 숫자는 보기로 넣은 것이고 재 본 값이 아니다 — 여러 순찰차 비교는 숫자 없이 차례만 그린다(도달 시간은 공개하지 않는다).
   · 움직임 줄이기(prefers-reduced-motion)면 처음부터 「한 장」.
   · gargo.js 를 고치지 않는다 — 설정 판(#gCfg)이 다시 그려질 때마다 맨 위 카드와 줄마다 🎬 를 끼우고(MutationObserver), 첫 안내 판(#gIntro)에도 단추 하나.
   · 앱의 말·단추 이름을 바꾸면 여기 그림 속 말도 같이 고친다. */
(function () {
  function $(id) { return document.getElementById(id); }
  var VIP = !!(window.TT && TT.VIP_ON), RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 그림 조각 ---------- */
  function car(c, police) {   /* 왼쪽 끝이 0 · 길이 30 */
    return '<rect x="0" y="-7" width="30" height="14" rx="4" fill="' + c + '"/>' + (police ? '<rect x="4" y="-2" width="22" height="4" fill="#1d4ed8"/><rect class="hw-lr" x="11" y="-10" width="4" height="4" rx="1" fill="#ef4444"/><rect class="hw-lb" x="15" y="-10" width="4" height="4" rx="1" fill="#3b82f6"/>' : '')
      + '<rect x="19" y="-5" width="7" height="10" rx="2" fill="rgba(255,255,255,.55)"/><circle cx="7" cy="7" r="3" fill="#0f172a"/><circle cx="23" cy="7" r="3" fill="#0f172a"/>';
  }
  function road(y, h) { return '<rect x="0" y="' + y + '" width="340" height="' + h + '" class="hw-rd"/><line x1="0" y1="' + (y + h / 2) + '" x2="340" y2="' + (y + h / 2) + '" class="hw-ln"/>'; }
  function lamp(x, y, cls) { return '<rect x="' + (x - 7) + '" y="' + (y - 16) + '" width="14" height="22" rx="4" fill="#1f2937"/><circle cx="' + x + '" cy="' + (y - 5) + '" r="5" class="' + cls + '"/><line x1="' + x + '" y1="' + (y + 6) + '" x2="' + x + '" y2="' + (y + 12) + '" stroke="#475569" stroke-width="2"/>'; }
  function card(x, w, c, n, s, v) {   /* 사다리 칸 한 개 — 앱의 #gLad 칸 모양 */
    var col = { g: '#16a34a', r: '#dc2626', y: '#f59e0b' }[c];
    return '<g><rect x="' + x + '" y="6" width="' + w + '" height="50" rx="8" class="hw-cd' + (c === 'r' ? ' rb' : '') + '"/><rect x="' + x + '" y="6" width="' + w + '" height="4" rx="2" fill="' + col + '"/>'
      + '<text x="' + (x + 7) + '" y="25" class="hw-t9">' + n + '</text><text x="' + (x + w - 7) + '" y="27" text-anchor="end" class="hw-t16" style="fill:' + col + '">' + s + '</text>'
      + '<text x="' + (x + 7) + '" y="47" class="hw-t11b">' + v + '</text></g>';
  }
  function T(x, y, s, c, a) { return '<text x="' + x + '" y="' + y + '"' + (a ? ' text-anchor="' + (a === 'm' ? 'middle' : 'end') + '"' : '') + ' class="' + (c || 'hw-t10b') + '">' + s + '</text>'; }
  function R(x, y, w, h, c, rx) { return '<rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="' + (rx == null ? 8 : rx) + '" class="' + (c || 'hw-cd') + '"/>'; }
  function BT(x, y, w, s, b) { return R(x, y, w, 22, b ? 'hw-bt' : 'hw-b2', 7) + T(x + w / 2, y + 15, s, b ? 'hw-t10w' : 'hw-t10b', 'm'); }
  function BUB(x, y, w, s, c) { return '<g' + (c ? ' class="' + c + '"' : '') + '>' + R(x, y, w, 24, 'hw-bub', 12) + T(x + w / 2, y + 16, s, 'hw-t11w', 'm') + '</g>'; }
  function BUB2(x, y, w, s1, s2, c) { return '<g' + (c ? ' class="' + c + '"' : '') + '>' + R(x, y, w, 38, 'hw-bub', 12) + T(x + w / 2, y + 16, s1, 'hw-t11w', 'm') + T(x + w / 2, y + 31, s2, 'hw-t11w', 'm') + '</g>'; }
  function TAP(x, y, c) { return '<g class="' + c + '"><circle cx="' + x + '" cy="' + y + '" r="11" class="hw-pl"/><text x="' + (x + 2) + '" y="' + (y + 19) + '" text-anchor="middle" style="font-size:20px">👆</text></g>'; }
  function MAP() { var g = '<rect x="0" y="0" width="340" height="190" class="hw-map"/>';
    [40, 95, 150].forEach(function (y) { g += '<rect x="0" y="' + y + '" width="340" height="9" class="hw-st"/>'; });
    [60, 170, 280].forEach(function (x) { g += '<rect x="' + x + '" y="0" width="9" height="190" class="hw-st"/>'; }); return g; }
  function PIN(x, y) { return '<path d="M' + (x - 6) + ' ' + (y - 9) + ' L' + x + ' ' + y + ' L' + (x + 6) + ' ' + (y - 9) + 'z" fill="#dc2626"/><circle cx="' + x + '" cy="' + (y - 13) + '" r="8" fill="#dc2626"/><circle cx="' + x + '" cy="' + (y - 13) + '" r="3" fill="#fff"/>'; }
  function ME(x, y) { return '<circle cx="' + x + '" cy="' + y + '" r="12" fill="#2563eb" opacity=".18"/><circle cx="' + x + '" cy="' + y + '" r="6" fill="#2563eb" stroke="#fff" stroke-width="2.5"/>'; }
  function RT(d, c) { return '<path d="' + d + '" pathLength="360" class="hw-rt' + (c ? ' ' + c : '') + '"/>'; }
  function ST(x, y) { return '<circle cx="' + x + '" cy="' + y + '" r="7" fill="#fff" stroke="#2563eb" stroke-width="3"/>'; }
  function CHIP(x, y, w, s) { return R(x, y, w, 26, 'hw-cd', 13) + T(x + w / 2, y + 17, s, 'hw-t10b', 'm'); }

  /* ---------- 갈래 · 장면 ----------
     w: { 이름: [나타남 %, 사라짐 %] } → 그림의 class="w-이름" 이 그 사이에만 보인다(0 이하 = 처음부터 · 100 이상 = 끝까지)
     m: { 이름: '키프레임' } → class="m-이름" 에 그 움직임 · 한 바퀴 8초 · st = 「한 장」에서 멈출 때 */
  var CH = [['st', '처음'], ['fd', '찾기'], ['cd', '길 고르기'], ['gd', '안내 중'], ['pc', '경찰 출동'], ['cr', '켜놓고 다니기·지도'], ['sc', '화면·소리'], ['rc', '기록·보정']];
  var SC = [
    { k: 'open', c: 'st', ic: '🔑', t: '처음 열기 — 확인코드 · 위치 허락', tour: -1,
      d: '처음 한 번 <b>받은 확인코드</b>를 넣는다(이 기기에 기억 · 다음부터 안 묻는다 · 데이터 압축지도와 같은 값). 브라우저가 위치를 물으면 <b>허락</b>해야 내 자리가 잡힌다. 첫 안내 판의 「알겠다 — 시작」을 누르면 지도.',
      r: '결과 — 파란 점이 내 자리. 위치를 막았으면 지도를 길게 눌러 「여기서 떠나기」로 출발점을 정한다.',
      w: { g: [2, 100], t1: [12, 26], d: [28, 100], t2: [42, 56], me: [58, 100] },
      svg: function () {
        return MAP() + '<g class="w-g">' + R(30, 8, 280, 58) + T(170, 28, '🚓 가르고 — 경찰 동료용입니다', 'hw-t10b', 'm') + R(46, 36, 160, 22, 'hw-b2', 7) + T(58, 51, '● ● ●', 'hw-t11') + BT(214, 36, 80, '들어가기', 1) + '</g>' + TAP(254, 47, 'w-t1')
          + '<g class="w-d">' + R(60, 74, 220, 58) + T(170, 94, '📍 위치 사용을 허락할까요?', 'hw-t10b', 'm') + BT(76, 104, 88, '차단') + BT(176, 104, 88, '허락', 1) + '</g>' + TAP(220, 115, 'w-t2')
          + '<g class="w-me">' + ME(52, 164) + BUB(78, 152, 254, '파란 점 = 내 자리 · 이제 목적지를 정한다') + '</g>';
      } },
    { k: 'find', c: 'fd', ic: '🔎', t: '목적지 찾기 — 적거나 · 말하거나 · 누르거나', st: '-8.6s', tour: 2,
      d: '위 칸에 주소·이름(건물·역·교차로)을 적거나 <b>🎤 말한다</b>. 아니면 지도를 <b>두 번 톡 · 길게 눌러</b> 「이곳을 목적지로 할까요?」 판에서 고른다. 통신이 끊겨 있으면 이 기기 안의 이름(역·신호)만 찾는다.',
      r: '결과 — 길과 걸리는 시간·도착 시각이 바로 나오고, 「▶ 안내 시작」을 누르면 신호 사다리가 뜬다.',
      svg: function () {
        return MAP() + '<rect x="10" y="8" width="320" height="26" rx="13" class="hw-cd"/><text x="22" y="26" class="hw-t11"><tspan class="hw-k1">서</tspan><tspan class="hw-k2">초</tspan><tspan class="hw-k3">역</tspan></text>'
          + '<g class="hw-mic"><circle cx="314" cy="21" r="9" fill="#2563eb"/><text x="314" y="25" text-anchor="middle" class="hw-t10w">🎤</text></g>'
          + '<g class="hw-o6"><rect x="10" y="38" width="200" height="24" rx="8" class="hw-cd"/><text x="20" y="54" class="hw-t11b">📍 서초역</text></g>'
          + '<path d="M64 154 V99 H174 V44 H284" class="hw-rt"/><circle cx="64" cy="154" r="7" fill="#fff" stroke="#2563eb" stroke-width="3"/>'
          + '<g class="hw-o7"><path d="M284 44 m0 -2 c-8 -12 8 -12 0 0 z" fill="#dc2626"/><circle cx="284" cy="30" r="8" fill="#dc2626"/><circle cx="284" cy="30" r="3" fill="#fff"/></g>'
          + '<g class="hw-o8"><rect x="96" y="128" width="96" height="22" rx="11" class="hw-bub"/><text x="144" y="143" text-anchor="middle" class="hw-t11w">12분 · 3.1km</text></g>'
          + '<g class="hw-fg"><circle cx="232" cy="120" r="12" class="hw-rip"/><text x="232" y="132" text-anchor="middle" style="font-size:22px">👆</text></g>'
          + '<g class="hw-o9"><rect x="120" y="58" width="190" height="56" rx="10" class="hw-cd"/><text x="215" y="76" text-anchor="middle" class="hw-t10b">이곳을 목적지·경유지로 할까요?</text>'
          + '<rect x="130" y="84" width="82" height="22" rx="7" fill="#2563eb"/><text x="171" y="99" text-anchor="middle" class="hw-t10w">목적지로</text><rect x="218" y="84" width="82" height="22" rx="7" class="hw-b2"/><text x="259" y="99" text-anchor="middle" class="hw-t10b">경유지로</text></g>';
      } },
    { k: 'places', c: 'fd', ic: '🏠', t: '집 · 근무지 · 즐겨찾기 · 최근', tour: -1,
      d: '길 카드의 <b>「더 보기」</b> 안 「이 목적지를 <b>🏠 집으로 · 🚓 근무지로 · ⭐ 즐겨찾기</b>」로 넣어 둔다(즐겨찾기 12곳). 찾아서 간 곳은 🕘 <b>최근 목적지</b>(8곳)로 저절로 남는다.',
      r: '결과 — 다음부터 첫 화면 칩 한 번이면 길이 나온다. 이 기기에만 · ⚙ 「최근 목적지 모두 지우기」.',
      w: { t1: [8, 22], ch: [24, 100], t2: [40, 54], rt: [54, 100], b: [68, 100] }, m: { dr: '0%,54%{stroke-dashoffset:360}70%,100%{stroke-dashoffset:0}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + R(8, 8, 324, 60) + T(18, 26, '길 카드 「더 보기」 — 이 목적지를', 'hw-t10b') + BT(18, 36, 92, '🏠 집으로') + BT(116, 36, 98, '🚓 근무지로') + BT(220, 36, 102, '⭐ 즐겨찾기') + TAP(271, 47, 'w-t1')
          + '<g class="w-ch">' + T(8, 88, '다음부터 첫 화면 칩 한 번', 'hw-t10') + CHIP(8, 94, 60, '🏠 집') + CHIP(72, 94, 80, '🚓 근무지') + CHIP(156, 94, 84, '⭐ 서초역') + CHIP(244, 94, 88, '🕘 방배역') + '</g>' + TAP(38, 107, 'w-t2')
          + '<g class="w-rt"><rect x="0" y="132" width="340" height="9" class="hw-st"/><rect x="0" y="172" width="340" height="9" class="hw-st"/>' + RT('M30 176 H150 V136 H306', 'm-dr') + ST(30, 176) + T(306, 130, '🏠', 'hw-t13', 'm') + '</g>' + BUB(170, 146, 130, '🏠 집까지 18분', 'w-b');
      } },
    { k: 'wp', c: 'fd', ic: '➕', t: '경유지 · 출발점 바꾸기', tour: -1,
      d: '길을 정한 뒤 지도를 두 번 톡 · 길게 눌러 <b>「경유지로」</b>를 고르거나, 찾기 목록에서 <b>＋경유</b>를 누른다. GPS 대신 다른 곳에서 떠나려면 같은 판의 <b>「여기서 떠나기」</b>.',
      r: '결과 — 길 카드에 「경유 1곳 — ○ → ○」와 전체 시간·거리가 나오고, 「경유지 빼기」로 되돌린다.',
      w: { r1: [0, 50], t1: [4, 20], pn: [18, 50], t2: [34, 48], wp: [50, 100], r2: [52, 100], b: [64, 100] },
      svg: function () {
        return MAP() + RT('M40 154 H174 V44 H300', 'w-r1') + RT('M40 154 H284 V44 H300', 'w-r2') + ST(40, 154) + PIN(300, 44) + TAP(240, 154, 'w-t1')
          + '<g class="w-pn">' + R(100, 62, 232, 60) + T(216, 81, '이곳을 목적지·경유지로 할까요?', 'hw-t10b', 'm') + BT(108, 92, 66, '목적지로') + BT(178, 92, 66, '경유지로', 1) + BT(248, 92, 78, '여기서 떠나기') + '</g>' + TAP(211, 103, 'w-t2')
          + '<g class="w-wp"><circle cx="240" cy="154" r="9" fill="#f59e0b" stroke="#fff" stroke-width="2"/>' + T(240, 158, '1', 'hw-t10w', 'm') + '</g>'
          + BUB(16, 164, 308, '경유 1곳 — 반포역 → 서초역 · 전체 18분', 'w-b');
      } },
    { k: 'card', c: 'cd', ic: '🧾', t: '길 카드 읽기 — 출발 전에 한눈에', tour: 0,
      d: '길을 고르면 아래 판이 길 카드가 된다. 위에서부터 <b>도착 시각 · 시간 폭 · 모드 · 신호 · 소통 막대 · 가는 차례</b>. 「가는 차례」를 펴면 꺾는 곳마다 거리·길 이름·신호가 나온다. 🚧 는 길 위 돌발(사고·공사·통제), 이 길의 단속 카메라·어린이보호구역·사고 다발 곳도 같이 적는다.',
      r: '결과 — 「몇 분 사이로 닿나 · 신호 몇 곳 · 어디서 꺾나」를 출발 전에 안다.',
      w: { h1: [0, 20], h2: [20, 40], h3: [40, 60], h4: [60, 80], h5: [80, 100] },
      svg: function () {
        var c = R(6, 4, 328, 152, 'hw-cd', 12) + T(16, 26, '14:32 도착', 'hw-t16') + T(324, 25, '12분 · 3.1km', 'hw-t10b', 'e') + T(16, 44, '10~13분 사이 · 실측 없는 길 30%', 'hw-t10')
          + BT(16, 53, 70, '🚗 일반', 1) + BT(92, 53, 96, '🚨 긴급 출동') + BT(194, 53, 70, '🔒 업무') + T(16, 92, '신호 9곳 · 지금 색을 아는 곳 7', 'hw-t10b')
          + '<rect x="16" y="99" width="134" height="8" rx="4" fill="#16a34a"/><rect x="150" y="99" width="50" height="8" fill="#f59e0b"/><rect x="200" y="99" width="30" height="8" fill="#dc2626"/><rect x="230" y="99" width="94" height="8" rx="4" fill="#94a3b8"/>'
          + [40, 90, 130, 170, 215, 260, 300].map(function (x) { return '<circle cx="' + x + '" cy="103" r="2.2" fill="#fff"/>'; }).join('')
          + T(16, 126, '가는 차례 6곳 · 신호 9곳 ▼', 'hw-t10b') + T(16, 145, '↱ 300m 우회전 · 반포대로 (서초역)', 'hw-t10');
        var H = [[9, 10, 320, 22], [9, 32, 320, 17], [9, 50, 320, 28], [9, 79, 320, 32], [9, 112, 320, 42]], C = ['① 도착 시각 · 걸리는 시간 · 거리', '② 시간 폭 — 실시간 값 없는 길만큼 넓다', '③ 모드 — 🚗 일반 · 🚨 긴급 · 🔒 업무', '④ 신호 수 · 지금 색을 아는 곳 · 소통', '⑤ 가는 차례 — 꺾는 곳·신호를 차례로'];
        return c + H.map(function (h, i) { return '<g class="w-h' + (i + 1) + '"><rect x="' + h[0] + '" y="' + h[1] + '" width="' + h[2] + '" height="' + h[3] + '" rx="7" class="hw-hl"/>' + BUB(10, 162, 320, C[i]) + '</g>'; }).join('');
      } },
    { k: 'alt', c: 'cd', ic: '🔀', t: '다른 길 — 회색 길과 견주기', tour: -1,
      d: '길이 둘 이상이면 지도에 <b>회색 길</b>을 같이 그리고 길 카드에 「다른 길(회색) 14분 · 3.4km · +2분」처럼 견준다. 그 줄을 누르면 그 길로 바꾼다.',
      r: '결과 — 막히는 길 · 신호 많은 길을 피해 고른다.',
      w: { b1: [0, 55], c1: [6, 54], t: [36, 54], b2: [57, 100], c2: [60, 100] },
      svg: function () {
        return MAP() + RT('M40 154 H174 V44 H300', 'hw-rg') + RT('M40 154 H284 V44 H300', 'hw-rg') + RT('M40 154 H174 V44 H300', 'w-b1') + RT('M40 154 H284 V44 H300', 'w-b2') + ST(40, 154) + PIN(300, 44)
          + BUB(40, 70, 260, '다른 길(회색) 14분 · 3.4km · +2분', 'w-c1') + TAP(284, 118, 'w-t') + BUB(70, 70, 200, '회색 길로 바꿈 → 파란 길', 'w-c2');
      } },
    { k: 'sim', c: 'cd', ic: '🎮', t: '모의 주행 — 떠나기 전에 미리', tour: -1,
      d: '길 카드의 <b>모의 주행</b>을 누르면 차가 제한속도로 길을 따라가며 신호에서는 예상대로 선다. 꺾는 곳 · 사다리 말 · 위험 카드를 미리 본다.',
      r: '결과 — 실제 위치가 아니다. 음성은 꺼진 채 시작하고, 보정·기록에 남지 않는다.',
      w: { b: [28, 55] }, m: { car: '0%{transform:translate(0,0)}28%,55%{transform:translate(132px,0)}78%{transform:translate(244px,0)}100%{transform:translate(244px,-110px)}', sg: '0%,55%{fill:#ef4444}56%,100%{fill:#22c55e}' },
      svg: function () {
        return MAP() + RT('M40 154 H284 V44') + '<line x1="182" y1="146" x2="182" y2="163" stroke="#fff" stroke-width="3"/>' + lamp(192, 138, 'm-sg') + PIN(284, 44)
          + '<g class="m-car">' + ME(40, 154) + '</g>' + R(8, 6, 324, 26, 'hw-dk', 13) + T(170, 23, '모의 주행 — 제한속도로 따라간다 · 실제 위치 아님', 'hw-t10w', 'm')
          + BUB(70, 98, 200, '적색 — 예상대로 선다', 'w-b');
      } },
    { k: 'hand', c: 'cd', ic: '📲', t: '다른 앱으로 넘기기', tour: -1,
      d: '긴 길 · 고속도로는 길 카드 「더 보기」의 <b>티맵 · 카카오맵 · 네이버지도</b>로 같은 목적지를 넘긴다. <b>🗺 데이터지도</b>는 그 자리를 데이터 압축지도로 연다.',
      r: '결과 — 가르고가 모르는 먼 길도 이어 간다. 넘긴 앱은 가르고의 신호값을 모른다.',
      w: { t: [8, 24], ar: [24, 100], ph: [40, 100], b: [54, 100] }, m: { dr: '0%,24%{stroke-dashoffset:360}40%,100%{stroke-dashoffset:0}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + R(8, 8, 324, 60) + T(18, 26, '이 목적지를 다른 앱으로', 'hw-t10b') + BT(18, 36, 86, '🗺 데이터지도') + BT(110, 36, 56, '티맵') + BT(172, 36, 72, '카카오맵') + BT(250, 36, 74, '네이버지도') + TAP(138, 47, 'w-t')
          + '<path d="M138 74 C138 120 196 140 236 140" pathLength="360" class="hw-ar w-ar m-dr"/>'
          + '<g class="w-ph">' + R(240, 92, 60, 92, 'hw-dk', 10) + T(270, 128, '티맵', 'hw-t10w', 'm') + T(270, 148, '📍 서초역', 'hw-t9w', 'm') + '</g>' + BUB(10, 150, 220, '같은 목적지로 열린다', 'w-b');
      } },
    { k: 'turn', c: 'gd', ic: '↱', t: '꺾을 곳 · 그다음 · 차로 · 자동 확대', tour: -1,
      d: '안내 중 위 판에 <b>꺾을 곳 · 남은 거리 · 길 이름</b>, 바로 밑 꼬리 칸에 <b>그다음</b> 꺾을 곳. 몇 차로 가운데 어느 차로로 갈지도 보인다(차로 표가 없으면 좌회전·유턴 = 1차로 · 우회전 = 맨 오른쪽). 빠르면 지도를 넓게, 꺾는 곳 250m 안이면 가깝게 저절로 맞춘다.',
      r: '결과 — 손대지 않아도 지도가 알맞게 커지고 줄어든다. 손으로 키우거나 줄이면 15초 쉰다.',
      w: { b: [50, 100] }, m: { zm: '0%,40%{transform:scale(1)}58%,100%{transform:scale(1.35)}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><g class="m-zm"><rect x="150" y="60" width="40" height="140" class="hw-rd"/><rect x="150" y="60" width="200" height="36" class="hw-rd"/>' + RT('M170 200 V78 H350') + ME(170, 160) + '</g>'
          + R(6, 6, 200, 60, 'hw-dk', 12) + '<text x="16" y="50" style="font-size:34px;font-weight:900;fill:#fff">↱</text>' + T(56, 34, '<tspan class="hw-p1">300m</tspan><tspan class="hw-p2" x="56">80m</tspan>', 'hw-t15w') + T(56, 55, '반포대로 우회전', 'hw-t10w')
          + R(6, 70, 118, 26, 'hw-dk2', 9) + T(14, 88, '그다음 ↰ 120m', 'hw-t10w')
          + R(214, 6, 120, 44, 'hw-dk', 10) + ['↑', '↑', '↑', '↱'].map(function (a, i) { return '<text x="' + (232 + i * 26) + '" y="36" text-anchor="middle" style="font-size:18px;font-weight:900;fill:' + (i === 3 ? '#4ade80' : '#64748b') + '">' + a + '</text>'; }).join('')
          + T(274, 64, '맨 오른쪽 차로', 'hw-t9', 'm') + BUB(10, 160, 250, '꺾는 곳 250m 안 — 지도가 가까이', 'w-b');
      } },
    { k: 'eco', c: 'gd', ic: '🚦', t: '신호 사다리 — 경제운전', st: '-7.6s', tour: 0,
      d: '안내 중 위에 <b>바로 앞 · 그다음 · 셋째</b> 신호를 「닿을 때 색」으로 보인다. 녹색이면 「이대로」, 앞이 적색이면 미리 <b>「발 떼기」</b>, 녹색 끝 무렵이면 「서두르지 않기」 — 급제동 없이 굴러가 녹색에 닿는다. 속도를 올리라는 말은 하지 않는다.',
      r: '결과 — 같은 때 도착하는데 위 차는 섰다 다시 출발, 아래 차는 서지 않는다(브레이크·연료·타이어·안전).',
      svg: function () {
        return '<text x="6" y="14" class="hw-t10">보통 운전 — 달렸다 선다</text>' + road(20, 34) + lamp(196, 16, 'hw-sg') + '<line x1="190" y1="20" x2="190" y2="54" class="hw-stop"/>'
          + '<g class="hw-cA"><g transform="translate(8,37)">' + car('#64748b') + '<rect class="hw-brk" x="-3" y="-5" width="4" height="10" rx="1" fill="#ef4444"/></g></g>'
          + '<text x="6" y="80" class="hw-t10">가르고 사다리를 보고 — 미리 발 떼기</text>' + road(86, 34) + lamp(196, 82, 'hw-sg') + '<line x1="190" y1="86" x2="190" y2="120" class="hw-stop"/>'
          + '<g class="hw-cB"><g transform="translate(8,103)">' + car('#2563eb') + '</g></g>'
          + '<g class="hw-o1"><rect x="40" y="132" width="260" height="26" rx="13" class="hw-bub"/><text x="170" y="149" text-anchor="middle" class="hw-t11w">그다음 신호 <tspan fill="#fca5a5">적색</tspan>에 닿음 → 지금 발 떼고 굴러가기</text></g>'
          + '<g class="hw-o2"><rect x="40" y="132" width="260" height="26" rx="13" class="hw-bub"/><text x="170" y="149" text-anchor="middle" class="hw-t11w">녹색에 닿음 → <tspan fill="#86efac">서지 않고 통과</tspan></text></g>'
          + '<g class="hw-o3"><text x="230" y="64" class="hw-t10r">⛔ 섰다 · 다시 출발</text><text x="230" y="130" class="hw-t10g">🍃 한 번도 안 섰다</text></g>'
          + '<g class="hw-o4"><text x="170" y="182" text-anchor="middle" class="hw-t13">🏁 같은 때 도착</text></g>';
      } },
    { k: 'warn', c: 'gd', ic: '📷', t: '단속 카메라 · 어린이보호구역 · 사고 다발', tour: -1,
      d: '길 위의 <b>단속 카메라 · 어린이보호구역 · 사고 다발 교차로</b>에 다가가면 왼쪽 카드(표지 + 남은 거리)와 음성으로 알린다. 일반 · 코드 2 에서 제한속도보다 10km 넘게 5초 달리면 「제한속도 ○○킬로미터 구간입니다」.',
      r: '결과 — 표지를 놓쳐도 미리 안다. 같은 말은 되풀이하지 않는다.',
      w: { a1: [4, 100], a2: [28, 100], a3: [52, 100], v1: [4, 26], v2: [28, 50], v3: [52, 74], v4: [78, 100], s1: [0, 78], s2: [78, 100] },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><rect x="150" y="0" width="60" height="190" class="hw-rd"/><line x1="180" y1="0" x2="180" y2="190" class="hw-ln"/>' + ME(180, 132)
          + '<g class="w-a1">' + R(8, 8, 124, 40) + T(16, 26, '📷 단속 카메라', 'hw-t10b') + T(16, 42, '320m · 제한 50', 'hw-t10') + '</g>'
          + '<g class="w-a2">' + R(8, 54, 124, 40) + T(16, 72, '🏫 어린이보호구역', 'hw-t10b') + T(16, 88, '150m · 제한 30', 'hw-t10') + '</g>'
          + '<g class="w-a3">' + R(8, 100, 124, 40) + T(16, 118, '⚠ 사고 다발 교차로', 'hw-t10b') + T(16, 134, '450m 앞', 'hw-t10') + '</g>'
          + '<circle cx="296" cy="34" r="24" fill="#fff" stroke="#dc2626" stroke-width="5"/><text x="296" y="42" text-anchor="middle" style="font-size:20px;font-weight:900;fill:#0f172a">50</text>'
          + R(266, 66, 60, 38) + T(296, 90, '<tspan class="w-s1">48</tspan><tspan class="w-s2" x="296" style="fill:#dc2626">63</tspan>', 'hw-t16', 'm') + T(296, 100, 'km/h', 'hw-t8', 'm')
          + BUB(126, 160, 208, '🔊 「앞에 단속 카메라가 있습니다」', 'w-v1') + BUB(126, 160, 208, '🔊 「어린이보호구역입니다」', 'w-v2') + BUB(126, 160, 208, '🔊 「앞 사고 다발 교차로」', 'w-v3') + BUB(126, 160, 208, '🔊 「제한속도 50킬로미터 구간입니다」', 'w-v4');
      } },
    { k: 'reroute', c: 'gd', ic: '🔁', t: '길을 벗어나면 · 더 빠른 길', tour: -1,
      d: '길을 벗어나면 「경로를 벗어났습니다. 다시 찾습니다」 하고 지금 자리에서 다시 찾는다. 안내를 시작하고 3분 뒤부터 3분마다 더 빠른 길을 살펴, 뚜렷이 빠르면 말로 알리고 <b>화면 위 단추</b>로 묻는다 — 누르면 바꾸고, 안 누르면 그대로 간다.',
      r: '결과 — 길을 잘못 들어도 멈추지 않는다. 바꿀지는 운전자가 정한다.',
      w: { r1: [0, 55], x: [40, 100], b1: [40, 60], r2: [55, 100], b2: [62, 78], f: [80, 100] }, m: { car: '0%{transform:translate(0,0)}25%{transform:translate(134px,0)}40%,100%{transform:translate(190px,0)}' },
      svg: function () {
        return MAP() + RT('M40 154 H174 V44 H300', 'w-r1') + RT('M230 154 H284 V44 H300', 'w-r2') + PIN(300, 44) + '<g class="m-car">' + ME(40, 154) + '</g>' + T(230, 140, '✕', 'hw-t13r w-x', 'm')
          + BUB(40, 100, 260, '🔊 「경로를 벗어났습니다. 다시 찾습니다」', 'w-b1') + BUB(100, 100, 140, '🔊 「새 경로입니다」', 'w-b2')
          + '<g class="w-f">' + R(30, 6, 280, 28, 'hw-bt', 14) + T(170, 25, '더 빠른 길 · 약 3분 줄어듦 — 누르면 바꿈', 'hw-t10w', 'm') + '</g>';
      } },
    { k: 'tunnel', c: 'gd', ic: '🚇', t: '터널 · 지하차도에서 GPS 가 끊기면', tour: -1,
      d: '터널 · 지하차도 · 고가 밑에서 GPS 가 3초 넘게 안 오면 마지막 속도의 90%(제한속도 안)로 <b>길을 따라 앞으로 어림</b>해 안내를 잇는다. 2분이 넘으면 멈추고, 다시 잡히면 실제 자리로 돌아간다.',
      r: '결과 — 터널 안에서도 꺾을 곳 · 사다리가 끊기지 않는다.',
      w: { g1: [0, 30], g2: [30, 64], g3: [64, 100], b: [30, 64] }, m: { car: '0%{transform:translateX(0)}100%{transform:translateX(300px)}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + road(102, 40) + '<g class="m-car"><g transform="translate(6,122)">' + car('#2563eb') + '</g></g>'
          + '<path d="M118 146 V98 Q180 58 242 98 V146 H232 V102 Q180 72 128 102 V146 Z" class="hw-tn"/><rect x="128" y="102" width="104" height="44" fill="rgba(15,23,42,.45)"/>'
          + T(12, 26, '📡 GPS 잡힘', 'hw-t10g w-g1') + T(12, 26, '📡✕ 끊김 — 길 따라 어림 중', 'hw-t10r w-g2') + T(12, 26, '📡 다시 잡힘 — 실제 자리로', 'hw-t10g w-g3')
          + BUB2(10, 150, 320, '🔊 「위치 신호가 약합니다.', '경로를 따라 계속 안내합니다」', 'w-b');
      } },
    { k: 'arrive', c: 'gd', ic: '🏁', t: '도착 — 길 어느 쪽인지까지', tour: -1,
      d: '목적지 가까이 오면 <b>길 오른쪽 · 왼쪽</b> 어디인지까지 말하고 안내를 마친다.',
      r: '결과 — 끝까지 마친 일반 주행은 걸린 시간이 ⚙ 「보정 · 기록」에 숫자로만 쌓인다.',
      w: { b: [56, 100], c: [72, 100] }, m: { car: '0%{transform:translateX(0)}56%,100%{transform:translateX(206px)}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + road(66, 40) + '<g class="m-car"><g transform="translate(6,86)">' + car('#2563eb') + '</g></g>'
          + R(232, 114, 66, 42, 'hw-cd', 6) + T(265, 142, '🏢', 'hw-t13', 'm') + PIN(265, 118)
          + BUB2(10, 8, 320, '🔊 「목적지 부근입니다. 목적지는', '오른쪽입니다. 안내를 마칩니다」', 'w-b') + T(12, 180, '끝까지 마친 일반 주행 → 보정에 쌓임', 'hw-t10 w-c');
      } },
    { k: 'em', c: 'pc', ic: '🚨', t: '긴급 출동 — 경찰차는 다르게', st: '-4.9s', tour: 1,
      d: '길 카드에서 🚨 긴급 출동을 고르면 길 셈에서 <b>신호 기다림을 뺀다</b>(코드 0·1 · 소방). 그 대신 닿을 때 적색인 교차로를 <b>「적색 진입 · 좌우」</b>로 미리 알리고, 음성 안내를 켰으면 말로도 알린다. 지도에 버스전용차로를 점선으로 그린다.',
      r: '결과 — 어디서 적색에 들어가는지 미리 알고 서행 · 좌우 확인 준비. 통과는 운전자 판단.',
      svg: function () {
        return card(4, 106, 'g', '바로 앞', '6초', '통과') + card(117, 106, 'r', '그다음', '24초', '적색 진입 · 좌우') + card(230, 106, 'g', '셋째', '15초', '통과')
          + road(86, 46) + '<line x1="0" y1="127" x2="340" y2="127" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="7 5" opacity=".8"/>'
          + lamp(118, 82, 'hw-gn') + lamp(232, 82, 'hw-rdl')
          + '<g class="hw-eye"><path d="M222 92 q-14 -12 -26 -8" class="hw-ey"/><path d="M222 128 q-14 12 -26 8" class="hw-ey"/><text x="150" y="80" class="hw-t10b">👀 좌</text><text x="150" y="148" class="hw-t10b">👀 우</text></g>'
          + '<g class="hw-cE"><g transform="translate(6,106)">' + car('#f8fafc', 1) + '<rect x="0" y="-7" width="30" height="14" rx="4" fill="none" stroke="#94a3b8"/></g></g>'
          + '<g class="hw-o5"><rect x="56" y="154" width="228" height="24" rx="12" class="hw-bub"/><text x="170" y="170" text-anchor="middle" class="hw-t11w">🔊 「적색 교차로입니다. 좌우 확인」</text></g>'
          + '<text x="334" y="148" text-anchor="end" class="hw-t10" style="fill:#3b82f6">┅ 버스전용차로</text>';
      } },
    { k: 'codes', c: 'pc', ic: '🔢', t: '코드 0·1 · 코드 2 · 소방 — 갈래마다', tour: 1,
      d: '🚨 긴급 출동을 고르면 <b>코드 0·1 · 코드 2 · 소방</b> 단추가 나온다. 코드 0·1 = 빨리 가야 하는 출동(신호 기다림을 빼고 셈). 코드 2 = 신속히 가되 <b>신호·제한속도는 지킨다</b>(적색 통과·버스전용차로 안내 없음). 소방 = 큰 차(신호 기다림은 빼고 · 골목·유턴은 두 배 불리하게 · 높이·폭 제한 자료는 없다).',
      r: '결과 — 같은 목적지라도 갈래마다 길과 말이 달라진다. 「안내를 시작합니다. 코드 2 출동. 신호를 지킵니다」.',
      w: { h1: [2, 34], h2: [34, 66], h3: [66, 100] },
      svg: function () {
        var C = [['코드 0·1', '#dc2626', ['빼고 셈', '적색 진입 · 좌우', '점선 표시', '보통']], ['코드 2', '#f59e0b', ['넣고 셈', '없음 — 신호 지킴', '안내 없음', '보통']], ['소방', '#ea580c', ['빼고 셈', '적색 진입 · 좌우', '점선 표시', '두 배 불리']]],
          L = ['신호 기다림', '적색 교차로 알림', '버스전용차로', '골목 · 유턴'], h = '';
        C.forEach(function (c, i) { var x = 6 + i * 112; h += R(x, 4, 104, 182, 'hw-cd', 10) + '<rect x="' + x + '" y="4" width="104" height="5" rx="2" fill="' + c[1] + '"/>' + T(x + 52, 28, c[0], 'hw-t13', 'm');
          c[2].forEach(function (v, j) { h += T(x + 8, 50 + j * 34, L[j], 'hw-t9') + T(x + 8, 64 + j * 34, v, 'hw-t10b'); });
          h += '<rect x="' + (x - 2) + '" y="2" width="108" height="186" rx="11" class="hw-hl w-h' + (i + 1) + '"/>'; });
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + h;
      } },
    { k: 'disp', c: 'pc', ic: '🚓', t: '여러 순찰차 — 누가 먼저 닿나', tour: -1,
      d: '길 카드 <b>「더 보기 — 순찰차 비교」</b>. 지도를 옮겨 순찰차 자리를 가운데 두고 <b>＋ 지도 가운데</b>(최대 6대), 또는 <b>＋ 내 자리</b>. 누가 먼저 닿는지 차례와 예상 폭을 셈하고, <b>📻 「…」 복사</b>로 무전할 말을 만든다.',
      r: '결과 — 참고용 예측이다. 지령·판단은 사람이 한다. 🔒 업무에서는 안 나온다.',
      w: { t: [2, 34], c1: [8, 100], c2: [18, 100], c3: [28, 100], ln: [36, 100], pn: [54, 100] }, m: { dr: '0%,36%{stroke-dashoffset:360}52%,100%{stroke-dashoffset:0}' },
      svg: function () {
        var P = [[40, 44], [296, 40], [300, 156]], h = MAP() + BT(222, 6, 112, '＋ 지도 가운데', 1) + TAP(278, 17, 'w-t') + PIN(230, 112);
        P.forEach(function (p, i) { h += '<path d="M' + p[0] + ' ' + p[1] + ' L230 100" pathLength="360" class="hw-ar w-ln m-dr"/><g class="w-c' + (i + 1) + '"><g transform="translate(' + (p[0] - 15) + ',' + p[1] + ')">' + car('#f8fafc', 1) + '<rect x="0" y="-7" width="30" height="14" rx="4" fill="none" stroke="#94a3b8"/></g>' + T(p[0], p[1] + 22, '순찰 ' + (i + 1), 'hw-t9', 'm') + '</g>'; });
        return h + '<g class="w-pn">' + R(8, 96, 186, 90) + T(18, 114, '1. 순찰 3 — 먼저', 'hw-t10b') + T(18, 132, '2. 순찰 2', 'hw-t10') + T(18, 150, '3. 순찰 1', 'hw-t10') + BT(16, 158, 170, '📻 「…」 복사', 1) + '</g>';
      } },
    { k: 'sr', c: 'pc', ic: '🚇', t: '열차 안 신고 — 열차보다 먼저 닿을 역', tour: 6,
      d: '목적지가 없을 때 아래 판의 <b>🚇 열차 안 신고</b>(⚙ 에도 있다). 노선과 열차가 떠난 때(방금 · 30초 전 · 1분 전…)를 고르면 <b>열차보다 먼저 닿을 역 · 선착 확률 · 출발을 미룰 수 있는 시간</b>을 시간표로 셈한다. 「이 역으로 안내」로 바로 길을 연다.',
      r: '결과 — 후보·예상이다. 최종 판단은 현장 경찰관. 하차 인파가 많은 때는 출구·개찰구 쪽 배치를 권한다.',
      w: { cp: [0, 62], t: [6, 20], s: [16, 62], hi: [50, 100], g: [66, 100], b: [56, 100] }, m: { tr: '0%{transform:translateX(0)}100%{transform:translateX(150px)}', pc: '0%{transform:translateX(0)}60%,100%{transform:translateX(168px)}' },
      svg: function () {
        var S = [[50, '교대'], [130, '서초'], [210, '방배'], [290, '사당']], h = '<rect x="0" y="0" width="340" height="190" class="hw-map"/>';
        h += '<g class="w-cp">' + T(8, 23, '열차가 떠났다', 'hw-t10b') + CHIP(96, 8, 56, '방금') + CHIP(158, 8, 76, '30초 전') + CHIP(240, 8, 72, '1분 전') + '<rect x="158" y="8" width="76" height="26" rx="13" class="hw-hl w-s"/></g>' + TAP(196, 21, 'w-t');
        h += '<g class="w-g">' + BT(186, 10, 146, '🚓 이 역으로 안내', 1) + '</g>';
        h += '<rect x="20" y="62" width="300" height="6" rx="3" fill="#16a34a"/>' + S.map(function (s) { return '<circle cx="' + s[0] + '" cy="65" r="7" fill="#fff" stroke="#16a34a" stroke-width="3"/>' + T(s[0], 90, s[1], 'hw-t10b', 'm'); }).join('');
        h += '<circle cx="210" cy="65" r="13" fill="none" stroke="#f59e0b" stroke-width="3" class="w-hi"/><g class="m-tr"><rect x="34" y="48" width="34" height="12" rx="4" fill="#0f172a"/><rect x="38" y="51" width="7" height="5" fill="#fde68a"/><rect x="49" y="51" width="7" height="5" fill="#fde68a"/></g>';
        h += '<rect x="0" y="104" width="340" height="26" class="hw-rd"/><g class="m-pc"><g transform="translate(26,117)">' + car('#f8fafc', 1) + '<rect x="0" y="-7" width="30" height="14" rx="4" fill="none" stroke="#94a3b8"/></g></g>';
        return h + BUB2(10, 144, 320, '열차보다 먼저 닿을 역 — 방배', '선착 확률 · 출발을 미룰 수 있는 시간', 'w-b');
      } },
    { k: 'meas', c: 'pc', ic: '⏱', t: '역 실측 — 스톱워치로 재 두기', tour: -1,
      d: '⚙ 의 <b>🚇 역 실측 열기</b>(따로 열리는 화면). 순찰차 세운 자리 → 출입구, 출입구 → 승강장을 스톱워치로 잰다. 이 기기에만 남고 JSON 으로 내보낸다.',
      r: '결과 — 같은 구간을 3번 넘게 재면 열차 안 신고의 도착 예측이 가정값 대신 잰 값을 쓴다.',
      w: { l1: [46, 100], l2: [90, 100] }, m: { wk: '0%{transform:translate(0,0)}46%{transform:translate(130px,0)}90%,100%{transform:translate(260px,-90px)}', hd: '0%{transform:rotate(0)}100%{transform:rotate(360deg)}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><path d="M40 150 H170 L300 60" class="hw-al"/>'
          + '<g transform="translate(25,150)">' + car('#f8fafc', 1) + '</g>' + T(40, 174, '🚓 세운 자리', 'hw-t9', 'm') + T(170, 140, '🚇', 'hw-t13', 'm') + T(170, 174, '출입구', 'hw-t9', 'm') + R(270, 48, 60, 24, 'hw-dk', 6) + T(300, 64, '승강장', 'hw-t10w', 'm')
          + '<g class="m-wk"><circle cx="40" cy="150" r="7" fill="#f59e0b" stroke="#fff" stroke-width="2"/></g>'
          + '<circle cx="46" cy="48" r="30" class="hw-cd" style="stroke-width:3"/><line x1="46" y1="48" x2="46" y2="26" stroke="#dc2626" stroke-width="3" stroke-linecap="round" class="m-hd"/><circle cx="46" cy="48" r="3" fill="#dc2626"/>'
          + T(90, 38, '출입구까지 1:12', 'hw-t11b w-l1') + T(90, 58, '승강장까지 0:48', 'hw-t11b w-l2') + T(90, 84, '3번 넘게 잰 값 → 가정값 대신', 'hw-t10');
      } },
    { k: 'vtime', c: 'pc', ic: '⏳', t: '업무 주행시간 — 설정 값이 하는 일', tour: -1,
      d: '⚙ <b>주행시간(업무 · 신고차량 예측)</b> 값은 🔒 업무와 데이터 압축지도의 주행시간 셈에 쓴다. 업무는 신호를 빼고 <b>업무 기본 속도</b>와 <b>가장 이른 도착 기준</b> 두 가지로 셈하고, 꺾을 때마다 · 진출입로마다 · 출발·정지마다 초를 더하며, 터널·지하차도는 배율로 늦춘다. 「직접 입력 — 가장 느린·빠른」은 속도를 손으로 넣을 때 받는 범위, 「도주 차량 속도 배율」은 데이터지도의 신고 차량 예측에 쓴다.',
      r: '결과 — 「기본 · 가장 이르면」 두 시간이 나온다. 바꾼 값 옆 ↺ 기본으로 되돌린다.',
      w: { a: [6, 100], b: [20, 100], c: [34, 100], d: [48, 100], e: [62, 100], f: [78, 100] },
      svg: function () {
        var L = [['b', '#f59e0b', '＋ 회전 감속 — 초 × 꺾는 번'], ['c', '#a855f7', '＋ 진출입로 감속 — 초 × 번'], ['d', '#ec4899', '＋ 출발·정지 가감속 — 초 × 번'], ['e', '#64748b', '× 터널·지하차도 속도 배율']], X = [[170, 34], [204, 26], [230, 24], [254, 22]], h = '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + T(10, 22, '업무 — 업무 기본 속도로 달리는 시간', 'hw-t10b');
        h += '<g class="w-a"><rect x="10" y="30" width="160" height="22" rx="4" fill="#2563eb"/>' + T(90, 45, '달리기(신호는 안 셈)', 'hw-t10w', 'm') + '</g>';
        L.forEach(function (l, i) { h += '<g class="w-' + l[0] + '"><rect x="' + X[i][0] + '" y="30" width="' + X[i][1] + '" height="22" fill="' + l[1] + '"/><rect x="10" y="' + (64 + i * 20) + '" width="10" height="10" rx="2" fill="' + l[1] + '"/>' + T(26, 73 + i * 20, l[2], 'hw-t10') + '</g>'; });
        return h + '<g class="w-f">' + T(10, 160, '가장 이른 도착 — 기준 속도로 같은 셈', 'hw-t10b') + '<rect x="10" y="166" width="120" height="18" rx="4" fill="#16a34a"/><rect x="130" y="166" width="70" height="18" fill="#94a3b8"/>' + T(208, 180, '→ 두 시간', 'hw-t10b') + '</g>';
      } },
    { k: 'cruise', c: 'cr', ic: '▶', t: '켜놓고 다니기 — 목적지 없이', st: '-3s', tour: 3,
      d: '목적지를 안 정하고 <b>▶ 켜놓고 다니기</b>를 누르면, 달리는 길의 이름 · 지금 소통 · 제한속도 · <b>앞 신호의 지금 색과 남은 초</b>를 계속 보인다. 움직일 때는 「지금 속도(제한속도 안)로 닿으면 녹색 · 적색」도 붙는다(밤에는 안 보임). ⚙ <b>사거리 표시 — 앞 · 뒤</b>로 지도에 보일 범위(앞 1~3km · 뒤 500m~1.5km)를 정한다.',
      r: '결과 — 화면을 안 만져도 앞 신호와 이 길 사정이 늘 위에 떠 있다. 제한속도를 넘으면 숫자가 붉어진다. 그만은 「끝」.',
      svg: function () {
        var g = '<rect x="0" y="0" width="340" height="190" class="hw-map"/><g class="hw-scr">';
        for (var i = -2; i < 6; i++) g += '<rect x="166" y="' + (i * 40) + '" width="8" height="22" fill="#fff" opacity=".9"/>';
        g += '</g>';
        return '<defs><clipPath id="hwc4"><rect x="0" y="0" width="340" height="190"/></clipPath></defs><g clip-path="url(#hwc4)">' + g.replace('<g class="hw-scr">', '<rect x="130" y="0" width="80" height="190" class="hw-rd"/><g class="hw-scr">') + '</g>'
          + '<g transform="translate(155,150) rotate(-90)">' + car('#2563eb') + '</g>'
          + '<rect x="8" y="8" width="214" height="52" rx="12" class="hw-dk"/><text x="22" y="40" style="font-size:22px;fill:#fff">⬆</text><text x="48" y="31" class="hw-t15w">반포대로</text><text x="48" y="50" class="hw-t10w">이 길 지금 — <tspan fill="#86efac" font-weight="900">원활</tspan> · 시속 42km쯤</text>'
          + '<g><rect x="8" y="68" width="150" height="34" rx="10" class="hw-cd"/><circle cx="26" cy="85" r="8" class="hw-sg2"/><text x="40" y="90" class="hw-t11b"><tspan class="hw-p1">앞 신호 녹색 18초</tspan><tspan class="hw-p2" x="40">앞 신호 적색 32초</tspan></text></g>'
          + '<circle cx="300" cy="40" r="26" fill="#fff" stroke="#dc2626" stroke-width="6"/><text x="300" y="48" text-anchor="middle" style="font-size:22px;font-weight:900;fill:#0f172a">50</text>'
          + '<rect x="270" y="74" width="60" height="38" rx="10" class="hw-cd"/><text x="300" y="98" text-anchor="middle" class="hw-t16"><tspan class="hw-p1">42</tspan><tspan class="hw-p2" x="300" fill="#dc2626">53</tspan></text><text x="300" y="108" text-anchor="middle" class="hw-t8">km/h</text>';
      } },
    { k: 'layer', c: 'cr', ic: '🗺', t: '신호 · 소통 층 — 신호 점을 눌러 보기', tour: 3,
      d: '지도 위 <b>🚦 신호 · 🚗 소통</b> 단추로 층을 켜고 끈다. 신호 점을 누르면 그 교차로의 방향별 지금 색 · 남은 초가 뜨고 <b>「여기로 안내」</b>로 바로 길을 정한다. 값이 없는 교차로는 「자료가 없다 — 눈으로 본다」라고 그대로 말한다.',
      r: '결과 — 출발 전에 둘레 신호·막힘을 본다. 신호값은 계획값이라 수동 조작·감응 신호면 다르다.',
      w: { off: [28, 50], t: [54, 66], pp: [66, 100] }, m: { tf: '0%,28%{opacity:1}31%,48%{opacity:0}51%,100%{opacity:1}' },
      svg: function () {
        var h = MAP() + '<g class="m-tf"><rect x="0" y="40" width="170" height="9" fill="#16a34a"/><rect x="170" y="40" width="170" height="9" fill="#f59e0b"/><rect x="0" y="95" width="120" height="9" fill="#dc2626"/><rect x="120" y="95" width="220" height="9" fill="#16a34a"/><rect x="170" y="0" width="9" height="190" fill="#f59e0b" opacity=".9"/><rect x="0" y="150" width="340" height="9" fill="#16a34a"/></g>';
        [[64, 44, 'g'], [174, 44, 'r'], [284, 44, 'g'], [64, 99, 'r'], [174, 99, 'g'], [284, 99, 'g'], [64, 154, 'g'], [174, 154, 'r'], [284, 154, 'g']].forEach(function (p) { h += '<circle cx="' + p[0] + '" cy="' + p[1] + '" r="6" fill="' + (p[2] === 'g' ? '#22c55e' : '#ef4444') + '" stroke="#fff" stroke-width="2"/>'; });
        return h + BT(196, 6, 66, '🚦 신호', 1) + BT(266, 6, 66, '🚗 소통', 1) + '<g class="w-off">' + BT(266, 6, 66, '🚗 소통') + '</g>' + TAP(176, 99, 'w-t')
          + '<g class="w-pp">' + R(150, 112, 182, 72) + T(160, 130, '🚦 서초역 사거리', 'hw-t10b') + T(160, 148, '남→북 직진 녹색 18초', 'hw-t10g') + BT(160, 156, 82, '여기로 안내', 1) + BT(248, 156, 76, '닫기') + '</g>';
      } },
    { k: 'man', c: 'cr', ic: '✍', t: '값 없는 신호에 주기 넣기', tour: -1,
      d: '길 카드 「가는 차례」에서 신호값이 없는 교차로 옆 <b>✍ 주기 넣기</b>. 교통과에서 받은 주기를 넣으면 그 신호를 평균 기다림으로 셈한다(지금 색은 모르므로 남은 초는 안 보인다). 받은 신호값이 있는 곳에는 이 단추가 안 나온다.',
      r: '결과 — 값 없는 곳 때문에 틀어지던 시간이 맞아진다. 이 기기에만 · ⚙ 「✍ 직접 넣은 신호 주기 — 모두 지우기」.',
      w: { t: [6, 20], in: [20, 58], a: [0, 58], b: [58, 100], bb: [62, 100] }, m: { ty: '0%,26%{opacity:0}30%,100%{opacity:1}' },
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + R(8, 8, 324, 92) + T(18, 26, '가는 차례', 'hw-t10b') + T(18, 46, '🚦 서초역 — 녹색 18초', 'hw-t10')
          + '<g class="w-a">' + T(18, 68, '🚦 ○○사거리 — 값 없음', 'hw-t10') + BT(236, 54, 88, '✍ 주기 넣기') + '</g><g class="w-b">' + T(18, 68, '🚦 ○○사거리 — 평균 기다림으로 셈', 'hw-t10b') + BT(236, 54, 88, '✍ 고치기') + '</g>'
          + T(18, 90, '↱ 300m 우회전 · 반포대로', 'hw-t10') + TAP(280, 65, 'w-t')
          + '<g class="w-in">' + R(40, 108, 260, 46) + T(52, 135, '주기(초)', 'hw-t10b') + R(110, 119, 90, 24, 'hw-b2', 6) + T(122, 136, '<tspan class="m-ty">120</tspan>', 'hw-t11b') + BT(210, 120, 80, '넣기', 1) + '</g>'
          + BUB(20, 160, 300, '남은 초는 안 보인다 · 이 기기에만', 'w-bb');
      } },
    { k: 'tilt', c: 'cr', ic: '🛣', t: '안내 중 지도 시점 — 기울임 · 평면', tour: -1,
      d: '⚙ <b>🛣 안내 중 지도 시점</b> — <b>기울임</b>(앞길을 멀리 · 폰 화면) 또는 <b>평면</b>(위에서 내려다봄). 지도는 한 손가락으로 끌고, 두 손가락으로 키우고, <b>◎</b> 로 내 자리로 돌아온다.',
      r: '결과 — 기울여도 길 이름 · 신호 점 글자는 눕지 않고 바로 선다.',
      w: { b: [62, 100] }, m: { tl: '0%,40%{transform:scaleY(1)}60%,100%{transform:scaleY(.58)}' },
      svg: function () {
        var g = '<g class="m-tl"><rect x="0" y="-110" width="340" height="300" class="hw-map"/>';
        [-70, -15, 40, 95, 150].forEach(function (y) { g += '<rect x="0" y="' + y + '" width="340" height="9" class="hw-st"/>'; });
        [60, 170, 280].forEach(function (x) { g += '<rect x="' + x + '" y="-110" width="9" height="300" class="hw-st"/>'; });
        g += RT('M174 190 V-110') + ME(174, 160) + '</g>';
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + g + R(8, 6, 208, 26, 'hw-dk', 13) + T(112, 23, '<tspan class="hw-p1">평면 — 위에서 내려다봄</tspan><tspan class="hw-p2" x="112">기울임 — 앞길을 멀리</tspan>', 'hw-t10w', 'm')
          + T(214, 100, '반포대로', 'hw-t11b') + BUB(110, 160, 224, '글자 · 신호 점은 눕지 않는다', 'w-b');
      } },
    { k: 'night', c: 'sc', ic: '🌙', t: '밤 · 글씨 크기', st: '-7.6s', tour: 4,
      d: '밤 22~06시에는 <b>속도 말 없이 색만</b> 보인다 — 과속을 막으려고 일부러 끊어 둔 신호를 거스르지 않는다. <b>◐</b> 로 밤 화면, ⚙ <b>기본 글씨 크기</b>를 작게 ×0.9 ~ 아주 크게 ×1.3 으로.',
      r: '결과 — 밤에는 「이대로 · 발 떼기」가 「녹색 · 적색」으로만 남는다. 글씨를 키우면 사다리 · 도착 시각 · 이 안내까지 같이 커진다.',
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-sky"/><text x="292" y="40" class="hw-sun" style="font-size:28px">☀</text><text x="292" y="40" class="hw-moon" style="font-size:26px">🌙</text>'
          + '<g class="hw-p1">' + card(4, 90, 'g', '바로 앞', '12초', '이대로') + card(100, 90, 'r', '그다음', '25초', '발 떼기') + '</g>'
          + '<g class="hw-p2">' + card(4, 90, 'g', '바로 앞', '12초', '녹색') + card(100, 90, 'r', '그다음', '25초', '적색') + '</g>'
          + '<g class="hw-o2"><rect x="4" y="64" width="250" height="24" rx="12" class="hw-bub"/><text x="129" y="80" text-anchor="middle" class="hw-t11w">밤 22~06시 — 속도 말 없이 색만</text></g>'
          + R(40, 116, 290, 62, 'hw-cd', 12) + '<g transform="translate(60,150)"><text class="hw-fz" x="0" y="0" style="font-size:26px;font-weight:900">가 12분</text></g><text x="200" y="146" class="hw-t11b"><tspan class="hw-p1">글씨 ×1</tspan><tspan class="hw-p2" x="200">글씨 ×1.3</tspan></text><text x="200" y="164" class="hw-t10">⚙ 설정 › 글씨 크기</text>';
      } },
    { k: 'voice', c: 'sc', ic: '🔊', t: '음성 안내 · 빠르기 · 남은 초 글씨', tour: 4,
      d: '<b>🔊</b> 를 누르면 「음성 안내를 켭니다」 — 꺾을 곳 · 적색 교차로 · 카메라 · 보호구역 · 도착 예정 시각을 말한다. ⚙ <b>음성 빠르기</b>(느리게 · 보통 · 빠르게 · 아주 빠르게), ⚙ <b>진행방향 남은 초 글씨</b>로 앞 신호 남은 초 숫자를 ×1 ~ ×3 으로 키운다.',
      r: '결과 — 화면을 안 봐도 귀로, 봐야 할 때는 숫자가 크게.',
      w: { t: [4, 16], b: [14, 40], h1: [40, 55], h2: [55, 70], h3: [70, 85], h4: [85, 100] }, m: { big: '0%,40%{transform:scale(1)}70%,100%{transform:scale(2)}' },
      svg: function () {
        var O = [[10, 60, '느리게'], [74, 52, '보통'], [130, 60, '빠르게'], [194, 84, '아주 빠르게']];
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><circle cx="34" cy="32" r="22" class="hw-cd"/>' + '<text x="34" y="40" text-anchor="middle" style="font-size:20px">🔊</text>' + TAP(36, 34, 'w-t') + BUB(66, 20, 190, '🔊 「음성 안내를 켭니다」', 'w-b')
          + T(10, 88, '⚙ 음성 빠르기', 'hw-t10b') + O.map(function (o, i) { return CHIP(o[0], 94, o[1], o[2]) + '<rect x="' + o[0] + '" y="94" width="' + o[1] + '" height="26" rx="13" class="hw-hl w-h' + (i + 1) + '"/>'; }).join('')
          + T(10, 150, '⚙ 진행방향 남은 초 글씨', 'hw-t10b') + T(10, 168, '×1 → ×3', 'hw-t10')
          + '<g class="m-big">' + T(250, 180, '<tspan style="fill:#16a34a">녹색</tspan> 18<tspan style="font-size:10px">초</tspan>', 'hw-t16', 'm') + '</g>';
      } },
    { k: 'speedo', c: 'sc', ic: '✈', t: '이동 속도 — 비행기 · 기차 · 배', tour: 5,
      d: '🚦 신호 · 🚗 소통 옆 <b>✈ 속도</b>. 통신 없이 폰 GPS 만으로 <b>지금 속도 · 고도 · 방향</b>과 지금 위 나라 · 가까운 도시를 보인다. 비행기 모드에서도 위치 서비스는 켜 둔다.',
      r: '결과 — 받은 위치는 저장하지 않는다(닫으면 사라진다). 창가에서 처음 위성을 잡는 데 몇 분 걸릴 수 있다.',
      m: { pl: '0%{transform:translate(0,0)}100%{transform:translate(110px,-20px)}' },
      svg: function () {
        return R(0, 0, 340, 190, 'hw-dk', 0) + T(16, 28, '이동 속도 — 비행기 · 기차 · 배', 'hw-t11w') + '<text x="16" y="92" class="hw-sp"><tspan class="hw-p1">812</tspan><tspan class="hw-p2" x="16">835</tspan></text>' + T(128, 92, 'km/h', 'hw-t11w')
          + T(16, 122, '고도 10,900m · 방향 남동', 'hw-t10w') + T(16, 142, '지금 위 — 나라 · 가까운 도시', 'hw-t10w') + T(16, 178, '통신 없이 GPS 만 · 저장 안 함', 'hw-t9w')
          + '<g class="m-pl"><text x="210" y="72" style="font-size:30px">✈</text></g>';
      } },
    { k: 'cal', c: 'rc', ic: '📈', t: '실측 보정 · 도착 기록 · 막힘 배율', tour: -1,
      d: '안내를 끝까지 마친 일반 주행마다 <b>「걸린 시간 ÷ 계산」</b>을 숫자로만 쌓아 실측 보정(×1.08 같은)을 만든다. ⏱ <b>예상·실제 도착 기록</b>은 예상 폭 안에 든 비율을 보이고 📤 내보낸다(좌표·목적지 없음). 실시간 소통이 없을 때는 ITS 실측 <b>막힘 배율</b>(요일 · 시간대)을 쓴다 — ⚙ 에서 끈다.',
      r: '결과 — 쓸수록 이 기기의 도착 예측이 내 운전에 맞는다. 업무 · 모의 주행은 쌓지 않는다.',
      w: { d1: [4, 100], d2: [14, 100], d3: [24, 100], d4: [34, 100], d5: [44, 100], d6: [54, 100], d7: [64, 100], md: [74, 100], f: [80, 100] },
      svg: function () {
        var D = [[40, 86], [74, 98], [108, 90], [142, 80], [176, 94], [210, 88], [244, 92]], h = '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + T(10, 22, '끝까지 마친 일반 주행 — 걸린 시간 ÷ 계산', 'hw-t10b')
          + '<line x1="20" y1="100" x2="290" y2="100" stroke="#94a3b8" stroke-dasharray="4 4"/>' + T(296, 104, '×1.00', 'hw-t9');
        D.forEach(function (d, i) { h += '<circle cx="' + d[0] + '" cy="' + d[1] + '" r="6" fill="#2563eb" class="w-d' + (i + 1) + '"/>'; });
        return h + '<g class="w-md"><line x1="20" y1="90" x2="290" y2="90" stroke="#16a34a" stroke-width="3"/>' + T(296, 86, '×1.08', 'hw-t10g') + '</g>'
          + '<g class="w-f">' + T(10, 150, '⏱ 예상 폭 안에 든 것 6/7 · 📤 내보내기', 'hw-t10b') + T(10, 172, '실시간 소통 없으면 — 요일·시간대 막힘 배율', 'hw-t10') + '</g>';
      } },
    { k: 'learn', c: 'rc', ic: '🧠', t: '다녀 본 길 기억 · 주행 기록', tour: -1,
      d: '⚙ <b>🧠 다녀 본 길 기억</b>(처음부터 켬)은 안내 중 · 켜놓고 다니기 중 실제로 지난 길 줄의 걸린 시간을 요일 · 시간대마다 모아, 같은 줄을 두 번 넘게 지나면 실시간 값 다음으로 쓴다(골목 지름길). ⚙ <b>🛰 주행 기록</b>을 켜면 안내 중 자리를 2초마다 남기고(최근 10번) 📤 파일로 예측과 실제를 맞대 본다.',
      r: '결과 — 내가 아는 지름길을 길 찾기가 배운다. 모두 이 기기에만 · 업무 · 모의 주행은 안 남긴다.',
      w: { n1: [0, 26], n2: [26, 50], n3: [50, 100], r1: [0, 70], r2: [70, 100], b: [72, 100] },
      svg: function () {
        return MAP() + '<path d="M40 154 Q120 150 150 100 T284 44" class="hw-al"/>' + RT('M40 154 H284 V44', 'w-r1') + RT('M40 154 Q120 150 150 100 T284 44', 'w-r2') + ST(40, 154) + PIN(284, 44)
          + R(8, 6, 170, 26, 'hw-dk', 13) + T(93, 23, '<tspan class="w-n1">이 골목 지난 횟수 1</tspan><tspan class="w-n2" x="93">이 골목 지난 횟수 2</tspan><tspan class="w-n3" x="93">이 골목 지난 횟수 3</tspan>', 'hw-t10w', 'm')
          + BUB(10, 162, 206, '🧠 다녀 본 길 — 지름길로 고름', 'w-b') + T(330, 182, '🛰 주행 기록 📤', 'hw-t10b', 'e');
      } },
    { k: 'mine', c: 'rc', ic: '🔐', t: '이 기기에만 · 지우기 · 기본값', tour: -1,
      d: '설정 · 보정 · 기록 · 즐겨찾기 · 넣은 신호는 모두 <b>이 기기에만</b> 있고 앱을 새로 받아도 남는다. 항목마다 🗑 지우기, 바꾼 값 옆 <b>↺ 기본</b>, 맨 아래 <b>전체 기본값으로</b>. 밖으로 나가는 것은 주소를 찾을 때의 그 글(브이월드)뿐이다.',
      r: '결과 — 다른 사람과 나누지 않는다. 기기를 바꾸면 처음부터 다시 쌓인다.',
      w: { a: [6, 100], b: [16, 100], c: [26, 100], d: [36, 100], e: [46, 100], f: [56, 100], bt: [70, 100] },
      svg: function () {
        var I = [['a', 20, 40, '⚙ 설정'], ['b', 20, 80, '📈 보정'], ['c', 20, 120, '🛰 주행 기록'], ['d', 226, 40, '🧠 다녀 본 길'], ['e', 226, 80, '⭐ 즐겨찾기'], ['f', 226, 120, '✍ 넣은 신호']];
        return '<rect x="0" y="0" width="340" height="190" class="hw-map"/>' + R(130, 14, 80, 136, 'hw-dk', 14) + '<text x="170" y="94" text-anchor="middle" style="font-size:30px">🔐</text>' + T(170, 136, '이 기기', 'hw-t10w', 'm')
          + I.map(function (i) { return T(i[1], i[2], i[3], 'hw-t10b w-' + i[0]); }).join('')
          + '<g class="w-bt">' + BT(14, 160, 92, '🗑 지우기') + BT(112, 160, 92, '↺ 기본') + BT(210, 160, 118, '전체 기본값으로', 1) + '</g>';
      } }
  ];
  if (VIP) SC.splice(SC.map(function (s) { return s.k; }).indexOf('vtime'), 0, { k: 'vip', c: 'pc', ic: '🔒', t: '업무 — 남기지 않는다', st: '-7.6s', tour: 1,
    d: '길 카드에서 🔒 업무를 고르면 <b>이 기기 안 이름 · 도로명 번호로만</b> 찾고, 경로 · 지점 · 시각을 <b>저장하지 않는다</b>. 최근 목적지 · 주행 기록 · 다녀 본 길에도 안 남고, 길 조각은 한 번에 모두 받아 받기 기록으로 구역이 드러나지 않게 한다.',
    r: '결과 — 이 화면이 닫히면 길이 사라진다. 남는 것 0.',
    svg: function () {
      return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><path d="M40 150 C 120 150 120 60 200 60 S 290 40 300 30" class="hw-rt hw-vr"/>'
        + '<g class="hw-o2"><circle cx="170" cy="100" r="30" class="hw-dk"/><text x="170" y="110" text-anchor="middle" style="font-size:28px">🔒</text></g>'
        + '<g class="hw-o4"><rect x="70" y="140" width="200" height="28" rx="14" class="hw-bub"/><text x="170" y="158" text-anchor="middle" class="hw-t11w">닫으면 사라짐 · 저장 0</text></g>';
    } });
  function ix(k) { for (var i = 0; i < SC.length; i++) if (SC[i].k === k) return i; return 0; }

  /* ---------- 모든 기능(☰ 항목별) — [그림, 이름, 어디서, 무엇을 · 어떻게, 장면] · ⚙ 은 설정 판 항목 ---------- */
  var FE = {
    st: [['🔑', '확인코드', '처음 한 번', '받은 코드를 넣으면 이 기기에 기억한다 — 다음부터 안 묻는다(데이터 압축지도와 같은 값).', 'open'],
      ['📍', '위치 허락', '처음 열 때 브라우저가 묻는다', '허락해야 내 자리 · 안내 · 켜놓고 다니기가 된다. 막았으면 지도를 길게 눌러 「여기서 떠나기」.', 'open'],
      ['🗺', '길을 아는 곳', '첫 안내 판', '첫 안내 판에 적힌 곳과 그 둘레의 길을 안다. 밖으로 나가면 「가르고 지도 밖」이라고 말한다.', null],
      ['📖', '이 그림 안내', '첫 안내 판 · ⚙ 맨 위', '▶ 움직임 · ▦ 한 장 · ☰ 항목별 · 👆 실제 화면. ⚙ 의 줄마다 🎬 로 그 그림을 바로 연다.', null]],
    fd: [['⌨', '이름 · 주소로 찾기', '위 찾는 칸', '주소 · 건물 · 역 · 교차로 이름을 적는다. 같은 이름이 가까이 겹치면 하나만 보인다.', 'find'],
      ['🎤', '말로 찾기', '찾는 칸 옆 🎤', '누르고 「서초역」처럼 말한다.', 'find'],
      ['👆', '지도에서 고르기', '지도를 두 번 톡 · 길게 누름', '「이곳을 목적지로 할까요?」 → 목적지로.', 'find'],
      ['📵', '통신이 끊겼을 때', '찾는 칸', '이 기기 안의 이름(역 · 신호)만 찾는다.', 'find'],
      ['🏠', '집 · 근무지 · 즐겨찾기 · 최근', '길 카드 「더 보기」 → 첫 화면 칩', '한 번 넣어 두면 칩 한 번으로 길. 즐겨찾기 12 · 최근 8.', 'places'],
      ['➕', '경유지', '고르는 판 「경유지로」 · 찾기 목록 「＋경유」', '「경유 1곳 — ○ → ○」 · 「경유지 빼기」로 되돌린다.', 'wp'],
      ['🚩', '여기서 떠나기', '고르는 판', 'GPS 대신 그 자리를 출발점으로.', 'wp']],
    cd: [['🧾', '길 카드 읽기', '아래 판', '도착 시각 · 시간 폭 · 모드 · 신호 수 · 소통 막대 · 가는 차례 · 🚧 돌발 · 위험 곳.', 'card'],
      ['🔀', '다른 길(회색)', '길 카드', '시간 · 거리 차이를 견주고 그 줄을 누르면 바꾼다.', 'alt'],
      ['🚗', '모드 고르기', '길 카드 위', '🚗 일반 · 🚨 긴급 출동' + (VIP ? ' · 🔒 업무' : '') + '.', 'em'],
      ['▶', '안내 시작', '길 카드', '신호 사다리 · 꺾을 곳 · 음성이 시작된다. 그만은 「끝」.', 'turn'],
      ['🎮', '모의 주행', '길 카드', '제한속도로 따라가며 신호에서 선다 — 떠나기 전에 미리.', 'sim'],
      ['📲', '다른 앱으로', '길 카드 「더 보기」', '티맵 · 카카오맵 · 네이버지도 · 데이터지도로 같은 목적지.', 'hand']],
    gd: [['↱', '꺾을 곳 · 그다음 · 차로', '안내 중 위 판', '남은 거리 · 길 이름 · 꼬리 칸의 그다음 · 갈 차로.', 'turn'],
      ['🔍', '자동 확대', '안내 중', '빠르면 넓게 · 꺾는 곳 250m 안이면 가깝게 · 손대면 15초 쉰다.', 'turn'],
      ['🚦', '신호 사다리', '안내 중 위 판 밑', '바로 앞 · 그다음 · 셋째의 「닿을 때 색」 — 이대로 · 발 떼기 · 서두르지 않기.', 'eco'],
      ['📷', '카메라 · 보호구역 · 사고 다발', '안내 중 왼쪽 카드 + 음성', '다가가면 표지 + 남은 거리. 제한속도 +10 을 5초 넘으면 말로.', 'warn'],
      ['🔁', '다시 찾기 · 더 빠른 길', '안내 중', '벗어나면 다시 찾고, 3분마다 더 빠른 길을 화면 위 단추로 묻는다.', 'reroute'],
      ['🚇', '터널에서 GPS 끊김', '안내 중', '길을 따라 2분까지 앞으로 어림한다.', 'tunnel'],
      ['🏁', '도착', '목적지 부근', '오른쪽 · 왼쪽까지 말하고 마친다.', 'arrive']],
    pc: [['🚨', '긴급 출동', '길 카드 모드', '적색 진입 · 좌우 · 버스전용차로 점선 · 신호 기다림을 셈에서 뺀다.', 'em'],
      ['🔢', '코드 0·1 · 코드 2 · 소방', '긴급 출동을 고른 뒤', '코드 2 는 신호 · 제한속도를 지킨다 · 소방은 골목 · 유턴을 두 배 불리하게.', 'codes'],
      ['🚓', '여러 순찰차 — 누가 먼저', '길 카드 「더 보기 — 순찰차 비교」', '＋ 지도 가운데 · ＋ 내 자리(최대 6대) → 차례 · 📻 복사.', 'disp'],
      ['🚇', '열차 안 신고', '목적지 없을 때 아래 판 · ⚙', '열차보다 먼저 닿을 역 · 선착 확률 · 출발 미룰 수 있는 시간 → 이 역으로 안내.', 'sr'],
      ['⏱', '역 실측', '⚙ → 따로 열리는 화면', '세운 자리 → 출입구 → 승강장을 잰다 · 3번 넘게 잰 값이 가정값 대신.', 'meas']]
      .concat(VIP ? [['🔒', '업무', '길 카드 모드', '이 기기 안 이름으로만 찾고 아무것도 남기지 않는다.', 'vip']] : [])
      .concat([['⚙', '업무 기본 속도 · 가장 이른 도착 기준', '⚙ 주행시간', '업무의 두 시간(기본 · 가장 이르면)을 셈하는 속도.', 'vtime'],
      ['⚙', '직접 입력 — 가장 느린 · 빠른', '⚙ 주행시간', '속도를 손으로 넣을 때 받는 범위.', 'vtime'],
      ['⚙', '회전 · 진출입로 · 출발·정지 감속', '⚙ 주행시간', '한 번마다 더하는 초(0 이면 안 더함).', 'vtime'],
      ['⚙', '터널·지하차도 속도 · 도주 차량 배율', '⚙ 주행시간', '터널은 ×0.8 ~ 그대로 · 도주 차량은 데이터지도 신고 차량 예측(×1.2 ~ ×1.5).', 'vtime']]),
    cr: [['▶', '켜놓고 다니기', '목적지 없을 때 아래 판', '길 이름 · 소통 · 제한속도 · 앞 신호 색과 남은 초를 계속.', 'cruise'],
      ['⚙', '사거리 표시 — 앞 · 뒤', '⚙ 안전운전', '켜놓고 다니기에서 지도에 보일 범위 — 앞 1~3km · 뒤 500m~1.5km.', 'cruise'],
      ['🚦', '신호 · 소통 층', '지도 위 단추', '층을 켜고 끈다.', 'layer'],
      ['👆', '신호 점 누르기', '지도', '방향별 지금 색 · 남은 초 · 「여기로 안내」.', 'layer'],
      ['✍', '값 없는 신호에 주기 넣기', '가는 차례 · ⚙', '받은 주기로 평균 기다림을 셈한다.', 'man'],
      ['🛣', '지도 시점', '⚙', '기울임 · 평면.', 'tilt'],
      ['✋', '지도 손가락 · ◎', '지도', '끌기 · 두 손가락 키우기 · ◎ 내 자리로.', 'tilt']],
    sc: [['◐', '밤 화면', '◐ 단추', '어두운 바탕으로.', 'night'],
      ['🌙', '밤 22~06시', '저절로', '속도 말 없이 색만.', 'night'],
      ['⚙', '기본 글씨 크기', '⚙ 글씨', '작게 ×0.9 ~ 아주 크게 ×1.3.', 'night'],
      ['🔊', '음성 안내', '🔊 단추', '꺾을 곳 · 적색 교차로 · 카메라 · 도착 예정 시각.', 'voice'],
      ['⚙', '음성 빠르기', '⚙ 음성', '느리게 · 보통 · 빠르게 · 아주 빠르게.', 'voice'],
      ['⚙', '진행방향 남은 초 글씨', '⚙ 글씨', '앞 신호 남은 초 숫자를 ×1 ~ ×3.', 'voice'],
      ['✈', '이동 속도', '🚦 신호 · 🚗 소통 옆 ✈ 속도', '비행기 · 기차 · 배에서 속도 · 고도 · 방향 — 통신 없이.', 'speedo']],
    rc: [['📈', '실측 보정', '⚙ 보정 · 기록', '끝까지 마친 일반 주행의 「걸린 ÷ 계산」 · 보정 지우기.', 'cal'],
      ['⏱', '예상·실제 도착 기록', '⚙ 보정 · 기록', '예상 폭 안에 든 비율 · 📤 내보내기 · 🗑 지우기.', 'cal'],
      ['⚙', '막힘 배율(ITS 실측)', '⚙ 주행시간', '실시간 소통이 없을 때 요일 · 시간대 배율 — 켬 · 끔.', 'cal'],
      ['🧠', '다녀 본 길 기억', '⚙ 보정 · 기록', '같은 줄을 두 번 넘게 지나면 그 시간을 쓴다 · 끄기 · 지우기.', 'learn'],
      ['🛰', '주행 기록', '⚙ 보정 · 기록', '켜면 2초마다 자리 · 최근 10번 · 📤 파일.', 'learn'],
      ['🔐', '이 기기에만 · 지우기 · 기본값', '⚙ 맨 아래', '↺ 기본 · 전체 기본값으로 · 최근 목적지 모두 지우기.', 'mine']]
  };

  /* ---------- 모양 ---------- */
  function css() {
    if ($('gHowCss')) return; var c = document.createElement('style'); c.id = 'gHowCss';
    var K = '', S = '';
    function kf(n, b) { K += '@keyframes ' + n + '{' + b + '}'; }
    kf('hwA', '0%{transform:translateX(0)}26%{transform:translateX(150px);animation-timing-function:linear}62%{transform:translateX(150px);animation-timing-function:ease-in}100%{transform:translateX(296px)}');
    kf('hwB', '0%{transform:translateX(0)}62%{transform:translateX(150px)}100%{transform:translateX(296px)}');
    kf('hwSg', '0%,61%{fill:#ef4444}62%,100%{fill:#22c55e}');
    kf('hwBrk', '0%,20%{opacity:0}22%,60%{opacity:1}62%,100%{opacity:0}');
    kf('hwO1', '0%,4%{opacity:0}8%,58%{opacity:1}61%,100%{opacity:0}'); kf('hwO2', '0%,61%{opacity:0}65%,100%{opacity:1}');
    kf('hwO3', '0%,30%{opacity:0}34%,100%{opacity:1}'); kf('hwO4', '0%,92%{opacity:0}95%,100%{opacity:1}');
    kf('hwE', '0%{transform:translateX(0)}30%{transform:translateX(110px)}52%{transform:translateX(190px)}72%{transform:translateX(205px)}100%{transform:translateX(310px)}');
    kf('hwO5', '0%,34%{opacity:0}38%,74%{opacity:1}78%,100%{opacity:0}'); kf('hwEye', '0%,50%{opacity:0}54%,72%{opacity:1}76%,100%{opacity:0}');
    kf('hwBl', '0%,49%{opacity:1}50%,100%{opacity:.15}'); kf('hwBl2', '0%,49%{opacity:.15}50%,100%{opacity:1}');
    kf('hwK1', '0%,5%{opacity:0}6%,100%{opacity:1}'); kf('hwK2', '0%,10%{opacity:0}11%,100%{opacity:1}'); kf('hwK3', '0%,15%{opacity:0}16%,100%{opacity:1}');
    kf('hwMic', '0%,2%,18%,100%{transform:scale(1)}8%,14%{transform:scale(1.25)}');
    kf('hwO6', '0%,19%{opacity:0}22%,34%{opacity:1}37%,100%{opacity:0}'); kf('hwRt', '0%,33%{stroke-dashoffset:360}50%,100%{stroke-dashoffset:0}');
    kf('hwO7', '0%,48%{opacity:0}51%,100%{opacity:1}'); kf('hwO8', '0%,51%{opacity:0}55%,100%{opacity:1}');
    kf('hwFg', '0%,58%{opacity:0;transform:translateY(10px)}62%,100%{opacity:1;transform:translateY(0)}');
    kf('hwRip', '0%,62%{r:0;opacity:0}64%{opacity:.6}76%{r:22;opacity:0}100%{r:22;opacity:0}');
    kf('hwO9', '0%,76%{opacity:0;transform:scale(.9)}80%,100%{opacity:1;transform:scale(1)}');
    kf('hwScr', '0%{transform:translateY(0)}100%{transform:translateY(80px)}');
    kf('hwP1', '0%,49%{opacity:1}52%,100%{opacity:0}'); kf('hwP2', '0%,49%{opacity:0}52%,100%{opacity:1}');
    kf('hwSg2', '0%,49%{fill:#22c55e}52%,100%{fill:#ef4444}');
    kf('hwSky', '0%,30%{fill:#e0f2fe}48%,100%{fill:#1e293b}'); kf('hwSun', '0%,30%{opacity:1}42%,100%{opacity:0}'); kf('hwMoon', '0%,38%{opacity:0}50%,100%{opacity:1}');
    kf('hwFz', '0%,60%{transform:scale(1)}72%,100%{transform:scale(1.3)}');
    kf('hwVr', '0%{stroke-dashoffset:360;opacity:1}35%,60%{stroke-dashoffset:0;opacity:1}80%,100%{stroke-dashoffset:0;opacity:0}');
    kf('hwPl', '0%{transform:scale(.6);opacity:.55}100%{transform:scale(1.6);opacity:0}');
    var D = 8;
    var A = function (sel, n, d, ex) { return '#gHow ' + sel + '{animation:' + n + ' ' + (d || D) + 's ' + (ex || 'linear') + ' infinite}'; };
    /* 장면마다 나타남(w-) · 움직임(m-) */
    SC.forEach(function (s) {
      Object.keys(s.w || {}).forEach(function (n) { var a = s.w[n][0], b = s.w[n][1], nm = 'hw_' + s.k + '_w' + n;
        kf(nm, a <= 0 ? '0%,' + b + '%{opacity:1}' + (b + 2) + '%,100%{opacity:0}' : b >= 100 ? '0%,' + a + '%{opacity:0}' + (a + 2) + '%,100%{opacity:1}' : '0%,' + a + '%{opacity:0}' + (a + 2) + '%,' + b + '%{opacity:1}' + (b + 2) + '%,100%{opacity:0}');
        S += '#gHow [data-k=' + s.k + '] .w-' + n + '{animation:' + nm + ' ' + D + 's linear infinite}'; });
      Object.keys(s.m || {}).forEach(function (n) { var nm = 'hw_' + s.k + '_m' + n; kf(nm, s.m[n]);
        S += '#gHow [data-k=' + s.k + '] .m-' + n + '{animation:' + nm + ' ' + (n === 'hd' ? 2 : D) + 's ' + (n === 'car' || n === 'wk' || n === 'pc' ? 'ease-in-out' : 'linear') + ' infinite}'; });
    });
    c.textContent = K
      + '#gHow{position:fixed;inset:0;z-index:70;display:none;background:var(--solid,#fff);color:var(--ink,#0f172a);overflow:auto;font-family:system-ui,sans-serif;word-break:keep-all;overflow-wrap:anywhere;'
      + '--hwmap:#eef2f7;--hwrd:#94a3b8;--hwst:#fff;--hwcd:#fff;--hwln:#e2e8f0}'
      + ':root.dark #gHow{--hwmap:#1f2937;--hwrd:#475569;--hwst:#374151;--hwcd:#111827;--hwln:#64748b}'
      + '#gHow.on{display:block}#gHow .in{max-width:520px;margin:0 auto;padding:calc(12px + env(safe-area-inset-top)) 16px calc(20px + env(safe-area-inset-bottom))}'
      + '#gHow .hd{display:flex;align-items:center;justify-content:space-between;gap:8px}#gHow .hd b{font-size:calc(19px * var(--fz,1))}'
      + '#gHow .hd button{flex:0 0 44px;width:44px;height:44px;border-radius:50%;border:0;background:rgba(15,23,42,.08);color:inherit;font-size:18px}:root.dark #gHow .hd button{background:rgba(255,255,255,.1)}'
      + '#gHow .vw{display:flex;gap:4px;margin:10px 0 10px;padding:4px;border-radius:14px;background:rgba(15,23,42,.06)}:root.dark #gHow .vw{background:rgba(255,255,255,.07)}'
      + '#gHow .vw button{flex:1;min-width:0;height:44px;border:0;border-radius:10px;background:transparent;color:inherit;font-weight:800;font-size:min(calc(14px * var(--fz,1)),3.7vw);white-space:nowrap;padding:0 1px}#gHow .vw button.on{background:var(--acc,#2563eb);color:#fff}'
      + '#gHow .cp{display:flex;gap:6px;overflow-x:auto;padding:2px 0 8px;margin:0 -16px;padding-left:16px;padding-right:16px;scrollbar-width:none}#gHow .cp::-webkit-scrollbar{display:none}'
      + '#gHow .cp button{flex:0 0 auto;height:36px;padding:0 12px;border-radius:18px;border:1px solid var(--line,#e2e8f0);background:transparent;color:inherit;font-weight:800;font-size:calc(13px * var(--fz,1));white-space:nowrap}#gHow .cp button.on{background:var(--ink,#0f172a);color:var(--solid,#fff);border-color:transparent}'
      + '#gHow .ct{font-size:calc(12px * var(--fz,1));font-weight:800;color:var(--dim,#55627a);margin:0 0 6px}'
      + '#gHow .sv{border-radius:16px;overflow:hidden;border:1px solid var(--line,#e2e8f0);background:var(--hwmap)}#gHow svg{display:block;width:100%;height:auto}'
      + '#gHow h3{margin:12px 0 4px;font-size:calc(17px * var(--fz,1))}#gHow p{margin:4px 0;font-size:calc(14px * var(--fz,1));line-height:1.55}#gHow p.rs{color:var(--acc2,#1d4ed8);font-weight:800}:root.dark #gHow p.rs{color:#93c5fd}'
      + '#gHow .nv{display:flex;align-items:center;gap:8px;margin-top:12px}#gHow .nv button{height:48px;border-radius:12px;border:1px solid var(--line,#e2e8f0);background:transparent;color:inherit;font-weight:800;font-size:min(calc(15px * var(--fz,1)),4.2vw);white-space:nowrap}'
      + '#gHow .nv .pv,#gHow .nv .nx{flex:0 0 56px}#gHow .nv .go{flex:1;min-width:0;background:var(--acc,#2563eb);color:#fff;border:0}'
      + '#gHow .gr{display:grid;grid-template-columns:1fr;gap:14px}@media (min-width:560px){#gHow .in{max-width:900px}#gHow .gr{grid-template-columns:1fr 1fr}}'
      + '#gHow .gr .it{border:1px solid var(--line,#e2e8f0);border-radius:16px;padding:10px}#gHow .gr .it .sv{border-radius:12px}#gHow .gr h3{margin-top:8px}'
      + '#gHow h4{margin:18px 0 8px;font-size:calc(15px * var(--fz,1));color:var(--dim,#55627a);letter-spacing:.02em}#gHow h4:first-of-type{margin-top:4px}'
      + '#gHow .li{display:flex;gap:10px;align-items:flex-start;padding:10px 0;border-bottom:1px solid var(--line,#e2e8f0)}#gHow .li .ic{flex:0 0 30px;font-size:20px;line-height:1.3;text-align:center}'
      + '#gHow .li .tx{flex:1;min-width:0}#gHow .li b{font-size:calc(15px * var(--fz,1))}#gHow .li .wh{display:block;margin-top:1px;font-size:calc(12px * var(--fz,1));font-weight:700;color:var(--acc2,#1d4ed8)}:root.dark #gHow .li .wh{color:#93c5fd}'
      + '#gHow .li p{margin:3px 0 0;font-size:calc(13.5px * var(--fz,1))}#gHow .li button{flex:0 0 auto;height:40px;padding:0 10px;border-radius:12px;border:1px solid rgba(37,99,235,.35);background:rgba(37,99,235,.08);color:inherit;font-weight:800;font-size:calc(12.5px * var(--fz,1));white-space:nowrap}'
      + '#gHow .still *{animation-play-state:paused!important}'
      + '#gHow .ft{margin-top:14px;font-size:calc(12px * var(--fz,1));color:var(--dim,#55627a);line-height:1.5}'
      /* 그림 속 글·모양 */
      + '#gHow .hw-rd{fill:var(--hwrd)}#gHow .hw-ln{stroke:#fff;stroke-width:2;stroke-dasharray:10 8;opacity:.8}#gHow .hw-stop{stroke:#fff;stroke-width:3}'
      + '#gHow .hw-map{fill:var(--hwmap)}#gHow .hw-st{fill:var(--hwst)}#gHow .hw-cd{fill:var(--hwcd);stroke:var(--hwln);stroke-width:1}#gHow .hw-cd.rb{fill:#fef2f2}:root.dark #gHow .hw-cd.rb{fill:#3b0d0d}'
      + '#gHow .hw-b2{fill:var(--hwcd);stroke:var(--hwln)}#gHow .hw-bt{fill:#2563eb}#gHow .hw-bub{fill:rgba(15,23,42,.88)}#gHow .hw-dk{fill:rgba(15,23,42,.9)}#gHow .hw-dk2{fill:rgba(30,41,59,.82)}'
      + '#gHow .hw-rt{fill:none;stroke:#2563eb;stroke-width:6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:360}#gHow .hw-rt.hw-rg{stroke:#94a3b8;opacity:.85}'
      + '#gHow .hw-ar{fill:none;stroke:#2563eb;stroke-width:2.5;stroke-linecap:round;stroke-dasharray:360}#gHow .hw-al{fill:none;stroke:#f59e0b;stroke-width:4;stroke-dasharray:7 6;stroke-linecap:round}'
      + '#gHow .hw-hl{fill:none;stroke:#f59e0b;stroke-width:2.5}#gHow .hw-tn{fill:#334155}#gHow .hw-pl{fill:#2563eb;transform-box:fill-box;transform-origin:center;animation:hwPl 1.2s ease-out infinite}'
      + '#gHow .hw-gn{fill:#22c55e}#gHow .hw-rdl{fill:#ef4444}#gHow .hw-ey{fill:none;stroke:#f59e0b;stroke-width:3;stroke-linecap:round}#gHow .hw-rip{fill:#2563eb}'
      + '#gHow text{font-family:system-ui,sans-serif;fill:var(--ink,#0f172a)}#gHow .hw-t8{font-size:8px;fill:var(--dim,#55627a)}#gHow .hw-t9{font-size:9.5px;font-weight:900;fill:var(--dim,#55627a)}#gHow .hw-t9w{font-size:9.5px;font-weight:800;fill:#cbd5e1}'
      + '#gHow .hw-t10{font-size:10.5px;font-weight:700;fill:var(--dim,#55627a)}#gHow .hw-t10b{font-size:10.5px;font-weight:800}#gHow .hw-t10w{font-size:10.5px;font-weight:800;fill:#fff}'
      + '#gHow .hw-t10r{font-size:10.5px;font-weight:900;fill:#dc2626}#gHow .hw-t10g{font-size:10.5px;font-weight:900;fill:#16a34a}:root.dark #gHow .hw-t10r{fill:#f87171}:root.dark #gHow .hw-t10g{fill:#4ade80}'
      + '#gHow .hw-t11{font-size:12px;font-weight:700}#gHow .hw-t11b{font-size:11.5px;font-weight:900}#gHow .hw-t11w{font-size:11.5px;font-weight:800;fill:#fff}#gHow .hw-t13{font-size:13px;font-weight:900}#gHow .hw-t13r{font-size:20px;font-weight:900;fill:#dc2626}'
      + '#gHow .hw-t15w{font-size:16px;font-weight:900;fill:#fff}#gHow .hw-t16{font-size:18px;font-weight:900}#gHow .hw-sp{font-size:46px;font-weight:900;fill:#fff}#gHow .hw-fz{transform-box:fill-box;transform-origin:left bottom}'
      + '#gHow .m-zm{transform-box:fill-box;transform-origin:30% 40%}#gHow .m-tl{transform-box:view-box;transform-origin:170px 190px}#gHow .m-big{transform-box:fill-box;transform-origin:center bottom}#gHow .m-hd{transform-box:fill-box;transform-origin:50% 100%}'
      /* 움직임 */
      + A('.hw-cA', 'hwA', D, 'ease-out') + A('.hw-cB', 'hwB') + A('.hw-sg', 'hwSg') + A('.hw-brk', 'hwBrk') + A('.hw-o1', 'hwO1') + A('.hw-o2', 'hwO2') + A('.hw-o3', 'hwO3') + A('.hw-o4', 'hwO4')
      + A('.hw-cE', 'hwE') + A('.hw-o5', 'hwO5') + A('.hw-eye', 'hwEye') + A('.hw-lr', 'hwBl', .6) + A('.hw-lb', 'hwBl2', .6)
      + A('.hw-k1', 'hwK1', 9) + A('.hw-k2', 'hwK2', 9) + A('.hw-k3', 'hwK3', 9) + A('.hw-o6', 'hwO6', 9) + A('[data-k=find] .hw-rt', 'hwRt', 9) + A('.hw-o7', 'hwO7', 9) + A('.hw-o8', 'hwO8', 9)
      + A('.hw-fg', 'hwFg', 9) + A('.hw-rip', 'hwRip', 9) + A('.hw-o9', 'hwO9', 9) + '#gHow .hw-mic,#gHow .hw-o9{transform-box:fill-box;transform-origin:center}' + A('.hw-mic', 'hwMic', 9)
      + A('.hw-scr', 'hwScr', 1.6) + A('.hw-p1', 'hwP1') + A('.hw-p2', 'hwP2') + A('.hw-sg2', 'hwSg2') + A('.hw-sky', 'hwSky') + A('.hw-sun', 'hwSun') + A('.hw-moon', 'hwMoon') + A('.hw-fz', 'hwFz')
      + A('.hw-vr', 'hwVr') + S
      + '#gHow [data-k=vip] .hw-o2{animation-name:hwO3}'
      /* 설정 판·첫 판 안 카드 */
      + '#gCfg .hwc{margin:10px 0 4px;padding:12px;border-radius:16px;background:linear-gradient(135deg,rgba(37,99,235,.10),rgba(22,163,74,.10));border:1px solid rgba(37,99,235,.25)}'
      + '#gCfg .hwc .hwt{display:flex;align-items:center;gap:10px}#gCfg .hwc .hwt svg{flex:0 0 76px;width:76px;height:auto;border-radius:10px}'
      + '#gCfg .hwc .hwt div{min-width:0}#gCfg .hwc .hwt b{display:block;font-size:calc(15px * var(--fz,1))}#gCfg .hwc .hwt span{display:block;margin-top:2px;font-size:calc(12.5px * var(--fz,1));color:var(--dim,#55627a);line-height:1.45}'
      + '#gCfg .hwc .hwb{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:10px}#gCfg .hwc .hwb button{min-width:0;height:44px;border-radius:12px;border:1px solid var(--line,#e2e8f0);background:var(--solid,#fff);color:inherit;font-weight:800;font-size:min(calc(13.5px * var(--fz,1)),4vw);white-space:nowrap;padding:0 2px}'
      + '#gCfg .hwc .hwb button:first-child{background:var(--acc,#2563eb);color:#fff;border:0}'
      + '#gCfg .hwq{display:inline-block;margin-left:6px;height:30px;padding:0 9px;border-radius:15px;border:1px solid rgba(37,99,235,.35);background:rgba(37,99,235,.08);color:inherit;font-size:calc(12px * var(--fz,1));font-weight:800;vertical-align:middle;white-space:nowrap}'
      + '#gIntro .hwi{display:block;width:100%;height:46px;margin:8px 0 0;border-radius:12px;border:1px solid rgba(37,99,235,.35);background:rgba(37,99,235,.08);color:inherit;font-weight:800;font-size:15px}'
      /* 실제 화면 짚기 */
      + '#gTour{position:fixed;inset:0;z-index:71;display:none}#gTour.on{display:block}#gTour .hole{position:fixed;border-radius:14px;box-shadow:0 0 0 9999px rgba(2,6,23,.66);transition:all .25s;pointer-events:none;outline:3px solid #fbbf24}'
      + '#gTour .tip{position:fixed;left:12px;right:12px;max-width:420px;margin:0 auto;background:var(--solid,#fff);color:var(--ink,#0f172a);border-radius:16px;padding:12px 14px;box-shadow:0 10px 30px rgba(0,0,0,.35);font-size:calc(14px * var(--fz,1));line-height:1.5;word-break:keep-all}'
      + '#gTour .tip b.n{color:var(--acc,#2563eb)}#gTour .tip .tb{display:flex;gap:6px;margin-top:10px}#gTour .tip button{flex:1;height:44px;border-radius:12px;border:1px solid var(--line,#e2e8f0);background:transparent;color:inherit;font-weight:800;font-size:calc(14px * var(--fz,1))}#gTour .tip button.go{background:var(--acc,#2563eb);color:#fff;border:0}'
      + '@media (prefers-reduced-motion:reduce){#gHow *{animation-play-state:paused!important}#gTour .hole{transition:none}}';
    document.head.appendChild(c);
  }

  /* ---------- 큰 판 ---------- */
  var EL = null, VIEW = 'm', IX = 0;
  function svgOf(s, still) { return '<div class="sv' + (still ? ' still' : '') + '" data-k="' + s.k + '"' + (still ? ' style="--d:' + (s.st || '-7.8s') + '"' : '') + '><svg viewBox="0 0 340 190" role="img" aria-label="' + s.t + '">' + s.svg() + '</svg></div>'; }
  function freeze(root) {   /* 「한 장」 — 그 장면의 결과가 보이는 때에 멈춘다 */
    [].forEach.call(root.querySelectorAll('.still'), function (w) { var d = w.style.getPropertyValue('--d'); [].forEach.call(w.querySelectorAll('*'), function (e) { if (getComputedStyle(e).animationName !== 'none') e.style.animationDelay = d; }); });
  }
  function chName(c) { for (var i = 0; i < CH.length; i++) if (CH[i][0] === c) return CH[i][1]; return ''; }
  function render() {
    var h = '<div class="in"><div class="hd"><b>🎬 가르고로 할 수 있는 것</b><button data-hw="x" aria-label="닫기">✕</button></div>'
      + '<div class="vw" role="tablist"><button data-hw="m" class="' + (VIEW === 'm' ? 'on' : '') + '">▶ 움직임</button><button data-hw="a" class="' + (VIEW === 'a' ? 'on' : '') + '">▦ 한 장</button><button data-hw="l" class="' + (VIEW === 'l' ? 'on' : '') + '">☰ 항목별</button><button data-hw="t">👆 실제</button></div>';
    if (VIEW === 'm') {
      var s = SC[IX];
      h += '<div class="cp">' + CH.map(function (c) { return '<button data-hwc="' + c[0] + '" class="' + (c[0] === s.c ? 'on' : '') + '">' + c[1] + '</button>'; }).join('') + '</div>'
        + '<div class="ct">' + chName(s.c) + ' · ' + (IX + 1) + ' / ' + SC.length + '</div>'
        + svgOf(s, RM) + '<h3>' + s.ic + ' ' + s.t + '</h3><p>' + s.d + '</p><p class="rs">' + s.r + '</p>'
        + '<div class="nv"><button class="pv" data-hw="pv" aria-label="앞 장면">◀</button><button class="go" data-hw="' + (s.tour >= 0 ? 'tg' : 'nx') + '">' + (s.tour >= 0 ? '👆 이것을 실제 화면에서' : '다음 장면 ▶') + '</button><button class="nx" data-hw="nx" aria-label="다음 장면">▶</button></div>';
    } else if (VIEW === 'a') {
      CH.forEach(function (c) { var L = SC.filter(function (s) { return s.c === c[0]; }); if (!L.length) return;
        h += '<h4>' + c[1] + '</h4><div class="gr">' + L.map(function (s) { return '<div class="it">' + svgOf(s, true) + '<h3>' + s.ic + ' ' + s.t + '</h3><p class="rs">' + s.r + '</p></div>'; }).join('') + '</div>'; });
    } else {
      var n = 0; CH.forEach(function (c) { n += (FE[c[0]] || []).length; });
      h += '<p>가르고의 기능과 ⚙ 설정 항목 <b>' + n + '가지</b>를 한 줄씩 적었다 — 어디서 찾는지 · 무엇을 하는지. 「▶ 그림」은 그 장면을 연다.</p>';
      CH.forEach(function (c) { h += '<h4>' + c[1] + '</h4>' + (FE[c[0]] || []).map(function (f) {
        return '<div class="li"><div class="ic">' + f[0] + '</div><div class="tx"><b>' + f[1] + '</b><span class="wh">' + f[2] + '</span><p>' + f[3] + '</p></div>' + (f[4] ? '<button data-hwk="' + f[4] + '">▶ 그림</button>' : '') + '</div>'; }).join(''); });
    }
    h += '<p class="ft">그림은 이해를 돕는 예시다 — 신호 숫자 · 시간 · 길 이름은 보기로 넣은 것. 실제 화면의 신호값은 <b>계획값</b>이라 수동 조작 · 감응 신호면 다르다 · 눈으로 확인한다. 일반 운전에서는 제한속도를 넘는 안내를 하지 않는다. 운전 중에는 화면을 조작하지 않는다.</p></div>';
    EL.innerHTML = h; freeze(EL); EL.scrollTop = 0;
    var on = EL.querySelector('.cp .on'); if (on && on.scrollIntoView) { var cp = on.parentNode; cp.scrollLeft = on.offsetLeft - cp.clientWidth / 2 + on.offsetWidth / 2; }
  }
  function open(v, i) { css(); if (!EL) { EL = document.createElement('div'); EL.id = 'gHow'; EL.setAttribute('role', 'dialog'); EL.setAttribute('aria-label', '가르고로 할 수 있는 것'); document.body.appendChild(EL); EL.addEventListener('click', onClick); bindSwipe(EL); }
    if (v === 't') { tour(0); return; } VIEW = v || (RM ? 'a' : 'm'); IX = typeof i === 'string' ? ix(i) : i || 0; render(); EL.classList.add('on'); }
  function close() { if (EL) EL.classList.remove('on'); }
  function onClick(e) { var b = e.target.closest('[data-hw],[data-hwc],[data-hwk]'); if (!b) return; var k = b.getAttribute('data-hw'), c = b.getAttribute('data-hwc'), q = b.getAttribute('data-hwk');
    if (c) { for (var i = 0; i < SC.length; i++) if (SC[i].c === c) { IX = i; break; } render(); return; }
    if (q) { VIEW = 'm'; IX = ix(q); render(); return; }
    if (k === 'x') close(); else if (k === 'm' || k === 'a' || k === 'l') { VIEW = k; render(); } else if (k === 't') tour(0);
    else if (k === 'nx') { IX = (IX + 1) % SC.length; render(); } else if (k === 'pv') { IX = (IX + SC.length - 1) % SC.length; render(); }
    else if (k === 'tg') tour(SC[IX].tour); }
  function bindSwipe(el) { var x0 = null, y0 = 0; el.addEventListener('touchstart', function (e) { if (VIEW !== 'm' || !e.touches[0] || e.target.closest('.cp')) { x0 = null; return; } x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    el.addEventListener('touchend', function (e) { if (x0 == null || !e.changedTouches[0]) return; var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null; if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) { IX = (IX + (dx < 0 ? 1 : SC.length - 1)) % SC.length; render(); } }, { passive: true }); }

  /* ---------- 실제 화면 짚기 ---------- */
  var STEPS = [
    { g: 0, el: function () { return document.querySelector('#gBot .hint') || document.querySelector('#gBot .sum'); }, t: '<b class="n">목적지를 정하면</b> 길 위 신호를 셈해 안내한다. 안내를 시작하면 위에 <b>바로 앞 · 그다음 · 셋째</b> 신호가 「닿을 때 색」으로 뜬다 — 적색이면 미리 발 떼기.' },
    { g: 1, el: function () { return document.querySelector('#gBot .mode'); }, t: '길을 고르면 여기서 <b>🚗 일반 · 🚨 긴급 출동</b>' + (VIP ? ' · 🔒 업무' : '') + '를 고른다. 긴급 출동은 신호 기다림을 셈에서 빼고, 닿을 때 적색인 교차로를 알린다.', miss: '길을 고르면 아래 판에 <b>🚗 일반 · 🚨 긴급 출동</b>' + (VIP ? ' · 🔒 업무' : '') + ' 단추가 나온다. 긴급 출동은 신호 기다림을 셈에서 빼고, 닿을 때 적색인 교차로를 알린다.' },
    { g: 2, el: function () { return $('gQ'); }, t: '<b>여기에 주소·이름</b>을 적는다.' },
    { g: 2, el: function () { return $('gMic'); }, t: '<b>🎤 누르고 말해도</b> 찾는다.' },
    { g: 2, el: function () { return $('gMap'); }, box: function () { var w = innerWidth, h = innerHeight; return { l: w / 2 - 60, t: h * 0.38, w: 120, h: 120 }; }, t: '지도를 <b>두 번 톡 · 길게 누르면</b> 「목적지로 · 경유지로」를 고르는 판이 뜬다.' },
    { g: 3, el: function () { return $('gCruise'); }, t: '<b>▶ 켜놓고 다니기</b> — 목적지 없이 달리는 길의 소통·제한속도·앞 신호를 계속 보인다.', miss: '목적지가 없을 때 아래 판에 <b>▶ 켜놓고 다니기</b>가 있다 — 목적지 없이 앞 신호·소통을 계속 보인다.' },
    { g: 3, el: function () { return $('gOv'); }, t: '지도 위 <b>🚦 신호 · 🚗 소통</b> 층을 켜고 끈다. 신호 점을 누르면 남은 초와 「여기로 안내」.' },
    { g: 4, el: function () { return $('gVoice'); }, t: '<b>🔊 음성 안내</b> — 꺾을 곳·적색 교차로를 말로 알린다.' },
    { g: 4, el: function () { return $('gCen'); }, t: '<b>◎ 내 자리로</b> — 지도를 움직였으면 다시 나를 따라간다.' },
    { g: 4, el: function () { return $('gDark'); }, t: '<b>◐ 밤 화면</b>.' },
    { g: 5, el: function () { return $('gSpdoB'); }, t: '<b>✈ 속도</b> — 비행기·기차·배에서 지금 속도·고도·방향(통신 없이 GPS 만).' },
    { g: 6, el: function () { return document.querySelector('#gBot [data-sr="open|"]'); }, t: '<b>🚇 열차 안 신고</b> — 열차보다 먼저 닿을 역을 셈한다.', miss: '목적지가 없을 때 아래 판에 <b>🚇 열차 안 신고</b>가 있다(⚙ 에도) — 열차보다 먼저 닿을 역을 셈한다.' },
    { g: 7, el: function () { return $('gCfgB'); }, t: '<b>⚙ 설정</b> — 글씨·음성·기록. 이 그림 안내는 설정 맨 위에서, 줄마다 🎬 로 다시 볼 수 있다.' }
  ];
  var TU = null, TI = 0, TL = [];
  function vis(e) { if (!e) return false; var r = e.getBoundingClientRect(); if (!r.width || !r.height) return false; var cs = getComputedStyle(e); return cs.display !== 'none' && cs.visibility !== 'hidden'; }
  function tour(g) { css(); close(); var cf = $('gCfg'); if (cf) cf.style.display = 'none'; var it = $('gIntro'); if (it && getComputedStyle(it).display !== 'none') { var ok = $('gOk'); if (ok) ok.click(); }
    TL = STEPS.filter(function (s) { return vis(s.el()) || s.miss; }); TI = 0; if (g > 0) { for (var i = 0; i < TL.length; i++) if (TL[i].g >= g) { TI = i; break; } }
    if (!TU) { TU = document.createElement('div'); TU.id = 'gTour'; TU.innerHTML = '<div class="hole"></div><div class="tip" role="dialog" aria-live="polite"></div>'; document.body.appendChild(TU);
      TU.addEventListener('click', function (e) { var b = e.target.closest('button'); if (b && b.getAttribute('data-tq') === 'x') { TU.classList.remove('on'); return; } if (b && b.getAttribute('data-tq') === 'pv') { TI = Math.max(0, TI - 1); step(); return; } TI++; if (TI >= TL.length) { TU.classList.remove('on'); return; } step(); });
      addEventListener('resize', function () { if (TU.classList.contains('on')) step(); }); }
    TU.classList.add('on'); step(); }
  function step() { var s = TL[TI], hole = TU.querySelector('.hole'), tip = TU.querySelector('.tip'), e = s.el(), on = vis(e), R;
    if (on) { R = s.box ? s.box() : (function () { var r = e.getBoundingClientRect(); return { l: r.left - 6, t: r.top - 6, w: r.width + 12, h: r.height + 12 }; })(); hole.style.display = 'block'; hole.style.left = R.l + 'px'; hole.style.top = R.t + 'px'; hole.style.width = R.w + 'px'; hole.style.height = R.h + 'px'; }
    else { hole.style.display = 'block'; hole.style.left = innerWidth / 2 + 'px'; hole.style.top = innerHeight / 2 + 'px'; hole.style.width = '0px'; hole.style.height = '0px'; }
    tip.innerHTML = '<div style="font-size:12px;font-weight:800;color:var(--dim,#55627a)">' + (TI + 1) + ' / ' + TL.length + '</div>' + (on ? s.t : s.miss) + '<div class="tb"><button data-tq="x">그만</button>' + (TI ? '<button data-tq="pv">◀</button>' : '') + '<button class="go">' + (TI + 1 < TL.length ? '다음 ▶' : '끝') + '</button></div>';
    var below = !on || R.t + R.h / 2 < innerHeight / 2; tip.style.top = below ? (on ? Math.min(innerHeight - tip.offsetHeight - 12, R.t + R.h + 12) : innerHeight / 2 - tip.offsetHeight / 2) + 'px' : Math.max(12, R.t - tip.offsetHeight - 12) + 'px'; }

  /* ---------- 설정 판·첫 판에 끼우기 ---------- */
  function mini() { return '<svg viewBox="0 0 76 52" aria-hidden="true"><rect width="76" height="52" fill="#1e293b"/><rect x="0" y="30" width="76" height="12" fill="#475569"/><rect x="5" y="6" width="20" height="16" rx="3" fill="#fff"/><rect x="5" y="6" width="20" height="3" fill="#16a34a"/><rect x="28" y="6" width="20" height="16" rx="3" fill="#fef2f2"/><rect x="28" y="6" width="20" height="3" fill="#dc2626"/><rect x="51" y="6" width="20" height="16" rx="3" fill="#fff"/><rect x="51" y="6" width="20" height="3" fill="#16a34a"/><g><rect x="6" y="32" width="16" height="8" rx="2" fill="#3b82f6"/>' + (RM ? '' : '<animateTransform attributeName="transform" type="translate" values="0 0;48 0;48 0" keyTimes="0;.7;1" dur="3s" repeatCount="indefinite"/>') + '</g></svg>'; }
  /* 설정 판 줄 → 그 그림 · 글이 바뀌면 여기 낱말도 같이 고친다(못 찾으면 🎬 가 안 붙을 뿐) */
  var RX = [[/음성 빠르기/, 'voice'], [/남은 초 글씨/, 'voice'], [/기본 글씨/, 'night'], [/사거리 표시/, 'cruise'], [/업무는 경로/, 'vip'],
    [/업무 기본 속도|가장 이른 도착|직접 입력|회전 감속|진출입로|가감속|터널·지하차도|도주 차량/, 'vtime'], [/막힘 배율|실측 보정|도착 기록/, 'cal'],
    [/열차 안 신고/, 'sr'], [/역 실측/, 'meas'], [/지도 시점/, 'tilt'], [/주행 기록|다녀 본 길/, 'learn'], [/직접 넣은 신호/, 'man']];
  function addRows(cf) { [].forEach.call(cf.querySelectorAll('.cl'), function (cl) { if (cl.querySelector('.hwq')) return; var tx = cl.textContent, k = null;
    for (var i = 0; i < RX.length; i++) if (RX[i][0].test(tx)) { k = RX[i][1]; break; } if (!k || (k === 'vip' && !VIP)) return;
    var b = document.createElement('button'); b.type = 'button'; b.className = 'hwq'; b.textContent = '🎬 그림'; b.setAttribute('aria-label', '이 항목을 그림으로 보기');
    b.addEventListener('click', function (e) { e.stopPropagation(); open('m', k); }); cl.appendChild(b); }); }
  function addCfg() { var cf = $('gCfg'); if (!cf) return; var cs = cf.querySelector('.cs'); if (!cs) return; addRows(cf); if (cf.querySelector('.hwc')) return;
    var d = document.createElement('div'); d.className = 'hwc';
    d.innerHTML = '<div class="hwt">' + mini() + '<div><b>🎬 가르고로 할 수 있는 것 — ' + SC.length + '장면</b><span>찾기 · 길 카드 · 안내 · 경찰 출동 · 켜놓고 다니기 · 기록까지 그림으로. 아래 줄마다 🎬 를 누르면 그 항목 그림.</span></div></div>'
      + '<div class="hwb"><button data-hwo="m">▶ 움직임</button><button data-hwo="a">▦ 한 장</button><button data-hwo="l">☰ 항목별</button><button data-hwo="t">👆 실제 화면</button></div>';
    d.addEventListener('click', function (e) { e.stopPropagation(); var b = e.target.closest('[data-hwo]'); if (b) open(b.getAttribute('data-hwo')); });   /* 설정 판의 클릭 처리(다시 그리기)로 넘기지 않는다 */
    cs.parentNode.insertBefore(d, cs.nextSibling); }
  function addIntro() { var it = $('gIntro'), ok = $('gOk'); if (!it || !ok || it.querySelector('.hwi')) return; var b = document.createElement('button'); b.className = 'hwi'; b.type = 'button'; b.textContent = '🎬 무엇을 하는지 그림으로 먼저 보기';
    b.addEventListener('click', function (e) { e.stopPropagation(); open('m'); }); ok.parentNode.insertBefore(b, ok.nextSibling); }
  function start() { css(); addIntro(); var cf = $('gCfg'); if (cf && window.MutationObserver) new MutationObserver(addCfg).observe(cf, { childList: true }); addCfg();
    addEventListener('keydown', function (e) { if (e.key === 'Escape') { if (TU && TU.classList.contains('on')) TU.classList.remove('on'); else close(); } }); }
  window.gargoHow = { open: open, tour: tour, scenes: SC, list: FE };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
