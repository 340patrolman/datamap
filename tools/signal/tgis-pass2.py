# -*- coding: utf-8 -*-
# 🚦 T-GIS 신호현시도 2차 판독 — tgis-raw.ps1 이 남긴 글자 인식(ko·en · 배율 3·4) 네 벌을 칸마다 맞대어 「두 번 이상 같은 값」만 쓴다
#   py -3.12 -X utf8 tools/signal/tgis-pass2.py <원자료 폴더(raw)> <목록 tsv> <결과 폴더>
#   결과: <결과>/<PDF 이름>.json (tod · pat · labels · day · no · bad) · <결과>/_요약.tsv
import json, os, sys, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
sp = importlib.util.spec_from_file_location('tp', os.path.join(HERE, 'tgis-parse.py')); tp = importlib.util.module_from_spec(sp); sp.loader.exec_module(tp)


def one(base):
    ko3, ko4, en3, en4 = ['%s.%s.s%d.json' % (base, k, s) for k, s in (('ko', 3), ('ko', 4), ('en', 3), ('en', 4))]
    R = [tp.parse(ko3), tp.parse(ko4)]
    anc = [tp.anchors(ko3), tp.anchors(ko4)]
    ys = {}
    for r in R:
        for n, q in (r['pat'] or {}).items(): ys.setdefault(n, []).append(q['y'])
    extra = {}
    for f, a in ((en3, 0), (en4, 1)):
        W, w, h = tp.load(f)
        alt = anc[a] if anc[a][0] else anc[1 - a]
        e = tp.parse_words(W, w, h, alt)
        for n, v in ys.items():
            if n not in (e['pat'] or {}): extra.setdefault(n, []).append(tp.off_cell(W, w, n, sum(v) / len(v)))
        R.append(e)
    m = tp.merge_strict(R, extra)
    hd = [r for r in R[:2] if r.get('no')]
    m['no'] = hd[0]['no'] if hd else None
    m['nm'] = next((r['nm'] for r in R[:2] if r.get('nm')), None)
    m['day'] = next((r['day'] for r in R[:2] if r.get('day') and r['day'][:2] == '20'), None)
    lb = [tp.labels(ko3), tp.labels(ko4)]
    m['labels'] = {k: sorted(set(x[k] for x in lb if x and x.get(k))) for k in '1234'}
    sc = {}
    for f in (ko3, ko4, en3, en4):
        if f.endswith(('.ko.s3.json', '.ko.s4.json')):
            for k, v in tp.special(f).items(): sc[k] = sc.get(k, 0) + v
    m['special'] = sc
    return m


def main():
    lst, outdir = sys.argv[2], sys.argv[3]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for line in open(lst, encoding='utf-8').read().split('\n'):
        if not line: continue
        pdf, base = line.split('\t'); b = os.path.basename(base)
        if not os.path.exists(base + '.en.s4.json'): continue
        try: m = one(base)
        except Exception as e: m = {'bad': ['오류 ' + repr(e)[:150]], 'tod': {}, 'pat': {}, 'no': None, 'day': None, 'labels': {}}
        m['file'] = os.path.basename(pdf)
        json.dump(m, open(os.path.join(outdir, b + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        rows.append([b, str(m.get('no') or ''), str(m.get('day') or ''), 'OK' if not m['bad'] else '확인', ' ; '.join(m['bad'][:4])])
    with open(os.path.join(outdir, '_요약.tsv'), 'w', encoding='utf-8') as f:
        f.write('파일\t교차로번호\t시행일\t판정\t까닭\n')
        for r in rows: f.write('\t'.join(r) + '\n')
    for r in rows: print(r[3], r[0], r[4][:110])
    print('OK %d / %d' % (sum(r[3] == 'OK' for r in rows), len(rows)))


if __name__ == '__main__':
    main()
