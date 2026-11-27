# -*- coding: utf-8 -*-
# 🚦 서울 전체 — 지도에 신호값이 없는 교차로를 골라 T-GIS 에서 받을 차례를 매긴다(소유자 2026-11-28 「빠진 곳 필요한 곳을 우선」)
#   값 있음 = T-Data 방향별(sigdir) · 경찰청 계획(signal-tod-seoul) · 교통과(sig-ksc) · T-GIS 계획(sig-tgis-plan) 중 하나가 같은 번호이거나 40m 안
#   딸린 신호(연동 부모 있음)·경보(점멸)는 현시도가 없어 뺀다
#   차례: ① 구 단계(서초 → 강남·동작·관악·용산·송파 → 한강 이남 → 그 밖) ② 둘레 60m 교통사고(taas10 · 있는 구만) 많은 곳
#   py -3.12 -X utf8 tools/signal/tgis-priority.py   → ../07_API키/신호앱/tgis_read/seoul_priority.tsv
import json, os, math, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱', 'tgis_read', 'seoul_priority.tsv')
J = lambda p: json.load(open(os.path.join(ROOT, 'data', p), encoding='utf-8'))
GU = {110: '종로', 140: '중', 170: '용산', 200: '성동', 215: '광진', 230: '동대문', 260: '중랑', 290: '성북', 305: '강북', 320: '도봉', 350: '노원', 380: '은평', 410: '서대문', 440: '마포', 470: '양천', 500: '강서', 530: '구로', 545: '금천', 560: '영등포', 590: '동작', 620: '관악', 650: '서초', 680: '강남', 710: '송파', 740: '강동'}
STAGE = {'서초': 1, '강남': 2, '동작': 2, '관악': 2, '용산': 2, '송파': 2, '영등포': 3, '구로': 3, '금천': 3, '양천': 3, '강서': 3, '강동': 3}


def dist(a, b, c, d): return math.hypot((b - d) * 88400.0, (a - c) * 111000.0)


def main():
    T = J('tgis-seoul.json')['items']
    D = J('sigdir-seoul.json'); P = J('signal-tod-seoul.json')['spots']
    K = J('sig-ksc-seocho.json')['items']; G = J('sig-tgis-plan.json')['items']
    nos = set(D['its']) | {str(x['no']) for x in P} | {str(x['no']) for x in K} | {str(x['no']) for x in G}
    pts = [(D['pts'][k][0], D['pts'][k][1]) for k in D['pts'] if D['its'].get(k)] + [(float(x['lat']), float(x['lon'])) for x in P] + [(float(x['lat']), float(x['lon'])) for x in K] + [(x['lat'], x['lon']) for x in G]
    grid = collections.defaultdict(list)
    for la, lo in pts: grid[(int(la * 1000), int(lo * 1000))].append((la, lo))

    def near(la, lo):
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for a, b in grid.get((int(la * 1000) + i, int(lo * 1000) + j), ()):
                    if dist(la, lo, a, b) <= 40: return True
        return False
    rows = []; st = collections.Counter(); have = collections.Counter()
    for c, n, la, lo, parent, pe, cits, gu in (r[:8] for r in T):
        g = GU.get(gu - 11000 if gu > 10000 else gu, str(gu))
        if parent or '연등' in n or '경보' in n: st['딸림·경보'] += 1; continue
        if (cits and str(cits) in nos) or near(la, lo): st['값 있음'] += 1; have[g] += 1; continue
        st['값 없음'] += 1; rows.append([STAGE.get(g, 4), g, c, cits, n, la, lo])
    rows.sort(key=lambda r: (r[0], r[1], r[4]))
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('단계\t구\tT-GIS코드\t교차로번호\t이름\t위도\t경도\n')
        for r in rows: f.write('\t'.join(str(v) for v in r) + '\n')
    miss = collections.Counter(r[1] for r in rows)
    print(dict(st))
    for s in (1, 2, 3, 4):
        gs = sorted({r[1] for r in rows if r[0] == s})
        print('단계 %d: %d곳 | %s' % (s, sum(miss[g] for g in gs), ' · '.join('%s %d(있음 %d)' % (g, miss[g], have[g]) for g in gs)))


if __name__ == '__main__':
    main()
