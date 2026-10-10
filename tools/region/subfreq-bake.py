# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚇 지하철·전철이 얼마나 자주 오나(소유자 2026-10-10 「경의중앙선은 잘 안 와 · 역세권이라 해도 그다지 좋지 않은 이런 것도 표현」) → data/subway-freq.json
#   재료 = 국토교통부 TAGO 지하철정보(공공데이터포털 1613000/SubwayInfo · 키 keys.json data_go_kr) — 역 목록 GetKwrdFndSubwaySttnList · 역별 시간표 GetSubwaySttnAcctoSchdulList(평일 01 · 상행 U·하행 D)
#   셈 = 그 역을 떠나는 시각을 모아(같은 시각·같은 행선지는 한 번만 — 원자료에 같은 줄이 세 번씩 온다) 시간대마다 한 시간에 몇 대 · 낮에 가장 길게 기다리는 간격
#   시간표 값이다(실제 지연·무정차는 모른다) · 급행·완행을 가르지 않는다(행선지만 있다) · 차 안 혼잡도는 이 자료에 없다
#   py -3.12 -X utf8 tools/region/subfreq-bake.py [fetch|build]   (fetch = 역 1,108 × 2방향 호출 · 원자료 07_API키/out/subfreq/ · 이어 받기 됨)
import json, os, sys, time, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subfreq'); os.makedirs(OUT, exist_ok=True)
def call(op, q):
    K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; k = K if '%' in K else urllib.parse.quote(K, safe='')
    u = 'https://apis.data.go.kr/1613000/SubwayInfo/%s?serviceKey=%s&_type=json&%s' % (op, k, q)
    for n in range(3):
        try:
            b = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace'))['response']['body']
            it = (b.get('items') or {}).get('item') or []; return it if isinstance(it, list) else [it]
        except Exception as e:
            err = type(e).__name__ + ' ' + str(getattr(e, 'code', '')); time.sleep(3 + n * 5)
    raise RuntimeError('호출 실패 ' + op + ' ' + err)
def fetch():
    sp = os.path.join(OUT, 'stations.json')
    if not os.path.exists(sp): json.dump(call('GetKwrdFndSubwaySttnList', 'numOfRows=3000&pageNo=1&subwayStationName='), open(sp, 'w', encoding='utf-8'), ensure_ascii=False)
    S = json.load(open(sp, encoding='utf-8')); tp = os.path.join(OUT, 'sched_01.json'); T = json.load(open(tp, encoding='utf-8')) if os.path.exists(tp) else {}
    for i, s in enumerate(S):
        for ud in 'UD':
            key = s['subwayStationId'] + ud
            if key in T: continue
            it = call('GetSubwaySttnAcctoSchdulList', 'numOfRows=1500&pageNo=1&subwayStationId=%s&dailyTypeCode=01&upDownTypeCode=%s' % (s['subwayStationId'], ud))
            T[key] = sorted(set((str(x.get('depTime', '')).zfill(6), x.get('endSubwayStationNm') or '') for x in it if str(x.get('depTime', '0')) not in ('0', '')))
            time.sleep(0.15)
        if i % 50 == 49: json.dump(T, open(tp, 'w', encoding='utf-8'), ensure_ascii=False); print(i + 1, '/', len(S), flush=True)
    json.dump(T, open(tp, 'w', encoding='utf-8'), ensure_ascii=False); print('역', len(S), '· 시간표', len(T))
def one(rows):
    m = sorted(set(int(t[:2]) * 60 + int(t[2:4]) for t, _ in rows))   # 같은 분에 떠나는 것은 한 대로
    if not m: return None
    day = [x for x in m if 240 <= x]   # 새벽 4시 앞(자정 넘긴 막차)은 편수에만 넣고 첫차·간격에서 뺀다
    def per(a, b): return round(sum(1 for x in m if a * 60 <= x < b * 60) / (b - a), 1)
    mid = [x for x in m if 600 <= x <= 960]; gap = max((b - a for a, b in zip(mid, mid[1:])), default=-1)
    ends = {}
    for _, e in rows: ends[e] = ends.get(e, 0) + 1
    fm = lambda x: '%02d:%02d' % (x // 60, x % 60)
    return [len(m), fm(day[0]) if day else '', fm(m[-1] if m[-1] >= 240 and not [x for x in m if x < 240] else max([x for x in m if x < 240] or [m[-1]])), per(7, 9), per(10, 16), per(18, 20), gap, sorted(ends, key=lambda e: -ends[e])[:2]]
def build():
    S = json.load(open(os.path.join(OUT, 'stations.json'), encoding='utf-8')); T = json.load(open(os.path.join(OUT, 'sched_01.json'), encoding='utf-8')); stn = []; line = {}
    for s in S:
        u = one(T.get(s['subwayStationId'] + 'U') or []); d = one(T.get(s['subwayStationId'] + 'D') or [])
        if not u and not d: continue
        stn.append([s['subwayStationId'], s['subwayStationName'], s['subwayRouteName'], u, d])
        for x in (u, d):
            if x: line.setdefault(s['subwayRouteName'], []).append((x[4], x[3], x[6]))
    L = {}
    for k, v in line.items():
        a = sorted(x[0] for x in v); b = sorted(x[1] for x in v); g = sorted(x[2] for x in v if x[2] >= 0)
        L[k] = [len(v), a[len(a) // 2], b[len(b) // 2], g[len(g) // 2] if g else -1]
    doc = {'schema': 'tg-subway-freq/1', 'made': datetime.date.today().isoformat(),
           'source': '국토교통부 TAGO 지하철정보(공공데이터포털 1613000/SubwayInfo) — 역별 평일 시간표(상행·하행) · 받은 날 ' + datetime.date.fromtimestamp(os.path.getmtime(os.path.join(OUT, 'sched_01.json'))).isoformat(),
           'how': '역을 떠나는 시각을 모아 시간대마다 한 시간에 몇 대인지 셌다(같은 시각·같은 행선지는 한 번 · 같은 분에 떠나는 것은 한 대). 낮 간격 = 10~16시 사이 가장 길게 벌어진 두 열차 사이.',
           'note': ['**평일 시간표 값이다** — 실제 지연·무정차·운휴는 모른다 · 주말·공휴일은 더 드물다',
                    '급행·완행을 가르지 않는다(자료에 행선지만 있다) — 급행이 서지 않는 역의 값은 그 역 시간표에 든 열차만이라 그대로 맞다',
                    '한 선로를 여러 노선이 같이 쓰는 역은 노선 이름별로 따로 실려 있다 · 종점은 한 방향만 있다',
                    '차 안이 얼마나 붐비는지(혼잡도)는 이 자료에 없다 — 따로 구한다',
                    '역 좌표는 싣지 않았다 — 역 이름 + 노선으로 맞댄다(data/r/stations.json · data/stations-kr.json)'],
           'fields': 'stn[[역 ID, 역 이름, 노선, 상행, 하행]] 방향 값 = [하루 편수, 첫차, 막차, 출근 7~9시 한 시간에 몇 대, 낮 10~16시 한 시간에 몇 대, 저녁 18~20시 한 시간에 몇 대, 낮 가장 긴 간격 분(-1 = 낮에 한 대 이하), 행선지 많은 순 2] — 없는 방향은 null · line{노선: [방향 수, 낮 한 시간 몇 대 가운데값, 출근 가운데값, 낮 가장 긴 간격 가운데값]}',
           'line': L, 'stn': stn}
    p = os.path.join(ROOT, 'data', 'subway-freq.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('역', len(stn), '· 바이트', os.path.getsize(p))
    for k, v in sorted(L.items(), key=lambda kv: kv[1][1]): print('  %-10s 낮 %4.1f대/시 · 출근 %4.1f · 낮 가장 긴 간격 %s분' % (k, v[1], v[2], v[3]))
if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if a == 'fetch': fetch()
    build()
