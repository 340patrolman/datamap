# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.1.0 — 📝 동 풀어 읽기의 「물가를 걷은 실질 증감」: 통계청 소비자물가지수(2020=100) 품목성질별(KOSIS 101 DT_1J22002) 월별 → 분기 평균
#   지역 C = 전국(T10)·서울(T11)·경기(T13 — 메타에서 이름으로 찾음) · 품목 J = 총지수(00)·외식(2231)
#   py -3.12 -X utf8 tools/region/cpi-bake.py  →  data/cpi.json  { q: { "20211": {서울: [총지수, 외식], …} } }
import json, os, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')

def main():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
    g = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
    meta = g('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=101&tblId=DT_1J22002&format=json&jsonVD=Y' % k)
    C = {x['ITM_NM']: x['ITM_ID'] for x in meta if x['OBJ_ID'] == 'C'}
    want = {'전국': C['전국'], '서울': C['서울특별시'], '경기': C['경기도']}
    u = ('https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=M&orgId=101&tblId=DT_1J22002&itmId=T&objL1=%s&objL2=00+2231&startPrdDe=202101&endPrdDe=203012'
         % (k, '+'.join(want.values())))
    rows = g(u)
    inv = {v: n for n, v in want.items()}; M = collections.defaultdict(lambda: collections.defaultdict(lambda: [[], []]))
    for r in rows:
        ym = r['PRD_DE']; q = ym[:4] + str((int(ym[4:6]) - 1) // 3 + 1); j = 0 if r['C2'] == '00' else 1
        M[q][inv[r['C1']]][j].append(float(r['DT']))
    out = {'schema': 'tg-cpi/1', 'source': '통계청 소비자물가지수(2020=100) 품목성질별 — KOSIS 101 DT_1J22002 · 월별을 분기 평균(그 분기에 나온 달만)',
           'fields': '{분기: {지역: [총지수, 외식]}}', 'last': max(r['PRD_DE'] for r in rows),
           'q': {q: {a: [round(sum(v[0]) / len(v[0]), 2) if v[0] else None, round(sum(v[1]) / len(v[1]), 2) if v[1] else None] for a, v in M[q].items()} for q in sorted(M)}}
    json.dump(out, open(os.path.join(ROOT, 'data', 'cpi.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('quarters', len(out['q']), 'last month', out['last'], out['q'][sorted(out['q'])[0]], out['q'][sorted(out['q'])[-1]])

if __name__ == '__main__':
    main()
