# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚶 가출·실종 신고(시도경찰청 · 해마다) + 인구 10만 명당 → data/runaway-sido.json
#   소유자 2026-10-19 「가출비율을 알 수 있을까? 시군구별로 만들면 좋겠다」 → 시군구·경찰서 단위는 공개 자료가 없다(공공데이터포털·KOSIS·경찰청 통계 확인)
#   → 「정보공개청구(경찰서별) + 시도 단위 먼저」(소유자 고름) · 청구 문안 = 07_API키/정보공개청구_가출인_경찰서별_20261019.md
#   원자료(공공데이터포털 파일데이터 · tools/region/dgfile.py 로 07_API키/out/dg/<번호>/x.csv):
#     전국 15129413 · 울산 15007070 · 대구 3077700 · 강원 15070195 · 부산 15081164 · 전남 15078056 · 전북 15040604 · 경북 15007170 · 제주 15135001 · 충남 15036166 · 광주 15102224 · 충북 15086168
#     안 내는 곳(2026-10-19 「가출인」으로 찾아봄): 서울 · 인천 · 대전 · 세종 · 경기남부 · 경기북부 · 경남 → 그해 열한 청이 다 있으면 「전국 − 열한 청 = 일곱 청 합」만 낸다
#   인구: 행정안전부 주민등록 인구통계(jumin.mois.go.kr 연령별 인구현황 · 그해 12월 · 시도 총인구 · 만 0~17세) — 캐시 07_API키/out/runaway/pop_<해>_<시도 코드>.csv
#   비율: 가출인(18세 이상) ÷ 18세 이상 인구 · 18세 미만 아동 ÷ 0~17세 인구 · 치매·장애는 인구 전체 — 모두 10만 명당
#   py -3.12 -X utf8 tools/region/runaway-bake.py
import csv, io, json, os, re, time, datetime, urllib.request, urllib.parse, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키', 'out')
SRC = [('전국', '15129413', None), ('울산', '15007070', ['31']), ('대구', '3077700', ['27']), ('강원', '15070195', ['51', '42']), ('부산', '15081164', ['26']), ('전남', '15078056', ['46']),
       ('전북', '15040604', ['52', '45']), ('경북', '15007170', ['47']), ('제주', '15135001', ['50']), ('충남', '15036166', ['44']), ('광주', '15102224', ['29']), ('충북', '15086168', ['43'])]
NONE = ['서울', '인천', '대전', '세종', '경기남부', '경기북부', '경남']
NOTE = {'전남': '2016~2019 값은 가출인이 수십~백여 건뿐이라 집계 방식이 달랐던 것으로 보인다(원자료 그대로 · 비율은 2020년부터만 낸다)',
        '경북': '「발생·발견」 칸 — 다른 청의 「접수·해제」와 같은 뜻으로 보고 견준다(미해제 칸 없음) · 원자료 설명의 「경찰서 단위」는 파일에 없다',
        '대구': '접수·미해제만(해제 칸 없음)', '충남': '접수만 · 2020~2024', '울산': '2019~2021 해제 칸이 비어 있다', '제주': '2020~2021 해제 칸이 0(원자료)'}
YEARS = list(range(2016, 2026))


def read(pk):
    b = open(os.path.join(KB, 'dg', pk, 'x.csv'), 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: t = b.decode(e); break
        except Exception: t = None
    R = list(csv.reader(io.StringIO(t)))
    H = [h.replace(' ', '').replace('_', '') for h in R[0]]
    def kind(h):
        g = 'run' if '가출' in h else 'dem' if '치매' in h else 'dis' if ('지적' in h or '장애' in h) else 'kid' if ('18세미만' in h or '아동' in h) else None
        k = 'open' if '미해제' in h else 'found' if ('해제' in h or '발견' in h) else 'rcv' if ('접수' in h or '발생' in h) else 'rcv'
        return (g, k) if g else None
    cols = [kind(h) for h in H]; out = {}
    for r in R[1:]:
        if not r or not re.match(r'^\d{4}$', r[0].strip()): continue
        y = int(r[0]); d = out.setdefault(y, {})
        for c, v in zip(cols[1:], r[1:]):
            if c is None or v.strip() == '': continue
            d.setdefault(c[0], {})[c[1]] = int(v.replace(',', ''))
    return out


def pop(year, codes):
    d = os.path.join(KB, 'runaway'); os.makedirs(d, exist_ok=True)
    for code in codes:
        p = os.path.join(d, 'pop_%d_%s.csv' % (year, code))
        if not os.path.exists(p):
            cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://jumin.mois.go.kr/ageStatMonth.do'}
            op.open(urllib.request.Request('https://jumin.mois.go.kr/ageStatMonth.do', headers=H), timeout=60).read()
            ym = '%d12' % year
            q = dict(sltOrgType='2', sltOrgLvl1=code + '00000000', sltOrgLvl2='A', sltUndefType='', nowYear=ym[:4], searchYearMonth='month', searchYearStart=ym[:4], searchMonthStart=ym[4:], searchYearEnd=ym[:4], searchMonthEnd=ym[4:],
                     gender='gender', sltArgTypes='1', sltArgTypeA='0', sltArgTypeB='17', category='month', sum='sum', sltOrderType='1', sltOrderValue='ASC', xlsStats='1')
            try: b = op.open(urllib.request.Request('https://jumin.mois.go.kr/downloadCsvAge.do', data=urllib.parse.urlencode(q).encode(), headers=H), timeout=90).read()
            except Exception: continue
            open(p, 'wb').write(b); time.sleep(0.3)
        b = open(p, 'rb').read()
        for e in ('utf-8-sig', 'cp949'):
            try: t = b.decode(e); break
            except Exception: t = None
        rows = list(csv.reader(io.StringIO(t or '')))
        if len(rows) > 1 and len(rows[1]) > 2 and rows[1][1].strip():
            tot, u18 = int(rows[1][1].replace(',', '')), int(rows[1][2].replace(',', ''))
            if tot > 0: return [tot, u18, rows[1][0].split('(')[0].strip()]
    return None


def main():
    data, popd = {}, {}
    for nm, pk, codes in SRC:
        data[nm] = read(pk)
        if codes:
            popd[nm] = {y: pop(y, codes) for y in YEARS if y in data[nm]}
    popd['전국'] = {}   # 전국 인구 = 열일곱 시도 합(같은 달 · 같은 곳에서 받은 값)
    for y in YEARS:
        if y in data['전국']:
            s = 0; ok = True
            for code_set in (['11'], ['26'], ['27'], ['28'], ['29'], ['30'], ['31'], ['36'], ['41'], ['51', '42'], ['43'], ['44'], ['52', '45'], ['46'], ['47'], ['48'], ['50']):
                v = pop(y, code_set)
                if not v: ok = False; break
                s = [s[0] + v[0], s[1] + v[1]] if s else [v[0], v[1]]
            popd['전국'][y] = [s[0], s[1], '전국(열일곱 시도 합)'] if ok else None
    rate = lambda n, d: round(n / d * 1e5, 1) if n is not None and d else None
    out = {}
    for nm, _, _ in SRC:
        rows = []
        for y in sorted(data[nm]):
            v = data[nm][y]; P = (popd.get(nm) or {}).get(y)
            g = lambda a, k: (v.get(a) or {}).get(k)
            row = {'y': y, 'run': [g('run', 'rcv'), g('run', 'found'), g('run', 'open')], 'kid': [g('kid', 'rcv'), g('kid', 'found'), g('kid', 'open')],
                   'dis': [g('dis', 'rcv'), g('dis', 'found'), g('dis', 'open')], 'dem': [g('dem', 'rcv'), g('dem', 'found'), g('dem', 'open')]}
            if P:
                row['pop'] = [P[0], P[1]]
                if not (nm == '전남' and y < 2020):
                    row['r_run'] = rate(g('run', 'rcv'), P[0] - P[1]); row['r_kid'] = rate(g('kid', 'rcv'), P[1])
                    row['r_all'] = rate(sum(x for x in (g('run', 'rcv'), g('kid', 'rcv'), g('dis', 'rcv'), g('dem', 'rcv')) if x is not None), P[0])
            rows.append(row)
        out[nm] = rows
    rest = []
    for y in YEARS:
        have = [nm for nm, _, c in SRC if c and y in data[nm] and (data[nm][y].get('run') or {}).get('rcv') is not None]
        if len(have) == len(SRC) - 1 and y in data['전국'] and popd['전국'].get(y):
            n = data['전국'][y]['run']['rcv'] - sum(data[nm][y]['run']['rcv'] for nm in have)
            p = popd['전국'][y]; ps = [p[0] - sum(popd[nm][y][0] for nm in have), p[1] - sum(popd[nm][y][1] for nm in have)]
            rest.append({'y': y, 'run': n, 'pop': ps, 'r_run': rate(n, ps[0] - ps[1])})
    doc = {'schema': 'tg-runaway-sido/1', 'made': datetime.date.today().isoformat(),
           'source': '공공데이터포털 경찰청·시도경찰청 「연도별 실종아동등 가출인 접수 및 해제현황」 등 열두 파일(' + ' · '.join('%s %s' % (nm, pk) for nm, pk, _ in SRC) + ') · 인구 = 행정안전부 주민등록 인구통계 연령별 인구현황(그해 12월)',
           'fields': 'sido{시도경찰청: [{y 해, run 가출인(18세 이상) [접수, 해제, 미해제], kid 18세 미만 아동 [같은 꼴], dis 지적·자폐성·정신장애인, dem 치매환자, pop [총인구, 0~17세], r_run 가출인 ÷ 18세 이상 인구 × 10만, r_kid 아동 ÷ 0~17세 × 10만, r_all 넷 합 ÷ 총인구 × 10만}]} · rest[일곱 청(' + '·'.join(NONE) + ') 합 = 전국 − 열한 청 · 그해 열한 청이 다 있을 때만] · none[안 내는 청] · note{청: 원자료 주의}',
           'note': ['**시군구·경찰서 단위는 공개 자료가 없다** — 시도경찰청 단위만(정보공개청구로 경찰서별을 받으면 시군구로 바꾼다)',
                    '「가출인」= 18세 이상 실종 신고(자발적 가출 · 연락 두절 · 자살 의심 등이 모두 든다) — 범죄나 위험의 크기가 아니다',
                    '접수 건수에는 지난해 발생 건의 올해 접수가 들 수 있고, 한 사람이 여러 번 신고될 수 있다(원자료 설명)',
                    '경기는 남부·북부 두 청이 모두 안 내 경기도 값이 없다'],
           'sido': out, 'rest': rest, 'none': NONE, 'note_by': NOTE}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'runaway-sido.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    for nm in out:
        L = [r for r in out[nm] if r.get('r_run') is not None]
        print(nm, ' '.join('%d:%s' % (r['y'], r['r_run']) for r in L[-5:]))
    print('일곱 청 합', [(r['y'], r['r_run']) for r in rest])


if __name__ == '__main__':
    main()
