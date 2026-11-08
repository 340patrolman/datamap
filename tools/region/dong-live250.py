# -*- coding: utf-8 -*-
# 서울 행정동 시간대 생활인구(dong.json 의 live)를 250m 격자 생활인구(live250.json)에서 다시 묶는다(2026-11-08 · 지도 세션)
#   까닭: 서울시 「행정동 단위 생활인구」(LOCAL_PEOPLE_DONG)는 2026-07-31 치로 생산이 끝났다 → 동 카드가 7월 값에 묶여 있었다.
#        또 그 7월 동 표는 일부 동이 크게 어긋났다(새벽 3시 ÷ 주민등록 인구가 0.5~2배 밖인 동: 7월 동 표 15 · 격자 묶음 4 — 422동 · 격자 쪽 4 는 7월 쪽 15 안에 다 든다
#        · 예 신월6동 주민 13,514 ↔ 7월 3,431 · 격자 14,471 / 북아현동 주민 14,881 ↔ 7월 63,232 · 격자 11,158).
#   셈: 칸마다 live250 의 dong{행정동: 평일 생활인구가 잡힌 몫 %} 대로 나눠 더한다(동 값 = Σ 칸 값 × 몫 ÷ 100)
#       ⚠ 주말도 평일 몫으로 나눈다(주말 몫은 원자료에 없다 — 어림) · 격자는 내국인만(원자료가 내국인 격자) · 같은 칸이 두 구 파일에 있으면 한 번만
#   격자에 잡히지 않은 동은 7월 값을 그대로 두고 source 에 적는다.
#   py -3.12 -X utf8 tools/region/dong-live250.py        (live250-bake.py build 다음 · dong-bake.py 를 다시 돌린 다음에도)
#   그다음 publish-data.py push 11
import json, os, glob, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
R = os.path.join(ROOT, 'data', 'r')


def main():
    cells, src = {}, ''
    for f in sorted(glob.glob(os.path.join(R, '11*', 'live250.json'))):
        d = json.load(open(f, encoding='utf-8')); src = src or d.get('source', '')
        for k, c in d['cells'].items(): cells.setdefault(k, c)
    agg = collections.defaultdict(lambda: {'wd': [0.0] * 24, 'we': [0.0] * 24})
    for c in cells.values():
        for dc, sh in (c.get('dong') or {}).items():
            for t in ('wd', 'we'):
                v = c.get(t) or []
                for h in range(min(24, len(v))): agg[str(dc)][t][h] += v[h] * sh / 100.0
    import re; m = re.search(r'(\d{8})~(\d{8})', src); week = (m.group(1)[:4] + '-' + m.group(1)[4:6] + '-' + m.group(1)[6:] + '~' + m.group(2)[4:6] + '-' + m.group(2)[6:] + ' 한 주') if m else ''
    n = keep = 0
    for f in sorted(glob.glob(os.path.join(R, '11*', 'dong.json'))):
        d = json.load(open(f, encoding='utf-8')); old = []
        for x in d.get('dong') or []:
            a = agg.get(str(x.get('k')))
            if a and sum(a['wd']) > 0:
                x['live'] = {t: [int(round(v)) for v in a[t]] for t in ('wd', 'we')}; n += 1
            elif x.get('live'): old.append(x.get('name')); keep += 1
        s = d.get('source')
        txt = ('서울시 250m 격자 생활인구(내국인 · OA-22784 · ' + week + ')를 행정동으로 묶음 — 칸마다 평일 생활인구가 잡힌 행정동 몫대로 나눠 더함(주말도 평일 몫으로 나눈 어림) · tools/region/dong-live250.py'
               + (' · 격자에 안 잡힌 동(' + '·'.join(old) + ')은 행정동 생활인구 2026년 7월 값 그대로' if old else '')
               + ' · 「그 시각 그 동에 있는 사람 수」 추정(주민등록 인구와 다르다)')
        if isinstance(s, dict): s['생활인구'] = txt
        d['source'] = s
        json.dump(d, open(f, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('격자 칸', len(cells), '· 동 바꿈', n, '· 7월 값 그대로', keep)


if __name__ == '__main__':
    main()
