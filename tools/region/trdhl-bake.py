# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.1.0 — 서울 골목상권의 「상권배후지」(본체와 나눈 수요 쪽)
#   py -3.12 -X utf8 tools/region/trdhl-bake.py fetch  → 07_API키/out/region/trdhl_*.json (받은 것은 건너뛴다)
#   py -3.12 -X utf8 tools/region/trdhl-bake.py build  → data/r/<구>/trdhl.json · r/index.json bytes.trdhl
# 서울시 상권분석서비스(서울 열린데이터광장) — 영역-상권배후지(OA-22159 · 07_API키/out/seoul_trdhl/trdhl.shp · EPSG:5181 · 골목상권 1,071곳만 있다)
#   추정매출 VwsmTrdhlSelngQq · 상주인구(가구·아파트/비아파트) VwsmTrdhlRepopQq · 길단위인구 VwsmTrdhlFlpopQq · 아파트 VwsmTrdhlAptQq ·
#   소비(소득·지출) VwsmTrdhlNcmCnsmpQq · 점포 VwsmTrdhlStorQq · 집객시설 VwsmTrdhlFcltyQq
#   ⚠ 직장인구-상권배후지(VwsmTrdhlWrcPopltnQq)·상권변화지표-배후지는 2026-10-04 에 서버 오류(ERROR-500)라 넣지 못했다.
# 키는 07_API키/keys.json 에서만(flow-bake.seoul).
import json, os, sys, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(KB, 'out', 'region')
SHP = os.path.join(KB, 'out', 'seoul_trdhl', 'trdhl')
spec = importlib.util.spec_from_file_location('tb', os.path.join(ROOT, 'tools', 'trdar-bake.py')); tb = importlib.util.module_from_spec(spec); spec.loader.exec_module(tb)
seoul, ind_row, latest = tb.seoul, tb.ind_row, tb.latest
TB, AG, DW, M = tb.TB, tb.AG, tb.DW, tb.M
spec2 = importlib.util.spec_from_file_location('tr', os.path.join(ROOT, 'tools', 'region', 'trdar-bake.py')); tr2 = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(tr2)
FC = tr2.FC
g = lambda r, k: round(r.get(k) or 0)

def jget(n):
    p = os.path.join(OUT, n); return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
def jput(n, o): open(os.path.join(OUT, n), 'w', encoding='utf-8').write(json.dumps(o, ensure_ascii=False, separators=(',', ':')))

def allrows(svc, q=''):   # 분기 인자를 무시하는 서비스가 있다 — 전부 받아 상권마다 가장 최근 분기를 쓴다
    out, st = [], 1
    while True:
        v = seoul('json/%s/%d/%d/%s' % (svc, st, st + 999, q)).get(svc) or {}
        rr = v.get('row') or []; tot = v.get('list_total_count') or 0
        out += rr; st += 1000
        if st > tot or not rr: break
    return out

def newest(rows, f):
    best = {}
    for r in rows:
        cd, q = r['TRDAR_CD'], r['STDR_YYQU_CD']
        v = f(r)
        if not any(x for x in v if isinstance(x, (int, float))): continue   # 빈 분기(값이 모두 0)는 건너뛴다 — 소비-배후지 최근 분기가 비어 있었다
        if cd not in best or q > best[cd][0]: best[cd] = (q, v)
    return best

ONE = {
    'rep': ('VwsmTrdhlRepopQq', lambda r: [g(r, 'TOT_REPOP_CO'), g(r, 'ML_REPOP_CO'), g(r, 'FML_REPOP_CO')] + [g(r, 'AGRDE_%s_REPOP_CO' % a) for a in AG] + [g(r, 'TOT_HSHLD_CO'), g(r, 'APT_HSHLD_CO'), g(r, 'NON_APT_HSHLD_CO')]),
    'flp': ('VwsmTrdhlFlpopQq', lambda r: [g(r, 'TOT_FLPOP_CO'), g(r, 'ML_FLPOP_CO'), g(r, 'FML_FLPOP_CO')] + [g(r, 'AGRDE_%s_FLPOP_CO' % a) for a in AG] + [g(r, 'TMZON_%s_FLPOP_CO' % x) for x in TB] + [g(r, '%s_FLPOP_CO' % d) for d in DW]),
    'apt': ('VwsmTrdhlAptQq', lambda r: [g(r, 'APT_HSMP_CO')] + [g(r, k) for k in ('AE_66_SQMT_BELO_HSHLD_CO', 'AE_66_SQMT_HSHLD_CO', 'AE_99_SQMT_HSHLD_CO', 'AE_132_SQMT_HSHLD_CO', 'AE_165_SQMT_HSHLD_CO')] +
            [g(r, 'PC_%s_HSHLD_CO' % k) for k in ('1_HDMIL_BELO', '1_HDMIL', '2_HDMIL', '3_HDMIL', '4_HDMIL', '5_HDMIL', '6_HDMIL_ABOVE')] + [g(r, 'AVRG_AE'), round((r.get('AVRG_MKTC') or 0) / M)]),
    'ncm': ('VwsmTrdhlNcmCnsmpQq', lambda r: [round((r.get(k) or 0) / M) for k in ('EXPNDTR_TOTAMT', 'FDSTFFS_EXPNDTR_TOTAMT', 'CLTHS_FTWR_EXPNDTR_TOTAMT', 'LVSPL_EXPNDTR_TOTAMT', 'MCP_EXPNDTR_TOTAMT', 'TRNSPORT_EXPNDTR_TOTAMT', 'LSR_EXPNDTR_TOTAMT', 'CLTUR_EXPNDTR_TOTAMT', 'EDC_EXPNDTR_TOTAMT', 'PLESR_EXPNDTR_TOTAMT')] +
            [round((r.get('MT_AVRG_INCOME_AMT') or 0) / M), r.get('INCOME_SCTN_CD') or '']),
    'fac': ('VwsmTrdhlFcltyQq', lambda r: [g(r, k) for k, _ in FC]),
}

def fetch():
    q = latest('VwsmTrdhlSelngQq'); print('quarter', q)
    if not jget('trdhl_selng_%s.json' % q):
        d = {}
        for r in allrows('VwsmTrdhlSelngQq', q):
            if r.get('STDR_YYQU_CD') == q: d.setdefault(r['TRDAR_CD'], []).append([r['SVC_INDUTY_CD']] + ind_row(r))
        jput('trdhl_selng_%s.json' % q, d); print('selng', len(d))
    if not jget('trdhl_stor_%s.json' % q):
        d = {}
        for r in allrows('VwsmTrdhlStorQq', q):
            if r.get('STDR_YYQU_CD') == q: d.setdefault(r['TRDAR_CD'], []).append([r['SVC_INDUTY_CD_NM'], g(r, 'STOR_CO'), g(r, 'FRC_STOR_CO'), g(r, 'OPBIZ_STOR_CO'), g(r, 'CLSBIZ_STOR_CO'), g(r, 'SIMILR_INDUTY_STOR_CO')])
        jput('trdhl_stor_%s.json' % q, d); print('stor', len(d))
    for k, (svc, f) in ONE.items():
        nm = 'trdhl_%s.json' % k
        if jget(nm): continue
        rows = allrows(svc)
        if rows: print(k, 'fields', [x for x in rows[0].keys()][:6], '…', len(rows))
        b = newest(rows, f)
        jput(nm, {'q': max([v[0] for v in b.values()] or ['']), 'd': {cd: v[1] for cd, v in b.items()}, 'qs': {cd: v[0] for cd, v in b.items()}}); print(k, len(b))

def build():
    import shapefile
    from shapely.geometry import shape
    from shapely.ops import transform
    from pyproj import Transformer
    tr = Transformer.from_crs('EPSG:5181', 'EPSG:4326', always_xy=True)
    sel = sorted(f for f in os.listdir(OUT) if f.startswith('trdhl_selng_'))[-1]; q = sel[12:17]
    S, ST = jget(sel), jget('trdhl_stor_%s.json' % q) or {}
    O = {k: jget('trdhl_%s.json' % k) or {'q': '', 'd': {}} for k in ONE}
    rd = shapefile.Reader(SHP, encoding='utf-8'); byGu = {}
    for sr in rd.shapeRecords():
        rec = sr.record; cd = rec[0]
        gm = shape(sr.shape.__geo_interface__)
        gs = transform(lambda x, y, z=None: tr.transform(x, y), gm.simplify(3.0))
        polys = [gs] if gs.geom_type == 'Polygon' else list(gs.geoms)
        t = {'cd': cd, 'name': rec[1], 'gu': rec[4], 'dong': rec[7], 'area': rec[8],
             'rings': [[[round(x, 6), round(y, 6)] for x, y in pg.exterior.coords][:-1] for pg in polys]}
        if cd in S: t['ind'] = [r[1:] for r in S[cd]]
        if cd in ST: t['stor'] = [s for s in ST[cd] if s[1] or s[3] or s[4]]
        for k in ONE:
            if cd in O[k]['d']: t[k] = O[k]['d'][cd]
        byGu.setdefault(rec[4], []).append(t)
    src = ('서울시 상권분석서비스(서울 열린데이터광장) — 영역-상권배후지(OA-22159) · 추정매출-상권배후지 %s(카드 결제 추정) · 점포 %s · 상주인구(%s) · 길단위인구(%s) · 아파트(%s) · 소비(%s) · 집객시설(%s)'
           % (q, q, O['rep']['q'], O['flp']['q'], O['apt']['q'], O['ncm']['q'], O['fac']['q']))
    fields = {'ind': '상권 파일과 같음(매출 만원)', 'rep': '[계, 남, 여, 연령 6, 가구, 아파트 가구, 비아파트 가구] 상주인구', 'flp': '[계, 남, 여, 연령 6, 시간대 6, 요일 7] 분기 유동인구',
              'apt': '[단지 수, 면적별 가구 5(66㎡ 미만·66·99·132·165㎡ 이상), 시가별 가구 7(1억 미만·1억대…6억 이상), 평균 면적(㎡), 평균 시가(만원)]',
              'ncm': '[지출 총액, 식료품, 의류·신발, 생활용품, 의료비, 교통, 여가, 문화, 교육, 유흥 (만원), 월평균 소득(만원), 소득 구간 코드]',
              'stor': '[업종, 점포, 프랜차이즈, 개업, 폐업, 유사업종 포함 점포]', 'fac': [n for _, n in FC]}
    note = ('상권배후지 = 골목상권 본체 둘레에서 그 상권을 이용한다고 보는 주거·생활 구역(서울시 상권분석서비스가 그은 경계 · 골목상권에만 있다). '
            '본체와 배후지를 나눠 보면 수요의 성격이 보인다 — 매출은 본체, 가구는 배후지에 많으면 주거 수요다. 매출은 카드 결제 추정(현금 제외)이고 법인 카드 매출은 연령·성별이 없다. '
            '직장인구-배후지는 열린데이터광장 서버 오류(2026-10-04)로 넣지 못했다. 3년 생존율은 우리마을가게 화면에만 있고 공개 자료(API·파일)에 없다.')
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for gu, items in byGu.items():
        fn = os.path.join(ROOT, 'data', 'r', gu, 'trdhl.json')
        if not os.path.isdir(os.path.dirname(fn)): continue
        json.dump({'schema': 'tg-trdhl/1', 'gu': gu, 'quarter': q, 'qs': {k: O[k]['q'] for k in ONE}, 'source': src, 'note': note, 'fields': fields, 'trdhl': items},
                  open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        gb[gu] = os.path.getsize(fn)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['trdhl'] = gb[g2['gu']]
    R['layers']['trdhl'] = '서울 골목상권 배후지(영역·매출·상주·가구·아파트·소비·유동·점포)'
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('quarter', q, 'items', sum(len(v) for v in byGu.values()), 'gus', len(gb), 'bytes', sum(gb.values()))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
