# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚥 교통시설 관점: 신호 교차로 시설 카드(소유자 2026-10-11 「교차로별 진행방향별 총 차로수에 직진 좌회전 직좌 동시 횡단보도 연등 신호등 — 시설이 보고 놀랄 만한 레이어 ·
#   우선 서초 강남 동작 관악 … 그리고 서울 전지역 확대」) → data/fac-signal.json
#   한 교차로 한 줄에 「시설담당이 보는 것」을 모은다: 번호(C-ITS = T-Data = 경찰청 같은 번호 체계) · 이름 · 들어오는 쪽마다 길·차로 수·제한속도 ·
#     그 쪽의 직진·좌회전 녹색 초와 **직좌 동시**(같은 때 같은 길이로 켜짐) · 보행 신호가 있는 쪽 · 주기(받은 것들) · 요일·시각 계획이 있는지 · (연등) 여부와 딸린 부모 · 가까운 단속 카메라 수
#   재료(모두 이미 있는 것 · 새로 받는 것 없음):
#     교차로 목록·자리 = 교통안전 신호등 실시간 정보의 교차로 지도정보(한국지역정보개발원 · 공공데이터포털 15157604 · 07_API키/out/rti/crsrd_map_info.json — 서울 2,779곳 = 서울 C-ITS 교차로)
#     들어오는 쪽·차로·제한속도 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(C:/Users/knpth/regionwork/nl)
#     방향별 초·보행 = data/sigdir-seoul.json(서울 T-Data V2X) · 계획 = data/signal-tod-seoul.json(경찰청) · data/sig-ksc-seocho.json(서초서 교통과 5곳)
#     T-GIS 코드·연동 부모 = data/tgis-seoul.json(서울 전체 · tools/signal/tgis-bake.py) · 카메라 = data/r/<구>/safety.json 의 cam
#   **한계**: 방향별 초는 받은 시간대의 실제 값이고 계획표가 아니다 · 차로 수는 링크 전체의 값이라 교차로 앞에서 늘어나는 좌회전 포켓·차로별 방향은 없다 · 「직좌 동시」는 받은 값으로 읽은 것(현시도 확인 아님)
#   py -3.12 -X utf8 tools/signal/facsig-bake.py [구 이름…]   (기본 = 서초구 강남구 동작구 관악구)
import json, os, sys, math, datetime, collections, warnings
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); SRC = 'C:/Users/knpth/regionwork/nl'
CODE = {g['name']: g['gu'] for g in json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus'] if g['sido'] == '11'}   # 서울 25구 이름 → 구 코드
GUS = [x for x in sys.argv[1:] if not x.startswith('-')] or sorted(CODE)   # 기본 = 서울 전체(2026-10-11 「서울 전지역 확대」) · 구 이름을 주면 그 구만
RANK = {'101': 1, '102': 2, '103': 3, '104': 4, '105': 5, '106': 6, '107': 7}; DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw']
def m(a, b): return math.hypot((a[0] - b[0]) * 88400.0, (a[1] - b[1]) * 111000.0)
def main():
    import shapefile
    from pyproj import Transformer
    from shapely.geometry import Polygon, Point
    from shapely.ops import unary_union
    tr = Transformer.from_crs('+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', 'EPSG:4326', always_xy=True); inv = Transformer.from_crs('EPSG:4326', '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m', always_xy=True)
    SG = {x['name']: unary_union([Polygon(r).buffer(0) for r in x['rings'] if len(r) >= 4]) for x in json.load(open(os.path.join(ROOT, 'data', 'base', 'sgg.json'), encoding='utf-8'))['sgg'] if x['sido'] == '서울특별시' and x['name'] in GUS}
    area = unary_union(list(SG.values())).buffer(0.004); bx = area.bounds; x0, y0 = inv.transform(bx[0], bx[1]); x1, y1 = inv.transform(bx[2], bx[3])
    n = shapefile.Reader(os.path.join(SRC, 'MOCT_NODE.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(n.fields[1:])}; NODE = {}
    for sr in n.iterShapeRecords():
        x, y = sr.shape.points[0]
        if x0 <= x <= x1 and y0 <= y <= y1: lon, lat = tr.transform(x, y); NODE[sr.record[fi['NODE_ID']]] = [lon, lat, sr.record[fi['NODE_TYPE']]]
    r = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949'); fi = {f[0]: k for k, f in enumerate(r.fields[1:])}; inc = collections.defaultdict(list); deg = collections.Counter()
    for k, rec in enumerate(r.iterRecords()):
        f, t = rec[fi['F_NODE']], rec[fi['T_NODE']]
        if f not in NODE or t not in NODE: continue
        rk = RANK.get(rec[fi['ROAD_RANK']])
        if not rk: continue
        deg[f] += 1; deg[t] += 1
        b = math.degrees(math.atan2((NODE[t][0] - NODE[f][0]) * 88400.0, (NODE[t][1] - NODE[f][1]) * 111000.0)) % 360   # 링크의 시작 → 끝 방위(짧은 링크라 끝머리 방위와 거의 같다)
        inc[t].append([rec[fi['LINK_ID']], f, rk, int(rec[fi['LANES']] or 0), int(rec[fi['MAX_SPD']] or 0), (rec[fi['ROAD_NAME']] or '').strip().replace('-', ''), b, 1 if rec[fi['CONNECT']] == '1' else 0])
    grid = collections.defaultdict(list)
    for k, v in NODE.items():
        if deg[k] >= 3: grid[(int(v[0] * 500), int(v[1] * 500))].append(k)
    def near_nodes(lon, lat, lim=55):
        out = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for k in grid.get((int(lon * 500) + dx, int(lat * 500) + dy), ()):
                    d = m((lon, lat), NODE[k][:2])
                    if d <= lim: out.append((d, k))
        if not out and lim == 55:   # 55m 안에 없으면 110m 안 가장 가까운 갈림길과 그 둘레 45m(큰 교차로·건널목 신호 — 신호 자리가 교차로 한가운데서 벗어나 있다)
            far = near_nodes(lon, lat, 110)
            if far: c0 = NODE[far[0]]; return [k for k in far if m(c0[:2], NODE[k][:2]) <= 45]
        return [k for _, k in sorted(out)]
    def load(fn):
        try: return json.load(open(fn, encoding='utf-8'))
        except Exception as e: print(os.path.basename(fn), '못 읽음', e); return {}
    sd = load(os.path.join(ROOT, 'data', 'sigdir-seoul.json')); its = sd.get('its', {}); pl = sd.get('pl', {})
    tod = {str(x['no']): x for x in load(os.path.join(ROOT, 'data', 'signal-tod-seoul.json')).get('spots', [])}
    ksc = {str(x['no']): x for x in load(os.path.join(ROOT, 'data', 'sig-ksc-seocho.json')).get('items', [])}
    phmv = load(os.path.join(ROOT, 'data', 'sig-phmv-seoul.json')).get('spots', {})
    tg = (load(os.path.join(ROOT, 'data', 'tgis-seoul.json')) or load(os.path.join(ROOT, 'data', 'tgis-seocho.json'))).get('items', []); tgc = {x[0]: x for x in tg}; tgn = {x[6]: x for x in tg if x[6]}   # 서울 전체(tools/signal/tgis-bake.py) — 없으면 서초 것
    CAM = []
    for g in GUS:
        CAM += load(os.path.join(ROOT, 'data', 'r', CODE.get(g, ''), 'safety.json')).get('cam', [])
    M = [x for x in load(os.path.join(KB, '07_API키', 'out', 'rti', 'crsrd_map_info.json')) if str(x.get('lclgvNm', '')).startswith('서울')]
    spots = {}; stat = collections.Counter()
    for x in M:
        lon, lat = float(x['mapCtptIntLot']), float(x['mapCtptIntLat']); p = Point(lon, lat); gu = next((g for g, poly in SG.items() if poly.contains(p)), None)
        if not gu: continue
        no = str(x['crsrdId']); nm = x['crsrdNm']; ns = near_nodes(lon, lat); nset = set(ns); side = {}
        for k in ns:
            for lid, f, rk, lanes, lim, road, b, con in inc.get(k, ()):
                if f in nset or rk > 6: continue
                d = DIRS[int(((b + 180) % 360 + 22.5) // 45) % 8]; e = side.setdefault(d, {'road': road, 'lanes': 0, 'lim': lim, 'ids': []})
                e['lanes'] += lanes; e['ids'].append(lid); e['lim'] = max(e['lim'], lim)
                if not e['road']: e['road'] = road
        recs = [q for q in its.get(no, []) if 'mv' in q and q.get('dq') != 'dir']; rec = None; S = {}
        if recs:   # 기록마다 빠진 이동류가 있어(밤 기록 등) 이동류가 가장 많은 기록을 바탕으로 하고, 없는 이동류·보행은 다른 기록에서 채운다
            okn = lambda q: sum(1 for z in q['mv'] if z[2] is not None); recs2 = sorted(recs, key=lambda q: (-okn(q), q.get('day', ''), q.get('from', ''))); base = recs2[0]; best = {}
            for q0 in recs2:   # 이동류마다 — 녹색 초가 있는 기록을 먼저, 녹색 시작(주기 안 자리)까지 있으면 그것으로 바꾼다(값이 빈 줄 None 이 섞여 있다)
                for q in q0['mv']:
                    if q[2] is None: continue
                    k2 = (q[0], q[1])
                    if k2 not in best or (best[k2][5] is None and q[5] is not None and q0 is base): best[k2] = q
            mv = list(best.values()); pd = []; pdh = set(); ped = []
            for q0 in recs2:
                for q in q0.get('pd') or []:
                    if q[0] not in pdh and q[1] is not None: pdh.add(q[0]); pd.append(q)
                for q in q0.get('ped') or []:
                    if q[0] not in set(z[0] for z in ped): ped.append(q)
            rec = {'mv': mv, 'pd': pd, 'ped': ped, 'day': base.get('day'), 'from': base.get('from')}
        elif no in ksc:   # 실시간 값이 없는 교통과 5곳 — 출력물의 첫 패턴(방향별 초)을 쓴다
            K = ksc[no]; pat = sorted(K.get('dir') or {})[:1]
            if pat: rec = {'mv': [[q[0], q[1], q[3], q[4], q[5], q[6], 1] for q in K['dir'][pat[0]]], 'pd': [], 'ped': [], 'day': K.get('day'), 'from': '교통과 패턴 ' + str(pat[0])}
        for d, e in sorted(side.items()):
            row = [d, e['road'], e['lanes'], e['lim'], None, None, 0, None]   # [들어오는 쪽, 길, 차로 합, 제한속도, 직진 녹색 초, 좌회전 녹색 초, 직좌 동시 1, 보행 녹색 초]
            if rec:
                i = DIRS.index(d)
                def pick(mv):
                    c = [(min((DIRS.index(q[0]) - i) % 8, (i - DIRS.index(q[0])) % 8), q) for q in rec['mv'] if q[1] == mv and q[0] in DIRS and q[2] is not None]
                    c = [z for z in c if z[0] <= 1]; return min(c, key=lambda z: z[0])[1] if c else None
                st, lt = pick('St'), pick('Lt')
                if st: row[4] = round(st[2])
                if lt: row[5] = round(lt[2])
                if st and lt and st[5] is not None and lt[5] is not None and abs(st[5] - lt[5]) <= 2 and abs(st[2] - lt[2]) <= 2: row[6] = 1
                pd = [q for q in rec.get('pd', []) if q[0] in DIRS and min((DIRS.index(q[0]) - i) % 8, (i - DIRS.index(q[0])) % 8) == 0]
                if pd: row[7] = round(pd[0][1])
                elif any(q[0] == d for q in rec.get('ped', [])): row[7] = -1   # 보행 신호는 있으나 녹색 초를 모른다
            S[d] = row
        yd = 1 if '(연등)' in nm or '연등' in nm else 0
        cyc = sorted(set(int(q.get('ci') or q.get('cyc') or 0) for q in recs if (q.get('ci') or q.get('cyc'))))
        t0 = tgn.get(int(no)) if no.isdigit() else None
        e = {'nm': nm, 'll': [round(lon, 6), round(lat, 6)], 'gu': gu, 'in': list(S.values()), 'cyc': cyc, 'cells': len(set((q[0], q[1]) for q in pl.get(no, []) if not (len(q) > 6 and q[6]))), 'plan': ('교통과' if no in ksc else '') + ('경찰청' if no in tod else ''), 'yd': yd,
             'cam': sum(1 for c in CAM if abs(c['lon'] - lon) < 0.002 and m((lon, lat), (c['lon'], c['lat'])) <= 100)}
        if t0: e['tgis'] = [t0[0], t0[1], t0[4], (tgc.get(t0[4]) or [0, ''])[1] if t0[4] else '']   # [T-GIS 코드, T-GIS 이름, 연동 부모 코드, 부모 이름]
        if rec: e['day'] = rec.get('day'); e['at'] = rec.get('from')
        # 현시와 신호값(소유자 2026-10-11 「교통시설 레이어인데 현시와 신호값도 있으면 표현해야지」) — 받은 값에서 읽은 켜지는 차례(seq) · 계획표의 현시별 초(pv) · 현시 → 이동류(phmv)
        if rec:
            got = sorted([q for q in rec['mv'] if q[2] is not None and q[5] is not None], key=lambda q: q[5]); grp = []
            for q in got:
                if grp and abs(q[5] - grp[-1][0]) <= 2: grp[-1][2].append([q[0], q[1], round(q[2])]); grp[-1][1] = max(grp[-1][1], round(q[2]))
                else: grp.append([round(q[5]), round(q[2]), [[q[0], q[1], round(q[2])]]])
            if grp: e['seq'] = grp; e['seq_n'] = [len(got), len(rec['mv']), max((q[6] for q in got), default=0)]
        hhmm = (rec.get('from') if rec else '12:00') or '12:00'; dow = (rec.get('dow') if rec.get('dow') is not None else (datetime.date.fromisoformat(rec['day']).weekday() + 1) % 7 if rec.get('day') else 3) if rec else 3   # 받은 값이 없으면 수요일 12시의 계획을 보기로
        if no in ksc:
            k = ksc[no]; cl = '1' if 1 <= dow <= 4 else ('2' if dow == 5 else ('3' if dow == 6 else '4')); rows = k.get('tod', {}).get(cl, []); h = hhmm.replace(':', '')
            r0 = ([r for r in rows if r[0] <= h] or rows[-1:])
            if r0:
                pt = k.get('pat', {}).get(str(r0[-1][2])) or {}
                if pt: e['pv'] = [r0[-1][0][:2] + ':' + r0[-1][0][2:], pt.get('c'), pt.get('off'), pt.get('a'), pt.get('b'), '교통과', cl, 1 if rec else 0]
                e['phn'] = [[x.get('p'), x.get('t', '')] for x in k.get('ph', [])]
        elif no in tod:
            t = tod[no]; pn = str(t.get('dow', {}).get(str(dow + 1), '')); rows = t.get('plans', {}).get(pn, []); r0 = ([r for r in rows if r[0] <= hhmm] or rows[-1:])
            if r0:
                num = lambda v: [int(z) for z in str(v).split()] if v else []
                e['pv'] = [r0[-1][0], r0[-1][1], r0[-1][2], num(r0[-1][3]), num(r0[-1][4]), '경찰청', pn, 1 if rec else 0]
        if no in phmv and phmv[no].get('ph'): e['phmv'] = {k2: [[q[0], q[1], q[2]] for q in v] for k2, v in phmv[no]['ph'].items()}; e['phmv_warn'] = phmv[no].get('warn') or ''
        spots[no] = e; stat[gu] += 1; stat[gu + ' 방향별 초'] += 1 if rec else 0; stat[gu + ' 들어오는 쪽 읽음'] += 1 if S else 0; stat[gu + ' 직좌 동시 있는 곳'] += 1 if any(v[6] for v in S.values()) else 0
    doc = {'schema': 'tg-fac-signal/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'area': '서울 ' + ('전체 25구' if len(GUS) >= 25 else '·'.join(GUS)),
           'source': '교차로 목록·자리 = 교통안전 신호등 실시간 정보의 교차로 지도정보(한국지역정보개발원 · 공공데이터포털 15157604 — 서울 C-ITS 교차로) · 들어오는 쪽·차로·제한속도 = 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판 · 방향별 초·보행 = 서울특별시 교통빅데이터플랫폼(T-Data) V2X 신호 잔여시간(data/sigdir-seoul.json %s) · 계획 = 경찰청 교차로계획정보서비스(공공데이터포털 15056569) · T-GIS = 서울시 T-GIS 교통안전시설물 교차로(A008_P · 서울 전체) · 카메라 = 무인교통단속카메라 표준데이터' % sd.get('made', ''),
           'note': ['**방향별 초는 받은 시간대에 실제로 돈 값이다(계획표가 아니다)** — 다른 시간대·요일은 다르고, 감응·수동 운영 중에는 또 다르다. day·at = 그 값을 받은 날·시각',
                    '차로 수 = 표준노드링크 LANES(링크 전체의 값)를 그 쪽으로 들어오는 링크끼리 더한 것 — 교차로 앞에서 늘어나는 좌회전 포켓·버스전용·차로별 진행 방향은 이 자료에 없다(시설담당 자료로 보완할 자리)',
                    '「직좌 동시」 = 같은 쪽의 직진과 좌회전이 같은 때(±2초) 같은 길이(±2초)로 켜진 것을 받은 값에서 읽은 것 — 현시도로 확인한 것이 아니다',
                    '보행 녹색 초 -1 = 그 쪽에 보행 신호가 있다고만 받았고 초는 모른다 · null = 받은 값에 없다(보행 신호가 없다는 뜻이 아니다)',
                    'plan = 요일·시각별 계획(주기·옵셋·현시값)이 있는 곳 — 「교통과」(서초서 교통과 출력물 5곳 · data/sig-ksc-seocho.json) · 「경찰청」(공개 계획 · data/signal-tod-seoul.json). 빈 글 = 계획 없음(시설담당 자료가 들어갈 자리 · data/fac-plan-schema.json)',
                    'cells = 요일 4갈래 × 24시 = 96칸 가운데 실시간 값으로 채운 칸 수 · yd 1 = 이름에 (연등)이 있는 딸린 신호 · tgis 의 연동 부모는 T-GIS 연동교차로코드(C-ITS 번호가 15m 안에서 맞은 곳만 붙는다)',
                    '들어오는 쪽이 비어 있으면 그 자리 55m 안에 갈림길 마디가 없는 것(이면도로 건널목 등) · 대각 교차로는 방위가 한 칸(45°) 어긋날 수 있다',
                    '**seq(켜지는 차례)는 현시도가 아니다** — 받은 값에서 녹색이 같은 때 켜지는 이동류끼리 묶은 것이다. 안 읽힌 이동류가 있으면(seq_n 의 첫 두 수가 다르면) 차례에 빈 데가 있다 · 한두 번 본 값(seq_n 셋째 수 ≤ 2)은 주기가 바뀌는 사이의 값일 수 있다',
                    'pv(계획표 현시별 초)는 「몇 현시가 몇 초」까지만 말한다 — 어느 현시가 어느 방향인지는 경찰청 공개 자료에 없다(교통과 5곳은 phn 현시 글 · 그 밖은 phmv 로 맞댄 66곳뿐) · 계획값이라 감응·수동 운영 중에는 실제와 다르다',
                    '차로 표시등·차로제어신호기(가변차로)는 공개 자료를 찾지 못해 없다 — 시설담당 자료가 오면 넣는다'],
           'fields': 'spots{교차로 번호: {nm, ll[경도, 위도], gu, in[[들어오는 쪽(nt 북쪽에서 오는 차 …), 길 이름, 차로 합, 제한속도, 직진 녹색 초, 좌회전 녹색 초, 직좌 동시 1, 보행 녹색 초]…], cyc[받은 주기 초…], cells, plan, yd, cam 100m 안 단속 카메라 수, tgis[T-GIS 코드, 이름, 연동 부모 코드, 부모 이름], day, at, seq[[녹색 시작(주기 안 초), 그 묶음의 가장 긴 녹색 초, [[들어오는 쪽, St 직진·Lt 좌회전, 녹색 초]…]]…](받은 값에서 같은 때(±2초) 켜지는 이동류끼리 묶은 **켜지는 차례** — 현시도가 아니다), seq_n[읽힌 이동류 수, 받은 이동류 수, 가장 많이 본 횟수], pv[시작 HH:MM, 주기, 옵셋, A링 현시별 초[], B링 현시별 초[], 출처(교통과·경찰청), 계획 번호, 1 = 받은 값의 요일·시각에 맞춘 줄 · 0 = 받은 값이 없어 수요일 12시 줄을 보기로], phn[[현시 번호, 현시 글]…](교통과 5곳), phmv{현시 번호: [[들어오는 쪽, 이동류, 링]…]}(계획표 현시값과 받은 값을 맞대 찾은 것 · data/sig-phmv-seoul.json), phmv_warn}}',
           'stat': dict(stat), 'spots': spots}
    p = os.path.join(ROOT, 'data', 'fac-signal.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(spots), '· 바이트', os.path.getsize(p))
    for g in GUS[:30]: print('  %s: %d곳 · 방향별 초 %d · 들어오는 쪽 읽음 %d · 직좌 동시 있는 곳 %d' % (g, stat[g], stat[g + ' 방향별 초'], stat[g + ' 들어오는 쪽 읽음'], stat[g + ' 직좌 동시 있는 곳']))
    for k in ('4039', '4916'): print(k, json.dumps(spots.get(k), ensure_ascii=False)[:700])
if __name__ == '__main__': main()
