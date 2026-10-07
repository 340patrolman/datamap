# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.87.0 — 경기 카드 3자리 업종코드(D01 등) 이름 붙이기
#   코드표: 07_API키/out/ggcode/경기_카드_3자리업종코드.csv(코워크 2026-10-07 · 83개 · 경기데이터드림 카드소비 원자료 card_tpbuz_cd·nm_1·nm_2 에서 뽑음 — 규격서 PDF 엔 목록 없음)
#   data/r/<경기 구>/ggdong.json 의 names(두 글자 「카드매출 분석」 체계)에 세 글자 「카드소비」 체계를 덧붙인다 — 「중분류」(대분류 = names3)
#   목록에 없는 코드는 지도에서 원문 그대로 보인다
#   py -3.12 -X utf8 tools/region/ggcode3-merge.py
import csv, json, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'ggcode', '경기_카드_3자리업종코드.csv')
C = {r['업종분류코드(3자리)'].strip(): (r['대분류명'].strip(), r['중분류명'].strip()) for r in csv.DictReader(open(CSV, encoding='utf-8-sig'))}
n = 0; miss = set()
for f in glob.glob(os.path.join(ROOT, 'data', 'r', '41*', 'ggdong.json')):
    j = json.load(open(f, encoding='utf-8')); nm = j.setdefault('names', {}); big = j.setdefault('names3', {})
    for k, (b, m) in C.items(): nm[k] = m; big[k] = b
    for d in j.get('dong', {}).values():
        for y, cd in (d.get('card') or {}).items():
            for code in cd:
                if code not in nm: miss.add(code)
    j['note3'] = '세 글자 업종 코드(D01 등) 이름 = 경기데이터드림 카드소비 원자료의 코드·대분류명·중분류명 짝(코워크 2026-10-07 · 83개) — 목록에 없는 코드는 원문'
    json.dump(j, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); n += 1
print('파일', n, '코드', len(C), '이름 없는 코드', sorted(miss))
