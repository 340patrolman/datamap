# -*- coding: utf-8 -*-
# 데이터 압축지도 — 👥 넷째 겹(사회·세대)의 시계열: 음주·음주운전·음주사고·단속·주점 사업자·주류 출고의 해마다 흐름(소유자 마스터 문서 7.8 「세대는 느린 변수」 · 2026-10-11) → data/gen-trend.json
#   재료 = ../07_API키/세대별행태_20261011/*.csv(코워크가 2026-10-11 각 기관 **조회 화면의 표를 옮긴 것** — 원본 파일 내려받기가 아니다 · 출처는 줄마다 · 00_찾은것.md)
#     1 국민건강영양조사(질병관리청) 고위험음주율·월간음주율·월간폭음률 · 2 연간 음주운전 경험률 · 3 지역사회건강조사 서울 25구 · 4 TAAS 음주운전 교통사고(나이대·시간대·요일·서울 구) + 경찰접수 음주정도별
#     5 경찰청 연령별 음주운전 적발 · 6 국세청 100대 생활업종 신규·폐업 사업자 · 7 주류 출고량
#   이 도구는 숫자를 고치지 않고 꼴만 바꾼다(긴 표 → 줄마다 [해, 값]) · 「-」(비제시)는 null · 다시 검산한다(음주사고: 나이대 합 = 합계 · 서울 구 합 = 서울)
#   **정의가 바뀐 해**(breaks)는 그대로 실어 둔다 — 그 앞뒤를 한 줄로 이으면 안 된다
#   py -3.12 -X utf8 tools/region/gentrend-bake.py
import json, os, csv, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', '세대별행태_20261011')
def num(v):
    v = (v or '').strip().replace(',', '')
    try: return int(v) if v.lstrip('-').isdigit() else float(v)
    except Exception: return None
def main():
    files = {}; st = collections.Counter()
    for f in sorted(glob.glob(os.path.join(SRC, '*.csv'))):
        name = os.path.splitext(os.path.basename(f))[0]; S = collections.defaultdict(list); src = None; star = 0
        for r in csv.DictReader(open(f, encoding='utf-8-sig')):
            src = src or [r['조사 이름'], r['표 이름'], r['받은 주소']]
            v = num(r['값']); row = [int(r['해']), v]; memo = r.get('비고') or ''; head = memo.split(';')[0].strip()
            if '변동계수 표시 **' in memo: row.append(2); star += 1
            elif '변동계수 표시 *' in memo: row.append(1); star += 1
            sub = head if head.startswith(('시간대 ', '요일 ', '1당 ')) else r['나이대']   # 시간대·요일·음주정도/주야 구분은 원표에서 비고 칸에 옮겨져 있다 — 줄 이름으로 올린다
            S['|'.join([r['지표'], r['성별'], sub, r['지역'], r['단위']])].append(row)
        for k in S: S[k].sort()
        files[name] = {'source': src, 'series': dict(S)}; st[name] = sum(len(v) for v in S.values()); st[name + ' 줄'] = len(S)
    chk = []
    A = files.get('4_음주사고_나이대별', {}).get('series', {}); tot = next((v for k, v in A.items() if k.startswith('음주운전 교통사고 건수|') and '합계' in k), None)
    if tot:
        parts = [v for k, v in A.items() if k.startswith('음주운전 교통사고 건수|') and '합계' not in k]; bad = [y for y, t in tot if sum(dict(p).get(y) or 0 for p in parts) != t]
        chk.append('음주사고 나이대 합 = 합계: ' + ('모든 해 맞음(%d해)' % len(tot) if not bad else '안 맞는 해 %s' % bad))
    G = files.get('4_음주사고_서울구별', {}).get('series', {}); seo = next((v for k, v in G.items() if k.startswith('음주운전 교통사고 건수|') and '|서울특별시|' in k), None)
    if seo:
        parts = [v for k, v in G.items() if k.startswith('음주운전 교통사고 건수|') and '|서울특별시|' not in k]; bad = [y for y, t in seo if sum(dict(p).get(y) or 0 for p in parts) != t]
        chk.append('음주사고 서울 구 합 = 서울: ' + ('모든 해 맞음(%d해 · 구 %d)' % (len(seo), len(parts)) if not bad else '안 맞는 해 %s' % bad))
    doc = {'schema': 'tg-gen-trend/1', 'made': datetime.date.today().isoformat(), 'got': '2026-10-11',
           'source': '질병관리청 국민건강영양조사·지역사회건강조사(KOSIS 177) · 도로교통공단 교통사고분석시스템 TAAS(경찰DB) · 경찰청 경찰접수교통사고현황(KOSIS 132)·연령별 음주운전 적발기록(공공데이터포털 15078190) · 국세청 국세통계(KOSIS 133) — 파일마다 source[조사 이름, 표 이름, 받은 주소]',
           'chain': '세대 교체(느린 변수) · 제도 변화 → 구성원의 행태(음주·음주운전) → 사고·단속 · 주점 상권 — ONTOLOGY.md §0 「느린 변수와 빠른 변수」 · 상권 쪽 흐름은 data/night-trend-seoul.json',
           'note': ['**숫자는 각 기관 조회 화면의 표를 옮긴 것이다**(2026-10-11 · 원본 파일을 내려받은 것이 아니다) — 옮긴 뒤 합계를 다시 맞춰 봤다(check). 쓰기 전에 받은 주소의 원표로 한 번 더 확인하면 좋다',
                    '해석을 붙이지 않았다 — 「왜 줄었나」는 이 자료에 없다(세대 · 단속 기준 · 대리운전 · 회식 문화가 같이 움직였다)',
                    '조사 값(%)은 표본 조사다 — 구 단위·나이대 단위는 해마다 흔들린다(셋째 칸 1·2 = 원표의 변동계수 표시) · 여러 해의 흐름으로 본다',
                    '음주운전 경험률은 「지난 한 해 운전한 사람 가운데 조금이라도 술을 마시고 운전한 적이 있다」고 답한 비율(스스로 답한 값)이다 — 적발·사고와 다른 것',
                    '음주사고·단속 건수는 단속 기준·단속 방식이 바뀌면 같이 바뀐다(breaks) · 사고의 나이대는 가해 운전자(1당)의 것',
                    '없는 것: 음주사고의 시군구 × 나이대 · 단속의 농도 구간·경찰서별 집계 · 주점 사업자의 시군구·달 값 · 가구 지출 · 회식 인식(공식 통계를 찾지 못함)'],
           'breaks': ['음주운전 경험률 1998년은 20세 이상 기준 · 1998·2001년과 여자 일부 해는 연령표준화율 비제시', '서울 구별 음주운전 경험률은 2009년 문항이 바뀌어 2009년부터만 실었다(2008년과 이어지지 않는다)',
                      '2019-06-25 단속 기준 혈중알코올농도 0.05% → 0.03% — 음주정도별 사고는 2019년부터 구간 이름이 다르다', '국민건강영양조사 2006년 값은 KOSIS 에 없다 · 2007년은 응답자가 다른 해의 절반 아래',
                      '주류 출고량의 수입분은 2006년부터 합계에 들어간다'],
           'fields': 'files{파일 이름: {source[조사 이름, 표 이름, 받은 주소], series{「지표|성별|나이대|지역|단위」: [[해, 값(null = 비제시)(, 1 = 변동계수 25~50% · 2 = 50% 이상 — 원표의 표본 주의 표시)]…] · 셋째 자리(나이대)에는 시간대·요일·음주정도/주야 구분이 들어가기도 한다}}}',
           'check': chk, 'files': files}
    p = os.path.join(ROOT, 'data', 'gen-trend.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '·', chk); print({k: v for k, v in st.items()})
    def s(fn, key):
        m = [v for k, v in files[fn]['series'].items() if all(x in k for x in key)]; return m[0] if m else None
    for fn, key in (('1_고위험음주율', ['|남자|', '19-29']), ('1_고위험음주율', ['|남자|', '50대']), ('1_고위험음주율', ['|여자|', '30대']), ('2_음주운전경험률', ['|전체|', '19-29']), ('2_음주운전경험률', ['|전체|', '70']),
                    ('4_음주사고_나이대별', ['건수', '20-29']), ('4_음주사고_나이대별', ['건수', '65']), ('4_음주사고_서울구별', ['건수', '서초']), ('3_지역사회건강조사_서울25구', ['음주운전', '서초'])):
        v = s(fn, key); print(' ', fn, key, (v[0], v[len(v) // 2], v[-1]) if v else '없음')
    print('  나이대 이름', sorted(set(k.split('|')[2] for k in files['4_음주사고_나이대별']['series'])))
if __name__ == '__main__': main()
