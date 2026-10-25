# -*- coding: utf-8 -*-
# 반포 터미널 블록 신호·수요 시뮬레이터 자료(2026-10-25 · intent/20261025-banpo-block-sim.md · 소유자 「1단계 권고대로 진행」)
#   교차로 넷(4031 강남터미널고가밑 · 4019 고속터미널 · 4028 삼호가든 · 4034 서울성모병원) + 블록 둘레 길 + 반포대교남단 갈림
#   값마다 출처 칸(src)을 단다 — 「현시도」(교통과 출력물 · sig-ksc-seocho) · 「T-Data」(방향별 신호 실측 · sigdir) · 「노드링크」(국가표준 MOCT_LINK 차로)
#   · 「좌표」(교차로 좌표 사이 직선거리) · 「조사」(서울시 교통량 조사 · traffic-vol-seoul) · 「설계값」(자료 없음 — 화면에서 막대로 바꾼다)
#   지도·가르고는 이 파일을 읽지 않는다 — js/sim.js 만 읽는다
# 쓰기: py -3.12 -X utf8 tools/sim/banpo-bake.py   →  data/sim-banpo.json
import json, math, os, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, 'data')
SIG = ['4031', '4019', '4028', '4034']
# 노드링크(MOCT_LINK) 교차로마다 들어오는 첫 구간의 차로 수 — 2026-10-25 regionwork/nl 에서 읽음(교차로 노드 묶음 12100417·12100438·12100412·12100373)
#   신반포로는 중앙버스전용차로(현시도 roads 「신반포로(중앙버스전용차로)」) — 노드링크 차로에서 1 을 뺀 값이 일반 차로(BUS)
LANES = {'4031': {'nt': 3, 'et': 4, 'st': 3, 'wt': 3}, '4019': {'nt': 3, 'et': 2, 'st': 4, 'wt': 4},
         '4028': {'nt': 4, 'et': 4, 'st': 3, 'wt': 4}, '4034': {'nt': 4, 'et': 2, 'st': 4, 'wt': 2}}
# 바깥에서 들어오는 길의 저장 길이(대기열이 이만큼 차면 망 밖에서 기다린다) — 노드링크 상류 구간 길이 · 600m 넘으면 600(설계값)
BUS = {('4031', 'et'), ('4031', 'wt'), ('4019', 'wt'), ('4019', 'et')}
for n9, l9 in BUS: LANES[n9][l9] -= 1
OUTLEN = {('4031', 'wt'): 600, ('4019', 'et'): 600, ('4019', 'nt'): 398, ('4028', 'et'): 600, ('4028', 'st'): 351,
          ('4034', 'wt'): 600, ('4034', 'st'): 434}
NAME = {('4031', 'nt'): '반포대로(반포대교 쪽)', ('4031', 'wt'): '신반포로(신반포역 쪽)', ('4019', 'nt'): '잠원로(북)', ('4019', 'et'): '신반포로(반포역 쪽)',
        ('4028', 'et'): '사평대로(사평역 쪽)', ('4028', 'st'): '서초중앙로(남)', ('4034', 'wt'): '사평대로(서래마을 쪽 · 지상)', ('4034', 'st'): '반포대로(서초역 쪽)'}
OPP = {'nt': 'st', 'st': 'nt', 'et': 'wt', 'wt': 'et'}
MVNO = {1: ('et', 'Lt'), 2: ('wt', 'St'), 3: ('st', 'Lt'), 4: ('nt', 'St'), 5: ('wt', 'Lt'), 6: ('et', 'St'), 7: ('nt', 'Lt'), 8: ('st', 'St')}


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111000, (a[1] - b[1]) * 111000 * math.cos(math.radians(37.5)))


def main():
    ksc = {i['no']: i for i in json.load(open(os.path.join(D, 'sig-ksc-seocho.json'), encoding='utf-8'))['items']}
    ix = json.load(open(os.path.join(D, 'sigdir', 'index.json'), encoding='utf-8'))['pts']
    XY = {n: ((ksc[n]['lat'], ksc[n]['lon']) if n in ksc else (ix[n][0], ix[n][1])) for n in SIG}
    XY['4032'] = (ix['4032'][0], ix['4032'][1])
    nodes, links = {}, {}

    def link(i, fr, to, ln, lanes, nm, src, **kw):
        links[i] = dict(id=i, fr=fr, to=to, len=round(ln), lanes=lanes, nm=nm, src=src, **kw)

    # ---- 신호 교차로 넷 ----
    for n in ['4031', '4028', '4034']:
        k = ksc[n]
        nodes[n] = {'id': n, 'nm': k['nm'], 'ty': 'sig', 'll': list(XY[n]), 'plan': {'src': '현시도', 'day': k['day'], 'tod': k['tod'], 'pat': k['pat'],
                    'Y': k['Y'], 'AR': k['AR'], 'ph': [[MVNO[m][0] + '.' + MVNO[m][1] for m in p['mv'] if m in MVNO] for p in k['ph']],
                    'dir': {p: [[r[0] + '.' + r[1], r[3], r[4], r[6]] for r in L if r[3] is not None] for p, L in k['dir'].items()}}, 'legs': {}}
    # 4019 고속터미널 — 현시도 없음 → T-Data 방향별 실측 · 일요일 저녁(2026-10-18 21:00 기록 · 주기 175초) · 비어 있는 이동류는 다른 날 같은 꼴로 채움(fill)
    rec = None
    for f in glob.glob(os.path.join(D, 'sigdir', 'c', '*.json')):
        its = json.load(open(f, encoding='utf-8'))['its']
        if '4019' in its:
            rec = [r for r in its['4019'] if r['day'] == '2026-10-18' and r.get('from') == '21:00'][0]
    W = {m[0] + '.' + m[1]: [m[2], m[3], m[5]] for m in rec['mv'] if m[1] in ('St', 'Lt') and m[2] is not None}
    fill = []
    if 'et.St' not in W: W['et.St'] = list(W['wt.St']); fill.append('et.St = wt.St(10-21·10-25 기록에서 둘이 같다)')
    if 'st.Lt' not in W:   # 10-21·10-25 기록: 남→서 좌회전은 북쪽 녹색이 끝난 뒤 남→북 직진 끝까지
        s0 = round(W['nt.St'][0] + 3 + 1); W['st.Lt'] = [round(W['st.St'][0] - s0, 1), 3.0, s0]; fill.append('st.Lt = 북 녹색 끝(+황색 3·전적색 1) ~ 남→북 직진 끝(10-21·10-25 기록의 꼴)')
    nodes['4019'] = {'id': '4019', 'nm': '고속터미널', 'ty': 'sig', 'll': list(XY['4019']), 'plan': {'src': 'T-Data', 'day': '2026-10-18 21:00(일)', 'cyc': rec['cyc'],
                     'win': [[k, round(v[0], 1), v[1], v[2]] for k, v in sorted(W.items(), key=lambda kv: kv[1][2])], 'fill': fill}, 'legs': {}}
    # ---- 블록 둘레 안쪽 길(양방향) ----
    # 신반포로 4031↔4019 는 신세계 쪽 문(진입 G · 진출 X)에서 둘로 나눈다 — 문 자리는 미결 질문(형님 현장 확인) · 지금은 4031 에서 200m(설계값)
    d3119 = dist(XY['4031'], XY['4019'])
    GATE = 200
    nodes['G'] = {'id': 'G', 'nm': '신세계 들어가는 문(설계값 자리)', 'ty': 'gate', 'll': [XY['4031'][0] + (XY['4019'][0] - XY['4031'][0]) * GATE / d3119, XY['4031'][1] + (XY['4019'][1] - XY['4031'][1]) * GATE / d3119]}
    nodes['X'] = {'id': 'X', 'nm': '신세계 나오는 문(설계값 자리)', 'ty': 'merge', 'll': list(nodes['G']['ll'])}
    link('4031>G', '4031', 'G', GATE, LANES['4019']['wt'], '신반포로(4031→신세계 문)', '좌표·노드링크 · 문 자리 설계값', ofr='et')
    link('G>4019', 'G', '4019', d3119 - GATE, LANES['4019']['wt'], '신반포로(신세계 문→고속터미널)', '좌표·노드링크', oto='wt')
    link('4019>X', '4019', 'X', d3119 - GATE, LANES['4031']['et'], '신반포로(고속터미널→신세계 문)', '좌표·노드링크', ofr='wt')
    link('X>4031', 'X', '4031', GATE, LANES['4031']['et'], '신반포로(신세계 문→4031)', '좌표·노드링크 · 문 자리 설계값', oto='et')
    # 반포대로 4034→4031 은 반포대교 고가로 오르는 갈림(H)이 중간에 있다(노드링크 「반포대교고가차도(남측)」) — 갈림 자리 = 4034 에서 절반(설계값)
    d3431 = dist(XY['4034'], XY['4031'])
    nodes['H'] = {'id': 'H', 'nm': '반포대교 고가 오르는 갈림', 'ty': 'div', 'll': [(XY['4034'][0] + XY['4031'][0]) / 2, (XY['4034'][1] + XY['4031'][1]) / 2]}
    link('4034>H', '4034', 'H', d3431 / 2, LANES['4031']['st'], '반포대로(서울성모병원→고가 갈림)', '좌표·노드링크 · 갈림 자리 설계값', ofr='nt')
    link('H>4031', 'H', '4031', d3431 / 2, LANES['4031']['st'], '반포대로(고가 갈림→4031 · 고가 아래)', '좌표·노드링크', oto='st')
    link('H>up', 'H', None, 0, 2, '반포대교 고가로(블록을 비켜 감)', '노드링크', sink=1)
    link('4031>4034', '4031', '4034', d3431, LANES['4034']['nt'], '반포대로(4031→서울성모병원 · 고가 아래)', '좌표·노드링크', ofr='st', oto='nt')
    for a, b, la, lb, nm in [('4019', '4028', 'st', 'nt', '잠원로·서초중앙로'), ('4028', '4034', 'wt', 'et', '사평대로')]:
        d0 = dist(XY[a], XY[b])
        link(a + '>' + b, a, b, d0, LANES[b][lb], nm + '(' + a + '→' + b + ')', '좌표·노드링크', ofr=la, oto=lb)
        link(b + '>' + a, b, a, d0, LANES[a][la], nm + '(' + b + '→' + a + ')', '좌표·노드링크', ofr=lb, oto=la)
    # ---- 반포대교남단 4032 ----
    d3132 = dist(XY['4031'], XY['4032'])
    nodes['4032'] = {'id': '4032', 'nm': '반포대교남단(한강공원 갈림)', 'ty': 'split', 'll': list(XY['4032'])}
    link('4031>4032', '4031', '4032', d3132, LANES['4031']['nt'], '반포대로(4031→반포대교남단)', '좌표·노드링크', ofr='nt')
    link('4032>4031', '4032', '4031', d3132, LANES['4031']['nt'], '반포대로(반포대교남단→4031 · 고가 아래)', '좌표·노드링크', oto='nt', src_in=1)
    link('park', '4032', None, 0, 1, '반포한강공원(분수) 들어가는 길', '설계값', sink=1, park=1)
    link('bridge', '4032', None, 0, 3, '반포대교로 빠짐', '노드링크', sink=1)
    # ---- 바깥 길(들어오는 길 · 나가는 길) ----
    for (n, lg), ln in OUTLEN.items():
        link('in.' + n + '.' + lg, None, n, ln, LANES[n][lg], NAME[(n, lg)] + ' — 들어옴', '노드링크 · 길이 600m 넘으면 600(설계값)', oto=lg, src_in=1)
        link('out.' + n + '.' + lg, n, None, 0, LANES[n][lg], NAME[(n, lg)] + ' — 나감', '노드링크', ofr=lg, sink=1)
    # 4034 동쪽에서 오는 사평대로는 사평지하차도로 4034 아래를 지난다(노드링크 「사평지하차도(동측)」 · 현시도에 동쪽 진입 현시가 없다) → 직진은 신호 없이 서쪽으로
    link('out.4034.wt', '4034', None, 0, 4, '사평대로(서래마을 쪽) — 나감(지하차도 포함)', '노드링크', ofr='wt', sink=1)
    # 다리(legs) 채우기
    for L in links.values():
        if L.get('oto') and L['to'] in nodes: nodes[L['to']]['legs'].setdefault(L['oto'], {})['in'] = L['id']
        if L.get('ofr') and L['fr'] in nodes: nodes[L['fr']]['legs'].setdefault(L['ofr'], {})['out'] = L['id']
    nodes['4034']['free'] = ['et.St']   # 지하차도
    # ---- 교통량 조사(서울시 · 시간당 대수 · 두 방향) ----
    vol = {s['id']: {k: s[k] for k in ('name', 'lat', 'lon', 'wd', 'sa', 'su', 'lanes')} for s in json.load(open(os.path.join(D, 'traffic-vol-seoul.json'), encoding='utf-8'))['spots'] if s['id'] in ('D-36', 'D-37', 'C-11')}
    volsrc = json.load(open(os.path.join(D, 'traffic-vol-seoul.json'), encoding='utf-8'))['note']
    # ---- 들어오는 수요(대/시) — 조사 지점 값 × 지상 몫(설계값) 또는 차로 × 차로당(설계값) ----
    entry = {
        'in.4031.wt': {'perLane': 350, 'src': '설계값 — 신반포로 조사 지점 없음 · 차로 × 차로당 대수'},
        'in.4019.et': {'perLane': 350, 'src': '설계값 — 조사 지점 없음'},
        'in.4019.nt': {'perLane': 300, 'src': '설계값 — 조사 지점 없음'},
        'in.4028.st': {'perLane': 350, 'src': '설계값 — 서초중앙로 조사 지점 없음'},
        'in.4028.et': {'spot': 'D-36', 'share': 1.0, 'src': '조사 D-36 사평대로(고속터미널역) 두 방향 평균 · 몫 1(설계값)'},
        'in.4034.wt': {'spot': 'D-36', 'share': 0.2, 'src': '조사 D-36 두 방향 평균 × 지상 몫 0.2(설계값 — 나머지는 사평지하차도)'},
        'in.4034.st': {'spot': 'D-37', 'share': 0.7, 'src': '조사 D-37 반포대로(서초역) 두 방향 평균 × 0.7(설계값)'},
        '4032>4031': {'spot': 'C-11', 'share': 0.4, 'src': '조사 C-11 반포대교 두 방향 평균 × 지상 몫 0.4(설계값 — 나머지는 반포대교 고가)'},
    }
    # ---- 설계값(화면 막대 · 바꿀 수 있다) ----
    design = {
        'turn': {'Lt': 0.15, 'Rt': 0.15, 'src': '설계값 — 회전 비율 조사 없음(좌·우 각 15% · 나머지 직진)'},
        'rtRed': {'v': 0.5, 'src': '설계값 — 우회전은 적색에도 이 몫만큼 빠진다(보행자·일시정지)'},
        'lostStart': {'v': 2, 'src': '설계값 — 녹색 처음 2초는 출발 손실'},
        'freeV': {'v': 30, 'src': '설계값 — 막히지 않을 때 블록 둘레 주행 속도(km/h)'},
        'box': {'v': 0.3, 'src': '설계값 — 하류가 찼는데도 교차로 안으로 들어가는(꼬리물기) 차 비율'},
    }
    # 신호 없는 갈림·합류 — p = 갈림에서 그쪽으로 가는 몫(설계값)
    mvx = [{'node': 'G', 'key': 'thru', 'fr': '4031>G', 'to': 'G>4019', 'la': links['G>4019']['lanes']},
           {'node': 'X', 'key': 'thru', 'fr': '4019>X', 'to': 'X>4031', 'la': links['X>4031']['lanes']},
           {'node': 'H', 'key': 'thru', 'fr': '4034>H', 'to': 'H>4031', 'la': links['H>4031']['lanes'], 'p': 0.4},
           {'node': 'H', 'key': 'up', 'fr': '4034>H', 'to': 'H>up', 'la': 2, 'p': 0.6, 'src': '설계값 — 4034 에서 북쪽으로 가는 차 가운데 반포대교 고가로 오르는 몫 0.6'},
           {'node': '4032', 'key': 'bridge', 'fr': '4031>4032', 'to': 'bridge', 'la': 3}]
    # 끌어들이는 곳 — 대수 자료 없음 · 전부 설계값(막대)
    att = [{'id': 'shin', 'nm': '신세계(블록 안 주차장)', 'mode': 'store', 'node': 'G', 'inFrom9': '4031>G', 'inCap': 1200, 'outLink': 'X>4031',
            'inPeak': 900, 'inT0': 15, 'inT1': 19, 'outPeak': 900, 'outT0': 17, 'outT1': 21,
            'from': {'in.4031.wt': 0.3, '4032>4031': 0.25, 'in.4034.st': 0.25, 'in.4019.et': 0.2},
            'src': '설계값 — 신세계 입차·출차 대수 자료 없음(대/시 · 막대) · 문 자리 = 신반포로 4031 에서 200m(미결 질문)'},
           {'id': 'fount', 'nm': '반포한강공원 분수', 'mode': 'hold', 'node': '4032', 'inFrom9': '4031>4032', 'inCap': 500, 'outLink': '4032>4031',
            'inPeak': 700, 'inT0': 18.5, 'inT1': 19.75, 'outT0': 21.0, 'outT1': 21.75, 'outRate': 500,
            'from': {'in.4034.st': 0.4, 'in.4031.wt': 0.3, 'in.4019.et': 0.3},
            'src': '설계값 — 분수(10월 19:30~21:00) 보러 오는 차 대수 자료 없음 · 공원 주차장 받는 속도 500대/시'}]
    actions = [{'id': 'cone4032', 'nm': '라바콘 — 반포대교남단 갈림(내려오는 차를 고가로)', 'closeEntry': ['4032>4031'], 'src': '앱 가정 — 라바콘 자리·효과는 형님 확인 필요'},
               {'id': 'coneH', 'nm': '라바콘 — 고가 진입 전 갈림(남쪽에서 북쪽으로 가는 차를 고가로)', 'mvp': {'4034>H>H>up': 1, '4034>H>H>4031': 0}, 'src': '앱 가정 — 형님 확인 필요'},
               {'id': 'rain', 'nm': '비(분수 정지)', 'attOff': ['fount']},
               {'id': 'shinStop', 'nm': '백화점 입차 중단', 'attInStop': ['shin']},
               {'id': 'shinOutFirst', 'nm': '백화점 출차 우선', 'attOutFirst': ['shin']}]
    preset = {'1018': {'date': '2026-10-18', 'att': {'shin': {'inPeak': 1500, 'outPeak': 1500}, 'fount': {'inPeak': 700}}, 'nm': '10/18(일) 재현 — 신세계 입·출 1,500대/시 · 분수 700대/시'},
              '1011': {'date': '2026-10-11', 'att': {'shin': {'inPeak': 600, 'outPeak': 600}, 'fount': {'inPeak': 600}}, 'nm': '10/11(일) 평소 — 신세계 입·출 600대/시 · 분수 600대/시'},
              'src': '설계값 — 신세계·분수 막대만 움직여 실측 속도(ITS · 07_API키/out/livespd)의 막힘 모양에 맞춘 값 · 대수 자료가 아니다(tools/sim/sim-check.py diag 가 맞대 본다)'}
    sat = {'v': 2200, 'unit': '대/녹색 1시간/차로', 'src': '2차 자료', 'quote': '신호교차로 기본 조건에서 포화교통류율 2,200pcphgpl — 도로용량편람(2013) p.427',
           'note': '편람 원문 직접 대조 못 함 — 게임 queueModel 과 같은 값 · 기본 조건이라 실제는 더 적게 빠진다'}
    spacing = {'v': 7.5, 'unit': 'm/대', 'src': '설계값', 'note': '정지 차량 한 대가 차지하는 길이 — 실측 아님(게임 queueModel 과 같은 값)'}
    doc = {'schema': 'tg-sim/2', 'area': 'banpo', 'nm': '반포 터미널 블록', 'date0': '2026-10-18', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'about': '반포 터미널 블록 신호·수요 시뮬레이터(개념 시연 — 예측·보증 아님) · intent/20261025-banpo-block-sim.md',
           'nodes': nodes, 'links': links, 'vol': vol, 'volNote': volsrc, 'entry': entry, 'design': design, 'mvx': mvx, 'att': att, 'actions': actions, 'preset': preset, 'sat': sat, 'spacing': spacing,
           'mv': '이동류 키 = 들어오는 쪽.회전(nt 북 · et 동 · st 남 · wt 서 / St 직진 · Lt 좌회전 · Rt 우회전) · dir 줄 = [이동류, 녹색 초, 황색 초, 녹색 시작(1현시 시작 = 0)]',
           'off': '옵셋 = 자정부터 센 1현시 시작(가설 A — tbook-signal 현장 측정 4036 에서 맞음) · 패턴 바뀜은 시각이 지난 뒤 다음 1현시부터'}
    out = os.path.join(D, 'sim-banpo.json')
    json.dump(doc, open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('ok', out, os.path.getsize(out), 'B · 교차로', len(nodes), '· 길', len(links), '· 4019 채움', fill)


if __name__ == '__main__':
    main()
