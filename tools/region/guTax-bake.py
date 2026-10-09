# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.2.0 — 📝 동 풀어 읽기의 「구 지갑」(시군구 평균 — 동으로 나누지 않는다): 국세청 국세통계(KOSIS 133)
#   DT_133001N_4215 시·군·구별 근로소득 연말정산 신고현황(주소지) — 인원·총급여 → 1인당 총급여
#   DT_133N_A3212   종합소득세 주요항목 신고 현황(시·군·구) — 신고인원·종합소득금액 → 1인당 종합소득금액
#   DT_133N_A7112   종합부동산세 결정세액 현황(시군구별) — 합계·주택분(백만 원)
#   py -3.12 -X utf8 tools/region/guTax-bake.py   →  data/gu-tax.json { 구 코드: {...} } (v2.96.0 전국 17개 시도 — 그 전은 서울·경기·인천)
#   v2.96.0 KOSIS 시도 이름(서울·부산 … · 「○○특별자치도」 포함)을 SDN 으로 지도 시도 코드에 잇는다 · 전남광주(12) = 옛 광주·전남 두 이름 모두 · 못 이은 줄은 끝에 「못 이음」으로 찍는다(코워크가 회신)
import json, os, re, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
T = [('DT_133001N_4215', 'wage'), ('DT_133N_A3212', 'inc'), ('DT_133N_A7112', 'jbs')]
nz = lambda s: re.sub(r'\s+', '', s or '')
SDN = {'서울': '11', '부산': '26', '대구': '27', '인천': '28', '광주': '12', '대전': '30', '울산': '31', '세종': '36', '경기': '41', '강원': '51', '충북': '43', '충남': '44', '전북': '52', '전남': '12', '경북': '47', '경남': '48', '제주': '50',
       '충청북': '43', '충청남': '44', '전라북': '52', '전라남': '12', '경상북': '47', '경상남': '48'}
# v2.97.0 인천 2026-07 개편(국세통계는 옛 구 이름) — 옛 구 값을 새 구에 근사로: 중구 → 영종구·제물포구 · 동구 → 제물포구 · 서구 → 서해구·검단구 · 제물포구처럼 두 옛 구가 겹치면 인원·금액을 더해 1인당을 다시 낸다
ALIAS = {('28', '중구'): ['영종구', '제물포구'], ('28', '동구'): ['제물포구'], ('28', '서구'): ['서해구', '검단구']}
def cands(byName, sd, name):
    n = nz(re.sub(r'\(.*?\)', '', name or ''))
    if (sd, n) in byName: return [byName[(sd, n)]], False
    if (sd, n) in ALIAS: return [byName[(sd, nz(x))] for x in ALIAS[(sd, n)] if (sd, nz(x)) in byName], True
    if sd == '36': return [v for (s2, n2), v in byName.items() if s2 == '36'], False
    return [v for (s2, n2), v in byName.items() if s2 == sd and n2.startswith(n)], False
def sdk(name):
    n = re.sub(r'(특별자치시|특별자치도|특별시|광역시|도)$', '', nz(name))
    return SDN.get(n) or SDN.get(n[:2])

def main():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
    g = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
    R = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    byName = {}
    for x in R['gus']:
        byName[(x['gu'][:2], nz(x['name']))] = x['gu']
    miss = collections.Counter(); aliasG = set()
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
                    a = r['C1']; p = par.get(a); sd = sdk(nm.get(p, '') if p else '') or ('36' if sdk(r['C1_NM']) == '36' else None)
                    if not sd: continue
                    cand, add = cands(byName, sd, r['C1_NM'])
                    for gc in cand:
                        kk = (r.get('C2_NM') or r.get('ITM_NM'), r.get('ITM_NM')); vv = float(r['DT']) if r['DT'] not in ('-', '') else None
                        if add:   # v2.97.1 옛 구 둘을 더할 때 빈칸('-')은 건너뛴다(먼저 들어간 다른 구 값을 지우지 않게 · 코워크 지적)
                            if vv is not None: VY[gc][kk] = (VY[gc].get(kk) or 0) + vv
                        else: VY[gc][kk] = vv
                for gc, d in VY.items():
                    v2 = per(key, d)
                    if v2: HIST[gc][key][str(y)] = v2
                print(tbl, y, len(VY), flush=True)
        for r in rows:
            a = r['C1']; p = par.get(a); sd = sdk(nm.get(p, '') if p else '') or ('36' if sdk(r['C1_NM']) == '36' else None)
            if not sd: continue
            cand, add = cands(byName, sd, r['C1_NM'])   # 일반구가 있는 시(구 없이) — 그 시의 모든 구에 같은 값 · 인천 옛 구 → 새 구(ALIAS)
            if not cand: miss[(key, nm.get(p, ''), r['C1_NM'])] += 1; continue
            if add: aliasG.update(cand)
            for gc in cand:
                kk = (r.get('C2_NM') or r.get('ITM_NM'), r.get('ITM_NM')); vv = float(r['DT']) if r['DT'] not in ('-', '') else None
                if add:
                    if vv is not None: V[gc][kk] = (V[gc].get(kk) or 0) + vv
                else: V[gc][kk] = vv
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
    for gc in aliasG:   # v2.97.1 인천 새 구(옛 구 값을 나눠 이음) — 1인당만 보이고 총액(종부세)·순위에서는 뺀다(옛 중구 값이 영종구·제물포구 둘에 들어가 시도 합계가 부풀지 않게 · 코워크 지적)
        if gc in out: out[gc]['alias'] = 1; out[gc].pop('jbs', None)
    for sd in sorted({gc[:2] for gc in out}):   # 순위 = 시도 안(v2.96.0 전국)
        for key in ('wage', 'inc'):
            L = sorted([(v[key][0], gc) for gc, v in out.items() if gc.startswith(sd) and key in v and not v.get('alias')], reverse=True); seen = []
            for rank, (val, gc) in enumerate(L): out[gc][key + 'R'] = [rank + 1, len(L)]
    J = {'schema': 'tg-gutax/1', 'years': yrs, 'source': '국세청 국세통계(KOSIS 133) — DT_133001N_4215 연말정산(주소지) · DT_133N_A3212 종합소득세(시군구) · DT_133N_A7112 종합부동산세(시군구)',
         'fields': 'wage = [1인당 총급여(만 원/년), 인원] · wageY·incY = [[해, 1인당(만 원/년)]…] 2016~ · inc = [1인당 종합소득금액(만 원/년), 신고인원] · jbs = [종부세 결정세액 합계, 주택분](백만 원) · *R = [순위, 개수](시도 안 순위) · alias = 1 이면 2026-07 개편 전 옛 구 값을 이은 근사(종부세·순위 없음)',
         'note': '시군구 평균이다 — 동 주민 수로 나누면 틀린다. 인천 제물포구·영종구·서해구·검단구는 2026-07 개편 전 옛 구(중구·동구·서구) 값을 이은 근사다. 주소지 기준 연말정산은 그 구에 사는 근로자 · 종부세는 공제를 넘는 사람만 · 경기 「○○시」 값은 그 시의 구마다 같은 값.', 'gu': out}
    json.dump(J, open(os.path.join(ROOT, 'data', 'gu-tax.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(yrs, len(out), out.get('11650'), out.get('11680'), out.get('41111'))
    print('시도별 시군구 수', dict(collections.Counter(gc[:2] for gc in out)))
    for (key, sdn, name), c in sorted(miss.items()): print('못 이음', key, sdn, name)

if __name__ == '__main__':
    main()
