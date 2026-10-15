# -*- coding: utf-8 -*-
"""가르고 ↔ 카카오 대조를 1시간마다 저절로(2026-10-15 소유자 「너의 권고가 맞다 그렇게 진행하자」)

07~23시 매시 5분에(예약 작업 datamap-compare-hourly 가 once 로 · 창으로 켜면 고리) route-spot.py --save(고정 짝 12) · kakao-spot.py --save(고정 구간 28) 를 한 번씩 → 07_API키/out/compare/ 에 우리 값 + 비율·겹침만(카카오 원래 값은 안 남김)
하루 약 40 × 17 = 680건(카카오 무료 10,000 의 7%) · 두 도구가 하루 9,000 에서 스스로 멈춤 · 401/403/429 도 멈춤
끄기 = 07_API키/out/compare/stop 파일(RUN_compare_stop.bat) · 이미 돌고 있으면 또 켜지지 않음(loop.lock)
  py -3.12 -X utf8 tools/signal/compare-loop.py [once]
"""
import os, sys, time, subprocess, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'compare')
KST = dt.timezone(dt.timedelta(hours=9))
HOURS = (7, 24)


def now():
    return dt.datetime.now(KST)


def log(*a):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'loop.log'), 'a', encoding='utf-8') as f:
        f.write(now().strftime('%m-%d %H:%M ') + ' '.join(str(x) for x in a) + chr(10))


def one():
    for tool in ('route-spot.py', 'kakao-spot.py'):
        try:
            p = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, tool), '--save'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=900)
            last = [l for l in (p.stdout or '').splitlines() if l.strip()][-1:] or [(p.stderr or '').strip()[-200:]]
            log(tool, '끝 ' + str(p.returncode), last[0][:160])
        except Exception as e:
            log(tool, '실패', type(e).__name__, str(e)[:120])


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'once':   # 예약 작업(datamap-compare-hourly · 매시 5분 07~23시)이 부르는 길 — 2026-10-15 오래 떠 있는 창이 두 번(14:48 · 17:31) 기록 없이 꺼져 이쪽으로
        lock, stop = os.path.join(OUT, 'loop.lock'), os.path.join(OUT, 'stop')
        if os.path.exists(stop):
            log('예약 — 끔 표시(stop)가 있어 건너뜀'); return
        try:
            if time.time() - os.path.getmtime(lock) < 600:
                return   # 창으로 켠 고리가 돌고 있으면 그쪽이 한다(두 번 부르지 않게)
        except FileNotFoundError:
            pass
        if not (HOURS[0] <= now().hour < HOURS[1]):
            return
        log('예약 회차'); one(); return
    os.makedirs(OUT, exist_ok=True)
    lock, stop = os.path.join(OUT, 'loop.lock'), os.path.join(OUT, 'stop')
    try:
        if time.time() - os.path.getmtime(lock) < 600:
            sys.exit('이미 돌고 있다(loop.lock) — 끄려면 RUN_compare_stop.bat')
    except FileNotFoundError:
        pass
    if os.path.exists(stop):
        os.remove(stop)
    log('켬')
    done = None
    while True:
        try:   # 2026-10-15 14:48 기록 없이 멈췄다 — 한 바퀴에서 무슨 일이 나도 고리는 이어 가고 남긴다
            open(lock, 'w').write(str(os.getpid()))
            if os.path.exists(stop):
                os.remove(stop); os.remove(lock); log('끔'); return
            n = now(); key = n.strftime('%Y%m%d%H')
            if HOURS[0] <= n.hour < HOURS[1] and n.minute >= 5 and done != key:
                done = key; one()
        except Exception as e:
            log('고리 오류', type(e).__name__, str(e)[:160])
        time.sleep(60)


if __name__ == '__main__':
    main()
