# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚗 경찰서별 교통사고 비율(인구 · 차량 · 넓이 · 도로 · 주행거리 대비) → data/acc-rate-police.json
#   소유자 2026-10-20 「인구대비 차량대비 사고발생이 많은 곳도 수치로 · 경찰서별 넓이 도로로 수치도」
#   재료
#     사고 = data/police-card.json acc.yr(TAAS 공개 사고를 250m 칸으로 모아 행정동 → 경찰서 · 2016~2025) — 최근 3해(2023~2025) 한 해 평균
#     주민·넓이 = 같은 파일 dongs [행정동, 이름, ㎢, 주민, 같이 맡는 서](주민등록 · SGIS 경계) — 여러 서가 나눠 맡는 동은 서 수로 똑같이 나눔
#     차량·주행거리 = KOSIS 한국교통안전공단 「용도별 차종별 시군구별 자동차주행거리」(426 · DT_426001_N004 · 전체·합계) 2024
#                     연간 주행거리(천㎞) ÷ (1일 평균 주행거리(㎞/대) × 365) = 그 시군구 자동차 대수(사용본거지 기준 · 어림)
#                     → 경찰서 몫 = 그 시군구 주민 중 그 서가 맡은 주민 비율로 나눔(근사)
#     도로 = 국가교통정보센터 표준노드링크(2026-09-14판 · C:/Users/knpth/regionwork/NODELINKDATA_20260914.zip · MOCT_LINK)
#            — 양방향 두 줄은 한 길로(같은 두 마디) · 가운데 점이 든 행정동으로 → 경찰서 · 「표준노드링크에 실린 길」(국도·지방도·시군구 주요 길)이라 골목은 빠진다
#   단위 묶음: KOSIS 가 경기·청주·천안·전주·포항·창원 등을 「시」로 내므로 일반구는 시로 · 인천은 2026-07 구 개편(제물포·영종·서해·검단)과 KOSIS 옛 구(중·동·서)가 달라 한 묶음
#   py -3.12 -X utf8 tools/region/accrate-bake.py
import json, os, re, io, zipfile, collections, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'accrate'); os.makedirs(OUT, exist_ok=True)
HJD = os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'); NL = r'C:/Users/knpth/regionwork/NODELINKDATA_20260914.zip'
YEAR = '2024'; ACCY = [2023, 2024, 2025]
GJ = {'동구', '서구', '남구', '북구', '광산구'}
INC = {'중구', '동구', '서구', '제물포구', '영종구', '서해구', '검단구'}


def unit(sido, gu):
    """(시도, 시군구) → 차량 묶음 열쇠"""
    if sido == '전남광주통합특별시': sido = '광주광역시' if gu in GJ else '전라남도'
    if sido == '인천광역시' and gu in INC: return ('인천광역시', '중·동·서구(2026 개편 전후 묶음)')
    if not sido.endswith('광역시') and not sido.endswith('특별시'):
        m = re.match(r'^(.+?시)(.+구)$', gu)
        if m: gu = m.group(1)
    return (sido, gu)


def kosis(YEAR=YEAR):
    p = os.path.join(OUT, 'kosis_%s.json' % YEAR)
    if not os.path.exists(p):
        K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['kosis']; K = K if isinstance(K, str) else (K.get('key') or K.get('value'))
        R = {}
        for itm in ('T001', 'T002'):
            q = {'method': 'getList', 'apiKey': K, 'orgId': '426', 'tblId': 'DT_426001_N004', 'itmId': itm, 'format': 'json', 'jsonVD': 'Y', 'prdSe': 'Y', 'startPrdDe': YEAR, 'endPrdDe': YEAR, 'objL1': 'ALL', 'objL2': '0001', 'objL3': '0001'}
            R[itm] = json.loads(urllib.request.urlopen('https://kosis.kr/openapi/Param/statisticsParameterData.do?' + urllib.parse.urlencode(q), timeout=120).read().decode('utf-8'))
        json.dump(R, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    R = json.load(open(p, encoding='utf-8'))
    # 묶음(인천 중·동·서)은 대수 = 각 구 대수 합이라 다시 셈
    veh = {}
    for itm_rows in [R['T002']]:
        cur = None; daily = {}
        for r in R['T001']:
            if len(r['C1']) == 2: cur = r['C1_NM']; continue
            daily[(cur, r['C1_NM'].replace(' ', ''))] = float(r['DT'])
        cur = None
        for r in itm_rows:
            if len(r['C1']) == 2: cur = r['C1_NM']; continue
            k = (cur, r['C1_NM'].replace(' ', '')); d = daily.get(k)
            if not d: continue
            u = unit(*k); x = veh.setdefault(u, [0.0, 0.0]); x[0] += float(r['DT']) * 1000 / (d * 365); x[1] += float(r['DT']) * 1000
    return veh                                                             # 묶음 → [대수, 연간 ㎞]


def roads(dong_of):
    p = os.path.join(OUT, 'road_dong.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    import shapefile
    from pyproj import CRS, Transformer
    z = zipfile.ZipFile(NL); tmp = os.path.join(OUT, 'moct')
    if not os.path.exists(os.path.join(tmp, 'MOCT_LINK.shp')):
        for n in ('MOCT_LINK.shp', 'MOCT_LINK.shx', 'MOCT_LINK.dbf', 'MOCT_LINK.prj', 'MOCT_LINK.cpg'): z.extract(n, tmp)
    tr = Transformer.from_crs(CRS.from_wkt(open(os.path.join(tmp, 'MOCT_LINK.prj'), encoding='utf-8').read()), 'EPSG:4326', always_xy=True)
    sr = shapefile.Reader(os.path.join(tmp, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(sr.fields[1:])}
    seen = set(); L = collections.Counter(); n = 0
    for s in sr.iterShapeRecords():
        rec = s.record; a, b = rec[fi['F_NODE']], rec[fi['T_NODE']]; k = (a, b) if a < b else (b, a)
        if k in seen: continue
        seen.add(k); pts = s.shape.points
        if not pts: continue
        mx, my = pts[len(pts) // 2]; lo, la = tr.transform(mx, my); d = dong_of(lo, la)
        if d: L[d] += float(rec[fi['LENGTH']] or 0) / 1000
        n += 1
        if n % 200000 == 0: print('  길', n, flush=True)
    out = {k: round(v, 3) for k, v in L.items()}; json.dump(out, open(p, 'w', encoding='utf-8')); return out



def nid_map():
    """행정동 8자리 → 그 동을 기본으로 맡는 경찰서 수(police.json labels 의 「~」 앞 · 반포 현장 기준 FIELD) — polcard-bake 와 같은 규칙"""
    import importlib.util as _iu
    pol = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8')); out = {}
    try:
        sp = _iu.spec_from_file_location('polcard_bake', os.path.join(ROOT, 'tools', 'region', 'polcard-bake.py')); m = _iu.module_from_spec(sp); sp.loader.exec_module(m); FIELD = m.FIELD
    except Exception:
        FIELD = {}
    for code, li in pol['dong'].items():
        ids = [x for x in str(pol['labels'][li]).split('~')[0].split(',') if x != '']
        out[code[:8]] = len(FIELD[code]) if code in FIELD else max(1, len(ids))
    return out

def main():
    NID = nid_map()
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    G = json.load(open(HJD, encoding='utf-8'))['features']; geoms, codes, meta = [], [], {}
    for f in G:
        q = f['properties']; c = str(q.get('adm_cd2') or '')[:8];   # police-card 의 동 코드 = adm_cd2 앞 8자리(adm_cd 는 옛 꼴)
        geoms.append(shape(f['geometry'])); codes.append(c); meta[c] = (q['sidonm'], q['sggnm'])
    tree = STRtree(geoms)
    def dong_of(lo, la):
        pt = Point(lo, la)
        for i in tree.query(pt):
            if geoms[i].contains(pt): return codes[i]
        return None
    PC = json.load(open(os.path.join(ROOT, 'data', 'police-card.json'), encoding='utf-8'))['st']
    veh = kosis(); v23 = kosis('2023'); FIX = {}
    for u, x in list(veh.items()):   # 2026-10-20 KOSIS 2024 부안군 연간 주행거리가 이웃 군의 1/10(원자료 잘못으로 보임) — 2023 과 견줘 ±50% 넘게 다르면 2023 값을 쓴다
        y = v23.get(u)
        if y and y[0] and not (0.67 <= x[0] / y[0] <= 1.5): veh[u] = y; FIX['·'.join(u)] = [round(x[0]), round(y[0])]
    rd = roads(dong_of)
    # 동 주민 · 묶음 주민
    upop = collections.Counter(); dpop = {}
    for st in PC.values():
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]
            if c in dpop: continue
            dpop[c] = dg[3] or 0; u = unit(*meta[c]) if c in meta else None
            if u: upop[u] += dpop[c]
    rows = {}; miss = collections.Counter()
    for sid, st in PC.items():
        pop = km2 = road = vv = vk = 0.0; vok = True
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]; w = 1.0 / NID.get(c, 1 + len(dg[4] or [])); p = (dg[3] or 0) * w
            pop += p; km2 += (dg[2] or 0) * w; road += rd.get(c, 0) * w
            u = unit(*meta[c]) if c in meta else None
            if u and u in veh and upop[u]: vv += veh[u][0] * p / upop[u]; vk += veh[u][1] * p / upop[u]
            elif p: vok = False; miss[str(u)] += 1
        a = st.get('acc') or {}; yr = a.get('yr') or []
        acc = round(sum(yr[y - 2016] for y in ACCY if 0 <= y - 2016 < len(yr)) / len(ACCY), 1) if len(yr) >= 10 else None
        r = lambda n, d, k: round(n / d * k, 2) if (n is not None and d) else None
        rows[sid] = {'n': st['n'], 'gus': st.get('gus'), 'acc': acc, 'dead10': a.get('dead'), 'pop': round(pop), 'km2': round(km2, 2), 'road_km': round(road, 1),
                     'veh': round(vv) if vok and vv else None, 'vkm': round(vk) if vok and vk else None,
                     'r_pop': r(acc, pop, 1e5), 'r_veh': r(acc, vv, 1e4) if vok else None, 'r_km2': r(acc, km2, 1), 'r_road': r(acc, road, 100), 'r_vkm': r(acc, vk, 1e8) if vok else None}
    # 순위(전국 · 많은 쪽이 1)
    for k in ('r_pop', 'r_veh', 'r_km2', 'r_road', 'r_vkm'):
        L = sorted([(v[k], s) for s, v in rows.items() if not s.startswith('_') and v[k] is not None], reverse=True)
        for i, (_, s) in enumerate(L): rows[s]['k_' + k[2:]] = i + 1
        rows['_n_' + k[2:]] = len(L)
    nat = {}
    T = [v for s, v in rows.items() if not s.startswith('_')]
    sa = sum(v['acc'] or 0 for v in T); nat = {'acc': round(sa), 'pop': sum(v['pop'] for v in T), 'km2': round(sum(v['km2'] for v in T)), 'road_km': round(sum(v['road_km'] for v in T)),
                                               'veh': round(sum(v['veh'] or 0 for v in T)), 'vkm': round(sum(v['vkm'] or 0 for v in T))}
    nat.update({'r_pop': round(sa / nat['pop'] * 1e5, 2), 'r_veh': round(sa / nat['veh'] * 1e4, 2), 'r_km2': round(sa / nat['km2'], 2), 'r_road': round(sa / nat['road_km'] * 100, 2), 'r_vkm': round(sa / nat['vkm'] * 1e8, 2)})
    doc = {'schema': 'tg-acc-rate-police/1', 'made': datetime.date.today().isoformat(), 'acc_years': ACCY, 'veh_year': YEAR,
           'source': '사고 = 도로교통공단 TAAS 공개 사고(data/police-card.json · 250m 칸 → 행정동 → 경찰서) · 주민·넓이 = 주민등록·SGIS 행정동(같은 파일) · 차량·주행거리 = KOSIS 한국교통안전공단 「용도별 차종별 시군구별 자동차주행거리」(426 · DT_426001_N004) %s · 도로 = 국가교통정보센터 표준노드링크 2026-09-14판(MOCT_LINK) · 관할 = 경찰청과 그 소속기관 직제 시행규칙 별표2' % YEAR,
           'fields': 'st{경찰서 번호(police-card 와 같음): {n 이름, gus, acc 사고(2023~2025 한 해 평균 · 건), dead10 사망자(10년), pop 주민, km2 넓이, road_km 표준노드링크 길이(㎞ · 양방향 한 길), veh 자동차(대 · 어림), vkm 연간 주행거리(㎞ · 어림), r_pop 주민 10만 명당, r_veh 자동차 1만 대당, r_km2 ㎢당, r_road 길 100㎞당, r_vkm 주행 1억 ㎞당, k_* 전국 순위(많은 쪽 1)}} · n_*(순위 낸 서 수) · nat(전국 합과 비율)',
           'note': ['**사고 수는 TAAS 공개 사고를 250m 칸으로 모아 행정동에 몰아 센 근사다** — 경찰 내부 사고 통계와 다르다(police-card 와 같은 값)',
                    '주민은 **사는 사람**이다 — 일터·번화가(서울 중구·종로·강남 등)는 낮에 오가는 사람이 많아 주민 대비 비율이 크게 나온다(그 지역이 위험하다는 뜻만은 아니다)',
                    '자동차 대수 = 그 시군구에 **사용본거지로 등록된** 차의 어림(연간 주행거리 ÷ (하루 평균 × 365)) — 경찰서 몫은 주민 비율로 나눴다 · 다른 곳에 등록된 차가 많이 오가는 곳은 크게 나온다',
                    '도로 = 표준노드링크(국도·지방도·주요 길)만 — 골목은 빠진다 · 넓이 = 행정동 넓이(산·물 포함)',
                    'KOSIS %s 값이 2023 과 ±50%% 넘게 다른 시군구는 2023 값을 썼다(veh_fix — 원자료 잘못으로 보임)' % YEAR,
                    '표준노드링크는 중앙분리 큰길을 방향마다 따로 그려 그런 길은 두 번 셀 수 있다 — 길 길이는 견주기용 값이다(국토부 도로 연장과 다르다)',
                    '여러 서가 나눠 맡는 동은 주민·넓이·길·차를 서 수로 똑같이 나눴다(근사)'],
           'nat': nat, 'miss_units': dict(miss), 'veh_fix': FIX, 'st': {s: v for s, v in rows.items() if not s.startswith('_')}, 'n_rank': {k[3:]: v for k, v in rows.items() if k.startswith('_n_')}}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'acc-rate-police.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('경찰서', len(doc['st']), '전국', nat, '차 못 붙인 묶음', dict(miss), '2023 으로 바꾼 곳', FIX)
    for k in ('r_pop', 'r_veh', 'r_road', 'r_vkm'):
        L = sorted([v for v in doc['st'].values() if v[k] is not None], key=lambda v: -v[k])
        print(k, [(v['n'], v[k]) for v in L[:5]], '…', [(v['n'], v[k]) for v in L[-3:]])


if __name__ == '__main__':
    main()
