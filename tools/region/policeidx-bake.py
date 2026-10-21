# -*- coding: utf-8 -*-
# 데이터 압축지도 — 👮 경찰서·시도경찰청 지표판 → data/police-index.json
#   소유자 2026-10-20 「데이터지도는 경찰서별 경찰청별로 데이터가 나와야 해 · 경찰관련 인구대비 소득대비 학생수 대비 통행량 대비 사건사고 등을 숫자로 뽑아줘야」
#   분자(사건·사고 · 해마다 한 번 세는 수)
#     acc  교통사고(TAAS 공개 사고 근사 · 2023~2025 한 해 평균 · data/police-card.json)        — 전국
#     dead 교통사고 사망자(10년 합 ÷ 10 · 같은 파일)                                             — 전국
#     dui  음주운전 적발(2024 · data/dui-catch-st.json · 경찰청 15043308)                       — 전국
#     call 112 신고(서울 = 출동 · 경기북부 = 접수 합 · data/call112.json · 최근 해)             — 서울·경기북부만
#     crime 5대 범죄 발생(2025 · data/police-stats.json crime · 서울청)                          — 서울만
#     enf  교통법규 위반 현장 단속(2024 · data/police-stats.json enf · 서울청)                    — 서울만
#   분모(견줄 것)
#     pop 주민 · emp 종사자 · shop 가게 · frn 외국인주민 · km2 넓이(data/police-card.json)
#     kid 학령인구 만 6~17세(data/dong-kidage · 주민등록 2026-09 · 행정동 → 서)
#     veh 자동차 · vkm 연간 주행거리 · road 표준노드링크 길이(data/acc-rate-police.json)
#     wage 1인당 총급여(만 원/년 · 국세청 연말정산 주소지 · data/gu-tax.json · 시군구 값을 주민 비율로 섞음) — 「소득 수준」(분모가 아니라 견주는 칸)
#   py -3.12 -X utf8 tools/region/policeidx-bake.py
import json, os, re, glob, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = lambda f: json.load(open(os.path.join(ROOT, 'data', f), encoding='utf-8'))


def short(n): return re.sub(r'경찰서$', '', re.sub(r'^서울', '', n))


CRK = ['all', 'strong', 'theft', 'viol', 'fraud', 'drug', 'traffic']
SH = {'서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구', '인천광역시': '인천', '광주광역시': '광주', '대전광역시': '대전', '울산광역시': '울산', '세종특별자치시': '세종', '경기도': '경기도', '강원특별자치도': '강원도', '강원도': '강원도',
      '충청북도': '충청북도', '충청남도': '충청남도', '전북특별자치도': '전라북도', '전라북도': '전라북도', '전라남도': '전라남도', '경상북도': '경상북도', '경상남도': '경상남도', '제주특별자치도': '제주도'}
SDC_SIDO = {'서울특별시경찰청': '서울특별시', '부산광역시경찰청': '부산광역시', '대구광역시경찰청': '대구광역시', '인천광역시경찰청': '인천광역시', '광주경찰청': '광주광역시', '대전광역시경찰청': '대전광역시', '울산광역시경찰청': '울산광역시', '세종특별자치시경찰청': '세종특별자치시',
            '강원특별자치도경찰청': '강원특별자치도', '충청북도경찰청': '충청북도', '충청남도경찰청': '충청남도', '전라북도경찰청': '전북특별자치도', '전남경찰청': '전라남도', '경상북도경찰청': '경상북도', '경상남도경찰청': '경상남도', '제주특별자치도경찰청': '제주특별자치도'}


def crime_units():
    """범죄 발생지(시군구 · 2023~2025 한 해 평균) — accrate-bake 의 묶음 열쇠(시도, 시군구)로"""
    import importlib.util
    sp = importlib.util.spec_from_file_location('ar', os.path.join(ROOT, 'tools', 'region', 'accrate-bake.py')); ar = importlib.util.module_from_spec(sp); sp.loader.exec_module(ar)
    PSF = D('police-staff.json'); U = {}
    for v in PSF['crime_sgg'].values():
        ys = [y for y in v['y'] if v['y'][y].get('all') is not None]
        if not ys: continue
        U[(v['sido'], v['n'])] = {k: sum(v['y'][y].get(k) or 0 for y in ys) / len(ys) for k in CRK}
    G = json.load(open(ar.HJD, encoding='utf-8'))['features']; meta = {}
    for f in G:
        q = f['properties']; meta[str(q.get('adm_cd2') or '')[:8]] = (q['sidonm'], q['sggnm'])
    def key(c):
        if c not in meta: return None
        u = ar.unit(*meta[c]); sd = SH.get(u[0], u[0]); g = u[1]
        if g.startswith('중·동·서구'): return ('인천', ('중구', '동구', '서구'))
        if sd == '세종': return ('세종', ('세종',))
        return (sd, (g,))
    return U, key, PSF



def nid_map():
    """행정동 8자리 → 그 동을 기본으로 맡는 경찰서 수(police.json labels 의 「~」 앞 · 반포 현장 기준 FIELD) — polcard-bake 와 같은 규칙"""
    import importlib.util as _iu
    pol = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8')); out = {}
    try:
        sp = _iu.spec_from_file_location('polcard_bake', os.path.join(ROOT, 'tools', 'region', 'polcard-bake.py')); m = _iu.module_from_spec(sp); sp.loader.exec_module(m); FIELD = m.FIELD
    except Exception:
        FIELD = {}
    for code, li in pol['dong'].items():
        ids = [x for x in str(pol['labels'][li]).split('~')[0].split(',') if x != '']
        out[code[:8]] = len(FIELD[code]) if code in FIELD else max(1, len(ids))
    return out

def main():
    NID = nid_map()
    PC = D('police-card.json')['st']; AR = D('acc-rate-police.json')['st']; POL = D('police.json')['stations']; GT = D('gu-tax.json')['gu']
    SDC = {str(s[0]): s[5] for s in POL}
    KID = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'dong-kidage', '*.json')):
        for c, v in json.load(open(f, encoding='utf-8')).get('dong', {}).items(): KID[c[:8]] = sum(v[1:4])
    DUI = D('dui-catch-st.json'); dy = max(DUI['years']); DU = {k: v.get('n', 0) for k, v in DUI['years'][dy].items()}
    C112 = D('call112.json'); cs = C112['seoul']; cyr = cs['years'][-1]; CALL = {k: v[-1] for k, v in cs['st'].items()}
    gn = C112.get('gg_north') or {}; gny = max(r[0] for r in gn.get('rows', [[0]]))
    for r in gn.get('rows', []):
        if r[0] != gny: continue
        for nm, v in zip(gn['st'], r[2:]): CALL['@' + nm] = CALL.get('@' + nm, 0) + (v or 0)
    PS = D('police-stats.json'); cy = PS.get('crimeYear'); CR = {k: sum(x[0] for x in v.values()) for k, v in (PS.get('crime') or {}).items()}
    EN = {k: (v.get('2024') or {}).get('n') for k, v in (PS.get('enf') or {}).items()}
    out = {}; miss = collections.Counter()
    try: PF = D('police-func.json')
    except Exception: PF = {'st': {}, 'fn': []}
    PFK = [f[0] for f in PF['fn'] if not f[0].startswith('c_')]
    # 집회(2025) — 서울 = 「오늘의 주요집회」 관할서(rally-hist-seoul · 주요 집회만) · 광주·대구 = 청 공개 경찰서별 개최(rally-sdc)
    RY = '2025'; RAL = {}
    try:
        for k, v in D('rally-hist-seoul.json')['st'].items():
            if v.get(RY): RAL['서울' + k + '경찰서'] = v[RY][0]
        for c, x in D('rally-sdc.json')['st'].items():
            for k, v in x.items():
                if v.get(RY): RAL[k if k.startswith(('광주', '대구')) else k] = v[RY][0]
    except Exception:
        pass
    CU, ckey, PSF = crime_units(); upop = collections.Counter(); seen = set()
    for st in PC.values():
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]
            if c in seen: continue
            seen.add(c); k = ckey(c)
            if k: upop[k] += dg[3] or 0
    for sid, st in PC.items():
        n = st['n']; s = short(n); a = AR.get(sid, {})
        kid = 0.0; wsum = wpop = 0.0
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]; w = 1.0 / NID.get(c, 1 + len(dg[4] or [])); kid += KID.get(c, 0) * w
            g = GT.get(c[:5]) or GT.get(c[:4] + '0')
            if g and g.get('wage') and dg[3]: wsum += g['wage'][0] * dg[3] * w; wpop += dg[3] * w
        cr = dict.fromkeys(CRK, 0.0); cok = True; share = collections.Counter()
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]; w = 1.0 / NID.get(c, 1 + len(dg[4] or [])); k = ckey(c); p = (dg[3] or 0) * w
            if not k or not upop[k]: cok = False; continue
            share[k] += p / upop[k]
            for g in k[1]:
                u = CU.get((k[0], g))
                if not u: cok = False; continue
                for x in CRK: cr[x] += u[x] * p / upop[k]
        cexact = 1 if share and all(v > 0.98 for v in share.values()) else 0
        dui = DU.get(n)
        if dui is None and n == '고성경찰서': dui = DU.get(('강원' if '강원' in SDC.get(sid, '') else '경남') + '고성경찰서')
        if dui is None and n == '인천제물포경찰서': dui = DU.get('인천중부경찰서')   # 2026-07 인천중부 → 제물포·영종으로 나뉨 — 2024 인천중부 값을 제물포에 둔다(영종 몫 포함 · 영종은 빈칸)
        if dui is None: miss['dui'] += 1
        call = CALL.get(s) if n.startswith('서울') else CALL.get('@' + s)
        num = {'acc': a.get('acc'), 'dead': round((st.get('acc') or {}).get('dead', 0) / 10, 1) if st.get('acc') else None, 'dui': dui, 'call': call,
               'crime': CR.get(s) if n.startswith('서울') else None, 'enf': EN.get(s) if n.startswith('서울') else None}
        for x in CRK: num['c_' + x] = round(cr[x], 1) if cok and share else None
        den = {'pop': a.get('pop') or st.get('pop'), 'kid': round(kid) or None, 'emp': st.get('emp'), 'shop': st.get('shop'), 'frn': st.get('frn'), 'km2': a.get('km2') or st.get('km2'),
               'road': a.get('road_km'), 'veh': a.get('veh'), 'vkm': a.get('vkm'), 'wage': round(wsum / wpop) if wpop else None}
        so = PSF.get('st', {}).get(sid, {})
        for k in ('k_murder', 'k_robbery', 'k_theft', 'k_viol'): num[k] = so.get(k)
        num['k4'] = sum(so[k] for k in ('k_murder', 'k_robbery', 'k_theft', 'k_viol')) if 'k_viol' in so else None
        den['cop'] = so.get('cop'); den['car'] = so.get('car112')
        f5 = so.get('f5') or {}
        if f5:
            num['g5'] = sum(x[0] or 0 for x in f5.values()); g5c = [x[1] for x in f5.values() if x[1] is not None]
            num['g5c'] = sum(g5c) if len(g5c) == len(f5) else None; den['g5o'] = num['g5'] if num['g5c'] is not None else None
            for k in ('murder', 'robbery', 'sex', 'theft', 'viol'): num['g5_' + k] = (f5.get(k) or [None])[0]
        den['live'] = PF['st'].get(sid, {}).get('live'); den['day'] = PF['st'].get(sid, {}).get('day')
        num['duiT'] = sum(so['dui_hr']) if so.get('dui_hr') else None
        for k in ('sat_all', 'sat_civ', 'sat_112', 'sat_trf', 'sat_inv'): num[k] = so.get(k)
        num['rally'] = RAL.get(n)
        pf = PF['st'].get(sid, {})
        for k in PFK: num['f_' + k] = pf.get(k)   # 기능별 지표(police-func · 동을 서로 묶은 값)
        out[sid] = {'n': n, 'sdc': SDC.get(sid, ''), 'num': num, 'den': den, 'cx': cexact}
    # 시도경찰청 묶음 — 분자·분모는 더하고(없는 서가 하나라도 있으면 그 칸은 빈칸) 소득은 주민 가중 평균
    sd = collections.OrderedDict()
    for sid, v in sorted(out.items(), key=lambda x: x[1]['sdc']):
        g = sd.setdefault(v['sdc'], {'n': v['sdc'], 'cnt': 0, 'num': {}, 'den': {}, '_w': [0.0, 0.0], '_cov': {}})
        g['cnt'] += 1
        for part in ('num', 'den'):
            for k, x in v[part].items():
                if k == 'wage' or k.startswith('sat_'): continue   # 점수는 더하지 않는다 — 청 줄은 청이 낸 값
                if x is None: continue
                g[part][k] = (g[part].get(k) or 0) + x; g['_cov'][part + '.' + k] = g['_cov'].get(part + '.' + k, 0) + 1
        if v['den'].get('wage') and v['den'].get('pop'): g['_w'][0] += v['den']['wage'] * v['den']['pop']; g['_w'][1] += v['den']['pop']
    for g in sd.values():
        g['cov'] = g.pop('_cov')   # 칸마다 값이 있는 서 수(cnt 보다 작으면 일부 서만 더한 합)
        for part in ('num', 'den'):
            for k in list(g[part]):
                if isinstance(g[part][k], float): g[part][k] = round(g[part][k], 1)
        g['den']['wage'] = round(g['_w'][0] / g['_w'][1]) if g['_w'][1] else None; del g['_w']
        # 시도청은 청이 낸 발생·검거(2023~2025 한 해 평균)로 바꿔 넣는다 — 서 몫 어림을 더한 것보다 맞다
        for k, v in (PSF.get('sat_sdc', {}).get(g['n']) or {}).items(): g['num'][k] = v
        cs = PSF['crime_sdc'].get(g['n'])
        if cs:
            ys = sorted(cs)
            for x in CRK:
                vv = [cs[y][x] for y in ys if cs[y].get(x) and cs[y][x][0] is not None]
                if vv: g['num']['c_' + x] = round(sum(a[0] for a in vv) / len(vv), 1)
            vv = [cs[y]['all'] for y in ys if cs[y].get('all')]
            if vv: g['num']['clr'] = round(sum(a[1] for a in vv) / len(vv), 1); g['den']['occ'] = round(sum(a[0] for a in vv) / len(vv), 1)
    doc = {'schema': 'tg-police-index/1', 'made': datetime.date.today().isoformat(),
           'years': {'acc': '2023~2025 한 해 평균', 'dead': '2016~2025 한 해 평균', 'c_': '2023~2025 한 해 평균(범죄 발생지)', 'cop': '2025 경찰서 정원(공공데이터포털 15092089 · 시도청 본청·기동대 등은 안 들어감)', 'k_': '2025 경찰서별 강력범죄 발생(15084592)', 'duiT': '2025 관서별 음주단속(15128722)', 'sat_': '치안고객만족도 — 종합·민원·112 = %s · 교통·수사 = %s' % (PSF.get('sat_y', {}).get('sat_all'), PSF.get('sat_y', {}).get('sat_trf')), 'car': '112 순찰차 — 서울·경기북부·강원·충남 청 공개분', 'g5': '청이 공개한 경찰서별 5대 범죄(서울·부산·인천·경기북부·강원·세종 · 2025 — 경기북부·세종은 파일의 가장 새 해)', 'live': '서울 생활인구(평일 24시간 평균 · 행정동 합)', 'rally': '2025 집회 — 서울 = 「오늘의 주요집회」(주요 집회만) · 광주·대구 = 청 공개 경찰서별 개최', 'dui': dy, 'call': '서울 %s · 경기북부 %s' % (cyr, gny), 'crime': cy, 'enf': 2024, 'kid': '2026-09', 'veh': '2024', 'wage': 'KOSIS 국세청 연말정산 최근 해'},
           'source': '교통사고 = 도로교통공단 TAAS 공개 사고(근사) · 음주운전 적발 = 경찰청 15043308 · 112 = 서울경찰청 15114082·경기북부경찰청 15036132 · 5대 범죄·단속 = 서울경찰청 공개 파일(police-stats) · 주민·종사자·가게·외국인 = 주민등록·SGIS·상가업소·행안부(행정동 합) · 학령인구 = 주민등록 연령별(2026-09) · 자동차·주행거리 = KOSIS 교통안전공단 · 도로 = 표준노드링크 · 소득 = 국세청 연말정산(주소지) · 범죄 발생·검거 = 경찰청 범죄통계(KOSIS DT_132004_A030 시군구 발생지 · A003~A020 시도경찰청) · 경찰관 = 경찰공무원 정원(e-지방지표 DT_1YL15013 · 2024) · 관할 = 직제 시행규칙 별표2',
           'fields': 'st{경찰서 번호: {n, sdc 시도경찰청, num{acc 교통사고/해, dead 사망자/해, dui 음주운전 적발/해, call 112/해, crime 5대 범죄 발생/해, enf 현장 단속/해}, den{pop 주민, kid 만 6~17세, emp 종사자, shop 가게, frn 외국인주민, km2, road 길 ㎞, veh 자동차, vkm 연간 주행 ㎞, wage 1인당 총급여 만 원}}} · sdc{시도경찰청: 같은 꼴(값이 있는 서만 더한 합) + cnt 서 수 + cov{num.acc 등: 값이 있는 서 수}}',
           'note': ['2024 파일의 수원중부·남부·서부는 2025-08-05 수원팔달서 개서 때 바뀐 이름(장안·영통·권선)에 이었다 — 팔달서가 떨어져 나가기 전 관할의 값', '치안고객만족도(sat_*)는 점수(100점) — 비율로 나누지 않고 시도청 줄은 청이 낸 값 · 전국 = 경찰서 평균', '112 순찰차는 서울·경기북부·강원·충남만 공개(다른 청은 빈칸)', '범죄 발생(c_*)은 시군구 값을 그 안 경찰서의 주민 몫으로 나눈 어림(cx=1 이면 서가 시군구를 혼자 맡아 나누지 않음) · 시도청 줄은 청이 낸 값', '경찰관 1명당 = 경찰서 정원(2025 · 공공데이터포털 경찰청 파일) — 시도청 줄은 그 청 경찰서 정원의 합(본청·기동대·부속 기관 인원은 안 들어감)', '행정동 단위 근사 — 두 서 이상이 나눠 맡는 동은 서 수로 똑같이 나눴다', '교통사고는 TAAS 공개 사고를 칸으로 모은 근사 · 경찰 내부 통계와 다르다',
                    '112·5대 범죄·단속은 공개한 청(서울 · 112 는 경기북부도)만 — 다른 청은 빈칸(없다는 뜻이 아니라 공개 안 함)', '주민 대비는 일터·번화가가, 자동차 대비는 다른 곳 차가 오가는 곳이 크게 나온다 — 여러 분모를 같이 본다',
                    '소득 = 시군구 1인당 총급여(주소지)를 서의 주민 비율로 섞은 값 — 그 서 관할 주민의 실제 소득이 아니다'],
           'st': out, 'sdc': sd, 'miss': dict(miss)}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'police-index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('경찰서', len(out), '시도청', len(sd), '못 이은 것', dict(miss), 'dui 해', dy)
    for k in ('dui', 'call', 'crime', 'enf', 'kid', 'wage'):
        part = 'den' if k in ('kid', 'wage') else 'num'
        print(k, sum(1 for v in out.values() if v[part].get(k) is not None), '서')
    print([(g['n'], g['cnt'], g['num'].get('acc'), g['num'].get('dui'), g['den'].get('pop'), g['den'].get('wage')) for g in list(sd.values())[:4]])


if __name__ == '__main__':
    main()
