# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.8.0 — 🌏 외국인주민(행정안전부 「지방자치단체 외국인주민 현황」 · KOSIS 110 TX_11025_A001_A · 시군구 · 해마다 11월 1일 기준)
#   설계서 4장 「외국인 구성」의 거주 쪽(3개월 넘게 사는 사람) — 서울 생활인구의 체류 외국인(그 시각 그 자리)과 합치지 않는다
#   항목: 총인구 · 외국인주민 합계 · 한국국적 없음(외국인근로자·결혼이민자·유학생·외국국적동포·기타) · 한국국적 취득(혼인귀화·기타) · 외국인주민 자녀 · 세대수
#   지역 맞추기: KOSIS 지역 이름(옛 시도·시군구) → 지도 시군구(이름) — 2024 뒤에 생긴 구(인천 제물포·영종·서해·검단 · 화성 4구)는 맞출 수 없어 비운다(지어내지 않음) ·
#                광주·전남은 2026-07 「전남광주통합특별시」(코드 12)로 이름을 맞춘다 · 경기 일반구가 없는 시는 「시 전체」로 표시
#   py -3.12 -X utf8 tools/region/foreign-bake.py → data/foreign.json
import json, os, re, urllib.request, urllib.parse, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
K = urllib.parse.quote(json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['kosis'], safe='')
IT = {'15110AA0AA': 'pop', '15110AA000': 'tot', '15110AA0AD': 'nf', '15110AA0ADAA': 'work', '15110AA0ADAK': 'marr', '15110AA0ADAC': 'stud', '15110AA0ADAL': 'kor', '15110AA0ADAD': 'etc',
      '15110AA0AF': 'nat', '15110AA0AFAA': 'natm', '15110AA0AFAB': 'nato', '15110AA0AM': 'kid', '15110AA0AN': 'hh'}
SIDO = {'서울특별시': '11', '부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '광주광역시': '12', '대전광역시': '30', '울산광역시': '31', '세종특별자치시': '36', '경기도': '41',
        '강원도': '51', '강원특별자치도': '51', '충청북도': '43', '충청남도': '44', '전라북도': '52', '전북특별자치도': '52', '전라남도': '12', '경상북도': '47', '경상남도': '48', '제주특별자치도': '50'}

def data(year):
    u = ('https://kosis.kr/openapi/Param/statisticsParameterData.do?method=getList&apiKey=%s&itmId=ALL&objL1=ALL&objL2=ALL&objL3=C001&format=json&jsonVD=Y&prdSe=Y&startPrdDe=%s&endPrdDe=%s&orgId=110&tblId=TX_11025_A001_A' % (K, year, year))
    j = json.loads(urllib.request.urlopen(u, timeout=180).read().decode('utf-8', 'replace'))
    if isinstance(j, dict): raise RuntimeError(j)
    return j

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    nz = lambda s: re.sub(r'\s', '', s or '')
    by = collections.defaultdict(list)
    for g in IX['gus']: by[(g['gu'][:2], nz(g['name']))].append(g['gu'])
    out = {}; years = {}; miss = set()
    for yr in ('2024', '2019'):
        rows = data(yr); years[yr] = yr; par = {}
        V = collections.defaultdict(dict)
        for r in rows:
            reg = r['C1']; nm = r['C1_NM']; it = IT.get(r['C2'])
            if not it: continue
            V[(reg, nm)][it] = int(float(r['DT'])) if re.match(r'^-?[0-9.]+$', str(r['DT'] or '')) else None   # '*'·'-' = 비밀보호·없음
        names = {}
        for r in rows: names[r['C1']] = r['C1_NM']
        kc = lambda reg: re.sub(r'A$', '', re.sub(r'^\d+HJG', '', reg))   # KOSIS 자체 지역 코드(옛 시도 2자리 + 시군구 3자리 + 일반구 2자리)
        nmc = {kc(c): n for c, n in names.items()}
        for (reg, nm), v in V.items():
            code = kc(reg)
            if nm == '세종특별자치시': cand = by.get(('36', '세종시'))   # 세종은 시도 단계에만 있다
            elif len(code) < 5: continue
            else:
                sd = SIDO.get(nmc.get(code[:2], ''))
                if not sd: continue
                full = nmc.get(code[:5], '') + nm if len(code) == 7 else nm   # 일반구 = 시 이름 + 구 이름(수원시장안구)
                cand = by.get((sd, nz(full))) or ([x for (s2, n2), xs in by.items() if s2 == sd and n2.startswith(nz(nm)) and nz(nm).endswith('시') for x in xs] if len(code) == 5 else [])
            if not cand: miss.add(nm); continue
            direct = len(cand) == 1
            for gc in cand:
                o = out.setdefault(gc, {})
                if direct: o[yr] = v; o['src'] = nm; o['_d'] = 1   # 그 구 자체 값이 이긴다
                elif not o.get('_d'): o[yr] = v; o['src'] = nm + '(시 전체)'
    for o in out.values(): o.pop('_d', None)
    doc = {'schema': 'tg-foreign/1', 'source': '행정안전부 「지방자치단체 외국인주민 현황」(KOSIS 110 TX_11025_A001_A) · 해마다 11월 1일 기준 · 2024·2019',
           'fields': 'pop 총인구 · tot 외국인주민 합계 · nf 한국국적 없음(work 외국인근로자 · marr 결혼이민자 · stud 유학생 · kor 외국국적동포 · etc 기타) · nat 한국국적 취득(natm 혼인귀화 · nato 기타) · kid 외국인주민 자녀 · hh 외국인주민 세대',
           'note': '3개월 넘게 사는 사람(거주) — 서울 생활인구의 체류 외국인(그 시각 그 자리)과 정의가 달라 합치지 않는다 · 2024 뒤에 생긴 구(인천 새 4구·화성 4구)는 비움 · 경기 일반구 없는 값은 시 전체',
           'gu': out}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'foreign.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(out), '/', len(IX['gus']), '못 맞춤(지역 이름)', sorted(miss)[:40], '서초', out.get('11650'))

if __name__ == '__main__': main()
