# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.15.0 — 🚌 광역시 버스 정류장 승하차(공공데이터포털 파일데이터)
#   대구광역시_정류소별 시간대별 승하차인원(15050942 · 달마다 정류소·시간대 05~23시 평균) → 가장 최근 달 · 정류소 자리 = OSM 같은 이름 정류장의 가운데(400m 안에 모일 때만 · 근사)
#      → 그 구 transit.json 「bus」(서울과 같은 꼴 [ID, 이름, 경도, 위도, 승차 24, 하차 24])
#   인천광역시_정류장별 이용승객 현황(15048264 · 시간대 없음) + 인천광역시_시내버스 정류소 현황(15074309 · 정류소번호·좌표) → data/bus-incheon.json(일평균 승하차)
#   ⚠ 인천 정류소 파일은 「위도」 칸에 경도, 「경도」 칸에 위도가 들어 있다(2026-02-28 판) — 값 범위로 가린다
#   py -3.12 -X utf8 tools/region/bus-bake.py
import csv, io, json, os, re, zipfile, collections, math
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'metro'); R = os.path.join(ROOT, 'data', 'r')
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')

def rows_of(b):
    for enc in ('utf-8-sig', 'cp949'):
        try: return list(csv.reader(io.StringIO(b.decode(enc))))
        except Exception: pass
def num(x):
    try: return float(str(x).replace(',', '').replace('"', ''))
    except ValueError: return 0.0
def norm(s):
    t = re.sub(r'\s|\(.*?\)|[.·]', '', s or '')
    for _ in range(2): t = re.sub(r'(건너|앞|맞은편|옆|뒤|정류장|정류소|1|2|3|방면)$', '', t)   # 길 건너·앞 정류장은 한 이름으로(근사)
    return t

def main():
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['sgg']) for f in g['features']]; tr = STRtree([x[0] for x in F])
    def gu_of(la, lo):
        p = Point(lo, la)
        for i in tr.query(p):
            if F[i][0].contains(p): return F[i][1]
    # OSM 정류장(대구 상자) — bstop.json 을 다시 쓴다
    osm = collections.defaultdict(list)
    for gu in os.listdir(R):
        if not gu.startswith('27') and gu not in ('47290',):   # 대구 + 경산(하양)
            continue
        p = os.path.join(R, gu, 'bstop.json')
        if os.path.exists(p):
            for la, lo, nm, ref in json.load(open(p, encoding='utf-8'))['pts']: osm[norm(nm)].append((la, lo))
    z = zipfile.ZipFile(os.path.join(MD, 'dgbus.bin')); files = []
    for i in z.infolist():
        n = i.filename
        try: n = n.encode('cp437').decode('cp949')
        except Exception: pass
        m = re.search(r'(\d{4})년(\d{1,2})월', n) or re.search(r'(\d{4})-(\d{2})~', n)
        if m: files.append(('%s%02d' % (m.group(1), int(m.group(2))), i))
    ym, inf = max(files); rows = rows_of(z.open(inf).read()); hd = rows[0]
    hi = {i: int(re.match(r'(\d+)', h).group(1)) for i, h in enumerate(hd) if re.match(r'\d+시', h)}
    S = collections.defaultdict(lambda: {'nm': '', 'on': [0] * 24, 'off': [0] * 24})
    for r in rows[1:]:
        if len(r) < 5: continue
        s = S[r[2]]; s['nm'] = r[1]; k = 'on' if '승' in r[3] else 'off'
        for i, h in hi.items(): s[k][h % 24] += num(r[i])
    add = collections.defaultdict(list); hit = miss = spread = 0
    for sid, s in S.items():
        c = osm.get(norm(s['nm']))
        if not c: miss += 1; continue
        la = sum(x[0] for x in c) / len(c); lo = sum(x[1] for x in c) / len(c)
        if max(math.hypot((x[0] - la) * 111000, (x[1] - lo) * 88000) for x in c) > 400: spread += 1; continue
        gu = gu_of(la, lo)
        if gu: add[gu].append([sid, s['nm'], round(lo, 5), round(la, 5), [round(v) for v in s['on']], [round(v) for v in s['off']]]); hit += 1
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}
    for gu, bus in add.items():
        if gu not in known: continue
        p = os.path.join(R, gu, 'transit.json')
        doc = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'schema': 'tg-transit/1', 'gu': gu, 'bus': [], 'sub': [], 'fields': {'bus': '[정류장ID, 이름, 경도, 위도, 승차 24, 하차 24]', 'sub': '[역, 노선, 경도, 위도, 승차 24, 하차 24]'}}
        doc['bus'] = bus; src = doc.get('source') if isinstance(doc.get('source'), dict) else {}
        src['bus'] = '대구광역시_정류소별 시간대별 승하차인원(공공데이터포털 15050942) ' + ym + ' 달 평균 — 정류소 자리는 OSM 같은 이름 정류장의 가운데(근사 · 길 건너 두 정류장이 한 점)'; doc['source'] = src; doc['ym'] = (doc.get('ym') or '') + (' · 버스 ' + ym)
        json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); known[gu].setdefault('bytes', {})['transit'] = os.path.getsize(p)
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('대구', ym, '정류소', len(S), '붙임', hit, '이름 없음', miss, '흩어짐', spread, '구', len(add))
    # 인천 — 일평균만
    st = rows_of(open(os.path.join(MD, 'icstop.bin'), 'rb').read()); pos = {}
    for r in st[1:]:
        if len(r) < 10: continue
        a, b = num(r[7]), num(r[9]); la, lo = (b, a) if a > 100 else (a, b)
        if 33 < la < 39 and 124 < lo < 132: pos[r[2].strip()] = (la, lo)
    rb = rows_of(open(os.path.join(MD, 'icbus.bin'), 'rb').read()); out = []; nm_ = 0
    for r in rb[1:]:
        if len(r) < 8: continue
        p = pos.get(r[1].strip())
        if not p: nm_ += 1; continue
        on, off, day = num(r[2]), num(r[3]), num(r[7]); tot = on + off
        out.append([r[0], r[1], round(p[1], 5), round(p[0], 5), round(day * on / tot) if tot else 0, round(day * off / tot) if tot else 0])
    json.dump({'schema': 'tg-busday/1', 'source': '인천광역시_정류장별 이용승객 현황(공공데이터포털 15048264 · 2025-06-30 판) · 자리 = 인천광역시_시내버스 정류소 현황(15074309 · 2026-02-28)', 'fields': '[이름, 정류소번호, 경도, 위도, 승차 하루 평균, 하차 하루 평균]',
               'note': '시간대 없음 — 일평균 승하차를 승차·하차 비율로 나눴다', 'stops': out}, open(os.path.join(ROOT, 'data', 'bus-incheon.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('인천 정류장', len(out), '자리 못 찾음', nm_)

if __name__ == '__main__': main()
