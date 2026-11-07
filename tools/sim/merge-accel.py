# -*- coding: utf-8 -*-
# 합류부 가속차로 길이 — OpenStreetMap 차로 수(lanes) 표시로 잰다(2026-11-07 · 합류부 시뮬의 「가속차로 길이 = 설계값」 빈칸)
#   원자료 = Geofabrik south-korea-latest.osm.pbf(osmium 은 한글 경로를 못 열어 C:/Users/knpth/regionwork/osm/)
#   잰 법: data/sim-merges.json 의 합류 노드 둘레 80m 안에서 연결로(*_link) 길이 본선 길에 붙는 OSM 마디를 찾고 →
#     본선 아래쪽(붙은 뒤)으로 같은 등급 길을 1.5km 까지 따라가며 차로 수를 읽는다 · 붙기 전 본선 차로(up) 보다 많아진 구간이 이어지는 거리 = 가속차로(또는 차로 더해짐)
#     1.5km 안에 다시 up 으로 줄면 「끝남」(가속차로) · 안 줄면 「이어짐」(차로 더해짐) · 처음부터 안 늘면 「OSM 에 늘어남 없음」(가속차로가 없거나 lanes 를 안 적음)
#   ⚠ OSM 은 자원봉사 지도라 차로 수가 빠지거나 틀릴 수 있다 — 지도에는 「OSM 표시로 잰 값 · 현장 확인 전」으로만 · 노드링크 차로(inL·outL)와 다르면 둘 다 보인다
#   결과 = 저장소 밖 07_API키/out/merge_accel.json(합류부마다 [m 또는 null, 'end'|'add'|'none'|'nl'|'nf', up 차로, 늘어난 차로, OSM 길 id]) — 지도 자료에는 안 싣는다
#   2026-11-07 첫 판: 255곳 중 끝남 6 · 이어짐 5 · 늘어남 없음 85 · 차로 안 적힘 97 · 합류점 못 찾음 62 — 서초IC 는 노드링크 4→5 인데 OSM 은 5→5(가속차로를 본선 차로에 넣어 적음)
#     → OSM 으로는 가속차로 길이를 못 채운다(「늘어남 없음」이 「가속차로 없음」이 아니다) · 채울 길 = 국토지리정보원 정밀도로지도(차선 노면선 · 국토정보플랫폼 map.ngii.go.kr · 고속국도·일반국도 · 서울 도시고속도로는 구축 여부 확인 필요) 또는 현장
#   쓰기: py -3.12 -X utf8 tools/sim/merge-accel.py [pbf]
import os, sys, json, math, datetime
import osmium

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PBF = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/osm/south-korea-latest.osm.pbf'
F = os.path.join(ROOT, 'data', 'sim-merges.json')
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'merge_accel.json')
J = json.load(open(F, encoding='utf-8'))
I = J['items']
B = (min(i['lat'] for i in I) - 0.03, max(i['lat'] for i in I) + 0.03, min(i['lon'] for i in I) - 0.03, max(i['lon'] for i in I) + 0.03)
MAIN = {'motorway', 'trunk', 'primary', 'secondary', 'tertiary'}
LINK = {k + '_link' for k in MAIN}


def num(s):
    try: return int(str(s).split(';')[0].strip())
    except (ValueError, TypeError): return None


class H(osmium.SimpleHandler):
    def __init__(s):
        super().__init__(); s.W = {}; s.N = {}

    def way(s, w):
        h = w.tags.get('highway')
        if h not in MAIN and h not in LINK: return
        try: pts = [(n.ref, n.location.lat, n.location.lon) for n in w.nodes]
        except osmium.InvalidLocationError: return
        if not any(B[0] <= p[1] <= B[1] and B[2] <= p[2] <= B[3] for p in pts): return
        ow = w.tags.get('oneway')
        s.W[w.id] = {'h': h, 'ln': num(w.tags.get('lanes')), 'ow': ow in ('yes', '1', 'true') or h == 'motorway' or h.endswith('_link') and ow != 'no',
                     'rev': ow == '-1', 'nd': [p[0] for p in pts], 'ref': w.tags.get('ref'), 'nm': w.tags.get('name')}
        for p in pts: s.N[p[0]] = (p[1], p[2])


h = H(); h.apply_file(PBF, locations=True, idx='flex_mem')
W, N = h.W, h.N
for w in W.values():
    if w['rev']: w['nd'] = w['nd'][::-1]
starts, ends, onw = {}, {}, {}
for wid, w in W.items():
    starts.setdefault(w['nd'][0], []).append(wid); ends.setdefault(w['nd'][-1], []).append(wid)
    for k, nd in enumerate(w['nd']): onw.setdefault(nd, []).append((wid, k))


def dist(a, b):
    (la1, lo1), (la2, lo2) = N[a], N[b]
    return math.hypot((la2 - la1) * 111000, (lo2 - lo1) * 111000 * math.cos(math.radians(la1)))


def bear(a, b):
    (la1, lo1), (la2, lo2) = N[a], N[b]
    return math.degrees(math.atan2((lo2 - lo1) * math.cos(math.radians(la1)), la2 - la1)) % 360


def adiff(x, y): d = abs(x - y) % 360; return min(d, 360 - d)


def walk(wid, k, up, hcls, maxd=1500):
    """본선 길 wid 의 k 번째 마디(합류점)부터 아래쪽으로 — (늘어난 거리, 끝 종류, 늘어난 차로)"""
    w = W[wid]; d = 0.0; seg = []   # (거리 끝, 차로)
    cur, pos, guard = wid, k, 0
    while d < maxd and guard < 40:
        guard += 1; w = W[cur]; nd = w['nd']
        for a, b in zip(nd[pos:], nd[pos + 1:]): d += dist(a, b)
        seg.append((d, w['ln']))
        last = nd[-1]; hb = bear(nd[-2], nd[-1]) if len(nd) > 1 else 0
        nx = [x for x in starts.get(last, []) if x != cur and W[x]['h'] == hcls and W[x]['ow'] and len(W[x]['nd']) > 1 and adiff(bear(W[x]['nd'][0], W[x]['nd'][1]), hb) < 35]
        if not nx: break
        cur, pos = nx[0], 0
    ln0 = seg[0][1]
    if ln0 is None or up is None: return None, 'nl', None
    if ln0 <= up: return 0, 'none', 0
    for (de, ln) in seg:
        if ln is None: return None, 'nl', ln0 - up
        if ln <= up:
            prev = [x for x in seg if x[0] < de]
            return round(prev[-1][0] if prev else de), 'end', ln0 - up
    return round(seg[-1][0]), 'add', ln0 - up


stat = {}
for it in I:
    la, lo = it['lat'], it['lon']; best = None
    for nd, (a, b) in N.items():
        if abs(a - la) > 0.0012 or abs(b - lo) > 0.0015: continue
        dd = math.hypot((a - la) * 111000, (b - lo) * 111000 * math.cos(math.radians(la)))
        if dd > 80: continue
        lk = [x for x in ends.get(nd, []) if W[x]['h'] in LINK]   # 연결로가 여기서 끝나고
        mn = [(x, k) for x, k in onw.get(nd, []) if W[x]['h'] in MAIN and W[x]['ow'] and k < len(W[x]['nd']) - 1]   # 본선이 여기를 지나 아래로 이어짐
        if lk and mn and (best is None or dd < best[0]): best = (dd, nd, lk, mn)
    if not best: it['acc'] = [None, 'nf', None, None, None]; stat['nf'] = stat.get('nf', 0) + 1; continue
    _, nd, lk, mn = best
    wid, k = mn[0]
    # 붙기 전 본선 차로 = 같은 마디로 들어오는 본선 길(연결로 아님)
    if k > 0: upw = wid
    else:
        ins = [x for x in ends.get(nd, []) if W[x]['h'] == W[wid]['h']]
        upw = ins[0] if ins else None
    up = W[upw]['ln'] if upw else None
    m, kind, add = walk(wid, k, up, W[wid]['h'])
    it['acc'] = [m, kind, up, add, wid]
    stat[kind] = stat.get(kind, 0) + 1
J['acc'] = {'source': 'OpenStreetMap contributors (ODbL) · Geofabrik south-korea-latest.osm.pbf %s' % datetime.date.fromtimestamp(os.path.getmtime(PBF)).isoformat(),
            'fields': 'items[].acc = [가속차로(늘어난 구간) m 또는 null, end 끝남·add 끝까지 이어짐(1.5km)·none 늘어남 없음·nl 차로 수 안 적힘·nf OSM 합류점 못 찾음, 붙기 전 본선 차로(OSM), 늘어난 차로 수, OSM 본선 길 id]',
            'note': 'OSM 차로 수(lanes) 표시로 잰 값 — 자원봉사 지도라 빠지거나 틀릴 수 있다 · 현장 확인 전 · 노드링크 차로(inL·outL)와 따로 · tools/sim/merge-accel.py', 'made': datetime.date.today().isoformat(), 'stat': stat}
json.dump({'acc': J['acc'], 'items': {it['id'] + ':' + it['link'][1]: [it['nm'], it['main'], it['inL'], it['outL']] + it['acc'] for it in I}}, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(stat)
E = [it['acc'][0] for it in I if it['acc'][1] == 'end']
if E: E.sort(); print('끝남', len(E), '가운데', E[len(E) // 2], '범위', E[0], E[-1])
