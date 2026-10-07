# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.74.0 — 🚇 전국 도시철도역 자리(서울 밖 역 「준비 중」 해제)
#   원자료: 07_API키/out/subway/station_master_YYYYMMDD.xlsx — 전국도시철도역사정보표준데이터(data.go.kr 15013205 · 국가철도공단 · 레일포털 「전체_도시철도역사정보」 · 1,099역)
#   서울 역(data/r/stations.json · 서울시 역사마스터 784)은 그대로 두고, 거기 없는 역만 data/stations-kr.json 에 담는다.
#   겹침 = 같은 역명(괄호·끝 「역」 뗌)이 1km 안에 이미 있으면 같은 역 — 두 자료의 노선 이름 표기가 달라(「2」 · 「2호선」 · 「서울 도시철도 9호선」) 노선 대신 거리로 가른다.
#   py -3.12 -X utf8 tools/region/stations-kr-bake.py
import json, os, glob, re, math, collections
import openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sorted(glob.glob(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subway', 'station_master_*.xlsx')))[-1]
def nm(s): return re.sub(r'역$', '', re.sub(r'\(.*?\)', '', str(s)).strip())
def dist(a, b): return math.hypot((a[0] - b[0]) * 111320 * math.cos(math.radians(a[1])), (a[1] - b[1]) * 110540)
SE = collections.defaultdict(list); ALL = []
for x in json.load(open(os.path.join(ROOT, 'data', 'r', 'stations.json'), encoding='utf-8'))['items']: SE[nm(x[0])].append((x[2], x[3])); ALL.append((x[2], x[3]))
R = list(openpyxl.load_workbook(SRC, read_only=True).active.iter_rows(values_only=True)); H = {h: i for i, h in enumerate(R[0])}
out, dup, seen, base = [], 0, set(), None
for r in R[1:]:
    n = nm(r[H['역사명']]); ll = (round(float(r[H['역경도']]), 5), round(float(r[H['역위도']]), 5)); ln = str(r[H['노선명']]).strip()
    if any(dist(ll, q) <= 1000 for q in SE.get(n, [])) or any(dist(ll, q) <= 150 for q in ALL): dup += 1; continue   # 이름이 바뀐 역(뚝섬유원지→자양 등)은 150m 안 서울 역이면 같은 역
    k = (n, ln, ll)
    if k in seen: continue
    seen.add(k); out.append([n, ln, ll[0], ll[1], str(r[H['운영기관명']] or '').strip()])
    d = r[H['데이터기준일자']]; d = d.strftime('%Y-%m-%d') if hasattr(d, 'strftime') else str(d)
    base = max(base or d, d)
doc = {'schema': 'tg-stations/1', 'source': '전국도시철도역사정보표준데이터(공공데이터포털 15013205 · 국가철도공단 레일포털 · 기준일 ' + str(base) + ' 무렵) — 서울시 역사마스터(data/r/stations.json)에 없는 역만', 'note': '같은 역명이 1km 안에 · 또는 이름과 상관없이 150m 안에 서울 역이 있으면 서울 자료를 쓴다(노선 이름 표기가 두 자료에서 달라 거리로 가름) · 항목 = [역명, 노선명, 경도, 위도, 운영기관]', 'file': os.path.basename(SRC), 'items': out}
p = os.path.join(ROOT, 'data', 'stations-kr.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('원자료', len(R) - 1, '· 서울과 겹침', dup, '· 새로', len(out), '·', os.path.getsize(p), 'B'); print(collections.Counter(x[4] for x in out).most_common())
