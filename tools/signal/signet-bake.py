# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🔗 신호 교차로 이음표(소유자 2026-10-10 밤 「교차로별 번호로 연결 및 신호값 데이터를 만들어야겠어 · 이건 따로」)
#   신호값이 붙은 교차로를 **교차로 번호**로 묶고, 「이 신호 다음에 만나는 신호」를 길을 따라 이은 표.
#   → data/sig-net-seocho.json (tg-sig-net/1)
#     nodes{교차로 번호: {nm 이름, ll [경도, 위도], src [자료 갈래…], its [붙은 ITS 노드 ID…], files {어느 파일에 값이 있나}}}
#     links[[떠나는 번호, 닿는 번호, 길이 m, 제한속도로 달리는 초, 떠나는 방위, 닿는 교차로에서 「들어오는 쪽」, 길 이름, 제한속도(가장 낮은 값), 사이의 신호 없는 교차점 수, 지나는 링크 수]]
#   재료 = data/nav-seocho.json(다른 세션 navgraph-bake.py — ITS 표준노드링크의 노드·방향 있는 링크·제한속도 + 노드마다 붙은 신호 자료)
#   법 = 신호 교차로의 노드에서 나가는 길마다 **곧게 따라가다**(갈림에서는 가장 덜 꺾이는 길 · 50° 넘게 꺾어야 하면 그친다) 다른 신호 교차로를 만나면 멈춘다(2.5km 까지) — 「이 길로 곧장 가면 다음에 만나는 신호」.
#   ⚠ 신호 자료가 없는 교차로는 「신호 없는 교차점」으로 센다 — 실제로는 신호등이 있는데 자료만 없는 곳일 수 있다(그래서 사이 교차점 수를 같이 적는다 · 0 이면 믿을 만하다).
#   py -3.12 -X utf8 tools/signal/signet-bake.py        (신호 자료가 늘면 navgraph-bake.py 를 먼저 다시 돌린 뒤)
import json, os, io, math, heapq, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIR8 = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw']
KO8 = {'nt': '북', 'ne': '북동', 'et': '동', 'se': '남동', 'st': '남', 'sw': '남서', 'wt': '서', 'nw': '북서'}
MAXM = 2500.0


def bearing(a, b):
    """a → b 방위(도 · 0 북 · 90 동) — 경위도 두 점"""
    dx = (b[0] - a[0]) * math.cos(math.radians((a[1] + b[1]) / 2)); dy = b[1] - a[1]
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360


def dir8(deg):
    return DIR8[int(((deg + 22.5) % 360) // 45)]


def pts(c):
    x, y, o = c[0], c[1], [(c[0] / 1e5, c[1] / 1e5)]
    for i in range(2, len(c), 2):
        x += c[i]; y += c[i + 1]; o.append((x / 1e5, y / 1e5))
    return o


def main():
    nav = json.load(io.open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8'))
    N, L = nav['nodes'], nav['links']
    out = collections.defaultdict(list)
    for k, l in enumerate(L):
        out[l[1]].append(k)
    # 노드 → 교차로 번호(교통과 → T-Data → 경찰청 차례 · 번호 체계는 셋이 같다)
    num, info = {}, {}
    for nid, v in N.items():
        sg = v[7] if len(v) > 7 else None
        if not sg: continue
        no = nm = None; src = []
        for key in ('ksc', 'sd', 'tod'):
            if sg.get(key):
                src.append({'ksc': '교통과 현시도', 'sd': '서울시 T-Data', 'tod': '경찰청 신호계획'}[key])
                if no is None: no, nm = str(sg[key][0]), sg[key][1]
        if no is None: continue
        num[nid] = no
        o = info.setdefault(no, {'nm': nm, 'll': [v[0], v[1]], 'src': [], 'its': [], 'in': v[4], '_d': 1e9})
        for s0 in src:
            if s0 not in o['src']: o['src'].append(s0)
        o['its'].append(nid)
        d = min([sg[k][-1] for k in ('ksc', 'sd', 'tod') if sg.get(k) and isinstance(sg[k][-1], (int, float))] or [1e9])
        if d < o['_d']: o['_d'] = d; o['ll'] = [v[0], v[1]]; o['in'] = v[4]
    # 큰 교차로는 ITS 노드가 여럿이다(상·하행이 갈린 길 — 귀퉁이마다 노드). 신호는 그중 한 노드에만 붙어 있어, 그대로 두면 한쪽 방향만 이어진다
    #   → 신호 자리에서 55m 안의 교차로 노드(유형 101 · 링크 셋 이상)를 같은 번호로 묶는다(더 가까운 신호가 있으면 그쪽)
    def dm(a, b):
        return math.hypot((a[0] - b[0]) * 88800 * math.cos(math.radians(a[1])) / math.cos(math.radians(37.49)), (a[1] - b[1]) * 111000)
    for nid, v in N.items():
        if nid in num or v[2] != '101' or v[5] < 3: continue
        bd, bn = 55.0, None
        for no, o in info.items():
            d = dm((v[0], v[1]), o['ll'])
            if d < bd: bd, bn = d, no
        if bn:
            num[nid] = bn; info[bn]['its'].append(nid)
    # 이음 — 신호 노드에서 나가는 길마다 **곧게 따라가다**(갈림에서는 꺾임이 가장 작은 길 · 50° 넘게 꺾어야 하면 그친다) 다른 번호의 신호 노드를 만나면 멈춘다.
    #   (처음에는 가장 빠른 길로 퍼지게 했더니 신호 자료 없는 교차점에서 사방으로 번져 195곳에 2,739짝이 나왔다 — 「이 길로 가면 다음에 만나는 신호」가 아니었다)
    G = [pts(l[9]) for l in L]
    H0 = [bearing(g[0], g[min(len(g) - 1, 2)]) for g in G]                 # 링크 첫머리 방위
    H1 = [bearing(g[max(0, len(g) - 3)], g[-1]) for g in G]               # 링크 끝머리 방위
    def turn(a, b):
        d = abs(a - b) % 360
        return min(d, 360 - d)
    best = {}
    for s in num:
        for k0 in out.get(s, []):
            k, m, t, mid, nl, spd, name, prev = k0, 0.0, 0.0, 0, 0, 999, L[k0][7] or '', s
            seenk = set()
            while True:
                l = L[k]; v = l[2]; ln = float(l[3] or 0); sp = float(l[4] or 0) or 30.0
                m += ln; t += ln / (sp / 3.6); nl += 1; spd = min(spd, int(sp)); seenk.add(k)
                if m > MAXM: break
                if num.get(v) and num[v] != num[s]:
                    key = (num[s], num[v])
                    rec = [num[s], num[v], int(round(m)), int(round(t)), dir8(H0[k0]), dir8((H1[k] + 180) % 360), name, spd, mid, nl]
                    if key not in best or rec[3] < best[key][3]: best[key] = rec
                    break
                if not num.get(v) and N[v][2] == '101' and N[v][5] >= 3: mid += 1
                cand = [(turn(H1[k], H0[q]), q) for q in out.get(v, []) if L[q][2] != prev and q not in seenk]
                if not cand: break
                dmin, q = min(cand)
                if dmin > 50: break
                prev, k = v, q
    links = sorted(best.values(), key=lambda r: (r[0], r[3]))
    # 같은 번호에서 너무 가까운 것(같은 교차로의 다른 노드로 본 짝)은 뺀다
    links = [r for r in links if r[2] >= 40]
    nodes = {}
    for no, o in sorted(info.items()):
        files = {}
        if '교통과 현시도' in o['src']: files['교통과 현시도'] = 'data/sig-ksc-seocho.json · items[no]'
        if '서울시 T-Data' in o['src']: files['서울시 T-Data'] = 'data/sigdir-seoul.json · its[번호](방향별 초·닻) · pl[번호](시각대 표)'
        if '경찰청 신호계획' in o['src']: files['경찰청 신호계획'] = 'data/signal-tod-seoul.json · spots[no] · 방향 = data/sig-phmv-seoul.json'
        nodes[no] = {'nm': o['nm'], 'll': o['ll'], 'in': o['in'], 'src': o['src'], 'its': o['its'], 'files': files}
    deg = collections.Counter(r[0] for r in links)
    doc = {
        'schema': 'tg-sig-net/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
        'area': nav.get('area'),
        'source': '이음 = data/nav-seocho.json(국가교통정보센터 ITS 전국 표준노드링크 2026-09-14판 — 노드·방향 있는 링크·길이·제한속도) · 신호 = 서울시 교통빅데이터플랫폼 T-Data · 경찰청 교차로계획정보 · 서초경찰서 교통과 현시도',
        'how': '신호 자료가 붙은 교차로의 노드에서 나가는 길마다 곧게 따라가다(방향을 지켜 · 갈림에서는 가장 덜 꺾이는 길 · 50° 넘게 꺾어야 하면 그친다) 다른 신호 교차로를 만나면 멈춘다 — 「이 길로 곧장 가면 다음에 만나는 신호」. 2.5km 까지 · 꺾어서 가는 짝은 없다.',
        'fields': 'nodes{교차로 번호(서울 C-ITS·T-Data·경찰청·교통과가 같은 번호): {nm 이름, ll [경도, 위도], in 서초구 안 1/밖 0, src [자료 갈래…], its [붙은 ITS 노드 ID…], files {갈래: 값이 든 파일과 자리}}} · links[[떠나는 번호, 닿는 번호, 길이 m, 제한속도로 달리는 초, 떠나는 방위(nt 북 · ne · et 동 · se · st 남 · sw · wt 서 · nw — 가는 쪽), 닿는 교차로에서 들어오는 쪽(같은 부호 — 신호 자료의 「○쪽에서 오는 차」와 같은 뜻), 처음 길 이름, 가는 길의 가장 낮은 제한속도 km/h, 사이의 신호 자료 없는 교차점 수(링크 셋 이상이 만나는 곳), 지나는 링크 수]]',
        'note': [
            '**신호값 자체는 이 파일에 없다** — 번호로 files 의 파일을 찾아 읽는다(값이 날마다 늘어 한곳에만 둔다).',
            '사이의 「신호 자료 없는 교차점」은 신호등이 없다는 뜻이 아니다 — 자료만 없는 신호 교차로일 수 있다. 0 인 짝이 가장 믿을 만하다.',
            '초 = 제한속도로 막힘없이 달릴 때(신호·정체 없음) · 길이는 링크 길이의 합 · 방향은 링크의 첫머리·끝머리 방위를 8방으로 접은 것.',
            '신호 자료가 늘면 navgraph-bake.py 를 다시 돌린 뒤 이 도구를 다시 돌린다.'],
        'count': {'교차로': len(nodes), '이음': len(links), '사이 교차점 0': sum(1 for r in links if r[8] == 0), '이음 없는 교차로': sum(1 for no in nodes if not deg.get(no))},
        'nodes': nodes, 'links': links}
    p = os.path.join(ROOT, 'data', 'sig-net-seocho.json')
    io.open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    print(doc['count'], '->', p, os.path.getsize(p), 'B')
    for r in links[:6]: print('  ', nodes[r[0]]['nm'], '→', nodes[r[1]]['nm'], r[2], 'm', r[3], '초', KO8[r[4]] + '쪽으로', KO8[r[5]] + '쪽에서 들어감', r[6], r[7], 'km/h 사이', r[8])


if __name__ == '__main__':
    main()
