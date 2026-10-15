# -*- coding: utf-8 -*-
"""경찰청 UTIC 신호계획(tsihub · 운영계획 getPlanCROPInfo) 전 쪽을 아주 천천히 받기 — 서울 교차로가 들어 있는지 끝까지 보려고
(2026-10-15 소유자 「한도가 넘지 않는 범위 내에서 진행되게 하자 · 시간이 많이 걸려 어쩔 수 없다」)

  지역·이름 거르기가 먹지 않아(다른 세션 실측) 처음부터 끝까지 훑을 수밖에 없다 — 운영계획 약 10,223쪽(100줄씩)
  · 2.5초에 한 번(UTIC 「1초 5회 넘으면 IP 차단」의 1/12) · 한 번 돌 때 최대 55분 — 예약 작업(datamap-utic-plan)이 매시 이어서 · numOfRows 는 100 이 끝(1000 을 넣어도 100) → 쪽당 약 6.5초 · 전체 약 18시간
  · 받은 쪽은 ../07_API키/out/utic/plan/p<쪽>.json 에 그대로(있으면 건너뜀 = 이어받기)
  · 오류(HTTP 4xx·5xx · JSON 아님 · 빈 응답)가 3번 이어지면 그날은 멈춘다(state.json 의 stop_until = 다음 날 06시) — 차단 낌새에 더 두드리지 않는다
  · 열쇠 = keys.json 「utic」(출력하지 않는다) · 등록 IP(이 PC)에서만 된다 · 출처 「경찰청 도시교통정보센터(UTIC)」
  py -3.12 -X utf8 tools/signal/utic-plan-fetch.py [MAXP]
  py -3.12 -X utf8 tools/signal/utic-plan-fetch.py --sum      받은 쪽 요약(지역 코드별 줄 수 · 서울 이름 표본)
"""
import os, sys, json, time, datetime, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
OUT = os.path.join(RAW, 'out', 'utic', 'plan')
GAP = 2.5
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
    maxp = int(next((a for a in sys.argv[1:] if a.isdigit()), '100000')); t_end = time.time() + 55 * 60   # 한 번 돌 때 최대 55분(응답 약 4초 + 쉼 2.5초 → 쪽당 약 6.5초 · 전체 약 18시간)
    stp = os.path.join(OUT, 'state.json')
    try:
        st = json.load(open(stp, encoding='utf-8'))
    except Exception:
        st = {}
    if st.get('stop_until') and datetime.datetime.now().isoformat() < st['stop_until']:
        return
    if st.get('done'):
        return
    key = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig'))['utic']
    total, got, bad, page = st.get('totPage'), 0, 0, 1
    while got < maxp and time.time() < t_end:
        if total and page > total:
            st['done'] = datetime.datetime.now().isoformat(); log('끝', total, '쪽'); break
        p = os.path.join(OUT, 'p%05d.json' % page)
        if os.path.exists(p):
            page += 1; continue
        time.sleep(GAP)
        try:
            raw = urllib.request.urlopen(urllib.request.Request(URL.format(key=key, page=page), headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'ignore')
            j = json.loads(raw)
            if not isinstance(j, list) or not j or not isinstance(j[0], dict) or str(j[0].get('resultCode')) != '0':
                raise ValueError('결과 코드 ' + str(j[0].get('resultCode') if isinstance(j, list) and j and isinstance(j[0], dict) else '?'))
            if not total:
                total = int(j[0].get('totPage') or 0); st['totPage'] = total; st['totCount'] = j[0].get('totCount')
            open(p, 'w', encoding='utf-8').write(raw); got += 1; bad = 0; page += 1
        except Exception as e:
            bad += 1; log('오류', page, type(e).__name__, str(e)[:120])
            if bad >= 3:
                st['stop_until'] = (datetime.datetime.now() + datetime.timedelta(days=1)).replace(hour=6, minute=0, second=0).isoformat()
                log('3번 이어진 오류 — 내일 06시까지 멈춤'); break
            time.sleep(30)
    json.dump(st, open(stp, 'w', encoding='utf-8'), ensure_ascii=False)
    log('이번에', got, '쪽 · 다음', page, '/', total)


if __name__ == '__main__':
    main()
