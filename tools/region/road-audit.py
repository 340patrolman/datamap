# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.88.0 — 도로 이름 맞대기(ITS 표준노드링크 링크 도로명 vs OpenStreetMap 도로명 — 서울·경기)
#   ITS = r/<구>/jcnm.json 의 r(도로 이름 표 자리 · [이름, 경도, 위도, 기울기, 등급]) · OSM = kr.pbf highway 이름(name)
#   같은 자리 = 25m 안 · 방향 30° 안 OSM 길 · 이름 견주기(띄어쓰기 무시) → 같음 / 다름 · 다른 곳은 ../도로이름_맞대기_YYYYMMDD.md · data/road-name-map.json(ITS 이름 → OSM 이름 · 자리)
#   py -3.12 -X utf8 tools/region/road-audit.py
import json, os, glob, math, re, collections, time
import osmium
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r')
CAP = (126.30, 36.85, 127.90, 38.32)
def nz(s): return re.sub(r'\s', '', s or '')
SEG = []; G = collections.defaultdict(list); C = 0.001
t0 = time.time()
fp = osmium.FileProcessor('C:/Users/knpth/osmwork/kr.pbf').with_locations().with_filter(osmium.filter.KeyFilter('highway'))
for o in fp:
    if not o.is_way(): continue
    nm = o.tags.get('name')
    if not nm or o.tags.get('highway') in ('footway', 'path', 'steps', 'cycleway', 'pedestrian', 'track', 'service'): continue
    try: pts = [(n.location.lon, n.location.lat) for n in o.nodes]
    except Exception: continue
    if not any(CAP[0] <= p[0] <= CAP[2] and CAP[1] <= p[1] <= CAP[3] for p in pts): continue
    for a, b in zip(pts, pts[1:]):
        i = len(SEG); SEG.append((a, b, nm, o.tags.get('ref') or ''))
        for x in range(int(min(a[0], b[0]) / C), int(max(a[0], b[0]) / C) + 1):
            for y in range(int(min(a[1], b[1]) / C), int(max(a[1], b[1]) / C) + 1): G[(x, y)].append(i)
print('OSM 조각', len(SEG), round(time.time() - t0), 's', flush=True)
def dseg(p, a, b):
    ax, ay = (a[0] - p[0]) * 88800, (a[1] - p[1]) * 111000; bx, by = (b[0] - p[0]) * 88800, (b[1] - p[1]) * 111000; vx, vy = bx - ax, by - ay; L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, -(ax * vx + ay * vy) / L)); return math.hypot(ax + vx * t, ay + vy * t), math.degrees(math.atan2(vy, vx))
cnt = collections.Counter(); DIFF = collections.defaultdict(lambda: collections.Counter()); WHERE = {}
KEEP = re.compile(r'(고속도로|간선도로|순환도로|도시고속화도로|도시고속도로|고속화도로)$')   # 다들 부르는 노선 이름 — ITS 를 보이고 도로명주소 이름은 「다른 이름」
ROUTE = re.compile(r'(국도|지방도|국지도|시도|군도)\d*호선$|\d+호선$')   # 노선 번호 — 도로명주소 이름을 보이고 번호는 카드에
FILES = {}; TOT = collections.Counter()
for f in glob.glob(os.path.join(R, '*', 'jcnm.json')):
    gu = os.path.basename(os.path.dirname(f))
    if gu[:2] not in ('11', '41'): continue
    J = json.load(open(f, encoding='utf-8')); FILES[f] = J
    for r in J.get('r', []):
        del r[5:]   # 다시 돌려도 처음부터 · r[5] OSM 이름(다를 때) · r[6] 보일 쪽 'osm'|'its'
        nm, lo, la, ang = r[0], r[1], r[2], r[3]; best = None
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in G.get((int(lo / C) + dx, int(la / C) + dy), []):
                    d, an = dseg((lo, la), SEG[i][0], SEG[i][1]); da = abs((an - ang + 90) % 180 - 90)
                    if d <= 25 and da <= 30 and (best is None or d < best[0]): best = (d, i)
        if not best: cnt['OSM 이름 길 없음(25m)'] += 1; continue
        on = re.sub(r'\s*\(.*?\)$', '', SEG[best[1]][2]).strip()   # 「섬강로 (남한강 자전거길)」 → 섬강로
        if nz(on) == nz(nm): cnt['같음'] += 1
        else:
            cnt['다름'] += 1; DIFF[gu][(nm, on)] += 1; WHERE.setdefault((gu, nm, on), (la, lo))
        TOT[(gu, nm)] += 1
FAC = re.compile(r'(고가차도|지하차도|고가도로|터널|교|육교|램프|진입로|진출로)$')
DEC = {}   # (구, ITS 이름) → OSM 이름 — 한 구 안에서 그 ITS 이름 표 자리 3곳 이상 · 60% 이상이 같은 OSM 이름일 때만(옆 길·고가·지하차도에 잘못 붙은 것 거르기)
for gu, D in DIFF.items():
    by = collections.defaultdict(list)
    for (a, b), v in D.items(): by[a].append((v, b))
    for a, L in by.items():
        v, b = max(L)
        if v >= 3 and v / TOT[(gu, a)] >= 0.6 and not FAC.search(b) and not re.search(r'자전거|BRT|둘레길|산책|누리길', b): DEC[(gu, a)] = b   # 자전거길·BRT 같은 OSM 이름은 도로명이 아니다
cnt['바꾼 짝(구×이름)'] = len(DEC)
for f, J in FILES.items():
    gu = os.path.basename(os.path.dirname(f))
    for r in J.get('r', []):
        b = DEC.get((gu, r[0]))
        if b: r += [b, 'its' if KEEP.search(r[0]) and not ROUTE.search(r[0]) else 'osm']
pi = os.path.join(R, 'jcnm-idx.json'); I = json.load(open(pi, encoding='utf-8'))
for t in I['r']:   # 찾기 색인 [이름, 경도, 위도, 구, 등급] → 다르면 [.., OSM 이름, 보일 쪽]
    del t[5:]
    b2 = DEC.get((t[3], t[0]))
    if b2: t += [b2, 'its' if KEEP.search(t[0]) and not ROUTE.search(t[0]) else 'osm']
json.dump(I, open(pi, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
for f, J in FILES.items():
    J['rnote'] = '도로 이름 = 같은 자리(25m · 방향 30°) OSM 도로명주소 이름과 다르면 — 보통 도로·노선 번호는 도로명주소 이름을 보이고 ITS 이름은 「다른 이름」 · 고속도로·간선도로·순환도로 같은 노선 통칭은 ITS 를 보이고 도로명주소 이름은 「다른 이름」(tools/region/road-audit.py)'
    json.dump(J, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
md = ['# 도로 이름 맞대기 — ITS 표준노드링크 vs OpenStreetMap(서울·경기 · ' + time.strftime('%Y-%m-%d') + ')', '', '같은 자리 = ITS 도로 이름 표 자리에서 25m 안 · 방향 30° 안 OSM 길. ' + ' · '.join('%s %d' % kv for kv in cnt.items()), '']
pairs = collections.Counter()
for gu, D in DIFF.items():
    for k, v in D.items(): pairs[k] += v
md += ['## 다른 짝 — 많은 순(ITS 이름 → OSM 이름 · 표 자리 수)', '', '| ITS 이름 | OSM 이름 | 자리 수 | 한 곳(위도, 경도) |', '|---|---|---|---|']
for (a, b), v in pairs.most_common(400):
    g0 = next(g for g in DIFF if (a, b) in DIFF[g]); w = WHERE[(g0, a, b)]; md.append('| %s | %s | %d | %.5f, %.5f |' % (a, b, v, w[0], w[1]))
out = os.path.join(KB, '도로이름_맞대기_' + time.strftime('%Y%m%d') + '.md'); open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n')
print(dict(cnt), len(pairs), '짝', out)
