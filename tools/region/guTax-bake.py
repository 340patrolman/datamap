# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.2.0 — 📝 동 풀어 읽기의 「구 지갑」(시군구 평균 — 동으로 나누지 않는다): 국세청 국세통계(KOSIS 133)
#   DT_133001N_4215 시·군·구별 근로소득 연말정산 신고현황(주소지) — 인원·총급여 → 1인당 총급여
#   DT_133N_A3212   종합소득세 주요항목 신고 현황(시·군·구) — 신고인원·종합소득금액 → 1인당 종합소득금액
#   DT_133N_A7112   종합부동산세 결정세액 현황(시군구별) — 합계·주택분(백만 원)
#   py -3.12 -X utf8 tools/region/guTax-bake.py   →  data/gu-tax.json { 구 코드: {...} } (서울·경기)
import json, os, re, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
T = [('DT_133001N_4215', 'wage'), ('DT_133N_A3212', 'inc'), ('DT_133N_A7112', 'jbs')]
nz = lambda s: re.sub(r'\s+', '', s or '')

def main():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
    g = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
    R = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    byName = {}
    for x in R['gus']:
        sd = {'11': '서울', '41': '경기', '28': '인천'}.get(x['gu'][:2])
        if sd: byName[(sd, nz(x['name']))] = x['gu']   # v2.7.0 인천 · v2.85.0 전국 색인이라 셋 밖은 건너뜀
    out = collections.defaultdict(dict); yrs = {}; HIST = collections.defaultdict(lambda: collections.defaultdict(dict))
    def per(key, d):
        if key == 'wage':
            n = d.get(('과세대상근로소득(총급여)', '인원')); a2 = d.get(('과세대상근로소득(총급여)', '금액'))
        else:
            n = d.get(('신고인원', '종합소득세 주요항목 신고 현황')); a2 = d.get(('종합소득금액', '종합소득세 주요항목 신고 현황'))
        return [round(a2 * 1e6 / n / 1e4), int(n)] if n and a2 else None
    for tbl, key in T:
        meta = g('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=133&tblId=%s&format=json&jsonVD=Y' % (k, tbl))
        objs = []
        for x in meta:
            if x['OBJ_ID'] != 'ITEM' and x['OBJ_ID'] not in objs: objs.append(x['OBJ_ID'])
        A = [x for x in meta if x['OBJ_ID'] == 'A']; par = {x['ITM_ID']: x.get('UP_ITM_ID') for x in A}; nm = {x['ITM_ID']: x['ITM_NM'] for x in A}
        u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=Y&orgId=133&tblId=%s&itmId=ALL&newEstPrdCnt=1' % (k, tbl)
        for i in range(len(objs)): u += '&objL%d=ALL' % (i + 1)
        rows = g(u); yrs[key] = max(r['PRD_DE'] for r in rows); V = collections.defaultdict(dict)
        if key in ('wage', 'inc'):   # v2.85.0 해마다(2016~) — 칸 4만 개 제한이라 해마다 나눠 받는다(코워크 10/7 회신)
            for y in range(2016, int(yrs[key]) + 1):
                uy = u.replace('&newEstPrdCnt=1', '&startPrdDe=%d&endPrdDe=%d' % (y, y)); VY = collections.defaultdict(dict)
                try: ry = g(uy)
                except Exception as e: print(tbl, y, '받지 못함', e); continue
                if not isinstance(ry, list): print(tbl, y, str(ry)[:120]); continue
                for r in ry:
                    a = r['C1']; p = par.get(a); sd = nm.get(p, '') if p else ''
                    if sd not in ('서울', '경기', '인천'): continue
                    gu = byName.get((sd, nz(r['C1_NM'])))
                    cand = [gu] if gu else [v for (s2, n2), v in byName.items() if s2 == sd and n2.startswith(nz(r['C1_NM']))]
                    for gc in cand: VY[gc][(r.get('C2_NM') or r.get('ITM_NM'), r.get('ITM_NM'))] = float(r['DT']) if r['DT'] not in ('-', '') else None
                for gc, d in VY.items():
                    v2 = per(key, d)
                    if v2: HIST[gc][key][str(y)] = v2
                print(tbl, y, len(VY), flush=True)
        for r in rows:
            a = r['C1']; p = par.get(a); sd = nm.get(p, '') if p else ''
            if sd not in ('서울', '경기', '인천'): continue
            gu = byName.get((sd, nz(r['C1_NM'])))
            if not gu:   # 경기 시(구 없이) — 그 시의 모든 구에 같은 값
                cand = [v for (s2, n2), v in byName.items() if s2 == sd and n2.startswith(nz(r['C1_NM']))]
                if not cand: continue
            else: cand = [gu]
            for gc in cand: V[gc][(r.get('C2_NM') or r.get('ITM_NM'), r.get('ITM_NM'))] = float(r['DT']) if r['DT'] not in ('-', '') else None
        for gc, d in V.items():
            if key == 'wage':
                n = d.get(('과세대상근로소득(총급여)', '인원')); a2 = d.get(('과세대상근로소득(총급여)', '금액'))
                if n and a2: out[gc]['wage'] = [round(a2 * 1e6 / n / 1e4), int(n)]
            elif key == 'inc':
                n = d.get(('신고인원', '종합소득세 주요항목 신고 현황')); a2 = d.get(('종합소득금액', '종합소득세 주요항목 신고 현황'))
                if n and a2: out[gc]['inc'] = [round(a2 * 1e6 / n / 1e4), int(n)]
            else:
                out[gc]['jbs'] = [d.get(('합계', '종합부동산세 결정세액 현황')), d.get(('주택분', '종합부동산세 결정세액 현황'))]
    for gc, H in HIST.items():
        for key, Y in H.items(): out[gc][key + 'Y'] = [[y, Y[y][0]] for y in sorted(Y)]
    for sd in ('11', '41', '28'):   # 순위(서울 25개 구 · 경기 시군구 · 인천 구·군)
        for key in ('wage', 'inc'):
            L = sorted([(v[key][0], gc) for gc, v in out.items() if gc.startswith(sd) and key in v], reverse=True); seen = []
            for rank, (val, gc) in enumerate(L): out[gc][key + 'R'] = [rank + 1, len(L)]
    J = {'schema': 'tg-gutax/1', 'years': yrs, 'source': '국세청 국세통계(KOSIS 133) — DT_133001N_4215 연말정산(주소지) · DT_133N_A3212 종합소득세(시군구) · DT_133N_A7112 종합부동산세(시군구)',
         'fields': 'wage = [1인당 총급여(만 원/년), 인원] · wageY·incY = [[해, 1인당(만 원/년)]…] 2016~ · inc = [1인당 종합소득금액(만 원/년), 신고인원] · jbs = [종부세 결정세액 합계, 주택분](백만 원) · *R = [순위, 개수](서울 25개 구 · 경기 시군구 따로)',
         'note': '시군구 평균이다 — 동 주민 수로 나누면 틀린다. 주소지 기준 연말정산은 그 구에 사는 근로자 · 종부세는 공제를 넘는 사람만 · 경기 「○○시」 값은 그 시의 구마다 같은 값.', 'gu': out}
    json.dump(J, open(os.path.join(ROOT, 'data', 'gu-tax.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(yrs, len(out), out.get('11650'), out.get('11680'), out.get('41111'))

if __name__ == '__main__':
    main()
