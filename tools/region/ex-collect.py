# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.13.0 — 🛣 고속도로 영업소별 1시간 교통량 모으기(한국도로공사 고속도로 공공데이터 포털 OpenAPI trafficIc · 영업소 위치 locationinfoUnit)
#   trafficIc 는 지난 날짜·시각을 받지 않고 「가장 최근 한 시간」만 준다 → 매시간 한 번씩 받아 쌓는다(기본 26시간 뒤 스스로 끝남)
#   키 = 07_API키/keys.json "ex_co_kr"(결과·로그에 키 없음) · 저장 = 07_API키/out/ex/ic_<날짜>_<시>.json
#   py -3.12 -X utf8 tools/region/ex-collect.py [시간 수=26]   ·  멈추려면 작업 관리자에서 이 python 을 끝내거나 07_API키/out/ex/STOP 파일을 만든다
import json, os, sys, time, urllib.request, urllib.parse
KB = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '07_API키')
OUT = os.path.join(KB, 'out', 'ex'); os.makedirs(OUT, exist_ok=True)
K = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['ex_co_kr'].strip()

def g(path, **q):
    q.update(key=K, type='json')
    for i in range(4):
        try: return json.loads(urllib.request.urlopen(urllib.request.Request('https://data.ex.co.kr/openapi/%s?%s' % (path, urllib.parse.urlencode(q)), headers={'User-Agent': 'Mozilla/5.0'}), timeout=90).read().decode('utf-8', 'replace'))
        except Exception: time.sleep(10 + i * 20)
    return None

def log(*a):
    open(os.path.join(OUT, 'collect.log'), 'a', encoding='utf-8').write(time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(str(x) for x in a) + '\n')

def once():
    rows = []; pg = 1
    while True:
        j = g('trafficapi/trafficIc', tmType='1', numOfRows='1000', pageNo=str(pg))
        if not j or not j.get('trafficIc'): break
        rows += j['trafficIc']; tot = int(j.get('count') or 0)
        if len(rows) >= tot: break
        pg += 1
    if not rows: log('빈 응답'); return
    d, t = rows[0]['sumDate'], rows[0]['sumTm']; fn = os.path.join(OUT, 'ic_%s_%s.json' % (d, t))
    keep = [[r['unitCode'].strip(), r['unitName'], r['inoutType'], r['tcsType'], r['carType'], int(r['trafficAmout'] or 0), r['exDivCode']] for r in rows]
    json.dump({'sumDate': d, 'sumTm': t, 'fields': '[영업소 코드, 이름, 0 입구·1 출구, 1 TCS·2 하이패스, 차종 1~8, 대수, 00 도공·그 밖 민자]', 'rows': keep}, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    log('받음', d, t, len(keep))

def main():
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 26
    if not os.path.exists(os.path.join(OUT, 'units.json')):
        j = g('locationinfo/locationinfoUnit', numOfRows='1000')
        if j: json.dump(j.get('list') or [], open(os.path.join(OUT, 'units.json'), 'w', encoding='utf-8'), ensure_ascii=False); log('영업소 위치', len(j.get('list') or []))
    end = time.time() + hours * 3600
    while time.time() < end and not os.path.exists(os.path.join(OUT, 'STOP')):
        once()
        now = time.localtime(); wait = (3600 - now.tm_min * 60 - now.tm_sec) + 20 * 60   # 다음 시 20분(집계가 늦게 올라온다)
        time.sleep(min(wait, 4200))
    log('끝')

if __name__ == '__main__': main()
