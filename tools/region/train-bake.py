# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚆 기차로 서울까지 몇 분(소유자 2026-10-10 「KTX 나 기차의 경우 소요시간 등을 보여주고」) → data/train-seoul.json
#   재료 = 한국철도공사_열차운행정보(공공데이터포털 B551457/run/v2/travelerTrainRunInfo2 · 키 keys.json data_go_kr) — 하루치 모든 열차의 역별 **실제** 도착·출발 시각
#   셈 = 같은 열차 번호의 줄을 차례로 이어, 역마다 「그 역을 떠나 서울 쪽 역(DEST)에 닿기까지」와 「서울 쪽 역을 떠나 그 역에 닿기까지」를 분으로 → 가장 빠른 값·가운데값·하루 편수·첫차·막차
#   실제 운행 기록이라 지연이 든 값이다(시간표 아님) · 열차 종류(KTX·무궁화 등)는 이 자료에 없어 가르지 않는다 · SRT(수서)는 한국철도공사 자료가 아니라 없다
#   py -3.12 -X utf8 tools/region/train-bake.py [YYYYMMDD 평일 하루 · 기본 = 사흘 전]   (원자료는 07_API키/out/train/ 에 둔다)
import json, os, sys, time, datetime, collections, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'train'); os.makedirs(OUT, exist_ok=True)
DEST = ['서울', '용산', '청량리', '영등포']   # 서울 안 큰 역 — 이 가운데 먼저 닿는(나중에 떠나는) 역까지로 센다
def fetch(day):
    fn = os.path.join(OUT, 'run_%s.json' % day)
    if os.path.exists(fn): return json.load(open(fn, encoding='utf-8'))
    K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; k = K if '%' in K else urllib.parse.quote(K, safe='')
    q = urllib.parse.quote; rows = []; page = 1
    while True:
        u = 'https://apis.data.go.kr/B551457/run/v2/travelerTrainRunInfo2?serviceKey=%s&returnType=json&pageNo=%d&numOfRows=1000&%s=%s&%s=%s' % (k, page, q('cond[run_ymd::GTE]'), day, q('cond[run_ymd::LTE]'), day)
        b = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read().decode('utf-8', 'replace'))['response']['body']
        it = (b.get('items') or {}).get('item') or []; rows += it
        if not it or page * 1000 >= int(b.get('totalCount') or 0): break
        page += 1; time.sleep(0.3)
    json.dump(rows, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); return rows
def ts(s): return datetime.datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S') if s else None
def main():
    day = sys.argv[1] if len(sys.argv) > 1 else (datetime.date.today() - datetime.timedelta(days=3)).strftime('%Y%m%d')
    rows = fetch(day); T = collections.defaultdict(list)
    for r in rows: T[r['trn_no']].append(r)
    up = collections.defaultdict(list); dn = collections.defaultdict(list); line = collections.defaultdict(collections.Counter)
    for no, st in T.items():
        st.sort(key=lambda r: int(r['trn_run_sn'])); st = [r for r in st if r['stop_se_nm'] in ('시발', '종착', '여객승하차')]
        for i, r in enumerate(st): line[r['stn_nm']][r['mrnt_nm']] += 1
        for i, r in enumerate(st):
            if r['stn_nm'] in DEST: continue
            dep = ts(r['trn_dptre_dt']); arr = ts(r['trn_arvl_dt'])
            nx = next((x for x in st[i + 1:] if x['stn_nm'] in DEST and x['trn_arvl_dt']), None)   # 이 역을 떠난 뒤 처음 닿는 서울 쪽 역
            if nx and dep:
                m = (ts(nx['trn_arvl_dt']) - dep).total_seconds() / 60
                if 0 < m < 600: up[r['stn_nm']].append((m, dep.strftime('%H:%M'), nx['stn_nm'], no))
            pv = next((x for x in reversed(st[:i]) if x['stn_nm'] in DEST and x['trn_dptre_dt']), None)   # 이 역에 닿기 전 마지막으로 떠난 서울 쪽 역
            if pv and arr:
                m = (arr - ts(pv['trn_dptre_dt'])).total_seconds() / 60
                if 0 < m < 600: dn[r['stn_nm']].append((m, ts(pv['trn_dptre_dt']).strftime('%H:%M'), pv['stn_nm'], no))
    def pack(v):
        if not v: return None
        v.sort(); ms = [x[0] for x in v]; tm = sorted(x[1] for x in v); ds = collections.Counter(x[2] for x in v).most_common(1)[0][0]
        return [round(ms[0]), round(ms[len(ms) // 2]), len(v), tm[0], tm[-1], ds]
    stn = {}
    for nm in sorted(set(up) | set(dn)):
        stn[nm] = {'ln': [k for k, _ in line[nm].most_common(3)], 'up': pack(up[nm]), 'dn': pack(dn[nm])}
    import csv, io
    LL = {}; lp = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15127532', 'x.csv')   # 한국철도공사_역 위치 정보(공공데이터포털 15127532 · 2024-04-01판 · tools/region/dgfile.py 15127532)
    for r in list(csv.reader(io.StringIO(open(lp, 'rb').read().decode('cp949'))))[1:]:
        try: LL[r[1].strip()] = [round(float(r[3]), 5), round(float(r[2]), 5)]
        except Exception: pass
    L2 = {}; lp2 = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15067652', 'x.csv')   # 국가철도공단_철도역 정보(15067652 · 2025-07-11판) — 첫 표에 없는 역만
    R2 = list(csv.reader(io.StringIO(open(lp2, 'rb').read().decode('cp949')))); h2 = {k: i for i, k in enumerate(R2[0])}
    for r in R2[1:]:
        try:
            n2 = r[h2['역이름']].strip(); n2 = n2[:-1] if n2.endswith('역') else n2; xy = [round(float(r[h2['경도좌표']]), 5), round(float(r[h2['위도좌표']]), 5)]
            if 124 < xy[0] < 132 and 33 < xy[1] < 39: L2[n2] = xy   # 0 으로 비어 있는 줄이 있다
        except Exception: pass
    L3 = {}   # 도시·광역철도 역(전국도시철도역사정보표준데이터 — data/stations-kr.json · 서울은 data/r/stations.json) — 앞 두 표에 없는 역만 · 같은 이름이 여럿이면 쓰지 않는다
    try:
        cnt = collections.Counter(); tmp = {}
        for it in json.load(open(os.path.join(ROOT, 'data', 'stations-kr.json'), encoding='utf-8'))['items']: cnt[it[0]] += 1; tmp[it[0]] = [it[2], it[3]]
        seen = set()
        for it in json.load(open(os.path.join(ROOT, 'data', 'r', 'stations.json'), encoding='utf-8'))['items']:
            n3 = it[0][:-1] if it[0].endswith('역') and len(it[0]) > 2 else it[0]; key = (n3, round(it[2], 2), round(it[3], 2))
            if key in seen: continue
            seen.add(key); cnt[n3] += 1; tmp[n3] = [it[2], it[3]]
        L3 = {k: v for k, v in tmp.items() if cnt[k] == 1}
    except Exception as e: print('stations-kr 못 읽음', e)
    ALIAS = {'경주': '신경주', '김천구미': '김천(구미)', '진부': '진부(오대산)', '판교(충남)': '판교'}   # 운행 자료의 역 이름 → 위치 표(2024-04)의 이름. 경주 = 고속철도가 서는 지금의 경주역(위치 표에는 옛 이름 신경주 · 둘째 표의 「경주역」은 문 닫은 옛 시내 역이라 쓰면 안 된다)
    for k2, v2 in ALIAS.items():
        if v2 in LL: LL[k2] = LL[v2]
    miss = []
    for nm, v in stn.items():
        if nm in LL: v['ll'] = LL[nm]
        elif nm in L2: v['ll'] = L2[nm]; v['lls'] = 2
        elif nm in L3: v['ll'] = L3[nm]; v['lls'] = 3
        else: miss.append(nm)
    print('좌표 붙은 역', len(stn) - len(miss), '· 못 붙인 역', miss)
    d8 = '%s-%s-%s' % (day[:4], day[4:6], day[6:])
    doc = {'schema': 'tg-train-seoul/1', 'made': datetime.date.today().isoformat(), 'day': d8,
           'source': '한국철도공사_열차운행정보(공공데이터포털 B551457 travelerTrainRunInfo2) — %s 하루 모든 여객열차의 역별 실제 도착·출발 시각 %d줄 · 열차 %d대' % (d8, len(rows), len(T)),
           'how': '같은 열차의 정차역을 차례로 이어, 역마다 그 역을 떠나 서울 쪽 역(%s)에 처음 닿기까지(up)와 서울 쪽 역을 떠나 그 역에 닿기까지(dn)를 분으로 셌다.' % '·'.join(DEST),
           'note': ['**하루치 실제 운행 기록이다(시간표가 아니다)** — 그날의 지연이 들어 있고 요일·철마다 편수가 다르다',
                    '열차 종류(KTX·ITX·무궁화 등)는 이 자료에 없어 가르지 않았다 — 가장 빠른 값은 대개 빠른 열차, 가운데값은 그 역에 서는 열차 전체',
                    'SRT(수서 출발)는 한국철도공사 자료가 아니라 들어 있지 않다 · 수도권 전철(광역전철)도 이 자료가 아니다',
                    '갈아타는 길은 세지 않았다 — 한 열차로 서울 쪽 역까지 가는 것만. 직통이 없는 역은 값이 없다',
                    '예매율·승차율은 이 자료에 없다(공개 API 없음 — 역별 승하차 인원은 따로 한국철도공사 파일 자료)',
                    '역 좌표 ll = 한국철도공사_역 위치 정보(공공데이터포털 15127532 · 2024-04-01판)를 역 이름으로 맞댄 것 — 없으면 lls 2 = 국가철도공단_철도역 정보(15067652 · 2025-07-11판) · lls 3 = 전국도시철도역사정보표준데이터·서울시 역사마스터(data/stations-kr.json · data/r/stations.json · 이름이 한 자리뿐인 역만) · 셋 다 없으면 ll 이 없다(자리를 지어 넣지 않았다)'],
           'fields': 'stn{역 이름: {ln [노선…], up 서울로 [가장 빠른 분, 가운데값 분, 하루 편수, 첫차 출발, 막차 출발, 가장 많이 닿는 서울 쪽 역], dn 서울에서 [가장 빠른 분, 가운데값, 편수, 서울 쪽 첫 출발, 막 출발, 가장 많이 떠나는 서울 쪽 역], ll [경도, 위도](없을 수 있음)}} — 값이 없으면 null',
           'dest': DEST, 'stn': stn}
    p = os.path.join(ROOT, 'data', 'train-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(d8, '줄', len(rows), '· 열차', len(T), '· 역', len(stn), '· 바이트', os.path.getsize(p))
    for nm in ('부산', '동대구', '대전', '천안아산', '오송', '강릉', '광주송정', '수원', '평택', '천안', '조치원', '춘천', '전주', '목포'): print(nm, stn.get(nm))
if __name__ == '__main__': main()
