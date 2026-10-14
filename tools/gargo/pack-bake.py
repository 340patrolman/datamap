# -*- coding: utf-8 -*-
"""가르고(서초 출동 길 안내) — 폰이 읽는 길 계산 묶음을 굽는다.

  읽는 것: ../gargo/data/graph-seocho.json (비공개 저장소 gargo 의 tools/graph-bake.py 가 구운 것 · 9MB — OSM 길 + ITS 제한속도 + 신호 교차로 + 경사)
  쓰는 것: gargo/pack-seocho.json (gargo-pack/1 · 2MB 아래 — 지도 그리기와 길 계산을 한 파일로)
  돌리기: py -3.12 -X utf8 tools/gargo/pack-bake.py

  줄이는 법: 마디를 번호(0…)로 · 좌표는 기준점에서 ×1e6 정수 · 두 방향 길은 한 줄(dir 3)로 · 선(가운데 점)은 한 번만 · 이름·길 ID 는 목록 번호로.
  seg 한 줄 = [떠나는 마디, 닿는 마디, 길이 m, 제한속도, 등급, 이름 번호(-1 없음), 길 번호, 방향(1 정방향만 · 2 역방향만 · 3 둘 다), 선 번호(-1 = 곧은 한 줄), 속도 출처(0 기본값 · 1 ITS · 2 OSM), 차로, 오르막 dm(정방향), 내리막 dm(정방향)]
"""
import json, os, sys, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AREA = sys.argv[sys.argv.index('--area') + 1] if '--area' in sys.argv else 'seocho'   # --area six = 서초·강남·송파·동작·관악·용산(2026-10-14)
SRC = os.path.join(os.path.dirname(ROOT), 'gargo', 'data', 'graph-%s.json' % AREA)
OUT = os.path.join(ROOT, 'gargo', 'pack-%s.json' % AREA)


def main():
    G = json.load(open(SRC, encoding='utf-8'))
    N = G['nodes']; E = G['edges']
    used = collections.OrderedDict()
    for e in E:
        used.setdefault(e[0], None); used.setdefault(e[1], None)
    ids = list(used.keys()); idx = {n: i for i, n in enumerate(ids)}
    def ll(n):
        v = N.get(str(n)) or N.get(n)
        return v
    lon0 = min(ll(n)[0] for n in ids); lat0 = min(ll(n)[1] for n in ids)
    bx = int(round(lon0 * 1e6)); by = int(round(lat0 * 1e6))
    nx = [int(round(ll(n)[0] * 1e6)) - bx for n in ids]; ny = [int(round(ll(n)[1] * 1e6)) - by for n in ids]
    names = []; nidx = {}
    ways = []; widx = {}
    geos = []; gidx = {}
    links = []; lidx = {}; tls = []; tidx = {}
    def li(v):
        v = str(v or '')
        if not v: return -1
        if v not in lidx: lidx[v] = len(links); links.append(v)
        return lidx[v]
    def ti(v):
        v = str(v or '')
        if not v: return -1
        if v not in tidx: tidx[v] = len(tls); tls.append(v)
        return tidx[v]
    segs = []; pair = {}
    for e in E:
        a, b, ln, spd, src, cls, lanes, nm, up, dn, flat, way, rev = e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8], e[9], e[10], e[11], e[12]
        line = e[15] if len(e) > 15 else None
        its = e[13] if len(e) > 13 else ''; tl = e[14] if len(e) > 14 else ''
        fa, fb = (b, a) if rev else (a, b)                       # 정방향(선이 적힌 차례)의 떠나는·닿는 마디
        key = (way, fa, fb, round(ln, 1))
        if key in pair:
            q = segs[pair[key]]; q[7] |= (2 if rev else 1); q[14 if rev else 13] = li(its); q[16 if rev else 15] = ti(tl); continue
        ni = -1
        if nm:
            if nm not in nidx: nidx[nm] = len(names); names.append(nm)
            ni = nidx[nm]
        if way not in widx: widx[way] = len(ways); ways.append(way)
        gi = -1
        if line and len(line) > 4:                               # 가운데 점이 있다 — 첫 점(마디)과 끝 점(마디)은 뺀다
            pts = []; x = line[0]; y = line[1]; P = [(x, y)]
            for k in range(2, len(line), 2):
                x += line[k]; y += line[k + 1]; P.append((x, y))
            mid = P[1:-1]
            if mid:
                ax = int(round(ll(fa)[0] * 1e6)); ay = int(round(ll(fa)[1] * 1e6)); d = []; px, py = ax, ay
                for (x, y) in mid:
                    d.append(x - px); d.append(y - py); px, py = x, y
                t = tuple(d)
                if t not in gidx: gidx[t] = len(geos); geos.append(d)
                gi = gidx[t]
        pair[key] = len(segs)
        segs.append([idx[fa], idx[fb], int(round(ln)), int(spd), int(cls), ni, widx[way], (2 if rev else 1), gi, int(src), int(lanes or 0), int(round((dn if rev else up) * 10)), int(round((up if rev else dn) * 10)), (-1 if rev else li(its)), (li(its) if rev else -1), (-1 if rev else ti(tl)), (ti(tl) if rev else -1)])
    turns = []
    for via, fw, tw, kind in G['turns']:
        if via in idx and fw in widx and tw in widx:
            turns.append([idx[via], widx[fw], widx[tw], 1 if str(kind).startswith('only_') else 0])
    sig = []
    for no, s in sorted(G['sig'].items(), key=lambda q: q[0]):
        nn = [idx[n] for n in s.get('n', []) if n in idx]
        if nn:
            sig.append([no, s.get('nm', ''), round(s['ll'][0], 6), round(s['ll'][1], 6), int(s.get('r', 45)), 1 if s.get('anchor') else 0, nn])
    doc = {'schema': 'gargo-pack/1', 'made': datetime.date.today().isoformat(), 'graph_made': G.get('made'), 'area': G.get('area'),
           'source': G.get('source'), 'dem': G.get('dem'), 'note': G.get('note'),
           'fields': 'base[경도, 위도 ×1e6] · nx·ny[마디마다 base 로부터 ×1e6] · names[길 이름] · seg[[떠나는 마디, 닿는 마디, 길이 m, 제한속도, 등급(1 고속 … 6 골목 · 7 생활도로 · 8 진입로), 이름 번호, 길 번호, 방향(1 정방향만 · 2 역방향만 · 3 둘 다), 선 번호(-1 곧은 줄), 속도 출처(0 기본값 · 1 ITS · 2 OSM), 차로(0 모름), 오르막 dm, 내리막 dm(정방향 기준), ITS 링크 번호(정방향 · links 목록 번호 · -1 없음), ITS 링크 번호(역방향), 차로별 진행 방향 번호(정방향 · tl 목록 번호 · OSM 에 적힌 곳만), 같은 것(역방향)]] · links[ITS 링크 ID — data/live-spd-seocho.json 의 m 열쇠] · tl[차로별 진행 방향 글 — 왼쪽 차로부터 | 로 가르고 한 차로의 여러 방향은 ; · left·through·right·reverse·slight_left …] · geo[가운데 점들 — 떠나는 마디에서의 차이 ×1e6 이어 적기] · turns[[거치는 마디, 들어오는 길 번호, 나가는 길 번호, 0 금지 · 1 이 길로만]] · sig[[신호 교차로 번호, 이름, 경도, 위도, 넓이 반지름 m, 닻 있음 1, [넓이 안의 마디]]]',
           'base': [bx, by], 'nx': nx, 'ny': ny, 'names': names, 'ways': len(ways), 'seg': segs, 'links': links, 'tl': tls, 'geo': geos, 'turns': turns, 'sig': sig}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    both = sum(1 for s in segs if s[7] == 3)
    print('마디', len(ids), '· 길 줄', len(segs), '(두 방향', both, '· 한 방향', len(segs) - both, ') ← 방향 있는 줄', len(E), '· 선', len(geos), '· 이름', len(names), '· 회전 제한', len(turns), '· 신호', len(sig), '->', OUT, os.path.getsize(OUT), 'B')
    # 맞대기: 방향 있는 줄 수가 되살아나는가
    back = sum((1 if s[7] & 1 else 0) + (1 if s[7] & 2 else 0) for s in segs)
    print('되살린 방향 줄', back, '(원본', len(E), ')')


if __name__ == '__main__':
    main()
