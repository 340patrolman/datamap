# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚇 지하철·전철로 강남역·서울시청·서울역까지 몇 분(소유자 2026-10-10 「지하철망별로 될까 · 강남으로의 접근성」) → data/subway-reach.json
#   역의 이음(어느 역 다음이 어느 역) = 국가철도공단 「역간거리」 파일 24개(공공데이터포털 · 노선마다 역 차례와 km — 07_API키/out/dg/<번호>/x.csv · tools/region/dgfile.py 로 받음)
#     파일이 못 이은 자리(운영사 경계 · 새 역 · 파일 없는 노선 — 신림선·김포골드라인·GTX-A 등)는 같은 노선의 가까운 역(곧은 거리 6km 안)을 후보로 넣고 시간표로 확인된 것만 잇는다(km -1)
#   역 사이 시간 = TAGO 역별 평일 시간표(subfreq-bake.py 가 받아 둔 07_API키/out/subfreq/) — 이웃한 두 역에서 같은 방향·같은 행선지 열차의 출발 시각 차이를 30초 칸에 모아
#     가장 많이 모인 칸(정차 포함). 거리로 본 빠르기가 시속 18~120km(1.2km 안 되는 짧은 구간은 8부터)(GTX-A 200) 안인 칸만 · 여러 칸이 비슷하면 가장 짧은 칸
#     (시간표에 열차 번호가 없어서 이렇게 읽는다 — **추정** · 시간표에서 못 읽은 이음은 넣지 않는다)
#   갈아타기 = 같은 이름 역끼리 · 걷기 4분(**가정**) + 옮겨 타는 역의 낮 평균 배차 간격 절반 · 가는 길 = 다익스트라 · 처음 타는 역의 기다림은 뺀다 · 급행을 가르지 못한다
#   py -3.12 -X utf8 tools/region/subreach-bake.py
import csv, io, glob, json, os, heapq, bisect, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
API = os.path.join(os.path.dirname(ROOT), '07_API키', 'out'); OUT = os.path.join(API, 'subfreq')
GAP = ['15041460', '15081860', '15081858', '15041074', '15041298', '15041327', '15041310', '15041269', '15041340', '15041348', '15041296', '15041295', '15041284', '15081855', '15041423', '15041297', '15041425', '15041350', '15041299', '15081850', '15081856', '15081857', '15081852', '15081853']
WALK = 4.0; CITY = {'BS': '부산', 'DG': '대구', 'DJ': '대전', 'GJ': '광주', 'BG': '부산'}
DEST = [['강남', '강남역', '강남'], ['시청', '서울시청', '시청'], ['서울역', '서울역', '서울역']]
def base(nm):
    nm = nm.split('(')[0].strip(); return nm[:-1] if nm.endswith('역') and len(nm) > 2 else nm
def mins(t): return int(t[:2]) * 60 + int(t[2:4]) + int(t[4:6] or 0) / 60.0
def main():
    S = json.load(open(os.path.join(OUT, 'stations.json'), encoding='utf-8')); T = json.load(open(os.path.join(OUT, 'sched_01.json'), encoding='utf-8'))
    info = {s['subwayStationId']: (s['subwayStationName'], s['subwayRouteName'], CITY.get(s['subwayStationId'][3:5], '')) for s in S}
    sid_of = collections.defaultdict(list)
    for sid, (nm, ln, city) in info.items():
        if not city: sid_of[(ln, base(nm))].append(sid)
    dep = {}
    for key, rows in T.items():
        d = collections.defaultdict(list)
        for t, e in rows:
            m = mins(t); d[e].append(m + 1440 if m < 240 else m)
        dep[(key[:-1], key[-1])] = {e: sorted(v) for e, v in d.items()}
    # ① 이음 후보(이름 짝 + km)
    PAIR = {}; nofile = collections.Counter(); noname = set()
    for n in GAP:
        for f in glob.glob(os.path.join(API, 'dg', n, 'x.*')):
            R = list(csv.reader(io.StringIO(open(f, 'rb').read().decode('cp949', 'replace')))); prev = None; seen = set()
            def num(x):
                try: return float(x)
                except Exception: return 0.0
            for r in R[1:]:
                if len(r) < 4: prev = None; continue
                sub = r[1].strip(); ln = sub.split('(')[0].strip(); nm = base(r[2])
                if (sub, nm) in seen: prev = None   # 같은 역이 다시 나오면 가지(지선)가 새로 시작하는 것
                seen.add((sub, nm)); cur = sid_of.get((ln, nm))
                if not cur: noname.add(ln + ' ' + r[2].strip()); prev = None; continue
                if prev and prev[0] == sub and prev[1] != nm:
                    km = sorted(set(x for x in (prev[3], prev[4], num(r[3]), num(r[4]) if len(r) > 4 else 0.0) if x > 0)) or None   # 파일마다 「역간거리」가 앞 역까지인지 다음 역까지인지 다르다(9호선 = 다음 역까지 · 공항철도는 반대로 보임) → 두 줄의 값을 모두 후보로 두고, 어느 하나로든 빠르기가 말이 되면 받는다
                    for a in prev[2]:
                        for b in cur:
                            if (a, b) not in PAIR or PAIR[(a, b)] is None: PAIR[(a, b)] = km; PAIR[(b, a)] = km
                prev = (sub, nm, cur, num(r[3]), num(r[4]) if len(r) > 4 else 0.0)
    import math
    XY = collections.defaultdict(list)   # 역 이름 → 좌표(서울시 역사마스터 · 전국도시철도역사정보표준데이터) — 역간거리 파일이 못 이은 자리(운영사 경계·새 역·파일 없는 노선)를 「같은 노선의 가까운 역」으로 메우는 데만 쓴다
    for fn in ('r/stations.json', 'stations-kr.json'):
        for it in json.load(open(os.path.join(ROOT, 'data', fn), encoding='utf-8'))['items']: XY[base(it[0])].append((it[2], it[3]))
    def near_km(a, b):
        pa, pb = XY.get(base(info[a][0])), XY.get(base(info[b][0]))
        if not pa or not pb: return None
        return min(math.hypot((p[0] - q[0]) * 88.8, (p[1] - q[1]) * 111.0) for p in pa for q in pb)
    deg = collections.Counter(a for a, _ in PAIR); GEO = set(); byline = collections.defaultdict(list)
    for sid, (nm, ln, city) in info.items(): byline[(city, ln)].append(sid)
    for (city, ln), ids in byline.items():
        for a in ids:
            if deg[a] >= 2: continue   # 이미 양쪽이 이어진 역은 건드리지 않는다
            nofile[(city + ' ' + ln).strip()] += 1
            cand = sorted((dk, b) for b in ids for dk in [near_km(a, b)] if b != a and dk is not None and dk <= (30 if ln == 'GTX-A' else 6))[:2]   # 가장 가까운 두 역만(멀리 있는 역까지 후보로 넣으면 앞 열차와 짝지어진 칸이 섞인다)
            for dk, b in cand:
                if (a, b) in PAIR: continue
                PAIR[(a, b)] = PAIR[(b, a)] = [round(max(dk, 0.3) * 1.2, 2)]; GEO.add((a, b)); GEO.add((b, a))   # 곧은 거리 × 1.2 를 선로 거리로 본다(가정 — 빠르기 거르기에만 쓴다)
    print('이음 후보', len(PAIR) // 2, '· 그 가운데 가까운 역으로 메운 후보', len(GEO) // 2, '· 한쪽만 이어졌거나 안 이어진 역(노선별)', dict(nofile)); print('TAGO 에 그 이름이 없는 역간거리 줄', len(noname), sorted(noname)[:30])
    # ② 시간 — 두 방향 가운데 그 차례로 달리는 쪽에서
    def bins(a, b, pool=False):
        out = []; tot = 0
        for ud in 'UD':
            da, db = dep.get((a, ud)), dep.get((b, ud))
            if not da or not db: continue
            if pool: da = {'': sorted(x for v in da.values() for x in v)}; db = {'': sorted(x for v in db.values() for x in v)}   # 행선지를 안 가리고(운영사 경계에서 행선지 이름이 다르다 — 3호선 지축~삼송: 「오금」 과 빈 글)
            cnt = collections.Counter(); n = 0
            for e, va in da.items():
                vb = db.get(e)
                if not vb: continue
                n += len(va); tot += len(va)
                for x in va:
                    k = bisect.bisect_right(vb, x + 0.4)
                    while k < len(vb) and vb[k] - x <= 20: cnt[int((vb[k] - x) * 2)] += 1; k += 1
            for k in cnt:
                c = cnt[k - 1] + cnt[k] + cnt[k + 1]
                if c >= max(5, 0.4 * n): out.append((c / n, (sum(cnt[q] * (q + 0.5) for q in (k - 1, k, k + 1)) / c) / 2))
        return out if (tot or pool) else None
    EDGE = {}; speeds = collections.defaultdict(list); hold = []
    for (a, b), km in PAIR.items():
        ln = info[a][1]; bs = bins(a, b)
        def okv(bs): return [x for x in bs if (any((8 if q < 1.2 else 18) <= q / (x[1] / 60) <= (200 if ln == 'GTX-A' else 120) for q in km) if km else 0.8 <= x[1] <= 6)]   # 역 사이가 짧으면 정차 시간 때문에 시속 10km 대까지 내려간다
        bs = okv(bs) if bs is not None else okv(bins(a, b, True) or [])   # 행선지를 안 가리는 것은 두 역에 같은 행선지 이름이 하나도 없을 때만(그 밖에는 앞 열차와 짝지어진 칸이 섞인다)
        pass
        if not bs: continue
        top = max(x[0] for x in bs); good = sorted(set(round(x[1], 1) for x in bs if x[0] >= top - 0.15))
        if len(good) == 1 or good[-1] - good[0] <= 1.0:
            EDGE[(a, b)] = good[0]
            if km: speeds[ln].append(km[0] / (good[0] / 60))
        else: hold.append((a, b, km, good))
    for a, b, km, good in hold:   # 칸이 여럿 남은 이음
        EDGE[(a, b)] = good[0]   # 가장 짧은 칸 — 이웃 역 사이는 배차 간격보다 짧아서, 남는 칸은 뒤 열차와 짝지어진 더 긴 칸이다(앞 열차와 짝지어진 더 짧은 칸은 빠르기 상한에서 걸러진다)
    SYM = set()   # 종점으로 들어가는 쪽은 종점에 「출발」이 없어 못 읽는다 → 반대 방향에서 읽은 시간을 그대로 쓴다(같은 구간 · 표시 sym)
    for (a, b) in list(PAIR):
        if (a, b) not in EDGE and (b, a) in EDGE: EDGE[(a, b)] = EDGE[(b, a)]; SYM.add((a, b))
    miss = [(info[a][1], info[a][0], info[b][0]) for (a, b) in PAIR if (a, b) not in EDGE]
    print('시간을 읽은 이음', len(EDGE), '/', len(PAIR), '· 여러 칸에서 고른 이음', len(hold), '· 못 읽은 이음', len(miss), miss[:25])
    def headway(sid):
        hs = []
        for ud in 'UD':
            d = dep.get((sid, ud))
            if not d: continue
            m = sorted(set(round(x) for v in d.values() for x in v if 600 <= x <= 960))
            if len(m) >= 2: hs.append((m[-1] - m[0]) / (len(m) - 1))
        return sum(hs) / len(hs) if hs else None
    HW = {sid: headway(sid) for sid in info}
    byname = collections.defaultdict(list)
    for sid, (nm, ln, city) in info.items(): byname[(city, base(nm))].append(sid)
    def far(nm):   # 이름만 같고 자리가 다른 역(5호선 양평 · 경의중앙 양평)은 갈아타는 역이 아니다 — 그 이름의 좌표들이 2km 넘게 벌어져 있으면 뺀다
        ps = XY.get(base(nm)) or []
        return any(math.hypot((p[0] - q[0]) * 88.8, (p[1] - q[1]) * 111.0) > 2 for p in ps for q in ps)
    REV = collections.defaultdict(list)
    for (a, b), w in EDGE.items(): REV[b].append((a, w, 0))
    for ids in byname.values():
        for a in ids:
            for b in ids:
                if a != b and info[a][1] != info[b][1] and HW.get(b) and not far(info[a][0]): REV[b].append((a, WALK + HW[b] / 2, 1))
    res = {}
    for key, label, nm in DEST:
        src = byname[('', base(nm))]; D = {s: (0.0, 0) for s in src}; h = [(0.0, 0, s) for s in src]; heapq.heapify(h)
        while h:
            d, x, u = heapq.heappop(h)
            if (d, x) > D.get(u, (1e9, 0)): continue
            for v, w, t in REV.get(u, ()):
                nd = (d + w, x + t)
                if nd < D.get(v, (1e9, 0)): D[v] = nd; heapq.heappush(h, (nd[0], nd[1], v))
        res[key] = D; print(label, '도착역', len(src), '· 닿는 역', len(D))
    stn = []
    for sid, (nm, ln, city) in info.items():
        row = [sid, nm, ln, city]
        for key, _, _ in DEST:
            v = res[key].get(sid); row += [round(v[0]), v[1]] if v else [-1, -1]
        stn.append(row)
    links = [[a, b, w, -1 if (not PAIR[(a, b)] or (a, b) in GEO) else min(PAIR[(a, b)], key=lambda q: abs(q / (w / 60) - 35))] + ([1] if (a, b) in SYM else []) for (a, b), w in sorted(EDGE.items())]
    doc = {'schema': 'tg-subway-reach/1', 'made': datetime.date.today().isoformat(),
           'source': '역의 이음·거리 = 국가철도공단 역간거리 파일 24개(공공데이터포털 15041460 등 · 2025-06-30~2026-06-30판) · 역 사이 시간 = 국토교통부 TAGO 지하철정보(1613000/SubwayInfo) 역별 평일 시간표',
           'how': '이웃한 두 역에서 같은 방향·같은 행선지 열차의 출발 시각 차이를 30초 칸에 모아 가장 많이 모인 칸을 그 구간 시간으로 읽었다(정차 포함 · 거리로 본 빠르기가 시속 18~120km(1.2km 안 되는 짧은 구간은 8부터) 안인 칸만). 갈아타기 = 같은 이름 역끼리 걷기 %d분(가정) + 옮겨 타는 역의 낮 평균 배차 간격 절반. 가장 빠른 길(다익스트라).' % WALK,
           'note': ['**시간표에서 읽어 낸 추정이다** — 시간표에 열차 번호가 없어 구간 시간을 출발 시각 차이로 읽었다. 운영사가 낸 소요시간 표가 아니다',
                    '갈아타는 걷기 %d분은 **가정값**이다(역마다 실제는 1~10분) · 기다림은 낮(10~16시) 배차 기준' % WALK,
                    '처음 타는 역에서 기다리는 시간은 넣지 않았다 — 배차가 드문 역은 data/subway-freq.json 의 간격만큼 더 걸린다',
                    '급행을 가르지 못해 완행에 가까운 값이다(급행을 타면 더 짧다) · 이름이 다른 환승(걸어서 옮기는 역)은 잇지 못했다',
                    '-1 = 닿지 않음(수도권 밖 도시철도 · 시간표에서 구간 시간을 못 읽어 길이 끊긴 역) — 「멀다」가 아니라 「못 셈」',
                    '못 센 수도권 역(2026-10-10 밤 판): 인천2호선 15역(원자료 시간표에 상행·하행이 섞여 있다) · 2호선 성수·신정 지선 6역(원자료에 시간표가 없다) · 자기부상 5역 · 경의중앙 3역 등 — 동해선·대경선은 수도권과 이어지지 않아 -1 이 맞다',
                    '눈으로 맞대 본 값(참고): 판교→강남역 14분 · 잠실→강남역 13분 · 사당→강남역 11분 · 홍대입구→서울역(공항철도) 8분 · 수원→서울시청 70분 · 인천→서울역 76분 — 흔히 아는 시간과 비슷하다. 갈아타는 길은 걷기·기다림 가정 때문에 실제보다 5~10분 길게 나오는 편이다',
                    'links 의 km -1 = 역간거리 파일이 못 이은 자리를 같은 노선의 가까운 역으로 메운 것(시간표에서 한결같은 시간이 읽힌 것만 · 한 역을 건너뛴 이음이 섞일 수 있으나 시간은 그 구간의 실제 시간표 값이다) — 노선도를 그릴 때는 km 가 있는 이음만 쓴다'],
           'dest': [[x[0], x[1]] for x in DEST],
           'fields': 'stn[[역 ID, 역 이름, 노선, 도시(빈 글 = 수도권 등), 강남역까지 분, 갈아타는 횟수, 서울시청까지 분, 횟수, 서울역까지 분, 횟수]] · links[[역 ID, 다음 역 ID, 분, km(-1 = 모름), 1 = 반대 방향에서 읽은 시간을 그대로 쓴 것(종점으로 들어가는 쪽 — 없으면 생략)]]',
           'stn': stn, 'links': links}
    p = os.path.join(ROOT, 'data', 'subway-reach.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('역', len(stn), '· 이음', len(links), '· 바이트', os.path.getsize(p))
    for nm in ('수색', '운정', '염창', '사당', '수원', '인천', '판교(판교테크노밸리)', '김포공항', '잠실(송파구청)', '노원', '의정부', '일산', '정자', '신림', '구래'):
        print('  ', [r[1:] for r in stn if r[1] == nm])
    for ln in ('신분당', '2호선', '9호선', '경의중앙'):
        v = sorted(speeds.get(ln) or [0]); print('  ', ln, '보통 빠르기 km/h', round(v[len(v) // 2]))
if __name__ == '__main__': main()
