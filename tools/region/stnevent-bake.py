# -*- coding: utf-8 -*-
"""역 둘레 큰 행사 — 선착 역 계산(js/station-reach.js)의 「행사 가산」 바탕(2026-10-15 도착 예측 프롬프트 1단계 ③)

역(data/train-run-seoul.json · 자리 있는 역) 500m 안의
  · 공연 회차(data/venue-events-kopis.json · 그 홀 객석 500석 이상 · 끝 시각이 있는 회차) — 끝나는 시각 앞뒤에 사람이 역으로 몰린다
  · 집회(data/rally-seoul.json · 신고 인원 300명 이상 · 시작·끝 시각이 있는 것) — 신고 인원은 신고한 값이지 실제 모인 수가 아니다
를 오늘부터 60일(집회는 받아 둔 날까지) 묶는다. 사람 수를 역 혼잡 몫으로 바꾸는 식은 쓰는 쪽(가르고)에 가정값으로 둔다.
  py -3.12 -X utf8 tools/region/stnevent-bake.py        (rally-seoul·kopis 를 다시 구우면 같이 다시 — data-check 1일)
  2026-10-23 수도권 밖도 — 역 자리에 data/stations-kr.json(서울 자료와 겹치지 않는 전국 312역)을 더하고, 공연에 data/venue-events-kopis/<시도>.json(수도권 11·41·28 밖 시도)을 더한다 · 꼴은 그대로(역 이름 열쇠가 늘 뿐)
"""
import os, json, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = lambda p: json.load(open(os.path.join(ROOT, 'data', p), encoding='utf-8'))
OUT = os.path.join(ROOT, 'data', 'station-events.json')
R0, SEATS, PEOPLE, DAYS = 500, 500, 300, 60


def dist(a, b, c, d):
    return math.hypot((a - c) * 111000, (b - d) * 88000)


def main():
    T, K, RL = J('train-run-seoul.json'), J('venue-events-kopis.json'), J('rally-seoul.json')
    today = datetime.date.today(); last = (today + datetime.timedelta(days=DAYS)).isoformat(); t0 = today.isoformat()
    spots = {}
    for s in T['st']:
        if s[3]:
            b = s[1].split('(')[0]
            spots.setdefault(b, (s[3], s[4]))
    for s in J('stations-kr.json')['items']:
        b = str(s[0]).split('(')[0]
        if b not in spots and s[3] is not None:
            spots[b] = (s[3], s[2])
    KV = list(K['venues'])
    kdir = os.path.join(ROOT, 'data', 'venue-events-kopis')
    for fn in (sorted(os.listdir(kdir)) if os.path.isdir(kdir) else []):
        if fn.endswith('.json') and fn[:2].isdigit() and fn[:2] not in ('11', '41', '28'):
            KV += json.load(open(os.path.join(kdir, fn), encoding='utf-8')).get('venues', [])
    near = lambda la, lo, r=R0: sorted([b for b, q in spots.items() if abs(q[0] - la) < 0.012 and abs(q[1] - lo) < 0.015 and dist(q[0], q[1], la, lo) < r], key=lambda b: dist(spots[b][0], spots[b][1], la, lo))
    ev, nk, nr = {}, 0, 0
    for v in KV:
        if v.get('lat') is None:
            continue
        big = max([h[1] or 0 for h in v.get('halls', [])] + [0]) >= 1500
        S = near(v['lat'], v['lon'], 1000 if big else R0)   # 1,500석 넘는 홀이 있는 큰 공연장은 1km(예술의전당 ↔ 남부터미널 약 800m)
        if not S:
            continue
        for d in v.get('day', []):
            if not (t0 <= d[0] <= last) or not d[2]:
                continue
            sh = v['shows'][d[3]]; seats = sh[7] or 0
            if seats < SEATS:
                continue
            for b in S[:2]:
                ev.setdefault(b, []).append([d[0], 'p', d[1], d[2], seats, (v['n'] + ' · ' + sh[0])[:40]]); nk += 1
    for r in RL['items']:
        if r.get('lat') is None or not r.get('from') or not r.get('to') or (r.get('n') or 0) < PEOPLE or r['d'] < t0:
            continue
        S = near(r['lat'], r['lon'])
        if r.get('dest'):
            S += [b for b in near(r['dest'][0], r['dest'][1]) if b not in S]
        for b in S[:3]:
            ev.setdefault(b, []).append([r['d'], 'r', r['from'], r['to'], r['n'], ('집회 · ' + r['p'])[:40]]); nr += 1
    for b in ev:
        ev[b].sort()
    doc = {'schema': 'tg-station-events/1', 'made': datetime.date.today().isoformat(),
           'source': '공연 = (재)예술경영지원센터 KOPIS OpenAPI(data/venue-events-kopis.json · 수도권 밖은 venue-events-kopis/<시도>.json) · 집회 = 서울특별시경찰청 「오늘의 주요집회」(data/rally-seoul.json) · 역 자리 = data/train-run-seoul.json + data/stations-kr.json(전국) — 굽는 도구 tools/region/stnevent-bake.py',
           'fields': 'ev{역 이름(괄호 앞): [[날짜, p 공연|r 집회, 시작 HH:MM, 끝 HH:MM, 사람(공연 = 그 홀 객석 · 집회 = 신고 인원), 이름]]} — 역 500m 안(1,500석 넘는 홀이 있는 공연장은 1km) · 공연은 객석 %d석 이상 · 집회는 신고 %d명 이상' % (SEATS, PEOPLE),
           'note': ['객석은 다 찬다고 본 위쪽 끝이다 · 신고 인원은 실제 모인 수가 아니다 — 쓰는 쪽에서 가정값으로 줄여 쓴다', '집회는 경찰청이 올린 「주요 집회」만 · 받아 둔 날(rally-seoul collected)까지만', '공연 끝 시각은 시작 + 공연 시간(KOPIS 칸)으로 셈한 값'],
           'range': [t0, last], 'ev': ev}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('역', len(ev), '· 공연 회차', nk, '· 집회', nr, '·', os.path.getsize(OUT), 'B')
    for b in ('고속터미널', '교대', '남부터미널', '강남', '서초', '양재', '종각', '광화문', '시청'):
        if b in ev:
            print(' ', b, len(ev[b]), ev[b][:2])


if __name__ == '__main__':
    main()
