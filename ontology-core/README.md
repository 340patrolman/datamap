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
