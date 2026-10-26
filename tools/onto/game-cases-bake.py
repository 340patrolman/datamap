# -*- coding: utf-8 -*-
# 게임 현장 사례 → 온톨로지 코어(2026-10-26 · 소유자 「권하는 차례대로」 3번 — 게임과 지도는 같은 파트 · 손으로 옮기던 것을 저절로)
#   traffic-game/data/ontology-seocho.json(게임 세션이 소유자 설계서 ver.1 에서 옮긴 현장 사례·조치·수요 시설)을 값 그대로 data/onto-game-cases.json 으로 옮긴다
#   코어는 저장소 안 파일로만 굽는다 — 그래서 원본을 복사해 두고 원본 해시를 같이 적는다(게임 쪽이 바뀌면 이 도구를 다시)
#   교차로는 게임의 ix.* 가 가진 신호 번호(sig.no = C-ITS 번호)로 온톨로지 INT 에 잇는다 — 번호가 없으면 잇지 않는다
# 쓰기: py -3.12 -X utf8 tools/onto/game-cases-bake.py   → ontology-core/build.py
import json, os, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), 'traffic-game', 'data', 'ontology-seocho.json')
raw = open(SRC, 'rb').read(); g = json.loads(raw.decode('utf-8'))
E = g['entities']
ix = {x['id']: {'nm': x['name'], 'cits': str((x.get('sig') or {}).get('no') or '') or None, 'tgis': (x.get('tgis') or {}).get('no')} for x in E['intersections']}
out = {'schema': 'tg-onto-game-cases/1', 'made': datetime.datetime.now().isoformat(timespec='seconds'),
       'source': 'traffic-game/data/ontology-seocho.json(%s · 게임 세션 · 소유자 「SEOUL PATROL 온톨로지 설계서 ver.1」 2026-10-01)' % g.get('version'),
       'source_sha256': hashlib.sha256(raw).hexdigest()[:16],
       'fields': {'ix': '게임 교차로 id → 이름·C-ITS 번호(cits)·T-GIS 번호', 'cases': '현장 사례(at 교차로 · when · cause 수요 시설 · measure 조치 · result 현장 결과 · quote 소유자 글 그대로)',
                  'measures': '현장 조치(tool · how · at)', 'gens': '수요를 만드는 시설(kind · schedule · near 교차로)', 'demand': '시설 → 교차로 수요(when · 원본 relations generatesDemandAt)'},
       'note': '값은 게임 원본 그대로 — 확인 필요(src 「확인 필요」)도 그대로 둔다',
       'ix': ix,
       'cases': [{k: c.get(k) for k in ('id', 'at', 'segment', 'when', 'cause', 'story', 'measure', 'result', 'src', 'observed', 'quote')} for c in g['cases']],
       'measures': [{k: m.get(k) for k in ('id', 'name', 'tool', 'at', 'how', 'src', 'open', 'quote')} for m in E['measures']],
       'gens': [{'id': f['id'], 'name': f['name'], 'kind': f.get('kind'), 'schedule': (f.get('schedule') or {}).get('v'), 'src': (f.get('schedule') or {}).get('src'), 'near': f.get('near') or []} for f in E['facilities']],
       'demand': [[r[0], r[2], (r[3] or {}).get('when'), (r[3] or {}).get('src')] for r in g['relations'] if r[1] == 'generatesDemandAt']}
p = os.path.join(ROOT, 'data', 'onto-game-cases.json')
json.dump(out, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('cases', len(out['cases']), 'measures', len(out['measures']), 'gens', len(out['gens']), 'demand', len(out['demand']), '· 신호 번호 있는 교차로', sum(1 for v in ix.values() if v['cits']), '/', len(ix))
