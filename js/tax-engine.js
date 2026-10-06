// tax-engine.js — 부동산 세금 시뮬레이터 계산부 v0 (2026-10-06 Cowork)
// 규칙은 tax-rules.json 에서만 읽는다(숫자 하드코딩 금지). 개인 입력은 이 함수 안에서만 쓰고 저장·전송하지 않는다.
// 결과마다 steps(계산 과정)와 warn(미확인·미구현 경고)을 돌려준다 — 화면은 이것을 그대로 펼친다.
(function (root) {
  'use strict';
  function prog(base, br) {            // 누진세: br = [[상한, 세율]…], 마지막 상한 null
    var tax = 0, lo = 0;
    for (var i = 0; i < br.length; i++) {
      var hi = br[i][0], r = br[i][1];
      if (hi === null || base <= hi) { tax += (base - lo) * r; return Math.max(0, tax); }
      tax += (hi - lo) * r; lo = hi;
    }
    return tax;
  }
  function step(tbl, n) { var v = 0; tbl.forEach(function (t) { if (n >= t[0]) v = t[1]; }); return v; }
  function W(R, keypath) { var v = keypath.split('.').reduce(function (o, k) { return o && o[k]; }, R); var s = Array.isArray(v) ? v[1] : (v && v._); return s && /미확인|미구현/.test(s) ? s : null; }
  var won = function (x) { return Math.round(x); };

  // ---------- 양도소득세 ----------
  // a = {kind:'house'|'land'|'nonbizLand'|'building', sell, buy, expense, holdYears, liveYears, oneHouseExempt(bool), surcharge:0|'two'|'three'}
  function cgt(R, a) {
    var C = R.cgt, st = [], warn = [];
    var gain = a.sell - a.buy - (a.expense || 0); st.push(['양도차익', gain, '양도가 − 취득가 − 필요경비']);
    if (gain <= 0) return { tax: 0, steps: st, warn: warn };
    var isHouse = a.kind === 'house';
    if (isHouse && a.oneHouseExempt) {
      warn.push(C.oneHouseExemptRule[0]);
      if (a.sell <= C.highPriceHouse[0]) { st.push(['1세대1주택 비과세', 0, C.highPriceHouse[1] + ' 이하']); return { tax: 0, steps: st, warn: warn }; }
      gain = gain * (a.sell - C.highPriceHouse[0]) / a.sell; st.push(['고가주택 과세 양도차익', won(gain), C.highPriceGainFormula[0]]); warn.push(C.highPriceGainFormula[1]);
    }
    var lt = 0;
    if (a.holdYears >= 3 && !(a.holdYears < 2)) {
      if (isHouse && a.oneHouseExempt && a.liveYears >= 2) {
        var r2 = step(C.ltsdTable2Hold[0], a.holdYears) + step(C.ltsdTable2Live[0], a.liveYears);
        lt = gain * r2; st.push(['장기보유특별공제(표2)', won(lt), (r2 * 100).toFixed(0) + '% · ' + C.ltsdTable2Hold[1]]);
      } else if (!(a.surcharge)) {
        var r1 = step(C.ltsdTable1[0], a.holdYears); lt = gain * r1; st.push(['장기보유특별공제(표1)', won(lt), (r1 * 100).toFixed(0) + '% · ' + C.ltsdTable1[1]]);
      } else st.push(['장기보유특별공제', 0, '중과 대상은 배제(가정)']);
    }
    var income = gain - lt, base = Math.max(0, income - C.basicDeduction[0]);
    st.push(['양도소득금액', won(income)], ['기본공제', C.basicDeduction[0], C.basicDeduction[1]], ['과세표준', won(base)]);
    var brk = a.kind === 'nonbizLand' ? R.brackets.nonbizLand[0] : R.brackets.basic[0];
    var tax = prog(base, brk), how = a.kind === 'nonbizLand' ? '비사업용 토지 세율' : '기본세율';
    if (a.surcharge) {
      var add = a.surcharge === 'three' ? C.surcharge.threeHomes : C.surcharge.twoHomes;
      tax = prog(base, R.brackets.basic[0].map(function (b) { return [b[0], b[1] + add]; })); how = '기본세율 + ' + add * 100 + '%p 중과'; warn.push(C.surcharge._);
    }
    if (a.holdYears < 2) {
      var sr = C.shortTerm[a.holdYears < 1 ? 'under1y' : '1to2y'][isHouse ? 1 : 0], t2 = base * sr;
      if (t2 > tax) { tax = t2; how = '단기보유 ' + sr * 100 + '%'; }
    }
    st.push(['산출세액', won(tax), how]);
    var local = tax * C.localIncomeTaxRate[0]; warn.push(C.localIncomeTaxRate[1]);
    st.push(['지방소득세', won(local)], ['합계', won(tax + local)]);
    return { tax: won(tax), local: won(local), total: won(tax + local), steps: st, warn: warn };
  }

  // ---------- 종합부동산세(주택) ----------
  // a = {officialSum, homes, oneHouse(bool), age, holdYears, corporate(bool)}
  function jbsHouse(R, a) {
    var J = R.jbs, st = [], warn = [J.propertyTaxCredit[0], J.burdenCap[0]];
    var ded = a.corporate ? J.houseDeduction.corporate : (a.oneHouse ? J.houseDeduction.oneHouse : J.houseDeduction.general);
    var base = Math.max(0, (a.officialSum - ded) * J.houseFMVRatio[0]);
    st.push(['공시가격 합계', a.officialSum], ['공제', ded, J.houseDeduction._], ['공정시장가액비율', J.houseFMVRatio[0], J.houseFMVRatio[1]], ['과세표준', won(base)]);
    var tax;
    if (a.corporate) tax = base * (a.homes >= 3 ? J.corpRate.ge3 : J.corpRate.le2);
    else tax = prog(base, (a.homes >= 3 ? R.brackets.jbsHouse3 : R.brackets.jbsHouse2)[0]);
    st.push(['산출세액(재산세 공제 전)', won(tax), a.homes >= 3 ? '3주택 이상 세율' : '2주택 이하 세율']);
    if (a.oneHouse && !a.corporate) {
      var cr = Math.min(J.creditCap[0], step(J.seniorCredit[0], a.age || 0) + step(J.holdCredit[0], a.holdYears || 0));
      if (cr > 0) { st.push(['고령·장기보유 세액공제', won(tax * cr), (cr * 100).toFixed(0) + '% (합계 한도 80%)']); tax = tax * (1 - cr); }
    }
    var rural = tax * J.ruralSpecialTax[0]; warn.push(J.ruralSpecialTax[1]);
    st.push(['종부세', won(tax)], ['농어촌특별세', won(rural)], ['합계(재산세 공제·세부담상한 전)', won(tax + rural)]);
    return { tax: won(tax), rural: won(rural), total: won(tax + rural), steps: st, warn: warn };
  }
  // ---------- 종합부동산세(토지) ----------  a = {aggregateSum, separateSum}
  function jbsLand(R, a) {
    var J = R.jbs, st = [], out = 0;
    var b1 = Math.max(0, ((a.aggregateSum || 0) - J.landDeduction.aggregate) * J.landFMVRatio[0]);
    var b2 = Math.max(0, ((a.separateSum || 0) - J.landDeduction.separate) * J.landFMVRatio[0]);
    var t1 = prog(b1, R.brackets.jbsLandAgg[0]), t2 = prog(b2, R.brackets.jbsLandSep[0]);
    st.push(['종합합산 과세표준', won(b1), '공제 5억 · 비율 100%'], ['종합합산 세액', won(t1)], ['별도합산 과세표준', won(b2), '공제 80억'], ['별도합산 세액', won(t2)]);
    out = t1 + t2; var rural = out * J.ruralSpecialTax[0];
    st.push(['농어촌특별세', won(rural)], ['합계(재산세 공제 전)', won(out + rural)]);
    return { total: won(out + rural), steps: st, warn: [J.propertyTaxCredit[0], J.ruralSpecialTax[1]] };
  }
  // ---------- 증여세 ----------  a = {value, relation:'spouse'|'lineal_ascendant'|..., priorGift10y, priorDeductUsed}
  function gift(R, a) {
    var G = R.inheritGift, st = [];
    var lim = G.giftDeduction[a.relation] || 0, ded = Math.max(0, lim - (a.priorDeductUsed || 0));
    var taxable = a.value + (a.priorGift10y || 0), base = Math.max(0, taxable - Math.min(ded, taxable));
    st.push(['증여재산가액', a.value], ['10년 내 같은 사람 증여 합산', a.priorGift10y || 0], ['증여재산공제', Math.min(ded, taxable), G.giftDeduction._], ['과세표준', won(base)]);
    var t = prog(base, R.brackets.inheritGift[0]); st.push(['산출세액', won(t)]);
    var fc = t * G.filingCredit[0]; st.push(['신고세액공제', won(fc), G.filingCredit[1]], ['납부세액(기납부 증여세 공제 전)', won(t - fc)]);
    return { total: won(t - fc), steps: st, warn: a.priorGift10y ? ['10년 합산 시 이미 낸 증여세는 빼야 한다(미구현)'] : [] };
  }
  // ---------- 상속세(단순) ----------  a = {estate, debts, spouseShare, spouseAlive}
  function inherit(R, a) {
    var G = R.inheritGift, st = [];
    var net = a.estate - (a.debts || 0), lump = G.inheritLumpSum[0];
    var sp = a.spouseAlive ? Math.min(G.spouseMax[0], Math.max(G.spouseMin[0], a.spouseShare || 0)) : 0;
    var base = Math.max(0, net - lump - sp);
    st.push(['상속재산 − 채무', won(net)], ['일괄공제', lump, G.inheritLumpSum[1]], ['배우자 상속공제', won(sp), '최소 5억 · 한도 30억(법정상속분 한도식 미구현)'], ['과세표준', won(base)]);
    var t = prog(base, R.brackets.inheritGift[0]), fc = t * G.filingCredit[0];
    st.push(['산출세액', won(t)], ['신고세액공제', won(fc)], ['납부세액', won(t - fc)]);
    return { total: won(t - fc), steps: st, warn: ['금융재산공제·동거주택공제·가업공제 등 미구현 · 배우자 공제 한도식 미구현'] };
  }
  // ---------- v2.41.0 지방세·중개보수(데이터 압축지도 세무 파트) — 규칙 = R.acq · R.prop · R.broker(지방세법·시행령·농특세법·공인중개사법 시행규칙 원문 2026-10-06) ----------
  var HOUSE = { apt: 1, house: 1 };
  // 취득세  a = {cat, cause:'buy'|'gift'|'inherit'|'new', price, official, homesAfter, adj, temp2, corp, area, giftFamily, inheritOne}
  function acq(R, a) {
    var A = R.acq, Q = A.rates, st = [], warn = [], p = a.price || 0, isH = !!HOUSE[a.cat], sb = A.surBase[0], r, edu, rural, mult = 0, how;
    var small = isH && a.area && a.area <= A.smallHouseM2;
    if (a.cause === 'buy') {
      if (isH) {
        if (a.corp) mult = A.multi.corp;
        else if (a.adj) mult = a.homesAfter >= 3 ? A.multi.threeAdj : (a.homesAfter === 2 && !a.temp2 ? A.multi.twoAdj : 0);
        else mult = a.homesAfter >= 4 ? A.multi.fourNon : (a.homesAfter === 3 ? A.multi.threeNon : 0);
        if (mult) { r = Q.other[0] + sb * mult; how = '중과 ' + (r * 100).toFixed(0) + '% · ' + A.multi._.split(' — ')[0]; edu = (Q.other[0] - sb) * 0.2; rural = (sb + sb * mult) * 0.1; }
        else { r = p <= 6e8 ? Q.houseLow[0] : p > 9e8 ? Q.houseHigh[0] : Math.round((p * 2 / 3e8 - 3) / 100 * 1e6) / 1e6; how = '유상 주택 ' + (r * 100).toFixed(2) + '% · ' + (p > 6e8 && p <= 9e8 ? Q.houseMidFormula[1] : p <= 6e8 ? Q.houseLow[1] : Q.houseHigh[1]); edu = r * 0.5 * 0.2; rural = sb * 0.1; }
      } else if (a.cat === 'farm') { r = Q.farm[0]; how = Q.farm[1]; edu = (r - sb) * 0.2; rural = sb * 0.1; }
      else { r = Q.other[0]; how = Q.other[1]; edu = (r - sb) * 0.2; rural = sb * 0.1; }
    } else if (a.cause === 'gift') {
      r = Q.gift[0]; how = Q.gift[1]; edu = (r - sb) * 0.2; rural = sb * 0.1;
      if (isH && a.adj && (a.official || 0) >= A.giftSur.min && !a.giftFamily) { r = Q.other[0] + sb * A.giftSur.mult; how = '증여 중과 12% · ' + A.giftSur._.split(' — ')[0]; edu = (Q.other[0] - sb) * 0.2; rural = (sb + sb * A.giftSur.mult) * 0.1; }
    } else if (a.cause === 'inherit') {
      r = a.cat === 'farm' ? Q.inheritFarm[0] : Q.inherit[0]; how = a.cat === 'farm' ? Q.inheritFarm[1] : Q.inherit[1]; edu = (r - sb) * 0.2; rural = sb * 0.1;
      if (isH && a.inheritOne) { r = r - sb; how = A.inheritOneHouse[0] + ' · ' + A.inheritOneHouse[1]; rural = 0; warn.push('상속 1가구 1주택 특례의 농어촌특별세는 0 으로 근사(표준세율 2% 를 빼고 셈) — 확인 필요'); }
    } else { r = Q.newBuild[0]; how = Q.newBuild[1]; edu = (r - sb) * 0.2; rural = sb * 0.1; }
    if (small) { rural = 0; }
    var t1 = p * r, t2 = p * Math.max(0, edu), t3 = p * rural;
    st.push(['과세표준(취득가액·시가인정액·시가표준액)', won(p), a.cause === 'inherit' ? '상속 = 시가표준액(공시가격)' : a.cause === 'gift' ? '증여 = 시가인정액(매매사례 등) — 없으면 시가표준액' : '사실상 취득가격'], ['취득세율', r, how], ['취득세', won(t1)], ['지방교육세', won(t2), A.eduTax[1]], ['농어촌특별세', won(t3), small ? '국민주택규모(85㎡) 이하 주택 — 비과세' : A.ruralTax[1]], ['합계', won(t1 + t2 + t3)]);
    if (isH && a.cause === 'buy' && !a.corp) warn.push('주택 수·조정대상지역·일시적 2주택은 내가 고른 값이다(지방세법 시행령 제28조의2~5 산정 방법 — 분양권·입주권·주거용 오피스텔도 셀 수 있음)');
    if (a.cat === 'farm') warn.push('자경 농민 농지 감면(지방세특례제한법 제6조)은 넣지 않았다');
    return { total: won(t1 + t2 + t3), acq: won(t1), edu: won(t2), rural: won(t3), rate: r, steps: st, warn: warn };
  }
  // 재산세(한 해)  a = {cat, official, bldg, landVal, oneHouse, urban}
  function prop(R, a) {
    var Pp = R.prop, st = [], t = 0, base = 0, tb = [];
    if (HOUSE[a.cat] || a.cat === 'offiH') {
      var fv = a.oneHouse ? step(Pp.fmv.oneHouse, a.official || 0) : Pp.fmv.house; base = (a.official || 0) * fv;
      var one = a.oneHouse && (a.official || 0) <= Pp.houseOneCap; t = prog(base, (one ? Pp.houseOne : Pp.house)[0]);
      st.push(['주택 시가표준액(공시가격)', won(a.official || 0)], ['공정시장가액비율', fv, Pp.fmv._], ['과세표준', won(base)], ['재산세', won(t), one ? Pp.houseOne[1] : Pp.house[1]]);
      tb.push(base);
    } else if (a.cat === 'landAgg') { base = (a.official || 0) * Pp.fmv.land; t = prog(base, Pp.landAgg[0]); st.push(['토지 공시가격', won(a.official || 0)], ['공정시장가액비율', Pp.fmv.land], ['과세표준', won(base)], ['재산세(종합합산)', won(t), Pp.landAgg[1]]); tb.push(base); }
    else if (a.cat === 'farm' || a.cat === 'forest') { base = (a.official || 0) * Pp.fmv.land; t = base * Pp.landFarm[0]; st.push(['토지 공시가격', won(a.official || 0)], ['과세표준', won(base)], ['재산세(분리과세 0.07%)', won(t), Pp.landFarm[1]]); tb.push(base); }
    else {
      var b1 = (a.bldg || 0) * Pp.fmv.land, t1 = b1 * Pp.building[0], b2 = (a.landVal || 0) * Pp.fmv.land, t2 = prog(b2, Pp.landSep[0]); t = t1 + t2; base = b1 + b2;
      st.push(['건물 시가표준액', won(a.bldg || 0), '국세청·지자체 건물 시가표준액(직접)'], ['건물 재산세 0.25%', won(t1), Pp.building[1]], ['부속토지 공시가격', won(a.landVal || 0)], ['부속토지 재산세(별도합산)', won(t2), Pp.landSep[1]]); tb.push(b1, b2);
    }
    var u = a.urban ? base * Pp.urban[0] : 0, e = t * Pp.eduTax[0];
    st.push(['도시지역분', won(u), a.urban ? Pp.urban[1] : '안 넣음'], ['지방교육세', won(e), Pp.eduTax[1]], ['합계(한 해)', won(t + u + e)]);
    return { total: won(t + u + e), steps: st, warn: [Pp.capNote] };
  }
  // 중개보수(한쪽)  a = {cat, price, offiOk}
  function broker(R, a) {
    var B = R.broker, p = a.price || 0, r, cap = null, how;
    if (HOUSE[a.cat]) { var row = B.houseSale[0].filter(function (x) { return x[0] === null || p < x[0]; })[0]; r = row[1]; cap = row[2]; how = B.houseSale[1]; }
    else if (a.cat === 'offiH' && a.offiOk) { r = B.offi[0]; how = B.offi[1]; }
    else { r = B.other[0]; how = B.other[1]; }
    var fee = p * r; if (cap != null) fee = Math.min(fee, cap);
    return { total: won(fee), steps: [['거래금액', won(p)], ['상한요율', r, how + (cap ? ' · 한도 ' + cap.toLocaleString() + '원' : '')], ['중개보수 상한(한쪽)', won(fee)]], warn: [B._] };
  }
  // 등기 부대비용 — 인지세 · 제1종 국민주택채권  a = {cat, price(계약서 기재금액), official(시가표준액), bldg, landVal, metro, disc(즉시매도 할인율 %)}
  function reg(R, a) {
    var G = R.reg, st = [], warn = [], isH = !!HOUSE[a.cat], p = a.price || 0, stamp = 0;
    if (!(isH && p <= G.stampHouseFree)) { var row = G.stamp[0].filter(function (x) { return x[0] === null || p <= x[0]; })[0]; stamp = row[1]; }
    st.push(['인지세(계약서 1부)', stamp, G.stamp[1]]);
    function bond(tbl, v) { var r = tbl.filter(function (x) { return x[0] === null || v < x[0]; })[0]; var rt = a.metro ? r[1] : r[2], b = Math.round(v * rt / 1e4) * 1e4; return [b, rt]; }
    var parts = [];
    if (isH) parts.push(['주택', a.official || 0, G.bond.house]);
    else if (a.cat === 'shop' || a.cat === 'offiB' || a.cat === 'offiH') { if (a.landVal) parts.push(['토지', a.landVal, G.bond.land]); parts.push(['건물', a.cat === 'shop' ? (a.bldg || 0) : (a.official || 0), G.bond.other]); }
    else parts.push(['토지', a.official || 0, G.bond.land]);
    var bt = 0; parts.forEach(function (q) { var b = bond(q[2], q[1]); bt += b[0]; st.push(['국민주택채권 매입액(' + q[0] + ' 시가표준액 ' + won(q[1]).toLocaleString() + '원 × ' + (b[1] * 1000).toFixed(0) + '/1,000)', b[0], G.bond._.split(' — ')[0] + (a.metro ? ' · 특별시·광역시' : ' · 그 밖 지역')]); });
    var dc = a.disc ? bt * a.disc / 100 : 0; st.push(['채권 즉시매도 비용(할인율 ' + (a.disc || 0) + '%)', won(dc), a.disc ? '입력한 할인율' : '할인율을 넣으면 셈 — 그날 은행 고지 할인율']);
    if (!a.official) warn.push('국민주택채권은 시가표준액(공시가격)으로 매긴다 — 공시가격이 없어 0으로 셈');
    if (a.cat === 'farm') warn.push('영농 목적 농지 취득은 국민주택채권 매입 면제(별표 3호 마목)');
    return { stamp: stamp, bond: bt, bondCost: won(dc), total: won(stamp + dc), steps: st, warn: warn.concat(['인지세는 계약서마다 — 매수·매도인이 나눠 내는 것이 보통(인지세법 제1조 공동작성 연대)', '법무사 보수·등기 신청 수수료는 넣지 않았다']) };
  }
  root.TaxEngine = { prog: prog, cgt: cgt, jbsHouse: jbsHouse, jbsLand: jbsLand, gift: gift, inherit: inherit, acq: acq, prop: prop, broker: broker, reg: reg };
  if (typeof module !== 'undefined') module.exports = root.TaxEngine;
})(typeof window !== 'undefined' ? window : globalThis);
