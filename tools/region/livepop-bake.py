# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.15.0 — 👥 인구감소지역 생활인구(통계청·행정안전부 · KOSIS e-지방지표 DT_1YL12001E 성별 · DT_1YL12002E 연령별 · 시/군/구 · 월별)
#   생활인구 = 주민등록 인구 + 체류인구(그 달 하루 3시간 넘게 머문 횟수가 1번 이상인 사람 — 통신 자료 · 통계청 정의) · 인구감소지역 89 + 관심지역 18 = 107곳만 공표된다
#   KOSIS 행정구역 코드(21010 등)는 이 지도 코드와 달라 「시도 + 이름」으로 맞춘다 · py -3.12 -X utf8 tools/region/livepop-bake.py → data/livepop.json
import json, os, collections, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KO = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'kosis')
sp = importlib.util.spec_from_file_location('rc', os.path.join(ROOT, 'tools', 'region', 'regcfg.py')); RC = importlib.util.module_from_spec(sp); sp.loader.exec_module(RC)
def num(x):
    try: return int(float(x))
    except (TypeError, ValueError): return None   # 「X」 = 비공개 · 「-」 = 없음
ALIAS = {'전라남도': '12', '광주광역시': '12', '전남광주통합특별시': '12', '강원도': '51', '강원특별자치도': '51', '전라북도': '52', '전북특별자치도': '52'}

def main():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    full = {}
    for g in IX['gus']:
        sd = g['gu'][:2]; full[(sd, g['name'])] = g['gu']
    sdn = {v: k for k, v in RC.NAME.items()}; sdn.update(ALIAS)
    def code(nm):
        a = nm.split(' ', 1)
        if len(a) < 2: return None
        sd = sdn.get(a[0]); n = a[1].replace(' ', '')
        if not sd: return None
        if (sd, n) in full: return full[(sd, n)]
        if a[0] == '대구광역시' and n == '군위군': return full.get(('27', '군위군'))
        return None
    S = json.load(open(os.path.join(KO, 'DT_1YL12001E.json'), encoding='utf-8')); A = json.load(open(os.path.join(KO, 'DT_1YL12002E.json'), encoding='utf-8'))
    out = collections.defaultdict(lambda: {'m': {}}); miss = set()
    for r in S:
        c = code(r['C1_NM'])
        if not c: miss.add(r['C1_NM']); continue
        o = out[c]; o['name'] = r['C1_NM']; o['kind'] = r['C2_NM']; mo = o['m'].setdefault(r['PRD_DE'], {})
        v = num(r['DT'])
        mo[{'T001': 'tot', 'T002': 'm', 'T003': 'f'}[r['ITM_ID']]] = v
    AK = ['T002', 'T003', 'T004', 'T005', 'T006', 'T007', 'T008']
    for r in A:
        c = code(r['C1_NM'])
        if not c or r['ITM_ID'] not in AK: continue
        mo = out[c]['m'].setdefault(r['PRD_DE'], {}); ag = mo.setdefault('age', [None] * 7)
        ag[AK.index(r['ITM_ID'])] = num(r['DT'])
    for c, o in out.items():   # 주민등록 합(이 지도 dong.json · 2026년 9월) — 「주민 대비 몇 배」
        try: o['reg'] = sum((d.get('pop') or {}).get('tot', 0) for d in json.load(open(os.path.join(ROOT, 'data', 'r', c, 'dong.json'), encoding='utf-8'))['dong'])
        except Exception: o['reg'] = None
        o['sgname'] = next((x['name'] for x in IX['gus'] if x['gu'] == c), '')
    doc = {'schema': 'tg-livepop/1', 'source': '통계청·행정안전부 인구감소지역 생활인구(KOSIS e-지방지표 DT_1YL12001E 성별 · DT_1YL12002E 연령별) · 시/군/구 · 월별 · ' + min(r['PRD_DE'] for r in S) + '~' + max(r['PRD_DE'] for r in S),
           'note': '생활인구 = 주민등록 인구 + 체류인구(그 달 하루 3시간 넘게 머문 사람 · 통신 자료 추정) · 인구감소지역 89곳과 관심지역 18곳만 공표 — 그 밖 시군구는 공표하지 않는다 · 한 사람이 여러 지역에서 셀 수 있다',
           'fields': 'gu = {이 지도 시군구 코드: {name(KOSIS 이름), sgname(이 지도 이름), reg(주민등록 합 · 2026년 9월), kind(감소·관심), m: {YYYYMM: {tot, m, f, age = [20세 미만, 20대, 30대, 40대, 50대, 60대, 70세 이상]}}}}', 'ages': ['20세 미만', '20대', '30대', '40대', '50대', '60대', '70세 이상'], 'gu': out}
    p = os.path.join(ROOT, 'data', 'livepop.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(out), '못 맞춘 이름', sorted(miss), '바이트', os.path.getsize(p))

if __name__ == '__main__': main()
