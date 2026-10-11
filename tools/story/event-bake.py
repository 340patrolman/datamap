# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧩 사건(Event) 객체: 계획 · 진행중 · 완료(소유자 마스터 문서 객체 9 · 7.7 · ONTOLOGY.md Object 11) → data/events-big.json
#   tools/story/event-seed.json 에 한 줄씩 적은 큰 사건(이전·재개발·개통)을 검사해 굽는다 — **출처가 없는 줄 · 상태가 셋 가운데 하나가 아닌 줄은 싣지 않는다**(날짜·규모를 지어 넣지 않는다)
#   py -3.12 -X utf8 tools/story/event-bake.py
import json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def main():
    S = json.load(open(os.path.join(ROOT, 'tools', 'story', 'event-seed.json'), encoding='utf-8')); ok = []; bad = []
    for x in S.get('items', []):
        if not x.get('src') or not all(s.get('t') for s in x['src']): bad.append((x.get('id'), '출처 없음')); continue
        if x.get('state') not in ('계획', '진행중', '완료'): bad.append((x.get('id'), '상태')); continue
        if not x.get('id') or not x.get('nm'): bad.append((x.get('id'), '이름')); continue
        ok.append({k: x.get(k, '') for k in ('id', 'nm', 'kind', 'state', 'll', 'area', 'd_plan', 'd_start', 'd_done', 'size', 'what', 'src', 'prev', 'next')})
    doc = {'schema': 'tg-event/1', 'made': datetime.date.today().isoformat(), 'object': '사건(Event) — ONTOLOGY.md Object 11',
           'source': 'tools/story/event-seed.json — 사건마다 src(출처 이름·주소·본 날)',
           'note': ['상태 = 계획(앞날의 신호) · 진행중(지켜볼 대상) · 완료(뒤돌아 맞대 볼 것) — 상태는 굽는 날 기준이라 시간이 지나면 바뀐다(다시 굽는다)', '날짜·규모는 출처에 적힌 것만 실었다(빈 글 = 모름) · 「무엇이 바뀌나」는 출처의 말이고 이 지도의 예측이 아니다',
                    '사건이 둘레 자리에 준 영향은 이 파일에 없다 — 완료된 사건의 앞뒤를 실거래·상권·생활인구로 맞대 보는 것은 따로 굽는다'],
           'fields': S.get('fields', ''), 'items': ok}
    p = os.path.join(ROOT, 'data', 'events-big.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('사건', len(ok), '· 싣지 않은 줄', bad, '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
