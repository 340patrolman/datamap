# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🛣 서울까지 승용차 몇 분(소유자 2026-10-10 「고속도로 주변으로 접근성 시간을 그라데이션으로 · 살아볼 동네」) → data/reach-seoul.json
#   재료 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(MOCT_LINK · MOCT_NODE — its.go.kr/nodelink 공개 파일) 하나뿐
#   셈 = 링크 길이 ÷ 제한속도(MAX_SPD)를 그 링크의 시간으로 보고, 방향(F_NODE → T_NODE)을 지켜 가장 빠른 길을 찾는다(다익스트라 · 목적지에서 거꾸로)
#   **막힘·신호·요금소·회전 금지가 없는 값이다** — 실제보다 짧다(시내 구간일수록 크게). 화면에는 「제한속도로 막힘없이 달릴 때」라고 밝힌다. 견주는 용도이지 도착 예정 시간이 아니다
#   목적지 둘: 서울시청(도심) · 강남역(강남) — 좌표에서 가장 가까운 등급 4 이상 도로의 노드
#   싣는 도로 = 등급 1 고속 · 2 도시고속 · 3 일반국도(넓게 볼 때 쓰는 층) + 시군구마다 한 값(그 구 안 등급 1~6 도로 노드의 가운데값·가장 빠른 값)
#   py -3.12 -X utf8 tools/region/reach-bake.py [MOCT_LINK.shp 폴더]   (처음 한 번은 원본을 읽어 캐시를 만든다 · 몇 분)
import json, os, sys, heapq, pickle, datetime, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
CACHE = os.path.join(SRC, 'reach_cache.pkl'); VER = '2026-09-14'
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}
DEST = [['시청', '서울시청', 126.9784, 37.5665], ['강남', '강남역', 127.0276, 37.4979]]
def load():
    if os.path.exists(CACHE): return pickle.load(open(CACHE, 'rb'))
    import shapefile
    from pyproj import Transformer
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True)
    n = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(n.fields[1:])}; NODE = {}
    for sr in n.iterShapeRecords():
        x, y = tr.transform(*sr.shape.points[0]); NODE[sr.record[fi['NODE_ID']]] = (round(x, 5), round(y, 5))
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}; LINK = []; nospd = collections.Counter()
    for sr in r.iterShapeRecords():
        rec = sr.record; rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        spd = int(rec[fi['MAX_SPD']] or 0); ln = float(rec[fi['LENGTH']] or 0)
        if spd <= 0 or ln <= 0: nospd[rk] += 1; continue   # 제한속도·길이가 없는 링크는 길에서 뺀다(값을 지어 넣지 않는다)
        geo = [tr.transform(x, y) for x, y in sr.shape.points] if rk <= 3 else None
        LINK.append((rec[fi['LINK_ID']], rec[fi['F_NODE']], rec[fi['T_NODE']], rk, spd, ln, (rec[fi['ROAD_NAME']] or '').strip(), geo))
    d = {'NODE': NODE, 'LINK': LINK, 'nospd': dict(nospd)}; pickle.dump(d, open(CACHE, 'wb'), protocol=4); return d
def dijk(REV, src):
    D = {src: 0.0}; h = [(0.0, src)]
    while h:
        d, u = heapq.heappop(h)
        if d > D.get(u, 1e18): continue
        for v, w in REV.get(u, ()):
            nd = d + w
            if nd < D.get(v, 1e18): D[v] = nd; heapq.heappush(h, (nd, v))
    return D
def main():
    from shapely.geometry import LineString, shape, Point
    from shapely.strtree import STRtree
    d = load(); NODE, LINK = d['NODE'], d['LINK']; print('노드', len(NODE), '· 링크', len(LINK), '· 제한속도·길이 없어 뺀 링크', d['nospd'])
    REV = collections.defaultdict(list); big = set()
    for lid, f, t, rk, spd, ln, nm, geo in LINK:
        REV[t].append((f, ln / (spd / 3.6) / 60.0))   # 분 · 거꾸로 그래프(t 에 닿으려면 f 에서)
        if rk <= 4: big.add(f); big.add(t)
    T = []
    for key, nm, lon, lat in DEST:
        nid = min(big, key=lambda k: (NODE[k][0] - lon) ** 2 + (NODE[k][1] - lat) ** 2) if big else None
        D = dijk(REV, nid); T.append(D); print(nm, '노드', nid, NODE[nid], '· 닿는 노드', len(D))
    roads = []; skip = 0
    for lid, f, t, rk, spd, ln, nm, geo in LINK:
        if rk > 3: continue
        m = [T[k].get(f) for k in range(len(DEST))]
        if m[0] is None and m[1] is None: skip += 1; continue   # 섬 등 길이 이어지지 않는 링크
        q = list(LineString(geo).simplify(0.0006, preserve_topology=False).coords); enc = []; px = py = 0
        for a, b in q: ix, iy = round(a * 1e4), round(b * 1e4); enc += [ix - px, iy - py]; px, py = ix, iy
        roads.append([rk, -1 if m[0] is None else round(m[0]), -1 if m[1] is None else round(m[1]), enc])
    # 시군구 값 — 그 구 경계 안 등급 1~6 도로 노드의 시간(가운데값·가장 빠른 값) · 경계 = data/base/sgg.json
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    feats = json.load(open(os.path.join(ROOT, 'data', 'base', 'sgg.json'), encoding='utf-8'))['sgg']; gus = {}
    if feats:
        gs = [unary_union([Polygon(r).buffer(0) for r in x['rings'] if len(r) >= 4]) for x in feats]; st = STRtree(gs); mid = set()
        for lid, f, t, rk, spd, ln, nm, geo in LINK:
            if rk <= 6: mid.add(f)
        acc = collections.defaultdict(lambda: [[], []])
        for nid in mid:
            p = Point(NODE[nid])
            for i in st.query(p):
                if gs[i].contains(p):
                    for k in range(len(DEST)):
                        v = T[k].get(nid)
                        if v is not None: acc[i][k].append(v)
                    break
        for i, a in acc.items():
            code = feats[i]['sido'] + ' ' + feats[i]['name']; row = [feats[i]['c']]
            for k in range(len(DEST)):
                v = sorted(a[k]); row += [round(v[len(v) // 2]), round(v[0]), len(v)] if v else [-1, -1, 0]
            gus[code] = row
    doc = {'schema': 'tg-reach/1', 'made': datetime.date.today().isoformat(),
           'source': '국가교통정보센터(ITS) 전국 표준노드링크 %s판 — MOCT_LINK(길이·제한속도·방향)·MOCT_NODE · its.go.kr/nodelink 공개 파일' % VER,
           'how': '링크 길이 ÷ 제한속도를 그 링크의 시간으로 보고 방향을 지켜 가장 빠른 길을 찾았다(다익스트라). 목적지 = 좌표에서 가장 가까운 등급 4 이상 도로 노드.',
           'note': ['**막힘·신호·요금소·회전 금지·진입 대기가 없는 값이다 — 실제보다 짧다**(시내 구간일수록 크게 짧다). 도착 예정 시간이 아니라 자리끼리 견주는 값이다',
                    '화면에 낼 때 「제한속도로 막힘없이 달릴 때」라고 밝힌다 · 실제 출퇴근 시간은 이 자료로 알 수 없다',
                    '제한속도나 길이가 비어 있는 링크는 길에서 뺐다(값을 넣지 않았다) — 그래서 길이 끊겨 -1(닿지 않음)인 곳이 있다 · 섬은 뱃길이 없어 -1',
                    '도로 선은 등급 1~3 만, 약 60m 로 단순화(넓게 볼 때 쓰는 층) · 분은 그 링크가 시작하는 자리에서 잰 값',
                    '시군구 값은 그 구 경계 안 등급 1~6 도로 노드들의 가운데값과 가장 빠른 값 — 구가 넓으면 안에서 차이가 크다'],
           'dest': [[x[0], x[1], x[2], x[3]] for x in DEST],
           'fields': 'roads[[등급 1 고속·2 도시고속·3 일반국도, 서울시청까지 분(-1 = 닿지 않음), 강남역까지 분, 선 = 경도·위도×1e4 정수 첫 점 + 차이]] · gus{「시도 시군구」(data/base/sgg.json 과 같은 이름 · 경기 일반구는 시로): [가운데 [경도, 위도], 시청 가운데값 분, 시청 가장 빠른 분, 노드 수, 강남 가운데값, 강남 가장 빠른, 노드 수]}',
           'gus': gus, 'roads': roads}
    r3 = [x for x in roads if x[0] == 3]; doc['roads'] = [x for x in roads if x[0] < 3]; doc['more'] = 'data/reach-seoul-r3.json(등급 3 일반국도 선 — 같은 꼴 · 가까이 볼 때만 읽는다)'
    p = os.path.join(ROOT, 'data', 'reach-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    d3 = {k: doc[k] for k in ('schema', 'made', 'source', 'how', 'note', 'dest')}; d3['fields'] = 'roads[[등급 3 일반국도, 서울시청까지 분(-1 = 닿지 않음), 강남역까지 분, 선 = 경도·위도×1e4 정수 첫 점 + 차이]] — data/reach-seoul.json 의 이어지는 장'; d3['roads'] = r3
    p3 = os.path.join(ROOT, 'data', 'reach-seoul-r3.json'); json.dump(d3, open(p3, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('도로 선 고속·도시고속', len(doc['roads']), '· 국도', len(r3), '· 닿지 않아 뺀 선', skip, '· 시군구', len(gus), '· 바이트', os.path.getsize(p), os.path.getsize(p3))
    for c in ('서울특별시 서초구', '경기도 화성시', '경기도 과천시', '충청북도 청주시', '충청남도 천안시', '대전광역시 유성구', '부산광역시 해운대구', '강원특별자치도 강릉시', '제주특별자치도 제주시'): print(c, gus.get(c))
if __name__ == '__main__': main()
