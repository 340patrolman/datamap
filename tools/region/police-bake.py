# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.8.0 — 🚓 전국 경찰서 관할(법정) · 지구대·파출소 자리
#   관할 = 「경찰청과 그 소속기관 직제 시행규칙」 별표2(2026.8.31 시행) × 행정동 경계(SGIS/admdongkor 2026-07) — T-Book v22.80 이 만든 표(13_관할경계/결과/labmap.tsv)
#          행정동마다 관할 경찰서(두 서가 번지로 나눠 맡는 동은 둘 다 — 「경계」) · 청사 = 경찰민원24 좌표·대표번호(13_관할경계/원자료/ps_pts.csv)
#   지구대·파출소 = 경찰청 「전국 지구대 파출소 주소 현황」(공공데이터포털 15077036 · 2025-12-31 · 2,047곳) → 주소를 브이월드 좌표로
#   ⚠ 지구대·파출소 관할 경계는 공개 자료가 없다 → 자리만 · 「가장 가까운 지구대」는 근사(관할이 아님)라고 밝힌다
#   py -3.12 -X utf8 tools/region/police-bake.py → data/police.json
import csv, json, os, time, urllib.request, urllib.parse, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); J = os.path.join(KB, '13_관할경계'); OUT = os.path.join(KB, '07_API키', 'out', 'police')

def geo(addr, vk, cache):
    if addr in cache: return cache[addr]
    res = None
    for typ in ('road', 'parcel'):
        q = {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326', 'address': addr, 'refine': 'true', 'simple': 'false', 'format': 'json', 'type': typ, 'key': vk}
        for i in range(3):
            try:
                j = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q), headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read().decode())['response']; break
            except Exception: time.sleep(2); j = {}
        if j.get('status') == 'OK': p = j['result']['point']; res = [round(float(p['y']), 6), round(float(p['x']), 6)]; break
    cache[addr] = res; time.sleep(0.15); return res

def main():
    vk = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['vworld']
    st = list(csv.DictReader(open(os.path.join(J, '원자료', 'ps_pts.csv'), encoding='utf-8-sig')))
    stations = [[int(r['i']), r['nm'], float(r['la']), float(r['lo']), r['tel'], r['sido']] for r in st]
    labels = [l.strip() for l in open(os.path.join(J, '결과', 'labels.txt'), encoding='utf-8-sig')]
    for i, r in enumerate(csv.DictReader(open(os.path.join(J, '결과', 'extra.csv'), encoding='utf-8-sig'))):   # 청사 좌표가 없어 이름만(울산북부·청주청원·태안 — T-Book JUR_X · 번호 1000부터)
        stations.append([1000 + i, r['nm'], None, None, '', r['sido']])
    dong = {}
    for l in open(os.path.join(J, '결과', 'labmap.tsv'), encoding='utf-8-sig'):
        a = l.strip().split('\t')
        if len(a) == 2: dong[a[0][:8]] = int(a[1])
    # v2.112.1 서초구 반포동 — 별표2 는 번지로만 나눔 → 소유자(서초서 교통관리계) 현장 기준(2026-10-04 말씀 · 2026-10-10 「이 내용 맞네」 · polcard-bake.py 와 같은 기준): 반포본동·반포2동 = 방배서(27) · 반포1동·반포3동 = 서초서(23) · 반포4동 = 반포대로로 갈려 「경계」 그대로(지도는 jur-seocho split 선)
    FIELD = {'11650550': '27', '11650570': '27', '11650560': '23', '11650580': '23'}
    for k8, lab in FIELD.items():
        if lab not in labels: labels.append(lab)
        if k8 in dong: dong[k8] = labels.index(lab)
    byname = {re.sub(r'경찰서$', '', s[1]): s[0] for s in stations}
    cp = os.path.join(OUT, 'geo.json'); cache = json.load(open(cp, encoding='utf-8')) if os.path.exists(cp) else {}
    rows = list(csv.reader(open(os.path.join(OUT, 'pbox.csv'), encoding='cp949')))[1:]; pbox = []; miss = []; nosm = 0
    op = os.path.join(OUT, 'osm_police.json'); OSM = json.load(open(op, encoding='utf-8')) if os.path.exists(op) else []   # 브이월드 하루 한도에 걸린 곳은 OSM 이름으로(tools/region/osm-police.py)
    nz = lambda x: re.sub(r'\s|\(.*?\)', '', x or '')
    import math
    def osm_match(nm, kind, st):
        key = nz(nm) + kind; c = [o for o in OSM if nz(o[0]).endswith(key)]
        if st and st[2] is None: st = None   # 청사 좌표 없는 서
        if st and c: c = [o for o in c if math.hypot((o[2] - st[3]) * 88.8, (o[1] - st[2]) * 111) <= 40]
        if not c: return None
        if st: c.sort(key=lambda o: math.hypot((o[2] - st[3]) * 88.8, (o[1] - st[2]) * 111))
        return [c[0][1], c[0][2]]
    for k, r in enumerate(rows):
        _, cheong, ps, nm, kind, addr = r[:6]; addr = re.sub(r'\s+', ' ', addr).strip()
        g = geo(addr, vk, cache); src = 'vw'
        if not g:
            g = osm_match(nm, kind, next((x for x in stations if x[0] == byname.get(ps, -1)), None)); src = 'osm'
            if g: nosm += 1
        if k % 200 == 0: json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False); print('주소', k, flush=True)
        if not g: miss.append(nm + ' ' + addr); continue
        pbox.append([nm, 0 if kind == '지구대' else 1, ps, g[0], g[1], addr, byname.get(ps, -1)] + ([1] if src == 'osm' else []))
    json.dump(cache, open(cp, 'w', encoding='utf-8'), ensure_ascii=False)
    doc = {'schema': 'tg-police/1',
           'source': '관할 = 경찰청과 그 소속기관 직제 시행규칙 별표2(2026.8.31 시행 · 국가법령정보) × 행정동 경계(통계청 SGIS · 가공 admdongkor 2026-07 · CC BY 4.0) · 청사 좌표·대표번호 = 경찰민원24(2026-09-09) · 지구대·파출소 = 경찰청 「전국 지구대 파출소 주소 현황」(공공데이터포털 15077036 · 2025-12-31) · 자리 = 브이월드 주소 좌표',
           'note': '행정동 단위 근사 — 별표2 가 번지로 나눈 동은 「경계」(labels 에 두 서) · 서초구 반포동 다섯 행정동은 소유자 현장 기준(반포본동·반포2동 방배서 · 반포1동·반포3동 서초서 · 반포4동 반포대로로 갈림 = 경계) · 지구대·파출소 관할 경계는 공개 자료가 없어 자리만(가장 가까운 지구대 = 근사)',
           'fields': 'stations = [번호, 이름, 위도, 경도, 대표번호, 시도청] · labels = 관서 번호 묶음(「1,4」 = 두 서가 나눠 맡음) · dong = {행정동 8자리: labels 번호} · pbox = [이름, 0 지구대·1 파출소, 경찰서, 위도, 경도, 주소, 경찰서 번호(, 1 = 자리를 OSM 이름으로 잡음)]',
           'stations': stations, 'labels': labels, 'dong': dong, 'pbox': pbox}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'police.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('경찰서', len(stations), '행정동', len(dong), '지구대·파출소', len(pbox), '/', len(rows), 'OSM 이름으로 채움', nosm, '좌표 못 찾음', len(miss), miss[:8], '바이트', os.path.getsize(os.path.join(ROOT, 'data', 'police.json')))

if __name__ == '__main__': main()
