# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.74.0 — 🏷 이 동네 지명(서울역사편찬원 「서울 지명사전」 12,628건)
#   원자료: 07_API키/out/jimyeong/seoul_jimyeong_YYYYMMDD.csv(RUN_jimyeong.bat · name·mark·lat·lon·text) — 출처 메모 같은 폴더 _출처.md
#   ⚠ 이용조건 미확인(서울역사편찬원 02-420-1256 문의 전) → 원문 전문을 싣지 않는다: 설명의 **첫 문장만**(140자 넘으면 자름) + 원문 검색 주소. 설명 빈칸은 이름만.
#   동 잇기: mark A·B·C(좌표 있음) = 그 점이 든 행정동(서울 밖 점은 버리고 아래로) · mark 없음 = 설명 첫머리 「○○구 ○○동」 → 법정동 → 행정동(b2a 10%↑) · 둘 다 안 되면 구만
#   → data/r/<서울 구>/jimyeong.json  {d: {행정동 8자리: [[이름, 경도|null, 위도|null, mark, 첫 문장], …]}, g: [구 단위 …]}
#   py -3.12 -X utf8 tools/region/jimyeong-bake.py
import csv, json, os, glob, re, collections
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r')
SRC = sorted(glob.glob(os.path.join(KB, '07_API키', 'out', 'jimyeong', 'seoul_jimyeong_*.csv')))[-1]
feats = [f for f in json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features'] if f['properties']['sido'] == '11']
geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms)
def dong_at(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return feats[i]['properties']['adm_cd2'][:8]
GUN = {f['properties']['sggnm']: f['properties']['sgg'] for f in feats}
B2A = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a']
BJ = collections.defaultdict(list)
for k, v in B2A.items():
    if v['gu'][:2] == '11': BJ[(v['gu'], v['n'])] += [a[0] for a in v['a'] if a[2] >= 10]
HEAD = re.compile(r'^\s*([가-힣]+구)\s+([가-힣0-9]+?(?:동|가))(?=[0-9\s에의,·(]|$)')
def first(t):
    t = re.sub(r'\s+', ' ', t or '').strip()
    if not t: return ''
    m = re.search(r'(다|음)\.\s', t + ' '); s = t[:m.end()].strip() if m else t
    return s if len(s) <= 140 else s[:139] + '…'
OUT = collections.defaultdict(lambda: {'d': collections.defaultdict(list), 'g': []}); cnt = collections.Counter(); seen = set()
for r in csv.DictReader(open(SRC, encoding='utf-8-sig')):
    nm = r['name'].strip(); fs = first(r['text']); key = (nm, fs)
    if key in seen: cnt['같은 항목'] += 1; continue
    seen.add(key)
    lon = lat = None; adm = []
    if r['lat'] and r['lon']:
        try:
            lo, la = float(r['lon']), float(r['lat']); k = dong_at(lo, la)
            if k: adm = [k]; lon, lat = round(lo, 6), round(la, 6)
        except ValueError: pass
    m = HEAD.match(r['text'] or '')
    gu = adm[0][:5] if adm else (GUN.get(m.group(1)) if m else None)
    if not adm and m and gu: adm = BJ.get((gu, m.group(2)), [])[:3]
    e = [nm, lon, lat, r['mark'] or '', fs]
    if adm:
        for k in adm: OUT[k[:5]]['d'][k].append(e)
        cnt['점' if lon else '동(설명 첫머리)'] += 1
    elif gu: OUT[gu]['g'].append(e); cnt['구만'] += 1
    else: cnt['못 놓음'] += 1
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8'))
IX.setdefault('layers', {})['jimyeong'] = '🏷 이 동네 지명(서울 지명사전 · 첫 문장 + 원문 링크)'
for gu, o in OUT.items():
    doc = {'schema': 'tg-jimyeong/1', 'gu': gu, 'source': '서울역사편찬원 「서울 지명사전」(history.seoul.go.kr/archive/ggdic · 2026-10-07 수집 ' + os.path.basename(SRC) + ')',
           'note': '이용조건 확인 전 — 설명은 첫 문장만 싣고 원문은 지명사전에서 본다 · mark = 사이트 지도의 주소 신뢰도 표시(A·B·C 와 높음·보통·낮음 대응 미확인) · 좌표 없는 지명은 설명 첫머리 「○○구 ○○동」으로 동을 잡았다(근사)',
           'baked': '2026-10-07', 'link': 'https://history.seoul.go.kr/archive/ggdic/list.do?key=2211220002&pageIndex=1&sc_cate=1&sc=&sw=', 'd': o['d'], 'g': o['g']}
    p = os.path.join(R, gu, 'jimyeong.json'); os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    g = next((x for x in IX['gus'] if x['gu'] == gu), None)
    if g is not None: g.setdefault('bytes', {})['jimyeong'] = os.path.getsize(p)
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt), '구', len(OUT), sum(os.path.getsize(os.path.join(R, g, 'jimyeong.json')) for g in OUT), 'B')
