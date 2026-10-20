# -*- coding: utf-8 -*-
# 데이터 압축지도 — 👮 경찰청 누리집 「경찰통계자료」 표 전부 → data/npa-stats.json
#   소유자 2026-10-20 「경찰 관련 모든 통계자료를 찾아서 넣어줘」 — www.police.go.kr › 정보공개 › 공공데이터 › 경찰통계자료(국·관마다 한 쪽)
#   표는 누리집에 적힌 글자 그대로(숫자 바꾸지 않음) · 쪽마다 [제목, 줄[칸…]] · 운전면허 소지자처럼 수백 줄 표는 줄 수만 적고 뺀다
#   누리집이 처음 오면 쿠키를 주고 같은 주소로 다시 보낸다(307) — 쿠키 통을 들고 다시 부른다
#   받은 쪽 = 07_API키/out/policestaff/npa/<쪽>.html
#   py -3.12 -X utf8 tools/region/npastat-bake.py
import os, re, json, html, datetime, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'policestaff', 'npa')
PAGES = [('publice02', '기획조정관'), ('publice0201', '경무인사기획관'), ('publice0202', '미래치안정책국'), ('publice0203', '범죄예방대응국'), ('publice0204', '생활안전교통국'), ('publice0205', '경비국'), ('publice0206', '국제치안협력국'),
         ('publice0207', '수사기획조정관'), ('publice0208', '수사국'), ('publice0209', '형사국'), ('publice0210', '안보수사국')]
BIG = 60


def opener():
    cj = http.cookiejar.CookieJar(); o = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); o.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130')]; return o


def clean(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def tables(h):
    m = h.find('<main'); h = h[m:] if m >= 0 else h
    out = []; pos = 0; head = ''
    for t in re.finditer(r'(?is)<(h3|h4|h5)[^>]*>(.*?)</\1>|<table.*?</table>', h):
        if t.group(1): head = clean(t.group(2)); continue
        tb = t.group(0); cap = re.search(r'(?is)<caption[^>]*>(.*?)</caption>', tb)
        rows = [[clean(c) for c in re.findall(r'(?is)<t[hd][^>]*>(.*?)</t[hd]>', r)] for r in re.findall(r'(?is)<tr[^>]*>(.*?)</tr>', tb)]
        rows = [r for r in rows if any(r)]
        out.append({'h': head, 'cap': clean(cap.group(1)) if cap else '', 'rows': rows if len(rows) <= BIG else [], 'nrows': len(rows)})
    return out


def main():
    os.makedirs(OUT, exist_ok=True); o = opener(); P = {}
    for pg, nm in PAGES:
        h = o.open('https://www.police.go.kr/www/open/publice/%s.jsp' % pg, timeout=60).read().decode('utf-8', 'replace')
        open(os.path.join(OUT, pg + '.html'), 'w', encoding='utf-8').write(h)
        T = tables(h); P[pg] = {'n': nm, 'url': 'https://www.police.go.kr/www/open/publice/%s.jsp' % pg, 't': T}
        print(pg, nm, len(T), '표', sum(1 for t in T if not t['rows']), '큰 표(뺌)')
    doc = {'schema': 'tg-npa-stats/1', 'made': datetime.date.today().isoformat(), 'source': '경찰청 누리집 「경찰통계자료」(www.police.go.kr › 정보공개 › 공공데이터 › 경찰통계자료) — 국·관마다 한 쪽',
           'fields': 'pages{쪽 이름: {n 국·관, url, t[{h 제목, cap 표 설명, rows[[칸 글…]] 누리집 글자 그대로, nrows}]}} — rows 가 비면 줄이 많아(%d 넘음) 뺀 표(누리집에서 본다)' % BIG,
           'note': ['숫자는 누리집 표 글자 그대로 — 기준 시점은 표 제목·설명에 적힌 대로(없으면 누리집 쪽을 본다)', '「112신고」·「집회시위」·「인력(계급·기능별)」·「순직·공상」 등은 공식 통계 · 의원실 보도 숫자와 다를 수 있다'],
           'pages': P}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'npa-stats.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('표', sum(len(v['t']) for v in P.values()), '·', os.path.getsize(os.path.join(ROOT, 'data', 'npa-stats.json')), 'B')


if __name__ == '__main__':
    main()
