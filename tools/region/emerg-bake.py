# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚨 112·119 출동의 공개분 → data/call112.json · data/rescue119.json
#   소유자 2026-10-12 「119 출동 112 출동도 들어가면 좋은데 어느 정도까지 공개를 하는지?」 → 공공데이터포털에 올라 있는 것을 실제로 받아 보고, 공개된 단위 그대로 굽는다
#   112(경찰): 공개는 **경찰서 × 해** 까지다 — 시간대·자리·사건 종별(서울)은 없다. 경기남부는 코드 0~4 × 해(청 전체), 경기북부는 경찰서 × 해 × 긴급/비긴급/비출동
#     15114082 서울경찰청 경찰서별 112신고출동 현황(2011~2025) · 15100217 경기남부경찰청 112신고 현황(2020~2025) · 15036132 경기북부경찰청 경찰서별 112신고접수 현황 · 15048902 경찰청 주요 112 신고 건수(시도청 · 2020)
#   119(소방): **구조** 출동은 소방청이 1건 단위로 올린다(15062386 「소방청_구조활동현황」 2025 — 신고·출동 시각 · 시·구·동(법정동) · 사고 원인). 구급은 서울 2019년 동 × 해(15073858)뿐이고 시간대가 없다
#   ⚠ 1건 단위 원자료(접수번호·분 단위 시각)는 저장소에 올리지 않는다 — 동 × 시 × 갈래로 묶은 수만. 「자살추정」은 「위치확인」과 한 갈래(신변·위치 확인)로 묶어 싣는다(동 단위로 따로 드러내지 않는다)
#   받기: py -3.12 -X utf8 tools/region/dgfile.py <번호> → 07_API키/out/dg/<번호>/x.csv   ·   굽기: py -3.12 -X utf8 tools/region/emerg-bake.py
import json, os, csv, io, datetime, collections, statistics
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); DG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg')
def rd(pk):
    b = open(os.path.join(DG, pk, 'x.csv'), 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return list(csv.reader(io.StringIO(b.decode(e))))
        except Exception: pass
def num(s):
    try: return int(str(s).replace(',', '').strip())
    except Exception: return None
GRP = ['화재', '교통', '승강기·갇힘·끼임', '수난·산악', '신변·위치 확인', '그 밖']
def grp(c):
    if c == '화재': return 0
    if c == '교통': return 1
    if c in ('승강기', '인명 갇힘', '끼임'): return 2
    if c in ('수난', '산악'): return 3
    if c in ('위치확인', '자살추정'): return 4
    return 5
def main():
    td = datetime.date.today().isoformat()
    # ── 112
    r = rd('15114082'); yrs = [int(x) for x in r[0][1:]]; seoul = {x[0].strip(): [num(v) for v in x[1:]] for x in r[1:] if x and x[0].strip()}
    r = rd('15100217'); H = [h.strip() for h in r[0]]; ggs = [[num(x[0])] + [num(v) for v in x[1:]] for x in r[1:] if x and num(x[0])]
    r = rd('15036132'); st = [h.strip() for h in r[0][2:]]; ggn = [[num(x[0]), x[1].strip()] + [num(v) for v in x[2:]] for x in r[1:] if x and num(x[0])]
    r = rd('15048902'); sido = [[x[1].strip(), num(x[2])] for x in r[1:] if len(x) > 2 and num(x[2])]
    doc = {'schema': 'tg-call112/1', 'made': td,
           'source': '공공데이터포털 — 경찰청 서울특별시경찰청_경찰서별 112신고출동 현황(15114082) · 경기도남부경찰청_112신고 현황(15100217) · 경기도북부경찰청_경찰서별 112신고접수 현황(15036132) · 경찰청_주요 112 신고 건수 현황(15048902)',
           'note': ['**112 의 공개 범위는 경찰서 × 해 까지다** — 시간대·요일·자리(동·지구대)·도착 시간은 공개 자료에 없다(2026-10-12 공공데이터포털에서 「112신고」로 찾은 20건을 훑어봄 · 지구대 단위는 충북청뿐)',
                    '서울 = 접수 뒤 **출동한** 사건 수(비출동 신고는 빠져 있다) · 경기북부 = 접수(긴급 출동·비긴급 출동·비출동) · 경기남부 = 청 전체의 코드 0~4 — 세 표의 뜻이 달라 서로 더하거나 견주지 않는다',
                    '경기북부의 「경찰서미지정(관할외)」은 서를 정하지 않고 끝난 신고다(대부분 비출동)',
                    '사건 1건 단위·자리 단위 112 기록은 공개 대상이 아니다 — 소유자가 업무로 가진 자료는 공개 지도에 싣지 않는다(집회 신고와 같은 원칙)'],
           'fields': {'seoul': '{years [해…], st {경찰서: [해마다 출동 건수]}}', 'gg_south': '{cols [칸 이름], rows [[해, 계, 코드0, 코드1, 코드2, 코드3, 코드4]]}', 'gg_north': '{st [경찰서…], rows [[해, 갈래, 경찰서 차례대로 건수…]]}', 'sido2020': '[[시도청, 2020년 신고 건수]]'},
           'seoul': {'years': yrs, 'st': seoul}, 'gg_south': {'cols': H, 'rows': ggs}, 'gg_north': {'st': st, 'rows': ggn}, 'sido2020': sido}
    p = os.path.join(ROOT, 'data', 'call112.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('112 바이트', os.path.getsize(p), '서울 서', len(seoul), {k: seoul[k][-1] for k in ('서초', '방배') if k in seoul})
    # ── 119 구조
    r = rd('15062386'); D = {}; SIDO = {'서울특별시': '서울', '경기도': '경기', '인천광역시': '인천'}; ALLH = {k: [0] * 24 for k in SIDO.values()}; ALLG = {k: [[0] * 24 for _ in GRP] for k in SIDO.values()}; n = 0; bad = 0
    for x in r[1:]:
        if len(x) < 10 or x[5] not in SIDO: continue
        try: h = int(x[2][:2])
        except Exception: bad += 1; continue
        sd = SIDO[x[5]]; k = (sd, x[6].strip(), x[7].strip()); d = D.setdefault(k, {'h': [0] * 24, 'g': [0] * 6, 't': [0] * 24, 'm': []}); g = grp(x[8].strip()); d['h'][h] += 1; d['g'][g] += 1; ALLH[sd][h] += 1; ALLG[sd][g][h] += 1; n += 1
        if g == 1: d['t'][h] += 1
        try:
            a = datetime.datetime.strptime(x[1] + ' ' + x[2], '%Y-%m-%d %H:%M'); b = datetime.datetime.strptime(x[3] + ' ' + x[4], '%Y-%m-%d %H:%M'); mm = (b - a).total_seconds() / 60
            if 0 <= mm <= 120: d['m'].append(mm)
        except Exception: pass
    items = [[k[0], k[1], k[2], sum(d['h']), d['h'], d['g'], d['t'], (round(statistics.median(d['m']), 1) if len(d['m']) >= 20 else None)] for k, d in sorted(D.items()) if k[2]]
    doc = {'schema': 'tg-rescue119/1', 'made': td, 'year': 2025, 'source': '공공데이터포털 「소방청_구조활동현황」(15062386 · 2025-01-01 ~ 12-31 · 전국 613,150건 가운데 서울·경기·인천 %d건)' % n,
           'note': ['**119 구조대 출동**이다(화재 확인·교통사고 구조·승강기 갇힘·수난·산악·위치 확인 등) — **구급차 출동(환자 이송)은 여기에 없다**. 구급의 동 × 시간대 공개 자료는 찾지 못했다(서울은 2019년 동 × 해뿐 · more-sources.json)',
                    '자리는 신고가 적힌 **법정동**(시·구·동 이름)이다 — 행정동이 아니다. 동 이름이 빈 줄은 뺐다 · 시각은 신고 시각의 시(0~23)',
                    '원자료는 1건 단위(접수번호·분 단위 시각·사고 원인)다 — 저장소에는 동 × 시 × 갈래로 묶은 수만 싣는다. 「자살추정」은 「위치확인」과 한 갈래(신변·위치 확인)로 묶었다',
                    '「화재」 갈래는 화재 현장에 구조대가 같이 나간 건(화재확인 포함)이라 화재 발생 건수가 아니다',
                    '신고 → 출동 시간(분)은 그 동의 가운데값이고 20건이 안 되는 동은 null — 「도착」 시간이 아니다(출동 지령까지)',
                    '시각 칸이 깨진 %d줄은 뺐다' % bad],
           'fields': {'groups': '갈래 여섯(이 차례)', 'sido': '{시도: {h [시 0~23 건수], g [갈래 6][시 0~23]}}', 'items': '[[시도, 시군구, 법정동, 한 해 건수, 시간대별 건수[24], 갈래별 건수[6], 교통 갈래의 시간대별 건수[24], 신고→출동 가운데값(분) 또는 null]]'},
           'groups': GRP, 'sido': {k: {'h': ALLH[k], 'g': ALLG[k]} for k in ALLH}, 'items': items}
    p = os.path.join(ROOT, 'data', 'rescue119.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('119 바이트', os.path.getsize(p), '동', len(items), '건', n, '깨짐', bad)
    print('서울 시간대', ALLH['서울']); print('서울 교통 시간대', ALLG['서울'][1])
    print([(i[2], i[3], i[5], i[7]) for i in items if i[1] == '서초구'])
if __name__ == '__main__': main()
