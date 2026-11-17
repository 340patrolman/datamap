/* deals.js — 🏷 최근 거래 찾기 v1 (2026-11-16 · 소유자 「향남읍 수직리처럼 거래가 드문 곳은 부동산에 보이는 것이 없다 — 판단 근거가 될 최근 거래를 · 농지·상가는 드물다 · 전월세도 · 목적을 가지고 찾아갈 수 있게」)
   자료 = 권역 저장소 r/<구>/ltrade.json(토지) · rtms.json(상가·업무) · shd.json(단독·다가구) · deals.json(아파트·연립·오피스텔) · home.json(전월세 묶은 값)
   모두 국토교통부 실거래가(공공데이터포털) — 해제 거래 뺌 · 지번·일자·당사자 없음 · 토지·단독·일반건물은 리·법정동까지만(필지 자리 아님)
   이 리에 거래가 적으면 같은 읍·면 → 구 전체로 넓혀 보인다(넓혔다고 밝힘) · 점수·추천 없음 · 저장·전송 없음 */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var ONGH = /github\.io$/.test(location.hostname), REG = null, IDX = null, CACHE = {}, ST = { gu: null, umd: null, pur: 'all', more: 0 }, PY = 3.3058;
  var PUR = [['all', '🕒', '전체', '땅·공장·상가·주택 매매를 한 줄로 — 최근 것부터(종류가 섞여 평당 가운데값은 내지 않습니다)'], ['farm', '🌾', '농지', '전·답·과수원·목장용지'], ['forest', '🌲', '임야', '산'], ['lot', '🏗', '대지·공장·잡종지', '집·공장을 지을 수 있는 땅 등'], ['etc', '🛤', '그 밖의 땅', '도로·구거·묘지 등(지분 거래가 많다)'], ['ind', '🏭', '공장·창고', '공장·창고 건물 매매 · 평당은 건물면적 기준'], ['shop', '🏢', '상가·업무', '근린생활·업무·판매·숙박 건물 매매 · 평당은 건물면적 기준'], ['house', '🏡', '단독·다가구', '매매 · 평당은 연면적 기준'], ['apt', '🏬', '아파트·연립·오피스텔', '매매 · 평당은 전용면적 기준'], ['rent', '🔑', '전세·월세', '주택 임대 — 단지·법정동 묶은 값']];
  var JG = { farm: ['전', '답', '과수원', '목장용지'], forest: ['임야'], lot: ['대', '공장용지', '창고용지', '잡종지', '주유소용지', '주차장'] };
  function get(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); }); }
  function boot() { if (REG) return Promise.resolve(); return Promise.all([get('data/regions.json'), ONGH ? null : get('data/r/index.json').catch(function () { return null; })]).then(function (r) { REG = {}; r[0].regions.forEach(function (g) { REG[g.sido] = g.repo; }); IDX = r[1]; }); }
  function rU(gu, f) { return (ONGH ? '/' + REG[gu.slice(0, 2)] + '/' : 'data/') + 'r/' + gu + '/' + f + '.json'; }
  function load(gu) { if (CACHE[gu]) return CACHE[gu]; return CACHE[gu] = Promise.all(['ltrade', 'rtms', 'shd', 'deals', 'home'].map(function (f) { return get(rU(gu, f)).catch(function () { return null; }); })).then(function (a) { return { gu: gu, lt: a[0], rt: a[1], sh: a[2], de: a[3], ho: a[4] }; }); }
  function gusAt(p) { var G = (window.TGMap2D && TGMap2D.ridx ? TGMap2D.ridx() : []) || []; if (!G.length && IDX) G = IDX.gus; var m = 0.02; return G.filter(function (g) { var b = g.box; return b && p.lon >= b[0] - m && p.lon <= b[2] + m && p.lat >= b[1] - m && p.lat <= b[3] + m; }); }
  function man(v) { if (v == null || !isFinite(v)) return '—'; if (v >= 10000) { var e = v / 10000; return (e >= 100 ? Math.round(e) : e.toFixed(e >= 10 ? 1 : 2).replace(/\.?0+$/, '')) + '억'; } return Math.round(v).toLocaleString() + '만'; }
  function ymS(y) { return String(y).slice(2, 4) + '.' + String(y).slice(4, 6); }
  function med(a) { if (!a.length) return null; a = a.slice().sort(function (x, y) { return x - y; }); var n = a.length; return n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2; }
  function eup(u) { var i = u.indexOf(' '); return i > 0 ? u.slice(0, i) : null; }

  /* 한 구의 거래를 목적별 한 꼴로 — {ym, umd, what, area(㎡), amt(만 원), part(지분), per(㎡당 만 원 · 견줄 수 있을 때만)} */
  function rows(D, pur) {
    var o = [], i, x;
    if (pur === 'all') { var any = false; PUR.forEach(function (p) { if (p[0] === 'all' || p[0] === 'rent') return; var r = rows(D, p[0]); if (!r) return; any = true; r.forEach(function (q) { q.what = p[1] + ' ' + q.what; q.per0 = q.per; q.per = null; o.push(q); }); }); if (!any) return null; o.sort(function (a, b) { return b.ym - a.ym || b.amt - a.amt; }); return o; }
    if (pur === 'farm' || pur === 'forest' || pur === 'lot' || pur === 'etc') { if (!D.lt || D.lt.lok === false) return null; var J = D.lt.jimok, all = JG.farm.concat(JG.forest, JG.lot);
      for (i = 0; i < D.lt.items.length; i++) { x = D.lt.items[i]; var jm = J[x[2]]; if (pur === 'etc' ? all.indexOf(jm) >= 0 : JG[pur].indexOf(jm) < 0) continue;
        o.push({ ym: 200000 + x[0], umd: D.lt.umds[x[1]], what: jm + ' · ' + D.lt.uses[x[3]], area: x[4], amt: x[5], part: !!x[6], per: x[5] / x[4], tag: (x[6] ? '지분' : '') + (x[7] ? (x[6] ? '·' : '') + '직거래' : '') }); } }
    else if (pur === 'ind') { if (!D.lt || !D.lt.ind || D.lt.iok === false) return null; for (i = 0; i < D.lt.ind.length; i++) { x = D.lt.ind[i]; o.push({ ym: 200000 + x[0], umd: D.lt.umds[x[1]], what: D.lt.iuses[x[2]] + (x[3] ? ' · 건물 통째' : ' · 집합(호)') + (x[7] ? ' · ' + x[7] + '년' : ''), area: x[4], amt: x[6], per: x[4] ? x[6] / x[4] : null, land: x[5], part: !!x[8], tag: x[8] ? '지분' : '' }); } }
    else if (pur === 'shop') { if (!D.rt) return null; for (i = 0; i < D.rt.items.length; i++) { x = D.rt.items[i]; o.push({ ym: x[0], umd: D.rt.umds[x[11]], what: D.rt.uses[x[1]] + (x[2] ? ' · 건물 통째' : ' · 집합(호)') + (x[3] != null ? ' ' + x[3] + '층' : '') + (x[12] ? ' · ' + x[12] + '년' : ''), area: x[4], amt: x[6], per: x[4] ? x[6] / x[4] : null, land: x[5], tag: '' }); } }
    else if (pur === 'house') { if (!D.sh) return null; for (i = 0; i < D.sh.d.length; i++) { x = D.sh.d[i]; o.push({ ym: x[6], umd: D.sh.umds[x[0]], what: (x[1] ? '다가구' : '단독') + (x[7] ? ' · ' + x[7] + '년' : ''), area: x[4], amt: x[5], per: x[4] ? x[5] / x[4] : null, land: x[3], tag: '' }); } }
    else if (pur === 'apt') { if (!D.de) return null; var K = ['아파트', '오피스텔', '연립·다세대']; for (i = 0; i < D.de.d.length; i++) { x = D.de.d[i]; if (x[4]) continue; var c = D.de.c[x[0]]; o.push({ ym: x[1], umd: D.de.umds[c[2]], what: K[c[0]] + ' · ' + c[1], area: x[2] / 100, amt: x[3], per: x[3] / (x[2] / 100), tag: '' }); } }
    o.sort(function (a, b) { return b.ym - a.ym || b.amt - a.amt; }); return o;
  }
  function rentRows(D) { if (!D.ho) return null; var o = [], H = D.ho, K = ['아파트', '오피스텔', '연립·다세대'];
    Object.keys(H.cx).forEach(function (k) { var c = H.cx[k], j = c[9] || [], w = c[10] || []; if (!(j[0] || w[0])) return; o.push({ umd: H.umds[c[2]], nm: K[c[0]] + ' · ' + c[1], jn: j[0] || 0, jper: j[1], wn: w[0] || 0, wm: w[1], wd: w[2] }); });
    Object.keys(H.sh || {}).forEach(function (k) { var s = H.sh[k]; if (!(s[2] || s[4])) return; o.push({ umd: H.umds[+k], nm: '단독·다가구(법정동 전체)', jn: s[2] || 0, jdep: s[3], wn: s[4] || 0, wm: s[5] }); });
    o.sort(function (a, b) { return (b.jn + b.wn) - (a.jn + a.wn); }); return o; }
  function scope(R, umd, lv) { var e = eup(umd); return R.filter(function (r) { return lv === 0 ? r.umd === umd : lv === 1 ? (e ? eup(r.umd) === e : r.umd === umd) : true; }); }

  function css() { if ($('m2dDealCss')) return; var s = document.createElement('style'); s.id = 'm2dDealCss';
    s.textContent = '#m2dDeal{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom));z-index:11;max-height:74vh;overflow:auto;background:var(--panel,#fff);color:var(--ink,#111);border:1px solid var(--line,#ddd);border-radius:14px;box-shadow:0 6px 24px rgba(0,0,0,.18);padding:10px 12px;display:none;font-size:14px;line-height:1.5}#m2dDeal.on{display:block}@media (min-width:760px){#m2dDeal{right:auto;width:460px;max-height:80vh}}' +
      'body.dealon #m2dEst{display:none!important}#m2dDeal h3{margin:0 80px 2px 0;font-size:16px}#m2dDeal .x{position:absolute;right:10px;top:8px;height:34px;padding:0 12px;border-radius:10px;border:0;background:#dc2626;color:#fff;font-weight:800;cursor:pointer}#m2dDeal .s{font-size:12px;color:var(--ink2,#555)}#m2dDeal select{height:36px;max-width:100%;border-radius:10px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit;font-size:14px;padding:0 8px}' +
      '#m2dDeal .pu{display:flex;gap:6px;overflow-x:auto;margin:8px 0;scrollbar-width:none}#m2dDeal .pu::-webkit-scrollbar{display:none}#m2dDeal .pu button{flex:0 0 auto;min-height:38px;padding:0 11px;border-radius:19px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit;font-size:13px;white-space:nowrap;cursor:pointer}#m2dDeal .pu button.on{background:var(--acc,#2563eb);border-color:transparent;color:#fff;font-weight:700}#m2dDeal .pu button i{font-style:normal;opacity:.75;font-size:11.5px;margin-left:3px}' +
      '#m2dDeal .sm{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin:6px 0}#m2dDeal .sm div{background:var(--chip,#f3f4f6);border-radius:8px;padding:4px 6px;text-align:center}#m2dDeal .sm small{display:block;font-size:11px;color:var(--ink2,#555)}#m2dDeal .sm b{font-size:14.5px}' +
      '#m2dDeal h4{margin:10px 0 2px;font-size:13.5px}#m2dDeal table{width:100%;border-collapse:collapse;font-size:12.5px}#m2dDeal td{padding:4px 2px;border-top:1px dashed var(--line,#ddd);vertical-align:top}#m2dDeal td.r{text-align:right;white-space:nowrap}#m2dDeal td small{display:block;color:var(--ink2,#555);font-size:11.5px}#m2dDeal .tg{display:inline-block;font-size:10.5px;border:1px solid #b45309;color:#b45309;border-radius:6px;padding:0 4px;margin-left:3px}:root.dark #m2dDeal .tg{color:#fbbf24;border-color:#fbbf24}' +
      '#m2dDeal .lk{display:block;width:100%;text-align:left;border:0;border-top:1px dashed var(--line,#ddd);background:transparent;color:inherit;padding:6px 2px;font-size:13px;cursor:pointer}#m2dDeal .lk b{color:var(--acc,#2563eb)}#m2dDeal .mr{width:100%;min-height:36px;margin-top:6px;border-radius:10px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit;cursor:pointer}.m2d-dealb{display:block;width:100%;min-height:40px;margin:8px 0 2px;border-radius:10px;border:1.5px solid #7c3aed;background:transparent;color:#6d28d9;font-weight:700;font-size:13.5px;cursor:pointer}:root.dark .m2d-dealb{color:#c4b5fd;border-color:#a78bfa}';
    document.head.appendChild(s); }
  function box() { var el = $('m2dDeal'); if (el) return el; el = document.createElement('div'); el.id = 'm2dDeal'; el.setAttribute('aria-label', '최근 거래 찾기'); document.body.appendChild(el);
    el.addEventListener('click', function (e) { e.stopPropagation(); var b = e.target.closest('button'); if (!b) return; if (b.classList.contains('x')) { el.classList.remove('on'); document.body.classList.remove('dealon'); return; }
      var p = b.getAttribute('data-pur'), u = b.getAttribute('data-umd'); if (p) { ST.pur = p; ST.more = 0; paint(); } else if (u) { ST.umd = u; ST.more = 0; paint(); go(u); } else if (b.hasAttribute('data-more')) { ST.more++; paint(); } });
    el.addEventListener('change', function (e) { if (e.target.id === 'm2dDealU') { ST.umd = e.target.value; ST.more = 0; paint(); } });
    return el; }
  function go(u) { var D = ST.D, i = D && D.lt ? D.lt.umds.indexOf(u) : -1, p = i >= 0 && D.lt.pos[i]; if (!p || !window.TGMap2D || !TGMap2D.applyHash) return; try { history.replaceState(null, '', '#lat=' + p[1] + '&lon=' + p[0]); TGMap2D.applyHash(); } catch (e) {} }

  function tbl(R, n) { return '<table>' + R.slice(0, n).map(function (r) { return '<tr><td>' + ymS(r.ym) + '</td><td>' + esc(r.what) + (r.tag ? '<span class="tg">' + esc(r.tag) + '</span>' : '') + '<small>' + esc(r.umd) + ' · ' + (r.area ? (+r.area).toLocaleString() + '㎡(' + Math.round(r.area / PY).toLocaleString() + '평)' : '') + (r.land ? ' · 대지 ' + (+r.land).toLocaleString() + '㎡' : '') + '</small></td><td class="r"><b>' + man(r.amt) + '</b><small>' + (r.per || r.per0 ? '평당 ' + man((r.per || r.per0) * PY) : '') + '</small></td></tr>'; }).join('') + '</table>'; }
  function sum(R) { var v = R.filter(function (r) { return !r.part && r.per; }).map(function (r) { return r.per; }), m = med(v); return '<div class="sm"><div><small>거래</small><b>' + R.length + '건</b></div><div><small>평당 가운데값' + (R.length !== v.length ? '(지분 뺌)' : '') + '</small><b>' + (m ? man(m * PY) : ST.pur === 'all' ? '종류별로' : '—') + '</b></div><div><small>가장 최근</small><b>' + (R.length ? ymS(R[0].ym) : '—') + '</b></div></div>'; }
  function paint() {
    var el = box(), D = ST.D, h = '<button class="x">✕ 닫기</button><h3>🏷 최근 거래 찾기</h3>';
    if (!D) { el.innerHTML = h + '<p class="s">' + esc(ST.msg || '자료를 받는 중…') + '</p>'; return; }
    var U = (D.lt ? D.lt.umds : D.ho ? D.ho.umds : []).slice().sort(function (a, b) { return a.localeCompare(b, 'ko'); });
    h += '<div class="s">' + esc(D.nm) + ' · 가장 가까운 법정동·리를 골랐습니다(바꿀 수 있음)</div><select id="m2dDealU" aria-label="법정동·리">' + U.map(function (u) { return '<option' + (u === ST.umd ? ' selected' : '') + '>' + esc(u) + '</option>'; }).join('') + '</select>';
    var isRent = ST.pur === 'rent', all = {}, e = eup(ST.umd || '');
    h += '<div class="pu">' + PUR.map(function (p) { var R = p[0] === 'rent' ? rentRows(D) : rows(D, p[0]); all[p[0]] = R; var n = R ? scope(R, ST.umd, 0).length : null; return '<button data-pur="' + p[0] + '" class="' + (ST.pur === p[0] ? 'on' : '') + '" title="' + esc(p[3]) + '">' + p[1] + ' ' + p[2] + '<i>' + (n == null ? '없음' : n) + '</i></button>'; }).join('') + '</div>';
    var R = all[ST.pur], P = PUR.filter(function (p) { return p[0] === ST.pur; })[0];
    h += '<div class="s">' + esc(P[3]) + ' · 최근 24개월 계약(전월세 12개월)</div>';
    if (!R) h += '<p class="s"><b>이 구는 이 자료를 아직 받지 않았습니다.</b> 토지·공장·창고 실거래는 2026-11-16 경기도부터 받기 시작했습니다.</p>';
    else if (isRent) { var a0 = scope(R, ST.umd, 0), a1 = scope(R, ST.umd, 1), use = a0.length ? a0 : a1.length ? a1 : R, lab = a0.length ? ST.umd : a1.length ? (e || ST.umd) + ' 전체(이 리에는 없어 넓힘)' : D.nm + ' 전체(이 읍·면에도 없어 넓힘)';
      h += '<h4>' + esc(lab) + ' — ' + use.length + '곳</h4><table>' + use.slice(0, 12 + ST.more * 20).map(function (r) { return '<tr><td>' + esc(r.nm) + '<small>' + esc(r.umd) + '</small></td><td class="r">전세 ' + r.jn + '건<small>' + (r.jper ? '평당 보증금 ' + man(r.jper * PY) : r.jdep ? '보증금 가운데 ' + man(r.jdep) : '') + '</small></td><td class="r">월세 ' + r.wn + '건<small>' + (r.wm != null ? '월 ' + man(r.wm) + (r.wd != null ? ' / 보증금 ' + man(r.wd) : '') : '') + '</small></td></tr>'; }).join('') + '</table>' + (use.length > 12 + ST.more * 20 ? '<button class="mr" data-more="1">더 보기</button>' : '');
      h += '<p class="s">전월세는 건별이 아니라 단지·법정동마다 묶은 가운데값입니다. 상가·농지 임대료는 실거래 신고 대상이 아니라 건별 자료가 없습니다(상가는 레이어 「💰 상가 임대」의 상권 통계).</p>'; }
    else { var r0 = scope(R, ST.umd, 0), r1 = scope(R, ST.umd, 1);
      h += '<h4>' + esc(ST.umd) + '</h4>' + sum(r0) + (r0.length ? tbl(r0, 8 + ST.more * 20) + (r0.length > 8 + ST.more * 20 ? '<button class="mr" data-more="1">더 보기(' + (r0.length - 8 - ST.more * 20) + '건)</button>' : '') : '<p class="s">이 리에는 최근 24개월 이 종류의 거래가 없습니다 — 아래 넓힌 범위를 보세요.</p>');
      if (r0.length < 5 && e && r1.length > r0.length) h += '<h4>' + esc(e) + ' 전체(넓혀 봄)</h4>' + sum(r1) + tbl(r1, 8);
      if (r0.length < 5 && (!e || r1.length < 5)) h += '<h4>' + esc(D.nm) + ' 전체(넓혀 봄)</h4>' + sum(R) + tbl(R, 8);
      var by = {}; R.forEach(function (r) { (by[r.umd] = by[r.umd] || []).push(r); });
      var top = Object.keys(by).map(function (u) { var v = by[u].filter(function (r) { return !r.part && r.per; }).map(function (r) { return r.per; }); return [u, by[u].length, med(v), by[u][0].ym]; }).sort(function (a, b) { return b[1] - a[1]; }).slice(0, 8);
      if (top.length > 1) h += '<h4>🧭 이 목적의 거래가 잦은 곳(' + esc(D.nm) + ')</h4>' + top.map(function (t) { return '<button class="lk" data-umd="' + esc(t[0]) + '"><b>' + esc(t[0]) + '</b> · ' + t[1] + '건' + (t[2] && ST.pur !== 'all' ? ' · 평당 ' + man(t[2] * PY) : '') + ' · 최근 ' + ymS(t[3]) + ' ›</button>'; }).join('') + '<p class="s">누르면 그곳으로 갑니다. 건수 순서일 뿐 좋고 나쁨이 아닙니다.</p>'; }
    var src = ST.pur === 'all' ? { source: '국토교통부 실거래가(공공데이터포털) — 토지·공장 및 창고·상업업무용·단독다가구·아파트·연립·오피스텔 매매' } : ST.pur === 'shop' ? D.rt : ST.pur === 'house' ? D.sh : ST.pur === 'apt' ? D.de : isRent ? D.ho : D.lt;
    h += '<p class="s">출처: ' + esc(src && src.source || '국토교통부 실거래가') + '. 해제된 거래는 뺐습니다. 땅·단독·건물 통째 거래는 국토부가 지번을 가려 리·법정동까지만 압니다. 지분 거래는 한 필지의 일부라 단가가 튀어 가운데값에서 뺐습니다. 마지막 달은 신고 기한이 안 지나 덜 찼을 수 있습니다. 시세 감정이 아니라 신고된 거래 기록입니다.</p>';
    el.innerHTML = h; }
  function pick(D, p) { if (!D.lt) return D.ho ? D.ho.umds[0] : null; var best = null, bd = 1e9; D.lt.pos.forEach(function (q, i) { if (!q) return; var d = Math.pow((q[0] - p.lon) * 0.8, 2) + Math.pow(q[1] - p.lat, 2); if (d < bd) { bd = d; best = D.lt.umds[i]; } }); return [best, bd]; }
  function open(o) {
    css(); var el = box(), cd = $('m2dCard'); if (cd) cd.classList.remove('on'); el.classList.add('on'); document.body.classList.add('dealon'); ST.D = null; ST.msg = ''; ST.more = 0; if (o && o.pur) ST.pur = o.pur; ST.umd0 = o && o.umd; paint();
    boot().then(function () { var p = o && o.lat ? o : (window.TGMap2D && TGMap2D.here ? TGMap2D.here() : null); if (!p) throw new Error('자리를 모른다'); var G = gusAt(p); if (!G.length) throw new Error('이 자리의 시군구 자료가 없다');
      return Promise.all(G.map(function (g) { return load(g.gu).then(function (D) { D.nm = g.name; return D; }); })).then(function (Ds) { var best = null; Ds.forEach(function (D) { var k = pick(D, p); if (k && Array.isArray(k) && (!best || k[1] < best[1])) best = [D, k[1], k[0]]; }); if (!best) { best = [Ds[0], 0, Ds[0].ho ? Ds[0].ho.umds[0] : null]; } ST.D = best[0]; ST.umd = (o && o.umd) || best[2]; paint(); }); })
      .catch(function (e) { ST.msg = '열지 못했습니다: ' + e.message; paint(); });
  }
  /* 동·리·구 카드 끝에 들어가는 단추 — map2d.js 는 건드리지 않는다 */
  function hook() { var cd = $('m2dCard'); if (!cd || !window.MutationObserver) return; var t = null; new MutationObserver(function () { clearTimeout(t); t = setTimeout(function () { if (!cd.classList.contains('on') || !cd.querySelector('.dgg') || cd.querySelector('.m2d-dealb')) return; css(); var b = document.createElement('button'); b.className = 'm2d-dealb'; b.textContent = '🏷 이 둘레 최근 거래 · 목적으로 찾기(농지·공장·상가·주택·전월세)'; b.onclick = function (e) { e.stopPropagation(); open(); }; cd.appendChild(b); }, 120); }).observe(cd, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] }); }
  window.tgDeal = { open: open, rows: rows, rentRows: rentRows, scope: scope, state: function () { return ST; } };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hook); else hook();
  if (/[#&]deal=1/.test(location.hash)) setTimeout(function () { open(); }, 1500);
})();
