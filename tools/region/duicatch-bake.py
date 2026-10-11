# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚔 음주운전 적발: 해마다 · 나이대 · 시간대 · 농도 · 다시 적발 × 경찰서(소유자 2026-10-11 「경찰관 업무용으로는 자세히 사용을 해야 해 — 음주운전 흐름은 공익을 위해 필요해」)
#   → data/dui-catch.json(전국 · 2007~2024 해마다) + data/dui-catch-st.json(경찰서마다 · 나이·경찰서 칸이 있는 해만)
#   재료 = ../07_API키/out/dg/15043308/ — 공공데이터포털 「경찰청_음주운전」(15043308 · 경찰청 생활안전교통국 교통안전과 · 이용허락범위 제한 없음 · 적발 1건당 1줄)의 올해 파일 + 「주기성 과거 데이터」 20개
#     2007~2019 = 적발횟수·알콜농도·측정거부·측정일시만 / 2020~2024 = 성별·나이·관할경찰서까지(2022년은 측정거부 칸 없음) · 한 해의 일부만 든 파일(20200518 · 20220630 · 20220731)은 쓰지 않는다
#   **1건 단위 원자료는 저장소에 올리지 않는다**(묶은 수만) — 경찰서 표는 원자료가 제한 없이 공개된 것이라 칸을 가리지 않았다(소유자 결정 · 처음 판은 1~4건 칸을 가렸다)
#   py -3.12 -X utf8 tools/region/duicatch-bake.py
import json, os, csv, io, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15043308')
AGE = ['19세 이하', '20대', '30대', '40대', '50대', '60~64세', '65세 이상']; BAC = ['0.03~0.049%', '0.05~0.079%', '0.08~0.149%', '0.15~0.199%', '0.2% 이상', '측정 거부', '0.03% 미만·그 밖']; REP = ['1번째', '2번째', '3번째', '4번째 이상']
SKIP = ('hist_20200518', 'hist_20220630', 'hist_20220731')
def age_i(a): return 0 if a <= 19 else 1 if a <= 29 else 2 if a <= 39 else 3 if a <= 49 else 4 if a <= 59 else 5 if a <= 64 else 6
def bac_i(r):
    if (r.get('측정거부') or '').strip() == 'Y': return 5
    try: v = float(r['알콜농도'])
    except Exception: return 6
    return 6 if v < 0.03 else 0 if v < 0.05 else 1 if v < 0.08 else 2 if v < 0.15 else 3 if v < 0.2 else 4
def read(f):
    b = open(f, 'rb').read(); t = None
    if b[:2] in (b'\xff\xfe', b'\xfe\xff'): t = b.decode('utf-16')
    else:
        for enc in ('utf-8-sig', 'cp949'):
            try: t = b.decode(enc); break
            except Exception: pass
    if t is None: t = b.decode('cp949', 'replace')
    head = t.split('\n', 1)[0]; R = list(csv.reader(io.StringIO(t), delimiter='\t' if head.count('\t') > head.count(',') else ','))
    cols = [c.strip().replace('측정거부여부', '측정거부') for c in R[0]]; return [dict(zip(cols, [x.strip() for x in r])) for r in R[1:] if len(r) >= len(cols) - 1], cols
def when(s):
    s = s.strip().replace('/', '-')
    for fm in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try: return datetime.datetime.strptime(s[:19] if fm.endswith('S') else s[:16], fm)
        except Exception: pass
    return None
def main():
    Y = {}; STY = {}
    for f in sorted(glob.glob(os.path.join(SRC, '*.csv'))):
        if os.path.basename(f).startswith(SKIP): continue
        R, cols = read(f); hasA = '나이' in cols and '관할경찰서' in cols; hasRef = '측정거부' in cols; bad = 0; yrs = collections.Counter()
        n = 0; hour = [0] * 24; bac = [0] * len(BAC); rep = [0] * 4; dh = [[0] * 12 for _ in range(7)]; mon = [0] * 12; sx = [0, 0]
        ah = [[0] * 12 for _ in AGE]; ab = [[0] * len(BAC) for _ in AGE]; ar = [[0] * 4 for _ in AGE]; ST = {}
        for r in R:
            t = when(r.get('측정일시', ''))
            try: k = int(r['적발횟수'])
            except Exception: k = None
            if t is None or k is None: bad += 1; continue
            n += 1; yrs[t.year] += 1; hi = t.hour // 2; bi = bac_i(r); ri = min(max(k, 1), 4) - 1; wd = (t.weekday() + 1) % 7
            hour[t.hour] += 1; bac[bi] += 1; rep[ri] += 1; dh[wd][hi] += 1; mon[t.month - 1] += 1
            if hasA:
                try: ai = age_i(int(r['나이']))
                except Exception: continue
                si = 0 if r.get('성별') == '남자' else 1; sx[si] += 1; ah[ai][hi] += 1; ab[ai][bi] += 1; ar[ai][ri] += 1
                nm = r['관할경찰서']; nm = nm if nm.endswith('경찰서') else '(시도경찰청 등)'
                e = ST.setdefault(nm, {'n': 0, 'age': [0] * 7, 'hour': [0] * 24, 'bac': [0] * len(BAC), 'rep': [0] * 4, 'mon': [0] * 12, 'sex': [0, 0], 'age_hour': [[0] * 12 for _ in AGE], 'dow_hour': [[0] * 12 for _ in range(7)], 'age_rep': [[0] * 4 for _ in AGE]})
                e['n'] += 1; e['age'][ai] += 1; e['hour'][t.hour] += 1; e['bac'][bi] += 1; e['rep'][ri] += 1; e['mon'][t.month - 1] += 1; e['sex'][si] += 1; e['age_hour'][ai][hi] += 1; e['dow_hour'][wd][hi] += 1; e['age_rep'][ai][ri] += 1
        yr = yrs.most_common(1)[0][0]
        if str(yr) in Y and Y[str(yr)]['n'] >= n: continue   # 같은 해 파일이 둘이면 줄이 많은 쪽
        d = {'n': n, 'bad': bad, 'file': os.path.basename(f), 'hour': hour, 'bac': bac, 'rep': rep, 'mon': mon, 'dow_hour': dh, 'refusal_col': 1 if hasRef else 0}
        if hasA: d.update({'sex': sx, 'age_hour': ah, 'age_bac': ab, 'age_rep': ar}); STY[str(yr)] = dict(sorted(ST.items()))
        Y[str(yr)] = d
        print(yr, os.path.basename(f), '· 건', n, '· 못 읽은 줄', bad, '· 2번째 이상 %.1f%%' % ((n - rep[0]) / n * 100), '· 0.08 이상 %.1f%%' % (sum(bac[2:5]) / n * 100), '· 밤 20~06 %.1f%%' % (sum(hour[20:] + hour[:6]) / n * 100), '· 낮 10~18 %.1f%%' % (sum(hour[10:18]) / n * 100), ('· 60세 이상 %.1f%%' % (sum(sum(x) for x in ah[5:]) / max(1, sum(sx)) * 100)) if hasA else '')
    Y = dict(sorted(Y.items())); STY = dict(sorted(STY.items()))
    base = {'made': datetime.date.today().isoformat(), 'got': '2026-10-11',
            'source': '경찰청 「경찰청_음주운전」(공공데이터포털 15043308 · 올해 파일 + 주기성 과거 데이터 · 경찰청 생활안전교통국 교통안전과 · 이용허락범위 제한 없음) — 적발 1건당 1줄 원자료를 묶은 수',
            'ages': AGE, 'bacs': BAC, 'reps': REP}
    note = ['**적발(단속에 걸린) 건수다 — 음주운전이 일어난 수가 아니다.** 어디서 · 언제 · 얼마나 단속했느냐에 따라 달라진다 · 사고는 data/gen-trend.json',
            '**정의가 바뀐 해**: 2019-06-25 단속 기준 0.05% → 0.03%(그 앞 해에는 0.03~0.049% 칸이 거의 없다) · 2020~2021년은 감염병 때 단속 방식이 바뀐 해 · 2022년 파일에는 측정거부 칸이 없다(거부가 「그 밖」이나 농도 칸에 섞였을 수 있다)',
            '**「적발횟수」 칸의 뜻이 2023년에 바뀐 것으로 보인다** — 2번째 이상이 2007~2022년에는 1.4~3.6% 인데 2023·2024년에는 43.6·43.7% 다(원자료에 설명이 없다 · 2022년까지는 그 해 안의 횟수, 2023년부터는 지금까지의 횟수로 짐작되지만 확인하지 못했다). **rep·age_rep 는 2022년 이전과 2023년 이후를 잇지 않는다**',
            '2007~2019년 파일에는 나이·성별·경찰서 칸이 없다 — 나이대·경찰서 표는 2020년부터 · 2016년은 과거 데이터에 한 파일(날짜 표기만 다름)',
            '적발 횟수 = 원자료의 「적발횟수」(그 사람이 이번까지 몇 번째인가) · 농도 구간은 이 지도가 나눈 것(0.03% 정지 · 0.08% 취소 · 0.2% 가중 기준에 맞춤) · 시간 = 측정한 시각',
            '요일 0 = 일 … 6 = 토 · 2시간대 0 = 0~2시 … 11 = 22~24시 · 달 0 = 1월']
    doc = dict(base, schema='tg-dui-catch/2', note=note,
               fields='years{해: {n 건수, hour[24시], bac[농도 7], rep[적발 횟수 4], mon[12달], dow_hour[요일 7][2시간대 12], refusal_col 1 = 측정거부 칸이 있는 해, (2020년부터) sex[남, 여], age_hour[나이대 7][2시간대 12], age_bac[7][7], age_rep[7][4]}} · 경찰서마다는 data/dui-catch-st.json', years=Y)
    p = os.path.join(ROOT, 'data', 'dui-catch.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    doc2 = dict(base, schema='tg-dui-catch-st/1', note=note + ['경찰서 = 적발한 관할 경찰서(운전자가 사는 곳이 아니다) · 이름은 원자료 그대로(해마다 신설·개칭이 있다 — 이름이 바뀐 서는 줄이 끊긴다) · 시도경찰청 이름으로 적힌 몇 건은 「(시도경찰청 등)」',
                                                             '칸을 가리지 않았다 — 원자료가 제한 없이 공개된 것이고 이 표는 그것을 묶은 수다. 건수가 한두 건인 칸으로 사람을 짐작하려 하지 말 것(업무·연구용)'],
                fields='years{해: {경찰서 이름: {n, age[나이대 7], hour[24시], bac[7], rep[4], mon[12], sex[남, 여], age_hour[7][2시간대 12], dow_hour[요일 7][2시간대 12], age_rep[7][4]}}}', years=STY)
    p2 = os.path.join(ROOT, 'data', 'dui-catch-st.json'); json.dump(doc2, open(p2, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), os.path.getsize(p2), '· 경찰서 표가 있는 해', list(STY))
    for nm in ('서울서초경찰서', '서울방배경찰서', '서울강남경찰서'):
        print(' ', nm, [(y, v[nm]['n'], '2번째↑ %d' % (v[nm]['n'] - v[nm]['rep'][0]), '60세↑ %d' % sum(v[nm]['age'][5:]), '낮 %d' % sum(v[nm]['hour'][10:18])) for y, v in STY.items() if nm in v])
if __name__ == '__main__': main()
