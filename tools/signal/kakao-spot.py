# -*- coding: utf-8 -*-
"""카카오 길찾기로 「지금 한 번 맞춰 보기」(2026-10-15 소유자 「카카오는 보조 · 대신 맞춰 볼 수는 있지? 영 틀릴 수가 있거든」)

카카오 결과는 저장하지 않는다(카카오 개발자 게시판 답 「임시 캐싱 등의 방법으로 API 호출 및 이용은 금지」 · 「요청 처리 시점에 일회성으로 참조」만).
  → 고정 구간(07_API키/kakao_eta_segments.json · 서초 간선 28 · 실사건 좌표 아님)을 지금 묻고, 같은 시각 우리 계산(제한속도 + 신호 기다림 · etacal-its.py 와 같은 식)
    과 가장 최근 ITS 실측(30분 안)을 나란히 화면에만 찍고 끝낸다. 파일에 쓰는 것은 하루 호출 수(07_API키/out/kakao_eta/day.json · 숫자 하나)뿐.
  하루 무료 10,000 의 90% 에서 멈춤 · 401/403/429 면 바로 멈춤 · 열쇠는 07_API키/keys.json 「kakao_navi」(출력하지 않는다)
  py -3.12 -X utf8 tools/signal/kakao-spot.py [S01 S07 …]      (구간을 안 적으면 28개 모두)
"""
import sys, os, json, time, urllib.request, urllib.parse, urllib.error, importlib.util, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('etacal', os.path.join(HERE, 'etacal-its.py'))
E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)
RAW, KST = E.RAW, E.KST
DAY = os.path.join(RAW, 'out', 'kakao_eta', 'day.json')
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
        ours = sum(x[1] / (x[2] / 3.6) for x in P) + 2 * E.ACC
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
        print('%-4s %-6s %-30s %6s초 %6d초 %7s %6s' % (s['id'], s['road'], (s['from'] + '→' + s['to'])[:30], kd if kd else '-', ours,
                                                  ('%d초' % its) if its else '-', ('%.2f' % r9) if r9 else '-'))
        time.sleep(0.3)
    if rat:
        rat.sort()
        print('가운데 비율 %.2f (%d구간) · 1.3 넘게 벌어지면 우리 계산이 이 시각 실제보다 짧게 잡는다는 뜻 · 오늘 카카오 호출 %d건' % (rat[len(rat) // 2], len(rat), day_book()))
    return 0


if __name__ == '__main__':
    sys.exit(main())
