# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏪 상권 지금 진단 둘째 판(소유자 마스터 문서 8장 · 8.7 「잰 값 그대로, 판단은 보는 사람에게」 · 2026-10-11 보강 다섯) → data/trade-diag2-seoul.json
#   첫 판(tradediag-bake.py → trade-diag-seoul.json)은 지도가 읽고 있어 그대로 둔다 — 꼴이 달라 새 파일로 낸다(지도가 이 파일로 옮기면 첫 판을 지운다)
#   재료 = data/r/<서울 구>/trdar.json(서울시 상권분석서비스 · 서울 열린데이터광장 — 이번 분기와 1년 전 같은 분기)
#        + 1년 전 같은 분기의 길단위 유동인구(VwsmTrdarFlpopQq — 이 도구가 한 번 받아 07_API키/out/seoul_trdar/flpop_<분기>.json 에 둔다 · 키 keys.json seoul)
#   보강 다섯(소유자 문서의 지적 그대로):
#     ① 신호가 같은 현상을 여러 번 세지 않게 — **공급 쪽**(매출·점포·폐업)과 **수요 쪽**(유동인구)을 갈라 싣는다 → 「사람이 안 오는가 / 와도 안 사는가」
#     ② 폐업은 절대 수가 아니라 **폐업률**(폐업 ÷ 점포)로
#     ③ **서울 전체와 견준 값** — 서울 상권의 분포에서 얼마나 낮은가(불황이면 다 떨어진다)
#     ④ 순위를 매기지 않는다 — 파일은 상권 코드 차례(「가장 나쁜 상권」 목록을 만들지 않는다 · 이름을 쇠퇴 프레임으로 찍지 않게)
#     ⑤ **업종 분해** — 무엇이 빠지는가(매출이 가장 많이 준 업종 · 점포가 가장 많이 준 업종)
#   신호(해당 목록 · 한 점수로 뭉치지 않는다 · 문턱은 **이번 분기 서울 상권 전체의 분포**에서 — 아래 사분위 = 서울 상권 넷 가운데 가장 낮은 하나):
#     S1 매출 변화가 아래 사분위보다 낮다 · S2 점포 변화가 아래 사분위보다 낮다 · S3 폐업률이 위 사분위보다 높고 개업률보다 높다 · S4 상권변화지표 「상권축소」(서울시가 매긴 값) · D1 유동인구 변화가 아래 사분위보다 낮다(수요 쪽)
#   py -3.12 -X utf8 tools/region/tradediag2-bake.py
import json, os, glob, time, datetime, collections, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'seoul_trdar')
def flpop(q):
    p = os.path.join(OUT, 'flpop_%s.json' % q)
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['seoul']; d = {}; st = 1
    while True:
        u = 'http://openapi.seoul.go.kr:8088/%s/json/VwsmTrdarFlpopQq/%d/%d/%s' % (K, st, st + 999, q)
        v = json.loads(urllib.request.urlopen(u, timeout=60).read().decode('utf-8', 'replace')).get('VwsmTrdarFlpopQq') or {}; rr = v.get('row') or []
        for r in rr:
            if r.get('STDR_YYQU_CD') == q: d[str(r['TRDAR_CD'])] = float(r.get('TOT_FLPOP_CO') or 0)
        st += 1000
        if st > (v.get('list_total_count') or 0) or not rr: break
        time.sleep(0.2)
    json.dump(d, open(p, 'w', encoding='utf-8')); return d
def quart(v, f):
    v = sorted(x for x in v if x is not None); return v[int((len(v) - 1) * f)] if v else None
def main():
    T = []; q = prev = src = ''
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'trdar.json'))):
        t = json.load(open(f, encoding='utf-8')); q = t.get('quarter', q); prev = t.get('prev', prev); src = t.get('source', src); T += t['trdar']
    try: FP = flpop(prev)
    except Exception as e: FP = {}; print('1년 전 유동인구를 못 받음', type(e).__name__)
    pc = lambda a, b: round((a / b - 1) * 100, 1) if a and b else None
    R = []
    for x in T:
        ind = {r[0]: (r[1] or 0) for r in x.get('ind', [])}; indp = {k: (v[0] or 0) for k, v in (x.get('indp') or {}).items()}; stor = {r[0]: r for r in x.get('stor', [])}; storp = x.get('storp') or {}
        now = sum(ind.values()); old = sum(indp.values()); sn = sum(r[1] or 0 for r in stor.values()); so = sum(v or 0 for v in storp.values()); op = sum(r[3] or 0 for r in stor.values()); cl = sum(r[4] or 0 for r in stor.values())
        ix = x.get('ix') or [None] * 5; fl = (x.get('flp') or [None])[0]; fo = FP.get(str(x['cd'])); tr = (x.get('tr') or {}).get(q)
        same = [k for k, v in indp.items() if v and k in ind and ind[k]]   # 두 분기에 다 값이 있는 업종
        dsal = sorted(((ind[k] - indp[k], k) for k in same), key=lambda z: z[0])[:3]
        dsto = sorted((((stor[k][1] or 0) - v, k) for k, v in storp.items() if v and k in stor), key=lambda z: z[0])[:3]
        usal = sorted(((ind[k] - indp[k], k) for k in same), key=lambda z: -z[0])[:3]   # 느는 업종(게임 세션 2026-10-11 — 소유자 A-2 「빠지는 업종 / 느는 업종」)
        usto = sorted((((stor[k][1] or 0) - v, k) for k, v in storp.items() if v and k in stor), key=lambda z: -z[0])[:3]
        miss = [k for k, v in indp.items() if v and not ind.get(k)]   # 1년 전에는 매출이 있었는데 이번 분기에 값이 없는 업종(가게가 적으면 가려진다)
        c = x['rings'][0]
        R.append({'cd': x['cd'], 'nm': x['name'], 'se': x.get('se', ''), 'gu': x.get('gu', ''), 'dong': x.get('dong', ''), 'll': [round(sum(p[0] for p in c) / len(c), 5), round(sum(p[1] for p in c) / len(c), 5)],
                  'sal': round(now), 'sy': pc(sum(ind[k] for k in same), sum(indp[k] for k in same)), 'sy_all': pc(now, old), 'miss': len(miss), 'sn': sn, 'ty': pc(sn, so), 'op': op, 'cl': cl,
                  'clr': round(cl / sn * 100, 1) if sn else None, 'opr': round(op / sn * 100, 1) if sn else None, 'ix': ix[0], 'om': ix[1], 'cm': ix[2], 'fl': fl, 'fy': pc(fl, fo), 'night': round(tr[2] / tr[0] * 100) if tr and tr[0] else None,
                  'dsal': [[k, round(v)] for v, k in dsal if v < 0], 'dsto': [[k, v] for v, k in dsto if v < 0], 'usal': [[k, round(v)] for v, k in usal if v > 0], 'usto': [[k, v] for v, k in usto if v > 0]})
    Q = {k: [quart([r[k] for r in R], f) for f in (0.25, 0.5, 0.75)] for k in ('sy', 'ty', 'clr', 'fy')}
    items = []; st = collections.Counter()
    for r in R:
        S = []
        if r['sy'] is not None and r['sy'] < Q['sy'][0]: S.append('S1')
        if r['ty'] is not None and r['ty'] < Q['ty'][0]: S.append('S2')
        if r['clr'] is not None and r['sn'] >= 30 and r['clr'] > Q['clr'][2] and r['clr'] > (r['opr'] or 0): S.append('S3')   # 점포 30곳 안 되는 상권은 한두 곳 폐업으로 비율이 튄다
        if r['ix'] in ('HL', '상권축소'): S.append('S4')
        if r['fy'] is not None and Q['fy'][0] is not None and r['fy'] < Q['fy'][0]: S.append('D1')
        sup = [s for s in S if s[0] == 'S']; dem = 'D1' in S
        kind = 0 if not S else (3 if sup and dem else (1 if sup else 2))   # 1 = 가게 쪽만(사람은 그대로 — 와도 덜 산다·가게가 빠진다) · 2 = 사람 쪽만 · 3 = 둘 다
        items.append([r['cd'], r['nm'], r['se'], r['gu'], r['dong'], r['ll'][0], r['ll'][1], r['sal'], r['sy'], None if r['sy'] is None or Q['sy'][1] is None else round(r['sy'] - Q['sy'][1], 1), r['sy_all'], r['miss'],
                      r['sn'], r['ty'], r['op'], r['cl'], r['opr'], r['clr'], r['fl'], r['fy'], r['ix'], r['om'], r['cm'], r['night'], S, kind, r['dsal'], r['dsto'], r['usal'], r['usto']])
        st['신호 %d개' % len(S)] += 1; st['갈래 %d' % kind] += 1
        for s in S: st[s] += 1
    items.sort(key=lambda r: str(r[0]))
    doc = {'schema': 'tg-trade-diag/2', 'made': datetime.date.today().isoformat(), 'quarter': q, 'prev': prev, 'area': '서울 25구의 상권(서울시 상권분석서비스 영역-상권)',
           'source': src + ' — data/r/<구>/trdar.json 을 다시 읽어 견준 것 · 1년 전 유동인구는 같은 서비스의 길단위유동인구(VwsmTrdarFlpopQq)',
           'seoul': {'sy 매출 변화 %(아래 사분위·가운데·위 사분위)': Q['sy'], 'ty 점포 변화 %': Q['ty'], 'clr 폐업률 %': Q['clr'], 'fy 유동인구 변화 %': Q['fy']},
           'signals': {'S1': '매출 변화가 서울 상권의 아래 사분위(%s%%)보다 낮다' % Q['sy'][0], 'S2': '점포 변화가 서울 상권의 아래 사분위(%s%%)보다 낮다' % Q['ty'][0], 'S3': '폐업률이 서울 상권의 위 사분위(%s%%)보다 높고 개업률보다 높다(점포 30곳 이상인 상권만)' % Q['clr'][2], 'S4': '상권변화지표가 「상권축소」다(서울시가 매긴 값)', 'D1': '유동인구 변화가 서울 상권의 아래 사분위(%s%%)보다 낮다(수요 쪽)' % Q['fy'][0]},
           'kinds': {'0': '신호 없음', '1': '가게 쪽만 — 사람은 그대로인데 매출·가게가 준다(와도 덜 산다 · 가게가 빠진다)', '2': '사람 쪽만 — 사람이 준다(가게 쪽 신호는 아직 없다)', '3': '둘 다 — 사람도 줄고 가게도 준다'},
           'signal_rule': 'S = 공급 쪽(매출·점포·폐업 — 같은 쇠퇴를 다른 각도에서 잰 것이라 서로 겹친다 · 넷을 따로 센 개수에 큰 뜻을 두지 않는다) · D = 수요 쪽(사람이 오는가). 문턱은 정한 숫자가 아니라 **이번 분기 서울 상권 전체의 분포**(사분위)에서 잡는다 — 불황으로 다 같이 떨어진 것은 신호가 되지 않는다. 사분위를 문턱으로 삼은 것은 이 지도의 선택이다(공식 기준이 아니다)',
           'note': ['**예언이 아니라 조기 신호다** — 「이 상권이 진다」가 아니라 「이런 사실이 겹쳐 있다」다. 무게를 매겨 한 점수로 뭉치지 않았고 순위를 매기지 않는다(파일은 상권 코드 차례)',
                    '이번 분기와 1년 전 같은 분기 둘만 견줬다 — 한 해의 출렁임(공사·행사·날씨)일 수 있다. 흐름은 분기 자료가 쌓여야 본다',
                    '매출 변화는 **두 분기에 다 값이 있는 업종끼리만** 견줬다 — 1년 전에는 있었는데 이번에 값이 없는 업종(가게가 적으면 가려진다)을 「0 으로 줄었다」로 세지 않으려고. 빠진 업종 수와, 다 넣어 견준 값도 따로 싣는다',
                    '폐업률 = 이번 분기 폐업 ÷ 점포 · 개업률 = 개업 ÷ 점포 · 매출은 카드 결제 추정(현금 제외 · 한 달 평균 만원)',
                    '「무엇이 빠지나」 = 매출·점포가 가장 많이 준 업종 셋(준 것만 · 업종 코드는 서울시 상권분석서비스의 서비스 업종 코드 — 이름은 data/r/bizidx.json)',
                    '「왜」는 이 자료에 없다(재개발·공사·큰 가게의 이전·새 상권) — 현장을 아는 사람이 가설을 붙일 자리다',
                    '사고팔기·창업을 권하거나 말리는 자료가 아니다. 상권 이름을 「지는 상권」으로 찍지 않는다 — 잰 값만 보인다'],
           'fields': 'items[[0 상권 코드, 1 이름, 2 갈래, 3 구 코드, 4 행정동, 5 가운데 경도, 6 위도, 7 한 달 평균 매출 만원, 8 매출 변화 %(두 분기에 다 있는 업종끼리), 9 그 값 − 서울 가운데값(%p), 10 매출 변화 %(빠진 업종까지 다 넣어), 11 이번 분기에 값이 빠진 업종 수, 12 점포 수, 13 점포 변화 %, 14 개업, 15 폐업, 16 개업률 %, 17 폐업률 %, 18 분기 유동인구, 19 유동인구 변화 %, 20 상권변화지표, 21 운영 가게 평균 영업 개월, 22 폐업 가게 평균 영업 개월, 23 밤(21~06시) 매출 %, 24 신호[S1·S2·S3·S4·D1 가운데 해당하는 것], 25 풀이 갈래(kinds), 26 매출이 준 업종[[업종 코드, 만원]…], 27 점포가 준 업종[[업종 코드, 곳]…], 28 매출이 는 업종[[업종 코드, 만원]…](두 분기에 다 값이 있는 업종 가운데 · 많이 는 차례 셋까지), 29 점포가 는 업종[[업종 코드, 곳]…]]] — 상권 코드 차례',
           'stat': dict(st), 'items': items}
    p = os.path.join(ROOT, 'data', 'trade-diag2-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('분기', q, '← 1년 전', prev, '· 상권', len(items), '· 1년 전 유동인구 받은 상권', len(FP), '· 바이트', os.path.getsize(p)); print('서울 분포', doc['seoul']); print({k: v for k, v in sorted(st.items())})
    for r in items:
        if r[1] in ('장안제일시장', '청평화시장', '양재화물트럭터미널앞'): print(' ', r[1], '· 매출', r[8], '%(서울 가운데값보다', r[9], '%p · 다 넣으면', r[10], '· 빠진 업종', r[11], ') · 점포', r[13], '% · 개업률', r[16], '폐업률', r[17], '· 유동', r[19], '% ·', r[24], '갈래', r[25], '· 준 업종', r[26], r[27])
if __name__ == '__main__': main()
