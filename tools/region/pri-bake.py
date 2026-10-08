# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.89.0 — 🚓 지금 순찰할 칸(250m) 기준표: 시도 안 백분위 눈금(분위수 101개)
#   소유자 2026-10-08 「데이터를 어떻게 조합해야 더 좋은 결과가 나올까」 → 단위가 다른 지표는 그대로 더하지 않고
#   같은 시도 칸들 사이의 백분위(0~1)로 바꾼 뒤 같은 무게로 평균한다. 칸 값은 지도가 이미 받는 taas250·live250 을 그대로 쓰고,
#   여기서는 「어느 값이 몇 백분위인가」를 재는 눈금만 굽는다(새 칸 파일 없음 · 약 20KB).
#   성분: ksi = 사망자+중상자(10년) · rec = 최근 3년(2023~2025) 사고 · b0~b3 = 시간대 사고(0~6 · 6~12 · 12~18 · 18~24시)
#         · wd/we = 서울 생활인구(평일/주말 0~23시 · 서울만)
#   눈금 = 0 이 아닌 값들의 분위수(0·1·…·100%) — 0 인 칸은 백분위 0.
#   py -3.12 -X utf8 tools/region/pri-bake.py
import json, os, glob, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')

def q101(vals):
    v = sorted(x for x in vals if x > 0)
    if not v: return []
    n = len(v); out = []
    for i in range(101):
        out.append(v[min(n - 1, int(round(i / 100 * (n - 1))))])
    return out

S = {}; gap = []; ncell = {}
for sd in ('11', '41'):
    C = {'ksi': [], 'rec': [], 'b0': [], 'b1': [], 'b2': [], 'b3': []}; WD = [[] for _ in range(24)]; WE = [[] for _ in range(24)]; nc = 0
    for d in sorted(glob.glob(os.path.join(R, sd + '*'))):
        gu = os.path.basename(d)
        if not os.path.isdir(d): continue
        f10 = os.path.join(d, 'taas10.json'); f250 = os.path.join(d, 'taas250.json'); fl = os.path.join(d, 'live250.json')
        ok = os.path.exists(f250)   # 100m 칸(taas10)이 「준비 중」인 11구도 250m 칸(taas250)은 따로 모아 온전하다(평택 32,399건 등 · 10-08 대조) — 빼지 않는다
        if ok:
            for k, c in json.load(open(f250, encoding='utf-8'))['cells'].items():
                C['ksi'].append(c[12] + c[13]); C['rec'].append(c[9] + c[10] + c[11])
                for i in range(4): C['b%d' % i].append(c[19 + i])
                nc += 1
        if os.path.exists(fl):
            for k, x in json.load(open(fl, encoding='utf-8'))['cells'].items():
                for h in range(24): WD[h].append(x['wd'][h]); WE[h].append(x['we'][h])
    o = {k: q101(v) for k, v in C.items()}
    if any(WD[0]): o['wd'] = [q101(a) for a in WD]; o['we'] = [q101(a) for a in WE]
    S[sd] = o; ncell[sd] = nc
out = {'schema': 'tg-priq/1', 'built': time.strftime('%Y-%m-%d'),
       'source': '도로교통공단 TAAS GIS 사고분석 2016~2025(250m 칸 · taas250) · 서울시 250M격자 생활인구 OA-22784(한 주 평균 · live250) — 둘 다 이 지도에 이미 구운 칸 자료',
       'note': '시도마다 0 이 아닌 칸 값의 분위수 101개(0~100%). 지도는 칸 값이 눈금 어디에 드는지로 백분위를 낸다(0 이면 0).',
       'fields': 'ksi 사망+중상자(10년) · rec 최근 3년 사고 · b0~b3 시간대 사고(0~6·6~12·12~18·18~24시) · wd/we 서울 생활인구 0~23시(평일/주말)',
       'cells': ncell, 'gap': gap, 'sido': S}
json.dump(out, open(os.path.join(ROOT, 'data', 'pri-q.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('칸', ncell, '뺀 구', gap, os.path.getsize(os.path.join(ROOT, 'data', 'pri-q.json')), 'B')
