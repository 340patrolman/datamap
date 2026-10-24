# -*- coding: utf-8 -*-
"""관할 경계 도로 표 → data/jur-road-seocho.json (2026-10-24)

정본은 T-Book index.html(v24.10~)의 BR_OWN·BR_LN — 소유자 「경계 도로는 북쪽·동쪽 서가 맡는다」(규칙 장부 RULE-JUR-3 · FK-JUR-BORDER-1·2).
지도는 그 표를 글자 그대로 옮겨 쓴다(두 앱이 같은 자리에서 다른 서를 말하지 않게). 값을 고치려면 T-Book 쪽을 고치고 이 도구를 다시 돌린다.

  py -3.12 -X utf8 tools/region/jurroad-bake.py [index.html 경로 또는 URL — 없으면 라이브 raw]
"""
import json, os, re, sys, urllib.request, hashlib, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = sys.argv[1] if len(sys.argv) > 1 else 'https://raw.githubusercontent.com/340patrolman/traffic-app/main/index.html'
s = (urllib.request.urlopen(SRC, timeout=60).read() if SRC.startswith('http') else open(SRC, 'rb').read()).decode('utf-8')
ver = re.search(r"const APP_VERSION='(v[\d.]+)'", s).group(1)
def grab(nm):
    m = re.search(r'var ' + nm + r'=(\{[^;]*\}|\[.*?\]);\n', s, re.S)
    if not m: raise SystemExit('T-Book %s 에 %s 가 없다 — v24.10 이전 판인가' % (ver, nm))
    t = m.group(1).replace("'", '"')
    if t.startswith('{'): t = re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', t)   # BR_ST 의 따옴표 없는 열쇠
    return json.loads(t)
ST, OWN, LN = grab('BR_ST'), grab('BR_OWN'), grab('BR_LN')
assert len(OWN) == 16, len(OWN)
for L in LN: assert isinstance(L[0], str) and len(L[0]) == 2 and L[0][0] in ST and L[0][1] in ST and (len(L) - 2) % 2 == 0 and len(L) >= 6, L[:3]
out = {'schema': 'jur-road/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
       'source': 'T-Book %s index.html BR_ST·BR_OWN·BR_LN 그대로(sha256 %s…) — 소유자 현장 기준 「경계 도로는 북쪽·동쪽 서가 맡는다」(RULE-JUR-3 · FK-JUR-BORDER-1·2) · 도로 선 = 국가교통정보센터 ITS 표준노드링크 · 양옆 관할 = 통계청 SGIS 행정동(가공 admdongkor · CC BY 4.0)' % (ver, hashlib.sha256(s.encode('utf-8')).hexdigest()[:12]),
       'note': 'own = [위도, 경도, 서 글자] 교차로 자리(40m 안이면 먼저) · ln = [맡는 서 글자 + 반대쪽 서 글자, 폭 m(길 가운데에서), 위도, 경도, …] · 그 밖은 종전 판정(관할 경계 · 행정동)',
       'fields': {'st': '서 글자 → 경찰서 이름', 'own': '[위도, 경도, 서 글자] — 소유자가 정한 교차로(40m 안이면 그 서)', 'ln': '[맡는 서 글자 + 반대쪽 서 글자, 폭 m, 위도, 경도, 위도, 경도, …] — 경계 도로 위 조각(길 가운데에서 폭 안이면 맡는 서)'},
       'st': ST, 'own': OWN, 'ln': LN}
p = os.path.join(ROOT, 'data', 'jur-road-seocho.json')
json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', ver, 'own', len(OWN), 'ln', len(LN), os.path.getsize(p), 'B')
