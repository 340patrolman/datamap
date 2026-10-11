# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚔 음주운전 적발: 나이대 · 시간대 · 농도 · 다시 적발 × 경찰서(소유자 2026-10-11 「권고대로 진행」 — 원자료는 저장소 밖 · 지도에는 집계만) → data/dui-catch.json
#   재료 = ../07_API키/out/dg/15043308/<해>.csv — 공공데이터포털 「경찰청_음주운전」(15043308 · 적발 1건당 1줄: 성별·적발횟수·나이·알콜농도·측정거부·측정일시·관할경찰서 · cp949)
#     **원자료는 저장소에 올리지 않는다** — 1건 단위라 작은 칸(경찰서 × 나이 × 시각)은 사람이 드러날 수 있다. 이 도구는 묶은 수만 싣는다
#   전국 = 나이대 × 시간대 · 나이대 × 농도 · 나이대 × 적발 횟수 · 요일 × 시간대(교차표) / 경찰서 = 나이대 · 시간대 · 농도 · 적발 횟수 · 요일 · 성별(갈래마다 따로 — 교차하지 않는다)
#   경찰서 표에서 1~4건인 칸은 null 로 가린다(가린 칸이 하나뿐이면 합에서 빼서 알 수 있으므로 그다음 작은 칸도 가린다) · 0 은 0 그대로
#   py -3.12 -X utf8 tools/region/duicatch-bake.py
import json, os, csv, io, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15043308')
AGE = ['19세 이하', '20대', '30대', '40대', '50대', '60~64세', '65세 이상']; BAC = ['0.03~0.049%', '0.05~0.079%', '0.08~0.149%', '0.15~0.199%', '0.2% 이상', '측정 거부', '0.03% 미만·그 밖']; REP = ['1번째', '2번째', '3번째', '4번째 이상']
def age_i(a): return 0 if a <= 19 else 1 if a <= 29 else 2 if a <= 39 else 3 if a <= 49 else 4 if a <= 59 else 5 if a <= 64 else 6
def bac_i(r):
    if r['측정거부'] == 'Y': return 5
    try: v = float(r['알콜농도'])
    except Exception: return 6
    return 6 if v < 0.03 else 0 if v < 0.05 else 1 if v < 0.08 else 2 if v < 0.15 else 3 if v < 0.2 else 4
def hide(v):
    v = [None if 0 < x < 5 else x for x in v]
    if sum(1 for x in v if x is None) == 1:
        c = [(x, i) for i, x in enumerate(v) if x]
        if c: v[min(c)[1]] = None
    return v
def main():
    years = {}
    for f in sorted(glob.glob(os.path.join(SRC, '*.csv'))):
        R = list(csv.DictReader(io.StringIO(open(f, 'rb').read().decode('cp949', 'replace')))); bad = 0
        ah = [[0] * 12 for _ in AGE]; ab = [[0] * len(BAC) for _ in AGE]; ar = [[0] * 4 for _ in AGE]; dh = [[0] * 12 for _ in range(7)]; sx = [0, 0]; ST = {}; yr = None
        for r in R:
            try: a = int(r['나이']); t = datetime.datetime.strptime(r['측정일시'].strip()[:16], '%Y-%m-%d %H:%M'); n = int(r['적발횟수'])
            except Exception: bad += 1; continue
            yr = yr or t.year; ai = age_i(a); hi = t.hour // 2; bi = bac_i(r); ri = min(n, 4) - 1 if n >= 1 else 0; wd = (t.weekday() + 1) % 7; si = 0 if r['성별'] == '남자' else 1
            ah[ai][hi] += 1; ab[ai][bi] += 1; ar[ai][ri] += 1; dh[wd][hi] += 1; sx[si] += 1
            nm = r['관할경찰서'].strip()
            if not nm.endswith('경찰서'): nm = '(시도경찰청 등)'
            e = ST.setdefault(nm, {'n': 0, 'age': [0] * 7, 'hour': [0] * 12, 'bac': [0] * len(BAC), 'rep': [0] * 4, 'dow': [0] * 7, 'sex': [0, 0]})
            e['n'] += 1; e['age'][ai] += 1; e['hour'][hi] += 1; e['bac'][bi] += 1; e['rep'][ri] += 1; e['dow'][wd] += 1; e['sex'][si] += 1
        for e in ST.values():
            for k in ('age', 'hour', 'bac', 'rep', 'dow', 'sex'): e[k] = hide(e[k])
        years[str(yr)] = {'n': len(R) - bad, 'bad': bad, 'sex': sx, 'age_hour': ah, 'age_bac': ab, 'age_rep': ar, 'dow_hour': dh, 'st': dict(sorted(ST.items()))}
        print(yr, '· 줄', len(R), '· 못 읽은 줄', bad, '· 경찰서', len(ST), '· 나이대 합', [sum(x) for x in ah], '· 적발 횟수 합', [sum(x[i] for x in ar) for i in range(4)], '· 농도 합', [sum(x[i] for x in ab) for i in range(len(BAC))])
        for nm in ('서울서초경찰서', '서울방배경찰서', '서울강남경찰서'): print('  ', nm, ST.get(nm))
    doc = {'schema': 'tg-dui-catch/1', 'made': datetime.date.today().isoformat(), 'got': '2026-10-11',
           'source': '경찰청 「경찰청_음주운전」(공공데이터포털 15043308 · 파일데이터 · 적발 1건당 1줄) — 이 지도는 묶은 수만 싣는다(원자료는 싣지 않는다)',
           'note': ['**적발(단속에 걸린) 건수다 — 음주운전이 일어난 수가 아니다.** 어디서 · 언제 · 얼마나 단속했느냐에 따라 달라진다(단속을 많이 한 시간대·경찰서가 많이 나온다) · 사고는 data/gen-trend.json',
                    '경찰서 = 적발한 관할 경찰서(운전자가 사는 곳이 아니다) · 시도경찰청 이름으로 적힌 몇 건은 「(시도경찰청 등)」으로 묶었다',
                    '경찰서 표의 null = 1~4건이라 가린 칸(하나만 가려지면 그다음 작은 칸도 가렸다) · 0 은 0 · 경찰서 표는 갈래마다 따로다(나이대와 시간대를 교차하지 않았다)',
                    '적발 횟수 = 원자료의 「적발횟수」(그 사람이 이번까지 몇 번째인가) · 「측정 거부」는 농도 값이 없다 · 농도 구간은 이 지도가 나눈 것(0.03% 면허정지 · 0.08% 취소 · 0.2% 가중 기준에 맞춤)',
                    '시간대 = 측정한 시각 2시간 단위(0 = 0~2시 … 11 = 22~24시) · 요일 0 = 일 … 6 = 토 · 나이는 적발 때 나이'],
           'ages': AGE, 'bacs': BAC, 'reps': REP,
           'fields': 'years{해: {n 건수, sex[남, 여], age_hour[나이대 7][시간대 12], age_bac[나이대 7][농도 7], age_rep[나이대 7][적발 횟수 4], dow_hour[요일 7][시간대 12], st{경찰서 이름: {n, age[7], hour[12], bac[7], rep[4], dow[7], sex[2]}}}}',
           'years': years}
    p = os.path.join(ROOT, 'data', 'dui-catch.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('바이트', os.path.getsize(p))
if __name__ == '__main__': main()
