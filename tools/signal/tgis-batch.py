# -*- coding: utf-8 -*-
# 🚦 T-GIS 신호현시도 PDF 폴더 → 글자 인식 네 번(배율 3 · 배율 4 · 표만 잘라 1배 · 1.5배) → 칸마다 맞대어 값 · 검산
#   소유자 2026-11-28 「T-GIS 신호값을 지도에 평문으로 · 서울 전체」
#   py -3.12 -X utf8 tools/signal/tgis-batch.py <PDF 폴더> <결과 폴더> [--redo]
#   결과: <결과>/<PDF 이름>.json (값 · bad 목록) · <결과>/_요약.tsv
#   PDF·그림·결과는 저장소 밖(07_API키)에만 둔다 — 원본 현시도는 공개하지 않는다
import json, os, sys, subprocess, glob, importlib.util, tempfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PS1 = os.path.join(HERE, 'tgis-ocr.ps1')
sp = importlib.util.spec_from_file_location('tp', os.path.join(HERE, 'tgis-parse.py')); tp = importlib.util.module_from_spec(sp); sp.loader.exec_module(tp)


def ps(*args):
    r = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', PS1] + list(args), capture_output=True, text=True, encoding='cp949', errors='replace', timeout=600)
    if r.returncode: raise RuntimeError((r.stdout + r.stderr)[-400:])


def crops(png, tmp):
    im = Image.open(png).convert('L'); W, H = im.size
    boxes = {'tod': (int(W * .04), int(H * .37), int(W * .82), int(H * .71)), 'pat': (int(W * .04), int(H * .63), int(W * .57), int(H * .985))}
    out = []
    for z in (1.0, 1.5):
        for k, b in boxes.items():
            c = im.crop(b)
            if z != 1.0: c = c.resize((int(c.width * z), int(c.height * z)), Image.LANCZOS)
            f = os.path.join(tmp, '%s_%s.png' % (k, z)); c.save(f); out.append((f, b, z))
    return out, W, H


def fill(m, c):
    """전체 판독 두 번이 못 읽은 칸만 잘라 읽기(두 번이 같은 값)로 메운다 — 잘라 읽기는 투표하지 않는다"""
    T = dict(m['tod']); P = {k: dict(v) for k, v in m['pat'].items()}; done = set()
    for k in '1234':
        if any(x == 'TOD%s 못 읽음' % k or x.startswith('TOD%s 읽을 때마다' % k) for x in m['bad']) and not any(x.startswith('TOD%s ' % k) and ('못' in x or '다름' in x) for x in c['bad']) and c['tod'].get(k):
            T[k] = c['tod'][k]; done.add('TOD%s ' % k)
    for n, q in c['pat'].items():
        bn = [x for x in c['bad'] if x.startswith('패턴%s ' % n)]
        if bn: continue
        if n not in P: P[n] = q; done.add('패턴%s ' % n)
        elif P[n]['off'] is None and P[n]['a'] == q['a'] and P[n]['b'] == q['b']: P[n]['off'] = q['off']; done.add('패턴%s 연동 못' % n)
    keep = [x for x in m['bad'] if not any(x.startswith(d) for d in done) and not x.startswith('패턴 ') and ' ≠ 패턴' not in x and ' 없음' not in x]
    bad = [x for x in keep if not x.endswith('못 읽음') or not x.startswith('TOD')]
    for k in '1234':
        if not T.get(k): bad.append('TOD%s 못 읽음' % k)
    for n, q in P.items():
        if q['off'] is None: bad.append('패턴%s 연동 못 읽음' % n)
        if sum(q['a']) != sum(q['b']): bad.append('패턴%s A합 ≠ B합' % n)
    if len(P) != 16: bad.append('패턴 %d개' % len(P))
    bad += tp.check(T, P)
    out = dict(m); out['tod'] = T; out['pat'] = P; out['bad'] = sorted(set(bad))
    return out


def one(pdf, outdir, tmp):
    b = os.path.splitext(os.path.basename(pdf))[0]
    j3 = os.path.join(tmp, 's3.json'); j4 = os.path.join(tmp, 's4.json'); png = os.path.join(tmp, 's3.png'); jc = os.path.join(tmp, 'c.json')
    ps('-Pdf', pdf, '-Out', j3, '-Scale', '3', '-Png', png)
    ps('-Pdf', pdf, '-Out', j4, '-Scale', '4')
    R = [tp.parse(j3), tp.parse(j4)]
    m = tp.merge_n(R)
    if not m['bad']:
        m['file'] = os.path.basename(pdf); m['how'] = 'page2'
        json.dump(m, open(os.path.join(outdir, b + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        return m
    cl, W, H = crops(png, tmp)
    ps('-Out', jc, '-Img', '|'.join(c[0] for c in cl))
    got = json.load(open(jc, encoding='utf-8-sig'))
    if isinstance(got, dict): got = [got]
    for z in (1.0, 1.5):
        words = []
        for (f, bx, zz), g in zip(cl, got):
            if zz != z: continue
            for t, x, y, w, h in g['words']:
                words.append([t, int(bx[0] + x / z), int(bx[1] + y / z), int(w / z), int(h / z)])
        R.append(tp.parse_words(words, W, H))
    m = fill(m, tp.merge_n(R[2:]))
    m['how'] = 'page2+crop'
    m['file'] = os.path.basename(pdf)
    json.dump(m, open(os.path.join(outdir, b + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    return m


def main():
    src, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]); redo = '--redo' in sys.argv
    os.makedirs(outdir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='tgis_')
    rows = []
    for pdf in sorted(glob.glob(os.path.join(src, '*.pdf'))):
        b = os.path.splitext(os.path.basename(pdf))[0]; jf = os.path.join(outdir, b + '.json')
        try:
            m = json.load(open(jf, encoding='utf-8')) if os.path.exists(jf) and not redo else one(pdf, outdir, tmp)
        except Exception as e:
            m = {'file': os.path.basename(pdf), 'bad': ['오류 ' + str(e)[:200]], 'pat': {}, 'no': None, 'day': None}
            json.dump(m, open(jf, 'w', encoding='utf-8'), ensure_ascii=False)
        rows.append([b, m.get('no') or '', m.get('day') or '', str(len(m.get('pat') or {})), 'OK' if not m['bad'] else '확인', ' ; '.join(m['bad'][:4])])
        print(rows[-1][4], b, rows[-1][5][:120], flush=True)
    with open(os.path.join(outdir, '_요약.tsv'), 'w', encoding='utf-8') as f:
        f.write('파일\t교차로번호\t시행일\t패턴수\t판정\t까닭\n')
        for r in rows: f.write('\t'.join(r) + '\n')
    print('OK %d / %d' % (sum(r[4] == 'OK' for r in rows), len(rows)))


if __name__ == '__main__':
    main()
