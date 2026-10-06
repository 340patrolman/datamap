# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.15.0 — 🚇 광역시 도시철도 역별 시간대 승하차(공공데이터포털 파일데이터) → 그 역이 든 구의 transit.json 「sub」(서울과 같은 꼴)
#   대전교통공사_시간대별 승하차인원(15060591) · 광주교통공사_역일시간대별 승하차량(15060048) — 일별·역별·시간대별 → 평일 하루 평균
#   대구교통공사_월별하차인원(15060372) — 월별 하차만 → 시간대가 없어 transit 에 넣지 않고 data/metro-daegu.json(역·하차 하루 평균)
#   ⚠ 부산교통공사(3057229) 파일은 받으면 그림 파일이 내려와(2026-10-06) OpenAPI 활용신청 대기 · 인천교통공사는 공개 파일을 아직 못 찾음
#   역 자리 = OpenStreetMap 역(railway=station|halt · subway/light_rail · © OpenStreetMap contributors · ODbL) 이름으로 맞춤(「역」 떼고)
#   py -3.12 -X utf8 tools/region/metro-bake.py
import csv, io, json, os, re, datetime, collections, osmium
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MD = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'metro'); R = os.path.join(ROOT, 'data', 'r')
PBF = r'C:\Users\knpth\osmwork\kr.pbf'; HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
CITY = {'daejeon': ('대전 도시철도 1호선', (36.25, 127.30, 36.42, 127.48)), 'gwangju': ('광주 도시철도 1호선', (35.08, 126.75, 35.23, 126.95)), 'daegu': ('대구 도시철도', (35.78, 128.43, 35.97, 128.86))}

class H(osmium.SimpleHandler):
    def __init__(self): super().__init__(); self.o = []
    def node(self, n):
        t = n.tags
        if t.get('railway') in ('station', 'halt', 'stop') or t.get('public_transport') == 'station':
            nm = t.get('name') or ''
            if nm: self.o.append((re.sub(r'\s|역$|\(.*?\)', '', nm), n.location.lat, n.location.lon, t.get('station', '') + t.get('subway', '') + t.get('light_rail', '')))

def norm(s): return re.sub(r'\s|역$|\(.*?\)', '', s or '')

def read(fn):
    b = open(os.path.join(MD, fn), 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):
        try: return list(csv.reader(io.StringIO(b.decode(enc))))
        except Exception: pass

def hourly(rows, hcols):   # 평일 하루 평균 [승차 24, 하차 24]
    hd = rows[0]; hi = {}
    for i, h in enumerate(hd):
        m = re.match(r'(\d{2})[-_]', h)
        if m: hi[i] = int(m.group(1)) % 24
    S = collections.defaultdict(lambda: {'on': [0] * 24, 'off': [0] * 24, 'd': set()})
    for r in rows[1:]:
        if len(r) < 5: continue
        try: d = datetime.date.fromisoformat(r[0].strip())
        except ValueError: continue
        if d.weekday() >= 5: continue
        s = S[norm(r[2])]; s['d'].add(d); k = 'on' if '승' in r[3] else 'off'
        for i, h in hi.items():
            try: s[k][h] += int(float(r[i] or 0))
            except ValueError: pass
    out = {}
    for nm, s in S.items():
        n = len(s['d']) or 1; out[nm] = ([round(v / n) for v in s['on']], [round(v / n) for v in s['off']], min(s['d']), max(s['d']))
    return out

def main():
    h = H(); h.apply_file(PBF); print('OSM 역', len(h.o), flush=True)
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['sgg']) for f in g['features']]; tr = STRtree([x[0] for x in F])
    def gu_of(la, lo):
        p = Point(lo, la)
        for i in tr.query(p):
            if F[i][0].contains(p): return F[i][1]
    ALI = {'학동증심사': '학동·증심사입구', '컨벤션센터': '김대중컨벤션센터'}
    def find(city, nm):
        nm = norm(ALI.get(nm, nm))
        b = CITY[city][1]; c = [o for o in h.o if b[0] <= o[1] <= b[2] and b[1] <= o[2] <= b[3] and o[0] == nm]
        if not c: c = [o for o in h.o if b[0] <= o[1] <= b[2] and b[1] <= o[2] <= b[3] and (o[0].startswith(nm) or nm.startswith(o[0])) and len(o[0]) >= 2]
        c.sort(key=lambda o: 0 if ('subway' in o[3] or 'light_rail' in o[3]) else 1)
        return c[0] if c else None
    add = collections.defaultdict(list); miss = []; per = {}
    for city, fn in (('daejeon', 'daejeon.bin'), ('gwangju', 'gwangju.bin')):
        H24 = hourly(read(fn), None)
        for nm, (on, off, d0, d1) in H24.items():
            o = find(city, nm)
            if not o: miss.append(city + ':' + nm); continue
            gu = gu_of(o[1], o[2])
            if gu: add[gu].append([nm, [CITY[city][0]], round(o[2], 5), round(o[1], 5), on, off]); per[city] = '%s~%s 평일' % (d0, d1)
    # 대구 — 월별 하차만
    rows = read('daegu.bin'); hd = rows[0]; last = rows[-1]; ym = last[0] + last[1]
    days = (datetime.date(int(last[0]) + (int(last[1]) // 12), int(last[1]) % 12 + 1, 1) - datetime.date(int(last[0]), int(last[1]), 1)).days
    dg = []
    for i, nm in enumerate(hd[2:], 2):
        try: v = int(float(last[i] or 0))
        except ValueError: continue
        o = find('daegu', norm(nm))
        if not o: miss.append('daegu:' + nm); continue
        dg.append([norm(nm), round(o[2], 5), round(o[1], 5), round(v / days), gu_of(o[1], o[2])])
    json.dump({'schema': 'tg-metro-daegu/1', 'source': '대구교통공사_월별하차인원(공공데이터포털 15060372) · ' + ym + ' · 역 자리 = OSM', 'fields': '[역, 경도, 위도, 하차 하루 평균(그 달 ÷ 날수), 시군구]', 'note': '대구는 월별 하차만 공개 — 시간대·승차 없음', 'stations': dg},
              open(os.path.join(ROOT, 'data', 'metro-daegu.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {x['gu']: x for x in IX['gus']}
    for gu, subs in add.items():
        if gu not in known: continue
        p = os.path.join(R, gu, 'transit.json')
        doc = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {'schema': 'tg-transit/1', 'gu': gu, 'bus': [], 'sub': [], 'fields': {'bus': '[정류장ID, 이름, 경도, 위도, 승차 24, 하차 24]', 'sub': '[역, 노선, 경도, 위도, 승차 24, 하차 24]'}}
        doc['sub'] = subs; doc['ym'] = ' · '.join(sorted(set(per.values())))
        doc['source'] = {'bus': '버스 승하차 자료 없음(이 시도)', 'sub': '대전교통공사 시간대별 승하차인원(15060591) · 광주교통공사 역일시간대별 승하차량(15060048) — 공공데이터포털 · 평일 하루 평균 · 역 자리 = OSM'}
        json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); known[gu].setdefault('bytes', {})['transit'] = os.path.getsize(p)
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('역(대전·광주)', sum(len(v) for v in add.values()), '구', len(add), per, '대구', len(dg), ym, '못 맞춘 역', miss[:20], len(miss))

if __name__ == '__main__': main()
