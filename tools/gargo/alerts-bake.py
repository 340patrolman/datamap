# -*- coding: utf-8 -*-
# 네비 가르고 — 길 위 알림 묶음(소유자 2026-10-14 「가르고 네비 더 고도화 · 일상적으로 틀어 놓고 쓸 만큼」)
#   티맵·카카오맵이 늘 해 주는 「앞에 단속 카메라 · 어린이보호구역」을 가르고도 하려면 자리 묶음이 한 장 있어야 한다 → data/gargo-alerts-seoul.json
#   cam = 무인교통단속카메라(전국무인교통단속카메라표준데이터 · 서울 25구 · data/r/<구>/safety.json 의 cam 을 그대로 모음)
#   sz  = 어린이보호구역 대상 시설(전국어린이보호구역표준데이터 · data/child-zone/11.json) — **구역 경계선이 아니라 학교·유치원 등 시설의 점**이다
#   통신 없음(받아 둔 원자료·구운 파일만 읽는다) · 다시 구울 때: safety-bake(카메라 원자료)·childzone-bake 를 다시 돌린 뒤 이 도구
#   py -3.12 -X utf8 tools/gargo/alerts-bake.py
import json, os, glob, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    # 원자료(관리기관 칸이 있다) — 07_API키/out/region/safe_cam.json(tools/region/safety-bake.py 가 받아 둔 서울 표준데이터 4,313행)
    raw = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region', 'safe_cam.json'), encoding='utf-8'))
    cams, gus = [], len(set(r.get('signguNm') for r in raw))
    for r in raw:
        try:
            lim = int(r.get('lmttVe') or 0)
            org = 'p' if '경찰' in (r.get('institutionNm') or '') else 'g'
            cams.append([round(float(r['longitude']), 6), round(float(r['latitude']), 6), lim or None, (str(r.get('regltSe') or '').lstrip('0') or ''), (str(r.get('prtcareaType') or '').lstrip('0') or ''),
                         r.get('roadRouteNm') or '', r.get('itlpc') or '', org, (str(r.get('roadRouteDrc') or '').lstrip('0') or '')])
        except Exception:
            pass
    seen, uc = set(), []
    for c in cams:                                             # 같은 자리(약 1m)·같은 제한속도는 한 대로
        k = (round(c[0], 5), round(c[1], 5), c[2], c[3])
        if k not in seen:
            seen.add(k); uc.append(c)
    cz = json.load(open(os.path.join(ROOT, 'data', 'child-zone', '11.json'), encoding='utf-8'))
    sz = [[x[0], x[1], x[2], x[3]] for x in cz['items']]
    doc = {'schema': 'tg-gargo-alerts/1', 'made': datetime.date.today().isoformat(),
           'source': {'cam': '전국무인교통단속카메라표준데이터(공공데이터포털 15028200 · 오픈API tn_pubr_public_unmanned_traffic_camera_api · 서울 · safety-bake 가 받아 둔 07_API키/out/region/safe_cam.json)', 'sz': cz.get('source')},
           'fields': {'cam': '[[경도, 위도, 제한속도 km/h|null, 단속구분 코드(se · 앞 0 뗌), 보호구역 코드(zone · 앞 0 뗌), 도로 이름, 설치 자리 글, 관리기관 p 경찰 · g 구청, 도로노선방향 코드(1·2·3 · 원자료 그대로)]]',
                      'sz': '[[경도, 위도, 시설 종류, 시설 이름]] — 어린이보호구역 **대상 시설의 점**(구역 경계 아님)'},
           'note': ['단속구분(se) 코드표는 공식 문서로 확인하지 못했다(2026-10-14 · 공공데이터포털 표준 페이지에 값 정의 없음) — 대신 관리기관으로 가른다: 공공데이터포털 설명 「경찰청 소관 = 속도·신호·통행위반·기타 · 지방자치단체 소관 = 버스전용차로·불법주정차·기타」 · 서울 실측 se 1·2·99 = 모두 서울특별시경찰청(제한속도 있음) · se 4 = 모두 구청(대부분 제한속도 없음 = 주정차 등으로 봄)',
                    '알림 권고: 관리기관 p(경찰) 이고 제한속도가 있는 카메라만 「단속 카메라 · 제한 N」 — 구청(g) 것은 주정차·버스전용 단속일 수 있어 알리지 않거나 따로',
                    '카메라 방향(어느 쪽으로 가는 차를 찍나)은 자료에 없다 — 길 위 거리만으로 알리면 반대 방향 카메라도 알릴 수 있다',
                    '어린이보호구역은 시설 점이라 「반경 안 = 보호구역 안」이 아니다 — 「어린이보호구역 시설 가까움」으로 알린다'],
           'n': {'cam': len(uc), 'sz': len(sz), 'gu': gus}, 'cam': uc, 'sz': sz}
    p = os.path.join(ROOT, 'data', 'gargo-alerts-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('카메라', len(uc), '(원자료', len(cams), ') · 보호구역 시설', len(sz), '· 구', gus, '·', os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
