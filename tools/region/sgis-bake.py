# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.4.0 — 통계청 SGIS 집계구(동보다 잘게 · 약 500명 단위) 인구·가구·주택·사업체·종사자 (서울·경기)
#   SGIS OpenAPI3 https://sgisapi.mods.go.kr/OpenAPI3 (옛 kostat 주소는 닫힘) · 키 = 07_API키/keys.json 의 "sgis" {consumer_key, consumer_secret}
#   통계: /stats/searchpopulation · household · house · company (year=2023 · adm_cd=동 · low_search=1 → 그 동의 집계구 14자리)
#   경계: /boundary/statsarea.geojson (year=2023 이지만 돌려주는 base_year=2025 · EPSG:5179 UTM-K) — 통계와 집계구 수가 다를 수 있다 → 코드로 맞추고 짝 없는 칸은 비운다
#   py -3.12 -X utf8 tools/region/sgis-bake.py fetch   → 07_API키/out/sgis/<동코드>.json (받은 동은 건너뜀)
#   py -3.12 -X utf8 tools/region/sgis-bake.py build   → data/r/<구>/jgg.json · r/index.json bytes.jgg
import json, os, sys, time, urllib.request, importlib.util, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'sgis')
H = 'https://sgisapi.mods.go.kr/OpenAPI3'; YEAR = '2023'
TK = {'t': None, 'at': 0}

def raw(p):
    return json.loads(urllib.request.urlopen(urllib.request.Request(H + p, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read().decode('utf-8'))
def token():
    if TK['t'] and time.time() - TK['at'] < 3000: return TK['t']
    K = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['sgis']
    TK['t'] = raw('/auth/authentication.json?consumer_key=%s&consumer_secret=%s' % (K['consumer_key'].strip(), K['consumer_secret'].strip()))['result']['accessToken']; TK['at'] = time.time()
    return TK['t']
def g(p):
    for a in range(5):
        try:
            j = raw(p + ('&' if '?' in p else '?') + 'accessToken=' + token())
            if str(j.get('errCd')) in ('-401', '-410'): TK['t'] = None; continue   # 토큰 만료
            return j
        except Exception as e: print('retry', str(e)[:80], flush=True); time.sleep(3)
    return {}

def fetch():
    os.makedirs(OUT, exist_ok=True)
    for sido in ('11', '31'):
        for sg in g('/addr/stage.json?cd=%s' % sido).get('result') or []:
            for d in g('/addr/stage.json?cd=%s' % sg['cd']).get('result') or []:
                fn = os.path.join(OUT, d['cd'] + '.json')
                if os.path.exists(fn): continue
                o = {'cd': d['cd'], 'name': d['addr_name'], 'sgg': sg['addr_name'], 'sido': sido}
                for k, ap in (('pop', 'searchpopulation'), ('hh', 'household'), ('house', 'house'), ('corp', 'company')):
                    j = g('/stats/%s.json?year=%s&adm_cd=%s&low_search=1' % (ap, YEAR, d['cd'])); o[k] = j.get('result') or []
                    if j.get('errCd') not in (0, '0', None): o[k + '_err'] = j.get('errMsg')
                j = g('/boundary/statsarea.geojson?year=%s&adm_cd=%s' % (YEAR, d['cd'])); o['bnd'] = j.get('features') or []
                json.dump(o, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
            print(sg['addr_name'], flush=True)
    print('DONE', flush=True)

def num(v):
    try: return int(float(v))
    except Exception: return None

def build():
    from shapely.geometry import shape, Point
    from shapely.ops import transform
    from shapely.strtree import STRtree
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:5179', 'EPSG:4326', always_xy=True)
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; st = STRtree(gs)
    def gu(lon, lat):
        q = Point(lon, lat)
        for i in st.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    G = collections.defaultdict(list); nost = nob = 0; bys = collections.Counter()
    for fn in os.listdir(OUT):
        o = json.load(open(os.path.join(OUT, fn), encoding='utf-8'))
        S = collections.defaultdict(dict)
        for r in o.get('pop', []): S[r['adm_cd']]['p'] = num(r.get('population'))
        for r in o.get('hh', []): S[r['adm_cd']]['h'] = num(r.get('household_cnt')); S[r['adm_cd']]['f'] = r.get('avg_family_member_cnt')
        for r in o.get('house', []): S[r['adm_cd']]['u'] = num(r.get('house_cnt'))
        for r in o.get('corp', []): S[r['adm_cd']]['c'] = num(r.get('corp_cnt')); S[r['adm_cd']]['w'] = num(r.get('tot_worker'))
        for f in o.get('bnd', []):
            cd = f['properties']['adm_cd']; v = S.get(cd)
            if not v: nost += 1
            gm = transform(lambda x, y, z=None: tr.transform(x, y), shape(f['geometry'])).simplify(0.00003, preserve_topology=True)
            if gm.is_empty: continue
            c = gm.representative_point(); gg = gu(c.x, c.y)
            if not gg: continue
            polys = [gm] if gm.geom_type == 'Polygon' else list(gm.geoms)
            area = sum(p.area for p in polys) * 111000 * 88800   # ㎡ 근사(서울 위도)
            v = v or {}
            G[gg].append([cd, o['name'], [[[round(x, 5), round(y, 5)] for x, y in p.exterior.coords][:-1] for p in polys], round(area), v.get('p'), v.get('h'), v.get('f'), v.get('u'), v.get('c'), v.get('w')])
            bys[f['properties'].get('base_year')] += 1
        nob += len(set(S) - {f['properties']['adm_cd'] for f in o.get('bnd', [])})
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for g2, items in G.items():
        fn = os.path.join(ROOT, 'data', 'r', g2, 'jgg.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        json.dump({'schema': 'tg-jgg/1', 'gu': g2, 'year': YEAR, 'bnd_year': dict(bys),
                   'source': '통계청 SGIS OpenAPI(sgisapi.mods.go.kr) — 집계구 인구·가구·주택·사업체·종사자 ' + YEAR + '년 · 집계구 경계 ' + '·'.join(sorted(k for k in bys if k)) + '년 (UTM-K → WGS84)',
                   'note': '집계구 = 통계청이 인구 약 500명 단위로 나눈 가장 작은 통계 구역. 통계(2023)와 경계(2025) 해가 달라 경계는 있는데 통계가 빈 칸이 있다(코드로 맞춤 · 빈 칸은 회색). 값이 작은 칸은 통계청이 가린다(N/A → 빈 칸).',
                   'fields': '[집계구 코드, 동, 고리들, 넓이㎡, 인구, 가구, 평균 가구원, 주택, 사업체, 종사자]', 'items': items},
                  open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[g2] = os.path.getsize(fn)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['jgg'] = gb[g2['gu']]
    R['layers']['jgg'] = '집계구 인구·가구·주택·사업체(통계청 SGIS)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('items', sum(len(v) for v in G.values()), 'bnd without stats', nost, 'stats without bnd', nob, 'gus', len(gb), 'bytes', sum(gb.values()), dict(bys))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
