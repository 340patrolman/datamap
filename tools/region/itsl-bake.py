# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.7.0 — ITS 실시간 소통 층(lspd)의 도로 선: 국가교통정보센터 전국 표준노드링크(MOCT_LINK.shp)에서 서울·경기 구간만
#   원본: https://www.its.go.kr/nodelink/nodelinkRef → [날짜]NODELINKDATA.zip (공개 · 로그인 없음 · 약 260MB) → 풀어 MOCT_LINK.* 를 아래 SRC 에
#   좌표계: ITRF2000 중부원점(TM 127° · 38° · x0 200000 · y0 600000 · GRS80) → WGS84
#   남기는 구간: ROAD_RANK 101 고속 · 102 도시고속 · 103 일반국도 · 104 특별·광역시도 · 105 국가지원지방도 · 106 지방도 · 107 시군도
#     (2026-10-04 실측 — 서초 상자 실시간 1,783구간 중 104 가 1,528 · 수원 상자 2,665 중 107 이 2,252 · 그 밖 등급은 오지 않았다)
#   py -3.12 -X utf8 tools/region/itsl-bake.py [MOCT_LINK.shp 경로]  →  data/r/<구>/itsl.json · r/index.json bytes.itsl
import json, os, sys, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl/MOCT_LINK.shp'
VER = sys.argv[2] if len(sys.argv) > 2 else '2026-09-14'   # 받은 NODELINKDATA 판 날짜
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}
BOX = (126.3, 36.85, 127.9, 38.35)

def enc(cs):   # 선 = [경도×1e5, 위도×1e5, 그다음은 앞 점과의 차이 …] 정수 — 지도가 풀어 쓴다
    o, px, py = [], 0, 0
    for k, (x, y) in enumerate(cs):
        ix, iy = round(x * 1e5), round(y * 1e5); o += [ix - px, iy - py] if k else [ix, iy]; px, py = ix, iy
    return o

def main():
    import shapefile, importlib.util
    from pyproj import Transformer
    from shapely.geometry import shape, Point, LineString
    from shapely.strtree import STRtree
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True)
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; st = STRtree(gs)
    def gu(lon, lat):
        q = Point(lon, lat)
        for i in st.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    r = shapefile.Reader(SRC, encoding='cp949')
    fi = {f[0]: k for k, f in enumerate(r.fields[1:])}
    G = collections.defaultdict(list); n = 0
    for sr in r.iterShapeRecords():
        rec = sr.record; rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        pts = sr.shape.points
        if len(pts) < 2: continue
        lon, lat = tr.transform(*pts[len(pts) // 2])
        if not (BOX[0] < lon < BOX[2] and BOX[1] < lat < BOX[3]): continue
        ll = [tr.transform(x, y) for x, y in pts]
        ls = LineString(ll).simplify(0.00003)
        g2 = gu(lon, lat)
        if not g2 or (rk == 7 and g2.startswith('11')): continue   # 서울 시군도는 실시간 소통이 오지 않는다(서초 실측 1,783 중 12)
        G[g2].append([rec[fi['LINK_ID']], rk, (rec[fi['ROAD_NAME']] or '').strip().replace('-', ''), int(rec[fi['MAX_SPD']] or 0), enc(ls.coords)])
        n += 1
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for g2, items in G.items():
        fn = os.path.join(ROOT, 'data', 'r', g2, 'itsl.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        json.dump({'schema': 'tg-itsl/1', 'gu': g2, 'source': '국가교통정보센터(ITS) 전국 표준노드링크 ' + VER + '판 — MOCT_LINK(ITRF2000 중부원점 → WGS84) · 등급 101~107',
                   'fields': '[링크 ID, 등급 1고속 2도시고속 3국도 4시도 5국지도 6지방도 7시군도, 도로 이름, 제한속도, 선 = 경도·위도×1e5 정수 첫 점 + 차이]', 'items': items},
                  open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[g2] = os.path.getsize(fn)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['itsl'] = gb[g2['gu']]
    R['layers']['itsl'] = 'ITS 표준노드링크 도로 선(실시간 소통용)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('links', n, 'gus', len(gb), 'bytes', sum(gb.values()), 'max', max(gb.values()))

if __name__ == '__main__':
    main()
