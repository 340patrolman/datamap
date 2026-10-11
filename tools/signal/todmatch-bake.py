# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 요일 계획이 지정되지 않은 교차로: 받은 값과 맞는 계획 번호 찾기(게임 세션 2026-10-11 — 이수교차로 1625 처럼 경찰청 계획의 dow 가 계획표에 없는 번호('0')인 곳) → data/sig-tod-match.json
#   경찰청 계획(data/signal-tod-seoul.json)에서 요일이 가리키는 계획 번호가 plans 에 없는 교차로만 본다 — 어느 계획이 도는지 원자료로는 모른다
#   받은 시각대 표(data/sigdir-seoul.json pl — 약한 줄 제외)의 줄마다, 계획 번호마다 「그 시의 계획 줄」(그 시 30분에 도는 줄 · 첫 줄보다 이르면 마지막 줄이 이어짐)과 견준다:
#     주기가 같으면(±1초) 「주기 맞음」 · 옵셋까지 같으면(±3초 · 주기로 나눈 나머지) 「옵셋도 맞음」 — 옵셋은 기준 이동류가 1현시가 아니면 달라지므로 참고로만 센다
#   best = 그 요일 갈래에서 주기 맞은 칸이 **혼자 가장 많고 2칸 이상이며 안 맞은 칸이 0** 인 계획 번호(아니면 null — 지어 고르지 않는다)
#   py -3.12 -X utf8 tools/signal/todmatch-bake.py
import json, os, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def row_at(rows, hr):
    t = '%02d:30' % hr; r = [x for x in rows if x[0] <= t]
    return (r or rows)[-1] if rows else None
def main():
    tod = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']; sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); pl = sd.get('pl', {})
    out = {}; st = collections.Counter()
    for x in tod:
        no = str(x['no']); plans = x.get('plans') or {}
        if not (set(map(str, (x.get('dow') or {}).values())) - set(plans)): continue
        st['요일 계획이 없는 번호인 곳'] += 1; rows = [r for r in pl.get(no, []) if not (len(r) > 6 and r[6])]; by = {}; best = {}
        for cl in (0, 1, 2, 3):
            mine = [r for r in rows if r[0] == cl]
            if not mine: continue
            sc = []
            for pn, prow in sorted(plans.items()):
                okc = oko = bad = 0
                for r in mine:
                    p = row_at(prow, r[1])
                    if p is None: continue
                    if abs(p[1] - r[2]) <= 1:
                        okc += 1; d = abs((p[2] - r[3]) % p[1]) if p[1] else 99; oko += 1 if min(d, p[1] - d) <= 3 else 0
                    else: bad += 1
                sc.append([pn, okc, oko, bad])
            sc.sort(key=lambda z: (-z[1], z[3], -z[2])); by[str(cl)] = sc
            top = [z for z in sc if z[1] == sc[0][1]]
            best[str(cl)] = sc[0][0] if sc and sc[0][1] >= 2 and sc[0][3] == 0 and len(top) == 1 else None
            st['요일 갈래 %d: %s' % (cl, '찾음' if best[str(cl)] else '못 가림')] += 1
        out[no] = {'nm': x.get('name', ''), 'plans': sorted(plans), 'got': len(rows), 'by': by, 'best': best}
        if not rows: st['받은 값이 없는 곳'] += 1
    doc = {'schema': 'tg-sig-tod-match/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': 'data/signal-tod-seoul.json(경찰청 교차로계획정보서비스 · 요일 계획 번호가 계획표에 없는 교차로) × data/sigdir-seoul.json pl(서울 T-Data 로 받은 시각대별 주기·옵셋 · 약한 줄 제외 · %s)' % sd.get('made', ''),
           'note': ['**받은 값과 견줘 찾은 것이다 — 경찰청이 알려 준 요일 계획이 아니다.** 받은 시각대가 늘면 결과가 바뀐다(신호 수집 뒤 다시 굽는다)',
                    'best 는 주기 맞은 칸이 혼자 가장 많고 2칸 이상이며 안 맞은 칸이 0 일 때만 적는다 — 여러 계획이 같은 주기를 쓰는 시각대만 받았으면 못 가린다(null)',
                    '옵셋 맞음은 참고다 — 받은 옵셋은 「기준 이동류가 켜지는 자리」라 그 이동류가 1현시가 아니면 계획표 옵셋과 다르다',
                    '요일 갈래 = 0 월~목 · 1 금 · 2 토 · 3 일(sigdir pl 과 같다)'],
           'fields': 'spots{교차로 번호: {nm, plans[계획표에 있는 번호…], got 받은 시각대 줄 수, by{요일 갈래: [[계획 번호, 주기 맞은 칸, 옵셋도 맞은 칸, 안 맞은 칸]…] 잘 맞는 차례}, best{요일 갈래: 계획 번호 | null}}}',
           'stat': dict(st), 'spots': out}
    p = os.path.join(ROOT, 'data', 'sig-tod-match.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print(dict(st), '· 바이트', os.path.getsize(p))
    for no, v in out.items():
        if v['got']: print(' ', no, v['nm'], '받은 줄', v['got'], 'best', v['best'], {k: z[:3] for k, z in v['by'].items()})
if __name__ == '__main__': main()
