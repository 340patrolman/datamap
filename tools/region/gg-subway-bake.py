# -*- coding: utf-8 -*-
# 데이터 압축지도 v1.3.0 — 경기(·인천 경계 안) 지하철·전철역 시간대 승차·하차
#   승하차: 서울시 지하철 호선별 역별 시간대별 승하차 인원(CardSubwayTime · 서울 열린데이터광장 · 2026년 6월) — 수도권 전 노선 역이 들어 있다
#   역 자리: 서울시 역사마스터(data/r/stations.json)에 없는 역은 OpenStreetMap(railway=station · Geofabrik 2026-10-03 · ODbL) 같은 이름 역
#   → 경기 구마다 data/r/<구>/transit.json 의 'sub' (서울 구 파일은 transit-bake 가 맡는다)
#   py -3.12 -X utf8 tools/region/gg-subway-bake.py
import json, os, importlib.util, collections
import osmium
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PBF = 'C:/Users/knpth/osmwork/kr.pbf'
spec = importlib.util.spec_from_file_location('fb', os.path.join(ROOT, 'tools', 'flow-bake.py')); fb = importlib.util.module_from_spec(spec); spec.loader.exec_module(fb)
YM = '202606'
nk = lambda s: (s or '').replace(' ', '').replace('역', '').split('(')[0]

class H(osmium.SimpleHandler):
    def __init__(self): super().__init__(); self.st = collections.defaultdict(list)
    def node(self, n):
        t = n.tags
        if t.get('railway') in ('station', 'halt') or (t.get('public_transport') == 'station' and t.get('train') == 'yes') or t.get('station') == 'subway':
            nm = t.get('name')
            if nm and 36.9 < n.location.lat < 38.3 and 126.3 < n.location.lon < 127.9: self.st[nk(nm)].append((n.location.lon, n.location.lat))

def main():
    sp = importlib.util.spec_from_file_location('db', os.path.join(ROOT, 'tools', 'region', 'dong-bake.py')); DB = importlib.util.module_from_spec(sp); sp.loader.exec_module(DB)
    feats, _ = DB.seoul_gus(); gs = [shape(x['geometry']) for x in feats]; tr = STRtree(gs)
    def gu(lon, lat):
        q = Point(lon, lat)
        for i in tr.query(q):
            if gs[i].contains(q): return feats[i]['properties']['sgg']
        return None
    rows = []
    for st in range(1, 3000, 1000):
        v = fb.seoul('json/CardSubwayTime/%d/%d/%s' % (st, st + 999, YM)).get('CardSubwayTime') or {}
        rows += v.get('row') or []
        if st + 999 >= (v.get('list_total_count') or 0): break
    sub = {}
    for r in rows:
        nm = r['STTN'].split('(')[0]
        s = sub.setdefault(nm, [[0] * 24, [0] * 24, []])
        if r['SBWY_ROUT_LN_NM'] not in s[2]: s[2].append(r['SBWY_ROUT_LN_NM'])
        for hr in range(24):
            k = hr if hr >= 4 else hr + 24
            for kk in ('HR_%d' % hr, 'HR_%d' % k):
                a = r.get(kk + '_GET_ON_NOPE')
                if a is not None: s[0][hr] += a; s[1][hr] += r.get(kk + '_GET_OFF_NOPE') or 0; break
    stn = collections.defaultdict(list)
    for it in json.load(open(os.path.join(ROOT, 'data', 'r', 'stations.json'), encoding='utf-8'))['items']: stn[it[0]].append((it[2], it[3]))
    h = H(); h.apply_file(PBF); print('osm stations', len(h.st))
    out = collections.defaultdict(list); miss = []
    for nm, s in sub.items():
        ps = stn.get(nm) or stn.get(nm.replace('역', '')) or h.st.get(nk(nm))
        if not ps: miss.append(nm); continue
        ps = [p for p in ps if abs(p[0] - ps[0][0]) < 0.02 and abs(p[1] - ps[0][1]) < 0.02]   # 같은 이름이 먼 곳에도 있으면 첫 묶음만
        lon, lat = sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps); g = gu(lon, lat)
        if not g or not g.startswith('41'): continue
        out[g].append([nm, s[2], round(lon, 5), round(lat, 5), [round(x / 30) for x in s[0]], [round(x / 30) for x in s[1]]])
    print('gg stations', sum(len(v) for v in out.values()), 'no coord', len(miss), miss[:30])
    rp = os.path.join(ROOT, 'data', 'r', 'index.json'); R = json.load(open(rp, encoding='utf-8')); gb = {}
    for g, v in out.items():
        pth = os.path.join(ROOT, 'data', 'r', g, 'transit.json')
        if not os.path.isdir(os.path.dirname(pth)): continue
        T = json.load(open(pth, encoding='utf-8')) if os.path.exists(pth) else {'schema': 'tg-transit/1', 'gu': g, 'ym': YM, 'source': {}, 'fields': {'bus': '[정류장ID, 이름, 경도, 위도, 승차 24, 하차 24]', 'sub': '[역, 노선, 경도, 위도, 승차 24, 하차 24]'}, 'bus': []}
        T['sub'] = v; T['source']['sub'] = '서울시 지하철 호선별 역별 시간대별 승하차 인원(CardSubwayTime · 2026년 6월 · 수도권 전 노선) — 역 이름으로 합친 하루 평균 · 자리: 서울시 역사마스터(같은 이름이면 노선 자리의 가운데) · 없으면 OpenStreetMap 같은 이름 역(ODbL)'
        T['source'].setdefault('bus', '경기 버스 정류장 시간대 승하차는 아직 없음(경기데이터드림에 하루치 집계만 있다)')
        json.dump(T, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[g] = os.path.getsize(pth)
    for g2 in R['gus']:
        if g2['gu'] in gb: g2.setdefault('bytes', {})['transit'] = gb[g2['gu']]
    json.dump(R, open(rp, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('gus', len(gb))

if __name__ == '__main__': main()
