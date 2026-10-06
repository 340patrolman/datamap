# v2.60.0 서울 상권분석서비스 매출을 「한 달 평균」으로 — 소유자 「일단 잘 모르니 진행하면서 고쳐 가자」(2026-10-06)
#   서울시 상권분석서비스 추정매출의 THSMON_SELNG_AMT(당월_매출_금액)·THSMON_SELNG_CO 와 시간대·연령·성별·요일 금액·건수는 **한 분기(3달) 합계**다.
#   근거(2026-10-06 실측): 서울 1,650 상권 100업종 합 23.4조 — 한 달이면 전국 카드 승인(월 약 90조)의 4분의 1이라 말이 안 되고, 분기면 월 7.8조(약 8.5%)
#     · 한식 3.9조 — 한 달이면 전국 한식 시장의 3분의 2 · 분기면 월 1.3조(약 21% · 서울 인구 몫 19%와 맞음)
#     · 점포당 한식 가운데 5,760만 ÷ 3 = 1,920만 ≈ KREI 업종 평균 월 2,308만 · 편의점 점포당 건수 53,266 ÷ 91일 = 하루 585건
#     · 열린데이터광장 OA-15572 설명 「분기당 매출 금액은 개인 매출액과 법인 매출액의 합산값」
#   종전 굽기 파일은 그 합계를 「한 달」로 적어 3배 컸다 → 이미 구운 파일의 금액·건수를 ÷ 3(반올림) 하고 표시(perMonth: 1)를 남긴다. 두 번 돌려도 다시 나누지 않는다.
#   점포 수·개업·폐업·유동·직장·상주·집객시설·변화지표는 그대로.
#   ⚠ trdar-bake·dong-bake·flow-bake·trend-bake 로 새로 구우면 반드시 이 도구를 다시 돌린다 — 그 뒤 profile-bake 11.
#   py -3.12 -X utf8 tools/region/q3-fix.py
import json, os, glob

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
NOTE = '금액·건수는 서울시 상권분석서비스 분기 합계 ÷ 3 = 한 달 평균(datamap v2.60.0 q3-fix)'
q = lambda x: round(x / 3) if isinstance(x, (int, float)) and not isinstance(x, bool) else x
ql = lambda a: [q(x) for x in a] if isinstance(a, list) else a
def row(r): return [r[0]] + [q(x) for x in r[1:]]   # [이름, 숫자…]
n = {'files': 0, 'skip': 0}

def rw(p, fn):
    if not os.path.exists(p): return
    j = json.load(open(p, encoding='utf-8'))
    if j.get('perMonth'): n['skip'] += 1; return
    fn(j); j['perMonth'] = 1; j['perMonthNote'] = NOTE
    open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(j, ensure_ascii=False, separators=(',', ':'))); n['files'] += 1

def trdar(j):   # tg-trdar/1·2 — 상권마다 ind(업종 줄) · indp(1년 전) · tr(분기 추이)
    for t in j.get('trdar', []):
        if 'ind' in t: t['ind'] = [row(r) for r in t['ind']]
        if 'indp' in t: t['indp'] = {k: ql(v) for k, v in t['indp'].items()}
        if 'tr' in t: t['tr'] = {k: ql(v) for k, v in t['tr'].items()}
    if isinstance(j.get('dong'), dict): j['dong'] = {k: [row(r) for r in v] for k, v in j['dong'].items()}
    if isinstance(j.get('fields'), dict):
        for k in ('ind', 'indp', 'tr'):
            if k in j['fields']: j['fields'][k] = j['fields'][k].replace('매출(만원)', '한 달 평균 매출(만원 · 분기 ÷ 3)').replace('} 만원', '} 만원 · 한 달 평균(분기 ÷ 3)')

def sales(s):   # {amt, cnt, tb, dw, top}
    if not isinstance(s, dict): return s
    for k in ('amt', 'cnt'):
        if k in s: s[k] = q(s[k])
    for k in ('tb', 'dw'):
        if k in s: s[k] = ql(s[k])
    if 'top' in s: s['top'] = [row(r) for r in s['top']]
    return s

def dong(j):
    for d in j.get('dong', []):
        if d.get('sales'): sales(d['sales'])
    if isinstance(j.get('source'), dict) and '매출' in j['source']: j['source']['매출'] += ' · 한 달 평균(분기 합계 ÷ 3)'

def dongx(j):
    for v in j.get('dong', {}).values():
        if 'ind' in v: v['ind'] = [row(r) for r in v['ind']]
        if 'tr' in v: v['tr'] = [ql(r) if r else r for r in v['tr']]

def flow(j):   # sales = {source, quarter, tb, items: {동: {amt, cnt, tb, dw, top}}}
    for v in j['sales']['items'].values(): sales(v)
    j['sales']['source'] += ' · 한 달 평균(분기 합계 ÷ 3)'

def trend(j):   # sales = {source, quarters, items: {동: {분기: [매출, 시간대 6, 주점류]}}}
    for v in j['sales']['items'].values():
        for qq in list(v): v[qq] = ql(v[qq])
    j['sales']['source'] = j['sales']['source'].replace('— 분기 · 만원', '— 분기마다 · 만원 · 한 달 평균(분기 합계 ÷ 3)')

BZ = {1, 2, 7} | set(range(9, 22))   # [상권 번호, 매출, 건수, 점포, 프랜차이즈, 개업, 폐업, 1년 전 매출, 1년 전 점포, 시간대 매출 6, 연령 매출 6, 주말 매출]
def biz(j): j['rows'] = [[q(x) if i in BZ and x is not None else x for i, x in enumerate(r)] for r in j['rows']]
def bizidx(j):
    for m in j['trdar']:
        if m and len(m) > 13: m[13] = q(m[13])
    for c in j['inds']: c[3] = q(c[3])
    j['meta'] = j['meta'].replace('한 달 매출 계(만원)', '한 달 평균 매출 계(만원 · 분기 ÷ 3)'); j['row'] = j['row'].replace('매출(만원)', '한 달 평균 매출(만원 · 분기 ÷ 3)')

rw(os.path.join(D, 'trdar-seocho.json'), trdar)
rw(os.path.join(D, 'flow-seocho.json'), flow)
rw(os.path.join(D, 'trend-seocho.json'), trend)
for g in sorted(glob.glob(os.path.join(D, 'r', '11*'))):
    rw(os.path.join(g, 'trdar.json'), trdar); rw(os.path.join(g, 'dong.json'), dong); rw(os.path.join(g, 'dongx.json'), dongx)
for p in sorted(glob.glob(os.path.join(D, 'r', 'biz', 'CS*.json'))): rw(p, biz)
rw(os.path.join(D, 'r', 'biz', 'index.json'), bizidx)
print('고친 파일', n['files'], '· 이미 고친 파일', n['skip'])
