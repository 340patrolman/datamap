# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 신호가 「일요일 계획」으로 도는 특수일(소유자 2026-10-11 「평일 금요일 토요일 일요일 특수일 해서 조금씩 달라 — 내가 붙인 pdf 파일 보면 알 거야」) → data/sig-special.json
#   교통과 신호현시도(표준신호제어기데이터베이스 KSC-5800SE · 서초역사거리 4039 시행일 2026.01.28)의 「특수일」 표 = 15종 모두 TOD 4(일요일 계획):
#     신정 · 설날전 · 설날 · 설날후 · 삼일절 · 어린이날 · 석탄일 · 현충일 · 광복절 · 추석전 · 추석 · 추석후 · 개천절 · 한글날 · 성탄일
#   **이 표에 없는 쉬는 날**(대체공휴일 · 선거일 · 제헌절 · 노동절 · 임시공휴일)은 제어기가 특수일로 알지 못한다 → 그 요일의 계획(평일이면 평일 계획)으로 돈다고 본다(현시도 한 장에서 읽은 것 — 교통과가 그날 따로 바꾸는지는 확인하지 못했다)
#   날짜는 data/holidays.json(한국천문연구원 특일 정보)의 이름으로 가른다
#   py -3.12 -X utf8 tools/signal/sigspecial-bake.py   (holidays.json 을 다시 구우면 같이 다시)
import json, os, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAP = {'1월1일': '신정', '신정': '신정', '설날': '설날(전·당일·후)', '삼일절': '삼일절', '어린이날': '어린이날', '부처님오신날': '석탄일', '현충일': '현충일', '광복절': '광복절', '추석': '추석(전·당일·후)', '개천절': '개천절', '한글날': '한글날', '기독탄신일': '성탄일'}
def main():
    H = json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8'))['days']; sp = {}; other = {}
    for d, nm in sorted(H.items()):
        if nm in MAP: sp[d] = MAP[nm]
        else: other[d] = nm
    doc = {'schema': 'tg-sig-special/1', 'made': datetime.date.today().isoformat(),
           'source': '서초경찰서 교통과 신호현시도(표준신호제어기데이터베이스 KSC-5800SE · 서초역사거리 4039 · 시행일 2026.01.28)의 특수일 표 15종 · 날짜 = data/holidays.json(한국천문연구원 특일 정보)',
           'special15': ['신정', '설날전', '설날', '설날후', '삼일절', '어린이날', '석탄일', '현충일', '광복절', '추석전', '추석', '추석후', '개천절', '한글날', '성탄일'],
           'note': ['**특수일 15종은 모두 TOD 4(일요일 계획)로 돈다** — 신호의 요일 갈래를 정할 때 days 에 든 날은 일요일 갈래(3)로 본다',
                    '**other 의 날(대체공휴일 · 선거일 · 제헌절 · 노동절)은 특수일 표에 없다** — 제어기는 그 요일의 계획으로 돈다고 본다(통행량은 휴일 같아도 신호는 평일 계획일 수 있다). 현시도 한 장(서초역사거리)에서 읽은 것이고 다른 교차로·교통과의 그날 운영은 확인하지 못했다',
                    '소유자 현장 지식(2026-10-11): 「신호값이 평일과 휴일이 달라 — 통행량이 다르니까 · 공휴일은 (일요일과) 비슷해 · 평일 · 금요일 · 토요일 · 일요일 · 특수일 해서 조금씩 달라」',
                    '통행속도·교통량 쪽(평소 속도)은 쉬는 날 전부를 휴일로 본다 — 신호의 갈래(이 파일)와 다르다'],
           'fields': 'days{날짜: 특수일 이름}(일요일 계획으로 도는 날) · other{날짜: 이름}(쉬는 날이지만 특수일 표에 없음 — 그 요일 계획)', 'days': sp, 'other': other}
    p = os.path.join(ROOT, 'data', 'sig-special.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('특수일', len(sp), '· 표에 없는 쉬는 날', len(other), '· 2026~2027 표에 없는 날:', {d: n for d, n in other.items() if d[:4] in ('2026', '2027')})
if __name__ == '__main__': main()
