# -*- coding: utf-8 -*-
"""대조 결과 묶어 쌓기(2026-10-15 소유자 「권고대로 모두 진행하자」 — 신호 수집 세션이 전함: 카카오 원값·줄마다 「우리 값 + 비율」 저장 금지 · 묶은 대조 값(3건 이상)은 PC 안에만 · 보정은 ITS 로만)

route-spot·kakao-spot 가 --save 로 부른다. 07_API키/out/compare/acc-YYYYMMDD.json 하나에
  칸 = 「종류|요일 갈래|시간대|짝 또는 구간」 → 비율 목록만(시각·우리 값 없이 · 소수 둘째 자리) + 건수
우리 값(가르고 거리·시간 · 우리 계산 초)과 시각은 남기지 않는다 — 비율만으로는 카카오 값을 되살릴 수 없다.
보고(compare-report.py)는 건수 3 미만 칸을 보이지 않는다.
"""
import os, json, datetime as dt

KST = dt.timezone(dt.timedelta(hours=9))
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '07_API키', 'out', 'compare')


def band(h):
    return '출근' if 7 <= h < 10 else '낮' if 10 <= h < 17 else '퇴근' if 17 <= h < 20 else '저녁' if 20 <= h < 23 else '밤'


def kind_of(t, hol=()):
    return '일·공휴' if t.strftime('%Y-%m-%d') in hol or t.weekday() == 6 else '토' if t.weekday() == 5 else '평일'


def prune(today):
    """지난 날 묶음 파일에서 건수 3 미만 칸을 지운다(한 번의 값이 그대로 남지 않게) · 하루에 한 번"""
    import glob
    for f in glob.glob(os.path.join(OUT, 'acc-*.json')):
        if os.path.basename(f)[4:12] >= today:
            continue
        try:
            A = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        if A.get('pruned'):
            continue
        A['cells'] = {k: v for k, v in A.get('cells', {}).items() if v.get('n', 0) >= 3}
        A['pruned'] = 1
        json.dump(A, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))


def add(kind, t, key, vals, hol=()):
    """kind = route|seg · t = 그때(KST datetime) · key = 짝 번호나 구간 ID · vals = {이름: 비율 또는 참·거짓}"""
    os.makedirs(OUT, exist_ok=True)
    p = os.path.join(OUT, 'acc-%s.json' % t.strftime('%Y%m%d'))
    if not os.path.exists(p):
        prune(t.strftime('%Y%m%d'))
    try:
        A = json.load(open(p, encoding='utf-8'))
    except Exception:
        A = {'schema': 'tg-compare-acc/1', 'note': '칸마다 비율 목록만 · 시각·우리 값 없음 · 보고는 3건 이상 칸만', 'cells': {}}
    k = '|'.join([kind, kind_of(t, hol), band(t.hour), str(key)])
    c = A['cells'].setdefault(k, {'n': 0})
    c['n'] += 1
    for nm, v in vals.items():
        if isinstance(v, bool):
            c[nm] = c.get(nm, 0) + (1 if v else 0)
        elif v is not None:
            c.setdefault(nm, []).append(round(float(v), 2))
    tmp = p + '.tmp'
    json.dump(A, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    os.replace(tmp, p)
