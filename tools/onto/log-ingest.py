# -*- coding: utf-8 -*-
# 팔란티어 방식 ④ 「해 보고 다시 적는다」 → 되먹임 (2026-10-23)
#   지도의 두 기록(이 기기에만 있는 것)을 형님이 CSV 로 복사해 주면 → 한 장으로 정리하고 「현장 판단 후보」를 뽑는다
#     ① 🧩 엮어서 답 찾기 「📒 내가 적은 기록」 CSV  = 날짜,질문,대상,한 일,결과
#     ② 🧭 오늘의 결정 「📒 되돌아보기」 CSV       = 날짜,적은때,교차로,이름,브리핑순위,결정,한일,까닭
#   후보는 저장소에 올리지 않는다(07_API키/out/onto_logs/) — 형님이 「이것 맞다」고 한 줄만 tools/onto/rules-bake.py FIELD 에 말 그대로 옮긴다
#   개인정보 꼴(차량번호·전화·주민번호·이름+계급)이 보이면 그 줄은 ○○ 로 가리고 「가림」 표시
# 쓰기: CSV 를 07_API키/out/onto_logs/in/ 에 아무 이름(.csv/.txt)으로 넣고   py -3.12 -X utf8 tools/onto/log-ingest.py
import csv, io, os, re, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'onto_logs')
PII = [re.compile(p) for p in (r'\d{2,3}[가-힣]\s?\d{4}', r'01[016789]-?\d{3,4}-?\d{4}', r'\d{6}-?[1-4]\d{6}', r'[가-힣]{2,4}\s?(순경|경장|경사|경위|경감|경정|총경)')]


def mask(t):
    hit = False
    for p in PII:
        if p.search(t or ''):
            t = p.sub('○○', t); hit = True
    return t, hit


def read_rows(path):
    b = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp949'):
        try:
            t = b.decode(enc); break
        except UnicodeDecodeError:
            continue
    rd = list(csv.reader(io.StringIO(t)))
    if not rd:
        return None, []
    h = [c.strip() for c in rd[0]]
    kind = 'orc' if h[:2] == ['날짜', '질문'] else 'dec' if '브리핑순위' in h else None
    return kind, [dict(zip(h, r)) for r in rd[1:] if any(x.strip() for x in r)]


def main():
    os.makedirs(os.path.join(BASE, 'in'), exist_ok=True)
    O, Dd, masked = [], [], 0
    for f in sorted(glob.glob(os.path.join(BASE, 'in', '*.csv')) + glob.glob(os.path.join(BASE, 'in', '*.txt'))):
        k, rows = read_rows(f)
        for r in rows:
            for c in list(r):
                r[c], h = mask(r[c]); masked += h
        (O if k == 'orc' else Dd if k == 'dec' else []).extend(rows)
    # 같은 줄이 두 번(기기 둘에서 복사) 들어오면 한 번만
    O = [dict(t) for t in {tuple(sorted(r.items())) for r in O}]
    Dd = [dict(t) for t in {tuple(sorted(r.items())) for r in Dd}]
    L = ['# 현장 기록 정리 — %s' % datetime.date.today().isoformat(), '',
         '엮어서 답 찾기 기록 %d건 · 오늘의 결정 기록 %d건 · 개인정보 꼴을 가린 칸 %d' % (len(O), len(Dd), masked), '']
    if O:
        L += ['## 🧩 엮어서 답 찾기 — 질문별', '']
        by = collections.defaultdict(list)
        for r in O:
            by[r.get('질문', '?')].append(r)
        for q, rs in sorted(by.items(), key=lambda kv: -len(kv[1])):
            L.append('### %s — %d건' % (q, len(rs)))
            for r in sorted(rs, key=lambda r: r.get('날짜', ''), reverse=True)[:30]:
                L.append('- %s · %s — %s%s' % (r.get('날짜', ''), r.get('대상', ''), r.get('한 일', ''), (' → ' + r['결과']) if r.get('결과') else ''))
            L.append('')
    why = collections.Counter()
    if Dd:
        L += ['## 🧭 오늘의 결정 — 브리핑 1순위를 고른 몫', '']
        n1 = sum(1 for r in Dd if str(r.get('브리핑순위', '')).strip() in ('1', '1순위'))
        L.append('- 1순위를 고름 %d / %d' % (n1, len(Dd)))
        why = collections.Counter(r.get('까닭', '').strip() for r in Dd if str(r.get('브리핑순위', '')).strip() not in ('1', '1순위') and r.get('까닭', '').strip())
        if why:
            L += ['', '### 1순위가 아닌 곳을 고른 까닭(많은 차례)']
            L += ['- %s (%d)' % (w, c) for w, c in why.most_common(20)]
        L.append('')
    # 현장 판단 후보 — 결과가 적힌 기록과 1순위가 아닌 까닭 중 두 번 넘게 나온 것
    cand = []
    for r in O:
        if r.get('결과'):
            cand.append('「%s」에서 %s 했더니 %s (%s · %s)' % (r.get('대상', ''), r.get('한 일', ''), r['결과'], r.get('질문', ''), r.get('날짜', '')))
    if Dd:
        for w, c in why.most_common(10):
            if c >= 2:
                cand.append('오늘의 결정에서 1순위가 아닌 곳을 고른 까닭 「%s」(%d번)' % (w, c))
    L += ['## ✍ 현장 판단 후보 — 형님이 「맞다」고 한 줄만 규칙 장부(onto-rules FIELD)에 말 그대로 옮긴다', '']
    L += ['- [ ] ' + c for c in cand[:40]] or ['- 아직 후보 없음(결과 칸이 적힌 기록이 없다)']
    out = os.path.join(BASE, '%s_정리.md' % datetime.date.today().strftime('%Y%m%d'))
    open(out, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('엮기 %d · 결정 %d · 가림 %d · 후보 %d → %s' % (len(O), len(Dd), masked, len(cand), out))


if __name__ == '__main__':
    main()
