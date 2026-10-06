# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.50.0 — 📋 동 현황 전국판(소유자 「서울에서 나오는 내용이 전국에서 다 나와야」 「받아」 2026-10-06)
#   원자료 07_API키/out/natfac/
#     cc/cc_<시도>.xls — 어린이집정보공개포털 「어린이집 기본정보」(정기 2026-09 말일 · 시도마다 · 좌표·정원·현원 · 인가일) — 운영 중(정상·재개)만
#     kg/kg_general_20261.csv — 교육부 유치원알리미 공시 「일반 현황」 2026년 1차(전체 시도 · 좌표·설립유형·정원·원아수) — 대표자·원장 이름은 받는 자리에서 버린다
#     kosis_DT_1KI1511.json · kosis_DT_2KI2011.json — 통계청 경제총조사 읍·면·동별/산업대분류별 총괄(2015 · 2020 · 사업체수·종사자수·매출액)
#   서울·경기는 fac-bake.py 가 만든 동 기록(어린이집 해마다·유치원 해마다·사업체 10년)을 그대로 두고, 빈 칸만 채운다(유치원 원아수 · 경제총조사)
#   그 밖 시도는 동 기록을 새로 만든다: 남녀(dong.json) · 어린이집 · 유치원 · 사업체(2015→2020)
#   py -3.12 -X utf8 tools/region/natfac-bake.py
import json, os, csv, glob, collections, xlrd
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); SRC = os.path.join(KB, '07_API키', 'out', 'natfac'); R = os.path.join(ROOT, 'data', 'r')
HJD = os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson')
feats = json.load(open(HJD, encoding='utf-8'))['features']; geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms)
def dong_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return feats[i]['properties']
    return None
NAME = {f['properties']['adm_cd2'][:8]: f['properties']['adm_nm'].split(' ')[-1] for f in feats}
A7 = {f['properties']['adm_cd'][:7]: f['properties']['adm_cd2'][:8] for f in feats if f['properties'].get('adm_cd')}
D = collections.defaultdict(dict); PTS = collections.defaultdict(lambda: collections.defaultdict(list)); cnt = collections.Counter()
def num(x):
    try: return int(float(str(x).replace(',', '')))
    except (TypeError, ValueError): return 0
# 어린이집
for f in sorted(glob.glob(os.path.join(SRC, 'cc', 'cc_*.xls'))):
    s = xlrd.open_workbook(f).sheet_by_index(0); H = s.row_values(0); ix = {h: i for i, h in enumerate(H)}
    for r in range(1, s.nrows):
        v = s.row_values(r); st = v[ix['운영현황']]
        if st not in ('정상', '재개'): continue
        try: lat, lon = float(v[ix['위도']]), float(v[ix['경도']])
        except (TypeError, ValueError): cnt['어린이집 좌표 없음'] += 1; continue
        p = dong_of(lon, lat)
        if not p: cnt['어린이집 경계 밖'] += 1; continue
        k = p['adm_cd2'][:8]; cap, cur = num(v[ix['정원수']]), num(v[ix['현원수']])
        c = D[k].setdefault('cc', [0, 0, 0]); c[0] += 1; c[1] += cap; c[2] += cur
        PTS[p['sgg']]['cc'].append([round(lat, 6), round(lon, 6), v[ix['어린이집명']], v[ix['어린이집유형구분']], cap, cur]); cnt['어린이집'] += 1
# 유치원(이름이 든 칸 중 대표자·원장은 읽지 않는다)
for r in csv.DictReader(open(os.path.join(SRC, 'kg', 'kg_general_20261.csv'), encoding='utf-8-sig')):
    try: lat, lon = float(r['위도']), float(r['경도'])
    except (TypeError, ValueError): cnt['유치원 좌표 없음'] += 1; continue
    p = dong_of(lon, lat)
    if not p: cnt['유치원 경계 밖'] += 1; continue
    k = p['adm_cd2'][:8]; cap = num(r['인가총정원수']); kids = sum(num(r[x]) for x in ('만3세원아수', '만4세원아수', '만5세원아수', '혼합원아수', '특수원아수'))
    g = D[k].setdefault('kgc', [0, 0, 0]); g[0] += 1; g[1] += cap; g[2] += kids
    PTS[p['sgg']]['kg2'].append([round(lat, 6), round(lon, 6), r['유치원명'], r['설립유형'], cap, kids]); cnt['유치원'] += 1
# 경제총조사(2015 · 2020) — 통계청 읍면동 7자리 = 행정동 adm_cd 앞 7자리
import re
def nz(x): return re.sub(r'[\s·.ㆍ,()\-]', '', str(x or ''))
def nzj(x): return re.sub(r'제(\d)', chr(92) + '1', nz(x))
def sg(sd):
    t = nz(sd)
    for a, b in (('광주', 'JN'), ('전라남', 'JN'), ('전남', 'JN'), ('강원', 'GW'), ('전라북', 'JB'), ('전북', 'JB'), ('제주', 'JJ'), ('세종', 'SJ'), ('경상북', 'GB'), ('경북', 'GB'), ('경상남', 'GN'), ('경남', 'GN'), ('충청북', 'CB'), ('충북', 'CB'), ('충청남', 'CN'), ('충남', 'CN')):
        if t.startswith(a): return b
    return t[:2]
IDX = collections.defaultdict(list)
for f in feats:
    pr = f['properties']; dn = pr['adm_nm'].split(' ')[-1]
    for q in {nz(dn), nzj(dn)}: IDX[(sg(pr['sidonm']), q)].append((pr['adm_cd2'][:8], nz(pr['sggnm'])))
def find(sd, sgg, dong):
    L = IDX.get((sg(sd), nz(dong))) or IDX.get((sg(sd), nzj(dong)), [])
    L = list(dict.fromkeys(L))
    if len(L) == 1: return L[0][0]
    s2 = nz(sgg); M = [x for x in L if x[1] == s2 or x[1].startswith(s2) or s2.startswith(x[1]) or (s2 and s2 in x[1])]
    return M[0][0] if len(M) == 1 else None
BZ = collections.defaultdict(lambda: collections.defaultdict(dict)); INM = {}
for tbl, yr in (('DT_1KI1511', '2015'), ('DT_2KI2011', '2020')):
    RR = json.load(open(os.path.join(SRC, 'kosis_%s.json' % tbl), encoding='utf-8')); KN = {r['C1']: r['C1_NM'] for r in RR}
    for r in RR:
        c = r['C1']
        if len(c) != 7: continue
        k = A7.get(c) or find(KN.get(c[:2], ''), KN.get(c[:5], ''), r['C1_NM'])
        if not k: cnt['사업체 못 맞춤 ' + yr] += 1; continue
        a = r['C2']; INM[a] = r['C2_NM'].split('(')[0].strip()
        BZ[k][(yr, a)][r['ITM_ID']] = num(r['DT'])
for k, v in BZ.items():
    bz = []
    for yr in ('2015', '2020'):
        t = v.get((yr, '0'))
        if t: bz.append([yr, t.get('T10', 0), t.get('T20', 0), t.get('T30', 0)])
    if bz: D[k]['bz5'] = bz
    bzi = [[INM[a], v.get(('2015', a), {}).get('T10', 0), v.get(('2020', a), {}).get('T10', 0)] for a in INM if a != '0' and (('2015', a) in v or ('2020', a) in v)]
    if bzi: D[k]['bzi5'] = sorted(bzi, key=lambda x: -x[2])
# 관공서(서울·경기 밖) — 주민센터 = 행정안전부 읍면동 하부행정기관 현황(동 이름) · 우체국 = 우정사업본부 전국 우체국 현황(주소의 법정동 → 행정동 근사)
GUBY = {}
for f in feats:
    pr = f['properties']; GUBY.setdefault((sg(pr['sidonm']), nz(pr['sggnm'])), pr['sgg'])
def gu_of(addr):
    t = addr.split()
    if len(t) < 3: return None
    for cand in (t[1] + t[2], t[1]):
        g = GUBY.get((sg(t[0]), nz(cand)))
        if g: return g
    return None
import glob as _g
for r in csv.DictReader(open(_g.glob(os.path.join(SRC, '*읍면동 하부행정기관*.csv'))[0], encoding='utf-8-sig')):
    nm = re.sub(r'\s*(행정복지센터|주민센터|사무소)$', '', r['읍면동'].strip()); k = find(r['시도'], r['시군구'], nm)
    if k: D[k].setdefault('gov', {})['주민센터'] = 1; cnt['주민센터'] += 1
    else: cnt['주민센터 못 맞춤'] += 1
SHB = {}
for fn in _g.glob(os.path.join(R, '*', 'shd.json')):
    J = json.load(open(fn, encoding='utf-8'))
    for u, v in J['b2h'].items(): SHB[(J['gu'], u)] = max(v, key=v.get)
for r in csv.DictReader(open(_g.glob(os.path.join(SRC, '*우체국 현황*.csv'))[0], encoding='utf-8-sig')):
    ad = (r.get(' 주소(도로명) ') or r.get('주소(도로명)') or '').strip(); g = gu_of(ad); m = re.search(r'\(([^,)]+)', ad)
    em = next((w for w in ad.split()[2:5] if re.search('[읍면]$', w)), None)
    if g and em:
        k = next((f['properties']['adm_cd2'][:8] for f in feats if f['properties']['sgg'] == g and f['properties']['adm_nm'].split(' ')[-1] == em), None)
        if k: g2 = D[k].setdefault('gov', {}); g2['우체국'] = g2.get('우체국', 0) + 1; cnt['우체국'] += 1; continue
    if not g or not m: cnt['우체국 못 맞춤'] += 1; continue
    bd = m.group(1).strip(); k = SHB.get((g, bd))
    if not k:
        st = re.sub(r'[0-9.·]*(동|가|리)$', '', bd); C = [f['properties']['adm_cd2'][:8] for f in feats if f['properties']['sgg'] == g and nz(f['properties']['adm_nm'].split(' ')[-1]).startswith(st)]
        k = C[0] if len(C) == 1 else None
    if k: g2 = D[k].setdefault('gov', {}); g2['우체국'] = g2.get('우체국', 0) + 1; cnt['우체국'] += 1
    else: cnt['우체국 못 맞춤'] += 1
SRCS = {'관공서(전국)': '주민센터 = 행정안전부 읍면동 하부행정기관 현황(2025-12-31) · 우체국 = 우정사업본부 전국 우체국 현황(2026-08-31 · 주소의 법정동으로 행정동 근사)', '어린이집(전국)': '어린이집정보공개포털 「어린이집 기본정보」(정기 2026-09 말일 · 운영 중 · 좌표로 행정동)', '유치원(전국)': '교육부 유치원알리미 공시 「일반 현황」 2026년 1차(국·공·사립 전체 · 좌표로 행정동)', '사업체(경제총조사)': '통계청 경제총조사 읍·면·동별/산업대분류별 총괄(KOSIS DT_1KI1511 · DT_2KI2011 — 2015 · 2020 · 5년마다)'}
# v2.69.0 전국 경로당 — 공공데이터포털 15114136 「전국마을회관및경로당표준데이터」(2026-10-07 받음 · 07_API키/out/natfac/kyr/) · 영업만 · 좌표로 행정동
#   서울·경기도 이것으로 바꾼다(종전 = 서울 주소 맞춤 79% · 경기 OSM). 경로당 = 시설유형 「경로당」·「마을회관및경로당」 · 「마을회관」만인 곳은 따로 센다(vh)
KF = sorted(_g.glob(os.path.join(SRC, 'kyr', 'tn_pubr_public_vill_hall_sen_cent_svc_*.csv'))); KYR = collections.defaultdict(list); KYRD = collections.Counter(); KVH = collections.Counter(); KYRDATE = ''
if KF:
    for r in csv.DictReader(open(KF[-1], encoding='utf-8-sig')):
        if (r['BUSI_COD_NM'] or '').strip() != '영업': cnt['경로당 폐업·휴업'] += 1; continue
        try: lat, lon = float(r['LAT']), float(r['LOT'])
        except ValueError: cnt['경로당 좌표 없음'] += 1; continue
        p = dong_of(lon, lat)
        if not p: cnt['경로당 동 밖'] += 1; continue
        k8 = p['adm_cd2'][:8]; t = (r['FLCT_TYP'] or '').strip(); KYRDATE = max(KYRDATE, r['CRTR_YMD'] or '')
        if '경로당' in t:
            KYRD[k8] += 1; cnt['경로당'] += 1
            KYR[p['sgg']].append([round(lat, 6), round(lon, 6), (r['FLCT_NM'] or '').strip(), (r['LCTN_ROAD_NM_ADDR'] or r['LCTN_LOTNO_ADDR'] or '').strip(), '표준데이터', t, (r['BUIL_YMD'] or '')[:4], round(num(r['BUIL_AREA']))])
        else: KVH[k8] += 1; cnt['마을회관'] += 1
    SRCS['경로당'] = '공공데이터포털 전국마을회관및경로당표준데이터(15114136 · 지자체 등록 · 데이터기준일 ~' + KYRDATE + ' · 받은 날 2026-10-07 · 운영 중만 · 좌표로 행정동)'
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); upd = 0
for g in IX['gus']:
    gu = g['gu']; fn = os.path.join(R, gu, 'fac.json')
    if not os.path.exists(fn): continue
    doc = json.load(open(fn, encoding='utf-8')); doc.setdefault('source', {}).update(SRCS); seoul_gg = gu[:2] in ('11', '41'); DD = doc.setdefault('dong', {})
    dj = os.path.join(R, gu, 'dong.json'); dn = json.load(open(dj, encoding='utf-8'))['dong'] if os.path.exists(dj) else []
    for q in dn:
        k = q.get('k')
        if not k: continue
        x = DD.setdefault(k, {}); x.setdefault('name', q['name']); v = D.get(k, {}); p = q.get('pop') or {}
        if 'sex' not in x and p.get('mage'): x['sex'] = [p['m'], p['f'], p['mage'], p['fage']]
        if 'kgc' in v: x['kgc'] = v['kgc']
        if KF:
            if KYRD.get(k): x['kyr'] = KYRD[k]
            else: x.pop('kyr', None)
            if KVH.get(k): x['vh'] = KVH[k]
            else: x.pop('vh', None)
        if not seoul_gg:
            if 'cc' in v: x['cc'] = v['cc']
            if 'gov' in v and 'gov' not in x: x['gov'] = v['gov']
            if 'bz5' in v: x['bz'] = v['bz5']; x['bzi'] = v.get('bzi5', []); x['bziy'] = ['2015', '2020']; x['bzsrc'] = SRCS['사업체(경제총조사)']
        if seoul_gg and gu[:2] == '41' and 'cc' in v and (x.get('cc') or [0, 0, -1])[2] < 0: x['cc'] = v['cc']   # 경기 어린이집 자료엔 현원이 없다(-1) — 전국 어린이집 기본정보(현원 있음)로
        elif 'bz' not in x and 'bz5' in v: x['bz'] = v['bz5']; x['bzi'] = v.get('bzi5', []); x['bziy'] = ['2015', '2020']; x['bzsrc'] = SRCS['사업체(경제총조사)']
    pts = doc.setdefault('pts', {})
    if not seoul_gg and PTS[gu]['cc']: pts['cc'] = PTS[gu]['cc']
    if PTS[gu]['kg2']: pts['kg2'] = PTS[gu]['kg2']
    if not seoul_gg and PTS[gu]['kg2']: pts['kg'] = PTS[gu]['kg2']
    doc['natkg'] = '2026-1'
    if KF: pts['kyr'] = KYR[gu]; doc['kyrNo'] = 0; doc['kyrnat'] = KYRDATE
    json.dump(doc, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); g.setdefault('bytes', {})['fac'] = os.path.getsize(fn); upd += 1
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', upd, dict(cnt), '동 사업체', len(BZ))
