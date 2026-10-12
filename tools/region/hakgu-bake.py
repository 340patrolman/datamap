# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🗺 학구도(초등학교 통학구역 · 중학교 학교군·중학구 · 고등학교 학교군) → data/school-zone/<시도 코드>.json
#   소유자 2026-10-12 「학군별 지역별」 → 반경이 아니라 **통학구역·학교군**으로 본다(그 구역의 학교 · 그 구역에 걸친 행정동)
#   원자료(공공데이터포털 · 한국교육시설안전원 학구도 · 기준일 2026-09-20 · 이용허락범위 제한 없음 · dgfile.py 로 07_API키/out/dg/<번호>/):
#     15159265 초등학교통학구역(SHP) · 15159264 중학교학교군(SHP) · 15159263 고등학교학교군(SHP) · 15159266 학교학구도연계정보(CSV — 학구 ID ↔ 학교 ID) · 15159184 초중등학교위치(CSV — 학교 ID·이름·주소·좌표)
#   좌표계 = Korea 2000 중부원점(EPSG:5186) → WGS84 · 테두리는 3m 로 줄인다
#   HAKGUDO_GB: 0 = 통학구역·학교군(·중학구) · 1 = 공동통학구역·공동학구(두 학교 가운데 고를 수 있는 곳 — 다른 구역과 겹친다)
#   행정동 겹침 = 통계청 SGIS 행정동 경계(13_관할경계/원자료/hjd20260701.geojson · CC BY 4.0)와 넓이로 — [[행정동 8자리, 이 구역 넓이 가운데 %, 그 동 넓이 가운데 %]] · 넓이 비율이지 사는 사람 비율이 아니다
#   학교 ID(B…)는 학구도 쪽 번호라 학교알리미의 정보공시 학교코드와 다르다 → 이름 + 300m 로 이은 SCHUL_CODE 를 같이 싣는다(수도권 · 07_API키/out/schoolinfo/api)
#   py -3.12 -X utf8 tools/region/hakgu-bake.py [시도 코드…]   (기본 11 41 28)
import csv, io, json, os, re, sys, glob, math, datetime, collections, warnings, shapefile
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); DG = os.path.join(KB, 'out', 'dg'); API = os.path.join(KB, 'out', 'schoolinfo', 'api'); HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
SRC = [('초', '15159265', '초등학교통학구역'), ('중', '15159264', '중학교학교군'), ('고', '15159263', '고등학교학교군')]
def rdcsv(pk):
    b = open(os.path.join(DG, pk, 'x.csv'), 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return list(csv.DictReader(io.StringIO(b.decode(e))))
        except Exception: pass
def norm(s): return re.sub(r'(서울|초등학교|중학교|고등학교|학교|\s|\(.*?\))', '', s or '')
def rings(g, nd=5):
    gj = mapping(g); rr = lambda c: [[round(x, nd), round(y, nd)] for x, y in c]
    return [rr(gj['coordinates'][0])] if gj['type'] == 'Polygon' else [rr(p[0]) for p in gj['coordinates']]
def main(sidos):
    tr = Transformer.from_crs('EPSG:5186', 'EPSG:4326', always_xy=True).transform; SCH = {r['학교ID']: r for r in rdcsv('15159184')}; LINK = collections.defaultdict(list)
    for r in rdcsv('15159266'): LINK[r['학구ID']].append(r['학교ID'])
    # 학교알리미 코드 잇기
    AL = collections.defaultdict(list)
    if glob.glob(os.path.join(API, '*_0_*.json')):
        yr = max(int(os.path.basename(x)[:4]) for x in glob.glob(os.path.join(API, '*_0_*.json')))
        for x in glob.glob(os.path.join(API, '%d_0_*.json' % yr)):
            for r in json.load(open(x, encoding='utf-8'))['list']:
                if r.get('LGTUD'): AL[(round(float(r['LGTUD']) * 100), round(float(r['LTTUD']) * 100))].append([float(r['LGTUD']), float(r['LTTUD']), r['SCHUL_NM'], r['SCHUL_CODE']])
    def al(s):
        try: lo = float(s['경도']); la = float(s['위도'])
        except Exception: return None
        best = None; a1 = norm(s['학교명'])
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for c in AL.get((round(lo * 100) + dx, round(la * 100) + dy), []):
                    d = math.hypot((lo - c[0]) * 88800, (la - c[1]) * 111000); b1 = norm(c[2])
                    if d <= 300 and a1 and (a1 == b1 or a1 in b1 or b1 in a1) and (best is None or d < best[0]): best = (d, c[3])
        return best[1] if best else None
    G = json.load(open(HJD, encoding='utf-8'))['features']; hg = []; hc = []
    for f in G:
        p = f['properties']
        if p['sido'] in sidos: hg.append(shape(f['geometry']).buffer(0)); hc.append(str(p['adm_cd2'])[:8])
    tree = STRtree(hg); harea = [g.area for g in hg]; OUT = {sd: [] for sd in sidos}; SCHOOLS = {sd: {} for sd in sidos}; td = datetime.date.today().isoformat(); base = ''
    for lv, pk, nm in SRC:
        r = shapefile.Reader(os.path.join(DG, pk, 'shp', nm), encoding='cp949', encodingErrors='replace')
        for sr in r.iterShapeRecords():
            d = sr.record.as_dict(); sd = str(d['SD_CD'])
            if sd not in sidos: continue
            base = d['BASE_DT']; g = shp_transform(tr, shape(sr.shape.__geo_interface__)).buffer(0)
            if g.is_empty: continue
            ov = []; ga = g.area
            for i in tree.query(g):
                try: a = hg[i].intersection(g).area
                except Exception: continue
                if a / ga >= 0.02 or a / harea[i] >= 0.05: ov.append([hc[i], round(a / ga * 100, 1), round(a / harea[i] * 100, 1)])
            ov.sort(key=lambda x: -x[1]); ids = LINK.get(d['HAKGUDO_ID'], [])
            for sid in ids:
                s = SCH.get(sid)
                if s and sid not in SCHOOLS[sd]: SCHOOLS[sd][sid] = [s['학교명'], s['학교급구분'], s['설립형태'], round(float(s['경도']), 5) if s['경도'] else None, round(float(s['위도']), 5) if s['위도'] else None, al(s), s['운영상태']]
            c = g.representative_point(); OUT[sd].append([lv, d['HAKGUDO_ID'], d['HAKGUDO_NM'], int(d['HAKGUDO_GB'] or 0), d['EDU_NM'], round(c.x, 5), round(c.y, 5), rings(g.simplify(0.00003)), ids, ov])
    os.makedirs(os.path.join(ROOT, 'data', 'school-zone'), exist_ok=True)
    for sd in sidos:
        items = sorted(OUT[sd], key=lambda x: ('초중고'.index(x[0]), x[4], x[2])); cnt = collections.Counter((i[0], i[3]) for i in items); nal = sum(1 for v in SCHOOLS[sd].values() if v[5])
        doc = {'schema': 'tg-school-zone/1', 'made': td, 'sido': sd, 'base': base,
               'source': '한국교육시설안전원 학구도 공공데이터(공공데이터포털 15159265 초등학교통학구역 · 15159264 중학교학교군 · 15159263 고등학교학교군 · 15159266 학교학구도연계정보 · 15159184 초중등학교위치 · 기준일 %s · 이용허락범위 제한 없음) · 행정동 경계 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0)' % base,
               'law': '「초·중등교육법 시행령」 제16조(초등학교 통학구역) · 제68조(중학교 학교군·중학구) · 제84조(고등학교 학교군) — 조문 번호는 표준데이터 설명에 적힌 것(원문 대조는 아직)',
               'note': ['종류: 초 = 통학구역(그 구역에 살면 그 학교로) · 중 = 학교군(추첨으로 군 안 학교에 배정) 또는 중학구(한 학교) · 고 = 학교군(평준화 지역 · 서울은 11개) — 고등학교는 학교군 밖 지원이 되는 전형이 있다',
                        'gb 1 = **공동통학구역·공동학구** — 두 학교 가운데 고를 수 있는 곳이라 다른 구역과 겹친다. 넓이를 더하면 겹쳐 세게 된다',
                        '행정동 겹침은 **넓이 비율**이다 — 사는 사람의 비율이 아니다(아파트 단지가 한쪽에 몰려 있으면 크게 다르다). 「구역 안 아이 수」를 어림할 때는 그 한계를 같이 적는다',
                        '학교 ID(B…)는 학구도의 번호다 — 학교알리미의 정보공시 학교코드(SCHUL_CODE)는 schools 의 여섯째 칸(이름 + 300m 로 이음 · 이 시도 %d / %d곳 · null = 못 이음)' % (nal, len(SCHOOLS[sd])),
                        '테두리는 3m 로 줄인 것이다 — 집 한 채가 어느 구역인지는 교육지원청 고시·학구도안내서비스(schoolzone.emac.kr)가 정본이다 · 해마다 조정된다(기준일 %s)' % base],
               'fields': {'schools': '{학구도 학교 ID: [학교 이름, 학교급, 설립, 경도, 위도, 정보공시 학교코드|null, 운영 상태]}',
                          'items': '[[종류(초·중·고), 학구 ID, 이름, gb(0 통학구역·학교군 · 1 공동), 교육지원청, 가운데 경도, 가운데 위도, 테두리 [[[경도, 위도]…]…], [이 구역의 학구도 학교 ID…], [[행정동 8자리, 이 구역 넓이 가운데 %, 그 동 넓이 가운데 %]…]]]'},
               'count': {'%s·%s' % (k[0], '공동' if k[1] else '구역'): v for k, v in sorted(cnt.items())}, 'schools': SCHOOLS[sd], 'items': items}
        p = os.path.join(ROOT, 'data', 'school-zone', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        print(sd, '바이트', os.path.getsize(p), dict(doc['count']), '학교', len(SCHOOLS[sd]), '학교알리미 이음', nal)
    sc = [i for i in OUT.get('11', []) if '강남서초' in i[4] and any(o[0].startswith('11650') for o in i[9])]; print('서초 걸친 구역', collections.Counter(i[0] for i in sc)); print([(i[2], len(i[8]), i[9][:3]) for i in sc if i[0] != '초'][:6]); print([(i[2], [SCHOOLS['11'][s][0] for s in i[8] if s in SCHOOLS['11']], i[9][:2]) for i in sc if i[0] == '초'][:4])
if __name__ == '__main__': main(sys.argv[1:] or ['11', '41', '28'])
