# -*- coding: utf-8 -*-
"""네비 가르고 — 길 묶음(pack-<area>.json)을 「큰길 한 장(core) + 골목 칸(t/<ix_iz>.json)」으로 나눈다.
  2026-10-14 소유자 「한강 이남이 완성되면 서울 전체로」 — 서울 전체 한 장은 폰에 너무 크다(여섯 구 9.5MB → 서울 약 40MB).
  나누는 법(번호는 그대로 — 폰이 받은 것끼리 다시 번호를 매겨 종전 묶음 꼴로 합친다 · gargo.js pkMerge):
    core.json = 등급 1~5(고속·도시고속·간선·보조간선·집산) 길 줄과 그 마디 · 이름·길·ITS 링크·차로 방향 목록 · 신호 전부 · 큰길끼리의 회전 제한 · 칸 목록
    t/<ix_iz>.json = 등급 6~8(골목·생활도로·진입로) 길 줄(가운데 점이 그 칸) + 그 줄의 마디 가운데 core 에 없는 것 + 거치는 마디가 그 칸인 나머지 회전 제한
    칸 = 2km(가르고 화면 좌표 x = (경도 − 127.01)×88800 · y = (37.49 − 위도)×111000 — 건물 칸과 같은 셈법이 아니다(건물은 게임 좌표))
  줄 한 줄 = [길 줄 번호(전체), …pack 의 seg 한 줄 그대로(마디는 전체 번호 · 선 번호는 그 파일의 geo 번호)]
  쓰기: py -3.12 -X utf8 tools/gargo/pack-tile.py seoul
"""
import json, os, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AREA = sys.argv[1] if len(sys.argv) > 1 else 'seoul'
CELL = 2000; CORE = 5
LON0, LAT0, KX, KY = 127.01, 37.49, 88800, 111000   # gargo.js PX·PY 와 같은 값이어야 한다(아래에서 gargo.js 를 읽어 대조)
def main():
    js = open(os.path.join(ROOT, 'gargo', 'gargo.js'), encoding='utf-8').read()
    for k, v in (('LON0', LON0), ('LAT0', LAT0), ('KX', KX), ('KY', KY)):
        if ('%s = %s' % (k, v)) not in js: raise SystemExit('gargo.js 의 %s 가 %s 가 아니다 — 칸 셈이 어긋난다' % (k, v))
    P = json.load(open(os.path.join(ROOT, 'gargo', 'pack-%s.json' % AREA), encoding='utf-8'))
    bx, by = P['base']; nx, ny = P['nx'], P['ny']
    def XY(i): lon = (bx + nx[i]) / 1e6; lat = (by + ny[i]) / 1e6; return ((lon - LON0) * KX, (LAT0 - lat) * KY)
    def cell(x, y): return '%d_%d' % (x // CELL, y // CELL)
    S = P['seg']; core = [i for i, s in enumerate(S) if s[4] <= CORE]; cs = set(core); cn = set()
    for i in core: cn.add(S[i][0]); cn.add(S[i][1])
    T = collections.defaultdict(list)
    for i, s in enumerate(S):
        if i in cs: continue
        (ax, ay), (bx2, by2) = XY(s[0]), XY(s[1]); T[cell((ax + bx2) / 2, (ay + by2) / 2)].append(i)
    def rows(ids):
        geo = []; out = []
        for i in ids:
            r = list(S[i])
            if r[8] >= 0: geo.append(P['geo'][r[8]]); r[8] = len(geo) - 1
            out.append([i] + r)
        return out, geo
    tc = {}
    for k, ids in T.items():
        for i in ids: tc[i] = k
    turns_core = []; turns_t = collections.defaultdict(list)
    for t in P['turns']:
        if t[1] in cs and t[2] in cs: turns_core.append(t); continue
        k = tc.get(t[1]) if t[1] not in cs else tc.get(t[2])
        if k is None: k = cell(*XY(t[0]))
        turns_t[k].append(t)
    D = os.path.join(ROOT, 'gargo', 'pk-%s' % AREA); os.makedirs(os.path.join(D, 't'), exist_ok=True)
    for f in os.listdir(os.path.join(D, 't')): os.remove(os.path.join(D, 't', f))
    sz = []
    keys = sorted(set(T) | set(turns_t))
    for k in keys:
        ids = T.get(k, []); r, g = rows(ids); need = set()
        for i in ids: need.add(S[i][0]); need.add(S[i][1])
        nodes = [[n, nx[n], ny[n]] for n in sorted(need - cn)]
        doc = {'schema': 'gargo-pack-tile/1', 'cell': k, 'nodes': nodes, 'segs': r, 'geo': g, 'turns': turns_t.get(k, [])}
        p = os.path.join(D, 't', k + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); sz.append(os.path.getsize(p))
    r, g = rows(core)
    C = {k: P[k] for k in P if k not in ('nx', 'ny', 'seg', 'geo', 'turns')}
    C.update({'schema': 'gargo-pack-tiles/1', 'cell': CELL, 'core_max_grade': CORE, 'proj': [LON0, LAT0, KX, KY], 'nodes': [[n, nx[n], ny[n]] for n in sorted(cn)], 'segs': r, 'geo': g, 'turns': turns_core,
              'tiles': {k: len(T.get(k, [])) for k in keys}, 'n_total': len(nx), 'seg_total': len(S),
              'fields_tiles': 'core = 등급 1~%d 길 줄과 그 마디 · t/<칸>.json = 나머지 길 줄(가운데 점 기준 %dm 칸) · nodes[[마디 번호(전체), nx, ny]] · segs[[길 줄 번호(전체), …seg 한 줄(마디 = 전체 번호 · 선 번호 = 그 파일 geo 번호)]] · turns 는 전체 번호 그대로' % (CORE, CELL)})
    p = os.path.join(D, 'core.json'); json.dump(C, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('core', len(core), '줄 ·', len(cn), '마디 ·', os.path.getsize(p), 'B · 칸', len(keys), '· 칸 합', sum(sz), 'B · 가장 큰 칸', max(sz) if sz else 0, 'B · 회전 제한 core', len(turns_core), '칸', sum(len(v) for v in turns_t.values()))
if __name__ == '__main__': main()
