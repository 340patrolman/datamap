# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚲 따릉이 대여소 × 시간대 대여 → data/bike-hour-seoul.json
#   소유자 2026-10-12 「서로가 서로에게 영향을 미치며 사니 · 오만가지 자료」 → 막차 뒤·새벽의 짧은 이동, 한강공원 가는 길 — 「이 자리의 하루」의 한 줄
#   원자료(서울 열린데이터광장 · 공공누리 1유형 · 파일은 POST 로): OA-15245 「서울특별시 공공자전거 이용정보(시간대별)」 달마다 csv(약 390MB · cp949 · 대여일자·대여시간·대여소번호·대여소명·대여구분·성별·연령대·이용건수…)
#     + OA-13252 「공공자전거 대여소 정보」 xlsx(대여소번호·자치구·주소·위도·경도) → 07_API키/out/bike/time_<연월>.csv · station.xlsx
#     받는 법: datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false 에 POST infId=OA-15245&seq=<파일 번호>&infSeq=2 + Referer(infSeq=3 은 「잘못된 접근」 — 2 가 내려받기다)
#   ⚠ 이 자료는 **대여한 곳·대여한 시각**만 있다 — 어디에 반납했는지(반납 시각·대여소)는 없다(대여-반납 짝은 OA-15182 「대여이력」에 있다 · 아직 안 받음)
#   py -3.12 -X utf8 tools/region/bike-bake.py [연월]
import json, os, sys, glob, csv, datetime, collections, openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'bike')
def main():
    f = os.path.join(SRC, 'time_%s.csv' % sys.argv[1]) if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(SRC, 'time_*.csv')))[-1]; ym = os.path.basename(f)[5:11]
    HOL = set(json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8'))['days'])
    XY = {}
    for r in openpyxl.load_workbook(os.path.join(SRC, 'station.xlsx'), read_only=True).worksheets[0].iter_rows(values_only=True):
        if isinstance(r[0], int) and isinstance(r[4], float) and r[4] > 30: XY[r[0]] = [(r[1] or '').strip(), r[2], round(r[5], 5), round(r[4], 5)]
    A = collections.defaultdict(lambda: [[0] * 24, [0] * 24]); NM = {}; DAYS = [set(), set()]; TOT = [[0] * 24, [0] * 24]; AGE = collections.Counter(); bad = 0
    with open(f, encoding='cp949', errors='replace', newline='') as fh:
        rd = csv.reader(fh); next(rd)
        for r in rd:
            try: d = r[0]; h = int(r[1]); sid = int(r[2]); n = int(r[7])
            except Exception: bad += 1; continue
            day = datetime.date(int(d[:4]), int(d[5:7]), int(d[8:10])); w = 1 if (day.weekday() >= 5 or d in HOL) else 0; DAYS[w].add(d); A[sid][w][h] += n; TOT[w][h] += n; NM[sid] = r[3]
            if h in (23, 0, 1, 2, 3, 4): AGE[r[6]] += n
    ND = [len(DAYS[0]), len(DAYS[1])]; items = []; miss = 0; missn = 0
    for sid, v in A.items():
        s = XY.get(sid)
        if not s: miss += 1; missn += sum(v[0]) + sum(v[1]); continue
        items.append([sid, s[0], s[1], s[2], s[3], [round(x / ND[0], 1) for x in v[0]], [round(x / ND[1], 1) for x in v[1]]])
    items.sort(key=lambda r: -(sum(r[5]) + sum(r[6])))
    doc = {'schema': 'tg-bike-hour/1', 'made': datetime.date.today().isoformat(), 'month': ym,
           'source': '서울 열린데이터광장 OA-15245 「서울특별시 공공자전거 이용정보(시간대별)」 %s-%s · OA-13252 「공공자전거 대여소 정보」(서울특별시 · 공공누리 1유형)' % (ym[:4], ym[4:]),
           'note': ['**대여한 곳·대여한 시각**이다 — 반납한 곳과 시각은 이 자료에 없다(도착하는 사람이 아니라 떠나는 사람) · 하루 평균(평일 %d일 · 주말·공휴일 %d일)' % (ND[0], ND[1]),
                    '따릉이는 철을 탄다 — 이 달(%s-%s)의 값이고 겨울·장마에는 크게 준다. 다른 달과 견주려면 그 달을 따로 받아 굽는다' % (ym[:4], ym[4:]),
                    '대여소 정보에 자리가 없는 대여소 %d곳(%d건 — 없어졌거나 새로 생긴 곳)은 뺐다' % (miss, missn),
                    '밤 23~04시 대여의 나이대 몫은 night_age(원자료의 연령대 칸 그대로 · 빈칸·기타 포함)'],
           'fields': {'days': '[평일 날수, 주말·공휴일 날수]', 'total': '[평일 [시 0~23 하루 평균 대여 건수], 주말 같은 꼴](서울 전체)', 'night_age': '{연령대: 밤 23~04시 대여 건수(한 달 합)}',
                      'items': '[[대여소 번호, 이름, 자치구, 경도, 위도, 평일 [시 0~23 하루 평균 대여], 주말·공휴일 같은 꼴]] — 대여 많은 차례'},
           'days': ND, 'total': [[round(x / ND[w]) for x in TOT[w]] for w in (0, 1)], 'night_age': dict(AGE.most_common()), 'items': items}
    p = os.path.join(ROOT, 'data', 'bike-hour-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '대여소', len(items), '자리 없음', miss, missn, '날', ND, '깨진 줄', bad); print('평일', doc['total'][0]); print('주말', doc['total'][1]); print('밤 나이대', doc['night_age'])
    print('밤 23~04시 대여 많은 곳(평일)', [(r[1], r[2], round(sum(r[5][h] for h in (23, 0, 1, 2, 3, 4)), 1)) for r in sorted(items, key=lambda r: -sum(r[5][h] for h in (23, 0, 1, 2, 3, 4)))[:12]])
    print('서초', [(r[1], round(sum(r[5]))) for r in items if r[2] == '서초구'][:10])
if __name__ == '__main__': main()
