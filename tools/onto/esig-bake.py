# -*- coding: utf-8 -*-
"""📶 업종 조기 신호 — 동 × 업종(인허가 30)마다 개업 흐름 · 폐업이 개업보다 많은 해 · 1년 생존을 나란히 → data/esig/<시도>.json
(ONTOLOGY-3-활용.md ③ 상권 조기 신호 · 「다음 판 순서」 2)

원칙(소유자 2026-10-12): 한 점수로 더하지 않는다 — 신호마다 따로 켜진다 · 「예언이 아니라 조기 신호」 — 크기(n)와 기준 기간을 같이 싣는다 ·
「유망·추천·투자·기회」 말을 쓰지 않는다(늘어나는 · 줄어드는 · 드나듦이 잦은) · 작은 수는 말하지 않는다.
입력: r/<구>/bizsv.json(인허가 개업·폐업 · 전국) · r/<구>/storind.json(서울 상권분석 분기 개업·폐업 · 있을 때만) · data/ind-dict.json(업종 사전) · data/redev.json(입주 예정 · 같은 동이면 표시)
    py -3.12 -X utf8 tools/onto/esig-bake.py [--src <r 폴더>…]      (기본 data/r = 집 PC 의 권역 빌드 출력 · 통신 없음)
bizsv 를 다시 구우면 이것도 다시.
"""
import json, os, sys, glob, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUTD = os.path.join(ROOT, 'data', 'esig')

# 파라미터 — 화면·문서와 같은 값(ONTOLOGY-3-활용.md ③). 바꾸면 파일 머리 params 도 같이 바뀐다.
P = {'min_open_pre': 9,      # 앞 3해 개업 합이 이보다 작으면 말하지 않음
     'min_now': 10,          # 지금 영업이 이보다 작으면 말하지 않음
     'up': 1.5, 'down': 0.6, # 개업 흐름(뒤 2해 해 평균 ÷ 앞 3해 해 평균) 문턱
     'close_years': 2,       # 폐업 > 개업 이 이어진 해 수
     'surv_gap': 0.10,       # 1년 생존이 구의 같은 업종보다 이만큼 낮으면
     'surv_min_n': 10}       # 1년 생존을 볼 최소 대상 수
FLAG = {1: '개업이 늘어남', 2: '개업이 줄어듦', 4: '폐업이 개업보다 많은 해가 이어짐', 8: '드나듦이 잦음(1년 생존이 구보다 낮음)'}


def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    a = sys.argv[1:]
    srcs = a[a.index('--src') + 1:] if '--src' in a else [os.path.join(ROOT, 'data', 'r')]
    dic = load(os.path.join(ROOT, 'data', 'ind-dict.json'))
    svc_of = {r[0]: [n for n, rel in r[1]] for r in dic['rows']}
    rel_of = {r[0]: [rel for n, rel in r[1]] for r in dic['rows']}
    redev = collections.defaultdict(list)
    try:
        for it in load(os.path.join(ROOT, 'data', 'redev.json'))['items']:
            redev[str(it['k'])[:8]].append([it['name'], it.get('move', ''), it.get('hh')])
    except Exception:
        pass
    gus = {}
    for s in srcs:
        for p in glob.glob(os.path.join(s, '*', 'bizsv.json')):
            gus[os.path.basename(os.path.dirname(p))] = os.path.dirname(p)
    by_sido = collections.defaultdict(dict)
    asof_all, tot = set(), collections.Counter()
    for gu in sorted(gus):
        d = gus[gu]
        b = load(os.path.join(d, 'bizsv.json'))
        cats, yrs = b['cats'], b['years']
        asof = str(b.get('asof', ''))
        asof_all.add(asof)
        last = int(asof[:4]) - 1 if asof[:4].isdigit() else yrs[-1] - 1   # 마지막 「다 찬 해」
        pre, post = [last - 4, last - 3, last - 2], [last - 1, last]
        iy = lambda y: 1 + yrs.index(y)
        ic = lambda y: 1 + len(yrs) + yrs.index(y)
        n0 = 1 + 2 * len(yrs)   # 1년 대상 자리
        nm = {}
        try:
            for e in load(os.path.join(d, 'dong.json'))['dong']:
                nm[e['k']] = e['name']
        except Exception:
            pass
        si = None
        if os.path.exists(os.path.join(d, 'storind.json')):
            si = load(os.path.join(d, 'storind.json'))
        gs = {}
        for dk, row in b['dong'].items():
            for c, v in row.items():
                g = gs.setdefault(c, [0, 0]); g[0] += v[n0]; g[1] += v[n0 + 1]
        G = {'gu': gu, 'name': '', 'dong': {}}
        for dk, row in b['dong'].items():
            out, quiet = [], 0
            for c, v in row.items():
                tot['동×업종'] += 1
                po = sum(v[iy(y)] for y in pre)
                if po < P['min_open_pre'] or v[0] < P['min_now']:
                    quiet += 1; continue
                pa = sum(v[iy(y)] for y in post)
                r = (pa / len(post)) / (po / len(pre))
                f = 0
                if r >= P['up']: f |= 1
                if r <= P['down']: f |= 2
                if all(v[ic(y)] > v[iy(y)] for y in post[-P['close_years']:]): f |= 4
                s1 = v[n0 + 1] / v[n0] if v[n0] >= P['surv_min_n'] else None
                g = gs[c][1] / gs[c][0] if gs[c][0] else None
                if s1 is not None and g is not None and s1 < g - P['surv_gap']: f |= 8
                if not f:
                    continue
                cat = cats[int(c)]
                sv = None
                if si and dk in si.get('dong', {}) and svc_of.get(cat):
                    rows = [x for x in si['dong'][dk] if x[0] in svc_of[cat]]
                    if rows:
                        sv = [sum(x[1] for x in rows), sum(x[2] for x in rows), sum(x[3] for x in rows), '+'.join(x[0] for x in rows), 'eq' if all(rr == 'eq' for rr in rel_of[cat]) else 'diff']
                out.append([int(c), v[0], round(po / len(pre), 1), round(pa / len(post), 1),
                            [v[ic(y)] for y in post], [v[iy(y)] for y in post],
                            None if s1 is None else round(s1 * 100), None if g is None else round(g * 100), f, sv])
                tot['신호'] += 1
                for k in FLAG:
                    if f & k: tot[FLAG[k]] += 1
            tot['적어서 말하지 않음'] += quiet
            if out or redev.get(dk):
                G['dong'][dk] = {'n': nm.get(dk, ''), 'quiet': quiet, 'rows': sorted(out, key=lambda x: -x[1]), 'redev': redev.get(dk) or None}
        if si:
            G['svc_q'] = [si.get('qL', ''), si.get('last4', [])]
        by_sido[gu[:2]][gu] = G
    os.makedirs(OUTD, exist_ok=True)
    made = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    idx = {}
    for sd, G in sorted(by_sido.items()):
        doc = {'schema': 'tg-esig/1', 'made': made, 'sido': sd,
               'source': '행정안전부 지방행정인허가(LOCALDATA) 개업·폐업(r/<구>/bizsv.json · 판 ' + ','.join(sorted(asof_all)) + ') · 서울시 상권분석서비스 점포-행정동 분기 개업·폐업(r/<구>/storind.json · 서울만) · 업종 맞댐 data/ind-dict.json(등급 C) · 입주 예정 data/redev.json(손 목록)',
               'params': P, 'flags': {str(k): v for k, v in FLAG.items()}, 'cats': dic['keys'],
               'fields': 'gu{시군구 5자리: {dong{행정동 8자리: {n 이름, quiet 적어서 말하지 않은 업종 수, rows[[업종 번호(cats), 지금 영업, 앞 3해 해 평균 개업, 뒤 2해 해 평균 개업, [폐업 뒤 2해], [개업 뒤 2해], 1년 생존 %|null, 구의 같은 업종 1년 생존 %|null, 신호 비트(flags), 서울 상권분석 [지금 점포, 최근 4분기 개업, 최근 4분기 폐업, 맞댄 업종 이름, eq|diff(범위가 다름)]|null]], redev[[단지, 입주 예정 달, 세대]]|null}}, svc_q[마지막 분기, 최근 4분기]}} · 앞 3해·뒤 2해 = 기준 판 해의 바로 앞 해까지(반쪽 해는 쓰지 않는다)',
               'note': ['**조기 신호이지 예언이 아니다** — 개업이 늘어난 것은 경쟁이 늘어난 것일 수도 있고, 폐업이 많은 것은 재건축 철거일 수도 있다(redev 를 같이 본다) · 신호끼리 더한 점수는 없다',
                        '인허가 30업종만이다(사무실·소매 대부분은 안 잡힌다) · 좌표 없는 가게는 빠졌다 · 큰 시설 안 식품관·팝업은 「드나듦이 잦음」으로 잡힐 수 있다 — 큰 점포 자리 자료가 아직 없다(ONTOLOGY-3-활용.md ③ 함정 1)',
                        '서울 상권분석 값은 업종 범위가 인허가와 다를 수 있다(diff) — 나란히 보기만 하고 빼거나 더하지 않는다',
                        '쓰지 않는 말: 유망 · 추천 · 투자 · 기회'],
               'gu': G}
        p = os.path.join(OUTD, sd + '.json')
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(doc, f, ensure_ascii=False, separators=(',', ':'))
        idx[sd] = [len(G), sum(len(g['dong']) for g in G.values()), os.path.getsize(p)]
    with open(os.path.join(OUTD, 'index.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema': 'tg-esig-index/1', 'made': made, 'source': 'data/esig/<시도>.json 의 목록', 'fields': 'sido{시도 2자리: [시군구 수, 신호·입주 예정이 있는 동 수, 바이트]}', 'note': ['tools/onto/esig-bake.py'], 'params': P, 'count': dict(tot), 'sido': idx}, f, ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(gus), '· 시도', len(idx), '·', dict(tot))
    for sd, v in sorted(idx.items()):
        print(' ', sd, v)


if __name__ == '__main__':
    main()
