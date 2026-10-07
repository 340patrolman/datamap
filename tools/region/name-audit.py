# -*- coding: utf-8 -*-
# 데이터 압축지도 — 교차로 이름 맞대기(소유자 2026-10-07 「도로이름·사거리이름이 출처마다 달라 일관성이 없다 · 서울도 경기도 가장 심해 · 다 맞아야지」)
#   기준 = ITS 국가교통정보센터 전국 표준노드링크(r/<구>/jcnm.json · 교차로·IC 노드 이름)
#   맞대는 것: 서울 C-ITS 신호 교차로(07_API키/신호앱/data/cits_cross_2779) · 경찰청 교차로계획 388(out/서울교차로_388) · 교차로 사고 jct.json(C-ITS+OSM 이름) · 서초 T-GIS(tgis-seocho) · 서초 교차로 카드(intersections-seocho · OSM)
#   같은 자리 = 40m 안 가장 가까운 ITS 노드 · 이름 견주기: 같음 / 띄어쓰기·괄호만 다름 / 끝말(사거리·삼거리·오거리·교차로·입구·앞)만 다름 / 다름
#   → ../교차로이름_맞대기_YYYYMMDD.md(소유자 보기) + data/name-map.json(지도가 「ITS 이름 · 다른 이름」으로 쓸 표)
import json, os, glob, math, re, csv, collections, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r')
def n0(s): return re.sub(r'\s|[·.,\-_/]|\(.*?\)|（.*?）', '', s or '')
SUF = re.compile(r'(사거리|삼거리|오거리|육거리|교차로|입구|앞|교차점|네거리|로터리|IC|JC|나들목|분기점)+$')
def n1(s): return SUF.sub('', n0(s))
def cmp(a, b):
    if a == b: return 'same'
    if n0(a) == n0(b): return 'space'
    if n1(a) == n1(b) and n1(a): return 'suffix'
    if n1(a) and n1(b) and (n1(a) in n1(b) or n1(b) in n1(a)): return 'part'
    return 'diff'
ITS = []   # [lon, lat, name, gu, kind]
for f in glob.glob(os.path.join(R, '*', 'jcnm.json')):
    gu = os.path.basename(os.path.dirname(f))
    if gu[:2] not in ('11', '41'): continue
    for x in json.load(open(f, encoding='utf-8'))['j']:
        if x[3] in (1, 6): ITS.append((x[1], x[2], x[0], gu, x[3]))
G = collections.defaultdict(list); C = 0.002
for i, x in enumerate(ITS): G[(int(x[0] / C), int(x[1] / C))].append(i)
def near(lon, lat, r=40):
    best = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in G.get((int(lon / C) + dx, int(lat / C) + dy), []):
                x = ITS[i]; d = math.hypot((x[0] - lon) * 88800, (x[1] - lat) * 111000)
                if d <= r and (best is None or d < best[0]): best = (d, i)
    return best
SRC = []   # (출처, 이름, lon, lat)
for l in open(os.path.join(KB, '07_API키', '신호앱', 'data', 'cits_cross_2779_20260910.txt'), encoding='utf-8'):
    p = l.strip().split('|')
    if len(p) >= 4 and '연등' not in p[1]: SRC.append(('서울 C-ITS', p[1], float(p[3]), float(p[2])))
for l in list(open(os.path.join(KB, '07_API키', 'out', '서울교차로_388_20260910.csv'), encoding='utf-8-sig'))[1:]:   # 이름에 쉼표가 든 줄이 있어 끝 두 칸을 좌표로
    p = l.strip().split(',')
    try: SRC.append(('경찰청 교차로계획', ','.join(p[1:-2]), float(p[-1]), float(p[-2])))
    except ValueError: pass
for f in glob.glob(os.path.join(R, '*', 'jct.json')):
    gu = os.path.basename(os.path.dirname(f))
    if gu[:2] not in ('11', '41'): continue
    for x in json.load(open(f, encoding='utf-8'))['items']: SRC.append(('교차로 사고(jct)', x[0], 127.01 + x[1] / 88800, 37.49 - x[2] / 111000))
T = json.load(open(os.path.join(ROOT, 'data', 'tgis-seocho.json'), encoding='utf-8'))
for x in T['items']: SRC.append(('경찰 T-GIS(서초·방배)', x[1], x[3], x[2]))
X = json.load(open(os.path.join(ROOT, 'data', 'intersections-seocho.json'), encoding='utf-8'))
for x in X.get('items', X.get('nodes', [])):
    if isinstance(x, dict) and x.get('name') and x.get('lat'): SRC.append(('서초 교차로 카드(OSM)', x['name'], x['lon'], x['lat']))
CNT = collections.defaultdict(collections.Counter); ROWS = collections.defaultdict(list); MAP = {}
for s, nm, lo, la in SRC:
    b = near(lo, la)
    if not b: CNT[s]['ITS 없음(40m)'] += 1; continue
    it = ITS[b[1]]; c = cmp(nm, it[2]); CNT[s][c] += 1
    if c != 'same': ROWS[s].append((it[3], it[2], nm, round(b[0]), c, la, lo))
    key = '%.5f,%.5f' % (it[0], it[1]); M = MAP.setdefault(key, {'its': it[2], 'gu': it[3], 'alt': {}})
    if c != 'same': M['alt'].setdefault(nm, []).append(s)
lab = {'same': '같음', 'space': '띄어쓰기·괄호만', 'suffix': '끝말만(사거리·삼거리·교차로 등)', 'part': '한쪽이 다른 쪽을 품음', 'diff': '다름', 'ITS 없음(40m)': 'ITS 노드 40m 안에 없음'}
md = ['# 교차로 이름 맞대기 — 서울·경기 (' + time.strftime('%Y-%m-%d') + ')', '', '기준 = ITS 국가교통정보센터 전국 표준노드링크(2026-09-14판 · 교차로·IC 노드) · 같은 자리 = 40m 안 가장 가까운 ITS 노드.', '', '| 출처 | ' + ' | '.join(lab.values()) + ' |', '|---|' + '---|' * len(lab)]
for s in CNT: md.append('| ' + s + ' | ' + ' | '.join(str(CNT[s].get(k, 0)) for k in lab) + ' |')
for s, L in ROWS.items():
    md += ['', '## ' + s + ' — ITS 와 다른 곳 ' + str(len(L)) + '곳(「다름」 먼저)', '', '| 구 | ITS 이름 | 이 출처 이름 | 거리 | 갈래 | 위도, 경도 |', '|---|---|---|---|---|---|']
    for r in sorted(L, key=lambda r: ({'diff': 0, 'part': 1, 'suffix': 2, 'space': 3}[r[4]], r[0])): md.append('| %s | %s | %s | %dm | %s | %.5f, %.5f |' % (r[0], r[1], r[2], r[3], lab[r[4]], r[5], r[6]))
out = os.path.join(KB, '교차로이름_맞대기_' + time.strftime('%Y%m%d') + '.md'); open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n')
json.dump({'schema': 'tg-namemap/1', 'base': 'ITS 국가교통정보센터 전국 표준노드링크(2026-09-14판)', 'note': '같은 자리(40m 안) 다른 출처 이름 → ITS 이름 · alt = {다른 이름: [출처…]}', 'map': {k: v for k, v in MAP.items() if v['alt']}},
          open(os.path.join(ROOT, 'data', 'name-map.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
for s in CNT: print(s, dict(CNT[s]))
print(out)
