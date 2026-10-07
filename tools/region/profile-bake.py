# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.10.0 — 🤖 AI용 지역 프로필(소유자 2026-10-05 「기초 자료를 AI 가 쉽게 쓸 수 있게 · 그 지역 기본 파악이 빨리 되게」)
#   행정동 하나 = 한 덩어리(인구 구성 → 가구 → 머무는 사람 → 이동 → 돈(카드) → 가게 → 집 → 사고 → 시설 → 치안) · 시군구 덩어리(외국인·점유형태·소득)
#   이 지도에 이미 구운 파일만 다시 묶는다(새로 받는 자료 없음 · 지어낸 값 없음) — 값마다 출처·기준 시점은 sources 에 · 추정은 「추정」이라 적는다
#   py -3.12 -X utf8 tools/region/profile-bake.py [시도코드…] → data/r/<구>/profile.json + index.json bytes
import json, os, sys, time, math, collections
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regcfg as RC

def J(p):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return None
def pct(a, b): return round(a / b * 100, 1) if b else None
def rnd(v, n=0):
    if v is None: return None
    return round(v, n) if n else int(round(v))

AGE10 = ['0~9', '10~19', '20~29', '30~39', '40~49', '50~59', '60~69', '70~79', '80~89', '90~99']
AGE6 = ['10대', '20대', '30대', '40대', '50대', '60대 이상']
DOW = ['월', '화', '수', '목', '금', '토', '일']
FAC = {'cc': '어린이집', 'kg': '유치원', 'edu': '학교', 'aca': '학원', 'kyr': '경로당', 'gov': '관공서', 'cam': '단속 카메라', 'sz': '어린이보호구역 대상', 'aed': 'AED', 'er': '응급의료기관',
       'fire': '소방용수', 'wc': '공중화장실', 'park': '주차장', 'ev': '전기차 충전', 'srItem': '안심귀갓길 시설', 'box': '안심택배함', 'dem': '치매안심센터', 'tow': '견인보관소'}

def mk_poly(polys):
    ps = []
    for pg in polys:
        try:
            p = Polygon(pg[0], pg[1:]).buffer(0)
            if not p.is_empty: ps.append(p)
        except Exception: pass
    if not ps: return None
    return ps[0] if len(ps) == 1 else MultiPolygon([q for p in ps for q in (p.geoms if hasattr(p, 'geoms') else [p])])

def km2(g):
    if g is None: return None
    c = g.centroid; return round(g.area * 111.32 * math.cos(math.radians(c.y)) * 110.57, 2)

def main(sidos):
    IX = J(os.path.join(R, 'index.json')); POL = J(os.path.join(ROOT, 'data', 'police.json')); FRN = J(os.path.join(ROOT, 'data', 'foreign.json'))
    CEN = J(os.path.join(ROOT, 'data', 'gu-census.json')); TAX = J(os.path.join(ROOT, 'data', 'gu-tax.json')); SIDX = J(os.path.join(R, 'stores-index.json'))
    CLS = [c[1] for c in SIDX['cls']] if SIDX else []
    pol_by = {s[0]: s for s in POL['stations']} if POL else {}
    def police(k8):
        if not POL or k8 not in POL['dong']: return None
        L = str(POL['labels'][POL['dong'][k8]]); main_, _, extra = L.partition('~')
        f = lambda t: [{'경찰서': pol_by[int(x)][1], '대표번호': pol_by[int(x)][4] or None} for x in t.split(',') if x and int(x) in pol_by]
        o = {'관할': f(main_)}
        if len(o['관할']) > 1: o['비고'] = '두 서가 번지로 나눠 맡는 동(경계)'
        if extra: o['일부 번지'] = f(extra)
        return o
    total = 0; ngu = 0
    for g in IX['gus']:
        gu = g['gu']
        if sidos and gu[:2] not in sidos: continue
        D = J(os.path.join(R, gu, 'dong.json'))
        if not D: continue
        B = g.get('bytes', {})
        dongs = D['dong']; polys = {}; geo = []
        for d in dongs:
            p = mk_poly(d.get('polys') or [])
            if p is not None: polys[d['k']] = p; geo.append((d['k'], p))
        tree = STRtree([p for _, p in geo]) if geo else None
        def where(lon, lat):
            if not tree: return None
            q = Point(lon, lat)
            for i in tree.query(q):
                if geo[i][1].contains(q): return geo[i][0]
            return None
        GRID = {}
        gj = J(os.path.join(R, gu, 'grid.json'))
        if gj:
            for c in gj['cells']:
                if len(c) > 4: GRID[c[0]] = c[4]
        out = {}
        for d in dongs:
            k = d['k']; o = {'이름': d['name'], '코드': k, '넓이_km2': km2(polys.get(k)), '가운데': d.get('c')}
            p = d.get('pop')
            if p and p.get('tot'):
                a = p['age']; t = p['tot']
                o['주민'] = {'계': t, '남': p.get('m'), '여': p.get('f'), '성비(여 100명당 남)': rnd(p['m'] / p['f'] * 100, 1) if p.get('m') and p.get('f') else None,
                            '연령10세': dict(zip(AGE10, a)), '연령 비중%': {'0~19': pct(a[0] + a[1], t), '20~39': pct(a[2] + a[3], t), '40~59': pct(a[4] + a[5], t), '60 이상': pct(sum(a[6:]), t), '70 이상': pct(sum(a[7:]), t)}}
                if p.get('mage'): o['주민']['연령10세_남'] = dict(zip(AGE10, p['mage'])); o['주민']['연령10세_여'] = dict(zip(AGE10, p['fage']))
            lv = d.get('live')
            if lv and lv.get('wd'):
                wd, we = lv['wd'], lv['we']; pk = wd.index(max(wd)); day = sum(wd[11:14]) / 3; ngt = sum(wd[1:4]) / 3
                o['머무는 사람(생활인구)'] = {'평일 시간대(0~23시)': [rnd(v) for v in wd], '주말 시간대(0~23시)': [rnd(v) for v in we], '평일 가장 많을 때': f'{pk}시 {rnd(wd[pk])}명',
                                        '낮(11~14시)÷새벽(1~3시)': rnd(day / ngt, 2) if ngt else None, '주말÷평일(하루 합)': rnd(sum(we) / sum(wd), 2) if sum(wd) else None,
                                        '주민 대비 평일 낮': rnd(day / p['tot'], 2) if p and p.get('tot') else None}
            sl = d.get('sales')
            if sl and sl.get('amt'):
                a = sl['amt']; tbs = sl.get('tb') or []; dw = sl.get('dw') or []
                o['카드 매출(추정)'] = {'분기': D.get('quarter'), '기간': '한 달 평균(서울 상권분석 분기 합계 ÷ 3)', '매출_만원': a, '건수': sl.get('cnt'), '주민 1인당_만원': rnd(a / p['tot'], 1) if p and p.get('tot') else None,
                                    '시간대 비중%': {D['tb'][i]: pct(v, sum(tbs)) for i, v in enumerate(tbs)} if tbs else None, '요일 비중%': {DOW[i]: pct(v, sum(dw)) for i, v in enumerate(dw)} if dw else None,
                                    '업종 상위': [{'업종': r[0], '매출_만원': r[1], '비중%': pct(r[1], a)} for r in (sl.get('top') or [])[:10]]}
            out[k] = o
        # 서울 카드 매출 — 연령·성별(dongx 업종 줄 합)
        X = J(os.path.join(R, gu, 'dongx.json'))
        if X and X.get('dong'):
            for k, x in X['dong'].items():
                if k not in out or '카드 매출(추정)' not in out[k]: continue
                ag = [0] * 6; m = f = 0
                for r in x.get('ind', []):
                    if len(r) > 16:
                        for i in range(6): ag[i] += r[9 + i] or 0
                        m += r[15] or 0; f += r[16] or 0
                s6 = sum(ag)
                if s6: out[k]['카드 매출(추정)']['연령 비중%'] = {AGE6[i]: pct(v, s6) for i, v in enumerate(ag)}
                if m + f: out[k]['카드 매출(추정)']['남녀 비중%'] = {'남': pct(m, m + f), '여': pct(f, m + f)}
        # 경기 카드 매출·유동인구(경기데이터드림)
        GG = J(os.path.join(R, gu, 'ggdong.json'))
        if GG:
            for k, x in (GG.get('dong') or {}).items():
                if k not in out: continue
                c = x.get('card') or {}; tt = {y: sum(q for kk, q in v.items() if kk != 'TO') for y, v in c.items()}
                if tt: out[k]['카드 매출(경기)'] = {'1~6월 월평균_만원': {y: rnd(v) for y, v in sorted(tt.items())}, '비고': '경기데이터드림 가공 카드 자료 · 업종 이름 = ggdong.json names(세 글자 코드표 · 코워크 2026-10-07) · 업종전체 칸은 빼고 더함 · 서울 추정매출과 금액을 직접 견주지 않는다'}
                fl = x.get('flow') or {}
                if fl:
                    y = max(fl); v = fl[y]; out[k]['유동인구(경기)'] = {'해': y, '요일 평균': v}
        # 경기 카드 소비 상세(경기데이터드림 카드 소비 데이터 · v2.12.0 · 일부 시만)
        GC = J(os.path.join(R, gu, 'ggcard.json'))
        if GC:
            per = '%s~%s' % (GC['months'][0], GC['months'][-1])
            for k, x in (GC.get('dong') or {}).items():
                if k not in out or not x.get('amt'): continue
                a = x['amt']; s6 = sum(x['ag']) or 1; sx = sum(x['sx']) or 1; dw = sum(x['dw']) or 1; hr = sum(x['hr']) or 1
                out[k]['카드 소비(경기 상세)'] = {'기간': per, '한 달 평균_만원': a, '한 달 건수': x['cnt'], '주민 1인당_만원': rnd(a / out[k]['주민']['계'], 1) if out[k].get('주민', {}).get('계') else None,
                    '연령 비중%': {GC['ag'][i]: pct(v, s6) for i, v in enumerate(x['ag'])}, '남녀 비중%': {'남': pct(x['sx'][0], sx), '여': pct(x['sx'][1], sx)},
                    '시간대 비중%': {GC['hr'][i]: pct(v, hr) for i, v in enumerate(x['hr'])}, '요일 비중%': {DOW[i]: pct(v, dw) for i, v in enumerate(x['dw'])},
                    '업종 대분류': [{'업종': b, '한 달_만원': v, '비중%': pct(v, a)} for b, v in x['big']], '업종 중분류 상위': [{'업종': b, '한 달_만원': v} for b, v in x['mid'][:10]],
                    '비고': '카드 다섯 곳(국민·비씨·롯데·삼성·하나) 결제만 · 공공누리 2유형(상업 이용 금지)'}
        # 가구·주택·사업체(SGIS 집계구 2023 — 동 이름으로 합)
        JG = J(os.path.join(R, gu, 'jgg.json'))
        if JG:
            byname = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0]); nm2k = {o['이름']: k for k, o in out.items()}
            for it in JG['items']:
                v = it[4:10]; b = byname[it[1]]
                for i, idx in ((0, 0), (1, 1), (3, 3), (4, 4), (5, 5)):
                    if isinstance(v[idx], (int, float)): b[i] += v[idx]
            for nm, b in byname.items():
                k = nm2k.get(nm)
                if k: out[k]['가구·주택·사업체(SGIS)'] = {'해': JG.get('year'), '인구': b[0], '가구': b[1], '인구÷가구': rnd(b[0] / b[1], 2) if b[1] else None, '주택': b[3], '사업체': b[4], '종사자': b[5],
                                                    '종사자÷인구': rnd(b[5] / b[0], 2) if b[0] else None}
        # 가게(소상공인 상가) — 점이 든 동
        ST = J(os.path.join(R, gu, 'stores.json'))
        if ST and CLS:
            O, K = ST['o'], ST['k']; cnt = collections.defaultdict(collections.Counter)
            for q in ST['pts']:
                k = where(O[0] + q[0] / K[0], O[1] + q[1] / K[1])
                if k: cnt[k][CLS[q[2]] if q[2] < len(CLS) else '?'] += 1
            for k, c in cnt.items():
                if k in out:
                    n = sum(c.values()); pp = out[k].get('주민', {}).get('계')
                    out[k]['가게(상가업소)'] = {'기준': ST.get('stdrYm'), '계': n, '주민 1천 명당': rnd(n / pp * 1000, 1) if pp else None, '대분류': dict(c.most_common())}
        # 대중교통(서울·경기 교통카드)
        TR = J(os.path.join(R, gu, 'transit.json'))
        if TR:
            agg = collections.defaultdict(lambda: {'정류장': 0, '버스 하루 승차': 0, '버스 하루 하차': 0, '역': [], '역 하루 승차': 0, '역 하루 하차': 0, 'on': [0] * 24, 'off': [0] * 24})
            for b in TR.get('bus') or []:
                k = where(b[2], b[3])
                if not k: continue
                a = agg[k]; a['정류장'] += 1; a['버스 하루 승차'] += sum(b[4]); a['버스 하루 하차'] += sum(b[5]); a['on'] = [x + y for x, y in zip(a['on'], b[4])]; a['off'] = [x + y for x, y in zip(a['off'], b[5])]
            for s in TR.get('sub') or []:
                k = where(s[2], s[3])
                if not k: continue
                a = agg[k]; a['역'].append(s[0] + '(' + '·'.join(s[1]) + ')'); a['역 하루 승차'] += sum(s[4]); a['역 하루 하차'] += sum(s[5]); a['on'] = [x + y for x, y in zip(a['on'], s[4])]; a['off'] = [x + y for x, y in zip(a['off'], s[5])]
            for k, a in agg.items():
                if k not in out: continue
                on_, off = a.pop('on'), a.pop('off'); ton, tof = sum(on_), sum(off)
                for q in ('버스 하루 승차', '버스 하루 하차', '역 하루 승차', '역 하루 하차'): a[q] = rnd(a[q])
                a['승차 많은 때'] = f'{on_.index(max(on_))}시' if ton else None; a['하차 많은 때'] = f'{off.index(max(off))}시' if tof else None
                a['아침(7~9시) 하차÷승차'] = rnd(sum(off[7:10]) / sum(on_[7:10]), 2) if sum(on_[7:10]) else None
                a['해석 기준'] = '아침 하차가 승차보다 많으면 일하러 들어오는 동 · 적으면 나가는 동(주거)'
                a['기준'] = TR.get('ym'); out[k]['이동(대중교통)'] = dict(a)
        # 교통사고 10년(TAAS 250m 칸 → 칸이 가장 넓게 걸친 동)
        T2 = J(os.path.join(R, gu, 'taas250.json'))
        if T2:
            agg = collections.defaultdict(lambda: [0] * 21)
            for ck, c in T2['cells'].items():
                k = GRID.get(ck) or where(c[1], c[0])
                if not k: continue
                a = agg[k]
                for i in range(21): a[i] += c[2 + i] or 0
            for k, a in agg.items():
                if k not in out: continue
                n = sum(a[:10])
                out[k]['교통사고(TAAS 2016~2025)'] = {'계': n, '해마다': dict(zip(range(2016, 2026), a[:10])), '사망자': a[10], '중상자': a[11], '보행자 피해': a[12], '자전거': a[13], 'PM': a[14], '이륜·원동기 가해': a[15],
                                                 '밤(20~6시)%': pct(a[16], n), '시간대%': {'0~6시': pct(a[17], n), '6~12시': pct(a[18], n), '12~18시': pct(a[19], n), '18~24시': pct(a[20], n)},
                                                 '주민 1천 명당 해마다': rnd(n / 10 / out[k]['주민']['계'] * 1000, 2) if out[k].get('주민') else None, '비고': '250m 칸을 가장 넓게 걸친 동에 몰아 셈(근사)'}
        # 집(국토부 실거래 · 행정동)
        H = J(os.path.join(R, gu, 'home.json'))
        if H:
            TY = {'a': '아파트', 'o': '오피스텔', 'r': '연립다세대'}
            for k, v in (H.get('dong') or {}).items():
                if k not in out: continue
                o2 = {}
                for t, x in v.items():
                    o2[TY.get(t, t)] = {'매매 건수': x[0], '매매 평당_만원(전용)': rnd(x[1] * 3.3058) if x[1] else None, '전세 건수': x[2], '전세 평당_만원': rnd(x[3] * 3.3058) if x[3] else None, '월세 건수': x[4], '월세 중앙값_만원': x[5], '전세가율%(추정)': x[6]}
                out[k]['집값(실거래)'] = {'기간': '매매 2024-09~2026-08 · 전월세 2025-09~2026-08', **o2}
        # 지금 머무는 외국인(서울 250m) · 시설(pts250)
        F = J(os.path.join(R, gu, 'forn250.json'))
        if F:
            agg = collections.defaultdict(lambda: {'L': [0] * 24, 'T': [0] * 24, 'nat': collections.Counter()})
            for ck, c in F['cells'].items():
                k = GRID.get(ck)
                if not k: continue
                a = agg[k]
                for q in ('L', 'T'):
                    if q in c:
                        a[q] = [x + y for x, y in zip(a[q], c[q]['wd'])]
                        for n_, v in c[q]['nat']: a['nat'][n_ + ('(장기)' if q == 'L' else '(단기)')] += v
            for k, a in agg.items():
                if k in out: out[k]['머무는 외국인(서울 생활인구 · 추정)'] = {'평일 14시 장기체류': rnd(a['L'][14]), '평일 14시 단기체류': rnd(a['T'][14]), '평일 3시 장기체류': rnd(a['L'][3]),
                                                                    '국적 상위(모든 시각 평균 인원)': [[n_, rnd(v, 1)] for n_, v in a['nat'].most_common(6)]}
        PT = J(os.path.join(R, gu, 'pts250.json'))
        if PT:
            agg = collections.defaultdict(collections.Counter)
            for ck, c in PT['cells'].items():
                k = GRID.get(ck)
                if not k: continue
                for q in FAC:
                    if c.get(q): agg[k][FAC[q]] += c[q]
                if c.get('fat'): agg[k]['사망사고(건)'] += c['fat']
            for k, c in agg.items():
                if k in out and c: out[k]['시설(250m 칸 합 · 근사)'] = dict(c.most_common())
        FD = main.__dict__.setdefault('_fd', J(os.path.join(ROOT, 'data', 'foreign-dong.json'))); FL = main.__dict__.setdefault('_fl', J(os.path.join(ROOT, 'data', 'lodging-seoul.json')))
        for k in out:
            f = FD and FD['dong'].get(k)
            if f: out[k]['외국인주민(이 동 · 행안부 2024.11)'] = {'합계': f.get('t'), '한국국적 없음': f.get('nf'), '외국인근로자': f.get('w'), '결혼이민자': f.get('m'), '유학생': f.get('s'), '외국국적동포': f.get('k'), '기타외국인': f.get('e'), '한국국적 취득': f.get('n'), '외국인주민 자녀': f.get('c'),
                                     '주민 대비%': round(f['t'] / out[k]['주민']['계'] * 100, 1) if f.get('t') and out[k].get('주민', {}).get('계') else None, '다문화가구원 [합계, 한국인 배우자, 결혼이민·귀화, 자녀, 기타동거인]': f.get('mc'), '비고': '빈칸 = 작아서 가린 값(*)'}
            MB = J(os.path.join(R, gu, 'minbak.json')) if k == next(iter(out)) else MB
            if MB and MB['dong'].get(k): out[k]['외국인관광 도시민박(업소 수 · 영업+휴업)'] = MB['dong'][k]
            l = FL and FL['dong'].get(k)
            if l: out[k]['외국인 관광숙박(서울 · 영업 중)'] = l
        for k in out:
            pc = police(k)
            if pc: out[k]['치안(경찰 관할)'] = pc
        # 시군구 덩어리
        G = {'코드': gu, '이름': g.get('name'), '시도': RC.NAME.get(gu[:2], gu[:2]), '행정동 수': len(out)}
        pops = [o['주민']['계'] for o in out.values() if o.get('주민')]
        if pops: G['주민 계'] = sum(pops)
        fx = FRN and FRN['gu'].get(gu)
        if fx:
            v = fx.get('2024') or {}
            G['외국인(구)'] = {'외국인주민(행안부 2024.11.1)': v.get('tot'), '총인구 대비%': pct(v.get('tot') or 0, v.get('pop') or 0), '한국국적 없음': v.get('nf'), '근로자': v.get('work'), '결혼이민': v.get('marr'), '유학생': v.get('stud'),
                              '외국국적동포': v.get('kor'), '귀화': v.get('nat'), '외국인주민 자녀': v.get('kid'), '체류자격(법무부 2025 말)': fx.get('q'), '국적 상위 [국적, 계, 남, 여]': fx.get('nat'), '값의 출처 이름': fx.get('src')}
        LP = J(os.path.join(ROOT, 'data', 'livepop.json')) if gu == IX['gus'][0]['gu'] or not hasattr(main, '_lp') else main._lp
        main._lp = LP; lp = LP and LP['gu'].get(gu)
        if lp:
            ms = sorted(lp['m']); v = lp['m'][ms[-1]]
            G['생활인구(통계청 · 인구감소지역)'] = {'기준월': ms[-1], '지역구분': lp['kind'], '생활인구': v.get('tot'), '주민 대비 배': round(v['tot'] / lp['reg'], 2) if lp.get('reg') and v.get('tot') else None, '남': v.get('m'), '여': v.get('f'),
                                         '연령(20세 미만~70세 이상 7구간)': v.get('age'), '달마다': {m: lp['m'][m].get('tot') for m in ms}, '정의': '주민등록 + 그 달 하루 3시간 넘게 머문 체류인구(통신 추정)'}
        cx = CEN and CEN['gu'].get(gu)
        if cx: G['주거·학력(2020 총조사 · 구)'] = {'일반가구': cx.get('hh'), '자기집%': cx.get('own'), '전세%': cx.get('jeonse'), '월세%': cx.get('wolse'), '4년제 졸업 이상%(25세+)': cx.get('uni4')}
        tx = TAX and TAX['gu'].get(gu)
        if tx: G['소득(국세청 · 구 평균)'] = {'1인당 총급여_만원(' + TAX['years']['wage'] + ')': (tx.get('wage') or [None])[0], '1인당 종합소득_만원(' + TAX['years']['inc'] + ')': (tx.get('inc') or [None])[0]}
        doc = {'schema': 'tg-profile/1', 'gu': gu, 'name': g.get('name'), 'built': time.strftime('%Y-%m-%d'),
               'how_to_read': '행정동마다 한 덩어리 — 주민(주민등록 · 사는 사람) · 머무는 사람(생활인구 · 그 시각 있는 사람 · 서울만) · 이동(교통카드 승하차) · 돈(카드 매출 · 서울 추정매출 / 경기 가공 자료) · 가게 · 집값 · 사고 · 시설 · 치안. 「추정」·「근사」라고 적힌 값은 그렇게 다룬다. 값이 없는 칸은 자료가 없는 것이지 0 이 아니다.',
               'sources': {'주민': '행정안전부 주민등록 인구통계(행정동·연령·성별 · 2026년 9월)', '머무는 사람': '서울시 행정동 생활인구(KT 통신 추정 · 2026년 7월 평일·주말 평균)', '카드 매출(추정)': '서울시 상권분석서비스 추정매출-행정동(' + str(D.get('quarter')) + ' 분기 · 카드사 결제로 추정 · 만원)',
                           '카드 매출(경기)': '경기데이터드림 카드매출_행정동_집계(1~6월 월평균)', '카드 소비(경기 상세)': '경기데이터드림 「카드 소비 데이터」(민간데이터 카드 · 시간대·성별·연령·요일·업종 · 공공누리 2유형 = 상업 이용 금지 · 일부 시만)', '가구·주택·사업체': '통계청 SGIS 집계구(2023 · 집계구 경계 2025 · 동 이름으로 합)', '가게': '소상공인시장진흥공단 상가(상권)정보', '이동': '서울시·경기 교통카드 정류장·역 시간대 승하차(하루 평균)',
                           '교통사고': '도로교통공단 TAAS 2016~2025(개인정보 없음)', '집값': '국토교통부 실거래가(공공데이터포털) · 평당 = 전용면적 기준', '머무는 외국인': '서울시 250M격자 생활인구 장기·단기체류 외국인(2026-09-07~13)', '치안': '경찰청과 그 소속기관 직제 시행규칙 별표2 × 행정동(근사) · 경찰민원24 대표번호',
                           '외국인(구)': '행정안전부 외국인주민 현황 2024 · 법무부 등록외국인 2025', '외국인주민(동)': '행정안전부 2024 지방자치단체 외국인주민 현황(읍면동 · 2024.11.1)', '외국인관광 도시민박': '행정안전부 문화_외국인관광도시민박업(공공데이터포털 15044966 · 2026-10-05 · 영업+휴업)', '외국인 관광숙박': '서울 지방행정인허가 외국인관광 도시민박업·관광숙박업(영업 중)', '생활인구': '통계청·행정안전부 인구감소지역 생활인구(KOSIS DT_1YL12001E·12002E · 시군구 월별 · 인구감소·관심지역 107곳만)', '주거·학력': '통계청 2020 인구주택총조사', '소득': '국세청 국세통계', '경계': '통계청 SGIS 행정동(가공 vuski/admdongkor 2026-07 · CC BY 4.0)'},
               'caution': '주민(사는 사람)·생활인구(머무는 사람)·외국인주민(행안부)·등록외국인(법무부)·체류 외국인(생활인구)은 정의가 서로 달라 더하거나 빼지 않는다 · 시군구 값을 동 주민 수로 나누지 않는다 · 서울 추정매출과 경기 카드 금액은 만든 곳·세는 법이 달라 직접 견주지 않는다 · 개인정보는 담지 않았다',
               'gu_summary': G, 'dong': out}
        pth = os.path.join(R, gu, 'profile.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        g.setdefault('bytes', {})['profile'] = os.path.getsize(pth); total += os.path.getsize(pth); ngu += 1
        print(gu, g.get('name'), len(out), os.path.getsize(pth), flush=True)
    IX['layers']['profile'] = '🤖 AI용 지역 프로필(행정동 덩어리 · 이 지도 자료를 다시 묶음)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('구', ngu, '바이트', total)

if __name__ == '__main__': main(set(sys.argv[1:]))
