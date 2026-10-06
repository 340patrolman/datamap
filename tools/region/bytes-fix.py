# -*- coding: utf-8 -*-
# data/r/index.json 의 시군구마다 층 바이트를 실제 파일로 다시 채운다(굽는 도구 둘이 동시에 index.json 을 쓰면 한쪽 기록이 덮인다 — 2026-10-06)
#   py -3.12 -X utf8 tools/region/bytes-fix.py [층 …]   (층을 안 주면 폴더에 있는 .json 전부)
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); R = os.path.join(ROOT, 'data', 'r')
IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); only = set(sys.argv[1:]); n = 0
for g in IX['gus']:
    d = os.path.join(R, g['gu'])
    if not os.path.isdir(d): continue
    for f in os.listdir(d):
        k = f[:-5]
        if not f.endswith('.json') or (only and k not in only): continue
        b = os.path.getsize(os.path.join(d, f))
        if (g.get('bytes') or {}).get(k) != b: g.setdefault('bytes', {})[k] = b; n += 1
L = {'deals': '공동주택 매매 한 건씩(세금 모의계산 유사매매사례 후보 · 연월·면적·금액)', 'acad': '학원(상가업소 교육 업종 · 한 곳씩)'}
for k, v in L.items(): IX['layers'].setdefault(k, v)
json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('고친 칸', n)
