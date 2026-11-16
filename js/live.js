/* 데이터 압축지도 — 🏡 여기 살면 얼마 (문답식 · v1 2026-11-15)
   의도 = intent/20261115-live-cost-qa.md · 계산 = js/live-engine.js(LiveEngine) + js/tax-engine.js(TaxEngine) · 규칙 = data/live-rules.json + data/tax-rules.json
   개인 입력(돈·나이·소득)은 이 창 안 변수에만 — localStorage 에도 쓰지 않고 어디로도 보내지 않습니다(창을 닫으면 사라짐)
   열기: 도구 모음 「🏡 여기 살면 얼마」 · 주소 #live=1 · window.tgLive.open() */
(function () {
  'use strict';
  var L = null, T = null, LOADING = null, A = null, STEP = 0, HOMEP = null, WORKP = null, PICK = null;
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function man(x) { x = Math.round(x || 0); if (Math.abs(x) >= 1e8) return (x / 1e8).toFixed(2).replace(/\.?0+$/, '') + '억'; if (Math.abs(x) >= 1e4) return Math.round(x / 1e4).toLocaleString() + '만'; return x.toLocaleString(); }
  function km(p, q) { if (!p || !q) return 0; var dx = (p.lon - q.lon) * 88.4, dy = (p.lat - q.lat) * 111; return Math.sqrt(dx * dx + dy * dy); }
  function fresh() { return { age: '', noHome: 'y', first: 'n', median60: 'u', cash: '', income: '', debt: '', mode: 'all', adj: 'y', didim: 'n', rentDep: '', cm: 'transit', gtx: 'n', red: 'n', car: 'none', price: '', cc: '', light: 'n', ev: 'n', carAge: '', kmMo: '', kmL: '', unit: '', ins: '', park: '', bond: '', mgmt: '', moving: '', legal: '', kmIn: '', rate: '', years: '', rateJ: '' }; }

  function load() {
    if (L && T && window.LiveEngine && window.TaxEngine) return Promise.resolve();
    if (LOADING) return LOADING;
    function js(src, has) { return new Promise(function (ok, no) { if (has()) return ok(); var s = document.createElement('script'); s.src = src; s.onload = function () { ok(); }; s.onerror = function () { no(new Error(src)); }; document.head.appendChild(s); }); }
    function get(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }); }
    LOADING = Promise.all([get('data/live-rules.json?v=2'), get('data/tax-rules.json'), js('js/tax-engine.js?v=2.90.0', function () { return !!window.TaxEngine; }), js('js/live-engine.js?v=3', function () { return !!window.LiveEngine; })])
      .then(function (r) { L = r[0]; T = r[1]; }).catch(function (e) { LOADING = null; throw e; });
    return LOADING;
  }

  function css() {
    if ($('m2dLiveCss')) return; var s = document.createElement('style'); s.id = 'm2dLiveCss';
    s.textContent = '#m2dLive{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom));z-index:11;max-height:70vh;overflow:auto;background:var(--panel,#fff);color:var(--ink,#111);border:1px solid var(--line,#ddd);border-radius:14px;box-shadow:0 6px 24px rgba(0,0,0,.18);padding:10px 12px;display:none;font-size:14px;line-height:1.5}' +
      '#m2dLive.on{display:block}#m2dLive.pick{top:calc(8px + env(safe-area-inset-top));bottom:auto;max-height:none;padding:6px 10px}#m2dLive.pick .ch{margin:4px 0 0}@media (min-width:760px){#m2dLive{right:auto;width:440px;max-height:78vh}}' +
      '#m2dLive h3{margin:0 70px 4px 0;font-size:16px}#m2dLive .x{position:absolute;right:10px;top:8px;height:34px;padding:0 12px;border-radius:10px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit}' +
      '#m2dLive .q{font-weight:700;margin:6px 0}#m2dLive .s{font-size:12px;color:var(--ink2,#555)}#m2dLive .bar{height:4px;background:var(--line,#ddd);border-radius:2px;margin:4px 0 8px}#m2dLive .bar i{display:block;height:4px;background:var(--acc,#2563eb);border-radius:2px}' +
      '#m2dLive .ch{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0}#m2dLive .ch button{flex:1 1 auto;min-height:38px;border:1px solid var(--line,#ddd);border-radius:10px;background:var(--chip,#f3f4f6);color:inherit;padding:0 10px}#m2dLive .ch button.on{border-color:var(--acc,#2563eb);box-shadow:inset 0 0 0 2px var(--acc,#2563eb);font-weight:700}' +
      '#m2dLive label.f{display:block;margin:6px 0}#m2dLive label.f span{display:block;font-size:12.5px;color:var(--ink2,#555)}#m2dLive label.f input{width:100%;box-sizing:border-box;min-height:38px;border:1px solid var(--line,#ddd);border-radius:10px;padding:0 10px;background:var(--chip,#f3f4f6);color:inherit;font-size:15px}' +
      '#m2dLive .nav{display:flex;gap:6px;margin-top:10px}#m2dLive .nav button{flex:1;min-height:40px;border-radius:10px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit;font-weight:700}#m2dLive .nav .go{background:var(--acc,#2563eb);color:#fff;border-color:transparent}' +
      '#m2dLive .cd{border:1px solid var(--line,#ddd);border-radius:12px;padding:8px 10px;margin:8px 0}#m2dLive .cd h4{margin:0 0 4px;font-size:14.5px}#m2dLive .big{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin:4px 0}#m2dLive .big div{background:var(--chip,#f3f4f6);border-radius:8px;padding:4px 6px;text-align:center}#m2dLive .big small{display:block;font-size:11px;color:var(--ink2,#555)}#m2dLive .big b{font-size:15px}' +
      '#m2dLive table{width:100%;border-collapse:collapse;font-size:12.5px}#m2dLive td{padding:2px 0;border-top:1px dashed var(--line,#ddd)}#m2dLive td:last-child{text-align:right;white-space:nowrap}#m2dLive details summary{cursor:pointer;font-size:12.5px;color:var(--acc,#2563eb);margin-top:4px}' +
      '#m2dLive .bd{border-top:1px solid var(--line,#ddd);margin-top:6px;padding-top:6px}#m2dLive .bd table{margin:6px 0 2px}#m2dLive .bd td{text-align:right;white-space:nowrap}#m2dLive .bd td:first-child{text-align:left;white-space:normal}#m2dLive .bd tr.nw td{font-weight:700}#m2dLive .mt{height:8px;background:var(--chip,#eef0f3);border-radius:4px;margin:3px 0 5px;overflow:hidden}#m2dLive .mt i{display:block;height:8px;background:var(--acc,#2563eb)}#m2dLive .mt.k i{background:#d97706}' +
      '#m2dLive .warn{font-size:12px;color:#b45309}:root.dark #m2dLive .warn{color:#fbbf24}#m2dLive .yo{font-size:13px;margin:2px 0}#m2dLive .yo b.y{color:#15803d}#m2dLive .yo b.n{color:#94a3b8}#m2dLive .yo b.u{color:#b45309}';
    document.head.appendChild(s);
  }
  function box() {
    var el = $('m2dLive'); if (el) return el; el = document.createElement('div'); el.id = 'm2dLive'; el.setAttribute('aria-label', '여기 살면 얼마'); document.body.appendChild(el);
    el.addEventListener('click', function (e) {
      e.stopPropagation(); var b = e.target.closest('button'); if (!b) return;
      if (b.classList.contains('x')) return close();
      var k = b.getAttribute('data-k'), v = b.getAttribute('data-v');
      if (k) { take(); A[k] = v; paint(); return; }
      var go = b.getAttribute('data-go');
      if (go === 'next') { take(); STEP++; paint(); } else if (go === 'back') { take(); STEP = Math.max(0, STEP - 1); paint(); } else if (go === 'redo') { STEP = 0; paint(); } else if (go === 'reset') { A = fresh(); HOMEP = WORKP = null; STEP = 0; paint(); }
      else if (go === 'work' || go === 'home') { take(); PICK = go; paint(); }
      else if (go === 'pickok') { var p = window.TGMap2D && window.TGMap2D.here ? window.TGMap2D.here() : null; if (!p || !p.tapped) return say('지도에서 자리를 먼저 누르세요'); if (PICK === 'work') WORKP = p; else HOMEP = p; PICK = null; var cd = document.getElementById('m2dCard'); if (cd) cd.classList.remove('on'); paint(); }
      else if (go === 'pickno') { PICK = null; paint(); }
    });
    return el;
  }
  function say(t) { var s = $('m2dLiveSay'); if (s) s.textContent = t; }
  function take() { var el = $('m2dLive'); if (!el) return; el.querySelectorAll('input[data-f]').forEach(function (i) { A[i.getAttribute('data-f')] = i.value.replace(/[^\d.]/g, ''); }); }
  function ch(k, opts) { return '<div class="ch">' + opts.map(function (o) { return '<button data-k="' + k + '" data-v="' + o[0] + '" class="' + (A[k] === o[0] ? 'on' : '') + '">' + esc(o[1]) + '</button>'; }).join('') + '</div>'; }
  function inp(k, label, unit, hint) { return '<label class="f"><span>' + esc(label) + (unit ? ' (' + esc(unit) + ')' : '') + (hint ? ' · ' + esc(hint) : '') + '</span><input inputmode="decimal" data-f="' + k + '" value="' + esc(A[k]) + '" autocomplete="off"></label>'; }
  function n(k, mul) { var v = parseFloat(A[k]); return isFinite(v) ? v * (mul || 1) : 0; }

  var STEPS = [
    function () { return '<p class="q">① 일하는 곳은?</p><p class="s">지도에서 직장 자리를 누른 뒤 아래 단추 · 모르면 건너뛰기</p><div class="ch"><button data-go="work">🗺 지도에서 직장 고르기</button></div><p class="s">' + (WORKP ? '직장 ✓ ' + WORKP.lat.toFixed(4) + ', ' + WORKP.lon.toFixed(4) : '아직 안 정함') + '</p>'; },
    function () { return '<p class="q">② 살 곳 후보는?</p><p class="s">지도에서 살 집 자리를 누른 뒤 아래 단추</p><div class="ch"><button data-go="home">🗺 지도에서 살 곳 고르기</button></div><p class="s">' + (HOMEP ? '살 곳 ✓ ' + HOMEP.lat.toFixed(4) + ', ' + HOMEP.lon.toFixed(4) + (WORKP ? ' · 직장까지 직선 ' + km(HOMEP, WORKP).toFixed(1) + 'km' : '') : '아직 안 정함') + '</p>' + inp('kmIn', '또는 직장까지 직선 거리', 'km', '자리를 안 찍을 때'); },
    function () { return '<p class="q">③ 누가 사나요?</p>' + inp('age', '만 나이(대표)', '세') + '<p class="s">집이 없나요(세대원 모두 무주택)?</p>' + ch('noHome', [['y', '무주택'], ['n', '집 있음']]) + '<p class="s">생애 처음 집을 사나요?</p>' + ch('first', [['y', '예'], ['n', '아니오']]) + '<p class="s">청년월세 지원 — 청년 가구 소득이 기준 중위소득 60% 이하인가요?</p>' + ch('median60', [['y', '예'], ['n', '아니오'], ['u', '모름']]); },
    function () { return '<p class="q">④ 돈</p>' + inp('cash', '쓸 수 있는 현금', '만 원') + inp('income', '연소득(부부 합산 · 세전)', '만 원') + inp('debt', '이미 내는 대출 원리금', '만 원/달'); },
    function () { var h = '<p class="q">⑤ 집 방식</p>' + ch('mode', [['all', '다 비교'], ['buy', '매매'], ['jeonse', '전세'], ['rent', '월세']]); if (A.mode === 'all' || A.mode === 'buy') h += '<p class="s">매매 — 규제지역(조정대상지역)인가요? 서울 25개 구 전역·경기 일부(국토부 공고 2026-07-01 · tax-rules adjArea)</p>' + ch('adj', [['y', '예'], ['n', '아니오']]) + '<p class="s">디딤돌(정책 구입 대출)도 견줄까요?</p>' + ch('didim', [['y', '예'], ['n', '아니오']]) + inp('rate', '주택담보 금리', '연 %', '비우면 ' + (L.loan.rateBuy[0] * 100).toFixed(1) + '% 가정 · 은행에서 들은 금리를 넣으세요') + inp('years', '갚는 기간', '년', '비우면 ' + L.loan.years[0] + '년 · 원리금 균등'); if (A.mode === 'all' || A.mode === 'jeonse') h += inp('rateJ', '전세대출 금리', '연 %', '비우면 ' + (L.loan.rateJeonse[0] * 100).toFixed(1) + '% 가정'); if (A.mode === 'all' || A.mode === 'rent') h += inp('rentDep', '월세 보증금', '만 원', '비우면 가진 돈의 절반'); return h; },
    function () { return '<p class="q">⑥ 출퇴근</p>' + ch('cm', [['transit', '대중교통'], ['car', '차']]) + (A.cm === 'transit' ? '<p class="s">GTX·광역버스를 타나요?</p>' + ch('gtx', [['n', 'GTX 안 탐'], ['y', 'GTX']]) + ch('red', [['n', '광역버스 안 탐'], ['y', '광역버스']]) : ''); },
    function () { var h = '<p class="q">⑦ 자동차</p>' + ch('car', [['none', '없음·안 삼'], ['have', '이미 있음'], ['new', '신차 살 예정'], ['used', '중고차 살 예정']]); if (A.car !== 'none') { if (A.car !== 'have') h += inp('price', '차값', '만 원') + inp('bond', '채권 즉시매도 비용', '만 원', '모르면 비움'); h += ch('ev', [['n', '기름차'], ['y', '전기차']]) + ch('light', [['n', '경차 아님'], ['y', '경차']]) + (A.ev === 'y' ? '' : inp('cc', '배기량', 'cc')) + (A.car === 'new' ? '' : inp('carAge', '차령', '년')) + inp('kmMo', '한 달 주행', 'km') + inp('kmL', '연비', A.ev === 'y' ? 'km/kWh' : 'km/L') + inp('unit', '연료 단가', A.ev === 'y' ? '원/kWh' : '원/L') + inp('ins', '보험료', '만 원/해', '견적 받은 값') + inp('park', '주차비', '만 원/달'); } return h; },
    function () { return '<p class="q">⑧ 그 밖(모르면 비움)</p>' + inp('mgmt', '관리비', '만 원/달') + inp('moving', '이사비', '만 원') + inp('legal', '법무사 보수(매매)', '만 원') + '<p class="s">🏪 생활시설 거리표(마트·편의점·병원·학교·관공서)는 다음 판에서 살 곳 자리 둘레로 붙입니다.</p>'; }
  ];

  function rng(k, lo, hi, div) { var v = parseFloat(A[k]); return isFinite(v) && v >= lo && v <= hi ? v / div : undefined; }
  function args(mode) {
    var d = HOMEP && WORKP ? km(HOMEP, WORKP) : n('kmIn');
    var c = { buy: A.car === 'have' ? 'none' : A.car, have: A.car === 'have', price: n('price', 1e4), cc: n('cc'), ev: A.ev === 'y', light: A.light === 'y', age: n('carAge'), kmMo: n('kmMo'), kmL: n('kmL'), unit: n('unit'), ins: n('ins', 1e4), park: n('park', 1e4), bond: n('bond', 1e4) };
    if (A.car === 'have') c.buy = 'have';
    return { mode: mode, age: n('age'), noHome: A.noHome === 'y', first: A.first === 'y', median60: A.median60, cash: n('cash', 1e4), incomeYr: n('income', 1e4), debtMo: n('debt', 1e4), adj: A.adj === 'y', metro: true, didim: A.didim === 'y', rentDeposit: A.rentDep === '' ? null : n('rentDep', 1e4), km: d, commuteMode: A.cm, gtx: A.gtx === 'y', red: A.red === 'y', car: A.car === 'none' ? { buy: 'none' } : c, mgmt: n('mgmt', 1e4), moving: n('moving', 1e4), legal: n('legal', 1e4), rate: rng('rate', 0.1, 20, 100), years: rng('years', 1, 50, 1), rateJ: rng('rateJ', 0.1, 20, 100) };
  }
  function steps(st) { return '<table>' + st.map(function (r) { return '<tr><td>' + esc(r[0]) + '</td><td>' + (typeof r[1] === 'number' ? man(r[1]) + '원' : esc(r[1])) + '</td></tr>'; }).join('') + '</table>'; }
  function pct(x) { return x == null ? '—' : (x * 100).toFixed(x < 0.1 ? 1 : 0) + '%'; }
  function burdenBox(s) {
    var b = s.burden; if (!b || !b.loan) return b ? '<div class="bd"><b>대출 없음</b> — 달마다 금융비용 0원</div>' : '';
    var buy = s.mode === 'buy', w = Math.min(100, Math.round(b.ratio * 100)), sh = b.share == null ? null : Math.min(100, Math.round(b.share * 100));
    var h = '<div class="bd"><div><b>💳 빌리는 돈과 달마다 금융비용</b></div>';
    h += '<div class="s">융자비율(' + (buy ? '집값' : '보증금') + ' 중 대출) <b>' + pct(b.ratio) + '</b> · 대출 ' + man(b.loan) + '원 · 금리 ' + (b.rate * 100).toFixed(1) + '%' + (buy ? ' · ' + b.years + '년 원리금 균등' : ' · 이자만(만기 일시)') + '</div><div class="mt"><i style="width:' + w + '%"></i></div>';
    h += '<div class="s">달마다 <b>' + man(b.pay) + '원</b>' + (buy ? '(첫 달 이자 ' + man(b.interest1) + '원)' : '') + (b.share == null ? ' · 소득을 넣으면 소득에서 차지하는 몫을 보여 드립니다' : ' = 세전 월소득 ' + man(b.incMo) + '원의 <b>' + pct(b.share) + '</b>' + (b.debtMo ? ' · 기존 빚까지 ' + pct(b.shareAll) : '')) + '</div>';
    if (sh != null) h += '<div class="mt k"><i style="width:' + sh + '%"></i></div><div class="s">금융비용을 내고 남는 돈(세전) <b>' + man(b.left) + '원/달</b> — 여기서 세금·보험료·생활비·저축이 나갑니다</div>';
    if (buy && b.totalInterest != null) h += '<div class="s">' + b.years + '년 동안 이자 합계 약 ' + man(b.totalInterest) + '원(금리가 그대로일 때)</div>';
    h += '<table><tr><td><b>금리가 바뀌면</b></td><td>달마다</td><td>차이</td><td>소득 몫</td></tr>' + b.rates.map(function (q) { return '<tr' + (q.d === 0 ? ' class="nw"' : '') + '><td>' + (q.rate * 100).toFixed(1) + '%' + (q.d === 0 ? ' (지금 가정)' : '') + '</td><td>' + man(q.pay) + '원</td><td>' + (q.d === 0 ? '—' : (q.diff > 0 ? '+' : '−') + man(Math.abs(q.diff)) + '원') + '</td><td>' + pct(q.share) + '</td></tr>'; }).join('') + '</table>';
    if (b.caps) h += '<table><tr><td><b>부담을 이만큼으로 묶으면</b></td><td>대출</td><td>집값</td><td>달마다</td></tr>' + b.caps.map(function (q) { return '<tr><td>소득의 ' + Math.round(q.share * 100) + '%' + (q.tight ? ' (한도가 먼저 걸림)' : '') + '</td><td>' + man(q.loan) + '원</td><td>' + man(q.price) + '원</td><td>' + man(q.pay) + '원</td></tr>'; }).join('') + '</table>';
    h += '<div class="s">금리 눈금·부담 눈금은 견줘 보려고 둔 설계값입니다(전망·권고 기준이 아닙니다). 소득은 세전이라 실제로 손에 남는 돈은 더 적습니다. 변동금리면 달마다 내는 돈이 위 표처럼 움직입니다.</div></div>';
    return h;
  }
  function card(title, s) {
    var h = '<div class="cd"><h4>' + esc(title) + '</h4>';
    var hd = s.mode === 'buy' ? '집값 최대 <b>' + man(s.house.price) + '원</b>' : s.mode === 'jeonse' ? '보증금 최대 <b>' + man(s.house.deposit) + '원</b>' : '보증금 ' + man(s.house.deposit) + '원 · 월세 최대 <b>' + man(s.house.monthlyMax) + '원</b>';
    h += '<div>' + hd + '</div><div class="big"><div><small>처음</small><b>' + man(s.first) + '</b></div><div><small>매달</small><b>' + man(s.monthly) + '</b></div><div><small>해마다</small><b>' + man(s.yearly) + '</b></div></div>';
    if (s.house.loan && s.house.loan.why) h += '<div class="s">대출을 묶은 조건: <b>' + esc(s.house.loan.why) + '</b></div>'; else if (s.house.why) h += '<div class="s">대출을 묶은 조건: <b>' + esc(s.house.why) + '</b></div>';
    h += burdenBox(s);
    h += '<details><summary>계산 과정</summary>' + steps(s.house.steps || []);
    if (s.mode === 'buy' && s.house.loan.lim) h += '<p class="s">한도 후보: ' + s.house.loan.lim.map(function (q) { return esc(q[0]) + ' ' + man(q[1]) + '원'; }).join(' · ') + '</p>';
    if (s.mode === 'buy' && s.house.yearly) h += '<p class="s">해마다 = 재산세 ' + man(s.house.yearly.prop) + '원 + 종부세 ' + man(s.house.yearly.jbs) + '원(공시가격 = 집값 × 0.7 가정)</p>';
    h += '</details></div>'; return h;
  }
  function result() {
    var modes = A.mode === 'all' ? ['buy', 'jeonse', 'rent'] : [A.mode], name = { buy: '🏠 매매', jeonse: '🔑 전세', rent: '📅 월세' }, h = '<p class="q">결과 — 같은 답으로 견줘 봄</p>', warn = [], E = window.LiveEngine, last;
    modes.forEach(function (m) { var s = E.sheet(L, T, window.TaxEngine, args(m)); last = s; h += card(name[m], s); warn = warn.concat(s.warn); });
    var y = last.youth.list; h += '<div class="cd"><h4>🎓 청년 지원 후보</h4>' + y.map(function (x) { return '<p class="yo"><b class="' + (x.ok === true ? 'y' : x.ok === false ? 'n' : 'u') + '">' + (x.ok === true ? '✓ 후보' : x.ok === false ? '— 아님' : '? 확인') + '</b> ' + esc(x.name) + '<br><span class="s">' + esc(x.why) + '</span></p>'; }).join('') + '<p class="s">최종 자격은 주택도시기금·복지로·마이홈 공고가 정합니다</p></div>';
    var c = last.commute; if (c) h += '<div class="cd"><h4>🚇 출퇴근(근사)</h4><div>길 ' + c.roadKm + 'km · 대중교통 약 <b>' + c.transitMin + '분</b> · 차 약 <b>' + c.carMin + '분</b>(편도)</div><div class="s">요금 ' + c.fare.toLocaleString() + '원 × 왕복 × ' + c.days + '일 = ' + man(c.transitRaw) + '원 → K-패스 ' + man(c.kpass) + '원 · 정액형 ' + man(c.flat) + '원 → <b>' + man(c.transitMo) + '원/달</b>' + (A.cm === 'car' ? ' (차로 다니면 매달에 안 더함)' : '') + '</div></div>';
    if (last.car) h += '<div class="cd"><h4>🚗 자동차</h4><div class="big"><div><small>처음</small><b>' + man(last.car.first) + '</b></div><div><small>매달</small><b>' + man(last.car.monthly) + '</b></div><div><small>해마다(세금)</small><b>' + man(last.car.yearly) + '</b></div></div><details><summary>계산 과정</summary>' + steps(last.car.steps) + '</details></div>';
    warn = warn.filter(function (w, i, a) { return a.indexOf(w) === i; });
    h += '<details><summary class="warn">⚠ 확인 안 된 규칙·가정 ' + warn.length + '개 — 펼쳐 보기</summary><ul class="warn">' + warn.map(function (w) { return '<li>' + esc(w) + '</li>'; }).join('') + '</ul></details>';
    h += '<p class="s">상담·심사가 아닙니다 — 실제 한도·금리·자격은 은행·기금·보증기관 심사와 공고가 정합니다. 규칙 기준일: ' + esc(L.made) + (L.checked ? ' · 1차 확인 ' + esc(L.checked) : ' · <b class="warn">1차 출처 대조 전</b>') + '</p>';
    h += '<div class="nav"><button data-go="redo">답 고치기</button><button data-go="reset">처음부터</button></div>';
    return h;
  }
  function paint() {
    var el = box(), N = STEPS.length, h = '<button class="x">닫기</button><h3>🏡 여기 살면 얼마</h3>';
    el.classList.toggle('pick', !!PICK);
    if (PICK) { el.innerHTML = '<div><b>🗺 지도에서 ' + (PICK === 'work' ? '직장' : '살 곳') + ' 자리를 누르세요</b></div><div class="ch"><button class="go" data-go="pickok">✓ 누른 자리로</button><button data-go="pickno">취소</button></div><p class="s" id="m2dLiveSay"></p>'; return; }
    if (!L) { el.innerHTML = h + '<p class="s">규칙을 받는 중…</p>'; return; }
    if (STEP >= N) { try { el.innerHTML = h + result(); } catch (e) { el.innerHTML = h + '<p class="warn">계산하다 멈췄습니다: ' + esc(e.message) + '</p><div class="nav"><button data-go="redo">답 고치기</button></div>'; } return; }
    h += '<div class="bar"><i style="width:' + Math.round(STEP / N * 100) + '%"></i></div>' + STEPS[STEP]() + '<p class="s" id="m2dLiveSay"></p><div class="nav">' + (STEP ? '<button data-go="back">← 앞</button>' : '') + '<button class="go" data-go="next">' + (STEP === N - 1 ? '결과 보기' : '다음 →') + '</button></div><p class="s">입력은 이 창 안에서만 쓰고 저장·전송하지 않습니다</p>';
    el.innerHTML = h;
  }
  function open() { css(); if (!A) A = fresh(); var el = box(), cd = $('m2dCard'); if (cd) cd.classList.remove('on'); el.classList.add('on'); paint(); load().then(paint).catch(function (e) { el.innerHTML = '<button class="x">닫기</button><h3>🏡 여기 살면 얼마</h3><p class="warn">규칙 파일을 못 받았습니다(' + esc(e.message) + ') — 통신을 확인하고 다시</p>'; }); }
  function close() { var el = $('m2dLive'); if (el) el.classList.remove('on'); }
  if (/[#&]live=1(?!\d)/.test(location.hash)) setTimeout(open, 600);
  window.tgLive = { open: open, close: close };
})();
