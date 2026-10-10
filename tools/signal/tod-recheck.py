# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 경찰청 신호계획이 받은 날(2026-09-10) 뒤로 바뀌었는지 교차로 몇 곳만 다시 불러 견준다(소유자 2026-10-10 「수정되는지 확인하자」)
#   경찰청_교차로계획정보서비스 getPlanCROPInfo(운영계획 · srchCRNm = 교차로 이름) — 키 = keys.json data_go_kr(다시 인코딩하지 않는다) · numOfRows 최대 100
#   py -3.12 -X utf8 tools/signal/tod-recheck.py [교차로 번호…]   (번호를 안 주면 data/sig-offset-check.json 에서 「맞은 수 0」인 곳)
#   고치지는 않는다 — 무엇이 달라졌는지만 적는다. 달라졌으면 07_API키/RUN_signal 로 전부 다시 받아 tod-bake.py
import json, os, sys, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']
def fetch(nm):
    rows = []; page = 1
    while True:
        u = 'https://apis.data.go.kr/1320000/PlanCrossRoadInfoService/getPlanCROPInfo?serviceKey=%s&type=json&pageNo=%d&numOfRows=100&srchCRNm=%s' % (K, page, urllib.parse.quote(nm))
        j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=40).read().decode('utf-8', 'replace'))
        hd = j[0] if isinstance(j, list) and j else {}; it = j[1:] if isinstance(j, list) else []; rows += it   # 응답 = [머리{totalCount …}, 줄, 줄 …]
        if not it or page * 100 >= int(hd.get('totalCount') or 0): return rows
        page += 1; time.sleep(0.2)
def main():
    T = {s['no']: s for s in json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']}
    nos = sys.argv[1:] or [k for k, v in json.load(open(os.path.join(ROOT, 'data', 'sig-offset-check.json'), encoding='utf-8')).get('spots', {}).items() if v[2] == 0]
    for no in nos:
        s = T.get(no)
        if not s: print(no, '계획 파일에 없음'); continue
        R = [r for r in fetch(s['name']) if str(r.get('INT_NO')) == no]
        if not R: print(no, s['name'], '— 응답에 이 번호가 없다(이름 검색 %d줄)' % 0); continue
        keys = sorted(R[0].keys())
        new = {}
        for r in R:
            c = int(float(r.get('INT_OPER_CYCLE_VAL') or 0))
            if c <= 0: continue
            pn = str(r.get('INT_PLAN_NO') or '?'); hh = '%02d:%02d' % (int(r.get('OPER_PLAN_HH') or 0), int(r.get('OPER_PLAN_MI') or 0))
            new[(pn, hh)] = (c, int(float(r.get('INT_OPER_OFFSET_VAL') or 0)))
        old = {(pn, row[0]): (row[1], row[2]) for pn, rows in s['plans'].items() for row in rows}
        diff = [(k, old.get(k), new.get(k)) for k in sorted(set(old) | set(new)) if old.get(k) != new.get(k)]
        print(no, s['name'], '· 수집', R[0].get('COLLCT_DTIME'), '· 줄 옛', len(old), '새', len(new), '· 다른 줄', len(diff), diff[:6])
        if not new: print('   칸 이름', keys)
if __name__ == '__main__': main()
