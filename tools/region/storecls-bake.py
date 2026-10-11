# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏪 행정동마다 등록 상가를 **소분류(247갈래)** 로 센 표(소유자 2026-10-11 「업종은 이렇게밖에 표현이 안 되는지 · 좀 더 세분이 안 되는지」) → data/storecls/<시도 코드>.json
#   매출 자료(서울 상권분석 추정매출)는 생활밀접 100업종까지만 나뉜다 — 더 잔 갈래(한식 안의 백반·고깃집·국밥 …)는 **점포 수**로만 볼 수 있다
#   재료 = 이미 구운 data/r/<구>/stores.json(소상공인시장진흥공단 상가(상권)정보 — 점포마다 [x, y, 소분류 번호, 층, 상호]) × data/r/<구>/dong.json(행정동 경계) · 분류표 data/r/stores-index.json 의 cls
#   등록 정보다 — 영업 중인지 · 매출은 이 자료에 없다(기준 연월 stdrYm)
#   py -3.12 -X utf8 tools/region/storecls-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def inside(px, py, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def main():
    ix = json.load(open(os.path.join(ROOT, 'data', 'r', 'stores-index.json'), encoding='utf-8')); cls = ix['cls']; S = collections.defaultdict(dict); tot = lost = 0; ym = ix.get('stdrYm')
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '*', 'stores.json'))):
        gu = os.path.basename(os.path.dirname(f)); dp = os.path.join(os.path.dirname(f), 'dong.json')
        if not os.path.exists(dp): continue
        st = json.load(open(f, encoding='utf-8')); O = st['o']; K = st['k']; D = json.load(open(dp, encoding='utf-8')).get('dong') or []
        box = []
        for d in D:
            xs = [p[0] for poly in d['polys'] for p in poly[0]]; ys = [p[1] for poly in d['polys'] for p in poly[0]]; box.append((min(xs), min(ys), max(xs), max(ys)))
        cnt = [collections.Counter() for _ in D]
        for p in st['pts']:
            lon = O[0] + p[0] / K[0]; lat = O[1] + p[1] / K[1]; tot += 1; hit = False
            for i, d in enumerate(D):
                b = box[i]
                if lon < b[0] or lon > b[2] or lat < b[1] or lat > b[3]: continue
                if any(inside(lon, lat, poly[0]) and not any(inside(lon, lat, h) for h in poly[1:]) for poly in d['polys']): cnt[i][p[2]] += 1; hit = True; break
            lost += 0 if hit else 1
        for i, d in enumerate(D):
            if cnt[i]: S[gu[:2]][str(d['k'])] = [d['name'], sum(cnt[i].values()), sorted(([c, n] for c, n in cnt[i].items()), key=lambda z: -z[1])]
    os.makedirs(os.path.join(ROOT, 'data', 'storecls'), exist_ok=True); sizes = {}
    for sd, dongs in sorted(S.items()):
        doc = {'schema': 'tg-store-cls/1', 'made': datetime.date.today().isoformat(), 'stdrYm': ym, 'sido': sd,
               'source': '소상공인시장진흥공단 상가(상권)정보(공공데이터포털 · 기준 %s) — data/r/<구>/stores.json 의 점포를 행정동 경계(통계청 SGIS 행정동 · data/r/<구>/dong.json)로 나눠 소분류마다 센 것' % ym,
               'note': ['**등록된 점포 수다** — 지금 영업하는지 · 얼마나 파는지는 이 자료에 없다(매출은 동 카드의 업종 표 = 서울 상권분석 추정매출 100업종)',
                        '소분류 번호는 data/storecls/cls.json 의 cls[번호](= data/r/stores-index.json 의 cls) = [대분류 코드, 대분류, 중분류 코드, 중분류, 소분류, 소분류 코드] 를 가리킨다',
                        '상가정보의 업종은 사업자가 등록한 대표 업종 하나다 — 고깃집이 「백반/한정식」으로 등록돼 있기도 하다 · 동 경계 밖(바다·경계선 위)의 점은 세지 않았다'],
               'fields': 'dong{행정동 8자리: [이름, 점포 수, [[소분류 번호, 점포 수]…] 많은 차례]}', 'dong': dict(sorted(dongs.items()))}
        p = os.path.join(ROOT, 'data', 'storecls', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); sizes[sd] = [len(dongs), os.path.getsize(p)]
    json.dump({'schema': 'tg-store-cls-table/1', 'made': ix.get('baked'), 'stdrYm': ym, 'source': '소상공인시장진흥공단 상가(상권)정보 업종 분류(data/r/stores-index.json 의 cls 를 옮긴 것)', 'note': ['data/storecls/<시도>.json 의 소분류 번호가 가리키는 표 — 번호 = 이 배열의 자리(0부터)'], 'fields': 'cls[[대분류 코드, 대분류, 중분류 코드, 중분류, 소분류, 소분류 코드]…]', 'cls': cls}, open(os.path.join(ROOT, 'data', 'storecls', 'cls.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('점포', tot, '· 동 밖', lost, '· 시도마다 [동 수, 바이트]', sizes)
    v = S['11'].get('11650610'); print(v[0], v[1], [(cls[c][4], n) for c, n in v[2][:12]])
if __name__ == '__main__': main()
