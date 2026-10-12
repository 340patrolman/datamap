# -*- coding: utf-8 -*-
"""도로 구간 → 지나는 250m 칸 (온톨로지 결정 D1 의 다리 · ONTOLOGY-2-조합.md 링크 「도로 구간 → 자리(칸)」).

data/nav-seocho.json 의 링크 선을 25m 마다 읽어 국가지점번호식 250m 칸 번호로 바꾸고, 지나는 차례대로 적는다.
통신 없음 · pyproj 필요(grid250.py 와 같은 변환):
    py -3.12 -X utf8 tools/onto/rdcell-bake.py
nav-seocho.json 을 다시 구우면 이것도 다시.
"""
import json, os, math, datetime, importlib.util

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'data', 'nav-seocho.json')
OUT = os.path.join(ROOT, 'data', 'rd-cell-seocho.json')
STEP = 25.0

_s = importlib.util.spec_from_file_location('grid250', os.path.join(ROOT, 'tools', 'region', 'grid250.py'))
G = importlib.util.module_from_spec(_s); _s.loader.exec_module(G)


def pts(line):
    x, y = line[0], line[1]; o = [(x / 1e5, y / 1e5)]
    for i in range(2, len(line) - 1, 2):
        x += line[i]; y += line[i + 1]; o.append((x / 1e5, y / 1e5))
    return o


def dist(a, b):
    k = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((b[0] - a[0]) * 111320 * k, (b[1] - a[1]) * 110540)


def main():
    nav = json.load(open(SRC, encoding='utf-8'))
    idx, cells, links = {}, [], {}
    for L in nav['links']:
        P = pts(L[9]); seq = []
        for a, b in zip(P, P[1:]):
            n = max(1, int(math.ceil(dist(a, b) / STEP)))
            for i in range(n + 1):
                t = i / n; lon = a[0] + (b[0] - a[0]) * t; lat = a[1] + (b[1] - a[1]) * t
                c = G.code_ll(lat, lon)
                if not seq or seq[-1] != c:
                    seq.append(c)
        if len(P) == 1:
            seq = [G.code_ll(P[0][1], P[0][0])]
        o = []
        for c in seq:
            if c not in idx:
                idx[c] = len(cells); cells.append(c)
            if not o or o[-1] != idx[c]:
                o.append(idx[c])
        links[L[0]] = o
    multi = sum(1 for v in links.values() if len(v) > 1)
    doc = {'schema': 'tg-rd-cell/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': 'data/nav-seocho.json(국가교통정보센터 ITS 전국 표준노드링크 2026-09-14판 · 서초구 + 경계 밖 2km) 의 링크 선 × 국가지점번호식 250m 격자(EPSG:5179 · tools/region/grid250.py 와 같은 변환)',
           'fields': 'cells[250m 칸 번호] · links{ITS 링크 ID: [cells 의 차례 번호 — 링크 방향(F → T)으로 지나는 차례]}',
           'note': ['링크 선을 %dm 마다 읽어 칸을 셌다 — 칸 모서리를 %dm 보다 짧게 스치는 곳은 빠질 수 있다' % (STEP, STEP),
                    '온톨로지 결정 D1(ONTOLOGY-2-조합.md): 길은 링크 ID 가 열쇠이고, 이 표는 격자에서 길로 닿는 다리다 — 길을 칸으로 쪼개 쓰라는 뜻이 아니다',
                    '칸에서 지나는 길을 찾을 때는 links 를 거꾸로 훑는다(한 칸에 여러 링크)'],
           'area': nav.get('area', ''), 'count': {'links': len(links), 'cells': len(cells), 'links_multi_cell': multi},
           'cells': cells, 'links': links}
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
    print('rd-cell-seocho.json', os.path.getsize(OUT), 'B · 링크', len(links), '· 칸', len(cells), '· 여러 칸을 지나는 링크', multi)


if __name__ == '__main__':
    main()
