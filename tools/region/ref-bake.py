# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.0.0 — 🗣 자동 해설의 「지역 평균」 기준값 : 이미 구운 r/<구>/dong.json(주민 연령·생활인구·동 카드 매출)과 r/<구>/jgg.json(집계구 주민·종사자)을 서울·경기로 모은다
#   계산만 한다(새로 받는 자료 없음) · py -3.12 -X utf8 tools/region/ref-bake.py  →  data/area-ref.json
import json, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    R = {}
    for sd, pre in (('서울', '11'), ('경기', '41'), ('인천', '28')):   # v2.7.0 인천
        app = []; age = [0] * 10; tot = 0; tb = [0] * 6; dw = [0] * 7; amt = 0; wd = [0] * 24; we = [0] * 24; jp = jw = jh = 0; nd = 0; ns = 0
        for fn in glob.glob(os.path.join(ROOT, 'data', 'r', pre + '*', 'dong.json')):
            for d in json.load(open(fn, encoding='utf-8'))['dong']:
                p = d.get('pop')
                if p and p.get('age'):
                    nd += 1; tot += p['tot']; age = [a + b for a, b in zip(age, p['age'])]
                s = d.get('sales')
                if s and s.get('tb'):
                    ns += 1; amt += s['amt']
                    if p and p.get('tot'): app.append(s['amt'] / p['tot'])
                    tb = [a + b for a, b in zip(tb, s['tb'])]
                    if s.get('dw'): dw = [a + b for a, b in zip(dw, s['dw'])]
                L = d.get('live')
                if L and L.get('wd'): wd = [a + b for a, b in zip(wd, L['wd'])]; we = [a + b for a, b in zip(we, L.get('we') or L['wd'])]
        for fn in glob.glob(os.path.join(ROOT, 'data', 'r', pre + '*', 'jgg.json')):
            for t in json.load(open(fn, encoding='utf-8'))['items']:
                if t[4] is not None and t[9] is not None: jp += t[4]; jw += t[9]
                if t[5] is not None: jh += t[5]
        S = sum(tb) or 1; W = sum(dw) or 1
        R[sd] = {'dongs': nd, 'age': [round(a / tot * 100, 1) for a in age] if tot else None,
                 'tb': [round(a / S * 100, 1) for a in tb] if ns else None, 'dw': [round(a / W * 100, 1) for a in dw] if ns else None, 'salesDongs': ns,
                 'liveDayNight': round((sum(wd[11:15]) / 4) / ((sum(wd[0:5]) / 5) or 1), 2) if sum(wd) else None,
                 'wrkPerPop': round(jw / jp, 2) if jp else None, 'amtPerPopMed': round(sorted(app)[len(app) // 2], 1) if app else None, 'amtPerPopP80': round(sorted(app)[int(len(app) * 0.8)], 1) if app else None, 'hhPop': jh and round(jp / jh, 2)}
        print(sd, R[sd])
    gg = []   # 경기 — 경기데이터드림 카드(2025년 1~6월 월평균) ÷ 주민
    for fn in glob.glob(os.path.join(ROOT, 'data', 'r', '41*', 'ggdong.json')):
        G = json.load(open(fn, encoding='utf-8')); dj = os.path.join(os.path.dirname(fn), 'dong.json')
        pops = {q['k']: (q.get('pop') or {}).get('tot') for q in json.load(open(dj, encoding='utf-8'))['dong']} if os.path.exists(dj) else {}
        for k, v in G['dong'].items():
            c = (v.get('card') or {}).get('2025'); pp = pops.get(k)
            if c and pp: gg.append(sum(q for kk, q in c.items() if kk != 'TO') / pp)   # v2.87.1 업종전체(TO) 빼고
    gg.sort()
    if gg: R['경기']['ggAmtPerPopMed'] = round(gg[len(gg) // 2], 1); R['경기']['ggAmtPerPopP80'] = round(gg[int(len(gg) * 0.8)], 1); print('경기 카드/주민', R['경기']['ggAmtPerPopMed'], R['경기']['ggAmtPerPopP80'], len(gg))
    out = {'schema': 'tg-arearef/1', 'source': '이 지도에 구운 자료로 다시 계산 — 주민 연령(행안부 주민등록 · dong.json) · 생활인구(서울시·KT · 경기는 있는 동만) · 동 카드 매출(서울시 상권분석서비스 추정매출-행정동 · 서울만) · 집계구 주민·종사자(통계청 SGIS 2023)',
           'fields': 'age = 0~9 … 90~ 세 10칸 비율(%) · tb = 카드 매출 시간대 6칸(0~6·6~11·11~14·14~17·17~21·21~24시) 비율 · dw = 요일(월~일) 비율 · liveDayNight = 평일 11~14시 생활인구 ÷ 0~4시 · wrkPerPop = 종사자 ÷ 주민 · amtPerPopMed/P80 = 동 카드 매출(만 원/월) ÷ 주민의 동별 중앙값·상위 20% 경계', 'ref': R}
    json.dump(out, open(os.path.join(ROOT, 'data', 'area-ref.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    main()
