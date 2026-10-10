# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧭 고속·도시고속 뼈대(게임 세션 부탁 2026-10-11 · 신고 차량 예측이 서초 밖 올림픽대로·경부고속도로로 이어지게) → data/nav-express.json
#   꼴 = data/nav-seocho.json(tg-nav-graph/1)과 같게: nodes{노드 ID: [경도, 위도, 유형, 이름, 0, 닿는 링크 수]} · links[[링크 ID, 시작, 끝, 길이 m, 제한속도, 등급, 차로, 길 이름, 연결로, 선(×1e5 첫 점 + 차이)]]
#     노드 ID·링크 ID 는 원자료 그대로(서초 그래프와 이어 붙일 수 있다)
#   싣는 것 = 수도권 상자(126.3~127.9 · 36.85~38.0) 안의 등급 1 고속 · 2 도시고속 링크(연결로 포함) + **그 마디에서 낮은 등급 길로 나가는/들어오는 첫 링크**(나가는 곳을 가리려고)
#   선 = 약 50m 로 성기게 · 재료 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(C:/Users/knpth/regionwork/nl)
#   py -3.12 -X utf8 tools/signal/navexpress-bake.py
import json, os, sys, datetime, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}; BOX = (126.3, 36.85, 127.9, 38.0)
def main():
    import shapefile
    from pyproj import Transformer
    from shapely.geometry import LineString
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True); inv = Transformer.from_crs('EPSG:4326', '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', always_xy=True)
    x0, y0 = inv.transform(BOX[0], BOX[1]); x1, y1 = inv.transform(BOX[2], BOX[3])
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}
    recs = []; hw = set()
    for k, rec in enumerate(r.iterRecords()):   # ① 속성만 훑어 고속·도시고속 마디를 모은다
        rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        recs.append((k, rec[fi['LINK_ID']], rec[fi['F_NODE']], rec[fi['T_NODE']], rk, int(rec[fi['MAX_SPD']] or 0), round(float(rec[fi['LENGTH']] or 0)), int(rec[fi['LANES']] or 0), (rec[fi['ROAD_NAME']] or '').strip().replace('-', ''), 1 if rec[fi['CONNECT']] == '1' else 0))
        if rk <= 2: hw.add(rec[fi['F_NODE']]); hw.add(rec[fi['T_NODE']])
    keep = [x for x in recs if x[4] <= 2 or x[2] in hw or x[3] in hw]   # ② 고속·도시고속 + 그 마디에 닿는 낮은 등급 첫 링크
    LINK = []; used = set()
    for k, lid, f, t, rk, spd, ln, lanes, nm, con in keep:
        sh = r.shape(k); pts = sh.points
        mx, my = pts[len(pts) // 2]
        if not (x0 <= mx <= x1 and y0 <= my <= y1): continue
        q = list(LineString([tr.transform(x, y) for x, y in pts]).simplify(0.0005, preserve_topology=False).coords); enc = []; px = py = 0
        for a, b in q: ix, iy = round(a * 1e5), round(b * 1e5); enc += [ix - px, iy - py]; px, py = ix, iy
        LINK.append([lid, f, t, ln, spd, rk, lanes, nm, con, enc]); used.add(f); used.add(t)
    n = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(n.fields[1:])}; deg = collections.Counter()
    for L in LINK: deg[L[1]] += 1; deg[L[2]] += 1
    nodes = {}
    for sr in n.iterShapeRecords():
        rec = sr.record; nid = rec[fi['NODE_ID']]
        if nid not in used: continue
        lon, lat = tr.transform(*sr.shape.points[0]); nodes[nid] = [round(lon, 6), round(lat, 6), rec[fi['NODE_TYPE']], (rec[fi['NODE_NAME']] or '').strip(), 0, deg[nid]]
    doc = {'schema': 'tg-nav-graph/1', 'made': datetime.date.today().isoformat(), 'area': '수도권 상자(경도 126.3~127.9 · 위도 36.85~38.0) — 고속·도시고속과 그 나들목',
           'source': '국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(MOCT_NODE·MOCT_LINK)',
           'note': ['data/nav-seocho.json 과 같은 꼴이다(같은 노드·링크 ID) — 서초 그래프에 이어 붙여 쓴다. 신호·높이·회전 제한은 여기 없다',
                    '등급 1 고속·2 도시고속 링크(연결로 포함) 전부 + 그 마디에 닿는 낮은 등급 길의 **첫 링크만**(나가는 곳·들어오는 곳을 가리는 데 쓴다 — 그 뒤의 길은 없다)',
                    '선은 약 50m 로 성기게 했다 · 제한속도 0 은 원자료에 값이 없는 것 · 링크는 방향이 있다(시작 → 끝)',
                    '상자 밖으로 이어지는 링크가 없는 마디는 「자료 밖으로 나감」이다'],
           'fields': 'nodes{노드 ID: [경도, 위도, 유형(원자료 코드), 이름, 0, 닿는 링크 수]} · links[[링크 ID, 시작 노드, 끝 노드, 길이 m, 제한속도, 등급 1~7, 차로, 길 이름, 연결로 1, 선 = 경도·위도×1e5 첫 점 + 차이]]',
           'nodes': nodes, 'links': LINK, 'turns': []}
    p = os.path.join(ROOT, 'data', 'nav-express.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('노드', len(nodes), '· 링크', len(LINK), collections.Counter(L[5] for L in LINK), '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
