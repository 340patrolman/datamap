# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌙 느린 변수와 빠른 변수: 주점·유흥 매출 비중과 밤 매출 비중의 분기 흐름(소유자 마스터 문서 7.8 · 2026-10-11 「세대는 느린 변수, 사건은 빠른 변수」
#   「음주단속 지점 선정의 전제가 바뀌었다」 · ONTOLOGY.md §0) → data/night-trend-seoul.json
#   재료 = 이미 구운 data/r/<서울 구>/trdar.json 의 tr{분기: [매출, 주점·유흥 매출, 밤(21~24 + 0~6) 매출]}(서울시 상권분석서비스 추정매출 · 2021년 1분기부터) 와 이번 분기 업종별 연령·시간대 매출
#   싣는 것 = **잰 값만**: 서울·구·상권마다 분기별 「주점·유흥 매출 ÷ 모든 매출」「밤 매출 ÷ 모든 매출」 · 호프·간이주점 매출의 연령대 구성과 시간대 구성(이번 분기)
#   「왜 줄었나」(세대 · 회식 문화 · 물가)는 이 자료에 없다 — 방향과 크기만 잰다. 2021년~2022년 1분기는 영업시간·모임 제한이 있던 때라 밤 매출이 눌려 있다(빠른 변수) — 느린 흐름은 2022년 2분기부터 본다
#   py -3.12 -X utf8 tools/region/nighttrend-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def sh(a, i): return round(a[i] / a[0] * 100, 2) if a[0] else None
def main():
    S = collections.defaultdict(lambda: [0, 0, 0]); G = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0])); gname = {}; rows = []; q = src = ''
    age = [0] * 6; tm = [0] * 6; ageall = [0] * 6; tmall = [0] * 6
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'trdar.json'))):
        t = json.load(open(f, encoding='utf-8')); q = t.get('quarter', q); src = t.get('source', src)
        for x in t['trdar']:
            tr = x.get('tr') or {}; gname[x.get('gu', '')] = x.get('guName', '')
            for k, v in tr.items():
                for i in range(3): S[k][i] += v[i] or 0; G[x.get('gu', '')][k][i] += v[i] or 0
            for r in x.get('ind', []):
                if len(r) < 15: continue
                for i in range(6): ageall[i] += r[9 + i] or 0; tmall[i] += r[3 + i] or 0
                if r[0] == '호프-간이주점':
                    for i in range(6): age[i] += r[9 + i] or 0; tm[i] += r[3 + i] or 0
            c = x['rings'][0]; yrs = [k for k in sorted(tr) if k.endswith(q[-1]) and k >= '2022' + q[-1]]   # 같은 분기끼리(철을 맞춘다) · 2022년부터
            rows.append([x['cd'], x['name'], x.get('se', ''), x.get('gu', ''), x.get('dong', ''), round(sum(p[0] for p in c) / len(c), 5), round(sum(p[1] for p in c) / len(c), 5),
                         [sh(tr[k], 1) for k in yrs], [sh(tr[k], 2) for k in yrs], round(tr[q][1]) if q in tr else None, round(tr[q][0]) if q in tr else None])
    qs = sorted(S); yq = [k for k in qs if k.endswith(q[-1]) and k >= '2022' + q[-1]]
    pct = lambda a: [round(v / sum(a) * 100, 1) for v in a] if sum(a) else []
    doc = {'schema': 'tg-night-trend/1', 'made': datetime.date.today().isoformat(), 'quarter': q, 'area': '서울 25구의 상권(서울시 상권분석서비스 영역-상권 · 상권 영역 밖의 가게는 들어 있지 않다)',
           'source': src + ' — data/r/<구>/trdar.json 의 분기 매출(tr)과 이번 분기 업종별 연령·시간대 매출을 다시 더한 것',
           'chain': '바깥 충격(빠른 변수) · 세대 교체(느린 변수) → 구성원의 행태(회식·음주) → 상권(주점·유흥 · 밤 매출) → 단속·순찰의 전제 — ONTOLOGY.md §0 「느린 변수와 빠른 변수」',
           'note': ['**잰 값만 실었다** — 주점·유흥과 밤 매출의 「비중」이 어느 쪽으로 얼마나 움직였는가. 왜 그런지(세대 · 회식 문화 · 물가 · 배달)는 이 자료로 알 수 없다',
                    '2021년 ~ 2022년 1분기는 영업시간·모임 제한이 있던 때라 밤 매출과 주점 매출이 눌려 있다(빠른 변수) — 그 뒤의 흐름(느린 변수)은 2022년 2분기부터 본다 · 상권마다의 줄(y)은 그래서 2022년부터 같은 분기끼리만 실었다',
                    '매출은 카드 결제로 추정한 값(현금 제외 · 한 달 평균) · 「주점·유흥」은 서울시 상권분석서비스의 업종 갈래를 더한 것 · 밤 = 21~24시 + 0~6시',
                    '상권 하나의 비중은 가게가 적으면 한두 곳의 개·폐업에 크게 흔들린다 — 상권 값은 서울·구의 흐름과 같이 본다',
                    '주점 매출이 주는 것이 음주운전이 주는 것을 뜻하지는 않는다(집·다른 곳에서 마실 수 있다) — 단속 지점을 다시 보는 **재료**이고 답은 현장이 낸다',
                    '투자·창업을 권하거나 말리는 자료가 아니다'],
           'fields': {'seoul': '[[분기 YYYYQ, 한 달 평균 매출 억원, 주점·유흥 비중 %, 밤 비중 %]…] 2021년 1분기부터', 'gu': '{구 코드: [구 이름, [분기마다 주점·유흥 비중 %], [분기마다 밤 비중 %]]} — 분기 차례는 seoul 과 같다',
                      'hof': '호프·간이주점 매출의 구성 %(이번 분기 · 서울) — age = 10대·20대·30대·40대·50대·60대 이상 / time = 0~6·6~11·11~14·14~17·17~21·21~24시 · all_* = 모든 업종의 같은 구성(견줌)',
                      'yq': '상권 줄의 해들(같은 분기)', 'items': '[[상권 코드, 이름, 갈래, 구 코드, 행정동, 가운데 경도, 위도, [해마다 주점·유흥 비중 %], [해마다 밤 비중 %], 이번 분기 주점·유흥 한 달 매출 만원, 이번 분기 모든 매출 만원]] — 상권 코드 차례'},
           'seoul': [[k, round(S[k][0] / 1e4), sh(S[k], 1), sh(S[k], 2)] for k in qs],
           'gu': {g: [gname.get(g, ''), [sh(v[k], 1) if k in v else None for k in qs], [sh(v[k], 2) if k in v else None for k in qs]] for g, v in sorted(G.items())},
           'hof': {'age': pct(age), 'time': pct(tm), 'all_age': pct(ageall), 'all_time': pct(tmall)}, 'yq': yq, 'items': sorted(rows)}
    p = os.path.join(ROOT, 'data', 'night-trend-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('분기', qs[0], '~', qs[-1], '· 상권', len(rows), '· 바이트', os.path.getsize(p)); print('같은 분기:', [(k, sh(S[k], 1), sh(S[k], 2)) for k in yq])
    i0 = qs.index(yq[0]); i1 = qs.index(yq[-1])
    print('구별 주점·유흥 비중', yq[0], '→', yq[-1], ':'); [print('   %-5s %5.2f → %5.2f (%+.2f%%p) · 밤 %5.2f → %5.2f' % (v[0], v[1][i0], v[1][i1], v[1][i1] - v[1][i0], v[2][i0], v[2][i1])) for g, v in sorted(doc['gu'].items(), key=lambda kv: kv[1][1][i1] - kv[1][1][i0]) if v[1][i0] is not None and v[1][i1] is not None]
    print('호프 매출 구성', doc['hof'])
if __name__ == '__main__': main()
