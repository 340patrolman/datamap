# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.3.0 — 서울 동별 사업체·종사자 10년(2015~2024) + 업종 대분류(2017~2024)
#   출처: KOSIS 서울특별시 「사업체현황(종사자규모별/동별)」 DT_201004_O040003_2015 · 「사업체현황(산업대분류별/동별)」 DT_201004_O040004_2017
#         (통계청 전국사업체조사 · KOSIS 공유서비스 OpenAPI · 키 = 07_API키/keys.json 의 kosis)
#   받기는 이 파일 아래 fetch() · 굽기는 fac.json 의 동마다 'bz'·'bzi' 를 더한다 — **fac-bake 다음에** 돌린다(fac-bake 가 fac.json 을 새로 쓰면 지워진다).
#   py -3.12 -X utf8 tools/region/biz10-bake.py fetch|build
import json, os, sys, re, time, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'kosis')
norm = lambda s: re.sub(r'[\s·.,ㆍ()]', '', s or '')

def fetch():
    ks = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis']
    def g(u):
        for a in range(4):
            try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8'))
            except Exception as e: print('retry', e); time.sleep(5)
    B = 'https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&format=json&jsonVD=Y&prdSe=Y&orgId=201&' % ks
    os.makedirs(OUT, exist_ok=True)
    json.dump(g(B + 'tblId=DT_201004_O040003_2015&itmId=13103128841T1&objL1=ALL&objL2=001001+001002&startPrdDe=2015&endPrdDe=2030'), open(os.path.join(OUT, 'seoul_biz_tot.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    allr = []
    for y in range(2017, 2031):
        r = g(B + 'tblId=DT_201004_O040004_2017&itmId=13103125585T1&objL1=ALL&objL2=ALL&objL3=001+002&startPrdDe=%d&endPrdDe=%d' % (y, y))
        if isinstance(r, list): allr += r
    json.dump(allr, open(os.path.join(OUT, 'seoul_biz_ind.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def build():
    T = json.load(open(os.path.join(OUT, 'seoul_biz_tot.json'), encoding='utf-8'))
    I = json.load(open(os.path.join(OUT, 'seoul_biz_ind.json'), encoding='utf-8'))
    nm = {}   # C1 코드 → 이름(구 = 6자리, 동 = 9자리)
    for r in T + I: nm[r['C1']] = r['C1_NM']
    def key(c1):
        if len(c1) != 9: return None
        return (norm(nm.get(c1[:6], '')), norm(nm.get(c1, '')))
    tot = collections.defaultdict(dict)   # (구, 동) → {해: [사업체, 종사자]}
    for r in T:
        k = key(r['C1'])
        if not k or r.get('DT') in (None, '', '-'): continue
        v = tot[k].setdefault(r['PRD_DE'], [0, 0]); v[0 if r['C2'] == '001001' else 1] = int(float(r['DT']))
    ind = collections.defaultdict(lambda: collections.defaultdict(dict))   # (구, 동) → 업종 → {해: 사업체}
    for r in I:
        k = key(r['C1'])
        if not k or r.get('C3') != '001' or r['C2'] == '001' or r.get('DT') in (None, '', '-'): continue
        ind[k][r['C2_NM']][r['PRD_DE']] = int(float(r['DT']))
    yrs = sorted({y for v in tot.values() for y in v})
    hit = miss = 0; gb = {}
    for gdir in sorted(os.listdir(os.path.join(ROOT, 'data', 'r'))):
        if not gdir.startswith('11'): continue
        fn = os.path.join(ROOT, 'data', 'r', gdir, 'fac.json')
        if not os.path.exists(fn): continue
        F = json.load(open(fn, encoding='utf-8')); gname = norm(F.get('name', ''))
        for code, d in F['dong'].items():
            k = (gname, norm(d['name']))
            if k in tot:
                hit += 1; d['bz'] = [[y] + tot[k].get(y, [None, None]) for y in yrs]
                if k in ind:
                    iy = sorted({y for v in ind[k].values() for y in v}); y0, y1 = iy[0], iy[-1]
                    d['bzi'] = sorted([[n, v.get(y0), v.get(y1)] for n, v in ind[k].items() if v.get(y1) or v.get(y0)], key=lambda q: -(q[2] or 0))
                    d['bziy'] = [y0, y1]
            else: miss += 1; print('miss', F.get('name'), d['name'])
        F['bzsrc'] = 'KOSIS 서울특별시 사업체현황(종사자규모별/동별) 2015~%s · (산업대분류별/동별) 2017~%s — 통계청 전국사업체조사' % (yrs[-1], max(r['PRD_DE'] for r in I))
        json.dump(F, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gdir] = os.path.getsize(fn)
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8'))
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['fac'] = gb[g2['gu']]
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('years', yrs, 'hit', hit, 'miss', miss)

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
