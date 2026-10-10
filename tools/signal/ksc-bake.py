# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 서초경찰서 교통과 신호 운영값(표준신호제어기DB KSC-5800SE/SEC-8400 출력물 손 판독) → data/sig-ksc-seocho.json
#   소유자 2026-10-10: 현시도 PDF 5장(서초역사거리 4039 · 서초경찰서 4036 · 서울성모병원 4034 · 강남터미널고가밑 4031 · 삼호가든사거리 4028)을 가리키며 「신호값데이터도 넣어라 · 여기까지는 ok다」
#     → 「잠가서 / 평문 / 안 넣기」를 여쭈어 **「평문으로 넣기」** 로 답하셨다(2026-09-12 의 「확인코드로 잠가서」 결정을 이 5곳에 한해 바꿈). **이 5곳까지만** — 다른 교차로의 교통과 자료는 소유자가 다시 정하기 전에는 넣지 않는다.
#   원자료 = 07_API키/신호앱/data/서초서_교통과_신호_불러오기용_20260911.json(tbsig-ksc/1 · 손 판독 두 벌 대조 96/96 · 현시 합 = 주기 80/80) — 값을 그대로 옮긴다(고치지 않는다)
#   PDF 원본·현시도 그림(어느 현시가 어느 방향인지)은 싣지 않는다 — 방향을 글로 옮기면 틀릴 수 있어 판독하지 않았다
#   py -3.12 -X utf8 tools/signal/ksc-bake.py
import json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱', 'data', '서초서_교통과_신호_불러오기용_20260911.json')
OK = ('4039', '4036', '4034', '4031', '4028')   # 소유자가 공개를 정한 곳만
def main():
    j = json.load(open(SRC, encoding='utf-8')); items = []
    for e in j['items']:
        if e['no'] not in OK: continue
        for k, p in e['pat'].items(): assert sum(p['a']) == p['c'] and sum(p['b']) == p['c'], (e['no'], k)   # 현시 합 = 주기
        for d, rows in e['tod'].items():
            for t, c, pn in rows: assert e['pat'][str(pn)]['c'] == c, (e['no'], d, t)   # 시간대 계획의 주기 = 그 패턴의 주기
        items.append({'no': e['no'], 'nm': e['nm'], 'lat': round(e['la'], 6), 'lon': round(e['lo'], 6), 'day': e['day'], 'dayk': e.get('dayk'), 'tod': e['tod'], 'pat': e['pat'], 'memo': e.get('memo') or []})
    doc = {'schema': 'tg-sig-ksc/1', 'made': datetime.date.today().isoformat(),
           'source': '서초경찰서 교통과 제공 · 표준신호제어기DB(KSC-5800SE/SEC-8400) 출력물 5장을 손으로 판독(%s) — 소유자가 이 5곳의 공개를 정함(2026-10-10)' % j.get('read', ''),
           'note': ['계획값이다 — 감응·수동 운영·행사·공사 중에는 실제와 다르다 · 출력물의 시행일(day) 뒤에 바뀌었을 수 있다',
                    '어느 현시가 어느 방향인지는 이 파일에 없다(현시도 그림을 글로 옮기지 않았다) — 현시 번호와 초만 있다',
                    '옵셋(off)의 기준(어느 현시·어느 시각)은 확인되지 않았다 — 이 값으로 「몇 초 뒤 바뀜」이나 연동 속도를 계산하지 않는다',
                    '밤(22시~)에는 과속을 막으려고 연동을 일부러 끊어 둔 구간이 있다(소유자 현장 지식) — 「이 속도면 계속 녹색」 같은 안내에 쓰지 않는다',
                    '삼호가든사거리(4028)는 서초중앙로 축 · 나머지 넷은 반포대로 축이다'],
           'fields': 'items[{no 교차로 번호, nm 이름, lat, lon, day 출력물의 날짜, dayk 그 날짜의 뜻(시행일·작성일), tod{요일 계획 1 월~목(평일) · 2 금 · 3 토 · 4 일·공휴일: [[시작 시각 HHMM, 주기 초, 패턴 번호]…] — 그날 첫 계획보다 이르면 전날 마지막 계획이 이어진다}, pat{패턴 번호: {c 주기 초, off 옵셋 초, a[A링 현시별 초], b[B링 현시별 초]} — 합 = 주기 · a 와 b 가 다르면 겹침 현시}, memo[출력물의 참고 글]}]',
           'items': items}
    p = os.path.join(ROOT, 'data', 'sig-ksc-seocho.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(items), [(e['no'], e['nm'], len(e['pat'])) for e in items], '바이트', os.path.getsize(p))
if __name__ == '__main__': main()
