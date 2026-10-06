# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.16.0 — 🌏 읍면동 외국인주민(행정안전부 「2024 지방자치단체 외국인주민 현황」 2024.11.1 기준 · 통계표 xlsx 시트 1-3 · 11)
#   시트 1-3 「유형 및 지역별(읍면동)」 = 합계 · 한국국적 없음(소계·근로자·결혼이민·유학생·외국국적동포·기타) · 한국국적 취득 · 외국인주민 자녀
#   시트 11 「다문화가구원 현황(읍면동)」 = 합계 · 한국인 배우자 · 결혼이민자·귀화자 · 자녀 · 기타동거인
#   「*」 = 작아서 가린 값(빈칸) · 2024 이름을 이 지도 행정동(2026-07)에 이름으로 맞춘다(시도 안에 같은 이름이 여럿이면 바로 위 시군구 이름으로 가림)
#   원자료 07_API키/out/foreign/mois2024.xlsx(행안부 누리집 nttId=121226 첨부) · py -3.12 -X utf8 tools/region/foreign-dong-bake.py → data/foreign-dong.json
import json, os, re, collections, openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'foreign', 'mois2024.xlsx'); R = os.path.join(ROOT, 'data', 'r')
SIDO = {'서울특별시': ['11'], '부산광역시': ['26'], '대구광역시': ['27'], '인천광역시': ['28'], '광주광역시': ['12'], '대전광역시': ['30'], '울산광역시': ['31'], '세종특별자치시': ['36'], '경기도': ['41'],
        '강원특별자치도': ['51'], '강원도': ['51'], '충청북도': ['43'], '충청남도': ['44'], '전북특별자치도': ['52'], '전라북도': ['52'], '전라남도': ['12'], '경상북도': ['47'], '경상남도': ['48'], '제주특별자치도': ['50']}
def v(x):
    if x in (None, '', '*', '-'): return None
    try: return int(float(x))
    except (TypeError, ValueError): return None
def nn(s): return re.sub(r'[\s.·ㆍ,]', '', str(s or ''))

def main():
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); D = collections.defaultdict(list)   # (시도코드, 동이름) → [(구코드, 구이름, 동코드)]
    for g in IX['gus']:
        try:
            for d in json.load(open(os.path.join(R, g['gu'], 'dong.json'), encoding='utf-8'))['dong']: D[(g['gu'][:2], nn(d['name']))].append((g['gu'], g['name'], d['k']))
        except Exception: pass
    wb = openpyxl.load_workbook(SRC, read_only=True)
    def walk(sheet, start):
        sd = None; sgg = ''; out = []
        for i, row in enumerate(wb[sheet].iter_rows(values_only=True)):
            if i < start or not row or not row[0]: continue
            nm = nn(row[0])
            if nm == '전국': continue
            if nm in SIDO: sd = SIDO[nm]; sgg = ''; continue
            if sd is None: continue
            if re.search(r'(시|군|구)$', nm): sgg = nm; continue
            out.append((sd, sgg, nm, row))
        return out
    res = {}; miss = []; amb = 0
    def find(sd, sgg, nm):
        c = [x for s in sd for x in D.get((s, nm), [])]
        if len(c) == 1: return c[0][2]
        if len(c) > 1:
            k = [x for x in c if sgg and (sgg in x[1] or x[1].endswith(sgg))]
            if len(k) == 1: return k[0][2]
        return None
    for sd, sgg, nm, r in walk('1-3. 유형 및 지역별(읍면동)', 6):
        k = find(sd, sgg, nm)
        if not k: miss.append(sgg + ' ' + nm); continue
        res[k] = {'t': v(r[1]), 'nf': v(r[2]), 'w': v(r[3]), 'm': v(r[4]), 's': v(r[5]), 'k': v(r[6]), 'e': v(r[7]), 'n': v(r[8]), 'c': v(r[9])}
    mc = 0
    for sd, sgg, nm, r in walk('11. 다문화가구 현황(읍⋅면⋅동)', 6):
        k = find(sd, sgg, nm)
        if not k: continue
        res.setdefault(k, {})['mc'] = [v(r[1]), v(r[2]), v(r[3]), v(r[6]), v(r[9])]; mc += 1
    doc = {'schema': 'tg-foreign-dong/1', 'source': '행정안전부 「2024 지방자치단체 외국인주민 현황」(2024.11.1 기준 · 통계표 시트 1-3 유형 및 지역별(읍면동) · 11 다문화가구원(읍면동)) — KOSIS DT_110025_A033_A · A045_A 와 같은 자료',
           'fields': '{행정동 8자리: {t 외국인주민 합계, nf 한국국적 없음, w 외국인근로자, m 결혼이민자, s 유학생, k 외국국적동포, e 기타외국인, n 한국국적 취득, c 외국인주민 자녀, mc = [다문화가구원 합계, 한국인 배우자, 결혼이민자·귀화자 등, 자녀, 기타동거인]}}',
           'note': '3개월 넘게 사는 외국인주민(주민등록·외국인등록·거소신고 기준) — 그 시각 머무는 사람(생활인구)과 다르다 · 「*」 로 가린 작은 값은 빈칸(0 이 아님) · 2024 이름을 2026 행정동에 이름으로 맞춰 나뉘거나 바뀐 동은 빠질 수 있다', 'dong': res}
    p = os.path.join(ROOT, 'data', 'foreign-dong.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('동', len(res), '다문화', mc, '못 맞춤', len(miss), miss[:25], '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
