# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.43.0 — NEIS 교육정보 개방 포털 「학원교습소정보」(acaInsTiInfo) 시·도 교육청마다 전부 받기 → 07_API키/out/neis/aca_<코드>.json
#   키 = 07_API키/keys.json 의 neis(출력 금지) · 한 번에 1,000행 · 이미 받은 시·도는 건너뛴다(서울 B10·경기 J10 은 코워크가 받음)
#   py -3.12 -X utf8 tools/region/neis-fetch.py
import json, os, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'neis'); os.makedirs(OUT, exist_ok=True)
K = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['neis']
if isinstance(K, dict): K = K.get('key') or list(K.values())[0]
CODES = ['B10', 'C10', 'D10', 'E10', 'F10', 'G10', 'H10', 'I10', 'J10', 'K10', 'M10', 'N10', 'P10', 'Q10', 'R10', 'S10', 'T10']
for c in CODES:
    p = os.path.join(OUT, 'aca_%s.json' % c)
    if os.path.exists(p): print('있음', c); continue
    rows, pi = [], 1
    while True:
        q = urllib.parse.urlencode({'KEY': K, 'Type': 'json', 'pIndex': pi, 'pSize': 1000, 'ATPT_OFCDC_SC_CODE': c})
        for i in range(4):
            try: j = json.loads(urllib.request.urlopen('https://open.neis.go.kr/hub/acaInsTiInfo?' + q, timeout=90).read().decode('utf-8')); break
            except Exception: time.sleep(3 + 3 * i); j = {}
        v = j.get('acaInsTiInfo')
        if not v: break
        tot = v[0]['head'][0]['list_total_count']; rows += v[1]['row']
        if len(rows) >= tot: break
        pi += 1; time.sleep(0.2)
    json.dump(rows, open(p, 'w', encoding='utf-8'), ensure_ascii=False); print(c, len(rows), flush=True)
