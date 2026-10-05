# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 구 단위 「사는 형편」: 2020 인구주택총조사(통계청 · KOSIS) 시군구
#   점유형태(DT_1PE2002 거처의 종류별/점유형태별 가구 · 일반가구 · 거처 계) → 자기집·전세·월세(보증금 있는+없는+사글세)·무상 비율
#   교육정도(DT_1PM2001 성·연령·교육정도별 인구 · 내국인 · 25세 이상) → 4년제 대학 졸업 이상 · 2~3년제 졸업 비율(재학·중퇴는 뺌)
#   ⚠ 동 단위 공식 값은 없다(SGIS 점유형태는 2010 까지) — 구 평균으로만 쓴다 · 화성시 새 구·부천시 구는 2020 에 없어 시 전체 값
#   py -3.12 -X utf8 tools/region/guCensus-bake.py → data/gu-census.json
import json, os, re, urllib.request, urllib.parse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
K = urllib.parse.quote(json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis'], safe='')

def fl(v):
    try: return float(v)
    except Exception: return 0.0   # '-' = 0 또는 비밀보호

def data(tb, **obj):
    q = '&'.join('%s=%s' % (k, v) for k, v in obj.items())
    u = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&itmId=ALL&format=json&jsonVD=Y&prdSe=F&startPrdDe=2020&endPrdDe=2020&orgId=101&tblId=%s&%s' % (K, tb, q)
    j = json.loads(urllib.request.urlopen(u, timeout=120).read().decode('utf-8', 'replace'))
    if isinstance(j, dict): raise RuntimeError(j)
    return j

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    T = collections.defaultdict(dict); nm = {}
    for r in data('DT_1PE2002', objL1='ALL', objL2='00'):
        a = r['C1']; T[a][r['ITM_ID']] = fl(r['DT']); nm[a] = r['C1_NM']
    E = collections.defaultdict(lambda: collections.defaultdict(float))
    meta = json.loads(urllib.request.urlopen('https://kosis.kr/openapi/statisticsData.do?method=getMeta&type=ITM&apiKey=%s&orgId=101&tblId=DT_1PM2001&format=json&jsonVD=Y' % K, timeout=60).read().decode('utf-8'))
    ages = [x['ITM_ID'] for x in meta if x['OBJ_ID'] == 'B' and len(x['ITM_ID']) == 3 and x['ITM_ID'] != '000' and re.match(r'(\d+)', x['ITM_NM']) and int(re.match(r'(\d+)', x['ITM_NM']).group(1)) >= 25]
    for b in ages:
        for r in data('DT_1PM2001', objL1='ALL', objL2='0', objL3=b):
            E[r['C1']][r['ITM_ID']] += fl(r['DT'])
    # 지도 구(행정 코드) ← 총조사 지역(옛 통계 코드) — 시·도 이름 + 구 이름으로 맞춘다
    sido_of = {}
    for a, n in nm.items():
        if len(a) == 2: sido_of[a] = n
    by = {}
    for a, n in nm.items():
        if len(a) == 5: by[(sido_of.get(a[:2], ''), n)] = a
    out = {}; miss = []
    for g in IX['gus']:
        sd = '서울특별시' if g['gu'][:2] == '11' else '경기도'; name = g['name']
        cand = [name, name.replace(' ', ''), re.sub(r'^(\S+시)\s*\S+구$', r'\1', name)]
        a = None
        for c in cand:
            if (sd, c) in by: a = by[(sd, c)]; break
        if not a: miss.append(name); continue
        t = T[a]; hh = t.get('T10') or 1; e = E.get(a, {})
        p25 = e.get('T10', 0) - e.get('T90', 0)   # 6세 이상 중 25세 이상만 더했으므로 T10 = 25세 이상 합
        out[g['gu']] = {'src': nm[a] if nm[a].replace(' ', '') == name.replace(' ', '') else nm[a] + '(시 전체)', 'hh': int(hh),
                        'own': round(t.get('T11', 0) / hh * 100, 1), 'jeonse': round(t.get('T12', 0) / hh * 100, 1),
                        'wolse': round((t.get('T13', 0) + t.get('T14', 0) + t.get('T15', 0)) / hh * 100, 1), 'free': round(t.get('T16', 0) / hh * 100, 1),
                        'uni4': round((e.get('T61', 0) + e.get('T71', 0) + e.get('T81', 0)) / (e.get('T10') or 1) * 100, 1) if e else None,
                        'col2': round(e.get('T51', 0) / (e.get('T10') or 1) * 100, 1) if e else None}
    for sd, a in (('서울', '11'), ('경기', '31')):
        t = T.get(a) or {}; hh = t.get('T10') or 1; e = E.get(a, {})
        out['_' + sd] = {'own': round(t.get('T11', 0) / hh * 100, 1), 'jeonse': round(t.get('T12', 0) / hh * 100, 1), 'wolse': round((t.get('T13', 0) + t.get('T14', 0) + t.get('T15', 0)) / hh * 100, 1),
                         'uni4': round((e.get('T61', 0) + e.get('T71', 0) + e.get('T81', 0)) / (e.get('T10') or 1) * 100, 1) if e else None}
    doc = {'schema': 'tg-gucensus/1', 'source': '통계청 2020 인구주택총조사(KOSIS DT_1PE2002 점유형태 · DT_1PM2001 교육정도) — 시군구 · 5년마다(다음 2025 결과)',
           'fields': 'hh 일반가구 · own 자기집 % · jeonse 전세 % · wolse 월세(보증금 있는·없는·사글세) % · free 무상 % · uni4 = 25세 이상 내국인 중 4년제 대학 졸업 이상(대학원 포함) % · col2 = 2~3년제 졸업 %',
           'note': '동 단위 공식 값 없음 → 구 평균 · 2020 년 값(화성 새 구·부천 구는 시 전체)', 'gu': out}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'gu-census.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('구', len(out) - 2, '못 맞춤', miss, '서초', out.get('11650'), '서울', out.get('_서울'))

if __name__ == '__main__': main()
