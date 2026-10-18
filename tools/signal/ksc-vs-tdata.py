# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 교통과 출력물(sig-ksc-seocho) ↔ 서울시 T-Data 실측(sigdir-seoul) 자세히 맞대기
#   소유자 2026-10-18 「커밋하고 신호값을 맞춰보자」 — sig-audit.py 의 ① 은 한 줄 요약뿐이라 기록마다 무엇이 맞고 다른지 표로 낸다
#   견주는 것(같은 요일 갈래·시각에 도는 교통과 계획의 패턴과):
#     ① 주기  ② 방향별 녹색 초(같은 방위·직진/좌회전 · 실측은 잔여시간에서 읽은 추정 — ±TOL+1초면 맞음)
#     ③ 옵셋 — 실측 기준 이동류의 녹색이 켜진 하루 초(mod 주기) ↔ 교통과 패턴 옵셋 + 그 이동류의 녹색 시작(옵셋 기준 = 자정 · ksc-bake 머리말)
#   계획이 바뀐 뒤 6분 · 받는 동안 계획이 바뀐 기록은 sig-audit 처럼 뺀다 · 원자료 방위가 실제와 다를 수 있는 기록(dq dir)은 표시만
#   결과 = 저장소 밖 07_API키/신호앱/교통과_실측대조_상세_<날>.md (출력물 값이 든 표라 저장소에는 요약만 — 지도는 data/sig-audit.json 을 읽는다)
#   py -3.12 -X utf8 tools/signal/ksc-vs-tdata.py
import json, os, sys, datetime, importlib.util, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = importlib.util.spec_from_file_location('sa', os.path.join(ROOT, 'tools', 'signal', 'sig-audit.py')); SA = importlib.util.module_from_spec(sp); sp.loader.exec_module(SA)
D, hm, cdev, ksc_plan, TOL = SA.D, SA.hm, SA.cdev, SA.ksc_plan, SA.TOL
DK = '월~목 금 토 일'.split(); BW = {'nt': '북', 'et': '동', 'st': '남', 'wt': '서', 'ne': '북동', 'nw': '북서', 'se': '남동', 'sw': '남서'}; MV = {'St': '직진', 'Lt': '좌회전', 'Bs': '버스', 'Ut': '유턴', 'Rt': '우회전'}


def main():
    S = D('sigdir-seoul.json'); its, pl = S['its'], S.get('pl', {})
    KSC = {str(x['no']): x for x in D('sig-ksc-seocho.json')['items']}
    md = ['# 교통과 출력물 ↔ T-Data 실측 자세히 — %s (sigdir %s)' % (datetime.date.today().isoformat(), S.get('made', '')), '',
          '같은 요일 갈래·시각에 도는 교통과 계획 패턴과 견준다. 실측 녹색 초는 잔여시간에서 읽은 추정이라 ±%d초면 맞음으로 본다. 옵셋 = 기준 이동류 녹색이 켜진 때(자정 기준 mod 주기)의 차이.' % (TOL + 1), '']
    tot = collections.Counter()
    for no, x in KSC.items():
        L = its.get(no) or []
        md.append('## %s %s (출력물 %s)' % (no, x['nm'], x.get('day', '')))
        if not L: md += ['- **실측 없음** — T-Data 가 이 교차로의 남은 초를 보내지 않는다(현장 측정으로만 맞춰 볼 수 있다)', '']; tot['none'] += 1; continue
        rows = []; sc = collections.Counter()
        for o in L:
            if o.get('cl') is None: continue
            m0 = hm(o['from']); q = ksc_plan(x, o['cl'], m0)
            if not q: continue
            pn, c, nxt, st0 = q; lab = '%s %s %s~%s' % (o['day'][5:], DK[o['cl']], o['from'], o['to'])
            if 0 <= m0 - st0 < 6 or (hm(o['to']) >= nxt and hm(o['to']) >= m0): rows.append([lab, pn, c, o['cyc'], '계획이 바뀌는 때라 뺌', '', '']); continue
            cyc_ok = abs(c - o['cyc']) <= 2.5; sc['cyc_ok' if cyc_ok else 'cyc_bad'] += 1
            K = {(r[0], r[1]): r for r in x['dir'].get(str(pn), []) if r[3] is not None}
            g = []
            if cyc_ok:
                for m in o['mv']:
                    if m[2] is None or (m[0], m[1]) not in K: continue
                    d = m[2] - K[(m[0], m[1])][3]; ok = abs(d) <= TOL + 1; sc['g_ok' if ok else 'g_bad'] += 1
                    g.append('%s %s %s→%s%s' % (BW.get(m[0], m[0]), MV.get(m[1], m[1]), K[(m[0], m[1])][3], round(m[2]), '' if ok else ' ❌'))
            od = ''
            if cyc_ok and o.get('a') is not None and x['pat'].get(str(pn)):
                ref = [m for m in o['mv'] if m[5] == 0 and (m[0], m[1]) in K]
                if ref:
                    v = cdev((o['a'] + 32400) % 86400 % c, (x['pat'][str(pn)]['off'] + K[(ref[0][0], ref[0][1])][6]) % c, c); ok = v <= TOL; sc['off_ok' if ok else 'off_bad'] += 1
                    od = '%d초%s' % (v, '' if ok else ' ❌')
            rows.append([lab, pn, c, o['cyc'], '' if cyc_ok else '❌', ' · '.join(g), od + (' (방위 확인 필요)' if o.get('dq') == 'dir' else '')])
        for prow in pl.get(no, []):
            if len(prow) > 6 and prow[6]: continue
            cl, hr, cyc, off = prow[:4]; rk = prow[5] if len(prow) > 5 else ''
            q0, q1 = ksc_plan(x, cl, hr * 60 + 6), ksc_plan(x, cl, hr * 60 + 59)
            if not q0 or not q1 or q0[0] != q1[0]: continue
            pn, c = q0[0], q0[1]; lab = '(시각대 표) %s %d시' % (DK[cl], hr)
            if abs(c - cyc) > 2.5: rows.append([lab, pn, c, cyc, '❌', '', '']); sc['cyc_bad'] += 1; continue
            Kd = {(r[0], r[1]): r for r in x['dir'].get(str(pn), []) if r[3] is not None}; kd = tuple(rk.split(':')) if rk else None; sc['cyc_ok'] += 1
            sh = 0.0
            if kd and kd not in Kd:   # 기준 이동류가 현시도에 없으면(초를 비운 이동류 등) 같은 요일 갈래·주기의 받은 기록에서 그 이동류와 현시도에 있는 이동류의 녹색 시작 차이만큼 옮긴다(지도 kscTd 와 같은 법)
                for o in reversed(L):
                    if o.get('cl') != cl or abs((o.get('ci') or o['cyc']) - cyc) > 0.6: continue
                    mm = {(m[0], m[1]): m for m in o['mv'] if m[5] is not None}
                    if kd not in mm: continue
                    alt = [k2 for k2 in mm if k2 in Kd and mm[k2][2] is not None]
                    if alt: sh = mm[alt[0]][5] - mm[kd][5]; kd = alt[0]; break
            if not kd or kd not in Kd: rows.append([lab, pn, c, cyc, '', '', '(기준 이동류가 현시도에 없어 옵셋은 못 견줌)']); continue
            v = cdev((off + sh) % c, (x['pat'][str(pn)]['off'] + Kd[kd][6]) % c, c); ok = v <= TOL; sc['off_ok' if ok else 'off_bad'] += 1
            rows.append([lab, pn, c, cyc, '', '', '%d초%s (기준 %s %s)' % (v, '' if ok else ' ❌', BW.get(kd[0], kd[0]), MV.get(kd[1], kd[1]))])
        f = lambda a, b: '%d / %d' % (sc[a], sc[a] + sc[b])
        md += ['- 주기 맞음 **%s** · 방향별 녹색 맞음 **%s** · 옵셋(±%d초) 맞음 **%s**' % (f('cyc_ok', 'cyc_bad'), f('g_ok', 'g_bad'), TOL, f('off_ok', 'off_bad')), '',
               '| 받은 때 | 패턴 | 계획 주기 | 실측 주기 | 주기 | 방향별 녹색(계획→실측) | 옵셋 어긋남 |', '|---|---|---|---|---|---|---|']
        md += ['| %s | %s | %s | %s | %s | %s | %s |' % (r[0], r[1], r[2], round(r[3]) if isinstance(r[3], (int, float)) else r[3], r[4], r[5], r[6]) for r in rows] + ['']
        tot.update(sc); print(no, x['nm'], dict(sc))
    g = lambda a, b: '%d / %d (%d%%)' % (tot[a], tot[a] + tot[b], round(100 * tot[a] / max(1, tot[a] + tot[b])))
    md += ['## 모두', '- 주기 %s · 방향별 녹색 %s · 옵셋 %s' % (g('cyc_ok', 'cyc_bad'), g('g_ok', 'g_bad'), g('off_ok', 'off_bad')),
           '- ❌ 이 나온 칸의 까닭 후보: ① 출력물 뒤 계획 변경 ② 감응·수동 운영 ③ 계획이 바뀌는 시각 ④ 특수일 ⑤ 실측 녹색 초는 잔여시간 추정(황색 경계 ±1~2초) — 같은 칸이 날마다 같은 값으로 어긋나면 ①(계획이 바뀐 것)일 가능성이 크다']
    out = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱', '교통과_실측대조_상세_%s.md' % datetime.date.today().strftime('%Y%m%d'))
    open(out, 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n'); print('모두', dict(tot)); print(out)


if __name__ == '__main__':
    main()
