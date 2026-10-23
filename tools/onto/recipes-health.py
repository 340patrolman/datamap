# -*- coding: utf-8 -*-
# 엮어서 답 찾기 — 레시피 건강 검사(2026-10-23) : 예시 몇 개가 아니라 한 구의 모든 학교·동에서 걸음마다 값이 나오는지 센다
#   빈 걸음이 많으면 그 자료가 비었다는 뜻 — 메울 곳을 찾는 장부
# 쓰기: py -3.12 -X utf8 tools/onto/recipes-health.py [구 5자리=11650]   →  결과는 화면(커밋하지 않음)
import json, os, sys, math
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = lambda p: json.load(open(os.path.join(ROOT, 'data', p), encoding='utf-8'))
GU = sys.argv[1] if len(sys.argv) > 1 else '11650'
SD = GU[:2]


def dist(a, b, c, d):
    return math.hypot((d - b) * math.cos(math.radians((a + c) / 2)) * 111320, (c - a) * 110540)


sp = D('school-police/%s.json' % SD); cz = D('child-zone/%s.json' % SD); ez = D('edu-zone-biz/%s.json' % SD)
pf = D('police-func/%s.json' % SD); kid = D('dong-kidage/%s.json' % SD); K = pf['keys']
sch = [(k, v) for k, v in sp['s'].items() if v[5].startswith(GU)]
cnt = {'학교': len(sch), '보호구역 잡힘': 0, '보호구역 CCTV 값': 0, '보호구역 도로 폭 값': 0, '둘레 업소 1곳 이상': 0, '동 사고 값': 0, '학령 인구 값': 0}
for k, v in sch:
    nm, lo, la, d8 = v[0], v[3], v[4], v[5]
    z = [x for x in cz['items'] if x[3] == nm or x[3] == nm.replace('서울', '')]
    if not z:
        z = sorted([x for x in cz['items'] if x[2] == '초등학교' and dist(la, lo, x[1], x[0]) < 300], key=lambda x: dist(la, lo, x[1], x[0]))[:1]
    if z:
        cnt['보호구역 잡힘'] += 1
        cnt['보호구역 CCTV 값'] += z[0][5] is not None
        cnt['보호구역 도로 폭 값'] += z[0][6] is not None
    cnt['둘레 업소 1곳 이상'] += any(dist(la, lo, x[1], x[0]) < 200 for x in ez['items'])
    cnt['동 사고 값'] += d8 in pf['dong']
    cnt['학령 인구 값'] += d8 in kid['dong']
print('== 학교 레시피(%s)' % GU)
for k, v in cnt.items():
    print('  %-14s %s' % (k, v))
# 보호구역 자료의 CCTV·도로 폭 칸이 시도 전체에서 비었는지
nz = len(cz['items'])
print('  (시도 전체 보호구역 %d곳 중 CCTV 값 %d · 도로 폭 값 %d)' % (nz, sum(1 for x in cz['items'] if x[5] is not None), sum(1 for x in cz['items'] if x[6] is not None)))

dongs = [k for k in pf['dong'] if k.startswith(GU)]
fd = D('foreign-dong.json')['dong']; es = D('esig/%s.json' % SD)['gu'].get(GU, {}).get('dong', {})
rs = D('rescue119/%s.json' % SD); dr = {x[0]: x for x in D({'11': 'dui-ref-seoul.json', '41': 'dui-ref-gg.json', '28': 'dui-ref-incheon.json'}[SD])['items']} if SD in ('11', '41', '28') else {}
c2 = {'동': len(dongs), '외국인 값': 0, '가게 신호 1개 이상': 0, '119 위치 확인 값': 0, '밤 술자리 값': 0}
for d8 in dongs:
    c2['외국인 값'] += d8 in fd
    c2['가게 신호 1개 이상'] += any(r[8] for r in es.get(d8, {}).get('rows', []))
    c2['119 위치 확인 값'] += any(it[9] and any(a[0] == d8 for a in it[9]) for it in rs['items'])
    c2['밤 술자리 값'] += d8 in dr
print('== 동 레시피(%s)' % GU)
for k, v in c2.items():
    print('  %-14s %s' % (k, v))
