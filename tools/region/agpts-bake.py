# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏛 기관 자리·연락처(소유자 2026-10-10 「구청·주민센터·소방서·세무서·교육청·등기소·법원 등도 찾아서 내용 넣자」) 1차 = 소방서·119안전센터 · 읍면동 주민센터(행정복지센터)
#   원자료(공공데이터포털 파일데이터 · tools/region/dgfile.py <번호> 로 07_API키/out/dg/<번호>/ 에 받음 · 2026-10-10):
#     15048243 소방청_시도 소방서 현황_20260701(본부·소방서·주소·전화) · 15065056 소방청_119안전센터 현황_20260701(소속 소방서·주소·전화)
#     15138232 소방청_전국소방서 좌표현황_20240901(소방서·안전센터 위도·경도 — 이름으로 맞는 것만 붙인다 · 없으면 자리 빈칸) · 15059715 행정안전부_읍면동 하부행정기관 현황_20251231(주민센터 우편번호·주소 — 전화·좌표 없음)
#   소방서 관할 = 그 소방서 119안전센터 주소의 시·군·구를 모은 「근사」다(법정 관할은 시·도 조례 — 아직 대조하지 않았다) · 주민센터 = 이름으로 행정동 코드에 붙인다(못 붙인 곳은 수만 적는다)
#   py -3.12 -X utf8 tools/region/agpts-bake.py → data/agency-pts.json
import csv, io, json, os, re, glob, zipfile, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg'); R = os.path.join(ROOT, 'data', 'r')
def rows(pk, pick=None):
    d = os.path.join(DG, pk); f = [x for x in os.listdir(d) if not x.startswith('_')][0]; b = open(os.path.join(d, f), 'rb').read()
    if f.endswith('.zip'):
        z = zipfile.ZipFile(io.BytesIO(b)); i = sorted(z.infolist(), key=lambda i: i.filename)[-1] if not pick else [i for i in z.infolist() if pick in i.filename][0]; b = z.read(i)
    for enc in ('utf-8-sig', 'cp949'):
        try: t = b.decode(enc); break
        except UnicodeDecodeError: continue
    return list(csv.DictReader(io.StringIO(t)))
def nk(s): return re.sub(r'[\s\-·()]|119|안전센터|소방서', '', s or '')
def sgg(addr):   # 주소 → 「시도 시군구」 낱말(시 아래 구가 있으면 구까지)
    p = (addr or '').split()
    if len(p) < 2: return None
    if p[1][-1:] not in '시군구': return None
    return ' '.join(p[:3]) if len(p) > 2 and p[1].endswith('시') and p[2].endswith('구') else ' '.join(p[:2])

def main():
    XY = {}
    for r in rows('15138232'):
        try: la, lo = float(r['X좌표']), float(r['Y좌표'])
        except (ValueError, KeyError): continue
        if 33 < la < 39 and 124 < lo < 132: XY[nk(r['소방서 및 안전센터명'])] = [round(la, 6), round(lo, 6)]
    ST = collections.OrderedDict()
    for r in rows('15048243'):
        n = r['소방서'].strip(); xy = XY.get(nk(n)) or [None, None]
        ST[(r['본부명'].strip()[:2], n)] = {'n': n, 'hq': r['본부명'].strip(), 'addr': r['주소'].strip(), 'tel': r['전화번호'].strip(), 'lat': xy[0], 'lon': xy[1], 'c': [], 'sgg': collections.Counter()}
    nc = 0; nox = 0; orphan = 0
    for r in rows('15065056'):
        n = r['119안전센터명'].strip(); key = (r['시도본부'].strip()[:2], r['소방서명'].strip()); s = ST.get(key)
        if s is None:
            c = [v for (h, sn), v in ST.items() if sn == key[1]]; s = c[0] if len(c) == 1 else None
        if s is None: orphan += 1; continue
        xy = XY.get(nk(s['n']) + nk(n)) or XY.get(nk(n)) or [None, None]
        if xy[0] is None: nox += 1
        s['c'].append([n, r['주소'].strip(), r['전화번호'].strip(), xy[0], xy[1]]); nc += 1
        g = sgg(r['주소'].strip())
        if g: s['sgg'][g] += 1
    for s in ST.values():
        g = sgg(s['addr'])
        if g: s['sgg'][g] += 1
        s['sgg'] = [k for k, _ in s['sgg'].most_common()]
    # 주민센터 → 행정동 코드
    DN = collections.defaultdict(dict)
    for f in glob.glob(os.path.join(R, '[0-9]' * 5, 'profile.json')):
        p = json.load(open(f, encoding='utf-8'))
        for k, v in p['dong'].items(): DN[re.sub(r'\s', '', p['name'])][re.sub(r'[\s·.,]', '', v['이름'])] = k
    JM = {}; nomatch = 0; tot = 0
    for r in rows('15059715'):
        tot += 1; g = re.sub(r'\s', '', r['시군구']); nm = re.sub(r'[\s·.,]', '', re.sub(r'(주민센터|행정복지센터|주민자치센터|읍사무소|면사무소|동사무소|사무소)\s*$', '', r['읍면동'].strip()))
        k = (DN.get(g) or {}).get(nm)
        if not k:   # 시 아래 구가 생기거나 바뀐 곳(화성시 → 화성시만세구 …) — 그 시로 시작하는 구들에서 이름이 하나뿐이면 그것
            c = [d[nm] for gg, d in DN.items() if gg.startswith(g) and nm in d]; k = c[0] if len(c) == 1 else None
        if not k: nomatch += 1; continue
        JM[k] = [r['읍면동'].strip(), str(r['우편번호']).strip().zfill(5), r['주소'].strip()]
    doc = {'schema': 'tg-agency-pts/1', 'made': datetime.date.today().isoformat(),
           'source': {'fire': '소방청_시도 소방서 현황_20260701(공공데이터포털 15048243) · 소방청_119안전센터 현황_20260701(15065056) · 자리 = 소방청_전국소방서 좌표현황_20240901(15138232 · 이름이 맞는 것만)',
                      'jumin': '행정안전부_읍면동 하부행정기관 현황_20251231(공공데이터포털 15059715) — 우편번호·주소(전화·좌표는 이 자료에 없다)'},
           'note': ['소방서가 맡는 시·군·구(sgg)는 그 소방서와 119안전센터 주소를 모은 근사다 — 법정 관할(시·도 조례)을 대조한 것이 아니다', '자리(lat·lon)가 null 인 곳은 좌표 자료에 같은 이름이 없는 곳이다(주소는 있다) — 지도에 점을 찍지 말고 목록에만',
                    '주민센터는 이름으로 행정동 코드에 붙였다 — 못 붙인 %d곳은 빠졌다(전체 %d)' % (nomatch, tot), '구청·시청·군청 · 등기소 · 검찰청 · 세무서·법원·교육지원청 청사 자리는 아직 없다'],
           'fields': 'fire[{n 소방서, hq 본부, addr, tel, lat, lon, sgg[맡는 시군구(근사)…], c[[119안전센터, 주소, 전화, lat, lon]…]}] · jumin{행정동 8자리: [이름, 우편번호, 주소]}',
           'fire': list(ST.values()), 'jumin': JM}
    p = os.path.join(ROOT, 'data', 'agency-pts.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('소방서', len(ST), '· 자리 있음', sum(1 for s in ST.values() if s['lat']), '· 안전센터', nc, '· 자리 없음', nox, '· 소방서 못 맞춘 센터', orphan, '· 주민센터', len(JM), '/', tot, '· 바이트', os.path.getsize(p))
    for s in ST.values():
        if s['n'] in ('서초소방서', '화성소방서'): print(s['n'], s['tel'], s['lat'], s['lon'], s['sgg'], len(s['c']), s['c'][:2])
    print(JM.get('11650621'), JM.get('41591253'))
if __name__ == '__main__': main()
