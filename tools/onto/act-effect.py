# -*- coding: utf-8 -*-
# 현장 조치 → 고리 앞뒤(2026-10-25 · 소유자 「계속 진행」 — 팔란티어 방식 「한 일 → 결과」)
#   지도 엮임 보기 「📝 현장 조치 적기」 CSV(고리,조치,이름,까닭,시각,전)를 07_API키/out/onto_logs/in/ 에 넣으면
#   이 PC 가 약 11분마다 쌓은 ITS 속도(07_API키/out/livespd/<날짜>.jsonl.gz)에서 고리 네 변의 속도를
#     전 = 조치 전 30분 · 뒤1 = 15~45분 뒤 · 뒤2 = 45~90분 뒤 로 평균 내고,
#     같은 요일 갈래(월~목·금·토·일)의 다른 날 같은 시각에 「전 → 뒤」가 얼마나 바뀌었나(평소 흐름)와 나란히 놓는다
#   → 조치한 날의 변화 − 평소의 변화 = 조치 쪽으로 기운 몫(어림 · 가능성 D — 그날 수요가 달랐을 수 있다)
#   결과는 저장소에 올리지 않는다(07_API키/out/onto_logs/act_<날짜>.md) — 형님이 「맞다」 한 줄만 규칙 장부 FIELD 로
#   py -3.12 -X utf8 tools/onto/act-effect.py
import csv, io, os, glob, gzip, json, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
LOGS = os.path.join(KB, '07_API키', 'out', 'onto_logs'); SPD = os.path.join(KB, '07_API키', 'out', 'livespd')


def dcls(d): w = d.weekday(); return 3 if w == 6 else 2 if w == 5 else 1 if w == 4 else 0   # 0 월~목 · 1 금 · 2 토 · 3 일


def read_acts():
    R = []
    for f in sorted(glob.glob(os.path.join(LOGS, 'in', '*.csv')) + glob.glob(os.path.join(LOGS, 'in', '*.txt'))):
        b = open(f, 'rb').read()
        for enc in ('utf-8-sig', 'cp949'):
            try: t = b.decode(enc); break
            except UnicodeDecodeError: continue
        rd = list(csv.reader(io.StringIO(t)))
        if not rd or [c.strip() for c in rd[0]][:2] != ['고리', '조치']: continue
        h = [c.strip() for c in rd[0]]
        R += [dict(zip(h, r)) for r in rd[1:] if any(x.strip() for x in r)]
    return [dict(t) for t in {tuple(sorted(r.items())) for r in R}]


def leg_links():
    loops = json.load(open(os.path.join(ROOT, 'data', 'onto-loops.json'), encoding='utf-8'))['loops']
    core = json.load(open(os.path.join(ROOT, 'ontology-core', 'data', 'core-seocho.json'), encoding='utf-8'))
    O = {o['id']: o for o in core['objects']}; ir = collections.defaultdict(list)
    for e in core['edges']:
        if e[1] == '이룸': ir[e[0]].append((e[3].get('k', 0), O[e[2]]['link']))
    out = {}
    for L in loops:
        out[L['id']] = (L, [(lg.get('links') or []) + [l for k, l in sorted(ir.get(lg['apr'], []))] for lg in L['legs']])   # 지도와 같은 셈 — 고리 자료 링크 먼저, 없으면 접근로 앞 조각부터 · 값 온 것 중 앞 둘
    return out


def snaps():
    S = []
    for f in sorted(glob.glob(os.path.join(SPD, '*.jsonl.gz'))):
        for line in gzip.open(f, 'rt', encoding='utf-8'):
            try: d = json.loads(line)
            except ValueError: continue
            S.append((int(d['at']), d['m']))
    return sorted(S, key=lambda x: x[0])


def win(S, links, t0, t1):
    vs = [[m[l] for l in links if l in m][:2] for a, m in S if t0 <= a < t1]
    vs = [sum(v) / len(v) for v in vs if v]
    return round(sum(vs) / len(vs), 1) if vs else None


def main():
    A = read_acts(); LL = leg_links(); S = snaps()
    os.makedirs(LOGS, exist_ok=True)
    out = ['# 현장 조치 → 고리 앞뒤 — %s' % datetime.date.today().isoformat(), '',
           '조치 %d건 · 쌓인 속도 기록 %d장(%s ~ %s)' % (len(A), len(S), datetime.datetime.fromtimestamp(S[0][0]).strftime('%m-%d %H:%M') if S else '—', datetime.datetime.fromtimestamp(S[-1][0]).strftime('%m-%d %H:%M') if S else '—'), '',
           '읽는 법: 변마다 「전 → 뒤1(15~45분) → 뒤2(45~90분)」 km/h · 「평소」 = 같은 요일 갈래 다른 날 같은 시각의 「전 → 뒤1」 변화 평균 · 「기운 몫」 = 그날 변화 − 평소 변화(+ 면 조치 뒤 더 빨라짐) · **가능성 D** — 그날 수요(신세계·분수·버스)가 달랐을 수 있어 조치 효과라고 단정하지 않는다', '']
    for r in sorted(A, key=lambda r: r.get('시각', '')):
        if r.get('고리') not in LL: continue
        L, legs = LL[r['고리']]
        try: t = datetime.datetime.strptime(r['시각'].strip(), '%Y-%m-%d %H:%M')
        except ValueError: continue
        ts = int(t.timestamp()); cls = dcls(t)
        out.append('## %s · %s%s' % (r['시각'], r.get('이름', ''), (' · ' + r['까닭']) if r.get('까닭') else ''))
        out.append('')
        out.append('| 변 | 전 | 뒤1 | 뒤2 | 그날 변화 | 평소 변화(같은 요일 갈래 · 날 수) | 기운 몫 |')
        out.append('|---|---|---|---|---|---|---|')
        for lg, links in zip(L['legs'], legs):
            b = win(S, links, ts - 1800, ts); a1 = win(S, links, ts + 900, ts + 2700); a2 = win(S, links, ts + 2700, ts + 5400)
            base = []
            days = sorted({datetime.date.fromtimestamp(a) for a, m in S} - {t.date()})
            for d in days:
                dd = datetime.datetime.combine(d, t.time())
                if dcls(dd) != cls: continue
                x = int(dd.timestamp()); bb = win(S, links, x - 1800, x); aa = win(S, links, x + 900, x + 2700)
                if bb is not None and aa is not None: base.append(aa - bb)
            ch = round(a1 - b, 1) if a1 is not None and b is not None else None
            bm = round(sum(base) / len(base), 1) if base else None
            lean = round(ch - bm, 1) if ch is not None and bm is not None else None
            f = lambda v: '—' if v is None else ('%+.1f' % v if isinstance(v, float) and v != round(v) or True else str(v))
            out.append('| %s | %s | %s | %s | %s | %s | %s |' % (lg['nm'].split(' — ')[0], b if b is not None else '—', a1 if a1 is not None else '—', a2 if a2 is not None else '—', f(ch), ('%s (%d날)' % (f(bm), len(base))) if bm is not None else '— (같은 갈래 다른 날 기록 없음)', f(lean)))
        out.append('')
    if len(out) <= 5:
        out.append('아직 고리 조치 기록이 없다 — 지도 엮임 보기 「📝 현장 조치 적기」 → 📋 CSV 복사 → 07_API키/out/onto_logs/in/ 에 넣기')
    p = os.path.join(LOGS, 'act_%s.md' % datetime.date.today().strftime('%Y%m%d'))
    open(p, 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print('조치 %d · 속도 기록 %d · → %s' % (len(A), len(S), p))


if __name__ == '__main__':
    main()
