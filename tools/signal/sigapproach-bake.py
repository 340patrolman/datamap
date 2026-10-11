# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 신호 교차로의 들어오는 쪽마다 어느 길(ITS 링크)인가(소유자 2026-10-11 「방향별로 교통량을 색으로 표시 가능할까 · 원활 증가 정체 등으로 글로 표현」) → data/sig-approach-seocho.json
#   실시간 소통(ITS trafficInfo)은 링크마다 지금 통행속도를 준다 → 신호 카드에서 「북쪽에서 오는 차 = 이 링크들」을 알면 방향별 막힘을 색·글로 낼 수 있다
#   재료 = data/nav-seocho.json(같은 신호 번호 no 로 묶인 노드 · 방향 있는 링크) 하나
#   들어오는 쪽 = 교차로 밖에서 안으로 들어오는 큰길 링크(등급 1~6)의 끝머리 방위의 반대를 8방으로(sigdir 과 같은 이름 nt·ne·et·se·st·sw·wt·nw)
#   한 쪽에 그 링크와, 같은 길로 거슬러 올라간 링크들을 300m 까지 모은다(교차로 바로 앞 한 조각만 보면 짧아서 값이 튄다)
#   py -3.12 -X utf8 tools/signal/sigapproach-bake.py
import json, os, math, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = ['nt', 'ne', 'et', 'se', 'st', 'sw', 'wt', 'nw']
def main():
    nav = json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8')); N = nav['nodes']; L = nav['links']
    grp = collections.defaultdict(set); name = {}
    for k, v in N.items():
        if len(v) > 7 and v[7].get('no'):
            no = v[7]['no']; grp[no].add(k); s = v[7]; name[no] = (s.get('sd') or s.get('tod') or s.get('ksc') or ['', ''])[1]
    inc = collections.defaultdict(list)
    for x in L: inc[x[2]].append(x)
    def brg_end(x):
        c = x[9]; a = b = 0; pts = []
        for k in range(0, len(c), 2): a += c[k]; b += c[k + 1]; pts.append((a / 1e5, b / 1e5))
        p, q = pts[-2], pts[-1]; return math.degrees(math.atan2((q[0] - p[0]) * 88400.0, (q[1] - p[1]) * 111000.0)) % 360
    out = {}
    for no, ns in grp.items():
        side = collections.defaultdict(list)
        for n in ns:
            for x in inc.get(n, ()):
                if x[1] in ns or x[5] > 6: continue
                d = DIRS[int(((brg_end(x) + 180) % 360 + 22.5) // 45) % 8]; ids = [[x[0], x[3]]]; ln = x[3]; cur = x; lim = x[4]
                while ln < 300:   # 같은 길 이름으로 거슬러 올라간다(다른 신호 교차로에 닿으면 멈춘다)
                    up = [y for y in inc.get(cur[1], ()) if y[7] == cur[7] and y[1] != cur[2] and y[5] <= 6]
                    if not up or any(len(N[cur[1]]) > 7 and N[cur[1]][7].get('no') not in (None, no) for _ in [0]): break
                    cur = up[0]; ids.append([cur[0], cur[3]]); ln += cur[3]
                side[d].append([x[7], lim, x[6], round(ln), ids])
        if side: out[no] = {'nm': name.get(no, ''), 'in': {d: v for d, v in sorted(side.items())}}
    doc = {'schema': 'tg-sig-approach/2', 'made': datetime.date.today().isoformat(), 'area': '서초구 + 경계 밖 2km(data/nav-seocho.json 과 같다)',
           'source': 'data/nav-seocho.json — 국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판 · 신호 교차로 묶음(no)',
           'note': ['신호 교차로에 **들어오는 쪽마다** 그 길의 ITS 링크 ID 를 모은 표다 — ITS 실시간 소통(trafficInfo 의 linkId → speed)과 맞대면 방향별 지금 통행속도가 나온다',
                    '들어오는 쪽 이름은 sigdir 과 같다(nt = 북쪽에서 오는 차). 링크 방위로 가른 것이라 대각 교차로에서는 한 칸(45°) 어긋날 수 있다',
                    '한 쪽에 길이 여럿이면(본선·연결로·측도) 줄이 여럿이다 · 링크 묶음은 교차로에서 거슬러 300m 까지(같은 길 이름) — 길이 가중 평균으로 쓰면 된다',
                    '통행속도는 「얼마나 막히나」이지 「몇 대 지나가나(교통량)」가 아니다 — 실시간 교통량은 이 자료로 알 수 없다'],
           'fields': 'spots{신호 교차로 번호: {nm, in{들어오는 쪽: [[길 이름, 제한속도, 차로, 모은 길이 m, [[ITS 링크 ID, 길이 m]…]]…]}}}',
           'spots': out}
    p = os.path.join(ROOT, 'data', 'sig-approach-seocho.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('신호 교차로', len(out), '· 들어오는 쪽', sum(len(v['in']) for v in out.values()), '· 바이트', os.path.getsize(p)); k = '4039'; print(k, json.dumps(out.get(k), ensure_ascii=False)[:600])
if __name__ == '__main__': main()
