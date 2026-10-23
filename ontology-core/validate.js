/* 교통 온톨로지 코어 v1 — 검증(의존성 0 · ES5)
   ontoValidate(core, schema) → { ok, errors[], warnings[], counts }
   보는 것: ID 중복 · 고아 링크(끝이 없는 객체) · 링크 타입 위반(스키마 from/to) · 필수 속성 누락 · 모르는 객체·링크 타입 · 등급 없음 · 개인정보 꼴(휴대전화·주민번호·차량번호) */
(function (root) {
  var PII = [[/01[016789]-?\d{3,4}-?\d{4}/, '휴대전화'], [/\d{6}-?[1-4]\d{6}/, '주민번호'], [/(^|[^\d])\d{2,3}[가-힣]\s?\d{4}(?!\d)/, '차량번호']];
  function ontoValidate(core, schema) {
    var errors = [], warnings = [], O = {}, OT = schema.objectTypes, LT = schema.linkTypes, seen = {};
    core.objects.forEach(function (o) {
      if (seen[o.id]) errors.push('ID 중복: ' + o.id); seen[o.id] = 1; O[o.id] = o;
      var T = OT[o.t]; if (!T) { errors.push('모르는 객체 타입: ' + o.id + ' (' + o.t + ')'); return; }
      if (String(o.id).indexOf(o.t + '-') !== 0) errors.push('ID 머리가 타입과 다름: ' + o.id);
      (T.required || []).forEach(function (k) { if (o[k] == null || o[k] === '') errors.push('필수 속성 없음: ' + o.id + '.' + k); });
      Object.keys(o).forEach(function (k) { var v = o[k]; if (typeof v !== 'string') return; PII.forEach(function (p) { if (p[0].test(v) && !/^(INT|CAM|ATT|PLC|ACC|ACT|REC|PREC|LAW|VIO|RULE|FK|DNG|EVT|APR|RD|ACL|STA|PBX)-/.test(v)) warnings.push('개인정보 꼴(' + p[1] + ')?: ' + o.id + '.' + k); }); });
    });
    core.edges.forEach(function (e, i) {
      var a = O[e[0]], b = O[e[2]], L = LT[e[1]];
      if (!a) errors.push('고아 링크(앞 끝 없음) #' + i + ': ' + e[0] + ' —' + e[1] + '→ ' + e[2]);
      if (!b) errors.push('고아 링크(뒤 끝 없음) #' + i + ': ' + e[0] + ' —' + e[1] + '→ ' + e[2]);
      if (!L) { errors.push('모르는 링크 타입 #' + i + ': ' + e[1]); return; }
      if (a && a.t !== L.from) errors.push('링크 타입 위반 #' + i + ': ' + e[1] + ' 은 ' + L.from + ' 에서 — ' + e[0]);
      if (b && b.t !== L.to) errors.push('링크 타입 위반 #' + i + ': ' + e[1] + ' 은 ' + L.to + ' 로 — ' + e[2]);
      if (!e[3] || !e[3].g) warnings.push('등급 없는 링크 #' + i); if (!e[3] || !e[3].src) warnings.push('출처 없는 링크 #' + i);
    });
    var counts = {}; core.objects.forEach(function (o) { counts[o.t] = (counts[o.t] || 0) + 1; });
    return { ok: errors.length === 0, errors: errors.slice(0, 50), nErrors: errors.length, warnings: warnings.slice(0, 50), nWarnings: warnings.length, counts: counts, edges: core.edges.length };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = ontoValidate; else root.ontoValidate = ontoValidate;
})(typeof self !== 'undefined' ? self : this);
