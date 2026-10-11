# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌧 겹과 겹을 잇는 첫 화살표: 폭우 → 침수 이력 길 → 통제 → 우회(소유자 2026-10-11 「폭우(자연) → 침수이력 도로 침수 → 교통통제 → 우회로 혼잡 → 출동 지연 …
#   이걸 풀면 『어디를 먼저 통제해야 하는가』가 계산돼요」 · ONTOLOGY.md §0 영향의 겹) → data/flood-link-seocho.json
#   ① 자연 → 만든 조건: 침수 흔적(서울시 침수흔적도 2010~2025 — data/season-seocho.json traces)이 30m 안에 있는 길 조각(data/nav-seocho.json 의 ITS 링크)마다
#        침수 흔적이 찍힌 해 수 · 마지막 해 · 가장 깊었던 침수심 — **건물·필지가 잠긴 자리의 가운데 점**이라 「그 길이 잠겼다」는 기록이 아니다(가까이에서 잠긴 적이 있다)
#   ② 통제 → 우회: 그 길 조각이 막히면(같은 링크 하나) 그 양 끝을 잇는 가장 빠른 다른 길이 얼마나 더 걸리나(제한속도 · 막힘 없음 · 회전 제한 무시) — 다른 길이 없으면 「돌아갈 길 없음」
#   「어디를 먼저 통제·대비하나」의 **재료**다: 잠긴 해 수(일어날 법함) × 돌아가는 부담(끊겼을 때의 아픔) × 차로(다니는 차의 양의 어림) — 한 점수로 뭉치지 않고 셋을 따로 싣는다(무게를 지어내지 않는다)
#   범위 = 서초구 + 2km(nav-seocho.json) · 침수 흔적 자료가 든 서초 둘레
#   py -3.12 -X utf8 tools/signal/floodlink-bake.py
import json, os, math, heapq, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def main():
    nav = json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8')); N = nav['nodes']; L = nav['links']
    se = json.load(open(os.path.join(ROOT, 'data', 'season-seocho.json'), encoding='utf-8')); TR = se['traces']
    grid = collections.defaultdict(list)   # 침수 흔적을 평면 m 30m 칸에
    for x, z, yr, n, dep, cz, zn in TR: grid[(x // 30, z // 30)].append((x, z, yr, dep))
    def xz(lon, lat): return (lon - 127.01) * 88800.0, -(lat - 37.49) * 111000.0
    out = collections.defaultdict(list)
    for i, x in enumerate(L): out[x[1]].append(i)
    rows = []
    for i, x in enumerate(L):
        if x[5] > 6: continue
        c = x[9]; a = b = 0; pts = []
        for k in range(0, len(c), 2): a += c[k]; b += c[k + 1]; pts.append(xz(a / 1e5, b / 1e5))
        yrs = set(); dmax = 0.0; cnt = 0; seen = set()
        for p, q in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(q[0] - p[0], q[1] - p[1]) // 20))
            for s in range(n + 1):
                u = p[0] + (q[0] - p[0]) * s / n; v = p[1] + (q[1] - p[1]) * s / n
                for dx in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        for tx, tz, yr, dep in grid.get((int(u // 30) + dx, int(v // 30) + dz), ()):
                            if (tx, tz, yr) in seen or math.hypot(tx - u, tz - v) > 30: continue
                            seen.add((tx, tz, yr)); yrs.add(yr); cnt += 1; dmax = max(dmax, dep or 0)
        if not yrs: continue
        rows.append([i, len(yrs), max(yrs), round(dmax, 1), cnt])
    # 돌아가는 부담 — 그 링크를 빼고 양 끝을 잇는 가장 빠른 길(초) − 그 링크를 달리는 시간
    def t(x): return x[3] / (max(x[4], 20) / 3.6)
    def detour(i):
        x = L[i]; src, dst = x[1], x[2]; D = {src: 0.0}; h = [(0.0, src)]; lim = t(x) + 900
        while h:
            d, u = heapq.heappop(h)
            if d > D.get(u, 1e18) or d > lim: continue
            if u == dst: return d - t(x)
            for j in out.get(u, ()):
                if j == i: continue
                nd = d + t(L[j])
                if nd < D.get(L[j][2], 1e18): D[L[j][2]] = nd; heapq.heappush(h, (nd, L[j][2]))
        return None
    items = []
    for i, ny, last, dmax, cnt in rows:
        x = L[i]
        if ny < 2 and x[5] > 4: continue   # 큰길(등급 1~4)은 한 해라도, 그 밖은 두 해 이상 찍힌 곳만
        dt = detour(i)
        items.append([x[0], x[7], x[5], x[6], x[3], ny, last, dmax, cnt, -1 if dt is None else round(dt), x[12] if len(x) > 12 else '000', x[9]])
    items.sort(key=lambda r: (-r[5], -(r[9] if r[9] >= 0 else 9999), -r[3]))
    doc = {'schema': 'tg-flood-link/1', 'made': datetime.date.today().isoformat(), 'area': '서초구 + 경계 밖 2km',
           'chain': '폭우(자연) → 침수 이력이 있는 길(만든 조건) → 통제 → 돌아가는 길(구성원의 움직임) → 출동 지연 — ONTOLOGY.md §0 의 겹을 잇는 첫 화살표',
           'source': '서울시 침수흔적도(OA-15636 · 서울특별시 물순환안전국 치수안전과 · 2010~2025 · 2015·2021 자료 없음 · 공공누리 1유형 — data/season-seocho.json) × 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(data/nav-seocho.json)',
           'note': ['침수 흔적은 **잠긴 건물·필지 범위의 가운데 점**이다 — 「그 길이 잠겼다」는 기록이 아니라 「그 길 30m 안에서 잠긴 적이 있다」다. 길 자체의 통제 기록은 공개 자료가 없다',
                    '돌아가는 부담 = 그 길 조각 하나가 막혔을 때 양 끝을 잇는 가장 빠른 다른 길이 더 걸리는 초(제한속도 · 막힘 없음 · 회전 제한을 보지 않음 — 실제보다 작게 나온다) · -1 = 15분 안에 돌아갈 길이 없다',
                    '한 점수로 뭉치지 않았다 — 「잠긴 해 수」(일어날 법함) · 「돌아가는 부담」(끊겼을 때) · 「차로」(다니는 차의 어림)를 따로 보고 판단한다',
                    '2022·2011·2010 의 큰비 흔적이 대부분이다(해마다 고르게 찍힌 것이 아니다) · 그 뒤 배수 시설이 고쳐진 곳은 지금은 덜 잠길 수 있다(이 자료로 모른다)',
                    '도로 유형 002 = 지하차도 · 003 = 교량 · 004 = 터널(원자료 코드) — 지하차도는 얕은 침수에도 통제된다'],
           'fields': 'items[[ITS 링크 ID, 길 이름, 등급, 차로, 길이 m, 침수 흔적이 찍힌 해 수, 마지막 해, 가장 깊었던 침수심 m, 흔적 수, 돌아가는 부담 초(-1 = 돌아갈 길 없음), 도로 유형, 선 = 경도·위도×1e5 첫 점 + 차이]] — 잠긴 해 수가 많은 차례',
           'items': items}
    p = os.path.join(ROOT, 'data', 'flood-link-seocho.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('침수 흔적 30m 안 길 조각', len(rows), '· 실은 것', len(items), '· 바이트', os.path.getsize(p))
    by = collections.defaultdict(lambda: [0, 0, 0, 0.0, 0])
    for r in items:
        e = by[r[1] or '(이름 없음)']; e[0] = max(e[0], r[5]); e[1] = max(e[1], r[9]); e[2] += r[4]; e[3] = max(e[3], r[7]); e[4] = max(e[4], r[3])
    print('길 이름별(큰길 · 잠긴 해 수 차례):')
    for nm, e in sorted(by.items(), key=lambda kv: (-kv[1][0], -kv[1][2]))[:18]: print('  %-14s 잠긴 해 %d · 걸친 길이 %4dm · 가장 깊이 %.1fm · 돌아가는 부담 최대 %s초 · 차로 %d' % (nm, e[0], e[2], e[3], e[1], e[4]))
    print('지하차도·터널:', [(r[1], r[5], r[6], r[9]) for r in items if r[10] in ('002', '004')][:12])
if __name__ == '__main__': main()
