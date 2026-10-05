# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 🚗 TAAS 교통사고 10년을 250m 국가표준격자로(전국 확장 설계서 Phase 1 · 소유자 「권고대로」 = 다시 모으기)
#   100m 칸은 250m 를 나누지 못해(250 ÷ 100) 옮기면 근사가 된다 → TAAS GIS 화면 안에서 사고 한 건씩 받아 x_crdnt·y_crdnt(EPSG:5179)로 바로 250m 칸 번호를 매겼다
#   (모으는 법 = MAP2D.md v2.4.0 ⑧ · 서울 = 구 25 × 해 × 등급 · 경기 = 시 31 × 해 × 등급 · 받는 자리에서 개인정보(나이·성별·상해·사고번호·일)는 읽지도 않음)
#   칸은 「구」가 아니라 칸 번호 하나로 모은다 → 두 구 파일에 같은 칸이 생기지 않는다 · 칸이 어느 구 파일에 들어갈지는 grid.json(가장 넓게 걸친 동의 구)
#   입력: 07_API키/out/region/taas250/*.json {cells: {칸: [a(21), 주 법규위반, 그 건수, 주 사고유형]}, rows, ...}
#   py -3.12 -X utf8 tools/region/taas250-bake.py → data/r/<구>/taas250.json (tg-taas250/1)
import json, os, glob, time, collections, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IN = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'region', 'taas250')
sp = importlib.util.spec_from_file_location('g250', os.path.join(ROOT, 'tools', 'region', 'grid250.py')); G = importlib.util.module_from_spec(sp); sp.loader.exec_module(G)

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    gu_of = {}
    for g in IX['gus']:
        for c in json.load(open(os.path.join(ROOT, 'data', 'r', g['gu'], 'grid.json'), encoding='utf-8'))['cells']: gu_of[c[0]] = g['gu']
    C = {}; rows = 0; src = []; bad = 0
    for fn in sorted(glob.glob(os.path.join(IN, 'raw_*.json'))):
        R = json.load(open(fn, encoding='utf-8')); rows += R.get('rows', 0); src.append('%s %s건' % (R.get('region', '?'), R.get('rows', '?')))
        for k, v in R['cells'].items():
            if len(k) != 10 or 'undefined' in k: bad += sum(v[:10]); continue   # 좌표가 격자 범위 밖(좌표 오류)
            if k in C:   # 서울·경기 원자료가 같은 칸에 — 다른 사고(법정동이 다름)라 더한다
                a = C[k]
                for i in range(21): a[i] += v[i]
                if v[22] > a[22]: a[21], a[22], a[23] = v[21], v[22], v[23]
            else: C[k] = list(v)
    per = collections.defaultdict(dict); lost = 0; near = 0
    for k, v in C.items():
        gu = gu_of.get(k)
        if not gu:   # 바다·이웃 시도 — 3km(12칸) 안 가장 가까운 칸의 구
            x, y = G.xy_code(k); best = None
            for dx in range(-12, 13):
                for dy in range(-12, 13):
                    try: q = G.code_xy(x + dx * 250, y + dy * 250)
                    except Exception: continue
                    if q in gu_of and (best is None or dx * dx + dy * dy < best[0]): best = (dx * dx + dy * dy, gu_of[q])
            if not best: lost += sum(v[:10]); continue
            gu = best[1]; near += 1
        lat, lon = G.center_ll(k); per[gu][k] = [lat, lon] + v
    gb = {}
    for gu, cells in per.items():
        doc = {'schema': 'tg-taas250/1', 'gu': gu,
               'source': '도로교통공단 교통사고분석시스템(TAAS) GIS 사고분석 2016~2025 사고 전부(사망·중상·경상·부상신고) · 250m 국가표준격자 · %s 다시 모음' % time.strftime('%Y-%m-%d'),
               'note': '개인정보(나이·성별·상해 부위·사고번호·날짜)는 받는 자리에서 읽지도 않았다 · 칸 번호 하나로 모아 같은 칸이 두 파일에 없다 · 사망사고 한 건씩은 taas10.json 에 그대로',
               'cellFields': '{칸 번호: [칸 가운데 위도, 경도, 2016…2025 해마다 건수(10), 사망자, 중상자, 보행자 피해, 자전거 관련, PM 관련, 이륜·원동기 가해, 밤(20~6시), 0~6시, 6~12시, 12~18시, 18~24시, 주 법규위반 코드, 그 건수, 주 사고유형 코드]}',
               'cells': cells}
        pth = os.path.join(ROOT, 'data', 'r', gu, 'taas250.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['taas250'] = gb[g['gu']]
    IX['layers']['taas250'] = 'TAAS 교통사고 10년(250m 국가표준격자)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    tot = sum(sum(v[2:12]) for c in per.values() for v in c.values())
    print('원자료', src, '받은 줄', rows, '칸', len(C), '구', len(per), '구운 사고', tot, '경계 밖 3km 안 붙임 칸', near, '버림 사고', lost, '좌표 오류 사고', bad, '바이트', sum(gb.values()))

if __name__ == '__main__': main()
