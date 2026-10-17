# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🐾 반려동물 산업(동물병원·약국·미용·위탁관리·판매·생산·전시·운송·장묘·수입) → data/pet-biz.json + data/pet-biz/<시도 2자리>.json
#   소유자 2026-10-17 「개·고양이 기르는 사람이 늘어나고 애견·애묘용품·동물병원·동물미용실 등의 산업이 생겨나서 이것도 지역 정보에 넣으면 좋을 것 같다」
#   원자료: 행정안전부 지방행정인허가(LOCALDATA) 전국 파일(동물 갈래 10가지) — file.localdata.go.kr/file/download/<이름>/info (Referer 필요 · 메모리 localdata-referer)
#     animal_hospitals 동물병원 · animal_pharmacies 동물약국 · pet_grooming 동물미용업 · animal_boarding 동물위탁관리업(공공데이터포털 15107029) · animal_sales 동물판매업
#     animal_breeding 동물생산업 · animal_exhibition 동물전시업 · animal_transport 동물운송업 · animal_cremation 동물장묘업(15045054) · animal_import 동물수입업 → 07_API키/out/pet/<이름>.csv(cp949)
#   지금 수 = 영업/정상(영업상태코드 01)만 · 해마다 = 인허가일자의 해(새로 연 곳) · 폐업일자의 해(닫은 곳) — 폐업·취소된 곳도 좌표가 남아 있으면 구에 셈
#   ⚠ 업종마다 등록·신고 제도가 생긴 해가 달라 그 앞의 해는 비거나 적다(산업이 없던 것이 아니다) · 동물약국은 사람 약국이 동물용 의약품 판매를 같이 신고한 곳이 많다
#   좌표(중부원점 TM EPSG:5174) → WGS84 → 그 점이 든 행정동(13_관할경계 hjd20260701 · 8자리) · **상호·주소·전화는 싣지 않는다**
#   py -3.12 -X utf8 tools/region/petbiz-bake.py
import csv, json, os, datetime, collections
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'pet')
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
KINDS = [['hosp', '동물병원', 'animal_hospitals'], ['pharm', '동물약국', 'animal_pharmacies'], ['groom', '동물미용', 'pet_grooming'], ['board', '위탁관리(호텔·유치원)', 'animal_boarding'],
         ['sales', '동물판매', 'animal_sales'], ['breed', '동물생산', 'animal_breeding'], ['exhib', '동물전시(카페 등)', 'animal_exhibition'], ['trans', '동물운송(펫택시 등)', 'animal_transport'],
         ['crem', '동물장묘', 'animal_cremation'], ['imp', '동물수입', 'animal_import']]
Y0 = 2005
S0 = 2015   # 「영업 중인 곳」 해마다(그해 끝 기준) 셈을 시작하는 해


def main():
    tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True); G = json.load(open(HJD, encoding='utf-8'))['features']; geoms, codes, names = [], [], {}
    for f in G:
        p = f['properties']; c = str(p.get('adm_cd2') or p.get('adm_cd8') or p.get('adm_cd') or '')[:8]
        geoms.append(shape(f['geometry'])); codes.append(c); names[c] = str(p.get('adm_nm') or '').split(' ')[-1]
    tree = STRtree(geoms); NK = len(KINDS); Z = lambda: [0] * NK
    yrs = list(range(Y0, datetime.date.today().year + 1))
    syrs = list(range(S0, yrs[-1] + 1)); ZS = lambda: [[0] * NK for _ in syrs]
    gu = collections.defaultdict(lambda: {'n': Z(), 's': ZS()}); dong = collections.defaultdict(Z); sdb = {}
    kr = {'n': Z(), 'o': collections.defaultdict(Z), 'c': collections.defaultdict(Z), 's': ZS()}; pts = collections.defaultdict(list); stat = collections.Counter(); made_at = ''
    for ki, (key, nm, fn) in enumerate(KINDS):
        with open(os.path.join(KB, fn + '.csv'), encoding='cp949', errors='replace', newline='') as fh:
            for r in csv.DictReader(fh):
                st = (r.get('영업상태코드') or '').strip(); act = st == '01'; oy = (r.get('인허가일자') or '')[:4]; cy = (r.get('폐업일자') or '')[:4]
                made_at = max(made_at, (r.get('데이터갱신시점') or '')[:10])
                if act: kr['n'][ki] += 1
                alive = (lambda yy: oy.isdigit() and int(oy) <= yy and (act or (cy.isdigit() and int(cy) > yy))) if (act or cy.isdigit()) else (lambda yy: False)
                for si, yy in enumerate(syrs):
                    if alive(yy): kr['s'][si][ki] += 1
                if oy.isdigit() and int(oy) >= Y0: kr['o'][int(oy)][ki] += 1
                if cy.isdigit() and int(cy) >= Y0 and not act: kr['c'][int(cy)][ki] += 1
                try: x = float(r['좌표정보(X)']); y = float(r['좌표정보(Y)'])
                except Exception: stat['noxy_act' if act else 'noxy'] += 1; continue
                lo, la = tr.transform(x, y)
                if not (33.0 < la < 38.7 and 124.5 < lo < 132.0): stat['noxy_act' if act else 'noxy'] += 1; continue
                pt = Point(lo, la); d = None
                for i in tree.query(pt):
                    if geoms[i].contains(pt): d = codes[i]; break
                if not d: stat['nodong'] += 1; continue
                g = gu[d[:5]]
                for si, yy in enumerate(syrs):
                    if alive(yy): g['s'][si][ki] += 1
                if act:
                    g['n'][ki] += 1; dong[d][ki] += 1; pts[d[:2]].append([round(lo, 5), round(la, 5), ki, int(oy) if oy.isdigit() else 0]); b = sdb.setdefault(d[:2], [lo, la, lo, la]); b[0] = min(b[0], lo); b[1] = min(b[1], la); b[2] = max(b[2], lo); b[3] = max(b[3], la)
    ser = lambda D: {str(y): D[y] for y in yrs if any(D.get(y, [0]))}
    out = {'schema': 'tg-pet-biz/1', 'made': datetime.date.today().isoformat(), 'stdr': made_at,
           'source': '행정안전부 지방행정인허가(LOCALDATA) 전국 파일 — 동물병원·동물약국·동물미용업·동물위탁관리업·동물판매업·동물생산업·동물전시업·동물운송업·동물장묘업·동물수입업(공공데이터포털 · 이용허락 제한 없음)',
           'fields': 'kinds[[키, 이름]] · syears[처음, 끝] · kr{n 지금 영업 중(갈래 차례), s[해마다 그해 끝 영업 중 · 갈래 차례], o{해: 그해 새로 연 곳}, c{해: 그해 닫은 곳(지금 영업 중이 아닌 곳의 폐업일자)}} · gu{시군구 5자리: {n, s}} · sdb{시도: [서, 남, 동, 북]} · dong{행정동 8자리: 지금 영업 중 갈래별} · 점 = data/pet-biz/<시도 2자리>.json items[[경도, 위도, 갈래 번호, 연 해]]',
           'note': ['지금 수 = 인허가 「영업/정상」만 · 상호·주소·전화는 싣지 않는다',
                    '업종마다 등록·신고 제도가 생긴 해가 달라 그 앞의 해는 비거나 적다 — 산업이 없던 것이 아니다',
                    '동물약국은 사람 약국이 동물용 의약품 판매를 같이 신고한 곳이 많다(동물 전문 약국 수가 아니다)',
                    '닫은 곳 = 지금 영업 중이 아닌 곳의 폐업일자 해 — 취소·말소는 폐업일자가 없으면 안 셈',
                    '자리 = 인허가 좌표가 든 행정동(2026-07 경계) · 좌표 없는 곳은 전국 합에만',
                    '해마다 영업 중 = 그해 끝에 열려 있던 곳(연 해 ≤ 그해 · 지금 영업 중이거나 닫은 해가 더 뒤) — 닫은 해를 모르는 취소·말소는 뺀다',
                    '동물미용·위탁관리·전시·운송은 이 파일에 2018년부터 한꺼번에 올라와 있다(그 앞 해는 거의 비어 있다) · 동물생산업은 2018 허가제 뒤 2022년에 대량 취소·말소가 있어 흐름 합에서 뺀다'],
           'n': {'gu': len(gu), 'dong': len(dong), 'pts': sum(len(v) for v in pts.values()), **stat},
           'kinds': [[k, nm] for k, nm, _ in KINDS], 'years': [yrs[0], yrs[-1]], 'syears': [syrs[0], syrs[-1]], 'sdb': {k: [round(x, 4) for x in v] for k, v in sorted(sdb.items())},
           'kr': {'n': kr['n'], 's': kr['s'], 'o': ser(kr['o']), 'c': ser(kr['c'])},
           'gu': {k: {'n': v['n'], 's': v['s']} for k, v in sorted(gu.items())},
           'dong': {k: v for k, v in sorted(dong.items())}}
    os.makedirs(os.path.join(ROOT, 'data', 'pet-biz'), exist_ok=True)
    json.dump(out, open(os.path.join(ROOT, 'data', 'pet-biz.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    for sd, L in sorted(pts.items()):
        L.sort(key=lambda q: (q[2], q[0]))
        json.dump({'schema': 'tg-pet-biz-pts/1', 'made': out['made'], 'source': out['source'], 'fields': 'items[[경도, 위도, 갈래 번호(pet-biz.json kinds 차례), 인허가 해]] · 지금 영업 중만 · 상호·주소 없음', 'items': L},
                  open(os.path.join(ROOT, 'data', 'pet-biz', sd + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('전국 지금', dict(zip([k for k, _, _ in KINDS], kr['n'])), '· 구', len(gu), '· 동', len(dong), '· 점', out['n']['pts'], '· 기준', made_at, '·', dict(stat))
    print('해마다 영업 중(생산업 뺌)', {syrs[i]: sum(v) - v[5] for i, v in enumerate(kr['s'])})
    print('해마다 새로 연 곳(전 갈래 합)', {y: sum(v) for y, v in out['kr']['o'].items()})
    print('해마다 닫은 곳(전 갈래 합)', {y: sum(v) for y, v in out['kr']['c'].items()})


if __name__ == '__main__':
    main()
