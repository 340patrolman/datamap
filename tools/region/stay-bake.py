# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.26.0 — 🛏 숙박시설(전국) · 행정안전부 지방행정인허가(LOCALDATA) 파일 다섯(공공데이터포털 15044967 관광숙박업 · 15045085 한옥체험업 · 15044965 관광펜션업 · 15113628 농어촌민박업 · 15044968 숙박업 · 2025-11-27 · 이용허락 제한 없음)
#   받는 곳 = file.localdata.go.kr/file/download/<이름>/info (data.go.kr 「바로가기」가 넘기는 주소 · Referer 가 data.go.kr 이어야 열린다) → 07_API키/out/lodging/<이름>.csv(cp949)
#   py -3.12 -X utf8 tools/region/stay-bake.py  → data/r/<구>/stay.json(tg-stay/1) · index.json bytes
#   ① 영업/정상·휴업만 ② 좌표정보(X·Y) = 중부원점 TM(EPSG:5174) → WGS84 ③ 좌표 없으면 브이월드 검색(도로명 → 지번 · 캐시 out/lodging/geo.json) ④ 전화번호는 옮기지 않는다(농어촌민박은 개인 집)
import csv, io, json, os, re, sys, time, urllib.request, urllib.parse, collections
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); SRC = os.path.join(KB, 'out', 'lodging'); R = os.path.join(ROOT, 'data', 'r')
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
# 종류 번호 = 지도 색·범례 차례
TY = ['관광호텔·가족·소형·전통호텔', '호스텔', '휴양콘도', '한옥체험(한옥스테이)', '관광펜션', '농어촌민박', '숙박업(여관·모텔·여인숙·생활숙박)']
FILES = [('tourist_accommodations', '관광숙박업'), ('hanok_experience', '한옥체험업'), ('tourist_pensions', '관광펜션업'), ('rural_homestays', '농어촌민박업'), ('lodgings', '숙박업')]

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):
        try: return list(csv.DictReader(io.StringIO(b.decode(enc))))
        except Exception: pass

def kind(f, r):
    if f == 'tourist_accommodations':
        d = (r.get('관광숙박업상세명') or '').strip()
        return 1 if d == '호스텔업' else 2 if d == '휴양콘도미니엄업' else 0
    return {'hanok_experience': 3, 'tourist_pensions': 4, 'rural_homestays': 5, 'lodgings': 6}[f]

def road_core(a):
    a = re.sub(r'\s*\(.*?\)\s*$', '', a or '').strip(); return a.split(',')[0].strip()

def num(s):
    s = (s or '').strip(); return int(float(s)) if re.match(r'^\d+(\.\d+)?$', s) else None

def main():
    vk = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
    tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True)
    cp = os.path.join(SRC, 'geo.json'); cache = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}
    def search(q, cat):
        if not q: return None
        key = cat + '|' + q
        if key in cache: return cache[key]
        p = {'service': 'search', 'request': 'search', 'version': '2.0', 'crs': 'EPSG:4326', 'size': '1', 'page': '1', 'query': q, 'type': 'address', 'category': cat, 'format': 'json', 'errorformat': 'json', 'key': vk}
        res = None
        for i in range(3):
            try:
                j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/search?' + urllib.parse.urlencode(p), headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode())['response']
                if j.get('status') == 'OK': pt = j['result']['items'][0]['point']; res = [round(float(pt['y']), 6), round(float(pt['x']), 6)]
                elif j.get('status') == 'ERROR': print('검색 오류', (j.get('error') or {}).get('code'), flush=True); return None
                break
            except Exception: time.sleep(2)
        cache[key] = res; time.sleep(0.2); return res
    rows = []; nfix = 0; fail = collections.Counter(); stat = collections.Counter()
    for f, nm in FILES:
        for r in read(os.path.join(SRC, f + '.csv')):
            st = (r.get('영업상태명') or '').strip()
            if st not in ('영업/정상', '휴업'): continue
            la = lo = None
            try:
                lo, la = tr.transform(float(r['좌표정보(X)']), float(r['좌표정보(Y)']))
                if not (33 < la < 39 and 124 < lo < 132): la = lo = None
            except (TypeError, ValueError, KeyError): pass
            how = 0
            if la is None:
                g = search(road_core(r.get('도로명주소')), 'road') or search(re.sub(r'\s+', ' ', (r.get('지번주소') or '').strip()), 'parcel')
                if g: la, lo = g; how = 1; nfix += 1
                else: fail[nm] += 1; continue
            k = kind(f, r); stat[k] += 1
            rooms = num(r.get('객실수'))
            if f == 'lodgings': rooms = (num(r.get('양실수')) or 0) + (num(r.get('한실수')) or 0) or None
            sub = (r.get('관광숙박업상세명') or r.get('업태구분명') or '').strip()
            rows.append([round(la, 6), round(lo, 6), (r.get('사업장명') or '').strip(), k, 1 if st == '휴업' else 0, rooms, road_core(r.get('도로명주소')) or (r.get('지번주소') or '').strip(), (r.get('인허가일자') or '').strip()[:10], sub if sub and sub != nm else '', (r.get('영문상호명') or '').strip(), how])
        if len(cache) % 50 == 0: json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(x['geometry']), x['properties']['sgg'], x['properties']['adm_cd2'][:8]) for x in g['features']]; T = STRtree([x[0] for x in F])
    def where(la, lo):
        p = Point(lo, la)
        for i in T.query(p):
            if F[i][0].contains(p): return F[i][1], F[i][2]
        return None, None
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}
    G = collections.defaultdict(lambda: {'pts': [], 'dong': collections.defaultdict(lambda: [0] * len(TY))}); nogu = 0
    for r in rows:
        gu, k8 = where(r[0], r[1])
        if not gu or gu not in known: nogu += 1; continue
        G[gu]['pts'].append(r + [k8 or ''])
        if k8: G[gu]['dong'][k8][r[3]] += 1
    for gu, v in G.items():
        p = os.path.join(R, gu, 'stay.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump({'schema': 'tg-stay/1', 'gu': gu, 'types': TY,
                   'source': '행정안전부 지방행정인허가(LOCALDATA · 2025-11-27) — 관광숙박업 · 한옥체험업 · 관광펜션업 · 농어촌민박업 · 숙박업(공공데이터포털 15044967·15045085·15044965·15113628·15044968 · 이용허락 제한 없음) · 영업/정상·휴업만 · 좌표 EPSG:5174 → WGS84 · 좌표 없던 곳은 브이월드 주소 검색',
                   'fields': 'pts = [위도, 경도, 사업장명, 종류(types 번호), 0 영업·1 휴업, 객실수, 주소, 인허가일자, 세부 업태, 영문 상호, 1 = 주소로 찾은 자리, 행정동] · dong = {행정동: 종류마다 곳 수}',
                   'note': '외국인관광 도시민박업은 「🏡 외국인관광 도시민박」 레이어 · 투숙 인원·국적은 공개되지 않는다 · 숙박업(위생)과 관광숙박업(관광)은 같은 호텔이 두 번 등록됐을 수 있다 · 전화번호는 싣지 않는다', 'pts': v['pts'], 'dong': v['dong']},
                  open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        known[gu].setdefault('bytes', {})['stay'] = os.path.getsize(p)
    IX['layers']['stay'] = '🛏 숙박시설(호텔·호스텔·콘도·한옥·펜션·농어촌민박·숙박업 · 전국)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('지도 점', len(rows) - nogu, '종류별', {TY[k]: v for k, v in sorted(stat.items())}, '주소로 찾음', nfix, '못 찾음', dict(fail), '구 밖', nogu, '구', len(G))

if __name__ == '__main__': main()
