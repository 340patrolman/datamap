# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏪 상권 지금 진단(소유자 마스터 문서 8장 · 2026-10-11 「단계 A = 현재 진단 — 있는 데이터로 오늘도 만들 수 있다」 · 상권 생애주기 · 얼리워닝) → data/trade-diag-seoul.json
#   재료 = 이미 구운 data/r/<서울 구>/trdar.json(서울시 상권분석서비스 · 서울 열린데이터광장 — 추정매출·점포·개업·폐업·유동인구·상권변화지표 · 이번 분기와 1년 전 같은 분기) 하나뿐
#   상권마다 **재어서 나온 사실만** 싣는다: 매출이 1년 전보다 몇 % · 점포 수 변화 · 개업과 폐업 · 상권변화지표(서울시가 매긴 네 갈래) · 운영·폐업한 가게의 평균 영업 개월(서울 평균과 견줌) · 밤 매출 비중
#   「조기 신호」 = 아래 넷 가운데 해당하는 것의 **목록**(개수) — 무게를 매겨 한 점수로 뭉치지 않는다(무게를 지어내지 않는다):
#     ① 매출이 1년 전보다 10% 넘게 줄었다 ② 점포 수가 3% 넘게 줄었다 ③ 폐업이 3곳 이상이고 개업의 1.5배 이상 ④ 상권변화지표가 「상권축소」 — 문턱은 이 지도가 정한 기준(공식 아님)
#   **예언이 아니라 조기 신호다**(소유자 원칙) · 두 분기를 견준 것이라 한 해의 출렁임일 수 있다 · 매출은 카드 결제 추정(현금 제외) · 투자·창업을 권하거나 말리는 자료가 아니다
#   py -3.12 -X utf8 tools/region/tradediag-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IX = {'LL': '다이나믹(새 가게도 오래된 가게도 빨리 바뀐다)', 'LH': '상권확장(새 가게가 살아남는다)', 'HL': '상권축소(새 가게가 못 버틴다)', 'HH': '정체(오래된 가게가 자리를 지킨다)'}
def main():
    rows = []; q = prev = src = ''; st = collections.Counter()
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'trdar.json'))):
        t = json.load(open(f, encoding='utf-8')); q = t.get('quarter', q); prev = t.get('prev', prev); src = t.get('source', src)
        for x in t['trdar']:
            now = sum(r[1] or 0 for r in x.get('ind', [])); old = sum((v[0] or 0) for v in (x.get('indp') or {}).values())
            sn = sum(r[1] or 0 for r in x.get('stor', [])); so = sum(v or 0 for v in (x.get('storp') or {}).values()); op = sum(r[3] or 0 for r in x.get('stor', [])); cl = sum(r[4] or 0 for r in x.get('stor', []))
            ix = x.get('ix') or [None] * 5; fl = (x.get('flp') or [None])[0]; tr = (x.get('tr') or {}).get(q)
            sy = round((now / old - 1) * 100, 1) if old and now else None; ty = round((sn / so - 1) * 100, 1) if so and sn else None
            sig = []
            if sy is not None and sy <= -10: sig.append(1)
            if ty is not None and ty <= -3: sig.append(2)
            if cl >= 3 and cl >= op * 1.5: sig.append(3)
            if ix[0] in ('HL', '상권축소'): sig.append(4)
            c = x['rings'][0]; cx = sum(p[0] for p in c) / len(c); cy = sum(p[1] for p in c) / len(c)
            rows.append([x['cd'], x['name'], x.get('se', ''), x.get('gu', ''), x.get('dong', ''), round(cx, 5), round(cy, 5), round(now), sy, sn, ty, op, cl, ix[0], ix[1], ix[2], fl, round(tr[2] / tr[0] * 100) if tr and tr[0] else None, sig])
            st['상권'] += 1; st['신호 %d개' % len(sig)] += 1
            for s in sig: st['신호 ' + str(s)] += 1
    rows.sort(key=lambda r: (-len(r[18]), r[8] if r[8] is not None else 0))
    doc = {'schema': 'tg-trade-diag/1', 'made': datetime.date.today().isoformat(), 'quarter': q, 'prev': prev, 'area': '서울 25구의 상권(서울시 상권분석서비스 영역-상권)',
           'source': src + ' — data/r/<구>/trdar.json 을 다시 읽어 견준 것',
           'signals': {'1': '매출이 1년 전 같은 분기보다 10% 넘게 줄었다', '2': '점포 수가 1년 전보다 3% 넘게 줄었다', '3': '이번 분기에 폐업이 3곳 이상이고 개업의 1.5배 이상이다', '4': '상권변화지표가 「상권축소」다(서울시가 매긴 값)'},
           'signal_rule': '문턱(10% · 3% · 3곳·1.5배)은 **이 지도가 정한 기준**이다(공식 기준이 아니다) — 처음에는 「줄었다」「폐업이 더 많다」로만 봤더니 서울 상권의 절반 넘게가 걸려 가르는 힘이 없었다(2026-10-11) · 「폐업 가게의 영업 개월이 서울 평균보다 짧다」는 정의상 절반이 걸려 뺐다',
           'ix': IX,
           'note': ['**예언이 아니라 조기 신호다** — 「이 상권이 진다」가 아니라 「이런 사실이 겹쳐 있다」다. 조기 신호 칸은 해당하는 신호의 번호 목록이고, 무게를 매겨 한 점수로 뭉치지 않았다',
                    '이번 분기와 1년 전 같은 분기 둘만 견줬다 — 한 해의 출렁임(공사·행사·날씨)일 수 있다. 흐름(여러 분기)은 분기 자료가 쌓여야 본다',
                    '매출은 카드사 결제 자료로 추정한 값(현금 제외 · 한 달 평균으로 실음) · 상권 영역이 바뀌면 1년 전과 견줌이 틀어진다',
                    '상권변화지표의 네 갈래 이름과 뜻은 서울시 상권분석서비스의 것이다(괄호 풀이는 이 지도가 붙인 것)',
                    '매출이 50% 넘게 줄었다고 나오는 상권은 실제 쇠퇴보다 **자료가 빠진 것**(업종 매출이 이번 분기에 공개되지 않음 — 점포 수가 적으면 가려진다)일 수 있다 — 그대로 믿지 말고 점포·개폐업과 같이 본다',
                    '투자·창업을 권하거나 말리는 자료가 아니다 — 판단은 현장을 본 사람이 한다'],
           'fields': 'items[[상권 코드, 이름, 갈래(골목상권·발달상권·전통시장·관광특구), 구 코드, 행정동, 가운데 경도, 위도, 한 달 평균 매출 만원, 매출 1년 전보다 %, 점포 수, 점포 1년 전보다 %, 개업, 폐업, 상권변화지표, 운영 가게 평균 영업 개월, 폐업 가게 평균 영업 개월, 분기 유동인구, 밤(21~06시) 매출 %, 조기 신호[번호…]]] — 신호가 많은 차례',
           'stat': dict(st), 'items': rows}
    p = os.path.join(ROOT, 'data', 'trade-diag-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('분기', q, '← 1년 전', prev, '· 상권', len(rows), '· 바이트', os.path.getsize(p)); print({k: v for k, v in sorted(st.items())})
    print('신호가 가장 많은 상권:'); [print('  ', r[1], r[2], r[4], '· 매출', r[8], '% · 점포', r[10], '% · 개업', r[11], '폐업', r[12], '·', r[13], '· 신호', r[18]) for r in rows[:10]]
    seo = [r for r in rows if r[3] == '11650']; print('서초구', len(seo), '· 신호 3개 이상', [(r[1], r[8], r[18]) for r in seo if len(r[18]) >= 3][:10])
if __name__ == '__main__': main()
