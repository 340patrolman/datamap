# -*- coding: utf-8 -*-
"""경찰청 UTIC 신호계획(tsihub · 운영계획 getPlanCROPInfo) 전 쪽을 아주 천천히 받기 — 서울 교차로가 들어 있는지 끝까지 보려고
(2026-10-15 소유자 「한도가 넘지 않는 범위 내에서 진행되게 하자 · 시간이 많이 걸려 어쩔 수 없다」)

  지역·이름 거르기가 먹지 않아(다른 세션 실측) 처음부터 끝까지 훑을 수밖에 없다 — 운영계획 약 10,223쪽(100줄씩)
  · 1초에 2번까지 출발(소유자 「1초에 2회」 · UTIC 「1초 5회」 아래) · 응답 4초 남짓이라 동시에 8개까지 · 한 번 돌 때 최대 55분 — 예약 작업(datamap-utic-plan)이 매시 이어서 · numOfRows 는 100 이 끝(1000 을 넣어도 100) → 10,223쪽 ÷ 초당 2 ≈ 1시간 반
  · 받은 쪽은 ../07_API키/out/utic/plan/p<쪽>.json 에 그대로(있으면 건너뜀 = 이어받기)
  · 오류(HTTP 4xx·5xx · JSON 아님 · 빈 응답)가 3번 이어지면 그날은 멈춘다(state.json 의 stop_until = 다음 날 06시) — 차단 낌새에 더 두드리지 않는다
  · 열쇠 = keys.json 「utic」(출력하지 않는다) · 등록 IP(이 PC)에서만 된다 · 출처 「경찰청 도시교통정보센터(UTIC)」
  py -3.12 -X utf8 tools/signal/utic-plan-fetch.py [MAXP]
  py -3.12 -X utf8 tools/signal/utic-plan-fetch.py --sum      받은 쪽 요약(지역 코드별 줄 수 · 서울 이름 표본)
"""
import os, sys, json, time, datetime, threading, concurrent.futures, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(RAW, 'out', 'utic', 'plan')
GAP = 2.5
RATE = 2.0      # 새 요청 출발 = 1초에 2번까지(UTIC 「1초 5회 넘으면 IP 차단」 · 소유자 2026-10-15 「1초에 2회」)
INFLIGHT = 8    # 응답이 4초 남짓이라 동시에 떠 있는 요청을 8개까지(그래도 출발은 초당 2번)
# 호출 주소 꼴 — 다른 세션이 실측한 것으로 채운다(열쇠 자리 {key} · 쪽 {page})
URL = 'http://tsihub.utic.go.kr/tsi/api/PlanCrossRoadInfoService/getPlanCROPInfo?serviceKey={key}&type=json&numOfRows=100&pageNo={page}'   # 다른 세션 실측(2026-10-15) · numOfRows 는 1000 을 넣어도 100 만 준다(실측)


def log(*a):
    with open(os.path.join(OUT, 'log.txt'), 'a', encoding='utf-8') as f:
        f.write(datetime.datetime.now().strftime('%m-%d %H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')


def summary():
    import collections, glob
    C, nm, n = collections.Counter(), collections.defaultdict(set), 0
    for f in sorted(glob.glob(os.path.join(OUT, 'p*.json'))):
        try:
            j = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        for r in (j[1:] if isinstance(j, list) else []):
            C[r.get('REGION_CD')] += 1; n += 1
            if len(nm[r.get('REGION_CD')]) < 6:
                nm[r.get('REGION_CD')].add(r.get('INT_NM'))
    print('받은 쪽', len(glob.glob(os.path.join(OUT, 'p*.json'))), '· 줄', n)
    for k, v in sorted(C.items(), key=lambda x: -x[1]):
        print(' ', k, v, '·', ' / '.join(sorted(nm[k])))


def main():
    os.makedirs(OUT, exist_ok=True)
    if '--sum' in sys.argv:
        summary(); return
    if not URL:
        sys.exit('호출 주소 꼴(URL)이 아직 비어 있다 — 다른 세션 실측값으로 채운 뒤 돌린다')
    maxp = int(next((a for a in sys.argv[1:] if a.isdigit()), '100000')); t_end = time.time() + 55 * 60   # 한 번 돌 때 최대 55분
    stp, lk = os.path.join(OUT, 'state.json'), os.path.join(OUT, 'run.lock')
    try:
        if time.time() - os.path.getmtime(lk) < 70 * 60:
            return   # 다른 회차가 돌고 있다 — 두 번 겹쳐 부르지 않는다
    except FileNotFoundError:
        pass
    open(lk, 'w').write(str(os.getpid()))
    try:
        st = json.load(open(stp, encoding='utf-8'))
    except Exception:
        st = {}
    try:
        if (st.get('stop_until') and datetime.datetime.now().isoformat() < st['stop_until']) or st.get('done'):
            return
        key = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig'))['utic']
        total = st.get('totPage') or 10223
        todo = [pg for pg in range(1, total + 1) if not os.path.exists(os.path.join(OUT, 'p%05d.json' % pg))][:maxp]
        lock, state = threading.Lock(), {'bad': 0, 'stop': False, 'got': 0, 'last': 0.0}

        def one(pg):
            with lock:   # 출발 간격 = 1 ÷ RATE 초(UTIC 「1초 5회」 아래 · 소유자 2026-10-15 「1초에 2회」)
                if state['stop'] or time.time() > t_end:
                    return
                w = state['last'] + 1.0 / RATE - time.time()
                if w > 0:
                    time.sleep(w)
                state['last'] = time.time()
            try:
                raw = urllib.request.urlopen(urllib.request.Request(URL.format(key=key, page=pg), headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'ignore')
                jj = json.loads(raw)
                if not isinstance(jj, list) or not jj or not isinstance(jj[0], dict) or str(jj[0].get('resultCode')) != '0':
                    raise ValueError('결과 코드 ' + str(jj[0].get('resultCode') if isinstance(jj, list) and jj and isinstance(jj[0], dict) else '?'))
                open(os.path.join(OUT, 'p%05d.json' % pg), 'w', encoding='utf-8').write(raw)
                with lock:
                    state['bad'] = 0; state['got'] += 1
                    if not st.get('totCount'):
                        st['totPage'] = int(jj[0].get('totPage') or total); st['totCount'] = jj[0].get('totCount')
            except Exception as e:
                with lock:
                    state['bad'] += 1; log('오류', pg, type(e).__name__, str(e)[:120])
                    if state['bad'] >= 3 and not state['stop']:   # 차단 낌새 — 모두 멈추고 그날은 더 두드리지 않는다
                        state['stop'] = True; st['stop_until'] = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=6, minute=0, second=0).isoformat(); log('3번 이어진 오류 — 모두 멈춤 · 내일 06시까지')

        with concurrent.futures.ThreadPoolExecutor(max_workers=INFLIGHT) as ex:
            list(ex.map(one, todo))
        left = sum(1 for pg in range(1, (st.get('totPage') or total) + 1) if not os.path.exists(os.path.join(OUT, 'p%05d.json' % pg)))
        if left == 0:
            st['done'] = datetime.datetime.now().isoformat(); log('끝', st.get('totPage'), '쪽')
        json.dump(st, open(stp, 'w', encoding='utf-8'), ensure_ascii=False)
        log('이번에', state['got'], '쪽 · 남은 쪽', left, '· 초당', RATE, '· 동시', INFLIGHT)
    finally:
        try:
            os.remove(lk)
        except OSError:
            pass


if __name__ == '__main__':
    main()
