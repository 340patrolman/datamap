# -*- coding: utf-8 -*-
# 📅 행사·집회 층의 「문화행사」 칸 다시 받기(2026-11-08 · 종전 events-seocho.json 의 events 는 09-28 에 손으로 모은 것)
#   원자료 = 서울특별시 문화행사 정보(서울 열린데이터광장 culturalEventInfo · OA-15486 · 공공누리 제1유형 · 출처표시)
#   거름 = 자치구 「서초구」 + 서초 쪽 한강공원(반포·잠원한강공원·세빛섬·예빛섬·서래섬 — 이름이 장소에 들어 있으면) · 오늘(굽는 날) 이후 끝나는 행사만
#   칸 = 종전과 같은 꼴 {t 제목, c 갈래, s 시작, e 끝, p 자리, org, free, lat, lon, hour} — 지도(js/map2d.js evt)가 그대로 읽는다 · 문의 전화·출연자·요금 글은 안 담음
#   집회(rallies)는 손대지 않는다 — 지도는 이제 data/rally-seoul.json(rally-bake.py)을 먼저 쓴다
#   열쇠 = 07_API키/keys.json "seoul"(http 만 · 화면·저장소에 안 씀)
#   쓰기: py -3.12 -X utf8 tools/region/culture-bake.py
import json, os, urllib.request, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
F = os.path.join(ROOT, 'data', 'events-seocho.json')
PARKS = ('반포한강공원', '잠원한강공원', '세빛섬', '예빛섬', '서래섬', '반포 한강공원', '잠원 한강공원')


def main():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['seoul']
    rows, s = [], 1
    while True:
        u = 'http://openapi.seoul.go.kr:8088/%s/json/culturalEventInfo/%d/%d/' % (k, s, s + 999)
        v = json.loads(urllib.request.urlopen(u, timeout=120).read().decode('utf-8')).get('culturalEventInfo') or {}
        rows += v.get('row') or []
        if s + 999 >= (v.get('list_total_count') or 0): break
        s += 1000
    today = datetime.date.today().isoformat(); items = []
    for r in rows:
        place = r.get('PLACE') or ''
        if r.get('GUNAME') != '서초구' and not any(p in place for p in PARKS): continue
        e = (r.get('END_DATE') or '')[:10]
        if not e or e < today: continue
        try: la, lo = float(r.get('LAT')), float(r.get('LOT'))
        except (TypeError, ValueError): la = lo = None
        if la is not None and not (33 < la < 39 and 124 < lo < 132): la = lo = None   # 자리가 이상하면 점을 안 찍는다(지어내지 않음)
        it = {'t': r.get('TITLE'), 'c': r.get('CODENAME'), 's': (r.get('STRTDATE') or '')[:10], 'e': e, 'p': place, 'org': r.get('ORG_NAME'), 'free': r.get('IS_FREE')}
        if la is not None: it['lat'], it['lon'] = round(la, 6), round(lo, 6)
        if r.get('PRO_TIME'): it['hour'] = r['PRO_TIME']
        items.append(it)
    items.sort(key=lambda x: (x['s'], x['t'] or ''))
    D = json.load(open(F, encoding='utf-8'))
    D['collected'] = today
    D['events'] = {'source': '서울특별시 문화행사 정보(서울 열린데이터광장 culturalEventInfo · OA-15486)', 'license': '공공누리 제1유형(출처표시)',
                   'scope': '자치구 서초구 + 서초 쪽 한강공원(반포·잠원한강공원·세빛섬·예빛섬·서래섬) · %s 이후 끝나는 행사 · tools/region/culture-bake.py' % today, 'items': items}
    json.dump(D, open(F, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('문화행사 전체', len(rows), '· 서초 쪽', len(items), '· 자리 없음', sum(1 for x in items if 'lat' not in x), '→', F)


if __name__ == '__main__':
    main()
