# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🛣 주요 지점별 영향권(소유자 2026-10-10 「고속도로 국도들을 이어주고 주요 지점별 영향권으로 그라데이션으로 표현」) → data/reach-hubs.json
#   reach-bake.py 와 같은 셈(ITS 표준노드링크 · 길이 ÷ 제한속도 · 방향을 지킨 가장 빠른 길)을 주요 지점 여러 곳에 대해 하고, 선마다 「가장 빠른 주요 지점과 그 분」을 붙인다
#   주요 지점 = **후보**다(소유자가 고른다) — 자리는 지어내지 않고 이미 있는 역 좌표에서(data/train-seoul.json 기차역 · data/r/stations.json 지하철역)
#   **막힘·신호·요금소가 없는 값 — 실제보다 짧다** · 견주는 값
#   py -3.12 -X utf8 tools/region/reachhub-bake.py   (reach-bake.py 가 만든 캐시 C:/Users/knpth/regionwork/nl/reach_cache.pkl 을 쓴다)
import json, os, sys, heapq, pickle, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
HUBS = [['시청', '서울 도심(시청역)', 'S', '시청'], ['강남', '강남(강남역)', 'S', '강남'], ['여의도', '여의도(여의도역)', 'S', '여의도'], ['판교', '판교(판교역)', 'S', '판교'],
        ['수원', '수원(수원역)', 'T', '수원'], ['인천', '인천(인천시청역)', 'K', '인천시청'], ['천안아산', '천안·아산(천안아산역)', 'T', '천안아산'], ['오송', '청주·세종 관문(오송역)', 'T', '오송'],
        ['대전', '대전(대전역)', 'T', '대전'], ['춘천', '춘천(춘천역)', 'T', '춘천'], ['원주', '원주(원주역)', 'T', '원주'], ['강릉', '강릉(강릉역)', 'T', '강릉'],
        ['전주', '전주(전주역)', 'T', '전주'], ['광주', '광주(광주송정역)', 'T', '광주송정'], ['동대구', '대구(동대구역)', 'T', '동대구'], ['부산', '부산(부산역)', 'T', '부산']]
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
    from shapely.geometry import LineString, Point, Polygon
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    TR = json.load(open(os.path.join(ROOT, 'data', 'train-seoul.json'), encoding='utf-8'))['stn']; XY = {}
    for fn in ('r/stations.json', 'stations-kr.json'):
        for it in json.load(open(os.path.join(ROOT, 'data', fn), encoding='utf-8'))['items']:
            nm = it[0][:-1] if it[0].endswith('역') and len(it[0]) > 2 else it[0]; XY.setdefault(nm, [it[2], it[3]])
    dest = []
    for key, label, kind, nm in HUBS:
        ll = TR.get(nm, {}).get('ll') if kind == 'T' else XY.get(nm)
        if not ll: print('자리 없음 — 뺌', label); continue
        dest.append([key, label, ll[0], ll[1]])
    d = pickle.load(open(os.path.join(SRC, 'reach_cache.pkl'), 'rb')); NODE, LINK = d['NODE'], d['LINK']
    REV = collections.defaultdict(list); big = set()
    for lid, f, t, rk, spd, ln, nm, geo in LINK:
        REV[t].append((f, ln / (spd / 3.6) / 60.0))
        if rk <= 4: big.add(f); big.add(t)
    T = []
    for key, label, lon, lat in dest:
        nid = min(big, key=lambda k: (NODE[k][0] - lon) ** 2 + ((NODE[k][1] - lat) * 1.25) ** 2); T.append(dijk(REV, nid)); print(label, NODE[nid], len(T[-1]), flush=True)
    N = len(dest); roads = []
    def row(nid):
        m = [T[k].get(nid) for k in range(N)]; best = min((v, k) for k, v in enumerate(m) if v is not None) if any(v is not None for v in m) else None
        return [-1 if v is None else round(v) for v in m], (best[1] if best else -1)
    for lid, f, t, rk, spd, ln, nm, geo in LINK:
        if rk > 2: continue
        m, b = row(f)
        if b < 0: continue
        q = list(LineString(geo).simplify(0.0006, preserve_topology=False).coords); enc = []; px = py = 0
        for a, c in q: ix, iy = round(a * 1e4), round(c * 1e4); enc += [ix - px, iy - py]; px, py = ix, iy
        roads.append([rk, m, b, enc])
    feats = json.load(open(os.path.join(ROOT, 'data', 'base', 'sgg.json'), encoding='utf-8'))['sgg']; gs = [unary_union([Polygon(r).buffer(0) for r in x['rings'] if len(r) >= 4]) for x in feats]; st = STRtree(gs)
    acc = collections.defaultdict(lambda: [[] for _ in range(N)]); mid = set(f for lid, f, t, rk, spd, ln, nm, geo in LINK if rk <= 6)
    for nid in mid:
        p = Point(NODE[nid])
        for i in st.query(p):
            if gs[i].contains(p):
                for k in range(N):
                    v = T[k].get(nid)
                    if v is not None: acc[i][k].append(v)
                break
    gus = {}
    for i, a in acc.items():
        md = [round(sorted(v)[len(v) // 2]) if v else -1 for v in a]; ok = [(v, k) for k, v in enumerate(md) if v >= 0]
        gus[feats[i]['sido'] + ' ' + feats[i]['name']] = [feats[i]['c'], md, min(ok)[1] if ok else -1]
    doc = {'schema': 'tg-reach-hubs/1', 'made': datetime.date.today().isoformat(),
           'source': '국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판 — MOCT_LINK(길이·제한속도·방향) · 주요 지점의 자리 = data/train-seoul.json(기차역)·data/r/stations.json(지하철역)',
           'how': 'data/reach-seoul.json 과 같은 셈(링크 길이 ÷ 제한속도 · 방향을 지킨 가장 빠른 길)을 주요 지점마다 하고, 선·시군구마다 가장 빠른 주요 지점을 골랐다.',
           'note': ['**막힘·신호·요금소·회전 금지가 없는 값이다 — 실제보다 짧다**(시내 구간일수록 크게). 견주는 값이지 도착 예정 시간이 아니다',
                    '주요 지점 %d곳은 **후보**다(2026-10-10 · 소유자가 고르기 전) — 어느 곳을 주요로 볼지 정해지면 다시 굽는다. 자리는 그 이름의 역 좌표를 썼다(도시의 중심이 아닐 수 있다)' % N,
                    '「가장 빠른 주요 지점」은 그 자리에서 승용차로 가장 빨리 닿는 후보일 뿐 생활권·통근권을 뜻하지 않는다(실제 통근 자료가 아니다)',
                    '도로 선은 등급 1 고속·2 도시고속만(약 60m 단순화) · 시군구 값은 그 구 안 등급 1~6 도로 노드의 가운데값'],
           'dest': dest,
           'fields': 'dest[[열쇠, 이름, 경도, 위도]] · roads[[등급, [dest 차례대로 분(-1 = 닿지 않음)], 가장 빠른 지점 번호, 선 = 경도·위도×1e4 정수 첫 점 + 차이]] · gus{「시도 시군구」: [가운데[경도, 위도], [dest 차례대로 가운데값 분], 가장 빠른 지점 번호]}',
           'gus': gus, 'roads': roads}
    p = os.path.join(ROOT, 'data', 'reach-hubs.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('지점', N, '· 도로 선', len(roads), '· 시군구', len(gus), '· 바이트', os.path.getsize(p))
    print('가장 빠른 지점별 시군구 수', collections.Counter(dest[v[2]][0] for v in gus.values() if v[2] >= 0))
    for c in ('경기도 화성시', '경기도 평택시', '충청남도 아산시', '충청북도 청주시', '세종특별자치시 세종시', '강원특별자치도 홍천군'): print(c, gus.get(c))
if __name__ == '__main__': main()
