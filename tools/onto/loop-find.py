# -*- coding: utf-8 -*-
# 🔁 막힘 고리 후보 찾기(2026-10-25 · 소유자 「다 하나로 · 유기적으로」 — 형님이 짚은 반포 고리와 같은 꼴이 서초 다른 곳에도 있나)
#   ontology-core core-seocho.json 의 신호 교차로 인접(sig-net) × 들어오는 길(APR 방위)로 「A 에서 B 로 들어가는 변」을 잇고
#   교차로 셋·넷이 한 방향으로 도는 닫힌 고리(둘레 ≤ PERIM m)를 모두 찾은 뒤,
#   07_API키/out/livespd 쌓인 ITS 속도에서 「변 대부분이 함께 TH km/h 이하」였던 받은 때 수로 줄 세운다.
#   ⚠ 후보일 뿐이다 — onto-loops.json 에 고리를 올리는 것은 형님이 현장에서 「맞다」 한 것만(onto-loops note).
#   결과는 저장소 밖 07_API키/out/onto_logs/loop_candidates_<날짜>.md (공개 자료로 만든 것이지만 형님 확인 전 목록이라 올리지 않는다)
#   py -3.12 -X utf8 tools/onto/loop-find.py
import os, json, math, datetime, collections, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
TH, PERIM, NEIGH_M, ANG = 10, 3200, 900, 50
DIRS = {'nt': 0, 'ne': 45, 'et': 90, 'se': 135, 'st': 180, 'sw': 225, 'wt': 270, 'nw': 315}
spec = importlib.util.spec_from_file_location('ae', os.path.join(ROOT, 'tools', 'onto', 'act-effect.py'))
ae = importlib.util.module_from_spec(spec); spec.loader.exec_module(ae)


def bearing(a, b):
    y = (b['lat'] - a['lat']) * 111000; x = (b['lon'] - a['lon']) * 111000 * math.cos(math.radians(a['lat']))
    return (math.degrees(math.atan2(x, y)) + 360) % 360, math.hypot(x, y)


def angd(a, b): return abs((a - b + 180) % 360 - 180)


def main():
    c = json.load(open(os.path.join(ROOT, 'ontology-core', 'data', 'core-seocho.json'), encoding='utf-8'))
    O = {o['id']: o for o in c['objects']}
    adj = collections.defaultdict(set); apr = collections.defaultdict(list); ir = collections.defaultdict(list)
    for e in c['edges']:
        if e[1] == '인접' and e[3].get('m', 1e9) <= NEIGH_M: adj[e[0]].add(e[2]); adj[e[2]].add(e[0])
        elif e[1] == '들어오는길': apr[e[0]].append(e[2])
        elif e[1] == '이룸': ir[e[0]].append((e[3].get('k', 0), O[e[2]]['link']))
    # 이웃 = 들어오는 길 자료가 있는 교차로끼리 NEIGH_M 안(sig-net 인접은 연동 묶음만이라 성기다 — 반포 넷 중 둘만 이어져 있었다)
    P = [i for i in apr if i in O and 'lat' in O[i]]
    for i in P:
        for j in P:
            if i < j and bearing(O[i], O[j])[1] <= NEIGH_M: adj[i].add(j); adj[j].add(i)
    # A → B : B 의 들어오는 길 방위가 B 에서 본 A 쪽과 맞을 때
    G = collections.defaultdict(dict)
    for B, aps in apr.items():
        for ap in aps:
            d = DIRS.get(O[ap].get('dir'))
            if d is None: continue
            cand = []   # 그 방위의 이웃 중 가까운 둘까지 — 가운데 신호 없는 갈림이나 작은 교차로를 건너뛴 변(반포 고리 신반포로 변처럼)도 잡게
            for A in adj[B]:
                if A not in O or 'lat' not in O[A]: continue
                bb, dist = bearing(O[B], O[A])
                if angd(bb, d) <= ANG: cand.append((dist, A))
            for dist, A in sorted(cand)[:2]:
                if B not in G[A] or dist < G[A][B][1]: G[A][B] = (ap, dist)
    cyc = set(); found = []
    for s in list(G):
        stack = [(s, [s], 0.0)]
        while stack:
            u, path, L = stack.pop()
            for v, (ap, dist) in G[u].items():
                if L + dist > PERIM: continue
                if v == s and len(path) >= 3:
                    k = min(range(len(path)), key=lambda i: path[i]); key = tuple(path[k:] + path[:k])
                    if key not in cyc: cyc.add(key); found.append((key, L + dist))
                elif v not in path and len(path) < 4: stack.append((v, path + [v], L + dist))
    S = ae.snaps(); W = '월화수목금토일'
    res = []
    for key, per in found:
        pts = [(O[i]['lon'], O[i]['lat']) for i in key]
        cr = [(pts[(i + 1) % len(pts)][0] - pts[i][0]) * (pts[(i + 2) % len(pts)][1] - pts[(i + 1) % len(pts)][1]) - (pts[(i + 1) % len(pts)][1] - pts[i][1]) * (pts[(i + 2) % len(pts)][0] - pts[(i + 1) % len(pts)][0]) for i in range(len(pts))]
        if not (all(x > 0 for x in cr) or all(x < 0 for x in cr)): continue   # 볼록한 블록만 — 꼬인 차례(같은 넷을 엇갈려 도는 것)는 블록을 도는 고리가 아니다
        legs = [G[key[i]][key[(i + 1) % len(key)]][0] for i in range(len(key))]
        lks = [[l for k, l in sorted(ir.get(a, []))] for a in legs]
        if any(not x for x in lks): continue
        need = len(legs) - 1 if len(legs) == 4 else len(legs)
        hits = []; seen = 0
        for a, m in S:
            vs = []
            for ls in lks:
                v = [m[l] for l in ls if l in m][:2]; vs.append(sum(v) / len(v) if v else None)
            k = sum(1 for x in vs if x is not None)
            if k < need: continue
            seen += 1
            if sum(1 for x in vs if x is not None and x <= TH) >= need: hits.append(a)
        eps = []; run = []
        for a in hits:
            if run and a - run[-1] <= 1500: run.append(a)
            else:
                if len(run) >= 3: eps.append(run)
                run = [a]
        if len(run) >= 3: eps.append(run)
        hits = [a for r in eps for a in r]
        days = collections.Counter(datetime.datetime.fromtimestamp(a).strftime('%m-%d') + '(' + W[datetime.datetime.fromtimestamp(a).weekday()] + ')' for a in hits)
        x0 = sum(O[i]['lon'] for i in key); y0 = sum(O[i]['lat'] for i in key)
        area = sum(O[key[i]]['lon'] * O[key[(i + 1) % len(key)]]['lat'] - O[key[(i + 1) % len(key)]]['lon'] * O[key[i]]['lat'] for i in range(len(key)))
        res.append({'ints': key, 'legs': legs, 'per': round(per), 'hits': len(hits), 'eps': len(eps), 'hrs': collections.Counter(datetime.datetime.fromtimestamp(a).hour for a in hits), 'longest': max((len(r) for r in eps), default=0), 'seen': seen, 'days': days, 'dir': '시계방향' if area < 0 else '반시계방향'})
    best = {}
    for r in res:
        k = frozenset(r['ints'])
        if k not in best or r['hits'] > best[k]['hits']: best[k] = r
    res = sorted((r for r in best.values() if r['eps']), key=lambda r: (-r['hits'], -r['eps']))
    reg = {tuple(L['members']) for L in json.load(open(os.path.join(ROOT, 'data', 'onto-loops.json'), encoding='utf-8'))['loops']}
    def regd(k): return any(set(k) == set(m) and len(k) == len(m) for m in reg)
    out = ['# 막힘 고리 후보 — 서초 · %s' % datetime.date.today().isoformat(), '',
           '찾은 닫힌 고리 %d개(교차로 셋·넷 · 둘레 %dm 이하 · 이웃 %dm 이하) · 쌓인 속도 %d장 · 「함께 막힘」 = 넷이면 셋 이상, 셋이면 셋 다 %dkm/h 이하' % (len(res), PERIM, NEIGH_M, len(S), TH), '',
           '⚠ 후보다 — 방위로 변을 이었기 때문에 대각 교차로는 어긋날 수 있다 · onto-loops 에 올리는 것은 형님이 현장에서 맞다 한 것만', '',
           '| 차례 | 교차로(도는 차례) | 방향 | 둘레 | 이어진 막힘 토막(30분↑) · 가장 긴 것 · 받은 때 합 | 날 | 많은 시각 | 등록 |', '|---|---|---|---|---|---|---|---|']
    for i, r in enumerate(res[:25], 1):
        out.append('| %d | %s | %s | %dm | %s | %s | %s | %s |' % (i, ' → '.join('%s(%s)' % (O[x]['nm'], x) for x in r['ints']), r['dir'], r['per'], '%d토막 · 약 %d분 · %d' % (r['eps'], r['longest'] * 11, r['hits']),
                   ' '.join('%s %d' % (d, n) for d, n in sorted(r['days'].items())) or '—', ' '.join('%d시 %d' % (h, n) for h, n in r['hrs'].most_common(4)), '✅ 형님 지정' if regd(r['ints']) else ''))
    p = os.path.join(KB, '07_API키', 'out', 'onto_logs', 'loop_candidates_%s.md' % datetime.date.today().strftime('%Y%m%d'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('\n'.join(out[:20])); print('→', p)


if __name__ == '__main__':
    main()
