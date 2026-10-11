# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧩 완료된 사건을 뒤돌아 맞대 보기(소유자 2026-10-11 「완료 = 사후 검증 · 다음 예측의 학습 자료」 · ONTOLOGY.md Object 11) → data/event-check.json
#   사건이 있던 구의 아파트 매매 실거래를 2016년부터 반기마다, **법정동의 ㎡당 중앙값 ÷ 그 구 전체의 ㎡당 중앙값**(둘레가 구 전체보다 더 올랐나)으로 본다
#   재료 = ../07_API키/out/home_hist/<구>_<연월>.json(tools/story/eventcheck-fetch.py — 국토교통부 아파트 매매 실거래가 · 해제된 거래 제외 · 전용면적 기준)
#   **「사건 때문에 올랐다」를 말하지 않는다** — 앞뒤로 얼마나 달랐나만 싣는다. 같은 때 금리·경기·새 단지 입주가 같이 움직였고, 동의 중앙값은 「그 반기에 어느 단지가 팔렸나」에 크게 흔들린다
#   py -3.12 -X utf8 tools/story/eventcheck-bake.py
import json, os, glob, statistics, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); H = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'home_hist')
GUS = {'11650': ['서초구', ['EV-jeongbosa-move', 'EV-seoripul-tunnel']], '11170': ['용산구', ['EV-yongsan-usfk-move', 'EV-yongsan-park', 'EV-yongsan-ibd']]}
NEAR = {'EV-seoripul-tunnel': ['방배동', '서초동'], 'EV-jeongbosa-move': ['방배동', '서초동'], 'EV-yongsan-usfk-move': ['한강로3가', '이촌동', '이태원동', '용산동5가', '서빙고동', '한남동'], 'EV-yongsan-park': ['한강로3가', '이촌동', '이태원동', '용산동5가', '서빙고동'], 'EV-yongsan-ibd': ['한강로3가', '이촌동']}
WIN = [('11650', 'EV-seoripul-tunnel', ('201707', '201903'), ('201905', '202012')), ('11170', 'EV-yongsan-usfk-move', ('201607', '201805'), ('201807', '202006')), ('11170', 'EV-yongsan-park', ('201907', '202112'), ('202207', '202408'))]
def same(gu, A, B):
    """같은 단지끼리 — 앞·뒤 두 때에 다 세 건 이상 팔린 단지의 (뒤 ㎡당 중앙값 ÷ 앞 ㎡당 중앙값)을 동마다 모은다(「어느 단지가 팔렸나」에 흔들리지 않게)"""
    C = collections.defaultdict(lambda: {'a': [], 'b': []})
    for f in sorted(glob.glob(os.path.join(H, gu + '_*.json'))):
        ym = os.path.basename(f)[6:12]; w = 'a' if A[0] <= ym <= A[1] else 'b' if B[0] <= ym <= B[1] else None
        if not w: continue
        for r in json.load(open(f, encoding='utf-8')):
            if not r[6] and r[2] > 0: C[(r[0], r[1], r[7])][w].append(r[3] / r[2])
    D = collections.defaultdict(list)
    for (dong, nm, jb), v in C.items():
        if len(v['a']) >= 3 and len(v['b']) >= 3: D[dong].append(statistics.median(v['b']) / statistics.median(v['a']))
    allr = sorted(x for v in D.values() for x in v)
    if not allr: return None
    g = statistics.median(allr)
    return {'before': list(A), 'after': list(B), 'n': len(allr), 'gu': round(g, 2), 'dong': {d: [len(v), round(statistics.median(v), 2), round(sorted(v)[len(v) // 4], 2), round(sorted(v)[len(v) * 3 // 4], 2), round((statistics.median(v) - g) * 100)] for d, v in sorted(D.items(), key=lambda kv: -len(kv[1])) if len(v) >= 4}}
def main():
    EV = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'data', 'events-big.json'), encoding='utf-8'))['items']}; out = {}
    for gu, (name, evs) in GUS.items():
        R = collections.defaultdict(lambda: collections.defaultdict(list)); months = set()
        for f in sorted(glob.glob(os.path.join(H, gu + '_*.json'))):
            ym = os.path.basename(f)[6:12]; months.add(ym); half = '%s-%d' % (ym[:4], 1 if int(ym[4:]) <= 6 else 2)
            for r in json.load(open(f, encoding='utf-8')):
                if r[6] or r[2] <= 0: continue
                v = r[3] / r[2]; R[r[0]][half].append(v); R['*'][half].append(v)
        hs = sorted(R['*']); dongs = sorted((d for d in R if d != '*' and sum(len(v) for v in R[d].values()) >= 250), key=lambda d: -sum(len(v) for v in R[d].values()))
        med = lambda d, h: round(statistics.median(R[d][h])) if len(R[d].get(h, [])) >= 5 else None
        out[gu] = {'name': name, 'months': [min(months), max(months)], 'halves': hs, 'gu': [[med('*', h), len(R['*'][h])] for h in hs],
                   'dong': {d: [[med(d, h), len(R[d].get(h, [])), (round(med(d, h) / med('*', h), 2) if med(d, h) and med('*', h) else None)] for h in hs] for d in dongs},
                   'events': [{'id': e, 'nm': EV[e]['nm'], 'state': EV[e]['state'], 'd_start': EV[e].get('d_start', ''), 'd_done': EV[e].get('d_done', ''), 'd_plan': EV[e].get('d_plan', ''), 'near': NEAR.get(e, [])} for e in evs if e in EV]}
        print(name, min(months), '~', max(months), '· 동', len(dongs), '· 거래', sum(len(R['*'][h]) for h in hs))
    SM = []
    for gu, ev, A, B in WIN:
        r = same(gu, A, B)
        if r: r.update({'gu_code': gu, 'event': ev, 'nm': EV[ev]['nm'] if ev in EV else ev}); SM.append(r); print(' 같은 단지끼리', r['nm'], '· 단지', r['n'], '· 구 ×', r['gu'], {d: v[4] for d, v in list(r['dong'].items())[:6]})
    doc = {'schema': 'tg-event-check/1', 'made': datetime.date.today().isoformat(),
           'source': '국토교통부 아파트 매매 실거래가(공공데이터포털 RTMSDataSvcAptTrade · 계약 연월 · 해제된 거래 제외 · 전용면적) — 사건은 data/events-big.json',
           'note': ['**「사건 때문에 올랐다·내렸다」를 말하는 자료가 아니다** — 사건 앞뒤로 그 동의 값이 구 전체에 견줘 얼마나 달랐나만 보인다. 같은 때 금리·경기·규제가 같이 움직였다',
                    '동의 중앙값은 「그 반기에 어느 단지가 팔렸나」에 크게 흔들린다(새 단지가 입주하면 그 동이 오른 것처럼 보인다) — 한 반기의 값이 아니라 여러 반기의 흐름으로 본다 · 거래가 5건 안 되는 반기는 null',
                    '비율 = 그 동의 ㎡당 중앙값 ÷ 그 구 전체의 ㎡당 중앙값(같은 반기) — 구 전체가 오르내린 몫을 덜어 낸 것이지 서울 전체·같은 조건의 다른 동과 견준 것이 아니다',
                    '2022년 하반기 ~ 2023년 상반기는 거래가 아주 적다(서초 2022년 628건) — 그때의 값은 믿지 않는다',
                    '같은 단지끼리(same) 본 것(2026-10-11): 서리풀터널 앞(2017-07~2019-03) → 뒤(2019-05~2020-12) 방배동 57단지 ×1.30 · 서초구 233단지 ×1.28 — **차이 +2%p 는 단지끼리의 벌어짐(사분위 1.18~1.39) 안**이라 터널의 자취로 볼 수 없다 · 용산 2022년 앞뒤 한강로3가 ×1.30(4단지뿐) · 이촌동 ×1.28(23단지) · 용산구 ×1.21 — 동 중앙값으로 보이던 「1.0 → 1.3」의 대부분은 새 단지가 섞인 탓이었다',
                    '2026-10-11 처음 본 것: 서리풀터널(2019-04 개통) 앞뒤로 방배동 ÷ 서초구는 0.76~0.90 사이를 오갈 뿐 뚜렷이 달라지지 않았다(이 자로는 가려지지 않는다) · 용산 한강로3가 ÷ 용산구는 2016~2021년 1.0 안팎에서 2022년 하반기부터 1.2~1.3 — 대통령 집무실 이전(2022-05) · 개발 구상 발표와 때가 겹치지만 거래가 적고(아홉 해 469건) 새 단지 입주가 섞여 까닭을 가릴 수 없다'],
           'fields': 'gu{구 코드: {name, months[처음, 끝 연월], halves[반기 「YYYY-1·2」…], gu[[구 전체 ㎡당 중앙값 만원, 거래 수]…], dong{법정동: [[㎡당 중앙값 만원, 거래 수, 구 전체에 견준 비율]…]}(거래 250건 이상인 동 · 반기 차례는 halves), events[{id, nm, state, d_plan, d_start, d_done, near[둘레 법정동]}]}} · same[{event, nm, gu_code, before[처음, 끝 연월], after[처음, 끝], n 두 때에 다 세 건 이상 팔린 단지 수, gu 구 전체 단지들의 (뒤 ÷ 앞) 가운데값, dong{법정동: [단지 수, (뒤 ÷ 앞) 가운데값, 아래 사분위, 위 사분위, 구 전체보다 %p]}}] — **같은 단지끼리** 견준 것(동 중앙값보다 믿을 만하다)',
           'gu': out, 'same': SM}
    p = os.path.join(ROOT, 'data', 'event-check.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('바이트', os.path.getsize(p))
if __name__ == '__main__': main()
