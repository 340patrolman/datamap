# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.76.0 — 🩺 병의원·약국(건강보험심사평가원 「전국 병의원 및 약국 현황」 · 보건의료빅데이터개방시스템 sno=11925 · 공공누리 출처표시 · 분기)
#   원자료: 07_API키/out/hira/hira_YYYY_M.zip(소유자 2026-10-07 「모두 진행」 · 2026.6 판 64MB) — 1.병원정보서비스 · 2.약국정보서비스 · 5.진료과목정보
#   좌표가 든 시군구(지도 시군구 경계 · 13_관할경계 hjd) 마다 → data/r/<구>/hira.json
#     h = [x, y, 종별 번호, 기관명, 총의사수, 개설 해, 전화, [[과목 번호, 과목별 전문의수]…]]  · p = [x, y, 약국명, 개설 해, 전화]
#     x, y = (경도 − o0)·k0, (위도 − o1)·k1 정수(med.json 과 같은 꼴)
#   암호화요양기호는 싣지 않는다(과목 잇기에만 씀).
#   py -3.12 -X utf8 tools/region/hira-bake.py
import zipfile, io, json, os, glob, collections, openpyxl
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r')
ZP = sorted(glob.glob(os.path.join(KB, '07_API키', 'out', 'hira', 'hira_*.zip')))[-1]; ED = os.path.basename(ZP)[5:-4].replace('_', '.')
feats = json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features']
geoms = [shape(f['geometry']) for f in feats]; tree = STRtree(geoms)
def gu_of(lon, lat):
    p = Point(lon, lat)
    for i in tree.query(p):
        if geoms[i].contains(p): return feats[i]['properties']['sgg']
z = zipfile.ZipFile(ZP)
def sheet(pref):
    for i in z.infolist():
        n = i.filename
        if not (i.flag_bits & 0x800):
            try: n = n.encode('cp437').decode('cp949')
            except UnicodeEncodeError: pass
        if os.path.basename(n).startswith(pref): return openpyxl.load_workbook(io.BytesIO(z.read(i)), read_only=True).active.iter_rows(values_only=True)
    raise SystemExit('없음 ' + pref)
def yr(d): return d.year if hasattr(d, 'year') else (int(str(d)[:4]) if d and str(d)[:4].isdigit() else 0)
SPN, SPI, SP = [], {}, collections.defaultdict(list)
it = sheet('5.'); H = {h: i for i, h in enumerate(next(it))}
for r in it:
    nm = r[H['진료과목코드명']]
    if nm not in SPI: SPI[nm] = len(SPN); SPN.append(nm)
    SP[r[H['암호화요양기호']]].append([SPI[nm], int(r[H['과목별 전문의수']] or 0)])
TYN, TYI = [], {}
OUT = collections.defaultdict(lambda: {'h': [], 'p': []}); cnt = collections.Counter()
it = sheet('1.'); H = {h: i for i, h in enumerate(next(it))}
for r in it:
    try: lon, lat = float(r[H['좌표(X)']]), float(r[H['좌표(Y)']])
    except (TypeError, ValueError): cnt['병의원 좌표 없음'] += 1; continue
    g = gu_of(lon, lat)
    if not g: cnt['병의원 경계 밖'] += 1; continue
    t = r[H['종별코드명']]
    if t not in TYI: TYI[t] = len(TYN); TYN.append(t)
    OUT[g]['h'].append([lon, lat, TYI[t], r[H['요양기관명']], int(r[H['총의사수']] or 0), yr(r[H['개설일자']]), r[H['전화번호']] or '', sorted(SP.get(r[H['암호화요양기호']], []), key=lambda q: -q[1])])
    cnt['병의원'] += 1
it = sheet('2.'); H = {h: i for i, h in enumerate(next(it))}
for r in it:
    try: lon, lat = float(r[H['좌표(X)']]), float(r[H['좌표(Y)']])
    except (TypeError, ValueError): cnt['약국 좌표 없음'] += 1; continue
    g = gu_of(lon, lat)
    if not g: cnt['약국 경계 밖'] += 1; continue
    OUT[g]['p'].append([lon, lat, r[H['요양기관명']], yr(r[H['개설일자']]), r[H['전화번호']] or '']); cnt['약국'] += 1
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); IX.setdefault('layers', {})['hira'] = '🩺 병의원·약국(심평원 · 진료과목·전문의·의사 수)'
tot = 0
for g, o in OUT.items():
    pts = [q[:2] for q in o['h']] + [q[:2] for q in o['p']]; o0 = [min(q[0] for q in pts), min(q[1] for q in pts)]; K = [88800, 111000]
    enc = lambda q: [round((q[0] - o0[0]) * K[0]), round((q[1] - o0[1]) * K[1])]
    doc = {'schema': 'tg-hira/1', 'gu': g, 'ed': ED, 'source': '건강보험심사평가원 「전국 병의원 및 약국 현황 ' + ED + '」(보건의료빅데이터개방시스템 · 병원정보서비스·약국정보서비스·진료과목정보 · 공공누리 출처표시)',
           'note': '분기말 기준 · 과목별 전문의수 0 = 그 과목을 진료하지만 그 과목 전문의는 없음 · 좌표는 심평원 제공 값', 'o': o0, 'k': K, 'types': TYN, 'specs': SPN,
           'h': [enc(q) + q[2:] for q in o['h']], 'p': [enc(q) + q[2:] for q in o['p']]}
    p = os.path.join(R, g, 'hira.json')
    if not os.path.isdir(os.path.dirname(p)): cnt['지도에 없는 구'] += 1; continue
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); tot += os.path.getsize(p)
    x = next((x for x in IX['gus'] if x['gu'] == g), None)
    if x is not None: x.setdefault('bytes', {})['hira'] = os.path.getsize(p)
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print(dict(cnt), '구', len(OUT), tot, 'B', TYN)
