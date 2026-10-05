# -*- coding: utf-8 -*-
# 데이터 압축지도 「지역 자료」 ⑥ — 서울 25개 구 TAAS 교통사고 10년(2016~2025 · v0.10.96)
#   입력: 07_API키/out/region/taas10_raw.json — TAAS GIS 사고분석 화면 안에서 모은 것(MAP2D.md §8 ⑧ · CLAUDE.md v0.10.96)
#         {cells: [[구, gx, gy, a(21), 주 법규위반 코드, 그 건수, 주 사고유형 코드]], fatal: [[구, 해, 월, 요일, 시, 등급, 유형, 위반, 도로, 날씨, 노면, 가해, 피해, 사망, 중상, 경상, 부상신고, x, y]], dic}
#         gx·gy = UTM-K(EPSG:5179) 100m 격자 번호 · 개인정보(나이·성별·상해 부위·사고번호·일)는 모으는 자리에서 버렸다
#   py -3.12 -X utf8 tools/region/taas10-bake.py [원자료 시도] → data/r/<구>/taas10.json (서초 data/taas10-seocho.json 과 같은 꼴)
#   v2.3.1 고유키 중복 거름 · 시도 경계 밖은 3km 안 그 시도 구로 · 수집일 = 원자료 파일 날짜
import json, os, time, sys, importlib.util
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region', 'taas10_raw.json')
tr = Transformer.from_crs('EPSG:5179', 'EPSG:4326', always_xy=True)

def gu_finder(region=None):   # v0.10.102 구 칸이 빈 원자료(경기 — 시 단위로 모음)는 칸 가운데가 든 시군구 경계로 나눈다
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    from shapely.ops import transform as stf
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(f['geometry']) for f in feats]; tr2 = STRtree(gs)
    # v2.3.1 그 시도 경계 밖(바닷가·이웃 시도) 사고는 3km 안 가장 가까운 그 시도 구에 붙인다 — 거리는 UTM-K(m)
    pre = {'경기': '41', '서울': '11', '인천': '28'}.get(region); to5179 = Transformer.from_crs('EPSG:4326', 'EPSG:5179', always_xy=True).transform
    rg = [(feats[i]['properties']['sgg'], stf(to5179, g)) for i, g in enumerate(gs) if (feats[i]['properties']['sgg'][:2] == pre if pre else True)]   # v2.10.0 「전국」도 가장 가까운 구에(부산 신항 매립지 사망사고 29건이 행정동 경계 밖이라 빠졌었다)
    def f(lon, lat, x=None, y=None):
        q = Point(lon, lat)
        for i in tr2.query(q):
            if gs[i].contains(q):
                g = feats[i]['properties']['sgg']
                if not pre or g[:2] == pre: return g
                break
        if not rg or x is None: return None
        qm = Point(x, y); best = min(rg, key=lambda t: t[1].distance(qm))
        return best[0] if best[1].distance(qm) <= NEAR_M else None
    return f

NEAR_M = 3000

def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else RAW; region = sys.argv[2] if len(sys.argv) > 2 else '서울'
    R = json.load(open(raw, encoding='utf-8')); G = {}; gf = None; lost = 0; lostF = []; near = [0, 0]
    got = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(raw)))   # v2.3.1 수집일 = 원자료 파일 날짜(다시 구운 날이 아니다)
    # v2.3.1 고유키로 중복을 막는다(2026-10-05 소유자 지시) — 사고번호는 개인정보 규칙으로 버렸으므로
    #   칸 = (구, gx, gy) · 사망사고 = (해, 월, 요일, 시, x, y, 사망자) — 구 칸은 빼고 본다(같은 사고가 두 구 이름으로 올 때도 잡는다)
    seenC = set(); seenF = set(); dupC = dupF = 0
    for c in R['cells']:
        gu, gx, gy, a, tv, tvn, tt = c
        if (gu, gx, gy) in seenC: dupC += 1; continue
        seenC.add((gu, gx, gy))
        lon, lat = tr.transform(gx * 100 + 50, gy * 100 + 50)
        if not gu:
            gf = gf or gu_finder(region); gu = gf(lon, lat, gx * 100 + 50, gy * 100 + 50)
            if not gu: lost += sum(a[:10]); continue
        G.setdefault(gu, {'cells': [], 'fatal': []})['cells'].append([round(lat, 6), round(lon, 6)] + a + [tv, tvn, tt])
    for f in R['fatal']:
        k = (f[1], f[2], f[3], f[4], f[17], f[18], f[13])
        if k in seenF: dupF += 1; continue
        seenF.add(k)
        gu = f[0]; lon, lat = tr.transform(f[17], f[18])
        if not gu:
            gf = gf or gu_finder(region); gu = gf(lon, lat, f[17], f[18])
            if not gu: lostF.append((f[1], f[2], round(lat, 5), round(lon, 5), f[13])); continue
        G.setdefault(gu, {'cells': [], 'fatal': []})['fatal'].append(f[1:17] + [round(lat, 6), round(lon, 6)])
    print('고유키로 거른 중복 — 칸', dupC, '· 사망사고', dupF)
    print('어느 구에도 못 붙인 사망사고(경계에서 %dm 넘게 떨어짐)' % NEAR_M, len(lostF), lostF)
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); IX = json.load(open(rp, encoding='utf-8')); gb = {}
    keep = {'경기': '41', '서울': '11', '인천': '28'}.get(region)
    for gu, v in list(G.items()):
        if keep and gu[:2] != keep: print('다른 시도 구 — 쓰지 않음', gu, len(v['cells']), len(v['fatal'])); del G[gu]   # v0.10.102 사고: 경기 원자료 중 서울 경계 안 칸이 서울 구 파일을 덮어썼다 — 그 시도 구만 쓴다(v2.3.1 부터 그런 칸은 gu_finder 가 3km 안 그 시도 구로 보낸다)
    for gu, v in G.items():
        cnt = sum(sum(c[2:12]) for c in v['cells'])
        doc = {'schema': 'tg-taas10/1', 'gu': gu,
               'source': '도로교통공단 교통사고분석시스템(TAAS) GIS 사고분석 — %s %s 2016~2025 사고 전부(사망·중상·경상·부상신고) · %s 수집' % (region, gu, got),
               'count': cnt, 'note': '개인정보(나이·성별·상해 부위·사고번호·날짜의 일)는 받는 자리에서 버렸다. 사고는 100m 칸으로 묶었다(UTM-K 100m 격자 → 칸 가운데를 WGS84 로). 사망사고는 한 건씩(연·월·요일·시만).',
               'cellFields': '[위도, 경도, 2016…2025 해마다 건수(10), 사망자, 중상자, 보행자 피해, 자전거 관련, PM 관련, 이륜·원동기 가해, 밤(20~6시), 0~6시, 6~12시, 12~18시, 18~24시, 주 법규위반 코드, 그 건수, 주 사고유형 코드]',
               'fatalFields': '[해, 월, 요일 코드(1 월…7 일), 시, 등급, 사고유형, 법규위반, 도로형태, 날씨, 노면, 가해 차종, 피해 차종, 사망, 중상, 경상, 부상신고, 위도, 경도]',
               'dow': ['', '월', '화', '수', '목', '금', '토', '일'], 'dic': R['dic'], 'cells': v['cells'], 'fatal': v['fatal']}
        pth = os.path.join(ROOT, 'data', 'r', gu, 'taas10.json'); os.makedirs(os.path.dirname(pth), exist_ok=True)
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(pth)
        print(gu, cnt, len(v['cells']), len(v['fatal']), gb[gu])
    for g in IX['gus']:
        if g['gu'] in gb: g['bytes']['taas10'] = gb[g['gu']]
    IX['layers']['taas10'] = 'TAAS 교통사고 10년(100m 칸 · 사망사고 한 건씩)'
    json.dump(IX, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('total', sum(gb.values()), '경계 밖 사고', lost)

if __name__ == '__main__': main()
