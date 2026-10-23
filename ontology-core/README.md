# 교통 온톨로지 코어 v1 (ontology-core)

세 앱(T-Book · 데이터 압축지도 · 네비 가르고)이 같이 읽는 **객체·링크·질문 틀**. 의존성 0(JSON + 순수 JS · ES5) — 그래프DB·벡터DB·OWL 안 씀 · 서버 0 · 외부 호출 0.

- 객체 이름·ID 규칙은 `data/onto-schema.json`(수집기 쪽 세션이 `tools/onto/schema-bake.py` 로 굽는다)을 그대로 쓰고, 거기 없는 것(위반유형 VIO · 법규 항목 LAW · 판례 PREC · 조치 ACT · 근거기록 REC)만 `schema-ext.json` 에 둔다.
- 이 폴더 밖 파일은 고치지 않는다(읽기만).

## 파일

| 파일 | 하는 일 |
|---|---|
| `schema-ext.json` | 객체 타입·링크 타입·질문(q1~q5)·비슷함 항목·규칙 |
| `build.py` | 공개 자료 파일에서 서초구 한 장 `data/core-seocho.json` 을 굽는다(값은 원자료에서 다시 셈 · 링크마다 출처·등급) |
| `tools/tbook-extract.py` | T-Book 을 머리 없는 크롬으로 열어 범칙금 DB(LAWS)·판례(PRECDOC)를 **읽기만** 해 `src/tbook-law.json` 으로(글 그대로) |
| `query.js` | `new OntoCore(core)` → `q1(INT)` 왜 위험한가 · `q2(INT)` 왜 바꿨고 어떻게 됐나 · `q3(VIO)` 근거 조문·판례·범칙금 · `q5(INT)` 비슷한 곳(항목마다 · 합치지 않음) · `follow`·`back`·`chain` |
| `validate.js` | `ontoValidate(core, schema)` — ID 중복 · 고아 링크 · 타입 위반 · 필수 속성 · 등급·출처 · 개인정보 꼴 |
| `test/run.py` + `test/test.html` | 시험 — 원자료에서 **따로 센 정답**과 머리 없는 크롬에서 돈 query.js 의 답을 맞댐 · 망가뜨린 사본으로 검증기 시험 |
| `tools/tbook-block.py` | T-Book `ontology.html`(ver.4.2 「서초 교차로 — 자료로 시작」)에 넣는 정적 블록 `data/tbook-block-seocho.json` — 조치 이력 5곳 + 10년 사고 상위 25곳(겹쳐 26곳)의 부분 그래프를 **값 그대로** 뗀다(250m 칸·이웃 교차로는 뺌) · 넣는 패치 = `../12_티북패치기록/onto_v42.py` |
| RULE · FK (2026-10-15) | `data/onto-rules.json`(수집기 쪽 세션이 굽는 규칙 장부 — 틀리면 사고 나는 규칙 21 · 소유자 현장 판단 11 말 그대로)을 build.py 가 객체로 옮기고 FK → **뒷받침** → RULE 로 잇는다 · 값은 고치지 않는다 · `query.js` `rules(영역)` · `why(RULE-…)`(= q6 — 정의·출처·등급·주인 앱 자리·시험값·기댄 현장 말) |
| DNG · 속함 (2026-10-23) | 행정동을 그래프에 — 교차로마다 `속함` → `DNG-<행정동 8자리>`(onto-int 행정동 코드 · 등급 B) · 동의 값은 그 동을 열쇠로 가진 파일 그대로(house-dong 세대·1인 · mig-dong 주민 · foreign-dong 외국인주민 · econ-dong 국민연금 사업장·가입자 · dui-ref-seoul 주점·호프 0~6시 결제 · police.json 별표2 관할 — 「27~23」 = 앞이 주 관서·뒤는 일부 번지) · `query.js` `q1(INT).dng` · `q7(DNG)` 이 동 한눈에(교차로 사고는 겹쳐 동 합계로 더하지 않음) · 시험 run.py 47/47(서초3동·방배본동·반포4동 원자료 대조) · 소유자 「엮임 지도 첫째 — 행정동부터」 |
| EVT · 근처 · 흔적 (2026-10-23) | 사건을 그래프에 — `data/onto-events.json`(tools/onto/evt-bake.py · 집회 = 경찰청 주요집회 90일 · 공연 = KOPIS 1,000석↑ 앞 90일~뒤 21일 · 돌발 = 07_API키/out/liveacc·utic/ims 받은 기록 2026-10-15~ · 침수 = 해마다) → 사건 「근처」 교차로(집회 300m·공연 500m·돌발 150m · 근사 C) · 침수 해 「흔적」(season-seocho 흔적 점 100m 안 · n·dep) · `query.js` `q8(INT, since)` 이 교차로에 무슨 일 · 시험 57/57(서초역사거리·예술의전당·트럭터미널·방배경찰서(경보) 원자료 따로 셈) · rally-bake 끝에서 evt-bake → 서초 코어 날마다(여섯 구는 손으로) |
| `build.py --area six` | 서초·강남·송파·동작·관악·용산 한 장 `data/core-six.json`(네비 가르고 범위 · 기본 실행의 서초 결과는 그대로) |
| `tools/gargo-risk.py` | 가르고 「⚠ 이 길 주의 교차로」 표 `../gargo/risk-six.json` — core-six 의 교차로마다 질문 1 답을 한 줄로(값 그대로) |
| `test/risk-run.py` | 위 표 2,157줄을 core-six + query.js q1 과 맞댐 · 여섯 구 코어의 서초 교차로가 서초 코어보다 줄지 않음 |
| `test/tbook-run.py` | 위 ontology.html 시험 — 26곳마다 열어 저장된 지도·화면 글을 **전체 코어 + query.js** 답과 맞댐 · 말풍선 넘침 · 외부 요청 0 · 옛 입구(#field) · 4.1 판에서는 실패해야 정상 |

## 다시 굽기 · 시험

```
py -3.12 -m http.server 8791 --bind 127.0.0.1      (T-Book 저장소 폴더에서 — 법령 자료를 새로 꺼낼 때만)
py -3.12 -X utf8 ontology-core/tools/tbook-extract.py http://127.0.0.1:8791/index.html
py -3.12 -X utf8 ontology-core/build.py
py -3.12 -X utf8 ontology-core/test/run.py          (끝 코드 1 = 실패)
```

## 지킬 것

- 개인정보(성명·연락처·차량번호·주민번호·사건 당사자) 넣지 않음 — 사고는 칸 집계만.
- 법령·판례 번호는 원문에 있는 것만 — T-Book PRECDOC 의 「조회실패」 판례는 잇지 않는다(`unverified_precedents` 에 적어 둠).
- 조치는 이미 공개된 사실만(교통과 출력물 5곳 · 소유자 공개 결정 2026-10-10) — 내부 사유는 「내부 문서 있음」.
- VIP(대통령 행차) 경로·시각은 어떤 객체에도 넣지 않는다.
- 근사 링크는 등급 C 로 밝힌다: 교차로 ↔ 사고 칸 70m · 카메라 100m · 보호구역 시설 300m · 위반유형 ↔ 범칙금 DB 항목은 이름 맞대기.
