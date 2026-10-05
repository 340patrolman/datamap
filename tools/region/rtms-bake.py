# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 🏢 상업업무용 부동산 매매 실거래(국토교통부 RTMSDataSvcNrgTrade · data.go.kr 15126463 · 활용 승인 2026-10-04)
#   받기: 서울·경기 72개 구(r/index.json) × 최근 24개월 · LAWD_CD = 시군구 5자리(구 전체가 온다 — 동 거름은 여기서)
#   자리: 지번 → 브이월드 주소 좌표(getcoord parcel) · 응답의 level4AC(행정동 코드)로 법정동→행정동 판정(설계서 2장 구현 규칙)
#         일반건물은 지번이 가려져 온다(예: 1**) → 좌표 없음 · 법정동까지만(격자에 넣지 않는다 — 가짜 정밀도 금지)
#   격자: 국가지점번호식 250m(EPSG:5179) — tools/region/grid250.py
#   개인정보: 매수·매도 구분(개인/법인)·중개사 소재지·거래일(일)은 버린다 → 연·월만
#   py -3.12 -X utf8 tools/region/rtms-bake.py fetch  → 07_API키/out/rtms/nrg_<구>_<YYYYMM>.json · geo.json
#   py -3.12 -X utf8 tools/region/rtms-bake.py build  → data/r/<구>/rtms.json · r/index.json bytes.rtms
import json, os, sys, time, urllib.request, urllib.parse, re, statistics, collections, importlib.util
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'rtms')
sp0 = importlib.util.spec_from_file_location('rc', os.path.join(ROOT, 'tools', 'region', 'regcfg.py')); RC = importlib.util.module_from_spec(sp0); sp0.loader.exec_module(RC)   # 시도 이름(v2.7.0)
sp = importlib.util.spec_from_file_location('g250', os.path.join(ROOT, 'tools', 'region', 'grid250.py')); G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)
END = (2026, 8); NM = 24
def months():
    y, m = END; o = []
    for _ in range(NM): o.append('%d%02d' % (y, m)); m -= 1; y, m = (y - 1, 12) if m == 0 else (y, m)
    return sorted(o)
def keys(): return json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))

def get(url, tries=4):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
        except Exception as e:
            if i == tries - 1: raise
            time.sleep(3 * (i + 1))

def fetch_nrg(gu, ym, key):
    rows = []; page = 1
    while True:
        u = 'https://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade?serviceKey=%s&LAWD_CD=%s&DEAL_YMD=%s&numOfRows=1000&pageNo=%d' % (key, gu, ym, page)
        t = get(u); x = ET.fromstring(t)
        code = (x.findtext('.//resultCode') or '').strip()
        if code not in ('000', '00'): raise RuntimeError('%s %s %s %s' % (gu, ym, code, x.findtext('.//resultMsg')))
        items = [{c.tag: (c.text or '').strip() for c in it} for it in x.iter('item')]; rows += items
        tot = int(x.findtext('.//totalCount') or 0)
        if page * 1000 >= tot or not items: return rows
        page += 1

def fetch():
    os.makedirs(OUT, exist_ok=True); K = keys(); dk = K['data_go_kr']
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    n = 0
    for g in IX['gus']:
        for ym in months():
            fn = os.path.join(OUT, 'nrg_%s_%s.json' % (g['gu'], ym))
            if os.path.exists(fn): continue
            r = fetch_nrg(g['gu'], ym, dk); json.dump(r, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); n += 1
            print('nrg', g['gu'], g['name'], ym, len(r), flush=True); time.sleep(0.15)
    print('받은 달', n, flush=True)
    geocode(K['vworld'], IX)

def addr_of(r, sdnm):
    j = r.get('jibun', '')
    if not j or '*' in j: return None
    return '%s %s %s %s' % (sdnm, r.get('sggNm', ''), r.get('umdNm', ''), j)

def geocode(vk, IX):
    gp = os.path.join(OUT, 'geo.json'); geo = json.load(open(gp, encoding='utf-8')) if os.path.exists(gp) else {}
    want = set()
    for g in IX['gus']:
        sd = RC.NAME[g['gu'][:2]]
        for ym in months():
            fn = os.path.join(OUT, 'nrg_%s_%s.json' % (g['gu'], ym))
            if not os.path.exists(fn): continue
            for r in json.load(open(fn, encoding='utf-8')):
                a = addr_of(r, sd)
                if a and a not in geo: want.add(a)
    print('좌표 찾을 지번', len(want), '이미', len(geo), flush=True); k = 0
    for a in sorted(want):
        q = {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326', 'address': a, 'refine': 'true', 'simple': 'false', 'format': 'json', 'type': 'parcel', 'key': vk}
        try:
            j = json.loads(get('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q)))['response']
            if j.get('status') == 'OK':
                st = j['refined']['structure']; pt = j['result']['point']
                geo[a] = [round(float(pt['y']), 6), round(float(pt['x']), 6), st.get('level4LC', '')[:10], st.get('level4A', ''), st.get('level4AC', '')[:10]]
            else: geo[a] = None
        except Exception as e:
            print('geo 오류', a, e, flush=True); continue
        k += 1
        if k % 200 == 0: json.dump(geo, open(gp, 'w', encoding='utf-8'), ensure_ascii=False); print('geo', k, flush=True)
        time.sleep(0.05)
    json.dump(geo, open(gp, 'w', encoding='utf-8'), ensure_ascii=False); print('geo 끝', len(geo), '못 찾음', sum(1 for v in geo.values() if v is None), flush=True)

def num(s):
    try: return float(str(s).replace(',', ''))
    except Exception: return None

def build():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    geo = json.load(open(os.path.join(OUT, 'geo.json'), encoding='utf-8'))
    tot = collections.Counter(); gb = {}; m2a = collections.defaultdict(collections.Counter)
    for g in IX['gus']:
        sd = RC.NAME[g['gu'][:2]]
        uses = []; umds = []; items = []; cells = collections.defaultdict(list)
        for ym in months():
            fn = os.path.join(OUT, 'nrg_%s_%s.json' % (g['gu'], ym))
            if not os.path.exists(fn): continue
            for r in json.load(open(fn, encoding='utf-8')):
                if (r.get('cdealType') or '').strip(): tot['해제'] += 1; continue   # 해제된 거래는 뺀다
                amt = num(r.get('dealAmount')); ar = num(r.get('buildingAr')); pa = num(r.get('plottageAr'))
                if not amt: continue
                u = r.get('buildingUse') or '-'; um = r.get('umdNm') or '-'
                if u not in uses: uses.append(u)
                if um not in umds: umds.append(um)
                typ = 0 if r.get('buildingType') == '집합' else 1
                a = addr_of(r, sd); gc = geo.get(a) if a else None
                lat = lon = k8 = cell = None
                if gc:
                    lat, lon = gc[0], gc[1]; k8 = (gc[4] or '')[:8] or None; cell = G.code_ll(lat, lon)
                    if gc[2] and gc[4]: m2a[gc[2][:10]][gc[4][:10]] += 1
                fl = r.get('floor') or ''
                items.append([int(ym), uses.index(u), typ, int(num(fl)) if num(fl) is not None else None, ar, pa, int(amt), lat, lon, k8, cell, umds.index(um), int(num(r.get('buildYear')) or 0) or None])
                tot['거래'] += 1; tot['좌표' if lat else '좌표없음'] += 1
                if cell and ar and typ == 0: cells[cell].append(amt / ar)
        if not items: continue
        gcells = {c: [len(v), round(statistics.median(v), 1)] for c, v in cells.items()}
        doc = {'schema': 'tg-rtms/1', 'gu': g['gu'],
               'source': '국토교통부 상업업무용 부동산 매매 실거래가(data.go.kr 15126463 · RTMSDataSvcNrgTrade) %s~%s 계약 · 자리 = 브이월드 지번 좌표 · %s 받음' % (months()[0], months()[-1], time.strftime('%Y-%m-%d')),
               'fields': '[계약 연월, 용도(uses), 0 집합·1 일반, 층, 건물면적㎡(집합 = 전용), 대지면적㎡, 거래금액(만 원), 위도, 경도, 행정동 8자리(지번 좌표로 판정), 250m 격자, 법정동(umds), 건축년도]',
               'note': '해제 거래 뺌 · 일반건물은 지번이 가려져 좌표 없음(법정동까지만) · 매수·매도 구분·중개사·일자는 버림 · 격자 값 = 집합건물 ㎡당 거래금액 중앙값(만 원 · 전용 기준 · 평당 = ×3.3058)',
               'uses': uses, 'umds': umds, 'items': items, 'grid': gcells}
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'rtms.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g['gu']] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['rtms'] = gb[g['gu']]
    IX['layers']['rtms'] = '상업업무용 매매 실거래(국토부 · 24개월 · 250m 격자 중앙값)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    # 법정동 → 행정동(지번 좌표로 본 것 · 거래가 있던 자리만) — 전체 표는 grid250 의 법정동 표와 함께 data/b2a.json
    json.dump({k: dict(v) for k, v in m2a.items()}, open(os.path.join(OUT, 'b2a_from_rtms.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    print(dict(tot), '구', len(gb), '바이트', sum(gb.values()))

if __name__ == '__main__':
    {'fetch': fetch, 'build': build, 'geo': lambda: geocode(keys()['vworld'], json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')))}[sys.argv[1]]()
