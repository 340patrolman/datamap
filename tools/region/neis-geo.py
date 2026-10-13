# -*- coding: utf-8 -*-
# 데이터 압축지도 — 학원·교습소 도로명주소 → 좌표(브이월드 주소 변환) → 07_API키/out/neis/geo.json
#   소유자 2026-10-13 신고 「관악구 은천동에 피아노 학원 10개 넘는다는데 몇 개 안 나온다」 — 법정동(봉천동·신림동)을 행정동 21곳에 넓이로 나눠 크게 어긋났다(실측 17 ↔ 5.2)
#   → 학원마다 도로명주소(FA_RDNMA)를 좌표로 바꿔 행정동 경계에 넣는다. neis-bake · neiscourse-bake 가 이 캐시를 먼저 보고, 없는 주소만 종전 넓이 나눔으로
#   같은 주소(같은 건물)는 한 번만 부른다 · 못 찾은 주소는 null 로 적어 다시 안 부른다 · 하루 한도(OVER_REQUEST_LIMIT)에 걸리면 멈춘다 — 다음 날 이어서(home-bake geo · jumin-geo 와 한도를 같이 쓴다)
#   ⚠ 2026-10-13 여섯 줄로 한꺼번에 불렀더니 브이월드가 연결을 끊었다(Remote end closed · 1분 뒤 풀림) — 두 줄 · 0.08초 쉼 · 300건마다 저장으로 고침
#   py -3.12 -X utf8 tools/region/neis-geo.py [교육청 코드… 기본 B10 J10 E10 그리고 나머지]
import json, os, sys, glob, time, threading, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); SRC = os.path.join(KB, 'out', 'neis'); P = os.path.join(SRC, 'geo.json')
KEY = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']; STOP = threading.Event(); LOCK = threading.Lock()
def one(addr):
    if STOP.is_set(): return addr, 'skip'
    q = dict(service='address', request='getcoord', version='2.0', crs='epsg:4326', address=addr, refine='true', simple='false', format='json', type='road', key=KEY, domain='https://340patrolman.github.io')
    for t in range(3):
        try: r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q), headers={'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8'))['response']
        except Exception: time.sleep(4 + t * 6); continue
        time.sleep(0.08)
        if r.get('status') == 'OK': p = r['result']['point']; return addr, [round(float(p['x']), 6), round(float(p['y']), 6)]
        if 'LIMIT' in json.dumps(r): STOP.set(); return addr, 'skip'
        if r.get('status') == 'NOT_FOUND': return addr, None
        time.sleep(0.5)
    return addr, 'skip'
def main(codes):
    C = json.load(open(P, encoding='utf-8')) if os.path.exists(P) else {}
    order = codes or (['B10', 'J10', 'E10'] + sorted(os.path.basename(f)[4:7] for f in glob.glob(os.path.join(SRC, 'aca_*.json')) if os.path.basename(f)[4:7] not in ('B10', 'J10', 'E10')))
    for code in order:
        if STOP.is_set(): break
        rows = json.load(open(os.path.join(SRC, 'aca_%s.json' % code), encoding='utf-8')); todo = sorted(set((r.get('FA_RDNMA') or '').strip() for r in rows) - set(C) - {''}); n = 0; t0 = time.time()
        print(code, '주소', len(set((r.get('FA_RDNMA') or '').strip() for r in rows)), '새로 부를 것', len(todo)); sys.stdout.flush()
        with ThreadPoolExecutor(2) as ex:
            for addr, v in ex.map(one, todo):
                if v == 'skip': continue
                C[addr] = v; n += 1
                if n % 300 == 0:
                    with LOCK: json.dump(C, open(P, 'w', encoding='utf-8'), ensure_ascii=False)
                    print('  ', code, n, '/', len(todo), round(time.time() - t0), '초'); sys.stdout.flush()
        json.dump(C, open(P, 'w', encoding='utf-8'), ensure_ascii=False); print(code, '받음', n, '· 캐시', len(C), '· 못 찾음', sum(1 for v in C.values() if v is None), '· 한도' if STOP.is_set() else ''); sys.stdout.flush()
if __name__ == '__main__': main(sys.argv[1:])
