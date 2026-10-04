# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.3.0 — 경기 생활·안전 시설(경기데이터드림) → 경기 구마다 data/r/<구>/safety.json 의 items 에 더한다
#   받기(07_API키/out/gg/*.json):
#     aed    자동제세동기(AED)설치 현황      시트 infId 2HRJNNCOR4Q8DUR0NIOP21226817   (regionwork/ggsheet.py)
#     er     응급의료기관 현황               시트 MB714IBPDSE5OPNIMW0V27143432
#     fest   문화축제 현황(제공표준)          시트 65YE99614B6X51X6084912706650
#     lamp   보안등 정보 현황(제공표준)       시트 VEY71398U2941WM4E7PV21507518
#     toilet 공중화장실 OpenAPI Publtolt · parking 주차장 ParkingPlace · ev 전기차충전소 Elctychrgstatn (키 = keys.json 의 gyeonggi)
#   py -3.12 -X utf8 tools/region/gg-life-bake.py   (safety-bake 다음에 — safety-bake 가 safety.json 을 새로 쓰면 지워진다)
#   개인 연락처(관리자 전화 mngr_telno 등)는 담지 않는다 — 기관 대표번호만.
import json, os, importlib.util, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'gg')
def L(n):
    p = os.path.join(GG, n + '.json'); return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else []
def f(v):
    try: return float(v)
    except Exception: return None
def s(v): return '' if v in (None, 'None') else str(v).strip()

def main():
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; tr = STRtree(gs)
    def gu(lat, lon):
        if lat is None or lon is None or not (36.8 < lat < 38.4 and 126.0 < lon < 127.9): return None
        q = Point(lon, lat)
        for i in tr.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    out = collections.defaultdict(lambda: collections.defaultdict(list)); cnt = collections.Counter()
    def put(key, lat, lon, row):
        g = gu(lat, lon)
        if not g or not g.startswith('41'): cnt[key + '_out'] += 1; return
        out[g][key].append([round(lat, 6), round(lon, 6)] + row); cnt[key] += 1
    for r in L('aed'):
        put('aed', f(r.get('refine_wgs84_lat')), f(r.get('refine_wgs84_logt')), [s(r.get('instl_inst_nm')), s(r.get('instl_loc')), s(r.get('refine_road_nm_addr')) or s(r.get('refine_lotno_addr')), s(r.get('instl_inst_telno'))])
    for r in L('toilet'):
        put('wc', f(r.get('REFINE_WGS84_LAT')), f(r.get('REFINE_WGS84_LOGT')), [s(r.get('PBCTLT_PLC_NM')), s(r.get('REFINE_ROADNM_ADDR')) or s(r.get('REFINE_LOTNO_ADDR')), s(r.get('PUBLFACLT_DIV_NM')), s(r.get('OPEN_TM_INFO')), '남녀 공용' if s(r.get('MALE_FEMALE_CMNUSE_TOILET_YN')) == 'Y' else '남자|여자'])
    for r in L('parking'):
        put('park', f(r.get('REFINE_WGS84_LAT')), f(r.get('REFINE_WGS84_LOGT')), [s(r.get('PARKPLC_NM')), s(r.get('LOCPLC_ROADNM_ADDR')) or s(r.get('LOCPLC_LOTNO_ADDR')), s(r.get('PARKPLC_DIV_NM')), s(r.get('PARKPLC_TYPE')), s(r.get('PARKNG_COMPRT_PLANE_CNT')),
            s(r.get('WKDAY_OPERT_BEGIN_TM')) + '~' + s(r.get('WKDAY_OPERT_END_TM')), s(r.get('CHRG_INFO')), s(r.get('DATA_STD_DE'))])
    for r in L('ev'):
        put('ev', f(r.get('REFINE_WGS84_LAT')), f(r.get('REFINE_WGS84_LOGT')), [s(r.get('CHRGSTATN_NM')), s(r.get('REFINE_ROADNM_ADDR')) or s(r.get('REFINE_LOTNO_ADDR')), s(r.get('OPERT_INST_NM')), s(r.get('CHARGER_TYPE_NM'))])
    for r in L('er'):
        put('er', f(r.get('refine_wgs84_lat')), f(r.get('refine_wgs84_logt')), [s(r.get('hosptl_nm_center_nm')), s(r.get('duty_div_nm')), s(r.get('refine_road_nm_addr')) or s(r.get('refine_lotno_addr')), s(r.get('rprs_telno'))])
    for r in L('fest'):
        put('fest', f(r.get('refine_wgs84_lat')), f(r.get('refine_wgs84_logt')), [s(r.get('fastvl_nm')), s(r.get('opnmt_plc')), s(r.get('fastvl_bgng_ymd')), s(r.get('fastvl_end_ymd')), s(r.get('host_inst_nm')) or s(r.get('sprvsn_inst_nm')), s(r.get('fastvl_cont'))[:160], s(r.get('dat_crtr_ymd'))])
    for r in L('lamp'):
        put('lamp', f(r.get('refine_wgs84_lat')), f(r.get('refine_wgs84_logt')), [s(r.get('instl_yr')), s(r.get('instl_div_nm'))])
    SRC = {'aed': '경기데이터드림 자동제세동기(AED) 설치 현황 — [위도, 경도, 기관, 설치 자리, 주소, 기관 전화]',
           'wc': '경기데이터드림 공중화장실 현황(Publtolt) — [위도, 경도, 이름, 주소, 구분, 개방 시간, 남녀]',
           'park': '경기데이터드림 주차장 현황(ParkingPlace) — [위도, 경도, 이름, 주소, 공영/민영, 노상/노외/부설, 면수, 평일 운영, 요금, 기준일]',
           'ev': '경기데이터드림 전기차 충전소 현황(Elctychrgstatn) — [위도, 경도, 충전소, 주소, 운영기관, 충전기 종류]',
           'er': '경기데이터드림 응급의료기관 현황 — [위도, 경도, 기관, 구분, 주소, 대표 전화]',
           'fest': '경기데이터드림 문화축제 현황(제공표준) — [위도, 경도, 축제, 장소, 시작, 끝, 주최·주관, 내용, 기준일]',
           'lamp': '경기데이터드림 보안등 정보 현황(제공표준) — [위도, 경도, 설치 연도, 설치 형태]'}
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}; lb = {}
    for g, items in out.items():
        fn = os.path.join(ROOT, 'data', 'r', g, 'safety.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        S = json.load(open(fn, encoding='utf-8')) if os.path.exists(fn) else {'schema': 'tg-rsafe/1', 'gu': g, 'cam': [], 'sz': [], 'items': {}, 'source': {}}
        S.setdefault('items', {}); S.setdefault('source', {})
        for k, v in items.items():
            if k == 'lamp': continue
            S['items'][k] = v; S['source'][k] = SRC[k]
        S['items'].pop('lamp', None)
        if items.get('lamp'):   # 보안등은 많아(29만) 따로 — 보안등 층을 켰을 때만 받는다
            json.dump({'schema': 'tg-lamp/1', 'gu': g, 'source': SRC['lamp'], 'pts': [[r[0], r[1], r[2], r[3]] for r in items['lamp']]}, open(os.path.join(ROOT, 'data', 'r', g, 'lamp.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
            lb[g] = os.path.getsize(os.path.join(ROOT, 'data', 'r', g, 'lamp.json'))
        json.dump(S, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g] = os.path.getsize(fn)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['safety'] = gb[g2['gu']]
        if g2['gu'] in lb: g2.setdefault('bytes', {})['lamp'] = lb[g2['gu']]
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(dict(cnt), 'gus', len(gb), 'bytes', sum(gb.values()))

if __name__ == '__main__': main()
