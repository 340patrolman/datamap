/* 가르고 「그림으로 보기」 (2026-11-22 형님 「설정칸에 니가 할 수 있는 것을 이미지와 모션으로 — 모르는 사람은 아예 모른다 ·
   그려서 결과를 보여 줄 수도, 그냥 보여 줄 수도, 다르게 볼 수도 있게」)
   · 보는 길 셋 — ▶ 움직임(장면마다 그림이 움직인다) · ▦ 한 장(움직임 없이 결과만 한 판에) · 👆 실제 화면(진짜 단추를 차례로 짚는다).
   · 그림 속 말은 앱이 실제로 하는 말 그대로 쓴다(sigladder.js 의 「이대로」「발 떼기」「적색 진입 · 좌우」 · gargo.js 의 음성 「적색 교차로입니다. 좌우 확인」).
     연비 몇 % 같은 숫자는 재 본 값이 없으므로 쓰지 않는다 — 「서는 횟수」처럼 그림으로 보이는 것만.
   · 움직임 줄이기(prefers-reduced-motion)면 처음부터 「한 장」.
   · gargo.js 를 고치지 않는다 — 설정 판(#gCfg)이 다시 그려질 때마다 맨 위에 카드 하나를 끼우고(MutationObserver), 첫 안내 판(#gIntro)에도 단추 하나. */
(function () {
  function $(id) { return document.getElementById(id); }
  var VIP = !!(window.TT && TT.VIP_ON), RM = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 그림 ---------- */
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
  var SC = [
    { k: 'eco', ic: '🚦', t: '신호 사다리 — 경제운전', st: '-7.6s',
      d: '안내 중 위에 <b>바로 앞 · 그다음 · 셋째</b> 신호를 「닿을 때 색」으로 보인다. 앞이 적색이면 미리 <b>발 떼기</b> — 급제동 없이 굴러가 녹색에 닿는다.',
      r: '결과 — 같은 때 도착하는데 위 차는 섰다 다시 출발, 아래 차는 서지 않는다(브레이크·연료·타이어·안전).',
      tour: 0,
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
    { k: 'em', ic: '🚨', t: '긴급 출동 — 경찰차는 다르게', st: '-4.9s',
      d: '🚨 긴급 출동을 고르면 길 셈에서 <b>신호 기다림을 뺀다</b>. 그 대신 닿을 때 적색인 교차로를 <b>「적색 진입 · 좌우」</b>로 미리 알리고, 음성 안내를 켰으면 말로도 알린다. 지도에 버스전용차로를 점선으로 그린다.',
      r: '결과 — 어디서 적색에 들어가는지 미리 알고 서행·좌우 확인 준비. 코드 2(신속히 · 신호 지킴)는 일반처럼 신호를 셈에 넣는다. 통과는 운전자 판단.',
      tour: 1,
      svg: function () {
        return card(4, 106, 'g', '바로 앞', '6초', '통과') + card(117, 106, 'r', '그다음', '24초', '적색 진입 · 좌우') + card(230, 106, 'g', '셋째', '15초', '통과')
          + road(86, 46) + '<line x1="0" y1="127" x2="340" y2="127" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="7 5" opacity=".8"/>'
          + lamp(118, 82, 'hw-gn') + lamp(232, 82, 'hw-rdl')
          + '<g class="hw-eye"><path d="M222 92 q-14 -12 -26 -8" class="hw-ey"/><path d="M222 128 q-14 12 -26 8" class="hw-ey"/><text x="150" y="80" class="hw-t10b">👀 좌</text><text x="150" y="148" class="hw-t10b">👀 우</text></g>'
          + '<g class="hw-cE"><g transform="translate(6,106)">' + car('#f8fafc', 1) + '<rect x="0" y="-7" width="30" height="14" rx="4" fill="none" stroke="#94a3b8"/></g></g>'
          + '<g class="hw-o5"><rect x="56" y="154" width="228" height="24" rx="12" class="hw-bub"/><text x="170" y="170" text-anchor="middle" class="hw-t11w">🔊 「적색 교차로입니다. 좌우 확인」</text></g>'
          + '<text x="334" y="148" text-anchor="end" class="hw-t10" style="fill:#3b82f6">┅ 버스전용차로</text>';
      } },
    { k: 'find', ic: '🔎', t: '목적지 찾기 — 적거나 · 말하거나 · 누르거나', st: '-8.6s',
      d: '위 칸에 주소·이름을 적거나 <b>🎤 말한다</b>. 아니면 지도를 <b>두 번 톡 · 길게 눌러</b> 「목적지로 · 경유지로」를 고른다. 길을 고른 뒤 티맵·카카오맵·네이버지도로 넘길 수도 있다.',
      r: '결과 — 길과 걸리는 시간·도착 시각이 바로 나오고, 「▶ 안내 시작」을 누르면 신호 사다리가 뜬다.',
      tour: 2,
      svg: function () {
        var g = '<rect x="0" y="0" width="340" height="190" class="hw-map"/>';
        [40, 95, 150].forEach(function (y) { g += '<rect x="0" y="' + y + '" width="340" height="9" class="hw-st"/>'; });
        [60, 170, 280].forEach(function (x) { g += '<rect x="' + x + '" y="0" width="9" height="190" class="hw-st"/>'; });
        return g + '<rect x="10" y="8" width="320" height="26" rx="13" class="hw-cd"/><text x="22" y="26" class="hw-t11"><tspan class="hw-k1">서</tspan><tspan class="hw-k2">초</tspan><tspan class="hw-k3">역</tspan></text>'
          + '<g class="hw-mic"><circle cx="314" cy="21" r="9" fill="#2563eb"/><text x="314" y="25" text-anchor="middle" class="hw-t10w">🎤</text></g>'
          + '<g class="hw-o6"><rect x="10" y="38" width="200" height="24" rx="8" class="hw-cd"/><text x="20" y="54" class="hw-t11b">📍 서초역</text></g>'
          + '<path d="M64 154 V99 H174 V44 H284" class="hw-rt"/><circle cx="64" cy="154" r="7" fill="#fff" stroke="#2563eb" stroke-width="3"/>'
          + '<g class="hw-o7"><path d="M284 44 m0 -2 c-8 -12 8 -12 0 0 z" fill="#dc2626"/><circle cx="284" cy="30" r="8" fill="#dc2626"/><circle cx="284" cy="30" r="3" fill="#fff"/></g>'
          + '<g class="hw-o8"><rect x="96" y="128" width="96" height="22" rx="11" class="hw-bub"/><text x="144" y="143" text-anchor="middle" class="hw-t11w">12분 · 3.1km</text></g>'
          + '<g class="hw-fg"><circle cx="232" cy="120" r="12" class="hw-rip"/><text x="232" y="132" text-anchor="middle" style="font-size:22px">👆</text></g>'
          + '<g class="hw-o9"><rect x="120" y="58" width="190" height="56" rx="10" class="hw-cd"/><text x="215" y="76" text-anchor="middle" class="hw-t10b">이곳을 목적지·경유지로 할까요?</text>'
          + '<rect x="130" y="84" width="82" height="22" rx="7" fill="#2563eb"/><text x="171" y="99" text-anchor="middle" class="hw-t10w">목적지로</text><rect x="218" y="84" width="82" height="22" rx="7" class="hw-b2"/><text x="259" y="99" text-anchor="middle" class="hw-t10b">경유지로</text></g>';
      } },
    { k: 'cruise', ic: '▶', t: '켜놓고 다니기 — 목적지 없이', st: '-3s',
      d: '목적지를 안 정하고 <b>▶ 켜놓고 다니기</b>를 누르면, 달리는 길의 이름·지금 소통·제한속도·<b>앞 신호의 지금 색과 남은 초</b>를 계속 보인다. 평소 순찰용.',
      r: '결과 — 화면을 안 만져도 앞 신호와 이 길 사정이 늘 위에 떠 있다. 제한속도를 넘으면 숫자가 붉어진다.',
      tour: 3,
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
    { k: 'night', ic: '🌙', t: '밤 · 글씨 크기', st: '-7.6s',
      d: '밤 22~06시에는 <b>속도 말 없이 색만</b> 보인다 — 과속을 막으려고 일부러 끊어 둔 신호를 거스르지 않는다. ◐ 로 밤 화면, ⚙ 설정에서 글씨를 ×0.9~×1.3 으로.',
      r: '결과 — 밤에는 「이대로·발 떼기」가 「녹색·적색」으로만 남는다. 글씨를 키우면 사다리·도착 시각이 같이 커진다.',
      tour: 4,
      svg: function () {
        return '<rect x="0" y="0" width="340" height="190" class="hw-sky"/><text x="292" y="40" class="hw-sun" style="font-size:28px">☀</text><text x="292" y="40" class="hw-moon" style="font-size:26px">🌙</text>'
          + '<g class="hw-p1">' + card(4, 90, 'g', '바로 앞', '12초', '이대로') + card(100, 90, 'r', '그다음', '25초', '발 떼기') + '</g>'
          + '<g class="hw-p2">' + card(4, 90, 'g', '바로 앞', '12초', '녹색') + card(100, 90, 'r', '그다음', '25초', '적색') + '</g>'
          + '<g class="hw-o2"><rect x="4" y="64" width="250" height="24" rx="12" class="hw-bub"/><text x="129" y="80" text-anchor="middle" class="hw-t11w">밤 22~06시 — 속도 말 없이 색만</text></g>'
          + '<g transform="translate(60,150)"><text class="hw-fz" x="0" y="0" style="font-size:26px;font-weight:900">가 12분</text></g><text x="200" y="146" class="hw-t11b"><tspan class="hw-p1">글씨 ×1</tspan><tspan class="hw-p2" x="200">글씨 ×1.3</tspan></text><text x="200" y="164" class="hw-t10">⚙ 설정 › 글씨 크기</text>';
      } }
  ];
  if (VIP) SC.push({ k: 'vip', ic: '🔒', t: '업무 — 남기지 않는다', st: '-7.6s',
    d: '🔒 업무로 찾으면 <b>이 기기 안 이름·도로명 번호로만</b> 찾고, 경로·지점·시각을 <b>저장하지 않는다</b>. 최근 목적지·주행 기록·다녀 본 길에도 안 남는다.',
    r: '결과 — 이 화면이 닫히면 길이 사라진다. 남는 것 0.',
    tour: -1,
    svg: function () {
      return '<rect x="0" y="0" width="340" height="190" class="hw-map"/><path d="M40 150 C 120 150 120 60 200 60 S 290 40 300 30" class="hw-rt hw-vr"/>'
        + '<g class="hw-o2"><circle cx="170" cy="100" r="30" class="hw-dk"/><text x="170" y="110" text-anchor="middle" style="font-size:28px">🔒</text></g>'
        + '<g class="hw-o4"><rect x="70" y="140" width="200" height="28" rx="14" class="hw-bub"/><text x="170" y="158" text-anchor="middle" class="hw-t11w">닫으면 사라짐 · 저장 0</text></g>';
    } });

  /* ---------- 모양 ---------- */
  function css() {
    if ($('gHowCss')) return; var c = document.createElement('style'); c.id = 'gHowCss';
    var K = '';
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
    var D = 8;
    var A = function (sel, n, d, ex) { return '#gHow ' + sel + '{animation:' + n + ' ' + (d || D) + 's ' + (ex || 'linear') + ' infinite}'; };
    c.textContent = K
      + '#gHow{position:fixed;inset:0;z-index:70;display:none;background:var(--solid,#fff);color:var(--ink,#0f172a);overflow:auto;font-family:system-ui,sans-serif;word-break:keep-all;overflow-wrap:anywhere;'
      + '--hwmap:#eef2f7;--hwrd:#94a3b8;--hwst:#fff;--hwcd:#fff;--hwln:#e2e8f0}'
      + ':root.dark #gHow{--hwmap:#1f2937;--hwrd:#475569;--hwst:#374151;--hwcd:#111827;--hwln:#64748b}'
      + '#gHow.on{display:block}#gHow .in{max-width:520px;margin:0 auto;padding:calc(12px + env(safe-area-inset-top)) 16px calc(20px + env(safe-area-inset-bottom))}'
      + '#gHow .hd{display:flex;align-items:center;justify-content:space-between;gap:8px}#gHow .hd b{font-size:calc(19px * var(--fz,1))}'
      + '#gHow .hd button{flex:0 0 44px;width:44px;height:44px;border-radius:50%;border:0;background:rgba(15,23,42,.08);color:inherit;font-size:18px}:root.dark #gHow .hd button{background:rgba(255,255,255,.1)}'
      + '#gHow .vw{display:flex;gap:6px;margin:10px 0 12px;padding:4px;border-radius:14px;background:rgba(15,23,42,.06)}:root.dark #gHow .vw{background:rgba(255,255,255,.07)}'
      + '#gHow .vw button{flex:1;min-width:0;height:44px;border:0;border-radius:10px;background:transparent;color:inherit;font-weight:800;font-size:min(calc(14px * var(--fz,1)),4vw);white-space:nowrap;padding:0 2px}#gHow .vw button.on{background:var(--acc,#2563eb);color:#fff}'
      + '#gHow .sv{border-radius:16px;overflow:hidden;border:1px solid var(--line,#e2e8f0);background:var(--hwmap)}#gHow svg{display:block;width:100%;height:auto}'
      + '#gHow h3{margin:12px 0 4px;font-size:calc(17px * var(--fz,1))}#gHow p{margin:4px 0;font-size:calc(14px * var(--fz,1));line-height:1.55}#gHow p.rs{color:var(--acc2,#1d4ed8);font-weight:800}:root.dark #gHow p.rs{color:#93c5fd}'
      + '#gHow .nv{display:flex;align-items:center;gap:8px;margin-top:12px}#gHow .nv button{height:48px;border-radius:12px;border:1px solid var(--line,#e2e8f0);background:transparent;color:inherit;font-weight:800;font-size:calc(15px * var(--fz,1))}'
      + '#gHow .nv .pv,#gHow .nv .nx{flex:0 0 56px}#gHow .nv .go{flex:1;background:var(--acc,#2563eb);color:#fff;border:0}'
      + '#gHow .dt{display:flex;justify-content:center;gap:6px;margin-top:10px}#gHow .dt i{width:8px;height:8px;border-radius:4px;background:var(--line,#cbd5e1);transition:width .2s}#gHow .dt i.on{width:22px;background:var(--acc,#2563eb)}'
      + '#gHow .gr{display:grid;grid-template-columns:1fr;gap:14px}@media (min-width:560px){#gHow .in{max-width:900px}#gHow .gr{grid-template-columns:1fr 1fr}}'
      + '#gHow .gr .it{border:1px solid var(--line,#e2e8f0);border-radius:16px;padding:10px}#gHow .gr .it .sv{border-radius:12px}#gHow .gr h3{margin-top:8px}'
      + '#gHow .still *{animation-play-state:paused!important}'
      + '#gHow .ft{margin-top:14px;font-size:calc(12px * var(--fz,1));color:var(--dim,#55627a);line-height:1.5}'
      /* 그림 속 글·모양 */
      + '#gHow .hw-rd{fill:var(--hwrd)}#gHow .hw-ln{stroke:#fff;stroke-width:2;stroke-dasharray:10 8;opacity:.8}#gHow .hw-stop{stroke:#fff;stroke-width:3}'
      + '#gHow .hw-map{fill:var(--hwmap)}#gHow .hw-st{fill:var(--hwst)}#gHow .hw-cd{fill:var(--hwcd);stroke:var(--hwln);stroke-width:1}#gHow .hw-cd.rb{fill:#fef2f2}:root.dark #gHow .hw-cd.rb{fill:#3b0d0d}'
      + '#gHow .hw-b2{fill:transparent;stroke:var(--hwln)}#gHow .hw-bub{fill:rgba(15,23,42,.88)}#gHow .hw-dk{fill:rgba(15,23,42,.9)}'
      + '#gHow .hw-rt{fill:none;stroke:#2563eb;stroke-width:6;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:360}'
      + '#gHow .hw-gn{fill:#22c55e}#gHow .hw-rdl{fill:#ef4444}#gHow .hw-ey{fill:none;stroke:#f59e0b;stroke-width:3;stroke-linecap:round}#gHow .hw-rip{fill:#2563eb}'
      + '#gHow text{font-family:system-ui,sans-serif;fill:var(--ink,#0f172a)}#gHow .hw-t8{font-size:8px;fill:var(--dim,#55627a)}#gHow .hw-t9{font-size:9.5px;font-weight:900;fill:var(--dim,#55627a)}'
      + '#gHow .hw-t10{font-size:10.5px;font-weight:700;fill:var(--dim,#55627a)}#gHow .hw-t10b{font-size:10.5px;font-weight:800}#gHow .hw-t10w{font-size:10.5px;font-weight:800;fill:#fff}'
      + '#gHow .hw-t10r{font-size:10.5px;font-weight:900;fill:#dc2626}#gHow .hw-t10g{font-size:10.5px;font-weight:900;fill:#16a34a}:root.dark #gHow .hw-t10r{fill:#f87171}:root.dark #gHow .hw-t10g{fill:#4ade80}'
      + '#gHow .hw-t11{font-size:12px;font-weight:700}#gHow .hw-t11b{font-size:11.5px;font-weight:900}#gHow .hw-t11w{font-size:11.5px;font-weight:800;fill:#fff}#gHow .hw-t13{font-size:13px;font-weight:900}'
      + '#gHow .hw-t15w{font-size:16px;font-weight:900;fill:#fff}#gHow .hw-t16{font-size:18px;font-weight:900}#gHow .hw-fz{transform-box:fill-box;transform-origin:left bottom}'
      /* 움직임 */
      + A('.hw-cA', 'hwA', D, 'ease-out') + A('.hw-cB', 'hwB') + A('.hw-sg', 'hwSg') + A('.hw-brk', 'hwBrk') + A('.hw-o1', 'hwO1') + A('.hw-o2', 'hwO2') + A('.hw-o3', 'hwO3') + A('.hw-o4', 'hwO4')
      + A('.hw-cE', 'hwE') + A('.hw-o5', 'hwO5') + A('.hw-eye', 'hwEye') + A('.hw-lr', 'hwBl', .6) + A('.hw-lb', 'hwBl2', .6)
      + A('.hw-k1', 'hwK1', 9) + A('.hw-k2', 'hwK2', 9) + A('.hw-k3', 'hwK3', 9) + A('.hw-o6', 'hwO6', 9) + A('.hw-rt:not(.hw-vr)', 'hwRt', 9) + A('.hw-o7', 'hwO7', 9) + A('.hw-o8', 'hwO8', 9)
      + A('.hw-fg', 'hwFg', 9) + A('.hw-rip', 'hwRip', 9) + A('.hw-o9', 'hwO9', 9) + '#gHow .hw-mic,#gHow .hw-o9{transform-box:fill-box;transform-origin:center}' + A('.hw-mic', 'hwMic', 9)
      + A('.hw-scr', 'hwScr', 1.6) + A('.hw-p1', 'hwP1') + A('.hw-p2', 'hwP2') + A('.hw-sg2', 'hwSg2') + A('.hw-sky', 'hwSky') + A('.hw-sun', 'hwSun') + A('.hw-moon', 'hwMoon') + A('.hw-fz', 'hwFz')
      + A('.hw-vr', 'hwVr')
      + '#gHow [data-k=vip] .hw-o2{animation-name:hwO3}'
      /* 설정 판·첫 판 안 카드 */
      + '#gCfg .hwc{margin:10px 0 4px;padding:12px;border-radius:16px;background:linear-gradient(135deg,rgba(37,99,235,.10),rgba(22,163,74,.10));border:1px solid rgba(37,99,235,.25)}'
      + '#gCfg .hwc .hwt{display:flex;align-items:center;gap:10px}#gCfg .hwc .hwt svg{flex:0 0 76px;width:76px;height:auto;border-radius:10px}'
      + '#gCfg .hwc .hwt div{min-width:0}#gCfg .hwc .hwt b{display:block;font-size:calc(15px * var(--fz,1))}#gCfg .hwc .hwt span{display:block;margin-top:2px;font-size:calc(12.5px * var(--fz,1));color:var(--dim,#55627a);line-height:1.45}'
      + '#gCfg .hwc .hwb{display:flex;gap:6px;margin-top:10px}#gCfg .hwc .hwb button{flex:1;min-width:0;height:44px;border-radius:12px;border:1px solid var(--line,#e2e8f0);background:var(--solid,#fff);color:inherit;font-weight:800;font-size:min(calc(13px * var(--fz,1)),3.9vw);white-space:nowrap;padding:0 2px}'
      + '#gCfg .hwc .hwb button:first-child{background:var(--acc,#2563eb);color:#fff;border:0}'
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
  function svgOf(s, still) { return '<div class="sv' + (still ? ' still' : '') + '" data-k="' + s.k + '"' + (still ? ' style="--d:' + s.st + '"' : '') + '><svg viewBox="0 0 340 190" role="img" aria-label="' + s.t + '">' + s.svg() + '</svg></div>'; }
  function freeze(root) {   /* 「한 장」 — 그 장면의 결과가 보이는 때에 멈춘다 */
    [].forEach.call(root.querySelectorAll('.still'), function (w) { var d = w.style.getPropertyValue('--d'); [].forEach.call(w.querySelectorAll('*'), function (e) { if (getComputedStyle(e).animationName !== 'none') e.style.animationDelay = d; }); });
  }
  function render() {
    var h = '<div class="in"><div class="hd"><b>🎬 가르고로 할 수 있는 것</b><button data-hw="x" aria-label="닫기">✕</button></div>'
      + '<div class="vw" role="tablist"><button data-hw="m" class="' + (VIEW === 'm' ? 'on' : '') + '">▶ 움직임</button><button data-hw="a" class="' + (VIEW === 'a' ? 'on' : '') + '">▦ 한 장</button><button data-hw="t">👆 실제 화면</button></div>';
    if (VIEW === 'm') {
      var s = SC[IX]; h += svgOf(s, RM) + '<h3>' + s.ic + ' ' + s.t + '</h3><p>' + s.d + '</p><p class="rs">' + s.r + '</p>'
        + '<div class="nv"><button class="pv" data-hw="pv" aria-label="앞 장면">◀</button><button class="go" data-hw="' + (s.tour >= 0 ? 'tg' : 'nx') + '">' + (s.tour >= 0 ? '👆 이것을 실제 화면에서' : '다음 ▶') + '</button><button class="nx" data-hw="nx" aria-label="다음 장면">▶</button></div>'
        + '<div class="dt">' + SC.map(function (x, i) { return '<i class="' + (i === IX ? 'on' : '') + '"></i>'; }).join('') + '</div>';
    } else {
      h += '<div class="gr">' + SC.map(function (s) { return '<div class="it">' + svgOf(s, true) + '<h3>' + s.ic + ' ' + s.t + '</h3><p class="rs">' + s.r + '</p></div>'; }).join('') + '</div>';
    }
    h += '<p class="ft">그림은 이해를 돕는 예시다 — 신호 숫자·길 이름은 보기로 넣은 것. 실제 화면의 신호값은 <b>계획값</b>이라 수동 조작·감응 신호면 다르다 · 눈으로 확인한다. 일반 운전에서는 제한속도를 넘는 안내를 하지 않는다.</p></div>';
    EL.innerHTML = h; freeze(EL); EL.scrollTop = 0;
  }
  function open(v, i) { css(); if (!EL) { EL = document.createElement('div'); EL.id = 'gHow'; EL.setAttribute('role', 'dialog'); EL.setAttribute('aria-label', '가르고로 할 수 있는 것'); document.body.appendChild(EL); EL.addEventListener('click', onClick); bindSwipe(EL); }
    if (v === 't') { tour(0); return; } VIEW = v || (RM ? 'a' : 'm'); IX = i || 0; render(); EL.classList.add('on'); }
  function close() { if (EL) EL.classList.remove('on'); }
  function onClick(e) { var b = e.target.closest('[data-hw]'); if (!b) return; var k = b.getAttribute('data-hw');
    if (k === 'x') close(); else if (k === 'm' || k === 'a') { VIEW = k; render(); } else if (k === 't') tour(0);
    else if (k === 'nx') { IX = (IX + 1) % SC.length; render(); } else if (k === 'pv') { IX = (IX + SC.length - 1) % SC.length; render(); }
    else if (k === 'tg') tour(SC[IX].tour); }
  function bindSwipe(el) { var x0 = null, y0 = 0; el.addEventListener('touchstart', function (e) { if (VIEW !== 'm' || !e.touches[0]) return; x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
    el.addEventListener('touchend', function (e) { if (x0 == null || !e.changedTouches[0]) return; var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null; if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) { IX = (IX + (dx < 0 ? 1 : SC.length - 1)) % SC.length; render(); } }, { passive: true }); }

  /* ---------- 실제 화면 짚기 ---------- */
  var STEPS = [
    { g: 0, el: function () { return document.querySelector('#gBot .hint') || document.querySelector('#gBot .sum'); }, t: '<b class="n">목적지를 정하면</b> 길 위 신호를 셈해 안내한다. 안내를 시작하면 위에 <b>바로 앞 · 그다음 · 셋째</b> 신호가 「닿을 때 색」으로 뜬다 — 적색이면 미리 발 떼기.' },
    { g: 1, el: function () { return document.querySelector('#gBot .mode'); }, t: '길을 고르면 여기서 <b>🚗 일반 · 🚨 긴급 출동</b>' + (VIP ? ' · 🔒 업무' : '') + '를 고른다. 긴급 출동은 신호 기다림을 셈에서 빼고, 닿을 때 적색인 교차로를 알린다.', miss: '길을 고르면 아래 판에 <b>🚗 일반 · 🚨 긴급 출동</b>' + (VIP ? ' · 🔒 업무' : '') + ' 단추가 나온다. 긴급 출동은 신호 기다림을 셈에서 빼고, 닿을 때 적색인 교차로를 알린다.' },
    { g: 2, el: function () { return $('gQ'); }, t: '<b>여기에 주소·이름</b>을 적는다.' },
    { g: 2, el: function () { return $('gMic'); }, t: '<b>🎤 누르고 말해도</b> 찾는다.' },
    { g: 2, el: function () { return $('gMap'); }, box: function () { var w = innerWidth, h = innerHeight; return { l: w / 2 - 60, t: h * 0.38, w: 120, h: 120 }; }, t: '지도를 <b>두 번 톡 · 길게 누르면</b> 「목적지로 · 경유지로」를 고르는 판이 뜬다.' },
    { g: 3, el: function () { return $('gCruise'); }, t: '<b>▶ 켜놓고 다니기</b> — 목적지 없이 달리는 길의 소통·제한속도·앞 신호를 계속 보인다.', miss: '목적지가 없을 때 아래 판에 <b>▶ 켜놓고 다니기</b>가 있다 — 목적지 없이 앞 신호·소통을 계속 보인다.' },
    { g: 3, el: function () { return $('gOv'); }, t: '지도 위 <b>🚦 신호 · 🚗 소통</b> 층을 켜고 끈다.' },
    { g: 4, el: function () { return $('gVoice'); }, t: '<b>🔊 음성 안내</b> — 꺾을 곳·적색 교차로를 말로 알린다.' },
    { g: 4, el: function () { return $('gCen'); }, t: '<b>◎ 내 자리로</b> — 지도를 움직였으면 다시 나를 따라간다.' },
    { g: 4, el: function () { return $('gDark'); }, t: '<b>◐ 밤 화면</b>.' },
    { g: 4, el: function () { return $('gCfgB'); }, t: '<b>⚙ 설정</b> — 글씨 크기 등. 이 그림 안내는 설정 맨 위에서 다시 볼 수 있다.' }
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
  function addCfg() { var cf = $('gCfg'); if (!cf || cf.querySelector('.hwc')) return; var cs = cf.querySelector('.cs'); if (!cs) return;
    var d = document.createElement('div'); d.className = 'hwc';
    d.innerHTML = '<div class="hwt">' + mini() + '<div><b>🎬 가르고로 할 수 있는 것</b><span>신호 사다리 · 긴급 출동 · 찾기 · 켜놓고 다니기 · 밤' + (VIP ? ' · 업무' : '') + ' — 그림으로 본다</span></div></div>'
      + '<div class="hwb"><button data-hwo="m">▶ 움직임</button><button data-hwo="a">▦ 한 장</button><button data-hwo="t">👆 실제 화면</button></div>';
    d.addEventListener('click', function (e) { e.stopPropagation(); var b = e.target.closest('[data-hwo]'); if (b) open(b.getAttribute('data-hwo')); });   /* 설정 판의 클릭 처리(다시 그리기)로 넘기지 않는다 */
    cs.parentNode.insertBefore(d, cs.nextSibling); }
  function addIntro() { var it = $('gIntro'), ok = $('gOk'); if (!it || !ok || it.querySelector('.hwi')) return; var b = document.createElement('button'); b.className = 'hwi'; b.type = 'button'; b.textContent = '🎬 무엇을 하는지 그림으로 먼저 보기';
    b.addEventListener('click', function (e) { e.stopPropagation(); open('m'); }); ok.parentNode.insertBefore(b, ok.nextSibling); }
  function start() { css(); addIntro(); var cf = $('gCfg'); if (cf && window.MutationObserver) new MutationObserver(addCfg).observe(cf, { childList: true }); addCfg();
    addEventListener('keydown', function (e) { if (e.key === 'Escape') { if (TU && TU.classList.contains('on')) TU.classList.remove('on'); else close(); } }); }
  window.gargoHow = { open: open, tour: tour, scenes: SC };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
