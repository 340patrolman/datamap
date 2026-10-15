# -*- coding: utf-8 -*-
"""선착 역(열차 안 신고 — 열차보다 먼저 닿을 역) 계산에 쓰는 한 장 — 수도권 지하철 역 · 역 사이 시간 · 역 자리 · 출입구 · 시간대 승하차 몫

이미 있는 자료만 엮는다(새로 부르지 않음):
  역 이음·역 사이 분 = data/subway-reach.json(TAGO 평일 시간표에서 읽은 출발 → 출발 · 정차 포함 · 추정)
  역 자리 = data/r/stations.json(서울시 역사마스터 · 역 대표 점) · 서울 밖 역은 data/stations-kr.json
  출입구 = data/exits-kr.json(OpenStreetMap · ODbL) — 역 자리 600m 안 · 이름 앞부분이 같은 것
  시간대 몫 = data/subway-hour-seoul.json(OA-12252 · 달 합계라 평일·주말 섞임)
  py -3.12 -X utf8 tools/region/trainrun-bake.py
"""
import os, json, math, re, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
J = lambda p: json.load(open(os.path.join(ROOT, 'data', p), encoding='utf-8'))
OUT = os.path.join(ROOT, 'data', 'train-run-seoul.json')
base = lambda s: re.sub(r'\(.*?\)', '', s or '').strip()
digit = lambda s: (re.match(r'(\d+)', s or '') or [None, None])[1]


def dist(a, b, c, d):
    return math.hypot((a - c) * 111000, (b - d) * 88000)


def main():
    R, S1, S2, E, HR = J('subway-reach.json'), J('r/stations.json')['items'], J('stations-kr.json'), J('exits-kr.json')['pts'], J('subway-hour-seoul.json')['stn']
    S2 = S2.get('items', S2) if isinstance(S2, dict) else S2
    pos = {}
    for it in list(S1) + [x for x in S2 if isinstance(x, list)]:
        pos.setdefault(base(it[0]), []).append((str(it[1]), float(it[2]), float(it[3])))   # (노선, 경도, 위도)
    hr = {(q[0], q[1]): q for q in HR}
    keep = [s for s in R['stn'] if s[3] == '']
    st, idx, miss = [], {}, []
    for s in keep:
        nm, ln = s[1], s[2]; C = pos.get(base(nm), []); dg = digit(ln)
        pick = [c for c in C if dg and digit(c[0]) == dg] or [c for c in C if ln[:2] in c[0]] or (C if C and all(dist(c[2], c[1], C[0][2], C[0][1]) < 1500 for c in C) else [])   # 노선 표기가 달라도(경부선 = 1호선 등) 같은 이름 점이 한자리에 모여 있으면 그 자리
        if not pick:
            miss.append(nm + ' ' + ln); lon = lat = None
        else:
            lon, lat = pick[0][1], pick[0][2]
        h = hr.get((nm, ln)) or next((q for (n2, l2), q in hr.items() if n2 == nm and l2.startswith(ln[:2])), None)
        ex = []
        if lat:
            for e in E:
                if abs(e[0] - lat) < 0.007 and abs(e[1] - lon) < 0.009 and dist(e[0], e[1], lat, lon) < 600 and (not e[3] or base(e[3]).startswith(base(nm)[:2])):
                    ex.append([e[2] or '', round(e[0], 6), round(e[1], 6)])
        idx[s[0]] = len(st)
        st.append([s[0], nm, ln, round(lat, 6) if lat else None, round(lon, 6) if lon else None, h[5] if h else None, h[2] if h else None, ex])
    lk = []
    for l in R['links']:
        if l[0] in idx and l[1] in idx:
            lk.append([idx[l[0]], idx[l[1]], round(l[2] * 60), 1 if l[3] >= 0 else 0])
    doc = {'schema': 'tg-train-run/1', 'made': datetime.date.today().isoformat(),
           'source': '역 이음·역 사이 시간 = data/subway-reach.json(국토교통부 TAGO 지하철 평일 시간표에서 읽은 추정) · 역 자리 = 서울시 역사마스터(data/r/stations.json)·data/stations-kr.json · 출입구 = OpenStreetMap(© OpenStreetMap contributors · ODbL · data/exits-kr.json) · 시간대 승하차 몫 = 서울 열린데이터광장 OA-12252(data/subway-hour-seoul.json) — 굽는 도구 tools/region/trainrun-bake.py',
           'fields': 'st[[역 ID, 역 이름, 노선, 위도, 경도, [0~23시 승하차 몫 — 그 역 5~24시 평균 = 1 · 없으면 null], 하루 평균 승하차|null, [[출구 번호, 위도, 경도]]]] · lk[[역 번호, 다음 역 번호, 초(앞 역 출발 → 다음 역 출발 · 정차 포함), 1 = 역간거리 파일과 맞은 이음 · 0 = 한 역을 건너뛸 수 있는 메움]]',
           'note': ['역 사이 시간은 시간표 출발 시각 차이로 읽은 추정(정차 포함 · 운영사 소요시간표 아님) · 급행을 가르지 못함',
                    '정차 시간(문 열림)은 따로 없다 — 쓰는 쪽에서 가정값(30초)으로 떼어 쓴다',
                    '출입구는 OSM 자원봉사 지도라 빠진 곳·번호 없는 곳이 있다',
                    '시간대 몫은 달 합계(평일·주말 섞임)'],
           'miss': miss, 'st': st, 'lk': lk}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('역', len(st), '· 이음', len(lk), '· 자리 못 찾음', len(miss), '· 몫 있음', sum(1 for x in st if x[5]), '· 출구 있음', sum(1 for x in st if x[7]), '·', os.path.getsize(OUT), 'B')
    print('못 찾음 예:', miss[:15])
    for x in st:
        if x[1] in ('교대(법원.검찰청)', '고속터미널', '방배'):
            print(' ', x[1], x[2], x[3], x[4], '몫' if x[5] else '-', '출구', len(x[7]), [e[0] for e in x[7]][:12])


if __name__ == '__main__':
    main()
