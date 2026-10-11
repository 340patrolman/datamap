# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🍺 음주 단속·순찰 참고: 행정동마다 「술자리가 어디·언제 몰리나」와 「밤 사고가 어디 났나」를 나란히(소유자 2026-10-11 「음주단속 지점 선정의 전제가 바뀌었다」
#   「경찰관 업무용으로는 자세히」) → data/dui-ref-seoul.json
#   재료(모두 이미 구운 것): 등록 상가 소분류(data/storecls/11.json — 주점 넷·노래방) · 동 매출(data/r/<구>/dongx.json — 호프·간이주점 매출·시간대 건수·연령 · 서울 상권분석 추정매출)
#                         · 사고 10년 100m 칸(data/r/<구>/taas10.json · 서초는 data/taas10-seocho.json — 밤 20~6시 · 0~6시 건수)
#   **한 점수로 뭉치지 않는다**(무게를 지어내지 않는다) — 동마다 잰 값을 나란히 싣고, 서울 동들 가운데 몇 번째쯤인지(백분위)만 곁들인다
#   사고 자료에 「음주」 구분이 없다 — 밤 사고는 음주 사고가 아니다(밤에 난 모든 사고) · 음주 사고의 구·해 값은 data/gen-trend.json · 적발은 data/dui-catch-st.json
#   py -3.12 -X utf8 tools/region/duiref-bake.py
import json, os, glob, datetime, bisect
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BAR = {108: '일반 유흥 주점', 109: '무도 유흥 주점', 110: '생맥주 전문', 111: '요리 주점'}; KARA = 219
def inside(px, py, ring):
    c = False; j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i][0], ring[i][1]; xj, yj = ring[j][0], ring[j][1]
        if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi: c = not c
        j = i
    return c
def bake(sd, out, area):
    SC = json.load(open(os.path.join(ROOT, 'data', 'storecls', sd + '.json'), encoding='utf-8'))['dong']; rows = []; thin = []
    for dp in sorted(glob.glob(os.path.join(ROOT, 'data', 'r', sd + '*', 'dong.json'))):
        gd = os.path.dirname(dp); gu = os.path.basename(gd); D = json.load(open(dp, encoding='utf-8')); dongs = D.get('dong') or []
        xp = os.path.join(gd, 'dongx.json'); X = json.load(open(xp, encoding='utf-8')).get('dong', {}) if os.path.exists(xp) else {}
        gp = os.path.join(gd, 'ggdong.json'); GG = json.load(open(gp, encoding='utf-8')).get('dong', {}) if os.path.exists(gp) else {}
        tp = os.path.join(ROOT, 'data', 'taas10-seocho.json') if gu == '11650' else os.path.join(gd, 'taas10.json'); cells = json.load(open(tp, encoding='utf-8')).get('cells', []) if os.path.exists(tp) else []
        if len(cells) < 100: thin.append(gu)
        box = []
        for d in dongs:
            xs = [p[0] for poly in d['polys'] for p in poly[0]]; ys = [p[1] for poly in d['polys'] for p in poly[0]]; box.append((min(xs), min(ys), max(xs), max(ys)))
        acc = [[0, 0, 0] for _ in dongs]
        for c in cells:
            la, lo = c[0], c[1]
            for i, d in enumerate(dongs):
                b = box[i]
                if lo < b[0] or lo > b[2] or la < b[1] or la > b[3]: continue
                if any(inside(lo, la, poly[0]) for poly in d['polys']): acc[i][0] += sum(c[2:12]); acc[i][1] += c[18]; acc[i][2] += c[19]; break
        for i, d in enumerate(dongs):
            k = str(d['k']); sc = SC.get(k); cnt = dict(sc[2]) if sc else {}
            bars = [cnt.get(c, 0) for c in BAR]; hof = next((r for r in (X.get(k) or {}).get('ind', []) if r[0] == '호프-간이주점'), None) if sd == '11' else None
            sal = hof[1] if hof else None; card = (GG.get(k) or {}).get('card') or {}; old = None
            if sd == '41' and card:   # 경기 = 경기데이터드림 카드 매출의 간이주점(Q01) + 유흥주점(Q08) — 시간대·연령은 업종별로 없다
                def q(y): v = card.get(y) or {}; return (v.get('Q01') or 0) + (v.get('Q08') or 0) if ('Q01' in v or 'Q08' in v) else None
                sal = q('2025'); old = q('2022')
            tcnt = hof[24:30] if hof and len(hof) >= 36 else None; age = hof[9:15] if hof else None
            rows.append({'k': k, 'nm': d['name'], 'gu': gu, 'll': d.get('c'), 'bars': bars, 'bar': sum(bars), 'kara': cnt.get(KARA, 0), 'sal': sal,
                         'late': round((tcnt[5] + tcnt[0]) / sum(tcnt) * 100) if tcnt and sum(tcnt) else None, 'n2124': tcnt[5] if tcnt else None, 'n0006': tcnt[0] if tcnt else None,
                         'young': round((age[1] + age[2]) / sum(age) * 100) if age and sum(age) else None, 'acc': acc[i][0] if gu not in thin else None, 'accN': acc[i][1] if gu not in thin else None, 'acc06': acc[i][2] if gu not in thin else None, 'old': old})
    def pct(key):
        v = sorted(r[key] for r in rows if r[key] is not None)
        for r in rows: r['p_' + key] = round(bisect.bisect_right(v, r[key]) / len(v) * 100) if r[key] is not None and v else None
    for key in ('bar', 'sal', 'n0006', 'accN', 'acc06'): pct(key)
    items = [[r['k'], r['nm'], r['gu'], r['ll'], r['bar'], r['bars'], r['kara'], r['sal'], r['late'], r['n2124'], r['n0006'], r['young'], r['acc'], r['accN'], r['acc06'], [r['p_bar'], r['p_sal'], r['p_n0006'], r['p_accN'], r['p_acc06']], r['old']] for r in rows]
    doc = {'schema': 'tg-dui-ref/1', 'made': datetime.date.today().isoformat(), 'area': area,
           'source': '소상공인시장진흥공단 상가(상권)정보(등록 상가 소분류 · data/storecls) · 서울시 상권분석서비스 추정매출-행정동(호프·간이주점 · data/r/<구>/dongx.json) · 도로교통공단 TAAS 사고 10년(2016~2025 · 100m 칸 · data/r/<구>/taas10.json)',
           'note': ['**한 점수가 아니다** — 술자리가 몰리는 곳(주점 수 · 호프 매출 · 심야 결제)과 밤 사고가 난 곳을 나란히 본다. 어디서 단속할지는 길의 모양·빠져나가는 길·현장 경험이 같이 정한다',
                    '**밤 사고와 음주(소유자 현장 지식 2026-10-11)**: 「밤에 나는 교통사고 가운데 절반, 적어도 30% 는 음주와 관련돼 있다 — 마신 곳과 사고 난 곳은 달라도 단속에 쓸 수 있다」. 기록된 통계로 어림하면 서울 2016~2025 음주운전 사고 22,638건 ÷ 밤 20~6시 사고 101,830건 = 많아야 22%(음주 사고의 65% 가 밤이라 치면 15% 안팎 · 새벽 0~6시만은 17% 안팎) — **통계는 음주로 적발·기록된 사고만 센다**(측정 전 달아남 · 음주 뒤 피해자 쪽 · 숙취는 빠진다). 현장 감각이 통계보다 높은 까닭으로 보인다',
                    '**밤 사고는 음주 사고가 아니다** — 20~6시에 난 모든 사고다(이 사고 자료에 음주 구분이 없다) · 사고는 난 자리이고 술을 마신 자리가 아니다(마신 동과 사고 난 동은 다를 수 있다)',
                    '주점 = 등록 상가의 소분류 넷(일반 유흥 · 무도 유흥 · 생맥주 전문 · 요리 주점) — 등록 정보라 지금 영업하는지는 모른다 · 호프 매출·결제 건수는 카드 추정(현금 제외 · 한 달 평균)',
                    '경기의 주점 매출(경기데이터드림 카드 · 간이주점 + 유흥주점)은 **크기를 그대로 믿지 않는다** — 점포 수에 견줘 값이 너무 작다(수원 인계동 주점 313곳에 한 달 7,390만원 · 단위나 표본 범위를 확인하지 못했다). 동끼리의 크고 작음과 2022 → 2025 변화로만 읽는다',
                    '결제한 사람이 운전한다는 뜻이 아니다 · 백분위는 그 시도 동들 가운데의 자리(100 = 가장 많은 쪽)일 뿐 좋고 나쁨이 아니다',
                    '사고 값 null = 그 구의 사고 자료가 비어 있다(다시 모으는 중인 구: %s)' % ' '.join(thin)],
           'bars': list(BAR.values()),
           'fields': 'items[[0 행정동 코드, 1 이름, 2 구 코드, 3 [경도, 위도], 4 주점 점포 수, 5 [일반 유흥, 무도 유흥, 생맥주 전문, 요리 주점], 6 노래방, 7 호프·간이주점 한 달 매출 만원, 8 그 결제 가운데 21~06시 %, 9 21~24시 결제 건수, 10 0~6시 결제 건수, 11 호프 매출의 20·30대 %, 12 사고 10년 건수, 13 그 가운데 밤 20~6시, 14 0~6시, 15 서울 동 가운데 백분위[주점 수, 호프 매출, 0~6시 결제, 밤 사고, 0~6시 사고], 16 주점 매출 3년 전(경기만 · 2022년 같은 달 평균 만원 — 7 과 견준다)]] · 경기 = 7 이 간이주점 + 유흥주점 카드 매출(2025년 1~6월 평균)이고 8~11(시간대·연령)은 null · 인천 = 7~11 null(동 단위 업종 매출 자료 없음)',
           'items': items}
    p = os.path.join(ROOT, 'data', out); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(area, '· 동', len(items), '· 바이트', os.path.getsize(p), '· 사고 자료가 빈 구', thin, '· 주점 매출 있는 동', sum(1 for r in items if r[7] is not None))
    for r in sorted(items, key=lambda x: -(x[13] or 0))[:6]: print('   %-10s 주점 %3d · 매출 %s(3년 전 %s) · 밤 사고 %s · 새벽 %s · 백분위 %s' % (r[1], r[4], r[7], r[16], r[13], r[14], r[15]))
def main():
    bake('11', 'dui-ref-seoul.json', '서울 25구 행정동'); bake('41', 'dui-ref-gg.json', '경기도 행정동'); bake('28', 'dui-ref-incheon.json', '인천광역시 행정동')
if __name__ == '__main__': main()
