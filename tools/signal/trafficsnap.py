# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚗 방향별 막힘의 바탕: 서초 둘레 지금 통행속도 한 장(소유자 2026-10-11 「방향별 막힘 실시간을 30분을 줘야 하는데」 → 「권고대로 모두 진행」) → data/traffic-snap-seocho.json
#   맛보기 중계가 ITS 에 잘 닿지 않아(522) 열쇠 없는 사람은 방향별 막힘을 못 봤다 → 이 PC 가 10분마다 한 번 받아 작은 파일로 올린다(열쇠 없이 누구나 읽는다 · **몇 분 늦은 값**이다)
#   자료 = 국가교통정보센터(ITS) 실시간 소통정보 trafficInfo(openapi.its.go.kr:9443 · 키 keys.json its · 한 번 부르면 상자 안 전부 · 월 한도 10,000건 — 10분마다 = 한 달 약 4,400건)
#   싣는 것 = 신호 교차로에 들어오는 길의 링크(data/sig-approach-seocho.json 에 있는 ITS 링크 ID)만 — {링크 ID: 통행속도 km/h}
#   py -3.12 -X utf8 tools/signal/trafficsnap.py            → 한 번 받아 파일만 쓴다
#   py -3.12 -X utf8 tools/signal/trafficsnap.py --commit   → 받아서 그 파일만 커밋·푸시(열쇠 검사 통과 때만) — 예약 작업이 10분마다 부른다(tools/home/소통수집_켜기.bat)
import json, os, sys, time, datetime, subprocess, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
OUT = 'data/traffic-snap-seocho.json'
def main():
    ap = json.load(open(os.path.join(ROOT, 'data', 'sig-approach-seocho.json'), encoding='utf-8'))['spots']; want = set()
    for v in ap.values():
        for rows in v['in'].values():
            for r in rows:
                for lk, _ in r[4]: want.add(str(lk))
    box = (126.955, 37.405, 127.115, 37.545)   # 서초구 + 2km 를 덮는 상자(가르고의 길 계산 지도와 같다)
    K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['its']
    u = 'https://openapi.its.go.kr:9443/trafficInfo?apiKey=%s&type=all&drcType=all&minX=%s&maxX=%s&minY=%s&maxY=%s&getType=json' % (K, box[0], box[2], box[1], box[3])
    j = None
    for k in range(3):
        try: j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'replace')); break
        except Exception as e: err = type(e).__name__; time.sleep(8)
    if j is None: print('못 받음', err); return 1
    items = (j.get('body') or {}).get('items') or []; spd = {}
    for it in items:
        try:
            if str(it['linkId']) in want: spd[str(it['linkId'])] = round(float(it['speed']), 1)
        except Exception: pass
    if len(spd) < 50: print('받은 링크가 너무 적다', len(spd), '/', len(items), '— 파일을 바꾸지 않는다'); return 1
    now = datetime.datetime.now()
    doc = {'schema': 'tg-traffic-snap/1', 'made': now.strftime('%Y-%m-%d %H:%M'), 'at': int(time.time()), 'every_min': 10, 'area': '서초구 + 경계 밖 2km(data/sig-approach-seocho.json 의 신호 교차로에 들어오는 길)',
           'source': '국가교통정보센터(ITS) 실시간 소통정보 trafficInfo(openapi.its.go.kr) — 원자료의 만든 때 ' + str(items[0].get('createdDate') if items else ''),
           'note': ['**실시간이 아니다 — 이 PC 가 10분마다 한 번 받아 올린 값이다**(made · at = 받은 때). 올라가 보이기까지 1~2분 더 걸린다 · PC 가 꺼져 있으면 멈춘다 → at 이 25분 넘게 지났으면 「오래된 값」으로 보고 쓰지 않는다',
                    '통행속도는 그 링크를 지난 차들의 평균 속도(km/h) — 「얼마나 막히나」이지 「신호를 몇 번 기다리나」가 아니다 · 제한속도와 견줘 읽는다(sig-approach 의 제한속도 칸)',
                    '링크마다 값이 안 오는 때가 있다(그 사이 지난 차가 없음) — 없는 링크는 「값 없음」이지 「원활」이 아니다',
                    '자기 열쇠로 실시간 소통을 켠 사람은 이 파일이 아니라 직접 받은 값을 쓴다'],
           'fields': 'spd{ITS 링크 ID: 통행속도 km/h} — data/sig-approach-seocho.json 의 링크 ID 와 맞댄다 · n = 값이 온 링크 수 · want = 찾는 링크 수',
           'n': len(spd), 'want': len(want), 'spd': dict(sorted(spd.items()))}
    p = os.path.join(ROOT, *OUT.split('/')); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(doc['made'], '· 값이 온 링크', len(spd), '/', len(want), '· 상자 안 전부', len(items), '· 바이트', os.path.getsize(p))
    if '--commit' in sys.argv:
        run = lambda *a: subprocess.run(a, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
        run('git', 'add', '--', OUT)
        if run('py', '-3.12', '-X', 'utf8', 'tools/keycheck.py').returncode != 0: run('git', 'reset', '-q', '--', OUT); print('열쇠 검사에 걸려 올리지 않는다'); return 1
        c = run('git', 'commit', '-q', '-m', 'traffic-snap: 서초 둘레 통행속도 자동 갱신\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>', '--', OUT)
        run('git', 'pull', '-q', '--rebase', '--autostash', 'origin', 'main'); p2 = run('git', 'push', '-q', 'origin', 'main')
        print('커밋', c.returncode, '· 푸시', p2.returncode, (p2.stderr or '')[:200])
    return 0
if __name__ == '__main__': sys.exit(main())
