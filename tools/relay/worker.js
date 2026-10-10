// 데이터 압축지도 「맛보기」 중계 — Cloudflare Workers(무료 플랜 · 하루 100,000건 · 요청마다 CPU 10ms)
// 소유자 2026-10-09 「API 키를 직접 넣는 것이 번거롭다 — 열쇠를 터치하면 맛보기로 접근 · 많이 쓸 사람은 직접 받으라」 → 권고안 승인
//
// 하는 일
//   1) 열쇠(ITS · 공공데이터포털 · 브이월드)는 이 Worker 의 비밀값(secret)에만 둔다 — 폰·저장소로 가지 않는다(브이월드만 예외: 아래 /vwkey)
//   2) 지도가 실제로 부르는 주소만 통과(ITS 3 · 공공데이터포털 16) — 그 밖은 404
//   3) 같은 요청은 1~10분 Cloudflare 캐시로 나눠 준다 → 100명이 봐도 원 기관에는 한 번
//   4) 접속 주소(IP)마다 하루 DAILY 번(기본 300) — 캐시 기반 셈이라 데이터센터마다 따로 센다(근사 · 맛보기라 충분)
//   5) Origin 이 ALLOW_ORIGINS 가 아니면 403 — 다른 사이트에서 이 중계를 가져다 쓰지 못하게(브라우저 기준 · curl 은 하루 한도로 막는다)
//
// 비밀값(wrangler secret put …): ITS_KEY · DG_KEY(공공데이터포털 일반 인증키 — 인코딩·디코딩 어느 쪽이든) · VW_KEY(브이월드 · 340patrolman.github.io 에 묶인 키)
// 설정값(wrangler.toml [vars]): ALLOW_ORIGINS · DAILY
// 받은 값은 저장하지 않는다(캐시는 몇 분 뒤 사라짐) · 기록(log)도 남기지 않는다
//
// v2(2026-10-10 · 소유자 「클라우드플레어에 키가 들어갔으니 서울시 데이터도 · 일반인에게 주는 실시간 데이터 활용」)
//   서울 갈래 넷을 더했다 — 서울시 API 는 http 만 열어서 https 지도가 직접 못 부르던 것들이다:
//     /seoul/<서비스>/<시작>/<끝>[/인자…]  서울 열린데이터광장(openapi.seoul.go.kr:8088) · 비밀값 SEOUL_KEY
//     /wsbus/<서비스>/<기능>?…             서울 버스(ws.bus.go.kr) · 비밀값 DG_KEY(공공데이터포털 — 서비스마다 활용신청)
//     /swsub/<역이름>                      서울 지하철 실시간 도착(swopenapi.seoul.go.kr) · 비밀값 SUBWAY_KEY(실시간 지하철 전용 키)
//     (T-Data V2X 신호는 중계에 두지 않는다 — 같은 API 가 키마다 5분에 한 번뿐이라 지도 사용자가 부르면 굽는 도구(tools/signal/spat-bake.py)가 막힌다)
//   /reach = 중계에서 원 기관에 닿는지 시험(키 없이 · 상태 코드만) — 새 갈래를 붙이기 전에 한 번 본다
//   ⚠ ITS(9443)·서울(8088)은 표준 포트가 아니다 — Worker 설정 › 런타임 › 「호환성 날짜」가 2024-09-02 뒤여야 그 포트로 나간다(앞이면 443 으로 가서 522)

const ITS_OK = { eventInfo: 120, trafficInfo: 120, cctvInfo: 600 };
const DG_OK = {
  '1360000/EqkInfoService/getEqkMsg': 300,
  '1360000/VilageFcstInfoService_2.0/getUltraSrtNcst': 600,
  '1360000/WthrWrnInfoService/getPwnStatus': 300,
  '1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList': 30,
  '1613000/BusLcInfoInqireService/getRouteAcctoBusLcList': 30,
  '1613000/BusSttnInfoInqireService/getCrdntPrxmtSttnList': 3600,
  '1613000/DmstcFlightNvgInfo/GetFlightOpratInfoList': 600,
  '1613000/SubwayInfo/GetKwrdFndSubwaySttnList': 86400,
  '1613000/SubwayInfo/GetSubwaySttnAcctoSchdulList': 3600,
  '6410000/busarrivalservice/v2/getBusArrivalListv2': 30,
  '6410000/buslocationservice/v2/getBusLocationListv2': 30,
  '6410000/busrouteservice/v2/getBusRouteStationListv2': 86400,
  '6410000/busstationservice/v2/getBusStationAroundListv2': 3600,
  'B551457/run/v2/travelerTrainRunInfo2': 60,
  'B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty': 600,
};
const SEOUL_OK = { citydata_ppltn: 300, citydata: 300, bikeList: 60, GetParkingInfo: 300, RealtimeCityAir: 600, AccInfo: 120, TrafficInfo: 120 };
const SEOUL_XML = { AccInfo: 1, TrafficInfo: 1 };   // 이 둘은 xml 만 준다
const WSBUS_OK = { 'arrive/getLowArrInfoByStId': 20, 'arrive/getArrInfoByRouteAll': 20, 'buspos/getBusPosByRtid': 20, 'stationinfo/getStationByPos': 3600, 'stationinfo/getStationByUid': 20, 'busRouteInfo/getStaionByRoute': 86400 };
const REACH = { its: 'https://openapi.its.go.kr:9443/', dg: 'https://apis.data.go.kr/', seoul: 'http://openapi.seoul.go.kr:8088/sample/json/bikeList/1/1/', wsbus: 'http://ws.bus.go.kr/api/rest/arrive/getLowArrInfoByStId', swsub: 'http://swopenapi.seoul.go.kr/api/subway/sample/json/realtimeStationArrival/0/1/%EC%84%9C%EC%9A%B8', td: 'https://t-data.seoul.go.kr/apig/apiman-gateway/tapi/v2xCrossroadMapInformation/1.0' };
const DROP = new Set(['apikey', 'servicekey', 'key']);

function json(o, status, cors) {
  return new Response(JSON.stringify(o), { status, headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' } });
}
function enc(x) { try { return encodeURIComponent(decodeURIComponent(x)); } catch (e) { return encodeURIComponent(x); } }
function kstDay() { return new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10); }

async function quota(ip, env, add) {
  const max = +(env.DAILY || 300), key = new Request('https://quota.relay/' + kstDay() + '/' + encodeURIComponent(ip)), c = caches.default;
  let n = 0; const r = await c.match(key); if (r) n = +(await r.text()) || 0;
  let blocked = false;
  if (add) { if (n >= max) blocked = true; else { n++; await c.put(key, new Response(String(n), { headers: { 'Cache-Control': 'max-age=90000' } })); } }
  return { used: n, max, left: max - n, blocked, day: kstDay() };
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url), origin = req.headers.get('Origin') || '';
    const allow = String(env.ALLOW_ORIGINS || 'https://340patrolman.github.io').split(',').map((s) => s.trim());
    const cors = { 'Access-Control-Allow-Origin': allow.includes(origin) ? origin : allow[0], 'Access-Control-Allow-Methods': 'GET, OPTIONS', 'Access-Control-Expose-Headers': 'X-Trial-Left, X-Trial-Max', 'Access-Control-Max-Age': '86400', Vary: 'Origin' };
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (req.method !== 'GET') return json({ err: 'GET 만 받는다' }, 405, cors);
    if (!allow.includes(origin)) return json({ err: '이 중계는 데이터 압축지도에서만 쓴다' }, 403, cors);
    const ip = req.headers.get('CF-Connecting-IP') || '0';
    const seg = url.pathname.replace(/^\/+/, '').split('/'), kind = seg.shift(), path = seg.join('/');

    if (kind === 'quota') return json({ ...(await quota(ip, env, false)), its: !!env.ITS_KEY, dg: !!env.DG_KEY, vw: !!env.VW_KEY, seoul: !!env.SEOUL_KEY, subway: !!env.SUBWAY_KEY, v: 2 }, 200, cors);
    if (kind === 'reach') {
      const out = {};
      await Promise.all(Object.entries(REACH).map(async ([k, u]) => {
        const t0 = Date.now(), ac = new AbortController(), tm = setTimeout(() => ac.abort(), 7000);
        try { const r = await fetch(u, { signal: ac.signal, headers: { Accept: '*/*' } }); out[k] = { ok: true, status: r.status, ms: Date.now() - t0 }; }
        catch (e) { out[k] = { ok: false, why: String(e && e.message || e), ms: Date.now() - t0 }; }
        clearTimeout(tm);
      }));
      return json(out, 200, cors);
    }

    let up = null, ttl = 120;
    const ps = new URLSearchParams(); [...url.searchParams.entries()].filter(([k]) => !DROP.has(k.toLowerCase())).sort().forEach(([k, v]) => ps.append(k, v));
    if (kind === 'its' && ITS_OK[path] && env.ITS_KEY) { ttl = ITS_OK[path]; up = 'https://openapi.its.go.kr:9443/' + path + '?apiKey=' + encodeURIComponent(env.ITS_KEY) + '&' + ps; }
    else if (kind === 'dg' && DG_OK[path] && env.DG_KEY) { ttl = DG_OK[path]; const k = env.DG_KEY.indexOf('%') >= 0 ? env.DG_KEY : encodeURIComponent(env.DG_KEY); up = 'https://apis.data.go.kr/' + path + '?serviceKey=' + k + '&' + ps; }
    else if (kind === 'seoul' && SEOUL_OK[seg[0]] && env.SEOUL_KEY && /^\d+$/.test(seg[1] || '') && /^\d+$/.test(seg[2] || '') && +seg[2] - +seg[1] < 1000) {
      ttl = SEOUL_OK[seg[0]]; up = 'http://openapi.seoul.go.kr:8088/' + encodeURIComponent(env.SEOUL_KEY) + '/' + (SEOUL_XML[seg[0]] ? 'xml' : 'json') + '/' + seg.map(enc).join('/'); }
    else if (kind === 'wsbus' && WSBUS_OK[path] && env.DG_KEY) { ttl = WSBUS_OK[path]; const k2 = env.DG_KEY.indexOf('%') >= 0 ? env.DG_KEY : encodeURIComponent(env.DG_KEY); ps.set('resultType', 'json'); up = 'http://ws.bus.go.kr/api/rest/' + path + '?serviceKey=' + k2 + '&' + ps; }
    else if (kind === 'swsub' && seg.length === 1 && seg[0] && env.SUBWAY_KEY) { ttl = 20; up = 'http://swopenapi.seoul.go.kr/api/subway/' + encodeURIComponent(env.SUBWAY_KEY) + '/json/realtimeStationArrival/0/12/' + enc(seg[0]); }
    else if (kind === 'vwkey' && env.VW_KEY) {
      const q = await quota(ip, env, true); if (q.blocked) return json({ err: '맛보기 하루 한도', ...q }, 429, cors);
      return json({ key: env.VW_KEY, note: '브이월드 키는 340patrolman.github.io 에 묶여 있다 — 다른 주소에서는 열리지 않는다', ...q }, 200, cors);
    }
    if (!up) return json({ err: '모르는 주소이거나 이 중계에 그 열쇠가 없다', kind, path }, 404, cors);

    const q = await quota(ip, env, true);
    if (q.blocked) {
      const ck0 = await caches.default.match(new Request('https://cache.relay/' + kind + '/' + path + '?' + ps));
      if (!ck0) return json({ err: '맛보기 하루 한도를 다 썼다 — 많이 쓰면 열쇠를 직접 받아 넣는다', ...q }, 429, cors);
    }
    const ck = new Request('https://cache.relay/' + kind + '/' + path + '?' + ps), cache = caches.default;
    let res = await cache.match(ck);
    if (!res) {
      let r;
      try { r = await fetch(up, { headers: { Accept: 'application/json, text/xml;q=0.9, */*;q=0.5' } }); }
      catch (e) { return json({ err: '원 기관에 닿지 못했다', why: String(e && e.message || e) }, 502, cors); }
      const body = await r.arrayBuffer();
      res = new Response(body, { status: r.status, headers: { 'Content-Type': r.headers.get('Content-Type') || 'application/json; charset=utf-8', 'Cache-Control': 'public, max-age=' + ttl } });
      if (r.ok) ctx.waitUntil(cache.put(ck, res.clone()));
    }
    const out = new Response(res.body, res);
    Object.entries(cors).forEach(([k, v]) => out.headers.set(k, v));
    out.headers.set('Cache-Control', 'no-store'); out.headers.set('X-Trial-Left', String(Math.max(0, q.left))); out.headers.set('X-Trial-Max', String(q.max));
    return out;
  },
};
