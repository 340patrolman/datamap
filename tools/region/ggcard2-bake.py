# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.12.0 — 💳 경기 카드 소비(상세) · 경기데이터드림 「카드 소비 데이터」(민간데이터 카드 · tbsh_gyeonggi_day · 공공누리 2유형 = 출처표시·상업 이용 금지)
#   행정동 × 업종(대·중분류) × 시간대 10 × 성별 × 연령 11 × 요일 → 동마다 한 분기 합(월평균은 ÷ 달 수)
#   코드 뜻 = 「경기도 시군 민간데이터 규격서_카드」(경기데이터드림 VXAO78X4HZWG2AZZJNNY35071454 · 2026-10-06 확인):
#     시간대 01 00~06:59 · 02 07~08:59 · 03 09~10:59 · 04 11~12:59 · 05 13~14:59 · 06 15~16:59 · 07 17~18:59 · 08 19~20:59 · 09 21~22:59 · 10 23~23:59
#     연령 01 0~9세 … 10 90~99세 · 11 100세 이상 · 요일 01 월 … 07 일 · 금액 = 원
#   원자료 07_API키/out/ggcard_raw/card_*.zip(손으로 받음 · 시마다 CSV) · 이 지도 행정동 코드와 안 맞는 동은 세어서 버린다(지어내지 않는다)
#   py -3.12 -X utf8 tools/region/ggcard2-bake.py → data/r/<경기 구>/ggcard.json
import csv, io, json, os, sys, zipfile, collections, glob, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'ggcard_raw')
R = os.path.join(ROOT, 'data', 'r')
HR = ['0~6시', '7~8시', '9~10시', '11~12시', '13~14시', '15~16시', '17~18시', '19~20시', '21~22시', '23시']
AG = ['0~9', '10대', '20대', '30대', '40대', '50대', '60대', '70대', '80대', '90대', '100+']

def main():
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); known = {}
    for g in IX['gus']:
        if g['gu'][:2] != '41': continue
        try:
            for d in json.load(open(os.path.join(R, g['gu'], 'dong.json'), encoding='utf-8'))['dong']: known[d['k']] = g['gu']
        except Exception: pass
    A = collections.defaultdict(lambda: {'amt': 0, 'cnt': 0, 'hr': [0] * 10, 'sx': [0, 0], 'ag': [0] * 11, 'agm': [0] * 11, 'agf': [0] * 11, 'dw': [0] * 7, 'big': collections.Counter(), 'mid': collections.Counter(), 'bigag': collections.defaultdict(lambda: [0] * 11)})
    months = set(); miss = collections.Counter(); cities = set(); rows = 0; t0 = time.time()
    for zp in sorted(glob.glob(os.path.join(RAW, 'card_*.zip'))):
        z = zipfile.ZipFile(zp)
        for inf in z.infolist():
            if not inf.filename.lower().endswith('.csv'): continue
            nm = inf.filename
            try: nm = nm.encode('cp437').decode('cp949')
            except Exception: pass
            cities.add(nm.rsplit('_', 1)[-1].replace('.csv', ''))
            rd = csv.reader(io.TextIOWrapper(z.open(inf), encoding='utf-8-sig')); hd = next(rd)
            ix = {h: i for i, h in enumerate(hd)}
            iy, ik, ib, im, ih, isx, ia, idw, iam, ic = [ix[h] for h in ('ta_ymd', 'admi_cty_no', 'card_tpbuz_nm_1', 'card_tpbuz_nm_2', 'hour', 'sex', 'age', 'day', 'amt', 'cnt')]
            for r in rd:
                rows += 1; k = r[ik][:8]
                if k not in known: miss[k] += 1; continue
                months.add(r[iy][:6]); a = A[k]; amt = int(r[iam] or 0); cnt = int(r[ic] or 0)
                a['amt'] += amt; a['cnt'] += cnt
                h = int(r[ih]) - 1; g = int(r[ia]) - 1; w = int(r[idw]) - 1
                if 0 <= h < 10: a['hr'][h] += amt
                if 0 <= g < 11:
                    a['ag'][g] += amt; (a['agm'] if r[isx] == 'M' else a['agf'])[g] += amt; a['bigag'][r[ib]][g] += amt
                if 0 <= w < 7: a['dw'][w] += amt
                a['sx'][0 if r[isx] == 'M' else 1] += amt
                a['big'][r[ib]] += amt; a['mid'][r[ib] + '·' + r[im]] += amt
            print(nm, rows, round(time.time() - t0), flush=True)
    nm_ = len(months) or 1; per = collections.defaultdict(dict)
    for k, a in A.items():
        f = lambda v: round(v / nm_ / 1e4)   # 만 원 · 한 달 평균
        per[known[k]][k] = {'amt': f(a['amt']), 'cnt': round(a['cnt'] / nm_), 'hr': [f(v) for v in a['hr']], 'sx': [f(v) for v in a['sx']], 'ag': [f(v) for v in a['ag']], 'agm': [f(v) for v in a['agm']], 'agf': [f(v) for v in a['agf']],
                            'dw': [f(v) for v in a['dw']], 'big': [[b, f(v)] for b, v in a['big'].most_common()], 'mid': [[b, f(v)] for b, v in a['mid'].most_common(12)],
                            'bigag': {b: [f(v) for v in vv] for b, vv in a['bigag'].items() if sum(vv) >= a['amt'] * 0.05}}
    gb = {}
    for gu, ds in per.items():
        doc = {'schema': 'tg-ggcard/1', 'gu': gu, 'months': sorted(months),
               'source': '경기데이터드림 「카드 소비 데이터」(민간데이터 카드 · 국민·비씨·롯데·삼성·하나카드 · tbsh_gyeonggi_day) ' + min(months) + '~' + max(months) + ' · 공공누리 2유형(출처표시 · 상업적 이용 금지) · 코드 = 「경기도 시군 민간데이터 규격서_카드」',
               'fields': '동: {amt 한 달 평균 매출(만 원), cnt 건수, hr 시간대 10(' + ' · '.join(HR) + '), sx [남, 여], ag·agm·agf 연령 11(' + ' · '.join(AG) + ') 전체·남·여, dw 요일 월~일, big 업종 대분류, mid 중분류 상위 12, bigag 대분류(5%↑)×연령}',
               'note': '카드 다섯 곳 결제만 — 현금·다른 카드·온라인 결제는 빠진다 · 서울 추정매출(만든 곳·세는 법 다름)과 금액을 직접 견주지 않는다 · 비상업 지도에만 쓴다(유료 기능에 쓰지 않음)', 'hr': HR, 'ag': AG, 'dong': ds}
        p = os.path.join(R, gu, 'ggcard.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(p)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['ggcard'] = gb[g['gu']]
    IX['layers']['ggcard'] = '💳 경기 카드 소비 상세(행정동 · 연령·성별·시간대·요일·업종)'
    json.dump(IX, open(os.path.join(R, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('줄', rows, '달', sorted(months), '시', sorted(cities), '동', sum(len(v) for v in per.values()), '구', len(per), '바이트', sum(gb.values()), '안 맞는 동', len(miss), sum(miss.values()), list(miss.most_common(8)))

if __name__ == '__main__': main()
