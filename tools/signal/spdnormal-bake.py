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
    C = collections.defaultdict(list); days = collections.defaultdict(set); n = 0; t0 = t1 = None
    for x in lines():
        d = datetime.datetime.fromtimestamp(x['at']); wd = d.weekday(); cl = 0 if wd <= 3 else 1 if wd == 4 else 2 if wd == 5 else 3; days[cl].add(d.date().isoformat()); n += 1
        t0 = x['at'] if t0 is None else min(t0, x['at']); t1 = x['at'] if t1 is None else max(t1, x['at'])
        for k, v in x['m'].items(): C[(k, cl, d.hour)].append(v)
    if not n: print('쌓인 것이 없다'); return 1
    out = collections.defaultdict(dict); cells = 0
    for (k, cl, h), v in C.items():
        if len(v) < 3: continue
        v.sort(); out[k]['%d-%d' % (cl, h)] = [round(statistics.median(v)), v[len(v) // 4], len(v)]; cells += 1
    f = lambda t: datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M')
    doc = {'schema': 'tg-spd-normal/1', 'made': datetime.date.today().isoformat(), 'from': f(t0), 'to': f(t1), 'snaps': n, 'days': {str(k): len(v) for k, v in sorted(days.items())},
           'source': '국가교통정보센터(ITS) 실시간 소통정보 trafficInfo 를 약 10분마다 받아 쌓은 것(tools/signal/livespd-bake.py → 저장소 밖 livespd/) — 서초구 + 2km 의 신호 접근로와 큰길(등급 1~4)',
           'note': ['**쌓인 날 수(days)가 적으면 「평소」라고 부를 수 없다** — 요일 갈래마다 몇 날을 봤는지 꼭 같이 본다(한두 날이면 그날의 사정일 뿐이다)',
                    '통행속도 = 그 링크를 지난 차들의 평균 속도(km/h). 가운데값 = 보통 때 · 아래 사분위 = 막히는 쪽 · 한 칸에 세 번 미만 본 것은 싣지 않았다',
                    '공휴일 · 행사 · 비·눈 온 날을 가르지 않았다 · 값이 안 오는 링크(지난 차가 없음)는 그 칸이 비어 있다',
                    '쓰임: 지금 속도가 평소보다 얼마나 느린가(이상 알아채기) · 길 안내의 시간대별 걸리는 시간 · 사건·공사 앞뒤 견주기'],
           'fields': 'links{ITS 링크 ID: {「요일 갈래-시」: [가운데값 km/h, 아래 사분위 km/h, 본 횟수]}} — 요일 갈래 0 월~목 · 1 금 · 2 토 · 3 일', 'links': dict(sorted(out.items()))}
    p = os.path.join(ROOT, 'data', 'spd-normal-seocho.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('받은 판', n, '·', doc['from'], '~', doc['to'], '· 요일 갈래마다 날 수', doc['days'], '· 링크', len(out), '· 칸', cells, '· 바이트', os.path.getsize(p)); return 0
if __name__ == '__main__': sys.exit(backfill() if sys.argv[1:2] == ['backfill'] else main())
