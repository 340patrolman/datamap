# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.81.0 — 🚶 예상 귀갓길(역·정류장 → 집) · 소유자 2026-10-07 「주민의 동선은 지하철 출입구·버스정류장에서 집으로 걸어가는 길 · 골목상권은 그렇게 된다 · 그런 곳에 편의점·가게가 있다」 · 「서울 경기도까지 가능한 범위에서 다」
#   모형(추정 · 관측이 아니다):
#     출발 = 저녁 귀가 시간(17~23시) 하차 인원 — transit.json(서울 = 버스 정류장 + 지하철 역 · 경기 = 지하철 역만 — 경기 버스 하차 자료가 없다)
#            지하철은 OSM 출입구(railway=subway_entrance) 300m 안 것들에 똑같이 나눈다(없으면 역 자리)
#     도착 = 집계구(통계청 SGIS · jgg.json) 가운데 · 가구 수만큼 끌어당김 — 이 구 + 상자에 걸친 이웃 구 집계구
#     나눔 = 정류장마다 하차 인원을 걸음 거리 d 안 집계구에 가구 × e^(−d/λ) 비율로(λ 버스 400m · 지하철 800m · 끝 거리 2.5λ — 정류장 400m·역 800m 보행권 관행을 쓴 가정)
#     길 = OSM 걸을 수 있는 길(© OpenStreetMap contributors · ODbL · kr.pbf 2026-10-03) 최단 거리 · 고속·자동차 전용(motorway·trunk)과 foot=no 는 뺀다
#     ⚠ 지형(언덕·계단 회피)은 아직 없다 — 높이 자료(DEM)가 오면 걸음 비용에 경사를 넣는다(Tobler 걸음 함수)
#   검증(가설 · 관계장부식): 편의점(소상공인 상가업소 G20405)이 예상 동선 굵은 길 가까이에 몰리는가 — 길 길이 몫과 견줌
#   수도권 길망은 처음 한 번 kr.pbf 에서 뽑아 07_API키/out/walknet/capital.npz 에 둔다(다시 쓸 때 빠름)
#   → data/r/<구>/walk.json  py -3.12 -X utf8 tools/region/walkflow-bake.py [구 …]   (구를 안 주면 서울·경기 transit 있는 곳 전부)
import json, os, sys, math, heapq, collections, glob, time
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r'); PBF = 'C:/Users/knpth/osmwork/kr.pbf'
CACHE = os.path.join(KB, '07_API키', 'out', 'walknet', 'capital.npz')
CAP = (126.30, 36.85, 127.90, 38.32)   # 서울·경기·인천 상자
H0, H1 = 17, 23
LAM = {'bus': 400, 'sub': 800}
NOWALK = {'motorway', 'motorway_link', 'trunk', 'trunk_link', 'construction', 'proposed', 'raceway', 'bus_guideway'}
def build_cache():
    import osmium
    t0 = time.time(); refs, lons, lats, off, ent = [], [], [], [0], []
    fp = osmium.FileProcessor(PBF).with_locations().with_filter(osmium.filter.KeyFilter('highway', 'railway'))
    for o in fp:
        if o.is_node():
            if o.tags.get('railway') == 'subway_entrance' and o.location.valid():
                lo, la = o.location.lon, o.location.lat
                if CAP[0] <= lo <= CAP[2] and CAP[1] <= la <= CAP[3]: ent.append((lo, la))
            continue
        if not o.is_way(): continue
        hw = o.tags.get('highway')
        if not hw or hw in NOWALK or o.tags.get('foot') == 'no' or (o.tags.get('access') in ('private', 'no') and o.tags.get('foot') not in ('yes', 'designated')): continue
        try: pts = [(n.ref, n.location.lon, n.location.lat) for n in o.nodes]
        except Exception: continue
        if not any(CAP[0] <= p[1] <= CAP[2] and CAP[1] <= p[2] <= CAP[3] for p in pts): continue
        for p in pts: refs.append(p[0]); lons.append(p[1]); lats.append(p[2])
        off.append(len(refs))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    np.savez_compressed(CACHE, refs=np.array(refs, dtype=np.int64), lon=np.array(lons, dtype=np.float64), lat=np.array(lats, dtype=np.float64), off=np.array(off, dtype=np.int64), ent=np.array(ent, dtype=np.float64).reshape(-1, 2))
    print('길망 저장', len(off) - 1, '길', len(refs), '점', len(ent), '출입구', round(time.time() - t0), 's', flush=True)
if not os.path.exists(CACHE): build_cache()
Z = np.load(CACHE); REFS, LON, LAT, OFF, ENT = Z['refs'], Z['lon'], Z['lat'], Z['off'], Z['ent']
NW = len(OFF) - 1
# 길마다 상자 → 0.02° 칸 색인
WB = np.zeros((NW, 4))
for w in range(NW):
    a, b = OFF[w], OFF[w + 1]; WB[w] = (LON[a:b].min(), LAT[a:b].min(), LON[a:b].max(), LAT[a:b].max())
WG = collections.defaultdict(list); C = 0.02
for w in range(NW):
    for gx in range(int(WB[w, 0] / C), int(WB[w, 2] / C) + 1):
        for gy in range(int(WB[w, 1] / C), int(WB[w, 3] / C) + 1): WG[(gx, gy)].append(w)
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); GBOX = {g['gu']: g.get('box') for g in IX['gus']}
SI = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8')); CV = {i for i, c in enumerate(SI['cls']) if c[5] == 'G20405'}
def load(gu, f):
    p = os.path.join(R, gu, f); return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
def ring0(it):
    r = it[2]
    while isinstance(r[0][0], list): r = r[0]
    return r
def run(gu):
    t0 = time.time(); TR = load(gu, 'transit.json'); JG = load(gu, 'jgg.json')
    if not TR or not JG or not (TR.get('bus') or TR.get('sub')): return None
    bb = [180, 90, -180, -90]
    for it in JG['items']:
        for q in ring0(it): bb = [min(bb[0], q[0]), min(bb[1], q[1]), max(bb[2], q[0]), max(bb[3], q[1])]
    PAD = 0.02; bb = [bb[0] - PAD, bb[1] - PAD, bb[2] + PAD, bb[3] + PAD]
    LAT0 = (bb[1] + bb[3]) / 2; KX = 111320 * math.cos(math.radians(LAT0)); KY = 110540
    xy = lambda lon, lat: ((lon - bb[0]) * KX, (lat - bb[1]) * KY)
    inv = lambda p: (p[0] / KX + bb[0], p[1] / KY + bb[1])
    ws = set()
    for gx in range(int(bb[0] / C), int(bb[2] / C) + 1):
        for gy in range(int(bb[1] / C), int(bb[3] / C) + 1): ws.update(WG.get((gx, gy), []))
    NI, NP, ADJ = {}, [], collections.defaultdict(list)
    def nid(k):
        r = int(REFS[k])
        if r not in NI: NI[r] = len(NP); NP.append(xy(LON[k], LAT[k]))
        return NI[r]
    for w in ws:
        if WB[w, 2] < bb[0] or WB[w, 0] > bb[2] or WB[w, 3] < bb[1] or WB[w, 1] > bb[3]: continue
        a, b = OFF[w], OFF[w + 1]; prev = None
        for k in range(a, b):
            i = nid(k)
            if prev is not None and prev != i:
                d = math.dist(NP[prev], NP[i]); ADJ[prev].append((i, d)); ADJ[i].append((prev, d))
            prev = i
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
    DEST = collections.defaultdict(float)
    for g2, x in GBOX.items():   # 이 구 + 상자에 걸친 이웃 구 집계구
        if not x or x[2] < bb[0] or x[0] > bb[2] or x[3] < bb[1] or x[1] > bb[3]: continue
        J2 = JG if g2 == gu else load(g2, 'jgg.json')
        if not J2: continue
        for it in J2['items']:
            hh = it[5] or 0
            if not hh: continue
            rg = ring0(it); cx = sum(q[0] for q in rg) / len(rg); cy = sum(q[1] for q in rg) / len(rg)
            if not (bb[0] <= cx <= bb[2] and bb[1] <= cy <= bb[3]): continue
            n = near(xy(cx, cy), 300)
            if n is not None: DEST[n] += hh
    ORI = []
    for b in TR.get('bus', []):
        v = sum(b[5][H0:H1]); n = near(xy(b[2], b[3]), 80)
        if v > 0 and n is not None: ORI.append(('bus', n, v))
    for s in TR.get('sub', []):
        v = sum(s[5][H0:H1]); p = xy(s[2], s[3]); E = [e for e in ENT if bb[0] <= e[0] <= bb[2] and bb[1] <= e[1] <= bb[3] and math.dist(xy(e[0], e[1]), p) <= 300] or [(s[2], s[3])]
        for e in E:
            n = near(xy(e[0], e[1]), 80)
            if n is not None and v > 0: ORI.append(('sub', n, v / len(E)))
    FLOW = collections.defaultdict(float)
    for kind, src, vol in ORI:
        lam = LAM[kind]; cut = lam * 2.5; dist = {src: 0.0}; prev = {}; pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, 1e18): continue
            for v2, w in ADJ[u]:
                nd = d + w
                if nd <= cut and nd < dist.get(v2, 1e18): dist[v2] = nd; prev[v2] = u; heapq.heappush(pq, (nd, v2))
        T = [(z, DEST[z] * math.exp(-dist[z] / lam)) for z in DEST if z in dist]; S = sum(w for _, w in T)
        if not S: continue
        acc = {z: vol * w / S for z, w in T}; carry = collections.defaultdict(float)
        for z in sorted(dist, key=lambda z: -dist[z]):
            f = carry[z] + acc.get(z, 0)
            if f <= 0 or z == src: continue
            p2 = prev[z]; FLOW[(min(p2, z), max(p2, z))] += f; carry[p2] += f
    if not FLOW: return None
    E = sorted(FLOW.items(), key=lambda kv: -kv[1]); tot_len = sum(math.dist(NP[a], NP[b]) for (a, b), _ in E)
    vals = sorted(f for _, f in E); q80 = vals[int(len(vals) * 0.8)]
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
                    if segd(pt, seg[i][0], seg[i][1]) <= r and (best is None or seg[i][2] > seg[best][2]): best = i
        return best
    conv = hit = 0; S2 = load(gu, 'stores.json')
    if S2:
        O, K = S2['o'], S2['k']
        for q in S2['pts']:
            if q[2] not in CV: continue
            conv += 1; i = nearseg(xy(O[0] + q[0] / K[0], O[1] + q[1] / K[1]))
            if i is not None and seg[i][2] >= q80: hit += 1
    top_len = sum(math.dist(p, q) for p, q, f in seg if f >= q80)
    check = {'conv': conv, 'hit': hit, 'share_conv': round(hit / conv, 3) if conv else None, 'share_len': round(top_len / tot_len, 3) if tot_len else None}
    keepE = [((a, b), round(f)) for (a, b), f in E if f >= 20]; deg = collections.Counter(); byN = collections.defaultdict(list)
    for k2, ((a, b), f) in enumerate(keepE): deg[a] += 1; deg[b] += 1; byN[a].append(k2); byN[b].append(k2)
    used = set(); lines = []
    for k2, ((a, b), f) in enumerate(keepE):
        if k2 in used: continue
        used.add(k2); chain = [a, b]
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
    O0 = [round(bb[0], 6), round(bb[1], 6)]; K0 = [88800, 111000]
    out = [[f] + [v for nd in chain for v in (round((inv(NP[nd])[0] - O0[0]) * K0[0]), round((inv(NP[nd])[1] - O0[1]) * K0[1]))] for chain, f in lines]
    nb = sum(1 for o in ORI if o[0] == 'bus'); ns = sum(1 for o in ORI if o[0] == 'sub')
    doc = {'schema': 'tg-walk/1', 'gu': gu, 'hours': [H0, H1], 'lam': LAM, 'origins': {'bus': nb, 'sub': ns},
           'source': '추정 — ' + ('서울시 버스·지하철' if gu[:2] == '11' else '수도권 지하철(서울시 교통카드 자료에 든 역 · 버스 없음)') + ' 시간대 하차(2026-06 하루 평균 · ' + str(H0) + '~' + str(H1) + '시) × 통계청 SGIS 집계구 가구(2023) × OpenStreetMap 걸을 수 있는 길·지하철 출입구(© OpenStreetMap contributors · ODbL)',
           'note': '관측이 아니라 모형이다: 정류장마다 저녁 하차 인원을 걸음 거리 안 집계구에 가구 × e^(−거리/λ)(λ 버스 400m · 지하철 800m — 보행권 관행을 쓴 가정)로 나눠 최단 길로 보냈다 · 지형(언덕·계단)은 아직 안 넣었다(높이 자료 대기) · 하차한 사람이 모두 주민은 아니다 · 하루 20명 미만 길은 뺐다' + ('' if gu[:2] == '11' else ' · 경기는 버스 하차 자료가 없어 지하철에서 걷는 길만 — 버스로 오는 사람 길은 빠졌다'),
           'check': check, 'o': O0, 'k': K0, 'fields': '[저녁 예상 걷는 사람(명/일), x1, y1, x2, y2, …] — 경도 = o0 + x/k0 · 위도 = o1 + y/k1', 'lines': out}
    p2 = os.path.join(R, gu, 'walk.json'); json.dump(doc, open(p2, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(gu, '출발', len(ORI), '줄', len(out), os.path.getsize(p2), 'B', check, round(time.time() - t0), 's', flush=True)
    return os.path.getsize(p2), check
GUS = sys.argv[1:] or [os.path.basename(d) for d in sorted(glob.glob(os.path.join(R, '11*'))) + sorted(glob.glob(os.path.join(R, '41*'))) if os.path.isdir(d)]
tot = collections.Counter()
for gu in GUS:
    r = run(gu)
    if not r: print(gu, '건너뜀(하차·집계구 없음)', flush=True); continue
    x = next((x for x in IX['gus'] if x['gu'] == gu), None)
    if x is not None: x.setdefault('bytes', {})['walk'] = r[0]
    c = r[1]; tot['conv'] += c['conv']; tot['hit'] += c['hit']
    IX.setdefault('layers', {})['walk'] = '🚶 예상 귀갓길(역·정류장 → 집 · 추정)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('전체 편의점', dict(tot))
