# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧾 동별 주택 보유세 범위(추정) · 소유자 2026-10-10 「읍면동별로 부동산 보유세 범위도 알 수 있을까 — 그 지역을 파악하기 좋은 방법」
#   재료 = 이미 구운 r/<구>/hp.json(국토부 공동주택 공시가격 2025 · 필지·전용면적 묶음마다 호수·최저·가운데·최고) × data/tax-rules.json 의 재산세 규칙(prop) · 종부세 공제(jbs.houseDeduction)
#   세율·비율은 이 파일에 적지 않는다 — 전부 tax-rules.json 에서 읽는다(법이 바뀌면 그 파일만 고치고 다시 굽는다) · 계산식은 js/tax-engine.js 의 prop() 과 같다
#   낸 세금이 아니다 — 공시가격에 규칙을 적용한 「추정」(과세표준상한·세부담 상한·조례 가감·감면 미반영 · 주택 한 채 기준 · 공동주택만)
#   종부세는 사람별 전국 합산이라 금액을 내지 않는다 — 공시가격이 공제액(1세대 1주택·일반)을 넘는 호수의 비율만
#   py -3.12 -X utf8 tools/region/ptax-bake.py → data/ptax-dong.json
import json, os, glob, collections, datetime, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
RULES = json.load(open(os.path.join(ROOT, 'data', 'tax-rules.json'), encoding='utf-8'))
P, J = RULES['prop'], RULES['jbs']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regcfg as RC
#   행정동 잇기 ① 지번 좌표(주택 실거래 때 브이월드로 받아 둔 07_API키/out/rtms/geo.json — 주소 → [위도, 경도, 법정동, 행정동 이름, 행정동 10자리]) ② 없는 필지는 hp.json 의 법정동→행정동(넓이·이름 근사) ③ 읍·면 이름
GEOF = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'rtms', 'geo.json')
GEO = json.load(open(GEOF, encoding='utf-8')) if os.path.exists(GEOF) else {}
def gu_name(nm): return re.sub(r'^(\S+?시)(\S+구)$', r'\1 \2', nm)   # home-bake.py 와 같은 주소 꼴
_b = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))
B2A = _b.get('b2a') or {k: v for k, v in _b.items() if isinstance(v, dict) and 'a' in v}   # 법정동 8자리 → 행정동 넓이 %(서울·경기)
def shares(bjd, ks):   # 좌표 없는 필지를 걸친 행정동에 나누는 몫 — 넓이 비율(있으면) · 없으면 똑같이(겹쳐 세지 않는다)
    a = {c: p for c, _, p in (B2A.get(bjd[:8]) or {}).get('a', []) if c in ks}
    if not a: a = {k: 1 for k in ks}
    t = sum(a.values()) or 1
    return {k: v / t for k, v in a.items()}
def jibun(pnu): return ('산' if pnu[10] == '2' else '') + str(int(pnu[11:15])) + ('-' + str(int(pnu[15:19])) if int(pnu[15:19]) else '')

def prog(base, br):   # js/tax-engine.js prog 와 같다 — br = [[상한, 세율]…] · 마지막 상한 null
    tax = 0; lo = 0
    for hi, r in br:
        if hi is None or base <= hi: return max(0, tax + (base - lo) * r)
        tax += (hi - lo) * r; lo = hi
    return max(0, tax)
def step(tbl, n):
    v = 0
    for a, b in tbl:
        if n >= a: v = b
    return v
def prop(official, one):   # 한 채 · 한 해 → (재산세+지방교육세, 도시지역분)
    fv = step(P['fmv']['oneHouse'], official) if one else P['fmv']['house']; base = official * fv
    t = prog(base, (P['houseOne'] if one and official <= P['houseOneCap'] else P['house'])[0])
    return t * (1 + P['eduTax'][0]), base * P['urban'][0]
def wq(pairs, qs):   # 무게 있는 분위수 — pairs = [(값, 무게)…]
    pairs = sorted(pairs); tot = sum(w for _, w in pairs); out = []
    for q in qs:
        acc = 0; want = tot * q; v = pairs[-1][0]
        for x, w in pairs:
            acc += w
            if acc >= want: v = x; break
        out.append(v)
    return out
def man(x): return int(round(x / 1e4))   # 원 → 만 원

def units(groups):   # [전용㎡, 호수, 최저, 가운데, 최고](만 원) → [(공시가격 원, 호수)…] — 묶음 안 낱낱 값은 없어 가운데에 몰고 3호 이상이면 최저·최고 한 호씩
    out = []
    for ar, n, lo, mid, hi in groups:
        if n >= 3: out += [(lo * 1e4, 1), (hi * 1e4, 1), (mid * 1e4, n - 2)]
        else: out.append((mid * 1e4, n))
    return out
def summ(U):
    n = sum(w for _, w in U)
    if not n: return None
    g = [(sum(prop(p, False)), w) for p, w in U]; o = [(sum(prop(p, True)), w) for p, w in U]
    gn = [(prop(p, False)[0], w) for p, w in U]; on = [(prop(p, True)[0], w) for p, w in U]
    QS = (0.1, 0.5, 0.9)
    d1, d9 = J['houseDeduction']['oneHouse'], J['houseDeduction']['general']
    return [int(round(n)), [man(x) for x in wq(g, QS)], [man(x) for x in wq(o, QS)], [man(x) for x in wq(gn, QS)], [man(x) for x in wq(on, QS)],
            round(100 * sum(w for p, w in U if p > d9) / n, 1), round(100 * sum(w for p, w in U if p > d1) / n, 1), man(wq(U, (0.5,))[0])]

def main():
    BJ = {}; HJ = collections.defaultdict(list); HJB = collections.defaultdict(set); HJX = collections.Counter(); GU = {}; year = None; cnt = collections.Counter()
    GN = {g['gu']: g['name'] for g in json.load(open(os.path.join(R, 'index.json'), encoding='utf-8'))['gus']}
    for f in sorted(glob.glob(os.path.join(R, '[0-9]' * 5, 'hp.json'))):
        h = json.load(open(f, encoding='utf-8')); gu = h['gu']; year = h['year']; by = collections.defaultdict(list)
        try: EM = {d['name']: d['k'] for d in json.load(open(os.path.join(R, gu, 'dong.json'), encoding='utf-8'))['dong']}   # 읍·면은 이름이 곧 행정동이다 — hp.json 이 못 이은 「○○읍 △△리」를 읍·면으로 잇는다
        except Exception: EM = {}
        byp = {}
        for pnu, e in h['pnu'].items(): u = units(e[2]); by[pnu[:10]] += u; byp[pnu] = u
        KS = set(EM.values())
        allu = []
        for bjd, U in by.items():
            m = h['bjd'].get(bjd); s = summ(U)
            if not m or not s: continue
            ks = m[6] or [EM[t] for t in m[0].split(' ')[:1] if t[-1:] in '읍면' and t in EM]
            BJ[bjd] = [m[0], gu] + s + [ks]; allu += U
            for pnu, u in byp.items():   # 필지마다 — 좌표가 있으면 그 행정동 하나에만, 없으면 걸친 행정동에 넓이 몫으로 나눠(근사)
                if pnu[:10] != bjd: continue
                n = sum(w for _, w in u); ge = GEO.get('%s %s %s %s' % (RC.NAME[gu[:2]], gu_name(GN.get(gu, '')), m[0], jibun(pnu)))
                k1 = str(ge[4])[:8] if ge and len(ge) > 4 and ge[4] else None
                if k1 in KS: HJ[k1] += u; HJB[k1].add(bjd); HJX[k1] += n; cnt['좌표로 이은 호'] += n
                else:
                    cnt['근사로 이은 호' if ks else '행정동 못 이은 호'] += n
                    for k, sh in shares(bjd, ks).items(): HJ[k] += [(p, w * sh) for p, w in u]; HJB[k].add(bjd)
        s = summ(allu)
        if s: GU[gu] = s
    doc = {'schema': 'tg-ptax/1', 'made': datetime.date.today().isoformat(), 'year': year,
           'source': '국토교통부 「주택 공시가격 정보」 %d년 정기공시(공동주택) × data/tax-rules.json 재산세 규칙(%s) · 종합부동산세법 제8조 제1항 공제액' % (year, P['fmv']['_'].split('(')[0]),
           'rules': {'checked': RULES['checked'], 'via': RULES['checkedVia'], '지방세법': RULES['versions'].get('지방세법'), '지방세법 시행령': RULES['versions'].get('지방세법 시행령'), '종합부동산세법': RULES['versions'].get('종합부동산세법'),
                     'fmv': P['fmv']['_'], 'house': P['house'][1], 'houseOne': P['houseOne'][1], 'urban': P['urban'][1], 'eduTax': P['eduTax'][1], 'jbs': J['houseDeduction']['_'],
                     'ded': [J['houseDeduction']['general'], J['houseDeduction']['oneHouse']]},
           'note': ['낸 세금이 아니다 — 공시가격에 규칙을 적용한 추정(주택 한 채 · 한 해)', P['capNote'], '공동주택(아파트·연립·다세대)만 — 단독·다가구는 개별주택가격 자료가 없어 빠졌다',
                    '공시가격은 %d년 것이고 규칙은 확인일 현재 것이다 — 해가 다르다' % year, '필지·전용면적 묶음의 가운데 값으로 셈(3호 이상이면 최저·최고 한 호씩) — 낱낱 호 값이 아니다',
                    '종부세는 사람별 전국 합산이라 금액을 내지 않고, 공시가격이 공제액을 넘는 호수 비율만 낸다(한 채 기준 — 여러 채 가진 사람은 더 낮은 값에서도 낸다)',
                    '행정동 값은 필지를 지번 좌표로 그 동에 넣은 것이다 — 좌표가 없는 필지만 걸친 행정동에 넓이 몫으로 나눠 넣은 근사(동마다 좌표로 넣은 비율을 같이 싣는다 · 낮은 동은 값이 이웃 동과 섞여 있다) · 도시지역분은 도시지역 안에서만 붙는다(읍·면은 안 붙을 수 있다)'],
           'fields': '값 = [호수, 일반 합계[하위10%·가운데·상위10%], 1세대1주택 합계[같음], 일반 도시지역분 뺀[같음], 1세대1주택 도시지역분 뺀[같음], 일반 공제액 초과 %, 1세대1주택 공제액 초과 %, 공시가격 가운데] · 금액 만 원 · 합계 = 재산세 + 지방교육세 + 도시지역분 · bjd 는 앞에 [이름, 구], 끝에 [행정동 코드] · hjd 는 끝에 [걸친 법정동 수, 지번 좌표로 이 동에 넣은 호수 %(100 에 가까울수록 정확 · 나머지는 법정동 넓이·이름 근사)]',
           'bjd': BJ, 'hjd': {k: summ(U) + [len(HJB[k]), round(100 * HJX[k] / max(1, sum(w for _, w in U)))] for k, U in HJ.items()}, 'gu': GU}
    p = os.path.join(ROOT, 'data', 'ptax-dong.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('법정동', len(BJ), '행정동', len(doc['hjd']), '구', len(GU), '바이트', os.path.getsize(p), dict(cnt))
    for k in ('11650590', '11650600', '11650610', '11650620', '11650621', '41591253'):
        if k in doc['hjd']: print(k, doc['hjd'][k])
    for k in ('1165010100', '1165010800', '4159025900'):
        if k in BJ: print(k, BJ[k][:10])
    print('검산 공시 10억 일반', [round(x) for x in prop(1e9, False)], '1주택', [round(x) for x in prop(1e9, True)], '· 공시 5억 1주택', [round(x) for x in prop(5e8, True)])
if __name__ == '__main__': main()
