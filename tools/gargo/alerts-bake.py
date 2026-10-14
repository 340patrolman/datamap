# -*- coding: utf-8 -*-
# 네비 가르고 — 길 위 알림 묶음(소유자 2026-10-14 「가르고 네비 더 고도화 · 일상적으로 틀어 놓고 쓸 만큼」)
#   티맵·카카오맵이 늘 해 주는 「앞에 단속 카메라 · 어린이보호구역」을 가르고도 하려면 자리 묶음이 한 장 있어야 한다 → data/gargo-alerts-seoul.json
#   cam = 무인교통단속카메라(전국무인교통단속카메라표준데이터 · 서울 25구 · data/r/<구>/safety.json 의 cam 을 그대로 모음)
#   sz  = 어린이보호구역 대상 시설(전국어린이보호구역표준데이터 · data/child-zone/11.json) — **구역 경계선이 아니라 학교·유치원 등 시설의 점**이다
#   통신 없음(이미 구운 파일만 읽는다) · 다시 구울 때: safety.json·child-zone 을 다시 구운 뒤 이 도구
#   py -3.12 -X utf8 tools/gargo/alerts-bake.py
import json, os, glob, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    cams, gus = [], 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'safety.json'))):
        d = json.load(open(f, encoding='utf-8')); gus += 1
        for c in d.get('cam') or []:
            try:
                cams.append([round(float(c['lon']), 6), round(float(c['lat']), 6), int(c['lim']) if str(c.get('lim') or '').isdigit() else None, str(c.get('se') or ''), str(c.get('zone') or ''), c.get('road') or '', c.get('at') or ''])
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
           'source': {'cam': '전국무인교통단속카메라표준데이터(공공데이터포털 · 행정안전부 표준데이터 · 서울 각 구) — data/r/<구>/safety.json 의 cam', 'sz': cz.get('source')},
           'fields': {'cam': '[[경도, 위도, 제한속도 km/h|null, 단속구분 코드(se · 원자료 그대로), 보호구역 코드(zone · 원자료 그대로), 도로 이름, 설치 자리 글]]',
                      'sz': '[[경도, 위도, 시설 종류, 시설 이름]] — 어린이보호구역 **대상 시설의 점**(구역 경계 아님)'},
           'note': ['단속구분(se)·보호구역(zone) 코드의 뜻은 표준데이터 문서로 아직 확인하지 못했다 — 화면에는 코드로 뜻을 지어 붙이지 말고 「단속 카메라 · 제한 N」만 쓴다',
                    '카메라 방향(어느 쪽으로 가는 차를 찍나)은 자료에 없다 — 길 위 거리만으로 알리면 반대 방향 카메라도 알릴 수 있다',
                    '어린이보호구역은 시설 점이라 「반경 안 = 보호구역 안」이 아니다 — 「어린이보호구역 시설 가까움」으로 알린다'],
           'n': {'cam': len(uc), 'sz': len(sz), 'gu': gus}, 'cam': uc, 'sz': sz}
    p = os.path.join(ROOT, 'data', 'gargo-alerts-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('카메라', len(uc), '(원자료', len(cams), ') · 보호구역 시설', len(sz), '· 구', gus, '·', os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
