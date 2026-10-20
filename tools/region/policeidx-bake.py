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


def main():
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
    for sid, st in PC.items():
        n = st['n']; s = short(n); a = AR.get(sid, {})
        kid = 0.0; wsum = wpop = 0.0
        for dg in st.get('dongs', []):
            c = str(dg[0])[:8]; w = 1.0 / (1 + len(dg[4] or [])); kid += KID.get(c, 0) * w
            g = GT.get(c[:5]) or GT.get(c[:4] + '0')
            if g and g.get('wage') and dg[3]: wsum += g['wage'][0] * dg[3] * w; wpop += dg[3] * w
        dui = DU.get(n)
        if dui is None and n == '고성경찰서': dui = DU.get(('강원' if '강원' in SDC.get(sid, '') else '경남') + '고성경찰서')
        if dui is None and n == '인천제물포경찰서': dui = DU.get('인천중부경찰서')   # 2026-07 인천중부 → 제물포·영종으로 나뉨 — 2024 인천중부 값을 제물포에 둔다(영종 몫 포함 · 영종은 빈칸)
        if dui is None: miss['dui'] += 1
        call = CALL.get(s) if n.startswith('서울') else CALL.get('@' + s)
        num = {'acc': a.get('acc'), 'dead': round((st.get('acc') or {}).get('dead', 0) / 10, 1) if st.get('acc') else None, 'dui': dui, 'call': call,
               'crime': CR.get(s) if n.startswith('서울') else None, 'enf': EN.get(s) if n.startswith('서울') else None}
        den = {'pop': a.get('pop') or st.get('pop'), 'kid': round(kid) or None, 'emp': st.get('emp'), 'shop': st.get('shop'), 'frn': st.get('frn'), 'km2': a.get('km2') or st.get('km2'),
               'road': a.get('road_km'), 'veh': a.get('veh'), 'vkm': a.get('vkm'), 'wage': round(wsum / wpop) if wpop else None}
        out[sid] = {'n': n, 'sdc': SDC.get(sid, ''), 'num': num, 'den': den}
    # 시도경찰청 묶음 — 분자·분모는 더하고(없는 서가 하나라도 있으면 그 칸은 빈칸) 소득은 주민 가중 평균
    sd = collections.OrderedDict()
    for sid, v in sorted(out.items(), key=lambda x: x[1]['sdc']):
        g = sd.setdefault(v['sdc'], {'n': v['sdc'], 'cnt': 0, 'num': {}, 'den': {}, '_w': [0.0, 0.0], '_cov': {}})
        g['cnt'] += 1
        for part in ('num', 'den'):
            for k, x in v[part].items():
                if k == 'wage': continue
                if x is None: continue
                g[part][k] = (g[part].get(k) or 0) + x; g['_cov'][part + '.' + k] = g['_cov'].get(part + '.' + k, 0) + 1
        if v['den'].get('wage') and v['den'].get('pop'): g['_w'][0] += v['den']['wage'] * v['den']['pop']; g['_w'][1] += v['den']['pop']
    for g in sd.values():
        g['cov'] = g.pop('_cov')   # 칸마다 값이 있는 서 수(cnt 보다 작으면 일부 서만 더한 합)
        for part in ('num', 'den'):
            for k in list(g[part]):
                if isinstance(g[part][k], float): g[part][k] = round(g[part][k], 1)
        g['den']['wage'] = round(g['_w'][0] / g['_w'][1]) if g['_w'][1] else None; del g['_w']
    doc = {'schema': 'tg-police-index/1', 'made': datetime.date.today().isoformat(),
           'years': {'acc': '2023~2025 한 해 평균', 'dead': '2016~2025 한 해 평균', 'dui': dy, 'call': '서울 %s · 경기북부 %s' % (cyr, gny), 'crime': cy, 'enf': 2024, 'kid': '2026-09', 'veh': '2024', 'wage': 'KOSIS 국세청 연말정산 최근 해'},
           'source': '교통사고 = 도로교통공단 TAAS 공개 사고(근사) · 음주운전 적발 = 경찰청 15043308 · 112 = 서울경찰청 15114082·경기북부경찰청 15036132 · 5대 범죄·단속 = 서울경찰청 공개 파일(police-stats) · 주민·종사자·가게·외국인 = 주민등록·SGIS·상가업소·행안부(행정동 합) · 학령인구 = 주민등록 연령별(2026-09) · 자동차·주행거리 = KOSIS 교통안전공단 · 도로 = 표준노드링크 · 소득 = 국세청 연말정산(주소지) · 관할 = 직제 시행규칙 별표2',
           'fields': 'st{경찰서 번호: {n, sdc 시도경찰청, num{acc 교통사고/해, dead 사망자/해, dui 음주운전 적발/해, call 112/해, crime 5대 범죄 발생/해, enf 현장 단속/해}, den{pop 주민, kid 만 6~17세, emp 종사자, shop 가게, frn 외국인주민, km2, road 길 ㎞, veh 자동차, vkm 연간 주행 ㎞, wage 1인당 총급여 만 원}}} · sdc{시도경찰청: 같은 꼴(값이 있는 서만 더한 합) + cnt 서 수 + cov{num.acc 등: 값이 있는 서 수}}',
           'note': ['행정동 단위 근사 — 두 서 이상이 나눠 맡는 동은 서 수로 똑같이 나눴다', '교통사고는 TAAS 공개 사고를 칸으로 모은 근사 · 경찰 내부 통계와 다르다',
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
