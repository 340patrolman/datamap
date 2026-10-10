# -*- coding: utf-8 -*-
"""방향별 신호(T-Data) 값이 제대로 맞는지 여러 길로 맞대 본다 — 소유자 2026-10-11 「신호체계가 제대로 맞는지 확인도 해야 해」.

 ① 교통과 현시도(sig-ksc-seocho · 5곳) × 받은 값 — 같은 요일 갈래·시각의 주기 · 옵셋 · 방향별 녹색 초
 ② 경찰청 계획(signal-tod-seoul · 351곳) × 받은 값 — 주기 · 옵셋(계획의 어느 현시 경계와든 ±3초)
 ③ 잔여시간 API × 신호 상태 API — 같은 교차로·같은 요일 갈래·같은 주기에서 방향별 녹색 초(서로 다른 두 원천)
 ④ 다시 받아 맞대기 — 시간을 두고 다시 받은 닻이 앞 닻에서 이어 센 것과 맞는가(기록의 v 통과 · x 실패)
 ⑤ 짜임새 — 직각 방향 직진이 함께 녹색 / 마주 오는 직진과 좌회전이 함께 녹색 / 녹+황+적 ≠ 주기

쓰기: data/sig-audit.json(tg-sig-audit/1) — 교차로마다 통과한 길·어긋난 길. 값을 고치지 않는다(맞대 본 결과만 적는다).
  py -3.12 -X utf8 tools/signal/sig-audit.py
"""
import json, os, sys, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = lambda n: json.load(open(os.path.join(ROOT, 'data', n), encoding='utf-8'))
TOL = 3.0          # 녹색 초·옵셋이 이만큼 안이면 맞는 것으로 본다
ANG = {'nt': 0, 'ne': 45, 'et': 90, 'se': 135, 'st': 180, 'sw': 225, 'wt': 270, 'nw': 315}


def adiff(a, b):
    """두 방위가 벌어진 각(0~180) — 모르는 방위면 None"""
    if a not in ANG or b not in ANG: return None
    d = abs(ANG[a] - ANG[b]) % 360
    return min(d, 360 - d)


def hm(s):
    s = s.replace(':', '')
    return int(s[:2]) * 60 + int(s[2:])


def cdev(a, b, c):
    """원 위(주기 c)에서 a 와 b 가 벌어진 초"""
    d = (a - b) % c
    return min(d, c - d)


def overlap(s1, l1, s2, l2, c):
    """주기 c 원 위 두 구간이 겹치는 초"""
    tot = 0.0
    for k in (-1, 0, 1):
        a, b = s2 + k * c, s2 + k * c + l2
        tot += max(0.0, min(s1 + l1, b) - max(s1, a))
    return tot


def ksc_plan(x, cl, minute):
    """교통과 계획 — 요일 갈래 cl(0 월~목·1 금·2 토·3 일) · 하루 분 → (패턴 번호, 주기, 그 계획이 끝나는 분) · 그날 첫 계획 전이면 전날 마지막 계획"""
    L = x['tod'].get(str(cl + 1)) or []
    cur, nxt = None, 1440
    for r in L:
        if hm(r[0]) <= minute: cur = r
        elif nxt == 1440: nxt = hm(r[0])
    if cur is None:
        prev = x['tod'].get(str({0: 4, 1: 1, 2: 2, 3: 3}[cl])) or []      # 월~목의 전날은 일(월요일 새벽)·월~목 — 섞여 있어 일요일 계획으로 본다(같으면 문제없다)
        if not prev: return None
        cur = prev[-1]; nxt = hm(L[0][0]) if L else 1440
    return cur[2], cur[1], nxt


def pol_plan(sp, cl, hour):
    """경찰청 계획 — 그 시(時)의 시작과 끝에 같은 계획이 돌 때만 [주기, 옵셋, 현시 경계들]"""
    dows = {0: ['2', '3', '4', '5'], 1: ['6'], 2: ['7'], 3: ['1']}[cl]
    ids = set(sp['dow'].get(d) for d in dows)
    if len(ids) != 1 or None in ids: return None
    P = sp['plans'].get(ids.pop())
    if not P: return None
    def at(m):
        cur = None
        for r in P:
            if hm(r[0]) <= m: cur = r
        return cur or P[-1]
    a, b = at(hour * 60), at(hour * 60 + 59)
    if a is not b: return None
    try:
        ph = [float(v) for v in a[3].split()]
    except Exception:
        ph = []
    bd, acc = [0.0], 0.0
    for v in ph[:-1]:
        acc += v; bd.append(acc)
    return a[1], a[2], bd


def main():
    S = D('sigdir-seoul.json'); its, pl = S['its'], S.get('pl', {})
    KSC = {str(x['no']): x for x in D('sig-ksc-seocho.json')['items']}
    POL = {str(s['no']): s for s in D('signal-tod-seoul.json')['spots']}
    out, tot = {}, collections.Counter()
    R = lambda no: out.setdefault(no, {'ok': [], 'bad': []})

    for no, L in its.items():
        # ⑤ 짜임새 — 가장 새 기록으로
        for o in L[-1:]:
            c = o.get('ci') or o.get('cyc')
            mv = [m for m in o['mv'] if m[2] is not None and m[5] is not None and (len(m) < 8 or m[7] != 2)]
            for m in mv:
                if abs(m[2] + (m[3] or 0) + (m[4] or 0) - o['cyc']) > 2.5:
                    R(no)['bad'].append(['sum', '%s %s 녹+황+적 %.0f ≠ 주기 %.0f' % (m[0], m[1], m[2] + (m[3] or 0) + (m[4] or 0), o['cyc'])]); tot['sum_bad'] += 1
            st = [m for m in mv if m[1] == 'St']
            perp = [(a, b) for a in st for b in st if adiff(a[0], b[0]) == 90 and a[0] < b[0] and overlap(a[5], a[2], b[5], b[2], c) > 3]
            if perp:
                R(no)['bad'].append(['perp', '직각 방향 직진이 함께 녹색(' + ' · '.join('%s·%s' % (a[0], b[0]) for a, b in perp) + ') — 방위 이름이 실제와 다를 수 있다']); tot['perp_bad'] += 1
            ol = [(a, b, overlap(a[5], a[2], b[5], b[2], c)) for a in mv if a[1] == 'Lt' for b in st if adiff(a[0], b[0]) == 180]
            ol = [q for q in ol if q[2] > 3]
            if ol:
                R(no)['bad'].append(['opp', '마주 오는 직진과 좌회전이 함께 녹색(' + ' · '.join('%s 좌회전 × %s 직진 %d초' % (a[0], b[0], v) for a, b, v in ol) + ') — 비보호·겹침 운영이거나 방위 이름이 다르다']); tot['opp_bad'] += 1
            if not perp and not ol and mv: tot['shape_ok'] += 1
        tot['its'] += 1

        # ④ 다시 받아 맞대기
        v = [o['v'] for o in L if o.get('v')]; x = [o['x'] for o in L if o.get('x')]
        if v: R(no)['ok'].append(['re', '다시 받아 맞음 %d번(가장 길게 %d분 뒤 · 어긋남 %.1f초)' % (len(v), max(q[0] for q in v), max(abs(q[1]) for q in v))]); tot['re_ok'] += 1
        if x and not v: R(no)['bad'].append(['re', '다시 받은 값이 이어 센 것과 안 맞음 %d번' % len(x)]); tot['re_bad'] += 1

        # ③ 두 API 맞대기
        A = [o for o in L if o.get('src') != 'p']; B = [o for o in L if o.get('src') == 'p']
        best = None
        for a in A:
            for b in B:
                if a.get('cl') != b.get('cl') or abs(a['cyc'] - b['cyc']) > 2.5: continue
                ga = {(m[0], m[1]): m[2] for m in a['mv'] if m[2] is not None}; gb = {(m[0], m[1]): m[2] for m in b['mv'] if m[2] is not None}
                ks = [k for k in ga if k in gb]
                if not ks: continue
                d = max(abs(ga[k] - gb[k]) for k in ks)
                if best is None or d < best[0]: best = (d, len(ks))
        if best:
            if best[0] <= TOL + 2: R(no)['ok'].append(['api', '두 API 값이 맞음(이동류 %d개 · 녹색 차 %.0f초 안)' % (best[1], best[0])]); tot['api_ok'] += 1
            else: R(no)['bad'].append(['api', '두 API 의 녹색 초가 다름(가장 큰 차 %.0f초)' % best[0]]); tot['api_bad'] += 1

        # ② 경찰청 계획
        sp = POL.get(no)
        if sp and pl.get(no):
            okc = badc = oko = bado = 0; ex = []
            for cl, hr, cyc, off, day in pl[no]:
                q = pol_plan(sp, cl, hr)
                if not q: continue
                if abs(q[0] - cyc) > 2.5: badc += 1; ex.append('%s %d시 계획 주기 %d · 받은 주기 %d' % ('월~목 금 토 일'.split()[cl], hr, q[0], cyc)); continue
                okc += 1
                dv = min(cdev(off, q[1] + b, cyc) for b in q[2])
                if dv <= TOL: oko += 1
                else: bado += 1; ex.append('%s %d시 옵셋 %d초 어긋남' % ('월~목 금 토 일'.split()[cl], hr, dv))
            if okc + badc:
                tot['pol_n'] += 1; tot['pol_slots'] += okc + badc; tot['pol_cyc_ok'] += okc; tot['pol_off_ok'] += oko; tot['pol_off_bad'] += bado
                if oko and not bado and not badc: R(no)['ok'].append(['pol', '경찰청 계획과 맞음 — 시각대 %d칸(주기·옵셋)' % oko]); tot['pol_ok'] += 1
                elif badc or bado: R(no)['bad'].append(['pol', '경찰청 계획과 다름 — ' + ' · '.join(ex[:3])]); tot['pol_bad'] += 1

        # ① 교통과 현시도
        x = KSC.get(no)
        if x:
            ex, okk = [], 0
            for o in L:
                if o.get('cl') is None: continue
                m0 = hm(o['from'])
                q = ksc_plan(x, o['cl'], m0)
                if not q: continue
                pn, c, nxt = q
                if hm(o['to']) >= nxt and hm(o['to']) >= m0: continue      # 받은 동안 계획이 바뀌었다
                lab = '%s %s' % ('월~목 금 토 일'.split()[o['cl']], o['from'])
                if abs(c - o['cyc']) > 2.5: ex.append('%s 주기 %d ≠ 받은 %.0f' % (lab, c, o['cyc'])); continue
                K = {(r[0], r[1]): r for r in x['dir'].get(str(pn), []) if r[3] is not None}
                dif = [(k, m[2] - K[k][3]) for m in o['mv'] if m[2] is not None for k in [(m[0], m[1])] if k in K]
                bad = [q2 for q2 in dif if abs(q2[1]) > TOL + 1]
                # 옵셋 — 받은 값의 기준 이동류(녹색 시작 0)가 교통과 계획에서 켜지는 자리만큼 옮겨 맞댄다
                od = None
                if o.get('a') is not None and x['pat'].get(str(pn)):
                    ref = [m for m in o['mv'] if m[5] == 0 and (m[0], m[1]) in K]
                    if ref:
                        sod = (o['a'] + 32400) % 86400
                        od = cdev(sod % c, (x['pat'][str(pn)]['off'] + K[(ref[0][0], ref[0][1])][6]) % c, c)
                if bad: ex.append('%s 녹색 초 다름(%s)' % (lab, ' · '.join('%s %s %+.0f초' % (k[0], k[1], d) for k, d in bad)))
                elif od is not None and od > TOL: ex.append('%s 옵셋 %d초 어긋남' % (lab, od))
                else: okk += 1
                tot['ksc_slots'] += 1
            if okk and not ex: R(no)['ok'].append(['ksc', '교통과 현시도와 맞음 — 받은 기록 %d개(주기·방향별 녹색·옵셋)' % okk])
            elif ex: R(no)['bad'].append(['ksc', '교통과 현시도와 다름 — ' + ' / '.join(ex[:3]) + (' · 맞은 기록 %d개' % okk if okk else '')])
            tot['ksc_n'] += 1; tot['ksc_ok' if okk and not ex else 'ksc_bad' if ex else 'ksc_none'] += 1

    n_ok = sum(1 for v in out.values() if v['ok'] and not v['bad']); n_bad = sum(1 for v in out.values() if v['bad']); n_mix = sum(1 for v in out.values() if v['ok'] and v['bad'])
    J = {'schema': 'tg-sig-audit/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
         'source': '이 지도가 받은 방향별 신호(data/sigdir-seoul.json)를 교통과 현시도 · 경찰청 교차로계획정보 · 두 API 서로 · 다시 받은 값과 맞대 본 결과(값을 고치지 않는다)',
         'fields': 'spots{교차로 번호: {ok[[길, 글]], bad[[길, 글]]}} — 길: ksc 교통과 현시도 · pol 경찰청 계획 · api 잔여시간×신호 상태 두 API · re 다시 받아 맞대기 · perp 직각 직진 겹침 · opp 마주 오는 직진×좌회전 겹침 · sum 녹+황+적≠주기. 아무 길로도 맞대 보지 못한 교차로는 없다(목록에 없음 = 대조 전)',
         'tol': TOL, 'sum': dict(tot, checked=len(out), ok_only=n_ok, any_bad=n_bad, mixed=n_mix), 'spots': out}
    json.dump(J, open(os.path.join(ROOT, 'data', 'sig-audit.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(json.dumps(J['sum'], ensure_ascii=False))
    if '-v' in sys.argv:
        for no, v in out.items():
            for b in v['bad']: print(no, (S['pts'].get(no) or ['', '', ''])[2], b[0], b[1])


if __name__ == '__main__':
    main()
