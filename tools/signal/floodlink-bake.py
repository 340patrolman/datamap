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
    # 돌아가는 부담 — **길 한 구간(갈림길에서 갈림길까지)** 이 막힐 때로 센다(게임 세션 2026-10-11 지적: 조각 하나만 빼면 큰길은 방향마다 마디가 따로라 「돌아갈 길 없음」이 77% 나왔다 — 조각 하나는 옆 조각으로 못 돌아간다)
    def t(x): return x[3] / (max(x[4], 20) / 3.6)
    indeg = collections.Counter(); outdeg = collections.Counter(); inl = collections.defaultdict(list)
    for k, x in enumerate(L): outdeg[x[1]] += 1; indeg[x[2]] += 1; inl[x[2]].append(k)
    def thru(n): return indeg[n] == 1 and outdeg[n] == 1   # 지나가기만 하는 마디(갈림이 없다)
    sec_of = {}; SEC = []
    for k, x in enumerate(L):
        if k in sec_of or x[5] > 6: continue
        chain = [k]; a = x[1]
        while thru(a) and len(chain) < 80:   # 거슬러 올라가 구간의 처음을 찾는다
            pk = inl[a][0]
            if pk in sec_of or pk in chain: break
            chain.insert(0, pk); a = L[pk][1]
        b = x[2]
        while thru(b) and len(chain) < 80:
            nk = out[b][0]
            if nk in sec_of or nk in chain: break
            chain.append(nk); b = L[nk][2]
        sid = len(SEC); SEC.append(chain)
        for q in chain: sec_of[q] = sid
    def detour(sid):
        ch = SEC[sid]; ban = set(ch); src, dst = L[ch[0]][1], L[ch[-1]][2]; base = sum(t(L[q]) for q in ch); D = {src: 0.0}; h = [(0.0, src)]; lim = base + 900
        if src == dst or sum(L[q][3] for q in ch) < 40: return None   # 40m 안 되는 구간은 교차로 안의 짧은 이음이다 — 「그 구간이 막힐 때」가 뜻이 없어 세지 않는다(남현1길 12m 구간이 +432초로 나오던 것 · 게임 세션 2026-10-11)
        while h:
            d, u = heapq.heappop(h)
            if d > D.get(u, 1e18) or d > lim: continue
            if u == dst: return d - base
            for q in out.get(u, ()):
                if q in ban: continue
                nd = d + t(L[q])
                if nd < D.get(L[q][2], 1e18): D[L[q][2]] = nd; heapq.heappush(h, (nd, L[q][2]))
        return None
    agg = {}   # 구간마다 — 잠긴 해(조각들의 합집합을 못 가지므로 가장 큰 값) · 가장 깊이 · 흔적 수 합
    for i2, ny, last, dmax, cnt in rows:
        sid = sec_of.get(i2)
        if sid is None: continue
        e = agg.setdefault(sid, [0, 0, 0.0, 0]); e[0] = max(e[0], ny); e[1] = max(e[1], last); e[2] = max(e[2], dmax); e[3] += cnt
    DT = {}
    items = []
    for i2, ny, last, dmax, cnt in rows:
        x = L[i2]; sid = sec_of.get(i2); e = agg.get(sid, [ny, last, dmax, cnt])
        if e[0] < 2 and x[5] > 4: continue   # 큰길(등급 1~4)은 한 해라도, 그 밖은 두 해 이상 찍힌 구간만
        if sid not in DT: DT[sid] = detour(sid) if sid is not None else None
        dt = DT[sid]; slen = round(sum(L[q][3] for q in SEC[sid])) if sid is not None else x[3]
        items.append([x[0], x[7], x[5], x[6], x[3], ny, last, dmax, cnt, -1 if dt is None else round(dt), x[12] if len(x) > 12 else '000', x[9], sid, slen, e[0]])
    items.sort(key=lambda r: (-r[5], -(r[9] if r[9] >= 0 else 9999), -r[3]))
    doc = {'schema': 'tg-flood-link/1', 'made': datetime.date.today().isoformat(), 'area': '서초구 + 경계 밖 2km',
           'chain': '폭우(자연) → 침수 이력이 있는 길(만든 조건) → 통제 → 돌아가는 길(구성원의 움직임) → 출동 지연 — ONTOLOGY.md §0 의 겹을 잇는 첫 화살표',
           'source': '서울시 침수흔적도(OA-15636 · 서울특별시 물순환안전국 치수안전과 · 2010~2025 · 2015·2021 자료 없음 · 공공누리 1유형 — data/season-seocho.json) × 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판(data/nav-seocho.json)',
           'note': ['침수 흔적은 **잠긴 건물·필지 범위의 가운데 점**이다 — 「그 길이 잠겼다」는 기록이 아니라 「그 길 30m 안에서 잠긴 적이 있다」다. 길 자체의 통제 기록은 공개 자료가 없다',
                    '돌아가는 부담 = 그 조각이 든 **길 한 구간(갈림길에서 갈림길까지 · 한 방향)** 이 통째로 막혔을 때 구간의 처음과 끝을 잇는 가장 빠른 다른 길이 더 걸리는 초(제한속도 · 막힘 없음 · 회전 제한을 보지 않음 — 실제보다 작게 나온다) · -1 = 15분 안에 돌아갈 길을 못 찾았거나(외길·자료의 가장자리) 구간이 40m 안 되는 교차로 안 이음이라 세지 않았다',
                    '같은 구간의 조각들은 돌아가는 부담이 같다(끝의 세 칸 — 구간 번호 · 구간 길이 · 구간의 잠긴 해 수)',
                    '한 점수로 뭉치지 않았다 — 「잠긴 해 수」(일어날 법함) · 「돌아가는 부담」(끊겼을 때) · 「차로」(다니는 차의 어림)를 따로 보고 판단한다',
                    '2022·2011·2010 의 큰비 흔적이 대부분이다(해마다 고르게 찍힌 것이 아니다) · 그 뒤 배수 시설이 고쳐진 곳은 지금은 덜 잠길 수 있다(이 자료로 모른다)',
                    '도로 유형 002 = 지하차도 · 003 = 교량 · 004 = 터널(원자료 코드) — 지하차도는 얕은 침수에도 통제된다'],
           'fields': 'items[[ITS 링크 ID, 길 이름, 등급, 차로, 길이 m, 침수 흔적이 찍힌 해 수, 마지막 해, 가장 깊었던 침수심 m, 흔적 수, 돌아가는 부담 초(-1 = 돌아갈 길 없음), 도로 유형, 선 = 경도·위도×1e5 첫 점 + 차이, 구간 번호, 구간 길이 m, 구간의 잠긴 해 수(조각들 가운데 가장 큰 값)]] — 잠긴 해 수가 많은 차례',
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
