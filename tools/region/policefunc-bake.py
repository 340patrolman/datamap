# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧭 경찰 기능별 치안 수요(동 · 시군구 · 경찰서) → data/police-func.json + data/police-func/<시도 2자리>.json
#   소유자 2026-10-20 「동과 시군구 경찰서 관할로 구분하고 공공데이터를 활용 분석 — 지역경찰 교통 경비 정보 보안 외사 파트로」 + 「여청 경제 수사 형사도」
#   한 점수로 더하지 않는다(ONTOLOGY-3 원칙) — 기능마다 지표를 따로 두고 순위(백분위)는 화면이 셈
#   동 = 행정동(data/r/<시군구>/profile.json · 가게 소분류 data/storecls · 학령 data/dong-kidage) · 시군구 = KOSIS 범죄 발생지와 같은 묶음(일반구는 시로 · accrate-bake 의 unit)
#   경찰서 = police.json 동 → 서(두 서가 나눠 맡는 동은 똑같이 나눔 · polcard-bake 와 같은 규칙 · 반포 현장 기준 FIELD)
#   py -3.12 -X utf8 tools/region/policefunc-bake.py   (polcard-bake · policestaff-bake 뒤 · 그다음 policeidx-bake)
import json, os, glob, collections, datetime, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def mod(name):
    sp = importlib.util.spec_from_file_location(name.replace('-', '_'), os.path.join(ROOT, 'tools', 'region', name + '.py')); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m

# [열쇠, 기능, 이름, 단위, 덧말]
FN = [
    ['bar', '지역경찰', '주점(유흥·생맥주·요리)', '곳', '상가업소 소분류 I21101~I21104'], ['yu', '지역경찰', '유흥주점(일반·무도)', '곳', 'I21101·I21102'],
    ['sing', '지역경찰', '노래방', '곳', 'R10407'], ['gosi', '지역경찰', '고시원·기숙사', '곳', 'I10201'], ['old70', '지역경찰', '70세 이상 주민', '명', '주민등록 연령 · 실종·보호조치'],
    ['kid', '여청', '학생 나이(만 6~17세)', '명', '주민등록 연령별 2026-09'], ['under10', '여청', '어린이(0~9세)', '명', '주민등록 연령'], ['pc', '여청', 'PC방·전자게임장', '곳', 'R10406·R10404 · 청소년 출입'],
    ['motel', '형사', '여관·모텔', '곳', 'I10102'], ['massage', '형사', '마사지·안마', '곳', 'S20802'], ['c_viol', '형사', '폭력범죄 발생', '건/해', 'KOSIS 범죄 발생지(시군구)'], ['c_theft', '형사', '절도 발생', '건/해', '같은 표'], ['c_strong', '형사', '강력범죄 발생', '건/해', '같은 표'],
    ['biz', '수사', '사업체', '곳', 'SGIS 2023 · 경제범죄의 바탕'], ['c_fraud', '수사', '지능범죄(사기 등) 발생', '건/해', 'KOSIS 범죄 발생지'], ['c_drug', '수사', '마약범죄 발생', '건/해', '같은 표'],
    ['acc', '교통', '교통사고', '건/해', 'TAAS 2016~2025 한 해 평균'], ['dead10', '교통', '사망자(10년)', '명', 'TAAS'], ['ped10', '교통', '보행자 피해(10년)', '명', 'TAAS'], ['moto10', '교통', '이륜·원동기 가해(10년)', '건', 'TAAS'], ['c_traffic', '교통', '교통범죄 발생', '건/해', 'KOSIS 범죄 발생지'],
    ['emp', '경비', '종사자(낮 인구)', '명', 'SGIS 2023 · 행사·집회·인파의 바탕'], ['sub', '경비', '지하철 하루 승차', '명', '역 승하차'], ['bus', '경비', '버스 하루 승차', '명', '정류장 승하차'],
    ['shop', '정보', '가게', '곳', '상가업소'], ['biz_i', '정보', '사업체(정보도 같은 값)', '곳', '노동·경제 현장 — 공개 지표가 적다'],
    ['frn', '외사', '외국인주민', '명', '행안부 2024.11'], ['frn_w', '외사', '외국인근로자', '명', '같은 표'], ['frn_m', '외사', '결혼이민자', '명', '같은 표'], ['frn_s', '외사', '유학생', '명', '같은 표'], ['frn_k', '외사', '외국국적동포', '명', '같은 표'], ['minbak', '외사', '외국인관광 도시민박', '곳', '지방행정 인허가'],
]
DEN = [['pop', '주민', '명'], ['km2', '넓이', '㎢'], ['emp', '종사자', '명'], ['live', '생활인구(평일 24시간 평균 · 서울)', '명'], ['day', '주간인구 어림(2020 주간인구지수 × 지금 주민)', '명']]
CLS = {'bar': [108, 109, 110, 111], 'yu': [108, 109], 'sing': [219], 'gosi': [68], 'pc': [216, 218], 'motel': [65], 'massage': [239]}
SIDO = {'11': '서울', '26': '부산', '27': '대구', '28': '인천', '29': '광주', '30': '대전', '31': '울산', '36': '세종', '41': '경기', '42': '강원', '51': '강원', '43': '충북', '44': '충남', '45': '전북', '52': '전북', '46': '전남', '12': '광주·전남', '47': '경북', '48': '경남', '50': '제주'}


def main():
    pidx = mod('policeidx-bake'); CU, ckey, PSF = pidx.crime_units()
    pol = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8'))
    try: FIELD = mod('polcard-bake').FIELD
    except Exception: FIELD = {}
    BYN = {s[1]: s[0] for s in pol['stations']}
    SC = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'storecls', '[0-9][0-9].json')):
        for c, v in json.load(open(f, encoding='utf-8')).get('dong', {}).items():
            cnt = dict((i, n) for i, n in v[2]); SC[c[:8]] = {k: sum(cnt.get(i, 0) for i in ids) for k, ids in CLS.items()}
    KID = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'dong-kidage', '*.json')):
        for c, v in json.load(open(f, encoding='utf-8')).get('dong', {}).items(): KID[c[:8]] = sum(v[1:4])
    DONG = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'r', '[0-9]' * 5, 'profile.json')):
        p = json.load(open(f, encoding='utf-8'))
        for code, d in p['dong'].items():
            jm = d.get('주민') or {}; ag = jm.get('연령10세') or {}; sg = d.get('가구·주택·사업체(SGIS)') or {}; ac = d.get('교통사고(TAAS 2016~2025)') or {}; tr = d.get('이동(대중교통)') or {}
            fr = d.get('외국인주민(이 동 · 행안부 2024.11)') or {}; sc = SC.get(code[:8], {})
            v = {'pop': jm.get('계'), 'km2': d.get('넓이_km2'), 'emp': sg.get('종사자'), 'biz': sg.get('사업체'), 'biz_i': sg.get('사업체'), 'shop': (d.get('가게(상가업소)') or {}).get('계'),
                 'old70': sum(ag.get(k, 0) or 0 for k in ('70~79', '80~89', '90~99', '100~')) if ag else None, 'under10': ag.get('0~9') if ag else None, 'kid': KID.get(code[:8]),
                 'acc': round(ac['계'] / 10, 1) if ac.get('계') is not None else None, 'dead10': ac.get('사망자'), 'ped10': ac.get('보행자 피해'), 'moto10': ac.get('이륜·원동기 가해'),
                 'sub': tr.get('역 하루 승차'), 'bus': tr.get('버스 하루 승차'), 'live': (lambda a: round(sum(a) / len(a)) if a else None)((d.get('머무는 사람(생활인구)') or {}).get('평일 시간대(0~23시)')),
                 'frn': fr.get('합계'), 'frn_w': fr.get('외국인근로자'), 'frn_m': fr.get('결혼이민자'), 'frn_s': fr.get('유학생'), 'frn_k': fr.get('외국국적동포'),
                 'minbak': d.get('외국인관광 도시민박(업소 수 · 영업+휴업)') if isinstance(d.get('외국인관광 도시민박(업소 수 · 영업+휴업)'), (int, float)) else None}
            for k in CLS: v[k] = sc.get(k) if sc else None
            DONG[code[:8]] = {'n': d.get('이름'), 'gu': p['gu'], 'gn': p['name'], 'v': v}
    print('동', len(DONG))
    # 주간인구지수(2020 인구총조사 KOSIS DT_1PA2020 · 시군구 — 일반구는 시) → 동 주민 × 지수 = 주간인구 어림
    KS = {'11': '서울', '21': '부산', '22': '대구', '23': '인천', '24': '광주', '25': '대전', '26': '울산', '29': '세종', '31': '경기도', '32': '강원도', '33': '충청북도', '34': '충청남도', '35': '전라북도', '36': '전라남도', '37': '경상북도', '38': '경상남도', '39': '제주도'}
    DI = collections.defaultdict(lambda: [0, 0]); DN = collections.defaultdict(list)
    try:
        for r in json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'policestaff', 'dayidx2020.json'), encoding='utf-8')):
            c = r['C1']
            if len(c) != 5: continue
            k = (KS.get(c[:2]), '세종' if c[:2] == '29' else r['C1_NM'])
            if r['ITM_ID'] == 'T00': DI[k][0] = float(r['DT'])
            elif r['ITM_ID'] == 'T30': DI[k][1] = float(r['DT'])
        for k in DI: DN[k[1]].append(k)
    except Exception as e:
        print('주간인구 없음', e)
    def dayidx(k):
        if not k: return None
        P = Dd = 0
        for g in k[1]:
            kk = (k[0], g) if (k[0], g) in DI else (DN[g][0] if len(DN.get(g, [])) == 1 else None)
            if not kk or not DI[kk][0]: return None
            P += DI[kk][0]; Dd += DI[kk][1]
        return Dd / P if P else None
    miss_d = 0
    for code, d in DONG.items():
        ix = dayidx(ckey(code)); p0 = d['v'].get('pop')
        d['v']['day'] = round(p0 * ix) if ix and p0 else None
        if ix is None: miss_d += 1
    print('주간인구 지수 못 붙인 동', miss_d)
    keys = [f[0] for f in FN] + ['pop', 'km2', 'live', 'day']
    CK = {'c_viol', 'c_theft', 'c_strong', 'c_fraud', 'c_drug', 'c_traffic'}
    # 시군구 묶음(KOSIS 범죄 발생지와 같은 열쇠)
    SG = {}
    for code, d in DONG.items():
        k = ckey(code)
        if not k: continue
        uk = k[0] + ' ' + '·'.join(k[1]); g = SG.setdefault(uk, {'n': '·'.join(k[1]), 'sido': k[0], 'gus': set(), 'v': collections.Counter(), 'has': collections.Counter(), 'nd': 0})
        g['gus'].add(d['gn']); g['nd'] += 1
        for kk in keys:
            if kk in CK: continue
            x = d['v'].get(kk)
            if x is not None: g['v'][kk] += x; g['has'][kk] += 1
    sgg = {}
    for uk, g in SG.items():
        v = {k: (round(g['v'][k], 1) if g['has'][k] else None) for k in keys if k not in CK}
        crm = collections.Counter()
        for gname in uk.split(' ', 1)[1].split('·'):
            u = CU.get((g['sido'], gname))
            if u:
                for kk in ('strong', 'theft', 'viol', 'fraud', 'drug', 'traffic'): crm['c_' + kk] += u[kk]
        for kk in CK: v[kk] = round(crm[kk], 1) if crm else None
        sgg[uk] = {'n': g['n'], 'sido': g['sido'], 'gus': sorted(g['gus']), 'v': v}
    # 경찰서(동 → 서 · 나눠 맡으면 똑같이)
    ST = collections.defaultdict(lambda: collections.Counter()); SH = collections.defaultdict(collections.Counter)
    for code, li in pol['dong'].items():
        d = DONG.get(code[:8])
        if not d: continue
        lab = str(pol['labels'][li]).split('~'); ids = [int(x) for x in lab[0].split(',') if x != '']
        if code in FIELD: ids = [BYN[n] for n in FIELD[code] if n in BYN]
        for i in ids:
            for kk in keys:
                if kk in CK: continue
                x = d['v'].get(kk)
                if x is not None: ST[i][kk] += x / len(ids); SH[i][kk] += 1
    st = {str(i): {k: round(v[k], 1) for k in v} for i, v in ST.items()}
    # 동 파일(시도 2자리마다)
    by = collections.defaultdict(dict)
    for code, d in DONG.items():
        by[code[:2]][code] = [d['n'], d['gn'], [d['v'].get(k) for k in keys if k not in CK]]
    os.makedirs(os.path.join(ROOT, 'data', 'police-func'), exist_ok=True)
    dk = [k for k in keys if k not in CK]
    for sd, x in by.items():
        json.dump({'schema': 'tg-police-func-dong/1', 'sido': SIDO.get(sd, sd), 'keys': dk, 'fields': 'dong{행정동 8자리: [이름, 시군구, [keys 차례 값…]]}', 'dong': x},
                  open(os.path.join(ROOT, 'data', 'police-func', sd + '.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    doc = {'schema': 'tg-police-func/1', 'made': datetime.date.today().isoformat(),
           'source': '행정동 = 주민등록(행안부) · SGIS 사업체·종사자 2023 · 소상공인시장진흥공단 상가업소 소분류(2026-06) · 주민등록 연령별(2026-09) · TAAS 2016~2025 · 대중교통 승하차 · 행안부 외국인주민(2024.11) · 지방행정 인허가(도시민박) · 범죄 발생지 = 경찰청 범죄통계(KOSIS DT_132004_A030 · 2023~2025 한 해 평균 · 시군구까지만) · 관할 = 직제 시행규칙 별표2',
           'fields': 'fn[[열쇠, 기능, 이름, 단위, 덧말]] · den[[열쇠, 이름, 단위]] · sgg{「시도 시군구」: {n, sido, gus[걸친 구], v{열쇠: 값}}}(시군구 = KOSIS 범죄 발생지와 같은 묶음 · 일반구는 시) · st{경찰서 번호: {열쇠: 값}}(동을 서로 · 나눠 맡는 동은 똑같이 나눔) · 동은 data/police-func/<시도 2자리>.json',
           'note': ['주간인구(day) = 2020 인구총조사 주간인구지수(통근·통학 유입·유출 반영 · 시군구, 일반구는 시)를 동 주민에 곱한 어림 — 같은 시군구 안 동은 같은 지수', '기능마다 지표를 따로 둔다 — 한 점수로 더하지 않는다', '「안보」 기능은 동·시군구 단위 공개 지표가 없다(북한이탈주민 거주 등은 시도 단위·비공개) — 청구 대상', '정보 기능도 공개 지표가 적어 사업체·가게를 바탕으로만 둔다', '범죄 발생은 시군구까지만 공개 — 경찰서·동에는 싣지 않는다(경찰서는 지표표의 어림값을 본다)', '가게 수는 상가업소 등록 기준 — 실제 영업과 다를 수 있다'],
           'fn': FN, 'den': DEN, 'sgg': sgg, 'st': st}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'police-func.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구 묶음', len(sgg), '경찰서', len(st), '동 파일', len(by), '·', os.path.getsize(os.path.join(ROOT, 'data', 'police-func.json')), 'B')
    print([(k, v['v'].get('bar'), v['v'].get('c_viol')) for k, v in list(sgg.items())[:3]])


if __name__ == '__main__':
    main()
