# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.9.0 — 🌏 서울 「지금 머무는 외국인」 250m 격자(서울시 생활인구 장기체류 외국인 OA-22785 · 단기체류 외국인 OA-22786 · 매일)
#   그 시각 그 칸에 있는 외국인(통신 자료 추정) — 행안부 외국인주민(3개월 넘게 사는 사람)·법무부 등록외국인과 정의가 달라 더하지 않는다(설계서 4장)
#   생활인구 내국인(live250)과 같은 한 주(2026-09-07 월 ~ 09-13 일) · 칸마다 평일·주말 24시간 평균 + 국적 상위(주 평균 · 칸 하루 평균)
#   「*」(3명 이하 비식별)은 0 · py -3.12 -X utf8 tools/region/forn250-bake.py fetch → build → data/r/<서울 구>/forn250.json
import csv, io, json, os, sys, time, zipfile, urllib.request, collections, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'grid')
DAYS = ['202609%02d' % d for d in range(7, 14)]
SETS = {'L': ('OA-22785', 'FORN_LONG', '장기체류'), 'T': ('OA-22786', 'FORN_TEMP', '단기체류')}

def fetch():
    for k, (oa, nm, _) in SETS.items():
        for d in DAYS:
            fn = os.path.join(OUT, '250_%s_%s.zip' % (nm, d))
            if os.path.exists(fn) and os.path.getsize(fn) > 1e5: continue
            r = urllib.request.urlopen(urllib.request.Request('https://datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false', data=('infId=%s&seqNo=&seq=%s&infSeq=1' % (oa, d[2:])).encode(),
                headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://data.seoul.go.kr/dataList/%s/S/1/datasetView.do' % oa}), timeout=300).read()
            if r[:2] != b'PK': raise RuntimeError('zip 아님 %s %s' % (nm, d))
            open(fn, 'wb').write(r); print('받음', nm, d, len(r), flush=True); time.sleep(1)

def num(s):
    try: return float(s)
    except Exception: return 0.0

def build():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); cell_gu = {}
    for g in IX['gus']:
        if g['gu'][:2] == '11':
            for c in json.load(open(os.path.join(ROOT, 'data', 'r', g['gu'], 'grid.json'), encoding='utf-8'))['cells']: cell_gu[c[0]] = g['gu']
    per = collections.defaultdict(dict)
    for k, (oa, nm, label) in SETS.items():
        S = collections.defaultdict(lambda: {'wd': [0.0] * 24, 'we': [0.0] * 24, 'nat': collections.Counter()}); nwd = nwe = 0
        for d in DAYS:
            wk = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])).weekday() >= 5
            if wk: nwe += 1
            else: nwd += 1
            z = zipfile.ZipFile(os.path.join(OUT, '250_%s_%s.zip' % (nm, d))); f = [n for n in z.namelist() if n.lower().endswith('.csv')][0]
            rd = csv.reader(io.TextIOWrapper(z.open(f), encoding='cp949')); hd = [h.strip() for h in next(rd)]; nats = [(i, h) for i, h in enumerate(hd) if i >= 5 and h]
            for row in rd:
                c = row[3].strip(); h = int(row[1]); x = S[c]; tot = num(row[4])
                (x['we'] if wk else x['wd'])[h] += tot
                for i, n2 in nats:
                    if i < len(row): x['nat'][n2] += num(row[i])
            print('읽음', nm, d, flush=True)
        for c, x in S.items():
            gu = cell_gu.get(c)
            if not gu: continue
            nd = (nwd + nwe) * 24
            per[gu].setdefault(c, {})[k] = {'wd': [round(v / nwd, 1) for v in x['wd']], 'we': [round(v / nwe, 1) for v in x['we']],
                                            'nat': [[n2, round(v / nd, 1)] for n2, v in x['nat'].most_common(6) if v > 0]}   # 국적 = 그 칸에 한 주 내내 평균으로 머문 인원(모든 시각 평균)
    gb = {}
    for gu, cells in per.items():
        doc = {'schema': 'tg-forn250/1', 'gu': gu,
               'source': '서울시 250M격자 생활인구 — 장기체류 외국인(OA-22785) · 단기체류 외국인(OA-22786) · 서울 열린데이터광장 · 공공누리 1유형 · %s~%s 한 주' % (DAYS[0], DAYS[-1]),
               'fields': '칸: {L 장기체류 · T 단기체류: {wd·we = 평일·주말 하루 평균 0~23시 인원, nat = [국적, 한 주 모든 시각 평균 인원] 상위 6}}',
               'note': '그 시각 그 칸에 있는 외국인(통신 자료 추정) — 행안부 외국인주민·법무부 등록외국인과 정의가 달라 더하지 않는다 · 3명 이하(*)는 0 · 장기 = 91일 이상 체류 · 단기 = 90일 이하(관광·방문)', 'cells': cells}
        pth = os.path.join(ROOT, 'data', 'r', gu, 'forn250.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':')); gb[gu] = os.path.getsize(pth)
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['forn250'] = gb[g['gu']]
    IX['layers']['forn250'] = '서울 지금 머무는 외국인 250m(장기·단기 체류 · 국적)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('칸', sum(len(v) for v in per.values()), '구', len(per), '바이트', sum(gb.values()))

if __name__ == '__main__': fetch() if sys.argv[1:] == ['fetch'] else build()
