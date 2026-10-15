# -*- coding: utf-8 -*-
"""서울 지하철 역별 날짜별 승하차(서울 열린데이터광장 CardSubwayStatsNew · 교통카드) 받기 — 평일·주말 비율(subhour-bake.py)의 바탕
  http://openapi.seoul.go.kr:8088/{키}/json/CardSubwayStatsNew/1/1000/{YYYYMMDD} — 칸 USE_YMD · SBWY_ROUT_LN_NM · SBWY_STNS_NM · GTON_TNOPE · GTOFF_TNOPE · REG_YMD(2026-10-15 실측)
  열쇠 = ../07_API키/keys.json 「seoul」(출력하지 않는다) · 받은 것 = ../07_API키/out/subway_day/<날짜>.json(있으면 건너뜀)
  py -3.12 -X utf8 tools/region/subday-fetch.py 20260701 20260930
"""
import os, sys, json, time, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(RAW, 'out', 'subway_day')


def main():
    a, b = sys.argv[1], sys.argv[2]
    key = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig'))['seoul']
    os.makedirs(OUT, exist_ok=True)
    d, e, n, skip = datetime.datetime.strptime(a, '%Y%m%d'), datetime.datetime.strptime(b, '%Y%m%d'), 0, 0
    while d <= e:
        ds = d.strftime('%Y%m%d'); p = os.path.join(OUT, ds + '.json'); d += datetime.timedelta(days=1)
        if os.path.exists(p):
            skip += 1; continue
        try:
            j = json.load(urllib.request.urlopen('http://openapi.seoul.go.kr:8088/%s/json/CardSubwayStatsNew/1/1000/%s' % (key, ds), timeout=40))
            r = j.get('CardSubwayStatsNew') or {}
            if (r.get('RESULT') or {}).get('CODE') != 'INFO-000':
                print(ds, '받지 못함', (r.get('RESULT') or j.get('RESULT') or {}).get('CODE')); continue
            json.dump(r.get('row', []), open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); n += 1
        except Exception as x:
            print(ds, '실패', type(x).__name__)
        time.sleep(0.3)
    print('받음', n, '· 이미 있음', skip, '→', OUT)


if __name__ == '__main__':
    main()
