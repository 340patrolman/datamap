# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.0.0 — 💰 손익 계산의 「업종 평균」(공식 통계) : 통계청·중기부 소상공인실태조사 + 통계청 기업생멸행정통계
#   KOSIS(키 = 07_API키/keys.json "kosis")
#   소상공인실태조사(142 · 시도 18 × 산업 중분류 54) : 주요지표 DT_3ME0100 · 영업시간 0127 · 영업일 0128 · 영업비용 0144 · 면적 0133 · 창업 준비기간 0113 · 임차형태 0131 · 운영 애로 0149 · 향후 계획 0154
#   신생기업 생존율(101) : 산업별 DT_2BD1103
#   py -3.12 -X utf8 tools/region/sbiz-bake.py fetch   → 07_API키/out/kosis/sbiz/<표>.json
#   py -3.12 -X utf8 tools/region/sbiz-bake.py build   → data/biz-bench.json (서울·경기·전국 × 54업종 · 최근 해)
import json, os, sys, time, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'kosis', 'sbiz')
T = [('142', 'DT_3ME0100', 'main'), ('142', 'DT_3ME0127', 'hours'), ('142', 'DT_3ME0128', 'days'), ('142', 'DT_3ME0144', 'cost'), ('142', 'DT_3ME0133', 'area'),
     ('142', 'DT_3ME0113', 'prep'), ('142', 'DT_3ME0131', 'lease'), ('142', 'DT_3ME0149', 'pain'), ('142', 'DT_3ME0154', 'plan'), ('101', 'DT_2BD1103', 'surv')]

def g(u):
    for a in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
        except Exception as e: print('retry', e); time.sleep(5)
    return []

def fetch():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']; os.makedirs(OUT, exist_ok=True)
    for org, tbl, nm in T:
        meta = g('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=%s&tblId=%s&format=json&jsonVD=Y' % (k, org, tbl))
        objs = []
        for x in meta:
            if x.get('OBJ_ID') != 'ITEM' and x.get('OBJ_ID') not in objs: objs.append(x['OBJ_ID'])
        u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=Y&orgId=%s&tblId=%s&itmId=ALL&newEstPrdCnt=3' % (k, org, tbl)
        for i in range(len(objs)): u += '&objL%d=ALL' % (i + 1)
        rows = g(u)
        if not isinstance(rows, list): print(tbl, 'ERR', str(rows)[:200]); rows = []
        json.dump({'tbl': tbl, 'meta': meta, 'objs': objs, 'rows': rows}, open(os.path.join(OUT, tbl + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        print(nm, tbl, len(rows), sorted({r.get('PRD_DE') for r in rows})[-3:] if rows else '')

def num(v):
    try: return float(v)
    except Exception: return None

def build():
    out = {'schema': 'tg-bizbench/1', 'source': '중소벤처기업부·통계청 「소상공인실태조사」(KOSIS 142 · DT_3ME0100·0127·0128·0144·0133·0113·0131·0149·0154) · 통계청 「기업생멸행정통계」 산업별 신생기업 생존율(KOSIS 101 DT_2BD1103)',
           'note': '값 = [값, 해] · 시도 단위는 대분류까지만 있는 표가 많다(지도는 시도 중분류 → 시도 대분류 → 전국 중분류 순으로 물러선다) · 시도 × 산업 평균이다 — 「음식점 및 주점업」은 한식·카페·주점·치킨을 다 합친 한 덩어리. 금액 단위는 표의 단위(대개 백만원) 그대로 UNIT 에 적었다.', 'sido': {}, 'units': {}, 'years': {}}
    want = {'전국', '서울특별시', '경기도'}
    for org, tbl, nm in T[:-1]:   # 항목마다 값이 있는 가장 최근 해 — [값, 해]
        J = json.load(open(os.path.join(OUT, tbl + '.json'), encoding='utf-8')); rows = J['rows']
        if not rows: continue
        out['years'][nm] = max(r['PRD_DE'] for r in rows)
        for r in sorted(rows, key=lambda r: r['PRD_DE']):
            sd = r.get('C1_NM'); ind = r.get('C2_NM'); item = r.get('ITM_NM'); v = num(r.get('DT'))
            if sd not in want or v is None: continue
            out['sido'].setdefault(sd, {}).setdefault(ind, {}).setdefault(nm, {})[item] = [v, r['PRD_DE']]
            out['units'][nm + '|' + item] = r.get('UNIT_NM')
    J = json.load(open(os.path.join(OUT, 'DT_2BD1103.json'), encoding='utf-8')); S = collections.defaultdict(dict)
    if J['rows']:
        yr = max(r['PRD_DE'] for r in J['rows']); out['years']['surv'] = yr
        for r in J['rows']:
            if r['PRD_DE'] != yr: continue
            S[r.get('C1_NM')][r.get('ITM_NM')] = num(r.get('DT'))
    out['surv'] = S
    fn = os.path.join(ROOT, 'data', 'biz-bench.json')
    json.dump(out, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('years', out['years'], 'bytes', os.path.getsize(fn), 'surv industries', len(S))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
