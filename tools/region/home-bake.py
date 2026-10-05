# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.5.0 — 🏠 주택 실거래(국토교통부 · data.go.kr 활용 승인 2026-10-05 · 8종)
#   아파트·오피스텔·연립다세대 매매(24개월)·전월세(12개월) → 지번 → 브이월드 좌표 → 250m 국가표준격자 · 단지(건물)별 · 행정동별
#   단독·다가구는 국토부가 지번을 가리거나(2**) 주지 않는다 → 법정동 단위로만(격자에 넣지 않는다 — 가짜 정밀도 금지)
#   지표(설계서 4장): 평당가 = 거래금액 ÷ 전용㎡ × 3.3058(「전용 기준」) · 전세가율 = 같은 자리 전세 ㎡당 중앙값 ÷ 매매 ㎡당 중앙값(아파트 · 추정)
#   개인정보·식별 줄이기: 매수·매도 구분·중개사·일자·층·동(棟) 번호는 버린다 → 연월·면적·금액만
#   py -3.12 -X utf8 tools/region/home-bake.py fetch → 07_API키/out/home/ · geo → 좌표(브이월드 · 하루 한도가 넘으면 다음 날 이어서) · build → data/r/<구>/home.json
import json, os, sys, time, urllib.request, urllib.parse, re, statistics, collections, importlib.util
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'home'); GEO = os.path.join(KB, 'out', 'rtms', 'geo.json')
sp = importlib.util.spec_from_file_location('g250', os.path.join(ROOT, 'tools', 'region', 'grid250.py')); G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)
END = (2026, 8)
SVC = {'AptTrade': 24, 'OffiTrade': 24, 'RHTrade': 24, 'SHTrade': 24, 'AptRent': 12, 'OffiRent': 12, 'RHRent': 12, 'SHRent': 12}
KEEP = ['aptNm', 'offiNm', 'mhouseNm', 'umdNm', 'jibun', 'buildYear', 'dealAmount', 'deposit', 'monthlyRent', 'excluUseAr', 'totalFloorAr', 'plottageAr', 'landAr', 'houseType', 'dealYear', 'dealMonth', 'cdealType', 'contractType']
def months(n):
    y, m = END; o = []
    for _ in range(n): o.append('%d%02d' % (y, m)); m -= 1; y, m = (y - 1, 12) if m == 0 else (y, m)
    return sorted(o)
def keys(): return json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))
def get(url, tries=4):
    for i in range(tries):
        try: return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read().decode('utf-8', 'replace')
        except Exception:
            if i == tries - 1: raise
            time.sleep(4 * (i + 1))
def gu_name(g):   # 경기 「수원시장안구」 → 「수원시 장안구」(주소 검색용)
    return re.sub(r'^(\S+?시)(\S+구)$', r'\1 \2', g['name'])

def fetch(only=None):
    os.makedirs(OUT, exist_ok=True); dk = keys()['data_go_kr']; IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    for svc, n in SVC.items():
        if only and svc not in only: continue
        for g in IX['gus']:
            for ym in months(n):
                fn = os.path.join(OUT, '%s_%s_%s.json' % (svc, g['gu'], ym))
                if os.path.exists(fn): continue
                rows = []; page = 1
                while True:
                    t = get('https://apis.data.go.kr/1613000/RTMSDataSvc%s/getRTMSDataSvc%s?serviceKey=%s&LAWD_CD=%s&DEAL_YMD=%s&numOfRows=1000&pageNo=%d' % (svc, svc, dk, g['gu'], ym, page))
                    x = ET.fromstring(t); code = (x.findtext('.//resultCode') or '').strip()
                    if code not in ('000', '00'): raise RuntimeError('%s %s %s %s %s' % (svc, g['gu'], ym, code, x.findtext('.//resultMsg')))
                    items = [{c.tag: (c.text or '').strip() for c in it if c.tag in KEEP} for it in x.iter('item')]; rows += items
                    if page * 1000 >= int(x.findtext('.//totalCount') or 0) or not items: break
                    page += 1
                json.dump(rows, open(fn + '.tmp', 'w', encoding='utf-8'), ensure_ascii=False); os.replace(fn + '.tmp', fn); time.sleep(0.1)
            print(svc, g['gu'], g['name'], flush=True)
    print('받기 끝', flush=True)

def addr(g, r):
    j = r.get('jibun', '')
    if not j or '*' in j: return None
    return '%s %s %s %s' % ('서울특별시' if g['gu'][:2] == '11' else '경기도', gu_name(g), r.get('umdNm', ''), j)

def geocode():
    vk = keys()['vworld']; IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    geo = json.load(open(GEO, encoding='utf-8')) if os.path.exists(GEO) else {}
    pri = collections.Counter()   # 거래가 많은 지번부터(하루 한도에 걸려도 중요한 자리가 먼저)
    for g in IX['gus']:
        for svc, n in SVC.items():
            if svc.startswith('SH'): continue
            for ym in months(n):
                fn = os.path.join(OUT, '%s_%s_%s.json' % (svc, g['gu'], ym))
                if not os.path.exists(fn): continue
                for r in json.load(open(fn, encoding='utf-8')):
                    a = addr(g, r)
                    if a and a not in geo: pri[a] += 1
    want = [a for a, _ in pri.most_common()]; print('좌표 찾을 지번', len(want), '이미', len(geo), flush=True); k = 0; stop = 0
    for a in want:
        q = {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326', 'address': a, 'refine': 'true', 'simple': 'false', 'format': 'json', 'type': 'parcel', 'key': vk}
        try:
            j = json.loads(get('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q)))['response']
            if j.get('status') == 'OK':
                st = j['refined']['structure']; pt = j['result']['point']
                geo[a] = [round(float(pt['y']), 6), round(float(pt['x']), 6), st.get('level4LC', '')[:10], st.get('level4A', ''), st.get('level4AC', '')[:10]]
            elif j.get('status') == 'NOT_FOUND': geo[a] = None
            else:
                print('geo 멈춤', j.get('status'), j.get('error'), flush=True); stop += 1
                if stop >= 3: break
                time.sleep(10); continue
        except Exception as e:
            print('geo 오류', e, flush=True); continue
        k += 1
        if k % 500 == 0: json.dump(geo, open(GEO, 'w', encoding='utf-8'), ensure_ascii=False); print('geo', k, flush=True)
        time.sleep(0.03)
    json.dump(geo, open(GEO, 'w', encoding='utf-8'), ensure_ascii=False); print('geo 끝', k, '전체', len(geo), flush=True)

def num(s):
    try: return float(str(s).replace(',', ''))
    except Exception: return None
def med(a): return round(statistics.median(a)) if a else None

def build():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); geo = json.load(open(GEO, encoding='utf-8'))
    TY = {'Apt': 0, 'Offi': 1, 'RH': 2}; NMK = {'Apt': 'aptNm', 'Offi': 'offiNm', 'RH': 'mhouseNm'}
    tot = collections.Counter(); gb = {}
    for g in IX['gus']:
        umds = []; cx = {}; cell = collections.defaultdict(lambda: collections.defaultdict(list)); dong = collections.defaultdict(lambda: collections.defaultdict(list)); sh = collections.defaultdict(lambda: collections.defaultdict(list))
        def U(u):
            if u not in umds: umds.append(u)
            return umds.index(u)
        for svc, n in SVC.items():
            kind = re.match(r'(Apt|Offi|RH|SH)(Trade|Rent)', svc); typ, tr = kind.group(1), kind.group(2) == 'Trade'
            for ym in months(n):
                fn = os.path.join(OUT, '%s_%s_%s.json' % (svc, g['gu'], ym))
                if not os.path.exists(fn): continue
                for r in json.load(open(fn, encoding='utf-8')):
                    if r.get('cdealType'): tot['해제'] += 1; continue
                    um = r.get('umdNm') or '-'
                    if typ == 'SH':   # 단독·다가구 — 법정동까지만
                        ar = num(r.get('totalFloorAr'))
                        if tr:
                            amt = num(r.get('dealAmount'))
                            if amt and ar: sh[U(um)]['t'].append(amt / ar)
                        else:
                            dep = num(r.get('deposit')) or 0; mr = num(r.get('monthlyRent')) or 0
                            (sh[U(um)]['j'] if mr == 0 else sh[U(um)]['w']).append(dep if mr == 0 else mr)
                        tot['단독·다가구'] += 1; continue
                    ar = num(r.get('excluUseAr'))
                    if not ar: continue
                    a = addr(g, r); gc = geo.get(a) if a else None
                    cid = '%d|%s|%s' % (TY[typ], um, r.get('jibun', ''))
                    c = cx.get(cid)
                    if not c:
                        lat = lon = k8 = cl = None
                        if gc: lat, lon, k8, cl = gc[0], gc[1], (gc[4] or '')[:8] or None, G.code_ll(gc[0], gc[1])
                        c = cx[cid] = {'t': TY[typ], 'n': r.get(NMK[typ]) or '', 'u': U(um), 'lat': lat, 'lon': lon, 'k8': k8, 'cell': cl, 'by': num(r.get('buildYear')), 'tr': [], 'last': None, 'je': [], 'wo': [], 'wd': []}
                    if tr:
                        amt = num(r.get('dealAmount'))
                        if not amt: continue
                        c['tr'].append(amt / ar); ym2 = int(r['dealYear']) * 100 + int(r['dealMonth'])
                        if not c['last'] or ym2 > c['last'][0]: c['last'] = [ym2, int(amt), round(ar, 1)]
                        tot['매매'] += 1
                    else:
                        dep = num(r.get('deposit')) or 0; mr = num(r.get('monthlyRent')) or 0
                        if mr == 0: c['je'].append(dep / ar)
                        else: c['wo'].append(mr); c['wd'].append(dep)
                        tot['전월세'] += 1
                    tot['좌표' if c['lat'] else '좌표없음'] += 1
        out = {}
        for cid, c in cx.items():
            row = [c['t'], c['n'], c['u'], c['lat'], c['lon'], c['cell'], c['k8'], int(c['by']) if c['by'] else None,
                   [len(c['tr']), med(c['tr'])] + (c['last'] or [None, None, None]), [len(c['je']), med(c['je'])], [len(c['wo']), med(c['wo']), med(c['wd'])]]
            if c['lat']: out[str(len(out))] = row   # 지도에 점을 찍을 수 있는 단지만 목록에 둔다(좌표 없는 것은 칸·동 집계에도 못 들어간다 — 좌표가 차면 다음 build 에 들어온다)
            for key, bucket in ((c['cell'], cell), (c['k8'], dong)):
                if not key: continue
                b = bucket[key]; p = ('a' if c['t'] == 0 else 'o' if c['t'] == 1 else 'r')
                b[p + 't'] += c['tr']; b[p + 'j'] += c['je']; b[p + 'w'] += c['wo']
        def agg(b):
            o = {}
            for p in 'aor':
                t, j, w = b.get(p + 't', []), b.get(p + 'j', []), b.get(p + 'w', [])
                if t or j or w: o[p] = [len(t), med(t), len(j), med(j), len(w), med(w), round(med(j) / med(t) * 100) if t and j and len(t) >= 3 and len(j) >= 3 else None]
            return o
        doc = {'schema': 'tg-home/1', 'gu': g['gu'],
               'source': '국토교통부 실거래가(공공데이터포털 · 아파트·오피스텔·연립다세대·단독다가구 매매 %s~%s · 전월세 %s~%s) · 자리 = 브이월드 지번 좌표 · %s 받음' % (months(24)[0], months(24)[-1], months(12)[0], months(12)[-1], time.strftime('%Y-%m-%d')),
               'fields': 'cx = {번호: [0 아파트·1 오피스텔·2 연립다세대, 이름, 법정동(umds), 위도, 경도, 250m 칸, 행정동 8자리, 건축년도, [매매 건수, ㎡당 중앙값(만 원 · 전용), 마지막 연월, 마지막 금액(만 원), 그 면적㎡], [전세 건수, ㎡당 보증금 중앙값], [월세 건수, 월세 중앙값(만 원), 보증금 중앙값]]} · grid·dong = {칸/동: {a 아파트·o 오피스텔·r 연립다세대: [매매 n, 매매 ㎡당, 전세 n, 전세 ㎡당, 월세 n, 월세 중앙값, 전세가율 %]}} · sh = {법정동: [매매 n, 연면적 ㎡당 중앙값, 전세 n, 보증금 중앙값, 월세 n, 월세 중앙값]}',
               'note': '해제 거래 뺌 · 매수·매도 구분·중개사·일자·층·동 번호는 버림 · 평당 = ㎡당 × 3.3058(전용 기준) · 전세가율 = 같은 자리 전세 ㎡당 중앙값 ÷ 매매 ㎡당 중앙값(같은 집끼리가 아니다 — 추정) · 전세 = 월세 0 인 계약 · 단독·다가구는 지번이 가려져 법정동 단위',
               'umds': umds, 'cx': out, 'grid': {k: agg(v) for k, v in cell.items()}, 'dong': {k: agg(v) for k, v in dong.items()},
               'sh': {str(k): [len(v['t']), med(v['t']), len(v['j']), med(v['j']), len(v['w']), med(v['w'])] for k, v in sh.items()}}
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'home.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g['gu']] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['home'] = gb[g['gu']]
    IX['layers']['home'] = '주택 실거래(아파트·오피스텔·연립다세대 · 250m 칸·단지 · 평당·전세가율)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print(dict(tot), '구', len(gb), '바이트', sum(gb.values()))

if __name__ == '__main__':
    fetch(sys.argv[2:]) if sys.argv[1] == 'fetch' else {'geo': geocode, 'build': build}[sys.argv[1]]()   # fetch AptRent … = 그 서비스만(서비스마다 한도가 따로라 나눠 동시에)
