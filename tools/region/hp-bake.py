# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.72.0 — 🏢 공동주택 공시가격(국토교통부 「주택 공시가격 정보」 2025 · 1월 1일 정기공시 · 단지·동·호 전부)
#   원자료: NAS \\NAS-baranno815\home\국토교통부_주택 공시가격 정보_20250626.zip (CSV 3.46GB · UTF-8) — 소유자 2026-10-07 전달
#   → data/r/<구>/hp.json
#     bjd = {법정동 10자리: [이름, 호수, 공시가격 가운데(만 원), ㎡당 가운데(만 원), 가격 띠 9칸 호수, 전용면적 6칸 호수, [이 법정동이 걸친 행정동 8자리…]]}
#     pnu = {필지 19자리: [단지명, 호수, [[전용면적, 호수, 최저, 가운데, 최고](만 원) …]]} — 세금 계산이 브이월드 키 없이도 쓰는 값
#   동·호 하나하나는 굽지 않는다(필지·면적마다 모아 최저·가운데·최고만).
#   행정동 잇기: 서울·경기 = data/b2a.json(법정동 경계 × 행정동 경계 넓이) · 그 밖 = 이름(○○동 ↔ ○○1동·○○2동 …) — 근사
#   2026-10-10: 2026년 정기공시 파일(공공데이터포털 3073746 「국토교통부_주택 공시가격 정보_20260101」 · 2026-10-01 등록 · 15,851,336건 · SHA-256 BBDFE3E1…BDD27DA 대조)로 갈았다 — 07_API키/out/hp2026/hp2026.zip
#   py -3.12 -X utf8 tools/region/hp-bake.py [zip 경로]   (기준연도는 파일의 「기준연도」 칸에서 읽는다 · 굽고 나면 ptax-bake.py 도 다시)
import zipfile, io, csv, json, os, re, collections, array, statistics, time, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
ZIP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'hp2026', 'hp2026.zip')   # 2025 판 = //NAS-baranno815/home/국토교통부_주택 공시가격 정보_20250626.zip
YEAR = None
BANDS = [10000, 30000, 60000, 90000, 120000, 150000, 200000, 300000]   # 만 원 — 1억·3억·6억·9억·12억·15억·20억·30억
AREAS = [40, 60, 85, 102, 135]
ix = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); GUS = {g['gu']: g['name'] for g in ix['gus']}
B2A = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a'] if 'b2a' in json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8')) else None
if B2A is None:
    j = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8')); B2A = {k: v for k, v in j.items() if isinstance(v, dict) and 'gu' in v}
    if not B2A: B2A = next(v for v in j.values() if isinstance(v, dict) and len(v) > 100)
N12 = {GUS[g].replace(' ', ''): g for g in GUS if g.startswith('12')}
def base(nm): return re.sub(r'(제?\d+(·\d+)*(가)?)?동$', '', re.sub(r'\s', '', nm))
DONGS = {}
for g in GUS:
    p = os.path.join(R, g, 'dong.json')
    if os.path.exists(p): DONGS[g] = [(d['k'], d['name']) for d in json.load(open(p, encoding='utf-8'))['dong'] if d.get('k')]
BN = collections.defaultdict(set); DN = collections.defaultdict(set)   # 2026 구 개편(화성 4구 · 인천 제물포·영종·서해·검단) — 2025 공시는 옛 코드라 법정동·읍면 이름으로 새 구를 찾는다
for b8, v in B2A.items(): BN[(v['gu'][:2], base(v['n']))].add(v['gu'])
for g, L in DONGS.items():
    for k, n2 in L: DN[(g[:2], base(n2))].add(g)
def gu_of(bjd, sido, sgg, em='', dr=''):
    b = B2A.get(bjd[:8])
    if b: return b['gu']
    g = bjd[:5]
    if g in GUS: return g
    if sido in ('광주광역시', '전라남도'): return N12.get(sgg)
    key = base(em or dr)
    for T in (BN, DN):
        c = T.get((bjd[:2], key))
        if c and len(c) == 1: return next(iter(c))
    return None
def bpos(v, B):
    for i, x in enumerate(B):
        if v < x: return i
    return len(B)
PN = collections.defaultdict(lambda: array.array('i'))   # (gu, pnu, 면적) → 가격들
PNM = {}
BJ = collections.defaultdict(lambda: array.array('i')); BJM = collections.defaultdict(lambda: array.array('f'))
BJB = collections.defaultdict(lambda: [0] * (len(BANDS) + 1)); BJA = collections.defaultdict(lambda: [0] * (len(AREAS) + 1)); BJN = {}
cnt = collections.Counter(); t0 = time.time()
z = zipfile.ZipFile(ZIP)
inf = next(i for i in z.infolist() if i.file_size > 1e9)
with z.open(inf) as f:
    rd = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
    hd = next(rd); C = {h: i for i, h in enumerate(hd)}
    for n, r in enumerate(rd):
        if YEAR is None: YEAR = int(r[C['기준연도']])
        try:
            bjd = r[C['법정동코드']]; pr = int(float(r[C['공시가격']])) // 10000; ar = float(r[C['전용면적']] or 0)
        except (ValueError, IndexError): cnt['칸 오류'] += 1; continue
        if pr <= 0: cnt['가격 0'] += 1; continue
        gu = gu_of(bjd, r[C['시도']], r[C['시군구']], r[C['읍면']], r[C['동리']])
        if not gu: cnt['구 못 맞춤'] += 1; continue
        sp = '2' if r[C['특수지코드']] == '1' else '1'
        pnu = bjd + sp + ('%04d' % int(r[C['본번']] or 0)) + ('%04d' % int(r[C['부번']] or 0))
        k = (gu, pnu, round(ar, 1)); PN[k].append(pr)
        if (gu, pnu) not in PNM: PNM[(gu, pnu)] = r[C['단지명']].strip()
        kb = (gu, bjd); BJ[kb].append(pr)
        if ar > 0: BJM[kb].append(pr / ar)
        BJB[kb][bpos(pr, BANDS)] += 1; BJA[kb][bpos(ar, AREAS)] += 1
        if kb not in BJN: BJN[kb] = (r[C['읍면']] + ' ' + r[C['동리']]).strip()
        cnt['호'] += 1
        if n % 2000000 == 0: print(n, round(time.time() - t0), 's', flush=True)
print(dict(cnt))
# 행정동 잇기
OUT = collections.defaultdict(lambda: {'bjd': {}, 'pnu': {}})
for (gu, bjd), A in BJ.items():
    nm = BJN[(gu, bjd)]; b = B2A.get(bjd[:8]); ks = [a[0] for a in b['a'] if a[2] >= 10] if b else []
    if not ks:
        lb = base(nm.split(' ')[-1]); ks = [k for k, n2 in DONGS.get(gu, []) if base(n2) == lb]
    M = BJM[(gu, bjd)]
    OUT[gu]['bjd'][bjd] = [nm, len(A), int(statistics.median(A)), round(statistics.median(M), 1) if M else None, BJB[(gu, bjd)], BJA[(gu, bjd)], ks]
for (gu, pnu, ar), A in PN.items():
    e = OUT[gu]['pnu'].setdefault(pnu, [PNM[(gu, pnu)], 0, []]); e[1] += len(A); s = sorted(A); e[2].append([ar, len(s), s[0], s[len(s) // 2], s[-1]])
for gu, o in OUT.items():
    for e in o['pnu'].values(): e[2].sort()
    doc = {'schema': 'tg-hp/1', 'gu': gu, 'year': YEAR, 'source': '국토교통부 「주택 공시가격 정보」(%d년 1월 1일 정기공시 · 공동주택 단지·동·호 · 공공데이터포털) — 필지·전용면적마다 모아 최저·가운데·최고(만 원)' % YEAR, 'bands': BANDS, 'areas': AREAS,
           'note': '행정동 잇기는 서울·경기 = 법정동·행정동 경계 넓이(10% 넘는 것) · 그 밖 = 이름 근사 · 기준연도 = 파일의 「기준연도」 칸', 'bjd': o['bjd'], 'pnu': o['pnu']}
    p = os.path.join(R, gu, 'hp.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    g = next((x for x in ix['gus'] if x['gu'] == gu), None)
    if g is not None: g.setdefault('bytes', {})['hp'] = os.path.getsize(p)
json.dump(ix, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', len(OUT), '법정동', sum(len(o['bjd']) for o in OUT.values()), '필지', sum(len(o['pnu']) for o in OUT.values()), round(time.time() - t0), 's')
