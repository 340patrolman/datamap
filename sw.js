// 데이터 압축지도(datamap) 서비스워커 — 앱 파일을 미리 저장(설치형·오프라인)하고 새 판은 다음 실행 때 바꿔 끼운다.
// 바탕 조각(data/base/t/)과 「📥 지역 받기」로 받은 구 자료는 판과 상관없는 보관함 tg-tiles 에서 먼저 꺼낸다.
var CACHE = 'dm-v2.320.1-d20';
var TILES = 'tg-tiles';
var SLOW = 4000, QUICK = 1500, BAD = 0, DOC = 0;   // 먹통 대비 — 아래 fetch 마지막 갈래(앱 기준 · 가정)
var FILES = ['./', './index.html', './manifest.json', './js/map2d.js?v=2.320.1', './js/decide.js?v=7', './js/link.js?v=24', './js/travel-time.js?v=5', './js/sim-ui.js?v=32', './js/sim-area.js?v=19', './js/sim-pick.js?v=1', './js/sim-merge.js?v=3', './js/nowcast.js?v=1', './data/regions.json', './data/place-keys-seocho.json', './data/base/index.json', './data/base/ov.json', './data/base/sgg.json', './icon-192.png', './icon-512.png'];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(FILES); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) { return Promise.all(keys.filter(function (k) { return k.indexOf('dm-v') === 0 && k !== CACHE; })   // 자기 판 저장소(dm-v…)만 — 같은 도메인의 게임(tg-v…)·T-Book(gtw-app-v2)·tg-tiles 는 건드리지 않는다
    .map(function (k) { return caches.delete(k); })); }).then(function () { return self.clients.claim(); }));
});
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  if (e.request.url.indexOf(self.location.origin + '/') !== 0) return;   // 다른 사이트(브이월드 배경 조각)는 보관하지 않고 브라우저에 맡긴다
  if (e.request.url.indexOf('/data/base/t/') >= 0 || e.request.url.indexOf('/datamap-tiles/t/') >= 0) {   // v2.8.0 조각은 datamap-tiles 저장소
    e.respondWith(caches.open(TILES).then(function (c) { return c.match(e.request).then(function (hit) { return hit || fetch(e.request).then(function (res) { if (res.ok) c.put(e.request, res.clone()); return res; }); }); }));
    return;
  }
  /* 2026-11-11 (신호 세션 · 형님 「권고대로 계속 진행」 — 통신 끊긴 곳에서 다시 열기) 먹통 대비: 망을 먼저 받되 SLOW 초 안에 답이 없고 보관본이 있으면 보관본으로 답한다. 망 받기는 뒤에서 끝내 보관함을 갱신(다음에 열 때 새것).
     실측(실제 사이트 · 가르고): 완전히 끊기면 1초 만에 열리는데, 이어지기만 하고 답이 안 오면 새 문서 30초·길은 2분 넘게 안 나왔다(받기가 실패할 때까지 기다려서). 보관본이 없으면 종전대로 끝까지 기다린다.
     SLOW 4초 · 4초를 넘긴 뒤 60초 동안은 QUICK 1.5초(망이 나쁜 줄 아니까 줄줄이 4초씩 기다리지 않게) · 1.5초 안에 답이 오면 다시 4초로 — 앱 기준(가정).
     독립 검수 반영: ① 보관본은 저장한 열쇠 그대로를 먼저 찾고, 없을 때만 물음표 뒤를 떼고 찾되 가장 나중에 넣은 것(떼고 찾으면 가장 먼저 넣은 옛 판이 나온다) ② 판 표시(?v= · ?b=)가 붙은 주소는 늦었다고 다른 판 내용으로 답하지 않는다(망을 기다림 · 받기가 실패했을 때만 종전처럼 아무 판)
     ③ 화면 문서를 보관본으로 답했으면 20초 동안은 딸린 파일도 보관본 먼저(옛 문서 + 새 스크립트가 섞이지 않게) ④ 보관함 조회가 실패해도 요청이 매달리지 않는다 ⑤ 이미 보관본으로 답한 뒤 온 응답은 복사하지 않고 그대로 보관(큰 파일이 메모리에 겹쳐 남지 않게)
     ⑥ (둘째 검수) 화면 문서·판 표시 주소를 보관본으로 답했으면 늦게 온 응답은 보관하지 않는다 — 문서와 스크립트를 따로따로 갈아 끼우면 보관함 안에서 판이 어긋난다(문서는 새 판 · 그 판 스크립트는 없음 → 다음 먹통 때 다시 매달림). 4초 안에 답하는 망에서 열 때 문서·스크립트가 같이 새것이 된다.
     알고 갈 것: BAD 는 「4초를 넘겼고 보관본이 있어 그것으로 답했을 때」만 찍힌다 · 머리는 왔는데 본문이 멈추는 먹통은 못 잡는다(종전과 같음) · DOC·BAD 는 워커 하나가 지도·가르고 탭에 같이 쓴다 */
  var req = e.request, u9 = req.url, k9 = u9.indexOf('/data/live-') >= 0 ? u9.split('?')[0] : req;   /* v2.300.3 실시간 파일은 ?t= 를 떼고 한 줄로만 보관(주소마다 쌓이지 않게) */
  var VER = /[?&](v|b)=/.test(u9), done = false, KEEP = [], t0 = Date.now();
  var own = function (loose) { return caches.open(CACHE).then(function (c) { return c.match(k9).then(function (hit) { return hit || (loose ? c.matchAll(req, { ignoreSearch: true }).then(function (a) { return a[a.length - 1]; }) : undefined); }); }); };
  var held = function (failed) { var any = failed || !VER; return own(any).then(function (hit) { return hit || (any ? caches.match(req, { ignoreSearch: true }).then(function (h) { return h || caches.open(TILES).then(function (c) { return c.match(req, { ignoreSearch: true }); }); }) : undefined); }).catch(function () {}); };
  var net = fetch(req, { cache: 'no-cache' }).then(function (res) {
    if (Date.now() - t0 < QUICK) BAD = 0;
    if (res.ok && !(done && (VER || req.mode === 'navigate'))) { var copy = done ? res : res.clone(); KEEP.push(caches.open(CACHE).then(function (c) { return c.put(k9, copy); }).catch(function () {})); }
    return res;
  });
  e.respondWith(new Promise(function (ok) {
    var wait = Date.now() - DOC < 20000 ? 0 : Date.now() - BAD < 60000 ? QUICK : SLOW;
    var tm = setTimeout(function () { held(false).then(function (hit) { if (!hit || done) return; done = true; if (wait === SLOW) BAD = Date.now(); if (wait && req.mode === 'navigate') DOC = Date.now(); ok(hit); }); }, wait);
    net.then(function (res) { clearTimeout(tm); if (!done) { done = true; ok(res); } }, function () { clearTimeout(tm); if (done) return; held(true).then(function (hit) { if (!done) { done = true; ok(hit); } }); });
  }));
  e.waitUntil(net.then(function () { return Promise.all(KEEP); }, function () {}));
});
