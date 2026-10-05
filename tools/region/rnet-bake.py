# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.13.0 — 🛣 전국 도로망(국가교통정보센터 ITS 표준노드링크 2026-09-14판 · 등급 1~6) 한 장 → data/base/rnet.json
#   소유자 2026-10-06 「전국 도로망 국도 지방도 포함 데이터가 있으면 모두」 — 시군구 파일(r/<구>/itsl.json)에 이미 있는 링크를 모아
#   등급 1 고속 · 2 도시고속 · 3 일반국도 · 4 특별·광역시도 · 5 국가지원지방도 · 6 지방도 만 넓게 볼 때 쓰는 한 장으로(약 30m 단순화) · 7 시군도는 확대해서 구 파일로
#   py -3.12 -X utf8 tools/region/rnet-bake.py
import json, os, glob
from shapely.geometry import LineString
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TOL = {1: 0.0003, 2: 0.0002, 3: 0.0003, 4: 0.0002, 5: 0.0003, 6: 0.0003}

def main():
    seen = set(); out = []; src = ''; names = []; nix = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '*', 'itsl.json'))):
        j = json.load(open(f, encoding='utf-8')); src = j.get('source', src)
        for t in j['items']:
            if t[1] > 6 or t[0] in seen: continue
            seen.add(t[0]); c = t[4]; x = y = 0; pts = []
            for k in range(0, len(c), 2): x += c[k]; y += c[k + 1]; pts.append((x / 1e5, y / 1e5))
            if len(pts) < 2: continue
            s = LineString(pts).simplify(TOL[t[1]], preserve_topology=False); q = list(s.coords)
            if len(q) < 2: continue
            enc = []; px = py = 0
            for a, b in q: ix, iy = round(a * 1e4), round(b * 1e4); enc += [ix - px, iy - py]; px, py = ix, iy
            nm = t[2] or ''
            if nm not in nix: nix[nm] = len(names); names.append(nm)
            out.append([t[1], nix[nm], t[3] or 0, enc])
    # v2.13.0 0.5° 조각 · a = 등급 1~3(넓게 볼 때) · b = 4~6(중간 확대) — 한 장(22MB)은 폰에 무겁다
    import math, shutil
    D = os.path.join(ROOT, 'data', 'base', 'rn'); shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
    T = {}
    for g, ni, ms, enc in out:
        k = ('a' if g <= 3 else 'b') + '_%d_%d' % (math.floor(enc[0] / 1e4 * 2), math.floor(enc[1] / 1e4 * 2))
        t = T.setdefault(k, {'names': [], 'nix': {}, 'links': []}); nm = names[ni]
        if nm not in t['nix']: t['nix'][nm] = len(t['names']); t['names'].append(nm)
        t['links'].append([g, t['nix'][nm], ms, enc])
    idx = {}
    for k, t in T.items():
        fp = os.path.join(D, k + '.json'); json.dump({'names': t['names'], 'links': t['links']}, open(fp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); idx[k] = os.path.getsize(fp)
    json.dump({'schema': 'tg-rnet/1', 'source': src + ' — 등급 1~6 · 약 20~30m 단순화 · 0.5° 조각(a = 1~3 · b = 4~6) · 7 시군도는 시군구 파일(itsl.json)', 'grades': {'1': '고속국도', '2': '도시고속', '3': '일반국도', '4': '특별·광역시도', '5': '국가지원지방도', '6': '지방도', '7': '시군도'},
               'fields': '조각 = {names, links: [등급, 이름 번호, 제한속도 km/h(0 = 자료 없음), 선 = 경도·위도×1e4 정수 첫 점 + 차이]} · 조각 열쇠 = 띠_floor(경도×2)_floor(위도×2)', 'tiles': idx},
              open(os.path.join(D, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('조각', len(idx), 'a', sum(v for k, v in idx.items() if k[0] == 'a'), 'b', sum(v for k, v in idx.items() if k[0] == 'b'), '가장 큰', max(idx.values()))
    return
    doc = {'schema': 'tg-rnet/1', 'source': src + ' — 등급 1~6 만 · 약 20~30m 단순화 · 7 시군도는 확대하면 시군구 파일(itsl.json)', 'grades': {'1': '고속국도', '2': '도시고속', '3': '일반국도', '4': '특별·광역시도', '5': '국가지원지방도', '6': '지방도', '7': '시군도'},
           'fields': 'links = [등급, 이름 번호(names), 제한속도 km/h(0 = 자료 없음), 선 = 경도·위도×1e4 정수 첫 점 + 차이]', 'names': names, 'links': out}
    p = os.path.join(ROOT, 'data', 'base', 'rnet.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    import collections
    print('링크', len(out), collections.Counter(l[0] for l in out), '이름', len(names), '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
