# 🎟 맛보기 중계(Cloudflare Workers) — 형님 PC에서 한 번 배포

열쇠(ITS · 공공데이터포털 · 브이월드)를 **Cloudflare 의 비밀값**에만 두고, 지도는 이 중계를 거쳐 실시간 자료를 받는다.
폰·저장소에는 열쇠가 가지 않는다(브이월드만 340patrolman.github.io 에 묶인 키라 맛보기 중 메모리로 받는다).

## ⚠ 돈 안 나가게 — 먼저 읽기(cloudflare-docs pricing.mdx·limits.mdx 원문 확인 2026-10-09)
- 가입하면 **Workers Free(무료)** 가 기본이다. 무료는 하루 100,000건을 넘으면 그날(UTC 자정까지) **Error 1027 로 멈출 뿐 청구되지 않는다.**
- 돈은 **Workers Paid(월 최소 $5)** 로 올렸을 때만 나간다 → **「Upgrade」·「Workers Paid」·「Purchase」 단추를 누르지 않는다 · 결제 수단(카드)을 등록하지 않는다.**
- 이 중계는 KV·R2·D1·Durable Objects·Queues 같은 유료가 될 수 있는 기능을 쓰지 않는다(Workers 와 무료 캐시만).
- 도메인 구입·연결도 필요 없다(`*.workers.dev` 무료 주소를 쓴다).
- 가입 뒤 한 번: 대시보드 → 「Billing」(결제)에서 플랜이 Free 이고 결제 수단이 비어 있는지 확인.

| 항목 | 값 |
|---|---|
| 무료 한도(Cloudflare) | 하루 100,000건 · 요청마다 CPU 10ms (cloudflare-docs limits.mdx 2026-10 확인) |
| 맛보기 한 번 | 30분(`data/relay.json` 의 `min`) |
| 하루 횟수 | 접속 주소(IP)마다 300번(`wrangler.toml` 의 `DAILY`) — 데이터센터마다 따로 세는 근사 |
| 캐시 | 같은 요청은 30초~하루(주소마다 다름 · `worker.js` 맨 위 표)를 나눠 씀 → 원 기관 호출이 크게 준다 |
| 막는 것 | 지도(340patrolman.github.io)가 아닌 사이트에서 부르기 · 목록 밖 주소 · 사용자가 끼워 보낸 키 |

## 1. 준비(한 번)
1. https://dash.cloudflare.com 무료 가입(이메일 인증까지).
2. PC 에 Node.js LTS 가 없으면 설치(https://nodejs.org).
3. 명령 창(PowerShell)에서:
   ```
   cd <datamap 저장소>\tools\relay
   npx wrangler login        ← 브라우저가 열리면 「Allow」
   ```

## 2. 열쇠 넣기 — 화면에 붙여 넣는다(파일·명령 줄에 남기지 않는다)
```
npx wrangler secret put ITS_KEY     ← 국가교통정보센터 운영키
npx wrangler secret put DG_KEY      ← 공공데이터포털 일반 인증키(인코딩·디코딩 어느 쪽이든)
npx wrangler secret put VW_KEY      ← 브이월드 키(340patrolman.github.io 에 묶인 것)
```
키 원본은 `07_API키\keys.json` 에 있다. 셋 중 넣지 않은 것은 맛보기에서 그 갈래만 빠진다.

## 3. 배포
```
npx wrangler deploy
```
끝에 `https://datamap-relay.<계정이름>.workers.dev` 주소가 나온다 — **이 주소를 Claude Code 에 알려 준다**(지도 `data/relay.json` 에 넣는다).

## 4. 첫 시험(꼭) — 정부 API 가 Cloudflare 에서 오는 호출을 받는지
문서로 확인하지 못한 두 가지: ① ITS 는 9443 포트 — Worker 가 그 포트로 나갈 수 있는지 ② 정부 API 가 Cloudflare 주소를 막는지.
PowerShell:
```
$o=@{Origin='https://340patrolman.github.io'}
irm 'https://datamap-relay.<계정이름>.workers.dev/quota' -Headers $o
irm 'https://datamap-relay.<계정이름>.workers.dev/its/eventInfo?type=all&eventType=all&minX=126.8&maxX=127.2&minY=37.4&maxY=37.7&getType=json' -Headers $o
irm 'https://datamap-relay.<계정이름>.workers.dev/dg/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?sidoName=서울&returnType=json&numOfRows=5&pageNo=1&ver=1.0' -Headers $o
```
- `quota` 가 `its: true, dg: true, vw: true` 면 열쇠가 들어간 것.
- ITS·공공데이터가 자료를 주면 성공. **`원 기관에 닿지 못했다`·HTTP 403 이면 그 결과를 그대로 Claude Code 에 붙여 준다**(다른 길을 찾는다).

## 5. 바꾸기
- 하루 횟수: `wrangler.toml` 의 `DAILY` → `npx wrangler deploy`
- 맛보기 시간: 지도 저장소 `data/relay.json` 의 `min`
- 끄기: `data/relay.json` 을 지우면 지도에서 🎟 단추가 사라진다(중계는 그대로 두어도 된다) · 완전히 끄려면 Cloudflare 대시보드에서 Worker 삭제
- 열쇠 바꾸기: 2번을 다시

## 6. 지켜볼 것
- Cloudflare 대시보드 → Workers → datamap-relay → 「Metrics」: 하루 요청 수 · 오류
- ITS 운영키 월 10,000건 · 공공데이터포털 서비스마다 하루 한도 — 캐시 덕에 사람 수보다 훨씬 적게 쓰지만, 많이 늘면 `DAILY` 를 낮춘다

## 7. 배포 기록 · v2 올리기(2026-10-10)
- **배포됨**: `https://datamap-relay.knpthe1cop.workers.dev` (대시보드에서 만든 Worker · 비밀값 DG_KEY·ITS_KEY·VW_KEY) → 지도 `data/relay.json` 에 등록(v2.99.0).
- **첫 시험 결과(2026-10-10)**: 공공데이터포털(에어코리아·TAGO)·브이월드 키 = 통과 · 다른 사이트 Origin = 403 · 목록 밖 = 404 · **ITS = 522(중계에서 닿지 않음)** → `relay.json` 의 `"off": ["its"]` 로 맛보기에서 ITS 갈래만 뺐다.
  - ITS 는 9443 포트다. Worker 「설정 › 런타임 › 호환성 날짜」가 **2024-09-02 앞**이면 표준이 아닌 포트를 무시하고 443 으로 나가 522 가 된다(이 PC 에서 443 은 응답 없음 · 9443 은 응답) → 날짜를 오늘로 바꾸고 다시 시험. 그래도 522 면 ITS 쪽이 Cloudflare 주소를 받지 않는 것.
- **v2(서울 갈래)** — `worker.js` 가 `/seoul` · `/wsbus` · `/swsub` · `/td` · `/reach` 를 더 받는다(파일 맨 위 설명).
  1. 대시보드 → datamap-relay → 「코드 편집」 → `tools/relay/worker.js` 내용을 통째로 붙여 넣고 「배포」.
  2. 「설정 › 변수 및 비밀」에 비밀값 추가(없는 것은 그 갈래만 빠진다):
     - `SEOUL_KEY` — 서울 열린데이터광장 일반 인증키(keys.json `seoul`)
     - `TD_KEY` — 서울 교통빅데이터 T-Data 키(keys.json `t_data_seoul`)
     - `SUBWAY_KEY` — 서울 열린데이터광장 **실시간 지하철** 인증키(일반 키로는 ERROR-338 · data.seoul.go.kr 에서 따로 신청)
  3. 시험: `…/quota` 에 `seoul·td·subway: true, v: 2` · `…/reach` 가 갈래마다 `ok: true` 인지(Origin 머리말 필요).
- 2026-10-10 이 PC 에서 직접 불러 확인한 서울 자료: `citydata_ppltn`·`bikeList`·`RealtimeCityAir`·`GetParkingInfo`(json) · `AccInfo`·`TrafficInfo`(xml 만) · 서울 버스 `arrive/getLowArrInfoByStId`(승인됨) · `stationinfo/getStationByPos`(401 — 활용신청 필요) · 지하철 실시간(ERROR-338 — 전용 키 필요).
