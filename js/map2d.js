// 🗜 서초 데이터 압축지도(v0.10.55 「2D 지도」 → v0.10.57 이름 바꿈) — 소유자 「교통경찰 게임에 2D 지도만 있으면 좋겠다. 서초구 위주로 거기서도 이것저것 볼 수 있게 — 나중에 이 부분만 따로 빼도 될 정도로」.
//  **게임 엔진(three.js·TG.game)에 기대지 않는다** — 이 파일 하나 + map2d.html + data/ 파일만 있으면 따로 떼어 돈다.
//  좌표는 모두 **실제 위경도**로 되돌려 그린다(게임의 축약·고무판 좌표를 쓰지 않는다). 없는 값을 지어내지 않고, 근사는 근사라고 적는다.
//  자료: 통계청 행정동 경계 · 행안부 인구 · OSM 도로·건물 · 도로교통공단 TAAS · 경찰청 무인단속 카메라·교차로 신호 · 서울시 문화행사·교통량 · 서울경찰청 집회 · 국가유산청.
(function () {
  'use strict';
  var LON0 = 127.01, LAT0 = 37.49, KX = 88800, KY = 111000;   // 서초 위도에서 1° = 가로 88.8km · 세로 111km(평면 근사)
  function P(lon, lat) { return [(lon - LON0) * KX, -(lat - LAT0) * KY]; }
  function kxAt(z) { return Math.cos((LAT0 - z / KY) * Math.PI / 180) * 111320 / KX; }   // v2.10.0 평면 가로 1m 가 그 위도에서 실제 몇 m 인가(서울 0.99 · 부산 0.97 · 제주 0.95)
  function dTrue(a, c) { return Math.hypot((a[0] - c[0]) * kxAt(c[1]), a[1] - c[1]); }   // 평면 두 점의 실제 거리(m) — 반경·가까운 것 거리                       // 위경도 → 평면 m(오른쪽 +x · 아래 +y)
  function fullM(x, z) { return [x - 2438 - (LON0 - 127.0077) * KX, z - 1743 - (37.4917 - LAT0) * KY]; }   // 서초구 1:1 자료 공간(m) → 평면 m
  var $ = function (id) { return document.getElementById(id); };
  var cv = $('m2d'), ctx = cv.getContext('2d'), DPR = Math.min(window.devicePixelRatio || 1, 2);
  var view = { s: 0.16, cx: 0, cy: 0 };   // s = 화면 px / m · cx,cy = 화면 가운데의 평면 m
  var D = {}, hit = [], sel = null;
  // 층 = [키, 이름, 기본 켜짐, 갈래, 위 줄 단추]. 위 줄에는 자주 쓰는 것만, 나머지는 「☰ 모든 층」 판에서(v0.10.57 · 소유자 「파출소·지구대에서 써도 좋을 만큼 — 찾을 수 있는 것 싹 다」)
  var LAYERS = [
    ['dong', '🏘 행정동', true, '바탕', 1], ['road', '🛣 도로', true, '바탕', 1], ['base', '🗺 바탕(물·녹지·철도)', true, '바탕', 0], ['vw', '🛰 위성·일반 지도(브이월드 · 인터넷)', false, '바탕', 1], ['jcnm', '🏷 교차로·도로 이름(서울·경기 전부)', true, '바탕', 1], ['bld', '🏢 건물', true, '바탕', 0], ['sub', '🚇 지하철역', true, '바탕', 0], ['exit', '🚪 지하철 출입구', false, '바탕', 0],
    ['lev', '🚧 지금 돌발·공사·사고(ITS)', false, '실시간', 1], ['lspd', '🚦 지금 도로 소통(ITS)', false, '실시간', 1], ['lcc', '📹 교통 CCTV 영상(국도·고속)', false, '실시간', 1],
    ['lak', '🟢 미세먼지 측정소(에어코리아)', false, '실시간', 1], ['lkma', '🌡 기상청 실황·특보·지진', false, '실시간', 1], ['lbus', '🚌 경기 버스 도착·위치', false, '실시간', 1],
    ['lwx', '🌦 지금 날씨(격자)', false, '실시간', 1], ['lrad', '🌧 비구름 레이더', false, '실시간', 0], ['lair', '😷 지금 미세먼지(격자)', false, '실시간', 0],
    ['acc', '🚗 교차로 사고(2019~)', true, '교통사고', 1], ['acc10', '🚗 사고 10년(100m 칸)', false, '교통사고', 1], ['fatal10', '🕯 사망사고 10년', false, '교통사고', 0], ['fatal', '🕯 사망사고', false, '교통사고', 0], ['jiga', '🟧 공시지가·지목 지도(대지 ㎡당 · 농지·임야 비율 · 250m·동)', false, '주거·부동산', 1], ['land', '📐 필지 — 공시지가·용도·건물(누르면 · 브이월드)', false, '주거·부동산', 1], ['home', '🏠 주택 실거래 — 평당·전세가율(250m)', false, '주거·부동산', 1], ['jurk', '🚓 경찰서 관할(전국 · 행정동)', false, '치안·안전', 1], ['pbox', '👮 지구대·파출소(전국)', false, '치안·안전', 1], ['rtc', '🏢 상가·업무 매매 실거래(250m)', false, '주거·부동산', 1], ['live250', '👥 생활인구 250m(서울)', false, '인구 구성', 1], ['fl250', '🌏 지금 머무는 외국인 250m(서울)', false, '인구 구성', 1], ['lpop', '👥 생활인구(인구감소지역 · 시군구 월별)', false, '인구 구성', 1], ['fdong', '🌏 외국인 현황(시군구·읍면동 · 비율·인원·유형·5년 변화)', false, '인구 구성', 1], ['minbak', '🏡 외국인관광 도시민박', false, '인구 구성', 1], ['stay', '🛏 숙박시설(호텔·호스텔·콘도·한옥·펜션·농어촌민박·모텔 · 전국)', false, '인구 구성', 1], ['flodge', '🏨 관광숙박(서울 · 호텔·호스텔)', false, '인구 구성', 0], ['msub', '🚇 대구 도시철도 하차(월별)', false, '이동·동선', 0], ['busd', '🚌 인천 버스 정류장 승하차(일평균)', false, '이동·동선', 0], ['ri', '🌾 리(里) 경계 · 가게·사고', false, '바탕', 1], ['usgg', '🗂 시군구로 나눠 보기', false, '바탕', 1], ['juris', '🏛 행정 관할(교육지원청·세무서·법원 · 전국)', false, '바탕', 1], ['rnet', '🛣 도로망 등급(전국 · 국도·지방도·시군도)', false, '도로·교통', 1], ['rpost', '🔢 도로 번호(서울 가로등 · 전국 고속도로 거리표 km)', false, '도로·교통', 1], ['volp', '🚙 시간대 교통량(서울 조사 지점)', false, '도로·교통', 1], ['exv', '🛣 고속도로 영업소 교통량(전국)', false, '도로·교통', 1], ['upb', '👮 지구대·파출소 관할(근사)', false, '치안·안전', 1], ['g250', '🧊 250m 격자(국가표준)', false, '바탕', 0], ['acc250', '🚗 사고 10년(250m 격자)', false, '교통사고', 1], ['hot', '⚠ 사고다발지', false, '교통사고', 0], ['drunk', '🍺 음주 사고 다발지', false, '교통사고', 1],
    ['risk', '🟥 사고위험지역', false, '교통사고', 0], ['sz', '🏫 어린이보호구역', false, '교통사고', 1], ['szh', '🧒 보호구역 어린이 사고', false, '교통사고', 0], ['cam', '📷 단속 카메라', false, '도로·교통', 0], ['spd', '🚥 도로 소통(받은 때)', false, '도로·교통', 0], ['sig', '🚦 신호 주기', false, '도로·교통', 0], ['sigx', '🔢 신호 교차로 번호', false, '도로·교통', 0],
    ['trd', '🏪 상권분석(카드·유동·점포)', false, '소비·상권', 1], ['rent', '💰 상가 임대료·공실률', false, '소비·상권', 0], ['szone', '🏬 소진공 주요상권(전국)', false, '소비·상권', 0], ['jgg', '🧩 집계구 인구·가구·사업체(SGIS)', false, '인구 구성', 1], ['crowd', '📡 실시간 인파·카드', false, '이동·동선', 1], ['live', '👥 생활인구(지금)', false, '인구 구성', 1], ['sales', '💳 카드 매출(시간대)', false, '소비·상권', 1], ['bus', '🚌 버스 승차·하차', false, '이동·동선', 1], ['subr', '🚇 지하철 승차·하차', false, '이동·동선', 0], ['vol', '🚙 교통량', false, '이동·동선', 0], ['bike', '🚲 따릉이', false, '이동·동선', 0],
    ['pol', '👮 경찰 관서', false, '치안·안전', 1], ['fire', '🚒 소방', false, '치안·안전', 0], ['er', '🏥 응급실', false, '치안·안전', 1], ['hosp', '🩺 병원·의원', false, '치안·안전', 0], ['phar', '💊 약국', false, '치안·안전', 1],
    ['bar', '🍺 주점(밤 순찰)', false, '치안·안전', 0], ['play', '🎤 노래방·PC방', false, '치안·안전', 0], ['inn', '🏨 숙박', false, '치안·안전', 0], ['heat', '🥵 무더위쉼터', false, '치안·안전', 0], ['cold', '🥶 한파쉼터', false, '치안·안전', 0], ['hyd', '🧯 소화전', false, '치안·안전', 0], ['wc', '🚻 화장실', false, '치안·안전', 0],
    ['school', '🏫 학교', false, '교육·돌봄', 0], ['kids', '🧸 유치원·어린이집', false, '교육·돌봄', 0], ['pg', '🛝 놀이터', false, '교육·돌봄', 0], ['park', '🌳 공원', false, '생활시설', 0], ['welf', '🧓 복지시설', false, '교육·돌봄', 0], ['kyr', '🧓 경로당(서울시)', false, '교육·돌봄', 0], ['cc', '👶 어린이집(서울시)', false, '교육·돌봄', 0], ['kg', '🎒 유치원(교육청)', false, '교육·돌봄', 0], ['aca', '📚 입시·교과학원', false, '교육·돌봄', 0], ['edu', '🏫 학교(초·중·고·대학)', false, '교육·돌봄', 0], ['govr', '🏛 관공서(서울·경기)', false, '생활시설', 0],
    ['gov', '🏢 관공서·주민센터', false, '생활시설', 0], ['lib', '📚 도서관', false, '생활시설', 0], ['post', '📮 우체국', false, '생활시설', 0], ['bank', '🏦 은행·ATM', false, '생활시설', 0], ['conv', '🏪 편의점', false, '생활시설', 0],
    ['fuel', '⛽ 주유소', false, '생활시설', 0], ['ev', '🔌 전기차 충전', false, '생활시설', 0], ['pk', '🅿 주차장', false, '생활시설', 0],
    ['jur', '🚓 경찰서 관할(서초·방배)', false, '치안·안전', 0], ['srcctv', '📹 CCTV(안심귀갓길)', false, '치안·안전', 0], ['srbell', '🔔 안심벨', false, '치안·안전', 0], ['srlamp', '💡 보안등(안심귀갓길)', false, '치안·안전', 0], ['sr112', '🆘 112 위치 신고 안내', false, '치안·안전', 0], ['srsvc', '🏪 안심 서비스·지킴이집', false, '치안·안전', 0],
    ['aed', '❤️ AED(서울·경기)', false, '치안·안전', 0], ['fw', '🧯 소방용수(서울시)', false, '치안·안전', 0], ['pkcctv', '📸 불법주정차 단속 CCTV', false, '도로·교통', 0], ['tow', '🛻 견인차량보관소', false, '도로·교통', 0], ['wc2', '🚻 공중화장실(서울·경기)', false, '생활시설', 0], ['gpark', '🅿 주차장(공식 목록 · 전국)', false, '생활시설', 0], ['tlt', '🚦 신호등(전국 · 현시 시간)', false, '도로·교통', 1], ['bstop', '🚏 버스정류장 자리(전국 · OSM)', false, '이동·동선', 0], ['gev', '🔌 전기차 충전소(경기)', false, '생활시설', 0], ['ger', '🏥 응급의료기관(경기)', false, '치안·안전', 0], ['gfest', '🎪 문화축제(경기)', false, '행사·역사', 0], ['glamp', '💡 보안등(경기 29만)', false, '치안·안전', 0], ['box', '📦 안심택배함', false, '생활시설', 0], ['dem', '🧠 치매안심센터', false, '교육·돌봄', 0], ['tgis', '🚥 T-GIS 신호 교차로', false, '도로·교통', 0], ['spot', '🎯 길목 — 이 시각 하차', false, '이동·동선', 0], ['spota', '🗂 길목 다발지(참고)', false, '교통사고', 0], ['hot10', '🗂 다발지 10년(2016~2025)', false, '교통사고', 1], ['jct', '🚦 교차로 사고 10년(서울·경기)', false, '교통사고', 0],
    ['evt', '📅 행사·집회', true, '행사·역사', 1], ['her', '🏛 국가유산', false, '행사·역사', 0],
    ['flt', '🌊 침수 흔적(2010~2025)', false, '날씨·계절', 0], ['flr', '🌧 침수 이력 도로', false, '날씨·계절', 0], ['und', '🚇 지하차도(침수 이력)', false, '날씨·계절', 0],
    ['ice', '🧊 제설함(결빙 우려 자리)', false, '날씨·계절', 0], ['hcab', '🔥 도로 열선 길', false, '날씨·계절', 0], ['advb', '❄ 제설 전진기지', false, '날씨·계절', 0],
    ['pbtn', '🚸 보행자작동신호기', false, '도로·교통', 0]
  ];
  // OSM 시설 갈래 → 층 키
  var FAC_K = { '경찰': 'pol', '소방': 'fire', '소화전': 'hyd', '화장실': 'wc', '학교': 'school', '유치원·어린이집': 'kids', '놀이터': 'pg', '공원': 'park', '복지시설': 'welf', '관공서·주민센터': 'gov', '도서관': 'lib',
    '우체국': 'post', '은행·ATM': 'bank', '편의점': 'conv', '주유소': 'fuel', '전기차 충전': 'ev', '주차장': 'pk', '지하철 출입구': 'exit', '병원': null, '의원': null, '약국': null };
  var FAC_C = { pol: '#1d4ed8', fire: '#dc2626', hyd: '#ef4444', wc: '#0891b2', school: '#ca8a04', kids: '#f59e0b', pg: '#84cc16', park: '#16a34a', welf: '#a855f7', gov: '#475569', lib: '#7c3aed',
    post: '#e11d48', bank: '#0f766e', conv: '#64748b', fuel: '#b45309', ev: '#059669', pk: '#2563eb', exit: '#0ea5e9' };
  var on = {}; LAYERS.forEach(function (l) { on[l[0]] = l[2]; });
  try { var sv = JSON.parse(localStorage.getItem('tg_map2d') || 'null'); if (sv && sv.on) Object.keys(sv.on).forEach(function (k) { if (k in on) on[k] = !!sv.on[k]; }); } catch (e) {}
  var HASHLY = false, HOUR = null;   // 주소의 #ly= 로 연 층 — 이 동안은 저장하지 않는다(T-Book 이 여는 보기는 그때만)
  function saveOn() { if (HASHLY) return; try { localStorage.setItem('tg_map2d', JSON.stringify({ on: on })); } catch (e) {} }
  function hashLayers() {   // #ly=acc,sz,cam → 행정동·도로 + 그 층만 켠다. 모르는 키는 건너뛴다
    var hm = /[#&]h=(\d{1,2})(?!\d)/.exec(location.hash); HOUR = hm && +hm[1] < 24 ? +hm[1] : null;   // #h=22 — 길목 층이 볼 시각
    var m = /[#&]ly=([a-z0-9,]*)/.exec(location.hash); if (!m) return false;
    var ks = m[1].split(',').filter(function (k) { return k in on && k !== 'crowd'; });   // v2.34.0 소유자 「실시간 인파는 필요할 때만」 — T-Book 주소의 crowd 는 켜지 않는다(레이어 판·「🎪 행사·인파」로 켠다)
    LAYERS.forEach(function (l) { on[l[0]] = false; }); on.dong = true; on.road = true; on.base = true; on.bld = true;
    ks.forEach(function (k) { on[k] = true; }); HASHLY = true; return true;
  }
  hashLayers();
  try { if (!localStorage.getItem('tg_map2d_crowd1')) { on.crowd = false; localStorage.setItem('tg_map2d_crowd1', '1'); saveOn(); } } catch (e) {}   // v2.34.0 이 기기에 「켜짐」으로 남은 인파를 한 번 끈다

  // ---------- 자료 읽기 ----------
  var FILES = { ridx: 'data/regions.json', pstat: 'data/police-stats.json', season: 'data/season-seocho.json', pbtn: 'data/pedbtn-seocho.json', enf: 'data/enforce-seocho.json', dong: 'data/dong-seocho.json', pop: 'data/pop-seocho.json', roads: 'data/maps/seocho-full-roads.json', full: 'data/maps/seocho-full.json',
    base: 'data/maps/seocho.json', gu: 'data/maps/seoul-districts.json', acc: 'data/taas-nodes-seocho.json', hot: 'data/taas.json',
    cam: 'data/cameras-seocho.json', sig: 'data/signal-tod-seocho.json', evt: 'data/events-seocho.json', vol: 'data/traffic-vol-seocho.json', her: 'data/heritage-seocho.json',
    near: 'data/dong-near.json', xing: 'data/intersections-seocho.json', pub: 'data/pubdata-seocho.json', police: 'data/police-seocho.json', sz: 'data/schoolzone-seocho.json', st: 'data/stores-seocho.json',
    jur: 'data/jur-seocho.json', tgis: 'data/tgis-seocho.json', spot: 'data/spot-seocho.json',
    bidx: 'data/base/index.json', ov: 'data/base/ov.json', sgg: 'data/base/sgg.json', flow: 'data/flow-seocho.json', livep: 'data/live-seocho.json', trend: 'data/trend-seocho.json', hot10: 'data/hot10-seocho.json', trdar: 'data/trdar-seocho.json', safety: 'data/safety-seocho.json', taas10: 'data/taas10-seocho.json' };
  // v2.6.0 지역 자료 받기 하나로(전국 확장 S1·S2) — 권역마다 따로 둔 자료 저장소(340patrolman.github.io/datamap-data-…/)에서 받는다 · 같은 파일은 한 번만 받고(글로 보관 · 쓰는 곳마다 새로 풀어 서로 건드리지 않음) · 없음(404)과 실패를 가른다
  // 이 PC(localhost)에서는 지금처럼 data/r/ 를 쓴다 · 권역 목록 = data/regions.json · 권역마다 manifest.json(시군구 → 층 바이트·상자·동 이름)
  var RBASE = {}, RGETT = {}, RMISS = {}, RMANU = [], ONGH = /github\.io$/.test(location.hostname), REGR = null, REGP = new Promise(function (res) { REGR = res; });   // REGP = 권역 목록을 읽은 뒤(그 전에 부른 받기는 기다린다)
  function rU(gu, f) { return (RBASE[String(gu).slice(0, 2)] || 'data/') + 'r/' + gu + '/' + f; }
  function rGet(gu, f) { var k = gu + '/' + f;
    if (!RGETT[k]) { RGETT[k] = REGP.then(function () { return fetch(rU(gu, f)); }).then(function (r) { if (!r.ok) { if (r.status === 404) RMISS[k] = 1; throw new Error(r.status === 404 ? 'none' : 'fail'); } return r.text(); });
      RGETT[k].catch(function (e) { if (!e || e.message !== 'none') delete RGETT[k]; }); }
    return RGETT[k].then(function (t) { return JSON.parse(t); }); }
  function regionsLoad() {
    return fetch('data/regions.json').then(function (r) { return r.json(); }).then(function (RG) { var parts = [], layers = {};
      return Promise.all(RG.regions.map(function (g, i) { if (ONGH) RBASE[g.sido] = '/' + g.repo + '/'; var u = ONGH ? '/' + g.repo + '/manifest.json' : 'data/r/manifest-' + g.sido + '.json'; RMANU.push(u);
        return fetch(u).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (m) { parts[i] = m.gus || []; Object.keys(m.layers || {}).forEach(function (k) { layers[k] = m.layers[k]; }); }).catch(function () { parts[i] = []; }); }))
        .then(function () { D.ridx = { gus: [].concat.apply([], parts), layers: layers, regions: RG.regions }; REGR(); }); }).catch(function () { D.ridx = null; REGR(); });
  }
  function get(k) { if (k === 'ridx') return regionsLoad(); return fetch(FILES[k]).then(function (r) { return r.json(); }).then(function (j) { D[k] = j; }).catch(function () { D[k] = null; }); }
  var LATE = ['livep', 'trend', 'hot10', 'trdar', 'safety', 'taas10', 'enf', 'season', 'pbtn', 'pstat'];   // v0.10.80 무거운 자료(상권·안전시설·사고 10년·추이)는 첫 그림 뒤에 읽는다 — 지도가 먼저 뜬다
  Promise.all(Object.keys(FILES).filter(function (k) { return LATE.indexOf(k) < 0; }).map(get)).then(function () { setTimeout(gpsHere, 0); prep(); pubPrep(); extraPrep(); basePrep(); sggPrep(); flowPrep(); fit(); if (on.bld && view.s > 0.12) loadBld(); draw(); applyHash(); $('m2dLoad').style.display = 'none'; paintTime(); summary();
    Promise.all(LATE.map(get)).then(function () { livePrep(); trdPrep(); safePrep(); a10Prep(); seasonPrep(); paintPre(); summary(); draw(); if (sel && $('m2dCard').classList.contains('on')) show(sel.it); }); });
  function loadBld() {   // 건물 593KB — 켤 때만
    if (D.bld !== undefined) return;
    D.bld = null; fetch('data/maps/seocho-full-buildings.json').then(function (r) { return r.json(); }).then(function (j) { D.bld = j; prepBld(); draw(); }).catch(function () {});
  }

  // ---------- 준비: 모든 자료를 평면 m 로 ----------
  var NEAR = [], DONG = [], ROADS = [], NODES = [], GU = [], BLD = [];
  // ---------- v0.10.91 서울 25개 구 행정동(지역 자료 · data/r/<구 5자리>/dong.json) — 화면에 걸린 구만 받는다 · 서초구는 기존 서초 자료가 우선 ----------
  // 동 열쇠는 행정동 코드 8자리(이름은 구가 달라도 겹친다 — 신사동 · 강남/관악). 업종 줄·분기 추이(dongx)는 카드를 열 때만 받는다.
  var RDONG = [], RGUN = {}, RLOAD = {}, RX = {}, LMX = {}, SMX = {}, RWANT = null, RLOADT = {}, TWANT = null;
  function rIdx() { return D.ridx && D.ridx.gus || []; }
  function viewLL() { var a = M(0, 0), b = M(cv.clientWidth, cv.clientHeight); return [a[0] / KX + LON0, LAT0 - b[1] / KY, b[0] / KX + LON0, LAT0 - a[1] / KY]; }
  // v0.10.95 단속 카메라 · 어린이보호구역 · 생활안전 시설(구마다 safety.json) — 서초는 기존 서초 파일이 우선(서초 구 파일은 안 받는다)
  var RLOADS = {}, SAFE_KEYS = ['tlt', 'cam', 'sz', 'srbell', 'srcctv', 'srlamp', 'sr112', 'srsvc', 'aed', 'fw', 'tow', 'wc2', 'box', 'dem', 'gpark', 'gev', 'ger', 'gfest'], RLOADL = {};
  function lpLoad(gu) {   // v1.3.0 경기 보안등(29만) — 보안등 층을 켰을 때만 그 구의 lamp.json
    if (RLOADL[gu]) return; RLOADL[gu] = 1; var L = SAFE.filter(function (x) { return x[0] === 'glamp'; })[0]; if (!L) { RLOADL[gu] = 0; return; }
    rGet(gu, 'lamp.json').then(function (j) { if (!L.src) L.src = j.source; j.pts.forEach(function (r) { L[3].push({ p: P(r[1], r[0]), r: r }); }); RLOADL[gu] = 3; draw(); }).catch(function () { RLOADL[gu] = 2; });
  }
  var RLOADB = {};
  function bsLoad(gu) {   // v2.14.0 전국 버스정류장 자리(OSM) — 층을 켰을 때만 그 구의 bstop.json
    if (RLOADB[gu]) return; RLOADB[gu] = 1; var L = SAFE.filter(function (x) { return x[0] === 'bstop'; })[0]; if (!L) { RLOADB[gu] = 0; return; }
    rGet(gu, 'bstop.json').then(function (j) { if (!L.src) L.src = j.source; j.pts.forEach(function (r) { L[3].push({ p: P(r[1], r[0]), r: r }); }); RLOADB[gu] = 3; draw(); }).catch(function () { RLOADB[gu] = 2; });
  }
  function sfLoad(gu) {
    if (RLOADS[gu]) return RLOADS[gu]; if (gu === '11650') return (RLOADS[gu] = Promise.resolve()); if (!SAFE.length) return Promise.resolve();   // 서초 안전 파일(늦게 읽음)이 칸을 만든 뒤에
    RLOADS[gu] = rGet(gu, 'safety.json').then(function (j) {
      var key = function (a, b) { return a + '|' + b; };
      if (!D.cam) D.cam = { items: [], source: j.source.cam }; var hc = {}; D.cam.items.forEach(function (c) { hc[key(c.lat, c.lon)] = 1; }); j.cam.forEach(function (c) { if (!hc[key(c.lat, c.lon)]) D.cam.items.push(c); });
      if (!D.sz) D.sz = { zones: [], hot: [], source: { zones: j.source.sz } }; var hz = {}; D.sz.zones.forEach(function (z) { hz[key(z.name, z.lat)] = 1; }); j.sz.forEach(function (z) { if (!hz[key(z.name, z.lat)]) D.sz.zones.push(z); });
      var I = j.items || {}, add = function (k, arr) { var L = SAFE.filter(function (x) { return x[0] === k; })[0]; if (!L || !arr) return; var hs = {}; L[3].forEach(function (q) { hs[key(q.r[0], q.r[1])] = 1; }); arr.forEach(function (r) { if (r[0] && r[1] && !hs[key(r[0], r[1])]) L[3].push({ p: P(r[1], r[0]), r: r }); }); };
      var it = I.srItem || []; add('srbell', it.filter(function (r) { return r[2] === '301'; })); add('srcctv', it.filter(function (r) { return r[2] === '302'; })); add('srlamp', it.filter(function (r) { return r[2] === '305'; }));
      add('sr112', it.filter(function (r) { return ['303', '304', '306', '307', '308'].indexOf(r[2]) >= 0; })); add('srsvc', I.srSvc); add('aed', I.aed); add('fw', I.fire); add('tow', I.tow); add('wc2', I.wc); add('box', I.box); add('dem', I.dem);
      add('gpark', I.park); add('tlt', I.tl); add('gev', I.ev); add('ger', I.er); add('gfest', I.fest); SRCX = Object.assign(SRCX, j.source || {});
      draw();
    }).catch(function () {}); return RLOADS[gu];
  }
  // v0.10.100 동 현황 보강(구마다 fac.json) — 남녀 · 어린이집·유치원(해마다) · 경로당 · 입시·교과학원 · 상권변화지표 · 점포 추이 · 이 동의 상권. 서초도 이 파일을 쓴다.
  var RLOADF = {}, RFAC = {}, FAC_KEYS = ['kyr', 'cc', 'kg', 'aca', 'edu', 'govr'];
  var GOVC = { '주민센터': '#16a34a', '시청·구청': '#1d4ed8', '세무서': '#a16207', '등기소': '#7c3aed', '법원': '#9333ea', '검찰': '#6b21a8', '경찰': '#0f172a', '소방': '#dc2626', '교육청': '#0d9488', '보건소': '#db2777', '우체국': '#ea580c', '국가기관': '#475569' };
  var FACL = { kyr: ['🧓 경로당(서울시)', '#b45309'], cc: ['👶 어린이집(서울시)', '#db2777'], kg: ['🎒 유치원(교육청)', '#d97706'], aca: ['📚 입시·교과학원', '#2563eb'], edu: ['🏫 학교(초·중·고·대학)', '#0f766e'], govr: ['🏛 관공서(서울·경기)', '#1d4ed8'] };
  function facL(k) { var L = SAFE.filter(function (x) { return x[0] === k; })[0]; if (!L) { L = [k, FACL[k][0], FACL[k][1], [], 0]; SAFE.push(L); POLL.push([k, FACL[k][0], FACL[k][1], FACL[k][0]]); } return L; }
  function fLoad(gu, then) {
    if (!RLOADF[gu]) RLOADF[gu] = rGet(gu, 'fac.json').then(function (j) { RFAC[gu] = j;
      FAC_KEYS.forEach(function (k) { var L = facL(k); (j.pts[k === 'govr' ? 'gov' : k] || []).forEach(function (r) { L[3].push({ p: P(r[1], r[0]), r: r, m: j }); }); }); draw(); }).catch(function () { RFAC[gu] = { dong: {}, pts: {}, source: {} }; });
    if (then) RLOADF[gu].then(then); return RLOADF[gu];
  }
  // v0.10.103 교차로별 사고 10년(구마다 jct.json — 이름 있는 교차로 · 70m 안 100m 칸 근사) · 다발지 10년 서울·경기(구마다 hot10.json — 서초는 기존 파일)
  var RLOADJ = {}, JCT = [], RLOADH = {};
  function jLoad(gu) {
    if (RLOADJ[gu]) return RLOADJ[gu];
    RLOADJ[gu] = rGet(gu, 'jct.json').then(function (j) {
      j.items.forEach(function (r) { var t = 0; r[3].forEach(function (v) { t += v; }); JCT.push({ p: [r[1], r[2]], r: r, t: t, m: j }); }); JCT.sort(function (a, b) { return a.t - b.t; }); draw(); }).catch(function () {}); return RLOADJ[gu];
  }
  function hLoad(gu) {
    if (gu === '11650' || RLOADH[gu]) return RLOADH[gu] || Promise.resolve(); if (!D.hot10) return Promise.resolve();   // 서초 파일(늦게 읽음)이 먼저
    RLOADH[gu] = rGet(gu, 'hot10.json').then(function (j) {
      j.spots.forEach(function (g) { g.m = j; D.hot10.spots.push(g); }); draw(); }).catch(function () {}); return RLOADH[gu];
  }
  // v0.10.96 TAAS 사고 10년(구마다 taas10.json · 서초 taas10-seocho 와 같은 꼴) — 서초는 기존 파일이 우선
  var RLOADA = {};
  function aLoad(gu) {
    if (gu === '11650') return Promise.resolve(); if (RLOADA[gu]) return RLOADA[gu];
    RLOADA[gu] = rGet(gu, 'taas10.json').then(function (j) {
      j.cells.forEach(function (c) { a10Add(c, j); }); j.fatal.forEach(function (f) { F10.push({ f: f, p: P(f[17], f[16]), m: j }); }); draw();
    }).catch(function () {}); return RLOADA[gu];
  }
  // v0.10.98 계절 위험 서울(구마다 season.json · 서초 둘레 상자 밖만) — 서초 판(LATE)이 SEA 를 만든 뒤에 붙인다
  var RLOADE = {}, SEA_KEYS = ['flt', 'flr', 'und', 'ice', 'hcab', 'advb'];
  function bbOf(pts) { var b = [1e9, -1e9, 1e9, -1e9]; pts.forEach(function (q) { b[0] = Math.min(b[0], q[0]); b[1] = Math.max(b[1], q[0]); b[2] = Math.min(b[2], q[1]); b[3] = Math.max(b[3], q[1]); }); return b; }
  function seaLoad(gu) {
    if (RLOADE[gu]) return RLOADE[gu]; if (!SEA) return Promise.resolve();
    RLOADE[gu] = rGet(gu, 'season.json').then(function (j) {
      j.traces.forEach(function (t) { SEA.tr.push({ p: [t[0], t[1]], t: t, m: j }); });
      j.floodRoads.forEach(function (r) { var pts = dec2(r, 6); SEA.fr.push({ r: r, pts: pts, bb: bbOf(pts), m: j }); });
      j.under.forEach(function (u) { SEA.un.push({ p: [u[2], u[3]], u: u, m: j }); });
      j.sbox.forEach(function (b) { SEA.ib.push({ p: [b[0], b[1]], b: b, m: j }); });
      j.adv.forEach(function (a) { SEA.ad.push({ p: [a[0], a[1]], a: a, m: j }); });
      j.heat.forEach(function (h) { SEA.ht.push({ h: h, segs: h[5].map(function (a) { return dec2(a, 0); }), m: j }); });
      draw();
    }).catch(function () {}); return RLOADE[gu];
  }
  var RLOADX = {};
  function xLoad(gu) {   // v0.10.94 버스·지하철 승하차(구마다) — 서초 정류장·역이 이미 있으면 건너뛴다
    if (RLOADX[gu]) return RLOADX[gu];
    RLOADX[gu] = rGet(gu, 'transit.json').then(function (j) {
      if (!PUB) return; var hb = {}, hs = {}; PUB.bus.forEach(function (q) { hb[q.o.id] = 1; }); PUB.subr.forEach(function (q) { hs[q.name] = 1; });
      j.bus.forEach(function (b) { if (hb[b[0]]) return; var on2 = b[4], off2 = b[5], day = on2.concat(off2).reduce(function (a, c) { return a + c; }, 0), tot = on2.map(function (v, i) { return v + off2[i]; });
        FLOW.bus[b[0]] = [on2, off2]; PUB.bus.push({ name: b[1], p: P(b[2], b[3]), o: { id: b[0], name: b[1], lon: b[2], lat: b[3], day: day, h: tot, peak: tot.indexOf(Math.max.apply(null, tot)), rg: j } }); });
      j.sub.forEach(function (b) { if (hs[b[0]]) return; FLOW.sub[b[0]] = [b[4], b[5], b[1]]; PUB.subr.push({ name: b[0], p: P(b[2], b[3]), o: { name: b[0], lines: b[1], lon: b[2], lat: b[3], rg: j } }); });
      draw();
    }).catch(function () {}); return RLOADX[gu];
  }
  function needRegions() {
    if ((on.jct || on.hot10) && view.s >= 0.025) { var vj = viewLL(); rIdx().forEach(function (g) { var x = g.box; if (x[2] < vj[0] || x[0] > vj[2] || x[3] < vj[1] || x[1] > vj[3]) return; var B = g.bytes || {}; if (on.jct && B.jct && !RLOADJ[g.gu]) jLoad(g.gu); if (on.hot10 && B.hot10 && !RLOADH[g.gu]) hLoad(g.gu); }); }
    if (view.s >= 0.03 && FAC_KEYS.some(function (k) { return on[k]; })) { var vf = viewLL(); rIdx().forEach(function (g) { if (RLOADF[g.gu] || !(g.bytes || {}).fac) return; var x = g.box; if (x[2] < vf[0] || x[0] > vf[2] || x[3] < vf[1] || x[1] > vf[3]) return; fLoad(g.gu); }); }
    if (view.s >= 0.02 && SEA && SEA_KEYS.some(function (k) { return on[k]; })) { var ve = viewLL(); rIdx().forEach(function (g) { if (RLOADE[g.gu] || !(g.bytes || {}).season) return; var x = g.box; if (x[2] < ve[0] || x[0] > ve[2] || x[3] < ve[1] || x[1] > ve[3]) return; seaLoad(g.gu); }); }
    if ((on.acc10 || on.fatal10 || on.fatal) && view.s >= 0.012) { var va = viewLL(); rIdx().forEach(function (g) { if (RLOADA[g.gu] || !(g.bytes || {}).taas10) return; var x = g.box; if (x[2] < va[0] || x[0] > va[2] || x[3] < va[1] || x[1] > va[3]) return; aLoad(g.gu); }); }
    if (on.bstop && view.s >= 0.03) { var vb = viewLL(); rIdx().forEach(function (g) { if (RLOADB[g.gu] || !(g.bytes || {}).bstop) return; var x = g.box; if (x[2] < vb[0] || x[0] > vb[2] || x[3] < vb[1] || x[1] > vb[3]) return; bsLoad(g.gu); }); }
    if (on.glamp && view.s >= 0.06) { var vl = viewLL(); rIdx().forEach(function (g) { if (RLOADL[g.gu] || !(g.bytes || {}).lamp) return; var x = g.box; if (x[2] < vl[0] || x[0] > vl[2] || x[3] < vl[1] || x[1] > vl[3]) return; lpLoad(g.gu); }); }
    if (view.s >= 0.03 && SAFE_KEYS.some(function (k) { return on[k]; })) { var vs2 = viewLL(); rIdx().forEach(function (g) { if (RLOADS[g.gu] || !(g.bytes || {}).safety) return; var x = g.box; if (x[2] < vs2[0] || x[0] > vs2[2] || x[3] < vs2[1] || x[1] > vs2[3]) return; sfLoad(g.gu); }); }
    if ((on.bus && view.s > 0.07) || (on.subr && view.s >= 0.02)) { var vx = viewLL(); rIdx().forEach(function (g) { if (RLOADX[g.gu] || !(g.bytes || {}).transit) return; var x = g.box; if (x[2] < vx[0] || x[0] > vx[2] || x[3] < vx[1] || x[1] > vx[3]) return; xLoad(g.gu); }); }
    if (on.lspd && spdSpan()) { var vs3 = viewLL(); rIdx().forEach(function (g) { if (RLOADI[g.gu] || !(g.bytes || {}).itsl) return; var x = g.box; if (x[2] < vs3[0] || x[0] > vs3[2] || x[3] < vs3[1] || x[1] > vs3[3]) return; slLoad(g.gu); }); }
    if (on.lcc && view.s >= 0.003) { var vc3 = viewLL(); rIdx().forEach(function (g) { if (RLOADC[g.gu] || !(g.bytes || {}).itscctv) return; var x = g.box; if (x[2] < vc3[0] || x[0] > vc3[2] || x[3] < vc3[1] || x[1] > vc3[3]) return; ccLoad(g.gu); }); }
    if (on.jcnm && view.s >= 0.02) { var vn3 = viewLL(); rIdx().forEach(function (g) { if (RLOADN[g.gu] || !(g.bytes || {}).jcnm) return; var x = g.box; if (x[2] < vn3[0] || x[0] > vn3[2] || x[3] < vn3[1] || x[1] > vn3[3]) return; jnLoad(g.gu); }); }
    if (on.jgg && view.s >= 0.03) { var vj2 = viewLL(); rIdx().forEach(function (g) { if (RLOADQ[g.gu] || !(g.bytes || {}).jgg) return; var x = g.box; if (x[2] < vj2[0] || x[0] > vj2[2] || x[3] < vj2[1] || x[1] > vj2[3]) return; qLoad(g.gu); }); }
    if (on.szone && view.s >= 0.012) { var vz = viewLL(); rIdx().forEach(function (g) { if (RLOADZ[g.gu] || !(g.bytes || {}).szone) return; var x = g.box; if (x[2] < vz[0] || x[0] > vz[2] || x[3] < vz[1] || x[1] > vz[3]) return; zLoad(g.gu); }); }
    if (on.trd && view.s >= 0.02) { var vg = viewLL(); rIdx().forEach(function (g) { if (RLOADG[g.gu] || !(g.bytes || {}).ggtrd) return; var x = g.box; if (x[2] < vg[0] || x[0] > vg[2] || x[3] < vg[1] || x[1] > vg[3]) return; gLoad(g.gu); }); }
    if (on.trd && view.s >= 0.02) { var vh = viewLL(); rIdx().forEach(function (g) { if (RLOADH2[g.gu] || !(g.bytes || {}).trdhl) return; var x = g.box; if (x[2] < vh[0] || x[0] > vh[2] || x[3] < vh[1] || x[1] > vh[3]) return; hlLoad(g.gu); }); }
    if ((on.trd || document.body.classList.contains('bizon')) && view.s >= 0.02) { var vt = viewLL(); rIdx().forEach(function (g) { if (RLOADT[g.gu] || !(g.bytes || {}).trdar) return; var x = g.box; if (x[2] < vt[0] || x[0] > vt[2] || x[3] < vt[1] || x[1] > vt[3]) return; tLoad(g.gu); }); }
    if (!(on.dong || on.live || on.sales || on.jurk || on.upb) || view.s < 0.012) return; var v = viewLL();
    rIdx().forEach(function (g) { if (g.gu === '11650' || RLOAD[g.gu]) return; var x = g.box; if (x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return;
      rLoadGu(g.gu); });
  }
  function rAdd(j) {
    RGUN[j.name] = 1;
    j.dong.forEach(function (d) { var polys = d.polys.map(function (Pg) { return Pg.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); });
      var box = [1e9, -1e9, 1e9, -1e9]; polys.forEach(function (Pg) { Pg[0].forEach(function (q) { box[0] = Math.min(box[0], q[0]); box[1] = Math.max(box[1], q[0]); box[2] = Math.min(box[2], q[1]); box[3] = Math.max(box[3], q[1]); }); });
      RDONG.push({ name: d.name, gu: j.name, gcd: j.gu, k: d.k, polys: polys, box: box, c: d.c ? P(d.c[0], d.c[1]) : labelPt(polys, box), pop: d.pop, live: d.live, sales: d.sales, old: d.old, rg: j }); });
    LMX = {}; SMX = {};
    if (RWANT) RDONG.forEach(function (d) { if (RWANT && d.gcd === RWANT.gu && d.name === RWANT.name) { RWANT = null; var s2 = S(d.c); sel = { x: s2[0], y: s2[1], r: 6, it: { kind: 'dong', d: d } }; show(sel.it); } });
  }
  function rExt(d) {   // 업종 줄·분기 추이 — 카드를 열 때만
    if (!d.rg || d.x !== undefined) return; var g = d.gcd;
    if (RX[g]) { d.x = RX[g].dong[d.k] || {}; return; }
    d.x = null; rGet(g, 'dongx.json').then(function (j) { RX[g] = j; RDONG.forEach(function (q) { if (q.gcd === g && q.x === null) q.x = j.dong[q.k] || {}; }); if (sel && sel.it.d && sel.it.d.gcd === g) show(sel.it); }).catch(function () { d.x = {}; });
  }
  var RLOADQ = {}, JGG = [], JGGM = 'dens';   // v1.4.0 통계청 SGIS 집계구
  var JGGMS = { pop: ['👥 인구', '#7c3aed'], dens: ['🏙 인구 밀도(명/ha)', '#6d28d9'], hh: ['🏠 가구', '#2563eb'], fam: ['👪 평균 가구원', '#0891b2'], house: ['🏢 주택', '#0d9488'], corp: ['🏪 사업체', '#b45309'], wrk: ['👔 종사자', '#c2410c'], job: ['⚖ 종사자 ÷ 인구', '#be123c'] };
  var RLOADN = {}, JCN = [], RDN = [], JIDX = null, JIDXP = null;   // v1.8.0 교차로·도로 이름
  var JTY = { 1: '교차로', 4: '도로시설(교량·터널·지하차도 끝)', 6: 'IC·연결로' };
  // v2.5.0 교차로 이름 두 출처(ITS 표준노드링크 · 바탕 OSM/C-ITS)가 같은 자리를 다르게 부를 때(예: 발안IC사거리 ↔ 발안IC삼거리) — 이름 층이 켜져 있으면 ITS 교차로 80m 안의 바탕 이름은 그리지 않고, 카드에 「다른 이름」으로 밝힌다(소유자 신고 2026-10-05)
  var JH = {};
  function itsNear(p) { var x = Math.floor(p[0] / 100), y = Math.floor(p[1] / 100); for (var dx = -1; dx <= 1; dx++) for (var dy = -1; dy <= 1; dy++) { var L2 = JH[(x + dx) + ',' + (y + dy)]; if (L2) for (var i = 0; i < L2.length; i++) if (Math.hypot(L2[i].p[0] - p[0], L2[i].p[1] - p[1]) <= 80) return L2[i]; } return null; }
  function osmNear(p, name) { var o = []; JLAB.forEach(function (L) { if (dTrue(L.p, p) <= 80 && L.name.replace(/\s/g, '') !== name.replace(/\s/g, '') && o.indexOf(L.name) < 0) o.push(L.name); }); return o; }
  function jnLoad(gu) {
    if (RLOADN[gu]) return; RLOADN[gu] = 1;
    rGet(gu, 'jcnm.json').then(function (j) {
      j.j.forEach(function (t) { var J = { t: t, p: P(t[1], t[2]), m: j }; JCN.push(J); if (t[3] === 1) { var hk = Math.floor(J.p[0] / 100) + ',' + Math.floor(J.p[1] / 100); (JH[hk] = JH[hk] || []).push(J); } }); JCN.sort(function (a, b) { return (a.t[3] === 6 ? 0 : 1) - (b.t[3] === 6 ? 0 : 1) || a.t[4] - b.t[4]; });
      j.r.forEach(function (t) { RDN.push({ t: t, p: P(t[1], t[2]), a: -t[3] * Math.PI / 180 }); }); RDN.sort(function (a, b) { return a.t[4] - b.t[4]; });
      if (!JCN.src) { JCN.src = j.source; JCN.note = j.note; } RLOADN[gu] = 3; draw(); }).catch(function () { RLOADN[gu] = 2; });
  }
  function jnCard(it) { var t = it.t;
    var h = '<h3>🏷 ' + esc(t[0]) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(JTY[t[3]] || '') + '</small></h3>';
    h += row('만나는 도로', t[5] ? esc(t[5]).replace(/·/g, ' · ') : '<em>(이름 있는 도로 없음)</em>') + row('가장 큰 도로', esc(RKN[t[4]] || '-')) + row('자리', t[2].toFixed(5) + ', ' + t[1].toFixed(5));
    var on2 = osmNear(P(t[1], t[2]), t[0]); if (on2.length) h += row('다른 이름', esc(on2.join(' · ')) + ' <em>(바탕 지도 OSM·서울 C-ITS 이름 — 같은 자리를 다르게 부른다 · 현장 이름을 알면 알려 주세요)</em>');
    h += '<div class="lg-btns"><button data-radhere="' + t[1].toFixed(5) + ',' + t[2].toFixed(5) + '">📐 여기서 반경 분석</button></div>';
    return h + '<p class="desc">' + esc(JCN.note || '교차로 이름은 표준노드링크를 만드는 기관이 붙인 이름이다 — 이름난 교차로가 아니면 가까운 건물·학교 이름이 붙어 있다.') + '</p>' + src(JCN.src || '국가교통정보센터(ITS) 전국 표준노드링크'); }
  function rdCard(it) { var t = it.t;
    return '<h3>🛣 ' + esc(t[0]) + '</h3>' + row('도로 등급', esc(RKN[t[4]] || '-')) + (it.g ? row('시군구', esc(it.g)) : '') + '<p class="desc">도로 이름은 표준노드링크 구간(링크)의 도로명이다 — 「…길」은 그 대로에서 갈라진 작은 길.</p>' + src(JCN.src || '국가교통정보센터(ITS) 전국 표준노드링크'); }
  function jidxLoad() { if (JIDX) return Promise.resolve(JIDX); if (JIDXP) return JIDXP;
    JIDXP = fetch('data/r/jcnm-idx.json').then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) { JIDX = j; return j; }).catch(function () { JIDXP = null; return null; }); return JIDXP; }
  var RLOADI = {}, ITSL = [], RLOADC = {}, CCB = [], CCLIVE = null;   // v1.7.0 ITS 도로 선(v2.3.1 RLOADS → RLOADI — 안전 파일 RLOADS 와 이름이 겹쳐 한쪽을 받으면 다른 쪽을 안 받았다) · CCTV 목록(구운 것)
  function spdSpan() { var v = viewLL(); return v[2] - v[0] <= 0.16 && v[3] - v[1] <= 0.16; }
  function slLoad(gu) {
    if (RLOADI[gu]) return; RLOADI[gu] = 1;
    rGet(gu, 'itsl.json').then(function (j) {
      j.items.forEach(function (t) { var c = t[4], x = 0, y = 0, pts = [], b = [1e9, 1e9, -1e9, -1e9];
        for (var k = 0; k < c.length; k += 2) { x += c[k]; y += c[k + 1]; var q = P(x / 1e5, y / 1e5); pts.push(q); if (q[0] < b[0]) b[0] = q[0]; if (q[1] < b[1]) b[1] = q[1]; if (q[0] > b[2]) b[2] = q[0]; if (q[1] > b[3]) b[3] = q[1]; }
        ITSL.push({ id: t[0], rk: t[1], nm: t[2], ms: t[3], pts: pts, bb: b }); });
      if (!ITSL.src) ITSL.src = j.source; RLOADI[gu] = 3; draw(); }).catch(function () { RLOADI[gu] = 2; });
  }
  function ccLoad(gu) {
    if (RLOADC[gu]) return; RLOADC[gu] = 1;
    rGet(gu, 'itscctv.json').then(function (j) {
      j.items.forEach(function (t) { CCB.push(t); }); CCB.src = j.source; CCB.at = j.at; RLOADC[gu] = 3; draw(); }).catch(function () { RLOADC[gu] = 2; });
  }
  function qLoad(gu) {
    if (RLOADQ[gu]) return; RLOADQ[gu] = 1;
    rGet(gu, 'jgg.json').then(function (j) {
      j.items.forEach(function (t) { var rings = t[2].map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }), r0 = rings[0], sx = 0, sy = 0; r0.forEach(function (q) { sx += q[0]; sy += q[1]; }); JGG.push({ t: t, m: j, rings: rings, c: [sx / r0.length, sy / r0.length] }); });
      RLOADQ[gu] = 3; draw(); }).catch(function () { RLOADQ[gu] = 2; });
  }
  function jggVal(t, m) { var a = t[3] / 1e4;
    if (m === 'pop') return t[4]; if (m === 'dens') return t[4] != null && a ? t[4] / a : null; if (m === 'hh') return t[5]; if (m === 'fam') return t[6] != null ? +t[6] : null;
    if (m === 'house') return t[7]; if (m === 'corp') return t[8]; if (m === 'wrk') return t[9]; if (m === 'job') return t[9] != null && t[4] ? t[9] / t[4] : null; return null; }
  function jggFmt(v, m) { return v == null ? '자료 없음' : m === 'dens' ? Math.round(v).toLocaleString() + '명/ha' : m === 'fam' ? v.toFixed(1) + '명' : m === 'job' ? v.toFixed(2) + '배' : Math.round(v).toLocaleString() + (m === 'corp' ? '곳' : m === 'house' ? '호' : m === 'hh' ? '가구' : '명'); }
  function jggRange() { var vs = JGG.map(function (x) { return jggVal(x.t, JGGM); }).filter(function (v) { return v != null; }).sort(function (a, b) { return a - b; }); return vs.length ? [vs[Math.floor(vs.length * 0.02)], vs[Math.floor(vs.length * 0.98)]] : [0, 1]; }
  function drawJgg(dark) {
    if (!on.jgg || !JGG.length || view.s < 0.03) return; var col = JGGMS[JGGM][1], R2 = jggRange(), W0 = cv.clientWidth, H0 = cv.clientHeight;
    JGG.forEach(function (x) { var s0 = S(x.c); if (s0[0] < -300 || s0[1] < -300 || s0[0] > W0 + 300 || s0[1] > H0 + 300) return; var v = jggVal(x.t, JGGM), k = v == null ? null : Math.max(0, Math.min(1, (v - R2[0]) / ((R2[1] - R2[0]) || 1)));
      x.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = k == null ? 'rgba(148,163,184,.15)' : hexA(col, 0.06 + 0.66 * k); ctx.fill(); if (view.s > 0.12) { ctx.lineWidth = 0.6; ctx.strokeStyle = dark ? 'rgba(226,232,240,.35)' : 'rgba(30,41,59,.25)'; ctx.stroke(); } });
      hit.push({ x: s0[0], y: s0[1], r: 9, it: { kind: 'jgg', x: x } });
      if (view.s > 0.45) label(x.c, jggFmt(v, JGGM), 9.5, dark ? '#e2e8f0' : '#1f2937', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.8)'); });
  }
  function jggLegend() { if (!on.jgg) return null; var R2 = jggRange();
    return ['🧩 집계구 — ' + JGGMS[JGGM][0], '<div class="lg-btns">' + Object.keys(JGGMS).map(function (k) { return '<button data-jggm="' + k + '" class="' + (k === JGGM ? 'on' : '') + '">' + JGGMS[k][0] + '</button>'; }).join('') + '</div>' +
      (JGG.length ? grad('rgba(255,255,255,.4)', JGGMS[JGGM][1], jggFmt(R2[0], JGGM), jggFmt(R2[1], JGGM) + ' 이상') : '<small class="lg-n">확대하면(구 하나 정도) 받는다</small>') + li('rgba(148,163,184,.6)', '회색 = 통계 없음(경계 해와 통계 해가 다르거나 값이 작아 가림)', 'box') + '<small class="lg-n">집계구 = 통계청이 인구 약 500명 단위로 나눈 가장 작은 통계 구역 · 색 눈금은 받은 집계구의 2~98%</small>']; }
  function jggCard(it) {
    var x = it.x, t = x.t, M = x.m, a = t[3] / 1e4, h = '<h3>🧩 집계구 ' + esc(t[0]) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(t[1]) + '</small></h3>';
    h += row('넓이', (a >= 1 ? a.toFixed(1) + 'ha' : Math.round(t[3]).toLocaleString() + '㎡')) + row('인구', t[4] == null ? '자료 없음' : t[4].toLocaleString() + '명' + (a ? ' · ' + Math.round(t[4] / a).toLocaleString() + '명/ha' : '')) +
      row('가구', t[5] == null ? '자료 없음' : t[5].toLocaleString() + '가구' + (t[6] ? ' · 평균 ' + t[6] + '명' : '')) + row('주택', t[7] == null ? '자료 없음' : t[7].toLocaleString() + '호') +
      row('사업체 · 종사자', (t[8] == null ? '-' : t[8].toLocaleString() + '곳') + ' · ' + (t[9] == null ? '-' : t[9].toLocaleString() + '명') + (t[9] != null && t[4] ? ' <em>(종사자가 인구의 ' + (t[9] / t[4]).toFixed(t[9] < t[4] ? 2 : 1) + '배 — ' + (t[9] > 2 * t[4] ? '낮에 사람이 몰리는 일터' : t[4] > 2 * t[9] ? '주거지' : '주거·일터 섞임') + ')</em>' : ''));
    h += talk({ sido: sidoOf(M.gu), pop: t[4], wrk: t[9], corp: t[8] });
    h += '<div class="lg-btns"><button data-radhere="' + (x.c[0] / KX + LON0).toFixed(5) + ',' + (LAT0 - x.c[1] / KY).toFixed(5) + '">📐 여기서 반경 분석</button><button data-pnlhere="' + (x.c[0] / KX + LON0).toFixed(5) + ',' + (LAT0 - x.c[1] / KY).toFixed(5) + '">💰 여기서 손익 계산</button></div>';
    return h + '<p class="desc">' + esc(M.note) + '</p>' + src(M.source);
  }
  var RLOADZ = {}, SZ = [];
  function zLoad(gu) {   // v1.2.0 소진공 주요상권(공식 오픈 API storeZoneInAdmi · 서울 176 · 경기 281)
    if (RLOADZ[gu]) return; RLOADZ[gu] = 1;
    rGet(gu, 'szone.json').then(function (j) {
      j.items.forEach(function (t) { SZ.push({ t: t, m: j, c: P(t.lon, t.lat), rings: t.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }) }); }); RLOADZ[gu] = 3; draw(); }).catch(function () { RLOADZ[gu] = 2; });
  }
  function drawSz(dark) {
    if (!on.szone || !SZ.length) return; var W0 = cv.clientWidth, H0 = cv.clientHeight, col = '#b45309';
    SZ.forEach(function (x) { var s0 = S(x.c); if (s0[0] < -500 || s0[1] < -500 || s0[0] > W0 + 500 || s0[1] > H0 + 500) return;
      x.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = dark ? 'rgba(217,119,6,.16)' : 'rgba(217,119,6,.13)'; ctx.fill(); ctx.lineWidth = 1.8; ctx.setLineDash([2, 3]); ctx.strokeStyle = col; ctx.stroke(); ctx.setLineDash([]); });
      hit.push({ x: s0[0], y: s0[1], r: 12, it: { kind: 'szone', x: x } });
      if (view.s > 0.06) label(x.c, x.t.n, 10.5, '#fff', 'rgba(180,83,9,.85)'); if (view.s > 0.2) label([x.c[0], x.c[1] + 15 / view.s], '점포 ' + x.t.st.toLocaleString(), 10, dark ? '#fde68a' : '#78350f', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); });
  }
  function szCard(it) {
    var x = it.x, t = x.t, h = '<h3>🏬 ' + esc(t.n) + ' <small style="font-weight:400;color:var(--ink2)">소진공 주요상권</small></h3>';
    rentLoad();
    h += '<div class="lg-btns"><button data-radhere="' + t.lon.toFixed(5) + ',' + t.lat.toFixed(5) + '">📐 여기서 반경 분석</button></div>';
    h += row('자리', esc(t.sgg) + ' ' + esc(t.dong) + ' · 넓이 ' + man(t.area) + '㎡ · 상권번호 ' + esc(t.no)) + row('영역 기준', esc(t.dt) + ' <em>(소진공 · 그 뒤 변동 없음)</em>');
    var ha = t.area / 1e4; h += row('등록 점포', t.st.toLocaleString() + '곳' + (ha ? ' · ' + (t.st / ha).toFixed(1) + '곳/ha' : '') + (t.f1[1] ? ' · 1층 ' + pct(t.f1[0], t.f1[1]) + '% <em>(층이 적힌 ' + t.f1[1].toLocaleString() + '곳 중)</em>' : ''));
    if (t.L.length) h += '<div class="cap">업종 대분류별 등록 점포(곳 · 영역 안)</div>' + bar(t.L.map(function (q) { return q[1]; }), '#d97706', t.L.map(function (q) { return q[0].slice(0, 2); }));
    if (t.S.length) h += row('많은 업종', t.S.map(function (q) { return esc(q[0]) + ' ' + q[1]; }).join(' · '));
    h += rentRows(x.c, '임대료(가까운 표본)');
    return h + '<p class="desc">' + esc(x.m.note) + '</p>' + src(x.m.source);
  }
  var TCB = {}, RLOADG = {}, GGT = [], GGM = 'amt', RLOADH2 = {}, HL = {}, HLALL = false;
  function hlLoad(gu) {   // v1.1.0 서울 골목상권 배후지(상권분석서비스 영역-상권배후지 OA-22159)
    if (RLOADH2[gu] && RLOADH2[gu].then) return RLOADH2[gu]; if (RLOADH2[gu]) return Promise.resolve();
    RLOADH2[gu] = rGet(gu, 'trdhl.json').then(function (j) {
      j.trdhl.forEach(function (t) { HL[t.cd] = { t: t, m: j, rings: t.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }) }; });
      RLOADH2[gu] = 3; draw(); if (sel && sel.it.kind === 'trd' && HL[sel.it.x.t.cd]) show(sel.it); }).catch(function () { RLOADH2[gu] = 2; });
    return RLOADH2[gu];
  }
  function drawHl(dark) {   // 고른 골목상권의 배후지(주황 점선) · 범례에서 「배후지 모두」
    if (!on.trd) return; var cds = [];
    if (HLALL) cds = Object.keys(HL); else if (sel && sel.it.kind === 'trd' && HL[sel.it.x.t.cd]) cds = [sel.it.x.t.cd];
    cds.forEach(function (cd) { var H = HL[cd];
      H.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = dark ? 'rgba(251,146,60,.10)' : 'rgba(251,146,60,.12)'; ctx.fill(); ctx.lineWidth = 1.6; ctx.setLineDash([6, 4]); ctx.strokeStyle = '#ea580c'; ctx.stroke(); ctx.setLineDash([]); }); });
  }
  function hlRows(t) {   // 본체 ↔ 배후지 — 수요의 성격
    var H = HL[t.cd]; if (!H) { var gq = (t.gu || '') ; if (gq && !RLOADH2[gq]) hlLoad(gq); return t.se === '골목상권' ? '<div class="dh">🏘 배후지</div>' + row('배후지', '<em>받는 중…</em>') : ''; }
    var b = H.t, QS = H.m.qs || {}, qk = function (k) { var q = QS[k]; return q ? q.slice(0, 4) + '년 ' + q[4] + '분기' : ''; }, aptH = function (x) { return !x ? 0 : x.rep && x.rep[10] ? x.rep[10] : x.apt ? x.apt.slice(1, 6).reduce(function (a, v) { return a + v; }, 0) : 0; }, sum = function (ind, k) { return (ind || []).reduce(function (a, r) { return a + r[k]; }, 0); }, h = '<div class="dh">🏘 본체 ↔ 배후지 — 이 골목상권을 받치는 생활 구역</div>';
    var a0 = sum(t.ind, 1), a1 = sum(b.ind, 1), wk0 = sum(t.ind, 17) + sum(t.ind, 18) + sum(t.ind, 19) + sum(t.ind, 20) + sum(t.ind, 21), we0 = sum(t.ind, 22) + sum(t.ind, 23);
    h += '<table class="it"><tr><th></th><th>본체(상권)</th><th>배후지</th></tr>' +
      '<tr><td>넓이</td><td>' + man(t.area) + '㎡</td><td>' + man(b.area) + '㎡</td></tr>' +
      '<tr><td>카드 매출(한 달)</td><td>' + won(a0) + '</td><td>' + won(a1) + '</td></tr>' +
      '<tr><td>점포</td><td>' + (t.stor || []).reduce(function (a, s2) { return a + s2[1]; }, 0) + '곳</td><td>' + (b.stor || []).reduce(function (a, s2) { return a + s2[1]; }, 0) + '곳</td></tr>' +
      '<tr><td>상주인구</td><td>' + (t.rep ? man(t.rep[0]) : '-') + '</td><td>' + (b.rep ? man(b.rep[0]) : '-') + '</td></tr>' +
      '<tr><td>가구(아파트)</td><td>' + (t.rep ? man(t.rep[9]) + '(' + (aptH(t) ? man(aptH(t)) : '-') + ')' : '-') + '</td><td>' + (b.rep ? man(b.rep[9]) + '(' + man(aptH(b)) + ')' : '-') + '</td></tr>' +
      '<tr><td>하루 유동(평균)</td><td>' + (t.flp ? man(t.flp[0] / 91) : '-') + '</td><td>' + (b.flp ? man(b.flp[0] / 91) : '-') + '</td></tr>' +
      '<tr><td>직장인구</td><td>' + (t.wrc ? man(t.wrc[0]) : '-') + '</td><td><em>자료 없음</em></td></tr></table>';
    var W = t.wrc ? t.wrc[0] : 0, R = (b.rep ? b.rep[0] : 0) + (t.rep ? t.rep[0] : 0), wkp = pct(wk0, wk0 + we0);
    var kind = !W && !R ? '판단 못 함' : W >= 2 * R ? '🏢 <b>직장 수요</b> — 직장인구가 상주인구의 두 배 넘음 · 평일 점심·회식 쪽' : R >= 2 * W ? '🏠 <b>주거 수요</b> — 배후지 가구가 받친다' + (b.rep && b.rep[9] ? ' · 아파트 가구 약 ' + Math.min(100, pct(aptH(b), b.rep[9])) + '%' : '') : '↔ <b>직장·주거 혼합</b>';
    h += row('수요 성격', kind + ' <em>(본체 매출 평일 ' + wkp + '% · 주말 ' + (100 - wkp) + '% · 문턱 2배는 설계값)</em>');
    if (b.rep) h += '<div class="cap">배후지 상주인구 연령대(명 · 10대 … 60세 이상)</div>' + bar(b.rep.slice(3, 9), '#ea580c', LB_AGE6) + row('배후지 가구', man(b.rep[9]) + ' · 아파트 약 ' + man(aptH(b)) + ' <em>(' + qk('rep') + ' · 아파트 가구는 아파트-배후지 면적별 가구 합 — 상주인구 자료의 아파트 칸이 비어 있다)</em>');
    if (b.apt && b.apt[0]) { var A = b.apt; h += row('배후지 아파트', A[0] + '단지 · 평균 ' + A[13] + '㎡ · 평균 시가 ' + won(A[14]) + ' <em>(아파트-상권배후지 · ' + qk('apt') + ')</em>') +
        '<div class="cap">배후지 아파트 시가별 가구(가구 · 1억 미만 … 6억 이상)</div>' + bar(A.slice(6, 13), '#f97316', ['1억↓', '1억', '2억', '3억', '4억', '5억', '6억↑']) +
        '<div class="cap">배후지 아파트 면적별 가구(가구 · 66㎡ 미만 … 165㎡ 이상)</div>' + bar(A.slice(1, 6), '#fb923c', ['66↓', '66', '99', '132', '165↑']); }
    if (b.ncm && b.ncm[0]) { var N = b.ncm, NL = ['식료품', '의류·신발', '생활용품', '의료', '교통', '여가', '문화', '교육', '유흥'];
      h += row('배후지 소비', '지출 총액 ' + won(N[0]) + (N[10] ? ' · 월평균 소득 ' + won(N[10]) : '') + ' <em>(소비-상권배후지 · ' + qk('ncm') + ' — 그 뒤 분기는 비어 있다 · 자료 값 그대로)</em>') +
        '<div class="cap">배후지 지출 갈래(원 · 식료품 … 유흥)</div>' + bar(N.slice(1, 10), '#c2410c', NL, 'w'); }
    if (b.ind && b.ind.length) { var tops = b.ind.slice().sort(function (p2, q2) { return q2[1] - p2[1]; }).slice(0, 5);
      h += row('배후지 매출 많은 업종', tops.map(function (r) { return esc(r[0]) + ' ' + won(r[1]); }).join(' · ')); }
    if (b.stor && b.stor.length) h += row('배후지 점포', b.stor.reduce(function (a, s2) { return a + s2[1]; }, 0) + '곳 · 개업 ' + b.stor.reduce(function (a, s2) { return a + s2[3]; }, 0) + ' · 폐업 ' + b.stor.reduce(function (a, s2) { return a + s2[4]; }, 0));
    return h + '<p class="desc">' + esc(H.m.note) + '</p>' + src(H.m.source);
  }
  function gLoad(gu, then) {   // v1.1.0 경기 상권 — 경기데이터드림 발달·골목상권 영역 + 업종별 추정매출(한 분기)
    if (RLOADG[gu] === 3 || RLOADG[gu] === 2) { if (then) then(); return Promise.resolve(); } if (RLOADG[gu] && RLOADG[gu].then) return RLOADG[gu];
    RLOADG[gu] = rGet(gu, 'ggtrd.json').then(function (j) {
      j.items.forEach(function (t) { var rings = t.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); var r0 = rings[0], a = 0;
        for (var i = 0, k = r0.length - 1; i < r0.length; k = i++) a += (r0[k][0] + r0[i][0]) * (r0[k][1] - r0[i][1]);
        GGT.push({ t: t, rings: rings, c: P(t.lon, t.lat), area: Math.abs(a / 2), m: j }); });
      RLOADG[gu] = 3; draw(); }).catch(function () { RLOADG[gu] = 2; });
    return RLOADG[gu];
  }
  var GGMS = { amt: ['💰 분기 매출', '#0f766e'], atv: ['🧾 객단가(건당)', '#0d9488'], perstor: ['🏬 점포당 매출', '#115e59'], stor: ['🏪 점포 수', '#14b8a6'], dens: ['📍 점포 밀도', '#2dd4bf'] };
  function ggVal(x, m) { var t = x.t, T = t.tot;
    if (m === 'amt') return T ? T[0] : null; if (m === 'atv') return T && T[1] ? T[0] * 1e4 / T[1] : null;
    if (m === 'perstor') return T && t.st ? T[0] / t.st : null; if (m === 'stor') return t.st || 0; if (m === 'dens') return x.area ? t.st / (x.area / 1e4) : 0; return null; }
  function ggFmt(v, m) { return v == null ? '자료 없음' : m === 'amt' ? '분기 ' + won(v) : m === 'perstor' ? '점포당 분기 ' + won(v) : m === 'atv' ? Math.round(v).toLocaleString() + '원' : m === 'dens' ? v.toFixed(1) + '곳/ha' : Math.round(v) + '곳'; }
  function drawGgt(dark) {
    if (!on.trd || !GGT.length) return; var col = GGMS[GGM][1], vs = GGT.map(function (x) { return ggVal(x, GGM); }), mx = Math.max.apply(null, vs.filter(function (v) { return v != null; }).concat([1]));
    GGT.forEach(function (x, k) { var v = vs[k], s0 = S(x.c); if (s0[0] < -400 || s0[1] < -400 || s0[0] > cv.clientWidth + 400 || s0[1] > cv.clientHeight + 400) return;
      x.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = v == null ? 'rgba(148,163,184,.18)' : hexA(col, 0.08 + 0.62 * Math.sqrt(v / mx)); ctx.fill(); ctx.lineWidth = x.t.k === 'dev' ? 2.2 : 1.1; ctx.strokeStyle = col; ctx.stroke(); });
      hit.push({ x: s0[0], y: s0[1], r: 12, it: { kind: 'ggt', x: x } });
      if (view.s > 0.11) { label(x.c, x.t.n, 11, '#fff', hexA(col, 0.85)); if (view.s > 0.2) label([x.c[0], x.c[1] + 16 / view.s], ggFmt(v, GGM), 10, dark ? '#e2e8f0' : '#1f2937', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); } });
  }
  function ggLegend() {
    if (!on.trd || !GGT.length) return ''; var vs = GGT.map(function (x) { return ggVal(x, GGM); }).filter(function (v) { return v != null; });
    return '<div class="lg-btns" style="margin-top:6px"><b style="font-size:12px">경기 상권</b> ' + Object.keys(GGMS).map(function (k) { return '<button data-ggm="' + k + '" class="' + (k === GGM ? 'on' : '') + '">' + GGMS[k][0] + '</button>'; }).join('') + '</div>' +
      (vs.length ? grad('rgba(255,255,255,.4)', GGMS[GGM][1], ggFmt(Math.min.apply(null, vs), GGM), ggFmt(Math.max.apply(null, vs), GGM)) : '') + li('#0f766e', '청록 = 경기(발달 굵은 테 · 골목 가는 테 · 회색 = 매출 자료 없음)', 'line') + '<small class="lg-n">경기는 업종 이름이 한국표준산업분류(10차)라 서울의 업종 고르기·시간대·연령 기준이 없다 — 한 분기 값</small>';
  }
  function ggtCard(it) {
    var x = it.x, t = x.t, M = x.m, T = t.tot, h = '<h3>🏪 ' + esc(t.n) + ' <small style="font-weight:400;color:var(--ink2)">경기 ' + (t.k === 'dev' ? '발달상권' : '골목상권') + '</small></h3>';
    rentLoad();
    h += '<div class="lg-btns"><button data-radhere="' + t.lon.toFixed(5) + ',' + t.lat.toFixed(5) + '">📐 여기서 반경 분석</button></div>';
    h += row('자리', esc(t.dong) + ' · 넓이 약 ' + man(x.area) + '㎡') + row('점포', t.st + '곳 <em>(경기도시장상권진흥원 영역 자료)</em>');
    if (T) { h += row('카드 매출(추정)', '<b>분기 ' + won(T[0]) + '</b> · 결제 ' + man(T[1]) + '건 <em>(' + esc(M.quarter.replace(' ', '년 ')) + '분기 · 자료 값 그대로)</em>') +
        row('객단가', (T[1] ? Math.round(T[0] * 1e4 / T[1]).toLocaleString() : '-') + '원(건당 결제)') + (t.st ? row('점포당', '분기 ' + won(T[0] / t.st) + ' <em>(매출 ÷ 영역 점포 수)</em>') : '');
      h += '<div class="cap">업종별 카드 매출(원 · 한 분기 · 매출 많은 업종 15 · 한국표준산업분류 10차 — 번호는 아래 목록)</div>' + bar(t.ind.map(function (r) { return r[1]; }), '#0f766e', t.ind.map(function (r, i) { return String(i + 1); }), 'w') +
        '<div class="lst">' + t.ind.map(function (r, i) { return '<div><b>' + (i + 1) + '. ' + esc(r[0]) + '</b><span>' + won(r[1]) + ' · ' + man(r[2]) + '건 · 건당 ' + (r[2] ? Math.round(r[1] * 1e4 / r[2]).toLocaleString() : '-') + '원</span></div>'; }).join('') + '</div>'; }
    else if (t.dup) h += row('카드 매출', '<em>같은 이름의 상권이 여럿이라 어느 영역의 매출인지 가릴 수 없어 붙이지 않았다</em>');
    else h += row('카드 매출', '이 상권은 매출 자료가 없다');
    if (t.indt && t.indt.length) h += row('주요 업종', esc(t.indt.join(' · ')) + ' <em>(영역 자료의 업종 목록)</em>');
    h += rentRows(x.c, '임대료(가까운 표본)');
    return h + '<p class="desc">' + esc(M.note) + '</p>' + src(M.source);
  }
  function tLoad(gu, then) {   // v0.10.92 구의 상권(서울시 상권분석서비스) — 서초는 기존 trdar-seocho 를 이 파일(1년 전 매출·점포 포함)로 갈아 끼운다
    if (RLOADT[gu] === 3 || RLOADT[gu] === 2) { if (then) then(); return; } if (then) (TCB[gu] = TCB[gu] || []).push(then); if (RLOADT[gu]) return; RLOADT[gu] = 1;
    var fin = function () { var L = TCB[gu] || []; TCB[gu] = []; L.forEach(function (f) { f(); }); };
    rGet(gu, 'trdar.json').then(function (j) { tAdd(j); RLOADT[gu] = 3; fin(); draw(); }).catch(function () { RLOADT[gu] = 2; fin(); });
  }
  function rLoadGu(gu) {   // 행정동 지역 파일 하나 — 약속으로(반경 분석이 기다린다)
    if (gu === '11650') return Promise.resolve(); if (RLOAD[gu] && RLOAD[gu].then) return RLOAD[gu]; if (RLOAD[gu]) return Promise.resolve();
    RLOAD[gu] = rGet(gu, 'dong.json').then(function (j) { rAdd(j); draw(); }).catch(function () { RLOAD[gu] = 2; }); return RLOAD[gu];
  }
  function tAdd(j) {
    var by = {}; TRD.forEach(function (x, i) { by[x.t.cd] = i; });
    j.trdar.forEach(function (t) { var o = trdItem(t, j); if (by[t.cd] != null) TRD[by[t.cd]] = o; else TRD.push(o); });
    trdList();
    if (TWANT) TRD.forEach(function (x) { if (TWANT && x.t.cd === TWANT.cd) { var it = { kind: 'trd', x: x, biz: TWANT.biz }; TWANT = null; var s2 = S(x.c); sel = { x: s2[0], y: s2[1], r: 12, it: it }; show(it); } });
  }
  function inViewBox(d) { var a = M(0, 0), b = M(cv.clientWidth, cv.clientHeight); return !(d.box[1] < a[0] || d.box[0] > b[0] || d.box[3] < a[1] || d.box[2] > b[1]); }
  function allDong() { return DONG.concat(RDONG); }
  function prep() {
    if (D.dong) DONG = D.dong.dong.map(function (d) {
      var polys = d.polys.map(function (Pg) { return Pg.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); });
      var box = [1e9, -1e9, 1e9, -1e9], sx = 0, sy = 0, n = 0;
      polys.forEach(function (Pg) { Pg[0].forEach(function (q) { box[0] = Math.min(box[0], q[0]); box[1] = Math.max(box[1], q[0]); box[2] = Math.min(box[2], q[1]); box[3] = Math.max(box[3], q[1]); sx += q[0]; sy += q[1]; n++; }); });
      var pop = D.pop && D.pop.dong ? D.pop.dong.filter(function (x) { return x.name === d.name; })[0] : null;
      return { name: d.name, polys: polys, box: box, c: labelPt(polys, box), pop: pop };
    });
    if (D.roads) Object.keys(D.roads.roads).forEach(function (nm) { var r = D.roads.roads[nm]; ROADS.push({ name: nm, axis: r.axis, pts: r.pts.map(function (q) { return fullM(q[0], q[1]); }) }); });
    // 실제 교차점 25곳 — 두 도로 중심선이 만나는 자리(게임과 같은 도로 쌍). 이름은 서초구 1:1 지도의 이름(v0.10.41 바로잡음)
    var F = D.full; F2 = F;
    if (F && D.roads) {
      for (var i = 0; i < F.roadNamesV.length; i++) for (var j = 0; j < F.roadNamesH.length; j++) {
        var V = D.roads.roads[F.roadNamesV[i]], H = D.roads.roads[F.roadNamesH[j]]; if (!V || !H) continue;
        var x = F.grid.xs[i], z = F.grid.zs[j];
        for (var it = 0; it < 30; it++) { z = along(H.pts, 0, x); x = along(V.pts, 1, z); }
        var pr = F.roadNamesV[i] + '×' + F.roadNamesH[j], br = D.pop && D.pop.byRoads ? D.pop.byRoads[pr] : null;
        var xr = D.xing && D.xing.nodes ? D.xing.nodes.filter(function (q) { return q.i === i && q.j === j; })[0] : null;
        NODES.push({ i: i, j: j, p: xr && xr.met ? P(xr.lon, xr.lat) : fullM(x, z), name: (xr && xr.name) || (F.nodeNames && F.nodeNames[i + ',' + j]) || (F.roadNamesV[i] + ' · ' + F.roadNamesH[j]), pair: pr, dong: br,
          real: xr ? !!xr.met : true, why: xr && xr.why, gap: xr ? xr.gapM : null, measured: !!xr, sig: xr && xr.sigName ? { name: xr.sigName, no: xr.sigNo, m: xr.sigM } : null, nameSrc: xr && xr.nameSource });
      }
    }
    // 서초구와 맞닿은 강남·동작·관악구 동 — 경계와 이름만(자료는 서초구만 자세하다)
    if (D.near && D.near.dong) NEAR = D.near.dong.map(function (d) {
      var polys = d.polys.map(function (Pg) { return Pg.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); });
      var box = [1e9, -1e9, 1e9, -1e9]; polys.forEach(function (Pg) { Pg[0].forEach(function (q) { box[0] = Math.min(box[0], q[0]); box[1] = Math.max(box[1], q[0]); box[2] = Math.min(box[2], q[1]); box[3] = Math.max(box[3], q[1]); }); });
      return { name: d.name, gu: d.gu, polys: polys, box: box, c: labelPt(polys, box), near: true };
    });
    if (D.gu) (D.gu.districts || D.gu.gu || []).forEach(function (g) { var rings = g.rings || g.lines || (g.coords ? [g.coords] : []); rings.forEach(function (r) { GU.push({ name: g.name, pts: r.map(function (q) { return P(q[0], q[1]); }) }); }); });
  }
  function prepBld() { if (!D.bld) return; BLD = (D.bld.buildings || []).map(function (b) { return { p: (b.p || []).map(function (q) { return fullM(q[0], q[1]); }), n: b.n || '', lv: b.lv || 0 }; }).filter(function (b) { return b.p.length > 2; }); }
  function along(pts, ax, t) {   // 중심선에서 주축 값 t 의 가로 값(ax 0: x 로 z 를 · ax 1: z 로 x 를)
    var s = pts.slice().sort(function (a, b) { return a[ax] - b[ax]; }), o = 1 - ax;
    if (t <= s[0][ax]) return s[0][o];
    for (var k = 1; k < s.length; k++) if (t <= s[k][ax]) { var a = s[k - 1], b = s[k], u = (t - a[ax]) / ((b[ax] - a[ax]) || 1); return a[o] + (b[o] - a[o]) * u; }
    return s[s.length - 1][o];
  }
  function labelPt(polys, box) {   // 이름 자리 — 가장 큰 고리의 무게중심(안에 안 들면 상자 가운데)
    var best = null, ba = 0;
    polys.forEach(function (Pg) { var r = Pg[0], a = 0, cx = 0, cy = 0; for (var i = 0, j = r.length - 1; i < r.length; j = i++) { var f = r[j][0] * r[i][1] - r[i][0] * r[j][1]; a += f; cx += (r[j][0] + r[i][0]) * f; cy += (r[j][1] + r[i][1]) * f; } if (Math.abs(a) > ba) { ba = Math.abs(a); best = [cx / (3 * a), cy / (3 * a)]; } });
    best = best || [(box[0] + box[1]) / 2, (box[2] + box[3]) / 2];
    // 오목한 동은 무게중심이 밖(옆 동)에 떨어진다 — 그러면 그 높이의 가로줄에서 가장 긴 안쪽 구간의 가운데로
    var R = null, ra = 0; polys.forEach(function (Pg) { var r = Pg[0], a = 0; for (var i = 0, j = r.length - 1; i < r.length; j = i++) a += r[j][0] * r[i][1] - r[i][0] * r[j][1]; if (Math.abs(a) > ra) { ra = Math.abs(a); R = r; } });
    if (!R || inRing(R, best[0], best[1])) return best;
    var y0 = Infinity, y1 = -Infinity; R.forEach(function (q) { y0 = Math.min(y0, q[1]); y1 = Math.max(y1, q[1]); });
    var pick = best, bw = 0;
    for (var k = 1; k < 20; k++) {
      var y = y0 + (y1 - y0) * k / 20, xs = [];
      for (var i = 0, j = R.length - 1; i < R.length; j = i++) { var a1 = R[j], b1 = R[i]; if ((a1[1] > y) !== (b1[1] > y)) xs.push(a1[0] + (y - a1[1]) * (b1[0] - a1[0]) / (b1[1] - a1[1])); }
      xs.sort(function (p, q) { return p - q; });
      for (var m = 0; m + 1 < xs.length; m += 2) { var w = xs[m + 1] - xs[m], wt = w * (1 - Math.abs(k - 10) / 14); if (wt > bw) { bw = wt; pick = [(xs[m] + xs[m + 1]) / 2, y]; } }
    }
    return pick;
  }
  function baseLL(gx, gz) {   // 기본 지도 아핀 공간(TAAS gx·gz) → 위경도(식을 거꾸로 푼다)
    var W = D.base && D.base.wgs84; if (!W) return null;
    var a = W.x[0], b = W.x[1], c = W.z[0], d = W.z[1], det = a * d - b * c, px = gx - W.x[2], pz = gz - W.z[2];
    return [(d * px - b * pz) / det + W.lon0, (-c * px + a * pz) / det + W.lat0];
  }
  function nodeAt(ij) { for (var k = 0; k < NODES.length; k++) if (NODES[k].i === ij[0] && NODES[k].j === ij[1]) return NODES[k]; return null; }

  // ---------- 보기 ----------
  // 처음에는 간선 격자(교차로 25곳)를 채우고, 「전체」는 격자 ↔ 서초구 전체를 번갈아 보인다
  var fitAll = false;
  function fit() {
    var W = cv.clientWidth, H = cv.clientHeight, b = [1e9, -1e9, 1e9, -1e9];
    if (!fitAll && NODES.length) NODES.forEach(function (n) { b[0] = Math.min(b[0], n.p[0] - 250); b[1] = Math.max(b[1], n.p[0] + 250); b[2] = Math.min(b[2], n.p[1] - 250); b[3] = Math.max(b[3], n.p[1] + 250); });
    else DONG.forEach(function (d) { b[0] = Math.min(b[0], d.box[0]); b[1] = Math.max(b[1], d.box[1]); b[2] = Math.min(b[2], d.box[2]); b[3] = Math.max(b[3], d.box[3]); });
    if (b[0] > b[1]) b = [-4000, 4000, -4000, 4000];
    view.cx = (b[0] + b[1]) / 2; view.cy = (b[2] + b[3]) / 2; view.s = Math.min(W / (b[1] - b[0]), H / (b[3] - b[2])) * 0.92;
  }
  function S(q) { return [(q[0] - view.cx) * view.s + cv.clientWidth / 2, (q[1] - view.cy) * view.s + cv.clientHeight / 2]; }
  function M(sx, sy) { return [(sx - cv.clientWidth / 2) / view.s + view.cx, (sy - cv.clientHeight / 2) / view.s + view.cy]; }
  function resize() { cv.width = cv.clientWidth * DPR; cv.height = cv.clientHeight * DPR; draw(); }
  window.addEventListener("m2dresize", resize);

  var LINE_C = { '2': '#00a84d', '3': '#ef7c1c', '4': '#00a5de', '7': '#747f00', '9': '#bdb092', '신': '#d4003b' };   // 노선 색(번호만 적는다 · 로고 없음)
  var F2 = null;
  var PAL = ['#dbeafe', '#fce7f3', '#dcfce7', '#fef9c3', '#ede9fe', '#ffedd5', '#cffafe', '#fee2e2', '#e0e7ff'];
  function path(pts) { ctx.beginPath(); pts.forEach(function (q, k) { var s = S(q); if (k) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); }); }
  function zk() { return Math.max(0.55, Math.min(1.35, view.s / 0.3)); }
  function dot(q, r, fill, stroke, item) { var s = S(q); if (s[0] < -40 || s[1] < -40 || s[0] > cv.clientWidth + 40 || s[1] > cv.clientHeight + 40) return; r = r * zk(); ctx.beginPath(); ctx.arc(s[0], s[1], r, 0, Math.PI * 2); ctx.fillStyle = fill; ctx.fill(); if (stroke) { ctx.lineWidth = 1.5; ctx.strokeStyle = stroke; ctx.stroke(); } if (item) hit.push({ x: s[0], y: s[1], r: Math.max(r, 9), it: item }); }
  function halo(q, text, size, color, dark) { var s0 = S(q); ctx.font = 'bold ' + size + 'px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round'; ctx.lineWidth = 3.5; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(text, s0[0], s0[1]); ctx.fillStyle = color; ctx.fillText(text, s0[0], s0[1]); }   // 글씨만(바탕 상자 없이 테두리 빛)
  function label(q, text, size, color, bg) { var s = S(q); ctx.font = 'bold ' + size + 'px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; if (bg) { var w = ctx.measureText(text).width; ctx.fillStyle = bg; ctx.fillRect(s[0] - w / 2 - 3, s[1] - size / 2 - 2, w + 6, size + 4); } ctx.fillStyle = color; ctx.fillText(text, s[0], s[1]); }
  // ---------- 🛰 브이월드 배경지도(v1.5.0) — 켠 사람만 api.vworld.kr 에서 256px 조각을 받는다 · 끄면 통신 0 ----------
  // 키는 저장소에 없다. 기기마다 「🔑 키 넣기」 또는 주소 #vwkey=… 로 한 번 넣으면 그 기기에만 남는다(tg_map2d_vwkey).
  var VWKEY = '', VWT = {}, VWN = 0, VWQ = 0, VWBAD = 0, VWOK = 0, VWM = 'Satellite';
  var VWMS = { Satellite: '🛰 위성', Hybrid: '🛰 위성+이름', Base: '🗺 일반', gray: '◻ 회색', midnight: '🌙 야간' };
  try { var vw0 = localStorage.getItem('tg_map2d_vw'); if (vw0 && VWMS[vw0]) VWM = vw0; VWKEY = localStorage.getItem('tg_map2d_vwkey') || ''; } catch (e) {}
  (function () { var m = /[#&]vwkey=([A-Za-z0-9-]{8,80})/.exec(location.hash); if (!m) return; VWKEY = m[1]; try { localStorage.setItem('tg_map2d_vwkey', VWKEY); } catch (e) {}
    var h = location.hash.replace(/[#&]vwkey=[A-Za-z0-9-]+/, '').replace(/^&/, '#'); try { history.replaceState(null, '', location.pathname + location.search + (h.length > 1 ? (h[0] === '#' ? h : '#' + h) : '')); } catch (e) {} on.vw = true; })();
  function vwSetKey() { var k = prompt('브이월드 인증키를 붙여 넣으세요(vworld.kr → 마이페이지 → 인증키 관리). 이 기기에만 저장됩니다. 비우면 지웁니다.', VWKEY || ''); if (k == null) return;
    VWKEY = (k || '').replace(/\s+/g, ''); VWT = {}; VWBAD = VWOK = 0; try { if (VWKEY) localStorage.setItem('tg_map2d_vwkey', VWKEY); else localStorage.removeItem('tg_map2d_vwkey'); } catch (e) {} draw(); }
  function vwLx(lon, z) { return (lon + 180) / 360 * Math.pow(2, z); }
  function vwLy(lat, z) { var r = lat * Math.PI / 180; return (1 - Math.log(Math.tan(r) + 1 / Math.cos(r)) / Math.PI) / 2 * Math.pow(2, z); }
  function vwLon(x, z) { return x / Math.pow(2, z) * 360 - 180; }
  function vwLat(y, z) { var n = Math.PI * (1 - 2 * y / Math.pow(2, z)); return Math.atan((Math.exp(n) - Math.exp(-n)) / 2) * 180 / Math.PI; }
  function vwTile(lay, z, x, y) {
    var k = lay + '/' + z + '/' + y + '/' + x, t = VWT[k];
    if (t) { t.u = ++VWN; return t.ok ? t : null; }
    var ks = Object.keys(VWT); if (ks.length > 500) ks.sort(function (a, b) { return VWT[a].u - VWT[b].u; }).slice(0, 150).forEach(function (q) { delete VWT[q]; });
    t = VWT[k] = { im: new Image(), ok: false, u: ++VWN };
    t.im.onload = function () { t.ok = true; VWOK++; if (!VWQ) VWQ = requestAnimationFrame(function () { VWQ = 0; draw(); }); };
    t.im.onerror = function () { t.bad = 1; VWBAD++; if (VWBAD === 4 && !VWOK && document.body.classList.contains('legon')) legend(); };
    t.im.src = 'https://api.vworld.kr/req/wmts/1.0.0/' + VWKEY + '/' + lay + '/' + z + '/' + y + '/' + x + '.' + (lay === 'Satellite' ? 'jpeg' : 'png');
    return null;
  }
  function drawVw() {
    if (!on.vw || !VWKEY) return false;
    var W = cv.clientWidth, H = cv.clientHeight, a = M(0, 0), b = M(W, H);
    var lonA = a[0] / KX + LON0, lonB = b[0] / KX + LON0, latA = LAT0 - a[1] / KY, latB = LAT0 - b[1] / KY;
    var z = Math.round(Math.log(156543.03 * Math.cos(LAT0 * Math.PI / 180) * view.s * Math.min(2, DPR)) / Math.LN2); z = Math.max(7, Math.min(19, z));
    (VWM === 'Hybrid' ? ['Satellite', 'Hybrid'] : [VWM]).forEach(function (lay) {
      var x0 = Math.floor(vwLx(lonA, z)), x1 = Math.floor(vwLx(lonB, z)), y0 = Math.floor(vwLy(latA, z)), y1 = Math.floor(vwLy(latB, z));
      if ((x1 - x0 + 1) * (y1 - y0 + 1) > 160) return;
      for (var x = x0; x <= x1; x++) for (var y = y0; y <= y1; y++) {
        var p0 = S(P(vwLon(x, z), vwLat(y, z))), p1 = S(P(vwLon(x + 1, z), vwLat(y + 1, z))), w = p1[0] - p0[0] + 0.6, h = p1[1] - p0[1] + 0.6, t = vwTile(lay, z, x, y);
        if (t) { ctx.drawImage(t.im, p0[0], p0[1], w, h); continue; }
        if (lay === 'Hybrid') continue;
        for (var dz = 1; dz <= 5; dz++) { var tk = VWT[lay + '/' + (z - dz) + '/' + (y >> dz) + '/' + (x >> dz)]; if (tk && tk.ok) { var n = 1 << dz, sw = 256 / n; ctx.drawImage(tk.im, (x - ((x >> dz) << dz)) * sw, (y - ((y >> dz) << dz)) * sw, sw, sw, p0[0], p0[1], w, h); break; } }
      }
    });
    if (VWOK) { ctx.font = '10px system-ui, sans-serif'; ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillStyle = 'rgba(255,255,255,.85)'; ctx.fillRect(4, 56, 118, 15); ctx.fillStyle = '#1f2937'; ctx.fillText('배경 © 브이월드(국토교통부)', 7, 58); }
    return true;
  }
  function vwLegend() { if (!on.vw) return null;
    var msg = !VWKEY ? '<small class="lg-n" style="color:#b91c1c">키가 아직 없다 — 「🔑 키 넣기」에 브이월드 인증키를 넣으면 이 기기에서 보인다(저장소·다른 기기로는 안 간다)</small>'
      : (VWBAD >= 4 && !VWOK) ? '<small class="lg-n" style="color:#b91c1c">조각을 못 받았다 — 인터넷·키 확인. 키는 340patrolman.github.io 에만 묶여 있어 다른 주소(PC 시험 등)에서는 안 열린다</small>' : '';
    return ['🛰 배경지도 — 브이월드', '<div class="lg-btns">' + Object.keys(VWMS).map(function (k) { return '<button data-vwm="' + k + '" class="' + (k === VWM ? 'on' : '') + '">' + VWMS[k] + '</button>'; }).join('') + '<button data-vwkey="1">🔑 ' + (VWKEY ? '키 바꾸기' : '키 넣기') + '</button></div>' + msg +
      '<small class="lg-n">국토교통부 브이월드(vworld.kr) 배경지도 · 위성 = 항공사진 · 인터넷이 있을 때만 보인다(끄면 통신 0) · 위성 위에서는 행정동 색을 옅게 · 「🗺 바탕」·「🏢 건물」을 끄면 사진이 더 잘 보인다</small>']; }
  // ---------- 📡 실시간 층(v1.6.0) — 켠 사람의 폰이 그때그때 직접 받는다 · 끄면 통신 0 · 받은 값은 메모리에만(저장 안 함) ----------
  // 키는 저장소에 없다. 기기마다 범례 「🔑 ITS 키」 또는 주소 #itskey=… 로 한 번 넣으면 그 기기 tg_map2d_keys 에만 남는다.
  var LK = {}, LIVE = { ev: null, wx: null }, LIVEW = 0;
  try { LK = JSON.parse(localStorage.getItem('tg_map2d_keys') || '{}') || {}; } catch (e) {}
  (function () { var m = /[#&]itskey=([A-Za-z0-9-]{8,80})/.exec(location.hash); if (!m) return; LK.its = m[1]; try { localStorage.setItem('tg_map2d_keys', JSON.stringify(LK)); } catch (e) {}
    var h = location.hash.replace(/[#&]itskey=[A-Za-z0-9-]+/, '').replace(/^&/, '#'); try { history.replaceState(null, '', location.pathname + location.search + (h.length > 1 ? (h[0] === '#' ? h : '#' + h) : '')); } catch (e) {} on.lev = true; })();
  (function () { var m = /[#&]dgkey=([A-Za-z0-9%+\/=_-]{20,200})/.exec(location.hash); if (!m) return; LK.dgk = decodeURIComponent(m[1]); try { localStorage.setItem('tg_map2d_keys', JSON.stringify(LK)); } catch (e) {}
    var h = location.hash.replace(/[#&]dgkey=[A-Za-z0-9%+\/=_-]+/, '').replace(/^&/, '#'); try { history.replaceState(null, '', location.pathname + location.search + (h.length > 1 ? (h[0] === '#' ? h : '#' + h) : '')); } catch (e) {} })();
  var LBOX = [126.3, 36.85, 127.9, 38.35];   // 서울·경기
  function lkSet(k, name) { var v = prompt(name + ' 인증키를 붙여 넣으세요. 이 기기에만 저장됩니다(저장소·다른 기기로 안 감). 비우면 지웁니다.', LK[k] || ''); if (v == null) return;
    v = v.replace(/\s+/g, ''); if (v) LK[k] = v; else delete LK[k]; try { localStorage.setItem('tg_map2d_keys', JSON.stringify(LK)); } catch (e) {} LIVE.ev = null; LIVE.sp = null; LIVE.ak = null; LIVE.kma = null; LIVE.wrn = null; LIVE.eqk = null; LIVE.bs = null; liveGo(); draw(); }
  // ITS 호출 한도 — 개발키 = 한 달 100건 · 운영키 = 한 달 10,000건(코워크가 2026-10-04 상향 신청 · 관리자 승인 뒤). 이 기기에서 부른 것만 센다(다른 기기·PC 도구가 쓴 것은 모른다).
  function itsTier() { return LK.itst === 'op' ? 'op' : 'dev'; }
  function itsPer() { var d = new Date(); return 'm' + (d.getFullYear() * 100 + d.getMonth() + 1); }
  function itsMax() { return itsTier() === 'op' ? 9500 : 90; }
  function itsQuota(add) { var pp = itsPer(), q; try { q = JSON.parse(localStorage.getItem('tg_map2d_itsn') || '{}') || {}; } catch (e) { q = {}; }
    if (q.p !== pp) q = { p: pp, n: 0 }; if (add) { q.n++; try { localStorage.setItem('tg_map2d_itsn', JSON.stringify(q)); } catch (e) {} } return q.n; }
  function itsGet(path, q) {
    if (!LK.its) return Promise.reject(new Error('ITS 키 없음'));
    if (itsQuota() >= itsMax()) return Promise.reject(new Error(itsTier() === 'op' ? '이 기기에서 이번 달 ITS 9,500건을 다 썼다' : '이 기기에서 이번 달 ITS ' + itsMax() + '건을 다 썼다(개발키 월 100건) — 운영키(월 10,000건) 승인 뒤 「운영키」를 누른다'));
    itsQuota(1);
    return fetch('https://openapi.its.go.kr:9443/' + path + '?apiKey=' + encodeURIComponent(LK.its) + q + '&getType=json').then(function (r) { if (r.ok) return r.json();
      return r.json().catch(function () { return {}; }).then(function (j) { var h = j && j.header; throw new Error(h && h.resultMsg ? h.resultMsg + ' (' + h.resultCode + ')' : 'HTTP ' + r.status); }); });
  }
  function hhmm(t) { var d = new Date(t); return ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  function gridGo(key, url, cur) {   // 화면을 칸으로 나눠 가운데 좌표 여럿을 한 번에(Open-Meteo) — 10분마다 또는 화면을 크게 옮기면
    var v = viewLL(), cx = (v[0] + v[2]) / 2, cy = (v[1] + v[3]) / 2, sx = v[2] - v[0], sy = v[3] - v[1], w = LIVE[key], now = Date.now();
    if (w && (w.busy || !(now - w.at > 10 * 60000 || Math.abs(cx - w.c[0]) > w.s[0] * 0.3 || Math.abs(cy - w.c[1]) > w.s[1] * 0.3 || sx / w.s[0] > 1.8 || sx / w.s[0] < 0.55))) return;
    var n = sx < 0.03 ? 2 : sx < 0.12 ? 3 : 4, la = [], lo = [];
    for (var i = 0; i < n; i++) for (var k = 0; k < n + 1; k++) { la.push((v[1] + sy * (i + 0.5) / n).toFixed(4)); lo.push((v[0] + sx * (k + 0.5) / (n + 1)).toFixed(4)); }
    LIVE[key] = { at: now, busy: 1, c: [cx, cy], s: [sx, sy], pts: (w || {}).pts || [] };
    fetch(url + '?latitude=' + la.join(',') + '&longitude=' + lo.join(',') + '&current=' + cur + '&timezone=Asia%2FSeoul')
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(function (j) { j = Array.isArray(j) ? j : [j]; LIVE[key] = { at: Date.now(), c: [cx, cy], s: [sx, sy], pts: j.map(function (o, q) { return { lat: +la[q], lon: +lo[q], c: o.current || {} }; }) }; draw(); })
      .catch(function (e) { LIVE[key] = { at: Date.now(), c: [cx, cy], s: [sx, sy], pts: (w || {}).pts || [], err: '받지 못함(' + (e && e.message || e) + ')' }; draw(); });
  }
  function liveGo(force) {
    if (document.hidden) return; var now = Date.now(), op = itsTier() === 'op';
    // 🚧 돌발 — 지도를 열 때(층을 켤 때) 한 번 · 「🔄 다시 받기」 · 운영키면 5분마다
    if (on.lev && LK.its && !(LIVE.ev && LIVE.ev.busy) && (force === 'ev' || !LIVE.ev || (op && now - LIVE.ev.at > 5 * 60000))) {
      var prev = LIVE.ev; LIVE.ev = { at: now, busy: 1, items: (prev || {}).items || [] };
      itsGet('eventInfo', '&type=all&eventType=all&minX=' + LBOX[0] + '&maxX=' + LBOX[2] + '&minY=' + LBOX[1] + '&maxY=' + LBOX[3])
        .then(function (j) { var b = j && j.body; if (!b || !b.items) throw new Error((j && j.header && j.header.resultMsg) || '빈 응답');
          LIVE.ev = { at: Date.now(), items: b.items.filter(function (e) { return isFinite(+e.coordX) && isFinite(+e.coordY) && +e.coordX > 120; }) }; draw(); })
        .catch(function (e) { LIVE.ev = { at: Date.now(), items: (prev || {}).items || [], err: '받지 못함(' + (e && e.message || e) + ')' }; draw(); });
    }
    // 🚦 소통 — 지금 화면(사방 25% 더)만 · 열 때 한 번 · 받은 범위를 벗어나면: 운영키 = 저절로(3분 간격) · 개발키 = 「🔄 이 화면 소통 받기」
    if (on.lspd && LK.its && spdSpan() && !(LIVE.sp && LIVE.sp.busy)) {
      var v = viewLL(), sp = LIVE.sp, inside = sp && sp.box && v[0] >= sp.box[0] && v[1] >= sp.box[1] && v[2] <= sp.box[2] && v[3] <= sp.box[3];
      if (force === 'sp' || !sp || (op && now - sp.at > 3 * 60000 && (!inside || now - sp.at > 5 * 60000))) {
        var dx = (v[2] - v[0]) * 0.25, dy = (v[3] - v[1]) * 0.25, bx = [v[0] - dx, v[1] - dy, v[2] + dx, v[3] + dy].map(function (x) { return +x.toFixed(4); }), ps = sp;
        LIVE.sp = { at: now, busy: 1, box: bx, m: (ps || {}).m || {} };
        itsGet('trafficInfo', '&type=all&drcType=all&minX=' + bx[0] + '&maxX=' + bx[2] + '&minY=' + bx[1] + '&maxY=' + bx[3])
          .then(function (j) { var b = j && j.body; if (!b || !b.items) throw new Error((j && j.header && j.header.resultMsg) || '빈 응답');
            var m = {}; b.items.forEach(function (x) { m[x.linkId] = [+x.speed, +x.travelTime, x.createdDate]; }); LIVE.sp = { at: Date.now(), box: bx, m: m, n: b.items.length }; draw(); })
          .catch(function (e) { LIVE.sp = { at: Date.now(), box: bx, m: (ps || {}).m || {}, err: '받지 못함(' + (e && e.message || e) + ')' }; draw(); });
      }
    }
    if (on.lwx) gridGo('wx', 'https://api.open-meteo.com/v1/forecast', 'temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,relative_humidity_2m,cloud_cover&wind_speed_unit=ms');
    if (on.lair) gridGo('air', 'https://air-quality-api.open-meteo.com/v1/air-quality', 'pm10,pm2_5,uv_index');
    dgGo(now);
    if (on.lrad && !(LIVE.rad && LIVE.rad.busy) && (!LIVE.rad || now - LIVE.rad.at > 10 * 60000)) {
      var pr = LIVE.rad; LIVE.rad = { at: now, busy: 1, f: (pr || {}).f, pf: (pr || {}).f };
      fetch('https://api.rainviewer.com/public/weather-maps.json').then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
        .then(function (j) { var ps2 = (j.radar && j.radar.past) || [], l = ps2[ps2.length - 1]; LIVE.rad = { at: Date.now(), f: l ? { u: j.host + l.path, t: l.time * 1000 } : null, pf: (pr || {}).f }; draw(); })
        .catch(function (e) { LIVE.rad = { at: Date.now(), f: (pr || {}).f, err: '받지 못함(' + (e && e.message || e) + ')' }; draw(); });
    }
  }
  function liveOn() { return on.lev || on.lwx || on.lspd || on.lair || on.lrad || on.lak || on.lkma || on.lbus; }
  function liveSoon() { if (!liveOn()) return; clearTimeout(LIVEW); LIVEW = setTimeout(liveGo, 1200); }
  setInterval(function () { if (liveOn()) liveGo(); if (BUSR && on.lbus && !document.hidden && Date.now() - BUSR.t0 < 15 * 60000 && BUSR.st) busPos(); if (HLS && !document.getElementById('ccv')) { try { HLS.destroy(); } catch (e) {} HLS = null; } }, 60000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) liveSoon(); });
  // 🌧 레이더 — RainViewer 조각(무료 판은 7단까지 · 한 칸 약 1km) · 우리 평면에 조각 모서리를 옮겨 그린다(브이월드와 같은 법)
  var RADT = {};
  function radTile(u, z, x, y) { var k = u + '/' + z + '/' + x + '/' + y, t = RADT[k]; if (t) return t.ok ? t : null;
    var ks = Object.keys(RADT); if (ks.length > 300) ks.slice(0, 100).forEach(function (q) { delete RADT[q]; });
    t = RADT[k] = { im: new Image(), ok: false }; t.im.onload = function () { t.ok = true; if (!VWQ) VWQ = requestAnimationFrame(function () { VWQ = 0; draw(); }); };
    t.im.src = u + '/256/' + z + '/' + x + '/' + y + '/2/1_1.png'; return null; }
  function drawRadar() {   // v2.5.0 이름 바꿈 — 반경 분석 drawRad(dark)가 뒤에서 같은 이름으로 덮어 레이더가 그려지지 않았다(v1.7.0~v2.4.0)
    var f = LIVE.rad && LIVE.rad.f; if (!on.lrad || !f) return; var pf = LIVE.rad.pf, W = cv.clientWidth, H = cv.clientHeight, a = M(0, 0), b = M(W, H);
    var lonA = a[0] / KX + LON0, lonB = b[0] / KX + LON0, latA = LAT0 - a[1] / KY, latB = LAT0 - b[1] / KY;
    var z = Math.round(Math.log(156543.03 * Math.cos(LAT0 * Math.PI / 180) * view.s) / Math.LN2); z = Math.max(3, Math.min(7, z));
    var x0 = Math.floor(vwLx(lonA, z)), x1 = Math.floor(vwLx(lonB, z)), y0 = Math.floor(vwLy(latA, z)), y1 = Math.floor(vwLy(latB, z));
    if ((x1 - x0 + 1) * (y1 - y0 + 1) > 60) return; ctx.save(); ctx.globalAlpha = 0.62; ctx.imageSmoothingEnabled = true;
    for (var x = x0; x <= x1; x++) for (var y = y0; y <= y1; y++) { var p0 = S(P(vwLon(x, z), vwLat(y, z))), p1 = S(P(vwLon(x + 1, z), vwLat(y + 1, z))), t = radTile(f.u, z, x, y);
      if (!t && pf && pf.u !== f.u) t = RADT[pf.u + '/' + z + '/' + x + '/' + y]; if (t && t.ok) ctx.drawImage(t.im, p0[0], p0[1], p1[0] - p0[0] + 0.6, p1[1] - p0[1] + 0.6); }
    ctx.restore();
  }
  // 🚦 소통 색 — 앱 기준(서울시 교통정보의 원활·서행·정체 구분을 본뜸): 고속·도시고속 40·70km/h · 그 밖 15·30km/h
  function spdCol(v, rk) { var a = rk <= 2 ? 40 : 15, b = rk <= 2 ? 70 : 30; return v < a ? '#dc2626' : v < b ? '#f59e0b' : '#16a34a'; }
  var RKN = ['', '고속국도', '도시고속도로', '일반국도', '특별·광역시도', '국가지원지방도', '지방도', '시군도'];
  function drawSpd() {
    if (!on.lspd || !LIVE.sp || !LIVE.sp.m || !ITSL.length) return; var m = LIVE.sp.m, a = M(-20, -20), b = M(cv.clientWidth + 20, cv.clientHeight + 20), wd = view.s > 0.1 ? 4 : view.s > 0.04 ? 3 : 2, off = wd * 0.8;
    ITSL.forEach(function (L) { var v = m[L.id]; if (!v) return; var bb = L.bb; if (bb[2] < a[0] || bb[0] > b[0] || bb[3] < a[1] || bb[1] > b[1]) return;
      var sp = L.pts.map(S), n = sp.length; ctx.beginPath();
      for (var i = 0; i < n; i++) { var p0 = sp[Math.max(0, i - 1)], p1 = sp[Math.min(n - 1, i + 1)], dx = p1[0] - p0[0], dy = p1[1] - p0[1], d = Math.hypot(dx, dy) || 1, ox = -dy / d * off, oy = dx / d * off;
        if (i) ctx.lineTo(sp[i][0] + ox, sp[i][1] + oy); else ctx.moveTo(sp[i][0] + ox, sp[i][1] + oy); }
      ctx.lineWidth = wd; ctx.lineCap = 'round'; ctx.strokeStyle = spdCol(v[0], L.rk); ctx.stroke();
      var mid = sp[n >> 1]; hit.push({ x: mid[0], y: mid[1], r: 7, it: { kind: 'lspd', L: L, v: v } }); });
  }
  // 📹 CCTV — 구운 목록(또는 「🔄 목록 새로 받기」로 받은 것) · 누르면 카드에서 영상(HLS) — 사파리는 그대로, 크롬 등은 hls.js(같은 사이트 js/vendor · 그때만 읽음)
  var HLS = null, HLSP = null;
  function ccList() { return CCLIVE || CCB; }
  function hlsLoad() { if (window.Hls) return Promise.resolve(); if (HLSP) return HLSP;
    HLSP = new Promise(function (ok, no) { var sc = document.createElement('script'); sc.src = 'js/vendor/hls.light.min.js'; sc.onload = ok; sc.onerror = no; document.head.appendChild(sc); }); return HLSP; }
  function ccPlay(url) {
    var v = document.getElementById('ccv'); if (!v) return; if (HLS) { try { HLS.destroy(); } catch (e) {} HLS = null; }
    var bad = function () { var m = document.getElementById('ccm'); if (m) m.innerHTML = '영상을 열지 못했다 — 목록이 오래되었거나 그 카메라가 쉬는 중일 수 있다. <button data-ccref="1">🔄 목록 새로 받기(ITS 2건)</button>'; };
    v.addEventListener('error', bad);
    v.addEventListener('playing', function () { var m = document.getElementById('ccm'); if (m) m.textContent = '● 실시간 · 소리 없음 · 몇 초 늦을 수 있다'; });
    if (v.canPlayType('application/vnd.apple.mpegurl')) { v.src = url; v.play().catch(function () {}); return; }
    hlsLoad().then(function () { if (!window.Hls || !Hls.isSupported() || !document.getElementById('ccv')) { bad(); return; }
      HLS = new Hls({ maxBufferLength: 10 }); HLS.on(Hls.Events.ERROR, function (e, d) { if (d && d.fatal) bad(); }); HLS.loadSource(url); HLS.attachMedia(v); v.play().catch(function () {}); }).catch(bad);
  }
  function ccRefresh() {
    var out = [], k = 0, fail = '';
    ['its', 'ex'].forEach(function (typ) { itsGet('cctvInfo', '&type=' + typ + '&cctvType=4&minX=' + LBOX[0] + '&maxX=' + LBOX[2] + '&minY=' + LBOX[1] + '&maxY=' + LBOX[3])
      .then(function (j) { ((j.response || {}).data || []).forEach(function (x) { if (/^https:/.test(x.cctvurl || '')) out.push([(x.cctvname || '').trim(), +x.coordx, +x.coordy, x.cctvurl, typ]); }); })
      .catch(function (e) { fail = (e && e.message) || String(e); })
      .then(function () { if (++k < 2) return; if (out.length) { CCLIVE = out; CCLIVE.at = hhmm(Date.now()) + ' 새로 받음'; } else alert('CCTV 목록을 받지 못했다 — ' + (fail || '빈 응답')); show(null); draw(); }); });
  }
  document.addEventListener('click', function (e) { if (e.target.closest('[data-ccref]')) ccRefresh(); });
  function drawCc() {
    if (!on.lcc) return; var L = ccList(), W0 = cv.clientWidth, H0 = cv.clientHeight, r = view.s > 0.02 ? 7 : 5;
    L.forEach(function (t) { var s0 = S(P(t[1], t[2])); if (s0[0] < -10 || s0[1] < -10 || s0[0] > W0 + 10 || s0[1] > H0 + 10) return;
      ctx.beginPath(); ctx.arc(s0[0], s0[1], r, 0, Math.PI * 2); ctx.fillStyle = t[4] === 'ex' ? '#0f766e' : '#1d4ed8'; ctx.fill(); ctx.lineWidth = 1.5; ctx.strokeStyle = '#fff'; ctx.stroke();
      if (r > 6) { ctx.fillStyle = '#fff'; ctx.fillRect(s0[0] - 3, s0[1] - 2, 5, 4); ctx.beginPath(); ctx.moveTo(s0[0] + 2, s0[1]); ctx.lineTo(s0[0] + 4.5, s0[1] - 2); ctx.lineTo(s0[0] + 4.5, s0[1] + 2); ctx.fill(); }
      hit.push({ x: s0[0], y: s0[1], r: 11, it: { kind: 'lcc', t: t } }); });
  }
  function pmGrade(v, small) { if (v == null) return null; var c = small ? [15, 35, 75] : [30, 80, 150]; return v <= c[0] ? 0 : v <= c[1] ? 1 : v <= c[2] ? 2 : 3; }
  var PMG = [['좋음', '#2563eb'], ['보통', '#16a34a'], ['나쁨', '#f59e0b'], ['매우나쁨', '#dc2626']];
  // ---------- 공공데이터포털 실시간(v1.9.0) ----------
  function dgGet(path, q) {
    if (!LK.dgk) return Promise.reject(new Error('공공데이터포털 키 없음 — 범례 「🔑 공공데이터포털 키」'));
    var k = LK.dgk.indexOf('%') >= 0 ? LK.dgk : encodeURIComponent(LK.dgk);
    return fetch('https://apis.data.go.kr/' + path + '?serviceKey=' + k + q).then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.text(); })
      .then(function (t) { try { return JSON.parse(t); } catch (e) { var m = /<returnAuthMsg>([^<]+)|<errMsg>([^<]+)|<resultMsg>([^<]+)/.exec(t); throw new Error(m ? (m[1] || m[2] || m[3]) : '응답이 JSON 이 아님'); } });
  }
  function dfsGrid(lat, lon) {   // 기상청 동네예보 격자(Lambert · 5km) — 기상청 공개 변환식
    var RE = 6371.00877 / 5, D2R = Math.PI / 180, s1 = 30 * D2R, s2 = 60 * D2R, ol = 126 * D2R, oa = 38 * D2R;
    var sn = Math.log(Math.cos(s1) / Math.cos(s2)) / Math.log(Math.tan(Math.PI * 0.25 + s2 * 0.5) / Math.tan(Math.PI * 0.25 + s1 * 0.5)), sf = Math.pow(Math.tan(Math.PI * 0.25 + s1 * 0.5), sn) * Math.cos(s1) / sn, ro = RE * sf / Math.pow(Math.tan(Math.PI * 0.25 + oa * 0.5), sn);
    var ra = RE * sf / Math.pow(Math.tan(Math.PI * 0.25 + lat * D2R * 0.5), sn), th = lon * D2R - ol; if (th > Math.PI) th -= 2 * Math.PI; if (th < -Math.PI) th += 2 * Math.PI; th *= sn;
    return [Math.floor(ra * Math.sin(th) + 43 + 0.5), Math.floor(ro - ra * Math.cos(th) + 136 + 0.5)];
  }
  function ymd(d) { return d.getFullYear() + ('0' + (d.getMonth() + 1)).slice(-2) + ('0' + d.getDate()).slice(-2); }
  var AKS = null, AKSP = null, BSTOP = {}, BSC = [], BUSR = null;
  function dgGo(now) {
    if (!LK.dgk) return;
    if (on.lak) {
      if (!AKS && !AKSP) AKSP = fetch('data/airkorea-stations.json').then(function (r) { return r.json(); }).then(function (j) { AKS = j; draw(); }).catch(function () { AKSP = null; });
      if (!(LIVE.ak && LIVE.ak.busy) && (!LIVE.ak || now - LIVE.ak.at > 20 * 60000)) { var pa = LIVE.ak; LIVE.ak = { at: now, busy: 1, m: (pa || {}).m || {} }; var m = {}, k2 = 0, er = '';
        ['서울', '경기'].forEach(function (sd) { dgGet('B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty', '&returnType=json&numOfRows=200&pageNo=1&ver=1.0&sidoName=' + encodeURIComponent(sd))
          .then(function (j) { (((j.response || {}).body || {}).items || []).forEach(function (x) { m[sd + '|' + x.stationName] = x; }); }).catch(function (e) { er = (e && e.message) || String(e); })
          .then(function () { if (++k2 < 2) return; LIVE.ak = { at: Date.now(), m: Object.keys(m).length ? m : (pa || {}).m || {}, err: Object.keys(m).length ? '' : '받지 못함(' + er + ')' }; draw(); }); }); }
    }
    if (on.lkma) {
      var v = viewLL(), g = dfsGrid((v[1] + v[3]) / 2, (v[0] + v[2]) / 2), kk = LIVE.kma;
      if (!(kk && kk.busy) && (!kk || now - kk.at > 30 * 60000 || kk.g[0] !== g[0] || kk.g[1] !== g[1])) {
        var d0 = new Date(now - 45 * 60000), bd = ymd(d0), bt = ('0' + d0.getHours()).slice(-2) + '00'; LIVE.kma = { at: now, busy: 1, g: g, v: (kk || {}).v };
        dgGet('1360000/VilageFcstInfoService_2.0/getUltraSrtNcst', '&dataType=JSON&numOfRows=20&pageNo=1&base_date=' + bd + '&base_time=' + bt + '&nx=' + g[0] + '&ny=' + g[1])
          .then(function (j) { var o = {}; ((((j.response || {}).body || {}).items || {}).item || []).forEach(function (x) { o[x.category] = x.obsrValue; }); if (!Object.keys(o).length) throw new Error(((j.response || {}).header || {}).resultMsg || '빈 응답'); LIVE.kma = { at: Date.now(), g: g, v: o, bt: bd.slice(4, 6) + '/' + bd.slice(6) + ' ' + bt.slice(0, 2) + ':00' }; draw(); })
          .catch(function (e) { LIVE.kma = { at: Date.now(), g: g, v: (kk || {}).v, err: '받지 못함(' + ((e && e.message) || e) + ')' }; draw(); }); }
      if (!(LIVE.wrn && LIVE.wrn.busy) && (!LIVE.wrn || now - LIVE.wrn.at > 10 * 60000)) { LIVE.wrn = { at: now, busy: 1 };
        dgGet('1360000/WthrWrnInfoService/getPwnStatus', '&dataType=JSON&numOfRows=5&pageNo=1').then(function (j) { var it = (((((j.response || {}).body || {}).items || {}).item) || [])[0] || {}; LIVE.wrn = { at: Date.now(), t6: (it.t6 || '').trim(), t7: (it.t7 || '').trim(), tm: it.tmFc }; draw(); })
          .catch(function (e) { LIVE.wrn = { at: Date.now(), err: '받지 못함(' + ((e && e.message) || e) + ')' }; draw(); }); }
      if (!(LIVE.eqk && LIVE.eqk.busy) && (!LIVE.eqk || now - LIVE.eqk.at > 10 * 60000)) { LIVE.eqk = { at: now, busy: 1, items: [] };
        dgGet('1360000/EqkInfoService/getEqkMsg', '&dataType=JSON&numOfRows=20&pageNo=1&fromTmFc=' + ymd(new Date(now - 3 * 864e5)) + '&toTmFc=' + ymd(new Date(now))).then(function (j) { LIVE.eqk = { at: Date.now(), items: (((((j.response || {}).body || {}).items || {}).item) || []) }; draw(); })
          .catch(function (e) { LIVE.eqk = { at: Date.now(), items: [], err: /NO_DATA|없/.test((e && e.message) || '') ? '' : '받지 못함(' + ((e && e.message) || e) + ')' }; draw(); }); }
    }
    if (on.lbus && view.s >= 0.04 && !(LIVE.bs && LIVE.bs.busy)) {
      var vb = viewLL(), cl = [(vb[0] + vb[2]) / 2, (vb[1] + vb[3]) / 2], cp = P(cl[0], cl[1]);
      if (!BSC.some(function (c) { return dTrue(c, cp) < 300; })) { BSC.push(cp); if (BSC.length > 60) BSC.shift(); LIVE.bs = { at: now, busy: 1 };
        dgGet('6410000/busstationservice/v2/getBusStationAroundListv2', '&x=' + cl[0].toFixed(6) + '&y=' + cl[1].toFixed(6) + '&format=json').then(function (j) {
          ((((j.response || {}).msgBody || {}).busStationAroundList) || []).forEach(function (x) { BSTOP[x.stationId] = { id: x.stationId, nm: x.stationName, p: P(+x.x, +x.y), mob: (x.mobileNo || '').trim(), reg: x.regionName }; });
          LIVE.bs = { at: Date.now() }; draw(); }).catch(function (e) { LIVE.bs = { at: Date.now(), err: '받지 못함(' + ((e && e.message) || e) + ')' }; draw(); }); }
    }
  }
  function busRoute(id, nm) {
    var keep = BUSR && BUSR.id === id ? BUSR.st : null; BUSR = { id: id, nm: nm, st: keep, v: [], at: 0, t0: Date.now() }; draw();
    (keep ? Promise.resolve() : dgGet('6410000/busrouteservice/v2/getBusRouteStationListv2', '&routeId=' + id + '&format=json').then(function (j) {
      BUSR.st = ((((j.response || {}).msgBody || {}).busRouteStationList) || []).map(function (x) { return { id: x.stationId, nm: x.stationName, p: P(+x.x, +x.y), seq: +x.stationSeq, turn: x.turnYn === 'Y' }; }).sort(function (a, b) { return a.seq - b.seq; }); }))
      .then(busPos).catch(function (e) { if (BUSR) { BUSR.err = '받지 못함(' + ((e && e.message) || e) + ')'; draw(); } });
  }
  function busPos() { var R0 = BUSR; if (!R0 || !R0.st) return;
    dgGet('6410000/buslocationservice/v2/getBusLocationListv2', '&routeId=' + R0.id + '&format=json').then(function (j) { if (BUSR !== R0) return;
      R0.v = ((((j.response || {}).msgBody || {}).busLocationList) || []).map(function (x) { return { pl: x.plateNo, seq: +x.stationSeq, cr: +x.crowded, seat: +x.remainSeatCnt, low: +x.lowPlate, sid: x.stationId }; }); R0.at = Date.now(); R0.err = ''; draw(); })
      .catch(function (e) { if (BUSR === R0) { R0.err = '받지 못함(' + ((e && e.message) || e) + ')'; draw(); } });
  }
  function bsArr(sid) { dgGet('6410000/busarrivalservice/v2/getBusArrivalListv2', '&stationId=' + sid + '&format=json').then(function (j) { var el = document.getElementById('bsarr'); if (!el) return;
      var L = (((j.response || {}).msgBody || {}).busArrivalList) || []; if (!L.length) { el.textContent = '지금 오는 경기 버스가 없다(또는 서울 시내버스만 서는 정류장).'; return; }
      L.sort(function (a, b) { return (a.predictTime1 === '' ? 999 : +a.predictTime1) - (b.predictTime1 === '' ? 999 : +b.predictTime1); });
      el.innerHTML = L.map(function (b) { var CR = ['', '여유', '보통', '혼잡', '매우혼잡'];
        return '<div class="r"><b>' + esc(b.routeName) + '</b><span>' + (b.predictTime1 !== '' ? '<b>' + b.predictTime1 + '분</b> · ' + b.locationNo1 + '정류장 전' : '-') + (+b.remainSeatCnt1 > 0 ? ' · 빈자리 ' + b.remainSeatCnt1 : '') + (CR[+b.crowded1] ? ' · ' + CR[+b.crowded1] : '') + (+b.lowPlate1 === 1 ? ' · 저상' : '') + (b.predictTime2 !== '' ? ' / 다음 ' + b.predictTime2 + '분' : '') + ' <em>→ ' + esc(b.routeDestName || '') + '</em> <button data-bsr="' + b.routeId + '|' + esc(String(b.routeName)) + '">🚌 위치</button></span></div>'; }).join(''); })
    .catch(function (e) { var el = document.getElementById('bsarr'); if (el) el.textContent = '받지 못함(' + ((e && e.message) || e) + ')'; }); }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-bsr]'); if (!b) return; var a = b.getAttribute('data-bsr').split('|'); busRoute(a[0], a[1]); show(null); });
  function akGrade(x) { var a = pmGrade(+x.pm25Value, 1), b = pmGrade(+x.pm10Value, 0); a = isFinite(+x.pm25Value) && x.pm25Value !== '-' ? a : null; b = isFinite(+x.pm10Value) && x.pm10Value !== '-' ? b : null; return a == null && b == null ? null : Math.max(a == null ? 0 : a, b == null ? 0 : b); }
  function drawAk() {
    if (!on.lak || !AKS || !LIVE.ak || !LIVE.ak.m) return; var W0 = cv.clientWidth, H0 = cv.clientHeight, r = view.s > 0.01 ? 11 : 7;
    AKS.items.forEach(function (t) { var x = LIVE.ak.m[t[3] + '|' + t[0]], s0 = S(P(t[1], t[2])); if (s0[0] < -20 || s0[1] < -20 || s0[0] > W0 + 20 || s0[1] > H0 + 20) return;
      var gr = x ? akGrade(x) : null; ctx.beginPath(); ctx.arc(s0[0], s0[1], r, 0, Math.PI * 2); ctx.fillStyle = gr == null ? '#94a3b8' : PMG[gr][1]; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
      if (r > 8) { ctx.fillStyle = '#fff'; ctx.font = 'bold 10px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(x && isFinite(+x.pm25Value) && x.pm25Value !== '-' ? x.pm25Value : '-', s0[0], s0[1] + 0.5); }
      hit.push({ x: s0[0], y: s0[1], r: 13, it: { kind: 'lak', t: t, x: x } }); });
  }
  function drawBus(dark) {
    if (!on.lbus) return; var W0 = cv.clientWidth, H0 = cv.clientHeight;
    if (BUSR && BUSR.st && BUSR.st.length) { path(BUSR.st.map(function (q) { return q.p; })); ctx.lineWidth = 4; ctx.strokeStyle = 'rgba(234,88,12,.55)'; ctx.stroke();
      var bySeq = {}; BUSR.st.forEach(function (q) { bySeq[q.seq] = q; });
      BUSR.v.forEach(function (b, i) { var q = bySeq[b.seq]; if (!q) return; var s0 = S(q.p); s0 = [s0[0] + 8, s0[1] - 8];
        ctx.fillStyle = '#ea580c'; ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(s0[0] - 11, s0[1] - 8, 22, 16, 4); else ctx.rect(s0[0] - 11, s0[1] - 8, 22, 16); ctx.fill(); ctx.lineWidth = 1.5; ctx.strokeStyle = '#fff'; ctx.stroke();
        ctx.fillStyle = '#fff'; ctx.font = 'bold 10px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('🚌', s0[0], s0[1] + 0.5);
        hit.push({ x: s0[0], y: s0[1], r: 12, it: { kind: 'lbv', b: b, st: q } }); }); }
    if (view.s < 0.04) return;
    Object.keys(BSTOP).forEach(function (k) { var q = BSTOP[k], s0 = S(q.p); if (s0[0] < -10 || s0[1] < -10 || s0[0] > W0 + 10 || s0[1] > H0 + 10) return;
      ctx.fillStyle = '#0d9488'; ctx.fillRect(s0[0] - 5, s0[1] - 5, 10, 10); ctx.lineWidth = 1.5; ctx.strokeStyle = '#fff'; ctx.strokeRect(s0[0] - 5, s0[1] - 5, 10, 10);
      if (view.s > 0.7) label([q.p[0], q.p[1] - 14 / view.s], q.nm, 10, dark ? '#e2e8f0' : '#134e4a', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)');
      hit.push({ x: s0[0], y: s0[1], r: 10, it: { kind: 'lbs', q: q } }); });
  }
  var PTYK = { '0': '없음', '1': '비', '2': '비/눈', '3': '눈', '5': '빗방울', '6': '빗방울눈날림', '7': '눈날림' };
  function kmaWarn() { var w = LIVE.wrn; if (!w || !w.t6) return ''; var L = w.t6.split(/\r?\n/).map(function (x) { return x.replace(/^o\s*/, '').trim(); }).filter(function (x) { return x && /서울|경기/.test(x); }); return L.join(' · '); }
  function drawKma(dark) {
    if (!on.lkma) return; var k = LIVE.kma, wn = kmaWarn(), y = 54 + (on.vw && VWOK ? 20 : 0), W0 = cv.clientWidth;
    if (k && k.v) { var v = k.v, t = '🌡 기상청 실황 ' + (v.T1H != null ? v.T1H + '°' : '-') + ' · 습도 ' + (v.REH || '-') + '% · 1시간 강수 ' + (v.RN1 || '0') + 'mm' + (v.PTY && v.PTY !== '0' ? ' · ' + (PTYK[v.PTY] || '') : '') + ' · 바람 ' + (v.WSD || '-') + 'm/s';
      ctx.font = 'bold 11px system-ui, sans-serif'; var tw = Math.min(W0 - 16, ctx.measureText(t).width + 14); ctx.fillStyle = dark ? 'rgba(15,22,36,.88)' : 'rgba(255,255,255,.94)'; ctx.fillRect(8, y, tw, 20); ctx.strokeStyle = '#0369a1'; ctx.lineWidth = 1; ctx.strokeRect(8, y, tw, 20);
      ctx.fillStyle = dark ? '#e0f2fe' : '#0c4a6e'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(t, 15, y + 10.5, tw - 12); hit.push({ x: 8 + tw / 2, y: y + 10, r: 14, it: { kind: 'lkma' } }); y += 24; }
    if (wn) { var t2 = '⚠ 특보 발효 — ' + wn; ctx.font = 'bold 11px system-ui, sans-serif'; var tw2 = Math.min(W0 - 16, ctx.measureText(t2).width + 14); ctx.fillStyle = '#b91c1c'; ctx.fillRect(8, y, tw2, 20); ctx.fillStyle = '#fff'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; ctx.fillText(t2, 15, y + 10.5, tw2 - 12); hit.push({ x: 8 + tw2 / 2, y: y + 10, r: 14, it: { kind: 'lkma' } }); }
    ((LIVE.eqk || {}).items || []).forEach(function (q) { if (!(q.lat > 32 && q.lat < 39.5 && q.lon > 123 && q.lon < 132)) return; var s0 = S(P(+q.lon, +q.lat));
      ctx.beginPath(); ctx.arc(s0[0], s0[1], 14, 0, Math.PI * 2); ctx.lineWidth = 3; ctx.strokeStyle = '#7c2d12'; ctx.stroke(); label([P(+q.lon, +q.lat)[0], P(+q.lon, +q.lat)[1] - 24 / view.s], '지진 M' + q.mt, 11, '#fff', 'rgba(124,45,18,.9)'); hit.push({ x: s0[0], y: s0[1], r: 16, it: { kind: 'leq', q: q } }); });
  }
  function akCard(it) { var t = it.t, x = it.x;
    var h = '<h3>🟢 ' + esc(t[0]) + ' 측정소 <small style="font-weight:400;color:var(--ink2)">' + esc(t[3] + ' · ' + t[4]) + '</small></h3>';
    if (!x) return h + '<p class="desc">이 측정소 값을 받지 못했다(점검 중이거나 목록 이름이 다름).</p>' + src(AKS.source);
    var gv = function (v, sm) { var g = pmGrade(+v, sm); return isFinite(+v) && v !== '-' ? v + '㎍/㎥ · <b style="color:' + PMG[g][1] + '">' + PMG[g][0] + '</b>' : '<em>점검·자료 없음</em>'; };
    h += row('초미세먼지(PM2.5)', gv(x.pm25Value, 1)) + row('미세먼지(PM10)', gv(x.pm10Value, 0)) + row('오존 · 이산화질소', esc((x.o3Value || '-') + 'ppm · ' + (x.no2Value || '-') + 'ppm')) + row('일산화탄소 · 아황산가스', esc((x.coValue || '-') + 'ppm · ' + (x.so2Value || '-') + 'ppm')) + row('통합대기환경지수', esc(x.khaiValue || '-')) + row('측정 시각', esc(x.dataTime || '-')) + row('주소', esc(t[5]));
    return h + '<p class="desc">측정소에서 실제로 잰 1시간 값(에어코리아 실시간 · 확정 전 값). 등급 색은 환경부 기준(PM2.5 15·35·75 · PM10 30·80·150).</p>' + src('한국환경공단 에어코리아 대기오염정보·측정소정보(공공데이터포털) — 20분마다 · 이 폰이 직접 받음 · 저장 안 함'); }
  function kmaCard() { var k = LIVE.kma || {}, v = k.v || {}, w = LIVE.wrn || {}, dirs = ['북', '북동', '동', '남동', '남', '남서', '서', '북서'];
    var h = '<h3>🌡 기상청 초단기실황 <small style="font-weight:400;color:var(--ink2)">격자 ' + (k.g || []).join(',') + ' · ' + esc(k.bt || '') + '</small></h3>';
    h += row('기온', v.T1H != null ? v.T1H + '°' : '-') + row('습도', v.REH != null ? v.REH + '%' : '-') + row('1시간 강수', (v.RN1 || '0') + 'mm' + (v.PTY && v.PTY !== '0' ? ' · ' + esc(PTYK[v.PTY] || v.PTY) : '')) + row('바람', (v.WSD || '-') + 'm/s' + (v.VEC != null ? ' · ' + dirs[Math.round(+v.VEC / 45) % 8] + '풍' : ''));
    h += row('특보(지금 발효)', w.t6 ? esc(w.t6).replace(/\n/g, '<br>') : (w.err ? esc(w.err) : '-')) + (w.t7 ? row('예비특보', esc(w.t7).replace(/\n/g, '<br>')) : '') + row('특보 발표', esc(w.tm || '-'));
    var eq = ((LIVE.eqk || {}).items || []); h += row('지진(3일)', eq.length ? eq.map(function (q) { return esc(String(q.tmEqk).replace(/^(\d{4})(\d\d)(\d\d)(\d\d)(\d\d).*/, '$2/$3 $4:$5') + ' M' + q.mt + ' ' + q.loc); }).join('<br>') : '없음');
    return h + '<p class="desc">실황 = 기상청이 관측을 그 5km 격자에 맞춘 값(지도 가운데 격자 · 30분마다 · 매시 40분쯤 나옴). 특보는 전국 발효 현황 글 그대로 — 지도 위 붉은 띠는 그중 서울·경기가 든 줄만.</p>' + src('기상청 단기예보(초단기실황)·기상특보·지진정보 조회서비스(공공데이터포털) — 이 폰이 직접 받음 · 저장 안 함'); }
  function bsCard(it) { var q = it.q; setTimeout(function () { bsArr(q.id); }, 0);
    return '<h3>🚏 ' + esc(q.nm) + ' <small style="font-weight:400;color:var(--ink2)">' + esc((q.reg || '') + (q.mob ? ' · ' + q.mob : '')) + '</small></h3><div id="bsarr" class="desc">도착 정보 받는 중…</div>' + src('경기도 버스도착정보·정류소 조회(공공데이터포털) — 실시간 · 이 폰이 직접 받음 · 저장 안 함 · ⚠ 서울 시내버스는 없다(서울시 API 는 https 가 없어 이 지도에서 못 부른다)'); }
  function bvCard(it) { var b = it.b, CR = ['', '여유', '보통', '혼잡', '매우혼잡'];
    return '<h3>🚌 ' + esc(BUSR ? BUSR.nm : '') + '번 <small style="font-weight:400;color:var(--ink2)">' + esc(b.pl || '') + '</small></h3>' + row('지금 정류장', esc(it.st.nm) + ' (' + b.seq + '번째)') + row('빈자리 · 혼잡', (b.seat >= 0 ? b.seat + '석' : '-') + (CR[b.cr] ? ' · ' + CR[b.cr] : '')) + row('저상', b.low === 1 ? '예' : '아니오') + row('받은 시각', BUSR && BUSR.at ? hhmm(BUSR.at) + ' <em>(1분마다 · 15분 뒤 멈춤)</em>' : '-') + '<p class="desc">버스 자리는 「지금 지난 정류장」으로 온다 — 그 정류장 옆에 그린다(정류장 사이 어디쯤인지는 자료에 없음).</p>' + src('경기도 버스위치정보·버스노선 조회(공공데이터포털)'); }
  function eqCard(it) { var q = it.q; return '<h3>🌏 지진 M' + esc(q.mt) + '</h3>' + row('시각', esc(String(q.tmEqk))) + row('위치', esc(q.loc)) + row('깊이', esc(q.dep) + 'km') + row('영향', esc(q.rem || '-')) + src('기상청 지진정보 조회서비스'); }
  var EVC = { '교통사고': ['#dc2626', '💥'], '공사': ['#ea580c', '🚧'], '기타돌발': ['#7c3aed', '⚠'], '재난': ['#0f172a', '🌊'], '기상': ['#0284c7', '🌧'], '행사': ['#0d9488', '🎪'] };
  function wmo(c, cc) { c = +c; if (c <= 3 && cc != null) return cc < 20 ? ['☀️', '맑음'] : cc < 50 ? ['🌤', '구름조금'] : cc < 80 ? ['⛅', '구름많음'] : ['☁️', '흐림']; return c === 0 ? ['☀️', '맑음'] : c <= 2 ? ['🌤', '구름조금'] : c === 3 ? ['☁️', '흐림'] : c <= 48 ? ['🌫', '안개'] : c <= 57 ? ['🌦', '이슬비'] : c <= 67 ? ['🌧', '비'] : c <= 77 ? ['🌨', '눈'] : c <= 82 ? ['🌧', '소나기'] : c <= 86 ? ['🌨', '눈 소나기'] : c >= 95 ? ['⛈', '뇌우'] : ['·', '?']; }
  function drawLive(dark) {
    var W0 = cv.clientWidth, H0 = cv.clientHeight;
    drawRadar(); drawSpd(); drawCc(); drawAk(); drawBus(dark);
    if (on.lair && LIVE.air && LIVE.air.pts) LIVE.air.pts.forEach(function (o) { var s0 = S(P(o.lon, o.lat)), c = o.c; s0[1] += on.lwx ? 25 : 0; if (s0[0] < -40 || s0[1] < -40 || s0[0] > W0 + 40 || s0[1] > H0 + 40 || c.pm2_5 == null) return;
      var g = Math.max(pmGrade(c.pm2_5, 1), pmGrade(c.pm10, 0)), t = String(Math.round(c.pm2_5)); ctx.font = 'bold 12px system-ui, sans-serif'; var tw = Math.max(26, ctx.measureText(t).width + 14);
      ctx.fillStyle = PMG[g][1]; ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(s0[0] - tw / 2, s0[1] - 10, tw, 20, 10); else ctx.rect(s0[0] - tw / 2, s0[1] - 10, tw, 20); ctx.fill();
      ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, s0[0], s0[1] + 0.5); hit.push({ x: s0[0], y: s0[1], r: 13, it: { kind: 'lair', o: o } }); });
    if (on.lwx && LIVE.wx && LIVE.wx.pts) LIVE.wx.pts.forEach(function (o) { var s0 = S(P(o.lon, o.lat)), c = o.c; if (s0[0] < -40 || s0[1] < -40 || s0[0] > W0 + 40 || s0[1] > H0 + 40 || c.temperature_2m == null) return;
      var t = wmo(c.weather_code, c.cloud_cover)[0] + ' ' + Math.round(c.temperature_2m) + '°' + (c.precipitation > 0 ? ' ' + c.precipitation + 'mm' : ''); ctx.font = 'bold 12px system-ui, sans-serif'; var tw = ctx.measureText(t).width + 12;
      ctx.fillStyle = dark ? 'rgba(15,22,36,.85)' : 'rgba(255,255,255,.92)'; ctx.strokeStyle = c.precipitation > 0 ? '#0284c7' : (dark ? '#64748b' : '#94a3b8'); ctx.lineWidth = c.precipitation > 0 ? 2 : 1;
      ctx.beginPath(); if (ctx.roundRect) ctx.roundRect(s0[0] - tw / 2, s0[1] - 11, tw, 22, 11); else ctx.rect(s0[0] - tw / 2, s0[1] - 11, tw, 22); ctx.fill(); ctx.stroke();
      ctx.fillStyle = dark ? '#e2e8f0' : '#0f172a'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, s0[0], s0[1] + 0.5); hit.push({ x: s0[0], y: s0[1], r: 14, it: { kind: 'lwx', o: o } }); });
    if (on.lev && LIVE.ev && LIVE.ev.items) LIVE.ev.items.forEach(function (e) { var s0 = S(P(+e.coordX, +e.coordY)), c = EVC[e.eventType] || ['#475569', '•']; if (s0[0] < -30 || s0[1] < -30 || s0[0] > W0 + 30 || s0[1] > H0 + 30) return;
      var r = view.s > 0.05 ? 11 : 7; ctx.beginPath(); ctx.arc(s0[0], s0[1], r, 0, Math.PI * 2); ctx.fillStyle = c[0]; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
      if (r > 8) { ctx.font = '12px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(c[1], s0[0], s0[1] + 0.5); } hit.push({ x: s0[0], y: s0[1], r: 13, it: { kind: 'lev', e: e } }); });
  }
  function ymdhm(t) { t = String(t || ''); return t.length >= 12 ? t.slice(0, 4) + '-' + t.slice(4, 6) + '-' + t.slice(6, 8) + ' ' + t.slice(8, 10) + ':' + t.slice(10, 12) : t; }
  function levCard(it) { var e = it.e, c = EVC[e.eventType] || ['#475569', '•'];
    var h = '<h3>' + c[1] + ' ' + esc(e.eventType) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(e.eventDetailType || '') + '</small></h3>';
    h += row('도로', esc((e.roadName || '') + (e.roadNo && e.roadNo !== '0' ? ' (' + e.roadNo + '번)' : '') + (e.type ? ' · ' + e.type : '') + (e.roadDrcType ? ' · ' + e.roadDrcType + ' 방향' : '')));
    if ((e.lanesBlocked || '').trim() || (e.lanesBlockType || '').trim()) h += row('막힌 차로', esc(((e.lanesBlockType || '') + ' ' + (e.lanesBlocked || '')).trim()));
    h += row('시작', esc(ymdhm(e.startDate))) + (e.endDate ? row('끝(예정)', esc(ymdhm(e.endDate))) : '') + ((e.message || '').trim() ? row('내용', esc(e.message.trim())) : '');
    h += row('받은 시각', hhmm(LIVE.ev.at) + ' <em>(5분마다 · 이 지도를 켜 둔 동안만)</em>');
    return h + '<p class="desc">고속도로·국도·시군도 관리기관이 국가교통정보센터에 올린 돌발상황이다. 서울 시내 사고는 다 올라오지 않는다(올린 것만) · 자리는 관리기관이 찍은 점.</p>' + src('국가교통정보센터(ITS) 돌발상황정보 OpenAPI — 실시간 · 이 폰이 직접 받음 · 저장하지 않음'); }
  function lwxCard(it) { var o = it.o, c = o.c, w = wmo(c.weather_code, c.cloud_cover), dirs = ['북', '북동', '동', '남동', '남', '남서', '서', '북서'];
    var h = '<h3>' + w[0] + ' 지금 날씨 <small style="font-weight:400;color:var(--ink2)">' + o.lat.toFixed(3) + ', ' + o.lon.toFixed(3) + '</small></h3>';
    h += row('기온 · 체감', (c.temperature_2m != null ? c.temperature_2m + '°' : '-') + ' · 체감 ' + (c.apparent_temperature != null ? c.apparent_temperature + '°' : '-')) + row('하늘', esc(w[1]) + (c.cloud_cover != null ? ' · 구름 ' + c.cloud_cover + '%' : ''));
    h += row('강수(최근)', (c.precipitation != null ? c.precipitation + 'mm' : '-')) + row('바람', (c.wind_speed_10m != null ? c.wind_speed_10m + 'm/s' : '-') + (c.wind_direction_10m != null ? ' · ' + dirs[Math.round(c.wind_direction_10m / 45) % 8] + '풍' : '')) + row('습도', c.relative_humidity_2m != null ? c.relative_humidity_2m + '%' : '-');
    h += row('받은 시각', hhmm(LIVE.wx.at) + ' <em>(10분마다 · 지도를 크게 옮기면 다시)</em>');
    return h + '<p class="desc">하늘 낱말은 구름 양으로 가른다(20·50·80% — 앱 기준). 관측소에서 잰 값이 아니라 기상 모형이 그 자리(격자 약 1~2km)에 낸 현재값이다. 화면을 ' + (LIVE.wx.pts.length) + '칸으로 나눠 가운데 값을 찍는다.</p>' + src('Open-Meteo(open-meteo.com) 현재 기상 API — CC BY 4.0 · 키 없음 · 이 폰이 직접 받음 · 저장하지 않음'); }
  function spdCard(it) { var L = it.L, v = it.v;
    var h = '<h3>🚦 ' + esc(L.nm || '(이름 없는 길)') + ' <small style="font-weight:400;color:var(--ink2)">' + esc(RKN[L.rk] || '') + '</small></h3>';
    h += row('지금 속도', '<b style="color:' + spdCol(v[0], L.rk) + '">' + v[0] + 'km/h</b>' + (L.ms ? ' · 제한 ' + L.ms + 'km/h' : '')) + row('이 구간 지나는 시간', (v[1] ? Math.round(v[1]) + '초' : '-')) + row('ITS 기준 시각', esc(ymdhm(v[2]))) + row('받은 시각', hhmm(LIVE.sp.at) + ' <em>(열 때 한 번 · 「🔄 이 화면 소통 받기」)</em>');
    return h + '<p class="desc">선은 달리는 방향의 오른쪽에 그린다(같은 길 두 방향이 나란히). 색은 앱 기준 — 고속·도시고속은 40·70km/h, 그 밖은 15·30km/h 로 정체·서행·원활을 가른다. 링크 ' + esc(L.id) + '.</p>' + src('국가교통정보센터(ITS) 교통소통정보 OpenAPI(실시간 · 이 폰이 직접 받음 · 저장 안 함) · 도로 선 = ' + (ITSL.src || 'ITS 표준노드링크')); }
  function ccCard(it) { var t = it.t; setTimeout(function () { ccPlay(t[3]); }, 0);
    var h = '<h3>📹 ' + esc(t[0]) + '</h3><video id="ccv" controls muted playsinline autoplay style="width:100%;max-height:42vh;background:#000;border-radius:8px"></video><p id="ccm" class="desc">불러오는 중… (소리 없음 · 몇 초 늦을 수 있다)</p>';
    h += row('구분', t[4] === 'ex' ? '고속도로(한국도로공사)' : '국도·기타(ITS)') + row('목록', esc(CCLIVE ? CCLIVE.at : (CCB.at || '') + ' 구움') + ' <button data-ccref="1">🔄 목록 새로 받기(ITS 2건)</button>');
    return h + src((CCB.src || '국가교통정보센터(ITS) CCTV 정보 OpenAPI') + ' · 영상은 열 때만 받고 저장하지 않는다'); }
  function airCard(it) { var o = it.o, c = o.c, g1 = pmGrade(c.pm10, 0), g2 = pmGrade(c.pm2_5, 1);
    var h = '<h3>😷 지금 미세먼지 <small style="font-weight:400;color:var(--ink2)">' + o.lat.toFixed(3) + ', ' + o.lon.toFixed(3) + '</small></h3>';
    h += row('초미세먼지(PM2.5)', c.pm2_5 != null ? Math.round(c.pm2_5) + '㎍/㎥ · <b style="color:' + PMG[g2][1] + '">' + PMG[g2][0] + '</b>' : '-') + row('미세먼지(PM10)', c.pm10 != null ? Math.round(c.pm10) + '㎍/㎥ · <b style="color:' + PMG[g1][1] + '">' + PMG[g1][0] + '</b>' : '-') + row('자외선 지수', c.uv_index != null ? c.uv_index : '-');
    h += row('받은 시각', hhmm(LIVE.air.at) + ' <em>(10분마다)</em>');
    return h + '<p class="desc">등급은 환경부 기준(PM2.5 15·35·75 · PM10 30·80·150㎍/㎥). 값은 측정소가 잰 것이 아니라 유럽 CAMS 대기 모형이 그 자리에 낸 현재값이라 측정소(에어코리아)와 다를 수 있다.</p>' + src('Open-Meteo 대기질 API(CAMS) — 키 없음 · 이 폰이 직접 받음 · 저장하지 않음'); }
  function liveLegend() { var b = [];
    if (on.lev || on.lspd || on.lcc) b.push('<div class="lg-btns"><button data-lkey="its">🔑 ITS 키' + (LK.its ? ' 바꾸기' : ' 넣기') + '</button><button data-itst="dev" class="' + (itsTier() === 'dev' ? 'on' : '') + '">개발키(월 100)</button><button data-itst="op" class="' + (itsTier() === 'op' ? 'on' : '') + '">운영키(월 10,000)</button></div><small class="lg-n">ITS 호출 이번 달 ' + itsQuota() + '/' + itsMax() + '(이 기기) · 개발키는 지도를 열 때 한 번 받고 「🔄」로 다시 · 운영키면 저절로</small>');
    if (on.lspd) { var sp = LIVE.sp, vv = viewLL(), inb = sp && sp.box && vv[0] >= sp.box[0] && vv[1] >= sp.box[1] && vv[2] <= sp.box[2] && vv[3] <= sp.box[3];
      b.push('<b>🚦 소통</b> ' + li('#16a34a', '원활') + li('#f59e0b', '서행') + li('#dc2626', '정체') + '<small class="lg-n">' + (!spdSpan() ? '<b>더 확대하면(화면 가로 약 14km 안) 받는다</b>' : sp && sp.err ? '<b style="color:#b91c1c">' + esc(sp.err) + '</b>' : sp && !sp.busy ? (sp.n || 0) + '구간 · ' + hhmm(sp.at) + ' 받음' + (inb ? '' : ' · <b>지금 화면은 받은 범위 밖</b>') : LK.its ? '받는 중' : 'ITS 키 필요') + '</small><div class="lg-btns"><button data-lre="sp">🔄 이 화면 소통 받기(ITS 1건)</button></div>'); }
    if (on.lcc) b.push('<b>📹 CCTV</b> ' + li('#1d4ed8', '국도·기타') + li('#0f766e', '고속도로') + '<small class="lg-n">' + ccList().length + '대 · 목록 ' + esc(CCLIVE ? CCLIVE.at : (CCB.at || '…') + ' 구움') + ' · 누르면 영상(ITS 호출 없음)</small>');
    if (on.lrad) { var rd = LIVE.rad; b.push('<b>🌧 레이더</b><small class="lg-n">' + (rd && rd.err ? '<b style="color:#b91c1c">' + esc(rd.err) + '</b>' : rd && rd.f ? hhmm(rd.f.t) + ' 관측 · 10분마다 · 파랑(약함) → 노랑·빨강(강함)' : '받는 중') + ' · RainViewer(rainviewer.com) 레이더 합성 · 무료 판은 7단 확대까지(한 칸 약 1km)</small>'); }
    if (on.lak || on.lkma || on.lbus) b.push('<div class="lg-btns"><button data-lkey="dgk">🔑 공공데이터포털 키' + (LK.dgk ? ' 바꾸기' : ' 넣기') + '</button></div>' + (LK.dgk ? '' : '<small class="lg-n" style="color:#b91c1c">에어코리아·기상청·경기 버스는 공공데이터포털(data.go.kr) 일반 인증키가 있어야 한다 — 이 기기에만 저장</small>'));
    if (on.lak) { var ak = LIVE.ak; b.push('<b>🟢 측정소</b> ' + PMG.map(function (g) { return li(g[1], g[0]); }).join('') + li('#94a3b8', '점검·없음') + '<small class="lg-n">' + (ak && ak.err ? '<b style="color:#b91c1c">' + esc(ak.err) + '</b>' : ak && !ak.busy ? Object.keys(ak.m).length + '곳 · ' + hhmm(ak.at) + ' 받음 · 20분마다' : '받는 중') + ' · 숫자 = PM2.5 실측(㎍/㎥) · 서울·경기 168곳</small>'); }
    if (on.lkma) { var km = LIVE.kma, wr = LIVE.wrn; b.push('<b>🌡 기상청</b><small class="lg-n">' + (km && km.err ? '<b style="color:#b91c1c">' + esc(km.err) + '</b>' : km && km.v ? '실황 ' + esc(km.bt || '') + ' · 지도 가운데 격자' : '받는 중') + ' · 특보 ' + (wr && wr.err ? esc(wr.err) : kmaWarn() ? '<b style="color:#b91c1c">서울·경기 발효 있음</b>' : wr && !wr.busy ? '서울·경기 없음' : '…') + ' · 지진 3일 ' + (((LIVE.eqk || {}).items || []).length) + '건 · 윗줄 띠를 누르면 자세히</small>'); }
    if (on.lbus) { var bs = LIVE.bs; b.push('<b>🚌 경기 버스</b> ' + li('#0d9488', '정류장', 'box') + li('#ea580c', '고른 노선 버스') + '<small class="lg-n">' + (view.s < 0.04 ? '<b>더 확대하면 화면 가운데 둘레 정류장을 받는다</b>' : bs && bs.err ? '<b style="color:#b91c1c">' + esc(bs.err) + '</b>' : '정류장 ' + Object.keys(BSTOP).length + '곳 받음') + (BUSR ? ' · 노선 ' + esc(BUSR.nm) + ' 버스 ' + BUSR.v.length + '대' + (BUSR.err ? ' <b style="color:#b91c1c">' + esc(BUSR.err) + '</b>' : '') + ' <button data-busx="1">노선 지우기</button>' : '') + ' · 정류장을 누르면 도착 · 「🚌 위치」로 그 노선 버스 · ⚠ 서울 시내버스는 없음</small>'); }
    if (on.lair) { var ar = LIVE.air; b.push('<b>😷 미세먼지</b> ' + PMG.map(function (g) { return li(g[1], g[0]); }).join('') + '<small class="lg-n">' + (ar && ar.err ? '<b style="color:#b91c1c">' + esc(ar.err) + '</b>' : ar && !ar.busy ? ar.pts.length + '칸 · ' + hhmm(ar.at) + ' 받음' : '받는 중') + ' · 숫자 = 초미세먼지(PM2.5 ㎍/㎥) · 색 = PM2.5·PM10 중 나쁜 쪽 환경부 등급 · CAMS 모형값(측정소 아님)</small>'); }
    if (on.lev) { var e = LIVE.ev; b.push('<b>🚧 돌발</b> ' + Object.keys(EVC).slice(0, 3).map(function (k) { return li(EVC[k][0], EVC[k][1] + ' ' + k); }).join(''));
      b.push(!LK.its ? '<small class="lg-n" style="color:#b91c1c">ITS 키가 아직 없다 — 「🔑 ITS 키」에 국가교통정보센터 인증키를 넣으면 이 기기에서 보인다</small>'
        : '<small class="lg-n">' + (e && e.err ? '<b style="color:#b91c1c">' + esc(e.err) + '</b> · ' : '') + (e && !e.busy ? '서울·경기 ' + (e.items || []).length + '건 · ' + hhmm(e.at) + ' 받음' : '받는 중') + '</small><div class="lg-btns"><button data-lre="ev">🔄 돌발 다시 받기(ITS 1건)</button></div>'); }
    if (on.lwx) { var w = LIVE.wx; b.push('<small class="lg-n">🌦 지금 날씨 — ' + (w && w.err ? '<b style="color:#b91c1c">' + esc(w.err) + '</b>' : w && !w.busy ? w.pts.length + '칸 · ' + hhmm(w.at) + ' 받음' : '받는 중') + ' · 파란 테 = 비·눈이 오는 칸 · Open-Meteo 모형값</small>'); }
    return b.length ? ['📡 실시간(켠 동안만 받음 · 저장 안 함)', b.join('')] : null; }
  function draw() {
    var needW = Math.round(cv.clientWidth * DPR), needH = Math.round(cv.clientHeight * DPR);
    if (cv.width !== needW || cv.height !== needH) { cv.width = needW; cv.height = needH; }
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0); hit = []; viewWatch();
    var W = cv.clientWidth, H = cv.clientHeight, dark = document.documentElement.classList.contains('dark');
    var BASE = on.base && OSM; ctx.fillStyle = dark ? '#0f1624' : (BASE ? '#f2efe8' : '#eef2f6'); ctx.fillRect(0, 0, W, H);
    var VW = drawVw();
    var ymd = pickDate(), RVIS = RDONG.filter(inViewBox);
    // 이웃 구의 동(회색 · 점선 경계) — 그 구의 지역 자료를 받았으면 그쪽이 그린다
    NEAR.forEach(function (d) { if (RGUN[d.gu]) return;
      d.polys.forEach(function (Pg) { ctx.beginPath(); Pg.forEach(function (r) { r.forEach(function (q, n) { var s = S(q); if (n) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); }); ctx.closePath(); });
        if (on.dong) { var hl = sel && sel.it.kind === 'near' && sel.it.d === d; ctx.fillStyle = dark ? (hl ? 'rgba(148,163,184,.35)' : 'rgba(148,163,184,.10)') : (hl ? '#e2e8f0' : '#f1f5f9'); ctx.fill('evenodd'); }
        ctx.lineWidth = 0.9; ctx.setLineDash([3, 3]); ctx.strokeStyle = dark ? 'rgba(148,163,184,.5)' : 'rgba(100,116,139,.55)'; ctx.stroke(); ctx.setLineDash([]); });
    });
    // 행정동
    DONG.concat(RVIS).forEach(function (d, k) {
      d.polys.forEach(function (Pg) { ctx.beginPath(); Pg.forEach(function (r) { r.forEach(function (q, n) { var s = S(q); if (n) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); }); ctx.closePath(); });
        var lv = on.live ? liveNow(d) : null;
        if (lv) { var t = Math.min(1, lv.n / (lv.max || 1)); ctx.fillStyle = 'rgba(' + Math.round(255 - 40 * t) + ',' + Math.round(230 - 170 * t) + ',' + Math.round(150 - 110 * t) + ',' + (dark ? .55 : .75) + ')'; ctx.fill('evenodd'); }
        else if (on.sales && salesNow(d)) { var sn = salesNow(d); ctx.fillStyle = 'rgba(' + Math.round(237 - 120 * sn.t) + ',' + Math.round(233 - 180 * sn.t) + ',' + Math.round(254 - 40 * sn.t) + ',' + (dark ? .5 : .8) + ')'; ctx.fill('evenodd'); }
        else if (on.dong) { var hl3 = sel && sel.it.kind === 'dong' && sel.it.d === d; ctx.fillStyle = dark ? 'rgba(90,120,170,' + (hl3 ? '.45' : BASE ? '.08' : '.18') + ')' : (hl3 ? '#fde68a' : PAL[k % PAL.length]); if (VW && !hl3) ctx.globalAlpha = 0.14; else if (BASE && !hl3 && !dark) ctx.globalAlpha = 0.3; ctx.fill('evenodd'); ctx.globalAlpha = 1; }
        if (!BASE) { ctx.lineWidth = (on.dong ? 1.6 : 0.8) * (d.rg ? 0.7 : 1); ctx.strokeStyle = dark ? 'rgba(160,190,230,.6)' : 'rgba(40,60,90,.45)'; ctx.stroke(); } });
    });
    if (BASE) { if (!VW) drawBaseAreas(dark); DONG.concat(RVIS).forEach(function (d) { d.polys.forEach(function (Pg) { ctx.beginPath(); Pg.forEach(function (r) { r.forEach(function (q, n) { var s = S(q); if (n) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); }); ctx.closePath(); });
      ctx.lineWidth = (on.dong ? 1.8 : 0.8) * (d.rg ? 0.65 : 1); ctx.setLineDash(on.dong ? [] : [4, 4]); ctx.strokeStyle = dark ? 'rgba(167,139,250,.65)' : 'rgba(109,40,217,.45)'; ctx.stroke(); ctx.setLineDash([]); }); }); }
    // 구 경계(서초·동작·관악·강남)
    GU.forEach(function (g) { path(g.pts); ctx.lineWidth = 2.4; ctx.setLineDash([8, 5]); ctx.strokeStyle = dark ? '#9fb3d1' : '#475569'; ctx.stroke(); ctx.setLineDash([]); });
    // 도로 — 바탕 지도가 있으면 OSM 도로 전부(종류별 폭·색 · 지하차도 점선 · 다리 테), 없으면 간선 10개
    if (on.road && OSM) drawBaseRoads(dark);
    drawUnits(dark); drawJrs(dark); drawLpop(dark); drawFdong(dark); drawRnet(dark); drawSgg(dark); drawVols(dark); drawExv(dark); drawMsub(dark); drawBusd(dark); drawFlodge(dark); drawMinbak(dark); drawStay(dark); drawRpost(dark); drawJiga(dark); drawLand(dark);   // v0.10.90 시·군·구 경계(서울·경기·인천)
    // 건물
    if (on.bld && BLD.length && view.s > 0.12) BLD.forEach(function (b) { path(b.p); ctx.closePath(); ctx.fillStyle = dark ? 'rgba(200,210,225,.28)' : (BASE ? 'rgba(186,176,164,.85)' : 'rgba(90,100,115,.30)'); ctx.fill(); if (BASE && !dark && view.s > 0.5) { ctx.lineWidth = 0.6; ctx.strokeStyle = 'rgba(120,110,100,.7)'; ctx.stroke(); } });
    if ((on.road || on.jcnm) && OSM) drawBaseLabels(dark);
    // 도로(OSM 간선 10개)
    if (on.road && !OSM) ROADS.forEach(function (r) { path(r.pts); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.lineWidth = Math.max(3, 26 * view.s); ctx.strokeStyle = dark ? '#3b4a63' : '#ffffff'; ctx.stroke(); ctx.lineWidth = Math.max(1, 3 * view.s); ctx.strokeStyle = dark ? '#8aa0c0' : '#f59e0b'; ctx.stroke(); });
    if (on.road && !OSM && view.s > 0.08) ROADS.forEach(function (r) { var q = r.pts[Math.floor(r.pts.length * 0.3)]; if (q) label(q, r.name, 12, dark ? '#e2e8f0' : '#334155', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.8)'); });
    if (on.dong && view.s > 0.09) NEAR.forEach(function (d) { if (RGUN[d.gu]) return; label(d.c, d.name, 11, dark ? '#94a3b8' : '#64748b'); if (view.s > 0.16) label([d.c[0], d.c[1] + 14 / view.s], d.gu, 10, dark ? '#64748b' : '#94a3b8'); });
    // 동 이름
    if (on.dong) DONG.concat(view.s > 0.045 ? RVIS : []).forEach(function (d) { label(d.c, d.name, view.s > 0.2 ? 14 : 12, dark ? '#dbe6f5' : '#1e293b'); if (d.rg && view.s > 0.12) label([d.c[0], d.c[1] - 15 / view.s], d.gu, 10, dark ? '#94a3b8' : '#64748b'); var lv2 = on.live ? liveNow(d) : null, sn2 = on.sales && !lv2 ? salesNow(d) : null; if (sn2 && view.s > 0.06) label([d.c[0], d.c[1] + 16 / view.s], '💳 시간당 약 ' + won(sn2.perH), 11, dark ? '#ddd6fe' : '#4c1d95'); else if (lv2 && view.s > 0.06) label([d.c[0], d.c[1] + 16 / view.s], '지금 ' + lv2.n.toLocaleString() + '명', 11, dark ? '#fde68a' : '#7c2d12'); else if (d.pop && view.s > 0.14) label([d.c[0], d.c[1] + 16 / view.s], d.pop.tot.toLocaleString() + '명', 11, dark ? '#94a3b8' : '#475569'); });
    // 교차로(이름 · 사고)
    NODES.forEach(function (n) {
      var st = D.acc && D.acc.nodes ? D.acc.nodes.filter(function (x) { return x.node[0] === n.i && x.node[1] === n.j; })[0] : null;
      if (!n.real) { var sx = S(n.p); ctx.strokeStyle = dark ? '#94a3b8' : '#64748b'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(sx[0] - 5, sx[1] - 5); ctx.lineTo(sx[0] + 5, sx[1] + 5); ctx.moveTo(sx[0] + 5, sx[1] - 5); ctx.lineTo(sx[0] - 5, sx[1] + 5); ctx.stroke(); hit.push({ x: sx[0], y: sx[1], r: 9, it: { kind: 'node', n: n, st: null } }); return; }
      var a19 = accN(n, 2019, 2025), d19 = deadN(n, 2019, 2025);
      if (on.acc && a19) { var r19 = 5 + Math.sqrt(a19) * 0.55; dot(n.p, r19, d19 ? 'rgba(220,38,38,.55)' : 'rgba(234,88,12,.45)', '#7f1d1d', { kind: 'node', n: n, st: st }); if (view.s > 0.09) label([n.p[0], n.p[1] + (r19 * zk() + 9) / view.s], a19 + '건' + (d19 ? ' · 사망 ' + d19 : ''), 10.5, '#7f1d1d', 'rgba(255,255,255,.85)'); }
      else if (on.acc && st && st.total) { var r = 5 + Math.sqrt(st.total) * 0.9; dot(n.p, r, st.death ? 'rgba(220,38,38,.55)' : 'rgba(234,88,12,.45)', '#7f1d1d', { kind: 'node', n: n, st: st }); }
      else dot(n.p, 4, dark ? '#e2e8f0' : '#1e293b', null, { kind: 'node', n: n, st: st });
      if (view.s > 0.13) label([n.p[0], n.p[1] - 22 / view.s], n.name, 11.5, dark ? '#fef3c7' : '#0f172a', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.85)');
    });
    // 사망사고 사례(한 건씩 — 기본 지도 아핀을 거꾸로 풀어 실제 자리로)
    // v2.3.1 「🕯 사망사고」(최근 2020~2025)는 사망사고 10년(F10) 자료 한 벌에서 그린다 — 옛 taas-fatal-seocho.json(55건)이 F10 의 같은 사고라 두 층을 켜면 한 사고가 두 점이었다 · 10년 층이 켜져 있으면 그쪽이 그린다
    if (on.fatal && !on.fatal10 && F10.length) F10.forEach(function (x) { if (x.f[0] >= 2020) dot(x.p, 5.5, '#111827', '#fca5a5', { kind: 'f10', x: x }); });
    if (on.hot && D.hot) (D.hot.layers || []).forEach(function (L) { (L.items || []).forEach(function (it) { if (it.lo && it.la) dot(P(it.lo, it.la), 7, 'rgba(250,204,21,.8)', '#a16207', { kind: 'hot', it: it, L: L }); }); });
    // 🏫 어린이보호구역(v0.10.65 · 전국어린이보호구역표준데이터) — 자리는 대상 시설의 점(구역 경계선은 자료에 없다)
    var SZC = { '초등학교': '#eab308', '유치원': '#f97316', '어린이집': '#fb923c', '특수학교': '#a855f7', '외국인학교': '#0ea5e9', '학원': '#84cc16' };
    if (on.sz && D.sz) D.sz.zones.forEach(function (z) { dot(P(z.lon, z.lat), z.kind === '초등학교' ? 6 : 4.5, SZC[z.kind] || '#eab308', '#1f2937', { kind: 'sz', z: z });
      if (view.s > 0.18 && z.kind === '초등학교') label([P(z.lon, z.lat)[0], P(z.lon, z.lat)[1] - 12 / view.s], z.name, 10, dark ? '#fde68a' : '#713f12', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
    if (on.szh && D.sz) D.sz.hot.forEach(function (t) { var q = P(t.lon, t.lat), s = S(q); ctx.beginPath(); ctx.arc(s[0], s[1], Math.max(10, 60 * view.s), 0, Math.PI * 2); ctx.fillStyle = 'rgba(220,38,38,.18)'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#dc2626'; ctx.stroke(); dot(q, 6, '#dc2626', '#fff', { kind: 'szh', t: t }); });
    if (on.cam && D.cam) D.cam.items.forEach(function (c) { dot(P(c.lon, c.lat), 4.5, camCol(c), '#fff', { kind: 'cam', c: c }); });
    if (on.sig && D.sig) D.sig.spots.forEach(function (s) { dot(P(s.lon, s.lat), 5, '#16a34a', '#fff', { kind: 'sig', s: s }); });
    if (on.sub && F2) (F2.subways || []).forEach(function (s) { var n = nodeAt([s.i, s.j]); if (!n) return; var q = [n.p[0] + (s.side || 1) * 26, n.p[1] + 26], ls = s.lines || [];
      ls.forEach(function (l, k) { dot([q[0] + k * 13 / view.s, q[1]], 6, LINE_C[l] || '#64748b', '#fff', k ? null : { kind: 'sub', s: s, n: n }); });
      if (view.s > 0.1) label([q[0], q[1] + 16 / view.s], s.name, 11, dark ? '#e2e8f0' : '#334155', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
    if (on.her && D.her) D.her.items.forEach(function (h) { if (h.lat && h.lon) dot(P(h.lon, h.lat), 5, '#92400e', '#fde68a', { kind: 'her', h: h }); });
    if (on.vol && D.vol) D.vol.spots.forEach(function (v) { var n = v.node && nodeAt(v.node); if (n && !v.outside) { var s2 = S(n.p); ctx.fillStyle = '#0ea5e9'; ctx.fillRect(s2[0] + 8, s2[1] - 8, 16, 16); hit.push({ x: s2[0] + 16, y: s2[1], r: 12, it: { kind: 'vol', v: v, n: n } }); } });
    drawJgg(dark); drawSz(dark); drawTrd(dark); drawHl(dark); drawGgt(dark); drawRent(dark); drawBiz(dark); drawRad(dark); drawA10(dark); drawGrid(dark); drawHome(dark); drawPolice(dark); drawRi(dark); drawPub(dark); drawExtra(dark); drawFlow(dark); drawSafe(dark); drawSeason(dark);
    if (on.evt && D.evt) {
      (D.evt.events && D.evt.events.items || []).forEach(function (e) { if (e.lat && e.s <= ymd && e.e >= ymd) dot(P(e.lon, e.lat), 5.5, '#a855f7', '#fff', { kind: 'evt', e: e }); });
      (D.evt.rallies && D.evt.rallies.items || []).forEach(function (r) {
        if (r.d !== ymd || !r.lat) return;
        if (r.march && r.dest) { path([P(r.lon, r.lat), P(r.dest[1], r.dest[0])]); ctx.lineWidth = 3; ctx.setLineDash([6, 4]); ctx.strokeStyle = '#ef4444'; ctx.stroke(); ctx.setLineDash([]); }
        dot(P(r.lon, r.lat), 7, '#ef4444', '#fff', { kind: 'rally', r: r });
      });
    }
    drawLive(dark); drawKma(dark); liveSoon();
    if (REP) { var rs = S(REP.p); ctx.beginPath(); ctx.arc(rs[0], rs[1], 14, 0, Math.PI * 2); ctx.lineWidth = 4; ctx.strokeStyle = '#dc2626'; ctx.stroke(); ctx.beginPath(); ctx.arc(rs[0], rs[1], 4, 0, Math.PI * 2); ctx.fillStyle = '#dc2626'; ctx.fill();
      label([REP.p[0], REP.p[1] - 26 / view.s], REP.here ? '📍 지금 위치' : '📋 보고 자리', 12, '#fff', REP.here ? 'rgba(29,78,216,.92)' : 'rgba(185,28,28,.9)'); hit.push({ x: rs[0], y: rs[1], r: 16, it: { kind: 'report' } }); }
    if (sel) { ctx.beginPath(); ctx.arc(sel.x, sel.y, sel.r + 5, 0, Math.PI * 2); ctx.lineWidth = 3; ctx.strokeStyle = '#facc15'; ctx.stroke(); }
    if (document.body.classList.contains('legon')) legend();
    needRegions();
    // 축척
    var mScale = [100, 200, 500, 1000, 2000].filter(function (m) { return m * view.s > 60; })[0] || 2000;
    ctx.fillStyle = dark ? '#e2e8f0' : '#0f172a'; ctx.fillRect(12, H - 22, mScale * view.s, 4); ctx.font = '11px system-ui'; ctx.textAlign = 'left'; ctx.fillText(mScale >= 1000 ? mScale / 1000 + 'km' : mScale + 'm', 12, H - 30);
  }

  // ---------- 누름 · 끌기 · 확대 ----------
  var ptrs = {}, drag = null, pinch = null;
  cv.addEventListener('pointerdown', function (e) { cv.setPointerCapture(e.pointerId); ptrs[e.pointerId] = [e.offsetX, e.offsetY]; var ks = Object.keys(ptrs);
    if (ks.length === 1) drag = { x: e.offsetX, y: e.offsetY, cx: view.cx, cy: view.cy, moved: 0 };
    else if (ks.length === 2) { var a = ptrs[ks[0]], b = ptrs[ks[1]]; pinch = { d: Math.hypot(a[0] - b[0], a[1] - b[1]), s: view.s, m: M((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) }; drag = null; } });
  cv.addEventListener('pointermove', function (e) { if (!ptrs[e.pointerId]) return; ptrs[e.pointerId] = [e.offsetX, e.offsetY]; var ks = Object.keys(ptrs);
    if (pinch && ks.length === 2) { var a = ptrs[ks[0]], b = ptrs[ks[1]], d = Math.hypot(a[0] - b[0], a[1] - b[1]); zoomAt(pinch.s * d / pinch.d, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2, pinch.m); return; }
    if (drag) { var dx = e.offsetX - drag.x, dy = e.offsetY - drag.y; drag.moved = Math.max(drag.moved, Math.abs(dx) + Math.abs(dy)); view.cx = drag.cx - dx / view.s; view.cy = drag.cy - dy / view.s; draw(); } });
  function up(e) { var wasTap = drag && drag.moved < 6 && !RPLP.fired; delete ptrs[e.pointerId]; if (Object.keys(ptrs).length < 2) pinch = null; if (wasTap) tap(e.offsetX, e.offsetY); if (!Object.keys(ptrs).length) drag = null; }
  cv.addEventListener('pointerup', up); cv.addEventListener('pointercancel', function (e) { delete ptrs[e.pointerId]; drag = null; pinch = null; });
  cv.addEventListener('wheel', function (e) { e.preventDefault(); zoomAt(view.s * (e.deltaY < 0 ? 1.18 : 1 / 1.18), e.offsetX, e.offsetY); }, { passive: false });
  function zoomAt(ns, sx, sy, anchor) { ns = Math.max(0.03, Math.min(3, ns)); var m = anchor || M(sx, sy); view.s = ns; view.cx = m[0] - (sx - cv.clientWidth / 2) / ns; view.cy = m[1] - (sy - cv.clientHeight / 2) / ns; if (on.bld && ns > 0.12) loadBld(); draw(); }
  $('m2dIn').onclick = function () { zoomAt(view.s * 1.5, cv.clientWidth / 2, cv.clientHeight / 2); };
  $('m2dOut').onclick = function () { zoomAt(view.s / 1.5, cv.clientWidth / 2, cv.clientHeight / 2); };
  $('m2dFit').onclick = function () { fitAll = !fitAll; this.textContent = fitAll ? '격자' : '전체'; fit(); if (on.bld && view.s > 0.12) loadBld(); draw(); };

  // ---------- 눌러서 보기 ----------
  function inRing(r, x, y) { var c = false; for (var i = 0, j = r.length - 1; i < r.length; j = i++) { if (((r[i][1] > y) !== (r[j][1] > y)) && (x < (r[j][0] - r[i][0]) * (y - r[i][1]) / (r[j][1] - r[i][1]) + r[i][0])) c = !c; } return c; }
  function dongAtM(m) { var AD = allDong(); for (var k = 0; k < AD.length; k++) { var d = AD[k]; if (m[0] < d.box[0] || m[0] > d.box[1] || m[1] < d.box[2] || m[1] > d.box[3]) continue; for (var p = 0; p < d.polys.length; p++) if (inRing(d.polys[p][0], m[0], m[1]) && !d.polys[p].slice(1).some(function (h) { return inRing(h, m[0], m[1]); })) return d; } return null; }
  function inPoly(d, m) { if (m[0] < d.box[0] || m[0] > d.box[1] || m[1] < d.box[2] || m[1] > d.box[3]) return false; for (var p = 0; p < d.polys.length; p++) if (inRing(d.polys[p][0], m[0], m[1]) && !d.polys[p].slice(1).some(function (h) { return inRing(h, m[0], m[1]); })) return true; return false; }
  function nearAtM(m) { for (var k = 0; k < NEAR.length; k++) if (!RGUN[NEAR[k].gu] && inPoly(NEAR[k], m)) return NEAR[k]; return null; }
  function tap(x, y) {
    TAPM = M(x, y);
    if (RAD.pick && document.body.classList.contains('radon')) { RAD.c = M(x, y); RAD.pick = false; radRun(); return; }
    var best = null, bd = 1e9;
    hit.forEach(function (h) { var d = Math.hypot(h.x - x, h.y - y); if (d <= h.r + 4 && d < bd) { bd = d; best = h; } });
    if (!best && on.rnet) { var rl = rnAt(x, y); if (rl) best = { x: x, y: y, r: 6, it: { kind: 'rnl', l: rl } }; }
    if (on.land && (!best || /^(g250|l250|f250|a10|rtg|hmg|jgg|jgc)$/.test(best.it.kind))) best = { x: x, y: y, r: 6, it: { kind: 'land', m: M(x, y) } };   // 필지를 켜면 칸(면) 자료보다 필지가 먼저 · 점은 그대로
    if (!best && (UNIT ? UNIT !== 'dong' : (on.upb || on.jurk || on.usgg))) { var mu = M(x, y), uu = unitAt(mu); if (uu) { var su = S(mu); best = { x: su[0], y: su[1], r: 6, it: { kind: 'unit', u: uu } }; } }
    if (!best && on.juris && JRS) { var mj = M(x, y); if (jrsAt('edu', mj) != null || jrsAt('court', mj) != null) best = { x: x, y: y, r: 6, it: { kind: 'jrs', m: mj } }; }
    if (!best && on.ri) { var r0 = riAtM(M(x, y)); if (r0) { var sr = S(r0.p); best = { x: sr[0], y: sr[1], r: 6, it: { kind: 'ri', r: r0 } }; } }
    if (!best && on.jur) { var j0 = jurAtM(M(x, y)); if (j0) { var sj = S(j0.c); best = { x: sj[0], y: sj[1], r: 6, it: { kind: 'jur', J: j0 } }; } }
    if (!best) { var d0 = dongAtM(M(x, y)); if (d0) { var s = S(d0.c); best = { x: s[0], y: s[1], r: 6, it: { kind: 'dong', d: d0 } }; } }
    if (!best) { var d1 = nearAtM(M(x, y)); if (d1) { var s1 = S(d1.c); best = { x: s1[0], y: s1[1], r: 6, it: { kind: 'near', d: d1 } }; } }
    sel = best; show(best ? best.it : null); draw();
  }
  function unent(t) { return String(t == null ? '' : t).replace(/<!\[CDATA\[|\]\]>/g, '').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&'); }
  function esc(t) { return String(t == null ? '' : t).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function row(k, v) { return '<div class="r"><b>' + esc(k) + '</b><span>' + v + '</span></div>'; }
  function src(t) { return '<div class="src">' + esc(t) + '</div>'; }
  // v0.10.83 24시간 막대 = 아래에 시각 숫자 · 붐빔(그 막대의 가장 작은 값~가장 큰 값 사이 위쪽 25%)/보통/한산(아래쪽 30%) 색 · 지금 시각 테 — 소유자 「시간을 숫자로 · 붐비는 시간대를 색을 달리」
  var BUSY = 0.75, QUIET = 0.30, C_BUSY = '#dc2626', C_QUIET = '#cbd5e1';
  function hourLv(v, mx, mn) { var t = (v - (mn || 0)) / Math.max(1e-9, mx - (mn || 0)); return t >= BUSY ? 2 : t < QUIET ? 0 : 1; }
  function hourAxis(lv) { var hh = nowH(); return '<div class="hx">' + lv.map(function (l, i) { return '<span class="' + (l === 2 ? 'b' : '') + (i === hh ? ' n' : '') + '">' + i + '</span>'; }).join('') + '</div>'; }
  function hourKey(lv, color) { var b = []; lv.forEach(function (l, i) { if (l === 2) b.push(i); }); var r = [], s0 = null;
    b.forEach(function (h, k) { if (s0 == null) s0 = h; if (b[k + 1] !== h + 1) { r.push(s0 === h ? s0 + '시' : s0 + '~' + h + '시'); s0 = null; } });
    return '<div class="hk"><i style="background:' + C_BUSY + '"></i>붐빔' + (r.length ? ' <b>' + r.join(' · ') + '</b>' : '') + ' <i style="background:' + (color || '#3b82f6') + '"></i>보통 <i style="background:' + C_QUIET + '"></i>한산 <i class="nw"></i>지금</div>'; }
  function bar(arr, color, lab, fmt) { if (!arr.some(function (v) { return +v; })) return '<div class="nil">이 기간 값이 모두 0 — 자료에 기록이 없다</div>';
    var mx = Math.max.apply(null, arr) || 1;
    if (arr.length === 24 && !lab) { var mn = Math.min.apply(null, arr), lv = arr.map(function (v) { return hourLv(v, mx, mn); }), hh = nowH();
      return vxRow(arr, hh) + '<div class="bars h24">' + arr.map(function (v, i) { return '<i title="' + i + '시 ' + Math.round(v).toLocaleString() + '" class="' + (i === hh ? 'n' : '') + '" style="height:' + Math.round(v / mx * 100) + '%;background:' + (lv[i] === 2 ? C_BUSY : lv[i] === 0 ? C_QUIET : (color || '#3b82f6')) + '"></i>'; }).join('') + '</div>' + hourAxis(lv) + hourKey(lv, color); }
    var ok = lab && lab.length === arr.length;
    return vxRow(arr, null, fmt) +
      '<div class="bars">' + arr.map(function (v, i) { return '<i title="' + esc(ok ? String(lab[i]).replace(/<[^>]+>/g, '') : String(i)) + ' ' + shortN(v) + '" style="height:' + Math.round(v / mx * 100) + '%;background:' + (color || '#3b82f6') + '"></i>'; }).join('') + '</div>' +
      (ok ? '<div class="lx">' + lab.map(function (t) { return '<span>' + t + '</span>'; }).join('') + '</div>' : ''); }
  // v0.10.86 막대 눈금 글자 — 소유자 「세로 막대에 몇 년도인지 숫자로 · 막대만 덜렁 있으니 이해하기 어렵다」
  // v0.10.87 막대 위 값 — 소유자 「모든 막대에 숫자 · 좁으면 작게 · 지저분하면 처음·끝·중요한 것만」: 12칸 이하면 전부, 넘으면 처음·끝·가장 큰 값(·지금 시각)
  function vxRow(arr, now, fmt) { var F = fmt === 'w' ? wonS : shortN; var n = arr.length, mx = -Infinity, im = 0; arr.forEach(function (v, i) { if (v > mx) { mx = v; im = i; } });
    var show = n <= 12 ? null : [0, n - 1, im].concat(now != null ? [now] : []);
    return '<div class="vx' + (n > 12 ? ' many' : '') + '">' + arr.map(function (v, i) { var on = show ? show.indexOf(i) >= 0 : true;
      return '<span class="' + (i === im && n > 1 ? 'mx' : '') + (now === i ? ' n' : '') + '">' + (on && v ? F(v) : '') + '</span>'; }).join('') + '</div>'; }
  function wonS(v) { return won(v).replace(/원$/, ''); }   // 만원 단위 값 → 「6,347만」「1.9억」
  function shortN(v) { v = +v || 0; var a = Math.abs(v); return a >= 1e8 ? (v / 1e8).toFixed(a >= 1e9 ? 0 : 1) + '억' : a >= 1e4 ? (v / 1e4).toFixed(a >= 1e5 ? 0 : 1) + '만' : a >= 100 ? Math.round(v).toLocaleString() : a >= 10 ? Math.round(v) : (Math.round(v * 10) / 10); }
  function yLab(y0, n) { var o = []; for (var i = 0; i < n; i++) o.push('<b>' + String(y0 + i).slice(0, 2) + '</b>' + String(y0 + i).slice(2)); return o; }
  function qLab(qs) { return qs.map(function (q) { return q[4] === '1' ? "'" + q.slice(2, 4) : ''; }); }
  var LB_Y16 = yLab(2016, 10), LB_TB6 = ['0~6', '6~11', '11~14', '14~17', '17~21', '21~24'], LB_TB4 = ['0~6', '6~12', '12~18', '18~24'], LB_DW = ['월', '화', '수', '목', '금', '토', '일'],
    LB_AGE6 = ['10대', '20대', '30대', '40대', '50대', '60+'];
  function ageLab(n) { var o = []; for (var i = 0; i < n; i++) o.push(i === 0 ? '~9' : i === n - 1 && n < 10 ? i * 10 + '+' : i * 10 + '대'); return o; }
  function show(it) {
    var card = $('m2dCard'), h = '';
    if (!it) { card.classList.remove('on'); return; }
    if (it.kind === 'report') {
      var nn = nearestRealNode(REP.p), dd = nn ? Math.round(dTrue(nn.p, REP.p)) : 0;
      if (nn && dd <= 800) { show({ kind: 'node', n: nn, st: accOf(nn), rep: dd }); return; }
      h = '<h3>' + (REP.here ? '📍 지금 위치' : '📋 보고 자리') + '</h3>' + row('가까운 교차로', '없음(800m 안) — 서초구 밖일 수 있음') + repAround() + hereRows() + src('T-Book 최초보고가 넘긴 좌표 — 이 기기 안에서만 쓰고 어디에도 저장하지 않는다');
    } else if (it.kind === 'near') {
      var nd = it.d, cnt = function (arr, ll) { return (arr || []).filter(function (q) { var v = ll(q); return v && inPoly(nd, P(v[0], v[1])); }).length; };
      var nS = D.sig ? cnt(D.sig.spots, function (q) { return [q.lon, q.lat]; }) : 0, nE = D.evt && D.evt.events ? cnt(D.evt.events.items, function (q) { return q.lat ? [q.lon, q.lat] : null; }) : 0, nC = D.cam ? cnt(D.cam.items, function (q) { return [q.lon, q.lat]; }) : 0;
      var touch = NODES.filter(function (n) { if (!n.real) return false; if (inPoly(nd, n.p)) return true; var m = 1e9; nd.polys.forEach(function (Pg) { Pg[0].forEach(function (q) { m = Math.min(m, dTrue(q, n.p)); }); }); return m < 120; });
      h = '<h3>🏘 ' + esc(nd.gu + ' ' + nd.name) + '</h3>' + row('자리', '서초구 밖 — 맞닿은 동') + (touch.length ? row('맞닿은 교차로', touch.map(function (n) { return esc(n.name); }).join(' · ')) : '') +
        row('이 동 안의 자료', '신호 ' + nS + '곳 · 단속 카메라 ' + nC + '대 · 행사 ' + nE + '건') + '<p class="desc">이 지도가 자세히 가진 것은 서초구 자료다(인구·사고·국가유산 등). 이웃 구는 경계와 이름, 그리고 서초 자료에 함께 들어온 신호·행사만 보인다.</p>' +
        src('경계: 통계청 SGIS 행정동(2026.7 · 공공누리 1유형) · 서초구 경계에서 1.5km 안의 동');
    } else if (it.kind === 'rgo') {   // 찾기 — 아직 안 받은 구의 동
      h = '<h3>🏘 ' + esc(it.g + ' ' + it.name) + '</h3><p class="desc">이 구 자료를 받는 중…</p>'; RWANT = { gu: it.gu, name: it.name }; if (!on.dong) { on.dong = true; saveOn(); paintLayers(); } setTimeout(draw, 0);
    } else if (it.kind === 'dong' && it.d.rg) { h = rDongCard(it.d);
    } else if (it.kind === 'dong') {
      var d = it.d, p = d.pop; h = '<h3>🏘 ' + esc(d.name) + '</h3>'; var jz = jurDongLine(d.name); if (jz) h += row('경찰서 관할', jz);
      if (p) { h += row('주민', p.tot.toLocaleString() + '명'); h += row('19세 이하', Math.round((p.age[0] + p.age[1]) / p.tot * 100) + '%') + row('70세 이상', Math.round((p.age[7] + p.age[8] + p.age[9]) / p.tot * 100) + '%');
        h += '<div class="cap">주민 연령대별 인구(명 · 주민등록 · 0~9세 … 90~99세)</div>' + bar(p.age, '#8b5cf6', ageLab(p.age.length)); }
      var lv = liveNow(d);
      if (lv) { h += row('생활인구 지금', lv.n.toLocaleString() + '명 <em>(' + (lv.we ? '주말' : '평일') + ' ' + lv.h + '시 평균)</em>') + row('하루 폭', Math.min.apply(null, lv.arr).toLocaleString() + ' ~ ' + Math.max.apply(null, lv.arr).toLocaleString() + '명') +
        '<div class="cap">시간대별 생활인구(명 · 그 시각 동 안에 있는 사람 · 0~23시 ' + (lv.we ? '주말' : '평일') + ' 평균)</div>' + bar(lv.arr, '#f97316'); }
      h += salesRows(d) + dongIndRows(d);
      var ag = D.st && D.st.agg && D.st.agg[d.name];   // 🏪 등록 상가(소상공인시장진흥공단 · v0.10.65)
      if (ag) h += row('등록 상가', (ag.all || 0).toLocaleString() + '곳 · 음식 ' + (ag.food || 0) + ' · 주점 ' + (ag.bar || 0) + ' · 노래방·PC방 ' + (ag.play || 0) + ' · 숙박 ' + (ag.inn || 0) + ' · 편의점 ' + (ag.conv || 0));
      var sz2 = D.sz ? D.sz.zones.filter(function (z) { var q = P(z.lon, z.lat); return inPoly(d, q); }).length : 0; if (D.sz) h += row('어린이보호구역', sz2 + '곳');
      var ns = NODES.filter(function (n) { return n.dong && (n.dong.dong === d.name || (n.dong.also || []).indexOf(d.name) >= 0); });
      if (ns.length) h += row('걸친 교차로', ns.map(function (n) { return esc(n.name); }).join(' · '));
      h += facRows('11650', d.name, null);
      h += polRows(d.k, d.c); h += jrsRows(d.k); h += fdRows(d.k); h += econRows(d.k);
      if (d.k) h += '<div class="lg-btns"><button data-ai="11650|' + esc(d.k || '') + '">🤖 AI용 복사 — 이 동 기본 자료</button></div>';
      if (FRN && FRN.gu['11650']) h += row('외국인 주민(구)', (FRN.gu['11650']['2024'].tot || 0).toLocaleString() + '명 <em>(서초구 · 2024)</em>') + '<div class="lg-btns"><button data-frn="11650">🌏 외국인 자세히(국적·영주·나이·성별)</button></div>';
      h += src('경계: 통계청 SGIS 행정동(2026.7 · 공공누리 1유형) · 인구: 행정안전부 주민등록(2026.8)' + (lv ? ' · 생활인구: 서울시(2026.7 · KT 통신 자료 추정)' : ''));
    } else if (it.kind === 'node') {
      var n = it.n, st = it.st; h = '<h3>' + (n.real ? '🚦 ' : '✕ ') + esc(n.name) + '</h3>' + (it.rep ? row(REP.here ? '지금 위치' : '보고 자리', (REP.here ? '지금 위치에서 ' : 'T-Book 보고 자리에서 ') + it.rep + 'm') + repAround() + hereRows() : '') + row('도로', esc(n.pair.replace('×', ' × ')));
      if (!n.real) { h += row('실제', '두 도로가 만나지 않는다 — ' + esc(n.why || ('최단 ' + n.gap + 'm'))) + '<p class="desc">게임 지도(격자)에는 교차로가 있지만 실제 길에는 없다. 사고·신호 자료를 이 자리에 붙이지 않는다.</p>' + src('OpenStreetMap(ODbL) · 2026-09-28 · 두 도로의 모든 선분 사이 최단 거리');
        card.classList.remove('haslad'); card.innerHTML = '<div class="grab" aria-hidden="true"><i></i></div><button class="x" id="m2dX">닫기</button>' + h; card.classList.add('on'); $('m2dX').onclick = function () { sel = null; show(null); draw(); }; return; }
      h += row('신호 교차로', n.sig ? esc(n.sig.name) + ' <em>#' + esc(n.sig.no) + '</em>' : '<em>공개 신호 목록(C-ITS)에 없음</em>');
      if (n.nameSrc) h += row('이름', '<em>' + esc(n.nameSrc) + '</em>');
      if (n.dong) h += row('행정동', esc(n.dong.dong) + ((n.dong.also || []).length ? ' · ' + esc(n.dong.also.join('·')) + ' <em>경계</em>' : ''));
      if (n.y10) { var t19 = accN(n, 2019, 2025); h += row('사고 2019~2025', t19 + '건 · 사망 ' + deadN(n, 2019, 2025) + '명 <em>(사망사고 기록)</em> · 해마다 평균 ' + Math.round(t19 / 7)) + row('2016~2025', accN(n, 2016, 2025) + '건 · 사망·중상자 ' + n.sev + ' · 보행자 피해 ' + n.ped) +
        '<div class="cap">해마다 교통사고 건수(건 · 2016~2025 · 585m 안 100m 칸을 이 교차로에 배정)</div>' + bar(n.y10, '#ea580c', LB_Y16) + (n.d10.some(function (v) { return v; }) ? '<div class="cap">해마다 교통사고 사망자 수(명 · 2016~2025 · 사망사고 기록)</div>' + bar(n.d10, '#111827', LB_Y16) : ''); }
      if (st && st.total) { h += row('사고(2023~25)', st.total + '건 · 사망 ' + st.death + ' · 중상 ' + st.serious + ' · 경상 ' + st.slight);
        h += row('주된 경위', st.violations.slice(0, 3).map(function (v) { return esc(v[0]) + ' ' + v[1]; }).join(' · ')) + row('사고 유형', st.types.slice(0, 3).map(function (v) { return esc(v[0]) + ' ' + v[1]; }).join(' · '));
        h += src('TAAS 도로교통공단 · 반경 약 585m 안 사고를 가장 가까운 교차로에 배정(근사)'); }
      var sp = D.sig && D.sig.spots ? D.sig.spots.filter(function (s) { return Math.hypot(P(s.lon, s.lat)[0] - n.p[0], P(s.lon, s.lat)[1] - n.p[1]) < 120; })[0] : null;
      if (sp) h += row('신호 지금', sigNow(sp));
      var v = D.vol && D.vol.spots ? D.vol.spots.filter(function (x) { return x.node && x.node[0] === n.i && x.node[1] === n.j; })[0] : null;
      if (v) h += volRows(v);
      h += src((n.measured ? '교차점: OSM 두 도로의 모든 선분이 만나는 자리(2026-09-28 실측) · 이름: OSM 신호·교차로 이름' : '교차점: OSM 도로 중심선이 만나는 자리') + ' · 행정동: 반경 50m 안 걸친 동 모두');
    } else if (it.kind === 'hot') {
      var t = it.it; h = '<h3>⚠ ' + esc(t.name) + '</h3>' + row('갈래', esc(it.L.name || '')) + row('사고', (t.total || '-') + '건 · 사망 ' + (t.death || 0) + ' · 중상 ' + (t.serious || 0)) + row('공표', esc(t.year || '')) + src('TAAS 사고다발지 공표자료');
    } else if (it.kind === 'sz') {
      var z = it.z; h = '<h3>🏫 어린이보호구역 · ' + esc(z.name) + '</h3>' + row('대상 시설', esc(z.kind)) + row('주소', esc(z.addr || '-')) + row('관할', esc(z.police || '-')) +
        row('CCTV', z.cctv > 0 ? z.cctv + '대' : z.cctv < 0 ? '있음(대수 모름)' : '없음') + row('보호구역 도로 폭', z.rw ? z.rw + 'm' : '모름') + row('기준일', esc(z.ref || '-')) +
        '<p class="desc">자리는 대상 시설의 점이다 — 보호구역이 걸친 도로 구간(경계선)은 이 자료에 없다. 보호구역 안 제한속도·주정차 금지(08~20시 가중)는 표지를 보고 확인한다.</p>';
      h += src((D.sz.source || {}).zones || '');
    } else if (it.kind === 'szh') {
      var t2 = it.t; h = '<h3>🧒 보호구역 어린이 사고 다발지</h3>' + row('곳', esc(t2.name)) + row('공표', t2.year + '년') + row('사고', t2.acc + '건 · 사상 ' + t2.cas + '(사망 ' + t2.dead + ' · 중상 ' + t2.ser + ' · 경상 ' + t2.sli + ')');
      h += src((D.sz.source || {}).hot || '');
    } else if (it.kind === 'cam') {
      var cm = it.c; h = '<h3>📷 무인 단속 카메라</h3>' + row('자리', esc(cm.at)) + row('도로', esc(cm.road)) + row('제한속도', cm.lim ? cm.lim + 'km/h' : '-') + row('설치', esc(cm.yr || '-')) + row('단속구분 코드', esc(cm.se) + ' <em>(코드 뜻은 대조 전)</em>');
      h += camEff(cm) + ledgLine('R4') + src('경찰청 전국무인교통단속카메라표준데이터(기준일 2026-04-06) · 설치 전후 사고 = TAAS 사고 10년(100m 칸)');
    } else if (it.kind === 'sig') {
      var s = it.s; h = '<h3>🚦 ' + esc(s.name) + '</h3>' + row('교차로 번호', esc(s.no)) + row('지금', sigNow(s)) + src('경찰청 교차로계획정보(공공데이터포털) · 계획값 — 감응·수동 운영 중에는 다르다');
    } else if (it.kind === 'sub') {
      h = '<h3>🚇 ' + esc(it.s.name) + '</h3>' + row('노선', (it.s.lines || []).map(function (l) { return '<i class="ln" style="background:' + (LINE_C[l] || '#64748b') + '">' + esc(l) + '</i>'; }).join(' ')) + row('교차로', esc(it.n.name)) + src('자리는 교차로 기준(출입구 위치 아님) · 역 이름은 지도 파일');
    } else if (it.kind === 'her') {
      var hr = it.h; h = '<h3>🏛 ' + esc(hr.name) + '</h3>' + row('종류', esc(hr.kind)) + row('시대', esc(hr.era || '-')) + row('주소', esc(hr.addr || '-')) + '<p class="desc">' + esc(unent(hr.desc).slice(0, 220)) + '…</p>' + src('국가유산청 국가유산 목록');
    } else if (it.kind === 'vol') {
      h = '<h3>🚙 ' + esc(it.v.name) + '</h3>' + volRows(it.v) + src('서울시 교통량조사(VolInfo) · 평일은 2일 평균');
    } else if (it.kind === 'evt') {
      var e = it.e; h = '<h3>📅 ' + esc(e.t) + '</h3>' + row('갈래', esc(e.c)) + row('기간', esc(e.s + ' ~ ' + e.e)) + row('시간', esc(e.hour || '-')) + row('자리', esc(e.p)) + row('요금', esc(e.free || '-')) + src('서울시 문화행사 정보(공공누리 1유형)');
    } else if (it.kind === 'ri') { h = riCard(it.r);
    } else if (it.kind === 'land') { h = landCard(it);
    } else if (it.kind === 'jgc') { h = jgCard(it);
    } else if (it.kind === 'unit') { h = unitCard(it);
    } else if (it.kind === 'ggc') { h = ggcCard(it);
    } else if (it.kind === 'rnl') { var l = it.l; h = '<h3>🛣 ' + esc(l.nm || '(이름 없는 길)') + '</h3>' + row('등급', esc(RNG[l.g] || l.g)) + row('제한속도', l.ms ? l.ms + 'km/h' : '자료 없음') + '<p class="desc">국가교통정보센터 표준노드링크(도로 한 토막 = 링크). 등급은 도로법상 도로 종류다. 차로 수·통행량은 이 자료에 없다 — 서울 조사 지점은 「🚙 시간대 교통량」.</p>' + src(RN.src || ITSL.src || '국가교통정보센터 표준노드링크');
    } else if (it.kind === 'vols') { h = volsCard(it.v);
    } else if (it.kind === 'exv') { h = exvCard(it.u);
    } else if (it.kind === 'stay') { h = stayCard(it);
    } else if (it.kind === 'rpost' || it.kind === 'rnear') { h = rpCard(it);
    } else if (it.kind === 'minbak') { var mb = it.s; h = '<h3>🏡 ' + esc(mb[2]) + '</h3>' + row('상태', mb[3] ? '<b>휴업</b>' : '영업') + row('주소', esc(mb[5])) + row('객실수', mb[4] != null ? mb[4] + '실' : '자료 없음') + row('인허가', esc(mb[6])) + (mb[8] ? row('자리', '원본에 좌표가 없어 주소로 찾음') : '') + '<p class="desc">외국인관광 도시민박업(관광진흥법) — 외국인 관광객에게 집을 내주는 민박. 투숙 인원·국적은 공개되지 않는다.</p>' + src(it.m.source);
    } else if (it.kind === 'flodge') { var fl = it.s; h = '<h3>🏨 ' + esc(fl[2]) + '</h3>' + row('업종', esc(fl[3]) + (fl[4] && fl[4] !== '도시민박' ? ' · ' + esc(fl[4]) : '')) + row('주소', esc(fl[5])) + row('인허가', esc(fl[6])) + '<p class="desc">' + esc(FLODGE.note) + '</p>' + src(FLODGE.source);
    } else if (it.kind === 'busd') { var bd = it.s; h = '<h3>🚌 ' + esc(bd[0]) + ' <small>(' + esc(bd[1]) + ')</small></h3>' + row('승차 하루 평균', bd[4].toLocaleString() + '명') + row('하차 하루 평균', bd[5].toLocaleString() + '명') + '<p class="desc">' + esc(BUSD.note) + '</p>' + src(BUSD.source);
    } else if (it.kind === 'msub') { var ms = it.s; h = '<h3>🚇 ' + esc(ms[0]) + '역 <small>(대구 도시철도)</small></h3>' + row('하차 하루 평균', ms[3].toLocaleString() + '명') + '<p class="desc">' + esc(MSUB.note) + '</p>' + src(MSUB.source);
    } else if (it.kind === 'jrs') { h = jrsCard(it);
    } else if (it.kind === 'pst') { h = pstCard(it.s);
    } else if (it.kind === 'pbx') { h = pbxCard(it.b);
    } else if (it.kind === 'frn') { h = frnCard(it.gu);
    } else if (it.kind === 'ai') { h = aiCard(it);
    } else if (it.kind === 'hmg' || it.kind === 'hmc') { h = homeCard(it);
    } else if (it.kind === 'g250' || it.kind === 'l250' || it.kind === 'f250' || it.kind === 'rtc' || it.kind === 'rtg') { h = gridCard(it);
    } else if (it.kind === 'a10' || it.kind === 'f10') { h = a10Card(it);
    } else if (it.kind === 'bizpin') { bizGo(it.k); return;
    } else if (it.kind === 'rent') { h = rentCard(it.it);
    } else if (it.kind === 'store') { var so = it.s, C3 = SIDX ? SIDX.cls[so.c] : null; h = '<h3>🏬 ' + esc(so.n) + '</h3>' + (C3 ? row('업종', esc(C3[1] + ' › ' + C3[3] + ' › ' + C3[4])) : '') + (so.f ? row('층', esc(so.f) + '층') : '') + (RAD.c ? row('반경 가운데에서', Math.round(dTrue(so.p, RAD.c)) + 'm') : '') + '<p class="desc">등록된 상가 정보다 — 영업 중인지·매출은 이 자료에 없다.</p>' + src(SIDX ? SIDX.source + ' · 기준 ' + SIDX.stdrYm : '');
    } else if (it.kind === 'lak') { h = akCard(it);
    } else if (it.kind === 'lkma') { h = kmaCard();
    } else if (it.kind === 'leq') { h = eqCard(it);
    } else if (it.kind === 'lbs') { h = bsCard(it);
    } else if (it.kind === 'lbv') { h = bvCard(it);
    } else if (it.kind === 'jcnm') { h = jnCard(it);
    } else if (it.kind === 'rdnm') { h = rdCard(it);
    } else if (it.kind === 'lev') { h = levCard(it);
    } else if (it.kind === 'lspd') { h = spdCard(it);
    } else if (it.kind === 'lcc') { h = ccCard(it);
    } else if (it.kind === 'lair') { h = airCard(it);
    } else if (it.kind === 'lwx') { h = lwxCard(it);
    } else if (it.kind === 'jgg') { h = jggCard(it);
    } else if (it.kind === 'szone') { h = szCard(it);
    } else if (it.kind === 'ggt') { h = ggtCard(it);
    } else if (it.kind === 'trd') { h = trdCard(it);
    } else if (it.kind === 'season') { h = seasonCard(it);
    } else if (it.kind === 'safe') { h = safeCard(it);
    } else if (['crowd', 'link', 'osmroad', 'hot10', 'jct'].indexOf(it.kind) >= 0) {
      h = flowCard(it);
    } else if (['jur', 'jurst', 'tgis', 'spot', 'spota'].indexOf(it.kind) >= 0) {
      h = extraCard(it);
    } else if (it.kind === 'pub') {
      h = pubCard(it);
    } else if (it.kind === 'rally') {
      var r = it.r; h = '<h3>🪧 집회' + (r.march ? '·행진' : '') + '</h3>' + row('때', esc(r.d + ' ' + r.from + '~' + r.to)) + row('자리', esc(r.p)) + row('신고 인원', (r.n || '-') + '명 <em>(신고값)</em>') + (r.approx ? row('자리 표시', '<em>근사</em> — ' + esc(r.note)) : '');
      h += src('서울경찰청 「오늘의 주요집회」 · 주최자는 담지 않았다');
    }
    if (it.kind === 'dong' && it.d && it.d.c) { h += talkDong(it.d) + '<div class="lg-btns"><button data-story="1">📝 이 동 풀어 읽기</button><button data-pnlhere="' + (it.d.c[0] / KX + LON0).toFixed(5) + ',' + (LAT0 - it.d.c[1] / KY).toFixed(5) + '">💰 여기서 손익 계산</button></div><div id="storyBox"></div>'; }
    card.classList.remove('haslad'); card.innerHTML = '<div class="grab" aria-hidden="true"><i></i></div><button class="x" id="m2dX">닫기</button><div id="m2dLad"></div>' + h + '<div id="m2dLadB"></div>'; card.classList.add('on');
    $('m2dX').onclick = function () { sel = null; show(null); draw(); };
    try { ladderFill(it); } catch (e) {}
  }
  // ---------- 공공데이터 묶음(pubdata) ----------
  var PUB = null;
  function pubPrep() {
    var p = D.pub; if (!p) return;
    PUB = { fac: {}, hosp: [], er: [], phar: [], heat: [], cold: [], bike: [], bus: [], subr: [], drunk: [], risk: [], sigx: [] };
    Object.keys((p.fac && p.fac.cats) || {}).forEach(function (c) { var k = FAC_K[c]; if (!k) return; PUB.fac[k] = p.fac.cats[c].map(function (o) { return { name: o.name, p: P(o.lon, o.lat), cat: c, er: o.er, ref: o.ref }; }); });
    var S2 = p.seoul || {};
    (S2.hosp || []).forEach(function (o) { var q = { name: o.name, p: P(o.lon, o.lat), o: o }; PUB.hosp.push(q); if (o.er) PUB.er.push(q); });
    (S2.phar || []).forEach(function (o) { PUB.phar.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    (S2.heat || []).forEach(function (o) { PUB.heat.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    (S2.cold || []).forEach(function (o) { PUB.cold.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    (S2.bike || []).forEach(function (o) { PUB.bike.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    ((p.bus && p.bus.items) || []).forEach(function (o) { PUB.bus.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    ((p.subway && p.subway.items) || []).forEach(function (o) { PUB.subr.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    ((p.drunk && p.drunk.items) || []).forEach(function (o) { PUB.drunk.push({ name: o.name, p: P(o.lon, o.lat), ring: (o.ring || []).map(function (q) { return P(q[0], q[1]); }), o: o }); });
    ((p.risk && p.risk.items) || []).forEach(function (o) { PUB.risk.push({ name: o.name, p: P(o.lon, o.lat), ring: (o.ring || []).map(function (q) { return P(q[0], q[1]); }), o: o }); });
    ((p.sigx && p.sigx.items) || []).forEach(function (o) { PUB.sigx.push({ name: o.name, p: P(o.lon, o.lat), o: o }); });
    // 👮 경찰 관서 = **공식 목록**(v0.10.63 · 경찰청 지구대·파출소 주소 현황 + 경찰민원24 경찰서) — OSM 표기(중복·틀린 이름)를 갈아 끼운다
    var ST = D.st; PUB.st = { bar: [], play: [], inn: [], conv: [] };
    if (ST && ST.pts) ST.pts.forEach(function (a) { var sub = ST.sub[a[3]], g = ST.group[sub]; if (!PUB.st[g]) return; PUB.st[g].push({ name: a[0], p: P(a[2], a[1]), sub: sub, dong: ST.dong[a[4]], fl: a[5] }); });
    if (PUB.st.conv.length) PUB.fac.conv = PUB.st.conv.map(function (q) { return { name: q.name, p: q.p, cat: '편의점', o: q, stq: 1 }; });   // 상가정보 편의점(등록 481곳)이 OSM 을 갈아 끼운다
    var PL = D.police;
    if (PL && PL.boxes) PUB.fac.pol = (PL.stations || []).map(function (o) { return { name: o.name, p: P(o.lon, o.lat), cat: '경찰서', o: o, off: 1, st: 1 }; })
      .concat(PL.boxes.map(function (o) { return { name: o.name, p: P(o.lon, o.lat), cat: o.kind, o: o, off: 1 }; }))
      .concat((PL.centers || []).map(function (o) { return { name: o.name, p: P(o.lon, o.lat), cat: '치안센터', o: o, off: 1, ctr: 1 }; }));   // v0.10.66 치안센터(공식 목록)
  }
  // 등록된 운영시간(월~일·공휴일 8칸 「0900-1930」)으로 지금 여는지
  function openNow(hs) {
    if (!hs) return null; var parts = hs.split(' '), d = new Date(), i = (d.getDay() + 6) % 7, t = parts[i];
    if (!t || t === '-') return false; var m = /(\d{4})-(\d{4})/.exec(t); if (!m) return null;
    var s = +m[1], c = +m[2], now = d.getHours() * 100 + d.getMinutes();
    if (c > 2400) return now >= s || now < c - 2400;   // 자정 넘어 여는 곳(예: 0900-2600)
    if (c <= s) return now >= s || now < c;
    return now >= s && now < c;
  }
  function hoursTxt(hs) { if (!hs) return '-'; var N = ['월', '화', '수', '목', '금', '토', '일', '공휴일']; return hs.split(' ').map(function (t, i) { return N[i] + ' ' + (t === '-' ? '휴무' : t.replace(/(\d\d)(\d\d)-(\d\d)(\d\d)/, '$1:$2~$3:$4')); }).join(' · '); }
  function liveArr(d) { if (d.rg || d.pre) return d.live || null; var L = D.pub && D.pub.livepop && D.pub.livepop.dong; return L && L[d.name] || null; }
  function liveMax(key, h) { var c = key + h; if (LMX[c] == null) { var m = 0; allDong().forEach(function (d) { var a = liveArr(d); if (a) m = Math.max(m, a[key][h]); }); LMX[c] = m; } return LMX[c]; }   // 서울 전체(받은 구까지) 한 눈금
  function liveNow(x) {
    var d = typeof x === 'string' ? { name: x } : x, A = liveArr(d); if (!A) return null;
    var dt = new Date(pickDate() + 'T00:00'), we = dt.getDay() === 0 || dt.getDay() === 6, h = nowH(), key = we ? 'we' : 'wd';
    return { n: A[key][h], max: liveMax(key, h), we: we, h: h, arr: A[key], other: A[we ? 'wd' : 'we'] };
  }
  function ring(pts, fill, stroke) { if (!pts || pts.length < 3) return; path(pts); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); ctx.lineWidth = 1.5; ctx.strokeStyle = stroke; ctx.stroke(); }
  // ---------- 관할 · T-GIS · 길목(v0.10.74 — T-Book 교통관리 요청) ----------
  var JUR = [], TG = [], TGC = {}, SPOTS = [], SPA = [];
  var JUR_C = { seocho: ['rgba(37,99,235,.10)', '#2563eb'], bangbae: ['rgba(13,148,136,.12)', '#0d9488'], banpo: ['rgba(124,58,237,.10)', '#7c3aed'],
    yongsan: ['rgba(234,88,12,.06)', '#c2410c'], dongjak: ['rgba(22,163,74,.06)', '#15803d'], gwanak: ['rgba(202,138,4,.07)', '#a16207'], geumcheon: ['rgba(120,113,108,.06)', '#57534e'],
    gangnam: ['rgba(219,39,119,.06)', '#be185d'], suseo: ['rgba(147,51,234,.06)', '#7e22ce'], songpa: ['rgba(8,145,178,.06)', '#0e7490'], gwacheon: ['rgba(101,163,13,.07)', '#4d7c0f'], sujeong: ['rgba(225,29,72,.06)', '#be123c'] };
  var SPA_C = { '음주': '#b45309', '이륜차': '#dc2626', '보행자': '#2563eb', '자전거': '#16a34a', '어린이': '#ca8a04', '고령자': '#7c3aed' };
  function extraPrep() {
    if (D.jur) JUR = D.jur.zones.map(function (z) { var rings = z.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); var r0 = rings[0], sx = 0, sy = 0; r0.forEach(function (q) { sx += q[0]; sy += q[1]; }); return { z: z, rings: rings, c: [sx / r0.length, sy / r0.length] }; });
    if (D.tgis) { TG = D.tgis.items.map(function (o) { return { c: o[0], name: o[1], p: P(o[3], o[2]), par: o[4], pe: o[5], cits: o[6] }; }); TG.forEach(function (t) { TGC[t.c] = t; }); }
    if (D.spot) { SPOTS = D.spot.stops.map(function (o) { var nt = 0; [22, 23, 0, 1].forEach(function (k) { nt += o.h[k]; }); var day = o.h.reduce(function (a, b) { return a + b; }, 0); return { o: o, name: o.n, p: P(o.lo, o.la), day: day, night: day ? nt / day : 0 }; });
      SPA = D.spot.spots.map(function (o) { return { o: o, name: o.n, p: P(o.lo, o.la) }; }); }
  }
  function spotHour() { return nowH(); }
  function nowH() { return HOUR != null ? HOUR : new Date().getHours(); }
  function spotRank() { var h = spotHour(); return SPOTS.slice().sort(function (a, b) { return b.o.h[h] - a.o.h[h]; }); }
  function jurAtM(m) { for (var k = 0; k < JUR.length; k++) { if (JUR[k].rings.some(function (r) { return inRing(r, m[0], m[1]); })) return JUR[k]; } return null; }
  function jurOfDong(nm) { var z = null; if (D.jur) D.jur.zones.forEach(function (x) { if (x.dongs.indexOf(nm) >= 0) z = x; }); return z; }
  function jurSplit(nm) { return D.jur && D.jur.split ? D.jur.split.filter(function (x) { return x.dong === nm; })[0] || null : null; }   // 도로로 갈린 동(반포4동 = 반포대로 서쪽 방배서 · 동쪽 서초서)
  function jurDongLine(nm) { var z = jurOfDong(nm); if (z) return esc(z.name); var sp = jurSplit(nm); if (!sp) return ''; var zn = function (id) { return (D.jur.zones.filter(function (x) { return x.id === id; })[0] || {}).name || id; };
    return esc(sp.road) + ' 서쪽 ' + esc(zn(sp.west)) + ' · 동쪽 ' + esc(zn(sp.east)) + ' <em>(현장 지식 · T-GIS 관할과 맞음)</em>'; }
  function drawExtra(dark) {
    if (on.jur && JUR.length) {
      JUR.forEach(function (J) { var c = JUR_C[J.z.id] || ['rgba(100,116,139,.1)', '#64748b'];
        J.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = c[0]; ctx.fill(); if (J.z.id === 'banpo') { ctx.save(); ctx.clip(); ctx.strokeStyle = 'rgba(124,58,237,.22)'; ctx.lineWidth = 1; for (var x = -cv.clientHeight; x < cv.clientWidth; x += 12) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x + cv.clientHeight, cv.clientHeight); ctx.stroke(); } ctx.restore(); }
          path(r); ctx.closePath(); ctx.lineWidth = 3; ctx.strokeStyle = c[1]; ctx.stroke(); });
        });
      (D.jur.split || []).forEach(function (sp) { (sp.line || []).forEach(function (ln) { path(ln.map(function (q) { return P(q[0], q[1]); })); ctx.setLineDash([10, 6]); ctx.lineWidth = 3; ctx.strokeStyle = dark ? '#fbbf24' : '#b45309'; ctx.stroke(); ctx.setLineDash([]); }); });
      JUR.forEach(function (J) { var c = JUR_C[J.z.id] || ['rgba(100,116,139,.1)', '#64748b'];
        var nm = J.z.id === 'banpo' ? '서초서·방배서 번지로 나눔' : J.z.name.replace('서울', '');
        label(J.c, nm, view.s > 0.12 ? 14 : 12, c[1], dark ? 'rgba(15,22,36,.8)' : 'rgba(255,255,255,.88)'); var s = S(J.c); hit.push({ x: s[0], y: s[1], r: 16, it: { kind: 'jur', J: J } }); });
      (D.jur.stations || []).forEach(function (st) { var zz = JUR.filter(function (J) { return J.z.name === st.name; })[0]; dot(P(st.lon, st.lat), 7, zz && JUR_C[zz.z.id] ? JUR_C[zz.z.id][1] : '#2563eb', '#fff', { kind: 'jurst', st: st }); });
    }
    if (on.tgis && TG.length && view.s > 0.07) {
      TG.forEach(function (t) { if (!t.par || t.par === t.c || !TGC[t.par]) return; path([t.p, TGC[t.par].p]); ctx.lineWidth = 1.2; ctx.strokeStyle = dark ? 'rgba(251,191,36,.6)' : 'rgba(180,83,9,.55)'; ctx.stroke(); });
      TG.forEach(function (t) { var s = S(t.p), r = t.par ? 2.5 : 4; ctx.beginPath(); ctx.arc(s[0], s[1], r * zk(), 0, Math.PI * 2); ctx.fillStyle = t.pe === 380 ? '#0d9488' : '#1d4ed8'; ctx.fill(); ctx.lineWidth = 1.2; ctx.strokeStyle = t.par ? '#f59e0b' : '#fff'; ctx.stroke(); hit.push({ x: s[0], y: s[1], r: 7, it: { kind: 'tgis', t: t } });
        if (view.s > 0.4 && !t.par) label([t.p[0], t.p[1] - 11 / view.s], t.name, 10, dark ? '#e2e8f0' : '#334155', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
    }
    if (on.spota && SPA.length) SPA.forEach(function (q) { dot(q.p, 4 + q.o.yrs * 1.2, SPA_C[q.o.k] || '#64748b', '#fff', { kind: 'spota', q: q }); });
    if (on.spot && SPOTS.length) { var h = spotHour(); spotRank().slice(0, 15).forEach(function (q, k) { var v = q.o.h[h]; if (!v) return; var s = S(q.p), r = Math.max(7, Math.sqrt(v) * 0.9) * zk();
      ctx.beginPath(); ctx.arc(s[0], s[1], r, 0, Math.PI * 2); ctx.fillStyle = q.o.t === 's' ? 'rgba(14,165,233,.35)' : 'rgba(234,88,12,.32)'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = q.o.t === 's' ? '#0369a1' : '#c2410c'; ctx.stroke();
      ctx.font = 'bold 12px system-ui, sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = dark ? '#fff' : '#111827'; ctx.fillText(String(k + 1), s[0], s[1]); hit.push({ x: s[0], y: s[1], r: Math.max(9, r), it: { kind: 'spot', q: q, rank: k + 1 } }); }); }
  }
  function extraCard(it) {
    var h = '';
    if (it.kind === 'jur') { var z = it.J.z; h = '<h3>🚓 ' + esc(z.id === 'banpo' ? '반포동 — 서초서·방배서가 번지로 나눔' : z.name + ' 관할') + '</h3>' + row('행정동', esc(z.dongs.join(' · '))) + enfRows(z.name) + polStats(z.name) + '<p class="desc">' + esc(z.note) + '</p>' + (D.jur.src ? '<p class="desc">반포동 나눔 — ' + esc(D.jur.src) + '</p>' : '') + src(D.jur.law + ' · ' + D.jur.boundary); }
    else if (it.kind === 'jurst') { var st = it.st; h = '<h3>🚓 ' + esc(st.name) + '</h3>' + (st.addr ? row('청사', esc(st.addr)) : '') + (st.tel ? row('대표번호', esc(st.tel)) : '') + enfRows(st.name) + polStats(st.name) + src('경찰민원24 청사 좌표(T-Book PS_PTS)'); }
    else if (it.kind === 'tgis') { var t = it.t, pa = t.par ? TGC[t.par] : null; h = '<h3>🚥 ' + esc(t.name) + '</h3>' + row('T-GIS 교차로코드', String(t.c)) + row('관할', t.pe === 380 ? '서울방배경찰서' : '서울서초경찰서') + (t.par && t.par !== t.c ? row('연동교차로코드', t.par + ' → ' + (pa ? esc(pa.name) + ' · ' + Math.round(dTrue(pa.p, t.p)) + 'm' : '이 구역 밖') + (/연등/.test(t.name) ? ' <em>(「(연등)」 종속 신호)</em>' : ' <em>(그 교차로에 딸려 도는 신호)</em>')) : '') + (t.cits ? row('C-ITS 번호', String(t.cits) + ' <em>(15m 안 같은 신호)</em>') : '') + src(D.tgis.source + ' · 신호 현시·주기는 이 표에 없다'); }
    else if (it.kind === 'spot') { var q = it.q, o = q.o, hh = spotHour(); h = '<h3>🎯 ' + esc(q.name) + '</h3>' + row('종류', o.t === 's' ? '지하철역' + (o.g === '경계' ? ' <em>(구 경계 — 이웃 구와 나눠 셈)</em>' : '') : '버스 정류장') + row(hh + '시 하차', o.h[hh].toLocaleString() + '명(하루 평균) · 서초 ' + it.rank + '위') + row('하루 하차', q.day.toLocaleString() + '명') + row('밤 22~01시 비중', Math.round(q.night * 100) + '%') + '<div class="cap">시간대별 하차 인원(명/시 · 0~23시 · 하루 평균 · 교통카드)</div>' + bar(o.h, o.t === 's' ? '#0284c7' : '#ea580c') + src(D.spot.source + ' · ' + D.spot.method); }
    else if (it.kind === 'spota') { var a = it.q.o; h = '<h3>🗂 ' + esc(a.k) + ' 다발지 — ' + esc(a.n) + '</h3>' + row('뽑힌 해', esc(a.y) + (a.yrs > 1 ? ' <em>(' + a.yrs + '해 — 고질 자리)</em>' : '')) + row('사고', a.c + '건 · 사상 ' + a.cs + (a.d ? ' · 사망 ' + a.d : '')) + '<p class="desc">참고 — 1년 전 자료·연 1회 갱신. 「0건」은 사고 없음이 아니다.</p>' + src(D.spot.source); }
    return h;
  }
  function drawPub(dark) {
    if (!PUB) return;
    if (on.risk) PUB.risk.forEach(function (q) { ring(q.ring, 'rgba(220,38,38,.18)', '#b91c1c'); dot(q.p, 5, '#b91c1c', '#fff', { kind: 'pub', layer: 'risk', q: q }); });
    if (on.drunk) PUB.drunk.forEach(function (q) { ring(q.ring, 'rgba(168,85,247,.18)', '#7e22ce'); dot(q.p, 6, '#7e22ce', '#fff', { kind: 'pub', layer: 'drunk', q: q }); });
    if (on.sigx && view.s > 0.12) PUB.sigx.forEach(function (q) { var s = S(q.p); ctx.fillStyle = dark ? '#94a3b8' : '#334155'; ctx.fillRect(s[0] - 3, s[1] - 3, 6, 6); hit.push({ x: s[0], y: s[1], r: 7, it: { kind: 'pub', layer: 'sigx', q: q } });
      if (view.s > 0.45) label([q.p[0], q.p[1] + 12 / view.s], q.o.no, 10, dark ? '#cbd5e1' : '#334155', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.8)'); });
    var hh = nowH();
    if (on.bus && view.s > 0.07) PUB.bus.forEach(function (q) { var f = FLOW.bus[q.o.id]; if (f) { var a = f[0][hh], b = f[1][hh]; if (a + b < (view.s < 0.14 ? 60 : 3)) return; dot(q.p, 2.5 + Math.sqrt(a + b) / 4.5, onoffC(a, b, .62), onoffC(a, b, 1), { kind: 'pub', layer: 'bus', q: q }); return; }
      if (view.s < 0.14 && q.o.day < 2000) return; dot(q.p, 2.5 + Math.sqrt(q.o.day) / 18, 'rgba(22,163,74,.55)', '#166534', { kind: 'pub', layer: 'bus', q: q }); });
    if (on.subr) PUB.subr.forEach(function (q) { var f = FLOW.sub[q.name]; if (f) { var a = f[0][hh], b = f[1][hh]; dot(q.p, 4 + Math.sqrt(a + b) / 7, onoffC(a, b, .55), onoffC(a, b, 1), { kind: 'pub', layer: 'subr', q: q }); if (view.s > 0.1) label([q.p[0], q.p[1] + 18 / view.s], q.name + ' ' + (a + b).toLocaleString(), 10.5, dark ? '#e0f2fe' : '#075985', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); return; }
      dot(q.p, 4 + Math.sqrt(q.o.on + q.o.off) / 22, 'rgba(14,165,233,.45)', '#075985', { kind: 'pub', layer: 'subr', q: q }); });
    if (on.bike && view.s > 0.1) PUB.bike.forEach(function (q) { dot(q.p, 3.5, '#16a34a', '#fff', { kind: 'pub', layer: 'bike', q: q }); });
    if (on.pol && PUB.fac.pol && PUB.fac.pol[0] && PUB.fac.pol[0].off) PUB.fac.pol.forEach(function (q) {   // 공식 관서: 경찰서는 크게 · 자리가 근사면 옅게
      dot(q.p, q.st ? 8 : q.ctr ? 4 : 5.5, q.st ? '#1e3a8a' : q.ctr ? '#0f766e' : (q.o.approx ? '#93c5fd' : '#2563eb'), '#fff', { kind: 'pub', layer: 'pol', q: q });
      if (view.s > (q.st ? 0.06 : 0.14)) label([q.p[0], q.p[1] - (q.st ? 16 : 12) / view.s], q.name.replace(/^서울/, ''), q.st ? 11 : 10, dark ? '#bfdbfe' : '#1e3a8a', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.85)');
    });
    Object.keys(PUB.fac).forEach(function (k) { if (!on[k] || (k === 'pol' && PUB.fac.pol[0] && PUB.fac.pol[0].off)) return; var small = PUB.fac[k].length > 80 && view.s < 0.1; PUB.fac[k].forEach(function (q) { dot(q.p, small ? 2.5 : 4.5, FAC_C[k] || '#64748b', small ? null : '#fff', small ? null : { kind: 'pub', layer: k, q: q }); }); });
    if (on.hosp && view.s > 0.1) PUB.hosp.forEach(function (q) { if (q.o.er) return; dot(q.p, 3.5, '#0891b2', '#fff', { kind: 'pub', layer: 'hosp', q: q }); });
    if (on.er) PUB.er.forEach(function (q) { dot(q.p, 8, '#dc2626', '#fff', { kind: 'pub', layer: 'er', q: q }); if (view.s > 0.08) label([q.p[0], q.p[1] - 16 / view.s], q.name, 11, dark ? '#fecaca' : '#7f1d1d', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.85)'); });
    if (on.phar) PUB.phar.forEach(function (q) { var op = openNow(q.o.h); dot(q.p, 4.5, op ? '#16a34a' : '#94a3b8', '#fff', { kind: 'pub', layer: 'phar', q: q }); });
    var STC = { bar: '#b45309', play: '#db2777', inn: '#7c3aed' };
    ['bar', 'play', 'inn'].forEach(function (g) { if (!on[g] || !PUB.st || (view.s < 0.07 && g === 'bar')) return; PUB.st[g].forEach(function (q) { dot(q.p, view.s < 0.12 ? 2.8 : 4, STC[g], view.s < 0.12 ? null : '#fff', { kind: 'pub', layer: g, q: q }); }); });
    if (on.heat) PUB.heat.forEach(function (q) { dot(q.p, 4.5, '#f97316', '#fff', { kind: 'pub', layer: 'heat', q: q }); });
    if (on.cold) PUB.cold.forEach(function (q) { dot(q.p, 4.5, '#38bdf8', '#fff', { kind: 'pub', layer: 'cold', q: q }); });
  }
  var PUB_T = { risk: '🟥 사고위험지역', drunk: '🍺 음주 사고 다발지', sigx: '🔢 신호 교차로', bus: '🚌 버스 정류장', subr: '🚇 지하철 승하차', bike: '🚲 따릉이 대여소', hosp: '🩺 병원·의원', er: '🏥 응급실', phar: '💊 약국', heat: '🥵 무더위쉼터', cold: '🥶 한파쉼터' };
  function pubCard(it) {
    var q = it.q, o = q.o || {}, k = it.layer, p = D.pub || {}, h = '<h3>' + esc((PUB_T[k] || (LAYERS.filter(function (l) { return l[0] === k; })[0] || [0, '📍'])[1]) + ' · ' + (q.name || '(이름 없음)')) + '</h3>', s = '';
    if (k === 'risk') { h += row('사고', o.acc + '건 · 사망 ' + o.dead + ' · 중상 ' + o.ser + ' · 경상 ' + o.sli) + row('주된 원인', esc([].concat(o.cause || []).join(' · ') || '-')) + '<p class="desc">' + esc(q.name) + '</p>'; s = p.risk && p.risk.source; }
    else if (k === 'drunk') { h += row('사고', o.acc + '건 · 사상 ' + o.caslt + '(사망 ' + o.dead + ' · 중상 ' + o.ser + ' · 경상 ' + o.sli + ')') + (o.year ? row('자료 해', o.year + '년 공표') : '') + '<p class="desc">음주 단속·순찰 동선을 잡을 때 참고 — 이 구역 둘레(다각형)에서 음주 사고가 몰렸다.</p>'; s = p.drunk && p.drunk.source; }
    else if (k === 'sigx') { h += row('신호 교차로 번호', esc(o.no)) + (/연등/.test(q.name) ? row('종류', '연동 보조 신호') : ''); s = p.sigx && p.sigx.source; }
    else if (k === 'bus') { var fb = FLOW.bus[o.id]; if (fb) { h += onoffRows(fb); s = o.rg ? o.rg.source.bus : D.flow.bus.source; } else { h += row('하루 승하차', o.day.toLocaleString() + '명') + row('가장 붐비는 때', o.peak + '시') + '<div class="cap">시간대별 승차+하차 인원(명/시 · 0~23시 · 하루 평균)</div>' + bar(o.h, '#16a34a'); s = p.bus && p.bus.source; } }
    else if (k === 'subr') { var fs = FLOW.sub[q.name]; h += row('노선', esc((fs ? fs[2] : o.lines || []).join(' · '))); if (fs) { h += onoffRows(fs) + subTrend(q.name); s = o.rg ? o.rg.source.sub : D.flow.subway.source + (D.trend ? ' · 여러 해: ' + D.trend.subway.source : ''); } else { h += row('하루 승차', o.on.toLocaleString() + '명') + row('하루 하차', o.off.toLocaleString() + '명'); s = p.subway && p.subway.source; } }
    else if (k === 'bike') { h += row('대여소 번호', esc(o.no)) + row('거치대', o.n + '대'); s = p.seoul && p.seoul.source; }
    else if (k === 'hosp' || k === 'er') { var op = openNow(o.h); h += row('종류', esc((o.div || '') + (o.er ? ' · 응급실 운영' : ''))) + (o.emcls && !/이외/.test(o.emcls) ? row('응급 등급', esc(o.emcls)) : '') + row('전화', esc(o.tel || '-')) + (o.ertel ? row('응급실 전화', esc(o.ertel)) : '') +
        row('지금', o.er ? '응급실 24시간(등록값)' : (op === null ? '시간 정보 없음' : op ? '<b style="color:#16a34a">진료 중</b>' : '진료 시간 아님')) + row('주소', esc(o.addr || '-')) + '<div class="cap">' + esc(hoursTxt(o.h)) + '</div>'; s = p.seoul && p.seoul.source; }
    else if (k === 'phar') { var op2 = openNow(o.h); h += row('지금', op2 === null ? '시간 정보 없음' : op2 ? '<b style="color:#16a34a">영업 중</b>' : '닫음') + row('전화', esc(o.tel || '-')) + row('주소', esc(o.addr || '-')) + '<div class="cap">' + esc(hoursTxt(o.h)) + '</div>'; s = p.seoul && p.seoul.source; }
    else if (k === 'heat' || k === 'cold') { h += row('시설', esc(o.type || '-')) + (o.days ? row('여는 날', esc(o.days)) : '') + (o.time && o.time !== '~' ? row('시간', esc(o.time)) : '') + (o.cap ? row('수용', o.cap + '명') : '') + row('주소', esc(o.addr || '-')) + (o.note ? '<p class="desc">' + esc(o.note) + '</p>' : ''); s = p.seoul && p.seoul.source; }
    else if (k === 'bar' || k === 'play' || k === 'inn' || (k === 'conv' && q.stq)) {
      var o3 = q.stq ? q.o : q; h += row('업종', esc(o3.sub)) + row('행정동', esc(o3.dong || '-')) + (o3.fl ? row('층', esc(o3.fl)) : '') +
        '<p class="desc">등록 상가 정보다 — 지금 영업 중인지·영업시간은 담지 않는다. 밤 순찰·주취 신고 동선 참고용.</p>';
      s = (D.st || {}).source;
    }
    else if (k === 'pol' && q.off) {
      var PL = D.police || {}, S3 = PL.source || {};
      h += row('구분', esc(q.cat)) + (q.st ? row('대표번호', esc(q.o.tel)) + row('관할', esc(q.o.gu)) + enfRows(q.o.name || q.name || '') + polStats(q.o.name || q.name || '') : row('소속', esc(q.o.station) + (q.ctr ? ' · ' + esc(q.o.box) : '')) + row('주소', esc(q.o.addr))) +
        (q.st ? '' : row('자리', (q.o.approx ? '⚠ ' : '') + esc(q.o.locNote || '')));
      s = q.st ? S3.stations : ((q.ctr ? S3.centers : S3.boxes) + ' · ' + S3.loc);
    }
    else { h += row('갈래', esc(q.cat || '')) + (q.ref ? row('출구', esc(q.ref)) : '') + (k === 'pol' ? '<p class="desc">⚠ 경찰 관서는 OpenStreetMap 표기 그대로다(공식 목록 data/police-seocho.json 을 읽지 못했다).</p>' : ''); s = p.fac && p.fac.source; }
    return h + src(s || '');
  }
  // ---------- 🗺 바탕 지도(v0.10.76 · OSM 전 도로·물·녹지·철도·주차장) ----------
  //  소유자 「지금 지도가 거칠고 부족하고 허술해 보여 — 제대로 된 지도를 구현하자」. 간선 10개만 긋던 것을 OSM 도로 전부로.
  //  자료 공간은 P() 와 같다(평면 m · 127.01/37.49 기준). 종류별로 Path2D 를 한 번 만들고, 그릴 때는 캔버스 변환만 바꾼다(끌기·확대가 가볍다).
  // v0.10.90 바탕 = 조각(소유자 「서울시 전역·경기도 전역 · 조각조각 나누어 받게」) — 개관 1장(고속·주간선·큰 물·큰 숲·철도) + 8km 조각(data/base/t/ix_iz.json)
  //  화면에 걸린 조각만 받는다(배율 TILE_S 넘을 때) · 너무 많아지면 먼 조각부터 내려놓는다 · 꼴은 옛 base-seocho.json(tg-base/1)과 같다
  var OSM = null, OSMN = [], OSMLAB = [], WLAB = [], JLAB = [], OSMBN = {}, PACKS = [], OVP = null, TILES = {}, TLOAD = {}, BIDX = null, BSET = {}, TILE_S = 0.045, TMAX = 64, TBAKE = '';
  var RCLS = { m: '고속·도시고속', p: '주간선', s: '보조간선', t: '집산', r: '국지·주거', l: '연결로', v: '단지·서비스', f: '보행', c: '자전거' };
  var RSTY = {   // 종류: 실제 폭(m) · 최소 px · 보이기 시작하는 배율 · [채움, 테두리] 낮 · 밤
    m: [24, 3.2, 0, ['#f9c56b', '#c9801c'], ['#b7791f', '#7c5212']], p: [21, 2.8, 0, ['#ffe08a', '#d4a12a'], ['#9a7b2c', '#6b5420']],
    s: [16, 2.3, 0, ['#fff2c2', '#cdb06a'], ['#6d6447', '#4b4533']], l: [8, 1.6, 0.05, ['#ffe7a3', '#cdb06a'], ['#7a6a3e', '#4b4533']],
    t: [12, 1.9, 0.04, ['#ffffff', '#b9c1cc'], ['#4a5568', '#2d3748']], r: [7, 1.2, 0.07, ['#ffffff', '#c7cdd6'], ['#3d4a5e', '#27303f']],
    v: [4.5, 0.8, 0.2, ['#ffffff', '#d6dbe2'], ['#344055', '#252e3d']], c: [2, 0.9, 0.3, ['#22a35a', null], ['#3fbf78', null]], f: [1.6, 0.8, 0.35, ['#a0a9b6', null], ['#64748b', null]]
  };
  var RORD = ['v', 'r', 't', 'l', 's', 'p', 'm'];
  function decLine(a, from) { var out = [], x = a[from], z = a[from + 1]; out.push([x, z]); for (var i = from + 2; i < a.length; i += 2) { x += a[i]; z += a[i + 1]; out.push([x, z]); } return out; }
  function addLine(pa, pts) { pa.moveTo(pts[0][0], pts[0][1]); for (var i = 1; i < pts.length; i++) pa.lineTo(pts[i][0], pts[i][1]); }
  function addRings(pa, rr) { rr.forEach(function (a) { var pts = decLine(a, 0); addLine(pa, pts); pa.closePath(); }); }
  function lenOf(pts) { var L = 0; for (var i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; }
  function midOf(pts) { var L = lenOf(pts) / 2; for (var i = 1; i < pts.length; i++) { var a = pts[i - 1], b = pts[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L <= d) { var u = L / (d || 1); return { p: [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u], ang: Math.atan2(b[1] - a[1], b[0] - a[0]) }; } L -= d; } return { p: pts[0], ang: 0 }; }
  var JR = /(사거리|삼거리|오거리|교차로|입구|네거리|IC|나들목|JC|분기점)$/;
  function addJunctions(cand, pk) {
    cand.sort(function (a, b) { return (JR.test(b[0]) ? 1 : 0) - (JR.test(a[0]) ? 1 : 0); });
    cand.forEach(function (c) {
      if (NODES.some(function (n) { return Math.hypot(n.p[0] - c[1][0], n.p[1] - c[1][1]) < 60; })) return;
      if (JLAB.some(function (o) { var d = Math.hypot(o.p[0] - c[1][0], o.p[1] - c[1][1]); return d < 25 || (o.name === c[0] && d < 150); })) return;
      JLAB.push({ name: c[0], p: c[1], major: JR.test(c[0]), pk: pk });
    });
  }
  function prepPack(B, key) {   // 한 묶음(개관 또는 조각)을 Path2D 로 — 이름표는 공용 목록에 key 를 달아 넣는다(내려놓을 때 같이 지운다)
    var K = { key: key, ov: key === 'ov', road: {}, green: { wood: new Path2D(), park: new Path2D(), pitch: new Path2D(), cem: new Path2D() }, water: new Path2D(), ww: [new Path2D(), new Path2D()], wwT: new Path2D(), rail: new Path2D(), railT: new Path2D(), pk: new Path2D() };
    if (B.tile) { var T = B.size; K.box = [B.tile[0] * T, B.tile[1] * T, (B.tile[0] + 1) * T, (B.tile[1] + 1) * T]; }
    var NM = B.names || [];
    Object.keys(B.roads || {}).forEach(function (c) {
      var R = K.road[c] = { n: new Path2D(), t: new Path2D(), b: new Path2D(), cnt: 0 };
      B.roads[c].forEach(function (f) { var pts = decLine(f, 2), fl = f[1]; addLine(fl & 2 ? R.t : fl & 1 ? R.b : R.n, pts); if (fl & 1) addLine(R.n, pts); R.cnt++;
        var nm = f[0] >= 0 ? NM[f[0]] : ''; if (!nm || fl & 2) return; var L = lenOf(pts), m = midOf(pts);
        if ('mpstr'.indexOf(c) >= 0 && L > 60) OSMLAB.push({ name: nm, c: c, p: m.p, ang: m.ang, L: L, pk: key, ov: K.ov });
        if (K.ov) return; var e = OSMBN[nm]; if (!e) { OSMBN[nm] = e = { name: nm, c: c, p: m.p, L: L, n: 0 }; OSMN.push(e); } e.n++; if (L > e.L) { e.p = m.p; e.L = L; e.c = c; } });
    });
    var PR = { m: 0, p: 1, s: 2, t: 3, r: 4 }; OSMLAB.sort(function (a, b) { return PR[a.c] - PR[b.c] || b.L - a.L; });
    var GK = { forest: 'wood', wood: 'wood', scrub: 'wood', park: 'park', garden: 'park', grass: 'park', grassland: 'park', recreation_ground: 'park', playground: 'park', golf_course: 'park', pitch: 'pitch', cemetery: 'cem' };
    function cen(pts) { var sx = 0, sy = 0; pts.forEach(function (q) { sx += q[0]; sy += q[1]; }); return [sx / pts.length, sy / pts.length]; }
    function area(pts) { var a = 0; for (var i = 0, j = pts.length - 1; i < pts.length; j = i++) a += pts[j][0] * pts[i][1] - pts[i][0] * pts[j][1]; return Math.abs(a) / 2; }
    (B.green || []).forEach(function (g) { addRings(K.green[GK[g[1]] || 'park'], g[2]); var nm = g[0] >= 0 ? NM[g[0]] : ''; if (nm && /공원|산|숲/.test(nm)) { var pts = decLine(g[2][0], 0), A = area(pts); if (A > 20000) WLAB.push({ name: nm, p: cen(pts), k: 'g', A: A, pk: key, ov: K.ov }); } });
    (B.water || []).forEach(function (w) { addRings(K.water, w[1]); var nm = w[0] >= 0 ? NM[w[0]] : ''; if (nm) { var pts = decLine(w[1][0], 0), A = area(pts); if (A > 300000 || /강$|천$|저수지$|호$/.test(nm)) WLAB.push({ name: nm, p: cen(pts), k: 'w', A: 1e9, big: A > 4000000 || /강$/.test(nm), pk: key, ov: K.ov }); } });   // 단지 안 연못·분수는 이름을 달지 않는다
    (B.waterways || []).forEach(function (w) { var pts = decLine(w, 3); addLine(w[2] & 2 ? K.wwT : K.ww[w[1] ? 1 : 0], pts); var nm = w[0] >= 0 ? NM[w[0]] : ''; if (nm && !(w[2] & 2) && lenOf(pts) > 300) { var m = midOf(pts); WLAB.push({ name: nm, p: m.p, ang: m.ang, k: 'ww', A: lenOf(pts), pk: key, ov: K.ov }); } });
    (B.rail || []).forEach(function (r) { var pts = decLine(r, 3); addLine(r[2] & 2 ? K.railT : K.rail, pts); });
    (B.parking || []).forEach(function (rr) { addRings(K.pk, rr); });
    WLAB.sort(function (a, b) { return b.A - a.A; });
    // 교차로 이름(v0.10.78 · 소유자 「삼거리·사거리 이름을 빠짐없이」) — 조각에 서울 C-ITS·OSM 이름 · 같은 이름 150m 안·다른 이름 25m 안은 하나만
    if (!K.ov) addJunctions((B.junctions || []).map(function (j) { return [j[0], [j[1], j[2]]]; }), key);
    return K;
  }
  function basePrep() {
    if (typeof Path2D === 'undefined') return;
    // 서초 둘레 T-GIS 신호 교차로·C-ITS(공공 자료) 이름을 먼저 — 조각 이름보다 앞에 선다
    var cand = []; TG.forEach(function (t) { if (!/연등/.test(t.name)) cand.push([t.name, t.p]); });
    if (PUB) PUB.sigx.forEach(function (q) { if (q.name && !/연등/.test(q.name)) cand.push([q.name, q.p]); });
    addJunctions(cand, 'pub');
    if (D.bidx) { BIDX = D.bidx; TBAKE = String(BIDX.bake || BIDX.total || ''); BIDX.tiles.forEach(function (t) { BSET[t[0] + '_' + t[1]] = t[2]; });
      // 새로 구운 조각이 올라오면 보관함의 옛 조각은 지운다(받은 지역 표시는 다시 받으라고 비워진다)
      if ('caches' in window) caches.open('tg-tiles').then(function (c) { c.keys().then(function (ks) { ks.forEach(function (r) { if (r.url.indexOf('b=' + encodeURIComponent(TBAKE)) < 0) c.delete(r); }); }); }).catch(function () {}); }
    if (D.ov) { OVP = prepPack(D.ov, 'ov'); OSM = OVP; }
  }
  function visTiles() { if (!BIDX) return []; var W = cv.clientWidth, H = cv.clientHeight, a = M(0, 0), b = M(W, H), T = BIDX.size, out = [];
    for (var ix = Math.floor(Math.min(a[0], b[0]) / T); ix <= Math.floor(Math.max(a[0], b[0]) / T); ix++) for (var iz = Math.floor(Math.min(a[1], b[1]) / T); iz <= Math.floor(Math.max(a[1], b[1]) / T); iz++) { var k = ix + '_' + iz; if (BSET[k]) out.push(k); }
    return out; }
  function tileUrl(k) { return (ONGH ? '/datamap-tiles/t/' : 'data/base/t/') + k + '.json?b=' + encodeURIComponent(TBAKE); }   // v2.8.0 전국 조각은 datamap-tiles 저장소
  var TQ = 0, TRAF = 0;
  function needTiles() { if (!BIDX || view.s < TILE_S) return; var vt = visTiles(); if (vt.length > 24) return;
    vt.forEach(function (k) { if (TILES[k] || TLOAD[k] || TQ >= 4) return; TLOAD[k] = 1; TQ++;
      fetch(tileUrl(k)).then(function (r) { if (!r.ok) throw 0; return r.json(); }).catch(function () { return caches.match(tileUrl(k), { ignoreSearch: true }).then(function (r) { if (!r) throw 0; return r.json(); }); }).then(function (j) { TILES[k] = prepPack(j, k); OSM = OSM || TILES[k]; trimTiles(); }).catch(function () {}).then(function () { TQ--; delete TLOAD[k]; if (!TRAF) TRAF = requestAnimationFrame(function () { TRAF = 0; draw(); }); }); }); }
  function trimTiles() { var ks = Object.keys(TILES); if (ks.length <= TMAX) return; var T = BIDX.size;
    ks.sort(function (a, b) { function d(k) { var q = k.split('_'); return Math.hypot((+q[0] + 0.5) * T - view.cx, (+q[1] + 0.5) * T - view.cy); } return d(b) - d(a); });
    ks.slice(0, ks.length - TMAX).forEach(function (k) { delete TILES[k]; var f = function (L) { return L.pk !== k; }; OSMLAB = OSMLAB.filter(f); WLAB = WLAB.filter(f); JLAB = JLAB.filter(f); }); }
  // ---------- 🗺 시·군·구 경계 · 📥 지역 받기(v0.10.90 · 소유자 「GPS 기반으로 구별·지역별로 받거나 골라서 받으면」·「인근 인접도 보이게」) ----------
  var SGG = [];
  function sggPrep() { if (!D.sgg) return; SGG = D.sgg.sgg.map(function (g) { return { g: g, rings: g.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }), c: P(g.c[0], g.c[1]) }; }); }
  function drawSgg(dark) { if (!SGG.length) return; var s = view.s;
    SGG.forEach(function (G) { G.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.setLineDash(s < 0.02 ? [6, 4] : [10, 6]); ctx.lineWidth = s < 0.02 ? 1.4 : 2; ctx.strokeStyle = dark ? 'rgba(203,213,225,.55)' : 'rgba(71,85,105,.55)'; ctx.stroke(); ctx.setLineDash([]); }); });
    if (s < 0.05) SGG.forEach(function (G) { if (s < 0.006 && G.g.sido === '인천광역시') return; label(G.c, G.g.name, s < 0.01 ? 11 : 13, dark ? '#e2e8f0' : '#334155', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.8)'); }); }
  function distToRings(pt, rings) { var inside = false, best = Infinity;
    rings.forEach(function (r) { if (inRing(r, pt[0], pt[1])) inside = true;
      for (var i = 1; i < r.length; i++) { var a = r[i - 1], b = r[i], dx = b[0] - a[0], dz = b[1] - a[1], L = dx * dx + dz * dz, u = L ? Math.max(0, Math.min(1, ((pt[0] - a[0]) * dx + (pt[1] - a[1]) * dz) / L)) : 0; best = Math.min(best, Math.hypot(a[0] + u * dx - pt[0], a[1] + u * dz - pt[1])); } });
    return inside ? 0 : best; }
  var DL_AROUND = 3000;   // 고른 구·시 경계 밖 이만큼(맞닿은 둘레)까지 함께 받는다 — 설계값
  function tilesForRings(rings) { if (!BIDX) return []; var T = BIDX.size, half = T * Math.SQRT1_2;
    return BIDX.tiles.filter(function (t) { var c = [(t[0] + 0.5) * T, (t[1] + 0.5) * T]; return distToRings(c, rings) <= DL_AROUND + half; }).map(function (t) { return t[0] + '_' + t[1]; }); }
  function tilesAround(p, R) { if (!BIDX) return []; var T = BIDX.size, half = T * Math.SQRT1_2;
    return BIDX.tiles.filter(function (t) { return Math.hypot((t[0] + 0.5) * T - p[0], (t[1] + 0.5) * T - p[1]) <= R + half; }).map(function (t) { return t[0] + '_' + t[1]; }); }
  function tbytes(ks) { return ks.reduce(function (a, k) { return a + (BSET[k] || 0); }, 0); }
  function mb(b) { return b >= 1048576 ? (b / 1048576).toFixed(1) + 'MB' : Math.max(1, Math.round(b / 1024)) + 'KB'; }
  var DLKEY = 'tg_map2d_dl';
  function dlDone() { try { return JSON.parse(localStorage.getItem(DLKEY) || '{}'); } catch (e) { return {}; } }
  function dlSave(o) { try { localStorage.setItem(DLKEY, JSON.stringify(o)); } catch (e) {} }
  var DLBUSY = false;
  function dlTiles(name, ks, msg, ext) { if (DLBUSY || !('caches' in window)) { msg('이 브라우저에서는 미리 받기를 쓸 수 없다'); return; } DLBUSY = true;
    ext = ext || []; var all = ks.slice(), n = 0, fail = 0, eb = ext.reduce(function (a, x) { return a + x.b; }, 0), q = ks.map(tileUrl).concat(ext.map(function (x) { return x.u; })), tot = q.length;
    caches.open('tg-tiles').then(function (c) {
      function next() { var u = q.shift(); if (!u) { DLBUSY = false; var o = dlDone(); o[name] = { n: all.length, b: tbytes(all) + eb, d: new Date().toISOString().slice(0, 10), bake: TBAKE, r: ext.length }; dlSave(o); paintDl(); msg('✅ ' + name + ' — 조각 ' + all.length + '개' + (ext.length ? ' + 행정동 자료 ' + ext.length + '개' : '') + '(' + mb(tbytes(all) + eb) + ') 받음' + (fail ? ' · 실패 ' + fail : '') + ' · 통신이 끊겨도 열린다'); return; }
        c.match(u).then(function (hitR) { if (hitR && !/(^|\/)r\/|manifest/.test(u)) return; return c.add(u); }).catch(function () { fail++; }).then(function () { n++; msg('받는 중 ' + n + ' / ' + tot); next(); }); }
      next(); }); }
  function rFilesFor(G, full) {   // v0.10.91 고른 구의 행정동 자료(+ full 이면 둘레 3km 에 걸친 서울 구의 가벼운 자료) — 바탕 조각과 같은 보관함에(서비스워커가 통신 끊김 때 모든 보관함에서 꺼낸다)
    var o = [], sgOf = function (g) { var sf = SIDO_FULL[g.sido]; return SGG.filter(function (x) { return x.g.sido === sf && (x.g.name === g.name || g.name.indexOf(x.g.name) === 0); })[0]; };   // v2.8.0 모든 시도 · 일반구는 시 경계로
    rIdx().forEach(function (g) { var B = g.bytes || {}, S2 = sgOf(g), me = S2 === G;
      if (!me) { if (!full || !S2) return;
        var near = S2.rings.some(function (r) { for (var i = 0; i < r.length; i += 4) if (distToRings(r[i], G.rings) <= DL_AROUND) return true; return false; }); if (!near) return; }
      o.push({ u: rU(g.gu, 'dong.json'), b: B.dong || 0 }); if (me) ['dongx', 'trdar', 'stores', 'transit', 'safety', 'taas10', 'season'].forEach(function (k) { if (B[k]) o.push({ u: rU(g.gu, k + '.json'), b: B[k] }); }); });
    if (o.length) RMANU.forEach(function (u) { o.unshift({ u: u, b: 20000 }); }); return o; }
  function paintDl() { var el = $('m2dGetP'); if (!el || !el.classList.contains('on')) return; var done = dlDone(), h = '';
    h += '<div class="lg-h"><b>📥 지역 받기</b><button id="m2dGetX">닫기</button></div><p class="lg-n">화면에 보이는 곳은 저절로 받는다. 미리 받아 두면 <b>통신이 끊긴 곳에서도</b> 그 지역 지도가 열린다(고른 구·시 경계 밖 ' + (DL_AROUND / 1000) + 'km 둘레까지 함께).</p>';
    h += '<div class="lg-btns"><button data-dl="gps">📍 지금 위치 둘레 6km</button><button data-dl="view">🖥 지금 화면 둘레</button></div><div id="m2dGetMsg" class="lg-n"></div>';
    var SIDO_F = SIDO_FULL;   // v2.8.0 전국 — 받은 권역만(regions.json)
    ((D.ridx && D.ridx.regions) || [{ sido: '11' }, { sido: '41' }]).map(function (r) { return SIDO_F[r.sido]; }).filter(Boolean).forEach(function (sd) { h += '<div class="lg"><b>' + sd + '</b><div class="dlg">' + SGG.filter(function (G) { return G.g.sido === sd; }).map(function (G) { var ks = tilesForRings(G.rings), d = done[G.g.name]; if (d && d.bake !== TBAKE) d = null;
      return '<button data-sg="' + esc(G.g.name) + '" class="' + (d ? 'on' : '') + '">' + (d ? '✓ ' : '') + esc(G.g.name) + ' <small>' + mb(tbytes(ks) + rFilesFor(G).reduce(function (a, x) { return a + x.b; }, 0)) + '</small></button>'; }).join('') + '</div></div>'; });
    var keys = Object.keys(done); h += '<div class="lg-btns"><button data-dl="clear">받은 지역 지우기' + (keys.length ? '(' + keys.length + ')' : '') + '</button></div><small class="lg-n">조각은 OSM 2026-10-03 기준(© OpenStreetMap contributors · ODbL) · 서울 구는 행정동 자료(주민·생활인구·카드 매출)도 함께 받는다 · 그 밖의 자료 층은 아직 서초 둘레</small>';
    el.innerHTML = h; }
  function dlMsg(t) { var m = $('m2dGetMsg'); if (m) m.textContent = t; }
  function dlClick(e) { var b = e.target.closest('button'); if (!b) return;
    if (b.id === 'm2dGetX') { $('m2dGetP').classList.remove('on'); return; }
    var sg = b.getAttribute('data-sg'), dl = b.getAttribute('data-dl');
    if (sg) { var G = SGG.filter(function (x) { return x.g.name === sg; })[0]; if (G) { var ks = tilesForRings(G.rings), rx = rFilesFor(G, true), rb = rx.reduce(function (a, x) { return a + x.b; }, 0); if (confirm(sg + ' 과 둘레 ' + (DL_AROUND / 1000) + 'km — 조각 ' + ks.length + '개' + (rx.length ? ' + 행정동 자료 ' + rx.length + '개' : '') + '(' + mb(tbytes(ks) + rb) + ')를 받을까요?')) dlTiles(sg, ks, dlMsg, rx); } return; }
    if (dl === 'view') { var c = [view.cx, view.cy], W = cv.clientWidth / view.s, H = cv.clientHeight / view.s, ks2 = tilesAround(c, Math.hypot(W, H) / 2 + 2000); if (ks2.length > 120) { dlMsg('화면이 너무 넓다 — 조금 확대한 뒤 받으세요'); return; } dlTiles('화면 둘레 ' + new Date().toLocaleDateString('ko-KR'), ks2, dlMsg); return; }
    if (dl === 'gps') { if (!navigator.geolocation) { dlMsg('위치를 쓸 수 없는 기기'); return; } dlMsg('위치를 잡는 중…'); navigator.geolocation.getCurrentPosition(function (pos) { var p = P(pos.coords.longitude, pos.coords.latitude), ks3 = tilesAround(p, 6000); if (!ks3.length) { dlMsg('지금 위치가 서울·경기 조각 밖이다'); return; } dlTiles('지금 위치 둘레(' + new Date().toLocaleDateString('ko-KR') + ')', ks3, dlMsg); }, function () { dlMsg('위치를 못 잡았다(권한 · 실내)'); }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 600000 }); return; }
    if (dl === 'clear') { if (!confirm('미리 받은 지도 조각을 모두 지울까요?')) return; caches.delete('tg-tiles').then(function () { dlSave({}); paintDl(); dlMsg('지웠다'); }); } }
  if ($('m2dGetB')) $('m2dGetB').onclick = function () { var el = $('m2dGetP'); el.classList.toggle('on'); paintDl(); };
  if ($('m2dGetP')) $('m2dGetP').addEventListener('click', dlClick);
  function basePacks() { var out = [], vt = view.s >= TILE_S ? visTiles() : [], all = vt.length > 0 && vt.every(function (k) { return TILES[k]; });
    if (OVP && !all) out.push(OVP); vt.forEach(function (k) { if (TILES[k]) out.push(TILES[k]); }); return out; }
  function worldT() { var W = cv.clientWidth, H = cv.clientHeight; ctx.setTransform(DPR * view.s, 0, 0, DPR * view.s, DPR * (W / 2 - view.cx * view.s), DPR * (H / 2 - view.cy * view.s)); }
  function screenT() { ctx.setTransform(DPR, 0, 0, DPR, 0, 0); }
  function drawBaseAreas(dark) {
    needTiles(); PACKS = basePacks(); if (!PACKS.length) return; worldT();
    function each(f) { PACKS.forEach(f); }
    ctx.fillStyle = dark ? 'rgba(34,84,52,.55)' : '#cfe6bd'; each(function (K) { ctx.fill(K.green.park, 'evenodd'); });
    ctx.fillStyle = dark ? 'rgba(28,74,44,.75)' : '#b9dba3'; each(function (K) { ctx.fill(K.green.wood, 'evenodd'); });
    ctx.fillStyle = dark ? 'rgba(52,96,60,.6)' : '#bfe0b0'; each(function (K) { ctx.fill(K.green.pitch, 'evenodd'); });
    ctx.fillStyle = dark ? 'rgba(60,80,64,.5)' : '#d6e3cf'; each(function (K) { ctx.fill(K.green.cem, 'evenodd'); });
    if (view.s > 0.25) { ctx.fillStyle = dark ? 'rgba(80,92,110,.35)' : 'rgba(205,210,218,.75)'; each(function (K) { ctx.fill(K.pk, 'evenodd'); }); }
    ctx.fillStyle = dark ? '#1c3b5e' : '#a8d0f0'; each(function (K) { ctx.fill(K.water, 'evenodd'); });
    ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.strokeStyle = dark ? '#2b5a8a' : '#8cc0ea';
    ctx.lineWidth = Math.max(1.6 / view.s, 9); each(function (K) { ctx.stroke(K.ww[1]); }); ctx.lineWidth = Math.max(1.2 / view.s, 4); each(function (K) { ctx.stroke(K.ww[0]); });
    ctx.setLineDash([4 / view.s, 3 / view.s]); ctx.lineWidth = Math.max(1 / view.s, 3); ctx.globalAlpha = 0.6; each(function (K) { ctx.stroke(K.wwT); }); ctx.globalAlpha = 1; ctx.setLineDash([]);
    screenT();
  }
  function drawBaseRoads(dark) {
    needTiles(); PACKS = basePacks(); if (!PACKS.length) return; worldT(); ctx.lineCap = 'round'; ctx.lineJoin = 'round'; var s = view.s, mode = dark ? 4 : 3;   // 바탕 층을 꺼도 길 조각은 받는다
    function each(f) { PACKS.forEach(f); }
    function eachR(c, f) { PACKS.forEach(function (K) { var R = K.road[c]; if (R) f(R); }); }
    // 철도(지상 · 회색 + 흰 줄) — 지하 노선은 옅은 점선
    if (s > 0.05) { ctx.strokeStyle = dark ? '#64748b' : '#8b95a3'; ctx.lineWidth = Math.max(2.6 / s, 4); each(function (K) { ctx.stroke(K.rail); }); ctx.strokeStyle = dark ? '#0f1624' : '#ffffff'; ctx.lineWidth = Math.max(1.2 / s, 1.8); ctx.setLineDash([6 / s, 6 / s]); each(function (K) { ctx.stroke(K.rail); }); ctx.setLineDash([]); }
    else if (s > 0.008) { ctx.strokeStyle = dark ? '#64748b' : '#8b95a3'; ctx.lineWidth = 1.4 / s; each(function (K) { ctx.stroke(K.rail); }); }
    // 보행·자전거 길(가늘게 · 점선)
    ['f', 'c'].forEach(function (c) { var st = RSTY[c]; if (s < st[2]) return; ctx.strokeStyle = st[mode][0]; ctx.lineWidth = Math.max(st[1] / s, st[0]); ctx.setLineDash([3 / s, 2.5 / s]); eachR(c, function (R) { ctx.stroke(R.n); ctx.stroke(R.b); }); ctx.setLineDash([]); });
    // 지하차도·터널: 옅은 점선 한 겹
    RORD.forEach(function (c) { var st = RSTY[c]; if (s < st[2]) return; ctx.globalAlpha = 0.55; ctx.setLineDash([5 / s, 4 / s]); ctx.strokeStyle = st[mode][1]; ctx.lineWidth = Math.max(st[1] / s, st[0] * 0.8); eachR(c, function (R) { ctx.stroke(R.t); }); ctx.setLineDash([]); ctx.globalAlpha = 1; });
    // 테두리 → 채움(낮은 종류부터 — 큰길이 위로)
    RORD.forEach(function (c) { var st = RSTY[c]; if (s < st[2]) return; var w = Math.max(st[1] / s, st[0]); ctx.strokeStyle = st[mode][1]; ctx.lineWidth = w + Math.max(1.4 / s, w * 0.18); eachR(c, function (R) { ctx.stroke(R.n); }); });
    RORD.forEach(function (c) { var st = RSTY[c]; if (s < st[2]) return; var w = Math.max(st[1] / s, st[0]); ctx.strokeStyle = dark ? '#0b1220' : '#5b6472'; ctx.lineWidth = w + Math.max(2.4 / s, w * 0.3); if (s > 0.15) eachR(c, function (R) { ctx.stroke(R.b); }); ctx.strokeStyle = st[mode][0]; ctx.lineWidth = w; eachR(c, function (R) { ctx.stroke(R.n); }); });
    screenT();
  }
  function drawBaseLabels(dark) {
    if (!OSM) return; var boxes = [], seen = {}, W = cv.clientWidth, H = cv.clientHeight, s = view.s, zin = s >= TILE_S && PACKS.some(function (K) { return !K.ov; });
    function free(x, y, w, h) { for (var i = 0; i < boxes.length; i++) { var b = boxes[i]; if (x < b[0] + b[2] && x + w > b[0] && y < b[1] + b[3] && y + h > b[1]) return false; } boxes.push([x, y, w, h]); return true; }
    WLAB.forEach(function (L) { if (zin && L.ov) return; if (s < 0.012 && !(L.k === 'w' && L.big)) return; if ((L.k === 'g' && s < 0.12) || (L.k === 'ww' && s < 0.08)) return; var q = S(L.p); if (q[0] < -50 || q[0] > W + 50 || q[1] < -20 || q[1] > H + 20) return; if (seen['w' + L.name] && L.k !== 'w') return;
      ctx.font = (L.k === 'g' ? '600 ' : 'italic 700 ') + (L.k === 'w' ? 15 : 12) + 'px system-ui, sans-serif'; var tw = ctx.measureText(L.name).width; if (!free(q[0] - tw / 2, q[1] - 9, tw, 18)) return; seen['w' + L.name] = 1;
      ctx.save(); ctx.translate(q[0], q[1]); if (L.ang) { var a = L.ang; if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI; ctx.rotate(a); } ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(15,22,36,.8)' : 'rgba(255,255,255,.85)'; ctx.strokeText(L.name, 0, 0); ctx.fillStyle = L.k === 'g' ? (dark ? '#86efac' : '#166534') : (dark ? '#7dd3fc' : '#1d5f99'); ctx.fillText(L.name, 0, 0); ctx.restore(); });
    JLAB.forEach(function (L) { if (!on.road || s < (L.major ? 0.12 : 0.2)) return; if (on.jcnm && itsNear(L.p)) return; var q = S(L.p); if (q[0] < -40 || q[0] > W + 40 || q[1] < -20 || q[1] > H + 20) return;
      ctx.font = '700 11px system-ui, sans-serif'; var tw = ctx.measureText(L.name).width; if (!free(q[0] - tw / 2 - 4, q[1] - 19, tw + 8, 15)) return; seen['j' + L.name.replace(/\s/g, '')] = 1;
      ctx.beginPath(); ctx.arc(q[0], q[1], 2.6, 0, Math.PI * 2); ctx.fillStyle = dark ? '#fde68a' : '#334155'; ctx.fill();
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(L.name, q[0], q[1] - 11); ctx.fillStyle = dark ? '#fef3c7' : (L.major ? '#7c2d12' : '#334155'); ctx.fillText(L.name, q[0], q[1] - 11); });
    if (on.jcnm) {   // v1.8.0 🏷 표준노드링크 교차로 이름 — IC·큰길이 먼저(먼저 자리를 잡는다)
      var nj = 0; for (var ji = 0; ji < JCN.length && nj < 140; ji++) { var J = JCN[ji], t = J.t, need = t[3] === 6 ? (t[4] <= 2 ? 0.02 : 0.05) : t[4] <= 2 ? 0.05 : t[4] <= 3 ? 0.07 : t[4] <= 4 ? 0.11 : t[4] <= 6 ? 0.16 : 0.22; if (s < need) continue;
        var q = S(J.p); if (q[0] < -40 || q[0] > W + 40 || q[1] < -20 || q[1] > H + 20) continue; if (seen['j' + t[0].replace(/\s/g, '')]) continue;
        ctx.font = '700 11px system-ui, sans-serif'; var tw = ctx.measureText(t[0]).width; if (!free(q[0] - tw / 2 - 4, q[1] - 19, tw + 8, 15)) continue; seen['j' + t[0].replace(/\s/g, '')] = 1; nj++;
        ctx.beginPath(); ctx.arc(q[0], q[1], 2.6, 0, Math.PI * 2); ctx.fillStyle = t[3] === 6 ? '#0f766e' : t[3] === 4 ? '#6b21a8' : (dark ? '#fde68a' : '#334155'); ctx.fill();
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(t[0], q[0], q[1] - 11);
        ctx.fillStyle = dark ? '#fef3c7' : t[3] === 6 ? '#0f766e' : t[3] === 4 ? '#6b21a8' : t[4] <= 3 ? '#7c2d12' : '#334155'; ctx.fillText(t[0], q[0], q[1] - 11);
        hit.push({ x: q[0], y: q[1] - 6, r: 10, it: { kind: 'jcnm', t: t } }); }
      var nr = 0; for (var ri = 0; ri < RDN.length && nr < 70; ri++) { var Rd = RDN[ri], rt = Rd.t, rneed = rt[4] <= 2 ? 0.02 : rt[4] <= 3 ? 0.04 : rt[4] <= 4 ? 0.07 : rt[4] <= 6 ? 0.1 : 0.18; if (s < rneed) continue;
        var rq = S(Rd.p); if (rq[0] < -40 || rq[0] > W + 40 || rq[1] < -20 || rq[1] > H + 20) continue; var rk2 = rt[0], rl = seen[rk2]; if (rl && rl.some(function (o) { return Math.hypot(o[0] - rq[0], o[1] - rq[1]) < 220; })) continue;
        var rfs = rt[4] <= 3 ? 12 : 11; ctx.font = '700 ' + rfs + 'px system-ui, sans-serif'; var rtw = ctx.measureText(rk2).width, ra = Rd.a;
        var rhw = Math.abs(Math.cos(ra)) * rtw / 2 + 6, rhh = Math.abs(Math.sin(ra)) * rtw / 2 + 7; if (!free(rq[0] - rhw, rq[1] - rhh, rhw * 2, rhh * 2)) continue; (seen[rk2] = seen[rk2] || []).push(rq); nr++;
        ctx.save(); ctx.translate(rq[0], rq[1]); ctx.rotate(ra); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3.2; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(rk2, 0, 0);
        ctx.fillStyle = dark ? '#bfdbfe' : '#1e3a8a'; ctx.fillText(rk2, 0, 0); ctx.restore(); }
    }
    var lim = { m: 0.06, p: 0.08, s: 0.14, t: 0.22, r: 0.55 }, n = 0;
    for (var i = 0; on.road && i < OSMLAB.length && n < 90; i++) {
      var L = OSMLAB[i]; if (zin && L.ov) continue; if (s < lim[L.c]) continue; if (L.L * s < 50) continue;
      var q = S(L.p); if (q[0] < -40 || q[0] > W + 40 || q[1] < -20 || q[1] > H + 20) continue;
      var key = L.name, last = seen[key]; if (last && last.some(function (o) { return Math.hypot(o[0] - q[0], o[1] - q[1]) < 260; })) continue;
      var fs = L.c === 'r' ? 10.5 : L.c === 't' ? 11 : 12; ctx.font = '700 ' + fs + 'px system-ui, sans-serif'; var tw = ctx.measureText(L.name).width; if (tw + 12 > L.L * s) continue;
      var a = L.ang; if (a > Math.PI / 2) a -= Math.PI; if (a < -Math.PI / 2) a += Math.PI;
      var hw = Math.abs(Math.cos(a)) * tw / 2 + 6, hh = Math.abs(Math.sin(a)) * tw / 2 + 7; if (!free(q[0] - hw, q[1] - hh, hw * 2, hh * 2)) continue;
      (seen[key] = seen[key] || []).push(q); n++;
      ctx.save(); ctx.translate(q[0], q[1]); ctx.rotate(a); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineWidth = 3.2; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.95)'; ctx.strokeText(L.name, 0, 0);
      ctx.fillStyle = dark ? '#e2e8f0' : (L.c === 'r' ? '#475569' : '#1f2937'); ctx.fillText(L.name, 0, 0); ctx.restore();
    }
  }

  // ---------- 흐름(v0.10.76): 버스·지하철 시간대 승차/하차 · 카드 매출 · 실시간 인파·카드·도로 소통 ----------
  //  소유자 「실시간 유동인구와 카드사용상황 · 버스정류장 승하차 인구 등 파악해서 넣고」. 지도는 통신 0 — 실시간 도시데이터는 **받은 시각의 한 장**이고,
  //  받은 뒤 12시간은 서울시 예측값을 보인다. 그 밖의 시각은 「받은 때」라고 적는다(지난 값을 지금처럼 보이지 않는다).
  var FLOW = { bus: {}, sub: {}, sales: {} }, LIVEP = [], LINKS = [];
  var LVC = { '여유': '#22c55e', '보통': '#eab308', '약간 붐빔': '#f97316', '붐빔': '#dc2626', '한산한': '#22c55e', '분주한': '#f97316', '바쁜': '#dc2626' };
  var IDXC = { '원활': '#16a34a', '서행': '#f59e0b', '정체': '#dc2626' };
  function flowPrep() {
    var F = D.flow; if (F) { FLOW.bus = (F.bus && F.bus.items) || {}; FLOW.sub = (F.subway && F.subway.items) || {}; FLOW.sales = (F.sales && F.sales.items) || {}; }
    livePrep();
  }
  function livePrep() {   // v0.10.95 실시간 도시데이터는 서울 121장소(약 1MB) — 첫 그림 뒤에 읽는다
    var L = D.livep; if (!L) return; var seen = {}; LINKS = [];
    LIVEP = (L.places || []).map(function (o) { var rings = (o.rings || []).map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); var r0 = rings[0] || [[0, 0]], sx = 0, sy = 0; r0.forEach(function (q) { sx += q[0]; sy += q[1]; });
      ((o.road && o.road.links) || []).forEach(function (k) { if (!k[3] || k[3].length < 2) return; var key = k[3][0].join() + '|' + k[3][k[3].length - 1].join(); if (seen[key]) return; seen[key] = 1; LINKS.push({ name: k[0], idx: k[1], spd: k[2], pts: k[3].map(function (q) { return P(q[0], q[1]); }), t: o.road.time, place: o.name }); });
      return { o: o, rings: rings, c: [sx / r0.length, sy / r0.length] }; });
  }
  function pad2(n) { return ('0' + n).slice(-2); }
  function crowdAt(Lp) {   // 고른 날짜·시각에 보일 값 — 받은 시각이면 그 값, 12시간 안이면 서울시 예측, 아니면 받은 때 값(옛것이라 적는다)
    var p = Lp.o.pop; if (!p) return null; var tgt = pickDate() + ' ' + pad2(nowH()) + ':00', got = (p.time || '').slice(0, 13) + ':00';
    if (tgt === got) return { kind: 'now', lvl: p.lvl, min: p.min, max: p.max, t: p.time };
    var f = (p.fcst || []).filter(function (x) { return x[0] === tgt; })[0];
    if (f) return { kind: 'fcst', lvl: f[1], min: f[2], max: f[3], t: f[0] };
    return { kind: 'old', lvl: p.lvl, min: p.min, max: p.max, t: p.time };
  }
  function man(n) { return n >= 10000 ? (n / 10000).toFixed(n >= 100000 ? 0 : 1) + '만' : Math.round(n).toLocaleString(); }
  function won(x) { return x >= 10000 ? (x >= 100000 ? Math.round(x / 10000).toLocaleString() : (x / 10000).toFixed(1)) + '억원' : Math.round(x).toLocaleString() + '만원'; }
  var TBH = [6, 5, 3, 3, 4, 3];
  function bandOf(h) { return h < 6 ? 0 : h < 11 ? 1 : h < 14 ? 2 : h < 17 ? 3 : h < 21 ? 4 : 5; }
  function salesOf(d) { return d.rg || d.pre ? d.sales || null : FLOW.sales[d.name] || null; }
  function salesNow(x) {
    var d = typeof x === 'string' ? { name: x } : x, s0 = salesOf(d); if (!s0) return null; var b = bandOf(nowH());
    if (SMX[b] == null) { var mx = 0; allDong().forEach(function (q) { var v = salesOf(q); if (v) mx = Math.max(mx, v.tb[b] / TBH[b]); }); SMX[b] = mx; }   // 서울 전체(받은 구까지) 한 눈금
    var perH = s0.tb[b] / TBH[b] / 30.4; return { perH: perH, t: Math.min(1, s0.tb[b] / TBH[b] / (SMX[b] || 1)), b: b };
  }
  function subTrend(nm) {   // 10년 추이(해마다 6월 · 하루 평균) — v0.10.77
    var T = D.trend && D.trend.subway && D.trend.subway.items[nm]; if (!T) return ''; var ys = Object.keys(T).sort(), hh = nowH();
    var tot = ys.map(function (y) { return T[y][0].reduce(function (a, b) { return a + b; }, 0) + T[y][1].reduce(function (a, b) { return a + b; }, 0); }), atH = ys.map(function (y) { return T[y][1][hh]; });
    var a = tot[0], b = tot[tot.length - 1];
    return row(ys[0] + '→' + ys[ys.length - 1], '하루 승하차 ' + man(a) + ' → ' + man(b) + ' <em>(' + (b >= a ? '+' : '') + Math.round((b - a) / (a || 1) * 100) + '% · 6월 기준)</em>') +
      '<div class="cap">해마다 하루 승하차 인원(명 · ' + ys[0] + '~' + ys[ys.length - 1] + ' · 그해 6월 하루 평균)</div>' + bar(tot, '#0284c7', ys.map(function (y) { return yLab(+y, 1)[0]; })) + '<div class="cap">해마다 ' + hh + '시 하차 인원(명/시 · 그해 6월 하루 평균)</div>' + bar(atH, '#ea580c', ys.map(function (y) { return yLab(+y, 1)[0]; }));
  }
  function salesTrend(x) {
    var d = typeof x === 'string' ? { name: x } : x, T, Q, tbl = d.rg ? d.rg.tb : D.flow.sales.tb;
    if (d.rg) { if (!d.x || !d.x.tr) return ''; T = {}; Q = d.rg.quarters; Q.forEach(function (q, i) { if (d.x.tr[i]) T[q] = d.x.tr[i]; }); }
    else { T = D.trend && D.trend.sales && D.trend.sales.items[d.name]; if (!T) return ''; Q = D.trend.sales.quarters; }
    var qs = Q.filter(function (q) { return T[q]; }); if (qs.length < 2) return ''; var b = bandOf(nowH());
    var lab = function (q) { return q.slice(2, 4) + '.' + q[4] + 'Q'; };
    return '<div class="cap">분기별 카드 매출(원 · 한 달 기준 · ' + lab(qs[0]) + '~' + lab(qs[qs.length - 1]) + ')</div>' + bar(qs.map(function (q) { return T[q][0]; }), '#6d28d9', qLab(qs), 'w') +
      '<div class="cap">분기별 주점·노래방류 카드 매출(원 · 한 달 기준)</div>' + bar(qs.map(function (q) { return T[q][7]; }), '#b45309', qLab(qs), 'w') + '<div class="cap">분기별 ' + esc(tbl[b]) + '시 카드 매출(원 · 한 달 기준 · 지금 시간대)</div>' + bar(qs.map(function (q) { return T[q][1 + b]; }), '#a78bfa', qLab(qs), 'w');
  }
  function salesRows(dd) {
    var d = typeof dd === 'string' ? { name: dd } : dd, x = salesOf(d); if (!x) return ''; var S5 = d.rg || d.pre ? { tb: (d.rg || d.pre).tb, source: (d.rg || d.pre).source['매출'] } : D.flow.sales, b = bandOf(nowH()), now = salesNow(d);
    var top = x.top.slice().sort(function (p, q) { return q[2 + b] - p[2 + b]; }).filter(function (t) { return t[2 + b] > 0; }).slice(0, 4);
    return row('카드 매출(추정)', '한 달 약 ' + won(x.amt) + ' · 결제 ' + man(x.cnt) + '건') + row('지금 시간대', esc(S5.tb[b]) + ' — 시간당 약 ' + won(now.perH) + ' <em>(하루 평균)</em>') +
      (top.length ? row('지금 많은 업종', top.map(function (t) { return esc(t[0]); }).join(' · ')) : '') +
      '<div class="cap">시간대별 시간당 카드 매출(원 · 하루 평균 · 0~6 … 21~24시)</div>' + bar(x.tb.map(function (v, i) { return v / TBH[i] / 30.4; }), '#7c3aed', LB_TB6, 'w') +
      '<div class="cap">요일별 카드 매출(원 · 한 달 동안 그 요일 합 · 월~일)</div>' + bar(x.dw, '#a78bfa', LB_DW, 'w') + (d.pre ? '' : salesTrend(d)) + '<div class="src">' + esc(S5.source) + (d.rg ? (d.x && d.x.tr ? ' · 추이: ' + esc(d.rg.source['추이']) : '') : d.pre ? '' : (D.trend ? ' · 추이: ' + esc(D.trend.sales.source) : '')) + '</div>';
  }
  function onoffC(a, b, al) { var c = a > b * 1.25 ? '37,99,235' : b > a * 1.25 ? '234,88,12' : '13,148,136'; return 'rgba(' + c + ',' + al + ')'; }
  function bar2(on, off) { var mx = 1, hh = nowH(), sm = [], sx = 1; for (var i = 0; i < 24; i++) { mx = Math.max(mx, on[i], off[i]); sm[i] = on[i] + off[i]; sx = Math.max(sx, sm[i]); }
    var sn = Math.min.apply(null, sm), lv = sm.map(function (v) { return hourLv(v, sx, sn); });
    return vxRow(sm, hh) + '<div class="bars h24 b2">' + on.map(function (v, i) { var op = i === hh ? 1 : lv[i] === 0 ? 0.35 : 0.7; return '<span class="hb' + (lv[i] === 2 ? ' b' : '') + (i === hh ? ' n' : '') + '"><i title="' + i + '시 승차" style="height:' + Math.round(v / mx * 100) + '%;background:#2563eb;opacity:' + op + '"></i><i title="' + i + '시 하차" style="height:' + Math.round(off[i] / mx * 100) + '%;background:#ea580c;opacity:' + op + '"></i></span>'; }).join('') + '</div>' + hourAxis(lv) +
      '<div class="hk"><i style="background:#2563eb"></i>승차 <i style="background:#ea580c"></i>하차 · <u></u>붐빔(승하차 합)' + (function () { var b = []; lv.forEach(function (l, i) { if (l === 2) b.push(i); }); var r = [], s0 = null; b.forEach(function (h, k) { if (s0 == null) s0 = h; if (b[k + 1] !== h + 1) { r.push(s0 === h ? s0 + '시' : s0 + '~' + h + '시'); s0 = null; } }); return r.length ? ' <b>' + r.join(' · ') + '</b>' : ''; })() + ' <i class="nw"></i>지금</div>'; }
  function onoffRows(f) {
    var hh = nowH(), on = f[0], off = f[1], so = on.reduce(function (a, b) { return a + b; }, 0), sf = off.reduce(function (a, b) { return a + b; }, 0);
    var pOn = on.indexOf(Math.max.apply(null, on)), pOff = off.indexOf(Math.max.apply(null, off)), a = on[hh], b = off[hh];
    return row(hh + '시', '승차 ' + a.toLocaleString() + ' · 하차 ' + b.toLocaleString() + '명 <em>(' + (a > b * 1.25 ? '떠나는 사람이 많다' : b > a * 1.25 ? '모여드는 사람이 많다' : '오가는 수가 비슷') + ')</em>') +
      row('하루', '승차 ' + so.toLocaleString() + ' · 하차 ' + sf.toLocaleString() + '명') + row('가장 붐빌 때', '타는 때 ' + pOn + '시 · 내리는 때 ' + pOff + '시') +
      '<div class="cap">시간대별 승차(파랑) · 하차(주황) 인원(명/시 · 하루 평균) — 아래 숫자 = 시각 · 빨간 밑줄 = 붐빔 · 검은 테 = 고른 시각</div>' + bar2(on, off);
  }
  function drawFlow(dark) {
    if (on.jct && JCT.length) { var ks = view.s, W1 = cv.clientWidth, H1 = cv.clientHeight; JCT.forEach(function (o) { if (o.t < (ks < 0.06 ? 60 : ks < 0.15 ? 20 : 1)) return; var sp = S(o.p); if (sp[0] < -30 || sp[1] < -30 || sp[0] > W1 + 30 || sp[1] > H1 + 30) return;
      dot(o.p, 3 + Math.min(15, Math.sqrt(o.t) * 0.7), o.r[4] ? 'rgba(185,28,28,.78)' : 'rgba(234,88,12,.72)', '#fff', { kind: 'jct', o: o });
      if (ks >= 0.2 && o.t >= 10) label([o.p[0], o.p[1] - 14 / ks], o.t + '건', 10.5, '#7f1d1d', 'rgba(255,255,255,.75)'); }); }
    if (on.hot10 && D.hot10) D.hot10.spots.forEach(function (g) { var cnt = {}; g.rec.forEach(function (r) { cnt[r[0]] = (cnt[r[0]] || 0) + 1; }); var k = Object.keys(cnt).sort(function (a, b) { return cnt[b] - cnt[a]; })[0], q = P(g.lo, g.la);
      dot(q, 5 + Math.min(8, g.rec.length * 1.3), H10C[k] || '#475569', '#fff', { kind: 'hot10', g: g });
      if (view.s > 0.16) { var ys = g.rec.map(function (r) { return r[1]; }); label([q[0], q[1] + 18 / view.s], g.rec.length + '회 · ' + Math.min.apply(null, ys) + (ys.length > 1 ? '~' + Math.max.apply(null, ys) : ''), 10, dark ? '#e2e8f0' : '#1f2937', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.85)'); } });
    if (on.spd && LINKS.length && view.s > 0.05) { LINKS.forEach(function (k) { path(k.pts); ctx.lineCap = 'round'; ctx.lineWidth = Math.max(3, 7 * view.s); ctx.strokeStyle = IDXC[k.idx] || '#64748b'; ctx.globalAlpha = 0.9; ctx.stroke(); ctx.globalAlpha = 1;
      var m = k.pts[Math.floor(k.pts.length / 2)], s = S(m); hit.push({ x: s[0], y: s[1], r: 7, it: { kind: 'link', k: k } }); }); }
    if (on.crowd && LIVEP.length) LIVEP.forEach(function (Lp) {
      var cw = crowdAt(Lp); if (!cw) return; var col = LVC[cw.lvl] || '#64748b';
      Lp.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.save(); ctx.globalAlpha = 0.28; ctx.lineWidth = 1; ctx.setLineDash(cw.kind === 'old' ? [5, 4] : []); ctx.strokeStyle = cw.kind === 'old' ? (dark ? '#94a3b8' : '#64748b') : col; ctx.stroke(); ctx.restore(); });   // v2.32.0 소유자 「인파는 테두리 아주 옅게 · 글씨로만」
      var s = S(Lp.c); hit.push({ x: s[0], y: s[1], r: 14, it: { kind: 'crowd', L: Lp } });
      if (view.s > 0.07) { var t1 = Lp.o.name + ' · ' + (cw.lvl || '-'), t2 = (cw.min ? man(cw.min) + '~' + man(cw.max) + '명' : '') + (cw.kind === 'fcst' ? ' 예측' : cw.kind === 'old' ? ' (받은 때 ' + (cw.t || '').slice(11, 16) + ')' : ' 지금');
        halo(Lp.c, t1, 12.5, cw.kind === 'old' ? (dark ? '#cbd5e1' : '#475569') : col, dark); halo([Lp.c[0], Lp.c[1] + 16 / view.s], t2, 10.5, dark ? '#e2e8f0' : '#334155', dark); }
    });
  }
  var H10C = { '보행자': '#2563eb', '보행노인': '#7c3aed', '보행어린이': '#ca8a04', '자전거': '#16a34a', '이륜차': '#dc2626', '화물차': '#78350f', '결빙': '#0891b2', '지자체별(전체)': '#475569' };
  function flowCard(it) {
    if (it.kind === 'jct') { var o = it.o, r = o.r, J = o.m, a19 = 0; for (var i9 = 3; i9 < 10; i9++) a19 += r[3][i9];
      return '<h3>🚦 ' + esc(r[0]) + '</h3>' + row('사고 2016~2025', o.t.toLocaleString() + '건 <em>· 해마다 평균 ' + Math.round(o.t / 10) + '</em>') + row('2019~2025', a19.toLocaleString() + '건') +
        row('사람', '사망 ' + r[4] + '명 · 중상 ' + r[5] + '명 · 보행자 피해 ' + r[6] + '건') + row('밤(20~6시)', Math.round(r[7] / Math.max(1, o.t) * 100) + '%') +
        (r[8].length ? row('주 법규위반', r[8].map(function (v) { return esc(v[0]) + ' ' + v[1]; }).join(' · ') + ' <em>(칸마다 주 위반의 합 — 근사)</em>') : '') +
        '<div class="cap">해마다 교통사고 건수(건 · 2016~2025 · 교차로 가운데 70m 안 100m 칸)</div>' + bar(r[3], '#ea580c', LB_Y16) + '<p class="desc">' + esc(J.note) + '</p>' + src(J.source); }
    if (it.kind === 'hot10') { var g = it.g; return '<h3>🗂 ' + esc(g.n) + '</h3>' + row('뽑힌 횟수', g.rec.length + '회(' + g.rec.map(function (r) { return r[1]; }).filter(function (v, i, a) { return a.indexOf(v) === i; }).join(' · ') + ')') +
      g.rec.map(function (r) { return row(r[1] + ' ' + r[0], r[2] + '건 · 사상 ' + r[3] + ' (사망 ' + r[4] + ' · 중상 ' + r[5] + ' · 경상 ' + r[6] + ')'); }).join('') + '<p class="desc">' + esc((g.m || D.hot10).note) + '</p>' + src((g.m || D.hot10).source); }
    var h = '', L = D.livep || {};
    if (it.kind === 'osmroad') { var r = it.r; return '<h3>🛣 ' + esc(r.name) + '</h3>' + row('종류', esc(RCLS[r.c] || r.c)) + row('구간', r.n + '개(OSM 길 조각)') + src(D.osm.source); }
    if (it.kind === 'link') { var k = it.k; return '<h3>🚥 ' + esc(k.name || '도로') + '</h3>' + row('소통', '<b style="color:' + (IDXC[k.idx] || '#64748b') + '">' + esc(k.idx) + '</b> · ' + k.spd + 'km/h') + row('받은 때', esc(k.t || '-') + ' <em>(지금 소통이 아니다)</em>') + row('장소', esc(k.place)) + src(L.source || ''); }
    var o = it.L.o, cw = crowdAt(it.L), p = o.pop || {}, c = o.card;
    h = '<h3>📡 ' + esc(o.name) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(o.cat) + '</small></h3>';
    if (cw) h += row(cw.kind === 'now' ? '지금' : cw.kind === 'fcst' ? '예측(' + esc(cw.t.slice(11, 16)) + ')' : '받은 때', '<b style="color:' + (LVC[cw.lvl] || '#64748b') + '">' + esc(cw.lvl) + '</b> · ' + (cw.min ? man(cw.min) + '~' + man(cw.max) + '명' : '-') + (cw.kind === 'old' ? ' <em>(' + esc(cw.t) + ' 값 — 지금이 아니다)</em>' : cw.kind === 'fcst' ? ' <em>(서울시 예측)</em>' : ''));
    if (p.msg) h += '<p class="desc">' + esc(p.msg) + '</p>';
    if (p.age) h += row('남·여', Math.round(p.male) + ' : ' + Math.round(100 - p.male) + ' · 상주 ' + Math.round(p.resnt) + '%') + '<div class="cap">지금 있는 사람의 연령대 비율(% · 10세 미만 … 70대 이상 · ' + esc(p.time) + ' 기준)</div>' + bar(p.age, '#0ea5e9', ageLab(p.age.length));
    if (p.fcst && p.fcst.length) h += '<div class="cap">앞으로 12시간 인구 예측(명 · 예측 범위의 상한 · ' + esc(p.fcst[0][0].slice(11, 16)) + '부터)</div>' + bar(p.fcst.map(function (f) { return f[3] || 0; }), '#64748b', p.fcst.map(function (f) { return String(f[0]).slice(11, 13) + '시'; }));
    if (c) { h += row('실시간 카드', '<b style="color:' + (LVC[c.lvl] || '#64748b') + '">' + esc(c.lvl) + '</b> · 결제 ' + c.cnt + '건 · ' + won(c.amin / 1e4) + '~' + won(c.amax / 1e4) + ' <em>(' + esc(String(c.time || '').replace(/^(\d{4})(\d\d)(\d\d) (\d\d)(\d\d)$/, '$2-$3 $4:$5')) + ' 표본)</em>');
      if (c.rsb && c.rsb.length) h += row('업종', c.rsb.map(function (x) { return esc(x[1]) + ' ' + esc(x[2]) + ' ' + (x[3] || 0) + '건'; }).join(' · '));
      if (c.age) h += '<div class="cap">실시간 카드 결제 연령대 비율(% · 최근 10분 · 10대 … 60대 이상)</div>' + bar(c.age, '#7c3aed', c.age.length === 6 ? LB_AGE6 : null); }
    if (o.bus) h += row('버스 오늘 누적', '승차 ' + man(o.bus.acc[0]) + '~' + man(o.bus.acc[1]) + ' · 하차 ' + man(o.bus.acc[2]) + '~' + man(o.bus.acc[3]) + ' <em>(정류장 ' + o.bus.n + ')</em>');
    if (o.sub) h += row('지하철 오늘 누적', '승차 ' + man(o.sub.acc[0]) + '~' + man(o.sub.acc[1]) + ' · 하차 ' + man(o.sub.acc[2]) + '~' + man(o.sub.acc[3]) + ' <em>(역 ' + o.sub.n + ')</em>');
    if (o.road && o.road.idx) h += row('둘레 도로', '<b style="color:' + (IDXC[o.road.idx] || '#64748b') + '">' + esc(o.road.idx) + '</b> · 평균 ' + o.road.spd + 'km/h · 링크 ' + ((o.road.links || []).length) + '개');
    if ((o.acdnt || []).length) h += row('사고·통제', o.acdnt.map(function (a) { return esc(a[1] + ' ' + (a[3] || '')); }).join(' · '));
    if ((o.event || []).length) h += row('행사', o.event.map(function (e) { return esc(e[0]); }).join(' · '));
    if (o.prk) h += row('주차장', o.prk + '곳(장소 안 등록)');
    if (o.wx) h += row('날씨(받은 때)', (o.wx.t != null ? o.wx.t + '℃ · ' : '') + esc(o.wx.pcp || '') + ' · 미세먼지 ' + esc(o.wx.pm10 || '-'));
    return h + '<p class="desc">' + esc(L.note || '') + '</p>' + src((L.source || '') + ' · 받은 시각 ' + (L.baked || ''));
  }

  // ---------- 🕐 시각 막대 · 🧭 근무별 한 번에 · 지금 요약(v0.10.76 · 소유자 「더 효율적이고 구체적으로」) ----------
  function setHour(h) { HOUR = h == null ? null : (h + 24) % 24; paintTime(); draw(); summary(); if (sel && $('m2dCard').classList.contains('on')) show(sel.it); }
  function paintTime() {
    var h = nowH(), dt = new Date(pickDate() + 'T00:00'), we = dt.getDay() === 0 || dt.getDay() === 6, r = $('m2dHour'); if (!r) return;
    r.value = h; $('m2dHourT').innerHTML = h + '시<span class="wk"> · ' + (we ? '주말' : '평일') + '</span>' + (HOUR == null ? '' : ' ✎'); $('m2dNowBtn').classList.toggle('on', HOUR == null);
    var db = $('m2dDateB'); if (db) { db.textContent = '📅 ' + (dt.getMonth() + 1) + '/' + dt.getDate() + '(' + '일월화수목금토'[dt.getDay()] + ')'; db.classList.toggle('we', we); }
    var tb = $('m2dTimeB'); if (tb) { tb.textContent = HOUR == null ? '🕒 지금 ' + h + '시' : '🕒 ' + h + '시 보기'; tb.classList.toggle('set', HOUR != null); }
  }
  if ($('m2dHour')) {
    $('m2dHour').addEventListener('input', function () { setHour(+this.value); });
    $('m2dHm').onclick = function () { setHour(nowH() - 1); }; $('m2dHp').onclick = function () { setHour(nowH() + 1); };
    $('m2dNowBtn').onclick = function () { setHour(null); };
  }
  var PRESETS = [
    ['basic', '🔎 지역 기본 파악', ['jgg', 'live250', 'sales', 'bus', 'subr', 'home', 'acc10', 'jurk']],
    ['traffic', '🚦 교통근무', ['acc', 'cam', 'sig', 'spd', 'vol', 'sz', 'risk', 'bus']],
    ['night', '🌙 야간순찰', ['trd', 'bar', 'play', 'inn', 'er', 'pol', 'drunk', 'srcctv', 'srbell', 'srsvc']],
    ['shop', '🏪 상권분석', ['trd', 'szone', 'rent', 'bus', 'subr', 'live']],
    ['acc10', '🚗 사고 10년', ['acc10', 'fatal10', 'hot10', 'jct', 'cam', 'sz']],
    ['crowd', '🎪 행사·인파', ['evt', 'crowd', 'live', 'subr', 'bus', 'spot']],
    ['jur', '🚓 관할·관서', ['jur', 'pol', 'tgis', 'fire', 'er']],
    ['kids', '🧒 어린이', ['sz', 'szh', 'school', 'kids', 'pg']],
    ['gov', '🏛 관공서', ['govr']],
    ['acc', '🚑 사고·응급', ['acc', 'fatal', 'hot10', 'er', 'ger', 'aed', 'pol', 'fire', 'cam', 'tow']],
    ['estate', '🏢 부동산·상권', ['home', 'rtc', 'live250', 'rent', 'trd', 'szone', 'sub']]
  ];
  var KEEP = ['dong', 'road', 'base', 'bld', 'sub'];
  function preset(id) {
    var P3 = PRESETS.filter(function (x) { return x[0] === id; })[0]; if (!P3) return;
    LAYERS.forEach(function (l) { if (KEEP.indexOf(l[0]) < 0) on[l[0]] = false; }); on.dong = true; on.road = true; on.base = true;
    P3[2].forEach(function (k) { if (k in on) on[k] = true; }); unitKeep(); saveOn(); paintLayers(); paintPre(); sel = null; show(null); draw(); summary();
  }
  function paintPre() {
    var el = $('m2dPre'); if (!el) return; var si = seasonInfo(); PRESETS = PRESETS.filter(function (x) { return x[0] !== 'season'; }); PRESETS.unshift(['season', si.icon + ' 지금 계절 · ' + si.short, si.keys]);
    el.innerHTML = '<button data-x="none" class="ctl">모두 끄기</button><button data-x="reset" class="ctl">처음대로</button><button data-x="biz" class="ctl biz">🏪 창업 자리 찾기</button><button data-x="rad" class="ctl biz">📐 반경 분석</button>' + PRESETS.map(function (x) { var act = LAYERS.every(function (l) { return KEEP.indexOf(l[0]) >= 0 || on[l[0]] === (x[2].indexOf(l[0]) >= 0); }); return '<button data-p="' + x[0] + '" class="' + (act ? 'on' : '') + '">' + x[1] + '</button>'; }).join('') +
      '';
    var pc = $('m2dPreC'); if (pc) pc.innerHTML = '<details id="m2dPreCD" class="prec"' + (PRECO ? ' open' : '') + '><summary>📋 묶음마다 켜는 레이어 — 어떻게 짜였나</summary>' + PRESETS.map(function (x) { return '<div><button data-p="' + x[0] + '" class="pk">' + x[1] + '</button> → ' + x[2].filter(hasL).map(function (k) { return esc(lname(k)); }).join(' · ') + (PRENOTE[x[0]] ? '<br><small>' + PRENOTE[x[0]] + '</small>' : '') + '</div>'; }).join('') + '<p class="lhn">묶음을 누르면 행정동·도로·바탕만 남기고 나머지는 끈 뒤 이 레이어들을 켠다 · 「처음대로」 = 레이어마다 처음 값 · 「모두 끄기」 = 바탕만</p></details>';
    preFit();
  }
  // v0.10.92 소유자 「모두 끄기·처음대로는 왼쪽 맨 앞 · 화면을 넘으면 두 줄로」 — 한 줄에 다 들면 한 줄, 넘치면 두 줄(그래도 넘치면 옆으로 민다)
  function preFit() { var el = $('m2dPre'); if (!el) return; el.classList.remove('two'); if (el.scrollWidth > el.clientWidth + 2) el.classList.add('two'); }
  window.addEventListener('resize', preFit);
  // v0.10.82 모두 끄기(행정동·도로·바탕만 남김) · 처음대로(층마다 기본값) — 근무별 줄과 「☰ 모든 층」 판이 같이 쓴다
  function layersNone() { LAYERS.forEach(function (l) { on[l[0]] = false; }); on.dong = true; on.road = true; on.base = true; unitKeep(); saveOn(); paintLayers(); paintPre(); sel = null; show(null); draw(); summary(); }
  function layersReset() { LAYERS.forEach(function (l) { on[l[0]] = l[2]; }); unitKeep(); saveOn(); paintLayers(); paintPre(); draw(); summary(); }
  if ($('m2dPre')) { $('m2dPre').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var x = b.getAttribute('data-x'); if (x === 'biz') bizOpen(); else if (x === 'rad') radOpen(null); else if (x === 'none') layersNone(); else if (x === 'reset') layersReset(); else preset(b.getAttribute('data-p')); }); }
  var SUMT = [];
  function summary() {
    var el = $('m2dSum'); if (!el || !DONG.length) return; var h = nowH(), out = [], it; SUMT = [];
    function go(txt, p, item) { SUMT.push({ p: p, it: item }); return '<button data-s="' + (SUMT.length - 1) + '">' + esc(txt) + '</button>'; }
    var best = null; DONG.forEach(function (d) { var lv = liveNow(d.name); if (lv && (!best || lv.n > best.n)) best = { d: d, n: lv.n }; });
    if (best) out.push('👥 생활인구 ' + go(best.d.name + ' ' + man(best.n), best.d.c, { kind: 'dong', d: best.d }));
    var bs = null; if (PUB) PUB.subr.forEach(function (q) { var f = FLOW.sub[q.name]; if (f && (!bs || f[1][h] > bs.v)) bs = { q: q, v: f[1][h] }; });
    if (bs && bs.v) out.push('🚇 하차 ' + go(bs.q.name + ' ' + bs.v.toLocaleString(), bs.q.p, { kind: 'pub', layer: 'subr', q: bs.q }));
    var bb = null; if (PUB) PUB.bus.forEach(function (q) { var f = FLOW.bus[q.o.id]; if (f && (!bb || f[1][h] > bb.v)) bb = { q: q, v: f[1][h] }; });
    if (bb && bb.v) out.push('🚌 하차 ' + go(bb.q.name + ' ' + bb.v.toLocaleString(), bb.q.p, { kind: 'pub', layer: 'bus', q: bb.q }));
    var sm = null; DONG.forEach(function (d) { var sn = salesNow(d.name); if (sn && (!sm || sn.perH > sm.v)) sm = { d: d, v: sn.perH }; });
    if (sm) out.push('💳 매출 ' + go(sm.d.name, sm.d.c, { kind: 'dong', d: sm.d }));
    if (LIVEP.length) { var cnt = { '붐빔': 0, '약간 붐빔': 0 }, kind = null, hot = null; LIVEP.forEach(function (L) { var cw = crowdAt(L); if (!cw) return; kind = kind || cw.kind; if (cnt[cw.lvl] != null) { cnt[cw.lvl]++; if (!hot || cw.lvl === '붐빔') hot = L; } });
      out.push('📡 ' + (kind === 'old' ? '실시간 인파(' + esc(String((D.livep || {}).baked || '').slice(5)) + ' 받음)' : '인파 ' + (kind === 'fcst' ? '예측' : '지금')) + ' 붐빔 ' + cnt['붐빔'] + ' · 약간 ' + cnt['약간 붐빔'] + (hot ? ' ' + go(hot.o.name, hot.c, { kind: 'crowd', L: hot }) : '')); }
    var si = seasonInfo(), sn = seasonCount(si); if (sn) out.unshift('<button data-sp="1">' + si.icon + ' ' + esc(si.name) + ' — ' + esc(sn) + '</button>');
    el.innerHTML = '<b>' + h + '시</b> ' + out.join(' · ');
  }
  if ($('m2dSum')) $('m2dSum').addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; if (b.getAttribute('data-sp')) { preset('season'); return; } var t = SUMT[+b.getAttribute('data-s')]; if (!t) return;
    var k = t.it.kind === 'pub' ? t.it.layer : t.it.kind === 'crowd' ? 'crowd' : null; if (k && !on[k]) { on[k] = true; saveOn(); paintLayers(); paintPre(); }
    view.cx = t.p[0]; view.cy = t.p[1]; view.s = Math.max(view.s, 0.3); draw(); var s = S(t.p); sel = { x: s[0], y: s[1], r: 8, it: t.it }; show(t.it); draw(); });
  paintPre();
  // ---------- 🏪 상권분석(v0.10.78 · 소유자 「상권분석과 똑같이 · 어떤 업종에서 어떤 연령대가 카드를 어떻게 쓰는지 — 음주운전 예방 · 지역을 세세하게」) ----------
  //  서울시 상권분석서비스: 상권(골목·발달·전통시장) 74곳 영역 + 업종별 추정매출(시간대·연령·성별·요일 — 금액·건수) · 길단위 유동인구 · 직장·상주인구 · 점포 · 집객시설 · 상권변화지표.
  //  ind 칸: 0 업종 · 1 매출(만원) · 2 건수 · 3~8 시간대 매출 · 9~14 연령 매출 · 15 남 · 16 여 · 17~23 요일 · 24~29 시간대 건수 · 30~35 연령 건수
  var TRD = [], TRDM = 'sales', TRDI = '', TRDIL = [];   // TRDI = 고른 업종('' = 전부)
  var AGEL = ['10대', '20대', '30대', '40대', '50대', '60+'], TBL = ['0~6', '6~11', '11~14', '14~17', '17~21', '21~24'];
  var TRDMS = { sales: ['💳 그 시간대 매출', '#7c3aed'], amt: ['💰 한 달 매출', '#6d28d9'], atv: ['🧾 객단가(건당)', '#9333ea'], night: ['🌙 밤(21~6시) 매출 비중', '#1e3a8a'], young: ['🧑 20·30대 매출 비중', '#db2777'], bar: ['🍺 밤 주점·유흥 매출', '#b45309'],
    flp: ['🚶 그 시간대 유동인구', '#0284c7'], wrc: ['🏢 직장인구', '#0f766e'], job: ['🏢 직장/(직장+상주) 비율', '#0d9488'], stor: ['🏬 점포 수', '#475569'], dens: ['🏬 점포 밀도(곳/ha)', '#334155'], perstor: ['📈 점포당 매출', '#4d7c0f'], cls: ['📉 폐업 점포', '#dc2626'] };
  function isBar(n) { return /주점|유흥/.test(n); }
  function trdItem(t, m) { var rings = t.rings.map(function (r) { return r.map(function (q) { return P(q[0], q[1]); }); }); var r0 = rings[0], sx = 0, sy = 0; r0.forEach(function (q) { sx += q[0]; sy += q[1]; }); return { t: t, rings: rings, c: [sx / r0.length, sy / r0.length], m: m || null }; }
  function trdList() { var tot = {}; TRD.forEach(function (x) { (x.t.ind || []).forEach(function (i) { tot[i[0]] = (tot[i[0]] || 0) + i[1]; }); }); TRDIL = Object.keys(tot).sort(function (a, b) { return tot[b] - tot[a]; }); }
  function trdPrep() {
    var T = D.trdar; if (!T) return; var have = {}; TRD.forEach(function (x) { have[x.t.cd] = 1; });   // 서울 상권 파일이 먼저 왔으면 그쪽(1년 전 값 포함)을 둔다
    T.trdar.forEach(function (t) { if (!have[t.cd]) TRD.push(trdItem(t, null)); }); trdList();
  }
  function trdInd(t) { var ind = t.ind || []; return TRDI ? ind.filter(function (i) { return i[0] === TRDI; }) : ind; }
  function sumI(ind, k) { return ind.reduce(function (a, r) { return a + r[k]; }, 0); }
  function trdVal(t, m) {
    var b = bandOf(nowH()), ind = trdInd(t), stor = (t.stor || []).filter(function (s) { return !TRDI || s[0] === TRDI; });
    if (m === 'amt') return sumI(ind, 1);
    if (m === 'atv') { var co = sumI(ind, 2); return co ? sumI(ind, 1) * 1e4 / co : 0; }
    if (m === 'night') { var a0 = sumI(ind, 1); return a0 ? (sumI(ind, 3) + sumI(ind, 8)) / a0 * 100 : 0; }
    if (m === 'young') { var ag = sumI(ind, 9) + sumI(ind, 10) + sumI(ind, 11) + sumI(ind, 12) + sumI(ind, 13) + sumI(ind, 14); return ag ? (sumI(ind, 10) + sumI(ind, 11)) / ag * 100 : 0; }
    if (m === 'job') return t.wrc && t.rep && (t.wrc[0] + t.rep[0]) ? t.wrc[0] / (t.wrc[0] + t.rep[0]) * 100 : 0;
    if (m === 'dens') return t.area ? stor.reduce(function (a, s) { return a + s[1]; }, 0) / (t.area / 1e4) : 0;
    if (m === 'perstor') { var n = stor.reduce(function (a, s) { return a + s[1]; }, 0); return n ? sumI(ind, 1) / n : 0; }
    if (m === 'stor') return stor.reduce(function (a, s) { return a + s[1]; }, 0);
    if (m === 'cls') return stor.reduce(function (a, s) { return a + s[4]; }, 0);
    if (m === 'sales') return ind.reduce(function (a, i) { return a + i[3 + b]; }, 0) / TBH[b] / 30.4;
    if (m === 'bar') return ind.filter(function (i) { return isBar(i[0]); }).reduce(function (a, i) { return a + i[3] + i[8]; }, 0);
    if (m === 'flp') return t.flp ? t.flp[9 + b] / TBH[b] / 91 : 0;
    if (m === 'wrc') return t.wrc ? t.wrc[0] : 0;
    return 0;
  }
  function trdFmt(v, m) { return m === 'sales' ? '시간당 ' + won(v) : m === 'bar' || m === 'amt' ? '한 달 ' + won(v) : m === 'perstor' ? '점포당 ' + won(v) : m === 'atv' ? Math.round(v).toLocaleString() + '원' : m === 'night' || m === 'young' || m === 'job' ? Math.round(v) + '%' : m === 'dens' ? v.toFixed(1) + '곳/ha' : m === 'flp' ? '시간당 약 ' + man(v) + '명' : m === 'wrc' ? man(v) + '명' : Math.round(v) + '곳'; }
  function trdMetricName() { return TRDMS[TRDM][0]; }
  function trdLegend() {
    if (!on.trd || (!TRD.length && !GGT.length)) return null; if (!TRD.length) return ['🏪 상권분석 — 경기', ggLegend()];
    var vs = TRD.map(function (x) { return trdVal(x.t, TRDM); }), mx = Math.max.apply(null, vs), mn = Math.min.apply(null, vs);
    return ['🏪 상권분석 — ' + (TRDI ? TRDI + ' · ' : '') + TRDMS[TRDM][0], '<div class="lg-btns"><button data-bizopen="1">🏪 이 업종 창업 자리 찾기</button></div><div class="lg-btns"><select data-trdi aria-label="업종"><option value="">업종 전부</option>' + TRDIL.map(function (n) { return '<option' + (n === TRDI ? ' selected' : '') + '>' + esc(n) + '</option>'; }).join('') + '</select></div><div class="lg-btns">' + Object.keys(TRDMS).map(function (k) { return '<button data-trdm="' + k + '" class="' + (k === TRDM ? 'on' : '') + '">' + TRDMS[k][0] + '</button>'; }).join('') + '</div>' +
      grad('rgba(255,255,255,.4)', TRDMS[TRDM][1], trdFmt(mn, TRDM), trdFmt(mx, TRDM)) + li('#64748b', '굵은 테 = 발달상권 · 가는 테 = 골목상권 · 점선 = 전통시장', 'line') + li('#ea580c', '주황 점선 = 골목상권의 배후지(누른 상권 · 서울)', 'line') + '<div class="lg-btns"><button data-hlall="1" class="' + (HLALL ? 'on' : '') + '">🏘 배후지 모두 보기</button></div><small class="lg-n">상권을 누르면 업종 × 연령 · 업종 × 시간대 표 · 골목상권은 본체 ↔ 배후지 비교</small>' + ggLegend()];
  }
  function hexA(c, a) { var n = parseInt(c.slice(1), 16); return 'rgba(' + (n >> 16) + ',' + ((n >> 8) & 255) + ',' + (n & 255) + ',' + a + ')'; }
  function drawTrd(dark) {
    if (!on.trd || !TRD.length) return; var vs = TRD.map(function (x) { return trdVal(x.t, TRDM); }), mx = Math.max.apply(null, vs) || 1, col = TRDMS[TRDM][1];
    TRD.forEach(function (x, k) { var t = vs[k] / mx;
      x.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = hexA(col, 0.08 + 0.62 * t); ctx.fill(); ctx.lineWidth = x.t.se === '발달상권' ? 2.4 : 1.2; ctx.setLineDash(x.t.se === '전통시장' ? [4, 3] : []); ctx.strokeStyle = col; ctx.stroke(); ctx.setLineDash([]); });
      var s = S(x.c); hit.push({ x: s[0], y: s[1], r: 12, it: { kind: 'trd', x: x } });
      if (view.s > 0.11) { label(x.c, x.t.name, 11, '#fff', hexA(col, 0.85)); if (view.s > 0.2) label([x.c[0], x.c[1] + 16 / view.s], trdFmt(vs[k], TRDM), 10, dark ? '#e2e8f0' : '#1f2937', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); }
    });
  }
  function pct(a, b) { return b ? Math.round(a / b * 100) : 0; }
  function indTable(ind, mode, n) {   // 업종 × (연령|시간대) — 칸 = 그 업종 안 비중(%) · 가장 큰 칸은 진하게
    var top = ind.slice().sort(function (a, b) { return b[1] - a[1]; }).slice(0, n || 8), cols = mode === 'age' ? AGEL : TBL, o = mode === 'age' ? 9 : 3, hh = bandOf(nowH());
    return '<table class="it"><tr><th>업종</th>' + cols.map(function (c, i) { return '<th' + (mode === 'tb' && i === hh ? ' class="now"' : '') + '>' + c + '</th>'; }).join('') + '</tr>' +
      top.map(function (r) { var tot = 0; for (var i = 0; i < 6; i++) tot += r[o + i]; var mxi = 0; for (i = 1; i < 6; i++) if (r[o + i] > r[o + mxi]) mxi = i;
        return '<tr' + (isBar(r[0]) ? ' class="bar"' : '') + '><td>' + esc(r[0]) + '</td>' + [0, 1, 2, 3, 4, 5].map(function (i) { var p = pct(r[o + i], tot); return '<td style="background:rgba(124,58,237,' + (p / 100 * 0.9).toFixed(2) + ')' + (i === mxi ? ';font-weight:800' : '') + '">' + p + '</td>'; }).join('') + '</tr>'; }).join('') + '</table>';
  }
  function barRows(ind, unit) {   // 🍺 주점·유흥 — 음주운전 예방에 쓰는 줄
    var bars = ind.filter(function (r) { return isBar(r[0]); }); if (!bars.length) return row('🍺 주점·유흥', '이 자료에 없음');
    var S2 = function (k) { return bars.reduce(function (a, r) { return a + r[k]; }, 0); }, amt = S2(1), night = S2(3) + S2(8), nCo = S2(24) + S2(29), all = ind.reduce(function (a, r) { return a + r[1]; }, 0);
    var ag = [0, 1, 2, 3, 4, 5].map(function (i) { return S2(9 + i); }), agt = ag.reduce(function (a, b) { return a + b; }, 0), ac = [0, 1, 2, 3, 4, 5].map(function (i) { return S2(30 + i); });
    var tbs = [0, 1, 2, 3, 4, 5].map(function (i) { return S2(24 + i); });
    return row('🍺 주점·유흥', esc(bars.map(function (r) { return r[0]; }).join('·')) + ' — 한 달 ' + won(amt) + ' (' + unit + ' 매출의 ' + pct(amt, all) + '%)') +
      row('밤 21~6시', '매출의 ' + pct(night, amt) + '% · 결제 하루 약 ' + Math.round(nCo / 30.4).toLocaleString() + '건') +
      row('누가', AGEL.map(function (a, i) { return a + ' ' + pct(ag[i], agt) + '%'; }).join(' · ') + ' <em>(20·30대 ' + pct(ag[1] + ag[2], agt) + '%)</em>') +
      '<div class="cap">주점·유흥 시간대별 카드 결제 건수(건 · 한 달 · 0~6 … 21~24시)</div>' + bar(tbs, '#b45309', LB_TB6) +
      '<div class="cap">주점·유흥 연령대별 카드 결제 건수(건 · 한 달 · 10대 … 60세 이상)</div>' + bar(ac, '#d97706', LB_AGE6) +
      '<p class="desc">음주 단속·순찰 참고 — 술자리 결제가 몰리는 시간·연령이다. 결제 = 카드 추정치(현금 제외)이고, 결제한 사람이 운전한다는 뜻은 아니다.</p>';
  }
  function trdCard(it) {
    var t = it.x.t, MT = it.x.m || D.trdar, h = '<h3>🏪 ' + esc(t.name) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(t.se) + '</small></h3>', ind = t.ind || [], Q = MT.quarter, b = bandOf(nowH());
    if (it.biz) h += bizWhy(it.biz);
    rentLoad();
    h += '<div class="lg-btns"><button data-radhere="' + (it.x.c[0] / KX + LON0).toFixed(5) + ',' + (LAT0 - it.x.c[1] / KY).toFixed(5) + '">📐 여기서 반경 분석</button></div>';
    h += row('자리', (t.guName ? esc(t.guName) + ' ' : '') + esc(t.dong) + ' · 넓이 ' + man(t.area) + '㎡') + (t.ix ? row('상권 변화', '<b>' + esc(t.ix[0]) + '</b> · 운영 평균 ' + t.ix[1] + '개월 · 폐업 평균 ' + t.ix[2] + '개월' + (t.ix[3] ? ' <em>(서울 평균 ' + t.ix[3] + ' · ' + t.ix[4] + ')</em>' : '')) : '');
    if (ind.length) { var amt = ind.reduce(function (a, r) { return a + r[1]; }, 0), co = ind.reduce(function (a, r) { return a + r[2]; }, 0), S3 = function (k) { return ind.reduce(function (a, r) { return a + r[k]; }, 0); };
      h += row('카드 매출(추정)', '한 달 ' + won(amt) + ' · 결제 ' + man(co) + '건 <em>(' + Q.slice(0, 4) + '년 ' + Q[4] + '분기)</em>') + yoyRow(t, MT) + row('남·여', pct(S3(15), S3(15) + S3(16)) + ' : ' + pct(S3(16), S3(15) + S3(16)));
      h += row('지금 시간대', TBL[b] + '시 — 시간당 약 ' + won(S3(3 + b) / TBH[b] / 30.4) + ' · 많은 업종 ' + ind.slice().sort(function (p, q) { return q[3 + b] - p[3 + b]; }).slice(0, 3).map(function (r) { return esc(r[0]); }).join(' · '));
      h += '<div class="cap">시간대별 시간당 카드 매출(원 · 하루 평균 · 0~6 … 21~24시)</div>' + bar([0, 1, 2, 3, 4, 5].map(function (i) { return S3(3 + i) / TBH[i] / 30.4; }), '#7c3aed', LB_TB6, 'w') + '<div class="cap">연령대별 카드 매출(원 · 한 달 · 10대 … 60세 이상)</div>' + bar([0, 1, 2, 3, 4, 5].map(function (i) { return S3(9 + i); }), '#a78bfa', LB_AGE6, 'w') + '<div class="cap">요일별 카드 매출(원 · 한 달 동안 그 요일 합 · 월~일)</div>' + bar([0, 1, 2, 3, 4, 5, 6].map(function (i) { return S3(17 + i); }), '#c4b5fd', LB_DW, 'w');
      var co2 = S3(2), wk = S3(17) + S3(18) + S3(19) + S3(20) + S3(21), we = S3(22) + S3(23), lunch = S3(5), eve = S3(7), nite = S3(8) + S3(3), pk = Math.max(lunch, eve, nite);
      h += row('객단가', (co2 ? Math.round(amt * 1e4 / co2).toLocaleString() : '-') + '원(건당 결제) · 주중 ' + pct(wk, wk + we) + '% · 주말 ' + pct(we, wk + we) + '%');
      h += row('피크', (pk === lunch ? '점심형(11~14시)' : pk === eve ? '저녁형(17~21시)' : '야간형(21~6시)') + ' — 점심 ' + pct(lunch, amt) + '% · 저녁 ' + pct(eve, amt) + '% · 밤 ' + pct(nite, amt) + '%');
      var nst = (t.stor || []).reduce(function (a, s) { return a + s[1]; }, 0); if (nst) h += row('경쟁·밀집', '점포 ' + nst + '곳 · ' + (nst / (t.area / 1e4)).toFixed(1) + '곳/ha · 점포당 한 달 ' + won(amt / nst));
      if (t.wrc && t.rep) { var jr = pct(t.wrc[0], t.wrc[0] + t.rep[0]); h += row('배후 수요', (jr >= 70 ? '직장 중심' : jr <= 30 ? '주거 배후' : '직장·주거 혼합') + ' — 직장 ' + man(t.wrc[0]) + ' · 상주 ' + man(t.rep[0]) + (t.flp ? ' · 하루 유동 ' + man(t.flp[0] / 91) : '')); }
      h += rentRows(it.x.c, '임대료(가까운 표본)');
      h += '<div class="cap">업종별 객단가 · 피크 · 점포(매출 많은 업종 8)</div>' + indCompare(t);
      h += barRows(ind, '이 상권');
      h += '<div class="cap">업종 × 연령(그 업종 매출 안 비중 % · 매출 많은 업종 8)</div>' + indTable(ind, 'age') + '<div class="cap">업종 × 시간대(그 업종 매출 안 비중 % · 테두리 = 지금)</div>' + indTable(ind, 'tb'); }
    if (t.se === '골목상권') h += hlRows(t);
    else h += row('카드 매출', '이 상권은 매출 자료가 없다');
    if (t.flp) { var f = t.flp; h += row('유동인구', '분기 ' + man(f[0]) + '명 · 하루 약 ' + man(f[0] / 91) + ' · 남 ' + pct(f[1], f[0]) + '%') + '<div class="cap">시간대별 유동인구(명/시 · 하루 평균 · 0~6 … 21~24시)</div>' + bar([0, 1, 2, 3, 4, 5].map(function (i) { return f[9 + i] / TBH[i] / 91; }), '#0284c7', LB_TB6) + '<div class="cap">연령대별 유동인구(명 · 한 분기 합 · 10대 … 60세 이상)</div>' + bar(f.slice(3, 9), '#38bdf8', LB_AGE6); }
    if (t.wrc) h += row('직장인구', man(t.wrc[0]) + '명 · 20·30대 ' + pct(t.wrc[4] + t.wrc[5], t.wrc[0]) + '%');
    if (t.rep) h += row('상주인구', man(t.rep[0]) + '명 · 가구 ' + man(t.rep[9]) + '(아파트 ' + man(t.rep[10]) + ')');
    if (t.stor && t.stor.length) { var st = t.stor.slice().sort(function (p, q) { return q[1] - p[1]; }), sn = st.reduce(function (a, s) { return a + s[1]; }, 0); h += row('점포', sn + '곳 · 개업 ' + st.reduce(function (a, s) { return a + s[3]; }, 0) + ' · 폐업 ' + st.reduce(function (a, s) { return a + s[4]; }, 0) + ' · 많은 업종 ' + st.slice(0, 4).map(function (s) { return esc(s[0]) + ' ' + s[1]; }).join(' · ')); }
    if (t.fac) { var FN = MT.fields.fac, fs = t.fac.map(function (v, i) { return v ? FN[i] + ' ' + v : ''; }).filter(Boolean); if (fs.length) h += row('집객시설', esc(fs.join(' · '))); }
    if (t.tr) { var qs = Object.keys(t.tr).sort(); h += '<div class="cap">분기별 카드 매출(원 · 한 달 기준 · ' + qs[0].slice(2, 4) + '.' + qs[0][4] + 'Q~' + qs[qs.length - 1].slice(2, 4) + '.' + qs[qs.length - 1][4] + 'Q)</div>' + bar(qs.map(function (q) { return t.tr[q][0]; }), '#6d28d9', qLab(qs), 'w') + '<div class="cap">분기별 밤(21~6시) 카드 매출(원 · 한 달 기준)</div>' + bar(qs.map(function (q) { return t.tr[q][2]; }), '#1e3a8a', qLab(qs), 'w') + '<div class="cap">분기별 주점·유흥 카드 매출(원 · 한 달 기준)</div>' + bar(qs.map(function (q) { return t.tr[q][1]; }), '#b45309', qLab(qs), 'w'); }
    return h + '<p class="desc">' + esc(MT.note) + '</p>' + src(MT.source);
  }
  // ---------- 💰 상가 임대료·공실률(v0.10.93 · 한국부동산원 상업용부동산 임대동향조사 · 표본 상권 72곳) ----------
  var RENT = null, RENTP = null;
  function rentLoad() { if (RENTP) return RENTP; RENTP = fetch('data/r/rent.json').then(function (r) { return r.json(); }).then(function (j) { RENT = j; j.items.forEach(function (it) { it.p = P(it.lon, it.lat); }); draw(); }).catch(function () { RENT = null; }); return RENTP; }
  function rentNear(q, max) { if (!RENT) return null; var b = null, bd = max || 1500; RENT.items.forEach(function (it) { var d = dTrue(it.p, q); if (d < bd) { bd = d; b = it; } }); return b ? { it: b, d: Math.round(bd) } : null; }
  function lastV(a) { if (!a) return null; for (var i = a.length - 1; i >= 0; i--) if (a[i] != null) return a[i]; return null; }
  function rentRows(q, title) {   // 가까운 부동산원 표본 상권 — 그 상권 자체 값이 아니다
    var R2 = rentNear(q, 1500); if (!R2) return RENT ? row('임대료', '<em>1.5km 안 부동산원 표본 상권 없음</em>') : '';
    var it = R2.it, Q = RENT.quarters, ql = Q[Q.length - 1], s1 = lastV(it.s), m1 = lastV(it.m), c1 = lastV(it.c);
    var won33 = function (v) { return v != null ? ' <small>(33㎡·10평이면 월 약 ' + Math.round(v * 33 / 10) + '만원)</small>' : ''; };
    return row(title || '임대료', '<b>' + esc(it.name) + '</b> <em>(부동산원 표본 상권 · ' + R2.d + 'm · ' + ql.slice(0, 4) + '년 ' + ql.slice(5) + '분기)</em>') +
      (s1 != null ? row('소규모 상가', s1 + '천원/㎡' + won33(s1) + (lastV(it.vs) != null ? ' · 공실 ' + lastV(it.vs) + '%' : '')) : '') +
      (m1 != null ? row('중대형 상가', m1 + '천원/㎡' + won33(m1) + (lastV(it.vm) != null ? ' · 공실 ' + lastV(it.vm) + '%' : '')) : '') +
      (c1 != null ? row('집합 상가', c1 + '천원/㎡' + won33(c1)) : '');
  }
  function rentCard(it) {
    var Q = RENT.quarters, L = Q.map(function (q) { return "'" + q.slice(2, 4) + '.' + q.slice(5); });
    var h = '<h3>💰 ' + esc(it.name) + ' <small style="font-weight:400;color:var(--ink2)">' + esc(it.grp) + ' · 부동산원 표본 상권</small></h3>' + row('대표 자리', esc(it.how) + ' <em>(상권 경계는 공개되지 않는다)</em>');
    [['s', '소규모 상가'], ['m', '중대형 상가'], ['c', '집합 상가']].forEach(function (k) { if (it[k[0]]) h += row(k[1], lastV(it[k[0]]) + '천원/㎡ · 33㎡(10평)이면 월 약 ' + Math.round(lastV(it[k[0]]) * 3.3) + '만원') + '<div class="cap">' + k[1] + ' 임대료 분기별(천원/㎡ · 한 달 · 전용+공용 면적)</div>' + bar(it[k[0]].map(function (v) { return v || 0; }), '#b45309', L); });
    [['vs', '소규모 상가'], ['vm', '중대형 상가']].forEach(function (k) { if (it[k[0]]) h += '<div class="cap">' + k[1] + ' 공실률 분기별(% · 빈 점포 면적 비율)</div>' + bar(it[k[0]].map(function (v) { return v || 0; }), '#64748b', L); });
    var SD = it.sido === '경기' ? '경기' : it.sido === '서울' ? '서울' : it.sido, A = RENT.agg[SD]; if (A && A.m) h += row(SD + ' 평균', '중대형 ' + lastV(A.m) + '천원/㎡ · 공실 ' + lastV(A.vm) + '% · 소규모 ' + lastV(A.s) + '천원/㎡ · 공실 ' + lastV(A.vs) + '%');
    h += '<div class="lg-btns"><button data-radhere="' + it.lon + ',' + it.lat + '">📐 여기서 반경 분석</button></div>';
    return h + '<p class="desc">' + esc(RENT.note) + '</p>' + src(RENT.source);
  }
  function drawRent(dark) {
    if (!on.rent) return; if (!RENT) { rentLoad(); return; }
    RENT.items.forEach(function (it) { var v = lastV(it.m) || lastV(it.s); dot(it.p, 6 + Math.min(10, (v || 0) / 15), 'rgba(180,83,9,.75)', '#fff', { kind: 'rent', it: it });
      if (view.s > 0.035) label([it.p[0], it.p[1] - 16 / view.s], it.name + (v ? ' ' + v : ''), 10.5, dark ? '#fde68a' : '#78350f', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); });
  }
  function yoyRow(t, MT) {   // 1년 전 같은 분기보다(지금도 있는 업종끼리)
    if (!t.indp) return ''; var a = 0, b = 0; (t.ind || []).forEach(function (r) { var q = t.indp[r[0]]; if (q && q[0] > 0) { a += r[1]; b += q[0]; } }); if (!b) return '';
    var ps = t.storp ? Object.keys(t.storp).reduce(function (x, k) { return x + t.storp[k]; }, 0) : 0, ns = (t.stor || []).reduce(function (x, s2) { return x + s2[1]; }, 0);
    return row('1년 전보다', (a >= b ? '+' : '') + Math.round((a - b) / b * 100) + '% 매출 <em>(' + (MT.prev || '').slice(0, 4) + '년 ' + (MT.prev || '').slice(4) + '분기 대비 · 같은 업종끼리)</em>' + (ps ? ' · 점포 ' + ps + ' → ' + ns : ''));
  }
  function indCompare(t) {   // 업종 | 한 달 매출 | 객단가 | 피크 | 점포(개업/폐업) — 같은 업종 경쟁
    var st = {}; (t.stor || []).forEach(function (s) { st[s[0]] = s; });
    var yy = !!t.indp;
    return '<table class="it"><tr><th>업종</th><th>한 달</th>' + (yy ? '<th>1년</th>' : '') + '<th>객단가</th><th>피크</th><th>점포</th></tr>' + (t.ind || []).slice().sort(function (a, b) { return b[1] - a[1]; }).slice(0, 8).map(function (r) {
      var pkI = 0; for (var i = 1; i < 6; i++) if (r[3 + i] > r[3 + pkI]) pkI = i; var s2 = st[r[0]], q = yy && t.indp[r[0]];
      return '<tr' + (isBar(r[0]) ? ' class="bar"' : '') + '><td>' + esc(r[0]) + '</td><td>' + won(r[1]) + '</td>' + (yy ? '<td>' + (q && q[0] > 0 ? (r[1] >= q[0] ? '+' : '') + Math.round((r[1] - q[0]) / q[0] * 100) + '%' : '-') + '</td>' : '') + '<td>' + (r[2] ? Math.round(r[1] * 1e4 / r[2]).toLocaleString() : '-') + '</td><td>' + TBL[pkI] + '</td><td>' + (s2 ? s2[1] + (s2[3] || s2[4] ? ' <small>+' + s2[3] + '/−' + s2[4] + '</small>' : '') : '-') + '</td></tr>'; }).join('') + '</table>';
  }
  function rDongCard(d) {   // 서울 다른 구의 동 — 지역 자료 하나로(서초 동 카드와 같은 줄 차례)
    rExt(d); var p = d.pop, R = d.rg, J = jurAtM(d.c), h = '<h3>🏘 ' + esc(d.gu + ' ' + d.name) + '</h3>';
    if (J) h += row('경찰서 관할', esc(J.z.name) + ' <em>(이 지도가 그린 관할 안)</em>');
    if (p) { h += row('주민', p.tot.toLocaleString() + '명') + row('19세 이하', Math.round((p.age[0] + p.age[1]) / p.tot * 100) + '%') + row('70세 이상', Math.round((p.age[7] + p.age[8] + p.age[9]) / p.tot * 100) + '%');
      h += '<div class="cap">주민 연령대별 인구(명 · 주민등록 · 0~9세 … 90~99세)</div>' + bar(p.age, '#8b5cf6', ageLab(p.age.length)); }
    var lv = liveNow(d);
    if (lv) h += row('생활인구 지금', lv.n.toLocaleString() + '명 <em>(' + (lv.we ? '주말' : '평일') + ' ' + lv.h + '시 평균)</em>') + row('하루 폭', Math.min.apply(null, lv.arr).toLocaleString() + ' ~ ' + Math.max.apply(null, lv.arr).toLocaleString() + '명') +
      '<div class="cap">시간대별 생활인구(명 · 그 시각 동 안에 있는 사람 · 0~23시 ' + (lv.we ? '주말' : '평일') + ' 평균)</div>' + bar(lv.arr, '#f97316');
    h += salesRows(d) + dongIndRows(d);
    if (d.old) { var o = { name: '옛 ' + d.old.name, live: d.old.live, sales: d.old.sales, pre: R };
      h += '<p class="desc">이 동은 옛 ' + esc(d.old.name) + '에서 나뉘었다 — 생활인구(2026.7)·카드 매출 원자료가 옛 동 하나로만 있어 아래는 <b>옛 ' + esc(d.old.name) + ' 전체</b> 값이다(나눠 지어내지 않는다).</p>';
      var lo = liveNow(o); if (lo) h += row('옛 ' + esc(d.old.name) + ' 생활인구', lo.n.toLocaleString() + '명 <em>(' + lo.h + '시)</em>') + '<div class="cap">옛 ' + esc(d.old.name) + ' 시간대별 생활인구(명 · 0~23시 ' + (lo.we ? '주말' : '평일') + ' 평균)</div>' + bar(lo.arr, '#fdba74');
      h += salesRows(o); }
    var sd2 = String(d.gcd).slice(0, 2), gg = sd2 !== '11';   // gg = 서울 밖(서울시 자료가 없는 곳)
    if (sd2 === '41') h += '<p class="desc">경기도 동 — 생활인구·카드 매출(상권분석)은 <b>서울시 자료</b>라 경기에는 없다. 주민 연령·남녀·관할·안전 시설·점포·학원·어린이집(경기도 자료)·유치원·학교는 있다.</p>';
    else if (gg) h += '<p class="desc">' + esc(sidoOf(d.gcd)) + ' 동 — 이 지역은 <b>전국 공통 자료</b>만 있다(주민 연령·남녀·상가·실거래·사고·집계구·교차로 이름). 생활인구·카드 매출(서울시)·경기데이터드림 자료는 그 지역에만 있어 여기에는 없다.</p>';
    else if (!lv && !d.old) h += '<p class="desc">생활인구(2026.7) 원자료에 이 동이 없다 — 새로 생긴 동이면 옛 동에 합쳐 있다.</p>';
    var sz2 = D.sz ? D.sz.zones.filter(function (z) { return inPoly(d, P(z.lon, z.lat)); }).length : 0; if (sz2) h += row('어린이보호구역', sz2 + '곳');
    h += facRows(d.gcd, d.name, d.k);
    h += polRows(d.k, d.c); h += jrsRows(d.k); h += fdRows(d.k); h += econRows(d.k);
    var GB = (rIdx().filter(function (g) { return g.gu === d.gcd; })[0] || {}).bytes || {};
    if (d.k) h += '<div class="lg-btns">' + (GB.ggcard ? '<button data-ggc="' + esc(d.gcd) + '|' + esc(d.k) + '">💳 카드 소비 자세히(연령·성별·시간·업종)</button>' : '') + '<button data-ai="' + esc(d.gcd) + '|' + esc(d.k) + '">🤖 AI용 복사 — 이 동 기본 자료</button></div>';
    var F3 = FRN && FRN.gu[d.gcd]; if (F3 && F3['2024']) h += row('외국인 주민(구)', (F3['2024'].tot || 0).toLocaleString() + '명 <em>(' + esc(F3.src) + ' · 2024)</em>') + '<div class="lg-btns"><button data-frn="' + esc(d.gcd) + '">🌏 외국인 자세히(국적·영주·나이·성별)</button></div>';
    return h + src('경계: ' + R.source['경계'] + ' · 주민: ' + R.source['주민'] + (gg ? '' : ' · 생활인구: ' + R.source['생활인구']));
  }
  function dongIndRows(x) {   // 행정동 — 업종 × 연령 · 업종 × 시간대 · 주점·유흥
    var d = typeof x === 'string' ? { name: x } : x, ind = d.rg ? d.x && d.x.ind : D.trdar && D.trdar.dong && D.trdar.dong[d.name]; if (!ind || !ind.length) return d.rg && d.x === null ? '<p class="desc">업종 표를 받는 중…</p>' : '';
    return barRows(ind, '이 동') + '<div class="cap">업종 × 연령(%) — 이 동 매출 많은 업종 8</div>' + indTable(ind, 'age') + '<div class="cap">업종 × 시간대(%)</div>' + indTable(ind, 'tb');
  }
  // ---------- 🚗 교통사고 10년(v0.10.79 · TAAS 2016~2025 서초 22,546건 · 100m 칸 + 사망사고 한 건씩) ----------
  // v0.10.89 경찰서 통계 — 소유자 「단속 실적도 5년치 · 범죄나 생활에 필요한 정보」: 현장 단속 5개 해 · 112 출동 15년 · 5대 범죄 · 지구대·파출소
  function stKey(name) { return String(name || '').replace(/^서울/, '').replace(/경찰서$/, ''); }
  function polStats(name) { var S = D.pstat; if (!S || !name) return ''; var k = stKey(name), h = '';
    var E = S.enf[k];
    if (E) { var ys = Object.keys(E).sort(), last = E[ys[ys.length - 1]];
      h += '<div class="cap">🚓 해마다 현장 단속 건수(건 · 경찰관 단속 기록 · 무인 장비 제외 · 2017~2020 파일 없음)</div>' + bar(ys.map(function (y) { return E[y].n; }), '#1d4ed8', ys.map(function (y) { return yLab(+y, 1)[0]; }));
      h += row(ys[ys.length - 1] + '년 많이 단속한 조항', last.art.slice(0, 6).map(function (a) { var m = String(a[0]).match(/(\d+)조(의\d+)?/), t = m ? S.titles[m[1] + (m[2] || '')] : ''; return esc(a[0]) + (t ? ' <em>' + esc(t) + '</em>' : '') + ' ' + a[1].toLocaleString(); }).join('<br>'));
      h += row('차종', last.veh.map(function (v) { return esc(v[0] || '-') + ' ' + v[1].toLocaleString(); }).join(' · '));
      h += row('많이 단속한 자리', last.pl.slice(0, 4).map(function (v) { return esc(v[0]) + ' ' + v[1].toLocaleString(); }).join('<br>') + ' <em>(기록 글 그대로)</em>');
      if (k === '동작' && E['2023'] && E['2023'].n < 2000) h += '<p class="desc">⚠ 동작서 2023년 파일은 건수가 다른 해의 10분의 1도 안 된다 — 원자료 그대로 둔다(빠진 기록으로 보임).</p>'; }
    var C = S.call[k];
    if (C) h += '<div class="cap">📞 해마다 112 신고 출동 건수(건 · ' + S.callYears[0] + '~' + S.callYears[S.callYears.length - 1] + ')</div>' + bar(C.map(function (v) { return v || 0; }), '#7c3aed', S.callYears.map(function (y) { return "'" + String(y).slice(2); }));
    var R = S.crime[k], ry = S.crimeYear;
    if (!R && S.gn) { R = S.gn[k]; ry = S.gnYear; }
    if (R) { var KS = ['살인', '강도', '강간·추행', '절도', '폭력'];
      h += '<div class="cap">🚨 5대 범죄 ' + ry + '년 — 발생 / 검거(검거율)</div><table class="it"><tr><th></th>' + KS.map(function (x) { return '<th>' + x + '</th>'; }).join('') + '</tr>' +
        '<tr><td>발생</td>' + KS.map(function (x) { return '<td>' + ((R[x] || [0])[0]).toLocaleString() + '</td>'; }).join('') + '</tr>' +
        '<tr><td>검거</td>' + KS.map(function (x) { var v = R[x] || [0, 0]; return '<td>' + v[1].toLocaleString() + (v[0] ? '<br><small>' + Math.round(v[1] / v[0] * 100) + '%</small>' : '') + '</td>'; }).join('') + '</tr></table>'; }
    var B = S.box[k];
    if (B) { var n = B.length; h += row('지역경찰 관서(' + String(S.boxCols[n - 1]).slice(0, 4) + ')', '지구대 ' + B[n - 3] + ' · 파출소 ' + B[n - 2] + ' · 치안센터 ' + B[n - 1]); }
    if (!E && !C && R) h += '<p class="desc">경기남부경찰청은 경찰서별 단속·112 출동 공개 파일을 찾지 못했다 — 5대 범죄만(' + ry + '년이 공개된 마지막 해).</p>';
    if (h) h += '<p class="desc">출처 — ' + esc([S.source.enf, S.source.call, S.source.crime, S.source.box, S.source.gn].join(' · ')) + ' · ' + esc(S.license) + '</p>';
    return h; }
  // v0.10.84 경찰서별 단속 건수(서울청 2024 · 무인·현장 합계) — 카메라 한 대 단위 건수는 공개되지 않는다
  function enfOf(name) { var E = D.enf; if (!E || !name) return null; var k = String(name).replace(/^서울/, '').replace(/경찰서$/, '');
    for (var i = 0; i < E.items.length; i++) if (E.items[i][0] === k) return E.items[i]; return null; }
  function enfRows(name) { var r = enfOf(name), E = D.enf; if (!r) return '';
    function rk(j) { var v = r[j], n = 1; E.items.forEach(function (x) { if (x[j] > v) n++; }); return n; }
    var lab = ['', '중앙선 침범', '신호위반', '음주운전', '무면허운전', '속도위반'], ord = [5, 2, 1, 3, 4];
    return row(E.year + '년 단속', ord.map(function (j) { return lab[j] + ' ' + r[j].toLocaleString() + '건 <em>(서울 ' + E.items.length + '서 중 ' + rk(j) + '위)</em>'; }).join('<br>')) +
      '<p class="desc">경찰서 한 해 합계 — 무인 장비와 경찰관 현장단속이 섞여 있다(속도위반은 대부분 무인 장비로 본다 · 추정). 카메라 한 대 단위 건수는 공개되지 않는다. 출처 ' + esc(E.source) + '</p>'; }
  // v0.10.84 카메라 설치 전후 둘레 사고(참고 지표) — 설치 해를 빼고 앞뒤 3년씩 연평균을 견주고, 같은 해 서초 전체 변화와 나란히 보인다
  var CAM_R = 150, CAM_W = 3;
  function camYears(yr) { var b = [], a = []; for (var y = Math.max(2016, yr - CAM_W); y < yr; y++) b.push(y); for (var y2 = yr + 1; y2 <= Math.min(2025, yr + CAM_W); y2++) a.push(y2); return [b, a]; }
  function camCalc(cm) { if (!A10.length) return null; if (cm._e) return cm._e; return (cm._e = camCalc0(cm)); }
  function camCalc0(cm) { var yr = parseInt(cm.yr, 10); if (!(yr >= 2017 && yr <= 2024)) return { no: '설치 ' + (cm.yr || '?') + '년 — 사고 자료(2016~2025)로 설치 전·뒤를 함께 볼 수 없다' };
    var p = P(cm.lon, cm.lat), ys = camYears(yr), loc = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], all = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
    A10.forEach(function (x) { var c = x.c, near = dTrue(x.p, p) <= CAM_R; for (var i = 0; i < 10; i++) { all[i] += c[2 + i]; if (near) loc[i] += c[2 + i]; } });
    function avg(arr, list) { return list.reduce(function (t, y) { return t + arr[y - 2016]; }, 0) / list.length; }
    var lb = avg(loc, ys[0]), la = avg(loc, ys[1]), ab = avg(all, ys[0]), aa = avg(all, ys[1]);
    return { yr: yr, ys: ys, loc: loc, lb: lb, la: la, ch: lb ? (la - lb) / lb : null, ach: ab ? (aa - ab) / ab : null, few: (lb + la) * ys[0].length < 6 }; }
  function pctS(v) { return (v > 0 ? '+' : '') + Math.round(v * 100) + '%'; }
  function camEff(cm) { var r = camCalc(cm); if (!r) return row('설치 전후 사고', '사고 10년 자료를 읽는 중…'); if (r.no) return row('설치 전후 사고', esc(r.no));
    var y0 = r.ys[0], y1 = r.ys[1], rng = function (l) { return l[0] + (l.length > 1 ? '~' + l[l.length - 1] : '') + '년'; };
    var v = r.few ? '둘레 사고가 적어 견주기 어렵다' : r.ch == null ? '설치 전 사고 0건' : (r.ch < r.ach - 0.1 ? '<b style="color:#15803d">서초 전체보다 더 줄었다</b>' : r.ch > r.ach + 0.1 ? '<b style="color:#b91c1c">서초 전체보다 덜 줄었다(늘었다)</b>' : '서초 전체와 비슷하게 변했다');
    return row('설치 전후 사고', '둘레 ' + CAM_R + 'm · 설치 전 ' + rng(y0) + ' 연평균 ' + r.lb.toFixed(1) + '건 → 설치 뒤 ' + rng(y1) + ' 연평균 ' + r.la.toFixed(1) + '건' + (r.ch != null ? ' (' + pctS(r.ch) + ')' : '')) +
      row('견주기', '서초 전체 같은 해 ' + (r.ach != null ? pctS(r.ach) : '-') + ' → ' + v) +
      '<div class="cap">카메라 둘레 ' + CAM_R + 'm 해마다 교통사고 건수(건 · 2016~2025 · 설치 ' + r.yr + '년)</div>' + bar(r.loc, '#2563eb', LB_Y16) +
      '<p class="desc">참고 지표 — 단속 건수가 아니라 둘레 사고의 변화다. 교통량·도로 공사·다른 시설 변화가 섞이고, 사고가 많아서 설치한 자리는 그 뒤 저절로 줄어 보일 수 있다(평균으로 돌아감). 100m 칸 가운데가 ' + CAM_R + 'm 안이면 센다.</p>'; }
  // 점 색 = 설치 전후 사고(참고) — 초록 서초 전체보다 더 줄었다 · 빨강 덜 줄거나 늘었다 · 파랑 비슷하거나 견줄 수 없음
  function camCol(c) { var r = camCalc(c); if (!r || r.no || r.few || r.ch == null) return '#2563eb'; return r.ch < r.ach - 0.1 ? '#16a34a' : r.ch > r.ach + 0.1 ? '#dc2626' : '#2563eb'; }
  function camSum() { if (!D.cam || !A10.length) return ''; var n = 0, more = 0, less = 0;
    D.cam.items.forEach(function (c) { var r = camCalc(c); if (!r || r.no || r.few || r.ch == null) return; n++; if (r.ch < r.ach - 0.1) more++; else if (r.ch > r.ach + 0.1) less++; });
    return '<small class="lg-n">설치 전후 사고를 견줄 수 있는 카메라 ' + n + '대 — 서초 전체보다 더 줄어든 곳 ' + more + ' · 덜 줄거나 는 곳 ' + less + ' · 비슷 ' + (n - more - less) + '(참고 지표 · 카드에 자세히)</small>'; }
  var A10 = [], F10 = [], A10M = 'all', A10Y = null;   // A10Y = 그 해만(null = 10년 전부)
  // v2.3.1 같은 100m 칸이 두 구 파일에 있으면(법정동이 다른 사고 — 서울 1,802칸·서울/경기 경계) 한 칸으로 더한다 — 겹쳐 그려 같은 칸이 두 번 보였다 · 건수는 더하고 주 법규위반·유형은 건수가 큰 쪽
  var A10K = {};
  function a10Add(c, m) { var k = c[0] + ',' + c[1], x = A10K[k];
    if (!x) { x = A10K[k] = { c: c, p: P(c[1], c[0]), m: m }; A10.push(x); return; }
    if (!x.mm) x.mm = [{ c: x.c, m: x.m }]; x.mm.push({ c: c, m: m }); var n = x.c.slice(); for (var i = 2; i <= 22; i++) n[i] += c[i]; if (c[24] > n[24]) { n[23] = c[23]; n[24] = c[24]; n[25] = c[25]; } x.c = n; }
  var A10MS = { all: ['전체 사고', '#ea580c'], sev: ['사망·중상자', '#b91c1c'], ped: ['보행자 피해', '#2563eb'], two: ['자전거·PM·이륜', '#16a34a'], night: ['밤(20~6시)', '#1e3a8a'], rate: ['사고율(÷하차 · R2)', '#9333ea'] };
  function a10Prep() { var T = D.taas10; if (!T) return; var kA = A10.filter(function (x) { return x.m; }), kF = F10.filter(function (x) { return x.m; });   // 먼저 온 구 파일은 남긴다
    A10 = []; A10K = {}; T.cells.forEach(function (c) { a10Add(c, null); }); kA.forEach(function (x) { (x.mm || [x]).forEach(function (q) { a10Add(q.c, q.m); }); }); F10 = T.fatal.map(function (f) { return { f: f, p: P(f[17], f[16]) }; }).concat(kF);
    // 교차로 집계를 2019년부터(v0.10.82 · 소유자 「사고 데이터 2019년부터」) — 칸을 585m 안 가장 가까운 실제 교차로에 배정(23~25 집계와 같은 규칙)
    NODES.forEach(function (n) { n.y10 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; n.d10 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; n.ped = 0; n.sev = 0; });
    function near(p) { var b = null, bd = 585; NODES.forEach(function (n) { if (!n.real) return; var d = dTrue(n.p, p); if (d < bd) { bd = d; b = n; } }); return b; }
    A10.forEach(function (x) { var n = near(x.p); if (!n) return; for (var i = 0; i < 10; i++) n.y10[i] += x.c[2 + i]; n.ped += x.c[14]; n.sev += x.c[12] + x.c[13]; });
    F10.forEach(function (x) { var n = near(x.p); if (n) n.d10[x.f[0] - 2016] += x.f[12]; });
  }
  function accN(n, a, b) { if (!n.y10) return 0; var t = 0; for (var y = a; y <= b; y++) t += n.y10[y - 2016]; return t; }
  function deadN(n, a, b) { if (!n.d10) return 0; var t = 0; for (var y = a; y <= b; y++) t += n.d10[y - 2016]; return t; }
  function a10Val(c, x) {
    if (A10M === 'rate') { var rr = x && a10Rate(x); return rr ? rr.v : 0; }
    if (A10M === 'all') return A10Y === 19 ? c.slice(5, 12).reduce(function (a, b) { return a + b; }, 0) : A10Y ? c[2 + A10Y - 2016] : c.slice(2, 12).reduce(function (a, b) { return a + b; }, 0);
    var share = A10Y === 19 ? c.slice(5, 12).reduce(function (a, b) { return a + b; }, 0) / Math.max(1, c.slice(2, 12).reduce(function (a, b) { return a + b; }, 0)) : A10Y ? c[2 + A10Y - 2016] / Math.max(1, c.slice(2, 12).reduce(function (a, b) { return a + b; }, 0)) : 1;
    return (A10M === 'sev' ? c[12] + c[13] : A10M === 'ped' ? c[14] : A10M === 'two' ? c[15] + c[16] + c[17] : c[18]) * share;
  }
  function drawA10(dark) {
    if (on.acc10 && A10.length) { if (A10M === 'rate') rateReady(); var vs = A10.map(function (x) { return a10Val(x.c, x); }), mx = Math.max.apply(null, vs) || 1, col = A10MS[A10M][1], h = 50;
      var W0 = cv.clientWidth, H0 = cv.clientHeight;
      A10.forEach(function (x, k) { var v = vs[k]; if (!v) return; var t = Math.sqrt(v / mx), a = S([x.p[0] - h, x.p[1] - h]), b = S([x.p[0] + h, x.p[1] + h]); if (b[0] < 0 || b[1] < 0 || a[0] > W0 || a[1] > H0) return;
        ctx.fillStyle = hexA(col, 0.12 + 0.7 * t); ctx.fillRect(a[0], a[1], b[0] - a[0], b[1] - a[1]); if (A10M === 'rate' && x.rt && x.rt.hid) { ctx.lineWidth = 2.5; ctx.strokeStyle = '#facc15'; ctx.strokeRect(a[0] + 1, a[1] + 1, b[0] - a[0] - 2, b[1] - a[1] - 2); }
        if (view.s > 0.35) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = t > 0.5 ? '#fff' : '#111827'; ctx.fillText(String(Math.round(v)), (a[0] + b[0]) / 2, (a[1] + b[1]) / 2); }
        hit.push({ x: (a[0] + b[0]) / 2, y: (a[1] + b[1]) / 2, r: Math.max(6, (b[0] - a[0]) / 2), it: { kind: 'a10', x: x } }); }); }
    if (on.fatal10 && F10.length) F10.forEach(function (x) { if (A10Y === 19 ? x.f[0] < 2019 : A10Y && x.f[0] !== A10Y) return; dot(x.p, 5.5, '#111827', '#fca5a5', { kind: 'f10', x: x }); });
  }
  var DICT = null;
  function dic(k, v) { var D2 = (((DICT && DICT.dic ? DICT : D.taas10) || {}).dic || {})[k] || {}; return D2[v] || v || '-'; }
  function a10Card(it) {
    var T = it.x.m || D.taas10; DICT = T;
    if (it.kind === 'f10') { var f = it.x.f; return '<h3>🕯 사망사고 — ' + f[0] + '년 ' + f[1] + '월</h3>' + row('때', T.dow[f[2]] + '요일 ' + f[3] + '시') + row('유형', esc(dic('t', f[5]))) + row('법규위반', esc(dic('v', f[6]))) + row('도로', esc(dic('r', f[7]))) +
      row('날씨·노면', esc(dic('w', f[8]) + ' · ' + dic('s', f[9]))) + row('가해 / 피해', esc(dic('k', f[10]) + ' / ' + dic('k', f[11]))) + row('사상', '사망 ' + f[12] + ' · 중상 ' + f[13] + ' · 경상 ' + f[14] + (f[15] ? ' · 부상신고 ' + f[15] : '')) + '<p class="desc">' + esc(T.note) + '</p>' + src(T.source); }
    var c = it.x.c, tot = c.slice(2, 12).reduce(function (a, b) { return a + b; }, 0), ys = []; for (var y = 2016; y <= 2025; y++) ys.push(y);
    return '<h3>🚗 사고 10년 — 이 ' + (it.x.k ? '250m 칸 ' + esc(it.x.k) : '100m 칸') + '</h3>' + row('2016~2025', tot + '건 · 사망 ' + c[12] + ' · 중상 ' + c[13]) + row('누가', '보행자 피해 ' + c[14] + ' · 자전거 ' + c[15] + ' · PM ' + c[16] + ' · 이륜·원동기 가해 ' + c[17]) +
      (function () { var rr = a10Rate(it.x); return rr ? row('사고율(R2)', '하루 하차 1천 명당 10년 <b>' + rr.v.toFixed(1) + '건</b> · 150m 안 하차 ' + Math.round(rr.off).toLocaleString() + '명' + (rr.hid ? ' · <b style="color:#a16207">숨은 위험(사고율 상위 10% · 건수는 아님)</b>' : '') + ' ' + ledgBadge('R2')) : ''; })() + row('주 법규위반', esc(dic('v', c[23])) + ' ' + c[24] + '건') + row('주 유형', esc(dic('t', c[25]))) + row('밤(20~6시)', c[18] + '건 (' + pct(c[18], tot) + '%)') + (it.x.mm ? row('자료', it.x.mm.length + '개 구 파일의 같은 칸을 더함 — 사고가 난 법정동이 서로 다른 구') : '') +
      '<div class="cap">해마다 교통사고 건수(건 · 2016~2025 · 이 ' + (it.x.k ? '250m' : '100m') + ' 칸)</div>' + bar(c.slice(2, 12), '#ea580c', LB_Y16) + '<div class="cap">시간대별 교통사고 건수(건 · 10년 합 · 0~6 · 6~12 · 12~18 · 18~24시)</div>' + bar(c.slice(19, 23), '#1e3a8a', LB_TB4) + '<p class="desc">' + esc(T.note) + '</p>' + src(T.source);
  }
  function a10Legend() {
    if (!on.acc10 && !on.fatal10 && !on.acc250) return null; var ys = ['', 19]; for (var y = 2016; y <= 2025; y++) ys.push(y);
    return ['🚗 사고 10년(TAAS)', '<div class="lg-btns">' + Object.keys(A10MS).map(function (k) { return '<button data-a10m="' + k + '" class="' + (k === A10M ? 'on' : '') + '">' + A10MS[k][0] + '</button>'; }).join('') + '</div>' +
      '<div class="lg-btns"><select data-a10y aria-label="해">' + ys.map(function (y) { return '<option value="' + y + '"' + ((A10Y || '') == y ? ' selected' : '') + '>' + (y === 19 ? '2019~2025' : y ? y + '년만' : '10년 전부') + '</option>'; }).join('') + '</select></div>' +
      li(hexA(A10MS[A10M][1], 0.8), A10M === 'rate' ? '사고율 = 10년 사고 ÷ 150m 안 하루 하차 × 1,000 · 하차 200명 미만 칸은 안 칠함' : '100m 칸 · 진할수록 많음(√) · 확대하면 숫자', 'box') + (A10M === 'rate' ? li('#facc15', '숨은 위험 — 사고율 상위 10% · 건수는 상위 10% 밖', 'line') + '<small class="lg-n">' + ledgBadge('R2') + ' 노출(하차)은 2026년 6월 한 달 값을 10년에 썼다 · 서울만(교통카드 자료)</small>' : '') + (on.fatal10 ? li('#111827', '사망사고(한 건씩)') : '') + '<small class="lg-n">' + (D.taas10 ? D.taas10.count.toLocaleString() + '건 · 개인정보 없음' : '') + '</small>'];
  }
  // ---------- 🛡 치안·생활안전 시설(v0.10.78 · 서울 열린데이터 — 서초구) ----------
  var SAFE = [], SRCX = {};   // [층 키, 이름, 색, 점들[{p, it}]] · SRCX = 경기 구 파일이 가져온 출처(경기 생활시설)
  var SRC_C = { '301': '#dc2626', '302': '#1d4ed8', '303': '#64748b', '304': '#94a3b8', '305': '#f59e0b', '306': '#64748b', '307': '#7c3aed', '308': '#64748b' };
  function safePrep() {
    var Sx = D.safety; if (!Sx) return; var I = Sx.items, C = Sx.codes || {};
    function add(k, name, col, arr, f) { var pts = []; arr.forEach(function (r) { if (r[0] && r[1]) pts.push({ p: P(r[1], r[0]), r: r }); }); SAFE.push([k, name, col, pts, f]); POLL.push([k, name, col, f ? '' : name]); }
    add('srbell', '🔔 안심벨(안심귀갓길)', '#dc2626', I.srItem.filter(function (r) { return r[2] === '301'; }));
    add('srcctv', '📹 CCTV(안심귀갓길)', '#1d4ed8', I.srItem.filter(function (r) { return r[2] === '302'; }));
    add('srlamp', '💡 보안등(안심귀갓길)', '#f59e0b', I.srItem.filter(function (r) { return r[2] === '305'; }));
    add('sr112', '🆘 112 위치 신고 안내', '#7c3aed', I.srItem.filter(function (r) { return r[2] === '307' || r[2] === '303' || r[2] === '304' || r[2] === '306' || r[2] === '308'; }));
    add('srsvc', '🏪 안심 서비스·지킴이집', '#db2777', I.srSvc);
    add('aed', '❤️ 자동심장충격기(AED)', '#e11d48', I.aed);
    add('fw', '🧯 소방용수(소화전 등)', '#ef4444', I.fire);
    add('pkcctv', '📸 불법주정차 단속 CCTV', '#0f766e', I.pkcctv);
    add('tow', '🛻 견인차량보관소', '#78350f', I.tow);
    add('wc2', '🚻 공중화장실(서울·경기 공식 목록)', '#0891b2', I.wc);
    add('gpark', '🅿 주차장(공식 목록 · 전국)', '#2563eb', []); add('tlt', '🚦 신호등(전국 표준데이터)', '#15803d', []); add('bstop', '🚏 버스정류장 자리(OSM)', '#0284c7', []); add('gev', '🔌 전기차 충전소(경기)', '#16a34a', []); add('ger', '🏥 응급의료기관(경기)', '#be123c', []); add('gfest', '🎪 문화축제(경기)', '#c026d3', []); add('glamp', '💡 보안등(경기)', '#eab308', []);
    add('box', '📦 안심택배함', '#a16207', I.box);
    add('dem', '🧠 치매안심센터', '#9333ea', I.dem);
  }
  // ---------- 🗓 계절 취약지(v0.10.85 · 소유자 「겨울에는 결빙 여름에는 폭우 등 위험한 지역을 자동으로 데이터에 맞게」) ----------
  // 고른 날짜의 달로 계절을 정한다 — 6~9월 폭우(침수흔적·침수 이력 도로·지하차도) · 11~3월 결빙(제설함·열선 길·전진기지·결빙 다발지) · 그 밖은 둘 다
  var SEA = null;
  function dec2(a, k) { var out = [], x = a[k], z = a[k + 1]; out.push([x, z]); for (var i = k + 2; i < a.length; i += 2) { x += a[i]; z += a[i + 1]; out.push([x, z]); } return out; }
  function seasonPrep() { var Sd = D.season; if (!Sd) return;
    SEA = { tr: Sd.traces.map(function (t) { return { p: [t[0], t[1]], t: t }; }), fr: Sd.floodRoads.map(function (r) { return { r: r, pts: dec2(r, 6) }; }),
      un: Sd.under.map(function (u) { return { p: [u[2], u[3]], u: u }; }), ib: Sd.sbox.map(function (b) { return { p: [b[0], b[1]], b: b }; }), ad: Sd.adv.map(function (a) { return { p: [a[0], a[1]], a: a }; }),
      ht: Sd.heat.map(function (h) { return { h: h, segs: h[5].map(function (a) { return dec2(a, 0); }) }; }), pb: D.pbtn ? D.pbtn.items.map(function (b) { return { p: [b[0], b[1]], b: b }; }) : [] }; }
  function seasonInfo() { var m = +String(pickDate()).slice(5, 7) || (new Date().getMonth() + 1), hh = nowH();
    if (m >= 6 && m <= 9) return { k: 'rain', icon: '🌧', short: '폭우', name: m + '월 장마·집중호우 철', keys: ['flt', 'flr', 'und', 'hot10'] };
    if (m >= 11 || m <= 3) return { k: 'ice', icon: '🧊', short: '결빙', name: m + '월 결빙 철' + (hh >= 0 && hh < 10 ? ' · 새벽·아침' : ''), keys: ['ice', 'hcab', 'advb', 'hot10'] };
    return { k: 'both', icon: '🗓', short: '침수·결빙', name: m + '월 환절기', keys: ['flr', 'und', 'ice', 'hcab'] }; }
  function seasonCount(si) { if (!SEA) return ''; var Sd = D.season;
    var nm = {}; SEA.fr.forEach(function (r) { if (r.r[2] >= 2 && r.r[0]) nm[r.r[0]] = 1; }); var fr = Object.keys(nm).length, un = SEA.un.filter(function (u) { return u.u[5]; }).length;
    if (si.k === 'rain') return '두 해 넘게 침수 흔적이 닿은 길 ' + fr + '곳 · 침수 흔적 가까운 지하차도 ' + un + '곳';
    if (si.k === 'ice') return '제설함 ' + SEA.ib.length + '곳 · 열선 길 ' + SEA.ht.length + '곳';
    return '두 해 넘게 침수 흔적이 닿은 길 ' + fr + '곳 · 제설함 ' + SEA.ib.length + '곳'; }
  function polyl(pts, col, w, dark, it) { if (pts.length < 2) return; ctx.beginPath(); pts.forEach(function (q, i) { var a = S(q); if (i) ctx.lineTo(a[0], a[1]); else ctx.moveTo(a[0], a[1]); });
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke();
    if (it) { var m = S(pts[Math.floor(pts.length / 2)]); hit.push({ x: m[0], y: m[1], r: 10, it: it }); } }
  var FR_C = ['#7dd3fc', '#38bdf8', '#0284c7', '#1e3a8a'];
  function drawSeason(dark) { if (!SEA) return; var Sd = D.season, z = view.s;
    var va2 = M(0, 0), vb2 = M(cv.clientWidth, cv.clientHeight), offv = function (bb) { return bb && (bb[1] < va2[0] || bb[0] > vb2[0] || bb[3] < va2[1] || bb[2] > vb2[1]); };
    if (on.flr) SEA.fr.forEach(function (r) { if (offv(r.bb)) return; var n = Math.min(3, r.r[2]); polyl(r.pts, FR_C[n], Math.max(3, (n + 2) * Math.min(1.6, z * 6)), dark, { kind: 'season', k: 'flr', r: r }); });
    if (on.hcab) SEA.ht.forEach(function (h) { h.segs.forEach(function (pts, i) { polyl(pts, '#f97316', Math.max(3, Math.min(7, z * 18)), dark, i === 0 ? { kind: 'season', k: 'hcab', h: h } : null); }); });
    if (on.flt) SEA.tr.forEach(function (t) { var d = t.t[4], c = d >= 1 ? '#1e3a8a' : d >= 0.5 ? '#2563eb' : '#60a5fa'; dot(t.p, z < 0.12 ? 2.2 : 3 + Math.min(4, Math.sqrt(t.t[3])), hexA(c, 0.75), z < 0.12 ? null : '#fff', z < 0.12 ? null : { kind: 'season', k: 'flt', t: t }); });
    if (on.und) SEA.un.forEach(function (u) { var a = S(u.p), wet = u.u[5] > 0, r = 7; ctx.fillStyle = wet ? '#b91c1c' : '#475569'; ctx.fillRect(a[0] - r, a[1] - r, r * 2, r * 2); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.strokeRect(a[0] - r, a[1] - r, r * 2, r * 2);
      ctx.fillStyle = '#fff'; ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('U', a[0], a[1] + 0.5); hit.push({ x: a[0], y: a[1], r: 11, it: { kind: 'season', k: 'und', u: u } });
      if (z > 0.18 && u.u[0]) label([u.p[0], u.p[1] + 16 / z], u.u[0] + (wet ? ' · 침수 ' + u.u[5] + '해' : ''), 10.5, wet ? '#7f1d1d' : '#334155', 'rgba(255,255,255,.85)'); });
    if (on.ice) SEA.ib.forEach(function (b) { dot(b.p, z < 0.12 ? 2 : 3.6, '#06b6d4', z < 0.12 ? null : '#fff', z < 0.12 ? null : { kind: 'season', k: 'ice', b: b }); });
    if (on.advb) SEA.ad.forEach(function (a) { dot(a.p, 7, '#0e7490', '#fff', { kind: 'season', k: 'advb', a: a }); });
    if (on.pbtn) SEA.pb.forEach(function (b) { dot(b.p, 5.5, '#16a34a', '#fff', { kind: 'season', k: 'pbtn', b: b }); if (z > 0.3) label([b.p[0], b.p[1] + 14 / z], '보행자 작동', 10, '#14532d', 'rgba(255,255,255,.85)'); });
  }
  function seasonCard(it) { var o0 = it.t || it.r || it.u || it.b || it.h || it.a || {}, Sd = o0.m || D.season, h = '', k = it.k, src2 = '';
    if (k === 'flt') { var t = it.t.t, near = SEA.tr.filter(function (o) { return dTrue(o.p, it.t.p) < 40; }), ys = {}; near.forEach(function (o) { ys[o.t[2]] = 1; });
      h = '<h3>🌊 침수 흔적 — ' + t[2] + '년</h3>' + row('흔적', t[3] + '곳(20m 칸에 묶음)') + row('최대 침수심', t[4] ? t[4] + 'm' : '기록 없음') + row('원인', esc(Sd.causes[t[5]] || '-')) + row('동', esc(Sd.zones[t[6]] || '-')) +
        row('이 자리 40m 안 침수 해', Object.keys(ys).sort().join(' · ')) + '<p class="desc">건물·필지가 물에 잠긴 범위의 가운데 점이다(도로 침수 기록이 아니다). 2015·2021년은 서울시 자료가 없다.</p>'; src2 = Sd.source.flood; }
    else if (k === 'flr') { var r = it.r.r; h = '<h3>🌧 침수 이력 도로 — ' + esc(r[0] || '이름 없는 길') + '</h3>' + row('침수 흔적 해 수', r[2] + '해 · 마지막 ' + r[3] + '년') + row('둘레 흔적', r[5] + '곳 · 최대 침수심 ' + (r[4] || '-') + 'm') +
        '<p class="desc">이 도로 조각 30m 안에 침수 흔적이 있다는 뜻 — 이 앱이 계산한 근사이고 도로가 잠겼다는 공식 기록은 아니다. 큰비 예보 때 먼저 볼 자리로 쓴다.</p>'; src2 = Sd.source.floodRoads; }
    else if (k === 'und') { var u = it.u.u; h = '<h3>🚇 지하차도 — ' + esc(u[0] || '이름 없음') + '</h3>' + row('길이', u[4] + 'm(OSM)') + row('150m 안 침수 흔적', u[5] ? u[5] + '해 · 마지막 ' + u[6] + '년' : '없음') +
        '<p class="desc">서울시는 침수 우려 지하차도에 진입차단시설·침수감지장치를 두고 통제 정보를 실시간으로 보낸다(행안부 재난안전데이터 공유플랫폼 → 내비). 차단시설 자리·실시간 통제는 공개 파일이 없어 이 지도(통신 0)에는 없다 — 큰비 때 통제 여부는 상황실·내비로 확인.</p>'; src2 = Sd.source.under; }
    else if (k === 'ice') { var b = it.b.b; h = '<h3>🧊 제설함 ' + esc(b[2]) + '</h3>' + row('자리', esc(b[3])) + '<p class="desc">제설함은 눈·결빙이 잦은 경사로·교량·그늘진 길에 둔다 — 겨울 새벽 결빙 우려 자리로 본다(추정).</p>'; src2 = Sd.source.sbox; }
    else if (k === 'hcab') { var hh = it.h.h; h = '<h3>🔥 도로 열선 — ' + esc(hh[4]) + '</h3>' + row('설치 위치(원문)', esc(hh[2])) + row('설치', esc(hh[1]) + ' · ' + esc(hh[3]) + 'm · ' + esc(hh[0])) +
        '<p class="desc">열선은 결빙이 잦은 경사로에 깐다. 선은 같은 이름 길 전체를 그린 근사 — 실제 깔린 구간은 원문 위치.</p>'; src2 = Sd.source.heat; }
    else if (k === 'advb') { var a = it.a.a; h = '<h3>❄ 제설 ' + esc(a[3]) + '기지 ' + esc(a[2]) + '</h3>' + row('자리', esc(a[4])) + row('관리', esc(a[5])); src2 = Sd.source.adv; }
    else if (k === 'pbtn') { var pb = it.b.b; h = '<h3>🚸 보행자작동신호기</h3>' + row('버튼', pb[2] + '개(30m 안 묶음)') + row('관리번호', esc(pb[3] || '-')) + (pb[4] ? row('설치일', esc(pb[4])) : '') +
        '<p class="desc">보행자가 버튼을 눌러야 보행 신호가 켜지는 곳 — 누르지 않으면 차량 신호가 이어진다(무단횡단 유혹 · 어르신·어린이 안내 자리).</p>'; src2 = D.pbtn.source; }
    return h + src(src2); }
  function seasonLegend(G) { if (!SEA) return; var Sd = D.season, b = '';
    if (on.flt) b += li('#1e3a8a', '침수 흔적 — 깊이 1m 넘음', 'box') + li('#2563eb', '0.5~1m') + li('#60a5fa', '얕음·기록 없음');
    if (on.flr) b += li(FR_C[1], '침수 이력 도로(30m 안 흔적) 1해', 'line') + li(FR_C[2], '2해', 'line') + li(FR_C[3], '3해 넘음', 'line');
    if (on.und) b += li('#b91c1c', '지하차도 — 150m 안 침수 흔적 있음', 'box') + li('#475569', '지하차도', 'box');
    if (on.ice) b += li('#06b6d4', '제설함(결빙 우려 자리)');
    if (on.hcab) b += li('#f97316', '도로 열선 길', 'line');
    if (on.advb) b += li('#0e7490', '제설 전진기지');
    if (on.pbtn) b += li('#16a34a', '보행자작동신호기');
    if (!b) return; var si = seasonInfo();
    G(si.icon + ' 계절 위험 · ' + esc(si.name), b + '<small class="lg-n">침수흔적 2010~2025(' + Sd.years.join('·') + ') · 자연재해위험개선지구: ' + Sd.danger.map(function (d) { return esc(d.DSTRCT_NM + '(' + d.PSTN + ')'); }).join(', ') + '</small>'); }
  function drawSafe(dark) {
    SAFE.forEach(function (L) { if (!on[L[0]]) return; var dense = L[3].length > 300, small = dense && view.s < 0.25; if ((L[0] === 'fw' && view.s < 0.18) || (L[0] === 'glamp' && view.s < 0.1)) return;
      L[3].forEach(function (q) { var c = L[0] === 'govr' ? (GOVC[q.r[3]] || L[2]) : L[0].indexOf('sr') === 0 && L[0] !== 'srsvc' ? (SRC_C[q.r[2]] || L[2]) : L[2]; dot(q.p, small ? 2.4 : 4.2, c, small ? null : '#fff', small ? null : { kind: 'safe', L: L, q: q }); }); });
  }
  function facCard(it) {
    var k = it.L[0], r = it.q.r, S = (it.q.m || {}).source || {}, h = '<h3>' + esc(FACL[k][0]) + '</h3>', s = '';
    if (k === 'kyr' && r[4] === 'OSM') { h += row('이름', esc(r[2])) + row('자리', '<em>OpenStreetMap 의 경로당 점 — 경기 경로당은 공식 좌표 목록을 찾지 못해 OSM 에 있는 곳만</em>'); s = S['경기 경로당']; }
    else if (k === 'kyr') { h += row('이름', esc(r[2])) + row('주소', esc(r[3])) + row('자리', r[4] === '이름' ? '<em>OpenStreetMap 의 같은 이름 경로당 점(근사)</em>' : r[4] === '근사' ? '<em>같은 길의 가장 가까운 번호 자리(근사 — 이 방법을 시험해 보니 오차 가운데 약 40m · 열에 아홉은 125m 안)</em>' : '<em>OpenStreetMap 건물 도로명주소와 맞춘 자리</em>'); s = S['경로당']; }
    else if (k === 'cc') { h += row('이름', esc(r[2])) + row('유형', esc(r[3])) + (r[5] == null ? row('정원', r[4] + '명') : row('정원 · 현원', r[4] + '명 · ' + r[5] + '명' + (r[4] ? ' <em>(채운 비율 ' + Math.round(r[5] / r[4] * 100) + '%)</em>' : ''))); s = r[5] == null ? S['경기 어린이집'] : S['어린이집']; }
    else if (k === 'kg') { h += row('이름', esc(r[2])) + row('설립', esc(r[3])) + (r[4] ? row('자리', '<em>' + (r[4] === 'OSM' ? 'OpenStreetMap 의 같은 이름 점' : r[4] === '병설 학교' ? '병설된 학교 자리' : '어린이보호구역 대상 시설(표준데이터)의 같은 이름 점') + '</em>') : ''); s = r[4] ? S['경기 유치원'] : S['유치원·학교']; }
    else if (k === 'govr') { h += row('이름', esc(r[2])) + row('갈래', '<span style="color:' + (GOVC[r[3]] || '#333') + ';font-weight:800">●</span> ' + esc(r[3])) + (r[4] ? row('주소', esc(r[4])) : '') + (r[5] ? row('전화', '<a href="tel:' + esc(r[5]) + '">' + esc(r[5]) + '</a>') : '') + '<p class="desc">OpenStreetMap 에 있는 곳이다 — 이름·자리는 실제와 다를 수 있고, 없는 곳도 있다.</p>'; s = S['관공서']; }
    else if (k === 'edu') { h += row('이름', esc(r[2])) + row('갈래', esc(({ '초': '초등학교', '중': '중학교', '고': '고등학교', '대학': '대학', '기타': '특수·기타 학교' })[r[3]] || r[3])) + row('자리', '<em>' + esc(r[4] === '교육청' ? '서울특별시교육청 학교 위치(2025)' : r[4] === '보호구역' ? '어린이보호구역 대상 시설(표준데이터)' : 'OpenStreetMap(학교 이름으로 갈래)') + '</em>'); s = S['학교']; }
    else if (k === 'aca') { h += row('상호', esc(r[2])) + '<p class="desc">등록된 상가 정보다 — 영업 여부·수강생 수는 이 자료에 없다.</p>'; s = S['학원']; }
    return h + src(s);
  }
  function pyr(m, f) { var mx = Math.max.apply(null, m.concat(f)) || 1, L = ageLab(m.length), o = '<div class="pyr"><div class="hd"><span class="l">남</span><b></b><span class="r">여</span></div>';
    for (var i = m.length - 1; i >= 0; i--) o += '<div><span class="l"><small>' + m[i].toLocaleString() + '</small><i style="width:' + Math.round(m[i] / mx * 70) + '%"></i></span><b>' + L[i] + '</b><span class="r"><i style="width:' + Math.round(f[i] / mx * 70) + '%"></i><small>' + f[i].toLocaleString() + '</small></span></div>';
    return o + '</div>'; }
  var IXC = { LH: '#16a34a', LL: '#f59e0b', HL: '#dc2626', HH: '#94a3b8' };
  function pctCh(a, b) { return a ? Math.round((b - a) / a * 100) : null; }
  function sgn(v) { return v == null ? '-' : (v > 0 ? '+' : '') + v + '%'; }
  function facRows(gcd, nm, k8) {   // 동 카드 아래 「동 현황」 — 소유자 2026-10-04 「상권이 살아나는지 죽는지 · 남녀 · 경로당·어린이집·유치원·입시학원」
    var F = RFAC[gcd]; if (!F) { fLoad(gcd, function () { if (sel && $('m2dCard').classList.contains('on')) show(sel.it); }); return '<p class="desc">동 현황(남녀·시설·상권 추이)을 읽는 중…</p>'; }
    var x = (k8 && F.dong[k8]) || null; if (!x) for (var kk in F.dong) if (F.dong[kk].name === nm) { x = F.dong[kk]; break; } if (!x) return '';
    var S = F.source || {}, h = '<div class="dh">📋 동 현황</div>', srcs = [];
    if (x.sex) { var m = x.sex[0], f = x.sex[1]; h += row('남녀', '남 ' + m.toLocaleString() + '(' + Math.round(m / (m + f) * 100) + '%) · 여 ' + f.toLocaleString() + '(' + Math.round(f / (m + f) * 100) + '%) <em>· 여자 100명당 남자 ' + Math.round(m / f * 100) + '명</em>') +
      '<div class="cap">연령대별 남녀 인구(명 · 주민등록 2026년 9월 · 위가 나이 많음)</div>' + pyr(x.sex[2], x.sex[3]); srcs.push(S['남녀']); }
    var fl = []; if (x.cc) fl.push('어린이집 ' + x.cc[0] + '곳(정원 ' + x.cc[1] + (x.cc[2] >= 0 ? ' · 현원 ' + x.cc[2] : '') + ')'); if (x.kgy) fl.push('유치원 ' + x.kgy[x.kgy.length - 1] + '곳'); else if (x.kgN) fl.push('유치원 ' + x.kgN + '곳');
    var E = x.edu || {}; if (x.edu || x.sch) fl.push('초 ' + (E['초'] != null ? E['초'] : (x.sch || {}).e || 0) + ' · 중 ' + (E['중'] != null ? E['중'] : (x.sch || {}).m || 0) + ' · 고 ' + (E['고'] != null ? E['고'] : (x.sch || {}).h || 0) + (E['대학'] ? ' · 대학 ' + E['대학'] : '') + (E['기타'] ? ' · 특수·기타 ' + E['기타'] : '')); if (x.kyr) fl.push('경로당 ' + x.kyr + '곳'); if (x.aca != null || x.acaAll) fl.push('입시·교과학원 ' + (x.aca || 0) + '곳(학원 전체 ' + (x.acaAll || 0) + ')');
    if (fl.length) h += row('아이·어르신·교육', fl.join(' · ') + (F.sido === '41' ? ' <em>(경기: 경로당은 OSM 에 있는 곳만 · 유치원은 이름으로 자리를 잡은 곳만(경기 전체 1,771곳 중 ' + (F.kgNo || 0) + '곳은 자리를 못 잡아 빠짐) · 학교는 OSM·어린이보호구역 자료)</em>' : x.kyr && F.kyrNo ? ' <em>(경로당은 주소로 자리를 잡은 곳만 — 이 구 ' + F.kyrNo + '곳 빠짐)</em>' : ''));
    if (x.ccy && x.ccy.some(function (v) { return v; })) { var c0 = x.ccy[0], c1 = x.ccy[x.ccy.length - 1];
      h += row('어린이집 추이', F.cyears[0] + '년 ' + c0 + '곳 → ' + F.cyears[F.cyears.length - 1] + '년 ' + c1 + '곳 <b>' + sgn(pctCh(c0, c1)) + '</b>') + '<div class="cap">해마다 운영 중인 어린이집 수(곳 · 그해 말 · 인가일~폐지일로 셈 · ' + F.cyears[F.cyears.length - 1] + '년은 ' + (F.sido === '41' ? '자료 기준일 2025.7' : '지금') + ')</div>' + bar(x.ccy, '#db2777', F.cyears.map(function (y) { return "'" + String(y).slice(2); })); srcs.push(F.sido === '41' ? S['경기 어린이집'] : S['어린이집']); }
    if (x.kgy && x.kgy.some(function (v) { return v; })) { var g0 = x.kgy[0], g1 = x.kgy[x.kgy.length - 1];
      h += row('유치원 추이', F.kyears[0] + '년 ' + g0 + '곳 → ' + F.kyears[F.kyears.length - 1] + '년 ' + g1 + '곳 <b>' + sgn(pctCh(g0, g1)) + '</b>') + '<div class="cap">해마다 유치원 수(곳 · 서울시교육청 · ' + F.kyears[0] + '~' + F.kyears[F.kyears.length - 1] + ')</div>' + bar(x.kgy, '#d97706', F.kyears.map(function (y) { return "'" + String(y).slice(2); })); srcs.push(S['유치원·학교']); }
    if (x.gov) { var GO = Object.keys(x.gov).sort(function (a, b) { return x.gov[b] - x.gov[a]; }); h += row('관공서', GO.map(function (k) { return esc(k) + ' ' + x.gov[k]; }).join(' · ') + ' <em>(OSM)</em>'); }
    if (x.gcs && x.gcs.m.length) { var g2 = x.gcs, ch = pctCh(g2.h22, g2.h25); srcs.push(S['경기 카드매출']);
      h += '<div class="dh">💳 카드 매출 — 경기도 카드사 집계</div>' + row('같은 1~6월 월평균', won(g2.h22) + ' (2022) → <b>' + won(g2.h25) + '</b> (2025) <b>' + sgn(ch) + '</b>') + (g2.bar ? row('주점·유흥(2025 월평균)', won(g2.bar)) : '') +
        '<div class="lst">' + g2.ind.slice(0, 8).map(function (t) { var c = pctCh(t[2], t[1]), mm = String(t[0]).match(/^(소매\/유통|생활서비스|여가\/오락|음식|학문\/교육|의료\/건강|공연\/전시|미디어\/통신|공공\/기업\/단체)\/(.+)$/) || [0, '', t[0]]; return '<div><b>' + esc(mm[2]) + '</b> <small>' + esc(mm[1]) + '</small><span class="' + (c == null ? '' : c > 10 ? 'up' : c < -10 ? 'dn' : '') + '">' + won(t[1]) + ' ' + sgn(c) + '</span></div>'; }).join('') + '</div>' +
        '<div class="cap">달마다 카드 매출(만원 · 같은 기준인 달만 — 빈 달은 자료 없음 · 2022.1~2025.6)</div>' + bar(g2.m.map(function (q) { return q[1]; }), '#7c3aed', g2.m.map(function (q) { return q[0].slice(4) === '01' ? "'" + q[0].slice(2, 4) : ''; }), 'w') +
        row('한 줄로', (ch == null ? '➡ 판단 못 함' : ch > 10 ? '📈 <b>매출이 늘어나는 쪽</b>' : ch < -10 ? '📉 <b>매출이 줄어드는 쪽</b>' : '➡ 큰 변화 없음') + ' <em>(같은 1~6월 월평균 ±10% · 물가 반영 안 함 · 설계값)</em>') +
        '<p class="desc">경기 카드 매출은 <b>카드사 집계</b>라 실제 전체 매출보다 작고, 2018~2021년 자료는 기준이 달라(규모가 몇 배 차이) 이어 붙이지 않았다. 경기 생활인구(동·시간대)는 공개 자료가 표본뿐이라 넣지 않았다.</p>'; }
    if (x.ix || x.st || x.trd) {
      h += '<div class="dh">🏪 상권 — 살아나는가, 줄어드는가</div>'; var sales = null, stores = null, ixl = null;
      if (x.st && x.st.length > 4) { var s0 = x.st[0], s1 = x.st[x.st.length - 1], op = 0, cl = 0; x.st.forEach(function (q) { op += q[2]; cl += q[3]; }); stores = pctCh(s0[1], s1[1]);
        h += row('점포(업종 합)', s0[1].toLocaleString() + ' → ' + s1[1].toLocaleString() + '곳 <b>' + sgn(stores) + '</b> <em>(' + s0[0].slice(2, 4) + '년 ' + s0[0][4] + '분기 → ' + s1[0].slice(2, 4) + '년 ' + s1[0][4] + '분기)</em>') + row('분기마다', '개업 평균 ' + Math.round(op / x.st.length) + ' · 폐업 평균 ' + Math.round(cl / x.st.length) + '곳') +
          '<div class="cap">분기마다 점포 수(곳 · 상권분석서비스 업종 합 · 행정동)</div>' + bar(x.st.map(function (q) { return q[1]; }), '#7c3aed', qLab(x.st.map(function (q) { return q[0]; }))); srcs.push(S['점포']); }
      if (x.trd && x.trd.length) { var A0 = 0, A1 = 0; x.trd.forEach(function (t) { A0 += t[4]; A1 += t[3]; }); sales = pctCh(A0, A1);
        h += row('이 동의 상권', x.trd.length + '곳 · 최근 1년 매출 약 ' + won(A1) + ' <b>' + sgn(sales) + '</b> <em>(처음 1년 ' + won(A0) + ' · 2021년부터)</em>') +
          '<div class="lst">' + x.trd.slice(0, 6).map(function (t) { var c = pctCh(t[4], t[3]); return '<div><b>' + esc(t[1]) + '</b> <small>' + esc(t[2]) + ' · ' + esc(t[5] || '') + '</small><span class="' + (c == null ? '' : c > 10 ? 'up' : c < -10 ? 'dn' : '') + '">' + won(t[3]) + ' ' + sgn(c) + '</span></div>'; }).join('') + '</div>'; }
      if (x.ix && x.ix.length) { var last = x.ix[x.ix.length - 1], N = F.ix_names || {}; ixl = last[1];
        h += row('상권변화지표', '<b>' + esc(N[last[1]] || last[1]) + '</b> <em>(' + last[0].slice(2, 4) + '년 ' + last[0][4] + '분기 · 운영 평균 ' + Math.round(last[2]) + '개월 · 폐업 평균 ' + Math.round(last[3]) + '개월)</em>') +
          '<div class="cap">분기마다 상권변화지표(' + x.ix[0][0].slice(0, 4) + '~' + last[0].slice(0, 4) + ')</div><div class="ixs">' + x.ix.map(function (q) { return '<i style="background:' + (IXC[q[1]] || '#ccc') + '" title="' + q[0].slice(0, 4) + '년 ' + q[0][4] + '분기 ' + esc(N[q[1]] || q[1]) + '"></i>'; }).join('') + '</div>' +
          '<div class="ixl"><span><i style="background:#16a34a"></i>상권확장 — 새로 연 점포가 버틴다</span><span><i style="background:#f59e0b"></i>다이나믹 — 많이 열고 많이 닫는다</span><span><i style="background:#94a3b8"></i>정체 — 오래된 점포가 그대로</span><span><i style="background:#dc2626"></i>상권축소 — 새로 연 곳이 빨리 닫는다</span></div>'; srcs.push(S['상권변화']); }
      var up = (sales != null && sales > 10) + (stores != null && stores > 3) + (ixl === 'LH'), dn = (sales != null && sales < -10) + (stores != null && stores < -3) + (ixl === 'HL');
      var vd = up >= 2 && !dn ? '📈 <b>살아나는 쪽</b>' : dn >= 2 && !up ? '📉 <b>줄어드는 쪽</b>' : up > dn ? '↗ 조금 살아나는 쪽' : dn > up ? '↘ 조금 줄어드는 쪽' : '➡ 큰 변화 없음';
      h += row('한 줄로', vd + ' <em>(매출 ±10% · 점포 ±3% · 지표를 함께 본 이 지도의 어림 — 판단 문턱은 설계값)</em>') + '<p class="desc">상권분석서비스는 <b>2021년부터</b>만 공개된다 — 그보다 앞 10년 상권 값은 이 자료에 없다. 어린이집(2016~)·유치원(2014~)은 더 길게 본다.</p>';
    }
    if (x.bz && x.bz.length) {   // v1.3.0 동별 사업체 10년(KOSIS · 통계청 전국사업체조사)
      var B0 = x.bz.filter(function (q) { return q[1] != null; }), b0 = B0[0], b1 = B0[B0.length - 1];
      var bN = B0.filter(function (q) { return +q[0] >= 2020; }), n0 = bN[0];
      if (b0 && b1) { var bc = n0 ? pctCh(n0[1], b1[1]) : pctCh(b0[1], b1[1]), wc = n0 ? pctCh(n0[2], b1[2]) : pctCh(b0[2], b1[2]);
        h += '<div class="dh">🏢 사업체 10년 — 상권이 커지는가 줄어드는가(' + b0[0] + '~' + b1[0] + ')</div>' +
          row('사업체', (n0 ? n0[1].toLocaleString() + '(2020) → <b>' : b0[1].toLocaleString() + ' → <b>') + b1[1].toLocaleString() + '곳</b> (' + b1[0] + ') <b>' + sgn(bc) + '</b> <em>· ' + b0[0] + '년 ' + b0[1].toLocaleString() + '곳</em>') + row('종사자', (n0 ? (n0[2] || 0).toLocaleString() + '(2020) → <b>' : (b0[2] || 0).toLocaleString() + ' → <b>') + (b1[2] || 0).toLocaleString() + '명</b> <b>' + sgn(wc) + '</b>') +
          '<div class="cap">해마다 사업체 수(곳 · 통계청 전국사업체조사 · 동별 · ' + b0[0] + '~' + b1[0] + ')</div>' + bar(B0.map(function (q) { return q[1]; }), '#0f766e', B0.map(function (q) { return "'" + String(q[0]).slice(2); })) +
          '<div class="cap">해마다 종사자 수(명)</div>' + bar(B0.map(function (q) { return q[2] || 0; }), '#14b8a6', B0.map(function (q) { return "'" + String(q[0]).slice(2); }));
        if (x.bzi && x.bzi.length) h += '<div class="cap">업종 대분류별 사업체 ' + x.bziy[0] + ' → ' + x.bziy[1] + '(많은 업종 8)</div><div class="lst">' + x.bzi.slice(0, 8).map(function (t) { var c = pctCh(t[1], t[2]); return '<div><b>' + esc(t[0]) + '</b><span class="' + (c == null ? '' : c > 10 ? 'up' : c < -10 ? 'dn' : '') + '">' + (t[1] == null ? '-' : t[1].toLocaleString()) + ' → ' + (t[2] == null ? '-' : t[2].toLocaleString()) + ' ' + sgn(c) + '</span></div>'; }).join('') + '</div>';
        h += row('한 줄로', (bc == null ? '➡ 판단 못 함' : bc > 10 ? '📈 <b>사업체가 늘어난 동</b>' : bc < -10 ? '📉 <b>사업체가 줄어든 동</b>' : '➡ 큰 변화 없음') + ' <em>(같은 조사 방식인 2020년부터 견줌 · ±10% · 설계값)</em>') +
          '<p class="desc">통계청 전국사업체조사(종사자 1명 이상 모든 사업체 — 상가만이 아니라 사무실·공장·학교 등도 든다) · 해마다 그해 12월 31일 기준. <b>2020년부터 조사 방식이 행정자료 중심으로 바뀌어 사업체 수가 크게 뛴다</b> — 2019년 이전과 2020년 이후를 곧바로 견주지 말 것(그래서 늘었다·줄었다 판단은 2020년부터만 본다).</p>';
        srcs.push(F.bzsrc); } }
    return h + src(srcs.filter(function (v, i, a) { return v && a.indexOf(v) === i; }).join(' · '));
  }
  function safeCard(it) {
    if (FACL[it.L[0]]) return facCard(it);
    var k = it.L[0], r = it.q.r, Sx = D.safety, C = Sx.codes || {}, h = '<h3>' + esc(it.L[1]) + '</h3>', s = '';
    if (k.indexOf('sr') === 0 && k !== 'srsvc') { h += row('시설', esc((C.srItem || {})[r[2]] || r[2]) + (r[5] > 1 ? ' ' + r[5] + '개' : '')) + row('안심귀갓길', esc(r[3] + ' · ' + r[4])) + (r[6] ? row('비고', esc(r[6])) : '') + (r[7] ? row('관리', esc(r[7] + ' ' + (r[8] || ''))) : ''); s = Sx.source.srItem + ' · 코드: ' + C.srItemSrc; }
    else if (k === 'srsvc') { h += row('이름', esc(r[3])) + row('구분', esc((C.srSvc || {})[r[2]] || r[2])) + row('주소', esc(r[4])) + row('운영', esc(String(r[7] || '').replace('_', '~'))) + row('관리', esc(r[5] + ' ' + (r[6] || ''))); s = Sx.source.srSvc; }
    else if (k === 'aed') { h += row('기관', esc(r[2])) + row('설치 자리', esc(r[3])) + row('주소', esc(r[4])) + (r[5] ? row('전화', esc(r[5])) : ''); s = /^경기/.test(r[4] || '') ? SRCX.aed : Sx.source.aed; }
    else if (k === 'fw') { var st = typeof r[4] === 'string' ? [r[4], ''] : (Sx.items.fireSt || [])[r[4]] || []; h += row('종류 코드', esc(r[2])) + row('사용', r[3] ? '가능' : '<b>불가·점검</b>') + row('관할 소방서', esc((st[0] || '') + ' ' + (st[1] || ''))); s = Sx.source.fire; }
    else if (k === 'pkcctv') { h += row('단속 지점', esc(r[2])) + row('주소', esc(r[3])) + row('구분', esc(r[4])); s = Sx.source.pkcctv; }
    else if (k === 'tow') { h += row('이름', esc(r[2])) + row('주소', esc(r[3])) + row('전화', esc(r[4])) + row('보관', esc(r[5]) + '대') + '<p class="desc">' + esc(r[6]) + '</p>'; s = Sx.source.tow; }
    else if (k === 'wc2') { h += row('이름', esc(r[2])) + row('주소', esc(r[3])) + row('구분', esc(r[4])) + row('개방', esc(r[5])) + row('남녀', esc(r[6])); s = /^경기/.test(r[3] || '') ? SRCX.wc : Sx.source.wc; }
    else if (k === 'box') { h += row('자리', esc(r[2])) + row('주소', esc(r[3])); s = Sx.source.box; }
    else if (k === 'dem') { h += row('이름', esc(r[2])) + row('주소', esc(r[3])) + row('전화', esc(r[4])) + '<p class="desc">배회·실종 치매 어르신 발견 때 연락.</p>'; s = Sx.source.dem; }
    else if (k === 'gpark') { h += row('이름', esc(r[2])) + row('주소', esc(r[3])) + row('구분', esc(r[4] + ' · ' + r[5])) + row('주차면', esc(r[6]) + '면') + row('평일 운영', esc(r[7])) + row('요금', esc(r[8])) + row('기준일', esc(r[9])); s = SRCX.park; }
    else if (k === 'tlt') { h += row('도로', esc(r[2] || '-')) + row('주소', esc(r[3] || '-')) + row('현시 순서', esc(r[5] || '-')) + row('현시 시간(초)', esc(r[6] || '-') + (r[6] && /\+/.test(r[6]) ? ' <em>(합 ' + String(r[6]).split('+').reduce(function (a, b) { return a + (+b || 0); }, 0) + '초)</em>' : '')) +
      row('잔여시간 표시', r[7] === 'Y' ? '있음' : r[7] === 'N' ? '없음' : '-') + row('음향신호기', r[8] === 'Y' ? '있음' : r[8] === 'N' ? '없음' : '-') + row('신호등 구분 코드', esc(r[4] || '-') + ' <em>(코드 뜻은 표준데이터 정의서 확인 전)</em>') + row('관리', esc(r[9] || '-')) + row('기준일', esc(r[10] || '-')) +
      '<p class="desc">지자체가 공공데이터포털에 올린 신호등 목록이다 — 현시 시간은 등록값이라 실제 운영(감응·시간대별 계획)과 다를 수 있다.</p>'; s = SRCX.tl; }
    else if (k === 'gev') { h += row('충전소', esc(r[2])) + row('주소', esc(r[3])) + row('운영', esc(r[4])) + row('충전기', esc(r[5])); s = SRCX.ev; }
    else if (k === 'ger') { h += row('기관', esc(r[2])) + row('구분', esc(r[3])) + row('주소', esc(r[4])) + row('대표 전화', '<a href="tel:' + esc(r[5]) + '">' + esc(r[5]) + '</a>'); s = SRCX.er; }
    else if (k === 'gfest') { h += row('축제', esc(r[2])) + row('장소', esc(r[3])) + row('기간', esc(r[4]) + ' ~ ' + esc(r[5])) + row('주최·주관', esc(r[6])) + (r[7] ? '<p class="desc">' + esc(r[7]) + '</p>' : '') + row('자료 기준', esc(r[8])); s = SRCX.fest; }
    else if (k === 'bstop') { h += row('이름', esc(r[2] || '(이름 없음)')) + (r[3] ? row('정류장 번호', esc(r[3])) : '') + '<p class="desc">자리·이름만 있다(OSM). 승하차 인원은 서울·경기만 「🚌 버스 승차·하차」 층에 있다.</p>'; s = it.L.src; }
    else if (k === 'glamp') { h += row('설치 연도', esc(r[2] || '-')) + row('설치 형태', esc(r[3] || '-')); s = it.L.src; }
    return h + src(s);
  }
  // ---------- 🗂 범례(v0.10.78 · 소유자 「색으로 구분만 되어 있으면 데이터 전달이 부실 — 범례로 확실하게」) ----------
  function sw(c, kind) { return kind === 'line' ? '<i class="lg-l" style="background:' + c + '"></i>' : kind === 'dash' ? '<i class="lg-l lg-d" style="border-color:' + c + '"></i>' : kind === 'box' ? '<i class="lg-b" style="background:' + c + '"></i>' : '<i class="lg-c" style="background:' + c + '"></i>'; }
  function li(c, t, kind) { return '<span>' + sw(c, kind) + esc(t) + '</span>'; }
  function grad(c0, c1, a, b) { return '<span class="lg-g"><i style="background:linear-gradient(90deg,' + c0 + ',' + c1 + ')"></i><small>' + esc(a) + '</small><small>' + esc(b) + '</small></span>'; }
  var POLL = [];   // 시설 층(이름 · 색 · 설명) — 아래 공공시설 층이 채운다
  function legend() {
    var el = $('m2dLeg'); if (!el) return; var g = [], hh = nowH();
    function G(t, body) { g.push('<div class="lg"><b>' + t + '</b><div>' + body + '</div></div>'); }
    if (on.jcnm) G('🏷 교차로·도로 이름', li('#7c2d12', '큰길 교차로', 'dot') + li('#334155', '그 밖 교차로', 'dot') + li('#0f766e', 'IC·연결로', 'dot') + li('#6b21a8', '교량·터널 끝', 'dot') + li('#1e3a8a', '도로 이름(글자)', 'line') + '<small class="lg-n">국가교통정보센터 전국 표준노드링크(2026-09-14판) · 서울·경기 교차로 2.5만 곳 · 확대할수록 작은 교차로·길 이름까지 · 「찾기」에 교차로·도로 이름을 넣어도 된다</small>');
    if (on.road && OSM) G('🛣 도로', li('#f9c56b', '고속·도시고속', 'line') + li('#ffe08a', '주간선', 'line') + li('#fff2c2', '보조간선', 'line') + li('#ffffff', '집산·국지', 'line') + li('#a0a9b6', '보행', 'dash') + li('#22a35a', '자전거', 'dash') + li('#8b95a3', '지하차도(점선)', 'dash') + li('#334155', '교차로 이름(점)'));
    if (on.base && OSM) G('🗺 바탕', li('#a8d0f0', '물', 'box') + li('#cfe6bd', '공원·녹지', 'box') + li('#b9dba3', '숲', 'box') + li('#8b95a3', '철도', 'line') + li('#bab0a4', '건물', 'box'));
    if (on.jiga) G('🟧 공시지가·지목', '<div class="lg-btns">' + Object.keys(JGMS).map(function (k) { return '<button data-jgm="' + k + '" class="' + (k === JGM ? 'on' : '') + '">' + JGMS[k][0] + '</button>'; }).join('') + '</div>' + (JGM !== 'p' ? li(hexA(JGMS[JGM][2], 0.7), '진할수록 ' + JGMS[JGM][0].replace(/^\S+ /, '') + ' 높음(0→100%)', 'box') + '<small class="lg-n">지목 넓이 비율 — 필지를 대표점이 든 칸·동에 통째로 넣은 근사 · 지목 이름은 측량·지적법 그대로</small>' : JGC.map(function (c, i) { return li(hexA(c, 0.75), JGL[i], 'box'); }).join('') + '<small class="lg-n">가까이 = 250m 칸 · 멀리 = 행정동 · ' + esc(jgYear() || '') + '년 1월 1일 · 세금·보상 기준값이지 시세가 아니다 · 받은 시군구 ' + Object.keys(JIGA).length + '</small>'));
    if (on.fdong) G('🌏 외국인 현황(시군구 · 읍면동)', fdLegend());
    if (on.stay) G('🛏 숙박시설', '<div class="lg-btns">' + STY.map(function (t, i) { return '<button data-sty="' + i + '" class="' + (STYON[i] ? 'on' : '') + '"><i style="display:inline-block;width:9px;height:9px;border-radius:50%;background:' + t[2] + ';margin-right:4px"></i>' + t[1] + '</button>'; }).join('') + '</div><small class="lg-n">회색 = 휴업 · 영문 상호가 있는 곳은 테가 굵다 · 행정안전부 지방행정인허가(2025-11-27) · 투숙 인원·국적·등록 안 한 숙소는 공개되지 않는다</small>');
    if (on.land) G('📐 필지(브이월드)', li('#f59e0b', '누른 필지', 'line') + li('#facc15', '지적선(많이 확대하면)', 'line') + '<div class="lg-btns"><button data-landuq="1" class="' + (LAND.uq ? 'on' : '') + '">🎨 용도지역 색 ' + (LAND.uq ? '끄기' : '켜기') + '</button><button data-vwkey="1">🔑 ' + (VWKEY ? '키 바꾸기' : '키 넣기') + '</button></div>' + (LAND.uq ? '<small class="lg-n">도시지역(주거·상업·공업·녹지) · 관리지역(계획·생산·보전) · 농림지역 · 자연환경보전지역 — 색은 국토교통부 브이월드 도시계획 지도 그대로(대략: 노랑·주황 주거 · 분홍 상업 · 보라 공업 · 연두·초록 녹지·관리·농림 · 빗금 = 지구·구역). <b>정확한 이름은 「📐 필지」로 눌러 「용도지역 · 토지이용계획」</b></small>' : '') + (VWKEY ? '' : '<small class="lg-n" style="color:#b91c1c">브이월드 키가 있어야 받는다 — 「🔑 키 넣기」(이 기기에만)</small>'));
    if (on.govr) G('🏛 관공서', Object.keys(GOVC).map(function (k) { return li(GOVC[k], k); }).join(''));
    if (on.juris) { var jl2 = jrsLegend(); if (jl2) G(jl2[0], jl2[1]); }
    if (on.dong) G('🏘 행정동', li('rgba(109,40,217,.6)', '행정동 경계', 'line') + li('#64748b', '이웃 구 동(점선)', 'dash') + li('#475569', '구 경계(굵은 점선)', 'dash'));
    if (on.live) { var mx = 0, mn = 1e9; allDong().forEach(function (d) { var lv = liveNow(d); if (lv) { mx = Math.max(mx, lv.n); mn = Math.min(mn, lv.n); } }); if (mx) G('👥 생활인구 ' + hh + '시', grad('rgb(255,230,150)', 'rgb(215,60,40)', man(mn) + '명', man(mx) + '명') + '<small class="lg-n">동 안의 숫자 = 그 시각 평균 체류 인구</small>'); }
    if (on.sales) { var a = 1e18, b = 0; allDong().forEach(function (d) { var sn = salesNow(d); if (sn) { a = Math.min(a, sn.perH); b = Math.max(b, sn.perH); } }); if (b) G('💳 카드 매출 ' + esc(D.flow.sales.tb[bandOf(hh)]), grad('rgb(237,233,254)', 'rgb(117,53,214)', won(a), won(b)) + '<small class="lg-n">시간당 추정 매출(하루 평균) · 동을 누르면 업종·연령</small>'); }
    if (typeof trdLegend === 'function') { var tl = trdLegend(); if (tl) G(tl[0], tl[1]); }
    var jl = jggLegend(); if (jl) G(jl[0], jl[1]);
    var vl = vwLegend(); if (vl) G(vl[0], vl[1]);
    var ll2 = liveLegend(); if (ll2) G(ll2[0], ll2[1]);
    if (on.szone) G('🏬 소진공 주요상권', li('#b45309', '주황 점선 = 소상공인시장진흥공단이 정한 주요상권 경계(2024.1 · 서울 176 · 경기 281)', 'line') + '<small class="lg-n">누르면 영역 안 등록 점포 · 업종 · 1층 비율</small>');
    if (typeof a10Legend === 'function') { var al = a10Legend(); if (al) G(al[0], al[1]); }
    gridLegend().forEach(function (q) { G(q[0], q[1]); }); var hl = homeLegend(); if (hl) G(hl[0], hl[1]);
    if (on.bus || on.subr) G('🚌🚇 ' + hh + '시 승하차', li('rgba(37,99,235,.8)', '타는 사람 많음(떠나는 곳)') + li('rgba(234,88,12,.8)', '내리는 사람 많음(모여드는 곳)') + li('rgba(13,148,136,.8)', '비슷') + '<small class="lg-n">원 크기 = 그 시각 승차+하차(하루 평균) · 지하철 옆 숫자 = 그 시각 승하차</small>');
    if (on.crowd) G('📡 실시간 인파', li(LVC['여유'], '여유') + li(LVC['보통'], '보통') + li(LVC['약간 붐빔'], '약간 붐빔') + li(LVC['붐빔'], '붐빔') + li('#64748b', '실선 지금 · 긴 점선 예측 · 회색 점선 받은 때', 'dash') + '<small class="lg-n">받은 시각 ' + esc(String((D.livep || {}).baked || '')) + '</small>');
    if (on.spd) G('🚥 도로 소통(받은 때)', li(IDXC['원활'], '원활', 'line') + li(IDXC['서행'], '서행', 'line') + li(IDXC['정체'], '정체', 'line'));
    if (on.jur) G('🚓 관할', li('#2563eb', '서울서초경찰서', 'box') + li('#0d9488', '서울방배경찰서', 'box') + li('#b45309', '반포4동 반포대로 경계', 'dash') +
      JUR.filter(function (J) { return J.z.near; }).map(function (J) { return li(JUR_C[J.z.id] ? JUR_C[J.z.id][1] : '#64748b', J.z.name.replace('서울', '') + '(별표2 · 행정동 근사)', 'box'); }).join('') + '<small class="lg-n">경계·청사를 누르면 단속 5개 해·112 출동·5대 범죄</small>');
    if (on.acc) G('🚗 교차로 사고 ' + (A10.length ? '2019~2025' : '2023~25'), li('rgba(234,88,12,.6)', '원 크기 = √사고 건수 · 아래 숫자 = 건수·사망') + li('rgba(220,38,38,.7)', '사망 포함') + '<small class="lg-n">585m 안 사고를 가장 가까운 교차로에 배정(근사) · 카드에 해마다 막대</small>');
    if (on.hot10) G('🗂 다발지 10년', Object.keys(H10C).map(function (k) { return li(H10C[k], k); }).join('') + '<small class="lg-n">원 크기 = 뽑힌 횟수 · 아래 숫자 = 횟수·해</small>');
    if (on.fatal) G('🕯 사망사고', li('#111827', '한 건씩(2020~2025)') + '<small class="lg-n">' + (on.fatal10 ? '「사망사고 10년」과 같은 자료라 10년 층이 그린다(한 사고 한 점)' : '「사망사고 10년」 자료의 최근 6년') + '</small>');
    if (on.hot) G('⚠ 사고다발지', li('rgba(250,204,21,.9)', 'TAAS 공표 다발지'));
    if (on.drunk || on.risk) G('🟥 구역', (on.drunk ? li('rgba(126,34,206,.5)', '음주 사고 다발지', 'box') : '') + (on.risk ? li('rgba(185,28,28,.5)', '사고위험지역', 'box') : ''));
    if (on.sz) G('🏫 어린이보호구역', li('#eab308', '초등학교') + li('#f97316', '유치원') + li('#fb923c', '어린이집') + li('#a855f7', '특수학교'));
    if (on.tgis) G('🚥 T-GIS 신호', li('#1d4ed8', '서초서 관할') + li('#0d9488', '방배서 관할') + li('#f59e0b', '주황 테 = 딸린 신호(선 = 부모)'));
    if (on.pol) G('👮 경찰', li('#1e3a8a', '경찰서') + li('#2563eb', '지구대·파출소') + li('#93c5fd', '자리 근사') + li('#0f766e', '치안센터'));
    if (on.phar) G('💊 약국', li('#16a34a', '지금 영업 중') + li('#94a3b8', '닫음·모름'));
    if (on.er || on.hosp) G('🏥 의료', (on.er ? li('#dc2626', '응급실') : '') + (on.hosp ? li('#0891b2', '병원·의원') : ''));
    if (on.bar || on.play || on.inn) G('🌙 밤 순찰', (on.bar ? li('#b45309', '주점') : '') + (on.play ? li('#db2777', '노래방·PC방') : '') + (on.inn ? li('#7c3aed', '숙박') : ''));
    if (on.evt) G('📅 행사·집회', li('#a855f7', '문화행사') + li('#ef4444', '집회(선 = 행진)'));
    seasonLegend(G);
    if (on.cam || on.sig) G('📷🚦', (on.cam ? li('#2563eb', '무인 단속 카메라') + (A10.length ? li('#16a34a', '설치 뒤 둘레 사고가 서초 전체보다 더 줄었다') + li('#dc2626', '덜 줄었거나 늘었다') : '') + camSum() : '') + (on.sig ? li('#16a34a', '신호 주기(경찰청)') : ''));
    if (on.spot) G('🎯 길목', li('rgba(234,88,12,.5)', '버스 정류장') + li('rgba(14,165,233,.5)', '지하철역') + '<small class="lg-n">숫자 = 그 시각 하차 순위</small>');
    POLL.forEach(function (L) { if (on[L[0]]) G(L[1], li(L[2], L[3])); });
    var oth = Object.keys(FAC_C).filter(function (k) { return on[k] && k !== 'pol'; }); if (oth.length) G('📍 시설', oth.map(function (k) { return li(FAC_C[k], (LAYERS.filter(function (l) { return l[0] === k; })[0] || [0, k])[1].replace(/^\S+ /, '')); }).join(''));
    el.innerHTML = '<div class="lgh"><b>🗂 범례</b><button id="m2dLegX" aria-label="범례 닫기">닫기</button></div>' + (g.join('') || '<small>켠 층이 없다</small>');
    $('m2dLegX').onclick = function () { legOpen(false); };
  }
  if ($('m2dLeg')) { $('m2dLeg').addEventListener('click', function (e) { if (e.target.closest('[data-bizopen]')) { if (TRDI && BIZ.idx) { var c = BIZ.idx.inds.filter(function (x) { return x[1] === TRDI; })[0]; if (c && c[0] !== BIZ.code) { BIZ.code = c[0]; bizOpen(); bizLoad(); return; } } bizOpen(); return; } var b = e.target.closest('[data-trdm]'); if (b) { TRDM = b.getAttribute('data-trdm'); draw(); return; } b = e.target.closest('[data-ggm]'); if (b) { GGM = b.getAttribute('data-ggm'); draw(); return; } b = e.target.closest('[data-hlall]'); if (b) { HLALL = !HLALL; draw(); return; } b = e.target.closest('[data-vwkey]'); if (b) { vwSetKey(); return; } b = e.target.closest('[data-lkey]'); if (b) { var lk0 = b.getAttribute('data-lkey'); lkSet(lk0, lk0 === 'dgk' ? '공공데이터포털(data.go.kr) 일반' : '국가교통정보센터(ITS)'); return; } b = e.target.closest('[data-busx]'); if (b) { BUSR = null; draw(); legend(); return; } b = e.target.closest('[data-lre]'); if (b) { liveGo(b.getAttribute('data-lre')); legend(); return; } b = e.target.closest('[data-itst]'); if (b) { LK.itst = b.getAttribute('data-itst'); try { localStorage.setItem('tg_map2d_keys', JSON.stringify(LK)); } catch (e2) {} legend(); return; } b = e.target.closest('[data-vwm]'); if (b) { VWM = b.getAttribute('data-vwm'); try { localStorage.setItem('tg_map2d_vw', VWM); } catch (e2) {} draw(); return; } b = e.target.closest('[data-jggm]'); if (b) { JGGM = b.getAttribute('data-jggm'); draw(); return; } b = e.target.closest('[data-a10m]'); if (b) { A10M = b.getAttribute('data-a10m'); draw(); return; } b = e.target.closest('[data-jrsm]'); if (b) { JRSM = b.getAttribute('data-jrsm'); try { localStorage.setItem('tg_map2d_jrs', JRSM); } catch (e2) {} draw(); legend(); return; } b = e.target.closest('[data-hm]'); if (b) { HM = b.getAttribute('data-hm'); draw(); } });
    $('m2dLeg').addEventListener('change', function (e) { var t = e.target; if (t.hasAttribute('data-trdi')) { TRDI = t.value; draw(); } else if (t.hasAttribute('data-a10y')) { A10Y = t.value ? +t.value : null; draw(); } }); }
  function legOpen(v) { if (v && window.innerWidth < 760 && $('m2dCard').classList.contains('on')) $('m2dCard').classList.remove('on');
    document.body.classList.toggle('legon', v); try { localStorage.setItem('tg_map2d_leg', v ? '1' : '0'); } catch (e) {} if (v) legend(); }
  if ($('m2dLegB')) $('m2dLegB').onclick = function () { legOpen(!document.body.classList.contains('legon')); };
  setTimeout(function () { try { var lv0 = localStorage.getItem('tg_map2d_leg'); legOpen(lv0 == null ? window.innerWidth >= 760 : lv0 === '1'); } catch (e) {} }, 0);
  // ---------- 📋 T-Book 보고 자리(v0.10.59 · 주소 #lat=..&lon=..) ----------
  //  T-Book 최초보고 「발생장소」 단추가 GPS 좌표를 해시로 넘긴다. 해시는 서버로 가지 않고, 이 좌표는 어디에도 저장하지 않는다.
  var REP = null;
  function accOf(n) { return D.acc && D.acc.nodes ? D.acc.nodes.filter(function (x) { return x.node[0] === n.i && x.node[1] === n.j; })[0] : null; }
  function nearestRealNode(p) { var best = null, bd = 1e9; NODES.forEach(function (n) { if (!n.real) return; var d = dTrue(n.p, p); if (d < bd) { bd = d; best = n; } }); return best; }
  function repAround() {
    if (!REP) return '';
    var nc = D.cam ? D.cam.items.filter(function (c) { var q = P(c.lon, c.lat); return dTrue(q, REP.p) <= 300; }).length : 0;
    var er = null, ed2 = 1e9; (PUB ? PUB.er : []).forEach(function (q) { var d = dTrue(q.p, REP.p); if (d < ed2) { ed2 = d; er = q; } });
    return row(REP.here ? '둘레' : '보고 자리 둘레', '300m 안 단속 카메라 ' + nc + '대' + (er ? ' · 가장 가까운 응급실 ' + esc(er.name.replace(/^학교법인가톨릭학원/, '')) + ' ' + (ed2 >= 1000 ? (ed2 / 1000).toFixed(1) + 'km' : Math.round(ed2) + 'm') + (er.o.ertel ? ' (' + esc(er.o.ertel) + ')' : '') : ''));
  }
  function hereRows() {   // 「📍 지금 위치」(T-Book 홈 · &here=1) — 한눈에 볼 것: 관할 · 가까운 지구대·파출소 · 지금 인파 · 지금 하차 상위
    if (!REP || !REP.here) return '';
    var h = '', p = REP.p, dist = function (q) { return dTrue(q, p); }, mt = function (d) { return d >= 1000 ? (d / 1000).toFixed(1) + 'km' : Math.round(d) + 'm'; };
    var dg = dongAtM(p), J = jurAtM(p); if (J || dg) h += row('관할', (J ? esc(J.z.name) : '-') + (dg ? ' · ' + esc(dg.name) : '') + (dg && jurSplit(dg.name) ? ' <em>(반포대로 기준으로 갈림)</em>' : ''));
    var boxes = PUB && PUB.fac.pol ? PUB.fac.pol.filter(function (q) { return q.off && !q.st && !q.ctr; }) : [], bx = null, bd = 1e9;
    boxes.forEach(function (q) { var d = dist(q.p); if (d < bd) { bd = d; bx = q; } });
    if (bx) { var stn = (D.police && D.police.stations || []).filter(function (x) { return x.name === bx.o.station; })[0]; h += row('가까운 지구대·파출소', esc(bx.name) + ' ' + mt(bd) + (stn ? ' · ' + esc(stn.name.replace(/^서울/, '')) + ' ' + esc(stn.tel) : '') + (bx.o.approx ? ' <em>(자리 근사)</em>' : '')); }
    var cw = null, cd = 1e9; LIVEP.forEach(function (L) { var d = dist(L.c); if (d < cd) { cd = d; cw = L; } });
    if (cw && cd < 2000) { var c = crowdAt(cw); if (c) h += row('가까운 인파', esc(cw.o.name) + ' ' + mt(cd) + ' — <b style="color:' + (LVC[c.lvl] || '#64748b') + '">' + esc(c.lvl) + '</b> ' + (c.min ? man(c.min) + '~' + man(c.max) + '명' : '') + (c.kind === 'old' ? ' <em>(받은 때 ' + esc(String(c.t).slice(11, 16)) + ')</em>' : c.kind === 'fcst' ? ' <em>(예측)</em>' : '')); }
    var hh = nowH(), offs = [];
    if (PUB) { PUB.bus.forEach(function (q) { var f = FLOW.bus[q.o.id]; if (f && dist(q.p) < 600) offs.push(['🚌 ' + q.name, f[1][hh]]); }); PUB.subr.forEach(function (q) { var f = FLOW.sub[q.name]; if (f && dist(q.p) < 1000) offs.push(['🚇 ' + q.name + '역', f[1][hh]]); }); }
    offs.sort(function (a, b) { return b[1] - a[1]; });
    if (offs.length) h += row(hh + '시 하차 상위', offs.slice(0, 3).map(function (x) { return esc(x[0]) + ' ' + x[1].toLocaleString(); }).join(' · ') + ' <em>(하루 평균)</em>');
    return h;
  }
  function applyHash() {
    var m = /[#&]lat=(-?[\d.]+)/.exec(location.hash), n = /[#&]lon=(-?[\d.]+)/.exec(location.hash);
    if (!m || !n) return false;
    var lat = +m[1], lon = +n[1];
    if (!isFinite(lat) || !isFinite(lon) || lat < 33.0 || lat > 38.7 || lon < 124.5 || lon > 131.95) return false;   // v2.11.0 전국(종전 서초 상자 — T-Book 주소는 그대로 됨)
    if (lat < 37.395 || lat > 37.535 || lon < 126.935 || lon > 127.135) { var q0 = P(lon, lat); TAPM = q0; view.s = Math.min(cv.clientWidth, cv.clientHeight) / (2 * 1500); view.cx = q0[0]; view.cy = q0[1]; draw(); return true; }   // 서초 밖 = 그 자리로 옮기기만(「보고 자리」 카드는 서초 자료 기준이라 띄우지 않는다)
    REP = { p: P(lon, lat), here: /[#&]here=1(?!\d)/.test(location.hash) };   // here=1 = T-Book 홈 「📍 지금 위치」(v0.10.77) — 아니면 최초보고 「보고 자리」
    TAPM = REP.p; view.s = Math.min(cv.clientWidth, cv.clientHeight) / (2 * 500); view.cx = REP.p[0]; view.cy = REP.p[1] + cv.clientHeight * 0.22 / view.s;   // 아래 카드에 가리지 않게 표시를 위쪽에   // 반경 약 500m
    if (on.bld && view.s > 0.12) loadBld();
    draw(); var s = S(REP.p); sel = { x: s[0], y: s[1], r: 12, it: { kind: 'report' } }; show({ kind: 'report' }); draw();
    return true;
  }
  // &gps=1(T-Book v23.52 · 홈 관내 이름) — 열린 뒤 스스로 지금 위치를 다시 잡는다. 정밀 1km 안 · 서초 상자 안일 때만 옮기고, 아니면 넘겨받은 자리 그대로. 좌표는 저장하지 않는다.
  var gpsAsked = false;
  function gpsHere() {
    if (gpsAsked || !/[#&]gps=1(?!\d)/.test(location.hash) || !navigator.geolocation) return; gpsAsked = true;
    navigator.geolocation.getCurrentPosition(function (pos) {
      var c = pos.coords; if (!(c.accuracy <= 1000) || c.latitude < 37.395 || c.latitude > 37.535 || c.longitude < 126.935 || c.longitude > 127.135) return;
      REP = { p: P(c.longitude, c.latitude), here: true, acc: Math.round(c.accuracy) }; view.cx = REP.p[0]; view.cy = REP.p[1] + cv.clientHeight * 0.22 / view.s;
      draw(); var s = S(REP.p); sel = { x: s[0], y: s[1], r: 12, it: { kind: 'report' } }; show({ kind: 'report' }); draw();
    }, function () {}, { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 });
  }
  window.addEventListener('hashchange', function () { if (hashLayers()) { paintLayers(); if (on.bld && view.s > 0.12) loadBld(); } if (Object.keys(D).length) { if (!applyHash()) draw(); } });
  function sigNow(s) {
    var d = new Date(), dk = String(d.getDay() + 1), pn = s.dow && s.dow[dk], rows = pn && s.plans && s.plans[pn], hm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2), cur = null;
    if (!rows || !rows.length) return '계획 없음';
    rows.forEach(function (r) { if (r[0] <= hm && r[1] > 0) cur = r; });
    if (!cur) cur = rows[rows.length - 1];
    return '주기 ' + cur[1] + '초 · ' + String(cur[3] || '').split(' ').filter(function (x) { return +x > 0; }).length + '현시 (' + esc(cur[0]) + ' 계획)';
  }
  function volRows(v) {
    var d = new Date(), dow = d.getDay(), arr = dow === 0 ? v.sun : dow === 6 ? v.sat : v.wd; if (!arr) return '';
    var h = d.getHours(), tot = arr.map(function (x) { return x[0] + x[1]; }), day = tot.reduce(function (a, b) { return a + b; }, 0), pk = tot.indexOf(Math.max.apply(null, tot));
    return row('지금 ' + h + '시', tot[h].toLocaleString() + '대/시(양방향)') + row('하루', day.toLocaleString() + '대 · 가장 붐비는 때 ' + pk + '시') + '<div class="cap">시간대별 교통량(대/시 · 양방향 · 0~23시 · 오늘 요일의 조사값)</div>' + bar(tot, '#0ea5e9');
  }

  // ---------- v2.4.0 🧊 250m 국가표준격자(전국 확장 설계서 Phase 1) — 칸 뼈대 · 서울 생활인구 250m · 상업업무용 매매 실거래 ----------
  // 격자 = 국가지점번호식 250m(EPSG:5179) · 칸 가운데 위경도는 구운 grid.json 에 있다(앱은 투영 계산을 하지 않는다) · 칸은 250m 정사각으로 그린다(UTM-K 회전은 서울에서 0.5도 안팎이라 무시)
  var GRID = {}, GRIDN = {}, A250 = [], A250K = {}, PT250 = {}, RLOADPT = {}, RLOADA2 = {}, RLOADGR = {}, L250 = {}, RLOADL2 = {}, RT = [], RTG = {}, RLOADRT = {}, F250 = {}, RLOADF2 = {};
  function grLoad(gu) {
    if (RLOADGR[gu]) return RLOADGR[gu];
    RLOADGR[gu] = rGet(gu, 'grid.json').then(function (j) {
      j.cells.forEach(function (c) { var k = []; for (var i = 4; i + 1 < c.length; i += 2) k.push([c[i], c[i + 1]]); GRID[c[0]] = { c: c[0], gu: gu, p: P(c[2], c[1]), land: c[3], k: k }; }); Object.keys(j.names || {}).forEach(function (q) { GRIDN[q] = j.names[q]; }); draw(); }).catch(function () {}); return RLOADGR[gu];
  }
  function l2Load(gu) {
    if (RLOADL2[gu]) return RLOADL2[gu];
    RLOADL2[gu] = grLoad(gu).then(function () { return rGet(gu, 'live250.json'); }).then(function (j) {
      Object.keys(j.cells).forEach(function (k) { var x = j.cells[k]; x.m = j; L250[k] = x; }); draw(); }).catch(function () {}); return RLOADL2[gu];
  }
  function f2Load(gu) {   // v2.9.0 🌏 서울 250m 지금 머무는 외국인(장기 L · 단기 T)
    if (RLOADF2[gu]) return RLOADF2[gu];
    RLOADF2[gu] = grLoad(gu).then(function () { return rGet(gu, 'forn250.json'); }).then(function (j) {
      Object.keys(j.cells).forEach(function (k) { var x = j.cells[k]; x.m = j; F250[k] = x; }); draw(); }).catch(function () {}); return RLOADF2[gu];
  }
  function f2At(x, h, we) { var a = 0; ['L', 'T'].forEach(function (q) { if (x[q]) a += (we ? x[q].we : x[q].wd)[h]; }); return a; }
  function f2Now(x) { return f2At(x, nowH(), isWe()); }
  function rtLoad(gu) {
    if (RLOADRT[gu]) return RLOADRT[gu];
    RLOADRT[gu] = grLoad(gu).then(function () { return rGet(gu, 'rtms.json'); }).then(function (j) {
      j.items.forEach(function (t) { RT.push({ t: t, m: j, p: t[7] ? P(t[8], t[7]) : null }); });
      Object.keys(j.grid).forEach(function (k) { RTG[k] = { n: j.grid[k][0], med: j.grid[k][1], m: j }; }); draw(); }).catch(function () {}); return RLOADRT[gu];
  }
  function a2Load(gu) {
    if (RLOADA2[gu]) return RLOADA2[gu];
    RLOADA2[gu] = rGet(gu, 'taas250.json').then(function (j) {
      j.dic = j.dic || (D.taas10 && D.taas10.dic); j.dow = j.dow || (D.taas10 && D.taas10.dow); Object.keys(j.cells).forEach(function (k) { var c = j.cells[k], x = { k: k, c: c, p: P(c[1], c[0]), m: j }; A250.push(x); A250K[k] = x; }); draw(); }).catch(function () {}); return RLOADA2[gu];
  }
  function ptLoad(gu) {
    if (RLOADPT[gu]) return RLOADPT[gu];
    RLOADPT[gu] = rGet(gu, 'pts250.json').then(function (j) { Object.keys(j.cells).forEach(function (k) { PT250[k] = j.cells[k]; }); PT250._m = j; if (sel && sel.it && sel.it.kind === 'g250') show(sel.it); }).catch(function () {}); return RLOADPT[gu];
  }
  function gridNeed() {
    if (!(on.g250 || on.live250 || on.fl250 || on.rtc || on.acc250 || on.home) || view.s < 0.012) return; var v = viewLL();
    rIdx().forEach(function (g) { var x = g.box, B = g.bytes || {}; if (x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return;
      if (on.acc250 && B.taas250) a2Load(g.gu); if (on.g250 && view.s >= 0.05) { if (B.pts250) ptLoad(g.gu); if (B.live250) l2Load(g.gu); if (B.forn250) f2Load(g.gu); if (B.taas250) a2Load(g.gu); if (B.home) hmLoad(g.gu); if (B.rtms) rtLoad(g.gu); } if (on.home && B.home) hmLoad(g.gu); if (on.g250 && B.grid) grLoad(g.gu); if (on.live250 && B.live250) l2Load(g.gu); if (on.fl250 && B.forn250) f2Load(g.gu); if (on.rtc && B.rtms) rtLoad(g.gu); });
  }
  function isWe() { var d = new Date().getDay(); return d === 0 || d === 6; }
  function l2Now(x) { return (isWe() ? x.we : x.wd)[nowH()]; }
  function sq(p, h) { var a = S([p[0] - h, p[1] - h]), b = S([p[0] + h, p[1] + h]); return [a[0], a[1], b[0] - a[0], b[1] - a[1]]; }
  function inView(r, W0, H0) { return !(r[0] + r[2] < 0 || r[1] + r[3] < 0 || r[0] > W0 || r[1] > H0); }
  function drawGrid(dark) {
    gridNeed(); var W0 = cv.clientWidth, H0 = cv.clientHeight;
    if (on.acc250 && A250.length) { var av = A250.map(function (x) { return a10Val(x.c); }), am = Math.max.apply(null, av) || 1, acol = A10MS[A10M][1];
      A250.forEach(function (x, i) { var r = sq(x.p, 125); if (!av[i] || !inView(r, W0, H0)) return; var t = Math.sqrt(av[i] / am); ctx.fillStyle = hexA(acol, 0.12 + 0.7 * t); ctx.fillRect(r[0], r[1], r[2], r[3]);
        if (r[2] > 30) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = t > 0.5 ? '#fff' : '#111827'; ctx.fillText(String(Math.round(av[i])), r[0] + r[2] / 2, r[1] + r[3] / 2); }
        hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'a10', x: x } }); }); }
    if (on.live250) { var ks = Object.keys(L250).filter(function (k) { return GRID[k]; }), vs = ks.map(function (k) { return l2Now(L250[k]); }), mx = Math.max.apply(null, vs.concat([1]));
      ks.forEach(function (k, i) { var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0) || !vs[i]) return; var t = Math.sqrt(vs[i] / mx);
        ctx.fillStyle = 'rgba(124,58,237,' + (0.08 + 0.62 * t).toFixed(3) + ')'; ctx.fillRect(r[0], r[1], r[2], r[3]);
        if (r[2] > 34) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = t > 0.55 ? '#fff' : (dark ? '#e2e8f0' : '#1e1b4b'); ctx.fillText(vs[i] >= 1000 ? (vs[i] / 1000).toFixed(1) + '천' : String(vs[i]), r[0] + r[2] / 2, r[1] + r[3] / 2); }
        hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'l250', c: k } }); }); }
    if (on.fl250) { var fk = Object.keys(F250).filter(function (k) { return GRID[k]; }), fv = fk.map(function (k) { return f2Now(F250[k]); }), fm = Math.max.apply(null, fv.concat([1]));
      fk.forEach(function (k, i) { var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0) || !fv[i]) return; var t = Math.sqrt(fv[i] / fm);
        ctx.fillStyle = 'rgba(13,148,136,' + (0.08 + 0.64 * t).toFixed(3) + ')'; ctx.fillRect(r[0], r[1], r[2], r[3]);
        if (r[2] > 34) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = t > 0.55 ? '#fff' : (dark ? '#e2e8f0' : '#134e4a'); ctx.fillText(fv[i] >= 1000 ? (fv[i] / 1000).toFixed(1) + '천' : String(Math.round(fv[i])), r[0] + r[2] / 2, r[1] + r[3] / 2); }
        hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'f250', c: k } }); }); }
    if (on.rtc) { var gk = Object.keys(RTG).filter(function (k) { return GRID[k]; }), meds = gk.map(function (k) { return RTG[k].med; }).sort(function (a, b) { return a - b; }), p90 = meds[Math.floor(meds.length * 0.9)] || 1;
      gk.forEach(function (k) { var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0)) return; var t = Math.min(1, RTG[k].med / p90);
        ctx.fillStyle = 'rgba(29,78,216,' + (0.10 + 0.5 * t).toFixed(3) + ')'; ctx.fillRect(r[0], r[1], r[2], r[3]); ctx.strokeStyle = 'rgba(30,58,138,.6)'; ctx.lineWidth = 1; ctx.strokeRect(r[0], r[1], r[2], r[3]);
        hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'rtg', c: k } }); });
      if (view.s >= 0.12) RT.forEach(function (x) { if (x.p) dot(x.p, 3.6, '#1e3a8a', '#fff', { kind: 'rtc', x: x }); }); }
    if (on.g250 && view.s >= 0.05) { ctx.strokeStyle = dark ? 'rgba(148,163,184,.45)' : 'rgba(30,41,59,.28)'; ctx.lineWidth = 0.8;
      Object.keys(GRID).forEach(function (k) { var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0)) return; ctx.strokeRect(r[0], r[1], r[2], r[3]);
        if (!on.live250 && !on.fl250 && !on.rtc) hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'g250', c: k } });
        if (r[2] > 90) { ctx.font = '9px system-ui'; ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillStyle = dark ? '#94a3b8' : '#475569'; ctx.fillText(k, r[0] + 3, r[1] + 3); } }); }
  }
  function dongNm(k8) { if (GRIDN[k8]) return GRIDN[k8]; var d = RDONG.filter(function (q) { return q.k === k8; })[0]; return d ? d.name : k8; }
  function gDongs(k) { var g = GRID[k]; return g ? g.k.map(function (q) { return esc(dongNm(q[0])) + ' ' + q[1] + '%'; }).join(' · ') : '-'; }
  var LB_H24 = []; for (var hq = 0; hq < 24; hq++) LB_H24.push(hq % 6 ? '' : String(hq));
  function gridCard(it) {
    var k = it.c || (it.x && it.x.t[10]), h = '';
    if (it.kind === 'g250') { var h0 = '<h3>🧊 이 250m 칸 한눈에 — ' + esc(k) + '</h3>' + row('걸친 행정동(넓이)', gDongs(k)), L2 = L250[k], A2 = A250K[k], T2 = PT250[k], H2 = HOMEG[k], R2 = RTG[k];
      if (L2) h0 += row('👥 사람(서울 · 한 주 평균)', '평일 14시 ' + L2.wd[14].toLocaleString() + '명 · 새벽 3시 ' + L2.wd[3].toLocaleString() + ' · 주말 14시 ' + L2.we[14].toLocaleString());
      var F3 = F250[k]; if (F3) h0 += row('🌏 머무는 외국인(서울)', '평일 14시 ' + Math.round(f2At(F3, 14, 0)).toLocaleString() + '명 · 새벽 3시 ' + Math.round(f2At(F3, 3, 0)).toLocaleString() + ' <em>(장기+단기 · 통신 추정)</em>');
      if (A2) { var c2 = A2.c, t10 = c2.slice(2, 12).reduce(function (a, b) { return a + b; }, 0); h0 += row('🚗 사고 10년', t10 + '건 · 사망 ' + c2[12] + ' · 중상 ' + c2[13] + ' · 보행자 피해 ' + c2[14] + ' · 밤 ' + pct(c2[18], t10) + '%'); }
      if (T2) { if (T2.fat) h0 += row('🕯 사망사고', T2.fat + '건 · 사망 ' + T2.dead + '명(2016~2025)');
        if (T2.st) h0 += row('🏪 가게', T2.st + '곳' + (T2.stb ? ' — ' + Object.keys(T2.stb).map(function (q) { return esc(q) + ' ' + T2.stb[q]; }).join(' · ') : ''));
        var FN = { cc: '어린이집', kg: '유치원', kyr: '경로당', aca: '학원', edu: '학교', gov: '관공서', cam: '단속 카메라', sz: '보호구역 대상', aed: 'AED', fire: '소방용수', wc: '공중화장실', srItem: '안심귀갓길 시설(벨·CCTV·보안등)', srSvc: '안심 서비스', box: '안심택배함', dem: '치매안심센터', tow: '견인보관소', park: '주차장', ev: '전기차 충전', er: '응급의료기관' }, fs = [];
        Object.keys(FN).forEach(function (q) { if (T2[q]) fs.push(FN[q] + ' ' + T2[q]); }); if (fs.length) h0 += row('🏛 시설', fs.join(' · '));
        if (T2.bus || T2.subn) h0 += row('🚌 대중교통', (T2.bus ? '정류장 ' + T2.bus + '곳 · 하루 승차 ' + T2.bon.toLocaleString() + '명' : '') + (T2.subn ? (T2.bus ? ' · ' : '') + '역 ' + esc((T2.stn || []).join('·')) + ' 하루 승차 ' + T2.son.toLocaleString() + '명' : '')); }
      if (H2) { h0 += hmRow('🏠 아파트', H2.v.a) + hmRow('🏠 오피스텔', H2.v.o) + hmRow('🏠 연립다세대', H2.v.r); }
      if (R2) h0 += row('🏢 상가·업무 매매', R2.n + '건(집합) · ㎡당 중앙 ' + Math.round(R2.med).toLocaleString() + '만 · 평당 ' + pyeong(R2.med));
      if (!L2 && !A2 && !T2 && !H2 && !R2) h0 += '<p class="desc">이 칸 자료를 받는 중이거나, 이 칸에 잡힌 자료가 없다.</p>';
      return h0 + '<p class="desc">국가지점번호식 250m 격자(EPSG:5179) 칸 하나에 이 지도의 점·칸 자료를 모았다. 행정동은 이 칸들을 묶어 보는 단위다(전국 확장 설계서). 사람 = 서울시 250m 생활인구 · 사고 = TAAS · 가게 = 소상공인시장진흥공단 · 집값 = 국토부 실거래(평당 = 전용 기준).</p>' + src('격자 = 이 지도 도구 · 행정동 경계 = 통계청 SGIS(가공 admdongkor 2026-07 · CC BY 4.0) · 칸마다 출처는 각 층 카드'); }
    if (it.kind === 'l250') { var x = L250[k], M2 = x.m, AG = M2.ages, top = function (a) { var i = a.indexOf(Math.max.apply(null, a)); return AG[i] + ' ' + a[i] + '%'; };
      var wd = x.wd, we = x.we, pk = wd.indexOf(Math.max.apply(null, wd)), sw = we.reduce(function (a, b) { return a + b; }, 0) / Math.max(1, wd.reduce(function (a, b) { return a + b; }, 0));
      h = '<h3>👥 생활인구 250m — ' + esc(k) + '</h3>' + row('지금(' + (isWe() ? '주말' : '평일') + ' ' + nowH() + '시)', l2Now(x).toLocaleString() + '명') + row('평일 가장 많을 때', pk + '시 ' + wd[pk].toLocaleString() + '명 · 새벽 3시 ' + wd[3].toLocaleString() + '명') +
        row('주말 ÷ 평일', (sw * 100).toFixed(0) + '% <em>(하루 합)</em>') + row('평일 낮 많은 나이', top(x.ad)) + row('평일 밤 많은 나이', top(x.an)) + row('걸친 행정동(사람 기준)', Object.keys(x.dong).map(function (q) { return esc(dongNm(q)) + ' ' + x.dong[q] + '%'; }).join(' · ')) +
        '<div class="cap">평일 하루 평균 시간대별 생활인구(명 · 0~23시)</div>' + bar(wd, '#7c3aed', LB_H24) + '<div class="cap">주말 하루 평균(명)</div>' + bar(we, '#a78bfa', LB_H24) +
        '<div class="cap">연령 구성 — 평일 낮 11~14시(%)</div>' + bar(x.ad, '#7c3aed', AG) + '<div class="cap">연령 구성 — 평일 밤 0~4시(%) · 밤이 많으면 사는 사람, 낮이 많으면 일하러·놀러 온 사람</div>' + bar(x.an, '#334155', AG);
      var TL = l250Talk(x); return h + (TL.length ? '<div class="talk"><b>🗣 이 칸 읽기</b>' + TL.map(function (q) { return '<div>' + q + '</div>'; }).join('') + '<small>기준(앱): 낮(11~14시)÷새벽(1~3시) 1.6배↑ 들어오는 칸 · 0.8배↓ 주거 칸 · 주말÷평일 ±15~20% · 20·30대 45%↑ · 밤 60대↑ 30%↑</small></div>' : '') + '<p class="desc">' + esc(M2.note) + '</p>' + src(M2.source); }
    if (it.kind === 'f250') { var y = F250[k], M3 = y.m, Lg = y.L, Tm = y.T, nm1 = function (q) { return q.replace('기타', '기타(그 밖 국적)'); };
      h = '<h3>🌏 지금 머무는 외국인 250m — ' + esc(k) + '</h3>' + row('걸친 행정동(넓이)', gDongs(k)) + row('지금(' + (isWe() ? '주말' : '평일') + ' ' + nowH() + '시)', Math.round(f2Now(y)).toLocaleString() + '명 — 장기 ' + Math.round(Lg ? (isWe() ? Lg.we : Lg.wd)[nowH()] : 0).toLocaleString() + ' · 단기 ' + Math.round(Tm ? (isWe() ? Tm.we : Tm.wd)[nowH()] : 0).toLocaleString());
      [['L', '장기체류(91일 이상 — 일·공부·결혼·동포 등)', '#0f766e', '#5eead4'], ['T', '단기체류(90일 이하 — 관광·출장·방문)', '#c2410c', '#fdba74']].forEach(function (q) { var z = y[q[0]]; if (!z) { h += row(q[1].replace(/\(.*$/, ''), '이 칸은 3명 이하(비식별)라 0'); return; }
        var pk = z.wd.indexOf(Math.max.apply(null, z.wd)); h += row(q[1], '평일 가장 많을 때 ' + pk + '시 ' + Math.round(z.wd[pk]).toLocaleString() + '명 · 새벽 3시 ' + Math.round(z.wd[3]).toLocaleString() + ' · 주말 14시 ' + Math.round(z.we[14]).toLocaleString()) +
          '<div class="cap">' + q[1].replace(/\(.*$/, '') + ' — 평일 시간대별(명 · 0~23시)</div>' + bar(z.wd, q[2], LB_H24) + '<div class="cap">주말(명)</div>' + bar(z.we, q[3], LB_H24) +
          (z.nat.length ? '<div class="cap">' + q[1].replace(/\(.*$/, '') + ' — 국적 상위(명 · 한 주 모든 시각 평균)</div>' + bar(z.nat.map(function (n) { return n[1]; }), q[2], z.nat.map(function (n) { return nm1(n[0]); })) : ''); });
      return h + '<p class="desc">' + esc(M3.note) + ' · 국적은 자료에 따로 칸이 있는 나라만(장기 20 · 단기 18) — 나머지는 「기타」.</p>' + src(M3.source); }
    var list = it.kind === 'rtc' ? [it.x] : RT.filter(function (q) { return q.t[10] === k; });
    var m = (list[0] || {}).m || (RTG[k] || {}).m; if (!m) return '<h3>🏢 실거래</h3><p class="desc">자료를 받는 중</p>';
    var jp = list.filter(function (q) { return q.t[2] === 0 && q.t[4]; }).map(function (q) { return q.t[6] / q.t[4]; }).sort(function (a, b) { return a - b; });
    var med = jp.length ? jp[Math.floor(jp.length / 2)] : null, per = (m.source.match(/\d{6}~\d{6}/) || [''])[0];
    h = '<h3>🏢 상가·업무 매매 실거래' + (it.kind === 'rtg' ? ' — 250m 칸 ' + esc(k) : '') + '</h3>' + row('거래', list.length + '건 <em>(' + per + ' 계약 · 해제 뺌)</em>') +
      (med ? row('㎡당 중앙값(집합 · 전용)', Math.round(med).toLocaleString() + '만 원 · <b>평당 약 ' + Math.round(med * 3.3058).toLocaleString() + '만 원</b> <em>(전용 기준 — 공급면적 기준 시세보다 25~35% 높게 나온다)</em>') : '') +
      list.slice().sort(function (a, b) { return b.t[0] - a.t[0]; }).slice(0, 8).map(function (q) { var t = q.t;
        return row(String(t[0]).replace(/(\d{4})(\d\d)/, '$1.$2'), esc(m.uses[t[1]]) + (t[2] ? ' · 일반건물' : ' · 집합') + (t[3] != null ? ' · ' + t[3] + '층' : '') + ' · ' + (t[4] || '-') + '㎡ · <b>' + (t[6] / 1e4).toFixed(t[6] >= 1e5 ? 1 : 2) + '억</b>' + (t[2] === 0 && t[4] ? ' <em>(평당 ' + Math.round(t[6] / t[4] * 3.3058).toLocaleString() + '만)</em>' : '') + ' · ' + esc(m.umds[t[11]])); }).join('') +
      '<p class="desc">평당가 = 거래금액 ÷ 전용면적(㎡) × 3.3058 — 신고된 값이지만 몇 건뿐인 칸은 한 건이 값을 정한다. 일반건물(통 건물)은 국토부가 지번을 가려 자리를 모른다 → 지도에는 집합(구분 소유) 거래만 찍히고, 구 전체 건수에는 들어간다. 추정 월세(매매가 × 상권 소득수익률 ÷ 12)는 한국부동산원 R-ONE 수익률을 붙인 뒤 「추정」으로 낸다.</p>' + src(m.source + ' · ' + m.note);
    return h;
  }
  function l250Talk(x) {
    var wd = x.wd, s = [], day = (wd[11] + wd[12] + wd[13]) / 3, ngt = (wd[1] + wd[2] + wd[3]) / 3, we = x.we.reduce(function (a, b) { return a + b; }, 0) / Math.max(1, wd.reduce(function (a, b) { return a + b; }, 0));
    if (ngt > 50 && day / ngt >= 1.6) s.push('낮(11~14시)이 새벽보다 ' + (day / ngt).toFixed(1) + '배 — 일하러·놀러 들어오는 칸이다. 점심 장사가 되는 자리다.');
    else if (ngt > 50 && day / ngt <= 0.8) s.push('낮이 새벽보다 적다(' + (day / ngt).toFixed(1) + '배) — 사는 사람이 낮에 나가는 주거 칸이다. 저녁·주말 장사 쪽.');
    if (we >= 1.15) s.push('주말이 평일보다 ' + Math.round((we - 1) * 100) + '% 많다 — 나들이·쇼핑·터미널처럼 주말에 모이는 칸.');
    else if (we <= 0.8) s.push('주말이 평일보다 ' + Math.round((1 - we) * 100) + '% 적다 — 사무실 칸. 주말 영업은 따져 볼 것.');
    var ya = x.ad[2] + x.ad[3]; if (ya >= 45) s.push('평일 낮 20·30대가 ' + ya + '% — 젊은 직장인·학생 쪽 소비.');
    var old = x.an[6] + x.an[7]; if (old >= 30) s.push('밤에 60대 이상이 ' + old + '% — 나이 든 주민이 많은 동네.');
    return s;
  }
  function gridLegend() {
    var o = [];
    if (on.live250) o.push(['👥 생활인구 250m ' + (isWe() ? '주말 ' : '평일 ') + nowH() + '시', li('rgba(124,58,237,.7)', '진할수록 많음(√) · 확대하면 숫자', 'box') + '<small class="lg-n">서울만 · 서울시 250M격자 생활인구 2026-09-07~13 한 주 평균 · 내국인</small>']);
    if (on.fl250) o.push(['🌏 머무는 외국인 250m ' + (isWe() ? '주말 ' : '평일 ') + nowH() + '시', li('rgba(13,148,136,.7)', '장기+단기 체류(진할수록 많음 · √) · 확대하면 숫자', 'box') + '<small class="lg-n">서울만 · 서울시 250M격자 생활인구(장기·단기체류 외국인) 2026-09-07~13 한 주 평균 · 통신 자료 추정</small>']);
    if (on.rtc) o.push(['🏢 상가·업무 매매 실거래', li('rgba(29,78,216,.55)', '250m 칸 = 집합건물 ㎡당 거래금액 중앙값(진할수록 비쌈)', 'box') + li('#1e3a8a', '집합건물 거래(확대하면)') + '<small class="lg-n">국토부 상업업무용 매매 · 서울·경기 24개월 · 평당 = 전용 기준</small>']);
    if (on.g250) o.push(['🧊 250m 격자', li('#475569', '국가지점번호식 250m 칸(확대하면 선)', 'line') + '<small class="lg-n">서울·경기 17.6만 칸 · 칸을 누르면 걸친 행정동</small>']);
    return o;
  }
  // 반경 분석에 더한다 — 250m 칸 가운데가 반경 안이면 센다
  function gridRad(c, r) {
    var o = { l: null, n: 0, rt: [] };
    Object.keys(L250).forEach(function (k) { if (!GRID[k]) return; var p = GRID[k].p; if (dTrue(p, c) > r) return; var x = L250[k];
      if (!o.l) o.l = { wd: x.wd.map(function () { return 0; }), we: x.we.map(function () { return 0; }) }; x.wd.forEach(function (v, i) { o.l.wd[i] += v; }); x.we.forEach(function (v, i) { o.l.we[i] += v; }); o.n++; });
    RT.forEach(function (x) { if (x.p && dTrue(x.p, c) <= r) o.rt.push(x); });
    return o;
  }
  function gridRadRows(g) {
    var h = '';
    if (g.l) h += row('생활인구 250m(서울)', '칸 ' + g.n + '개 · 평일 14시 약 ' + g.l.wd[14].toLocaleString() + '명 · 새벽 3시 ' + g.l.wd[3].toLocaleString() + ' · 주말 14시 ' + g.l.we[14].toLocaleString() + ' <em>(2026-09-07~13 · 칸 가운데가 반경 안)</em>') + '<div class="cap">평일 시간대별 생활인구(명 · 반경 안 250m 칸 합)</div>' + bar(g.l.wd, '#7c3aed', LB_H24);
    if (g.rt.length) { var jp = g.rt.filter(function (q) { return q.t[2] === 0 && q.t[4]; }).map(function (q) { return q.t[6] / q.t[4]; }).sort(function (a, b) { return a - b; });
      h += row('상가·업무 매매', g.rt.length + '건(24개월 · 집합건물)' + (jp.length ? ' · ㎡당 중앙값 ' + Math.round(jp[Math.floor(jp.length / 2)]).toLocaleString() + '만 원 · 평당 약 ' + Math.round(jp[Math.floor(jp.length / 2)] * 3.3058).toLocaleString() + '만 원 <em>(전용 기준)</em>' : '')); }
    return h;
  }
  // 테마 — 층 고르기를 주제별로(소유자 2026-10-05 「부동산·교통 등 테마를 잘 선택할 수 있게」) · 층 키는 그대로 · 한 층이 여러 테마에 들 수 있다
  // v2.10.0 테마 다시 묶음(소유자 2026-10-05 「인구 구성이 기본 · 이동 · 교통 … 합리적인 묶음으로」) — 그 지역을 아는 차례: 사람 → 움직임 → 돈 → 집 → 길 → 사고 → 치안 → 돌봄 → 생활 · 층 키는 그대로
  var THEMES = [
    ['all', '전체', null],
    ['split', '🗂 나눠 보기', ['dong', 'usgg', 'juris', 'jurk', 'upb', 'pbox', 'ri'], ['usgg']],
    ['people', '👥 인구 구성', ['dong', 'jgg', 'live250', 'live', 'lpop', 'fdong', 'minbak', 'flodge', 'fl250', 'crowd', 'ri'], ['dong', 'jgg', 'live250']],
    ['move', '🚶 이동·동선', ['volp', 'live250', 'lpop', 'bus', 'bstop', 'msub', 'busd', 'subr', 'sub', 'exit', 'bike', 'lbus', 'spot', 'crowd', 'vol', 'evt', 'gfest'], ['bus', 'subr', 'sub', 'live250']],
    ['spend', '💳 소비·상권', ['sales', 'trd', 'szone', 'rent', 'crowd', 'rtc', 'conv', 'bank', 'bar', 'play', 'inn'], ['sales', 'trd', 'szone']],
    ['estate', '🏠 주거·부동산', ['home', 'rtc', 'rent', 'jgg', 'bld'], ['home', 'rtc']],
    ['traffic', '🚦 도로·교통', ['rnet', 'volp', 'exv', 'tlt', 'road', 'jcnm', 'lspd', 'spd', 'lev', 'lcc', 'vol', 'sig', 'sigx', 'tgis', 'pbtn', 'cam', 'pkcctv', 'pk', 'gpark', 'ev', 'gev', 'fuel', 'tow'], ['rnet', 'volp', 'jcnm', 'lspd', 'cam']],
    ['acc', '🚗 교통사고', ['acc', 'acc250', 'acc10', 'fatal', 'fatal10', 'jct', 'hot', 'hot10', 'drunk', 'risk', 'sz', 'szh', 'spot', 'spota'], ['acc10', 'fatal10', 'jct', 'hot10']],
    ['safe', '🛡 치안·안전', ['jurk', 'pbox', 'jur', 'pol', 'fire', 'er', 'ger', 'aed', 'srbell', 'srcctv', 'srlamp', 'sr112', 'srsvc', 'glamp', 'fw', 'hyd', 'box', 'bar', 'play', 'inn', 'dem'], ['jurk', 'pbox', 'pol', 'fire', 'er']],
    ['care', '🎒 교육·돌봄', ['edu', 'school', 'kg', 'cc', 'kids', 'aca', 'kyr', 'welf', 'dem', 'pg', 'sz'], ['edu', 'kg', 'cc', 'kyr']],
    ['life', '🏥 생활시설', ['govr', 'gov', 'post', 'lib', 'park', 'hosp', 'phar', 'wc', 'wc2', 'heat', 'cold', 'her', 'conv', 'bank', 'box'], ['govr', 'hosp', 'phar', 'park', 'wc2']],
    ['season', '⛅ 날씨·계절', ['lwx', 'lair', 'lak', 'lkma', 'lrad', 'flt', 'flr', 'und', 'ice', 'hcab', 'advb', 'heat', 'cold'], ['lwx', 'lair', 'flt', 'ice']],
    ['live', '📡 실시간', ['lev', 'lspd', 'lcc', 'lak', 'lkma', 'lbus', 'lwx', 'lair', 'lrad', 'crowd'], ['lev', 'lspd', 'lcc', 'lwx', 'lrad']],
    ['map', '🗺 바탕·격자', ['dong', 'road', 'base', 'bld', 'vw', 'jcnm', 'g250', 'ri'], ['g250']]
  ];
  var GORD = ['바탕', '인구 구성', '이동·동선', '소비·상권', '주거·부동산', '도로·교통', '교통사고', '치안·안전', '교육·돌봄', '생활시설', '행사·역사', '날씨·계절', '실시간'];
  var THEME = 'all'; try { THEME = localStorage.getItem('tg_map2d_theme') || 'all'; } catch (e) {}
  function themeDef(id) { var t = THEMES.filter(function (x) { return x[0] === id; })[0]; return t && t[3] ? t[3] : []; }
  function themeKeys(id) { var t = THEMES.filter(function (x) { return x[0] === id; })[0]; return t && t[2] ? t[2].filter(function (k) { return LAYERS.some(function (l) { return l[0] === k; }); }) : null; }

  // ---------- v2.5.0 🏠 주택 실거래(국토부 · 아파트·오피스텔·연립다세대 · 250m 칸·단지) ----------
  var HOMEG = {}, HCX = [], RLOADHM = {}, HOMED = {}, HM = 'apt';
  var HMS = { apt: ['아파트 매매 평당', 'a', 1, '#b91c1c'], je: ['아파트 전세 평당', 'a', 3, '#1d4ed8'], jr: ['아파트 전세가율', 'a', 6, '#7c3aed'], wo: ['아파트 월세', 'a', 5, '#0f766e'], of: ['오피스텔 매매 평당', 'o', 1, '#9333ea'], rh: ['연립다세대 매매 평당', 'r', 1, '#92400e'] };
  var HTY = ['아파트', '오피스텔', '연립다세대'], HTC = ['#b91c1c', '#9333ea', '#92400e'];
  function hmLoad(gu) {
    if (RLOADHM[gu]) return RLOADHM[gu];
    RLOADHM[gu] = grLoad(gu).then(function () { return rGet(gu, 'home.json'); }).then(function (j) {
      HOMED[gu] = j; Object.keys(j.cx).forEach(function (k) { var c = j.cx[k]; HCX.push({ c: c, p: c[3] ? P(c[4], c[3]) : null, m: j }); });
      Object.keys(j.grid).forEach(function (k) { HOMEG[k] = { v: j.grid[k], m: j }; }); draw(); }).catch(function () {}); return RLOADHM[gu];
  }
  function hmVal(v) { var M3 = HMS[HM], x = v[M3[1]]; if (!x) return null; var n = M3[2] === 6 ? Math.min(x[0], x[2]) : x[M3[2] - 1]; if (!n || x[M3[2]] == null) return null; return x[M3[2]]; }
  function pyeong(v) { return v == null ? '-' : Math.round(v * 3.3058).toLocaleString() + '만'; }
  function drawHome(dark) {
    if (!on.home) return; var W0 = cv.clientWidth, H0 = cv.clientHeight, ks = Object.keys(HOMEG).filter(function (k) { return GRID[k]; });
    var vals = ks.map(function (k) { return hmVal(HOMEG[k].v); }), sv = vals.filter(function (v) { return v != null; }).sort(function (a, b) { return a - b; });
    var lo = sv[Math.floor(sv.length * 0.1)] || 0, hi = sv[Math.floor(sv.length * 0.9)] || 1, col = HMS[HM][3];
    ks.forEach(function (k, i) { var v = vals[i]; if (v == null) return; var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0)) return;
      var t = HM === 'jr' ? Math.max(0, Math.min(1, (v - 40) / 50)) : Math.max(0, Math.min(1, (v - lo) / ((hi - lo) || 1)));
      ctx.fillStyle = hexA(col, 0.08 + 0.6 * t); ctx.fillRect(r[0], r[1], r[2], r[3]);
      if (r[2] > 40) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = t > 0.55 ? '#fff' : (dark ? '#e2e8f0' : '#111827');
        ctx.fillText(HM === 'jr' ? v + '%' : HM === 'wo' ? v + '만' : (Math.round(v * 3.3058 / 100) / 10).toLocaleString() + '천', r[0] + r[2] / 2, r[1] + r[3] / 2); }
      hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'hmg', c: k } }); });
    if (view.s >= 0.12) HCX.forEach(function (x) { if (x.p) dot(x.p, 3.4, HTC[x.c[0]], '#fff', { kind: 'hmc', x: x }); });
  }
  function hmRow(lbl, x) { if (!x) return ''; return row(lbl, (x[0] ? '매매 ' + x[0] + '건 · 평당 <b>' + pyeong(x[1]) + '</b>' : '매매 없음') + (x[2] ? ' · 전세 ' + x[2] + '건 평당 ' + pyeong(x[3]) : '') + (x[4] ? ' · 월세 ' + x[4] + '건 중앙 ' + x[5] + '만' : '') + (x[6] != null ? ' · 전세가율 <b>' + x[6] + '%</b>' : '')); }
  var HM_NOTE = '<p class="desc">평당 = ㎡당 × 3.3058 — <b>전용면적 기준</b>이라 흔히 말하는 공급면적 기준 시세보다 25~35% 높게 나온다. 전세가율 = 같은 칸(단지) 전세 ㎡당 중앙값 ÷ 매매 ㎡당 중앙값 — 같은 집끼리 견준 값이 아니라 <b>추정</b>이다(높으면 세입자·실수요 쪽, 낮으면 자가·투자 쪽 신호 — 추론). 매매 24개월 · 전월세 12개월 · 몇 건뿐이면 한 건이 값을 정한다.</p>';
  function homeCard(it) {
    if (it.kind === 'hmg') { var g = HOMEG[it.c]; if (!g) return ''; var v = g.v;
      return '<h3>🏠 주택 실거래 — 250m 칸 ' + esc(it.c) + '</h3>' + hmRow('아파트', v.a) + hmRow('오피스텔', v.o) + hmRow('연립다세대', v.r) + (GRID[it.c] ? row('걸친 행정동', gDongs(it.c)) : '') + HM_NOTE + src(g.m.source + ' · ' + g.m.note); }
    var c = it.x.c, m = it.x.m, tr = c[8], je = c[9], wo = c[10];
    return '<h3>🏠 ' + esc(c[1] || '(이름 없음)') + ' <small>' + HTY[c[0]] + (c[7] ? ' · ' + c[7] + '년' : '') + '</small></h3>' + row('자리', esc(m.umds[c[2]]) + (c[6] ? ' · ' + esc(dongNm(c[6])) : '') + (c[5] ? ' · 칸 ' + c[5] : '')) +
      row('매매(24개월)', tr[0] ? tr[0] + '건 · 평당 중앙 <b>' + pyeong(tr[1]) + '</b> · 마지막 ' + String(tr[2]).replace(/(\d{4})(\d\d)/, '$1.$2') + ' ' + (tr[3] / 1e4).toFixed(2) + '억(' + tr[4] + '㎡)' : '없음') +
      row('전세(12개월)', je[0] ? je[0] + '건 · 평당 보증금 중앙 ' + pyeong(je[1]) + (tr[0] >= 3 && je[0] >= 3 ? ' · 전세가율 약 <b>' + Math.round(je[1] / tr[1] * 100) + '%</b>' : '') : '없음') +
      row('월세(12개월)', wo[0] ? wo[0] + '건 · 월세 중앙 ' + wo[1] + '만 · 보증금 중앙 ' + Math.round(wo[2]).toLocaleString() + '만' : '없음') + HM_NOTE + src(m.source);
  }
  function homeLegend() {
    if (!on.home) return null;
    return ['🏠 주택 실거래(250m)', '<div class="lg-btns">' + Object.keys(HMS).map(function (k) { return '<button data-hm="' + k + '" class="' + (k === HM ? 'on' : '') + '">' + HMS[k][0] + '</button>'; }).join('') + '</div>' +
      li(hexA(HMS[HM][3], 0.6), HM === 'jr' ? '진할수록 전세가율 높음(40%→90%)' : '진할수록 높음(화면 안 하위 10% → 상위 10%)', 'box') + li(HTC[0], '아파트 단지') + li(HTC[1], '오피스텔') + li(HTC[2], '연립다세대') +
      '<small class="lg-n">국토부 실거래 · 매매 24개월 · 전월세 12개월 · 숫자 = 평당(전용 · 천만 원) · 단독·다가구는 지번이 가려져 칸에 없음</small>'];
  }
  function homeDong(k8) { for (var gu in HOMED) { var d = HOMED[gu].dong[k8]; if (d) return { v: d, m: HOMED[gu] }; } return null; }

  // v2.8.0 🌏 외국인 자세히(시군구) — 국적·체류자격(영주 등)·연령×성별·체류기간·귀화 · 출처마다 기준일이 달라 더하지 않는다
  var LB_AGE8 = ['0~9', '10대', '20대', '30대', '40대', '50대', '60대', '70~'], LB_STAY7 = ['1년↓', '1~2', '2~3', '3~4', '4~5', '5~10', '10년↑'];
  function frnCard(gu) {
    FRCUR = gu;
    var F2 = FRN && FRN.gu[gu]; if (!F2) return '<h3>🌏 외국인 주민</h3><p class="desc">이 시군구는 자료가 없다(2024 뒤에 생긴 구 등).</p>';
    var v = F2['2024'] || {}, Dt = FRN.detail || {}, h = '<h3>🌏 외국인 — ' + esc(guName(gu)) + ' <small>(' + esc(F2.src) + ')</small></h3>';
    h += row('외국인 주민(행안부 2024)', (v.tot || 0).toLocaleString() + '명 · 총인구의 ' + (v.pop ? (v.tot / v.pop * 100).toFixed(1) : '-') + '% · 세대 ' + (v.hh || 0).toLocaleString());
    h += row('한국국적 없음', (v.nf || 0).toLocaleString() + '명 — 근로자 ' + (v.work || 0).toLocaleString() + ' · 결혼이민 ' + (v.marr || 0).toLocaleString() + ' · 유학생 ' + (v.stud || 0).toLocaleString() + ' · 외국국적동포 ' + (v.kor || 0).toLocaleString() + ' · 기타 ' + (v.etc || 0).toLocaleString());
    h += row('귀화(한국국적 취득)', (v.nat || 0).toLocaleString() + '명 — 혼인귀화 ' + (v.natm || 0).toLocaleString() + ' · 기타 ' + (v.nato || 0).toLocaleString()) + row('외국인주민 자녀', (v.kid || 0).toLocaleString() + '명');
    if (F2.q) { var qk = Object.keys(F2.q), qs = qk.reduce(function (a, k) { return a + F2.q[k]; }, 0), pr = F2.q['영주(F-5)'] || 0;
      h += row('영주권(F-5)', pr.toLocaleString() + '명' + (qs ? ' · 등록외국인(상위 자격 합)의 ' + Math.round(pr / qs * 100) + '%' : '')) + '<div class="cap">체류자격별 등록외국인(명 · ' + esc((Dt.q || '').replace(/^.*\(KOSIS[^·]*· /, '').replace(/\).*$/, '')) + ')</div>' + bar(qk.map(function (k) { return F2.q[k]; }), '#0e7490', qk.map(function (k) { return k.replace(/\(.*\)/, ''); })); }
    if (F2.nat) h += '<div class="cap">국적별 등록외국인(명 · 상위 10 · 남/여)</div>' + bar(F2.nat.map(function (x) { return x[1]; }), '#7c3aed', F2.nat.map(function (x) { return x[0].replace('한국계중국인', '중국(동포)').replace('타이(태국)', '태국'); })) +
      '<p class="desc">' + F2.nat.slice(0, 5).map(function (x) { return esc(x[0]) + ' ' + x[1].toLocaleString() + '(남 ' + x[2].toLocaleString() + ' · 여 ' + x[3].toLocaleString() + ')'; }).join(' · ') + '</p>';
    if (F2.age && F2.age.mf) { var A2 = F2.age, tm = A2.mf.reduce(function (a, b) { return a + b; }, 0), tf = (A2.ff || []).reduce(function (a, b) { return a + b; }, 0);
      h += '<div class="cap">연령별 외국인(한국국적 없음 · 남 ' + tm.toLocaleString() + ' · 2024)</div>' + bar(A2.mf, '#2563eb', LB_AGE8) + '<div class="cap">연령별 외국인(한국국적 없음 · 여 ' + tf.toLocaleString() + ')</div>' + bar(A2.ff || [], '#db2777', LB_AGE8);
      if (A2.mn) h += '<div class="cap">연령별 귀화자(남 파랑 · 여 분홍 합 — 한국국적 취득)</div>' + bar(A2.mn.map(function (x, i) { return x + ((A2.fn || [])[i] || 0); }), '#64748b', LB_AGE8); }
    if (F2.stay) { var ts = F2.stay.reduce(function (a, b) { return a + b; }, 0); h += row('머문 기간', '1년 미만 ' + pct(F2.stay[0], ts) + '% · 5년 이상 ' + pct(F2.stay[5] + F2.stay[6], ts) + '% <em>(장기 거주 비중)</em>') + '<div class="cap">체류기간별 외국인 주민(명 · 2024)</div>' + bar(F2.stay, '#0f766e', LB_STAY7); }
    if (FEST && FEST.gu[gu]) { var E = FEST.gu[gu], hs = E.house, ld = E.land;
      if (hs) h += row('외국인 소유 공동주택(' + esc(hs['기간']) + ')', (hs['주택수'] || 0).toLocaleString() + '호 · 소유자 ' + (hs['소유자수'] || 0).toLocaleString() + '명 · 1인당 ' + (hs['1인당 평균소유주택수'] || '-') + (hs['범위'] === 'city' ? ' <em>(시 전체 값)</em>' : ''));
      if (ld) { var lm = Object.keys(ld.m).sort(); h += '<div class="cap">외국인 토지 거래(필지 · 달마다' + (ld['범위'] === 'city' ? ' · 시 전체' : '') + ')</div>' + bar(lm.map(function (q) { return ld.m[q]['필지'] || 0; }), '#b45309', lm.map(function (q) { return q.slice(4); })); } }
    else if (!FEST) festLoad();
    if (FSIDO) { var sdn = SIDO_FULL[gu.slice(0, 2)], Fs = FSIDO.sido[sdn] || (gu.slice(0, 2) === '12' ? FSIDO.sido['전라남도'] : null);
      if (Fs) h += row('고용허가 외국인 근로자(' + esc(sdn === '전남광주통합특별시' ? '전라남도' : sdn) + ' 전체 · ' + esc(Fs['기준월']) + ')', 'E-9 ' + ((Fs.E9 || {})['계'] || 0).toLocaleString() + '명(제조 ' + ((Fs.E9 || {})['제조업'] || 0).toLocaleString() + ' · 농축산 ' + ((Fs.E9 || {})['농축산업'] || 0).toLocaleString() + ') · H-2 ' + ((Fs.H2 || {})['계'] || 0).toLocaleString() + '명 · 사업장 ' + ((Fs.biz || {})['계'] || 0).toLocaleString() + ' <em>(시도 단위만 공표)</em>'); }
    else fsLoad();
    h += '<p class="desc"><b>단기체류(90일 이하 · 관광·단기방문)</b>는 시군구 공식 통계가 없다(법무부 단기체류외국인 현황은 전국 단위) — 서울은 <b>🌏 지금 머무는 외국인 250m</b> 층(서울시 생활인구 장기·단기체류)으로 「그 시각 그 칸에 머무는 사람」과 국적을 볼 수 있다. 등록외국인(법무부 · 연말)과 외국인주민(행안부 · 11월 1일)은 기준이 달라 더하지 않는다.</p>';
    return h + src(FRN.source + ' · ' + [Dt.q, Dt.nat, Dt.age, Dt.stay].filter(Boolean).join(' · '));
  }

  // ---------- v2.8.0 🚓 전국 경찰서 관할(별표2 × 행정동) · 👮 지구대·파출소 자리 ----------
  // T-Book 이 쓰는 jur 층(서초·방배 세밀 관할 · 반포 현장 기준)은 그대로 — 이 층은 전국을 행정동 단위로 근사한다
  var POL2 = null, POL2P = null;
  function polLoad() { if (POL2P) return POL2P; POL2P = fetch('data/police.json').then(function (r) { return r.json(); }).then(function (j) { POL2 = j; j.byI = {}; j.stations.forEach(function (s2) { j.byI[s2[0]] = s2; s2.p = s2[2] != null ? P(s2[3], s2[2]) : null; }); j.pbox.forEach(function (b) { b.p = P(b[4], b[3]); }); draw(); }).catch(function () { POL2 = null; }); return POL2P; }
  function polCol(i) { var h = (i * 137.508) % 360; return 'hsl(' + h.toFixed(0) + ',62%,52%)'; }
  function polLab(L) { var pr = String(L).split('~'), f = function (t) { return (t || '').split(',').filter(function (x) { return x !== ''; }).map(function (x) { return POL2.byI[+x]; }).filter(Boolean); }; return { main: f(pr[0]), extra: f(pr[1]) }; }   // 「21~6」 = 기본 21번 서 + 일부 번지 6번 서 · 「1,4」 = 두 서가 나눠 맡음
  function polOf(k8) { if (!POL2 || !k8) return null; var L = POL2.labels[POL2.dong[k8]]; if (L == null) return null; var o = polLab(L), st = o.main; st.extra = o.extra; return st; }
  function pboxNear(p) { if (!POL2) return null; var b = null, bd = 1e12; POL2.pbox.forEach(function (x) { var d = dTrue(x.p, p); if (d < bd) { bd = d; b = x; } }); return b ? { b: b, d: bd } : null; }
  // ---------- v2.11.0 🌾 리(里) 경계 — 리마다 가게·사고 수(점을 세는 그릇 · 리 인구 통계는 비공개) ----------
  var RIS = [], RLOADRI = {}, RIM = {};
  function riLoad(gu) {
    if (RLOADRI[gu]) return RLOADRI[gu];
    RLOADRI[gu] = rGet(gu, 'ri.json').then(function (j) { RIM[gu] = j;
      j.ri.forEach(function (x) { var b = [1e12, -1e12, 1e12, -1e12]; x.polys = x.polys.map(function (pg) { return pg.map(function (rg) { return rg.map(function (q) { var p = P(q[0], q[1]); if (p[0] < b[0]) b[0] = p[0]; if (p[0] > b[1]) b[1] = p[0]; if (p[1] < b[2]) b[2] = p[1]; if (p[1] > b[3]) b[3] = p[1]; return p; }); }); }); x.box = b; x.p = P(x.c[0], x.c[1]); x.gu = gu; x.m = j; RIS.push(x); });
      draw(); }).catch(function () {}); return RLOADRI[gu];
  }
  function riAtM(m) { for (var i = 0; i < RIS.length; i++) if (inPoly(RIS[i], m)) return RIS[i]; return null; }
  function drawRi(dark) {
    if (!on.ri || view.s < 0.004) return; var v = viewLL();
    rIdx().forEach(function (g) { var x = g.box, B = g.bytes || {}; if (B.ri && !(x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3])) riLoad(g.gu); });
    var a0 = M(0, 0), a1 = M(cv.clientWidth, cv.clientHeight), vis = RIS.filter(function (r) { return !(r.box[1] < a0[0] || r.box[0] > a1[0] || r.box[3] < a0[1] || r.box[2] > a1[1]); }), mx = 1;
    vis.forEach(function (r) { if (r.st > mx) mx = r.st; });
    vis.forEach(function (r) { var t = Math.sqrt(r.st / mx); ctx.fillStyle = 'rgba(101,163,13,' + (0.04 + 0.32 * t).toFixed(3) + ')'; ctx.strokeStyle = dark ? 'rgba(190,242,100,.85)' : 'rgba(77,124,15,.9)'; ctx.lineWidth = 1.6;
      r.polys.forEach(function (pg) { path(pg[0]); ctx.fill(); ctx.stroke(); }); });
    if (view.s >= 0.008) vis.forEach(function (r) { label(r.p, r.name.split(' ').pop(), 11, dark ? '#d9f99d' : '#365314', dark ? 'rgba(15,22,36,.6)' : 'rgba(255,255,255,.7)'); });
  }
  function riCard(r) {
    return '<h3>🌾 ' + esc(r.name) + ' <small>(' + esc(guName(r.gu)) + ' · 법정리 ' + esc(r.k) + ')</small></h3>' + row('가게(상가업소)', r.st.toLocaleString() + '곳' + (r.st ? ' — ' + Object.keys(r.stb).map(function (q) { return esc(q) + ' ' + r.stb[q]; }).join(' · ') : '')) +
      row('교통사고 10년', r.acc.toLocaleString() + '건 · 사망자 ' + r.dead + ' · 중상자 ' + r.ser + ' <em>(2016~2025 · 100m 칸 가운데가 든 리 — 근사)</em>') + row('사망사고', r.fat + '건') +
      '<p class="desc">' + esc(r.m.note) + '</p>' + src(r.m.source);
  }
  // ---------- v2.12.0 🗂 나눠 보기 — 읍면동·시군구·경찰서·지구대·파출소(근사) 단위로 칠하고 누르면 그 단위 합계(profile.json 을 더한다) ----------
  var UCUR = null;
  function profP(gu) { if (AIP[gu]) return Promise.resolve(AIP[gu]); return rGet(gu, 'profile.json').then(function (x) { AIP[gu] = x; return x; }).catch(function () { AIP[gu] = { none: 1, dong: {} }; return AIP[gu]; }); }
  function pbOfP(k8, p) {   // 그 동의 관할 경찰서(번지로 나눠 맡으면 둘 다) 지구대·파출소 가운데 동 가운데에서 가장 가까운 곳 — 근사
    var st = polOf(k8); if (!st || !st.length || !p) return null; var ids = st.map(function (q) { return q[0]; }), b = null, bd = 1e12;
    POL2.pbox.forEach(function (x, i) { if (ids.indexOf(x[6]) < 0) return; var d = dTrue(x.p, p); if (d < bd) { bd = d; b = i; } }); return b; }
  function sggAt(m) { for (var i = 0; i < SGG.length; i++) if (SGG[i].rings.some(function (r) { return inRing(r, m[0], m[1]); })) return i; return -1; }
  function unitAt(m) {
    if (UNIT) return unitAtU(m);
    if ((on.upb || on.jurk) && POL2) { var d = dongAtM(m); if (d && d.k) { if (on.upb) { if (d._pb === undefined) d._pb = pbOfP(d.k, d.c); if (d._pb != null) return { t: 'pb', id: d._pb }; }
        if (on.jurk) { var st = polOf(d.k); if (st && st.length) return { t: 'ps', id: st[0][0] }; } } }
    if (on.usgg) { var i = sggAt(m); if (i >= 0) return { t: 'sgg', id: i }; }
    return null; }
  function unitTitle(u) { if (u.t === 'sgg') return '🗂 ' + SGG[u.id].g.sido + ' ' + SGG[u.id].g.name; if (u.t === 'ps') return '🚓 ' + POL2.byI[u.id][1] + ' 관할'; var b = POL2.pbox[u.id]; return '👮 ' + b[0] + (b[1] ? ' 파출소' : ' 지구대') + ' 구역(근사)'; }
  function unitKeys(u) {   // 경찰서·지구대 = 그 서가 맡는 행정동 코드
    var o = []; Object.keys(POL2.dong).forEach(function (k) { var st = polOf(k); if (!st) return; var ids = st.map(function (q) { return q[0]; });
      if (u.t === 'ps' ? ids.indexOf(u.id) >= 0 : ids.indexOf(POL2.pbox[u.id][6]) >= 0) o.push(k); }); return o; }
  function unitGus(u) {
    if (u.t === 'sgg') { var G = SGG[u.id].g; return rIdx().filter(function (g) { return SIDO_FULL[g.gu.slice(0, 2)] === G.sido && (g.name === G.name || g.name.indexOf(G.name) === 0); }).map(function (g) { return g.gu; }); }
    var o = []; unitKeys(u).forEach(function (k) { if (o.indexOf(k.slice(0, 5)) < 0) o.push(k.slice(0, 5)); }); return o; }
  function unitDongs(u) {
    var gus = unitGus(u), out = [];
    if (u.t === 'sgg') { gus.forEach(function (g) { var j = AIP[g]; if (j && j.dong) Object.keys(j.dong).forEach(function (k) { out.push(j.dong[k]); }); }); return out; }
    unitKeys(u).forEach(function (k) { var j = AIP[k.slice(0, 5)], d = j && j.dong && j.dong[k]; if (!d) return;
      if (u.t === 'pb') { var c = d['가운데']; if (!c || pbOfP(k, P(c[0], c[1])) !== u.id) return; } out.push(d); });
    return out; }
  function unitAgg(ds) {
    var A = { n: ds.length, km2: 0, pop: 0, m: 0, f: 0, age: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], hh: 0, hp: 0, house: 0, biz: 0, emp: 0, st: 0, stb: {}, acc: 0, accY: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dead: 0, ser: 0, ped: 0, bus: 0, sub: 0, sales: 0, salesQ: '', gg: 0, ggY: '', names: [] };
    ds.forEach(function (d) { A.km2 += d['넓이_km2'] || 0; var p = d['주민']; A.names.push([d['이름'], p ? p['계'] : 0]);
      if (p) { A.pop += p['계'] || 0; A.m += p['남'] || 0; A.f += p['여'] || 0; var a = p['연령10세'] || {}; Object.keys(a).forEach(function (q, i) { A.age[i] += a[q] || 0; }); }
      var h = d['가구·주택·사업체(SGIS)']; if (h) { A.hh += h['가구'] || 0; A.hp += h['인구'] || 0; A.house += h['주택'] || 0; A.biz += h['사업체'] || 0; A.emp += h['종사자'] || 0; }
      var g = d['가게(상가업소)']; if (g) { A.st += g['계'] || 0; Object.keys(g['대분류'] || {}).forEach(function (q) { A.stb[q] = (A.stb[q] || 0) + g['대분류'][q]; }); }
      var t = d['교통사고(TAAS 2016~2025)']; if (t) { A.acc += t['계'] || 0; A.dead += t['사망자'] || 0; A.ser += t['중상자'] || 0; A.ped += t['보행자 피해'] || 0; Object.keys(t['해마다'] || {}).forEach(function (y, i) { A.accY[i] += t['해마다'][y] || 0; }); }
      var b = d['이동(대중교통)']; if (b) { A.bus += b['버스 하루 승차'] || 0; A.sub += b['역 하루 승차'] || 0; }
      var c = d['카드 매출(추정)']; if (c) { A.sales += c['매출_만원'] || 0; A.salesQ = c['분기'] || A.salesQ; }
      var c2 = d['카드 소비(경기 상세)']; if (c2) { A.gg += c2['한 달 평균_만원'] || 0; A.ggY = c2['기간'] || A.ggY; } });
    return A; }
  function unitCard(it) {
    var u = it.u; UCUR = it; if (!POL2 && u.t !== 'sgg') { polLoad(); }
    if (u.t === 'sgg' && !LPOP) lpLoad2().then(function () { var c = $('m2dCard'); if (UCUR === it && c && c.classList.contains('on')) show(it); });
    var gus = unitGus(u), need = gus.filter(function (g) { return !AIP[g]; });
    if (need.length) { Promise.all(need.map(profP)).then(function () { var c = $('m2dCard'); if (UCUR === it && c && c.classList.contains('on') && c.querySelector('[data-uwait]')) show(it); });
      return '<h3>' + esc(unitTitle(u)) + '</h3><p class="desc" data-uwait="1">자료를 받는 중… (시군구 ' + gus.length + '곳의 동 프로필)</p>'; }
    var ds = unitDongs(u), A = unitAgg(ds), h = '<h3>' + esc(unitTitle(u)) + '</h3>', f1 = function (v) { return (Math.round(v * 10) / 10).toLocaleString(); };
    if (!ds.length) return h + '<p class="desc">이 단위에 든 행정동 자료가 없다(자료 밖이거나 새로 생긴 동).</p>';
    if (u.t === 'ps') { var s2 = POL2.byI[u.id], bx = POL2.pbox.filter(function (b) { return b[6] === u.id; }); h += row('대표번호', s2[4] ? '<a href="tel:' + esc(s2[4]) + '">' + esc(s2[4]) + '</a>' : '-') + row('지구대·파출소', bx.length + '곳 — ' + bx.map(function (b) { return esc(b[0]); }).join(' · ')); }
    if (u.t === 'pb') { var b = POL2.pbox[u.id], s3 = POL2.byI[b[6]]; h += row('주소', esc(b[5])) + row('경찰서', esc(s3 ? s3[1] : b[2]) + (s3 && s3[4] ? ' · <a href="tel:' + esc(s3[4]) + '">' + esc(s3[4]) + '</a> <em>(서 대표번호)</em>' : '')); }
    h += row('행정동', A.n + '곳 · 넓이 ' + f1(A.km2) + 'km²');
    if (A.pop) { var ag = A.age, sh = function (a, b2) { var t = 0; for (var i = a; i <= b2; i++) t += ag[i]; return pct(t, A.pop); };
      h += row('주민', A.pop.toLocaleString() + '명 · 남 ' + A.m.toLocaleString() + ' · 여 ' + A.f.toLocaleString() + ' · km²당 ' + Math.round(A.pop / (A.km2 || 1)).toLocaleString() + '명') + row('나이 구성', '0~19 ' + sh(0, 1) + '% · 20~39 ' + sh(2, 3) + '% · 40~59 ' + sh(4, 5) + '% · 60+ ' + sh(6, 9) + '% · 70+ ' + sh(7, 9) + '%') +
        '<div class="cap">연령 10세 구간(명 · 주민등록)</div>' + bar(ag, '#7c3aed', ['0~9', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대', '90+']); }
    if (A.hh) h += row('가구·일터(SGIS 2023)', '가구 ' + A.hh.toLocaleString() + ' · 인구÷가구 ' + f1(A.hp / A.hh) + ' · 주택 ' + A.house.toLocaleString() + ' · 사업체 ' + A.biz.toLocaleString() + ' · 종사자 ' + A.emp.toLocaleString() + (A.hp ? ' <em>(종사자÷인구 ' + f1(A.emp / A.hp) + ' — 1 넘으면 일터형)</em>' : ''));
    if (A.st) { var sb = Object.keys(A.stb).sort(function (a, b2) { return A.stb[b2] - A.stb[a]; }); h += row('가게', A.st.toLocaleString() + '곳' + (A.pop ? ' · 주민 1천 명당 ' + f1(A.st / A.pop * 1000) : '') + ' — ' + sb.slice(0, 6).map(function (q) { return esc(q) + ' ' + A.stb[q].toLocaleString(); }).join(' · ')); }
    if (A.acc) h += row('교통사고 10년', A.acc.toLocaleString() + '건(해마다 약 ' + Math.round(A.acc / 10).toLocaleString() + ') · 사망자 ' + A.dead + ' · 중상자 ' + A.ser.toLocaleString() + ' · 보행자 피해 ' + A.ped.toLocaleString()) + '<div class="cap">해마다 사고(2016~2025 · TAAS)</div>' + bar(A.accY, '#dc2626', ['16', '', '18', '', '20', '', '22', '', '24', '25']);
    if (A.bus || A.sub) h += row('대중교통 하루 승차', [A.bus ? '버스 ' + Math.round(A.bus).toLocaleString() + '명' : '', A.sub ? '지하철 ' + Math.round(A.sub).toLocaleString() + '명' : ''].filter(Boolean).join(' · ') + (A.bus ? '' : ' <em>(버스 승하차 자료 없음)</em>'));
    if (A.sales) h += row('카드 매출(서울 추정)', '약 ' + (A.sales / 1e4).toLocaleString(undefined, { maximumFractionDigits: 1 }) + '억 원 <em>(' + esc(A.salesQ) + ' 분기)</em>');
    if (A.gg) h += row('카드 소비(경기)', '한 달 약 ' + (A.gg / 1e4).toLocaleString(undefined, { maximumFractionDigits: 1 }) + '억 원 <em>(' + esc(A.ggY) + ')</em>');
    if (u.t === 'sgg' && LPOP) { gus.forEach(function (g) { var L = LPOP.gu[g]; if (!L) return; var ms = Object.keys(L.m).sort(), lm = ms[ms.length - 1], v = L.m[lm];
        h += row('생활인구(' + lm.slice(0, 4) + '.' + lm.slice(4) + ' · ' + esc(L.kind) + '지역)', (v.tot || 0).toLocaleString() + '명' + (L.reg ? ' · <b>주민의 ' + (v.tot / L.reg).toFixed(1) + '배</b>' : '') + (v.m ? ' · 남 ' + v.m.toLocaleString() + ' · 여 ' + (v.f || 0).toLocaleString() : '')) +
          '<div class="cap">생활인구 달마다(명 · 통계청)</div>' + bar(ms.map(function (q) { return L.m[q].tot || 0; }), '#7c3aed', ms.map(function (q) { return q.slice(4); })) + (v.age ? '<div class="cap">생활인구 연령(' + lm + ')</div>' + bar(v.age.map(function (x) { return x || 0; }), '#a78bfa', LPOP.ages) : ''); }); }
    else if (u.t === 'sgg' && !LPOP) lpLoad2();
    if (u.t === 'sgg') { var fx = 0, fn = []; gus.forEach(function (g) { var F2 = FRN && FRN.gu[g]; if (F2 && F2['2024'] && fn.indexOf(F2.src) < 0) { fx += F2['2024'].tot || 0; fn.push(F2.src); } }); if (fx) h += row('외국인 주민(행안부 2024)', fx.toLocaleString() + '명' + (A.pop ? ' · 주민 대비 약 ' + pct(fx, A.pop) + '%' : '')); }
    var nm = A.names.sort(function (a, b2) { return b2[1] - a[1]; });
    h += row('든 동(주민 많은 순)', nm.slice(0, 30).map(function (q) { return esc(q[0]); }).join(' · ') + (nm.length > 30 ? ' … 외 ' + (nm.length - 30) + '곳' : ''));
    if (u.t === 'sgg') h += econGuHtml(econSggKeys(u.id), SGG[u.id].g.name);
    h += '<div class="lg-btns"><button data-aiu="' + u.t + '|' + u.id + '">🤖 AI용 복사 — 이 단위 기본 자료</button></div>';
    return h + '<p class="desc">이 지도에 구운 행정동 프로필(profile.json)을 더한 값이다. ' + (u.t === 'pb' ? '<b>지구대·파출소 구역은 공식 관할이 아니라 근사</b>(관할 경계 비공개 — 그 동의 관할 경찰서 지구대·파출소 가운데 가장 가까운 곳). ' : u.t === 'ps' ? '경찰서 관할은 별표2 × 행정동 근사 — 번지로 나뉜 동은 두 서 모두에 든다. ' : '') + '생활인구·카드(서울)는 서울만, 카드 상세는 경기 일부 시만 있다.</p>' + src('행정동 프로필(주민 행안부 · 가구 SGIS · 가게 소진공 · 사고 TAAS · 교통카드 · 카드) · 관할 = 직제 시행규칙 별표2 · 지구대 자리 = 경찰청 주소 현황');
  }
  function unitText(u) {
    var ds = unitDongs(u), A = unitAgg(ds), sum = { '단위': unitTitle(u), '행정동 수': A.n, '넓이_km2': Math.round(A.km2 * 10) / 10, '주민': A.pop, '남': A.m, '여': A.f, '연령10세': A.age, '가구(SGIS 2023)': A.hh, '주택': A.house, '사업체': A.biz, '종사자': A.emp, '가게': A.st, '가게 대분류': A.stb, '교통사고 10년': A.acc, '해마다 사고(2016~2025)': A.accY, '사망자': A.dead, '중상자': A.ser, '보행자 피해': A.ped, '버스 하루 승차': Math.round(A.bus), '지하철 하루 승차': Math.round(A.sub), '카드 매출 서울 추정(만원·분기)': A.sales || null, '카드 소비 경기(만원·한 달)': A.gg || null };
    var dm = {}; ds.forEach(function (d) { dm[d['코드']] = d; });
    return '[데이터 압축지도 — 지역 단위 기본 자료 · AI 분석용]\n단위: ' + unitTitle(u) + (u.t === 'pb' ? ' (지구대·파출소 구역은 공식 관할이 아닌 근사 — 동의 관할 경찰서 지구대 가운데 가장 가까운 곳)' : u.t === 'ps' ? ' (별표2 × 행정동 근사)' : '') +
      '\n읽는 법: 「합계」는 아래 행정동 값을 더한 것. 주민(사는 사람)·생활인구(머무는 사람)·외국인은 정의가 달라 더하지 않는다. 「추정」·「근사」는 그렇게 밝힌다. 빈 칸은 자료가 없는 것.\n요청 예: 이 구역의 인구 구성·나이·일터형/주거형·가게 구성·사고 위험·대중교통·소비 특성을 요약하고 동마다 다른 점을 짚어 줘. 근거 숫자를 함께.\n\n```json\n' + JSON.stringify({ '합계': sum, '행정동': dm }) + '\n```\n';
  }
  // v2.12.0 💳 경기 카드 소비 상세(경기데이터드림 · 일부 시 · 공공누리 2유형 = 상업 이용 금지)
  var GGC = {}, GGCUR = null;
  function ggcCard(it) {
    GGCUR = it; var j = GGC[it.gu];
    if (!j) { rGet(it.gu, 'ggcard.json').then(function (x) { GGC[it.gu] = x; }).catch(function () { GGC[it.gu] = { dong: {} }; }).then(function () { var c = $('m2dCard'); if (GGCUR === it && c && c.querySelector('[data-gwait]')) show(it); });
      return '<h3>💳 카드 소비</h3><p class="desc" data-gwait="1">자료를 받는 중…</p>'; }
    var x = j.dong[it.k], nm = dongNm(it.k); if (!x) return '<h3>💳 카드 소비 — ' + esc(nm) + '</h3><p class="desc">이 동은 자료에 없다(개방된 시만 · 동 코드가 바뀐 곳은 뺐다).</p>';
    var won = function (v) { return v >= 1e4 ? (v / 1e4).toFixed(1) + '억' : v.toLocaleString() + '만'; }, tot = x.amt || 1;
    var h = '<h3>💳 카드 소비 — ' + esc(nm) + '</h3>' + row('한 달 평균', '<b>' + won(x.amt) + ' 원</b> · ' + x.cnt.toLocaleString() + '건 <em>(' + esc(j.months[0]) + '~' + esc(j.months[j.months.length - 1]) + ')</em>') +
      row('남 · 여', Math.round(x.sx[0] / (x.sx[0] + x.sx[1] || 1) * 100) + '% · ' + Math.round(x.sx[1] / (x.sx[0] + x.sx[1] || 1) * 100) + '%') +
      '<div class="cap">연령별 — 남(만 원 · 한 달)</div>' + bar(x.agm.slice(0, 9), '#2563eb', j.ag.slice(0, 9)) + '<div class="cap">연령별 — 여(만 원 · 한 달)</div>' + bar(x.agf.slice(0, 9), '#db2777', j.ag.slice(0, 9)) +
      '<div class="cap">시간대별(만 원)</div>' + bar(x.hr, '#f59e0b', j.hr.map(function (q) { return q.replace('시', ''); })) + '<div class="cap">요일별(만 원)</div>' + bar(x.dw, '#0d9488', ['월', '화', '수', '목', '금', '토', '일']) +
      '<div class="cap">업종 대분류(만 원)</div>' + bar(x.big.map(function (q) { return q[1]; }), '#7c3aed', x.big.map(function (q) { return q[0].split('/')[0]; })) +
      row('많이 쓰는 곳', x.mid.slice(0, 8).map(function (q) { return esc(q[0].split('·').pop()) + ' ' + Math.round(q[1] / tot * 100) + '%'; }).join(' · '));
    var bg = Object.keys(x.bigag || {}); if (bg.length) h += row('업종마다 많이 쓰는 나이', bg.map(function (b) { var a = x.bigag[b], i = a.indexOf(Math.max.apply(null, a)); return esc(b.split('/')[0]) + ' ' + j.ag[i]; }).join(' · '));
    return h + '<p class="desc">' + esc(j.note) + '</p>' + src(j.source);
  }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-ggc]'); if (!b) return; var a = b.getAttribute('data-ggc').split('|'); show({ kind: 'ggc', gu: a[0], k: a[1] }); });
  // ---------- v2.13.0 🪜 단위 사다리 — 지점 → 250m 칸 → (리) → 행정동 → 지구대 구역 → 경찰서 관할 → 시군구 · 넓혀 보기 ⬆ / 아래 단위 순위 ⬇ / 윗단위와 비교 ----------
  var TAPM = null, LADS = [];
  function ladLevel(it) { if (it.kind === 'unit') return it.u.t; if (it.kind === 'dong' || it.kind === 'rgo') return 'dong'; if (/^(g250|l250|f250|a10|rtg|hmg|jgc)$/.test(it.kind)) return 'cell'; if (it.kind === 'ri') return 'ri'; return 'pt'; }
  function cellAt(m) { var b = null; Object.keys(GRID).forEach(function (k) { var p = GRID[k].p; if (Math.abs(p[0] - m[0]) <= 125 && Math.abs(p[1] - m[1]) <= 125) b = k; }); return b; }
  function goDong(gu, k, name, c) {   // ⬇ 좁혀 가기 — 그 동으로 옮겨 동 카드
    var p = P(c[0], c[1]); TAPM = p; view.cx = p[0]; view.cy = p[1]; if (view.s < 0.03) view.s = 0.03;
    var d = allDong().filter(function (q) { return q.k === k; })[0];
    var it2 = d ? { kind: 'dong', d: d } : { kind: 'rgo', gu: gu, g: guName(gu), name: name }, sp = S(d ? d.c : p); sel = { x: sp[0], y: sp[1], r: 8, it: it2 }; show(it2); draw();
  }
  function cmpHtml(A, Ap, pn) {
    if (!A.pop || !Ap.pop) return '';
    var o60 = function (X) { var t = 0; for (var i = 6; i < 10; i++) t += X.age[i]; return t / X.pop * 100; }, f = function (v, n) { return (Math.round(v * Math.pow(10, n)) / Math.pow(10, n)).toLocaleString(); },
      r = function (a, b) { return b ? ' <em>(' + f(a / b, 1) + '배)</em>' : ''; }, h = '';
    h += row('60세 이상', f(o60(A), 1) + '% · ' + esc(pn) + ' ' + f(o60(Ap), 1) + '%' + r(o60(A), o60(Ap)));
    if (A.acc && Ap.acc) h += row('사고(주민 1천 명당 · 해마다)', f(A.acc / 10 / A.pop * 1000, 1) + ' · ' + esc(pn) + ' ' + f(Ap.acc / 10 / Ap.pop * 1000, 1) + r(A.acc / A.pop, Ap.acc / Ap.pop));
    if (A.st && Ap.st) h += row('가게(주민 1천 명당)', f(A.st / A.pop * 1000, 1) + ' · ' + esc(pn) + ' ' + f(Ap.st / Ap.pop * 1000, 1) + r(A.st / A.pop, Ap.st / Ap.pop));
    if (A.hp && Ap.hp) h += row('종사자÷인구', f(A.emp / A.hp, 2) + ' · ' + esc(pn) + ' ' + f(Ap.emp / Ap.hp, 2));
    return '<div class="cap">⚖ 윗단위(' + esc(pn) + ')와 비교 — 배 = 이 단위 ÷ 윗단위</div>' + h;
  }
  function rankHtml(ds, title) {   // 아래 단위(동) 순위 — 누르면 그 동으로
    if (ds.length < 2) return ''; var one = function (lab, fn, unit) { var a = ds.map(function (d) { return [d, fn(d)]; }).filter(function (q) { return q[1] != null && isFinite(q[1]); }).sort(function (x, y) { return y[1] - x[1]; }).slice(0, 5);
      return a.length ? '<div class="r"><b>' + lab + '</b><span>' + a.map(function (q) { var d = q[0]; return '<button class="lk" data-godong="' + esc(d['코드'].slice(0, 5)) + '|' + esc(d['코드']) + '|' + esc(d['이름']) + '|' + (d['가운데'] || []).join(',') + '">' + esc(d['이름']) + '</button> ' + (Math.round(q[1] * 10) / 10).toLocaleString() + unit; }).join(' · ') + '</span></div>' : ''; };
    var pop = function (d) { return d['주민'] && d['주민']['계']; };
    return '<div class="cap">⬇ ' + esc(title) + ' — 누르면 그 동으로</div>' + one('주민 많은', function (d) { return pop(d); }, '명') +
      one('사고 많은(주민 1천 명당·해마다)', function (d) { var t = d['교통사고(TAAS 2016~2025)'], p = pop(d); return t && p > 300 ? t['계'] / 10 / p * 1000 : null; }, '') +
      one('사망자 많은(10년)', function (d) { var t = d['교통사고(TAAS 2016~2025)']; return t && t['사망자'] ? t['사망자'] : null; }, '명') +
      one('60세 이상 비율', function (d) { var p = d['주민']; return p && p['연령 비중%'] ? p['연령 비중%']['60 이상'] : null; }, '%') +
      one('가게 많은', function (d) { var g = d['가게(상가업소)']; return g ? g['계'] : null; }, '곳');
  }
  function ladderFill(it) {
    var top = $('m2dLad'), bot = $('m2dLadB'); if (!top || !TAPM || /^(ai|frn|ggc|rnl)$/.test(it.kind)) return;
    var m = TAPM, lv = ladLevel(it), steps = [['pt', '📍 지점', null]];
    var ck = cellAt(m); if (ck) steps.push(['cell', '🧊 250m 칸', { kind: 'g250', c: ck }]);
    var rr = RIS.length ? riAtM(m) : null; if (rr) steps.push(['ri', '🌾 ' + rr.name.split(' ').pop(), { kind: 'ri', r: rr }]);
    var d = dongAtM(m); if (d) steps.push(['dong', '🏘 ' + d.name, { kind: 'dong', d: d }]);
    if (d && d.k && POL2) { if (d._pb === undefined) d._pb = pbOfP(d.k, d.c); if (d._pb != null) steps.push(['pb', '👮 ' + POL2.pbox[d._pb][0], { kind: 'unit', u: { t: 'pb', id: d._pb } }]);
      var st = polOf(d.k); if (st && st.length) steps.push(['ps', '🚓 ' + st[0][1].replace(/경찰서$/, '서'), { kind: 'unit', u: { t: 'ps', id: st[0][0] } }]); }
    var gi = sggAt(m); if (gi >= 0) steps.push(['sgg', '🗂 ' + SGG[gi].g.name, { kind: 'unit', u: { t: 'sgg', id: gi } }]);
    if (!POL2) polLoad();
    if (steps.length < 3) return; LADS = steps;
    top.innerHTML = '<div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;font-size:12px;margin:0 0 6px">⬆ ' + steps.map(function (q, i) { return q[2] ? '<button data-lad="' + i + '" style="font-size:12px;padding:3px 7px;border-radius:999px;border:1px solid #94a3b8;background:' + (q[0] === lv ? '#1e3a8a;color:#fff' : 'transparent') + '">' + esc(q[1]) + '</button>' : '<span style="padding:3px 4px;' + (lv === 'pt' ? 'font-weight:800' : 'opacity:.7') + '">' + esc(q[1]) + '</span>'; }).join('<span style="opacity:.5">›</span>') + '<button class="ladx" data-cardx="1" aria-label="카드 닫기">닫기</button></div>'; var cdx = $('m2dCard'); if (cdx) cdx.classList.add('haslad');
    relFill(steps, m, it);
    if (!bot) return;
    // 윗단위 비교 · 아래 단위 순위 — profile.json 을 받은 뒤
    var cur = null, par = null, parName = '', kids = null, kidTitle = '';
    var li = steps.map(function (q) { return q[0]; }).indexOf(lv);
    if (lv === 'dong' && d && d.k) { cur = { ds: function () { var j = AIP[d.k.slice(0, 5)]; return j && j.dong && j.dong[d.k] ? [j.dong[d.k]] : []; }, gus: [d.k.slice(0, 5)] }; }
    else if (it.kind === 'unit') { cur = { ds: function () { return unitDongs(it.u); }, gus: unitGus(it.u) }; kids = cur; kidTitle = it.u.t === 'sgg' ? '이 시군구 안 동 순위' : it.u.t === 'ps' ? '이 경찰서 관할 동 순위' : '이 지구대 구역 동 순위'; }
    if (!cur) return;
    for (var i = li + 1; i < steps.length; i++) if (steps[i][2] && steps[i][2].kind === 'unit') { par = steps[i][2].u; parName = steps[i][1].replace(/^\S+ /, ''); break; }
    var gus = cur.gus.concat(par ? unitGus(par) : []).filter(function (g, i, a) { return a.indexOf(g) === i; }), need = gus.filter(function (g) { return !AIP[g]; });
    bot.innerHTML = '<p class="desc">윗단위 비교·아래 단위 순위를 계산하는 중…</p>';
    Promise.all(need.map(profP)).then(function () { var b2 = $('m2dLadB'); if (!b2 || $('m2dCard').querySelector('#m2dLadB') !== b2) return;
      var A = unitAgg(cur.ds()), h = '';
      if (par) { var Ap = unitAgg(unitDongs(par)); h += cmpHtml(A, Ap, parName); }
      if (kids) h += rankHtml(kids.ds(), kidTitle);
      b2.innerHTML = h; });
  }
  document.addEventListener('click', function (e) {
    if (e.target.closest('[data-cardx]')) { var x0 = $('m2dX'); if (x0) x0.click(); return; }
    var b = e.target.closest('[data-lad]'); if (b) { var q = LADS[+b.getAttribute('data-lad')]; if (q && q[2]) { if (sel) sel.it = q[2]; else sel = { x: -99, y: -99, r: 0, it: q[2] }; show(q[2]); } return; }
    var g = e.target.closest('[data-godong]'); if (g) { var a = g.getAttribute('data-godong').split('|'); goDong(a[0], a[1], a[2], a[3].split(',').map(Number)); } });

  // ---------- v2.13.0 🛣 전국 도로망(ITS 표준링크 · 0.5° 조각 a = 고속·국도 · b = 시도·국지도·지방도 · 크게 확대하면 시군구 파일로 시군도) ----------
  var RN = { idx: null, ip: null, ld: {}, L: [], src: '' }, RNC = { 1: '#1d4ed8', 2: '#7c3aed', 3: '#dc2626', 4: '#ea580c', 5: '#16a34a', 6: '#ca8a04', 7: '#64748b' }, RNW = { 1: 3.4, 2: 3, 3: 2.8, 4: 1.8, 5: 2.3, 6: 2.1, 7: 1.1 },
    RNG = { 1: '고속국도', 2: '도시고속', 3: '일반국도', 4: '특별·광역시도', 5: '국가지원지방도', 6: '지방도', 7: '시군도' };
  function rnTile(k) { if (RN.ld[k]) return; RN.ld[k] = 1;
    fetch('data/base/rn/' + k + '.json').then(function (r) { return r.json(); }).then(function (j) { j.links.forEach(function (l) { var c = l[3], x = 0, y = 0, pts = [], b = [1e12, 1e12, -1e12, -1e12];
      for (var i = 0; i < c.length; i += 2) { x += c[i]; y += c[i + 1]; var q = P(x / 1e4, y / 1e4); pts.push(q); if (q[0] < b[0]) b[0] = q[0]; if (q[1] < b[1]) b[1] = q[1]; if (q[0] > b[2]) b[2] = q[0]; if (q[1] > b[3]) b[3] = q[1]; }
      RN.L.push({ g: l[0], nm: j.names[l[1]], ms: l[2], pts: pts, bb: b }); }); RN.L.sort(function (a, b) { return b.g - a.g; }); draw(); }).catch(function () { RN.ld[k] = 0; }); }
  function rnVis() { var s = view.s, a0 = M(0, 0), a1 = M(cv.clientWidth, cv.clientHeight), o = RN.L.filter(function (l) { return (l.g <= 3 || s >= 0.01) && !(l.bb[2] < a0[0] || l.bb[0] > a1[0] || l.bb[3] < a0[1] || l.bb[1] > a1[1]); });
    if (s >= 0.03) ITSL.forEach(function (t) { if (t.rk === 7 && !(t.bb[2] < a0[0] || t.bb[0] > a1[0] || t.bb[3] < a0[1] || t.bb[1] > a1[1])) o.unshift({ g: 7, nm: t.nm, ms: t.ms, pts: t.pts, bb: t.bb }); }); return o; }
  function drawRnet(dark) {
    if (!on.rnet) return; if (!RN.idx) { if (!RN.ip) RN.ip = fetch('data/base/rn/index.json').then(function (r) { return r.json(); }).then(function (j) { RN.idx = j; RN.src = j.source; draw(); }).catch(function () {}); return; }
    var s = view.s; if (s < 0.0015) return; var v = viewLL();
    for (var x = Math.floor(v[0] * 2) - 1; x <= Math.floor(v[2] * 2); x++) for (var y = Math.floor(v[1] * 2) - 1; y <= Math.floor(v[3] * 2); y++) { if (RN.idx.tiles['a_' + x + '_' + y]) rnTile('a_' + x + '_' + y); if (s >= 0.01 && RN.idx.tiles['b_' + x + '_' + y]) rnTile('b_' + x + '_' + y); }
    if (s >= 0.03) rIdx().forEach(function (g) { var bx = g.box; if (!(g.bytes || {}).itsl || bx[2] < v[0] || bx[0] > v[2] || bx[3] < v[1] || bx[1] > v[3]) return; slLoad(g.gu); });
    var k = s >= 0.05 ? 1.5 : s >= 0.01 ? 1.1 : 0.8; ctx.save(); ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    rnVis().forEach(function (l) { ctx.strokeStyle = RNC[l.g]; ctx.globalAlpha = l.g === 7 ? 0.7 : 0.9; ctx.lineWidth = RNW[l.g] * k; path(l.pts); ctx.stroke(); });
    ctx.restore();
  }
  function rnAt(x, y) { var best = null, bd = 9; rnVis().forEach(function (l) { for (var i = 1; i < l.pts.length; i++) { var a = S(l.pts[i - 1]), b = S(l.pts[i]), dx = b[0] - a[0], dy = b[1] - a[1], t = Math.max(0, Math.min(1, ((x - a[0]) * dx + (y - a[1]) * dy) / (dx * dx + dy * dy || 1))), d = Math.hypot(a[0] + t * dx - x, a[1] + t * dy - y); if (d < bd) { bd = d; best = l; } } }); return best; }

  // ---------- v2.13.0 🚙 서울 시간대 교통량(서울시 교통량조사 · 조사 지점 전부) ----------
  var VOLS = null, VOLSP = null;
  function drawVols(dark) {
    if (!on.volp) return; if (!VOLS) { if (!VOLSP) VOLSP = fetch('data/traffic-vol-seoul.json').then(function (r) { return r.json(); }).then(function (j) { j.spots.forEach(function (v) { v.p = P(v.lon, v.lat); var t = 0; (v.wd || v.sa || []).forEach(function (q) { t += q[0] + q[1]; }); v.day = t; }); VOLS = j; draw(); }).catch(function () {}); return; }
    var mx = Math.max.apply(null, VOLS.spots.map(function (v) { return v.day; }).concat([1]));
    VOLS.spots.forEach(function (v) { var r = 5 + 13 * Math.sqrt(v.day / mx); dot(v.p, r, 'rgba(14,165,233,.75)', '#fff', { kind: 'vols', v: v });
      if (view.s >= 0.02) label([v.p[0], v.p[1] - (r + 9) / view.s], v.name, 10, dark ? '#e2e8f0' : '#0c4a6e', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
  }
  function volsCard(v) {
    var sum = function (a) { return a ? a.map(function (q) { return q[0] + q[1]; }) : null; }, wd = sum(v.wd), sa = sum(v.sa), su = sum(v.su), tot = function (a) { return a ? a.reduce(function (x, y) { return x + y; }, 0) : 0; };
    var pk = wd ? wd.indexOf(Math.max.apply(null, wd)) : -1, h = '<h3>🚙 ' + esc(v.name) + ' <small>(' + esc(v.id) + ')</small></h3>';
    h += row('하루 대수', (wd ? '평일 ' + tot(wd).toLocaleString() : '') + (sa ? ' · 토 ' + tot(sa).toLocaleString() : '') + (su ? ' · 일 ' + tot(su).toLocaleString() : '') + '대 <em>(두 방향 합)</em>');
    if (pk >= 0) h += row('평일 가장 많을 때', pk + '시 ' + wd[pk].toLocaleString() + '대/시 · 새벽 4시 ' + wd[4].toLocaleString() + '대/시');
    h += row('조사 차로', '방향1 ' + v.lanes[0] + ' · 방향2 ' + v.lanes[1]);
    if (v.wd) h += '<div class="cap">평일 시간대(대/시 · 방향1 진한색 · 0~23시)</div>' + bar(v.wd.map(function (q) { return q[0]; }), '#0369a1', LB_H24) + '<div class="cap">평일 시간대 — 방향2</div>' + bar(v.wd.map(function (q) { return q[1]; }), '#38bdf8', LB_H24);
    if (sa) h += '<div class="cap">토요일(두 방향 합)</div>' + bar(sa, '#a855f7', LB_H24); if (su) h += '<div class="cap">일요일(두 방향 합)</div>' + bar(su, '#db2777', LB_H24);
    return h + '<p class="desc">' + esc(VOLS.note) + ' · ' + esc(VOLS.days) + '</p>' + src(VOLS.source);
  }
  // v2.13.0 🛣 고속도로 영업소 시간대 교통량(한국도로공사 trafficIc 를 매시간 모은 것)
  var EXV = null, EXVP = null;
  function exHrs(u) { var a = []; for (var i = 0; i < 24; i++) { var q = u.h[String(i)]; a.push(q ? q[0] + q[1] : 0); } return a; }
  function drawExv(dark) {
    if (!on.exv) return; if (!EXV) { if (!EXVP) EXVP = fetch('data/traffic-ex.json').then(function (r) { return r.json(); }).then(function (j) { j.units.forEach(function (u) { u.p = P(u.lon, u.lat); u.tot = exHrs(u).reduce(function (a, b) { return a + b; }, 0); }); EXV = j; draw(); }).catch(function () {}); return; }
    var mx = Math.max.apply(null, EXV.units.map(function (u) { return u.tot; }).concat([1]));
    EXV.units.forEach(function (u) { var r = 4 + 12 * Math.sqrt(u.tot / mx); dot(u.p, r, 'rgba(29,78,216,.75)', '#fff', { kind: 'exv', u: u });
      if (view.s >= 0.01) label([u.p[0], u.p[1] - (r + 9) / view.s], u.name, 10, dark ? '#e2e8f0' : '#1e3a8a', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
  }
  function exvCard(u) {
    var hs = Object.keys(u.h).map(Number).sort(function (a, b) { return a - b; }), ins = [], outs = [];
    for (var i = 0; i < 24; i++) { var q = u.h[String(i)]; ins.push(q ? q[0] : 0); outs.push(q ? q[1] : 0); }
    var h = '<h3>🛣 ' + esc(u.name) + ' 영업소 <small>(' + esc(u.route || '') + ')</small></h3>' + row('모은 시각', hs.length + '시간 — ' + hs.map(function (x) { return x + '시'; }).join(' · ') + ' <em>(이 API 는 지난 시각을 주지 않아 매시간 모은 만큼)</em>') +
      row('모은 시간 합', u.tot.toLocaleString() + '대(입구+출구)') + (u.hp != null ? row('하이패스', u.hp + '%') : '') + (u.big != null ? row('4~6종(대형·화물)', u.big + '%') : '');
    if (hs.length > 1) h += '<div class="cap">시간대 — 입구(대/시)</div>' + bar(ins, '#1d4ed8', LB_H24) + '<div class="cap">시간대 — 출구(대/시)</div>' + bar(outs, '#60a5fa', LB_H24);
    else h += row('입구 · 출구', ins[hs[0]].toLocaleString() + ' · ' + outs[hs[0]].toLocaleString() + '대 (' + hs[0] + '시)');
    return h + '<p class="desc">' + esc(EXV.note) + '</p>' + src(EXV.source);
  }
  // v2.15.0 👥 인구감소지역 생활인구(통계청) · 🚇 대구 도시철도 하차
  var LPOP = null, LPOPP = null, MSUB = null, MSUBP = null;
  function lpLoad2() { if (!LPOPP) LPOPP = fetch('data/livepop.json').then(function (r) { return r.json(); }).then(function (j) { LPOP = j; draw(); }).catch(function () {}); return LPOPP; }
  function lpopOf(G) { if (!LPOP) return null; for (var c in LPOP.gu) { var L = LPOP.gu[c]; if (SIDO_FULL[c.slice(0, 2)] === G.g.sido && L.sgname === G.g.name) return L; } return null; }
  function drawLpop(dark) {
    if (!on.lpop) return; if (!LPOP) { lpLoad2(); return; }
    SGG.forEach(function (G) { var L = G._lp === undefined ? (G._lp = lpopOf(G)) : G._lp; if (!L || !L.reg) return; var ms = Object.keys(L.m).sort(), v = L.m[ms[ms.length - 1]], r = v.tot / L.reg, t = Math.min(1, Math.log(Math.max(1, r)) / Math.log(20));
      ctx.save(); ctx.globalAlpha = 0.18 + 0.5 * t; ctx.fillStyle = '#7c3aed'; G.rings.forEach(function (rg) { path(rg); ctx.closePath(); ctx.fill(); }); ctx.restore();
      if (view.s < 0.03) label(G.c, G.g.name + ' ' + r.toFixed(1) + '배', 11, '#fff', 'rgba(76,29,149,.85)'); });
  }
  var BUSD = null, BUSDP = null;
  function drawBusd(dark) {
    if (!on.busd) return; if (!BUSD) { if (!BUSDP) BUSDP = fetch('data/bus-incheon.json').then(function (r) { return r.json(); }).then(function (j) { j.stops.forEach(function (b) { b.p = P(b[2], b[3]); b.t = b[4] + b[5]; }); BUSD = j; draw(); }).catch(function () {}); return; }
    if (view.s < 0.01) return; var mx = Math.max.apply(null, BUSD.stops.map(function (b) { return b.t; }).concat([1])), W0 = cv.clientWidth, H0 = cv.clientHeight;
    BUSD.stops.forEach(function (b) { var q = S(b.p); if (q[0] < -20 || q[1] < -20 || q[0] > W0 + 20 || q[1] > H0 + 20) return; dot(b.p, 3 + 9 * Math.sqrt(b.t / mx), 'rgba(22,163,74,.75)', '#fff', { kind: 'busd', s: b }); });
  }
  // v2.16.0 🌏 읍면동 외국인주민(행안부 2024) · 🏨 서울 외국인 관광숙박 · 🏠 외국인 부동산(시군구)
  var FDONG = null, FDONGP = null, FLODGE = null, FLODGEP = null, FEST = null, FESTP = null;
  var FSIDO = null, FSIDOP = null, FRCUR = null;
  function frnAgain() { var c = $('m2dCard'); if (FRCUR && c && c.classList.contains('on') && /🌏 외국인 —/.test((c.querySelector('h3') || {}).textContent || '')) show({ kind: 'frn', gu: FRCUR }); }
  function fsLoad() { if (!FSIDOP) FSIDOP = fetch('data/foreign-sido.json').then(function (r) { return r.json(); }).then(function (j) { FSIDO = j; frnAgain(); }).catch(function () {}); return FSIDOP; }
  function fdLoad() { if (!FLODGEP) FLODGEP = fetch('data/lodging-seoul.json').then(function (r) { return r.json(); }).then(function (j) { j.pts.forEach(function (q) { q.p = P(q[1], q[0]); }); FLODGE = j; draw(); }).catch(function () {});
    if (!FDONGP) FDONGP = fetch('data/foreign-dong.json').then(function (r) { return r.json(); }).then(function (j) { FDONG = j; draw(); if (sel && sel.it && sel.it.kind === 'dong') show(sel.it); }).catch(function () {}); return FDONGP; }
  function festLoad() { if (!FESTP) FESTP = fetch('data/foreign-estate.json').then(function (r) { return r.json(); }).then(function (j) { FEST = j; frnAgain(); }).catch(function () {}); return FESTP; }
  function fdRows(k8) {
    if (!k8) return ''; if (!FDONG) { fdLoad(); return ''; } var f = FDONG.dong[k8]; if (!f) return '';
    var n = function (v) { return v == null ? '*' : v.toLocaleString(); }, h = row('외국인주민(이 동 · 2024.11)', '<b>' + n(f.t) + '명</b> — 한국국적 없음 ' + n(f.nf) + ' · 귀화 ' + n(f.n) + ' · 자녀 ' + n(f.c));
    h += row('한국국적 없는 사람', '근로자 ' + n(f.w) + ' · 결혼이민 ' + n(f.m) + ' · 유학생 ' + n(f.s) + ' · 동포 ' + n(f.k) + ' · 기타 ' + n(f.e) + ' <em>(* = 작아서 가린 값)</em>');
    if (f.mc) h += row('다문화가구원', n(f.mc[0]) + '명 — 한국인 배우자 ' + n(f.mc[1]) + ' · 결혼이민·귀화 ' + n(f.mc[2]) + ' · 자녀 ' + n(f.mc[3]) + ' · 기타 동거인 ' + n(f.mc[4]));
    if (!MBK[k8.slice(0, 5)]) mbLoad(k8.slice(0, 5));
    var STg = STK[k8.slice(0, 5)]; if (!STg) stLoad(k8.slice(0, 5)); else if (STg.dong && STg.dong[k8]) { var sv = STg.dong[k8]; h += row('숙박시설(이 동)', sv.map(function (n, i) { return n ? esc(STY[i][1]) + ' ' + n : ''; }).filter(Boolean).join(' · ') + ' <em>(영업·휴업 · 지방행정인허가 2025-11)</em>'); }
    var MBg = MBK[k8.slice(0, 5)]; if (MBg && MBg.dong && MBg.dong[k8]) h += row('외국인관광 도시민박(이 동)', MBg.dong[k8] + '곳 <em>(영업·휴업 · 행안부 인허가 2026-10)</em>');
    var JMg = jgJmDong(k8); if (JMg) h += jmRow(JMg, jgGroups());
    var JDg = jgDong(k8); if (JDg) h += row('공시지가(대지 ㎡당 중앙값)', '<b>' + wonM2(JDg[0]) + '원</b> · 평당 ' + wonM2(JDg[0] * 3.305785) + '원 · 대지 ' + JDg[1].toLocaleString() + '필지 <em>(' + esc(jgYear()) + '년 1월 1일 · 시세 아님)</em>');
    if (FLODGE && FLODGE.dong[k8]) { var L = FLODGE.dong[k8]; h += row('외국인 관광숙박(서울)', Object.keys(L).map(function (q) { return esc(q || '기타') + ' ' + L[q]; }).join(' · ') + '곳 <em>(영업 중 · 투숙 인원은 비공개)</em>'); }
    return h;
  }
  // v2.23.0 외국인 현황 — 소유자 「외국인 현황도 시군구·읍면동별로 표시할 수 있으면 모두」 → 무엇을(비율·인원·유형·5년 변화) 고르고, 멀리 = 시군구(2024·2019) · 가까이 = 읍면동(2024)
  var FDM = 'r'; try { FDM = localStorage.getItem('tg_map2d_fdm') || 'r'; } catch (e) {}
  var FDMS = { r: ['외국인주민 비율', null, null, '#0e7490'], t: ['외국인주민 수', 't', 'tot', '#0e7490'], w: ['외국인근로자', 'w', 'work', '#b45309'], m: ['결혼이민자', 'm', 'marr', '#be185d'], s: ['유학생', 's', 'stud', '#4338ca'], k: ['외국국적동포', 'k', 'kor', '#15803d'], n: ['귀화(한국국적 취득)', 'n', 'nat', '#7c3aed'], c: ['외국인주민 자녀', 'c', 'kid', '#0369a1'], d: ['5년 변화(2019→2024 · 시군구)', null, null, '#dc2626'] };
  var FDSG = null;
  function fdSgg() {   // foreign.json(시군구 · 2024·2019) → 시군구 경계(SGG) 번호마다 · 일반구가 없어 「시 전체」인 값은 한 번만
    if (FDSG || !FRN || !SGG.length) return FDSG; var o = {}, IX = {}; rIdx().forEach(function (g) { IX[g.gu] = g; });
    Object.keys(FRN.gu).forEach(function (k) { var g = IX[k], F2 = FRN.gu[k]; if (!g || !F2['2024']) return; var si = -1; SGG.forEach(function (q, i) { if (si < 0 && q.g.sido === SIDO_FULL[g.sido] && (g.name === q.g.name || g.name.indexOf(q.g.name) === 0)) si = i; }); if (si < 0) return;
      var whole = /시 전체/.test(F2.src || ''), A = o[si] = o[si] || { a: {}, b: {}, whole: false, nat: F2.nat || null, gus: [] }; if (A.whole) return; A.gus.push(k);
      if (whole) { A.a = Object.assign({}, F2['2024']); A.b = Object.assign({}, F2['2019'] || {}); A.whole = true; A.nat = F2.nat || A.nat; return; }
      ['2024', '2019'].forEach(function (y, yi) { var T = yi ? A.b : A.a, V = F2[y] || {}; Object.keys(V).forEach(function (q) { if (typeof V[q] === 'number') T[q] = (T[q] || 0) + V[q]; }); });
      if (A.gus.length > 1) A.nat = null; });
    FDSG = o; return o; }
  function fdVal(v, mode, pop) { var M0 = FDMS[mode]; if (!v) return null; if (mode === 'r') return pop ? (v.t != null ? v.t : v.tot) / pop : null; var x = v[M0[1]] != null ? v[M0[1]] : v[M0[2]]; return x == null ? null : x; }
  var FDMX = {};
  function fdMax(mode) { if (FDMX[mode]) return FDMX[mode]; var a = []; Object.keys(FDONG.dong).forEach(function (k) { var x = FDONG.dong[k][FDMS[mode][1]]; if (x) a.push(x); }); a.sort(function (p, q) { return p - q; }); return (FDMX[mode] = a[Math.floor(a.length * 0.97)] || 1); }
  function fdNum(x) { return x >= 1e4 ? (x / 1e4).toFixed(x >= 1e5 ? 0 : 1) + '만' : Math.round(x).toLocaleString(); }
  function drawFdong(dark) {
    if (!on.fdong) return; if (!FDONG) { fdLoad(); return; } var M0 = FDMS[FDM] || FDMS.r, a0 = M(0, 0), a1 = M(cv.clientWidth, cv.clientHeight);
    if (view.s < 0.012 || FDM === 'd') { var SG = fdSgg(); if (!SG) return; var vals = {}, mx = 0;
      Object.keys(SG).forEach(function (i) { var A = SG[i], v; if (FDM === 'r') v = A.a.pop ? A.a.tot / A.a.pop : null; else if (FDM === 'd') v = A.b.tot ? A.a.tot / A.b.tot - 1 : null; else v = A.a[M0[2]]; if (v == null) return; vals[i] = v; if (FDM !== 'r' && FDM !== 'd') mx = Math.max(mx, v); });
      Object.keys(vals).forEach(function (i) { var G = SGG[i], v = vals[i], t, col = M0[3]; if (FDM === 'r') t = Math.min(1, Math.sqrt(v / 0.12)); else if (FDM === 'd') { t = Math.min(1, Math.abs(v) / 0.5); col = v >= 0 ? '#dc2626' : '#2563eb'; } else t = Math.min(1, Math.sqrt(v / (mx || 1)));
        ctx.save(); ctx.globalAlpha = 0.1 + 0.62 * t; ctx.fillStyle = col; G.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fill(); }); ctx.restore();
        if (view.s >= 0.0035 && G.g.box && (G.g.box[2] - G.g.box[0]) * view.s > 62) { var A = SG[i], tx = FDM === 'r' ? (v * 100).toFixed(1) + '%' : FDM === 'd' ? (v >= 0 ? '+' : '') + Math.round(v * 100) + '%' : fdNum(v); var nt = A.nat && A.nat[0] && view.s >= 0.006 && FDM !== 'd' ? ' · ' + A.nat[0][0] : '';
          label(G.c, G.g.name.replace(/(시|군|구)$/, '') + ' ' + tx + nt, 10.5, '#fff', 'rgba(15,23,42,.72)'); } });
      return; }
    allDong().forEach(function (d) { if (!d.k || !d.polys || !d.box || d.box[1] < a0[0] || d.box[0] > a1[0] || d.box[3] < a0[1] || d.box[2] > a1[1]) return; var f = FDONG.dong[d.k], p = d.pop && d.pop.tot; if (!f) return;
      var v = fdVal(f, FDM, p); if (v == null) return; var t = FDM === 'r' ? Math.min(1, Math.sqrt(v / 0.3)) : Math.min(1, Math.sqrt(v / fdMax(FDM)));
      ctx.save(); ctx.globalAlpha = 0.12 + 0.6 * t; ctx.fillStyle = M0[3]; d.polys.forEach(function (Pg) { path(Pg[0]); ctx.fill(); }); ctx.restore();
      if (view.s >= 0.02) label([d.c[0], d.c[1] + 14 / view.s], FDM === 'r' ? (v * 100).toFixed(1) + '%' : fdNum(v) + '명', 10, '#fff', hexA(M0[3], 0.88)); });
  }
  function fdLegend() { if (!on.fdong) return '';
    return '<div class="lg-btns">' + Object.keys(FDMS).map(function (k) { return '<button data-fdm="' + k + '" class="' + (k === FDM ? 'on' : '') + '">' + FDMS[k][0] + '</button>'; }).join('') + '</div>' +
      (FDM === 'd' ? li('#dc2626', '늘었다', 'box') + li('#2563eb', '줄었다', 'box') : li(hexA((FDMS[FDM] || FDMS.r)[3], 0.7), '진할수록 ' + (FDMS[FDM] || FDMS.r)[0] + ' 많음', 'box')) +
      '<small class="lg-n">멀리 보면 시군구(행정안전부 외국인주민 현황 2024 · 2019 · 글자 옆 = 가장 많은 국적(법무부 2025 말)) · 가까이 보면 읍면동(2024.11.1) · 3개월 넘게 사는 사람(거주) — 그 시각 머무는 사람은 「🌏 지금 머무는 외국인 250m(서울)」 · 「*」로 가린 작은 동 값은 빈칸</small>'; }
  var MBK = {}, RLOADMB = {};
  function mbLoad(gu) { if (RLOADMB[gu]) return; RLOADMB[gu] = 1; rGet(gu, 'minbak.json').then(function (j) { j.pts.forEach(function (q) { q.p = P(q[1], q[0]); }); MBK[gu] = j; draw(); }).catch(function () { RLOADMB[gu] = 2; }); }
  function drawMinbak(dark) {
    if (!on.minbak || view.s < 0.004) return; var v = viewLL(), W0 = cv.clientWidth, H0 = cv.clientHeight;
    rIdx().forEach(function (g) { var x = g.box; if (!(g.bytes || {}).minbak || x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return; mbLoad(g.gu); });
    Object.keys(MBK).forEach(function (gu) { var j = MBK[gu]; j.pts.forEach(function (q) { var sx = S(q.p); if (sx[0] < -10 || sx[1] < -10 || sx[0] > W0 + 10 || sx[1] > H0 + 10) return;
      dot(q.p, view.s >= 0.02 ? 4 : 3, q[3] ? '#94a3b8' : '#ec4899', '#fff', { kind: 'minbak', s: q, m: j }); }); });
  }
  function drawFlodge(dark) {
    if (!on.flodge) return; if (!FLODGE) { if (!FLODGEP) FLODGEP = fetch('data/lodging-seoul.json').then(function (r) { return r.json(); }).then(function (j) { j.pts.forEach(function (q) { q.p = P(q[1], q[0]); }); FLODGE = j; draw(); }).catch(function () {}); return; }
    if (view.s < 0.01) return; var W0 = cv.clientWidth, H0 = cv.clientHeight;
    FLODGE.pts.forEach(function (q) { if (q[3] !== '관광숙박업') return; var sx = S(q.p); if (sx[0] < -10 || sx[1] < -10 || sx[0] > W0 + 10 || sx[1] > H0 + 10) return; dot(q.p, q[3] === '관광숙박업' ? 4.5 : 3, q[3] === '관광숙박업' ? '#be185d' : '#f472b6', '#fff', { kind: 'flodge', s: q }); });
  }
  function drawMsub(dark) {
    if (!on.msub) return; if (!MSUB) { if (!MSUBP) MSUBP = fetch('data/metro-daegu.json').then(function (r) { return r.json(); }).then(function (j) { j.stations.forEach(function (s2) { s2.p = P(s2[1], s2[2]); }); MSUB = j; draw(); }).catch(function () {}); return; }
    var mx = Math.max.apply(null, MSUB.stations.map(function (s2) { return s2[3]; }).concat([1]));
    MSUB.stations.forEach(function (s2) { dot(s2.p, 4 + 10 * Math.sqrt(s2[3] / mx), 'rgba(234,88,12,.8)', '#fff', { kind: 'msub', s: s2 }); if (view.s >= 0.02) label([s2.p[0], s2.p[1] - 16 / view.s], s2[0], 10, dark ? '#e2e8f0' : '#7c2d12', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); });
  }
  function drawUnits(dark) {
    var W0 = cv.clientWidth, H0 = cv.clientHeight;
    if (on.usgg && SGG.length) { SGG.forEach(function (G, i) { ctx.save(); ctx.globalAlpha = 0.17; ctx.fillStyle = 'hsl(' + ((i * 137.508) % 360).toFixed(0) + ',62%,50%)'; G.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fill(); }); ctx.restore(); });
      SGG.forEach(function (G) { G.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.setLineDash([]); ctx.lineWidth = 2.2; ctx.strokeStyle = dark ? 'rgba(226,232,240,.75)' : 'rgba(30,41,59,.7)'; ctx.stroke(); }); });
      if (view.s >= 0.05) SGG.forEach(function (G) { var q = S(G.c); if (q[0] > -60 && q[1] > -20 && q[0] < W0 + 60 && q[1] < H0 + 20) label(G.c, G.g.name, 13, dark ? '#e2e8f0' : '#1e293b', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); }); }
    if (on.upb) { if (!POL2) { polLoad(); return; } var a0 = M(0, 0), a1 = M(W0, H0);
      allDong().forEach(function (d) { if (!d.k || !d.polys || !d.box || d.box[1] < a0[0] || d.box[0] > a1[0] || d.box[3] < a0[1] || d.box[2] > a1[1]) return; if (d._pb === undefined) d._pb = pbOfP(d.k, d.c); if (d._pb == null) return;
        ctx.save(); ctx.globalAlpha = 0.28; ctx.fillStyle = polCol(d._pb * 3 + 1); d.polys.forEach(function (Pg) { path(Pg[0]); ctx.fill(); }); ctx.restore(); });
      if (view.s >= 0.006) POL2.pbox.forEach(function (b, i) { var q = S(b.p); if (q[0] < -40 || q[1] < -40 || q[0] > W0 + 40 || q[1] > H0 + 40) return; dot(b.p, b[1] ? 4 : 5, polCol(i * 3 + 1), '#fff', { kind: 'pbx', b: b });
        if (view.s >= 0.012) label([b.p[0], b.p[1] - 13 / view.s], b[0] + (b[1] ? '파' : '지'), 10, dark ? '#e2e8f0' : '#0f172a', dark ? 'rgba(15,22,36,.7)' : 'rgba(255,255,255,.85)'); }); }
  }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-aiu]'); if (!b) return; var a = b.getAttribute('data-aiu').split('|'); show({ kind: 'ai', u: { t: a[0], id: +a[1] } }); });
  function drawPolice(dark) {
    if (!on.jurk && !on.pbox) return; if (!POL2) { polLoad(); return; } var W0 = cv.clientWidth, H0 = cv.clientHeight;
    if (on.jurk) { var DL = (DONG || []).concat(RDONG || []);
      var a0 = M(0, 0), a1 = M(W0, H0);
      DL.forEach(function (d) { if (!d.k || !d.polys || !d.box || d.box[1] < a0[0] || d.box[0] > a1[0] || d.box[3] < a0[1] || d.box[2] > a1[1]) return; var st = polOf(d.k); if (!st || !st.length) return; var col = st.length > 1 ? 'rgba(100,116,139,.32)' : polCol(st[0][0]);
        ctx.save(); ctx.globalAlpha = st.length > 1 ? 1 : 0.22; ctx.fillStyle = col; d.polys.forEach(function (Pg) { path(Pg[0]); ctx.fill(); }); ctx.restore(); });
      if (view.s >= 0.004) POL2.stations.forEach(function (s2) { if (!s2.p) return; var q = S(s2.p); if (q[0] < -40 || q[1] < -40 || q[0] > W0 + 40 || q[1] > H0 + 40) return;
        ctx.fillStyle = polCol(s2[0]); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2; ctx.beginPath(); ctx.rect(q[0] - 6, q[1] - 6, 12, 12); ctx.fill(); ctx.stroke();
        if (view.s >= 0.012) label([s2.p[0], s2.p[1] - 14 / view.s], s2[1].replace(/경찰서$/, '서'), 11, dark ? '#e2e8f0' : '#0f172a', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)');
        hit.push({ x: q[0], y: q[1], r: 10, it: { kind: 'pst', s: s2 } }); }); }
    if (on.pbox && view.s >= 0.02) POL2.pbox.forEach(function (b) { dot(b.p, b[1] ? 3.6 : 4.6, b[1] ? '#0284c7' : '#1d4ed8', '#fff', { kind: 'pbx', b: b }); });
  }
  function pstCard(s2) {
    var nd = 0, mix = 0; Object.keys(POL2.dong).forEach(function (k) { var o = polLab(POL2.labels[POL2.dong[k]]); if (o.main.indexOf(s2) >= 0) { nd++; if (o.main.length > 1 || o.extra.length) mix++; } });
    var bx = POL2.pbox.filter(function (b) { return b[6] === s2[0]; });
    return '<h3>🚓 ' + esc(s2[1]) + '</h3>' + row('대표번호', s2[4] ? '<a href="tel:' + esc(s2[4]) + '">' + esc(s2[4]) + '</a>' : '<em>(청사 좌표·번호 원자료 없음)</em>') + row('시도청', esc(s2[5])) + row('관할 행정동', nd + '곳' + (mix ? ' (그중 ' + mix + '곳은 다른 서와 번지로 나눠 맡음 — 「경계」)' : '')) +
      row('지구대·파출소', bx.length ? bx.length + '곳 — ' + bx.map(function (b) { return esc(b[0]) + (b[1] ? '파출소' : '지구대'); }).join(' · ') : '자료에 없음') +
      '<p class="desc">관할은 「경찰청과 그 소속기관 직제 시행규칙」 별표2(2026.8.31 시행)를 행정동 경계에 붙인 <b>행정동 단위 근사</b>다 — 번지로 나뉜 동은 「경계」. 지구대·파출소 관할 경계는 공개 자료가 없다.</p>' + src(POL2.source);
  }
  function pbxCard(b) { var s2 = POL2.byI[b[6]];
    return '<h3>👮 ' + esc(b[0]) + (b[1] ? ' 파출소' : ' 지구대') + '</h3>' + row('경찰서', esc(s2 ? s2[1] : b[2]) + (s2 ? ' · <a href="tel:' + esc(s2[4]) + '">' + esc(s2[4]) + '</a> <em>(서 대표번호)</em>' : '')) + row('주소', esc(b[5])) +
      '<p class="desc">지구대·파출소 직통번호와 관할 경계는 공개 자료에 없다 — 대표번호는 경찰서 번호다. 자리는 주소를 브이월드로 좌표화한 것.</p>' + src(POL2.source); }
  function polRows(k8, c) {   // 동 카드에 — 관할 경찰서 · 가장 가까운 지구대(근사)
    if (!POL2) { polLoad(); return ''; } var st = polOf(k8), h = '';
    if (st && st.length) h += row('관할 경찰서', st.map(function (s2) { return esc(s2[1]) + ' <a href="tel:' + esc(s2[4]) + '">' + esc(s2[4]) + '</a>'; }).join(' · ') + (st.length > 1 ? ' <em>(번지로 나눠 맡음 — 경계)</em>' : '') + (st.extra && st.extra.length ? ' <em>(일부 번지는 ' + st.extra.map(function (x) { return esc(x[1]); }).join('·') + ')</em>' : '') + ' <em>(별표2 · 행정동 단위)</em>');
    var nb = c && pboxNear(c); if (nb) h += row('가까운 지구대·파출소', esc(nb.b[0]) + (nb.b[1] ? '파출소' : '지구대') + ' ' + (nb.d >= 1000 ? (nb.d / 1000).toFixed(1) + 'km' : Math.round(nb.d) + 'm') + ' <em>(동 가운데에서 · 관할이 아니라 거리 — 관할 경계는 비공개)</em>');
    return h; }

  // ---------- v2.38.0 🏛 행정 관할 — 교육지원청 · 세무서 · 지방법원·지원(data/juris.json · tools/region/juris-bake.py) ----------
  //   교육지원청·법원 = 법령 별표의 시군구 관할 그대로 · 세무서 = 국세청이 법정동·읍면으로 적은 관할을 행정동에 붙인 근사(한 동이 둘에 20% 넘게 걸치면 「나뉨」)
  var JRS = null, JRSP = null, JRSM = 'tax';
  try { JRSM = localStorage.getItem('tg_map2d_jrs') || 'tax'; } catch (e) {}
  if (!/^(edu|tax|court)$/.test(JRSM)) JRSM = 'tax';
  var JRSK = { edu: ['🎒 교육지원청', '교육지원청'], tax: ['🧾 세무서', '세무서'], court: ['⚖ 법원(지방법원·지원)', '법원'] };
  function jrsLoad() { if (JRSP) return JRSP; JRSP = fetch('data/juris.json').then(function (r) { return r.json(); }).then(function (j) { JRS = j; draw(); if (document.body.classList.contains('legon')) legend(); }).catch(function () { JRS = null; }); return JRSP; }
  function jrsOfK(K, k8) { if (!k8) return null; var v = K.d[k8]; if (v != null) return v; v = K.g5[k8.slice(0, 5)]; return v == null || v < 0 ? null : v; }
  function jrsAt(kind, m) { if (!JRS) return null; var K = JRS.kinds[kind], d = dongAtM(m), v = d && d.k ? jrsOfK(K, d.k) : null; if (v != null) return v;
    var i = sggAt(m); if (i < 0) return null; var ky = SGG[i].g.sido + '|' + SGG[i].g.name; v = K.sg[ky]; if (v === -1 && K.sc && K.sc[ky]) return { c: K.sc[ky] }; return v == null || v < 0 ? null : v; }
  function jrsShort(kind, n) { if (kind === 'edu') return n.replace(/^(서울특별시|부산광역시|대구광역시|인천광역시|대전광역시|울산광역시|경기도|강원특별자치도|충청북도|충청남도|전북특별자치도|경상북도|경상남도|전남광주통합특별시)/, '').replace(/\(.*\)$/, '');
    if (kind === 'court') return n.replace('지방법원 ', '지법 ').replace(/지방법원$/, '지법'); return n; }
  function jrsCol(kind, i) { return polCol(i * (kind === 'tax' ? 7 : kind === 'edu' ? 5 : 11) + 3); }
  function drawJrs(dark) {
    if (!on.juris) return; if (!JRS) { jrsLoad(); return; } var K = JRS.kinds[JRSM]; if (!K || !SGG.length) return;
    var W0 = cv.clientWidth, H0 = cv.clientHeight, a0 = M(0, 0), a1 = M(W0, H0), LP = {};
    function put(i, c, w) { var o = LP[i] || (LP[i] = [0, 0, 0]); o[0] += c[0] * w; o[1] += c[1] * w; o[2] += w; }
    SGG.forEach(function (G, gi) { var v = K.sg[G.g.sido + '|' + G.g.name]; if (v == null) return;
      ctx.save(); ctx.globalAlpha = v < 0 ? 0.10 : 0.22; ctx.fillStyle = v < 0 ? '#64748b' : jrsCol(JRSM, v); G.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fill(); }); ctx.restore();
      if (v >= 0) put(v, G.c, 1); });
    allDong().forEach(function (d) { if (!d.k || !d.polys || !d.box) return; var v = K.d[d.k]; if (v == null) return; if (!Array.isArray(v) && d.c) put(v, d.c, 0.2);
      if (d.box[1] < a0[0] || d.box[0] > a1[0] || d.box[3] < a0[1] || d.box[2] > a1[1]) return;
      ctx.save(); ctx.globalAlpha = Array.isArray(v) ? 0.30 : 0.30; ctx.fillStyle = Array.isArray(v) ? 'rgba(100,116,139,.95)' : jrsCol(JRSM, v); d.polys.forEach(function (Pg) { path(Pg[0]); ctx.fill(); }); ctx.restore(); });
    if (view.s < 0.0035) return;
    Object.keys(LP).forEach(function (i) { var o = LP[i]; if (!o[2]) return; var c = [o[0] / o[2], o[1] / o[2]], q = S(c); if (q[0] < -60 || q[1] < -20 || q[0] > W0 + 60 || q[1] > H0 + 20) return;
      label(c, jrsShort(JRSM, K.o[i][0]), view.s < 0.01 ? 10 : 12, dark ? '#f1f5f9' : '#0f172a', dark ? 'rgba(15,22,36,.72)' : 'rgba(255,255,255,.88)'); });
  }
  function jrsLegend() {
    if (!JRS) { jrsLoad(); return ['🏛 행정 관할', '<small class="lg-n">받는 중…</small>']; } var K = JRS.kinds[JRSM];
    return ['🏛 행정 관할', '<div class="lg-btns">' + Object.keys(JRSK).map(function (k) { return '<button data-jrsm="' + k + '" class="' + (k === JRSM ? 'on' : '') + '">' + JRSK[k][0] + ' ' + JRS.kinds[k].o.length + '</button>'; }).join('') + '</div>' +
      li(jrsCol(JRSM, 1), '색 = ' + JRSK[JRSM][1] + '마다 · 이름 = 관할 가운데', 'box') + (JRSM === 'tax' ? li('rgba(100,116,139,.6)', '회색 = 시군구 또는 동이 둘 이상으로 나뉨(확대하면 동마다)', 'box') : JRSM === 'court' ? li('rgba(100,116,139,.6)', '회색 = 시군구가 나뉨(창원시 — 마산지원)', 'box') : '') +
      '<small class="lg-n">' + esc(K.note) + ' · 누르면 이 자리의 세 관할</small>']; }
  function jrsLine(kind, v) {
    var K = JRS.kinds[kind]; if (v == null) return '<em>(자료 밖)</em>';
    if (v.c) return v.c.map(function (i) { return esc(jrsShort(kind, K.o[i][0])); }).join(' · ') + ' <em>— 이 시군구는 나뉜다 · 더 확대하면 동마다 가른다</em>';
    var L = (Array.isArray(v) ? v : [v]).map(function (i) { var o = K.o[i];
      if (kind === 'tax') return '<b>' + esc(o[0]) + '</b>' + (o[2] ? ' <a href="tel:' + esc(o[2].replace(/[^\d-]/g, '')) + '">' + esc(o[2]) + '</a>' : '') + ' <em>(' + esc(o[4]) + ')</em>';
      if (kind === 'edu') return '<b>' + esc(o[0]) + '</b> <em>(위치 ' + esc(o[1]) + ')</em>';
      return '<b>' + esc(o[0]) + '</b> <em>(' + esc(o[1]) + ')</em>'; });
    return L.join(' · ') + (Array.isArray(v) ? ' <em>— 이 동은 둘로 나뉜다(법정동·번지로 확인)</em>' : ''); }
  function jrsCard(it) {
    if (!JRS) { jrsLoad(); return '<h3>🏛 이 자리의 행정 관할</h3><p class="desc">자료를 받는 중…</p>'; }
    var m = it.m, d = dongAtM(m), gi = sggAt(m), h = '<h3>🏛 이 자리의 행정 관할</h3>' + (gi >= 0 ? row('자리', esc(SGG[gi].g.sido + ' ' + SGG[gi].g.name) + (d ? ' ' + esc(d.name || '') : '')) : '');
    Object.keys(JRSK).forEach(function (k) { var v = jrsAt(k, m), K = JRS.kinds[k]; h += row(JRSK[k][0], jrsLine(k, v));
      if (v != null && !v.c) (Array.isArray(v) ? v : [v]).forEach(function (i) { var o = K.o[i]; h += '<p class="desc"><b>' + esc(jrsShort(k, o[0])) + ' 관할(원문)</b> — ' + esc(k === 'tax' ? o[3] : o[2]) + (k === 'tax' && o[1] ? ' · 청사 ' + esc(o[1]) : '') + '</p>'; }); });
    h += '<p class="desc">교육지원청·법원은 법령 별표의 <b>시군구 단위</b> 관할 그대로다. 세무서는 국세청이 법정동·읍면으로 적은 관할을 행정동에 붙인 <b>근사</b> — 경계 근처는 원문(법정동·번지)으로 확인. 검찰청(지검·지청)은 법원 관할을 따른다. 학교 배정(학군·통학구역)·등기소·가정법원·행정법원은 다르다.' + (JRS.rename ? ' 이름 바꿈: ' + esc(JRS.rename) + '.' : '') + '</p>';
    if (!d && view.s < 0.012) h += '<p class="desc">더 확대하면 동 경계로 세무서 「나뉨」을 가른다.</p>';
    return h + src(Object.keys(JRSK).map(function (k) { return JRSK[k][1] + ': ' + JRS.kinds[k].source; }).join(' · ') + ' · ' + JRS.dong); }
  function jrsRows(k8) {   // 동 카드에 — 관할 교육지원청·세무서·법원
    if (!JRS) { jrsLoad(); return ''; } if (!k8) return ''; var h = '';
    Object.keys(JRSK).forEach(function (k) { var v = jrsOfK(JRS.kinds[k], k8); if (v != null) h += row('관할 ' + JRSK[k][1], jrsLine(k, v)); });
    return h ? h + '<p class="desc">관할 — 교육지원청·법원은 법령 별표(시군구) · 세무서는 국세청 관할 글을 행정동에 붙인 근사.</p>' : ''; }
  function jrsRel(m) {   // 「이 자리의 관계」에 — 이 자리는 ○○ 관할이다
    if (!JRS) { jrsLoad(); return []; } var o = [], d = dongAtM(m);
    Object.keys(JRSK).forEach(function (k) { var v = jrsAt(k, m); if (v == null || v.c) return; var K = JRS.kinds[k], split = d && d.k && K.d[d.k] != null && k === 'tax';
      (Array.isArray(v) ? v : [v]).forEach(function (i) { o.push(['이 자리는', '<b>' + esc(K.o[i][0]) + '</b>', ' 관할이다', k === 'tax' ? '국세청 세무서별 관할구역' : k === 'edu' ? '지방교육자치법 시행령 별표2·교육청 조례' : '각급 법원의 설치와 관할구역에 관한 법률 별표3', split ? '계산' : '원자료']); }); });
    return o; }

  // ---------- 층 단추 · 찾기 ----------
  var lay = $('m2dLayers');
  function paintLayers() {
    var nOn = LAYERS.filter(function (l) { return on[l[0]]; }).length; if ($('m2dLayN')) $('m2dLayN').textContent = nOn;
    lay.innerHTML = '<button data-all="1" class="all">🗂 모든 레이어 <b>' + nOn + '</b></button>' +
      LAYERS.slice().sort(function (a, b) { return (on[b[0]] ? 2 : b[4] ? 1 : 0) - (on[a[0]] ? 2 : a[4] ? 1 : 0); }).map(function (l) { return '<button data-k="' + l[0] + '" class="' + (on[l[0]] ? 'on' : '') + '">' + l[1] + '</button>'; }).join('');
    var pn = $('m2dPanel'); if (!pn) return;
    catPaint(pn, nOn);
    paintPre();
  }
  // v2.10.0 층 설명에 범위·출처·이용허락·추정 여부(data/layers.json — 굽는 도구가 실제 파일에서 센다)
  var LMETA = null, LMETAP = null;
  function lhTxt(k) {
    if (!LMETA && !LMETAP) LMETAP = fetch('data/layers.json').then(function (r) { return r.json(); }).then(function (j) { LMETA = {}; j.layers.forEach(function (x) { LMETA[x.key] = x; }); if (LHON || Object.keys(LHK).some(function (q) { return LHK[q]; })) paintLayers(); }).catch(function () { LMETA = {}; });
    var m = LMETA && LMETA[k], t = LHELP[k] ? esc(LHELP[k]) : '';
    var mt = m ? '<details class="lmd"><summary>📎 범위·출처·이용허락</summary><i class="lm">' + esc(m.cover || '') + ' · ' + esc(m.src) + (m.estimate ? ' · 추정 포함' : '') + ' · 이용허락 ' + esc(m.license) + '</i></details>' : '';   // v2.33.0 소유자 「범위·출처는 필요할 때만」
    return t || mt ? '<small>' + t + mt + '</small>' : '';
  }
  function toggle(k) { on[k] = !on[k]; if (k === 'bld' && on[k]) loadBld(); saveOn(); paintLayers(); draw(); }
  function onLayerClick(e) {
    var b = e.target.closest('button'); if (!b) return; var pn = $('m2dPanel');
    if (catClick(b)) return;
    if (b.getAttribute('data-lh')) { LHON = !LHON; LHK = {}; try { localStorage.setItem('tg_map2d_lh2', LHON ? '1' : '0'); } catch (e2) {} paintLayers(); return; }
    if (b.getAttribute('data-all')) { pn.classList.toggle('on'); return; }
    if (b.getAttribute('data-close')) { pn.classList.remove('on'); return; }
    if (b.getAttribute('data-none')) { layersNone(); return; }
    if (b.getAttribute('data-reset')) { layersReset(); return; }
    if (b.getAttribute('data-th')) { THEME = b.getAttribute('data-th'); try { localStorage.setItem('tg_map2d_theme', THEME); } catch (e3) {} paintLayers(); return; }
    if (b.getAttribute('data-thon') || b.getAttribute('data-thoff')) { var tk = themeKeys(THEME) || [], onq = !!b.getAttribute('data-thon');
      if (onq) LAYERS.forEach(function (l) { if (KEEP.indexOf(l[0]) < 0) on[l[0]] = false; }); (onq ? themeDef(THEME) : tk).forEach(function (k) { on[k] = onq; }); on.dong = true; on.road = true; on.base = true; saveOn(); paintLayers(); paintPre(); draw(); summary(); return; }
    var k = b.getAttribute('data-k'); if (k) toggle(k);
  }
  var pnEl = document.createElement('div'); pnEl.id = 'm2dPanel'; document.body.appendChild(pnEl);
  lay.addEventListener('click', onLayerClick); pnEl.addEventListener('click', onLayerClick);
  paintLayers();
  $('m2dFind').addEventListener('keydown', function (e) {
    if (e.key !== 'Enter') return;
    var q = this.value.trim(); if (!q) return;
    if (rpFind(q, this)) return;
    var c = [];
    DONG.forEach(function (d) { if (d.name.indexOf(q) >= 0) c.push({ p: d.c, it: { kind: 'dong', d: d } }); });
    var rseen = {}; RDONG.forEach(function (d) { if ((d.gu + ' ' + d.name).indexOf(q) >= 0) { rseen[d.gcd + d.name] = 1; c.push({ p: d.c, it: { kind: 'dong', d: d } }); } });
    rIdx().forEach(function (g) { if (g.gu === '11650') return; (g.d || []).forEach(function (x) { if (!rseen[g.gu + x[0]] && (g.name + ' ' + x[0]).indexOf(q) >= 0) c.push({ p: P(x[1], x[2]), it: { kind: 'rgo', gu: g.gu, name: x[0], g: g.name } }); }); });
    NEAR.forEach(function (d) { if (!RGUN[d.gu] && !c.some(function (x) { return x.it.kind === 'rgo' && x.it.g === d.gu && x.it.name === d.name; }) && (d.gu + ' ' + d.name).indexOf(q) >= 0) c.push({ p: d.c, it: { kind: 'near', d: d } }); });
    NODES.forEach(function (n) { if (n.name.indexOf(q) >= 0 || (n.sig && n.sig.name.indexOf(q) >= 0)) c.push({ p: n.p, it: { kind: 'node', n: n, st: D.acc && D.acc.nodes ? D.acc.nodes.filter(function (x) { return x.node[0] === n.i && x.node[1] === n.j; })[0] : null } }); });
    if (D.her) D.her.items.forEach(function (h) { if (h.name.indexOf(q) >= 0 && h.lat) c.push({ p: P(h.lon, h.lat), it: { kind: 'her', h: h } }); });
    if (D.sig) D.sig.spots.forEach(function (s) { if (s.name.indexOf(q) >= 0) c.push({ p: P(s.lon, s.lat), it: { kind: 'sig', s: s } }); });
    TG.forEach(function (t) { if (t.name.indexOf(q) >= 0 || String(t.c) === q) c.push({ p: t.p, it: { kind: 'tgis', t: t }, k: 'tgis' }); });
    SPOTS.forEach(function (s2) { if (s2.name.indexOf(q) >= 0) { var rk = spotRank().indexOf(s2) + 1; c.push({ p: s2.p, it: { kind: 'spot', q: s2, rank: rk }, k: 'spot' }); } });
    TRD.forEach(function (x) { if (x.t.name.indexOf(q) >= 0) c.push({ p: x.c, it: { kind: 'trd', x: x }, k: 'trd' }); });
    GGT.forEach(function (x) { if (x.t.n.indexOf(q) >= 0) c.push({ p: x.c, it: { kind: 'ggt', x: x }, k: 'trd' }); });
    SZ.forEach(function (x) { if (x.t.n.indexOf(q) >= 0) c.push({ p: x.c, it: { kind: 'szone', x: x }, k: 'szone' }); });
    if (!c.length && TRDIL.indexOf(q) >= 0) { TRDI = q; if (!on.trd) { on.trd = true; saveOn(); paintLayers(); } $('m2dFindMsg').textContent = '업종 「' + q + '」 — 상권을 그 업종 매출로 칠했다(범례에서 바꿈)'; draw(); return; }
    SAFE.forEach(function (L) { L[3].forEach(function (z) { var nm = FACL[L[0]] ? z.r[2] : L[0] === 'aed' ? z.r[2] : L[0] === 'wc2' || L[0] === 'srsvc' || L[0] === 'dem' || L[0] === 'tow' ? (L[0] === 'srsvc' ? z.r[3] : z.r[2]) : ''; if (nm && nm.indexOf(q) >= 0) c.push({ p: z.p, it: { kind: 'safe', L: L, q: z }, k: L[0] }); }); });
    LIVEP.forEach(function (L) { if (L.o.name.indexOf(q) >= 0) c.push({ p: L.c, it: { kind: 'crowd', L: L }, k: 'crowd' }); });
    OSMN.filter(function (r) { return r.name.indexOf(q) >= 0; }).sort(function (a, b) { return (a.name === q ? 0 : 1) - (b.name === q ? 0 : 1) || a.name.length - b.name.length; }).forEach(function (r) { if (r.name.indexOf(q) >= 0 && !c.some(function (x) { return x.rn === r.name; })) c.push({ p: r.p, it: { kind: 'osmroad', r: r }, rn: r.name }); });
    if (PUB) { ['er', 'hosp', 'phar', 'heat', 'cold', 'bus', 'subr', 'bike', 'sigx', 'drunk'].forEach(function (k) { PUB[k].forEach(function (x) { if ((x.name || '').indexOf(q) >= 0 || (k === 'sigx' && x.o.no === q)) c.push({ p: x.p, it: { kind: 'pub', layer: k, q: x }, k: k }); }); });
      Object.keys(PUB.fac).forEach(function (k) { PUB.fac[k].forEach(function (x) { if (x.name && x.name.indexOf(q) >= 0) c.push({ p: x.p, it: { kind: 'pub', layer: k, q: x }, k: k }); }); }); }
    if (JIDX) { var qn = q.replace(/\s/g, ''), jm = JIDX.j.filter(function (t) { return t[0].replace(/\s/g, '').indexOf(qn) >= 0; }).sort(function (a, b) { return (a[0] === q ? 0 : 1) - (b[0] === q ? 0 : 1) || a[4] - b[4] || a[0].length - b[0].length; });
      jm.slice(0, 30).forEach(function (t) { c.push({ p: P(t[1], t[2]), it: { kind: 'jcnm', t: t }, k: 'jcnm' }); });
      JIDX.r.filter(function (t) { return t[0] === q || (qn.length >= 2 && t[0].indexOf(qn) === 0); }).sort(function (a, b) { return (a[0] === q ? 0 : 1) - (b[0] === q ? 0 : 1) || a[0].length - b[0].length; }).slice(0, 10).forEach(function (t) { var g = rIdx().filter(function (x) { return x.gu === t[3]; })[0]; c.push({ p: P(t[1], t[2]), it: { kind: 'rdnm', t: [t[0], t[1], t[2], 0, t[4] || 0], g: g ? g.name : '' }, k: 'jcnm' }); }); }
    else if (!c.length) { var self = this; $('m2dFindMsg').textContent = '교차로·도로 이름 목록을 받는 중…'; jidxLoad().then(function (j) { if (j) self.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); else $('m2dFindMsg').textContent = '「' + q + '」 — 이 지도 자료에 없다'; }); return; }
    else jidxLoad();
    if (c.length && c[0].k && !on[c[0].k]) { on[c[0].k] = true; saveOn(); paintLayers(); }
    if (!c.length) { $('m2dFindMsg').textContent = '「' + q + '」 — 이 지도 자료에 없다'; return; }
    $('m2dFindMsg').textContent = c.length > 1 ? c.length + '곳 중 첫째' : '';
    view.cx = c[0].p[0]; view.cy = c[0].p[1]; view.s = Math.max(view.s, 0.35); draw();
    var s = S(c[0].p); sel = { x: s[0], y: s[1], r: 8, it: c[0].it }; show(c[0].it); draw();
  });
  // ---------- 🏪 창업 자리 찾기(v0.10.92 · 소유자 「상권분석은 그 부분만 따로 써도 어떤 업종을 어디에 열어 할 수 있을 만큼 제대로」) ----------
  //  고른 업종을 서울 상권 1,650곳(또는 고른 구 · 지금 화면)에서 견준다. 점수 = 항목마다 「그 업종이 있는 상권 안 백분위」의 가중 합(가중은 고르는 목적마다 — 설계값).
  //  지표는 전부 서울시 상권분석서비스 값이다(카드 추정 매출 · 점포 · 개업/폐업 · 1년 전 같은 분기 · 유동·직장·상주인구 · 상권변화지표). 임대료·권리금·공실·동선은 이 자료에 없다.
  var BIZ = { idx: null, ind: null, code: '', mode: 'bal', area: 'view', res: [], top: 15, busy: false, list: window.innerWidth >= 760 };
  var VW = { k: '', t: 0 };
  function viewWatch() {   // v1.1.0 소유자 「지금 보고 있는 지도를 중심으로 우선」 — 화면을 옮기고 0.6초 멈추면 다시 센다
    var k = Math.round(view.cx) + '|' + Math.round(view.cy) + '|' + view.s.toFixed(4) + '|' + cv.clientWidth + 'x' + cv.clientHeight; if (k === VW.k) return; VW.k = k; clearTimeout(VW.t);
    VW.t = setTimeout(function () {
      if (document.body.classList.contains('bizon') && BIZ.area === 'view' && BIZ.ind && !BIZ.busy) { bizCalc(); bizPaint(); draw(); }
      if (document.body.classList.contains('radon') && RAD.follow && !RAD.busy) { var c = viewMid(); if (!RAD.c || dTrue(c, RAD.c) > RAD.r * 0.08) { RAD.c = c; radRun(); } }
    }, 600);
  }
  function viewMid() {   // 지도가 보이는 가운데 — 아래 판이 덮은 만큼 위로
    var el = $('m2dRad'), hb = el && el.classList.contains('on') && !el.classList.contains('min') ? el.getBoundingClientRect().height : 0, top = $('m2dTop') ? $('m2dTop').getBoundingClientRect().bottom : 0;
    return M(cv.clientWidth / 2, (top + (cv.clientHeight - hb)) / 2);
  }
  function scoreCol(v, a) { var C = v >= 85 ? [21, 128, 61] : v >= 70 ? [34, 197, 94] : v >= 55 ? [234, 179, 8] : v >= 40 ? [249, 115, 22] : [239, 68, 68]; return 'rgba(' + C.join(',') + ',' + (a == null ? 1 : a) + ')'; }
  var BIZW = { bal: ['⚖ 균형', { D: .22, G: .17, V: .18, C: .13, B: .18, R: .12 }], sales: ['💰 매출 큰 곳', { D: .4, Z: .3, B: .15, G: .15 }], safe: ['🛡 오래 버티는 곳', { V: .4, C: .2, D: .15, R: .15, G: .1 }],
    grow: ['📈 크는 곳', { G: .45, D: .25, B: .15, V: .15 }], gap: ['🆕 빈 자리', { P: .45, D: .2, B: .25, V: .1 }], rent: ['💸 임대료 대비', { Y: .45, D: .2, V: .15, B: .1, C: .1 }] };
  var BIZN = { D: '점포당 매출', Z: '시장 크기', C: '경쟁 적음', G: '1년 성장', V: '버티기', B: '배후 사람', P: '사람 대비 점포 적음', R: '임대료 낮음', Y: '점포당 매출 ÷ 임대료' };
  function bizOpen() {
    rentLoad(); radClose();
    var el = $('m2dBiz'); el.classList.add('on'); el.classList.remove('min'); document.body.classList.add('bizon');
    if (!BIZ.idx) { el.innerHTML = '<div class="lg-h"><b>🏪 창업 자리 찾기</b><button data-bx="x">닫기</button></div><p class="lg-n">서울 상권 목록을 받는 중…</p>';
      fetch('data/r/biz/index.json').then(function (r) { return r.json(); }).then(function (j) { BIZ.idx = j; if (!BIZ.code) { var c = j.inds.filter(function (x) { return x[1] === (TRDI || '커피-음료'); })[0] || j.inds[0]; BIZ.code = c[0]; } bizLoad(); }).catch(function () { el.querySelector('.lg-n').textContent = '상권 목록을 받지 못했다(통신)'; }); return; }
    bizPaint();
  }
  function bizLoad() { BIZ.ind = null; BIZ.busy = true; bizPaint();
    fetch('data/r/biz/' + BIZ.code + '.json').then(function (r) { return r.json(); }).then(function (j) { BIZ.ind = j; BIZ.busy = false; bizCalc(); bizPaint(); draw(); }).catch(function () { BIZ.busy = false; bizPaint(); }); }
  function bizArea(m) { if (BIZ.area === 'all') return true; if (BIZ.area === 'view') { var q = P(m[4], m[5]), a = M(0, 0), b = M(cv.clientWidth, cv.clientHeight); return q[0] >= a[0] && q[0] <= b[0] && q[1] >= a[1] && q[1] <= b[1]; } return m[3] === BIZ.area; }
  function prank(list, key, hi) {   // 백분위(0~1 · 높을수록 좋음) — 값 없는 칸은 0.5(가운데)로 두고 표시한다
    var v = list.filter(function (x) { return x[key] != null; }).sort(function (a, b) { return a[key] - b[key]; }), n = v.length;
    v.forEach(function (x, i) { var r = n > 1 ? i / (n - 1) : 0.5; x['p' + key] = hi ? r : 1 - r; }); list.forEach(function (x) { if (x[key] == null) x['p' + key] = 0.5; });
  }
  function bizCalc() {
    var I = BIZ.ind, MT = BIZ.idx.trdar; if (!I) return; var L = [], seen = {};
    I.rows.forEach(function (r) { var m = MT[r[0]]; if (!m || !m[13] || !bizArea(m)) return; seen[r[0]] = 1;
      var st = r[3], amt = r[1], ha = Math.max(m[6] / 1e4, 0.5), ppl = m[7] / 91 + m[8] + m[9];
      L.push({ r: r, m: m, i: r[0], D: st && amt ? amt / st : null, Z: amt || null, C: st / ha, G: r[7] > 0 && amt > 0 && r[7] >= 1000 && (st >= 2 || (r[8] || 0) >= 2) ? (amt - r[7]) / r[7] : null,
        cr: st ? r[6] / st : null, mo: m[11] || null, B: ppl || null, P: ppl ? ppl / (st + 1) : null }); });
    if (BIZ.mode === 'gap') MT.forEach(function (m, i) { if (seen[i] || !m[13] || !bizArea(m)) return; var ppl = m[7] / 91 + m[8] + m[9]; if (!ppl) return;
      L.push({ r: null, m: m, i: i, D: null, Z: null, C: 0, G: null, cr: null, mo: m[11] || null, B: ppl, P: ppl, none: true }); });
    L.forEach(function (x) { var rn = rentNear(P(x.m[4], x.m[5]), 1500); x.rn = rn; x.R = rn ? lastV(rn.it.s) || lastV(rn.it.m) : null; x.Y = x.R && x.D ? x.D / x.R : null; });
    ['D', 'Z', 'G', 'B', 'P', 'mo', 'Y'].forEach(function (k) { prank(L, k, true); }); prank(L, 'C', false); prank(L, 'cr', false); prank(L, 'R', false);
    L.forEach(function (x) { x.pV = x.cr == null && x.mo == null ? 0.5 : (x.cr == null ? x.pmo : x.mo == null ? x.pcr : x.pcr * 0.6 + x.pmo * 0.4); });
    var W = BIZW[BIZ.mode][1]; L.forEach(function (x) { var s2 = 0; Object.keys(W).forEach(function (k) { s2 += W[k] * x['p' + k]; }); x.score = Math.round(s2 * 100); });
    L.sort(function (a, b) { return b.score - a.score; }); BIZ.res = L; BIZ.n = L.length;
  }
  function bizPct(v) { return v >= 0.5 ? '상위 ' + Math.max(1, Math.round((1 - v) * 100)) + '%' : '하위 ' + Math.max(1, Math.round(v * 100)) + '%'; }
  function bizFacts(x) {   // 숫자 줄 — 그 업종이 이 상권에서
    var r = x.r; if (!r) return '이 업종 점포·매출 없음 — 상권 사람 ' + man(x.B) + '명(하루 유동 + 직장 + 상주)';
    var tb = r.slice(9, 15), pk = 0; for (var i = 1; i < 6; i++) if (tb[i] > tb[pk]) pk = i; var ag = r.slice(15, 21), at = ag.reduce(function (a, b) { return a + b; }, 0);
    return '한 달 ' + won(r[1]) + ' · 점포 ' + r[3] + (r[5] || r[6] ? ' (+' + r[5] + '/−' + r[6] + ')' : '') + (r[3] ? ' · 점포당 ' + won(r[1] / r[3]) : '') + (r[2] ? ' · 객단가 ' + Math.round(r[1] * 1e4 / r[2]).toLocaleString() + '원' : '') +
      (r[1] ? ' · 피크 ' + TBL[pk] + '시 · 20·30대 ' + pct(ag[1] + ag[2], at) + '% · 주말 ' + pct(r[21], r[1]) + '%' : '') + (x.G != null ? ' · 1년 ' + (x.G >= 0 ? '+' : '') + Math.round(x.G * 100) + '%' : '') +
      (x.rn ? ' · 임대료 ' + x.R + '천원/㎡(' + x.rn.it.name + ' ' + x.rn.d + 'm)' : '');
  }
  function bizWhy(b) {   // 상권 카드 맨 위 — 왜 이 순위인가
    var x = b.x, W = BIZW[b.mode][1];
    return '<div class="bizwhy"><button data-bizback="1">◀ 목록</button><b>🏪 ' + esc(b.ind) + ' — ' + b.rank + '위 / ' + b.n + '곳 · 점수 ' + x.score + '</b> <small>(' + BIZW[b.mode][0] + ')</small><br>' +
      Object.keys(W).map(function (k) { var v = x['p' + k]; return esc(BIZN[k]) + ' ' + (k === 'G' && x.G == null ? '<em>자료 적음</em>' : (k === 'R' || k === 'Y') && x.R == null ? '<em>1.5km 안 표본 없음</em>' : k === 'V' && x.cr == null && x.mo == null ? '<em>자료 없음</em>' : bizPct(v)) + ' <small>×' + Math.round(W[k] * 100) + '</small>'; }).join(' · ') +
      '<br><small>' + esc(bizFacts(x)) + '</small></div>';
  }
  function bizPaint() {
    var el = $('m2dBiz'); if (!el.classList.contains('on')) return; var X = BIZ.idx, h = '<div class="lg-h"><b>🏪 창업 자리 찾기</b><span><button data-bx="pnl">💰 손익 계산</button> <button data-bx="min">▾ 접기</button> <button data-bx="x">닫기</button></span></div>';
    if (!X) { el.innerHTML = h; return; }
    h += '<!--SUM-->'; var sumH = '';
    var gus = (D.ridx && D.ridx.gus || []).map(function (g) { return [g.gu, g.name]; });
    h += '<div class="bizrow"><label>업종 <select data-bz="ind">' + X.inds.map(function (c) { return '<option value="' + c[0] + '"' + (c[0] === BIZ.code ? ' selected' : '') + '>' + esc(c[1]) + ' · ' + c[2] + '곳</option>'; }).join('') + '</select></label>' +
      '<label>어디서 <select data-bz="area"><option value="view"' + (BIZ.area === 'view' ? ' selected' : '') + '>🗺 지금 보는 지도</option><option value="all"' + (BIZ.area === 'all' ? ' selected' : '') + '>서울 전체</option>' + gus.map(function (g) { return '<option value="' + g[0] + '"' + (BIZ.area === g[0] ? ' selected' : '') + '>' + esc(g[1]) + '</option>'; }).join('') + '</select></label></div>';
    h += '<div class="lg-btns">' + Object.keys(BIZW).map(function (k) { return '<button data-bm="' + k + '" class="' + (k === BIZ.mode ? 'on' : '') + '">' + BIZW[k][0] + '</button>'; }).join('') + '</div>';
    var W = BIZW[BIZ.mode][1]; h += '<p class="lg-n">점수 = ' + Object.keys(W).map(function (k) { return BIZN[k] + ' ' + Math.round(W[k] * 100); }).join(' + ') + ' (그 업종이 있는 상권 안 백분위 · 가중은 설계값)' + (BIZ.mode === 'gap' ? ' — 「빈 자리」는 그 업종 점포가 없는 상권도 넣는다(수요는 사람 수로만 본다)' : '') + '</p>';
    if (BIZ.busy || !BIZ.ind) h += '<p class="lg-n">업종 자료를 받는 중…</p>';
    else { var R = BIZ.res.slice(0, BIZ.top);
      sumH = '<div class="bizsum">' + (BIZ.area === 'view' ? '🗺 <b>지금 보는 지도</b> 안 상권 ' + BIZ.res.length + '곳' : '상권 ' + BIZ.res.length + '곳') + (R.length ? ' · 1위 <b>' + esc(R[0].m[1]) + '</b> ' + R[0].score + '점' + (R[1] ? ' · 2위 ' + esc(R[1].m[1]) + ' ' + R[1].score : '') + (R[2] ? ' · 3위 ' + esc(R[2].m[1]) + ' ' + R[2].score : '') : ' — 지도를 옮기거나 줄여 보세요') +
        '<div class="bizscale"><i style="background:' + scoreCol(20) + '"></i><i style="background:' + scoreCol(45) + '"></i><i style="background:' + scoreCol(60) + '"></i><i style="background:' + scoreCol(75) + '"></i><i style="background:' + scoreCol(90) + '"></i><span>낮음</span><span>점수 → 지도 색</span><span>높음</span></div>' +
        '<small class="lg-n">지도의 상권이 점수 색으로 칠해진다 — 지도를 옮기거나 확대하면 그 화면 안에서 다시 순위를 매긴다. 원을 누르면 그 상권 카드.</small>' +
        '<button data-bx="list">' + (BIZ.list ? '▴ 목록 접기' : '📋 목록 보기(' + Math.min(BIZ.top, BIZ.res.length) + ')') + '</button></div>';
      h = h.replace('<!--SUM-->', sumH);
      if (BIZ.list) h += '<ol class="bizl">' + R.map(function (x, k) { var m = x.m; return '<li data-bi="' + k + '"><b>' + (k + 1) + '. ' + esc(m[1]) + '</b> <small>' + esc(m[2]) + ' · ' + esc(guName(m[3])) + '</small> <i style="--w:' + x.score + '%">' + x.score + '</i><br><small>' +
        ['D', 'G', 'C', 'V', 'B', 'R', 'Y'].filter(function (q) { return W[q] || q === 'D'; }).map(function (q) { return BIZN[q] + ' ' + ((q === 'G' && x.G == null) || ((q === 'R' || q === 'Y') && x.R == null) ? '-' : bizPct(x['p' + q])); }).join(' · ') + '</small><br><small class="f">' + esc(bizFacts(x)) + '</small></li>'; }).join('') + '</ol>';
      if (BIZ.list) h += '<div class="lg-btns">' + (BIZ.res.length > BIZ.top ? '<button data-bx="more">더 보기(' + BIZ.top + ' / ' + BIZ.res.length + ')</button>' : '') + '<button data-bx="map">🗺 상권 층을 이 업종으로</button></div>'; }
    h += '<small class="lg-n">' + esc(X.source) + ' · ' + esc(X.note) + '<br>⚠ 참고 지표다 — <b>임대료는 1.5km 안 부동산원 표본 상권(72곳) 평균일 뿐 그 자리 값이 아니다 · 권리금·보증금·개별 공실·유동 동선·상가 위치(1층·코너)는 이 자료에 없다</b>. 고른 상권은 현장에서 확인한다. 추정 매출은 카드 결제 기반(현금 제외)이고, 점포가 적은 상권은 값이 크게 흔들린다.</small>';
    el.innerHTML = h;
  }
  function guName(c) { var g = (D.ridx && D.ridx.gus || []).filter(function (x) { return x.gu === c; })[0]; return g ? g.name : c; }
  function bizGo(k) {
    var x = BIZ.res[k]; if (!x) return; var m = x.m, q = P(m[4], m[5]); view.cx = q[0]; view.cy = q[1]; view.s = Math.max(view.s, 0.28);
    if (!on.trd) { on.trd = true; saveOn(); paintLayers(); } TRDI = BIZ.ind.name;
    var biz = { x: x, rank: k + 1, n: BIZ.res.length, ind: BIZ.ind.name, mode: BIZ.mode }; TWANT = { cd: m[0], biz: biz };
    if (window.innerWidth < 760) { $('m2dBiz').classList.add('min'); }
    tLoad(m[3], function () { TRD.forEach(function (y) { if (TWANT && y.t.cd === TWANT.cd) { var it = { kind: 'trd', x: y, biz: TWANT.biz }; TWANT = null; var s2 = S(y.c); sel = { x: s2[0], y: s2[1], r: 12, it: it }; show(it); } }); draw(); });
    draw();
  }
  function drawBiz(dark) {   // v1.1.0 고른 업종의 점수 분포 — 상권 다각형을 점수 색으로 칠하고, 상권마다 점수 원 · 상위 3은 순위
    if (!document.body.classList.contains('bizon') || !BIZ.res.length) return; var R = BIZ.res, byCd = {}, W0 = cv.clientWidth, H0 = cv.clientHeight;
    TRD.forEach(function (x) { byCd[x.t.cd] = x; });
    R.forEach(function (x) { var T = byCd[x.m[0]]; if (!T) return; var b = trdBB(T), a = S([b[0], b[2]]), z = S([b[1], b[3]]); if (z[0] < 0 || a[0] > W0 || a[1] < 0 || z[1] > H0) return;
      T.rings.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = scoreCol(x.score, 0.42); ctx.fill(); ctx.lineWidth = 1.4; ctx.strokeStyle = scoreCol(x.score, 0.95); ctx.stroke(); }); });
    var rr = Math.max(8, Math.min(15, 6 + view.s * 30));
    for (var j = R.length - 1; j >= 0; j--) { var qj = P(R[j].m[4], R[j].m[5]), sj = S(qj); if (sj[0] < -20 || sj[1] < -20 || sj[0] > W0 + 20 || sj[1] > H0 + 20) continue;
      ctx.beginPath(); ctx.arc(sj[0], sj[1], j < 3 ? rr + 3 : rr, 0, Math.PI * 2); ctx.fillStyle = scoreCol(R[j].score, 0.95); ctx.fill(); ctx.lineWidth = j < 3 ? 3 : 1.6; ctx.strokeStyle = j < 3 ? '#4c1d95' : '#fff'; ctx.stroke();
      ctx.fillStyle = R[j].score >= 55 && R[j].score < 70 ? '#1f2937' : '#fff'; ctx.font = 'bold ' + (j < 3 ? 12 : 10.5) + 'px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(j < 3 ? (j + 1) + '위' : String(R[j].score), sj[0], sj[1]);
      hit.push({ x: sj[0], y: sj[1], r: rr + 2, it: { kind: 'bizpin', k: j } });
      if (j < 3 || view.s > 0.12) label([qj[0], qj[1] + (rr + 10) / view.s], R[j].m[1] + (j < 3 ? ' ' + R[j].score + '점' : ''), 10.5, dark ? '#ede9fe' : '#4c1d95', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); }
    return;
    for (var i = R.length - 1; i >= BIZ.top; i--) { var q = P(R[i].m[4], R[i].m[5]), s2 = S(q); if (s2[0] < -10 || s2[1] < -10 || s2[0] > cv.clientWidth + 10 || s2[1] > cv.clientHeight + 10) continue; ctx.beginPath(); ctx.arc(s2[0], s2[1], 3, 0, Math.PI * 2); ctx.fillStyle = 'rgba(124,58,237,' + (0.15 + 0.6 * R[i].score / 100).toFixed(2) + ')'; ctx.fill(); }
    for (i = Math.min(BIZ.top, R.length) - 1; i >= 0; i--) { var q2 = P(R[i].m[4], R[i].m[5]), s3 = S(q2); ctx.beginPath(); ctx.arc(s3[0], s3[1], 11, 0, Math.PI * 2); ctx.fillStyle = i < 3 ? '#7c3aed' : '#a78bfa'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
      ctx.fillStyle = '#fff'; ctx.font = 'bold 11px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(i + 1), s3[0], s3[1]); hit.push({ x: s3[0], y: s3[1], r: 12, it: { kind: 'bizpin', k: i } });
      if (view.s > 0.06) label([q2[0], q2[1] + 20 / view.s], R[i].m[1], 10.5, dark ? '#ede9fe' : '#4c1d95', dark ? 'rgba(15,22,36,.75)' : 'rgba(255,255,255,.88)'); }
  }
  document.addEventListener('click', function (e) { if (e.target.closest('[data-bizback]')) bizOpen(); });
  if ($('m2dBiz')) {
    $('m2dBiz').addEventListener('click', function (e) { var b = e.target.closest('[data-bx],[data-bm],[data-bi]'); if (!b) { if ($('m2dBiz').classList.contains('min')) $('m2dBiz').classList.remove('min'); return; }
      var x = b.getAttribute('data-bx');
      if (x === 'pnl') { pnlOpen(viewMid()); return; } if (x === 'x') { $('m2dBiz').classList.remove('on'); document.body.classList.remove('bizon'); draw(); return; }
      if (x === 'min') { e.stopPropagation(); $('m2dBiz').classList.toggle('min'); return; }
      if (x === 'more') { BIZ.top += 15; bizPaint(); draw(); return; }
      if (x === 'list') { BIZ.list = !BIZ.list; bizPaint(); return; }
      if (x === 'map') { if (!on.trd) { on.trd = true; saveOn(); paintLayers(); } TRDI = BIZ.ind ? BIZ.ind.name : ''; TRDM = 'perstor'; document.body.classList.add('legon'); draw(); return; }
      var m2 = b.getAttribute('data-bm'); if (m2) { BIZ.mode = m2; bizCalc(); bizPaint(); draw(); return; }
      var k = b.getAttribute('data-bi'); if (k != null) bizGo(+k); });
    $('m2dBiz').addEventListener('change', function (e) { var t = e.target, w = t.getAttribute('data-bz'); if (w === 'ind') { BIZ.code = t.value; BIZ.top = 15; bizLoad(); } else if (w === 'area') { BIZ.area = t.value; BIZ.top = 15; bizCalc(); bizPaint(); draw(); } });
  }
  // ---------- 📐 반경 분석(v0.10.93 · 소유자 「상용 상권분석 프로그램만큼의 퍼포먼스」) ----------
  //  고른 자리에서 반경 300m·500m·1km — 점포(소상공인 상가정보 · 하나하나) · 경쟁점 · 추정 매출(걸친 상권을 겹친 넓이 비율로) · 생활인구·주민(걸친 동을 넓이 비율로) ·
  //  유동·직장 인구 · 지하철역 · 가까운 부동산원 임대료. 넓이 비율 = 반경 안을 격자로 찍어 센 것(근사 · 화면에 밝힌다).
  var RAD = { c: null, r: 500, ind: '', sind: '', res: null, busy: false, pick: false, follow: false, heat: null }, SIDX = null, SIDXP = null, SPTS = {}, STNS = null;
  function sLoadIdx() { if (SIDXP) return SIDXP; SIDXP = fetch('data/r/stores-index.json').then(function (r) { return r.json(); }).then(function (j) { SIDX = j; }).catch(function () {}); return SIDXP; }
  function sLoad(gu) {
    if (SPTS[gu]) return SPTS[gu].p; var o = SPTS[gu] = { a: null };
    o.p = rGet(gu, 'stores.json').then(function (j) { var O = j.o, K = j.k; o.ym = j.stdrYm; o.a = j.pts.map(function (q) { return { p: P(O[0] + q[0] / K[0], O[1] + q[1] / K[1]), c: q[2], f: q[3], n: q[4] }; }); }).catch(function () { o.a = []; });
    return o.p;
  }
  function polyA(polys) { var a = 0; polys.forEach(function (Pg) { Pg.forEach(function (r, i) { var s2 = 0; for (var k = 0, j = r.length - 1; k < r.length; j = k++) s2 += r[j][0] * r[k][1] - r[k][0] * r[j][1]; a += (i ? -1 : 1) * Math.abs(s2) / 2; }); }); return a; }
  function trdBB(x) { if (!x.bb) { var b = [1e9, -1e9, 1e9, -1e9]; x.rings.forEach(function (r) { r.forEach(function (q) { b[0] = Math.min(b[0], q[0]); b[1] = Math.max(b[1], q[0]); b[2] = Math.min(b[2], q[1]); b[3] = Math.max(b[3], q[1]); }); }); x.bb = b; } return x.bb; }
  // ---------- ❓ 층 설명(v2.0.0 · 소유자 「많은 레이어가 있어 이제는 친절한 설명이 필요해」) — 무엇을 · 어디서 · 어떻게 쓰나 ----------
  var LHELP = {
    rpost: '도로 위 기둥 번호 — 서울 도시고속도로 가로등주 관리번호(예: 올_23-05 · 서울시 2022-11 · 19,291개). 많이 확대하면 점과 번호가 보인다. 찾기 칸에 「올 23-05」·「올림픽 23-5」를 넣으면 그 자리로 간다. 지도를 길게 누르면(PC 는 오른쪽 클릭) 가장 가까운 번호를 알려 준다 — 112·무전으로 위치를 불러 줄 때. 전국 고속도로 거리표(km · 한국도로공사 2025 · 100m)도 찾기 칸에 「경부 400.1」 · 길게 누르기로 · 민자·지자체 고속도로는 자료에 없다 · 일반국도 km 는 공개 자료가 없어 만들지 않는다.',
    stay: '전국 숙박시설 — 관광호텔·호스텔·휴양콘도·한옥체험(한옥스테이)·관광펜션·농어촌민박·일반 숙박업(여관·모텔 등) 영업 중인 곳(행정안전부 지방행정인허가 2025-11-27). 범례에서 종류를 골라 켜고 끈다. 영문 상호가 있으면 외국인 손님을 받는 곳일 가능성이 크다(추론). 에어비앤비 등 등록 안 한 숙소·투숙 인원은 공개되지 않는다.',
    jiga: '대지(지목 「대」) 필지의 ㎡당 개별공시지가 중앙값 — 250m 칸 색(가까이) · 행정동 색(멀리). 범례에서 「🌾 농지 · 🌳 임야 · 🏠 대지 · 🏭 공장 비율」로 바꾸면 지목(땅 쓰임) 넓이 비율을 칠한다. 국토교통부 개별공시지가(브이월드 연속지적도 · 이용허락 제한 없음)를 이 지도가 칸·동으로 묶었다. 필지 하나는 「📐 필지」를 켜고 누른다. 공시지가는 세금·보상 기준값이지 시세가 아니다.',
    land: '켜고 지도를 누르면 그 자리 필지 하나 — 지번·개별공시지가(1990년부터 해마다)·면적·지목·이용상황·도로접면·용도지역·지구(토지이용계획)·소유 구분·건물(용도·층·연면적·사용승인). 많이 확대하면 지적선, 범례에서 용도지역 색. 국토교통부 브이월드에서 그때 받는다(브이월드 키 · 이 기기에만) · 받은 값은 저장하지 않는다 · 공시지가는 시세가 아니다.',
    dong: '행정동 경계. 동을 누르면 주민 연령·생활인구·카드 매출과 「🗣 이 자리 읽기」 해설이 나온다.',
    road: '도로(OSM). 굵기·색 = 도로 등급(고속·간선·보조·골목). 확대하면 도로 이름이 나온다.',
    base: '바탕 지도 — 물·공원·숲·철도·건물 덩어리(OSM). 지도를 읽기 쉽게 하는 배경.',
    vw: '국토교통부 브이월드 위성사진·일반 지도를 밑에 깐다. 인터넷이 있을 때만 · 처음 한 번 기기에 키를 넣는다(범례 🔑).',
    jcnm: '서울·경기 교차로 2.5만 곳과 도로 이름(국가교통정보센터 표준노드링크). 누르면 그 교차로에서 만나는 도로. 「찾기」에 교차로·도로 이름을 넣어도 된다.',
    bld: '건물 윤곽(OSM). 많이 확대해야 나온다.',
    sub: '지하철역 자리.',
    exit: '지하철 출입구 번호(OSM).',
    lev: '지금 고속도로·국도·시군도의 공사·사고·통제(국가교통정보센터). 켤 때 한 번 받고 범례 🔄 로 다시 · ITS 키 필요.',
    lspd: '지금 도로 속도를 원활(초록)·서행(노랑)·정체(빨강)로 칠한다(ITS 실시간). 화면 가로 약 14km 안까지 확대해야 받는다 · ITS 키 필요.',
    lcc: '국도·고속도로 교통 CCTV 1,801대. 점을 누르면 카드에서 실시간 영상이 나온다(ITS 호출 없음).',
    lak: '에어코리아 측정소 168곳이 지금 잰 미세먼지. 원 안 숫자 = 초미세먼지(㎍/㎥), 색 = 환경부 등급 · 공공데이터포털 키 필요.',
    lkma: '기상청 초단기실황(지도 가운데) · 서울·경기 특보(붉은 띠) · 최근 3일 지진 · 공공데이터포털 키 필요.',
    lbus: '경기 버스 — 확대하면 정류장이 나오고, 누르면 몇 분 뒤 오는지, 「🚌 위치」로 그 노선 버스가 지도에. 서울 시내버스는 없다(서울시 API 가 https 를 안 받음).',
    lwx: '지금 날씨(기온·하늘·강수)를 화면 칸마다(Open-Meteo 모형값 · 키 없음).',
    lrad: '비구름 레이더(RainViewer · 한 칸 약 1km). 비가 올 때만 색이 칠해진다.',
    lair: '지금 미세먼지를 화면 칸마다(Open-Meteo 대기질 모형값 · 측정소 값과 다를 수 있다).',
    acc: '교차로별 교통사고 건수(2019~ · TAAS). 원이 클수록 사고가 많다 — 누르면 유형·시간대.',
    acc10: '10년 교통사고를 100m 칸으로(TAAS). 사고가 몰린 칸이 진하다.',
    fatal10: '10년 사망사고 자리(TAAS).',
    jurk: '전국 경찰서 관할 — 「경찰청과 그 소속기관 직제 시행규칙」 별표2(2026.8.31)를 행정동에 붙인 근사. 색 = 관할 경찰서 · 회색 = 두 서가 번지로 나눠 맡는 동(경계) · 네모 = 청사(누르면 대표번호·소속 지구대).',
    pbox: '전국 지구대·파출소 2,047곳(경찰청 2025-12-31 주소 → 좌표). 관할 경계는 공개 자료가 없어 자리만 — 동 카드의 「가까운 지구대」는 거리 근사.',
    home: '국토부 아파트·오피스텔·연립다세대 실거래(매매 24개월·전월세 12개월). 250m 칸 색을 범례에서 고른다 — 아파트 매매 평당·전세 평당·전세가율·월세·오피스텔·연립다세대. 확대하면 단지마다 점. 평당 = 전용 기준 · 전세가율은 추정.',
    rtc: '국토부 상업업무용 부동산 매매 실거래(서울·경기 24개월). 250m 칸 색 = 집합건물 ㎡당 거래금액 중앙값, 확대하면 거래 한 건씩. 평당 = 전용 기준.',
    bstop: '전국 버스정류장 자리(OpenStreetMap · 약 10.5만) — 이름·번호만. 승하차 인원은 서울·경기만(🚌 버스 승차·하차). 확대하면 보인다.',
    tlt: '전국 신호등(공공데이터포털 전국신호등표준데이터 · 약 9.9만) — 누르면 도로·현시 순서·현시 시간·잔여시간 표시·음향신호기. 등록값이라 실제 운영과 다를 수 있다.',
    rnet: '전국 도로를 등급별 색으로(국가교통정보센터 표준노드링크 2026-09) — 파랑 고속국도 · 보라 도시고속 · 빨강 일반국도 · 주황 특별·광역시도 · 초록 국가지원지방도 · 노랑 지방도 · 회색 시군도(크게 확대하면). 넓게 볼 때는 고속·국도만, 확대할수록 아래 등급까지. 길을 누르면 이름·등급·제한속도.',
    exv: '전국 고속도로 영업소(요금소)마다 시간당 드나든 차(입구·출구) — 한국도로공사 OpenAPI. 이 API 는 지난 시각을 주지 않아 매시간 모은 만큼만 있다(카드에 모은 시각). 본선 통행량이 아니라 영업소를 드나든 차다.',
    volp: '서울시 교통량 조사 지점(약 130곳)의 시간대별 차량 대수 — 평일(2일 평균)·토·일, 방향 둘. 원 크기 = 평일 하루 대수. 누르면 시간대 막대. 조사 지점 밖 도로는 이 값으로 추정하지 않는다.',
    juris: '행정 관할 — 🎒 교육지원청(지방교육자치법 시행령 종전 별표2 · 교육청 조례) · 🧾 세무서(국세청 세무서별 관할구역) · ⚖ 지방법원·지원(각급 법원의 설치와 관할구역에 관한 법률 별표3)을 행정동·시군구에 칠한다. 범례에서 셋 중 하나를 고르고, 지도를 누르면 그 자리의 세 관할을 한 번에 — 원문 관할 글·전화·상급 기관. 세무서는 법정동으로 적힌 관할을 행정동에 붙인 근사(회색 = 한 동이 둘로 나뉨).',
    usgg: '시·군·구마다 다른 색으로 칠한다(경기 일반구는 시로). 누르면 그 시군구의 합계 — 주민·연령·가구·가게·사고·대중교통·카드·외국인 — 와 「🤖 AI용 복사」.',
    upb: '지구대·파출소마다 맡는 동네를 칠한다 — 공식 관할 경계는 공개되지 않아 「그 동의 관할 경찰서 지구대·파출소 가운데 동 가운데에서 가장 가까운 곳」으로 근사한다. 누르면 그 지구대·파출소 구역의 합계.',
    ri: '읍·면의 리(里) 경계(브이월드 법정리 약 1.5만 · 147개 시군구). 리 단위 인구·카드 통계는 공개되지 않아 리마다 가게 수·사고 10년·사망사고만 이 지도의 점으로 센다. 리를 누르면 숫자.',
    fdong: '행정안전부 외국인주민 현황 — 멀리 보면 시군구(2024·2019 · 가장 많은 국적), 가까이 보면 읍면동(2024.11.1). 범례에서 비율·인원·근로자·결혼이민·유학생·동포·귀화·자녀·5년 변화를 고른다. 동을 누르면 근로자·결혼이민·유학생·동포·귀화·자녀·다문화가구원. 3개월 넘게 사는 사람 기준.',
    minbak: '전국 외국인관광 도시민박업(행정안전부 지방행정인허가 · 공공데이터포털 15044966 · 2026-10-05) — 영업 중(분홍)·휴업(회색) 11,658곳. 외국인 관광객에게 집을 내주는 민박이라 단기체류 외국인이 묵는 자리. 누르면 사업장명·주소·객실수. 투숙 인원·국적은 공개되지 않는다. 분기마다 다시 받는다.',
    flodge: '서울 관광숙박업(호텔·호스텔 등) 영업 중인 곳(지방행정인허가 · 서울 열린데이터). 외국인관광 도시민박은 「🏡 외국인관광 도시민박」 층(전국).',
    lpop: '통계청·행정안전부 인구감소지역 생활인구(주민등록 + 그 달 하루 3시간 넘게 머문 체류인구 · 통신 추정) — 인구감소지역 89·관심지역 18곳만 공표. 시군구를 「주민 대비 몇 배」로 칠한다. 누르면 달마다·남녀·연령.',
    busd: '인천광역시 정류장별 이용승객(공공데이터포털 · 시간대 없음) — 정류장마다 하루 평균 승차·하차. 원 크기 = 승하차 합.',
    msub: '대구교통공사 월별 하차 인원(공공데이터포털) — 역마다 하루 평균 하차. 대구는 시간대·승차를 공개하지 않는다(대전·광주는 「🚇 지하철 승차·하차」에 시간대로).',
    fl250: '서울 250m 칸마다 그 시각 머무는 외국인(서울시 생활인구 — 장기체류 91일 이상 · 단기체류 90일 이하 관광·방문 · 통신 자료 추정 · 한 주 평균). 칸을 누르면 장기·단기 시간대와 국적 상위. 행안부 외국인주민·법무부 등록외국인과 정의가 달라 더하지 않는다.',
    live250: '서울 생활인구를 250m 칸으로(서울시 · 한 주 평균 · 평일/주말 24시간 · 낮·밤 연령). 동 단위 생산이 2026-07 에 끝나 이것으로 바뀐다. 칸을 누르면 낮/밤·주말 해설.',
    acc250: 'TAAS 교통사고 10년(2016~2025 · 서울·경기 88.7만 건)을 250m 국가표준격자 칸으로 — 칸 번호 하나로 모아 같은 칸이 겹치지 않는다. 색 기준(전체·사망중상·보행자…)·해 고르기는 사고 10년 층과 같다.',
    g250: '국가지점번호식 250m 격자 선(EPSG:5179). 칸을 누르면 「이 칸 한눈에」 — 걸친 행정동·사람·사고·가게·시설·대중교통·집값을 한 카드에. 전국 확장의 기본 단위.',
    fatal: '사망사고 자리(2020~2025 · TAAS) — 「사망사고 10년」과 같은 자료의 최근 6년이다. 둘 다 켜도 한 사고는 한 점.',
    hot: '도로교통공단이 정한 사고다발지(보행자·자전거·어린이 등 갈래별).',
    drunk: '음주운전 사고 다발지(도로교통공단).',
    risk: '사고위험지역(도로교통공단 분석).',
    sz: '어린이보호구역(스쿨존) — 30km/h 구역.',
    szh: '어린이보호구역 안 어린이 사고.',
    cam: '무인 교통단속 카메라(과속·신호).',
    spd: '서울시 도로 소통(받은 때 한 장 · 실시간 아님). 실시간은 「🚦 지금 도로 소통」.',
    sig: '신호 주기(받은 교차로만).',
    sigx: '신호 교차로 번호(경찰청 신호 자료).',
    trd: '서울시 상권분석 — 상권마다 카드 추정 매출·유동·점포·개폐업. 범례에서 업종·보기를 고른다. 「🏪 창업 자리 찾기」·「📐 반경 분석」·「💰 손익 계산」의 바탕 자료.',
    rent: '한국부동산원 상가 임대료(㎡당)·공실률 표본 지점. 매물 1건 월세가 아니라 그 상권 평균이다.',
    szone: '소상공인시장진흥공단이 정한 주요상권(서울·경기) 영역과 점포 수.',
    jgg: '통계청 집계구(약 500명 단위) 인구·가구·주택·사업체·종사자. 「종사자÷인구」로 일터형·주거형을 가른다.',
    crowd: '서울시 실시간 도시데이터(주요 120곳 인파·카드) — 받은 때 한 장.',
    live: '생활인구 — 그 시각 그 동 안에 있는 사람(서울시·KT 통신 추정). 위 시간 막대로 시각을 바꾼다.',
    sales: '동별 카드 매출(시간대) — 서울시 추정매출.',
    bus: '버스 정류장 시간대 승차·하차(하루 평균).',
    subr: '지하철역 시간대 승차·하차(하루 평균).',
    vol: '도로 교통량 측정 지점(서울시).',
    bike: '따릉이 대여소.',
    pol: '경찰서·지구대·파출소.', fire: '소방서·안전센터.', er: '응급실 있는 병원.', hosp: '병원·의원.', phar: '약국.',
    bar: '주점 — 밤 순찰 참고.', play: '노래방·PC방.', inn: '숙박업소.', heat: '무더위쉼터.', cold: '한파쉼터.', hyd: '소화전.', wc: '화장실(OSM).',
    school: '학교(OSM).', kids: '유치원·어린이집(OSM).', pg: '놀이터.', park: '공원.', welf: '복지시설.', kyr: '경로당(서울시).', cc: '어린이집(서울시).', kg: '유치원(교육청).', aca: '입시·교과 학원.', edu: '학교(초·중·고·대 · 공식).',
    govr: '관공서(시청·구청·주민센터·세무서·법원·경찰·소방 등 · 서울·경기). 큰 관공서 둘레는 점심 수요와 민원인 낮 유입이 있다.',
    gov: '관공서·주민센터(OSM).', lib: '도서관.', post: '우체국.', bank: '은행·ATM.', conv: '편의점.', fuel: '주유소.', ev: '전기차 충전.', pk: '주차장(OSM).',
    jur: '경찰서 관할 경계(서초·방배 — 반포동은 현장 기준).',
    srcctv: '안심귀갓길 CCTV(서울시).', srbell: '안심벨(비상벨).', srlamp: '안심귀갓길 보안등.', sr112: '112 위치 신고 안내 표지.', srsvc: '안심 서비스·아동안전지킴이집 등.',
    aed: '자동심장충격기(서울·경기).', fw: '소방용수시설(서울시).', pkcctv: '불법 주정차 단속 CCTV.', tow: '견인차량 보관소.', wc2: '공중화장실(서울·경기 공식).',
    gpark: '주차장(경기 공식).', gev: '전기차 충전소(경기).', ger: '응급의료기관(경기).', gfest: '문화축제(경기).', glamp: '보안등(경기 29만 개 · 많이 확대해야 나온다).',
    box: '안심택배함.', dem: '치매안심센터.', tgis: 'T-GIS 신호 교차로(서울시 · 종속 신호 포함).',
    spot: '길목 — 지금 시각 버스·지하철 하차가 많은 곳(숫자 = 순위). 순찰·단속 자리 고르기용.',
    spota: '길목 다발지(참고).', hot10: '사고다발지 10년(2016~2025) 겹친 자리.', jct: '교차로별 10년 사고(서울·경기) — 가장 가까운 교차로 하나에 모은 값.',
    evt: '행사·집회(서울시 문화행사 · 서울경찰청 주요 집회).', her: '국가유산(문화재).',
    flt: '침수 흔적(2010~2025).', flr: '침수 이력이 있는 도로.', und: '침수 이력 지하차도.', ice: '제설함 — 결빙 우려 자리.', hcab: '도로 열선 설치 길.', advb: '제설 전진기지.',
    pbtn: '보행자 작동 신호기(누름 버튼).'
  };
  var LHON = false;
  try { LHON = localStorage.getItem('tg_map2d_lh2') === '1'; } catch (e) {}
  // ---------- 🗣 자동 해설(v2.0.0 · 소유자 「인구분포가 나오면 데이터에 따른 설명 — 모르고 넘어갈 수 있으니」) ----------
  //  숫자를 앱 기준으로 읽어 문장으로 — 기준(몇 배·몇 %p)을 같이 적는다. 「그래서 어떤 장사」 쪽은 일반론이라 그렇게 밝힌다.
  var AREF = null; fetch('data/area-ref.json').then(function (r) { return r.json(); }).then(function (j) { AREF = j; }).catch(function () {});
  var SIDO_S = { '12': '전남광주', '11': '서울', '41': '경기', '28': '인천', '30': '대전', '36': '세종', '43': '충북', '44': '충남', '51': '강원', '26': '부산', '27': '대구', '31': '울산', '47': '경북', '48': '경남', '29': '광주', '46': '전남', '52': '전북', '50': '제주' };
  var SIDO_FULL = { '11': '서울특별시', '41': '경기도', '28': '인천광역시', '30': '대전광역시', '36': '세종특별자치시', '43': '충청북도', '44': '충청남도', '51': '강원특별자치도', '26': '부산광역시', '27': '대구광역시', '31': '울산광역시', '47': '경상북도', '48': '경상남도', '12': '전남광주통합특별시', '52': '전북특별자치도', '50': '제주특별자치도' };
  function sidoOf(gu) { return SIDO_S[String(gu || '11650').slice(0, 2)] || '서울'; }   // v2.7.0 인천부터 — 종전엔 경기가 아니면 모두 「서울」
  function talk(S) {
    var L = [], ref = AREF && AREF.ref[S.sido || '서울'] || null, rn = S.sido || '서울', f1 = function (x) { return (Math.round(x * 10) / 10).toLocaleString(); };
    if (S.wrk != null && S.pop > 50) { var r = S.wrk / S.pop, rr = ref && ref.wrkPerPop;
      L.push(r >= 2 ? '👔 <b>일터형</b> — 일하러 오는 사람(종사자 ' + Math.round(S.wrk).toLocaleString() + '명)이 사는 사람의 <b>' + f1(r) + '배</b>' + (rr ? '(' + rn + ' 평균 ' + rr + '배)' : '') + '. 평일 점심(11~14시)과 퇴근길이 승부이고, 주말·밤에는 손님이 빠진다.'
        : r >= 0.8 ? '🏙 <b>주거·일터 섞임</b> — 종사자가 주민의 ' + f1(r) + '배' + (rr ? '(' + rn + ' 평균 ' + rr + '배)' : '') + '. 점심과 저녁 손님이 둘 다 있다.'
        : '🏠 <b>주거형</b> — 종사자가 주민의 ' + f1(r) + '배뿐' + (rr ? '(' + rn + ' 평균 ' + rr + '배)' : '') + '. 저녁·주말·배달 수요가 중심이고, 평일 낮은 조용한 편이다.'); }
    if (S.corp > 0 && S.wrk > 0) L.push('🏢 사업체 ' + Math.round(S.corp).toLocaleString() + '곳 · 종사자 ' + Math.round(S.wrk).toLocaleString() + '명 — 이 사람들이 낮 동안의 잠재 손님이다(그중 몇 명이 밖에서 사 먹는지는 자료에 없다).');
    if (S.gov && S.gov.n) L.push('🏛 관공서 ' + S.gov.n + '곳(' + Object.keys(S.gov.c).sort(function (a, b) { return S.gov.c[b] - S.gov.c[a]; }).map(function (k) { return k + ' ' + S.gov.c[k]; }).join(' · ') + ') — 공무원 점심과 민원인 낮 유입이 있다. 시청·구청·법원·세무서처럼 큰 곳일수록 크다.');
    if (S.age && S.pop > 50) { var a = S.age, T = a.reduce(function (x, y) { return x + y; }, 0) || 1, y2030 = (a[2] + a[3]) / T * 100, o60 = (a[6] + a[7] + a[8] + a[9]) / T * 100, k19 = (a[0] + a[1]) / T * 100;
      var R2 = ref && ref.age ? ref.age[2] + ref.age[3] : null, R6 = ref && ref.age ? ref.age[6] + ref.age[7] + ref.age[8] + ref.age[9] : null, R1 = ref && ref.age ? ref.age[0] + ref.age[1] : null, dv = function (v, r0) { return r0 == null ? '' : ' (' + rn + ' 평균 ' + f1(r0) + '% · ' + (v - r0 >= 0 ? '+' : '') + f1(v - r0) + '%p)'; };
      L.push('👥 주민 20·30대 <b>' + f1(y2030) + '%</b>' + dv(y2030, R2) + ' · 60세 이상 <b>' + f1(o60) + '%</b>' + dv(o60, R6) + ' · 19세 이하 ' + f1(k19) + '%' + dv(k19, R1) + '.');
      if (R2 != null && y2030 - R2 >= 5) L.push('　→ 젊은 층이 많다: 카페·간편식·배달·저녁 술자리 쪽이 맞는 편 <em>(일반론)</em>');
      if (R6 != null && o60 - R6 >= 5) L.push('　→ 어르신이 많다: 낮 손님 비중이 크고 값에 민감, 일찍 닫는 동네일 수 있다 <em>(일반론)</em>');
      if (R1 != null && k19 - R1 >= 4) L.push('　→ 아이 있는 집이 많다: 가족 외식·학원가 간식·주말 장사 쪽 <em>(일반론)</em>'); }
    if (S.live && S.live.wd) { var W = S.live.wd, dn = (W[11] + W[12] + W[13] + W[14]) / 4 / (((W[0] + W[1] + W[2] + W[3] + W[4]) / 5) || 1), rd = ref && ref.liveDayNight, pk = 0; for (var i = 1; i < 24; i++) if (W[i] > W[pk]) pk = i;
      L.push('🕐 평일 생활인구는 <b>' + pk + '시</b>에 가장 많고, 낮(11~14시)이 새벽의 <b>' + f1(dn) + '배</b>' + (rd ? '(서울 평균 ' + rd + '배)' : '') + ' — ' + (dn >= (rd || 1.07) * 1.25 ? '서울 평균보다 낮에 사람이 더 몰려드는 곳.' : dn <= (rd || 1.07) * 0.85 ? '낮에 사람이 빠져나가는 곳(출근해 나가는 주거지).' : '서울 평균과 비슷하다.'));
      if (S.live.we) { var sw = S.live.we.reduce(function (x, y) { return x + y; }, 0) / (W.reduce(function (x, y) { return x + y; }, 0) || 1); if (sw < 0.9) L.push('　주말 생활인구가 평일의 ' + Math.round(sw * 100) + '% — 주말에 비는 곳(사무실 쪽).'); else if (sw > 1.08) L.push('　주말 생활인구가 평일의 ' + Math.round(sw * 100) + '% — 주말에 더 붐빈다(나들이·쇼핑).'); } }
    if (S.tb && S.tb.some(function (v) { return v; })) { var tt = S.tb.reduce(function (x, y) { return x + y; }, 0) || 1, sh = S.tb.map(function (v) { return v / tt * 100; }), TBN = ['새벽(0~6시)', '아침(6~11시)', '점심(11~14시)', '오후(14~17시)', '저녁(17~21시)', '밤(21~24시)'], RT = ref && ref.tb, best = -1, bd = -99;
      for (var j = 0; j < 6; j++) { var d0 = RT ? sh[j] - RT[j] : 0; if (d0 > bd) { bd = d0; best = j; } }
      L.push('💳 카드 매출은 ' + TBN.map(function (n, k) { return n.split('(')[0] + ' ' + f1(sh[k]) + '%'; }).join(' · ') + (RT && bd >= 3 ? ' — <b>' + TBN[best] + '</b> 비중이 서울 평균(' + RT[best] + '%)보다 ' + f1(bd) + '%p 높다: 그 시간대 상권이다.' : '.')); }
    if (S.dw && S.dw.some(function (v) { return v; })) { var dt = S.dw.reduce(function (x, y) { return x + y; }, 0) || 1, wk = (S.dw[5] + S.dw[6]) / dt * 100, RW = ref && ref.dw ? ref.dw[5] + ref.dw[6] : null;
      L.push('📅 토·일 매출 비중 <b>' + f1(wk) + '%</b>' + (RW ? '(서울 평균 ' + f1(RW) + '%)' : '') + (RW && wk - RW <= -5 ? ' — 주말 장사가 약하다(평일 직장인 상권).' : RW && wk - RW >= 5 ? ' — 주말 장사가 강하다.' : '.')); }
    if (S.ag && S.ag.some(function (v) { return v; })) { var at = S.ag.reduce(function (x, y) { return x + y; }, 0) || 1, AGN = ['10대', '20대', '30대', '40대', '50대', '60대 이상'], am = 0; for (var q = 1; q < 6; q++) if (S.ag[q] > S.ag[am]) am = q;
      L.push('🧾 카드로 돈을 쓰는 사람은 <b>' + AGN[am] + '</b>' + (/[상]$/.test(AGN[am]) ? '이' : '가') + ' 가장 많다(' + f1(S.ag[am] / at * 100) + '%) — 주민 연령과 다르면 밖에서 와서 쓰는 사람이 많다는 뜻.'); }
    if (!L.length) return '';
    return '<div class="talk"><b>🗣 이 자리 읽기</b>' + L.map(function (x) { return '<div>' + x + '</div>'; }).join('') + '<small>기준(앱): 종사자÷주민 2배↑ 일터형 · 0.8배↓ 주거형 · 연령은 ' + rn + ' 평균과 ±5%p · 매출 시간대는 서울 평균과 +3%p. 「→」 줄은 경영 일반론이지 통계가 아니다. 평균은 이 지도에 구운 주민등록·생활인구·서울시 추정매출·SGIS 집계구로 다시 계산(area-ref.json).</small></div>';
  }
  function talkDong(d) { var gu = d.gcd || (d.rg && d.rg.gu) || '11650', x = salesOf(d) || d.sales, S = { sido: sidoOf(gu), age: d.pop && d.pop.age, pop: d.pop && d.pop.tot, live: d.live, tb: x && x.tb, dw: x && x.dw };
    if (!S.live) { var la = liveArr(d); if (la) S.live = la; }
    if (JGGL[gu] && JGGL[gu].done) { var w = 0, c = 0, n = 0; JGGA.forEach(function (q) { if (q.gu === gu && q.t[1] === d.name) { n++; w += q.t[9] || 0; c += q.t[8] || 0; } }); if (n) { S.wrk = w; S.corp = c; } }
    else jgP(gu).then(function () { if (sel && sel.it && sel.it.d === d) show(sel.it); });
    return talk(S); }
  // ---------- 💰 손익 계산(v2.0.0) — 계약서 숫자(확정) · 공공 자료 · 업종 평균(KREI·실태조사)을 한 장에 ----------
  var BZ = { tpl: null, krei: null, bench: null, rates: null }, BZP = null;
  var PNL = { k: 'hansik', c: null, v: {}, res: null, ready: false, wait: false };
  function bzLoad() { if (BZP) return BZP;
    BZP = Promise.all(['data/biz-templates.json', 'data/biz-krei.json', 'data/biz-bench.json', 'data/biz-rates.json'].map(function (u) { return fetch(u).then(function (r) { if (!r.ok) throw new Error(u); return r.json(); }); }))
      .then(function (a) { BZ.tpl = a[0]; BZ.krei = a[1]; BZ.bench = a[2]; BZ.rates = a[3]; return BZ; }).catch(function (e) { BZP = null; throw e; }); return BZP; }
  function kr(t, row) { var T = BZ.krei && BZ.krei.tables[t]; return T && T.rows[row] || null; }
  function krAvg(t, row) { var r = kr(t, row); return r ? r[r.length - 1] : null; }
  function tplOf(k) { return BZ.tpl.items.filter(function (x) { return x.k === k; })[0] || BZ.tpl.items[0]; }
  function rv(k) { var v = BZ.rates[k]; return Array.isArray(v) ? v[0] : v; }
  function empRate() { return rv('pension') + rv('health') * (1 + rv('ltc_of_health')) + rv('emp_ui') + rv('emp_stable') + rv('ind') + rv('commute'); }
  function cardRate(yearMan) { var C = BZ.rates.card; for (var i = 0; i < C.length; i++) if (yearMan <= C[i][0]) return C[i][1]; return null; }
  var PF = [   // [키, 이름, 단위, 설명] — 입력칸 차례
    ['dep', '보증금', '만 원', '계약서의 보증금.'], ['rent', '월세', '만 원/월', '부가세 뺀 월세.'], ['mgmt', '관리비', '만 원/월', '건물 관리비(전기·가스·수도는 아래 기타 비용률에 들어 있다).'],
    ['prem', '권리금', '만 원', '앞 가게에 준 돈. 나갈 때 돌려받을 수 있을지 모르니 비용으로 나눠 갚는다고 본다.'], ['inv', '시설·인테리어 투자', '만 원', '인테리어·주방·집기 등 개업 투자.'], ['mon', '투자 회수 기간', '개월', '권리금·투자를 몇 달에 나눠 갚을지. 숙박·음식점 5년 생존율이 27%라 5년(60개월) 안에 갚는 것이 안전하다는 뜻으로 기본 60.'],
    ['conv', '보증금 기회비용', '%/년', '보증금을 은행에 두었으면 받을 이자. 기본 = 한국은행 기준금리. 법정 전환율 상한(연 12% 또는 기준금리×4.5 중 낮은 것)까지 바꿔 볼 수 있다.'],
    ['area', '면적', '㎡', '전용 면적(3.3㎡ = 1평).'], ['seats', '좌석', '석', '앉을 자리 수.'], ['turns', '하루 회전 한계', '회', '좌석이 하루에 몇 번 찰 수 있나 — 물리 상한 계산용(가정 · 기본은 업종 평균 손님 ÷ 좌석).'],
    ['hours', '영업시간', '시간/일', '문 여는 시간.'], ['days', '영업일', '일/월', '한 달에 문 여는 날.'], ['price', '객단가', '원', '손님 1명(배달·포장은 1건)이 내는 돈.'], ['cust', '하루 손님', '명', '홀·배달·포장을 다 합친 하루 손님(주문) 수 — 이 값이 매출을 정한다. 모르면 비워 두고 손익분기 손님 수를 본다.'],
    ['food', '재료비율', '%', '매출 중 식재료·주류 구입비.'], ['other', '기타 비용률', '%', '전기·가스·수도·소모품·수선 등 기타 비용 ÷ 매출.'], ['dlv', '배달 매출 비중', '%', '전체 매출 중 배달 몫.'], ['to', '포장 매출 비중', '%', '전체 매출 중 테이크아웃 몫 — 홀 좌석을 안 쓰는 매출이라 물리 상한 계산에 쓴다.'], ['dlvfee', '배달 비용률', '% (배달 매출 대비)', '배달앱 수수료·광고·배달대행비 ÷ 배달 매출.'],
    ['staffN', '직원 수', '명', '사장·무급 가족을 뺀 고용 인원.'], ['staffH', '직원 1명 주 근무', '시간/주', '주 15시간 이상이면 주휴수당·퇴직금이 생긴다.'], ['wage', '직원 시급', '원', '기본 = 2026년 최저임금.'],
    ['open', '문 여는 시각', '시', '예 10.5 = 10시 30분.', 'sch'], ['close', '문 닫는 시각', '시', '자정을 넘기면 24 이상(예 26 = 새벽 2시).', 'sch'], ['brk', '브레이크타임', '분/일', '점심과 저녁 사이 문을 닫는 시간 — 영업시간에서 빠지고 사장은 가게에 있는 것으로 본다.', 'sch'],
    ['rest', '정기 휴무', '일/주', '매주 쉬는 날 수(0 = 휴일 없음).', 'sch'], ['prep', '사장 준비·정리', '분/일', '문 열기 전 장보기·준비 + 닫은 뒤 정리·마감.', 'sch'],
    ['c_util', '전기·가스·수도', '만 원/월', '고지서 값 — 냉난방·주방 화력이 크면 크다.', 'cost'], ['c_net', '인터넷·전화·POS·키오스크', '만 원/월', '통신·단말기·키오스크 대여.', 'cost'], ['c_clean', '청소·위생·방역', '만 원/월', '청소 용역·방역 업체·위생 소모품.', 'cost'],
    ['c_ins', '화재·배상 보험', '만 원/월', '다중이용업소는 화재배상책임보험 의무.', 'cost'], ['c_acct', '세무 기장료', '만 원/월', '세무사 기장·신고 대행.', 'cost'], ['c_sup', '소모품·포장재', '만 원/월', '컵·포장 용기·냅킨 등(재료비에 안 넣었다면).', 'cost'],
    ['c_ad', '광고·판촉', '만 원/월', '배달앱 광고·전단·SNS.', 'cost'], ['c_fix', '수선·유지', '만 원/월', '기계 수리·정기 점검.', 'cost'], ['c_tax', '세금과 공과', '만 원/월', '재산세·주민세·면허세·협회비 등(종합소득세 아님).', 'cost'], ['c_etc', '그 밖', '만 원/월', '음악 저작권료·정수기·렌탈·차량 등.', 'cost'],
    ['own', '사장 인원', '명', '일하는 사장(부부면 2).'], ['ownH', '사장 하루 일하는 시간', '시간/일', '기본 = 영업시간(문 열 때 늘 있는 경우).'], ['fam', '무급 가족 일손', '명', '월급 안 받는 가족. 사장 시급 계산 때 사람 수에 넣는다.']
  ];
  function pnlDefaults(k) {
    var t = tplOf(k), R = t.krei, v = {}, sal = krAvg('sales', R), dd = krAvg('days', R) || 27.7, ch = kr('channel', R);
    v.rent = krAvg('rent', R); v.dep = krAvg('deposit', R); v.prem = 0; v.inv = Math.round(krAvg('invest', R) || 0); v.mon = 60; v.conv = (rv('base_rate') * 100);
    v.mgmt = 0; v.area = krAvg('area', R); v.seats = Math.round(krAvg('seats', R) || 0) || null; v.hours = krAvg('hours', R); v.days = dd; v.price = krAvg('price', R);
    v.cust = sal && v.price ? Math.round(sal * 1e4 / 12 / dd / v.price) : null;
    v.turns = v.seats && v.cust ? Math.max(0.5, Math.round(v.cust * (ch ? ch[1] / 100 : 1) / v.seats * 10) / 10) : null;
    v.food = sal ? Math.round(krAvg('food', R) / sal * 1000) / 10 : null; v.other = sal ? Math.round((krAvg('other', R) + krAvg('tax', R)) / sal * 1000) / 10 : null;
    v.dlv = ch ? ch[2] : 0; v.to = ch ? ch[3] : 0; var dc = (krAvg('dlvapp_cost', R) || 0) + (krAvg('dlvagent_cost', R) || 0), dshare = (kr('dlvapp', R) || [0, 0])[1] / 100;
    v.dlvfee = sal && ch && ch[2] > 0 && dc ? Math.min(60, Math.round(dc * 12 / 1e4 * (dshare || 1) / (sal * ch[2] / 100) * 1000) / 10) : 0;
    var wg = krAvg('wage', R), mw = rv('min_wage'), W = 52 / 12, hEq = wg ? wg * 1e4 / 12 / (mw * (1 + empRate())) : 0;
    v.wage = mw; if (hEq > 0) { v.staffN = Math.max(1, Math.round(hEq / W / 1.2 / 40 + 0.4)); v.staffH = Math.round(Math.min(40, hEq / W / 1.2 / v.staffN)); } else { v.staffN = 0; v.staffH = 0; }
    v.own = 1; v.fam = 0;
    var hol = kr('holiday', R); v.open = 10; v.close = Math.round((10 + (v.hours || 0)) * 10) / 10; v.brk = 0; v.rest = hol && hol[1] >= 50 ? 1 : 0; v.prep = 60; v.ownH = Math.round(((v.hours || 0) + 1) * 10) / 10;   // v2.36.0 사장 일정 — 영업시간·휴무는 KREI, 여는 시각·준비 시간은 가정
    ['c_util', 'c_net', 'c_clean', 'c_ins', 'c_acct', 'c_sup', 'c_ad', 'c_fix', 'c_etc'].forEach(function (q) { v[q] = 0; }); v.c_tax = krAvg('tax', R) ? Math.round(krAvg('tax', R) / 12 * 10) / 10 : 0; v.useItem = 0;
    Object.keys(v).forEach(function (x) { if (typeof v[x] === 'number') v[x] = Math.round(v[x] * 10) / 10; });
    return v;
  }
  var PSRC = { open: '가정(10시)', close: '여는 시각 + KREI 표24 영업시간', brk: '가정(없음)', rest: 'KREI 표26 정기휴무 「매주」가 절반 넘으면 1', prep: '가정(1시간)', c_tax: 'KREI 표100 ÷ 12', rent: 'KREI 표20', dep: 'KREI 표19', inv: 'KREI 표31', area: 'KREI 표12', seats: 'KREI 표29', hours: 'KREI 표24', days: 'KREI 표25', price: 'KREI 표67', cust: 'KREI 표95 매출 ÷ 객단가 ÷ 영업일', food: 'KREI 표97÷95', other: 'KREI 표100+103÷95', dlv: 'KREI 표58', to: 'KREI 표58', dlvfee: 'KREI 표51·54÷배달 매출', staffN: 'KREI 표98 인건비를 최저시급 시간으로', staffH: '같은 환산', wage: '2026 최저임금', conv: '기준금리', mon: '가정(5년)', turns: '평균 손님÷좌석(가정)', ownH: '영업시간', own: '가정', fam: '가정', prem: '0(직접)', mgmt: '0(직접)' };
  function pnlCalc(v) {
    var W = 52 / 12, n = function (x) { return +x || 0; }, er = empRate(), o = {};
    o.convRent = n(v.rent) + n(v.dep) * n(v.conv) / 100 / 12; o.amort = (n(v.prem) + n(v.inv)) / Math.max(1, n(v.mon));
    var sh = n(v.staffH), hrs = sh * W + (sh >= 15 ? sh / 40 * 8 * W : 0); o.staffPay = hrs * n(v.wage) / 1e4; o.staffOne = o.staffPay * (1 + er + (sh >= 15 ? 1 / 12 : 0)); o.staff = n(v.staffN) * o.staffOne; o.staffHrs = hrs;
    o.items = ['c_util', 'c_net', 'c_clean', 'c_ins', 'c_acct', 'c_sup', 'c_ad', 'c_fix', 'c_tax', 'c_etc'].reduce(function (a, q) { return a + n(v[q]); }, 0);
    o.fixed = o.convRent + n(v.mgmt) + o.amort + o.staff + (v.useItem ? o.items : 0);
    o.salesQ = v.cust ? n(v.price) * n(v.cust) * n(v.days) / 1e4 : null;
    var guess = o.salesQ || o.fixed * 4; o.card = cardRate(guess * 12); if (o.card == null) o.card = 0.02;
    o.yu = tplOf(PNL.k).yuheung ? rv('yuheung_tax') * 1.3 : 0;
    o.varRate = n(v.food) / 100 + (v.useItem ? 0 : n(v.other) / 100) + o.card * 1.1 + n(v.dlv) / 100 * n(v.dlvfee) / 100 + o.yu; o.cm = 1 - o.varRate;
    o.bep = o.cm > 0 ? o.fixed / o.cm : null; o.ownHrs = (n(v.own) + n(v.fam)) * n(v.ownH) * n(v.days); o.mwLine = o.cm > 0 ? (o.fixed + rv('min_wage') * n(v.own) * n(v.ownH) * n(v.days) / 1e4) / o.cm : null;
    var dayRev = n(v.price) * n(v.days) / 1e4; o.bepCust = o.bep && dayRev ? o.bep / dayRev : null; o.mwCust = o.mwLine && dayRev ? o.mwLine / dayRev : null;
    o.cap = n(v.seats) && n(v.turns) ? n(v.seats) * n(v.turns) * n(v.price) * n(v.days) / 1e4 / Math.max(0.1, 1 - n(v.dlv) / 100 - n(v.to) / 100) : null;
    o.at = function (s) { var p = s * o.cm - o.fixed, tx = ownTax(p, n(v.own)); return { sales: s, profit: p, tax: tx, net: p - tx.sum, hourly: o.ownHrs ? p * 1e4 / o.ownHrs : null, netHourly: o.ownHrs ? (p - tx.sum) * 1e4 / o.ownHrs : null, rentPct: s ? o.convRent / s * 100 : null }; };
    if (o.salesQ != null) o.q = o.at(o.salesQ);
    o.five = n(v.staffN) >= 5; o.er = er;
    return o;
  }

  // v2.36.0 사장 본인 4대보험(지역가입자)·종합소득세 어림 — 소득 = 사장 몫(세전) · 사장이 둘이면 반씩 · 요율 biz-rates.json · 세율 소득세법 제55조 ①(2023년 귀속부터)
  var ITAX = [[1400, 0.06, 0], [5000, 0.15, 126], [8800, 0.24, 576], [15000, 0.35, 1544], [30000, 0.38, 1994], [50000, 0.40, 2594], [100000, 0.42, 3594], [1e12, 0.45, 6594]];
  function incTax(base) { if (base <= 0) return 0; for (var i = 0; i < ITAX.length; i++) if (base <= ITAX[i][0]) return base * ITAX[i][1] - ITAX[i][2]; return 0; }
  function ownTax(pMonth, nOwn) {
    var k = Math.max(1, nOwn || 1), y = Math.max(0, pMonth) * 12 / k, pen = y * rv('pension') * 2, hea = y * rv('health') * 2 * (1 + rv('ltc_of_health')), base = Math.max(0, y - pen - hea - 150), it = incTax(base), loc = it * 0.1;
    return { pen: pen * k / 12, hea: hea * k / 12, it: it * k / 12, loc: loc * k / 12, sum: (pen + hea + it + loc) * k / 12, base: base, rate: base > 0 ? (it + loc) / y : 0 }; }
  function wn(x) { return x == null || !isFinite(x) ? '-' : (Math.abs(x) >= 10000 ? (x / 10000).toFixed(2).replace(/\.?0+$/, '') + '억' : Math.round(x).toLocaleString() + '만') + ' 원'; }
  function pnlOpen(c) {
    var el = $('m2dPnl'); if (!el) return; el.classList.add('on'); el.classList.remove('min'); document.body.classList.add('pnlon');
    ['m2dRad', 'm2dBiz'].forEach(function (id) { if ($(id)) $(id).classList.remove('on'); }); document.body.classList.remove('radon', 'bizon');
    if (c) PNL.c = c; el.innerHTML = '<div class="lg-h"><b>💰 손익 계산</b><span><button data-px="x">닫기</button></span></div><p class="lg-n">업종 자료를 받는 중…</p>';
    bzLoad().then(function () { if (!PNL.ready) { PNL.v = pnlDefaults(PNL.k); PNL.ready = true; } pnlForm(); pnlGather(); }).catch(function (e) { el.innerHTML += '<p class="lg-n" style="color:#b91c1c">자료를 받지 못했다(' + esc(e && e.message || e) + ')</p>'; });
  }
  function pnlGather() {
    if (!PNL.c) { PNL.res = null; pnlOut(); return; }
    var t = tplOf(PNL.k); PNL.wait = true; pnlOut(); RAD.c = PNL.c; RAD.r = 500; RAD.ind = ''; RAD.sind = t.seoul || ''; radRun();
    var tk = setInterval(function () { if (RAD.busy) return; clearInterval(tk); PNL.res = RAD.res; PNL.wait = false; pnlOut(); }, 300);
  }


  // ---------- v2.37.0 📒 관계 장부(증거 사다리) — data/relations-ledger.json · 3단계 이상만 「근거」, 1~2단계는 「가설」 · 4단계(현장 확인)는 이 기기 안 메모만 ----------
  //  규칙: 장부에 없는 관계는 해석으로 화면에 내보내지 않는다 — 새 해석을 넣을 때 장부 항목(가설·단위·검정·등급·주의)을 먼저 만든다
  var LEDG = null, LEDGP = null;
  function ledgLoad() { if (LEDGP) return LEDGP; LEDGP = fetch('data/relations-ledger.json').then(function (r) { return r.json(); }).then(function (j) { LEDG = {}; j.relations.forEach(function (r) { LEDG[r.id] = r; }); LEDG._meta = j; var c = $('m2dCard'); if (c && c.classList.contains('on') && sel && sel.it) show(sel.it); paintPre(); return j; }).catch(function () { LEDG = {}; }); return LEDGP; }
  function ledgBadge(id) { if (!LEDG) { ledgLoad(); return '<span class="lgb">' + id + '</span>'; } var r = LEDG[id]; if (!r) return ''; var g = +r['등급'] || 0, f = fieldCnt(id);
    return '<span class="lgb g' + g + '" title="' + esc(r['가설'] + ' — ' + (r['판정'] || '')) + '">' + id + ' · ' + g + '단계 ' + (g >= 3 ? '근거' : '가설') + (f.n ? ' · 현장 ' + f.yes + '/' + f.n : '') + '</span>'; }
  function ledgLine(id) { if (!LEDG) { ledgLoad(); return ''; } var r = LEDG[id]; if (!r) return ''; return '<div class="talk"><b>📒 관계 장부 ' + ledgBadge(id) + '</b><div>' + esc(r['가설']) + '</div><div>' + esc(r['판정'] || '') + '</div>' + (r['주의'] ? '<small>주의 — ' + esc(r['주의']) + '</small>' : '') + (r['다음'] ? '<small>다음 — ' + esc(r['다음']) + '</small>' : '') + '</div>'; }
  var PRENOTE = { night: '근거 — R3 3단계: 주점 비중이 높은 100m 칸은 밤(20~6시) 사고 비율이 높다(서울 두 지역 묶음에서 재현 · 번화가 효과만은 아님)', traffic: '기준선 — R1 3단계: 지난 5년 사고가 많던 칸은 다음 5년에도 많다(상위 1% 칸의 97%가 다음 기간 상위 5%)', acc10: '기준선 R1(3단계) · 「🚗 사고 10년」 범례의 「사고율」 = R2(3단계)' };
  // R2 사고율 — 150m 안 버스·지하철 하루 하차 합으로 나눈다(서울 교통카드 · 받은 구만)
  var RTD = { n: -1, stops: [], grid: {} };
  function rateReady() { if (!PUB) return; var v = viewLL(); rIdx().forEach(function (g) { var x = g.box; if (g.gu.slice(0, 2) !== '11' || !(g.bytes || {}).transit || x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return; xLoad(g.gu); });
    var n = PUB.bus.length + PUB.subr.length; if (n === RTD.n) return; RTD.n = n; RTD.grid = {}; RTD.stops = [];
    function add(p, off) { if (!off) return; var k = Math.floor(p[0] / 300) + ',' + Math.floor(p[1] / 300); (RTD.grid[k] = RTD.grid[k] || []).push([p, off]); }
    PUB.bus.forEach(function (q) { var f = FLOW.bus[q.o.id]; if (f) add(q.p, f[1].reduce(function (a, b) { return a + b; }, 0)); });
    PUB.subr.forEach(function (q) { var f = FLOW.sub[q.name]; if (f) add(q.p, f[1].reduce(function (a, b) { return a + b; }, 0)); });
    A10.forEach(function (x) { x.rt = undefined; }); rateHid(); }
  function a10Rate(x) { if (x.rt !== undefined) return x.rt; var gx = Math.floor(x.p[0] / 300), gy = Math.floor(x.p[1] / 300), off = 0;
    for (var i = -1; i <= 1; i++) for (var j = -1; j <= 1; j++) (RTD.grid[(gx + i) + ',' + (gy + j)] || []).forEach(function (q) { if (dTrue(q[0], x.p) <= 150) off += q[1]; });
    var tot = x.c.slice(2, 12).reduce(function (a, b) { return a + b; }, 0); x.rt = off >= 200 && tot ? { v: tot / off * 1000, off: off, tot: tot } : null; return x.rt; }
  function rateHid() { var L = A10.map(function (x) { return [x, a10Rate(x)]; }).filter(function (q) { return q[1]; }); if (L.length < 20) return;
    var rs = L.map(function (q) { return q[1].v; }).sort(function (a, b) { return a - b; }), ts = L.map(function (q) { return q[1].tot; }).sort(function (a, b) { return a - b; }), r90 = rs[Math.floor(rs.length * 0.9)], t90 = ts[Math.floor(ts.length * 0.9)];
    L.forEach(function (q) { q[1].hid = q[1].v >= r90 && q[1].tot < t90; }); }
  // 4단계 — 현장 확인 메모(이 기기 localStorage 만 · 공개 저장소·서버로 가지 않는다)
  var FIELD = []; try { FIELD = JSON.parse(localStorage.getItem('tg_map2d_field') || '[]') || []; } catch (e) {}
  function fieldSave() { try { localStorage.setItem('tg_map2d_field', JSON.stringify(FIELD)); } catch (e) {} }
  function fieldCnt(id) { var o = { n: 0, yes: 0 }; FIELD.forEach(function (f) { if (f.r === id) { o.n++; if (f.v === 'yes') o.yes++; } }); return o; }
  function fieldHtml(m) { var ll = [m[0] / KX + LON0, LAT0 - m[1] / KY], near = FIELD.filter(function (f) { return dTrue(P(f.ll[1], f.ll[0]), m) <= 200; });
    var opts = (LEDG ? Object.keys(LEDG).filter(function (k) { return k !== '_meta'; }) : ['R1', 'R2', 'R3', 'R4']).map(function (k) { return '<option value="' + k + '">' + k + (LEDG && LEDG[k] ? ' — ' + esc(String(LEDG[k]['가설']).slice(0, 26)) : '') + '</option>'; }).join('') + '<option value="자유">자유 메모</option>';
    return '<div class="fld"><b>✅ 현장 확인 — 4단계(이 기기에만 저장)</b>' + (near.length ? '<div class="fl">' + near.slice(-6).map(function (f) { return '<div>' + esc(f.t) + ' · ' + esc(f.r) + ' · ' + ({ yes: '✅ 맞다', no: '❌ 아니다', unk: '❔ 모르겠다' })[f.v] + (f.m ? ' — ' + esc(f.m) : '') + ' <button data-fdel="' + f.id + '" aria-label="지우기">×</button></div>'; }).join('') + '</div>' : '') +
      '<div class="ff"><select data-fr>' + opts + '</select><select data-fv><option value="yes">✅ 맞다</option><option value="no">❌ 아니다</option><option value="unk">❔ 모르겠다</option></select><input data-fm placeholder="메모(사람 이름·차량번호는 적지 않는다)" maxlength="200"><button data-fadd="' + ll[1].toFixed(5) + ',' + ll[0].toFixed(5) + '">저장</button></div>' +
      '<small>기록은 이 폰·PC 브라우저 안에만 남는다(밖으로 나가지 않는다) · 이 기기 기록 ' + FIELD.length + '건 <button data-fexp="1">📤 파일로 내보내기</button> <label class="fimp">📥 가져오기<input type="file" accept=".json" data-fimp hidden></label></small></div>'; }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-fadd],[data-fdel],[data-fexp]'); if (!b) return; var cd = b.closest('#m2dCard');
    if (b.getAttribute('data-fadd')) { var a = b.getAttribute('data-fadd').split(','), box = b.closest('.ff'), m = (box.querySelector('[data-fm]').value || '').replace(/\d{2,3}[가-힣]\d{4}/g, '○○○').slice(0, 200);
      FIELD.push({ id: Date.now().toString(36), t: new Date().toISOString().slice(0, 10), ll: [+a[0], +a[1]], r: box.querySelector('[data-fr]').value, v: box.querySelector('[data-fv]').value, m: m }); fieldSave(); if (sel && sel.it) show(sel.it); return; }
    if (b.getAttribute('data-fdel')) { var id = b.getAttribute('data-fdel'); FIELD = FIELD.filter(function (f) { return f.id !== id; }); fieldSave(); if (sel && sel.it) show(sel.it); return; }
    if (b.getAttribute('data-fexp')) { var bl = new Blob([JSON.stringify({ schema: 'tg-field/1', items: FIELD }, null, 1)], { type: 'application/json' }), u = URL.createObjectURL(bl), aa = document.createElement('a'); aa.href = u; aa.download = '현장확인_' + new Date().toISOString().slice(0, 10) + '.json'; document.body.appendChild(aa); aa.click(); setTimeout(function () { URL.revokeObjectURL(u); aa.remove(); }, 500); } });
  document.addEventListener('change', function (e) { var t = e.target; if (!t.hasAttribute || !t.hasAttribute('data-fimp') || !t.files || !t.files[0]) return; var fr = new FileReader();
    fr.onload = function () { try { var j = JSON.parse(fr.result), it = (j && j.items) || [], seen = {}; FIELD.forEach(function (f) { seen[f.id] = 1; }); it.forEach(function (f) { if (f && f.id && !seen[f.id] && f.ll) FIELD.push(f); }); fieldSave(); if (sel && sel.it) show(sel.it); } catch (e2) { alert('현장 확인 파일이 아니다'); } }; fr.readAsText(t.files[0]); });
  function ledgRel(m) { if (!LEDG) { ledgLoad(); return ''; } var ids = Object.keys(LEDG).filter(function (k) { return k !== '_meta'; });
    return '<details class="ledg"><summary>📒 관계 장부 — 검증 등급 ' + ids.length + '개</summary>' + ids.map(function (k) { var r = LEDG[k]; return '<div>' + ledgBadge(k) + ' ' + esc(r['가설']) + '<small>' + esc(r['판정'] || '') + '</small></div>'; }).join('') +
      '<p class="relh">사다리 — 1 공존 · 2 시간 동조 · 3 재현(기간·지역 분할) · 4 현장 확인. 3단계 이상만 근무 묶음 판단에 쓴다 · R1(과거 사고 → 미래 사고)보다 나은 정보를 줄 때만 값어치가 있다.</p>' + fieldHtml(m) + '</details>'; }
  // ---------- v2.36.0 개업 손익 시뮬레이션 — 소유자 「업종별 개업 손익 · 시뮬레이션 · 사장 일정·휴무·브레이크 · 4대보험·전기·청소·인터넷·세금 · 그래프 · 지역별 개업 초기비용」 ----------
  var FTC = null, FTCP = null;
  var TPLCAT = { cafe: ['커피'], cafe_low: ['커피'], drink: ['음료 (커피 외)', '아이스크림/빙수 '], bakery: ['제과제빵'], hansik: ['한식'], meat: ['한식'], noodle: ['한식'], seafood: ['한식', '일식'], chinese: ['중식'], japanese: ['일식'], western: ['서양식', '기타 외국식'], chicken: ['치킨'], pizza: ['피자', '패스트푸드'], bunsik: ['분식'], delivery: ['분식', '패스트푸드', '기타 외식'], hof: ['주점'], pub: ['주점'] };
  function ftcLoad() { if (FTCP) return FTCP; FTCP = fetch('data/ftc-brands.json').then(function (r) { return r.json(); }).then(function (j) { FTC = j; if ($('m2dPnl') && $('m2dPnl').classList.contains('on')) pnlForm(); return j; }).catch(function () { FTC = { b: [], cats: [] }; }); return FTCP; }
  function ftcList(k) { if (!FTC) return null; var cs = (TPLCAT[k] || []).map(function (c) { return FTC.cats.indexOf(c); }).filter(function (i) { return i >= 0; }); if (!cs.length) return null; return FTC.b.filter(function (r) { return cs.indexOf(r[1]) >= 0; }); }
  function brandOf(nm) { return FTC && nm ? FTC.b.filter(function (r) { return r[0] === nm; })[0] : null; }
  function brandApply(nm) { PNL.brand = nm; var r = brandOf(nm), v = PNL.v;
    if (r) { if (r[6] && v.price && v.days) v.cust = Math.round(r[6] * 1000 / 12 / v.days / v.price); if (r[6] && r[7]) v.area = Math.round(r[6] / r[7] * 3.305785 * 10) / 10; if (r[9] && r[9][4]) v.inv = Math.max(+v.inv || 0, Math.round(r[9][4] / 10)); }
    pnlForm(); }
  function row2(k, val) { return '<div class="rcard">' + row(k, val) + '</div>'; }
  function simBox() { var v = PNL.v, c0 = Math.max(60, Math.round((+v.cust || 50) * 3)), p0 = +v.price || 10000, r0 = +v.rent || 100;
    function sl(k, lab, mn, mx, st) { return '<label class="sim"><span>' + lab + ' <b data-simv="' + k + '"></b></span><input type="range" data-pf="' + k + '" min="' + mn + '" max="' + mx + '" step="' + st + '" value="' + (v[k] == null ? 0 : v[k]) + '"></label>'; }
    return '<details open class="simb"><summary><b>🎚 시뮬레이션 — 끌어서 바꿔 보기</b> <small>(그래프·결과가 바로 따라 움직인다)</small></summary>' + sl('cust', '하루 손님', 0, c0, 1) + sl('price', '객단가', Math.round(p0 * 0.4), Math.round(p0 * 2), 100) + sl('rent', '월세(만 원)', 0, Math.round(Math.max(r0 * 3, 300)), 5) + sl('staffN', '직원 수', 0, 10, 1) + sl('days', '영업일/월', 15, 31, 0.5) + '</details>'; }
  function simLab() { var el = $('m2dPnl'); if (!el) return; el.querySelectorAll('[data-simv]').forEach(function (b) { var k = b.getAttribute('data-simv'), x = PNL.v[k]; b.textContent = x == null ? '-' : (k === 'price' ? Math.round(x).toLocaleString() + '원' : k === 'rent' ? Math.round(x) + '만' : x); }); }
  function schSync() { var v = PNL.v, el = $('m2dPnl'), o = +v.open || 0, c = +v.close || 0, b = (+v.brk || 0) / 60, r = Math.min(7, Math.max(0, +v.rest || 0)), pr = (+v.prep || 0) / 60;
    v.hours = Math.max(0, Math.round((c - o - b) * 10) / 10); v.days = Math.round((7 - r) * 52 / 12 * 10) / 10; v.ownH = Math.round((c - o + pr) * 10) / 10;
    ['hours', 'days', 'ownH'].forEach(function (k) { el.querySelectorAll('[data-pf="' + k + '"]').forEach(function (x) { x.value = v[k]; }); }); simLab(); }
  function hmT(x) { x = +x || 0; var h = Math.floor(x), m = Math.round((x - h) * 60); return (h >= 24 ? '다음날 ' + ('0' + (h - 24)).slice(-2) : ('0' + h).slice(-2)) + ':' + ('0' + m).slice(-2); }
  function schText(v) { var pr = (+v.prep || 0) / 60, half = pr / 2; return '사장 하루 <b>' + hmT((+v.open || 0) - half) + ' ~ ' + hmT((+v.close || 0) + half) + '</b>(준비·정리 ' + Math.round(pr * 60) + '분 포함 ' + v.ownH + '시간)' + (+v.brk ? ' · 브레이크 ' + v.brk + '분' : '') + ' · ' + (+v.rest ? '매주 ' + v.rest + '일 휴무' : '휴일 없음') + ' → 한 달 영업 ' + v.days + '일 · 사장 약 <b>' + Math.round((+v.ownH || 0) * (+v.days || 0)) + '시간</b>(주 ' + Math.round((+v.ownH || 0) * (7 - (+v.rest || 0))) + '시간)'; }
  // 그림 — 폭포(매출 → 비용 → 사장 몫) · 손님 수 곡선 · 시나리오 막대
  function svgWaterfall(o, v) { var Q = o.q; if (!Q) return ''; var S0 = o.salesQ, card = S0 * o.card * 1.1, dlv = S0 * (+v.dlv || 0) / 100 * (+v.dlvfee || 0) / 100, food = S0 * (+v.food || 0) / 100, oth = v.useItem ? o.items : S0 * (+v.other || 0) / 100;
    var L = [['매출', S0, 1], ['재료', food], ['카드·배달', card + dlv + (o.yu || 0) * S0], ['기타 비용', oth], ['임대(환산)', o.convRent + (+v.mgmt || 0)], ['직원', o.staff], ['투자 상각', o.amort], ['사장 보험·세금', Q.tax.sum], ['사장 몫(세후)', Q.net, 2]];
    var W = 520, H = 190, mx = S0 * 1.05, bw = W / L.length, y = function (x) { return H - 22 - x / mx * (H - 40); }, cur = S0, g = '';
    L.forEach(function (it, i) { var x0 = i * bw + 6, w = bw - 12, top, bot, col;
      if (it[2] === 1) { top = y(S0); bot = y(0); col = '#2563eb'; } else if (it[2] === 2) { top = y(Math.max(0, it[1])); bot = y(Math.min(0, it[1]) < 0 ? 0 : 0); col = it[1] >= 0 ? '#16a34a' : '#dc2626'; if (it[1] < 0) { top = y(0); bot = Math.min(H - 4, y(0) + (-it[1]) / mx * (H - 40)); } }
      else { top = y(cur); cur -= it[1]; bot = y(Math.max(cur, 0)); col = '#f59e0b'; }
      g += '<rect x="' + x0 + '" y="' + Math.min(top, bot) + '" width="' + w + '" height="' + Math.max(1, Math.abs(bot - top)) + '" rx="3" fill="' + col + '"/><text x="' + (x0 + w / 2) + '" y="' + (Math.min(top, bot) - 3) + '" font-size="10" text-anchor="middle" fill="currentColor">' + Math.round(it[1]).toLocaleString() + '</text><text x="' + (x0 + w / 2) + '" y="' + (H - 6) + '" font-size="9.5" text-anchor="middle" fill="currentColor">' + it[0] + '</text>'; });
    return '<div class="simc"><b>💧 한 달 돈의 흐름</b> <small>(만 원 · 매출에서 비용을 차례로 빼면 사장 몫)</small><svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="한 달 돈의 흐름">' + g + '<line x1="0" x2="' + W + '" y1="' + y(0) + '" y2="' + y(0) + '" stroke="currentColor" stroke-opacity=".3"/></svg></div>'; }
  function svgCurve(o, v) { if (!o.bep || !v.price || !v.days) return ''; var cmax = Math.max(40, Math.ceil(Math.max(+v.cust || 0, o.mwCust || 0, o.bepCust || 0) * 1.6)), W = 520, H = 200, P0 = 34;
    var pts = [], mn = 0, mx = 0; for (var c = 0; c <= cmax; c += Math.max(1, cmax / 60)) { var a = o.at(c * v.price * v.days / 1e4); pts.push([c, a.net]); mn = Math.min(mn, a.net); mx = Math.max(mx, a.net); }
    var X = function (c) { return P0 + c / cmax * (W - P0 - 8); }, Y = function (p) { return 10 + (mx - p) / ((mx - mn) || 1) * (H - 34); };
    var line = pts.map(function (q, i) { return (i ? 'L' : 'M') + X(q[0]).toFixed(1) + ' ' + Y(q[1]).toFixed(1); }).join(' ');
    function vl(c, col, lab) { return c ? '<line x1="' + X(c) + '" x2="' + X(c) + '" y1="8" y2="' + (H - 24) + '" stroke="' + col + '" stroke-dasharray="4 3"/><text x="' + (X(c) + 3) + '" y="18" font-size="10" fill="' + col + '">' + lab + ' ' + Math.round(c) + '명</text>' : ''; }
    var cur = +v.cust ? o.at(v.cust * v.price * v.days / 1e4) : null;
    return '<div class="simc"><b>📈 하루 손님 수에 따른 사장 몫(세후)</b> <small>(만 원/월)</small><svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="손님 수 곡선"><line x1="' + P0 + '" x2="' + W + '" y1="' + Y(0) + '" y2="' + Y(0) + '" stroke="currentColor" stroke-opacity=".35"/><path d="' + line + '" fill="none" stroke="#2563eb" stroke-width="2.5"/>' +
      vl(o.bepCust, '#dc2626', '손익분기') + vl(o.mwCust, '#f59e0b', '최저시급') + (cur ? '<circle cx="' + X(+v.cust) + '" cy="' + Y(cur.net) + '" r="5" fill="#111827"/><text x="' + (X(+v.cust) + 7) + '" y="' + (Y(cur.net) - 6) + '" font-size="11" font-weight="700" fill="currentColor">지금 ' + v.cust + '명 → ' + Math.round(cur.net).toLocaleString() + '만</text>' : '') +
      '<text x="2" y="' + (Y(mx) + 4) + '" font-size="9.5" fill="currentColor">' + Math.round(mx) + '</text><text x="2" y="' + (Y(mn) + 4) + '" font-size="9.5" fill="currentColor">' + Math.round(mn) + '</text><text x="' + (W - 4) + '" y="' + (H - 6) + '" font-size="9.5" text-anchor="end" fill="currentColor">하루 손님 ' + cmax + '명</text></svg></div>'; }
  function svgScen(o, v) { if (!v.price || !v.days) return ''; var base = +v.cust || o.mwCust || o.bepCust; if (!base) return ''; var br = brandOf(PNL.brand), L = [['비관 −30%', base * 0.7], ['보통', base], ['낙관 +30%', base * 1.3]];
    if (br && br[6]) L.push(['브랜드 평균', br[6] * 1000 / 12 / v.days / v.price]); if (PNL.seoulPS) L.push(['이 자리 카드 추정', PNL.seoulPS * 1e4 / v.days / v.price]);
    var A = L.map(function (q) { return [q[0], q[1], o.at(q[1] * v.price * v.days / 1e4).net]; }), mx = Math.max.apply(null, A.map(function (a) { return Math.abs(a[2]); })) || 1, W = 520, rowH = 24, H = A.length * rowH + 8, mid = 200;
    var g = A.map(function (a, i) { var w = Math.abs(a[2]) / mx * (W - mid - 70), x = a[2] >= 0 ? mid : mid - Math.min(mid - 6, w), yy = 4 + i * rowH; return '<text x="0" y="' + (yy + 15) + '" font-size="11" fill="currentColor">' + a[0] + ' · ' + Math.round(a[1]) + '명</text><rect x="' + x + '" y="' + (yy + 3) + '" width="' + Math.max(1, Math.min(w, a[2] >= 0 ? W : mid - 6)) + '" height="16" rx="3" fill="' + (a[2] < 0 ? '#dc2626' : a[2] * 1e4 / (o.ownHrs || 1) < rv('min_wage') ? '#f59e0b' : '#16a34a') + '"/><text x="' + (a[2] >= 0 ? x + w + 4 : mid + 4) + '" y="' + (yy + 15) + '" font-size="11" font-weight="700" fill="currentColor">' + Math.round(a[2]).toLocaleString() + '만</text>'; }).join('');
    return '<div class="simc"><b>🎲 경우마다 사장 몫(세후)</b> <small>(빨강 손해 · 주황 최저시급 아래 · 초록 그 위)</small><svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="시나리오">' + g + '<line x1="' + mid + '" x2="' + mid + '" y1="0" y2="' + H + '" stroke="currentColor" stroke-opacity=".3"/></svg></div>'; }
  function simCharts(o, v, t) { return '<h4>🎚 시뮬레이션 그림</h4><p class="lg-n">' + schText(v) + '</p>' + svgWaterfall(o, v) + svgCurve(o, v) + svgScen(o, v); }
  // 개업 비용 — KREI 업종 평균 × 권역 비율(근사) + 공정위 브랜드 부담금
  var RGN = { '11': '서울권', '41': '수도권', '28': '수도권', '30': '충청권', '36': '충청권', '43': '충청권', '44': '충청권', '24': '호남권', '12': '호남권', '45': '호남권', '46': '호남권', '52': '호남권', '26': '경남권', '31': '경남권', '48': '경남권', '27': '경북권', '47': '경북권' };
  function openCost(o, v, t) { var R = t.krei, sc = PNL.c && RAD.gus && RAD.gus[0] && RAD.gus[0].gu ? String(RAD.gus[0].gu).slice(0, 2) : null, rg = sc && RGN[sc], f = 1, rgTxt = '전국 평균';
    if (rg && krAvg('invest', rg) && krAvg('invest', '전체')) { f = krAvg('invest', rg) / krAvg('invest', '전체'); rgTxt = rg + ' × ' + f.toFixed(2) + '(KREI 권역 투자비 ÷ 전국 — 근사)'; }
    var inv = krAvg('invest', R) || 0, inr = krAvg('interior', R) || 0, kit = krAvg('kitchen', R) || 0, br = brandOf(PNL.brand), al = br && br[9];
    var L = [['임차 보증금', +v.dep || 0, '① 칸 · KREI 표19'], ['권리금', +v.prem || 0, '① 칸'], ['인테리어', inr * f, 'KREI 표31-1 · ' + rgTxt], ['주방 설비', kit * f, 'KREI 표31-2 · ' + rgTxt], ['그 밖 설비(냉난방·간판·집기 등)', Math.max(0, inv - inr - kit) * f, 'KREI 표31 투자 − 인테리어 − 주방 · ' + rgTxt]];
    if (al) { if (al[3]) L.forEach(function (q, i) { if (i >= 2) { q[3] = 1; q[2] += ' — 브랜드 기타 부담금과 겹칠 수 있어 합계에 안 넣음(참고)'; } }); [['가맹비', al[0]], ['교육비', al[1]], ['가맹 보증금', al[2]], ['기타 부담금(인테리어·설비 등 본부가 정한 것)', al[3]]].forEach(function (q) { if (q[1]) L.push([q[0], q[1] / 10, '공정위 정보공개 ' + FTC.yr + ' · ' + esc(PNL.brand) + ' · 범위의 가운데']); }); }
    L.push(['초기 운영자금(고정비 3개월)', o.fixed * 3, '권고(일반론) — 처음 석 달 손님이 적어도 버틸 돈']);
    var tot = L.reduce(function (a, q) { return a + (q[3] ? 0 : q[1]); }, 0), Q = o.q, back = Q && Q.net > 0 ? tot / Q.net : null, mx = Math.max.apply(null, L.map(function (q) { return q[1]; })) || 1;
    var COL = ['#64748b', '#94a3b8', '#2563eb', '#0891b2', '#7c3aed', '#db2777', '#f59e0b', '#16a34a', '#ea580c', '#475569'];
    return '<h4>④ 개업 비용 — 처음에 드는 돈</h4><div class="simc"><svg viewBox="0 0 520 24" width="100%" role="img" aria-label="개업 비용 구성">' + (function () { var x = 0; return L.map(function (q, i) { var w = q[3] ? 0 : q[1] / tot * 520; var r = '<rect x="' + x + '" y="2" width="' + Math.max(0, w) + '" height="20" fill="' + COL[i % COL.length] + '"/>'; x += w; return r; }).join(''); })() + '</svg>' +
      '<table class="it"><tr><th>항목</th><th>만 원</th><th>근거</th></tr>' + L.map(function (q, i) { return '<tr' + (q[3] ? ' style="opacity:.5"' : '') + '><td><i style="display:inline-block;width:9px;height:9px;border-radius:2px;background:' + COL[i % COL.length] + ';margin-right:4px"></i>' + q[0] + '</td><td>' + Math.round(q[1]).toLocaleString() + '</td><td style="text-align:left;font-size:11px">' + q[2] + '</td></tr>'; }).join('') +
      '<tr><td><b>합계</b></td><td><b>' + Math.round(tot).toLocaleString() + '</b></td><td style="text-align:left">' + (back ? '세후 사장 몫으로 약 <b>' + Math.ceil(back) + '개월</b>에 돌려받는다' : '사장 몫이 0 이하라 돌려받지 못한다') + '</td></tr></table><p class="lg-n">보증금은 나갈 때 돌려받는 돈이다(회수 기간에는 넣었다). 권리금·인테리어는 나갈 때 못 받을 수 있다. 가맹 브랜드는 정보공개서 원문(가맹사업거래 franchise.ftc.go.kr)에서 인테리어 평당 비용·로열티·광고분담금을 꼭 확인한다.</p></div>'; }
  function brandBox() { var r = brandOf(PNL.brand); if (!r) return ''; var close = r[4] + r[5], rate = r[2] ? close / r[2] * 100 : null, Rg = r[10] || {}, ks = Object.keys(Rg).sort(function (a, b) { return Rg[b][0] - Rg[a][0]; });
    return '<h4>🏷 ' + esc(r[0]) + ' — 공정위 가맹정보 ' + esc(FTC.yr) + '</h4><div class="rcard">' + row('가맹점', r[2].toLocaleString() + '곳 · 한 해 새로 ' + r[3] + ' · 계약 종료 ' + r[4] + ' · 해지 ' + r[5] + (rate != null ? ' <em>(닫은 비율 ' + rate.toFixed(1) + '%)</em>' : '')) +
      (r[6] ? row('가맹점 연 평균매출', wn(r[6] / 10) + (r[7] ? ' · 3.3㎡(평)당 ' + wn(r[7] / 10) + ' → 평균 넓이 약 ' + (r[6] / r[7]).toFixed(1) + '평(' + (r[6] / r[7] * 3.305785).toFixed(0) + '㎡) <em>(평균매출 ÷ 평당매출 — 근사)</em>' : '')) : row('가맹점 평균매출', '공개 안 함')) +
      (r[8] ? row('주요 상품', esc(r[8])) : '') + (r[9] ? row('가맹점 부담금', ['가맹비', '교육비', '보증금', '기타'].map(function (q, i) { return r[9][i] ? q + ' ' + wn(r[9][i] / 10) : ''; }).filter(Boolean).join(' · ') + (r[9][4] ? ' · <b>합계 ' + wn(r[9][4] / 10) + '</b>' : '') + ' <em>(범위의 가운데)</em>') : '') +
      (ks.length ? row('지역별 평균매출', ks.slice(0, 6).map(function (k) { return esc(k) + ' ' + wn(Rg[k][1] / 10) + '(' + Rg[k][0] + '곳)'; }).join(' · ')) : '') + '</div><p class="src">' + esc(FTC.source) + ' · ' + esc(FTC.note) + '</p>'; }
  function pnlForm() {
    var el = $('m2dPnl'), t = tplOf(PNL.k), G = {};
    BZ.tpl.items.forEach(function (x) { (G[x.g] = G[x.g] || []).push(x); });
    var h = '<div class="lg-h"><b>💰 손익 계산</b><span><button data-px="min">▾ 접기</button> <button data-px="x">닫기</button></span></div>';
    h += '<div class="bizrow"><label>업종 <select data-pz="k">' + Object.keys(G).map(function (g) { return '<optgroup label="' + esc(g) + '">' + G[g].map(function (x) { return '<option value="' + x.k + '"' + (x.k === PNL.k ? ' selected' : '') + '>' + esc(x.n) + '</option>'; }).join('') + '</optgroup>'; }).join('') + '</select></label></div>';
    h += '<div class="lg-btns"><button data-px="here">📍 지금 화면 가운데를 자리로</button><button data-px="reset">↺ 업종 평균으로 되돌리기</button><button data-px="copy">📋 글로 복사</button><button data-px="xlsx">📥 엑셀(수식 그대로)</button></div>';
    if (t.pending) h += '<p class="pbig bad">⏳ ' + esc(t.pending) + '</p>';
    h += '<p class="lg-n">' + (t.tip ? '💡 ' + esc(t.tip) + ' ' : '') + '영업 종류: ' + esc(t.lic || '-') + '. 회색 글씨는 <b>업종 평균(KREI 2025 외식업체 경영실태조사)</b> 기본값 — 계약서·견적의 실제 숫자로 바꿔 쓴다.</p>';
    var FTCB = ftcList(PNL.k);
    if (FTCB) h += '<div class="bizrow"><label>브랜드 <select data-pz="brand"><option value="">— 브랜드 없이(업종 평균) —</option>' + FTCB.slice(0, 400).map(function (r) { return '<option value="' + esc(r[0]) + '"' + (PNL.brand === r[0] ? ' selected' : '') + '>' + esc(r[0]) + ' · ' + r[2].toLocaleString() + '곳</option>'; }).join('') + '</select></label><small class="lg-n">공정위 가맹정보 ' + esc(FTC.yr) + ' · 가맹점 많은 순 · 고르면 평균매출·면적·가맹비가 기본값으로</small></div>';
    else if (!FTC) { ftcLoad(); }
    h += simBox();
    function pfOne(f) { var val = PNL.v[f[0]];
      if (f[0] === 'area') return '<label title="' + esc(f[3]) + '"><span>면적 <i>㎡ ↔ 평</i></span><span class="pyw"><input type="number" inputmode="decimal" step="any" data-pf="area" value="' + (val == null ? '' : val) + '" aria-label="면적 ㎡"><b>㎡</b><input type="number" inputmode="decimal" step="any" data-py="1" value="' + (val == null ? '' : Math.round(val / 3.305785 * 10) / 10) + '" aria-label="면적 평"><b>평</b></span><small>' + esc(PSRC.area || '') + ' · 1평 = 3.3058㎡</small></label>';   // v2.35.0 소유자 「평방미터·평을 바꿔 가며 볼 수 있게」
      return '<label title="' + esc(f[3]) + '"><span>' + esc(f[1]) + ' <i>' + esc(f[2]) + '</i></span><input type="number" inputmode="decimal" step="any" data-pf="' + f[0] + '" value="' + (val == null ? '' : val) + '"><small>' + esc(PSRC[f[0]] || '') + '</small></label>'; }
    h += '<details open><summary><b>① 내 가게 조건</b> <small>(숫자를 바꾸면 바로 다시 계산)</small></summary><div class="pform">' + PF.filter(function (f) { return !f[4]; }).map(pfOne).join('') + '</div>';
    h += '<details open><summary><b>⏰ 사장 하루 일정</b> <small>(여는·닫는 시각 · 브레이크 · 휴무 → 영업시간·영업일·사장 시간이 따라 바뀐다)</small></summary><div class="pform">' + PF.filter(function (f) { return f[4] === 'sch'; }).map(pfOne).join('') + '</div><p class="lg-n" id="pnlSch"></p></details>';
    var R0 = tplOf(PNL.k).krei, ko = krAvg('other', R0);
    h += '<details><summary><b>🧾 세부 비용 — 고지서·견적 숫자로</b> <small>(전기·통신·청소·보험·기장·소모품·광고·수선·세금과공과)</small></summary><label class="pchk"><input type="checkbox" data-pt="useItem"' + (PNL.v.useItem ? ' checked' : '') + '> 이 세부 비용을 「기타 비용률」 대신 쓴다</label><p class="lg-n">업종 평균 기타비용 = 월 약 <b>' + wn(ko ? ko / 12 : null) + '</b>(KREI 표103 — 전기·통신·소모품 등을 다 합친 값 · 항목별 평균은 공개 통계에 없다). 아래 칸은 0 으로 두었다 — 고지서·견적 숫자를 넣는다.</p><div class="pform">' + PF.filter(function (f) { return f[4] === 'cost'; }).map(pfOne).join('') + '</div></details>';
    h += '<details><summary>❓ 칸마다 뜻</summary><ul class="pexp">' + PF.map(function (f) { return '<li><b>' + esc(f[1]) + '</b> — ' + esc(f[3]) + '</li>'; }).join('') + '</ul></details></details>';
    h += '<div id="pnlOut"></div>';
    el.innerHTML = h; pnlOut(); simLab();
  }
  function band(o, extra) {
    var pts = [['손익분기', o.bep, '#dc2626'], ['사장 최저시급', o.mwLine, '#f59e0b'], ['내 예상', o.salesQ, '#111827'], ['물리 상한', o.cap, '#64748b']].concat(extra || []).filter(function (p) { return p[1] != null && isFinite(p[1]) && p[1] > 0; });
    if (!pts.length || !o.bep) return ''; var mx = Math.max.apply(null, pts.map(function (p) { return p[1]; })) * 1.12;
    return '<div class="pband"><div class="pbar"><i style="left:0;width:' + (o.bep / mx * 100) + '%;background:rgba(220,38,38,.18)"></i>' + (o.mwLine ? '<i style="left:' + (o.bep / mx * 100) + '%;width:' + ((o.mwLine - o.bep) / mx * 100) + '%;background:rgba(245,158,11,.18)"></i>' : '') + '<i style="left:' + ((o.mwLine || o.bep) / mx * 100) + '%;right:0;background:rgba(22,163,74,.14)"></i>' +
      pts.map(function (p) { return '<b style="left:' + (p[1] / mx * 100) + '%;background:' + p[2] + '"></b>'; }).join('') + '</div><div class="pleg">' + pts.map(function (p) { return '<span><i style="background:' + p[2] + '"></i>' + esc(p[0]) + ' ' + wn(p[1]) + '</span>'; }).join('') + '</div>' +
      '<small>빨강 = 고정비도 못 덮음 · 주황 = 고정비는 덮지만 사장 몫이 최저시급 아래 · 초록 = 사장이 최저시급 이상 가져감 (월 매출, 공급가)</small></div>';
  }
  function pnlOut() {
    var el = $('pnlOut'); if (!el || !BZ.tpl) return; var v = PNL.v, t = tplOf(PNL.k), o = pnlCalc(v), R = t.krei, h = '', mw = rv('min_wage');
    PNL.calc = o;
    h += '<h4>② 결과 — 한 달</h4>';
    var Q = o.q;
    if (Q) h += '<div class="pbig ' + (Q.profit < 0 ? 'bad' : Q.hourly < mw ? 'mid' : 'good') + '">하루 손님 <b>' + v.cust + '명</b>이면 월 매출 <b>' + wn(o.salesQ) + '</b> → 사장 몫 <b>' + wn(Q.profit) + '</b>' + (Q.hourly != null ? ' · 사장 시급 환산 <b>' + Math.round(Q.hourly).toLocaleString() + '원</b> (최저시급의 ' + Math.round(Q.hourly / mw * 100) + '%)' : '') + '</div>';
    h += '<div class="rcard">' + row('손익분기 매출', wn(o.bep) + (o.bepCust ? ' · 하루 손님 <b>' + Math.ceil(o.bepCust) + '명</b>' : '')) + row('사장 최저시급 선', wn(o.mwLine) + (o.mwCust ? ' · 하루 손님 <b>' + Math.ceil(o.mwCust) + '명</b>' : '') + ' <em>(사장 ' + v.own + '명 × 하루 ' + v.ownH + '시간 × ' + v.days + '일을 최저시급으로 쳐서 더한 매출)</em>') +
      row('물리 상한', o.cap ? wn(o.cap) + ' <em>(좌석 ' + v.seats + ' × 회전 ' + v.turns + ' × 객단가 × 영업일' + (v.dlv > 0 || v.to > 0 ? ' ÷ 홀 매출 비중 ' + Math.round(100 - (+v.dlv || 0) - (+v.to || 0)) + '%' : '') + ')</em>' : '-') +
      (o.salesQ && o.cap && o.salesQ > o.cap ? '<p class="lg-n" style="color:#b91c1c">⚠ 내 예상 매출이 물리 상한을 넘는다 — 손님 수나 회전 가정이 맞는지 다시 본다.</p>' : '') + '</div>';
    h += band(o);
    if (Q) h += row2('사장 몫(세후 어림)', '<b>' + wn(Q.net) + '</b> · 시급 ' + (Q.netHourly != null ? Math.round(Q.netHourly).toLocaleString() + '원' : '-') + ' <em>(− 국민연금 ' + wn(Q.tax.pen) + ' · 건강·요양 ' + wn(Q.tax.hea) + ' · 종합소득세 ' + wn(Q.tax.it) + ' · 지방소득세 ' + wn(Q.tax.loc) + ' — 사장 몫만 소득으로 본 어림 · 다른 소득·공제·세액공제는 안 봤다)</em>');
    h += simCharts(o, v, t);
    h += openCost(o, v, t);
    h += brandBox();
    h += '<details><summary>🧮 비용 내역과 공식(펼치기)</summary><div class="rcard">' + row('환산 임대료', wn(o.convRent) + ' <em>= 월세 + 보증금 × ' + v.conv + '% ÷ 12</em>') + row('관리비', wn(+v.mgmt || 0)) + row('투자·권리금 상각', wn(o.amort) + ' <em>= (권리금 + 투자) ÷ ' + v.mon + '개월</em>') +
      row('직원 인건비', wn(o.staff) + ' <em>= ' + v.staffN + '명 × (월 ' + Math.round(o.staffHrs) + '시간(주휴 포함) × ' + (+v.wage).toLocaleString() + '원) × (1 + 사업주 4대보험 ' + (o.er * 100).toFixed(2) + '%' + (v.staffH >= 15 ? ' + 퇴직적립 8.33%' : '') + ')</em>') +
      (v.useItem ? row('세부 비용', wn(o.items) + ' <em>(🧾 칸의 합 — 기타 비용률 대신)</em>') : '') + row('고정비 합', '<b>' + wn(o.fixed) + '</b>') + row('매출에 비례하는 비용', (o.varRate * 100).toFixed(1) + '% <em>= 재료 ' + v.food + '% + 기타 ' + v.other + '% + 카드 ' + (o.card * 100).toFixed(2) + '%×1.1 + 배달 ' + v.dlv + '%×' + v.dlvfee + '%' + (o.yu ? ' + 개별소비세·교육세 ' + (o.yu * 100).toFixed(0) + '%' : '') + '</em>') +
      row('손익분기 공식', '<em>고정비 ÷ (1 − 비례 비용률) = ' + wn(o.fixed) + ' ÷ ' + o.cm.toFixed(3) + '</em>') + row('카드 수수료', (o.card * 100).toFixed(2) + '% <em>(예상 연매출로 고른 우대수수료 — ' + esc(BZ.rates.card_note) + ')</em>') +
      row('5인 규칙', o.five ? '<b style="color:#b91c1c">직원 5인 이상 — 연장·야간·휴일 가산 50%를 따로 더해야 한다(이 계산에 없음)</b>' : '직원 5인 미만 — 연장·야간·휴일 가산수당 없음(사장은 인원에 안 넣는다)') + '</div></details>';
    if (o.bep) { var base = v.cust || o.mwCust || o.bepCust, rows = [0.6, 0.8, 1, 1.2, 1.5].map(function (m) { var c2 = Math.round(base * m), s = c2 * v.price * v.days / 1e4, a = o.at(s); return [c2, a]; });
      h += '<details><summary>📊 손님 수가 바뀌면(민감도)</summary><table class="it"><tr><th>하루 손님</th><th>월 매출</th><th>사장 몫</th><th>사장 시급</th><th>임대료/매출</th></tr>' + rows.map(function (r) { var a = r[1]; return '<tr' + (a.profit < 0 ? ' class="bar"' : '') + '><td>' + r[0] + '명</td><td>' + wn(a.sales) + '</td><td>' + wn(a.profit) + '</td><td>' + (a.hourly != null ? Math.round(a.hourly).toLocaleString() + '원' : '-') + '</td><td>' + (a.rentPct != null ? a.rentPct.toFixed(1) + '%' : '-') + '</td></tr>'; }).join('') + '</table></details>'; }
    h += '<h4>③ 이 자리 — 공공 자료</h4>';
    if (!PNL.c) h += '<p class="lg-n">자리를 고르지 않았다 — 「📍 지금 화면 가운데를 자리로」를 누르거나 지도 카드의 「💰 여기서 손익」으로 연다.</p>';
    else if (PNL.wait || !PNL.res) h += '<p class="lg-n">반경 500m 자료를 모으는 중…</p>';
    else h += pnlPlace(o);
    h += pnlBench();
    h += '<p class="src">계산: 이 지도 — 공식은 위 「비용 내역」에 다 펼쳐 있다. 요율: ' + esc(BZ.rates.year + '년 고시(biz-rates.json)') + ' · 업종 평균: ' + esc(BZ.krei.source) + ' · ' + esc(BZ.bench.source) + ' · 경비율: 국세청 고시 제2025-6호. 매출은 공급가(부가세 뺀 값). 사장 몫에서 사장 본인 4대보험(지역 건보·연금)·종합소득세는 빼지 않았다.</p>';
    el.innerHTML = h;
  }
  function jgAround(c, r) { var o = { pop: 0, hh: 0, wrk: 0, corp: 0, cells: [] }; JGGA.forEach(function (x) { var d = dTrue(x.c, c); if (d > r) return; var t = x.t; o.pop += t[4] || 0; o.hh += t[5] || 0; o.corp += t[8] || 0; o.wrk += t[9] || 0; o.cells.push({ p: x.c, hh: t[5] || 0, pop: t[4] || 0 }); }); return o; }
  function govAround(c, r) { var L = SAFE.filter(function (x) { return x[0] === 'govr'; })[0], o = { n: 0, c: {} }; if (!L) return o; L[3].forEach(function (q) { if (dTrue(q.p, c) > r) return; o.n++; o.c[q.r[3]] = (o.c[q.r[3]] || 0) + 1; }); return o; }
  function compAround(t, c, r) { var CL = SIDX ? SIDX.cls : [], L = []; if (!(t.small || t.mid) || !(t.small || []).length && !(t.mid || []).length) return null;
    Object.keys(SPTS).forEach(function (gu) { var S2 = SPTS[gu]; if (!S2 || !S2.a) return; S2.a.forEach(function (st) { var C3 = CL[st.c]; if (!C3) return; if ((t.small || []).indexOf(C3[5]) < 0 && (t.mid || []).indexOf(C3[2]) < 0) return; var d = dTrue(st.p, c); if (d <= r) L.push({ p: st.p, d: d, s: st }); }); });
    return L.sort(function (a, b) { return a.d - b.d; }); }
  function pnlPlace(o) {
    var c = PNL.c, t = tplOf(PNL.k), R = PNL.res, v = PNL.v, h = '<div class="rcard">', sd = sidoOf((RAD.gus && RAD.gus[0] && RAD.gus[0].gu) || '11');
    var comp = compAround(t, c, 500), comp1 = compAround(t, c, 1000);
    h += row('같은 업종 점포', comp ? '반경 500m <b>' + comp.length + '곳</b> · 1km ' + comp1.length + '곳' + (comp.length ? ' · 가장 가까운 곳 ' + Math.round(comp[0].d) + 'm' : '') + ' <em>(소상공인 상가정보 ' + esc(R.ym || '') + ')</em>' : '<em>이 업종을 셀 상가 분류가 없다</em>');
    var B = t.seoul && R.bi && R.bi[t.seoul];
    if (B && B.st >= 0.5) { var ps = B.amt / B.st, pc = ps * 1e4 / (v.price || 1) / (v.days || 1);
      h += row('이 자리 같은 업종 점포당 매출', '월 약 <b>' + wn(ps) + '</b> · 하루 손님 약 ' + Math.round(pc) + '명 상당 <em>(서울시 상권분석 카드 추정 · 반경에 걸친 상권 평균 · 현금 제외)</em>');
      PNL.seoulPS = ps; } else PNL.seoulPS = null;
    if (R.rent) { var my = v.area ? v.rent * 10 / v.area : null, sm = lastV(R.rent.it.s);
      h += row('임대료 비교', '부동산원 표본(' + esc(R.rent.it.name) + ' · ' + R.rent.d + 'm) 소규모 상가 ' + (sm != null ? '㎡당 <b>' + sm + '천 원</b>(평당 ' + (sm * 3.305785).toFixed(1) + '천 원)' : '<em>최근 분기 값 없음</em>') + (my ? ' · 내 월세 ㎡당 <b>' + my.toFixed(1) + '천 원</b>(평당 ' + (my * 3.305785).toFixed(1) + '천 원)' + (sm && my > sm * 1.3 ? ' <em>— 표본보다 30% 넘게 비싸다</em>' : sm && my < sm * 0.7 ? ' <em>— 표본보다 싸다(자리·층·면적 차이일 수 있다)</em>' : '') : '')); }
    var J = jgAround(c, 500), G = govAround(c, 500);
    if (J.pop || J.wrk) h += row('배후(반경 500m)', '주민 ' + Math.round(J.pop).toLocaleString() + '명 · 가구 ' + Math.round(J.hh).toLocaleString() + ' · 사업체 ' + Math.round(J.corp).toLocaleString() + '곳 · 종사자 ' + Math.round(J.wrk).toLocaleString() + '명 <em>(SGIS 집계구 2023)</em>');
    if (comp && J.cells.length && J.hh) { var lam = 2, my2 = 0;
      J.cells.forEach(function (q) { var d0 = Math.max(30, dTrue(q.p, c)), a0 = 1 / Math.pow(d0, lam), s = a0; comp1.forEach(function (x) { s += 1 / Math.pow(Math.max(30, dTrue(q.p, x.p)), lam); }); my2 += q.hh * a0 / s; });
      h += row('Huff 몫', '반경 500m 가구 ' + Math.round(J.hh).toLocaleString() + ' 중 약 <b>' + Math.round(my2).toLocaleString() + '가구</b>(' + (my2 / J.hh * 100).toFixed(1) + '%)가 이 가게 쪽으로 기운다 <em>(거리만으로 나눈 몫 · 같은 업종 1km 안 ' + comp1.length + '곳과 경쟁 · 크기·맛·값은 같다고 봄 · λ=' + lam + ')</em>'); }
    h += '</div>';
    h += band(PNL.calc, PNL.seoulPS ? [['이 자리 점포당(카드)', PNL.seoulPS, '#2563eb']] : []);
    var S = { sido: sd, pop: J.pop || R.pop, wrk: J.wrk || null, corp: J.corp, gov: G, age: R.age, live: null, tb: R.tb, ag: R.ag };
    if (R.live && R.live.some(function (x) { return x; })) S.live = R.we ? null : { wd: R.live };
    var bw = R.bi && t.seoul && R.bi[t.seoul]; if (bw && bw.amt) S.dw = null;
    h += talk(S);
    return h;
  }
  function pnlBench() {
    var t = tplOf(PNL.k), R = t.krei, h = '<h4>④ 이 업종 평균 — 알아 두기</h4><div class="rcard">', f = function (x, d) { return x == null ? '-' : (+x).toLocaleString(undefined, { maximumFractionDigits: d == null ? 1 : d }); };
    var ns = kr('price', R); h += row('조사 표본', ns ? ns[0] + '곳 <em>(KREI 2025 · 전국)</em>' + (ns[0] < 60 ? ' <b style="color:#b45309">표본이 작아 평균이 흔들린다</b>' : '') : '-');
    var sal = krAvg('sales', R), pf = krAvg('profit', R), ow = krAvg('owner', R);
    h += row('연 매출 · 영업이익', f(sal, 0) + '만 원 · ' + f(pf, 0) + '만 원(' + (sal ? (pf / sal * 100).toFixed(1) : '-') + '%) <em>(KREI 표95·104)</em>') + row('대표자 인건비(연)', f(ow, 0) + '만 원 — 영업이익과 별도로 사장이 가져간 몫 <em>(표102)</em>');
    h += row('국세청이 보는 소득률', (100 - t.nts[2]).toFixed(1) + '% <em>(단순경비율 ' + t.nts[2] + '% · 업종코드 ' + t.nts[0] + ' ' + esc(t.nts[1]) + ' · 소규모 사업자 추계 기준)</em>');
    var hd = kr('holiday', R), dd = kr('days', R), hr = kr('hours', R);
    h += row('일하는 시간', '하루 영업 ' + f(krAvg('hours', R)) + '시간(12시간 넘는 곳 ' + (hr ? hr[3] : '-') + '%) · 한 달 ' + f(krAvg('days', R)) + '일 · <b>정기 휴일 없음 ' + (hd ? hd[4] : '-') + '%</b> <em>(표24·25·26)</em>');
    var ag = kr('cust_age', R), ch = kr('channel', R), dw = kr('dow', R);
    if (ag) { var AG = ['20대 미만', '20대', '30대', '40대', '50대', '60대', '70대 이상'], mx = 1; for (var i = 2; i < 8; i++) if (ag[i] > ag[mx]) mx = i; h += row('주 손님', AG[mx - 1] + ' ' + ag[mx] + '% <em>(표63 · 중복응답)</em>'); }
    if (ch) h += row('판매 방식', '홀 ' + ch[1] + '% · 배달 ' + ch[2] + '% · 포장 ' + ch[3] + '% <em>(표58)</em>');
    if (dw) h += row('요일', '평일(월~목) ' + dw[1] + '% · 금~일 ' + dw[2] + '% <em>(표66)</em>');
    var wk = kr('workers', R); if (wk) h += row('일하는 사람', '평균 ' + f(wk[wk.length - 1], 2) + '명(대표 포함 상용 ' + wk[1] + ' · 임시 ' + wk[2] + ' · 일용 ' + wk[3] + ' · 무급 가족 ' + wk[7] + ') <em>(표115)</em>');
    h += row('개업 투자 · 권리금', f(krAvg('invest', R), 0) + '만 원(인테리어 ' + f(krAvg('interior', R), 0) + ') · 권리금 낸 곳 평균 ' + f(krAvg('premium', R), 0) + '만 원 <em>(표31·32·22)</em>');
    var B = BZ.bench, sdn = { '서울': '서울특별시', '경기': '경기도' }[PNL.c && RAD.gus && RAD.gus[0] ? sidoOf(RAD.gus[0].gu) : ''] || '전국', pick = function (tbl) { var x = (B.sido[sdn] || {})['숙박 및 음식점업']; return x && x[tbl] ? [x[tbl], sdn + ' 숙박·음식점업'] : [(B.sido['전국'] || {})['음식점 및 주점업'] && B.sido['전국']['음식점 및 주점업'][tbl], '전국 음식점·주점업']; };
    var pn = pick('pain'); if (pn[0]) { var top = Object.keys(pn[0]).filter(function (k) { return k !== '기업체 수'; }).sort(function (a, b) { return pn[0][b][0] - pn[0][a][0]; }).slice(0, 4); h += row('사장들이 꼽은 어려움', top.map(function (k) { return esc(k) + ' ' + pn[0][k][0] + '%'; }).join(' · ') + ' <em>(소상공인실태조사 ' + pn[0][top[0]][1] + ' · ' + pn[1] + ' · 복수응답)</em>'); }
    var pl = pick('plan'); if (pl[0] && pl[0]['계속운영']) { h += row('앞으로 계획', ['계속운영', '사업전환', '폐업 및 은퇴', '폐업 후 임금근로자 희망'].filter(function (k) { return pl[0][k]; }).map(function (k) { return esc(k) + ' ' + pl[0][k][0] + '%'; }).join(' · ') + ' <em>(' + pl[1] + ')</em>'); }
    var pr = pick('prep'); if (pr[0] && pr[0]['평균']) h += row('창업 준비 기간', '평균 ' + pr[0]['평균'][0] + '개월 · 3개월 미만 ' + ((pr[0]['3개월 미만'] || [0])[0]) + '% <em>(' + pr[1] + ')</em>');
    var sv = B.surv && B.surv['숙박 및 음식점업']; if (sv) h += row('살아남는 비율', '1년 ' + sv['1년 생존율'] + '% · 3년 ' + sv['3년 생존율'] + '% · <b>5년 ' + sv['5년 생존율'] + '%</b> <em>(통계청 기업생멸행정통계 · 숙박·음식점업 신생기업 · 전 산업 5년 ' + (B.surv['전체'] || {})['5년 생존율'] + '%)</em>');
    h += '</div><details open><summary><b>🧭 오래가는 가게가 계약 전에 하는 일</b> <small>(숫자는 위 통계 · 순서는 일반론)</small></summary><ol class="pexp">' +
      '<li><b>손익분기 손님 수를 현장에서 세 본다</b> — 위 「하루 손님 ' + (PNL.calc && PNL.calc.bepCust ? Math.ceil(PNL.calc.bepCust) + '명' : 'N명') + '」을 같은 시간대 근처 같은 업종 가게 앞에서 평일·주말 하루씩 직접 센다. 이 지도의 카드 추정은 현금·배달을 빼서 실제보다 작거나 다를 수 있다.</li>' +
      '<li><b>사장 시간도 비용으로 친다</b> — 이 업종 평균 영업 ' + f(krAvg('hours', R)) + '시간·월 ' + f(krAvg('days', R)) + '일. 사장 시급이 최저시급 아래면 남의 가게에서 일하는 것보다 못하다.</li>' +
      '<li><b>임대료는 매출의 몇 %인가</b> — 민감도 표의 「임대료/매출」. 같은 업종 평균은 KREI 표99÷95 = ' + (krAvg('sales', R) ? (krAvg('rentcost', R) / krAvg('sales', R) * 100).toFixed(1) : '-') + '%. 이보다 높으면 손님이 평균보다 많아야 버틴다.</li>' +
      '<li><b>경쟁과 배후를 같이 본다</b> — 같은 업종 점포 수와 Huff 몫, 그리고 「🗣 이 자리 읽기」의 일터형·주거형. 일터형에 저녁 장사 업종, 주거형에 점심 업종은 시간대가 엇갈린다.</li>' +
      '<li><b>준비 기간을 충분히</b> — 실태조사 평균 준비 기간과 5년 생존율(숙박·음식점업 ' + (sv ? sv['5년 생존율'] + '%' : '-') + ')을 같이 본다. 3개월 미만으로 서둘러 연 곳이 적지 않다.</li>' +
      '<li><b>권리금·투자는 몇 달에 갚나</b> — 회수 기간을 생존율보다 짧게 잡는다. 권리금은 나갈 때 못 받을 수 있다고 보고 계산했다.</li>' +
      '<li><b>허가·용도를 먼저 확인</b> — 영업 종류(' + esc(t.lic || '-') + ')에 맞는 건물 용도·면적·시설 기준인지 구청 위생과·건축과에 계약 전에 묻는다' + (t.yuheung ? ' — 유흥주점은 특히 허가 제한이 많다' : '') + '.</li>' +
      '<li><b>성실함은 기본</b> — 위 숫자는 평균이다. 같은 자리·같은 업종에서도 맛·친절·위생·꾸준함이 매출 차이를 만든다(통계로는 잴 수 없는 부분).</li></ol></details>';
    return h;
  }
  function pnlText() { var v = PNL.v, o = PNL.calc, t = tplOf(PNL.k); if (!o) return '';
    return ['[손익 계산] ' + t.n + (PNL.c ? ' · 위도 ' + (LAT0 - PNL.c[1] / KY).toFixed(5) + ', 경도 ' + (PNL.c[0] / KX + LON0).toFixed(5) : ''),
      '조건: 보증금 ' + v.dep + '만 · 월세 ' + v.rent + '만 · 관리비 ' + v.mgmt + '만 · 권리금 ' + v.prem + '만 · 투자 ' + v.inv + '만(' + v.mon + '개월) · ' + v.area + '㎡ · 좌석 ' + v.seats + ' · 영업 ' + v.hours + '시간×' + v.days + '일 · 객단가 ' + v.price + '원 · 직원 ' + v.staffN + '명×주 ' + v.staffH + '시간',
      '고정비 ' + wn(o.fixed) + '/월 · 매출 비례 비용 ' + (o.varRate * 100).toFixed(1) + '%',
      '손익분기 ' + wn(o.bep) + '(하루 손님 ' + (o.bepCust ? Math.ceil(o.bepCust) : '-') + '명) · 사장 최저시급 선 ' + wn(o.mwLine) + '(하루 ' + (o.mwCust ? Math.ceil(o.mwCust) : '-') + '명) · 물리 상한 ' + wn(o.cap),
      o.q ? '하루 손님 ' + v.cust + '명이면 월 매출 ' + wn(o.salesQ) + ' → 사장 몫 ' + wn(o.q.profit) + ' · 사장 시급 ' + (o.q.hourly != null ? Math.round(o.q.hourly).toLocaleString() + '원' : '-') : '',
      '출처: 요율 ' + BZ.rates.year + '년 고시 · 업종 평균 KREI 2025 외식업체 경영실태조사 · 소상공인실태조사 · 국세청 경비율 — 데이터 압축지도 계산(추정)'].filter(Boolean).join('\n'); }
  // ---------- 📥 엑셀 — 같은 공식을 수식째(엔진 하나 · 출구 둘) · 압축 없는 zip 을 직접 만든다(빌드 도구·외부 라이브러리 없음) ----------
  function crc32(u8) { var c, t = crc32.t; if (!t) { t = crc32.t = []; for (var n = 0; n < 256; n++) { c = n; for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } }
    c = 0xFFFFFFFF; for (var i = 0; i < u8.length; i++) c = t[(c ^ u8[i]) & 0xFF] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
  function zipStore(files) { var enc = new TextEncoder(), parts = [], cen = [], off = 0;
    function u16(n) { return [n & 255, (n >>> 8) & 255]; } function u32(n) { return [n & 255, (n >>> 8) & 255, (n >>> 16) & 255, (n >>> 24) & 255]; }
    files.forEach(function (f) { var nm = enc.encode(f[0]), dt = enc.encode(f[1]), cr = crc32(dt);
      var lh = [].concat(u32(0x04034b50), u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(cr), u32(dt.length), u32(dt.length), u16(nm.length), u16(0));
      parts.push(new Uint8Array(lh), nm, dt);
      cen.push([].concat(u32(0x02014b50), u16(20), u16(20), u16(0x0800), u16(0), u16(0), u16(0x21), u32(cr), u32(dt.length), u32(dt.length), u16(nm.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(off)), nm);
      off += lh.length + nm.length + dt.length; });
    var cs = 0; cen.forEach(function (x, i) { if (i % 2 === 0) { parts.push(new Uint8Array(x)); cs += x.length; } else { parts.push(x); cs += x.length; } });
    parts.push(new Uint8Array([].concat(u32(0x06054b50), u16(0), u16(0), u16(files.length), u16(files.length), u32(cs), u32(off), u16(0)))); return new Blob(parts, { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }); }
  function xe(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function sheetXml(rows) { return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><cols><col min="1" max="1" width="30" customWidth="1"/><col min="2" max="2" width="18" customWidth="1"/><col min="3" max="3" width="70" customWidth="1"/></cols><sheetData>' +
    rows.map(function (r, i) { return '<row r="' + (i + 1) + '">' + r.map(function (c, j) { var ref = String.fromCharCode(65 + j) + (i + 1); if (c == null || c === '') return ''; if (typeof c === 'number') return '<c r="' + ref + '"><v>' + c + '</v></c>'; if (c.charAt(0) === '=') return '<c r="' + ref + '"><f>' + xe(c.slice(1)) + '</f></c>'; return '<c r="' + ref + '" t="inlineStr"><is><t xml:space="preserve">' + xe(c) + '</t></is></c>'; }).join('') + '</row>'; }).join('') + '</sheetData></worksheet>'; }
  function pnlXlsx() {
    var v = PNL.v, t = tplOf(PNL.k), o = PNL.calc, A = {}, rows = [['손익 계산 — ' + t.n, '', '노란 칸(B열 숫자)만 바꾸면 아래 수식이 다시 계산된다. 데이터 압축지도에서 내보냄 ' + new Date().toISOString().slice(0, 10)], ['항목', '값', '설명·근거']];
    PF.forEach(function (f) { rows.push([f[1] + ' (' + f[2] + ')', v[f[0]] == null ? 0 : +v[f[0]], f[3] + (PSRC[f[0]] ? ' [기본값: ' + PSRC[f[0]] + ']' : '')]); A[f[0]] = 'B' + rows.length; });
    rows.push(['', '', '']); rows.push(['요율(' + BZ.rates.year + ')', '', '']);
    [['min_wage', '최저시급(원)'], ['pension', '국민연금 사업주'], ['health', '건강보험 사업주'], ['ltc_of_health', '장기요양(건보료 대비)'], ['emp_ui', '고용보험 실업 사업주'], ['emp_stable', '고용안정·직능'], ['ind', '산재(음식·숙박)'], ['commute', '출퇴근재해']].forEach(function (x) { rows.push([x[1], rv(x[0]), BZ.rates[x[0]][1]]); A[x[0]] = 'B' + rows.length; });
    rows.push(['카드수수료(적용)', o.card, '예상 연매출로 고른 우대수수료']); A.card = 'B' + rows.length;
    rows.push(['개별소비세+교육세', o.yu, o.yu ? '유흥주점 — 2차 출처 · 원문 미대조' : '해당 없음']); A.yu = 'B' + rows.length;
    rows.push(['', '', '']); rows.push(['계산', '', '']);
    var F = function (lbl, f, d) { rows.push([lbl, '=' + f, d]); return 'B' + rows.length; };
    A.er = F('사업주 보험 합', A.pension + '+' + A.health + '*(1+' + A.ltc_of_health + ')+' + A.emp_ui + '+' + A.emp_stable + '+' + A.ind + '+' + A.commute, '연금+건강×(1+장기요양)+고용+고용안정+산재+출퇴근');
    A.conv = F('환산 임대료(만 원)', A.rent + '+' + A.dep + '*' + A.conv + '/100/12', '월세 + 보증금×기회비용률÷12');
    A.am = F('투자·권리금 상각(만 원)', '(' + A.prem + '+' + A.inv + ')/MAX(1,' + A.mon + ')', '');
    A.sh = F('직원 1명 월 시간', A.staffH + '*52/12+IF(' + A.staffH + '>=15,' + A.staffH + '/40*8*52/12,0)', '주휴 포함');
    A.st = F('직원 인건비(만 원)', A.staffN + '*' + A.sh + '*' + A.wage + '/10000*(1+' + A.er + '+IF(' + A.staffH + '>=15,1/12,0))', '× (1 + 사업주 보험 + 퇴직적립)');
    A.fx = F('고정비(만 원)', A.conv + '+' + A.mgmt + '+' + A.am + '+' + A.st, '');
    A.vr = F('매출 비례 비용률', A.food + '/100+' + A.other + '/100+' + A.card + '*1.1+' + A.dlv + '/100*' + A.dlvfee + '/100+' + A.yu, '재료+기타+카드×1.1+배달+개소세');
    A.bep = F('손익분기 월매출(만 원)', 'IF(1-' + A.vr + '<=0,NA(),' + A.fx + '/(1-' + A.vr + '))', '고정비 ÷ (1 − 비례 비용률)');
    F('손익분기 하루 손님', A.bep + '*10000/(' + A.price + '*' + A.days + ')', '');
    A.mw = F('사장 최저시급 선 월매출(만 원)', '(' + A.fx + '+' + A.min_wage + '*' + A.own + '*' + A.ownH + '*' + A.days + '/10000)/(1-' + A.vr + ')', '');
    F('사장 최저시급 선 하루 손님', A.mw + '*10000/(' + A.price + '*' + A.days + ')', '');
    A.sq = F('내 예상 월매출(만 원)', A.price + '*' + A.cust + '*' + A.days + '/10000', '객단가×하루 손님×영업일');
    A.pr = F('사장 몫(만 원)', A.sq + '*(1-' + A.vr + ')-' + A.fx, '사장 본인 4대보험·종소세 전');
    F('사장 시급(원)', 'IF((' + A.own + '+' + A.fam + ')*' + A.ownH + '*' + A.days + '=0,NA(),' + A.pr + '*10000/((' + A.own + '+' + A.fam + ')*' + A.ownH + '*' + A.days + '))', '사장+무급 가족 시간으로 나눔');
    F('임대료/매출', 'IF(' + A.sq + '=0,NA(),' + A.conv + '/' + A.sq + ')', '');
    F('물리 상한 월매출(만 원)', A.seats + '*' + A.turns + '*' + A.price + '*' + A.days + '/10000', '좌석×회전×객단가×영업일(홀만)');
    rows.push(['', '', '']); rows.push(['출처', '', BZ.krei.source + ' · ' + BZ.bench.source + ' · 국세청 고시 제2025-6호 · ' + BZ.rates.card_note]);
    var bench = [['KREI 업종 평균 — ' + t.krei, '', '표 번호는 보고서 그대로'], ['항목', '평균', '표']];
    [['price', '객단가(원)'], ['sales', '연 매출(만 원)'], ['food', '식재료비(만 원/년)'], ['wage', '고용인 인건비(만 원/년)'], ['rentcost', '임차료(만 원/년)'], ['owner', '대표자 인건비(만 원/년)'], ['profit', '영업이익(만 원/년)'], ['rent', '월세(만 원)'], ['deposit', '보증금(만 원)'], ['premium', '권리금(만 원)'], ['invest', '개업 투자(만 원)'], ['hours', '영업시간'], ['days', '영업일'], ['seats', '좌석'], ['area', '면적(㎡)'], ['cust', '하루 방문 고객']].forEach(function (x) { var T = BZ.krei.tables[x[0]]; bench.push([x[1], krAvg(x[0], t.krei), '표' + (T ? T.no : '')]); });
    var wb = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="손익" sheetId="1" r:id="rId1"/><sheet name="업종평균" sheetId="2" r:id="rId2"/></sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>';
    var files = [['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'],
      ['xl/workbook.xml', wb], ['xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'],
      ['xl/worksheets/sheet1.xml', sheetXml(rows)], ['xl/worksheets/sheet2.xml', sheetXml(bench)], ['xl/styles.xml', '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="1"><font><sz val="11"/><name val="맑은 고딕"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>']];
    var b = zipStore(files), a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = '손익계산_' + t.n.replace(/[^\w가-힣]+/g, '_') + '_' + new Date().toISOString().slice(0, 10) + '.xlsx'; document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 2000);
  }
  if ($('m2dPnl')) {
    $('m2dPnl').addEventListener('click', function (e) { var b = e.target.closest('[data-px]'); if (!b) { if ($('m2dPnl').classList.contains('min') && !e.target.closest('input,select,summary')) $('m2dPnl').classList.remove('min'); return; } var x = b.getAttribute('data-px');
      if (x === 'x') { $('m2dPnl').classList.remove('on'); document.body.classList.remove('pnlon'); draw(); return; } if (x === 'min') { e.stopPropagation(); $('m2dPnl').classList.toggle('min'); return; }
      if (x === 'here') { PNL.c = viewMid(); pnlGather(); return; } if (x === 'reset') { PNL.v = pnlDefaults(PNL.k); pnlForm(); return; }
      if (x === 'copy') { var tx = pnlText(); if (navigator.clipboard) navigator.clipboard.writeText(tx).then(function () { b.textContent = '✅ 복사됨'; }); return; } if (x === 'xlsx') { pnlXlsx(); return; } });
    $('m2dPnl').addEventListener('input', function (e) { var t = e.target, el = $('m2dPnl');
      if (t.getAttribute('data-py')) { var a = t.value === '' ? null : Math.round(+t.value * 3.305785 * 10) / 10; PNL.v.area = a; var am = el.querySelector('[data-pf="area"]'); if (am) am.value = a == null ? '' : a; pnlOut(); return; }
      var k = t.getAttribute('data-pf'); if (!k) return; var val = t.value; PNL.v[k] = val === '' ? null : +val; el.querySelectorAll('[data-pf="' + k + '"]').forEach(function (x) { if (x !== t) x.value = val; }); if (/^(open|close|brk|rest|prep)$/.test(k)) schSync(); if (t.type === 'range') simLab(); if (k === 'area') { var pyi = el.querySelector('[data-py]'); if (pyi) pyi.value = val === '' ? '' : Math.round(+val / 3.305785 * 10) / 10; } pnlOut(); });
    $('m2dPnl').addEventListener('change', function (e) { if (e.target.getAttribute('data-pt') === 'useItem') { PNL.v.useItem = e.target.checked ? 1 : 0; pnlOut(); return; } if (e.target.getAttribute('data-pz') === 'brand') { brandApply(e.target.value); return; } if (e.target.getAttribute('data-pz') === 'k') { PNL.brand = ''; PNL.k = e.target.value; PNL.v = pnlDefaults(PNL.k); pnlForm(); if (PNL.c) pnlGather(); } });
  }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-pnlhere]'); if (!b) return; var a = b.getAttribute('data-pnlhere').split(','); pnlOpen(P(+a[0], +a[1])); });
  var JGGA = [], JGGL = {};
  function jgP(gu) { if (JGGL[gu]) return JGGL[gu]; JGGL[gu] = rGet(gu, 'jgg.json').then(function (j) { j.items.forEach(function (t) { var r0 = t[2][0], sx = 0, sy = 0; r0.forEach(function (q) { sx += q[0]; sy += q[1]; }); JGGA.push({ t: t, c: P(sx / r0.length, sy / r0.length), gu: gu }); }); JGGL[gu].done = 1; }).catch(function () { JGGL[gu].done = 1; }); return JGGL[gu]; }
  // ---------- 📝 이 동 풀어 읽기(v2.1.0 · 소유자 「동별·읍별로 데이터가 알려주는 만큼 구체적이고 세세하게 · 데이터를 충분히 풀어서 설명해야 이해도가 높아진다」) ----------
  //  화면의 숫자를 규칙으로 읽어 문단으로 쓴다(지어내는 문장 없음 · 기준은 문단 끝에) — 원인 단정·전국 맥락은 자료에 없어서 쓰지 않는다.
  var SDJ = {}, CPI = null, CPIP = null, GTAX = null, GCEN = null;
  fetch('data/gu-tax.json').then(function (r) { return r.json(); }).then(function (j) { GTAX = j; }).catch(function () {});
  fetch('data/gu-census.json').then(function (r) { return r.json(); }).then(function (j) { GCEN = j; }).catch(function () {});
  // v2.8.0 🌏 외국인주민(행안부 · 시군구 · 거주 3개월 넘게) — 서울 생활인구의 체류 외국인과 정의가 달라 합치지 않는다(설계서 4장)
  var FRN = null; fetch('data/foreign.json').then(function (r) { return r.json(); }).then(function (j) { FRN = j; var sd = {}; Object.keys(j.gu).forEach(function (k) { var v = j.gu[k]['2024']; if (!v || !v.pop || /시 전체/.test(j.gu[k].src)) return; var s2 = k.slice(0, 2); sd[s2] = sd[s2] || [0, 0]; sd[s2][0] += v.tot || 0; sd[s2][1] += v.pop; }); FRN.sd = sd; }).catch(function () {});
  function frnPara(gu) { var F2 = FRN && FRN.gu[gu]; if (!F2 || !F2['2024']) return ''; var v = F2['2024'], o = F2['2019'], sd = FRN.sd && FRN.sd[String(gu).slice(0, 2)], sh = v.pop ? v.tot / v.pop * 100 : null, ssh = sd && sd[1] ? sd[0] / sd[1] * 100 : null;
    var parts = [['외국인근로자', v.work], ['결혼이민자', v.marr], ['유학생', v.stud], ['외국국적동포', v.kor], ['기타 외국인', v.etc], ['귀화(한국국적 취득)', v.nat], ['외국인주민 자녀', v.kid]].filter(function (q) { return q[1]; }).sort(function (a, b) { return b[1] - a[1]; });
    var t = '<b>외국인 주민(구 · ' + esc(F2.src) + ').</b> ' + (v.tot || 0).toLocaleString() + '명' + (sh != null ? '(주민의 ' + sh.toFixed(1) + '%' + (ssh != null ? ' · ' + sidoOf(gu) + ' 평균 ' + ssh.toFixed(1) + '%' : '') + ')' : '') + ' — ' + parts.slice(0, 4).map(function (q) { return q[0] + ' ' + q[1].toLocaleString(); }).join(' · ');
    if (o && o.tot) { var ch = (v.tot - o.tot) / o.tot * 100; t += ' · 2019년 ' + o.tot.toLocaleString() + '명보다 ' + (ch >= 0 ? '+' : '') + ch.toFixed(0) + '%'; }
    if (F2.nat && F2.nat.length) t += ' · 국적은 ' + F2.nat.slice(0, 3).map(function (x) { return x[0] + ' ' + x[1].toLocaleString(); }).join('·') + '(법무부 등록외국인)';
    if (F2.q && F2.q['영주(F-5)']) t += ' · 영주권 ' + F2.q['영주(F-5)'].toLocaleString() + '명';
    if (F2.stay) { var ts2 = F2.stay.reduce(function (a, b) { return a + b; }, 0); if (ts2) t += ' · 5년 넘게 산 사람 ' + Math.round((F2.stay[5] + F2.stay[6]) / ts2 * 100) + '%'; }
    if (sh != null && ssh != null && sh >= ssh * 1.5) t += ' — 외국인 주민 비율이 시도 평균의 ' + (sh / ssh).toFixed(1) + '배: 외국어 안내·국적별 가게 수요가 있을 수 있다(추론).';
    else t += '.';
    return t + ' <small>(행정안전부 지방자치단체 외국인주민 현황 2024.11.1 · KOSIS 110 · 3개월 넘게 사는 사람 — 그 시각 머무는 사람(생활인구)과 다르다 · 구 전체 값이라 동마다 다르다)</small>'; }
  rGet('11650', 'dong.json').then(function (j) { var go = function () { if (!DONG.length) return setTimeout(go, 500); j.dong.forEach(function (q) { var d = DONG.filter(function (x) { return x.name === q.name; })[0]; if (d && !d.k && q.k) d.k = q.k; if (d && q.pop) { d.pop = q.pop; d.popAsOf = j.source && j.source['주민']; } }); }; go(); }).catch(function () {});   // v2.2.0 서초 기본 동도 지역 파일의 최신 주민등록(달마다 굽는 쪽) · v2.5.0 서초 동에도 8자리 코드(d.k — 이름 열쇠 대신 코드로 맞추는 첫걸음)
  function sdLoad(gu) { if (SDJ[gu]) return SDJ[gu]; SDJ[gu] = Promise.all([rGet(gu, 'dong.json').catch(function () { return null; }), rGet(gu, 'dongx.json').catch(function () { return null; }), fLoad(gu), jgP(gu), rGet(gu, 'dongw.json').catch(function () { return null; }), sLoad(gu), sLoadIdx(), rGet(gu, 'ggdong.json').catch(function () { return null; }), hmLoad(gu)]).then(function (a) { return { dong: a[0], x: a[1], w: a[4], gg: a[7] }; }); return SDJ[gu]; }
  function cpiLoad() { if (CPIP) return CPIP; CPIP = fetch('data/cpi.json').then(function (r) { return r.json(); }).then(function (j) { CPI = j; return j; }).catch(function () { return null; }); return CPIP; }
  // v2.5.0 qLab → qLab1 · sgn → sgn1 — 950·1956줄의 같은 이름 함수를 덮어 동 카드 분기 이름표·「%」가 깨졌다(v2.1.0~v2.4.0) · 새 이름은 모듈 안 grep 으로 겹침부터 확인
  function qLab1(q) { q = String(q); return q.slice(2, 4) + '년 ' + q.slice(4) + '분기'; }
  function sgn1(x, d) { return (x >= 0 ? '+' : '') + (d ? x.toFixed(d) : Math.round(x)) ; }
  function storyData(d) {
    var gu = d.gcd || '11650';
    return Promise.all([sdLoad(gu), cpiLoad()]).then(function (a) {
      var Dg = a[0].dong, Xg = a[0].x, row0 = Dg && Dg.dong.filter(function (q) { return d.k ? q.k === d.k : q.name === d.name; })[0] || {};
      var k = row0.k || d.k, F = RFAC[gu] && RFAC[gu].dong ? RFAC[gu].dong[k] || null : null; if (!F && RFAC[gu] && RFAC[gu].dong) for (var kk in RFAC[gu].dong) if (RFAC[gu].dong[kk].name === (row0.name || d.name)) { F = RFAC[gu].dong[kk]; break; } var X = Xg && Xg.dong ? Xg.dong[k] || null : null;
      var w = 0, c = 0, n = 0; JGGA.forEach(function (q) { if (q.gu === gu && q.t[1] === (row0.name || d.name)) { n++; w += q.t[9] || 0; c += q.t[8] || 0; } });
      var Wg = a[0].w, GGd = a[0].gg, guPop = Dg ? Dg.dong.reduce(function (x, q) { return x + (q.pop && q.pop.tot || 0); }, 0) : 0;
      return { d: d, guPop: guPop, GG: GGd && GGd.dong ? GGd.dong[k] || null : null, GGm: GGd, W: Wg && Wg.dong ? Wg.dong[k] || null : null, Wm: Wg, GT: GTAX && GTAX.gu[gu] || null, GTm: GTAX, GC: GCEN && GCEN.gu[gu] || null, GCa: GCEN && GCEN.gu, HMd: HOMED[gu] ? HOMED[gu].dong[k] || null : null, HMg: HOMED[gu] || null, gu: gu, sido: sidoOf(gu), name: row0.name || d.name, guName: (Dg && Dg.name) || d.gu || '', pop: row0.pop || d.pop, live: row0.live || d.live || liveArr(d), sales: row0.sales || d.sales || salesOf(d), X: X, quarters: Xg && Xg.quarters, F: F, Fm: RFAC[gu], wrk: n ? w : null, corp: n ? c : null };
    });
  }
  function storyHtml(S) {
    var ref = AREF && AREF.ref[S.sido] || {}, P = [], tags = [], p = S.pop, f1 = function (x) { return (Math.round(x * 10) / 10).toLocaleString(); }, pc = function (a, b) { return b ? a / b * 100 : 0; };
    var sum = function (a) { return (a || []).reduce(function (x, y) { return x + (y || 0); }, 0); };
    // ① 사는 사람
    if (p && p.tot) { var A = p.age, T = sum(A), s0 = pc(A[0], T), s2039 = pc(A[2] + A[3], T), s60 = pc(A[6] + A[7] + A[8] + A[9], T), s19 = pc(A[0] + A[1], T), RA = ref.age;
      var r60 = RA ? RA[6] + RA[7] + RA[8] + RA[9] : null, r2039 = RA ? RA[2] + RA[3] : null, r0 = RA ? RA[0] : null, t = '<b>사는 사람.</b> 주민 ' + p.tot.toLocaleString() + '명. ';
      t += '0~9세 ' + A[0].toLocaleString() + '명(' + f1(s0) + '%' + (r0 != null ? ' · ' + S.sido + ' 평균 ' + r0 + '%' : '') + '), 20·30대 ' + f1(s2039) + '%' + (r2039 != null ? '(평균 ' + f1(r2039) + '%)' : '') + ', 60세 이상 ' + f1(s60) + '%' + (r60 != null ? '(평균 ' + f1(r60) + '%)' : '') + '. ';
      var kind = r60 != null && s60 - r60 >= 3 ? '어르신 비중이 평균보다 높은 주거지' : r2039 != null && s2039 - r2039 >= 3 ? '젊은 층 비중이 평균보다 높은 동' : r0 != null && s0 - r0 >= 1 ? '아이 있는 집이 평균보다 많은 동' : '연령 구성이 ' + S.sido + ' 평균과 비슷한 동';
      t += '인구 구조만 보면 <b>' + kind + '</b>이다.';
      if (S.F && S.F.sex) { var m = S.F.sex[0], fm = S.F.sex[1], sr = m / fm * 100; t += ' 남 ' + m.toLocaleString() + ' · 여 ' + fm.toLocaleString() + '(여자 100명당 남자 ' + Math.round(sr) + '명)' + (sr >= 110 ? ' — <b>남자가 눈에 띄게 많다</b>: 공장·산업단지·건설 현장 근로자가 사는 동에서 흔한 모습이다(추론 · 일하는 사람 문단과 같이 본다).' : sr <= 88 ? ' — 여자가 더 많다: 어르신(여성이 오래 산다)이나 젊은 여성 1인 가구가 많은 동에서 흔하다(추론 · 연령과 같이 본다).' : '.'); }
      if (S.F && S.F.cc && S.F.cc[1]) { var fill = S.F.cc[2] > 0 ? pc(S.F.cc[2], S.F.cc[1]) : null; t += ' 어린이집 ' + S.F.cc[0] + '곳 · 정원 ' + S.F.cc[1].toLocaleString() + '명' + (fill != null ? ', 지금 ' + S.F.cc[2].toLocaleString() + '명 — ' + Math.round(fill) + '% 찬다' + (fill < 60 ? '(아이가 줄었거나 다른 동으로 다닌다)' : '') : '(이 자료에는 현원이 없다)') + '.';
        if (S.F.ccy && S.Fm && S.Fm.cyears) { var cy = S.F.ccy; t += ' 어린이집 수는 ' + S.Fm.cyears[0] + '년 ' + cy[0] + '곳 → 지금 ' + cy[cy.length - 1] + '곳.'; } }
      if (S.F && S.F.aca != null) t += ' 입시·교과 학원 ' + S.F.aca + '곳(학원 전체 ' + (S.F.acaAll || '-') + ')' + (s19 < 12 && S.F.aca > 20 ? ' — 학원 수는 이 동 아이 수와 따로 간다(다른 동 아이들이 온다)' : '') + '.';
      if (/[읍면]$/.test(S.name)) t += ' <small>(' + esc(S.name) + '은 여러 리(里)로 나뉘지만 주민·카드·유동인구 통계는 읍·면 단위까지만 공개된다 — 리마다 다른 사정은 이 숫자에 섞여 있다)</small>';
      tags.push(r60 != null && s60 - r60 >= 3 ? '어르신 많은 주거지' : r2039 != null && s2039 - r2039 >= 3 ? '젊은 층 많음' : r0 != null && s0 - r0 >= 1 ? '아이 많음' : '연령은 ' + S.sido + ' 평균 수준'); P.push(t); }
    // ② 머무는 사람
    var L = S.live; if (L && (L.wd || L.we) && p && p.tot) { var t2 = '<b>머무는 사람.</b> ', o = [];
      ['wd', 'we'].forEach(function (k2) { var a = L[k2]; if (!a) return; var mx = Math.max.apply(null, a), mn = Math.min.apply(null, a), pk = a.indexOf(mx), busy = []; a.forEach(function (v, i) { if (v >= mn + (mx - mn) * 0.7) busy.push(i); });
        o.push((k2 === 'wd' ? '평일' : '주말') + '에는 ' + pk + '시에 ' + mx.toLocaleString() + '명으로 가장 많고(주민의 ' + Math.round(mx / p.tot * 100) + '%), 가장 적을 때 ' + mn.toLocaleString() + '명 · 붐비는 때 ' + busy[0] + '~' + busy[busy.length - 1] + '시'); });
      t2 += o.join('. ') + '. ';
      var mxa = Math.max.apply(null, (L.wd || []).concat(L.we || [])), ratio = mxa / p.tot;
      t2 += ratio >= 1.3 ? '머무는 사람이 주민보다 <b>' + Math.round((ratio - 1) * 100) + '% 많다</b> — 밖에서 들어왔다가 빠지는 사람이 주민 수 밖에 있다(일·장보기·술자리).' : ratio <= 0.95 ? '가장 붐빌 때도 주민 수보다 적다 — <b>낮에 주민이 밖으로 나가는 동</b>(출근·통학).' : '머무는 사람과 주민 수가 비슷하다 — 들고 나는 사람이 크지 않다.';
      t2 += ' <small>(생활인구 = 그 시각 동 안에 있는 사람 수를 통신으로 추정한 값 — 하루 방문자 수가 아니다)</small>';
      if (ratio >= 1.3) tags.push('밖에서 사람이 들어오는 곳'); P.push(t2); }
    // ③ 일하는 사람
    if (S.wrk != null && p && p.tot) { var r3 = S.wrk / p.tot, rr = ref.wrkPerPop, t3 = '<b>일하는 사람.</b> 이 동 집계구를 합치면 사업체 ' + Math.round(S.corp).toLocaleString() + '곳 · 종사자 ' + Math.round(S.wrk).toLocaleString() + '명 — 주민의 ' + f1(r3) + '배' + (rr ? '(' + S.sido + ' 평균 ' + rr + '배)' : '') + '. ';
      t3 += r3 >= 2 ? '<b>일터형</b> — 낮에 일하러 오는 사람이 사는 사람보다 훨씬 많다. 평일 점심·퇴근길 장사.' : r3 >= 0.8 ? '<b>주거·일터 섞임</b> — 점심 손님(직장인)과 저녁 손님(주민)이 둘 다 있다.' : '<b>주거형</b> — 일터가 적어 낮 장사보다 저녁·주말 장사.';
      if (S.W && S.W.wrc && S.W.wrc[0]) { var wa = S.W.wrc[3], wt = sum(wa) || 1, WAG = ['10대', '20대', '30대', '40대', '50대', '60대 이상'], wm = wa.indexOf(Math.max.apply(null, wa)); t3 += ' 서울시 직장인구(' + qLab1(S.Wm.quarters.wrc) + ')로 보면 이 동에서 일하는 사람 ' + Math.round(S.W.wrc[0]).toLocaleString() + '명은 ' + WAG.map(function (n0, i) { return n0 + ' ' + Math.round(wa[i] / wt * 100) + '%'; }).join(' · ') + ' · 남 ' + Math.round(S.W.wrc[1] / S.W.wrc[0] * 100) + '% — 점심 손님은 <b>' + WAG[wm] + '</b>가 가장 많다.'; }
      t3 += ' <small>(통계청 SGIS 집계구 2023' + (S.W && S.W.wrc ? ' · 서울시 상권분석 직장인구' : '') + ' · 기준: 종사자÷주민 2배↑ 일터형 · 0.8배↓ 주거형 — 앱 기준)</small>'; tags.push(r3 >= 2 ? '일터' : r3 >= 0.8 ? '주거·일터 섞임' : '주거지'); P.push(t3); }
    if (S.F && S.F.gov) { var gk = Object.keys(S.F.gov); if (gk.length) P.push('<b>관공서.</b> ' + gk.map(function (k4) { return k4 + ' ' + S.F.gov[k4]; }).join(' · ') + ' — 공무원 점심과 민원인 낮 유입이 있다. 시청·구청·법원·세무서 같은 큰 곳일수록 크다. <small>(OSM·공식 관공서 자리)</small>'); }
    // ③-2 지갑(구매력) — 동 = 공동주택 시세·평형 · 구 = 국세청(구 평균 — 나누지 않는다)
    var WP = []; if (S.W && S.W.apt && sum(S.W.apt[2]) > 0) { var ap = S.W.apt, hh = sum(ap[2]), aa = sum(ap[1]) || 1, six = ap[2][6] / hh * 100, rw = ref.w || {}, ARN = ['66㎡ 미만', '66~99㎡', '99~132㎡', '132~165㎡', '165㎡ 이상'];
      var tw = '<b>지갑(사는 사람의 자산).</b> 이 동 공동주택 ' + Math.round(ap[0]) + '단지 · ' + Math.round(hh).toLocaleString() + '가구 — 평형: ' + ARN.map(function (n0, i) { return n0 + ' ' + Math.round(ap[1][i] / aa * 100) + '%'; }).join(' · ') + ' · 평균 ' + ap[3] + '㎡. 시세 6억 이상 가구 <b>' + f1(six) + '%</b>' + (rw.six_med != null ? '(서울 동 중앙값 ' + rw.six_med + '% · 상위 20% 경계 ' + rw.six_p80 + '%)' : '') + ', 평균 시세 <b>' + won(ap[4]) + '</b>' + (rw.mktc_med ? '(서울 동 중앙값 ' + won(rw.mktc_med) + ' · 상위 20% ' + won(rw.mktc_p80) + ')' : '') + ' — ';
      var hi = rw.mktc_p80 && ap[4] >= rw.mktc_p80, mid = rw.mktc_med && ap[4] >= rw.mktc_med; tw += hi ? '<b>서울에서 집값이 높은 쪽(상위 20%)</b>이라 주민 자산 구매력이 크다.' : mid ? '서울 동 가운데 중간보다 높다.' : '서울 동 가운데 중간보다 낮다(소형·저가 공동주택이 많다).';
      tw += ' 같은 가구 수라도 20평대와 40평대는 다른 시장이다 — 평형 구성이 손님층의 크기를 말해 준다. <small>(서울시 상권분석서비스 아파트-행정동 ' + qLab1(S.Wm.quarters.apt) + ' · 서울신용보증재단 추정 시세 · 단지·가구 수는 이 자료가 시세를 잡은 곳만이라 실제 세대 수보다 적을 수 있다(소규모 공동주택 포함 · 단독·다가구 빠짐) — 비율과 시세 수준으로 읽는다)</small>';
      WP.push(tw); tags.push(hi ? '집값 상위 20% 동' : mid ? '집값 중간 이상' : '집값 중간 이하'); }
    if (S.GT && (S.GT.wage || S.GT.inc)) { var G2 = S.GT, gn = S.guName || '이 구', tg = '<b>구 지갑(참고 · 구 평균 — 이 동에 나누지 않는다).</b> ' + esc(gn) + ' ';
      if (G2.wage) tg += '근로자 1인당 총급여 <b>' + won(G2.wage[0]) + '</b>(' + S.GTm.years.wage + '년 · 주소지 기준 · ' + (S.sido === '서울' ? '서울 25개 구' : S.sido + ' 시군구') + ' 중 ' + G2.wageR[0] + '위)';
      if (G2.inc) tg += ' · 종합소득 신고자 1인당 종합소득금액 <b>' + won(G2.inc[0]) + '</b>(' + S.GTm.years.inc + '년 · ' + G2.incR[0] + '위)';
      if (G2.jbs && G2.jbs[1] != null) tg += ' · 종합부동산세 주택분 ' + won(G2.jbs[1] * 100) + '(' + S.GTm.years.jbs + '년)';
      if (S.GC) { var C2 = S.GC, CA = S.GCa['_' + S.sido] || {};
        tg += ' · 2020 인구주택총조사(' + esc(C2.src) + '): 사는 집이 <b>자기집 ' + C2.own + '%</b> · 전세 ' + C2.jeonse + '% · 월세 ' + C2.wolse + '%(' + S.sido + ' 평균 자기집 ' + CA.own + '% · 월세 ' + CA.wolse + '%)' + (C2.uni4 != null ? ' · 25세 이상 4년제 대학 졸업 이상 <b>' + C2.uni4 + '%</b>(평균 ' + CA.uni4 + '%)' : '');
        if (C2.wolse >= (CA.wolse || 99) + 5) tg += ' — 월세 사는 집이 많다: 젊은 1~2인 가구·이동이 잦은 동네일 가능성(구 평균 · 추론)';
        else if (C2.own >= (CA.own || 99) + 8) tg += ' — 자기집이 많다: 오래 사는 가구·자산 쪽(구 평균 · 추론)'; }
      tg += '. 이 숫자는 구(시) 전체 평균이라 그 안의 동네마다 다르다 — 부자 동네와 아닌 동네가 섞인 값이다. <small>(국세청 국세통계 KOSIS 133 · 종부세는 공제를 넘는 사람만 세서 중간 자산이 빠진다 · 점유형태·학력 = 통계청 2020 총조사 시군구(KOSIS DT_1PE2002·DT_1PM2001 · 동 단위 공식 값 없음 · 경기 일반구·화성·부천 새 구는 시 전체) · 차량 보유는 시군구 공식 표를 찾지 못해 넣지 않았다)</small>';
      if (S.W && S.W.apt && sl0(S) && ref.amtPerPopMed && rw0(ref, S)) tg += ' 집값은 서울 위쪽인데 주민 1인당 카드 매출은 중앙값 아래다 — <b>이 동 주민의 소비는 동 밖(큰 상권)에서 이뤄질 가능성이 크다</b>(어디로 가는지는 이 자료에 없다 · 추론).';
      WP.push(tg); }
    if (S.HMd) { var HV = S.HMd, gm = function (t, i) { var a2 = []; for (var q in S.HMg.dong) { var z = S.HMg.dong[q][t]; if (z && z[i] != null && z[i - 1] >= 3) a2.push(z[i]); } a2.sort(function (x, y) { return x - y; }); return a2.length >= 3 ? a2[Math.floor(a2.length / 2)] : null; };
      var hp = '<b>집값·전월세(실거래 · 이 동).</b> ', seg = [];
      [['a', '아파트'], ['o', '오피스텔'], ['r', '연립다세대']].forEach(function (q) { var x = HV[q[0]]; if (!x) return; var g1 = gm(q[0], 1);
        seg.push(q[1] + ' ' + (x[0] ? '매매 ' + x[0] + '건 평당 <b>' + pyeong(x[1]) + '</b>' + (g1 && x[0] >= 3 ? '(' + esc(S.guName || '구') + ' 동 중앙 ' + pyeong(g1) + ')' : '') : '매매 없음') + (x[2] ? ' · 전세 ' + x[2] + '건 평당 ' + pyeong(x[3]) : '') + (x[4] ? ' · 월세 ' + x[4] + '건 중앙 ' + x[5] + '만' : '') + (x[6] != null ? ' · 전세가율 ' + x[6] + '%' : '')); });
      if (seg.length) { hp += seg.join(' / ') + '.';
        var ax = HV.a, gj = gm('a', 6); if (ax && ax[6] != null && gj != null) hp += ax[6] >= gj + 8 ? ' 전세가율이 구 안 동들보다 높다 — 세입자·실수요가 많고 집값에 거품이 덜한 쪽(추론).' : ax[6] <= gj - 8 ? ' 전세가율이 구 안 동들보다 낮다 — 자가·투자 수요가 집값을 받치는 쪽(추론).' : '';
        if (ax && ax[4] && ax[2] && ax[4] > ax[2]) hp += ' 아파트도 월세 계약이 전세보다 많다 — 매달 나가는 돈이 큰 가구가 많다(추론).';
        hp += ' <small>(국토부 실거래 · 매매 24개월·전월세 12개월 · 지번 좌표로 행정동을 가름 · 평당 = 전용 기준 · 전세가율 = 전세 ㎡당 중앙값 ÷ 매매 ㎡당 중앙값(추정) · 몇 건뿐이면 한 건이 값을 정한다)</small>'; WP.push(hp); } }
    var fp = frnPara(S.gu); if (fp) WP.push(fp);
    WP.forEach(function (x) { P.push(x); });
    // 경기 — 경기데이터드림 동 단위 유동인구·카드(서울 자료가 없는 자리)
    if (S.GG && S.GG.flow && p && p.tot) { var fy = Object.keys(S.GG.flow).sort(), fl = S.GG.flow[fy[fy.length - 1]], WDN = { MON: '월', TUE: '화', WED: '수', THU: '목', FRI: '금', SAT: '토', SUN: '일' }, wdA = ['MON', 'TUE', 'WED', 'THU', 'FRI'].map(function (w) { return fl[w] || 0; }), weA = ['SAT', 'SUN'].map(function (w) { return fl[w] || 0; });
      var wdv = sum(wdA) / 5, wev = sum(weA) / 2, f0 = S.GG.flow[fy[0]], av0 = f0 ? sum(Object.keys(f0).map(function (w) { return f0[w]; })) / Object.keys(f0).length : null, avL = sum(Object.keys(fl).map(function (w) { return fl[w]; })) / Object.keys(fl).length;
      var tf = '<b>머무는 사람(경기 유동인구).</b> ' + fy[fy.length - 1] + '년 평균 유동인구는 평일 약 ' + Math.round(wdv).toLocaleString() + '명 · 주말 약 ' + Math.round(wev).toLocaleString() + '명 — ';
      tf += wev > wdv * 1.08 ? '<b>주말에 더 붐빈다</b>(나들이·쇼핑·주말 외식).' : wev < wdv * 0.92 ? '<b>주말에 빈다</b> — 평일에 일하러 오는 사람이 많은 동.' : '평일과 주말이 비슷하다.';
      if (av0 && fy[0] !== fy[fy.length - 1]) tf += ' ' + fy[0] + '년보다 ' + sgn1(pc(avL - av0, av0)) + '%.';
      tf += ' <small>(경기데이터드림 「데이터분석 유동인구 요일별 행정동」 · 최신 ' + esc(S.GGm.flowLast || '') + ' · 통신 기반 추정 — 세는 법(시간 평균 등)이 서울 생활인구·주민 수와 달라 크기를 견주지 않고 평일·주말 차이와 해마다 변화로만 읽는다)</small>'; P.push(tf); }
    if (S.GG && S.GG.card && S.GG.card['2025']) { var c25 = S.GG.card['2025'], NM = S.GGm.names || {}, tot25 = sum(Object.keys(c25).map(function (c) { return c25[c]; })), tops = Object.keys(c25).sort(function (a, b) { return c25[b] - c25[a]; }).slice(0, 5);
      var tc = '<b>돈(경기 카드 매출).</b> 2025년 1~6월 월평균 약 <b>' + won(tot25) + '</b>' + (p && p.tot ? ' — 주민 1명으로 나누면 월 ' + Math.round(tot25 / p.tot).toLocaleString() + '만 원' + (ref.ggAmtPerPopMed ? '(경기 동 중앙값 ' + ref.ggAmtPerPopMed + '만 · 상위 20% 경계 ' + ref.ggAmtPerPopP80 + '만) — ' + (tot25 / p.tot >= ref.ggAmtPerPopP80 ? '<b>주민 수에 비해 돈이 아주 많이 도는 동</b>(바깥 손님·큰 상권)' : tot25 / p.tot >= ref.ggAmtPerPopMed ? '경기 동 평균보다 돈이 많이 돈다' : '경기 동 평균보다 적다 — <b>주민 생활 지출 중심</b>') : '') : '') + '. ';
      var cyr = function (y) { var x = S.GG.card[y]; return x ? sum(Object.keys(x).map(function (c) { return x[c]; })) : null; }, t23 = cyr('2023'), t22 = cyr('2022'), cH = function (y) { var a1 = CPI && CPI.q[y + '1'] && CPI.q[y + '1'][S.sido], a2 = CPI && CPI.q[y + '2'] && CPI.q[y + '2'][S.sido]; return a1 && a2 ? (a1[0] + a2[0]) / 2 : null; };
      if (t23) { var c23 = cH('2023'), c25p = cH('2025'); tc += '같은 1~6월끼리 2023년 ' + won(t23) + ' → 2025년 ' + won(tot25) + '(명목 ' + sgn1(pc(tot25 - t23, t23)) + '%' + (c23 && c25p ? ' · 경기 물가 ' + sgn1(pc(c25p - c23, c23), 1) + '% → <b>실질 ' + sgn1((tot25 / c25p) / (t23 / c23) * 100 - 100) + '%</b>' : '') + ')' + (t22 ? ' · 2022년 ' + won(t22) : '') + '. '; }
      tc += '<small>(경기데이터드림 「카드매출_행정동_집계」 — 달마다 담긴 범위가 달라 빠짐없이 담긴 1~6월끼리만 견준다 · 서울시 추정매출과 만든 곳·세는 법이 달라 서울 동과 금액을 직접 견주지 않는다 · 업종 코드표가 공개되지 않아 업종 이름을 붙이지 않았다 · 시간대·요일·연령은 경기 동 단위로 쓸 만한 자료가 없다(시간대 자료는 2020년 3월 한 달뿐))</small>'; P.push(tc); }
    if (S.sido === '경기' && !S.GG && S.GGm) P.push('<b>머무는 사람·돈(경기).</b> 이 동은 최근 새로 생기거나 나뉜 동이라 경기데이터드림 유동인구·카드 자료(옛 동 기준)와 맞지 않는다 — 옛 동 값을 나눠 지어내지 않는다.');
    // 가게 구성 — 상가업소(소상공인시장진흥공단)를 이 동 안에서 세어 구 평균과
    if (S.d && S.d.polys && SPTS[S.gu] && SPTS[S.gu].a && SIDX && p && p.tot && S.guPop) { var CLs = SIDX.cls, inD = {}, inG = {}, nD = 0;
      SPTS[S.gu].a.forEach(function (st) { var c3 = CLs[st.c]; if (!c3) return; var key = c3[1]; inG[key] = (inG[key] || 0) + 1; if (inPoly(S.d, st.p)) { inD[key] = (inD[key] || 0) + 1; nD++; } });
      if (nD) { var rows = Object.keys(inD).sort(function (a, b) { return inD[b] - inD[a]; }).slice(0, 7).map(function (k5) { var dp = inD[k5] / p.tot * 1000, gp = (inG[k5] || 0) / S.guPop * 1000; return [k5, inD[k5], dp, gp]; });
        var tg2 = '<b>가게 구성.</b> 이 동 안 상가 ' + nD.toLocaleString() + '곳(주민 1천 명당 ' + f1(nD / p.tot * 1000) + '곳). 업종별 주민 1천 명당(구 평균): ' + rows.map(function (r) { return esc(r[0]) + ' ' + r[1].toLocaleString() + '곳 ' + f1(r[2]) + '(' + f1(r[3]) + ')'; }).join(' · ') + '. ';
        var hot = rows.filter(function (r) { return r[3] > 0 && r[2] / r[3] >= 1.5 && r[1] >= 10; }); if (hot.length) tg2 += '<b>' + hot.map(function (r) { return esc(r[0]) + josa(r[0], '이', '가') + ' 구 평균의 ' + f1(r[2] / r[3]) + '배'; }).join(' · ') + '</b> — 주민 수보다 그 업종 가게가 몰려 있다(바깥 손님을 받는 곳이거나 경쟁이 센 곳). ';
        tg2 += '<small>(소상공인시장진흥공단 상가(상권)정보 ' + esc(SPTS[S.gu].ym || '') + ' · 이 동 경계 안 점포 · 구 평균 = 구 전체 점포 ÷ 구 주민)</small>'; P.push(tg2); } }
    // ④ 돈이 어디서 도나
    var sl = S.sales; if (sl && sl.amt) { var per = p && p.tot ? sl.amt / p.tot : null, t4 = '<b>돈.</b> 카드 매출 한 달 약 ' + won(sl.amt) + ' · 결제 ' + man(sl.cnt) + '건 → 결제 1건 평균 ' + Math.round(sl.amt * 1e4 / sl.cnt).toLocaleString() + '원. ';
      if (per) { t4 += '주민 1명으로 나누면 월 ' + Math.round(per).toLocaleString() + '만 원(서울 동 중앙값 ' + ref.amtPerPopMed + '만 · 상위 20% 경계 ' + ref.amtPerPopP80 + '만) — ';
        t4 += per >= ref.amtPerPopP80 ? '<b>주민 수에 비해 돈이 아주 많이 도는 동</b>이다. 이 돈의 대부분은 동 밖에서 온 사람이 쓴 것이다.' : per >= ref.amtPerPopMed ? '평균보다 돈이 많이 돈다 — 주민 지출에 바깥 손님 지출이 얹혀 있다.' : '평균보다 적다 — <b>주민 생활 지출 중심</b>인 동네 상권.'; }
      var TR = S.F && S.F.trd; if (TR && TR.length) { var tot = sum(TR.map(function (x) { return x[3]; })), top = TR.slice().sort(function (a, b) { return b[3] - a[3]; });
        t4 += ' 이 동에 걸친 상권 ' + TR.length + '곳의 최근 1년 매출 약 ' + won(tot) + ' 중 <b>' + esc(top[0][1]) + '</b>(' + esc(top[0][2]) + ') 한 곳이 ' + Math.round(pc(top[0][3], tot)) + '%' + (pc(top[0][3], tot) >= 70 ? ' — <b>이 동의 돈 이야기는 사실상 이 상권 이야기</b>다. 같은 동을 한 덩어리로 읽으면 이 상권의 장사를 동네 주택가에 붙이는 잘못을 한다.' : '.');
        t4 += ' 상권별로: ' + top.map(function (x) { return esc(x[1]) + ' ' + won(x[3]) + '(' + (x[4] ? sgn1(pc(x[3] - x[4], x[4])) + '%' : '-') + ' · ' + esc(x[5] || '') + ')'; }).join(' · ') + '. <small>(최근 1년 vs 처음 1년(2021~) · 지표 = 서울시 상권변화지표)</small>';
        if (top[0] && pc(top[0][3], tot) >= 70) tags.push(top[0][1].replace(/\(.*\)/, '') + ' 상권이 돈의 ' + Math.round(pc(top[0][3], tot)) + '%'); }
      P.push(t4);
      // ⑤ 시간·요일
      if (sl.tb && sl.tb.length === 6) { var TBN = ['0~6시', '6~11시', '11~14시', '14~17시', '17~21시', '21~24시'], perH = sl.tb.map(function (v, i) { return v / TBH[i] / 30.4; }), pk2 = perH.indexOf(Math.max.apply(null, perH)), lunch = perH[2], eve = perH[4];
        var t5 = '<b>시간.</b> 시간당 매출이 가장 큰 때는 <b>' + TBN[pk2] + '</b>(시간당 약 ' + won(perH[pk2]) + '). 점심(11~14시) 시간당 ' + won(lunch) + ' · 저녁(17~21시) ' + won(eve) + ' · 밤(21~24시) ' + won(perH[5]) + ' · 새벽 ' + won(perH[0]) + ' — ';
        t5 += eve > lunch * 1.2 ? '<b>저녁 장사가 중심</b>인 동.' : lunch > eve * 1.2 ? '<b>점심 장사가 중심</b>인 동(직장인).' : '점심과 저녁이 비슷하다.';
        if (perH[5] > lunch) t5 += ' 밤 9시 뒤가 점심보다 크다 — 술자리 상권.';
        if (sl.dw && sl.dw.length === 7) { var DW = ['월', '화', '수', '목', '금', '토', '일'], mxD = sl.dw.indexOf(Math.max.apply(null, sl.dw)), mnD = sl.dw.indexOf(Math.min.apply(null, sl.dw)), we = pc(sl.dw[5] + sl.dw[6], sum(sl.dw)), rw = ref.dw ? ref.dw[5] + ref.dw[6] : null;
          t5 += ' 요일: 가장 큰 날 ' + DW[mxD] + '(' + won(sl.dw[mxD]) + '), 가장 작은 날 ' + DW[mnD] + '(' + won(sl.dw[mnD]) + ') — ' + DW[mxD] + '요일이 ' + DW[mnD] + '요일의 ' + f1(sl.dw[mxD] / sl.dw[mnD]) + '배. 토·일 비중 ' + f1(we) + '%' + (rw ? '(서울 평균 ' + f1(rw) + '%)' : '') + (rw && we < rw - 3 ? ' — 주말 장사가 약하다.' : rw && we > rw + 3 ? ' — 주말 장사가 강하다.' : '.'); }
        if (eve > lunch * 1.2) tags.push('저녁 상권'); else if (lunch > eve * 1.2) tags.push('점심 상권');
        P.push(t5); } }
    // ⑥ 물가를 걷은 추이
    var X = S.X, Q = S.quarters; if (X && X.tr && Q && X.tr.length > 4 && CPI) { var tr = X.tr, n0 = 0, nL = tr.length - 1, ser = tr.map(function (r) { return r[0]; }), pkI = ser.indexOf(Math.max.apply(null, ser)), ci = function (q, j) { var c = CPI.q[q]; return c && c[S.sido] ? c[S.sido][j] : null; };
      var c0 = ci(Q[n0], 0), cL = ci(Q[nL], 0) || ci(CPI.last.slice(0, 4) + String(Math.ceil(+CPI.last.slice(4) / 3)), 0), cP = ci(Q[pkI], 0);
      var t6 = '<b>추이(물가를 걷고).</b> 카드 매출(한 달 기준)은 ' + qLab1(Q[n0]) + ' ' + won(ser[n0]) + ' → 고점 ' + qLab1(Q[pkI]) + ' ' + won(ser[pkI]) + ' → 지금(' + qLab1(Q[nL]) + ') ' + won(ser[nL]) + '. ';
      var nom = pc(ser[nL] - ser[n0], ser[n0]); t6 += '처음보다 명목 ' + sgn1(nom) + '%';
      if (c0 && cL) { var real = (ser[nL] / cL) / (ser[n0] / c0) * 100 - 100; t6 += ', 같은 기간 소비자물가(' + S.sido + ' 총지수)는 ' + sgn1(pc(cL - c0, c0), 1) + '% — 물가만큼 올랐다면 ' + won(ser[n0] * cL / c0) + '이어야 하니 <b>실질 ' + sgn1(real) + '%</b>'; }
      t6 += '. 고점보다는 명목 ' + sgn1(pc(ser[nL] - ser[pkI], ser[pkI])) + '%' + (cP && cL ? '(실질 ' + sgn1((ser[nL] / cL) / (ser[pkI] / cP) * 100 - 100) + '%)' : '') + '.';
      if (String(Q[n0]).slice(0, 4) === '2021') t6 += ' <small>(2021년 초는 영업 제한기라 바닥이다 — 그 대비 배율은 성장이라기보다 회복이다. 고점과 지금을 견주는 쪽이 더 정확하다.)</small>';
      var bs = tr.map(function (r) { return r[7] || 0; }); if (sum(bs) > 0) { var bp = bs.indexOf(Math.max.apply(null, bs)), e0 = ci(Q[n0], 1), eL = ci(Q[nL], 1) || ci(CPI.last.slice(0, 4) + String(Math.ceil(+CPI.last.slice(4) / 3)), 1), eP = ci(Q[bp], 1);
        t6 += ' 주점·노래방류는 ' + won(bs[n0]) + ' → 고점 ' + won(bs[bp]) + '(' + qLab1(Q[bp]) + ') → 지금 ' + won(bs[nL]) + ' — 고점보다 명목 ' + sgn1(pc(bs[nL] - bs[bp], bs[bp])) + '%' + (eP && eL ? ', 외식 물가로 걷으면 ' + sgn1((bs[nL] / eL) / (bs[bp] / eP) * 100 - 100) + '%' : '') + '.'; }
      var nt = tr.map(function (r) { return r[6] || 0; }); if (sum(nt) > 0) { var np = nt.indexOf(Math.max.apply(null, nt)); t6 += ' 밤(21~24시) 매출도 고점 ' + won(nt[np]) + ' → 지금 ' + won(nt[nL]) + '(' + sgn1(pc(nt[nL] - nt[np], nt[np])) + '%).'; }
      t6 += ' <small>(소비자물가: ' + esc(CPI.source) + ' · 최신 ' + CPI.last.slice(0, 4) + '년 ' + +CPI.last.slice(4) + '월)</small>';
      var dPk = pc(ser[nL] - ser[pkI], ser[pkI]), tag6 = dPk <= -5 ? '매출이 고점보다 ' + Math.round(-dPk) + '% 아래' : pc(ser[nL] - ser[n0], ser[n0]) >= 10 ? '매출이 커지는 중' : '매출 큰 변화 없음'; tags.push(tag6); P.push(t6); }
    // ⑦ 업종별 손님 — 주민인가 바깥 손님인가
    if (X && X.ind && X.ind.length && p && p.tot) { var A2 = p.age, T2 = sum(A2), res2039 = pc(A2[2] + A2[3], T2), res60 = pc(A2[6] + A2[7] + A2[8] + A2[9], T2), TBN2 = ['새벽', '아침', '점심', '오후', '저녁', '밤'];
      var top7 = X.ind.slice().sort(function (a, b) { return b[1] - a[1]; }).slice(0, 6), allA = sum(X.ind.map(function (r) { return r[1]; }));
      var t7 = '<b>업종별 손님.</b> 결제한 사람의 나이를 주민 나이와 겹쳐 보면 그 장사가 동네 사람 장사인지 바깥 손님 장사인지 갈린다(주민 20·30대 ' + f1(res2039) + '% · 60세 이상 ' + f1(res60) + '%). ';
      t7 += top7.map(function (r) { var ag = r.slice(9, 15), at = sum(ag) || 1, y = pc(ag[1] + ag[2], at), o6 = pc(ag[5], at), tb = r.slice(3, 9), pkb = tb.indexOf(Math.max.apply(null, tb)), shb = pc(tb[pkb], sum(tb));
        var who = y - res2039 >= 15 ? '<b>바깥 젊은 손님</b> 장사' : o6 >= res60 && o6 >= 30 ? '<b>동네 어르신</b> 장사' : '주민과 비슷한 손님'; return esc(r[0]) + '(월 ' + won(r[1]) + ' · ' + Math.round(pc(r[1], allA)) + '%) — 20·30대 ' + Math.round(y) + '%, 60세 이상 ' + Math.round(o6) + '%, ' + TBN2[pkb] + ' ' + Math.round(shb) + '% → ' + who; }).join('; ') + '.';
      var bars = X.ind.filter(function (r) { return isBar(r[0]); }); if (bars.length) { var bA = sum(bars.map(function (r) { return r[1]; })), bC = sum(bars.map(function (r) { return r[2]; })), nightA = sum(bars.map(function (r) { return r[3] + r[8]; }));
        t7 += ' 주점·유흥 결제는 한 달 ' + man(bC) + '건, 건당 약 ' + Math.round(bA * 1e4 / (bC || 1)).toLocaleString() + '원 — 한 잔 값이 아니라 <b>테이블 객단가</b>다. 밤(21~6시)이 금액의 ' + Math.round(pc(nightA, bA)) + '%.'; }
      t7 += ' <small>(기준: 결제 20·30대가 주민보다 15%p↑면 바깥 젊은 손님 · 60세 이상 결제가 30%↑이고 주민 비중 이상이면 동네 어르신 — 앱 기준 · 결제 연령은 개인 카드만)</small>';
      P.push(t7); }
    // ⑧ 가게 수와 돈
    if (S.F && S.F.st && S.F.st.length > 2) { var st = S.F.st, a0 = st[0], aL = st[st.length - 1], op = sum(st.map(function (x) { return x[2]; })) / st.length, cl = sum(st.map(function (x) { return x[3]; })) / st.length, chg = pc(aL[1] - a0[1], a0[1]);
      var t8 = '<b>가게 수.</b> 상권분석 점포(업종 합) ' + qLab1(a0[0]) + ' ' + a0[1].toLocaleString() + '곳 → ' + qLab1(aL[0]) + ' ' + aL[1].toLocaleString() + '곳(' + sgn1(chg) + '%) · 분기마다 평균 개업 ' + Math.round(op) + ' · 폐업 ' + Math.round(cl) + '곳. ';
      if (S.F.ix && S.F.ix.length) { var ix = S.F.ix[S.F.ix.length - 1], nm = S.Fm && S.Fm.ix_names ? S.Fm.ix_names[ix[1]] || ix[1] : ix[1]; t8 += '상권변화지표 <b>' + esc(nm) + '</b>(' + qLab1(ix[0]) + ' · 운영 평균 ' + ix[2] + '개월 · 폐업까지 평균 ' + ix[3] + '개월). '; }
      if (X && X.tr && X.tr.length > 4) { var sN = pc(X.tr[X.tr.length - 1][0] - X.tr[0][0], X.tr[0][0]); t8 += Math.abs(chg) < 5 && sN > 15 ? '가게 수는 거의 그대로인데 카드 금액은 ' + sgn1(sN) + '% — <b>가게가 늘어서가 아니라 한 가게가 버는 돈이 커졌다</b>(물가 몫 포함).' : chg > 10 && sN < chg ? '가게는 ' + sgn1(chg) + '% 늘었는데 금액은 ' + sgn1(sN) + '% — 가게당 매출은 얇아졌다.' : ''; }
      P.push(t8); }
    // ⑨ 사업체 10년
    if (S.F && S.F.bz && S.F.bz.length > 2) { var bz = S.F.bz, b20 = bz.filter(function (x) { return x[0] === '2020'; })[0], bL = bz[bz.length - 1];
      var t9 = '<b>사업체 10년.</b> ' + bz[0][0] + '년 ' + bz[0][1].toLocaleString() + '곳';
      if (!b20 && bz.length > 1) t9 += ' → ' + bL[0] + '년 ' + bL[1].toLocaleString() + '곳(' + sgn1(pc(bL[1] - bz[0][1], bz[0][1])) + '%) — ' + (+bz[0][0] < 2020 && +bL[0] >= 2020 ? '2019→2020년 조사 방식이 바뀌어 늘어 보인다(그 앞과 뒤를 견주지 않는다)' : '같은 조사 방식 안의 비교');
      if (b20) t9 += ' · 2020년 ' + b20[1].toLocaleString() + '곳 → ' + bL[0] + '년 ' + bL[1].toLocaleString() + '곳(' + sgn1(pc(bL[1] - b20[1], b20[1])) + '%) · 종사자 ' + (b20[2] || 0).toLocaleString() + ' → ' + (bL[2] || 0).toLocaleString() + '명(' + sgn1(pc((bL[2] || 0) - (b20[2] || 1), b20[2] || 1)) + '%). 2019→2020년에 크게 뛴 것은 통계청 조사 방식이 바뀐 탓이라 그 앞과 견주지 않는다';
      if (S.F.bzi && S.F.bzi.length) { var g3 = S.F.bzi.filter(function (x) { return x[1] > 20; }).map(function (x) { return [x[0], x[1], x[2], pc(x[2] - x[1], x[1])]; }).sort(function (a, b) { return b[3] - a[3]; });
        if (g3.length) t9 += '. ' + (S.F.bziy ? S.F.bziy[0] + '→' + S.F.bziy[1] + '년 ' : '') + '가장 많이 늘어난 업종: ' + g3.slice(0, 3).map(function (x) { return esc(x[0]) + ' ' + x[1] + '→' + x[2] + '(' + sgn1(x[3]) + '%)'; }).join(' · ') + (g3[g3.length - 1][3] < 0 ? ' / 줄어든 업종: ' + esc(g3[g3.length - 1][0]) + ' ' + sgn1(g3[g3.length - 1][3]) + '%' : ''); }
      t9 += '. <small>(통계청 전국사업체조사 · ' + esc((S.Fm && S.Fm.bzsrc) || 'KOSIS') + ')</small>'; P.push(t9); }
    if (!P.length) return '<p class="desc">이 동은 풀어 읽을 자료가 부족하다.</p>';
    var head = '<div class="story"><p class="sline"><b>한 줄로 — ' + esc(S.name) + ':</b> ' + esc(tags.filter(Boolean).join(' · ') || '자료가 적다') + '.</p>' + P.map(function (x) { return '<p>' + x + '</p>'; }).join('');
    head += '<p class="snot"><b>데이터가 말하지 않는 것.</b> ' + (S.sido === '경기' ? '경기는 동 단위 시간대·연령별 카드 매출과 서울식 생활인구가 공개되지 않아 서울 동보다 문단이 적다 · 경기 카드 매출은 경기데이터드림 가공 자료라 서울과 금액을 견주지 않는다 · ' : '카드 매출은 서울시 추정(현금·배달앱 일부 빠짐) · ') + '왜 늘고 줄었는지(원인)는 이 자료에 없다 — 전국 흐름·물가·상권 이동은 따로 확인해야 한다 · 생활인구는 체류 인원이지 방문자 수가 아니다 · 범죄·사고 건수는 이 문단에 넣지 않았다(관서 통계 층에서 본다). 문장 속 판단 기준(○배·±%p)은 앱이 정한 설계값이다.</p></div>';
    return head;
  }
  function josa(w, a, b) { var c = String(w || '').charCodeAt(String(w || '').length - 1); return c >= 0xAC00 && c <= 0xD7A3 && (c - 0xAC00) % 28 ? a : b; }
  function sl0(S) { return S.sales && S.sales.amt && S.pop && S.pop.tot && S.sales.amt / S.pop.tot < ((AREF && AREF.ref[S.sido] || {}).amtPerPopMed || 0); }
  function rw0(ref, S) { return ref.w && ref.w.mktc_med && S.W.apt[4] >= ref.w.mktc_med; }
  function storyText(el) { return el ? el.innerText : ''; }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-story]'); if (!b) return; var box = document.getElementById('storyBox'); if (!box || !sel || !sel.it || !sel.it.d) return;
    if (b.getAttribute('data-story') === 'copy') { if (navigator.clipboard) navigator.clipboard.writeText(storyText(box)).then(function () { b.textContent = '✅ 복사됨'; }); return; }
    box.innerHTML = '<p class="desc">자료를 모으는 중…</p>'; var d = sel.it.d;
    storyData(d).then(function (S) { if (!document.getElementById('storyBox')) return; document.getElementById('storyBox').innerHTML = storyHtml(S) + '<div class="lg-btns"><button data-story="copy">📋 이 글 복사</button></div>'; })
      .catch(function (er) { box.innerHTML = '<p class="desc">자료를 받지 못했다(' + esc(er && er.message || er) + ')</p>'; }); });
  function radOpen(c) {
    rentLoad(); sLoadIdx(); var el = $('m2dRad'); el.classList.add('on'); el.classList.remove('min'); document.body.classList.add('radon');
    $('m2dBiz') && $('m2dBiz').classList.remove('on'); document.body.classList.remove('bizon');
    if (c) { RAD.c = c; RAD.pick = false; RAD.follow = false; radRun(); } else { RAD.c = viewMid(); RAD.pick = false; RAD.follow = true; radRun(); }
  }
  function radClose() { var el = $('m2dRad'); if (el) el.classList.remove('on'); document.body.classList.remove('radon'); RAD.pick = false; draw(); }
  function radRun() {
    var c = RAD.c, r = RAD.r; RAD.busy = true; radPaint(); draw();
    var ll = [c[0] / KX + LON0, LAT0 - c[1] / KY], dl = r / KX * 1.1, dt = r / KY * 1.1, bx = [ll[0] - dl, ll[1] - dt, ll[0] + dl, ll[1] + dt];
    var gus = rIdx().filter(function (g) { var b = g.box; return !(b[2] < bx[0] || b[0] > bx[2] || b[3] < bx[1] || b[1] > bx[3]); });
    var jobs = [sLoadIdx(), rentLoad()];
    if (!STNS) jobs.push(fetch('data/r/stations.json').then(function (x) { return x.json(); }).then(function (j) { STNS = j.items.map(function (s2) { return { n: s2[0], l: s2[1], p: P(s2[2], s2[3]) }; }); }).catch(function () { STNS = []; }));
    gus.forEach(function (g) { jobs.push(sLoad(g.gu)); jobs.push(jgP(g.gu)); jobs.push(fLoad(g.gu)); if ((g.bytes || {}).ggtrd) jobs.push(gLoad(g.gu)); if ((g.bytes || {}).trdar) jobs.push(new Promise(function (res) { tLoad(g.gu, res); setTimeout(res, 20000); })); jobs.push(rLoadGu(g.gu)); if ((g.bytes || {}).transit) jobs.push(xLoad(g.gu)); if ((g.bytes || {}).safety) jobs.push(sfLoad(g.gu)); if ((g.bytes || {}).taas10) jobs.push(aLoad(g.gu)); if ((g.bytes || {}).live250) jobs.push(l2Load(g.gu)); if ((g.bytes || {}).rtms) jobs.push(rtLoad(g.gu)); });
    Promise.all(jobs).then(function () { RAD.gus = gus; RAD.res = radCalc(gus); RAD.res.grid = gridRad(RAD.c, RAD.r); RAD.busy = false; radPaint(); draw(); });
  }
  function radCalc(gus) {
    var c = RAD.c, r = RAD.r, r2 = r * r, o = { n: 0, byL: {}, byS: {}, comp: [], r: r, ym: '' }, CL = SIDX ? SIDX.cls : [];
    gus.forEach(function (g) { var S2 = SPTS[g.gu]; if (!S2 || !S2.a) return; o.ym = S2.ym || o.ym;
      S2.a.forEach(function (st) { var dx = (st.p[0] - c[0]) * kxAt(c[1]), dy = st.p[1] - c[1], d2 = dx * dx + dy * dy; if (d2 > r2) return; var C3 = CL[st.c] || ['', '?', '', '?', '?']; o.n++;
        o.byL[C3[1]] = (o.byL[C3[1]] || 0) + 1; o.byS[C3[4]] = (o.byS[C3[4]] || 0) + 1; if (RAD.ind && C3[4] === RAD.ind) o.comp.push({ s: st, d: Math.sqrt(d2) }); }); });
    o.comp.sort(function (a, b) { return a.d - b.d; });
    // 넓이 비율 — 반경 안 격자(한 변 r/16)
    var RKc = kxAt(c[1]), step = r / 16, cell = step * step, smp = [], dc = new Map(), tc = new Map(), gc = new Map(), AD = allDong(); for (var x = -r / RKc + step / RKc / 2; x < r / RKc; x += step / RKc) for (var y = -r + step / 2; y < r; y += step) if (x * x * RKc * RKc + y * y <= r2) smp.push([c[0] + x, c[1] + y]);
    smp.forEach(function (q) { var d = dongAtM(q); if (d) dc.set(d, (dc.get(d) || 0) + 1);
      for (var k2 = 0; k2 < GGT.length; k2++) { var Y = GGT[k2], b2 = trdBB(Y); if (q[0] < b2[0] || q[0] > b2[1] || q[1] < b2[2] || q[1] > b2[3]) continue; if (Y.rings.some(function (rr) { return inRing(rr, q[0], q[1]); })) gc.set(Y, (gc.get(Y) || 0) + 1); }
      for (var k = 0; k < TRD.length; k++) { var X = TRD[k], b = trdBB(X); if (q[0] < b[0] || q[0] > b[1] || q[1] < b[2] || q[1] > b[3]) continue; if (X.rings.some(function (rr) { return inRing(rr, q[0], q[1]); })) tc.set(X, (tc.get(X) || 0) + 1); } });
    var h = nowH(), dt2 = new Date(pickDate() + 'T00:00'), we = dt2.getDay() === 0 || dt2.getDay() === 6, key = we ? 'we' : 'wd';
    o.pop = 0; o.age = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]; o.live = []; for (var i = 0; i < 24; i++) o.live.push(0); o.dongs = [];
    dc.forEach(function (n, d) { if (d.area == null) d.area = polyA(d.polys); var w = Math.min(1, n * cell / (d.area || 1)); o.dongs.push([(d.gu ? d.gu + ' ' : '') + d.name, Math.round(w * 100)]);
      if (d.pop) { o.pop += d.pop.tot * w; d.pop.age.forEach(function (v, k) { o.age[k] += v * w; }); } var A = liveArr(d); if (A) A[key].forEach(function (v, k) { o.live[k] += v * w; }); });
    o.we = we; o.dongs.sort(function (a, b) { return b[1] - a[1]; });
    o.amt = 0; o.cnt = 0; o.tb = [0, 0, 0, 0, 0, 0]; o.ag = [0, 0, 0, 0, 0, 0]; o.ind = {}; o.bi = {}; o.flp = 0; o.wrc = 0; o.trd = [];
    tc.forEach(function (n, X) { var t = X.t, w = Math.min(1, n * cell / (t.area || 1)); o.trd.push([t.name, Math.round(w * 100)]);
      (t.ind || []).forEach(function (rr) { o.amt += rr[1] * w; o.cnt += rr[2] * w; for (var k = 0; k < 6; k++) { o.tb[k] += rr[3 + k] * w; o.ag[k] += rr[9 + k] * w; } o.ind[rr[0]] = (o.ind[rr[0]] || 0) + rr[1] * w;
        var B = o.bi[rr[0]] || (o.bi[rr[0]] = { amt: 0, cnt: 0, tb: [0, 0, 0, 0, 0, 0], ag: [0, 0, 0, 0, 0, 0], we: 0, st: 0, pa: 0, pa2: 0, ps: 0, op: 0, cl: 0 });
        B.amt += rr[1] * w; B.cnt += rr[2] * w; for (k = 0; k < 6; k++) { B.tb[k] += rr[3 + k] * w; B.ag[k] += rr[9 + k] * w; } B.we += (rr[22] + rr[23]) * w;
        var q = t.indp && t.indp[rr[0]]; if (q && q[0] > 0) { B.pa += q[0] * w; B.pa2 += rr[1] * w; } });
      (t.stor || []).forEach(function (st) { var B = o.bi[st[0]] || (o.bi[st[0]] = { amt: 0, cnt: 0, tb: [0, 0, 0, 0, 0, 0], ag: [0, 0, 0, 0, 0, 0], we: 0, st: 0, pa: 0, pa2: 0, ps: 0, op: 0, cl: 0 }); B.st += st[1] * w; B.op += st[3] * w; B.cl += st[4] * w; var ps = t.storp && t.storp[st[0]]; if (ps) B.ps += ps * w; });
      if (t.flp) o.flp += t.flp[0] / 91 * w; if (t.wrc) o.wrc += t.wrc[0] * w; });
    o.trd.sort(function (a, b) { return b[1] - a[1]; });
    o.gg = { amt: 0, cnt: 0, st: 0, list: [], ind: {}, q: '' };
    gc.forEach(function (n, Y) { var t = Y.t, w = Math.min(1, n * cell / (Y.area || 1)); o.gg.list.push([t.n, Math.round(w * 100), !!t.tot]); o.gg.st += (t.st || 0) * w; o.gg.q = Y.m.quarter;
      if (t.tot) { o.gg.amt += t.tot[0] * w; o.gg.cnt += t.tot[1] * w; (t.ind || []).forEach(function (rr) { o.gg.ind[rr[0]] = (o.gg.ind[rr[0]] || 0) + rr[1] * w; }); } });
    o.gg.list.sort(function (a, b) { return b[1] - a[1]; });
    o.stn = (STNS || []).map(function (s2) { return { s: s2, d: dTrue(s2.p, c) }; }).filter(function (q) { return q.d <= r; }).sort(function (a, b) { return a.d - b.d; });
    var seenN = {}; o.stn = o.stn.filter(function (q) { var k = seenN[q.s.n]; if (k) { if (k.ls.indexOf(q.s.l) < 0) k.ls.push(q.s.l); return false; } seenN[q.s.n] = { ls: [q.s.l] }; q.ls = seenN[q.s.n].ls; return true; });
    o.rent = rentNear(c, 1500);
    o.acc = { y: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dead: 0, ser: 0, ped: 0, night: 0, bike: 0, pm: 0, v: {} }; o.fat = [];
    A10.forEach(function (x) { if (dTrue(x.p, c) > r) return; var q = x.c; for (var k = 0; k < 10; k++) o.acc.y[k] += q[2 + k]; o.acc.dead += q[12]; o.acc.ser += q[13]; o.acc.ped += q[14]; o.acc.bike += q[15]; o.acc.pm += q[16]; o.acc.night += q[18]; var dv = (x.m || D.taas10 || {}).dic; var vn = dv && dv.v ? dv.v[q[23]] || q[23] : q[23]; o.acc.v[vn] = (o.acc.v[vn] || 0) + q[24]; });
    F10.forEach(function (x) { if (dTrue(x.p, c) <= r) o.fat.push(x); });
    o.cam = D.cam ? D.cam.items.filter(function (q) { var p2 = P(q.lon, q.lat); return dTrue(p2, c) <= r; }).length : 0;
    o.szn = D.sz ? D.sz.zones.filter(function (q) { var p2 = P(q.lon, q.lat); return dTrue(p2, c) <= r; }).length : 0;
    o.bus = { n: 0, on: [], off: [] }; o.sub = { n: 0, on: [], off: [], names: [] }; for (var hh2 = 0; hh2 < 24; hh2++) { o.bus.on.push(0); o.bus.off.push(0); o.sub.on.push(0); o.sub.off.push(0); }
    if (PUB) { PUB.bus.forEach(function (q) { var f = FLOW.bus[q.o.id]; if (!f || dTrue(q.p, c) > r) return; o.bus.n++; for (var k = 0; k < 24; k++) { o.bus.on[k] += f[0][k]; o.bus.off[k] += f[1][k]; } });
      PUB.subr.forEach(function (q) { var f = FLOW.sub[q.name]; if (!f || dTrue(q.p, c) > r) return; o.sub.n++; o.sub.names.push(q.name); for (var k = 0; k < 24; k++) { o.sub.on[k] += f[0][k]; o.sub.off[k] += f[1][k]; } }); }
    return o;
  }
  function radText() {   // 📋 복사 — 보고서 글
    var o = RAD.res, ll = [RAD.c[0] / KX + LON0, LAT0 - RAD.c[1] / KY]; if (!o) return '';
    var L = ['[반경 ' + o.r + 'm 상권 요약] 위도 ' + ll[1].toFixed(5) + ', 경도 ' + ll[0].toFixed(5),
      '점포 ' + o.n.toLocaleString() + '곳(' + (o.n / (Math.PI * o.r * o.r / 1e4)).toFixed(1) + '곳/ha) · ' + Object.keys(o.byL).sort(function (a, b) { return o.byL[b] - o.byL[a]; }).slice(0, 6).map(function (k) { return k + ' ' + o.byL[k]; }).join(' · '),
      RAD.ind ? '「' + RAD.ind + '」 ' + o.comp.length + '곳 · 가장 가까운 ' + (o.comp[0] ? Math.round(o.comp[0].d) + 'm' : '-') : '',
      '추정 카드 매출 한 달 약 ' + won(o.amt) + '(걸친 상권 ' + o.trd.length + '곳을 겹친 넓이 비율로)',
      o.gg && o.gg.amt ? '경기 상권 카드 매출 분기 약 ' + won(o.gg.amt) + '(걸친 경기 상권 ' + o.gg.list.length + '곳 · ' + o.gg.q.replace(' ', '년 ') + '분기)' : '',
      RAD.sind && o.bi[RAD.sind] && o.bi[RAD.sind].st >= 0.5 ? '「' + RAD.sind + '」 한 달 약 ' + won(o.bi[RAD.sind].amt) + ' · 점포 약 ' + Math.round(o.bi[RAD.sind].st) + '곳 · 점포당 약 ' + won(o.bi[RAD.sind].amt / o.bi[RAD.sind].st) : '',
      '생활인구 ' + nowH() + '시 약 ' + Math.round(o.live[nowH()]).toLocaleString() + '명 · 주민 약 ' + Math.round(o.pop).toLocaleString() + '명 · 하루 유동 약 ' + Math.round(o.flp).toLocaleString() + ' · 직장 약 ' + Math.round(o.wrc).toLocaleString(),
      o.stn.length ? '지하철역 ' + o.stn.map(function (q) { return q.s.n + ' ' + Math.round(q.d) + 'm'; }).join(' · ') : '반경 안 지하철역 없음',
      o.acc && o.acc.y.some(function (v) { return v; }) ? '교통사고 10년 ' + o.acc.y.reduce(function (a, b) { return a + b; }, 0).toLocaleString() + '건 · 사망 ' + o.acc.dead + '명 · 보행자 피해 ' + o.acc.ped : '',
      o.bus.n ? '버스 정류장 ' + o.bus.n + '곳 하루 승차 ' + o.bus.on.reduce(function (a, b) { return a + b; }, 0).toLocaleString() + ' · 하차 ' + o.bus.off.reduce(function (a, b) { return a + b; }, 0).toLocaleString() : '',
      o.rent ? '임대료(부동산원 표본 ' + o.rent.it.name + ' ' + o.rent.d + 'm) 소규모 ' + lastV(o.rent.it.s) + ' · 중대형 ' + lastV(o.rent.it.m) + '천원/㎡' : '',
      '출처: 소상공인 상가정보(' + o.ym + ') · 서울시 상권분석서비스 · 서울 생활인구 · 행안부 주민등록 · 한국부동산원 임대동향 — 추정·근사 포함'];
    return L.filter(Boolean).join('\n');
  }
  function radPaint() {
    var el = $('m2dRad'); if (!el || !el.classList.contains('on')) return; var o = RAD.res, h = '<div class="lg-h"><b>📐 반경 분석</b><span><button data-rx="min">▾ 접기</button> <button data-rx="x">닫기</button></span></div>';
    h += '<div class="lg-btns">' + [300, 500, 1000].map(function (r) { return '<button data-rr="' + r + '" class="' + (RAD.r === r ? 'on' : '') + '">반경 ' + (r >= 1000 ? r / 1000 + 'km' : r + 'm') + '</button>'; }).join('') +
      '<button data-rx="follow" class="' + (RAD.follow ? 'on' : '') + '">🧭 지도 따라가기' + (RAD.follow ? ' 켜짐' : '') + '</button><button data-rx="pick" class="' + (RAD.pick ? 'on' : '') + '">📍 지도에서 자리 고르기</button>' + (REP ? '<button data-rx="rep">' + (REP.here ? '📍 지금 위치' : '📋 보고 자리') + '</button>' : '') + '</div>';
    if (SIDX) { var grp = {}; SIDX.cls.forEach(function (C3) { (grp[C3[1]] = grp[C3[1]] || []).push(C3[4]); });
      h += '<div class="bizrow"><label>경쟁 업종 <select data-rz="ind"><option value="">(고르지 않음)</option>' + Object.keys(grp).map(function (g) { return '<optgroup label="' + esc(g) + '">' + grp[g].sort().map(function (n) { return '<option' + (n === RAD.ind ? ' selected' : '') + '>' + esc(n) + '</option>'; }).join('') + '</optgroup>'; }).join('') + '</select></label></div>'; }
    if (RAD.pick) h += '<p class="lg-n"><b>지도를 눌러 분석할 자리를 고르세요.</b></p>';
    else if (RAD.follow) h += '<p class="lg-n">🧭 <b>지금 보는 지도 가운데</b>를 분석한다 — 지도를 옮기고 손을 떼면 그 자리로 다시 센다. 반경 안 점포 분포는 지도에 색 칸으로(진할수록 많음 · 빨간 점 = 고른 경쟁 업종).</p>';
    if (RAD.busy) h += '<p class="lg-n">반경 안 자료를 모으는 중…</p>';
    else if (o && RAD.c) {
      var ha = Math.PI * o.r * o.r / 1e4, Lk = Object.keys(o.byL).sort(function (a, b) { return o.byL[b] - o.byL[a]; }), Sk = Object.keys(o.byS).sort(function (a, b) { return o.byS[b] - o.byS[a]; }).slice(0, 12);
      h += '<div class="rcard">' + row('점포', o.n.toLocaleString() + '곳 · ' + (o.n / ha).toFixed(1) + '곳/ha <em>(반경 넓이 ' + ha.toFixed(1) + 'ha · 등록 상가 ' + o.ym + ')</em>');
      h += '<div class="cap">업종 대분류별 점포 수(곳 · 반경 안 등록 상가)</div>' + bar(Lk.map(function (k) { return o.byL[k]; }), '#475569', Lk.map(function (k) { return ({ '과학·기술': '전문', '시설관리·임대': '시설', '수리·개인': '수리', '예술·스포츠': '예체', '보건의료': '의료' })[k] || k.slice(0, 3); })) + '<p class="lg-n">' + Lk.map(function (k) { return esc(k) + ' ' + o.byL[k]; }).join(' · ') + '</p>';
      h += row('많은 업종', Sk.map(function (k) { return esc(k) + ' ' + o.byS[k]; }).join(' · '));
      if (RAD.ind) { var cp = o.comp; h += row('경쟁점 「' + esc(RAD.ind) + '」', cp.length + '곳' + (cp.length ? ' · 가장 가까운 곳 ' + Math.round(cp[0].d) + 'm · ' + (cp.length / ha).toFixed(2) + '곳/ha' : ' — 반경 안에 없음'));
        if (cp.length) h += '<ol class="comp">' + cp.slice(0, 25).map(function (q) { return '<li>' + esc(q.s.n) + ' <small>' + (q.s.f ? q.s.f + '층 · ' : '') + Math.round(q.d) + 'm</small></li>'; }).join('') + '</ol>' + (cp.length > 25 ? '<p class="lg-n">… 외 ' + (cp.length - 25) + '곳(지도에 빨간 점)</p>' : ''); }
      h += row('추정 카드 매출', o.trd.length ? '한 달 약 ' + won(o.amt) + ' · 결제 약 ' + man(o.cnt) + '건 <em>(걸친 상권 ' + o.trd.length + '곳 × 겹친 넓이 비율 — 상권 밖 점포 매출은 빠진다)</em>' : o.gg && o.gg.list.length ? '<em>서울 상권 없음 — 아래 경기 상권</em>' : '<em>반경에 걸친 상권이 없다(주거지 등)</em>');
      if (o.gg && o.gg.list.length) { var GI = Object.keys(o.gg.ind).sort(function (a, b) { return o.gg.ind[b] - o.gg.ind[a]; });
        h += row('경기 상권 매출', (o.gg.amt ? '<b>분기 약 ' + won(o.gg.amt) + '</b> · 결제 약 ' + man(o.gg.cnt) + '건 · ' : '') + '점포 약 ' + Math.round(o.gg.st) + '곳 <em>(걸친 경기 상권 ' + o.gg.list.length + '곳 × 겹친 넓이 비율 · ' + esc(o.gg.q.replace(' ', '년 ')) + '분기 · 경기데이터드림)</em>') +
          (GI.length ? row('경기 매출 많은 업종', GI.slice(0, 5).map(function (k) { return esc(k) + ' ' + won(o.gg.ind[k]); }).join(' · ')) : '') +
          row('걸친 경기 상권', o.gg.list.slice(0, 6).map(function (d) { return esc(d[0]) + ' ' + d[1] + '%' + (d[2] ? '' : '(매출 없음)'); }).join(' · ')); }
      if (o.amt) { var ik = Object.keys(o.ind).sort(function (a, b) { return o.ind[b] - o.ind[a]; }).slice(0, 8);
        h += '<div class="cap">시간대별 시간당 카드 매출(원 · 하루 평균 · 반경 추정)</div>' + bar(o.tb.map(function (v, i) { return v / TBH[i] / 30.4; }), '#7c3aed', LB_TB6, 'w');
        h += '<div class="cap">연령대별 카드 매출(원 · 한 달 · 반경 추정)</div>' + bar(o.ag, '#a78bfa', LB_AGE6, 'w');
        h += row('매출 많은 업종', ik.map(function (k) { return esc(k) + ' ' + won(o.ind[k]); }).join(' · '));
        var bk = Object.keys(o.bi).filter(function (k) { return o.bi[k].amt > 0; }).sort(function (a, b) { return o.bi[b].amt - o.bi[a].amt; });
        h += '<div class="bizrow"><label>💰 예상 매출 볼 업종 <select data-rz="sind"><option value="">(고르기 — 상권분석 업종)</option>' + bk.map(function (k) { return '<option' + (k === RAD.sind ? ' selected' : '') + '>' + esc(k) + '</option>'; }).join('') + '</select></label></div>';
        var B = RAD.sind && o.bi[RAD.sind];
        if (B) { var per = B.st >= 0.5 ? B.amt / B.st : null, pk = 0; for (var i2 = 1; i2 < 6; i2++) if (B.tb[i2] > B.tb[pk]) pk = i2; var agt = B.ag.reduce(function (a, b) { return a + b; }, 0);
          var yy = B.pa > 0 ? (B.pa2 - B.pa) / B.pa : null, rn = o.rent && (lastV(o.rent.it.s) || lastV(o.rent.it.m));
          h += '<div class="bizwhy"><b>💰 「' + esc(RAD.sind) + '」 이 반경에서</b><br>' +
            '한 달 매출 약 ' + won(B.amt) + ' · 결제 약 ' + man(B.cnt) + '건 · 점포 약 ' + Math.round(B.st) + '곳' + (B.op || B.cl ? ' (분기 개업 ' + Math.round(B.op) + ' · 폐업 ' + Math.round(B.cl) + ')' : '') +
            (per ? '<br><b>점포당 한 달 평균 매출 약 ' + won(per) + '</b>' : '<br><em>점포 수가 적어 점포당 값을 내지 않는다</em>') +
            (yy != null ? ' · 1년 전 같은 분기보다 ' + (yy >= 0 ? '+' : '') + Math.round(yy * 100) + '%' : '') +
            '<br>객단가 ' + (B.cnt ? Math.round(B.amt * 1e4 / B.cnt).toLocaleString() + '원' : '-') + ' · 피크 ' + TBL[pk] + '시 · 20·30대 ' + pct(B.ag[1] + B.ag[2], agt) + '% · 50대 이상 ' + pct(B.ag[4] + B.ag[5], agt) + '% · 주말 ' + pct(B.we, B.amt) + '%' +
            (per && rn ? '<br>임대료 견주기: 33㎡(10평) 월 약 ' + Math.round(rn * 3.3) + '만원 ÷ 점포당 매출 = 매출의 약 ' + Math.round(rn * 3.3 / per * 100) + '% <em>(가까운 표본 임대료 · 점포 넓이를 10평으로 친 어림)</em>' : '') +
            '</div><div class="cap">「' + esc(RAD.sind) + '」 시간대별 시간당 카드 매출(원 · 하루 평균 · 반경 추정)</div>' + bar(B.tb.map(function (v, i) { return v / TBH[i] / 30.4; }), '#7c3aed', LB_TB6, 'w') +
            '<div class="cap">「' + esc(RAD.sind) + '」 연령대별 카드 매출(원 · 한 달 · 반경 추정)</div>' + bar(B.ag, '#a78bfa', LB_AGE6, 'w') +
            '<p class="lg-n">예상 매출 = 반경에 걸친 상권의 그 업종 카드 매출 × 겹친 넓이 비율 ÷ 같은 방식으로 센 점포 수(서울시 상권분석서비스 추정 · 현금 제외 · 상권 밖 점포는 빠짐). 실제 한 점포의 매출이 아니라 평균이다.</p>'; }
      }
      var J0 = jgAround(RAD.c, RAD.r); h += talk({ sido: sidoOf(RAD.gus && RAD.gus[0] && RAD.gus[0].gu), pop: J0.pop || o.pop, wrk: J0.pop ? J0.wrk : null, corp: J0.corp, gov: govAround(RAD.c, RAD.r), age: o.age, live: o.we ? null : { wd: o.grid && o.grid.l ? o.grid.l.wd : o.live }, tb: o.tb, ag: o.ag });
      var GL = o.grid && o.grid.l;   // v2.5.0 서울은 250m 칸 합(같은 서울시 생활인구 · 칸 가운데가 반경 안) — 없으면 종전 「걸친 동 × 넓이 비율」
      if (GL) { var ga = o.we ? GL.we : GL.wd; h += row('생활인구 지금', ga[nowH()].toLocaleString() + '명 <em>(' + (o.we ? '주말' : '평일') + ' ' + nowH() + '시 · 250m 칸 ' + o.grid.n + '개 합 · 2026-09-07~13 한 주)</em>') + '<div class="cap">시간대별 생활인구(명 · 반경 안 250m 칸 합 · 0~23시 ' + (o.we ? '주말' : '평일') + ' 평균)</div>' + bar(ga, '#7c3aed', LB_H24); }
      else { h += row('생활인구 지금', Math.round(o.live[nowH()]).toLocaleString() + '명 <em>(' + (o.we ? '주말' : '평일') + ' ' + nowH() + '시 · 걸친 동 × 넓이 비율)</em>');
      h += '<div class="cap">시간대별 생활인구(명 · 반경 안 추정 · 0~23시 ' + (o.we ? '주말' : '평일') + ' 평균)</div>' + bar(o.live.map(Math.round), '#f97316'); }
      h += row('주민', '약 ' + Math.round(o.pop).toLocaleString() + '명 · 19세 이하 ' + pct(o.age[0] + o.age[1], o.pop) + '% · 20·30대 ' + pct(o.age[2] + o.age[3], o.pop) + '% · 60세 이상 ' + pct(o.age[6] + o.age[7] + o.age[8] + o.age[9], o.pop) + '%');
      h += '<div class="cap">주민 연령대별 인구(명 · 반경 안 추정 · 0~9세 … 90~99세)</div>' + bar(o.age.map(Math.round), '#8b5cf6', ageLab(10));
      h += row('유동·직장', '하루 유동 약 ' + man(o.flp) + '명 · 직장인구 약 ' + man(o.wrc) + '명 <em>(걸친 상권 기준)</em>');
      var sumA = function (a) { return a.reduce(function (x, y) { return x + y; }, 0); };
      if (o.bus.n) h += row('버스 승하차', '정류장 ' + o.bus.n + '곳 · 하루 승차 ' + man(sumA(o.bus.on)) + ' · 하차 ' + man(sumA(o.bus.off)) + ' <em>(2026년 6월 하루 평균)</em>') + '<div class="cap">시간대별 버스 승차(파랑) · 하차(주황) 인원(명/시 · 반경 안 정류장 합 · 하루 평균)</div>' + bar2(o.bus.on, o.bus.off);
      if (o.sub.n) h += row('지하철 승하차', esc(o.sub.names.join('·')) + ' · 하루 승차 ' + man(sumA(o.sub.on)) + ' · 하차 ' + man(sumA(o.sub.off))) + '<div class="cap">시간대별 지하철 승차(파랑) · 하차(주황) 인원(명/시 · 반경 안 역 합 · 하루 평균)</div>' + bar2(o.sub.on, o.sub.off);
      var at = o.acc.y.reduce(function (a, b) { return a + b; }, 0);
      if (at) { var vk = Object.keys(o.acc.v).sort(function (a, b) { return o.acc.v[b] - o.acc.v[a]; }).slice(0, 3);
        h += row('교통사고 10년', at.toLocaleString() + '건(2016~2025) · 사망 ' + o.acc.dead + '명(사망사고 ' + o.fat.length + '건) · 중상 ' + o.acc.ser + ' · 보행자 피해 ' + o.acc.ped + ' · 밤(20~6시) ' + pct(o.acc.night, at) + '%') +
          row('주 법규위반', vk.map(function (k) { return esc(k) + ' ' + o.acc.v[k]; }).join(' · ') + ' <em>(100m 칸마다 가장 많은 위반의 합 — 근사)</em>') +
          '<div class="cap">해마다 교통사고 건수(건 · 2016~2025 · 반경 안 100m 칸 합 · TAAS)</div>' + bar(o.acc.y, '#ea580c', LB_Y16); }
      if (o.grid) h += gridRadRows({ l: null, n: o.grid.n, rt: o.grid.rt });
      h += row('안전', '무인 단속 카메라 ' + o.cam + '대 · 어린이보호구역 대상 시설 ' + o.szn + '곳');
      h += row('지하철역', o.stn.length ? o.stn.map(function (q) { return esc(q.s.n) + ' <small>' + esc(q.ls.join('·')) + ' · ' + Math.round(q.d) + 'm</small>'; }).join(' · ') : '반경 안에 없음');
      h += rentRows(RAD.c, '임대료(가까운 표본)');
      h += row('걸친 동', o.dongs.slice(0, 6).map(function (d) { return esc(d[0]) + ' ' + d[1] + '%'; }).join(' · ') + ' <em>(동 넓이 중 반경 안 비율)</em>');
      if (o.trd.length) h += row('걸친 상권', o.trd.slice(0, 6).map(function (d) { return esc(d[0]) + ' ' + d[1] + '%'; }).join(' · '));
      h += '<div class="lg-btns"><button data-rx="pnl">💰 이 자리 손익 계산</button><button data-rx="copy">📋 요약 복사</button><button data-rx="biz">🏪 이 업종 서울 다른 자리</button></div></div>';
      h += '<small class="lg-n">넓이 비율은 반경 안을 격자로 찍어 센 근사다. 추정 매출은 카드 결제 기반(현금 제외) · 상권 밖 점포 매출은 빠진다. 임대료는 1.5km 안 부동산원 표본 상권 평균이다. 점포는 등록 정보라 문 닫은 곳이 섞일 수 있다. <b>한 점포 실제 매출·권리금·50m 단위 유동은 공공 자료에 없다.</b></small>';
    }
    el.innerHTML = h;
  }
  function drawRad(dark) {
    if (!document.body.classList.contains('radon') || !RAD.c) return; var c = S(RAD.c), rr = RAD.r * view.s;
    ctx.beginPath(); ctx.ellipse(c[0], c[1], rr / kxAt(RAD.c[1]), rr, 0, 0, Math.PI * 2); ctx.fillStyle = 'rgba(14,165,233,.06)'; ctx.fill(); ctx.lineWidth = 2.5; ctx.setLineDash([8, 5]); ctx.strokeStyle = '#0284c7'; ctx.stroke(); ctx.setLineDash([]);
    ctx.beginPath(); ctx.arc(c[0], c[1], 6, 0, Math.PI * 2); ctx.fillStyle = '#0284c7'; ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = '#fff'; ctx.stroke();
    var o = RAD.res; if (!o || RAD.busy || !SIDX) return; var r2 = RAD.r * RAD.r, CL = SIDX.cls, pal = { '음식': '#ea580c', '소매': '#2563eb', '과학·기술': '#0d9488', '시설관리·임대': '#64748b', '교육': '#16a34a', '보건의료': '#dc2626', '수리·개인': '#9333ea', '예술·스포츠': '#db2777', '숙박': '#a16207', '부동산': '#475569' };
    if (!RAD.heat || RAD.heat.k !== RAD.c[0] + '|' + RAD.c[1] + '|' + RAD.r + '|' + RAD.ind + '|' + (RAD.gus || []).length) {   // 칸 = 반경/12 m
      var cs = RAD.r / 12, cells = {}, mxc = 0; (RAD.gus || []).forEach(function (g) { var S2 = SPTS[g.gu]; if (!S2 || !S2.a) return; S2.a.forEach(function (st) { var dx = (st.p[0] - RAD.c[0]) * kxAt(RAD.c[1]), dy = st.p[1] - RAD.c[1]; if (dx * dx + dy * dy > r2) return;
        var kk = Math.floor(dx / cs) + ',' + Math.floor(dy / cs), C4 = CL[st.c] || [], e = cells[kk] || (cells[kk] = [0, 0]); e[0]++; if (RAD.ind && C4[4] === RAD.ind) e[1]++; mxc = Math.max(mxc, e[0]); }); });
      RAD.heat = { k: RAD.c[0] + '|' + RAD.c[1] + '|' + RAD.r + '|' + RAD.ind + '|' + (RAD.gus || []).length, cs: cs, cells: cells, mx: mxc || 1 }; }
    var HT = RAD.heat, csz = HT.cs * view.s; Object.keys(HT.cells).forEach(function (kk) { var e = HT.cells[kk], ij = kk.split(','), x0 = RAD.c[0] + (+ij[0]) * HT.cs, y0 = RAD.c[1] + (+ij[1]) * HT.cs, s0 = S([x0, y0]);
      ctx.fillStyle = 'rgba(2,132,199,' + (0.08 + 0.55 * Math.sqrt(e[0] / HT.mx)).toFixed(2) + ')'; ctx.fillRect(s0[0], s0[1], csz + 0.5, csz + 0.5);
      if (e[1]) { ctx.fillStyle = 'rgba(220,38,38,' + Math.min(0.85, 0.3 + 0.15 * e[1]).toFixed(2) + ')'; ctx.beginPath(); ctx.arc(s0[0] + csz / 2, s0[1] + csz / 2, Math.max(3, Math.min(csz / 2, 3 + e[1] * 1.5)), 0, Math.PI * 2); ctx.fill(); }
      if (csz > 26) { ctx.fillStyle = dark ? '#e0f2fe' : '#0c4a6e'; ctx.font = '10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(e[1] ? e[0] + '·' + e[1] : String(e[0]), s0[0] + csz / 2, s0[1] + csz / 2); } });
    if (view.s > 0.3) (RAD.gus || []).forEach(function (g) { var S2 = SPTS[g.gu]; if (!S2 || !S2.a) return; S2.a.forEach(function (st) { var dx = (st.p[0] - RAD.c[0]) * kxAt(RAD.c[1]), dy = st.p[1] - RAD.c[1]; if (dx * dx + dy * dy > r2) return; var C3 = CL[st.c] || []; if (RAD.ind && C3[4] === RAD.ind) return; var s3 = S(st.p); ctx.fillStyle = pal[C3[1]] || '#94a3b8'; ctx.globalAlpha = 0.55; ctx.fillRect(s3[0] - 1.5, s3[1] - 1.5, 3, 3); ctx.globalAlpha = 1; }); });
    o.comp.forEach(function (q) { dot(q.s.p, 5, '#dc2626', '#fff', { kind: 'store', s: q.s }); });
  }
  // ---------- v2.10.0 🤖 AI용 지역 프로필(profile.json) — 동 하나 + 시군구 요약을 AI 에 붙여 넣을 글로 ----------
  var AIP = {}, AICUR = null;
  function aiText(j, k) {
    var G = j.gu_summary || {}, d = k === '*' ? null : j.dong[k], nm = (G['시도'] || '') + ' ' + (G['이름'] || j.name || '') + (d ? ' ' + d['이름'] : ' 전체(행정동 ' + Object.keys(j.dong).length + '곳)');
    var body = d ? { '행정동': d, '시군구 요약': G } : { '시군구 요약': G, '행정동': j.dong };
    return '[데이터 압축지도 — 지역 기본 자료 · AI 분석용]\n지역: ' + nm + (d ? ' (행정동 코드 ' + k + ')' : '') + ' · 묶은 날 ' + j.built + '\n읽는 법: ' + j.how_to_read + '\n주의: ' + j.caution + '\n출처: ' + Object.keys(j.sources).map(function (q) { return q + ' = ' + j.sources[q]; }).join(' / ') +
      '\n요청 예: 이 지역의 인구 구성(나이·성별) · 머무는 사람과 사는 사람의 차이 · 이동(출근·퇴근 방향) · 소비(시간대·연령·업종) · 가게 구성 · 집값 · 사고 위험을 요약하고, 근거 숫자를 함께 대 줘. 「추정」·「근사」 값은 그렇게 밝히고, 자료에 없는 것은 없다고 말해 줘.\n\n```json\n' + JSON.stringify(body) + '\n```\n';
  }
  function aiCard(it) {
    if (it.u) { var tu = unitText(it.u); return '<h3>🤖 AI용 지역 자료 — ' + esc(unitTitle(it.u)) + '</h3><p class="desc">이 단위에 든 행정동 자료를 한 덩어리로 묶었다(합계 + 동마다). 복사해서 AI 에 붙여 넣는다. 개인정보는 없다.</p><div class="lg-btns"><button data-aicopy="1">📋 복사 (' + Math.round(tu.length / 1000) + '천 자)</button></div><textarea class="aitx" readonly rows="9" style="width:100%;font:11px/1.4 ui-monospace,monospace;box-sizing:border-box">' + esc(tu) + '</textarea>'; }
    var j = AIP[it.gu]; AICUR = it; var again = function () { var c = $('m2dCard'); if (AICUR === it && c && c.classList.contains('on') && c.querySelector('[data-aiwait]')) show(it); };
    if (!j) { rGet(it.gu, 'profile.json').then(function (x) { AIP[it.gu] = x; again(); }).catch(function () { AIP[it.gu] = { none: 1 }; again(); });
      return '<h3>🤖 AI용 지역 자료</h3><p class="desc" data-aiwait="1">자료를 받는 중…</p>'; }
    if (j.none || (it.k !== '*' && !j.dong[it.k])) return '<h3>🤖 AI용 지역 자료</h3><p class="desc">이 동은 아직 프로필이 없다(새로 생긴 동이거나 받지 못함).</p>';
    var t = aiText(j, it.k), d = j.dong[it.k];
    return '<h3>🤖 AI용 지역 자료 — ' + esc(d ? d['이름'] : (j.name || '') + ' 전체') + '</h3><p class="desc">이 지도에 구운 기본 자료(인구 구성·머무는 사람·이동·카드 소비·가게·집값·사고·시설·관할)를 한 덩어리 글로 묶었다. 복사해서 ChatGPT·Claude 같은 AI 에 붙여 넣으면 그 지역을 빨리 파악한다. 개인정보는 없다.</p>' +
      '<div class="lg-btns"><button data-aicopy="1">📋 복사 (' + Math.round(t.length / 1000) + '천 자)</button>' + (d ? '<button data-ai="' + esc(it.gu) + '|*">🏙 이 시군구 전체 동</button>' : '') + '</div>' +
      '<textarea class="aitx" readonly rows="9" style="width:100%;font:11px/1.4 ui-monospace,monospace;box-sizing:border-box">' + esc(t) + '</textarea>' +
      '<p class="desc">같은 자료가 파일로도 있다 — 권역 저장소의 <code>r/' + esc(it.gu) + '/profile.json</code> · 찾는 법은 <code>data/ai.json</code>.</p>';
  }
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-ai]'); if (b) { var a = b.getAttribute('data-ai').split('|'); show({ kind: 'ai', gu: a[0], k: a[1] }); return; }
    var c = e.target.closest('[data-aicopy]'); if (!c) return; var ta = document.querySelector('textarea.aitx'); if (!ta) return;
    var done = function () { c.textContent = '✅ 복사됨'; };
    try { if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(ta.value).then(done, function () { ta.select(); try { document.execCommand('copy'); done(); } catch (e3) {} }); else { ta.select(); document.execCommand('copy'); done(); } } catch (e2) { ta.select(); } });
  document.addEventListener('click', function (e) { var bf = e.target.closest('[data-frn]'); if (bf) { show({ kind: 'frn', gu: bf.getAttribute('data-frn') }); return; } });
  document.addEventListener('click', function (e) { var b = e.target.closest('[data-radhere]'); if (!b) return; var a = b.getAttribute('data-radhere').split(','); var q = P(+a[0], +a[1]); view.cx = q[0]; view.cy = q[1]; view.s = Math.max(view.s, 0.25); radOpen(q); });
  if ($('m2dRad')) {
    $('m2dRad').addEventListener('click', function (e) { var b = e.target.closest('[data-rx],[data-rr]'); if (!b) { if ($('m2dRad').classList.contains('min')) $('m2dRad').classList.remove('min'); return; }
      var x = b.getAttribute('data-rx'), rr = b.getAttribute('data-rr');
      if (rr) { RAD.r = +rr; if (RAD.c) radRun(); else radPaint(); return; }
      if (x === 'pnl') { pnlOpen(RAD.c); return; } if (x === 'x') return radClose(); if (x === 'min') { e.stopPropagation(); $('m2dRad').classList.toggle('min'); return; }
      if (x === 'pick') { RAD.pick = !RAD.pick; if (RAD.pick) RAD.follow = false; radPaint(); return; }
      if (x === 'follow') { RAD.follow = !RAD.follow; if (RAD.follow) { RAD.pick = false; RAD.c = viewMid(); radRun(); } else radPaint(); return; }
      if (x === 'rep' && REP) { RAD.c = REP.p; radRun(); return; }
      if (x === 'copy') { var t = radText(); try { navigator.clipboard.writeText(t).then(function () { b.textContent = '✅ 복사했다'; }); } catch (e2) { prompt('복사', t); } return; }
      if (x === 'biz') { bizOpen(); return; } });
    $('m2dRad').addEventListener('change', function (e) { var t = e.target; if (t.getAttribute('data-rz') === 'sind') { RAD.sind = t.value; radPaint(); return; } if (t.getAttribute('data-rz') === 'ind') { RAD.ind = t.value; if (RAD.c && RAD.res) { RAD.res = radCalc(RAD.gus || []); radPaint(); draw(); } } });
  }
  // 시계(행사·집회·신호·교통량이 「지금」을 본다)
  function clock() { var d = new Date(); $('m2dNow').textContent = (d.getMonth() + 1) + '월 ' + d.getDate() + '일(' + '일월화수목금토'[d.getDay()] + ') ' + ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2); }
  clock(); setInterval(function () { clock(); if (HOUR == null) { summary(); } }, 30000);
  function ymdOf(d) { return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2); }
  function pickDate() { var v = $('m2dDate') && $('m2dDate').value; return v || ymdOf(new Date()); }
  if ($('m2dDate')) { $('m2dDate').value = ymdOf(new Date()); $('m2dDate').addEventListener('change', function () { var wasSea = $('m2dPre') && $('m2dPre').querySelector('[data-p="season"].on'); sel = null; show(null); paintPre(); if (wasSea) preset('season'); draw(); paintTime(); summary(); }); }
  // v0.10.85 날짜를 바꾸면 계절 단추도 따라 바뀌고, 계절 단추가 켜져 있었으면 새 계절 층으로







  // ---------- v2.30.0 🔢 도로 번호 → 위치(코워크 지시 2026-10-06) — data/road-posts.json(tools/region/roadpost-bake.py) ----------
  //  가로등주 관리번호 「접두_구간-순번」 · 찾기 칸에서 번호로 가기 · 길게 누르기(PC 오른쪽 클릭) = 가장 가까운 번호 · 접두 뜻(올=올림픽대로 …)은 추정
  var RP = null, RPP = null, RPIX = null, RPLP = { t: 0, fired: false, x: 0, y: 0 };
  var RPALIAS = [[/^올림픽(대로)?/, '올'], [/^강변(북로)?/, '강'], [/^동부(간선(도로)?)?/, '동'], [/^내부(순환(로)?)?/, '내'], [/^북부(간선(도로)?)?/, '북부']];
  function rpKey(t) { t = String(t || '').replace(/\s+/g, ' ').trim(); RPALIAS.forEach(function (a) { t = t.replace(a[0], a[1]); });
    var m = /^(.*?)[\s_]*(\d+)\s*-\s*(\d+)$/.exec(t) || /^(.*?)[\s_]+(\d+)\s+(\d+)$/.exec(t); if (m) return m[1].replace(/[\s_-]+$/, '').replace(/\s+/g, '') + '|' + (+m[2]) + '|' + (+m[3]);
    var m2 = /^(.*?)[\s_-]*(\d+)$/.exec(t); return m2 ? m2[1].replace(/[\s_-]+$/, '').replace(/\s+/g, '') + '|' + (+m2[2]) : t.replace(/\s+/g, ''); }
  function rpLoad() { if (RPP) return RPP; RPP = fetch('data/road-posts.json').then(function (r) { return r.json(); }).then(function (j) { RP = j; RPIX = {};
      Object.keys(j.sets).forEach(function (sk) { j.sets[sk].items.forEach(function (it) { it.p = sk === 'exkm' ? P(it[3], it[2]) : P(it[2], it[1]); it.sk = sk; if (sk === 'lamp') RPIX[rpKey(it[0])] = it; }); }); draw(); return j; }).catch(function () { RPP = null; return null; }); return RPP; }
  function exNm(it) { var R0 = RP.sets.exkm.routes[it[0]]; return R0 ? R0[1] : ''; }
  function exKm(it) { return (+it[1]).toFixed(1); }
  function rpRoad(id) { var L = RP && RP.sets.lamp; if (!L) return ''; var pre = String(id).split('_')[0]; return L.prefix && L.prefix[pre] ? L.prefix[pre] + ' <em>(접두로 본 추정)</em>' : esc(String(id).replace(/[-_]?\d+(-\d+)?$/, '')); }
  function rpGo(it) { view.cx = it.p[0]; view.cy = it.p[1]; view.s = Math.max(view.s, 0.6); if (!on.rpost) { on.rpost = true; saveOn(); paintLayers(); } draw(); var sx = S(it.p); TAPM = it.p; sel = { x: sx[0], y: sx[1], r: 8, it: { kind: 'rpost', r: it } }; show(sel.it); draw(); }
  function exFind(q) {
    var m = /^(.+?)\s*(\d+(?:\.\d+)?)\s*(?:km|키로|k)?$/i.exec(String(q).trim()); if (!m) return null; var nm = m[1].replace(/\s+/g, '').replace(/고속도로$|고속$/, ''), km = +m[2]; if (!nm || /\d$/.test(nm)) return null;
    var R = RP.sets.exkm.routes, cand = []; R.forEach(function (r, i) { var a = r[1].replace(/\s+/g, ''); if (a.indexOf(nm) === 0 || a.replace(/선/, '').indexOf(nm.replace(/선$/, '')) === 0) cand.push(i); }); if (!cand.length) return null;
    var best = null, bd = 1e9; RP.sets.exkm.items.forEach(function (it) { if (cand.indexOf(it[0]) < 0) return; var d = Math.abs(it[1] - km); if (d < bd) { bd = d; best = it; } }); return best ? [best, bd] : null; }
  function rpFind(q, inp) {
    if (/\d/.test(q) && /[가-힣]/.test(q) && (RP ? RP.sets.exkm : true)) { if (!RP) { $('m2dFindMsg').textContent = '도로 번호 목록을 받는 중…'; rpLoad().then(function (j) { if (j) inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); }); return true; }
      var ex = exFind(q); if (ex) { $('m2dFindMsg').textContent = ex[1] > 0.05 ? '「' + q + '」 가장 가까운 거리표 ' + exNm(ex[0]) + ' ' + exKm(ex[0]) + 'km' : ''; rpGo(ex[0]); return true; } }
    var k = rpKey(q), kk0 = k.split('|'); if (kk0.length < 2 || !kk0[0]) return false;
    if (!RP) { $('m2dFindMsg').textContent = '도로 번호 목록을 받는 중…'; rpLoad().then(function (j) { if (j) inp.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' })); }); return true; }
    var it = RPIX[k];
    if (!it) { var kk = k.split('|'), cand = RP.sets.lamp.items.filter(function (x) { var y = rpKey(x[0]).split('|'); return y[0] === kk[0] && y[1] === kk[1]; });
      if (!cand.length) return false; if (kk[2] != null) { cand.sort(function (a, b) { return Math.abs(+rpKey(a[0]).split('|')[2] - kk[2]) - Math.abs(+rpKey(b[0]).split('|')[2] - kk[2]); }); } it = cand[0]; $('m2dFindMsg').textContent = '「' + q + '」 그대로는 없어 가장 가까운 번호 ' + it[0] + ' 로'; }
    else $('m2dFindMsg').textContent = '';
    rpGo(it); return true; }
  function rpNear(m, sk, lim) { if (!RP || !RP.sets[sk]) return null; var b = null, bd = 1e12; RP.sets[sk].items.forEach(function (it) { var dx = it.p[0] - m[0], dy = it.p[1] - m[1]; if (Math.abs(dx) > lim || Math.abs(dy) > lim) return; var d = dTrue(it.p, m); if (d < bd) { bd = d; b = it; } }); return b && bd <= lim ? [b, bd] : null; }
  function drawRpost(dark) {
    if (!on.rpost) return; if (!RP) { rpLoad(); return; } if (view.s < 0.35) return; var W0 = cv.clientWidth, H0 = cv.clientHeight, lab = view.s >= 0.9;
    Object.keys(RP.sets).forEach(function (sk) { RP.sets[sk].items.forEach(function (it) { var sx = S(it.p); if (sx[0] < -20 || sx[1] < -20 || sx[0] > W0 + 20 || sx[1] > H0 + 20) return;
      dot(it.p, 3, sk === 'exkm' ? '#16a34a' : '#f59e0b', dark ? '#111827' : '#fff', { kind: 'rpost', r: it });
      if (lab) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'left'; ctx.textBaseline = 'middle'; var tx = sk === 'exkm' ? exNm(it).replace(/선(\(.*\))?$/, '') + ' ' + exKm(it) : String(it[0]).replace('_', ''); ctx.lineWidth = 3; ctx.strokeStyle = dark ? 'rgba(15,22,36,.9)' : 'rgba(255,255,255,.9)'; ctx.strokeText(tx, sx[0] + 5, sx[1]); ctx.fillStyle = dark ? '#fde68a' : '#92400e'; ctx.fillText(tx, sx[0] + 5, sx[1]); } }); });
  }
  function rpCopyBtn(p) { var ll = [p[0] / KX + LON0, LAT0 - p[1] / KY]; return '<button data-copy="' + ll[1].toFixed(6) + ', ' + ll[0].toFixed(6) + '">📋 좌표 복사 ' + ll[1].toFixed(5) + ', ' + ll[0].toFixed(5) + '</button>'; }
  function rpCard(it) {
    var L = RP && RP.sets.lamp, srcT = src((L ? L.source + ' · ' + L.license : '서울특별시 가로등 위치 정보') + ' · 기준일 2022-11-08 — 그 뒤 바뀐 번호는 다를 수 있다');
    if (it.kind === 'rpost') { var r = it.r; if (r.sk === 'exkm') return '<h3>🔢 ' + esc(exNm(r)) + ' ' + exKm(r) + 'km</h3>' + row('노선', esc(exNm(r)) + ' <small style="color:var(--ink2)">(노선번호 ' + esc((RP.sets.exkm.routes[r[0]] || [])[0]) + ')</small>') + row('이정', exKm(r) + 'km — 노선 기점에서 잰 거리(거리표 숫자)') + '<div class="lg-btns">' + rpCopyBtn(r.p) + '</div><p class="desc">⚠ 도로 중심선 위 점이라 실제 거리표 기둥과 수~수십 m 다르다 · 상·하행 구분 없음</p>' + src(RP.sets.exkm.source || '한국도로공사 도로중심선 이정 좌표');
      return '<h3>🔢 ' + esc(r[0]) + '</h3>' + row('도로', rpRoad(r[0])) + row('번호 꼴', '접두_구간-순번 (가로등주 관리번호)') + '<div class="lg-btns">' + rpCopyBtn(r.p) + '</div><p class="desc">' + esc((L && L.prefixNote) || '') + ' · 기둥에 붙은 번호와 다르면 현장 번호가 맞다.</p>' + srcT; }
    if (!RP) { rpLoad(); return '<h3>📍 여기서 가장 가까운 번호</h3><p class="desc">도로 번호 목록을 받는 중…</p>'; }
    var m = it.m, a = rpNear(m, 'lamp', 600), b = rpNear(m, 'exkm', 1500), h = '<h3>📍 여기서 가장 가까운 번호</h3>';
    h += a ? row('가로등 번호', '<button class="lk" data-rpgo="lamp|' + esc(a[0][0]) + '"><b>' + esc(a[0][0]) + '</b></button> · ' + Math.round(a[1]) + 'm · ' + rpRoad(a[0][0])) : row('가로등 번호', '600m 안에 없다 <em>(서울 도시고속도로만 자료가 있다)</em>');
    if (RP.sets.exkm) h += b ? row('고속도로 거리표', '<button class="lk" data-exgo="' + RP.sets.exkm.items.indexOf(b[0]) + '">' + esc(exNm(b[0])) + ' <b>' + exKm(b[0]) + 'km</b></button> · ' + Math.round(b[1]) + 'm') : row('고속도로 거리표', '1.5km 안에 없다');
    else h += row('고속도로 거리표', '자료 대기 <em>(한국도로공사 이정 좌표를 받으면 붙는다)</em>');
    return h + '<div class="lg-btns">' + rpCopyBtn(m) + '</div><p class="desc">112·119·무전으로 위치를 불러 줄 때 — 「올림픽대로 올_23-05 가로등 앞」처럼. 일반국도 km 는 공개 자료가 없다.</p>' + srcT; }
  cv.addEventListener('pointerdown', function (e) { RPLP.fired = false; clearTimeout(RPLP.t); if (e.pointerType === 'mouse') return; RPLP.x = e.offsetX; RPLP.y = e.offsetY;
    RPLP.t = setTimeout(function () { if (drag && drag.moved >= 8) return; if (Object.keys(ptrs).length > 1) return; RPLP.fired = true; rpLong(RPLP.x, RPLP.y); }, 650); });
  cv.addEventListener('pointermove', function (e) { if (Math.abs(e.offsetX - RPLP.x) + Math.abs(e.offsetY - RPLP.y) > 8) clearTimeout(RPLP.t); });
  cv.addEventListener('pointerup', function () { clearTimeout(RPLP.t); });
  cv.addEventListener('contextmenu', function (e) { e.preventDefault(); clearTimeout(RPLP.t); RPLP.fired = true; rpLong(e.offsetX, e.offsetY); });
  function rpLong(x, y) { var m = M(x, y); TAPM = m; var it = { kind: 'rnear', m: m }; sel = { x: x, y: y, r: 6, it: it }; rpLoad().then(function () { if (sel && sel.it === it) show(it); }); show(it); draw(); try { navigator.vibrate && navigator.vibrate(30); } catch (e) {} }
  document.addEventListener('click', function (e) { var x = e.target.closest('[data-exgo]'); if (x && RP) { var it0 = RP.sets.exkm.items[+x.getAttribute('data-exgo')]; if (it0) rpGo(it0); return; } var b = e.target.closest('[data-rpgo]'); if (b) { var a = b.getAttribute('data-rpgo').split('|'), it = RPIX && RPIX[rpKey(a[1])]; if (it) rpGo(it); return; }
    var c = e.target.closest('#m2dCard [data-copy]'); if (c) { var t = c.getAttribute('data-copy'); try { navigator.clipboard.writeText(t).then(function () { c.textContent = '✅ 복사했다 ' + t; }); } catch (e2) { prompt('복사', t); } } });
  // ---------- v2.28.0 🔗 이 자리의 관계(온톨로지) — 소유자 「여러 가지 온톨로지적 개념을 넣은 설명을 상단에」 ----------
  //  대상(지점·칸·동·지구대·경찰서·시군구·교차로·카메라·응급실·관서)과 그 사이 관계(속함·관할·구역·가까움)를 이름 붙여 잇는다 · 관계마다 근거 = 원자료 / 계산(거리) / 근사
  var RELON = true; try { RELON = localStorage.getItem('tg_map2d_rel') !== '0'; } catch (e) {}
  function relNear(m, arr, pf, nf) { var b = null, bd = 1e12; arr.forEach(function (q) { var p = pf(q); if (!p) return; var d = dTrue(p, m); if (d < bd) { bd = d; b = q; } }); return b ? [nf(b), bd] : null; }
  function relFill(steps, m, it) {
    var box = $('m2dLad'); if (!box) return; var R = [], REL = { cell: ['속한다', '국가지점번호 250m 격자', '원자료'], ri: ['속한다', '브이월드 리 경계', '원자료'], dong: ['속한다', '통계청 SGIS 행정동 경계', '원자료'], pb: ['구역이다', '가장 가까운 지구대·파출소(관할 경계 비공개)', '근사'], ps: ['관할한다', '직제 시행규칙 별표2 × 행정동', '근사'], sgg: ['속한다', 'SGIS 시군구 경계', '원자료'] };
    var PRED = { cell: '에 속한다', ri: '에 속한다', dong: '에 속한다', pb: ' 구역이다(근사)', ps: ' 관할이다', sgg: '에 속한다' };
    steps.forEach(function (q, i) { var r = REL[q[0]]; if (!r || !q[2]) return; R.push(['이 자리는', '<button data-lad="' + i + '">' + esc(q[1]) + '</button>', PRED[q[0]], r[1], r[2]]); });
    jrsRel(m).forEach(function (q) { R.push(q); });
    function fm(d) { return d >= 1000 ? (d / 1000).toFixed(1) + 'km' : Math.round(d) + 'm'; }
    var nx = [];
    var jc = JCN.length ? relNear(m, JCN, function (J) { return J.p; }, function (J) { return J.t[0]; }) : null; if (jc && jc[1] < 3000) nx.push(['🚦 교차로', jc[0], jc[1], 'ITS 교차로 이름(원자료) · 거리 계산']);
    var cm = D.cam && D.cam.items.length ? relNear(m, D.cam.items, function (c) { return P(c.lon, c.lat); }, function (c) { return c.name || c.loc || c.addr || '무인 단속 카메라'; }) : null; if (cm && cm[1] < 3000) nx.push(['📷 단속 카메라', cm[0], cm[1], '경찰청 무인단속카메라(원자료) · 거리 계산']);
    var er = PUB && PUB.er && PUB.er.length ? relNear(m, PUB.er, function (q) { return q.p; }, function (q) { return q.name; }) : null; if (er && er[1] < 15000) nx.push(['🏥 응급실', er[0], er[1], '응급의료기관(원자료) · 거리 계산']);
    if (POL2) { var pb = relNear(m, POL2.pbox, function (b) { return b.p; }, function (b) { return b[0] + (b[1] ? ' 파출소' : ' 지구대'); }); if (pb) nx.push(['👮 지구대·파출소 청사', pb[0], pb[1], '경찰청 주소 현황 → 좌표 · 거리 계산']);
      var ps = relNear(m, POL2.stations, function (q) { return q.p; }, function (q) { return q[1]; }); if (ps) nx.push(['🚓 경찰서 청사', ps[0], ps[1], '경찰민원24 좌표 · 거리 계산']); }
    var rpn = RP ? rpNear(m, 'lamp', 400) : null; if (rpn) nx.push(['🔢 가로등 번호', rpn[0][0], rpn[1], '서울시 가로등 위치(2022-11) · 거리 계산']);
    var ll = [m[0] / KX + LON0, LAT0 - m[1] / KY];
    var h = '<details class="rel"' + (RELON ? ' open' : '') + '><summary>🔗 이 자리의 관계 <small>— 대상과 관계를 이름 붙여 잇는 「온톨로지」 보기</small></summary>' +
      '<div class="relx">지점 <b>' + ll[1].toFixed(5) + ', ' + ll[0].toFixed(5) + '</b>' + (it && it.kind && it.kind !== 'dong' && it.kind !== 'unit' ? ' · 지금 카드 = ' + esc(({ g250: '250m 칸', land: '필지', jgc: '공시지가 칸', node: '교차로', cam: '단속 카메라', stay: '숙박시설', minbak: '도시민박', pub: '시설', rnl: '도로', rpost: '도로 번호', rnear: '가까운 도로 번호' })[it.kind] || it.kind) : '') + '</div>' +
      '<div class="rell">' + R.map(function (r) { return '<div><span class="s">' + r[0] + '</span> ' + r[1] + ' <span class="p">' + r[2] + '</span><small>' + esc(r[3]) + ' · <i class="' + (r[4] === '원자료' ? 'o' : 'a') + '">' + r[4] + '</i></small></div>'; }).join('') +
      nx.map(function (q) { return '<div><span class="s">가장 가까운 ' + q[0] + '</span> <b>' + esc(q[1]) + '</b> <span class="p">' + fm(q[2]) + '</span><small>' + esc(q[3]) + ' · <i class="c">계산</i></small></div>'; }).join('') + '</div>' +
      '<p class="relh">위 단추를 누르면 그 대상의 카드로 넘어간다(넓혀 가기). 아래는 그 대상과 윗단위 비교 · 아래 단위 순위(좁혀 가기). 근거 표시 — <i class="o">원자료</i> 공식 자료에 적힌 관계 · <i class="c">계산</i> 이 지도가 거리로 만든 관계 · <i class="a">근사</i> 공식 경계가 없어 가까운 쪽으로 정한 관계.</p></details>';
    h = h.replace(/<\/details>$/, ledgRel(m) + '</details>');
    box.insertAdjacentHTML('beforeend', h);
    var dd = box.querySelector('details.rel'); if (dd) dd.addEventListener('toggle', function () { RELON = dd.open; try { localStorage.setItem('tg_map2d_rel', RELON ? '1' : '0'); } catch (e) {} });
  }
  // ---------- v2.27.0 일터·생활업종 역추정(코워크 지시 2026-10-06) — 국민연금 사업장(행정동) · 국세청 사업자현황(시군구) · tools/region/econ-bake.py ----------
  //  값은 원자료 합 그대로 · 「어림」·「가설」 딱지 · 시군구 값을 동으로 나누지 않는다
  var ECD = null, ECG = null, ECP = null, ECNK = null, ECR = null;
  function econLoad() { if (ECP) return ECP; ECP = Promise.all([fetch('data/econ-dong.json').then(function (r) { return r.json(); }), fetch('data/econ-gu.json').then(function (r) { return r.json(); }), fetch('data/biz-rates.json').then(function (r) { return r.json(); }).catch(function () { return null; })]).then(function (a) { ECD = a[0]; ECG = a[1]; ECR = a[2]; ECNK = {}; Object.keys(ECG.gu).forEach(function (k) { ECNK[k.replace(/\s/g, '')] = k; });
    var c = $('m2dCard'); if (c && c.classList.contains('on') && sel && sel.it && /^(dong|unit)$/.test(sel.it.kind)) show(sel.it); }).catch(function () { ECD = ECG = null; }); return ECP; }
  var ECALT = { '12': ['광주광역시', '전라남도', '전남광주통합특별시'], '51': ['강원특별자치도', '강원도'], '52': ['전북특별자치도', '전라북도'] };
  function econGuKey(gu) { if (!ECNK) return null; var g = rIdx().filter(function (x) { return x.gu === gu; })[0]; if (!g) return null; var nm = g.name.replace(/\s/g, ''), sds = (ECALT[g.sido] || []).concat([SIDO_FULL[g.sido] || '']);
    for (var i = 0; i < sds.length; i++) { var k = ECNK[sds[i].replace(/\s/g, '') + nm]; if (k) return k; }
    var c = Object.keys(ECNK).filter(function (q) { return q.slice(-nm.length) === nm; }); return c.length === 1 ? ECNK[c[0]] : null; }
  function econSggKeys(i) { if (!ECNK) { econLoad(); return []; } var G = SGG[i].g, sds = [G.sido].concat(ECALT[Object.keys(SIDO_FULL).filter(function (c) { return SIDO_FULL[c] === G.sido; })[0]] || []), nm = G.name.replace(/\s/g, '');
    var o = []; Object.keys(ECNK).forEach(function (q) { sds.forEach(function (sd) { var p = sd.replace(/\s/g, '') + nm; if (q === p || (q.indexOf(p) === 0 && /구$/.test(q))) if (o.indexOf(ECNK[q]) < 0) o.push(ECNK[q]); }); }); return o; }
  function econMerge(keys) { var B = {}, D = {}, A = {}; keys.forEach(function (k) { var g = ECG.gu[k]; if (!g) return;
      Object.keys(g.b100).forEach(function (q) { var t = B[q] = B[q] || [0, 0]; t[0] += g.b100[q][0]; t[1] += g.b100[q][1]; });
      Object.keys(g.dur).forEach(function (q) { var t = D[q] = D[q] || [0, 0, 0]; t[0] += g.dur[q][0]; t[1] += g.dur[q][1]; t[2] += g.dur[q][2]; });
      Object.keys(g.age).forEach(function (q) { var t = A[q] = A[q] || [0, 0]; t[0] += g.age[q][0]; t[1] += g.age[q][1]; }); }); return { b100: B, dur: D, age: A }; }
  var ECFIX = ['호프주점', '간이주점', '노래방', '편의점', '커피음료점', '한식음식점', 'pc방', '여관ㆍ모텔'];
  function ecPct(a, b) { return b ? (a / b - 1) * 100 : null; }
  function econGuHtml(keys, nm) { if (!ECG) { econLoad(); return '<p class="cap">국세청 생활업종 자료를 받는 중…</p>'; } if (!keys.length) return ''; var M0 = econMerge(keys), B = M0.b100, h = '<div class="dh">🌡 생활업종 체온 — ' + esc(nm) + ' <small style="font-weight:600;color:var(--ink2)">(국세청 ' + esc(String(ECG.asof).replace(/(\d{4})(\d\d)(\d\d)/, '$1.$2')) + ' · 시군구)</small></div>';
    var L2 = Object.keys(B).filter(function (q) { return B[q][1] >= 20; }).map(function (q) { return [q, B[q][0], ecPct(B[q][0], B[q][1])]; });
    var up = L2.slice().sort(function (a, b) { return b[2] - a[2]; }).slice(0, 5), dn = L2.slice().sort(function (a, b) { return a[2] - b[2]; }).slice(0, 5);
    function f(q) { return esc(q[0]) + ' ' + q[1].toLocaleString() + ' <b style="color:' + (q[2] >= 0 ? '#dc2626' : '#2563eb') + '">' + (q[2] >= 0 ? '+' : '') + q[2].toFixed(1) + '%</b>'; }
    h += row('많이 는 업종', up.map(f).join(' · ')) + row('많이 준 업종', dn.map(f).join(' · '));
    h += row('밤·생활 업종', ECFIX.filter(function (q) { return B[q]; }).map(function (q) { return f([q, B[q][0], ecPct(B[q][0], B[q][1]) || 0]); }).join(' · ') + ' <em>(사업자 수 · 한 해 전 같은 달 대비)</em>');
    var D = M0.dur, A = M0.age; function age2(up) { var d = D[up], a = A[up]; if (!d || !d[2]) return ''; return esc(up) + ' 3년 미만 <b>' + Math.round(d[0] / d[2] * 100) + '%</b> · 10년 이상 ' + Math.round(d[1] / d[2] * 100) + '%' + (a && a[1] ? ' · 대표자 40세 미만 ' + Math.round(a[0] / a[1] * 100) + '%' : ''); }
    h += row('상권 나이', ['음식업', '소매업', '숙박업'].map(age2).filter(Boolean).join('<br>'));
    var bar = B['호프주점'] && B['간이주점'] ? [B['호프주점'][0] + B['간이주점'][0], B['호프주점'][1] + B['간이주점'][1]] : null, fd = D['음식업'];
    var hy = []; if (bar && bar[0] > bar[1]) hy.push('주점(호프·간이) ' + bar[1] + ' → ' + bar[0] + '곳 — 밤 음주운전 단속 자리를 다시 볼 만하다');
    if (fd && fd[2] && fd[0] / fd[2] >= 0.35) hy.push('음식업 3년 미만 ' + Math.round(fd[0] / fd[2] * 100) + '% — 상권이 바뀌는 중일 수 있다(이면도로 조업·배달 이륜 증가 가능)');
    if (hy.length) h += '<div class="talk"><b>🧪 가설 — 숫자에서 끌어낸 해석(사실 확인 전)</b>' + hy.map(function (q) { return '<div>· ' + esc(q) + (/주점/.test(q) ? ' <small>관련 근거 ' + ledgBadge('R3') + ' 주점 비중이 높은 칸은 밤 사고 비율이 높다(서울 두 지역 묶음 재현) — 이 구의 「늘었다」 자체는 검증 전</small>' : '') + '</div>'; }).join('') + '</div>';
    return h + src(ECG.source + ' · ' + ECG.note); }
  function econRows(k8) { if (!k8) return ''; if (!ECD) { econLoad(); return ''; } var v = ECD.dong[k8], h = '', rt = ECR && ECR.pension ? ECR.pension[0] * 2 : null;
    if (v) { h += '<div class="dh">🏢 일터 — 국민연금 가입 사업장 <small style="font-weight:600;color:var(--ink2)">(' + esc(ECD.ym) + ')</small></div>';
      h += row('국민연금 가입 직장인(어림)', '<b>' + v[1].toLocaleString() + '명</b> · 사업장 ' + v[0].toLocaleString() + '곳(법인 ' + v[5].toLocaleString() + ' · 50인 이상 ' + v[6] + ')');
      if (rt && v[1]) h += row('1인당 월 보수 어림', '약 ' + Math.round(v[2] / v[1] / rt / 1e4).toLocaleString() + '만 원 <em>(고지금액 ÷ 가입자 ÷ 보험료율 ' + (rt * 100).toFixed(1) + '%)</em>');
      h += row('이번 달 고용', '신규 ' + v[3].toLocaleString() + ' · 상실 ' + v[4].toLocaleString() + ' → <b style="color:' + (v[3] - v[4] >= 0 ? '#dc2626' : '#2563eb') + '">' + (v[3] - v[4] >= 0 ? '+' : '') + (v[3] - v[4]).toLocaleString() + '명</b>');
      if (v[7] && v[7].length) h += row('가입자 많은 업종', v[7].map(function (q) { return esc(q[0]) + ' ' + q[1].toLocaleString(); }).join(' · '));
      h += '<p class="cap">⚠ 상한 때문에 고소득 동은 보수가 낮게 나온다 · ⚠ 본사 일괄신고 사업장은 본사 동에 몰린다(강남·서초·여의도 과대) · ⚠ 공무원·사학·군인 연금 대상자는 빠진다</p>'; }
    var gk = econGuKey(k8.slice(0, 5)); if (gk) h += econGuHtml([gk], gk.replace(/^\S+\s/, ''));
    return h; }
  // ---------- v2.26.0 🛏 숙박시설(전국 · 지방행정인허가 다섯 업종) — tools/region/stay-bake.py → r/<구>/stay.json ----------
  var STY = [['🏨', '관광호텔', '#2563eb'], ['🎒', '호스텔', '#f59e0b'], ['🏖', '휴양콘도', '#0891b2'], ['🏯', '한옥체험', '#9a3412'], ['🏡', '관광펜션', '#16a34a'], ['🌾', '농어촌민박', '#65a30d'], ['🛌', '숙박업(여관·모텔 등)', '#7c3aed']];
  var STK = {}, RLOADST = {}, STYON = [1, 1, 1, 1, 1, 1, 1];
  try { var sy0 = localStorage.getItem('tg_map2d_sty'); if (sy0 && sy0.length === STY.length) STYON = sy0.split('').map(function (x) { return x === '1'; }); } catch (e) {}
  function stLoad(gu) { if (RLOADST[gu]) return; RLOADST[gu] = 1; var g = rIdx().filter(function (x) { return x.gu === gu; })[0]; if (g && !(g.bytes || {}).stay) return;
    rGet(gu, 'stay.json').then(function (j) { j.pts.forEach(function (q) { q.p = P(q[1], q[0]); }); STK[gu] = j; draw(); var c = $('m2dCard'); if (c && c.classList.contains('on') && sel && sel.it && /^(dong|rgo)$/.test(sel.it.kind)) show(sel.it); }).catch(function () { RLOADST[gu] = 2; }); }
  function drawStay(dark) {
    if (!on.stay || view.s < 0.006) return; var v = viewLL(), W0 = cv.clientWidth, H0 = cv.clientHeight;
    rIdx().forEach(function (g) { var x = g.box; if (!(g.bytes || {}).stay || x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return; stLoad(g.gu); });
    Object.keys(STK).forEach(function (gu) { var j = STK[gu]; j.pts.forEach(function (q) { if (!STYON[q[3]]) return; var sx = S(q.p); if (sx[0] < -10 || sx[1] < -10 || sx[0] > W0 + 10 || sx[1] > H0 + 10) return;
      dot(q.p, view.s >= 0.03 ? 4.2 : 3, q[4] ? '#94a3b8' : STY[q[3]][2], q[9] ? (dark ? '#fde047' : '#111827') : '#fff', { kind: 'stay', s: q, m: j }); }); });
  }
  function stayCard(it) { var q = it.s, m = it.m, t = STY[q[3]];
    return '<h3>' + t[0] + ' ' + esc(q[2] || '(이름 없음)') + '</h3>' + row('종류', esc((m.types || [])[q[3]] || t[1]) + (q[8] ? ' · ' + esc(q[8]) : '')) + row('상태', q[4] ? '<b>휴업</b>' : '영업') + (q[9] ? row('영문 상호', esc(q[9]) + ' <em>(외국인 손님을 받는 곳일 가능성 — 추론)</em>') : '') +
      row('객실', q[5] != null ? q[5] + '실' : '자료 없음') + row('주소', esc(q[6])) + (q[7] ? row('인허가', esc(q[7])) : '') + (q[10] ? row('자리', '원본에 좌표가 없어 주소로 찾음') : '') +
      '<p class="desc">투숙 인원·국적은 공개되지 않는다. 같은 호텔이 관광숙박업(관광)과 숙박업(위생)에 두 번 등록됐을 수 있다.</p>' + src(m.source); }
  // ---------- v2.21.0 🟧 공시지가 지도(대지 ㎡당 중앙값 · 250m 칸·동) — tools/region/jiga-bake.py → r/<구>/jiga.json ----------
  var JIGA = {}, JIGAG = {}, RLOADJG = {}, JIGJM = {}, JGM = 'p';
  try { JGM = localStorage.getItem('tg_map2d_jgm') || 'p'; } catch (e) {}
  var JGMS = { p: ['💰 공시지가', -1, '#7c3aed'], f: ['🌾 농지 비율', 1, '#65a30d'], w: ['🌳 임야 비율', 2, '#166534'], h: ['🏠 대지 비율', 0, '#c2410c'], i: ['🏭 공장·창고 비율', 3, '#475569'] };
  function jmShare(v, gi) { var t = 0; v.forEach(function (x) { t += x; }); return t ? v[gi] / t : null; }
  function jmRow(v, G) { if (!v) return ''; var t = 0; v.forEach(function (x) { t += x; }); if (!t) return ''; return row('땅 쓰임(지목 · 넓이)', v.map(function (x, i) { return [x, i]; }).filter(function (q) { return q[0] / t >= 0.01; }).sort(function (a, b) { return b[0] - a[0]; }).map(function (q) { return esc(G[q[1]].replace(/\(.*\)/, '')) + ' <b>' + Math.round(q[0] / t * 100) + '%</b>'; }).join(' · ') + ' <em>(지목 · 측량·지적법)</em>'); }
  var JGB = [0, 1e6, 3e6, 5e6, 1e7, 2e7, 4e7], JGC = ['#fef3c7', '#fde047', '#fb923c', '#ef4444', '#be123c', '#86198f', '#3b0764'], JGL = ['100만 원 미만', '100~300만', '300~500만', '500만~1천만', '1천~2천만', '2천~4천만', '4천만 이상'];
  function jgBin(v) { var i = 0; while (i < JGB.length - 1 && v >= JGB[i + 1]) i++; return i; }
  function jgLoad(gu) { if (RLOADJG[gu]) return; RLOADJG[gu] = 1; grLoad(gu).then(function () { return rGet(gu, 'jiga.json'); }).then(function (j) { JIGA[gu] = j; if (j.jm) Object.keys(j.jm.grid).forEach(function (k) { JIGJM[k] = j.jm.grid[k]; }); Object.keys(j.grid).forEach(function (k) { if (!JIGAG[k] || JIGAG[k].v[1] < j.grid[k][1]) JIGAG[k] = { v: j.grid[k], m: j, n: (j.n && j.n.grid[k]) || 0 }; }); draw(); }).catch(function () { RLOADJG[gu] = 2; }); }
  function jgDong(k8) { if (!k8) return null; var j = JIGA[k8.slice(0, 5)]; if (j && j.dong[k8]) return j.dong[k8]; for (var g in JIGA) if (JIGA[g].dong[k8]) return JIGA[g].dong[k8]; return null; }
  function jgJmDong(k8) { var j = JIGA[k8.slice(0, 5)]; if (j && j.jm && j.jm.dong[k8]) return j.jm.dong[k8]; for (var g in JIGA) if (JIGA[g].jm && JIGA[g].jm.dong[k8]) return JIGA[g].jm.dong[k8]; return null; }
  function jgGroups() { for (var g in JIGA) if (JIGA[g].jm) return JIGA[g].jm.groups; return ['대지', '농지', '임야', '공장·창고', '길·물', '그 밖']; }
  function jgYear() { for (var g in JIGA) return JIGA[g].year; return ''; }
  function drawJiga(dark) {
    if (!on.jiga) return; var v = viewLL(), W0 = cv.clientWidth, H0 = cv.clientHeight;
    rIdx().forEach(function (g) { var x = g.box; if (!(g.bytes || {}).jiga || x[2] < v[0] || x[0] > v[2] || x[3] < v[1] || x[1] > v[3]) return; jgLoad(g.gu); });
    if (JGM !== 'p') { var MQ = JGMS[JGM]; if (view.s < 0.03) { allDong().forEach(function (d) { var jj = d.k && jgJmDong(d.k), sh = jj && jmShare(jj, MQ[1]); if (sh == null || !inViewBox(d)) return; ctx.fillStyle = hexA(MQ[2], 0.06 + 0.7 * sh); d.polys.forEach(function (pg) { path(pg[0]); ctx.closePath(); ctx.fill(); }); }); return; }
      Object.keys(JIGJM).forEach(function (k) { if (!GRID[k]) return; var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0)) return; var sh = jmShare(JIGJM[k], MQ[1]); if (sh == null) return; ctx.fillStyle = hexA(MQ[2], 0.06 + 0.7 * sh); ctx.fillRect(r[0], r[1], r[2], r[3]);
        if (r[2] > 40 && sh >= 0.01) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = sh > 0.5 ? '#fff' : '#111827'; ctx.fillText(Math.round(sh * 100) + '%', r[0] + r[2] / 2, r[1] + r[3] / 2); }
        hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'jgc', c: k } }); }); return; }
    if (view.s < 0.03) { allDong().forEach(function (d) { var jd = d.k && jgDong(d.k); if (!jd || !inViewBox(d)) return; ctx.fillStyle = hexA(JGC[jgBin(jd[0])], 0.55); d.polys.forEach(function (pg) { path(pg[0]); ctx.closePath(); ctx.fill(); }); }); return; }
    Object.keys(JIGAG).forEach(function (k) { if (!GRID[k]) return; var r = sq(GRID[k].p, 125); if (!inView(r, W0, H0)) return; var val = JIGAG[k].v[0], bi = jgBin(val);
      ctx.fillStyle = hexA(JGC[bi], 0.62); ctx.fillRect(r[0], r[1], r[2], r[3]);
      if (r[2] > 44) { ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = bi >= 3 ? '#fff' : '#111827'; ctx.fillText(val >= 1e8 ? (val / 1e8).toFixed(1) + '억' : Math.round(val / 1e4).toLocaleString() + '만', r[0] + r[2] / 2, r[1] + r[3] / 2); }
      hit.push({ x: r[0] + r[2] / 2, y: r[1] + r[3] / 2, r: Math.max(6, r[2] * 0.71), it: { kind: 'jgc', c: k } }); });
  }
  function jgCard(it) { var g = JIGAG[it.c], jm = JIGJM[it.c], G0 = jgGroups(); if (!g) return jm ? '<h3>🟧 땅 쓰임 — 250m 칸 ' + esc(it.c) + '</h3>' + jmRow(jm, G0) + '<p class="desc">이 칸에는 대지가 없어 공시지가 중앙값이 없다.</p>' : ''; var v = g.v;
    return '<h3>🟧 공시지가 — 250m 칸 ' + esc(it.c) + '</h3>' + jmRow(jm, G0) + row('대지 ㎡당 중앙값', '<b>' + wonM2(v[0]) + '원</b> · 평당 ' + wonM2(v[0] * 3.305785) + '원') + row('가장 높은 대지', '㎡당 ' + wonM2(v[3]) + '원') +
      row('필지', '대지 ' + v[1].toLocaleString() + '필지(' + Math.round(v[2]).toLocaleString() + '㎡)' + (g.n ? ' · 이 칸 모든 필지 ' + g.n.toLocaleString() : '')) + (GRID[it.c] ? row('걸친 행정동', gDongs(it.c)) : '') +
      '<p class="desc">중앙값 = 이 칸에 대표점이 든 대지(지목 「대」) 필지들의 ㎡당 공시지가를 줄 세운 가운데 값. 도로·하천·임야 등은 뺐다. 필지 하나하나는 「📐 필지」를 켜고 누른다.</p>' + src(g.m.source + ' · ' + g.m.note); }
  // ---------- v2.19.0 📐 필지(브이월드 · 누르면 그때 받기) — 소유자 2026-10-06 「토지이음 토지 자료와 공시지가 · 쉽게 다 찾아볼 수 있는 세상 하나뿐인 지도」 ----------
  // 받는 곳 = api.vworld.kr 만(사용자가 켠 레이어 · 키는 기기마다 tg_map2d_vwkey) · 브이월드가 교차 출처 응답 머리를 안 줘서 callback 방식(JSONP) · 받은 값은 저장하지 않는다
  var LAND = { uq: false, g: null, gp: null, cad: null, uqi: null, wk: '', wt: null, n: 0 };
  try { LAND.uq = localStorage.getItem('tg_map2d_landuq') === '1'; } catch (e) {}
  function vwJ(url) { return new Promise(function (ok, no) {
    var cb = '__tgvw' + (++LAND.n) + 'x' + Date.now(), sc = document.createElement('script'), t = setTimeout(function () { fin(); no(new Error('응답 없음')); }, 15000);
    function fin() { clearTimeout(t); window[cb] = function () {}; if (sc.parentNode) sc.parentNode.removeChild(sc); }
    window[cb] = function (j) { fin(); ok(j); }; sc.onerror = function () { fin(); no(new Error('받기 실패')); };
    sc.src = url + (url.indexOf('?') < 0 ? '?' : '&') + 'callback=' + cb; document.head.appendChild(sc); }); }
  function vwDom() { return '340patrolman.github.io'; }
  function nedGet(op, pnu, ex) { return vwJ('https://api.vworld.kr/ned/data/' + op + '?key=' + encodeURIComponent(VWKEY) + '&domain=' + vwDom() + '&format=json&numOfRows=100&pageNo=1&pnu=' + pnu + (ex || '')).then(function (j) { var k = Object.keys(j || {})[0], v = k && j[k]; var f = v && (v.field || v[k] || v.ladfrlVOList); return Array.isArray(f) ? f : []; }).catch(function () { return null; }); }
  function landLL(m) { return [m[0] / KX + LON0, LAT0 - m[1] / KY]; }
  function landGet(it) {
    var ll = landLL(it.m);
    return vwJ('https://api.vworld.kr/req/data?service=data&request=GetFeature&data=LP_PA_CBND_BUBUN&key=' + encodeURIComponent(VWKEY) + '&domain=' + vwDom() + '&format=json&errorformat=json&size=1&page=1&crs=EPSG:4326&geometry=true&attribute=true&geomFilter=POINT(' + ll[0].toFixed(7) + '%20' + ll[1].toFixed(7) + ')').then(function (j) {
      var r = j && j.response; if (!r || r.status !== 'OK') { it.err = r && r.status === 'NOT_FOUND' ? '이 자리에는 필지가 없다(바다·하천일 수 있다)' : '브이월드가 답하지 않았다' + (r && r.error ? ' — ' + (r.error.text || r.error.code) : '') + ' · 키·하루 한도를 확인'; return; }
      var f = r.result.featureCollection.features[0]; it.f = f.properties; var gm = f.geometry, polys = gm.type === 'MultiPolygon' ? gm.coordinates : [gm.coordinates];
      it.rings = []; polys.forEach(function (pg) { pg.forEach(function (rg) { it.rings.push(rg.map(function (q) { return P(q[0], q[1]); })); }); }); LAND.g = it.rings; LAND.gp = it.f.pnu; draw();
      if (LCUR === it) show(it);
      var pnu = it.f.pnu;
      var ll2 = landLL(it.m); vwJ('https://api.vworld.kr/req/address?service=address&request=getAddress&type=both&format=json&crs=epsg:4326&key=' + encodeURIComponent(VWKEY) + '&domain=' + vwDom() + '&point=' + ll2[0].toFixed(7) + ',' + ll2[1].toFixed(7)).then(function (j) { var r2 = j && j.response; it.ad = r2 && r2.status === 'OK' ? r2.result : []; if (LCUR === it && $('m2dCard').classList.contains('on')) show(it); }).catch(function () { it.ad = []; });
      return Promise.all([nedGet('getIndvdLandPriceAttr', pnu), nedGet('getLandCharacteristics', pnu), nedGet('getLandUseAttr', pnu), nedGet('getBuildingUse', pnu), nedGet('ladfrlList', pnu)]).then(function (a) { it.pr = a[0]; it.ch = a[1]; it.lu = a[2]; it.bd = a[3]; it.fr = a[4]; it.done = 1; });
    }).catch(function (e) { it.err = '브이월드에 닿지 못했다(' + e.message + ') · 인터넷·키를 확인'; }).then(function () { if (LCUR === it && $('m2dCard').classList.contains('on')) show(it); }); }
  var LCUR = null;
  function wonM2(v) { v = +v || 0; return v >= 1e10 ? Math.round(v / 1e8).toLocaleString() + '억' : v >= 1e8 ? (v / 1e8).toFixed(v >= 1e9 ? 1 : 2).replace(/\.?0+$/, '') + '억' : v >= 1e4 ? Math.round(v / 1e4).toLocaleString() + '만' : Math.round(v).toLocaleString(); }
  function landCard(it) {
    LCUR = it; var hd = '<h3>📐 ' + esc(it.f ? it.f.addr : '필지') + '</h3>';
    var srcT = src('국토교통부 브이월드(연속지적도 · 개별공시지가 · 토지특성 · 토지이용계획 · 건축물 · 토지임야 · 주소 — 도로명주소는 행정안전부 자료) — 누를 때 받고 저장하지 않는다 · 공시지가는 세금·보상 기준값이지 시세가 아니다');
    if (!VWKEY) return hd + '<p class="desc">브이월드 인증키가 있어야 이 자리 필지를 받는다(vworld.kr → 마이페이지 → 인증키 · 이 기기에만 저장).</p><div class="lg-btns"><button data-vwkey="1">🔑 브이월드 키 넣기</button></div>' + srcT;
    if (it.err) return hd + '<p class="desc">⚠ ' + esc(it.err) + '</p>' + srcT;
    if (!it.f) { if (!it.q) it.q = landGet(it); return hd + '<p class="desc">브이월드에서 이 자리 필지를 받는 중…</p>' + srcT; }
    var f = it.f, h = hd, ch = (it.ch || []).slice().sort(function (a, b) { return (a.stdrYear + a.stdrMt).localeCompare(b.stdrYear + b.stdrMt); }).pop(), fr = (it.fr || [])[0];
    var jiga = +f.jiga || (ch && +ch.pblntfPclnd) || 0, ar = ch ? +ch.lndpclAr : fr ? +fr.lndpclAr : 0;
    var py = {}; (it.pr || []).forEach(function (q) { if (+q.pblntfPclnd) py[q.stdrYear] = +q.pblntfPclnd; }); var ys = Object.keys(py).sort(), yl = ys[ys.length - 1], yp = ys[ys.length - 2];
    var ch1 = yl && yp && py[yp] ? (py[yl] / py[yp] - 1) * 100 : null, jy = f.gosi_year; if (yl && py[yl]) { jiga = py[yl]; jy = yl; }
    if (jiga) h += row('개별공시지가', '<b>㎡당 ' + wonM2(jiga) + '원</b> · 평당 ' + wonM2(jiga * 3.305785) + '원' + (jy ? ' <em>(' + esc(jy) + '년 1월 1일 기준)</em>' : '') + (ch1 != null ? ' · 한 해 전보다 <b style="color:' + (ch1 >= 0 ? '#dc2626' : '#2563eb') + '">' + (ch1 >= 0 ? '+' : '') + ch1.toFixed(1) + '%</b>' : ''));
    var jck = cellAt(it.m), JGc = jck && JIGAG[jck]; var jsame = JGc && (py[JGc.m.year] || (String(f.gosi_year) === String(JGc.m.year) ? +f.jiga : 0)); if (JGc && jsame && f.jibun && /대$/.test(f.jibun)) h += row('이 250m 칸 대지 중앙값', wonM2(JGc.v[0]) + '원 — 같은 해(' + esc(JGc.m.year) + '년) 이 필지 ' + wonM2(jsame) + '원은 그 <b>' + (jsame / JGc.v[0]).toFixed(2) + '배</b>');
    if (ar) h += row('면적', Math.round(ar).toLocaleString() + '㎡ (' + Math.round(ar / 3.305785).toLocaleString() + '평)' + (jiga ? ' · 공시지가 × 면적 ≈ <b>' + wonM2(jiga * ar) + '원</b>' : ''));
    var rd = (it.ad || []).filter(function (a) { return a.type === 'road'; })[0], pc = (it.ad || []).filter(function (a) { return a.type === 'parcel'; })[0];
    if (rd) h += row('도로명주소', esc(rd.text) + (rd.zipcode ? ' <small style="color:var(--ink2)">(우 ' + esc(rd.zipcode) + ')</small>' : ''));
    if (pc && pc.structure && pc.structure.level4A) h += row('행정동', esc(pc.structure.level4A) + (pc.structure.level4L ? ' <small style="color:var(--ink2)">(법정동 ' + esc(pc.structure.level4L) + ')</small>' : ''));
    h += row('지번 · 고유번호', esc(f.jibun || '') + ' <small style="color:var(--ink2)">PNU ' + esc(f.pnu) + '</small>');
    if (ch) { h += row('지목 · 이용상황', esc(ch.lndcgrCodeNm || '') + ' · ' + esc(ch.ladUseSittnNm || '')); h += row('용도지역', esc(ch.prposArea1Nm || '') + (ch.prposArea2Nm && ch.prposArea2Nm !== '지정되지않음' ? ' · ' + esc(ch.prposArea2Nm) : ''));
      h += row('땅 모양 · 길', esc([ch.tpgrphHgCodeNm, ch.tpgrphFrmCodeNm].filter(Boolean).join(' · ')) + (ch.roadSideCodeNm ? ' · 도로접면 ' + esc(ch.roadSideCodeNm) : '')); }
    if (fr) h += row('소유 구분', esc(fr.posesnSeCodeNm || '') + (+fr.cnrsPsnCo ? ' · 공유 ' + esc(fr.cnrsPsnCo) + '명' : '') + ' <em>(이름은 공개되지 않는다)</em>');
    if (it.lu && it.lu.length) { var LU = {}; it.lu.forEach(function (q) { var k = q.cnflcAtNm || '포함'; (LU[k] = LU[k] || []).indexOf(q.prposAreaDstrcCodeNm) < 0 && LU[k].push(q.prposAreaDstrcCodeNm); });
      h += row('토지이용계획', Object.keys(LU).map(function (k) { return '<b>' + esc(k) + '</b> ' + LU[k].map(esc).join(' · '); }).join('<br>')); }
    if (ys.length > 1) { var arr = ys.map(function (y) { return py[y] / 1e4; }); h += '<div class="dh">📈 공시지가 해마다(㎡당 · ' + ys[0] + '~' + yl + ')</div>' + bar(arr, '#d97706', ys.map(function (y) { return "'" + y.slice(2); }), 'w') + '<p class="cap">' + ys[0] + '년 ' + wonM2(py[ys[0]]) + '원 → ' + yl + '년 ' + wonM2(py[yl]) + '원 (' + (py[yl] / py[ys[0]]).toFixed(1) + '배)</p>'; }
    if (it.bd && it.bd.length) { h += '<div class="dh">🏢 이 필지의 건물 ' + it.bd.length + '동</div>' + it.bd.slice(0, 8).map(function (b) { var yr = (b.useConfmDe || '').slice(0, 4), age = yr ? new Date().getFullYear() - +yr : null;
        return row(esc(b.buldNm || b.buldDongNm || b.buldMainAtachSeCodeNm || '건물'), esc(b.mainPrposCodeNm || '') + (b.detailPrposCodeNm && b.detailPrposCodeNm !== b.mainPrposCodeNm ? '(' + esc(b.detailPrposCodeNm) + ')' : '') + ' · 지상 ' + esc(b.groundFloorCo || '?') + '층/지하 ' + esc(b.undgrndFloorCo || 0) + '층 · 연면적 ' + Math.round(+b.buldTotar || 0).toLocaleString() + '㎡' + (b.strctCodeNm ? ' · ' + esc(b.strctCodeNm) : '') + (+b.btlRt ? ' · 건폐율 ' + esc(b.btlRt) + '% · 용적률 ' + esc(b.measrmtRt) + '%' : '') + (yr ? ' · 사용승인 ' + esc(b.useConfmDe) + (age != null ? ' <em>(' + age + '년 됨)</em>' : '') : '')); }).join('') + (it.bd.length > 8 ? '<p class="cap">… 외 ' + (it.bd.length - 8) + '동</p>' : ''); }
    else if (it.done) h += '<p class="cap">건축물대장에 오른 건물이 없다(빈 땅·도로이거나 대장이 다른 필지에 있다).</p>';
    if (!it.done) h += '<p class="cap">공시지가 추이·토지특성·건물을 받는 중…</p>';
    h += '<div class="lg-btns" style="margin-top:8px"><a class="xl" target="_blank" rel="noopener" href="https://www.eum.go.kr/web/ar/lu/luLandDet.jsp?pnu=' + esc(f.pnu) + '&mode=search&isNoScr=script">토지이음에서 보기 ↗</a></div>';
    return h + srcT; }
  function drawLand(dark) {
    if (!on.land) return; var W0 = cv.clientWidth, H0 = cv.clientHeight;
    [LAND.uqi, LAND.cad].forEach(function (I, i) { if (!I || !I.ok || (i === 0 && !LAND.uq) || (i === 1 && view.s < 0.5)) return; var a = S(P(I.b[0], I.b[3])), b = S(P(I.b[2], I.b[1]));
      ctx.save(); ctx.globalAlpha = i === 0 ? 0.42 : 0.95; if (i === 1 && !dark && !on.vw) ctx.filter = 'brightness(0.42) saturate(1.6)'; try { ctx.drawImage(I.im, a[0], a[1], b[0] - a[0], b[1] - a[1]); } catch (e) {} ctx.restore(); });
    if (LAND.g && sel && sel.it && sel.it.kind === 'land' && sel.it.rings === LAND.g) { LAND.g.forEach(function (r) { path(r); ctx.closePath(); ctx.fillStyle = 'rgba(250,204,21,.22)'; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = '#f59e0b'; ctx.stroke(); }); }
    if (!VWKEY) return; var v = viewLL(), wk = v.map(function (x) { return x.toFixed(5); }).join(',') + (LAND.uq ? 'u' : '');
    if (wk === LAND.wk) return; LAND.wk = wk; clearTimeout(LAND.wt);
    LAND.wt = setTimeout(function () { var sc = Math.min(2, window.devicePixelRatio || 1);
      function wms(lays, sty, k, w, h) { var I = { im: new Image(), b: v, ok: false }; I.im.onload = function () { I.ok = true; LAND[k] = I; draw(); };
        I.im.src = 'https://api.vworld.kr/req/wms?service=WMS&request=GetMap&version=1.3.0&layers=' + lays + '&styles=' + sty + '&crs=EPSG:4326&bbox=' + v[1] + ',' + v[0] + ',' + v[3] + ',' + v[2] + '&width=' + w + '&height=' + h + '&format=image/png&transparent=true&key=' + encodeURIComponent(VWKEY) + '&domain=' + vwDom(); }
      if (LAND.uq) wms('lt_c_uq111,lt_c_uq112,lt_c_uq113,lt_c_uq114', 'lt_c_uq111,lt_c_uq112,lt_c_uq113,lt_c_uq114', 'uqi', Math.min(2048, Math.round(W0 * sc)), Math.min(2048, Math.round(H0 * sc)));
      var need = Math.max(1, 1.7 / view.s), cw = Math.round(W0 * need), chh = Math.round(H0 * need);   // 지적선은 1m 에 1.6px 넘게 그려 달라고 해야 나온다(브이월드 축척 문턱)
      if (view.s >= 0.5 && cw <= 2048 && chh <= 2048) wms('lp_pa_cbnd_bubun', 'lp_pa_cbnd_bubun_line', 'cad', cw, chh);
    }, 380); }
  if ($('m2dLeg')) $('m2dLeg').addEventListener('click', function (e) { var b = e.target.closest('[data-sty]'); if (!b) return; var i = +b.getAttribute('data-sty'); STYON[i] = !STYON[i]; try { localStorage.setItem('tg_map2d_sty', STYON.map(function (x) { return x ? 1 : 0; }).join('')); } catch (e2) {} draw(); legend(); });
  if ($('m2dLeg')) $('m2dLeg').addEventListener('click', function (e) { var b = e.target.closest('[data-fdm]'); if (!b) return; FDM = b.getAttribute('data-fdm'); try { localStorage.setItem('tg_map2d_fdm', FDM); } catch (e2) {} draw(); legend(); });
  if ($('m2dLeg')) $('m2dLeg').addEventListener('click', function (e) { var b = e.target.closest('[data-jgm]'); if (!b) return; JGM = b.getAttribute('data-jgm'); try { localStorage.setItem('tg_map2d_jgm', JGM); } catch (e2) {} draw(); legend(); });
  if ($('m2dLeg')) $('m2dLeg').addEventListener('click', function (e) { var b = e.target.closest('[data-landuq]'); if (!b) return; LAND.uq = !LAND.uq; LAND.wk = ''; try { localStorage.setItem('tg_map2d_landuq', LAND.uq ? '1' : '0'); } catch (e2) {} draw(); legend(); });
  document.addEventListener('click', function (e) { var b = e.target.closest('#m2dCard [data-vwkey]'); if (!b) return; vwSetKey(); LAND.wk = ''; if (sel && sel.it && sel.it.kind === 'land') { sel.it.q = null; sel.it.err = null; show(sel.it); } });

  // ---------- v2.24.0 폰 카드 = 양옆 꽉 · 위 손잡이를 끌어 높이(기억) · 끝까지 내리면 닫힘 · 두 손가락으로 글씨 크기(기억) — 소유자 「반만 보인다 · 위아래로 크기 · 두 손가락 확대 축소 · 작은 화면 활용」 ----------
  (function () {
    var cd = $('m2dCard'); if (!cd) return; var small = function () { return window.innerWidth < 760; }, root = document.documentElement;
    var CH = 0.55, CZ = 1; try { CH = +localStorage.getItem('tg_map2d_cardh') || 0.55; CZ = +localStorage.getItem('tg_map2d_cardz') || 1; } catch (e) {}
    var CUR = 0;   // 지금 카드 높이(눈에 보이는 px) — 카드 전체를 zoom 하므로 잰 값 대신 이 값으로 끈다
    function setH(px) { var vh = window.innerHeight, h = Math.max(140, Math.min(vh - 24, px)); CUR = h; root.style.setProperty('--cardh', Math.round(h) + 'px'); document.body.classList.toggle('cardtall', h > vh * 0.62); }
    function setZ(z) { CZ = Math.max(0.8, Math.min(2.2, z)); root.style.setProperty('--cz', CZ.toFixed(2)); }
    setH(CH * window.innerHeight); setZ(CZ); window.addEventListener('resize', function () { setH(CH * window.innerHeight); });
    var dr = null;
    cd.addEventListener('pointerdown', function (e) { if (!small() || !e.target.closest('.grab')) return; dr = { y: e.clientY, h: CUR, n: CUR, id: e.pointerId, t: Date.now() }; try { cd.setPointerCapture(e.pointerId); } catch (e2) {} cd.classList.add('drag'); e.preventDefault(); });
    cd.addEventListener('pointermove', function (e) { if (!dr || e.pointerId !== dr.id) return; var nh = dr.h + (dr.y - e.clientY * 1); dr.n = Math.max(60, Math.min(window.innerHeight - 24, nh)); root.style.setProperty('--cardh', dr.n + 'px'); });
    function end(e) { if (!dr) return; var nh = dr.n, moved = Math.abs(nh - dr.h), quick = Date.now() - dr.t < 250; cd.classList.remove('drag'); dr = null;
      if (nh < 120) { setH(CH * window.innerHeight); var x = $('m2dX'); if (x) x.click(); return; }
      if (moved < 6 && quick) { nh = nh < window.innerHeight * 0.7 ? window.innerHeight * 0.92 : window.innerHeight * 0.5; }   // 손잡이를 톡 누르면 크게 ↔ 반
      CH = nh / window.innerHeight; setH(nh); try { localStorage.setItem('tg_map2d_cardh', CH.toFixed(3)); } catch (e2) {} }
    cd.addEventListener('pointerup', end); cd.addEventListener('pointercancel', end);
    function dist(t) { return Math.hypot(t[0].clientX - t[1].clientX, t[0].clientY - t[1].clientY); }
    var pz = null;
    cd.addEventListener('touchstart', function (e) { if (e.touches.length === 2) pz = { d: dist(e.touches) || 1, z: CZ }; }, { passive: true });
    cd.addEventListener('touchmove', function (e) { if (!pz || e.touches.length !== 2) return; e.preventDefault(); setZ(pz.z * dist(e.touches) / pz.d); }, { passive: false });
    cd.addEventListener('touchend', function (e) { if (pz && e.touches.length < 2) { pz = null; try { localStorage.setItem('tg_map2d_cardz', CZ.toFixed(2)); } catch (e2) {} } });
    if (window.MutationObserver) new MutationObserver(function () { document.body.classList.toggle('cardon', cd.classList.contains('on')); }).observe(cd, { attributes: true, attributeFilter: ['class'] });
    window.TGCard = { setH: setH, setZ: setZ, h: function () { return CH; }, z: function () { return CZ; } };
  })();
  // ---------- v2.18.0 쓰기 쉽게(소유자 2026-10-06 「밤 낮 모드 · 층 → 레이어 · 네이버·카카오·미국 부동산 지도처럼 · 1단계 단위 → 2단계 인구 → 3단계 업무 대·중·소 분류」) ----------
  // 레이어 키는 그대로(T-Book 주소 #ly= 그대로) — 묶음은 보여 주는 차례만 바꾼다 · 한 레이어가 여러 묶음에 들 수 있다
  var CATS = [
    ['people', '👥 인구·생활', [
      ['pop', '👥 인구 구성', [['주민·가구', ['jgg', 'dong']], ['그 시각 머무는 사람', ['live', 'live250', 'lpop']], ['외국인', ['fdong', 'fl250', 'minbak', 'stay', 'flodge']]], ['jgg', 'live250', 'lpop']],
      ['move', '🚶 이동·동선', [['대중교통', ['bus', 'subr', 'sub', 'exit', 'bstop', 'msub', 'busd', 'lbus']], ['사람 흐름', ['crowd', 'spot', 'bike', 'evt', 'gfest']]], ['bus', 'subr', 'sub']],
      ['life', '🏥 생활시설', [['의료', ['hosp', 'phar', 'er', 'ger', 'aed']], ['관공서', ['govr', 'gov', 'post', 'lib', 'dem', 'welf', 'kyr']], ['편의', ['conv', 'bank', 'box', 'wc', 'wc2', 'park', 'heat', 'cold', 'her']], ['차·연료', ['fuel', 'ev', 'gev', 'pk', 'gpark']]], ['govr', 'hosp', 'phar']],
      ['care', '🎒 교육·돌봄', [['학교', ['edu', 'school', 'aca']], ['어린이', ['kg', 'cc', 'kids', 'pg', 'sz']]], ['edu', 'kg', 'cc']]
    ]],
    ['police', '🚓 경찰업무', [
      ['traf', '🚦 교통', [['교통사고', ['acc', 'acc10', 'acc250', 'fatal', 'fatal10', 'jct', 'hot', 'hot10', 'drunk', 'risk', 'szh', 'spota']], ['신호·교차로', ['tlt', 'sig', 'sigx', 'tgis', 'pbtn', 'jcnm']], ['단속·시설', ['cam', 'pkcctv', 'sz', 'tow', 'pk', 'gpark']], ['도로·교통량', ['rnet', 'rpost', 'volp', 'exv', 'vol', 'spd', 'road']], ['지금 도로(실시간)', ['lev', 'lspd', 'lcc']]], ['acc', 'cam', 'sig', 'rnet', 'volp']],
      ['local', '👮 지역경찰', [['관할·관서', ['jurk', 'upb', 'pbox', 'pol', 'jur', 'fire', 'er']], ['야간 순찰', ['bar', 'play', 'inn', 'stay', 'srcctv', 'srbell', 'srlamp', 'glamp']], ['행사·인파', ['evt', 'crowd', 'spot', 'live']]], ['jurk', 'pbox', 'pol', 'bar', 'play']],
      ['safety', '🛡 생활안전', [['안심 귀갓길', ['srcctv', 'srbell', 'srlamp', 'sr112', 'srsvc', 'glamp', 'box']], ['어린이·노인', ['sz', 'szh', 'school', 'kids', 'pg', 'kyr', 'dem']], ['재난·계절', ['flt', 'flr', 'und', 'ice', 'hcab', 'advb', 'hyd', 'fw', 'heat', 'cold']]], ['srcctv', 'srbell', 'sz']]
    ]],
    ['biz', '💳 상권·부동산', [
      ['spend', '💳 소비·상권', [['카드·매출', ['sales', 'crowd']], ['상권', ['trd', 'szone', 'rent']], ['가게', ['conv', 'bank', 'bar', 'play', 'inn']]], ['sales', 'trd', 'szone']],
      ['estate', '🏠 주거·부동산', [['토지 · 공시지가', ['jiga', 'land']], ['실거래', ['home', 'rtc']], ['집·건물', ['jgg', 'bld']]], ['jiga', 'land', 'home']]
    ]],
    ['wx', '⛅ 날씨·실시간', [
      ['now', '🌦 지금 날씨', [['날씨', ['lwx', 'lair', 'lrad', 'lak', 'lkma']]], ['lwx', 'lair']],
      ['season', '⛅ 계절 위험', [['비·침수', ['flt', 'flr', 'und']], ['눈·결빙', ['ice', 'hcab', 'advb']], ['더위·추위', ['heat', 'cold']]], ['flt', 'ice']],
      ['live', '📡 실시간 교통', [['도로', ['lev', 'lspd', 'lcc', 'lbus']], ['인파', ['crowd']]], ['lev', 'lspd']]
    ]],
    ['base', '🗺 바탕', [
      ['map', '🗺 바탕 지도', [['바탕', ['dong', 'road', 'base', 'bld', 'vw', 'jcnm']], ['나눠 보기 경계', ['usgg', 'juris', 'jurk', 'upb', 'ri']], ['격자', ['g250']], ['역사', ['her']]], []]
    ]],
    ['all', '전체', null]
  ];
  // 맨 위 빠른 칩(네이버 지도의 「음식점·카페」 줄처럼) = 자주 쓰는 중분류
  var QCHIP = [['people', 'pop', '👥 인구'], ['police', 'traf', '🚦 교통'], ['police', 'local', '👮 지역경찰'], ['police', 'safety', '🛡 생활안전'], ['people', 'move', '🚶 이동'], ['biz', 'spend', '💳 상권'], ['biz', 'estate', '🏠 부동산'], ['wx', 'now', '🌦 날씨']];
  var UNITS = [['dong', '🏘 읍면동'], ['sgg', '🗂 시군구'], ['ps', '🚓 경찰서'], ['pb', '👮 지구대']];
  var UNIT = null, CTR = false, CAT = 'police', MID = 'traf', MODE = 'auto';
  try { UNIT = localStorage.getItem('tg_map2d_unit') || null; CTR = localStorage.getItem('tg_map2d_ctr') === '1'; CAT = localStorage.getItem('tg_map2d_cat') || CAT; MID = localStorage.getItem('tg_map2d_mid') || MID; MODE = localStorage.getItem('tg_map2d_mode') || 'auto'; } catch (e) {}
  if (UNIT && !UNITS.some(function (u) { return u[0] === UNIT; })) UNIT = null;
  function catOf(id) { return CATS.filter(function (c) { return c[0] === id; })[0]; }
  function catMid(c, id) { var C = catOf(c); return C && C[2] ? C[2].filter(function (m) { return m[0] === id; })[0] : null; }
  function hasL(k) { return LAYERS.some(function (l) { return l[0] === k; }); }
  function lname(k) { var l = LAYERS.filter(function (q) { return q[0] === k; })[0]; return l ? l[1] : k; }
  function midKeys(m) { var o = []; m[2].forEach(function (g) { g[1].forEach(function (k) { if (hasL(k) && o.indexOf(k) < 0) o.push(k); }); }); return o; }
  function midAct(m) { var d = m[3].filter(hasL); return d.length > 0 && d.every(function (k) { return on[k]; }); }
  function unitKeep() { if (UNIT === 'sgg') on.usgg = true; else if (UNIT === 'ps') on.jurk = true; else if (UNIT === 'pb') on.upb = true; }
  function unitAtU(m) {
    if (UNIT === 'sgg') { var i = sggAt(m); return i >= 0 ? { t: 'sgg', id: i } : null; }
    if (UNIT === 'ps' || UNIT === 'pb') { if (!POL2) { polLoad(); return null; } var d = dongAtM(m); if (!d || !d.k) return null;
      if (UNIT === 'pb') { if (d._pb === undefined) d._pb = pbOfP(d.k, d.c); if (d._pb != null) return { t: 'pb', id: d._pb }; }
      var st = polOf(d.k); if (st && st.length) return { t: 'ps', id: st[0][0] }; }
    return null; }
  function unitSet(u) {   // 누르면 볼 단위 — 시군구 경계는 그 단위일 때만 · 경찰서·지구대 경계는 켜 준다(내용 레이어이기도 해서 끄지는 않는다)
    UNIT = u; on.usgg = u === 'sgg'; if (u === 'ps') on.jurk = true; if (u === 'pb') on.upb = true; if (u === 'ps' || u === 'pb') polLoad();
    try { localStorage.setItem('tg_map2d_unit', u); } catch (e) {} saveOn(); paintLayers(); sel = null; show(null); draw(); }
  function ctrSet(f) { CTR = !!f; try { localStorage.setItem('tg_map2d_ctr', CTR ? '1' : '0'); } catch (e) {} ctrPaint(); paintLayers(); }
  function midApply(c, id, only) {   // 그 중분류 기본 레이어만 켠다(only) / 켜져 있으면 끈다
    var m = catMid(c, id); if (!m) return;
    if (!only && midAct(m)) { m[3].forEach(function (k) { if (KEEP.indexOf(k) < 0) on[k] = false; }); }
    else { LAYERS.forEach(function (l) { if (KEEP.indexOf(l[0]) < 0) on[l[0]] = false; }); on.dong = true; on.road = true; on.base = true; m[3].forEach(function (k) { if (hasL(k)) on[k] = true; }); }
    unitKeep(); CAT = c; MID = id; try { localStorage.setItem('tg_map2d_cat', c); localStorage.setItem('tg_map2d_mid', id); } catch (e) {}
    saveOn(); paintLayers(); sel = null; show(null); draw(); summary(); }
  var LFQ = '', LV = 'cat'; try { LV = localStorage.getItem('tg_map2d_lv') || 'cat'; } catch (e) {}
  // v2.29.0 소유자 「근무별 한 번에 메뉴를 전체 목록 밑에 — 어떻게 구성되고 진행되는지 알 수 있게 · 설명(건물·단속카메라 등)은 지금 전부 펼쳐져 있다 → 그 부분만도, 전체로도 접고 펼치게」
  var LHK = {}, GCL = {}, PRECO = false, PSTO = true;
  try { GCL = JSON.parse(localStorage.getItem('tg_map2d_gcl') || '{}') || {}; PSTO = localStorage.getItem('tg_map2d_pst') !== '0'; } catch (e) {}
  function gclSave() { try { localStorage.setItem('tg_map2d_gcl', JSON.stringify(GCL)); } catch (e) {} }
  function catPaint(pn, nOn) {   // v2.20.0 탭으로 가리지 않고 모두 펼친다 · v2.25.0 보기 셋 · v2.29.0 근무별 묶음을 위로 · 하나씩/모두 접기
    if (!CATS) return;
    if (!$('m2dPanB')) { pn.innerHTML = '<div id="m2dPanH"></div><details class="pst ptop" id="m2dPstD"' + (PSTO ? ' open' : '') + '><summary class="psec">⚡ 근무별 한 번에 <small>— 누르면 그 근무에 맞는 레이어 묶음만 켠다</small></summary><div id="m2dPreC"></div></details><div id="m2dPanB"></div><div class="pst" id="m2dPst2"></div>';
      var pd = $('m2dPstD'); if ($('m2dPre')) pd.insertBefore($('m2dPre'), $('m2dPreC')); pd.addEventListener('toggle', function () { PSTO = pd.open; try { localStorage.setItem('tg_map2d_pst', PSTO ? '1' : '0'); } catch (e) {} });
      var st = $('m2dPst2'), t2 = document.createElement('div'); t2.className = 'psec'; t2.textContent = '🕒 이 시각 한눈에'; st.appendChild(t2); if ($('m2dSum')) st.appendChild($('m2dSum'));
      var ft = document.createElement('div'); ft.className = 'pg pft'; ft.innerHTML = '<button data-none="1">모두 끄기</button><button data-reset="1">처음대로</button><button data-onb="1">❔ 처음 안내 다시</button>'; st.appendChild(ft);
      $('m2dPanH').innerHTML = '<div class="ph"><b>🗂 레이어 <small id="m2dPanN"></small></b><button class="x" data-close="1">닫기</button></div><div class="lvs"><button data-lv="cat">🗂 묶음별</button><button data-lv="all">📋 전체 목록</button><button data-lv="on">✅ 켜진 것</button></div>' +
        '<div class="fold"><button data-gall="open">▾ 묶음 모두 펼치기</button><button data-gall="close">▸ 묶음 모두 접기</button><button data-lh="1">ⓘ 설명 모두</button></div><input id="m2dLF" type="search" placeholder="레이어 이름으로 찾기 — 예: 사고 · 공시지가 · 버스" autocomplete="off"><div class="jmp" id="m2dJmp"></div>';
      $('m2dLF').addEventListener('input', function () { LFQ = this.value.trim(); lfApply(); });
      pn.addEventListener('toggle', function (e) { if (e.target && e.target.id === 'm2dPreCD') PRECO = e.target.open; }, true); }
    pn.classList.toggle('lvall', LV !== 'cat'); $('m2dPanN').textContent = nOn + '개 켜짐'; var lhb = $('m2dPanH').querySelector('[data-lh]'); if (lhb) { lhb.classList.toggle('on', !!LHON); lhb.textContent = LHON ? 'ⓘ 설명 모두 접기' : 'ⓘ 설명 모두 펼치기'; }
    $('m2dPanH').querySelectorAll('[data-lv]').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-lv') === LV); if (b.getAttribute('data-lv') === 'on') b.textContent = '✅ 켜진 것 ' + nOn; });
    var GL = []; LAYERS.forEach(function (l) { if (GL.indexOf(l[3]) < 0) GL.push(l[3]); }); GL.sort(function (a, b) { var x = GORD.indexOf(a), y = GORD.indexOf(b); return (x < 0 ? 99 : x) - (y < 0 ? 99 : y); });
    $('m2dJmp').innerHTML = LV === 'cat' ? CATS.filter(function (c) { return c[2]; }).map(function (c) { return '<button data-jump="' + c[0] + '">' + c[1] + '</button>'; }).join('') + '<button data-jump="etc">➕ 그 밖</button>' : LV === 'all' ? GL.map(function (g, i) { return '<button data-jump="g' + i + '">' + esc(g) + '</button>'; }).join('') : '';
    function chip(k) { var bt = '<button data-k="' + k + '" class="lyr' + (on[k] ? ' on' : '') + '" data-n="' + esc(lname(k)) + '">' + lname(k) + '</button>', op = LHON || LHK[k], q = '<button class="lhq' + (op ? ' on' : '') + '" data-lhk="' + k + '" aria-label="' + esc(lname(k)) + ' 설명 ' + (op ? '접기' : '펼치기') + '">ⓘ</button>';
      return op ? '<div class="lhi"><span class="lyw">' + bt + q + '</span>' + lhTxt(k) + '</div>' : '<span class="lyw">' + bt + q + '</span>'; }
    function sec(id, head, body, extra) { var cl = !!GCL[id]; return '<div class="c2' + (cl ? ' cl' : '') + '"><div class="c2h"><button class="gc" data-gc="' + esc(id) + '" aria-expanded="' + !cl + '">' + (cl ? '▸' : '▾') + ' ' + head + '</button>' + (extra || '') + '</div>' + (cl ? '' : body) + '</div>'; }
    var seen = {}, h = '';
    if (LV === 'all' || LV === 'on') {   // v2.25.0 모든 레이어를 분류마다 한 번씩 · 켜진 것만
      var LS = LV === 'on' ? LAYERS.filter(function (l) { return on[l[0]]; }) : LAYERS;
      h += LV === 'on' && !LS.length ? '<p class="lhn">켜진 레이어가 없다.</p>' : '';
      h += GL.map(function (g, i) { var ls = LS.filter(function (l) { return l[3] === g; }); if (!ls.length) return ''; var n = ls.filter(function (l) { return on[l[0]]; }).length;
        return '<section class="c1" id="lc-g' + i + '">' + sec('g:' + g, '<b>' + esc(g) + '</b> <small style="color:var(--ink2)">' + ls.length + '</small>' + (n ? ' <i>' + n + '</i>' : ''), '<div class="pg">' + ls.map(function (l) { return chip(l[0]); }).join('') + '</div>') + '</section>'; }).join('');
      if (LV === 'all') h += '<p class="lhn">모두 ' + LAYERS.length + '개 레이어 · 이름을 누르면 켜고 끈다 · ⓘ 를 누르면 그 레이어 설명(무엇 · 어디서 온 자료 · 어떻게 쓰나)만 펼친다 · 「🗂 묶음별」은 쓰임새(인구·경찰업무·상권…)로 다시 묶어 같은 레이어가 여러 곳에 나온다.</p>';
      $('m2dPanB').innerHTML = h; lfApply(); qcPaint(); return; }
    CATS.forEach(function (c) { if (!c[2]) return;
      h += '<section class="c1" id="lc-' + c[0] + '"><h4>' + c[1] + '</h4>' + c[2].map(function (m) { var ks = midKeys(m), n = ks.filter(function (k) { return on[k]; }).length; ks.forEach(function (k) { seen[k] = 1; });
        return sec('m:' + c[0] + '|' + m[0], '<b>' + m[1] + '</b>' + (n ? ' <i>' + n + '</i>' : ''), m[2].map(function (g) { var gk = g[1].filter(hasL); return gk.length ? '<div class="pg"><div class="pgt">' + esc(g[0]) + '</div>' + gk.map(chip).join('') + '</div>' : ''; }).join(''),
          (m[3].length ? '<button data-mon="' + c[0] + '|' + m[0] + '">기본만 켜기</button>' : '') + (n ? '<button data-moff="' + c[0] + '|' + m[0] + '">끄기</button>' : '')); }).join('') + '</section>'; });
    var etc = LAYERS.filter(function (l) { return !seen[l[0]]; });
    if (etc.length) h += '<section class="c1" id="lc-etc"><h4>➕ 그 밖의 레이어</h4>' + sec('m:etc', '<b>그 밖</b>', '<div class="pg">' + etc.map(function (l) { return chip(l[0]); }).join('') + '</div>') + '</section>';
    $('m2dPanB').innerHTML = h; lfApply(); qcPaint();
  }
  function gcAll(open) { var ids = []; if (LV === 'cat') CATS.forEach(function (c) { if (c[2]) c[2].forEach(function (m) { ids.push('m:' + c[0] + '|' + m[0]); }); }); else LAYERS.forEach(function (l) { if (ids.indexOf('g:' + l[3]) < 0) ids.push('g:' + l[3]); }); ids.push('m:etc');
    ids.forEach(function (k) { if (open) delete GCL[k]; else GCL[k] = 1; }); gclSave(); paintLayers(); }
  function lfApply() { var B = $('m2dPanB'); if (!B) return; var q = LFQ.replace(/\s/g, '');
    B.querySelectorAll('button.lyr').forEach(function (b) { var hit = !q || (b.getAttribute('data-n') || '').replace(/\s/g, '').indexOf(q) >= 0 || (b.getAttribute('data-k') === q); var el = b.closest('.lhi') || b.closest('.lyw') || b; el.style.display = hit ? '' : 'none'; });
    B.querySelectorAll('.pg, .c2, .c1').forEach(function (g) { if (!q) { g.style.display = ''; return; } var any = Array.prototype.some.call(g.querySelectorAll('button.lyr'), function (b) { var el = b.closest('.lhi') || b.closest('.lyw') || b; return el.style.display !== 'none'; }); g.style.display = any ? '' : 'none'; }); }
  function catClick(b) {
    var a;
    if ((a = b.getAttribute('data-p')) && b.classList.contains('pk')) { preset(a); return true; }
    if ((a = b.getAttribute('data-gc'))) { if (GCL[a]) delete GCL[a]; else GCL[a] = 1; gclSave(); paintLayers(); return true; }
    if ((a = b.getAttribute('data-gall'))) { gcAll(a === 'open'); return true; }
    if ((a = b.getAttribute('data-lhk'))) { if (LHON) { LHON = false; try { localStorage.setItem('tg_map2d_lh2', '0'); } catch (e) {} LAYERS.forEach(function (l) { LHK[l[0]] = 1; }); } LHK[a] = !LHK[a]; paintLayers(); return true; }
    if ((a = b.getAttribute('data-lv'))) { LV = a; try { localStorage.setItem('tg_map2d_lv', LV); } catch (e) {} paintLayers(); var pn0 = $('m2dPanel'); if (pn0) pn0.scrollTop = 0; return true; }
    if ((a = b.getAttribute('data-jump'))) { var sc = $('lc-' + a), pn = $('m2dPanel'); if (sc && pn) pn.scrollTo({ top: sc.offsetTop - ($('m2dPanH') ? $('m2dPanH').offsetHeight : 0) - 4, behavior: 'smooth' }); return true; }
    if ((a = b.getAttribute('data-cat'))) { CAT = a; var C = catOf(a); if (C && C[2] && !C[2].some(function (m) { return m[0] === MID; })) MID = C[2][0][0]; try { localStorage.setItem('tg_map2d_cat', CAT); localStorage.setItem('tg_map2d_mid', MID); } catch (e) {} paintLayers(); return true; }
    if ((a = b.getAttribute('data-mid'))) { MID = a; try { localStorage.setItem('tg_map2d_mid', MID); } catch (e) {} paintLayers(); return true; }
    if ((a = b.getAttribute('data-mon'))) { a = a.split('|'); midApply(a[0], a[1], true); return true; }
    if ((a = b.getAttribute('data-moff'))) { a = a.split('|'); var m = catMid(a[0], a[1]); if (m) { midKeys(m).forEach(function (k) { if (KEEP.indexOf(k) < 0) on[k] = false; }); unitKeep(); saveOn(); paintLayers(); draw(); summary(); } return true; }
    if ((a = b.getAttribute('data-unit'))) { unitSet(a); return true; }
    if (b.getAttribute('data-ctr')) { ctrSet(!CTR); return true; }
    if (b.getAttribute('data-onb')) { $('m2dPanel').classList.remove('on'); onbOpen(); return true; }
    return false; }
  function qcPaint() { var el = $('m2dQC'); if (!el) return;
    el.innerHTML = QCHIP.map(function (q) { var m = catMid(q[0], q[1]); return m ? '<button data-qc="' + q[0] + '|' + q[1] + '" class="' + (midAct(m) ? 'on' : '') + '">' + q[2] + '</button>' : ''; }).join(''); }
  if ($('m2dQC')) $('m2dQC').addEventListener('click', function (e) { var b = e.target.closest('[data-qc]'); if (!b) return; var a = b.getAttribute('data-qc').split('|'); midApply(a[0], a[1], false); });
  if ($('m2dTimeB')) $('m2dTimeB').onclick = function () { document.body.classList.toggle('timeon'); this.setAttribute('aria-expanded', document.body.classList.contains('timeon') ? 'true' : 'false'); };

  // 지도 가운데 기준 — 십자 표시 · 지도를 옮기면 가운데 동(고른 단위)을 바로 보인다
  var CROSS = document.createElement('div'); CROSS.id = 'm2dCross'; CROSS.setAttribute('aria-hidden', 'true'); document.body.appendChild(CROSS);
  var CTRB = document.createElement('button'); CTRB.id = 'm2dCtrB'; CTRB.textContent = '📍 가운데 보기'; document.body.appendChild(CTRB);
  var CTRAUTO = false, ctrT = null;
  function ctrXY() { return [cv.clientWidth / 2, Math.round(cv.clientHeight * 0.4)]; }
  function ctrPaint() { document.body.classList.toggle('ctron', CTR); var q = ctrXY(); CROSS.style.left = q[0] + 'px'; CROSS.style.top = (cv.offsetTop + q[1]) + 'px'; }
  function ctrTap() {   // 가운데 = 점(가게·집계구)이 아니라 고른 단위(동·시군구·경찰서·지구대)
    var q = ctrXY(), m = M(q[0], q[1]), it = null, at = m; CTRAUTO = true;
    if (UNIT && UNIT !== 'dong') { var u = unitAtU(m); if (u) it = { kind: 'unit', u: u }; }
    if (!it) { var d = dongAtM(m); if (d) { it = { kind: 'dong', d: d }; at = d.c; } else { var d1 = nearAtM(m); if (d1) { it = { kind: 'near', d: d1 }; at = d1.c; } } }
    if (!it) { tap(q[0], q[1]); return; } TAPM = m; var sx = S(at); sel = { x: sx[0], y: sx[1], r: 6, it: it }; show(it); draw(); }
  CTRB.onclick = ctrTap;
  function ctrSoon() { if (!CTR || !CTRAUTO || !$('m2dCard').classList.contains('on')) return; clearTimeout(ctrT); ctrT = setTimeout(ctrTap, 450); }
  var ctrV = null; cv.addEventListener('pointerdown', function () { ctrV = [view.cx, view.cy, view.s]; });
  cv.addEventListener('pointerup', function () { if (ctrV && (ctrV[0] !== view.cx || ctrV[1] !== view.cy || ctrV[2] !== view.s)) ctrSoon(); });
  cv.addEventListener('wheel', ctrSoon);
  window.addEventListener('m2dresize', ctrPaint); window.addEventListener('resize', ctrPaint);

  // 밤·낮 — 자동(기기 설정) → 낮 → 밤
  var MQD = null; try { MQD = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)'); } catch (e) {}
  function dnApply() { var d = MODE === 'dark' || (MODE === 'auto' && MQD && MQD.matches); document.documentElement.classList.toggle('dark', !!d);
    var b = $('m2dDN'); if (b) { b.textContent = MODE === 'auto' ? '🌓' : MODE === 'dark' ? '🌙' : '☀️'; b.setAttribute('aria-label', '화면 밝기 — 지금 ' + (MODE === 'auto' ? '자동(기기 설정)' : MODE === 'dark' ? '밤' : '낮')); b.title = b.getAttribute('aria-label'); }
    var mt = document.querySelector('meta[name="theme-color"]'); if (mt) mt.setAttribute('content', d ? '#0f1624' : '#ffffff'); draw(); }
  function toast(t) { var el = $('m2dToast'); if (!el) { el = document.createElement('div'); el.id = 'm2dToast'; el.setAttribute('role', 'status'); document.body.appendChild(el); } el.textContent = t; el.classList.add('on'); clearTimeout(toast.t); toast.t = setTimeout(function () { el.classList.remove('on'); }, 1600); }
  if ($('m2dDN')) $('m2dDN').onclick = function () { MODE = MODE === 'auto' ? 'light' : MODE === 'light' ? 'dark' : 'auto'; try { localStorage.setItem('tg_map2d_mode', MODE); } catch (e) {} dnApply(); toast(MODE === 'auto' ? '🌓 자동 — 기기 설정을 따른다' : MODE === 'dark' ? '🌙 밤 화면' : '☀️ 낮 화면'); };
  if (MQD && MQD.addEventListener) MQD.addEventListener('change', function () { if (MODE === 'auto') dnApply(); });

  // 처음 쓸 때 세 걸음 — ① 누르면 볼 단위 ② 기초 인구 ③ 업무(대분류 → 중분류)
  var ONB = { step: 1, unit: 'dong', ctr: false, pop: ['jgg', 'live250', 'lpop'], mids: [] };
  var POPK = [['jgg', '🧩 주민·가구·사업체', '집계구(동보다 작은 칸) 인구·가구·주택·사업체 — 전국'], ['live250', '👥 그 시각 생활인구', '250m 칸 · 서울 · 시간대별(통신 자료로 추정)'], ['lpop', '👥 인구감소지역 생활인구', '시군구 · 월별 · 체류 인구'], ['fdong', '🌏 외국인주민 비율', '읍면동 · 전국 · 근로자·결혼이민·유학생']];
  function onbOpen() {
    ONB.step = 1; ONB.unit = UNIT || 'dong'; ONB.ctr = CTR; ONB.mids = [];
    var el = $('m2dOnb'); if (!el) { el = document.createElement('div'); el.id = 'm2dOnb'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); el.setAttribute('aria-label', '처음 안내'); document.body.appendChild(el); el.addEventListener('click', onbClick); }
    el.classList.add('on'); onbPaint(); }
  function onbPaint() {
    var el = $('m2dOnb'), st = ONB.step, h = '<div class="sh"><div class="dots">' + [1, 2, 3].map(function (i) { return '<i class="' + (i === st ? 'on' : i < st ? 'done' : '') + '"></i>'; }).join('') + '</div><span>' + st + ' / 3</span><button data-o="skip" class="lnk">건너뛰기</button></div>';
    if (st === 1) {
      h += '<h2>지도를 누르면 무엇을 볼까요?</h2><p class="sub">나중에 「🗂 레이어」 판 맨 위에서 언제든 바꿀 수 있습니다.</p><div class="opts">' +
        [['dong', '🏘', '읍면동 단위', '동 하나씩 자세히 — 인구·가게·사고·이동'], ['sgg', '🗂', '시군구 단위', '구·시·군 전체를 한 장으로 — 동 순위·비교'], ['ctr', '📍', '지도 가운데 기준', '지도를 옮기면 십자(+) 아래 동을 바로 보여 줌']].map(function (o) {
          var act = o[0] === 'ctr' ? ONB.ctr : (!ONB.ctr && ONB.unit === o[0]); return '<button data-o="u:' + o[0] + '" class="opt' + (act ? ' on' : '') + '"><em>' + o[1] + '</em><b>' + o[2] + '</b><small>' + o[3] + '</small></button>'; }).join('') + '</div>' +
        '<div class="more"><span>경찰 단위로 보기</span><button data-o="u:ps" class="' + (ONB.unit === 'ps' && !ONB.ctr ? 'on' : '') + '">🚓 경찰서 관할</button><button data-o="u:pb" class="' + (ONB.unit === 'pb' && !ONB.ctr ? 'on' : '') + '">👮 지구대 구역(근사)</button></div>';
    } else if (st === 2) {
      h += '<h2>먼저 사람부터 — 기초 인구</h2><p class="sub">그 지역을 아는 첫걸음입니다. 동을 누르면 남녀·연령 피라미드와 가구·주택이 같이 나옵니다.</p><div class="opts chk">' +
        POPK.map(function (o) { var act = ONB.pop.indexOf(o[0]) >= 0; return '<button data-o="p:' + o[0] + '" class="opt' + (act ? ' on' : '') + '" aria-pressed="' + act + '"><em>' + (act ? '✓' : '') + '</em><b>' + o[1] + '</b><small>' + o[2] + '</small></button>'; }).join('') + '</div>';
    } else {
      h += '<h2>어떤 일에 쓰시나요?</h2><p class="sub">큰 묶음 → 작은 묶음. 여러 개 골라도 됩니다(고른 것의 기본 레이어가 켜짐).</p>' +
        CATS.filter(function (c) { return c[2] && c[0] !== 'base'; }).map(function (c) { return '<div class="grp"><b>' + c[1] + '</b><div>' + c[2].map(function (m) { var k = c[0] + '|' + m[0], act = ONB.mids.indexOf(k) >= 0; return '<button data-o="m:' + k + '" class="' + (act ? 'on' : '') + '" aria-pressed="' + act + '">' + m[1] + '</button>'; }).join('') + '</div></div>'; }).join('');
    }
    h += '<div class="nav">' + (st > 1 ? '<button data-o="prev">← 이전</button>' : '<span></span>') + '<button data-o="' + (st < 3 ? 'next' : 'done') + '" class="pri">' + (st < 3 ? '다음 →' : '지도 보기') + '</button></div>';
    el.innerHTML = '<div class="sheet">' + h + '</div>'; }
  function onbClick(e) {
    if (e.target.id === 'm2dOnb') return; var b = e.target.closest('[data-o]'); if (!b) return; var o = b.getAttribute('data-o');
    if (o === 'skip') { onbClose(); return; }
    if (o === 'prev') { ONB.step--; onbPaint(); return; }
    if (o === 'next') { ONB.step++; onbPaint(); return; }
    if (o === 'done') { onbDone(); return; }
    var v = o.slice(2);
    if (o[0] === 'u') { if (v === 'ctr') { ONB.ctr = true; ONB.unit = 'dong'; } else { ONB.ctr = false; ONB.unit = v; } }
    else if (o[0] === 'p') { var i = ONB.pop.indexOf(v); if (i >= 0) ONB.pop.splice(i, 1); else ONB.pop.push(v); }
    else if (o[0] === 'm') { var j = ONB.mids.indexOf(v); if (j >= 0) ONB.mids.splice(j, 1); else ONB.mids.push(v); }
    onbPaint(); }
  function onbClose() { var el = $('m2dOnb'); if (el) el.classList.remove('on'); try { localStorage.setItem('tg_map2d_onb', '1'); } catch (e) {} }
  function onbDone() {
    LAYERS.forEach(function (l) { if (KEEP.indexOf(l[0]) < 0) on[l[0]] = false; }); on.dong = true; on.road = true; on.base = true;
    ONB.pop.forEach(function (k) { if (hasL(k)) on[k] = true; });
    ONB.mids.forEach(function (k) { var a = k.split('|'), m = catMid(a[0], a[1]); if (m) m[3].forEach(function (q) { if (hasL(q)) on[q] = true; }); });
    if (ONB.mids.length) { var a0 = ONB.mids[0].split('|'); CAT = a0[0]; MID = a0[1]; } else { CAT = 'people'; MID = 'pop'; }
    try { localStorage.setItem('tg_map2d_cat', CAT); localStorage.setItem('tg_map2d_mid', MID); } catch (e) {}
    CTR = ONB.ctr; try { localStorage.setItem('tg_map2d_ctr', CTR ? '1' : '0'); } catch (e) {}
    onbClose(); unitSet(ONB.unit); REG.mode = ONB.unit; ctrPaint(); summary();
    toast(CTR ? '📍 지도를 옮기고 「가운데 보기」를 누르세요' : '지도에서 ' + (UNITS.filter(function (u) { return u[0] === UNIT; })[0] || ['', '동'])[1].replace(/^\S+ /, '') + '을(를) 누르세요'); }

  // ---------- v2.20.0 📍 지역 고르기 — 소유자 「행정구역 단위로 · 경찰서 관할로 · 지구대 파출소 별로 지역을 선택」 ----------
  var REG = { mode: UNIT || 'dong', a: null, b: null };
  var RGEL = document.createElement('div'); RGEL.id = 'm2dReg'; RGEL.setAttribute('role', 'dialog'); RGEL.setAttribute('aria-label', '지역 고르기'); document.body.appendChild(RGEL);
  function regOpen(f) { RGEL.classList.toggle('on', f); if (f) { $('m2dPanel').classList.remove('on'); if ((REG.mode === 'ps' || REG.mode === 'pb') && !POL2) polLoad().then(regPaint); regPaint(); } var b = $('m2dRegB'); if (b) b.setAttribute('aria-expanded', f ? 'true' : 'false'); }
  function kSort(a, b) { return String(a).localeCompare(String(b), 'ko'); }
  function sidoName(code) { return (SIDO_FULL[code] || code); }
  function regFit(box, sMin) { var a = P(box[0], box[3]), b = P(box[2], box[1]), w = Math.abs(b[0] - a[0]), h = Math.abs(b[1] - a[1]); view.cx = (a[0] + b[0]) / 2; view.cy = (a[1] + b[1]) / 2;
    view.s = Math.max(0.006, Math.min(sMin || 1, Math.min(cv.clientWidth / (w * 1.08 || 1), cv.clientHeight * 0.55 / (h * 1.08 || 1)))); view.cy += cv.clientHeight * 0.18 / view.s; }
  function regShow(it, p) { var s0 = S(p); TAPM = p; sel = { x: s0[0], y: s0[1], r: 8, it: it }; show(it); draw(); if (window.innerWidth < 760) regOpen(false); }
  function regPaint() {
    var m = REG.mode, h = '<div class="ph"><b>📍 지역 고르기</b><button class="x" data-rg="x">닫기</button></div>';
    h += '<div class="seg">' + [['dong', '🏘 읍면동'], ['sgg', '🗂 시군구'], ['ps', '🚓 경찰서 관할'], ['pb', '👮 지구대·파출소']].map(function (u) { return '<button data-rgm="' + u[0] + '" class="' + (m === u[0] ? 'on' : '') + '">' + u[1] + '</button>'; }).join('') + '</div>';
    h += '<p class="rgn">고른 단위로 지도를 누를 때도 카드가 뜬다 · <button data-ctr="1" class="ctr' + (CTR ? ' on' : '') + '">📍 지도 가운데 기준 ' + (CTR ? '켬' : '끔') + '</button></p>';
    var crumbs = [], list = '';
    function chips(arr, attr) { return '<div class="rgl">' + arr.map(function (x) { return '<button ' + attr + '="' + esc(x[0]) + '">' + esc(x[1]) + (x[2] ? ' <small>' + esc(x[2]) + '</small>' : '') + '</button>'; }).join('') + '</div>'; }
    if (m === 'dong' || m === 'sgg') {
      var G = rIdx(); if (!G.length) list = '<p class="rgn">지역 목록을 받는 중…</p>';
      else if (!REG.a) { var sd = {}; G.forEach(function (g) { sd[g.sido] = (sd[g.sido] || 0) + 1; }); list = '<div class="rgt">시·도</div>' + chips(Object.keys(sd).sort(function (a, b) { return kSort(sidoName(a), sidoName(b)); }).map(function (k) { return [k, sidoName(k), sd[k] + '']; }), 'data-rga'); }
      else { crumbs.push(['a', sidoName(REG.a)]);
        if (m === 'sgg') { var SG = SGG.map(function (x, i) { return [i, x]; }).filter(function (q) { return q[1].g.sido === sidoName(REG.a); }).sort(function (a, b) { return kSort(a[1].g.name, b[1].g.name); });
          list = '<div class="rgt">시·군·구 — 누르면 그 시군구 한 장</div>' + chips(SG.map(function (q) { return ['s' + q[0], q[1].g.name]; }), 'data-rgp'); }
        else if (!REG.b) { list = '<div class="rgt">시·군·구</div>' + chips(G.filter(function (g) { return g.sido === REG.a; }).sort(function (a, b) { return kSort(a.name, b.name); }).map(function (g) { return [g.gu, g.name, (g.d || []).length + '']; }), 'data-rgb'); }
        else { var g = G.filter(function (x) { return x.gu === REG.b; })[0]; crumbs.push(['b', g ? g.name : REG.b]);
          list = '<div class="rgt">읍·면·동 — 누르면 그 동으로</div><div class="rgl"><button data-rgp="g' + esc(REG.b) + '" class="all">🗂 ' + esc(g ? g.name : '') + ' 전체</button></div>' + chips(((g && g.d) || []).slice().sort(function (a, b) { return kSort(a[0], b[0]); }).map(function (x) { return ['d' + REG.b + '|' + x[0], x[0]]; }), 'data-rgp'); } } }
    else {
      if (!POL2) list = '<p class="rgn">경찰 관서 목록을 받는 중…</p>';
      else if (!REG.a) { var cg = {}; POL2.stations.forEach(function (st) { cg[st[5]] = (cg[st[5]] || 0) + 1; }); list = '<div class="rgt">시·도경찰청</div>' + chips(Object.keys(cg).sort(kSort).map(function (k) { return [k, k.replace(/경찰청$/, ''), cg[k] + '서']; }), 'data-rga'); }
      else { crumbs.push(['a', REG.a]); var ST = POL2.stations.filter(function (st) { return st[5] === REG.a; }).sort(function (a, b) { return kSort(a[1], b[1]); });
        if (m === 'ps') list = '<div class="rgt">경찰서 — 누르면 그 관할 한 장</div>' + chips(ST.map(function (st) { return ['p' + st[0], st[1].replace(/경찰서$/, '서')]; }), 'data-rgp');
        else if (!REG.b) list = '<div class="rgt">경찰서</div>' + chips(ST.map(function (st) { var n = POL2.pbox.filter(function (b) { return b[6] === st[0]; }).length; return [st[0], st[1].replace(/경찰서$/, '서'), n + '곳']; }), 'data-rgb');
        else { var s1 = POL2.byI[+REG.b]; crumbs.push(['b', s1 ? s1[1] : REG.b]);
          list = '<div class="rgt">지구대·파출소 — 누르면 그 구역(근사) 한 장</div><div class="rgl"><button data-rgp="p' + esc(REG.b) + '" class="all">🚓 ' + esc(s1 ? s1[1] : '') + ' 관할 전체</button></div>' + chips(POL2.pbox.map(function (b, i) { return [i, b]; }).filter(function (q) { return q[1][6] === +REG.b; }).sort(function (a, b) { return kSort(a[1][0], b[1][0]); }).map(function (q) { return ['b' + q[0], q[1][0] + (q[1][1] ? ' 파출소' : ' 지구대')]; }), 'data-rgp'); } } }
    if (crumbs.length) h += '<div class="crm"><button data-rgc="0">전국</button>' + crumbs.map(function (c, i) { return '<span>›</span><button data-rgc="' + (i + 1) + '">' + esc(c[1]) + '</button>'; }).join('') + '</div>';
    RGEL.innerHTML = '<div class="rgw">' + h + list + '</div>'; }
  RGEL.addEventListener('click', function (e) { var b = e.target.closest('button'); if (!b) return; var v;
    if (b.getAttribute('data-rg') === 'x') { regOpen(false); return; }
    if (b.getAttribute('data-ctr')) { ctrSet(!CTR); regPaint(); return; }
    if ((v = b.getAttribute('data-rgm'))) { var pol = v === 'ps' || v === 'pb', wasPol = REG.mode === 'ps' || REG.mode === 'pb'; REG.mode = v; if (pol !== wasPol) REG.a = null; REG.b = null; unitSet(v); if (pol && !POL2) polLoad().then(regPaint); regPaint(); return; }
    if ((v = b.getAttribute('data-rgc'))) { if (v === '0') { REG.a = null; REG.b = null; } else if (v === '1') REG.b = null; regPaint(); return; }
    if ((v = b.getAttribute('data-rga'))) { REG.a = v; REG.b = null; regPaint(); return; }
    if ((v = b.getAttribute('data-rgb'))) { REG.b = v; regPaint(); return; }
    if ((v = b.getAttribute('data-rgp'))) { var t = v[0], r = v.slice(1);
      if (t === 's') { var i = +r, G = SGG[i]; var bx = [1e9, 1e9, -1e9, -1e9]; G.rings.forEach(function (rg) { rg.forEach(function (q) { var ll = landLL(q); bx[0] = Math.min(bx[0], ll[0]); bx[1] = Math.min(bx[1], ll[1]); bx[2] = Math.max(bx[2], ll[0]); bx[3] = Math.max(bx[3], ll[1]); }); }); regFit(bx); regShow({ kind: 'unit', u: { t: 'sgg', id: i } }, G.c); }
      else if (t === 'g') { var g = rIdx().filter(function (x) { return x.gu === r; })[0]; if (!g) return; regFit(g.box); var si = -1; SGG.forEach(function (q, k) { if (si < 0 && q.g.sido === sidoName(g.sido) && (g.name === q.g.name || g.name.indexOf(q.g.name) === 0)) si = k; }); var c = P((g.box[0] + g.box[2]) / 2, (g.box[1] + g.box[3]) / 2); if (si >= 0) regShow({ kind: 'unit', u: { t: 'sgg', id: si } }, c); else { draw(); if (window.innerWidth < 760) regOpen(false); } }
      else if (t === 'd') { var a = r.split('|'), g2 = rIdx().filter(function (x) { return x.gu === a[0]; })[0], x = g2 && (g2.d || []).filter(function (q) { return q[0] === a[1]; })[0]; if (!x) return; var p = P(x[1], x[2]); view.cx = p[0]; view.cy = p[1]; view.s = Math.max(0.09, Math.min(view.s, 0.3)); view.cy += cv.clientHeight * 0.18 / view.s; draw();
        var d = dongAtM(p); regShow(d ? { kind: 'dong', d: d } : { kind: 'rgo', gu: g2.gu, name: x[0], g: g2.name }, d ? d.c : p); }
      else if (t === 'p') { var st = POL2.byI[+r]; if (!st || !st.p) return; view.cx = st.p[0]; view.cy = st.p[1]; view.s = 0.045; view.cy += cv.clientHeight * 0.18 / view.s; if (!on.jurk) { on.jurk = true; saveOn(); paintLayers(); } regShow({ kind: 'unit', u: { t: 'ps', id: st[0] } }, st.p); }
      else if (t === 'b') { var bx2 = POL2.pbox[+r]; if (!bx2) return; view.cx = bx2.p[0]; view.cy = bx2.p[1]; view.s = 0.09; view.cy += cv.clientHeight * 0.18 / view.s; if (!on.upb) { on.upb = true; saveOn(); paintLayers(); } regShow({ kind: 'unit', u: { t: 'pb', id: +r } }, bx2.p); } } });
  if ($('m2dRegB')) $('m2dRegB').onclick = function () { regOpen(!RGEL.classList.contains('on')); };
  if ($('m2dFindB')) $('m2dFindB').onclick = function () { var on2 = !document.body.classList.contains('findon'); document.body.classList.toggle('findon', on2); this.setAttribute('aria-expanded', on2 ? 'true' : 'false'); if (on2) setTimeout(function () { $('m2dFind').focus(); }, 30); };
  cv.addEventListener('pointerdown', function () { if (window.innerWidth < 760) regOpen(false); });
  paintLayers(); ctrPaint(); dnApply();
  (function () { var hs = location.hash || ''; var seen = '1'; try { seen = localStorage.getItem('tg_map2d_onb'); } catch (e) {} if (seen || /(^|[#&])(lat|ly|here|gps)=/.test(hs)) return;
    if (document.documentElement.classList.contains('gated')) window.addEventListener('tggate', function () { setTimeout(onbOpen, 300); }); else setTimeout(onbOpen, 700); })();   // 처음 안내는 확인코드 관문 뒤에
  window.TGMap2D = { ledg: function () { return LEDG; }, field: function () { return FIELD; }, ftc: function () { return FTC; }, pnl: function () { return PNL; }, pnlOpen: pnlOpen, rp: function () { return RP; }, rpFind: rpFind, rpLong: rpLong, stk: function () { return STK; }, fdsg: function () { return fdSgg(); }, jiga: function () { return JIGA; }, regOpen: regOpen, reg: function () { return REG; }, land: function () { return LAND; }, onbOpen: onbOpen, unitSet: unitSet, midApply: midApply, cats: function () { return CATS; }, unit: function () { return UNIT; }, preFit: preFit, a10: function () { return A10; }, rad: function () { return RAD; }, radOpen: radOpen, radRun: radRun, rent: function () { return RENT; }, biz: function () { return BIZ; }, bizOpen: bizOpen, bizGo: bizGo, trd: function () { return TRD; }, rdong: function () { return RDONG; }, ridx: rIdx, osm: function () { return OSM; }, flow: function () { return FLOW; }, livep: function () { return LIVEP; }, setHour: setHour, preset: preset, PRESETS: PRESETS, summary: summary, salesNow: salesNow, crowdAt: crowdAt, nowH: function () { return nowH(); }, hashLayers: hashLayers, hour: spotHour, jur: function () { return JUR; }, tgis: function () { return TG; }, spots: function () { return SPOTS; }, saving: function () { return !HASHLY; }, report: function () { return REP; }, applyHash: applyHash, hits: function () { return hit; }, pub: function () { return PUB; }, openNow: openNow, liveNow: liveNow, layers: LAYERS, view: view, nodes: function () { return NODES; }, dongs: function () { return DONG; }, draw: draw, tap: tap, on: on, S: S, P: P };   // 검사·다른 페이지가 읽는 창구
})();
