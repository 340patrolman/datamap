# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌾 토지 매매 실거래(국토교통부 RTMSDataSvcLandTrade · 공공데이터포털) → data/r/<구>/ltrade.json
#   (소유자 2026-11-16 「향남읍 수직리를 보니 거래가 없어 부동산에 표시되는 것이 없다 — 판단 근거가 될 최근 거래를 · 농지·상가는 거래가 드물다 · 목적을 가지고 찾아갈 수 있게」)
#   받기: LAWD_CD = 시군구 5자리(r/index.json 의 구 코드 그대로 — 화성은 2026 일반구 41591~41597) × 최근 24개월
#   싣는 것: 계약 연월 · 법정동(읍면 리) · 지목 · 용도지역 · 면적㎡ · 금액(만 원) · 지분 거래 여부 · 직거래 여부
#   버리는 것: 지번(국토부가 끝자리를 가린 값 — 자리를 못 잡는다) · 계약 일 · 중개사 소재지 · 해제 거래
#   자리: 법정동·리의 한 점(ri.json 안쪽 점 · 없으면 b2a 캐시 읍면동 경계 가운데) — 「이 리의 거래」까지만 말한다(필지 자리 아님)
#   py -3.12 -X utf8 tools/region/ltrade-bake.py fetch 41591 41593   (구 코드 또는 시도 두 자리)
#   py -3.12 -X utf8 tools/region/ltrade-bake.py build 41591 41593
import json, os, sys, time, urllib.request, statistics, collections
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'ltrade')
END = (2026, 10); NM = 24

def months():
    y, m = END; o = []
    for _ in range(NM):
        o.append('%d%02d' % (y, m)); m -= 1
        if m == 0: y, m = y - 1, 12
    return sorted(o)

def gus(args):
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    return IX, [g for g in IX['gus'] if any(g['gu'] == a or (len(a) == 2 and g['gu'][:2] == a) for a in args)]

def get(url, tries=3):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
        except Exception as e:
            if i == tries - 1: raise RuntimeError(type(e).__name__ + ' ' + str(getattr(e, 'code', '')))   # 주소(열쇠)는 오류 글에 싣지 않는다
            time.sleep(3 * (i + 1))

def fetch(args):
    os.makedirs(OUT, exist_ok=True); key = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']
    IX, G = gus(args); n = 0
    for g in G:
        for ym in months():
            fn = os.path.join(OUT, '%s_%s.json' % (g['gu'], ym))
            if os.path.exists(fn): continue
            rows = []; page = 1
            while True:
                t = get('https://apis.data.go.kr/1613000/RTMSDataSvcLandTrade/getRTMSDataSvcLandTrade?serviceKey=%s&LAWD_CD=%s&DEAL_YMD=%s&numOfRows=1000&pageNo=%d' % (key, g['gu'], ym, page))
                x = ET.fromstring(t); code = (x.findtext('.//resultCode') or '').strip()
                if code not in ('000', '00'): raise RuntimeError('%s %s %s %s' % (g['gu'], ym, code, x.findtext('.//resultMsg')))
                items = [{c.tag: (c.text or '').strip() for c in it} for it in x.iter('item')]; rows += items
                if page * 1000 >= int(x.findtext('.//totalCount') or 0) or not items: break
                page += 1
            json.dump(rows, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); n += 1
            print(g['gu'], g['name'], ym, len(rows), flush=True); time.sleep(0.15)
    print('받은 달', n, flush=True)

def num(s):
    try: return float(str(s).replace(',', ''))
    except Exception: return None

def ring_mid(geom):
    xs = []; ys = []
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for p in polys:
        for x, y in p[0]: xs.append(x); ys.append(y)
    return [round((min(xs) + max(xs)) / 2, 5), round((min(ys) + max(ys)) / 2, 5)]

def positions(gu):
    pos = {}
    try:
        for f in json.load(open(os.path.join(KB, 'out', 'b2a', gu + '.json'), encoding='utf-8')): pos[f['properties']['emd_kor_nm']] = ring_mid(f['geometry'])
    except Exception: pass
    try:
        for r in json.load(open(os.path.join(ROOT, 'data', 'r', gu, 'ri.json'), encoding='utf-8'))['ri']: pos[r['name']] = [round(r['c'][0], 5), round(r['c'][1], 5)]
    except Exception: pass
    return pos

def build(args):
    IX, G = gus(args); gb = {}
    for g in G:
        umds = []; jim = []; uses = []; items = []; n_can = 0
        for ym in months():
            fn = os.path.join(OUT, '%s_%s.json' % (g['gu'], ym))
            if not os.path.exists(fn): continue
            for r in json.load(open(fn, encoding='utf-8')):
                if (r.get('cdealType') or '').strip(): n_can += 1; continue
                amt = num(r.get('dealAmount')); ar = num(r.get('dealArea'))
                if not amt or not ar: continue
                um = r.get('umdNm') or '-'; jm = r.get('jimok') or '-'; us = r.get('landUse') or '-'
                for L, v in ((umds, um), (jim, jm), (uses, us)):
                    if v not in L: L.append(v)
                items.append([int(ym) % 10000, umds.index(um), jim.index(jm), uses.index(us), round(ar, 1) if ar % 1 else int(ar), int(amt), 1 if (r.get('shareDealingType') or '').strip() else 0, 1 if r.get('dealingGbn') == '직거래' else 0])
        if not items: print(g['gu'], g['name'], '거래 없음(받은 달이 없거나 0건)'); continue
        pos0 = positions(g['gu']); pos = []
        for um in umds:
            p = pos0.get(um) or pos0.get(um.split(' ')[-1]) or pos0.get(um.split(' ')[0])
            pos.append(p)
        # 법정동 × 지목 — 지분 아닌 거래의 ㎡당 중앙값(만 원)
        by = collections.defaultdict(list)
        for it in items:
            if not it[6]: by[(it[1], it[2])].append(it[5] / it[4])
        summ = collections.defaultdict(dict)
        for (u, j), v in by.items(): summ[str(u)][str(j)] = [len(v), round(statistics.median(v), 2)]
        doc = {'schema': 'tg-ltrade/1', 'gu': g['gu'],
               'source': '국토교통부 토지 매매 실거래가(공공데이터포털 · RTMSDataSvcLandTrade) %s~%s 계약 · %s 받음' % (months()[0], months()[-1], time.strftime('%Y-%m-%d')),
               'fields': 'items = [계약 연월(YYMM), 법정동(umds 자리), 지목(jimok 자리), 용도지역(uses 자리), 면적㎡, 금액(만 원), 지분 거래 1, 직거래 1] · pos = umds 와 같은 차례의 [경도, 위도](리·읍면동의 한 점 — 필지 자리가 아니다 · 없으면 null) · summ = {법정동: {지목: [지분 아닌 거래 수, ㎡당 중앙값(만 원)]}}',
               'note': '해제 거래 뺌(%d건) · 지번은 국토부가 끝자리를 가려 자리를 못 잡는다 → 법정동·리까지만 · 계약 일·중개사 소재지는 버림 · 지분 거래는 한 필지의 일부 지분이라 단가가 튄다(중앙값에서 뺌 · 목록에는 「지분」 표시) · 평당 = ㎡당 × 3.3058 · 마지막 달은 신고 기한(30일)이 안 지나 덜 찼을 수 있다 · 공장·창고 실거래(RTMSDataSvcInduTrade)는 활용 승인이 없어 없다' % n_can,
               'made': time.strftime('%Y-%m-%d'), 'umds': umds, 'pos': pos, 'jimok': jim, 'uses': uses, 'items': items, 'summ': summ}
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'ltrade.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g['gu']] = os.path.getsize(pth)
        print(g['gu'], g['name'], '거래', len(items), '법정동', len(umds), '자리 없음', sum(1 for p in pos if not p), '크기', gb[g['gu']], flush=True)
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))   # 굽는 사이 다른 도구가 고쳤을 수 있어 다시 읽는다
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['ltrade'] = gb[g['gu']]
    IX['layers']['ltrade'] = '토지 매매 실거래(국토부 · 24개월 · 법정동·리 단위 · 지목·용도지역)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    (fetch if sys.argv[1] == 'fetch' else build)(sys.argv[2:])
