# -*- coding: utf-8 -*-
# 데이터 갱신 점검 — Claude Code 세션이 열릴 때(SessionStart 훅) 돈다. 통신 0 · 2초 안.
# 소유자 지시(2026-10-04): 「클로드코드를 켜면 자동으로 찾아서 수정·보완·입력·삭제가 되도록」
# 하는 일: 데이터 압축지도 자료 파일마다 마지막 커밋 날짜를 보고, 다시 굽는 주기를 넘긴 것을 목록으로 낸다.
#          이 출력은 세션 문맥에 들어가고, 그 세션의 Claude 가 목록대로 다시 굽고 검증해 커밋한다(MAP2D.md §6·§8).
# 키·자료 값은 읽지 않는다(파일 날짜만 본다).
import datetime, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KB = os.path.dirname(ROOT)
# [파일, 주기(일), 다시 굽는 법(auto = 키만 있으면 혼자 돈다 / hand = 사람·브라우저 단계가 있다), 명령·절차]
SETS = [
    ['data/r/41111/lamp.json', 183, 'hand', '경기데이터드림 시트 다시 받기(regionwork/ggsheet.py) → `tools/region/gg-life-bake.py`(AED·화장실·주차장·충전소·응급·축제·보안등)'],
    ['data/r/11680/fac.json', 365, 'auto', 'KOSIS 서울 동별 사업체(해마다 새 해) — `tools/region/biz10-bake.py fetch` → `build`(fac-bake 다음)'],
    ['data/r/11650/itscctv.json', 30, 'auto', 'ITS CCTV 목록(영상 주소) — `tools/region/itscctv-bake.py fetch` → `build`(ITS 2건) · 지도에서 영상이 안 열리면 더 자주'],
    ['data/biz-rates.json', 365, 'hand', '해마다 1월 — 최저임금·4대보험·산재·카드 우대수수료·기준금리 고시를 확인해 data/biz-rates.json 을 고친다'],
    ['data/biz-krei.json', 365, 'hand', '농식품부 「외식업체 경영실태 조사 통계보고서」 새 해 PDF → `tools/region/krei-bake.py <pdf>`(표 번호가 바뀌었는지 먼저 본다)'],
    ['data/biz-bench.json', 365, 'auto', 'KOSIS 소상공인실태조사 새 해 → `tools/region/sbiz-bake.py fetch` → `build`'],
    ['data/r/11650/dongw.json', 92, 'auto', '`tools/region/dongw-bake.py fetch` → `build`(서울 아파트·직장인구-행정동 분기)'],
    ['data/gu-tax.json', 365, 'auto', '`tools/region/guTax-bake.py`(국세통계 새 해)'],
    ['data/r/41111/ggdong.json', 183, 'hand', '경기데이터드림 카드매출_행정동·유동인구 요일별 행정동 새 달 확인 → `tools/region/gg-dong-bake.py fetch` → `build`(빠짐없이 담긴 달만 MONTHS 에)'],
    ['data/cpi.json', 31, 'auto', '`tools/region/cpi-bake.py`(소비자물가 다음 달)'],
    ['data/area-ref.json', 92, 'auto', '`tools/region/ref-bake.py`(dong·jgg 다시 구운 뒤)'],
    ['data/airkorea-stations.json', 365, 'auto', '에어코리아 측정소 자리 — `tools/region/airkorea-bake.py fetch` → `build`(504 가 나면 다시)'],
    ['data/r/11650/live250.json', 31, 'auto', '서울 250m 생활인구 — `tools/region/live250-bake.py` 의 DAYS 를 최근 평범한 한 주(명절·연휴 피함)로 바꾸고 `fetch` → `build`'],
    ['data/r/11650/rtms.json', 31, 'auto', '상업업무용 매매 실거래 — `tools/region/rtms-bake.py` 의 END 를 지난달로 올리고 `fetch`(새 달·새 지번 좌표만 받음) → `build`'],
    ['data/foreign.json', 365, 'auto', '외국인 — 행안부 외국인주민(해마다 11월 1일 · 다음 해 말 공표) · 법무부 등록외국인(연말) → `tools/region/foreign-bake.py` → `tools/region/foreign-detail.py`'],
    ['data/police.json', 183, 'auto', '경찰 관할·지구대 — 별표2 개정(직제 시행규칙)·지구대 주소 새 판(공공데이터포털 15077036) → 13_관할경계 다시 맞춤 → `tools/region/police-bake.py`'],
    ['data/base/index.json', 182, 'auto', '전국 바탕 조각 — kr.pbf 새로 → `tools/map2d-build/tiles-bake.py`(5분) → `tools/map2d-build/sgg-bake.py` → `tools/region/publish-data.py tiles`'],
    ['data/r/11650/home.json', 2, 'auto', '주택 실거래 — 지번 좌표가 다 찰 때까지 날마다 `tools/region/home-bake.py geo`(브이월드 하루 한도 · 거래 많은 지번부터) → `build` · 다 차면 주기를 31일로 · 새 달은 END 를 올리고 `fetch <서비스>` 8개 동시'],
    ['data/r/11650/pts250.json', 92, 'auto', '점 자료 250m 칸 — 상가·안전·생활시설·정류장·사고 중 하나를 다시 구우면 `tools/region/pts250-bake.py`(3분)'],
    ['data/r/11650/taas250.json', 365, 'hand', 'TAAS 사고 250m — 앱 안 브라우저 TAAS GIS 화면에서 법정동 5자리 코드 × 해 × 등급으로 다시 모아(MAP2D.md v2.4.0 ⑧ · 새 해 자료가 열리면) 07_API키/out/region/taas250/raw_*.json → `tools/region/taas250-bake.py`'],
    ['data/r/11650/grid.json', 365, 'auto', '250m 격자 뼈대 — 행정동 경계(hjd)가 바뀌면 `tools/region/grid250.py`(약 5분) 다음 live250·rtms build'],
    ['data/b2a.json', 365, 'auto', '법정동→행정동 표 — 07_API키/out/b2a 를 비우고 `tools/region/b2a-bake.py`(브이월드 법정동 경계 · 행정구역 개편 때)'],
    ['data/r/11650/jcnm.json', 183, 'hand', 'itsl 과 같은 NODELINKDATA 새 판으로 `tools/region/jcnm-bake.py <풀어 둔 폴더> <판 날짜>`(교차로·도로 이름 · 1분)'],
    ['data/r/11650/itsl.json', 183, 'hand', 'its.go.kr 「전국표준노드링크」 새 판 NODELINKDATA.zip 받기(약 270MB · 공개) → 풀어서 `tools/region/itsl-bake.py <MOCT_LINK.shp> <판 날짜>`'],
    ['data/r/11650/jgg.json', 365, 'auto', '통계청 SGIS 새 해 집계구 통계 — `tools/region/sgis-bake.py` 의 YEAR 를 올리고 07_API키/out/sgis 를 비운 뒤 `fetch` → `build`(1,027동 · 약 1시간)'],
    ['data/r/11650/trdhl.json', 92, 'auto', '`py -3.12 -X utf8 tools/region/trdhl-bake.py fetch` → `build`(서울 골목상권 배후지 · 분기)'],
    ['data/r/41111/ggtrd.json', 92, 'hand', '경기데이터드림 발달·골목상권 영역(시트) + TBGGESTDEVALLSTM 새 분기 → `tools/region/gg-trdar-bake.py`'],
    ['data/live-seocho.json', 0.5, 'auto', '작업 스케줄러 「SEOUL-PATROL 실시간 지도 갱신」(3시간마다) — 멈췄으면 `py -3.12 tools/live-refresh.py`'],
    ['data/flow-seocho.json', 31, 'auto', '`py -3.12 tools/flow-bake.py flow`(교통카드 다음 달 · 동 매출 다음 분기)'],
    ['data/pubdata-seocho.json', 31, 'auto', '`perl tools/map2d-build/build_pub.pl`(생활인구·지하철·버스·병의원·약국 — 원자료를 먼저 다시 받는다)'],
    ['data/events-seocho.json', 31, 'auto', '서울시 문화행사 OA-15486 + 서울경찰청 오늘의 주요집회(CLAUDE.md v0.10.44) — 끝난 행사는 지우고 새 것을 넣는다'],
    ['data/trend-seocho.json', 92, 'auto', '`py -3.12 tools/trend-bake.py`(새 분기 매출 · 해마다 6월 지하철)'],
    ['data/trdar-seocho.json', 92, 'hand', '상권 영역 shp(OA-15560) 받은 뒤 `py -3.12 tools/trdar-bake.py <shp>` — 새 분기(STDR_YYQU_CD)가 나왔는지 먼저 본다 · ⚠ 구운 뒤 `tools/region/q3-fix.py`(분기 합계 → 한 달 평균)'],
    ['data/stores-seocho.json', 92, 'auto', '소상공인 상가정보 storeListInDong(키 data_go_kr · CLAUDE.md v0.10.65)'],
    ['data/pop-seocho.json', 92, 'hand', '행안부 주민등록 인구(jumin.mois.go.kr POST · CLAUDE.md v0.10.26)'],
    ['data/traffic-vol-seocho.json', 92, 'auto', '서울시 VolInfo `…/VolInfo/1/40/{지점}/{YYYYMMDD}/{HH}/`(CLAUDE.md v0.10.44)'],
    ['data/safety-seocho.json', 182, 'auto', '`py -3.12 tools/safety-bake.py`'],
    ['data/base/index.json', 182, 'auto', 'Geofabrik south-korea-latest.osm.pbf 를 C:/Users/knpth/osmwork/kr.pbf 로 받고(영문 경로) → `py -3.12 -X utf8 tools/map2d-build/tiles-bake.py`(2분) → `tools/map2d-build/sgg-bake.py`'],
    ['data/cameras-seocho.json', 182, 'auto', '전국무인교통단속카메라표준데이터(키 data_go_kr)'],
    ['data/schoolzone-seocho.json', 182, 'auto', '전국어린이보호구역표준데이터 tn_pubr_public_child_prtc_zn_api(키 data_go_kr)'],
    ['data/tgis-seocho.json', 365, 'hand', '서울시 T-GIS A008_P(소유자가 받아 둔 shp) → `perl tools/map2d-build/tgis.pl`'],
    ['data/police-seocho.json', 365, 'hand', '경찰청 지구대·파출소·치안센터 주소 CSV(data.go.kr 15077036·15076962 — 해마다 12월 말 기준) → police_*.pl'],
    ['data/hot10-seocho.json', 365, 'auto', '도로교통공단 다발지 OpenAPI(키 koroad · MAP2D.md §7) — 새 해가 나왔는지'],
    ['data/taas10-seocho.json', 365, 'hand', 'TAAS GIS — 브라우저 안 절차(MAP2D.md §8 ⑧) · 새 해(2026) 자료가 열리면'],
    ['data/season-seocho.json', 182, 'auto', '침수흔적도(OA-15636 · 해마다 봄에 전년분)·제설함·열선·전진기지 다시 받기 → `py -3.12 -X utf8 tools/season-bake.py`(받는 법은 파일 머리 주석)'],
    ['data/pedbtn-seocho.json', 182, 'auto', '서울 API trafficSafetyA077PInfo(OA-15545) → 07_API키/out/season/ped_button.json → `py -3.12 -X utf8 tools/pedbtn-bake.py`'],
    ['data/enforce-seocho.json', 365, 'hand', '경찰청 서울특별시경찰청_경찰서별 교통법규 위반 단속 수(공공데이터포털 15097296 · 해마다 새 해 파일)'],
    ['data/police-stats.json', 365, 'hand', '공공데이터포털 15097296(단속)·15114082(112 출동)·15054738(5대 범죄)·15114084(지역경찰)·15126908(경기남부 범죄) 새 해 파일 → 07_API키/단속통계_20260929/seoul_years 집계 → `py -3.12 -X utf8 tools/map2d-build/police-stats-bake.py`'],
    ['data/heritage-seocho.json', 365, 'auto', '국가유산청 목록 OpenAPI(키 없음)'],
    ['data/r/biz/index.json', 92, 'auto', '서울 상권 1,650곳(매출 분기 · 1년 전 · 점포 · 유동·직장·상주 · 변화지표) — 07_API키/out/region/trdar_* 를 지우고 `py -3.12 -X utf8 tools/region/trdar-bake.py fetch` → `build`(dong-bake build 뒤에 — r/index.json 에 상권 바이트를 더한다) → ⚠ `tools/region/q3-fix.py`(분기 합계 → 한 달 평균) → `profile-bake.py 11`'],
    ['data/r/stores-index.json', 92, 'auto', '서울 상가 점포(소상공인 상가정보 · 분기마다 기준 연월 갱신) — 07_API키/out/region/stores_* 를 지우고 `py -3.12 -X utf8 tools/region/store-bake.py fetch` → `build`(dong·trdar build 뒤에)'],
    ['data/r/rent.json', 92, 'hand', '한국부동산원 임대동향(R-ONE 화면 「임대동향 지역별 임대료·공실률(2024년3분기~)」 5개 표 — CLAUDE.md v0.10.93 받는 법) → `py -3.12 -X utf8 tools/region/rent-bake.py`'],
    ['data/r/11680/transit.json', 31, 'auto', '서울 버스·지하철 승하차(다음 달 교통카드 CSV·CardSubwayTime) — transit-bake.py 의 BUSCSV·YM 을 새 달로 · `py -3.12 -X utf8 tools/region/transit-bake.py`'],
    ['data/r/11680/safety.json', 182, 'auto', '서울 단속 카메라·어린이보호구역·생활안전 시설 — 07_API키/out/region/safe_* 를 지우고 `py -3.12 -X utf8 tools/region/safety-bake.py fetch` → `build`'],
    ['data/r/11680/taas10.json', 365, 'hand', 'TAAS 사고 서울 25개 구 — TAAS GIS 화면 안에서 모으기(CLAUDE.md v0.10.96 절차) → 07_API키/out/region/taas10_raw.json → `py -3.12 -X utf8 tools/region/taas10-bake.py` · 새 해(2026) 자료가 열리면'],
    ['data/r/11560/season.json', 182, 'auto', '서울 계절 위험(침수흔적도 봄마다 전년분 · 제설함 · 열선) — tools/season-bake.py 와 같은 원자료를 다시 받은 뒤 `py -3.12 -X utf8 tools/region/season-bake.py`(바탕 조각 data/base/t 길을 쓴다)'],
    ['data/r/11680/fac.json', 92, 'auto', '동 현황 보강(남녀 · 어린이집·유치원 해마다 · 경로당 · 입시학원 · 상권변화지표 · 점포 추이) — 07_API키/out/region/fac 의 받은 것을 지우고 `py -3.12 -X utf8 tools/region/fac-fetch.py` → (dong-bake fetch 로 jumin_<월>g) → `tools/region/fac-bake.py` · 경로당 자리는 osmwork/addr_scan.py(OSM 도로명주소)'],
    ['data/r/41591/fac.json', 92, 'auto', '경기 동 현황 — 경기 어린이집 ChildHouse·유치원 Kndrgrschoolstus(`tools/region/gg-fac-fetch.py` · ggfac 파일 지우고) · 경기 카드 매출 TB25BPTCARDDONGM(`tools/region/gg-card-fetch.py` · ggcard 폴더 비우고) · 학교·관공서·경로당 OSM(`edu_scan.py`·`gov_scan.py` — pbf 새로 받으면) → `tools/region/fac-bake.py`'],
    ['data/r/11680/jct.json', 365, 'auto', '교차로별 사고 10년 — 사고 10년(taas10) 또는 바탕 조각 교차로가 바뀌면 `py -3.12 -X utf8 tools/region/jct-bake.py`'],
    ['data/r/11680/hot10.json', 365, 'auto', '다발지 10년 서울·경기 — 새 공표 해가 나오면 `tools/region/hot10-bake.py fetch`(1개씩 · 동시 호출하면 막힘) → `build`'],
    # v2.99.0(2026-10-09) 이번 판들에서 생긴 자료
    ['data/mig-dong.json', 31, 'hand', '동별 전입·전출(행정안전부 지역별 인구이동 15108093 · 달마다) — 코워크가 받아 동·달 CSV(07_API키/out/mig) → `py -3.12 -X utf8 tools/region/mig-bake.py "<자료 이름 (받은 날)>"` · 지금 서초·강남만(전국은 받는 방식부터)'],
    ['data/redev.json', 31, 'hand', '입주 예정 단지(손 목록 · 출처·checked) — 새 입주 예정(고시·국토부 15160169·언론)을 더하고, 주민 기준월보다 앞이 된 단지는 add=false 로'],
    ['data/home-ref.json', 92, 'auto', '시도·시군구 집값 기준표 — 실거래(home.json)를 다시 구운 뒤 `py -3.12 -X utf8 tools/region/homeref-bake.py`'],
    ['data/ind-age.json', 92, 'auto', '업종×나이 카드 비중(서울 추정매출 분기) — `py -3.12 -X utf8 tools/region/indage-bake.py`'],
    ['data/popproj.json', 365, 'hand', '통계청 시군구 장래인구추계(KOSIS DT_1BPB002E · 몇 해에 한 번 새 기준) — 새 기준이 공표됐는지 확인 → 다시 굽고 `ppProject` 기준 해(2026·2036) 확인'],
    ['data/r/index.json', 92, 'auto', '서울 25개 구 행정동(주민 연령 매월 · 상권 매출 분기 · 생활인구 월 파일) — 07_API키/out/region 의 받은 것을 지우거나 JUMIN_YM·LOCAL_PEOPLE 달을 올리고 `py -3.12 -X utf8 tools/region/dong-bake.py fetch` → `build`'],
]

def last_commit(path):
    try:
        out = subprocess.run(['git', '-C', ROOT, 'log', '-1', '--format=%cI', '--', path], capture_output=True, text=True, timeout=5).stdout.strip()
        if out: return datetime.datetime.fromisoformat(out)
    except Exception: pass
    p = os.path.join(ROOT, path)
    if os.path.exists(p): return datetime.datetime.fromtimestamp(os.path.getmtime(p)).astimezone()
    return None

# v2.99.0 날짜가 정해진 일 — 기한 DUE_SOON 일 앞부터 알린다 [날짜, 누가(형님/코워크/Claude), 할 일]
DATES = [
    ['2027-04-04', '코워크→형님', '브이월드 개발키 만료(2027-04-04) — 3월 초까지 운영키 전환 신청 · 바뀌면 각 기기 🔑 와 맛보기 중계 VW_KEY 다시 넣기'],
    ['2027-01-31', 'Claude', '해마다 1월 — data/biz-rates.json(최저임금·4대보험·카드 수수료·기준금리) · 세금 계산 요율(tax-rules.json) 새 해 고시 확인'],
    ['2027-05-31', 'Claude', '해마다 4~5월 — 공동주택·개별 공시가격 새 해(hp·jiga) · 침수흔적도 전년분(season)'],
]
DUE_SOON = 60

def main():
    now = datetime.datetime.now().astimezone()
    for d, who, what in DATES:
        left = (datetime.date.fromisoformat(d) - now.date()).days
        if left <= DUE_SOON: print('⏰ ' + ('기한 지남 ' + str(-left) + '일' if left < 0 else str(left) + '일 남음') + ' [' + who + '] ' + what)
    stale, missing = [], []
    for f, days, kind, how in SETS:
        t = last_commit(f)
        if t is None: missing.append(f); continue
        age = (now - t).total_seconds() / 86400
        if age > days: stale.append((f, age, days, kind, how))
    # 실시간 자동 갱신 기록(마지막 줄)
    log = os.path.join(KB, '07_API키', 'out', 'live-refresh.log'); last = ''
    try:
        with open(log, encoding='utf-8') as h: lines = [l.strip() for l in h if l.strip()]
        last = lines[-1] if lines else ''
    except Exception: pass
    if not stale and not missing:
        print('📋 데이터 압축지도 자료 점검(' + now.strftime('%Y-%m-%d %H:%M') + ') — 기한 지난 자료 없음.' + (' 실시간 갱신 마지막: ' + last if last else ''))
        return
    print('📋 데이터 압축지도 자료 점검(' + now.strftime('%Y-%m-%d %H:%M') + ') — 다시 굽는 주기를 넘긴 자료 ' + str(len(stale)) + '건')
    for f, age, days, kind, how in sorted(stale, key=lambda x: (x[3] != 'auto', -x[1] / x[2])):
        print('- [' + ('자동' if kind == 'auto' else '사람 단계') + '] ' + f + ' — 마지막 ' + (str(round(age * 24)) + '시간' if age < 2 else str(int(age)) + '일') + ' 전(주기 ' + (str(int(days * 24)) + '시간' if days < 1 else str(int(days)) + '일') + ') · ' + how)
    for f in missing: print('- [없음] ' + f)
    if last: print('실시간 갱신 마지막 기록: ' + last)
    print('소유자 지시(2026-10-04): 세션이 열리면 이 목록을 찾아 수정·보완·입력·삭제까지 한다 — 1차 출처에 새 자료가 있는지 먼저 확인하고(없으면 「새 자료 없음」으로 끝), '
          '[자동] 은 다시 굽고 [사람 단계] 는 할 수 있는 데까지 한 뒤 막힌 단계를 소유자에게 알린다. 굽은 뒤 map2d 브라우저 검사(콘솔 0 · 해당 층 카드) → 판올림 없이 「data:」 커밋·푸시 · CLAUDE.md 한 줄. '
          '키는 07_API키/keys.json 에서만 읽고 출력·커밋하지 않는다. 지어낸 값·개인정보 금지(MAP2D.md 원칙).')

if __name__ == '__main__':
    try: main()
    except Exception as e: print('📋 데이터 점검 실패: ' + str(e))
    sys.exit(0)
