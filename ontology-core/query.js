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
    return { id: intId, nm: it.nm, cits: it.cits || null, dong: it.dongnm || '',
      acc: A ? { y0: A.y0, years: A.years, total: tot, dead: A.dead, serious: A.serious, ped: A.ped, night: A.night, nightShare: tot ? A.night / tot : null, tod: A.tod, cells: A.cells, r: A.r, grade: acc.p.g } : null,
      noAcc: A ? null : '둘레 ' + 70 + 'm 안에 사고 칸이 없다(TAAS 2016~2025)',
      mainViolations: vio, cams: cams, zones: zones, actions: acts,
      notes: ['사고는 교차로에서 70m 안 100m 칸을 묶은 근사(등급 C) · 칸마다 주 위반 하나만 있어 위반 건수는 「주 위반인 칸들의 건수」', '과거 조치는 교통과 출력물이 있는 5곳만'] };
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
  if (typeof module !== 'undefined' && module.exports) module.exports = OntoCore; else root.OntoCore = OntoCore;
})(typeof self !== 'undefined' ? self : this);
