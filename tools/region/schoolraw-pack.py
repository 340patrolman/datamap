# -*- coding: utf-8 -*-
"""학교알리미 OpenAPI 응답을 **원문 그대로** 항목 폴더 × 시군구 파일로 싸서 data/school-raw/ 에 둔다.

소유자 2026-10-12 「학교를 선택하면 모든 정보를 보여줘야지」 · 「항목별로 적정 용량의 데이터 폴더로 나누자 · 합리적 효율적으로」.
학교알리미 OpenAPI 는 공공누리 3유형(출처표시 · 변경금지)이다 — 그래서 **값도 칸 이름도 고치지 않고, 칸을 고르지도 묶지도 않는다**.
여기서 하는 일은 받은 응답(JSON)을 폴더·학교급·해 열쇠 밑에 그대로 넣는 것뿐이다(내용 변경 없음 · 어느 해의 응답을 싣느냐만 고른다).
동·구로 묶은 값은 지도가 화면에서 그때그때 더한다(저장소에 굽지 않는다).

  받기(다른 세션): 07_API키/out/schoolinfo/api/<해>_<항목>_<학교급>_<시군구>.json  (fetch_api.py <시도>)
  싸기: py -3.12 -X utf8 tools/region/schoolraw-pack.py
  나오는 것(폴더마다 <시군구>.json 한 장 — 지도는 필요한 폴더만 읽는다):
     index.json      폴더 목록(groups) · 항목 이름 · 해 · 시군구 · 조건
     base/           학교기본정보(가장 새 해) — 지도 점 · 카드 머리                     {raw{학교급: 응답}}
     core/           09 학년별·학급별 학생수 + 10 전·출입 — 카드의 표 · 동·구 합       {raw{학교급: {항목: {해: 응답}}}}
     i<항목>/        그 밖의 항목 하나씩 — 카드에서 그 항목을 펼칠 때만                 {raw{학교급: {해: 응답}}}
"""
import glob, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'schoolinfo', 'api')
OUT = os.path.join(ROOT, 'data', 'school-raw')
ITEMS = {'0': '학교기본정보', '09': '학년별·학급별 학생수', '10': '전·출입 및 학업중단 학생 수', '63': '성별 학생수', '51': '입학생 현황', '59': '방과후학교 운영 계획 및 운영·지원현황',
         '94': '대상별 학교폭력 예방교육 실적', '61': '학생·학부모 상담', '43': '안전교육 계획 및 실시현황', '38': '보건관리', '44': '시설안전 점검', '16': '학교용지'}
KINDS = {'02': '초등학교', '03': '중학교', '04': '고등학교'}
CORE = ['09', '10']                                   # 카드의 표와 동·구 합이 늘 쓰는 것 — 한 폴더에
LATEST_ONLY = {'94', '61', '43', '38', '44', '16'}    # 안전·생활 항목 — 세 해를 다 실으면 저장소가 100MB 를 넘는다. 가장 새 공시연도의 응답만(응답 자체는 원문 그대로 · 지난 해는 학교알리미에서)
SOURCE = '학교알리미(교육부 · 한국교육학술정보원) OpenAPI — https://www.schoolinfo.go.kr/openApi.do'
LICENSE = '공공누리 3유형(출처표시 · 변경금지) — 응답 원문을 값·칸 이름 그대로 실었다(고르거나 묶지 않았다). 이 자료로 2차 저작물을 만들지 않는다'


def dump(path, doc):
    json.dump(doc, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return os.path.getsize(path)


def main():
    files = sorted(glob.glob(os.path.join(SRC, '*.json')))
    if not files:
        sys.exit('받은 파일이 없다: ' + SRC)
    tree, years, gus = {}, set(), set()
    for f in files:
        yr, it, kd, gu = os.path.basename(f)[:-5].split('_')
        if kd not in KINDS:
            continue
        raw = json.load(open(f, encoding='utf-8'))
        if raw.get('resultCode') != 'success':
            print('건너뜀(성공 아님)', os.path.basename(f)); continue
        tree.setdefault(gu, {}).setdefault(kd, {}).setdefault(it, {})[yr] = raw
        years.add(yr); gus.add(gu)
    years = sorted(years); last = years[-1]
    have = set(it for g in tree.values() for kd in g.values() for it in kd)
    others = [it for it in ITEMS if it in have and it != '0' and it not in CORE] + sorted(it for it in have if it not in ITEMS)
    # 옛 꼴(<시군구>.json 이 맨 위에 있던 것)과 옛 폴더를 치운다 — index·labels 는 둔다
    for f in glob.glob(os.path.join(OUT, '*.json')):
        if os.path.basename(f) not in ('index.json', 'labels.json'):
            os.remove(f)
    for d in ['base', 'core'] + ['i' + it for it in others]:
        shutil.rmtree(os.path.join(OUT, d), ignore_errors=True); os.makedirs(os.path.join(OUT, d))
    made = __import__('datetime').date.today().isoformat()
    size = {}; nsch = {k: 0 for k in KINDS}
    head = lambda sch, gu: {'schema': sch, 'made': made, 'source': SOURCE, 'license': LICENSE, 'gu': gu}
    for gu in sorted(gus):
        G = tree[gu]
        base = {kd: G.get(kd, {}).get('0', {}).get(last) for kd in KINDS}
        for kd in KINDS:
            nsch[kd] += len((base[kd] or {}).get('list') or [])
        doc = head('tg-school-raw-base/1', gu); doc.update({'year': last, 'fields': 'raw{학교급 코드(02 초 · 03 중 · 04 고): 학교기본정보 응답 원문 {resultCode, resultMsg, list[학교마다 원문 칸]}}', 'raw': base})
        size['base'] = size.get('base', 0) + dump(os.path.join(OUT, 'base', gu + '.json'), doc)
        doc = head('tg-school-raw/2', gu); doc.update({'years': years, 'fields': 'raw{학교급 코드: {항목 번호(09 · 10): {공시연도: 응답 원문}}} — 학교는 SCHUL_CODE 로 잇는다',
                                                        'raw': {kd: {it: G.get(kd, {}).get(it, {}) for it in CORE} for kd in KINDS}})
        size['core'] = size.get('core', 0) + dump(os.path.join(OUT, 'core', gu + '.json'), doc)
        for it in others:
            ys = [last] if it in LATEST_ONLY else years
            doc = head('tg-school-raw-item/1', gu); doc.update({'item': it, 'name': ITEMS.get(it, it), 'years': ys, 'fields': 'raw{학교급 코드: {공시연도: 응답 원문}} — 학교는 SCHUL_CODE 로 잇는다(한 학교가 여러 줄인 항목이 있다)',
                                                                 'raw': {kd: {y: G.get(kd, {}).get(it, {}).get(y) for y in ys if G.get(kd, {}).get(it, {}).get(y)} for kd in KINDS}})
            size['i' + it] = size.get('i' + it, 0) + dump(os.path.join(OUT, 'i' + it, gu + '.json'), doc)
    groups = {'base': {'items': ['0'], 'years': [last]}, 'core': {'items': CORE, 'years': years}}
    for it in others:
        groups['i' + it] = {'items': [it], 'years': [last] if it in LATEST_ONLY else years}
    for k in groups:
        groups[k]['mb'] = round(size.get(k, 0) / 1e6, 1); groups[k]['kb_per_file'] = round(size.get(k, 0) / 1e3 / max(1, len(gus)))
    idx = {'schema': 'tg-school-raw-index/2', 'made': made, 'source': SOURCE, 'license': LICENSE,
           'note': ['**응답 원문 그대로다** — 값도 칸 이름도 고치지 않았고 칸을 고르지 않았다. 묶은 표는 저장소에 굽지 않는다(지도가 화면에서 더한다)',
                    '폴더 = 항목 묶음(groups) · 파일 = 시군구 하나 — 지도는 학교 점에 base, 카드의 표와 동·구 합에 core, 그 밖의 항목은 펼칠 때 그 폴더만 읽는다',
                    '졸업생 진로(대학·상급학교 진학) · 교과별 학업성취 · 학교폭력 심의 건수 · 학생 안전사고는 OpenAPI 에 없다 — 학교알리미의 학교별 화면에만 있다(school_page 주소에 SHL_IDF_CD 를 붙인다)',
                    '안전·생활 항목(' + ' · '.join(sorted(LATEST_ONLY)) + ')은 가장 새 공시연도의 응답만 실었다(저장소 크기 때문 — 지난 해는 학교알리미에서 본다)',
                    '공시연도는 최근 3년만 온다 · 받은 시군구는 gus 에 있는 곳(서울·경기·인천) · 초·중·고(특수·각종학교는 받지 않았다)',
                    '칸 이름의 뜻은 labels.json(학교알리미 「공개용 데이터」 화면의 표 머리) — 사전에 없는 칸은 칸 이름 그대로 보인다'],
           'fields': 'groups{폴더: {items[항목 번호], years[실린 공시연도], mb, kb_per_file}} · items{항목 번호: 이름} · kinds{학교급 코드: 이름} · years[공시연도] · gus[시군구 코드] · 파일 = <폴더>/<시군구>.json',
           'groups': groups, 'items': {k: v for k, v in ITEMS.items() if k in have}, 'kinds': KINDS, 'years': years, 'gus': sorted(gus), 'count': nsch,
           'school_page': 'https://www.schoolinfo.go.kr/ei/ss/Pneiss_b01_s0.do?SHL_IDF_CD='}
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('시군구', len(gus), '· 해', years, '· 학교', nsch, '· 합', round(sum(size.values()) / 1e6, 1), 'MB')
    for k in groups:
        print('  %-5s %6.1f MB · 파일마다 약 %4d KB · 항목 %s · 해 %s' % (k, groups[k]['mb'], groups[k]['kb_per_file'], ','.join(groups[k]['items']), ','.join(groups[k]['years'])))


if __name__ == '__main__':
    main()
