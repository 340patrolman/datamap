# -*- coding: utf-8 -*-
# 교차로 CCTV 목록 — 경찰청 도시교통정보센터(UTIC) 개방데이터 cctvOpenData.do(열쇠 keys.json utic · 등록 IP 에서만 동작 · 2026-10-15 소유자 「권고대로」 = 목록만 지도 · 영상은 TOPIS 공식 사이트)
#   fetch  → 07_API키/out/utic/cctv_<날짜>.html (열쇠는 지워서 저장) — 이 PC 에서만 된다
#   build  → 07_API키/out/utic/cctv_seoul.json — 서울교통정보센터 카메라의 번호·이름 + 같은 이름 교차로(data/onto-int.json) 좌표 맞대기(이름이 하나로 맞을 때만 · 근사 C)
#   build --publish → data/cctv-utic-seoul.json (지도용) — ⚠ UTIC 이용 조건(메일 첨부 「2026 도시교통정보센터 개방데이터 세부내용.hwp」)을 확인한 뒤에만
#   영상 주소·열쇠는 어디에도 싣지 않는다 · 영상은 정차 중·동승자만(지도 쪽 규칙)
#   py -3.12 -X utf8 tools/region/utic-cctv-bake.py fetch|build [--publish]
import sys, os, re, json, glob, datetime, urllib.request, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'utic')
TERMS_OK = False   # 이용 조건 확인 뒤 True 로(확인한 날·근거를 옆에 적는다)


def fetch():
    K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['utic']
    b = urllib.request.urlopen(urllib.request.Request('https://www.utic.go.kr/guide/cctvOpenData.do?key=' + K, headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read().decode('utf-8', 'ignore').replace(K, '***')
    os.makedirs(OUT, exist_ok=True); p = os.path.join(OUT, 'cctv_%s.html' % datetime.date.today().strftime('%Y%m%d'))
    open(p, 'w', encoding='utf-8').write(b); print('받음', p, len(b))


def norm(s):
    return re.sub(r'[\s·.\-()（）]|사거리$|삼거리$|교차로$|오거리$|R$', '', s)


def build(publish):
    src = sorted(glob.glob(os.path.join(OUT, 'cctv_*.html')))[-1]
    b = open(src, encoding='utf-8').read()
    rows = re.findall(r"test\('([A-Z0-9]+)'\)\">(\d+)\.([^<]+)</a>\s*</td>\s*<td[^>]*>\s*<a[^>]*window\.open\('([^']*)'\)\">([^<]+)</a>", b)
    cnt = collections.Counter(r[4] for r in rows)
    seoul = [r for r in rows if r[4].strip() == '서울교통정보센터']
    ints = json.load(open(os.path.join(ROOT, 'data', 'onto-int.json'), encoding='utf-8'))['items']
    byn = collections.defaultdict(list)
    for x in ints:
        byn[norm(x[1])].append(x)
    out, miss = [], []
    for cid, no, nm, url, ctr in seoul:
        c = byn.get(norm(nm), [])
        if len(c) == 1:
            x = c[0]; out.append({'id': cid, 'no': int(no), 'nm': nm.strip(), 'lat': x[2], 'lon': x[3], 'int': 'INT-%s' % x[0], 'gu': x[6], 'how': '이름 맞대기(C)'})
        else:
            out.append({'id': cid, 'no': int(no), 'nm': nm.strip(), 'lat': None, 'lon': None, 'int': None, 'gu': None, 'how': '자리 못 찾음' if not c else '같은 이름 %d곳' % len(c)}); miss.append(nm.strip())
    doc = {'schema': 'tg-cctv-utic/1', 'made': datetime.date.today().isoformat(),
           'source': '경찰청 도시교통정보센터(UTIC) 개방데이터 CCTV 목록(cctvOpenData.do) — 서울교통정보센터(TOPIS) 카메라 · %s' % os.path.basename(src),
           'fields': '[{id UTIC 카메라 번호, no 목록 번호, nm 이름, lat, lon, int 교차로 ID, gu 시군구, how 자리 잡은 법}] — 좌표는 원자료에 없어 같은 이름의 교차로(data/onto-int.json)에 맞댄 근사',
           'note': ['영상은 TOPIS 공식 누리집(topis.seoul.go.kr)에서 본다 — 영상 주소·열쇠는 싣지 않는다', '영상은 정차 중·동승자만 · 출동 첫 화면 자동 재생 금지', '이름이 같은 교차로가 둘 이상이거나 없으면 좌표 없음(지어 고르지 않음)'],
           'n': {'all': len(rows), 'seoul': len(seoul), 'placed': sum(1 for o in out if o['lat']), 'centers': len(cnt)}, 'items': out}
    p = os.path.join(OUT, 'cctv_seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('전국', len(rows), '· 센터', len(cnt), '· 서울', len(seoul), '· 자리 잡음', doc['n']['placed'], '·', p)
    six = collections.Counter(o['gu'] for o in out if o['gu'] in ('11650', '11680', '11590', '11620', '11170', '11710'))
    print('여섯 구 자리 잡은 카메라', dict(six)); print('못 잡은 것 앞 20', miss[:20])
    if publish:
        if not TERMS_OK:
            print('❌ 이용 조건 확인 전 — data/ 에 쓰지 않는다(TERMS_OK = False)'); return
        json.dump(doc, open(os.path.join(ROOT, 'data', 'cctv-utic-seoul.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        print('지도용으로 씀 data/cctv-utic-seoul.json')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a and a[0] == 'fetch':
        fetch()
    else:
        build('--publish' in a)
