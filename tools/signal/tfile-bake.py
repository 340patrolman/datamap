# -*- coding: utf-8 -*-
# 🚦 T-Data 신호 하루치 파일(data_id 10382 「전일 신호제어기 신호 및 잔여시간 정보」 · signalPhaseTimeFusion_YYYYMMDD.zip) → 수집기와 같은 red 기록
#   (2026-11-21 · 코워크 조사: 역사 API 셋은 2026-11-15 로 끝난다는 공지(T-Data 공지 boardId=104 · 10-21) — 단기 이력은 하루치 파일로 옮겨 감 · 로그인 없이 받아짐 실측)
#   파일 = 교차로마다 1초 줄(잔여 초 RMDR_CS · 상태 STAT_NM) · 하루 약 1,300만~1,700만 줄 · zip 약 370~470MB(풀면 약 6GB) · 서울 약 2,520 교차로
#   ⚠ 줄은 1초마다지만 교차로마다 「약 8분마다 1분 창」(11-20 18시 실측 · 18:08:00~18:08:59 → 18:16:00~) — 한 주기를 통째로 보는 창이 드물다
#   ⚠ 하루 24시간이 다 있지 않다(11-20 파일: 4·13·14·23시 없음 · 12시 1곳 · 시마다 교차로당 몇 분) — 그래도 시마다 2,400곳 넘게 실린 시가 많다
#   하는 일: zip 을 풀지 않고 흘려 읽어 (교차로, 시)마다 연속 줄 최대 MAXR 개를 모아 spat-bake 의 reduce_one 으로 줄인다 → 07_API키/out/tdata/red/<번호>_<날짜>_<시>5959x.json
#            (이름의 날짜·시 = 자료의 시각 · 끝 x = 잔여+상태 역사(api f)와 같은 꼴) → 수집기의 다음 굽기(build)가 그대로 섞는다 · prune 이 (교차로, 요일 갈래, 시)마다 최신 둘만 남긴다
#   이미 그 (교차로, 요일 갈래, 시) 칸에 red 기록이 둘 이상 있으면 쓰지 않는다(빈 칸 먼저 · red 폴더가 불지 않게)
#   원본 zip 은 저장소 밖 07_API키/out/tdata/file/ → 다 줄이면 NAS datamap-raw/tdata_file/ 로 옮긴다(PowerShell 몫 · 이 도구는 지우지 않는다)
#   py -3.12 -X utf8 tools/signal/tfile-bake.py list            # 받을 수 있는 날짜
#   py -3.12 -X utf8 tools/signal/tfile-bake.py get [YYYYMMDD…]  # 안 받은 날 받기(없으면 전부)
#   py -3.12 -X utf8 tools/signal/tfile-bake.py red [YYYYMMDD…]  # 받은 zip → red(이미 한 날은 건너뜀 · done_<날짜>.json)
import os, sys, io, re, json, time, zipfile, datetime, importlib.util, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'tdata'); FD = os.path.join(RAW, 'file')
sp = importlib.util.spec_from_file_location('spat', os.path.join(HERE, 'spat-bake.py')); SP = importlib.util.module_from_spec(sp); sp.loader.exec_module(SP)
PAGE = 'https://t-data.seoul.go.kr/dataprovide/trafficdataviewfile.do?data_id=10382'
DL = 'https://t-data.seoul.go.kr/dataprovide/download.do?id='
MAXR = 900      # (교차로, 시)마다 연속 15분이면 주기 여럿을 읽는다(수집기 역사 훑기도 한 번에 몇 분)
MINR = 240      # 수집기 sweep 과 같은 문턱
RED = os.environ.get('TFILE_RED') or os.path.join(RAW, 'red')   # 시험할 때만 다른 폴더(TFILE_RED) — 그때는 done 표시도 안 남긴다


def listing():
    h = urllib.request.urlopen(urllib.request.Request(PAGE, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
    return {d: i for i, d in re.findall(r'value="(\d+)">signalPhaseTimeFusion_(\d{8})\.zip', h)}


def get(days):
    os.makedirs(FD, exist_ok=True); L = listing()
    for d in sorted(days or L):
        if d not in L: print(d, '목록에 없음', flush=True); continue
        fn = os.path.join(FD, 'signalPhaseTimeFusion_%s.zip' % d)
        if os.path.exists(fn) or os.path.exists(os.path.join(FD, 'done_%s.json' % d)): continue
        t = time.time(); tmp = fn + '.part'
        with urllib.request.urlopen(urllib.request.Request(DL + L[d], headers={'User-Agent': 'Mozilla/5.0'}), timeout=600) as r, open(tmp, 'wb') as o:
            while True:
                b = r.read(1 << 20)
                if not b: break
                o.write(b)
        if not zipfile.is_zipfile(tmp): os.remove(tmp); print(d, 'zip 아님 — 버림', flush=True); continue
        os.replace(tmp, fn); print(d, '받음', round(os.path.getsize(fn) / 1e6), 'MB', round(time.time() - t), '초', flush=True)


def have():
    """지금 red 에 있는 (교차로, 요일 갈래, 시)마다 기록 수 — 이름에서 읽는다(prune 과 같은 셈)"""
    G = {}
    for e in os.scandir(RED):
        b = e.name[:-5]
        try:
            i, d, hm = b.split('_')[:3]; dt = datetime.datetime.strptime(d + hm[:6], '%Y%m%d%H%M%S')
        except Exception:
            continue
        if b.endswith('p'): continue
        k = (i, SP.cls_of(dt.isoweekday() % 7, dt.strftime('%Y-%m-%d')), dt.hour); G[k] = G.get(k, 0) + 1
    return G


def red(days):
    G = have(); tot = {'w': 0, 'skip': 0, 'none': 0}
    for d in sorted(days or [re.findall(r'\d{8}', f)[0] for f in os.listdir(FD) if f.endswith('.zip')]):
        fn = os.path.join(FD, 'signalPhaseTimeFusion_%s.zip' % d); dn = os.path.join(FD, 'done_%s.json' % d)
        if not os.path.exists(fn) or os.path.exists(dn): continue
        dt0 = datetime.datetime.strptime(d, '%Y%m%d'); cl = SP.cls_of(dt0.isoweekday() % 7, dt0.strftime('%Y-%m-%d'))
        z = zipfile.ZipFile(fn)
        def lines():
            f = io.TextIOWrapper(z.open(z.infolist()[0]), encoding='utf-8', errors='replace'); f.readline(); return f
        f0 = io.TextIOWrapper(z.open(z.infolist()[0]), encoding='utf-8', errors='replace')
        H = f0.readline().rstrip('\n').split(','); f0.close(); iU, iI, iH = H.index('TRSM_UTC_TIME'), H.index('ITST_ID'), H.index('TRSM_HR')
        # 이름: NT_STSG_RMDR_CS → ntStsgRmdrCs (수집기 API 이름 = 방향 + 이동류(St·Lt·Ut·Bs·Bc·Pd) + sgRmdrCs/sgStatNm)
        cols = [(j, c[:2].lower() + c[3] + c[4].lower() + 'sg' + ('RmdrCs' if c.endswith('RMDR_CS') else 'StatNm')) for j, c in enumerate(H) if c.endswith('_RMDR_CS') or c.endswith('_STAT_NM')]
        t = time.time(); st = {'w': 0, 'skip': 0, 'none': 0, 'rows': 0}; hrs = set()
        # 파일은 시 순서가 아니라 토막마다 0~23시를 되풀이한다(11-20 실측) → 시마다 한 번씩 흘려 읽는다(한 번 약 15초)
        for h in range(24):
            hs = str(h); B = {}
            for line in lines():
                p = line.split(',', max(iH, iI) + 1)
                if len(p) <= max(iH, iI) or p[iH] != hs: continue
                B.setdefault(p[iI], []).append(line)
            if not B: continue
            hrs.add(h)
            for i, L in B.items():
                st['rows'] += len(L)
                if G.get((i, cl, h), 0) >= 2: st['skip'] += 1; continue
                if len(L) < MINR: st['none'] += 1; continue
                rows = []
                for line in L:
                    p = line.rstrip('\n').split(',')
                    try: x = {'itstId': i, 'trsmUtcTime': int(p[iU])}
                    except (ValueError, IndexError): continue
                    for j, nm in cols:
                        v = p[j] if j < len(p) else ''
                        if v: x[nm] = int(v) if nm.endswith('Cs') else v
                    rows.append(x)
                r = SP.reduce_one(i, rows)
                if not r or not r.get('cyc'): st['none'] += 1; continue
                json.dump(r, open(os.path.join(RED, '%s_%s_%02d5959x.json' % (i, d, h)), 'w', encoding='utf-8'), ensure_ascii=False)
                G[(i, cl, h)] = G.get((i, cl, h), 0) + 1; st['w'] += 1
        if not os.environ.get('TFILE_RED'): json.dump({'day': d, 'hours': sorted(hrs), **st, 'sec': round(time.time() - t)}, open(dn, 'w', encoding='utf-8'), ensure_ascii=False)
        print(d, '시', len(hrs), '줄', st['rows'], '새 기록', st['w'], '칸 이미 참', st['skip'], '못 읽음', st['none'], round(time.time() - t), '초', flush=True)
        for k in tot: tot[k] += st[k]
    print('합', tot, flush=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    if not a or a[0] == 'list':
        L = listing(); print(len(L), '날', min(L), '~', max(L))
    elif a[0] == 'get': get(a[1:])
    elif a[0] == 'red':
        # (2026-11-21) 시험만 — 파일은 1초 줄이지만 「8분마다 1분 창」꼴이라(실측) reduce_one 이 주기를 거의 못 읽고(18시 2,515곳 중 756) 읽은 것도 수집기와 37%만 맞는다.
        #  창마다 색이 바뀐 때의 잔여로 녹·황·적 길이를 더해 주기를 내는 방법(scratch tf_cyc)도 수집기와 71~87% — 틀린 신호값은 사고라 운영 red 에는 넣지 않는다 → TFILE_RED 시험 폴더로만
        if not os.environ.get('TFILE_RED'): sys.exit('운영 red 에는 아직 쓰지 않는다 — TFILE_RED=<시험 폴더> 로만(수집기와 95% 넘게 맞으면 풀기)')
        red(a[1:])
