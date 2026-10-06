# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.43.0 — 🎒 학원·교습소(교육청 등록 · NEIS 학원교습소정보) → data/neis-dong.json
#   원자료 07_API키/out/neis/aca_<시도교육청>.json(tools/region/neis-fetch.py · 서울·경기는 코워크) · 개원 중인 곳만(폐원 기록 없음) · 체육도장(태권도)·개인과외교습자는 이 자료에 없다
#   자리 = 주소 괄호의 법정동 이름 → 행정동(서울·경기 = data/b2a.json 넓이 비율 가장 큰 동 · 그 밖 = 같은 시군구 행정동 이름 줄기) — 좌표가 없어 동 단위 근사
#   갈래 = 입시·보습(입시.검정 및 보습·종합) · 외국어(국제화) · 음악 · 미술 · 무용 · 그 밖 예능·기예 · 독서실 · 그 밖(직업기술·정보·인문사회·기타)
#   교습비 = 「1인당 수강료」 글의 금액들(1만~300만 원)의 가운데 값 → 동·시군구마다 갈래·학원/교습소별 가운데 값
#   py -3.12 -X utf8 tools/region/neis-bake.py
import json, os, glob, re, csv, collections, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); SRC = os.path.join(KB, '07_API키', 'out', 'neis')
SD = {'B10': '서울특별시', 'C10': '부산광역시', 'D10': '대구광역시', 'E10': '인천광역시', 'F10': '전남광주통합특별시', 'G10': '대전광역시', 'H10': '울산광역시', 'I10': '세종특별자치시', 'J10': '경기도', 'K10': '강원특별자치도',
      'M10': '충청북도', 'N10': '충청남도', 'P10': '전북특별자치도', 'Q10': '전남광주통합특별시', 'R10': '경상북도', 'S10': '경상남도', 'T10': '제주특별자치도'}
REN = {('E10', '중구'): ['제물포구', '영종구'], ('E10', '동구'): ['제물포구'], ('E10', '서구'): ['서해구', '검단구'], ('I10', '세종특별자치시'): ['세종시']}
GR = ['입시·보습', '외국어', '음악', '미술', '무용', '그 밖 예능·기예', '독서실', '그 밖']
def grp(r):
    f = r.get('REALM_SC_NM') or ''; c = (r.get('LE_CRSE_NM') or '') + ' ' + (r.get('LE_CRSE_LIST_NM') or '')
    if f.startswith('입시') or f.startswith('종합'): return 0
    if f == '국제화': return 1
    if f.startswith('예능'):
        if '미술' in c: return 3
        if '무용' in c or '댄스' in c: return 4
        if '음악' in c or '피아노' in c or '성악' in c: return 2
        return 5
    if f.startswith('기예'): return 5
    if f == '독서실': return 6
    return 7
ADM = [(r['cd'][:8], r['sido'], r['sggnm'], r['nm'].split(' ')[-1]) for r in csv.DictReader(open(os.path.join(KB, '13_관할경계', '결과', 'adm_props.csv'), encoding='utf-8-sig'))]
BYK = {a[0]: a for a in ADM}
B2A = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a']
LEG = collections.defaultdict(list)   # 법정동 이름 → [(행정동, %)]
for v in B2A.values():
    for x in v['a']:
        if x[0] in BYK: LEG[v['n']].append((x[0], x[2]))
def stem(n): return re.sub(r'[\d·,.]+(?=[동읍면가]$)', '', n)
def cands(code, zone):
    sd = SD.get(code); names = REN.get((code, zone), [zone])
    return [a for a in ADM if a[1] == sd and any(a[2] == z or (a[2].startswith(z) and z.endswith('시')) or (z.endswith('구') and a[2].endswith(z) and len(a[2]) > len(z)) for z in names)]
CC = {}
def match(code, zone, ld, emd):   # → ([(행정동, 무게)], 방법) · 못 찾으면 ([], 시군구 5자리)
    key = (code, zone)
    if key not in CC: CC[key] = cands(code, zone)
    C = CC[key]; ks = {a[0] for a in C}
    if not C: return [], None
    if emd:   # 읍·면 = 행정 읍·면 이름 그대로
        S = [a for a in C if a[3] == emd]
        if S: return [(S[0][0], 1.0)], 'emd'
    if ld:
        L = [x for x in LEG.get(ld, []) if x[0] in ks]
        if L: t = sum(x[1] for x in L); return [(x[0], x[1] / t) for x in L], 'b2a'
        S = [a for a in C if a[3] == ld or stem(a[3]) == ld or stem(a[3]) == stem(ld)]
        if S: return [(a[0], 1.0 / len(S)) for a in S], 'name'
    return [], C[0][0][:5]
def fee(t):
    a = [int(x.replace(',', '')) for x in re.findall(r':\s*([\d,]{5,})', t or '')]
    a = [x for x in a if 10000 <= x <= 3000000]
    return statistics.median(a) if a else None
D = collections.defaultdict(lambda: {'n': [0, 0], 'g': [[0, 0] for _ in GR], 'f': [[[], []] for _ in GR], 'cap': 0, 'y': collections.Counter()})
G = collections.defaultdict(lambda: {'n': [0, 0], 'g': [[0, 0] for _ in GR], 'f': [[[], []] for _ in GR]})
cnt = collections.Counter()
for fn in sorted(glob.glob(os.path.join(SRC, 'aca_*.json'))):
    for r in json.load(open(fn, encoding='utf-8')):
        code = r['ATPT_OFCDC_SC_CODE']; ad = (r.get('FA_RDNMA') or '').split(); zone = (r.get('ADMST_ZONE_NM') or '').strip()
        if len(ad) > 2 and re.search(r'[시군구]$', ad[1]): zone = ad[1] + (ad[2] if ad[1].endswith('시') and ad[2].endswith('구') else '') if code != 'I10' else zone
        emd = next((w for w in ad[2:4] if re.search(r'[읍면]$', w)), None)
        m = re.search(r'\(([^,)]+)', r.get('FA_RDNDA') or ''); ld = re.sub(r'\s', '', m.group(1)) if m else None
        W, how = match(code, zone, ld, emd)
        if not W and zone != (r.get('ADMST_ZONE_NM') or '').strip(): W, how = match(code, (r.get('ADMST_ZONE_NM') or '').strip(), ld, emd)
        t = 1 if r.get('ACA_INSTI_SC_NM') == '교습소' else 0; g = grp(r); fv = fee(r.get('PSNBY_THCC_CNTNT'))
        gk = (W[0][0][:5] if W else how) or 'x'
        for o, w in [(D[k8], w) for k8, w in W] + [(G[gk], 1.0)]:
            o['n'][t] += w; o['g'][g][t] += w
            if fv: o['f'][g][t].append(fv)
        for k8, w in W:
            D[k8]['cap'] += int(r.get('TOFOR_SMTOT') or 0) * w
            y = (r.get('ESTBL_YMD') or '')[:4]
            if y.isdigit(): D[k8]['y'][int(y)] += w
        cnt[('동 ' + how) if W else '시군구만'] += 1; cnt['전체'] += 1
def med(a): return int(statistics.median(a)) if a else None
def pack(o, full):
    r1 = lambda v: round(v, 1)
    x = [[r1(o['n'][0]), r1(o['n'][1])], [[r1(a), r1(b), med(o['f'][i][0]), med(o['f'][i][1])] for i, (a, b) in enumerate(o['g'])]]
    if full: x += [round(o['cap']), {str(k): r1(v) for k, v in sorted(o['y'].items()) if k >= 1990}]
    return x
res = {'schema': 'tg-neis/1', 'groups': GR, 'source': '교육부 NEIS 교육정보 개방 포털 「학원교습소정보」(시·도 교육청 등록 · 2026-10-06 받음) · 행정동 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0) · 법정동→행정동 = 브이월드 경계(서울·경기)',
       'fields': 'dong = {행정동 8자리: [[학원, 교습소], [[갈래별 학원, 교습소, 학원 교습비 가운데 값(원), 교습소 교습비 가운데 값] × 갈래], 정원 합, {개원 연도: 수}]} · sgg = {시군구 5자리: 앞 둘}',
       'note': '개원 중인 곳만(폐원 기록 없음) · 체육도장(태권도 등)·개인과외교습자는 없다 · 좌표가 없어 주소의 읍·면·법정동으로 행정동에 붙인 근사(한 법정동이 여러 행정동에 걸치면 넓이 비율로 나눠 소수로 센다) · 교습비는 교습소만 공개(학원 칸은 비어 있다) — 등록한 과정별 1인 교습비 금액들의 가운데 값(기간 단위는 과정마다 다를 수 있다)',
       'counts': dict(cnt), 'dong': {k: pack(v, True) for k, v in D.items()}, 'sgg': {k: pack(v, False) for k, v in G.items()}}
p = os.path.join(ROOT, 'data', 'neis-dong.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt), '동', len(D), '시군구', len(G), os.path.getsize(p) // 1024, 'KB')
