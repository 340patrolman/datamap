# -*- coding: utf-8 -*-
"""학교알리미 OpenAPI 응답을 **원문 그대로** 구마다 한 묶음으로 싸서 data/school-raw/ 에 둔다.

소유자 2026-10-12 「학교를 선택하면 모든 정보를 보여줘야지」.
학교알리미 OpenAPI 는 공공누리 3유형(출처표시 · 변경금지)이다 — 그래서 **값도 칸 이름도 고치지 않고, 칸을 고르지도 묶지도 않는다**.
여기서 하는 일은 받은 응답(JSON) 여러 장을 구·학교급·항목·해 열쇠 밑에 그대로 넣는 것뿐이다(내용 변경 없음).
동·학군으로 묶은 값이나 견주는 값은 이 자료로 만들지 않는다(그런 것은 1유형인 「공개용 데이터」가 와야 한다).

  받기(다른 세션): 07_API키/out/schoolinfo/api/<해>_<항목>_<학교급>_<구>.json
     https://www.schoolinfo.go.kr/openApi.do?apiKey=&apiType=<항목>&pbanYr=<해>&schulKndCode=<학교급>&sidoCode=11&sggCode=<구>
  싸기: py -3.12 -X utf8 tools/region/schoolraw-pack.py
  나오는 것:
     data/school-raw/index.json            항목 이름 · 해 · 구 목록 · 조건
     data/school-raw/base/<구>.json         학교기본정보(가장 새 해) — 지도 점과 카드 머리
     data/school-raw/<구>.json              나머지 항목 × 해 — 학교를 눌렀을 때
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'schoolinfo', 'api')
OUT = os.path.join(ROOT, 'data', 'school-raw')
ITEMS = {'0': '학교기본정보', '09': '학년별·학급별 학생수', '10': '전·출입 및 학업중단 학생 수', '51': '입학생 현황', '59': '방과후학교 운영 계획 및 운영·지원현황', '63': '성별 학생수'}
KINDS = {'02': '초등학교', '03': '중학교', '04': '고등학교'}
SOURCE = '학교알리미(교육부 · 한국교육학술정보원) OpenAPI — https://www.schoolinfo.go.kr/openApi.do'
LICENSE = '공공누리 3유형(출처표시 · 변경금지) — 응답 원문을 값·칸 이름 그대로 실었다(고르거나 묶지 않았다). 이 자료로 2차 저작물을 만들지 않는다'


def main():
    files = sorted(glob.glob(os.path.join(SRC, '*.json')))
    if not files:
        sys.exit('받은 파일이 없다: ' + SRC)
    tree, years, gus = {}, set(), set()
    for f in files:
        yr, it, kd, gu = os.path.basename(f)[:-5].split('_')
        raw = json.load(open(f, encoding='utf-8'))
        if raw.get('resultCode') != 'success':
            print('건너뜀(성공 아님)', os.path.basename(f)); continue
        tree.setdefault(gu, {}).setdefault(kd, {}).setdefault(it, {})[yr] = raw
        years.add(yr); gus.add(gu)
    years = sorted(years); last = years[-1]
    os.makedirs(os.path.join(OUT, 'base'), exist_ok=True)
    made = __import__('datetime').date.today().isoformat()
    tot = 0; nsch = {k: 0 for k in KINDS}
    for gu in sorted(gus):
        base = {kd: (tree[gu].get(kd, {}).get('0', {}).get(last)) for kd in KINDS}
        for kd in KINDS:
            nsch[kd] += len((base[kd] or {}).get('list') or [])
        doc = {'schema': 'tg-school-raw-base/1', 'made': made, 'source': SOURCE, 'license': LICENSE, 'gu': gu, 'year': last,
               'fields': 'raw{학교급 코드(02 초 · 03 중 · 04 고): 학교기본정보 응답 원문 {resultCode, resultMsg, list[학교마다 원문 칸]}}',
               'raw': base}
        p = os.path.join(OUT, 'base', gu + '.json')
        json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); tot += os.path.getsize(p)
        rest = {kd: {it: tree[gu].get(kd, {}).get(it, {}) for it in ITEMS if it != '0'} for kd in KINDS}
        doc = {'schema': 'tg-school-raw/1', 'made': made, 'source': SOURCE, 'license': LICENSE, 'gu': gu, 'years': years,
               'fields': 'raw{학교급 코드: {항목 번호(index.json 의 items): {공시연도: 응답 원문}}} — 학교는 SCHUL_CODE 로 잇는다',
               'raw': rest}
        p = os.path.join(OUT, gu + '.json')
        json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); tot += os.path.getsize(p)
    idx = {'schema': 'tg-school-raw-index/1', 'made': made, 'source': SOURCE, 'license': LICENSE,
           'note': ['**응답 원문 그대로다** — 값도 칸 이름도 고치지 않았고 칸을 고르지 않았다. 동·학군으로 묶은 값, 학교끼리 견주는 값은 이 자료로 만들지 않는다(변경금지)',
                    '졸업생 진로(대학·상급학교 진학)와 교과별 학업성취는 OpenAPI 에 없다 — 학교알리미의 학교별 화면에만 있다(school_page 주소에 SHL_IDF_CD 를 붙인다)',
                    '공시연도는 최근 3년만 온다 · 받은 시군구는 gus 에 있는 곳(서울·경기·인천) · 초·중·고(특수·각종학교는 받지 않았다)',
                    '칸 이름의 뜻은 학교알리미 OpenAPI 안내서에 있다 — 지도는 뜻을 확인한 칸에만 우리말 이름을 붙이고 나머지는 칸 이름 그대로 보인다'],
           'fields': 'items{항목 번호: 이름} · kinds{학교급 코드: 이름} · years[공시연도] · gus[구 코드] · base = base/<구>.json · detail = <구>.json',
           'items': ITEMS, 'kinds': KINDS, 'years': years, 'gus': sorted(gus), 'count': nsch,
           'school_page': 'https://www.schoolinfo.go.kr/ei/ss/Pneiss_b01_s0.do?SHL_IDF_CD='}
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('구', len(gus), '· 해', years, '· 학교', nsch, '· 합', round(tot / 1e6, 1), 'MB ->', OUT)


if __name__ == '__main__':
    main()
