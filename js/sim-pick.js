/* 🧪 시뮬 — 아무 신호 교차로나 골라 그 둘레 구역을 이 자리에서 엮기(2026-11-02 · 소유자 「지정체 교차로 지역을 선정해 통행량 시뮬 · 구역 선정 및 신호값 통행량을 알아보며」)
   tools/sim/area-bake.py 를 그대로 옮겼다(같은 자료 · 같은 차례 · 같은 설계값) — 다른 점: 도로망은 여섯 구 판(data/nav-six.json · 공개 파일)만 · 엮는 곳이 PC 가 아니라 이 기기.
   고른 자리 = 지도에서 마지막으로 누른 곳(TGMap2D.tapm) · 그 둘레 150m 에 신호 교차로가 있으면 카드에 단추.
   열기 전 「이 구역 신호값·통행량·평소 속도」를 먼저 보이고, 평소 속도로 수요를 맞춘 뒤(tgSim.calibrate) 「🧪 시뮬 — 서울 여러 구역」 판(js/sim-area.js · openDoc)으로 연다.
   개념 시연 — 예측·보증이 아니다. 미리 구운 구역(sim-areas.json)은 그대로 그쪽 단추가 맡는다. */
(function () {
  'use strict';
  var SDA = { nt: 0, ne: 45, et: 90, se: 135, st: 180, sw: 225, wt: 270, nw: 315 }, LEG4 = ['nt', 'et', 'st', 'wt'], LEGK = { nt: '북', et: '동', st: '남', wt: '서' };
  var MAXOUT = 600, MAXCHAIN = 1500, R0 = 500;
  var NAMEFIX = { '4031': '반포사거리' };   /* 형님이 정한 화면 이름(규칙 장부 FK-NAME-4031 · T-GIS·도로망 이름은 강남터미널고가밑) */
  var MVNO = { 1: ['et', 'Lt'], 2: ['wt', 'St'], 3: ['st', 'Lt'], 4: ['nt', 'St'], 5: ['wt', 'Lt'], 6: ['et', 'St'], 7: ['nt', 'Lt'], 8: ['st', 'St'] };
  var NAV = null, KSC = null, SDX = null, VOL = null, OI = null, SPI = null, CELLS = {}, SPDG = {}, PANEL = null, CUR = null;
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function getJ(u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u + ' ' + r.status); return r.json(); }); }
  function bearing(a, b) { var d = Math.atan2((b[0] - a[0]) * Math.cos(37.5 * Math.PI / 180), b[1] - a[1]) * 180 / Math.PI; return ((d % 360) + 360) % 360; }
  function dist(a, b) { return Math.hypot((a[0] - b[0]) * 88200, (a[1] - b[1]) * 111000); }
  function adiff(a, b) { return Math.abs((((a - b + 180) % 360) + 360) % 360 - 180); }
  function minBy(arr, f) { var b = null, bv = Infinity; arr.forEach(function (x) { var v = f(x); if (v < bv) { bv = v; b = x; } }); return b; }   /* 같은 값이면 앞의 것(파이썬 min 과 같음) */
  function sigCell(lat, lon) { var c = SDX.cell; return Math.floor(lat / c[0]) + '_' + Math.floor(lon / c[1]); }

  /* ---- 자료 받기(처음 한 번 · 도로망 약 5MB) ---- */
  function base(prog) {
    if (NAV) return Promise.resolve();
    prog && prog('자료 받는 중 — 여섯 구 도로망(약 5MB)·신호값·교통량 조사…');
    return Promise.all([getJ('data/nav-six.json'), getJ('data/sig-ksc-seocho.json'), getJ('data/sigdir/index.json'), getJ('data/traffic-vol-seoul.json'), getJ('data/onto-int.json'), getJ('data/spd-normal-six/index.json')])
      .then(function (a) {
        var n = a[0], L = [], IN = {}, OUT = {};
        n.links.forEach(function (r) { var l = { id: r[0], f: r[1], t: r[2], len: r[3], lim: r[4], gr: r[5], lanes: r[6] || 1, nm: r[7] || '', ramp: r[8], ty: r.length > 12 ? r[12] : '000' }; L.push(l); });
        L.forEach(function (l) { if (n.nodes[l.f] && n.nodes[l.t]) { (OUT[l.f] = OUT[l.f] || []).push(l); (IN[l.t] = IN[l.t] || []).push(l); } });
        NAV = { N: n.nodes, IN: IN, OUT: OUT, made: n.made };
        KSC = {}; a[1].items.forEach(function (i) { KSC[i.no] = i; });
        SDX = a[2]; VOL = a[3].spots;
        OI = {}; a[4].items.forEach(function (r) { if (r[4]) OI[String(r[4])] = 'INT-' + r[0]; });
        SPI = a[5];
      });
  }
  function cellsFor(nos) {   /* T-Data 기록 — 그 교차로가 든 칸 파일만 */
    var need = {}; nos.forEach(function (no) { var p = SDX.pts[no]; if (p) need[sigCell(p[0], p[1])] = 1; });
    return Promise.all(Object.keys(need).filter(function (k) { return !CELLS[k] && SDX.cells[k]; }).map(function (k) { return getJ('data/sigdir/c/' + k + '.json').then(function (j) { CELLS[k] = j.its || {}; }).catch(function () { CELLS[k] = {}; }); }));
  }
  function spdFor(lat, lon) {   /* 평소 속도 — 구역 둘레 약 2km 와 겹치는 구 파일만 */
    var m = 0.025, gs = Object.keys(SPI.gu).filter(function (g) { var b = SPI.gu[g].bbox; return !(b[2] < lon - m || b[0] > lon + m || b[3] < lat - m || b[1] > lat + m); });
    return Promise.all(gs.filter(function (g) { return !SPDG[g]; }).map(function (g) { return getJ('data/' + SPI.gu[g].file).then(function (j) { SPDG[g] = j.links || {}; }).catch(function () { SPDG[g] = {}; }); }));
  }
  function nspOf(lid) {
    var v = null; Object.keys(SPDG).some(function (g) { if (SPDG[g][lid]) { v = SPDG[g][lid]; return true; } return false; }); if (!v) return null;
    var o = {}; Object.keys(v).forEach(function (k) { var h = +k.split('-')[1]; if (h >= 7 && h <= 23) o[k] = v[k][0]; }); return o;
  }

  /* ---- 엮기 — tools/sim/area-bake.py main() 과 같은 차례 ---- */
  function bake(nm, lat, lon, R) {
    R = R || R0; var C = [lon, lat], N = NAV.N, IN = NAV.IN, OUT = NAV.OUT;
    var grp = {}, log = [], sig = {}, owner = {};
    Object.keys(N).forEach(function (nid) { var n = N[nid], s = n.length > 7 && n[7] && typeof n[7] === 'object' ? n[7] : null; if (s && s.no && dist([n[0], n[1]], C) <= R) (grp[s.no] = grp[s.no] || []).push(nid); });
    var sd = {}; Object.keys(CELLS).forEach(function (k) { Object.keys(CELLS[k]).forEach(function (no) { sd[no] = CELLS[k][no]; }); });
    Object.keys(grp).forEach(function (no) {
      var ns = grp[no], has = !!KSC[no] || (sd[no] || []).some(function (r) { return r.mv && r.mv.length; });
      if (!has) { log.push('신호값 없음 — 지나가는 교차로로 ' + no); return; }
      var cx = 0, cy = 0; ns.forEach(function (x) { cx += N[x][0]; cy += N[x][1]; }); cx /= ns.length; cy /= ns.length;
      var s0 = N[ns[0]][7], nmv = s0 && typeof s0 === 'object' ? (s0.sd || s0.ksc || [no, N[ns[0]][3]])[1] : N[ns[0]][3];
      sig[no] = { ns: ns, set: ns.reduce(function (o, x) { o[x] = 1; return o; }, {}), c: [cx, cy], nm: NAMEFIX[no] || nmv };
      ns.forEach(function (x) { owner[x] = no; });
    });
    function chain(start, up) {
      var cur = start, tot = 0, seen = {}, links = [];
      for (;;) {
        links.push(cur); tot += cur.len; seen[cur.id] = 1;
        var nx = up ? cur.f : cur.t;
        if (owner[nx]) return [links, tot, owner[nx]];
        if (tot > MAXCHAIN || dist([N[nx][0], N[nx][1]], C) > R + 400) return [links, tot, null];
        var back = up ? cur.t : cur.f;
        var cand = ((up ? IN[nx] : OUT[nx]) || []).filter(function (l) { return !seen[l.id] && l.ty !== '001' && l.ty !== '002' && !l.ramp && (up ? l.f : l.t) !== back; });
        if (!cand.length) return [links, tot, null];
        var same = cand.filter(function (l) { return l.nm && l.nm === cur.nm; }), pool = (same.length ? same : cand).slice();
        var b0 = bearing(N[cur.f].slice(0, 2), N[cur.t].slice(0, 2));
        pool.sort(function (p, q) { return adiff(bearing(N[p.f].slice(0, 2), N[p.t].slice(0, 2)), b0) - adiff(bearing(N[q.f].slice(0, 2), N[q.t].slice(0, 2)), b0); });
        cur = pool[0];
      }
    }
    var nodes = {}, links = {}, entry = {}, used = {}, legs = {};
    Object.keys(sig).forEach(function (no) { legs[no] = {}; });
    Object.keys(sig).forEach(function (no) {
      var g = sig[no], apps = [], outs = [];
      g.ns.forEach(function (x) { (IN[x] || []).forEach(function (l) { if (g.set[l.f] || l.ty === '001' || l.ty === '002' || l.ramp) return; var c = chain(l, true), lk = c[0], far = lk[Math.min(lk.length - 1, 1)].f; apps.push({ l: l, len: c[1], fr: c[2], brg: bearing(g.c, N[far].slice(0, 2)), lanes: l.lanes, nm: l.nm }); }); });
      g.ns.forEach(function (x) { (OUT[x] || []).forEach(function (l) { if (g.set[l.t] || l.ty === '001' || l.ty === '002' || l.ramp) return; var c = chain(l, false), lk = c[0], far = lk[Math.min(lk.length - 1, 1)].t; outs.push({ l: l, len: c[1], to: c[2], brg: bearing(g.c, N[far].slice(0, 2)), lanes: l.lanes, nm: l.nm, lk: lk }); }); });
      [['in', apps], ['out', outs]].forEach(function (pair) {
        var by = {}; pair[1].forEach(function (a) { var lg = minBy(LEG4, function (k) { return adiff(SDA[k], a.brg); });
          if (by[lg]) { var keep = a.lanes > by[lg].lanes ? a : by[lg], drop = keep === a ? by[lg] : a; log.push(no + ' ' + lg + ' 다리 겹침 — ' + drop.nm + '(' + drop.lanes + '차로) 버림'); by[lg] = keep; } else by[lg] = a; });
        Object.keys(by).forEach(function (lg) { (legs[no][lg] = legs[no][lg] || {})[pair[0]] = by[lg]; });
      });
    });
    Object.keys(sig).forEach(function (no) {
      Object.keys(legs[no]).forEach(function (lg) {
        var d = legs[no][lg], a = d['in'], done = false;
        if (a) {
          if (a.fr && sig[a.fr] && a.fr !== no) {
            var up = Object.keys(legs[a.fr]).filter(function (k) { var v = legs[a.fr][k]; return v.out && v.out.to === no; });
            if (up.length) { var lid0 = a.fr + '>' + no; links[lid0] = { id: lid0, fr: a.fr, to: no, len: Math.round(a.len), lanes: a.lanes, nm: a.nm + '(' + a.fr + '→' + no + ')', src: '노드링크', ofr: up[0], oto: lg, its: a.l.id, nsp: nspOf(a.l.id) }; done = true; }
          }
          if (!done) {
            var lid = 'in.' + no + '.' + lg;
            links[lid] = { id: lid, fr: null, to: no, len: Math.round(Math.min(a.len, MAXOUT)), lanes: a.lanes, nm: (a.nm || '이름 없는 길') + ' — 들어옴', src: '노드링크 · 길이 ' + MAXOUT + 'm 넘으면 ' + MAXOUT + '(설계값)', oto: lg, src_in: 1, its: a.l.id, nsp: nspOf(a.l.id) };
            var sp = null; VOL.some(function (s) { if (a.nm && a.nm === s.name.split('(')[0].trim() && dist([s.lon, s.lat], sig[no].c) < 1200) { sp = s; return true; } return false; });   /* 조사 지점의 길 이름(괄호 앞)과 같은 길만 — 앞 세 글자로 맞추면 반포대로27길(1차로)이 반포대로 교통량을 받았다(2026-11-02) */
            entry[lid] = sp ? { spot: sp.id, share: 1.0, src: '조사 ' + sp.id + ' ' + sp.name + ' 두 방향 평균(같은 길 1.2km 안)' } : { perLane: 300, src: '설계값 — 조사 지점 없음 · 차로 × 차로당 300대/시' };
            if (sp) used[sp.id] = sp;
          }
        }
        var o = d.out;
        if (done) return;   /* area-bake.py 와 같이 — 들어오는 쪽이 안쪽 길이면 그 다리의 나가는 길은 만들지 않는다(파이썬 continue · 사슬이 이웃 교차로 노드를 비켜 가는 곳에서 가짜 출구가 생기지 않게) */
        if (o && !(o.to && sig[o.to] && o.to !== no)) {
          var lo = 'out.' + no + '.' + lg; links[lo] = { id: lo, fr: no, to: null, len: 0, lanes: o.lanes, nm: (o.nm || '이름 없는 길') + ' — 나감', src: '노드링크', ofr: lg, sink: 1 };
          var on = {}; o.lk.forEach(function (l2) { var v2 = nspOf(l2.id) || {}; Object.keys(v2).forEach(function (k2) { if (on[k2] == null || v2[k2] < on[k2]) on[k2] = v2[k2]; }); });
          if (Object.keys(on).length) { links[lo].onsp = on; links[lo].oits = o.lk.map(function (l2) { return l2.id; }); }
        }
      });
    });
    Object.keys(sig).forEach(function (no) { nodes[no] = { id: no, nm: sig[no].nm, ty: 'sig', ll: [sig[no].c[1], sig[no].c[0]], legs: {} }; });
    Object.keys(links).forEach(function (k) { var l = links[k]; if (l.oto) (nodes[l.to].legs[l.oto] = nodes[l.to].legs[l.oto] || {})['in'] = l.id; if (l.ofr && l.fr) (nodes[l.fr].legs[l.ofr] = nodes[l.fr].legs[l.ofr] || {}).out = l.id; });
    Object.keys(sig).forEach(function (no) {
      if (KSC[no]) { var k = KSC[no], dir = {}; Object.keys(k.dir).forEach(function (p) { dir[p] = k.dir[p].filter(function (r) { return r[3] != null; }).map(function (r) { return [r[0] + '.' + r[1], r[3], r[4], r[6]]; }); });
        nodes[no].plan = { src: '현시도', day: k.day, tod: k.tod, pat: k.pat, Y: k.Y, AR: k.AR, ph: k.ph.map(function (p) { return p.mv.filter(function (m) { return MVNO[m]; }).map(function (m) { return MVNO[m][0] + '.' + MVNO[m][1]; }); }), dir: dir }; return; }
      var legb = {}; Object.keys(legs[no]).forEach(function (lg) { if (legs[no][lg]['in']) legb[lg] = legs[no][lg]['in'].brg; });
      var lgs = Object.keys(legb);
      function legOf(dc) { if (SDA[dc] == null || !lgs.length) return null; var lg = minBy(lgs, function (k) { return adiff(legb[k], SDA[dc]); }); return adiff(legb[lg], SDA[dc]) <= 60 ? lg : null; }
      var recs = [];
      (sd[no] || []).forEach(function (r) {
        if (!r.mv || !r.mv.length || !r.cyc) return; var w = [];
        r.mv.forEach(function (m) { if ((m[1] !== 'St' && m[1] !== 'Lt') || m[2] == null || m[5] == null) return; var lg = legOf(m[0]); if (lg) w.push([lg + '.' + m[1], Math.round(m[2] * 10) / 10, m[3] || 3, Math.round(m[5] * 10) / 10]); });
        if (!w.length) return; var hm = (r.from || '12:00').split(':');
        recs.push({ day: r.day, dk: [r.dow], t: (+hm[0]) * 3600 + (+hm[1]) * 60, cyc: r.cyc, win: w.sort(function (p, q) { return p[3] - q[3]; }), src: r.src });
      });
      nodes[no].plan = { src: 'T-Data', recs: recs };
      if (!recs.length) { log.push('T-Data 기록을 다리에 못 붙임 — 신호 없이 지나감 ' + no); nodes[no].plan = { src: '없음(지나감)', win: [], cyc: 100 }; nodes[no].free = []; Object.keys(legs[no]).forEach(function (lg) { nodes[no].free.push(lg + '.St', lg + '.Lt'); }); }
    });
    Object.keys(nodes).forEach(function (k) { if (OI[String(k)]) nodes[k].int = OI[String(k)]; });
    var vol = {}; Object.keys(used).forEach(function (k) { var v = used[k]; vol[k] = { name: v.name, lat: v.lat, lon: v.lon, wd: v.wd, sa: v.sa, su: v.su, lanes: v.lanes }; });
    var now = new Date(), pad = function (x) { return ('0' + x).slice(-2); };
    return { schema: 'tg-sim/2', area: nm, nm: nm, made: now.getFullYear() + '-' + pad(now.getMonth() + 1) + '-' + pad(now.getDate()) + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()), auto: 1, pick: 1, center: [lat, lon], r: R,
      about: '이 기기에서 바로 엮은 구역(js/sim-pick.js · tools/sim/area-bake.py 와 같은 방법 · 도로망은 여섯 구 판 nav-six) — 개념 시연 · 신호 없는 교차로는 지나감 · 다리는 넷으로 줄임 · 회전 금지 미반영 · 고가·지하차도 차는 빠짐',
      nodes: nodes, links: links, vol: vol, entry: entry,
      design: { turn: { Lt: 0.15, Rt: 0.15, src: '설계값 — 회전 비율 조사 없음(좌·우 각 15% · 나머지 직진)' }, rtRed: { v: 0.5, src: '설계값 — 우회전은 적색에도 이 몫만큼 빠진다' }, lostStart: { v: 2, src: '설계값 — 녹색 처음 2초는 출발 손실' }, freeV: { v: 30, src: '설계값 — 막히지 않을 때 주행 속도(km/h)' }, box: { v: 0.3, src: '설계값 — 하류가 찼는데도 교차로 안으로 들어가는(꼬리물기) 차 비율' } },
      mvx: [], att: [], actions: [], preset: {},
      sat: { v: 2200, unit: '대/녹색 1시간/차로', src: '2차 자료', quote: '신호교차로 기본 조건에서 포화교통류율 2,200pcphgpl — 도로용량편람(2013) p.427' },
      spacing: { v: 7.5, unit: 'm/대', src: '설계값' }, log: log };
  }
  /* 자리 → 구역 자료(받기 + 엮기) */
  function build(lat, lon, R, nm, prog) {
    return base(prog).then(function () {
      var near = []; Object.keys(SDX.pts).forEach(function (no) { var p = SDX.pts[no]; if (dist([p[1], p[0]], [lon, lat]) <= (R || R0) + 200) near.push(no); });
      Object.keys(KSC).forEach(function (no) { var k = KSC[no]; if (k.lat && dist([k.lon, k.lat], [lon, lat]) <= (R || R0) + 200 && near.indexOf(no) < 0) near.push(no); });
      prog && prog('신호 기록·평소 속도 받는 중…');
      return Promise.all([cellsFor(near), spdFor(lat, lon)]);
    }).then(function () { return bake(nm || '고른 자리', lat, lon, R); });
  }

  /* ---- 이 자리에 신호 교차로가 있나(카드 단추용 · 색인만 봄) ---- */
  var IDXP = null;
  function idxGet() {   /* 신호 자리 = T-Data 색인 pts + 교통과 현시도(서초 · 현시도만 있는 교차로도 있다) */
    if (IDXP) return IDXP;
    IDXP = Promise.all([getJ('data/sigdir/index.json'), getJ('data/sig-ksc-seocho.json').catch(function () { return { items: [] }; })]).then(function (a) { var j = a[0]; if (!SDX) SDX = j; var pts = {}; Object.keys(j.pts).forEach(function (k) { pts[k] = j.pts[k]; }); a[1].items.forEach(function (i) { if (i.lat && !pts[i.no]) pts[i.no] = [i.lat, i.lon, NAMEFIX[i.no] || i.nm]; }); return { pts: pts }; }).catch(function () { IDXP = null; return null; });
    return IDXP;
  }
  function tapLL() {
    var T = window.TGMap2D; if (!T || !T.tapm || !T.P) return null; var m = T.tapm(); if (!m) return null;
    var a = T.P(127, 37.5), b = T.P(127.01, 37.5), c = T.P(127, 37.51);   /* 지도 투영은 1차식 — 세 점으로 되돌린다 */
    return [37.5 + (m[1] - a[1]) / (c[1] - a[1]) * 0.01, 127 + (m[0] - a[0]) / (b[0] - a[0]) * 0.01];
  }
  function sixIn(lat, lon) { if (!SPI) return true; return Object.keys(SPI.gu).some(function (g) { var b = SPI.gu[g].bbox; return lon >= b[0] && lon <= b[2] && lat >= b[1] && lat <= b[3]; }); }
  function nearSig(ll, j) { var best = null, bd = 150; Object.keys(j.pts).forEach(function (no) { var p = j.pts[no]; if (/\(연등\)/.test(p[2] || '')) return; var d = dist([p[1], p[0]], [ll[1], ll[0]]); if (d < bd) { bd = d; best = { no: no, nm: NAMEFIX[no] || p[2], lat: p[0], lon: p[1], d: d }; } }); return best; }
  function cardHook() {
    var c = $('m2dCard'); if (!c || !window.MutationObserver) return;
    if (!SPI) getJ('data/spd-normal-six/index.json').then(function (j) { SPI = SPI || j; }).catch(function () {});
    new MutationObserver(function () {
      if (!c.classList.contains('on') || c.querySelector('[data-simpick]')) return;
      var ll = tapLL(); if (!ll) return;
      idxGet().then(function (j) {
        if (!j || !c.classList.contains('on') || c.querySelector('[data-simpick]')) return;
        var s = nearSig(ll, j); if (!s || !sixIn(s.lat, s.lon)) return;
        var bx = c.querySelector('.lg-btns') || c.querySelector('.dhb') || c, b = document.createElement('button'); b.setAttribute('data-simpick', s.no);
        b.title = '이 교차로 둘레 500m 의 신호 교차로·길·신호값·교통량을 이 자리에서 엮어 시뮬한다 · 개념 시연';
        b.textContent = '🧪 이 교차로 둘레 시뮬 — ' + s.nm; b.style.cssText = 'background:#5b21b6;color:#fff;border-color:#5b21b6';
        b.onclick = function (e) { e.stopPropagation(); open(s.lat, s.lon, s.nm); };
        if (bx === c) c.appendChild(b); else bx.appendChild(b);
      });
    }).observe(c, { childList: true, subtree: true, attributes: true, attributeFilter: ['class'] });
  }

  /* ---- 화면 — 엮은 구역 한눈에 → 맞추고 열기 ---- */
  function css() {
    if ($('m2dSimPCss')) return; var s = document.createElement('style'); s.id = 'm2dSimPCss';
    s.textContent = '#m2dSimP{position:fixed;left:8px;right:8px;top:8px;bottom:8px;max-width:560px;margin:0 auto;z-index:2600;background:#fff;color:#111;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.35);padding:10px 12px;overflow:auto;display:none;font-size:13px;line-height:1.45}' +
      '#m2dSimP.on{display:block}#m2dSimP h3{margin:0 0 6px;font-size:15px;display:flex;justify-content:space-between;align-items:center;gap:8px}#m2dSimP h4{margin:10px 0 4px;font-size:13.5px}' +
      '#m2dSimP table{border-collapse:collapse;width:100%;font-size:12px}#m2dSimP td,#m2dSimP th{border-bottom:1px solid #e5e7eb;padding:3px 4px;text-align:left;vertical-align:top}' +
      '#m2dSimP .sn{color:#555;font-size:12px}#m2dSimP .warn{background:#fff7ed;border:1px solid #fdba74;border-radius:8px;padding:6px 8px;margin:6px 0;font-size:12px}' +
      '#m2dSimP button{min-height:36px;border-radius:8px;border:1px solid #c4b5fd;background:#f5f3ff;padding:4px 10px;font-weight:700;cursor:pointer}#m2dSimP button.go{background:#5b21b6;color:#fff;border-color:#5b21b6}' +
      '#m2dSimP .b{display:inline-block;padding:0 6px;border-radius:6px;font-size:11px;font-weight:700}#m2dSimP .b.k{background:#dcfce7;color:#166534}#m2dSimP .b.t{background:#dbeafe;color:#1e40af}#m2dSimP .b.x{background:#f3f4f6;color:#6b7280}#m2dSimP .b.d{background:#fef3c7;color:#92400e}' +
      '@media (prefers-color-scheme:dark){#m2dSimP{background:#111827;color:#e5e7eb}#m2dSimP td,#m2dSimP th{border-color:#374151}#m2dSimP .sn{color:#9ca3af}#m2dSimP button{background:#1f2937;color:#e5e7eb;border-color:#4c1d95}#m2dSimP .warn{background:#3b2a12;border-color:#92400e}}';
    document.head.appendChild(s);
  }
  function panel() { css(); if (!PANEL) { PANEL = document.createElement('div'); PANEL.id = 'm2dSimP'; document.body.appendChild(PANEL); PANEL.addEventListener('click', onClick); PANEL.addEventListener('change', function (e) { if (e.target.getAttribute('data-sp') === 'h') { LIST.h = +e.target.value; relist(); } }); } PANEL.classList.add('on'); return PANEL; }
  function close() { if (PANEL) PANEL.classList.remove('on'); }
  function head(t) { return '<h3>🧪 ' + esc(t) + '<button data-sp="x" aria-label="닫기">✕ 닫기</button></h3>'; }
  function hourNow() { return new Date().getHours(); }
  function volNow(s) { var d = new Date().getDay(), arr = d === 0 ? s.su : d === 6 ? s.sa : s.wd, r = arr && arr[hourNow()]; return r ? r[0] + r[1] : null; }
  function summary(doc) {
    var ks = Object.keys(doc.nodes), h = head(doc.nm + ' 둘레 ' + Math.round(doc.r) + 'm — 이 자리에서 엮은 구역');
    h += '<div class="sn">신호 교차로 ' + ks.length + '곳 · 길 ' + Object.keys(doc.links).length + ' · 들어오는 길 ' + Object.keys(doc.entry).length + ' · <b>개념 시연 — 예측·보증이 아니다</b></div>';
    if (!ks.length) return h + '<div class="warn">이 둘레 ' + Math.round(doc.r) + 'm 에 신호값(교통과 현시도·T-Data 기록)이 있는 교차로가 없다 — 엮을 것이 없다. 신호 기록이 쌓이면 다시.</div>';
    h += '<h4>🚦 신호값</h4><table><tr><th>교차로</th><th>신호값 출처</th><th>주기</th></tr>' + ks.map(function (k) { var n = doc.nodes[k], p = n.plan || {}, b, cy = '—';
      if (p.src === '현시도') { b = '<span class="b k">교통과 현시도</span>'; cy = '시간대별(패턴 ' + (p.pat ? Object.keys(p.pat).length : 0) + ')'; }
      else if (p.src === 'T-Data') { b = '<span class="b t">T-Data 실측 ' + p.recs.length + '기록</span>'; var cs = p.recs.map(function (r) { return r.cyc; }); cy = cs.length ? Math.min.apply(null, cs) + (Math.max.apply(null, cs) !== Math.min.apply(null, cs) ? '~' + Math.max.apply(null, cs) : '') + '초' : '—'; }
      else b = '<span class="b x">신호 없이 지나감</span>';
      return '<tr><td>' + esc(n.nm) + ' <small>' + esc(k) + '</small></td><td>' + b + '</td><td>' + esc(cy) + '</td></tr>'; }).join('') + '</table>';
    var es = Object.keys(doc.entry);
    h += '<h4>🚗 들어오는 길 — 통행량</h4><table><tr><th>길</th><th>차로</th><th>지금 시각 조사값(양방향 대/시)</th><th>평소 속도</th></tr>' + es.map(function (e) { var l = doc.links[e], E = doc.entry[e], s = E.spot && doc.vol[E.spot], v = s ? volNow(s) : null;
      var ns = l.nsp ? Object.keys(l.nsp).length : 0;
      return '<tr><td>' + esc(l.nm.replace(/ — 들어옴$/, '')) + ' <small>(' + (LEGK[l.oto] || l.oto) + '쪽)</small></td><td>' + l.lanes + '</td><td>' + (s ? '<span class="b k">조사 ' + esc(E.spot) + '</span> ' + (v != null ? v.toLocaleString() : '—') : '<span class="b d">설계값</span> 차로당 300') + '</td><td>' + (ns ? '<span class="b t">ITS ' + ns + '칸</span>' : '<span class="b x">없음</span>') + '</td></tr>'; }).join('') + '</table>';
    var withN = es.filter(function (e) { return doc.links[e].nsp; }).length;
    h += '<div class="warn">수요는 교통량 조사(같은 길 이름 1.2km 안) · 없으면 설계값이다. 다음 단계에서 <b>평소 속도(ITS 가운데값 · 평일 16~21시)</b>로 들어오는 길마다 배율을 맞춘다' + (withN ? '(평소 속도가 붙은 길 ' + withN + '/' + es.length + ')' : ' — 이 구역은 평소 속도가 붙은 길이 없어 맞추지 못한다') + '.</div>';
    if (doc.log.length) h += '<details><summary>엮으며 남긴 것(' + doc.log.length + ')</summary><ul style="margin:4px 0;padding-left:18px;font-size:11.5px">' + doc.log.slice(0, 20).map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></details>';
    h += '<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px"><button class="go" data-sp="cal">▶ 평소 속도로 맞추고 시뮬 열기</button><button data-sp="raw">맞추지 않고 바로 열기</button></div>';
    return h + '<div class="sn" style="margin-top:6px">출처: 국가표준 노드링크(여섯 구 판) · 교통과 현시도 · 서울시 T-Data 방향별 신호 · 서울시 교통량 조사 · ITS 평소 속도 · 도로용량편람(2013) 포화교통류율 · 나머지 설계값(회전 15% 등)</div>';
  }
  function onClick(e) {
    var t = e.target.closest('[data-sp]'); if (!t) return; var k = t.getAttribute('data-sp');
    if (k === 'x') return close();
    if (k.indexOf('dg:') === 0) { LIST.dg = +k.slice(3); return relist(); }
    if (k.indexOf('pk:') === 0) { var r = LIST.rows[+k.slice(3)]; if (r) open(r.lat, r.lon, r.nm); return; }
    if ((k === 'cal' || k === 'raw') && CUR) { var doc = CUR; t.disabled = true; t.textContent = k === 'cal' ? '맞추는 중…(몇 초)' : '여는 중…';
      setTimeout(function () { simReady(function () {
        var ar = { id: 'pick:' + doc.center.join(','), nm: doc.nm + ' 둘레(고른 자리)', c: doc.center, r: doc.r, sig: [], hit: 0, n: 0, mh: 0, mn: 0, jh: 0, jn: 0, calDay: '' };
        if (k === 'cal' && Object.keys(doc.entry).length) { try { var cl = window.tgSim.calibrate(doc, { iter: 8 }); doc.cal = cl; ar.hit = cl.best.hit; ar.n = cl.best.n; ar.mh = cl.best.mh; ar.mn = cl.best.mn; ar.jh = cl.best.jh; ar.jn = cl.best.jn; ar.calDay = cl.date; } catch (er) { doc.log.push('맞춤 실패 — ' + er.message); } }
        close(); if (window.tgSimArea && window.tgSimArea.openDoc) window.tgSimArea.openDoc(doc, ar); else alert('시뮬 판(sim-area.js)을 찾지 못했다');
      }); }, 30); }
  }
  function simReady(cb) { if (window.tgSim) return cb(); var s = document.createElement('script'); s.src = 'js/sim.js?v=24'; s.onload = cb; s.onerror = function () { alert('시뮬 계산기(sim.js)를 받지 못했다'); }; document.head.appendChild(s); }
  var SEQ = 0;
  function open(lat, lon, nm, R) {
    var my = ++SEQ, P = panel(); P.innerHTML = head((nm || '고른 자리') + ' 둘레 — 엮는 중') + '<div class="sn" id="m2dSimPProg">준비…</div>';
    build(lat, lon, R || R0, nm, function (m) { var e = $('m2dSimPProg'); if (e) e.textContent = m; })
      .then(function (doc) { if (my !== SEQ) return; CUR = doc; P.innerHTML = summary(doc); })   /* 두 자리를 잇달아 누르면 나중 것만 그린다 */
      .catch(function (er) { if (my !== SEQ) return; P.innerHTML = head('엮지 못했다') + '<div class="warn">' + esc(er && er.message || er) + ' — 통신을 확인하고 다시</div>'; });
  }
  /* ---- 🚦 막히는 교차로 고르기 — 지금 지도 가운데 둘레 2km 의 신호 교차로를 「들어오는 길 가운데 가장 느린 곳」의 평소 속도(ITS 가운데값 · 요일 갈래 · 시)로 줄 세운다 ·
     지금 실측(live-spd-six · 20분 안 값만)이 있으면 나란히 · 고르면 그 교차로 둘레를 엮는다 ---- */
  var LIST = { h: null, dg: null, rows: null, c: null }, DGK = ['월~목', '금', '토', '일·공휴일'];
  function viewLL() { var T = window.TGMap2D; if (!T || !T.view || !T.P) return null; var a = T.P(127, 37.5), b = T.P(127.01, 37.5), c = T.P(127, 37.51); return [37.5 + (T.view.cy - a[1]) / (c[1] - a[1]) * 0.01, 127 + (T.view.cx - a[0]) / (b[0] - a[0]) * 0.01]; }
  function dgOf(d) { var w = d.getDay(); return w === 0 ? 3 : w === 6 ? 2 : w === 5 ? 1 : 0; }
  function rank(lat, lon, live) {
    var N = NAV.N, IN = NAV.IN, grp = {}, out = [];
    Object.keys(N).forEach(function (nid) { var n = N[nid], s = n.length > 7 && n[7] && typeof n[7] === 'object' ? n[7] : null; if (s && s.no && dist([n[0], n[1]], [lon, lat]) <= 2000) (grp[s.no] = grp[s.no] || []).push(nid); });
    var key = LIST.dg + '-' + LIST.h, nw = new Date(), nk = dgOf(nw) + '-' + nw.getHours();   /* 지금 실측은 「지금 시각」의 평소와 견준다(고른 시각이 아니라) */
    Object.keys(grp).forEach(function (no) {
      if (!KSC[no] && !SDX.pts[no]) return;   /* 신호값이 있을 만한 곳만(현시도 · T-Data 자리) — 엮을 때 다시 가린다 */
      var ns = grp[no], set = {}; ns.forEach(function (x) { set[x] = 1; });
      var worst = null, lv = null;
      ns.forEach(function (x) { (IN[x] || []).forEach(function (l) { if (set[l.f] || l.ramp || l.ty === '001' || l.ty === '002') return;
        var v = nspOf(l.id), m = v && v[key]; if (m != null && (!worst || m < worst.v)) worst = { v: m, nm: l.nm, lim: l.lim };
        if (live && live[l.id] != null && v && v[nk] && (!lv || live[l.id] / v[nk] < lv.r)) lv = { v: live[l.id], r: live[l.id] / v[nk], nm: l.nm }; }); });
      if (!worst) return;
      var cx = 0, cy = 0; ns.forEach(function (x) { cx += N[x][0]; cy += N[x][1]; });
      var s0 = N[ns[0]][7], nm = NAMEFIX[no] || (s0.sd || s0.ksc || [no, N[ns[0]][3]])[1];
      if (/\(연등\)/.test(nm || '')) return;
      out.push({ no: no, nm: nm, lat: cy / ns.length, lon: cx / ns.length, v: worst.v, rd: worst.nm, lim: worst.lim, lv: lv, src: KSC[no] ? '현시도' : 'T-Data', d: dist([cx / ns.length, cy / ns.length], [lon, lat]) });
    });
    return out.sort(function (a, b) { return a.v - b.v || a.d - b.d; });
  }
  function listPaint() {
    var P = panel(), R = LIST.rows || [], live = LIST.live;
    var hs = []; for (var h = 7; h <= 23; h++) hs.push('<option value="' + h + '"' + (h === LIST.h ? ' selected' : '') + '>' + h + '시</option>');
    var h0 = head('막히는 교차로 고르기 — 지도 가운데 둘레 2km') +
      '<div class="sn">들어오는 길 가운데 가장 느린 곳의 <b>평소 속도</b>(ITS 가운데값 · 국가교통정보센터 · ' + esc(SPI && SPI.from || '') + '~' + esc(SPI && SPI.to || '') + ')로 줄 세웠다 · 느린 차례 · 고르면 그 교차로 둘레 500m 를 엮는다</div>' +
      '<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin:6px 0">' + DGK.map(function (k, i) { return '<button data-sp="dg:' + i + '"' + (i === LIST.dg ? ' class="go"' : '') + '>' + k + '</button>'; }).join('') +
      '<select data-sp="h">' + hs.join('') + '</select></div>' +
      (live ? '<div class="sn">🔴 지금 = ITS ' + esc(live.made) + ' 받은 값(20분 안) · 괄호 = 지금 시각(' + DGK[dgOf(new Date())] + ' ' + new Date().getHours() + '시) 평소의 몇 % · 60% 밑이면 붉게</div>' : '<div class="warn">지금 실측(ITS)은 20분 넘은 값이거나 없어 쓰지 않았다 — 평소 값만으로 줄 세웠다</div>');
    if (!R.length) return void (P.innerHTML = h0 + '<div class="warn">이 둘레 2km 에 평소 속도가 붙은 신호 교차로가 없다 — 여섯 구(서초·강남·송파·동작·관악·용산) 안으로 지도를 옮겨 다시</div>');
    P.innerHTML = h0 + '<table><tr><th>교차로</th><th>가장 느린 들어오는 길(평소)</th><th>지금</th><th></th></tr>' + R.slice(0, 25).map(function (r, i) {
      var lvt = r.lv ? '<b style="color:' + (r.lv.r < 0.6 ? '#dc2626' : 'inherit') + '">' + r.lv.v + '</b> <small>(평소 ' + Math.round(r.lv.r * 100) + '%)</small>' : '—';
      return '<tr><td>' + esc(r.nm) + ' <small>' + esc(r.no) + ' · ' + r.src + ' · ' + Math.round(r.d) + 'm</small></td><td><b>' + r.v + 'km/h</b> ' + esc(r.rd) + (r.lim ? ' <small>(제한 ' + r.lim + ')</small>' : '') + '</td><td>' + lvt + '</td><td><button data-sp="pk:' + i + '">🧪 엮기</button></td></tr>'; }).join('') + '</table>' +
      '<div class="sn" style="margin-top:6px">평소 속도는 접근로 첫 링크 기준 · 요일 갈래마다 3날 미만은 잠정 · 신호값이 실제로 붙는지는 엮을 때 다시 본다(없으면 「신호 없이 지나감」)</div>';
  }
  function list() {
    var c = viewLL() || [37.4919, 127.0076], P = panel(); LIST.c = c; P.innerHTML = head('막히는 교차로 고르기') + '<div class="sn" id="m2dSimPProg">자료 받는 중…</div>';
    var now = new Date(); if (LIST.h == null) { LIST.h = Math.min(23, Math.max(7, now.getHours())); LIST.dg = dgOf(now); }
    base(function (m) { var e = $('m2dSimPProg'); if (e) e.textContent = m; }).then(function () {
      return Promise.all([spdFor(c[0], c[1]), fetch('data/live-spd-six.json?t=' + Math.floor(Date.now() / 300000)).then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })]);
    }).then(function (a) { var j = a[1]; LIST.live = j && j.at && (Date.now() / 1000 - j.at) / 60 <= 20 ? j : null; relist(); })
      .catch(function (er) { P.innerHTML = head('막히는 교차로 고르기') + '<div class="warn">' + esc(er && er.message || er) + '</div>'; });
  }
  function relist() { LIST.rows = rank(LIST.c[0], LIST.c[1], LIST.live && LIST.live.m); listPaint(); }
  window.tgSimPick = { build: build, bake: bake, open: open, close: close, list: list, rank: function (lat, lon, dg, h) { LIST.dg = dg; LIST.h = h; return rank(lat, lon, null); }, tapLL: tapLL, ready: function () { return !!NAV; } };
  function boot() { cardHook(); document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && PANEL && PANEL.classList.contains('on')) close(); }); }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
