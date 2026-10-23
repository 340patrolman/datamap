# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧭 오늘의 결정(js/decide.js)이 읽는 한 장 → data/decide-seocho.json (tg-decide/1)
#   소유자 2026-10-23 「온톨로지 팔란티어 방식을 내 앱들에 · 아는 모든 것을 투입해서 지도와 티북에」 — 설계 = ../14_팔란티어AIP/설계_앱적용.md
#   결정 넷: D1 이 날·시간대에 어느 교차로에 설까 · D2 음주 단속 어디·언제 · D3 집회·행사 날 미리 볼 곳·상류 · D4 큰비 때 먼저 통제할 길·출동 지연
#   숫자는 원자료 값 그대로 옮긴다(순위·둘레 찾기는 지도가 기기에서 한다 — 잣대는 결정마다 하나)
#   py -3.12 -X utf8 tools/onto/decide-bake.py      (rally-bake.py 끝에서도 부른다 — 집회·공연 날짜가 날마다 바뀜)
import json, os, math, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D = os.path.join(ROOT, 'data')
def J(p): return json.load(open(os.path.join(ROOT, p), encoding='utf-8'))
def m(la1, lo1, la2, lo2): return math.hypot((lo1 - lo2) * 88400.0, (la1 - la2) * 111000.0)
R5 = lambda x: round(x, 5)


def main():
    core = J('ontology-core/data/core-seocho.json')
    O = {o['id']: o for o in core['objects']}; out = collections.defaultdict(list)
    for a, rel, b, p in core['edges']: out[(a, rel)].append((b, p))
    ints = {}
    for i, o in O.items():
        if o['t'] != 'INT': continue
        acc = out.get((i, '발생'))
        if not acc: continue
        A = O[acc[0][0]]; mv = collections.Counter()
        for v, p in out.get((A['id'], '주요원인'), []): mv[v] += p.get('n', 0)
        zs = sorted(p.get('d', 9999) for _, p in out.get((i, '가까움'), []))
        ints[i] = [o['nm'], R5(o['lat']), R5(o['lon']), o.get('dongnm') or '', sum(A['years']), A['tod'], A['night'], A['ped'], A['dead'], A['serious'],
                   [[v, n] for v, n in mv.most_common(2)], len(out.get((i, '보유'), [])), len(zs), zs[0] if zs else None,
                   [[b, p.get('m')] for b, p in out.get((i, '인접'), [])], A['years']]
    # 인접이 사고 없는 교차로를 가리킬 수 있다 — 이름·자리는 따로
    nb = {}
    for i, r in ints.items():
        for b, _ in r[14]:
            if b not in ints and b in O: nb[b] = [O[b]['nm'], R5(O[b]['lat']), R5(O[b]['lon'])]
    vio = {k: [o['nm'], [b for b, _ in out.get((k, '근거'), [])]] for k, o in O.items() if o['t'] == 'VIO'}
    law = {k: [o['title'], o.get('penalty') or '', o.get('meta') or '', [O[b]['no'] for b, _ in out.get((k, '해석'), [])]] for k, o in O.items() if o['t'] == 'LAW'}
    hot = [[s['n'], s['la'], s['lo'], sorted({r[0] for r in s['rec']}), sorted({r[1] for r in s['rec']})] for s in J('data/hot10-seocho.json')['spots']]
    # D2 음주
    dc = J('data/dui-catch-st.json'); yrs = sorted(dc['years']); ST = ['서울서초경찰서', '서울방배경찰서']
    grid = {s: [[sum(dc['years'][y][s]['dow_hour'][d][h] for y in yrs if s in dc['years'][y]) for h in range(12)] for d in range(7)] for s in ST}
    dong = []
    for r in J('data/dui-ref-seoul.json')['items']:
        if any(s in (r[17] or []) for s in ST):
            dong.append([r[0], r[1], r[17], r[13], r[14], r[4], r[10], r[8], (r[15] or [None] * 5)])
    # D3 집회·공연 — 서초 교차로 700m 안
    def near(la, lo, rr=700): return any(m(la, lo, v[1], v[2]) <= rr for v in ints.values())
    RS = J('data/rally-seoul.json'); today = datetime.date.today()
    rally = [[x['d'], x.get('from'), x.get('to'), x['p'], x.get('n'), 1 if x.get('march') else 0, R5(x['lat']), R5(x['lon']), [R5(v) for v in x['dest']] if x.get('dest') else None, x.get('approx', 0), x.get('st')]
             for x in RS['items'] if 'lat' in x and near(x['lat'], x['lon'])]
    K = J('data/venue-events-kopis.json'); hz = (today + datetime.timedelta(days=21)).isoformat(); t0 = (today - datetime.timedelta(days=1)).isoformat()
    shows = []
    for v in K['venues']:
        if not v.get('lat') or not near(v['lat'], v['lon']): continue
        for s in v.get('shows') or []:
            if (s[7] or 0) >= 1000 and s[3] >= t0 and s[2] <= hz:
                shows.append([v['n'], R5(v['lat']), R5(v['lon']), s[0], s[2], s[3], s[4], s[5], s[6], s[7]])
    # D4 큰비
    F = J('data/flood-link-seocho.json'); S = {}
    for it in F['items']:
        s = S.setdefault(it[12], dict(n=it[1], ty=it[10], y=0, last=0, dep=0, ln=0, det=it[9], len=it[13], p=None))
        s['y'] = max(s['y'], it[14]); s['last'] = max(s['last'], it[6]); s['dep'] = max(s['dep'], it[7] or 0); s['ln'] = max(s['ln'], it[3] or 0)
        if s['p'] is None: s['p'] = (it[11][1] / 1e5, it[11][0] / 1e5)
    segs = sorted(S.items(), key=lambda x: (0 if x[1]['ty'] == '002' else 1, -x[1]['y'], -x[1]['dep'], x[0]))
    seg = []
    for sid, s in segs:
        if any(q[1] == s['n'] and q[3] == s['y'] and m(q[9], q[10], *s['p']) <= 150 for q in seg): continue   # 맞은편 방향 같은 구간
        seg.append([sid, s['n'], s['ty'], s['y'], s['last'], s['dep'], s['ln'], s['det'], s['len'], R5(s['p'][0]), R5(s['p'][1])])
        if len(seg) >= 60: break
    Dl = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto', 'flood-delay-seocho.json'), encoding='utf-8')); dly = {}   # 비공개(소유자 2026-10-23 「flood-delay 도 비공개로」) — 공개 판에는 모은 수만
    for sc in ('polA', 'polB'):
        dly[sc[-1]] = {'what': Dl['scenarios'][sc[-1]], 'stat': Dl['stat'][sc], 'trapN': sum(1 for x in Dl[sc] if x[3] < 0 and not x[7])}   # 교차로별 값(top·trap)은 관할 도달 공백이 드러나 공개하지 않는다
    doc = {'schema': 'tg-decide/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': 'ontology-core/data/core-seocho.json(TAAS 2016~2025 · 경찰 단속 카메라 · 어린이보호구역 · 다음 신호 · T-Book 범칙금 DB·판례) · data/hot10-seocho.json(TAAS 다발지) · dui-catch-st.json(경찰청 음주운전 적발 2020~2024) · dui-ref-seoul.json · rally-seoul.json(서울경찰청 오늘의 주요집회) · venue-events-kopis.json(KOPIS) · flood-link-seocho.json(서울시 침수흔적도 × ITS) · flood-delay-seocho.json',
           'note': ['결정 넷(D1 어디 설까 · D2 음주 단속 · D3 집회·행사 · D4 큰비)이 읽는 값 — 원자료 값 그대로 · 순위는 지도가 결정마다 잣대 하나로',
                    '사고 = 교차로 70m 안 100m 칸 합(근사 · 가까운 교차로끼리 겹침) · 시간대 넷 = 0~6 · 6~12 · 12~18 · 18~24',
                    '음주 적발 = 단속한 만큼 나온다(일어난 수가 아님) · 요일 0 = 일요일',
                    '집회 = 주요 집회만 · 신고값 · 받은 날까지 · 공연은 1,000석 이상 공연장 · 끝 시각 = 시작 + 공연시간',
                    '침수 흔적 = 그 길 30m 안 건물·필지가 잠긴 해(길 통제 기록 아님) · 출동 지연 = 막힘·신호 없이 센 견줌값'],
           'fields': 'int{INT: [이름, 위도, 경도, 행정동, 10년 사고, 시간대 넷, 밤 20~6, 보행자, 사망, 중상, 주 위반[[VIO, 건]], 100m 안 경찰 카메라 수, 300m 안 보호구역 시설 수, 가장 가까운 시설 m, 다음 신호[[INT, m]], 해마다 2016~]} · nb{사고 없는 이웃 INT: [이름, 위도, 경도]} · vio{VIO: [이름, [LAW]]} · law{LAW: [항목, 범칙금·벌점 글, 조문 글, [판례 번호]]}(T-Book 글 그대로) · hot[[다발지 이름, 위도, 경도, 갈래, 해]] · d2{years, grid{서: [요일 0=일][2시간 12]}, dong[[코드, 이름, [관할서], 밤 사고, 0~6시 사고, 주점, 호프 0~6시 결제, 호프 결제 중 21~06시 %, 백분위[주점, 호프 매출, 0~6 결제, 밤 사고, 0~6 사고]]]} · d3{collected, rally[[날, 부터, 까지, 장소 글, 신고 인원, 행진, 위도, 경도, 끝[위도, 경도], 근사, 관할]], shows[[공연장, 위도, 경도, 제목, 시작일, 끝일, 시각 글, 공연시간 분, 관, 좌석]]} · d4{seg[[구간, 길 이름, 도로 유형(002 지하차도), 잠긴 해 수, 마지막 해, 가장 깊은 m, 차로, 돌아가는 부담 초(-1 없음), 구간 m, 위도, 경도]], delay{A|B: {what, stat, trapN}}}(교차로별 값은 비공개 — 07_API키/out/onto/flood-delay-seocho.json)',
           'int': ints, 'nb': nb, 'vio': vio, 'law': law, 'hot': hot,
           'd2': {'years': [yrs[0], yrs[-1]], 'grid': grid, 'dong': dong},
           'd3': {'collected': RS['collected'], 'kopis': K['made'], 'rally': rally, 'shows': shows},
           'd4': {'seg': seg, 'delay': dly}}
    p = os.path.join(D, 'decide-seocho.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('decide-seocho.json 교차로', len(ints), '· 집회', len(rally), '· 공연', len(shows), '· 침수 구간', len(seg), '·', os.path.getsize(p) // 1024, 'KB')


if __name__ == '__main__':
    main()
