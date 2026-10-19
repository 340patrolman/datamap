# -*- coding: utf-8 -*-
# T-Data 신호 역사 API — 새벽 3시대 「교차로 하나(itstId)」 호출 시험 10건(2026-10-18 소유자 지시)
#   왜: 역사 API 는 01·07·13·19시 시작 6시간 묶음의 뒤쪽 시간에 서버 순서 뒤쪽(서초 1,668번째~)이 HTTP 500 으로 끊긴다(10-15 실측) ·
#       10-15 16:13 에 itstId 를 넣어 봤을 때도 500 — 묶음 셋째 시간(03시대)에 교차로 하나씩은 받히는지 본다
#   방법: 02:58 에 잔여시간 훑기(sweep · api t) 하나만 멈춘다(같은 열쇠·같은 API 의 5분 제한을 시험이 뺏지 않게 — 429 가 쌓이면 수집기가 열쇠를 여섯 시간 쉬게 한다)
#         03:00 부터 3분마다 10건 · 열쇠 KEY1/KEY2 번갈아(열쇠마다 6분 간격) · 서초 교차로 10곳(서버 순서 1,668~1,963번째에 고르게)
#         03:33 에 tools/signal/sweep-run.ps1 로 멈춘 훑기를 다시 띄운다 · 호출은 keyday.json(하루 999)에 같이 센다
#   결과: ../07_API키/TData_새벽시험_20261019.md (열쇠 값은 쓰지 않는다)
#   띄우기: Start-Process py -ArgumentList '-3.12','-X','utf8','-u','tools\signal\tdata-night-test.py' -WindowStyle Hidden  (기다렸다가 스스로 돈다 · PC 가 절전·로그아웃되면 못 돈다)
import os, sys, time, json, datetime, subprocess, importlib.util, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
DAY = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date(2026, 10, 19)
OUT = os.path.join(KB, 'TData_새벽시험_%s.md' % DAY.strftime('%Y%m%d'))
sp = importlib.util.spec_from_file_location('sb', os.path.join(ROOT, 'tools', 'signal', 'spat-bake.py')); SB = importlib.util.module_from_spec(sp); sp.loader.exec_module(SB)
PICK = [('1668', '2610', '경문고교'), ('1822', '22979', '씨티극장(연등)'), ('1840', '1375', '서초롯데캐슬아파트'), ('1856', '7513', '시민의숲공영주차장'), ('1873', '146', '탑성마을'),
        ('1891', '2665', '예술의전당'), ('1912', '3993', '내방역동측'), ('1928', '4031', '강남터미널고가밑'), ('1944', '4568', '파고타워앞'), ('1963', '24001', '서초소방서(연등)')]
at = lambda h, m: datetime.datetime.combine(DAY, datetime.time(h, m))


def wait(t):
    while datetime.datetime.now() < t:
        time.sleep(min(30, max(1, (t - datetime.datetime.now()).total_seconds())))


def ps(cmd):
    return subprocess.run(['powershell', '-NoProfile', '-Command', cmd], capture_output=True, text=True, encoding='utf-8', errors='ignore').stdout.strip()


def main():
    wait(at(2, 58))
    stopped = ps("$p = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*spat-bake.py*sweep*' -and $_.CommandLine -notlike '*--api*' -and $_.Name -notlike 'powershell*' }; $p | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }; @($p).Count")
    rows = []
    for i, (pos, itst, nm) in enumerate(PICK):
        wait(at(3, 0) + datetime.timedelta(minutes=3 * i))
        kl = 'KEY1' if i % 2 == 0 else 'KEY2'
        u = SB.BASE + '?apikey=' + SB.keyval(kl) + '&pageNo=1&numOfRows=3000&itstId=%s' % itst
        t0 = time.time(); code = None; n = None; note = ''
        try:
            b = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read()
            code = 200
            try:
                d = json.loads(b); n = len(d) if isinstance(d, list) else len(d.get('data') or d.get('items') or [])
                if isinstance(d, list) and d:
                    ts = sorted(str(x.get('trsmTm') or x.get('regDt') or '') for x in d if isinstance(x, dict))
                    note = '받은 줄 시각 %s ~ %s' % (ts[0], ts[-1]) if ts and ts[0] else ''
            except Exception:
                note = '응답이 JSON 아님(%d B)' % len(b)
        except urllib.error.HTTPError as e:
            code = e.code; note = (e.read()[:120].decode('utf-8', 'replace') if hasattr(e, 'read') else '').replace(SB.keyval(kl), '***')
        except Exception as e:
            code = type(e).__name__
        try: SB.kd_add(kl)
        except Exception: pass
        rows.append((datetime.datetime.now().strftime('%H:%M:%S'), kl, pos, itst, nm, code, n, round(time.time() - t0, 1), note))
    wait(at(3, 33))
    rs = ps("& '%s'" % os.path.join(ROOT, 'tools', 'signal', 'sweep-run.ps1'))
    ok = sum(1 for r in rows if r[5] == 200 and r[6])
    from collections import Counter
    c = Counter(str(r[5]) for r in rows)
    L = ['# T-Data 신호 역사 API — 새벽 3시대 교차로 하나씩 호출 시험 (%s)' % DAY.isoformat(), '',
         '- API: v2xSignalPhaseTimingInformation (잔여시간 역사) · `itstId` 하나 · `numOfRows=3000` · 열쇠 KEY1/KEY2 번갈아 · 3분 간격',
         '- 시각대: 01시 시작 6시간 묶음의 셋째 시간(03시대) — 10-15 실측으로 묶음 뒤쪽 시간에 서버 순서 뒤쪽 교차로가 500 으로 끊기던 자리',
         '- 시험 동안 잔여시간 훑기 %s개를 멈췄다가 03:33 다시 띄움: %s' % (stopped or '?', (rs or '').replace(chr(10), ' / ')), '',
         '## 결과: 성공(200·줄 있음) %d / 10 · 응답 코드 %s' % (ok, dict(c)), '',
         '| 시각 | 열쇠 | 서버 순서 | 번호 | 교차로 | 응답 | 줄 수 | 걸린 초 | 비고 |', '|---|---|---|---|---|---|---|---|---|']
    L += ['| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % tuple('' if x is None else x for x in r) for r in rows]
    open(OUT, 'w', encoding='utf-8').write('\n'.join(L) + '\n')


if __name__ == '__main__':
    main()
