# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.4.0 — 👥 서울 생활인구 250m 격자(서울시 「서울특별시 250M격자 생활인구(내국인)」 OA-22784 · 공공누리 1유형 · 매일)
#   행정동 단위 생활인구는 2026-07-31 생산 끝 → 이 격자 자료로 바꾼다(전국 확장 설계서 2장)
#   한 주(2026-09-07 월 ~ 09-13 일 · 추석 9/24~26 을 피함)를 받아 칸마다 평일 평균·주말 평균 24시간 + 낮(11~14시)·밤(0~4시) 연령 구성
#   한 칸에 행정동이 여럿이면 동마다 줄이 따로 온다 → 칸 합계는 더한다 · 「*」(3명 이하 비식별)은 0 으로 본다(작은 칸은 조금 적게 나온다)
#   py -3.12 -X utf8 tools/region/live250-bake.py fetch → 07_API키/out/grid/*.zip · build → data/r/<서울 구>/live250.json
import csv, io, json, os, sys, time, zipfile, urllib.request, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'grid')
DAYS = ['202609%02d' % d for d in range(7, 14)]
AGES = ['0~9', '10대', '20대', '30대', '40대', '50대', '60대', '70~']
COLS = {i: b for b, idx in enumerate([[0], [1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12], [13]]) for i in idx}   # 남·여 14칸(0~9 … 70~) → 8칸

def fetch():
    os.makedirs(OUT, exist_ok=True)
    for d in DAYS:
        fn = os.path.join(OUT, '250_LOCAL_RESD_%s.zip' % d)
        if os.path.exists(fn) and os.path.getsize(fn) > 1e6: continue
        body = ('infId=OA-22784&seqNo=&seq=%s&infSeq=1' % d[2:]).encode()
        r = urllib.request.urlopen(urllib.request.Request('https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false', data=body,
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://data.seoul.go.kr/dataList/OA-22784/S/1/datasetView.do'}), timeout=300).read()
        if r[:2] != b'PK': raise RuntimeError('zip 아님 %s %s' % (d, r[:120]))
        open(fn, 'wb').write(r); print('받음', d, len(r), flush=True); time.sleep(1)

def num(s):
    s = s.strip()
    try: return float(s)
    except Exception: return 0.0

def build():
    cell_gu = {}
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    for g in IX['gus']:
        if g['gu'][:2] != '11': continue
        for c in json.load(open(os.path.join(ROOT, 'data', 'r', g['gu'], 'grid.json'), encoding='utf-8'))['cells']: cell_gu[c[0]] = g['gu']
    S = collections.defaultdict(lambda: {'wd': [0.0] * 24, 'we': [0.0] * 24, 'ad': [0.0] * 8, 'an': [0.0] * 8, 'dong': collections.Counter()})
    nwd = nwe = 0
    for d in DAYS:
        wk = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday() >= 5
        if wk: nwe += 1
        else: nwd += 1
        z = zipfile.ZipFile(os.path.join(OUT, '250_LOCAL_RESD_%s.zip' % d)); nm = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
        rd = csv.reader(io.TextIOWrapper(z.open(nm), encoding='cp949')); next(rd)
        for row in rd:
            c = row[3].strip(); h = int(row[1]); tot = num(row[4]); x = S[c]
            (x['we'] if wk else x['wd'])[h] += tot
            if not wk:
                x['dong'][row[2].strip()[:8]] += tot
                if 11 <= h <= 13 or 0 <= h <= 3:
                    tgt = x['ad'] if h >= 11 else x['an']
                    for i in range(14): tgt[COLS[i]] += num(row[5 + i]) + num(row[19 + i])
        print('읽음', d, '주말' if wk else '평일', flush=True)
    per = collections.defaultdict(dict); miss = 0
    for c, x in S.items():
        gu = cell_gu.get(c)
        if not gu:
            dm = x['dong'].most_common(1); gu = dm[0][0][:5] if dm else None
            if not gu or not os.path.isdir(os.path.join(ROOT, 'data', 'r', gu)): miss += 1; continue
        sd = sum(x['ad']) or 1; sn = sum(x['an']) or 1; dt = sum(x['dong'].values()) or 1
        per[gu][c] = {'wd': [round(v / nwd) for v in x['wd']], 'we': [round(v / nwe) for v in x['we']],
                      'ad': [round(v / sd * 100) for v in x['ad']], 'an': [round(v / sn * 100) for v in x['an']],
                      'dong': {k: round(v / dt * 100) for k, v in x['dong'].most_common() if v / dt >= 0.05}}
    gb = {}
    for gu, cells in per.items():
        doc = {'schema': 'tg-live250/1', 'gu': gu,
               'source': '서울시 서울특별시 250M격자 생활인구(내국인) OA-22784 · 공공누리 1유형(출처표시) · %s~%s 한 주(평일 %d일·주말 %d일)' % (DAYS[0], DAYS[-1], nwd, nwe),
               'fields': 'wd/we = 평일·주말 하루 평균 0~23시 생활인구(명) · ad/an = 평일 낮(11~14시)·밤(0~4시) 연령 8칸 비율 %(' + '·'.join(AGES) + ') · dong = 평일 생활인구가 잡힌 행정동 비율 %',
               'note': '3명 이하 값(*)은 0 으로 셈 · 내국인만(장기·단기 체류 외국인은 별도 자료) · 행정동 단위 생산은 2026-07-31 끝', 'ages': AGES, 'cells': cells}
        pth = os.path.join(ROOT, 'data', 'r', gu, 'live250.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['live250'] = gb[g['gu']]
    IX['layers']['live250'] = '서울 생활인구 250m 격자(한 주 평균 · 평일·주말 24시간)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('칸', sum(len(v) for v in per.values()), '구', len(per), '못 붙임', miss, '바이트', sum(gb.values()))

if __name__ == '__main__':
    fetch() if sys.argv[1:] == ['fetch'] else build()
