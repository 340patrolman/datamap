# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌊 홍수위험지도 × 서울 25구 길·교차로·관서(소유자 업무용 · **결과는 저장소 밖**) → ../07_API키/out/floodmap/seoul/분석_서울.json · 분석_서울.md
#   ⚠ 홍수위험지도는 공공누리 4유형(변경금지) — 이 도구가 센 값은 공개 저장소·공개 지도에 싣지 않는다(tools/region/floodmap-fetch.py seoul 이 받은 10m 칸을 읽는다)
#   구마다: 길(ITS 표준노드링크 · data/r/<구>/itsl.json)의 잠기는 길이 · 교차로(T-GIS · data/tgis-seoul.json)가 놓인 자리 · 지구대·파출소·경찰서·소방서·119안전센터 자리(둘레 60m)
#   「0.5m 이상」은 이 도구가 잡은 문턱이다(공식 통제 기준이 아니다) · 서초처럼 길을 따라 출동 지연까지 세는 것은 tools/signal/floodzone-check.py(서초 둘레만)
#   py -3.12 -X utf8 tools/region/floodzone-seoul.py
import json, os, math, glob, datetime, collections
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); FD = os.path.join(KB, '07_API키', 'out', 'floodmap', 'seoul')
DEP = ['없음', '0.5m 미만', '0.5~1m', '1~2m', '2~5m', '5m 이상']; USE = ['cty_030', 'cty_100', 'ntn_100', 'ntn_200', 'ntn_500']
NM = {'cty_030': '도시침수 30년', 'cty_100': '도시침수 100년', 'ntn_100': '한강 범람 100년', 'ntn_200': '한강 범람 200년', 'ntn_500': '한강 범람 500년'}
def inside(px, py, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def main():
    M = json.load(open(os.path.join(FD, 'meta.json'), encoding='utf-8')); box = M['box']; dx, dy, W, H = M['dx'], M['dy'], M['w'], M['h']
    R = {k: np.load(os.path.join(FD, k + '.npz'))['cls'] for k in USE if M['layers'].get(k) == 'ok'}
    def at(k, lon, lat):
        x = int((lon - box[0]) / dx); y = int((box[3] - lat) / dy)
        return int(R[k][y, x]) if 0 <= x < W and 0 <= y < H else 0
    def around(k, lon, lat):
        return max(at(k, lon + a / 88800, lat + b / 111000) for a in (-60, -30, 0, 30, 60) for b in (-60, -30, 0, 30, 60))
    GU = {}; polys = []
    for dp in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'dong.json'))):
        d = json.load(open(dp, encoding='utf-8')); gu = os.path.basename(os.path.dirname(dp)); GU[gu] = d.get('name') or gu
        for x in d.get('dong') or []:
            for poly in x['polys']:
                xs = [p[0] for p in poly[0]]; ys = [p[1] for p in poly[0]]; polys.append((min(xs), min(ys), max(xs), max(ys), poly[0], gu, x['name']))
    def where(lon, lat):
        for b in polys:
            if b[0] <= lon <= b[2] and b[1] <= lat <= b[3] and inside(lon, lat, b[4]): return b[5], b[6]
        return None, None
    S = {g: {'road': {k: [0.0] * 6 for k in R}, 'int': {k: [0] * 6 for k in R}, 'roads': {k: collections.defaultdict(lambda: [0.0, 0]) for k in R}, 'stn': [], 'ints': []} for g in GU}
    for gu in GU:   # 길
        fp = os.path.join(ROOT, 'data', 'r', gu, 'itsl.json')
        if not os.path.exists(fp): continue
        for x in json.load(open(fp, encoding='utf-8'))['items']:
            c = x[4]; a = b = 0; pts = []
            for j in range(0, len(c), 2): a += c[j]; b += c[j + 1]; pts.append((a / 1e5, b / 1e5))
            wet = {k: 0.0 for k in R}; mx = {k: 0 for k in R}
            for p, q in zip(pts, pts[1:]):
                d = math.hypot((q[0] - p[0]) * 88800, (q[1] - p[1]) * 111000); n = max(1, int(d // 20)); st = d / n
                for s in range(n):
                    lo = p[0] + (q[0] - p[0]) * (s + 0.5) / n; la = p[1] + (q[1] - p[1]) * (s + 0.5) / n
                    for k in R:
                        v = at(k, lo, la); S[gu]['road'][k][v] += st
                        if v >= 2: wet[k] += st
                        if v > mx[k]: mx[k] = v
            for k in R:
                if wet[k] > 0 and x[2]: e = S[gu]['roads'][k][x[2]]; e[0] += wet[k]; e[1] = max(e[1], mx[k])
    for t in json.load(open(os.path.join(ROOT, 'data', 'tgis-seoul.json'), encoding='utf-8'))['items']:   # 교차로
        gu, dn = where(t[3], t[2])
        if not gu: continue
        c = {k: at(k, t[3], t[2]) for k in R}
        for k in R: S[gu]['int'][k][c[k]] += 1
        if c.get('cty_100', 0) >= 3 or c.get('ntn_200', 0) >= 3: S[gu]['ints'].append([t[1], dn] + [DEP[c[k]] for k in R])
    PO = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8')); FI = json.load(open(os.path.join(ROOT, 'data', 'agency-pts.json'), encoding='utf-8'))['fire']
    pts = [(b[0] + ('지구대' if b[1] == 0 else '파출소'), '경찰', b[4], b[3]) for b in PO['pbox']] + [(s[1], '경찰', s[3], s[2]) for s in PO['stations']]
    for f in FI:
        if f.get('lon') and f.get('lat'): pts.append((f['n'], '소방', f['lon'], f['lat']))
        pts += [(c[0], '소방', c[4], c[3]) for c in f.get('c', []) if c[3] and c[4]]
    for nm, kind, lo, la in pts:
        if not lo or not la or not (box[0] <= lo <= box[2] and box[1] <= la <= box[3]): continue
        gu, dn = where(lo, la)
        if not gu: continue
        c = [around(k, lo, la) for k in R]
        if max(c) >= 2: S[gu]['stn'].append([nm, kind, dn] + [DEP[v] for v in c])
    keys = list(R); res = {'made': datetime.date.today().isoformat(), 'license': '공공누리 4유형(출처표시 · 상업적 이용금지 · 변경금지) — 환경부 한강홍수통제소 홍수위험지도를 읽어 센 값 · 공개 저장소·공개 지도에 싣지 않는다', 'layers': [NM[k] for k in keys], 'gu': {}}
    o = ['# 홍수위험지도 × 서울 25구 (내부용 · %s)' % res['made'], '', '> 환경부 한강홍수통제소 홍수위험지도(공공누리 4유형)를 읽어 센 값이다. **공개 저장소·공개 지도에 싣지 않는다.**',
         '> 가장 나쁜 경우를 가정한 계산이다(제방 붕괴·월류 · 하수도가 감당 못 하는 비) — 실제로 그렇게 잠긴다는 뜻이 아니다. 「0.5m 이상」은 이 도구의 문턱이다.', '',
         '## 구마다 — 0.5m 이상 잠기는 길(km) · 그런 자리에 놓인 교차로(곳)', '', '| 구 | ' + ' | '.join(NM[k] + ' 길' for k in keys) + ' | ' + ' | '.join(NM[k] + ' 교차로' for k in ('cty_100', 'ntn_200') if k in R) + ' | 잠기는 자리의 관서 |', '|---|' + '---|' * (len(keys) + 3)]
    order = sorted(GU, key=lambda g: -sum(S[g]['road'].get('cty_100', [0] * 6)[2:]))
    for g in order:
        v = S[g]; wet = {k: sum(v['road'][k][2:]) / 1000 for k in keys}; iw = {k: sum(v['int'][k][2:]) for k in keys}
        res['gu'][g] = {'name': GU[g], 'wet_km': {NM[k]: round(wet[k], 2) for k in keys}, 'road_m': {NM[k]: [round(z) for z in v['road'][k]] for k in keys}, 'int': {NM[k]: v['int'][k] for k in keys},
                        'roads': {NM[k]: sorted(([n, round(e[0]), DEP[e[1]]] for n, e in v['roads'][k].items()), key=lambda r: -r[1])[:12] for k in keys}, 'stations': v['stn'], 'deep_ints': v['ints']}
        o.append('| %s | ' % GU[g] + ' | '.join('%.1f' % wet[k] for k in keys) + ' | ' + ' | '.join(str(iw[k]) for k in ('cty_100', 'ntn_200') if k in R) + ' | %d |' % len(v['stn']))
    tot = {k: sum(sum(S[g]['road'][k][2:]) for g in GU) / 1000 for k in keys}
    o += ['| **서울** | ' + ' | '.join('**%.1f**' % tot[k] for k in keys) + ' | ' + ' | '.join('**%d**' % sum(sum(S[g]['int'][k][2:]) for g in GU) for k in ('cty_100', 'ntn_200') if k in R) + ' | **%d** |' % sum(len(S[g]['stn']) for g in GU), '']
    for g in order:
        v = res['gu'][g]; o += ['## ' + v['name'], '']
        for k in ('cty_100', 'ntn_200'):
            if k in R and v['roads'][NM[k]]: o.append('- **%s** 0.5m 이상 길: ' % NM[k] + ' · '.join('%s %sm(%s)' % (r[0], '{:,}'.format(r[1]), r[2]) for r in v['roads'][NM[k]][:8]))
        if v['stations']: o.append('- **잠기는 자리의 관서**(둘레 60m · ' + '/'.join(NM[k] for k in keys) + '): ' + ' · '.join('%s(%s)' % (r[0], '/'.join(r[3:])) for r in v['stations']))
        if v['deep_ints']: o.append('- **1m 이상 잠기는 자리의 교차로** %d곳: ' % len(v['deep_ints']) + ' · '.join(r[0] for r in v['deep_ints'][:25]) + (' …' if len(v['deep_ints']) > 25 else ''))
        o.append('')
    json.dump(res, open(os.path.join(FD, '분석_서울.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(FD, '분석_서울.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(o) + '\n'); print('\n'.join(o[:36])); print('…'); print('\n'.join([l[:400] for l in o if '잠기는 자리의 관서**' in l][:8]))
if __name__ == '__main__': main()
