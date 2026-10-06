# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.17.0 — 🏡 외국인관광 도시민박(전국) · 행정안전부 「문화_외국인관광도시민박업」(공공데이터포털 15044966 · 지방행정인허가 · 원본 갱신 2026-10-05)
#   갱신 = 분기마다 파일을 새로 받아 이 도구로 다시 굽는다(일일 API 안 씀) — py -3.12 -X utf8 tools/region/minbak-bake.py <원본 csv> [기준일 YYYYMMDD]
#   ① 영업상태 「영업/정상」·「휴업」만(폐업·취소/말소/만료 제외) ② 좌표정보(X·Y) = 중부원점 TM(Bessel · EPSG:5174) → WGS84
#   ③ 좌표가 없으면 브이월드 「검색」 API(req/search · 주소 변환 API 와 한도가 따로)로 도로명주소 → 지번주소 차례 · 캐시 07_API키/out/foreign/minbak_geo.json
#   ④ 점이 든 시군구(SGIS 행정동 2026-07)의 r/<구>/minbak.json · 정리본 CSV(지시서 열) 07_API키/out/foreign/외국인관광도시민박업_영업중_WGS84_<기준일>.csv
import csv, io, json, os, re, sys, time, urllib.request, urllib.parse, collections
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'foreign'); R = os.path.join(ROOT, 'data', 'r')
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')

def read(p):
    b = open(p, 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):
        try: return list(csv.DictReader(io.StringIO(b.decode(enc))))
        except Exception: pass

def road_core(a):   # 「서울특별시 종로구 평창25길 27, 1층 (평창동)」 → 「서울특별시 종로구 평창25길 27」
    a = re.sub(r'\s*\(.*?\)\s*$', '', a or '').strip()
    return a.split(',')[0].strip()

def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'minbak_raw.csv'); ymd = sys.argv[2] if len(sys.argv) > 2 else time.strftime('%Y%m%d')
    vk = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
    rows = [r for r in read(src) if (r.get('영업상태명') or '').strip() in ('영업/정상', '휴업')]
    tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True)
    cp = os.path.join(OUT, 'minbak_geo.json'); cache = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}
    def search(q, cat):
        if not q: return None
        key = cat + '|' + q
        if key in cache: return cache[key]
        p = {'service': 'search', 'request': 'search', 'version': '2.0', 'crs': 'EPSG:4326', 'size': '1', 'page': '1', 'query': q, 'type': 'address', 'category': cat, 'format': 'json', 'errorformat': 'json', 'key': vk}
        res = None
        for i in range(3):
            try:
                j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/search?' + urllib.parse.urlencode(p), headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode())['response']
                if j.get('status') == 'OK':
                    pt = j['result']['items'][0]['point']; res = [round(float(pt['y']), 6), round(float(pt['x']), 6)]
                elif j.get('status') == 'ERROR': print('검색 오류', (j.get('error') or {}).get('code'), flush=True); return None
                break
            except Exception: time.sleep(2)
        cache[key] = res; time.sleep(0.25); return res
    out = []; geo_n = 0; fail = []
    for r in rows:
        la = lo = None
        try:
            x, y = float(r['좌표정보(X)']), float(r['좌표정보(Y)']); lo, la = tr.transform(x, y)
            if not (33 < la < 39 and 124 < lo < 132): la = lo = None
        except (TypeError, ValueError, KeyError): pass
        how = '원본'
        if la is None:
            g = search(road_core(r.get('도로명주소')), 'road') or search(re.sub(r'\s+', ' ', (r.get('지번주소') or '').strip()), 'parcel')
            if g: la, lo = g; how = '주소 찾기'; geo_n += 1
            else: fail.append([r.get('관리번호'), r.get('사업장명'), r.get('도로명주소') or r.get('지번주소')])
        r['_la'], r['_lo'], r['_how'] = la, lo, how; out.append(r)
    json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['sgg'], f['properties']['adm_cd2'][:8], f['properties']['sidonm'] if 'sidonm' in f['properties'] else '') for f in g['features']]; T = STRtree([x[0] for x in F])
    def where(la, lo):
        p = Point(lo, la)
        for i in T.query(p):
            if F[i][0].contains(p): return F[i][1], F[i][2]
        return None, None
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}
    G = collections.defaultdict(lambda: {'pts': [], 'dong': collections.Counter()}); sido = collections.Counter(); sido_open = collections.Counter(); nogu = []
    def addr_sido(a): return (a or '').split(' ')[0]
    for r in out:
        sd = addr_sido(r.get('도로명주소') or r.get('지번주소')); sido[sd] += 1
        if (r.get('영업상태명') or '').strip() == '영업/정상': sido_open[sd] += 1
        if r['_la'] is None: continue
        gu, k8 = where(r['_la'], r['_lo'])
        if not gu:   # 바닷가 — 행정동 경계(단순화) 밖이면 주소의 시군구로
            a = (r.get('도로명주소') or r.get('지번주소') or '').split(' ')
            sdc = {'서울특별시': '11', '부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '대전광역시': '30', '울산광역시': '31', '세종특별자치시': '36', '경기도': '41', '강원특별자치도': '51', '충청북도': '43', '충청남도': '44', '전북특별자치도': '52', '전남광주통합특별시': '12', '경상북도': '47', '경상남도': '48', '제주특별자치도': '50'}.get(a[0] if a else '')
            c = [x for x in known if sdc and x[:2] == sdc and len(a) > 1 and known[x]['name'] in (a[1], (a[1] + (a[2] if len(a) > 2 else '')))]
            gu = c[0] if len(c) == 1 else None
        if not gu or gu not in known: nogu.append([r.get('사업장명'), r.get('도로명주소')]); continue
        rooms = (r.get('객실수') or '').strip()
        G[gu]['pts'].append([r['_la'], r['_lo'], (r.get('사업장명') or '').strip(), 1 if r['영업상태명'].strip() == '휴업' else 0, int(float(rooms)) if re.match(r'^\d+(\.\d+)?$', rooms) else None,
                             road_core(r.get('도로명주소')) or (r.get('지번주소') or '').strip(), (r.get('인허가일자') or '').strip(), (r.get('관리번호') or '').strip(), 1 if r['_how'] != '원본' else 0, k8])
        if k8: G[gu]['dong'][k8] += 1
    tot = 0
    for gu, v in G.items():
        p = os.path.join(R, gu, 'minbak.json')
        json.dump({'schema': 'tg-minbak/1', 'gu': gu, 'source': '행정안전부 문화_외국인관광도시민박업(공공데이터포털 15044966 · 지방행정인허가 · 원본 갱신 2026-10-05) — 영업/정상·휴업만 · 좌표 EPSG:5174 → WGS84 · 좌표 없던 곳은 브이월드 주소 검색',
                   'fields': 'pts = [위도, 경도, 사업장명, 0 영업·1 휴업, 객실수, 주소, 인허가일자, 관리번호, 1 = 주소로 찾은 자리, 행정동] · dong = {행정동: 업소 수}', 'note': '외국인 관광객에게 집을 내주는 민박(관광진흥법) · 투숙 인원·국적은 공개되지 않는다 · 분기마다 다시 받는다', 'pts': v['pts'], 'dong': v['dong']},
                  open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        known[gu].setdefault('bytes', {})['minbak'] = os.path.getsize(p); tot += len(v['pts'])
    IX['layers']['minbak'] = '🏡 외국인관광 도시민박(전국 · 영업·휴업)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    # 정리본 CSV(지시서 열)
    cols = ['관리번호', '사업장명', '영업상태명', '시도', '시군구', '도로명주소', '지번주소', '객실수', '인허가일자', '위도', '경도', '최종수정시점']
    cf = os.path.join(OUT, '외국인관광도시민박업_영업중_WGS84_%s.csv' % ymd)
    with open(cf, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(cols)
        for r in out:
            a = (r.get('도로명주소') or r.get('지번주소') or '').split(' ')
            w.writerow([r.get('관리번호'), r.get('사업장명'), r.get('영업상태명'), a[0] if a else '', a[1] if len(a) > 1 else '', r.get('도로명주소'), r.get('지번주소'), r.get('객실수'), r.get('인허가일자'), r['_la'] or '', r['_lo'] or '', r.get('최종수정시점')])
    json.dump(fail, open(os.path.join(OUT, 'minbak_좌표못찾음.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('대상', len(out), '원본 좌표 없음→주소로 찾음', geo_n, '못 찾음', len(fail), '구 밖', len(nogu), '지도 점', tot, '구', len(G))
    print('시도별(영업+휴업 · 영업)', [(k, sido[k], sido_open[k]) for k in sorted(sido, key=lambda k: -sido[k])])
    print('못 찾은 곳', fail)

if __name__ == '__main__': main()
