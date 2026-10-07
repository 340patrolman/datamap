# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.88.0 — 교차로 이름 하나로(소유자 2026-10-07 「도로이름·사거리이름이 출처마다 달라 일관성이 없다 · 다 맞아야지」)
#   맞대 보니(tools/region/name-audit.py → ../교차로이름_맞대기_YYYYMMDD.md) ITS 표준노드링크 이름은 신호 교차로에서 가까운 건물·가게 이름인 곳이 많다(금호빌딩 · 히트뉴스 …)
#   → 같은 자리(40m 안) 대표 이름을 우선순위로 고른다:
#     5 경찰 T-GIS(서초·방배 · 경찰 신호 교차로 이름) > 4 경찰청 교차로계획(서울 388) · 서울 C-ITS 신호 교차로(2,779) — 「(연등)」 보조 신호는 부모 교차로 이름이라 빼고
#     > 3 ITS 이름이 교차로다운 이름(○○사거리·삼거리·교차로·IC·입구·역 …) > 2 교차로 사고 jct 이름(C-ITS·OSM) > 1 ITS 건물·가게 이름
#   r/<구>/jcnm.json 의 j 이름을 대표 이름으로 바꾸고 원래 ITS 이름은 7번째 칸 · 고른 출처는 8번째 칸 · jcnm-idx.json 도 같이 · jct.json 이름도 같은 규칙(우선 4 이상만)
#   ⚠ jcnm-bake.py 로 다시 구우면 이 도구를 뒤에 돌린다
#   py -3.12 -X utf8 tools/region/jname-bake.py
import json, os, glob, math, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r')
GOOD = re.compile(r'(사거리|삼거리|오거리|육거리|교차로|네거리|로터리|IC|JC|나들목|분기점|입구|역)(\(.*\))?$')
FACN = re.compile(r'(교|육교|고가|고가차도|터널|램프|지하차도|진입로|진출로)(\(.*\))?$|\((남|북|동|서)측\)$')   # 다리·시설 이름 — 교차로 이름으로 안 씀
def clean(n): return re.sub(r'^연\d+\)\s*', '', re.sub(r'\s*\((연등|경보|보행|점멸)\)\s*\d*$', '', re.sub(r'\s+', ' ', n or '').strip()))   # 「연2)」 연동 표시 · 「(경보)」 점멸 표시는 뗀다
PTS = []   # (lon, lat, 이름, 우선, 출처)
for l in open(os.path.join(KB, '07_API키', '신호앱', 'data', 'cits_cross_2779_20260910.txt'), encoding='utf-8'):
    p = l.strip().split('|')
    if len(p) >= 4 and '연등' not in p[1]: PTS.append((float(p[3]), float(p[2]), clean(p[1]), 4, '서울 C-ITS 신호 교차로'))   # 「(연등)」 = 부모 교차로 이름을 딴 보조 신호(예: 대검찰청 앞 「서초경찰서(연등)」) — 이름 근거로 안 씀
for l in list(open(os.path.join(KB, '07_API키', 'out', '서울교차로_388_20260910.csv'), encoding='utf-8-sig'))[1:]:
    p = l.strip().split(',')
    try:
        nm = ','.join(p[1:-2])
        if '연등' not in nm: PTS.append((float(p[-1]), float(p[-2]), clean(nm), 4.2, '경찰청 교차로계획'))
    except ValueError: pass
for x in json.load(open(os.path.join(ROOT, 'data', 'tgis-seocho.json'), encoding='utf-8'))['items']:
    if '연등' not in x[1]: PTS.append((x[3], x[2], clean(x[1]), 5, '경찰 T-GIS'))
for f in glob.glob(os.path.join(R, '*', 'jct.json')):
    if os.path.basename(os.path.dirname(f))[:2] not in ('11', '41'): continue
    for x in json.load(open(f, encoding='utf-8'))['items']: PTS.append((127.01 + x[1] / 88800, 37.49 - x[2] / 111000, x[-1][3:] if isinstance(x[-1], str) and x[-1].startswith('원래:') else x[0], 2, 'C-ITS·OSM(교차로 사고)'))   # 앞 실행에서 바꾼 이름이 아니라 원래 이름으로
G = collections.defaultdict(list); C = 0.002
for i, x in enumerate(PTS): G[(int(x[0] / C), int(x[1] / C))].append(i)
def alts(lon, lat, minp=4, r=40):
    o = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in G.get((int(lon / C) + dx, int(lat / C) + dy), []):
                x = PTS[i]
                if x[3] >= minp and math.hypot((x[0] - lon) * 88800, (x[1] - lat) * 111000) <= r and x[2] and x[2] not in o: o.append(x[2])
    return o
def best(lon, lat, minp, r=40):
    b = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in G.get((int(lon / C) + dx, int(lat / C) + dy), []):
                x = PTS[i]
                if x[3] < minp: continue
                d = math.hypot((x[0] - lon) * 88800, (x[1] - lat) * 111000)
                if d <= r and (b is None or (x[3], -d) > (PTS[b[1]][3], -b[0])): b = (d, i)
    return PTS[b[1]] if b else None
cnt = collections.Counter(); REN = {}; CAN = []; TAIL = {}
for f in glob.glob(os.path.join(R, '*', 'jcnm.json')):
    gu = os.path.basename(os.path.dirname(f))
    if gu[:2] not in ('11', '41'): continue
    j = json.load(open(f, encoding='utf-8'))
    for t in j['j']:
        if len(t) > 6: t[0] = t[6]; del t[6:]   # 다시 돌려도 처음 ITS 이름에서 · t[6] 원래 ITS 이름 · t[7] 고른 출처 · t[8] 다른 신호 이름
        if t[3] not in (1, 6): continue
        its = t[0]; good = bool(GOOD.search(its)); al = [a for a in alts(t[1], t[2]) if a.replace(' ', '') != its.replace(' ', '')]
        b = None if good else best(t[1], t[2], 2)   # v2.88.0 ITS 이름이 교차로다운 이름이면 그대로(신호 이름은 「다른 이름」) · 건물·가게 이름일 때만 바꾼다
        if b and b[2] and b[2].replace(' ', '') != its.replace(' ', ''):
            t[0] = b[2]; t += [its, b[4], ' · '.join(a for a in al if a != b[2])]; cnt[b[4]] += 1; REN[(gu, t[1], t[2])] = b[2]
        else:
            if al: t += [its, 'ITS', ' · '.join(al)]; cnt['ITS 그대로 · 신호 이름 덧붙임'] += 1
            else: cnt['ITS 그대로'] += 1
        if t[3] == 1 and not FACN.search(t[0]): CAN.append((t[1], t[2], t[0]))
        if len(t) > 6: TAIL[(gu, t[1], t[2])] = [t[0], t[6], t[7], t[8]]
    j['note'] = '교차로 이름 = 같은 자리(40m) 경찰 T-GIS → 경찰청 교차로계획·서울 C-ITS 신호 교차로 → ITS(교차로다운 이름) → OSM 순으로 고른 대표 이름 · 원래 ITS 이름은 카드 「ITS 이름」 · ITS 이름 중 건물·학교 이름은 신호·OSM 이름이 있으면 바꿨다(tools/region/jname-bake.py)'
    json.dump(j, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
pi = os.path.join(R, 'jcnm-idx.json'); I = json.load(open(pi, encoding='utf-8'))
for t in I['j']:   # 찾기 색인 = [이름, 경도, 위도, 종류, 등급, 도로, 구, 원래 ITS 이름, 출처, 신호 이름] — 지도 jcnm 과 같은 꼬리
    if len(t) > 7: t[0] = t[7] or t[0]; del t[7:]
    x = TAIL.get((t[6], t[1], t[2]))
    if x: t[0] = x[0]; t += x[1:]
json.dump(I, open(pi, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
jc = collections.Counter(); CG = collections.defaultdict(list)
for i, x in enumerate(CAN): CG[(int(x[0] / C), int(x[1] / C))].append(i)
def canon(lon, lat, r=30):   # 지도 교차로 이름(대표 이름)과 같게 — 교차로 노드(1) · 다리·시설 이름 빼고 · 30m
    b = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in CG.get((int(lon / C) + dx, int(lat / C) + dy), []):
                x = CAN[i]; d = math.hypot((x[0] - lon) * 88800, (x[1] - lat) * 111000)
                if d <= r and (b is None or d < b[0]): b = (d, x[2])
    return b[1] if b else None
for f in glob.glob(os.path.join(R, '*', 'jct.json')):
    if os.path.basename(os.path.dirname(f))[:2] not in ('11', '41'): continue
    j = json.load(open(f, encoding='utf-8')); ch = 0
    for x in j['items']:
        if isinstance(x[-1], str) and x[-1].startswith('원래:'): x[0] = x[-1][3:]; x.pop()
        nn = canon(127.01 + x[1] / 88800, 37.49 - x[2] / 111000)
        if nn and nn.replace(' ', '') != x[0].replace(' ', '') and not FACN.search(nn): x.append('원래:' + x[0]); x[0] = nn; ch += 1; jc['지도 이름에 맞춤'] += 1
    if ch: json.dump(j, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('jcnm', dict(cnt)); print('jct', dict(jc))
