# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.85.0 — 🏚 시·군·구 미분양(국토교통부 · KOSIS 116 DT_MLTM_2082 「시·군·구별 미분양현황」 · 월 · 코워크 10/7 회신)
#   서울·경기·인천 시군구 최근 36달 → data/unsold.json {구 코드: [[연월, 호], …]} — 경기 「○○시」(일반구 있는 시)는 그 시의 구마다 같은 값
#   py -3.12 -X utf8 tools/region/unsold-bake.py
import json, os, re, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
nz = lambda s: re.sub(r'\s+', '', s or '')
k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
g = lambda u: json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
TBL = 'DT_MLTM_2082'
meta = g('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=116&tblId=%s&format=json&jsonVD=Y' % (k, TBL))
A = {x['ITM_NM']: x['ITM_ID'] for x in meta if x['OBJ_ID'].endswith('A')}
R = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); byName = {}
for x in R['gus']:
    sd = {'11': '서울', '41': '경기', '28': '인천'}.get(x['gu'][:2])
    if sd: byName[(sd, nz(x['name']))] = x['gu']
OUT = collections.defaultdict(dict); last = ''
for sd in ('서울', '경기', '인천'):
    u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=M&orgId=116&tblId=%s&itmId=ALL&objL1=%s&objL2=ALL&newEstPrdCnt=36' % (k, TBL, A[sd])
    rows = g(u)
    if not isinstance(rows, list): print(sd, rows); continue
    for r in rows:
        nm = nz(r.get('C2_NM'))
        if nm in ('계', '') or r['DT'] in ('-', ''): continue
        gu = byName.get((sd, nm)); cand = [gu] if gu else [v for (s2, n2), v in byName.items() if s2 == sd and n2.startswith(nm)]
        for gc in cand: OUT[gc][r['PRD_DE']] = int(float(r['DT']))
        last = max(last, r['PRD_DE'])
    print(sd, len(rows))
doc = {'schema': 'tg-unsold/1', 'source': '국토교통부 「시·군·구별 미분양현황」(KOSIS 116 DT_MLTM_2082 · 월)', 'last': last,
       'note': '공동주택 분양 뒤 팔리지 않은 호수(준공 전·후 합) · 일반구가 있는 경기 시는 시 값이 구마다 같다 · 집값·구매력의 참고 지표(늘면 그 지역 새 집 수요가 약하다는 신호)',
       'gu': {gc: [[ym, v[ym]] for ym in sorted(v)] for gc, v in OUT.items()}}
json.dump(doc, open(os.path.join(ROOT, 'data', 'unsold.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(len(OUT), last, doc['gu'].get('11650', [])[-3:], doc['gu'].get('41463', [])[-3:])
