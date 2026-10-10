# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚌 버스가 얼마나 자주 오나(소유자 2026-10-10 「대중교통은 있어도 배차시간이 길어서 어쩌다 한두 대 온다든지 그런 데이터도 중요」) → data/bus-freq/<시도 두 자리>.json + data/bus-freq.json(머리)
#   재료 = 국토교통부 TAGO 버스노선정보(공공데이터포털 1613000/BusRouteInfoInqireService · 키 keys.json data_go_kr)
#     도시 목록 getCtyCodeList → 도시별 노선 getRouteNoList → 노선마다 getRouteInfoIem(배차 간격 평일·토·일 분 · 첫차·막차) + getRouteAcctoThrghSttnList(서는 정류장·좌표)
#   셈 = 정류장마다 서는 노선의 「60 ÷ 평일 배차 간격」을 더해 한 시간에 몇 대(배차 간격이 비어 있는 노선은 대수에서 빼고 노선 수에만 넣는다 — 값을 지어 넣지 않는다)
#   **운영사가 신고한 배차 간격이다**(시간표·실제 도착이 아니다) · 서울 시내버스는 이 API 에 없다(서울시 API 가 따로) · 하루 몇 번만 다니는 농어촌 노선은 간격이 비어 있는 일이 많다
#   py -3.12 -X utf8 tools/region/busfreq-bake.py fetch [도시 코드 앞머리…]   (이어 받기 됨 · 원자료 07_API키/out/busfreq/<도시>.jsonl · 한도에 걸리면 멈춘다 — 다음 날 다시)
#   py -3.12 -X utf8 tools/region/busfreq-bake.py build
import json, os, sys, time, datetime, collections, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'busfreq'); os.makedirs(OUT, exist_ok=True)
_K = None
def call(op, q):
    global _K
    if _K is None:
        K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; _K = K if '%' in K else urllib.parse.quote(K, safe='')
    u = 'https://apis.data.go.kr/1613000/BusRouteInfoInqireService/%s?serviceKey=%s&_type=json&%s' % (op, _K, q); err = ''
    for n in range(4):
        try:
            t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
            if 'LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS' in t or 'LIMITED NUMBER' in t: raise SystemExit('하루 한도에 닿음 — 내일 이어서(' + op + ')')
            b = json.loads(t)['response']['body']; it = (b.get('items') or {}).get('item') or []
            return int(b.get('totalCount') or 0), (it if isinstance(it, list) else [it])
        except SystemExit: raise
        except Exception as e:
            err = type(e).__name__ + ' ' + str(getattr(e, 'code', '')); time.sleep(4 + n * 8)
            if getattr(e, 'code', 0) == 429: raise SystemExit('429 — 한도에 닿음 · 내일 이어서')
    raise RuntimeError('호출 실패 ' + op + ' ' + err)
def pages(op, q, size=500):
    rows = []; p = 1
    while True:
        n, it = call(op, 'numOfRows=%d&pageNo=%d&%s' % (size, p, q)); rows += it
        if not it or p * size >= n: return rows
        p += 1
def fetch(pre):
    cp = os.path.join(OUT, 'cities.json')
    if not os.path.exists(cp): json.dump(pages('getCtyCodeList', ''), open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
    C = json.load(open(cp, encoding='utf-8')); C.sort(key=lambda c: (0 if str(c['citycode']).startswith(('31', '23', '12', '25', '33', '34')) else 1, str(c['citycode'])))   # 수도권·충청 먼저
    seen = set()
    for f in os.listdir(OUT):
        if f.endswith('.jsonl'):
            for ln in open(os.path.join(OUT, f), encoding='utf-8'): seen.add(json.loads(ln)['id'])
    for c in C:
        code = str(c['citycode'])
        if pre and not code.startswith(tuple(pre)): continue
        dp = os.path.join(OUT, code + '.done')
        if os.path.exists(dp): continue
        R = pages('getRouteNoList', 'cityCode=' + code); n = 0
        with open(os.path.join(OUT, code + '.jsonl'), 'a', encoding='utf-8') as w:
            for r in R:
                rid = r['routeid']
                if rid in seen: continue
                _, inf = call('getRouteInfoIem', 'cityCode=%s&routeId=%s' % (code, rid)); i = inf[0] if inf else r
                st = pages('getRouteAcctoThrghSttnList', 'cityCode=%s&routeId=%s' % (code, rid))
                w.write(json.dumps({'id': rid, 'city': code, 'no': str(i.get('routeno', '')), 'tp': i.get('routetp', ''), 'iv': [i.get('intervaltime'), i.get('intervalsattime'), i.get('intervalsuntime')], 'ft': [str(i.get('startvehicletime', '')), str(i.get('endvehicletime', ''))],
                                    'st': [[s.get('nodeid'), s.get('nodenm'), s.get('gpslong'), s.get('gpslati')] for s in st]}, ensure_ascii=False) + chr(10)); w.flush()
                seen.add(rid); n += 1; time.sleep(0.05)
        open(dp, 'w').write(datetime.datetime.now().isoformat()); print(c['cityname'], code, '노선', len(R), '· 새로 받은', n, flush=True)
def build():
    C = {str(c['citycode']): c['cityname'] for c in json.load(open(os.path.join(OUT, 'cities.json'), encoding='utf-8'))}
    stop = {}; nr = 0; noiv = 0; done = [f[:-5] for f in os.listdir(OUT) if f.endswith('.done')]
    for f in sorted(os.listdir(OUT)):
        if not f.endswith('.jsonl'): continue
        for ln in open(os.path.join(OUT, f), encoding='utf-8'):
            r = json.loads(ln); nr += 1
            try: iv = float(r['iv'][0] or 0)
            except Exception: iv = 0
            if iv <= 0: noiv += 1
            for nid, nm, x, y in r['st']:
                try: x = float(x); y = float(y)
                except Exception: continue
                if not (124 < x < 132 and 33 < y < 39): continue
                e = stop.setdefault(nid, [nm, x, y, 0, 0.0, 0, 9999])
                e[3] += 1
                if iv > 0: e[4] += 60.0 / iv; e[5] += 1; e[6] = min(e[6], iv)
    by = collections.defaultdict(list)
    for nid, (nm, x, y, n, ph, nk, mn) in stop.items():
        by[nid[:3]].append([round(x * 1e5), round(y * 1e5), nm, n, round(ph, 1) if nk else -1, round(mn) if nk else -1, nk])
    os.makedirs(os.path.join(ROOT, 'data', 'bus-freq'), exist_ok=True); files = {}
    for k, v in sorted(by.items()):
        v.sort(); p = os.path.join(ROOT, 'data', 'bus-freq', k + '.json')
        json.dump({'schema': 'tg-bus-freq/1', 'key': k, 'stops': v}, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); files[k] = [len(v), os.path.getsize(p)]
    doc = {'schema': 'tg-bus-freq/1', 'made': datetime.date.today().isoformat(),
           'source': '국토교통부 TAGO 버스노선정보(공공데이터포털 1613000/BusRouteInfoInqireService) — 노선의 배차 간격(평일)·서는 정류장',
           'how': '정류장마다 서는 노선의 「60 ÷ 평일 배차 간격(분)」을 더해 한 시간에 몇 대로 셌다. 배차 간격이 비어 있는 노선은 대수에서 빼고 노선 수에만 넣었다.',
           'note': ['**운영사가 신고한 배차 간격이다** — 시간표나 실제 도착이 아니다. 출퇴근·낮·밤을 가르지 않은 한 값이라 낮에는 더 드물 수 있다',
                    '배차 간격이 비어 있는 노선(하루 몇 번만 다니는 농어촌·마을버스에 많다)은 대수에 못 넣었다 — 한 시간 대수 -1 = 서는 노선은 있으나 간격을 아는 노선이 하나도 없음(「안 온다」가 아니라 「모름」)',
                    '서울 시내버스는 이 API 에 없다(경기·인천 버스가 서울 안에서 서는 정류장만 나온다) — 서울 안 값은 실제보다 훨씬 작다. 화면에서 서울은 「자료 없음」으로',
                    '같은 자리라도 방향이 다르면 정류장이 따로다 · 한 노선이 한 정류장에 두 번 서면(순환) 두 번 세었다',
                    '받은 도시만 들어 있다(cities) — 하루 호출 한도 때문에 여러 날에 걸쳐 받는다. 없는 도시는 「아직 안 받음」'],
           'fields': 'files{정류장 ID 앞 세 글자(운영 쪽 · GGB 경기 · ICB 인천 …): [정류장 수, 바이트]} → data/bus-freq/<앞 세 글자>.json 의 stops[[경도×1e5, 위도×1e5, 정류장 이름, 서는 노선 수, 한 시간에 몇 대(평일 · -1 = 모름), 가장 잦은 노선의 배차 간격 분(-1 = 모름), 간격을 아는 노선 수]]',
           'cities': {k: C.get(k, '') for k in sorted(done)}, 'routes': nr, 'routes_no_interval': noiv, 'files': files}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'bus-freq.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('도시', len(done), '· 노선', nr, '· 간격 없는 노선', noiv, '· 정류장', len(stop), '· 파일', {k: v for k, v in files.items()})
if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if a == 'fetch': fetch(sys.argv[2:])
    else: build()
