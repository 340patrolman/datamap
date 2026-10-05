# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.10.0 — 🤖 AI 길잡이(data/ai.json) · AI(또는 사람)가 이 지도 자료를 스스로 찾아 읽게 하는 한 장
#   시도 → 권역 저장소 → 시군구 코드 → r/<구>/profile.json(행정동 덩어리) · 층 파일 목록·뜻은 data/layers.json · 지어낸 값 없음
#   py -3.12 -X utf8 tools/region/ai-guide-bake.py → data/ai.json
import json, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://340patrolman.github.io/'

def main():
    RG = json.load(open(os.path.join(ROOT, 'data', 'regions.json'), encoding='utf-8'))
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    rep = {r['sido']: r['repo'] for r in RG['regions']}
    gus = [[g['gu'], g.get('name'), rep.get(g['gu'][:2])] for g in IX['gus'] if rep.get(g['gu'][:2])]
    doc = {
        'schema': 'tg-ai-guide/1', 'built': time.strftime('%Y-%m-%d'),
        'what': '데이터 압축지도 — 전국 시군구·행정동의 기본 자료(인구 구성·머무는 사람·이동·카드 소비·가게·집값·교통사고·시설·경찰 관할)를 공공데이터에서 묶은 정적 파일. 서버·키 없이 주소만으로 읽는다.',
        'start_here': '1) 아래 gus 에서 시군구 코드(5자리)를 찾는다 → 2) ' + SITE + '<repo>/r/<코드>/profile.json 을 읽는다(행정동마다 한 덩어리 + gu_summary) → 3) 더 자세한 층이 필요하면 ' + SITE + '<repo>/manifest.json 의 gus[].bytes 에 있는 파일 이름(<층>.json)을 같은 자리에서 읽는다.',
        'profile_sections': {'주민': '주민등록 — 사는 사람(연령 10세·성별)', '머무는 사람(생활인구)': '서울만 — 그 시각 그 동에 있는 사람(통신 추정 · 평일/주말 0~23시)', '카드 매출(추정)': '서울만 — 추정매출(분기 · 시간대·요일·연령·성별 비중 · 업종 상위)',
                             '카드 매출(경기)': '경기만 — 1~6월 월평균 총액(업종 이름 없음)', '유동인구(경기)': '경기만 — 요일별', '가구·주택·사업체(SGIS)': '전국 — 집계구 2023 을 동으로 합', '가게(상가업소)': '전국 — 대분류별 수',
                             '이동(대중교통)': '서울·경기 — 정류장·역 하루 승하차 · 아침 하차÷승차', '교통사고(TAAS 2016~2025)': '전국 — 해마다·사망·중상·보행자·시간대', '집값(실거래)': '전국(지번 좌표 잡힌 만큼) — 평당·전세가율(추정)',
                             '머무는 외국인(서울 생활인구 · 추정)': '서울만 — 장기·단기체류 · 국적', '시설(250m 칸 합 · 근사)': '어린이집·학교·경로당·카메라 등', '치안(경찰 관할)': '별표2 × 행정동 근사 · 대표번호', 'gu_summary': '시군구 — 외국인(체류자격·국적·성별) · 점유형태·학력(2020) · 소득(국세청)'},
        'rules_for_ai': ['주민·생활인구·외국인주민(행안부)·등록외국인(법무부)·체류 외국인(생활인구)은 정의가 달라 더하거나 빼지 않는다', '시군구 값을 동 주민 수로 나누지 않는다', '「추정」「근사」 값은 그렇게 밝힌다',
                         '빈 칸은 자료가 없는 것이지 0 이 아니다', '서울 추정매출과 경기 카드 금액은 직접 견주지 않는다', '출처는 각 파일의 sources/source 를 그대로 인용한다'],
        'other_files': {'layers': SITE + 'datamap/data/layers.json (층 목록 — 파일·범위·출처·이용허락·추정 여부)', 'police': SITE + 'datamap/data/police.json (전국 경찰서·지구대·파출소 · 행정동 관할)',
                        'foreign': SITE + 'datamap/data/foreign.json (시군구 외국인 자세히)', 'regions': SITE + 'datamap/data/regions.json (시도 → 저장소 · 범위)'},
        'privacy': '개인정보 없음 — 사고는 나이·성별·상해·사고번호·날짜의 일을 받는 자리에서 버렸고, 실거래는 매수·매도인·중개사·일자·층을 버렸다.',
        'gus_fields': '[시군구 코드, 이름, 저장소(repo)]', 'gus': gus}
    p = os.path.join(ROOT, 'data', 'ai.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('시군구', len(gus), '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
