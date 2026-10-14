# -*- coding: utf-8 -*-
# 🚦 여섯 구 신호값 얼마나 찼나 — 소유자 2026-10-14 「서초 강남 동작 관악 용산 · 송파까지 · 교차로 신호값도 다 받아야지」
#   구마다: 신호 교차로(data/fac-signal.json spots) · T-Data 역사 목록에 있음(07_API키/out/tdata/ids_*.json) · 기록 있음(data/sigdir-seoul.json its)
#           · 닻 12분 안(가르고가 「지금 색」으로 쓰는 것) · 요일 갈래 × 시 칸(pl · 4갈래 × 24 = 96칸 가운데 채운 칸 · 약한 줄 뺌) · 받을 수 없는 곳(fusion_none_why.json)
#   통신 없음 · 읽기만 · 결과는 화면에 찍고 저장소 밖 07_API키/out/tdata/six_cover.md 에도 쓴다
#   py -3.12 -X utf8 tools/signal/six-cover.py
import json, os, glob, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'tdata')
G6 = ['서초구', '강남구', '동작구', '관악구', '용산구', '송파구']


def main():
    fs = json.load(open(os.path.join(ROOT, 'data', 'fac-signal.json'), encoding='utf-8'))['spots']
    sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); its, pl = sd['its'], sd.get('pl', {})
    f = sorted(glob.glob(os.path.join(RAW, 'ids_*.json'))); ids = set(json.load(open(f[-1], encoding='utf-8'))['ids']) if f else set()
    wf = os.path.join(RAW, 'fusion_none_why.json'); why = json.load(open(wf, encoding='utf-8')) if os.path.exists(wf) else {}
    now = time.time(); rows = []; T = [0] * 8
    for g in G6 + ['여섯 구']:
        ks = [k for k, v in fs.items() if (v.get('gu') in G6 if g == '여섯 구' else v.get('gu') == g)]
        rec = [k for k in ks if its.get(k)]
        fresh = sum(1 for k in ks if any(r.get('a') and now - r['a'] < 720 for r in its.get(k, [])))
        cells = [len(set((x[0], x[1]) for x in pl.get(k, []) if not (len(x) > 6 and x[6]))) for k in rec]
        rows.append((g, len(ks), sum(1 for k in ks if k in ids), len(rec), fresh, sum(cells), 96 * len(rec), sum(1 for k in ks if k in why)))
    out = ['# 여섯 구 신호값 — %s (sigdir %s)' % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), sd.get('made')), '',
           '| 구 | 신호 교차로 | T-Data 목록에 있음 | 기록 있음 | 닻 12분 안 | 요일×시 칸(채움/기록 × 96) | 받을 수 없음(확인) |', '|---|---|---|---|---|---|---|']
    for g, n, inl, rec, fr, c, cmax, no in rows:
        out.append('| %s | %d | %d | %d | %d | %d / %d (%.1f%%) | %d |' % (g, n, inl, rec, fr, c, cmax, 100.0 * c / cmax if cmax else 0, no))
    if why:
        out += ['', '받을 수 없는 곳(Fusion 으로 확인 · 날짜 · 까닭):'] + ['- %s %s · %s · %s' % (k, fs.get(k, {}).get('nm', ''), v[0], v[1]) for k, v in sorted(why.items()) if fs.get(k, {}).get('gu') in G6]
    t = '\n'.join(out); print(t)
    open(os.path.join(RAW, 'six_cover.md'), 'w', encoding='utf-8').write(t + '\n')


if __name__ == '__main__':
    main()
