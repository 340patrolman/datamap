# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏫 학교 둘레에서 보는 업소(교육환경보호구역에서 금지되는 행위·시설에 드는 갈래) → data/edu-zone-biz/<시도 코드>.json
#   소유자 2026-10-12 「학교 담당 경찰관이 공공데이터를 충분히 이용할 수 있게」 → 학교 반경 안에 이런 업소가 몇 곳 있는지 지도가 센다
#   근거(국가법령정보 원문 2026-10-12 확인 · 법률 MST 280023 · 시행 2026-06-03): 「교육환경 보호에 관한 법률」 제8조 제1항(학교경계등에서 직선거리 200m = 교육환경보호구역 ·
#     절대보호구역 = 학교출입문에서 50m · 상대보호구역 = 나머지) · 제9조 제19호(게임제공업·인터넷컴퓨터게임시설제공업·복합유통게임제공업 — 유치원·대학 구역 제외) · 제24호(노래연습장업 — 유치원·대학 제외) ·
#     제26호(단란주점영업·유흥주점영업) · 제27호(숙박업·관광숙박업 — 대통령령으로 정하는 것 제외). 제9조 단서: 상대보호구역에서는 제14~27호·제29~32호 가운데 지역위원회 심의를 거쳐 인정된 것은 제외
#   ⚠ 그래서 「반경 안에 있다 = 위반」이 아니다 — 심의로 허용된 곳, 학교보다 먼저 있던 곳이 섞여 있다. 그리고 법의 거리는 **학교 경계·출입문에서** 재는데 지도의 학교 자리는 점 하나다
#   원자료: 행정안전부 지방행정인허가(LOCALDATA) 전국 파일 — 공공데이터포털 15045018 유흥주점 · 15045017 단란주점 · 15045109 노래연습장 · 15045073 인터넷컴퓨터게임시설제공업 · 15045071 일반게임제공업 ·
#     15045069 청소년게임제공업 · 15045072 복합유통게임제공업 → 07_API키/out/eduzone/<이름>.csv · 15044968 숙박업 · 15044967 관광숙박업 → 07_API키/out/lodging/(stay-bake 가 받은 것)
#     받는 법 = data.go.kr selectLinkUrl.do?publicDataPk=<번호> → file.localdata.go.kr/file/download/<이름>/info (Referer 필요 · 메모리 localdata-referer)
#   영업/정상(영업상태코드 01)만 · 좌표(중부원점 TM EPSG:5174) → WGS84 · 좌표 없는 곳은 뺀다(수를 note 에) · **상호·주소·전화는 싣지 않는다**
#   py -3.12 -X utf8 tools/region/eduzone-bake.py
import csv, json, os, datetime, collections
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키', 'out'); HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
KINDS = [['유흥주점', '제26호', 'eduzone/entertainment_bars.csv'], ['단란주점', '제26호', 'eduzone/singing_bars.csv'], ['노래연습장', '제24호', 'eduzone/karaoke_rooms.csv'], ['인터넷컴퓨터게임시설(PC방)', '제19호', 'eduzone/pc_bangs.csv'],
         ['일반게임제공업', '제19호', 'eduzone/general_game_providers.csv'], ['청소년게임제공업', '제19호', 'eduzone/youth_game_providers.csv'], ['복합유통게임제공업', '제19호', 'eduzone/mixed_game_providers.csv'],
         ['숙박업(여관·모텔 등)', '제27호', 'lodging/lodgings.csv'], ['관광숙박업(호텔 등)', '제27호', 'lodging/tourist_accommodations.csv']]
SIDO = None   # 전국(2026-10-12 소유자 「기회될 때 전국으로」) — 시도는 주소 글자가 아니라 그 점이 든 행정동 경계의 시도 코드로 가른다(지도의 시도 코드 그대로 · 광주·전남 = 12)
def main():
    tr = Transformer.from_crs('EPSG:5174', 'EPSG:4326', always_xy=True); G = json.load(open(HJD, encoding='utf-8'))['features']; geoms = []; codes = []
    for f in G:
        p = f['properties']; c = str(p.get('adm_cd2') or p.get('adm_cd8') or p.get('adm_cd') or '')
        geoms.append(shape(f['geometry'])); codes.append(c[:8])
    tree = STRtree(geoms); OUT = collections.defaultdict(list); CNT = collections.defaultdict(collections.Counter); noxy = collections.Counter(); nodong = 0; ALLN = collections.Counter()
    for ki, (nm, ho, path) in enumerate(KINDS):
        with open(os.path.join(KB, path), encoding='cp949', errors='replace', newline='') as fh:
            for r in csv.DictReader(fh):
                if (r.get('영업상태코드') or '').strip() != '01': continue
                ALLN[ki] += 1
                try: x = float(r['좌표정보(X)']); y = float(r['좌표정보(Y)'])
                except Exception: noxy['all'] += 1; continue
                lo, la = tr.transform(x, y)
                if not (33.0 < la < 38.7 and 124.5 < lo < 132.0): noxy['all'] += 1; continue
                pt = Point(lo, la); d = None
                for i in tree.query(pt):
                    if geoms[i].contains(pt): d = codes[i]; break
                if not d: nodong += 1; continue
                sd = d[:2]
                OUT[sd].append([round(lo, 5), round(la, 5), ki, (d or '')[:5]]); CNT[sd][ki] += 1
    os.makedirs(os.path.join(ROOT, 'data', 'edu-zone-biz'), exist_ok=True); td = datetime.date.today().isoformat()
    for sd, items in sorted(OUT.items()):
        items.sort(key=lambda r: (r[3], r[2], r[0]))
        doc = {'schema': 'tg-edu-zone-biz/1', 'made': td, 'sido': sd,
               'source': '행정안전부 지방행정인허가(LOCALDATA) 전국 파일 — 유흥주점·단란주점·노래연습장·인터넷컴퓨터게임시설제공업·일반/청소년/복합유통 게임제공업·숙박업·관광숙박업(공공데이터포털 15045018·15045017·15045109·15045073·15045071·15045069·15045072·15044968·15044967 · 이용허락범위 제한 없음) · 영업/정상만',
               'law': '「교육환경 보호에 관한 법률」 제8조 제1항(학교경계등에서 직선거리 200m · 절대보호구역 = 학교출입문에서 50m) · 제9조 제19호·제24호·제26호·제27호와 단서(상대보호구역에서는 지역위원회 심의를 거쳐 인정된 것은 제외) — 국가법령정보 원문 2026-10-12 확인(시행 2026-06-03)',
               'note': ['**반경 안에 있다고 위반이 아니다** — 상대보호구역에서는 심의를 거쳐 허용된 곳이 있고, 학교보다 먼저 있던 곳도 섞여 있다. 이 파일은 「어디에 무엇이 있나」만 말한다',
                        '법의 거리는 학교 **경계**(200m)와 **출입문**(50m)에서 잰다 — 지도의 학교 자리는 점 하나라 그 거리와 다르다(운동장이 넓은 학교는 100m 넘게 어긋난다)',
                        '제19호·제24호는 유치원·대학의 보호구역에서는 빠진다 · 제27호 숙박업 가운데 대통령령으로 정하는 것은 빠진다(이 파일은 가르지 못한다)',
                        '인허가 대장의 「영업/정상」이다 — 실제로 문을 열고 있는지는 다를 수 있다 · 전국에서 좌표가 없거나 틀린 %d곳(%d%%)과 동 경계 밖 %d곳은 뺐다(시도마다 빠진 몫이 다르다 — 인천이 크다) · 상호·주소·전화는 싣지 않았다' % (noxy['all'], round(noxy['all'] / max(1, sum(ALLN.values())) * 100), nodong),
                        '청소년게임제공업(오락실·인형뽑기 등)도 법의 「게임제공업」에 든다 — 갈래를 나눠 실었으니 화면에서 골라 센다'],
               'fields': {'kinds': '[[갈래 이름, 제9조의 호, 이 시도의 곳 수]](items 의 갈래 번호 차례)', 'items': '[[경도, 위도, 갈래 번호, 시군구 코드 5자리(동 경계 밖이면 빈칸)]]'},
               'kinds': [[k[0], k[1], CNT[sd][i]] for i, k in enumerate(KINDS)], 'items': items}
        p = os.path.join(ROOT, 'data', 'edu-zone-biz', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        print(sd, '바이트', os.path.getsize(p), '곳', len(items), [CNT[sd][i] for i, k in enumerate(KINDS)])
    print('영업 중', sum(ALLN.values()), '좌표 없음', noxy['all'], '동 경계 밖', nodong, '서초', collections.Counter(KINDS[r[2]][0] for r in OUT['11'] if r[3] == '11650'))
if __name__ == '__main__': main()
