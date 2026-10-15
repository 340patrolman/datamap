# -*- coding: utf-8 -*-
"""카카오 길찾기로 「지금 한 번 맞춰 보기」(2026-10-15 소유자 「카카오는 보조 · 대신 맞춰 볼 수는 있지? 영 틀릴 수가 있거든」)

카카오 결과는 저장하지 않는다(카카오 개발자 게시판 답 「임시 캐싱 등의 방법으로 API 호출 및 이용은 금지」 · 「요청 처리 시점에 일회성으로 참조」만).
  → 고정 구간(07_API키/kakao_eta_segments.json · 서초 간선 28 · 실사건 좌표 아님)을 지금 묻고, 같은 시각 우리 계산(제한속도 + 신호 기다림 · etacal-its.py 와 같은 식)
    과 가장 최근 ITS 실측(30분 안)을 나란히 화면에 찍는다 · --save 면 「카카오 ÷ 우리」 비율만 묶음 칸에(compare_acc.py · 시각·우리 값 없이 · 소유자 2026-10-15 「묶은 값만」) · 그 밖에 쓰는 것은 하루 호출 수(day.json).
  하루 무료 10,000 의 90% 에서 멈춤 · 401/403/429 면 바로 멈춤 · 열쇠는 07_API키/keys.json 「kakao_navi」(출력하지 않는다)
  py -3.12 -X utf8 tools/signal/kakao-spot.py [S01 S07 …] [--save]      (구간을 안 적으면 28개 모두)
"""
import sys, os, json, time, urllib.request, urllib.parse, urllib.error, importlib.util, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('etacal', os.path.join(HERE, 'etacal-its.py'))
E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
RAW, KST = E.RAW, E.KST
DAY = os.path.join(RAW, 'out', 'kakao_eta', 'day.json')


def E_calF(t):
    """그 시각 막힘 배율(data/eta-cal.json) — 비교 줄에 같이 남겨 보정 전후를 가를 수 있게"""
    try:
        j = json.load(open(os.path.join(E.ROOT, 'data', 'eta-cal.json'), encoding='utf-8'))
        kd = '일·공휴' if t.strftime('%Y-%m-%d') in j.get('holidays', []) or t.weekday() == 6 else '토' if t.weekday() == 5 else '평일'
        h = t.hour; bd = '출근' if 7 <= h < 10 else '낮' if 10 <= h < 17 else '퇴근' if 17 <= h < 20 else '저녁' if 20 <= h < 23 else '밤'
        k = kd + '|' + bd; return j['f'].get(k) or j['f'].get(j.get('fill', {}).get(k, ''), 1)
    except Exception:
        return 1
CAP = 9000
URL = 'https://apis-navi.kakaomobility.com/v1/directions'


def day_book(add=0):
    today = dt.datetime.now(KST).strftime('%Y-%m-%d')
    try:
        b = json.load(open(DAY, encoding='utf-8'))
    except Exception:
        b = {}
    if b.get('date') != today:
        b = {'date': today, 'calls': 0}
    b['calls'] += add
    os.makedirs(os.path.dirname(DAY), exist_ok=True)
    json.dump(b, open(DAY, 'w', encoding='utf-8'))
    return b['calls']


def save_row(kind, row):
    """대조 한 번 → 묶음 칸에 비율만(compare_acc.py · 시각·우리 값은 안 남김 · 소유자 결정 2026-10-15 「묶은 값만」)"""
    if '--save' not in sys.argv:
        return
    import importlib.util as iu
    sp = iu.spec_from_file_location('compare_acc', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compare_acc.py')); A = iu.module_from_spec(sp); sp.loader.exec_module(A)
    try:
        hol = set(json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'eta-cal.json'), encoding='utf-8')).get('holidays', []))
    except Exception:
        hol = set()
    t = dt.datetime.fromisoformat(row['t'])
    if kind == 'route':
        same = min(row['ov_k'], row['ov_g']) >= 0.7
        A.add('route', t, row['pair'], {'rt': row['rt'], 'rd': row['rd'], 'ovk': row['ov_k'], 'ovg': row['ov_g'], 'rts': row['rt'] if same else None, 'far': bool(row['far']), 'same': same}, hol)
    else:
        A.add('seg', t, row['id'], {'rk': row['rk'], 'rkc': row.get('rkc')}, hol)

def main():
    key = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig')).get('kakao_navi')
    if not key:
        print('keys.json 에 kakao_navi 가 없다'); return 1
    segs = json.load(open(os.path.join(RAW, 'kakao_eta_segments.json'), encoding='utf-8'))['segments']
    want = [a for a in sys.argv[1:] if a.startswith('S')]
    if want:
        segs = [s for s in segs if s['id'] in want]
    if day_book() + len(segs) > CAP:
        print('오늘 카카오 호출이 한도의 90% 에 닿았다 — 내일 다시'); return 1
    N, L = E.load_graph()
    SD = json.load(open(os.path.join(E.ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))['its']
    now = dt.datetime.now(KST)
    S = E.load_spd(now.strftime('%Y%m%d'), now.strftime('%Y%m%d'))
    snap = S[-1] if S and abs(S[-1][0] - now.timestamp()) <= 1800 else None
    print('카카오 맞춰 보기 %s · 비율 = 카카오 ÷ 우리 계산(제한속도+신호) · 카카오 값은 저장하지 않는다' % now.strftime('%Y-%m-%d %H:%M'))
    print('ITS 실측: %s' % (dt.datetime.fromtimestamp(snap[0], KST).strftime('%H:%M 받음') if snap else '30분 안 받은 것 없음'))
    print('%-4s %-6s %-30s %7s %7s %7s %6s' % ('구간', '길', '출발 → 도착', '카카오', '우리', 'ITS', '비율'))
    rat = []
    for s in segs:
        ids = s['its_links']
        if any(l not in L for l in ids):
            continue
        P = [(lid, L[lid]['m'] * ((E.F1 - E.F0) if len(ids) == 1 else (1 - E.F0) if i == 0 else E.F1 if i == len(ids) - 1 else 1.0), L[lid]['lim']) for i, lid in enumerate(ids)]
        m = sum(x[1] for x in P)
        mv = sum(x[1] / (x[2] / 3.6) for x in P); ours = mv + 2 * E.ACC
        seen = None
        for lid in ids:
            no = N.get(L[lid]['t'])
            if no and no != seen:
                seen = no
                rc = E.sig_wait(SD, no, L[lid]['hd'], now)
                if rc:
                    ours += rc[0] * rc[0] / (2 * rc[1]) + rc[0] / rc[1] * E.ACC
        its = None
        if snap:
            mp = snap[1]
            cov = sum(x[1] for x in P if mp.get(x[0], 0) > 0)
            if cov >= 0.4 * m:
                vh = cov / sum(x[1] / mp[x[0]] for x in P if mp.get(x[0], 0) > 0)
                its = sum(x[1] / ((mp[x[0]] if mp.get(x[0], 0) > 0 else vh) / 3.6) for x in P)
        o, d = s['origin'], s['dest']
        qs = urllib.parse.urlencode({'origin': '%s,%s,angle=%s' % (o['lon'], o['lat'], o['angle']), 'destination': '%s,%s,angle=%s' % (d['lon'], d['lat'], d['angle']), 'priority': 'TIME'}, safe=',=')
        kd = None
        try:
            with urllib.request.urlopen(urllib.request.Request(URL + '?' + qs, headers={'Authorization': 'KakaoAK ' + key}), timeout=20) as r:
                j = json.loads(r.read().decode('utf-8'))
            day_book(1)
            x = (j.get('routes') or [{}])[0]
            if x.get('result_code') == 0:
                kd = x['summary']['duration']
        except urllib.error.HTTPError as e:
            day_book(1)
            print('카카오 오류 %s — 멈춤' % e.code)
            if e.code in (401, 403, 429):
                return 1
        except Exception as e:
            print('통신 오류 —', str(e)[:80])
        r9 = kd / ours if kd else None
        if r9:
            rat.append(r9)
        if r9:
            save_row('seg', {'t': now.isoformat(timespec='seconds'), 'id': s['id'], 'ours': round(ours), 'its': round(its) if its else None, 'rk': round(r9, 3), 'calF': round(E_calF(now), 3), 'rkc': round(kd / (ours + mv * (E_calF(now) - 1)), 3)})   # rkc = 카카오 ÷ 막힘 배율을 곱한 우리 계산(지도·가르고가 실시간 없을 때 쓰는 값)
        print('%-4s %-6s %-30s %6s초 %6d초 %7s %6s' % (s['id'], s['road'], (s['from'] + '→' + s['to'])[:30], kd if kd else '-', ours,
                                                  ('%d초' % its) if its else '-', ('%.2f' % r9) if r9 else '-'))
        time.sleep(0.3)
    if rat:
        rat.sort()
        print('가운데 비율 %.2f (%d구간) · 1.3 넘게 벌어지면 우리 계산이 이 시각 실제보다 짧게 잡는다는 뜻 · 오늘 카카오 호출 %d건' % (rat[len(rat) // 2], len(rat), day_book()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
