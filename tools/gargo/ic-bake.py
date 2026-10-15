# -*- coding: utf-8 -*-
"""가르고 「고속도로 모드」 나들목 목록 — gargo/ic-capital.json (2026-10-15 · 소유자 「카카오네비 스타일 · 권고대로 계속 진행」)

자료 = data/nav-express.json(국가교통정보센터 ITS 표준노드링크 2026-09-14판 · 수도권 고속·도시고속과 그 나들목)의 마디 이름
  이름 끝이 IC·JC·JCT·TG·분기점·나들목·휴게소·졸음쉼터 인 마디만(「(남측)」 같은 방향 꼬리는 떼고) · 주유소·아파트·교차로·입구·교(다리) 이름은 뺀다
  같은 이름은 한 줄로 묶고 그 이름 마디 자리를 모두(가장 먼 것끼리 3km 넘으면 다른 곳 — 이름 뒤에 번호) · 가르고는 안내 중 길에서 40m 안에 드는 것을 「앞으로 나올 나들목」으로 쓴다
  py -3.12 -X utf8 tools/gargo/ic-bake.py
"""
import os, re, json, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'data', 'nav-express.json')
OUT = os.path.join(ROOT, 'gargo', 'ic-capital.json')
END = re.compile(r'(IC|JC|JCT|TG|분기점|나들목|휴게소|졸음쉼터)$')
BAD = re.compile(r'(주유소|아파트|화장실|셀프|\d+-\d+|육교|입구|교차로|삼거리|사거리|앞$)')


def kind(nm):
    for k, v in (('휴게소', '휴게소'), ('졸음쉼터', '쉼터'), ('TG', 'TG'), ('JCT', 'JC'), ('JC', 'JC'), ('분기점', 'JC'), ('IC', 'IC'), ('나들목', 'IC')):
        if nm.endswith(k):
            return v
    return 'IC'


def main():
    j = json.load(open(SRC, encoding='utf-8'))
    by = {}
    for v in j['nodes'].values():
        nm = (v[3] or '').strip()
        nm = re.sub(r'\((남|북|동|서|상|하)(측|행|방향)?\)$', '', nm).strip()
        if not nm or BAD.search(nm) or not END.search(nm):
            continue
        by.setdefault(nm, []).append((round(v[0], 6), round(v[1], 6)))
    out = []
    for nm, P in sorted(by.items()):
        groups = []
        for p in P:   # 같은 이름이 서로 3km 넘게 떨어지면 다른 곳(예: 같은 이름의 휴게소 두 방향은 가깝다)
            for g in groups:
                if math.hypot((p[0] - g[0][0]) * 88800, (p[1] - g[0][1]) * 111000) < 3000:
                    g.append(p); break
            else:
                groups.append([p])
        for g in groups:
            out.append([nm, kind(nm), [list(p) for p in g[:8]]])
    doc = {'schema': 'tg-gargo-ic/1', 'made': datetime.date.today().isoformat(), 'source': '국가교통정보센터(ITS) 전국 표준노드링크 2026-09-14판 — data/nav-express.json 마디 이름 · 굽는 도구 tools/gargo/ic-bake.py',
           'fields': 'pts[[이름, 갈래 IC·JC·TG·휴게소·쉼터, [[경도, 위도] … 그 이름 마디 자리(8개까지)]]]',
           'note': '이름 끝으로 고른 것이라 빠진 나들목이 있을 수 있다 · 가르고는 길에서 40m 안에 드는 것만 쓴다', 'pts': out}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    c = {}
    for x in out:
        c[x[1]] = c.get(x[1], 0) + 1
    print('→', OUT, len(out), '곳', c, os.path.getsize(OUT), 'B')


if __name__ == '__main__':
    main()
