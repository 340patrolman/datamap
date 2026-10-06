# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.55.0 — 🏪 업종별 개업·폐업·생존율 전국(소유자 「점포 개업·폐업 업종과 업종별 생존율·기간」 · 「권고 모두 진행」 2026-10-06) → data/r/<구>/bizsv.json
#   원자료 07_API키/out/biz/*.csv = 지방행정 인허가(LOCALDATA · 공공데이터포털 15045016 일반음식점 · 15006730 휴게음식점 · 15044973 제과점 · 15045037 미용업 · 15045109 노래연습장 · 15045073 PC방 · 15045048 체력단련장 · 15044964 세탁업 · 15045036 약국 · 15045050 동물병원 · 15045028 안경업 · 15045045 체육도장업 · 의원(15045024) · 숙박업(여관·모텔 등))
#   가게마다 인허가일자·폐업일자·업태·좌표(EPSG:5174) → 행정동(SGIS 경계) · 사업장명·전화·주소는 읽지 않는다
#   동마다 업종마다 [지금 영업, 해마다 개업 ×11(2016~2026), 해마다 폐업 ×11, 1년 대상, 1년 생존, 3년 대상, 3년 생존, 5년 대상, 5년 생존, 폐업 가게 영업일 합, 폐업 가게 수]
#   생존 = 그 날까지 폐업하지 않음(휴업은 살아 있는 것으로) · 대상 = 2016년 1월 1일 이후 개업하고 기준일보다 N년 앞서 연 가게
#   py -3.12 -X utf8 tools/region/biz-bake.py
import csv, json, os, sys, datetime, collections
import numpy as np, shapely
from shapely.geometry import shape
from shapely.strtree import STRtree
from pyproj import Transformer
csv.field_size_limit(10 ** 8)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); SRC = os.path.join(KB, '07_API키', 'out', 'biz'); R = os.path.join(ROOT, 'data', 'r')
feats = json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features']
geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms); KEYS = [f['properties']['adm_cd2'][:8] for f in feats]
tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True)
YRS = list(range(2016, 2027))
CATS = ['한식', '중식', '일식·횟집', '양식·뷔페', '고기구이', '분식·김밥', '치킨·호프', '주점', '카페·찻집', '제과·디저트', '패스트푸드', '편의점', '외국음식', '기타 음식점', '미용실', '피부관리', '네일·메이크업', '노래방', 'PC방', '헬스장', '세탁소', '키즈카페', '의원', '치과', '한의원', '약국', '동물병원', '안경원', '체육도장', '숙박(여관·모텔)']
def cat(f, u):
    if f == 'general_restaurants':
        return {'한식': '한식', '중국식': '중식', '일식': '일식·횟집', '횟집': '일식·횟집', '복어취급': '일식·횟집', '경양식': '양식·뷔페', '패밀리레스트랑': '양식·뷔페', '뷔페식': '양식·뷔페', '식육(숯불구이)': '고기구이', '분식': '분식·김밥', '김밥(도시락)': '분식·김밥',
                '호프/통닭': '치킨·호프', '통닭(치킨)': '치킨·호프', '정종/대포집/소주방': '주점', '감성주점': '주점', '라이브카페': '주점', '까페': '카페·찻집', '전통찻집': '카페·찻집', '패스트푸드': '패스트푸드', '외국음식전문점(인도,태국등)': '외국음식'}.get(u, '기타 음식점')
    if f == 'rest_cafes':
        return {'커피숍': '카페·찻집', '다방': '카페·찻집', '전통찻집': '카페·찻집', '떡카페': '카페·찻집', '편의점': '편의점', '패스트푸드': '패스트푸드', '과자점': '제과·디저트', '아이스크림': '제과·디저트', '키즈카페': '키즈카페'}.get(u, '기타 음식점')
    if f == 'bakeries': return '제과·디저트'
    if f == 'beauty_salons': return {'일반미용업': '미용실', '피부미용업': '피부관리', '네일아트업': '네일·메이크업', '메이크업업': '네일·메이크업'}.get(u, '미용실')
    if f == 'clinics': return {'치과의원': '치과', '한의원': '한의원'}.get(u, '의원' if u == '의원' else None)
    if f == 'lodgings': return '숙박(여관·모텔)'
    return {'karaoke_rooms': '노래방', 'pc_bangs': 'PC방', 'fitness_centers': '헬스장', 'laundries': '세탁소', 'pharmacies': '약국', 'animal_hospitals': '동물병원', 'optical_shops': '안경원', 'martial_arts_dojo': '체육도장'}[f]
def dt(s):
    try: return datetime.date(int(s[:4]), int(s[5:7]), int(s[8:10]))
    except Exception: return None
REC = []; ASOF = datetime.date(2000, 1, 1); cnt = collections.Counter()
FP = {'clinics': os.path.join(KB, '07_API키', 'out', 'medical', 'clinics.csv'), 'lodgings': os.path.join(KB, '07_API키', 'out', 'lodging', 'lodgings.csv')}
for f in ['general_restaurants', 'rest_cafes', 'bakeries', 'beauty_salons', 'karaoke_rooms', 'pc_bangs', 'fitness_centers', 'laundries', 'pharmacies', 'animal_hospitals', 'optical_shops', 'martial_arts_dojo', 'clinics', 'lodgings']:
    xs, ys, rec = [], [], []
    with open(FP.get(f) or os.path.join(SRC, f + '.csv'), encoding='cp949', errors='replace', newline='') as fh:
        for r in csv.DictReader(fh):
            stt = r['영업상태명'] or ''; dead = ('폐업' in stt) or ('취소' in stt) or ('말소' in stt); o = dt(r['인허가일자']); c = (dt(r.get('폐업일자') or '') or dt(r.get('인허가취소일자') or '')) if dead else None
            if not o: cnt['날짜 없음'] += 1; continue
            if dead and not c: cnt['폐업일 없음'] += 1; continue
            try: x, y = float(r['좌표정보(X)']), float(r['좌표정보(Y)'])
            except ValueError: cnt['좌표 없음'] += 1; continue
            if c and c.year < 2016: continue
            cn = cat(f, r.get('업태구분명') or '')
            if not cn: continue
            ASOF = max(ASOF, o, c or o); xs.append(x); ys.append(y); rec.append((CATS.index(cn), o, c))
    lon, lat = tr.transform(np.array(xs), np.array(ys)); pts = shapely.points(lon, lat)
    pi, gi = tree.query(pts, predicate='within'); D = np.full(len(rec), -1); D[pi] = gi
    for i, rr in enumerate(rec):
        if D[i] < 0: cnt['경계 밖'] += 1; continue
        REC.append((KEYS[D[i]],) + rr)
    print(f, len(rec), flush=True)
ASOF = min(ASOF, datetime.date.today())   # 미래 날짜로 잘못 적힌 인허가가 있다
print('기준일', ASOF, dict(cnt), flush=True)
def addy(d, n):
    try: return d.replace(year=d.year + n)
    except ValueError: return d.replace(year=d.year + n, day=28)
N = len(YRS)
A = collections.defaultdict(lambda: collections.defaultdict(lambda: [0] * (1 + 2 * N + 8)))
for k, ci, o, c in REC:
    a = A[k][ci]
    if not c: a[0] += 1
    if o.year >= 2016: a[1 + YRS.index(min(o.year, 2026))] += 1
    if c and c.year >= 2016: a[1 + N + YRS.index(min(c.year, 2026))] += 1
    if o >= datetime.date(2016, 1, 1):
        for j, yy in enumerate((1, 3, 5)):
            if addy(o, yy) <= ASOF:
                a[1 + 2 * N + j * 2] += 1
                if not c or c > addy(o, yy): a[2 + 2 * N + j * 2] += 1
    if c and c.year >= 2016: a[1 + 2 * N + 6] += (c - o).days; a[1 + 2 * N + 7] += 1
G = collections.defaultdict(dict)
for k, v in A.items(): G[k[:5]][k] = {str(ci): x for ci, x in v.items()}
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); ng = 0
for g in IX['gus']:
    gu = g['gu']
    if gu not in G or not os.path.isdir(os.path.join(R, gu)): continue
    doc = {'schema': 'tg-biz/1', 'gu': gu, 'asof': str(ASOF), 'cats': CATS, 'years': YRS,
           'source': '지방행정 인허가(LOCALDATA · 공공데이터포털 일반음식점·휴게음식점·제과점·미용업·노래연습장·PC방·체력단련장·세탁업·약국·동물병원·안경업·체육도장업·의원·숙박업 · 개업일·폐업일·좌표로 행정동)',
           'fields': 'dong = {행정동 8자리: {업종 자리: [지금 영업, 개업 ×11(2016~2026), 폐업 ×11, 1년 대상, 1년 생존, 3년 대상, 3년 생존, 5년 대상, 5년 생존, 폐업 가게 영업일 합, 폐업 가게 수]}}',
           'note': '생존 = 그 날까지 폐업 안 함(휴업 포함) · 대상 = 2016-01-01 이후 개업하고 기준일보다 N년 앞서 연 가게 · 폐업 가게 영업기간 = 2016년 이후 폐업한 가게의 개업~폐업 · 좌표 없는 가게 빠짐', 'dong': G[gu]}
    fn = os.path.join(R, gu, 'bizsv.json'); json.dump(doc, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); g.setdefault('bytes', {})['bizsv'] = os.path.getsize(fn); ng += 1
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', ng, '가게', len(REC))
