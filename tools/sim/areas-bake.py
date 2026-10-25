# -*- coding: utf-8 -*-
# 시뮬 구역 목록(2026-10-25 · 소유자 「잘 작동되면 서울시 전역으로 확대」) — data/sim-<이름>.json 자동 구역(auto)을 훑어 data/sim-areas.json 한 장으로
#   지도 화면 js/sim-area.js 가 이 목록만 먼저 읽고(작다), 지도 가운데가 구역 둘레면 「🧪 시뮬 — ○○ 둘레」 단추를 띄운다 · 카드 이름이 구역 교차로면 카드에 단추
#   반포 터미널 블록은 손으로 짠 구역(sim-banpo · js/sim-ui.js)이 맡으므로 banpo-auto 는 목록에서 뺀다
#   맞음 = sim-cal.py 의 마지막 맞춤(평소 속도와 맞대 본 접근로 칸 수) — 화면에 그대로 적는다
# 쓰기: py -3.12 -X utf8 tools/sim/areas-bake.py   (area-bake.py · sim-cal.py 로 구역을 굽거나 다시 맞춘 뒤)
import json, os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
NAMES = {'seochoyeok': '서초역 둘레', 'gangnam': '강남역 둘레', 'yangjae': '양재역 둘레', 'sadang': '사당역 둘레', 'isu': '이수역 둘레', 'nambu': '남부터미널 둘레', 'naebang': '내방역 둘레'}
SKIP = {'banpo-auto'}

out = []
for p in sorted(glob.glob(os.path.join(D, 'sim-*.json'))):
    nm = os.path.basename(p)[4:-5]
    if nm in SKIP or nm == 'areas':
        continue
    d = json.load(open(p, encoding='utf-8'))
    if not d.get('auto'):
        continue
    sig = [n for n in d['nodes'].values() if n.get('ty') == 'sig']
    cal = d.get('cal') or {}
    h = cal.get('best') or (cal.get('hist') or [{}])[-1]
    out.append({'id': nm, 'nm': NAMES.get(nm, nm), 'c': d['center'], 'r': d['r'],
                'sig': [[n['id'], n['nm'], n['ll'][0], n['ll'][1]] for n in sig],
                'hit': h.get('hit'), 'n': h.get('n'), 'mh': h.get('mh'), 'mn': h.get('mn'), 'jh': h.get('jh'), 'jn': h.get('jn'), 'calDay': cal.get('date'), 'made': d.get('made'), 'bytes': os.path.getsize(p)})
J = {'schema': 'tg-sim-areas/1', 'made': datetime.date.today().isoformat(),
     'source': 'tools/sim/areas-bake.py ← data/sim-<이름>.json(tools/sim/area-bake.py 가 서울 도로망·신호값·교통량 조사로 엮음 · sim-cal.py 가 평소 속도로 수요 배율 맞춤)',
     'fields': {'id': '구역 자료 data/sim-<id>.json', 'nm': '이름', 'c': '가운데 [위도, 경도]', 'r': '반지름 m', 'sig': '신호 교차로 [번호, 이름, 위도, 경도]',
                'hit/n': '맞춤 칸 가운데 맞은 수(가장 잘 맞은 맞춤 · 실측 없는 들어오는 길은 「막히지 않음」으로 셈)', 'mh/mn': '평소 속도(ITS) 실측이 있는 칸만 맞은 수', 'jh/jn': '실측 막힘(6km/h 이하) 칸 가운데 시뮬도 막힌 수', 'calDay': '맞춘 날'},
     'note': '개념 시연 — 예측·보증 아님 · 반포 터미널 블록은 sim-banpo(손으로 짠 구역 · js/sim-ui.js)', 'areas': out}
json.dump(J, open(os.path.join(D, 'sim-areas.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for a in out:
    print(a['id'], a['nm'], len(a['sig']), '신호', '맞음', a['hit'], '/', a['n'], '실측 칸', a['mh'], '/', a['mn'], '실측 막힘', a['jh'], '/', a['jn'])
