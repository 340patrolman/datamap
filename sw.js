// 데이터 압축지도(datamap) 서비스워커 — 앱 파일을 미리 저장(설치형·오프라인)하고 새 판은 다음 실행 때 바꿔 끼운다.
// 바탕 조각(data/base/t/)과 「📥 지역 받기」로 받은 구 자료는 판과 상관없는 보관함 tg-tiles 에서 먼저 꺼낸다.
// 쓰면서 받은 파일(가르고 파일·길 묶음·신호 칸·구 자료)은 판과 상관없는 보관함 dm-run-1 에 둔다 — 판 보관함(dm-v…)에는 미리 받는 FILES 만. 고치면 tools/check/swcheck.py 를 돌린다.
var CACHE = 'dm-v2.321.1-d20';
var TILES = 'tg-tiles';
var RUN = 'dm-run-1', KEEPN = 2000;   // 쓰면서 받은 것 — 판이 바뀌어도 남긴다(activate 는 dm-v… 만 지운다) · 아래 ⑦
var SLOW = 4000, QUICK = 1500, BAD = 0, DOC = 0;   // 먹통 대비 — 아래 fetch 마지막 갈래(앱 기준 · 가정)
var FILES = ['./', './index.html', './manifest.json', './js/map2d.js?v=2.321.1', './js/decide.js?v=7', './js/link.js?v=24', './js/travel-time.js?v=5', './js/sim-ui.js?v=32', './js/sim-area.js?v=19', './js/sim-pick.js?v=1', './js/sim-merge.js?v=3', './js/nowcast.js?v=1', './data/regions.json', './data/place-keys-seocho.json', './data/base/index.json', './data/base/ov.json', './data/base/sgg.json', './icon-192.png', './icon-512.png'];
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(FILES); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) { return Promise.all(keys.filter(function (k) { return k.indexOf('dm-v') === 0 && k !== CACHE; })   // 자기 판 저장소(dm-v…)만 — 같은 도메인의 게임(tg-v…)·T-Book(gtw-app-v2)·tg-tiles 는 건드리지 않는다
    .map(function (k) { return caches.delete(k); })); }).then(function () { return self.clients.claim(); }));
});
/* RUN 줄이기 — 자료(/data/)만 센다. n 줄을 넘으면 오래 넣은 것부터 지워 80%로. 문서·스크립트·가르고 길 묶음과 길 칸(gargo/)은 건드리지 않는다(지도에서 구 자료를 많이 봐도 가르고 본체가 밀려 지워지지 않게). */
function prune(n) { return caches.open(RUN).then(function (c) { return c.keys().then(function (ks) { ks = ks.filter(function (q) { return q.url.indexOf('/data/') >= 0; }); return ks.length > n ? Promise.all(ks.slice(0, ks.length - Math.round(n * 0.8)).map(function (q) { return c.delete(q); })) : 0; }); }).catch(function () {}); }
self.addEventListener('message', function (e) { if (e.data && e.data.dmPrune) e.waitUntil(prune(+e.data.dmPrune)); });   // 검사용(tools/check/swcheck.py) — 줄이기를 지금 한 번 돌린다
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
  /* ⑦ (2026-11-11 낮 · 신호 세션) 쓰면서 받은 것은 판과 상관없는 보관함 RUN 에 둔다 — 지도 판이 바뀌면(하루에도 여러 번) 판 보관함이 새로 만들어져 가르고 파일·길 묶음·신호 칸이 통째로 사라졌고, 그 직후 먹통·끊김이면 가르고가 안 열렸다(실측: 통신 좋은 곳에서 두 번 열어야 다시 채워짐).
     열쇠: 판 표시(?v= · ?b=) 주소는 # 뒤만 뗀 주소 그대로(같은 길의 다른 판은 새 판을 넣을 때 지운다) · 그 밖은 물음표·# 뒤를 모두 뗀 길(같은 파일이 주소마다 쌓이지 않게 · 가르고를 여는 주소의 # 뒤에 실리는 출발·목적지 좌표가 보관함 열쇠로 남지 않게).
     셋째 검수 반영: 같은 길의 다른 판은 가장 나중 하나를 더 남긴다(같은 파일을 다른 판 표시로 부르는 곳이 있다 — ontology-core/query.js ?v=2·?v=3) · 판 보관함에서 찾아 답한 것은 RUN 에도 넣는다(RUN 이 「마지막 화면이 실제로 쓴 것」을 갖게 — 안 그러면 다음 판 올림 뒤 그 판 스크립트가 어디에도 없다) · 줄이기는 자료(/data/)만(문서·스크립트·가르고 길 묶음·길 칸은 안 지운다).
     찾는 차례: RUN 정확 일치 → 판 보관함(미리 받은 FILES) 정확 일치 → (받기가 실패했거나 판 표시가 없는 주소만) 물음표 뒤 떼고 RUN 의 가장 나중 것 → 아무 보관함 → tg-tiles. RUN 의 자료가 KEEPN 줄을 넘으면 오래 넣은 것부터 지운다(받을 때마다 다시 넣으므로 자주 쓰는 것은 뒤에 있다 · 줄 수만 본다 — 크기는 안 봄). */
  var req = e.request, u0 = req.url.split('#')[0], VER = /[?&](v|b)=/.test(u0), p0 = u0.split('?')[0], k9 = VER ? u0 : p0, done = false, KEEP = [], t0 = Date.now();
  var own = function (loose) { return caches.open(RUN).then(function (c) { return c.match(k9).then(function (hit) { return hit || caches.open(CACHE).then(function (c2) { return c2.match(k9); }).then(function (h2) { if (h2 && !done) KEEP.push(keep(h2.clone())); return h2; }); }).then(function (hit) { return hit || (loose ? c.matchAll(p0, { ignoreSearch: true }).then(function (a) { return a[a.length - 1]; }) : undefined); }); }); };
  var held = function (failed) { var any = failed || !VER; return own(any).then(function (hit) { return hit || (any ? caches.match(req, { ignoreSearch: true }).then(function (h) { return h || caches.open(TILES).then(function (c) { return c.match(req, { ignoreSearch: true }); }); }) : undefined); }).catch(function () {}); };
  var keep = function (res) { return caches.open(RUN).then(function (c) { return c.put(k9, res).then(function () { return VER ? c.keys(p0, { ignoreSearch: true }).then(function (ks) { ks = ks.filter(function (q) { return q.url !== u0; }); return Promise.all(ks.slice(0, Math.max(0, ks.length - 1)).map(function (q) { return c.delete(q); })); }) : 0; }).then(function () { return Math.random() < 0.02 ? prune(KEEPN) : 0; }); }).catch(function () {}); };
  var net = fetch(req, { cache: 'no-cache' }).then(function (res) {
    if (Date.now() - t0 < QUICK) BAD = 0;
    if (res.ok && !(done && (VER || req.mode === 'navigate'))) KEEP.push(keep(done ? res : res.clone()));
    return res;
  });
  var answered = new Promise(function (ok) {
    var nav = req.mode === 'navigate', wait = !nav && Date.now() - DOC < 20000 ? 0 : Date.now() - BAD < 60000 ? QUICK : SLOW;   /* 새로 여는 문서 자체는 20초 창과 상관없이 망을 먼저 본다 · 망에서 제때 오면 창을 끈다(망이 살아났는데 딸린 파일이 계속 보관본으로 나가지 않게) */
    var tm = setTimeout(function () { held(false).then(function (hit) { if (!hit || done) return; done = true; if (wait === SLOW) BAD = Date.now(); if (nav) DOC = Date.now(); ok(hit); }); }, wait);
    net.then(function (res) { clearTimeout(tm); if (!done) { done = true; if (nav) DOC = 0; ok(res); } }, function () { clearTimeout(tm); if (done) return; held(true).then(function (hit) { if (!done) { done = true; ok(hit); } }); });
  });
  e.respondWith(answered);
  e.waitUntil(Promise.all([answered, net.then(function () {}, function () {})]).then(function () { return Promise.all(KEEP); }, function () { return Promise.all(KEEP); }));   /* 화면에 답한 뒤(끊김 갈래에서 보관본 사본을 넣는 것까지) 기다린다 */
});
