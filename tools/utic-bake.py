# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚨 경찰청 도시교통정보센터(UTIC) 돌발 정보 스냅숏(소유자 2026-10-10 「이 키를 입력하고 써먹자」)
#   UTIC 개방데이터는 신청한 IP 대역(이 PC)에서 http 로만 열린다 → 지도(https · 다른 IP)가 직접 못 부른다 → 이 PC 가 받아 한 장으로 구워 올린다(live-refresh.py 가 같이 부른다)
#   주소 = http://www.utic.go.kr/guide/imsOpenData.do?key=…(메일 안내 2026-10-06) · 키 = 07_API키/keys.json 의 utic(출력·커밋 금지)
#   UTIC 공지: 과다 호출·크롤링은 차단한다 → 한 번에 한 번만 부른다(되풀이·쪽 넘김 없음) · 받은 원문은 저장소 밖 07_API키/out/utic/ 에
#   싣는 것 = 돌발마다 자리·갈래 글머리([사고]·[공사] …)·제목·도로·시작·끝·고친 때 · 코드 칸은 뜻을 지어 적지 않고 원문 값 그대로(tc·gc·rc·sc)
#   실시간이 아니다 — 받은 시각(made)의 한 장이다(지도는 그렇게 밝힌다) · 고속도로·국도는 국가교통정보센터(ITS) 층이 따로 있다
#   py -3.12 -X utf8 tools/utic-bake.py → data/utic-ims.json
import json, os, re, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'utic')
def when(s):   # 「2026년 10월 10일 13시 28분」 → 「2026-10-10 13:28」
    m = re.match(r'\s*(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2})시\s*(\d{1,2})분', s or '')
    return '%s-%02d-%02d %02d:%02d' % (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))) if m else ''
def bake():
    os.makedirs(OUT, exist_ok=True)
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['utic']
    b = urllib.request.urlopen(urllib.request.Request('http://www.utic.go.kr/guide/imsOpenData.do?key=' + k, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read()
    open(os.path.join(OUT, 'ims_last.xml'), 'wb').write(b); t = b.decode('utf-8', 'replace')
    if '<record>' not in t: raise RuntimeError('UTIC 돌발: record 가 없다(' + re.sub(r'\s+', ' ', t[:120]).replace(k, '***') + ')')
    f = lambda r, n: ((re.search('<%s>(.*?)</%s>' % (n, n), r, re.S) or [0, ''])[1] or '').strip()
    items = []
    for r in re.findall(r'<record>(.*?)</record>', t, re.S):
        try: lon, lat = round(float(f(r, 'locationDataX')), 6), round(float(f(r, 'locationDataY')), 6)
        except ValueError: continue
        if not (124 < lon < 132 and 33 < lat < 39): continue
        ti = re.sub(r'\s+', ' ', f(r, 'incidentTitle')); kind = (re.match(r'\[(.+?)\]', ti) or [0, ''])[1]
        items.append([f(r, 'incidentId'), kind, lon, lat, ti[:200], f(r, 'roadName'), when(f(r, 'startDate')), when(f(r, 'endDate')), when(f(r, 'updateDate')), f(r, 'addressJibun'),
                      f(r, 'incidenteTypeCd'), f(r, 'incidenteGradeCd'), f(r, 'incidentRegionCd'), f(r, 'sourceCode'), f(r, 'lane')])
    items.sort(key=lambda x: x[8], reverse=True)
    doc = {'schema': 'tg-utic-ims/1', 'made': time.strftime('%Y-%m-%d %H:%M'),
           'source': '경찰청 도시교통정보센터(UTIC) 개방데이터 — 돌발정보(www.utic.go.kr/guide/imsOpenData.do · 인증키·등록 IP 로 받음) · 시내 도로의 사고·공사·행사·통제 등',
           'note': ['실시간이 아니다 — made 시각에 이 PC 가 받아 구운 한 장이다(PC 가 꺼져 있으면 낡는다 · 끝 시각 end 가 지난 것은 이미 풀렸을 수 있다)', '자치단체 사정에 따라 일부 지역은 비어 있을 수 있다(UTIC 안내)',
                    '코드 칸(tc·gc·rc·sc)은 UTIC 원문 값 그대로다 — 뜻은 UTIC 「개방데이터 세부내용」 문서에 있다(여기에 지어 적지 않았다) · 갈래(kind)는 제목 맨 앞 [ ] 안 글', '고속도로·국도 돌발은 국가교통정보센터(ITS) 층을 같이 본다'],
           'fields': 'items[[id, kind 갈래(제목 글머리), lon, lat, title 제목(200자까지), road 도로 이름, start 시작, end 끝(예정), upd 고친 때, addr 지번 주소, tc 유형 코드, gc 등급 코드, rc 지역 코드, sc 출처 코드, lane]] · 때 = YYYY-MM-DD HH:MM · 고친 때가 새 것부터',
           'items': items}
    p = os.path.join(ROOT, 'data', 'utic-ims.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    return len(items), os.path.getsize(p)
if __name__ == '__main__':
    n, sz = bake(); print('UTIC 돌발', n, '건 · 바이트', sz)
