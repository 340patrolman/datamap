# -*- coding: utf-8 -*-
# 데이터 압축지도 — 📢 서울 주요 집회 해마다·달마다(2021~) → data/rally-hist-seoul.json
#   소유자 2026-10-20 「집회시위 행진 등 5년치 월별 연별로 데이터가 있어야 해」
#   원천 = 서울경찰청 「오늘의 주요집회」 게시판(www.smpa.go.kr/user/nd54882.do) — 날마다 한 글 · 2025 하반기 전 글은 본문 없이 첨부(hwp·pdf·jpg)뿐 → PDF 의 글자층을 읽는다
#   ⚠ 「주요 집회」만이다(서울청이 그날 알린 것) — 신고된 집회 전부가 아니다. 경찰청 공식 「집회시위 개최 현황」(신고·개최 전부)과 숫자가 다르다
#   싣는 것 = 날짜·시각·장소 글·신고 인원·관할서를 묶은 수(달·해·관할서·시간대·행진 여부) · 주최자는 원문에도 없다
#   받은 것 = 07_API키/out/rally/hist/<글 번호>.html · <글 번호>.pdf(새 것만 받음 · 요청 사이 0.7초)
#   py -3.12 -X utf8 tools/region/rallyhist-bake.py [fetch] [build]
import json, os, re, sys, time, html, datetime, urllib.request, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'rally', 'hist')
BASE = 'https://www.smpa.go.kr/user/nd54882.do'; DL = 'https://www.smpa.go.kr/common/attachfile/attachfileDownload.do?attachNo='; UA = {'User-Agent': 'Mozilla/5.0'}
START = '2021-01-01'


def get(url, binary=False):
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read(); time.sleep(0.7)
            return b if binary else b.decode('utf-8', 'replace')
        except Exception:
            time.sleep(5 + t * 15)
    return b'' if binary else ''


def fetch():
    os.makedirs(OUT, exist_ok=True); ip = os.path.join(OUT, 'index.json'); idx = json.load(open(ip, encoding='utf-8')) if os.path.exists(ip) else {}
    page = 1; new = 0; miss = 0
    while page <= 400:
        s = get(BASE + '?page=%d' % page); rows = re.findall(r"goBoardView\('[^']*','View','(\d+)'\)[^>]*>\s*(?:<[^>]+>\s*)*([^<]*오늘의 집회[^<]*)", s)
        if not rows: miss += 1; page += 1
        if not rows and miss > 3: break
        if not rows: continue
        old = 0; todo = []
        for no, title in rows:
            m = re.search(r'(\d{6})', title)
            if not m: continue
            d = '20%s-%s-%s' % (m.group(1)[:2], m.group(1)[2:4], m.group(1)[4:6])
            if d < START: old += 1; continue
            todo.append((no, d))
        def one(x):
            no, d = x; hp = os.path.join(OUT, no + '.html'); pp = os.path.join(OUT, no + '.pdf')
            if not os.path.exists(hp):
                b = get(BASE + '?View&boardNo=' + no)
                if len(b) < 5000: return None
                open(hp, 'w', encoding='utf-8').write(b)
            if not os.path.exists(pp):
                b = open(hp, encoding='utf-8').read(); a = re.findall(r"attachfileDownload\('/common/attachfile/attachfileDownload\.do','(\d+)'\)\"[^>]*>([^<]*\.pdf)<", b)
                if a:
                    p = get(DL + a[0][0], True)
                    if p[:4] == b'%PDF': open(pp, 'wb').write(p)
            return x
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(4) as ex:   # 서버가 한 글에 약 10초 — 넷만 같이
            for r in ex.map(one, todo):
                if r: idx[r[0]] = r[1]; new += 1
        print('쪽', page, rows[-1][1].strip()[:20], '새', new, flush=True)
        json.dump(idx, open(ip, 'w', encoding='utf-8'), ensure_ascii=False)
        if old == len(rows): break
        page += 1
    print('글', len(idx), '새로', new)


ST = ['종로', '남대문', '중부', '서대문', '혜화', '용산', '성북', '종암', '동대문', '마포', '영등포', '성동', '동작', '광진', '서부', '강북', '금천', '중랑', '강남', '관악', '강서', '강동', '양천', '구로', '노원', '송파', '서초', '방배', '은평', '도봉', '수서', '동대문']


def text_of(no):
    pp = os.path.join(OUT, no + '.pdf')
    if os.path.exists(pp):
        try:
            import pypdf
            return '\n'.join(p.extract_text() or '' for p in pypdf.PdfReader(pp).pages), 'pdf'
        except Exception:
            pass
    hp = os.path.join(OUT, no + '.html')
    if os.path.exists(hp):
        t = html.unescape(re.sub(r'<[^>]+>', '\n', re.sub(r'(?is)<(script|style).*?</\1>', '', open(hp, encoding='utf-8').read())))
        a = t.find('일시')
        if a >= 0: return t[a:t.find('이전글', a)], 'html'
    return '', None


def parse(t):
    t = re.sub(r'[ \t\xa0]+', ' ', t); out = []
    stre = '|'.join(sorted(set(re.escape(' '.join(s)) if len(s) == 2 else re.escape(s) for s in ST) | set(ST), key=len, reverse=True))
    # 한 건 = 시각 범위 … 「N명 관할서」(2024 상반기 전 PDF 는 「명」 없이 「690 수 서」)
    for m in re.finditer(r'(\d{1,2}):(\d{2})\s*[~∼\-]\s*(\d{1,2}):(\d{2})(.*?)([0-9][0-9,]*)\s*명?\s*(' + stre + r')(?![가-힣])', t, re.S):
        place = re.sub(r'\s+', ' ', m.group(5)).strip()
        st = m.group(7).replace(' ', '')
        out.append({'h': int(m.group(1)), 'h2': int(m.group(3)), 'n': int(m.group(6).replace(',', '')), 'st': st, 'march': bool(re.search(r'→|⇆|->|↔|⇄', place)), 'p': place[:120]})
    return out


def build():
    idx = json.load(open(os.path.join(OUT, 'index.json'), encoding='utf-8'))
    M = collections.defaultdict(lambda: [0, 0, 0, 0]); Y = collections.defaultdict(lambda: [0, 0, 0, 0]); STY = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
    HR = collections.defaultdict(lambda: [0] * 24); WD = collections.defaultdict(lambda: [0] * 7); BIG = []
    bad = []
    days = collections.Counter(); empty = 0; noread = []; src = collections.Counter(); seen = set()
    for no, d in sorted(idx.items(), key=lambda x: x[1]):
        if d in seen: continue
        try: datetime.date.fromisoformat(d)
        except ValueError:   # 글 제목 날짜가 잘못 적힌 글(「240080」 등) — PDF 머리의 「2024. 03. 12.(화)」 로 고친다
            t0, _ = text_of(no); m0 = re.search(r'(20\d{2})\.\s*(\d{1,2})\.\s*(\d{1,2})\.\s*\(', t0)
            if not m0: bad.append([no, d]); continue
            d = '%s-%02d-%02d' % (m0.group(1), int(m0.group(2)), int(m0.group(3)))
            if d in seen: continue
        t, how = text_of(no)
        if not how: noread.append(d); continue
        seen.add(d); src[how] += 1; ym = d[:7]; y = d[:4]; days[ym] += 1
        R = parse(t)
        if not R:
            if '없음' in t: empty += 1
            else: noread.append(d)
            continue
        for r in R:
            for A in (M[ym], Y[y]):
                A[0] += 1; A[1] += r['n']; A[2] += r['march']; A[3] += r['n'] >= 1000
            s = STY[r['st']][y]; s[0] += 1; s[1] += r['n']; s[2] += r['march']
            HR[y][min(23, r['h'])] += 1; WD[y][datetime.date.fromisoformat(d).weekday()] += 1
            if r['n'] >= 10000: BIG.append([d, '%02d시' % r['h'], r['n'], r['st'], r['march'], r['p']])
    doc = {'schema': 'tg-rally-hist-seoul/1', 'made': datetime.date.today().isoformat(),
           'source': '서울경찰청 「오늘의 주요집회」 게시판(www.smpa.go.kr/user/nd54882.do) — 글 본문 · 첨부 PDF 글자층',
           'fields': 'month{YYYY-MM: [건수, 신고 인원 합, 행진 건수, 1천 명 이상 건수, 글 있는 날 수]} · year{YYYY: [건수, 인원 합, 행진, 1천 명↑]} · st{관할서: {YYYY: [건수, 인원 합, 행진]}} · hour{YYYY: 시작 시각 0~23 건수} · wday{YYYY: 월~일 건수} · big[[날짜, 시작, 신고 인원, 관할서, 행진, 장소 글]](신고 1만 명 이상)',
           'note': ['「주요 집회」만 — 서울청이 그날 알린 것이지 신고된 집회 전부가 아니다(경찰청 「집회시위 개최 현황」과 다르다)', '인원 = 신고 인원(실제 참가 인원 아님)', '행진 = 장소 글에 →·⇆ 가 있는 것', '글이 없는 날·읽지 못한 날은 세지 않았다 — 달마다 「글 있는 날 수」를 같이 본다', '2025 하반기 전 글은 첨부 PDF 를 읽었다'],
           'month': {k: M[k] + [days[k]] for k in sorted(M)}, 'year': {k: Y[k] for k in sorted(Y)},
           'st': {k: dict(sorted(v.items())) for k, v in sorted(STY.items(), key=lambda x: -sum(a[0] for a in x[1].values()))},
           'hour': dict(sorted(HR.items())), 'wday': dict(sorted(WD.items())), 'big': BIG,
           'read': {'days': len(seen), 'empty_days': empty, 'unread_days': len(noread), 'pdf': src['pdf'], 'html': src['html'], 'unread_sample': noread[:20], 'bad_title': bad}}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'rally-hist-seoul.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('읽은 날', len(seen), '집회 없음', empty, '못 읽음', len(noread), dict(src))
    for y in sorted(Y): print(y, Y[y])


if __name__ == '__main__':
    a = sys.argv[1:] or ['fetch', 'build']
    if 'fetch' in a: fetch()
    if 'build' in a: build()
