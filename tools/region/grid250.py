# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 공간 뼈대(전국 확장 설계서 ver.1 · Phase 1): 250m 국가표준격자
#   격자 = 국가지점번호 체계(EPSG:5179 UTM-K) 250m — 서울시 「250M격자 생활인구」(OA-22784)의 격자 번호와 같다(2026-10-05 실측: 8,567칸 모두 250m 배수 · 「다사52255325」)
#   번호 = 가로 100km 글자(가 = 700,000m …) + 세로 100km 글자(가 = 1,300,000m …) + 가로 4자리 + 세로 4자리(100km 안 10m 단위 · 칸 왼쪽 아래 모서리)
#   행정동은 집계 단위로만 — 칸마다 겹치는 행정동과 넓이 비율(%)을 둔다(행정동 경계 = SGIS/admdongkor hjd 2026-07)
#   py -3.12 -X utf8 tools/region/grid250.py → data/r/<구>/grid.json (tg-grid250/1)
import json, os, sys, importlib.util
from pyproj import Transformer
L = '가나다라마바사아자차카타파하'
_to = Transformer.from_crs('EPSG:4326', 'EPSG:5179', always_xy=True); _fr = Transformer.from_crs('EPSG:5179', 'EPSG:4326', always_xy=True)
def code_xy(x, y):
    x = int(x // 250 * 250); y = int(y // 250 * 250)
    return L[(x - 700000) // 100000] + L[(y - 1300000) // 100000] + '%04d%04d' % (x % 100000 // 10, y % 100000 // 10)
def code_ll(lat, lon): x, y = _to.transform(lon, lat); return code_xy(x, y)
def xy_code(c): return 700000 + L.index(c[0]) * 100000 + int(c[2:6]) * 10, 1300000 + L.index(c[1]) * 100000 + int(c[6:10]) * 10
def center_ll(c): x, y = xy_code(c); lon, lat = _fr.transform(x + 125, y + 125); return round(lat, 6), round(lon, 6)

def main():
    from shapely.geometry import shape, box
    from shapely.ops import transform as stf
    from shapely.strtree import STRtree
    ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, gus = DB.seoul_gus()
    P = [(f['properties']['sgg'], f['properties']['adm_cd2'][:8], stf(_to.transform, shape(f['geometry']))) for f in feats]
    NM = {f['properties']['adm_cd2'][:8]: f['properties']['adm_nm'].split(' ')[-1] for f in feats}
    tree = STRtree([p[2] for p in P]); IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    have = {g['gu'] for g in IX['gus']}; per = {}
    x0, y0, x1, y1 = tree.geometries[0].bounds
    for g in tree.geometries: b = g.bounds; x0, y0, x1, y1 = min(x0, b[0]), min(y0, b[1]), max(x1, b[2]), max(y1, b[3])
    x0 = x0 // 250 * 250; y0 = y0 // 250 * 250; n = 0
    x = x0
    while x < x1:
        y = y0
        while y < y1:
            c = box(x, y, x + 250, y + 250); hit = []
            for i in tree.query(c):
                a = P[i][2].intersection(c).area
                if a > 1: hit.append((a, P[i][0], P[i][1]))
            if hit:
                hit.sort(reverse=True); tot = sum(h[0] for h in hit); gu = hit[0][1]
                if gu in have:
                    cd = code_xy(x, y); lat, lon = center_ll(cd)
                    row = [cd, lat, lon, round(tot / 625)]   # 칸 안 땅(행정동 안) 비율 %
                    for a, _, k8 in hit: row += [k8, round(a / 625)]
                    per.setdefault(gu, []).append(row); n += 1
            y += 250
        x += 250
    for gu, cells in per.items():
        doc = {'schema': 'tg-grid250/1', 'gu': gu, 'grid': '국가지점번호식 250m 격자(EPSG:5179 UTM-K) — 서울시 250M격자 생활인구와 같은 번호',
               'fields': '[격자 번호, 칸 가운데 위도, 경도, 칸 안 행정동 땅 %, 행정동 8자리, 그 동 넓이 %, …(넓은 순)] — 칸은 가장 넓게 걸친 동의 구에 둔다',
               'source': '행정동 경계 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0) · 격자 계산은 이 도구', 'cells': cells,
               'names': {k: NM[k] for k in sorted({c[i] for c in cells for i in range(4, len(c), 2)})}}
        pth = os.path.join(ROOT, 'data', 'r', gu, 'grid.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    for g in IX['gus']:
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'grid.json')
        if os.path.exists(pth): g.setdefault('bytes', {})['grid'] = os.path.getsize(pth)
    IX['layers']['grid'] = '250m 국가표준격자 뼈대(칸 → 행정동 넓이 비율)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('칸', n, '구', len(per), '바이트', sum(os.path.getsize(os.path.join(ROOT, 'data', 'r', g, 'grid.json')) for g in per))

if __name__ == '__main__':
    if sys.argv[1:] == ['test']:
        print(code_ll(37.57852626, 126.96063187), '기대 다사52255325', center_ll('다사52255325'))
    else: main()
