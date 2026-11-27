# -*- coding: utf-8 -*-
# 🚦 T-GIS 신호현시도(표준신호제어기DB KSC-5800SE 출력물) 글자 인식 결과 → 요일 계획(TOD)·패턴(주기·연동·현시값)
#   소유자 2026-11-28 「T-GIS 신호값을 지도에 평문으로 · 서울 전체」 — 손 판독 대신 윈도우 글자 인식(tools/signal/tgis-ocr.ps1)으로 읽고,
#   **두 배율로 따로 읽어 같은 값만** 쓰며 검산(현시값 A 합 = B 합 = 주기 · 요일 계획의 주기 = 그 패턴 주기)이 하나라도 틀리면 그 교차로는 통째로 「사람 확인」으로 돌린다.
#   현시도 그림(어느 현시가 어느 방향인지)은 글자가 아니라 이 도구로 읽지 않는다.
#   py -3.12 -X utf8 tools/signal/tgis-parse.py <ocr.json> [<ocr2.json>]   → 표준출력 JSON
import json, re, sys

SPLIT = re.compile(r'^\d{1,3}(:\d{1,3}){1,7}$')


def load(p):
    j = json.load(open(p, encoding='utf-8-sig'))
    pg = j[0] if isinstance(j, list) else j
    return pg['words'], pg['w'], pg['h']


def fixnum(t):
    t = t.replace('()', '0').replace('O', '0').replace('o', '0').replace('l', '1').replace('I', '1')
    return t


def head(W):
    txt = ' '.join(w[0] for w in sorted(W, key=lambda w: (w[2] // 20, w[1])))
    no = re.search(r'교차로번호\s*[:：]?\s*(\d+)', txt)
    nm = re.search(r'교차로명\s*[:：]?\s*(\S+)', txt)
    dy = re.search(r'시\s*행\s*일\s*[:：]?\s*(\d{4})\s*[.\-]?\s*(\d{2})\s*[.\-]?\s*(\d{2})', txt)
    return (no.group(1) if no else None, nm.group(1) if nm else None, '%s-%s-%s' % dy.groups() if dy else None)


# 양식이 같아 칸 자리가 같다(서초역사거리 4039 배율 3 · 폭 3572 기준 가운데 x) — 머리 글자가 빠져도 자리로 읽는다
TODX = [(253 + 678 * k, 407 + 678 * k, 572 + 678 * k, 722 + 678 * k) for k in range(4)]
PATX = [(277, 434, 582, 729, 977), (1223, 1363, 1512, 1658, 1906)]


def rowy(W, names, need, y0=0, y1=10 ** 9):
    c = {}
    for w in W:
        if w[0] in names and y0 < w[2] < y1: c.setdefault(round(w[2] / 40.0), []).append(w)
    best = max(c.values(), key=len) if c else []
    return (sum(w[2] for w in best) / len(best)) if len(best) >= need else None


def anchors(p):
    """한글 판독에서 머리 줄 높이(배율 3 기준) — 영어 판독은 한글 머리 글자를 못 읽으므로 이것을 빌린다"""
    W, w, h = load(p); k3 = w / 3572.0
    yh = rowy(W, ('번호', '시각', '주기', '패턴'), 5)
    yp = rowy(W, ('번호', '주기', '패턴', '연동', '현시값'), 4, (yh or 0) + 300 * k3) if yh else None
    return (yh / k3 if yh else None, yp / k3 if yp else None)


def special(p):
    """오른쪽 「특수일」 표 — 날마다 따르는 TOD 번호(대개 모두 4). 읽힌 번호의 갯수를 돌려준다"""
    W, w, h = load(p); k3 = w / 3572.0
    yh = rowy(W, ('번호', '시각', '주기', '패턴'), 5)
    if not yh: return {}
    c = {}
    for q in W:
        if yh + 40 * k3 < q[2] < yh + 1200 * k3 and abs(q[1] + q[3] / 2 - 3311 * k3) < 70 * k3 and fixnum(q[0]) in ('1', '2', '3', '4'):
            c[fixnum(q[0])] = c.get(fixnum(q[0]), 0) + 1
    return c


def labels(p):
    """TOD 표 머리의 괄호 글(월~목요일·평일·토요일·특수일 …) — 장마다 번호의 뜻이 다르다"""
    W, w, h = load(p); k3 = w / 3572.0
    yh = rowy(W, ('번호', '시각', '주기', '패턴'), 5)
    if not yh: return None
    out = {}
    for k, cx in enumerate(TODX):
        ws = sorted([q for q in W if yh - 130 * k3 < q[2] < yh - 35 * k3 and cx[0] * k3 - 110 * k3 < q[1] + q[3] / 2 < cx[3] * k3 + 110 * k3], key=lambda q: q[1])
        t = ''.join(q[0] for q in ws)
        m = re.search(r'[\(（](.*?)[\)）]?$', t.replace('PLAN', '').replace('TOD', ''))
        out[str(k + 1)] = (m.group(1).strip(' ()') if m else t).strip()
    return out


def tod(W, k3, yh=None, ypa=None):
    if yh is None: yh = rowy(W, ('번호', '시각', '주기', '패턴'), 5, 0, 10 ** 9)
    if yh is None: return None, ['TOD 머리 못 찾음']
    yp = ypa or rowy(W, ('번호', '주기', '패턴', '연동', '현시값'), 4, yh + 300)
    yend = (yp - 140 * k3) if yp else yh + 1400 * k3
    out = {}; bad = []
    for k, cx in enumerate(TODX):
        cx = [v * k3 for v in cx]
        rows = {}
        for w in W:
            if not (yh + 40 * k3 < w[2] < yend): continue
            m = w[1] + w[3] / 2
            col = min(range(4), key=lambda i: abs(cx[i] - m))
            if abs(cx[col] - m) > 75 * k3: continue
            r = round((w[2] - yh) / (70.0 * k3))
            rows.setdefault(r, {}).setdefault(col, []).append(w[0])
        L = []
        for r in sorted(rows):
            c = rows[r]
            if 1 not in c and 2 not in c and 3 not in c: continue
            tm = re.sub(r'\D', '', fixnum(''.join(c.get(1, []))))
            cy = re.sub(r'\D', '', fixnum(''.join(c.get(2, []))))
            pt = re.sub(r'\D', '', fixnum(''.join(c.get(3, []))))
            if len(tm) != 4 or not cy or not pt or not (0 <= int(tm[:2]) < 24 and int(tm[2:]) < 60):
                bad.append('TOD%d 줄%d %s' % (k + 1, r, [c.get(1), c.get(2), c.get(3)])); continue
            L.append([tm, int(cy), int(pt)])
        out[str(k + 1)] = L
    return out, bad


def pats(W, k3, yt, ypa=None):
    yh = ypa or rowy(W, ('번호', '주기', '패턴', '연동', '현시값'), 4, (yt or 0) + 300 * k3)
    if yh is None: return None, ['패턴 머리 못 찾음']
    res = {}; bad = []
    for side, cx in enumerate(PATX):
        cx = [v * k3 for v in cx]
        sp = sorted([w for w in W if SPLIT.match(w[0]) and w[2] > yh + 30 * k3 and abs(w[1] + w[3] / 2 - cx[4]) < 200 * k3], key=lambda w: w[2])
        if len(sp) % 2: bad.append('현시값 줄 수 %d (쪽 %d)' % (len(sp), side)); continue
        for i in range(0, len(sp), 2):
            a, b = sp[i], sp[i + 1]
            n = side * len(sp) // 2 + i // 2 + 1
            av = [int(v) for v in a[0].split(':')]; bv = [int(v) for v in b[0].split(':')]
            mid_y = (a[2] + b[2]) / 2
            def cell(ci):
                c = [w for w in W if abs(w[2] + w[4] / 2 - mid_y - a[4] / 2) < 30 * k3 and abs(w[1] + w[3] / 2 - cx[ci]) < 50 * k3 and re.fullmatch(r'\d+', fixnum(w[0]))]
                return int(fixnum(c[0][0])) if len(c) == 1 else None
            off = cell(3); cy = cell(1); pn = cell(2)
            e = []
            if sum(av) != sum(bv): e.append('A합 %d ≠ B합 %d' % (sum(av), sum(bv)))
            if cy is not None and cy != sum(av): e.append('주기 %d ≠ 합 %d' % (cy, sum(av)))
            if pn is not None and pn != n: e.append('패턴 번호 %d ≠ %d' % (pn, n))
            if off is None: e.append('연동 못 읽음')
            elif off >= sum(av): e.append('연동 %d ≥ 주기' % off)
            if e: bad.append('패턴%d %s' % (n, ' · '.join(e)))
            res[str(n)] = {'c': sum(av), 'off': off, 'a': av, 'b': bv, 'y': (mid_y + a[4] / 2) / k3}
    return res, bad


def parse(p):
    return parse_words(*load(p))


def parse_words(W, w, h, anc=None):
    k3 = w / 3572.0
    no, nm, day = head(W)
    ay = anc[0] * k3 if anc and anc[0] else None
    ap = anc[1] * k3 if anc and anc[1] else None
    T, tb = tod(W, k3, ay, ap)
    P, pb = pats(W, k3, ay or rowy(W, ('번호', '시각', '주기', '패턴'), 5), ap)
    bad = tb + pb
    if T and P:
        for k, L in T.items():
            for tm, cy, pt in L:
                q = P.get(str(pt))
                if not q: bad.append('TOD%s %s 패턴 %d 없음' % (k, tm, pt))
                elif q['c'] != cy: bad.append('TOD%s %s 주기 %d ≠ 패턴%d %d' % (k, tm, cy, pt, q['c']))
    return {'no': no, 'nm': nm, 'day': day, 'tod': T, 'pat': P, 'bad': bad}


def same(x, y):
    return json.dumps([x['tod'], x['pat']], sort_keys=True) == json.dumps([y['tod'], y['pat']], sort_keys=True)


def check(T, P):
    bad = []
    if T and P:
        for k, L in T.items():
            for tm, cy, pt in L:
                q = P.get(str(pt))
                if not q: bad.append('TOD%s %s 패턴 %d 없음' % (k, tm, pt))
                elif q['c'] != cy: bad.append('TOD%s %s 주기 %d ≠ 패턴%d %d' % (k, tm, cy, pt, q['c']))
    return bad


def merge_n(R):
    """여러 번 읽은 것(배율·잘라 읽기)을 칸마다 맞댄다 — 읽힌 값이 하나뿐이거나 모두 같으면 그 값 · 다르면 둘 이상이 같은 값(다수) · 그래도 갈리면 「다름」"""
    bad = []; T = {}; P = {}
    def pick(vals, what):
        vals = [v for v in vals if v is not None]
        if not vals: return None, '못 읽음'
        ks = [json.dumps(v, sort_keys=True) for v in vals]
        best = max(set(ks), key=ks.count)
        if len(set(ks)) == 1 or ks.count(best) >= 2 and ks.count(best) > len(ks) / 2: return vals[ks.index(best)], None
        return vals[ks.index(best)], '읽을 때마다 다름'
    for k in '1234':
        vals = [(r['tod'] or {}).get(k) for r in R if not any(b.startswith('TOD%s 줄' % k) for b in r['bad'])]
        v, e = pick(vals, 'TOD')
        T[k] = v or []
        if e: bad.append('TOD%s %s' % (k, e))
    ns = sorted(set(n for r in R for n in (r['pat'] or {})), key=int)
    for n in ns:
        ab, e = pick([[q['a'], q['b']] for q in [(r['pat'] or {}).get(n) for r in R] if q and sum(q['a']) == sum(q['b'])], '현시값')
        if e or not ab: bad.append('패턴%s 현시값 %s' % (n, e or '못 읽음'))
        off, e2 = pick([q['off'] for q in [(r['pat'] or {}).get(n) for r in R] if q], '연동')
        if e2: bad.append('패턴%s 연동 %s' % (n, e2))
        if ab: P[n] = {'c': sum(ab[0]), 'off': off, 'a': ab[0], 'b': ab[1]}
        if off is not None and ab and off >= sum(ab[0]): bad.append('패턴%s 연동 ≥ 주기' % n)
    if len(P) != 16: bad.append('패턴 %d개' % len(P))
    bad += check(T, P)
    hd = [r for r in R if r.get('no')]
    out = {'no': hd[0]['no'] if hd else None, 'nm': next((r['nm'] for r in R if r.get('nm')), None),
           'day': next((r['day'] for r in R if r.get('day') and r['day'][:2] == '20'), None), 'tod': T, 'pat': P, 'bad': sorted(set(bad)), 'reads': len(R)}
    return out


def off_cell(W, w, n, y):
    """영어 판독은 현시값 줄(55:27:44:24)을 통째로 놓친다 — 한글 판독이 잡은 줄 높이 y(배율 3 기준)에서 연동 칸 숫자만 다시 읽는다"""
    k3 = w / 3572.0; cx = PATX[0 if int(n) <= 8 else 1][3] * k3; cy = y * k3
    c = [q for q in W if abs(q[2] + q[4] / 2 - cy) < 30 * k3 and abs(q[1] + q[3] / 2 - cx) < 55 * k3 and re.fullmatch(r'\d+', fixnum(q[0]))]
    return int(fixnum(c[0][0])) if len(c) == 1 else None


def merge_strict(R, extra=None):
    """칸마다 **두 번 이상** 같게 읽힌 값만 · 가장 많이 읽힌 값이 하나뿐이어야 한다(동률이면 못 씀). 한 번만 읽힌 칸은 쓰지 않는다"""
    bad = []; T = {}; P = {}
    def vote(vals):
        c = {}
        for v in vals:
            k = json.dumps(v); c[k] = c.get(k, 0) + 1
        top = sorted(c.items(), key=lambda x: -x[1])
        if top and top[0][1] >= 2 and (len(top) == 1 or top[1][1] < top[0][1]): return json.loads(top[0][0]), True
        return None, False
    for k in '1234':
        c = {}; seen = {}
        for r in R:
            for row in (r['tod'] or {}).get(k) or []:
                t = tuple(row); c[t] = c.get(t, 0) + 1
        good = sorted([list(t) for t, n in c.items() if n >= 2])
        times = [g[0] for g in good]
        if len(times) != len(set(times)): bad.append('TOD%s 같은 시각이 두 값' % k)
        weak = sorted(set(t[0] for t, n in c.items() if n < 2) - set(times))
        if weak: bad.append('TOD%s 한 번만 읽힌 줄 %s' % (k, ','.join(weak[:3])))
        if not good and any((r['tod'] or {}).get(k) for r in R): bad.append('TOD%s 맞는 줄 없음' % k)
        T[k] = good
    ns = sorted(set(n for r in R for n in (r['pat'] or {})), key=int)
    for n in ns:
        qs = [(r['pat'] or {}).get(n) for r in R]
        qs = [q for q in qs if q and sum(q['a']) == sum(q['b'])]
        if len(qs) < 2: continue
        ab, okab = vote([[q['a'], q['b']] for q in qs])
        off, okof = vote([q['off'] for q in [(r['pat'] or {}).get(n) for r in R] if q and q['off'] is not None] + [v for v in (extra or {}).get(n, []) if v is not None])
        if not okab: bad.append('패턴%s 현시값 합의 안 됨' % n); continue
        if not okof: bad.append('패턴%s 연동 합의 안 됨' % n)
        elif off >= sum(ab[0]): bad.append('패턴%s 연동 ≥ 주기' % n)
        P[n] = {'c': sum(ab[0]), 'off': off, 'a': ab[0], 'b': ab[1]}
    if sorted(P, key=int) != [str(i) for i in range(1, 17)]: bad.append('패턴 %d개' % len(P))
    if not any(T.values()): bad.append('TOD 없음')
    bad += check(T, P)
    return {'tod': T, 'pat': P, 'bad': sorted(set(bad)), 'reads': len(R)}


def merge(r, r2):
    """두 배율을 칸마다 맞댄다 — 한쪽만 읽은 칸은 그 값을, 둘 다 읽었는데 다르면 「다름」. 검산은 합친 값으로 다시"""
    bad = []; T = {}; P = {}
    def badk(x, pre): return any(b.startswith(pre) for b in x['bad'])
    for k in '1234':
        x = (r['tod'] or {}).get(k); y = (r2['tod'] or {}).get(k); bx = badk(r, 'TOD%s 줄' % k) or x is None; by = badk(r2, 'TOD%s 줄' % k) or y is None
        if not bx and not by:
            if x != y: bad.append('TOD%s 두 배율 다름' % k)
            T[k] = x
        elif not bx: T[k] = x
        elif not by: T[k] = y
        else: bad.append('TOD%s 둘 다 못 읽음' % k); T[k] = x or y or []
    ns = sorted(set((r['pat'] or {})) | set((r2['pat'] or {})), key=int)
    for n in ns:
        x = (r['pat'] or {}).get(n); y = (r2['pat'] or {}).get(n)
        if x and y:
            if x['a'] != y['a'] or x['b'] != y['b']: bad.append('패턴%s 현시값 두 배율 다름' % n)
            o = [v for v in (x['off'], y['off']) if v is not None]
            if len(set(o)) > 1: bad.append('패턴%s 연동 %s 두 배율 다름' % (n, o))
            if not o: bad.append('패턴%s 연동 못 읽음' % n)
            P[n] = dict(x, off=o[0] if o else None)
            if sum(x['a']) != sum(x['b']): bad.append('패턴%s A합 ≠ B합' % n)
        else:
            q = x or y; P[n] = q; bad.append('패턴%s 한 배율만' % n)
    for b in r['bad'] + r2['bad']:
        if not (b.startswith('TOD') and ' 줄' in b) and not b.startswith('패턴') and not b.startswith('TOD') : bad.append(b)
    if len(P) not in (16,): bad.append('패턴 %d개' % len(P))
    bad += check(T, P)
    out = dict(r); out['no'] = r['no'] or r2['no']; out['nm'] = r['nm'] or r2['nm']; out['day'] = r['day'] if r['day'] and r['day'][:2] == '20' else r2['day']
    out['tod'] = T; out['pat'] = P; out['bad'] = sorted(set(bad))
    return out


if __name__ == '__main__':
    r = parse(sys.argv[1])
    if len(sys.argv) > 2: r = merge(r, parse(sys.argv[2]))
    print(json.dumps(r, ensure_ascii=False))
