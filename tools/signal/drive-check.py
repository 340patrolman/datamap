# -*- coding: utf-8 -*-
# 주행 기록 대조 — 형님이 가르고를 켜고 실제로 달린 기록(tg-drive-log/1)으로 「교차로마다 실제로 걸린 시간 ↔ 가르고 예측」을 맞댄다
#   (2026-10-15 소유자 「보정이 필요 · 대조도 해 보고」 → 권고 ④ 정답 자료 = 실제 주행 · ①(시각 폭 표시) 다음 차례)
#   기록 파일은 저장소에 올리지 않는다 — 07_API키/out/drive/*.json 에만 두고, 결과도 화면과 07_API키/out/drive/check.md 에만
#   꼴(게임 세션에 제안 · 바뀌면 여기를 맞춘다):
#     {"schema":"tg-drive-log/1","app":"가르고 판","pts":[[ms, 위도, 경도, 정확도m, 속도m/s|null]],
#      "plan":{"at":출발 ms,"rows":[[교차로(INT-<T-GIS 코드> · C-ITS 번호 · 이름), 예측 +초, 근거 'its'|'cal'|'lim']]}}
#   교차로 자리 = data/onto-int.json(서울 8,097) · 도착 = 궤적이 그 교차로 30m 안에 처음 든 때(정확도 50m 넘는 점은 안 씀)
#   py -3.12 -X utf8 tools/signal/drive-check.py [파일 …]      (안 적으면 07_API키/out/drive/*.json 모두)
#   py -3.12 -X utf8 tools/signal/drive-check.py --selftest     (가짜 궤적으로 셈이 맞는지)
import sys, os, json, glob, math, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DRV = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'drive')
NEAR, ACCMAX = 30.0, 50.0


def load_ints():
    d = json.load(open(os.path.join(ROOT, 'data', 'onto-int.json'), encoding='utf-8'))
    by_code, by_cits, by_name = {}, {}, {}
    for x in d['items']:
        by_code[str(x[0])] = (x[2], x[3], x[1])
        if x[4]:
            by_cits[str(x[4])] = (x[2], x[3], x[1])
        by_name.setdefault(x[1], []).append((x[2], x[3], x[1]))
    def find(key):
        k = str(key)
        if k.startswith('INT-'):
            return by_code.get(k[4:])
        if k.isdigit():
            return by_cits.get(k) or by_code.get(k)
        c = by_name.get(k)
        return c[0] if c and len(c) == 1 else None   # 이름이 둘 이상이면 못 가린다(지어 고르지 않음)
    return find


def dist(a, b, c, d):
    k = math.cos(math.radians((a + c) / 2))
    return math.hypot((a - c) * 111320, (b - d) * 111320 * k)


def check(doc, find):
    pts = [p for p in doc.get('pts', []) if (p[3] is None or p[3] <= ACCMAX)]
    plan = doc.get('plan') or {}
    t0, out = plan.get('at') or (pts[0][0] if pts else 0), []
    for key, pred, basis in plan.get('rows', []):
        ll = find(key)
        if not ll:
            out.append((key, pred, basis, None, '자리 못 찾음')); continue
        hit = next((p for p in pts if p[0] >= t0 and dist(p[1], p[2], ll[0], ll[1]) <= NEAR), None)
        out.append((ll[2], pred, basis, (hit[0] - t0) / 1000.0 if hit else None, '' if hit else '안 지남'))
    return out


def report(files):
    find = load_ints(); lines, R = [], []
    for f in files:
        doc = json.load(open(f, encoding='utf-8'))
        if doc.get('schema') != 'tg-drive-log/1':
            print('건너뜀(꼴 아님)', f); continue
        rows = check(doc, find)
        lines.append('## %s · %s · 점 %d' % (os.path.basename(f), doc.get('app', ''), len(doc.get('pts', []))))
        lines.append('| 교차로 | 근거 | 예측 +초 | 실제 +초 | 실제÷예측 |'); lines.append('|---|---|---|---|---|')
        for nm, pred, basis, act, why in rows:
            r = act / pred if act and pred else None
            if r: R.append((basis, r))
            lines.append('| %s | %s | %s | %s | %s |' % (nm, basis, round(pred) if pred else '', round(act) if act else why, '%.2f' % r if r else ''))
    if R:
        lines.append('\n근거별 실제÷예측 가운데(1보다 크면 실제가 더 걸림):')
        for b in sorted(set(x[0] for x in R)):
            v = [x[1] for x in R if x[0] == b]
            lines.append('- %s: %.2f (%d곳)' % (b, st.median(v), len(v)))
    txt = '\n'.join(lines); print(txt)
    os.makedirs(DRV, exist_ok=True); open(os.path.join(DRV, 'check.md'), 'w', encoding='utf-8').write(txt + '\n')


def selftest():
    find = load_ints()
    a = find('INT-6'); assert a and a[2] == '연신내역', a
    lat0, lon0 = a[0] - 0.009, a[1]                       # 1km 남쪽에서 북으로 10 m/s → 100초 뒤 도착
    pts = [[1_000_000 + i * 1000, lat0 + 0.009 * i / 100, lon0, 5, 10] for i in range(130)]
    doc = {'schema': 'tg-drive-log/1', 'pts': pts, 'plan': {'at': 1_000_000, 'rows': [['INT-6', 80, 'cal'], ['없는곳XYZ', 50, 'lim']]}}
    rows = check(doc, find)
    assert rows[0][3] is not None and 95 <= rows[0][3] <= 100, rows[0]   # 30m 앞에서 듦 → 약 97초
    assert rows[1][4] == '자리 못 찾음', rows[1]
    print('✅ 자체 시험 통과 — 예측 80초 · 실제 %.0f초(비 %.2f) · 없는 교차로는 「자리 못 찾음」' % (rows[0][3], rows[0][3] / 80))


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        selftest()
    else:
        fs = [a for a in sys.argv[1:] if not a.startswith('--')] or sorted(glob.glob(os.path.join(DRV, '*.json')))
        if not fs:
            print('주행 기록 파일이 없다 —', DRV, '에 가르고에서 내보낸 파일을 넣는다')
        else:
            report(fs)
