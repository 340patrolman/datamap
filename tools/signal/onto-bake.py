# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧩 온톨로지: 교차로 객체의 ID 매핑표(소유자 2026-10-11 「온톨로지를 팔란티어식으로 구현 · 너의 권고대로 모두 진행하자」 · ONTOLOGY.md Phase 1) → data/onto-int.json
#   교차로(Intersection) 객체의 기본 ID = `INT-<T-GIS 교차로코드>`(서울 8,097곳 · 코드 겹침 없음 · 장비 없는 교차로까지 있는 가장 넓은 목록)
#   한 줄에: 다른 번호 체계(서울 C-ITS = T-Data = 경찰청 계획이 같은 번호)와의 맞댐 · 관할 경찰서 · 구 · 행정동 · 250m 격자 번호(넓이 자료와 잇는 열쇠) · 연동 부모 · **지금 어떤 속성이 채워져 있는지**
#   재료(모두 이미 구운 파일): data/tgis-seoul.json · data/fac-signal.json · data/sigdir-seoul.json · data/signal-tod-seoul.json · data/sig-ksc-seocho.json · 행정동 경계 13_관할경계/원자료/hjd20260701.geojson(통계청 SGIS · 가공 vuski/admdongkor 2026-07)
#   py -3.12 -X utf8 tools/signal/onto-bake.py
import json, os, sys, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'region'))
def main():
    from shapely.geometry import shape, Point
    from shapely.strtree import STRtree
    import grid250 as GR
    T = json.load(open(os.path.join(ROOT, 'data', 'tgis-seoul.json'), encoding='utf-8'))['items']
    F = json.load(open(os.path.join(ROOT, 'data', 'fac-signal.json'), encoding='utf-8'))['spots']
    sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); its = sd['its']; pl = sd['pl']
    tod = {str(x['no']) for x in json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']}
    ksc = {str(x['no']) for x in json.load(open(os.path.join(ROOT, 'data', 'sig-ksc-seocho.json'), encoding='utf-8'))['items']}
    H = [f for f in json.load(open(os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features'] if f['properties']['sido'] == '11']; HG = [shape(f['geometry']) for f in H]; HT = STRtree(HG)
    def dong(lon, lat):
        p = Point(lon, lat)
        for i in HT.query(p):
            if HG[i].contains(p): pr = H[i]['properties']; return pr['adm_cd2'], pr['adm_nm'].split()[-1], pr['sgg']
        return '', '', ''
    items = []; st = collections.Counter()
    for c, nm, la, lo, par, pe, cits, gu in T:
        dc, dn, sgg = dong(lo, la); no = str(cits) if cits else ''; f = F.get(no) if no else None
        has = (1 if (no and its.get(no)) else 0) | (2 if no in tod else 0) | (4 if no in ksc else 0) | (8 if (f and f.get('in')) else 0) | (16 if cits else 0)
        items.append([c, nm, la, lo, cits, pe, sgg, dc, dn, GR.code_ll(la, lo), par, has, len(set((q[0], q[1]) for q in pl.get(no, []))) if no else 0])
        st['모두'] += 1; st['실시간 장비 번호 있음'] += 1 if cits else 0; st['방향별 초 있음'] += 1 if has & 1 else 0; st['경찰청 계획 있음'] += 1 if has & 2 else 0; st['교통과 출력물 있음'] += 1 if has & 4 else 0; st['방향별 차로 읽음'] += 1 if has & 8 else 0; st['연동 부모 있음'] += 1 if par else 0; st['행정동 못 찾음'] += 0 if dc else 1
    doc = {'schema': 'tg-onto-int/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'object': '교차로(Intersection) — ONTOLOGY.md 의 Object 1',
           'id': 'INT-<T-GIS 교차로코드>(예: INT-548 = 서울성모병원 · C-ITS 4034)',
           'source': '서울시 T-GIS 교통안전시설물 교차로(A008_P · data/tgis-seoul.json) · C-ITS 번호 = 교통안전 신호등 실시간 정보의 교차로 지도정보(공공데이터포털 15157604) · 행정동 = 통계청 SGIS 행정동 경계(가공 vuski/admdongkor 2026-07 · 공공누리 1유형·CC BY 4.0) · 격자 = 국가지점번호식 250m(EPSG:5179 — tools/region/grid250.py)',
           'note': ['번호 체계가 둘이다: ① T-GIS 교차로코드(서울 모든 신호 교차로 · 이 표의 기본 ID) ② 서울 C-ITS 번호 = T-Data 번호 = 경찰청 계획 번호(같은 체계 · 실시간 장비·공개 계획이 있는 곳만). 둘은 좌표 15m 안에서 맞댔다 — 1대1 이 아니다(C-ITS 번호가 없는 T-GIS 교차로가 훨씬 많다)',
                    'has 는 「지금 그 속성이 채워져 있나」의 비트다 — 온톨로지의 빈 칸이 어디인지 보는 데 쓴다. 채워진 값 자체는 data/fac-signal.json(방향별)·data/sigdir-seoul.json(받은 초)·data/signal-tod-seoul.json(계획)에 있다',
                    '격자 번호는 넓이 자료(사고 250m·생활인구·상가 — data/r/<구>/…250.json)와 잇는 열쇠다 · 길을 따라가는 관계(다음 교차로까지 몇 초·연동)는 격자가 아니라 교차로 ID·ITS 링크 ID 로 잇는다(data/nav-*.json · data/sig-net-seocho.json)',
                    '연동 부모는 T-GIS 연동교차로코드(그 신호가 딸려 도는 부모 교차로)다 — 간선 연동(그린웨이브) 묶음이 아니다',
                    '관할 경찰서 코드는 원자료 값(340 서초 · 380 방배 …) — 반포동처럼 현장 기준이 다른 곳은 data/police-card.json 의 FIELD 를 따른다'],
           'fields': 'items[[T-GIS 교차로코드, 이름, 위도, 경도, C-ITS 번호(0 = 없음), 관할 경찰서 코드, 구 코드, 행정동 코드, 행정동 이름, 250m 격자 번호, 연동 부모 T-GIS 코드(0 = 없음), has 비트(1 방향별 초 · 2 경찰청 계획 · 4 교통과 출력물 · 8 방향별 차로 · 16 C-ITS 번호), 요일×시각 96칸 가운데 채운 칸]]',
           'stat': dict(st), 'items': items}
    p = os.path.join(ROOT, 'data', 'onto-int.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(items), dict(st), '· 바이트', os.path.getsize(p)); print(items[0]); print([x for x in items if x[0] == 548])
    pe = collections.Counter(x[5] for x in items); print('관할서 340·380:', pe.get(340), pe.get(380))
if __name__ == '__main__': main()
