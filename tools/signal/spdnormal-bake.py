# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚗 「평소 속도」: 길 조각마다 요일 갈래 × 시각의 보통 통행속도(소유자 2026-10-11 온톨로지 「평소(바탕) + 지금(실시간) → 조치」 · 교통 사건의 앞뒤는 통행으로 잰다) → data/spd-normal-seocho.json
#   재료 = ../07_API키/out/livespd/<날짜>.jsonl.gz — tools/signal/livespd-bake.py 가 받을 때마다 한 줄씩 쌓은 것(국가교통정보센터 ITS 실시간 소통 · 약 10분마다 · 서초구 + 2km 의 큰길·신호 접근로)
#   링크 × 요일 갈래(0 월~목 · 1 금 · 2 토 · 3 일 — 신호 계획과 같은 갈래) × 시(0~23)마다 가운데값 · 아래 사분위(막힐 때) · 본 횟수
#   **쌓인 날이 적으면 「평소」가 아니다** — days(갈래마다 쌓인 날 수)를 같이 싣고, 한 칸에 본 횟수가 3 미만이면 싣지 않는다. 공휴일·행사·비 오는 날을 가르지 않았다
#   py -3.12 -X utf8 tools/signal/spdnormal-bake.py            → 굽기
#   py -3.12 -X utf8 tools/signal/spdnormal-bake.py backfill   → git 에 남은 data/live-spd-seocho.json 의 지난 판을 쌓아 둔 곳에 채운다(처음 한 번)
import json, os, sys, glob, gzip, datetime, statistics, collections, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); AD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'livespd')
def lines():
    for f in sorted(glob.glob(os.path.join(AD, '*.jsonl.gz'))):
        try:
            with gzip.open(f, 'rt', encoding='utf-8') as g:
                for ln in g:
                    try: yield json.loads(ln)
                    except Exception: pass
        except Exception as e: print(os.path.basename(f), '못 읽음', type(e).__name__)
def backfill():
    os.makedirs(AD, exist_ok=True); have = set(x['at'] for x in lines()); n = 0
    run = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore').stdout
    for h in run('git', 'log', '--format=%H', '--', 'data/live-spd-seocho.json').split():
        try: j = json.loads(run('git', 'show', h + ':data/live-spd-seocho.json'))
        except Exception: continue
        if j.get('at') in have or not j.get('m'): continue
        have.add(j['at']); d = datetime.datetime.fromtimestamp(j['at']).strftime('%Y%m%d'); n += 1
        with gzip.open(os.path.join(AD, d + '.jsonl.gz'), 'at', encoding='utf-8') as f: f.write(json.dumps({'at': j['at'], 'm': j['m']}, separators=(',', ':')) + chr(10))
    print('채움', n, '· 모두', len(have))
def main():
    HOL = set(json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8')).get('days', {}))   # 공휴일 = 일요일 갈래(소유자 2026-10-11 「신호값이 평일과 휴일이 달라 — 통행량이 다르니까」 · 신호 계획의 TOD 4 = 일·공휴일과 같게)
    KEEP = set()   # (2026-10-18) 10-14 부터 쌓인 곳에 여섯 구 링크가 섞인다 → 서초 판은 livespd-bake 의 서초 링크(신호 접근로 + nav-seocho 등급 1~4)만
    for v in json.load(open(os.path.join(ROOT, 'data', 'sig-approach-seocho.json'), encoding='utf-8'))['spots'].values():
        for rows in v['in'].values():
            for r in rows:
                for lk, _ in r[4]: KEEP.add(str(lk))
    for x in json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8'))['links']:
        if x[5] <= 4: KEEP.add(str(x[0]))
    SIX = 'six' in sys.argv[1:]   # (2026-10-18) py … spdnormal-bake.py six → data/spd-normal-six.json(여섯 구 · livespd-bake 의 want6 = 서초 링크 + nav-six 등급 1~4 · 같은 꼴)
    if SIX:
        for x in json.load(open(os.path.join(ROOT, 'data', 'nav-six.json'), encoding='utf-8'))['links']:
            if x[5] <= 4: KEEP.add(str(x[0]))
    C = collections.defaultdict(list); DD = collections.defaultdict(set); days = collections.defaultdict(set); n = 0; t0 = t1 = None
    for x in lines():
        d = datetime.datetime.fromtimestamp(x['at']); wd = d.weekday(); cl = 3 if d.date().isoformat() in HOL else 0 if wd <= 3 else 1 if wd == 4 else 2 if wd == 5 else 3; days[cl].add(d.date().isoformat()); n += 1
        t0 = x['at'] if t0 is None else min(t0, x['at']); t1 = x['at'] if t1 is None else max(t1, x['at'])
        for k, v in x['m'].items():
            if k in KEEP: C[(k, cl, d.hour)].append(v); DD[(k, cl, d.hour)].add(d.date().isoformat())
    if not n: print('쌓인 것이 없다'); return 1
    out = collections.defaultdict(dict); cells = 0; prov = 0; NEED = 3   # (2026-10-18 소유자) 요일 갈래마다 3날(3주) 미만으로 본 칸은 「잠정」
    for (k, cl, h), v in C.items():
        if len(v) < 3: continue
        nd = len(DD[(k, cl, h)]); v.sort(); out[k]['%d-%d' % (cl, h)] = [round(statistics.median(v)), v[len(v) // 4], len(v), nd, 1 if nd < NEED else 0]; cells += 1; prov += nd < NEED
    f = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    doc = {'schema': 'tg-spd-normal/1', 'made': datetime.date.today().isoformat(), 'from': f(t0), 'to': f(t1), 'snaps': n, 'days': {str(k): len(v) for k, v in sorted(days.items())}, 'need_days': NEED, 'provisional': {str(k): len(v) < NEED for k, v in sorted(days.items())},
           'source': '국가교통정보센터(ITS) 실시간 소통정보 trafficInfo 를 약 10분마다 받아 쌓은 것(tools/signal/livespd-bake.py → 저장소 밖 livespd/) — 서초구 + 2km 의 신호 접근로와 큰길(등급 1~4)',
           'note': ['**본 날 수가 요일 갈래마다 3날(3주) 미만인 칸은 「잠정」**(칸 다섯째 값 1 · provisional) — 지도·가르고는 「잠정」이라고 같이 보여야 한다', '**쌓인 날 수(days)가 적으면 「평소」라고 부를 수 없다** — 요일 갈래마다 몇 날을 봤는지 꼭 같이 본다(한두 날이면 그날의 사정일 뿐이다)',
                    '통행속도 = 그 링크를 지난 차들의 평균 속도(km/h). 가운데값 = 보통 때 · 아래 사분위 = 막히는 쪽 · 한 칸에 세 번 미만 본 것은 싣지 않았다',
                    '공휴일은 일요일 갈래(3)에 넣었다(data/holidays.json — 신호 계획의 「일·공휴일」과 같게) · 행사 · 비·눈 온 날은 가르지 않았다 · 값이 안 오는 링크(지난 차가 없음)는 그 칸이 비어 있다',
                    '쓰임: 지금 속도가 평소보다 얼마나 느린가(이상 알아채기) · 길 안내의 시간대별 걸리는 시간 · 사건·공사 앞뒤 견주기'],
           'fields': 'links{ITS 링크 ID: {「요일 갈래-시」: [가운데값 km/h, 아래 사분위 km/h, 본 횟수, 본 날 수, 잠정 1|0(본 날 수 < need_days)]}} — 요일 갈래 0 월~목 · 1 금 · 2 토 · 3 일·공휴일 · days = 갈래마다 쌓인 날 수 · provisional = 갈래 전체가 아직 잠정인가(앞 세 칸은 첫 판과 같은 뜻 — 덧붙이기만)', 'links': dict(sorted(out.items()))}
    if SIX: doc['source'] = doc['source'].replace('서초구 + 2km', '여섯 구(서초·강남·동작·관악·용산·송파) + 둘레') ; doc['area'] = 'six'
    if SIX: return six_split(doc, out, prov, cells, n)
    p = os.path.join(ROOT, 'data', 'spd-normal-seocho.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('잠정 칸', prov, '/', cells); print('받은 판', n, '·', doc['from'], '~', doc['to'], '· 요일 갈래마다 날 수', doc['days'], '· 링크', len(out), '· 칸', cells, '· 바이트', os.path.getsize(p)); return 0
def six_split(doc, out, prov, cells, n):
    """(2026-10-18 게임 세션과 정함 · 폰 먼저) 여섯 구 판은 구마다 쪼갠다 → data/spd-normal-six/<구 코드>.json(서초 판과 같은 칸 꼴) + index.json
    링크의 구 = 선 첫 점·끝 점마다 가장 가까운 행정동 가운데(data/r/index.json 의 서울 동 점)의 구 — 두 구에 걸치면 양쪽에 같은 값 · 근사(동 가운데 기준)"""
    G = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus']
    pts = [(lo, la, g['gu']) for g in G if g['sido'] == '11' for _, lo, la in g['d']]
    def gu_of(lo, la): return min(pts, key=lambda p: (p[0] - lo) ** 2 + ((p[1] - la) * 1.25) ** 2)[2]
    geo = {}
    for fn in ('nav-six.json', 'nav-seocho.json'):
        fp = os.path.join(ROOT, 'data', fn)
        if not os.path.exists(fp): continue
        for x in json.load(open(fp, encoding='utf-8'))['links']:
            ln = x[9]
            if str(x[0]) in geo or not ln or len(ln) < 2: continue
            xs, ys = [ln[0]], [ln[1]]
            for i in range(2, len(ln) - 1, 2): xs.append(xs[-1] + ln[i]); ys.append(ys[-1] + ln[i + 1])
            geo[str(x[0])] = [(xs[0] / 1e5, ys[0] / 1e5), (xs[-1] / 1e5, ys[-1] / 1e5)]
    by = collections.defaultdict(dict); box = {}; nogeo = 0
    for k, v in out.items():
        e = geo.get(k)
        if not e: nogeo += 1; continue
        for lo, la in e:
            g = gu_of(lo, la); by[g][k] = v
            b = box.setdefault(g, [lo, la, lo, la]); box[g] = [min(b[0], lo), min(b[1], la), max(b[2], lo), max(b[3], la)]
    D = os.path.join(ROOT, 'data', 'spd-normal-six'); os.makedirs(D, exist_ok=True)
    names = {g['gu']: g['name'] for g in G}; idx = {}
    for g, L in sorted(by.items()):
        d = dict(doc, gu=g, gu_name=names.get(g, ''), links=dict(sorted(L.items())))
        json.dump(d, open(os.path.join(D, g + '.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        idx[g] = {'file': 'spd-normal-six/%s.json' % g, 'name': names.get(g, ''), 'bbox': [round(x, 5) for x in box[g]], 'n': len(L)}
    ix = {'schema': 'tg-spd-normal-index/1', 'made': doc['made'], 'from': doc['from'], 'to': doc['to'], 'days': doc['days'], 'need_days': doc['need_days'], 'provisional': doc['provisional'],
          'source': doc['source'], 'fields': 'gu{구 코드: {file, name, bbox[서, 남, 동, 북](WGS84 · 그 구에 넣은 링크 끝점들의 상자), n 링크 수}} — 구 파일 칸 꼴은 data/spd-normal-seocho.json 과 같다',
          'note': ['링크의 구 = 링크 첫 점·끝 점에서 가장 가까운 행정동 가운데의 구(근사) · 두 구에 걸친 링크는 양쪽 파일에 같은 값', '좌표를 못 찾은 링크 %d 개는 뺐다' % nogeo] + doc['note'], 'gu': idx}
    json.dump(ix, open(os.path.join(D, 'index.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('잠정 칸', prov, '/', cells, '· 구', len(idx), {g: v['n'] for g, v in idx.items()}, '· 좌표 없음', nogeo, '· 받은 판', n, '· 날 수', doc['days'])
    return 0
if __name__ == '__main__': sys.exit(backfill() if sys.argv[1:2] == ['backfill'] else main())
