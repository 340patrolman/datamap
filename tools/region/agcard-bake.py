# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏛 기관 카드에 붙일 「이 기관 관할 한눈에」(소유자 2026-10-10 「경찰서 하고 있으니 구청·주민센터·소방서·세무서·교육청·등기소·법원 등도 찾아서 내용 넣자」)
#   1차 = 관할 표가 이미 있는 세 가지(data/juris.json — 교육지원청 edu · 법원 court · 세무서 tax) × r/<구>/profile.json 의 행정동 값을 기관마다 더한다(경찰서 polcard-bake.py 와 같은 꼴)
#   새로 받는 자료 없음 · 동이 두 기관에 걸치면(d 값이 [둘]) 반씩(근사) · 기관마다 그렇게 넣은 동 수(nshare)
#   소방서·구청·주민센터·등기소는 관할·주소 자료를 받는 대로 kinds 에 더한다(지금은 없다 — 빈칸이지 0 이 아니다)
#   py -3.12 -X utf8 tools/region/agcard-bake.py → data/agency-card.json   (juris.json·profile.json 을 다시 구우면 이것도 다시)
import json, os, glob, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
JUR = json.load(open(os.path.join(ROOT, 'data', 'juris.json'), encoding='utf-8'))
YEARS = [str(y) for y in range(2016, 2026)]
I = lambda x: int(round(x))

def agg(owner_of, names):   # owner_of(행정동 코드) → [기관 자리…] · names[자리] = 기관 이름
    A = {}
    def a_of(i):
        if i not in A: A[i] = {'dongs': [], 'w': collections.Counter(), 'yr': collections.Counter(), 'age': collections.Counter(), 'fac': collections.Counter(), 'nshare': 0, 'gus': collections.Counter()}
        return A[i]
    for code, d in D.items():
        ids = [i for i in owner_of(code) if i is not None and 0 <= i < len(names)]
        for i in ids:
            a = a_of(i); w = 1.0 / len(ids); jm = d.get('주민') or {}; sg = d.get('가구·주택·사업체(SGIS)') or {}; ac = d.get('교통사고(TAAS 2016~2025)') or {}
            a['dongs'].append([code, d['이름'], round(d.get('넓이_km2') or 0, 2), jm.get('계') or 0, [names[x] for x in ids if x != i] or None]); a['gus'][d['_gu']] += 1
            if len(ids) > 1: a['nshare'] += 1
            W = a['w']
            W['pop'] += w * (jm.get('계') or 0); W['km2'] += w * (d.get('넓이_km2') or 0); W['hh'] += w * (sg.get('가구') or 0); W['house'] += w * (sg.get('주택') or 0); W['biz'] += w * (sg.get('사업체') or 0); W['emp'] += w * (sg.get('종사자') or 0)
            W['shop'] += w * ((d.get('가게(상가업소)') or {}).get('계') or 0); W['frn'] += w * ((d.get('외국인주민(이 동 · 행안부 2024.11)') or {}).get('합계') or 0)
            W['acc'] += w * (ac.get('계') or 0); W['dead'] += w * (ac.get('사망자') or 0)
            for y in YEARS: a['yr'][y] += w * ((ac.get('해마다') or {}).get(y) or 0)
            for g, n in (jm.get('연령10세') or {}).items(): a['age'][g] += w * n
            for g, n in (d.get('시설(250m 칸 합 · 근사)') or {}).items(): a['fac'][g] += w * n
    OUT = {}
    for i, a in A.items():
        W = a['w']; ag = a['age']; pop = W['pop'] or 1
        kid = ag.get('0~9', 0); teen = ag.get('10~19', 0); old60 = sum(v for k, v in ag.items() if k[:2] in ('60', '70', '80', '90')); old70 = sum(v for k, v in ag.items() if k[:2] in ('70', '80', '90'))
        OUT[str(i)] = {'n': names[i], 'gus': [k for k, _ in a['gus'].most_common()], 'ndong': len(a['dongs']), 'dongs': sorted(a['dongs'], key=lambda x: -x[3])[:60], 'nshare': a['nshare'],
                       'pop': I(W['pop']), 'km2': round(W['km2'], 1), 'hh': I(W['hh']), 'house': I(W['house']), 'biz': I(W['biz']), 'emp': I(W['emp']), 'shop': I(W['shop']), 'frn': I(W['frn']),
                       'kid': I(kid), 'teen': I(teen), 'age': [round(100 * (kid + teen) / pop, 1), round(100 * old60 / pop, 1), round(100 * old70 / pop, 1)],
                       'acc': {'n': I(W['acc']), 'yr': [I(a['yr'][y]) for y in YEARS], 'dead': I(W['dead'])},
                       'fac': {k: I(v) for k, v in sorted(a['fac'].items(), key=lambda x: -x[1]) if I(v) > 0}}
    L = list(OUT)
    for key in ('pop', 'km2', 'biz', 'emp'):
        for r, i in enumerate(sorted(L, key=lambda i: -OUT[i][key])): OUT[i].setdefault('rank', {})[key] = [r + 1, len(L)]
    return OUT

def main():
    global D
    D = {}
    for f in glob.glob(os.path.join(R, '[0-9]' * 5, 'profile.json')):
        p = json.load(open(f, encoding='utf-8'))
        for k, v in p['dong'].items(): v['_gu'] = p['name']; D[k] = v
    K = {}
    for kind, J in JUR['kinds'].items():
        names = [o[0] for o in J['o']]; g5 = J.get('g5') or {}; dd = J.get('d') or {}
        def owner(code, g5=g5, dd=dd):
            v = dd.get(code)
            if v is None: v = g5.get(code[:5])
            if v is None or v == -1: return []
            return v if isinstance(v, list) else [v]
        K[kind] = {'title': J['title'], 'source': J['source'], 'note': J['note'], 'ag': agg(owner, names)}
        print(kind, '기관', len(K[kind]['ag']), '/', len(names), '· 주민 합', sum(o['pop'] for o in K[kind]['ag'].values()))
    doc = {'schema': 'tg-agency-card/1', 'made': datetime.date.today().isoformat(),
           'source': '관할 = data/juris.json(기관마다 출처는 kinds[…].source) · 값 = r/<구>/profile.json 의 행정동 값을 기관마다 더한 것(주민등록 · SGIS 2023 가구·주택·사업체·종사자 · 상가업소 · TAAS 2016~2025 · 250m 칸 시설 · 행안부 외국인주민)',
           'note': ['행정동 단위 근사다 — 동이 두 기관에 걸치면 반씩 더했다(nshare = 그런 동 수)', '세무서는 사업체·종사자(SGIS 2023), 교육지원청은 0~9세(kid)·10~19세(teen) 주민과 학교·학원·유치원·어린이집(fac), 법원은 주민·넓이가 그 기관의 일감을 가늠하는 값이다 — 실제 처리 건수가 아니다',
                    '등기소(reg)는 부동산등기 관할이다 — 주택·가구·사업체 수가 일감을 가늠하는 값 · 소방서·주민센터 자리는 agency-pts.json · 구청·검찰청은 아직 없다', '서 사이 차례(rank)는 전국 같은 종류 기관 안에서 센 것이다 — 1 이 가장 크다', '관할 동 목록(dongs)은 주민 많은 순 60곳까지만 실었다(ndong = 전체 수)'],
           'fields': 'kinds{edu·court·tax·reg: {title, source, note, ag{기관 자리(juris.json kinds[…].o 의 차례): {n 이름, gus[걸친 시군구], ndong, dongs[[행정동 코드, 이름, ㎢, 주민, 같이 맡는 기관|null]…], nshare, pop, km2, hh 가구, house 주택, biz 사업체, emp 종사자, shop 가게, frn 외국인주민, kid 0~9세, teen 10~19세, age[19세 이하 %, 60세 이상 %, 70세 이상 %], acc{n 10년 사고, yr[2016…2025], dead}, fac{시설: 수}, rank{pop·km2·biz·emp: [차례, 기관 수]}}}}}',
           'kinds': K}
    p = os.path.join(ROOT, 'data', 'agency-card.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p))
    for kind, nm in (('tax', '서초세무서'), ('tax', '반포세무서'), ('edu', '서울특별시강남서초교육지원청'), ('court', '서울중앙지방법원')):
        for o in K[kind]['ag'].values():
            if o['n'] == nm: print(nm, o['gus'], o['ndong'], '동 · 주민', o['pop'], '· 사업체', o['biz'], '· 종사자', o['emp'], '· 0~9세', o['kid'], '· 10~19세', o['teen'], '· 학교', o['fac'].get('학교'), '· 차례', o['rank'])
if __name__ == '__main__': main()
