/* 데이터 압축지도 — 🧭 오늘의 결정 (팔란티어 방식: 결정 → 근거 객체 → 행동 기록 → 되돌아보기)
   소유자 2026-10-23 「온톨로지 팔란티어 방식을 내 앱들에 · 지도와 티북에 구현」 · 설계 = 지식베이스/14_팔란티어AIP/설계_앱적용.md
   자료 = data/decide-seocho.json(tools/onto/decide-bake.py · 원자료 값 그대로) · 순위는 결정마다 잣대 하나 · 섞은 점수 없음
   행동 기록 = 이 기기 localStorage tg_map2d_dec_log 에만(교차로 id · 한 일 · 까닭) · 좌표·사람·차량번호 안 씀
   열기: 도구 모음 「🧭 오늘의 결정」 · 주소 #dec=1 (T-Book 등에서) · window.tgDecide.open() */
(function () {
  'use strict';
  var URL_DATA = 'data/decide-seocho.json', TB = 'https://340patrolman.github.io/traffic-app/#laws', LOGK = 'tg_map2d_dec_log';
  var DATA = null, LOADING = null, ST = { tab: 'd1', date: '', slot: '18-24', goal: '사고', slot2: '22-24', form: null, focus: null };
  var WD = '일월화수목금토', SLOTS = ['00-06', '06-12', '12-18', '18-24'], SLOTN = { '00-06': '새벽 0~6시', '06-12': '오전 6~12시', '12-18': '낮 12~18시', '18-24': '저녁 18~24시' };
  var GOALS = { '사고': '그 시간대 둘레 사고 10년 합', '공백': '그 시간대 사고 — 100m 안 경찰 카메라 없는 곳만', '보행자': '보행자 피해 10년 합(하루 전체)' };
  var PII = [/01[016789][-\s]?\d{3,4}[-\s]?\d{4}/, /\d{6}[-\s]?[1-4]\d{6}/, /\d{2,3}\s?[가-힣]\s?\d{4}/];

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function m(la1, lo1, la2, lo2) { return Math.sqrt(Math.pow((lo1 - lo2) * 88400, 2) + Math.pow((la1 - la2) * 111000, 2)); }
  function fmt(n) { return n == null ? '—' : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function today() { var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function dow(ds) { var p = ds.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]).getDay(); }
  function slotOfHour(h) { return SLOTS[Math.min(3, Math.floor(h / 6))]; }
  function slotIdx(s) { return SLOTS.indexOf(s); }
  function logGet() { try { return JSON.parse(localStorage.getItem(LOGK) || '[]'); } catch (e) { return []; } }
  function logSet(a) { try { localStorage.setItem(LOGK, JSON.stringify(a)); return true; } catch (e) { return false; } }

  function css() {
    if ($('m2dDecCss')) return; var s = document.createElement('style'); s.id = 'm2dDecCss';
    s.textContent = '#m2dDec{position:fixed;left:8px;right:8px;bottom:calc(8px + env(safe-area-inset-bottom));z-index:6;max-height:62vh;overflow:auto;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:14px;padding:12px 14px 10px;box-shadow:0 8px 24px rgba(0,0,0,.22);display:none;font-size:13.5px}' +
      '#m2dDec.on{display:block}@media (min-width:760px){#m2dDec{right:auto;width:420px;max-height:72vh}}' +
      '#m2dDec h3{margin:0 70px 6px 0;font-size:16px}#m2dDec .x{position:absolute;right:10px;top:8px;height:34px;padding:0 12px;border-radius:10px;border:1px solid var(--line);background:var(--chip);color:var(--ink);cursor:pointer}' +
      '#m2dDec .tabs{display:flex;gap:4px;flex-wrap:wrap;margin:4px 0 8px}#m2dDec .tabs button{flex:1 1 auto;min-height:36px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);font-weight:700;font-size:13px;cursor:pointer;padding:0 8px}#m2dDec .tabs button.on{background:var(--chipOn);color:var(--chipOnInk);border-color:var(--chipOn)}' +
      '#m2dDec .ctl{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:6px}#m2dDec .ctl select,#m2dDec .ctl input{min-height:36px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);font-size:13px;padding:0 8px}' +
      '#m2dDec .rule{font-size:12px;color:var(--ink2);margin:2px 0 8px}#m2dDec .cd{border:1px solid var(--line);border-radius:12px;padding:8px 10px;margin:6px 0}#m2dDec .cd .t{display:flex;align-items:baseline;gap:8px}#m2dDec .cd .t b{font-size:15px}#m2dDec .cd .t .k{margin-left:auto;font-size:20px;font-weight:800;color:var(--acc);font-variant-numeric:tabular-nums}' +
      '#m2dDec .cd .s{font-size:12px;color:var(--ink2)}#m2dDec .ev{margin:4px 0 0;padding:0;list-style:none}#m2dDec .ev li{font-size:12.5px;padding:2px 0;border-top:1px dashed var(--line)}#m2dDec .btns{display:flex;gap:6px;margin-top:6px}#m2dDec .btns button,#m2dDec .btns a{flex:1;min-height:36px;border:1px solid var(--line);border-radius:10px;background:var(--chip);color:var(--ink);font-weight:700;font-size:13px;cursor:pointer;display:flex;align-items:center;justify-content:center;text-decoration:none}' +
      '#m2dDec details summary{cursor:pointer;font-size:12.5px;color:var(--acc);margin-top:4px}#m2dDec .warn{font-size:12px;color:#b45309;margin:4px 0}:root.dark #m2dDec .warn{color:#fbbf24}#m2dDec .src{margin-top:8px;font-size:11.5px;color:var(--ink2)}' +
      '#m2dDec .hb{display:flex;gap:2px;align-items:flex-end;height:40px;margin-top:4px}#m2dDec .hb i{flex:1;background:#94a3b8;border-radius:2px 2px 0 0;min-height:1px}#m2dDec .hb i.n{background:#dc2626}#m2dDec .hl{display:flex;gap:2px}#m2dDec .hl span{flex:1;text-align:center;font-size:9.5px;color:var(--ink2)}' +
      '#m2dDec .fm{border:1px dashed var(--acc);border-radius:10px;padding:8px;margin-top:6px}#m2dDec .fm select,#m2dDec .fm input{width:100%;min-height:36px;margin:3px 0;border:1px solid var(--line);border-radius:8px;background:var(--chip);color:var(--ink);font-size:13px;padding:0 8px;box-sizing:border-box}';
    document.head.appendChild(s);
  }
  function box() { var el = $('m2dDec'); if (el) return el; el = document.createElement('div'); el.id = 'm2dDec'; el.setAttribute('aria-label', '오늘의 결정'); document.body.appendChild(el); el.addEventListener('click', onClick); el.addEventListener('change', onChange); return el; }

  function load() {
    if (DATA) return Promise.resolve(DATA); if (LOADING) return LOADING;
    LOADING = fetch(URL_DATA, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); }).then(function (d) {
      DATA = d; d.into = {};
      Object.keys(d.int).forEach(function (i) { (d.int[i][14] || []).forEach(function (x) { (d.into[x[0]] = d.into[x[0]] || []).push([i, x[1]]); }); });
      return d; });
    return LOADING;
  }
  function nm(i) { var r = DATA.int[i] || DATA.nb[i]; return r ? r[0] : i; }
  function ll(i) { var r = DATA.int[i] || DATA.nb[i]; return r ? [r[1], r[2]] : null; }
  function slotAcc(i, s) { var r = DATA.int[i]; return r ? r[5][slotIdx(s)] : 0; }
  function upstream(area, k) { var U = {}; Object.keys(area).forEach(function (t) { (DATA.into[t] || []).forEach(function (x) { if (!area[x[0]] && (!U[x[0]] || x[1] < U[x[0]][1])) U[x[0]] = [t, x[1]]; }); });
    return Object.keys(U).sort(function (a, b) { return U[a][1] - U[b][1] || (a < b ? -1 : 1); }).slice(0, k || 3).map(function (f) { return [f, U[f][0], U[f][1]]; }); }
  function around(la, lo, r, s, k) { var all = Object.keys(DATA.int).filter(function (i) { var v = DATA.int[i]; return m(la, lo, v[1], v[2]) <= r; }), area = {};
    all.forEach(function (i) { area[i] = 1; }); return { top: all.sort(function (a, b) { return slotAcc(b, s) - slotAcc(a, s) || (a < b ? -1 : 1); }).slice(0, k || 3), area: area }; }
  function lawLines(vid) { var v = DATA.vio[vid]; if (!v) return ''; if (!v[1].length) return '<li>⚖ ' + esc(v[0]) + ' — T-Book 범칙금 DB 에 같은 이름의 항목 없음(지어 잇지 않음)</li>';
    return v[1].map(function (l) { var L = DATA.law[l]; return L ? '<li>⚖ ' + esc(L[0]) + ' — ' + esc(L[1]) + ' <small>(' + esc(L[2]) + (L[3].length ? ' · 판례 ' + esc(L[3].join(', ')) : '') + ' · T-Book 글 그대로 · 이름 맞대기 C)</small></li>' : ''; }).join(''); }
  function dayEvents(ds) { var out = [], D3 = DATA.d3, w = dow(ds);
    D3.rally.forEach(function (x) { if (x[0] === ds) out.push({ k: '집회', t: (x[1] || '?') + '~' + (x[2] || '?'), p: x[3], n: x[4], march: x[5], la: x[6], lo: x[7], dest: x[8], h: x[1] ? +x[1].slice(0, 2) : 12 }); });
    D3.shows.forEach(function (s) { if (s[4] <= ds && ds <= s[5]) { var tm = showTimes(s[6], w); out.push({ k: '공연', t: tm.length ? tm.join(' · ') : '시각 원문: ' + s[6], p: s[0] + ' — ' + s[3] + '(' + s[8] + ' ' + fmt(s[9]) + '석)', la: s[1], lo: s[2], ends: tm.map(function (t) { var mm = +t.slice(0, 2) * 60 + +t.slice(3) + (s[7] || 0); return ('0' + Math.floor(mm / 60) % 24).slice(-2) + ':' + ('0' + mm % 60).slice(-2); }), dur: s[7], seats: s[9], h: tm.length ? (+tm[tm.length - 1].slice(0, 2) + Math.round((s[7] || 0) / 60)) % 24 : 19 }); } });
    return out; }
  function showTimes(txt, w) { var found = [], re = /([^()]+)\(([^)]*)\)/g, g, WN = '월화수목금토일', wk = (w + 6) % 7;
    while ((g = re.exec(txt || ''))) { var days = g[1].replace(/^[\s,]+|[\s,]+$/g, ''), ok = false, r = /(.)요일\s*~\s*(.)요일/.exec(days);
      if (r) { var a = WN.indexOf(r[1]), b = WN.indexOf(r[2]); ok = a <= wk && wk <= b; } else ok = days.split(',').some(function (d) { return d.trim() === WN.charAt(wk) + '요일'; });
      if (ok) found = found.concat(g[2].match(/\d{1,2}:\d{2}/g) || []); }
    return found; }

  /* ---------- D1 어디 설까 ---------- */
  function d1() { var s = ST.slot, g = ST.goal, I = DATA.int, key = function (i) { return g === '사고' ? I[i][5][slotIdx(s)] : g === '공백' ? (I[i][11] ? -1 : I[i][5][slotIdx(s)]) : I[i][7]; };
    var chosen = [], same = {}; Object.keys(I).sort(function (a, b) { return key(b) - key(a) || (a < b ? -1 : 1); }).some(function (i) { if (key(i) < 0) return true;
      var near = chosen.filter(function (c) { return m(I[i][1], I[i][2], I[c][1], I[c][2]) <= 150; })[0]; if (near) { (same[near] = same[near] || []).push(i); return false; } chosen.push(i); return chosen.length >= 5; });
    var ev = dayEvents(ST.date), h = '<div class="ctl"><select data-k="slot">' + SLOTS.map(function (x) { return '<option value="' + x + '"' + (x === s ? ' selected' : '') + '>' + SLOTN[x] + '</option>'; }).join('') + '</select><select data-k="goal">' + Object.keys(GOALS).map(function (x) { return '<option' + (x === g ? ' selected' : '') + '>' + x + '</option>'; }).join('') + '</select></div>';
    h += '<div class="rule">잣대: <b>' + GOALS[g] + '</b> · 150m 안 이웃은 한 자리로 · 사고 = TAAS 2016~2025 교차로 70m 안 100m 칸 합(근사)</div>' + focusBox();
    chosen.forEach(function (i, k) { var r = I[i], sv = ''; h += '<div class="cd"><div class="t"><span>' + (k + 1) + '</span><b>' + esc(r[0]) + '</b><span class="s">' + esc(r[3]) + '</span><span class="k">' + fmt(key(i)) + '</span></div>';
      h += '<div class="s">' + (g === '보행자' ? '보행자 피해' : SLOTN[s] + ' 사고') + ' · 10년 ' + fmt(r[4]) + ' · 밤 ' + fmt(r[6]) + ' · 보행자 ' + fmt(r[7]) + ' · 사망 ' + r[8] + ' · 중상 ' + r[9] + '</div><ul class="ev">';
      if (same[i]) h += '<li>같은 자리: ' + esc(same[i].map(nm).join(', ')) + '</li>';
      h += '<li>📷 100m 안 경찰 카메라 ' + r[11] + '대 · 🏫 300m 안 보호구역 시설 ' + r[12] + '곳' + (r[13] != null ? '(가장 가까운 ' + r[13] + 'm)' : '') + '</li>';
      if (r[10][0]) h += '<li>🚦 주 위반: ' + r[10].map(function (x) { return esc(DATA.vio[x[0]] ? DATA.vio[x[0]][0] : x[0]) + ' ' + x[1] + '건'; }).join(' · ') + '</li>' + lawLines(r[10][0][0]);
      DATA.hot.forEach(function (x) { if (m(r[1], r[2], x[1], x[2]) <= 120) sv += '<li>🔺 TAAS 다발지 「' + esc(x[0]) + '」 ' + esc(x[3].join('·')) + ' · ' + esc(x[4].join(', ')) + '</li>'; });
      ev.forEach(function (e) { var d = m(r[1], r[2], e.la, e.lo); if (d <= 1500) sv += '<li>📢 ' + e.k + ' ' + esc(e.t) + ' ' + esc(e.p) + ' · ' + Math.round(d) + 'm</li>'; });
      if (r[14].length) sv += '<li>➡ 길 따라 다음 신호: ' + r[14].map(function (x) { return esc(nm(x[0])) + ' ' + x[1] + 'm(' + slotAcc(x[0], s) + ')'; }).join(' · ') + '</li>';
      h += sv + '</ul>' + btns(i, k + 1, 'd1:' + s + ':' + g) + '</div>'; });
    return h; }
  /* 대상 하나에서 결정으로(2026-10-23 게임 세션 「🧩 엮어서 답 찾기」 사슬 카드가 부른다) — tgDecide.open('d1', { int: 'INT-…' }) · #dec=1&int=INT-…
     이 교차로가 시간대 넷 × 목적 셋에서 몇 위인지(이웃 묶음 없이 그 잣대 그대로 · 같은 값은 같은 순위) */
  function focusBox() { var f = ST.focus, I = DATA.int, via = '';
    if (!f && ST.focusLL) { var la = ST.focusLL[0], lo = ST.focusLL[1], best = null, bd = 151;   /* 좌표로 부를 때 — 150m 안 가장 가까운 사고 교차로(게임 세션 큰비 사슬 · polA 좌표) */
      Object.keys(I).forEach(function (i) { var d = m(la, lo, I[i][1], I[i][2]); if (d < bd) { bd = d; best = i; } });
      if (!best) return '<div class="warn">📌 누른 자리 150m 안에 둘레 사고 기록이 있는 교차로가 없다 — 이 결정의 후보가 아니다</div>';
      f = best; via = ' · 누른 자리에서 ' + Math.round(bd) + 'm'; }
    if (!f) return ''; if (!I[f]) return '<div class="warn">📌 ' + esc(nm(f)) + ' — 둘레 사고 기록이 없는 교차로라 이 결정의 후보가 아니다</div>';
    var rows = SLOTS.map(function (s) { var si = slotIdx(s); return '<tr><td>' + SLOTN[s] + '</td>' + ['사고', '공백'].map(function (g) {
        if (g === '공백' && I[f][11]) return '<td>카메라 있음</td>'; var v = I[f][5][si], n = 1 + Object.keys(I).filter(function (i) { return (g === '사고' || !I[i][11]) && I[i][5][si] > v; }).length; return '<td><b>' + n + '위</b> · ' + v + '</td>'; }).join('') + '</tr>'; }).join('');
    var pn = 1 + Object.keys(I).filter(function (i) { return I[i][7] > I[f][7]; }).length;
    return '<div class="cd" style="border-color:var(--acc)"><div class="t"><span>📌</span><b>' + esc(I[f][0]) + '</b><span class="s">' + esc(I[f][3]) + via + ' · 사고 있는 교차로 ' + Object.keys(I).length + '곳 중</span><button data-unfocus="1" style="margin-left:auto;border:1px solid var(--line);border-radius:8px;background:var(--chip);color:var(--ink)">✕</button></div>' +
      '<table style="width:100%;font-size:12.5px;border-collapse:collapse"><tr><th></th><th>사고</th><th>카메라 공백</th></tr>' + rows + '</table><div class="s">보행자 피해 ' + I[f][7] + ' — ' + pn + '위 · 같은 값은 같은 순위</div>' + btns(f, '대상에서', 'd1:' + ST.slot + ':' + ST.goal) + '</div>'; }
  function btns(i, rank, ctx) { var p = ll(i); return '<div class="btns"><button data-go="' + p[0] + ',' + p[1] + '">🗺 지도에서</button><button data-did="' + i + '|' + rank + '|' + ctx + '">✋ 여기 섰다</button>' + (ctx.indexOf('d1') === 0 && DATA.int[i] && DATA.int[i][10][0] && DATA.vio[DATA.int[i][10][0][0]] && DATA.vio[DATA.int[i][10][0][0]][1].length ? '<a href="' + TB + '" target="_blank" rel="noopener">⚖ T-Book</a>' : '') + '</div>' + (ST.form === i + '|' + ctx ? form(i, rank, ctx) : ''); }
  function form(i, rank, ctx) { return '<div class="fm"><b>기록 — ' + esc(nm(i)) + '</b><select id="m2dDecDid"><option>정체</option><option>위반</option><option>보행자</option><option>순찰</option><option>음주</option><option>통제</option></select>' +
      '<input id="m2dDecWhy" maxlength="80" placeholder="고른 까닭 한 줄 — 사람·차량번호는 쓰지 않음"><div class="btns"><button data-save="' + i + '|' + rank + '|' + ctx + '">저장(이 기기에만)</button><button data-cancel="1">취소</button></div></div>'; }

  /* ---------- D2 음주 ---------- */
  function d2() { var D2 = DATA.d2, w = dow(ST.date), k = +ST.slot2.slice(0, 2) / 2, late = +ST.slot2.slice(0, 2) < 6, h = '<div class="ctl"><select data-k="slot2">';
    for (var x = 0; x < 12; x++) { var v = ('0' + 2 * x).slice(-2) + '-' + ('0' + (2 * x + 2)).slice(-2); h += '<option value="' + v + '"' + (v === ST.slot2 ? ' selected' : '') + '>' + v + '시</option>'; }
    h += '</select></div><div class="warn">⚠ 적발 수는 단속한 만큼 나온다 — 「음주운전이 많다」가 아니라 「이만큼 걸렸다」(경찰서 단위 · ' + D2.years[0] + '~' + D2.years[1] + ' 다섯 해 합)</div>';
    Object.keys(D2.grid).forEach(function (s) { var G = D2.grid[s], v = G[w][k], all = [], tot = 0; G.forEach(function (r) { r.forEach(function (c) { all.push(c); tot += c; }); });
      var rank = 1 + all.filter(function (c) { return c > v; }).length, mx = Math.max.apply(null, G[w]);
      h += '<div class="cd"><div class="t"><b>' + esc(s.replace('서울', '')) + '</b><span class="s">' + WD.charAt(w) + ' ' + ST.slot2 + '시</span><span class="k">' + fmt(v) + '</span></div><div class="s">한 주 84칸 중 ' + rank + '번째 · 전체 ' + fmt(tot) + '건의 ' + (tot ? (100 * v / tot).toFixed(1) : 0) + '%</div>';
      h += '<div class="hb">' + G[w].map(function (c, j) { return '<i class="' + (j === k ? 'n' : '') + '" style="height:' + Math.max(2, Math.round(40 * c / (mx || 1))) + 'px" title="' + (2 * j) + '~' + (2 * j + 2) + '시 ' + c + '건"></i>'; }).join('') + '</div><div class="hl">' + G[w].map(function (c, j) { return '<span>' + (j % 3 ? '' : 2 * j) + '</span>'; }).join('') + '</div></div>'; });
    var di = late ? 4 : 3; h += '<div class="rule">동 순위 잣대: <b>' + (late ? '0~6시 사고' : '밤 20~6시 사고') + '(10년)</b> · 주점·결제는 곁들임 · 어느 동에서 걸렸는지는 공개 자료에 없다</div>';
    DATA.d2.dong.slice().sort(function (a, b) { return (b[di] || 0) - (a[di] || 0); }).slice(0, 4).forEach(function (r, n) {
      var ins = Object.keys(DATA.int).filter(function (i) { return DATA.int[i][3] === r[1]; }).sort(function (a, b) { return DATA.int[b][6] - DATA.int[a][6]; }).slice(0, 2);
      h += '<div class="cd"><div class="t"><span>' + (n + 1) + '</span><b>' + esc(r[1]) + '</b><span class="s">' + esc((r[2] || []).join('/').replace(/서울|경찰서/g, '')) + '</span><span class="k">' + fmt(r[di]) + '</span></div><div class="s">밤 사고 ' + fmt(r[3]) + ' · 0~6시 ' + fmt(r[4]) + ' · 주점 ' + fmt(r[5]) + '곳 · 호프 0~6시 결제 ' + fmt(r[6]) + '건(서울 동 백분위 ' + (r[8][2] == null ? '—' : r[8][2]) + ')</div><ul class="ev">' +
        ins.map(function (i) { return '<li>교차로 ' + esc(nm(i)) + ' — 밤 사고 ' + DATA.int[i][6] + ' / 10년 ' + DATA.int[i][4] + '</li>'; }).join('') + '</ul>' + (ins[0] ? btns(ins[0], n + 1, 'd2:' + ST.slot2) : '') + '</div>'; });
    return h; }

  /* ---------- D3 집회·행사 ---------- */
  function d3() { var ev = dayEvents(ST.date), D3 = DATA.d3, h = '<div class="rule">둘레 교차로 잣대: <b>그 시각이 든 6시간 칸 사고 10년 합</b> · 상류 = 길 따라 바로 앞 신호 교차로(둘레 밖) — 「상류에서 먼저 끊는다 · 분기점 앞에서」(형님 원칙)</div>';
    if (ST.date > D3.collected) { var w = dow(ST.date), past = D3.rally.filter(function (x) { return dow(x[0]) === w; }), cnt = {};
      past.forEach(function (x) { var p = x[3].replace(/\s*<.*/, ''); cnt[p] = (cnt[p] || 0) + 1; });
      h += '<div class="warn">집회 글은 받은 날(' + esc(D3.collected) + ')까지만 — 경찰청이 전날 올린다. 지난 기록: 같은 요일 서초 둘레 ' + past.length + '건 · ' + esc(Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; }).slice(0, 3).map(function (p) { return p + ' ' + cnt[p]; }).join(' · ') || '없음') + '</div>'; }
    if (!ev.length) h += '<div class="cd">이 날 서초 둘레 주요집회·큰 공연 자료 없음 <span class="s">(주요집회만 · 공연은 ' + esc(D3.kopis) + ' 받은 것)</span></div>';
    ev.sort(function (a, b) { return (b.n || b.seats || 0) - (a.n || a.seats || 0); }).forEach(function (e, n) {
      var r = e.k === '집회' ? 500 : 700, s = slotOfHour(e.h), A = around(e.la, e.lo, r, s, 3), path = '';
      if (e.march && e.dest) { var p = marchPath(e.la, e.lo, e.dest[0], e.dest[1]); p.forEach(function (i) { A.area[i] = 1; }); if (p.length) path = '<li>🚶 행진 길(직선 150m 근사): ' + esc(p.map(nm).join(' → ')) + '</li>'; }
      var up = upstream(A.area, 3);
      h += '<div class="cd"><div class="t"><span>' + (e.k === '집회' ? '📢' : '🎭') + '</span><b>' + esc(e.t) + '</b><span class="k">' + (e.n ? fmt(e.n) + '명' : e.seats ? fmt(e.seats) + '석' : '') + '</span></div><div class="s">' + esc(e.p) + (e.ends && e.ends.length ? ' · 끝 약 ' + e.ends.join(' · ') + '(공연시간 ' + e.dur + '분)' : '') + '</div><ul class="ev">' + path +
        '<li>👀 둘레 ' + r + 'm 미리 볼 곳: ' + A.top.map(function (i) { return esc(nm(i)) + '(' + slotAcc(i, s) + ')'; }).join(' · ') + '</li>' + (up.length ? '<li>✂ 상류: ' + up.map(function (u) { return esc(nm(u[0])) + ' → ' + esc(nm(u[1])) + ' ' + u[2] + 'm'; }).join(' · ') + '</li>' : '') + '</ul>' +
        (up[0] ? btns(up[0][0], n + 1, 'd3:' + ST.date) : A.top[0] ? btns(A.top[0], n + 1, 'd3:' + ST.date) : '') + '</div>'; });
    return h + '<div class="src">집회 = 서울경찰청 「오늘의 주요집회」(주요 집회만 · 신고값 · 받은 날 ' + esc(D3.collected) + ') · 공연 = KOPIS(' + esc(D3.kopis) + ' 받음 · 1,000석 이상)</div>'; }
  function marchPath(la1, lo1, la2, lo2) { var vx = (lo2 - lo1) * 88400, vy = (la2 - la1) * 111000, L2 = vx * vx + vy * vy || 1, out = [];
    Object.keys(DATA.int).forEach(function (i) { var v = DATA.int[i], wx = (v[2] - lo1) * 88400, wy = (v[1] - la1) * 111000, t = Math.max(0, Math.min(1, (wx * vx + wy * vy) / L2)); if (Math.sqrt(Math.pow(wx - t * vx, 2) + Math.pow(wy - t * vy, 2)) <= 150) out.push([t, i]); });
    return out.sort(function (a, b) { return a[0] - b[0]; }).map(function (x) { return x[1]; }); }

  /* ---------- D4 큰비 ---------- */
  function d4() { var D4 = DATA.d4, h = '<div class="warn">비 예보는 지도의 날씨 층·기상청 특보로 볼 것 — 여기는 「비가 오면 어디부터」만</div><div class="rule">잣대: <b>잠긴 해 수</b>(그 길 30m 안 건물·필지가 잠긴 해 — 길 통제 기록 아님) · 지하차도는 얕은 침수에도 통제라 따로 맨 앞</div>';
    var under = D4.seg.filter(function (s) { return s[2] === '002'; }), rest = D4.seg.filter(function (s) { return s[2] !== '002'; });
    function segCard(s, n) { var near = null, dmin = 151; Object.keys(DATA.int).forEach(function (i) { var d = m(s[9], s[10], DATA.int[i][1], DATA.int[i][2]); if (d < dmin) { dmin = d; near = i; } });
      var up = near ? upstream((function () { var a = {}; a[near] = 1; return a; })(), 2) : [];
      return '<div class="cd"><div class="t"><span>' + n + '</span><b>' + esc(s[1] || '(이름 없음)') + (s[2] === '002' ? ' 🚇지하차도' : '') + '</b><span class="k">' + s[3] + '해</span></div><div class="s">마지막 ' + s[4] + ' · 가장 깊은 ' + s[5] + 'm · ' + s[6] + '차로 · 구간 ' + fmt(s[8]) + 'm · ' + (s[7] < 0 ? '돌아갈 길 없음/못 셈' : s[7] < 10 ? '곁길로 돌아도 거의 안 늦음' : '돌아가면 +' + s[7] + '초') + '</div>' +
        (near ? '<ul class="ev"><li>가까운 교차로 ' + esc(nm(near)) + ' ' + Math.round(dmin) + 'm' + (up.length ? ' · 상류 ' + up.map(function (u) { return esc(nm(u[0])) + ' ' + u[2] + 'm'; }).join(' · ') : '') + '</li></ul>' + btns(near, n, 'd4') : '<div class="btns"><button data-go="' + s[9] + ',' + s[10] + '">🗺 지도에서</button></div>') + '</div>'; }
    h += '<b>🚇 지하차도</b>' + (under.length ? under.slice(0, 4).map(function (s, n) { return segCard(s, n + 1); }).join('') : '<div class="cd">침수 흔적 30m 안 지하차도 없음</div>');
    h += '<b>그 밖의 길</b>' + rest.slice(0, 6).map(function (s, n) { return segCard(s, n + 1); }).join('');
    ['A', 'B'].forEach(function (k) { var X = D4.delay[k]; if (!X) return;
      h += '<details><summary>🚓 출동이 늦어지는 곳 — 시나리오 ' + k + ' (견주는 값 · 실제 출동 시간 아님)</summary><div class="s">' + esc(X.what) + ' · 교차로 ' + fmt(X.stat['교차로']) + '곳 중 닿지 못함 ' + fmt(X.stat['닿지 못함']) + ' · 3분 넘게 늦음 ' + fmt(X.stat['3분 넘게 늦음']) + ' · 갇힘 ' + X.trapN + '</div><div class="s">교차로별 값은 비공개 — 관할 도달 공백이 드러나는 자료라 공개 지도에 싣지 않는다</div></details>'; });
    return h + '<div class="src">서울시 침수흔적도(2010~2025 · 2022·2011·2010 큰비 흔적이 대부분 · 배수 공사 뒤 덜 잠길 수 있음) × ITS 표준노드링크 · 출동 지연 = 막힘·신호 없이 센 견줌값</div>'; }

  /* ---------- 📒 되돌아보기 ---------- */
  function d5() { var L = logGet(), h = '<div class="rule">이 기기에만 저장 · 교차로 번호·한 일·까닭만(좌표·사람·차량번호 없음)</div>';
    if (!L.length) return h + '<div class="cd">아직 기록이 없다 — 후보의 「✋ 여기 섰다」로 남긴다.</div>';
    var rk = {}, did = {}; L.forEach(function (x) { rk[x.rank] = (rk[x.rank] || 0) + 1; did[x.did] = (did[x.did] || 0) + 1; });
    h += '<div class="cd"><div class="t"><b>기록 ' + L.length + '줄</b><span class="s">' + esc(L[0].date) + ' ~ ' + esc(L[L.length - 1].date) + '</span></div><div class="s">브리핑 순위: ' + Object.keys(rk).sort().map(function (k) { return k + '위 ' + rk[k]; }).join(' · ') + ' · 한 일: ' + Object.keys(did).map(function (k) { return k + ' ' + did[k]; }).join(' · ') + '</div></div>';
    var odd = L.filter(function (x) { return String(x.rank) !== '1'; });
    if (odd.length) h += '<b>1순위가 아닌 곳을 고른 까닭 — 형님 현장 판단(규칙 후보)</b><ul class="ev">' + odd.map(function (x) { return '<li>' + esc(x.date) + ' ' + esc(x.ctx) + ' → ' + esc(x.nm) + ' [' + esc(x.rank) + '위] ' + esc(x.why) + '</li>'; }).join('') + '</ul>';
    h += '<ul class="ev">' + L.slice().reverse().slice(0, 30).map(function (x) { return '<li>' + esc(x.date) + ' · ' + esc(x.nm) + ' · ' + esc(x.did) + ' · ' + esc(x.ctx) + (x.why ? ' · ' + esc(x.why) : '') + '</li>'; }).join('') + '</ul>';
    return h + '<div class="btns"><button data-csv="1">📋 CSV 복사</button><button data-clear="1">🗑 모두 지우기</button></div><div class="s">복사한 CSV 를 Claude 에게 붙여 주면 「현장 판단 후보」로 정리해, 형님이 맞다고 한 줄만 규칙 장부에 올린다 · 사람 이름·차량번호는 적지 않는다</div>'; }

  function paint() { var el = box(); if (!DATA) { el.innerHTML = '<button class="x" data-close="1">닫기</button><h3>🧭 오늘의 결정</h3><div class="s">자료를 읽는 중…</div>'; return; }
    var T = [['d1', '어디 설까'], ['d2', '🍺 음주'], ['d3', '📢 집회·행사'], ['d4', '🌧 큰비'], ['d5', '📒 기록']], body = { d1: d1, d2: d2, d3: d3, d4: d4, d5: d5 }[ST.tab]();
    el.innerHTML = '<button class="x" data-close="1">닫기</button><h3>🧭 오늘의 결정 <small style="font-weight:400;color:var(--ink2);font-size:12px">서초 · 방배</small></h3>' +
      '<div class="ctl"><input type="date" data-k="date" value="' + ST.date + '"><span class="s">' + WD.charAt(dow(ST.date)) + '요일</span></div>' +
      '<div class="tabs">' + T.map(function (t) { return '<button data-tab="' + t[0] + '" class="' + (t[0] === ST.tab ? 'on' : '') + '">' + t[1] + '</button>'; }).join('') + '</div>' + body +
      '<div class="src">자료 한 장 data/decide-seocho.json(' + esc(DATA.made) + ' 구움) · 판단은 사람이 한다 — 이 화면은 근거를 모아 줄 뿐</div>'; }

  function onChange(e) { var k = e.target.getAttribute('data-k'); if (!k) return; ST[k] = e.target.value; if (k === 'date' && !ST.date) ST.date = today(); ST.form = null; paint(); }
  function onClick(e) { e.stopPropagation(); var b = e.target.closest('button,a'); if (!b) return; var a;
    if (b.hasAttribute('data-close')) return close();
    if (b.hasAttribute('data-unfocus')) { ST.focus = null; ST.focusLL = null; paint(); return; }
    if ((a = b.getAttribute('data-tab'))) { ST.tab = a; ST.form = null; paint(); $('m2dDec').scrollTop = 0; return; }
    if ((a = b.getAttribute('data-go'))) { var p = a.split(','); if (window.innerWidth < 760) close(); location.hash = 'v=' + p[0] + ',' + p[1] + ',250&t=' + p[0] + ',' + p[1]; return; }   /* 「PC로 보내기」 꼴 — 보고 자리 표시 없이 그 자리 카드 */
    if ((a = b.getAttribute('data-did'))) { var q = a.split('|'); ST.form = q[0] + '|' + q[2]; paint(); return; }
    if (b.hasAttribute('data-cancel')) { ST.form = null; paint(); return; }
    if ((a = b.getAttribute('data-save'))) { var z = a.split('|'), why = ($('m2dDecWhy').value || '').trim(), did = $('m2dDecDid').value;
      if (PII.some(function (r) { return r.test(why); })) { alert('까닭에 전화번호·주민번호·차량번호 꼴이 있어 저장하지 않았습니다. 사람·차량은 적지 않습니다.'); return; }
      var L = logGet(); L.push({ date: ST.date, at: (function (d) { return today() + ' ' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); })(new Date()), int: z[0], nm: nm(z[0]), rank: z[1], ctx: z.slice(2).join('|'), did: did, why: why });
      if (!logSet(L)) alert('이 기기에 저장하지 못했습니다'); ST.form = null; paint(); return; }
    if (b.hasAttribute('data-csv')) { var rows = [['날짜', '적은때', '교차로', '이름', '브리핑순위', '결정', '한일', '까닭']].concat(logGet().map(function (x) { return [x.date, x.at, x.int, x.nm, x.rank, x.ctx, x.did, x.why]; }));
      var t = rows.map(function (r) { return r.map(function (c) { c = String(c == null ? '' : c); return /[",\n]/.test(c) ? '"' + c.replace(/"/g, '""') + '"' : c; }).join(','); }).join('\n');
      if (navigator.clipboard) navigator.clipboard.writeText(t).then(function () { b.textContent = '✔ 복사됨'; }, function () { prompt('복사', t); }); else prompt('복사', t); return; }
    if (b.hasAttribute('data-clear')) { if (confirm('이 기기의 결정 기록을 모두 지울까요? 되돌릴 수 없습니다.')) { logSet([]); paint(); } return; } }

  function open(tab, opt) { css(); var el = box(); if (!ST.date) { ST.date = today(); ST.slot = slotOfHour(new Date().getHours()); }
    if (tab && /^d[1-5]$/.test(tab)) ST.tab = tab; if (opt && opt.int) { ST.focus = String(opt.int); ST.focusLL = null; ST.tab = 'd1'; } else if (opt && isFinite(+opt.lat) && isFinite(+opt.lon)) { ST.focus = null; ST.focusLL = [+opt.lat, +opt.lon]; ST.tab = 'd1'; } el.classList.add('on'); paint(); load().then(paint, function (e) { el.innerHTML = '<button class="x" data-close="1">닫기</button><h3>🧭 오늘의 결정</h3><div class="warn">자료를 읽지 못했습니다(' + esc(e && e.message) + ') — 통신이 되는 곳에서 한 번 열면 다음부터 됩니다.</div>'; }); }
  function close() { var el = $('m2dDec'); if (el) el.classList.remove('on'); }
  window.tgDecide = { open: open, close: close };
  function fromHash() { var h = location.hash || '', dm = /(^|[#&])dec=(1|d[1-5])(?=&|$)/.exec(h); if (!dm) return; var im = /(^|[#&])int=(INT-\d+)(?=&|$)/.exec(h), lm = /(^|[#&])ll=(-?[\d.]+),(-?[\d.]+)(?=&|$)/.exec(h);
    open(dm[2] === '1' ? null : dm[2], im ? { int: im[2] } : lm ? { lat: +lm[2], lon: +lm[3] } : null);
    var rest = h.replace(/^#/, '').split('&').filter(function (x) { return x && !/^(dec|int|ll)=/.test(x); }).join('&');
    try { history.replaceState(null, '', location.pathname + location.search + (rest ? '#' + rest : '')); } catch (e) {} }
  window.addEventListener('hashchange', fromHash);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', fromHash); else fromHash();
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
})();
