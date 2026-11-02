# 🔀 합류부 목록 굽기(2026-11-02 · 소유자 「IC 나 합류지점 등 사고다발지역 원인을 찾아볼 수 있게 시뮬」)
# data/nav-six.json(국가표준 노드링크 여섯 구 판)에서 연결로(ramp=1) 링크가 본선에 붙는 노드를 찾아
# data/sim-merges.json 으로 굽는다 — 지도(js/sim-merge.js)가 5MB 도로망을 받지 않고 합류부를 고르게.
# 값은 도로망에 적힌 것만(차로 수·제한속도·길이·이름) · 가속차로 길이는 자료에 없어 넣지 않는다(지도에서 설계값).
import json, math, os, collections

ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
NAV = os.path.join(ROOT, 'data', 'nav-six.json')
RIDX = os.path.join(ROOT, 'data', 'r', 'index.json')
OUT = os.path.join(ROOT, 'data', 'sim-merges.json')


def dist(a, b):   # [lon, lat]
    return math.hypot((a[0] - b[0]) * 88200, (a[1] - b[1]) * 111000)


def main():
    d = json.load(open(NAV, encoding='utf-8'))
    N, L = d['nodes'], d['links']
    IN, OUT_ = collections.defaultdict(list), collections.defaultdict(list)
    for l in L:
        OUT_[l[1]].append(l); IN[l[2]].append(l)
    gus = json.load(open(RIDX, encoding='utf-8'))['gus']

    def gu_of(lon, lat):
        best, bd = None, 1e18
        for g in gus:
            b = g['box']
            if not (b[0] - 0.01 <= lon <= b[2] + 0.01 and b[1] - 0.01 <= lat <= b[3] + 0.01):
                continue
            for dn in g['d']:
                dd = dist([lon, lat], [dn[1], dn[2]])
                if dd < bd:
                    bd, best = dd, g
        return (best['gu'], best['name']) if best else (None, None)

    def walk(node, name, up, lim=1500):
        # 본선을 따라 다음(아래쪽) 갈라지는 곳 / 앞(위쪽) 붙는 곳까지의 거리
        s, cur, seen = 0, node, {node}
        while s < lim:
            cand = [x for x in (IN[cur] if up else OUT_[cur]) if not x[8]]
            if not cand:
                return None
            same = [x for x in cand if x[7] == name] or cand
            l = same[0]
            s += l[3]
            cur = l[1] if up else l[2]
            if cur in seen:
                return None
            seen.add(cur)
            other = [x for x in (IN[cur] if up else OUT_[cur]) if x[8]]
            if other:
                return [round(s), other[0][7] or '연결로', cur]
        return None

    items = []
    for l in L:
        if not l[8]:
            continue
        t = l[2]
        mi = [x for x in IN[t] if not x[8]]
        mo = [x for x in OUT_[t] if not x[8]]
        if not (mi and mo and len(OUT_[t]) == 1 and t in N):
            continue
        n = N[t]
        a, b = mi[0], mo[0]
        gu, gnm = gu_of(n[0], n[1])
        dn = walk(t, b[7], False)
        upm = walk(t, a[7], True)
        items.append({
            'id': t, 'nm': n[3] or '', 'lat': n[1], 'lon': n[0], 'gu': gu, 'gnm': gnm,
            'main': b[7] or a[7] or '', 'gr': b[5], 'ty': b[12] if len(b) > 12 else '000',
            'inL': a[6] or 1, 'outL': b[6] or 1, 'lim': b[4] or a[4] or 0,
            'ramp': [l[7] or '연결로', l[6] or 1, l[4] or 0, l[3]],
            'dn': dn[:2] if dn else None, 'up': upm[:2] if upm else None,
            'link': [a[0], l[0], b[0]],
        })
    items.sort(key=lambda x: (x['gr'], x['main'], x['id']))
    doc = {
        'schema': 'tg-sim-merges/1', 'made': d.get('made'),
        'source': d['source'].split(' · 신호')[0] + ' — 연결로(ramp) 링크가 본선에 붙는 노드',
        'fields': 'items = [{id 노드, nm 노드 이름, lat, lon, gu·gnm 구(행정동 가운데점이 가장 가까운 구), main 본선 이름, gr 등급 1~7, ty 도로 유형(000 일반·001 고가·002 지하·003 교량·004 터널), '
                  'inL 본선 들어오는 차로, outL 본선 나가는 차로, lim 본선 제한속도, ramp [연결로 이름, 차로, 제한속도, 붙는 링크 길이 m], dn [아래쪽 다음 갈라지는 곳까지 m, 그 연결로 이름], up [위쪽 앞 연결로까지 m, 이름], link [본선 들어옴, 연결로, 본선 나감]}]',
        'note': '차로 수·제한속도는 표준노드링크에 적힌 값(현장과 다를 수 있다) · 가속차로 길이는 자료에 없다 · 갈라지는 곳 거리는 본선 링크를 따라 1.5km 안에서만 셌다',
        'items': items,
    }
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('merges', len(items), 'bytes', os.path.getsize(OUT))
    c = collections.Counter('더해짐' if x['outL'] >= x['inL'] + x['ramp'][1] else '줄어듦' for x in items)
    print(c)
    print(collections.Counter(x['gnm'] for x in items).most_common(12))
    w = [x for x in items if x['dn'] and x['dn'][0] < 600]
    print('다음 진출 600m 안', len(w))


if __name__ == '__main__':
    main()
