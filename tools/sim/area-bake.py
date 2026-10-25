# -*- coding: utf-8 -*-
# 신호·수요 시뮬레이터 — 구역 자동 만들기(2026-10-25 · 소유자 「서울 시내 지도에서도 · 통행량을 고르고 여러 조건 · 확대할 수 있게 준비」)
#   고른 자리 둘레(반지름)의 신호 교차로를 서울 도로망(nav-seoul — 국가표준 노드링크)에서 찾아 서로 잇고, 신호값·교통량을 붙여
#   js/sim.js 가 바로 돌리는 구역 자료(tg-sim/2)를 만든다. 반포처럼 손으로 짠 구역(banpo-bake.py)과 같은 꼴이다.
#   값의 출처: 신호 = 교통과 현시도(sig-ksc-seocho · 있으면 먼저) → 서울시 T-Data 방향별 실측(sigdir · 요일·시각마다 한 기록) · 길 = 노드링크 길이·차로
#   · 교통량 = 서울시 교통량 조사(같은 길 이름 1.2km 안 지점 · 두 방향 평균) · 그 밖 = 설계값(차로 × 차로당 대수 · 회전 비율 등)
#   한계(구역 자료 about 칸에도 적는다): 신호 없는 교차로는 그냥 지나간다 · 다리는 넷(북·동·남·서)으로 줄인다(다섯 갈래는 하나 버림 · log)
#   · 회전 금지(nav turns)는 아직 안 씀 · 고가·지하차도로 지나는 차는 이 구역 길에 안 든다 · 끌어들이는 곳(att)·조치(actions)는 화면에서 붙인다
# 쓰기: py -3.12 -X utf8 tools/sim/area-bake.py <이름> <위도> <경도> [반지름 m=500]   →  data/sim-<이름>.json
#   nav-seoul.json(13MB · 지도 저장소 data/ · 올리지 않는 파일일 수 있음)이 없으면 nav-six.json 을 쓴다
import json, math, os, sys, glob, datetime, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
SDA = {'nt': 0, 'ne': 45, 'et': 90, 'se': 135, 'st': 180, 'sw': 225, 'wt': 270, 'nw': 315}   # 나침반 각(북 0 · 시계 방향)
LEG4 = ['nt', 'et', 'st', 'wt']
MAXOUT = 600     # 바깥 길 저장 길이 상한(설계값)
MAXCHAIN = 1500  # 신호 사이를 이을 때 이보다 길면 끊는다


def bearing(a, b):   # a→b 나침반 각(경도·위도)
    return math.degrees(math.atan2((b[0] - a[0]) * math.cos(math.radians(37.5)), b[1] - a[1])) % 360


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 88200, (a[1] - b[1]) * 111000)


def adiff(a, b):
    return abs((a - b + 180) % 360 - 180)


def main():
    name, lat, lon = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
    R = float(sys.argv[4]) if len(sys.argv) > 4 else 500
    C = (lon, lat)
    navf = os.path.join(D, 'nav-seoul.json')
    if not os.path.exists(navf): navf = os.path.join(D, 'nav-six.json')
    nav = json.load(open(navf, encoding='utf-8'))
    N = nav['nodes']
    L = {}
    for r in nav['links']:
        L[r[0]] = {'id': r[0], 'f': r[1], 't': r[2], 'len': r[3], 'lim': r[4], 'gr': r[5], 'lanes': r[6] or 1, 'nm': r[7] or '', 'ramp': r[8], 'ty': r[12] if len(r) > 12 else '000'}
    IN, OUT = collections.defaultdict(list), collections.defaultdict(list)
    for l in L.values():
        if l['f'] in N and l['t'] in N:
            OUT[l['f']].append(l); IN[l['t']].append(l)
    # ---- 신호 교차로(번호로 묶은 노드) — 반지름 안 · 신호값 있는 곳만 ----
    ksc = {i['no']: i for i in json.load(open(os.path.join(D, 'sig-ksc-seocho.json'), encoding='utf-8'))['items']}
    sd = {}
    for f in glob.glob(os.path.join(D, 'sigdir', 'c', '*.json')):
        for k, v in json.load(open(f, encoding='utf-8'))['its'].items(): sd[k] = v
    grp = collections.defaultdict(list)
    for nid, n in N.items():
        s = n[7] if len(n) > 7 and isinstance(n[7], dict) else None
        if s and s.get('no') and dist((n[0], n[1]), C) <= R: grp[s['no']].append(nid)
    log = []
    sig = {}
    for no, ns in grp.items():
        has = no in ksc or any(r.get('mv') for r in sd.get(no, []))
        if not has: log.append('신호값 없음 — 지나가는 교차로로 ' + no); continue
        cx = sum(N[x][0] for x in ns) / len(ns); cy = sum(N[x][1] for x in ns) / len(ns)
        nm = (N[ns[0]][7].get('sd') or N[ns[0]][7].get('ksc') or [no, N[ns[0]][3]])[1] if isinstance(N[ns[0]][7], dict) else N[ns[0]][3]
        sig[no] = {'ns': set(ns), 'c': (cx, cy), 'nm': nm}
    owner = {}
    for no, g in sig.items():
        for x in g['ns']: owner[x] = no

    def chain(start_link, up):   # up=True: 상류로(들어오는 길) · False: 하류로(나가는 길) — 다른 신호 교차로 / 길이 상한 / 구역 밖까지
        cur, tot, seen, links = start_link, 0.0, set(), []
        while True:
            links.append(cur); tot += cur['len']; seen.add(cur['id'])
            nxt_node = cur['f'] if up else cur['t']
            if nxt_node in owner: return links, tot, owner[nxt_node]
            if tot > MAXCHAIN or dist((N[nxt_node][0], N[nxt_node][1]), C) > R + 400: return links, tot, None
            cand = [l for l in (IN[nxt_node] if up else OUT[nxt_node]) if l['id'] not in seen and l['ty'] not in ('001', '002') and not l['ramp']]
            # 되돌아가는 링크(맞은편 방향) 빼기
            back = cur['t'] if up else cur['f']
            cand = [l for l in cand if (l['f'] if up else l['t']) != back]
            if not cand: return links, tot, None
            same = [l for l in cand if l['nm'] and l['nm'] == cur['nm']]
            pool = same or cand
            b0 = bearing(N[cur['f']][:2], N[cur['t']][:2])
            pool.sort(key=lambda l: adiff(bearing(N[l['f']][:2], N[l['t']][:2]), b0))
            cur = pool[0]

    # 평소 속도(ITS · spd-normal-six · 링크 ID = 노드링크 ID) — 접근로 정지선 링크마다 「요일 갈래-시」 가운데값 · 자동 맞춤(sim-cal.py)이 쓴다
    NSP = {}
    for f in glob.glob(os.path.join(D, 'spd-normal-six', '*.json')):
        if f.endswith('index.json'): continue
        try: NSP.update(json.load(open(f, encoding='utf-8')).get('links', {}))
        except Exception: pass
    def nsp_of(lid):
        v = NSP.get(lid); return {k: x[0] for k, x in v.items() if 7 <= int(k.split('-')[1]) <= 23} if v else None
    nodes, links, entry = {}, {}, {}
    vol = {s['id']: s for s in json.load(open(os.path.join(D, 'traffic-vol-seoul.json'), encoding='utf-8'))['spots']}
    used_spot = {}
    legs = {no: {} for no in sig}
    for no, g in sig.items():
        # 들어오는 길: 교차로 노드로 들어오는 링크 가운데 출발점이 교차로 밖인 것
        apps = []
        for x in g['ns']:
            for l in IN[x]:
                if l['f'] in g['ns'] or l['ty'] in ('001', '002') or l['ramp']: continue
                lk, tot, fr = chain(l, True)
                far = lk[min(len(lk) - 1, 1)]['f']
                apps.append({'l': l, 'len': tot, 'fr': fr, 'brg': bearing(g['c'], N[far][:2]), 'lanes': l['lanes'], 'nm': l['nm']})
        outs = []
        for x in g['ns']:
            for l in OUT[x]:
                if l['t'] in g['ns'] or l['ty'] in ('001', '002') or l['ramp']: continue
                lk, tot, to = chain(l, False)
                far = lk[min(len(lk) - 1, 1)]['t']
                outs.append({'l': l, 'len': tot, 'to': to, 'brg': bearing(g['c'], N[far][:2]), 'lanes': l['lanes'], 'nm': l['nm']})
        for kind, arr in (('in', apps), ('out', outs)):
            by = {}
            for a in arr:
                lg = min(LEG4, key=lambda k: adiff(SDA[k], a['brg']))
                if lg in by:
                    keep, drop = (a, by[lg]) if a['lanes'] > by[lg]['lanes'] else (by[lg], a)
                    log.append('%s %s 다리 겹침 — %s(%s차로) 버림' % (no, lg, drop['nm'], drop['lanes'])); by[lg] = keep
                else: by[lg] = a
            for lg, a in by.items(): legs[no].setdefault(lg, {})[kind] = a
    # 길 만들기 — 안쪽(신호→신호)은 들어오는 쪽 기준으로 하나 · 바깥은 들어옴(in.) / 나감(out.)
    for no in sig:
        for lg, d in legs[no].items():
            a = d.get('in')
            if a:
                if a['fr'] and a['fr'] in sig and a['fr'] != no:
                    # 위쪽 교차로의 나가는 다리 가운데 이쪽으로 오는 것
                    up = [k for k, v in legs[a['fr']].items() if v.get('out') and v['out']['to'] == no]
                    if up:
                        lid = a['fr'] + '>' + no
                        links[lid] = {'id': lid, 'fr': a['fr'], 'to': no, 'len': round(a['len']), 'lanes': a['lanes'], 'nm': a['nm'] + '(' + a['fr'] + '→' + no + ')', 'src': '노드링크', 'ofr': up[0], 'oto': lg, 'its': a['l']['id'], 'nsp': nsp_of(a['l']['id'])}
                        continue
                lid = 'in.' + no + '.' + lg
                links[lid] = {'id': lid, 'fr': None, 'to': no, 'len': round(min(a['len'], MAXOUT)), 'lanes': a['lanes'], 'nm': (a['nm'] or '이름 없는 길') + ' — 들어옴', 'src': '노드링크 · 길이 ' + str(MAXOUT) + 'm 넘으면 ' + str(MAXOUT) + '(설계값)', 'oto': lg, 'src_in': 1, 'its': a['l']['id'], 'nsp': nsp_of(a['l']['id'])}
                # 교통량 조사 — 같은 길 이름 · 1.2km 안
                sp = None
                for s in vol.values():
                    if a['nm'] and a['nm'][:3] in s['name'] and dist((s['lon'], s['lat']), sig[no]['c']) < 1200: sp = s; break
                entry[lid] = {'spot': sp['id'], 'share': 1.0, 'src': '조사 ' + sp['id'] + ' ' + sp['name'] + ' 두 방향 평균(같은 길 1.2km 안)'} if sp else {'perLane': 300, 'src': '설계값 — 조사 지점 없음 · 차로 × 차로당 300대/시'}
                if sp: used_spot[sp['id']] = vol[sp['id']]
            o = d.get('out')
            if o and not (o['to'] and o['to'] in sig and o['to'] != no):
                lid = 'out.' + no + '.' + lg
                links[lid] = {'id': lid, 'fr': no, 'to': None, 'len': 0, 'lanes': o['lanes'], 'nm': (o['nm'] or '이름 없는 길') + ' — 나감', 'src': '노드링크', 'ofr': lg, 'sink': 1}
    # 안쪽 길의 나가는 쪽이 안 생긴 경우(위 교차로 다리 겹침으로 버려짐) — 그 길을 바깥 들어옴으로
    for no in sig:
        nodes[no] = {'id': no, 'nm': sig[no]['nm'], 'ty': 'sig', 'll': [sig[no]['c'][1], sig[no]['c'][0]], 'legs': {}}
    for l in links.values():
        if l.get('oto'): nodes[l['to']]['legs'].setdefault(l['oto'], {})['in'] = l['id']
        if l.get('ofr') and l['fr']: nodes[l['fr']]['legs'].setdefault(l['ofr'], {})['out'] = l['id']
    # ---- 신호 계획 ----
    MVNO = {1: ('et', 'Lt'), 2: ('wt', 'St'), 3: ('st', 'Lt'), 4: ('nt', 'St'), 5: ('wt', 'Lt'), 6: ('et', 'St'), 7: ('nt', 'Lt'), 8: ('st', 'St')}
    for no in sig:
        if no in ksc:
            k = ksc[no]
            nodes[no]['plan'] = {'src': '현시도', 'day': k['day'], 'tod': k['tod'], 'pat': k['pat'], 'Y': k['Y'], 'AR': k['AR'],
                                 'ph': [[MVNO[m][0] + '.' + MVNO[m][1] for m in p['mv'] if m in MVNO] for p in k['ph']],
                                 'dir': {p: [[r[0] + '.' + r[1], r[3], r[4], r[6]] for r in Ls if r[3] is not None] for p, Ls in k['dir'].items()}}
            continue
        # T-Data — 여덟 방위를 이 교차로의 실제 다리(넷)에 붙인다(60° 안 가장 가까운 것)
        legb = {lg: legs[no][lg]['in']['brg'] for lg in legs[no] if legs[no][lg].get('in')}
        def leg_of(dcode):
            if dcode not in SDA or not legb: return None
            lg = min(legb, key=lambda k: adiff(legb[k], SDA[dcode]))
            return lg if adiff(legb[lg], SDA[dcode]) <= 60 else None
        recs = []
        for r in sd.get(no, []):
            if not r.get('mv') or not r.get('cyc'): continue
            w = []
            for m in r['mv']:
                if m[1] not in ('St', 'Lt') or m[2] is None or m[5] is None: continue
                lg = leg_of(m[0])
                if lg: w.append([lg + '.' + m[1], round(m[2], 1), m[3] or 3, round(m[5], 1)])
            if not w: continue
            hh, mm = (r.get('from') or '12:00').split(':')
            recs.append({'day': r['day'], 'dk': [r['dow']], 't': int(hh) * 3600 + int(mm) * 60, 'cyc': r['cyc'], 'win': sorted(w, key=lambda x: x[3]), 'src': r.get('src')})
        nodes[no]['plan'] = {'src': 'T-Data', 'recs': recs}
        if not recs:   # 다리에 붙는 기록이 없으면 신호 없이 지나가게(설계 — log 에 남김)
            log.append('T-Data 기록을 다리에 못 붙임 — 신호 없이 지나감 ' + no)
            nodes[no]['plan'] = {'src': '없음(지나감)', 'win': [], 'cyc': 100}
            nodes[no]['free'] = [lg + '.' + t for lg in legs[no] for t in ('St', 'Lt')]
    design = {
        'turn': {'Lt': 0.15, 'Rt': 0.15, 'src': '설계값 — 회전 비율 조사 없음(좌·우 각 15% · 나머지 직진)'},
        'rtRed': {'v': 0.5, 'src': '설계값 — 우회전은 적색에도 이 몫만큼 빠진다'},
        'lostStart': {'v': 2, 'src': '설계값 — 녹색 처음 2초는 출발 손실'},
        'freeV': {'v': 30, 'src': '설계값 — 막히지 않을 때 주행 속도(km/h)'},
        'box': {'v': 0.3, 'src': '설계값 — 하류가 찼는데도 교차로 안으로 들어가는(꼬리물기) 차 비율'}}
    doc = {'schema': 'tg-sim/2', 'area': name, 'nm': name, 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'auto': 1, 'center': [lat, lon], 'r': R,
           'about': '자동으로 엮은 구역(tools/sim/area-bake.py) — 개념 시연 · 신호 없는 교차로는 지나감 · 다리는 넷으로 줄임 · 회전 금지 미반영 · 고가·지하차도 차는 빠짐',
           'nodes': nodes, 'links': links, 'vol': {k: {kk: v[kk] for kk in ('name', 'lat', 'lon', 'wd', 'sa', 'su', 'lanes')} for k, v in used_spot.items()}, 'entry': entry, 'design': design,
           'mvx': [], 'att': [], 'actions': [], 'preset': {},
           'sat': {'v': 2200, 'unit': '대/녹색 1시간/차로', 'src': '2차 자료', 'quote': '신호교차로 기본 조건에서 포화교통류율 2,200pcphgpl — 도로용량편람(2013) p.427'},
           'spacing': {'v': 7.5, 'unit': 'm/대', 'src': '설계값'}, 'log': log}
    out = os.path.join(D, 'sim-' + name + '.json')
    json.dump(doc, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('ok', out, os.path.getsize(out), 'B · 신호 교차로', len(nodes), '·', ', '.join(no + ' ' + n['nm'] for no, n in nodes.items()), '· 길', len(links), '· 들어오는 길', len(entry), '(조사 지점', sum(1 for e in entry.values() if 'spot' in e), ')')
    for x in log: print('  ·', x)


if __name__ == '__main__':
    main()
