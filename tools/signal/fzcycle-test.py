# -*- coding: utf-8 -*-
"""Fusion 두 닻으로 주기 재기(spat-bake fz_state·fz_cycle) 시험 — 통신 없음 · 그 교차로의 줄인 기록(07_API키/out/tdata/red)을 빌린 기록으로 삼아
진짜 주기를 빌린 주기 +0·+9·−12·+25초로 놓고(늘거나 준 몫은 주 녹색이 가져감) 모든 이동류 상태를 흉내 낸 Fusion 줄 두 개(1.5 빌린 주기 간격)를 만들어
fz_anchor → fz_state → fz_cycle 이 진짜 주기·진짜 녹색 시작(±0.6초)을 내는지, 다시 읽기('again')는 까닭(상태 다름·빌린 기록 다름·주기 값 다름·간격 모자람)이 있을 때만인지 본다.
  py -3.12 -X utf8 tools/signal/fzcycle-test.py [교차로 번호]   (기본 23251 · 2026-11-12 형님 사당동우체국앞 동영상) · 끝 코드 1 = 틀림"""
import sys, os, time, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ID = sys.argv[1] if len(sys.argv) > 1 else '23251'
sp = importlib.util.spec_from_file_location('sb', os.path.join(ROOT, 'tools', 'signal', 'spat-bake.py')); SB = importlib.util.module_from_spec(sp)
sys.argv = ['x']; sp.loader.exec_module(SB)
now = time.time()
G = 'protected-Movement-Allowed'; R = 'stop-And-Remain'
def mkrow(T, MV, G0, Ct, D):
    r = {'trsmUtcTime': int(T * 1000)}
    for x in MV:
        if x.get('g') is None or x.get('o') is None: continue
        o = x['o'] + (D if x['o'] > 0 else 0); g = x['g'] + (D if x['o'] == 0 else 0); y = x['y']
        q = (T - G0 - o) % Ct
        if q < g: st, rm = G, g - q
        elif q < g + y: st, rm = 'permissive-clearance', g + y - q
        else: st, rm = R, Ct - q
        r['%s%ssgStatNm' % (x['d'], x['m'])] = st; r['%s%ssgRmdrCs' % (x['d'], x['m'])] = int(round(rm * 10))
    return r
# 빌릴 기록 = 지금 시각에 fz_anchor 가 고르는 것(주기 그대로 흉내 내 한 번)
import glob, json
ok = True; n = 0
BASES = []
for f in sorted(glob.glob(os.path.join(SB.RAW, 'red', '%s_*.json' % ID)))[::-1]:
    r = json.load(open(f, encoding='utf-8'))
    if r.get('src') == 'f' or not r.get('ci'): continue
    BASES.append(r)
PICK = []   # fz_anchor 가 지금 시각에 실제로 빌려 가는 기록(같은 요일 갈래·같은 시 먼저) — 그 기록으로 시험한다
for b in BASES:
    pr = SB.fz_anchor(ID, mkrow(now - 450, b['mv'], now - 450 - 5, float(b['ci']), 0))
    if pr:
        PICK = [x for x in BASES if x['day'] + ' ' + x['from'] == pr['fz']['base']][:1]
        break
for base, Ct0 in [(b, d) for b in (PICK or BASES[:6]) for d in (0, 9, -12, 25, -25)]:
  Cb = float(base['ci']); Ct = Cb + Ct0
  if True:
    D = Ct - Cb
    for el0 in range(0, int(Ct), 7):
        T1 = now - 450; G0 = T1 - el0; T2 = T1 + 1.5 * Cb
        r1, r2 = mkrow(T1, base['mv'], G0, Ct, D), mkrow(T2, base['mv'], G0, Ct, D)
        a1, a2 = SB.fz_anchor(ID, r1), SB.fz_anchor(ID, r2)
        if not a1 or not a2: continue
        if a1['fz']['base'] != base['day'] + ' ' + base['from'] or a2['fz']['base'] != a1['fz']['base']: continue      # 그 기록을 빌린 경우만
        s1, s2 = SB.fz_state(r1, a1), SB.fz_state(r2, a2)
        res = SB.fz_cycle(a1, s1, a2, s2)
        trueG = G0 + ((T2 - G0) // Ct) * Ct
        if isinstance(res, dict):
            n += 1; good = res['ci'] == int(round(Ct)) and abs(res['a'] - trueG) <= 0.6
            if not good: print('  틀림 주기 %.0f 자리 %d %s %s → 잰 %s 닻 어긋남 %.1f' % (Ct, el0, s1, s2, res['ci'], res['a'] - trueG))
            ok &= good
        elif res == 'again':
            good = s1[0] != s2[0] or a1['fz']['base'] != a2['fz']['base'] or abs(float(a1['ci']) - float(a2['ci'])) > 0.05 or round((s2[1] - s1[1]) / float(a2['ci'])) < 1
            if not good: print('  다시 읽기인데 까닭 없음', Ct, el0, s1, s2, a1['ci'], a2['ci'], a1['fz']['base'], a2['fz']['base'], Cb); ok &= good
print(ID, '기록', len(BASES), '· 잰 경우', n, '·', '모두 맞음' if ok else '틀린 것 있음')
sys.exit(0 if ok else 1)
