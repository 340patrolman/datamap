# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧑‍🤝‍🧑 위기 청소년을 이어 줄 곳(청소년상담복지센터 · 청소년쉼터 · 학교밖청소년지원센터(꿈드림) · 자립지원관) → data/youth-support.json
#   소유자 2026-10-12 「학교 담당 경찰관이 공공데이터를 충분히 이용할 수 있게」 → 학교·동 카드에서 「가까운 지원기관」을 바로 본다
#   원자료(공공데이터포털 파일 · dgfile.py 로 07_API키/out/dg/<번호>/x.csv): 3084537 성평등가족부_청소년상담복지센터 현황 · 3084536 청소년쉼터 현황 · 15088280 한국청소년상담복지개발원_전국_꿈드림_센터 · 15100267 청소년 자립지원관 현황
#   자리 = 주소를 브이월드 주소 변환(도로명 → 지번)으로 — 캐시 07_API키/out/youthsup/geo.json(다시 돌리면 통신 없음 · 하루 한도를 지번 좌표 변환과 같이 쓴다) · 못 잡은 곳은 좌표 null 로 싣는다
#   전화는 기관 대표번호(원자료 그대로) — 개인 번호가 아니다
#   py -3.12 -X utf8 tools/region/youthsup-bake.py
import csv, io, json, os, re, time, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); DG = os.path.join(KB, 'out', 'dg'); GC = os.path.join(KB, 'out', 'youthsup', 'geo.json')
KINDS = ['청소년상담복지센터', '청소년쉼터', '학교밖청소년지원센터(꿈드림)', '청소년자립지원관']
def rd(pk):
    b = open(os.path.join(DG, pk, 'x.csv'), 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return list(csv.DictReader(io.StringIO(b.decode(e))))
        except Exception: pass
def clean(a):
    a = re.sub(r'^\(\d{5}\)\s*', '', (a or '').strip()); a = re.sub(r'\([^)]*\)', ' ', a); a = re.sub(r'\s+', ' ', a).strip()
    m = re.match(r'(.+?(?:로|길)\s*\d+(?:-\d+)?(?:번길\s*\d+(?:-\d+)?)?)', a.replace(' 길', '길'))
    return (m.group(1) if m else a.split(',')[0]).strip()
def geo(addr, C, key):
    if addr in C: return C[addr]
    for ty in ('road', 'parcel'):
        q = dict(service='address', request='getcoord', version='2.0', crs='epsg:4326', address=addr, refine='true', simple='false', format='json', type=ty, key=key, domain='https://340patrolman.github.io')
        try: r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q), headers={'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8'))['response']
        except Exception: time.sleep(2); continue
        if r.get('status') == 'OK': p = r['result']['point']; C[addr] = [round(float(p['x']), 5), round(float(p['y']), 5)]; return C[addr]
        if 'LIMIT' in json.dumps(r): raise SystemExit('브이월드 하루 한도 — 내일 이어서')
        time.sleep(0.1)
    C[addr] = None; return None
def main():
    key = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']; os.makedirs(os.path.dirname(GC), exist_ok=True); C = json.load(open(GC, encoding='utf-8')) if os.path.exists(GC) else {}
    rows = []
    for r in rd('3084537'): rows.append([0, r['센터명'].strip(), r['시도명'].strip(), r['시군구명'].strip(), r['주소'], r['전화번호_1'].strip(), ''])
    for r in rd('3084536'): rows.append([1, r['시설명'].strip(), r['시도'].strip(), r['시군구'].strip(), r['시설주소'], r['대표전화'].strip(), r['시설유형'].strip()])
    for r in rd('15088280'): rows.append([2, r['센터명'].strip(), r['시도'].strip(), r['시군구'].strip(), (r['주소1'] + ' ' + r['주소2']), r['대표전화번호'].strip(), ''])
    for r in rd('15100267'): rows.append([3, r['시설명'].strip(), r['시도'].strip(), r['시군구'].strip(), r['시설주소'], r['대표전화'].strip(), r['시설유형'].strip()])
    items = []; miss = 0
    for i, (k, nm, sd, sg, addr, tel, sub) in enumerate(rows):
        a = clean(addr); xy = geo(a, C, key)
        if xy is None and a != addr.strip(): xy = geo(re.sub(r'^\(\d{5}\)\s*', '', addr.strip()).split(',')[0].split('(')[0].strip(), C, key)
        miss += 0 if xy else 1; items.append([k, nm, sd, sg, xy[0] if xy else None, xy[1] if xy else None, tel, sub])
        if i % 100 == 0: json.dump(C, open(GC, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(C, open(GC, 'w', encoding='utf-8'), ensure_ascii=False)
    doc = {'schema': 'tg-youth-support/1', 'made': datetime.date.today().isoformat(),
           'source': '공공데이터포털 — 성평등가족부_청소년상담복지센터 현황(3084537) · 청소년쉼터 현황(3084536) · 청소년 자립지원관 현황(15100267) · 한국청소년상담복지개발원_전국_꿈드림_센터(15088280) · 자리 = 브이월드 주소 변환',
           'note': ['위기 청소년을 **이어 줄 곳**이다: 상담복지센터(상담·긴급구조 · 청소년전화 1388) · 쉼터(가출 청소년 보호 — 일시·단기·중장기 · 남·여 구분은 시설 이름에) · 꿈드림(학교 밖 청소년) · 자립지원관(쉼터를 나온 뒤)',
                    '자리는 주소를 좌표로 바꾼 것이다(건물 입구와 어긋날 수 있다) · 좌표를 못 잡은 %d곳은 좌표가 null — 시군구로만 찾는다' % miss,
                    '전화는 원자료의 기관 대표번호다 · 옮긴 곳·문 닫은 곳이 있을 수 있으니 가기 전에 전화로 확인한다 · 밤·휴일에는 청소년전화 1388(24시간)',
                    '쉼터는 정원·성별·나이 조건이 있다 — 받아 줄 수 있는지는 전화로 묻는다(이 자료에 빈자리는 없다)'],
           'fields': {'kinds': '갈래(items 의 갈래 번호 차례)', 'items': '[[갈래 번호, 이름, 시도, 시군구, 경도|null, 위도|null, 대표전화, 유형(쉼터: 일시·단기·중장기 / 자립지원관: 이용형·혼합형 — 없으면 빈칸)]]'},
           'kinds': KINDS, 'items': items}
    p = os.path.join(ROOT, 'data', 'youth-support.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    import collections; print('바이트', os.path.getsize(p), '곳', len(items), '좌표 없음', miss, collections.Counter(KINDS[i[0]] for i in items)); print([i for i in items if i[3] in ('서초구', '강남구')])
    print('못 잡은 주소', [r[4][:50] for r, i in zip(rows, items) if i[4] is None][:12])
if __name__ == '__main__': main()
