# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚗 방향별 막힘의 바탕: 서초 둘레 지금 통행속도 한 장(소유자 2026-10-11 「방향별 막힘 실시간을 30분을 줘야 하는데」 → 「권고대로 모두 진행」) → data/live-spd-seocho.json
#   맛보기 중계가 ITS 에 잘 닿지 않아(522) 열쇠 없는 사람은 방향별 막힘을 못 봤다 → 이 PC 가 받아 작은 파일로 올린다(지도는 맛보기 30분 동안 이 파일을 읽는다 · **몇 분 늦은 값**)
#   한 번 부르면 ITS trafficInfo 를 **한 번** 호출한다(상자 하나 · 키 keys.json its — 찍지도 올리지도 않는다 · 월 한도 10,000건)
#   **이 도구는 커밋하지 않는다** — 신호 수집기(tools/signal/spat-bake.py sweep · 게임 세션)가 두 번에 한 번 불러 그 파일을 같이 올린다(예약 작업을 따로 두지 않는다)
#   싣는 것 = 신호 교차로에 들어오는 길의 링크(data/sig-approach-seocho.json) + 큰길(data/nav-seocho.json 의 등급 1~4 링크) — {ITS 링크 ID: 통행속도 km/h 정수}
#   실패하거나 받은 것이 너무 적으면 파일을 건드리지 않고 1 로 끝난다
#   받을 때마다 저장소 밖 ../07_API키/out/livespd/<날짜>.jsonl.gz 에 한 줄씩 쌓는다 → tools/signal/spdnormal-bake.py 가 「평소 속도」로 굽는다
#   py -3.12 -X utf8 tools/signal/livespd-bake.py
import json, os, sys, time, datetime, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
BOX = [126.955, 37.405, 127.115, 37.545]   # 서초구 + 2km 를 덮는 상자(가르고의 길 계산 지도와 같다)
def main():
    want = set()
    for v in json.load(open(os.path.join(ROOT, 'data', 'sig-approach-seocho.json'), encoding='utf-8'))['spots'].values():
        for rows in v['in'].values():
            for r in rows:
                for lk, _ in r[4]: want.add(str(lk))
    for x in json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8'))['links']:
        if x[5] <= 4: want.add(str(x[0]))
    K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['its']
    u = 'https://openapi.its.go.kr:9443/trafficInfo?apiKey=%s&type=all&drcType=all&minX=%s&maxX=%s&minY=%s&maxY=%s&getType=json' % (K, BOX[0], BOX[2], BOX[1], BOX[3])
    try: j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'replace'))
    except Exception as e: print('못 받음', type(e).__name__); return 1
    items = (j.get('body') or {}).get('items') or []; m = {}
    for it in items:
        try:
            if str(it['linkId']) in want: m[str(it['linkId'])] = int(round(float(it['speed'])))
        except Exception: pass
    if len(m) < 50: print('받은 링크가 너무 적다', len(m), '/', len(items), '— 파일을 바꾸지 않는다'); return 1
    doc = {'schema': 'tg-live-spd/1', 'at': int(time.time()), 'made': datetime.datetime.now().strftime('%H:%M'), 'day': datetime.date.today().isoformat(), 'box': BOX,
           'source': '국가교통정보센터(ITS) 실시간 소통정보 trafficInfo(openapi.its.go.kr) — 원자료의 만든 때 ' + str(items[0].get('createdDate') if items else ''),
           'note': ['실시간이 아니다 — 이 PC 가 약 11분마다 한 번 받아 올린 값이다(at = 받은 때 epoch 초) · 올라가 보이기까지 몇 분 더 걸린다 · PC 가 꺼져 있으면 멈춘다 → at 이 20분 넘게 지났으면 쓰지 않는다',
                    '통행속도 = 그 링크를 지난 차들의 평균 속도(km/h) — 「얼마나 막히나」이지 「신호를 몇 번 기다리나」가 아니다 · 값이 없는 링크는 「값 없음」이지 「원활」이 아니다',
                    '자기 열쇠로 실시간 소통을 켠 사람은 이 파일이 아니라 직접 받은 값을 쓴다'],
           'fields': 'm{ITS 링크 ID: 통행속도 km/h(정수)} — data/sig-approach-seocho.json 의 링크와 data/nav-seocho.json 의 등급 1~4 링크 · n 값이 온 링크 수 · want 찾는 링크 수',
           'n': len(m), 'want': len(want), 'm': dict(sorted(m.items()))}
    p = os.path.join(ROOT, 'data', 'live-spd-seocho.json'); tmp = p + '.tmp'
    json.dump(doc, open(tmp, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); os.replace(tmp, p)
    try:   # 쌓아 두기(저장소 밖) — 「평소 속도」의 바탕(링크 × 요일 × 시각)을 만들려는 것. 하루 한 파일 · 한 번 받을 때마다 한 줄(gzip 이어 붙이기) · 실패해도 위 파일은 이미 썼다
        import gzip
        ad = os.path.join(KB, '07_API키', 'out', 'livespd'); os.makedirs(ad, exist_ok=True)
        with gzip.open(os.path.join(ad, datetime.date.today().strftime('%Y%m%d') + '.jsonl.gz'), 'at', encoding='utf-8') as f: f.write(json.dumps({'at': doc['at'], 'm': doc['m']}, separators=(',', ':')) + chr(10))
    except Exception as e: print('쌓아 두기 실패', type(e).__name__)
    print(doc['made'], '· 값이 온 링크', len(m), '/', len(want), '· 상자 안 전부', len(items), '· 바이트', os.path.getsize(p)); return 0
if __name__ == '__main__': sys.exit(main())
