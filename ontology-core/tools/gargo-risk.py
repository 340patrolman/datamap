# -*- coding: utf-8 -*-
"""교통 온톨로지 코어 v1 — 네비 가르고가 읽는 「경로 위 주의 교차로」 표(작업지시서 Phase 4 · 질문 4).
  core-six.json(build.py --area six)의 교차로마다 질문 1(왜 위험한가)의 답을 한 줄로 줄인다 — 값은 코어 그대로(다시 세지 않음).
  주 위반 = 주요원인 링크 중 건수가 가장 큰 것(같으면 코어의 링크 차례 — query.js q1 과 같은 규칙).
  사고 칸이 없는 교차로는 뺀다(지도에서 「사고 없음」이 아니라 「70m 안에 사고 칸 없음」).
  쓰기: py -3.12 -X utf8 ontology-core/tools/gargo-risk.py  → gargo/risk-six.json
"""
import json, os, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE); ROOT = os.path.dirname(CORE)
SRC = os.path.join(CORE, 'data', 'core-six.json'); OUT = os.path.join(ROOT, 'gargo', 'risk-six.json')
raw = open(SRC, 'rb').read(); c = json.loads(raw)
O = {o['id']: o for o in c['objects']}
out = {}
for e in c['edges']: out.setdefault(e[0], []).append(e)
inn = {}
for e in c['edges']: inn.setdefault(e[2], []).append(e)
vio = {o['id'][4:]: o['nm'] for o in c['objects'] if o['t'] == 'VIO'}
law = {}
for v in vio:
    for e in out.get('VIO-' + v, []):
        if e[1] == '근거':
            L = O[e[2]]; law.setdefault(v, []).append([L['title'], L.get('penalty') or ''])
rows = []
for o in c['objects']:
    if o['t'] != 'INT': continue
    a = [e for e in out.get(o['id'], []) if e[1] == '발생']
    if not a: continue
    A = O[a[0][2]]; tot = sum(A['years'])
    if tot <= 0: continue
    mv = sorted(((e[3].get('n', 0), k, e[2][4:]) for k, e in enumerate(out.get(A['id'], [])) if e[1] == '주요원인'), key=lambda x: (-x[0], x[1]))
    cams = sum(1 for e in out.get(o['id'], []) if e[1] == '보유')
    acts = sum(1 for e in inn.get(o['id'], []) if e[1] == '대상')
    rows.append([int(o['id'][4:]), o['nm'], round(o['lon'], 6), round(o['lat'], 6), tot, A['dead'], A['serious'], A['ped'], A['night'],
                 mv[0][2] if mv else '', mv[0][0] if mv else 0, cams, acts, A['years'][-3:]])
rows.sort(key=lambda r: -r[4])
doc = {'schema': 'tg-gargo-risk/1', 'made': datetime.datetime.now().isoformat(timespec='seconds'), 'core': 'ontology-core/data/core-six.json',
       'core_sha256': hashlib.sha256(raw).hexdigest()[:16], 'core_made': c.get('made'), 'area': c.get('area'),
       'fields': '[T-GIS 교차로 코드(INT-번호), 이름, 경도, 위도, 10년 사고(TAAS 2016~2025 · 70m 안 100m 칸), 사망자, 중상자, 보행자 피해, 밤(20~6시), 주 위반 코드, 그 칸들의 건수, 경찰 단속 카메라(100m 안), 교통과 조치 이력 수, 최근 3해(2023·2024·2025) 사고]',
       'vio': vio, 'law': law,
       'note': '근사(등급 C) — 사고는 교차로 둘레 70m 안 100m 칸을 묶은 것 · 주 위반은 칸마다 하나뿐인 「주 법규위반」을 모은 것 · 위반유형 ↔ 범칙금 DB 항목은 이름 맞대기(확인 필요) · 조치 이력은 서초 교통과 출력물 5곳만',
       'rows': rows}
s = json.dumps(doc, ensure_ascii=False, separators=(',', ':'))
open(OUT, 'w', encoding='utf-8', newline='\n').write(s)
print('교차로 %d곳 · %d B' % (len(rows), len(s.encode('utf-8'))))
