# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 경찰청 신호계획 서울 전부(소유자 2026-10-10 「신호값이 있는 서울을 먼저 하고 수정되는지 확인하자」) → data/signal-tod-seoul.json
#   종전 data/signal-tod-seocho.json 은 서초 둘레 51곳뿐 — 같은 꼴(tg-signal-tod/1)로 경찰청이 공개한 서울 교차로 전부를 굽는다(값을 그대로 · 고치지 않는다)
#   원자료 = 07_API키/신호앱/data/signal_cross.tsv(번호·이름·좌표) · signal_dow.tsv(요일 1 일 … 7 토 → 계획 번호) · signal_plan.tsv(계획·시각·주기·옵셋·현시값 A·B)
#     ← 경찰청_교차로기반정보서비스(15056721)·교차로계획정보서비스(15056569) · 공공데이터포털 · 2026-09-10 01:00 갱신분(경찰청이 날마다 01시 갱신 — 새로 받으려면 07_API키/RUN_signal.bat)
#   옵셋의 기준 = 자정(data/sig-offset-check.json): 주기 시작 = (하루 초 − 옵셋) 이 주기로 나누어떨어지는 때
#   py -3.12 -X utf8 tools/signal/tod-bake.py
import csv, json, os, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱', 'data')
def rows(fn): return list(csv.DictReader(open(os.path.join(SRC, fn), encoding='utf-8-sig'), delimiter='\t'))
def main():
    X = rows('signal_cross.tsv'); DW = collections.defaultdict(dict); PL = collections.defaultdict(lambda: collections.defaultdict(list)); bad = 0
    for r in rows('signal_dow.tsv'): DW[r['int_no']][r['dow']] = r['plan']
    for r in rows('signal_plan.tsv'):
        c = int(r['cycle']); a = [int(x) for x in r['aring'].split()]; b = [int(x) for x in r['bring'].split()]
        if sum(a) != c or sum(b) != c: bad += 1
        PL[r['int_no']][r['plan']].append([r['hhmm'], c, int(r['offset']), r['aring'], r['bring']])
    spots = []; nodow = 0
    for x in X:
        no = x['int_no']
        if no not in PL: continue
        for p in PL[no].values(): p.sort()
        if not DW.get(no): nodow += 1
        spots.append({'no': no, 'name': x['name'], 'lat': round(float(x['lat']), 7), 'lon': round(float(x['lon']), 7), 'dow': DW.get(no) or {}, 'plans': {k: v for k, v in sorted(PL[no].items(), key=lambda kv: int(kv[0]))}})
    doc = {'schema': 'tg-signal-tod/1', 'made': __import__('datetime').date.today().isoformat(),
           'source': '경찰청_교차로기반정보서비스 · 교차로계획정보서비스 · 공공데이터포털(data.go.kr 15056721·15056569) · 2026-09-10 01:00 갱신분 — 경찰청이 공개한 서울 교차로 전부',
           'note': ['요일마다 도는 계획 번호가 다르고(dow · 1 일 … 7 토), 계획마다 시각별 주기·옵셋·현시값이 있다 · 그날 첫 계획보다 이르면 전날 마지막 계획이 이어진다',
                    '현시값의 합 = 주기 — 어긋나는 줄 %d개는 원자료 그대로 두었다(어느 요일도 쓰지 않는 예비 계획에 몰려 있다)' % bad,
                    'dow 가 빈 교차로 %d곳은 요일 계획이 지정되지 않은 곳이다(원자료에 없음) — 어느 계획이 도는지 이 자료로는 모른다' % nodow,
                    'A링과 B링이 다르면 겹침 현시(좌회전 lead/lag)다 · 어느 현시가 어느 방향인지는 이 자료에 없다',
                    '옵셋은 자정 기준이다 — 주기 시작 = (하루 초 − 옵셋) 이 주기로 나누어떨어지는 때(data/sig-offset-check.json 에서 실제 녹색 시각과 대조) · 계획값이라 감응·수동 운영 때는 다르다',
                    '계획은 바뀐다(경찰청이 날마다 갱신) — 이 파일은 받은 날의 것이다'],
           'fields': 'spots[{no 교차로 번호(서울 C-ITS·T-Data 와 같은 번호), name, lat, lon, dow{요일 1 일 … 7 토: 계획 번호}, plans{계획 번호: [[시작 HH:MM, 주기 초, 옵셋 초, A링 현시값(빈칸으로 나눔), B링 현시값]…]}}]',
           'dowKo': ['일', '월', '화', '수', '목', '금', '토'], 'spots': spots}
    p = os.path.join(ROOT, 'data', 'signal-tod-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('교차로', len(spots), '· 요일 계획 없는 곳', nodow, '· 합 ≠ 주기 줄', bad, '· 바이트', os.path.getsize(p))
    old = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seocho.json'), encoding='utf-8')); N = {s['no']: s for s in spots}
    same = sum(1 for o in old['spots'] if str(o['no']) in N and N[str(o['no'])]['plans'] == o['plans'] and N[str(o['no'])]['dow'] == o['dow'])
    print('서초 파일과 같은 곳', same, '/', len(old['spots']))
if __name__ == '__main__': main()
