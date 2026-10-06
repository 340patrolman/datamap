# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.40.1 — 🏬 상가 임차 평균(권리금·보증금·월세·공용관리비) — 소유자 2026-10-06 「평균적인 권리금·해당지역 평균 월세·관리비를 근사치로 넣고 빼고 고칠 수 있게」
#   출처 = 중소벤처기업부 「상가건물 임대차 실태조사」 2025(KOSIS 기관 142) — 권역·시도·업종(대분류 일부)별 평균
#     DT_S25A068 기업체의 임대차 현황(현 계약사항 d1~d5 = 계약기간·계약면적·전용면적·보증금·월세)
#     DT_S25A098 권리금 지급 경험(예 %) · DT_S25A099 권리금 지급 금액(평균 · 구간 %) · DT_S25A070 월평균 공용관리비(평균 · 없음 %)
#   키 = 07_API키/keys.json 의 kosis(출력 금지) · 원자료 07_API키/out/lease/ · 결과 data/lease-bench.json
#   py -3.12 -X utf8 tools/region/lease-bake.py
import json, os, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'lease'); os.makedirs(OUT, exist_ok=True)
k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
if isinstance(k, dict): k = k.get('key') or list(k.values())[0]
def get(tbl):
    p = os.path.join(OUT, tbl + '.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    q = {'method': 'getList', 'apiKey': k, 'format': 'json', 'jsonVD': 'Y', 'orgId': '142', 'tblId': tbl, 'itmId': 'ALL', 'objL1': 'ALL', 'objL2': 'ALL', 'prdSe': 'F', 'startPrdDe': '2025', 'endPrdDe': '2025'}
    t = urllib.request.urlopen('https://kosis.kr/openapi/Param/statisticsParameterData.do?' + urllib.parse.urlencode(q), timeout=90).read().decode('utf-8')
    j = json.loads(t)
    if not isinstance(j, list): raise SystemExit('%s: %s' % (tbl, j))
    json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False); return j
NM = {'0201': None}   # 권역(0201 서울 등)과 시도 이름이 같은 「서울」이 두 번 나온다 — 처음 것만 쓴다
out = {}
def put(r, key, val):
    nm = r['C1_NM'].strip(); o = out.setdefault(nm, {})
    if key not in o: o[key] = val
for r in get('DT_S25A068'):
    m = {'d1': 'term', 'd2': 'area', 'd3': 'areaEx', 'd4': 'dep', 'd5': 'rent'}.get(r['C2'])
    if m: put(r, m, float(r['DT']))
for r in get('DT_S25A098'):
    if r['C2_NM'] == '예': put(r, 'premPay', float(r['DT']))
for r in get('DT_S25A099'):
    if r['C2_NM'].endswith('평균'): put(r, 'prem', float(r['DT']))
    elif r['C2_NM'] != '사례수': out.setdefault(r['C1_NM'].strip(), {}).setdefault('premDist', {}).setdefault(r['C2_NM'], float(r['DT']))
for r in get('DT_S25A070'):
    if r['C2_NM'].endswith('평균'): put(r, 'mgmt', float(r['DT']))
    elif r['C2_NM'] == '없음': put(r, 'mgmtNone', float(r['DT']))
res = {'schema': 'tg-lease/1', 'year': 2025,
       'source': '중소벤처기업부 「상가건물 임대차 실태조사」 2025(KOSIS 142 · DT_S25A068 임대차 현황 현 계약사항 · DT_S25A098 권리금 지급 경험 · DT_S25A099 권리금 지급 금액 · DT_S25A070 월평균 공용관리비)',
       'fields': '이름(전체·권역·시도·업종) → term 계약기간(개월) · area 계약면적㎡ · areaEx 전용㎡ · dep 보증금(만 원) · rent 월세(만 원) · premPay 권리금을 낸 비율(%) · prem 낸 곳의 평균 권리금(만 원) · premDist 구간 % · mgmt 월평균 공용관리비(만 원 · 전기·수도 등 개별 사용료 아님) · mgmtNone 공용관리비 없음 %',
       'note': '표본조사 평균(근사) — 업종은 대분류 몇 개뿐(음식점·주점 · 교육 서비스업 · 소매 · 제조 · 스포츠·오락 · 수리 · 기타 개인 서비스) · 시도와 업종을 함께 가른 값은 없다', 'by': out}
p = os.path.join(ROOT, 'data', 'lease-bench.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(len(out), '항목 →', p, os.path.getsize(p))
for n in ['전체', '서울', '경기', 'P. 교육 서비스업', 'I56. 음식점 및 주점업']: print(n, {k2: v for k2, v in out.get(n, {}).items() if k2 != 'premDist'})
