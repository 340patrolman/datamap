# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 경찰청 신호계획 인천·대구·대전(UTIC tsihub) → data/signal-tod-<도시>.json (서울 data/signal-tod-seoul.json 과 같은 꼴 tg-signal-tod/1)
#   (2026-10-16 · UTIC 두 번째 신청 열쇠 · 게임 세션이 운영계획 1,022,240줄 전부 받음 → 서울 줄 0 · 지역 L02 인천 · L29 대구 · L30 대전(세종 이름 일부 포함))
#   원자료(저장소 밖):
#     07_API키/out/utic/plan/p<쪽>.json  — PlanCrossRoadInfoService/getPlanCROPInfo(운영계획 · 계획 번호·시각 칸·주기·옵셋·A/B링 1~8현시)
#     07_API키/out/utic/cross/cross_<날짜>.json — CrossRoadInfoService/getCrossRoadInfoList(번호·이름·좌표 WGS84×10^7 · 6,389곳)
#     07_API키/out/utic/cross/wd_<날짜>.json    — PlanCrossRoadInfoService/getPlanCRWDInfo(요일 → 계획 번호)
#   값은 그대로 · 주기 0 줄(쓰지 않는 계획 칸)만 뺀다 · 현시값 끝의 0 은 뗀다(서울 파일도 쓰는 현시만 적혀 있다)
#   요일 번호 뜻은 서울 자료와 같다고 본다(1 일 … 7 토 — 서울 388곳 패턴에서 유추한 것 · 이 세 도시에서 따로 확인하지 않음)
#   출처 표기 의무: 「경찰청 도시교통정보센터(UTIC)」
#   py -3.12 -X utf8 tools/signal/utic-tod-bake.py [cross 파일 날짜 20261016]
import sys, os, json, glob, collections, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'utic')
CITY = {'L02': ('incheon', '인천'), 'L29': ('daegu', '대구'), 'L30': ('daejeon', '대전')}


def ring(r, k):
    v = [int(r['%s_RING_%d_PHASE_VAL' % (k, i)] or 0) for i in range(1, 9)]
    while v and v[-1] == 0:
        v.pop()
    return ' '.join(map(str, v))


def main():
    day = next((a for a in sys.argv[1:] if a.isdigit()), '20261016')
    X = json.load(open(os.path.join(RAW, 'cross', 'cross_%s.json' % day), encoding='utf-8'))
    W = json.load(open(os.path.join(RAW, 'cross', 'wd_%s.json' % day), encoding='utf-8'))
    PL = collections.defaultdict(lambda: collections.defaultdict(dict)); bad = collections.Counter(); got = None
    for f in sorted(glob.glob(os.path.join(RAW, 'plan', 'p*.json'))):
        for r in json.load(open(f, encoding='utf-8'))[1:]:
            c = int(r['INT_OPER_CYCLE_VAL'] or 0)
            if c <= 0:
                continue
            key = (r['REGION_CD'], r['INT_NO']); hm = '%02d:%02d' % (int(r['OPER_PLAN_HH']), int(r['OPER_PLAN_MI']))
            a, b = ring(r, 'A'), ring(r, 'B')
            if sum(map(int, a.split() or [0])) != c or sum(map(int, b.split() or [0])) != c:
                bad[r['REGION_CD']] += 1
            PL[key][r['INT_PLAN_NO']][hm] = [hm, c, int(r['INT_OPER_OFFSET_VAL'] or 0), a, b]
    DW = collections.defaultdict(dict)
    for r in W:
        DW[(r['REGION_CD'], r['INT_NO'])][r['PLAN_DY']] = r['INT_PLAN_NO']
        got = got or r.get('COLLCT_DTIME')
    for reg, (en, ko) in CITY.items():
        spots, nodow, noll = [], 0, 0
        for x in X:
            if x['REGION_CD'] != reg:
                continue
            key = (reg, x['INT_NO'])
            if key not in PL:
                continue
            try:
                lat, lon = int(x['Y_COORD']) / 1e7, int(x['X_COORD']) / 1e7
            except (ValueError, TypeError):
                lat = lon = 0
            if not (33 < lat < 39 and 124 < lon < 132):
                noll += 1; continue
            dw = {k: v for k, v in sorted(DW.get(key, {}).items())}
            if not dw or set(dw.values()) <= {'0'}:
                nodow += 1   # 요일마다 계획 번호 0 = 지정 안 됨
            plans = {k: sorted(v.values()) for k, v in sorted(PL[key].items(), key=lambda kv: int(kv[0]))}
            spots.append({'no': x['INT_NO'], 'name': x['INT_NM'], 'lat': round(lat, 7), 'lon': round(lon, 7), 'dow': dw, 'plans': plans})
        doc = {'schema': 'tg-signal-tod/1', 'made': datetime.date.today().isoformat(), 'region': reg, 'city': ko,
               'source': '경찰청 도시교통정보센터(UTIC) 개방데이터 — 교차로 기본정보(CrossRoadInfoService) · 신호 운영·요일 계획(PlanCrossRoadInfoService) · 받은 날 %s · 원자료 수집 %s' % (day, got or ''),
               'credit': '신호정보: 경찰청 도시교통정보센터(UTIC) 제공',
               'note': ['요일마다 도는 계획 번호가 다르고(dow), 계획마다 시각별 주기·옵셋·현시값이 있다 · 그날 첫 계획보다 이르면 전날 마지막 계획이 이어진다',
                        '요일 번호는 서울 자료와 같은 뜻(1 일 … 7 토)으로 본다 — 서울 388곳 패턴에서 유추했고 이 도시에서 따로 확인하지 않았다',
                        '현시값의 합 = 주기 — 어긋나는 줄 %d개는 원자료 그대로 두었다' % bad[reg],
                        'dow 가 비었거나 모든 요일 계획 번호가 0 인 교차로 %d곳은 요일 계획이 지정되지 않은 곳이다(원자료 그대로)' % nodow,
                        '받은 날 이 세 도시는 거의 모두 요일 1 → 4번 · 2 → 2번 · 3~6 → 1번 · 7 → 3번 계획이다 — 요일 번호 뜻을 아직 확인하지 않아 「어느 요일이 어느 계획」은 단정하지 않는다',
                        '이웃한 시각 칸 값이 같은 줄(예 07:00·09:30 같은 값)도 원자료대로 둔다',
                        '옵셋 기준(자정)은 서울에서만 대조했다 — 이 도시에서는 실제 녹색 시각과 맞대 보지 않았다',
                        'A링과 B링이 다르면 겹침 현시다 · 어느 현시가 어느 방향인지는 이 자료에 없다 · 계획값이라 감응·수동 운영 때는 다르다',
                        '번호는 그 도시 안 번호다 — 서울 C-ITS 번호와 겹칠 수 있으니 region 으로 가른다'],
               'fields': 'spots[{no 교차로 번호(그 도시 안), name, lat, lon, dow{요일 1 일 … 7 토: 계획 번호}, plans{계획 번호: [[시작 HH:MM, 주기 초, 옵셋 초, A링 현시값(빈칸으로 나눔), B링 현시값]…]}}]',
               'dowKo': ['일', '월', '화', '수', '목', '금', '토'], 'n': len(spots), 'spots': spots}
        p = os.path.join(ROOT, 'data', 'signal-tod-%s.json' % en)
        json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        print(ko, reg, '교차로', len(spots), '· 요일 없음', nodow, '· 좌표 없음', noll, '· 합≠주기', bad[reg], '· 바이트', os.path.getsize(p))


if __name__ == '__main__':
    main()
