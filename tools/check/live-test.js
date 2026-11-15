/* 🏡 여기 살면 계산 시험 — node tools/check/live-test.js
   손계산 값과 맞댄다(규칙 값이 바뀌면 기대값도 같이 고친다) · 세금 계산(tax-engine) 기존 결과가 그대로인지도 본다 */
'use strict';
var path = require('path'), fs = require('fs'), root = path.join(__dirname, '..', '..');
var L = JSON.parse(fs.readFileSync(path.join(root, 'data/live-rules.json'), 'utf8'));
var T = JSON.parse(fs.readFileSync(path.join(root, 'data/tax-rules.json'), 'utf8'));
var TE = require(path.join(root, 'js/tax-engine.js')), E = require(path.join(root, 'js/live-engine.js'));
var ok = 0, bad = 0;
function eq(name, got, want, tol) { var g = Math.abs(got - want) <= (tol || 0); if (g) ok++; else bad++; console.log((g ? 'ok  ' : 'BAD ') + name + ' = ' + got + (g ? '' : ' (기대 ' + want + ')')); }
function tr(name, c) { if (c) ok++; else bad++; console.log((c ? 'ok  ' : 'BAD ') + name); }

/* 1. 원리금 균등 — 1억 · 연 4.2% · 30년 → 손계산 489,016원(엑셀 PMT 와 같음) */
eq('pmt 1억 4.2% 30년', Math.round(E.pmt(1e8, 0.042, 30)), 489016, 1);
eq('principal 역산', Math.round(E.principal(489016, 0.042, 30) / 1e4), 1e4, 1);

/* 2. 임대차 중개보수 — 전세 3억: 3억 × 0.3% = 90만 · 월세 1천/50만: 환산 6천 × 0.4% = 24만(한도 30만) · 500/40: 4,500 → ×70 = 3,300 × 0.5% = 16.5만 */
eq('전세 3억 중개', E.brokerLease(L, { deposit: 3e8 }, []).fee, 900000);
eq('월세 1천/50 중개', E.brokerLease(L, { deposit: 1e7, monthly: 5e5 }, []).fee, 240000);
eq('월세 500/40 중개(×70)', E.brokerLease(L, { deposit: 5e6, monthly: 4e5 }, []).fee, 165000);
eq('전세 4천 중개(한도 20만 안)', E.brokerLease(L, { deposit: 4e7 }, []).fee, 200000);

/* 3. 매매 — 가진 돈 3억 · 연소득 8천 · 서울(규제·수도권) · 무주택 · 생애최초 아님 */
var a = { cash: 3e8, incomeYr: 8e7, debtMo: 0, adj: true, first: false, metro: true, noHome: true, age: 40 };
var b = E.affordBuy(L, T, TE, a);
tr('매매 최대값이 나온다 (' + b.price + '원 · ' + b.loan.why + ')', b.price > 3e8 && b.price < 2e9);
tr('내 돈 쓰는 것 ≤ 가진 돈', b.need <= a.cash);
tr('규제지역 무주택 LTV 40% 를 넘지 않는다', b.loan.amt <= b.price * 0.4 + 1);
var c = E.buyCosts(T, TE, a, b.price); tr('부대비용 = 취득세+중개+등기 합', c.total === c.acq + c.broker + c.reg + c.legal + c.moving);
var tight = E.affordBuy(L, T, TE, { cash: 3e8, incomeYr: 3e7, adj: true, metro: true, noHome: true });
tr('소득이 낮으면 DSR 이 묶는다 (' + tight.loan.why + ')', /DSR/.test(tight.loan.why));

/* 4. 전세 — 가진 돈 1억 · 28세 · 소득 4천 · 무주택
      청년 전용(한도 1.5억 · A 2026-11-16): D − 1.5억 + 0.3%D ≤ 1억 → 2.49억 / 은행(보증 한도 2억): D − 2억 + 0.3%D ≤ 1억 → 2.991억 → 은행 쪽이 큼 (이분법 허용 10만 원) */
var j = E.affordJeonse(L, { cash: 1e8, incomeYr: 4e7, age: 28, noHome: true });
eq('전세 최대(만 원) — 은행 보증 한도 2억이 묶음: D − 2억 + 0.3%D ≤ 1억', Math.round(j.deposit / 1e4), Math.round(3e8 / 1.003 / 1e4), 12);
tr('청년 한도 1.5억 < 은행 2억 → 보증금이 더 큰 은행 쪽', j.youth === false);
var j2 = E.affordJeonse(L, { cash: 1e8, incomeYr: 4e7, age: 40, noHome: true });
eq('40세 은행 전세 최대(만 원) — D − 2억 + 0.3%D ≤ 1억', Math.round(j2.deposit / 1e4), Math.round(3e8 / 1.003 / 1e4), 12);
var dd = E.affordBuy(L, T, TE, { cash: 1.5e8, incomeYr: 5e7, adj: true, metro: true, noHome: true, didim: true, first: true, age: 33 });
tr('디딤돌을 켜면 은행만보다 작지 않다', dd.price >= E.affordBuy(L, T, TE, { cash: 1.5e8, incomeYr: 5e7, adj: true, metro: true, noHome: true, first: true, age: 33 }).price);
tr('디딤돌 집값 상한 5억 안', !/디딤돌/.test(dd.loan.why) || dd.price <= 5e8);
tr('전세 내 돈 ≤ 1억', j.need <= 1e8);

/* 4-1. 수도권·규제 주담대 한도 구간(B) — 시가 20억 → 4억 · 10억 → 6억 */
var hi = E.loanBuy(L, { incomeYr: 1e9, adj: true, metro: true }, 2e9, []); eq('20억 집 한도 4억', hi.amt, 4e8);
var mid = E.loanBuy(L, { incomeYr: 1e9, adj: true, metro: true }, 1e9, []); eq('10억 집 = LTV 40% 4억 < 6억', mid.amt, 4e8);
/* 4-2. GTX — 직선 20km → 길 26km → 3,200 + ⌈16/5⌉×250 = 4,200 · 정액은 플러스형 10만 */
var gx = E.commute(L, { km: 20, gtx: true, age: 40 }); eq('GTX 26km 요금', gx.fare, 4200); eq('GTX 정액 플러스형 한도', gx.flat, 100000);
/* 5. 청년 자격 */
var y = E.youth(L, { age: 28, noHome: true, incomeYr: 4e7, median60: 'y' });
tr('28세 버팀목 청년 후보', y.list[0].ok === true); tr('28세 청년월세 후보', y.list[1].ok === true); tr('공공임대 = 공고 확인(null)', y.list[2].ok === null);
var y2 = E.youth(L, { age: 36, noHome: true, incomeYr: 4e7, median60: 'y' });
tr('36세 버팀목 청년 아님', y2.list[0].ok === false); tr('36세 행복주택 청년은 후보(39세까지)', y2.list[2].ok === null);

/* 6. 출퇴근 — 직선 10km → 길 13km · 지하철 1,550 + (13−10)/5 올림 1 × 100 = 1,650 · 왕복 21일 = 69,300 · K-패스 20% = 55,440 · 정액 62,000 → 55,440 */
var m = E.commute(L, { km: 10, age: 40 });
eq('요금 13km', m.fare, 1650); eq('월 교통비(K-패스)', m.transitMo, 55440); eq('대중교통 분', m.transitMin, Math.round(16 + 5 + 13 / 28 * 60));

/* 7. 자동차 — 신차 3천만 · 1,999cc → 취득세 210만 · 자동차세 1,999 × 200 × 1.3 = 519,740 */
var k = E.car(L, { buy: 'new', price: 3e7, cc: 1999, kmMo: 1000, kmL: 12, unit: 1700, ins: 1200000, park: 100000 });
eq('신차 처음', k.first, 3e7 + 2100000); eq('자동차세 해', k.yearly, 519740);
eq('달 유지(자동차세는 해마다에만 — 달에 또 넣지 않는다)', k.monthly, Math.round(1000 / 12 * 1700 + 100000 + 100000));

/* 7-1. 독립 검수(2026-11-16) 지적 — 손계산
   집 있음 → 추가 주택 대출 0 · 수도권 비규제도 시가 구간 한도(12억 집 → 6억) · 디딤돌 생애최초 수도권 LTV 70%(3억 집 → 2.1억: 한도 2.4억·DSR 여력보다 작다)
   월세 상한 = 연 3,600만 ÷ 12 × 30% = 90만(청년월세 지원 20만은 더하지 않는다) · 전기차 5년차 자동차세 = 10만 × 1.3 = 13만(차령 경감 없음) */
tr('집 있음 → 대출 0', E.affordBuy(L, T, TE, { cash: 3e8, incomeYr: 8e7, adj: true, metro: true, noHome: false, age: 45 }).loan.amt === 0);
tr('수도권 비규제 12억 집 → 6억 넘지 않음', E.loanBuy(L, { incomeYr: 3e8, adj: false, metro: true, noHome: true }, 12e8, []).amt <= 6e8);
eq('디딤돌 생애최초 수도권 3억 집', E.didim(L, { noHome: true, first: true, incomeYr: 6e7, metro: true, cash: 1e8 }, 3e8, []).amt, 2.1e8);
eq('월세 상한(지원 안 더함)', E.affordRent(L, { cash: 2e7, incomeYr: 3.6e7, age: 25, noHome: true, median60: 'y' }).monthlyMax, 900000);
eq('전기차 5년차 자동차세', E.car(L, { buy: 'used', price: 1e7, ev: true, age: 5 }).yearly, 130000);
var ev = E.car(L, { buy: 'new', price: 5e7, ev: true }); eq('전기차 취득세 감면', ev.first, 5e7 + 3500000 - 1400000);

/* 8. 한 장 */
var s = E.sheet(L, T, TE, { mode: 'jeonse', cash: 1e8, incomeYr: 4e7, age: 28, noHome: true, km: 10, car: { buy: 'none' } });
tr('한 장 매달 = 이자 + 교통비', s.monthly === s.house.monthly + s.commute.transitMo);
tr('미확인 경고가 붙는다', s.warn.some(function (w) { return /미확인/.test(w); }));

/* 9. 기존 세금 계산 그대로 — 6억 아파트 1주택 취득세 1% + 교육세 0.1% = 660만(85㎡ 이하 농특세 없음) */
eq('기존 취득세 6억', TE.acq(T, { cat: 'apt', cause: 'buy', price: 6e8, homesAfter: 1, area: 84 }).total, 6600000);

console.log('\n' + ok + ' 통과 · ' + bad + ' 실패'); process.exit(bad ? 1 : 0);
