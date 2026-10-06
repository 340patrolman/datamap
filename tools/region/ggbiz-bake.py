# v2.58.0 경기 창업 자리 찾기 바탕 — data/r/ggbiz.json
#   소유자 「서울은 업종별 창업 데이터까지 나와 있는데 경기도는 없네 · 동백2동도 시뮬레이션 · 서울과 같거나 비슷하게」
#   경기 발달·골목상권 1,692곳(r/<구>/ggtrd.json · 산업분류 10차 업종별 한 분기 추정매출)마다 고른 31개 창업 업종의
#     한 달 매출(분기 ÷ 3) · 그 상권 다각형 안 같은 업종 점포(소상공인 상가정보 r/<구>/stores.json · 소분류를 산업분류에 손으로 맞춤) · 넓이(ha)
#   상권이 든 행정동마다 주민(r/<구>/dong.json) · 유동인구(ggdong.json 최신 해 평균) · 카드 매출 2022→2025(fac.json gcs)
#   업종마다 그 동 인허가 1·3·5년 생존 · 폐업 가게 평균 영업기간 · 지난해 폐업 ÷ 지금 영업(bizsv.json · 사례 5곳 미만이면 구 전체)
#   py -3.12 -X utf8 tools/region/ggbiz-bake.py
import json, os, glob, math
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.prepared import prep

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
# [열쇠, 이름, 산업분류 10차(경기 추정매출 업종명), 상가정보 소분류, 인허가 묶음(bizsv), 경기 카드 업종(fac gcs), 손익 계산 틀]
INDS = [
    ['hansik', '한식(백반·찌개·족발)', ['한식 일반 음식점업'], ['I20101', 'I20102', 'I20103', 'I20104', 'I20199'], '한식', '음식/한식', 'hansik'],
    ['meat', '고기구이', ['한식 육류 요리 전문점'], ['I20107', 'I20108', 'I20109', 'I20110'], '고기구이', '음식/고기요리', 'meat'],
    ['noodle', '국수·냉면', ['한식 면 요리 전문점'], ['I20105', 'I20106'], '한식', '음식/한식', 'noodle'],
    ['seafood', '횟집·해산물', ['한식 해산물 요리 전문점'], ['I20111', 'I20112', 'I20113'], '일식·횟집', '음식/일식/수산물', 'seafood'],
    ['chinese', '중식', ['중식 음식점업'], ['I20201', 'I20202'], '중식', '음식/중식', 'chinese'],
    ['japanese', '일식(초밥·돈가스·라멘)', ['일식 음식점업'], ['I20301', 'I20302', 'I20303', 'I20399'], '일식·횟집', '음식/일식/수산물', 'japanese'],
    ['western', '양식', ['서양식 음식점업'], ['I20401', 'I20402', 'I20403', 'I20499'], '양식·뷔페', '음식/양식', 'western'],
    ['pizza', '피자·버거·샌드위치', ['피자, 햄버거, 샌드위치 및 유사 음식점업'], ['I21003', 'I21004', 'I21005'], '패스트푸드', '음식/패스트푸드', 'pizza'],
    ['chicken', '치킨', ['치킨 전문점'], ['I21006'], '치킨·호프', '음식/닭/오리요리', 'chicken'],
    ['bunsik', '분식·김밥', ['김밥 및 기타 간이 음식점업'], ['I21007', 'I21099'], '분식·김밥', '음식/분식', 'bunsik'],
    ['bakery', '빵·떡·케이크', ['제과점업'], ['I21001', 'I21002'], '제과·디저트', '음식/제과/제빵/떡/케익', 'bakery'],
    ['cafe', '카페', ['커피 전문점'], ['I21201'], '카페·찻집', '음식/커피/음료', 'cafe'],
    ['hof', '호프(생맥주)', ['생맥주 전문점'], ['I21103'], '치킨·호프', '음식/간이주점', 'hof'],
    ['pub', '주점(요리주점 등)', ['기타 주점업'], ['I21104', 'I21101'], '주점', '음식/간이주점', 'pub'],
    ['conv', '편의점', ['체인화 편의점'], ['G20405'], '편의점', '소매/유통/종합소매점', None],
    ['hair', '미용실', ['두발 미용업'], ['S20701'], '미용실', '생활서비스/미용서비스', None],
    ['skin', '피부관리', ['피부 미용업'], ['S20702'], '피부관리', '생활서비스/미용서비스', None],
    ['laundry', '세탁소·빨래방', ['가정용 세탁업'], ['S20901', 'S20902'], '세탁소', '생활서비스/세탁/가사서비스', None],
    ['karaoke', '노래방', ['노래 연습장 운영업'], ['R10407'], '노래방', '여가/오락/취미/오락', None],
    ['pc', 'PC방', ['컴퓨터 게임방 운영업'], ['R10406'], 'PC방', '여가/오락/취미/오락', None],
    ['gym', '헬스장', ['체력 단련시설 운영업'], ['R10307'], '헬스장', '여가/오락/일반스포츠', None],
    ['pharm', '약국', ['의약품 및 의료용품 소매업'], ['G21501'], '약국', '의료/건강/의약/의료품', None],
    ['optic', '안경점', ['안경 및 렌즈 소매업'], ['G21602'], '안경원', None, None],
    ['academy', '입시·교과학원', ['일반 교과학원'], ['P10501'], None, '학문/교육/입시학원', None],
    ['clinic', '의원(치과·한의원 빼고)', ['일반의원'], ['Q10201', 'Q10202', 'Q10203', 'Q10204', 'Q10205', 'Q10206', 'Q10207', 'Q10208', 'Q10209', 'Q10212'], '의원', '의료/건강/일반병원', None],
    ['dental', '치과의원', ['치과의원'], ['Q10210'], '치과', None, None],
    ['oriental', '한의원', ['한의원'], ['Q10211'], '한의원', None, None],
    ['vet', '동물병원', ['수의업'], ['M11101'], '동물병원', '의료/건강/수의업', None],
    ['tkd', '태권도·무술', ['태권도 및 무술 교육기관'], ['P10601'], '체육도장', '학문/교육/예체능계학원', None],
    ['butcher', '정육점', ['육류 소매업'], ['G20503'], None, '소매/유통/음/식료품소매', None],
    ['motel', '여관·모텔', ['여관업'], ['I10102'], '숙박(여관·모텔)', '여가/오락/숙박', None],
]
SIDX = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8'))
CLS = {c[5]: i for i, c in enumerate(SIDX['cls'])}
C2I = {}
for ii, d in enumerate(INDS):
    for c in d[3]:
        assert c in CLS, c
        C2I[CLS[c]] = ii

def ha_of(g, lat0):   # 경위도 다각형 넓이(ha) — 위도 0 근처 등거리 근사
    kx, ky = 111320 * math.cos(math.radians(lat0)), 110574
    def ring(r): return abs(sum((r[i][0] * kx) * (r[i - 1][1] * ky) - (r[i - 1][0] * kx) * (r[i][1] * ky) for i in range(len(r)))) / 2
    a = 0
    for p in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        a += ring(list(p.exterior.coords)) - sum(ring(list(h.coords)) for h in p.interiors)
    return a / 1e4

def sv(a, b):
    s = lambda j: round(a[b + j * 2 + 1] / a[b + j * 2] * 100, 1) if a[b + j * 2] else None
    return [s(0), s(1), s(2), round(a[b + 6] / a[b + 7] / 365, 1) if a[b + 7] else None, a[b + 2]]

items, dongs, svs, quarter, gus = [], {}, {}, None, 0
for f in sorted(glob.glob(os.path.join(R, '41*', 'ggtrd.json'))):
    gd = os.path.dirname(f); gu = os.path.basename(gd); T = json.load(open(f, encoding='utf-8')); quarter = T['quarter']; gus += 1
    ST = json.load(open(os.path.join(gd, 'stores.json'), encoding='utf-8')); O, K = ST['o'], ST['k']
    pts = [(O[0] + q[0] / K[0], O[1] + q[1] / K[1], C2I[q[2]]) for q in ST['pts'] if q[2] in C2I]
    DJ = json.load(open(os.path.join(gd, 'dong.json'), encoding='utf-8'))
    DP = []
    for d in DJ['dong']:
        try: DP.append((d['k'], d['name'], prep(MultiPolygon([Polygon(p[0], p[1:]) for p in d['polys']])), d))
        except Exception: pass
    GD = json.load(open(os.path.join(gd, 'ggdong.json'), encoding='utf-8')) if os.path.exists(os.path.join(gd, 'ggdong.json')) else {'dong': {}}
    FA = json.load(open(os.path.join(gd, 'fac.json'), encoding='utf-8')) if os.path.exists(os.path.join(gd, 'fac.json')) else {'dong': {}}
    BZ = json.load(open(os.path.join(gd, 'bizsv.json'), encoding='utf-8')); N = len(BZ['years']); b = 1 + 2 * N
    G = {}
    for k8, v in BZ['dong'].items():
        for ci, a in v.items():
            t = G.setdefault(ci, [0] * len(a))
            for i, x in enumerate(a): t[i] += x
    for it in T['items']:
        try: g = MultiPolygon([Polygon(r) for r in it['rings']]) if len(it['rings']) > 1 else Polygon(it['rings'][0])
        except Exception: continue
        if not g.is_valid: g = g.buffer(0)
        pg = prep(g); x0, y0, x1, y1 = g.bounds
        cnt = {}
        for lo, la, ii in pts:
            if x0 <= lo <= x1 and y0 <= la <= y1 and pg.contains(Point(lo, la)): cnt[ii] = cnt.get(ii, 0) + 1
        pt = Point(it['lon'], it['lat']); dk = None
        for k8, nm, pp, d in DP:
            if pp.contains(pt): dk = (k8, nm, d); break
        if not dk:
            dk = next(((k8, nm, d) for k8, nm, pp, d in DP if nm == it.get('dong')), None)
        k8 = dk[0] if dk else ''
        if dk and k8 not in dongs:
            d = dk[2]; fl = GD['dong'].get(k8, {}).get('flow') or {}; fy = max(fl) if fl else None
            gc = FA['dong'].get(k8, {}).get('gcs') or {}
            dongs[k8] = [dk[1], (d.get('pop') or {}).get('tot'), fl[fy]['TOT'] if fy else None, fy,
                         round((gc['h25'] - gc['h22']) / gc['h22'] * 100, 1) if gc.get('h22') else None,
                         {t[0]: round((t[1] - t[2]) / t[2] * 100, 1) for t in gc.get('ind', []) if t[2]}]
            s = svs[k8] = {}
            for ii, dd in enumerate(INDS):
                if not dd[4]: continue
                ci = str(BZ['cats'].index(dd[4])); a = BZ['dong'].get(k8, {}).get(ci); gA = G.get(ci)
                use, isg = (a, 0) if a and a[b + 2] >= 5 else (gA, 1)
                if not use: continue
                now = a[0] if a else 0; cl = a[1 + N + N - 2] if a else 0   # 지난해(2025) 폐업
                s[ii] = sv(use, b) + [isg, now, cl]
        amt = {}
        for r in it.get('ind') or []:
            for ii, dd in enumerate(INDS):
                if r[0] in dd[2]: a = amt.setdefault(ii, [0, 0]); a[0] += r[1]; a[1] += r[2]
        per = {}
        for ii in set(amt) | set(cnt):
            a = amt.get(ii, [0, 0]); per[ii] = [round(a[0] / 3), round(a[1] / 3), cnt.get(ii, 0)]
        items.append([it['n'], it['k'], gu, k8, round(it['lat'], 5), round(it['lon'], 5), round(ha_of(g, it['lat']), 2), it.get('st') or 0, (it.get('tot') or [0])[0] and round(it['tot'][0] / 3) or 0, {str(k): v for k, v in per.items()}])
    print(gu, len(T['items']))

doc = {'schema': 'tg-ggbiz/1', 'quarter': quarter, 'baked': __import__('datetime').date.today().isoformat(),
       'source': '경기데이터드림 발달·골목상권 영역과 추정매출(경기도시장상권진흥원 · 산업분류 10차 · ' + quarter + '분기) · 소상공인시장진흥공단 상가정보(' + SIDX['stdrYm'] + ') · 지방행정 인허가(LOCALDATA) · 경기 카드 매출(경기데이터드림) · 주민등록 인구',
       'note': '한 달 매출 = 경기도 추정 분기 매출 ÷ 3(모델 추정값 · 실제 매출 아님 · 공개분 한 분기) · 점포 = 그 상권 다각형 안 상가정보 점포(소분류를 산업분류에 손으로 맞춤 — 1:1 이 아니다) · 생존·성장·인구는 상권이 든 행정동 값(같은 동 상권은 같다)',
       'fields': 'inds = [열쇠, 이름, 산업분류, 상가 소분류, 인허가 묶음, 카드 업종, 손익 틀] · items = [이름, dev/alley, 구, 행정동, 위도, 경도, 넓이 ha, 상권 점포, 상권 한 달 매출(만 원), {업종 자리: [한 달 매출 만 원, 한 달 건수, 상권 안 같은 업종 점포]}] · dong = {행정동: [이름, 주민, 유동 하루 평균, 유동 해, 카드 매출 2022→2025 %(전체), {카드 업종: %}]} · sv = {행정동: {업종 자리: [1년 생존 %, 3년, 5년, 폐업 가게 평균 영업 년, 3년 대상 수, 구 값이면 1, 지금 영업, 지난해 폐업]}}',
       'inds': INDS, 'items': items, 'dong': dongs, 'sv': svs}
fn = os.path.join(R, 'ggbiz.json')
json.dump(doc, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('구', gus, '상권', len(items), '동', len(dongs), os.path.getsize(fn), 'B')
