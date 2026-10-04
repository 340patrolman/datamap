# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.9.0 — 🟢 에어코리아 측정소 자리(서울·경기) : 한국환경공단 에어코리아 측정소정보(B552584 · MsrstnInfoInqireSvc/getMsrstnList)
#   측정값은 지도가 그때그때 받는다(getCtprvnRltmMesureDnsty · 기기마다 공공데이터포털 키) — 여기서는 바뀌지 않는 자리만 굽는다.
#   py -3.12 -X utf8 tools/region/airkorea-bake.py fetch   → 07_API키/out/airkorea/msrstn_서울.json · msrstn_경기.json (서버가 느려 504 가 잦다 — 다시 돌리면 된다)
#   py -3.12 -X utf8 tools/region/airkorea-bake.py build   → data/airkorea-stations.json
import json, os, sys, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'airkorea')

def fetch():
    os.makedirs(OUT, exist_ok=True)
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; k = (k if isinstance(k, str) else next(iter(k.values()))).strip()
    ek = k if '%' in k else urllib.parse.quote(k, safe='')
    for sido in ('서울', '경기'):
        rows, pg = [], 1
        while True:
            u = 'https://apis.data.go.kr/B552584/MsrstnInfoInqireSvc/getMsrstnList?serviceKey=%s&returnType=json&numOfRows=100&pageNo=%d&addr=%s' % (ek, pg, urllib.parse.quote(sido))
            for a in range(5):
                try: it = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))['response']['body']['items']; break
                except Exception as e: print('retry', e); time.sleep(5)
            else: sys.exit('못 받음 ' + sido)
            rows += it
            if len(it) < 100: break
            pg += 1
        json.dump(rows, open(os.path.join(OUT, 'msrstn_%s.json' % sido), 'w', encoding='utf-8'), ensure_ascii=False); print(sido, len(rows))

def build():
    S = []
    for sido in ('서울', '경기'):
        for x in json.load(open(os.path.join(OUT, 'msrstn_%s.json' % sido), encoding='utf-8')):
            try: S.append([x['stationName'], round(float(x['dmY']), 5), round(float(x['dmX']), 5), sido, (x.get('mangName') or ''), (x.get('addr') or '')])
            except Exception: pass
    fn = os.path.join(ROOT, 'data', 'airkorea-stations.json')
    json.dump({'schema': 'tg-airk/1', 'at': time.strftime('%Y-%m-%d'), 'source': '한국환경공단 에어코리아 측정소정보(공공데이터포털 15073877) — 서울·경기 측정소 자리',
               'fields': '[측정소 이름, 경도, 위도, 시도(측정값 API 의 sidoName), 측정망, 주소]', 'items': S}, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('stations', len(S), os.path.getsize(fn))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
