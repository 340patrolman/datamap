# -*- coding: utf-8 -*-
# 데이터 압축지도 — 📜 경찰서 연혁(소유자 2026-10-10 「역사 같은 것도」) · 1차 = 서울 31서
#   출처 = 서울경찰청 누리집의 경찰서별 「소개마당 › 연혁」(www.smpa.go.kr/<서 약자> — 서마다 같은 주소 꼴 · 약자는 누리집의 경찰서 고르기 목록에서 읽는다)
#   누리집 저작권 정책(2026-10-10 확인): 공공누리 표시가 붙은 자료만 자유이용 · 연혁 쪽에는 표시가 없다 → 글을 통째로 옮기지 않는다:
#     날짜와 사실(개서·청사 이전·이름 바뀜·관서 수)만 짧게 줄여 적고, 줄마다 출처(그 서 누리집)를 단다 · 받은 원문은 07_API키/out/polhist/ 에만(저장소 밖)
#   지어내지 않는다 — 누리집에 연혁이 없거나 못 읽은 서는 빈칸으로 둔다
#   py -3.12 -X utf8 tools/region/polhist-fetch.py → tools/region/polcard-hist.json (그 뒤 polcard-bake.py)
import json, os, re, html, time, datetime, urllib.request, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'polhist'); HERE = os.path.dirname(os.path.abspath(__file__))
KEEP = re.compile(r'개서|開署|개청|창립|발족|신설|개칭|명칭|이전|준공|승격|분리|분할|통합|설치|개편|청사|인수|지구대|파출소|관할')
def text(t):
    b = re.sub(r'<script.*?</script>|<style.*?</style>|<!--.*?-->', '', t, flags=re.S)
    x = re.sub(r'[ \t\r\xa0]+', ' ', html.unescape(re.sub(r'<[^>]+>', '\n', b))); return [l.strip() for l in x.split('\n') if l.strip()]
def main():
    os.makedirs(RAW, exist_ok=True); today = datetime.date.today().isoformat()
    cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    def get(u, ref=None):
        h = {'User-Agent': 'Mozilla/5.0'}
        if ref: h['Referer'] = ref
        return op.open(urllib.request.Request(u, headers=h), timeout=40).read().decode('utf-8', 'replace')
    top = get('https://www.smpa.go.kr/home/homeIndex.do?menuCode=bb')
    ST = re.findall(r'<option[^>]*value="https://www\.smpa\.go\.kr/([a-z0-9]+)"[^>]*>\s*(서울[가-힣]+경찰서)', top)
    OUT = {}; bad = []
    for code, name in ST:
        try:
            home = 'https://www.smpa.go.kr/home/homeIndex.do?menuCode=' + code; t = get(home)
            m = re.search(r'<a[^>]+href="(/user/nd\d+\.do)"[^>]*>\s*연혁\s*<', t)
            if not m: bad.append(name + '(연혁 메뉴 없음)'); continue
            h = get('https://www.smpa.go.kr' + m.group(1), home); L = text(h)
            if ('서울 ' + name[2:]) not in ' '.join(L[:400]) and name not in ' '.join(L[:400]): bad.append(name + '(다른 서 쪽이 열림)'); continue
            i = max(k for k, l in enumerate(L) if l == '연혁'); j = next((k for k in range(i, len(L)) if '열람하신 정보' in L[k]), len(L)); body = L[i + 1:j]
            json.dump({'name': name, 'url': 'https://www.smpa.go.kr/' + code, 'got': today, 'lines': body}, open(os.path.join(RAW, code + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
            ev = []; k = 0
            while k < len(body):
                d = re.match(r'^[\'’]?(\d{2,4})\s*[.\-년]\s*(\d{1,2})?\s*[.\-월]?\s*(\d{1,2})?\s*[.일]?\s*$', body[k]); d2 = re.match(r'^[\'’]?((?:19|20)\d{2})\s*[.\-년]\s*(\d{1,2})\s*[.\-월]\s*(\d{1,2})?\s*[.일]?\s+(.+)$', body[k])
                if d and k + 1 < len(body):
                    y = d.group(1); y = ('19' if int(y) > 30 else '20') + y if len(y) == 2 else y
                    ev.append(['.'.join(x.zfill(2) if n else x for n, x in enumerate([y, d.group(2) or '', d.group(3) or '']) if x), body[k + 1]]); k += 2
                elif d2: ev.append(['.'.join(x.zfill(2) if n else x for n, x in enumerate([d2.group(1), d2.group(2), d2.group(3) or '']) if x), d2.group(4)]); k += 1
                else: k += 1
            keep = [[d, re.sub(r'\s+', ' ', s)[:70]] for d, s in ev if KEEP.search(s)]
            if not keep: bad.append(name + '(날짜 줄을 못 읽음 · 원문 %d줄)' % len(body)); continue
            if len(keep) > 10: keep = keep[:5] + keep[-5:]   # 처음 다섯(개서 무렵)과 마지막 다섯(요즘)
            OUT[name] = [[d, s, '서울경찰청 누리집 %s 「연혁」(smpa.go.kr/%s · %s 확인 · 줄여 적음)' % (name, code, today)] for d, s in keep]
        except Exception as e: bad.append(name + '(%s)' % type(e).__name__)
        time.sleep(0.4)
    json.dump(OUT, open(os.path.join(HERE, 'polcard-hist.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, indent=0)
    print('서울 서', len(ST), '· 연혁 읽음', len(OUT), '· 못 읽음', bad)
    for n in ('서울서초경찰서', '서울방배경찰서'):
        for e in OUT.get(n, []): print(' ', n, e[0], e[1])
if __name__ == '__main__': main()
