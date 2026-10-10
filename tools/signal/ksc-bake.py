# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 서초경찰서 교통과 신호 운영값(표준신호제어기DB KSC-5800SE/SEC-8400 출력물 손 판독) → data/sig-ksc-seocho.json
#   소유자 2026-10-10: 현시도 PDF 5장(서초역사거리 4039 · 서초경찰서 4036 · 서울성모병원 4034 · 강남터미널고가밑 4031 · 삼호가든사거리 4028)을 가리키며 「신호값데이터도 넣어라 · 여기까지는 ok다」
#     → 「잠가서 / 평문 / 안 넣기」를 여쭈어 **「평문으로 넣기」** 로 답하셨다(2026-09-12 의 「확인코드로 잠가서」 결정을 이 5곳에 한해 바꿈). **이 5곳까지만** — 다른 교차로의 교통과 자료는 소유자가 다시 정하기 전에는 넣지 않는다.
#   같은 날 소유자가 T-Data 방향별 신호 카드(「어느 쪽에서 오는 차?」 · 방향별 녹·황·적 · 켜지는 차례)를 붙여 주며 「이렇게 표시를 해줘」 → 방향별 값(dir)을 같이 굽는다(tg-sig-ksc/2)
#   원자료 둘(서로 따로 판독 · 주기·현시값 96/96 일치):
#     ① 07_API키/신호앱/data/서초서_교통과_신호_불러오기용_20260911.json(tbsig-ksc/1 · 요일 계획·패턴 — 값을 그대로)
#     ② 07_API키/현시도_서초서/현시도_5곳_전사.json(tg-signal-sheet/1 · 현시마다 켜지는 이동류 번호 · 황색·전적색 · 참고 글)
#   방향별 값은 **계산값**이다: 이동류가 켜지는 현시들의 현시값 합 − 마지막 현시의 황색·전적색 = 녹색 · 주기 − 녹색 − 황색 = 적색
#     - 출력물에 「○초 고정」·따로 적힌 운영이 있는 이동류는 계산이 안 맞으므로 초를 비운다(g = null · why 에 까닭)
#     - A링·B링 현시값이 다른 곳(서초역사거리)은 어느 링이 어느 이동류인지 도면에 명시가 없어 표준 관례(이동류 1~4 = A링)로 읽은 **추정**이다(rg = 1)
#   PDF 원본·현시도 그림은 싣지 않는다
#   py -3.12 -X utf8 tools/signal/ksc-bake.py
import json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
SRC = os.path.join(KB, '신호앱', 'data', '서초서_교통과_신호_불러오기용_20260911.json')
SHEET = os.path.join(KB, '현시도_서초서', '현시도_5곳_전사.json')
OK = ('4039', '4036', '4034', '4031', '4028')   # 소유자가 공개를 정한 곳만
# 이동류 번호표(도면 오른쪽 아래 · 다섯 장 공통 · 도면 위 = 북) → [들어오는 쪽 방위, 직진 St·좌회전 Lt, 나가는 쪽]
MV = {1: ['et', 'Lt', '남'], 2: ['wt', 'St', '동'], 3: ['st', 'Lt', '서'], 4: ['nt', 'St', '남'], 5: ['wt', 'Lt', '북'], 6: ['et', 'St', '서'], 7: ['nt', 'Lt', '동'], 8: ['st', 'St', '북']}
# 계산으로 초를 낼 수 없는 이동류(출력물 참고 글 그대로의 까닭) — 초를 비운다
FIX = {('4034', 7): '4현시에서 북→동 좌회전은 11초 고정(출력물) — 현시값 합으로 계산되지 않는다',
       ('4036', 5): '3현시에서 서→북 좌회전은 A지점 7초 고정(출력물)',
       ('4036', 3): '2현시 남→서 좌회전은 출력물에 따로 적혀 있다: 녹17 + 황3 + 적22(북→북 유턴 포함 현시)'}
# 초는 내되 같이 알릴 글
WARN = {('4034', 2): '평일·금 16~20시는 시차제 — 5현시 서→동 직진은 23초(황색 포함) 뒤 적색(출력물)',
        ('4028', 5): '도면에 27/5 로 적혀 있다(27 = 미확인 · B연등지점 우회전 신호일 가능성)',
        ('4036', 8): '남→북 직진 연장운영(출력물) — 계산값보다 길 수 있다'}
# 소유자가 현장에서 보고 알려 준 것(날짜와 함께 · 말씀 그대로) — 판독과 맞는지의 근거로 싣는다
FIELD = {'4034': ['2026-10-10 소유자 현장 확인: 「1현시는 반포대로 남북 간 방향, 2현시는 북에서 남 직좌 — 이렇게 흘러간다」 → 판독의 차례(남북 동시 직진 → 북쪽 진입 직진+좌회전)와 같다. 출력물은 남북 동시 직진을 1·2현시 둘로 나눠 적어, 현장에서 보는 「2현시(북 직좌)」는 출력물의 3·4현시다']}
def secs(s): return [int(x) for x in s.split(':')]

def main():
    j = json.load(open(SRC, encoding='utf-8')); SH = {str(s['no']): s for s in json.load(open(SHEET, encoding='utf-8'))['sheets']}; items = []
    for e in j['items']:
        if e['no'] not in OK: continue
        for k, p in e['pat'].items(): assert sum(p['a']) == p['c'] and sum(p['b']) == p['c'], (e['no'], k)   # 현시 합 = 주기
        for d, rows in e['tod'].items():
            for t, c, pn in rows: assert e['pat'][str(pn)]['c'] == c, (e['no'], d, t)   # 시간대 계획의 주기 = 그 패턴의 주기
        it = {'no': e['no'], 'nm': e['nm'], 'lat': round(e['la'], 6), 'lon': round(e['lo'], 6), 'day': e['day'], 'dayk': e.get('dayk'), 'tod': e['tod'], 'pat': e['pat'], 'memo': e.get('memo') or []}
        s = SH.get(e['no'])
        if s:
            for k, p in e['pat'].items():   # 두 판독이 같은 값인지(주기·옵셋·현시값)
                q = s['patterns'][k]; assert q['cycle'] == p['c'] and q['offset'] == p['off'] and secs(q['rows'][0]) == p['a'] and secs(q['rows'][1]) == p['b'], (e['no'], k)
            n = len(s['phases']); Y = secs(s['params']['황색'])[:n]; AR = secs(s['params']['전적색'])[:n]
            ph = [{'p': x['p'], 'mv': [m for m in x['moves']], 't': x['text'], 'ped': x.get('ped') or []} for x in s['phases']]
            diff = any(p['a'] != p['b'] for p in e['pat'].values())
            where = collections_phases(s['phases'])
            D = {}
            for k, p in e['pat'].items():
                rows = []
                for m, P in sorted(where.items()):
                    if m not in MV: continue
                    row = p['a'] if m <= 4 else p['b']   # 표준 관례 — 이동류 1~4 = A링 · 5~8 = B링(도면에 명시 없음 — a ≠ b 인 곳은 추정)
                    st = sum(row[:P[0] - 1]); tot = sum(row[x - 1] for x in P); y = Y[P[-1] - 1]; ar = AR[P[-1] - 1]
                    fx = FIX.get((e['no'], m))
                    g = None if fx else tot - y - ar
                    rows.append([MV[m][0], MV[m][1], MV[m][2], g, y, (None if g is None else p['c'] - g - y), st, P, m])
                rows.sort(key=lambda r: (r[6], r[8])); D[k] = rows
            it.update({'ph': ph, 'Y': Y, 'AR': AR, 'dir': D, 'rg': 1 if diff else 0,
                       'why': {str(m): t for (no, m), t in FIX.items() if no == e['no']}, 'warn': {str(m): t for (no, m), t in WARN.items() if no == e['no']},
                       'roads': s.get('roads'), 'around': s.get('around'), 'hist': s.get('history') or [], 'pnote': s.get('phase6note') or [], 'field': FIELD.get(e['no']) or []})
        items.append(it)
    doc = {'schema': 'tg-sig-ksc/2', 'made': datetime.date.today().isoformat(),
           'source': '서초경찰서 교통과 제공 · 표준신호제어기DB(KSC-5800SE/SEC-8400) 출력물 5장을 손으로 판독(%s) · 현시별 이동류·황색·전적색 = 같은 출력물의 다른 판독(2026-09-11 · 주기·현시값 서로 일치) — 소유자가 이 5곳의 공개를 정함(2026-10-10)' % j.get('read', ''),
           'note': ['계획값이다 — 감응·수동 운영·행사·공사 중에는 실제와 다르다 · 출력물의 시행일(day) 뒤에 바뀌었을 수 있다',
                    '방향별 초(dir)는 출력물에 적힌 값이 아니라 계산값이다: 그 이동류가 켜지는 현시들의 현시값 합에서 마지막 현시의 황색·전적색을 뺀 것이 녹색 · 주기에서 녹색·황색을 뺀 것이 적색',
                    '출력물에 「○초 고정」 등 따로 적힌 이동류는 계산이 맞지 않아 초를 비웠다(g = null · why 에 까닭) — 지어 넣지 않는다',
                    'A링·B링 현시값이 다른 교차로(rg = 1 · 서초역사거리)는 어느 링이 어느 이동류인지 도면에 명시가 없어 표준 관례(이동류 1~4 = A링)로 읽은 추정이다 — 직진·좌회전 초가 서로 바뀌어 있을 수 있다',
                    '옵셋(off)의 기준 = 자정으로 본다: 주기 시작(1현시 시작) = (하루 초 − off) 가 주기로 나누어떨어지는 때 — 경찰청 계획이 있는 다른 교차로 22곳에서 실제 녹색 시각과 23/25 가 0~+4초로 맞았다(data/sig-offset-check.json · 2026-10-10). 다만 이 5곳은 T-Data 에 값이 없어 직접 검증되지 않았다 → 이 규칙으로 센 「지금 몇 초」는 추정이고, 현장에서 어긋나면 그 교차로는 쓰지 않는다 · 연동 속도 계산에는 쓰지 않는다',
                    '밤(22시~)에는 과속을 막으려고 연동을 일부러 끊어 둔 구간이 있다(소유자 현장 지식) — 「이 속도면 계속 녹색」 같은 안내에 쓰지 않는다',
                    '보행 신호·유턴·보조등(이동류 18·21·27)은 방향별 표에 넣지 않았다 — ph 의 ped 와 pnote(출력물 참고 글)를 본다',
                    '삼호가든사거리(4028)는 서초중앙로 축 · 나머지 넷은 반포대로 축이다'],
           'mv': '이동류 번호(도면 번호표 · 위 = 북): 1 동→남 좌회전 · 2 서→동 직진 · 3 남→서 좌회전 · 4 북→남 직진 · 5 서→북 좌회전 · 6 동→서 직진 · 7 북→동 좌회전 · 8 남→북 직진 · 18 보행 · 21·27 미확인',
           'fields': 'items[{no 교차로 번호, nm, lat, lon, day 출력물의 날짜, dayk(시행일·작성일), tod{요일 계획 1 월~목 · 2 금 · 3 토 · 4 일·공휴일: [[시작 HHMM, 주기 초, 패턴 번호]…] — 그날 첫 계획보다 이르면 전날 마지막 계획이 이어진다}, pat{패턴: {c 주기, off 옵셋, a[A링 현시별 초], b[B링 현시별 초]}}, memo[참고 글], '
                     'ph[{p 현시, mv[켜지는 이동류 번호], t 글, ped[보행]}], Y[현시별 황색 초], AR[현시별 전적색 초], '
                     'dir{패턴: [[들어오는 쪽(nt 북 · et 동 · st 남 · wt 서), St 직진·Lt 좌회전, 나가는 쪽, g 녹색 초|null, y 황색 초, r 적색 초|null, st 녹색 시작(주기 안 · 1현시 시작 = 0), [켜지는 현시…], 이동류 번호]…] — 녹색 시작이 이른 것부터}, '
                     'rg 1 이면 링 추정, why{이동류: 초를 비운 까닭}, warn{이동류: 같이 알릴 글}, roads{NS·EW 도로}, around{N·S·W·E 이웃}, hist[개선 이력], pnote[현시 참고 글], field[소유자 현장 확인 글]}]',
           'items': items}
    p = os.path.join(ROOT, 'data', 'sig-ksc-seocho.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(items), '바이트', os.path.getsize(p))
    for it in items:
        k = str(it['tod']['3'][2][2]) if len(it['tod']['3']) > 2 else '1'
        print(it['no'], it['nm'], '패턴', k, '주기', it['pat'][k]['c'], 'rg', it.get('rg'), '|', ' · '.join('%s %s→%s %s/%s/%s' % (r[0], r[1], r[2], r[3], r[4], r[5]) for r in it['dir'][k]))

def collections_phases(phases):   # 이동류 → 켜지는 현시들(차례대로 · 주기 끝에서 처음으로 이어지면 뒤쪽부터)
    w = {}
    for x in phases:
        for m in x['moves']: w.setdefault(m, []).append(x['p'])
    n = len(phases)
    for m, P in w.items():
        P.sort()
        if P[0] == 1 and P[-1] == n and len(P) < n:   # 끝 현시와 첫 현시에 걸친 이동류 — 끝쪽 묶음을 앞으로
            i = max(k for k in range(1, len(P)) if P[k] - P[k - 1] > 1) if any(P[k] - P[k - 1] > 1 for k in range(1, len(P))) else 0
            w[m] = P[i:] + P[:i]
    return w
if __name__ == '__main__': main()
