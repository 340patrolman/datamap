/* 교통 온톨로지 코어 v1 — 질의(의존성 0 · ES5 · 브라우저·Cloudflare Worker·node 어디서나 같은 코드)
   쓰기: var o = new OntoCore(core);  o.q1('INT-521') · o.q2('INT-521') · o.q3('VIO-02') · o.q5('INT-521')
   core = ontology-core/data/core-seocho.json(build.py 가 굽는다) · 스키마 = ontology-core/schema-ext.json
   원칙: 값을 지어내지 않는다(없으면 null 과 「없음」 까닭) · 질문 5 는 한 점수로 합치지 않는다(항목마다 가까운 순) */
(function (root) {
  function OntoCore(core) {
    var self = this; this.core = core; this.O = {}; this.out = {}; this.inn = {};
    core.objects.forEach(function (o) { self.O[o.id] = o; });
    core.edges.forEach(function (e) { (self.out[e[0]] = self.out[e[0]] || []).push(e); (self.inn[e[2]] = self.inn[e[2]] || []).push(e); });
  }
  var P = OntoCore.prototype;
  P.get = function (id) { return this.O[id] || null; };
  /* 링크 따라가기 — rel 이 같은 바깥(out)·안쪽(in) 링크의 상대 객체와 링크 속성 */
  P.follow = function (id, rel) { var self = this; return (this.out[id] || []).filter(function (e) { return !rel || e[1] === rel; }).map(function (e) { return { o: self.O[e[2]], p: e[3] }; }); };
  P.back = function (id, rel) { var self = this; return (this.inn[id] || []).filter(function (e) { return !rel || e[1] === rel; }).map(function (e) { return { o: self.O[e[0]], p: e[3] }; }); };
  /* 체인 — rels 차례대로 따라감(예 ['발생', '주요원인', '근거']) */
  P.chain = function (id, rels) { var cur = [id], self = this; rels.forEach(function (r) { var nx = []; cur.forEach(function (c) { self.follow(c, r).forEach(function (x) { if (nx.indexOf(x.o.id) < 0) nx.push(x.o.id); }); }); cur = nx; }); return cur.map(function (i) { return self.O[i]; }); };
  function sum(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return s; }
  /* 질문 1 — 이 교차로는 왜 위험한가 */
  P.q1 = function (intId) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; var self = this;
    var acc = this.follow(intId, '발생')[0], A = acc ? acc.o : null;
    var vio = A ? this.follow(A.id, '주요원인').map(function (x) { return { id: x.o.id, nm: x.o.nm, n: x.p.n }; }).sort(function (a, b) { return b.n - a.n; }) : [];
    var cams = this.follow(intId, '보유').map(function (x) { return { lim: x.o.lim, road: x.o.road || '' }; });
    var zones = this.follow(intId, '가까움').map(function (x) { return { kind: x.o.kind, nm: x.o.nm || '', d: x.p.d }; }).sort(function (a, b) { return a.d - b.d; });
    var acts = this.back(intId, '대상').map(function (x) { return { id: x.o.id, what: x.o.what, ym: x.o.ym || null }; });
    var tot = A ? sum(A.years) : 0;
    var dg = this.follow(intId, '속함')[0], G = dg ? dg.o : null;
    return { id: intId, nm: it.nm, cits: it.cits || null, dong: it.dongnm || '',
      dng: G ? { id: G.id, nm: G.nm, hh: G.hh, res: G.res, fgn: G.fgn, biz: G.biz, bars: G.bars, jur: G.jur || [], grade: dg.p.g } : null,
      acc: A ? { y0: A.y0, years: A.years, total: tot, dead: A.dead, serious: A.serious, ped: A.ped, night: A.night, nightShare: tot ? A.night / tot : null, tod: A.tod, cells: A.cells, r: A.r, grade: acc.p.g } : null,
      noAcc: A ? null : '둘레 ' + 70 + 'm 안에 사고 칸이 없다(TAAS 2016~2025)',
      mainViolations: vio, cams: cams, zones: zones, actions: acts,
      notes: ['사고는 교차로에서 70m 안 100m 칸을 묶은 근사(등급 C) · 칸마다 주 위반 하나만 있어 위반 건수는 「주 위반인 칸들의 건수」', '과거 조치는 교통과 출력물이 있는 5곳만'] };
  };
  /* 질문 7 — 이 동 한눈에(2026-10-23 행정동을 그래프에 · 엮임 지도 첫째): 동의 사람·일터·술자리·관할 + 그 동 안 교차로(10년 사고 많은 순)
     교차로마다 사고는 70m 안 칸을 묶은 근사라 이웃 교차로끼리 겹친다 — 동 합계로 더하지 않는다 */
  P.q7 = function (dngId, k) {
    var G = this.O[dngId]; if (!G || G.t !== 'DNG') return null; var self = this;
    var ints = this.back(dngId, '속함').map(function (x) { var q = self.q1(x.o.id); return { id: q.id, nm: q.nm, total: q.acc ? q.acc.total : 0, night: q.acc ? q.acc.night : 0, ped: q.acc ? q.acc.ped : 0, cams: q.cams.length, main: q.mainViolations[0] ? q.mainViolations[0].nm : null }; })
      .sort(function (a, b) { return b.total - a.total || (a.id < b.id ? -1 : 1); });
    return { id: dngId, nm: G.nm, code: G.code, people: { hh: G.hh, one: G.one, res: G.res, fgn: G.fgn }, work: { biz: G.biz, wk: G.wk }, night: { bars: G.bars, hof06: G.hof06 }, jur: G.jur || [],
      nInt: ints.length, ints: ints.slice(0, k || 5), noCam: ints.filter(function (x) { return !x.cams && x.total > 0; }).length,
      notes: ['교차로 사고는 70m 안 칸 묶음이라 겹친다 — 동 합계로 더하지 않았다', '값은 그 동을 열쇠로 가진 파일 그대로(세대·주민 = 행정안전부 · 외국인주민 = 2024.11.1 · 사업장 = 국민연금 2026-08 · 주점·결제 = 서울만)'] };
  };
  /* 질문 8 — 이 교차로에 무슨 일이 있었나(2026-10-23 사건을 그래프에 · 엮임 지도 둘째): since(YYYY-MM-DD) 뒤에 시작한 집회·공연·돌발(최근 먼저) + 침수 흔적이 있던 해
     「근처」 = 집회 300m · 공연 500m · 돌발 150m 안(근사 C) · 돌발은 이 PC 가 10분마다 받은 기록(2026-10-15~)이라 받지 못한 때의 일은 없다 */
  P.q8 = function (intId, since, k) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; since = since || '';
    var ev = this.back(intId, '근처').filter(function (x) { return String(x.o.d0) >= since; }).map(function (x) { return { id: x.o.id, kind: x.o.kind, sub: x.o.sub || null, d0: x.o.d0, d1: x.o.d1 || null, nm: x.o.nm, n: x.o.n == null ? null : x.o.n, d: x.p.d, src: x.o.src }; })
      .sort(function (a, b) { return a.d0 < b.d0 ? 1 : a.d0 > b.d0 ? -1 : (a.id < b.id ? -1 : 1); });
    var cnt = {}; ev.forEach(function (e) { var key = e.kind + (e.sub ? '·' + e.sub : ''); cnt[key] = (cnt[key] || 0) + 1; });
    var fl = this.back(intId, '흔적').map(function (x) { return { year: +x.o.d0, n: x.p.n, dep: x.p.dep }; }).sort(function (a, b) { return a.year - b.year; });
    return { id: intId, nm: it.nm, since: since, n: ev.length, counts: cnt, events: ev.slice(0, k || 20), flood: fl,
      notes: ['둘레 반지름 안 사건(근사 C) — 그 교차로에서 일어났다는 뜻이 아니다', '집회 = 경찰청 주요 집회만(신고값) · 공연 = 1,000석 이상 · 돌발 = 2026-10-15 부터 이 PC 가 받은 기록', '침수 = 서울시 침수흔적도(건물·필지 가운데 점 · 100m 안) — 길이 잠겼다는 기록이 아니다'] };
  };
  /* 도로 구간들에 걸친 사고 칸 묶음(2026-10-23) — 칸은 한 구간에만 붙어 겹쳐 세지 않는다 · 주 위반은 「그 위반이 주 위반인 칸들의 건수」 */
  P.rdAcc = function (rds) {
    var self = this, cs = []; rds.forEach(function (r) { self.follow(r.id, '사고칸').forEach(function (x) { cs.push(x.o); }); });
    if (!cs.length) return null; var yrs = [], mv = {};
    cs.forEach(function (c) { c.years.forEach(function (v, i) { yrs[i] = (yrs[i] || 0) + v; }); if (c.mv) mv[c.mv] = mv[c.mv] || { nm: c.mvnm, n: 0 }, mv[c.mv].n += c.mvn; });
    return { cells: cs.length, y0: 2016, years: yrs, total: sum(yrs), dead: sum(cs.map(function (c) { return c.dead; })), serious: sum(cs.map(function (c) { return c.serious; })), ped: sum(cs.map(function (c) { return c.ped; })), night: sum(cs.map(function (c) { return c.night; })),
      mainViolations: Object.keys(mv).map(function (k) { return { code: k, nm: mv[k].nm, n: mv[k].n }; }).sort(function (a, b) { return b.n - a.n || (a.code < b.code ? -1 : 1); }) };
  };
  /* 질문 9 — 이 교차로로 들어오는 길(2026-10-23 접근로·도로 구간 · 엮임 지도 셋째): 들어오는 쪽마다 길 이름·제한속도·차로 · 평소 속도(월~목 8·18·3시) · 침수 흔적 · 막히면 돌아가는 부담 · 지나는 250m 칸
     평소 속도 = 그 쪽 ITS 링크 가운데 값 있는 것만 길이를 시간으로 나눈 것(링크마다 가운데값 · 덮은 길이 cov 를 같이 본다) · 본 날이 3날 미만이면 잠정 */
  P.q9 = function (intId) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; var self = this, H = ['0-8', '0-18', '0-3'];
    var aps = this.follow(intId, '들어오는길').map(function (x) {
      var A = x.o, rds = self.follow(A.id, '이룸').sort(function (a, b) { return a.p.r - b.p.r || a.p.k - b.p.k; }).map(function (y) { return y.o; }), sp = {}, cells = {};
      H.forEach(function (h) { var t = 0, c = 0, pv = 0; rds.forEach(function (r) { var v = r.sp && r.sp[h]; if (v && v[0] > 0) { t += r.len / v[0] * 3.6; c += r.len; if (v[3]) pv = 1; } }); sp[h] = c ? { kmh: Math.round(c / t * 3.6), cov: c, prov: pv } : null; });
      var wet = rds.filter(function (r) { return r.fy; });
      rds.forEach(function (r) { self.follow(r.id, '지남').forEach(function (z) { cells[z.o.id] = 1; }); });
      return { id: A.id, dir: A.dir, frm: A.frm, nm: A.nm, roads: A.rds, nLinks: rds.length, len: rds.reduce(function (s, r) { return s + r.len; }, 0), speed: sp,
        flood: wet.length ? { links: wet.length, years: Math.max.apply(null, wet.map(function (r) { return r.fy; })), last: Math.max.apply(null, wet.map(function (r) { return r.fl; })), dep: Math.max.apply(null, wet.map(function (r) { return r.fd || 0; })),
          detour: Math.max.apply(null, wet.map(function (r) { return r.dt == null ? -1 : r.dt; })), noDetour: wet.filter(function (r) { return r.dt === -1; }).length } : null,
        cells: Object.keys(cells).sort(), acc: self.rdAcc(rds) };
    }).sort(function (a, b) { return ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw'].indexOf(a.dir) - ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw'].indexOf(b.dir); });
    return { id: intId, nm: it.nm, cits: it.cits, n: aps.length, approaches: aps,
      notes: aps.length ? ['들어오는 쪽은 ITS 링크 방위로 가른 것(대각 교차로는 45° 어긋날 수 있다)', '평소 속도 = 2026-10-11 부터 쌓은 ITS 실시간 소통의 가운데값 · 잠정 = 본 날 3날 미만', '침수 = 그 길 30m 안 침수 흔적(길이 잠겼다는 기록 아님) · 돌아가는 부담은 제한속도·막힘 없음 기준이라 실제보다 작다', '사고 = TAAS 2016~2025 100m 칸 가운데가 길 50m 안인 것(가장 가까운 구간 하나에만) — 칸에는 방향이 없어 맞은편 차로·교차로 안 사고도 섞인다 · 교차로 q1 의 70m 묶음과 겹친다'] : ['이 교차로는 접근로 자료가 없다(신호 번호가 없거나 서초구 + 2km 밖)'] };
  };
  /* 질문 10 — 이 도로 구간이 막히면(2026-10-23): 그 길이 들어가는 교차로·쪽 · 평소 속도 · 침수 · 돌아가는 부담 · 지나는 칸 */
  P.q10 = function (rdId) {
    var R = this.O[rdId]; if (!R || R.t !== 'RD') return null; var self = this;
    var feeds = this.back(rdId, '이룸').map(function (x) { var I = self.back(x.o.id, '들어오는길')[0]; return { apr: x.o.id, dir: x.o.dir, frm: x.o.frm, int: I ? I.o.id : null, intNm: I ? I.o.nm : null, k: x.p.k }; })
      .sort(function (a, b) { return a.k - b.k || (a.apr < b.apr ? -1 : 1); });
    return { id: rdId, link: R.link, nm: R.nm, len: R.len, lim: R.lim || null, gr: R.gr || null, ln: R.ln || null, speed: R.sp || null,
      flood: R.fy ? { years: R.fy, last: R.fl, dep: R.fd, detour: R.dt } : null, acc: this.rdAcc([R]), feeds: feeds, cells: this.follow(rdId, '지남').map(function (z) { return z.o.id; }),
      notes: ['k = 교차로에서 거슬러 간 차례(0 이 교차로에 바로 닿는 링크)', '돌아가는 부담은 그 길 한 구간이 통째로 막혔다고 본 제한속도 기준 값'] };
  };
  /* 질문 11 — 이 교차로 둘레 사람과 사고 시각(2026-10-23 칸 ↔ 생활인구): 교차로가 든 250m 칸의 평일·주말 시간대 사람 · 들어오는 길이 지나는 칸들의 합 ·
     6시간 네 갈래(0~6·6~12·12~18·18~24)마다 「사람 몫」과 「사고 몫」(교차로 70m 사고 묶음)을 나란히 — 둘을 한 점수로 섞지 않는다 */
  P.q11 = function (intId) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; var self = this;
    var pc = this.follow(intId, '들어감')[0], C = pc ? pc.o : null;
    function bins(a) { var b = [0, 0, 0, 0]; a.forEach(function (v, h) { b[Math.floor(h / 6)] += v; }); return b; }
    function pct(b) { var t = sum(b); return t ? b.map(function (v) { return Math.round(v / t * 1000) / 10; }) : null; }
    function peak(a) { var m = -1, h = null; a.forEach(function (v, i) { if (v > m) { m = v; h = i; } }); return { h: h, n: m }; }
    var here = C && C.wd ? { id: C.id, wd: C.wd, we: C.we, ad: C.ad, an: C.an, peakWd: peak(C.wd), peakWe: peak(C.we), dayWd: sum(C.wd), dayWe: sum(C.we) } : null;
    var cells = {}; this.follow(intId, '들어오는길').forEach(function (a) { self.follow(a.o.id, '이룸').forEach(function (r) { self.follow(r.o.id, '지남').forEach(function (z) { cells[z.o.id] = z.o; }); }); });
    if (C) cells[C.id] = C;
    var ids = Object.keys(cells).sort(), wd = [], we = [], miss = 0;
    for (var h = 0; h < 24; h++) { wd[h] = 0; we[h] = 0; }
    ids.forEach(function (k) { var o = cells[k]; if (!o.wd) { miss++; return; } o.wd.forEach(function (v, h) { wd[h] += v; }); o.we.forEach(function (v, h) { we[h] += v; }); });
    var A = (this.follow(intId, '발생')[0] || {}).o, acc = A && A.tod ? A.tod : null;
    return { id: intId, nm: it.nm, here: here,
      around: ids.length - miss ? { cells: ids.length, noData: miss, wd: wd, we: we, peakWd: peak(wd), peakWe: peak(we) } : null,
      bins: { names: ['0~6시', '6~12시', '12~18시', '18~24시'], peopleWd: here ? pct(bins(here.wd)) : null, acc: acc ? pct(acc) : null, accN: acc },
      notes: ['사람 = 서울 생활인구(내국인) 250m 격자 · 2026-09-07~13 한 주 평균(추석 피함) · 3명 이하 칸은 0 · 서울 밖 칸은 값 없음', '사람 몫은 「그 칸에 머문 사람」을 시간마다 더한 것 — 지나간 차량 수가 아니다', '사고 몫 = 교차로 70m 안 사고 칸 10년 시간대(TAAS) · 두 몫은 나란히 볼 뿐 한 점수로 섞지 않는다', '둘레 = 교차로 칸 + 들어오는 길이 지나는 칸(사람 수를 그냥 더함 — 칸끼리 겹치지 않는다)'] };
  };
  /* 질문 12 — 이 교차로는 어느 서·어느 지구대 몫인가(2026-10-23): 관할 경찰서(대표번호) · 가장 가까운 지구대·파출소(근사) · 그 서의 다른 지구대 가까운 차례 */
  P.q12 = function (intId) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; var self = this;
    var st = this.follow(intId, '관할').map(function (x) { return { id: x.o.id, nm: x.o.nm, tel: x.o.tel || null, g: x.p.g, kind: x.p.kind || null, tgis: x.p.tg == null ? null : x.p.tg, how: x.p.src }; });
    var nb = this.follow(intId, '가까운지구대')[0];
    var others = st.length ? this.back(st[0].id, '소속').map(function (x) { return { id: x.o.id, nm: x.o.nm, kind: x.o.kind, d: Math.round(Math.hypot((x.o.lon - it.lon) * 88400, (x.o.lat - it.lat) * 111000)) }; }).sort(function (a, b) { return a.d - b.d || (a.id < b.id ? -1 : 1); }) : [];
    return { id: intId, nm: it.nm, stations: st, pbox: nb ? { id: nb.o.id, nm: nb.o.nm, kind: nb.o.kind, addr: nb.o.addr || null, d: nb.p.d, g: nb.p.g } : null, others: others.slice(0, 4),
      notes: ['관할서 = 현장 기준 경계(서초·방배 · 반포4동은 반포대로) 또는 별표2 × 행정동 — 번지로 나뉜 동은 두 서를 다 적는다', '지구대·파출소 = 관할 경계가 공개되지 않아 그 서의 가장 가까운 곳(근사) — 실제 담당 구역과 다를 수 있다', 'tgis = 서울시 T-GIS 교차로 관할 코드와 맞는지(1 맞음 · 0 다름 · null 코드 이름을 모름)', 'kind disagree·tgis = 경계와 T-GIS 관할 코드가 다른 서를 가리킨다(서로 맞닿은 길 위 교차로가 대부분) — 둘 다 적고 앞이 경계 쪽 · 형님 확인 대기'] };
  };
  /* 질문 13 — 이 지구대·파출소 몫(가장 가까운 지구대로 묶은 근사) 교차로: 10년 사고 많은 순 */
  P.q13 = function (pbxId, k) {
    var B = this.O[pbxId]; if (!B || B.t !== 'PBX') return null; var self = this, S = this.follow(pbxId, '소속')[0];
    var ints = this.back(pbxId, '가까운지구대').map(function (x) { var q = self.q1(x.o.id); return { id: q.id, nm: q.nm, d: x.p.d, total: q.acc ? q.acc.total : 0, night: q.acc ? q.acc.night : 0, main: q.mainViolations[0] ? q.mainViolations[0].nm : null }; })
      .sort(function (a, b) { return b.total - a.total || (a.id < b.id ? -1 : 1); });
    return { id: pbxId, nm: B.nm, kind: B.kind, station: S ? { id: S.o.id, nm: S.o.nm, tel: S.o.tel || null } : null, nInt: ints.length, ints: ints.slice(0, k || 10),
      notes: ['가장 가까운 지구대로 묶은 근사 — 공식 담당 구역이 아니다', '교차로 사고는 70m 안 칸 묶음이라 이웃 교차로끼리 겹친다 — 더하지 않았다'] };
  };
  /* 질문 14 — 이 교차로에 누가 가장 빨리 닿나(2026-10-23 도착 · 엮임 지도 일곱째): 지구대·파출소 다섯의 제한속도·평일 8시·18시 초 · 관할(가까운 지구대)과 견줌
     견주는 값이다 — 실측 평소 속도가 없는 길은 eta-cal 배율이라 짧게 나오고, 회전 제한·순찰 중인 차·긴급 주행은 보지 않는다 */
  P.q14 = function (intId, hour) {
    var it = this.O[intId]; if (!it || it.t !== 'INT') return null; var self = this, key = hour === 8 ? 's8' : hour === 18 ? 's18' : 's0';
    var nb = this.follow(intId, '가까운지구대')[0], st = this.follow(intId, '관할').map(function (x) { return x.o.id; });
    var L = this.follow(intId, '도착').map(function (x) { var S = self.follow(x.o.id, '소속')[0]; return { id: x.o.id, nm: x.o.nm, station: S ? S.o.nm : null, ownStation: S ? st.indexOf(S.o.id) >= 0 : false, s0: x.p.s0, s8: x.p.s8, s18: x.p.s18, c8: x.p.c8, c18: x.p.c18 }; })
      .filter(function (x) { return x[key] >= 0; }).sort(function (a, b) { return a[key] - b[key] || (a.id < b.id ? -1 : 1); });
    var mine = nb ? L.filter(function (x) { return x.id === nb.o.id; })[0] || null : null;
    return { id: intId, nm: it.nm, by: key, fastest: L[0] || null, list: L, nearestOwn: nb ? { id: nb.o.id, nm: nb.o.nm, t: mine ? mine[key] : null } : null,
      otherFaster: !!(L[0] && nb && L[0].id !== nb.o.id), gap: L[0] && mine ? mine[key] - L[0][key] : null,
      notes: ['견주는 값 — 실제 출동 시간이 아니다(신호·회전 제한·순찰 중인 차·긴급 주행 없음 · 실측 없는 길은 짧게 나옴)', 's8·s18 = 평일 8·18시 평소 속도(ITS 2026-10-11~ 쌓음 · 잠정일 수 있음) · c = 그 길 가운데 실측 속도로 센 몫 %', '가까운 지구대(관할 근사)보다 다른 곳이 빨리 닿으면 otherFaster — 관할·배정을 바꾸자는 뜻이 아니라 지원 요청 차례를 볼 때 쓴다'] };
  };
  /* 질문 15 — 이 지구대·파출소가 가장 빨리 닿는 교차로(평일 18시 기준 · 근사) · 자기 몫인데 다른 곳이 더 빠른 교차로 */
  P.q15 = function (pbxId, hour) {
    var B = this.O[pbxId]; if (!B || B.t !== 'PBX') return null; var self = this, first = [], slower = [];
    Object.keys(this.O).forEach(function (i) { if (self.O[i].t !== 'INT') return; var q = self.q14(i, hour == null ? 18 : hour); if (!q || !q.fastest) return;
      if (q.fastest.id === pbxId) first.push({ id: i, nm: q.nm, t: q.fastest[q.by] });
      if (q.nearestOwn && q.nearestOwn.id === pbxId && q.otherFaster) slower.push({ id: i, nm: q.nm, fastest: q.fastest.nm, gap: q.gap }); });
    first.sort(function (a, b) { return a.t - b.t || (a.id < b.id ? -1 : 1); }); slower.sort(function (a, b) { return (b.gap || 0) - (a.gap || 0) || (a.id < b.id ? -1 : 1); });
    return { id: pbxId, nm: B.nm, hour: hour == null ? 18 : hour, nFirst: first.length, under3min: first.filter(function (x) { return x.t <= 180; }).length, first: first, slowerOwn: slower,
      notes: ['가장 빨리 닿는 곳 = 도착 다섯 가운데 그 시각 초가 가장 짧은 곳(견주는 값)', 'slowerOwn = 이 지구대가 가장 가까운(관할 근사) 교차로인데 다른 지구대·파출소가 더 빨리 닿는 곳'] };
  };
  /* 질문 2 — 왜 바꿨고 바꾼 뒤 어떻게 됐나(해 단위 · 앞 2해 vs 뒤 2해 · 바꾼 해는 뺀다) */
  P.q2 = function (intId) {
    var self = this, it = this.O[intId]; if (!it) return null; var acc = this.follow(intId, '발생')[0], A = acc ? acc.o : null;
    var list = this.back(intId, '대상').map(function (x) {
      var a = x.o, rec = self.follow(a.id, '근거기록')[0], y = a.ym ? +String(a.ym).slice(0, 4) : null, cmp = null, why = null;
      if (y && A) { var yr = function (k) { var i = k - A.y0; return i >= 0 && i < A.years.length ? A.years[i] : null; }, b = [yr(y - 2), yr(y - 1)], f = [yr(y + 1), yr(y + 2)];
        if (b[0] == null || b[1] == null) why = '앞 두 해 자료가 없다(TAAS 2016 부터)'; else if (f[0] == null || f[1] == null) why = '뒤 두 해가 아직 지나지 않았다(TAAS ' + (A.y0 + A.years.length - 1) + ' 까지)';
        else cmp = { before: [y - 2, y - 1], beforeN: b[0] + b[1], after: [y + 1, y + 2], afterN: f[0] + f[1] }; }
      else if (!y) why = '이력 글에 연·월이 없다'; else why = '둘레 사고 칸이 없다';
      return { id: a.id, what: a.what, ym: a.ym || null, reason: rec ? rec.o.text : null, reasonGrade: rec ? rec.p.g : null, internalDoc: !!(rec && rec.o.internal), compare: cmp, noCompare: why };
    }).sort(function (a, b) { return String(a.ym || '9999').localeCompare(String(b.ym || '9999')); });   /* 연·월이 있는 것부터 · 없는 것은 끝에 */
    return { id: intId, nm: it.nm, actions: list, notes: list.length ? ['사고는 해 단위라 같은 해·이웃 해에 조치가 여럿이면 어느 조치 덕인지 가르지 못한다', '사유는 이력 글에 적힌 것만 — 자세한 사유는 교통과 내부 문서'] : ['이 교차로의 조치 이력 자료가 없다(교통과 출력물 5곳만 있다)'] };
  };
  /* 질문 3 — 이 위반유형의 근거 조문·판례·범칙금·벌점 */
  P.q3 = function (vioId) {
    var self = this, v = this.O[vioId]; if (!v || v.t !== 'VIO') return null;
    var laws = this.follow(vioId, '근거').map(function (x) { return { id: x.o.id, title: x.o.title, meta: x.o.meta, penalty: x.o.penalty || null, linkGrade: x.p.g,
      precedents: self.follow(x.o.id, '해석').map(function (y) { return { no: y.o.no, court: y.o.court, date: y.o.date, nm: y.o.nm || '', how: y.p.src, arts: y.p.arts || null }; }) }; });
    return { id: vioId, nm: v.nm, laws: laws, none: laws.length ? null : 'T-Book 범칙금 DB 에 이 위반유형과 같은 항목이 없다', notes: ['조문·범칙금·벌점 글은 T-Book 범칙금 DB 그대로(2026-10-08 월간 점검) · 위반유형↔항목은 이름 맞대기(등급 C)', '판례는 원문 대조된 것만(T-Book PRECDOC)'] };
  };
  /* 질문 5 — 비슷한 교차로(항목마다 가까운 순 5곳 · 합치지 않는다) */
  P.q5 = function (intId, k) {
    k = k || 5; var self = this, me = this.q1(intId); if (!me || !me.acc) return { id: intId, none: '사고 자료가 없어 비교할 수 없다' };
    var all = Object.keys(this.O).filter(function (i) { return self.O[i].t === 'INT' && i !== intId; }).map(function (i) { return self.q1(i); }).filter(function (q) { return q && q.acc && q.acc.total > 0; });
    var mv = me.mainViolations[0] ? me.mainViolations[0].id : null;
    function top(list, f) { return list.map(function (q) { return [q, f(q)]; }).filter(function (x) { return x[1] != null; }).sort(function (a, b) { return a[1] - b[1]; }).slice(0, k).map(function (x) { return { id: x[0].id, nm: x[0].nm, diff: Math.round(x[1] * 1000) / 1000 }; }); }
    var mvn = me.mainViolations[0] ? me.mainViolations[0].n : 0;
    return { id: intId, nm: me.nm, base: { mainViolation: mv ? self.O[mv].nm : null, nightShare: me.acc.nightShare, total: me.acc.total, cams: me.cams.length, zones: me.zones.length },
      dims: {
        mainv: { name: '주 위반이 같다(' + (mv ? self.O[mv].nm : '없음') + ')', list: mv ? top(all.filter(function (q) { return q.mainViolations[0] && q.mainViolations[0].id === mv; }), function (q) { return Math.abs(q.mainViolations[0].n - mvn); }) : [] },
        night: { name: '밤 사고 몫', list: top(all, function (q) { return q.acc.nightShare == null ? null : Math.abs(q.acc.nightShare - me.acc.nightShare); }) },
        total: { name: '사고 규모(10년 합)', list: top(all, function (q) { return Math.abs(Math.log(1 + q.acc.total) - Math.log(1 + me.acc.total)); }) },
        fac: { name: '시설 구성(카메라·보호구역)', list: top(all, function (q) { return Math.abs(q.cams.length - me.cams.length) + Math.abs(q.zones.length - me.zones.length); }) }
      }, notes: ['항목마다 따로 가까운 순 — 한 점수로 합치지 않는다(ONTOLOGY-2 결정 D4)'] };
  };
  /* 질문 6 — 이 규칙은 무엇에 기대나(data/onto-rules.json · 값은 장부 그대로) · rules(영역) = 그 영역 규칙 목록 */
  P.rules = function (area) { var self = this; return Object.keys(this.O).filter(function (i) { var o = self.O[i]; return o.t === 'RULE' && (!area || o.area === area); }).sort().map(function (i) { var o = self.O[i]; return { id: o.id, area: o.area, title: o.title, g: o.g, n: self.back(o.id, '뒷받침').length }; }); };
  P.why = function (ruleId) { var r = this.O[ruleId]; if (!r || r.t !== 'RULE') return null;
    return { id: r.id, area: r.area, title: r.title, d: r.d, g: r.g, s: r.s || [], o: r.o || [], test: r.test || null,
      field: this.back(ruleId, '뒷받침').map(function (x) { return { id: x.o.id, date: x.o.date, said: x.o.said, conf: x.o.conf || null }; }).sort(function (a, b) { return String(a.date).localeCompare(String(b.date)); }),
      notes: ['규칙·현장 판단은 장부(data/onto-rules.json) 글 그대로 — 법령 숫자는 정본(T-Book) 자리만 가리킨다'] }; };
  P.q6 = P.why;
  if (typeof module !== 'undefined' && module.exports) module.exports = OntoCore; else root.OntoCore = OntoCore;
})(typeof self !== 'undefined' ? self : this);
