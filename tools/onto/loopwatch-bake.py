# -*- coding: utf-8 -*-
# 🔔 고리 지켜보기 자료(2026-11-07 · 소유자 「계속 진행」 — 차례 셋째 「고리 감시: 지금 막히기 시작 · 먼저 막힌 변」)
#   지도 js/link.js 가 고리 카드를 열지 않고도(코어 430KB · 평소 속도 4MB 를 안 받고) 네 변 상태를 셀 수 있게
#   고리마다 변 → 볼 ITS 링크 차례(고리 자료 링크 먼저, 없으면 접근로 「이룸」 앞 조각부터 — act-effect.leg_links 와 같은 셈 = 카드 legNow 와 같은 차례)
#   + 그 링크들의 평소 속도 가운데값(spd-normal-seocho.json · 「요일 갈래-시」 · 잠정 칸은 표시 1)
#   막힘 잣대는 카드와 같다: 평소 값이 있으면 지금 ÷ 평소 < 0.6 · 없으면 15km/h 아래 · 네 변 중 둘 = 일부 · 셋 넘게 = 전체(값 있는 변 셋 미만이면 판정 안 함)
#   spd-normal-seocho.json 이나 onto-loops.json 을 다시 구우면 이것도 다시
#   py -3.12 -X utf8 tools/onto/loopwatch-bake.py  → data/loop-watch.json
import os, json, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sp = importlib.util.spec_from_file_location('ae', os.path.join(HERE, 'act-effect.py')); AE = importlib.util.module_from_spec(sp); sp.loader.exec_module(AE)
N = json.load(open(os.path.join(ROOT, 'data', 'spd-normal-seocho.json'), encoding='utf-8'))
out = []
for lid, (L, legs) in AE.leg_links().items():
    LG = []
    for lg, links in zip(L['legs'], legs):
        fix = list(lg.get('links') or []); apr = [l for l in links[len(fix):]][:6]   # 카드 legNow: 고리 자료 링크 중 값 온 것 전부 → 없으면 접근로 앞 조각 중 값 온 것 앞 둘
        ls = list(dict.fromkeys(fix + apr))
        LG.append({'nm': lg['nm'].split(' — ')[0], 'full': lg['nm'], 'fix': fix, 'apr': apr,
                   'norm': {l: {k: [v[0], v[4]] for k, v in N['links'][l].items()} for l in ls if l in N['links']}})
    out.append({'id': lid, 'nm': L['nm'], 'open': L['members'][0], 'legs': LG})
json.dump({'schema': 'tg-loop-watch/1', 'made': N['made'], 'normFrom': N['from'], 'normTo': N['to'],
           'rule': {'ratio': 0.6, 'abs': 15, 'part': 2, 'full': 3, 'stale': 20},
           'fields': 'loops[{id, nm, open(카드를 열 교차로), legs[{nm 짧은 이름, full, fix 고리 자료가 정한 링크(값 온 것 전부), apr 접근로 링크 차례(fix 에 값이 없을 때 값 온 것 앞 둘), norm{링크: {「요일 갈래-시」: [평소 가운데값 km/h, 잠정 1|0]}}]}]}',
           'source': 'data/onto-loops.json · ontology-core/data/core-seocho.json(접근로 이룸) · data/spd-normal-seocho.json(ITS 쌓은 속도) — tools/onto/loopwatch-bake.py',
           'loops': out}, open(os.path.join(ROOT, 'data', 'loop-watch.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(' · '.join('%s 변 %d · 링크 %s' % (L['nm'], len(L['legs']), [(len(x['fix']), len(x['apr'])) for x in L['legs']]) for L in out))
