# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🎭 공연 일정(민간 공연장 포함) · 공연장 좌표·객석 수 → data/venue-events-kopis.json
#   소유자 2026-10-12 KOPIS 열쇠 발급 「api 목록에 기억하고 모두 진행하자」 → 끝나는 시각에 둘레 역·교차로가 몰리는 것을 보려면 「어디서(객석 몇) · 몇 시에 시작해 · 몇 분 하나」
#   원자료: (재)예술경영지원센터 공연예술통합전산망 KOPIS OpenAPI(열쇠 keys.json "kopis" · http://www.kopis.or.kr/openApi/restful/ · XML)
#     pblprfr?stdate&eddate(31일까지)&cpage&rows(100까지)&signgucode(11 서울·41 경기·28 인천) 공연 목록 → pblprfr/<공연 ID> 상세(공연장 ID mt10id · dtguidance 요일(시각) · prfruntime 공연 시간) → prfplc/<공연장 ID> 상세(la·lo·seatscale·홀)
#     받은 것은 07_API키/out/kopis/{list,prf,plc}/ 에 그대로 둔다(다시 돌리면 없는 것만 받는다)
#   끝 시각 = 시작 시각 + 공연 시간(자료의 prfruntime 그대로 — 인터미션 포함 여부는 공연마다 다르고 커튼콜·퇴장 시간은 없다). 공연 시간이 없으면 끝은 null
#   ⚠ 2026-10-13 전국을 한 번에(약 9천 번 · 0.05초 간격) 받은 뒤 KOPIS 가 이 PC 를 막았다(HTTP 400 「Request Blocked」 — 모든 요청) → 간격을 0.5초로 늘렸다. 막히면 그날은 다시 부르지 않는다. 광주(29)·전남(46)은 그때 한 건도 안 받아졌다(코드가 바뀌었는지 막힌 탓인지 모름 — 풀린 뒤 한 번 불러 확인)
#   py -3.12 -X utf8 tools/region/kopis-bake.py fetch [앞 달수 3] [뒤 달수 3]   → 받기(오래 걸린다 · 뒤에서)
#   py -3.12 -X utf8 tools/region/kopis-bake.py build                            → 굽기(한 장 = 서울·경기·인천 · venue-events-kopis/<시도>.json = 전국)
import json, os, re, sys, time, glob, datetime, collections, urllib.request, html
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'kopis'); SIDO = {'11': '서울', '41': '경기', '28': '인천'}
def key(): return json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kopis']
def get(path, **q):
    u = 'http://www.kopis.or.kr/openApi/restful/%s?service=%s' % (path, key()) + ''.join('&%s=%s' % x for x in q.items())
    for t in range(4):
        try: return urllib.request.urlopen(u, timeout=60).read().decode('utf-8', 'replace')
        except Exception: time.sleep(3 + t * 4)
    return ''
def num(v):
    v = re.sub(r'[^0-9]', '', v or ''); return int(v) if v else 0
def tag(x, t):
    m = re.search(r'<%s>(.*?)</%s>' % (t, t), x, re.S); return html.unescape(m.group(1)).strip() if m else ''
# 전국(2026-10-13 소유자 「기회될 때 전국으로」): KOPIS 의 시도 코드(signgucode) — 지도의 시도 코드와 다른 곳이 있다(광주 29 · 전남 46 · 전북 45 · 강원 51)
KSG = ['11', '26', '27', '28', '29', '30', '31', '36', '41', '51', '43', '44', '45', '46', '47', '48', '50']
# 주소 앞 낱말 → 지도의 시도 코드(광주·전남 = 12 · 전북 52 · 강원 51)
ADDR = [('서울', '11'), ('부산', '26'), ('대구', '27'), ('인천', '28'), ('광주', '12'), ('대전', '30'), ('울산', '31'), ('세종', '36'), ('경기', '41'), ('강원', '51'), ('충청북', '43'), ('충북', '43'), ('충청남', '44'), ('충남', '44'), ('전북', '52'), ('전라북', '52'), ('전남', '12'), ('전라남', '12'), ('경상북', '47'), ('경북', '47'), ('경상남', '48'), ('경남', '48'), ('제주', '50')]
def fetch(back=3, fwd=3):
    for d in ('list', 'prf', 'plc'): os.makedirs(os.path.join(OUT, d), exist_ok=True)
    today = datetime.date.today(); a = today - datetime.timedelta(days=30 * back); end = today + datetime.timedelta(days=30 * fwd); ids = {}
    while a < end:
        b = min(a + datetime.timedelta(days=30), end)
        for sg in KSG:
            pg = 1
            while True:
                t = get('pblprfr', stdate=a.strftime('%Y%m%d'), eddate=b.strftime('%Y%m%d'), cpage=pg, rows=100, signgucode=sg); dbs = re.findall(r'<db>(.*?)</db>', t, re.S)
                for x in dbs: ids[tag(x, 'mt20id')] = sg
                if len(dbs) < 100: break
                pg += 1
        print(a, b, '공연', len(ids)); sys.stdout.flush(); a = b + datetime.timedelta(days=1)
    json.dump(ids, open(os.path.join(OUT, 'list', 'ids_%s.json' % today.isoformat()), 'w'))
    n = 0; plc = set()
    for i, pid in enumerate(sorted(ids)):
        p = os.path.join(OUT, 'prf', pid + '.xml')
        if not os.path.exists(p):
            t = get('pblprfr/' + pid)
            if '<mt20id>' not in t: continue
            open(p, 'w', encoding='utf-8', newline='\n').write(t); n += 1; time.sleep(0.5)
        else: t = open(p, encoding='utf-8').read()
        plc.add(tag(t, 'mt10id'))
        if i % 500 == 0: print('상세', i, '/', len(ids), '새로', n); sys.stdout.flush()
    m = 0
    for fid in sorted(x for x in plc if x):
        p = os.path.join(OUT, 'plc', fid + '.xml')
        if os.path.exists(p): continue
        t = get('prfplc/' + fid)
        if '<mt10id>' in t: open(p, 'w', encoding='utf-8', newline='\n').write(t); m += 1; time.sleep(0.5)
    print('끝 — 공연', len(ids), '새 상세', n, '공연장', len(plc), '새로', m)
WD = '월화수목금토일'
def runtime(s):
    h = re.search(r'(\d+)\s*시간', s); m = re.search(r'(\d+)\s*분', s); v = (int(h.group(1)) * 60 if h else 0) + (int(m.group(1)) if m else 0); return v or None
def guide(s):
    # 'HOL(15:00)' 은 공휴일 — 요일 0~6 과 7(공휴일). '화요일 ~ 금요일(19:30), 토요일(14:00,18:00)' → {요일: [시각…]}
    out = collections.defaultdict(list)
    for part in re.findall(r'([^()]+)\(([^()]*)\)', s or ''):
        days = set(); lab = part[0]
        for seg in re.split(r'[,、]', lab):
            seg = seg.strip(' ,'); r = re.findall(r'([월화수목금토일])요일', seg)
            if '~' in seg and len(r) == 2:
                i, j = WD.index(r[0]), WD.index(r[1]); days |= set(range(i, j + 1)) if i <= j else set(list(range(i, 7)) + list(range(0, j + 1)))
            else: days |= set(WD.index(x) for x in r)
            if 'HOL' in seg: days.add(7)
        ts = re.findall(r'(\d{1,2}:\d{2})', part[1])
        for d in days: out[d] += ['%02d:%s' % (int(t.split(':')[0]), t.split(':')[1]) for t in ts]
    return out
def build():
    HOL = set(json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8'))['days']); today = datetime.date.today(); lo = today - datetime.timedelta(days=95); hi = today + datetime.timedelta(days=95)
    V = {}
    for f in glob.glob(os.path.join(OUT, 'plc', '*.xml')):
        t = open(f, encoding='utf-8').read(); fid = tag(t, 'mt10id')
        try: la = float(tag(t, 'la')); lg = float(tag(t, 'lo'))
        except Exception: continue
        if not (33 < la < 39 and 124 < lg < 132): continue
        halls = [[tag(h, 'prfplcnm'), num(tag(h, 'seatscale'))] for h in re.findall(r'<mt13>(.*?)</mt13>', t, re.S)]; top = t.split('<mt13s>')[0]
        V[fid] = {'id': fid, 'n': tag(top, 'fcltynm'), 'addr': tag(top, 'adres'), 'lat': round(la, 5), 'lon': round(lg, 5), 'seats': sum(h[1] for h in halls), 'kind': tag(top, 'fcltychartr'), 'halls': halls, 'shows': [], 'day': []}
    np = 0; nrt = 0; nd = 0; ne = 0
    for f in glob.glob(os.path.join(OUT, 'prf', '*.xml')):
        t = open(f, encoding='utf-8').read(); v = V.get(tag(t, 'mt10id'))
        if not v: continue
        try: a = datetime.datetime.strptime(tag(t, 'prfpdfrom'), '%Y.%m.%d').date(); b = datetime.datetime.strptime(tag(t, 'prfpdto'), '%Y.%m.%d').date()
        except Exception: continue
        rt = runtime(tag(t, 'prfruntime')); g = guide(tag(t, 'dtguidance')); hall = tag(t, 'fcltynm'); hm = re.search(r'\(([^()]*)\)\s*$', hall); hn = hm.group(1) if hm else ''; seats = next((h[1] for h in v['halls'] if h[0] == hn), None)
        np += 1; nrt += 1 if rt else 0; si = len(v['shows']); v['shows'].append([tag(t, 'prfnm')[:60], tag(t, 'genrenm'), a.isoformat(), b.isoformat(), tag(t, 'dtguidance')[:80], rt, hn, seats, tag(t, 'mt20id')])
        d = max(a, lo)
        while d <= min(b, hi):
            ds = d.isoformat(); wd = 7 if (ds in HOL and 7 in g) else d.weekday()
            for st in g.get(wd, []):
                en = None
                if rt:
                    x = int(st[:2]) * 60 + int(st[3:]) + rt; en = '%02d:%02d' % (x // 60, x % 60); ne += 1
                v['day'].append([ds, st, en, si]); nd += 1
            d += datetime.timedelta(days=1)
    venues = [v for v in V.values() if v['shows']]
    for v in venues: v['day'].sort(key=lambda x: (x[0], x[1], x[3])); v['sd'] = next((c for k, c in ADDR if v['addr'].startswith(k)), ''); v['sido'] = next((s for s in SIDO.values() if s in v['addr'][:8]), ''); a = v.pop('addr').split(); v['gu'] = ' '.join(a[1:3]) if len(a) > 2 and a[1].endswith('시') and a[2].endswith('구') else (a[1] if len(a) > 1 else '')
    venues.sort(key=lambda v: -len(v['day']))
    doc = {'schema': 'tg-venue-kopis/1', 'made': today.isoformat(), 'source': '(재)예술경영지원센터 공연예술통합전산망(KOPIS · www.kopis.or.kr) OpenAPI — 공연 목록·상세·공연시설 상세 · %s 받음 · 서울·경기·인천' % today.isoformat(),
           'note': ['공연장마다 좌표·객석 수가 있고 공연마다 요일별 시작 시각·공연 시간이 있다 — **끝 시각 = 시작 + 공연 시간**(자료의 공연 시간 칸 그대로 · 커튼콜·퇴장에 걸리는 시간은 없다 · 공연 시간이 없는 공연은 끝 null). 공연 %d건 가운데 공연 시간이 있는 것 %d건' % (np, nrt),
                    '날마다의 회차(day)는 「요일(시각)」 안내 글을 공연 기간에 펼친 것이다 — 휴연·특별 회차·매진 여부는 반영되지 않는다. 오늘 앞뒤 95일만 펼쳤다',
                    '**객석 수는 그 홀의 자리 수이지 온 사람 수가 아니다** — 얼마나 찼는지는 이 자료에 없다(둘레 역 승하차와 날짜를 맞대 본다)',
                    'KOPIS 는 공연(연극·뮤지컬·클래식·국악·무용·대중음악·서커스 등)만 다룬다 — 프로야구·축구·농구 경기, 전시·박람회는 없다(more-sources.json)',
                    '대중음악 큰 공연은 예매처가 KOPIS 에 보내는 것만 실린다 — 빠진 공연이 있을 수 있다. 서울시·자치구 행사는 venue-events-seoul.json'],
           'fields': {'venues': '[{id 공연시설 ID, n 이름, sido, gu 시군구, lat, lon, seats 홀 객석 수의 합(자료의 시설 전체 값은 틀린 곳이 있어 쓰지 않았다), kind 시설 성격, halls [[홀 이름, 객석 수]], shows [[제목, 갈래, 시작일, 끝일, 요일(시각) 안내 글 그대로, 공연 시간(분)|null, 홀 이름, 그 홀 객석 수|null, 공연 ID]], day [[날짜, 시작 HH:MM, 끝 HH:MM|null, shows 의 차례 번호]](오늘 앞뒤 95일)}] — 회차 많은 차례'},
           'venues': venues}
    # 시도마다 한 장(전국) — data/venue-events-kopis/<지도의 시도 코드>.json · 꼴은 한 장과 같다. 옛 한 장(venue-events-kopis.json)은 서울·경기·인천만 그대로 둔다(지도가 읽는다)
    os.makedirs(os.path.join(ROOT, 'data', 'venue-events-kopis'), exist_ok=True); allv = venues; bysd = collections.defaultdict(list)
    for v in allv: bysd[v.pop('sd')].append(v)
    for sd, vs in sorted(bysd.items()):
        if not sd: continue
        dd = dict(doc); dd['sido_code'] = sd; dd['venues'] = vs; dd['source'] = doc['source'].replace('서울·경기·인천', '전국 가운데 이 시도'); ps = os.path.join(ROOT, 'data', 'venue-events-kopis', sd + '.json'); json.dump(dd, open(ps, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('  ', sd, len(vs), sum(len(v['day']) for v in vs), os.path.getsize(ps))
    # 서울은 구마다 한 장 더(폰이 2.3MB 를 통째로 받지 않게 · 2026-10-13) — data/venue-events-kopis/g/<구 코드>.json · 꼴은 시도 파일 그대로 · 공연장이 없는 구도 빈 venues 로 한 장
    GU = {g['name']: g['gu'] for g in json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus'] if g['gu'][:2] == '11'}; os.makedirs(os.path.join(ROOT, 'data', 'venue-events-kopis', 'g'), exist_ok=True); big = 0; lost = 0
    for nm, code in GU.items():
        vs = [v for v in bysd.get('11', []) if v.get('gu') == nm]; dd = dict(doc); dd['sido_code'] = '11'; dd['gu'] = code; dd['venues'] = vs; dd['source'] = doc['source'].replace('서울·경기·인천', '서울 ' + nm)
        pg = os.path.join(ROOT, 'data', 'venue-events-kopis', 'g', code + '.json'); json.dump(dd, open(pg, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        if os.path.getsize(pg) > 1000000:   # 대학로가 든 종로구처럼 1MB 를 넘으면 회차를 오늘 앞 30일 · 뒤 60일로 줄인다(note 에 적는다 · 시도 한 장에는 95일 그대로)
            d0 = (today - datetime.timedelta(days=30)).isoformat(); d1 = (today + datetime.timedelta(days=60)).isoformat(); dd['venues'] = [dict(v, day=[x for x in v['day'] if d0 <= x[0] <= d1]) for v in vs]; dd['note'] = doc['note'] + ['이 구는 공연이 많아 회차(day)를 오늘 앞 30일 · 뒤 60일만 실었다(그 밖의 구와 시도 파일은 앞뒤 95일)']; dd['day_window'] = [d0, d1]
            json.dump(dd, open(pg, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        big = max(big, os.path.getsize(pg))
    lost = sum(1 for v in bysd.get('11', []) if v.get('gu') not in GU); print('   서울 구 파일', len(GU), '가장 큰', big, '구를 못 가른 공연장', lost)
    venues = [v for v in allv if v['sido']]; doc['venues'] = venues
    p = os.path.join(ROOT, 'data', 'venue-events-kopis.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '공연장', len(venues), '공연', np, '공연 시간 있음', nrt, '회차', nd, '끝 시각 있음', ne)
    for v in sorted(venues, key=lambda v: -v['seats'])[:15]: print(v['n'], v['seats'], len(v['shows']), len(v['day']))
    print('서초', [(v['n'], v['seats'], len(v['day'])) for v in venues if v['gu'] == '서초구'][:15])
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'fetch': fetch(*(int(x) for x in sys.argv[2:4]))
    else: build()
