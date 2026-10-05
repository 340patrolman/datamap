# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.8.0 — 🌏 외국인 세부(소유자 「단기·장기체류·영주권·귀화자 · 국적 · 성별 · 나이 자세히」) → data/foreign.json 에 더한다(foreign-bake.py 다음에)
#   법무부 출입국·외국인정책 통계(KOSIS 111): DT_1B040A11 시군구별 체류자격별 등록외국인 · DT_1B040A9C 시군구별 국적별 등록외국인(성별) — 최신 해
#   행정안전부(KOSIS 110): DT_110025_A031_A·A032_A 연령별(남·여) · DT_110025_A034_A 체류기간별 — 2024
#   ⚠ 단기체류 외국인(90일 이하)은 법무부 통계가 전국 단위뿐(시군구 없음) — 서울만 생활인구 단기체류 외국인으로 볼 수 있다
#   지역 맞추기: 표마다 지역 코드가 달라 메타의 상위 항목(UP_ITM_ID)을 따라 시도·시 이름을 붙여 지도 시군구 이름과 맞춘다
#   py -3.12 -X utf8 tools/region/foreign-detail.py
import json, os, re, urllib.request, urllib.parse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
K = urllib.parse.quote(json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis'], safe='')

def kmeta(org, tbl):
    u = 'https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=%s&tblId=%s&format=json&jsonVD=Y' % (K, org, tbl)
    return json.loads(urllib.request.urlopen(u, timeout=120).read().decode('utf-8', 'replace'))
def kdata(org, tbl, objs, prd='Y', last=1):
    q = '&'.join('objL%d=%s' % (i + 1, o) for i, o in enumerate(objs))
    u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&itmId=ALL&%s&format=json&jsonVD=Y&prdSe=%s&newEstPrdCnt=%d&orgId=%s&tblId=%s' % (K, q, prd, last, org, tbl)
    j = json.loads(urllib.request.urlopen(u, timeout=300).read().decode('utf-8', 'replace'))
    if isinstance(j, dict): raise RuntimeError('%s %s' % (tbl, j))
    return j
def num(v):
    try: return int(float(v))
    except Exception: return None
SDN = [('서울', '11'), ('부산', '26'), ('대구', '27'), ('인천', '28'), ('광주', '12'), ('대전', '30'), ('울산', '31'), ('세종', '36'), ('경기', '41'), ('강원', '51'), ('충청북', '43'), ('충북', '43'),
       ('충청남', '44'), ('충남', '44'), ('전라북', '52'), ('전북', '52'), ('전라남', '12'), ('전남', '12'), ('경상북', '47'), ('경북', '47'), ('경상남', '48'), ('경남', '48'), ('제주', '50')]
def sdcode(nm):
    for k, v in SDN:
        if nm.startswith(k): return v
    return None
def is_sido(nm): return bool(re.search(r'(특별시|광역시|특별자치시|특별자치도|도)$', nm)) and sdcode(nm) is not None

def regmap(meta, obj, IX):
    nz = lambda s: re.sub(r'\s', '', s or '')
    by = collections.defaultdict(list)
    for g in IX['gus']: by[(g['gu'][:2], nz(g['name']))].append(g['gu'])
    it = {x['ITM_ID']: (x['ITM_NM'], x.get('UP_ITM_ID')) for x in meta if x['OBJ_ID'] == obj}
    out = {}
    for iid, (nm, up) in it.items():
        if nm.startswith('세종'): out[iid] = by.get(('36', '세종시'), []); continue
        chain = []; u = up
        while u and u in it and len(chain) < 4: chain.append(it[u][0]); u = it[u][1]
        sd = None; city = ''
        for c in chain:
            if is_sido(c): sd = sdcode(c)
            elif c.endswith('시'): city = c
        if not sd or is_sido(nm): continue
        full = city + nm if city and nm.endswith('구') else nm
        cand = by.get((sd, nz(full))) or by.get((sd, nz(nm)))
        if not cand and nz(nm).endswith('시'): cand = [x for (s2, n2), xs in by.items() if s2 == sd and n2.startswith(nz(nm)) for x in xs]
        if cand: out[iid] = cand
    return out

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    doc = json.load(open(os.path.join(ROOT, 'data', 'foreign.json'), encoding='utf-8')); G = doc['gu']; direct = collections.defaultdict(set)
    def put(gc, key, val, d):
        o = G.setdefault(gc, {'src': ''})
        if d: o[key] = val; direct[gc].add(key)
        elif key not in direct[gc]: o[key] = val
    # 1) 체류자격(법무부 · 계)
    m = kmeta('111', 'DT_1B040A11'); R = regmap(m, '13101870964C', IX); quals = {x['ITM_ID']: x['ITM_NM'] for x in m if x['OBJ_ID'] == '13101870964A'}
    rows = kdata('111', 'DT_1B040A11', ['ALL', '13102870964B.0', 'ALL']); yq = rows[0]['PRD_DE'] if rows else ''   # 차원 순서 = 지역 · 성별 · 체류자격
    acc = collections.defaultdict(dict)
    for r in rows:
        if r['C1'] not in R or r['C3'] == 'AAA0000': continue
        v = num(r['DT'])
        if v: acc[r['C1']][quals.get(r['C3'], r['C3'])] = v
    for rid, d in acc.items():
        for gc in R[rid]: put(gc, 'q', dict(sorted(d.items(), key=lambda kv: -kv[1])[:12]), len(R[rid]) == 1)
    print('체류자격', yq, len(acc), flush=True)
    # 2) 국적(법무부 · 상위 30개 국적 · 성별)
    m = kmeta('111', 'DT_1B040A9C'); R2 = regmap(m, 'SGG', IX)
    natl = [x for x in m if x['OBJ_ID'] == '13101870964A']; nats = [x['ITM_ID'] for x in natl][:31]; natn = {x['ITM_ID']: x['ITM_NM'] for x in natl}
    acc = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0])); yn = ''
    for chunk in (nats[1:11], nats[11:21], nats[21:31]):
        for r in kdata('111', 'DT_1B040A9C', ['ALL', 'ALL', '+'.join(chunk)]):
            yn = r['PRD_DE']
            if r['C1'] not in R2: continue
            v = num(r['DT'])
            if v is None: continue
            acc[r['C1']][natn.get(r['C3'], r['C3'])][{'0': 0, '1': 1, '2': 2}.get(r['C2'], 0)] = v
    for rid, d in acc.items():
        top = sorted(([k] + v for k, v in d.items() if v[0]), key=lambda x: -x[1])[:10]
        for gc in R2[rid]: put(gc, 'nat', top, len(R2[rid]) == 1)
    print('국적', yn, len(acc), flush=True)
    # 3) 연령·성별(행안부 · 한국국적 없는 외국인 AD · 귀화 AF)
    m = kmeta('110', 'DT_110025_A031_A'); R3 = regmap(m, '11101HJG', IX); ya = ''; AG = ['010', '060', '110', '140', '170', '200', '250', '290']
    for sex, tb in (('m', 'DT_110025_A031_A'), ('f', 'DT_110025_A032_A')):
        acc = collections.defaultdict(lambda: {'AD': [0] * 8, 'AF': [0] * 8})
        for r in kdata('110', tb, ['ALL', '15110AA0AD+15110AA0AF', 'ALL']):
            ya = r['PRD_DE']
            if r['C1'] not in R3 or r['C3'] not in AG: continue
            acc[r['C1']]['AD' if r['C2'] == '15110AA0AD' else 'AF'][AG.index(r['C3'])] = num(r['DT']) or 0
        for rid, d in acc.items():
            for gc in R3[rid]:
                a = dict(G.get(gc, {}).get('age') or {}); a[sex + 'f'] = d['AD']; a[sex + 'n'] = d['AF']; put(gc, 'age', a, len(R3[rid]) == 1)
    print('연령', ya, flush=True)
    # 4) 체류기간(행안부 · 한국국적 없는 외국인 합계)
    m = kmeta('110', 'DT_110025_A034_A'); R4 = regmap(m, '11101HJG', IX); BB = ['B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08']
    acc = collections.defaultdict(lambda: [0] * 7)
    for r in kdata('110', 'DT_110025_A034_A', ['ALL', '15110AA000', 'ALL']):
        if r['C1'] in R4 and r['C3'] in BB: acc[r['C1']][BB.index(r['C3'])] = num(r['DT']) or 0
    for rid, v in acc.items():
        for gc in R4[rid]: put(gc, 'stay', v, len(R4[rid]) == 1)
    doc['detail'] = {'q': '법무부 등록외국인 체류자격별(KOSIS 111 DT_1B040A11 · %s년 말) — 등록외국인(90일 넘게 머무는 외국인) · 상위 12' % yq,
                     'nat': '법무부 등록외국인 국적별(KOSIS 111 DT_1B040A9C · %s년 말) — [국적, 계, 남, 여] 상위 10(전국 상위 30개 국적 중)' % yn,
                     'age': '행정안전부 외국인주민 연령별(%s.11.1) — mf·ff = 한국국적 없는 외국인 남·여 · mn·fn = 귀화(한국국적 취득) 남·여 · 0~9 · 10대 … 60대 · 70~' % ya,
                     'stay': '행정안전부 외국인주민 체류기간별(2024.11.1) — 1년 미만 · 1~2 · 2~3 · 3~4 · 4~5 · 5~10 · 10년 이상',
                     'short': '단기체류(90일 이하)는 시군구 공식 통계가 없다(법무부 단기체류외국인 현황은 전국 단위) — 서울만 생활인구 단기체류 외국인으로 볼 수 있다',
                     'note': '등록외국인(법무부)과 외국인주민(행안부)은 기준일·범위가 달라 숫자가 맞지 않는다 — 함께 더하지 않는다'}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'foreign.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    s = G.get('11650', {}); print('서초', s.get('q'), s.get('nat', [])[:3], s.get('stay'), (s.get('age') or {}).get('mf'))
    print('채운 시군구 q', sum(1 for v in G.values() if 'q' in v), 'nat', sum(1 for v in G.values() if 'nat' in v), 'age', sum(1 for v in G.values() if 'age' in v), 'stay', sum(1 for v in G.values() if 'stay' in v), '/', len(IX['gus']))

if __name__ == '__main__': main()
