# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.7.0 — 📹 실시간 교통 CCTV(국도·고속도로) 목록: 국가교통정보센터 cctvInfo(HLS · cctvType=4) → 구마다 itscctv.json
#   영상 주소(cctvsec.ktict.co.kr · https · CORS *)에는 키가 들어 있지 않다(2026-10-04 확인) — 목록을 구워 두면 폰은 ITS 호출 없이 영상만 연다.
#   열 때마다 2시간짜리 인증표가 붙는 구조라 목록 주소가 언제까지 사는지는 지켜본다 → 안 열리면 지도 카드의 「🔄 목록 새로 받기」(ITS 2건)
#   ITS 키 = 07_API키/keys.json "its" (개발키 월 100건 — 이 도구는 2건)
#   py -3.12 -X utf8 tools/region/itscctv-bake.py fetch   → 07_API키/out/its/cctv_its.json · cctv_ex.json
#   py -3.12 -X utf8 tools/region/itscctv-bake.py build   → data/r/<구>/itscctv.json · r/index.json bytes.itscctv
import json, os, sys, time, urllib.request, importlib.util, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'its')
BOX = (124.5, 33.0, 131.95, 38.7)   # v2.8.0 전국(종전 수도권 126.3~127.9 · 36.85~38.35)

def fetch():
    os.makedirs(OUT, exist_ok=True)
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['its']; k = (k if isinstance(k, str) else next(iter(k.values()))).strip()
    for typ in ('its', 'ex'):
        u = 'https://openapi.its.go.kr:9443/cctvInfo?apiKey=%s&type=%s&cctvType=4&minX=%s&maxX=%s&minY=%s&maxY=%s&getType=json' % (k, typ, BOX[0], BOX[2], BOX[1], BOX[3])
        b = urllib.request.urlopen(u, timeout=180).read().decode('utf-8')
        assert k[:8] not in b
        open(os.path.join(OUT, 'cctv_%s.json' % typ), 'w', encoding='utf-8').write(b); print(typ, len(b))

def build():
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; st = STRtree(gs)
    def gu(lon, lat):
        q = Point(lon, lat)
        for i in st.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    G = collections.defaultdict(list); when = None
    for typ in ('its', 'ex'):
        fn = os.path.join(OUT, 'cctv_%s.json' % typ); when = when or time.strftime('%Y-%m-%d %H:%M', time.localtime(os.path.getmtime(fn)))
        for x in json.load(open(fn, encoding='utf-8'))['response']['data']:
            lon, lat, url = float(x['coordx']), float(x['coordy']), x.get('cctvurl') or ''
            if not url.startswith('https://'): continue
            g2 = gu(lon, lat)
            if g2: G[g2].append([(x.get('cctvname') or '').strip(), round(lon, 5), round(lat, 5), url, typ])
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for g2, items in G.items():
        f2 = os.path.join(ROOT, 'data', 'r', g2, 'itscctv.json')
        if not os.path.isdir(os.path.dirname(f2)): continue
        json.dump({'schema': 'tg-itscctv/1', 'gu': g2, 'at': when, 'source': '국가교통정보센터(ITS) CCTV 정보 OpenAPI(cctvInfo · 국도 its · 고속도로 ex · HLS) — 목록 ' + when + ' 받음 · 영상 = 각 도로관리기관',
                   'fields': '[이름, 경도, 위도, 영상 주소(HLS), its 국도 / ex 고속도로]', 'items': items}, open(f2, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[g2] = os.path.getsize(f2)
    for g2 in R['gus']:
        b2 = g2.setdefault('bytes', {})
        if g2['gu'] in gb: b2['itscctv'] = gb[g2['gu']]
        else: b2.pop('itscctv', None)
    R['layers']['itscctv'] = '실시간 교통 CCTV 목록(ITS 국도·고속도로)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('cctv', sum(len(v) for v in G.values()), 'gus', len(gb), 'bytes', sum(gb.values()))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
