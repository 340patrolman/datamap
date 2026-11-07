# -*- coding: utf-8 -*-
# 「이 자리 한 줄 진단」 굽기(2026-11-07 · 소유자 「권고대로 진행」 — 시안 세 곳(서초역·반포쇼핑타운·이수역) 꼴로 사고 교차로 전부 · 「계속 진행」 → 여섯 구)
#   있는 사실만 묶는다 — 원인 단정 없음 · 문턱·점수 없음 · 숫자는 모두 원자료에서 센 값
#   원자료: ontology-core/data/core-six/<구>.json(build.py · TAAS 10년 교차로 70m 안 100m 칸 · 주 위반(칸마다 하나) · 경찰 카메라 100m(보유) · 보호구역 300m(가까움) · 들어오는길 → 길 이름·차로 · VIO 근거 LAW = T-Book 범칙금 DB 이름 맞대기)
#   순위 = 그 구 안 사고 건수 순위(같은 건수는 같은 순위) — 교통량을 반영하지 않는다(화면에 밝힌다)
#   T-Book 법규 단추 = 주 위반이 T-Book 범칙금 항목과 이어질 때만 · 안전운전불이행·기타는 잇지 않는다
#   py -3.12 -X utf8 tools/onto/brief-bake.py  → data/int-brief.json
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUN = {'11650': '서초구', '11680': '강남구', '11710': '송파구', '11590': '동작구', '11620': '관악구', '11170': '용산구'}
DIRS = {'북쪽': 0, '북동쪽': 1, '동쪽': 2, '남동쪽': 3, '남쪽': 4, '남서쪽': 5, '서쪽': 6, '북서쪽': 7}
out, gus, made = {}, {}, ''
for f in sorted(glob.glob(os.path.join(ROOT, 'ontology-core', 'data', 'core-six', '1*.json'))):
    C = json.load(open(f, encoding='utf-8')); gu = C.get('gu') or os.path.basename(f)[:5]; made = max(made, str(C.get('made', '')))
    O = {o['id']: o for o in C['objects']}; E = collections.defaultdict(list)
    for a, r, b, p in C['edges']: E[(a, r)].append((b, p))
    rows = {}
    for i, o in O.items():
        if o['t'] != 'INT' or not E.get((i, '발생')): continue
        if str(o.get('dong') or '')[:5] != gu: continue   # 구 파일에는 경계 너머 이웃 구 교차로도 들어 있다 — 교차로가 든 행정동의 구에서만 센다
        A = O.get(E[(i, '발생')][0][0])
        if not A or sum(A['years']) <= 0: continue
        mv = collections.Counter()
        for v, p in E.get((A['id'], '주요원인'), []): mv[v] += p.get('n', 0)
        vio = []
        for v, n in mv.most_common(2):   # 칸마다 주 위반 하나 — 구 경계 교차로처럼 칸이 둘이면 둘째가 생긴다
            law = [O[b]['title'] for b, _ in E.get((v, '근거'), []) if b in O and O[b].get('title')]
            vio.append([O[v]['nm'] if v in O else v, n, law[0] if law else ''])
        rd = []
        for b, _ in E.get((i, '들어오는길'), []):
            x = O.get(b)
            if not x or not x.get('rds'): continue
            r0 = x['rds'][0]; rd.append([(x.get('frm') or '').replace('에서 오는 길', '').strip(), r0[0], r0[2]])
        rd.sort(key=lambda r: DIRS.get(r[0], 9))
        y = A['years']
        rows[i.replace('INT-', '')] = [0, sum(y), A['dead'], A['serious'], A['ped'], A['tod'], vio, sum(y[:3]), sum(y[-3:]), len(E.get((i, '보유'), [])), len(E.get((i, '가까움'), [])), rd, gu]
    acc = [r[1] for r in rows.values()]
    for r in rows.values(): r[0] = 1 + sum(1 for a in acc if a > r[1])
    for k, r in rows.items():
        out[k] = r
    gus[gu] = [GUN.get(gu, gu), len(rows)]
json.dump({'schema': 'tg-int-brief/2', 'made': made[:16], 'gus': gus, 'y0': 2016, 'y1': 2025,
           'fields': 'gus{구 코드: [이름, 사고 교차로 수]} · int{T-GIS 코드: [그 구 안 사고 건수 순위, 10년 사고, 사망, 중상, 보행자, 시간대 넷(0~6·6~12·12~18·18~24), 주 위반[[이름, 건, T-Book 항목 또는 빈칸]], 앞 3년(2016~18), 뒤 3년(2023~25), 100m 안 경찰 카메라, 300m 안 보호구역 시설, 들어오는 길[[쪽, 길 이름, 차로]], 구 코드]}',
           'source': 'TAAS 교통사고 10년(2016~2025 · 교차로 70m 안 100m 칸) · T-GIS 교차로 · ITS 링크(들어오는 길·차로) · 경찰 카메라 · 보호구역 — ontology-core/data/core-six 값 그대로',
           'int': out}, open(os.path.join(ROOT, 'data', 'int-brief.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(' · '.join('%s %d' % (v[0], v[1]) for v in gus.values()), '· 모두', len(out), '· 법규 잇기', sum(1 for r in out.values() if r[6] and r[6][0][2]), '· 길 있음', sum(1 for r in out.values() if r[11]))
