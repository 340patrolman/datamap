# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.2.0 — 📝 동 풀어 읽기의 「사는 사람의 지갑」: 서울시 상권분석서비스 행정동 3종(서울신용보증재단 · 서울 열린데이터광장 · http 만)
#   아파트-행정동 VwsmAdstrdAptW(단지 수 · 면적대별 가구 · 가격대별 가구 · 평균 면적 · 평균 시세)
#   소득소비-행정동 VwsmAdstrdNcmCnsmpW(지출 총액·항목별 — 월평균 소득·소득구간 칸은 서울시가 2026-05~06 지웠다 · 지출이 주거지 기준인지 결제지 기준인지 설명 없음)
#   직장인구-행정동 VwsmAdstrdWrcPopltnW(그 동에서 일하는 사람 성별·연령)
#   키 = 07_API키/keys.json "seoul" · 분기 = 서비스마다 가장 최근 분기
#   py -3.12 -X utf8 tools/region/dongw-bake.py fetch → 07_API키/out/region/dongw/<서비스>.json · build → data/r/<구>/dongw.json + data/area-ref.json 의 ref.서울.w
import json, os, sys, time, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'region', 'dongw')
SV = ['VwsmAdstrdAptW', 'VwsmAdstrdNcmCnsmpW', 'VwsmAdstrdWrcPopltnW']

def g(u):
    for a in range(4):
        try: return json.loads(urllib.request.urlopen(u, timeout=120).read().decode('utf-8'))
        except Exception as e: print('retry', e); time.sleep(3)
    return {}

def fetch():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['seoul']; k = (k if isinstance(k, str) else next(iter(k.values()))).strip(); os.makedirs(OUT, exist_ok=True)
    for sv in SV:
        rows, s = [], 1
        while True:
            j = g('http://openapi.seoul.go.kr:8088/%s/json/%s/%d/%d/' % (k, sv, s, s + 999)).get(sv) or {}
            r = j.get('row') or []; rows += r
            if len(r) < 1000: break
            s += 1000
        json.dump(rows, open(os.path.join(OUT, sv + '.json'), 'w', encoding='utf-8'), ensure_ascii=False); print(sv, len(rows))

def build():
    D = collections.defaultdict(dict); Q = {}
    for sv in SV:
        rows = json.load(open(os.path.join(OUT, sv + '.json'), encoding='utf-8')); q = max(r['STDR_YYQU_CD'] for r in rows); Q[sv] = q
        for r in rows:
            if r['STDR_YYQU_CD'] != q: continue
            cd = r['ADSTRD_CD']; f = lambda c: r.get(c) or 0
            if sv == 'VwsmAdstrdAptW':
                D[cd]['apt'] = [f('APT_HSMP_CO'), [f('AE_66_SQMT_BELO_HSHLD_CO'), f('AE_66_SQMT_HSHLD_CO'), f('AE_99_SQMT_HSHLD_CO'), f('AE_132_SQMT_HSHLD_CO'), f('AE_165_SQMT_HSHLD_CO')],
                                [f('PC_1_HDMIL_BELO_HSHLD_CO'), f('PC_1_HDMIL_HSHLD_CO'), f('PC_2_HDMIL_HSHLD_CO'), f('PC_3_HDMIL_HSHLD_CO'), f('PC_4_HDMIL_HSHLD_CO'), f('PC_5_HDMIL_HSHLD_CO'), f('PC_6_HDMIL_ABOVE_HSHLD_CO')], f('AVRG_AE'), round(f('AVRG_MKTC') / 1e4)]
            elif sv == 'VwsmAdstrdNcmCnsmpW':
                D[cd]['ncm'] = [round(f(c) / 1e4) for c in ('EXPNDTR_TOTAMT', 'FDSTFFS_EXPNDTR_TOTAMT', 'CLTHS_FTWR_EXPNDTR_TOTAMT', 'LVSPL_EXPNDTR_TOTAMT', 'MCP_EXPNDTR_TOTAMT', 'TRNSPORT_EXPNDTR_TOTAMT', 'EDC_EXPNDTR_TOTAMT', 'PLESR_EXPNDTR_TOTAMT', 'LSR_CLTUR_EXPNDTR_TOTAMT', 'ETC_EXPNDTR_TOTAMT', 'FD_EXPNDTR_TOTAMT')]
            else:
                D[cd]['wrc'] = [f('TOT_WRC_POPLTN_CO'), f('ML_WRC_POPLTN_CO'), f('FML_WRC_POPLTN_CO'), [f('AGRDE_10_WRC_POPLTN_CO'), f('AGRDE_20_WRC_POPLTN_CO'), f('AGRDE_30_WRC_POPLTN_CO'), f('AGRDE_40_WRC_POPLTN_CO'), f('AGRDE_50_WRC_POPLTN_CO'), f('AGRDE_60_ABOVE_WRC_POPLTN_CO')]]
    G = collections.defaultdict(dict)
    for cd, v in D.items(): G[cd[:5]][cd] = v
    meta = {'schema': 'tg-dongw/1', 'quarters': {'apt': Q['VwsmAdstrdAptW'], 'ncm': Q['VwsmAdstrdNcmCnsmpW'], 'wrc': Q['VwsmAdstrdWrcPopltnW']},
            'source': '서울시 상권분석서비스(서울신용보증재단) — 아파트-행정동(OA-22171 계열) · 소득소비-행정동(OA-22166) · 직장인구-행정동 · 서울 열린데이터광장 API',
            'fields': 'apt = [단지 수, 면적대 가구 5(66㎡ 미만·66·99·132·165㎡ 이상 대), 가격대 가구 7(1억 미만·1·2·3·4·5억대·6억 이상), 평균 면적㎡, 평균 시세(만 원)] · ncm = 지출(만 원) [총액, 식료품, 의류·신발, 생활용품, 의료, 교통, 교육, 유흥, 여가·문화, 기타, 외식] · wrc = [직장인구, 남, 여, 연령 6(10대~60대 이상)]',
            'note': '아파트 시세·가구는 그 동 아파트만(단독·다세대 빠짐) · 지출은 서울신용보증재단 추정(카드 등) — 주거지 기준인지 결제지 기준인지 서울시 설명에 없어 동 카드 매출과 견주지 않는다 · 소득 칸은 2026년 서울시가 지웠다'}
    for gu, dd in G.items():
        fn = os.path.join(ROOT, 'data', 'r', gu, 'dongw.json')
        if os.path.isdir(os.path.dirname(fn)): json.dump(dict(meta, gu=gu, dong=dd), open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    # 서울 기준값 — 가격대 6억 이상 가구 비중(아파트 가구 중) 중앙값 · 평균 시세 중앙값 · 지출 구성 평균
    six = sorted(v['apt'][2][6] / (sum(v['apt'][2]) or 1) * 100 for v in D.values() if v.get('apt') and sum(v['apt'][2]) > 50)
    mk = sorted(v['apt'][4] for v in D.values() if v.get('apt') and v['apt'][4])
    tot = [0] * 11
    for v in D.values():
        if v.get('ncm'): tot = [a + b for a, b in zip(tot, v['ncm'])]
    rp = os.path.join(ROOT, 'data', 'area-ref.json'); R = json.load(open(rp, encoding='utf-8'))
    R['ref']['서울']['w'] = {'six_med': round(six[len(six) // 2], 1) if six else None, 'six_p80': round(six[int(len(six) * 0.8)], 1) if six else None, 'mktc_med': mk[len(mk) // 2] if mk else None, 'mktc_p80': mk[int(len(mk) * 0.8)] if mk else None,
                             'ncm_share': [round(x / (tot[0] or 1) * 100, 1) for x in tot], 'q': meta['quarters']}
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('dongs', len(D), 'gus', len(G), R['ref']['서울']['w'])

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
