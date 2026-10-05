# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.5.0 — 점 자료를 250m 국가표준격자 칸으로 센다(전국 확장 설계서 Phase 1 「점 데이터는 좌표로 격자에 넣는다」)
#   이미 구운 구 파일만 다시 읽는다(새로 받는 자료 없음): 상가(stores · 대분류) · 안전(safety · 단속 카메라·보호구역·안심 시설·AED…) ·
#   생활시설(fac pts · 어린이집·유치원·경로당·학원·학교·관공서) · 정류장·역(transit · 하루 승차) · 사망사고(taas10 fatal · 한 건씩)
#   칸은 구가 아니라 칸 번호로 모은 뒤 grid.json(가장 넓게 걸친 동의 구) 파일에 나눈다 → 같은 칸이 두 파일에 없다
#   py -3.12 -X utf8 tools/region/pts250-bake.py → data/r/<구>/pts250.json (tg-pts250/1)
import json, os, collections, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = importlib.util.spec_from_file_location('g250', os.path.join(ROOT, 'tools', 'region', 'grid250.py')); G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)
R = os.path.join(ROOT, 'data', 'r')

def main():
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); SI = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8'))
    BIG = [c[1] for c in SI['cls']]
    gu_of = {}
    for g in IX['gus']:
        for c in json.load(open(os.path.join(R, g['gu'], 'grid.json'), encoding='utf-8'))['cells']: gu_of[c[0]] = g['gu']
    C = collections.defaultdict(lambda: collections.defaultdict(lambda: 0)); ST = collections.defaultdict(collections.Counter); NM = collections.defaultdict(list)
    def put(lat, lon, key, n=1):
        k = G.code_ll(lat, lon); C[k][key] += n; return k
    for g in IX['gus']:
        d = os.path.join(R, g['gu'])
        f = os.path.join(d, 'stores.json')
        if os.path.exists(f):
            j = json.load(open(f, encoding='utf-8')); O, K = j['o'], j['k']
            for q in j['pts']:
                k = G.code_ll(O[1] + q[1] / K[1], O[0] + q[0] / K[0]); ST[k][BIG[q[2]]] += 1; C[k]['st'] += 1
        f = os.path.join(d, 'safety.json')
        if os.path.exists(f):
            j = json.load(open(f, encoding='utf-8'))
            for c in j.get('cam', []): put(c['lat'], c['lon'], 'cam')
            for c in j.get('sz', []): put(c['lat'], c['lon'], 'sz')
            for key, arr in (j.get('items') or {}).items():
                for c in arr:
                    if isinstance(c, list) and len(c) >= 2 and isinstance(c[0], (int, float)): put(c[0], c[1], key)
        f = os.path.join(d, 'fac.json')
        if os.path.exists(f):
            j = json.load(open(f, encoding='utf-8'))
            for key, arr in (j.get('pts') or {}).items():
                for c in arr:
                    if isinstance(c, list) and len(c) >= 2 and isinstance(c[0], (int, float)): put(c[0], c[1], key)
        f = os.path.join(d, 'transit.json')
        if os.path.exists(f):
            j = json.load(open(f, encoding='utf-8'))
            for b in j.get('bus', []): k = put(b[3], b[2], 'bus'); C[k]['bon'] += sum(b[4])
            for s in j.get('sub', []): k = put(s[3], s[2], 'subn'); C[k]['son'] += sum(s[4]); NM[k].append(s[0])
        f = os.path.join(d, 'taas10.json') if g['gu'] != '11650' else os.path.join(ROOT, 'data', 'taas10-seocho.json')
        if os.path.exists(f):
            for x in json.load(open(f, encoding='utf-8'))['fatal']: k = put(x[16], x[17], 'fat'); C[k]['dead'] += x[12]
    per = collections.defaultdict(dict); lost = 0
    for k, v in C.items():
        gu = gu_of.get(k)
        if not gu: lost += 1; continue
        o = dict(v)
        if k in ST: o['stb'] = dict(ST[k].most_common(6))
        if k in NM: o['stn'] = sorted(set(NM[k]))
        per[gu][k] = o
    gb = {}
    for gu, cells in per.items():
        doc = {'schema': 'tg-pts250/1', 'gu': gu,
               'source': '이 지도에 구운 점 자료를 250m 국가표준격자 칸으로 셈 — 상가 = 소상공인시장진흥공단(202606) · 안전 = 표준데이터·서울시·경기 · 생활시설 = 서울시·경기·교육청·OSM · 정류장 = 서울시·경기 교통카드 · 사망사고 = TAAS(2016~2025)',
               'fields': 'st 상가 수 · stb 대분류 상위 6 · cam 단속 카메라 · sz 어린이보호구역 대상 · srItem/srSvc/aed… 안전 시설 · cc 어린이집 · kg 유치원 · kyr 경로당 · aca 학원 · edu 학교 · gov 관공서 · bus 정류장 수 · bon 하루 승차 합 · subn 역 · son 역 하루 승차 · stn 역 이름 · fat 사망사고 건 · dead 사망자',
               'cells': cells}
        pth = os.path.join(R, gu, 'pts250.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['pts250'] = gb[g['gu']]
    IX['layers']['pts250'] = '점 자료 250m 칸 집계(상가·안전·생활시설·정류장·사망사고)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('칸', sum(len(v) for v in per.values()), '구', len(per), '격자 밖 칸', lost, '바이트', sum(gb.values()))

if __name__ == '__main__': main()
