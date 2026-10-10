# -*- coding: utf-8 -*-
# 깨진 글자 검사(v2.98.1 · 소유자 2026-10-09 「동작경찰서를 누르니 한글이 깨져 나온다 — 다른 곳·다른 레이어도 확인」)
#   py -3.12 -X utf8 tools/textcheck.py data/*.json data/r/*/*.json   → 파일마다 깨진 글 수(bin = 이진 조각 · fffd = � · cp949 = EUC-KR 을 UTF-8 로 잘못 읽은 꼴)와 보기 3개
#   자료를 다시 구운 뒤 · publish-data push 전에 한 번. 0 이 아니면 그 굽는 도구의 읽는 법(인코딩·xls)을 먼저 고친다. 지도는 txtFix 로 화면에서도 막는다.
#   2026-10-09 전수(지도 저장소 + 권역 8개 · 1,400여 파일): police-stats 동작 2024(xls 이진) · season zones 6개(서울시 원본 shp) · safety 소방 관할명(금천 55 · 종로 1 · 충남 1) · 경기 41220 어린이집 1
import json,sys,re,collections
HG=re.compile(r'[가-힣]')
CTRL=re.compile(r'[\x00-\x08\x0e-\x1f]')
def broken(s):
    if CTRL.search(s): return 'bin'
    if '�' in s: return 'fffd'
    if not re.search(r'[一-鿿가-힣]', s): return None
    try: r=s.encode('cp949',errors='replace').decode('utf-8',errors='replace')
    except Exception: return None
    if re.search(r'[\u4e00-\u9fff?]', s) and len(HG.findall(r))>=2 and r.count('\ufffd')<=len(HG.findall(r)): return 'cp949'
    return None
def walk(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items():
            if isinstance(k,str) and broken(k): yield p+'/{'+k[:15]+'}', k, broken(k)
            yield from walk(v,p+'/'+str(k)[:20])
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from walk(v,p+'['+str(i)+']')
    elif isinstance(o,str):
        b=broken(o)
        if b: yield p,o,b
tot=collections.Counter()
for f in sys.argv[1:]:
    try: d=json.load(open(f,encoding='utf-8'))
    except Exception as e: print(f,'읽기 실패',str(e)[:60]); continue
    hits=list(walk(d))
    if hits:
        c=collections.Counter(h[2] for h in hits); tot.update(c)
        print(f, dict(c)); [print('    ',p[:60],repr(s[:50])) for p,s,b in hits[:3]]
print('합계',dict(tot))
