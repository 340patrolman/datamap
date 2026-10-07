# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.73.0 — 📜 이야기 층(지역 스토리) 굽기
#   원본: tools/story/seed-*.json — 코워크가 출처를 붙여 준 글(지식베이스/코드세션_지시_지역스토리레이어_20261007.md). 이 도구는 글을 고치지 않는다 — 자리만 푼다.
#   자리 풀기(손으로 좌표를 찍지 않는다):
#     stations  → data/r/stations.json 의 역 좌표(노선이 여럿이면 평균) · 그 점에서 350m 안에 걸친 행정동
#     jc / line → data/r/<구>/jcnm.json(ITS 표준노드링크 교차로·IC 이름) · 줄은 그 도로 이름이 붙은 노드를 위도 순으로
#     tgis      → data/tgis-seocho.json 교차로 이름 · her → data/heritage-seocho.json 이름 · area → data/live-seocho.json 장소 경계
#     bjd       → data/b2a.json 법정동 → 행정동(넓이 10% 넘는 것) · adm → 행정동 이름 그대로
#   행정동 경계: 13_관할경계/원자료/hjd20260701.geojson(통계청 SGIS · vuski/admdongkor 2026-07)
#   → data/stories.json
#   py -3.12 -X utf8 tools/story/story-bake.py
import json, os, glob, math
from shapely.geometry import shape, Point, LineString
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); D = os.path.join(ROOT, 'data')
NEAR = 350   # m
feats = json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features']
geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms)
ADM = {f['properties']['adm_cd2'][:8]: f['properties'] for f in feats}
def dname(k): p = ADM.get(k); return p['adm_nm'].split(' ', 1)[1] if p else k
def near_dongs(lon, lat, r=NEAR):
    kx = 111320 * math.cos(math.radians(lat)); ky = 110540
    q = Point(lon, lat).buffer(r / ky)   # 위도 기준 원 — 경도 쪽은 아래에서 다시 거른다
    out = []
    for i in tree.query(q):
        g = geoms[i]; c = g.boundary if not g.contains(Point(lon, lat)) else None
        if c is None: out.append(feats[i]['properties']['adm_cd2'][:8]); continue
        pt = c.interpolate(c.project(Point(lon, lat))); d = math.hypot((pt.x - lon) * kx, (pt.y - lat) * ky)
        if d <= r: out.append(feats[i]['properties']['adm_cd2'][:8])
    return out
def dong_at(lon, lat):
    for i in tree.query(Point(lon, lat)):
        if geoms[i].contains(Point(lon, lat)): return feats[i]['properties']['adm_cd2'][:8]
STN = {}
for x in json.load(open(os.path.join(D, 'r', 'stations.json'), encoding='utf-8'))['items']: STN.setdefault(x[0], []).append((x[2], x[3], x[1]))
B2A = json.load(open(os.path.join(D, 'b2a.json'), encoding='utf-8'))['b2a']
JC = {}
def jc(gu):
    if gu not in JC: JC[gu] = json.load(open(os.path.join(D, 'r', gu, 'jcnm.json'), encoding='utf-8'))['j']
    return JC[gu]
TG = json.load(open(os.path.join(D, 'tgis-seocho.json'), encoding='utf-8')); TGF = TG['fields']
HER = json.load(open(os.path.join(D, 'heritage-seocho.json'), encoding='utf-8'))['items']
LIVE = json.load(open(os.path.join(D, 'live-seocho.json'), encoding='utf-8'))['places']
miss = []
def resolve(a):
    adm, pts, lines, areas, gus = [], [], [], [], []
    def add(ks):
        for k in ks:
            if k and k not in adm: adm.append(k)
    for n in a.get('stations', []):
        L = STN.get(n)
        if not L: miss.append('역 ' + n); continue
        lon = sum(x[0] for x in L) / len(L); lat = sum(x[1] for x in L) / len(L)
        pts.append([round(lon, 5), round(lat, 5), n + '역', 'stn']); add(near_dongs(lon, lat))
    for gu, nm in a.get('jc', []):
        h = [x for x in jc(gu) if x[0] == nm]
        if not h: miss.append('교차로 ' + nm); continue
        pts.append([h[0][1], h[0][2], nm, 'jc']); add([dong_at(h[0][1], h[0][2])])
    for nm in a.get('tgis', []):
        h = [x for x in TG['items'] if x[1] == nm]
        if not h: miss.append('T-GIS ' + nm); continue
        pts.append([h[0][3], h[0][2], nm, 'tgis']); add(near_dongs(h[0][3], h[0][2]))
    for nm in a.get('her', []):
        h = [x for x in HER if x['name'] == nm and x.get('lat')]
        if not h: miss.append('국가유산 ' + nm); continue
        pts.append([round(h[0]['lon'], 5), round(h[0]['lat'], 5), nm, 'her']); add([dong_at(h[0]['lon'], h[0]['lat'])])
    for nm in a.get('area', []):
        h = [x for x in LIVE if x['name'] == nm]
        if not h: miss.append('장소 ' + nm); continue
        ring = [[round(p[0], 5), round(p[1], 5)] for p in h[0]['rings'][0]]; areas.append(ring)
        g = shape({'type': 'Polygon', 'coordinates': [ring]})
        for i in tree.query(g):
            if geoms[i].intersection(g).area >= g.area * 0.05: add([feats[i]['properties']['adm_cd2'][:8]])   # 장소 넓이의 5% 넘게 걸친 동만(강 건너 스친 동 빼기)
    ln = a.get('line')
    if ln:
        if 'pts' in ln:
            P = []
            for gu, nm in ln['pts']:
                h = [x for x in jc(gu) if x[0] == nm]
                if h: P.append([h[0][1], h[0][2]])
                else: miss.append('교차로 ' + nm)
        else:   # 같은 도로 이름이 붙은 노드 — from·to 사이 위도만
            J = jc(ln['gu']); f = [x for x in J if x[0] == ln['from']]; t = [x for x in J if x[0] == ln['to']]
            la0 = max(x[2] for x in f); la1 = min(x[2] for x in t)
            P = sorted({(x[1], x[2]) for x in J if ln['road'] in x[5].split('·') and la1 <= x[2] <= la0}, key=lambda q: -q[1])
            P = [list(q) for q in P]
        if len(P) >= 2:
            lines.append(P); L = LineString(P)
            for i in tree.query(L):
                if geoms[i].intersects(L): add([feats[i]['properties']['adm_cd2'][:8]])
    for gu, nm in a.get('bjd', []):
        h = [(k, v) for k, v in B2A.items() if v['gu'] == gu and v['n'] == nm]
        if not h: miss.append('법정동 ' + nm); continue
        add([x[0] for x in h[0][1]['a'] if x[2] >= 10])
    for gu, nm in a.get('adm', []):
        h = [k for k, p in ADM.items() if p['sgg'] == gu and p['adm_nm'].split(' ')[-1] == nm]
        if not h: miss.append('행정동 ' + nm); continue
        add(h)
    if a.get('gu'): gus.append(a['gu'])
    o = {'adm': adm, 'names': {k: dname(k) for k in adm}}
    if adm and not pts and not lines and not areas:   # 동 단위 이야기 — 표시는 첫 동 안쪽 한 점(정확한 자리 아님 · 지도에 빈 동그라미)
        i = next(j for j, f in enumerate(feats) if f['properties']['adm_cd2'][:8] == adm[0]); rp = geoms[i].representative_point(); o['cen'] = [round(rp.x, 5), round(rp.y, 5)]
    if pts: o['pts'] = pts
    if lines: o['lines'] = lines
    if areas: o['areas'] = areas
    if gus: o['gu'] = gus
    if a.get('region'): o['region'] = a['region']
    return o
OUT = []; SRC = []
for f in sorted(glob.glob(os.path.join(ROOT, 'tools', 'story', 'seed-*.json'))):
    j = json.load(open(f, encoding='utf-8')); SRC.append(os.path.basename(f))
    for s in j['stories']:
        s = dict(s); s['src_anchor'] = s.pop('anchor'); s['at'] = resolve(s['src_anchor']); del s['src_anchor']
        if not s.get('sources'): raise SystemExit('출처 없음: ' + s['id'])
        OUT.append(s)
ids = {s['id'] for s in OUT}
for s in OUT:
    for l in s.get('links', []):
        if l not in ids: raise SystemExit('없는 연결 ' + s['id'] + ' → ' + l)
doc = {'schema': 'tg-story/1', 'source': '코워크가 출처를 붙여 공급한 글(웹 검증 2026-10-07 · 그록 교차검증 반영) — 코드 세션은 글을 쓰지 않고 자리만 풀었다',
       'grade': {'A': '1차 사료·공문서', 'A-': '공공 편찬물·학술지', 'B': '언론·공공 해설', 'B-': '2차 인용(원문 대조 대기)', 'C': '위키·통념'},
       'cats': {'toponym': '지명', 'fengshui': '풍수·지형', 'disaster': '재난', 'war': '전쟁', 'development': '개발', 'society': '사회', 'traffic': '교통', 'politics': '정치·집회', 'history': '역사'},
       'anchor_note': '자리: 역·교차로·IC·국가유산·장소 경계는 지도에 있는 자료에서 · 역 둘레 동 = 역 좌표 350m 안에 걸친 행정동(출구 자리 아님) · 법정동은 행정동으로 넓이 10% 넘게 걸친 것',
       'files': SRC, 'items': OUT}
json.dump(doc, open(os.path.join(D, 'stories.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
for s in OUT: print(s['id'], '·', ', '.join(s['at']['names'].values()), '· 점', len(s['at'].get('pts', [])), '· 줄', len(s['at'].get('lines', [])))
print('못 찾음', miss); print(len(OUT), '건', os.path.getsize(os.path.join(D, 'stories.json')), 'B')
