# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.3.0 — 📝 경기 동 풀어 읽기: 경기데이터드림 행정동 단위 3종(시트 · 세션+_csrf · 필터 CRTR_YM)
#   카드매출_행정동_집계 H92OOSWZXICJM0UO4IHH38259217 — 기준년월·행정동(10자리)·업종 중분류 코드·매출액
#     ⚠ 달마다 담긴 범위가 다르다(줄 수 1.5만 ↔ 3.6만) → 빠짐없이 담긴 같은 달끼리만 견준다: 2022·2023·2025년 1~6월
#   데이터분석 유동인구 요일별 행정동 QG3PQ8O43NXGS62A95GO38124431 — 기준년월·행정동·요일·유동인구(2018~)
#   경기도_카드업종대분류_지역화폐 업종구분별 매출 7US3M3EDUQ02JX063KZJ38263831 — 업종 코드 → 이름표(같은 중분류 코드 체계)
#   py -3.12 -X utf8 tools/region/gg-dong-bake.py fetch → 07_API키/out/gg/dong/*.json · build → data/r/<경기 구>/ggdong.json
import json, os, sys, re, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'gg', 'dong')
sys.path.insert(0, 'C:/Users/knpth/regionwork');
MONTHS = ['%d%02d' % (y, m) for y in (2022, 2023, 2025) for m in range(1, 7)]

def fetch():
    from ggf import S
    os.makedirs(OUT, exist_ok=True)
    s = S('H92OOSWZXICJM0UO4IHH38259217')
    for ym in MONTHS:
        fn = os.path.join(OUT, 'card_%s.json' % ym)
        if os.path.exists(fn): continue
        r = s.all(CRTR_YM=ym); json.dump(r, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); print('card', ym, len(r), flush=True)
    for inf, nm in (('QG3PQ8O43NXGS62A95GO38124431', 'flow'), ('7US3M3EDUQ02JX063KZJ38263831', 'lc')):
        fn = os.path.join(OUT, nm + '.json')
        if os.path.exists(fn): continue
        r = S(inf).all(); json.dump(r, open(fn, 'w', encoding='utf-8'), ensure_ascii=False); print(nm, len(r), flush=True)
    print('DONE', flush=True)

def build():
    names = {}
    for r in json.load(open(os.path.join(OUT, 'lc.json'), encoding='utf-8')):
        if r.get('indutype_mdclass_cd') and r.get('indutype_nm'): names[r['indutype_mdclass_cd']] = r['indutype_nm']
    C = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float)))   # 동 → 해 → 업종 → 1~6월 합
    for ym in MONTHS:
        for r in json.load(open(os.path.join(OUT, 'card_%s.json' % ym), encoding='utf-8')):
            k = str(r['admdong_cd'])[:8]; C[k][ym[:4]][r.get('mdclass_indutype_cd') or '?'] += float(r.get('sls_amt') or 0)
    F = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))   # 동 → 해 → 요일 → 달마다 값
    flow = json.load(open(os.path.join(OUT, 'flow.json'), encoding='utf-8')); last = max(r['crtr_ym'] for r in flow)
    for r in flow:
        k = str(r['admdong_cd'])[:8]; F[k][r['crtr_ym'][:4]][r['wday_cd']].append(float(r.get('curr_popltn_cnt') or 0))
    # 옛 코드 → 지금 지도 코드(이름으로) — 화성시 4개 구 신설(2026) 등으로 코드가 바뀐 동. 목록 = 경기데이터드림 「경기도_읍면동_리스트」(T3UYOBH7M6L3F50K6FN138198713)
    R = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); have = {}
    for x in R['gus']:
        if not x['gu'].startswith('41'): continue
        dj = os.path.join(ROOT, 'data', 'r', x['gu'], 'dong.json')
        if os.path.exists(dj):
            for q in json.load(open(dj, encoding='utf-8'))['dong']: have[q['k']] = (re.sub(r'(시).*$', lambda m0: m0.group(1), x['name']), q['name'])
    byName = {}
    for k8, (city, nm) in have.items(): byName.setdefault((city, nm), []).append(k8)
    old = {}
    lf = os.path.join(OUT, 'emdlist.json')
    if os.path.exists(lf):
        for e in json.load(open(lf, encoding='utf-8')):
            k8 = str(e['emd_cd'])[:8]; m = re.match(r'경기도\s+(\S+?[시군])', e.get('detail_addr') or '')
            if k8 not in have and m: c = byName.get((m.group(1), e['emd_nm']));
            else: c = None
            if c and len(c) == 1: old[k8] = c[0]
    remap = lambda k: old.get(k, k)
    C2 = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(float))); F2 = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(list)))
    for k, v in C.items():
        for y, d in v.items():
            for c3, a3 in d.items(): C2[remap(k)][y][c3] += a3
    for k, v in F.items():
        for y, d in v.items():
            for w, l in d.items(): F2[remap(k)][y][w] += l
    C, F = C2, F2; print('옛 코드 이어 붙임', len(old))
    G = collections.defaultdict(dict)
    for k in set(C) | set(F):
        o = {}
        if k in C: o['card'] = {y: {c: round(v / 6 / 1e4) for c, v in d.items()} for y, d in C[k].items()}   # 1~6월 월평균(만 원)
        if k in F: o['flow'] = {y: {w: round(sum(v) / len(v)) for w, v in d.items()} for y, d in F[k].items() if y >= '2019'}
        G[k[:5]][k] = o
    meta = {'schema': 'tg-ggdong/1', 'source': '경기데이터드림 — 카드매출_행정동_집계(H92OOSWZXICJM0UO4IHH38259217) · 데이터분석 유동인구 요일별 행정동(QG3PQ8O43NXGS62A95GO38124431) · 업종 이름표 = 카드업종대분류_지역화폐(7US3M3EDUQ02JX063KZJ38263831)',
            'fields': 'card = {해: {업종 코드: 1~6월 월평균 매출(만 원)}} — 2022·2023·2025년만(빠짐없이 담긴 같은 달) · flow = {해: {요일: 그해 달마다 유동인구 평균}} · names = 업종 코드 → 이름',
            'note': '카드 매출은 경기데이터드림이 가공한 카드사 자료(어느 카드사·현금 포함 여부는 설명 없음) · 서울시 추정매출과 숫자 크기를 직접 견주지 않는다 · 유동인구 최신 ' + last, 'flowLast': last, 'names': names}
    n = 0
    for gu, dd in G.items():
        fn = os.path.join(ROOT, 'data', 'r', gu, 'ggdong.json')
        if os.path.isdir(os.path.dirname(fn)): json.dump(dict(meta, gu=gu, dong=dd), open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); n += 1
    print('dongs', sum(len(v) for v in G.values()), 'gus', n, 'names', len(names), 'flow last', last)

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
