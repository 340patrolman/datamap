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

SIDO = {'서울특별시': '11', '부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '광주광역시': '12', '대전광역시': '30', '울산광역시': '31', '경기도': '41', '강원도': '51', '강원특별자치도': '51',
        '충청북도': '43', '충청남도': '44', '전라북도': '52', '전북특별자치도': '52', '전라남도': '12', '경상북도': '47', '경상남도': '48', '제주도': '50', '제주특별자치도': '50', '세종특별자치시': '36'}
def do_build():
    T = json.load(open(os.path.join(OUT, 'tables.json'), encoding='utf-8')); IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus']
    POP = {}
    for g in IX:
        try: POP[g['gu']] = json.load(open(os.path.join(ROOT, 'data', 'r', g['gu'], 'profile.json'), encoding='utf-8'))['gu_summary'].get('주민 계')
        except Exception: pass
    A = {}; unmatched = []   # 단체 이름 → {해: {세(시세·구세…): {재산세: [부과, 징수], 합계: […]}}}
    for o in T:
        m = re.search(r'부과징수 현황-(.+?)\((도세|시세|군세|구세)\)\s*$', o['nm'] or '')
        fn = os.path.join(OUT, o['tbl'] + '.json')
        if not m or not os.path.exists(fn) or '본청' in m.group(1): continue
        nm, kind = m.group(1).strip(), m.group(2); sd = SIDO.get((o['path'] or [''])[-1])
        if kind == '도세': continue   # 도세에는 재산세가 없다(도가 걷는 취득세·지방소비세 등) — 재산세는 시·군·구 표에
        e = A.setdefault((sd, nm), {})
        for r in json.load(open(fn, encoding='utf-8')):
            if r['C1_NM'] not in ('재산세', '합계') or r['ITM_NM'] not in ('부과액', '징수액'): continue
            try: v = float(r['DT'])
            except (TypeError, ValueError): continue
            y = e.setdefault(r['PRD_DE'], {}).setdefault(kind, {}).setdefault(r['C1_NM'], [0, 0]); y[0 if r['ITM_NM'] == '부과액' else 1] = v
    GU = {}; years = set()
    for (sd, nm), e in A.items():
        gs = [g for g in IX if g['sido'] == sd and (g['name'] == nm or g['name'].startswith(nm))]   # 「수원시」 표 → 수원시 구 네 곳에 같은 값(시 단위)
        if not gs: gs = [g for g in IX if g['name'] == nm]; gs = gs if len(gs) == 1 else []
        if not gs: unmatched.append('%s %s' % (sd, nm)); continue
        ys = {}
        for y, kk in e.items():
            lv = sum(v.get('재산세', [0, 0])[0] for v in kk.values()); co = sum(v.get('재산세', [0, 0])[1] for v in kk.values())
            if lv: ys[y] = [int(round(lv / 1000)), int(round(co / 1000)), {k: int(round(v.get('재산세', [0, 0])[0] / 1000)) for k, v in kk.items() if v.get('재산세', [0, 0])[0]}]; years.add(y)
        if not ys: continue
        last = max(ys); pop = sum(POP.get(g['gu']) or 0 for g in gs)
        for g in gs:
            GU[g['gu']] = {'y': [[y, ys[y][0], ys[y][1]] for y in sorted(ys)], 'by': ys[last][2], 'pc': round(ys[last][0] * 100 / pop, 1) if pop else None, 'city': nm if len(gs) > 1 else None}
    last = max(years)
    for sd in set(g['sido'] for g in IX):
        L = sorted({(v['city'] or k): v for k, v in GU.items() if k[:2] == sd and v['pc'] is not None}.items(), key=lambda x: -x[1]['pc'])
        for r, (k, v) in enumerate(L):
            for kk, vv in GU.items():
                if kk[:2] == sd and (vv is v or (v['city'] and vv['city'] == v['city'])): vv['r'] = [r + 1, len(L)]
    doc = {'schema': 'tg-gu-proptax/1', 'made': datetime.date.today().isoformat(), 'last': last,
           'source': '행정안전부 지방세통계(KOSIS orgId 110 · 「시도·시군구별 징수실적 › 기초자치단체별 부과징수 현황」 · 해마다 · 최근 6해) — 세목 「재산세」 부과액·징수액',
           'note': ['실제로 부과·징수된 재산세 총액이다(추정이 아니다) — 주택·토지·건축물을 모두 합친 값이라 「주택 보유세 범위(추정)」와 바로 견줄 수 없다',
                    '특별시·광역시의 자치구는 구세 재산세와 그 구에서 걷은 시세 재산세(특별시분·도시지역분 등)를 더했다(by 에 나눠 적음) · 시·군은 시세·군세 재산세',
                    '구가 있는 시(수원·성남 등)는 시 단위 표뿐이라 그 시의 구마다 같은 값이다(city 에 시 이름) · 1명당 값도 시 전체 주민으로 나눴다', '읍면동 단위는 공개되지 않는다',
                    '2026년 행정구역 개편(인천 제물포·영종·서해·검단구 등)으로 이름이 바뀐 곳은 옛 이름 표와 이어지지 않아 빠졌다: ' + (' · '.join(unmatched) or '없음')],
           'fields': 'gu{시군구 5자리: {y[[해, 재산세 부과액(백만 원), 징수액(백만 원)]…], by{세(구세·시세·군세): 마지막 해 부과액(백만 원)}, pc 마지막 해 주민 1명당 부과액(만 원), r[같은 시도 안 1명당 차례, 단체 수], city 시 단위 값이면 시 이름|null}}',
           'gu': GU}
    p = os.path.join(ROOT, 'data', 'gu-proptax.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('구', len(GU), '/', len(IX), '· 마지막 해', last, '· 못 맞춘 단체', unmatched, '· 바이트', os.path.getsize(p))
    for k in ('11650', '11680', '41591', '41111', '26350'): print(k, GU.get(k))

if __name__ == '__main__':
    {'list': do_list, 'fetch': do_fetch, 'build': do_build}[sys.argv[1]]()
