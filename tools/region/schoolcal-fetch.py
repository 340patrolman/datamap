# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🎒 학교 달력 원자료 받기(나이스 교육정보 개방 포털 · 열쇠 neis · 07_API키/keys.json 에서만 읽는다 · 출력·저장 안 함)
#   학교 목록(schoolInfo · 교육청 코드) → 초·중·고마다 학사일정(SchoolSchedule) → 07_API키/out/neis_cal/<교육청>_<처음>_<끝>.json
#   꼴은 서울 것(B10_…)과 같다: {schools {학교급: 수}, got 받은 학교 수, rows [[YYYYMMDD, 학교급, 행사 이름, 그 날 그 행사를 적은 학교 수]]}
#   py -3.12 -X utf8 tools/region/schoolcal-fetch.py J10 [E10 …] [--from 20260301 --to 20270228]
#   교육청 코드: B10 서울 · J10 경기 · E10 인천 (나이스 ATPT_OFCDC_SC_CODE)
import json, os, sys, time, collections, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
OUT = os.path.join(KB, '07_API키', 'out', 'neis_cal'); K = ['초등학교', '중학교', '고등학교']
KEY = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8'))['neis']
if isinstance(KEY, dict):
    KEY = KEY.get('key') or KEY.get('KEY') or list(KEY.values())[0]


def get(api, **q):
    q.update({'KEY': KEY, 'Type': 'json', 'pSize': 1000})
    out, page = [], 1
    while True:
        q['pIndex'] = page
        u = 'https://open.neis.go.kr/hub/%s?%s' % (api, urllib.parse.urlencode(q))
        for t in range(4):
            try:
                j = json.loads(urllib.request.urlopen(u, timeout=30).read().decode('utf-8')); break
            except Exception:
                time.sleep(2 + t * 3)
        else:
            return out, 'fail'
        if api not in j:
            return out, (j.get('RESULT') or {}).get('CODE', '?')
        head, rows = j[api][0]['head'], j[api][1]['row']
        out += rows; total = head[0]['list_total_count']
        if len(out) >= total:
            return out, 'ok'
        page += 1


def main():
    a = sys.argv[1:]; fr = a[a.index('--from') + 1] if '--from' in a else '20260301'; to = a[a.index('--to') + 1] if '--to' in a else '20270228'
    codes = [x for x in a if len(x) == 3 and x[0].isalpha()]
    os.makedirs(OUT, exist_ok=True)
    for code in codes:
        sch, st = get('schoolInfo', ATPT_OFCDC_SC_CODE=code)
        sch = [s for s in sch if s.get('SCHUL_KND_SC_NM') in K]
        n = collections.Counter(s['SCHUL_KND_SC_NM'] for s in sch)
        print(code, '학교', len(sch), dict(n), st, flush=True)
        C, got = collections.Counter(), 0
        for i, s in enumerate(sch):
            rows, st = get('SchoolSchedule', ATPT_OFCDC_SC_CODE=code, SD_SCHUL_CODE=s['SD_SCHUL_CODE'], AA_FROM_YMD=fr, AA_TO_YMD=to)
            if rows:
                got += 1
            seen = set()
            for r in rows:
                k = (r.get('AA_YMD'), s['SCHUL_KND_SC_NM'], (r.get('EVENT_NM') or '').strip())
                if k[0] and k[2] and k not in seen:
                    seen.add(k); C[k] += 1
            if i % 200 == 0:
                print(' ', i, got, flush=True)
            time.sleep(0.05)
        doc = {'schools': dict(n), 'got': got, 'rows': [[d, kd, nm, c] for (d, kd, nm), c in sorted(C.items())]}
        p = os.path.join(OUT, '%s_%s_%s.json' % (code, fr, to)); json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
        print(code, '끝 학교', got, '갈래', len(C), p, flush=True)


if __name__ == '__main__':
    main()
