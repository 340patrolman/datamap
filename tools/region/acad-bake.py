# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.39.0 — 🎒 학원 현황(소유자 2026-10-06 「각 동별 학원 위치 현황 — 미술학원·교습소·영어학원」)
#   이미 받은 상가(상권)정보 r/<구>/stores.json(소상공인시장진흥공단 · 공공데이터포털 OpenAPI) 에서 교육 업종만 뽑는다 — 새로 받는 자료 없음
#   ① r/<구>/acad.json = 학원 한 곳씩 [x m, y m, 종류, 층, 상호](stores.json 과 같은 좌표 방식 · 작게)
#   ② data/acad-dong.json = 전국 행정동마다 [경도, 위도, 동 이름, 종류별 수 …] — 넓게 볼 때 동마다 수를 그린다(지도 저장소에 올림)
#   종류 9 = 입시·교과 · 외국어 · 미술 · 음악 · 태권도·무술 · 그 밖 예술·스포츠 · 요가·필라테스 · 컴퓨터 · 자격·기술·운전(전문자격/고시·기타 기술/직업·운전)
#   ⚠ 학원과 교습소를 가르지 않는 등록 자료 · 영업 여부·수강생 없음 · 교육청 「학원·교습소 정보」(NEIS)는 좌표가 없어 아직 안 씀
#   py -3.12 -X utf8 tools/region/acad-bake.py
import json, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')
T = [['P10501'], ['P10615'], ['P10611'], ['P10609'], ['P10601'], ['P10613'], ['P10603'], ['P10627'], ['P10617', 'P10625', 'P10623']]
NAMES = ['입시·교과', '외국어', '미술', '음악', '태권도·무술', '그 밖 예술·스포츠', '요가·필라테스', '컴퓨터', '자격·기술·운전']
I = json.load(open(os.path.join(R, 'stores-index.json'), encoding='utf-8'))
TY = {}
for i, c in enumerate(I['cls']):
    for j, codes in enumerate(T):
        if c[5] in codes: TY[i] = j
def inring(r, x, y):
    c = False; j = len(r) - 1
    for i in range(len(r)):
        if ((r[i][1] > y) != (r[j][1] > y)) and (x < (r[j][0] - r[i][0]) * (y - r[i][1]) / (r[j][1] - r[i][1]) + r[i][0]): c = not c
        j = i
    return c
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8'))
out, tot, nb = {}, [0] * len(T), {}
for g in IX['gus']:
    gu = g['gu']; fs = os.path.join(R, gu, 'stores.json'); fd = os.path.join(R, gu, 'dong.json')
    if not os.path.exists(fs): continue
    S = json.load(open(fs, encoding='utf-8')); O, K = S['o'], S['k']
    pts = [[q[0], q[1], TY[q[2]], q[3], q[4]] for q in S['pts'] if q[2] in TY]
    doc = {'schema': 'tg-acad/1', 'gu': gu, 'stdrYm': S.get('stdrYm'), 'o': O, 'k': K, 'types': NAMES, 'source': I['source'] + ' · 교육 업종만', 'fields': 'pts = [x m, y m(o 에서 · k = m/도), 종류(types 자리), 층, 상호]', 'pts': pts}
    p = os.path.join(R, gu, 'acad.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); nb[gu] = os.path.getsize(p)
    if not os.path.exists(fd): continue
    D = json.load(open(fd, encoding='utf-8'))['dong']
    for d in D:
        polys = d['polys']; xs = [q[0] for pg in polys for q in pg[0]]; ys = [q[1] for pg in polys for q in pg[0]]; bb = (min(xs), max(xs), min(ys), max(ys))
        n = [0] * len(T)
        for q in pts:
            x, y = O[0] + q[0] / K[0], O[1] + q[1] / K[1]
            if x < bb[0] or x > bb[1] or y < bb[2] or y > bb[3]: continue
            if any(inring(pg[0], x, y) and not any(inring(h, x, y) for h in pg[1:]) for pg in polys): n[q[2]] += 1
        c = d.get('c') or [(bb[0] + bb[1]) / 2, (bb[2] + bb[3]) / 2]
        if d['k'] not in out or sum(out[d['k']][3:]) < sum(n): out[d['k']] = [round(c[0], 5), round(c[1], 5), d['name']] + n
        for i, v in enumerate(n): tot[i] += v
for g in IX['gus']:
    if g['gu'] in nb: g.setdefault('bytes', {})['acad'] = nb[g['gu']]
IX['layers']['acad'] = '학원(상가업소 교육 업종 · 한 곳씩)'
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
res = {'schema': 'tg-acad-dong/1', 'types': NAMES, 'source': I['source'] + ' · 교육 업종 · 행정동 = 통계청 SGIS(가공 vuski/admdongkor 2026-07 · CC BY 4.0)', 'stdrYm': I.get('stdrYm'),
       'fields': 'dong = {행정동 8자리: [경도, 위도, 이름, 종류별 수(types 차례)]}', 'note': '학원과 교습소를 가르지 않는다 · 영업 여부 없음 · 동 경계 밖(도로 위 등)에 찍힌 점은 어느 동에도 안 든다', 'dong': out}
p = os.path.join(ROOT, 'data', 'acad-dong.json'); json.dump(res, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('구', len(nb), '학원 점 파일', sum(nb.values()) // 1024, 'KB · 동', len(out), '· 동 요약', os.path.getsize(p) // 1024, 'KB')
print(dict(zip(NAMES, tot)))
