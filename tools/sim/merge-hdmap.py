# -*- coding: utf-8 -*-
# 합류부 가속차로 길이 — 국토지리정보원 정밀도로지도(공공누리 1유형 · 출처 「국토지리정보원 정밀도로지도」)로 잰다
#   의도 문서 = intent/20261107-merge-accel-hdmap.md(확정 2026-11-07) · 원본 SHP 는 저장소 밖 ../07_API키/out/hdmap/(받은 이름 그대로 · zip 은 풀어 둔 폴더)
#   칸·코드 = 국토지리정보원 「정밀도로지도 설명 및 안내자료(2023. 5.)」(map.ngii.go.kr/static/download/ms/pblictn/preciseRoadMap/ · 2026-11-07 받아 읽음)
#     A2_LINK(주행경로링크 = 차로 중심선 · 차로 하나가 선 하나): ID · FromNodeID · ToNodeID · LinkType · LaneNo · R_LinkID · L_LinKID · ITSLinkID(ITS 표준링크 — sim-merges.json 의 link 와 같은 번호 체계) · Length
#     A1_NODE: NodeType 7 = 도로차로수변화 · B2_SURFACELINEMARK(노면선표시): Type 211 백색-단선-실선 · 212 백색-단선-점선 · 213/214 좌·우점혼선 · 221~224 겹선 · Kind 503 차선 · 506 진로변경제한선 · R_linkID/L_linkID = 선 오른쪽·왼쪽 차로 링크
#     좌표 = UTM-K(EPSG:5179) 또는 UTM52N — .prj 로 읽고 5179 미터로 맞춘다(없으면 값 범위로 가림)
#   잰 법(합류부마다 · link = [본선 들어옴, 연결로, 본선 나감])
#     ① 차로 위상: ITSLinkID = 연결로 인 차로 링크의 끝(노즈)에서 아래로 그 차로를 따라간다 — 끝 노드에 다른 차로가 함께 들어오면 「차로가 합쳐짐 = 가속차로 끝」(end) ·
#        노즈에서 바로 합쳐지면 가속차로 없음(none) · 1.5km 넘게 이어지면 차로 더해짐(add) · 다음 링크가 없으면 dead(자료 끊김)
#     ② 노면선: 그 차로 왼쪽 차선(R_linkID = 가속차로 · L_linkID = 본선 차로)을 실선·점선별로 더한다 — 실선 합 ≈ 시뮬의 「가속차로 앞 실선 S」
#     ①과 ② 차이(① 전체 또는 마지막 링크를 뺀 길이 중 가까운 쪽)가 30m 넘으면 「검토 필요」(rv 1)
#   결과 = data/sim-merge-accel.json(tg-sim-merge-accel/1 · 열쇠 = 노드 id + ':' + 연결로 링크) · 못 잰 까닭·표 = SRC/_measure.txt
#   ⚠ 정밀도로지도는 「교통 흐름이 바뀌는 곳」에서 링크를 끊는다 — 마지막 링크가 꼭 테이퍼는 아니다(last 로만 적음) · 도로 구조 규칙 제35조 값은 설계속도 기준이라 제한속도만 있는 우리 자료와 맞대지 않는다(참고로만)
#   쓰기: py -3.12 -X utf8 tools/sim/merge-hdmap.py schema | measure   (시험: HDMAP_SRC·HDMAP_OUT 로 폴더·결과 파일을 바꾼다)
import os, sys, glob, json, math, collections, datetime
import shapefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.environ.get('HDMAP_SRC') or os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'hdmap')
OUT = os.environ.get('HDMAP_OUT') or os.path.join(ROOT, 'data', 'sim-merge-accel.json')
MERGES = os.path.join(ROOT, 'data', 'sim-merges.json')
ENC = ['cp949', 'utf-8', 'euc-kr']
LAYER = {'link': ['A2_LINK', 'NT2_LINK'], 'node': ['A1_NODE', 'NT1_NODE'], 'line': ['B2_SURFACELINEMARK', 'RM1_LANELINE']}   # 뒤 이름 = 다른 세션이 말한 옛 이름(1차 출처 미확인 · 받은 파일이 그 이름이면 경고)
SOLID, DASH, MXL, MXR = {111, 121, 211, 221, 311, 321}, {112, 122, 212, 222, 312, 322}, {113, 123, 213, 223, 313, 323}, {114, 124, 214, 224, 314, 324}
MAXD, NEAR, RV = 1500, 400, 30


def open_shp(p):
    for e in ENC:
        try:
            r = shapefile.Reader(p, encoding=e)
            for i in range(min(len(r), 200)): r.record(i)   # 앞 200줄을 읽어 글자 판별
            return r, e
        except UnicodeDecodeError:
            continue
    return shapefile.Reader(p, encoding='latin-1'), 'latin-1'


def all_shp():
    return sorted(glob.glob(os.path.join(SRC, '**', '*.shp'), recursive=True))


def schema():
    shps = all_shp()
    if not shps:
        print('SHP 없음 —', SRC); sys.exit(1)
    out = []
    for p in shps:
        r, e = open_shp(p)
        prj = p[:-4] + '.prj'
        out.append('## %s  (도형 %s · %d개 · 글자 %s)' % (os.path.relpath(p, SRC), r.shapeTypeName, len(r), e))
        if os.path.exists(prj): out.append('prj: ' + open(prj, encoding='latin-1').read().strip()[:300])
        out.append('bbox: %s' % (list(r.bbox),))
        flds = [f for f in r.fields[1:]]
        recs = r.records()
        for i, f in enumerate(flds):
            c = collections.Counter(str(x[i]) for x in recs)
            top = ', '.join('%s×%d' % (k, v) for k, v in c.most_common(15))
            out.append('  %s (%s,%s) 고유 %d: %s' % (f[0], f[1], f[2], len(c), top[:400]))
        out.append('')
    t = '\n'.join(out)
    open(os.path.join(SRC, '_schema.txt'), 'w', encoding='utf-8').write(t)
    print(t[:6000])


# ---------- 읽기 ----------
_TR = {}


def to5179(p, pts):
    """그 파일 좌표 → EPSG:5179 미터"""
    if p not in _TR:
        from pyproj import CRS, Transformer
        prj = p[:-4] + '.prj'; crs = None
        if os.path.exists(prj):
            try: crs = CRS.from_wkt(open(prj, encoding='latin-1').read())
            except Exception: crs = None
        if crs is None:
            y = pts[0][1] if pts else 0
            crs = CRS.from_epsg(32652 if y > 3e6 else 5179)
        _TR[p] = None if crs.to_epsg() == 5179 else Transformer.from_crs(crs, CRS.from_epsg(5179), always_xy=True)
    t = _TR[p]
    return [(x, y) for x, y in pts] if t is None else [t.transform(x, y) for x, y in pts]


def plen(pts): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))


def sid(v):
    s = str(v).strip()
    return '' if s in ('', 'None', '0', 'nan') else s


def load(kind):
    rows, used = {}, []
    for p in all_shp():
        b = os.path.basename(p).upper()
        hit = [k for k in LAYER[kind] if k in b]
        if not hit: continue
        used.append((os.path.relpath(p, SRC), hit[0]))
        r, _ = open_shp(p)
        names = [f[0].lower() for f in r.fields[1:]]
        for sr in r.iterShapeRecords():
            a = dict(zip(names, sr.record))
            pts = to5179(p, [tuple(q[:2]) for q in sr.shape.points])
            k = sid(a.get('id')) or '%s#%d' % (b, len(rows))
            a['_pts'] = pts
            rows[k] = a
    return rows, used


def num(v):
    try: return int(float(str(v).strip()))
    except (ValueError, TypeError): return None


# ---------- 재기 ----------
def measure():
    J = json.load(open(MERGES, encoding='utf-8'))
    L, uL = load('link'); B, uB = load('line')
    if not L:
        print('A2_LINK(주행경로링크) SHP 없음 —', SRC); sys.exit(1)
    warn = [u for u in uL + uB if u[1] in ('NT2_LINK', 'RM1_LANELINE')]
    lk = {}
    for k, a in L.items():
        lk[k] = {'id': k, 'fn': sid(a.get('fromnodeid')), 'tn': sid(a.get('tonodeid')), 'its': sid(a.get('itslinkid')), 'lt': num(a.get('linktype')),
                 'ln': num(a.get('laneno')), 'r': sid(a.get('r_linkid')), 'l': sid(a.get('l_linkid')), 'len': plen(a['_pts']), 'pts': a['_pts'], 'ver': str(a.get('version') or '').strip()}
    outN, inN, byIts = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
    for k, x in lk.items():
        if x['fn']: outN[x['fn']].append(k)
        if x['tn']: inN[x['tn']].append(k)
        if x['its']: byIts[x['its']].append(k)
    grid = collections.defaultdict(list)   # 500m 칸 → 링크 끝점(가까운 자료가 있는지)
    for k, x in lk.items():
        for q in (x['pts'][0], x['pts'][-1]): grid[(int(q[0] // 500), int(q[1] // 500))].append(q)
    lines = collections.defaultdict(list)   # 가속차로 링크 id → 그 링크를 오른쪽에 둔 노면선
    for k, a in B.items():
        r, l = sid(a.get('r_linkid')), sid(a.get('l_linkid'))
        if r: lines[r].append((num(a.get('type')), num(a.get('kind')), l, plen(a['_pts'])))
    from pyproj import Transformer
    tr = Transformer.from_crs(4326, 5179, always_xy=True)

    def near(x, y):
        gx, gy = int(x // 500), int(y // 500)
        return any(math.hypot(q[0] - x, q[1] - y) < NEAR for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in grid.get((gx + dx, gy + dy), ()))

    def pick(cands, mo):
        c = sorted(cands, key=lambda k: (lk[k]['its'] != mo, bool(lk[k]['r']), -(lk[k]['ln'] or 0)))   # 본선 나감 번호 먼저 · 오른쪽 끝 차로 먼저
        return c[0]

    def walk(e, rset, mo):
        """연결로 차로 마지막 링크 e 의 끝(노즈)부터 — (m, 종류, 마지막 링크 m, 가속차로 링크들)"""
        n = lk[e]['tn']
        if [x for x in inN.get(n, []) if x != e and x not in rset]: return 0, 'none', 0, []
        nx = [x for x in outN.get(n, []) if x not in rset]
        if not nx: return None, 'dead', None, []
        cur, d, ch, g = pick(nx, mo), 0.0, [], 0
        while g < 80:
            g += 1; x = lk[cur]; d += x['len']; ch.append(cur)
            if [y for y in inN.get(x['tn'], []) if y != cur]: return round(d), 'end', round(x['len']), ch
            if d > MAXD: return round(d), 'add', None, ch
            nx = [y for y in outN.get(x['tn'], []) if y not in ch]
            if not nx: return round(d), 'dead', round(x['len']), ch
            cur = pick(nx, mo)
        return round(d), 'dead', None, ch

    res, stat, rows = {}, collections.Counter(), []
    for it in J['items']:
        key = it['id'] + ':' + it['link'][1]
        mi, rp, mo = it['link']
        x0, y0 = tr.transform(it['lon'], it['lat'])
        if not near(x0, y0): stat['noarea'] += 1; rows.append((it, 'noarea', None)); continue
        R = byIts.get(rp, [])
        if not R: stat['norp'] += 1; rows.append((it, 'norp', None)); continue
        if not byIts.get(mo): stat['nomo'] += 1; rows.append((it, 'nomo', None)); continue
        rset = set(R)
        ends = [k for k in R if not [y for y in outN.get(lk[k]['tn'], []) if y in rset]]   # 연결로 차로의 마지막 링크(차로마다 하나)
        best = None
        for e in ends:
            m, kind, last, ch = walk(e, rset, mo)
            sol = dash = mxl = mxr = 0.0
            for c in ch:
                for ty, kd, l, ln in lines.get(c, []):
                    if not l or l in ch: continue
                    if ty in SOLID: sol += ln
                    elif ty in DASH: dash += ln
                    elif ty in MXL: mxl += ln
                    elif ty in MXR: mxr += ln
            b2 = sol + dash + mxl + mxr
            r = {'m': m, 'k': kind, 'last': last, 'sol': round(sol), 'dash': round(dash), 'mxL': round(mxl), 'mxR': round(mxr), 'b2': round(b2), 'nl': len(ch), 'rl': len(ends)}
            if kind == 'end' and b2 > 0:
                df = min(abs(m - b2), abs(m - (last or 0) - b2))
                r['rv'] = 1 if df > RV else 0
            elif kind == 'end': r['rv'] = 1   # 노면선이 없어 맞대 볼 수 없음
            rank = {'end': 3, 'add': 2, 'none': 1, 'dead': 0}[kind]
            if best is None or (rank, m or 0) > best[0]: best = ((rank, m or 0), r)
        if best is None: stat['noend'] += 1; rows.append((it, 'noend', None)); continue
        r = best[1]; stat[r['k']] += 1
        if r['k'] != 'dead': res[key] = r
        rows.append((it, r['k'], r))
    ver = collections.Counter(x['ver'] for x in lk.values() if x['ver']).most_common(3)
    D = {'schema': 'tg-sim-merge-accel/1', 'made': datetime.date.today().isoformat(),
         'source': '국토지리정보원 정밀도로지도(공공누리 제1유형 · 출처표시) · 국토정보플랫폼 내려받음 · 구축판 %s' % ', '.join(v for v, _ in ver),
         'fields': 'items{노드 id:연결로 링크} = {m 가속차로(노즈→차로 끝) m, k end 끝남·add 1.5km 넘게 이어짐(차로 더해짐)·none 노즈에서 바로 합쳐짐, last 마지막 링크 m(테이퍼 포함일 수 있음), sol·dash·mxL·mxR 가속차로 왼쪽 차선 실선·점선·좌점혼선·우점혼선 m, b2 차선 합 m, nl 링크 수, rl 연결로 차로 수(정밀도로지도), rv 1 = 차로 위상과 차선이 30m 넘게 다름(검토 필요)}',
         'note': '차로 하나하나의 중심선(A2_LINK)을 ITS 표준링크 번호(ITSLinkID)로 합류부에 맞춰 잰 값 · 도로 구조 규칙 제35조 최소 길이는 설계속도 기준이라 참고로만 · tools/sim/merge-hdmap.py',
         'stat': dict(stat), 'items': res}
    json.dump(D, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    T = ['# 합류부 가속차로 — 정밀도로지도로 잰 결과 %s' % D['made'], '', '읽은 파일: ' + ', '.join('%s(%s)' % u for u in uL + uB), '']
    if warn: T.append('⚠ 옛 이름 층(NT2_LINK·RM1_LANELINE)을 읽었다 — 칸 이름이 안내서(A2_LINK·B2)와 같은지 _schema.txt 로 확인할 것'); T.append('')
    T.append('까닭: ' + ' · '.join('%s %d' % kv for kv in sorted(stat.items())) + '  (noarea 그 자리 자료 없음 · norp 연결로 번호(ITSLinkID) 없음 · nomo 본선 나감 번호 없음 · noend 연결로 끝 못 찾음 · dead 이어지는 차로 끊김)')
    T.append(''); T.append('| 이름 | 본선 | 차로(ITS) | 결과 | 가속차로 m | 마지막 링크 | 실선 | 점선 | 검토 |'); T.append('|---|---|---|---|---|---|---|---|---|')
    for it, k, r in rows:
        if k in ('noarea',): continue
        T.append('| %s | %s | %s→%s | %s | %s | %s | %s | %s | %s |' % (it['nm'], it['main'], it['inL'], it['outL'], k, (r or {}).get('m', ''), (r or {}).get('last', ''), (r or {}).get('sol', ''), (r or {}).get('dash', ''), '⚠' if (r or {}).get('rv') else ''))
    open(os.path.join(SRC, '_measure.txt'), 'w', encoding='utf-8').write('\n'.join(T))
    print(dict(stat)); print('→', OUT, '·', len(res), '곳')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'schema'
    if cmd == 'schema': schema()
    elif cmd == 'measure': measure()
    else: print('schema | measure'); sys.exit(1)
