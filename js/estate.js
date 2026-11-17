/* estate.js — 🏠 단지 실거래 자세히 v1 (2026-11-17 · 소유자 「부동산을 눌러 보면 거의 네이버 부동산급이 되어야 — 부족한 점·추가할 점을 권고대로」)
   단지 카드(map2d.js homeCard — 「🧾 세무」 단추의 data-taxh = 구|단지번호)가 열리면 그 아래에 붙인다 — map2d.js 는 안 고친다
   자료 = 권역 저장소 r/<구>/deals.json(국토교통부 실거래가 · 아파트·오피스텔·연립다세대 매매 24개월 · 건별: 연월·전용면적·금액 · 해제 표시)
   보이는 것: 면적별 표(건수·최근·최고·최저·평당) · 24개월 가격 흐름 점 그림 · 최근 거래 목록 · 매물(호가)은 공공자료에 없다고 밝히고 바깥 검색 링크만
   시세 감정·추천 아님 · 저장·전송 없음 */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var ONGH = /github\.io$/.test(location.hostname), REG = null, CACHE = {}, PY = 3.3058, COL = ['#2563eb', '#dc2626', '#059669', '#d97706', '#7c3aed', '#64748b'];
  function get(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(String(r.status)); return r.json(); }); }
  function boot() { if (REG) return Promise.resolve(); return get('data/regions.json').then(function (j) { REG = {}; j.regions.forEach(function (g) { REG[g.sido] = g.repo; }); }); }
  function load(gu) { if (CACHE[gu]) return CACHE[gu]; return CACHE[gu] = boot().then(function () { return get((ONGH ? '/' + REG[gu.slice(0, 2)] + '/' : 'data/') + 'r/' + gu + '/deals.json'); }); }
  function eok(v) { if (v >= 10000) { var e = v / 10000; return (e >= 100 ? Math.round(e) : e.toFixed(e >= 10 ? 1 : 2).replace(/\.?0+$/, '')) + '억'; } return Math.round(v).toLocaleString() + '만'; }
  function ymS(y) { return String(y).slice(2, 4) + '.' + String(y).slice(4, 6); }
  function ymI(y) { return Math.floor(y / 100) * 12 + y % 100 - 1; }

  /* 한 단지의 거래 — [{ym, area(㎡), amt(만 원), can(해제)}] */
  function trades(D, k) { var ci = -1; D.c.forEach(function (c, i) { if (String(c[4]) === String(k)) ci = i; }); if (ci < 0) return null;
    return { c: D.c[ci], t: D.d.filter(function (d) { return d[0] === ci; }).map(function (d) { return { ym: d[1], area: d[2] / 100, amt: d[3], can: !!d[4] }; }).sort(function (a, b) { return b.ym - a.ym || b.amt - a.amt; }) }; }
  function groups(T) { var g = {}; T.forEach(function (t) { if (t.can) return; var k = Math.round(t.area); (g[k] = g[k] || []).push(t); });
    return Object.keys(g).map(function (k) { var a = g[k], am = a.map(function (t) { return t.amt; }); return { k: +k, n: a.length, last: a[0], max: Math.max.apply(null, am), min: Math.min.apply(null, am), per: a[0].amt / a[0].area }; }).sort(function (a, b) { return b.n - a.n || a.k - b.k; }); }
  function chart(T, G) { var ok = T.filter(function (t) { return !t.can; }); if (ok.length < 2) return '';
    var x0 = Math.min.apply(null, ok.map(function (t) { return ymI(t.ym); })), x1 = Math.max.apply(null, ok.map(function (t) { return ymI(t.ym); })), y0 = Math.min.apply(null, ok.map(function (t) { return t.amt; })), y1 = Math.max.apply(null, ok.map(function (t) { return t.amt; }));
    if (x1 === x0) x1 = x0 + 1; var pad = (y1 - y0) * 0.12 || y1 * 0.1; y0 -= pad; y1 += pad; var W = 320, H = 140, L = 44, R = 8, T0 = 8, B = 20;
    var X = function (m) { return L + (m - x0) / (x1 - x0) * (W - L - R); }, Y = function (v) { return T0 + (1 - (v - y0) / (y1 - y0)) * (H - T0 - B); }, gi = {}; G.slice(0, 5).forEach(function (g, i) { gi[g.k] = i; });
    var s = '<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="24개월 실거래 가격 흐름" style="width:100%;height:auto;display:block">';
    [0, 0.5, 1].forEach(function (f) { var v = y0 + (y1 - y0) * f, y = Y(v); s += '<line x1="' + L + '" x2="' + (W - R) + '" y1="' + y + '" y2="' + y + '" stroke="currentColor" stroke-opacity=".15"/><text x="' + (L - 4) + '" y="' + (y + 3.5) + '" text-anchor="end" font-size="10" fill="currentColor" fill-opacity=".7">' + eok(v) + '</text>'; });
    [x0, Math.round((x0 + x1) / 2), x1].forEach(function (m, i) { s += '<text x="' + X(m) + '" y="' + (H - 5) + '" text-anchor="' + (i === 0 ? 'start' : i === 2 ? 'end' : 'middle') + '" font-size="10" fill="currentColor" fill-opacity=".7">' + String(Math.floor(m / 12)).slice(2) + '.' + ('0' + (m % 12 + 1)).slice(-2) + '</text>'; });
    /* 면적 묶음마다 달 가운데값을 이은 선 + 거래 점 */
    G.slice(0, 5).forEach(function (g, i) { var by = {}; ok.forEach(function (t) { if (Math.round(t.area) === g.k) (by[ymI(t.ym)] = by[ymI(t.ym)] || []).push(t.amt); });
      var pts = Object.keys(by).map(Number).sort(function (a, b) { return a - b; }).map(function (m) { var a = by[m].sort(function (p, q) { return p - q; }); return [X(m), Y(a[Math.floor(a.length / 2)])]; });
      if (pts.length > 1) s += '<polyline fill="none" stroke="' + COL[i] + '" stroke-width="1.6" stroke-opacity=".75" points="' + pts.map(function (p) { return p[0].toFixed(1) + ',' + p[1].toFixed(1); }).join(' ') + '"/>'; });
    ok.forEach(function (t) { var i = gi[Math.round(t.area)]; s += '<circle cx="' + X(ymI(t.ym)).toFixed(1) + '" cy="' + Y(t.amt).toFixed(1) + '" r="2.6" fill="' + COL[i == null ? 5 : i] + '" stroke="#fff" stroke-width=".6"/>'; });
    return s + '</svg><div class="es-lg">' + G.slice(0, 5).map(function (g, i) { return '<span><i style="background:' + COL[i] + '"></i>전용 ' + g.k + '㎡</span>'; }).join('') + (G.length > 5 ? '<span><i style="background:' + COL[5] + '"></i>그 밖</span>' : '') + '</div>'; }
  function html(R, more) { var T = R.t, G = groups(T), ok = T.filter(function (t) { return !t.can; });
    if (!T.length) return '<div class="es"><b>📈 실거래 자세히</b><p class="s">이 단지는 최근 24개월 매매 신고가 없습니다.</p>' + out(R) + '</div>';
    var h = '<div class="es"><b>📈 실거래 자세히 — 매매 ' + ok.length + '건(24개월)</b>' + chart(T, G);
    h += '<table><tr><th>전용면적</th><th>건수</th><th>가장 최근</th><th>최고 ~ 최저</th></tr>' + G.map(function (g) { return '<tr><td>' + g.k + '㎡<small>' + Math.round(g.k / PY) + '평(전용)</small></td><td>' + g.n + '</td><td><b>' + eok(g.last.amt) + '</b><small>' + ymS(g.last.ym) + ' · 평당 ' + eok(g.per * PY) + '</small></td><td>' + eok(g.max) + (g.max !== g.min ? ' ~ ' + eok(g.min) : '') + '</td></tr>'; }).join('') + '</table>';
    var n = more ? T.length : 6; h += '<div class="es-h">최근 거래</div><table>' + T.slice(0, n).map(function (t) { return '<tr' + (t.can ? ' class="can"' : '') + '><td>' + ymS(t.ym) + '</td><td>전용 ' + t.area + '㎡' + (t.can ? ' <i>해제</i>' : '') + '</td><td><b>' + eok(t.amt) + '</b></td><td>평당 ' + eok(t.amt / t.area * PY) + '</td></tr>'; }).join('') + '</table>' + (T.length > n ? '<button class="es-more" data-esmore="1">전체 ' + T.length + '건 보기</button>' : '');
    return h + '<p class="s">국토교통부 실거래가 신고 기록(계약 연월 기준 · 층·동·일자는 받지 않음). 평당은 전용면적 기준이라 흔히 말하는 공급면적 기준보다 높게 나옵니다. 해제된 거래는 목록에 표시하고 표·그림에서는 뺐습니다. 마지막 달은 신고 기한(30일)이 안 지나 덜 찼을 수 있습니다.</p>' + out(R) + '</div>'; }
  function out(R) { var q = encodeURIComponent(R.c[1] + ' 매물'); return '<p class="s">지금 나와 있는 매물(호가)·세대수·평면도는 공공자료에 없습니다. <a href="https://search.naver.com/search.naver?query=' + q + '" target="_blank" rel="noopener noreferrer">네이버에서 「' + esc(R.c[1]) + ' 매물」 찾기 ↗</a> (바깥 사이트로 단지 이름만 넘어갑니다)</p>'; }
  function css() { if ($('m2dEsCss')) return; var s = document.createElement('style'); s.id = 'm2dEsCss';
    s.textContent = '#m2dCard .es{border-top:1px solid var(--line,#ddd);margin-top:8px;padding-top:8px;font-size:13px}#m2dCard .es table{width:100%;border-collapse:collapse;font-size:12.5px;margin:6px 0}#m2dCard .es th{font-weight:600;font-size:11.5px;color:var(--ink2,#555);text-align:right;padding:2px}#m2dCard .es th:first-child,#m2dCard .es td:first-child{text-align:left}#m2dCard .es td{padding:4px 2px;border-top:1px dashed var(--line,#ddd);text-align:right;vertical-align:top;white-space:nowrap}#m2dCard .es td small{display:block;font-size:11px;color:var(--ink2,#555)}#m2dCard .es tr.can td{opacity:.5;text-decoration:line-through}#m2dCard .es tr.can i{font-style:normal;text-decoration:none;color:#b45309}' +
      '#m2dCard .es-lg{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:11.5px;color:var(--ink2,#555)}#m2dCard .es-lg i{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:3px}#m2dCard .es-h{font-weight:700;margin-top:8px}#m2dCard .es .s{font-size:12px;color:var(--ink2,#555);margin:6px 0 0}#m2dCard .es-more{width:100%;min-height:36px;border-radius:10px;border:1px solid var(--line,#ddd);background:var(--chip,#f3f4f6);color:inherit;cursor:pointer}';
    document.head.appendChild(s); }
  function put(cd, key, more) { var a = key.split('|'); load(a[0]).then(function (D) { var b = cd.querySelector('[data-taxh]'); if (!b || b.getAttribute('data-taxh') !== key) return; var R = trades(D, a[1]); if (!R) return; css();
      var old = cd.querySelector('.es'); if (old) old.remove(); var d = document.createElement('div'); d.innerHTML = html(R, more); var box = b.closest('.lg-btns') || b; box.parentNode.insertBefore(d.firstChild, box);
      var mb = cd.querySelector('[data-esmore]'); if (mb) mb.onclick = function (e) { e.stopPropagation(); put(cd, key, true); }; }).catch(function () {}); }
  function hook() { var cd = $('m2dCard'); if (!cd || !window.MutationObserver) return; var t = null; new MutationObserver(function () { clearTimeout(t); t = setTimeout(function () { if (!cd.classList.contains('on')) return; var b = cd.querySelector('[data-taxh]'); if (!b || cd.querySelector('.es')) return; put(cd, b.getAttribute('data-taxh'), false); }, 100); }).observe(cd, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] }); }
  window.tgEstate = { trades: trades, groups: groups, html: html, load: load };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', hook); else hook();
})();
