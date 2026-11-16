/* 가르고 「신호 사다리」 (2026-11-16 형님 「바로 앞 · 그다음 · 필요하면 그다음까지 — 안전운전·연비·환경 경제운전이 기본 · 경찰차는 다른 개념」)
   안내 중 위 판 바로 밑에 앞 신호 셋을 한 줄로 — 닿을 때 색(앞 신호에서 서는 시간까지 이어 셈) · 몇 초 · 한 마디.
   · 일반(🚗) = 경제운전 말: 녹색에 닿으면 「이대로」 · 적색이면 「발 떼기」(미리 굴러가 브레이크·연료 아낌) · 녹색 끝 무렵이면 「서두르지 않기」.
     속도를 올리라는 말은 하지 않는다(제한속도 안 · 밤 22~06시에는 말 없이 색만 — 과속을 막으려 끊어 둔 신호를 거스르지 않는다).
   · 긴급 출동(🚨) = 교차로 위험 말: 닿을 때 적색 = 「적색 진입 · 좌우 확인」 · 녹색 = 「통과」 · 셋 중 적색 진입 수를 한 줄로.
   · 업무(🔒) = 색만(말 없음).
   · 값은 gargo.js 의 신호 예측(GARGO.sigAtT · 계획값·이어 셈)을 그대로 쓴다 — 새로 지어 내지 않는다 · 자료 없는 신호는 「눈으로」.
   · gargo.js 를 고치지 않는다(판 밑에 따로 그림 · 기존 「그 다음」 한 줄은 사다리가 보일 때만 감춘다). */
(function () {
  var EL = null, MAXD = 3000, LAST = '';
  function $(id) { return document.getElementById(id); }
  function css() {
    if ($('gLadCss')) return; var c = document.createElement('style'); c.id = 'gLadCss';
    c.textContent = '#gLad{position:fixed;left:10px;right:10px;z-index:6;display:none;font-family:system-ui,sans-serif;pointer-events:none}'
      + '#gLad .rw{display:flex;gap:6px}#gLad .k{flex:1 1 0;min-width:0;background:var(--solid,#fff);border-radius:12px;box-shadow:0 4px 14px rgba(15,23,42,.18);padding:6px 8px 7px;border-top:4px solid #94a3b8;color:var(--ink,#0f172a)}'
      + '#gLad .k.g{border-top-color:#16a34a}#gLad .k.r{border-top-color:#dc2626}#gLad .k.y{border-top-color:#f59e0b}'
      + '#gLad .k .t{display:flex;align-items:baseline;gap:4px;white-space:nowrap}#gLad .k .n{font-size:11px;font-weight:900;color:var(--dim,#55627a)}#gLad .k .s{font-size:22px;font-weight:900;line-height:1.05;font-variant-numeric:tabular-nums}#gLad .k.g .s{color:#15803d}#gLad .k.r .s{color:#b91c1c}#gLad .k.y .s{color:#b45309}#gLad .k .s small{font-size:12px;font-weight:800;margin-left:1px}'
      + '#gLad .k .d{font-size:11.5px;font-weight:700;color:var(--dim,#55627a);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#gLad .k .v{margin-top:2px;font-size:13px;font-weight:900;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}'
      + '#gLad .k.x{border-top-color:#cbd5e1;opacity:.85}#gLad .k.x .s{color:var(--dim,#55627a);font-size:15px}'
      + '#gLad .co{margin-top:6px;background:rgba(15,23,42,.86);color:#fff;border-radius:10px;padding:6px 10px;font-size:13px;font-weight:800;line-height:1.35;box-shadow:0 4px 14px rgba(15,23,42,.18)}#gLad .co b{color:#86efac}#gLad .co b.r{color:#fca5a5}#gLad .co em{font-style:normal;font-weight:700;color:#cbd5e1}'
      + ':root.dark #gLad .k{background:#111827;color:#eef2f7}:root.dark #gLad .k.g .s{color:#4ade80}:root.dark #gLad .k.r .s{color:#f87171}:root.dark #gLad .k.y .s{color:#fbbf24}'
      + 'body.mode-e #gLad .k.r{background:#fef2f2}:root.dark body.mode-e #gLad .k.r{background:#3b0d0d}'
      + 'body.ladder #gSig.cp .ln.nx2,body.ladder.guiding #gSig.cp:not(.open) .ln.nx2,body.ladder #gSig .ln.nx2{display:none!important}'
      + '@media (min-width:760px){#gLad{left:12px;right:auto;width:380px}}';
    document.head.appendChild(c);
  }
  function km(d) { return d >= 1000 ? (d / 1000).toFixed(1) + 'km' : Math.round(d / 10) * 10 + 'm'; }
  function mode() { var b = document.body.classList; return b.contains('mode-e') && !b.contains('em-2') ? 'e' : b.contains('mode-v') ? 'v' : 'n'; }
  function night() { var h = new Date().getHours(); return h >= 22 || h < 6; }
  /* 앞 신호 셋 — 닿는 때를 이어 셈: 지금 속도(서 있으면 제한의 60% 어림)로 가다가, 앞 신호가 닿을 때 적색이면 그만큼 기다린 뒤 출발 */
  function plan(S) {
    var r = S.route, G = window.GARGO; if (!r || !r.sigs || !G || !G.sigAtT) return null;
    var pos = r.pos || 0, now = Date.now() / 1000, me = S.me, vNow = me && me.spd > 3 ? me.spd : 0, out = [], t = now, at = pos, est = !vNow;
    for (var i = 0; i < r.sigs.length && out.length < 3; i++) {
      var g = r.sigs[i]; if (g.d <= pos + 8) continue; if (g.d - pos > MAXD) break;
      if (g.mv === 'Rt' || g.mv === 'U') continue;   /* 우회전·유턴 = 신호 없음 — 칸을 쓰지 않는다 */
      var v = vNow || Math.max(5, (g.lim || 50) / 3.6 * 0.6); t += (g.d - at) / v; at = g.d;
      var s = g.unk ? null : G.sigAtT(g.no, t, g.side, g.mv), k = { g: g, dd: g.d - pos, eta: t - now, st: s && s.kind !== 'avg' ? s : null, stop: !out.length && g.d - pos < 40 && !(me && me.spd > 1) };
      if (k.st && !k.st.green) t += k.st.wait;   /* 닿을 때 적색이면 그만큼 서 있다가 다음으로 */
      out.push(k);
    }
    return { ks: out, est: est };
  }
  function verb(k, M, nt) {
    if (!k.st) return { c: 'x', v: '눈으로', s: '?' };
    var st = k.st, sec = Math.ceil(st.green ? st.remain : st.wait);
    if (M === 'e') return st.green ? { c: st.remain < 4 ? 'y' : 'g', v: st.remain < 4 ? '바뀔 무렵' : '통과', s: sec } : { c: 'r', v: '적색 진입 · 좌우', s: sec };
    if (M === 'v') return { c: st.green ? 'g' : 'r', v: st.green ? '녹색' : '적색', s: sec };
    if (st.green) return st.remain < 4 ? { c: 'y', v: '서두르지 않기', s: sec } : { c: 'g', v: nt ? '녹색' : '이대로', s: sec };
    return { c: 'r', v: nt ? '적색' : k.stop ? '정지 · 출발 대기' : k.dd < 500 ? '발 떼기' : '천천히', s: sec };
  }
  function coach(P, M, nt) {
    var ks = P.ks, r = ks.filter(function (k) { return k.st && !k.st.green; }), first = ks[0];
    if (!first) return '';
    var gn = ks.filter(function (k) { return k.st && k.st.green; }).length, un = ks.filter(function (k) { return !k.st; }).length;
    if (M === 'e') return r.length ? '앞 신호 ' + ks.length + '곳 중 <b class="r">적색 진입 ' + r.length + '곳</b> — 사이렌·경광등 · 교차로 앞에서 서행하며 좌우 확인' + (un ? ' <em>· 자료 없는 ' + un + '곳은 눈으로</em>' : '') : (gn ? '앞 ' + gn + '곳 <b>녹색에 닿음</b>' + (un ? ' · 자료 없음 ' + un + '곳' : '') : '앞 신호 자료 없음') + ' — 그래도 교차로마다 좌우 확인';
    if (M === 'v') return '';
    if (nt) return '밤 22~06시 — 속도 말 없이 색만 · <em>이어진 신호를 일부러 끊어 둔 시간</em>';
    if (!first.st) return '앞 신호 자료 없음 — <em>눈으로 확인</em>';
    if (first.stop && !first.st.green) return '정지 중 — 녹색까지 <b>' + Math.ceil(first.st.wait) + '초</b> <em>· 급출발 없이 천천히 출발하면 연료가 가장 덜 든다</em>';
    if (!first.st.green) return first.dd < 500 ? '앞 신호 <b class="r">적색</b>에 닿음 — <b>지금 발 떼고 굴러가기</b> <em>· 급제동 없이 연료·타이어·안전</em>' : '앞 신호 <b class="r">적색</b>에 닿을 예정 — <b>서두를 것 없음</b> <em>· 일정한 속도로</em>';
    for (var i = 1; i < ks.length; i++) if (ks[i].st && !ks[i].st.green) return '앞은 <b>녹색 통과</b>, ' + ['', '그다음', '셋째'][i] + '(' + (ks[i].dd >= 1000 ? (ks[i].dd / 1000).toFixed(1) + 'km' : Math.round(ks[i].dd / 10) * 10 + 'm') + ')' + ['', '은', '는'][i] + ' <b class="r">적색</b> — <b>속도를 올릴 필요 없음</b> <em>· 거기서는 미리 발 떼기</em>';
    if (first.st.remain < 4) return '앞 녹색이 곧 끝남 — <b>무리하게 지나지 않기</b>';
    return '<b>이대로</b> 가면 앞 ' + gn + '곳 녹색' + (un ? ' · 자료 없음 ' + un + '곳' : '') + ' <em>· 일정한 속도가 가장 경제적</em>';
  }
  function place() { var b = 70; ['gTop', 'gSig'].forEach(function (id) { var e = $(id); if (!e) return; var cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden' || !e.offsetHeight) return; b = Math.max(b, e.getBoundingClientRect().bottom); }); EL.style.top = Math.round(b + 6) + 'px'; }   /* 위 판 + 신호 판 아래 */
  function tick() {
    var S = window.GARGO && GARGO.state && GARGO.state(), on = !!(S && S.guide && S.route);
    if (!on) { if (EL.style.display !== 'none') { EL.style.display = 'none'; document.body.classList.remove('ladder'); } return; }
    var P = plan(S); if (!P || !P.ks.length) { EL.style.display = 'none'; document.body.classList.remove('ladder'); return; }
    var M = mode(), nt = night() && M === 'n', h = '<div class="rw">';
    P.ks.forEach(function (k, i) { var V = verb(k, M, nt), nm = String(k.g.nm || '').replace(/</g, '&lt;'); h += '<div class="k ' + V.c + '"><div class="t"><span class="n">' + ['바로 앞', '그다음', '셋째'][i] + '</span><span class="s">' + V.s + (V.s === '?' ? '' : '<small>초</small>') + '</span></div><div class="d">' + km(k.dd) + ' · ' + nm + '</div>' + (V.v ? '<div class="v">' + V.v + '</div>' : '') + '</div>'; });
    for (var j = P.ks.length; j < 3; j++) h += '<div class="k x" style="visibility:hidden"></div>';
    h += '</div>'; var co = coach(P, M, nt); if (co) h += '<div class="co">' + co + (P.est ? ' <em>(서 있어 속도는 어림)</em>' : '') + '</div>';
    if (h !== LAST) { EL.innerHTML = h; LAST = h; }
    EL.style.display = 'block'; document.body.classList.add('ladder'); place();
  }
  function start() { css(); EL = document.createElement('div'); EL.id = 'gLad'; EL.setAttribute('aria-live', 'polite'); document.body.appendChild(EL); setInterval(function () { try { tick(); } catch (e) {} }, 1000); window.addEventListener('resize', function () { if (EL.style.display === 'block') place(); }); }
  window.gargoLadder = { plan: plan, verb: verb, coach: coach };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
