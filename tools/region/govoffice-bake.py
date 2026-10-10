# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏛 시청·군청·구청·도청 자리(소유자 2026-10-10 「경찰서와 파출소 소방서 구청 시청 등은 각각의 이미지를 넣자 · 전국에 표현」) → data/gov-offices.json
#   CLAUDE.md 「막힌 것 ①」(구청·시청 좌표 — 도로명주소 전자지도는 신청·본인 인증)을 다른 길로: 브이월드 검색 API(장소 · 키 keys.json vworld)에서 「○○구청」을 찾아
#     분류가 「지방행정기관」이고 주소에 그 시군구 이름이 든 것만 받는다(없으면 싣지 않는다 — 자리를 지어 넣지 않는다)
#   시군구 목록 = data/r/index.json(256 시군구 · 구 코드) + 시도 17(도청·시청)
#   py -3.12 -X utf8 tools/region/govoffice-bake.py   (원자료 07_API키/out/govoffice/raw.json · 이어 받기 됨 · 하루 한도에 닿으면 멈춘다)
import json, os, time, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'govoffice'); os.makedirs(OUT, exist_ok=True)
SIDO = {'11': '서울특별시', '26': '부산광역시', '27': '대구광역시', '28': '인천광역시', '29': '광주광역시', '30': '대전광역시', '31': '울산광역시', '36': '세종특별자치시', '41': '경기도', '51': '강원특별자치도', '43': '충청북도', '44': '충청남도', '52': '전북특별자치도', '46': '전라남도', '47': '경상북도', '48': '경상남도', '50': '제주특별자치도'}
def search(q, K):
    u = 'https://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:4326&size=10&page=1&type=place&format=json&errorformat=json&query=%s&key=%s&domain=https://340patrolman.github.io' % (urllib.parse.quote(q), K)
    j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://340patrolman.github.io/'}), timeout=40).read().decode('utf-8', 'replace'), strict=False)['response']   # 응답 글에 제어 문자가 섞인 줄이 있다
    if j.get('status') == 'ERROR': raise SystemExit('브이월드 오류 — ' + json.dumps(j.get('error'), ensure_ascii=False)[:200])
    return (j.get('result') or {}).get('items', [])
def main():
    K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['vworld']
    G = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus']; rp = os.path.join(OUT, 'raw.json'); RAW = json.load(open(rp, encoding='utf-8')) if os.path.exists(rp) else {}
    want = []
    for g in G:
        nm = g['name']; last = nm.split()[-1]; kind = '구청' if last.endswith('구') else ('군청' if last.endswith('군') else '시청')
        want.append([g['gu'], SIDO.get(g['sido'], ''), nm, kind, (nm if ' ' in nm else nm) + '청', last])
        if ' ' in nm and nm.split()[0] + '청' not in [w[4] for w in want]: want.append([g['gu'][:4] + '0', SIDO.get(g['sido'], ''), nm.split()[0], '시청', nm.split()[0] + '청', nm.split()[0]])   # 일반구가 있는 시의 시청
    for c, s in SIDO.items(): want.append([c, s, s, '도청' if s.endswith('도') else '시청', s.replace('특별자치도', '특별자치도').replace('광역시', '광역시') + '청', s])
    import re
    def variants(sido, nm, q):   # 검색어 후보 — 이름이 겹치는 구(동구·중구…)는 시도 이름을 붙여, 일반구(수원시장안구)는 구 이름만으로도
        v = [q]; mm = re.match(r'^(.+시)(.+구)$', nm.replace(' ', ''))
        if mm: v += [mm.group(2) + '청', mm.group(1) + ' ' + mm.group(2) + '청']
        if sido and nm != sido: v += [sido[:2] + ' ' + nm.replace(' ', '') + '청', sido + ' ' + nm + '청']
        out = []
        for x in v:
            if x not in out: out.append(x)
        return out
    for code, sido, nm, kind, q, last in want:
        for x in variants(sido, nm, q):
            if x in RAW: continue
            RAW[x] = search(x, K); time.sleep(0.12)
    json.dump(RAW, open(rp, 'w', encoding='utf-8'), ensure_ascii=False)
    items = []; miss = []
    for code, sido, nm, kind, q, last in want:
        mm = re.match(r'^(.+시)(.+구)$', nm.replace(' ', '')); gu = mm.group(2) if mm else nm.split()[-1]; city = mm.group(1) if mm else ''
        titles = set([q, q.replace(' ', ''), gu + '청', nm + '청', nm.replace(' ', '') + '청']); ok = []
        for x in variants(sido, nm, q):
            for it in RAW.get(x, []):
                cat = it.get('category') or ''; ad = (it.get('address') or {}); addr = ad.get('road') or ad.get('parcel') or ''
                if not cat.startswith('지방행정기관') or (it.get('title') or '').replace(' ', '') not in set(t.replace(' ', '') for t in titles) or not addr: continue
                if len(code) > 2 and (gu not in addr or (city and city not in addr) or (sido and sido[:2] not in addr and sido not in addr)): continue
                if len(code) == 2 and sido[:2] not in addr: continue
                ok.append((0 if ad.get('road') else 1, it, addr))
        if not ok: miss.append((sido[:2] + ' ' if len(code) > 2 else '') + nm + '청'); continue
        ok.sort(key=lambda z: z[0]); it, addr = ok[0][1], ok[0][2]
        items.append([kind, nm if len(code) > 2 else sido, sido, round(float(it['point']['x']), 6), round(float(it['point']['y']), 6), addr, code, 0])
    doc = {'schema': 'tg-gov-offices/1', 'made': datetime.date.today().isoformat(),
           'source': '브이월드 검색 API(장소 · 국토교통부 공간정보 오픈플랫폼) — 분류 「지방행정기관」 · 시군구 목록 = data/r/index.json',
           'note': ['청사 이름으로 찾아, 분류가 지방행정기관이고 주소에 그 시군구 이름이 든 것만 실었다 — 찾지 못한 곳은 miss 에 있다(자리를 지어 넣지 않았다)',
                    '본청 한 곳만(별관·제2청사·민원동은 싣지 않았다) · 청사를 옮긴 곳은 검색 자료가 옛 자리일 수 있다',
                    '마지막 칸 1 = 검색 결과에 주소가 비어 있어 이름·분류만으로 고른 곳(같은 이름의 다른 곳일 수 있다 — 확인 필요)',
                    '전화번호·민원 시간은 이 자료에 없다 · 주민센터·읍면사무소는 data/agency-pts.json'],
           'fields': 'items[[갈래(도청·시청·군청·구청), 이름, 시도, 경도, 위도, 주소, 구 코드(시도는 두 자리 · 일반구가 있는 시의 시청은 넷째 자리까지 + 0), 주소 없이 고름 1]] · miss[찾지 못한 청사 이름]',
           'miss': miss, 'items': items}
    p = os.path.join(ROOT, 'data', 'gov-offices.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    import collections
    print('찾은 곳', len(items), collections.Counter(x[0] for x in items), '· 못 찾은 곳', len(miss), miss[:40], '· 주소 없이 고른 곳', sum(x[7] for x in items), '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
