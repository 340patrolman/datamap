# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.69.0 — 🏘 집값·거래 흐름(한국부동산원 R-ONE 부동산통계 OpenAPI · 시군구 월간)
#   소유자 2026-10-07 「R-ONE 시군구 월간 매매·전세 변동률 + 아파트·토지 거래량 층 · 배치로 받아 정적 JSON」(코워크 전달서 F절 — 표 ID·호출 형식 실측)
#   키 = ../07_API키/keys.json 의 "rone" — 이 도구 안에서만 쓴다(결과 JSON·저장소·브라우저에 키 없음)
#   검증값: 아파트 매매지수 2026-08 전월 대비 전국 +0.39% · 서울 +1.05% · 서초구 -0.35%(R-ONE 첫 화면 공표값과 같음 — 코워크 확인)
#   py -3.12 -X utf8 tools/region/rone-bake.py → data/rone.json
import json, os, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['rone']
KEY = K if isinstance(K, str) else (K.get('key') or K.get('value'))
URL = 'https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do?'
TBL = [   # [열쇠, STATBL_ID, 이름, 단위, 쓰는 항목 이름(None = 하나뿐)]
    ['apt', 'A_2024_00045', '아파트 매매가격지수', '지수', None],
    ['jeon', 'A_2024_00050', '아파트 전세가격지수', '지수', None],
    ['house', 'A_2024_00016', '주택종합 매매가격지수', '지수', None],
    ['rh', 'A_2024_00080', '연립·다세대 매매가격지수', '지수', None],
    ['wol', 'A_2024_00054', '아파트 월세통합지수', '지수', None],
    ['aptN', 'A_2024_00554', '아파트 매매거래', '호', '동(호)수'],
    ['landN', 'A_2024_00536', '토지 매매거래', '필지', '필지수'],
    ['jiga', 'A_2024_00903', '지가변동률(전월 대비)', '%', '변동률'],
]
def get(sid, t):
    rows, pi = [], 1
    while True:
        q = urllib.parse.urlencode({'KEY': KEY, 'Type': 'json', 'pIndex': pi, 'pSize': 1000, 'STATBL_ID': sid, 'DTACYCLE_CD': 'MM', 'WRTTIME_IDTFR_ID': t})
        for k in range(4):
            try: j = json.loads(urllib.request.urlopen(URL + q, timeout=60).read().decode('utf-8')); break
            except Exception as e:
                if k == 3: raise
                time.sleep(2 + k * 3)
        b = j.get('SttsApiTblData')
        if not b or len(b) < 2: return rows
        rr = b[1].get('row') or []; rows += rr; tot = b[0]['head'][0]['list_total_count']
        if len(rows) >= tot or not rr: return rows
        pi += 1

def ym_back(ym, n):
    y, m = int(ym[:4]), int(ym[4:]); m -= n
    while m <= 0: m += 12; y -= 1
    return '%d%02d' % (y, m)
now = time.localtime(); last = '%d%02d' % (now.tm_year, now.tm_mon)
while not get('A_2024_00045', last): last = ym_back(last, 1)
MONTHS = [ym_back(last, 12 - i) for i in range(13)]
print('마지막 달', last)

def key_of(path):   # 「경기>경부2권>용인시>기흥구」 → ('경기', ['용인시', '기흥구']) — 권역 칸(…권 · …지역)은 뺀다
    s = path.split('>'); sd = s[0]; adm = [x for x in s[1:] if x[-1] in '시군구' and not x.endswith('권')]
    return sd, adm
SGG, GU, AGG, ITEMS = {}, {}, {}, {}
ix = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
SD2 = {'서울': '11', '부산': '26', '대구': '27', '인천': '28', '대전': '30', '울산': '31', '세종': '36', '경기': '41', '강원': '51', '충북': '43', '충남': '44', '전북': '52', '경북': '47', '경남': '48', '제주': '50', '전남광주': '12'}
OURS = {}
for g in ix['gus']: OURS.setdefault(g['gu'][:2], {})[g['name'].replace(' ', '')] = g['gu']
for key, sid, nm, unit, itm in TBL:
    ITEMS[key] = [nm, unit, sid]
    for mi, ym in enumerate(MONTHS):
        rows = get(sid, ym)
        if mi == len(MONTHS) - 1: print(key, ym, len(rows), sorted(set(r['ITM_NM'] for r in rows)))
        for r in rows:
            if itm and r['ITM_NM'] != itm: continue
            if not itm and len(set(x['ITM_NM'] for x in rows[:50])) > 1 and r['ITM_NM'] not in ('지수', '변동률', '필지수', '동(호)수', '건수'): continue
            v = r['DTA_VAL']; v = None if v is None else round(float(v), 3)
            fp = r.get('CLS_FULLNM') or r.get('CLS_NM') or ''
            if not fp: continue
            sd, adm = key_of(fp); seg = fp.split('>')
            if len(seg) > 1 and not (sd == '전남광주' and len(seg) == 2) and (seg[-1][-1] not in '시군구' or seg[-1].endswith('권')): continue   # 권역·읍면동 줄은 뺀다(지가변동률은 읍면동까지 온다)
            if len(seg) == 1 or (sd == '전남광주' and not adm):
                tgt = AGG.setdefault(fp.split('>')[-1], {})
            elif not adm: continue
            else:
                if len(adm) == 1: SGG.setdefault(sd + '|' + adm[0], {}).setdefault(key, [None] * 13)[mi] = v
                code = OURS.get(SD2.get(sd, ''), {}).get(''.join(adm))
                if code: GU.setdefault(code, {}).setdefault(key, [None] * 13)[mi] = v
                continue
            tgt.setdefault(key, [None] * 13)[mi] = v
def chg(a, i, j): return round((a[i] / a[j] - 1) * 100, 2) if a and a[i] and a[j] else None
A = AGG.get('전국', {}).get('apt'); S = AGG.get('서울', {}).get('apt'); C = SGG.get('서울|서초구', {}).get('apt')
print('검증 2026-08 전월 대비 — 전국', chg(A, MONTHS.index('202608'), MONTHS.index('202607')) if '202608' in MONTHS else '-', '서울', chg(S, MONTHS.index('202608'), MONTHS.index('202607')) if '202608' in MONTHS else '-', '서초', chg(C, MONTHS.index('202608'), MONTHS.index('202607')) if '202608' in MONTHS else '-')
print('시군구', len(SGG), '구(지도 코드)', len(GU), '/', len(ix['gus']), '묶음', len(AGG))
doc = {'schema': 'tg-rone/1', 'baked': time.strftime('%Y-%m-%d'), 'months': MONTHS, 'items': ITEMS,
       'source': '한국부동산원 R-ONE 부동산통계정보 OpenAPI(SttsApiTblData · 월간) — 전국주택가격동향조사(매매·전세·월세 지수) · 부동산거래현황(아파트·토지 매매거래) · 지가변동률(국토교통부·부동산원) · 받은 날 ' + time.strftime('%Y-%m-%d'),
       'note': '지수 = 기준 시점 100 · 변동률은 이 지도가 지수의 비로 계산(공표값과 소수 둘째 자리까지 같음 — 2026-08 전국 0.39 · 서울 1.05 확인) · 거래량은 신고 기준(동·호수 · 필지) · 조사 표본이 없는 군은 값이 없다',
       'sgg': SGG, 'gu': GU, 'agg': AGG}
json.dump(doc, open(os.path.join(ROOT, 'data', 'rone.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('바이트', os.path.getsize(os.path.join(ROOT, 'data', 'rone.json')))
