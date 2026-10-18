# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏬 상권 임대료·공실률·수익률(한국부동산원 R-ONE 「상업용부동산 임대동향조사」 · 상권별 · 분기) → data/rone-shop.json
#   NEXT.md A8 「상권별 소득수익률·임대료」 · 키 = ../07_API키/keys.json 의 "rone"(이 도구 안에서만 · 결과·저장소에 키 없음)
#   표(2024년 3분기~ · R-ONE 표 목록 SttsApiTbl.do 에서 이름으로 찾음 2026-10-18):
#     임대료(천원/㎡) 오피스 TT249843134237374 · 중대형 상가 T244363134858603 · 소규모 상가 T248223134698125 · 집합 상가 T244913134948657
#     공실률(%)       오피스 TT244763134428698 · 중대형 T249633134845544 · 소규모 T241833134686576 · 집합 T243283134931290
#     수익률(분기 %)  오피스 T245883135037859 · 중대형 T242083134887473 · 소규모 T246253134913401 · 집합 T246393134978815(소득·자본·투자)
#   자리: R-ONE 은 상권 이름만 준다(경계·좌표 없음) → 이름으로 대표 점 하나를 찾는다(근사 · 경계 아님)
#     ① 이름이 역이면(또는 「/」로 나눈 앞 이름이 역이면) 전국 도시철도역 정보(국가철도공단 등 · 07_API키/out/subway/station_master_20261007.xlsx) — 같은 시도 안 같은 이름 역
#     ② 행정동 이름이면 그 동(한 시군구 안일 때만)의 대표 점(통계청 SGIS 행정동 경계 · vuski/admdongkor 2026-07)
#     ③ 아니면 브이월드 검색 API 장소(place) 「<시도> <이름>」 — 주소가 그 시도이고 제목에 이름(앞 두 글자)이 든 첫 결과
#     ④ 못 찾으면 좌표 없이(카드·목록에만) — 지어 넣지 않는다
#   py -3.12 -X utf8 tools/region/roneshop-bake.py [fetch]   (fetch = R-ONE 다시 받기 · 없으면 받아 둔 것으로)
import json, os, sys, time, re, urllib.request, urllib.parse, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'rone', 'shop'); os.makedirs(OUT, exist_ok=True)
KEYS = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))
def key(n): k = KEYS[n]; return k if isinstance(k, str) else (k.get('key') or k.get('value'))
TYPES = [['off', '오피스'], ['mid', '중대형 상가'], ['sml', '소규모 상가'], ['col', '집합 상가']]
TBL = {'rent': ['TT249843134237374', 'T244363134858603', 'T248223134698125', 'T244913134948657'],
       'vac': ['TT244763134428698', 'T249633134845544', 'T241833134686576', 'T243283134931290'],
       'yld': ['T245883135037859', 'T242083134887473', 'T246253134913401', 'T246393134978815']}
ITM = {'임대료': 'rent', '공실률': 'vac', '소득수익률': 'inc', '자본수익률': 'cap', '투자수익률': 'tot'}
SIDO = {'서울': ['서울특별시'], '부산': ['부산광역시'], '대구': ['대구광역시'], '인천': ['인천광역시'], '광주': ['광주광역시', '전남광주'], '대전': ['대전광역시'], '울산': ['울산광역시'],
        '세종': ['세종특별자치시'], '경기': ['경기도'], '강원': ['강원특별자치도', '강원도'], '충북': ['충청북도'], '충남': ['충청남도'], '전북': ['전북특별자치도', '전라북도'],
        '전남': ['전라남도', '전남광주'], '경북': ['경상북도'], '경남': ['경상남도'], '제주': ['제주특별자치도']}


def fetch_one(sid):
    rows, pi = [], 1
    while True:
        q = urllib.parse.urlencode({'KEY': key('rone'), 'Type': 'json', 'pIndex': pi, 'pSize': 1000, 'STATBL_ID': sid, 'DTACYCLE_CD': 'QY'})
        for k in range(4):
            try: j = json.loads(urllib.request.urlopen('https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do?' + q, timeout=60).read().decode('utf-8')); break
            except Exception:
                if k == 3: raise
                time.sleep(3)
        b = j.get('SttsApiTblData')
        if not b: raise SystemExit('R-ONE 응답 이상 ' + sid + ' ' + str(j)[:120])
        r = b[1]['row']; rows += r
        if len(r) < 1000: return rows
        pi += 1; time.sleep(0.3)


def stations():
    import openpyxl
    ws = openpyxl.load_workbook(os.path.join(KB, '07_API키', 'out', 'subway', 'station_master_20261007.xlsx'), read_only=True).active
    S = collections.defaultdict(list)
    for i, r in enumerate(ws.iter_rows(values_only=True)):
        if i == 0 or not r[9]: continue
        S[re.sub(r'\(.*\)', '', str(r[1])).strip()].append((float(r[9]), float(r[10]), str(r[12] or '')))
    return S


VC = os.path.join(OUT, 'geo_cache.json'); VCACHE = json.load(open(VC, encoding='utf-8')) if os.path.exists(VC) else {}
def vworld(q):
    if q in VCACHE: return VCACHE[q]
    u = 'https://api.vworld.kr/req/search?' + urllib.parse.urlencode(dict(service='search', request='search', version='2.0', crs='EPSG:4326', size=10, page=1, query=q, type='place', format='json', errorformat='json', key=key('vworld'), domain='https://340patrolman.github.io'))
    try: r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8'))['response']
    except Exception: return None
    time.sleep(0.25)
    if 'LIMIT' in json.dumps(r): raise SystemExit('브이월드 검색 한도')
    items = [[it.get('title', ''), (it.get('address') or {}).get('road') or (it.get('address') or {}).get('parcel') or '', round(float(it['point']['y']), 6), round(float(it['point']['x']), 6)] for it in ((r.get('result') or {}).get('items') or [])]
    if r.get('status') in ('OK', 'NOT_FOUND'): VCACHE[q] = items
    return items


# 장소 검색어만 바꾼다(좌표를 적어 넣지 않는다) — 이름 그대로 찾으면 같은 이름 가게·정류장이 먼저 잡히는 곳 · 길 이름 상권은 그 길의 대표 역
ALIAS = {'북촌': '북촌한옥마을', '서촌': '통인시장', '경희대': '경희대학교', '숙명여대': '숙명여자대학교', '성신여대': '성신여대입구', '전남대': '전남대학교',
         '강남대로': '강남', '서래마을': '반포 서래마을', '동대구': '동대구역', '테헤란로': '역삼', '도산대로': '압구정로데오', '목원대': '목원대학교', '공주대': '공주대학교', '계명대': '계명대학교', '울산대': '울산대학교', '충북대학교': '충북대학교'}
HJD = None
def dongs():
    global HJD
    if HJD is None:
        from shapely.geometry import shape
        HJD = []
        for f in json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features']:
            q = f['properties']; nm = q['adm_nm'].split()[-1]; base = re.sub(r'(제?\d+(·\d+)*(가)?)?(동|읍|면)$', '', nm)
            pt = shape(f['geometry']).representative_point(); HJD.append([q['sidonm'], q['sggnm'], nm, base, pt.y, pt.x])
    return HJD


def locate(sido, name, S):
    full = SIDO.get(sido, [sido])
    parts = [p.strip() for p in re.split(r'[/·]', name) if p.strip()]
    def stn(nm):
        for la, lo, ad in S.get(nm, []):
            if any(f in ad for f in full) or (not ad and sido in ('서울', '경기', '인천')): return [la, lo]
        return None
    for p in parts:   # ① 역 — 이름 그대로 · 「…역」 · 이름 안의 역 이름(3자 이상 · 가장 긴 것) · 대표 역 별칭
        q = ALIAS.get(p, p); cand = [q[:-1] if q.endswith('역') else q, q]
        m = re.search(r'([가-힣]{2,})역', q)
        if m: w = m.group(1); cand += [w[i:] for i in range(len(w) - 1)]
        cand += sorted({k for k in S if len(k) >= 3 and k in q}, key=len, reverse=True)
        for c in cand:
            h = stn(c)
            if h: return [h[0], h[1], 'stn', c + '역' + ('' if q == p else ' (' + p + ' 대표 역)')]
    D = [d for d in dongs() if any(d[0].startswith(f) for f in full)]
    TOK = {}
    for d in D:   # 시군구 이름 조각(「창원시마산합포구」 → 창원 · 마산합포) — 상권 이름 앞에 붙은 도시 이름을 떼고 그 시군구로 좁히는 데 쓴다
        for t in re.split(r'시|군|구', d[1]):
            if len(t) >= 2: TOK.setdefault(t, set()).add(d[1])
    for p in parts:   # ② 행정동 이름 — 그 동(들)이 한 시군구 안일 때만 · 이름 앞에 도시 이름이 붙어 있으면(울산농소 · 광명철산 · 마산동서동) 그 시군구 안에서만
        core, sg = p.replace(' ', ''), None
        for n in range(4, 1, -1):
            hit = {g for t, gs in TOK.items() if t.startswith(core[:n]) for g in gs} | ({d[1] for d in D} if core[:n] == sido else set())
            if hit and len(core) > n: core, sg = core[n:], hit; break
        hit = [d for d in D if len(d[3]) >= 2 and (sg is None or d[1] in sg) and (core == d[3] or core == d[2] or any(d[3] + x in core for x in ('동', '읍', '면')))]
        if hit and len({d[1] for d in hit}) == 1:
            return [round(sum(d[4] for d in hit) / len(hit), 6), round(sum(d[5] for d in hit) / len(hit), 6), 'dong', hit[0][1] + ' ' + '·'.join(sorted({d[2] for d in hit}))]
    for p in parts:   # ③ 브이월드 장소 — 주소가 그 시도이고 제목에 이름(또는 별칭) 전체가 든 첫 결과
        q = ALIAS.get(p, p)
        for t, ad, la, lo in vworld(full[0] + ' ' + q) or []:
            tt = t.replace(' ', ''); qq = q.replace(' ', '')
            if any(f in ad for f in full) and qq in tt and not re.search(re.escape(qq) + '(애|원|학)', tt): return [la, lo, 'vw', t + ('' if q == p else ' (' + p + ' 검색어)')]
    return None


def main():
    raw = {}
    for kind, ids in TBL.items():
        for ti, sid in enumerate(ids):
            f = os.path.join(OUT, sid + '.json')
            if 'fetch' in sys.argv or not os.path.exists(f): json.dump(fetch_one(sid), open(f, 'w', encoding='utf-8'), ensure_ascii=False); time.sleep(0.5)
            raw[(kind, ti)] = json.load(open(f, encoding='utf-8'))
    qs = sorted({r['WRTTIME_IDTFR_ID'] for v in raw.values() for r in v}); qlab = {r['WRTTIME_IDTFR_ID']: r['WRTTIME_DESC'] for v in raw.values() for r in v}
    val = collections.defaultdict(lambda: collections.defaultdict(dict))   # path → type → metric → [q…]
    for (kind, ti), rows in raw.items():
        for r in rows:
            m = ITM.get(r['ITM_NM'])
            if not m or r.get('DTA_VAL') in (None, ''): continue
            arr = val[r['CLS_FULLNM']][TYPES[ti][0]].setdefault(m, [None] * len(qs)); arr[qs.index(r['WRTTIME_IDTFR_ID'])] = round(float(r['DTA_VAL']), 3)
    paths = sorted(val); parent = {p for p in paths for q in paths if q.startswith(p + '>')}
    S = stations(); items, agg, how = [], {}, collections.Counter()
    for p in paths:
        v = {t: dict(m) for t, m in val[p].items()}
        if p in parent or '>' not in p: agg[p] = v; continue
        seg = p.split('>'); loc = locate(seg[0], seg[-1], S); how[loc[2] if loc else 'none'] += 1
        items.append([p, loc[0] if loc else None, loc[1] if loc else None, loc[2] if loc else '', loc[3] if loc else '', v])
    json.dump(VCACHE, open(VC, 'w', encoding='utf-8'), ensure_ascii=False)
    doc = {'schema': 'tg-rone-shop/1', 'made': datetime.date.today().isoformat(),
           'source': '한국부동산원 R-ONE 부동산통계 OpenAPI — 상업용부동산 임대동향조사(2024년 3분기~ 표 · 오피스·중대형·소규모·집합 상가 × 임대료·공실률·수익률) · 상권 자리 = 전국 도시철도역 정보(2026-06-18 기준) 또는 브이월드 검색 API 장소',
           'q': [qlab[x] for x in qs], 'qid': qs, 'types': TYPES,
           'fields': 'items[[상권 경로(시도>…>상권), 위도, 경도, 자리 찾은 법(stn 역 · dong 행정동 대표 점 · vw 브이월드 장소 · 빈 글 못 찾음), 찾은 이름, {종류: {rent 임대료 천원/㎡ · vac 공실률 % · inc 소득수익률 · cap 자본수익률 · tot 투자수익률(분기 %): [분기마다 값 — q 차례 · 없으면 null]}}]] · agg{전국·시도·권역(하위 상권이 있는 줄): 같은 꼴}',
           'note': ['상권 자리는 이름으로 찾은 대표 점 하나다 — R-ONE 상권 경계가 아니다(근사)', '임대료·공실률은 표본 조사값(R-ONE 표 설명: 2024년 2분기 표본 재설계 · 상권 재구획·추가로 시계열 해석에 유의)', '종류마다 조사하지 않은 상권은 값이 없다(오피스는 업무 상권 위주)', '수익률은 분기 값(연 수익률이 아니다)'],
           'items': items, 'agg': agg}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'rone-shop.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('상권', len(items), '묶음', len(agg), '자리', dict(how), '분기', doc['q'][0], '~', doc['q'][-1])
    rent_json(doc)


def rent_json(doc):
    """지도의 「💰 상가 임대료·공실률」 층이 읽는 data/r/rent.json(tg-rent/1)을 전국으로 — 꼴은 덧붙이기만(옛 칸 s·m·c·vs·vm·name·grp·lon·lat·how 그대로 + sido·o·vo·vc·yi·yt)
    서울·경기 145곳은 옛 파일의 자리(역 가운데·OSM 이름 점·손으로 잡은 3곳 — tools/region/rent-bake.py)를 그대로 쓴다"""
    p = os.path.join(ROOT, 'data', 'r', 'rent.json'); old = json.load(open(p, encoding='utf-8'))
    OLD = {(o['grp'], o['name']): o for o in old['items']}
    r1 = lambda a: [None if v is None else round(v, 1) for v in a] if a else None
    r2 = lambda a: [None if v is None else round(v, 2) for v in a] if a else None
    M = collections.OrderedDict()
    for path, la, lo, hw, fn, v in doc['items']:
        seg = path.split('>'); sido, grp, name = seg[0], (seg[1] if len(seg) == 3 else seg[0]), seg[-1]
        k = (sido, name); e = M.setdefault(k, {'name': name, 'grp': grp, 'sido': sido, 'la': la, 'lo': lo, 'how': (('역 ' if hw == 'stn' else '행정동 ' if hw == 'dong' else '장소 검색 ') + fn) if hw else '', 'v': {}})
        for t, mm in v.items():
            for m2, arr in mm.items(): e['v'].setdefault(t, {}).setdefault(m2, arr)
        if sido == '서울' and grp != e['grp'] and (grp, name) in OLD: e['grp'] = grp
    items, miss = [], []
    for (sido, name), e in M.items():
        o = (OLD.get((e['grp'], name)) or OLD.get(('경기', name) if sido == '경기' else ('', ''))) if sido in ('서울', '경기') else None   # 옛 판(rent-bake) 자리는 서울·경기만
        V = e['v']; g = lambda t, m2: (V.get(t) or {}).get(m2)
        it = {'name': name, 'grp': e['grp'], 's': r1(g('sml', 'rent')), 'm': r1(g('mid', 'rent')), 'c': r1(g('col', 'rent')), 'vs': r1(g('sml', 'vac')), 'vm': r1(g('mid', 'vac'))}
        if o: it.update(lon=o['lon'], lat=o['lat'], how=o['how'])
        elif e['la'] is not None: it.update(lon=round(e['lo'], 5), lat=round(e['la'], 5), how=e['how'])
        else: miss.append(sido + ' ' + name); continue
        it['sido'] = sido; it['o'] = r1(g('off', 'rent')); it['vo'] = r1(g('off', 'vac')); it['vc'] = r1(g('col', 'vac'))
        it['yi'] = {t: r2(g(t, 'inc')) for t in ('mid', 'sml', 'col', 'off') if g(t, 'inc')}; it['yt'] = {t: r2(g(t, 'tot')) for t in ('mid', 'sml', 'col', 'off') if g(t, 'tot')}
        for k2 in [k3 for k3, x in it.items() if x in (None, {})]: del it[k2]
        items.append(it)
    agg = {}
    for path, v in doc['agg'].items():
        g = lambda t, m2: (v.get(t) or {}).get(m2); k = path.split('>')[-1]
        agg[k] = {x: y for x, y in {'s': r1(g('sml', 'rent')), 'm': r1(g('mid', 'rent')), 'c': r1(g('col', 'rent')), 'vs': r1(g('sml', 'vac')), 'vm': r1(g('mid', 'vac')), 'o': r1(g('off', 'rent')), 'vo': r1(g('off', 'vac')), 'vc': r1(g('col', 'vac'))}.items() if y}
    note0 = (old.get('note') or '').split(' (v2.248.0)')[0]
    new = dict(old); new.update({'note': note0 + ' (v2.248.0) 서울·경기 밖은 전국 도시철도역·행정동 대표 점·브이월드 장소 검색으로 자리를 잡았다(근사 · 이름만 맞춘 것) · 수익률은 분기 값(연 수익률 아님) · 2024년 2분기 표본 재설계로 시계열 해석에 유의(R-ONE 표 설명).', 'baked': doc['made'], 'quarters': doc['qid'], 'items': items, 'agg': agg, 'miss': miss,
        'source': '한국부동산원 상업용부동산 임대동향조사 — 부동산통계정보시스템 R-ONE OpenAPI 「임대동향 지역별 임대료·공실률·수익률(2024년3분기~)」 오피스·중대형·소규모·집합 상가(전국 · tools/region/roneshop-bake.py) · 서울·경기 자리는 옛 판(rent-bake.py) 그대로 · 그 밖 자리 = 전국 도시철도역 정보·행정동 대표 점·브이월드 장소 검색',
        'unit': dict(old.get('unit') or {}, o='오피스 임대료(천원/㎡)', vo='오피스 공실률(%)', vc='집합 상가 공실률(%)', yi='소득수익률(분기 % · {mid 중대형 · sml 소규모 · col 집합 · off 오피스})', yt='투자수익률(분기 % · 소득 + 자본)', sido='시도')})
    json.dump(new, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('rent.json 상권', len(items), '(서울·경기 옛 자리', sum(1 for i in items if i['sido'] in ('서울', '경기')), ') · 자리 못 찾음', len(miss))


if __name__ == '__main__':
    main()
