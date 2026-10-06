# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.16.0 — 🏨 외국인 단기체류 숙박(서울 · 지방행정인허가 — 서울 열린데이터광장 LOCALDATA_031104 외국인관광 도시민박업 · LOCALDATA_031101 관광숙박업(호텔·호스텔 등))
#   영업 중(TRDSTATEGBN 01)만 · 좌표 X·Y = 중부원점 TM(Bessel · EPSG:5174 — 서울시 데이터셋 설명) → WGS84 · 점이 든 행정동(SGIS 2026-07)에 붙임
#   ⚠ 전국판(LOCALDATA localdata.go.kr)은 이 작업 환경에서 접속이 막혀 서울만 · 전국은 공공데이터포털 「행정안전부_지방행정인허가」 API 활용신청 또는 소유자가 LOCALDATA 에서 내려받기
#   py -3.12 -X utf8 tools/region/lodge-bake.py → data/lodging-seoul.json
import json, os, time, urllib.request, collections
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
SVC = {'LOCALDATA_031104': '외국인관광 도시민박업', 'LOCALDATA_031101': '관광숙박업'}

def rows(svc):
    sk = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['seoul'].strip(); out = []; st = 1
    while True:
        for i in range(4):
            try: j = json.loads(urllib.request.urlopen('http://openapi.seoul.go.kr:8088/%s/json/%s/%d/%d/' % (sk, svc, st, st + 999), timeout=60).read().decode()); break
            except Exception: time.sleep(3); j = {}
        v = j.get(svc) or {}; rr = v.get('row') or []; out += rr; tot = v.get('list_total_count') or 0; st += 1000
        if st > tot or not rr: break
    return out

def main():
    tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True)
    g = json.load(open(HJD, encoding='utf-8')); F = [(shape(f['geometry']), f['properties']['adm_cd2'][:8]) for f in g['features'] if f['properties']['adm_cd2'][:2] == '11']; T = STRtree([x[0] for x in F])
    def dong_of(la, lo):
        p = Point(lo, la)
        for i in T.query(p):
            if F[i][0].contains(p): return F[i][1]
    pts = []; cnt = collections.defaultdict(collections.Counter); nopos = 0
    for svc, kind in SVC.items():
        for r in rows(svc):
            if (r.get('TRDSTATEGBN') or '').strip() != '01': continue
            try: x, y = float(r['X']), float(r['Y'])
            except (TypeError, ValueError, KeyError): nopos += 1; continue
            lo, la = tr.transform(x, y)
            if not (37.4 < la < 37.72 and 126.7 < lo < 127.2): nopos += 1; continue
            sub = (r.get('TRSTLODGCLNM') or '').strip() if kind == '관광숙박업' else '도시민박'
            k8 = dong_of(la, lo); pts.append([round(la, 6), round(lo, 6), (r.get('BPLCNM') or '').strip(), kind, sub, (r.get('RDNWHLADDR') or r.get('SITEWHLADDR') or '').strip(), (r.get('APVPERMYMD') or '').strip(), k8])
            if k8: cnt[k8][sub] += 1
    json.dump({'schema': 'tg-lodging/1', 'source': '서울 열린데이터광장 지방행정인허가 — 외국인관광 도시민박업(LOCALDATA_031104) · 관광숙박업(LOCALDATA_031101) · 영업 중만 · ' + time.strftime('%Y-%m-%d') + ' 받음',
               'fields': 'pts = [위도, 경도, 이름, 업종, 세부(도시민박·호텔업·호스텔업 등), 주소, 인허가일, 행정동 8자리] · dong = {행정동: {세부: 수}}',
               'note': '외국인관광 도시민박업 = 외국인 관광객에게 집을 내주는 민박(관광진흥법) — 단기체류 외국인이 묵는 자리 · 실제 투숙 인원은 공개되지 않는다 · 서울만(전국판은 활용신청 대기)', 'pts': pts, 'dong': cnt},
              open(os.path.join(ROOT, 'data', 'lodging-seoul.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    c = collections.Counter(p[4] for p in pts)
    print('숙박', len(pts), c.most_common(8), '자리 없음', nopos, '동', len(cnt))

if __name__ == '__main__': main()
