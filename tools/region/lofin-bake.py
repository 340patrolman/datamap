# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏛 시·군·구가 실제로 걷은 재산세(소유자 2026-10-10 「읍면동별 세금 … 그 지역을 파악하기 좋은 방법」 · 추정(ptax-dong.json) 옆에 놓을 「실제 걷힌 총액」)
#   출처 = 행정안전부 지방세통계(KOSIS orgId 110 · 「시도·시군구별 징수실적 › 기초자치단체별 부과징수 현황-○○(시세·군세·구세)」 · 2005~ · 해마다) — 표가 시·군·구마다 하나라 목록을 걸어 모은다
#   싣는 것 = 세목 「재산세」·「합계」의 부과액·징수액(천 원) 최근 6해 · 읍면동 단위는 공개되지 않는다 · 주택·토지·건축물을 합친 재산세다(주택분만이 아니다)
#   ⚠ 특별시·광역시 자치구의 재산세는 구세(서울은 특별시분 재산세 공동과세가 따로 — 그 표의 「재산세」는 구에 귀속된 몫이다) · 시·군은 시·군세 재산세
#   py -3.12 -X utf8 tools/region/lofin-bake.py list  → 07_API키/out/lofin/tables.json(표 목록) · fetch → 표마다 받아 둠 · build → data/gu-proptax.json
import json, os, sys, time, re, urllib.request, urllib.parse, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'lofin')
def key(): return json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
def g(u, tries=4):
    for i in range(tries):
        try:
            t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
            return json.loads(t)
        except Exception as e:
            if i == tries - 1: return {'err': 'x', 'errMsg': type(e).__name__}
            time.sleep(3 * (i + 1))

def walk(k, pid, path, out, depth=0):
    j = g('https://kosis.kr/openapi/statisticsList.do?method=getList&apiKey=%s&vwCd=MT_ZTITLE&parentListId=%s&format=json&jsonVD=Y' % (k, pid))
    if not isinstance(j, list): return
    for r in j:
        if r.get('TBL_ID'):
            if r.get('ORG_ID') == '110': out.append({'tbl': r['TBL_ID'], 'nm': r.get('TBL_NM'), 'path': path})
        elif r.get('LIST_ID') and depth < 6:
            walk(k, r['LIST_ID'], path + [r.get('LIST_NM')], out, depth + 1)

def do_list():
    os.makedirs(OUT, exist_ok=True); k = key()
    top = g('https://kosis.kr/openapi/statisticsList.do?method=getList&apiKey=%s&vwCd=MT_ZTITLE&parentListId=%s&format=json&jsonVD=Y' % (k, sys.argv[2] if len(sys.argv) > 2 else 'O'))
    print('맨 위', [(r.get('LIST_ID'), r.get('LIST_NM')) for r in top] if isinstance(top, list) else top)
    if len(sys.argv) > 3:
        out = []; walk(k, sys.argv[3], [], out)
        json.dump(out, open(os.path.join(OUT, 'tables.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
        print('표', len(out), [o['nm'] for o in out[:5]])

def do_fetch():
    k = key(); T = json.load(open(os.path.join(OUT, 'tables.json'), encoding='utf-8')); n = 0
    for o in T:
        if '기초자치단체별 부과징수 현황' not in (o['nm'] or ''): continue
        fn = os.path.join(OUT, o['tbl'] + '.json')
        if os.path.exists(fn): continue
        d = g('https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=Y&orgId=110&tblId=%s&itmId=ALL&objL1=ALL&newEstPrdCnt=6' % (k, o['tbl']))
        if isinstance(d, list):
            json.dump([{x: r.get(x) for x in ('PRD_DE', 'C1_NM', 'ITM_NM', 'DT', 'UNIT_NM')} for r in d], open(fn, 'w', encoding='utf-8'), ensure_ascii=False); n += 1
        else: print('못 받음', o['tbl'], o['nm'], d)
        time.sleep(0.25)
    print('받음', n)

if __name__ == '__main__':
    {'list': do_list, 'fetch': do_fetch}[sys.argv[1]]()
