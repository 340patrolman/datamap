# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.21.0 — 🟧 공시지가 지도(대지 ㎡당 중앙값 · 250m 칸 · 행정동)
#   원자료 = 국토교통부 개별공시지가(브이월드 연속지적도 LP_PA_CBND_BUBUN 속성 jiga · 공공데이터포털 15124014 「국토교통부_개별공시지가정보」 이용허락범위 제한 없음)
#   py -3.12 -X utf8 tools/region/jiga-bake.py fetch <구 또는 시도 코드…>   → 07_API키/out/jiga/<구>.json (필지 한 줄씩: PNU·공시지가·지목·면적·대표점 — 이 PC 에만)
#   py -3.12 -X utf8 tools/region/jiga-bake.py build [<구 또는 시도 코드…>]  → data/r/<구>/jiga.json (tg-jiga/1) · index.json bytes
#   집계 = 지목 「대」(대지) 필지만 · 칸·동마다 ㎡당 공시지가 중앙값(넓이 무게 없음) · 필지 자리 = 필지 안 대표점 · 도로·하천·임야 등은 땅값 뜻이 달라 뺀다
import json, os, re, sys, time, statistics, collections, urllib.request, urllib.parse, importlib.util
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform as stf
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'jiga'); R = os.path.join(ROOT, 'data', 'r')
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
sp = importlib.util.spec_from_file_location('g250', os.path.join(ROOT, 'tools', 'region', 'grid250.py')); G250 = importlib.util.module_from_spec(sp); sp.loader.exec_module(G250)
TO = Transformer.from_crs('EPSG:4326', 'EPSG:5179', always_xy=True)
H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://340patrolman.github.io/datamap/'}

def gus_of(args):
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); al = [g['gu'] for g in IX['gus']]
    if not args: return al
    o = []
    for a in args: o += [g for g in al if g.startswith(a)]
    return o

def page(key, gu, n):
    p = {'service': 'data', 'request': 'GetFeature', 'data': 'LP_PA_CBND_BUBUN', 'key': key, 'format': 'json', 'size': '1000', 'page': str(n), 'crs': 'EPSG:4326',
         'geometry': 'true', 'attribute': 'true', 'attrFilter': 'pnu:like:' + gu, 'domain': '340patrolman.github.io'}
    for i in range(5):
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/data?' + urllib.parse.urlencode(p), headers=H), timeout=120).read())['response']
            if j.get('status') in ('OK', 'NOT_FOUND'): return j
            raise SystemExit('브이월드 오류 %s %s' % (j.get('status'), (j.get('error') or {}).get('code')))
        except SystemExit: raise
        except Exception as e: print('  다시', i + 1, e, flush=True); time.sleep(3 + 3 * i)
    raise SystemExit('받기 실패 %s p%d' % (gu, n))

def fetch(gus):
    key = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']; os.makedirs(OUT, exist_ok=True)
    for gu in gus:
        fp = os.path.join(OUT, gu + '.json')
        if os.path.exists(fp): print(gu, '있음 — 건너뜀'); continue
        rows = []; n = 1; tot = None; t0 = time.time()
        while True:
            j = page(key, gu, n)
            if j.get('status') == 'NOT_FOUND': break
            tot = int(j['page']['total'])
            for f in j['result']['featureCollection']['features']:
                a = f['properties']; jb = a.get('jibun') or ''; m = re.search(r'([가-힣]+)$', jb); jm = m.group(1) if m else ''
                try: g = shape(f['geometry'])
                except Exception: continue
                if g.is_empty: continue
                rp = g.representative_point(); ar = stf(TO.transform, g).area
                rows.append([a.get('pnu'), int(a['jiga']) if (a.get('jiga') or '').isdigit() else None, jm, round(ar, 1), round(rp.y, 6), round(rp.x, 6), (a.get('gosi_year') or '') + (a.get('gosi_month') or '')])
            if n >= tot: break
            n += 1
        json.dump({'gu': gu, 'got': time.strftime('%Y-%m-%d'), 'fields': 'PNU·공시지가(원/㎡)·지목·면적(㎡ · EPSG:5179)·대표점 위도·경도·공시 연월', 'rows': rows}, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print(gu, '필지', len(rows), '쪽', tot, round(time.time() - t0), '초', flush=True)

def build(gus):
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['adm_cd2'][:8], f['properties']['sgg']) for f in g['features']]; T = STRtree([x[0] for x in F])
    def dong(la, lo):
        p = Point(lo, la)
        for i in T.query(p):
            if F[i][0].contains(p): return F[i][1], F[i][2]
        return None, None
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}; tot = 0
    for gu in gus:
        fp = os.path.join(OUT, gu + '.json')
        if not os.path.exists(fp) or gu not in known: continue
        rows = json.load(open(fp, encoding='utf-8'))['rows']
        cell = collections.defaultdict(list); dg = collections.defaultdict(list); yr = collections.Counter(); alln = collections.Counter(); alld = collections.Counter()
        for r in rows:
            pnu, v, jm, ar, la, lo, ym = r
            c = G250.code_ll(la, lo); k8, sg = dong(la, lo); alln[c] += 1
            if sg != gu: k8 = None   # 동은 이 구 것만(경계 필지의 대표점이 이웃 구로 넘어간 것은 칸에만)
            if k8: alld[k8] += 1
            if jm != '대' or not v: continue
            yr[ym[:4]] += 1; cell[c].append((v, ar))
            if k8: dg[k8].append((v, ar))
        def agg(a): vs = [x[0] for x in a]; return [round(statistics.median(vs)), len(vs), round(sum(x[1] for x in a)), round(max(vs))]
        y = yr.most_common(1)[0][0] if yr else ''
        out = {'schema': 'tg-jiga/1', 'gu': gu, 'year': y,
               'source': '국토교통부 개별공시지가(브이월드 연속지적도 LP_PA_CBND_BUBUN · 공공데이터포털 15124014 「국토교통부_개별공시지가정보」 이용허락범위 제한 없음) · %s년 1월 1일 기준' % y,
               'note': '지목 「대」(대지) 필지만 · ㎡당 공시지가 중앙값(원) · 칸·동 = 필지 안 대표점이 든 곳 · 공시지가는 세금·보상 기준값이지 시세가 아니다',
               'fields': 'grid/dong = {키: [대지 ㎡당 중앙값(원), 대지 필지 수, 대지 넓이 합(㎡), 가장 높은 ㎡당(원)]} · n = 칸·동마다 모든 필지 수',
               'grid': {k: agg(v) for k, v in cell.items()}, 'dong': {k: agg(v) for k, v in dg.items()}, 'n': {'grid': dict(alln), 'dong': dict(alld)}}
        op = os.path.join(R, gu, 'jiga.json'); os.makedirs(os.path.dirname(op), exist_ok=True)
        json.dump(out, open(op, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        known[gu].setdefault('bytes', {})['jiga'] = os.path.getsize(op); tot += 1
        print(gu, known[gu]['name'], '대지', sum(len(v) for v in dg.values()), '/ 필지', len(rows), '칸', len(cell), '동', len(dg), y, os.path.getsize(op), 'B')
    IX['layers']['jiga'] = '🟧 공시지가 지도(대지 ㎡당 중앙값 · 250m 칸·동)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('구웠다', tot)

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'build'; gus = gus_of(sys.argv[2:])
    if cmd == 'fetch': fetch(gus)
    else: build(gus)
