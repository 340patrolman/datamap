# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.11.0 — 🌾 리(里) 경계 · 리마다 가게·사고 수(브이월드 데이터 API LT_C_ADRI_INFO · 법정리 약 1.5만)
#   리 단위 인구·카드 통계는 공개되지 않는다(주민등록은 읍·면 = 행정동까지) → 이 지도에 이미 구운 점(상가·TAAS 100m 칸·사망사고)만 리 경계로 센다
#   데이터 API 는 주소 좌표(geocoder)와 한도가 따로다(2026-10-05 주소 한도 걸린 때도 응답) · 키 = 07_API키/keys.json 'vworld' · 결과에 키 없음
#   py -3.12 -X utf8 tools/region/ri-bake.py fetch → 07_API키/out/ri/ · build → data/r/<구>/ri.json
import json, os, sys, time, urllib.request, urllib.parse, collections
from shapely.geometry import shape, Point, mapping
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'ri'); os.makedirs(OUT, exist_ok=True)
R = os.path.join(ROOT, 'data', 'r')
SD = ['26', '27', '28', '31', '36', '41', '43', '44', '47', '48', '50', '51', '52', '12']   # 리가 있는 시도(2026-10-05 조회 · 서울·광주 옛 29·대전 0)

def fetch():
    vk = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
    for sd in SD:
        pg = 1
        while True:
            fn = os.path.join(OUT, '%s_%02d.json' % (sd, pg))
            if os.path.exists(fn): j = json.load(open(fn, encoding='utf-8'))
            else:
                q = {'service': 'data', 'request': 'GetFeature', 'data': 'LT_C_ADRI_INFO', 'key': vk, 'format': 'json', 'size': '1000', 'page': str(pg), 'geometry': 'true', 'attrFilter': 'li_cd:like:' + sd, 'crs': 'EPSG:4326', 'domain': '340patrolman.github.io'}
                for t in range(4):
                    try:
                        j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/data?' + urllib.parse.urlencode(q), headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://340patrolman.github.io/'}), timeout=180).read().decode())['response']; break
                    except Exception as e: print('다시', sd, pg, e, flush=True); time.sleep(5); j = {}
                if j.get('status') != 'OK': print('멈춤', sd, pg, j.get('status'), j.get('error'), flush=True); return
                json.dump(j, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); time.sleep(0.5)
            tp = int(j['page']['total']); print(sd, pg, '/', tp, flush=True)
            if pg >= tp: break
            pg += 1

def build():
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); gus = {g['gu']: g for g in IX['gus']}
    SIDX = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8')); CLS = [c[1] for c in SIDX['cls']]
    by = collections.defaultdict(list); seen = set(); nogu = 0
    for fn in sorted(os.listdir(OUT)):
        j = json.load(open(os.path.join(OUT, fn), encoding='utf-8'))
        for f in j['result']['featureCollection']['features']:
            p = f['properties']; cd = p['li_cd']
            if cd in seen or cd[:2] not in SD: continue
            seen.add(cd)
            if cd[:5] not in gus: nogu += 1; continue
            by[cd[:5]].append((cd, p['full_nm'], shape(f['geometry']).buffer(0)))
    tot = 0; nri = 0
    for gu, items in by.items():
        geo = [g for _, _, g in items]; tr = STRtree(geo)
        def where(lon, lat):
            q = Point(lon, lat)
            for i in tr.query(q):
                if geo[i].contains(q): return i
            return None
        st = [collections.Counter() for _ in items]; acc = [[0, 0, 0] for _ in items]; fat = [0] * len(items); dead = [0] * len(items)
        try:
            S = json.load(open(os.path.join(R, gu, 'stores.json'), encoding='utf-8')); O, K = S['o'], S['k']
            for q in S['pts']:
                i = where(O[0] + q[0] / K[0], O[1] + q[1] / K[1])
                if i is not None: st[i][CLS[q[2]] if q[2] < len(CLS) else '?'] += 1
        except Exception: pass
        try:
            T = json.load(open(os.path.join(R, gu, 'taas10.json'), encoding='utf-8'))
            for c in T['cells']:
                i = where(c[1], c[0])
                if i is not None: acc[i][0] += sum(c[2:12]); acc[i][1] += c[12]; acc[i][2] += c[13]
            for f in T['fatal']:
                i = where(f[17], f[16])
                if i is not None: fat[i] += 1; dead[i] += f[12]
        except Exception: pass
        out = []
        for i, (cd, nm, g) in enumerate(items):
            s = g.simplify(0.00012, preserve_topology=True)
            polys = [s] if s.geom_type == 'Polygon' else list(getattr(s, 'geoms', []))
            P = [[[[round(x, 5), round(y, 5)] for x, y in ring.coords] for ring in [pg.exterior] + list(pg.interiors)] for pg in polys if pg.geom_type == 'Polygon' and not pg.is_empty]
            c = g.representative_point()
            nm2 = nm.split(' ')[-2:] if nm else ['', '']
            out.append({'k': cd, 'name': ' '.join(nm2), 'c': [round(c.x, 5), round(c.y, 5)], 'polys': P, 'st': sum(st[i].values()), 'stb': dict(st[i].most_common(4)), 'acc': acc[i][0], 'dead': acc[i][1], 'ser': acc[i][2], 'fat': fat[i]})
        doc = {'schema': 'tg-ri/1', 'gu': gu, 'source': '리 경계 = 국토교통부 브이월드 데이터 API LT_C_ADRI_INFO(법정리 · ' + time.strftime('%Y-%m-%d') + ' 받음 · 약 13m 단순화) · 가게 = 소상공인시장진흥공단 상가(상권)정보 · 사고 = 도로교통공단 TAAS 2016~2025(100m 칸 가운데가 든 리)',
               'fields': 'ri = [{k 법정리 코드, name 읍면 리, c 안쪽 한 점, polys, st 가게 수, stb 대분류 상위 4, acc 사고 10년(칸 가운데 기준 · 근사), dead 사망자, ser 중상자, fat 사망사고 건}]',
               'note': '리 단위 인구·카드 매출은 공개 통계가 없다(주민등록은 읍·면까지) — 리는 점을 세는 그릇으로만 쓴다 · 사고는 100m 칸 가운데가 든 리에 몰아 셈', 'ri': out}
        pth = os.path.join(R, gu, 'ri.json'); json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gus[gu].setdefault('bytes', {})['ri'] = os.path.getsize(pth); tot += os.path.getsize(pth); nri += len(out)
    IX['layers']['ri'] = '🌾 리(里) 경계 · 리마다 가게·사고 수'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('리', nri, '구', len(by), '구 코드 없음', nogu, '바이트', tot)

if __name__ == '__main__': fetch() if sys.argv[1:] == ['fetch'] else build()
