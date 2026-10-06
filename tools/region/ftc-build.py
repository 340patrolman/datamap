# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.36.0 — ftc-bake.py 가 받아 둔 공정위 가맹정보(07_API키/out/ftc)를 지도용 data/ftc-brands.json 으로
#   외식 · 가맹점 3곳 이상 · 금액은 원자료 단위(천 원) · 범위값(「12000~14000」)은 가운데 값 · 0 은 「공개 안 함」으로 본다
import json, os, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'ftc'); YR = sys.argv[1] if len(sys.argv) > 1 else '2024'
J = lambda n: json.load(open(os.path.join(OUT, n % YR), encoding='utf-8'))
stats, info, unit = J('stats_%s.json'), J('brandinfo_%s.json'), J('unitsales_%s.json')
alotm = J('alotm_%s.json') if os.path.exists(os.path.join(OUT, 'alotm_%s.json' % YR)) else {}
def mid(s):
    s = str(s or '').replace(',', '').strip()
    if not s or s == '0': return None
    if '~' in s:
        a, b = s.split('~', 1)
        try: return round((float(a) + float(b)) / 2)
        except ValueError: return None
    try: v = float(s); return round(v) if v else None
    except ValueError: return None
inf = {}
for b in info:
    if b.get('indutyLclasNm') == '외식': inf[(b.get('corpNm') or '', b.get('brandNm') or '')] = b
reg = collections.defaultdict(dict)
for u in unit:
    if u.get('indutyLclasNm') != '외식' or not u.get('frcsCnt'): continue
    a, p = mid(u.get('fyerAvrgSlsAmtScopeVal')), mid(u.get('arFyerAvrgSlsAmtScopeVal'))
    if a: reg[u['brandMnno']][u.get('areaNm') or ''] = [u['frcsCnt'], a, p]
cats, CI, out = [], {}, []
for s in stats:
    if s.get('indutyLclasNm') != '외식' or (s.get('frcsCnt') or 0) < 3: continue
    c = (s.get('indutyMlsfcNm') or '').strip()
    if c not in CI: CI[c] = len(cats); cats.append(c)
    b = inf.get((s.get('corpNm') or '', s.get('brandNm') or '')); mn = b['brandMnno'] if b else None
    al = None
    if mn and alotm.get(mn):
        x = alotm[mn][0]; al = [mid(x.get('jngAmtScopeVal')), mid(x.get('eduAmtScopeVal')), mid(x.get('assrncAmtScopeVal')), mid(x.get('etcAmtScopeVal')), mid(x.get('smtnAmtScopeVal'))]
    out.append([s['brandNm'], CI[c], s.get('frcsCnt') or 0, s.get('newFrcsRgsCnt') or 0, s.get('ctrtEndCnt') or 0, s.get('ctrtCncltnCnt') or 0, s.get('avrgSlsAmt') or None, s.get('arUnitAvrgSlsAmt') or None,
                (b or {}).get('majrGdsNm') or '', al, reg.get(mn, {}) if mn else {}])
out.sort(key=lambda r: -r[2])
res = {'schema': 'tg-ftc/1', 'yr': YR, 'source': '공정거래위원회 가맹정보(공공데이터포털 15110241 브랜드별 가맹점 현황 · 15125467 브랜드 목록 · 15125494 단위면적당 평균매출(지역별) · 15125475 가맹점 사업자 부담금 · 이용허락 제한 없음) · %s년 정보공개서 기준(매출은 그 전 해 결산)' % YR,
       'fields': 'b = [브랜드, cats 자리, 가맹점 수, 신규, 계약 종료, 계약 해지, 연 평균매출(천 원), 3.3㎡당 연 평균매출(천 원), 주요 상품, 부담금[가맹금, 교육비, 보증금, 기타, 합계](천 원 · 범위의 가운데) 또는 null, 지역{시도: [가맹점 수, 연 평균매출, 3.3㎡당]}]',
       'note': '정보공개서에 본부가 적은 값 · 평균매출은 가맹점 사업자 평균(본부 매출 아님) · 범위로 공개된 값은 가운데 값 · 기타 부담금에 인테리어·설비가 들어가는 브랜드가 많다(정보공개서 원문 확인)', 'cats': cats, 'b': out}
p = os.path.join(ROOT, 'data', 'ftc-brands.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('브랜드', len(out), '부담금 있음', sum(1 for r in out if r[9]), '지역 있음', sum(1 for r in out if r[10]), os.path.getsize(p))
