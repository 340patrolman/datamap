/* 주행시간 계산 — 데이터 압축지도(js/map2d.js)와 네비 가르고(gargo/gargo.js)가 같은 이 파일 하나를 읽는다(작업지시서 v1.0 · 2026-10-15)
   의존성 0 · ES5 · 통신 0(이 파일은 어디에도 보내지 않는다 · 저장은 이 기기 localStorage 의 설정값과 보정 비율 숫자뿐 — 경로·지점·시각은 저장하지 않는다)
   쓰기:
     TT.cfg()                       설정값(기본값 + 이 기기에서 바꾼 값)
     TT.set(k, v) · TT.reset(k?)    한 항목 바꾸기 · 항목 또는 전체 기본값으로
     TT.run(segs, opt)              구간 목록 → 총 시간 · 체크포인트별 통과 예정
       segs = [{ m: 거리(m), v: 그 구간 속도(km/h · 없으면 opt.v), turn: 꺾임(좌·우·유턴), ramp: 진출입로, tunnel: 터널·지하차도, sig: 신호 기다림 초(신호 대기 적용일 때만 셈), stop: 신호에서 서는가, cp: 체크포인트 이름 }]
       opt = { v: 기본 속도 km/h, sig: 신호 대기 적용(true)/무시(false), t0: 출발 시각(ms) , cal: 보정계수 적용(기본 true) }
       신호를 무시해도 회전·진출입·터널 감속과 출발·정지 가감속은 그대로 셈한다 — 신호 기다림(과 신호에서 서는 가감속)만 0
     TT.need(m, sec)                역산 — 거리 m 를 sec 초 안에 가려면 평균 km/h
     TT.vipTwo(segs, opt)           중요업무 두 줄 — 예상 도착(기본 속도) · 가장 이른 도착(직접 입력 · 없으면 기준 속도)
     TT.calAdd(실제초, 계산초) · TT.calK()   보정 — 실측 ÷ 계산 비율을 쌓아 다음 계산에 곱한다(숫자만 저장)
     TT.calTab(json) · TT.calF(ms) · TT.calWhy(ms)   막힘 배율 — data/eta-cal.json(ITS 실측 · 요일 갈래 × 시간대) · 실시간 통행속도가 없는 줄은 제한속도 ÷ calF 로 달린다고 본다 · 설정 calOn 0 이면 1
     TT.fmt(sec) → 「8분 34초」 · TT.hm(ms) → 「14:05」
   중요업무 끄기 스위치 = 아래 VIP_ON(공개 판에서 이 기능을 빼려면 false — 두 앱 모두 단추가 사라진다) */
(function (root) {
  var VIP_ON = true;
  var KEY = 'tg_tt_cfg', KCAL = 'tg_tt_cal';
  /* 기본값 — 회전·진출입·가감속 초는 앱이 정한 제안값(실측 보정 전) · 화면에 그렇게 밝힌다 */
  var DEF = {
    fz: 1.15,           /* 가르고 기본 글씨 배율(지금 = 1.0 → 「크게」 1.15) */
    sz: 2,              /* 진행방향 남은 초 글씨 배율(지금의 2배) */
    fwd: 2000, back: 1000,   /* 안전운전(켜놓고 다니기) 사거리 표시 범위 m */
    vipV: 60,           /* 중요업무 기본 속도(선택지 60/70) */
    vipFast: 100,       /* 가장 이른 도착 — 직접 입력이 없을 때 */
    vMin: 30, vMax: 120,/* 직접 입력 허용 범위 */
    turnS: 6,           /* 회전(좌·우·유턴) 한 번에 더하는 초 */
    rampS: 8,           /* 진출입로 한 번에 더하는 초 */
    tunK: 0.9,          /* 터널·지하차도 속도 배율 */
    accS: 4,            /* 출발·정지 가감속 보정(한 번에 · 처음 출발과 마지막 정지 · 신호에서 설 때) */
    runK: 1.3,          /* 도주 차량 속도 배율(도로 평균 × ) */
    calOn: 1            /* 막힘 배율(ITS 실측) 쓰기 — 1 켬 · 0 끔 */
  };
  var LBL = { calOn: '막힘 배율(ITS 실측)', fz: '기본 글씨 크기', sz: '진행방향 남은 초 글씨 크기', fwd: '사거리 표시 범위 — 앞(m)', back: '사거리 표시 범위 — 뒤(m)', vipV: '중요업무 기본 속도(km/h)', vipFast: '가장 이른 도착 기준 속도(km/h)', vMin: '직접 입력 — 가장 느린(km/h)', vMax: '직접 입력 — 가장 빠른(km/h)', turnS: '회전 감속(초/번)', rampS: '진출입로 감속(초/번)', tunK: '터널 속도 배율', accS: '출발·정지 가감속(초/번)', runK: '도주 차량 속도 배율' };
  var RNG = { calOn: [0, 1], fz: [0.8, 1.6], sz: [1, 3], fwd: [500, 5000], back: [200, 3000], vipV: [30, 120], vipFast: [30, 120], vMin: [10, 60], vMax: [60, 150], turnS: [0, 30], rampS: [0, 30], tunK: [0.5, 1], accS: [0, 15], runK: [1, 2] };
  function ls(k, v) { try { if (v === undefined) return localStorage.getItem(k); if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch (e) { return null; } }
  function mine() { try { return JSON.parse(ls(KEY) || '{}') || {}; } catch (e) { return {}; } }
  function cfg() { var m = mine(), o = {}, k; for (k in DEF) o[k] = typeof m[k] === 'number' && isFinite(m[k]) ? m[k] : DEF[k]; return o; }
  function set(k, v) { if (!(k in DEF)) return false; v = +v; var r = RNG[k]; if (!isFinite(v) || v < r[0] || v > r[1]) return false; var m = mine(); m[k] = v; ls(KEY, JSON.stringify(m)); return true; }
  function reset(k) { if (k == null) { ls(KEY, null); return; } var m = mine(); delete m[k]; ls(KEY, JSON.stringify(m)); }
  function calK() { try { var c = JSON.parse(ls(KCAL) || 'null'); return c && c.n > 0 ? Math.max(0.7, Math.min(1.5, c.s / c.n)) : 1; } catch (e) { return 1; } }
  function calN() { try { var c = JSON.parse(ls(KCAL) || 'null'); return c ? c.n : 0; } catch (e) { return 0; } }
  /* 보정 — 너무 짧은 주행(3분 아래)·이상한 비율(0.5~2 밖)은 안 쌓는다 · 최근 20번만 */
  function calAdd(real, calc) { if (!(real > 180 && calc > 60)) return false; var r = real / calc; if (r < 0.5 || r > 2) return false; var c; try { c = JSON.parse(ls(KCAL) || 'null'); } catch (e) {} c = c || { n: 0, s: 0, l: [] }; c.l = (c.l || []).concat([Math.round(r * 1000) / 1000]).slice(-20); c.n = c.l.length; c.s = c.l.reduce(function (a, b) { return a + b; }, 0); ls(KCAL, JSON.stringify(c)); return true; }
  function calReset() { ls(KCAL, null); }
  /* 막힘 배율 — 표는 같은 사이트 자료 파일(data/eta-cal.json)을 앱이 읽어 넘긴다 · 이 파일은 아무것도 받지도 저장하지도 않는다 */
  var CT = null;
  function calTab(j) { CT = j && j.f ? j : null; }
  function calKey(ms) { var d = new Date(ms || Date.now()), ds = d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2), h = d.getHours(), w = d.getDay();
    var kd = (CT && CT.holidays && CT.holidays.indexOf(ds) >= 0) || w === 0 ? '일·공휴' : w === 6 ? '토' : '평일', bd = h >= 7 && h < 10 ? '출근' : h >= 10 && h < 17 ? '낮' : h >= 17 && h < 20 ? '퇴근' : h >= 20 && h < 23 ? '저녁' : '밤'; return kd + '|' + bd; }
  function calF(ms) { if (!CT || !cfg().calOn) return 1; var k = calKey(ms), v = CT.f[k] != null ? CT.f[k] : CT.fill && CT.fill[k] ? CT.f[CT.fill[k]] : null; return v > 0 ? Math.max(0.8, Math.min(2.5, v)) : 1; }
  function calWhy(ms) { if (!CT) return '표 없음'; if (!cfg().calOn) return '끔'; return calKey(ms).replace('|', ' ') + ' ×' + calF(ms).toFixed(2) + (CT.fill && CT.fill[calKey(ms)] ? '(' + CT.fill[calKey(ms)].replace('|', ' ') + ' 값)' : ''); }
  function run(segs, opt) { opt = opt || {}; var C = cfg(); if (opt.pure) { C.turnS = 0; C.rampS = 0; C.tunK = 1; C.accS = 0; }   /* pure = 거리 ÷ 속도만(검증 기준값) */
    var v0 = +opt.v || 60, useSig = opt.sig !== false, k = opt.cal === false || opt.pure ? 1 : calK(), a0 = opt.mid ? 0 : C.accS, t = a0, d = 0, cps = [], parts = { move: 0, turn: 0, ramp: 0, sig: 0, acc: a0 };   /* mid = 이미 달리는 중(안내 중 다시 셈) — 출발 가감속을 빼고 셈 */
    (segs || []).forEach(function (s) { var v = (+s.v || v0) * (s.tunnel ? C.tunK : 1), mv = (+s.m || 0) / (v / 3.6); t += mv; parts.move += mv; d += +s.m || 0;
      if (s.turn) { t += C.turnS; parts.turn += C.turnS; } if (s.ramp) { t += C.rampS; parts.ramp += C.rampS; }
      if (useSig && s.sig > 0) { t += s.sig; parts.sig += s.sig; if (s.stop) { t += C.accS; parts.acc += C.accS; } }
      if (s.cp) cps.push({ nm: s.cp, m: d, t: t }); });
    t += C.accS; parts.acc += C.accS;
    var t0 = opt.t0 || Date.now(); cps.forEach(function (c) { c.t *= k; c.at = t0 + c.t * 1000; });
    return { sec: t * k, raw: t, k: k, m: d, cps: cps, parts: parts, t0: t0, at: t0 + t * k * 1000, sig: useSig, v: v0 }; }
  /* 역산(구간 그대로) — 이 구간들을 sec 초 안에 가려면 고른 속도가 얼마여야 하나(회전·진출입·터널·가감속 그대로 · 보정 없음 · 신호 무시) — 이분 찾기 */
  function needSegs(segs, sec) { if (!(sec > 0) || !segs || !segs.length) return null; var lo = 1, hi = 400; if (run(strip(segs), { v: hi, sig: false, cal: false }).sec > sec) return null; for (var i = 0; i < 40; i++) { var md = (lo + hi) / 2; if (run(strip(segs), { v: md, sig: false, cal: false }).sec > sec) lo = md; else hi = md; } return hi; }
  function need(m, sec) { if (!(m > 0 && sec > 0)) return null; var C = cfg(); var mv = sec - 2 * C.accS; return mv > 0 ? m / mv * 3.6 : null; }
  /* 중요업무 — 신호 무시 · 두 줄(예상 = 기본 속도 · 가장 이른 = 직접 입력, 없으면 기준 속도) · 범위 밖 직접 입력은 거부(err) */
  function vipTwo(segs, opt) { opt = opt || {}; var C = cfg(), base = +opt.base || C.vipV, fast = opt.fast == null || opt.fast === '' ? null : +opt.fast;
    if (fast != null && !(fast >= C.vMin && fast <= C.vMax)) return { err: '직접 입력은 ' + C.vMin + '~' + C.vMax + 'km/h 안에서만 받는다' };
    var a = run(strip(segs), { v: base, sig: false, t0: opt.t0, cal: false, mid: opt.mid }), b = run(strip(segs), { v: fast || C.vipFast, sig: false, t0: opt.t0, cal: false, mid: opt.mid });   /* 중요업무는 보정 비율을 곱하지 않는다 */
    return { base: a, fast: b, fastV: fast || C.vipFast, typed: fast != null }; }
  function strip(segs) { return (segs || []).map(function (s) { return { m: s.m, turn: s.turn, ramp: s.ramp, tunnel: s.tunnel, cp: s.cp }; }); }   /* 중요업무는 구간 속도가 아니라 고른 속도 하나로 */
  function fmt(sec) { sec = Math.round(sec); var h = Math.floor(sec / 3600), m = Math.floor(sec % 3600 / 60), s = sec % 60; return (h ? h + '시간 ' : '') + (h || m ? m + '분 ' : '') + (s < 10 && (h || m) ? '0' : '') + s + '초'; }
  function hm(ms) { var d = new Date(ms); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function mmss(sec) { sec = Math.round(sec); return Math.floor(sec / 60) + ':' + ('0' + sec % 60).slice(-2); }
  root.TT = { VIP_ON: VIP_ON, DEF: DEF, LBL: LBL, RNG: RNG, cfg: cfg, set: set, reset: reset, run: run, need: need, needSegs: needSegs, vipTwo: vipTwo, calAdd: calAdd, calK: calK, calN: calN, calReset: calReset, calTab: calTab, calF: calF, calWhy: calWhy, fmt: fmt, hm: hm, mmss: mmss };
})(typeof self !== 'undefined' ? self : this);
