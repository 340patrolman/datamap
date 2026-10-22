# -*- coding: utf-8 -*-
# 학교 → 관할 경찰서·지구대·행정동 (2026-10-22 소유자 「서초구를 열면 서초경찰서 방배경찰서 별로 학교들도 구분 · 여성청소년과에서 쓰기 좋고 학생 학부모도 어느 학교가 어디 관내인지」)
#   학교 = 한국교육시설안전원 초중등학교위치(공공데이터포털 15159184 · ../07_API키/out/dg/15159184/x.csv · dgfile.py 로 받음 · 학구도와 같은 학교 ID · 학교알리미 school-raw 는 3유형이라 쓰지 않는다)
#   행정동 = 학교 좌표가 든 SGIS 행정동(13_관할경계/원자료/hjd20260701.geojson · vuski/admdongkor · CC BY 4.0)
#   경찰서 = data/police.json dong(별표2 × 행정동) · 두 서가 나눠 맡는 동은 서초·방배 둘레만 data/jur-seocho.json 경계(현장 기준 · 반포4동 = 반포대로)로 가르고, 그 밖은 둘 다 적고 가까운 지구대 쪽을 먼저(근사)
#   지구대·파출소 = 그 서의 지구대·파출소 가운데 학교에서 가장 가까운 곳(관할 경계 비공개 — 근사 · 지도 pbNear 와 같은 셈)
# 쓰기: py -3.12 -X utf8 tools/region/schoolpol-bake.py   →  data/school-police/<시도 2자리>.json + index.json
import json, os, csv, glob, math, datetime
from shapely.geometry import shape, Point
from shapely.strtree import STRtree

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HJD = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
OUT = os.path.join(ROOT, 'data', 'school-police')
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15159184', 'x.csv')


def dist(la1, lo1, la2, lo2):
    x = (lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2)) * 111320
    y = (la2 - la1) * 110540
    return math.hypot(x, y)


def main():
    P = json.load(open(os.path.join(ROOT, 'data', 'police.json'), encoding='utf-8'))
    ST = {s[0]: s for s in P['stations']}
    byname = {s[1]: s[0] for s in P['stations']}
    # labels: 「1,4」 = 두 서가 나눠 맡음 · 「21~6」 = 기본 21번 서 + 일부 번지 6번 서(지도 polLab 과 같은 뜻)
    LAB = [[int(x) for x in str(l).split('~')[0].split(',') if x != ''] for l in P['labels']]
    LABX = [[int(x) for x in (str(l).split('~') + [''])[1].split(',') if x != ''] for l in P['labels']]
    PB = P['pbox']
    J = json.load(open(os.path.join(ROOT, 'data', 'jur-seocho.json'), encoding='utf-8'))
    JZ = []
    for z in J['zones']:
        sid = byname.get(z['name'])
        if sid is None:
            continue
        for ring in z['rings']:
            if len(ring) >= 4:
                JZ.append((shape({'type': 'Polygon', 'coordinates': [ring]}), sid))
    G = json.load(open(HJD, encoding='utf-8'))['features']
    polys = [shape(f['geometry']) for f in G]
    tree = STRtree(polys)
    # 학교 목록 = 한국교육시설안전원 초중등학교위치(공공데이터포털 15159184 · 사립·각종학교 포함) — 학구도 g 파일의 schools 는 학구에 걸린 학교만이라 서울반포초 등이 빠진다
    S = {}
    with open(SRC, encoding='utf-8-sig') as fh:
        for r in csv.DictReader(fh):
            r = {k.strip().lstrip('﻿'): v for k, v in r.items()}
            try:
                la, lo = float(r['위도']), float(r['경도'])
            except (ValueError, TypeError):
                la = lo = None
            S[r['학교ID']] = [r['학교명'], r['학교급구분'], r['설립형태'], lo, la, None, r['운영상태']]
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'school-zone', 'g', '*.json'))):   # 위치 파일에 없고 학구도에만 있는 학교를 더함
        for k, v in json.load(open(f, encoding='utf-8'))['schools'].items():
            if k not in S:
                S[k] = [v[0], v[1], v[2], v[3], v[4], None, v[6]]
    out = {}
    nst = {'경계': 0, '한 서': 0, '나눔(근사)': 0, '동 없음': 0}
    for k, v in S.items():
        nm, lv, est, lo, la = v[0], v[1], v[2], v[3], v[4]
        if lo is None or la is None:
            nst['동 없음'] += 1
            continue
        pt = Point(lo, la)
        hit = None
        for i in tree.query(pt):
            if polys[int(i)].covers(pt):
                hit = G[int(i)]['properties']
                break
        if not hit:
            nst['동 없음'] += 1
            continue
        d8 = hit['adm_cd2'][:8]
        sids = LAB[P['dong'][d8]] if d8 in P['dong'] else []
        xs = LABX[P['dong'][d8]] if d8 in P['dong'] else []
        how = 1
        if len(sids) > 1:
            zs = [sid for g, sid in JZ if g.covers(pt)]
            if zs:
                sids, how, xs = zs[:1], 0, []
            else:
                how = 2
        if not sids:
            nst['동 없음'] += 1
            continue
        if xs and len(sids) == 1:
            zs = [sid for g, sid in JZ if g.covers(pt)]
            if zs:
                sids, how, xs = zs[:1], 0, []
        # 나눠 맡는 동(근사)은 지구대가 더 가까운 서를 앞으로
        best = []
        for sid in sids:
            b, bd = None, 1e12
            for i, x in enumerate(PB):
                if x[6] != sid:
                    continue
                dd = dist(la, lo, x[3], x[4])
                if dd < bd:
                    b, bd = i, dd
            best.append((bd, sid, b))
        best.sort()
        sid0, pb0 = best[0][1], best[0][2]
        sids = [x[1] for x in best]
        nst[['경계', '한 서', '나눔(근사)'][how]] += 1
        sido = d8[:2]
        o = out.setdefault(sido, {'s': {}, 'st': {}, 'pb': {}})
        o['s'][k] = [nm, lv, est, lo, la, d8, hit['adm_nm'].split(' ')[-1], hit['sggnm'], sids, pb0, how, v[5], v[6], xs]
        for sid in sids:
            o['st'].setdefault(str(sid), []).append(k)
        if pb0 is not None:
            o['pb'].setdefault(str(pb0), []).append(k)
    os.makedirs(OUT, exist_ok=True)
    made = datetime.date.today().isoformat()
    idx = {}
    for sido, o in sorted(out.items()):
        doc = {
            'schema': 'tg-school-police/1', 'made': made, 'sido': sido,
            'source': '학교 = 한국교육시설안전원 초중등학교위치(공공데이터포털 15159184 · 학구도와 같은 학교 ID) · 행정동 = 통계청 SGIS 행정동 경계(vuski/admdongkor 2026-07 · CC BY 4.0) · 경찰서 = 「경찰청과 그 소속기관 직제 시행규칙」 별표2 × 행정동(data/police.json) · 서초·방배 둘레 = 현장 기준 경계(data/jur-seocho.json) · 지구대 자리 = 경찰청 지구대·파출소 주소 현황',
            'fields': 's{학구도 학교 ID: [이름, 학교급, 설립, 경도, 위도, 행정동 8자리, 행정동 이름, 시군구 이름, [경찰서 번호…](앞 = 먼저), 지구대·파출소 자리(police.json pbox 차례)|null, 서 정한 법(0 현장 기준 경계 · 1 동을 한 서가 맡음 · 2 두 서가 나눠 맡는 동 — 가까운 지구대 쪽 먼저 · 근사), (비움), 운영 상태, [그 동 일부 번지를 맡는 다른 서 번호…](별표2 「기본 서 + 일부 번지」 · 학교가 그 번지인지는 모름)]} · st{경찰서 번호: [학교 ID…]}(나눠 맡는 동의 학교는 두 서 모두에 든다) · pb{지구대 자리: [학교 ID…]}',
            'note': ['지구대·파출소 구역은 공식 관할이 아니라 근사다(관할 경계 비공개 — 그 서의 지구대·파출소 가운데 학교에서 가장 가까운 곳)',
                     '서 정한 법 2 = 별표2 가 번지로 두 서에 나눈 동이라 행정동으로는 못 가른다 — 두 서를 다 적고 지구대가 가까운 쪽을 앞에',
                     '학교 = 초중등학교위치 파일의 초·중·고·특수·각종학교(운영 상태 칸 그대로) — 유치원은 없다'],
            'count': {'학교': len(o['s']), '경찰서': len(o['st']), '지구대·파출소': len(o['pb'])},
            's': o['s'], 'st': o['st'], 'pb': o['pb']}
        open(os.path.join(OUT, sido + '.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
        idx[sido] = doc['count']
    open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8').write(json.dumps({'schema': 'tg-school-police-index/1', 'made': made, 'sido': idx, 'how': nst}, ensure_ascii=False, indent=1))
    print('학교', sum(len(o['s']) for o in out.values()), '·', nst)


if __name__ == '__main__':
    main()
