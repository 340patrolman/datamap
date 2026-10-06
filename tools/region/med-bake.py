# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.42.0 — 🏥 병·의원 현황(개업·폐업 흐름) — 소유자 2026-10-06 「읍면동별 병의원 현황 · 언제 개업하고 어떻게 되는지」
#   출처 = 행정안전부 지방행정인허가(LOCALDATA) 건강_의원(공공데이터포털 15045024) · 건강_병원(15045025) · 2025-11-27 · 이용허락 제한 없음
#   원자료 07_API키/out/medical/clinics.csv · hospitals.csv(cp949 · 좌표 EPSG:5174 중부원점 TM) — 받는 법은 메모리 localdata-referer
#   ① data/med-dong.json = 행정동마다 [경도, 위도, 이름, 영업 중 종류별 수(MT), 해마다 개업 수(Y0~), 해마다 폐업 수, 2010~2020 개업 코호트 수, 그중 5년 안 폐업 수, 폐업한 곳 운영 개월 합, 폐업 수]
#   ② r/<구>/med.json = 한 곳씩 — 영업·휴업 [x m, y m, 종류, 과목(이름으로 추정), 개업 연월, 병상, 의료인, 이름, 휴업 1] · 폐업 [x, y, 종류, 과목, 개업 연월, 폐업 연월](이름 없음 — 개인 이름이 든 상호가 많다)
#   「제외/삭제/전출」은 뺀다(다른 시군구로 옮긴 기록) · 좌표 없는 기록(대개 오래된 폐업)은 동에 못 붙여 센 수만 적는다
#   py -3.12 -X utf8 tools/region/med-bake.py
import csv, json, os, collections, re
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); SRC = os.path.join(KB, '07_API키', 'out', 'medical'); HJD = os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson')
MT = ['의원', '치과의원', '한의원', '병원', '요양병원', '한방병원', '종합병원', '치과병원', '정신병원', '보건소·지소·진료소', '조산원']
def mtype(u):
    u = u or ''
    if u.startswith('요양병원'): return 4
    if u.startswith('보건') : return 9
    return MT.index(u) if u in MT else (0 if u == '' else None)
SP = [('소아', '소아청소년과'), ('이비인후', '이비인후과'), ('정형', '정형외과'), ('피부', '피부과'), ('안과', '안과'), ('산부인', '산부인과'), ('여성', '산부인과'), ('비뇨', '비뇨의학과'), ('정신', '정신건강의학과'), ('마음', '정신건강의학과'),
      ('성형', '성형외과'), ('재활', '재활의학과'), ('통증', '마취통증의학과'), ('마취', '마취통증의학과'), ('가정의학', '가정의학과'), ('영상', '영상의학과'), ('신경외과', '신경외과'), ('신경과', '신경과'), ('내과', '내과'), ('외과', '외과')]
SPN = ['미상'] + sorted({x[1] for x in SP})
def spec(name, t, subj=''):   # 의원 과목 — ① 상호(○○내과) ② 상호에 없으면 신고 진료과목이 하나뿐일 때 그 과목
    if t != 0: return 0
    for k, v in SP:
        if k in (name or ''): return SPN.index(v)
    L = [x.strip() for x in (subj or '').split(',') if x.strip()]
    if len(L) == 1 and L[0] in SPN: return SPN.index(L[0])
    return 0
def ym(d):
    d = (d or '').strip()
    m = re.match(r'(\d{4})-?(\d{2})', d)
    return int(m.group(1)) * 100 + int(m.group(2)) if m else None
Y0, Y1 = 2006, 2026
tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True)
G = json.load(open(HJD, encoding='utf-8'))
F = [(shape(f['geometry']), f['properties']['adm_cd2'][:8], f['properties']['adm_nm'].split(' ')[-1]) for f in G['features']]
T = STRtree([x[0] for x in F])
def dong_of(lo, la):
    p = Point(lo, la)
    for i in T.query(p):
        if F[i][0].contains(p): return i
    return None
D = {}; PTS = collections.defaultdict(list); cnt = collections.Counter()
for fn in ('clinics.csv', 'hospitals.csv'):
    R = csv.reader(open(os.path.join(SRC, fn), encoding='cp949', errors='replace')); H = next(R); ix = {h: i for i, h in enumerate(H)}
    for r in R:
        g = lambda k: (r[ix[k]] if k in ix and ix[k] < len(r) else '').strip()
        st = g('영업상태명')
        if st.startswith('제외'): cnt['전출·제외'] += 1; continue
        t = mtype(g('업태구분명') or g('의료기관종별명'))
        if t is None: cnt['종류 모름'] += 1; continue
        try: x, y = float(g('좌표정보(X)')), float(g('좌표정보(Y)'))
        except ValueError: cnt['좌표 없음 ' + ('폐업' if st != '영업/정상' else '영업')] += 1; continue
        lo, la = tr.transform(x, y)
        if not (33 < la < 39 and 124 < lo < 132): cnt['좌표 이상'] += 1; continue
        di = dong_of(lo, la)
        if di is None: cnt['동 밖'] += 1; continue
        k8 = F[di][1]; d = D.get(k8)
        if not d:
            c = F[di][0].representative_point(); d = D[k8] = {'c': [round(c.x, 5), round(c.y, 5)], 'n': F[di][2], 'open': [0] * len(MT), 'yo': [0] * (Y1 - Y0 + 1), 'yc': [0] * (Y1 - Y0 + 1), 'co': 0, 'c5': 0, 'lm': 0, 'ln': 0, 'sp': collections.Counter()}
        o = ym(g('인허가일자')); closed = st not in ('영업/정상', '휴업'); cl = (ym(g('폐업일자')) or ym(g('인허가취소일자'))) if closed else None
        sp = spec(g('사업장명'), t, g('진료과목내용명'))
        if not closed: d['open'][t] += 1; d['sp'][sp] += 1; cnt['영업' if st == '영업/정상' else '휴업'] += 1
        else: cnt['폐업'] += 1
        if o and Y0 <= o // 100 <= Y1: d['yo'][o // 100 - Y0] += 1
        if cl and Y0 <= cl // 100 <= Y1: d['yc'][cl // 100 - Y0] += 1
        if o and 2010 <= o // 100 <= 2020:
            d['co'] += 1
            if cl and (cl // 100 * 12 + cl % 100) - (o // 100 * 12 + o % 100) < 60: d['c5'] += 1
        if o and cl and cl >= o: d['lm'] += (cl // 100 * 12 + cl % 100) - (o // 100 * 12 + o % 100); d['ln'] += 1
        gu = k8[:5]; nm = g('사업장명')
        PTS[gu].append((lo, la, t, sp, o or 0, cl, closed, st == '휴업', int(float(g('병상수') or 0)), int(float(g('의료인수') or 0)), nm))
        cnt['동에 붙음'] += 1
out = {k: d['c'] + [d['n'], d['open'], d['yo'], d['yc'], d['co'], d['c5'], d['lm'], d['ln'], {str(a): b for a, b in d['sp'].items() if a}] for k, d in D.items()}
res = {'schema': 'tg-med-dong/1', 'types': MT, 'specs': SPN, 'y0': Y0, 'y1': Y1,
       'source': '행정안전부 지방행정인허가(LOCALDATA) 건강_의원 15045024 · 건강_병원 15045025(공공데이터포털 · 2025-11-27 · 이용허락 제한 없음) · 행정동 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0)',
       'fields': 'dong = {행정동 8자리: [경도, 위도, 이름, 영업 중 종류별 수(types), 해마다 개업(y0~y1), 해마다 폐업, 2010~2020 개업 수, 그중 5년 안 폐업, 폐업한 곳 운영 개월 합, 그 수, {의원 과목(이름으로 추정): 영업 수}]}',
       'note': '인허가 기록 그대로 — 개업 = 인허가일자 · 폐업 = 폐업일자(직권폐업은 취소일자) · 전출·제외 기록은 뺌 · 좌표 없는 기록(대개 오래된 폐업)은 동에 못 붙였다 · 의원 과목 = 상호(○○내과·○○소아과…)로 추정 · 상호에 없으면 신고 진료과목이 하나뿐일 때 그 과목(여러 개 신고한 의원은 「미상」)',
       'counts': dict(cnt), 'dong': out}
p = os.path.join(ROOT, 'data', 'med-dong.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); KX, KY = 88800, 111000; nb = {}
for g in IX['gus']:
    P = PTS.get(g['gu'])
    if not P: continue
    O = [min(q[0] for q in P), min(q[1] for q in P)]; rows = []
    for q in P:
        x, y = round((q[0] - O[0]) * KX), round((q[1] - O[1]) * KY)
        rows.append([x, y, q[2], q[3], q[4], q[5] or 0] if q[6] else [x, y, q[2], q[3], q[4], q[8], q[9], q[10], 1 if q[7] else 0])
    doc = {'schema': 'tg-med/1', 'gu': g['gu'], 'o': O, 'k': [KX, KY], 'types': MT, 'specs': SPN, 'source': res['source'], 'fields': '영업·휴업 = [x m, y m, 종류, 과목(추정), 개업 연월, 병상, 의료인, 상호, 휴업 1] · 폐업 = [x, y, 종류, 과목, 개업 연월, 폐업 연월](상호 없음)', 'pts': rows}
    pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'med.json')
    if os.path.isdir(os.path.dirname(pth)): json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); nb[g['gu']] = os.path.getsize(pth)
for g in IX['gus']:
    if g['gu'] in nb: g.setdefault('bytes', {})['med'] = nb[g['gu']]
IX['layers']['med'] = '병·의원(영업·폐업 · 한 곳씩)'
json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt)); print('동', len(out), '· 동 요약', os.path.getsize(p) // 1024, 'KB · 구 파일', len(nb), sum(nb.values()) // 1024, 'KB · 구 코드 없는 점', sum(len(v) for k, v in PTS.items() if k not in nb))
