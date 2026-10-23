# -*- coding: utf-8 -*-
# 데이터 압축지도 — 온톨로지 「지구대·파출소 → 교차로 도착 시간」 한 장 → 07_API키/out/onto/onto-reach-<area>.json (tg-onto-reach/1 · **비공개** — 소유자 2026-10-23 「공개 저장소에서 빼고 비공개 쪽에만」 · 관할 도달 공백이 드러나는 자료)
#   소유자 2026-10-23 「권고대로 지구대에서 교차로까지 도착 가능 시간을 잇는 것 진행」(엮임 지도 일곱째)
#   길 = data/nav-<area>.json(ITS 표준노드링크 · 방향 지킴) · 출발 = data/police.json pbox(경찰청 지구대·파출소 주소 현황) · 도착 = data/onto-int.json 교차로(그 자리에서 가장 가까운 들어오는 링크가 있는 노드)
#   시간 셋(링크마다 따로 셈 · 길도 따로 찾음):
#     s0  = 제한속도로 막힘 없이(20 km/h 아래·빈 값은 20) — 가장 짧은 값
#     s8  = 평일 8시: 그 링크에 쌓인 평소 속도(spd-normal 월~목 8시 가운데값)가 있으면 그 속도 · 없으면 제한속도 주행 × eta-cal 「평일|출근」 배율(신호 기다림 뺀 배율이라 실측 없는 길은 짧게 나옴)
#     s18 = 평일 18시: 같은 셈(18시 · 「평일|퇴근」)
#     c8·c18 = 그 길 길이 가운데 실측 평소 속도로 센 몫(%)
#   교차로마다 s0 가 짧은 지구대·파출소 다섯 곳을 싣는다. 출발 자리는 관서에서 가장 가까운 나가는 링크 노드(400m 안 · 그 거리는 20 km/h 로 걸음).
#   **견주는 값이다 — 실제 출동 시간이 아니다.** 신호(실측 없는 길)·회전 제한·순찰 중인 차·긴급 주행을 보지 않는다.
#   py -3.12 -X utf8 tools/onto/reach-bake.py [seocho|six]
import json, os, sys, math, heapq, datetime, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D = os.path.join(ROOT, 'data')
AREA = sys.argv[1] if len(sys.argv) > 1 else 'seocho'
GUS = {'seocho': ['11650'], 'six': ['11650', '11680', '11710', '11590', '11620', '11170']}[AREA]
def J(f): return json.load(open(os.path.join(D, f), encoding='utf-8'))
def dist(lo1, la1, lo2, la2): return math.hypot((lo1 - lo2) * 88400.0, (la1 - la2) * 111000.0)


def main():
    nav = J('nav-%s.json' % AREA); N = nav['nodes']; L = nav['links']
    if AREA == 'seocho': SP = J('spd-normal-seocho.json')['links']
    else:
        SP = {}
        for f in sorted(glob.glob(os.path.join(D, 'spd-normal-six', '1*.json'))): SP.update(json.load(open(f, encoding='utf-8'))['links'])
    EC = J('eta-cal.json')['f']; F = {8: EC['평일|출근'], 18: EC['평일|퇴근']}
    out = {}; inn = set()
    for i, x in enumerate(L):
        out.setdefault(x[1], []).append(i); inn.add(x[2])
    def cost(i, h):
        x = L[i]; lim = max(x[4] or 0, 20); t0 = x[3] / (lim / 3.6)
        if h is None: return t0, 0
        v = (SP.get(x[0]) or {}).get('0-%d' % h)
        if v and v[0] > 0: return x[3] / (v[0] / 3.6), x[3]
        return t0 * F[h], 0
    lo0 = min(v[0] for v in N.values()); lo1 = max(v[0] for v in N.values()); la0 = min(v[1] for v in N.values()); la1 = max(v[1] for v in N.values())
    G = {}
    for k, v in N.items(): G.setdefault((int(v[1] * 500), int(v[0] * 500)), []).append(k)
    def snap(lo, la, ok, r):
        best = None
        for i in (-2, -1, 0, 1, 2):
            for j in (-2, -1, 0, 1, 2):
                for k in G.get((int(la * 500) + i, int(lo * 500) + j), ()):
                    if k not in ok: continue
                    d = dist(lo, la, N[k][0], N[k][1])
                    if d <= r and (best is None or (d, k) < best): best = (d, k)
        return best
    P = J('police.json'); boxes = []
    for k, b in enumerate(P['pbox']):
        if not (lo0 <= b[4] <= lo1 and la0 <= b[3] <= la1): continue
        s = snap(b[4], b[3], out, 400)
        if s: boxes.append((k, s[1], s[0] / (20 / 3.6)))
    ints = []
    for r in J('onto-int.json')['items']:
        if r[6] not in GUS: continue
        s = snap(r[3], r[2], inn, 80)
        if s: ints.append((r[0], s[1], round(s[0])))
    tgt = {}
    for t in ints: tgt.setdefault(t[1], []).append(t[0])
    res = {t[0]: [] for t in ints}
    for k, n0, w in boxes:
        row = {}
        for h in (None, 8, 18):
            Dd = {n0: w}; Ln = {n0: 0}; Cm = {n0: 0}; q = [(w, n0)]
            while q:
                d, u = heapq.heappop(q)
                if d > Dd.get(u, 1e18): continue
                for i in out.get(u, ()):
                    c, m = cost(i, h); nd = d + c; v = L[i][2]
                    if nd < Dd.get(v, 1e18): Dd[v] = nd; Ln[v] = Ln[u] + L[i][3]; Cm[v] = Cm[u] + m; heapq.heappush(q, (nd, v))
            row[h] = (Dd, Ln, Cm)
        for node, ids in tgt.items():
            if node not in row[None][0]: continue
            def cv(h): Dd, Ln, Cm = row[h]; return (round(Cm[node] / Ln[node] * 100) if Ln[node] else 0) if node in Dd else None
            def tm(h): Dd = row[h][0]; return round(Dd[node]) if node in Dd else -1
            for iid in ids: res[iid].append([k, tm(None), tm(8), tm(18), cv(8), cv(18)])
    items = {}
    for iid, rows in res.items():
        rows.sort(key=lambda x: (x[1], x[0]))
        items[str(iid)] = rows[:5]
    snapd = {str(t[0]): t[2] for t in ints}
    doc = {'schema': 'tg-onto-reach/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'area': nav.get('area') or AREA,
           'source': '길 = data/nav-%s.json(국가교통정보센터 ITS 표준노드링크 2026-09-14판) · 평소 속도 = data/spd-normal-%s(ITS 실시간 소통 2026-10-11~ 쌓은 월~목 가운데값) · 실측 없는 길 배율 = data/eta-cal.json(서초 간선 28구간 · 평일|출근 %.2f · 평일|퇴근 %.2f) · 관서 = data/police.json pbox(경찰청 전국 지구대·파출소 주소 현황 2025-12-31)' % (AREA, 'seocho.json' if AREA == 'seocho' else 'six/', F[8], F[18]),
           'fields': 'items{T-GIS 교차로코드: [[police.json pbox 차례, s0 초(제한속도·막힘 없음), s8 초(평일 8시), s18 초(평일 18시 · -1 = 닿지 않음), c8 %, c18 % (길 길이 가운데 실측 평소 속도로 센 몫)] … s0 짧은 차례 다섯}} · snap{교차로코드: 도착 노드까지 m}',
           'note': ['**견주는 값이다 — 실제 출동 시간이 아니다.** 실측 평소 속도가 없는 길은 제한속도 × eta-cal 배율(신호 기다림을 뺀 배율)이라 짧게 나오고, 회전 제한·순찰 중인 차·긴급 주행은 보지 않는다',
                    '출발 = 관서 청사 자리(순찰 중인 차는 세지 않음) · 평소 속도는 2026-10-11 부터 쌓은 것이라 요일 갈래마다 날 수가 적으면 잠정(spd-normal provisional)',
                    '관할이 아니라 「가장 빨리 닿는 곳」 차례다 — 법정 관할·출동 배정과 다를 수 있다'],
           'count': {'관서': len(boxes), '교차로': len(ints)}, 'snap': snapd, 'items': items}
    od = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto'); os.makedirs(od, exist_ok=True)   # 비공개 — 공개 저장소에 두지 않는다(소유자 2026-10-23)
    p = os.path.join(od, 'onto-reach-%s.json' % AREA); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('onto-reach-%s.json' % AREA, doc['count'], os.path.getsize(p) // 1024, 'KB')



if __name__ == '__main__':
    main()
