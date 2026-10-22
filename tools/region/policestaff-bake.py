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


def dgcsv(n):
    """공공데이터포털 파일(tools/region/dgfile.py 가 받은 07_API키/out/dg/<번호>/x.csv) — utf-8 이 아니면 cp949"""
    import csv, io as _io
    p = os.path.join(KB, '07_API키', 'out', 'dg', str(n), 'x.csv')
    if not os.path.exists(p): return []
    b = open(p, 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return list(csv.reader(_io.StringIO(b.decode(e))))
        except UnicodeDecodeError: pass
    return []


def st_official():
    """경찰서별 공식 파일 — 정원(15092089) · 살인·강도·절도·폭력 발생(15084592) → police-card 경찰서 번호로"""
    PC = json.load(open(os.path.join(ROOT, 'data', 'police-card.json'), encoding='utf-8'))['st']
    SDC = {str(x[0]): x[5] for x in json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8'))['stations']}
    PRE = ['서울', '부산', '대구', '인천', '광주', '대전', '울산', '세종', '경기', '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']
    SDP = {'강원': '강원', '경남': '경상남', '경북': '경상북', '경기': '경기', '전남': '전남', '전북': '전라북', '충남': '충청남', '충북': '충청북'}
    idx = collections.defaultdict(list)
    for sid, v in PC.items(): idx[re.sub('경찰서$', '', v['n'])].append(sid)
    def match(nm, pre=None):
        if re.sub('(경찰)?서$', '', nm.replace(' ', '')) == '인천중부': nm = '인천제물포'   # 2026-07 인천중부 → 제물포·영종 — 그 전 자료는 제물포에(영종 몫 포함)
        nm0 = re.sub('(경찰)?서$', '', nm.replace(' ', ''))
        if nm0 in ('수원중부', '수원남부', '수원서부'): nm = {'수원중부': '수원장안', '수원남부': '수원영통', '수원서부': '수원권선'}[nm0]   # 2025-08-05 수원팔달서 개서와 함께 이름 바뀜(경인일보 2025-08-05) — 그 전 자료는 팔달서가 떨어져 나가기 전 관할의 값
        r9 = match0(nm, pre)
        if r9 and pre and pre in SDP and not SDC.get(r9, '').startswith(SDP[pre]): return None   # 이름만 같은 다른 청 경찰서(강원 고성 ↔ 경남 고성)
        return r9
    def match0(nm, pre=None):
        nm = re.sub('경찰서$', '서', nm.strip())
        b0 = nm.replace(' ', '')
        if b0 in idx and len(idx[b0]) == 1: return idx[b0][0]   # 강서·수서·달서·성서처럼 「서」로 끝나는 이름
        b = re.sub('서$', '', nm.replace(' ', ''))
        if b in idx and len(idx[b]) == 1: return idx[b][0]
        if pre and b.startswith(pre) and b[len(pre):] in idx and len(idx[b[len(pre):]]) == 1: return idx[b[len(pre):]][0]
        for q in ([pre] if pre else []) + PRE:
            c = b[len(q):] if b.startswith(q) else (b if q == pre else None)
            if c and c in idx:
                if len(idx[c]) == 1: return idx[c][0]
                cand = [x for x in idx[c] if SDC.get(x, '').startswith(SDP.get(q, q))]
                if len(cand) == 1: return cand[0]
        return None
    out = collections.defaultdict(dict); miss = []
    A = dgcsv(15092089)
    for r in A[1:]:
        nm = '인천제물포' if r[2] == '인천중부' else r[2]   # 2026-07 인천중부 → 제물포·영종 — 2025 정원은 제물포에 둔다(영종 몫 포함)
        sid = match(nm.replace('경남 ', '경남'), r[1][:2])
        if sid: out[sid]['cop'] = int(r[3].replace(',', '')); out[sid]['cop_y'] = r[0]
        else: miss.append(r[2])
    B = dgcsv(15084592)
    for r in B[1:]:
        sid = match(r[1])
        if not sid: miss.append(r[1]); continue
        out[sid].update({'k_murder': int(r[2].replace(',', '')), 'k_robbery': int(r[3].replace(',', '')), 'k_theft': int(r[4].replace(',', '')), 'k_viol': int(r[5].replace(',', '')), 'k_y': r[0]})
    # 치안고객만족도 관서별(종합·민원·112 = 2025 · 교통·수사 = 2024 파일) — 경찰서 줄은 out 에 · 시도청 줄은 sat_sdc 에
    SAT = [('sat_all', 15064412), ('sat_civ', 15064323), ('sat_112', 15064400), ('sat_trf', 15064404), ('sat_inv', 15064409)]
    SDN = {'광주광역시경찰청': '광주경찰청', '전라남도경찰청': '전남경찰청', '전북특별자치도경찰청': '전라북도경찰청', '강원도경찰청': '강원특별자치도경찰청', '경기남부경찰청': '경기도남부경찰청', '경기북부경찰청': '경기도북부경찰청'}
    sat_sdc = collections.defaultdict(dict); sat_y = {}
    for k, n in SAT:
        T = dgcsv(n)
        if not T: continue
        sat_y[k] = re.search(r'_(\d{4})\d{4}', open(os.path.join(KB, '07_API키', 'out', 'dg', str(n), '_meta.json'), encoding='utf-8').read()).group(1) if os.path.exists(os.path.join(KB, '07_API키', 'out', 'dg', str(n), '_meta.json')) else None
        for r in T[1:]:
            nm = r[0].strip(); v = num(r[1]) if len(r) > 1 else None
            if v is None: continue
            if nm.endswith('경찰청'): sat_sdc[SDN.get(nm, nm)][k] = v; continue
            if not nm.endswith('경찰서'): continue
            sid = match(nm)
            if sid: out[sid][k] = v
            else: miss.append(nm)
    # 관서별 시간대별 음주단속(15128722 · 2025) — 0~23시
    for r in dgcsv(15128722)[1:]:
        sid = match(r[1], re.sub(r'^\d+\.', '', r[0])[:2])
        if not sid: miss.append(r[1]); continue
        a = out[sid].setdefault('dui_hr', [0] * 24); a[int(r[2])] += int(r[3].replace(',', ''))
    # 112 순찰차 — 서울(15114083) · 경기북부(15144083 · 가장 새 줄) · 강원(15125675) · 충남(15144536)
    car = {}
    for r in dgcsv(15114083)[1:]: car[match('서울' + r[1].replace(' ', ''))] = int(r[2])
    T = dgcsv(15144083)
    if T:
        new = max(T[1:], key=lambda r: r[0])
        for nm, v in zip(T[0][1:], new[1:]): car[match(nm, '경기')] = int(v)
    for r in dgcsv(15125675)[1:]:
        if r[1].endswith('청'): continue
        car[match(r[1], '강원')] = int(r[2])
    for r in dgcsv(15144536)[1:]: car[match(r[1], '충남')] = int(r[2])
    for sid, v in car.items():
        if sid: out[sid]['car112'] = v
    # 청 공개 경찰서별 5대 범죄 발생·검거(서울 15054738 · 부산 15036510(발생만) · 인천 15070377 · 경기북부 15086083 · 강원 15107518 · 세종 15127530)
    KN = {'살인': 'murder', '강도': 'robbery', '강간': 'sex', '성범죄': 'sex', '강간강제추행': 'sex', '강간·강제추행': 'sex', '절도': 'theft', '폭력': 'viol'}
    def kn(x): x = re.sub(r'\s|발생|검거', '', x); return KN.get(x) or next((v for k, v in KN.items() if x.startswith(k)), None)
    f5 = collections.defaultdict(lambda: collections.defaultdict(lambda: [None, None])); f5y = {}
    def put(sid, k, i, v, y):
        if sid and k and v not in (None, ''):
            a = f5[sid][k]; a[i] = (a[i] or 0) + int(str(v).replace(',', '')); f5y[sid] = y
    for r in dgcsv(15054738)[1:]: put(match('서울' + r[0].replace(' ', '')), kn(r[1]), 0 if r[2].startswith('발생') else 1, r[3], '2025')
    T = dgcsv(15036510)
    for r in T[1:]:
        if r[2] != '경찰서': continue
        sid = match('부산' + r[1].replace(' ', ''))
        for c, v in zip(T[0][3:], r[3:]): put(sid, kn(c), 0, v, '2025')
    T = dgcsv(15070377)
    for r in T[1:]:
        k = kn(r[0]); i = 0 if '발생' in r[0] else 1
        for c, v in zip(T[0][1:], r[1:]): put(match('인천' + c.replace(' ', '')), k, i, v, '2025')
    T = dgcsv(15086083)
    if T:
        yy = max(r[0] for r in T[1:])
        for r in T[1:]:
            if r[0] != yy or r[2] not in ('발생건수', '검거건수'): continue
            for c, v in zip(T[0][3:], r[3:]): put(match(c.replace(' ', ''), '경기'), kn(r[1]), 0 if r[2] == '발생건수' else 1, v, yy)
    T = dgcsv(15107518)
    for r in T[1:]:
        sid = match(r[0].replace(' ', ''), '강원')
        for c, v in zip(T[0][1:], r[1:]): put(sid, kn(c), 0 if '발생' in c else 1, v, '2025')
    T = dgcsv(15127530)
    if T:
        yy = max(r[0] for r in T[1:])
        for r in T[1:]:
            if r[0] == yy:
                sid = match('세종' + r[1].replace(' ', '')); put(sid, kn(r[2]), 0, r[3], yy); put(sid, kn(r[2]), 1, r[4], yy)
    for sid, v in f5.items(): out[sid]['f5'] = {k: list(x) for k, x in v.items()}; out[sid]['f5_y'] = f5y.get(sid)
    print('5대 범죄(청 공개) 경찰서', len(f5))
    # 112 신고(청이 공개한 경찰서별 · 청마다 접수/출동 기준이 다를 수 있다) — 인천 3081475 · 경남 15006967 · 울산 15007069 · 제주 15007251 · 충남 15007055 · 충북 15039573 · 대구 15065363 · 부산 15067163 · 경북 15007169
    def nn(v):
        try: return int(str(v).replace(',', '').strip())
        except ValueError: return None
    c112 = {}
    def yrows(n, pre, skip=()):
        T = dgcsv(n)
        if not T: return
        last = max(T[1:], key=lambda r: r[0]); y = re.sub(r'\D', '', last[0])[:4]
        for c, v in zip(T[0][1:], last[1:]):
            c = c.replace(' ', '')
            if c in skip or not nn(v): continue
            sid = match(pre + c) if pre else match(c)
            if sid: c112[sid] = [nn(v), y, n]
            else: miss.append('112 ' + c)
    yrows(3081475, '인천'); yrows(15007069, '울산', ('울산청',)); yrows(15007251, '제주'); yrows(15067163, '부산', ('계', '부산청'))
    T = dgcsv(15039573)
    if T:
        last = max(T[1:], key=lambda r: r[0])
        for c, v in zip(T[0][1:], last[1:]):
            sid = match(c.replace(' ', ''), '충북')
            if sid and nn(v): c112[sid] = [nn(v), last[0], 15039573]
    T = dgcsv(15007169)
    if T:
        last = max(T[1:], key=lambda r: r[0])
        for c, v in zip(T[0][1:], last[1:]):
            if c.endswith('청') or not nn(v): continue
            sid = match(c.replace(' ', ''), '경북')
            if sid: c112[sid] = [nn(v), last[0], 15007169]
    T = dgcsv(15006967)
    if T:
        yc = max(range(1, len(T[0])), key=lambda i: T[0][i])
        for r in T[1:]:
            sid = match(r[0].replace(' ', ''), '경남')
            if sid and nn(r[yc]): c112[sid] = [nn(r[yc]), re.sub(r'\D', '', T[0][yc]), 15006967]
    T = dgcsv(15065363)
    if T:
        yy = max(r[0][:4] for r in T[1:] if r[0][:4].isdigit())
        for r in T[1:]:
            if r[0][:4] != yy or '청' in r[0][4:]: continue
            sid = match('대구' + r[0][4:].replace(' ', ''))
            if sid: c112[sid] = [sum(nn(x) or 0 for x in r[1:]), yy, 15065363]
    T = dgcsv(15007055)
    for r in (T or [])[1:]:
        if r[0].endswith('청') or '순찰대' in r[0]: continue
        sid = match(r[0].replace(' ', ''), '충남')
        if sid: c112[sid] = [sum(nn(x) or 0 for x in r[1:]), '2026-06 파일', 15007055]
    for sid, v in c112.items(): out[sid]['call112'] = v
    print('112(청 공개 경찰서별)', len(c112))
    for sid in out: out[sid]['n'] = PC[sid]['n'] if sid in PC else None
    print('경찰서 공식 파일 이음', len(out), '못 이음', sorted(set(miss)), '· 순찰차', sum(1 for k in car if k), '/', len(car))
    return dict(out), dict(sat_sdc), sat_y


def pb112():
    """광주청 경찰서별 지구대·파출소 112 신고 출동 건수(15113437) → police.json pbox 와 이름으로 이음"""
    POL = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8')); out = {}
    for r in dgcsv(15113437)[1:]:
        st = re.sub('서$', '', r[1]); nm = re.sub('(지구대|파출소)$', '', r[2].strip())
        hit = [b for b in POL['pbox'] if b[0] == nm and str(b[2]).replace(' ', '') == st]
        if hit: out['%s|%s' % (hit[0][6], hit[0][0])] = [int(r[4].replace(',', '')), r[3]]
        else: print('지구대 못 이음', r[1], r[2])
    return out


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
    st_off, sat_sdc, sat_y = st_official(); pbx = pb112()
    # 시도청 현원 2005~(15048477) · 서울 경찰서별 경찰관 2011~(15114290) · 시도청 가정폭력 검거·조치(15127380) · 서울 경찰서별 지역경찰 관서(15114084)
    def table(n): T = dgcsv(n); return [T[0], T[1:]] if T else None
    dg = {'sdc_now': table(15048477), 'seoul_cop': table(15114290), 'dv_sdc': table(15127380), 'seoul_box': table(15114084)}
    press2 = json.load(open(os.path.join(ROOT, 'tools', 'region', 'police-press.json'), encoding='utf-8'))   # 기사 원문 대조한 보도 숫자(사람이 고치는 표)
    doc = {'schema': 'tg-police-staff/1', 'made': datetime.date.today().isoformat(),
           'source': '경찰공무원 1인당 담당주민수 = 통계청 e-지방지표 DT_1YL15013(경찰청 · 정원) · 경찰관 수 = 행정안전부 DT_11001N_2013_A051(시군구 · 2020 이 마지막) · 범죄 발생지 = 경찰청 범죄통계 DT_132004_A030 · 시도경찰청 발생·검거 = 경찰청 범죄통계 DT_132004_A003~A020 (KOSIS 국가통계포털) · 경찰서별 정원·강력범죄·시도청 현원·서울 경찰서별 경찰관·지역경찰 관서·가정폭력 = 공공데이터포털 경찰청 파일 15092089·15084592·15048477·15114290·15114084·15127380',
           'fields': 'cop_sido{시도: {해: [경찰 1인당 담당주민, 주민등록인구, 경찰공무원 정원]}} · cop_kind{KOSIS 시도 코드(시군구 줄은 KOSIS 에 값이 없다): {n, sido, y{해: {pop 주민(등록외국인 포함), all 합계, p10k 만 명당, npa 경찰청 소속, hq 지방청 본청, st 경찰서, box 지구대파출소, cg 해경 소속, cg_hq·cg_st·cg_box}}}} · crime_sgg{KOSIS 코드: {n 시군구, sido, y{해: {all 계, strong 강력, theft 절도, viol 폭력, fraud 지능, vice 풍속, drug 마약, traffic 교통}}}} · crime_sdc{시도경찰청: {해: {죄종: [발생, 검거, 검거인원]}}} · sdc_q{시도경찰청: {분기 YYYYQ: [발생, 검거, 검거인원]}}(총계) · nat{proc 처리기간·catch 발생부터 검거까지·clue 수사단서·decide 사법경찰관 결정·hour 발생 시간: {cols, v{죄종: {해: [칸…]}}}} · proc 는 2011~2022 옛 표(범죄자 기준)를 앞에 이음 · press 보도로 알려진 수사관 1인당 사건 접수(공식 통계 아님) · nat_kind{죄종: {해: [발생, 검거, 검거인원]}}(전국 · DT_132004_A001) · st{경찰서 번호: {cop 경찰서 정원, cop_y, k_murder 살인 · k_robbery 강도 · k_theft 절도 · k_viol 폭력 발생, k_y}}(공공데이터포털 15092089·15084592 · 경찰서 이름을 police-card 와 맞춤) · st 에 덧붙임: sat_all 치안고객만족도 종합 · sat_civ 민원 · sat_112 112신고 · sat_trf 교통 · sat_inv 수사(점 · 15064412·15064323·15064400·15064404·15064409 · 해는 sat_y) · dui_hr[0~23시 음주단속 건수](15128722) · car112 112 순찰차 대수(서울·경기북부·강원·충남 · 15114083·15144083·15125675·15144536) · f5{murder 살인·robbery 강도·sex 성범죄·theft 절도·viol 폭력: [발생, 검거]}·f5_y(청이 공개한 경찰서별 5대 범죄 — 서울·부산(발생만)·인천·경기북부·강원·세종) · sat_sdc{시도청: 같은 칸} · pb112{"경찰서 번호|지구대·파출소 이름": [112 출동 건수, 기간]}(광주청 15113437) · dg{sdc_now 시도청 현원 2005~ · seoul_cop 서울 경찰서별 경찰관 2011~ · dv_sdc 시도청 가정폭력 검거·조치 · seoul_box 서울 경찰서별 지구대·파출소·치안센터: [머리, 줄…]}(공공데이터포털 15048477·15114290·15127380·15114084 · 글자 그대로) · press2{src{열쇠: {t, o, d, url}}, items[[갈래, 지표, 단위, src, {칸: 값 | [앞, 뒤]}, 단위(전국·청·서)]]}(tools/region/police-press.json · 기사 원문 대조한 것만) · catalog[[표 ID, 이름, 처음 해, 끝 해]](경찰청 KOSIS 표)',
           'note': ['경찰관 수(소속별)는 2020 이 마지막 공개이고 KOSIS 에는 시도 줄에만 값이 있다 — 경찰서별 인원은 공개 통계에 없다', '1인당 담당주민수는 정원 기준(현원 아님)', '범죄 발생지 = 범죄가 일어난 곳(검거한 경찰서가 아님) · 시는 구로 나누지 않은 곳이 있다(창원·포항 등)', '검거 건수에는 앞 해 발생 사건 검거가 들어 있어 검거율이 100% 를 넘을 수 있다'],
           'cop_sido': {k: dict(sorted(v.items())) for k, v in sido.items()}, 'cop_kind': cop_sgg, 'crime_sgg': crime_sgg, 'crime_sdc': crime_sdc, 'sdc_q': sdc_q, 'nat': natd, 'press': press, 'press2': press2, 'nat_kind': nat_kind, 'st': st_off, 'sat_sdc': sat_sdc, 'sat_y': sat_y, 'pb112': pbx, 'dg': dg, 'catalog': catalog}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'police-staff.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시도', len(sido), '시군구 경찰관', len(cop_sgg), '시군구 범죄', len(crime_sgg), '청', len(crime_sdc))
    print('서울', sido.get('서울특별시', {}).get('2024'), '| 서초 범죄', [v for v in crime_sgg.values() if v['n'] == '서초구'][:1])
    print('서울청', crime_sdc['서울특별시경찰청'].get('2025', {}).get('all'))


if __name__ == '__main__':
    main()
