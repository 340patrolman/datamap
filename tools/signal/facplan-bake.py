# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚥 시설담당이 준 신호주기 표(CSV) → 지도가 읽는 꼴(소유자 2026-10-11 「시설담당이 나중에 신호주기 CSV 를 주면 바로 올릴 수 있게, 데이터 스키마를 분리된 파일로」)
#   넣는 곳 = 저장소 **밖** ../07_API키/신호앱/시설담당_신호주기/*.csv (내부 자료 — 저장소에 올리지 않는다) · 틀 = tools/signal/fac-plan-template.csv · 칸 설명 = data/fac-plan-schema.json
#   기본은 검사만 하고 저장소 밖 ../07_API키/신호앱/fac-plan.json 에 쓴다. **--publish 를 줄 때만** data/fac-plan.json(공개 저장소)에 쓴다 —
#     교통과 신호 자료는 소유자가 정한 곳까지만 공개한다(2026-10-10 「다섯 곳까지」) → 새로 받은 자료를 공개할지는 그때마다 소유자가 정한다
#   검사: 현시값의 합 = 주기(A링·B링 각각) · 시각 꼴 · 요일구분 낱말 — 하나라도 틀린 줄은 싣지 않고 까닭을 적는다(고쳐 넣지 않는다)
#   py -3.12 -X utf8 tools/signal/facplan-bake.py [--publish]
import csv, glob, json, os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
SRC = os.path.join(KB, '07_API키', '신호앱', '시설담당_신호주기'); DOW = {'월~목': 0, '평일': 0, '금': 1, '토': 2, '일': 3, '일·공휴일': 3, '공휴일': 3}
def main():
    os.makedirs(SRC, exist_ok=True); spots = {}; bad = []; n = 0
    for f in sorted(glob.glob(os.path.join(SRC, '*.csv'))):
        for i, r in enumerate(csv.DictReader(open(f, encoding='utf-8-sig')), 2):
            n += 1; w = os.path.basename(f) + ' ' + str(i) + '줄'
            try:
                no = r['교차로번호'].strip(); c = int(r['주기']); off = int(r['옵셋'] or 0); a = [int(x) for x in r['A링현시값'].split()]; b = [int(x) for x in (r['B링현시값'] or r['A링현시값']).split()]; hh, mm = r['시작시각'].strip().split(':'); dw = DOW[r['요일구분'].strip()]
                if not no or '보기 줄' in (r.get('비고') or ''): continue
                if sum(a) != c or sum(b) != c: bad.append(w + ' — 현시값의 합(%d · %d)이 주기 %d 와 다르다' % (sum(a), sum(b), c)); continue
                if not (0 <= int(hh) < 24 and 0 <= int(mm) < 60): bad.append(w + ' — 시작시각'); continue
            except Exception as e: bad.append(w + ' — 읽지 못함(' + type(e).__name__ + ')'); continue
            s = spots.setdefault(no, {'nm': r['교차로명'].strip(), 'day': r.get('기준일', '').strip(), 'by': r.get('제공', '').strip(), 'ph': r.get('현시구성', '').strip(), 'rows': []})
            s['rows'].append([dw, '%02d:%02d' % (int(hh), int(mm)), c, off, ' '.join(map(str, a)), ' '.join(map(str, b))])
    for s in spots.values(): s['rows'].sort()
    doc = {'schema': 'tg-fac-plan/1', 'made': datetime.date.today().isoformat(), 'source': '시설담당(교통과 신호운영)이 준 신호주기 표 — 교차로마다 day 기준일 · by 제공',
           'note': ['계획값이다 — 감응·수동 운영 중에는 실제와 다르다 · 옵셋은 자정 기준(주기 시작 = 하루 초 − 옵셋 이 주기로 나누어떨어지는 때)으로 읽는다', '현시구성은 준 글 그대로(어느 현시가 어느 방향인지)'],
           'fields': 'spots{교차로 번호: {nm, day 기준일, by 제공, ph 현시구성 글, rows[[요일 갈래 0 월~목·1 금·2 토·3 일/공휴일, 시작 HH:MM, 주기 초, 옵셋 초, A링 현시값, B링 현시값]…]}}', 'spots': spots}
    pub = '--publish' in sys.argv; p = os.path.join(ROOT, 'data', 'fac-plan.json') if pub else os.path.join(KB, '07_API키', '신호앱', 'fac-plan.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('읽은 줄', n, '· 교차로', len(spots), '· 싣지 않은 줄', len(bad), '·', '공개 저장소에 씀' if pub else '저장소 밖에 씀(공개하려면 --publish)', p)
    for x in bad[:30]: print('  ', x)
if __name__ == '__main__': main()
