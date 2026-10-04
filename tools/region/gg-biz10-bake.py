# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.3.1 — 경기 동별 사업체·종사자(시가 KOSIS 에 올린 「동·읍면동별 사업체」 표 · 시마다 표 모양이 다르다)
#   표: 수원 DT_D200002 · 용인 DT_DBA0021 · 화성 DT_63601_D000004 · 안양 DT_61401_D000003 · 광명 DT_61601_D000003 · 평택 DT_61701_D000004 ·
#       과천 DT_A050104 · 남양주 DT_62301_D000004 · 의왕 DT_62701_D000006 · 이천 DT_63101_D000003 · 안성 DT_63201_D000004 · 김포 DT_63301_D000007 ·
#       양주 DT_63401_D000007 · 포천 DT_63901_D000003 (나머지 시는 KOSIS 에서 동별 표를 찾지 못했다)
#   규칙: 「사업체수」·「종사자수」 = 동이 아닌 쪽 차원에서 처음 나오는 그 이름(= 전 산업·전 규모 합) · 항목 차원에 그 이름이 있으면 그것 + 다른 차원 첫 항목(합계)
#   py -3.12 -X utf8 tools/region/gg-biz10-bake.py fetch|build   (fac-bake·biz10-bake 다음)
import json, os, sys, re, time, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'kosis', 'ggbiz')
T = [('수원시', '611', 'DT_D200002'), ('용인시', '629', 'DT_DBA0021'), ('화성시', '636', 'DT_63601_D000003'), ('안양시', '614', 'DT_61401_D000003'), ('광명시', '616', 'DT_61601_D000003'),
     ('평택시', '617', 'DT_61701_D000004'), ('과천시', '621', 'DT_A050104'), ('남양주시', '623', 'DT_62301_D000004'), ('의왕시', '627', 'DT_62701_D000006'), ('이천시', '631', 'DT_63101_D000003'),
     ('안성시', '632', 'DT_63201_D000004'), ('김포시', '633', 'DT_63301_D000007'), ('양주시', '634', 'DT_63401_D000007'), ('포천시', '639', 'DT_63901_D000003')]
norm = lambda s: re.sub(r'[\s·.,ㆍ()]', '', s or '')

def g(u):
    for a in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
        except Exception as e: print('retry', e); time.sleep(5)
    return []

def fetch():
    ks = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']; os.makedirs(OUT, exist_ok=True)
    for city, org, tbl in T:
        fn = os.path.join(OUT, tbl + '.json')
        if os.path.exists(fn): continue
        meta = g('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=%s&tblId=%s&format=json&jsonVD=Y' % (ks, org, tbl))
        objs = []
        for x in meta:
            if x.get('OBJ_ID') != 'ITEM' and x.get('OBJ_ID') not in objs: objs.append(x.get('OBJ_ID'))
        rows = []
        for y in range(2015, 2031):
            u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=Y&orgId=%s&tblId=%s&itmId=ALL&startPrdDe=%d&endPrdDe=%d' % (ks, org, tbl, y, y)
            for i in range(len(objs)): u += '&objL%d=ALL' % (i + 1)
            r = g(u)
            if isinstance(r, list): rows += r
        json.dump({'city': city, 'meta': meta, 'objs': objs, 'rows': rows}, open(fn, 'w', encoding='utf-8'), ensure_ascii=False)
        print(city, tbl, len(rows))

def build():
    fac = {}   # 시 이름 → [(구 코드, fac, 동 코드, 동 dict)]
    for gdir in os.listdir(os.path.join(ROOT, 'data', 'r')):
        fn = os.path.join(ROOT, 'data', 'r', gdir, 'fac.json')
        if not gdir.startswith('41') or not os.path.exists(fn): continue
        F = json.load(open(fn, encoding='utf-8')); nm = F.get('name', '')
        m = re.match(r'(.+?[시군])', nm); city = m.group(1) if m else nm
        fac.setdefault(city, []).append((gdir, F, fn))
    hit = miss = 0; gb = {}; touched = set()
    for city, org, tbl in T:
        fn = os.path.join(OUT, tbl + '.json')
        if not os.path.exists(fn): continue
        J = json.load(open(fn, encoding='utf-8')); meta, rows = J['meta'], J['rows']
        dims = collections.OrderedDict()
        for x in meta: dims.setdefault(x['OBJ_ID'], []).append((x['ITM_ID'], (x['ITM_NM'] or '').strip()))
        dong_dim = [k for k in dims if k != 'ITEM' and any(re.search(r'(동|읍|면)$', n) for _, n in dims[k][1:])][0]
        other = [k for k in dims if k not in ('ITEM', dong_dim)]
        item_names = [n for _, n in dims.get('ITEM', [])]
        pick = {}   # 무엇 → (항목 ID 또는 None, 다른 차원 ID 또는 None)
        for want in ('사업체수', '종사자수'):
            it = [i for i, n in dims.get('ITEM', []) if n.replace(' ', '') == want]
            if it: pick[want] = ('ITM', it[0], [dims[o][0][0] for o in other])
            else:
                for o in other:   # 위계(UP_ITM_ID)로 가장 얕은 「사업체수」 — 산업마다 있는 것 말고 전체 합계 바로 아래 것 · 그 값이 실제 줄에 있어야 한다
                    up = {x['ITM_ID']: x.get('UP_ITM_ID') for x in meta if x['OBJ_ID'] == o}
                    def depth(i):
                        d = 0
                        while up.get(i) and d < 9: i = up[i]; d += 1
                        return d
                    have = set(r.get('C%d' % (1 + [k for k in dims if k != 'ITEM'].index(o))) for r in rows)
                    nmo = {i: n.replace(' ', '') for i, n in dims[o]}
                    c = [i for i, n in dims[o] if n.replace(' ', '').startswith(want) and i in have]
                    top = [i for i in c if nmo.get(up.get(i)) in ('합계', '계', '전산업', '총계', '전체') or not up.get(i)]
                    if top: pick[want] = ('OBJ', o, sorted(top, key=depth)[0]); break
                    if len(c) > 3: pick[want] = ('SUM', o, set(c)); break   # 산업마다 따로인 표 — 모든 산업의 그 칸을 더한다(산업 대분류는 한 겹)
        oi = {o: i + 1 for i, o in enumerate([k for k in dims if k != 'ITEM'])}
        val = collections.defaultdict(lambda: collections.defaultdict(lambda: [None, None]))
        nmof = {i: n for i, n in dims[dong_dim]}
        for r in rows:
            dc = r.get('C%d' % oi[dong_dim]); dn = nmof.get(dc) or r.get('C%d_NM' % oi[dong_dim])
            if not dn or not re.search(r'(동|읍|면)$', dn.strip()) or r.get('DT') in (None, '', '-'): continue
            for k, (want, p) in enumerate(pick.items()):
                if p[0] == 'SUM':
                    if r.get('C%d' % oi[p[1]]) not in p[2]: continue
                    if any(r.get('C%d' % oi[o]) != dims[o][0][0] for o in other if o != p[1]): continue
                    try:
                        cur = val[norm(dn)][r['PRD_DE']]; j = 0 if want == '사업체수' else 1; cur[j] = (cur[j] or 0) + int(float(r['DT']))
                    except Exception: pass
                    continue
                if p[0] == 'ITM':
                    if r.get('ITM_ID') != p[1] or any(r.get('C%d' % oi[o]) != p[2][j] for j, o in enumerate(other)): continue
                else:
                    if r.get('C%d' % oi[p[1]]) != p[2]: continue
                    if any(r.get('C%d' % oi[o]) != dims[o][0][0] for o in other if o != p[1]): continue
                try: val[norm(dn)][r['PRD_DE']][0 if want == '사업체수' else 1] = int(float(r['DT']))
                except Exception: pass
        for gdir, F, ffn in fac.get(city, []):
            for code, d in F['dong'].items():
                v = val.get(norm(d['name']))
                if v:
                    ser, prev = [], None
                    for y in sorted(v):   # 표가 바뀐 해에 갑자기 무너지는 값(전해의 30% 아래)은 뺀다 — 시 표의 산업 칸 이름이 해마다 달라 더한 값이 비는 경우
                        n = v[y][0]
                        if n is None or (prev and n < prev * 0.3): continue
                        ser.append([y] + v[y]); prev = n
                    if ser: d['bz'] = ser; hit += 1; touched.add(ffn)
                else: miss += 1
            F['bzsrc'] = 'KOSIS %s 동·읍면동별 사업체수·종사자수(%s · 통계청 전국사업체조사 · 시 공표)' % (city, tbl)
        print(city, tbl, 'dongs', len(val), 'pick', {k: v[0] for k, v in pick.items()})
    for gdir, lst in [(c, l) for c, l in fac.items()]:
        for g2, F, ffn in lst:
            if ffn in touched:
                json.dump(F, open(ffn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g2] = os.path.getsize(ffn)
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8'))
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['fac'] = gb[g2['gu']]
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('hit', hit, 'miss', miss, 'gus', len(gb))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
