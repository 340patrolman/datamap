# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧭 서초 길찾기 바탕(소유자 2026-10-10 「신호값이 계속 모이면 서초구 전용 내비게이션도 만들겠다 · 준비하자 · 신호값 기반 최적효율 내비와 순찰차용」) → data/nav-seocho.json
#   길찾기에 필요한 뼈대를 한 파일로: 교차로(노드) · 방향 있는 길(링크 — 길이·제한속도·차로·등급) · 회전 제한 · 그리고 **교차로마다 어떤 신호 자료가 붙어 있는지**
#   재료 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(MOCT_NODE · MOCT_LINK · TURNINFO — C:/Users/knpth/regionwork/nl) + 이미 구운 신호 파일들
#     data/sigdir-seoul.json(서울 T-Data 방향별 초 · 닻) · data/signal-tod-seoul.json(경찰청 요일·시각별 계획) · data/sig-ksc-seocho.json(교통과 출력물 5곳) · data/sig-phmv-seoul.json(현시 → 이동류)
#   범위 = 서초구 경계에서 2km 바깥까지(구 밖으로 나갔다 들어오는 길이 더 빠를 수 있다)
#   이 파일은 **준비물**이다 — 길을 찾아 주는 기능은 아직 없다. 신호 자료가 붙은 교차로가 얼마나 되는지(coverage)가 「언제 만들 수 있나」의 잣대
#   py -3.12 -X utf8 tools/signal/navgraph-bake.py
import json, os, sys, math, datetime, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}
TURN = {'001': '비보호회전', '002': '버스만 회전', '003': '회전금지', '011': '유턴', '012': '피턴', '101': '좌회전금지', '102': '직진금지', '103': '우회전금지'}   # 표준노드링크 구축·운영 지침의 회전 유형 코드
DEMD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dem'); DEMT = {}
def elev(lon, lat):   # Copernicus DEM GLO-30(30m DSM — 건물·나무가 섞인다) → 5×5칸(약 150m) 평균으로 고르게(walkflow-bake.py 와 같은 법)
    import numpy as np
    from PIL import Image
    key = (int(math.floor(lat)), int(math.floor(lon)))
    if key not in DEMT:
        f = os.path.join(DEMD, 'Copernicus_DSM_COG_10_N%02d_00_E%03d_00_DEM.tif' % key)
        if not os.path.exists(f): DEMT[key] = None
        else:
            a = np.array(Image.open(f), dtype=np.float64); n = 5; c = np.cumsum(np.cumsum(np.pad(a, ((n // 2 + 1, n // 2), (n // 2 + 1, n // 2)), mode='edge'), 0), 1)
            DEMT[key] = ((c[n:, n:] - c[:-n, n:] - c[n:, :-n] + c[:-n, :-n]) / (n * n)).astype(np.float32)
    t = DEMT[key]
    if t is None: return None
    r = min(t.shape[0] - 1, int((key[0] + 1 - lat) * t.shape[0])); c = min(t.shape[1] - 1, int((lon - key[1]) * t.shape[1])); return float(t[r, c])
def main():
    import shapefile
    from pyproj import Transformer
    from shapely.geometry import Polygon, Point, LineString
    from shapely.ops import unary_union
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True); inv = Transformer.from_crs('EPSG:4326', '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', always_xy=True)
    sg = [x for x in json.load(open(os.path.join(ROOT, 'data', 'base', 'sgg.json'), encoding='utf-8'))['sgg'] if x['sido'] == '서울특별시' and x['name'] == '서초구'][0]
    gu = unary_union([Polygon([inv.transform(*p) for p in r]).buffer(0) for r in sg['rings'] if len(r) >= 4]); area = gu.buffer(2000); bx = area.bounds
    n = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(n.fields[1:])}; NODE = {}
    for sr in n.iterShapeRecords():
        x, y = sr.shape.points[0]
        if not (bx[0] <= x <= bx[2] and bx[1] <= y <= bx[3]) or not area.contains(Point(x, y)): continue
        lon, lat = tr.transform(x, y); rec = sr.record
        NODE[rec[fi['NODE_ID']]] = {'ll': [round(lon, 6), round(lat, 6)], 'tp': rec[fi['NODE_TYPE']], 'nm': (rec[fi['NODE_NAME']] or '').strip(), 'tp_turn': rec[fi['TURN_P']], 'in': 1 if gu.contains(Point(x, y)) else 0, 'xy': (x, y)}
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}; LINK = []; lid_ok = set()
    for sr in r.iterShapeRecords():
        rec = sr.record; f, t = rec[fi['F_NODE']], rec[fi['T_NODE']]
        if f not in NODE or t not in NODE: continue
        rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        full = LineString(sr.shape.points); up = dn = 0.0; z0 = None; nseg = max(1, int(full.length // 40))   # 40m 마다 높이를 읽어 오르막·내리막을 따로 더한다(전기차 회생제동·전비 셈에 쓸 것)
        for i2 in range(nseg + 1):
            pt = full.interpolate(i2 / nseg, normalized=True); z = elev(*tr.transform(pt.x, pt.y))
            if z is None: continue
            if z0 is not None: up += max(0.0, z - z0); dn += max(0.0, z0 - z)
            z0 = z
        q = list(LineString([tr.transform(x, y) for x, y in sr.shape.points]).simplify(0.00002).coords); enc = []; px = py = 0
        for a, b in q: ix, iy = round(a * 1e5), round(b * 1e5); enc += [ix - px, iy - py]; px, py = ix, iy
        LINK.append([rec[fi['LINK_ID']], f, t, round(float(rec[fi['LENGTH']] or 0)), int(rec[fi['MAX_SPD']] or 0), rk, int(rec[fi['LANES']] or 0), (rec[fi['ROAD_NAME']] or '').strip().replace('-', ''), 1 if rec[fi['CONNECT']] == '1' else 0, enc, round(up, 1), round(dn, 1), rec[fi['ROAD_TYPE']]]); lid_ok.add(rec[fi['LINK_ID']])
    t2 = shapefile.Reader(os.path.join(SRC, 'TURNINFO.dbf'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(t2.fields[1:])}; TURNS = []
    for rec in t2.iterRecords():
        if rec[fi['NODE_ID']] in NODE and rec[fi['ST_LINK']] in lid_ok and rec[fi['ED_LINK']] in lid_ok: TURNS.append([rec[fi['NODE_ID']], rec[fi['ST_LINK']], rec[fi['ED_LINK']], rec[fi['TURN_TYPE']]])
    # 신호 자료를 교차로에 붙인다 — 가장 가까운 「교차로」 노드(101) 60m 안
    deg = collections.Counter()
    for L in LINK: deg[L[1]] += 1; deg[L[2]] += 1
    X = [(k, v['xy']) for k, v in NODE.items() if deg[k] >= 3]
    def snap(lon, lat, lim=60):
        x, y = inv.transform(lon, lat); best = None
        for k, (a, b) in X:
            d = (a - x) ** 2 + (b - y) ** 2
            if best is None or d < best[0]: best = (d, k)
        return (best[1], round(math.sqrt(best[0]))) if best and best[0] <= lim * lim else (None, None)
    SIG = collections.defaultdict(dict); lost = collections.Counter()
    def load(fn):
        try: return json.load(open(os.path.join(ROOT, 'data', fn), encoding='utf-8'))
        except Exception as e: print(fn, '못 읽음', e); return {}
    sd = load('sigdir-seoul.json'); its = sd.get('its', {})
    for no, p in (sd.get('pts') or {}).items():
        if not (37.40 < p[0] < 37.56 and 126.94 < p[1] < 127.13): continue
        k, d = snap(p[1], p[0])
        if not k: lost['sigdir'] += 1; continue
        recs = its.get(no) or []; SIG[k]['sd'] = [no, p[2], len(recs), 1 if any('a' in x for x in recs) else 0, d]   # 서울 T-Data: [번호, 이름, 기록 수, 닻(이어 세기) 있음, 붙인 거리 m]
    for s in load('signal-tod-seoul.json').get('spots', []):
        if not (37.40 < s['lat'] < 37.56 and 126.94 < s['lon'] < 127.13): continue
        k, d = snap(s['lon'], s['lat'])
        if not k: lost['tod'] += 1; continue
        SIG[k]['tod'] = [s['no'], s['name'], len(s['plans']), d]   # 경찰청 계획: [번호, 이름, 계획 수, 거리]
    ks = load('sig-ksc-seocho.json')
    for it in ks.get('items') or []:
        if not it.get('lon'): lost['ksc 좌표 없음'] += 1; continue
        k, d = snap(it['lon'], it['lat'], 90)
        if k: SIG[k]['ksc'] = [it['no'], it.get('nm', ''), d]   # 교통과 출력물(요일·시각별 주기·현시·방향별 초)
        else: lost['ksc'] += 1
    pm = load('sig-phmv-seoul.json').get('spots', {})
    for k, v in SIG.items():
        no = (v.get('sd') or v.get('tod') or [None])[0]
        if no in pm: v['phmv'] = len(pm[no]['ph'])   # 현시 → 이동류를 읽은 현시 수
    nodes = {}
    for k, v in NODE.items():
        z = elev(v['ll'][0], v['ll'][1]); row = [v['ll'][0], v['ll'][1], v['tp'], v['nm'], v['in'], deg[k], None if z is None else round(z, 1)]
        if k in SIG: row.append(SIG[k])
        nodes[k] = row
    inx = [k for k, v in NODE.items() if v['in'] and v['tp'] == '101' and deg[k] >= 3]
    big = set()   # 큰길 교차로 = 등급 1~4 링크가 닿는 교차로
    for L in LINK:
        if L[5] <= 4: big.add(L[1]); big.add(L[2])
    inbig = [k for k in inx if k in big]
    def cov(ids): return {'교차로': len(ids), '신호 자료 있음': sum(1 for k in ids if k in SIG), '방향별 초(T-Data)': sum(1 for k in ids if 'sd' in SIG.get(k, {})), '지금 이어 셀 수 있음(닻)': sum(1 for k in ids if SIG.get(k, {}).get('sd', [0, 0, 0, 0])[3]), '요일·시각 계획(경찰청)': sum(1 for k in ids if 'tod' in SIG.get(k, {})), '교통과 출력물': sum(1 for k in ids if 'ksc' in SIG.get(k, {})), '현시 → 방향 읽음': sum(1 for k in ids if 'phmv' in SIG.get(k, {}))}
    doc = {'schema': 'tg-nav-graph/1', 'made': datetime.date.today().isoformat(), 'area': '서울특별시 서초구 + 경계 밖 2km',
           'dem': 'produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved.',
           'source': '국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(MOCT_NODE·MOCT_LINK·TURNINFO) · 신호 = data/sigdir-seoul.json · signal-tod-seoul.json · sig-ksc-seocho.json · sig-phmv-seoul.json',
           'note': ['**준비물이다 — 길을 찾아 주는 기능은 아직 없다.** 길찾기를 만들 때 이 한 파일을 읽으면 되도록 뼈대와 신호 자료의 붙음을 모아 둔 것',
                    '링크는 방향이 있다(F → T) · 제한속도 0 은 원자료에 값이 없는 것 · 회전 제한은 TURNINFO 에 적힌 것만(적히지 않은 금지가 있을 수 있다 — 현장 확인)',
                    '신호 자료는 좌표로 가장 가까운 교차로(링크 셋 이상이 만나는 노드) 60m 안에 붙였다 — 큰 교차로는 노드가 여럿이라 한 노드에만 붙는다(나머지 노드는 같은 교차로라도 비어 보인다). 교차로를 하나로 묶는 일이 다음 단계',
                    'coverage = 서초구 안 교차로 가운데 신호 자료가 붙은 수 — 분모에는 신호 없는 교차로도 들어 있다(서울은 시군도 등급을 싣지 않아 대부분 등급 4 라 큰길만 따로 가르지 못한다). 붙은 「개수」를 본다',
                    '높이 = Copernicus DEM GLO-30(30m · 건물·나무가 섞인 표면 높이)을 150m 평균으로 고른 값 — **땅 높이의 근사**다. 고가·지하차도·교량·터널(도로 유형 001~004)은 길이 땅과 다른 높이로 가므로 그 링크의 오르막·내리막은 믿지 않는다. 짧은 링크의 1~2m 차이는 잡음이다',
                    '차로 수는 링크 전체의 값이다 — 교차로 앞 차로별 진행 방향(좌회전·직진·우회전 전용)은 이 자료에 없다. 「몇 차로로 가라」를 안내하려면 따로 구해야 한다',
                    '길찾기에 쓸 때의 규칙(T-Book 신호 앱과 같다): 제한속도를 넘는 값은 안 낸다 · 밤(22시~)에는 연동속도를 안 보인다 · 계획값과 실제가 다를 수 있다고 밝힌다 · 「몇 초 뒤 바뀜」은 닻이 맞는 교차로에서만'],
           'turn_types': TURN,
           'fields': 'nodes{노드 ID: [경도, 위도, 유형(101 교차로·102 도로 시작/끝·103 속성변화점·104 도로시설·106 IC/JC 등 — 원자료 코드), 이름, 서초구 안 1/밖 0, 닿는 링크 수, 높이 m, 신호{sd[T-Data 번호, 이름, 기록 수, 닻 있음, 거리 m], tod[경찰청 번호, 이름, 계획 수, 거리], ksc[번호, 이름, 거리], phmv 방향 읽은 현시 수}(있을 때만)]} · links[[링크 ID, 시작 노드, 끝 노드, 길이 m, 제한속도, 등급 1~7, 차로, 길 이름, 연결로 1, 선 = 경도·위도×1e5 첫 점 + 차이, 오르막 합 m, 내리막 합 m(F → T 방향 · 40m 마다 읽음), 도로 유형(000 일반 · 001 고가 · 002 지하차도 · 003 교량 · 004 터널 — 원자료 코드)]] · turns[[노드, 들어오는 링크, 나가는 링크, 회전 유형 코드]]',
           'coverage': {'서초구 안 교차로(링크 셋 이상이 만나는 노드)': cov(inx), '참고': '서초경찰서 관내 신호제어기는 교통과 대장으로 178대(2026-09 · 방배서 관내 제외) — 위 분모는 신호 없는 교차로까지 든 수라 비율로 읽지 않는다', '서초 밖이라 안 붙인 신호 자료(범위 상자 안)': dict(lost)},
           'nodes': nodes, 'links': LINK, 'turns': TURNS}
    p = os.path.join(ROOT, 'data', 'nav-seocho.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('노드', len(nodes), '· 링크', len(LINK), '· 회전 제한', len(TURNS), collections.Counter(TURN.get(t[3], t[3]) for t in TURNS), '· 바이트', os.path.getsize(p))
    for k, v in doc['coverage'].items(): print(' ', k, v)
    print('  닻 있는 교차로', len([1 for v in nodes.values() if len(v) > 7 and v[4] and 'sd' in v[7] and v[7]['sd'][3]]))
if __name__ == '__main__': main()
