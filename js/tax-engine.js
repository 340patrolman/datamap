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
  root.TaxEngine = { prog: prog, cgt: cgt, jbsHouse: jbsHouse, jbsLand: jbsLand, gift: gift, inherit: inherit };
  if (typeof module !== 'undefined') module.exports = root.TaxEngine;
})(typeof window !== 'undefined' ? window : globalThis);
