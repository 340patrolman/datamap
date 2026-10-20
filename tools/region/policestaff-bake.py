# -*- coding: utf-8 -*-
# 데이터 압축지도 — 👮 경찰관 수·범죄 발생·검거(KOSIS) → data/police-staff.json
#   소유자 2026-10-20 「범죄발생율 · 1인당 담당 경찰관 수와 실질적인 부분도 다 찾아서 넣자」
#   ① 경찰공무원 1인당 담당주민수(시도) — 통계청 e-지방지표 DT_1YL15013(경찰청 · 정원 기준) 2007~
#   ② 경찰관 수(시군구 · 소속별 — 경찰서 · 지구대파출소 · 지방청 본청 · 해경) — 행정안전부 DT_11001N_2013_A051 2009~2020(마지막 해 2020)
#   ③ 범죄 발생지(시군구 × 죄종) — 경찰청 DT_132004_A030 2023~
#   ④ 범죄 발생·검거(시도경찰청 × 죄종) — 경찰청 DT_132004_A003~A020 2023~
#   받은 응답 = 07_API키/out/policestaff/*.json(있으면 다시 안 부름 · 새 해가 나오면 지우고 다시)
#   py -3.12 -X utf8 tools/region/policestaff-bake.py
import json, os, re, sys, urllib.request, urllib.parse, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'policestaff')
K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['kosis']; K = K if isinstance(K, str) else (K.get('key') or K.get('value'))
CRIME = ['A01', 'A02', 'A03', 'A04', 'A05', 'A06', 'A08', 'A11']   # 계·강력·절도·폭력·지능·풍속·마약·교통
CK = {'A01': 'all', 'A02': 'strong', 'A03': 'theft', 'A04': 'viol', 'A05': 'fraud', 'A06': 'vice', 'A08': 'drug', 'A11': 'traffic'}
SDC_T = {'A003': '서울특별시경찰청', 'A004': '부산광역시경찰청', 'A005': '대구광역시경찰청', 'A006': '인천광역시경찰청', 'A007': '광주경찰청', 'A008': '대전광역시경찰청', 'A009': '울산광역시경찰청', 'A010': '세종특별자치시경찰청',
         'A011': '경기도남부경찰청', 'A012': '경기도북부경찰청', 'A013': '강원특별자치도경찰청', 'A014': '충청북도경찰청', 'A015': '충청남도경찰청', 'A016': '전라북도경찰청', 'A017': '전남경찰청', 'A018': '경상북도경찰청', 'A019': '경상남도경찰청', 'A020': '제주특별자치도경찰청'}


def kosis(name, org, tbl, s, e, **obj):
    p = os.path.join(OUT, name + '.json')
    if os.path.exists(p): return json.load(open(p, encoding='utf-8'))
    q = {'method': 'getList', 'apiKey': K, 'orgId': org, 'tblId': tbl, 'itmId': 'ALL', 'format': 'json', 'jsonVD': 'Y', 'prdSe': 'Y', 'startPrdDe': s, 'endPrdDe': e}
    q.update(obj)
    j = json.loads(urllib.request.urlopen('https://kosis.kr/openapi/Param/statisticsParameterData.do?' + urllib.parse.urlencode(q), timeout=180).read().decode('utf-8'))
    if not isinstance(j, list): raise SystemExit('%s %s' % (name, str(j)[:300]))
    os.makedirs(OUT, exist_ok=True); json.dump(j, open(p, 'w', encoding='utf-8'), ensure_ascii=False); return j


def num(x):
    try: return float(str(x).replace(',', ''))
    except Exception: return None


def main():
    y = datetime.date.today().year
    # ① 시도 담당주민수
    A = kosis('cop_sido', '101', 'DT_1YL15013', '2007', str(y), objL1='ALL')
    sido = collections.defaultdict(dict)
    for r in A:
        k = {'T001': 0, 'T003': 1, 'T002': 2}[r['ITM_ID']]; sido[r['C1_NM']].setdefault(r['PRD_DE'], [None] * 3)[k] = num(r['DT'])
    # ② 시군구 경찰관 수(2009~2020)
    M = json.loads(urllib.request.urlopen('https://kosis.kr/openapi/statisticsData.do?' + urllib.parse.urlencode({'method': 'getMeta', 'type': 'ITM', 'apiKey': K, 'orgId': '110', 'tblId': 'DT_11001N_2013_A051', 'format': 'json', 'jsonVD': 'Y'}), timeout=120).read().decode('utf-8')) if not os.path.exists(os.path.join(OUT, 'cop_sgg2.json')) else []
    B = kosis('cop_sgg2', '110', 'DT_11001N_2013_A051', '2009', '2020', objL1=' '.join(r['ITM_ID'] for r in M if r['OBJ_ID'] == 'DO001'), objL2='ALL')
    BI = {'B001': 'pop', 'B002': 'all', 'B003': 'p10k', 'B006': 'st', 'B007': 'box', 'B005': 'hq', 'B010': 'cg_st', 'B011': 'cg_box', 'B009': 'cg_hq', 'B004': 'npa', 'B008': 'cg'}
    sgg = collections.defaultdict(lambda: collections.defaultdict(dict)); par = {}
    for r in B:
        c = r['C1']; par[c] = r['C1_NM']
        k = BI.get(r['C2'])
        if k: sgg[c][r['PRD_DE']][k] = num(r['DT'])
    cop_sgg = {}
    for c, v in sgg.items():
        sd = par.get(c[:4]) if len(c) > 4 else None   # A0021 → A002 · A01027 → A010
        cop_sgg[c] = {'n': par[c], 'sido': sd, 'y': {k: v[k] for k in sorted(v)}}
    # ③ 시군구 범죄 발생지
    C = kosis('crime_sgg', '132', 'DT_132004_A030', '2023', str(y), objL1=' '.join(CRIME), objL2='ALL')
    cs = collections.defaultdict(lambda: collections.defaultdict(dict)); cn = {}
    for r in C:
        c = r['C2']; cn[c] = r['C2_NM']
        if not c.startswith('B02'): continue
        cs[c][r['PRD_DE']][CK[r['C1']]] = num(r['DT'])
    crime_sgg = {}
    for c, v in cs.items():
        sd = cn.get(c[:5]) if len(c) > 5 else None
        if cn[c] == '세종': sd = '세종'   # KOSIS 가 울산 아래 코드로 둠
        if sd: crime_sgg[c] = {'n': cn[c], 'sido': sd, 'y': {k: v[k] for k in sorted(v)}}
    # ④ 시도경찰청 발생·검거
    crime_sdc = {}
    for t, nm in SDC_T.items():
        D = kosis('crime_' + t, '132', 'DT_132004_' + t, '2023', str(y), objL1=' '.join(CRIME), objL2='B01 B02 B04')
        v = collections.defaultdict(lambda: collections.defaultdict(list))
        for r in D:
            i = {'B01': 0, 'B02': 1, 'B04': 2}[r['C2']]; a = v[r['PRD_DE']][CK[r['C1']]]
            while len(a) < 3: a.append(None)
            a[i] = num(r['DT'])
        crime_sdc[nm] = {k: dict(v[k]) for k in sorted(v)}
    # ⑤ 전국 수사 표(경찰청 범죄통계) — 처리기간 · 검거까지 기간 · 수사단서 · 사법경찰관 결정 · 발생 시간
    TOP = 'A01 A02 A03 A04 A05 A06 A07 A08 A11 A16'
    def nat(name, tbl, s0='2023', o2='ALL'):
        D = kosis(name, '132', tbl, s0, str(y), objL1=TOP, objL2=o2); cols = []; v = collections.defaultdict(lambda: collections.defaultdict(dict))
        for r in D:
            if r['C2_NM'] not in cols: cols.append(r['C2_NM'])
            v[r['C1_NM']][r['PRD_DE']][r['C2_NM']] = num(r['DT'])
        return {'cols': cols, 'v': {k: {yy: [x.get(c) for c in cols] for yy, x in sorted(d.items())} for k, d in v.items()}}
    natd = {'proc': nat('nat_proc', 'DT_132004_A025'), 'catch': nat('nat_catch', 'DT_132004_A024'), 'clue': nat('nat_clue', 'DT_132004_A022'),
            'decide': nat('nat_decide', 'DT_132004_A027', o2='B01 B02 B0201 B020101 B020102 B03 B0301 B0302 B0303 B04'), 'hour': nat('nat_hour', 'DT_132004_A028')}
    # 처리기간 2011~2022(옛 표 · 같은 칸) 앞에 잇기
    O = kosis('nat_proc_old', '132', 'DT_13204_2_N70', '2011', '2022', objL1='00 01 02 03 04 05 06 07 08 11 12', objL2='ALL')
    NM = {'계': '계', '강력범죄': '강력범죄', '절도범죄': '절도범죄', '폭력범죄': '폭력범죄', '지능범죄': '지능범죄', '풍속범죄': '풍속범죄', '특별경제범죄': '특별경제범죄', '마약범죄': '마약범죄', '교통범죄': '교통범죄', '기타범죄': '기타범죄'}
    old = collections.defaultdict(lambda: collections.defaultdict(dict))
    for r in O:
        k = NM.get(r['C1_NM'].strip())
        if k: old[k][r['PRD_DE']][r['C2_NM']] = num(r['DT'])
    pc = natd['proc']['cols']
    for k, d in old.items():
        if k in natd['proc']['v']:
            for yy, x in d.items():
                if yy not in natd['proc']['v'][k]: natd['proc']['v'][k][yy] = [x.get(c) for c in pc]
            natd['proc']['v'][k] = dict(sorted(natd['proc']['v'][k].items()))
    # (옛 표 DT_13204_2011_N212 의 죄종 코드가 새 표와 어긋나 총계가 엉뚱하게 나와 싣지 않는다 — 2026-10-20)
    # ⑥ 시도경찰청 분기 — 발생·검거(가장 새 분기까지)
    QT = {'A0401': '서울특별시경찰청', 'A0402': '부산광역시경찰청', 'A0403': '대구광역시경찰청', 'A0404': '인천광역시경찰청', 'A0405': '광주경찰청', 'A0406': '대전광역시경찰청', 'A0407': '울산광역시경찰청', 'A0408': '세종특별자치시경찰청', 'A0409': '경기도남부경찰청',
          'A0410': '경기도북부경찰청', 'A0411': '강원특별자치도경찰청', 'A0412': '충청북도경찰청', 'A0413': '충청남도경찰청', 'A0414': '전라북도경찰청', 'A0415': '전남경찰청', 'A0416': '경상북도경찰청', 'A0417': '경상남도경찰청', 'A0418': '제주특별자치도경찰청'}
    sdc_q = {}
    for t, nm in QT.items():
        D = kosis('q_' + t, '132', 'DT_13204_' + t, '2023', str(y), objL1='01', prdSe='Q', startPrdDe='20231', endPrdDe=str(y) + '4')
        v = collections.defaultdict(dict)
        for r in D: v[r['PRD_DE']][r['ITM_ID']] = num(r['DT'])
        sdc_q[nm] = {k: [x.get('T001'), x.get('T002'), x.get('T004')] for k, x in sorted(v.items())}
    # ⑦ 경찰청이 KOSIS 에 올린 표 목록(찾아 둔 것)
    cat = json.load(open(os.path.join(OUT, 'kosis132_search.json'), encoding='utf-8')) if os.path.exists(os.path.join(OUT, 'kosis132_search.json')) else {}
    catalog = [[k, v[0], v[1], v[2]] for k, v in sorted(cat.items())]
    press = {'src': '한국경제 2026-06-13 「수사 마비될 판…업무 폭탄에 경찰 1700명 줄퇴사」 — 경찰청이 송석준 의원실(국회 법사위)에 낸 자료', 'url': 'https://www.hankyung.com/article/2026061222427',
             'per_inv': {'2020': 108.4, '2021': 100.8, '2022': 101.8, '2023': 110.4, '2024': 127.7, '2025': 133.8},
             'per_inv_sdc_2025': {'경기도남부경찰청': 154.1, '제주특별자치도경찰청': 153.9, '경기도북부경찰청': 152.8, '충청남도경찰청': 150.9, '광주경찰청': 150.4, '전라북도경찰청': 108.7},
             'quit': {'2021': 265, '2022': 338, '2023': 304, '2024': 373, '2025': 410, '2026(1~5월)': 75},
             'note': '경찰서 실수사관 1인당 한 해 사건 접수 건수 · 기사에 나온 청만(나머지 12청은 기사에 없음) · 보유(미처리) 건수·평균 처리일수는 공개 통계에 없다'}
    # ⑧ 경찰청(전국) 죄종마다 발생·검거 — DT_132004_A001(전국 — A002 는 경찰청 본청 자체 사건이라 쓰지 않는다) · 이름으로 고른 죄종
    MK = json.loads(urllib.request.urlopen('https://kosis.kr/openapi/statisticsData.do?' + urllib.parse.urlencode({'method': 'getMeta', 'type': 'ITM', 'apiKey': K, 'orgId': '132', 'tblId': 'DT_132004_A001', 'format': 'json', 'jsonVD': 'Y'}), timeout=120).read().decode('utf-8')) if not os.path.exists(os.path.join(OUT, 'nat_kind.json')) else []
    WANT = ['총계', '강력범죄', '살인기수', '강도', '강간', '강제추행', '절도범죄', '폭력범죄', '상해', '폭행', '지능범죄', '사기', '컴퓨터등사용사기', '횡령', '배임', '풍속범죄', '마약범죄', '교통범죄', '도로교통법', '특가법(위험운전치사상)', '교통사고처리특례법']
    ids = []
    for r in MK:
        if r['OBJ_ID'] == 'A' and r['ITM_NM'] in WANT and len(r['ITM_ID']) <= 5 and r['ITM_ID'] not in ids: ids.append(r['ITM_ID'])
    NK = kosis('nat_kind', '132', 'DT_132004_A001', '2023', str(y), objL1=' '.join(ids) or 'A01', objL2='B01 B02 B04')
    nk = collections.defaultdict(lambda: collections.defaultdict(lambda: [None, None, None]))
    for r in NK: nk[r['C1_NM']][r['PRD_DE']][{'B01': 0, 'B02': 1, 'B04': 2}[r['C2']]] = num(r['DT'])
    nat_kind = {k: dict(sorted(v.items())) for k, v in nk.items()}
    press2 = json.load(open(os.path.join(ROOT, 'tools', 'region', 'police-press.json'), encoding='utf-8'))   # 기사 원문 대조한 보도 숫자(사람이 고치는 표)
    doc = {'schema': 'tg-police-staff/1', 'made': datetime.date.today().isoformat(),
           'source': '경찰공무원 1인당 담당주민수 = 통계청 e-지방지표 DT_1YL15013(경찰청 · 정원) · 경찰관 수 = 행정안전부 DT_11001N_2013_A051(시군구 · 2020 이 마지막) · 범죄 발생지 = 경찰청 범죄통계 DT_132004_A030 · 시도경찰청 발생·검거 = 경찰청 범죄통계 DT_132004_A003~A020 (KOSIS 국가통계포털)',
           'fields': 'cop_sido{시도: {해: [경찰 1인당 담당주민, 주민등록인구, 경찰공무원 정원]}} · cop_kind{KOSIS 시도 코드(시군구 줄은 KOSIS 에 값이 없다): {n, sido, y{해: {pop 주민(등록외국인 포함), all 합계, p10k 만 명당, npa 경찰청 소속, hq 지방청 본청, st 경찰서, box 지구대파출소, cg 해경 소속, cg_hq·cg_st·cg_box}}}} · crime_sgg{KOSIS 코드: {n 시군구, sido, y{해: {all 계, strong 강력, theft 절도, viol 폭력, fraud 지능, vice 풍속, drug 마약, traffic 교통}}}} · crime_sdc{시도경찰청: {해: {죄종: [발생, 검거, 검거인원]}}} · sdc_q{시도경찰청: {분기 YYYYQ: [발생, 검거, 검거인원]}}(총계) · nat{proc 처리기간·catch 발생부터 검거까지·clue 수사단서·decide 사법경찰관 결정·hour 발생 시간: {cols, v{죄종: {해: [칸…]}}}} · proc 는 2011~2022 옛 표(범죄자 기준)를 앞에 이음 · press 보도로 알려진 수사관 1인당 사건 접수(공식 통계 아님) · nat_kind{죄종: {해: [발생, 검거, 검거인원]}}(전국 · DT_132004_A001) · press2{src{열쇠: {t, o, d, url}}, items[[갈래, 지표, 단위, src, {칸: 값 | [앞, 뒤]}, 단위(전국·청·서)]]}(tools/region/police-press.json · 기사 원문 대조한 것만) · catalog[[표 ID, 이름, 처음 해, 끝 해]](경찰청 KOSIS 표)',
           'note': ['경찰관 수(소속별)는 2020 이 마지막 공개이고 KOSIS 에는 시도 줄에만 값이 있다 — 경찰서별 인원은 공개 통계에 없다', '1인당 담당주민수는 정원 기준(현원 아님)', '범죄 발생지 = 범죄가 일어난 곳(검거한 경찰서가 아님) · 시는 구로 나누지 않은 곳이 있다(창원·포항 등)', '검거 건수에는 앞 해 발생 사건 검거가 들어 있어 검거율이 100% 를 넘을 수 있다'],
           'cop_sido': {k: dict(sorted(v.items())) for k, v in sido.items()}, 'cop_kind': cop_sgg, 'crime_sgg': crime_sgg, 'crime_sdc': crime_sdc, 'sdc_q': sdc_q, 'nat': natd, 'press': press, 'press2': press2, 'nat_kind': nat_kind, 'catalog': catalog}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'police-staff.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시도', len(sido), '시군구 경찰관', len(cop_sgg), '시군구 범죄', len(crime_sgg), '청', len(crime_sdc))
    print('서울', sido.get('서울특별시', {}).get('2024'), '| 서초 범죄', [v for v in crime_sgg.values() if v['n'] == '서초구'][:1])
    print('서울청', crime_sdc['서울특별시경찰청'].get('2025', {}).get('all'))


if __name__ == '__main__':
    main()
