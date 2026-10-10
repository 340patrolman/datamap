# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚓 경찰서 카드에 붙일 「이 서 관할 한눈에」(소유자 2026-10-10 「경찰서를 터치하면 관련 모든 내용이 다 나와야 하는데 지금 안 나온다 · 추가할 내용 있으면 더 넣고 역사 같은 것도」)
#   새로 받는 자료 없음 — 이미 구운 것만 묶는다: data/police.json(별표2 관할 × 행정동 · 지구대·파출소) × r/<구>/profile.json(행정동마다 주민·가구·사업체·가게·교통사고 10년·시설·대중교통·생활인구·외국인)
#   둘 이상의 서가 번지로 나눠 맡는 동(「경계」)은 서 수로 나눠 더한다(근사 — 어느 번지가 어느 서인지는 이 자료로 못 가린다) · 값마다 그렇게 넣은 동 수를 같이 싣는다
#   연혁(hist)은 tools/region/polcard-hist.json 에 출처와 함께 손으로 적은 것만 싣는다(지어내지 않는다 — 없는 서는 빈칸)
#   py -3.12 -X utf8 tools/region/polcard-bake.py → data/police-card.json   (police.json·profile.json 을 다시 구우면 이것도 다시)
import json, os, glob, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
POL = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8'))
HF = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polcard-hist.json')
HIST = json.load(open(HF, encoding='utf-8')) if os.path.exists(HF) else {}
YEARS = [str(y) for y in range(2016, 2026)]

def main():
    D = {}
    for f in glob.glob(os.path.join(R, '[0-9]' * 5, 'profile.json')):
        p = json.load(open(f, encoding='utf-8'))
        for k, v in p['dong'].items(): v['_gu'] = p['name']; D[k] = v
    S = {s[0]: s for s in POL['stations']}; A = {}
    for i in S: A[i] = {'dongs': [], 'w': collections.Counter(), 'yr': collections.Counter(), 'age': collections.Counter(), 'fac': collections.Counter(), 'day': [0.0] * 24, 'st': [], 'nshare': 0, 'gus': collections.Counter()}
    miss = 0
    for code, li in POL['dong'].items():
        lab = str(POL['labels'][li]).split('~')   # 「21~6」 = 기본 21번 서 + 일부 번지 6번 서 · 「1,4」 = 두 서가 나눠 맡음(js polLab 과 같다)
        ids = [int(x) for x in lab[0].split(',') if x != '']; ext = [int(x) for x in (lab[1] if len(lab) > 1 else '').split(',') if x != '']
        d = D.get(code)
        if not d: miss += 1; continue
        for i in ids:
            if i not in A: continue
            a = A[i]; w = 1.0 / len(ids); jm = d.get('주민') or {}; sg = d.get('가구·주택·사업체(SGIS)') or {}; ac = d.get('교통사고(TAAS 2016~2025)') or {}; tr = d.get('이동(대중교통)') or {}
            a['dongs'].append([code, d['이름'], round(d.get('넓이_km2') or 0, 2), jm.get('계') or 0, [S[x][1] for x in ids + ext if x != i and x in S] or None])
            a['gus'][d['_gu']] += 1
            if len(ids) > 1 or ext: a['nshare'] += 1
            W = a['w']
            W['pop'] += w * (jm.get('계') or 0); W['km2'] += w * (d.get('넓이_km2') or 0); W['hh'] += w * (sg.get('가구') or 0); W['biz'] += w * (sg.get('사업체') or 0); W['emp'] += w * (sg.get('종사자') or 0)
            W['shop'] += w * ((d.get('가게(상가업소)') or {}).get('계') or 0); W['frn'] += w * ((d.get('외국인주민(이 동 · 행안부 2024.11)') or {}).get('합계') or 0)
            W['acc'] += w * (ac.get('계') or 0); W['dead'] += w * (ac.get('사망자') or 0); W['hurt'] += w * (ac.get('중상자') or 0); W['ped'] += w * (ac.get('보행자 피해') or 0)
            W['bike'] += w * (ac.get('자전거') or 0); W['pm'] += w * (ac.get('PM') or 0); W['moto'] += w * (ac.get('이륜·원동기 가해') or 0); W['night'] += w * (ac.get('계') or 0) * (ac.get('밤(20~6시)%') or 0) / 100
            for y in YEARS: a['yr'][y] += w * ((ac.get('해마다') or {}).get(y) or 0)
            for g, n in (jm.get('연령10세') or {}).items(): a['age'][g] += w * n
            for g, n in (d.get('시설(250m 칸 합 · 근사)') or {}).items(): a['fac'][g] += w * n
            W['bus'] += w * (tr.get('버스 하루 승차') or 0); W['sub'] += w * (tr.get('역 하루 승차') or 0)
            for nm in (tr.get('역') or []):
                if nm not in a['st']: a['st'].append(nm)
            lv = (d.get('머무는 사람(생활인구)') or {}).get('평일 시간대(0~23시)')
            if lv and len(lv) == 24:
                W['live_n'] += 1
                for h in range(24): a['day'][h] += w * lv[h]
    OUT = {}; I = lambda x: int(round(x))
    for i, a in A.items():
        if not a['dongs']: continue
        W = a['w']; ag = a['age']; pop = W['pop'] or 1
        young = ag.get('0~9', 0) + ag.get('10~19', 0); old60 = sum(v for k, v in ag.items() if k[:2] in ('60', '70', '80', '90')); old70 = sum(v for k, v in ag.items() if k[:2] in ('70', '80', '90'))
        o = {'n': S[i][1], 'gus': [k for k, _ in a['gus'].most_common()], 'dongs': sorted(a['dongs'], key=lambda x: -x[3]), 'nshare': a['nshare'],
             'pop': I(W['pop']), 'km2': round(W['km2'], 1), 'hh': I(W['hh']), 'biz': I(W['biz']), 'emp': I(W['emp']), 'shop': I(W['shop']), 'frn': I(W['frn']),
             'age': [round(100 * young / pop, 1), round(100 * old60 / pop, 1), round(100 * old70 / pop, 1)],
             'acc': {'n': I(W['acc']), 'yr': [I(a['yr'][y]) for y in YEARS], 'dead': I(W['dead']), 'hurt': I(W['hurt']), 'ped': I(W['ped']), 'bike': I(W['bike']), 'pm': I(W['pm']), 'moto': I(W['moto']),
                     'night': round(100 * W['night'] / W['acc'], 1) if W['acc'] else None, 'per1k': round(W['acc'] / 10 / pop * 1000, 2) if W['pop'] else None},
             'fac': {k: I(v) for k, v in sorted(a['fac'].items(), key=lambda x: -x[1]) if I(v) > 0},
             'tr': {'bus': I(W['bus']), 'sub': I(W['sub']), 'st': a['st'][:30]} if (W['bus'] or W['sub']) else None,
             'live': [I(x) for x in a['day']] if W['live_n'] else None}
        h = HIST.get(S[i][1])
        if h: o['hist'] = h
        OUT[str(i)] = o
    # 같은 시도청 안 차례(주민 · 넓이 · 사고 10년 · 주민 1천 명당 사고) — 1 이 가장 큼
    by = collections.defaultdict(list)
    for i, o in OUT.items(): by[S[int(i)][5]].append(i)
    for hq, L in by.items():
        for key, fn in (('pop', lambda o: o['pop']), ('km2', lambda o: o['km2']), ('acc', lambda o: o['acc']['n']), ('per1k', lambda o: o['acc']['per1k'] or 0)):
            for r, i in enumerate(sorted(L, key=lambda i: -fn(OUT[i]))): OUT[i].setdefault('rank', {})[key] = [r + 1, len(L)]
    doc = {'schema': 'tg-police-card/1', 'made': datetime.date.today().isoformat(),
           'source': '관할 = data/police.json(경찰청과 그 소속기관 직제 시행규칙 별표2 × 행정동 경계) · 값 = r/<구>/profile.json 의 행정동 값을 서마다 더한 것(주민등록 · SGIS 2023 · 상가업소 · TAAS 2016~2025 · 250m 칸 시설 · 교통카드 · 서울 생활인구 · 행안부 외국인주민)',
           'note': ['행정동 단위 근사다 — 둘 이상의 서가 번지로 나눠 맡는 동은 서 수로 똑같이 나눠 더했다(nshare = 그런 동 수)', '교통사고는 TAAS 공개 자료를 250m 칸으로 모아 가장 넓게 걸친 동에 몰아 센 값이다(경찰 내부 사고 통계와 다르다)',
                    '생활인구(live)·대중교통(tr)은 자료가 있는 동만 더했다(서울·경기 일부) — 없는 서는 빈칸', '연혁(hist)은 출처를 확인한 서만 싣는다 — 없는 서는 빈칸이지 「역사가 없다」가 아니다', '서 사이 차례(rank)는 같은 시도경찰청 안에서 센 것이다 — 1 이 가장 크다'],
           'fields': 'st{경찰서 번호(police.json stations 의 번호): {n 이름, gus[걸친 시군구], dongs[[행정동 코드, 이름, 넓이 ㎢, 주민, 같이 맡는 서 이름들|null]…], nshare, pop 주민, km2, hh 가구, biz 사업체, emp 종사자, shop 가게, frn 외국인주민, age[19세 이하 %, 60세 이상 %, 70세 이상 %], acc{n 10년 사고, yr[2016…2025], dead 사망자, hurt 중상자, ped 보행자 피해, bike 자전거, pm, moto 이륜 가해, night 밤(20~6시) %, per1k 주민 1천 명당 한 해}, fac{시설: 수}, tr{bus 버스 하루 승차, sub 역 하루 승차, st[역]}|null, live[평일 0~23시 생활인구]|null, rank{pop·km2·acc·per1k: [차례, 서 수]}, hist[[연도·날짜, 글, 출처]…]}}',
           'st': OUT}
    p = os.path.join(ROOT, 'data', 'police-card.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('서', len(OUT), '/', len(S), '· 프로필 없는 동', miss, '· 바이트', os.path.getsize(p), '· 연혁 있는 서', sum(1 for o in OUT.values() if o.get('hist')))
    for i, o in OUT.items():
        if o['n'] in ('서울서초경찰서', '서울방배경찰서', '화성서부경찰서'):
            print(o['n'], o['gus'], len(o['dongs']), '동 · 나눠 맡는', o['nshare'], '· 주민', o['pop'], '· 사고', o['acc']['n'], o['acc']['yr'], '사망', o['acc']['dead'], '· 차례', o['rank'], '· 역', len(o['tr']['st']) if o['tr'] else 0)
if __name__ == '__main__': main()
