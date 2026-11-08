# -*- coding: utf-8 -*-
# 서초 공공데이터 묶음(data/pubdata-seocho.json) 의 「seoul」 칸만 다시 받는다(2026-11-08 · 지도 세션)
#   옛 굽는 도구 tools/map2d-build/build_pub.pl 은 그때 임시 폴더 원자료를 읽어 다시 못 돌린다 → 그 도구의 81~91줄(서울 열린데이터광장 OpenAPI 갈래)만 같은 칸·같은 거름으로 옮김
#   공영주차장(GetParkInfo) · 무더위쉼터(TbGtnHwcwP) · 한파쉼터(TbGtnCwP) · 따릉이 대여소(tbCycleStationInfo) · 병의원(TbHospitalInfo) · 약국 운영시간(TbPharmacyOperateInfo) — 서초구만
#   다른 칸(생활인구·음주다발·위험지역·지하철·버스·시설·신호)은 건드리지 않는다 · 받은 수가 종전의 절반 아래면 그 갈래는 바꾸지 않는다(API 가 덜 준 날 막기)
#   키 = ../07_API키/keys.json "seoul"(출력·커밋 금지) · 서울시 API 는 http 만
#   py -3.12 -X utf8 tools/region/pub-seoul-refresh.py
import json, os, sys, time, datetime, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS = os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json')
OUT = os.path.join(ROOT, 'data', 'pubdata-seocho.json')


def key():
    k = json.load(open(KEYS, encoding='utf-8'))['seoul']
    return k['key'] if isinstance(k, dict) else k


def get(path):
    u = 'http://openapi.seoul.go.kr:8088/%s/json/%s' % (key(), path)
    for t in range(3):
        try:
            return json.loads(urllib.request.urlopen(u, timeout=60).read().decode('utf-8'))
        except Exception as e:   # 키가 든 주소는 찍지 않는다
            last = type(e).__name__
            time.sleep(2 + t * 3)
    raise SystemExit('받기 실패 ' + path.split('/')[0] + ' ' + last)


def pages(svc):
    out, a = [], 1
    while True:
        j = get('%s/%d/%d/' % (svc, a, a + 999)); b = j.get(svc) or next((v for v in j.values() if isinstance(v, dict) and 'row' in v), {})   # 따릉이는 서비스 이름과 다른 열쇠(stationInfo)로 준다 — 옛 build_pub.pl 처럼 한 덩어리를 읽음
        rows = b.get('row') or []
        if not rows:
            code = (b.get('RESULT') or j.get('RESULT') or {}).get('CODE', '')
            if a == 1 and code and code != 'INFO-000': raise SystemExit('%s %s' % (svc, code))
            break
        out += rows; total = int(b.get('list_total_count') or 0)
        if a + 999 >= total: break
        a += 1000
    return out


def r6(v):
    try: return round(float(v), 6)
    except Exception: return None


def num(v):
    try: return int(float(v or 0))
    except Exception: return 0


def hrs(x): return ' '.join(('%s-%s' % (x.get('DUTYTIME%dS' % i), x.get('DUTYTIME%dC' % i))) if x.get('DUTYTIME%dS' % i) and x.get('DUTYTIME%dC' % i) else '-' for i in range(1, 9))


def main():
    D = json.load(open(OUT, encoding='utf-8')); S = D['seoul']; new = {}
    park, seen = [], set()
    for x in pages('GetParkInfo'):
        if '서초구' not in (x.get('ADDR') or '') or not (r6(x.get('LAT')) or 0) > 30: continue
        o = dict(name=x.get('PKLT_NM'), addr=x.get('ADDR'), kind=x.get('PKLT_KND_NM'), oper=x.get('OPER_SE_NM'), tel=x.get('TELNO') or '', cap=num(x.get('TPKCT')), fee=x.get('CHGD_FREE_NM'), night=x.get('NGHT_FREE_OPN_YN_NAME'), lat=r6(x.get('LAT')), lon=r6(x.get('LOT')))
        k = (o['name'], o['lat'])
        if k in seen: continue
        seen.add(k); park.append(o)
    new['park'] = park
    new['heat'] = [dict(name=x.get('R_AREA_NM'), type=x.get('FACILITY_TYPE2') or x.get('FACILITY_TYPE1'), addr=x.get('R_DETL_ADD') or x.get('LOTNO_ADDR'), days=x.get('OPR_DAYS'), time=(x.get('OPR_START_TIME') or '') + '~' + (x.get('OPR_END_TIME') or ''), lat=r6(x.get('LAT')), lon=r6(x.get('LON')))
                   for x in pages('TbGtnHwcwP') if str(x.get('AREA_CD') or '').startswith('11650') and x.get('LAT')]
    new['bike'] = [dict(name=x.get('RENT_NM'), no=x.get('RENT_NO'), n=num(x.get('HOLD_NUM')), lat=r6(x.get('STA_LAT')), lon=r6(x.get('STA_LONG')))
                   for x in pages('tbCycleStationInfo') if (x.get('STA_LOC') or '') == '서초구' and x.get('STA_LAT')]
    hosp, hs = [], set()
    for x in pages('TbHospitalInfo'):
        if '서울특별시 서초구' not in (x.get('DUTYADDR') or '') or not x.get('WGS84LAT') or x.get('HPID') in hs: continue
        hs.add(x.get('HPID'))
        hosp.append(dict(name=x.get('DUTYNAME'), div=x.get('DUTYDIVNAM'), er=1 if str(x.get('DUTYERYN') or '') == '1' else 0, emcls=x.get('DUTYEMCLSNAME'), tel=x.get('DUTYTEL1') or '', ertel=x.get('DUTYTEL3') or '', addr=x.get('DUTYADDR'), h=hrs(x), lat=r6(x.get('WGS84LAT')), lon=r6(x.get('WGS84LON'))))
    new['hosp'] = hosp
    phar, ps = [], set()
    for x in pages('TbPharmacyOperateInfo'):
        if '서울특별시 서초구' not in (x.get('DUTYADDR') or '') or not x.get('WGS84LAT') or x.get('HPID') in ps: continue
        ps.add(x.get('HPID'))
        phar.append(dict(name=x.get('DUTYNAME'), tel=x.get('DUTYTEL1') or '', addr=x.get('DUTYADDR'), h=hrs(x), lat=r6(x.get('WGS84LAT')), lon=r6(x.get('WGS84LON'))))
    new['phar'] = phar
    new['cold'] = [dict(name=x.get('RESTAREA_NM'), type=x.get('FACILITY_TYPE2') or '', addr=x.get('ROAD_NM_ADDR') or x.get('LOTNO_ADDR'), cap=num(x.get('UTZTN_PSBLTY_NOPE')), note=(x.get('RMRK') or '')[:120], lat=r6(x.get('LAT')), lon=r6(x.get('LOT')))
                   for x in pages('TbGtnCwP') if '서초구' in ((x.get('LOTNO_ADDR') or '') + (x.get('ROAD_NM_ADDR') or '')) and x.get('LAT')]
    kept = []
    for k, v in new.items():
        old = len(S.get(k) or [])
        if old and len(v) < old / 2: kept.append('%s %d→%d(그대로)' % (k, old, len(v))); continue
        print(k, old, '→', len(v)); S[k] = v
    day = datetime.date.today().isoformat()
    S['source'] = S['source'].split('(수집 ')[0] + '(수집 ' + day + ' · tools/region/pub-seoul-refresh.py): ' + S['source'].split('): ', 1)[1]
    json.dump(D, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('그대로 둔 갈래:', kept or '없음', '·', os.path.getsize(OUT) // 1024, 'KB')


if __name__ == '__main__':
    main()
