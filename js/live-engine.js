/* live-engine.js — 🏡 여기 살면 계산부 v1 (2026-11-15)
   규칙 = data/live-rules.json(L) + data/tax-rules.json(T) · 세금은 TaxEngine(TE) 그대로 다시 씀 · 숫자 하드코딩 금지
   결과마다 steps(계산 과정)·warn(미확인·가정)·why(한도를 묶은 조건)를 돌려준다 · 개인 입력은 저장·전송하지 않는다
   금액 단위 = 원 · 나이 = 만 나이 */
(function (root) {
  'use strict';
  var won = function (x) { return Math.round(x); };
  function V(x) { return Array.isArray(x) ? x[0] : x; }
  function S(x) { return Array.isArray(x) ? x[1] : ''; }
  function W(warn, x) { var s = S(x); if (s && /미확인|설계값|일반적 견해|가정|— B|\(B\)|\/ B|B등급/.test(s) && warn.indexOf(s) < 0) warn.push(s); return V(x); }

  /* 원리금 균등 — 달마다 내는 돈 */
  function pmt(P, r, years) { var n = years * 12, i = r / 12; if (P <= 0) return 0; if (i === 0) return P / n; return P * i / (1 - Math.pow(1 + i, -n)); }
  /* 달마다 낼 수 있는 돈 → 빌릴 수 있는 원금 */
  function principal(M, r, years) { var n = years * 12, i = r / 12; if (M <= 0) return 0; if (i === 0) return M * n; return M * (1 - Math.pow(1 + i, -n)) / i; }

  /* 임대차 중개보수(한쪽) — a = {deposit, monthly} */
  function brokerLease(L, a, warn) {
    var Q = L.lease, d = a.deposit || 0, m = a.monthly || 0, base = d + m * W(warn, Q.mul);
    if (m && base < 5e7) base = d + m * W(warn, Q.mulLow);
    var tb = W(warn, Q.table), row = tb.filter(function (x) { return x[0] === null || base < x[0]; })[0], fee = base * row[1];
    if (row[2] != null) fee = Math.min(fee, row[2]);
    return { base: won(base), rate: row[1], fee: won(fee), cap: row[2] };
  }

  /* 매매 때 드는 부대비용(취득세·중개·인지세·채권 할인) — TaxEngine 그대로 */
  function buyCosts(T, TE, a, P) {
    var acq = TE.acq(T, { cat: 'apt', cause: 'buy', price: P, homesAfter: a.homesAfter || (a.noHome === false ? 2 : 1), adj: !!a.adj, area: a.area || 84 });
    var br = TE.broker(T, { cat: 'apt', price: P });
    var rg = TE.reg(T, { cat: 'apt', price: P, official: P * (a.offRatio || 0.7), metro: a.metro !== false, disc: a.bondDisc || 0 });
    var extra = a.legal || 0, moving = a.moving || 0;
    return { acq: acq.total, broker: br.fee != null ? br.fee : (br.total || 0), reg: rg.total, legal: extra, moving: moving, total: acq.total + (br.fee != null ? br.fee : (br.total || 0)) + rg.total + extra + moving, warn: [].concat(acq.warn || [], br.warn || [], rg.warn || []) };
  }

  /* 매매 대출 가능액 — 제한 중 가장 작은 값 · a = {incomeYr, debtMo, adj, first, rate, years, metro, didim(bool), age} */
  function loanBuy(L, a, P, warn) {
    var B = L.loan, lim = [];
    if (a.noHome === false) { var w0 = '집이 있는 사람의 추가 주택 대출은 셈하지 않았습니다(대출 0원으로 봄) — 수도권·규제지역은 추가 주택 구입 대출이 막히거나 기존 집 처분 조건이 붙습니다 · 미확인(은행 상담)'; if (warn.indexOf(w0) < 0) warn.push(w0); return { amt: 0, why: '집 있음 — 추가 주택 대출 셈 안 함', lim: [], rate: a.rate || V(B.rateBuy) }; }
    var ltvR = a.adj ? (a.first ? W(warn, B.ltv.adjFirst) : W(warn, B.ltv.adj)) : (a.first ? W(warn, B.ltv.nonFirst) : W(warn, B.ltv.non));
    lim.push(['LTV ' + Math.round(ltvR * 100) + '%', P * ltvR]);
    var r = a.rate || W(warn, B.rateBuy), yrs = a.years || W(warn, B.years), st = a.metro !== false ? W(warn, B.stress.metro) : W(warn, B.stress.other);
    var room = (a.incomeYr || 0) * W(warn, B.dsr) / 12 - (a.debtMo || 0);
    lim.push(['DSR ' + Math.round(W(warn, B.dsr) * 100) + '% (스트레스 +' + (st * 100).toFixed(2) + '%p)', principal(room, r + st, yrs)]);
    if (a.metro !== false || a.adj) { var ct = W(warn, B.capTiers).filter(function (x) { return x[0] === null || P <= x[0]; })[0]; lim.push(['수도권·규제 한도(시가 구간)', ct[1]]); }
    var best = lim.reduce(function (p, q) { return q[1] < p[1] ? q : p; });
    return { amt: Math.max(0, won(best[1])), why: best[0], lim: lim.map(function (q) { return [q[0], Math.max(0, won(q[1]))]; }), rate: r };
  }

  /* 디딤돌(정책 구입) — 자격이 되면 한도·금리 */
  function didim(L, a, P, warn) {
    var D = L.policy.didim, inc = a.first ? W(warn, D.incomeFirst) : W(warn, D.income);
    if (!a.noHome) return { ok: false, why: '무주택 아님' };
    if ((a.incomeYr || 0) > inc) return { ok: false, why: '소득 기준 넘음(' + (inc / 1e4).toLocaleString() + '만 원)' };
    if (P > W(warn, D.priceCap)) return { ok: false, why: '집값 기준 넘음' };
    if ((a.cash || 0) > W(warn, D.asset)) return { ok: false, why: '순자산 기준 넘음(가진 돈만으로 ' + (V(D.asset) / 1e8) + '억 초과)' };
    var wA = '디딤돌 순자산 ' + (V(D.asset) / 1e8) + '억 이하 · DTI 60% 는 묻지 않았습니다 — 가진 돈 말고 다른 재산·빚이 있으면 달라집니다(가정)'; if (warn.indexOf(wA) < 0) warn.push(wA);
    var max = a.first ? W(warn, D.maxFirst) : W(warn, D.max), r = W(warn, D.rate), yrs = W(warn, D.years);
    var room = (a.incomeYr || 0) * W(warn, L.loan.dsr) / 12 - (a.debtMo || 0);
    var lr = a.first && a.metro === false && !a.adj ? W(warn, D.ltvFirst) : W(warn, D.ltv), ltv = P * lr, dsr = principal(room, r, yrs), lim = [['상품 한도', max], ['LTV ' + Math.round(lr * 100) + '%', ltv], ['원리금 여력(DSR 40% 가정)', dsr]];
    warn.push('디딤돌 LTV·DSR 적용 방식 — 미확인(정책대출은 은행 DSR 과 다르게 셀 수 있습니다)');
    var best = lim.reduce(function (p, q) { return q[1] < p[1] ? q : p; });
    return { ok: true, amt: Math.max(0, won(best[1])), why: best[0], rate: r, lim: lim };
  }

  /* 거꾸로 — 이 돈이면 집값 얼마까지 (이분법) · a.cash = 가진 현금 */
  function affordBuy(L, T, TE, a) {
    var warn = [];
    function solve(useDidim, cap) {
      var lo = 0, hi = cap, best = null;
      for (var k = 0; k < 60; k++) {
        var P = (lo + hi) / 2, loan;
        if (useDidim) { var dd = didim(L, a, P, warn); if (!dd.ok) { hi = P; continue; } loan = { amt: dd.amt, why: '디딤돌 · ' + dd.why, rate: dd.rate, lim: dd.lim }; }
        else loan = loanBuy(L, a, P, warn);
        if (a.loanCap != null && loan.amt > a.loanCap) loan = { amt: won(a.loanCap), why: '내가 정한 부담 눈금', rate: loan.rate, lim: loan.lim };
        var c = buyCosts(T, TE, a, P), need = P - loan.amt + c.total;
        if (need <= (a.cash || 0)) { lo = P; best = { price: won(P), loan: loan, costs: c, need: won(need) }; } else hi = P;
        if (hi - lo < 1e5) break;
      }
      return best;
    }
    /* 은행 대출과 디딤돌은 따로 푼다 — 디딤돌은 집값 상한이 있어 한 줄로 풀면 경계에서 답이 튄다 */
    var best = solve(false, 5e9), bd = a.didim ? solve(true, W(warn, L.policy.didim.priceCap)) : null;
    if (bd && (!best || bd.price > best.price)) best = bd;
    if (!best) { var c0 = buyCosts(T, TE, a, 0); best = { price: 0, loan: { amt: 0, why: '가진 돈이 부대비용보다 적음', lim: [] }, costs: c0, need: 0 }; }
    var yrs = a.years || W(warn, L.loan.years), mo = pmt(best.loan.amt, best.loan.rate || a.rate || W(warn, L.loan.rateBuy), yrs);
    best.monthly = won(mo); best.rate = best.loan.rate || a.rate || V(L.loan.rateBuy); best.years = yrs;
    best.yearly = yearlyHold(T, TE, best.price, a);
    best.warn = warn.concat(best.costs.warn || []);
    best.steps = [['살 수 있는 집값(최대)', best.price], ['대출(' + best.loan.why + ')', best.loan.amt], ['취득세·교육세·농특세', best.costs.acq], ['중개보수(상한)', best.costs.broker], ['인지세(국민주택채권 할인 비용은 안 넣음)', best.costs.reg], ['법무사·이사(입력)', best.costs.legal + best.costs.moving], ['내 돈 쓰는 것', best.need], ['달마다 원리금(' + yrs + '년 균등)', best.monthly]];
    return best;
  }

  /* 금융비용 — 융자비율 · 달마다 내는 돈이 소득에서 차지하는 몫 · 금리가 바뀌면 · 부담 눈금으로 묶으면 집값 얼마
     눈금(금리 걸음·부담 몫)은 live-rules design.burden = 견줘 보는 설계값이지 기준·권고가 아니다 · 소득은 세전 */
  function burden(L, T, TE, a, h, mode) {
    var buy = mode === 'buy', loan = buy ? h.loan.amt : (h.loan || 0), base = buy ? h.price : h.deposit, r = h.rate, yrs = buy ? h.years : 0, inc = (a.incomeYr || 0) / 12, debt = a.debtMo || 0, D = L.design.burden;
    function pay(rr) { return buy ? pmt(loan, rr, yrs) : loan * rr / 12; }
    var now = pay(r);
    var o = { loan: won(loan), base: won(base), ratio: base ? loan / base : 0, rate: r, years: yrs, pay: won(now), interest1: won(loan * r / 12), totalInterest: buy ? won(now * yrs * 12 - loan) : null,
      incMo: won(inc), debtMo: won(debt), share: inc > 0 ? now / inc : null, shareAll: inc > 0 ? (now + debt) / inc : null, left: inc > 0 ? won(inc - now - debt) : null,
      rates: V(D.rateSteps).map(function (d) { var rr = Math.max(0, r + d), p = pay(rr); return { d: d, rate: rr, pay: won(p), diff: won(p - now), share: inc > 0 ? p / inc : null }; }), caps: null, note: [S(D.rateSteps), S(D.shares)] };
    if (buy && inc > 0 && a.noHome !== false && loan > 0) o.caps = V(D.shares).map(function (sh) {
      var cap = Math.max(0, principal(inc * sh - debt, r, yrs)), a2 = {}, k; for (k in a) a2[k] = a[k]; a2.loanCap = cap;
      var b = affordBuy(L, T, TE, a2);
      return { share: sh, loan: b.loan.amt, price: b.price, pay: b.monthly, ratio: b.price ? b.loan.amt / b.price : 0, tight: b.loan.amt < cap - 1e5 };
    });
    return o;
  }

  /* 해마다 보유세 — 공시가격 = 집값 × 비율(입력 · 기본 0.7 가정) */
  function yearlyHold(T, TE, P, a) {
    if (!P) return { total: 0 };
    var off = P * (a.offRatio || 0.7), one = a.noHome !== false, pr = TE.prop(T, { cat: 'apt', official: off, oneHouse: one, urban: true });
    var jb = TE.jbsHouse ? TE.jbsHouse(T, { officialSum: off, homes: one ? 1 : 2, oneHouse: one, age: a.age || 40, holdYears: 0 }) : null;
    return { prop: pr.total, jbs: jb ? jb.total || 0 : 0, total: pr.total + (jb ? jb.total || 0 : 0) };
  }

  /* 청년 자격 후보 — 셋 */
  function youth(L, a) {
    var Y = L.youth, warn = [], age = a.age || 0, min = W(warn, Y.ageMin), out = [];
    var jn = Y.jeonse, rich = (a.cash || 0) > V(jn.asset), ok1 = age >= min && age <= W(warn, jn.ageMax) && a.noHome && (a.incomeYr || 0) <= W(warn, jn.income) && !rich;
    if (ok1) warn.push('청년 전용 버팀목 순자산 ' + (V(jn.asset) / 1e8) + '억 이하 — 가진 돈만 보고 셈했습니다 · 다른 재산이 있으면 달라집니다(가정) · 만 25세 미만은 단독세대주 한도(낮은 쪽)로 셈');
    out.push({ k: 'jeonse', name: '버팀목 청년 전용 전세대출', ok: !!ok1, why: ok1 ? '나이·소득·무주택 맞음 — 보증금 ' + (W(warn, jn.deposit) / 1e8) + '억 이하 집' : (age < min || age > W(warn, jn.ageMax) ? '나이 범위 밖' : !a.noHome ? '무주택 아님' : rich ? '순자산 기준 넘음(가진 돈만으로)' : '소득 기준 넘음') });
    var ra = Y.rentAid, ok2 = age >= min && age <= W(warn, ra.ageMax) && a.noHome && a.median60 === 'y';
    out.push({ k: 'rentAid', name: '청년월세 지원(월 최대 ' + (W(warn, ra.monthly) / 1e4) + '만 원 · ' + W(warn, ra.months) + '개월)', ok: ok2 ? true : (a.median60 === 'u' && age >= min && age <= W(warn, ra.ageMax) && a.noHome ? null : false), why: ok2 ? '나이·무주택·소득(중위 60% 이하라고 답함) 맞음' : a.median60 === 'u' ? '소득이 중위 60% 이하인지 복지로에서 확인' : (age < min || age > W(warn, ra.ageMax) ? '나이 범위 밖' : !a.noHome ? '무주택 아님' : '소득 기준 밖이라고 답함') });
    W(warn, ra.rule); if (ok2 || out[1].ok === null) out[1].why += ' · 2026 신청기간(3-30~5-29) 끝남 — 다음 정기 신청 대기';
    var pr = Y.publicRent, ok3 = age >= min && age <= W(warn, pr.ageMax) && a.noHome;
    out.push({ k: 'publicRent', name: '청년 공공임대(행복주택·매입임대 등)', ok: ok3 ? null : false, why: ok3 ? '나이·무주택 맞음 — 소득·자산·임대료는 모집 공고(마이홈)에서' : '나이 범위 밖이거나 무주택 아님' });
    W(warn, pr.rule);
    return { list: out, warn: warn };
  }

  /* 전세 — 보증금 얼마까지 */
  function affordJeonse(L, a) {
    var warn = [], B = L.loan, Y = L.youth.jeonse, yo = youth(L, a), yj = yo.list[0].ok;
    function solve(isYouth, cap) {
      var lo = 0, hi = cap, best = null;
      for (var k = 0; k < 60; k++) {
        var D = (lo + hi) / 2, ym = a.age < 25 && a.single !== false ? W(warn, Y.maxU25) : W(warn, Y.max), lim = isYouth ? [['청년 전용 한도', ym], ['보증금의 ' + Math.round(W(warn, Y.ratio) * 100) + '%', D * W(warn, Y.ratio)]] : [['은행 전세 보증 한도', W(warn, B.jeonseCap)], ['보증금의 ' + Math.round(W(warn, B.jeonseGuar) * 100) + '%', D * W(warn, B.jeonseGuar)]];
        var bq = lim.reduce(function (p, q) { return q[1] < p[1] ? q : p; }), br = brokerLease(L, { deposit: D }, warn), need = D - bq[1] + br.fee + (a.moving || 0);
        if (need <= (a.cash || 0)) { lo = D; best = { deposit: won(D), loan: won(bq[1]), why: (isYouth ? '청년 전용 · ' : '') + bq[0], broker: br.fee, need: won(need), youth: isYouth }; } else hi = D;
        if (hi - lo < 1e5) break;
      }
      return best;
    }
    /* 청년 전용은 대상 보증금 상한이 있어 은행 대출과 따로 풀고 큰 쪽을 고른다 */
    var best = solve(false, 3e9), by = yj ? solve(true, W(warn, Y.deposit)) : null;
    if (by && (!best || by.deposit >= best.deposit)) best = by;
    if (!best) best = { deposit: 0, loan: 0, why: '가진 돈이 부족', broker: 0, need: 0, youth: false };
    var r = best.youth ? W(warn, Y.rate) : (a.rateJ || W(warn, B.rateJeonse));
    best.monthly = won(best.loan * r / 12); best.rate = r;
    best.steps = [['보증금(최대)', best.deposit], ['전세대출(' + best.why + ')', best.loan], ['중개보수(상한)', best.broker], ['이사(입력)', a.moving || 0], ['내 돈 쓰는 것', best.need], ['달마다 이자(만기 일시 · 금리 ' + (r * 100).toFixed(1) + '%)', best.monthly]];
    best.warn = warn.concat(['전세대출 소득·DSR 심사 · 1주택자 제한 등은 넣지 않았습니다 — 미확인']);
    return best;
  }

  /* 월세 — 보증금을 정하면 월세 얼마까지 (주거비 30% 기준선) */
  function affordRent(L, a) {
    var warn = [], D = L.design, burden = W(warn, D.rentBurden), inc = (a.incomeYr || 0) / 12;
    var dep = Math.max(0, a.rentDeposit != null ? a.rentDeposit : (a.cash || 0) * 0.5);
    var yo = youth(L, a), aid = yo.list[1].ok ? W(warn, L.youth.rentAid.monthly) : 0;
    var mMax = inc * burden, br = brokerLease(L, { deposit: dep, monthly: mMax }, warn);
    if (dep + br.fee + (a.moving || 0) > (a.cash || 0)) warn.push('넣은 보증금·중개보수·이사비가 가진 돈보다 많습니다 — 모자란 돈을 빌리는 것은 셈하지 않았습니다(가정)');
    return { deposit: won(dep), monthlyMax: won(mMax), aid: aid, broker: br.fee, need: won(dep + br.fee + (a.moving || 0)),
      steps: [['보증금(넣은 값 · 없으면 가진 돈의 절반)', won(dep)], ['월소득 × ' + Math.round(burden * 100) + '%', won(inc * burden)], ['월세 상한(지원은 안 더함)', won(mMax)], ['청년월세 지원(후보면 · 따로 · 올해 신청 끝남)', aid], ['중개보수(상한 · 환산보증금)', br.fee], ['내 돈 쓰는 것', won(dep + br.fee + (a.moving || 0))]], warn: warn };
  }

  /* 출퇴근 — 직선 거리로 근사 · a = {km(직선), mode:'transit'|'car', gtx, red, youthAge} */
  function commute(L, a) {
    var warn = [], D = L.design, F = L.fare, km = (a.km || 0) * W(warn, D.detour), out = {};
    var walk = W(warn, D.walkMin) * 2, wait = W(warn, D.waitMin), ride = km / W(warn, D.transitKmh) * 60;
    out.transitMin = Math.round(walk + wait + ride);
    var fare;
    if (a.gtx) { var g = W(warn, F.gtx); fare = g[0] + (km > g[1] ? Math.ceil((km - g[1]) / g[2]) * g[3] : 0); }
    else if (a.red) fare = a.mbus ? W(warn, F.mbus) : W(warn, F.red);
    else { fare = W(warn, F.subway); W(warn, F.subwayAdd).forEach(function (z) { var from = z[0], to = z[1] == null ? 1e9 : z[1]; if (km > from) fare += Math.ceil((Math.min(km, to) - from) / z[2]) * z[3]; }); }
    var days = W(warn, D.workDays), mo = fare * 2 * days, yth = a.age >= 19 && a.age <= 34;
    var kp = mo * (1 - (yth ? W(warn, F.kpassYouth) : W(warn, F.kpass))), flat = Math.min(mo, a.gtx || a.red ? W(warn, F.flatPlus) : yth ? W(warn, F.flatYouth) : W(warn, F.flat));
    var best = Math.min(mo, 2 * days >= W(warn, F.minTrips) ? Math.min(kp, flat) : mo);
    out.fare = fare; out.transitMo = won(best); out.transitRaw = won(mo); out.kpass = won(kp); out.flat = won(flat);
    out.carMin = Math.round(km / W(warn, D.carKmh) * 60); out.roadKm = Math.round(km * 10) / 10; out.days = days;
    out.warn = warn.concat(['출퇴근 시간은 직선 거리로 낸 근사입니다 — 실제 길찾기와 다를 수 있습니다(설계값)']);
    return out;
  }

  /* 자동차 — a = {buy:'none'|'new'|'used', price, cc, ev(bool), light(bool), age(차령 년), kmMo, kmL(연비 km/L 또는 km/kWh), unit(원/L), ins(연 보험), park(월 주차), bond(채권 할인 비용 입력)} */
  function car(L, a) {
    var warn = [], C = L.car, st = [], first = 0;
    if (a.buy === 'new' || a.buy === 'used') {
      var base = a.price || 0, r = a.light ? W(warn, C.acqLight) : W(warn, C.acq), t = base * r;
      if (a.light) t = Math.max(0, t - W(warn, C.lightRelief)); else if (a.ev) t = Math.max(0, t - W(warn, C.evRelief));
      if (a.buy === 'used') warn.push('중고차 취득세 과세표준 = 실거래가와 시가표준액 중 큰 값 — 시가표준액은 위택스에서(미확인)');
      first = base + t + (a.bond || 0);
      st.push(['차값', won(base)], ['취득세(' + (r * 100).toFixed(0) + '%' + (a.light ? ' · 경차 감면' : a.ev ? ' · 전기차 감면' : '') + ')', won(t)], ['채권 할인 비용(입력)', a.bond || 0]);
      W(warn, C.bondNote);
    }
    var tax = 0;
    if (a.buy !== 'none' || a.have) {
      if (a.ev) tax = W(warn, C.evTax);
      else { var tb = W(warn, C.taxPerCc), cc = a.cc || 0, row = tb.filter(function (x) { return x[0] === null || cc <= x[0]; })[0]; tax = cc * row[1]; }
      var ar = W(warn, C.ageRelief), yrs = a.buy === 'new' ? 1 : (a.age || 1);
      if (!a.ev && yrs >= ar[1]) tax *= 1 - Math.min(ar[2], (yrs - ar[1] + 1) * ar[0]);
      if (!a.ev && !(a.cc > 0)) warn.push('배기량을 넣지 않아 자동차세를 0원으로 셈했습니다(가정)');
      tax *= 1 + W(warn, C.eduTax);
      st.push(['자동차세+지방교육세(해마다)', won(tax)]);
    }
    var fuel = a.kmL ? (a.kmMo || 0) / a.kmL * (a.unit || 0) : 0, mo = fuel + (a.park || 0) + (a.ins || 0) / 12;
    st.push(['기름·충전(달 · 입력으로 셈)', won(fuel)], ['주차(달 · 입력)', a.park || 0], ['보험(해 · 입력)', a.ins || 0]);
    return { first: won(first), yearly: won(tax), monthly: won(mo), steps: st, warn: warn };
  }

  /* 한 장으로 — 처음 / 매달 / 해마다 */
  function sheet(L, T, TE, a) {
    var out = { mode: a.mode, warn: [] }, h;
    if (a.mode === 'buy') { h = affordBuy(L, T, TE, a); out.house = h; out.first = h.need; out.monthly = h.monthly; out.yearly = h.yearly.total; out.burden = burden(L, T, TE, a, h, 'buy'); }
    else if (a.mode === 'jeonse') { h = affordJeonse(L, a); out.house = h; out.first = h.need; out.monthly = h.monthly; out.yearly = 0; out.burden = burden(L, T, TE, a, h, 'jeonse'); }
    else { h = affordRent(L, a); out.house = h; out.first = h.need; out.monthly = h.monthlyMax; out.yearly = 0; }
    out.warn = out.warn.concat(h.warn || []);
    out.youth = youth(L, a); out.warn = out.warn.concat(out.youth.warn);
    if (a.km) { out.commute = commute(L, a); out.warn = out.warn.concat(out.commute.warn); if (a.commuteMode !== 'car') out.monthly += out.commute.transitMo; }
    if (a.car && a.car.buy !== 'none') { out.car = car(L, a.car); out.first += out.car.first; out.monthly += out.car.monthly; out.yearly += out.car.yearly; out.warn = out.warn.concat(out.car.warn); }
    if (a.mgmt) out.monthly += a.mgmt;
    out.first = won(out.first); out.monthly = won(out.monthly); out.yearly = won(out.yearly);
    out.warn = out.warn.filter(function (w, i, arr) { return arr.indexOf(w) === i; });
    return out;
  }

  root.LiveEngine = { pmt: pmt, principal: principal, brokerLease: brokerLease, buyCosts: buyCosts, loanBuy: loanBuy, didim: didim, affordBuy: affordBuy, burden: burden, affordJeonse: affordJeonse, affordRent: affordRent, youth: youth, commute: commute, car: car, sheet: sheet };
  if (typeof module !== 'undefined') module.exports = root.LiveEngine;
})(typeof window !== 'undefined' ? window : this);
