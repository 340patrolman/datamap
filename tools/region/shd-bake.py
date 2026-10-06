# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.51.0 — 🏠 단독·다가구 매매 한 건씩(소유자 「지번을 가려도 대략적인 가격대는 근사치로」) → data/r/<구>/shd.json
#   원자료 07_API키/out/home/SHTrade_<구>_<연월>.json(국토부 단독/다가구 매매 실거래 · home-bake.py 가 받은 24개월 · 공공데이터포털)
#   지번은 국토부가 가려서 준다(「8**」 = 800번대) → 좌표를 못 잡아 법정동 단위 · 행정동에는 「이 법정동이 걸친 동」으로 근사(아파트 단지·상업업무용 집합건물 자리에서 본 법정동→행정동)
#   d = [법정동 자리, 0 단독·1 다가구, 지번(가린 그대로), 대지㎡, 연면적㎡, 금액(만 원), 연월, 건축년도] · 해제 거래 뺌
#   b2h = {법정동: {행정동 8자리: 그 동에서 본 단지·건물 수}}
#   py -3.12 -X utf8 tools/region/shd-bake.py
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'home'); R = os.path.join(ROOT, 'data', 'r')
def num(x):
    try: return float(str(x).replace(',', ''))
    except (TypeError, ValueError): return None
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); tot = 0; ng = 0
for g in IX['gus']:
    gu = g['gu']; files = sorted(glob.glob(os.path.join(SRC, 'SHTrade_%s_*.json' % gu)))
    if not files: continue
    umds = []; d = []
    for f in files:
        for r in json.load(open(f, encoding='utf-8')) or []:
            if r.get('cdealType'): continue
            a = num(r.get('dealAmount')); u = (r.get('umdNm') or '').strip()
            if not a or not u: continue
            if u not in umds: umds.append(u)
            d.append([umds.index(u), 1 if r.get('houseType') == '다가구' else 0, r.get('jibun') or '', num(r.get('plottageAr')), num(r.get('totalFloorAr')), int(a), int(r['dealYear']) * 100 + int(r['dealMonth']), int(r['buildYear']) if str(r.get('buildYear') or '').isdigit() else None])
    if not d: continue
    b2h = collections.defaultdict(collections.Counter)
    hp = os.path.join(R, gu, 'home.json')
    if os.path.exists(hp):
        H = json.load(open(hp, encoding='utf-8'))
        for c in H['cx'].values():
            if c[6] and H['umds'][c[2]]: b2h[H['umds'][c[2]]][c[6]] += 1
    rp = os.path.join(R, gu, 'rtms.json')
    if os.path.exists(rp):
        T = json.load(open(rp, encoding='utf-8'))
        for it in T['items']:
            if it[9] and it[11] is not None: b2h[T['umds'][it[11]]][it[9]] += 1
    doc = {'schema': 'tg-shd/1', 'gu': gu, 'source': '국토교통부 단독/다가구 매매 실거래가(공공데이터포털 · RTMSDataSvcSHTrade · 최근 24개월 계약 · 해제 거래 뺌)', 'fields': 'd = [법정동(umds 자리), 0 단독·1 다가구, 지번(국토부가 가린 그대로 · 「8**」 = 800번대), 대지㎡, 연면적㎡, 금액(만 원), 연월, 건축년도] · b2h = {법정동: {행정동 8자리: 그 동에서 본 단지·건물 수}}',
           'note': '지번이 가려져 자리를 못 잡는다 — 행정동 값은 「이 동에 걸친 법정동」 전체 거래로 본 근사', 'umds': umds, 'd': d, 'b2h': {k: dict(v) for k, v in b2h.items()}}
    fn = os.path.join(R, gu, 'shd.json'); json.dump(doc, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); g.setdefault('bytes', {})['shd'] = os.path.getsize(fn); tot += len(d); ng += 1
IX.setdefault('layers', {})['shd'] = '단독·다가구 매매 한 건씩(법정동 · 지번 가림 · 근사)'
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', ng, '거래', tot)
