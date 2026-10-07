# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.83.0 — 👶 어린이집·유치원을 유형별로(소유자 2026-10-07 「생기고 없어질 때 병설유치원·구립·시립·직장 어린이집 등 동네 수요와 상관없는 것이 생겼는지 · 사립과 공립으로 나누어 · 직장 어린이집은 거의 제외」)
#   어린이집(인가일·폐지일 · 유형):
#     서울 = 07_API키/out/region/fac/ChildCareInfo.json(서울시 어린이집 정보 · CRTYPENAME · CRCNFMDT 인가 · CRABLDT 폐지) · 해마다 그해 말 운영 수 2016~2026
#     경기 = fac/gg_ChildHouse.json(경기데이터드림 · KIDGARTN_DIV_NM · TEMP_CONT01 인가 · TEMP_CONT04 폐지) · 2016~2025(자료 기준일 2025.7)
#     갈래: 국공립(구립·시립 등 — 정책으로 생김) · 직장(그 일터 아이 — 동네 수요와 무관) · 민간 · 가정 · 법인·단체(사회복지법인·법인·단체등·협동)
#   유치원:
#     서울 = fac/school_ll.csv(서울특별시교육청 연도별 학교 · 2014~2025 · 설립구분 공립/사립 · 이름에 「병설」) — 해마다 그 해 목록에 있는 수
#     경기 = 07_API키/out/natfac/kg/kg_general_*.csv(유치원알리미 공시 · 설립유형 공립(병설)·공립(단설)·사립(사인)·사립(법인)·국립 · 개원일) — 지금 문 연 곳만(문 닫은 곳은 자료에 없다)
#   행정동 = 통계청 SGIS 경계(13_관할경계 hjd 2026-07)
#   → data/r/<구>/cct.json   py -3.12 -X utf8 tools/region/cctype-bake.py
import json, os, csv, glob, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r'); FAC = os.path.join(KB, '07_API키', 'out', 'region', 'fac')
feats = [f for f in json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features'] if f['properties']['sido'] in ('11', '41')]
geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms)
def dong(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return feats[i]['properties']['adm_cd2'][:8]
CCG = ['국공립', '직장', '민간', '가정', '법인·단체']
def ccg(t): return t if t in ('국공립', '직장', '민간', '가정') else '법인·단체'
YS = {'11': list(range(2016, 2027)), '41': list(range(2016, 2026))}
OUT = collections.defaultdict(lambda: collections.defaultdict(dict)); cnt = collections.Counter()
def yr(v):
    v = str(v or '')[:4]; return int(v) if v.isdigit() else 0
def add_cc(k, grp, y0, y1, sd, alive):
    Y = YS[sd]; D = OUT[k[:5]][k]
    for key in ('cc', 'cco', 'ccc'): D.setdefault(key, {g: [0] * len(Y) for g in CCG})
    for i, y in enumerate(Y):
        if y0 and y0 <= y < y1 and (alive or y < Y[-1] or y1 > y): D['cc'][grp][i] += 1
        if y0 == y: D['cco'][grp][i] += 1
        if y1 == y: D['ccc'][grp][i] += 1
for r in json.load(open(os.path.join(FAC, 'ChildCareInfo.json'), encoding='utf-8')):
    if not r['LA'] or (r['LA'], r['LO']) == ('37.566470', '126.977963'): cnt['서울 어린이집 좌표 없음'] += 1; continue
    k = dong(float(r['LO']), float(r['LA']))
    if not k: continue
    y1 = yr(r['CRABLDT']) or 9999
    if r['CRSTATUSNAME'] == '폐지' and y1 == 9999: y1 = 2026
    add_cc(k, ccg(r['CRTYPENAME']), yr(r['CRCNFMDT']), y1, '11', r['CRSTATUSNAME'] != '폐지'); cnt['서울 어린이집'] += 1
gfn = os.path.join(FAC, 'gg_ChildHouse.json')
for r in json.load(open(gfn, encoding='utf-8')):
    if not r.get('WGS84_LAT'): continue
    k = dong(float(r['WGS84_LOGT']), float(r['WGS84_LAT']))
    if not k or k[:2] != '41': continue
    add_cc(k, ccg(r['KIDGARTN_DIV_NM']), yr(r.get('TEMP_CONT01')), yr(r.get('TEMP_CONT04')) or 9999, '41', not yr(r.get('TEMP_CONT04'))); cnt['경기 어린이집'] += 1
# 서울 유치원(해마다 목록)
KGG = ['공립(병설)', '공립(단설)', '사립']; KY = list(range(2014, 2026))
for r in list(csv.reader(open(os.path.join(FAC, 'school_ll.csv'), encoding='cp949')))[1:]:
    if r[3] != '유치원' or not r[8]: continue
    k = dong(float(r[9]), float(r[8]))
    if not k: continue
    g = '사립' if r[4] == '사립' else ('공립(병설)' if '병설' in r[5] else '공립(단설)')
    D = OUT[k[:5]][k].setdefault('kg', {x: [0] * len(KY) for x in KGG}); D[g][KY.index(int(r[0]))] += 1; cnt['서울 유치원 행'] += 1
# 경기 유치원(지금 · 개원 해)
kgf = sorted(glob.glob(os.path.join(KB, '07_API키', 'out', 'natfac', 'kg', 'kg_general_*.csv')))[-1]
KGN = ['공립(병설)', '공립(단설)', '사립(사인)', '사립(법인)', '국립']
rows = list(csv.reader(open(kgf, encoding='utf-8-sig'))); H = {h: i for i, h in enumerate(rows[0])}
for r in rows[1:]:
    try: lat, lon = float(r[H['위도']]), float(r[H['경도']])
    except ValueError: continue
    k = dong(lon, lat)
    if not k or k[:2] != '41': continue
    t = r[H['설립유형']].strip()
    if t not in KGN: continue
    D = OUT[k[:5]][k]; n = D.setdefault('kgn', {x: 0 for x in KGN}); n[t] += 1
    oy = yr(r[H['개원일']]) or yr(r[H['설립일']]); o = D.setdefault('kgo', {x: [0] * 10 for x in KGN})
    if 2016 <= oy <= 2025: o[t][oy - 2016] += 1
    cnt['경기 유치원'] += 1
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); IX.setdefault('layers', {})['cct'] = '👶 어린이집·유치원 유형별(국공립·직장·민간·가정 · 병설·단설·사립)'
tot = 0
for gu, dd in OUT.items():
    if not os.path.isdir(os.path.join(R, gu)): continue
    sd = gu[:2]
    doc = {'schema': 'tg-cct/1', 'gu': gu, 'ccYears': YS[sd], 'ccGroups': CCG, 'kgYears': KY if sd == '11' else list(range(2016, 2026)), 'kgGroups': KGG if sd == '11' else KGN,
           'source': ('서울시 어린이집 정보(서울 열린데이터광장 ChildCareInfo · 인가일·폐지일·유형) · 서울특별시교육청 연도별 학교 위도 경도(공공데이터포털 15152021 · 2014~2025)' if sd == '11' else '경기데이터드림 어린이집 현황(ChildHouse · 인가일·폐지일·유형 · 2025.7) · 교육부 유치원알리미 공시 일반 현황(' + os.path.basename(kgf) + ' · 설립유형·개원일 · 지금 문 연 곳만)'),
           'note': '어린이집 cc = 해마다 그해 말 운영 수 · cco 그해 인가 · ccc 그해 폐지 · 국공립 = 구립·시립 등(정책으로 생김) · 직장 = 그 일터 아이(동네 수요와 무관 — 동네 수요 보기에서 뺀다) · 유치원 공립(병설) = 초등학교에 딸림' + ('' if sd == '11' else ' · 경기 유치원은 문 닫은 곳이 자료에 없어 「지금 수 · 개원 해」만'),
           'dong': dd}
    p = os.path.join(R, gu, 'cct.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); tot += os.path.getsize(p)
    x = next((x for x in IX['gus'] if x['gu'] == gu), None)
    if x is not None: x.setdefault('bytes', {})['cct'] = os.path.getsize(p)
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt), '구', len(OUT), tot, 'B')
