# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.16.0 — 🏠 외국인 부동산(시군구) · KOSIS 한국부동산원
#   외국인주택소유현황 지역별(공동주택) DT_408004_005 — 주택수·지분반영 주택수·소유자수·1인당 평균(가장 최근 기간)
#   부동산거래현황 외국인 거래 토지거래현황 DT_408_2006_S0012 — 필지·면적(달마다 12달)
#   KOSIS 지역 코드(A01·A0101 / …A.0002·…A.00020001) 계층으로 시도를 알고 이름으로 이 지도 시군구에 맞춤 · 시 단위만 있는 곳(경기 일반구 등)은 그 시의 모든 구에 「시 전체」로
#   py -3.12 -X utf8 tools/region/foreign-estate-bake.py → data/foreign-estate.json
import json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KO = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'kosis')
SD = {'서울': '11', '부산': '26', '대구': '27', '인천': '28', '광주': '12', '대전': '30', '울산': '31', '세종': '36', '경기': '41', '강원': '51', '충북': '43', '충남': '44', '전북': '52', '전남': '12', '경북': '47', '경남': '48', '제주': '50'}
def sdcode(nm):
    for k, v in SD.items():
        if nm.startswith(k) or nm.startswith({'충북': '충청북', '충남': '충청남', '전북': '전', '전남': '전라남', '경북': '경상북', '경남': '경상남'}.get(k, k)): pass
    full = {'서울특별시': '11', '부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '광주광역시': '12', '대전광역시': '30', '울산광역시': '31', '세종특별자치시': '36', '경기도': '41', '강원특별자치도': '51', '강원도': '51', '충청북도': '43', '충청남도': '44',
            '전북특별자치도': '52', '전라북도': '52', '전라남도': '12', '경상북도': '47', '경상남도': '48', '제주특별자치도': '50'}
    return SD.get(nm) or full.get(nm)
def num(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); gus = collections.defaultdict(list)
    for g in IX['gus']: gus[g['gu'][:2]].append((g['gu'], g['name']))
    def targets(sd, nm):
        k = nm.replace(' ', '')
        ex = [c for c, n in gus.get(sd, []) if n == k]
        if ex: return ex, 'gu'
        if k.endswith('구') and not k.startswith('('):
            ex = [c for c, n in gus.get(sd, []) if n.endswith(k) and n != k]
            if len(ex) == 1: return ex, 'gu'
        city = [c for c, n in gus.get(sd, []) if n.startswith(nm) and nm.endswith('시')]
        return city, 'city'
    out = collections.defaultdict(dict); miss = set()
    def walk(rows, sido_of, put):
        names = {}
        for r in rows: names[r['C1']] = r['C1_NM']
        for r in rows:
            c = r['C1']; sd = sido_of(c, names)
            if not sd or sd == 'top': continue
            ts, lvl = targets(sd, r['C1_NM'])
            if not ts: miss.add(r['C1_NM']); continue
            for t in ts: put(out[t], r, lvl)
    H = json.load(open(os.path.join(KO, 'DT_408004_005.json'), encoding='utf-8')); last = max(r['PRD_DE'] for r in H)
    def sd_h(c, names): return 'top' if len(c) == 3 else sdcode(names.get(c[:3], ''))
    def put_h(o, r, lvl):
        if r['PRD_DE'] != last: return
        h = o.get('house')
        if h and h['범위'] == 'gu' and lvl == 'city': return
        if not h or (h['범위'] == 'city' and lvl == 'gu' and h.get('_c') != r['C1']): h = o['house'] = {'기간': last, '범위': lvl, '_c': r['C1']}
        h[r['ITM_NM']] = num(r['DT'])
    walk(H, sd_h, put_h)
    L = json.load(open(os.path.join(KO, 'DT_408_2006_S0012.json'), encoding='utf-8'))
    def sd_l(c, names):
        tail = c.split('.')[1]
        return 'top' if len(tail) <= 4 else sdcode(names.get(c.split('.')[0] + '.' + tail[:4], ''))
    def put_l(o, r, lvl):
        l = o.get('land')
        if l and l['범위'] == 'gu' and lvl == 'city': return
        if not l or (l['범위'] == 'city' and lvl == 'gu' and l.get('_c') != r['C1']): l = o['land'] = {'범위': lvl, 'm': {}, '_c': r['C1']}
        l['m'].setdefault(r['PRD_DE'], {})[r['ITM_NM']] = num(r['DT'])
    walk(L, sd_l, put_l)
    doc = {'schema': 'tg-foreign-estate/1', 'source': '한국부동산원 — 외국인주택소유현황 지역별(공동주택 · KOSIS DT_408004_005 · ' + last + ') · 부동산거래현황 외국인 거래 토지거래현황(KOSIS DT_408_2006_S0012 · 달마다)',
           'fields': 'gu = {시군구: {house: {기간, 범위(gu·city = 시 전체 값), 주택수, 지분반영 주택수, 소유자수, 1인당 평균소유주택수, …}, land: {범위, m: {YYYYMM: {필지, 면적(㎡)}}}}}',
           'note': '외국인 = 외국 국적 개인·법인(한국부동산원 정의) · 공동주택만(단독주택은 별도 표) · 「범위 city」 는 일반구가 따로 없어 시 전체 값을 그 시의 구마다 같은 값으로 둔 것', 'gu': out}
    p = os.path.join(ROOT, 'data', 'foreign-estate.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(out), '주택', sum(1 for v in out.values() if 'house' in v), '토지', sum(1 for v in out.values() if 'land' in v), '못 맞춤', sorted(miss)[:20], '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
