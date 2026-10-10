# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚆 철도 노선도식 선(게임 세션 부탁 2026-10-10 「철도·지하철 노선 선 — 노선도로 그릴 것」 · 소유자 「교통 노선도 도로 철도」) → data/rail-lines.json
#   실제 선로 모양 자료가 아직 없어, 한국철도공사 열차운행정보(train-bake.py 가 받아 둔 하루치 07_API키/out/train/run_<날>.json)의 **정차 차례**로 역과 역을 곧게 잇는다
#   이음 = 어떤 열차가 A 다음에 B 에 섰고, 다른 어떤 열차도 A 와 B 사이에 다른 역에 서지 않은 짝(가장 잘게 쪼갠 이음 — 고속열차가 건너뛴 긴 선은 버린다)
#   역 자리 = data/train-seoul.json 의 ll(없는 역은 그 이음을 뺀다) · 갈래 = 노선 이름에 「고속」이 있으면 고속철, 아니면 일반철도
#   py -3.12 -X utf8 tools/region/railline-bake.py [YYYYMMDD]
import json, os, sys, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'train')
def main():
    fs = sorted(glob.glob(os.path.join(OUT, 'run_%s.json' % (sys.argv[1] if len(sys.argv) > 1 else '*'))))
    rows = json.load(open(fs[-1], encoding='utf-8')); day = os.path.basename(fs[-1])[4:12]
    LL = {k: v['ll'] for k, v in json.load(open(os.path.join(ROOT, 'data', 'train-seoul.json'), encoding='utf-8'))['stn'].items() if 'll' in v}
    LL.update({'서울': [126.9708, 37.55473], '용산': [126.9648, 37.52991]})   # 한국철도공사_역 위치 정보(15127532) 값 — train-seoul.json 은 도착지인 서울 쪽 역을 stn 에 싣지 않는다
    try:
        import csv, io
        cnt = collections.Counter(); tmp = {}   # 서울시 역사마스터(전철이 같이 서는 역 — 청량리·왕십리·상봉 등) · 이름이 한 자리뿐인 역만
        seen = set()
        for it in json.load(open(os.path.join(ROOT, 'data', 'r', 'stations.json'), encoding='utf-8'))['items']:
            n3 = it[0][:-1] if it[0].endswith('역') and len(it[0]) > 2 else it[0]; key = (n3, round(it[2], 2), round(it[3], 2))
            if n3 in tmp and abs(tmp[n3][0] - it[2]) < 0.02 and abs(tmp[n3][1] - it[3]) < 0.02: continue   # 같은 역의 노선별 승강장(2km 안)은 한 자리로
            if key not in seen: seen.add(key); cnt[n3] += 1; tmp[n3] = [it[2], it[3]]
        for k3, v3 in tmp.items():
            if cnt[k3] == 1: LL.setdefault(k3, v3)
        R2 = list(csv.reader(io.StringIO(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15067652', 'x.csv'), 'rb').read().decode('cp949')))); h2 = {k: i for i, k in enumerate(R2[0])}
        for r in R2[1:]:   # 국가철도공단_철도역 정보(15067652) — 0 으로 빈 줄은 뺀다
            try:
                n2 = r[h2['역이름']].strip(); n2 = n2[:-1] if n2.endswith('역') else n2; xy = [round(float(r[h2['경도좌표']]), 5), round(float(r[h2['위도좌표']]), 5)]
                if 124 < xy[0] < 132 and 33 < xy[1] < 39 and n2 != '경주': LL.setdefault(n2, xy)   # 「경주역」 줄은 문 닫은 옛 시내 역
            except Exception: pass
        for r in list(csv.reader(io.StringIO(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15127532', 'x.csv'), 'rb').read().decode('cp949'))))[1:]:
            if len(r[2].split('.')[-1]) > 2 and len(r[3].split('.')[-1]) > 2: LL.setdefault(r[1].strip(), [round(float(r[3]), 5), round(float(r[2]), 5)])   # 소수 둘째 자리까지만 적힌 거친 자리는 쓰지 않는다
    except Exception as e: print('역 위치 표 못 읽음', e)
    T = collections.defaultdict(list)
    for r in rows:
        if r['stop_se_nm'] in ('시발', '종착', '여객승하차'): T[r['trn_no']].append(r)
    pair = collections.defaultdict(collections.Counter); between = set()
    for no, st in T.items():
        st.sort(key=lambda r: int(r['trn_run_sn'])); nm = [r['stn_nm'] for r in st]
        for i in range(len(st) - 1):
            a, b = nm[i], nm[i + 1]
            if a != b: pair[tuple(sorted((a, b)))][st[i + 1]['mrnt_nm']] += 1
        for i in range(len(nm)):
            for j in range(i + 2, len(nm)): between.add(tuple(sorted((nm[i], nm[j]))))   # 사이에 다른 정차역이 있는 짝
    lines = []; noll = set(); cut = 0
    import math
    far = collections.Counter(); tot = collections.Counter()
    for (a, b) in pair:
        if (a, b) in between or a not in LL or b not in LL: continue
        km = math.hypot((LL[a][0] - LL[b][0]) * 88.8, (LL[a][1] - LL[b][1]) * 111.0)
        for x in (a, b): tot[x] += 1; far[x] += 1 if km > 100 else 0
    bad = sorted(x for x in tot if far[x] == tot[x])   # 모든 이음이 100km 를 넘는 역 = 좌표가 틀린 역(출처 표의 잘못) — 뺀다
    for x in bad: LL.pop(x, None)
    print('좌표가 틀려 뺀 역', bad)
    for (a, b), c in sorted(pair.items()):
        if (a, b) in between: cut += 1; continue
        if a not in LL or b not in LL: noll.add(a if a not in LL else b); continue
        ln = c.most_common(1)[0][0]; pa, pb = LL[a], LL[b]
        lines.append([ln, '고속철' if '고속' in ln else '일반철도', '', [round(pa[0] * 1e4), round(pa[1] * 1e4), round(pb[0] * 1e4) - round(pa[0] * 1e4), round(pb[1] * 1e4) - round(pa[1] * 1e4)], a, b, sum(c.values())])
    d8 = '%s-%s-%s' % (day[:4], day[4:6], day[6:])
    doc = {'schema': 'tg-rail-lines/1', 'made': datetime.date.today().isoformat(),
           'source': '한국철도공사_열차운행정보(공공데이터포털 B551457 · %s 하루 정차 기록)의 정차 차례 · 역 자리 = 한국철도공사_역 위치 정보(15127532) 등(data/train-seoul.json 의 ll)' % d8,
           'note': ['**실제 선로 모양이 아니다** — 역과 역을 곧게 이은 노선도식 선이다(산·강을 가로지르는 것처럼 보일 수 있다). 화면에 그렇게 밝힌다',
                    '이음은 그날 다닌 여객열차의 정차 차례에서 읽었다 — 어떤 열차도 그 사이에 서지 않은 짝만(가장 잘게 쪼갠 이음). 고속열차만 다니는 구간은 고속열차가 서는 역끼리 길게 이어진다',
                    '노선 이름은 그 구간을 지난 열차 기록에 가장 많이 적힌 노선이다(한 선로를 여러 노선이 같이 쓰면 하나만 적힌다) · 갈래는 노선 이름에 「고속」이 있는지로 갈랐다',
                    'SRT(수서고속철)·화물 전용선·광역전철은 이 자료에 없다 — 지하철·전철 노선도식 선은 data/subway-reach.json 의 links(km ≠ -1)',
                    '색은 비워 두었다(공식 노선색 자료를 싣지 않았다)'],
           'fields': 'lines[[노선 이름, 갈래(고속철·일반철도), 색(빈 글), 선 = 경도·위도×1e4 정수 첫 점 + 차이, 역 A, 역 B, 그날 이 구간을 지난 열차 수]]',
           'lines': lines}
    p = os.path.join(ROOT, 'data', 'rail-lines.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(d8, '이음', len(lines), '· 사이에 역이 있어 버린 긴 짝', cut, '· 자리 없는 역', sorted(noll), '· 바이트', os.path.getsize(p))
    print(collections.Counter(x[0] for x in lines).most_common(30))
if __name__ == '__main__': main()
