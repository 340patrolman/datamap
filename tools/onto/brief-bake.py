# -*- coding: utf-8 -*-
# 「이 자리 한 줄 진단」 굽기(2026-11-07 · 소유자 「권고대로 진행」 — 시안 세 곳(서초역·반포쇼핑타운·이수역) 꼴로 서초 사고 교차로 전부)
#   있는 사실만 묶는다 — 원인 단정 없음 · 문턱·점수 없음 · 숫자는 모두 원자료에서 센 값
#   원자료: data/decide-seocho.json(decide-bake.py · TAAS 10년 70m 안 · 주 위반 · 카메라 · 보호구역) + ontology-core/data/core-seocho.json(들어오는길 → 길 이름·차로)
#   순위 = 사고 건수 순위(같은 건수는 같은 순위) — 교통량을 반영하지 않는다(화면에 밝힌다)
#   T-Book 법규 단추 = 주 위반이 T-Book 범칙금 항목과 이어질 때만(decide vio → law · 이름 맞대기 C) · 안전운전불이행·기타는 이어 붙이지 않는다
#   py -3.12 -X utf8 tools/onto/brief-bake.py  → data/int-brief.json
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = json.load(open(os.path.join(ROOT, 'data', 'decide-seocho.json'), encoding='utf-8'))
C = json.load(open(os.path.join(ROOT, 'ontology-core', 'data', 'core-seocho.json'), encoding='utf-8'))
O = {o['id']: o for o in C['objects']}
AP = {}
for e in C['edges']:
    if e[1] == '들어오는길' and e[2] in O: AP.setdefault(e[0], []).append(O[e[2]])
DIRS = {'북쪽': 0, '북동쪽': 1, '동쪽': 2, '남동쪽': 3, '남쪽': 4, '남서쪽': 5, '서쪽': 6, '북서쪽': 7}
I = D['int']; accs = [v[4] for v in I.values()]
out = {}
for k, v in I.items():
    acc = v[4]
    if acc <= 0: continue
    rank = 1 + sum(1 for a in accs if a > acc)
    vio = []
    for w in v[10][:1]:
        nmv, laws = D['vio'].get(w[0], [w[0], []])
        li = D['law'][laws[0]][0] if laws and laws[0] in D['law'] else ''
        vio.append([nmv, w[1], li])
    rd = []
    for x in AP.get(k, []):
        if not x.get('rds'): continue
        dr = (x.get('frm') or '').replace('에서 오는 길', '').strip()
        r0 = x['rds'][0]
        rd.append([dr, r0[0], r0[2]])
    rd.sort(key=lambda r: DIRS.get(r[0], 9))
    yr = v[15]
    out[k.replace('INT-', '')] = [rank, acc, v[8], v[9], v[7], v[5], vio, sum(yr[:3]), sum(yr[-3:]), v[11], v[12], rd]
json.dump({'schema': 'tg-int-brief/1', 'made': D['made'], 'n': len(out), 'y0': 2016, 'y1': 2025,
           'fields': '{T-GIS 코드: [사고 건수 순위, 10년 사고, 사망, 중상, 보행자, 시간대 넷(0~6·6~12·12~18·18~24), 주 위반[[이름, 건, T-Book 항목 또는 빈칸]], 앞 3년(2016~18), 뒤 3년(2023~25), 100m 안 경찰 카메라, 300m 안 보호구역 시설, 들어오는 길[[쪽, 길 이름, 차로]]]}',
           'source': 'TAAS 교통사고 10년(2016~2025 · 교차로 70m 안 100m 칸) · T-GIS 교차로 · ITS 링크(들어오는 길·차로) · 경찰 카메라 · 보호구역 — decide-seocho.json·core-seocho.json 값 그대로',
           'int': out}, open(os.path.join(ROOT, 'data', 'int-brief.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('교차로 %d곳 · 법규 잇기 %d곳 · 길 있음 %d곳' % (len(out), sum(1 for r in out.values() if r[6] and r[6][0][2]), sum(1 for r in out.values() if r[11])))
