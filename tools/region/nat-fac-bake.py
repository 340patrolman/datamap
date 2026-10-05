# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.14.0 — 전국 생활·안전시설(공공데이터포털 「전국 ○○ 표준데이터」 · 키 data_go_kr 로 부를 수 있는 것만 · 2026-10-06 시험)
#   무인단속카메라(tn_pubr_public_unmanned_traffic_camera_api) · 어린이보호구역(tn_pubr_public_child_prtc_zn_api) · 주차장(tn_pubr_prkplce_info_api)
#   초중등학교 위치(tn_pubr_public_elesch_mskul_lc_api) · 신호등(tn_pubr_public_traffic_light_api)
#   ⚠ 403(활용신청 필요): CCTV · 보안등 · 공중화장실 · AED · 전기차충전 · 도서관 · 횡단보도 — 코워크 요청
#   서울·경기(11·41)는 이미 있는 safety.json·fac.json 을 두고 신호등(tl)·주차장(서울)만 더한다 · 그 밖 시도는 safety.json(cam·sz·park·tl) · fac.json(edu·aca 점만) 을 새로
#   학원 = 이 지도의 소진공 상가(stores.json)에서 입시·교과학원(P10501) · 구 = 점이 든 SGIS 행정동의 구 · py -3.12 -X utf8 tools/region/nat-fac-bake.py fetch → build
import json, os, sys, time, urllib.request, urllib.parse, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'nat'); os.makedirs(OUT, exist_ok=True)
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
R = os.path.join(ROOT, 'data', 'r')
EP = {'cam': 'tn_pubr_public_unmanned_traffic_camera_api', 'sz': 'tn_pubr_public_child_prtc_zn_api', 'park': 'tn_pubr_prkplce_info_api', 'school': 'tn_pubr_public_elesch_mskul_lc_api', 'tl': 'tn_pubr_public_traffic_light_api'}
SRC = {'cam': '전국무인교통단속카메라표준데이터(공공데이터포털 · 행정안전부 표준데이터)', 'sz': '전국어린이보호구역표준데이터(공공데이터포털 15012891)', 'park': '전국주차장정보표준데이터(공공데이터포털) — [위도, 경도, 이름, 주소, 공영/민영, 노상/노외/부설, 면수, 평일 운영, 요금, 기준일]',
       'school': '전국초중등학교위치표준데이터(공공데이터포털 · 한국교육시설안전원)', 'tl': '전국신호등표준데이터(공공데이터포털 15028198 · 경찰청 소관 · 지자체 제공) — [위도, 경도, 도로명, 주소, 신호등구분 코드, 현시 순서, 현시 시간(초), 잔여시간 표시, 음향신호기, 관리기관, 기준일]'}
def f6(x):
    try: return round(float(x), 6) if x not in (None, '') else None
    except (TypeError, ValueError): return None

def fetch():
    K = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']
    for k, ep in EP.items():
        fn = os.path.join(OUT, k + '.json')
        if os.path.exists(fn): continue
        out, page = [], 1
        while True:
            q = urllib.parse.urlencode(dict(pageNo=page, numOfRows=1000, type='json'))
            j = None
            for i in range(5):
                try: j = json.loads(urllib.request.urlopen('https://api.data.go.kr/openapi/%s?serviceKey=%s&%s' % (ep, K, q), timeout=180).read().decode('utf-8')); break
                except Exception: time.sleep(5 + 5 * i)
            if j is None: print('멈춤', k, page); break
            b = (j.get('response') or j).get('body') or {}; it = b.get('items') or []
            if isinstance(it, dict): it = it.get('item') or []
            if isinstance(it, dict): it = [it]
            out += it; tot = int(b.get('totalCount') or 0)
            if page * 1000 >= tot or not it: break
            page += 1
        json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); print(k, len(out), flush=True)

def build():
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['sgg']) for f in g['features']]; tree = STRtree([x[0] for x in F])
    def gu_of(la, lo):
        if not la or not lo: return None
        p = Point(lo, la)
        for i in tree.query(p):
            if F[i][0].contains(p): return F[i][1]
        return None
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu'] for x in IX['gus']}
    S = collections.defaultdict(lambda: {'cam': [], 'sz': [], 'items': collections.defaultdict(list)}); E = collections.defaultdict(lambda: {'edu': [], 'aca': []})
    J = lambda k: json.load(open(os.path.join(OUT, k + '.json'), encoding='utf-8'))
    for r in J('cam'):
        la, lo = f6(r.get('latitude')), f6(r.get('longitude')); gu = gu_of(la, lo)
        if gu: S[gu]['cam'].append({'at': r.get('itlpc'), 'road': r.get('roadRouteNm'), 'lat': la, 'lon': lo, 'se': r.get('regltSe'), 'lim': int(r.get('lmttVe') or 0) if str(r.get('lmttVe') or '').isdigit() else 0, 'zone': r.get('prtcareaType'), 'yr': r.get('installationYear'), 'sec': r.get('ovrspdRegltSctnLt') or ''})
    seen = set()
    for r in J('sz'):
        la, lo = f6(r.get('latitude')), f6(r.get('longitude')); key = (r.get('trgetFcltyNm'), la)
        if key in seen or not la: continue
        seen.add(key); gu = gu_of(la, lo)
        if gu: S[gu]['sz'].append({'name': r.get('trgetFcltyNm'), 'kind': r.get('fcltyKnd'), 'lat': la, 'lon': lo, 'addr': r.get('rdnmadr') or r.get('lnmadr'), 'police': r.get('cmptncPolcsttnNm'), 'gu': '',
                                   'cctv': (int(r['cctvNumber']) if (r.get('cctvNumber') or '').strip().isdigit() else -1) if r.get('cctvYn') == 'Y' else 0,
                                   'rw': float(r['prtcareaRw']) if (r.get('prtcareaRw') or '').replace('.', '', 1).isdigit() else None, 'ref': r.get('referenceDate')})
    for r in J('park'):
        la, lo = f6(r.get('latitude')), f6(r.get('longitude')); gu = gu_of(la, lo)
        if gu: S[gu]['items']['park'].append([la, lo, r.get('prkplceNm'), r.get('rdnmadr') or r.get('lnmadr'), r.get('prkplceSe'), r.get('prkplceType'), r.get('prkcmprt'), (r.get('weekdayOperOpenHhmm') or '') + '~' + (r.get('weekdayOperColseHhmm') or ''), r.get('parkingchrgeInfo'), (r.get('referenceDate') or '').replace('-', '')])
    for r in J('tl'):
        la, lo = f6(r.get('latitude')), f6(r.get('longitude')); gu = gu_of(la, lo)
        if gu: S[gu]['items']['tl'].append([la, lo, r.get('roadRouteNm'), r.get('rdnmadr') or r.get('lnmadr'), r.get('tfclghtSe'), r.get('sgnaspOrdr'), r.get('sgnaspTime'), r.get('remndrIdctYn'), r.get('sondSgngnrYn'), r.get('institutionNm'), r.get('referenceDate')])
    SK = {'초등학교': '초', '중학교': '중', '고등학교': '고'}
    for r in J('school'):
        if r.get('operSttus') and r['operSttus'] != '운영': continue
        la, lo = f6(r.get('latitude')), f6(r.get('longitude')); gu = gu_of(la, lo)
        if gu: E[gu]['edu'].append([la, lo, r.get('schoolNm'), SK.get(r.get('schoolSe'), r.get('schoolSe') or ''), '표준데이터'])
    SIDX = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8')); aca_i = {i for i, c in enumerate(SIDX['cls']) if c[-1] == 'P10501'}
    nS = nF = 0; gb = collections.defaultdict(dict)
    for gu in sorted(known):
        sd = gu[:2]; sp = os.path.join(R, gu, 'safety.json'); fp = os.path.join(R, gu, 'fac.json')
        if sd in ('11', '41'):
            if not os.path.exists(sp): continue
            v = json.load(open(sp, encoding='utf-8')); v.setdefault('items', {})['tl'] = S[gu]['items']['tl']; v.setdefault('source', {})['tl'] = SRC['tl']
            if sd == '11' and 'park' not in v['items']: v['items']['park'] = S[gu]['items']['park']; v['source']['park'] = SRC['park']
        else:
            v = {'schema': 'tg-rsafe/1', 'gu': gu, 'baked': time.strftime('%Y-%m-%d'), 'cam': S[gu]['cam'], 'sz': S[gu]['sz'], 'items': dict(S[gu]['items']), 'source': {k: SRC[k] for k in ('cam', 'sz', 'park', 'tl')}}
            v['source']['items'] = '공공데이터포털 전국 표준데이터 — park 주차장 · tl 신호등'
            # 학교·학원 점만 담은 fac.json(서울·경기의 동별 추이·어린이집·경로당은 다른 시도 공개 자료가 없어 비움)
            aca = []
            try:
                st = json.load(open(os.path.join(R, gu, 'stores.json'), encoding='utf-8')); O, Kk = st['o'], st['k']
                aca = [[round(O[1] + q[1] / Kk[1], 6), round(O[0] + q[0] / Kk[0], 6), q[4]] for q in st['pts'] if q[2] in aca_i]
            except Exception: pass
            fd = {'schema': 'tg-fac/1', 'gu': gu, 'name': next(x['name'] for x in IX['gus'] if x['gu'] == gu), 'sido': sd, 'dong': {}, 'pts': {'edu': E[gu]['edu'], 'aca': aca},
                  'source': {'학교': SRC['school'], '학원': '소상공인시장진흥공단 상가(상권)정보 — 입시·교과학원(P10501)', '비고': '어린이집·유치원·경로당·관공서와 동별 추이는 이 시도 공개 자료를 아직 못 받아 비움'}}
            json.dump(fd, open(fp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu]['fac'] = os.path.getsize(fp); nF += 1
        json.dump(v, open(sp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu]['safety'] = os.path.getsize(sp); nS += 1
    for x in IX['gus']:
        for k, b in gb.get(x['gu'], {}).items(): x.setdefault('bytes', {})[k] = b
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    tot = lambda k: sum(len(S[g][k]) for g in S); ti = lambda k: sum(len(S[g]['items'][k]) for g in S)
    print('safety', nS, 'fac(새로)', nF, '카메라', tot('cam'), '보호구역', tot('sz'), '주차장', ti('park'), '신호등', ti('tl'), '학교', sum(len(E[g]['edu']) for g in E))

if __name__ == '__main__': fetch() if sys.argv[1:] == ['fetch'] else build()
