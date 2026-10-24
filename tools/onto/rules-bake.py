# -*- coding: utf-8 -*-
# 교통 온톨로지 — 규칙 장부 + 현장 지식 기록(소유자 2026-10-15 「계속 진행」 · 티로 사례 「틀리면 사고 나는 규칙만 공통 언어로 못 박는다」)
#   RULE = 틀리면 사고가 나는 규칙 하나 — 정의 · 출처(법령/공식/소유자 말씀/실측/앱 기준) · 주인 앱과 자리 · 정답 시험값
#   FK   = 소유자가 현장에서 말한 판단 하나 — 누가(소유자) · 언제 · 무엇을 · 어디에 적용했나 · 말 그대로
#   → data/onto-rules.json (tg-onto-rules/1) · 온톨로지 코어(ontology-core · 게임 세션)는 이 파일을 「가리키기만」 한다
#   법령 숫자(범칙금·벌점·단가)는 여기 옮기지 않는다 — 정본은 T-Book(LAWS · 시간외 단가)이고 여기는 그 자리만 가리킨다
#   py -3.12 -X utf8 tools/onto/rules-bake.py        (끝 코드 1 = 검사 실패 → 파일 안 씀)
import json, os, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # datamap
KB = os.path.dirname(ROOT)                                                              # 지식베이스

SRC_KIND = {'law': '법령 원문', 'off': '공식 자료', 'own': '소유자 말씀', 'meas': '실측·대조', 'app': '앱 기준(공식 아님)'}
GRADES = 'ABCDE'   # onto-schema 와 같다 — A 원문·공식 · B 받은 값 · C 근사 · D 추정 · E 가설

# ── 규칙 장부 ──────────────────────────────────────────────────────────────
# o = 주인(앱 · 자리) — 'dm:<datamap 안 경로>' 는 파일이 있는지 검사한다 · 'tb:' 'gg:' 는 이름만
RULES = [
    # 관할
    dict(id='RULE-JUR-1', area='관할', title='관할은 법정 관할(직제 시행규칙 별표2)로 가른다 — 청사가 가까운 서가 아니다',
         d='읍·면·동 관할(별표2)을 행정동 경계에 붙여 그 안의 자리면 그 서. 못 가릴 때(바다 등)만 청사 거리.',
         s=[('law', '경찰청과 그 소속기관 직제 시행규칙 별표2(2026.8.31 · DRF MST 289159)', '2026-09-16'), ('off', '통계청 SGIS 행정동 경계(가공 vuski/admdongkor · CC BY 4.0 — 출처 표기 의무)', '2026-09-16')],
         g='A', o=['tb:jurPick · psJur · tbJurAt', 'dm:data/jur-seocho.json'],
         t='화성 향남읍 수직리 → 화성서부(청사 거리로는 오산이 나왔다 · v22.80 사고) · 부산시청 → 연제 (T-Book gate.py 관할 6곳)'),
    dict(id='RULE-JUR-2', area='관할', title='반포동 관할은 현장 기준 — 본동·2동 방배 · 1·3동 서초 · 4동은 반포대로 서쪽 방배(서래) / 동쪽 서초(반포)',
         d='별표2 는 반포동을 두 서에 다 적어 행정동으로 못 가린다 → 현장 경찰관의 관할을 덮어쓴다. 반포4동은 한 동에 관서 둘.',
         s=[('own', 'FK-BANPO-1 · FK-BANPO-2', '2026-10-10')], g='B',
         o=['tb:banpoJur(jurPick 맨 앞)', 'dm:data/jur-seocho.json', 'dm:tools/region/polcard-bake.py'],
         t='구반포역 → 방배 (T-Book gate.py) · 반포대로 서 40m → 방배 · 고속터미널 → 서초'),
    dict(id='RULE-JUR-3', area='관할', title='경계 도로는 북쪽·동쪽 서가 맡는다 — 동서로 난 경계 도로는 북쪽 서 · 남북으로 난 경계 도로는 동쪽 서',
         d='두 서의 경계가 도로 위에 있으면 그 도로 위 교차로는 북쪽(동서 도로)·동쪽(남북 도로) 서 몫이다. 강남대로는 서초서 동쪽 경계라 신사~강남역 = 강남서 · 강남역~양재역 = 수서서. 반포대로(반포4동)는 동쪽 서초서. 행정동 경계만으로 가르면 길 위 교차로가 틀린다.',
         s=[('own', 'FK-JUR-BORDER-1 · FK-JUR-BORDER-2 · FK-JUR-BORDER-3 · FK-JUR-BORDER-4', '2026-10-24'), ('meas', 'T-GIS 교차로 관할 코드와 맞대 봄 — 원칙으로 정한 10곳 모두 T-GIS 와 같음', '2026-10-24')], g='B',
         o=['dm:ontology-core/build.py'],
         t='교보타워사거리·남서울빌딩앞·전기공제회관 → 강남서 · 양재역·양재전화국 → 수서서 · 서울성모병원·강남터미널고가밑·반포대교남단 → 서초서'),
    dict(id='RULE-ADM-1', area='관할', title='행정동 8자리 코드 = 행정안전부 adm_cd2 의 앞 8자리 — 통계청 코드와 다르다',
         d='세 앱이 동을 잇는 열쇠. 통계청(SGIS) 7자리·adm_cd 와 섞으면 동이 엇갈린다.',
         s=[('meas', 'b2a(법정동→행정동) 표와 맞댐', '2026-10-14')], g='A', o=['dm:data/onto-schema.json', 'ontology-core INT.dong'],
         t='게임 세션 온톨로지 코어 질문에 답한 값(2026-10-14)'),
    # 신호 — 읽는 법
    dict(id='RULE-SIG-1', area='신호', title='방향 모르는 신호 계획은 「보통 1현시 = 주도로(통행량 많은 쪽) 직진」으로 읽고 추정이라 밝힌다',
         d='경찰청 신호계획에는 현시 방향이 없다. 실제 신호와 맞댄 표(sig-phmv-seoul.json)가 있으면 그쪽이 이긴다.',
         s=[('own', 'FK-SIG-PHASE1', '2026-10-10'), ('meas', '교통과 현시도 5곳 — 서초역·서초경찰서·성모병원 = 반포대로 남북 직진 · 강남터미널고가밑 = 신반포로 · 삼호가든 = 사평대로', '2026-10-10')],
         g='D', o=['dm:data/sig-phmv-seoul.json', 'gg:경찰청 계획으로 그릴 때'], t='4039·4036·4034 1현시 = 반포대로 직진'),
    dict(id='RULE-SIG-2', area='신호', title='신호 요일 갈래 = 월~목 · 금 · 토 · 일 + 특수일 15종(일요일 계획) — 대체공휴일·선거일·제헌절·노동절은 그 요일 계획',
         d='제어기는 특수일 15종만 안다. 통행량 갈래(쉬는 날 전부 휴일)와 신호 갈래는 다르다.',
         s=[('off', '교통과 신호현시도 KSC-5800SE TOD PLAN 1~4 · 특수일표(4039 · 2026.01.28)', '2026-10-11'), ('own', 'FK-SIG-HOLIDAY', '2026-10-11')],
         g='A', o=['dm:data/sig-special.json', 'dm:tools/signal/spat-bake.py'], t='2026-10-03 개천절 → 일요일 계획 · 대체공휴일 → 그 요일 계획(교통과 손 변경 여부 미확인)'),
    dict(id='RULE-SIG-3', area='신호', title='T-Data 잔여시간은 0.1초 단위 · 값 36000 = 모름 · 방위 = 들어오는 쪽(접근로) · 보행 방위 = 걷는 축',
         d='차량 신호는 3~6초 구간 = 황색 → 그 앞이 녹색. 보행은 이 방법으로 색을 못 가린다.',
         s=[('off', 'T-Data 명세 data_id 10120', '2026-10-10'), ('meas', '청계2가 일방(동만 있음) · 서울 818쌍 대 7쌍(보행=걷는 축)', '2026-10-11')],
         g='A', o=['dm:tools/signal/spat-bake.py'], t='청계2가: 동 접근로만 있고 서는 없음'),
    dict(id='RULE-SIG-4', area='신호', title='「지금 몇 초」는 받은 닻에서 계획 주기(녹+황+적 합)로 이어 센다 — 다시 잰 주기를 쓰면 몇 시간 뒤 100초 어긋난다',
         d='닻(기준 녹색이 켜진 실제 시각)은 두 이동류가 ±3초로 맞고 10분 안 줄일 때만 받는다. 기록은 |ci−주기| ≤ 2.5 · 정수여야 한다.',
         s=[('meas', '교대역 170→172 어긋남 · 서초역 토 17:23 영상 1초 안', '2026-10-10')], g='B',
         o=['dm:tools/signal/spat-bake.py(plan_ci · fz_anchor)', 'gg:sigwait'], t='data/sig-field-check.json'),
    dict(id='RULE-SIG-5', area='신호', title='연동 속도는 이웃 주기가 같을 때만 · 제한속도를 넘는 값은 절대 안 보임 · 밤(22~23시 뒤)은 아예 안 보임',
         d='야간에는 과속을 막으려 일부러 연동을 끊는다 — 경찰 앱이 「이 속도면 계속 녹색」을 내면 안 된다. 옵셋 기준 확인 전에는 계산하지 않는다.',
         s=[('own', 'FK-SIG-NIGHT', '2026-09-11'), ('meas', '반포대로 네 곳 22:00 부터 성모병원만 140초', '2026-09-11')],
         g='A', o=['tb-signal(자매 앱)', 'gg:정속 안내'], t='서초역→서초경찰서 옵셋 없이 빼면 10km/h·124km/h 가 나온다(쓰면 안 되는 값)'),
    dict(id='RULE-SIG-6', area='신호', title='경찰청 신호계획 요일 번호(PLAN_DY·dow) = 1 일 · 2 월 … 7 토 — UTIC 코드정의서·명세서의 「1 월 … 7 일」은 자료와 안 맞는다',
         d='서울(공공데이터포털)·인천·대구·대전(UTIC) 계획 모두 같은 체계로 읽는다. 문서대로 읽으면 토요일이 평일 계획이 되어 주말 신호 예측이 하루씩 어긋난다. 세 도시는 그 도시 실측 대조 전이라 「어림」.',
         s=[('off', 'UTIC sig_code.hwp · PlanCrossRoadInfoService.hwp 「1 월요일 … 7 일요일」(자료와 다름)', '2026-10-18'), ('meas', '서울 T-Data 실제 주기 × 계획: 토 관측 929건 중 7번 89% · 일 601건 중 1번 87%', '2026-10-18')],
         g='B', o=['dm:tools/signal/tod-bake.py', 'dm:tools/signal/utic-tod-bake.py', 'dm:js/map2d.js(신호 카드)', 'tb-signal(자매 앱)'], t='07_API키/out/utic/doc/요일코드_대조_20261018.md'),
    dict(id='RULE-SIG-7', area='신호', title='교통과 신호 출력물(소유자가 공개를 정한 서초 5곳)이 맞는 자료 · T-Data 실시간은 그것과 맞춰 본다 · 그 밖의 교차로는 공개 자료로 찾아지는 값(T-Data 실측 · 경찰청 공개 계획)을 먼저',
         d='반포대로 서초역사거리·서초경찰서·서울성모병원·강남터미널고가밑 + 삼호가든사거리 5곳은 교통과 출력물 값을 싣고, T-Data 실측과 맞대 본다(tools/signal/ksc-compare.py · 결과는 저장소 밖 · 10-18 세 곳 87% 일치). 10-18 낮에 2곳으로 줄였다가 소유자 지시로 5곳으로 되돌림.',
         s=[('own', 'FK-SIG-FINDFIRST', '2026-10-18'), ('meas', '세 곳 교통과 계획 ↔ T-Data 실측 주기 87%(142/164칸) 맞음 · 성모병원 92%', '2026-10-18')],
         g='A', o=['dm:tools/signal/ksc-bake.py(OK 5곳)', 'dm:tools/signal/ksc-compare.py'], t='07_API키/신호앱/교통과_실측대조_<날짜>.md'),
    # 신호 — 수집
    dict(id='RULE-COL-1', area='수집', title='T-Data 는 열쇠·API 짝마다 5분에 한 번 · 하루 1,000 — 이 프로젝트는 열쇠마다 모든 API 합 999 로 멈춘다',
         d='404 = 그 짝에 계약 없음(30분마다 다시 봄) · 429 = 5분 제한. 두 열쇠(KEY1·KEY2) 모두 신호 API 여섯 가지 승인(2026-10-14 15:40).',
         s=[('off', 'T-Data 이용 안내 「1일 1,000회」', '2026-10-14'), ('own', 'FK-COL-999', '2026-10-14'), ('meas', '두 열쇠 번갈아 2분 반 간격 429 없음', '2026-10-14')],
         g='A', o=['dm:tools/signal/spat-bake.py(KeyPool · KEYCAP)'], t='07_API키/out/tdata/keyday.json 하루 합 ≤ 999'),
    dict(id='RULE-COL-2', area='수집', title='수집 단계 = 서초 → 강남·동작·관악·용산·송파 → 한강 이남 여섯 → 서울 · 「다 찼다」= 기록 ≥ 95% 이고 평일 07~22시 칸 ≥ 80%',
         d='한 시간에 한 번 판정해 다음 단계를 바구니에 더한다.',
         s=[('own', 'FK-COL-STAGE', '2026-10-14')], g='B', o=['dm:tools/signal/spat-bake.py(STAGE_GU · stage_done)', 'dm:tools/signal/six-cover.py'],
         t='07_API키/out/tdata/six_cover.md'),
    dict(id='RULE-COL-3', area='수집', title='공개 자료로 끝내 못 받는 교차로는 「받을 수 없음」으로 밝힌다 — 값을 지어 채우지 않는다',
         d='Fusion 응답 없음·잔여 초가 모두 빈 곳(여섯 구 40곳 · 2026-10-14). 그 자리는 교통과 현시도가 있어야 한다.',
         s=[('meas', 'fusion_none.json · fusion_none_why.json', '2026-10-14')], g='A', o=['dm:tools/signal/six-cover.py'], t='인재개발원 3971 = 줄은 오지만 잔여 초 비어 있음'),
    # 길 안내 · 알림
    dict(id='RULE-NAV-1', area='길 알림', title='단속 카메라 알림은 관리기관이 경찰이고 제한속도가 있는 것만 — 구청 카메라는 주정차·버스전용일 수 있다',
         d='단속구분(se) 코드표는 공식 문서로 못 찾았다 → 관리기관으로 가른다. 카메라가 어느 방향을 찍는지는 자료에 없다.',
         s=[('off', '공공데이터포털 15028200 설명(경찰청 소관 = 속도·신호 · 지자체 소관 = 버스전용·주정차)', '2026-10-14'), ('meas', '서울 se 1·2·99 = 모두 서울청 · se 4 = 모두 구청', '2026-10-14')],
         g='C', o=['dm:tools/gargo/alerts-bake.py', 'dm:data/gargo-alerts-seoul.json'], t='서울 경찰 카메라 + 제한속도 2,368대'),
    dict(id='RULE-NAV-2', area='길 알림', title='어린이보호구역 자료는 대상 시설의 점이다 — 「반경 안 = 보호구역 안」으로 말하지 않는다',
         d='「어린이보호구역 시설 가까움」으로 알린다. 구역 경계선은 공개 자료에 없다.',
         s=[('off', '전국어린이보호구역표준데이터', '2026-10-14')], g='A', o=['dm:data/child-zone/11.json', 'dm:data/gargo-alerts-seoul.json'], t='—'),
    dict(id='RULE-NAV-3', area='길 알림', title='조작하는 자리에서 다른 교차로 값을 보이지 않는다 — 300m 넘으면 「이 자리에는 자료가 없습니다」',
         d='자료 없는 다른 교차로가 50m 넘게 더 가까우면 먼 자료를 이 자리 것으로 보이지 않는다.',
         s=[('app', 'T-Book 신호 v0.2~0.3 설계', '2026-09-10')], g='A', o=['tb-signal(자매 앱)'], t='—'),
    dict(id='RULE-NAV-4', area='길 알림', title='걸리는 시간 보정은 공공 실측(ITS 통행속도)으로만 — 카카오 원값·한 번마다의 비율은 저장하지 않고, 가르고와 맞댄 결과는 묶은 값(3건 이상 칸의 가운데값·사분위)만 PC 안에 남긴다',
         d='카카오 약관 원문(코워크 10-15 확인) — 운영정책 제5조·서비스 약관 제11조 ③ 이 결과 저장·2차 이용을 막는다. 소유자 10-15 「대조 결과값은 남겨도 된다」 → 우리 값과 비율을 같은 줄에 두면 카카오 값이 되살아나므로 묶은 값만(권고 · 소유자 승인). 맞대 보기에서 차이가 크면 ITS 배율이나 길 고르기를 고친다 — 숫자를 옮겨 오지 않는다.',
         s=[('own', 'FK-NAV-KAKAO', '2026-10-15'), ('meas', '게임 세션 판단 — kakao_eta.py 수집 중단 · kakao-spot.py 저장 0', '2026-10-15'),
            ('off', '카카오디벨로퍼스 운영정책 제5조(사용자 환경 개선 목적 외 캐시 금지 · 시행 2026-04-20) https://developers.kakao.com/terms/latest/ko/site-policies', '2026-10-15'),
            ('off', '카카오디벨로퍼스 서비스 약관 제11조 ③(사전 승낙 없이 데이터 복사·변경·사용·제공 금지 · 시행 2026-02-06) https://developers.kakao.com/terms/latest/ko/site-terms', '2026-10-15')], g='A',
         o=['dm:tools/signal/etacal-its.py', 'dm:data/eta-cal.json', 'dm:tools/signal/kakao-spot.py', 'dm:tools/signal/spdnormal-bake.py'], t='data/eta-cal.json 의 원자료가 07_API키/out/livespd 뿐인지'),
    dict(id='RULE-NAV-5', area='길 알림', title='교차로 CCTV 는 목록(이름·번호·자리)만 지도에 — 출처 「경찰청 도시교통정보센터(UTIC)」 표기 · 영상은 TOPIS 공식 사이트 · 목록은 하루 1번만 받기',
         d='UTIC 열쇠는 등록 IP 에서만 동작 — 폰·중계 서버에 넣지 않는다. 영상 중계는 허용 문구가 없어 안 한다. 2026-10-15 15:41 두 번째 신청(소속 서초경찰서 · 목적 「경찰업무 보조 연구개발」 · 7종) 승인 열쇠로 바꿈 → 지도·가르고(출동 보조) 모두 목적 안 · 출처 표기는 그대로. 영상은 정차 중·동승자만 · 출동 첫 화면 자동 재생 금지.',
         s=[('off', 'UTIC 「경찰청 교통정보 개방데이터 요청자 준수사항」(2026 개방데이터 세부내용.hwp · 메일 2026-10-06) — 신청 목적 외 사용 불가 · UTIC 표기 · 1초 5회 넘으면 IP 차단', '2026-10-15'), ('own', 'FK-CCTV-1', '2026-10-15'), ('own', 'FK-CCTV-2 — UTIC 신청 목적 「경찰업무 보조 연구개발」', '2026-10-15')], g='A',
         o=['dm:tools/region/utic-cctv-bake.py', 'dm:data/cctv-utic-seoul.json'], t='data/cctv-utic-seoul.json 의 credit 칸 · 영상 주소·열쇠 칸 없음'),
    # 자료 읽는 법
    dict(id='RULE-DATA-1', area='자료', title='서울 상권분석 「당월 매출」은 한 분기(3달) 합계 — 달로 쓰려면 ÷3',
         d='공공 추정이 업종 조사 평균보다 3배 넘게 크면 기간 단위부터 의심한다. 경기 상권 추정은 확인 중.',
         s=[('off', '서울 열린데이터 OA-15572 FAQ 「분기당 매출 금액」', '2026-10-07')], g='A', o=['dm:tools/region/q3-fix.py'], t='서울 상권 합 23.4조가 한 달이면 전국 카드의 4분의 1(불가능)'),
    dict(id='RULE-DATA-2', area='자료', title='사고는 칸 집계만 — 개인정보(성명·연락처·차량번호·주민번호·사건 당사자)는 어느 객체에도 넣지 않는다',
         d='112·내부 자료와 1건 단위 원자료는 공개 저장소 밖에 둔다.', s=[('own', '프로젝트 상시 규칙', '2026-10-04')], g='A',
         o=['ontology-core validate.js(개인정보 꼴)', 'dm:tools/keycheck.py'], t='validate.js 망가뜨린 사본 시험'),
    dict(id='RULE-DATA-3', area='자료', title='VIP(대통령 행차) 경로·시각은 어떤 객체·파일에도 넣지 않는다', d='—',
         s=[('own', '온톨로지 코어 v1 작업지시', '2026-10-14')], g='A', o=['ontology-core schema-ext.json rules'], t='—'),
    dict(id='RULE-DATA-4', area='자료', title='법령·판례 숫자의 정본은 T-Book — 다른 앱은 그 판을 가리키고, 미대조 표시도 그대로 옮긴다',
         d='범칙금·벌점(LAWS 53줄)·판례(PRECDOC)·시간외 단가는 T-Book 이 국가법령정보센터 원문과 대조한 값만.',
         s=[('law', '국가법령정보센터 DRF 원문(T-Book 월간 점검)', '2026-10-08')], g='A', o=['tb:LAWS · PRECDOC', 'ontology-core src/tbook-law.json'],
         t='유턴(§18) 벌점 없음 · 계급 단가 6줄 (T-Book gate.py)'),
    # 앱 기준(공식 아님이라고 밝힐 것)
    dict(id='RULE-APP-1', area='앱 기준', title='하늘 낱말은 운량 20/50/80/90 으로 가른다(맑음·구름조금·구름많음·흐림) — 기상청 예보용어가 아니라 앱 기준',
         d='weather_code 만 보면 운량 44% 가 「맑음」이 된다. 그림과 글이 어긋나면 안 된다.', s=[('app', 'T-Book v22.46', '2026-09-10')], g='E',
         o=['tb:wxSkyKo · wxCloudStep'], t='방배동 2026-09-10 code 1 · 운량 44% → 구름조금'),
    dict(id='RULE-APP-2', area='앱 기준', title='체감 3시간 안 5도 넘게 움직이면 「급변」 — 기상특보가 아니라 앱 기준 · 폭염(체감 33·35)만 기상청 기준',
         d='교통외근은 밖에 서 있어 체온관리가 안전 문제다.', s=[('own', 'T-Book 날씨(체온관리 지시)', '2026-09-10'), ('app', 'WX_SWING=5 · WX_SWING_H=3', '2026-09-10')],
         g='E', o=['tb:wxSwing'], t='—'),
    dict(id='RULE-APP-3', area='앱 기준', title='공휴일은 천문연 특일정보와 「관공서의 공휴일에 관한 규정」 원문으로 대조한 것만 — 2026.5.1 부터 노동절',
         d='2026~2028 은 64/64 일치. 2029~2030 은 규정 계산값(선거일·임시공휴일 미반영).',
         s=[('off', '천문연 SpcdeInfoService', '2026-10-08'), ('law', '관공서의 공휴일에 관한 규정(대통령령 제36290호 · MST 285779)', '2026-10-08')], g='A',
         o=['tb:HOLIDAYS_BASE', 'dm:data/sig-special.json'], t='2028-10-06 은 대체공휴일 아님 (T-Book gate.py)'),
]

# ── 현장 지식 기록(소유자 말씀 · 말 그대로) ────────────────────────────────
FIELD = [
    dict(id='FK-BANPO-1', date='2026-10-04', said='반포본동·반포2동은 반포동 중에 확실히 방배경찰서이고, 반포4동은 반포대로를 기준으로 반포2동·반포본동 쪽이 방배경찰서 관내',
         use=['RULE-JUR-2'], conf='소유자 확인'),
    dict(id='FK-BANPO-2', date='2026-10-10', said='반포4동은 서래지구대와 반포지구대로 나누어진다 — 한 동에 경찰관서가 2개 표시되어야 할 경우가 있다',
         use=['RULE-JUR-2'], conf='소유자 확인 · 1·3동 서초는 같은 날 「이 내용 맞네」'),
    dict(id='FK-SIG-PHASE1', date='2026-10-10', said='지도를 보면 주도로 방향이 1현시야 — 반포대로·서초대로가 있어도 반포대로 남북간부터 1현시로 보통 잡아 · 어긋나는 2곳은 아마 통행량 많은 곳이 주도로일 듯',
         use=['RULE-SIG-1'], conf='「보통」 — 예외 있음'),
    dict(id='FK-SIG-HOLIDAY', date='2026-10-11', said='신호값이 평일과 휴일이 달라 왜냐면 통행량이 다르니까 · 평일 금요일 토요일 일요일 특수일 해서 조금씩 달라',
         use=['RULE-SIG-2'], conf='현시도로 확인 · 대체공휴일에 교통과가 손으로 바꾸는지는 미확인'),
    dict(id='FK-SIG-NIGHT', date='2026-09-11', said='23시가 넘으면 꼭 그런 건 아니지만 중간중간 적색을 넣어 필요 이상의 과속을 막으려고 신호를 끊어 놓았다',
         use=['RULE-SIG-5'], conf='자료로 확인(22:00 부터 성모병원만 140초)'),
    dict(id='FK-SIG-FINDFIRST', date='2026-10-18', said='2곳만 찾아서 올린 걸로 하자 · 딱히 내부 자료라고도 못 해 · 찾아지는 신호값은 찾는 게 우선이고 맞춰 보는 거지 · 실시간 자료와 맞춰 보는 것도 중요해 · 내가 pdf 로 올린 자료가 맞는 자료고 실시간 자료는 맞춰 보는 걸로 · 온톨로지는 공공데이터로만 · 민감한 내용은 빼는 걸로',
         use=['RULE-SIG-7'], conf='소유자 결정 · 성모병원 출력물(2025-12-11)은 최신이고 맞다고 하심(실측 92% 일치)'),
    dict(id='FK-JUR-BORDER-1', date='2026-10-24', said='강남대로는 강남경찰서 관할 강남역부터 양재역까지는 수서경찰서 관할이야 경찰 경계관할 획정 방법은 북에서남 동에서 서 즉 북쪽에 위치한 경찰서가 남쪽에 인접한 도로가 있다면 관할을하고 동쪽에 인접한 경찰서가 바로옆 도로의 동쪽을 우선 관할한다는거지',
         use=['RULE-JUR-3'], conf='소유자 현장 지식'),
    dict(id='FK-JUR-BORDER-2', date='2026-10-24', said='2 3 4 7 방배경찰서 12서초경찰서 한남대교 잠원동쪽도 서초경찰서 단 강남대로는 강남경찰서',
         use=['RULE-JUR-3'], conf='소유자 확인 — 엇갈린 16곳(다이치빌딩·뒷벌어린이공원(연등)2·래미안아트힐·코끼리마트앞 = 방배서 · 삼성R&D캠퍼스·한남대교램프 = 서초서) · 나머지 10곳은 RULE-JUR-3 원칙대로'),
    dict(id='FK-JUR-BORDER-3', date='2026-10-24', said='양재대로 구룡사앞까지 효령로 37길 양재천로 영동2교까지 헌릉로 헌릉ic까지 매헌로 우면산로 주암2교까지 서초서 11번 방배서 12번 명달로 레미안아트힐 앞쪽은 서초경찰서',
         use=['RULE-JUR-3'], conf='소유자 확인 — 원칙대로 계산한 경계 도로 목록에 답함(11 = 사평대로 동작·방배 사이 · 12 = 명달로) · 동작대로·과천대로·논현로는 답 없음(확인 전)'),
    dict(id='FK-JUR-BORDER-4', date='2026-10-24', said='래미안아트힐 교차로도 서초경찰서로 해.',
         use=['RULE-JUR-3'], conf='소유자 결정 — FK-JUR-BORDER-2 의 래미안아트힐 = 방배를 바꿈(명달로 앞쪽 서초와 맞춤)'),
    dict(id='FK-COL-999', date='2026-10-14', said='하루에 키별 999회까지 하자', use=['RULE-COL-1'], conf='지시'),
    dict(id='FK-COL-STAGE', date='2026-10-14', said='우선 서초구부터 완성시키는 쪽으로 · 한강 이남이 완성되면 서울 전체로', use=['RULE-COL-2'], conf='지시'),
    dict(id='FK-OPS-UPSTREAM', date='2026-10-01', said='상류에서 먼저 끊는다 · 분기점 앞에서 · 신호는 소폭(SEOUL PATROL 온톨로지 설계서 ver.1 원칙)',
         use=[], conf='정체 사례 5건의 원칙 — T-Book 성모병원 카드(v23.44)에 글 그대로'),
    dict(id='FK-OPS-PUBLIC', date='2026-10-02', said='공개가능하다 다 공공데이터 (정체 사례·신호 운영 방식 — 성모병원 좌회전 5초 지연 · 서초경찰서 앞 상류 적색 15초 선행 등)',
         use=['RULE-DATA-2'], conf='공개 범위 결정 · 교통과 현시도 원본·판독 JSON 은 여전히 비공개'),
    dict(id='FK-TGIS-LINK', date='2026-10-02', said='T-GIS 「(연등)」 교차로는 부모 교차로 신호에 딸려 돈다(LK_CS_CDE = 부모 코드)', use=['RULE-SIG-1'],
         conf='자료로 확인(서초·방배 비 0 87곳 중 70곳이 「(연등)」)'),
    dict(id='FK-NAV-KAKAO', date='2026-10-15', said='내가 지금 이렇게 카카오로 보정하는게 맞는거지 보조적으로만 사용하고 · 너의 권고대로 진행하자',
         use=['RULE-NAV-4'], conf='소유자 결정(권고 = ITS 로 보정 · 카카오는 검증만)'),
    dict(id='FK-NAV-KAKAO-2', date='2026-10-15', said='카카오 기록을 남기는 게 아니라 가르고와 대조한 결과값을 남기는 것은 문제없다 — 카카오 결과가 아니라 우리와 비교한 결과니까 · (묶은 값만 남기자는 권고에) 권고대로 모두 진행하자',
         use=['RULE-NAV-4'], conf='소유자 결정 · 첫 말씀은 게임 세션이 전함 · 묶은 값 방식은 소유자가 직접 승인'),
    dict(id='FK-CCTV-1', date='2026-10-15', said='(코워크 권고 (나) 「카메라 이름·위치만 지도에 · 누르면 TOPIS 공식 사이트」에) 권고대로 모두 진행하자',
         use=['RULE-NAV-5'], conf='소유자 결정 · 신청 목적 확인은 형님 몫으로 남음'),
    dict(id='FK-CCTV-2', date='2026-10-15', said='UTIC 신청 목적 = 경찰업무 보조 연구개발', use=['RULE-NAV-5'], conf='소유자 말씀(게임 세션이 전함) — 코워크 기록상 첫 신청(10-04 · 키 발급분)의 목적은 「교육·연구용 개인 지도(비영리)」 · 이 말씀은 10-15 형님이 직접 낸 두 번째 신청(소속 서초경찰서 · 7종 · 승인 대기)으로 보임 → 지금 열쇠로는 지도 표시까지 · 가르고(출동) 쓰임은 두 번째 승인 뒤'),
    dict(id='FK-CCTV-3', date='2026-10-15', said='(UTIC 두 번째 신청 승인 메일 15:41 · 형님 지시) keys.json UTIC 교체만 해줘', use=['RULE-NAV-5'], conf='승인 확인 — 메일 2026-10-15 06:41 UTC · 새 열쇠로 CCTV·돌발 시험 통과'),
    dict(id='FK-SIG-4045', date='2026-10-24', said='(법원검찰청 4045 신호값이 겹친다 — 가장 긴 직진은?) 서초대로(동서 방향)', use=['RULE-SIG-1'], conf='소유자 현장 판단 → 원자료 방위 남↔서 바로잡음(spat-bake DIRFIX)'),
    dict(id='FK-CAR-NUM', date='2026-10-08', said='고속309 = 고속도로순찰대 3지구대 9호 · 경찰서 교통순찰차는 서마다 01번부터(많으면 06)', use=[], conf='게임 그림에 적용'),
]


def check():
    bad = []
    ids = [r['id'] for r in RULES] + [f['id'] for f in FIELD]
    for i in set(ids):
        if ids.count(i) > 1: bad.append('ID 겹침 ' + i)
    fk = {f['id'] for f in FIELD}; rk = {r['id'] for r in RULES}
    pii = [re.compile(r'01[016789]-?\d{3,4}-?\d{4}'), re.compile(r'\d{6}-?[1-4]\d{6}'), re.compile(r'\d{2,3}[가-힣]\s?\d{4}')]
    for r in RULES:
        for k in ('id', 'area', 'title', 'd', 's', 'g', 'o', 't'):
            if not r.get(k): bad.append('%s 빈 칸 %s' % (r['id'], k))
        if r['g'] not in GRADES: bad.append('%s 등급 %s' % (r['id'], r['g']))
        for kind, ref, dt in r['s']:
            if kind not in SRC_KIND: bad.append('%s 출처 종류 %s' % (r['id'], kind))
            datetime.date.fromisoformat(dt)
            for x in re.findall(r'FK-[A-Z0-9-]+', ref):
                if x not in fk: bad.append('%s 없는 현장 기록 %s' % (r['id'], x))
        for o in r['o']:
            if o.startswith('dm:'):
                p = o[3:].split('(')[0].strip()
                if not os.path.exists(os.path.join(ROOT, p)): bad.append('%s 자리 없음 %s' % (r['id'], p))
    for f in FIELD:
        datetime.date.fromisoformat(f['date'])
        for u in f['use']:
            if u not in rk: bad.append('%s 없는 규칙 %s' % (f['id'], u))
    blob = json.dumps([RULES, FIELD], ensure_ascii=False)
    for p in pii:
        for m in p.findall(blob):
            if m not in ('고속309',): bad.append('개인정보 꼴 ' + m)
    if '교' + '34' in blob: bad.append('확인코드 평문')
    return bad


def main():
    bad = check()
    if bad:
        print('❌ 검사 실패', len(bad)); [print(' -', b) for b in bad]; sys.exit(1)
    used = {u for f in FIELD for u in f['use']}
    doc = {'schema': 'tg-onto-rules/1', 'made': datetime.date.today().isoformat(),
           'about': '틀리면 사고가 나는 규칙(RULE)과 그 근거가 된 소유자 현장 판단(FK)의 장부 — 세 앱(T-Book · 데이터 압축지도 · 네비 가르고)이 같은 근거를 읽게 한다. 법령 숫자는 옮기지 않고 정본(T-Book) 자리만 가리킨다.',
           'fields': {'rules': '[{id, area, title, d(정의), s[[출처 종류, 무엇, 날짜]], g(등급 A~E), o[주인 앱·자리 — dm: datamap 경로 · tb: T-Book 함수 · gg: 가르고], t(정답 시험값·확인 방법)}]',
                      'field': '[{id, date, said(소유자 말 그대로), use[이 말에 기댄 규칙], conf(확인 정도)}]'},
           'srcKind': SRC_KIND, 'grades': 'A 원문·공식 · B 받은 값 · C 근사 · D 추정 · E 가설(앱 기준 포함)',
           'n': {'rules': len(RULES), 'field': len(FIELD), 'fieldUsed': len(used)},
           'rules': [{'id': r['id'], 'area': r['area'], 'title': r['title'], 'd': r['d'], 's': [list(x) for x in r['s']], 'g': r['g'], 'o': r['o'], 't': r['t']} for r in RULES],
           'field': FIELD}
    p = os.path.join(ROOT, 'data', 'onto-rules.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    by = {}
    for r in RULES: by[r['area']] = by.get(r['area'], 0) + 1
    print('✅ 규칙', len(RULES), by, '· 현장 기록', len(FIELD), '(규칙에 쓰인 것', len(used), ') ·', os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
