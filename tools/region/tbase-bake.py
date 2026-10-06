# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.43.0 — 🧾 국세청 상업용건물·오피스텔 기준시가(2026-01-01 고시 · 공공데이터포털 3036455 · 이용허락 제한 없음)
#   원자료 07_API키/out/taxbase/상업용건물 및 오피스텔 기준시가(2026년 1월 1일 기준).xlsx(받은 zip 안 · 시트 5 · 약 249만 호)
#   칸 = 상가건물번호·상가종류(상가/오피스텔)·고시일자·법정동코드·특수지(일반지번/산)·번지·호·건물명·동·층구분·층·호·고시가격(㎡당 원)·전용면적·공유면적
#   → r/<시군구(법정동 코드 앞 5자리)>/tbase.json = {필지 열쇠(법정동10+산1/일반0+번지4+호4 = PNU 와 같은 꼴): [건물명, [[종류 0상가·1오피스텔, 전용㎡, 공유㎡, ㎡당 원, 호수, 층 최저, 층 최고], …]]}
#   같은 값(종류·면적·㎡당 가격)의 호는 묶어 센다 · 세무 화면은 필지(PNU)로 찾아 「기준시가 = ㎡당 가격 × (전용 + 공유)」(국세청 고시 방식)로 쓴다
#   py -3.12 -X utf8 tools/region/tbase-bake.py
import os, json, collections, openpyxl, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'taxbase', '상업용건물 및 오피스텔 기준시가(2026년 1월 1일 기준).xlsx')
t0 = time.time(); wb = openpyxl.load_workbook(SRC, read_only=True)
B = collections.defaultdict(lambda: ['', collections.Counter(), {}]); n = 0; bad = 0
def fl(x):
    try: return int(str(x).strip())
    except Exception: return None
for ws in wb.worksheets:
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i == 0: continue
        try:
            kind = 1 if str(r[1]).strip() == '오피스텔' else 0; ld = str(r[3]).strip(); sp = '1' if str(r[4]).strip().startswith('산') else '0'
            key = ld + ('2' if sp == '1' else '1') + str(r[5]).strip().zfill(4) + str(r[6]).strip().zfill(4)
            pr = int(r[12]); ex = round(float(r[13]), 2); co = round(float(r[14] or 0), 2)
        except Exception: bad += 1; continue
        b = B[key]; b[0] = b[0] or str(r[7] or '').strip(); k = (kind, ex, co, pr); b[1][k] += 1
        f = fl(r[10]); f = -f if f is not None and str(r[9]).startswith('지하') else f
        if f is not None: lo, hi = b[2].get(k, (f, f)); b[2][k] = (min(lo, f), max(hi, f))
        n += 1
    print(ws.title, n, round(time.time() - t0), flush=True)
G = collections.defaultdict(dict)
for key, (nm, cnt, fr) in B.items():
    G[key[:5]][key] = [nm, [[k[0], k[1], k[2], k[3], c, (fr.get(k) or (None, None))[0], (fr.get(k) or (None, None))[1]] for k, c in sorted(cnt.items(), key=lambda x: (x[0][0], x[0][1]))]]
R = os.path.join(ROOT, 'data', 'r'); tot = 0; miss = 0; sizes = {}
# 2026 행정체제 개편으로 폴더가 바뀐 곳(기준시가는 2026-01-01 옛 법정동 코드) → 새 시군구 폴더에 넣고 옛 법정동 이름(ld)을 같이 둔다 — 지도는 지번 + 법정동 이름으로 찾는다
NEWG = {'28110': ['28125', '28155'], '28140': ['28125'], '28260': ['28275', '28290']}
LDN = {}
for l in open(os.path.join(os.path.dirname(SRC), '법정동전체자료.csv'), encoding='cp949').read().splitlines()[1:]:
    c = l.split(','); LDN[c[0]] = c[1].split(' ')[-1]
EXTRA = collections.defaultdict(dict); LDX = collections.defaultdict(dict)
IXG = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8'))['gus']
for gu, d in list(G.items()):
    if os.path.isdir(os.path.join(R, gu)): continue
    tg = NEWG.get(gu) or sorted(x for x in os.listdir(R) if len(x) == 5 and x[:4] == gu[:4] and os.path.isdir(os.path.join(R, x)))
    if not tg and gu[:2] in ('29', '46'):   # 광주·전남 → 전남광주통합특별시(12) — 시군구 이름으로
        nm = LDN.get(gu + '00000', '').split(' ')[-1]; tg = [g['gu'] for g in IXG if g['gu'][:2] == '12' and g['name'] == nm][:1]
    for t in tg:
        EXTRA[t].update(d)
        for k in d: LDX[t][k[:10]] = LDN.get(k[:10], '')
    if not tg: miss += len(d)
for t, d in EXTRA.items(): G[t].update(d)
for gu, d in G.items():
    p = os.path.join(R, gu)
    if not os.path.isdir(p): continue
    doc = {'schema': 'tg-tbase/1', 'gu': gu, 'asof': '2026-01-01', 'source': '국세청 상업용건물·오피스텔 기준시가(2026-01-01 고시 · 공공데이터포털 3036455 · 이용허락 제한 없음)',
           'fields': 'b = {필지(PNU 꼴 19자리): [건물명, [[0 상가·1 오피스텔, 전용㎡, 공유㎡, ㎡당 고시가격(원), 같은 값 호수, 층 최저, 층 최고(지하 −)], …]]} · 기준시가 = ㎡당 고시가격 × (전용 + 공유) · ld = 옛 법정동 코드 → 이름(2026 개편 전 코드로 고시된 건물 — 지번 + 이름으로 찾는다)', 'b': d, 'ld': LDX.get(gu, {})}
    f = os.path.join(p, 'tbase.json'); json.dump(doc, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); sizes[gu] = os.path.getsize(f); tot += sizes[gu]
print('호', n, '못 읽음', bad, '건물', len(B), '시군구', len(sizes), round(tot / 1048576, 1), 'MB · 폴더 없는 시군구의 건물', miss)
