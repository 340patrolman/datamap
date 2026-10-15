# -*- coding: utf-8 -*-
"""주행시간 보정 — ITS 통행속도(실측) ↔ 우리 계산(제한속도 + 신호 기다림)(2026-10-15)

카카오 길찾기 결과는 저장할 수 없어(카카오 개발자 게시판 답 「임시 캐싱 등의 방법으로 API 호출 및 이용은 금지」 · 소유자 결정 2026-10-15 「멈추고 ITS 로 대신」)
기준선을 저장해도 되는 공공 자료 ITS 통행속도로 바꿨다. 첫 비교에서 카카오 ≈ ITS × 1.10(9구간)이었다.

고정 구간 = 07_API키/kakao_eta_segments.json 의 28개(서초 간선 · 교차로 사이 · 실사건 좌표 아님 · ITS 링크 목록만 쓴다)
  실측(ITS)  = 같은 링크의 ITS 통행속도(07_API키/out/livespd/<날짜>.jsonl.gz · 약 22분마다)로 링크마다 m ÷ 속도 · 값 없는 링크는 같은 구간 값 있는 링크의 조화 평균 속도
              (값 있는 길이가 구간의 40% 넘을 때만 셈)
  우리 계산   = ① 제한속도: m ÷ 제한속도 + 출발·정지 가감속(travel-time.js accS 4초 × 2)
              ② ① + 신호 기다림: 지나는 신호 교차로(nav-seocho 마디의 신호 번호)마다 그 방향(들어오는 쪽) 직진의 적색 r·주기 C(sigdir-seoul.json · 같은 요일 갈래·가까운 시)
                 → 아무 때나 닿을 때 기다림 r²/(2C) + 설 확률 r/C × 가감속 4초 — 연동(녹색 물결)은 안 셈
  거리는 출발 첫 링크 30%·도착 끝 링크 70%(구간 굽는 규칙 그대로) · 도착 교차로 신호도 센다(ITS 링크 평균 속도에 링크 끝 대기가 들어 있어 실측과 같은 뜻으로)
결과(공공 자료라 저장 가능하지만 아직 판단 전이라 저장소 밖): 07_API키/out/eta_cal/report.md · cells.json
  py -3.12 -X utf8 tools/signal/etacal-its.py [--from YYYYMMDD] [--to YYYYMMDD] [--bake]
  --bake → datamap/data/eta-cal.json(tg-eta-cal/1) — 「주행 배율」 f = (실측 − 신호 기다림 − 가감속) ÷ 제한속도 주행 시간 의 요일 갈래 × 시간대 가운데값.
           지도(신고차량 예측)·가르고가 실시간 통행속도가 없을 때 제한속도 ÷ f 로 달린다고 본다(신호 기다림은 따로 셈하므로 이 배율은 주행 몫만).
           ITS 는 공공 자료(국가교통정보센터)라 배율 숫자는 저장소에 싣는다 · 카카오 값은 한 번도 들어가지 않는다.
"""
import sys, os, json, gzip, glob, math, statistics, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(RAW, 'out', 'eta_cal')
ACC = 4
F0, F1 = 0.30, 0.70
KST = dt.timezone(dt.timedelta(hours=9))
DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw']


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def load_graph():
    N, L = {}, {}
    for f in ('nav-seocho', 'nav-arterial'):
        p = os.path.join(ROOT, 'data', f + '.json')
        if not os.path.exists(p):
            continue
        j = json.load(open(p, encoding='utf-8'))
        for k, v in j['nodes'].items():
            if k in N:
                continue
            sg = v[7] if len(v) > 7 and isinstance(v[7], dict) else None
            N[k] = str(sg['no']) if sg and sg.get('no') is not None else None
        for q in j['links']:
            if q[0] in L:
                continue
            a = q[9] or []
            hd = None
            if len(a) >= 4:
                x, y, pts = a[0], a[1], [(a[0], a[1])]
                for i in range(2, len(a) - 1, 2):
                    x += a[i]; y += a[i + 1]; pts.append((x, y))
                (x0, y0), (x1, y1) = pts[-2], pts[-1]
                hd = math.degrees(math.atan2((x1 - x0) * math.cos(math.radians(37.5)), y1 - y0)) % 360   # 북 0 · 동 90
            L[q[0]] = {'m': q[3] or 1, 'lim': q[4] or 50, 't': q[2], 'hd': hd}
    return N, L


def dkind(t):          # sigdir tod 의 요일 갈래: 0 평일 · 1 토 · 2 일
    return 2 if t.weekday() == 6 else (1 if t.weekday() == 5 else 0)


def dname(t, hol):
    if t.strftime('%Y-%m-%d') in hol or t.weekday() == 6:
        return '일·공휴'
    return '토' if t.weekday() == 5 else '평일'


def load_hol():
    try:
        j = json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8'))
    except Exception:
        return set()
    d = j.get('days') or j.get('holidays') or j
    return set(d.keys()) if isinstance(d, dict) else set(x if isinstance(x, str) else x.get('d', '') for x in d)


def from_side(hd):     # 달리는 방향(북 0) → 들어오는 쪽(반대)
    return DIRS[int(((hd + 180) % 360 + 22.5) // 45) % 8]


def sig_wait(SD, no, hd, t):
    """그 교차로·그 방향 직진의 (r, C) — 같은 요일 갈래 가까운 시 · 없으면 아무 요일 · 방향은 같은 쪽 → 옆 45° · 없으면 None"""
    recs = SD.get(no) or []
    if not recs or hd is None:
        return None
    side = from_side(hd)
    i0 = DIRS.index(side)
    want = [side, DIRS[(i0 + 1) % 8], DIRS[(i0 - 1) % 8]]
    best = None
    for r in recs:
        try:
            h = int(r['from'][:2])
            rd = dt.date.fromisoformat(r['day'])
        except Exception:
            continue
        rk = 2 if r.get('dow') == 0 else (1 if r.get('dow') == 6 else 0)
        for w, sd in enumerate(want):
            mv = [x for x in r.get('mv', []) if x[0] == sd and x[1] == 'St']
            if not mv:
                continue
            g, y, red = mv[0][2], mv[0][3], mv[0][4]
            if red is None or g is None:
                continue
            C = r.get('cyc') or (g + (y or 0) + red)
            if not C or C <= 0:
                continue
            score = (0 if rk == dkind(t) else 100) + w * 10 + min(abs(h - t.hour), 24 - abs(h - t.hour))
            if best is None or score < best[0]:
                best = (score, red, C)
            break
    return None if best is None else (best[1], best[2])


def load_spd(d0, d1):
    S = []
    for f in sorted(glob.glob(os.path.join(RAW, 'out', 'livespd', '*.jsonl.gz'))):
        day = os.path.basename(f)[:8]
        if day < d0 or day > d1:
            continue
        for ln in gzip.open(f, 'rt', encoding='utf-8'):
            try:
                j = json.loads(ln)
                m = j['m'] if isinstance(j['m'], dict) else json.loads(j['m'])
                S.append((int(j['at']), m))
            except Exception:
                continue
    return sorted(S, key=lambda x: x[0])


def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    a = int(k); b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)


def band(h):
    return '출근 07~09' if 7 <= h < 10 else '낮 10~16' if 10 <= h < 17 else '퇴근 17~19' if 17 <= h < 20 else '저녁 20~22' if 20 <= h < 23 else '밤 23~06'


def main():
    d0, d1 = arg('--from', '20000101'), arg('--to', '29991231')
    segs = json.load(open(os.path.join(RAW, 'kakao_eta_segments.json'), encoding='utf-8'))['segments']
    N, L = load_graph()
    SD = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))['its']
    hol = load_hol()
    S = load_spd(d0, d1)
    rows, nsig = [], {}
    for s in segs:
        P = []
        ids = s['its_links']
        if any(l not in L for l in ids):
            continue
        for i, lid in enumerate(ids):
            fr = (F1 - F0) if len(ids) == 1 else (1 - F0) if i == 0 else F1 if i == len(ids) - 1 else 1.0
            P.append((lid, L[lid]['m'] * fr, L[lid]['lim']))
        m = sum(x[1] for x in P)
        t_lim = sum(x[1] / (x[2] / 3.6) for x in P) + 2 * ACC
        sigs = []
        for lid in ids:                          # 끝 링크의 끝(도착 교차로) 신호도 센다 — ITS 링크 통행속도에는 링크 끝 신호 대기가 들어 있다
            no = N.get(L[lid]['t'])
            if no and (not sigs or sigs[-1][0] != no):
                sigs.append((no, L[lid]['hd']))
        nsig[s['id']] = len(sigs)
        for at, mp in S:
            t = dt.datetime.fromtimestamp(at, KST)
            cov = sum(x[1] for x in P if mp.get(x[0], 0) > 0)
            if cov < 0.4 * m:
                continue
            vh = cov / sum(x[1] / mp[x[0]] for x in P if mp.get(x[0], 0) > 0)      # 값 있는 링크의 조화 평균 km/h
            t_its = sum(x[1] / ((mp[x[0]] if mp.get(x[0], 0) > 0 else vh) / 3.6) for x in P)
            w, miss = 0.0, 0
            for no, hd in sigs:
                rc = sig_wait(SD, no, hd, t)
                if not rc:
                    miss += 1
                    continue
                r, C = rc
                w += r * r / (2 * C) + (r / C) * ACC
            mv = t_lim - 2 * ACC
            rows.append({'id': s['id'], 'kind': dname(t, hol), 'h': t.hour, 'band': band(t.hour), 'its': t_its, 'lim': t_lim, 'sig': t_lim + w, 'miss': miss, 'ns': len(sigs),
                         'f': max(0.8, (t_its - w - 2 * ACC) / mv) if mv > 0 and miss == 0 else None})   # 신호 값을 다 아는 줄만 배율에
    if not rows:
        print('맞댈 ITS 기록이 없다'); return 1
    os.makedirs(OUT, exist_ok=True)
    cells = {}
    for r in rows:
        c = cells.setdefault((r['kind'], r['band']), {'its/lim': [], 'its/sig': [], 'n': 0})
        c['n'] += 1; c['its/lim'].append(r['its'] / r['lim']); c['its/sig'].append(r['its'] / r['sig'])
    f2 = lambda x: '-' if x is None else '%.2f' % x
    days = sorted(set(os.path.basename(f)[:8] for f in glob.glob(os.path.join(RAW, 'out', 'livespd', '*.jsonl.gz')) if d0 <= os.path.basename(f)[:8] <= d1))
    md = ['# 주행시간 보정 — ITS 실측 ↔ 우리 계산 (%s)' % dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M'), '',
          '구간 %d개 · 맞댄 줄 %d · ITS 받은 날 %s · 비율 = 실측(ITS) ÷ 우리 계산(1보다 크면 실제가 더 걸림)' % (len(nsig), len(rows), ', '.join(days)), '',
          '| 요일 | 시간대 | 줄 수 | ÷제한속도만 가운데 | ÷제한속도+신호 25% | 가운데 | 75% |', '|---|---|---|---|---|---|---|']
    order = ['출근 07~09', '낮 10~16', '퇴근 17~19', '저녁 20~22', '밤 23~06']
    for kd in ('평일', '토', '일·공휴'):
        for b in order:
            c = cells.get((kd, b))
            if c:
                md.append('| %s | %s | %d | %s | %s | %s | %s |' % (kd, b, c['n'], f2(q(c['its/lim'], .5)), f2(q(c['its/sig'], .25)), f2(q(c['its/sig'], .5)), f2(q(c['its/sig'], .75))))
    md += ['', '## 구간별 (모든 시각 · 가운데값)', '', '| 구간 | 길 | 출발 → 도착 | 지나는 신호 | 줄 | 실측 초 | 제한속도 초 | +신호 초 | 실측÷(+신호) |', '|---|---|---|---|---|---|---|---|---|']
    for s in segs:
        rr = [r for r in rows if r['id'] == s['id']]
        if not rr:
            md.append('| %s | %s | %s → %s | %d | 0 | ITS 값 모자람 | | | |' % (s['id'], s['road'], s['from'], s['to'], nsig.get(s['id'], 0)))
            continue
        md.append('| %s | %s | %s → %s | %d | %d | %d | %d | %d | %s |' % (s['id'], s['road'], s['from'], s['to'], rr[0]['ns'], len(rr), q([r['its'] for r in rr], .5),
                                                                     rr[0]['lim'], q([r['sig'] for r in rr], .5), f2(q([r['its'] / r['sig'] for r in rr], .5))))
    miss = sum(r['miss'] for r in rows); tot = sum(r['ns'] for r in rows)
    md += ['', '신호 값을 못 찾은 교차로 %d / %d 회(그 교차로는 기다림 0 으로 셈 — 우리 계산이 짧게 나오는 쪽)' % (miss, tot),
           '', '읽는 법: 「÷제한속도+신호」가 1 근처면 우리 계산(신호 반영)이 실측과 맞는다 · 시간대별로 1 에서 먼 만큼이 보정값 후보(지도·가르고에 넣기 전 소유자 승인).',
           'ITS 통행속도는 링크 평균이라 신호 대기·막힘이 다 들어 있다 · 우리 계산은 아무 때나 닿는다고 본 평균 기다림(연동 안 셈)이라 녹색 물결이 맞는 축에서는 실측이 더 짧을 수 있다.']
    open(os.path.join(OUT, 'report.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    json.dump({'schema': 'eta-cal-its/1', 'made': dt.datetime.now(KST).isoformat(timespec='seconds'), 'days': days,
               'cells': [{'kind': k[0], 'band': k[1], 'n': c['n'], 'its_over_lim_p50': q(c['its/lim'], .5), 'its_over_sig': [q(c['its/sig'], .25), q(c['its/sig'], .5), q(c['its/sig'], .75)]} for k, c in sorted(cells.items())]},
              open(os.path.join(OUT, 'cells.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if '--bake' in sys.argv:
        bake(rows, days, hol)
    print('\n'.join(md[:22]))
    print('→', os.path.join(OUT, 'report.md'))
    return 0


BANDS = [('출근', 7, 10), ('낮', 10, 17), ('퇴근', 17, 20), ('저녁', 20, 23), ('밤', 23, 7)]
KINDS = ['평일', '토', '일·공휴']


def bake(rows, days, hol):
    """요일 갈래 × 시간대 「주행 배율」 — 줄이 30 아래인 칸은 비우고, 읽는 쪽이 정한 차례(토 → 일·공휴 → 평일 · 출근 → 낮)로 메운다(fill 에 적음)"""
    tab, n = {}, {}
    for kd in KINDS:
        for nm, a, b in BANDS:
            bb = {'출근': '출근 07~09', '낮': '낮 10~16', '퇴근': '퇴근 17~19', '저녁': '저녁 20~22', '밤': '밤 23~06'}[nm]
            v = [r['f'] for r in rows if r['kind'] == kd and r['band'] == bb and r['f']]
            n[kd + '|' + nm] = len(v)
            if len(v) >= 30:
                tab[kd + '|' + nm] = round(min(2.5, q(v, .5)), 2)
    fill = {}
    for kd in KINDS:
        for nm, a, b in BANDS:
            k = kd + '|' + nm
            if k in tab:
                continue
            for alt in ([('일·공휴', nm)] if kd == '토' else []) + [(kd, '낮' if nm == '출근' else nm), ('평일', nm)]:
                ak = alt[0] + '|' + alt[1]
                if ak in tab:
                    fill[k] = ak
                    break
    y0 = dt.datetime.now(KST).year
    hd = sorted(d for d in hol if d[:4] in (str(y0), str(y0 + 1)))
    out = {'schema': 'tg-eta-cal/1', 'made': dt.datetime.now(KST).strftime('%Y-%m-%d %H:%M'),
           'source': '국가교통정보센터(ITS) 통행속도 — 이 PC 가 약 22분마다 받아 쌓은 것(07_API키/out/livespd) · 신호 = data/sigdir-seoul.json · 길 = data/nav-seocho.json · 굽는 도구 tools/signal/etacal-its.py --bake',
           'how': '서초 간선 고정 구간 28개(교차로 사이)마다 실측 시간(ITS 링크 통행속도) − 신호 기다림(방향별 직진 적색 r²/2C + 설 확률 × 4초) − 출발·정지 4초×2 를 제한속도 주행 시간으로 나눈 값의 가운데값 · 0.8 아래는 0.8 · 2.5 위는 2.5',
           'use': '실시간 통행속도가 없는 줄을 제한속도 ÷ f 로 달린다고 본다(신호 기다림은 따로 셈) · 중요업무(정속 가정)에는 쓰지 않는다',
           'fields': 'f{「요일 갈래|시간대」: 주행 배율(제한속도 주행 시간 × f = 실측에서 신호 기다림·가감속을 뺀 시간)} · n{같은 칸: 맞댄 줄 수(30 아래면 f 없음)} · fill{빈 칸: 대신 쓸 칸} · bands[[이름, 시작 시, 끝 시]] · kinds[요일 갈래] · holidays[일·공휴로 볼 날]', 'days': days, 'bands': [[nm, a, b] for nm, a, b in BANDS], 'kinds': KINDS, 'f': tab, 'n': n, 'fill': fill, 'holidays': hd,
           'note': '서초 간선 28구간에서 잰 값을 다른 곳에도 쓴다(근사) · 토요일 등 줄이 모자란 칸은 fill 의 칸 값을 쓴다 · 이레 넘게 쌓일 때마다 다시 굽는다'}
    json.dump(out, open(os.path.join(ROOT, 'data', 'eta-cal.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('→ data/eta-cal.json', tab, 'fill', fill)


if __name__ == '__main__':
    sys.exit(main())
