# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧒 행정동 학령인구(만 6~11 · 12~14 · 15~17세) → data/dong-kidage/<시도 코드>.json
#   소유자 2026-10-12 「학군별 지역별」 → 통학구역 안에 사는 아이 수(어림)와 학교 학생 수를 나란히 보려면 동마다 1세 단위 인구가 있어야 한다(통계청 KOSIS 의 읍면동 자료는 5세 단위뿐)
#   원자료: 행정안전부 주민등록 인구통계(jumin.mois.go.kr) 「연령별 인구현황」 — 읍면동 · 1세 단위 · 달마다. 화면의 CSV 내려받기(downloadCsvAge.do)에 시군구마다 한 번
#     POST sltOrgType=2 · sltOrgLvl1=<시도 10자리> · sltOrgLvl2=<시군구 10자리> · sltArgTypes=1 · sltArgTypeA=6 · sltArgTypeB=17 · searchYear/Month Start=End → 07_API키/out/dongkid/<연월>/<시군구>.csv
#   나이는 주민등록의 만 나이다 — 학년과 딱 맞지 않는다(초 = 만 6~11 · 중 = 12~14 · 고 = 15~17 로 어림)
#   py -3.12 -X utf8 tools/region/dongkid-bake.py [연월 202609] [시도 코드…]
import csv, io, json, os, sys, time, datetime, urllib.request, urllib.parse, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dongkid')
def main(ym, sidos):
    gus = sorted(g for g in json.load(open(os.path.join(ROOT, 'data', 'ptax-dong.json'), encoding='utf-8'))['gu'] if g[:2] in sidos); d = os.path.join(KB, ym); os.makedirs(d, exist_ok=True)
    cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); H = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://jumin.mois.go.kr/ageStatMonth.do'}; op.open(urllib.request.Request('https://jumin.mois.go.kr/ageStatMonth.do', headers=H), timeout=60).read()
    OUT = {sd: {} for sd in sidos}; bad = []
    for g in gus:
        p = os.path.join(d, g + '.csv')
        if not os.path.exists(p):
            q = dict(sltOrgType='2', sltOrgLvl1=g[:2] + '00000000', sltOrgLvl2=g + '00000', sltUndefType='', nowYear=ym[:4], searchYearMonth='month', searchYearStart=ym[:4], searchMonthStart=ym[4:], searchYearEnd=ym[:4], searchMonthEnd=ym[4:], gender='gender', sltArgTypes='1', sltArgTypeA='6', sltArgTypeB='17', category='month', sum='sum', sltOrderType='1', sltOrderValue='ASC', xlsStats='1')
            try: b = op.open(urllib.request.Request('https://jumin.mois.go.kr/downloadCsvAge.do', data=urllib.parse.urlencode(q).encode(), headers=H), timeout=90).read()
            except Exception as e: bad.append(g); continue
            if b[:3] != b'\xef\xbb\xbf' and b'"' not in b[:5]: bad.append(g); continue
            open(p, 'wb').write(b); time.sleep(0.2)
        b = open(p, 'rb').read()
        for e in ('utf-8-sig', 'cp949'):
            try: t = b.decode(e); break
            except Exception: t = None
        n = 0
        for r in list(csv.reader(io.StringIO(t or '')))[1:]:
            if len(r) < 15: continue
            code = r[0][r[0].rfind('(') + 1:r[0].rfind(')')]
            if len(code) != 10 or code.endswith('00000'): continue
            v = [int(x.replace(',', '') or 0) for x in r[3:15]]; nm = r[0][:r[0].rfind('(')].split()[-1]
            OUT[g[:2]][code[:8]] = [nm, sum(v[0:6]), sum(v[6:9]), sum(v[9:12])]; n += 1
        if not n: bad.append(g)
    os.makedirs(os.path.join(ROOT, 'data', 'dong-kidage'), exist_ok=True)
    for sd in sidos:
        doc = {'schema': 'tg-dong-kidage/1', 'made': datetime.date.today().isoformat(), 'sido': sd, 'month': ym,
               'source': '행정안전부 주민등록 인구통계(jumin.mois.go.kr) 연령별 인구현황 — 읍면동 · 1세 단위 · %s-%s' % (ym[:4], ym[4:]),
               'note': ['주민등록의 **만 나이**로 센 사람 수다 — 초 = 만 6~11 · 중 = 12~14 · 고 = 15~17 로 어림한 것이라 학년과 딱 맞지 않는다(1~2월생·조기입학·유예)',
                        '그 동에 **주민등록이 된** 아이다 — 그 동의 학교에 다니는 아이가 아니다(사립·국립초 · 학구 밖 전입학 · 특목·자사고 · 주소만 둔 경우)',
                        '통학구역으로 나눌 때는 school-zone 의 넓이 비율을 쓴 **어림**이다 — 아파트가 한쪽에 몰린 동에서는 크게 어긋난다. 학교 학생 수와의 차이를 위장전입으로 단정하지 않는다',
                        '동 코드는 행정안전부 행정기관코드 앞 8자리 — 통계청 SGIS 의 행정동 코드와 거의 같으나 새로 갈라진 동은 다를 수 있다'],
               'fields': {'dong': '{행정동 8자리: [동 이름, 만 6~11세, 만 12~14세, 만 15~17세]}'}, 'dong': OUT[sd]}
        p = os.path.join(ROOT, 'data', 'dong-kidage', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        print(sd, '동', len(OUT[sd]), '바이트', os.path.getsize(p), '합', [sum(v[i] for v in OUT[sd].values()) for i in (1, 2, 3)])
    print('못 받은 시군구', bad); print({k: v for k, v in OUT.get('11', {}).items() if k.startswith('11650')})
if __name__ == '__main__':
    a = sys.argv[1:]; ym = a[0] if a and len(a[0]) == 6 else '202609'; main(ym, [x for x in a if len(x) == 2] or ['11', '41', '28'])
