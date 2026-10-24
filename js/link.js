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
  var CORE = 'ontology-core/data/core-seocho.json', QJS = 'ontology-core/query.js?v=3', SCH = 'ontology-core/schema-ext.json';
  var Q = null, SC = null, LOAD = null, ST = { id: null, back: [], more: {}, q: '' };
  var NAV = { INT: 1, DNG: 1, STN: 1, TRD: 1, PBX: 1, STA: 1, EVT: 1 };
  var TN = { INT: '교차로', DNG: '행정동', STN: '지하철역', TRD: '상권', PBX: '지구대·파출소', STA: '경찰서', EVT: '사건', ACC: '사고(10년)', ACL: '사고 칸', CAM: '단속 카메라', ATT: '시설', PLC: '250m 칸', APR: '들어오는 길', RD: '도로 구간', ACT: '교통과 조치', REC: '조치 기록', VIO: '위반 유형', LAW: '법규', PREC: '판례', RULE: '규칙', FK: '현장 판단' };
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
  function nm(o) { if (!o) return '—'; return o.nm || o.title || o.what || o.text || o.no || o.id; }
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
      '#m2dLnk .hy{border:1px dashed #d97706;border-radius:12px;padding:8px 10px;margin:6px 0;background:rgba(217,119,6,.06)}#m2dLnk .hy b.t{font-size:14px}' +
      '#m2dLnk .k4{display:grid;grid-template-columns:62px minmax(0,1fr);gap:1px 8px;font-size:12.5px;margin-top:4px}#m2dLnk .k4 span{color:var(--ink2)}#m2dLnk .k4 div{min-width:0;overflow-wrap:anywhere}' +
      '#m2dLnk details.rel{border:1px solid var(--line);border-radius:12px;margin:6px 0;padding:0 10px}#m2dLnk details.rel>summary{cursor:pointer;padding:8px 0;font-weight:700;list-style:none}#m2dLnk details.rel>summary::-webkit-details-marker{display:none}#m2dLnk details.rel>summary small{font-weight:400;color:var(--ink2)}' +
      '#m2dLnk .lk{border-top:1px solid var(--line);padding:6px 0}#m2dLnk .lk .t{display:flex;gap:6px;align-items:baseline;flex-wrap:wrap}#m2dLnk .lk .t b{font-size:13.5px}#m2dLnk .lk button.go{margin-left:auto;min-height:30px;border:1px solid var(--acc);color:var(--acc);background:none;border-radius:999px;padding:0 10px;font-size:12px;cursor:pointer}' +
      '#m2dLnk .gd{display:inline-flex;gap:2px;vertical-align:middle;margin-right:4px}#m2dLnk .gd i{width:7px;height:7px;border-radius:2px;background:var(--line)}#m2dLnk .gd i.f{background:#16a34a}#m2dLnk .gd.c i.f{background:#d97706}#m2dLnk .gd.d i.f{background:#94a3b8}' +
      '#m2dLnk .src{margin-top:10px;font-size:11.5px;color:var(--ink2)}#m2dLnk .wait{padding:16px 0;color:var(--ink2)}';
    document.head.appendChild(s);
  }
  function box() { var el = $('m2dLnk'); if (el) return el; el = document.createElement('div'); el.id = 'm2dLnk'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-label', '엮임 보기'); document.body.appendChild(el); el.addEventListener('click', onClick); el.addEventListener('input', onInput); return el; }

  function load() {
    if (LOAD) return LOAD;
    function js() { return window.OntoCore ? Promise.resolve() : new Promise(function (ok, no) { var s = document.createElement('script'); s.src = QJS; s.onload = ok; s.onerror = no; document.head.appendChild(s); }); }
    LOAD = js().then(function () { return Promise.all([fetch(CORE).then(function (r) { return r.json(); }), fetch(SCH).then(function (r) { return r.json(); }).catch(function () { return null; })]); })
      .then(function (a) { Q = new window.OntoCore(a[0]); SC = a[1]; return Q; })
      .catch(function (e) { LOAD = null; throw e; });
    return LOAD;
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
      case 'FK': return '「' + esc(String(o.said || '').slice(0, 60)) + '…」 ' + esc(o.date || '');
      default: return '';
    }
  }
  function asofOf(src) { var A = Q.core.asof || {}, k = Object.keys(A).filter(function (f) { return String(src || '').indexOf(f) >= 0; })[0]; return k ? A[k] : null; }
  function gdots(g) { var x = GR[g] || null, n = x ? x[2] : 0, c = g === 'C' ? ' c' : g === 'D' || g === 'E' ? ' d' : ''; var s = '<span class="gd' + c + '" aria-hidden="true">'; for (var i = 0; i < 5; i++) s += '<i class="' + (i < n ? 'f' : '') + '"></i>'; return s + '</span>'; }
  function poss(g) { var x = GR[g]; return x ? gdots(g) + '<b>' + g + ' ' + x[0] + '</b> — ' + x[1] : '— (등급 없음)'; }
  function why(rel, p) { var k = KEY[rel] || (SC && SC.linkTypes && SC.linkTypes[rel] ? SC.linkTypes[rel].name : rel); var d = p && p.d != null ? ' · ' + fmt(p.d) + 'm' : ''; return esc(k) + d; }
  function k4(rel, p, o, dir) {
    var src = p && p.src ? p.src : (SC && SC.linkTypes && SC.linkTypes[rel] ? (SC.linkTypes[rel].from || '') + '→' + (SC.linkTypes[rel].to || '') : ''), af = asofOf(src);
    return '<div class="k4"><span>연결 이유</span><div>' + why(rel, p) + '</div><span>근거</span><div>' + esc(src || '—') + (af ? ' · <i>' + esc(af) + '</i>' : '') + '</div><span>결과</span><div>' + (summ(o) || '—') + '</div><span>가능성</span><div>' + poss(p && p.g) + '</div></div>';
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

  /* ---------- 💡 엮으면 보이는 것(가설) ---------- */
  function hy(t, ev, wy, res, g) { return { t: t, ev: ev, wy: wy, res: res, g: g || 'D' }; }
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
      '<div class="bar">' + (ST.back.length ? '<button data-back="1">← ' + esc(nm(O(ST.back[ST.back.length - 1]))) + '</button>' : '') + (o.lat && o.lon ? '<button data-map="' + o.lat + ',' + o.lon + '">📍 지도에서</button>' : '') + '<button data-pick="1">🔎 다른 대상</button></div>';
  }
  function paint() {
    var el = box(); if (!Q) { el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">서초 온톨로지 코어를 받는 중…</div>'; return; }
    var o = O(ST.id); if (!o) return pick();
    var GS = groups(o.id), H = hyps(o), h = '<button class="lx" data-close="1">닫기</button>' + head(o) + graph(o, GS) + nowBox(o);
    if (H.length) h += '<h4>💡 엮으면 보이는 것 — 가설 ' + H.length + '</h4><div class="note">이은 것들을 겹쳐 본 짐작이다(등급 D) · 처음 해 보는 연결이라 틀릴 수 있다 — 현장에서 맞는지 보고 알려 주시면 고친다</div>' +
      H.map(function (x) { return '<div class="hy"><b class="t">' + esc(x.t) + '</b><div class="k4"><span>근거</span><div><ul>' + x.ev.map(function (e) { return '<li>' + esc(e) + '</li>'; }).join('') + '</ul></div><span>연결 이유</span><div>' + esc(x.wy) + '</div><span>결과</span><div><b>' + esc(x.res) + '</b></div><span>가능성</span><div>' + poss(x.g) + '</div></div></div>'; }).join('');
    h += '<h4>🔗 이어진 것 ' + GS.length + '갈래</h4>';
    GS.forEach(function (g) { var lim = ST.more[g.key] ? 200 : 6, it = g.items.slice(0, lim);
      h += '<details class="rel" id="lnk-' + esc(g.key) + '"' + (GS.length <= 4 ? ' open' : '') + '><summary>' + gdots(g.best) + esc(gname(g)) + ' <small>' + g.items.length + '개 · ' + esc(KEY[g.rel] ? KEY[g.rel].split(' — ')[0] : '') + '</small></summary>' +
        it.map(function (x) { return '<div class="lk"><div class="t"><b>' + esc(nm(x.o)) + '</b>' + (NAV[x.o.t] && x.o.id !== o.id ? '<button class="go" data-go="' + esc(x.o.id) + '">여기서 엮임 ›</button>' : '') + '</div>' + k4(g.rel, x.p, x.o, g.dir) + '</div>'; }).join('') +
        (g.items.length > lim ? '<button class="sb" data-more="' + esc(g.key) + '">' + (g.items.length - lim) + '개 더 보기</button>' : '') + '</details>'; });
    h += '<div class="src">자료 = 서초 온톨로지 코어(' + esc(Q.core.made || '') + ' 구움 · 원자료 값 그대로) · 가능성 A 확실 · B 높음 · C 근사 · D 추정 · E 가설 · 판단은 사람이 한다 — 이 화면은 이어 보일 뿐</div>';
    el.innerHTML = h;
  }
  function pick() {
    var el = box(), q = ST.q.trim(), L = [];
    if (Q) { var T = ['INT', 'DNG', 'STN', 'TRD', 'PBX', 'STA']; Q.core.objects.forEach(function (o) { if (T.indexOf(o.t) < 0) return; if (o.t === 'STA' && !Q.back(o.id, '관할').length) return; var n = String(nm(o)); if (!q || n.indexOf(q) >= 0) L.push(o); });
      L.sort(function (a, b) { return T.indexOf(a.t) - T.indexOf(b.t) || (String(nm(a)) < String(nm(b)) ? -1 : 1); }); }
    var keep = $('m2dLnkQ') && document.activeElement === $('m2dLnkQ');
    el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><p class="sub">대상 하나를 고르면 이어진 것과 그 까닭·근거·결과·가능성을 보여 준다 · 지금은 서초구(여섯 구는 다음)</p>' +
      '<input id="m2dLnkQ" type="search" placeholder="교차로·동·역·상권·지구대 이름" value="' + esc(ST.q) + '" aria-label="대상 찾기">' +
      (Q ? '<ul class="pick">' + L.slice(0, 40).map(function (o) { return '<li><button data-go="' + esc(o.id) + '">' + esc(nm(o)) + ' <small>' + esc(TN[o.t]) + (o.t === 'INT' ? ' · ' + esc(o.dongnm || '') : '') + '</small></button></li>'; }).join('') + '</ul>' + (L.length > 40 ? '<p class="note">' + (L.length - 40) + '개 더 — 이름을 더 적어 주세요</p>' : '') : '<div class="wait">받는 중…</div>');
    if (keep) { var i = $('m2dLnkQ'); i.focus(); i.setSelectionRange(i.value.length, i.value.length); }
  }
  function onInput(e) { if (e.target.id === 'm2dLnkQ') { ST.q = e.target.value; ST.id = null; pick(); } }
  function go(id, push) { if (push && ST.id && ST.id !== id) ST.back.push(ST.id); ST.id = id; ST.more = {}; paint(); var el = $('m2dLnk'); if (el) el.scrollTop = 0; }
  function onClick(e) { e.stopPropagation(); var b = e.target.closest('button,g.gn'), a; if (!b) return;
    if (b.hasAttribute('data-close')) return close();
    if ((a = b.getAttribute('data-go'))) return go(a, true);
    if (b.hasAttribute('data-back')) { ST.id = ST.back.pop(); ST.more = {}; paint(); return; }
    if (b.hasAttribute('data-pick')) { if (ST.id) ST.back.push(ST.id); ST.id = null; ST.q = ''; pick(); return; }
    if ((a = b.getAttribute('data-more'))) { ST.more[a] = 1; paint(); var d = $('lnk-' + a); if (d) { d.open = true; d.scrollIntoView({ block: 'start' }); } return; }
    if ((a = b.getAttribute('data-jump'))) { var d2 = $('lnk-' + a); if (d2) { d2.open = true; d2.scrollIntoView({ block: 'start', behavior: 'smooth' }); } return; }
    if ((a = b.getAttribute('data-map'))) { var p = a.split(','); if (window.innerWidth < 760) close(); location.hash = 'v=' + p[0] + ',' + p[1] + ',250&t=' + p[0] + ',' + p[1]; return; } }

  function nearInt(lat, lon) { var best = null, bd = 1e9; Q.core.objects.forEach(function (o) { if (o.t !== 'INT' || !o.lat) return; var d = m(lat, lon, +o.lat, +o.lon); if (d < bd) { bd = d; best = o; } }); return bd <= 600 ? best : null; }
  function open(opt) {
    css(); var el = box(); el.classList.add('on'); ST.back = []; ST.more = {}; paint();
    load().then(function () {
      var id = null;
      if (opt && opt.id && O(opt.id)) id = opt.id;
      else if (opt && opt.dong) { var d = Q.core.objects.filter(function (o) { return o.t === 'DNG' && (o.code === String(opt.dong) || o.nm === opt.dong); })[0]; if (d) id = d.id; }
      if (!id && opt && isFinite(+opt.lat) && isFinite(+opt.lon)) { var n = nearInt(+opt.lat, +opt.lon); if (n) id = n.id; }
      ST.id = id; if (id) paint(); else pick();
    }, function () { el.innerHTML = '<button class="lx" data-close="1">닫기</button><h3>🧩 엮임 보기</h3><div class="wait">온톨로지 코어를 받지 못했습니다 — 통신을 확인해 주세요.</div>'; });
  }
  function close() { var el = $('m2dLnk'); if (el) el.classList.remove('on'); }
  window.tgLink = { open: open, close: close, _hyps: function (id) { return Q && O(id) ? hyps(O(id)) : null; }, _q: function () { return Q; } };
  function fromHash() { var h = location.hash || ''; if (!/(^|[#&])lnk=1(?=&|$)/.test(h)) return; var im = /(^|[#&])id=([A-Z]+-[^&]+)(?=&|$)/.exec(h), lm = /(^|[#&])ll=(-?[\d.]+),(-?[\d.]+)(?=&|$)/.exec(h);
    open(im ? { id: decodeURIComponent(im[2]) } : lm ? { lat: +lm[2], lon: +lm[3] } : null);
    var rest = h.replace(/^#/, '').split('&').filter(function (x) { return x && !/^(lnk|id|ll)=/.test(x); }).join('&');
    try { history.replaceState(null, '', location.pathname + location.search + (rest ? '#' + rest : '')); } catch (e) {} }
  window.addEventListener('hashchange', fromHash);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fromHash); else fromHash();
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
