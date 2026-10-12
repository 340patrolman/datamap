# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🎒 동마다 「어떤 학원이 몇 개」 → data/neis-course/<시도 코드>.json
#   소유자 2026-10-13 「동별로 학원 어떤 학원이 몇개있는지 넣어줘」 → neis-dong.json 은 갈래 여덟뿐이라, 교육청에 등록한 **교습과정**(보습·음악·미술·실용외국어·독서실·이미용·간호조무사 …)마다 세고,
#     가장 많은 「보습」은 과목(수학·영어·국어·과학·사회·논술·코딩)과 대상(초·중·고)으로, 「음악」은 악기(피아노·현악·관악·성악·기타·드럼)로 한 번 더 가른다
#   원자료: 교육부 NEIS 교육정보 개방 포털 「학원교습소정보」(acaInsTiInfo) — tools/region/neis-fetch.py → 07_API키/out/neis/aca_<교육청>.json(전국 138,524곳 · 2026-10-13 다시 받음)
#   동에 붙이는 법 = neis-bake.py 와 똑같다(그 파일의 match 를 그대로 가져다 쓴다 — 주소의 읍·면·법정동 → 행정동 · 한 법정동이 여러 행정동에 걸치면 넓이 비율로 나눠 소수로 센다)
#   ⚠ 과목·대상·악기는 **학원 이름과** 학원이 적어 낸 「교습과목 목록」 글에서 낱말을 찾은 것이다(목록에 과목을 적은 곳은 13~22% 뿐이고 이름에는 61~74% 가 과목 낱말을 넣는다 · 2026-10-13 서울·경기·부산 실측) — 한 학원이 여러 과목을 적으면 과목마다 한 번씩 센다(합이 학원 수보다 크다) · 목록을 안 적은 학원은 과목을 모른다
#   학원 이름·전화는 싣지 않는다(수만 센다)
#   py -3.12 -X utf8 tools/region/neiscourse-bake.py
import json, os, re, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'neis')
src = open(os.path.join(ROOT, 'tools', 'region', 'neis-bake.py'), encoding='utf-8').read(); NS = {'__file__': os.path.join(ROOT, 'tools', 'region', 'neis-bake.py')}; exec(src[:src.index('def fee(t):')], NS); match = NS['match']
SUBJ = [('수학', r'수학|수리|연산|산수|주산|매쓰|매스|[Mm][Aa][Tt][Hh]'), ('영어', r'영어|영문|[Ee][Nn][Gg][Ll][Ii][Ss][Hh]|잉글리|파닉스|토플|토익|텝스|어학원'), ('국어', r'국어|언어|문학|독해|한글'), ('과학', r'과학|물리|화학|생물|지구과학|생명과학'), ('사회·역사', r'사회|역사|한국사|세계사|지리|윤리|경제'),
        ('논술·독서', r'논술|독서|토론|글쓰기|작문'), ('코딩·컴퓨터', r'코딩|컴퓨터|프로그래밍|소프트웨어|SW|파이썬|로봇'), ('한자·제2외국어', r'한자|한문|중국어|일본어|일어|불어|독일어|스페인어')]
LEVEL = [('유아', r'유아|유치|미취학|5세|6세|7세'), ('초등', r'초등|초[1-6]|초\d|초저|초고|아동'), ('중등', r'중등|중학|중[1-3]|중\d'), ('고등', r'고등|고[1-3]|고\d|수능|입시|재수|내신'), ('성인', r'성인|일반인|직장인|대학생')]
MUSIC = [('피아노', r'피아노|건반'), ('현악(바이올린·첼로 등)', r'바이올린|첼로|비올라|현악|더블베이스|콘트라베이스'), ('관악(플루트·클라리넷 등)', r'플루트|플룻|클라리넷|색소폰|트럼펫|관악|오보에|호른'), ('성악·보컬', r'성악|보컬|노래|합창'), ('기타·드럼·실용음악', r'기타|드럼|베이스|실용음악|밴드|우쿨렐레'), ('국악', r'국악|가야금|해금|대금|판소리|장구')]
def tags(text, table): return [i for i, (_, pat) in enumerate(table) if re.search(pat, text)]
def main():
    ALLC = collections.Counter(); D = collections.defaultdict(lambda: {'c': collections.defaultdict(lambda: [0.0, 0.0]), 's': [0.0] * len(SUBJ), 'l': [0.0] * len(LEVEL), 'm': [0.0] * len(MUSIC), 'bo': 0.0, 'bol': 0.0, 'mu': 0.0, 'mul': 0.0}); cnt = collections.Counter()
    for fn in sorted(glob.glob(os.path.join(SRC, 'aca_*.json'))):
        for r in json.load(open(fn, encoding='utf-8')):
            code = r['ATPT_OFCDC_SC_CODE']; ad = (r.get('FA_RDNMA') or '').split(); zone = (r.get('ADMST_ZONE_NM') or '').strip()
            if len(ad) > 2 and re.search(r'[시군구]$', ad[1]): zone = ad[1] + (ad[2] if ad[1].endswith('시') and ad[2].endswith('구') else '') if code != 'I10' else zone
            emd = next((w for w in ad[2:4] if re.search(r'[읍면]$', w)), None); m = re.search(r'\(([^,)]+)', r.get('FA_RDNDA') or ''); ld = re.sub(r'\s', '', m.group(1)) if m else None
            W, how = match(code, zone, ld, emd)
            if not W and zone != (r.get('ADMST_ZONE_NM') or '').strip(): W, how = match(code, (r.get('ADMST_ZONE_NM') or '').strip(), ld, emd)
            cnt['전체'] += 1
            if not W: cnt['동을 못 찾음'] += 1; continue
            cr = (r.get('LE_CRSE_NM') or '').strip() or ((r.get('REALM_SC_NM') or '분야 모름').strip() + ' — 과정 미기재'); t = 1 if r.get('ACA_INSTI_SC_NM') == '교습소' else 0; lst = (r.get('LE_CRSE_LIST_NM') or '').strip()
            bo = (r.get('REALM_SC_NM') or '').startswith(('입시', '종합')); mu = cr.startswith(('음악', '실용음악')) or (cr.endswith('과정 미기재') and (r.get('REALM_SC_NM') or '').startswith('예능') and re.search(r'피아노|음악|바이올린', lst))
            txt = (r.get('ACA_NM') or '') + ' ' + re.sub(r'보습·논술|입시·논술', ' ', lst)   # 과목 = 학원 이름 + 교습과목 목록(과정 이름 「보습·논술」 자체는 논술로 치지 않는다)
            st = tags(txt, SUBJ) if bo else []; lv = tags(txt, LEVEL) if bo else []; mt = tags(txt, MUSIC) if mu else []
            for k8, w in W:
                d = D[k8]; d['c'][cr][t] += w; ALLC[cr] += w
                if bo:
                    d['bo'] += w; d['bol'] += w if st else 0
                    for i in st: d['s'][i] += w
                    for i in lv: d['l'][i] += w
                if mu:
                    d['mu'] += w; d['mul'] += w if mt else 0
                    for i in mt: d['m'][i] += w
    courses = [c for c, _ in ALLC.most_common()]; ci = {c: i for i, c in enumerate(courses)}; r1 = lambda v: round(v, 1); BY = collections.defaultdict(dict)
    for k8, d in D.items():
        cs = sorted(([ci[c], r1(v[0]), r1(v[1])] for c, v in d['c'].items() if v[0] + v[1] >= 0.05), key=lambda x: -(x[1] + x[2]))
        BY[k8[:2]][k8] = [cs, [r1(d['bo']), r1(d['bol']), [r1(x) for x in d['s']], [r1(x) for x in d['l']]], [r1(d['mu']), r1(d['mul']), [r1(x) for x in d['m']]]]
    os.makedirs(os.path.join(ROOT, 'data', 'neis-course'), exist_ok=True); td = datetime.date.today().isoformat()
    for sd, dong in sorted(BY.items()):
        doc = {'schema': 'tg-neis-course/1', 'made': td, 'sido': sd, 'source': '교육부 NEIS 교육정보 개방 포털 「학원교습소정보」(시·도 교육청 등록 · %s 받음 · 전국 %d곳) · 행정동 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0)' % (td, cnt['전체']),
               'note': ['**교육청에 등록한 교습과정 이름 그대로** 센 것이다(courses) — 개원 중인 학원·교습소만 · 체육도장(태권도 등)·개인과외교습자·무등록은 없다',
                        '과목(수학·영어 …)·대상(초·중·고)·악기는 **학원 이름과 교습과목 목록 글에서 낱말을 찾은 어림**이다(「○○수학학원」 → 수학) — 한 학원에 여러 낱말이 있으면 과목마다 한 번씩 센다(합이 학원 수보다 클 수 있다) · 낱말이 없는 학원은 과목을 모른다(「과목을 알 수 있는 곳」 수를 같이 싣는다 — 보습 학원의 60~70%쯤)',
                        '좌표가 없어 주소의 읍·면·법정동으로 행정동에 붙인 근사다 — 한 법정동이 여러 행정동에 걸치면 넓이 비율로 나눠 소수로 센다(그래서 0.3곳 같은 값이 나온다) · 전국 %d곳 가운데 동을 못 찾은 %d곳은 빠졌다' % (cnt['전체'], cnt['동을 못 찾음']),
                        '학원이 많다고 「공부를 잘 시키는 동」이라는 뜻은 아니다 — 이웃 동·다른 구에서 오는 학생이 섞인다(큰 학원가는 그 동 아이 수보다 훨씬 많다)',
                        '학원 이름·전화·교습비는 여기에 없다(교습비 가운데값은 neis-dong.json)'],
               'fields': {'courses': '교습과정 이름(전국에서 많은 차례 · dong 의 과정 번호가 가리킨다) — 「… — 과정 미기재」 = 과정 이름을 안 적어 분야 이름으로 묶은 것',
                          'subjects': '보습(입시·검정 및 보습 · 종합)의 과목 낱말(차례)', 'levels': '보습의 대상 낱말(차례)', 'music': '음악의 악기 낱말(차례)',
                          'dong': '{행정동 8자리: [[[과정 번호, 학원 수, 교습소 수]…많은 차례], [보습 곳 수, 그 가운데 과목을 알 수 있는 곳, [과목별 곳 수], [대상별 곳 수]], [음악 곳 수, 악기를 알 수 있는 곳, [악기별 곳 수]]]}'},
               'courses': courses, 'subjects': [s[0] for s in SUBJ], 'levels': [s[0] for s in LEVEL], 'music': [s[0] for s in MUSIC], 'dong': dong}
        p = os.path.join(ROOT, 'data', 'neis-course', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print(sd, '동', len(dong), os.path.getsize(p))
    print(dict(cnt), '과정', len(courses), courses[:14])
    for k in ('11650520', '11680600', '41590253'):
        v = BY[k[:2]].get(k)
        if v: print(k, [(courses[c[0]], c[1], c[2]) for c in v[0][:8]], '보습', v[1][:2], list(zip([s[0] for s in SUBJ], v[1][2])), list(zip([s[0] for s in LEVEL], v[1][3])), '음악', v[2][:2], list(zip([s[0][:3] for s in MUSIC], v[2][2])))
if __name__ == '__main__': main()
