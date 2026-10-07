# -*- coding: utf-8 -*-
# ⚠ v2.88.0 다시 구우면 tools/region/jname-bake.py → tools/region/road-audit.py 순으로 이어서 돌린다(교차로·도로 이름 하나로)
# 데이터 압축지도 v1.8.0 — 🏷 교차로 이름·도로 이름(서울·경기 전부) : 국가교통정보센터 전국 표준노드링크(MOCT_NODE · MOCT_LINK)
#   원본: https://www.its.go.kr/nodelink/nodelinkRef → [날짜]NODELINKDATA.zip(공개 · 로그인 없음) → 풀어 둔 폴더를 SRC 로
#   교차로 = MOCT_NODE 의 NODE_TYPE 101(교차로) · 104(교량·터널·지하차도 등 도로시설 시·종점) · 106(IC·연결로 접속부)
#     이름이 지번 주소(「서초동 1454-14」)·「속성변화점」·「최소노드배치점」이면 뺀다(이름 없는 자리에 주소를 넣어 둔 것)
#     같은 이름이 150m 안에 여럿이면(한 교차로의 여러 노드) 한 점으로 모은다 · 그 노드에 닿는 링크의 도로 이름을 「만나는 도로」로 붙인다
#   도로 이름 = MOCT_LINK 의 ROAD_NAME(등급 101~107) — 같은 이름은 350m(고속·도시고속 800m)마다 하나씩 글자 자리(가운데·기울기)
#   좌표: ITRF2000 중부원점(TM 127° · 38° · 200000/600000 · GRS80) → WGS84
#   py -3.12 -X utf8 tools/region/jcnm-bake.py [풀어 둔 폴더] [판 날짜]  →  data/r/<구>/jcnm.json · r/index.json bytes.jcnm
import json, os, sys, re, math, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
VER = sys.argv[2] if len(sys.argv) > 2 else '2026-09-14'
BOX = (124.5, 33.0, 131.95, 38.7)   # v2.8.0 전국(종전 수도권 126.3~127.9 · 36.85~38.35)
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}
NT = {'101': 1, '104': 4, '106': 6}
BAD = re.compile(r'(\d+(-\d+)?\s*$)|속성변화점|최소노드배치점|^\s*$')

def main():
    import shapefile, importlib.util
    from pyproj import Transformer
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True)
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; st = STRtree(gs)
    def gu(lon, lat):
        q = Point(lon, lat)
        for i in st.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    # 1) 링크 — 노드에 닿는 도로 · 도로 이름 글자 자리 후보
    NR = collections.defaultdict(dict)          # 노드 → {도로 이름: 등급}
    RC = collections.defaultdict(list)          # (구, 이름) → [(길이, x, y, 각도, 등급)]   x,y = TM m
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}
    for sr in r.iterShapeRecords():
        rec = sr.record; rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        nm = (rec[fi['ROAD_NAME']] or '').strip()
        if not nm or nm == '-': continue
        pts = sr.shape.points; n = len(pts)
        if n < 2: continue
        mx, my = pts[n // 2] if n > 2 else ((pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2)
        lon, lat = tr.transform(mx, my)
        if not (BOX[0] < lon < BOX[2] and BOX[1] < lat < BOX[3]): continue
        for nd in (rec[fi['F_NODE']], rec[fi['T_NODE']]):
            o = NR[nd]
            if nm not in o or o[nm] > rk: o[nm] = rk
        ln = float(rec[fi['LENGTH']] or 0)
        if ln < 60: continue
        a, b = pts[max(0, n // 2 - 1)], pts[min(n - 1, n // 2 + (0 if n > 2 else 1))]
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        g2 = gu(lon, lat)
        if g2: RC[(g2, nm)].append((ln, mx, my, ang, rk))
    # 2) 도로 이름 글자 자리 솎기
    RD = collections.defaultdict(list)
    for (g2, nm), cs in RC.items():
        cs.sort(key=lambda c: -c[0]); kept = []; gap = 800 if min(c[4] for c in cs) <= 2 else 350
        for c in cs:
            if all((c[1] - k[1]) ** 2 + (c[2] - k[2]) ** 2 >= gap * gap for k in kept): kept.append(c)
        for c in kept:
            lon, lat = tr.transform(c[1], c[2]); a = c[3]
            if a > 90: a -= 180
            if a < -90: a += 180
            RD[g2].append([nm, round(lon, 5), round(lat, 5), round(a), c[4]])
    # 3) 노드 — 교차로·시설·IC 이름
    raw = collections.defaultdict(list)          # (구, 이름) → [(x, y, 종류, 노드 ID)]
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}
    for sr in r.iterShapeRecords():
        rec = sr.record; t = NT.get(rec[fi['NODE_TYPE']])
        if not t: continue
        nm = (rec[fi['NODE_NAME']] or '').strip()
        if BAD.search(nm): continue
        x, y = sr.shape.points[0]; lon, lat = tr.transform(x, y)
        if not (BOX[0] < lon < BOX[2] and BOX[1] < lat < BOX[3]): continue
        g2 = gu(lon, lat)
        if g2: raw[(g2, nm)].append((x, y, t, rec[fi['NODE_ID']]))
    JC = collections.defaultdict(list); nn = 0
    for (g2, nm), ps in raw.items():
        cl = []
        for p in ps:
            for c in cl:
                if (p[0] - c[0][0]) ** 2 + (p[1] - c[0][1]) ** 2 <= 150 * 150: c.append(p); break
            else: cl.append([p])
        for c in cl:
            x = sum(p[0] for p in c) / len(c); y = sum(p[1] for p in c) / len(c); lon, lat = tr.transform(x, y)
            rd = {}
            for p in c:
                for k, v in NR.get(p[3], {}).items():
                    if k not in rd or rd[k] > v: rd[k] = v
            rs = sorted(rd.items(), key=lambda kv: (kv[1], kv[0]))
            JC[g2].append([nm, round(lon, 5), round(lat, 5), min(p[2] for p in c), rs[0][1] if rs else 8, '·'.join(k for k, v in rs[:6])])
            nn += 1
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for g2 in set(JC) | set(RD):
        fn = os.path.join(ROOT, 'data', 'r', g2, 'jcnm.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        json.dump({'schema': 'tg-jcnm/1', 'gu': g2, 'source': '국가교통정보센터(ITS) 전국 표준노드링크 ' + VER + '판 — MOCT_NODE(교차로·도로시설·IC 이름) · MOCT_LINK(도로 이름)',
                   'note': '교차로 이름은 표준노드링크를 만드는 기관이 붙인 이름이다 — 이름난 교차로가 아니면 가까운 건물·학교 이름이 붙어 있다(예: 「롯데마트(서초점)」). 이름 대신 지번이 들어 있던 노드는 뺐다.',
                   'fields': 'j = [교차로 이름, 경도, 위도, 종류 1교차로 4도로시설 6IC·연결로, 만나는 도로 중 가장 큰 등급 1~7(8 = 모름), 만나는 도로] · r = [도로 이름, 경도, 위도, 기울기(도 · 동쪽 0 · 반시계 +), 등급]',
                   'j': JC.get(g2, []), 'r': RD.get(g2, [])}, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[g2] = os.path.getsize(fn)
    # 찾기용 한 파일(지도 「찾기」에서 처음 못 찾을 때 한 번 받는다) — 교차로 전부 + 도로 이름은 구마다 첫 자리 하나
    J = [[x[0], x[1], x[2], x[3], x[4], x[5], g2] for g2 in sorted(JC) for x in JC[g2]]
    RR = []
    for g2 in sorted(RD):
        seen = set()
        for x in RD[g2]:
            if x[0] in seen: continue
            seen.add(x[0]); RR.append([x[0], x[1], x[2], g2, x[4]])
    json.dump({'schema': 'tg-jcnm-idx/1', 'source': '국가교통정보센터(ITS) 전국 표준노드링크 ' + VER + '판', 'j': J, 'r': RR},
              open(os.path.join(ROOT, 'data', 'r', 'jcnm-idx.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['jcnm'] = gb[g2['gu']]
    R['layers']['jcnm'] = '교차로 이름·도로 이름(ITS 표준노드링크)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('junctions', nn, 'road labels', sum(len(v) for v in RD.values()), 'gus', len(gb), 'bytes', sum(gb.values()), 'max', max(gb.values()))

if __name__ == '__main__':
    main()
