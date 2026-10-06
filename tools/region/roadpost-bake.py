# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.30.0 — 🔢 도로 번호(코워크 지시 `../코드세션_지시_도로번호위치_20261006.md`)
#   07_API키/roadpost_prep.py 정리본(out/roadpost/prep/road-posts.json · tg-roadposts/1) → data/road-posts.json
#   서울 도시고속도로 가로등주 관리번호(공공데이터포털 15107934 · 2022-11-08 · 이용허락 제한 없음) · 고속도로 거리표(한국도로공사 이정 좌표)는 소유자가 받으면 같은 파일에 들어온다
#   py -3.12 -X utf8 tools/region/roadpost-bake.py
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(KB, 'roadpost_prep.py')], check=True)
j = json.load(open(os.path.join(KB, 'out', 'roadpost', 'prep', 'road-posts.json'), encoding='utf-8'))
for k, v in j['sets'].items(): v.pop('prefixCount', None)
json.dump(j, open(os.path.join(ROOT, 'data', 'road-posts.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print({k: len(v['items']) for k, v in j['sets'].items()}, os.path.getsize(os.path.join(ROOT, 'data', 'road-posts.json')))
