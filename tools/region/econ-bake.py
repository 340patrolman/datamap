# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.27.0 — 지역 경제 역추정(코워크 지시 2026-10-06) · 전국
#   ① 국민연금공단 국민연금 가입 사업장 내역(공공데이터포털 15083277 · 사업장 하나하나 · 행정동 코드) → data/econ-dong.json
#      [사업장 수, 가입자 수, 당월 고지금액 합(원), 신규 취득, 상실, 법인 사업장, 50인 이상, 가입자 많은 업종 다섯 [[업종, 가입자]]] · 가입상태 1(등록)만
#   ② 국세청 사업자현황 100대 생활업종 · 연령별 · 존속연수별(15061118 · 15061120 · 15061121 · 시군구 · 매월) → data/econ-gu.json
#      b100 = {업종: [당월, 전년동월]} · dur = {업태: [3년 미만, 10년 이상, 계]} · age = {업태: [40세 미만, 계]} (전체 = 개인+법인 · 당월)
#   원본 = 07_API키/out/ntsfsc_20261006 · out/purchasing (공개 저장소에 안 올림) · py -3.12 -X utf8 tools/region/econ-bake.py
import csv, io, json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); RAW = os.path.join(KB, 'out', 'ntsfsc_20261006')

def text(p):
    b = open(p, 'rb').read()
    for e in ('utf-8-sig', 'cp949'):
        try: return b.decode(e)
        except UnicodeDecodeError: pass
    return b.decode('cp949', 'replace')

def num(v):
    v = (v or '').strip().replace(',', '')
    try: return int(float(v))
    except ValueError: return 0

def last(pat, base=RAW):
    g = sorted(glob.glob(os.path.join(base, pat))); return g[-1] if g else None

def nps():
    p = last('국민연금공단_국민연금 가입 사업장 내역_*.csv', os.path.join(KB, 'out', 'purchasing'))
    rd = csv.reader(io.StringIO(text(p))); hdr = [h.strip() for h in next(rd)]
    def col(pre): return [i for i, h in enumerate(hdr) if h.startswith(pre)][0]
    c = {k: col(v) for k, v in {'ym': '자료생성년월', 'st': '사업장가입상태코드', 'hjd': '고객행정동주소코드', 'type': '사업장형태구분코드', 'ind': '사업장업종코드명', 'mem': '가입자수', 'amt': '당월고지금액', 'new': '신규취득자수', 'lost': '상실가입자수'}.items()}
    A = collections.defaultdict(lambda: [0] * 7); I = collections.defaultdict(lambda: collections.Counter()); ym = None; n = 0
    for r in rd:
        if len(r) < len(hdr) or r[c['st']].strip() != '1': continue
        ym = ym or r[c['ym']].strip(); k = r[c['hjd']].strip()[:8]
        if len(k) < 8: continue
        mem = num(r[c['mem']]); a = A[k]
        a[0] += 1; a[1] += mem; a[2] += num(r[c['amt']]); a[3] += num(r[c['new']]); a[4] += num(r[c['lost']]); a[5] += 1 if r[c['type']].strip() == '1' else 0; a[6] += 1 if mem >= 50 else 0
        nm = r[c['ind']].strip()
        if nm and nm not in ('해당없음', 'BIZ_NO미존재사업장'): I[k][nm] += mem
        n += 1
    out = {'schema': 'tg-econ-dong/1', 'ym': ym, 'source': '국민연금공단 국민연금 가입 사업장 내역(공공데이터포털 15083277 · %s · 가입상태 등록만 · 행정동 = 사업장 소재지)' % ym,
           'fields': 'dong = {행정동 8자리: [사업장 수, 가입자 수, 당월 고지금액 합(원), 신규 취득, 상실, 법인 사업장, 50인 이상 사업장, [[업종, 가입자] 다섯]]}',
           'note': '공무원·사학·군인 연금 대상자는 빠진다 · 본사 일괄신고 사업장은 본사 동에 몰린다 · 고지금액은 기준소득월액 상한이 있어 고소득일수록 낮게 잡힌다',
           'dong': {k: v + [[[q, m] for q, m in I[k].most_common(5)]] for k, v in A.items()}}
    json.dump(out, open(os.path.join(ROOT, 'data', 'econ-dong.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('국민연금', ym, '사업장', n, '행정동', len(A))

def nts():
    G = collections.defaultdict(lambda: {'b100': {}, 'dur': {}, 'age': {}}); asof = ''
    p = last('국세청_사업자현황_100대 생활업종_*.csv'); asof = p.rsplit('_', 1)[-1][:8]
    rd = csv.reader(io.StringIO(text(p))); hdr = [h.strip() for h in next(rd)]; ix = {h: i for i, h in enumerate(hdr)}
    for r in rd:
        if len(r) < len(hdr): continue
        G[r[ix['시도']].strip() + ' ' + r[ix['시군구']].strip()]['b100'][r[ix['업종']].strip()] = [num(r[ix['당월']]), num(r[ix['전년동월']])]
    for pat, key, cat in (('국세청_사업자현황_존속연수별_*.csv', 'dur', '존속연수별'), ('국세청_사업자현황_연령별_*.csv', 'age', '연령별')):
        rd = csv.reader(io.StringIO(text(last(pat)))); hdr = [h.strip() for h in next(rd)]; ix = {h: i for i, h in enumerate(hdr)}
        vi = [i for i, h in enumerate(hdr) if h.startswith('(전체)') and h.endswith('당월')][0]
        for r in rd:
            if len(r) < len(hdr): continue
            g = G[r[ix['시도']].strip() + ' ' + r[ix['시군구']].strip()][key]; up = r[ix['업태별']].strip(); c = r[ix[cat]].strip(); v = num(r[vi])
            t = g.setdefault(up, [0, 0, 0] if key == 'dur' else [0, 0])
            if key == 'dur':
                if c in ('6개월 미만', '6개월 이상', '1년 이상', '2년 이상'): t[0] += v
                if c in ('10년 이상', '20년 이상', '30년 이상'): t[1] += v
                t[2] += v
            else:
                if c in ('30세 미만', '30세 이상'): t[0] += v
                t[1] += v
    out = {'schema': 'tg-econ-gu/1', 'asof': asof, 'source': '국세청 사업자현황 — 100대 생활업종 · 연령별 · 존속연수별(공공데이터포털 15061118 · 15061120 · 15061121 · %s · 시군구 · 개인+법인)' % asof,
           'fields': 'gu = {「시도 시군구」: {b100: {업종: [당월, 전년동월]}, dur: {업태: [3년 미만, 10년 이상, 계]}, age: {업태: [대표자 40세 미만, 계]}}}',
           'note': '시군구 값 — 동으로 나누지 않는다 · 존속연수 「3년 미만」 = 6개월 미만~2년 이상 칸의 합 · 연령 「40세 미만」 = 30세 미만 + 30세 이상(30대)', 'gu': G}
    json.dump(out, open(os.path.join(ROOT, 'data', 'econ-gu.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('국세청', asof, '시군구', len(G))

if __name__ == '__main__': nps(); nts()
