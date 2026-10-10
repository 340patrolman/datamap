# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🤖 AI 길잡이(data/ai.json) · AI(또는 사람)가 이 지도 자료를 스스로 찾아 읽게 하는 한 장
#   v2.10.0(2026-10-05) 시도 → 권역 저장소 → 시군구 코드 → r/<구>/profile.json
#   2026-10-10 tg-ai-guide/2(소유자 「AI 가 여기를 보면 대한민국의 거의 모든 공공데이터가 들어 있으니 잘 쓸 수 있게」) —
#     ① catalog = data/*.json 을 훑어 파일마다 주소·크기·만든 날·출처·칸 설명·맨 위 열쇠를 저절로 적는다(손으로 안 적는다 → 파일이 늘어도 다시 굽기만)
#     ② region_layers = 권역 저장소 manifest 의 층(뜻·출처·기준·몇 개 시군구에 있는지)  ③ keys = 코드 체계와 잇는 법  ④ recipes = 자주 묻는 것 → 읽는 차례
#   지어낸 값 없음 — 글은 각 파일의 source/fields/note 를 그대로 옮긴다(길면 자른다 · 전문은 그 파일에)
#   py -3.12 -X utf8 tools/region/ai-guide-bake.py → data/ai.json   (자료 파일을 더하거나 다시 구운 뒤 · data-check 가 주기를 본다)
import json, os, time, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = 'https://340patrolman.github.io/'
def cut(v, n):
    if v is None: return None
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + ' …(전문은 파일에)'
def deep(v, d=0):   # 칸 설명(fields)이 없는 옛 파일용 — 꼴을 저절로 적는다(열쇠 이름 · 값의 종류 · 보기 값) · 뜻을 지어 적지 않는다
    if isinstance(v, dict):
        ks = list(v.keys())
        if d >= 3: return '{…%d}' % len(ks)
        num = sum(1 for k in ks[:20] if str(k).replace('-', '').replace('.', '').isdigit() or len(str(k)) in (5, 8, 10, 19) and str(k)[:2].isdigit())
        if len(ks) > 12 or num >= max(2, len(ks[:20]) // 2): return '{<열쇠 %d개 · 예 %s>: %s}' % (len(ks), cut(str(ks[0]), 24), deep(v[ks[0]], d + 1))
        return '{' + ', '.join('%s: %s' % (k, deep(v[k], d + 1)) for k in ks) + '}'
    if isinstance(v, list):
        if not v: return '[]'
        if d >= 3: return '[…%d]' % len(v)
        if all(not isinstance(x, (list, dict)) for x in v[:8]): return '[%d개 · 예 %s]' % (len(v), cut(json.dumps(v[:4], ensure_ascii=False), 70))
        return '[%d개 × %s]' % (len(v), deep(v[0], d + 1))
    if isinstance(v, str): return '글' if len(v) > 30 else json.dumps(v, ensure_ascii=False)
    return 'null' if v is None else ('참거짓' if isinstance(v, bool) else '수(예 %s)' % v)
def shape(v):
    if isinstance(v, dict): return '{%d}' % len(v)
    if isinstance(v, list): return '[%d]' % len(v)
    return None

def main():
    RG = json.load(open(os.path.join(ROOT, 'data', 'regions.json'), encoding='utf-8'))
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    rep = {r['sido']: r['repo'] for r in RG['regions']}
    gus = [[g['gu'], g.get('name'), rep.get(g['gu'][:2])] for g in IX['gus'] if rep.get(g['gu'][:2])]
    # ① 지도 저장소의 자료 파일
    cat = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', '*.json'))):
        nm = os.path.basename(f)
        if nm in ('ai.json', 'ai-catalog.json'): continue
        try: j = json.load(open(f, encoding='utf-8'))
        except Exception: continue
        e = {'file': nm, 'url': SITE + 'datamap/data/' + nm, 'bytes': os.path.getsize(f)}
        if isinstance(j, dict):
            for k in ('schema', 'title'):
                if isinstance(j.get(k), str): e[k] = j[k]
            for k in ('made', 'built', 'baked', 'asof', 'year', 'last', 'updated'):
                if isinstance(j.get(k), (str, int)): e['date'] = str(j[k]); break
            src = j.get('source') or j.get('sources') or j.get('src')
            if src: e['source'] = cut(src, 420)
            if j.get('fields'): e['fields'] = cut(j['fields'], 700)
            nt = j.get('note') or j.get('caution') or j.get('how')
            if nt: e['note'] = cut(nt if isinstance(nt, str) else ' · '.join(str(x) for x in nt[:3]) if isinstance(nt, list) else nt, 420)
            e['top'] = {k: shape(v) for k, v in j.items() if shape(v)}
            if not e.get('source'):   # 출처가 갈래마다 따로 적힌 파일(juris.json kinds[…].source 등)
                ns = [v2.get('source') for v in j.values() if isinstance(v, dict) for v2 in v.values() if isinstance(v2, dict) and isinstance(v2.get('source'), str)]
                if ns: e['source'] = cut(' / '.join(ns), 600)
            ab = {k: cut(v, 300) for k, v in j.items() if isinstance(v, str) and k not in ('schema', 'title', 'source', 'fields', 'note', 'made', 'built', 'baked', 'asof') and len(v) > 12}
            if ab: e['about'] = ab   # 그 밖 맨 위의 설명 글(범위·한계·읽는 법 등 — 파일이 적어 둔 그대로)
            sm = {}   # 칸 설명이 없는 파일도 꼴을 알 수 있게 — 큰 묶음 둘의 첫 항목(잘라서)
            for k, v in sorted(((k, v) for k, v in j.items() if isinstance(v, (list, dict)) and v), key=lambda x: -len(x[1]))[:2]:
                if isinstance(v, list): sm[k + '[0]'] = cut(v[0], 240)
                else: k0 = next(iter(v)); sm[k + '.' + str(k0)] = cut(v[k0], 240)
            if sm: e['sample'] = sm
            if not e.get('fields'): e['shape'] = cut(deep({k: v for k, v in j.items() if isinstance(v, (list, dict))}), 900)   # 칸 설명이 없는 파일 — 꼴만(뜻은 source·note·about 와 layers.json 을 같이 본다)
        else: e['top'] = shape(j)
        cat.append(e)
    # ② 권역 저장소의 층(시군구마다 한 파일)
    lay = {}; cnt = collections.Counter()
    for mf in glob.glob(os.path.join(ROOT, 'data', 'r', 'manifest-*.json')):
        m = json.load(open(mf, encoding='utf-8'))
        for k, v in (m.get('layers') or {}).items():
            if k not in lay or (v.get('src') and not lay[k].get('src')): lay[k] = {'d': v.get('d'), 'src': cut(v.get('src'), 300), 'asof': v.get('asof')}
        for g in m.get('gus') or []:
            for k in (g.get('bytes') or {}): cnt[k] += 1
    for k in cnt: lay.setdefault(k, {'d': None, 'src': None, 'asof': None})['gus'] = cnt[k]
    doc = {
        'schema': 'tg-ai-guide/2', 'built': time.strftime('%Y-%m-%d'),
        'what': '데이터 압축지도 — 대한민국 전국 %d개 시군구·%d개 행정동의 공공데이터(인구·머무는 사람·이동·카드 소비·가게·집값·공시가격·세금·교통사고·신호·시설·경찰·소방·세무서·법원·등기소·교육지원청 관할 등)를 한 곳에 묶은 정적 파일 모음. 서버·키 없이 주소만으로 읽는다(JSON · UTF-8).' % (len(gus), sum(g.get('n') or 0 for g in IX['gus'])),
        'start_here': ['1) 이 파일의 gus 에서 시군구 코드(5자리)와 저장소(repo)를 찾는다', '2) ' + SITE + '<repo>/r/<코드>/profile.json = 그 시군구의 행정동마다 한 덩어리(+ gu_summary) — 지역을 처음 파악할 때는 이것 하나면 된다',
                       '3) 더 자세한 층은 region_layers 의 이름으로 ' + SITE + '<repo>/r/<코드>/<층>.json (그 시군구에 있는지는 ' + SITE + '<repo>/manifest.json 의 gus[].bytes)',
                       '4) 전국 한 파일짜리(경찰·기관 관할·세금·공시가격 요약 등)는 catalog 의 url', '5) 무엇을 어떻게 잇는지는 keys 와 recipes · 여기에 없는 자료는 find-it.json(공식 창구)'],
        'keys': {'시군구 5자리': '행정안전부 행정구역 코드 앞 5자리(예 11650 서초구) — r/<코드>/ 폴더 이름 · 2026-07 개편 반영(인천 제물포·영종·서해·검단구 · 전남광주통합특별시 12 · 강원 51 · 전북 52 · 화성시 구 4곳)',
                 '행정동 8자리': '시군구 5자리 + 3자리(예 11650621 방배4동) — profile.json dong 의 열쇠 · police.json dong · juris.json d · ptax-dong.json hjd · agency-pts.json jumin',
                 '법정동 10자리': '예 1165010100 방배동 — ptax-dong.json bjd · hp.json bjd · 필지(PNU 19자리 = 법정동 10 + 대지 1/산 2 + 본번 4 + 부번 4)의 앞 10자리',
                 '경찰서 번호': 'police.json stations[i][0] — police-card.json st 의 열쇠(문자열)', '기관 자리': 'juris.json kinds[종류].o 의 차례(0부터) — agency-card.json kinds[종류].ag 의 열쇠(문자열)',
                 '좌표': 'WGS84 경도·위도(소수) — 파일마다 [lon, lat] 인지 [lat, lon] 인지 fields 를 본다', '250m 칸': '국가표준격자 — r/<구>/grid.json 이 칸 이름·자리'},
        'recipes': [
            {'q': '이 동네(행정동)는 어떤 곳인가', 'do': ['gus 에서 시군구 코드 → <repo>/r/<코드>/profile.json', 'dong[행정동 8자리] 의 주민·가구·사업체·가게·교통사고·집값·시설 · gu_summary 의 외국인·소득', 'how_to_read·caution·sources 를 같이 읽는다']},
            {'q': '좌표(또는 주소)가 어느 행정동인가', 'do': ['<repo>/r/<코드>/dong.json 의 dong[].polys(경계 다각형)에 점이 드는지 본다 → k(8자리)', '주소만 있으면 시군구 이름으로 gus 를 찾고 동 이름으로 profile.json dong 의 이름을 찾는다']},
            {'q': '이 동을 맡는 경찰서·지구대는', 'do': ['police.json dong[8자리] → labels[그 값] = 경찰서 번호(「1,4」 = 둘이 나눠 맡음 · 「21~6」 = 21번 + 일부 번지 6번) → stations', 'police.json pbox 에서 그 경찰서의 지구대·파출소(자리·주소)', 'police-card.json st[번호] = 그 서 관할 한눈에(동·주민·사고 10년·시설·연혁) · 서울 31서는 police-stats.json(112 신고·5대 범죄·교통단속)']},
            {'q': '이 동을 맡는 세무서·법원·등기소·교육지원청은', 'do': ['juris.json kinds[tax|court|reg|edu] 에서 d[8자리] 가 있으면 그 값, 없으면 g5[앞 5자리](-1 이면 동마다 다름) → o[자리] = [이름, …, 관할 원문]', 'agency-card.json kinds[종류].ag[자리] = 그 기관 관할 한눈에(동·주민·사업체·학령인구 등)']},
            {'q': '이 동의 소방서·119안전센터·주민센터는', 'do': ['agency-pts.json fire[] 에서 sgg(맡는 시군구 — 근사)에 그 시군구가 든 소방서 · c[] = 119안전센터(주소·전화·자리)', 'agency-pts.json jumin[8자리] = [주민센터 이름, 우편번호, 주소]']},
            {'q': '이 동의 집값·공시가격·보유세는', 'do': ['profile.json dong[…].「집값(실거래)」 = 실거래 평당·전세가율(추정)', '<repo>/r/<코드>/hp.json = 공동주택 공시가격(법정동 bjd · 필지 pnu)', 'ptax-dong.json hjd[8자리](없으면 gu[5자리]) = 주택 보유세 범위(추정 · 하위10%·가운데·상위10%) + prev(지난해 견줌) — 낸 세금이 아니다', 'gu-proptax.json gu[5자리] = 그 시군구가 실제로 부과·징수한 재산세(주택·토지·건축물 합)']},
            {'q': '이 시군구 주민의 소득·종부세는', 'do': ['gu-tax.json gu[5자리] — 국세청 1인당 총급여·종합소득·종부세(시군구 평균 — 동으로 나누지 않는다)']},
            {'q': '이 교차로의 신호·사고는', 'do': ['sigdir-seoul.json = 서울 일부 교차로의 방향별 신호 길이(받은 시간대의 실제 값 · 추정 포함)', '<repo>/r/<코드>/jct.json = 교차로별 사고 10년 · taas10.json·taas250.json = 사고 100m·250m 칸']},
            {'q': '어떤 층이 있고 어디까지 덮나', 'do': ['layers.json = 지도 층 목록(파일·범위·출처·이용허락·추정 여부)', '이 파일의 region_layers(시군구마다 있는 층과 몇 곳에 있는지) · catalog(전국 한 파일짜리)']},
            {'q': '여기에 없는 자료는 어디서', 'do': ['find-it.json items — 무엇이 없고 왜 없는지, 누가 볼 수 있는지, 공식 창구(sites) 주소']}],
        'paste_to_ai': '아래를 AI 에게 그대로 붙여 준다 → 「%sdatamap/data/ai.json 을 먼저 읽어라. 대한민국 시군구·행정동 공공데이터 묶음의 길잡이다. start_here·keys·recipes 대로 필요한 파일만 골라 읽고, 값을 말할 때는 그 파일의 출처와 기준 시점을 같이 말하고, 추정·근사는 그렇게 밝히고, 없는 값은 지어내지 말고 find-it.json 의 공식 창구를 알려 줘라.」 — 주소를 못 여는 AI(검색 차단 규칙을 따르는 도구)에게는 같은 파일의 원본 주소 https://raw.githubusercontent.com/340patrolman/datamap/main/data/ai.json 을 주거나 파일을 내려받아 올린다(권역 파일은 raw.githubusercontent.com/340patrolman/<repo>/main/r/<코드>/<층>.json)' % SITE,
        'not_searchable': '이 사이트는 검색에 걸리지 않게 해 두었다(noindex · robots.txt) — 주소를 아는 사람·AI 만 읽는다. 자료 자체는 모두 공개 공공데이터를 가공한 것이다.',
        'gus_fields': '[시군구 코드, 이름, 저장소(repo)]', 'gus': gus,
        'profile_sections': {'주민': '주민등록 — 사는 사람(연령 10세·성별)', '머무는 사람(생활인구)': '서울만 — 그 시각 그 동에 있는 사람(통신 추정 · 평일/주말 0~23시)', '카드 매출(추정)': '서울만 — 추정매출(분기 · 시간대·요일·연령·성별 비중 · 업종 상위)',
                             '카드 매출(경기)': '경기만 — 1~6월 월평균 총액(업종 이름 없음)', '유동인구(경기)': '경기만 — 요일별', '가구·주택·사업체(SGIS)': '전국 — 집계구 2023 을 동으로 합', '가게(상가업소)': '전국 — 대분류별 수',
                             '이동(대중교통)': '서울·경기 — 정류장·역 하루 승하차 · 아침 하차÷승차', '교통사고(TAAS 2016~2025)': '전국 — 해마다·사망·중상·보행자·시간대', '집값(실거래)': '전국(지번 좌표 잡힌 만큼) — 평당·전세가율(추정)',
                             '머무는 외국인(서울 생활인구 · 추정)': '서울만 — 장기·단기체류 · 국적', '시설(250m 칸 합 · 근사)': '어린이집·학교·경로당·카메라 등', '치안(경찰 관할)': '별표2 × 행정동 근사 · 대표번호', 'gu_summary': '시군구 — 외국인(체류자격·국적·성별) · 점유형태·학력(2020) · 소득(국세청)'},
        'rules_for_ai': ['값을 말할 때는 그 파일의 source(출처)와 기준 시점(date·asof·year)을 같이 말한다 — 출처 글은 파일의 것을 그대로 인용한다', '「추정」「근사」라고 적힌 값은 그렇게 밝힌다(보유세·전세가율·생활인구·카드 매출·소방서 관할·행정동 단위 관할 등)',
                         '빈 칸·없는 열쇠는 자료가 없는 것이지 0 이 아니다 — 없으면 「이 자료에 없다」고 말하고 find-it.json 의 창구를 안내한다', '주민·생활인구·외국인주민(행안부)·등록외국인(법무부)·체류 외국인(생활인구)은 정의가 달라 더하거나 빼지 않는다',
                         '시군구 값을 동 주민 수로 나누지 않는다(국세청 소득·재산세 총액 등) · 구가 있는 시는 시 단위 값이 구마다 같게 실린 파일이 있다(city 칸)', '서울 추정매출과 경기 카드 금액은 직접 견주지 않는다 · 단위(만 원·백만 원·천 원·명·호)를 fields 에서 확인한다',
                         '교통사고는 TAAS 공개 자료를 칸으로 모은 값이다 — 경찰 내부 통계·한 건 한 건의 기록이 아니다', '세금·법령 값은 확인한 날의 규칙(tax-rules.json 의 checked·versions)이다 — 법률 자문이 아니다',
                         '관할(경찰서·기관)은 법령 별표를 행정동에 붙인 근사다 — 번지로 나뉘는 동은 「경계」로 둘 다 말한다', '이용허락은 layers.json 의 license 를 본다 — 「확인 필요」·ODbL·공공누리 유형마다 다르다(다시 배포하려면 원 출처 조건을 따른다)'],
        'units': {'금액': '파일마다 다르다 — ptax-dong 만 원 · gu-proptax 백만 원 · gu-tax 만 원/년(종부세 백만 원) · hp 만 원 · 실거래 평당 만 원 · KOSIS 원자료 천 원', '넓이': '㎢(동) · ㎡(전용면적)', '사고': '건·명 — 2016~2025 열 해 합(해마다 값은 yr·해마다)'},
        'other_files': {'layers': SITE + 'datamap/data/layers.json (층 목록 — 파일·범위·출처·이용허락·추정 여부)', 'regions': SITE + 'datamap/data/regions.json (시도 → 저장소 · 범위)', 'find_it': SITE + 'datamap/data/find-it.json (없는 자료의 공식 창구)'},
        'privacy': '개인정보 없음 — 사고는 나이·성별·상해·사고번호·날짜의 일을 받는 자리에서 버렸고, 실거래는 매수·매도인·중개사·일자·층을 버렸다. 기관 전화는 대표번호만.',
        'catalog_fields': 'catalog[[파일 이름, 만든 날·기준, 출처 한 줄]] · 주소 = ' + SITE + 'datamap/data/<파일 이름> · 자세한 것(칸 설명 fields · 한계 note · 맨 위 열쇠 top · 표본 sample)은 catalog_full — 전국 한 파일짜리 %d개' % len(cat),
        'catalog': [[e['file'], e.get('date') or '', cut(e.get('source') or e.get('note') or (e.get('about') and ' · '.join(e['about'].values())) or '', 110)] for e in cat],
        'catalog_full': SITE + 'datamap/data/ai-catalog.json (파일마다 칸 설명·한계·표본까지 — 쓸 파일을 고른 뒤 그 파일 항목만 읽는다)',
        'region_layers_fields': 'region_layers{층 이름: {d 뜻, src 출처, asof 기준, gus 이 층이 있는 시군구 수(전체 %d)}} — 주소 = %s<repo>/r/<시군구 5자리>/<층>.json' % (len(gus), SITE),
        'region_layers': dict(sorted(lay.items())),
        }
    json.dump({'schema': 'tg-ai-catalog/1', 'built': doc['built'], 'guide': SITE + 'datamap/data/ai.json', 'fields': 'files[{file, url, bytes, schema, date(만든 날·기준 해), source, fields(칸 설명), note, about{그 밖 설명 글}, top{맨 위 열쇠: {개수} 또는 [개수]}, sample{큰 묶음의 첫 항목 — 꼴 보기}, shape(칸 설명이 없는 파일의 꼴 — 저절로 적은 것: 열쇠·값 종류·보기)}]', 'files': cat},
              open(os.path.join(ROOT, 'data', 'ai-catalog.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, indent=1)
    p = os.path.join(ROOT, 'data', 'ai.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print('시군구', len(gus), '· 전국 파일', len(cat), '· 권역 층', len(lay), '· 바이트', os.path.getsize(p))
    print('출처 없는 파일:', [e['file'] for e in cat if not e.get('source')])
    print('칸 설명 없는 파일:', [e['file'] for e in cat if not e.get('fields')])

if __name__ == '__main__': main()
