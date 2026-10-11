# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚥 T-GIS 신호 교차로 서울 전체(소유자 2026-10-11 「우선 서초 강남 동작 관악 … 그리고 서울 전지역 확대」) → data/tgis-seoul.json
#   data/tgis-seocho.json(서초·방배서 432곳)과 **같은 꼴**로 서울 8,097곳: items[[c 교차로코드, n 명칭, la, lo, p 연동교차로코드(딸려 도는 부모 · 0 없음), pe 관할 경찰서 코드, cits 서울 C-ITS 교차로 번호(15m 안), gu 구 코드(GU_CDE)]]
#   재료 = 서울시 T-GIS 교통안전시설물 「교차로(A008_P)」 shapefile(공공데이터포털 공개자료 — 소유자 2026-10-02 받음 · NAS \\NAS-baranno815\home\A008_P → C:/Users/knpth/regionwork/a008 · EPSG:5186)
#     C-ITS 번호 = 교통안전 신호등 실시간 정보의 교차로 지도정보(07_API키/out/rti/crsrd_map_info.json — 서울 2,779곳)
#   전기 고객번호·계량기번호 칸(CUST_NUM·MSE_NUM)은 옮기지 않는다. 신호 현시·주기는 이 표에 없다
#   py -3.12 -X utf8 tools/signal/tgis-bake.py
import json, os, math, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
def main():
    import shapefile
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:5186', 'EPSG:4326', always_xy=True)
    r = shapefile.Reader('C:/Users/knpth/regionwork/a008/A008_P.shp', encoding='cp949', encodingErrors='replace'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}
    M = [x for x in json.load(open(os.path.join(KB, '07_API키', 'out', 'rti', 'crsrd_map_info.json'), encoding='utf-8')) if str(x.get('lclgvNm', '')).startswith('서울')]; grid = collections.defaultdict(list)
    for x in M: lo, la = float(x['mapCtptIntLot']), float(x['mapCtptIntLat']); grid[(int(lo * 1000), int(la * 1000))].append((lo, la, int(x['crsrdId'])))
    items = []; seen = collections.Counter(); bad = 0
    for sr in r.iterShapeRecords():
        rec = sr.record; c = int(rec[fi['CSS_NUM']] or 0); lo, la = tr.transform(*sr.shape.points[0])
        if not c or not (126.7 < lo < 127.3 and 37.4 < la < 37.72): bad += 1; continue
        seen[c] += 1; best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for a, b, no in grid.get((int(lo * 1000) + dx, int(la * 1000) + dy), ()):
                    d = math.hypot((a - lo) * 88400.0, (b - la) * 111000.0)
                    if d <= 15 and (best is None or d < best[0]): best = (d, no)
        def num(v):
            try: return int(v or 0)
            except Exception: return 0
        items.append([c, (rec[fi['CSS_NAM']] or '').strip(), round(la, 6), round(lo, 6), num(rec[fi['LK_CS_CDE']]), num(rec[fi['NW_PE_CDE']]), best[1] if best else 0, num(rec[fi['GU_CDE']])])
    items.sort(); codes = set(x[0] for x in items); dup = [c for c, v in seen.items() if v > 1]
    doc = {'schema': 'tg-tgis/1', 'made': datetime.date.today().isoformat(), 'area': '서울특별시 전체 — T-GIS 신호 교차로',
           'source': '서울시 T-GIS 교통안전시설물 「교차로(A008_P)」(교통운영과 테이블 정의서 · 공공데이터포털 공개자료 — 소유자 2026-10-02 받음 · EPSG:5186 → WGS84) · C-ITS 번호 = 교통안전 신호등 실시간 정보의 교차로 지도정보(한국지역정보개발원 · 공공데이터포털 15157604)',
           'fields': 'items[[c 교차로코드(CSS_NUM), n 명칭, la 위도, lo 경도, p 연동교차로코드(LK_CS_CDE — 그 신호가 딸려 도는 부모 교차로 · 0 = 없음), pe 관할 경찰서 코드(NW_PE_CDE · 340 서초서 · 380 방배서 …), cits 서울 C-ITS 교차로 번호(15m 안에 같은 신호가 있을 때 · 0 = 없음), gu 구 코드(GU_CDE — 원자료 값)]] — data/tgis-seocho.json 과 앞 일곱 칸이 같다',
           'note': ['전기 고객번호·계량기번호 칸은 옮기지 않았다 · 신호 현시·주기·차로는 이 표에 없다', '연동교차로코드는 간선 연동 그룹이 아니라 그 신호가 딸려 도는 부모 교차로다(이름에 「(연등)」이 붙은 곳이 대부분)',
                    '교차로코드가 겹치는 줄 %d개 · 부모 코드가 이 표에 없는 줄 %d개 — 원자료 그대로' % (len(dup), sum(1 for x in items if x[4] and x[4] not in codes))],
           'items': items}
    p = os.path.join(ROOT, 'data', 'tgis-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(items), '· 좌표 밖·코드 없음', bad, '· 코드 겹침', len(dup), dup[:8], '· C-ITS 번호 붙음', sum(1 for x in items if x[6]), '· 연동 부모 있음', sum(1 for x in items if x[4]), '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
