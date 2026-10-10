# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.104.0 — 서울시 실시간 층이 기대는 고정 표 → data/seoul-live.json
#   ① 실시간 주차 정보(GetParkingInfo)에는 좌표가 없다 → 주차장 안내 정보(GetParkInfo · LAT·LOT)에서 주차장 코드별 자리
#   ② 돌발 유형 코드 이름(AccMainCode · AccSubCode)
#   출처: 서울 열린데이터광장(서울특별시 · 서울시설공단 · 서울시 교통정보센터 TOPIS) · 키 = ../07_API키/keys.json "seoul"(출력·커밋 금지)
#   py -3.12 -X utf8 tools/region/seoul-live-bake.py
import json, os, urllib.request, datetime
import xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS = os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json')
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'seoul_live')
OUT = os.path.join(ROOT, 'data', 'seoul-live.json')


def key():
    k = json.load(open(KEYS, encoding='utf-8-sig'))['seoul']
    return k['key'] if isinstance(k, dict) else k


def get(path, fmt='json'):
    u = 'http://openapi.seoul.go.kr:8088/%s/%s/%s' % (key(), fmt, path)
    return urllib.request.urlopen(u, timeout=90).read().decode('utf-8', 'ignore')


def main():
    os.makedirs(RAW, exist_ok=True)
    P, a = [], 1
    while True:
        j = json.loads(get('GetParkInfo/%d/%d' % (a, a + 999)))['GetParkInfo']
        P += j['row']; tot = j['list_total_count']
        if a + 999 >= tot: break
        a += 1000
    json.dump(P, open(os.path.join(RAW, 'GetParkInfo_all.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    RT = json.loads(get('GetParkingInfo/1/1000'))['GetParkingInfo']['row']
    byc = {}
    for p in P:
        try: la, lo = float(p.get('LAT') or 0), float(p.get('LOT') or 0)
        except ValueError: continue
        if 37.3 < la < 37.8 and 126.6 < lo < 127.3: byc[str(p['PKLT_CD'])] = [round(la, 6), round(lo, 6)]
    park, miss = {}, []
    for r in RT:
        c = str(r['PKLT_CD'])
        if c in byc: park[c] = byc[c]
        else: miss.append(r['PKLT_NM'])
    main_, sub = {}, {}
    for row in ET.fromstring(get('AccMainCode/1/100', 'xml')).findall('row'): main_[row.find('acc_type').text] = row.find('acc_type_nm').text
    for row in ET.fromstring(get('AccSubCode/1/300', 'xml')).findall('row'): sub[row.find('acc_dtype').text] = row.find('acc_dtype_nm').text
    json.dump({'schema': 'tg-seoul-live/1', 'at': datetime.date.today().isoformat(),
               'source': '서울 열린데이터광장 — 서울시 공영주차장 안내 정보(GetParkInfo · 주차장 자리) · 서울시 실시간 돌발 유형 코드(AccMainCode · AccSubCode)',
               'note': '실시간 주차 정보를 주는 %d곳 중 자리를 아는 %d곳 · 자리 없는 곳은 지도에 못 놓는다: %s' % (len(RT), len(park), ' · '.join(miss)),
               'fields': 'park{주차장 코드(PKLT_CD): [위도, 경도]}(실시간 주차 정보가 오는 주차장만) · acc{main{돌발 유형 코드: 이름}, sub{세부 코드: 이름}}', 'made': datetime.date.today().isoformat(),
               'park': park, 'acc': {'main': main_, 'sub': sub}}, open(OUT, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('주차장 안내', len(P), '실시간', len(RT), '자리 있음', len(park), '없음', miss, os.path.getsize(OUT), 'B')


if __name__ == '__main__': main()
