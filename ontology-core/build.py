# -*- coding: utf-8 -*-
"""교통 온톨로지 코어 v1 — 서초구 객체·링크 한 장(ontology-core/data/core-seocho.json)을 굽는다.
  모든 값은 이미 있는 공개 자료 파일에서 다시 센다(지어낸 값 없음). 링크마다 출처 파일과 등급(A~E).
  원천:
    INT·PLC  = data/onto-int.json(T-GIS 교차로 · C-ITS 번호 · 250m 칸 · 행정동 10자리 → 앞 8자리)
               PLC 사람 = data/r/<서울 구>/live250.json(서울 생활인구 내국인 250m 격자 · 2026-09-07~13 한 주 · 평일·주말 0~23시 평균 · 연령 구성) — 칸 번호가 열쇠 · 값 그대로(2026-10-23)
    EVT      = 사건(2026-10-23 엮임 지도 둘째) = data/onto-events.json(tools/onto/evt-bake.py — 집회·공연·돌발 · 침수는 해마다) → 교차로 「근처」(집회 300m·공연 500m·돌발 150m · 근사 C)
               침수는 data/season-seocho.json 흔적 점이 교차로 100m 안이면 「흔적」(그 해 흔적 수·가장 깊은 침수심) · 교차로에 안 닿는 사건은 싣지 않는다
    APR·RD   = 접근로·도로 구간(2026-10-23 엮임 지도 셋째) = data/sig-approach-seocho.json(신호 교차로에 들어오는 쪽마다 ITS 링크) → 교차로 「들어오는길」 접근로 「이룸」 도로 구간(ITS 링크 · 등급 B)
               도로 구간 값 = nav-seocho(길 이름·길이·제한속도·등급·차로) · spd-normal-seocho(월~목 8·18·3시 평소 속도 · 잠정 표시) · flood-link-seocho(침수 흔적 해 수·마지막 해·침수심·돌아가는 부담 초)
               도로 구간 → TAAS 100m 사고 칸 「사고칸」(ACL · 칸 가운데가 구간 선 50m 안 · 가장 가까운 구간 하나에만 · 칸은 방향이 없어 맞은편 차로 사고도 섞임 · 근사 C · 2026-10-23)
               도로 구간 → 250m 칸 「지남」(rd-cell-seocho) · 범위는 서초구 + 경계 밖 2km 뿐(여섯 구 코어에서도 그 밖 교차로는 접근로가 없다)
    도착     = 교차로 「도착」 지구대·파출소(data/onto-reach-<area>.json · tools/onto/reach-bake.py · s0 제한속도 · s8·s18 평일 8·18시 평소 속도 + eta-cal 배율 · 다섯 곳 · 견주는 값 C)
    STA·PBX  = 관할 경찰서·지구대·파출소(2026-10-23) — 교차로 「관할」 경찰서(jur-seocho 현장 기준 경계 → 밖이면 police.json 별표2 × 행정동 · 나눠 맡는 동은 둘 다 C · T-GIS 관할 코드와 맞는지 tg)
               지구대·파출소 「소속」 경찰서(경찰청 주소 현황 · A) · 교차로 「가까운지구대」(그 서의 지구대·파출소 가운데 가장 가까운 곳 · 관할 경계 비공개 — 근사 C · d m)
    DNG      = 교차로가 든 행정동(onto-int 행정동 코드 · 2026-10-23 엮임 지도 첫째) — 값은 그 동을 열쇠로 가진 파일에서 그대로:
               house-dong(세대·1인 세대) · mig-dong(주민) · foreign-dong(외국인주민) · econ-dong(국민연금 가입 사업장·가입자) · dui-ref-seoul(주점 점포·호프 0~6시 결제) · police.json(별표2 관할서)
    인접      = data/sig-net-seocho.json(신호 교차로 사이 길 · C-ITS 번호로 INT 에 이음)
    ACC·VIO  = data/taas10-seocho.json(TAAS 2016~2025 · 100m 칸 · 주 법규위반 코드 dic.v) — 교차로에서 70m 안 칸을 묶음(jct-bake 와 같은 반지름 · 근사 C)
    CAM·ATT  = data/gargo-alerts-seoul.json(경찰 관리 · 제한속도 있는 카메라 100m 안 · 어린이보호구역 시설 300m 안 · 근사 C)
    ACT·REC  = data/sig-ksc-seocho.json hist(교통과 출력물 — 교통과 출력물 5곳 · 소유자 공개 결정 2026-10-10 · 10-18 저녁 다시 확인 · 이력 글 그대로)
    LAW·PREC = ontology-core/src/tbook-law.json(T-Book 범칙금 DB · 원문 대조 판례 — tools/tbook-extract.py 가 읽기만 해서 꺼냄)
    RULE·FK  = data/onto-rules.json(틀리면 사고 나는 규칙 · 소유자 현장 판단 말 그대로 — 수집기 쪽 세션의 tools/onto/rules-bake.py 가 정본 · 여기서는 값을 고치지 않고 객체·링크로만 옮긴다) — FK → 뒷받침 → RULE(등급 B · 소유자 현장)
  VIO → LAW 는 이름 맞대기 표(아래 VIO_LAW · 등급 C · 확인 필요) · LAW → PREC 은 조문 번호가 같을 때만(교특법 §3 은 12대 중과실 공통이라 빼고)(범칙금 DB meta 「도교법§5」 ↔ 판결문 참조조문 「도로교통법 제5조」 · 등급 A · 「구 ○○법」 이면 C)
  쓰기: py -3.12 -X utf8 ontology-core/build.py            → data/core-seocho.json(서초)
        py -3.12 -X utf8 ontology-core/build.py --area six → data/core-six.json(서초·강남·송파·동작·관악·용산 — 네비 가르고 길 묶음 범위 · 작업지시서 Phase 4)
        여섯 구의 사고 칸 = 서초 data/taas10-seocho.json + 나머지 data/r/<구>/taas10.json(권역 저장소 datamap-data-seoul 에 올린 것과 같은 로컬 빌드 출력 · 같은 꼴 tg-taas10/1)
        여섯 구에서도 인접(sig-net)·조치(교통과 출력물)는 서초에만 있다
"""
import json, os, re, math, hashlib, datetime, collections, sys
CORE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(CORE); D = os.path.join(ROOT, 'data'); PRIV = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto')
def J(p): return json.load(open(p, encoding='utf-8'))
def m(la1, lo1, la2, lo2): return math.hypot((lo1 - lo2) * 88400.0, (la1 - la2) * 111000.0)
GU = '11650'
AREAS = {'seocho': (['11650'], '서울특별시 서초구(11650)', 'core-seocho.json'),
         'six': (['11650', '11680', '11710', '11590', '11620', '11170'], '서울특별시 서초·강남·송파·동작·관악·용산구(11650·11680·11710·11590·11620·11170)', 'core-six.json')}
AREA = sys.argv[sys.argv.index('--area') + 1] if '--area' in sys.argv else 'seocho'
GUS, AREA_NM, OUTF = AREAS[AREA]
# 위반유형 → T-Book 범칙금 DB 항목(제목 그대로) — 이름 맞대기(등급 C). 「06 안전운전불이행」·「기타」는 DB 에 같은 항목이 없어 잇지 않는다
VIO_LAW = {'02': ['① 신호위반·안전표지 위반'], '01': ['② 중앙선 침범'], '05': ['③ 제한속도 20km/h 초과', '과속 (일반도로)', '스쿨존 과속'],
           '03': ['안전거리 미확보'], '07': ['교차로 통행방법 위반 (꼬리물기)'], '08': ['⑥ 횡단보도 보행자보호의무 위반']}
ABBR = {'도교법': '도로교통법', '교특법': '교통사고처리 특례법', '특가법': '특정범죄 가중처벌 등에 관한 법률', '자관법': '자동차관리법'}
def arts_meta(meta):   # 「도교법§13③,§62 · 교특법§3②1 · 도교법§21~23」 → [[법, '13'], [법, '62'], …]
    out = []; law = None
    for tok in re.finditer(r'(도교법|교특법|특가법|자관법|형법)|§\s*(\d+)(의\d+)?(?:\s*~\s*(\d+))?', meta):
        if tok.group(1): law = ABBR.get(tok.group(1), tok.group(1)); continue
        if not law: continue
        a = int(tok.group(2)); b = int(tok.group(4)) if tok.group(4) else a; sub = tok.group(3) or ''
        for n in range(a, b + 1): out.append([law, str(n) + (sub if n == a else '')])
    return [list(x) for x in dict.fromkeys(tuple(x) for x in out)]
def arts_jo(jo):   # 판결문 참조조문 「도로교통법 제44조 제1항, 제4항, 제148조의2 제3항 …」 → [[법, '44', 구?], …]
    out = []; law = None; old = False
    for tok in re.finditer(r'(구\s+)?(도로교통법|교통사고처리\s*특례법|특정범죄\s*가중처벌\s*등에\s*관한\s*법률|자동차관리법|형사소송법|형법)(\s*시행규칙|\s*시행령)?|제(\d+)조(의\d+)?', jo):
        if tok.group(2):
            nm = re.sub(r'\s+', ' ', tok.group(2)).replace('교통사고처리특례법', '교통사고처리 특례법')
            law = None if tok.group(3) else nm; old = bool(tok.group(1)); continue
        if law: out.append([law, tok.group(4) + (tok.group(5) or ''), old])
    return out
def ym_of(t):
    for rx in (r'(\d{4})\.\s?(\d{1,2})', r'(\d{4})(\d{2})\d{2}\)', r'(\d{4})년\s?(\d{1,2})월', r'(\d{4})년'):
        g = re.search(rx, t)
        if g: return '%s-%02d' % (g.group(1), int(g.group(2))) if g.lastindex >= 2 else g.group(1)
    return None
EVT_R = {'집회': 300, '공연': 500, '돌발': 150}   # 사건 → 교차로 「근처」 반지름 m(근사 C) · 침수는 흔적 점 100m 안
def evt_build(O, obj, edge, INTs):
    ev = J(os.path.join(D, 'onto-events.json'))['items']
    G = collections.defaultdict(list)
    for it in INTs: G[(int(it['lat'] * 200), int(it['lon'] * 200))].append(it)   # 0.005° 칸(약 550×440m) — 둘레만 빨리 찾기
    def near(la, lo, r):
        a, b = int(la * 200), int(lo * 200); out = []
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                for it in G.get((a + i, b + j), ()):
                    d = m(la, lo, it['lat'], it['lon'])
                    if d <= r: out.append((it['id'], round(d)))
        return out
    keep = ('kind', 'sub', 'src', 'd0', 'd1', 'nm', 'lat', 'lon', 'n', 'march', 'approx', 'st', 'hall', 'times', 'dur', 'road', 'first', 'last', 'dep')
    for e in ev:
        if e['kind'] == '침수': continue
        hit = dict(near(e['lat'], e['lon'], EVT_R[e['kind']]))
        if e.get('dest'):
            for i, d in near(e['dest'][0], e['dest'][1], EVT_R['집회']): hit.setdefault(i, d)
        if not hit: continue
        obj(e['id'], 'EVT', **{k: e.get(k) for k in keep})
        for i, d in sorted(hit.items()): edge(e['id'], '근처', i, 'C', 'onto-events.json(%s · %dm 안%s)' % (e['src'], EVT_R[e['kind']], ' · 행진 끝 포함' if e.get('dest') else ''), d=d)
    S = J(os.path.join(D, 'season-seocho.json')); fl = {e['id']: e for e in ev if e['kind'] == '침수'}; acc = collections.defaultdict(lambda: [0, 0.0])
    for t in S['traces']:
        lo = 127.01 + t[0] / 88800.0; la = 37.49 - t[1] / 111000.0
        for i, d in near(la, lo, 100):
            a = acc[('EVT-FLD-%d' % t[2], i)]; a[0] += t[3]; a[1] = max(a[1], t[4] or 0)
    for (fid, i), (n, dep) in sorted(acc.items()):
        if fid not in fl: continue
        if fid not in O: obj(fid, 'EVT', **{k: fl[fid].get(k) for k in keep})
        edge(fid, '흔적', i, 'C', 'season-seocho.json(서울시 침수흔적도 · 교차로 100m 안 흔적 점)', n=n, dep=round(dep, 2))
DIR_KO = {'nt': '북쪽', 'ne': '북동쪽', 'et': '동쪽', 'se': '남동쪽', 'st': '남쪽', 'sw': '남서쪽', 'wt': '서쪽', 'nw': '북서쪽'}
SPD_K = ('0-8', '0-18', '0-3')   # 평소 속도는 월~목 8시·18시·3시(막힘 없는 때 견줌)만 싣는다 — 나머지 칸은 spd-normal-seocho.json 그대로 본다
def rd_build(obj, edge, by_cits):
    ap = J(os.path.join(D, 'sig-approach-seocho.json'))['spots']; nv = {l[0]: l for l in J(os.path.join(D, 'nav-seocho.json'))['links']}
    sn = J(os.path.join(D, 'spd-normal-seocho.json'))['links']; fl = {x[0]: x for x in J(os.path.join(D, 'flood-link-seocho.json'))['items']}
    rc = J(os.path.join(D, 'rd-cell-seocho.json')); cells = rc['cells']
    for no in sorted(ap, key=lambda k: int(k)):
        it = by_cits.get(no)
        if not it: continue
        for dr in sorted(ap[no]['in'], key=lambda k: list(DIR_KO).index(k)):
            roads = ap[no]['in'][dr]; a = 'APR-%s-%s' % (no, dr)
            obj(a, 'APR', no=no, dir=dr, frm=DIR_KO[dr] + '에서 오는 길', nm=' · '.join(dict.fromkeys(r[0] for r in roads)), rds=[r[:4] for r in roads])
            edge(it, '들어오는길', a, 'B', 'sig-approach-seocho.json(ITS 링크 방위로 들어오는 쪽을 가름 — 대각 교차로는 45° 어긋날 수 있다)')
            for ri, r in enumerate(roads):
                for k, (lid, ln) in enumerate(r[4]):
                    rid = 'RD-' + lid
                    if rid not in O_RD:
                        L = nv.get(lid); s = sn.get(lid) or {}; f = fl.get(lid)
                        O_RD.add(rid)
                        obj(rid, 'RD', link=lid, nm=L[7] if L else r[0], len=L[3] if L else ln, lim=(L[4] or None) if L else None, gr=L[5] if L else None, ln=L[6] if L else None,
                            sp={h: [s[h][0], s[h][1], s[h][3], s[h][4]] for h in SPD_K if h in s} or None,
                            fy=f[5] if f else None, fl=f[6] if f else None, fd=f[7] if f else None, dt=f[9] if f else None)
                        for ci in rc['links'].get(lid, []):
                            edge(rid, '지남', obj('PLC-' + cells[ci], 'PLC'), 'B', 'rd-cell-seocho.json(링크 선을 25m 마다 읽어 250m 칸을 셈)')
                    edge(a, '이룸', rid, 'B', 'sig-approach-seocho.json(교차로에서 거슬러 모은 ITS 링크)', r=ri, k=k)
O_RD = set()
ACL_R = 50   # 사고 칸(100m) 가운데가 도로 구간 선에서 50m 안이면 그 칸이 그 길에 걸친다고 본다 — 한 칸은 가장 가까운 구간 하나에만(겹쳐 세지 않게)
def acl_build(obj, edge, rds, nv, ta):
    """도로 구간(접근로를 이루는 ITS 링크) → 그 길에 걸친 TAAS 100m 사고 칸 「사고칸」(근사 C). 칸은 방향이 없어 맞은편 차로 사고도 섞인다."""
    G = collections.defaultdict(list)
    for rid in rds:
        L = nv.get(rid[3:])
        if not L: continue
        g = L[9]; x, y = g[0], g[1]; pts = [(x / 1e5, y / 1e5)]
        for k in range(2, len(g), 2): x += g[k]; y += g[k + 1]; pts.append((x / 1e5, y / 1e5))
        for a, b in zip(pts, pts[1:]):
            for i in range(int(min(a[1], b[1]) * 500) - 1, int(max(a[1], b[1]) * 500) + 2):
                for j in range(int(min(a[0], b[0]) * 500) - 1, int(max(a[0], b[0]) * 500) + 2): G[(i, j)].append((rid, a, b))
    def seg(la, lo, a, b):   # 점에서 선분까지 m(평면 근사 — m() 와 같은 눈금)
        ax, ay, bx, by = (a[0] - lo) * 88400.0, (a[1] - la) * 111000.0, (b[0] - lo) * 88400.0, (b[1] - la) * 111000.0
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy; t = 0 if not L2 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L2))
        return math.hypot(ax + t * dx, ay + t * dy)
    dv = ta['dic']['v']; n = 0; M = {}
    for c in ta['cells']:   # 여섯 구는 구 경계 칸이 두 구 파일에 같은 자리로 들어 있다 — 한 칸으로 더한다(주 위반은 건수가 큰 쪽 · 같은 코드면 더함)
        k = '%.6f,%.6f' % (c[0], c[1]); o = M.get(k)
        if o is None: M[k] = list(c); continue
        for i in range(2, 23): o[i] += c[i]
        if o[23] == c[23]: o[24] += c[24]
        elif c[24] > o[24]: o[23], o[24], o[25] = c[23], c[24], c[25]
    for c in M.values():
        best = None
        for rid, a, b in G.get((int(c[0] * 500), int(c[1] * 500)), ()):
            d = seg(c[0], c[1], a, b)
            if d <= ACL_R and (best is None or d < best[1] or (d == best[1] and rid < best[0])): best = (rid, d)
        if not best: continue
        cid = 'ACL-%.6f,%.6f' % (c[0], c[1])
        obj(cid, 'ACL', lat=c[0], lon=c[1], y0=2016, years=c[2:12], dead=c[12], serious=c[13], ped=c[14], night=c[18], tod=c[19:23], mv=c[23], mvnm=dv.get(c[23]), mvn=c[24], typ=c[25])
        edge(best[0], '사고칸', cid, 'C', 'taas10(100m 사고 칸 가운데가 구간 선 %dm 안 · 가장 가까운 구간 하나 · 방향 섞임)' % ACL_R, d=round(best[1])); n += 1
    return n
# 출처마다 「언제의 세계인가」(2026-10-23 · 다른 AI 의견 중 받아들인 것 — 기준일 없는 값은 쓰지 않는다) — 파일 안 source·note 글에 적힌 기준을 그대로 옮긴 표 · 새 출처를 더하면 여기도 한 줄
ASOF = {
    'live250': '서울 생활인구 250m 격자 2026-09-07~13 한 주 평균',
    'onto-int.json': 'T-GIS 교차로(2026-10-11 받음) · C-ITS 번호 · 행정동 경계 2026-07',
    'sig-net-seocho.json': 'ITS 표준노드링크 2026-09-14판 · 신호 자료는 번호로 따로',
    'taas10-seocho.json': 'TAAS 사고 2016~2025(2026-10-04 받음)',
    'gargo-alerts-seoul.json': '무인단속카메라·어린이보호구역 표준데이터(2026-10-12~14 받음)',
    'sig-ksc-seocho.json': '서초서 교통과 출력물 5곳(2026-09-11 판독 · 출력물마다 시행일 다름)',
    'onto-rules.json': '규칙 장부(2026-10-18)',
    'house-dong.json': '주민등록 세대 2026-08-31',
    'mig-dong.json': '행정안전부 인구이동(2026-10-09 받음 · 최근 12달)',
    'foreign-dong.json': '외국인주민 현황 2024-11-01',
    'econ-dong.json': '국민연금 가입 사업장 2026-08',
    'dui-ref-seoul.json': '상가정보·상권 추정매출·TAAS 2016~2025(2026-10-15 구움)',
    'police.json': '직제 시행규칙 별표2 2026-08-31 시행 · 지구대·파출소 주소 2025-12-31 · 대표번호 2026-09-09',
    'onto-events.json': '집회 지난 90일 · 공연 앞 90일~뒤 21일 · 돌발 2026-10-15~ 받은 기록 · 침수 2010~2025(굽는 날 기준)',
    'season-seocho.json': '침수흔적도 2010~2025(2015·2021 없음)',
    'sig-approach-seocho.json': 'ITS 표준노드링크 2026-09-14판',
    'nav-seocho.json': 'ITS 표준노드링크 2026-09-14판',
    'spd-normal-seocho.json': 'ITS 실시간 소통 2026-10-11~ 쌓음(요일 갈래 3날 미만은 잠정)',
    'flood-link-seocho.json': '침수흔적도 2010~2025 × ITS 2026-09-14판',
    'rd-cell-seocho.json': 'ITS 표준노드링크 2026-09-14판',
    'jur-seocho.json': '별표2 2026-08-31 시행 · 반포 현장 기준 2026-10-04',
    'tgis-pe.json': 'T-GIS 관할 코드 × 별표2(2026-10-18 맞춤)',
}
def asof_of(s): return ASOF.get(s) or (ASOF['live250'] if s.endswith('/live250.json') else ASOF['taas10-seocho.json'].replace('(2026-10-04 받음)', '(권역 저장소 판)') if s.endswith('/taas10.json') else None)
def plc_people(O):
    """250m 칸(PLC)에 서울 생활인구(내국인) 250m 격자 값을 그대로 붙인다(속성 — 칸 번호가 열쇠 · 등급 A).
       wd/we = 평일·주말 하루 평균 0~23시(명) · ad/an = 평일 낮(11~14시)·밤(0~4시) 연령 8칸 % — data/r/<서울 구>/live250.json(tools/region/live250-bake.py)"""
    used = []; L = {}
    for g in sorted(os.listdir(os.path.join(D, 'r'))):
        f = 'r/%s/live250.json' % g
        if not g.startswith('11') or not os.path.exists(os.path.join(D, f)): continue
        cs = J(os.path.join(D, f))['cells']; hit = False
        for k, v in cs.items():
            o = O.get('PLC-' + k)
            if o is None: continue
            p = L.setdefault(k, {'wd': [0] * 24, 'we': [0] * 24, 'ad': v['ad'], 'an': v['an'], 'sd': 0}); hit = True
            p['wd'] = [a + b for a, b in zip(p['wd'], v['wd'])]; p['we'] = [a + b for a, b in zip(p['we'], v['we'])]
            s_ = sum(v['wd'])
            if s_ > p['sd']: p['ad'], p['an'], p['sd'] = v['ad'], v['an'], s_   # 칸이 두 구 파일에 나뉘어 있으면 사람 수는 더하고 연령 구성은 많은 쪽
        if hit: used.append(f)
    for k, p in L.items(): O['PLC-' + k].update(wd=p['wd'], we=p['we'], ad=p['ad'], an=p['an'])
    return used
def pip(lo, la, ring):   # 점이 고리(경도·위도) 안인가 — 짝홀 셈
    c = False; n = len(ring)
    for i in range(n):
        x1, y1 = ring[i][0], ring[i][1]; x2, y2 = ring[i - 1][0], ring[i - 1][1]
        if (y1 > la) != (y2 > la) and lo < (x2 - x1) * (la - y1) / (y2 - y1) + x1: c = not c
    return c
def sta_build(obj, edge, INTs):
    """관할 경찰서(STA)·지구대·파출소(PBX). 교차로 → 관할서 = jur-seocho 현장 기준 경계(서초·방배와 이웃 서 · 반포4동은 반포대로) 안이면 그 서,
       밖이면 police.json 별표2 × 행정동(두 서가 나눠 맡는 동은 둘 다 · 「~」 뒤는 일부 번지). 지구대·파출소 관할 경계는 공개 자료가 없어
       그 서의 지구대·파출소 가운데 가장 가까운 곳(근사 C · 지도 pbNear·학교 school-police 와 같은 셈). T-GIS 교차로 관할 코드(tgis-pe 이름 맞춤)와 맞는지 tg 로 적는다."""
    P = J(os.path.join(D, 'police.json')); Z = J(os.path.join(D, 'jur-seocho.json'))['zones']; PE = J(os.path.join(D, 'tgis-pe.json'))['pe']
    byname = {s[1]: s for s in P['stations']}; boxes = collections.defaultdict(list)
    for k, b in enumerate(P['pbox']): boxes[b[6]].append((k, b))
    def sta(no):
        s = P['stations'][no] if P['stations'][no][0] == no else next(x for x in P['stations'] if x[0] == no)
        return obj('STA-%d' % no, 'STA', no=no, nm=s[1], tel=s[4] or None, sido=s[5] or None, lat=s[2], lon=s[3])
    def pbx(k, b):
        return obj('PBX-%d' % k, 'PBX', nm=b[0] + ('지구대' if b[1] == 0 else '파출소'), kind='지구대' if b[1] == 0 else '파출소', st=b[6], lat=b[3], lon=b[4], addr=b[5] or None, osm=1 if len(b) > 7 and b[7] else None)
    seen = set()
    for it in INTs:
        hit = [z for z in Z if any(pip(it['lon'], it['lat'], r) for r in z['rings'])]
        if len(hit) == 1 and hit[0]['name'] in byname:
            js = [(byname[hit[0]['name']][0], 'B', '현장 기준 경계(jur-seocho · 별표2 행정동 + 반포 현장 판단)', None)]
        else:
            lab = P['dong'].get(it.get('dong') or '')
            if lab is None: continue
            t = P['labels'][lab]
            if '~' in t: a, b = t.split('~'); js = [(int(a), 'B', '별표2 × 행정동(주 관서)', None), (int(b), 'C', '별표2 × 행정동(일부 번지만)', 'part')]
            else:
                ns = [int(x) for x in t.split(',')]
                js = [(n, 'B' if len(ns) == 1 else 'C', '별표2 × 행정동' + ('' if len(ns) == 1 else '(두 서가 나눠 맡는 동 — 어느 쪽인지 번지로만 갈림)'), None if len(ns) == 1 else 'shared') for n in ns]
        pe = PE.get(str(it.get('st'))); tgn = pe[0] if pe and pe[4] else None
        if tgn and len(js) == 1 and js[0][3] is None and tgn != O_STA_NM(js[0][0], P) and tgn in byname:   # 경계와 T-GIS 관할 코드가 다른 서 — 둘 다 적고 C(소유자 확인 대기)
            js = [(js[0][0], 'C', js[0][2] + ' — T-GIS 관할 코드와 다름', 'disagree'), (byname[tgn][0], 'C', 'T-GIS 교차로 관할 코드(tgis-pe 이름 맞춤) — 경계와 다름', 'tgis')]
        for n, g, how, kind in js:
            s = sta(n); tg = None if tgn is None else (1 if tgn == O_STA_NM(n, P) else 0)
            edge(it['id'], '관할', s, g, 'police.json·jur-seocho.json·tgis-pe.json(' + how + ')', kind=kind, tg=tg)
            if n not in seen:
                seen.add(n)
                for k, b in boxes.get(n, []): edge(pbx(k, b), '소속', s, 'A', '경찰청 전국 지구대·파출소 주소 현황(police.json pbox)')
        n0 = js[0][0]; bs = boxes.get(n0, [])
        if bs:
            k, b = min(bs, key=lambda kb: (m(it['lat'], it['lon'], kb[1][3], kb[1][4]), kb[0]))
            edge(it['id'], '가까운지구대', 'PBX-%d' % k, 'C', '그 관할서의 지구대·파출소 가운데 가장 가까운 곳(관할 경계 비공개 — 근사)', d=round(m(it['lat'], it['lon'], b[3], b[4])))
    # 도착(2026-10-23 엮임 지도 일곱째) — data/onto-reach-<area>.json(tools/onto/reach-bake.py): 교차로마다 s0 가 짧은 지구대·파출소 다섯 곳 · 근사 C
    rp = os.path.join(PRIV, 'onto-reach-%s.json' % AREA)   # 비공개(소유자 2026-10-23 「도착 시간 자료는 공개 저장소에서 빼고 비공개 쪽에만」) — 없으면 도착 없이 굽는다
    RC = J(rp)['items'] if os.path.exists(rp) else {}
    for it in INTs:
        for r, row in enumerate(RC.get(it['id'][4:], [])):
            k, s0, s8, s18, c8, c18 = row; b = P['pbox'][k]
            if b[6] not in seen:
                seen.add(b[6]); s_ = sta(b[6])
                for k2, b2 in boxes.get(b[6], []): edge(pbx(k2, b2), '소속', s_, 'A', '경찰청 전국 지구대·파출소 주소 현황(police.json pbox)')
            edge(it['id'], '도착', 'PBX-%d' % k, 'C', '07_API키/out/onto/onto-reach-%s.json(비공개 · ITS 길 · 제한속도 / 평소 속도 + eta-cal 배율 · 견주는 값 — 실제 출동 시간 아님)' % AREA, r=r, s0=s0, s8=s8, s18=s18, c8=c8, c18=c18)
def O_STA_NM(n, P): return next(x[1] for x in P['stations'] if x[0] == n)
def dng_build(O, obj, rows):
    hd = J(os.path.join(D, 'house-dong.json'))['dong']; mg = J(os.path.join(D, 'mig-dong.json'))['dong']; fg = J(os.path.join(D, 'foreign-dong.json'))['dong']
    ec = J(os.path.join(D, 'econ-dong.json'))['dong']; dr = {x[0]: x for x in J(os.path.join(D, 'dui-ref-seoul.json'))['items']}
    pl = J(os.path.join(D, 'police.json')); stn = {str(s[0]): s[1] for s in pl['stations']}
    for r in rows:
        c = (r[7] or '')[:8]
        if not c or ('DNG-' + c) in O: continue
        h = hd.get(c) or {}; d = dr.get(c); lab = pl['dong'].get(c)
        obj('DNG-' + c, 'DNG', code=c, nm=r[8], gu=r[6],
            hh=(h.get('hh') or [None])[0], one=(h.get('hh') or [None, None])[1], res=(mg.get(c) or [None, None, None])[2],
            fgn=(fg.get(c) or {}).get('t'), biz=(ec.get(c) or [None])[0], wk=(ec.get(c) or [None, None])[1],
            bars=d[4] if d else None, hof06=d[10] if d else None,
            jur=jur_names(pl['labels'][lab], stn) if lab is not None else None)
def jur_names(lab, stn):   # police.json 관서 묶음 — 「23,27」 = 두 서가 나눠 맡음 · 「27~23」 = 앞이 주 관서 · 뒤는 일부 번지만
    if '~' in lab:
        a, b = lab.split('~', 1); return [stn.get(a)] + [stn.get(x) + '(일부 번지)' for x in b.split(',') if stn.get(x)]
    return [stn.get(x) for x in lab.split(',')]
def main():
    O = {}; E = []
    def obj(i, t, **p): O[i] = dict(id=i, t=t, **{k: v for k, v in p.items() if v is not None}); return i
    def edge(a, rel, b, grade, src, **p): E.append([a, rel, b, dict(g=grade, src=src, **p)])
    oi = J(os.path.join(D, 'onto-int.json')); rows = [r for r in oi['items'] if r[6] in GUS]
    by_cits = {}
    for r in rows:
        i = obj('INT-%s' % r[0], 'INT', nm=r[1], lat=r[2], lon=r[3], cits=r[4] or 0, st=r[5], dong=(r[7] or '')[:8], dongnm=r[8], has=r[11])
        if r[4]: by_cits[str(r[4])] = i
        if r[9]: edge(i, '들어감', obj('PLC-%s' % r[9], 'PLC'), 'A', 'onto-int.json')
        if r[7]: edge(i, '속함', 'DNG-%s' % r[7][:8], 'B', 'onto-int.json(행정동 코드 · 교차로 자리가 든 행정동 경계)')
    dng_build(O, obj, rows)
    net = J(os.path.join(D, 'sig-net-seocho.json'))
    for l in net['links']:
        a, b = by_cits.get(str(l[0])), by_cits.get(str(l[1]))
        if a and b and a != b: edge(a, '인접', b, 'B', 'sig-net-seocho.json', m=l[2], s=l[3])
    ta = J(os.path.join(D, 'taas10-seocho.json')); dv = ta['dic']['v']; R = 70
    taf = ['taas10-seocho.json'] + ['r/%s/taas10.json' % g for g in GUS if g != '11650']
    for f in taf[1:]:
        tb = J(os.path.join(D, f))
        if tb.get('schema') != ta.get('schema') or tb['dic']['v'] != dv: raise SystemExit('사고 칸 꼴·위반 사전이 서초와 다르다: ' + f)
        ta = dict(ta, cells=ta['cells'] + tb['cells'])
    CG = collections.defaultdict(list)
    for k, c in enumerate(ta['cells']): CG[(int(c[0] * 1000), int(c[1] * 1000))].append((k, c))   # 위도·경도 0.001° 칸(약 111×88m) — 70m 안 칸만 빨리 찾기
    def near_cells(la, lo):
        a, b = int(la * 1000), int(lo * 1000)
        return [kc[1] for kc in sorted(kc for i in (-1, 0, 1) for j in (-1, 0, 1) for kc in CG.get((a + i, b + j), ()))]   # 원래 칸 차례 그대로(동점 주 위반이 바뀌지 않게)
    for code, nm in dv.items(): obj('VIO-%s' % code, 'VIO', nm=nm)
    INTs = [O[k] for k in O if O[k]['t'] == 'INT']
    for it in INTs:
        cs = [c for c in near_cells(it['lat'], it['lon']) if m(c[0], c[1], it['lat'], it['lon']) <= R]
        if not cs: continue
        yrs = [sum(c[2 + k] for c in cs) for k in range(10)]
        a = obj('ACC-%s' % it['id'], 'ACC', y0=2016, years=yrs, dead=sum(c[12] for c in cs), serious=sum(c[13] for c in cs), ped=sum(c[14] for c in cs), night=sum(c[18] for c in cs), tod=[sum(c[19 + k] for c in cs) for k in range(4)], cells=len(cs), r=R)
        edge(it['id'], '발생', a, 'C', ('taas10-seocho.json' if AREA == 'seocho' else 'taas10(여섯 구)') + '(70m 안 100m 칸)')
        vc = collections.Counter()
        for c in cs: vc[c[23]] += c[24]
        for code, n in vc.items(): edge(a, '주요원인', 'VIO-%s' % code, 'C', ('taas10-seocho.json' if AREA == 'seocho' else 'taas10(여섯 구)') + '(칸마다 주 위반 하나)', n=n)
    al = J(os.path.join(D, 'gargo-alerts-seoul.json'))
    for it in INTs:
        for c in al['cam']:
            if c[2] and len(c) > 7 and c[7] == 'p' and m(c[1], c[0], it['lat'], it['lon']) <= 100:
                edge(it['id'], '보유', obj('CAM-%.6f,%.6f' % (c[0], c[1]), 'CAM', lim=c[2], road=c[5] or None, place=c[6] or None), 'C', 'gargo-alerts-seoul.json(100m 안)')
        for z in al['sz']:
            d = m(z[1], z[0], it['lat'], it['lon'])
            if d <= 300: edge(it['id'], '가까움', obj('ATT-SZ-%.5f,%.5f' % (z[0], z[1]), 'ATT', kind=z[2], nm=z[3] or None), 'C', 'gargo-alerts-seoul.json(300m 안)', d=round(d))
    evt_build(O, obj, edge, INTs)
    rd_build(obj, edge, by_cits)
    sta_build(obj, edge, INTs)
    acl_build(obj, edge, sorted(O_RD), {l[0]: l for l in J(os.path.join(D, 'nav-seocho.json'))['links']}, ta)
    ks = J(os.path.join(D, 'sig-ksc-seocho.json'))
    for it in ks['items']:
        tgt = by_cits.get(str(it['no']))
        if not tgt: continue
        for n, h in enumerate(it.get('hist') or []):
            a = obj('ACT-%s-%d' % (it['no'], n + 1), 'ACT', what=h, ym=ym_of(h), public=1)
            edge(a, '대상', tgt, 'A', 'sig-ksc-seocho.json hist(교통과 출력물)')
            why = re.search(r'([^()]+?)\s*(?:을|를)?\s*(?:관련|위한|위해)', h)   # 「사고잦은곳 관련 개선」 「꼬리물기 해소를 위한 시차제」 꼴만 — 조치 자체(연장·신설…)는 이유가 아니다
            r = obj('REC-%s' % a, 'REC', text=(why.group(1).strip() if why else '이력 글에 이유가 적혀 있지 않다 — 교통과 내부 문서 확인'), internal=1)
            edge(a, '근거기록', r, 'A' if why else 'E', 'sig-ksc-seocho.json hist')
    tl = J(os.path.join(CORE, 'src', 'tbook-law.json')); title_idx = {l['title']: k for k, l in enumerate(tl['laws'])}
    used = set(t for v in VIO_LAW.values() for t in v)
    law_ids = {}
    for k, l in enumerate(tl['laws']):
        if l['title'] not in used: continue
        law_ids[k] = obj('LAW-T%d' % k, 'LAW', title=l['title'], meta=l['meta'], penalty=l.get('penalty'), arts=arts_meta(l['meta']))
    for code, titles in VIO_LAW.items():
        for t in titles:
            if t not in title_idx: raise SystemExit('T-Book 범칙금 DB 에 없는 제목: ' + t)
            edge('VIO-%s' % code, '근거', law_ids[title_idx[t]], 'C', 'VIO_LAW 이름 맞대기(build.py) · 확인 필요')
    def verified(p): return bool(p and p.get('c') and p.get('d') and p.get('nm') != '조회실패')   # T-Book PRECDOC 의 「조회실패」(원문을 못 받은 것)는 확인된 판례가 아니다
    unver = sorted(no for no, p in tl['precdoc'].items() if not verified(p))
    for no, p in tl['precdoc'].items():
        if not verified(p): continue
        jo = p.get('jo') or ''
        pid = obj('PREC-%s' % no, 'PREC', no=no, court=p.get('c'), date=p.get('d'), nm=p.get('nm'), jo=jo or None)
        ja = arts_jo(jo)
        for k, lid in law_ids.items():
            la = set(tuple(x) for x in O[lid]['arts'])
            hit = [x for x in ja if (x[0], x[1]) in la and x[0] != '교통사고처리 특례법']   # 교특법 §3 은 12대 중과실이 모두 같은 조라 판례를 가르지 못한다 — 도로교통법 등 나머지 조가 같을 때만
            if hit: edge(lid, '해석', pid, 'C' if all(x[2] for x in hit) else 'A', '판결문 참조조문 ↔ 범칙금 DB 조문(같은 조)', arts=sorted(set('%s 제%s조' % (x[0], x[1]) for x in hit)))
    # T-Book 범칙금 DB 의 처리 글(handle)이 적은 판례 사건번호 — 원문 대조된 판례(PRECDOC)에 있으면 「T-Book 본문이 그 항목의 해석으로 적은 판례」(등급 A)
    for k, lid in law_ids.items():
        for no in sorted(set(re.findall(r'(\d{4}[가-힣]{1,3}\d+)', tl['laws'][k].get('handle') or ''))):
            if verified(tl['precdoc'].get(no)) and not any(e[0] == lid and e[2] == 'PREC-' + no for e in E): edge(lid, '해석', 'PREC-' + no, 'A', 'T-Book 범칙금 DB handle 글에 적힌 사건번호 · 원문 대조(PRECDOC)')
    rl = J(os.path.join(D, 'onto-rules.json'))
    for r in rl['rules']: obj(r['id'], 'RULE', area=r.get('area'), title=r['title'], d=r['d'], g=r['g'], s=r.get('s') or [], o=r.get('o') or [], test=r.get('t'))   # 장부의 t(시험값) → test(객체의 t 는 타입)
    for f in rl['field']:
        obj(f['id'], 'FK', date=f['date'], said=f['said'], conf=f.get('conf'))
        for u in f.get('use') or []:
            if u not in O or O[u]['t'] != 'RULE': raise SystemExit('onto-rules.json — 현장 판단 %s 가 없는 규칙 %s 에 기댄다' % (f['id'], u))
            edge(f['id'], '뒷받침', u, 'B', 'onto-rules.json(소유자 현장 판단)')
    used_ids = set(i for e in E for i in (e[0], e[2]))
    O = {k: v for k, v in O.items() if v['t'] in ('INT', 'VIO', 'RULE', 'FK') or k in used_ids}   # 아무 링크도 없는 PREC·LAW 는 뺀다
    pplf = plc_people(O)
    srcs = pplf + ['onto-int.json', 'sig-net-seocho.json'] + taf + ['gargo-alerts-seoul.json', 'sig-ksc-seocho.json', 'onto-rules.json', 'house-dong.json', 'mig-dong.json', 'foreign-dong.json', 'econ-dong.json', 'dui-ref-seoul.json', 'police.json', 'onto-events.json', 'season-seocho.json', 'sig-approach-seocho.json', 'nav-seocho.json', 'spd-normal-seocho.json', 'flood-link-seocho.json', 'rd-cell-seocho.json', 'jur-seocho.json', 'tgis-pe.json']
    doc = {'schema': 'onto-core/1', 'area': AREA_NM, 'made': datetime.datetime.now().isoformat(timespec='seconds'), 'schema_ext': 'ontology-core/schema-ext.json',
           'sources': {s: hashlib.sha256(open(os.path.join(D, s), 'rb').read()).hexdigest()[:16] for s in srcs} | {'src/tbook-law.json': tl.get('sha256_of_values', '')[:16] + ' · T-Book ' + str(tl.get('ver'))},
           'asof': {s: asof_of(s) for s in srcs} | {'src/tbook-law.json': 'T-Book ' + str(tl.get('ver')) + ' 범칙금 DB·원문 대조 판례'},
           'unverified_precedents': unver, 'unverified_note': 'T-Book 판례 목록에 있으나 원문 조회에 실패한 사건번호 — 잇지 않았다(확인된 번호만)',
           'count': dict(collections.Counter(v['t'] for v in O.values())), 'edges_count': dict(collections.Counter(e[1] for e in E)),
           'objects': sorted(O.values(), key=lambda v: v['id']), 'edges': E}
    # 비공개 전체 판(도착 포함) → ontology-core/data/private/(git 밖 · .gitignore) · 공개 판은 「도착」 링크를 뺀다(소유자 2026-10-23)
    PRIV_REL = {'도착'}; os.makedirs(os.path.join(CORE, 'data', 'private'), exist_ok=True)
    rp = os.path.join(PRIV, 'onto-reach-%s.json' % AREA)
    full = dict(doc, private='비공개 전체 판 — 공개 판에 없는 링크 ' + ','.join(sorted(PRIV_REL)), sources=dict(doc['sources'], **({'07_API키/out/onto/onto-reach-%s.json' % AREA: hashlib.sha256(open(rp, 'rb').read()).hexdigest()[:16]} if os.path.exists(rp) else {})))
    json.dump(full, open(os.path.join(CORE, 'data', 'private', OUTF[:-5] + '-full.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    E = [e for e in E if e[1] not in PRIV_REL]; doc = dict(doc, edges=E, edges_count=dict(collections.Counter(e[1] for e in E)))
    os.makedirs(os.path.join(CORE, 'data'), exist_ok=True); p = os.path.join(CORE, 'data', OUTF)
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(doc['count'], doc['edges_count'], os.path.getsize(p), 'B')
    # 지도용 가벼운 판(2026-10-23 게임 세션 부탁 — 지도는 q1·q2·q3·q5 만 쓴다): 사건·접근로·도로 구간·250m 칸과 그 링크를 뺀 같은 꼴 · 값은 그대로
    LITE = {'EVT', 'APR', 'RD', 'PLC', 'ACL', 'STA', 'PBX'}; keep = {o['id'] for o in doc['objects'] if o['t'] not in LITE}
    lite = dict(doc, lite='지도용 — 뺀 객체 ' + ','.join(sorted(LITE)) + ' · 전체는 ' + OUTF, objects=[o for o in doc['objects'] if o['id'] in keep], edges=[e for e in E if e[0] in keep and e[2] in keep])
    lite['count'] = dict(collections.Counter(v['t'] for v in lite['objects'])); lite['edges_count'] = dict(collections.Counter(e[1] for e in lite['edges']))
    pl = p[:-5] + '-map.json'; json.dump(lite, open(pl, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('지도용', os.path.getsize(pl), 'B')
if __name__ == '__main__': main()
