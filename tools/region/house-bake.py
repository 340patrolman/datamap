# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.46.0 — 🏠 집안 구성(세대원수 · 혼자 사는 사람 · 1인가구 추이 · 혼인상태 · 혼인·이혼 건수 · 기초생활수급자) → data/house-dong.json
#   원자료 07_API키/out/household/ (소유자 「받아」 2026-10-06)
#     ① 행정안전부 행정동 세대원수별 주민등록 세대수(공공데이터포털 15097974 · 2026-08-31)
#     ② 행정안전부 행정동 성별 연령별 주민등록 1인세대수(15097973 · 2026-08-31)
#     ③ 통계청 KOSIS DT_1JC1502 가구원수별 가구 - 읍면동(등록센서스 · 읍면동은 2015·2020·2024·2025)
#     ④ 통계청 KOSIS DT_1PM2007 혼인상태별 인구(15세 이상 내국인) - 동읍면(2020 20% 표본)
#     ⑤ 통계청 KOSIS DT_1B8000K 읍면동 인구동태건수(혼인·이혼 · 2016~2025)
#     ⑥ 서울 열린데이터광장 OA-22227 국민기초생활 수급자 동별 현황(2024-05 · 자격은 사람마다 하나 — 합 43.7만 ≈ 서울 수급자 46.6만(2025-12))
#     ⑦ 경기데이터드림 경기도 국민기초생활 수급자 현황(GGBSLHRCPSTUS · 읍면동 · 가장 최근 해)
#     ⑧ 한국사회보장정보원 복지사업 시군구별 수급권자 현황(15062448 · 2025-12 · 기초생활보장(맞춤형급여))
#   열쇠 = 행정안전부 행정기관코드 앞 8자리(지도 동 코드와 같다) · 통계청·서울·경기는 코드 체계가 달라 시도·시군구·동 이름으로 짝을 맞춘다
#   py -3.12 -X utf8 tools/region/house-bake.py
import os, re, csv, io, json, glob, collections, openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'household')
def rd(pat): f = glob.glob(os.path.join(SRC, pat))[0]; return list(csv.DictReader(io.StringIO(open(f, 'rb').read().decode('cp949'))))
def num(x):   # 통계청 'X' = 비밀보호(작은 값) → 0
    try: return int(float(x))
    except (TypeError, ValueError): return 0
def nz(s): return re.sub(r'[\s·.ㆍ,()\-]', '', str(s or ''))
def nzj(s): return re.sub(r'제(\d)', r'\1', nz(s))   # 행안부 「창신제1동」 = 통계청·서울 「창신1동」 — 이름 색인은 두 꼴 다(「홍제1동」은 제를 떼면 안 된다)
def sg(sd):   # 시도 묶음(개편 전후 이름을 한 열쇠로)
    s = nz(sd)
    for a, b in (('광주', 'JN'), ('전라남', 'JN'), ('전남', 'JN'), ('강원', 'GW'), ('전라북', 'JB'), ('전북', 'JB'), ('제주', 'JJ'), ('세종', 'SJ'), ('경상북', 'GB'), ('경북', 'GB'), ('경상남', 'GN'), ('경남', 'GN'), ('충청북', 'CB'), ('충북', 'CB'), ('충청남', 'CN'), ('충남', 'CN')):
        if s.startswith(a): return b
    return s[:2]
# ① 세대원수 — 지도 동 열쇠 · 이름 색인
H = {}; IDX = collections.defaultdict(list); SDN = {}
for r in rd('*세대원수별*세대수*.csv'):
    c = r['행정기관코드']
    if not r['읍면동명'].strip() or c[-2:] != '00': continue
    k = c[:8]; n = [int(r[x] or 0) for x in ('전체세대수', '1인세대', '2인세대', '3인세대', '4인세대')]
    n.append(sum(int(r[x] or 0) for x in ('5인세대', '6인세대', '7인세대', '8인세대', '9인세대', '10인이상세대')))
    H[k] = {'hh': n}; [IDX[(sg(r['시도명']), q)].append((k, nz(r['시군구명']))) for q in {nz(r['읍면동명']), nzj(r['읍면동명'])}]; SDN[k[:2]] = r['시도명']
def find(sd, sgg, dong):
    L = IDX.get((sg(sd), nz(dong))) or IDX.get((sg(sd), nzj(dong)), [])
    if len(L) == 1: return L[0][0]
    s = nz(sgg); M = [x for x in L if x[1] == s or x[1].startswith(s) or s.startswith(x[1]) or (s and s in x[1])]
    return M[0][0] if len(M) == 1 else None
# ② 1인세대 나이 — [0~19, 20대, 30대, 40대, 50~64, 65~79, 80+] · [남, 여]
AG = [(0, 19), (20, 29), (30, 39), (40, 49), (50, 64), (65, 79), (80, 200)]
for r in rd('*1인세대수*.csv'):
    k = r['행정기관코드'][:8]
    if k not in H or r['행정기관코드'][-2:] != '00': continue
    def age(a, b): return sum(int(r.get('%d세%s' % (x, sx)) or 0) for x in range(a, min(b, 109) + 1) for sx in ('남자', '여자')) + (sum(int(r.get('110세 이상' + sx) or 0) for sx in ('남자', '여자')) if b >= 110 else 0)
    H[k]['one'] = [age(a, b) for a, b in AG]; H[k]['onesx'] = [int(r['남자'] or 0), int(r['여자'] or 0)]
# 통계청 지역 이름 사다리(코드 앞자리 = 위 단위)
def kosis(tbl):
    rows = []
    for f in sorted(glob.glob(os.path.join(SRC, 'kosis_%s_*.json' % tbl))): rows += json.load(open(f, encoding='utf-8'))
    NM = {r['C1']: r['C1_NM'] for r in rows}
    def path(c): return (NM.get(c[:2], ''), NM.get(c[:5], ''), NM.get(c, ''))
    return rows, path
miss = collections.Counter()
def kk(path, c):
    if len(c) < 7: return None
    sd, gu, dn = path(c); return find(sd, gu, dn)
# ③ 1인가구 추이(통계청 일반가구)
rows, path = kosis('DT_1JC1502'); CEN = collections.defaultdict(dict)
for r in rows:
    k = kk(path, r['C1'])
    if not k: miss['1인가구'] += len(r['C1']) >= 7; continue
    CEN[k].setdefault(r['PRD_DE'], {})[r['ITM_ID']] = num(r['DT'])
for k, ys in CEN.items():
    if k in H: H[k]['cen'] = {y: [v.get('T0', 0), v.get('T1', 0), v.get('T2', 0), v.get('T3', 0), v.get('T4', 0), max(0, v.get('T0', 0) - v.get('T1', 0) - v.get('T2', 0) - v.get('T3', 0) - v.get('T4', 0))] for y, v in sorted(ys.items())}
# ④ 혼인상태 2020 — [계, 미혼, 배우자있음, 사별, 이혼]
rows, path = kosis('DT_1PM2007'); MR = collections.defaultdict(dict)
for r in rows:
    if r.get('C2') != '0' or r.get('C3') != '000': continue
    k = kk(path, r['C1'])
    if not k: miss['혼인'] += len(r['C1']) >= 7; continue
    MR[k][r['C4']] = num(r['DT'])
for k, v in MR.items():
    if k in H: H[k]['mar'] = [v.get('0', 0), v.get('1', 0), v.get('2', 0), v.get('5', 0), v.get('4', 0)]
# ⑤ 혼인·이혼 건수 — {해: [혼인, 이혼]}
rows, path = kosis('DT_1B8000K'); DV = collections.defaultdict(dict)
for r in rows:
    if r.get('C2') != '0': continue
    k = kk(path, r['C1'])
    if not k: continue
    DV[k].setdefault(r['PRD_DE'], [0, 0])[0 if r['ITM_ID'] == 'T40' else 1] += num(r['DT'])
for k, v in DV.items():
    if k in H: H[k]['div'] = dict(sorted(v.items()))
# ⑥ 서울 수급자(동) — [합, 생계, 의료, 주거, 교육, 18세 미만, 65세 이상]
QI = {'기초생계급여': 1, '기초의료급여': 2, '기초주거급여': 3, '기초교육급여': 4}
def addw(k, q, a, n, src):
    w = H[k].setdefault('wel', [0, 0, 0, 0, 0, 0, 0]); w[0] += n; w[QI.get(q, 1)] += n
    if a and '18세미만' in nz(a): w[5] += n
    if a and '65' in a: w[6] += n
    H[k]['welsrc'] = src
cur = gu = q = None; GUWEL = collections.Counter()
ws = openpyxl.load_workbook(os.path.join(SRC, 'seoul_welfare_202405.xlsx'), read_only=True).worksheets[0]
for r in list(ws.iter_rows(values_only=True))[3:]:
    if r[0]:
        cur = r[0]
        if re.search(r'구$', cur): gu = cur
    if r[1]: q = r[1]
    if not r[4]: continue
    if cur == gu: GUWEL[gu] += r[4]; continue
    k = find('서울특별시', gu, cur)
    if k: addw(k, q, r[2], r[4], 'seoul')
    else: miss['서울 수급'] += 1
# ⑦ 경기 수급자(동) — 가장 최근 해
GG = json.load(open(os.path.join(SRC, 'gg_welfare.json'), encoding='utf-8')); GY = {}
for r in GG: GY[r['SIGNGU_NM']] = max(GY.get(r['SIGNGU_NM'], ''), r['YY'])   # 시군마다 올린 해가 달라 시군마다 가장 최근 해
gy = '%s~%s' % (min(GY.values()), max(GY.values()))
seen = set()
for r in GG:
    if r['YY'] != GY[r['SIGNGU_NM']]: continue
    key = (r['SIGNGU_NM'], r['EMD_NM'], r['QUALFCTN_DIV'], r['AGE_DIV'])
    if key in seen: continue
    seen.add(key); k = find('경기도', r['SIGNGU_NM'], r['EMD_NM'])
    if k: addw(k, r['QUALFCTN_DIV'], r['AGE_DIV'], int(r['PSN_CNT'] or 0), 'gg'); H[k]['welyy'] = r['YY']
    else: miss['경기 수급'] += 1
# ⑥-2 서울 차상위(동) — cha [합, 한부모가족(모자·부자·청소년·조손), 본인부담경감, 차상위계층 확인, 차상위장애인, 차상위자활, 18세 미만, 65세 이상] · 서울 열린데이터광장 OA-22226
CHK = {'차상위본인부담경감대상자': 2, '차상위계층 확인': 3, '차상위장애인': 4, '차상위자활': 5}
f = os.path.join(SRC, 'seoul_cha.csv')
if os.path.exists(f):
    for r in csv.DictReader(io.StringIO(open(f, 'rb').read().decode('cp949'))):
        n = int(r['수급권자수'] or 0)
        if not n: continue
        k = find(r['시도'], r['시군구'], r['읍면동'])
        if not k: miss['서울 차상위'] += 1; continue
        o = H[k].setdefault('cha', [0] * 8); o[0] += n; o[CHK.get(r['자격'], 1)] += n
        if '18세미만' in nz(r['연령구간']): o[6] += n
        if '65' in r['연령구간']: o[7] += n
        H[k]['chasrc'] = 'seoul'
# ⑧ 시군구 수급권자(전국 · 2025-12) — 시군구 이름 → 지도 구 코드
GUS = {}
for k in H: GUS.setdefault((sg(SDN[k[:2]]), nz(SDN[k[:2]])), set()).add(k[:5])
SGN = {}
for r in rd('*세대원수별*세대수*.csv'):
    c = r['행정기관코드']
    if r['시군구명'].strip(): SGN.setdefault((sg(r['시도명']), nz(r['시군구명'])), c[:5])
SGW = {}   # [기초생활 수급권자, 수급가구, 차상위 3사업 합(본인부담경감·자활·장애인), 기초연금 수급권자]
CHA = {'차상위본인부담경감대상자': 2, '차상위자활': 2, '차상위장애인': 2, '기초생활보장(맞춤형급여)': 0, '기초연금': 3}
for r in rd('*수급권자*.csv'):
    if r['사업명'] not in CHA: continue
    s = nz(r['시군구']); L = [c for (a, b), c in SGN.items() if a == sg(r['시도']) and (b == s or b.endswith(s) or b.startswith(s))]
    if len(L) >= 1:
        o = SGW.setdefault(L[0], [0, 0, 0, 0]); i = CHA[r['사업명']]; o[i] += int(r['수급권자수'])
        if i == 0: o[1] += int(r['수급가구수'])
    else: miss['시군구 수급'] += 1
# 2026 기준 중위소득·선정기준(보건복지부 고시 제2025-135호 · 2026-01-01 시행 · 표 그림에서 읽음) · 차상위 = 중위 50% 이하(국민기초생활 보장법 시행령 제3조)
MID = {'year': 2026, 'src': '보건복지부 고시 제2025-135호 「2026년 기준 중위소득 및 생계·의료급여 선정기준과 최저보장수준」 · 차상위 = 기준 중위소득 50% 이하(국민기초생활 보장법 제2조 제10호 · 시행령 제3조) · 주거급여 48%·교육급여 50% 선정기준은 국토부·교육부 소관(이 표에 없음)',
       'mid': [2564238, 4199292, 5359036, 6494738, 7556719, 8555952, 9515150], 'live': [820556, 1343773, 1714892, 2078316, 2418150, 2737905, 3044848], 'med': [1025695, 1679717, 2143614, 2597895, 3022688, 3422381, 3806060]}
# 시도·시군구 합(평균 견주기용)
def agg(keys):
    o = {'hh': [0] * 6, 'one': [0] * 7}
    for k in keys:
        for i, v in enumerate(H[k]['hh']): o['hh'][i] += v
        for i, v in enumerate(H[k].get('one', [0] * 7)): o['one'][i] += v
    return o
SD = collections.defaultdict(list); GU = collections.defaultdict(list)
for k in H: SD[k[:2]].append(k); GU[k[:5]].append(k)
res = {'schema': 'tg-house/1', 'asof': {'hh': '2026-08', 'cen': '2015·2020·2024·2025', 'mar': '2020', 'div': '2016~2025', 'wel_seoul': '2024-05', 'wel_gg': gy, 'wel_sgg': '2025-12', 'cha_seoul': 'OA-22226(서울 열린데이터광장 · 받은 날 2026-10-06 · 파일에 기준일 없음 — 공공데이터포털 판 15086094 는 2021-07-31 기준)'},
       'source': '행정안전부 주민등록 세대원수별 세대수·1인세대수(공공데이터포털 15097974·15097973 · 2026-08-31) · 통계청 KOSIS 가구원수별 가구-읍면동(DT_1JC1502)·혼인상태(DT_1PM2007 · 2020 표본)·인구동태건수(DT_1B8000K) · 서울 열린데이터광장 OA-22227(수급자)·OA-22226(차상위) · 경기데이터드림 국민기초생활 수급자 현황 · 한국사회보장정보원 시군구별 수급권자(15062448 · 기초생활·차상위·기초연금) · 보건복지부 고시 제2025-135호(2026 기준 중위소득)',
       'fields': 'dong = {행정동 8자리: hh [세대, 1인, 2인, 3인, 4인, 5인 이상] · one 1인세대 나이 [0~19, 20대, 30대, 40대, 50~64, 65~79, 80+] · onesx [남, 여] · cen {해: 일반가구 [계, 1인, 2인, 3인, 4인, 5인 이상]} · mar 2020 15세 이상 [계, 미혼, 배우자있음, 사별, 이혼] · div {해: [혼인, 이혼]} · wel [수급자, 생계, 의료, 주거, 교육, 18세 미만, 65세 이상] · welsrc seoul|gg · cha 서울 차상위 [합, 한부모가족, 본인부담경감, 계층확인, 장애인, 자활, 18세 미만, 65세 이상]} · sd/sg = 시도·시군구 합 · sgw = {시군구 5자리: [기초생활 수급권자, 수급가구, 차상위 3사업 합, 기초연금 수급권자]} · mid = 2026 기준 중위소득·생계·의료 선정기준(1~7인 · 원/월) · guwel = 서울 구청 직접(동에 안 붙은) 수급자',
       'note': '주민등록 「세대」는 통계청 「가구」와 다르다(주소만 같이 두거나 따로 둔 경우) · 혼인상태는 2020 표본 한 시점 · 이혼은 그 해 신고 건수(주소지 기준) · 수급자는 자격(생계·의료·주거·교육)마다 한 사람을 한 번 센 값',
       'dong': H, 'sd': {k: agg(v) for k, v in SD.items()}, 'sg': {k: agg(v) for k, v in GU.items()}, 'sgw': SGW, 'mid': MID, 'guwel': dict(GUWEL), 'miss': dict(miss)}
p = os.path.join(ROOT, 'data', 'house-dong.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
c = collections.Counter(); [c.update(x for x in ('one', 'cen', 'mar', 'div', 'wel') if x in v) for v in H.values()]
print('동', len(H), dict(c), '시군구 수급', len(SGW), '못 맞춤', dict(miss), os.path.getsize(p) // 1024, 'KB')
