# -*- coding: utf-8 -*-
# 신호 교차로마다 실제 길 방향(다리) — 신호 카드 맨 위 입체 그림이 진짜 교차로 모양으로 그려지게 (2026-10-24 · 소유자 「서울성모병원 4거리인데 모양이 부자연스러워 · 신호값 있는 교차로에 제대로 표현되는지 모두 확인」)
#   T-Data 방위는 여덟 갈래(북·북동·동…)라 30° 로 들어오는 길도 45° 로 그려졌다(교차로 2,462 중 대각선 방위 948) → 국가표준 노드링크(ITS · MOCT_LINK) 길이 교차로 둘레 원(70m)을 지나는 자리의 방향을 모아 다리로 묶는다
#   큰 교차로는 노드가 여럿이라 노드를 쓰지 않고 원과 만나는 자리만 본다 · 각도 = 화면 각도(동 0° · 남 90° · 서 180° · 북 -90° — 지도 SDA 와 같은 꼴)
# 쓰기: py -3.12 -X utf8 tools/signal/sigleg-bake.py [노드링크 폴더=C:/Users/knpth/regionwork/nl]   →  data/sig-legs.json
import json, math, os, sys, datetime, collections
import shapefile
from pyproj import Transformer
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/nl'
TM = '+proj=tmerc +lat_0=38 +lon_0=127 +k=1 +x_0=200000 +y_0=600000 +ellps=GRS80 +units=m'
R = 70.0
CL = 24.0   # 이만큼 안의 방향은 한 다리


def main():
    inv = Transformer.from_crs('EPSG:4326', TM, always_xy=True)
    ix = json.load(open(os.path.join(ROOT, 'data', 'sigdir', 'index.json'), encoding='utf-8'))
    P = {}
    for no, q in ix['pts'].items():
        if q and q[0] and q[1]:
            x, y = inv.transform(q[1], q[0]); P[no] = (x, y)
    try:   # 교통과 현시도 다섯 곳(sig-ksc-seocho) — T-Data 자리에 없는 번호(서초역사거리 4039 등)
        for x in json.load(open(os.path.join(ROOT, 'data', 'sig-ksc-seocho.json'), encoding='utf-8')).get('items', []):
            if str(x.get('no')) not in P and x.get('lat') and x.get('lon'):
                xx, yy = inv.transform(x['lon'], x['lat']); P[str(x['no'])] = (xx, yy)
    except Exception as e:
        print('현시도 자리 못 읽음', e)
    xs = [v[0] for v in P.values()]; ys = [v[1] for v in P.values()]
    bx = (min(xs) - 500, max(xs) + 500, min(ys) - 500, max(ys) + 500)
    G = collections.defaultdict(list)   # 200m 칸 → 교차로
    for no, (x, y) in P.items():
        G[(int(x // 200), int(y // 200))].append(no)
    hits = collections.defaultdict(list)
    rd = shapefile.Reader(os.path.join(SRC, 'MOCT_LINK.shp'), encoding='cp949')
    nlink = 0
    for sr in rd.iterShapes():
        pts = sr.points
        if not pts: continue
        x0, y0 = pts[0]
        if not (bx[0] < x0 < bx[1] and bx[2] < y0 < bx[3]): continue
        nlink += 1
        near = set()
        for (x, y) in pts[::max(1, len(pts) // 8)] + [pts[-1]]:
            cx, cy = int(x // 200), int(y // 200)
            for i in (-1, 0, 1):
                for j in (-1, 0, 1):
                    near.update(G.get((cx + i, cy + j), ()))
        for no in near:
            px, py = P[no]
            for k in range(len(pts) - 1):
                (ax, ay), (bx2, by2) = pts[k], pts[k + 1]
                d1 = math.hypot(ax - px, ay - py); d2 = math.hypot(bx2 - px, by2 - py)
                if (d1 - R) * (d2 - R) < 0:
                    t = (R - d1) / (d2 - d1); cx2 = ax + (bx2 - ax) * t; cy2 = ay + (by2 - ay) * t
                    hits[no].append(math.degrees(math.atan2(-(cy2 - py), cx2 - px)))   # 화면 각도(아래가 +) — TM 의 y 는 북쪽이 + 라 뒤집는다
    out = {}
    for no in P:
        a = sorted(hits.get(no, []))
        if not a: continue
        cl = []
        for v in a:
            for c in cl:
                if abs(((v - c[0] / c[1]) + 180) % 360 - 180) < CL:
                    base = c[0] / c[1]; vv = base + ((v - base + 180) % 360 - 180); c[0] += vv; c[1] += 1; break
            else:
                cl.append([v, 1])
        legs = sorted(round(((c[0] / c[1]) + 180) % 360 - 180) for c in cl)
        out[no] = legs
    doc = {'schema': 'tg-sig-legs/1', 'made': datetime.date.today().isoformat(),
           'source': '국토교통부 국가표준 노드링크(ITS · MOCT_LINK 2026-09-14) — 신호 교차로(data/sigdir/index.json pts) 둘레 %dm 원을 길이 지나는 자리의 방향' % R,
           'fields': 'legs{교차로 번호: [다리 방향(화면 각도 · 동 0 · 남 90 · 서 180 · 북 -90)…]}',
           'note': ['그림을 진짜 모양으로 그리려는 값이다 — T-Data 방위(여덟 갈래)는 가장 가까운 다리에 붙인다(지도)', '자리 좌표가 교차로 가운데에서 벗어나면 다리가 틀어질 수 있다 · 진출입로·이면도로도 다리로 잡힐 수 있다'],
           'legs': out}
    p = os.path.join(ROOT, 'data', 'sig-legs.json')
    json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    c = collections.Counter(len(v) for v in out.values())
    print('링크', nlink, '· 교차로', len(P), '· 다리 잡힘', len(out), '· 다리 수 분포', dict(sorted(c.items())), '·', os.path.getsize(p), 'B')


if __name__ == '__main__':
    main()
