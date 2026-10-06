// 데이터 압축지도(datamap) 서비스워커 — 앱 파일을 미리 저장(설치형·오프라인)하고 새 판은 다음 실행 때 바꿔 끼운다.
// 바탕 조각(data/base/t/)과 「📥 지역 받기」로 받은 구 자료는 판과 상관없는 보관함 tg-tiles 에서 먼저 꺼낸다.
var CACHE = 'dm-v2.27.0';
var TILES = 'tg-tiles';
var FILES = ['./', './index.html', './manifest.json', './js/map2d.js?v=2.27.0', './data/regions.json', './data/base/index.json', './data/base/ov.json', './data/base/sgg.json', './icon-192.png', './icon-512.png'];
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
  e.respondWith(fetch(e.request, { cache: 'no-cache' }).then(function (res) {
    var copy = res.clone(); caches.open(CACHE).then(function (c) { c.put(e.request, copy); }); return res;
  }).catch(function () { return caches.match(e.request, { ignoreSearch: true }).then(function (hit) { return hit || caches.open(TILES).then(function (c) { return c.match(e.request, { ignoreSearch: true }); }); }); }));
});
