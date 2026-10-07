# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.75.0 — 📅 공휴일(한국천문연구원 특일 정보 · 공공데이터포털 15012690 · 활용신청 승인 2026-10-07 · 2028-10-07 까지)
#   getRestDeInfo(공휴일 · 대체공휴일 · 선거일 등 isHoliday=Y) 를 해마다 받아 data/holidays.json 에 굽는다 — 키는 브라우저에 안 나간다
#   지도는 이 날을 「주말·공휴일」로 본다(생활인구 휴일 평균 · 지하철 휴일 시간표 · 날짜 칩)
#   py -3.12 -X utf8 tools/region/holiday-bake.py [첫해 끝해]   (기본 2016 2027)
import json, os, sys, urllib.request, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']   # 이미 URL 인코딩된 키 — 다시 인코딩하지 않는다
y0, y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (2016, 2027)
H, got = {}, {}
for y in range(y0, y1 + 1):
    u = 'https://apis.data.go.kr/B090041/openapi/service/SpcdeInfoService/getRestDeInfo?serviceKey=' + K + '&solYear=%d&numOfRows=100&_type=json' % y
    for t in range(3):
        try: j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode('utf-8')); break
        except Exception as e: print(y, '다시', e); time.sleep(2)
    else: raise SystemExit('받지 못함 %d' % y)
    if j['response']['header']['resultCode'] != '00': raise SystemExit(json.dumps(j['response']['header'], ensure_ascii=False))
    it = (j['response']['body'].get('items') or {}) or {}; it = it.get('item', []) if isinstance(it, dict) else []
    if isinstance(it, dict): it = [it]
    n = 0
    for x in it:
        if x.get('isHoliday') != 'Y': continue
        d = str(x['locdate']); k = d[:4] + '-' + d[4:6] + '-' + d[6:]
        H[k] = (H[k] + '·' + x['dateName']) if k in H and x['dateName'] not in H[k] else x['dateName']; n += 1
    got[y] = n; time.sleep(0.3)
doc = {'schema': 'tg-holidays/1', 'source': '한국천문연구원 특일 정보 getRestDeInfo(공공데이터포털 15012690) — ' + time.strftime('%Y-%m-%d') + ' 받음', 'note': 'isHoliday=Y 인 날(공휴일·대체공휴일·임시공휴일·선거일) · 해마다 건수 ' + json.dumps(got), 'years': got, 'days': dict(sorted(H.items()))}
p = os.path.join(ROOT, 'data', 'holidays.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(got, len(H), os.path.getsize(p), 'B')
