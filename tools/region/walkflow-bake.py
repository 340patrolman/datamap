# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.79.0 — 🚶 예상 귀갓길(역·정류장 → 집) · 소유자 2026-10-07 「주민의 동선은 지하철 출입구·버스정류장에서 집으로 걸어가는 길 · 골목상권은 그렇게 된다 · 그런 곳에 편의점·가게가 있다」
#   모형(추정 · 관측이 아니다):
#     출발 = 저녁 귀가 시간(17~23시) 하차 인원 — 서울시 버스 정류장별·지하철 역별 시간대 하차(transit.json · 2026-06 하루 평균)
#            지하철은 OSM 출입구(railway=subway_entrance) 300m 안 것들에 똑같이 나눈다(없으면 역 자리)
#     도착 = 집계구(통계청 SGIS · jgg.json) 가운데 · 가구 수만큼 끌어당김
#     나눔 = 정류장마다 하차 인원을 걸음 거리 d 안 집계구에 가구 × e^(−d/λ) 비율로(λ 버스 400m · 지하철 800m · 끝 거리 2.5λ — 정류장 400m·역 800m 보행권 관행을 쓴 가정)
#     길 = OSM 걸을 수 있는 길(© OpenStreetMap contributors · ODbL · 2026-10-03) 최단 거리 · 고속·자동차 전용(motorway·trunk)과 foot=no 는 뺀다
#     ⚠ 지형(언덕·계단 회피)은 아직 없다 — 높이 자료(DEM)가 오면 걸음 비용에 경사를 넣는다(Tobler 걸음 함수)
#   검증(가설 · 관계장부식): 편의점(소상공인 상가업소 G20405)이 예상 동선 굵은 길 가까이에 몰리는가 — 길 길이 몫과 견줌
#   → data/r/<구>/walk.json  py -3.12 -X utf8 tools/region/walkflow-bake.py 11650
import json, os, sys, math, heapq, collections
import osmium
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r'); PBF = 'C:/Users/knpth/osmwork/kr.pbf'
GUS = sys.argv[1:] or ['11650']
H0, H1 = 17, 23
LAM = {'bus': 400, 'sub': 800}
NOWALK = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'construction', 'proposed', 'raceway', 'bus_guideway'}
def load(gu, f): return json.load(open(os.path.join(R, gu, f), encoding='utf-8'))
JG = {g: load(g, 'jgg.json') for g in GUS}; TR = {g: load(g, 'transit.json') for g in GUS}
bb = [180, 90, -180, -90]
for g in GUS:
    for it in JG[g]['items']:
        for ring in it[2]:
            for q in (ring if isinstance(ring[0][0], (int, float)) else [p for r2 in ring for p in r2]):
                bb = [min(bb[0], q[0]), min(bb[1], q[1]), max(bb[2], q[0]), max(bb[3], q[1])]
PAD = 0.015; bb = [bb[0] - PAD, bb[1] - PAD, bb[2] + PAD, bb[3] + PAD]
LAT0 = (bb[1] + bb[3]) / 2; KX = 111320 * math.cos(math.radians(LAT0)); KY = 110540
def xy(lon, lat): return ((lon - bb[0]) * KX, (lat - bb[1]) * KY)
def inb(lon, lat): return bb[0] <= lon <= bb[2] and bb[1] <= lat <= bb[3]
class Hd(osmium.SimpleHandler):
    def __init__(s): super().__init__(); s.ways = []; s.ent = []
    def node(s, n):
        if n.tags.get('railway') == 'subway_entrance' and n.location.valid() and inb(n.location.lon, n.location.lat): s.ent.append((n.location.lon, n.location.lat))
    def way(s, w):
        hw = w.tags.get('highway')
        if not hw or hw in NOWALK or w.tags.get('foot') == 'no' or w.tags.get('access') in ('private', 'no') and w.tags.get('foot') not in ('yes', 'designated'): return
        try: pts = [(nd.ref, nd.location.lon, nd.location.lat) for nd in w.nodes]
        except osmium.InvalidLocationError: return
        if not any(inb(p[1], p[2]) for p in pts): return
        s.ways.append(pts)
h = Hd(); h.apply_file(PBF, locations=True, idx='flex_mem'); print('길', len(h.ways), '출입구', len(h.ent), flush=True)
NI, NP, ADJ = {}, [], collections.defaultdict(list)
def nid(ref, lon, lat):
    if ref not in NI: NI[ref] = len(NP); NP.append(xy(lon, lat))
    return NI[ref]
for pts in h.ways:
    for a, b in zip(pts, pts[1:]):
        i, j = nid(*a), nid(*b); d = math.dist(NP[i], NP[j])
        if d <= 0: continue
        ADJ[i].append((j, d)); ADJ[j].append((i, d))
print('마디', len(NP), flush=True)
# 가까운 마디 찾기(격자)
CELL = 100; GRID = collections.defaultdict(list)
for i, p in enumerate(NP):
    if ADJ[i]: GRID[(int(p[0] // CELL), int(p[1] // CELL))].append(i)
def near(p, r=150):
    cx, cy = int(p[0] // CELL), int(p[1] // CELL); best = (r, None)
    for dx in (-2, -1, 0, 1, 2):
        for dy in (-2, -1, 0, 1, 2):
            for i in GRID.get((cx + dx, cy + dy), []):
                d = math.dist(p, NP[i])
                if d < best[0]: best = (d, i)
    return best[1]
# 도착 = 집계구 가운데(가구)
DEST = collections.defaultdict(float)
for g in GUS:
    for it in JG[g]['items']:
        hh = it[5] or 0
        if not hh: continue
        ring = it[2][0] if isinstance(it[2][0][0][0], (int, float)) else it[2][0][0]
        cx = sum(q[0] for q in ring) / len(ring); cy = sum(q[1] for q in ring) / len(ring); n = near(xy(cx, cy), 300)
        if n is not None: DEST[n] += hh
print('집계구 마디', len(DEST), '가구', round(sum(DEST.values())), flush=True)
# 출발
ORI = []
for g in GUS:
    for b in TR[g].get('bus', []):
        v = sum(b[5][H0:H1]); n = near(xy(b[2], b[3]), 80)
        if v > 0 and n is not None: ORI.append(('bus', n, v, b[1]))
    for s in TR[g].get('sub', []):
        v = sum(s[5][H0:H1]); p = xy(s[2], s[3]); E = [e for e in h.ent if math.dist(xy(*e), p) <= 300] or [(s[2], s[3])]
        for e in E:
            n = near(xy(*e), 80)
            if n is not None: ORI.append(('sub', n, v / len(E), s[0]))
print('출발', len(ORI), '저녁 하차 합', round(sum(o[2] for o in ORI)), flush=True)
FLOW = collections.defaultdict(float)
for k, (kind, src, vol, nm) in enumerate(ORI):
    lam = LAM[kind]; cut = lam * 2.5; dist = {src: 0.0}; prev = {}; pq = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18) or d > cut: continue
        for v2, w in ADJ[u]:
            nd = d + w
            if nd < dist.get(v2, 1e18) and nd <= cut: dist[v2] = nd; prev[v2] = u; heapq.heappush(pq, (nd, v2))
    T = [(z, DEST[z] * math.exp(-dist[z] / lam)) for z in DEST if z in dist]; S = sum(w for _, w in T)
    if not S: continue
    acc = collections.defaultdict(float)
    for z, w in T: acc[z] += vol * w / S
    order = sorted(acc, key=lambda z: -dist[z])   # 먼 곳부터 앞 마디로 흘려 보낸다(나무 위 누적)
    carry = collections.defaultdict(float)
    for z in sorted(dist, key=lambda z: -dist[z]):
        f = carry[z] + acc.get(z, 0)
        if f <= 0 or z == src: continue
        p = prev[z]; FLOW[(min(p, z), max(p, z))] += f; carry[p] += f
    if k % 50 == 0: print(k, '/', len(ORI), flush=True)
# 검증 — 편의점과 굵은 길
def inv(p): return (p[0] / KX + bb[0], p[1] / KY + bb[1])
E = sorted(FLOW.items(), key=lambda kv: -kv[1]); tot_len = sum(math.dist(NP[a], NP[b]) for (a, b), _ in E)
vals = sorted(f for _, f in E); q80 = vals[int(len(vals) * 0.8)] if vals else 0
SI = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8')); CV = {i for i, c in enumerate(SI['cls']) if c[5] == 'G20405'}
seg = [(NP[a], NP[b], f) for (a, b), f in E]; SG = collections.defaultdict(list)
for i, (p, q, f) in enumerate(seg):
    for t in (0, 0.5, 1): SG[(int((p[0] + (q[0] - p[0]) * t) // CELL), int((p[1] + (q[1] - p[1]) * t) // CELL))].append(i)
def segd(pt, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]; L = vx * vx + vy * vy; t = 0 if L == 0 else max(0, min(1, ((pt[0] - a[0]) * vx + (pt[1] - a[1]) * vy) / L)); return math.dist(pt, (a[0] + vx * t, a[1] + vy * t))
def nearseg(pt, r=30):
    cx, cy = int(pt[0] // CELL), int(pt[1] // CELL); best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in SG.get((cx + dx, cy + dy), []):
                d = segd(pt, seg[i][0], seg[i][1])
                if d <= r and (best is None or seg[i][2] > seg[best][2]): best = i
    return best
conv = hit = 0
for g in GUS:
    S2 = load(g, 'stores.json'); O, K = S2['o'], S2['k']
    for q in S2['pts']:
        if q[2] not in CV: continue
        lon, lat = O[0] + q[0] / K[0], O[1] + q[1] / K[1]; conv += 1; i = nearseg(xy(lon, lat))
        if i is not None and seg[i][2] >= q80: hit += 1
top_len = sum(math.dist(p, q) for p, q, f in seg if f >= q80)
check = {'conv': conv, 'hit': hit, 'share_conv': round(hit / conv, 3) if conv else None, 'share_len': round(top_len / tot_len, 3) if tot_len else None}
print('검증', check)
for g in GUS:
    # 하루 20명 미만 길은 빼고 · 같은 사람 수로 이어지는 조각은 한 줄로 잇는다(갈림 마디에서 끊음) · 좌표 = (경도−o0)·K0, (위도−o1)·K1 정수
    keepE = [((a2, b2), round(f)) for (a2, b2), f in E if f >= 20]; deg = collections.Counter()
    for (a2, b2), f in keepE: deg[a2] += 1; deg[b2] += 1
    byN = collections.defaultdict(list)
    for k2, ((a2, b2), f) in enumerate(keepE): byN[a2].append(k2); byN[b2].append(k2)
    used = set(); lines = []
    for k2, ((a2, b2), f) in enumerate(keepE):
        if k2 in used: continue
        used.add(k2); chain = [a2, b2]
        for end in (1, 0):
            while True:
                nd = chain[-1] if end else chain[0]
                if deg[nd] != 2: break
                nx = [j for j in byN[nd] if j not in used and keepE[j][1] == f]
                if not nx: break
                j = nx[0]; used.add(j); (c1, c2), _ = keepE[j]; nn = c2 if c1 == nd else c1
                if end: chain.append(nn)
                else: chain.insert(0, nn)
        lines.append((chain, f))
    O0 = [bb[0], bb[1]]; K0 = [88800, 111000]
    out = [[f] + [v for nd in chain for v in (round((inv(NP[nd])[0] - O0[0]) * K0[0]), round((inv(NP[nd])[1] - O0[1]) * K0[1]))] for chain, f in lines]
    doc = {'schema': 'tg-walk/1', 'gu': g, 'hours': [H0, H1], 'lam': LAM,
           'source': '추정 — 서울시 버스·지하철 시간대 하차(2026-06 하루 평균 · ' + str(H0) + '~' + str(H1) + '시) × 통계청 SGIS 집계구 가구(2023) × OpenStreetMap 걸을 수 있는 길·지하철 출입구(© OpenStreetMap contributors · ODbL)',
           'note': '관측이 아니라 모형이다: 정류장마다 저녁 하차 인원을 걸음 거리 안 집계구에 가구 × e^(−거리/λ)(λ 버스 400m · 지하철 800m — 보행권 관행을 쓴 가정)로 나눠 최단 길로 보냈다 · 지형(언덕·계단)은 아직 안 넣었다(높이 자료 대기) · 하차한 사람이 모두 이 구 주민은 아니다 · 하루 20명 미만 길은 뺐다',
           'check': check, 'o': [round(O0[0], 6), round(O0[1], 6)], 'k': K0, 'fields': '[저녁 예상 걷는 사람(명/일), x1, y1, x2, y2, …] — 경도 = o0 + x/k0 · 위도 = o1 + y/k1', 'lines': out}
    p2 = os.path.join(R, g, 'walk.json'); json.dump(doc, open(p2, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); IX.setdefault('layers', {})['walk'] = '🚶 예상 귀갓길(역·정류장 → 집 · 추정)'
    x = next((x for x in IX['gus'] if x['gu'] == g), None)
    if x is not None: x.setdefault('bytes', {})['walk'] = os.path.getsize(p2)
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(g, len(out), '줄', os.path.getsize(p2), 'B')
