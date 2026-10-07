# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.86.0 — 🚌 경기 버스 정류소 하차(경기 예상 귀갓길용)
#   승하차: 07_API키/out/ggstop/gg_stop_ridership_202607_avg.csv — 경기도 「정류소 별 승하차 인원 집계」(경기데이터드림 · data.go.kr 15144886 · 2026-07 · 일 단위 · 「상업적이용허용 및 콘텐츠변경허용」) — 코워크가 받아 정리
#   좌표: 국토교통부 TAGO 버스정류소정보(BusSttnInfoInqireService getSttnNoList · 경기 31개 시군 cityCode 31xxx) — nodeid 「GGB」+경기 BIS 정류소ID 로 잇는다
#   → 07_API키/out/ggstop/gg_stop_coords.json [[정류소ID, 이름, 경도, 위도, 평일 일평균 하차, 일평균 하차]…] (walkflow-bake.py 가 읽는다)
#   py -3.12 -X utf8 tools/region/ggstop-bake.py
import json, os, csv, urllib.request, time, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'ggstop')
k = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']   # 이미 URL 인코딩된 키
def g(u):
    for t in range(3):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8'))
        except Exception as e: print('다시', e); time.sleep(2)
    raise SystemExit('받지 못함 ' + u[:80])
B = 'https://apis.data.go.kr/1613000/BusSttnInfoInqireService/'
cities = [x for x in g(B + 'getCtyCodeList?serviceKey=%s&_type=json' % k)['response']['body']['items']['item'] if str(x['citycode']).startswith('31')]
NODE = {}
cache = os.path.join(OUT, 'tago_gg_nodes.json')
REDO = set(sys.argv[1:])   # 시군 이름 — 그 시군만 다시 받아 덧붙인다(TAGO 「가용한 세션이 존재하지 않습니다」 때)
if os.path.exists(cache): NODE = json.load(open(cache, encoding='utf-8'))
if not os.path.exists(cache) or REDO:
    for c in cities:
        if REDO and c['cityname'] not in REDO: continue
        p = 1
        while True:
            j = g(B + 'getSttnNoList?serviceKey=%s&cityCode=%s&numOfRows=1000&pageNo=%d&_type=json' % (k, c['citycode'], p)); b = j.get('response', {}).get('body')
            if not isinstance(b, dict):
                print(c['cityname'], '응답 없음 — 10초 뒤 다시', str(j)[:80]); time.sleep(10); j = g(B + 'getSttnNoList?serviceKey=%s&cityCode=%s&numOfRows=1000&pageNo=%d&_type=json' % (k, c['citycode'], p)); b = j.get('response', {}).get('body')
                if not isinstance(b, dict): print(c['cityname'], '또 응답 없음'); break
            it = (b.get('items') or {}).get('item') or []
            if isinstance(it, dict): it = [it]
            for x in it:
                if str(x.get('nodeid', '')).startswith('GGB') and x.get('gpslati'): NODE[x['nodeid'][3:]] = [x['nodenm'], float(x['gpslong']), float(x['gpslati'])]
            if p * 1000 >= int(b.get('totalCount') or 0): break
            p += 1; time.sleep(1)
        print(c['cityname'], len(NODE), flush=True)
    json.dump(NODE, open(cache, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False)
rows = list(csv.DictReader(open(os.path.join(OUT, 'gg_stop_ridership_202607_avg.csv'), encoding='utf-8-sig')))
out, miss, missv = [], 0, 0.0
for r in rows:
    n = NODE.get(r['정류소ID'])
    if not n: miss += 1; missv += float(r['일평균하차'] or 0); continue
    out.append([r['정류소ID'], r['정류소명'], round(n[1], 6), round(n[2], 6), float(r['평일평균하차'] or 0), float(r['일평균하차'] or 0)])
tot = sum(float(r['일평균하차'] or 0) for r in rows)
doc = {'schema': 'tg-ggstop/1', 'month': '2026-07', 'source': '경기도 정류소 별 승하차 인원 집계(경기데이터드림 · 2026-07) × 국토교통부 TAGO 버스정류소정보(좌표)', 'fields': '[정류소ID, 이름, 경도, 위도, 평일 일평균 하차, 일평균 하차]',
       'match': {'stops': len(rows), 'hit': len(out), 'miss': miss, 'share_alight': round(1 - missv / tot, 4) if tot else None}, 'stops': out}
json.dump(doc, open(os.path.join(OUT, 'gg_stop_coords.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('정류소', len(rows), '좌표 붙음', len(out), '못 붙음', miss, '하차 몫', doc['match']['share_alight'])
