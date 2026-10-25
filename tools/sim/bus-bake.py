# -*- coding: utf-8 -*-
# 고속버스 시간당 대수(서울경부 = 경부·영동선 · 센트럴시티 = 호남선) — 요일 갈래 월~목·금·토·일 × 0~23시 · 출발/도착
#   원자료 = 국토교통부 TAGO 고속버스정보 시간표(게임 세션이 받은 C:/Users/knpth/bus-analysis/raw_timetable.csv · 2026-10-01 목 · 10-02 금 · 10-03 토(개천절) · 10-04 일)
#   → tools/sim/bus-tago.json (banpo-bake.py 가 구역 자료 tbl.bus 로 넣는다) · 날 수가 갈래마다 하루라 「그날의 시간표」다(행사·명절 시간표는 다를 수 있다)
# 쓰기: py -3.12 -X utf8 tools/sim/bus-bake.py [raw_timetable.csv]
import csv, collections, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/bus-analysis/raw_timetable.csv'
rows = list(csv.DictReader(open(SRC, encoding='utf-8-sig')))
DK = {'목': 'mt', '금': 'fr', '토(개천절)': 'sa', '토': 'sa', '일': 'su'}
TERM = {'서울경부': 'gb', '센트럴시티(서울)': 'ct'}
days = collections.defaultdict(set)
C = collections.Counter()
for x in rows:
    k = DK.get(x['요일']); tm = TERM.get(x['서울터미널'])
    if not k or not tm: continue
    days[k].add(x['조회일'])
    t = x['출발시각'] if x['방향'] == '출발' else x['도착시각']
    C[(k, tm, 'out' if x['방향'] == '출발' else 'in', int(t[:2]) % 24)] += 1
out = {'src': '국토교통부 TAGO 고속버스정보 시간표(2026-10-01 목 · 10-02 금 · 10-03 토(개천절) · 10-04 일)', 'note': '시간당 대수 · out = 출발(터미널에서 나감) · in = 도착(터미널로 들어옴) · 월~목 갈래는 목요일 하루 · 토는 개천절이라 보통 토요일과 다를 수 있다',
       'terms': {'gb': '서울경부(경부·영동선)', 'ct': '센트럴시티(호남선)'}, 't': {}}
for k in ('mt', 'fr', 'sa', 'su'):
    nd = max(1, len(days[k]))
    out['t'][k] = {tm: {w: [round(C[(k, tm, w, h)] / nd) for h in range(24)] for w in ('in', 'out')} for tm in ('gb', 'ct')}
json.dump(out, open(os.path.join(HERE, 'bus-tago.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', {k: (out['t'][k]['gb']['out'][17], out['t'][k]['ct']['out'][17]) for k in out['t']})
