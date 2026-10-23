# -*- coding: utf-8 -*-
# 엮어서 답 찾기 — 질문 레시피 (2026-10-23 소유자 「잘 모르는 사람도 데이터들을 연결해 결과를 만들어낼 수 있게 · 널려 있는 데이터를 다시 잘 엮어 · 티북과 데이터 압축지도에 녹여서」)
#   팔란티어 방식을 네 걸음으로: ① 무엇이 있나(대상) ② 무엇과 무엇이 이어지나(같은 자리·같은 때·같은 코드) ③ 그래서 무엇을 하나(판단·할 일) ④ 해 보고 다시 적는다(조치 기록)
#   사람은 온톨로지를 짜지 않는다 — 질문을 고르면 레시피가 이미 있는 공개 자료 파일을 차례로 엮어 「자료 → 연결 → 판단 → 할 일」 사슬을 보여 준다.
#   정본 = 이 파일의 RECIPES · 예시 값은 굽는 순간 원자료에서 다시 센다(지어낸 값 없음) · 한 점수로 더하지 않는다(갈래마다 따로) · 「위반·위험」으로 단정하지 않는다
# 쓰기: py -3.12 -X utf8 tools/onto/recipes-bake.py   →  data/onto-recipes.json   (걸음마다 쓴 파일·칸이 없으면 끝 코드 1)
import json, os, sys, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = lambda p: json.load(open(os.path.join(ROOT, 'data', p), encoding='utf-8'))
OUT = os.path.join(ROOT, 'data', 'onto-recipes.json')
TODAY = datetime.date.today()
ERR = []


def dist(lat1, lon1, lat2, lon2):
    return math.hypot((lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2)) * 111320, (lat2 - lat1) * 110540)


DIRK = {'I': '내선', 'O': '외선', 'U': '상행', 'D': '하행'}   # 지하철 혼잡도 방향 코드


def need(cond, msg):
    if not cond:
        ERR.append(msg)
    return cond


HOW = [
    {'n': '① 무엇이 있나', 't': '대상을 정한다 — 학교·역·동·교차로·경찰서처럼 「이름 붙은 것」. 자료 파일의 한 줄이 대상 하나다.'},
    {'n': '② 무엇과 이어지나', 't': '같은 자리(좌표·행정동·관할), 같은 때(날짜·시각), 같은 코드(학교 ID·교차로 번호)로 다른 자료를 붙인다. 이것이 「엮기」다 — 새 자료를 캐는 것이 아니라 흩어진 공개 자료를 같은 열쇠로 모은다.'},
    {'n': '③ 그래서 무엇을 하나', 't': '모인 값을 사람이 판단하기 쉽게 문장으로 — 갈래마다 따로 보이고 한 점수로 합치지 않는다. 문턱이 있으면 그 출처를 같이 적는다.'},
    {'n': '④ 해 보고 다시 적는다', 't': '한 일과 결과를 남기면 다음 판단의 근거가 된다(온톨로지 「조치」). 개인정보는 적지 않는다 — 사람이 아니라 상황을 적는다.'},
    {'id': 'chase', 'q': '신고 차량이 빠져나갈 곳 — 어느 관서에 먼저 알리나', 'who': ['지역경찰', '교통', '상황실'], 'start': '신고 자리(큰길·고속도로 위) + 가는 쪽',
     'steps': [
         {'n': '출발 길', 'file': 'nav-seoul.json', 'key': '신고 좌표 70m 안 링크 가운데 가는 쪽(방위 60° 안)과 맞는 본선(연결로 아님)', 'take': '길 이름 · 차로 수 · 제한속도', 'grade': 'C'},
         {'n': '앞에 나오는 진출로', 'file': 'nav-seoul.json', 'key': '본선을 따라가며 연결로(링크 칸 [8]=1)로 갈라지는 마디', 'take': '갈림 이름 · 거리 · 진출로 차로 수 · 본선 차로 수', 'grade': 'A'},
         {'n': '빠지면 닿는 길', 'file': 'nav-seoul.json', 'key': '진출로를 따라 3km 안 처음 닿는 일반 길', 'take': '길 이름 · 닿는 자리', 'grade': 'A'},
         {'n': '그 자리 관할', 'file': 'police.json', 'key': '닿는 자리가 든 행정동 → 별표2 관할 경찰서(동 경계 = SGIS)', 'take': '관할 경찰서', 'grade': 'B'}],
     'judge': '길 자료로 「빠질 수 있는 곳」을 차례로 늘어놓은 것이지 「이리로 갔다」가 아니다. 끝 차로였다면 바로 다음 진출로, 1차로였다면 본선을 먼저 본다(데이터 압축지도 「🚨 신고 차량 예측」이 차로·신호를 넣어 갈 가능성을 어림한다). 관할서 이름은 닿는 자리 하나의 관할이다.',
     'act': ['가장 가까운 진출로 두 곳의 닿는 길 관할서에 먼저 공조 요청', '본선 다음 큰 나들목 둘레 관서에 이어서', '진출로 끝 신호 교차로는 데이터 압축지도에서 적색 대기 시각을 확인', '차종·색만 공유하고 개인정보는 무전·공조 시스템으로']},
    {'id': 'crowd', 'q': '지금 사람이 몰리는 곳 — 몇 시까지 붐비나', 'who': ['경비', '지역경찰', '교통'], 'start': '서울 실시간 장소(121곳)',
     'steps': [
         {'n': '지금 붐빔', 'file': 'live-seocho.json', 'key': '장소 코드(서울 실시간 도시데이터)', 'take': '붐빔 단계 · 추정 인원 범위 · 받은 시각', 'grade': 'A'},
         {'n': '앞으로 12시간', 'file': 'live-seocho.json', 'key': '같은 장소의 예측(fcst)', 'take': '가장 붐빌 때 · 「여유」로 풀리는 첫 시각', 'grade': 'A'},
         {'n': '가까운 역 평소 혼잡', 'file': 'subway-crowd.json', 'key': '장소 이름에 든 역 이름', 'take': '방향별 퇴근 18~20시 가장 높은 혼잡 %', 'grade': 'B'}],
     'judge': '실시간 값이라 열 때마다 바뀐다(받은 시각을 같이 본다). 인원은 통신사 기지국으로 어림한 범위다. 「약간 붐빔」 이상이면 보는 자리로 둔다 — 단계 낱말은 서울시 원문 그대로.',
     'act': ['「붐빔」 단계인 곳은 출구·횡단보도 배치를 앞당긴다', '예측에서 붐빔이 풀리는 시각까지 인원을 남긴다', '역 혼잡이 높은 방향은 역무실과 공유']},
    {'id': 'elder', 'q': '이 동 어르신 — 실종·보행 사고를 어디서 볼까', 'who': ['지역경찰', '여청', '교통'], 'start': '행정동',
     'steps': [
         {'n': '어르신 인구', 'file': 'police-func/<시도>.json', 'key': '행정동 8자리', 'take': '70세 이상 주민 · 주민 대비 %', 'grade': 'A'},
         {'n': '보행 사고', 'file': 'police-func/<시도>.json', 'key': '같은 줄', 'take': '보행자 피해(10년)', 'grade': 'A'},
         {'n': '119 신변·위치 확인 출동', 'file': 'rescue119/<시도>.json', 'key': '법정동 → 걸친 행정동(넓이 %)', 'take': '한 해 신변·위치 확인 출동 · 신고→출동 가운데값', 'grade': 'B'}],
     'judge': '갈래마다 따로 본다. 119 신변·위치 확인에는 어르신만이 아니라 모든 연령의 위치 확인이 들어 있다(자살 추정도 이 갈래로 묶여 있다 — 원자료 그대로). 법정동 값은 그 법정동 전체다.',
     'act': ['어르신이 많은 동은 실종 신고 때 처음 30분 수색 동선(공원·하천·역)을 미리 정한다', '보행 사고가 많은 동의 무단횡단 잦은 곳에 낮 시간 계도', '배회감지기·지문 사전등록을 주민센터와 같이 안내']},
]
GRADE = {'A': '원자료에 그대로 있는 값', 'B': '원자료끼리 코드·이름으로 맞댄 값', 'C': '자리 거리로 붙인 어림(몇 m 안)'}

RECIPES = [
    {'id': 'school', 'q': '이 학교 둘레 — 등하교 때 무엇을 봐야 하나', 'who': ['여청', '교통', '학부모'], 'start': '학교',
     'steps': [
         {'n': '관할', 'file': 'school-police/<시도>.json', 'key': '학교 ID → 행정동·경찰서·지구대', 'take': '관할 경찰서 · 지구대(근사) · 행정동', 'grade': 'B'},
         {'n': '어린이보호구역', 'file': 'child-zone/<시도>.json', 'key': '학교 이름 맞대기 → 없으면 학교 300m 안 초등학교 구역', 'take': 'CCTV 대수 · 보호구역 도로 폭', 'grade': 'B'},
         {'n': '학교 둘레 업소', 'file': 'edu-zone-biz/<시도>.json', 'key': '학교 점 200m 안(교육환경보호구역 상대구역 반경의 어림)', 'take': '갈래별 곳 수 — 유흥·단란·노래연습장·PC방·숙박', 'grade': 'C'},
         {'n': '그 동 교통사고', 'file': 'police-func/<시도>.json', 'key': '행정동 8자리', 'take': '한 해 평균 사고 · 보행자 피해(10년)', 'grade': 'A'},
         {'n': '학령 인구', 'file': 'dong-kidage/<시도>.json', 'key': '행정동 8자리', 'take': '만 6~11 · 12~14 · 15~17세', 'grade': 'A'},
         {'n': '학사 일정', 'file': 'school-cal-seoul.json', 'key': '날짜', 'take': '오늘 뒤 가장 가까운 방학·재량휴업·졸업식 날', 'grade': 'A'}],
     'judge': '값을 갈래마다 따로 보인다. 업소가 반경 안에 있다고 위반이 아니다(상대구역은 심의로 허용된 곳·학교보다 먼저 있던 곳이 섞인다). 보호구역 CCTV 0대는 「자료에 0」이지 「없다」가 아닐 수 있다.',
     'act': ['등교 07:50~08:40 · 하교 13:00~15:30 횡단보도·보호구역 진입로에서 서행 지도', 'CCTV 가 적은 보호구역은 순찰 차례 앞으로', '업소 밀집 쪽 하교길은 학교전담경찰관과 공유', '방학·재량휴업 날은 등하교 배치를 줄인다']},
    {'id': 'event', 'q': '공연·집회가 끝나는 시각 — 어느 역 출구가 붐비나', 'who': ['경비', '교통', '지역경찰'], 'start': '역',
     'steps': [
         {'n': '오늘 앞뒤 행사', 'file': 'station-events.json', 'key': '역 이름 → 그 역 500m(큰 홀 1km) 안 공연·집회', 'take': '날짜 · 시작·끝 시각 · 객석/신고 인원', 'grade': 'C'},
         {'n': '그 역 평소 혼잡', 'file': 'subway-crowd.json', 'key': '역 이름', 'take': '방향별 퇴근 18~20시 가장 높은 혼잡 %', 'grade': 'A'},
         {'n': '집회 원문', 'file': 'rally-seoul.json', 'key': '날짜 · 시작 자리 500m', 'take': '장소 글 그대로 · 관할서 · 행진 여부', 'grade': 'C'}],
     'judge': '끝나는 시각에 객석·신고 인원만큼 한꺼번에 역으로 온다고 보고, 그 역의 평소 혼잡이 높은 방향을 먼저 본다. 공연 끝 시각이 자료에 없으면 시작 + 공연 시간(분)이다.',
     'act': ['끝나기 30분 전 그 역 출구·횡단보도에 배치', '혼잡이 높은 방향 승강장 쪽은 역무실과 공유', '집회 행진이 있으면 끝 자리 둘레 교차로 신호 수동 대기']},
    {'id': 'night', 'q': '오늘 밤 술자리가 몰리는 동 — 어디를 볼까', 'who': ['교통', '지역경찰'], 'start': '행정동',
     'steps': [
         {'n': '술자리 바탕', 'file': 'dui-ref-seoul.json', 'key': '행정동 코드', 'take': '주점 수 · 호프 매출 중 21~06시 % · 0~6시 결제 건수 · 서울 동 가운데 백분위', 'grade': 'A'},
         {'n': '밤 사고', 'file': 'dui-ref-seoul.json', 'key': '같은 줄', 'take': '10년 사고 중 밤 20~6시 · 0~6시', 'grade': 'A'},
         {'n': '올빼미버스 내리는 곳', 'file': 'night-bus-seoul.json', 'key': '동 가운데 700m 안 정류장', 'take': '마지막 달 하차 많은 정류장', 'grade': 'C'},
         {'n': '관할', 'file': 'dui-ref-seoul.json', 'key': '같은 줄(police.json 동 → 관서)', 'take': '관할 경찰서', 'grade': 'B'}],
     'judge': '백분위를 갈래마다 따로 보인다(합친 점수 없음). 결제한 사람이 운전한다는 뜻이 아니다 — 술자리가 몰리는 시간과 자리를 아는 바탕이다.',
     'act': ['0~6시 결제가 많은 동의 큰길 출구에서 23~02시 음주 단속 자리 검토', '밤 사고 많은 동은 순찰 경로에 넣기', '올빼미버스 하차 정류장 둘레 보행자 사고 주의']},
    {'id': 'flood', 'q': '큰비로 길이 막히면 — 출동이 어디서 얼마나 늦나', 'who': ['지역경찰', '소방', '교통'], 'start': '교차로',
     'steps': [
         {'n': '늦어지는 교차로', 'file': 'flood-delay-seocho.json', 'key': '침수 통제 가정(시나리오) → 교차로마다 평소·통제 때 걸리는 초', 'take': '평소 초 · 통제 때 초 · 가장 빨리 오는 관서가 바뀌나', 'grade': 'B'},
         {'n': '그 자리 119 센터', 'file': 'fire-jur-seoul.json', 'key': '교차로가 든 행정동 → 조례 관할 센터', 'take': '119안전센터(조례 관할 · 기계로 읽음)', 'grade': 'B'}],
     'judge': '시나리오(통제 가정)에서 계산한 값이다 — 실제 비 때는 막히는 길이 다르다. 30초 넘게 늦어지는 교차로만 자료에 있다.',
     'act': ['큰비 예보 때 늦어지는 교차로 둘레는 다른 관서에서 먼저 출동할 수 있게 상황실과 공유', '통제 때 닿지 못하는 교차로는 우회로를 미리 정하기']},
    {'id': 'foreign', 'q': '이 동 외국인 주민 — 어떤 외사 업무가 생길까', 'who': ['외사', '여청', '지역경찰'], 'start': '행정동',
     'steps': [
         {'n': '외국인 주민 갈래', 'file': 'foreign-dong.json', 'key': '행정동 8자리', 'take': '외국인주민 합계 · 근로자 · 결혼이민자 · 유학생 · 외국국적동포 · 자녀', 'grade': 'A'},
         {'n': '주민 대비', 'file': 'police-func/<시도>.json', 'key': '행정동 8자리', 'take': '주민 수 → 외국인 주민 몫 %', 'grade': 'A'},
         {'n': '구 안에서 어디쯤', 'file': 'foreign-dong.json', 'key': '같은 구 행정동끼리', 'take': '외국인 주민 수 차례(구 안)', 'grade': 'A'}],
     'judge': '갈래마다 따로 본다. 외국인 주민이 많다고 범죄가 많은 것이 아니다 — 언어·제도 안내와 피해 신고가 어려운 사람이 많은 자리라는 뜻이다. 행안부 외국인주민 현황(2024.11)은 1년에 한 번 나온다.',
     'act': ['결혼이민자가 많은 동은 가정폭력 피해 신고 길(다국어 1366 · 외국인 도움 1345)을 지구대에 비치', '근로자·동포가 많은 동은 임금 체불·사기 피해 안내', '유학생이 많은 동은 학기 초 전동킥보드·자전거 교통 안내', '다국어 통역이 필요한 신고에 대비해 통역 연락 길을 확인']},
    {'id': 'march', 'q': '집회 행진이 끝나는 곳 — 어느 교차로를 볼까', 'who': ['경비', '교통'], 'start': '집회',
     'steps': [
         {'n': '행진 경로', 'file': 'rally-seoul.json', 'key': '날짜 · 장소 글(「->」 = 행진)', 'take': '시작·끝 자리 · 시각 · 신고 인원 · 관할서', 'grade': 'C'},
         {'n': '끝 자리 둘레 교차로', 'file': 'onto-int.json', 'key': '행진 끝 좌표 300m 안', 'take': '교차로 이름 · 관할 · 연동 부모(종속 신호)', 'grade': 'C'},
         {'n': '그 교차로 신호 자료', 'file': 'onto-int.json', 'key': '같은 줄 has 비트', 'take': '방향별 초 · 경찰청 계획 · 교통과 출력물이 있는지', 'grade': 'A'}],
     'judge': '행진 끝 자리는 게시판 장소 글을 장소 검색으로 잡은 것이라 어림이다. 연동 부모가 있는 교차로는 부모 교차로 신호를 같이 봐야 한다.',
     'act': ['행진 끝 시각 30분 전 끝 자리 교차로에 신호 수동 대기', '연동 부모 교차로 신호를 같은 시각에 확인', '신호 자료가 없는 교차로는 현장 수신호 인원 배치']},
    {'id': 'biz', 'q': '이 동 가게가 늘고 줄고 — 무엇이 달라지고 있나', 'who': ['정보', '생활안전', '지역경찰'], 'start': '행정동',
     'steps': [
         {'n': '업종 조기 신호', 'file': 'esig/<시도>.json', 'key': '행정동 8자리 → 업종(인허가 30갈래)', 'take': '개업 늘어남·줄어듦 · 폐업이 개업보다 많은 해 · 드나듦 잦음(비트마다 따로)', 'grade': 'A'},
         {'n': '서울 상권분석과 맞대기', 'file': 'esig/<시도>.json', 'key': '같은 줄(업종 사전 ind-dict 로 이름 맞댐)', 'take': '최근 4분기 개업·폐업 점포', 'grade': 'B'},
         {'n': '입주 예정 단지', 'file': 'esig/<시도>.json', 'key': '같은 동 redev', 'take': '입주 예정 달 · 세대', 'grade': 'A'}],
     'judge': '점수로 합치지 않는다. 「유망·추천」이 아니다 — 동네가 바뀌는 흐름을 아는 바탕이다. 작은 수(앞 3해 개업 9곳 미만 · 지금 10곳 미만)는 말하지 않는다.',
     'act': ['주점·노래방 개업이 늘어나는 동은 밤 순찰 시간대 다시 보기', '폐업이 이어지는 거리는 빈 점포 둘레 방범 순찰', '입주 예정 단지 둘레는 입주 달 앞뒤 교통·주차 민원 대비']},
]


def run_school():
    sp = D('school-police/11.json'); P = D('police.json'); ST = {s[0]: s[1] for s in P['stations']}
    cz = D('child-zone/11.json'); ez = D('edu-zone-biz/11.json'); pf = D('police-func/11.json'); kid = D('dong-kidage/11.json'); cal = D('school-cal-seoul.json')
    K = pf['keys']
    need('acc' in K and 'ped10' in K, 'police-func 칸 acc·ped10')
    out = []
    picks = [k for k, v in sp['s'].items() if v[7] == '서초구' and v[1] == '초등학교' and v[0] in ('서울이수초등학교', '서울서초초등학교', '서울원명초등학교')]
    for k in picks:
        v = sp['s'][k]; nm, lo, la, d8 = v[0], v[3], v[4], v[5]
        ch = []
        st = ' · '.join(ST.get(s, '?') for s in v[8]); pb = P['pbox'][v[9]][0] if v[9] is not None else None
        ch.append(['관할', '%s · %s(근사) · %s' % (st, pb, v[6]), 'B'])
        z = [x for x in cz['items'] if x[3] == nm or x[3] == nm.replace('서울', '')]
        if not z:
            z = sorted([x for x in cz['items'] if x[2] == '초등학교' and dist(la, lo, x[1], x[0]) < 300], key=lambda x: dist(la, lo, x[1], x[0]))[:1]
        ch.append(['어린이보호구역', ('있음(%s) · CCTV %s · 도로 폭 %s' % (z[0][3], ('%s대' % z[0][5]) if z[0][5] is not None else '대수 자료 없음', ('%sm' % z[0][6]) if z[0][6] is not None else '자료 없음')) if z else '이 학교 이름으로 잡힌 구역 없음', 'B'])
        near = [x for x in ez['items'] if dist(la, lo, x[1], x[0]) < 200]
        cnt = {}
        for x in near:
            g = ez['kinds'][x[2]][0]; cnt[g] = cnt.get(g, 0) + 1
        ch.append(['학교 둘레 업소(200m 어림)', ' · '.join('%s %d' % (g, c) for g, c in sorted(cnt.items(), key=lambda t: -t[1])) or '없음', 'C'])
        dv = pf['dong'].get(d8)
        if need(dv, 'police-func 동 ' + d8):
            ch.append(['그 동 교통사고', '한 해 평균 %s건 · 보행자 피해 10년 %s명' % (dv[2][K.index('acc')], dv[2][K.index('ped10')]), 'A'])
        kv = kid['dong'].get(d8)
        if need(kv, 'dong-kidage 동 ' + d8):
            ch.append(['학령 인구', '초등 나이 %s · 중 %s · 고 %s명 (%s 기준)' % (kv[1], kv[2], kv[3], kid.get('month', '')), 'A'])
        nx = [x for x in cal['days'] if x[0] >= TODAY.isoformat() and (x[1] >= 50 or x[4] >= 20 or x[6] >= 20)]
        if nx:
            y = nx[0]; bits = [b for b in [('초 방학 몫 %s%%' % y[1]) if y[1] else '', ('재량휴업 %s교' % y[4]) if y[4] else '', ('졸업식 %s교' % y[6]) if y[6] else ''] if b]
            cs = [c for c in cal.get('csat', []) if c[0] == y[0]]
            ch.append(['학사 일정', '다음 큰 날 %s%s — %s' % (y[0], ' (수능날)' if cs else '', ' · '.join(bits)), 'A'])
        else:
            ch.append(['학사 일정', '앞으로 큰 날이 자료에 없음', 'A'])
        out.append({'obj': nm, 'where': [la, lo], 'chain': ch})
    return out


def run_event():
    se = D('station-events.json'); sc = D('subway-crowd.json'); out = []
    up = sorted(se['ev'], key=lambda k: -sum(e[4] or 0 for e in se['ev'][k] if e[0] >= TODAY.isoformat()))
    for stn in (['남부터미널'] + [k for k in up if k != '남부터미널'])[:3]:
        evs = [e for e in se['ev'].get(stn, []) if e[0] >= TODAY.isoformat()][:3]
        if not need(stn in se['ev'], 'station-events 역 ' + stn):
            continue
        ch = [['다가오는 행사', ' / '.join('%s %s~%s %s명 · %s' % (e[0][5:], e[2], e[3], e[4], e[5][:24]) for e in evs) or '앞으로 자료에 없음', 'C']]
        cr = [x for x in sc['stn'] if x[0] == stn]
        ch.append(['평소 퇴근 혼잡', ' · '.join('%s %s %s%%' % (x[1], DIRK.get(x[2], x[2] + '방향'), x[7]) for x in cr) if cr else '혼잡도 자료 없는 역', 'A'])
        out.append({'obj': stn + '역', 'chain': ch})
    return out


def run_night():
    dr = D('dui-ref-seoul.json'); nb = D('night-bus-seoul.json')
    seo = [x for x in dr['items'] if x[2] == '11650']
    need(seo, 'dui-ref 서초 동')
    seo.sort(key=lambda x: -(x[10] or 0))
    out = []
    for x in seo[:3]:
        lo, la = x[3]
        ch = [['술자리 바탕', '주점 %s곳 · 호프 매출 중 21~06시 %s%% · 0~6시 결제 %s건/달' % (x[4], x[8], x[10]), 'A'],
              ['서울 동 가운데 백분위', '주점 수 %s · 호프 매출 %s · 0~6시 결제 %s · 밤 사고 %s · 0~6시 사고 %s' % tuple(x[15][:5]), 'A'],
              ['밤 사고(10년)', '%s건 중 밤 20~6시 %s · 0~6시 %s' % (x[12], x[13], x[14]), 'A']]
        stops, seen = [], set()
        for s in sorted([s for s in nb['items'] if dist(la, lo, s[3], s[2]) < 700], key=lambda s: -s[4 + len(nb['months']) - 1][1]):
            if s[1] not in seen:
                seen.add(s[1]); stops.append(s)
        stops = stops[:2]
        ch.append(['올빼미버스 내리는 곳(700m)', ' · '.join('%s(한 달 하차 %s)' % (s[1], s[4 + len(nb['months']) - 1][1]) for s in stops) or '둘레에 없음', 'C'])
        ch.append(['관할', ' · '.join(x[17]) if isinstance(x[17], list) else str(x[17]), 'B'])
        out.append({'obj': x[1], 'where': [la, lo], 'chain': ch})
    return out


def run_flood():
    fd = D('flood-delay-seocho.json'); fj = D('fire-jur-seoul.json')
    out = []
    import importlib
    try:
        from shapely.geometry import shape, Point
        G = [f for f in json.load(open(os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features'] if f['properties']['sgg'] == '11650']
        polys = [(shape(f['geometry']), f['properties']) for f in G]
    except Exception:
        polys = []
    rows = fd.get('polA') or []
    need(rows, 'flood-delay polA')
    for r in rows[:3]:
        lo, la = r[0], r[1]
        ch = [['출동 늦어짐(경찰 · 시나리오 A)', '%s — 평소 %s초 → 통제 때 %s · 가장 빨리 오는 곳 %s%s' % (r[6] or '이름 없는 교차로', r[2], ('닿지 못함' if r[3] == -1 else '%s초' % r[3]), r[4], (' → ' + r[5]) if r[5] else ''), 'B']]
        hit = [p for g, p in polys if g.covers(Point(lo, la))]
        if hit:
            d8 = hit[0]['adm_cd2'][:8]
            cs = fj['d'].get(d8, [])
            ch.append(['그 자리 119(조례 관할)', '%s — %s' % (hit[0]['adm_nm'].split(' ')[-1], ' · '.join(fj['c'][c[0]][1] + (' 일부' if c[2] else '') for c in cs) or '못 읽음'), 'B'])
        out.append({'obj': r[6] or '교차로', 'where': [la, lo], 'chain': ch})
    return out


def run_foreign():
    fd = D('foreign-dong.json')['dong']; pf = D('police-func/11.json'); K = pf['keys']
    seo = sorted([(k, v) for k, v in fd.items() if k.startswith('11650')], key=lambda kv: -(kv[1].get('t') or 0))
    need(seo, 'foreign-dong 서초')
    out = []
    for i, (k, v) in enumerate(seo[:2]):
        dv = pf['dong'].get(k); pop = dv[2][K.index('pop')] if dv else None
        ch = [['외국인 주민 갈래', '합계 %s명 — 근로자 %s · 결혼이민자 %s · 유학생 %s · 외국국적동포 %s · 자녀 %s' % tuple('자료 없음' if v.get(f) is None else v.get(f) for f in ('t', 'w', 'm', 's', 'k', 'c')), 'A'],
              ['주민 대비', ('주민 %s명 가운데 %.1f%%' % (pop, 100.0 * v['t'] / pop)) if pop else '주민 수 자료 없음', 'A'],
              ['구 안에서 어디쯤', '서초구 %d개 동 가운데 %d번째로 많음' % (len(seo), i + 1), 'A']]
        out.append({'obj': dv[0] if dv else k, 'chain': ch})
    return out


def run_march():
    rs = D('rally-seoul.json'); oi = D('onto-int.json'); P = D('police.json')
    it = [x for x in rs['items'] if x.get('march') and x.get('dest')]
    need(it, 'rally-seoul 행진')
    it.sort(key=lambda x: (x['d'], x.get('n') or 0), reverse=True)
    HAS = [(1, '방향별 초'), (2, '경찰청 계획'), (4, '교통과 출력물')]
    out = []
    for x in it[:2]:
        la, lo = x['dest']
        near = sorted([r for r in oi['items'] if dist(la, lo, r[2], r[3]) < 300], key=lambda r: dist(la, lo, r[2], r[3]))[:3]
        ch = [['행진 경로', '%s %s~%s · 신고 %s명 · 관할 %s — %s' % (x['d'], x.get('from') or '?', x.get('to') or '?', x.get('n') or '?', x.get('st'), x['p'][:40]), 'C']]
        ch.append(['끝 자리 둘레 교차로(300m)', ' · '.join('%s(%dm%s)' % (r[1], dist(la, lo, r[2], r[3]), ' · 연동 부모 있음' if r[10] else '') for r in near) or '300m 안 교차로 없음', 'C'])
        ch.append(['그 교차로 신호 자료', ' · '.join('%s: %s' % (r[1], '·'.join(n for b, n in HAS if r[11] & b) or '없음') for r in near) or '—', 'A'])
        out.append({'obj': x['p'][:30], 'where': [la, lo], 'chain': ch})
    return out


def run_biz():
    es = D('esig/11.json'); cats = es['cats']; fl = es['flags']
    dd = es['gu'].get('11650', {}).get('dong', {})
    need(dd, 'esig 서초')
    pick = sorted(dd.items(), key=lambda kv: -sum(1 for r in kv[1]['rows'] if r[8]))[:2]
    out = []
    for k, v in pick:
        sig = [r for r in v['rows'] if r[8]][:5]
        ch = [['업종 조기 신호', ' / '.join('%s %s곳: %s' % (cats[r[0]], r[1], ' · '.join(t for b, t in fl.items() if r[8] & int(b))) for r in sig) or '눈에 띄는 신호 없음', 'A']]
        sv = [r for r in v['rows'] if r[9] and r[8]][:3]
        ch.append(['서울 상권분석과 맞대기', ' / '.join('%s(%s) 최근 4분기 개업 %s · 폐업 %s' % (cats[r[0]], r[9][3], r[9][1], r[9][2]) for r in sv) or '맞댄 업종 없음', 'B'])
        ch.append(['입주 예정 단지', ' · '.join('%s %s %s세대' % tuple(x) for x in (v.get('redev') or [])) or '없음', 'A'])
        out.append({'obj': v['n'], 'chain': ch})
    return out


def run_chase():
    nv = D('nav-seoul.json'); N = nv['nodes']; Lk = nv['links']; P = D('police.json')
    ST = {x[0]: x[1] for x in P['stations']}
    LAB = [[int(t) for t in str(l).split('~')[0].split(',') if t] for l in P['labels']]
    out_ = {}
    for l in Lk:
        out_.setdefault(l[1], []).append(l)
    try:
        from shapely.geometry import shape, Point
        from shapely.strtree import STRtree
        G = [f for f in json.load(open(os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features'] if f['properties']['sido'] in ('11', '41', '28')]
        polys = [shape(f['geometry']) for f in G]; tree = STRtree(polys)
    except Exception:
        G = []
    def jur(lat, lon):
        if not G:
            return '?'
        pt = Point(lon, lat)
        for k in tree.query(pt):
            if polys[int(k)].covers(pt):
                pr = G[int(k)]['properties']; d8 = pr['adm_cd2'][:8]
                lab = P['dong'].get(d8)
                return '%s(%s)' % (' · '.join(ST.get(x, '?') for x in LAB[lab]) if lab is not None else '?', pr['adm_nm'].split(' ')[-1])
        return '?'
    def bear(l):
        a, b = N[l[1]], N[l[2]]
        return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360   # 북 0 · 동 90
    def first_road(l, road, lim=3000):
        seen, fr = set(), [(l, l[3])]
        best = None
        while fr:
            x, dd = fr.pop(0)
            if x[0] in seen or dd > lim:
                continue
            seen.add(x[0])
            if x[8] == 0 and x[7] != road:
                return x
            for y in out_.get(x[2], []):
                fr.append((y, dd + y[3]))
        return best
    out = []
    for nm, la, lo, hd in [('올림픽대로 반포 → 잠실 쪽', 37.5145, 127.0055, 70), ('경부고속도로 양재 → 한남 쪽', 37.4640, 127.0395, 330)]:
        cand = [l for l in Lk if l[8] == 0 and l[5] <= 3 and dist(la, lo, N[l[1]][1], N[l[1]][0]) < 400]
        cand = [l for l in cand if min(abs(bear(l) - hd), 360 - abs(bear(l) - hd)) < 60]
        if not need(cand, 'chase 출발 길 ' + nm):
            continue
        cur = min(cand, key=lambda l: dist(la, lo, N[l[1]][1], N[l[1]][0])); road = cur[7]
        ch = [['출발 길', '%s · %s차로 · 제한 %skm/h' % (road, cur[6], cur[4] or '?'), 'C']]
        seen, dsum, exits = set(), 0, []
        while cur and cur[0] not in seen and dsum < 8000 and len(exits) < 4:
            seen.add(cur[0]); dsum += cur[3]
            nx = out_.get(cur[2], [])
            for r in nx:
                if r[8] == 1 and r[2] != cur[1]:
                    fr = first_road(r, road)
                    if fr and (N[cur[2]][3], fr[7]) not in [(e[0], e[4]) for e in exits]:
                        a = N[fr[1]]
                        exits.append((N[cur[2]][3] or '이름 없는 갈림', dsum, r[6], cur[6], fr[7], jur(a[1], a[0])))
            main = [y for y in nx if y[7] == road and y[8] == 0]
            cur = main[0] if main else None
        ch.append(['앞에 나오는 진출로', ' / '.join('%s %.1fkm(진출로 %s차로 · 본선 %s차로)' % (e[0], e[1] / 1000, e[2], e[3]) for e in exits) or '8km 안 진출로 없음', 'A'])
        ch.append(['빠지면 닿는 길', ' / '.join('%s → %s' % (e[0], e[4]) for e in exits) or '—', 'A'])
        ch.append(['그 자리 관할', ' / '.join('%s → %s' % (e[4], e[5]) for e in exits) or '—', 'B'])
        out.append({'obj': nm, 'where': [la, lo], 'chain': ch})
    return out


def run_crowd():
    lv = D('live-seocho.json'); sc = D('subway-crowd.json')
    ORD = {'여유': 0, '보통': 1, '약간 붐빔': 2, '붐빔': 3}
    pl = [x for x in lv['places'] if x.get('pop')]
    need(pl, 'live-seocho 장소')
    pl.sort(key=lambda x: (-ORD.get(x['pop'].get('lvl'), -1), -(x['pop'].get('max') or 0)))
    out = []
    for x in pl[:2]:
        po = x['pop']
        ch = [['지금 붐빔', '%s · %s~%s명 (%s 받음)' % (po.get('lvl'), int(po.get('min') or 0), int(po.get('max') or 0), po.get('time')), 'A']]
        fc = po.get('fcst') or []
        if fc:
            top = max(fc, key=lambda f: (ORD.get(f[1], -1), f[3] or 0))
            free = [f for f in fc if f[1] == '여유']
            ch.append(['앞으로 12시간', '가장 붐빌 때 %s %s · 「여유」로 풀리는 첫 시각 %s' % (top[0][11:], top[1], free[0][0][11:] if free else '12시간 안 없음'), 'A'])
        else:
            ch.append(['앞으로 12시간', '예측 자료 없음', 'A'])
        st = [r for r in sc['stn'] if r[0] and r[0] in x['name']]
        ch.append(['가까운 역 평소 혼잡', ' · '.join('%s %s %s %s%%' % (r[0], r[1], DIRK.get(r[2], r[2] + '방향'), r[7]) for r in st[:3]) or '이름으로 이은 역 없음', 'B'])
        out.append({'obj': x['name'], 'chain': ch})
    return out


def run_elder():
    pf = D('police-func/11.json'); K = pf['keys']; rs = D('rescue119/11.json')
    seo = sorted([(k, v) for k, v in pf['dong'].items() if k.startswith('11650')], key=lambda kv: -kv[1][2][K.index('old70')])
    need(seo, 'police-func 서초')
    gi = rs['groups'].index('신변·위치 확인')
    out = []
    for k, v in seo[:2]:
        va = v[2]; pop = va[K.index('pop')]
        ch = [['어르신 인구', '70세 이상 %s명 · 주민의 %.1f%%' % (va[K.index('old70')], 100.0 * va[K.index('old70')] / pop if pop else 0), 'A'],
              ['보행 사고', '보행자 피해 10년 %s명' % va[K.index('ped10')], 'A']]
        hits = [it for it in rs['items'] if it[9] and any(a[0] == k for a in it[9])]
        ch.append(['119 신변·위치 확인 출동', ' · '.join('%s 한 해 %s건(신고→출동 가운데값 %s분)' % (it[2], it[5][gi], it[7]) for it in hits) or '이 동에 걸친 법정동 자료 없음', 'B'])
        out.append({'obj': v[0], 'chain': ch})
    return out


def main():
    ex = {'school': run_school(), 'event': run_event(), 'night': run_night(), 'flood': run_flood(), 'foreign': run_foreign(), 'march': run_march(), 'biz': run_biz(), 'chase': run_chase(), 'crowd': run_crowd(), 'elder': run_elder()}
    for r in RECIPES:
        for s in r['steps']:
            f = s['file'].replace('<시도>', '11')
            need(os.path.exists(os.path.join(ROOT, 'data', f)), '파일 없음 ' + f)
        need(ex.get(r['id']), '예시 없음 ' + r['id'])
    doc = {'schema': 'tg-onto-recipes/1', 'made': TODAY.isoformat(),
           'source': '이 저장소 data/ 의 공개 자료 파일(각 걸음의 file) — 레시피 정본은 tools/onto/recipes-bake.py',
           'note': ['질문을 고르면 걸음 차례대로 자료를 엮어 사슬을 보인다 — 사람이 온톨로지를 짜지 않아도 된다',
                    '예시(examples)는 서초 둘레를 굽는 순간 원자료에서 다시 센 값이다 — 화면은 같은 레시피로 누른 대상의 값을 셈한다',
                    '한 점수로 더하지 않는다 · 「위반」「위험 지역」으로 단정하지 않는다 · 등급 C 는 거리로 붙인 어림',
                    '개인정보 없음 — 대상은 학교·역·동·교차로뿐'],
           'how': HOW, 'grade': GRADE,
           'fields': 'recipes[{id, q 질문, who 쓰는 사람, start 출발 대상, steps[{n 걸음, file 자료, key 무엇으로 잇나, take 무엇을 꺼내나, grade}], judge 판단할 때 지킬 것, act 할 일}] · examples{id: [{obj 대상, where [위도, 경도], chain [[걸음, 값 글, 등급]]}]}',
           'recipes': RECIPES, 'examples': ex}
    open(OUT, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, indent=1))
    for k, v in ex.items():
        print('==', k)
        for o in v:
            print('  ', o['obj']); [print('     ', c[0], '|', c[1], '|', c[2]) for c in o['chain']]
    if ERR:
        print('❌', ERR); sys.exit(1)
    print('✅', OUT, os.path.getsize(OUT))


if __name__ == '__main__':
    main()
