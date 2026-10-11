# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧭 서초에서 이어지는 큰길 뼈대(소유자 2026-10-11 「범위는 합리적으로 정하자 … 대로 고속도로 등으로 연결되어 있으면 행정적으로 분리되어 있어도 시간적으로 비슷하거나 같은 권역이 되지」) → data/nav-arterial.json
#   범위를 구 경계가 아니라 **길로 이어진 시간 권역**으로: 서초구청 둘레에서 제한속도로 LIM 분 안에 닿는 마디에서 시작하는 큰길을 모은다
#     큰길 = 등급 1 고속 · 2 도시고속 · 3 일반국도 + 등급 4(특별·광역시도) 가운데 차로 3 이상이거나 이름이 「…대로」로 끝나는 길 + 그 연결로
#   꼴 = data/nav-seocho.json(tg-nav-graph/1)과 같게(같은 노드·링크 ID): nodes{노드 ID: [경도, 위도, 유형, 이름, 0, 닿는 링크 수, null, 신호{no, sd·tod}]} · links[[링크 ID, 시작, 끝, 길이, 제한속도, 등급, 차로, 길 이름, 연결로, 선]]
#   신호 = data/sigdir-seoul.json(서울 T-Data 자리) · data/signal-tod-seoul.json(경찰청 계획) 의 자리에서 60m 안 교차로 마디(유형 101)에 번호를 붙인다(자료가 있는 곳만 — 없는 교차로는 신호 없음으로 보인다)
#   재료 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(C:/Users/knpth/regionwork/nl) · 시간 셈은 tools/region/reach-bake.py 의 캐시
#   py -3.12 -X utf8 tools/signal/navarterial-bake.py [분 · 기본 15]
import json, os, sys, math, heapq, pickle, datetime, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = 'C:/Users/knpth/regionwork/nl'; LIM = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}; C0 = (127.0327, 37.4836)   # 서초구청(data/gov-offices.json)
def main():
    import shapefile
    from pyproj import Transformer
    from shapely.geometry import LineString
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True)
    d = pickle.load(open(os.path.join(SRC, 'reach_cache.pkl'), 'rb')); NODE, CL = d['NODE'], d['LINK']; FWD = collections.defaultdict(list); REV = collections.defaultdict(list); big = set()
    for lid, f, t, rk, spd, ln, nm, geo in CL:
        w = ln / (spd / 3.6) / 60.0; FWD[f].append((t, w)); REV[t].append((f, w))
        if rk <= 4: big.add(f); big.add(t)
    src = min(big, key=lambda k: (NODE[k][0] - C0[0]) ** 2 + (NODE[k][1] - C0[1]) ** 2)
    def dij(G):
        D = {src: 0.0}; h = [(0.0, src)]
        while h:
            x, u = heapq.heappop(h)
            if x > D.get(u, 1e18) or x > LIM: continue
            for v, w in G.get(u, ()):
                if x + w < D.get(v, 1e18): D[v] = x + w; heapq.heappush(h, (x + w, v))
        return D
    DF = dij(FWD); DR = dij(REV); near = set(k for k, v in DF.items() if v <= LIM) | set(k for k, v in DR.items() if v <= LIM)   # 서초에서 가거나 서초로 오는 데 LIM 분 안
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}; keep = []
    for k, rec in enumerate(r.iterRecords()):
        rk = RANK.get(rec[fi['ROAD_RANK']]); f, t = rec[fi['F_NODE']], rec[fi['T_NODE']]
        if not rk or rk > 4 or (f not in near and t not in near): continue
        lanes = int(rec[fi['LANES']] or 0); nm = (rec[fi['ROAD_NAME']] or '').strip().replace('-', ''); con = 1 if rec[fi['CONNECT']] == '1' else 0
        if rk == 4 and not (lanes >= 3 or nm.endswith('대로') or con): continue
        keep.append((k, rec[fi['LINK_ID']], f, t, round(float(rec[fi['LENGTH']] or 0)), int(rec[fi['MAX_SPD']] or 0), rk, lanes, nm, con))
    LINK = []; used = set()
    for k, lid, f, t, ln, spd, rk, lanes, nm, con in keep:
        q = list(LineString([tr.transform(x, y) for x, y in r.shape(k).points]).simplify(0.0003, preserve_topology=False).coords); enc = []; px = py = 0
        for a, b in q: ix, iy = round(a * 1e5), round(b * 1e5); enc += [ix - px, iy - py]; px, py = ix, iy
        LINK.append([lid, f, t, ln, spd, rk, lanes, nm, con, enc]); used.add(f); used.add(t)
    deg = collections.Counter()
    for L in LINK: deg[L[1]] += 1; deg[L[2]] += 1
    n = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.dbf'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(n.fields[1:])}; nodes = {}
    for rec in n.iterRecords():
        nid = rec[fi['NODE_ID']]
        if nid in used: nodes[nid] = [NODE[nid][0], NODE[nid][1], rec[fi['NODE_TYPE']], (rec[fi['NODE_NAME']] or '').strip(), 0, deg[nid], None]
    # 신호 붙이기 — 55m 안 갈림길 마디(링크 셋 이상) 전부에 같은 번호(한 마디에 둘이 닿으면 가까운 쪽)
    grid = collections.defaultdict(list)
    for k, v in nodes.items():
        if v[2] == '101': grid[(int(v[0] * 500), int(v[1] * 500))].append(k)   # 유형 101 = 교차로(큰길만 남긴 그래프라 닿는 링크 수로는 못 가린다 — 곁길이 빠져 대부분 2)
    def m(a, b): return math.hypot((a[0] - b[0]) * 88400.0, (a[1] - b[1]) * 111000.0)
    SIG = {}
    def put(lon, lat, kind, row):
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in grid.get((int(lon * 500) + dx, int(lat * 500) + dy), ()):
                    dd = m((lon, lat), nodes[k][:2])
                    if dd <= 60 and (k not in SIG or kind not in SIG[k] or dd < SIG[k][kind][-1]): SIG.setdefault(k, {})[kind] = row + [round(dd)]
    sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); its = sd.get('its', {})
    for no, p in (sd.get('pts') or {}).items():
        recs = its.get(no) or []; put(p[1], p[0], 'sd', [no, p[2], len(recs), 1 if any('a' in x for x in recs) else 0])
    for s in json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']: put(s['lon'], s['lat'], 'tod', [s['no'], s['name'], len(s['plans'])])
    for k, v in SIG.items(): v['no'] = (v.get('sd') or v.get('tod'))[0]; nodes[k].append(v)
    doc = {'schema': 'tg-nav-graph/1', 'made': datetime.date.today().isoformat(), 'area': '서초구청 둘레에서 제한속도로 %d분 안에 닿는(가거나 오는) 마디에서 이어지는 큰길' % LIM,
           'source': '국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판 · 신호 자리 = data/sigdir-seoul.json · data/signal-tod-seoul.json',
           'note': ['data/nav-seocho.json 과 같은 꼴(같은 노드·링크 ID)이다 — 서초 그래프·data/nav-express.json 에 이어 붙여 쓴다(겹치는 링크는 ID 로 한 번만)',
                    '범위는 구 경계가 아니라 길로 이어진 시간 권역이다(소유자 2026-10-11) — 「제한속도로 막힘없이」 잰 %d분이라 실제 시간 권역보다 넓다' % LIM,
                    '큰길만: 등급 1 고속 · 2 도시고속 · 3 일반국도 + 등급 4 가운데 차로 3 이상이거나 이름이 「…대로」인 길 + 연결로 — 그 밖의 길(골목·2차로 길)은 없다',
                    '신호는 서울 T-Data·경찰청 자료가 있는 자리만 붙였다(경기도 쪽은 신호 자료가 없어 붙지 않는다 — 「신호 없음」이 아니라 「신호 자료 없음」)',
                    '높이·회전 제한은 없다(높이 칸 null · turns 빈 목록) · 선은 약 30m 로 성기게'],
           'fields': 'nodes{노드 ID: [경도, 위도, 유형, 이름, 0, 닿는 링크 수, null, 신호{no 신호 교차로 번호, sd[T-Data 번호, 이름, 기록 수, 닻 있음, 거리 m], tod[경찰청 번호, 이름, 계획 수, 거리]}(있을 때만)]} · links[[링크 ID, 시작, 끝, 길이 m, 제한속도, 등급, 차로, 길 이름, 연결로 1, 선 = 경도·위도×1e5 첫 점 + 차이]]',
           'nodes': nodes, 'links': LINK, 'turns': []}
    p = os.path.join(ROOT, 'data', 'nav-arterial.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    xs = [v[0] for v in nodes.values()]; ys = [v[1] for v in nodes.values()]
    print('%d분 권역 · 노드' % LIM, len(nodes), '· 링크', len(LINK), collections.Counter(L[5] for L in LINK), '· 신호 붙은 교차로', len(set(v['no'] for v in SIG.values())), '· 상자 %.3f~%.3f · %.3f~%.3f' % (min(xs), max(xs), min(ys), max(ys)), '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
