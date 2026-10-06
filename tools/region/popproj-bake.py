# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.53.0 — 👥 인구 5년·10년 뒤(소유자 「인구예측 5년 뒤 10년 뒤 · 거기 따라가는 상권도 유추」) → data/popproj.json
#   원자료 07_API키/out/natfac/kosis_DT_1BPB002E.json = 통계청 「추계인구(시/군/구)」(2022년 기준 시군구 장래인구추계 · 2026·2031·2036·2041 · 5세 계급 · 계·여자)
#   지도 시군구(2026 행정체제) ← 통계청 시군구(2022 기준) 이름 짝 · 새로 생기거나 바뀐 구(인천 제물포·영종·검단·서해 · 화성·부천 일반구 등)는 같은 시(또는 옛 구) 값을 빌린다(근사 · 빌린 곳을 적는다)
#   py -3.12 -X utf8 tools/region/popproj-bake.py
import json, os, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
rows = json.load(open(os.path.join(KB, '07_API키', 'out', 'natfac', 'kosis_DT_1BPB002E.json'), encoding='utf-8'))
ITM = sorted({r['ITM_ID'] for r in rows if r['ITM_ID'] != 'T10'}); INM = {r['ITM_ID']: r['ITM_NM'] for r in rows}
V = collections.defaultdict(lambda: collections.defaultdict(dict))   # 코드 → (해, 성) → 항목
NM = {}
for r in rows:
    NM[r['C1']] = r['C1_NM']; V[r['C1']][(r['PRD_DE'], r['C2'])][r['ITM_ID']] = int(float(r['DT'] or 0))
def nz(x): return re.sub(r'[\s·]', '', x or '')
def sg(sd):
    t = nz(sd)
    for a, b in (('광주', 'JN'), ('전라남', 'JN'), ('전남', 'JN'), ('강원', 'GW'), ('전라북', 'JB'), ('전북', 'JB'), ('제주', 'JJ'), ('세종', 'SJ'), ('경상북', 'GB'), ('경북', 'GB'), ('경상남', 'GN'), ('경남', 'GN'), ('충청북', 'CB'), ('충북', 'CB'), ('충청남', 'CN'), ('충남', 'CN')):
        if t.startswith(a): return b
    return t[:2]
K = {}
for c, n in NM.items():
    if c[:2] == '12':
        if len(c) == 7: K[('JN', nz(n))] = c   # 광주 구(1224010 …) — 2026 개편 뒤 표가 전남광주 아래 7자리
    elif len(c) == 5: K[(sg(NM.get(c[:2], '')), nz(n).replace('통합', ''))] = c
# 전남·세종(통계청 시군구 표에 없음 — 2026 개편 뒤 빠짐) → 시도 장래인구추계(DT_1BPB001 · 중위) 연령 비율
SR = json.load(open(os.path.join(KB, '07_API키', 'out', 'natfac', 'kosis_DT_1BPB001_sido.json'), encoding='utf-8'))
SAGE = ['040', '050', '070', '100', '120', '130', '150', '160', '180', '190', '210', '230', '260', '280', '310', '330', '360', '380', '410', '430']
for r in SR:
    c = 'S' + r['C2']; NM[c] = r['C2_NM'] + '(시도)'; a = '430' if r['C4'] == '440' else r['C4']
    if a not in SAGE: continue
    d = V[c][(r['PRD_DE'], r['C3'])]; i = ITM[SAGE.index(a)]; d[i] = d.get(i, 0) + int(float(r['DT'] or 0))
IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
SIDN = {'11': '서울', '26': '부산', '27': '대구', '28': '인천', '29': '광주', '30': '대전', '31': '울산', '36': '세종', '41': '경기', '43': '충북', '44': '충남', '46': '전남', '12': '전남', '47': '경북', '48': '경남', '50': '제주', '51': '강원', '52': '전북'}
BORROW = {'28125': '28110', '28155': '28110', '28275': '28260', '28290': '28260'}   # 인천 제물포·영종(옛 중구) · 서해·검단(옛 서구) — 개편 전 구 값의 비율을 빌림
def pack(c):
    o = {}
    for (y, sx), d in V[c].items():
        o.setdefault(y, {})['m' if sx == '2' else 't'] = [d.get(i, 0) for i in ITM]
    return o
out = {}; how = collections.Counter()
for g in IX['gus']:
    gu, nm = g['gu'], g['name']; k = K.get((sg(SIDN.get(gu[:2], '')), nz(nm)))
    note = ''
    if not k and gu in BORROW:
        oc = [c for c in NM if len(c) == 5 and NM[c] in ('중구', '서구') and c[:2] == '23']
        k = next((c for c in oc if NM[c] == ('중구' if BORROW[gu] == '28110' else '서구')), None); note = '개편 전 ' + ('중구' if BORROW[gu] == '28110' else '서구') + ' 비율'
    if not k:
        city = re.sub(r'(시)\s?\S+구$', r'\1', nm)
        k = K.get((sg(SIDN.get(gu[:2], '')), nz(city))); note = city + ' 전체 비율' if k else ''
    if not k and '시' in nm[1:]:
        city = nm.split('시')[0] + '시'; k = K.get((sg(SIDN.get(gu[:2], '')), nz(city))); note = city + ' 전체 비율' if k else ''
    if not k and gu[:2] == '12': k = 'S36'; note = '전라남도 시도 추계 비율(통계청 시군구 표에 전남이 빠짐)'
    if not k and gu[:2] == '36': k = 'S29'; note = '세종 시도 추계'
    if not k and gu == '27720': k = next((c for c in NM if NM[c] == '군위군'), None); note = '군위군(2022 기준 경북 소속)'
    if not k:
        k = next((c for c in NM if len(c) == 2 and sg(NM[c]) == sg(SIDN.get(gu[:2], ''))), None); note = '시도 전체 비율' if k else ''
    if not k: how['없음'] += 1; continue
    how['짝' if not note else '빌림'] += 1; out[gu] = {'k': k, 'n': NM[k], 'note': note, 'y': pack(k)}
doc = {'schema': 'tg-popproj/1', 'source': '통계청 「추계인구(시/군/구)」(KOSIS DT_1BPB002E · 2022년 기준 시군구 장래인구추계 · 2025-02 공표)', 'ages': [INM[i] for i in ITM],
       'fields': 'gu = {지도 시군구: {k 통계청 코드, n 이름, note 빌린 곳, y: {해: {t 5세 계급 계, m 5세 계급 여자}}}}', 'gu': out}
p = os.path.join(ROOT, 'data', 'popproj.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(how), len(ITM), [INM[i] for i in ITM][:3], [INM[i] for i in ITM][-3:], os.path.getsize(p) // 1024, 'KB')
