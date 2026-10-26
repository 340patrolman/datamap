/* 데이터 압축지도 — 🧩 엮임 보기 (팔란티어 방식: 대상 하나에서 이어진 것을 따라가며 「연결 이유 · 근거 · 결과 · 가능성」을 같이 본다)
   소유자 2026-10-24 「동적인 연결이 눈에 보일 줄 알았어 — 근거와 연결 이유, 결과, 가능성 등 · 전혀 새로운 연결이라 완벽하지 않아도 된다 · 메뉴 단추를 만들고 과감하게」
   자료 = ontology-core/data/core-seocho.json(서초 전체 코어 · build.py · 값은 원자료 그대로) + query.js 질문 함수 + schema-ext.json(관계 뜻)
   네 칸: 연결 이유 = 무엇으로 이었나(자리·때·코드 · 거리) · 근거 = 원자료 파일·기준일 · 결과 = 이어진 대상에서 얻는 값 · 가능성 = 등급 A~E(확실 → 가설)
   「💡 엮으면 보이는 것」은 이은 것들을 겹쳐 본 짐작(가설 D) — 판단은 사람이 한다 · 섞은 점수 없음
   「⏱ 지금 이 시각」은 지금 요일·시각에 맞춘 평소 모양(실시간 값이 아니다) + 오늘 잡힌 행사
   기록·전송 없음(이 기기에서 읽기만) · 도달 시간·출동 지연은 공개 코어에 없다(소유자 2026-10-23 비공개)
   열기: 도구 모음 「🧩 엮임 보기」 · 주소 #lnk=1(&id=INT-번호 | &ll=위도,경도) · window.tgLink.open({id}|{lat,lon}) */
(function () {
  'use strict';
  var CORE = 'ontology-core/data/core-seocho.json', QJS = 'ontology-core/query.js?v=3', SCH = 'ontology-core/schema-ext.json', IDXF = 'ontology-core/data/core-six/index.json';
  var GUN = { '11650': '서초구', '11680': '강남구', '11710': '송파구', '11590': '동작구', '11620': '관악구', '11170': '용산구' }, QS = {}, AREA = null, IDX = null, IDXL = null, IGU = {};   /* 여섯 구 — 서초는 전체 코어 · 다른 다섯은 core-six 를 구로 나눈 것(split-gu.py) */
  var Q = null, SC = null, LOAD = null, ST = { id: null, back: [], more: {}, q: '' };
  var LOGK = 'tg_map2d_lnk_log', PII = [/01[016789][-\s]?\d{3,4}[-\s]?\d{4}/, /\d{6}[-\s]?[1-4]\d{6}/, /\d{2,3}\s?[가-힣]\s?\d{4}/];   /* 가설 현장 판정 — 이 기기에만 · 사람·차량 안 씀 */
  function logGet() { try { return JSON.parse(localStorage.getItem(LOGK) || '[]'); } catch (e) { return []; } }
  function logSet(a) { try { localStorage.setItem(LOGK, JSON.stringify(a)); return true; } catch (e) { return false; } }
  function hkey(id, t) { return id + '|' + String(t).split(' — ')[0]; }
  var LOOPS = null, SIMD = null, ACTK = 'tg_map2d_lnk_act';   /* 현장 조치 기록(고리) — 이 기기에만 · 적을 때 네 변 속도를 「조치 전」으로 같이 남긴다 */
  function actGet() { try { return JSON.parse(localStorage.getItem(ACTK) || '[]'); } catch (e) { return []; } }
  function actSet(a) { try { localStorage.setItem(ACTK, JSON.stringify(a)); return true; } catch (e) { return false; } }   /* 막힘 고리(data/onto-loops.json · 소유자가 짚은 교착 자리) · 시뮬 구역 자료(data/sim-<구역>.json — 조치 목록) */
  var LIVE = null, LIVEAT = 0, NORM = null, NORMING = false;   /* 실시간 세 장(돌발 둘 · 통행속도) — 3분마다 다시(sw 가 네트워크 먼저 · 주소에 시각을 안 붙여 보관함이 쌓이지 않게) · 평소 속도(4MB)는 누를 때만 */
  var NAV = { INT: 1, DNG: 1, STN: 1, TRD: 1, PBX: 1, STA: 1, EVT: 1, ACC: 1, VIO: 1, LAW: 1, PREC: 1, ACT: 1 };   /* 사고 → 위반 → 법규 → 판례(T-Book) 까지 걸어갈 수 있게 */
  var TN = { INT: '교차로', DNG: '행정동', STN: '지하철역', TRD: '상권', PBX: '지구대·파출소', STA: '경찰서', EVT: '사건', ACC: '사고(10년)', ACL: '사고 칸', CAM: '단속 카메라', ATT: '시설', PLC: '250m 칸', APR: '들어오는 길', RD: '도로 구간', ACT: '교통과 조치', REC: '조치 기록', VIO: '위반 유형', LAW: '법규', PREC: '판례', RULE: '규칙', FK: '현장 판단', SCN: '시뮬로 시험해 본 대책' };
  var KEY = { 속함: '자리 — 교차로가 그 동 경계 안', 근처: '자리 + 때 — 둘레 반지름 안에서 그날 일어난 일', 흔적: '자리 + 때 — 그 해 침수 흔적 100m 안', 가까움: '자리 — 300m 안', 보유: '자리 — 100m 안', 들어감: '자리 — 교차로가 든 250m 칸', 지남: '자리 — 길이 지나는 250m 칸', 사고칸: '자리 — 길 가운데 50m 안 사고 칸', 품음: '자리 — 상권 경계 안', 가까운교차로: '자리 — 역에서 300m 안', 근처역: '자리 + 때 — 행사 자리에서 500m(큰 공연장 1km) 안 역', 가까운지구대: '자리 + 코드 — 관할서 지구대 중 가장 가까운 곳', 인접: '코드 — 신호망에서 이웃한 교차로', 관할: '코드 — 별표2 관할 × 행정동 + 현장 기준', 소속: '코드 — 소속 경찰서', 발생: '자리 — 교차로 70m 안 사고 칸 묶음', 주요원인: '코드 — 사고 칸의 주 위반', 근거: '코드 — 위반 → 법 조문', 해석: '코드 — 조문 → 판례', 들어오는길: '코드 — 표준노드링크 방향', 이룸: '코드 — ITS 링크 번호', 들어감동: '코드 — 원자료의 행정동 이름', 대상: '코드 — 교통과 조치의 교차로 번호', 근거기록: '코드 — 조치의 기록', 뒷받침: '코드 — 규칙을 받친 현장 판단' };
  var GR = { A: ['확실', '원자료 코드·번호가 같다', 5], B: ['높음', '자리·경계를 맞춰 이었다', 4], C: ['근사', '거리 반지름으로 어림해 이었다', 3], D: ['추정', '이은 것들을 겹쳐 본 짐작', 2], E: ['가설', '아직 확인하지 않은 생각', 1] };

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function fmt(n) { return n == null || n === '' ? '—' : String(Math.round(+n)).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function sum(a) { var s = 0; (a || []).forEach(function (v) { s += +v || 0; }); return s; }
  function m(la1, lo1, la2, lo2) { return Math.sqrt(Math.pow((lo1 - lo2) * 88400, 2) + Math.pow((la1 - la2) * 111000, 2)); }
  function today() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function ago(days) { var d = new Date(Date.now() - days * 864e5); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function O(id) { return Q && Q.O[id]; }
  function nm(o) { if (!o) return '—'; if (o.t === 'ACC' && Q) { var i0 = Q.back(o.id, '발생')[0]; return '사고 10년 — ' + (i0 ? (i0.o.nm || i0.o.id) : o.id); } return o.nm || o.title || o.what || o.text || o.no || o.id; }
  function won(v) { v = +v; if (!v) return '—'; return v >= 10000 ? (Math.round(v / 1000) / 10) + '억' : fmt(v) + '만'; }

  function css() {
    if ($('m2dLnkCss')) return; var s = document.createElement('style'); s.id = 'm2dLnkCss';
    s.textContent = '#m2dLnk{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom));z-index:40;max-height:78vh;overflow:auto;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:14px;padding:12px 14px 10px;box-shadow:0 8px 28px rgba(0,0,0,.25);display:none;font-size:13.5px;line-height:1.5}' +
      '#m2dLnk.on{display:block}@media (min-width:760px){#m2dLnk{right:auto;width:460px;max-height:80vh}}' +
      '#m2dLnk h3{margin:0 76px 2px 0;font-size:16px}#m2dLnk .lx{position:absolute;right:10px;top:8px;height:34px;padding:0 12px;border-radius:10px;border:1px solid var(--line);background:var(--chip);color:var(--ink);cursor:pointer}' +
      '#m2dLnk .sub{font-size:12px;color:var(--ink2);margin:0 0 6px}#m2dLnk .bar{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 8px}#m2dLnk .bar button,#m2dLnk .sb{min-height:34px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);font-size:12.5px;padding:0 10px;cursor:pointer}' +
      '#m2dLnk input[type=search]{width:100%;box-sizing:border-box;min-height:38px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);padding:0 10px;font-size:14px}' +
      '#m2dLnk .pick{list-style:none;margin:6px 0;padding:0}#m2dLnk .pick li{border-top:1px solid var(--line)}#m2dLnk .pick button{width:100%;text-align:left;background:none;border:0;color:var(--ink);padding:8px 2px;font-size:13.5px;cursor:pointer}#m2dLnk .pick small{color:var(--ink2)}' +
      '#m2dLnk svg{display:block;width:100%;height:auto;margin:2px 0 4px}#m2dLnk svg text{font-size:11px;fill:var(--ink);paint-order:stroke;stroke:var(--panel);stroke-width:3px}#m2dLnk svg g.gn{cursor:pointer}' +
      '#m2dLnk .lg{display:flex;gap:10px;flex-wrap:wrap;font-size:11.5px;color:var(--ink2);margin-bottom:6px}#m2dLnk .lg i{display:inline-block;width:20px;border-top:3px solid #16a34a;vertical-align:middle;margin-right:4px}#m2dLnk .lg i.c{border-top:2px dashed #d97706}#m2dLnk .lg i.d{border-top:2px dotted #94a3b8}' +
      '#m2dLnk h4{margin:12px 0 4px;font-size:14px}#m2dLnk .note{font-size:11.5px;color:var(--ink2);margin:2px 0 6px}' +
      '#m2dLnk .now{border:1px solid #0ea5e9;border-radius:12px;padding:8px 10px;background:rgba(14,165,233,.07)}#m2dLnk .now li{margin:2px 0}#m2dLnk .now ul,#m2dLnk .hy ul{margin:2px 0;padding-left:18px}' +
      '#m2dLnk .sg2{margin:6px 0 2px;font-size:13px}#m2dLnk details.acts{border-top:1px dashed var(--line);margin-top:6px;padding-top:4px}#m2dLnk details.acts>summary{cursor:pointer;font-weight:700;font-size:13px}#m2dLnk details.acts select{min-height:34px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);font-size:12.5px;max-width:100%}#m2dLnk .loop{border:1px solid #7c3aed;border-radius:12px;padding:8px 10px;background:rgba(124,58,237,.06)}#m2dLnk .loop>div{margin:3px 0}#m2dLnk .loop button.go{min-height:26px;border:1px solid var(--acc);color:var(--acc);background:none;border-radius:999px;padding:0 8px;font-size:11.5px;margin-left:4px}#m2dLnk .live{border:1px solid #dc2626;border-radius:12px;padding:8px 10px;background:rgba(220,38,38,.06)}#m2dLnk .live>div{margin:3px 0}#m2dLnk .live ul{margin:2px 0;padding-left:18px}#m2dLnk .live li{margin:2px 0}#m2dLnk .live .sb{min-height:28px;font-size:12px;margin-left:4px}#m2dLnk a.tb{font-size:12px;color:#1d4ed8;white-space:nowrap}#m2dLnk a.wi{display:inline-block;margin-top:6px;padding:6px 10px;border:1px solid #7c3aed;border-radius:999px;color:#7c3aed;font-size:12.5px;text-decoration:none}#m2dLnk .hv{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px;padding-top:6px;border-top:1px dashed var(--line)}#m2dLnk .hv .sb{min-height:32px}#m2dLnk .hq{font-size:12px;color:var(--ink2)}#m2dLnk .hb{font-size:12px;padding:2px 8px;border-radius:999px;background:var(--chip)}#m2dLnk .hb.ok{background:rgba(22,163,74,.15);color:#15803d}#m2dLnk .hb.no{background:rgba(220,38,38,.12);color:#b91c1c}#m2dLnk .lg2{margin:2px 0;padding-left:18px;font-size:12.5px}#m2dLnk .hy{border:1px dashed #d97706;border-radius:12px;padding:8px 10px;margin:6px 0;background:rgba(217,119,6,.06)}#m2dLnk .hy b.t{font-size:14px}' +
      '#m2dLnk .k4{display:grid;grid-template-columns:62px minmax(0,1fr);gap:1px 8px;font-size:12.5px;margin-top:4px}#m2dLnk .k4 span{color:var(--ink2)}#m2dLnk .k4 div{min-width:0;overflow-wrap:anywhere}' +
      '#m2dLnk details.rel{border:1px solid var(--line);border-radius:12px;margin:6px 0;padding:0 10px}#m2dLnk details.rel>summary{cursor:pointer;padding:8px 0;font-weight:700;list-style:none}#m2dLnk details.rel>summary::-webkit-details-marker{display:none}#m2dLnk details.rel>summary small{font-weight:400;color:var(--ink2)}' +
      '#m2dLnk .lk{border-top:1px solid var(--line);padding:6px 0}#m2dLnk .lk .t{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}#m2dLnk .lk .t b{font-size:13.5px}#m2dLnk .lk button.go{margin-left:auto;min-height:30px;border:1px solid var(--acc);color:var(--acc);background:none;border-radius:999px;padding:0 10px;font-size:12px;cursor:pointer}' +
      '#m2dLnk .gd{display:inline-flex;gap:2px;vertical-align:middle;margin-right:4px}#m2dLnk .gd i{width:7px;height:7px;border-radius:2px;background:var(--line)}#m2dLnk .gd i.f{background:#16a34a}#m2dLnk .gd.c i.f{background:#d97706}#m2dLnk .gd.d i.f{background:#94a3b8}' +
      '#m2dLnk .src{margin-top:10px;font-size:11.5px;color:var(--ink2)}#m2dLnk .wait{padding:16px 0;color:var(--ink2)}';
    document.head.appendChild(s);
  }
  function box() { var el = $('m2dLnk'); if (el) return el; el = document.createElement('div'); el.id = 'm2dLnk'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', '엮임 보기'); document.body.appendChild(el); el.addEventListener('click', onClick); el.addEventListener('input', onInput); return el; }

  function loadIdx() {
    if (IDXL) return IDXL;
    IDXL = fetch(IDXF).then(function (r) { return r.json(); }).then(function (j) { IDX = j; j.items.forEach(function (it) { IGU[it[0]] = it[4]; }); return j; }).catch(function (e) { IDXL = null; throw e; });
    return IDXL;
  }
  function load(gu) {
    gu = gu || '11650';
    function js() { return window.OntoCore ? Promise.resolve() : new Promise(function (ok, no) { var s = document.createElement('script'); s.src = QJS; s.onload = ok; s.onerror = no; document.head.appendChild(s); }); }
    if (QS[gu] && QS[gu].then) return QS[gu].then(function (q) { if (AREA !== gu) NORM = null; Q = q; AREA = gu; return q; });
    QS[gu] = js().then(function () { return Promise.all([fetch(gu === '11650' ? CORE : 'ontology-core/data/core-six/' + gu + '.json').then(function (r) { return r.json(); }), SC ? SC : fetch(SCH).then(function (r) { return r.json(); }).catch(function () { return null; })]); })
      .then(function (a) { var q = new window.OntoCore(a[0]); SC = a[1]; return q; })
      .catch(function (e) { QS[gu] = null; throw e; });
    return QS[gu].then(function (q) { if (AREA !== gu) NORM = null; Q = q; AREA = gu; return q; });
  }

  /* ---------- 대상 한 줄 요약 = 「결과」 칸 ---------- */
  function accOf(intId) { var a = Q.follow(intId, '발생')[0]; return a ? a.o : null; }
  function summ(o) {
    if (!o) return ''; var h = new Date().getHours(), we = [0, 6].indexOf(new Date().getDay()) >= 0;
    switch (o.t) {
      case 'INT': var A = accOf(o.id), t = A ? sum(A.years) : 0; return (o.dongnm ? o.dongnm + ' · ' : '') + (A ? '사고 10년 ' + fmt(t) + '건 · 밤 ' + fmt(A.night) + ' · 보행자 ' + fmt(A.ped) : '둘레 70m 사고 칸 없음');
      case 'ACC': var tt = sum(o.years); return '10년 ' + fmt(tt) + '건(' + o.y0 + '~) · 사망 ' + fmt(o.dead) + ' · 중상 ' + fmt(o.serious) + ' · 밤 ' + fmt(o.night) + ' · 보행자 ' + fmt(o.ped);
      case 'ACL': return '10년 ' + fmt(sum(o.years)) + '건 · 주 위반 ' + esc(o.mvnm || '—');
      case 'DNG': return '주민 ' + fmt(o.res) + ' · 일하는 사람 ' + fmt(o.wk) + ' · 가게 ' + fmt(o.stN) + (o.stOpen4 != null ? '(1년 개업 ' + fmt(o.stOpen4) + ' · 폐업 ' + fmt(o.stClose4) + ')' : '');
      case 'STA': return (o.tel ? '대표 ' + o.tel + ' · ' : '') + esc(o.sido || '');
      case 'PBX': return esc(o.kind || '') + ' · ' + esc(o.addr || '');
      case 'CAM': return '제한 ' + (o.lim || '—') + 'km/h · ' + esc(o.road || '') + ' · ' + esc(o.place || '');
      case 'ATT': return esc(o.kind || '') + (o.nm ? ' · ' + esc(o.nm) : '');
      case 'PLC': var a2 = we ? o.we : o.wd; return a2 ? '지금 ' + h + '시 평소 ' + fmt(a2[h]) + '명 머묾(' + (we ? '주말' : '평일') + ' · 하루 가장 많을 때 ' + fmt(Math.max.apply(null, a2)) + '명)' : '사람 자료 없음';
      case 'APR': return esc(o.frm || '') + ' · ' + esc(o.nm || '');
      case 'RD': return esc(o.nm || '') + ' · 제한 ' + (o.lim || '—') + ' · ' + (o.ln || '—') + '차로' + (+o.fy ? ' · 침수 흔적 ' + o.fy + '해' : '') + (+o.dt > 0 ? ' · 막히면 돌아가는 부담 ' + fmt(o.dt) + '초' : +o.dt === -1 ? ' · 돌아갈 길 없음' : '');
      case 'EVT': return esc(o.kind || '') + (o.sub ? '·' + esc(o.sub) : '') + ' · ' + esc(o.d0 || '') + (o.d1 && o.d1 !== o.d0 ? '~' + esc(o.d1) : '') + (o.n ? ' · ' + fmt(o.n) + (o.kind === '공연' ? '석' : o.kind === '침수' ? '곳' : '명') : '');
      case 'STN': var hr = o.hr ? o.hr[h] : null; return '하루 승하차 ' + fmt(o.day) + '명' + (hr != null ? ' · 지금 ' + h + '시 몫 ' + hr + '(1 = 평소 한 시간)' : '') + (o.lines ? ' · ' + esc(o.lines.join(',')) : '');
      case 'TRD': var g = o.sales && o.salesPrev ? Math.round((o.sales / o.salesPrev - 1) * 100) : null; return esc(o.se || '') + ' · 한 달 매출 ' + won(o.sales) + '원' + (g != null ? '(1년 전보다 ' + (g >= 0 ? '+' : '') + g + '%)' : '') + ' · 점포 ' + fmt(o.stores);
      case 'ACT': return esc(o.what || '') + (o.ym ? ' · ' + esc(o.ym) : '');
      case 'VIO': return esc(o.nm || '');
      case 'LAW': return esc(o.meta || '') + ' · ' + esc(o.penalty || '');
      case 'PREC': return esc(o.court || '') + ' ' + esc(o.date || '') + ' · ' + esc(o.nm || '');
      case 'RULE': return esc(o.d || '');
      case 'SCN': var b0 = o.base || {}, r0 = o.res || {}, dv = b0.delayVh ? Math.round((r0.delayVh - b0.delayVh) / b0.delayVh * 100) : null, hm = function (x) { return x == null ? '—' : Math.floor(x / 3600) + ':' + ('0' + Math.round(x % 3600 / 60)).slice(-2); };
        if (!b0.delayVh) return esc(o.date || '') + ' · 총 지체 ' + fmt(r0.delayVh) + ' · 갇힘 ' + fmt(r0.trappedMax) + ' · 해소 ' + hm(r0.clearT) + (o.match ? ' · 실측 맞음 ' + o.match.hit + '/' + o.match.n : '') + ' · 견줄 기준 판 · 개념 시연 · 수요는 설계값';
        return esc(o.date || '') + ' · 총 지체 ' + fmt(b0.delayVh) + '→' + fmt(r0.delayVh) + (dv != null ? '(' + (dv > 0 ? '+' : '') + dv + '%)' : '') + ' · 갇힘 ' + fmt(b0.trappedMax) + '→' + fmt(r0.trappedMax) + ' · 해소 ' + hm(b0.clearT) + '→' + hm(r0.clearT) + (o.match ? ' · 실측 맞음 ' + o.match.hit + '/' + o.match.n : '') + (o.conflict ? ' · ⚠ ' + esc(o.conflict) : '') + ' · 개념 시연 · 수요는 설계값';
      case 'FK': return '「' + esc(String(o.said || '').slice(0, 60)) + '…」 ' + esc(o.date || '');
      default: return '';
    }
  }
  /* T-Book 이 출발점(소유자 2026-10-25 「다 하나로 · 다 파생」) — 법령·범칙금·판례 정본은 T-Book: 위반·법규·판례에서 T-Book 그 화면으로 */
  var TBK = 'https://340patrolman.github.io/traffic-app/#';
  function tbLink(o) { var pg = o && (o.t === 'LAW' || o.t === 'VIO') ? 'laws' : o && o.t === 'PREC' ? 'precedent' : null; return pg ? ' <a class="tb" target="_blank" rel="noopener" href="' + TBK + pg + '">📘 T-Book ' + (pg === 'laws' ? '법령자료' : '판례') + ' ›</a>' : ''; }
  function asofOf(src) { var A = Q.core.asof || {}, k = Object.keys(A).filter(function (f) { return String(src || '').indexOf(f) >= 0; })[0]; return k ? A[k] : null; }
  function gdots(g) { var x = GR[g] || null, n = x ? x[2] : 0, c = g === 'C' ? ' c' : g === 'D' || g === 'E' ? ' d' : ''; var s = '<span class="gd' + c + '" aria-hidden="true">'; for (var i = 0; i < 5; i++) s += '<i class="' + (i < n ? 'f' : '') + '"></i>'; return s + '</span>'; }
  function poss(g) { var x = GR[g]; return x ? gdots(g) + '<b>' + g + ' ' + x[0] + '</b> — ' + x[1] : '— (등급 없음)'; }
  function why(rel, p) { var k = KEY[rel] || (SC && SC.linkTypes && SC.linkTypes[rel] ? SC.linkTypes[rel].name : rel); var d = p && p.d != null ? ' · ' + fmt(p.d) + 'm' : ''; return esc(k) + d; }
  function k4(rel, p, o, dir) {
    var src = p && p.src ? p.src : (SC && SC.linkTypes && SC.linkTypes[rel] ? (SC.linkTypes[rel].from || '') + '→' + (SC.linkTypes[rel].to || '') : ''), af = asofOf(src);
    return '<div class="k4"><span>연결 이유</span><div>' + why(rel, p) + '</div><span>근거</span><div>' + esc(src || '—') + (af ? ' · <i>' + esc(af) + '</i>' : '') + '</div><span>결과</span><div>' + (summ(o) || '—') + tbLink(o) + '</div><span>가능성</span><div>' + poss(p && p.g) + '</div></div>';
  }

  /* ---------- 관계 묶음 ---------- */
  function groups(id) {
    var G = {}, order = [];
    (Q.out[id] || []).forEach(function (e) { var k = '→' + e[1]; if (!G[k]) { G[k] = { rel: e[1], dir: 1, items: [] }; order.push(k); } G[k].items.push({ o: Q.O[e[2]], p: e[3] || {} }); });
    (Q.inn[id] || []).forEach(function (e) { var sy = e[1] === '인접', k = (sy ? '→' : '←') + e[1]; if (!G[k]) { G[k] = { rel: e[1], dir: sy ? 1 : -1, items: [] }; order.push(k); } if (sy && G[k].items.some(function (x) { return x.o && x.o.id === e[0]; })) return; G[k].items.push({ o: Q.O[e[0]], p: e[3] || {} }); });   /* 인접은 두 방향이 같은 뜻 — 한 묶음 */
    return order.map(function (k) { var g = G[k]; g.key = k; g.items = g.items.filter(function (x) { return x.o; });
      g.items.sort(function (a, b) { var da = a.p.d == null ? 1e9 : a.p.d, db = b.p.d == null ? 1e9 : b.p.d; if (g.rel === '근처') return String(b.o.d0) < String(a.o.d0) ? -1 : 1; return da - db || (nm(a.o) < nm(b.o) ? -1 : 1); });
      var t = g.items[0] ? g.items[0].o.t : ''; g.t = t; g.best = g.items.reduce(function (b, x) { return x.p.g && (!b || x.p.g < b) ? x.p.g : b; }, null); return g; }).filter(function (g) { return g.items.length; });
  }
  function gname(g) { var t = TN[g.t] || g.t; return (g.dir > 0 ? '' : '← ') + g.rel + ' · ' + t; }

  /* ---------- 연결 그림 ---------- */
  function graph(o, GS) {
    var W = 360, H = 250, cx = W / 2, cy = H / 2, R = 92, n = GS.length; if (!n) return '';
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="' + esc(nm(o)) + '에 이어진 대상 ' + n + '갈래">';
    GS.forEach(function (g, i) { var a = -Math.PI / 2 + i * 2 * Math.PI / n, x = cx + R * 1.25 * Math.cos(a), y = cy + R * 0.95 * Math.sin(a), b = g.best || 'D',
      col = b <= 'B' ? '#16a34a' : b === 'C' ? '#d97706' : '#94a3b8', da = b <= 'B' ? '' : b === 'C' ? ' stroke-dasharray="6 4"' : ' stroke-dasharray="2 4"', w = Math.min(6, 1.5 + Math.log(1 + g.items.length));
      s += '<line x1="' + cx + '" y1="' + cy + '" x2="' + x.toFixed(1) + '" y2="' + y.toFixed(1) + '" stroke="' + col + '" stroke-width="' + w.toFixed(1) + '"' + da + ' opacity=".85"/>'; });
    GS.forEach(function (g, i) { var a = -Math.PI / 2 + i * 2 * Math.PI / n, x = cx + R * 1.25 * Math.cos(a), y = cy + R * 0.95 * Math.sin(a), r = Math.min(16, 7 + Math.sqrt(g.items.length) * 1.6);
      s += '<g class="gn" data-jump="' + esc(g.key) + '"><circle cx="' + x.toFixed(1) + '" cy="' + y.toFixed(1) + '" r="' + r.toFixed(1) + '" fill="var(--chip)" stroke="var(--ink2)"/><text x="' + x.toFixed(1) + '" y="' + (y + r + 11).toFixed(1) + '" text-anchor="middle">' + esc((TN[g.t] || g.t) + ' ' + g.items.length) + '</text></g>'; });
    var cn = String(nm(o)), c1 = cn.length > 5 ? cn.slice(0, 5) : cn, c2 = cn.length > 5 ? cn.slice(5, 10) + (cn.length > 10 ? '…' : '') : '';
    s += '<circle cx="' + cx + '" cy="' + cy + '" r="30" fill="var(--acc)" opacity=".92"/><text x="' + cx + '" y="' + (cy + (c2 ? -2 : 4)) + '" text-anchor="middle" style="fill:#fff;stroke:none;font-weight:700">' + esc(c1) + '</text>' + (c2 ? '<text x="' + cx + '" y="' + (cy + 12) + '" text-anchor="middle" style="fill:#fff;stroke:none;font-weight:700">' + esc(c2) + '</text>' : '') + '</svg>';
    return s + '<div class="lg"><span><i></i>A·B 확실·높음</span><span><i class="c"></i>C 근사(거리)</span><span><i class="d"></i>D·E 추정·가설</span><span>원을 누르면 그 묶음으로</span></div>';
  }

  /* ---------- ⏱ 지금 이 시각 ---------- */
  function nowBox(o) {
    var d = new Date(), h = d.getHours(), we = [0, 6].indexOf(d.getDay()) >= 0, td = today(), L = [], bin = Math.floor(h / 6), BN = ['0~6시', '6~12시', '12~18시', '18~24시'];
    function evToday(ids) { var seen = {}, r = []; ids.forEach(function (i) { Q.back(i, '근처').forEach(function (x) { var e = x.o; if (seen[e.id] || e.kind === '침수') return; var d0 = String(e.d0).slice(0, 10), d1 = String(e.d1 || e.d0).slice(0, 10); if (d0 <= td && td <= d1) { seen[e.id] = 1; r.push(e); } }); }); return r; }
    var ints = o.t === 'INT' ? [o.id] : o.t === 'DNG' ? Q.back(o.id, '속함').map(function (x) { return x.o.id; }) : o.t === 'STN' ? Q.follow(o.id, '가까운교차로').map(function (x) { return x.o.id; }) : o.t === 'TRD' ? Q.follow(o.id, '품음').map(function (x) { return x.o.id; }) : o.t === 'PBX' ? Q.back(o.id, '가까운지구대').map(function (x) { return x.o.id; }) : [];
    if (o.t === 'INT') { var c = Q.follow(o.id, '들어감')[0]; if (c && c.o.wd) { var a = we ? c.o.we : c.o.wd, av = sum(a) / 24; L.push('둘레 250m 칸에 지금 ' + h + '시 평소 <b>' + fmt(a[h]) + '명</b> — 하루 평균의 ' + (av ? (a[h] / av).toFixed(1) : '—') + '배 (' + (we ? '주말' : '평일') + ' 생활인구)'); }
      var A = accOf(o.id); if (A && A.tod) { var t = sum(A.tod); if (t) L.push('10년 사고 중 지금 시간대(' + BN[bin] + ') 몫 <b>' + Math.round(A.tod[bin] / t * 100) + '%</b> — 네 시간대 평균은 25%'); } }
    if (o.t === 'STN' && o.hr) L.push('이 역 지금 ' + h + '시 승하차 몫 <b>' + o.hr[h] + '</b>(1 = 평소 한 시간 · 가장 붐비는 때 ' + Math.max.apply(null, o.hr) + ')');
    if (o.t === 'TRD' && o.sales) L.push((h >= 21 || h < 6 ? '지금은 밤 시간 — ' : '') + '이 상권 매출 중 밤(21~6시) 몫 <b>' + Math.round((o.night || 0) / o.sales * 100) + '%</b>');
    if (o.t === 'DNG' && o.sales) L.push('이 동 매출 중 밤 몫 <b>' + Math.round((o.salesNight || 0) / o.sales * 100) + '%</b>' + (h >= 21 || h < 6 ? ' — 지금이 그 시간' : ''));
    var ev = evToday(ints); if (ev.length) L.push('오늘 잡힌 일 <b>' + ev.length + '건</b> — ' + ev.slice(0, 4).map(function (e) { return esc(e.kind + (e.sub ? '·' + e.sub : '') + ' ' + String(e.nm || '').slice(0, 24)); }).join(' / ') + (ev.length > 4 ? ' 외' : ''));
    else if (ints.length) L.push('오늘 날짜에 걸린 집회·공연·돌발 기록은 없음(받은 자료 기준)');
    if (!L.length) return '';
    return '<h4>⏱ 지금 이 시각 — ' + ['일', '월', '화', '수', '목', '금', '토'][d.getDay()] + ' ' + h + '시</h4><div class="now"><ul>' + L.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul><div class="note">평소 모양(지난 기록의 평균)을 지금 시각에 맞춘 것 — 실시간 값이 아니다 · 오늘 일은 받아 둔 일정·기록</div></div>';
  }


  /* ---------- 🔴 지금 실제로 — 받아 올린 실시간 값(돌발 · 통행속도)을 이 대상에 잇는다 ---------- */
  function liveLoad(force) {
    if (!force && LIVE && Date.now() - LIVEAT < 180000) return Promise.resolve(LIVE);
    function J(u) { return fetch(u, { cache: 'no-cache' }).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }); }
    return Promise.all([J('data/live-acc-seoul.json'), J('data/live-ims-seoul.json'), J('data/live-spd-six.json')]).then(function (a) { LIVE = { acc: a[0], ims: a[1], spd: a[2] }; LIVEAT = Date.now(); return LIVE; });
  }
  function normLoad() { if (NORM || NORMING) return; NORMING = true; paint();
    fetch(AREA && AREA !== '11650' ? 'data/spd-normal-six/' + AREA + '.json' : 'data/spd-normal-seocho.json').then(function (r) { return r.json(); }).then(function (j) { NORM = j; NORMING = false; paint(); }, function () { NORMING = false; paint(); }); }
  function dcls(d) { var w = d.getDay(); return w === 0 ? 3 : w === 6 ? 2 : w === 5 ? 1 : 0; }
  function ymd(x) { x = String(x || ''); var mm = /(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2})시\s*(\d{1,2})분/.exec(x); if (mm) return (+mm[2]) + '/' + (+mm[3]) + ' ' + ('0' + mm[4]).slice(-2) + ':' + ('0' + mm[5]).slice(-2);
    return x.length >= 12 ? (+x.slice(4, 6)) + '/' + (+x.slice(6, 8)) + ' ' + x.slice(8, 10) + ':' + x.slice(10, 12) : x; }
  function scopeInts(o) { return o.t === 'INT' ? [o] : (o.t === 'DNG' ? Q.back(o.id, '속함') : o.t === 'STN' ? Q.follow(o.id, '가까운교차로') : o.t === 'TRD' ? Q.follow(o.id, '품음') : o.t === 'PBX' ? Q.back(o.id, '가까운지구대') : []).map(function (x) { return x.o || x; }); }
  function liveInc(o) {
    var ints = scopeInts(o).filter(function (i) { return i.lat; }), R = [], seen = {};
    function near(la, lo) { var b = null; ints.forEach(function (i) { var d = m(la, lo, +i.lat, +i.lon); if (!b || d < b.d) b = { d: d, i: i }; }); return b; }
    ((LIVE.acc && LIVE.acc.items) || []).forEach(function (x) { var n = near(x[5], x[6]); if (n && n.d <= 400 && !seen[x[0]]) { seen[x[0]] = 1; R.push({ src: '서울시 실시간 돌발(TOPIS)', kind: x[2], road: '', txt: String(x[9] || '').split(/\r|\n/)[0], s: ymd(x[7]), e: ymd(x[8]), link: x[4], d: n.d, at: n.i }); } });
    ((LIVE.ims && LIVE.ims.items) || []).forEach(function (x) { var n = near(x[4], x[5]); if (n && n.d <= 400 && !seen[x[0]]) { seen[x[0]] = 1; R.push({ src: '경찰청 UTIC 돌발', kind: x[1], road: x[7] || '', txt: String(x[11] || '').replace(/^\[[^\]]*\]\s*/, '').slice(0, 70), s: ymd(x[9]), e: ymd(x[10]), link: x[12], d: n.d, at: n.i }); } });
    return R.sort(function (a, b) { return a.d - b.d; });
  }
  function liveApr(o) {
    if (o.t !== 'INT' || !LIVE.spd || !LIVE.spd.m) return [];
    var d = new Date(), key = dcls(d) + '-' + d.getHours(), M = LIVE.spd.m;
    return Q.follow(o.id, '들어오는길').map(function (a) {
      var rd = Q.follow(a.o.id, '이룸').sort(function (x, y) { return (x.p.k || 0) - (y.p.k || 0); }).map(function (x) { return x.o; }).filter(function (r) { return M[r.link] != null; }).slice(0, 2);
      if (!rd.length) return null;
      var v = Math.round(sum(rd.map(function (r) { return M[r.link]; })) / rd.length), lim = Math.max.apply(null, rd.map(function (r) { return +r.lim || 0; })) || null, nv = null, prov = 0;
      if (NORM && NORM.links) { var ns = rd.map(function (r) { var c = (NORM.links[r.link] || {})[key]; if (c && c[4]) prov = 1; return c ? c[0] : null; }).filter(function (x) { return x != null; }); if (ns.length) nv = Math.round(sum(ns) / ns.length); }
      var ratio = nv ? v / nv : null, st = ratio != null ? (ratio < 0.6 ? 'slow' : ratio < 0.85 ? 'mid' : 'ok') : (v < 15 ? 'slow' : v < 25 ? 'mid' : 'ok');
      return { frm: a.o.frm, nm: rd[0].nm || a.o.nm, v: v, lim: lim, nv: nv, prov: prov, ratio: ratio, st: st, links: rd.map(function (r) { return r.link; }) };
    }).filter(Boolean);
  }
  function liveBox(o) {
    if (!LIVE) return '<h4>🔴 지금 실제로</h4><div class="live"><div class="note">실시간 값을 받는 중…</div></div>';
    var S = LIVE.spd, age = S && S.at ? Math.round((Date.now() / 1000 - (+S.at)) / 60) : null, stale = age == null || age > 20, L = [], inc = liveInc(o), apr = stale ? [] : liveApr(o);
    if (apr.length) { L.push('<b>들어오는 길 지금 속도</b>' + (NORM ? '' : ' <button class="sb" data-norm="1">' + (NORMING ? '평소 값 받는 중…' : '평소와 견주기(약 4MB)') + '</button>') + '<ul>' + apr.map(function (a) { var c = a.st === 'slow' ? '#dc2626' : a.st === 'mid' ? '#d97706' : '#16a34a';
      return '<li><b style="color:' + c + '">' + a.v + 'km/h</b> ' + esc(a.frm) + ' ' + esc(a.nm) + ' <small>(' + (a.nv ? '평소 이 시각 ' + a.nv + (a.prov ? ' 잠정' : '') + ' · ' + Math.round(a.ratio * 100) + '%' : '제한 ' + (a.lim || '—')) + ')</small></li>'; }).join('') + '</ul>'); }
    if (inc.length) L.push('<b>둘레 400m 돌발 ' + inc.length + '건</b><ul>' + inc.slice(0, 6).map(function (x) { return '<li><b>' + esc(x.kind) + '</b> ' + esc(x.road ? x.road + ' · ' : '') + esc(x.txt) + ' <small>(' + esc(x.s) + '~' + esc(x.e) + ' · ' + esc(nm(x.at)) + '에서 ' + fmt(x.d) + 'm · ' + esc(x.src) + ')</small></li>'; }).join('') + '</ul>');
    else L.push('둘레 400m 에 지금 걸린 돌발(공사·사고·통제)은 없음(받은 자료 기준)');
    return '<h4>🔴 지금 실제로' + (S && S.made ? ' — ' + esc(S.made) + ' 받은 값' : '') + '</h4><div class="live">' + L.map(function (x) { return '<div>' + x + '</div>'; }).join('') +
      '<div class="note">' + (stale ? '⚠ 통행속도가 ' + (age == null ? '없음' : age + '분 전 값') + '이라 쓰지 않았다(20분 넘으면 버림) · ' : '통행속도 = ITS(약 11분마다 받아 올림 · ' + age + '분 전) · ') + '돌발 = 서울시 TOPIS·경찰청 UTIC(10분마다) · 막힘 색 = ' + (NORM ? '평소 이 요일·시각 가운데값의 60%↓ 빨강 · 85%↓ 주황' : '15km/h↓ 빨강 · 25km/h↓ 주황(평소와 견주면 더 정확)') + ' · 가능성 B(측정값 · 몇 분 늦음)</div></div>';
  }
  function liveHyps(o) {
    if (!LIVE) return []; var S = LIVE.spd, age = S && S.at ? (Date.now() / 1000 - (+S.at)) / 60 : 1e9; if (age > 20) return [];   /* 통행속도가 20분 넘으면 「지금」 가설을 내지 않는다(칸 글과 같은 잣대) */
    var H = [], inc = liveInc(o), apr = liveApr(o).filter(function (a) { return a.st === 'slow'; });
    apr.forEach(function (a) { var hit = inc.filter(function (x) { return a.links.indexOf(String(x.link)) >= 0 || (x.road && a.nm && (x.road.indexOf(a.nm) >= 0 || a.nm.indexOf(x.road) >= 0)); })[0];
      H.push(hy('지금 ' + a.frm + '이 막혔다' + (hit ? ' — 돌발 때문일 수 있다' : ''), [a.nm + ' 지금 ' + a.v + 'km/h' + (a.nv ? '(평소 이 시각 ' + a.nv + ' · ' + Math.round(a.ratio * 100) + '%)' : '(제한 ' + (a.lim || '—') + ')'), hit ? hit.kind + ' ' + (hit.road || '') + ' ' + hit.txt + '(' + hit.s + '~' + hit.e + ')' : '둘레 400m 에 잡힌 돌발 없음 — 신호·사고·행사 등 다른 까닭'], '교차로 → 들어오는 길 → ITS 링크의 지금 속도 · 같은 링크·같은 길 이름의 지금 돌발을 겹쳤다', hit ? '돌발 자리 앞에서 미리 차로를 바꾸게 안내 · 끝나는 ' + hit.e + ' 까지 이어질 수 있다' : '현장 확인 — 지도 신호 카드·실시간 CCTV 로 까닭을 본다', hit ? 'C' : 'D')); });
    return H;
  }

  /* ---------- 🔁 막힘 고리 — 교차로 넷이 한 방향으로 서로의 출구를 막는 자리(소유자 지정) ---------- */
  var LHIST = null;   /* 지난 막힘 실측(data/onto-loop-hist.json · tools/onto/loop-hist.py) */
  function loopsLoad() { if (LOOPS) return Promise.resolve(LOOPS);
    fetch('data/onto-loop-hist.json', { cache: 'no-cache' }).then(function (r) { return r.json(); }).then(function (j) { LHIST = j; }).catch(function () { LHIST = { loops: {} }; });
    return fetch('data/onto-loops.json').then(function (r) { return r.json(); }).then(function (j) { LOOPS = j.loops || []; return LOOPS; }).catch(function () { LOOPS = []; return LOOPS; }); }
  function simLoad(a) { if (SIMD && SIMD.a === a) return Promise.resolve(SIMD.d);
    return fetch('data/sim-' + a + '.json').then(function (r) { return r.json(); }).then(function (d) { SIMD = { a: a, d: d }; return d; }).catch(function () { return null; }); }
  function loopsOf(o) { if (!LOOPS) return []; var ids = scopeInts(o).map(function (i) { return i.id; }); return LOOPS.filter(function (L) { return L.members.some(function (m) { return ids.indexOf(m) >= 0; }); }); }
  function legNow(lg) { var a = O(lg.apr); if (!a || !LIVE || !LIVE.spd || !LIVE.spd.m) return null; var M = LIVE.spd.m, d = new Date(), key = dcls(d) + '-' + d.getHours();
    var rd = lg.links ? lg.links.map(function (l) { return { link: l }; }).filter(function (r) { return M[r.link] != null; }) : [];   /* 고리 자료가 링크를 정해 주면 그것 먼저(ITS 원자료에 안 오는 조각이 있다) */
    if (!rd.length) rd = Q.follow(a.id, '이룸').sort(function (x, y) { return (x.p.k || 0) - (y.p.k || 0); }).map(function (x) { return x.o; }).filter(function (r) { return M[r.link] != null; }).slice(0, 2); if (!rd.length) return null;
    var v = Math.round(sum(rd.map(function (r) { return M[r.link]; })) / rd.length), nv = null;
    if (NORM && NORM.links) { var ns = rd.map(function (r) { var c = (NORM.links[r.link] || {})[key]; return c ? c[0] : null; }).filter(function (x) { return x != null; }); if (ns.length) nv = Math.round(sum(ns) / ns.length); }
    var ratio = nv ? v / nv : null, slow = ratio != null ? ratio < 0.6 : v < 15; return { v: v, nv: nv, ratio: ratio, slow: slow, mid: !slow && (ratio != null ? ratio < 0.85 : v < 25) }; }
  function loopState(L) { var S = LIVE && LIVE.spd, age = S && S.at ? (Date.now() / 1000 - (+S.at)) / 60 : 1e9; if (age > 20) return { stale: true, age: Math.round(age) };
    var legs = L.legs.map(function (lg) { return { lg: lg, n: legNow(lg) }; }), k = legs.filter(function (x) { return x.n && x.n.slow; }).length, seen = legs.filter(function (x) { return x.n; }).length;
    return { legs: legs, k: k, seen: seen, lvl: seen < 3 ? 'unk' : k >= 4 || (k >= 3 && seen === 3) ? 'full' : k >= 2 ? 'part' : 'ok' }; }
  function loopBox(o) {
    var Ls = loopsOf(o); if (!Ls.length) return '';
    return Ls.map(function (L) { var st = loopState(L), acts = [], h = '';
      L.members.forEach(function (m) { Q.back(m, '대상').forEach(function (x) { acts.push({ int: m, what: x.o.what }); }); });
      h += '<h4>🔁 막힘 고리 — ' + esc(L.nm) + ' (' + esc(L.dir) + ')</h4><div class="loop"><div class="note">' + esc(L.why) + ' — 소유자 지정 고리 · 한 변이 막히면 다음 교차로 출구가 막혀 고리 전체로 번진다</div>';
      if (st.stale) h += '<div>⚠ 통행속도가 ' + st.age + '분 전 값이라 지금 고리 상태는 보이지 않는다</div>';
      else { var lab = { full: ['고리 전체 막힘 — 교착 위험', '#dc2626'], part: ['고리 일부 막힘 — 번질 수 있다', '#d97706'], ok: ['고리 풀림', '#16a34a'], unk: ['속도 값이 모자라 판정 못 함', 'var(--ink2)'] }[st.lvl];
        h += '<div><b style="color:' + lab[1] + '">' + lab[0] + '</b> <small>(네 변 중 막힘 ' + st.k + ' · 값 있는 변 ' + st.seen + ')</small>' + (NORM ? '' : ' <button class="sb" data-norm="1">' + (NORMING ? '평소 값 받는 중…' : '평소와 견주기') + '</button>') + '</div><ol class="lg2">' +
          st.legs.map(function (x) { var n = x.n, c = !n ? 'var(--ink2)' : n.slow ? '#dc2626' : n.mid ? '#d97706' : '#16a34a';
            return '<li>' + esc(x.lg.nm) + ' — <b style="color:' + c + '">' + (n ? n.v + 'km/h' : '값 없음') + '</b>' + (n && n.nv ? ' <small>(평소 ' + n.nv + ' · ' + Math.round(n.ratio * 100) + '%)</small>' : '') + (x.lg.to !== o.id && O(x.lg.to) ? ' <button class="go" data-go="' + esc(x.lg.to) + '">' + esc(nm(O(x.lg.to))) + ' ›</button>' : '') + '</li>'; }).join('') + '</ol>'; }
      h += '<div class="note">원인(끌어들이는 곳): ' + ((L.causes || []).length ? esc(L.causes.join(' · ')) : '아직 형님 말씀 없음 — 현장에서 짚으시면 더한다') + '</div>' + (L.causesWhy ? '<div class="note">원인 근거: ' + esc(L.causesWhy) + '</div>' : '') + (L.found ? '<div class="note">찾은 길: ' + esc(L.found) + '</div>' : '');
      if (acts.length) h += '<details><summary>교통과가 이 넷에 해 온 조치 ' + acts.length + '건(교통과 출력물 · 근거기록)</summary><ul class="lg2">' + acts.slice(0, 30).map(function (a) { return '<li>' + esc(nm(O(a.int))) + ' — ' + esc(a.what) + '</li>'; }).join('') + '</ul></details>';
      var sd = SIMD && SIMD.a === L.sim ? SIMD.d : null;
      if (sd && sd.actions) h += '<details><summary>🧪 시뮬로 견줘 볼 수 있는 조치 ' + sd.actions.length + '가지</summary><ul class="lg2">' + sd.actions.map(function (a) { return '<li>' + esc(a.nm) + (a.src ? ' <small>— ' + esc(a.src) + '</small>' : '') + '</li>'; }).join('') + '</ul></details>';
      h += fieldBox(L) + histBox(L) + actBox(L) + (L.sim === 'banpo' ? '<div class="bar">' + (window.tgSimUI ? '<button data-sim="1">🧪 이 블록 시뮬 열기</button>' : '') + '</div><div class="note">시뮬은 개념 시연(예측·보증 아님) — 10/18 실측과 막히는 모양·풀리는 시각은 맞고 일부 접근로는 틀린다(시뮬 화면 경고 그대로) · 형님 현장 결과가 시뮬과 다르면 현장 결과가 이긴다</div>' : L.sim && window.tgSimArea ? '<div class="bar"><button data-sim="' + esc(L.sim) + '">🧪 이 둘레 시뮬 열기</button></div><div class="note">자동으로 엮은 구역 시뮬(' + esc(L.sim) + ') — 반포 블록(손으로 짠 구역)보다 거칠고 실제 막힘을 덜 낸다(시뮬 화면에 맞음 수) · 개념 시연 · 형님 현장 결과가 이긴다</div>' : '<div class="note">이 블록 시뮬은 아직 없다</div>') + '</div>';
      return h; }).join('');
  }



  /* 🚓 현장 대응(onto-loops field — 소유자 물음 「왜 엉키나 · 진출하면 먼저 · 신호값 그대로 수동으로 끊기」) · 시뮬 견주기 표는 개념 시연 */
  function fieldBox(L) {
    var F = L.field; if (!F) return '';
    var li = function (a) { return '<ul class="lg2">' + (a || []).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul>'; };
    var h = '<details class="acts" open><summary>🚓 진출하면 먼저 — 왜 엉키나 · 손볼 곳 · 수동으로 끊기</summary>';
    h += '<div class="sg2"><b>왜 엉킬 수밖에 없나</b></div>' + li(F.why) + '<div class="sg2"><b>진출하면 먼저 손볼 곳(차례)</b></div>' + li(F.first) + '<div class="sg2"><b>신호값은 그대로 · 수동으로 끊어 신반포로 줄이기</b></div>' + li(F.manual);
    if (F.sim && F.sim.rows) { var c = F.sim.cols || [], r0 = F.sim.rows[0];
      h += '<div class="sg2"><b>🧪 시뮬로 견줘 본 것</b> <small>' + esc(F.sim.day || '') + '</small></div><ul class="lg2">' + F.sim.rows.map(function (r, i) {
        var dv = i && r0[1] ? Math.round((r[1] - r0[1]) / r0[1] * 100) : null;
        return '<li><b>' + esc(r[0]) + '</b> — ' + esc(c[1] || '지체') + ' ' + r[1].toLocaleString() + (dv != null ? ' <small style="color:' + (dv < 0 ? '#16a34a' : dv > 0 ? '#dc2626' : 'inherit') + '">(' + (dv > 0 ? '+' : '') + dv + '%)</small>' : '') + ' · ' + esc(c[2] || '') + ' ' + r[2] + ' · ' + esc(c[3] || '') + ' ' + esc(r[3]) + ' · ' + esc(c[4] || '') + ' ' + r[4].toLocaleString() + '</li>'; }).join('') + '</ul>' +
        (F.sim.more ? li(F.sim.more) : '') + '<div class="note">' + esc(F.sim.rule || '') + (F.sim.check ? ' · ' + esc(F.sim.check) : '') + '</div><div class="note">⚠ ' + esc(F.sim.warn || '') + '</div>'; }
    var X = F.real;
    if (X) h += '<div class="sg2"><b>📼 ' + esc(X.title) + '</b></div><div class="note">' + esc(X.said) + '</div>' + li(X.rows) + '<div class="note">💡 ' + esc(X.lesson) + '</div><div class="note">출처: ' + esc(X.src) + '</div>';
    var Q = F.propose;
    if (Q) h += '<div class="sg2"><b>📝 ' + esc(Q.title) + '</b></div><div class="note">' + esc(Q.said) + '</div><div class="sg2">왜</div>' + li(Q.why) + '<div class="sg2">건의 내용</div>' + li(Q.ask) + '<div class="sg2">시뮬로 본 근거</div>' + li(Q.sim) + '<div class="note">' + esc(Q.who) + '</div>';
    return h + '</details>';
  }
  /* 지난 막힘 실측 — 네 변 중 셋 이상이 문턱 이하로 이어진 토막 · 먼저 막힌 변 차례 · 저녁 기록이 빈 날은 「모름」 */
  function histBox(L) {
    var H = LHIST && LHIST.loops && LHIST.loops[L.id]; if (!H) return '';
    var R = LHIST.rule || {}, ep = H.ep || [], gone = (H.days || []).filter(function (d) { return d.eve < 6; });
    var h = '<details class="acts"' + (ep.length ? ' open' : '') + '><summary>📜 지난 고리 막힘 — 실측 ' + ep.length + '토막</summary>';
    h += '<div class="note">쌓인 ITS 통행속도 ' + esc((LHIST.from || '').slice(5)) + ' ~ ' + esc((LHIST.to || '').slice(5)) + ' · 네 변 중 ' + (R.legs || 3) + '변 이상이 ' + (R.th || 10) + 'km/h 이하로 이어진 때(앱 문턱 · 어림 · 약 11분 간격이라 시각은 그만큼 어긋남)</div>';
    if (ep.length > 10) { var wd = {}; ep.forEach(function (e) { wd[e.w] = (wd[e.w] || 0) + 1; }); h += '<div>요일마다 토막 수: ' + '월화수목금토일'.split('').filter(function (w) { return wd[w]; }).map(function (w) { return esc(w) + ' ' + wd[w]; }).join(' · ') + ' — 아래는 최근 10토막</div>'; }
    if (ep.length) h += '<ul class="lg2">' + ep.slice(-10).reverse().map(function (e) {
      var fr = (e.first || []).map(function (k) { var lg = L.legs[k]; return lg ? esc(lg.nm.split(' — ')[0]) : '?'; });
      return '<li><b>' + esc(e.d.slice(5).replace('-', '/')) + '(' + esc(e.w) + ') ' + esc(e.b) + '~' + esc(e.e) + '</b> <small>· 받은 때 ' + e.n + '번</small>' +
        (fr.length ? '<br><small>먼저 막힌 차례: ' + fr.join(' → ') + '</small>' : '') +
        '<br><small>가장 느릴 때 ' + (e.min || []).map(function (v) { return v == null ? '—' : Math.round(v); }).join(' · ') + ' km/h(위 네 변 차례)</small></li>'; }).join('') + '</ul>';
    else h += '<div>쌓인 기간에는 문턱을 넘은 막힘이 없다</div>';
    if (gone.length) h += '<div class="note">⚠ 저녁(15~22시) 기록이 비거나 거의 없는 날: ' + gone.map(function (d) { return esc(d.d.slice(5).replace('-', '/')) + '(' + esc(d.w) + ')'; }).join(' · ') + ' — 이 PC 가 꺼져 못 받은 날이라 막힘이 없었다는 뜻이 아니다</div>';
    var fs = ep.map(function (e) { return (e.first || [])[0]; }).filter(function (x) { return x != null; }), cnt = {};
    fs.forEach(function (k) { cnt[k] = (cnt[k] || 0) + 1; });
    var top = Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; })[0];
    (H.chronic || []).forEach(function (k) { if (L.legs[k]) h += '<div class="note">⚠ 「' + esc(L.legs[k].nm.split(' — ')[0]) + '」 변은 평소에도 ' + Math.round(H.med[k]) + 'km/h 안팎이라(쌓인 기록 가운데값) 막힘 판정·먼저 막힌 차례에서 힘이 약하다 — 이 변을 보는 길이 맞는지 현장 확인이 필요하다</div>'; });
    if (top != null && L.legs[top]) h += '<div class="note">💡 가설(D): 막힘이 「' + esc(L.legs[top].nm.split(' — ')[0]) + '」 변에서 먼저 시작한 토막이 ' + cnt[top] + '/' + fs.length + ' — 그 변으로 들어오는 수요를 먼저 끊으면 고리로 번지는 것을 늦출 수 있다(' + (fs.length < 10 ? '토막 수가 적어 확인 전 · ' : '') + '현장 판단이 이긴다)</div>';
    return h + '</details>';
  }
  /* 조치 앞뒤 — 적을 때의 네 변 속도(전) ↔ 지금 받은 값(뒤 · 받은 때가 조치보다 15분 넘게 뒤일 때만) · 같은 요일·시각의 다른 날과 견준 것이 아니다 — 정밀한 앞뒤는 PC 의 쌓인 기록으로(tools/onto/act-effect.py) */
  function legsSnap(L) { var st = loopState(L); if (st.stale) return null; return { at: +LIVE.spd.at, v: st.legs.map(function (x) { return x.n ? x.n.v : null; }) }; }
  function actBox(L) {
    var A = actGet().filter(function (r) { return r.loop === L.id; }), sd = SIMD && SIMD.a === L.sim ? SIMD.d : null, opts = (sd && sd.actions || []).map(function (a) { return [a.id, a.nm]; }).concat([['etc', '그 밖(한 줄로 적기)']]);
    var now = LIVE && LIVE.spd && LIVE.spd.at ? +LIVE.spd.at : null, cur = legsSnap(L);
    var h = '<details class="acts"' + (A.length ? ' open' : '') + '><summary>📝 현장 조치 적기 · 앞뒤 견주기' + (A.length ? ' — ' + A.length + '건' : '') + '</summary>' +
      '<div class="note">지금 한 조치를 고르면 그때 네 변 속도를 「전」으로 남기고, 15분 넘게 뒤 받은 값이 오면 「뒤」와 견준다 · 이 기기에만 · 사람·차량은 적지 않는다</div>' +
      '<div class="bar"><select id="m2dLnkAct">' + opts.map(function (o) { return '<option value="' + esc(o[0]) + '">' + esc(o[1]) + '</option>'; }).join('') + '</select><button data-actadd="' + esc(L.id) + '">지금 했다</button></div>';
    if (A.length) h += '<ul class="lg2">' + A.slice(-10).reverse().map(function (r) { var b = r.before, aft = cur && r.before && cur.at - r.at > 900 ? cur : null, d = new Date(r.at * 1000);
      var line = esc(('0' + (d.getMonth() + 1)).slice(-2) + '/' + ('0' + d.getDate()).slice(-2) + ' ' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2)) + ' <b>' + esc(r.nm) + '</b>' + (r.note ? ' · ' + esc(r.note) : '');
      if (b && b.v) line += '<br><small>전 ' + b.v.map(function (v) { return v == null ? '—' : v; }).join(' · ') + ' km/h' + (aft ? ' → 뒤(' + Math.round((aft.at - r.at) / 60) + '분 뒤) ' + aft.v.map(function (v, i) { var x = b.v[i]; return v == null ? '—' : '<b style="color:' + (x == null ? 'inherit' : v > x * 1.15 ? '#16a34a' : v < x * 0.85 ? '#dc2626' : 'inherit') + '">' + v + '</b>'; }).join(' · ') + ' km/h' : ' · 뒤 = 15분 넘게 지난 값을 기다리는 중') + '</small>';
      return '<li>' + line + '</li>'; }).join('') + '</ul><div class="bar"><button data-actcsv="1">📋 CSV 복사</button><button data-actclr="1">지우기</button></div><div class="note">네 변 차례 = 위 고리 목록 차례 · 초록 = 15% 넘게 빨라짐 · 빨강 = 15% 넘게 느려짐 · 그 사이 수요가 바뀌었을 수 있어 조치 효과라고 단정하지 않는다(가능성 D)</div>';
    return h + '</details>';
  }
  function loopHyps(o) { var H = []; loopsOf(o).forEach(function (L) { var st = loopState(L); if (st.stale || (st.lvl !== 'full' && st.lvl !== 'part')) return;
    H.push(hy(L.nm + ' 고리가 ' + L.dir + '으로 막히는 중' + (st.lvl === 'full' ? ' — 교착 위험' : ''), st.legs.filter(function (x) { return x.n; }).map(function (x) { return x.lg.nm + ' ' + x.n.v + 'km/h' + (x.n.nv ? '(평소 ' + Math.round(x.n.ratio * 100) + '%)' : ''); }), '고리(소유자 지정) 네 변 = 다음 교차로로 들어오는 길의 ITS 지금 속도를 한 묶음으로 봤다', st.lvl === 'full' ? '블록으로 들어오는 차를 먼저 끊는다(라바콘·입차 중단) — 시뮬로 어느 조치가 먼저 풀리는지 견줘 보기' : '막힌 변 다음 교차로의 출구를 먼저 살핀다 — 번지기 전에 들어오는 차 조절', 'C')); }); return H; }

  /* ---------- 💡 엮으면 보이는 것(가설) ---------- */
  function hy(t, ev, wy, res, g) { return { t: t, ev: ev, wy: wy, res: res, g: g || 'D' }; }
  /* 🧪 게임 「만약에」로 돌려 보기(게임 v0.10.121 · ?whatif=<조건>&at=<INT-코드|위도,경도>&nm=) — 가설 갈래에 어울리는 조건 하나 · 게임 설계값 위의 비교다 */
  var WI = [['지금 북쪽에서', 'green', '그 교차로 남북 녹색 +10초'], ['지금 남쪽에서', 'green', '그 교차로 남북 녹색 +10초'],   /* 게임 조건이 남북 +10초뿐 — 동서·대각 막힘에는 안 붙인다 */
    ['사람보다 사고가', 'viol50', '위반 성향 절반(단속·계도 효과 가정)'], ['행사 끝 인파', 'ped2', '보행자 2배'], ['밤 장사와 밤 사고', 'viol50', '위반 성향 절반(단속·계도 효과 가정)'], ['사고는 많은데 단속 카메라', 'viol50', '위반 성향 절반(단속 효과 가정)'], ['행사 끝 시각에 역이', 'ped2', '보행자 2배']];
  function wiLink(o, x) { var w = WI.filter(function (r) { return x.t.indexOf(r[0]) === 0; })[0]; if (!w) return '';
    var at = o.t === 'INT' ? o.id : o.lat && o.lon ? (+o.lat).toFixed(5) + ',' + (+o.lon).toFixed(5) : null; if (!at) return '';
    return '<a class="wi" target="_blank" rel="noopener" href="https://340patrolman.github.io/traffic-game/?whatif=' + w[1] + '&at=' + encodeURIComponent(at) + '&nm=' + encodeURIComponent(nm(o)) + '">🧪 게임에서 돌려 보기 — ' + esc(w[2]) + ' ›</a><div class="note">게임 「만약에」가 그대로·바꾼 것을 씨앗 셋으로 돌려 견준다 — 게임 설계값 위의 비교라 현실 숫자가 아니다 · 같은 판에서 「조건 하나를 바꾸면 어느 쪽으로 움직이나」를 보는 데만 쓴다 — 게임은 실제 교차로 사고 순위를 재현하지 못한다(게임 세션 10-25 측정 ρ −0.14) · 서초 간선 25곳(700m 안)이 아니면 조건만 고른 채 열린다</div>'; }
  function hyps(o) {
    var H = [], since = ago(90);
    if (o.t === 'INT') {
      var A = accOf(o.id), tot = A ? sum(A.years) : 0, q11 = Q.q11 ? Q.q11(o.id) : null;
      if (q11 && q11.bins && q11.bins.peopleWd && q11.bins.acc) { var pb = q11.bins.peopleWd, ab = q11.bins.acc, bi = -1, br = 0; for (var i = 0; i < 4; i++) { if (ab[i] >= 20 && pb[i] > 0 && q11.bins.accN && q11.bins.accN[i] >= 12 && ab[i] / pb[i] > br) { br = ab[i] / pb[i]; bi = i; } }
        if (bi >= 0 && br >= 1.6) H.push(hy('사람보다 사고가 몰리는 시간 — ' + q11.bins.names[bi], ['둘레 250m 칸 생활인구 몫 ' + pb[bi] + '% (평일 한 주 평균)', '교차로 70m 안 사고 10년 중 ' + ab[bi] + '% (TAAS)'], '같은 자리를 「사람 칸」과 「사고 칸」으로 이어 시간대 몫을 나란히 놓았다', '이 시간대는 사람 수에 비해 사고가 ' + (Math.round(br * 10) / 10) + '배 몰린다 → 순찰·단속을 이 시간에 두면 효과가 클 수 있다', 'D')); }
      var q8 = Q.q8 ? Q.q8(o.id, since, 50) : null, st = Q.back(o.id, '가까운교차로')[0];
      if (q8 && q8.n && st) { var S = st.o, big = q8.events.filter(function (e) { return e.kind === '공연' || e.kind === '집회'; });
        if (big.length) { var hh = big.map(function (e) { var mm = /(\d{1,2}):\d{2}\s*$/.exec(String(e.d1 || '')); return mm ? +mm[1] : null; }).filter(function (v) { return v != null; }), sh = hh.length ? hh.sort(function (a, b) { return a - b; })[Math.floor(hh.length / 2)] : null;
          H.push(hy('행사 끝 인파와 역 붐빔이 겹칠 수 있다', ['지난 90일 둘레 집회·공연 ' + big.length + '건(근처 · C)', S.nm + '역 ' + fmt(st.p.d) + 'm · 하루 승하차 ' + fmt(S.day) + '명' + (sh != null && S.hr ? ' · 행사 끝나는 ' + sh + '시 몫 ' + S.hr[sh] : '')], '교차로 ← 사건(근처) · 교차로 ← 역(가까운교차로)을 한 자리에서 겹쳤다', '행사가 끝나는 시각에 ' + S.nm + '역 쪽 건널목·택시 승하차가 몰릴 수 있다 → 그 시각 보행 신호·불법 정차 관리', 'D')); } }
      var wet = []; Q.follow(o.id, '들어오는길').forEach(function (a) { Q.follow(a.o.id, '이룸').forEach(function (r) { if (+r.o.fy > 0) wet.push({ a: a.o, r: r.o }); }); });
      if (wet.length) { var w0 = wet.sort(function (x, y) { return (+y.r.fy) - (+x.r.fy); })[0], dt = wet.filter(function (x) { return +x.r.dt === -1 || +x.r.dt > 120; });
        H.push(hy('큰비 때 들어오는 길이 막힐 수 있다', [w0.a.frm + ' ' + esc(w0.r.nm) + ' — 침수 흔적 ' + w0.r.fy + '해(마지막 ' + (w0.r.fl || '—') + ' · 깊이 ' + (w0.r.fd || '—') + 'm)', '침수 흔적 있는 구간 ' + wet.length + '개' + (dt.length ? ' · 그중 돌아가기 어려운 구간 ' + dt.length + '개' : '')], '교차로 → 들어오는 길 → 도로 구간(ITS 링크) → 침수흔적도를 이어 따라갔다', '호우 특보 때 이 쪽 길을 먼저 살피고 ' + (dt.length ? '돌아갈 길이 마땅치 않아 통제 시 우회 안내가 필요' : '막히면 우회로 안내'), 'D')); }
      var tr = Q.back(o.id, '품음').map(function (x) { return x.o; }).filter(function (t) { return t.sales && t.night != null; }).sort(function (a, b) { return b.night / b.sales - a.night / a.sales; })[0];
      if (tr && A && tot >= 10) { var ns = Math.round(tr.night / tr.sales * 100), na = Math.round(A.night / tot * 100); if (ns >= 15 && na >= 35) H.push(hy('밤 장사와 밤 사고가 같은 자리', [tr.nm + ' 상권 밤 매출 몫 ' + ns + '%(카드 추정)', '교차로 사고 10년 중 밤(20~6시) ' + na + '%'], '상권 → 경계 안 교차로(품음) · 교차로 → 사고(발생)를 겹쳤다', '밤 음주운전·보행자 사고 위험 후보 → 밤 음주 단속 자리로 검토', 'D')); }
      var cams = Q.follow(o.id, '보유').length; if (!cams && tot >= 40) H.push(hy('사고는 많은데 단속 카메라가 없다', ['사고 10년 ' + fmt(tot) + '건', '100m 안 경찰 단속 카메라 0대(gargo-alerts · 구청 카메라·CCTV 는 세지 않음)'], '교차로 → 카메라(보유) 링크가 비어 있음을 「빈 연결」로 읽었다', '현장 단속·카메라 설치 건의 검토 대상', 'D'));
    }
    if (o.t === 'DNG') {
      var q7 = Q.q7 ? Q.q7(o.id, 3) : null, top = q7 && q7.ints && q7.ints[0];
      if (o.stOpen4 != null && o.stClose4 >= o.stOpen4 * 1.2 && o.stClose4 - o.stOpen4 >= 20) H.push(hy('가게가 줄고 있다', ['최근 1년 개업 ' + fmt(o.stOpen4) + ' · 폐업 ' + fmt(o.stClose4) + '(서울 상권분석 100업종)'], '행정동 ← 점포 집계(같은 동 코드)', '빈 점포·밤 어두운 거리가 늘 수 있다 → 생활안전 순찰 시 살펴볼 곳', 'D'));
      if (o.wk && o.res && o.wk / o.res >= 1.5 && top) H.push(hy('낮에 사람이 몰리는 일터 동네', ['국민연금 가입 일하는 사람 ' + fmt(o.wk) + ' ÷ 주민 ' + fmt(o.res) + ' = ' + (Math.round(o.wk / o.res * 10) / 10) + '배', '사고 가장 많은 교차로 ' + top.nm + ' 10년 ' + fmt(top.total) + '건'], '동 ← 교차로(속함) · 동의 사람 자료를 겹쳤다', '출퇴근 시간 보행·이륜차 사고 관리가 우선일 수 있다', 'D'));
    }
    if (o.t === 'STN' && Q.q16) { var q16 = Q.q16(o.id, since, 30); if (q16 && q16.nEvents) { var ev2 = q16.events.filter(function (e) { return e.stnShareAtEnd != null && e.stnShareAtEnd >= 1; });
      H.push(hy('행사 끝 시각에 역이 이미 붐빈다', ['지난 90일 500m 안 집회·공연 ' + q16.nEvents + '건', ev2.length ? '그중 ' + ev2.length + '건은 끝나는 시각에 역이 평소 한 시간보다 붐빔(몫 ≥ 1)' : '끝나는 시각 역 몫은 대부분 1 미만'], '역 ← 사건(근처역) · 역 시간대 몫을 끝나는 시각에 맞췄다', ev2.length ? '그 시각 역 출입구·횡단보도 인파 관리 필요 가능' : '행사 끝 인파가 역 평소 붐빔과 겹칠 가능성은 낮다', 'D')); } }
    if (o.t === 'TRD' && Q.q17) { var q17 = Q.q17(o.id); if (q17 && q17.ints && q17.ints[0] && q17.nightShare != null) H.push(hy('상권 밤 몫과 안 교차로 사고', ['밤 매출 몫 ' + q17.nightShare + '% · 주점 몫 ' + (q17.barShare == null ? '—' : q17.barShare + '%'), '경계 안 사고 가장 많은 교차로 ' + q17.ints[0].nm + ' 10년 ' + fmt(q17.ints[0].total) + '건 · 밤 ' + fmt(q17.ints[0].night)], '상권 → 경계 안 교차로(품음) → 사고(발생)', q17.nightShare >= 20 ? '밤 장사 비중이 커 밤 시간 보행·음주 사고 관리 후보' : '낮 장사 중심 — 낮 시간 보행 사고·불법 주정차가 먼저', 'D')); }
    return H;
  }

  /* ---------- 그리기 ---------- */
  function head(o) {
    var t = TN[o.t] || o.t;
    return '<h3>🧩 ' + esc(nm(o)) + '</h3><p class="sub">' + esc(t) + ' · ' + esc(o.id) + ' — 이어진 것을 「연결 이유 · 근거 · 결과 · 가능성」으로 본다</p>' +
      '<div class="bar">' + (ST.back.length ? '<button data-back="1">← ' + esc(O(ST.back[ST.back.length - 1]) ? nm(O(ST.back[ST.back.length - 1])) : '앞 대상') + '</button>' : '') + (o.lat && o.lon ? '<button data-map="' + o.lat + ',' + o.lon + '">📍 지도에서</button>' : '') + '<button data-pick="1">🔎 다른 대상</button></div>';
  }
  function paint() {
    var el = box(); if (!Q) { el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">서초 온톨로지 코어를 받는 중…</div>'; return; }
    var o = O(ST.id); if (!o) return pick();
    var GS = groups(o.id), H = loopHyps(o).concat(liveHyps(o), hyps(o)), h = '<button class="lx" data-close="1">닫기</button>' + head(o) + graph(o, GS) + liveBox(o) + loopBox(o) + nowBox(o);
    if (H.length) h += '<h4>💡 엮으면 보이는 것 — 가설 ' + H.length + '</h4><div class="note">이은 것들을 겹쳐 본 짐작이다(등급 C·D) · 처음 해 보는 연결이라 틀릴 수 있다 — 현장에서 맞는지 보고 알려 주시면 고친다</div>' +
      H.map(function (x) { var k = hkey(o.id, x.t), L0 = logGet().filter(function (r) { return r.k === k; }), last = L0[L0.length - 1];
        var vb = '<div class="hv">' + (last ? '<span class="hb ' + (last.v === '맞다' ? 'ok' : last.v === '틀리다' ? 'no' : '') + '">' + esc(last.v) + ' · ' + esc(last.d) + (last.why ? ' · ' + esc(last.why) : '') + (L0.length > 1 ? ' (' + L0.length + '번)' : '') + '</span>' : '<span class="hq">현장에서 보니</span>') +
          ['맞다', '틀리다', '모르겠다'].map(function (v) { return '<button class="sb" data-hv="' + esc(k) + '" data-v="' + v + '" data-g="' + x.g + '">' + v + '</button>'; }).join('') + '</div>';
        return '<div class="hy"><b class="t">' + esc(x.t) + '</b><div class="k4"><span>근거</span><div><ul>' + x.ev.map(function (e) { return '<li>' + esc(e) + '</li>'; }).join('') + '</ul></div><span>연결 이유</span><div>' + esc(x.wy) + '</div><span>결과</span><div><b>' + esc(x.res) + '</b></div><span>가능성</span><div>' + poss(x.g) + '</div></div>' + wiLink(o, x) + vb + '</div>'; }).join('');
    h += '<h4>🔗 이어진 것 ' + GS.length + '갈래</h4>';
    GS.forEach(function (g) { var lim = ST.more[g.key] ? 200 : 6, it = g.items.slice(0, lim);
      h += '<details class="rel" id="lnk-' + esc(g.key) + '"' + (GS.length <= 4 ? ' open' : '') + '><summary>' + gdots(g.best) + esc(gname(g)) + ' <small>' + g.items.length + '개 · ' + esc(KEY[g.rel] ? KEY[g.rel].split(' — ')[0] : '') + '</small></summary>' +
        it.map(function (x) { return '<div class="lk"><div class="t"><b>' + esc(nm(x.o)) + '</b>' + (NAV[x.o.t] && x.o.id !== o.id ? '<button class="go" data-go="' + esc(x.o.id) + '">여기서 엮임 ›</button>' : '') + '</div>' + k4(g.rel, x.p, x.o, g.dir) + '</div>'; }).join('') +
        (g.items.length > lim ? '<button class="sb" data-more="' + esc(g.key) + '">' + (g.items.length - lim) + '개 더 보기</button>' : '') + '</details>'; });
    var LG = logGet(); if (LG.length) h += '<h4>📒 내가 매긴 가설 ' + LG.length + '건</h4><div class="note">이 기기에만 있다 · CSV 를 복사해 07_API키/out/onto_logs/in/ 에 넣으면 log-ingest 가 「현장 판단 후보」로 정리한다 — 형님이 맞다고 한 것만 규칙 장부에</div><ul class="lg2">' +
      LG.slice(-8).reverse().map(function (r) { return '<li>' + esc(r.d) + ' · ' + esc(r.nm) + ' — ' + esc(r.h) + ' → <b>' + esc(r.v) + '</b>' + (r.why ? ' · ' + esc(r.why) : '') + '</li>'; }).join('') + '</ul><div class="bar"><button data-lcsv="1">📋 CSV 복사</button><button data-lclr="1">지우기</button></div>';
    h += '<div class="src">자료 = ' + esc(GUN[AREA] || '') + ' 온톨로지 코어(' + esc(Q.core.made || '') + ' 구움' + (AREA !== '11650' ? ' · 여섯 구 코어를 구로 나눈 것' : '') + ' · 원자료 값 그대로) · 가능성 A 확실 · B 높음 · C 근사 · D 추정 · E 가설 · 판단은 사람이 한다 — 이 화면은 이어 보일 뿐 · 법령·범칙금·판례 정본 = T-Book(출발점) · 게임 「만약에」·현장 기록·규칙 장부와 이어져 있다</div>';
    el.innerHTML = h;
  }
  function pick() {
    var el = box(), q = ST.q.trim(), L = [];
    var T = ['INT', 'DNG', 'STN', 'TRD', 'PBX'];
    if (IDX) { IDX.items.forEach(function (it) { var t = it[0].split('-')[0]; if (T.indexOf(t) < 0) return; if (!q || String(it[1]).indexOf(q) >= 0) L.push({ id: it[0], t: t, nm: it[1], gu: it[4] }); });
      L.sort(function (a, b) { return (a.gu === AREA ? 0 : 1) - (b.gu === AREA ? 0 : 1) || T.indexOf(a.t) - T.indexOf(b.t) || (String(a.nm) < String(b.nm) ? -1 : 1); }); }
    var keep = $('m2dLnkQ') && document.activeElement === $('m2dLnkQ');
    el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><p class="sub">대상 하나를 고르면 이어진 것과 그 까닭·근거·결과·가능성을 보여 준다 · 서초·강남·송파·동작·관악·용산 여섯 구</p>' +
      '<input id="m2dLnkQ" type="search" placeholder="교차로·동·역·상권·지구대 이름" value="' + esc(ST.q) + '" aria-label="대상 찾기">' +
      (IDX ? '<ul class="pick">' + L.slice(0, 40).map(function (o) { return '<li><button data-go="' + esc(o.id) + '">' + esc(o.nm) + ' <small>' + esc(TN[o.t]) + ' · ' + esc(GUN[o.gu] || '') + '</small></button></li>'; }).join('') + '</ul>' + (L.length > 40 ? '<p class="note">' + (L.length - 40) + '개 더 — 이름을 더 적어 주세요</p>' : '') : '<div class="wait">받는 중…</div>');
    if (keep) { var i = $('m2dLnkQ'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }
  }
  function onInput(e) { if (e.target.id === 'm2dLnkQ') { ST.q = e.target.value; ST.id = null; pick(); } }
  function go(id, push) { if (push && ST.id && ST.id !== id) ST.back.push(ST.id); ST.more = {};
    function done() { ST.id = id; paint(); var el = $('m2dLnk'); if (el) el.scrollTop = 0; }
    var g = IGU[id]; if (Q && O(id) && (!g || g === AREA)) return done();   /* 이웃 구 교차로가 이 코어에 「이웃」으로만 들어 있으면 그 구 코어로 옮겨 펼친다 */
    if (g && g !== AREA) { var el = box(); el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">' + esc(GUN[g] || g) + ' 코어를 받는 중…</div>'; load(g).then(done, function () { el.innerHTML = '<button class="lx" data-close="1">닫기</button><div class="wait">' + esc(GUN[g] || g) + ' 코어를 받지 못했습니다.</div>'; }); return; }
    done(); }
  function onClick(e) { e.stopPropagation(); var b = e.target.closest('button,g.gn'), a; if (!b) return;
    if (b.hasAttribute('data-close')) return close();
    if ((a = b.getAttribute('data-go'))) return go(a, true);
    if (b.hasAttribute('data-back')) { go(ST.back.pop(), false); return; }
    if (b.hasAttribute('data-pick')) { if (ST.id) ST.back.push(ST.id); ST.id = null; ST.q = ''; pick(); return; }
    if (b.hasAttribute('data-norm')) { normLoad(); return; }
    if ((a = b.getAttribute('data-actadd'))) { var L0 = (LOOPS || []).filter(function (x) { return x.id === a; })[0], sel = $('m2dLnkAct'), v = sel ? sel.value : 'etc', nm0 = sel ? sel.options[sel.selectedIndex].text : '', note = '';
      if (v === 'etc') { note = (prompt('무엇을 했나요? (한 줄 · 사람·차량번호는 적지 않습니다)', '') || '').trim().slice(0, 120); if (!note) return; nm0 = '그 밖'; }
      if (PII.some(function (r) { return r.test(note); })) { alert('전화번호·주민번호·차량번호 꼴이 있어 저장하지 않았습니다.'); return; }
      var snap = L0 ? legsSnap(L0) : null, AA = actGet(); AA.push({ loop: a, act: v, nm: nm0, note: note, at: Math.round(Date.now() / 1000), before: snap });
      if (!actSet(AA)) alert('이 기기에 저장하지 못했습니다'); else if (!snap) alert('지금 받은 속도가 없거나 20분 넘게 묵어 「전」 속도는 비어 있습니다 — 시각만 남겼습니다(PC 의 쌓인 기록으로 앞뒤를 볼 수 있습니다)');
      var sc0 = $('m2dLnk').scrollTop; paint(); $('m2dLnk').scrollTop = sc0; return; }
    if (b.hasAttribute('data-actcsv')) { var rows = [['고리', '조치', '이름', '까닭', '시각', '전']].concat(actGet().map(function (r) { var d = new Date(r.at * 1000); return [r.loop, r.act, r.nm, r.note, d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2) + ' ' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2), r.before && r.before.v ? r.before.v.join('/') : '']; }));
      var t = rows.map(function (r) { return r.map(function (c) { c = String(c == null ? '' : c); return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c; }).join(','); }).join('\n');
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(function () { b.textContent = '✔ 복사됨'; }, function () { prompt('복사', t); }); else prompt('복사', t); return; }
    if (b.hasAttribute('data-actclr')) { if (confirm('이 기기의 현장 조치 기록을 모두 지울까요?')) { actSet([]); paint(); } return; }
    if (b.hasAttribute('data-sim')) { var sv = b.getAttribute('data-sim'); if (sv !== '1' && window.tgSimArea) { if (window.innerWidth < 760) close(); window.tgSimArea.open(sv); } else if (window.tgSimUI) { if (window.innerWidth < 760) close(); window.tgSimUI.open(); } return; }
    if ((a = b.getAttribute('data-hv'))) { var v = b.getAttribute('data-v'), why = '';
      if (v !== '맞다') { why = (prompt(v === '틀리다' ? '어디가 틀렸나요? (한 줄 · 사람·차량번호는 적지 않습니다)' : '덧붙일 말(비워도 됨)', '') || '').trim().slice(0, 120); }
      if (PII.some(function (r) { return r.test(why); })) { alert('전화번호·주민번호·차량번호 꼴이 있어 저장하지 않았습니다.'); return; }
      var o = O(ST.id), L = logGet(), dd = new Date(); L.push({ k: a, id: ST.id, nm: nm(o), h: a.split('|').slice(1).join('|'), v: v, why: why, g: b.getAttribute('data-g') || '', d: today() + ' ' + ('0' + dd.getHours()).slice(-2) + ':' + ('0' + dd.getMinutes()).slice(-2) });
      if (!logSet(L)) alert('이 기기에 저장하지 못했습니다'); var sc = $('m2dLnk').scrollTop; paint(); $('m2dLnk').scrollTop = sc; return; }
    if (b.hasAttribute('data-lcsv')) { var rows = [['날짜', '대상', '이름', '가설', '판정', '까닭', '가능성']].concat(logGet().map(function (r) { return [r.d, r.id, r.nm, r.h, r.v, r.why, r.g]; }));
      var t = rows.map(function (r) { return r.map(function (c) { c = String(c == null ? '' : c); return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c; }).join(','); }).join('\n');
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(function () { b.textContent = '✔ 복사됨'; }, function () { prompt('복사', t); }); else prompt('복사', t); return; }
    if (b.hasAttribute('data-lclr')) { if (confirm('이 기기의 가설 판정 기록을 모두 지울까요? 되돌릴 수 없습니다.')) { logSet([]); paint(); } return; }
    if ((a = b.getAttribute('data-more'))) { ST.more[a] = 1; paint(); var d = $('lnk-' + a); if (d) { d.open = true; d.scrollIntoView({ block: 'start' }); } return; }
    if ((a = b.getAttribute('data-jump'))) { var d2 = $('lnk-' + a); if (d2) { d2.open = true; d2.scrollIntoView({ block: 'start', behavior: 'smooth' }); } return; }
    if ((a = b.getAttribute('data-map'))) { var p = a.split(','); if (window.innerWidth < 760) close(); location.hash = 'v=' + p[0] + ',' + p[1] + ',250&t=' + p[0] + ',' + p[1]; return; } }

  function nearInt(lat, lon) { var best = null, bd = 1e9; Q.core.objects.forEach(function (o) { if (o.t !== 'INT' || !o.lat) return; var d = m(lat, lon, +o.lat, +o.lon); if (d < bd) { bd = d; best = o; } }); return bd <= 600 ? best : null; }
  function open(opt) {
    css(); var el = box(); el.classList.add('on'); ST.back = []; ST.more = {}; if (Q) paint(); else el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">온톨로지 코어를 받는 중…</div>';
    loadIdx().then(function () {
      var id = null;
      if (opt && opt.id && IGU[opt.id]) id = opt.id;
      else if (opt && opt.dong) { var d = IDX.items.filter(function (it) { return /^DNG-/.test(it[0]) && (it[0] === 'DNG-' + opt.dong || it[1] === opt.dong); })[0]; if (d) id = d[0]; }
      if (!id && opt && isFinite(+opt.lat) && isFinite(+opt.lon)) { var bd = 1e9; IDX.items.forEach(function (it) { if (!/^INT-/.test(it[0]) || it[2] == null) return; var dd = m(+opt.lat, +opt.lon, it[2], it[3]); if (dd < bd) { bd = dd; id = dd <= 600 ? it[0] : id; } }); }
      return load(id ? IGU[id] : (AREA || '11650')).then(function () { if (!id && opt && opt.id && O(opt.id)) id = opt.id; return id; });   /* 사고·위반·법규처럼 고르기 목록에 없는 대상도 그 코어에 있으면 연다 */
    }).then(function (id) {
      ST.id = id; if (id) paint(); else pick();
      loopsLoad().then(function (Ls) { var a = (Ls[0] || {}).sim; return a ? simLoad(a) : null; }).then(function () { if (ST.id && $('m2dLnk') && $('m2dLnk').classList.contains('on')) { var sc = $('m2dLnk').scrollTop; paint(); $('m2dLnk').scrollTop = sc; } });
      liveLoad(true).then(function () { if (ST.id && $('m2dLnk') && $('m2dLnk').classList.contains('on')) { var sc = $('m2dLnk').scrollTop; paint(); $('m2dLnk').scrollTop = sc; } });
    }, function () { el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">온톨로지 코어를 받지 못했습니다 — 통신을 확인해 주세요.</div>'; });
  }
  function close() { var el = $('m2dLnk'); if (el) el.classList.remove('on'); }
  window.tgLink = { open: open, close: close, _hyps: function (id) { return Q && O(id) ? hyps(O(id)) : null; }, _q: function () { return Q; }, _area: function () { return AREA; }, _load: load };
  function fromHash() { var h = location.hash || ''; if (!/(^|[#&])lnk=1(?=&|$)/.test(h)) return; var im = /(^|[#&])id=([A-Z]+-[^&]+)(?=&|$)/.exec(h), lm = /(^|[#&])ll=(-?[\d.]+),(-?[\d.]+)(?=&|$)/.exec(h);
    open(im ? { id: decodeURIComponent(im[2]) } : lm ? { lat: +lm[2], lon: +lm[3] } : null);
    var rest = h.replace(/^#/, '').split('&').filter(function (x) { return x && !/^(lnk|id|ll)=/.test(x); }).join('&');
    try { history.replaceState(null, '', location.pathname + location.search + (rest ? '#' + rest : '')); } catch (e) {} }
  window.addEventListener('hashchange', fromHash);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fromHash); else fromHash();
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
