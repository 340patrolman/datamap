# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏫 학교 경계(학교용지 필지) → data/school-bound/<구>.json
#   소유자 2026-10-12 「학교 담당 경찰관이 공공데이터를 충분히 이용할 수 있게」 → 교육환경보호구역 200m 는 **학교 경계**에서 잰다(교육환경법 제8조 제1항). 점에서 재면 운동장만큼 어긋난다
#   만드는 법: 학교 자리(학교알리미 학교기본정보의 좌표 — 07_API키/out/schoolinfo/api/<해>_0_<학교급>_<구>.json) 둘레 250m 의 연속지적도(국토교통부 브이월드 LP_PA_CBND_BUBUN · 열쇠 vworld)에서
#     지목이 「학」(학교용지)인 필지를 받아 → 학교 점을 품거나 가장 가까운(60m 안) 필지에서 시작해 맞닿은(3m 안) 「학」 필지를 이어 붙인다 → 한 덩어리의 바깥 테두리
#   ⚠ 근사다: 지목이 「학」이 아닌 땅을 쓰는 학교(대지·임야 위 학교)는 경계를 못 만든다(null) · 이웃 학교와 필지가 맞닿으면 한 덩어리로 붙는다(shared 에 적는다) · 연속지적도는 측량 성과가 아니다
#   받은 필지는 07_API키/out/schoolbound/<구>.json 에 캐시(다시 돌리면 통신 없음) · 브이월드 하루 한도를 지번 좌표 변환과 같이 쓴다
#   py -3.12 -X utf8 tools/region/schoolbound-bake.py <구 코드…|11|41|28>
import json, os, sys, glob, time, datetime, urllib.request, urllib.parse
from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); API = os.path.join(KB, 'out', 'schoolinfo', 'api'); CACHE = os.path.join(KB, 'out', 'schoolbound'); M = 1 / 111000.0
def key(): return json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
def parcels(lo, la):
    dx = 250 * M / 0.8; dy = 250 * M
    q = dict(service='data', request='GetFeature', data='LP_PA_CBND_BUBUN', key=key(), domain='https://340patrolman.github.io', format='json', size=1000, page=1, geometry='true', attribute='true', crs='EPSG:4326', geomFilter='BOX(%f,%f,%f,%f)' % (lo - dx, la - dy, lo + dx, la + dy))
    for t in range(3):
        try:
            r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/data?' + urllib.parse.urlencode(q), headers={'Referer': 'https://340patrolman.github.io/'}), timeout=60).read().decode('utf-8'))['response']
            if r['status'] == 'OK': return [[f['properties'].get('pnu'), f['geometry']] for f in r['result']['featureCollection']['features'] if str(f['properties'].get('jibun', '')).strip().endswith('학')]
            if r['status'] == 'NOT_FOUND': return []
            if 'LIMIT' in json.dumps(r): raise SystemExit('브이월드 하루 한도 — 내일 이어서')
        except SystemExit: raise
        except Exception: time.sleep(3)
    return None
def one(gu):
    yr = max(int(os.path.basename(f)[:4]) for f in glob.glob(os.path.join(API, '*_0_*_%s.json' % gu))); S = []
    for knd in ('02', '03', '04'):
        p = os.path.join(API, '%d_0_%s_%s.json' % (yr, knd, gu))
        if os.path.exists(p): S += [r for r in json.load(open(p, encoding='utf-8'))['list'] if r.get('LGTUD') and r.get('CLOSE_YN', 'N') != 'Y']
    os.makedirs(CACHE, exist_ok=True); cp = os.path.join(CACHE, gu + '.json'); C = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}; items = []; got = 0; new = 0
    for r in S:
        code = r['SCHUL_CODE']; lo = float(r['LGTUD']); la = float(r['LTTUD'])
        if code not in C:
            ps = parcels(lo, la)
            if ps is None: continue
            C[code] = ps; new += 1; time.sleep(0.12)
            if new % 20 == 0: json.dump(C, open(cp, 'w', encoding='utf-8'))
        G = [(pnu, shape(g).buffer(0)) for pnu, g in C[code]]; pt = Point(lo, la); poly = None; pn = []
        if G:
            d = sorted(((g.distance(pt), i) for i, (_, g) in enumerate(G)));
            if d[0][0] <= 60 * M:
                use = {d[0][1]}; grew = True
                while grew:
                    grew = False; u = unary_union([G[i][1] for i in use]).buffer(3 * M)
                    for i, (_, g) in enumerate(G):
                        if i not in use and g.intersects(u): use.add(i); grew = True
                poly = unary_union([G[i][1] for i in use]).buffer(1.5 * M).buffer(-1.5 * M).simplify(0.6 * M); pn = sorted(G[i][0] for i in use)
        if poly is not None and not poly.is_empty:
            got += 1; gj = mapping(poly); rr = lambda c: [[round(x, 6), round(y, 6)] for x, y in c]
            rings = [rr(gj['coordinates'][0])] if gj['type'] == 'Polygon' else [rr(p[0]) for p in gj['coordinates']]
            area = round(poly.area / (M * M) * 0.8)
        else: rings = None; area = None
        items.append([code, r['SCHUL_NM'], r['SCHUL_KND_SC_CODE'], rings, area, len(pn)])
    json.dump(C, open(cp, 'w', encoding='utf-8'))
    key2 = {}
    for it in items:
        if it[3]: key2.setdefault(json.dumps(it[3][0][:3]), []).append(it[0])
    shared = [v for v in key2.values() if len(v) > 1]
    doc = {'schema': 'tg-school-bound/1', 'made': datetime.date.today().isoformat(), 'gu': gu,
           'source': '국토교통부 브이월드 연속지적도(LP_PA_CBND_BUBUN) 가운데 지목 「학」(학교용지) 필지 — 학교 자리는 학교알리미 학교기본정보(%d 공시)' % yr,
           'law': '「교육환경 보호에 관한 법률」 제8조 제1항 — 교육환경보호구역 = 학교경계등에서 직선거리 200m(절대보호구역 = 학교출입문에서 50m) · 국가법령정보 원문 2026-10-12 확인',
           'note': ['**근사 경계다** — 학교 점을 품거나 60m 안에 있는 「학」 필지에서 시작해 맞닿은 「학」 필지를 이어 붙인 바깥 테두리. 연속지적도는 측량 성과가 아니고, 교육청이 고시한 보호구역 도면이 정본이다',
                    '지목이 「학」이 아닌 땅 위의 학교는 경계가 없다(null) — 그런 학교는 점에서 재는 수밖에 없다 · 이 구에서 경계를 만든 학교 %d / %d곳' % (got, len(items)),
                    '이웃 학교와 필지가 맞닿으면 한 덩어리로 붙는다(같은 재단의 중·고 등) — shared 에 같은 덩어리를 쓰는 학교 코드를 적었다',
                    '출입문 자리는 이 자료에 없다 — 절대보호구역(출입문에서 50m)은 만들 수 없다'],
           'fields': {'items': '[[정보공시 학교코드, 학교 이름, 학교급 코드(02 초·03 중·04 고), 테두리 [[[경도, 위도]…]…]|null(덩어리가 여럿이면 여러 개), 넓이 ㎡(어림)|null, 이어 붙인 필지 수]]', 'shared': '[[같은 덩어리를 쓰는 학교 코드…]]'},
           'shared': shared, 'items': items}
    os.makedirs(os.path.join(ROOT, 'data', 'school-bound'), exist_ok=True); p = os.path.join(ROOT, 'data', 'school-bound', gu + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(gu, '학교', len(items), '경계', got, '새로 받음', new, '바이트', os.path.getsize(p), '붙은 덩어리', len(shared)); sys.stdout.flush(); return items
if __name__ == '__main__':
    a = sys.argv[1:] or ['11650']; gus = []
    for x in a: gus += sorted(set(os.path.basename(f)[:-5].split('_')[3] for f in glob.glob(os.path.join(API, '*_0_02_%s*.json' % x)))) if len(x) == 2 else [x]
    for g in gus:
        it = one(g)
        if g == '11650': print([(i[1], i[4], i[5]) for i in it][:60])
