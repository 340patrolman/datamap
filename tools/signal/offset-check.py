# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 신호 옵셋의 기준 가리기(소유자 2026-10-10 「초가 바뀌면서 표시를 해줄 수 있나 · 스마트폰 시간·컴퓨터 시간과 맞을 거야」)
#   묻는 것: 신호계획의 옵셋(off)은 어느 시각을 0 으로 세나?  A = 자정 기준((하루 초 − off) ÷ 주기 의 나머지가 0 일 때 주기가 시작) · B = 그 계획이 시작한 시각 기준
#   재료(둘 다 이미 있는 파일 · 새로 받는 것 없음): data/sigdir-seoul.json(서울 T-Data — 기준 이동류 녹색이 **실제로 켜진 시각** a) × data/signal-tod-seoul.json(경찰청 교차로계획정보 — 요일·시각별 주기·옵셋)
#   같은 교차로 번호가 두 파일에 다 있고 받은 주기가 계획 주기와 같은 기록만 써서, 가설마다 「켜진 시각이 주기 시작에서 몇 초 어긋났나」를 잰다(±4초 안이면 맞음)
#   py -3.12 -X utf8 tools/signal/offset-check.py → data/sig-offset-check.json   (sigdir 가 더 모이면 다시 — 판정은 사람이 본다)
import json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KST = datetime.timezone(datetime.timedelta(hours=9))
def main():
    s = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); t = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))   # 2026-10-10 서울 전부(tod-bake.py)로 넓힘
    SP = {str(e['no']): e for e in t['spots']}; rows = []
    for k, recs in s['its'].items():
        e = SP.get(k)
        if not e: continue
        for rec in recs:
            if 'a' not in rec: continue
            d = datetime.datetime.fromtimestamp(rec['a'], KST); sod = d.hour * 3600 + d.minute * 60 + d.second
            plan = e['plans'].get(e['dow'].get(str(d.isoweekday() % 7 + 1)))   # 경찰청 요일 코드 1 = 일 … 7 = 토
            if not plan: continue
            cur = None
            for r in plan:
                if int(r[0][:2]) * 3600 + int(r[0][3:]) * 60 <= sod: cur = r
            cur = cur or plan[-1]; C, off = cur[1], cur[2]
            if rec.get('ci') != C: continue   # 받은 주기가 계획과 다르면(다른 계획·감응) 뺀다
            ps = int(cur[0][:2]) * 3600 + int(cur[0][3:]) * 60; cen = lambda x: x if x <= C / 2 else x - C
            # 자정 기준으로 본 주기 안 자리(res)가 1현시 시작(0)이 아니어도 다른 현시의 시작과 맞으면 — 받은 값의 기준 이동류(가장 긴 녹색)가 그 현시에 켜지는 것
            res = (sod - off) % C; hit = 0
            for ring in (cur[3], cur[4]):
                acc = 0
                for i, x in enumerate(int(v) for v in ring.split()):
                    if min((res - acc) % C, (acc - res) % C) <= 5 and not hit: hit = i + 1
                    acc += x
            base = [m[0] + ' ' + m[1] for m in rec.get('mv', []) if len(m) > 5 and m[5] == 0]
            rows.append([k, e['name'], rec['day'], d.strftime('%H:%M:%S'), C, off, cur[0], round(cen((sod - off) % C)), round(cen((sod - ps - off) % C)), hit, base])
    n = len(rows); okA = sum(1 for r in rows if abs(r[7]) <= 4); okB = sum(1 for r in rows if abs(r[8]) <= 4)
    by = {}
    for r in rows: e = by.setdefault(r[0], [r[1], 0, 0, [], 0, []]); e[1] += 1; e[2] += 1 if abs(r[7]) <= 4 else 0; e[3].append(r[7]); e[4] = r[9] or e[4]; e[5] = r[10] or e[5]
    spots = {k: [v[0], v[1], v[2], round(sum(v[3]) / len(v[3]), 1), v[4], v[5]] for k, v in by.items()}
    okP = sum(1 for r in rows if r[9])
    doc = {'schema': 'tg-sig-offset-check/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': 'data/sigdir-seoul.json(서울 T-Data V2X — 기준 이동류 녹색이 실제로 켜진 시각) × data/signal-tod-seoul.json(경찰청 교차로계획정보 — 주기·옵셋)',
           'result': {'n': n, 'A_자정 기준': okA, 'B_계획 시작 기준': okB, 'tol': 4, '교차로': len(spots), '교차로_모두 맞음': sum(1 for v in spots.values() if v[1] == v[2]), '교차로_하나도 안 맞음': sum(1 for v in spots.values() if v[2] == 0), '어느 현시든 시작과 맞음(±5초)': okP, '교차로_어느 현시와도 안 맞음': sum(1 for v in spots.values() if not v[4])},
           'read': '±4초 안이면 맞음. A 가 대부분 맞고 B 는 계획 시작 시각이 주기의 배수일 때만 맞으면 → 옵셋은 자정(0시 0분 0초)을 0 으로 센다: 주기 시작 = (하루 초 − 옵셋) 이 주기로 나누어떨어지는 때. 남는 +1~+4초는 기준 이동류 녹색이 주기 시작보다 조금 늦게 켜지는 몫(전적색 등)과 잔여시간 자료의 1초 눈금.',
           'note': ['1현시 시작과 안 맞는 곳의 대부분은 옵셋이 틀린 것이 아니라 받은 값의 기준 이동류(가장 긴 녹색)가 1현시가 아닌 다른 현시에 켜지는 곳이다 — 그 현시의 시작과는 ±5초로 맞는다(2026-10-10 · 안 맞은 11곳의 계획을 경찰청에서 다시 받아 보니 9월 10일 것과 한 줄도 다르지 않았다)', '교차로 제어기 시계가 표준시에 맞춰져 있어야 성립한다(맞지 않는 교차로는 어긋남으로 드러난다)', '맞지 않는 기록은 기준 이동류가 1현시가 아니거나 그 시간대에 다른 계획·감응 운영이었을 수 있다 — 까닭은 이 자료로 못 가린다',
                    '경찰청 계획 자료가 있는 교차로끼리의 시험이다 — 교통과 출력물 5곳(sig-ksc-seocho.json)은 T-Data 에 값이 없어 이 시험에 들어 있지 않다(같은 규칙을 적용하면 추정)'],
           'fields': 'spots{교차로 번호: [이름, 대조한 기록 수, 1현시 시작과 맞은 수, 평균 어긋남(초), ph 받은 값의 기준 이동류가 켜지는 현시(0 = 어느 현시 시작과도 안 맞음), 기준 이동류[방위 이동류…]]} — ph ≥ 1 이면 자정 기준 옵셋이 맞는 교차로이고 「기준 이동류 = ph 현시」라는 뜻(현시와 방향을 잇는 근거) · ph = 0 인 곳만 계획으로 센 초를 믿지 않는다 · rows[[교차로 번호, 이름, 받은 날, 녹색이 켜진 시각, 주기, 옵셋, 그 계획의 시작 시각, A 어긋남(초), B 어긋남(초), 맞은 현시, 기준 이동류]]',
           'spots': spots, 'rows': rows}
    p = os.path.join(ROOT, 'data', 'sig-offset-check.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('기록', n, '· A 자정 기준 맞음', okA, '· B 계획 시작 기준 맞음', okB, '· 교차로', len(spots), '· 모두 맞음', doc['result']['교차로_모두 맞음'], '· 하나도 안 맞음', doc['result']['교차로_하나도 안 맞음'], '· 바이트', os.path.getsize(p))
    import collections
    print('어느 현시든 맞은 기록', okP, '/', n, '· 어느 현시와도 안 맞는 곳', [(v[0], v[3]) for v in spots.values() if not v[4]])
    print('기준 이동류가 1현시가 아닌 곳', [(v[0], v[4], v[5]) for v in spots.values() if v[4] > 1])
    print('맞은 기록의 어긋남 분포', sorted(collections.Counter(r[7] for r in rows if abs(r[7]) <= 4).items()))
    print('받은 주기가 계획과 달라 뺀 기록은 세지 않았다')
if __name__ == '__main__': main()
