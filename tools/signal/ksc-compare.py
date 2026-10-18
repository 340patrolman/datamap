# -*- coding: utf-8 -*-
# 교통과 신호 출력물 ↔ T-Data 실측 주기 대조 (2026-10-18 소유자 「찾아지는 신호값은 찾는 게 우선이고 맞춰 보는 거지」)
#   지도에는 공개 자료로 찾아지는 값(T-Data 실측 · 경찰청 공개 계획)을 먼저 싣고, 교통과 출력물은 ① 공개 자료에 값이 없는 곳(서초역사거리·삼호가든사거리)만 싣고 ② 나머지는 이 도구로 맞춰 보기에만 쓴다
#   읽기: 07_API키/신호앱/data/서초서_교통과_신호_불러오기용_20260911.json(저장소 밖 · 교통과 원자료) · data/sigdir-seoul.json pl(요일 갈래 × 시 × 실측 주기)
#   쓰기: 07_API키/신호앱/교통과_실측대조_<날짜>.md(저장소 밖) — 통신 없음 · 커밋할 것 없음
#   py -3.12 -X utf8 tools/signal/ksc-compare.py
import os, json, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
DN = ['월~목', '금', '토', '일·공휴일']


def plan_cycle(e, d, h):
    rows = e['tod'].get(str(d + 1)) or []; t = '%02d30' % h; cur = None
    for r in rows:
        if r[0] <= t: cur = r
    if cur is None:   # 그날 첫 계획보다 이르면 전날 마지막 계획이 이어진다
        prev = e['tod'].get(str(((d - 1) % 4) + 1)) or rows; cur = prev[-1] if prev else None
    return cur[1] if cur else None


def main():
    K = {e['no']: e for e in json.load(open(os.path.join(KB, '신호앱', 'data', '서초서_교통과_신호_불러오기용_20260911.json'), encoding='utf-8'))['items']}
    sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); pl = sd.get('pl', {})
    day = datetime.date.today().isoformat()
    L = ['# 교통과 출력물 ↔ T-Data 실측 주기 대조 — %s (sigdir %s)' % (day, sd.get('made')), '', '칸 = 요일 갈래 × 시(그 시 30분의 교통과 계획 주기 ↔ 그 시에 실제로 받은 주기) · ±1초면 맞음 · 실측이 없는 칸은 「실측 없음」.', '']
    tot = [0, 0]
    for no, e in K.items():
        ok = bad = 0; mis = []
        for x in pl.get(no, []):
            if len(x) > 6 and x[6]: continue
            c0 = plan_cycle(e, x[0], x[1])
            if c0 is None: continue
            if abs(c0 - x[2]) <= 1: ok += 1
            else: bad += 1; mis.append('%s %02d시 계획 %d ↔ 실측 %d' % (DN[x[0]], x[1], c0, x[2]))
        n = ok + bad; tot[0] += ok; tot[1] += n
        L.append('## %s %s (출력물 %s) — %s' % (no, e['nm'], e.get('day', ''), ('맞음 %d / %d (%.0f%%)' % (ok, n, 100.0 * ok / n)) if n else '실측 없음 — T-Data 가 남은 초를 보내지 않는 곳(현장 측정으로만 맞춰 볼 수 있다)'))
        if mis: L.append('- 안 맞은 칸: ' + ' · '.join(mis[:20]))
        L.append('')
    L += ['**실측이 있는 칸 전체 맞음 %d / %d (%.0f%%)**' % (tot[0], tot[1], 100.0 * tot[0] / max(1, tot[1])), '',
          '- 안 맞는 칸 = ① 출력물 뒤 계획 변경 ② 감응·수동 운영 ③ 계획 바뀌는 시각에 걸친 칸 ④ 특수일 — 어느 쪽인지는 그 칸의 실측을 더 쌓거나 현장에서 본다.']
    p = os.path.join(KB, '신호앱', '교통과_실측대조_%s.md' % day.replace('-', ''))
    open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n'); print('\n'.join(L[:3] + [l for l in L if l.startswith('##') or l.startswith('**')])); print('->', p)


if __name__ == '__main__':
    main()
