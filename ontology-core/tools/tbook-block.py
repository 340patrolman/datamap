# -*- coding: utf-8 -*-
"""교통 온톨로지 코어 v1 — T-Book ontology.html 에 넣을 정적 블록(작업지시서 Phase 3).
  core-seocho.json 에서 교차로 몇 곳의 부분 그래프만 그대로 떼어 낸다(값을 다시 셈하지 않는다 — 객체·링크 모양 그대로).
  고르는 교차로 = 조치 이력이 있는 곳(교통과 출력물 5곳) + 10년 사고가 많은 차례로 TOP 곳.
  넣는 것: 교차로(INT) · 사고 집계(ACC) · 위반유형(VIO) · 법규 항목(LAW) · 판례(PREC) · 카메라(CAM) · 보호구역 시설(ATT) · 조치(ACT) · 근거기록(REC)
  빼는 것: 250m 칸(PLC) · 이웃 교차로(인접) — 화면에서 안 쓴다
  쓰기: py -3.12 -X utf8 ontology-core/tools/tbook-block.py [TOP=25]  → ontology-core/data/tbook-block-seocho.json
"""
import json, os, sys, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE)
SRC = os.path.join(CORE, 'data', 'core-seocho.json'); OUT = os.path.join(CORE, 'data', 'tbook-block-seocho.json')
TOP = int(sys.argv[1]) if len(sys.argv) > 1 else 25
raw = open(SRC, 'rb').read(); c = json.loads(raw)
O = {o['id']: o for o in c['objects']}
out = {}
for e in c['edges']: out.setdefault(e[0], []).append(e)
inn = {}
for e in c['edges']: inn.setdefault(e[2], []).append(e)
def acc_total(i):
    a = [e for e in out.get(i, []) if e[1] == '발생']
    return sum(O[a[0][2]]['years']) if a else 0
ints = [o['id'] for o in c['objects'] if o['t'] == 'INT']
withact = [i for i in ints if any(e[1] == '대상' for e in inn.get(i, []))]
top = sorted(ints, key=lambda i: (-acc_total(i), i))[:TOP]
pick = list(dict.fromkeys(withact + top))
keep, edges = set(), []
def add_edge(e):
    edges.append(e); keep.add(e[0]); keep.add(e[2])
for i in pick:
    keep.add(i)
    for e in out.get(i, []):
        if e[1] in ('발생', '보유', '가까움'): add_edge(e)
        if e[1] == '발생':
            for f in out.get(e[2], []):
                if f[1] == '주요원인': add_edge(f)
    for e in inn.get(i, []):
        if e[1] == '대상':
            add_edge(e)
            for f in out.get(e[0], []):
                if f[1] == '근거기록': add_edge(f)
for o in c['objects']:
    if o['t'] in ('VIO', 'LAW', 'PREC'): keep.add(o['id'])
for e in c['edges']:
    if e[1] in ('근거', '해석'): add_edge(e)
seen, E2 = set(), []
for e in edges:
    k = json.dumps(e[:3], ensure_ascii=False)
    if k not in seen: seen.add(k); E2.append(e)
objs = [O[i] for i in sorted(keep, key=lambda x: (O[x]['t'], x))]
blk = {'schema': 'tg-onto-core-block/1', 'area': c.get('area'), 'core_made': c.get('made'),
       'core_sha256': hashlib.sha256(raw).hexdigest()[:16], 'made': datetime.date.today().isoformat(),
       'pick': {'with_actions': withact, 'top_accidents': TOP, 'n': len(pick)},
       'sources': c.get('sources'), 'unverified_precedents': c.get('unverified_precedents'),
       'note': 'core-seocho.json 의 부분 그래프 — 값은 손대지 않고 그대로 옮김. 사고는 교차로 70m 안 100m 칸 묶음(근사 · 등급 C). 조치는 교통과 출력물 이력(공개 결정 2026-10-10). 판례는 원문 대조된 것만.',
       'objects': objs, 'edges': E2}
s = json.dumps(blk, ensure_ascii=False, separators=(',', ':'))
open(OUT, 'w', encoding='utf-8', newline='\n').write(s)
print('교차로 %d곳(조치 %d + 사고 상위 %d) · 객체 %d · 링크 %d · %d B' % (len(pick), len(withact), TOP, len(objs), len(E2), len(s.encode('utf-8'))))
