# -*- coding: utf-8 -*-
# 데이터 압축지도 — 📢 집회·시위 해마다(전국 · 시도청 · 일부 경찰서) → data/rally-sdc.json
#   소유자 2026-10-20 「집회시위 행진 등 5년치 월별 연별로 데이터가 있어야 해」 — 서울 달마다는 rallyhist-bake.py(data/rally-hist-seoul.json)
#   원천 = 공공데이터포털 경찰청·시도경찰청 파일(tools/region/dgfile.py <번호> → 07_API키/out/dg/<번호>/x.csv) — 표 글자 그대로 옮겨 같은 꼴로만 맞춘다
#     전국 15045212 집회신고 및 개최 현황(2011~2023) · 경찰력 동원 집회시위(경찰청 누리집 → data/npa-stats.json)
#     강원 15045152(분야별)·15045153(신고/미신고)·15070160(불법폭력시위) · 경기북부 15114224 · 광주 15119358(경찰서별) · 대구 15066382(경찰서별 · 신고·개최)
#     대전 15142268 · 부산 15127924 · 울산 15007072 · 전남 15036156
#   서울·경기남부·인천·충청·경상·전북·제주·세종 청은 공개 파일이 없다(서울은 「오늘의 주요집회」 게시판으로 따로)
#   py -3.12 -X utf8 tools/region/rallysdc-bake.py
import csv, io, json, os, re, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); DG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg')


def rd(n):
    p = os.path.join(DG, str(n), 'x.csv')
    if not os.path.exists(p): return []
    b = open(p, 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return [[c.strip() for c in r] for r in csv.reader(io.StringIO(b.decode(e)))]
        except UnicodeDecodeError: pass
    return []


def n(x):
    try: return int(float(str(x).replace(',', '')))
    except ValueError: return None


def kind(t):
    t = t.replace(' ', '')
    return 'soc' if t.startswith('사회') else 'eco' if t.startswith('경제') else 'pub' if t.startswith('공공') else None


def yr(x): m = re.search(r'(20\d{2})', x); return m.group(1) if m else None


def main():
    SD = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0])))   # 청 → 해 → 갈래 → [횟수, 인원]
    ST = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0])))   # 청 → 서 → 해 → [횟수, 인원]
    src = {}
    # 강원
    for r in rd(15045152)[1:]:
        for i, k in ((2, 'eco'), (3, 'soc'), (4, 'pub')):
            SD['강원특별자치도경찰청'][r[0]][k][0 if r[1] == '횟수' else 1] += n(r[i]) or 0
    for r in rd(15045153)[1:]: SD['강원특별자치도경찰청'][r[0]]['unrep'][0 if r[1] == '횟수' else 1] += n(r[3]) or 0
    src['강원특별자치도경찰청'] = '15045152 · 15045153'
    viol = {r[0]: {'rally': n(r[1]), 'illegal': n(r[2]), 'cop_hurt': n(r[7])} for r in rd(15070160)[1:]}
    # 경기북부(전체만)
    for r in rd(15114224)[1:]: SD['경기도북부경찰청'][r[0]]['tot'] = [n(r[1]), n(r[2])]
    src['경기도북부경찰청'] = '15114224'
    # 광주(청 + 경찰서 5)
    T = rd(15119358)
    for r in T[1:]:
        k = kind(r[1]); j = 0 if r[2].startswith('횟수') else 1
        for c, v in zip(T[0][3:], r[3:]):
            SD['광주경찰청'][r[0]][k][j] += n(v) or 0
            if c != '광주경찰청': ST['광주경찰청'][c][r[0]][j] += n(v) or 0
    src['광주경찰청'] = '15119358'
    # 대구(관서마다 · 개최 칸 6~11)
    for r in rd(15066382)[1:]:
        y = yr(r[6]); j = 0 if r[8].startswith('횟수') else 1
        for i, k in ((9, 'soc'), (10, 'eco'), (11, 'pub')):
            SD['대구광역시경찰청'][y][k][j] += n(r[i]) or 0
            if r[7] != '대구경찰청': ST['대구광역시경찰청']['대구' + re.sub('경찰서$', '', r[7]) + '경찰서'][y][j] += n(r[i]) or 0
    src['대구광역시경찰청'] = '15066382'
    # 대전·부산·전남(같은 꼴)
    for no, nm in ((15142268, '대전광역시경찰청'), (15127924, '부산광역시경찰청'), (15036156, '전남경찰청')):
        for r in rd(no)[1:]:
            for i, k in ((2, 'soc'), (4, 'eco'), (6, 'pub')): SD[nm][r[0]][k] = [n(r[i]), n(r[i + 1])]
        src[nm] = str(no)
    # 울산
    for r in rd(15007072)[1:]:
        for i, k in ((2, 'soc'), (3, 'eco'), (4, 'pub')): SD['울산광역시경찰청'][r[0]][k][0 if '횟수' in r[1] else 1] += n(r[i]) or 0
    src['울산광역시경찰청'] = '15007072'
    sdc = {}
    for c, ys in SD.items():
        o = {}
        for y, v in sorted(ys.items()):
            if not y: continue
            d = {k: list(x) for k, x in v.items()}
            if 'tot' not in d: d['tot'] = [sum(d[k][0] for k in ('soc', 'eco', 'pub') if k in d), sum(d[k][1] for k in ('soc', 'eco', 'pub') if k in d)]
            o[y] = d
        sdc[c] = o
    st = {c: {s: dict(sorted(v.items())) for s, v in x.items()} for c, x in ST.items()}
    nat = {r[0]: [n(r[1]), n(r[2]), n(r[3]), n(r[4])] for r in rd(15045212)[1:]}
    mob = {}
    try:
        NP = json.load(open(os.path.join(ROOT, 'data', 'npa-stats.json'), encoding='utf-8'))
        t = [x for x in NP['pages']['publice0205']['t'] if '집회' in x['h']][0]
        mob = {y: n(v) for y, v in zip(t['rows'][0][1:], t['rows'][1][1:])}
    except Exception:
        pass
    doc = {'schema': 'tg-rally-sdc/1', 'made': datetime.date.today().isoformat(),
           'source': '경찰청·시도경찰청 공공데이터포털 파일 — 전국 15045212 집회신고 및 개최 현황 · 강원 15045152·15045153·15070160 · 경기북부 15114224 · 광주 15119358 · 대구 15066382 · 대전 15142268 · 부산 15127924 · 울산 15007072 · 전남 15036156 · 경찰력 동원 = 경찰청 누리집 경비국 표',
           'fields': 'nat{해: [신고 건수, 신고 횟수, 개최 횟수, 미개최 횟수]}(2011~2023) · mob{해: 경찰력 동원 집회시위 건수} · sdc{시도청: {해: {soc 사회·eco 경제(노동)·pub 공공·tot 합·unrep 미신고(강원): [횟수, 인원]}}} · st{시도청: {경찰서: {해: [횟수, 인원]}}}(광주·대구) · viol{해: {rally 집회시위, illegal 불법폭력시위, cop_hurt 경찰관 부상}}(강원) · src{시도청: 파일 번호}',
           'note': ['「신고 횟수」는 신고된 날짜 수를 다 센 것이라 개최 횟수보다 훨씬 크다(미리 여러 날을 신고해 두고 일부만 연다)', '청마다 공개한 파일만 — 서울·경기남부·인천·충청·경상·전북·제주·세종 청은 해마다 파일이 없다(서울은 rally-hist-seoul.json 의 「주요 집회」 게시판)', '인원 = 청이 집계한 참가(또는 신고) 인원 — 청마다 기준이 다를 수 있다'],
           'nat': nat, 'mob': mob, 'sdc': sdc, 'st': st, 'viol': viol, 'src': src}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'rally-sdc.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('전국', len(nat), '해 · 동원', len(mob), '· 청', {c: len(v) for c, v in sdc.items()}, '· 경찰서', {c: len(v) for c, v in st.items()})
    print(sdc.get('부산광역시경찰청', {}).get('2025'), sdc.get('광주경찰청', {}).get('2025', {}).get('tot'), sdc.get('대구광역시경찰청', {}).get('2025', {}).get('tot'))


if __name__ == '__main__':
    main()
