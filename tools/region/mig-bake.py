# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.93.0 — 🔀 동별 전입·전출 → data/mig-dong.json (지도 「🔮 인구 5년·10년 뒤」·업종 칸의 전입·전출 보정)
#   원자료 = 07_API키/out/mig/*.csv (코워크가 받는다 · 행정안전부 주민등록 인구이동 등 · UTF-8 또는 CP949)
#   열 이름은 글자로 찾는다 — 「코드」(행정동 코드 10자리 또는 8자리) · 「연도/기간/년월」(YYYY 또는 YYYYMM) · 「전입」 · 「전출」 · (있으면) 「인구/주민」
#     같은 열 이름에 「시도」·「구」 묶음 줄이 섞여 있으면 코드 끝이 00 인 묶음은 건너뛴다(동 줄만 쓴다)
#   계산: 동마다 최근 3년(달 자료면 최근 36달)을 해마다로 고친 평균 전입·전출 · 주민 = 원자료 「인구」 열 평균, 없으면 data/r/<구>/dong.json 의 주민
#         시군구 = 그 동들을 더한 값(구 안 이사는 한 동의 전입·다른 동의 전출로 서로 지워진다)
#   py -3.12 -X utf8 tools/region/mig-bake.py [출처 글] [원자료 폴더]
#   지도 쪽 공식(js ppMig): d = 동 순이동률 − 구 순이동률 · 10년 배율 = (1 + d × 0.5)^10 을 0.7~1.3 으로 자름(설계값)
import csv, glob, io, json, os, re, sys, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
SRC = sys.argv[1] if len(sys.argv) > 1 else '행정안전부 주민등록 인구통계 — 행정동 전입·전출'
IN = sys.argv[2] if len(sys.argv) > 2 else os.path.join(KB, 'out', 'mig')
OUTF = os.path.join(ROOT, 'data', 'mig-dong.json')
num = lambda v: float(re.sub(r'[^\d.\-]', '', str(v)) or 0)

def rows(fp):
    raw = open(fp, 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):
        try: txt = raw.decode(enc); break
        except UnicodeDecodeError: continue
    r = list(csv.reader(io.StringIO(txt)))
    hi = next(i for i, x in enumerate(r) if any('전입' in c for c in x) and any('전출' in c for c in x))
    H = [c.strip() for c in r[hi]]
    col = lambda *ks: next((i for i, c in enumerate(H) if any(k in c for k in ks)), None)
    ck, cp, ci, co, cn = col('코드'), col('연도', '기간', '년월', '시점'), col('전입'), col('전출'), col('인구', '주민')
    if None in (ck, cp, ci, co): raise SystemExit('%s: 열을 못 찾음 %s' % (fp, H))
    for x in r[hi + 1:]:
        if len(x) <= max(ck, cp, ci, co): continue
        k = re.sub(r'\D', '', x[ck])
        if len(k) < 8 or k[5:8] == '000': continue
        if len(k) >= 10 and k[8:10] != '00': continue
        yield k[:8], re.sub(r'\D', '', x[cp]), num(x[ci]), num(x[co]), (num(x[cn]) if cn is not None and x[cn].strip() else None)

def main():
    fs = sorted(glob.glob(os.path.join(IN, '*.csv')))
    if not fs: raise SystemExit('원자료 없음: ' + IN)
    D = collections.defaultdict(dict)
    for fp in fs:
        for k, per, i, o, n in rows(fp):
            a = D[k].setdefault(per, [0, 0, None]); a[0] += i; a[1] += o
            if n is not None: a[2] = n
    pers = sorted({p for v in D.values() for p in v})
    monthly = all(len(p) == 6 for p in pers)
    use = pers[-36:] if monthly else pers[-3:]
    scale = 12.0 / len(use) if monthly else 1.0 / len(use)
    years = sorted({p[:4] for p in use})
    popc = {}
    def pop_of(k):
        g = k[:5]
        if g not in popc:
            f = os.path.join(ROOT, 'data', 'r', g, 'dong.json'); popc[g] = {}
            if os.path.exists(f):
                for q in json.load(open(f, encoding='utf-8')).get('dong', []):
                    if q.get('k') and q.get('pop'): popc[g][q['k']] = q['pop'].get('tot')
        return popc[g].get(k)
    dong, gu, miss = {}, collections.defaultdict(lambda: [0.0, 0.0, 0.0]), 0
    for k, v in D.items():
        got = [v[p] for p in use if p in v]
        if len(got) < len(use) * 0.75: continue
        sc = 12.0 / len(got) if monthly else 1.0 / len(got)
        i = sum(x[0] for x in got) * sc; o = sum(x[1] for x in got) * sc
        ns = [x[2] for x in got if x[2]]; n = sum(ns) / len(ns) if ns else pop_of(k)
        if not n: miss += 1; continue
        dong[k] = [round(i), round(o), round(n)]
        g = gu[k[:5]]; g[0] += i; g[1] += o; g[2] += n
    doc = {'schema': 'tg-migdong/1', 'source': SRC, 'years': years, 'per': '%s %s~%s' % ('달' if monthly else '해', use[0], use[-1]),
           'fields': 'dong = {행정동 8자리: [해마다 전입, 해마다 전출, 주민]} · gu = {시군구 5자리: 동 합}',
           'note': '해마다 = 최근 %s 평균 · 구 안 이사는 동 합에서 지워진다 · 지도는 (동 순이동률 − 구 순이동률)의 절반이 10년 이어진다고 보고 0.7~1.3배로 자른다(설계값)' % ('36달' if monthly else '3년'),
           'dong': dong, 'gu': {g: [round(v[0]), round(v[1]), round(v[2])] for g, v in gu.items()}}
    json.dump(doc, open(OUTF, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('동 %d · 시군구 %d · 주민 없어 뺀 동 %d · %s → %s (%.0f KB)' % (len(dong), len(doc['gu']), miss, doc['per'], OUTF, os.path.getsize(OUTF) / 1024))

if __name__ == '__main__':
    main()
