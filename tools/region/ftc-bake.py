# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.36.0 — 🏷 브랜드(가맹) 손익 기본값 · 공정거래위원회 가맹정보(공공데이터포털 · 이용허락 제한 없음)
#   ① 브랜드별 가맹점 현황 15110241(FftcBrandFrcsStatsService/getBrandFrcsStats · yr) — 가맹점 수 · 신규 · 계약 종료·해지 · 연 평균매출(천 원) · 3.3㎡당 평균매출(천 원)
#   ② 브랜드 목록 15125467(FftcBrandRlsInfo2_Service/getBrandinfo) — 브랜드 관리번호 · 주요 상품
#   ③ 단위면적당 평균매출(지역별) 15125494(FftcBrandFrcsUnitAvrSalInfo3_Service/getbrandFrcsBzmnAvrgsls2) — 지역마다 연 평균매출·평당 범위
#   ④ 가맹점 부담금 15125475(FftcBrandFrcsAlotmInfo2_Service/getbrandFrcsbzmnAlotminfo · brandMnno 필수) — 가맹비·교육비·보증금·기타·인테리어 등
#   외식만 · ④는 가맹점 5곳 이상 브랜드만 · 원자료 07_API키/out/ftc/ · 결과 data/ftc-brands.json
#   py -3.12 -X utf8 tools/region/ftc-bake.py [기준년도]
import json, os, sys, time, urllib.request, urllib.parse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'ftc'); os.makedirs(OUT, exist_ok=True)
YR = sys.argv[1] if len(sys.argv) > 1 else '2024'
k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']
if isinstance(k, dict): k = k.get('decoding') or urllib.parse.unquote(k.get('encoding', ''))
if '%' in k: k = urllib.parse.unquote(k)

def call(path, prm, rows=1000):
    out, page = [], 1
    while True:
        u = 'https://apis.data.go.kr/1130000/' + path + '?' + urllib.parse.urlencode(dict({'serviceKey': k, 'pageNo': page, 'numOfRows': rows, 'resultType': 'json'}, **prm))
        for i in range(4):
            try: j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read().decode('utf-8', 'replace')); break
            except Exception as e: time.sleep(3 + 3 * i); j = None
        if not j or j.get('resultCode') != '00': return out if out else None
        it = j.get('items') or []; out += it
        if len(out) >= int(j.get('totalCount') or 0) or not it: return out
        page += 1; time.sleep(0.15)

def cached(name, fn):
    p = os.path.join(OUT, name)
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    v = fn(); json.dump(v, open(p, 'w', encoding='utf-8'), ensure_ascii=False); return v

stats = cached('stats_%s.json' % YR, lambda: call('FftcBrandFrcsStatsService/getBrandFrcsStats', {'yr': YR}))
info = cached('brandinfo_%s.json' % YR, lambda: call('FftcBrandRlsInfo2_Service/getBrandinfo', {'jngBizCrtraYr': YR}))
unit = cached('unitsales_%s.json' % YR, lambda: call('FftcBrandFrcsUnitAvrSalInfo3_Service/getbrandFrcsBzmnAvrgsls2', {'jngBizCrtraYr': YR}))
print('현황', len(stats), '목록', len(info), '지역별', len(unit))
food = [s for s in stats if s.get('indutyLclasNm') == '외식']
byname = collections.defaultdict(list)
for b in info:
    if b.get('indutyLclasNm') == '외식': byname[(b.get('corpNm') or '', b.get('brandNm') or '')].append(b)
reg = collections.defaultdict(dict)
for u in unit:
    if u.get('indutyLclasNm') != '외식': continue
    reg[u['brandMnno']][u.get('areaNm') or ''] = [u.get('frcsCnt') or 0, u.get('fyerAvrgSlsAmtScopeVal') or '', u.get('arFyerAvrgSlsAmtScopeVal') or '', u.get('acntgYr') or '']
apath = os.path.join(OUT, 'alotm_%s.json' % YR); alotm = json.load(open(apath, encoding='utf-8')) if os.path.exists(apath) else {}
todo = []
for s in food:
    if (s.get('frcsCnt') or 0) < 5: continue
    b = byname.get((s.get('corpNm') or '', s.get('brandNm') or ''))
    if b and b[0]['brandMnno'] not in alotm: todo.append(b[0]['brandMnno'])
print('부담금 받을 브랜드', len(todo))
for i, mn in enumerate(todo):
    r = call('FftcBrandFrcsAlotmInfo2_Service/getbrandFrcsbzmnAlotminfo', {'jngBizCrtraYr': YR, 'brandMnno': mn}, rows=50)
    alotm[mn] = r or []
    if i % 100 == 0: json.dump(alotm, open(apath, 'w', encoding='utf-8'), ensure_ascii=False); print(' ', i, flush=True)
json.dump(alotm, open(apath, 'w', encoding='utf-8'), ensure_ascii=False)
ex = next((v for v in alotm.values() if v), None); print('부담금 예', json.dumps(ex[:2] if ex else None, ensure_ascii=False)[:600])
