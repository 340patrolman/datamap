# -*- coding: utf-8 -*-
# 조치 장부 — 팔란티어 방식 「행동 → 결과 → 되먹임」 한 고리(2026-11-07 · 소유자 「권고대로 1번부터 진행」)
#   지도에 흩어진 세 기록(이 기기에만 있는 것)을 한 꼴로 묶고, 시각과 자리가 있는 조치에는 쌓인 실측으로 앞뒤를 붙인다.
#     ① 🔁 고리 「📝 현장 조치 적기」 CSV   = 고리,조치,이름,까닭,시각,전          (js/link.js tg_map2d_lnk_act)
#     ② 🧭 오늘의 결정 「📒 되돌아보기」 CSV = 날짜,적은때,교차로,이름,브리핑순위,결정,한일,까닭 (js/decide.js tg_map2d_dec_log)
#     ③ 🧩 엮어서 답 찾기 「📒 내가 적은 기록」 CSV = 날짜,질문,대상,한 일,결과  (map2d.js tg_map2d_orclog · 시각·자리 번호 없음 → 장부에만)
#     ④ 📒 「조치 기록 한곳에」 CSV(tg-act/1) = 출처,적은때,대상,이름,한 일,까닭,결과   (map2d.js v2.310.0 · 위 셋을 한 번에)
#   앞뒤 셈은 act-effect.py 와 같다 — 전 = 조치 전 30분 · 뒤1 = 15~45분 뒤 · 뒤2 = 45~90분 뒤 · 평소 = 같은 요일 갈래 다른 날 같은 시각의 「전 → 뒤1」 변화 평균
#     고리(LOOP-…) = 네 변 · 교차로(INT-…) = 그 교차로로 들어오는 길(코어 「들어오는길」 → 「이룸」 링크 앞 둘)
#   기운 몫 = 그날 변화 − 평소 변화 · 가능성 D(그날 수요가 달랐을 수 있다 — 조치 효과라고 단정하지 않는다) · 한 점수로 더하지 않는다 · 문턱을 두지 않는다
#   결과는 저장소에 올리지 않는다(07_API키/out/onto_logs/ledger_<날짜>.md · ledger.json) — 형님이 「맞다」 한 줄만 tools/onto/rules-bake.py FIELD 에
#   개인정보 꼴은 log-ingest.py 와 같은 잣대로 ○○
#   py -3.12 -X utf8 tools/onto/act-ledger.py
import csv, io, os, glob, json, datetime, collections, importlib.util
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def _mod(name):
    sp = importlib.util.spec_from_file_location(name.replace('-', '_'), os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


AE = _mod('act-effect'); LI = _mod('log-ingest')
LOGS = AE.LOGS


def read_any():
    R = []
    for f in sorted(glob.glob(os.path.join(LOGS, 'in', '*.csv')) + glob.glob(os.path.join(LOGS, 'in', '*.txt'))):
        b = open(f, 'rb').read()
        for enc in ('utf-8-sig', 'cp949'):
            try: t = b.decode(enc); break
            except UnicodeDecodeError: continue
        rd = list(csv.reader(io.StringIO(t)))
        if not rd: continue
        h = [c.strip() for c in rd[0]]; rows = [dict(zip(h, r)) for r in rd[1:] if any(x.strip() for x in r)]
        g = lambda r, k: (r.get(k) or '').strip()
        if h[:2] == ['출처', '적은때']:
            R += [dict(src=g(r, '출처'), at=g(r, '적은때'), tgt=g(r, '대상'), nm=g(r, '이름'), what=g(r, '한 일'), why=g(r, '까닭'), res=g(r, '결과')) for r in rows]
        elif h[:2] == ['고리', '조치']:
            R += [dict(src='고리', at=g(r, '시각'), tgt=g(r, '고리'), nm='', what=(g(r, '이름') if g(r, '이름') != '그 밖' else '') + ((' — ' if g(r, '이름') != '그 밖' else '') + g(r, '까닭') if g(r, '까닭') else '') or g(r, '조치'), why='', res='') for r in rows]   # link.js 「이름」 = 고른 조치 이름 · 「까닭」 = 「그 밖」일 때 적은 한 줄
        elif '브리핑순위' in h:
            R += [dict(src='결정', at=g(r, '적은때'), tgt=g(r, '교차로'), nm=g(r, '이름'), what=g(r, '한일'), why=g(r, '까닭'), res='') for r in rows]
        elif h[:2] == ['날짜', '질문']:
            R += [dict(src='엮어서', at=g(r, '날짜'), tgt='', nm=g(r, '대상'), what=g(r, '한 일'), why=g(r, '질문'), res=g(r, '결과')) for r in rows]
    U = {tuple(sorted(r.items())): r for r in R}
    out, nmask = [], 0
    for r in U.values():
        for k in ('nm', 'what', 'why', 'res'):
            r[k], hit = LI.mask(r[k]); nmask += hit
        out.append(r)
    return sorted(out, key=lambda r: r['at']), nmask


def int_links():
    core = json.load(open(os.path.join(ROOT, 'ontology-core', 'data', 'core-seocho.json'), encoding='utf-8'))
    O = {o['id']: o for o in core['objects']}; ir = collections.defaultdict(list); ap = collections.defaultdict(list)
    for e in core['edges']:
        if e[1] == '이룸' and e[2] in O and O[e[2]].get('link'): ir[e[0]].append((e[3].get('k', 0), O[e[2]]['link']))
        elif e[1] == '들어오는길': ap[e[0]].append(e[2])
    return {i: [(a, [l for k, l in sorted(ir.get(a, []))]) for a in A if ir.get(a)] for i, A in ap.items()}


def measure(S, links, t):
    ts = int(t.timestamp()); cls = AE.dcls(t)
    b = AE.win(S, links, ts - 1800, ts); a1 = AE.win(S, links, ts + 900, ts + 2700); a2 = AE.win(S, links, ts + 2700, ts + 5400)
    base = []
    for d in sorted({datetime.date.fromtimestamp(a) for a, m in S} - {t.date()}):
        dd = datetime.datetime.combine(d, t.time())
        if AE.dcls(dd) != cls: continue
        x = int(dd.timestamp()); bb = AE.win(S, links, x - 1800, x); aa = AE.win(S, links, x + 900, x + 2700)
        if bb is not None and aa is not None: base.append(aa - bb)
    ch = round(a1 - b, 1) if a1 is not None and b is not None else None
    bm = round(sum(base) / len(base), 1) if base else None
    return dict(b=b, a1=a1, a2=a2, ch=ch, bm=bm, nb=len(base), lean=round(ch - bm, 1) if ch is not None and bm is not None else None)


def main():
    A, nmask = read_any(); LL = AE.leg_links(); IL = int_links(); S = AE.snaps()
    f = lambda v: '—' if v is None else '%+.1f' % v
    n = lambda v: '—' if v is None else str(v)
    rows, md = [], []
    for r in A:
        try: t = datetime.datetime.strptime(r['at'], '%Y-%m-%d %H:%M')
        except ValueError: t = None
        parts = []
        if r['tgt'] in LL and not r['nm']: r['nm'] = LL[r['tgt']][0].get('nm', '')
        if t and r['tgt'] in LL:
            L, legs = LL[r['tgt']]; parts = [(lg['nm'].split(' — ')[0], links) for lg, links in zip(L['legs'], legs)]
        elif t and r['tgt'] in IL:
            parts = [(a.replace('APR-', ''), links) for a, links in IL[r['tgt']]]
        M = [(p, measure(S, links, t)) for p, links in parts if links]
        why = '시각 없음(날짜만)' if not t else '자리 번호 없음' if not r['tgt'] else '고리·교차로 목록에 없음' if not parts else ''
        rows.append(dict(r, parts=[dict(p=p, **m) for p, m in M], note=why))
    md += ['# 조치 장부 — %s' % datetime.date.today().isoformat(), '',
           '기록 %d건(고리 %d · 결정 %d · 엮어서 %d · 기타 %d) · 앞뒤를 잰 것 %d건 · 가림 %d칸 · 쌓인 속도 기록 %d장(%s ~ %s)' % (
               len(rows), sum(r['src'] == '고리' for r in rows), sum(r['src'] == '결정' for r in rows), sum(r['src'] == '엮어서' for r in rows),
               sum(r['src'] not in ('고리', '결정', '엮어서') for r in rows), sum(bool(r['parts']) for r in rows), nmask, len(S),
               datetime.datetime.fromtimestamp(S[0][0]).strftime('%m-%d %H:%M') if S else '—', datetime.datetime.fromtimestamp(S[-1][0]).strftime('%m-%d %H:%M') if S else '—'), '',
           '읽는 법: 길마다 「전 → 뒤1(15~45분) → 뒤2(45~90분)」 km/h · 평소 = 같은 요일 갈래 다른 날 같은 시각의 「전 → 뒤1」 변화 평균 · 기운 몫 = 그날 변화 − 평소 변화(+ 면 조치 뒤 더 빨라짐) · **가능성 D** — 그날 수요가 달랐을 수 있어 조치 효과라고 단정하지 않는다 · 결정 기록의 시각은 「적은 때」(조치한 때보다 늦을 수 있다)', '']
    for r in rows:
        md.append('## %s · %s · %s%s' % (r['at'] or '(시각 없음)', r['src'], r['nm'] or r['tgt'] or '—', (' (' + r['tgt'] + ')') if r['tgt'] and r['nm'] else ''))
        md.append(''); md.append('- 한 일: %s%s%s' % (r['what'] or '—', (' · 까닭: ' + r['why']) if r['why'] else '', (' · 결과(적은 것): ' + r['res']) if r['res'] else ''))
        if not r['parts']:
            md += ['- 앞뒤: 못 잼 — ' + (r['note'] or '그 시각 앞뒤 속도 기록 없음'), '']; continue
        md += ['', '| 길 | 전 | 뒤1 | 뒤2 | 그날 변화 | 평소 변화(날 수) | 기운 몫 |', '|---|---|---|---|---|---|---|']
        for p in r['parts']:
            md.append('| %s | %s | %s | %s | %s | %s | %s |' % (p['p'], n(p['b']), n(p['a1']), n(p['a2']), f(p['ch']), ('%s (%d날)' % (f(p['bm']), p['nb'])) if p['bm'] is not None else '— (같은 갈래 다른 날 없음)', f(p['lean'])))
        md.append('')
    if not rows:
        md.append('아직 기록이 없다 — 지도 「📒 조치 기록 한곳에」(또는 세 화면의 CSV)를 07_API키/out/onto_logs/in/ 에 넣기')
    os.makedirs(LOGS, exist_ok=True)
    day = datetime.date.today().strftime('%Y%m%d')
    p = os.path.join(LOGS, 'ledger_%s.md' % day); open(p, 'w', encoding='utf-8').write('\n'.join(md) + '\n')
    json.dump(dict(schema='tg-act-ledger/1', made=datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), rows=rows), open(os.path.join(LOGS, 'ledger.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('기록 %d · 앞뒤 잰 것 %d · 가림 %d · 속도 기록 %d · → %s' % (len(rows), sum(bool(r['parts']) for r in rows), nmask, len(S), p))


if __name__ == '__main__':
    main()
