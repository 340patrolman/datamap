# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.75.0 — 🚌 서울 중앙버스전용차로 정류장을 지나는 경기버스(코워크·소유자 결정 2026-10-07)
#   원자료(07_API키/out · 경기도 버스 API · data_go_kr 키 · RUN_gg_scan405.bat · RUN_alloc.bat):
#     gg_scan405_YYYYMMDD_HHMM.csv — 서울 중앙차로 정류장 405곳마다 경기도 API 가 아는 노선(STOPS_NO·이름·좌표·routeId·노선·종류·지역·방면)
#     alloc_YYYYMMDD_HHMM.csv      — 그 노선 488개의 첨두·비첨두 배차간격(분)·첫차·막차·기점·종점
#   지역이 「서울」인 노선은 뺀다(서울 시내버스 — 경기도 API 에 일부만 · 배차 칸이 비어 있다).
#   시간당 대수 = Σ 60 ÷ 배차간격(배차가 있는 노선만 · 계산값) — 「버스가 얼마나 자주 서는가」 기준값(관계장부 R2 승하차 노출의 보조 분모)
#   gg_bus_routes_*.csv(역 주변 정류장 703행)는 정류장 좌표가 없어 이 층에 안 쓴다.
#   → data/ggbrt.json · py -3.12 -X utf8 tools/region/ggbrt-bake.py
import csv, json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
O = os.path.join(os.path.dirname(ROOT), '07_API키', 'out')
SC = sorted(glob.glob(os.path.join(O, 'gg_scan405_2*.csv')))[-1]; AL = sorted(glob.glob(os.path.join(O, 'alloc_2*.csv')))[-1]
A = {r['routeId']: r for r in csv.DictReader(open(AL, encoding='utf-8-sig'))}
RT, RI, ST = [], {}, collections.OrderedDict(); cnt = collections.Counter()
def num(v):
    try: return int(float(v)) if v not in ('', None) and float(v) > 0 else None
    except ValueError: return None
for r in csv.DictReader(open(SC, encoding='utf-8-sig')):
    if r['routeRegion'] == '서울': cnt['서울 노선 뺌'] += 1; continue
    rid = r['routeId']
    if rid not in RI:
        a = A.get(rid, {}); RI[rid] = len(RT)
        RT.append([r['routeName'], r['routeType'], r['routeRegion'], num(a.get('peekAlloc')), num(a.get('nPeekAlloc')), a.get('upFirstTime') or '', a.get('upLastTime') or '', a.get('startStationName') or '', a.get('endStationName') or ''])
    s = ST.setdefault(r['STOPS_NO'], [r['STOPS_NO'], r['STOPS_NM'], round(float(r['XCRD']), 6), round(float(r['YCRD']), 6), []])
    if RI[rid] not in s[4]: s[4].append(RI[rid])
ODD = 3   # 배차 3분 미만 = 의심값(직행좌석 1151 첨두 1분 등 · API 값 그대로 두되 시간당 대수 합에서 뺀다)
ok = lambda v: v and v >= ODD
for s in ST.values():
    pk = sum(60 / RT[i][3] for i in s[4] if ok(RT[i][3])); np = sum(60 / RT[i][4] for i in s[4] if ok(RT[i][4]))
    s += [round(pk, 1), round(np, 1), sum(1 for i in s[4] if not RT[i][3]), sum(1 for i in s[4] if RT[i][3] and RT[i][3] < ODD)]
stamp = os.path.basename(SC).split('_')[2] if '_' in os.path.basename(SC) else ''
doc = {'schema': 'tg-ggbrt/1', 'source': '경기도 버스 API(공공데이터포털 · 정류소 경유 노선·노선 정보) — ' + os.path.basename(SC) + ' · ' + os.path.basename(AL), 'collected': stamp[:4] + '-' + stamp[4:6] + '-' + stamp[6:8],
       'note': '서울 중앙버스전용차로 정류장 405곳만 · 지역 「서울」 노선(서울 시내버스)은 뺐다 · 배차간격 = 노선 정보의 첨두·비첨두(분) · 시간당 대수 = Σ 60÷배차(계산값 · 배차 모르는 노선과 3분 미만 의심값은 빠짐) · 방면(상·하행) 구분 없이 정류장에 서는 노선 기준',
       'routes_f': '[노선, 종류, 지역, 첨두 배차(분), 비첨두 배차(분), 첫차, 막차, 기점, 종점]', 'stops_f': '[정류장 번호, 이름, 경도, 위도, [노선 번호…], 첨두 시간당 대수, 비첨두 시간당 대수, 배차 모르는 노선 수, 첨두 배차 의심값(3분 미만) 노선 수]',
       'routes': RT, 'stops': list(ST.values())}
p = os.path.join(ROOT, 'data', 'ggbrt.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt), '정류장', len(ST), '노선', len(RT), '배차 있음', sum(1 for r in RT if r[3]), os.path.getsize(p), 'B')
top = sorted(ST.values(), key=lambda s: -s[5])[:5]; print([(s[1], len(s[4]), s[5]) for s in top])
