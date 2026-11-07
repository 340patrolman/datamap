# -*- coding: utf-8 -*-
# 합류부 가속차로 길이 — 국토지리정보원 정밀도로지도(공공누리 1유형 · 출처 「국토지리정보원 정밀도로지도」)로 잰다
#   의도 문서 = intent/20261107-merge-accel-hdmap.md(확정 2026-11-07) · 원본 SHP 는 저장소 밖 ../07_API키/out/hdmap/(받은 이름 그대로 · zip 이면 풀어 둔 폴더도 됨)
#   1단계(지금) = schema — 층·칸·고유값·좌표계 목록을 ../07_API키/out/hdmap/_schema.txt 로 뽑는다(코드값은 이것을 보고 정한다 · 지어내지 않음)
#   2단계(목록을 본 뒤) = measure — ① 차로중심선 위상 ② 차선 실선→점선 · 결과 data/sim-merge-accel.json
#   쓰기: py -3.12 -X utf8 tools/sim/merge-hdmap.py schema
import os, sys, glob, collections
import shapefile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'hdmap')
ENC = ['cp949', 'utf-8', 'euc-kr']


def open_shp(p):
    for e in ENC:
        try:
            r = shapefile.Reader(p, encoding=e)
            for i in range(min(len(r), 200)): r.record(i)   # 앞 200줄을 읽어 글자 판별
            return r, e
        except UnicodeDecodeError:
            continue
    return shapefile.Reader(p, encoding='latin-1'), 'latin-1'


def schema():
    shps = sorted(glob.glob(os.path.join(SRC, '**', '*.shp'), recursive=True))
    if not shps:
        print('SHP 없음 —', SRC); sys.exit(1)
    out = []
    for p in shps:
        r, e = open_shp(p)
        prj = p[:-4] + '.prj'
        out.append('## %s  (도형 %s · %d개 · 글자 %s)' % (os.path.relpath(p, SRC), r.shapeTypeName, len(r), e))
        if os.path.exists(prj): out.append('prj: ' + open(prj, encoding='latin-1').read().strip()[:300])
        out.append('bbox: %s' % (list(r.bbox),))
        flds = [f for f in r.fields[1:]]
        recs = r.records()
        for i, f in enumerate(flds):
            c = collections.Counter(str(x[i]) for x in recs)
            top = ', '.join('%s×%d' % (k, v) for k, v in c.most_common(15))
            out.append('  %s (%s,%s) 고유 %d: %s' % (f[0], f[1], f[2], len(c), top[:400]))
        out.append('')
    t = '\n'.join(out)
    open(os.path.join(SRC, '_schema.txt'), 'w', encoding='utf-8').write(t)
    print(t[:6000])


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'schema'
    if cmd == 'schema': schema()
    else: print('measure 는 _schema.txt 를 본 뒤 짠다'); sys.exit(1)
