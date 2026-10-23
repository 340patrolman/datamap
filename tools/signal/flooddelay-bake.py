# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌧 폭우 연쇄의 마지막 고리: 침수 이력 길이 통제되면 **출동이 어디서 얼마나 늦어지나**(소유자 2026-10-11 「폭우 → 침수이력 도로 침수 → 교통통제 → 우회로 혼잡 → 출동 지연」 · ONTOLOGY.md §0) → data/flood-delay-seocho.json
#   재료(이미 구운 것): 길 = data/nav-seocho.json(ITS 표준노드링크 · 서초구 + 2km) · 통제되는 길 = data/flood-link-seocho.json(침수 흔적 30m 안의 길 구간)
#                     · 출동하는 곳 = 지구대·파출소(data/police-seocho.json boxes) · 119안전센터·소방서(data/agency-pts.json fire — 좌표 있는 곳)
#   시나리오 둘: A = 침수 흔적이 두 해 이상 찍힌 구간이 모두 막힘(되풀이 잠기는 곳) · B = 2022년 흔적이 찍힌 구간이 모두 막힘(2022-08 큰비의 재현 — 흔적이 찍힌 해가 2022 인 조각의 구간)
#   마디(교차로)마다 「가장 가까운 관서에서 오는 시간」을 평소 / 통제 때로 구해 늘어난 초를 싣는다(제한속도 · 막힘 없음 · 신호 없음 · 회전 제한 무시 — **견주는 값이지 실제 출동 시간이 아니다**)
#   통제된 길 위의 마디는 「닿지 못함」으로 따로 센다(물에 잠긴 자리 자체)
#   py -3.12 -X utf8 tools/signal/flooddelay-bake.py
import json, os, sys, math, heapq, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AREA = sys.argv[1] if len(sys.argv) > 1 else 'seocho'   # seocho(종전) · six(여섯 구 · nav-six · flood-link-six · 지구대·파출소 = police.json pbox · 2026-10-23)
def dist(a, b): return math.hypot((a[0] - b[0]) * 88800.0, (a[1] - b[1]) * 111000.0)
def main():
    nav = json.load(open(os.path.join(ROOT, 'data', 'nav-%s.json' % AREA), encoding='utf-8')); N = nav['nodes']; L = nav['links']
    FL = json.load(open(os.path.join(ROOT, 'data', 'flood-link-%s.json' % AREA), encoding='utf-8'))['items']
    out = collections.defaultdict(list); lid = {}
    for i, x in enumerate(L):
        if x[5] <= 6: out[x[1]].append(i)
        lid[str(x[0])] = i
    secA = set(r[12] for r in FL if r[14] >= 2); secB = set(r[12] for r in FL if r[6] == 2022)
    # flood-link 에는 구간 번호만 있다 — 같은 구간의 조각을 모두 막으려면 구간 → 조각 표가 필요하다. 실린 조각(큰길은 한 해 · 그 밖은 두 해 이상)만 막는다
    banA = set(lid[str(r[0])] for r in FL if r[12] in secA and str(r[0]) in lid); banB = set(lid[str(r[0])] for r in FL if r[12] in secB and str(r[0]) in lid)
    def near(ll):
        best = None
        for k, v in N.items():
            if not out.get(k): continue
            d = dist(ll, (v[0], v[1]))
            if best is None or d < best[0]: best = (d, k)
        return best
    P = json.load(open(os.path.join(ROOT, 'data', 'police-seocho.json'), encoding='utf-8')); A = json.load(open(os.path.join(ROOT, 'data', 'agency-pts.json'), encoding='utf-8'))['fire']
    box = (min(v[0] for v in N.values()), min(v[1] for v in N.values()), max(v[0] for v in N.values()), max(v[1] for v in N.values()))
    def inb(lon, lat): return lon and lat and box[0] <= lon <= box[2] and box[1] <= lat <= box[3]
    pol = [(b['name'], (b['lon'], b['lat'])) for b in P['boxes'] if inb(b.get('lon'), b.get('lat'))]
    if AREA != 'seocho':
        PJ = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8'))
        pol = [(b[0] + ('파출소' if b[1] else '지구대'), (b[4], b[3])) for b in PJ['pbox'] if inb(b[4], b[3])]
    fire = []
    for f in A:
        if inb(f.get('lon'), f.get('lat')): fire.append((f['n'], (f['lon'], f['lat'])))
        for c in f.get('c', []):
            if inb(c[4], c[3]): fire.append((c[0], (c[4], c[3])))
    def spread(srcs, ban):
        D = {}; W = {}; h = []
        for nm, ll in srcs:
            d, k = near(ll)
            if d > 400: continue
            t0 = d / (20 / 3.6)
            if t0 < D.get(k, 1e18): D[k] = t0; W[k] = nm; heapq.heappush(h, (t0, k))
        while h:
            d, u = heapq.heappop(h)
            if d > D.get(u, 1e18): continue
            for q in out.get(u, ()):
                if q in ban: continue
                x = L[q]; nd = d + x[3] / (max(x[4], 20) / 3.6)
                if nd < D.get(x[2], 1e18): D[x[2]] = nd; W[x[2]] = W[u]; heapq.heappush(h, (nd, x[2]))
        return D, W
    res = {}; stat = {}
    for who, srcs in (('pol', pol), ('fire', fire)):
        D0, W0 = spread(srcs, set())
        for sc, ban in (('A', banA), ('B', banB)):
            D1, W1 = spread(srcs, ban); onban = set(L[q][1] for q in ban) | set(L[q][2] for q in ban); rows = []; cut = 0; late = [0, 0, 0]
            for k, v in N.items():
                if v[4] != 1 or k not in D0 or str(v[2]) != '101': continue
                if k not in D1: cut += 1; rows.append([round(v[0], 5), round(v[1], 5), round(D0[k]), -1, W0[k], '', v[3] or '', 1 if k in onban else 0]); continue
                dl = D1[k] - D0[k]
                if dl >= 30:
                    rows.append([round(v[0], 5), round(v[1], 5), round(D0[k]), round(D1[k]), W0[k], W1[k] if W1[k] != W0[k] else '', v[3] or '', 1 if k in onban else 0])
                    late[0 if dl < 60 else 1 if dl < 180 else 2] += 1
            rows.sort(key=lambda r: -((r[3] - r[2]) if r[3] >= 0 else 99999)); res[who + sc] = rows
            tot = sum(1 for k, v in N.items() if v[4] == 1 and k in D0 and str(v[2]) == '101')
            stat[who + sc] = {'교차로': tot, '닿지 못함': cut, '30~60초 늦음': late[0], '1~3분 늦음': late[1], '3분 넘게 늦음': late[2]}
    doc = {'schema': 'tg-flood-delay/1', 'made': datetime.date.today().isoformat(), 'area': '서초구(길은 경계 밖 2km 까지)' if AREA == 'seocho' else (nav.get('area') or AREA),
           'chain': '폭우(자연) → 침수 이력 길(만든 조건) → 통제 → 돌아가는 길 → **출동 지연** — ONTOLOGY.md §0 겹을 잇는 화살표의 끝 고리 · 앞 고리는 data/flood-link-' + AREA + '.json',
           'source': 'data/nav-seocho.json(국가교통정보센터 표준노드링크 2026-09-14판) × data/flood-link-seocho.json(서울시 침수흔적도 2010~2025) × data/police-seocho.json(지구대·파출소 %d곳) × data/agency-pts.json(소방서·119안전센터 %d곳 — 좌표가 있는 곳만)' % (len(pol), len(fire)),
           'scenarios': {'A': '침수 흔적이 두 해 이상 찍힌 구간이 모두 막힌다(되풀이 잠기는 곳) — 길 조각 %d' % len(banA), 'B': '2022년 흔적이 마지막인 구간이 모두 막힌다(2022년 8월 큰비 모양) — 길 조각 %d' % len(banB)},
           'note': ['**견주는 값이다 — 실제 출동 시간이 아니다.** 제한속도로 달리고 · 막히지 않고 · 신호가 없고 · 회전 제한을 보지 않는다고 셌다. 통제 때는 돌아가는 길도 막혀 실제로는 더 늦다',
                    '침수 흔적은 잠긴 건물·필지의 가운데 점이다 — 「그 길이 잠겼다」가 아니라 「30m 안에서 잠긴 적이 있다」 · 그런 길이 **한꺼번에 다** 막힌다고 본 가장 나쁜 쪽의 그림이다(실제 통제는 그 일부)',
                    '출동하는 곳 = 그 교차로에 평소 가장 빨리 닿는 관서(관할이 아니다 — 법정 관할·출동 배정과 다를 수 있다) · 순찰 중인 차는 세지 않았다(관서에서 떠난다고 봄)',
                    '닿지 못함(-1) = 통제된 길을 지나지 않고는 갈 수 없는 교차로 · 끝 칸 1 = 그 교차로가 통제된 길에 붙어 있다(잠긴 자리 자체일 수 있다)',
                    '119안전센터 가운데 좌표가 없는 곳은 빠졌다(소방청 좌표 자료에 이름이 맞는 것만) — 소방 쪽 지연은 실제보다 크게 나올 수 있다'],
           'fields': '{polA·polB·fireA·fireB: [[경도, 위도, 평소 초, 통제 때 초(-1 = 닿지 못함), 평소 가장 빨리 오는 관서, 통제 때 바뀐 관서(같으면 빈 글), 교차로 이름, 통제된 길에 붙어 있음 1]…]} — 30초 이상 늦어지는 교차로만 · 많이 늦는 차례',
           'stat': stat}
    doc.update(res)
    od = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto'); os.makedirs(od, exist_ok=True)   # 비공개 — 소유자 2026-10-23 「flood-delay 도 비공개로」(관할 도달 공백이 드러나는 자료 · 공개 저장소에 두지 않는다)
    p = os.path.join(od, 'flood-delay-%s.json' % AREA); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '· 지구대·파출소', len(pol), '· 소방', len(fire), '· 막는 조각 A', len(banA), 'B', len(banB)); print(json.dumps(stat, ensure_ascii=False))
    for key in ('polA', 'fireA'):
        print(key, [(r[6] or '(이름 없음)', r[2], r[3], r[4], r[5]) for r in res[key] if r[6]][:10])
if __name__ == '__main__': main()
