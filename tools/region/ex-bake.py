# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.13.0 — 🛣 고속도로 영업소 시간대 교통량(ex-collect.py 가 모은 ic_*.json + 영업소 위치) → data/traffic-ex.json
#   영업소마다 시각(0~23)별 [입구, 출구] 대수 — 여러 날이면 같은 시각끼리 평균 · 하이패스 비율 · 화물·대형(4~6종) 비율 · 모은 시각 목록
#   출처 = 한국도로공사 고속도로 공공데이터 포털 OpenAPI(trafficIc · locationinfoUnit) · py -3.12 -X utf8 tools/region/ex-bake.py
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EX = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'ex')

def main():
    units = {u['unitCode'].strip(): u for u in json.load(open(os.path.join(EX, 'units.json'), encoding='utf-8'))}
    S = collections.defaultdict(lambda: {'h': collections.defaultdict(lambda: [0, 0]), 'n': collections.Counter(), 'hp': 0, 'big': 0, 'all': 0, 'nm': ''}); seen = []
    for f in sorted(glob.glob(os.path.join(EX, 'ic_*.json'))):
        j = json.load(open(f, encoding='utf-8')); h = int(j['sumTm']); seen.append(j['sumDate'] + ' ' + j['sumTm'] + '시'); got = set()
        for code, nm, io, tcs, car, v, exd in j['rows']:
            s = S[code]; s['nm'] = nm; s['h'][h][0 if io == '0' else 1] += v; s['all'] += v; got.add(code)
            if tcs == '2': s['hp'] += v
            if car in ('4', '5', '6'): s['big'] += v
        for code in got: S[code]['n'][h] += 1
    out = []; nopos = 0
    for code, s in S.items():
        u = units.get(code)
        if not u or not u.get('xValue'): nopos += 1; continue
        hrs = {}
        for h, (a, b) in s['h'].items(): n = s['n'][h] or 1; hrs[str(h)] = [round(a / n), round(b / n)]
        out.append({'code': code, 'name': s['nm'] or u['unitName'], 'route': u.get('routeName'), 'lat': round(float(u['yValue']), 6), 'lon': round(float(u['xValue']), 6), 'h': hrs,
                    'hp': round(s['hp'] / s['all'] * 100) if s['all'] else None, 'big': round(s['big'] / s['all'] * 100) if s['all'] else None})
    doc = {'schema': 'tg-traffic-ex/1', 'source': '한국도로공사 고속도로 공공데이터 포털 OpenAPI — 영업소별 교통량(trafficIc · 1시간) · 영업소 위치(locationinfoUnit)', 'hours': seen,
           'fields': 'units = [{code, name, route, lat, lon, h = {시: [입구, 출구] 대수(여러 날이면 같은 시각 평균)}, hp = 하이패스 비율 %, big = 4~6종(대형·화물) 비율 %}]',
           'note': '영업소(요금소)를 드나든 차 — 고속도로 본선 통행량이 아니다 · 이 API 는 지난 시각을 주지 않아 매시간 모은 만큼만 있다(모은 시각 = hours) · 민자 영업소 포함', 'units': out}
    p = os.path.join(ROOT, 'data', 'traffic-ex.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('영업소', len(out), '위치 없음', nopos, '모은 시각', len(seen), seen[:3], '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
