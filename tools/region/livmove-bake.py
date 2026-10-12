# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚕 수도권 생활이동: 도착 행정동 × 시간대 × 이동 수단 → data/move-mode-seoul.json
#   소유자 2026-10-12 「서로가 서로에게 영향을 미치며 사니 · 오만가지 자료」 → 택시 승하차(동 × 시)는 공개 자료가 없다 — 가장 가까운 것이 이 자료의 「차량」(택시·자가용·대리운전이 섞여 있다)
#   원자료: 서울 열린데이터광장 OA-22655 「수도권 생활이동 (도착 행정동 기준 시간대별 성연령별 수단 데이터 (내국인))」(서울시·KT · 공공누리 1유형 · 달마다 zip 약 110MB · 날마다 csv)
#     받는 법: datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false 에 POST infId=OA-22655&seq=<연월>&infSeq=1 + Referer → 07_API키/out/livmove/in_<연월>.zip
#   칸: d_admdong_cd(서울은 행정동 8자리 · 서울 밖은 시군구 5자리+000) · time_cd(00~23 · 7~9시·17~19시는 20분 칸 0700·0720…) · move_trans(1~9) · 성×나이 16칸 · total_cnt
#   ⚠ move_trans 코드표를 원문으로 보지 못했다 — 서울시 발표의 차례(항공·기차·고속버스·광역버스·일반버스·지하철·도보·차량 + 기타)와 **값의 분포**(1 = 제주·공항동 · 2 = 용산·수서·서울역 · 6 = 새벽 1~4시에 거의 0 이고 역삼1동·종로 · 8 = 가장 큼)로 맞췄다. 매뉴얼을 받으면 다시 본다
#   py -3.12 -X utf8 tools/region/livmove-bake.py [연월]   (기본 = 받아 둔 것 가운데 마지막)
import json, os, sys, glob, csv, io, zipfile, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'livmove')
G = {'8': 0, '6': 1, '4': 2, '5': 2, '7': 3}; GN = ['차량', '지하철', '버스(광역+일반)', '도보', '그 밖(항공·기차·고속버스·기타)']; M9 = ['항공', '기차', '고속버스', '광역버스', '일반버스', '지하철', '도보', '차량', '기타']
def main():
    f = os.path.join(SRC, 'in_%s.zip' % sys.argv[1]) if len(sys.argv) > 1 else sorted(glob.glob(os.path.join(SRC, 'in_*.zip')))[-1]; ym = os.path.basename(f)[3:9]
    HOL = set(json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8')).get('days', {}))
    if not HOL: HOL = set(d[0] if isinstance(d, list) else d for d in json.load(open(os.path.join(ROOT, 'data', 'holidays.json'), encoding='utf-8')).get('items', []))
    A = collections.defaultdict(lambda: [[[0.0] * 5 for _ in range(24)], [[0.0] * 5 for _ in range(24)]]); ND = [0, 0]; T9 = [[[0.0] * 9 for _ in range(24)], [[0.0] * 9 for _ in range(24)]]; LATE = [collections.Counter(), collections.Counter()]
    z = zipfile.ZipFile(f)
    for n in sorted(z.namelist()):
        d = n[-12:-4]; day = datetime.date(int(d[:4]), int(d[4:6]), int(d[6:])); w = 1 if (day.weekday() >= 5 or day.isoformat() in HOL) else 0; ND[w] += 1
        with z.open(n) as fh:
            rd = csv.reader(io.TextIOWrapper(fh, encoding='utf-8')); next(rd)
            for r in rd:
                c = r[0]
                if c[:2] not in ('11', '41', '28'): continue
                h = int(r[1][:2]); t = float(r[19]); m = r[2]; A[c][w][h][G.get(m, 4)] += t
                if c[:2] == '11': T9[w][h][int(m) - 1] += t
    items = []
    for c in sorted(A):
        row = [c]
        for w in (0, 1): row.append([[round(x / ND[w]) for x in A[c][w][h]] for h in range(24)] if ND[w] else None)
        items.append(row)
    doc = {'schema': 'tg-move-mode/1', 'made': datetime.date.today().isoformat(), 'month': ym,
           'source': '서울 열린데이터광장 OA-22655 「수도권 생활이동 (도착 행정동 기준 시간대별 성연령별 수단 데이터 (내국인))」 %s-%s (서울특별시·KT · 공공누리 1유형)' % (ym[:4], ym[4:]),
           'note': ['**도착한 곳 기준** — 그 시간대에 그 동(서울 밖은 시군구)에 도착한 이동의 수(통신 자료로 어림한 값 · 내국인만). 하루 평균(평일 %d일 · 주말·공휴일 %d일)' % (ND[0], ND[1]),
                    '「차량」에는 택시·자가용·대리운전이 섞여 있다 — 택시만 따로는 아니다(택시 승하차의 동 × 시 공개 자료는 없다 · more-sources.json)',
                    '수단 코드(1~9)의 뜻은 원문 코드표를 보지 못해 서울시 발표의 차례와 값의 분포로 맞췄다(1 항공 · 2 기차 · 3 고속버스 · 4 광역버스 · 5 일반버스 · 6 지하철 · 7 도보 · 8 차량 · 9 기타) — 매뉴얼로 확인되기 전까지 「추정」으로 읽는다',
                    '통신 신호로 수단을 가른 것이라 교통카드 승하차(지하철·버스 자료)와 수가 맞지 않는다 — 같은 줄에 놓고 더하지 않는다. 한 동 안의 시간대 흐름과 수단끼리의 몫을 보는 데 쓴다',
                    '서울은 행정동 8자리(뒤에 00 을 붙이면 10자리 코드) · 경기·인천은 시군구(5자리 + 000) 단위다 · 그 밖의 시도는 뺐다',
                    '7~9시·17~19시는 원자료가 20분 칸이라 한 시간으로 합쳤다'],
           'fields': {'groups': '수단 묶음 다섯(이 차례)', 'modes9': '원자료 수단 아홉(코드 1~9 차례 — 추정)', 'days': '[평일 날수, 주말·공휴일 날수]',
                      'items': '[[도착지 코드, 평일 [시 0~23][수단 묶음 5] 하루 평균 도착 수, 주말·공휴일 같은 꼴]]', 'seoul9': '[평일, 주말] 서울 전체 [시 0~23][수단 9] 하루 평균'},
           'groups': GN, 'modes9': M9, 'days': ND, 'seoul9': [[[round(x / ND[w]) for x in T9[w][h]] for h in range(24)] for w in (0, 1)], 'items': items}
    p = os.path.join(ROOT, 'data', 'move-mode-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '도착지', len(items), '날', ND)
    s = doc['seoul9'][0]; print('서울 평일 시간대별 차량', [s[h][7] for h in range(24)]); print('지하철', [s[h][5] for h in range(24)]); print('도보', [s[h][6] for h in range(24)])
    it = {r[0]: r for r in items}
    for c, nm in (('11650510', '서초1동?'), ('11650621', '방배?'), ('11680640', '역삼1동')):
        if c in it: print(c, nm, '평일 차량 22~03시', [it[c][1][h][0] for h in (22, 23, 0, 1, 2, 3)], '주말', [it[c][2][h][0] for h in (22, 23, 0, 1, 2, 3)])
    late = sorted(((sum(r[1][h][0] for h in (23, 0, 1, 2, 3)), r[0]) for r in items if r[0][:2] == '11'), reverse=True)[:12]; print('평일 밤 23~03시 차량 도착 많은 서울 동', late)
if __name__ == '__main__': main()
