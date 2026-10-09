# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.95.0 — 🏠 시도·시군구 집값 기준표 → data/home-ref.json (🧭 유력·쇠퇴 업종 종합의 「소득·자산」 줄을 전국으로)
#   원자료 = 각 구 r/<구>/home.json 의 dong.a(아파트 매매 [건수, ㎡당 중앙값(만 원 · 전용), …]) — 국토교통부 실거래가(home-bake.py 가 구움)
#   계산: 매매 5건 이상인 행정동만 · 시도마다 동 ㎡당의 아래 20% 경계·가운데·위 20% 경계 · 시군구마다 동 가운데값(건수로 가중하지 않은 동 중앙)
#   py -3.12 -X utf8 tools/region/homeref-bake.py [home.json 들을 찾을 glob ...]   (기본 data/r/*/home.json — publish-data 전 로컬 빌드 출력)
import glob, json, os, sys, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PATS = sys.argv[1:] or [os.path.join(ROOT, 'data', 'r', '*', 'home.json')]
OUTF = os.path.join(ROOT, 'data', 'home-ref.json')
MINN = 5

def q(a, p):
    a = sorted(a); i = (len(a) - 1) * p; lo = int(i); hi = min(lo + 1, len(a) - 1)
    return a[lo] + (a[hi] - a[lo]) * (i - lo)

def main():
    fs = sorted({f for p in PATS for f in glob.glob(p)})
    if not fs: raise SystemExit('home.json 없음: %s' % PATS)
    sd, sdc, gu, src = {}, {}, {}, ''
    for f in fs:
        d = json.load(open(f, encoding='utf-8')); g = str(d.get('gu') or os.path.basename(os.path.dirname(f)))
        src = src or d.get('source', '')
        v = [x['a'][1] for x in (d.get('dong') or {}).values() if x.get('a') and x['a'][0] >= MINN and x['a'][1]]
        if v: gu[g] = [len(v), round(statistics.median(v))]; sd.setdefault(g[:2], []).extend(v); continue
        # 동 칸이 빈 구(지번 좌표 → 행정동 잇기가 밀린 곳 · 2026-10 강원·전북) = 아파트 단지(cx) ㎡당으로 시군구 가운데 · 시도 분포도 단지 기준으로 따로
        c = [x[8][1] for x in (d.get('cx') or {}).values() if x and x[0] == 0 and x[8] and x[8][0] >= 3 and x[8][1]]
        if c: gu[g] = [len(c), round(statistics.median(c)), 'cx']; sdc.setdefault(g[:2], []).extend(c)
    doc = {'schema': 'tg-homeref/1', 'source': src, 'min_deals': MINN,
           'fields': 'sido = {시도 2자리: [동 수, 아래 20% 경계, 가운데, 위 20% 경계]} · gu = {시군구 5자리: [동 수, 동 가운데]} — 아파트 매매 ㎡당(만 원 · 전용) 동 중앙값의 분포',
           'note': '매매 %d건 이상인 행정동만 · 아파트만(오피스텔·연립·단독 뺌) · 집값은 소득이 아니라 자산의 대리 지표다' % MINN,
           'sido': {k: [len(v), round(q(v, .2)), round(q(v, .5)), round(q(v, .8))] + ([] if k in sd else ['cx']) for k, v in sorted(list(sd.items()) + [(k2, v2) for k2, v2 in sdc.items() if k2 not in sd])}, 'gu': dict(sorted(gu.items()))}
    doc['fields'] += ' · 끝에 \'cx\' = 동 칸이 비어 아파트 단지(매매 3건 이상) ㎡당으로 셈(동 기준과 바로 견주지 않는다)'
    json.dump(doc, open(OUTF, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('파일 %d · 시군구 %d · 시도 %d → %s (%.1f KB)' % (len(fs), len(gu), len(sd), OUTF, os.path.getsize(OUTF) / 1024))
    for k, v in doc['sido'].items(): print(' ', k, v)

if __name__ == '__main__':
    main()
