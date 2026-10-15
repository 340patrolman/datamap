# -*- coding: utf-8 -*-
# 역 사이 시간 메우기 — 서울 열린데이터 「서울시 역코드로 지하철역별 열차 시간표」(SearchSTNTimeTableByIDService · 열차 번호 있음)
#   (2026-10-16 · 게임 세션이 찾은 역 이음 구멍: TAGO 역별 시간표가 2호선 성수지선(용답·신답·용두·신설동)·신정지선(도림천·양천구청·신정네거리·까치산)은 0줄,
#    7호선 장암은 한 방향뿐 → subreach-bake 가 그 구간 시간을 못 읽었다)
#   같은 열차 번호가 두 역을 떠난 시각 차이 = 그 구간 시간(정차 포함) · 평일(WEEK_TAG 1) 가운데값 · 노선 하나를 통째로 받아 열차마다 「바로 다음 역」만 잇는다
#   받기: py -3.12 -X utf8 tools/region/subtt-seoul.py fetch [호선 02 07]   → 07_API키/out/subfreq/seoul_tt/<역코드>_<1|2>.json(키 seoul · http 만)
#   굽기: py -3.12 -X utf8 tools/region/subtt-seoul.py build             → 07_API키/out/subfreq/seoul_links.json [[TAGO 역 ID, 다음 역 ID, 분, 열차 수]] — subreach-bake 가 TAGO 로 못 읽은 이음에만 쓴다
import sys, os, json, time, glob, statistics, collections, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(KB, 'out', 'subfreq', 'seoul_tt')
LINES = {'02': '2호선', '07': '7호선'}


def g(path):
    K = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['seoul']
    for n in range(3):
        try:
            return json.loads(urllib.request.urlopen('http://openapi.seoul.go.kr:8088/%s/json/%s' % (K, path), timeout=60).read())
        except Exception:
            time.sleep(3 + 4 * n)
    return {}


def fetch(lines):
    os.makedirs(OUT, exist_ok=True)
    st = []
    for ln in lines:   # 호선 역 목록 — 역명 검색에 빈 글이 안 되어 호선 이름으로
        d = g('SearchSTNBySubwayLineInfo/1/300/%%20/%%20/%s' % urllib.parse.quote(ln + '호선'))
        rows = (d.get('SearchSTNBySubwayLineInfo') or {}).get('row') or []
        st += rows; print(ln, '역', len(rows), flush=True)
    json.dump(st, open(os.path.join(OUT, 'stations.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for s in st:
        for io in '12':
            p = os.path.join(OUT, '%s_%s.json' % (s['STATION_CD'], io))
            if os.path.exists(p):
                continue
            rows = []
            for a in range(1, 2001, 1000):
                d = g('SearchSTNTimeTableByIDService/%d/%d/%s/1/%s/' % (a, a + 999, s['STATION_CD'], io))
                r = (d.get('SearchSTNTimeTableByIDService') or {}).get('row') or []
                rows += [[x['TRAIN_NO'], x['LEFTTIME'], x['ARRIVETIME']] for x in r]
                if len(r) < 1000:
                    break
            json.dump(rows, open(p, 'w', encoding='utf-8'), ensure_ascii=False); time.sleep(0.25)
    print('받음', len(glob.glob(os.path.join(OUT, '*_?.json'))))


def sec(t):
    try:
        h, m, s = map(int, t.split(':'))
    except Exception:
        return None
    v = h * 3600 + m * 60 + s
    return v + 86400 if h < 4 else v


def build():
    st = json.load(open(os.path.join(OUT, 'stations.json'), encoding='utf-8'))
    nm = {s['STATION_CD']: (s['STATION_NM'].split('(')[0].strip(), s['LINE_NUM']) for s in st}
    run = collections.defaultdict(list)   # (inout, 열차) → [(초, 역)]
    for f in glob.glob(os.path.join(OUT, '*_?.json')):
        cd, io = os.path.basename(f)[:-5].rsplit('_', 1)
        if cd not in nm:
            continue
        for tr, lv, ar in json.load(open(f, encoding='utf-8')):
            t = sec(lv) if lv and lv != '00:00:00' else sec(ar)
            if t is not None:
                run[(io, tr)].append((t, cd))
    gap = collections.defaultdict(list)
    for v in run.values():
        v.sort()
        for (t1, a), (t2, b) in zip(v, v[1:]):
            if a != b and 20 <= t2 - t1 <= 900:
                gap[(a, b)].append(t2 - t1)
    T = json.load(open(os.path.join(KB, 'out', 'subfreq', 'stations.json'), encoding='utf-8'))
    tago = collections.defaultdict(list)
    base = lambda s: (s.split('(')[0].strip()[:-1] if s.split('(')[0].strip().endswith('역') and len(s.split('(')[0].strip()) > 2 else s.split('(')[0].strip())
    for s in T:
        tago[(s['subwayRouteName'], base(s['subwayStationName']))].append(s['subwayStationId'])
    out, miss = [], set()
    for (a, b), v in gap.items():
        if len(v) < 5:
            continue   # 한두 편만 지나는 짝(회송·되돌이)은 안 씀
        la = '%d호선' % int(nm[a][1][:2]); ta, tb = tago.get((la, base(nm[a][0]))), tago.get((la, base(nm[b][0])))
        if not ta or not tb:
            miss.add(nm[a][0] if not ta else nm[b][0]); continue
        for x in ta:
            for y in tb:
                out.append([x, y, round(statistics.median(v) / 60, 1), len(v)])
    p = os.path.join(KB, 'out', 'subfreq', 'seoul_links.json')
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('이음', len(out), '· TAGO 이름 못 맞춘 역', sorted(miss)[:20])


if __name__ == '__main__':
    a = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if a == 'fetch':
        fetch([x for x in sys.argv[2:] if x.isdigit()] or list(LINES))
    else:
        build()
