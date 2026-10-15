# -*- coding: utf-8 -*-
"""카카오 길찾기 예상 시간 ↔ 우리 계산 비교(2026-10-15 · 코워크 전달 「카카오 길찾기 보정 측정」 할 일 2)

같은 고정 구간 28개(07_API키/kakao_eta_segments.json · 실사건 좌표 아님)를 같은 ITS 링크 위에서 두 잣대로 셈해 카카오 dur 와 맞댄다.
  ① 제한속도 — 링크 길이 ÷ 제한속도 + 출발·정지 가감속(travel-time.js accS 4초 × 2) — 「막힘 없는」 바닥값
  ② ITS 그 시각 — 같은 링크의 ITS 통행속도(07_API키/out/livespd/<날짜>.jsonl.gz · 카카오 측정 시각 ±20분 안 가장 가까운 받음) · 값 없는 링크는 제한속도
  거리는 출발점(첫 링크 30%)·도착점(끝 링크 70%)에 맞춰 첫·끝 링크를 잘라 쓴다(굽는 도구 kakao_eta_segbake.py 와 같은 규칙).
  ③ 신호 반영(가르고 계산)은 다음 단계 — 이레 넘게 쌓인 뒤 가르고 길 계산을 머리 없는 크롬으로 같은 구간에 돌려 붙인다.

읽기만 한다 · 열쇠를 읽지 않는다 · 결과는 저장소 밖 07_API키/out/kakao_eta/compare.md · compare.json(카카오 결과를 공개 저장소에 싣지 않는다 — 약관 확인 전)
  py -3.12 -X utf8 tools/signal/kakaoeta-compare.py [--from YYYY-MM-DD] [--to YYYY-MM-DD]
"""
import sys, os, json, gzip, glob, bisect, statistics, datetime as dt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # datamap
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(RAW, 'out', 'kakao_eta')
ACC = 4          # travel-time.js accS — 처음 출발·마지막 정지 한 번씩
F0, F1 = 0.30, 0.70
WIN = 20 * 60    # ITS 받음과 카카오 측정의 허용 시차(초)
KST = dt.timezone(dt.timedelta(hours=9))


def arg(k, d=None):
    return sys.argv[sys.argv.index(k) + 1] if k in sys.argv else d


def load_links():
    L = {}
    for f in ('nav-seocho', 'nav-arterial'):
        p = os.path.join(ROOT, 'data', f + '.json')
        if not os.path.exists(p):
            continue
        for q in json.load(open(p, encoding='utf-8'))['links']:
            L.setdefault(q[0], (q[3] or 1, q[4] or 0, q[7] or ''))
    return L


def load_hol():
    p = os.path.join(ROOT, 'data', 'holidays.json')
    try:
        j = json.load(open(p, encoding='utf-8'))
    except Exception:
        return set()
    d = j.get('days') or j.get('holidays') or j
    if isinstance(d, dict):
        return set(d.keys())
    return set(x if isinstance(x, str) else x.get('d', '') for x in d)


def day_kind(t, hol):
    ds = t.strftime('%Y-%m-%d')
    if ds in hol or t.weekday() == 6:
        return '일·공휴'
    return '토' if t.weekday() == 5 else ('금' if t.weekday() == 4 else '월~목')


def load_spd(d0, d1):
    S = []   # [(epoch, {link: kmh})]
    for f in sorted(glob.glob(os.path.join(RAW, 'out', 'livespd', '*.jsonl.gz'))):
        day = os.path.basename(f)[:8]
        if day < d0.replace('-', '') or day > d1.replace('-', ''):
            continue
        for ln in gzip.open(f, 'rt', encoding='utf-8'):
            try:
                j = json.loads(ln)
                m = j['m'] if isinstance(j['m'], dict) else json.loads(j['m'])
                S.append((int(j['at']), m))
            except Exception:
                continue
    S.sort(key=lambda x: x[0])
    return S


def near(S, ts):
    if not S:
        return None
    ks = [x[0] for x in S]
    i = bisect.bisect_left(ks, ts)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(S) and abs(S[j][0] - ts) <= WIN and (best is None or abs(S[j][0] - ts) < abs(best[0] - ts)):
            best = S[j]
    return best


def parts(seg, L):
    out = []
    ids = seg['its_links']
    for i, lid in enumerate(ids):
        if lid not in L:
            return None
        m, lim, nm = L[lid]
        fr = 1.0
        if len(ids) == 1:
            fr = F1 - F0
        elif i == 0:
            fr = 1 - F0
        elif i == len(ids) - 1:
            fr = F1
        out.append((lid, m * fr, lim or 50))
    return out


def q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    a = int(k)
    b = min(a + 1, len(v) - 1)
    return v[a] + (v[b] - v[a]) * (k - a)


def main():
    d0 = arg('--from', '2000-01-01')
    d1 = arg('--to', '2999-12-31')
    segs = {s['id']: s for s in json.load(open(os.path.join(RAW, 'kakao_eta_segments.json'), encoding='utf-8'))['segments']}
    L = load_links()
    hol = load_hol()
    S = load_spd(d0, d1)
    rows = []
    for f in sorted(glob.glob(os.path.join(OUT, '20*.jsonl'))):
        day = os.path.basename(f)[:10]
        if day < d0 or day > d1:
            continue
        seen = set()
        for ln in open(f, encoding='utf-8'):
            j = json.loads(ln)
            if j.get('err') or not j.get('dur') or j['id'] not in segs:
                continue
            t = dt.datetime.fromisoformat(j['t'])
            key = (j['id'], t.strftime('%H%M'))
            if key in seen:          # 켤 때 한 회차가 두 번 돈 것(10-15 12:44) — 같은 분은 하나만
                continue
            seen.add(key)
            P = parts(segs[j['id']], L)
            if not P:
                continue
            m = sum(x[1] for x in P)
            t_lim = sum(x[1] / (x[2] / 3.6) for x in P) + 2 * ACC
            sn = near(S, int(t.timestamp()))
            t_its, cov = None, 0.0
            if sn:
                tt = 2 * ACC
                for lid, mm, lim in P:
                    v = sn[1].get(lid)
                    if v and v > 0:
                        cov += mm
                    tt += mm / ((v if v and v > 0 else lim) / 3.6)
                t_its, cov = tt, cov / m
            rows.append({'id': j['id'], 't': t, 'kind': day_kind(t, hol), 'h': t.hour, 'kd': j['dur'], 'km': j['dist'], 'om': m,
                         'lim': t_lim, 'its': t_its, 'cov': cov})
    if not rows:
        print('비교할 카카오 기록이 없다')
        return 1
    # 구간 × 요일 갈래 × 시 → 비율(카카오 ÷ 우리)
    agg = {}
    for r in rows:
        k = (r['id'], r['kind'], r['h'])
        a = agg.setdefault(k, {'n': 0, 'k_lim': [], 'k_its': [], 'kd': []})
        a['n'] += 1
        a['kd'].append(r['kd'])
        a['k_lim'].append(r['kd'] / r['lim'])
        if r['its'] and r['cov'] >= 0.5:
            a['k_its'].append(r['kd'] / r['its'])
    allL = [r['kd'] / r['lim'] for r in rows]
    allI = [r['kd'] / r['its'] for r in rows if r['its'] and r['cov'] >= 0.5]
    dd = [abs(r['km'] - r['om']) / r['om'] for r in rows]
    summ = {'schema': 'kakao-eta-compare/1', 'made': dt.datetime.now(KST).isoformat(timespec='seconds'), 'n': len(rows),
            'days': sorted(set(r['t'].strftime('%Y-%m-%d') for r in rows)),
            'ratio_kakao_over_limit': {'p25': q(allL, .25), 'p50': q(allL, .5), 'p75': q(allL, .75)},
            'ratio_kakao_over_its': {'n': len(allI), 'p25': q(allI, .25), 'p50': q(allI, .5), 'p75': q(allI, .75)},
            'dist_gap_p50': q(dd, .5),
            'cells': [{'id': k[0], 'kind': k[1], 'h': k[2], 'n': a['n'], 'kakao_p50': q(a['kd'], .5),
                       'k_lim_p50': q(a['k_lim'], .5), 'k_its_p50': q(a['k_its'], .5) if a['k_its'] else None}
                      for k, a in sorted(agg.items())],
            'note': '비율 = 카카오 예상 초 ÷ 우리 계산 초 · 1 보다 크면 카카오가 더 오래 걸린다고 본다 · ITS 값은 받은 링크 길이가 절반 넘을 때만 · 신호 반영(가르고) 잣대는 다음 단계'}
    json.dump(summ, open(os.path.join(OUT, 'compare.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    f2 = lambda x: '-' if x is None else '%.2f' % x
    md = ['# 카카오 예상 시간 ↔ 우리 계산 (%s)' % summ['made'][:16], '',
          '기록 %d건 · 날짜 %s · 비율 = 카카오 ÷ 우리(1보다 크면 카카오가 더 걸림)' % (len(rows), ', '.join(summ['days'])), '',
          '| 잣대 | 25% | 가운데 | 75% |', '|---|---|---|---|',
          '| ① 제한속도 | %s | %s | %s |' % tuple(f2(summ['ratio_kakao_over_limit'][k]) for k in ('p25', 'p50', 'p75')),
          '| ② ITS 그 시각 (%d건) | %s | %s | %s |' % ((len(allI),) + tuple(f2(summ['ratio_kakao_over_its'][k]) for k in ('p25', 'p50', 'p75'))), '',
          '거리 차이 가운데값 %.1f%% (카카오 거리 ↔ 잘라 쓴 ITS 링크 길이)' % (100 * summ['dist_gap_p50']), '',
          '## 구간별 (모든 시각)', '', '| 구간 | 길 | 출발 → 도착 | 건수 | 카카오 가운데 | ÷제한속도 | ÷ITS |', '|---|---|---|---|---|---|---|']
    for sid in sorted(segs):
        rr = [r for r in rows if r['id'] == sid]
        if not rr:
            continue
        s = segs[sid]
        ri = [r['kd'] / r['its'] for r in rr if r['its'] and r['cov'] >= 0.5]
        md.append('| %s | %s | %s → %s | %d | %d초 | %s | %s |' % (sid, s['road'], s['from'], s['to'], len(rr), q([r['kd'] for r in rr], .5),
                                                             f2(q([r['kd'] / r['lim'] for r in rr], .5)), f2(q(ri, .5))))
    open(os.path.join(OUT, 'compare.md'), 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    print('\n'.join(md[:12]))
    print('→', os.path.join(OUT, 'compare.md'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
