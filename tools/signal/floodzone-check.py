# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌊 홍수위험지도 × 길·교차로·관서 맞대기(소유자 업무용 · **결과는 저장소 밖**) → ../07_API키/out/floodmap/seocho/분석.json · 분석.md
#   ⚠ 홍수위험지도는 공공누리 4유형(변경금지) — 이 도구가 센 값은 공개 저장소·공개 지도에 싣지 않는다(tools/region/floodmap-fetch.py 가 받은 것을 읽는다)
#   하는 일: ① 서초구 교차로마다 그 자리의 침수심 단계(도시침수 30·50·100년 · 국가하천 100·200·500년) ② 길 조각마다 15m 간격으로 읽어 가장 깊은 단계와 잠기는 길이
#          ③ 지구대·파출소·경찰서·소방서·119안전센터 자리의 단계 ④ 지하차도·터널 ⑤ 「0.5m 이상 잠기는 길이 막힌다」고 본 출동 지연(도시침수 100년 · 국가하천 200년)
#   침수심 0.5m = 승용차가 다니기 어려워지는 깊이로 잡은 이 도구의 문턱이다(공식 통제 기준이 아니다)
#   py -3.12 -X utf8 tools/signal/floodzone-check.py
import json, os, math, heapq, datetime, collections
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); FD = os.path.join(KB, '07_API키', 'out', 'floodmap', 'seocho')
DEP = ['없음', '0.5m 미만', '0.5~1m', '1~2m', '2~5m', '5m 이상']; USE = ['cty_030', 'cty_050', 'cty_100', 'ntn_100', 'ntn_200', 'ntn_500']
NM = {'cty_030': '도시침수 30년', 'cty_050': '도시침수 50년', 'cty_100': '도시침수 100년', 'ntn_100': '한강 범람 100년', 'ntn_200': '한강 범람 200년', 'ntn_500': '한강 범람 500년'}
def main():
    M = json.load(open(os.path.join(FD, 'meta.json'), encoding='utf-8')); box = M['box']; dx, dy, W, H = M['dx'], M['dy'], M['w'], M['h']
    R = {k: np.load(os.path.join(FD, k + '.npz'))['cls'] for k in USE if M['layers'].get(k) == 'ok'}
    def at(k, lon, lat):
        x = int((lon - box[0]) / dx); y = int((box[3] - lat) / dy)
        return int(R[k][y, x]) if 0 <= x < W and 0 <= y < H else 0
    nav = json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8')); N = nav['nodes']; L = nav['links']
    # ① 교차로
    ints = [(k, v) for k, v in N.items() if v[4] == 1 and str(v[2]) == '101']; ist = {k: collections.Counter() for k in R}; deep = []
    for k, v in ints:
        c = {z: at(z, v[0], v[1]) for z in R}
        for z in R: ist[z][c[z]] += 1
        if c.get('cty_100', 0) >= 3 or c.get('ntn_200', 0) >= 4: deep.append([v[3] or '(이름 없음)', round(v[0], 5), round(v[1], 5)] + [c[z] for z in R])
    # ② 길 조각
    lst = {k: [0.0] * 6 for k in R}; lk_max = {k: {} for k in R}; byroad = {k: collections.defaultdict(lambda: [0.0, 0]) for k in R}; under = []
    for i, x in enumerate(L):
        if x[5] > 6: continue
        c = x[9]; a = b = 0; pts = []
        for j in range(0, len(c), 2): a += c[j]; b += c[j + 1]; pts.append((a / 1e5, b / 1e5))
        mx = {k: 0 for k in R}; wet = {k: 0.0 for k in R}
        for p, q in zip(pts, pts[1:]):
            d = math.hypot((q[0] - p[0]) * 88800, (q[1] - p[1]) * 111000); n = max(1, int(d // 15)); step = d / n
            for s in range(n):
                lo = p[0] + (q[0] - p[0]) * (s + 0.5) / n; la = p[1] + (q[1] - p[1]) * (s + 0.5) / n
                for k in R:
                    v = at(k, lo, la); lst[k][v] += step
                    if v > mx[k]: mx[k] = v
                    if v >= 2: wet[k] += step
        for k in R:
            lk_max[k][i] = mx[k]
            if wet[k] > 0 and x[7]: e = byroad[k][x[7]]; e[0] += wet[k]; e[1] = max(e[1], mx[k])
        if len(x) > 12 and x[12] in ('002', '004'): under.append([x[7] or '(이름 없음)', '지하차도' if x[12] == '002' else '터널', x[3]] + [mx[k] for k in R])
    # ③ 관서
    P = json.load(open(os.path.join(ROOT, 'data', 'police-seocho.json'), encoding='utf-8')); A = json.load(open(os.path.join(ROOT, 'data', 'agency-pts.json'), encoding='utf-8'))['fire']
    def inb(lon, lat): return lon and lat and box[0] <= lon <= box[2] and box[1] <= lat <= box[3]
    pol = [(b['name'], b['lon'], b['lat']) for b in P['boxes'] if inb(b.get('lon'), b.get('lat'))] + [(s['name'], s['lon'], s['lat']) for s in P['stations'] if inb(s.get('lon'), s.get('lat'))]
    fire = []
    for f in A:
        if inb(f.get('lon'), f.get('lat')): fire.append((f['n'], f['lon'], f['lat']))
        fire += [(c[0], c[4], c[3]) for c in f.get('c', []) if inb(c[4], c[3])]
    def around(k, lon, lat):   # 자리와 둘레 60m 안에서 가장 깊은 단계
        m = 0
        for ddx in (-60, -30, 0, 30, 60):
            for ddy in (-60, -30, 0, 30, 60): m = max(m, at(k, lon + ddx / 88800, lat + ddy / 111000))
        return m
    stn = [[nm, '경찰', round(lo, 5), round(la, 5)] + [at(k, lo, la) for k in R] + [around(k, lo, la) for k in R] for nm, lo, la in pol] + [[nm, '소방', round(lo, 5), round(la, 5)] + [at(k, lo, la) for k in R] + [around(k, lo, la) for k in R] for nm, lo, la in fire]
    # ⑤ 출동 지연 — 0.5m 이상 지나는 길 조각이 막힌다
    out = collections.defaultdict(list)
    for i, x in enumerate(L):
        if x[5] <= 6: out[x[1]].append(i)
    def near(lon, lat):
        best = None
        for k, v in N.items():
            if not out.get(k): continue
            d = math.hypot((lon - v[0]) * 88800, (lat - v[1]) * 111000)
            if best is None or d < best[0]: best = (d, k)
        return best
    def spread(srcs, ban):
        D = {}; Wn = {}; h = []
        for nm, lo, la in srcs:
            d, k = near(lo, la)
            if d > 400: continue
            t0 = d / (20 / 3.6)
            if t0 < D.get(k, 1e18): D[k] = t0; Wn[k] = nm; heapq.heappush(h, (t0, k))
        while h:
            d, u = heapq.heappop(h)
            if d > D.get(u, 1e18): continue
            for q in out.get(u, ()):
                if q in ban: continue
                x = L[q]; nd = d + x[3] / (max(x[4], 20) / 3.6)
                if nd < D.get(x[2], 1e18): D[x[2]] = nd; Wn[x[2]] = Wn[u]; heapq.heappush(h, (nd, x[2]))
        return D, Wn
    delay = {}
    for sc in ('cty_100', 'cty_030', 'ntn_200'):
        if sc not in R: continue
        ban = set(i for i, v in lk_max[sc].items() if v >= 2)
        for who, srcs in (('경찰', [p for p in pol if '경찰서' not in p[0]]), ('소방', fire)):
            D0, W0 = spread(srcs, set()); D1, W1 = spread(srcs, ban); cut = 0; late = [0, 0, 0]; worst = []
            for k, v in ints:
                if k not in D0: continue
                if k not in D1: cut += 1; continue
                dl = D1[k] - D0[k]
                if dl >= 30: late[0 if dl < 60 else 1 if dl < 180 else 2] += 1
                if dl >= 120 and v[3]: worst.append([v[3], round(D0[k]), round(D1[k]), W0[k], W1[k]])
            worst.sort(key=lambda r: -(r[2] - r[1])); cz = collections.Counter(W0[k] for k, v in ints if k in D0 and k not in D1)
            delay['%s · %s' % (NM[sc], who)] = {'막는 길 조각': len(ban), '교차로': sum(1 for k, v in ints if k in D0), '닿지 못함': cut, '30~60초 늦음': late[0], '1~3분 늦음': late[1], '3분 넘게 늦음': late[2], '가장 늦는 곳': worst[:10], '닿지 못함이 많은 구역': cz.most_common(8)}
    res = {'made': datetime.date.today().isoformat(), 'license': '공공누리 4유형(출처표시 · 상업적 이용금지 · 변경금지) — 환경부 한강홍수통제소 홍수위험지도를 읽어 센 값 · 공개 저장소·공개 지도에 싣지 않는다', 'layers': list(R), 'dep': DEP,
           'ints': {NM[k]: {DEP[c]: n for c, n in sorted(v.items())} for k, v in ist.items()}, 'road_m': {NM[k]: {DEP[c]: round(v[c]) for c in range(6)} for k, v in lst.items()},
           'roads': {NM[k]: sorted(([nm, round(e[0]), DEP[e[1]]] for nm, e in v.items()), key=lambda r: -r[1])[:25] for k, v in byroad.items()}, 'under': sorted(under, key=lambda r: -max(r[3:])), 'stations': stn, 'deep_ints': deep, 'delay': delay}
    json.dump(res, open(os.path.join(FD, '분석.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    o = ['# 홍수위험지도 × 서초 길·교차로·관서 (내부용 · %s)' % res['made'], '', '> 환경부 한강홍수통제소 홍수위험지도(공공누리 4유형 — 출처표시 · 상업적 이용금지 · 변경금지)를 읽어 센 값이다. **공개 저장소·공개 지도에 싣지 않는다.**',
         '> 홍수위험지도는 제방이 무너지거나 넘치는 가장 나쁜 경우(하천 범람), 하수도·펌프장이 감당 못 하는 비(도시침수)를 가정한 계산이다 — 실제로 그렇게 잠긴다는 뜻이 아니다.', '', '## 교차로 %d곳이 놓인 자리의 침수심' % len(ints), '', '| 지도 | ' + ' | '.join(DEP) + ' |', '|---|' + '---|' * 6]
    for k in R: o.append('| %s | ' % NM[k] + ' | '.join(str(ist[k].get(c, 0)) for c in range(6)) + ' |')
    o += ['', '## 길이(m) — 등급 1~6 길', '', '| 지도 | ' + ' | '.join(DEP[1:]) + ' |', '|---|' + '---|' * 5]
    for k in R: o.append('| %s | ' % NM[k] + ' | '.join('{:,}'.format(round(lst[k][c])) for c in range(1, 6)) + ' |')
    for k in ('cty_100', 'ntn_200'):
        if k in R: o += ['', '## 0.5m 이상 잠기는 길 — %s (긴 차례)' % NM[k], ''] + ['- %s %sm · 가장 깊이 %s' % (r[0], '{:,}'.format(r[1]), r[2]) for r in res['roads'][NM[k]][:20]]
    o += ['', '## 지하차도·터널', '', '| 이름 | 갈래 | 길이 m | ' + ' | '.join(NM[k] for k in R) + ' |', '|---|---|---|' + '---|' * len(R)]
    seen = set()
    for r in res['under']:
        if (r[0], tuple(r[3:])) in seen or max(r[3:]) == 0: continue
        seen.add((r[0], tuple(r[3:]))); o.append('| %s | %s | %d | ' % (r[0], r[1], r[2]) + ' | '.join(DEP[c] for c in r[3:]) + ' |')
    o += ['', '## 관서 자리(둘레 60m 안에서 가장 깊은 단계)', '', '| 관서 | | ' + ' | '.join(NM[k] for k in R) + ' |', '|---|---|' + '---|' * len(R)]
    nR = len(R)
    for r in sorted(stn, key=lambda r: -max(r[4 + nR:])):
        if max(r[4 + nR:]) > 0: o.append('| %s | %s | ' % (r[0], r[1]) + ' | '.join(DEP[c] for c in r[4 + nR:]) + ' |')
    o += ['', '## 출동 지연 — 0.5m 이상 잠기는 길이 막힌다고 보면', '', '견주는 값이다(제한속도 · 막힘 없음 · 신호 없음) — 실제 출동 시간이 아니다. 0.5m 는 이 도구가 잡은 문턱이다.', '']
    for k, v in delay.items():
        o += ['### ' + k, '', '- 막는 길 조각 %d · 교차로 %d 가운데 닿지 못함 **%d** · 3분 넘게 늦음 %d · 1~3분 %d · 30~60초 %d' % (v['막는 길 조각'], v['교차로'], v['닿지 못함'], v['3분 넘게 늦음'], v['1~3분 늦음'], v['30~60초 늦음']),
              '- 닿지 못함이 많은 구역: ' + ' · '.join('%s %d' % (a, b) for a, b in v['닿지 못함이 많은 구역']), '- 가장 늦는 곳: ' + ' / '.join('%s(%s %d초 → %s %d초)' % (r[0], r[3], r[1], r[4], r[2]) for r in v['가장 늦는 곳'][:6]), '']
    open(os.path.join(FD, '분석.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n'); print('\n'.join(o[:200]))
if __name__ == '__main__': main()
