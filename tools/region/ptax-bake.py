# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧾 동별 주택 보유세 범위(추정) · 소유자 2026-10-10 「읍면동별로 부동산 보유세 범위도 알 수 있을까 — 그 지역을 파악하기 좋은 방법」
#   재료 = 이미 구운 r/<구>/hp.json(국토부 공동주택 공시가격 2025 · 필지·전용면적 묶음마다 호수·최저·가운데·최고) × data/tax-rules.json 의 재산세 규칙(prop) · 종부세 공제(jbs.houseDeduction)
#   세율·비율은 이 파일에 적지 않는다 — 전부 tax-rules.json 에서 읽는다(법이 바뀌면 그 파일만 고치고 다시 굽는다) · 계산식은 js/tax-engine.js 의 prop() 과 같다
#   낸 세금이 아니다 — 공시가격에 규칙을 적용한 「추정」(과세표준상한·세부담 상한·조례 가감·감면 미반영 · 주택 한 채 기준 · 공동주택만)
#   종부세는 사람별 전국 합산이라 금액을 내지 않는다 — 공시가격이 공제액(1세대 1주택·일반)을 넘는 호수의 비율만
#   py -3.12 -X utf8 tools/region/ptax-bake.py → data/ptax-dong.json
import json, os, glob, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
RULES = json.load(open(os.path.join(ROOT, 'data', 'tax-rules.json'), encoding='utf-8'))
P, J = RULES['prop'], RULES['jbs']

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
    return [n, [man(x) for x in wq(g, QS)], [man(x) for x in wq(o, QS)], [man(x) for x in wq(gn, QS)], [man(x) for x in wq(on, QS)],
            round(100 * sum(w for p, w in U if p > d9) / n, 1), round(100 * sum(w for p, w in U if p > d1) / n, 1), man(wq(U, (0.5,))[0])]

def main():
    BJ = {}; HJ = collections.defaultdict(list); HJN = collections.Counter(); GU = {}; year = None
    for f in sorted(glob.glob(os.path.join(R, '[0-9]' * 5, 'hp.json'))):
        h = json.load(open(f, encoding='utf-8')); gu = h['gu']; year = h['year']; by = collections.defaultdict(list)
        try: EM = {d['name']: d['k'] for d in json.load(open(os.path.join(R, gu, 'dong.json'), encoding='utf-8'))['dong']}   # 읍·면은 이름이 곧 행정동이다 — hp.json 이 못 이은 「○○읍 △△리」를 읍·면으로 잇는다
        except Exception: EM = {}
        for pnu, e in h['pnu'].items(): by[pnu[:10]] += units(e[2])
        allu = []
        for bjd, U in by.items():
            m = h['bjd'].get(bjd); s = summ(U)
            if not m or not s: continue
            ks = m[6] or [EM[t] for t in m[0].split(' ')[:1] if t[-1:] in '읍면' and t in EM]
            BJ[bjd] = [m[0], gu] + s + [ks]; allu += U
            for k in ks: HJ[k] += U; HJN[k] += 1
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
                    '행정동 값은 그 동에 걸친 법정동의 호수를 모두 합친 근사다(법정동 하나가 여러 행정동에 걸치면 겹쳐 센다) · 도시지역분은 도시지역 안에서만 붙는다(읍·면은 안 붙을 수 있다)'],
           'fields': '값 = [호수, 일반 합계[하위10%·가운데·상위10%], 1세대1주택 합계[같음], 일반 도시지역분 뺀[같음], 1세대1주택 도시지역분 뺀[같음], 일반 공제액 초과 %, 1세대1주택 공제액 초과 %, 공시가격 가운데] · 금액 만 원 · 합계 = 재산세 + 지방교육세 + 도시지역분 · bjd 는 앞에 [이름, 구], 끝에 [행정동 코드] · hjd 는 끝에 걸친 법정동 수',
           'bjd': BJ, 'hjd': {k: summ(U) + [HJN[k]] for k, U in HJ.items()}, 'gu': GU}
    p = os.path.join(ROOT, 'data', 'ptax-dong.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('법정동', len(BJ), '행정동', len(doc['hjd']), '구', len(GU), '바이트', os.path.getsize(p))
    for k in ('1165010100', '1165010800', '4159025900'):
        if k in BJ: print(k, BJ[k][:10])
    print('검산 공시 10억 일반', [round(x) for x in prop(1e9, False)], '1주택', [round(x) for x in prop(1e9, True)], '· 공시 5억 1주택', [round(x) for x in prop(5e8, True)])
if __name__ == '__main__': main()
