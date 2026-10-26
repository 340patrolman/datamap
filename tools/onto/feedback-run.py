# -*- coding: utf-8 -*-
# 현장 기록 되먹임 한 번에(2026-10-26 · 소유자 「권하는 차례대로」 4번 — 서버를 두지 않는 원칙은 그대로 · 손 가는 일만 줄인다)
#   ① 다운로드 폴더(그리고 07_API키/out/onto_logs/in)에서 지도가 내보낸 기록 파일(tg-*.csv · 지도기록*.csv)을 찾아 onto_logs/in/ 으로 옮긴다
#   ② tools/onto/log-ingest.py(질문·결정·가설 기록 → 현장 판단 후보) · tools/onto/act-effect.py(현장 조치 → 전·뒤 속도) 를 차례로 돌린다
#   결과는 저장소 밖 07_API키/out/onto_logs/ 에만 — 형님이 「맞다」 한 줄만 규칙 장부(rules-bake.py FIELD)로
# 쓰기: py -3.12 -X utf8 tools/onto/feedback-run.py        (또는 07_API키\현장기록_되먹임.bat 두 번 누르기)
import os, glob, shutil, subprocess, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
IN = os.path.join(KB, '07_API키', 'out', 'onto_logs', 'in'); os.makedirs(IN, exist_ok=True)
DL = os.path.join(os.path.expanduser('~'), 'Downloads')
moved = []
for pat in ('tg-*.csv', 'tg-*.txt', '지도기록*.csv'):
    for f in glob.glob(os.path.join(DL, pat)):
        dst = os.path.join(IN, os.path.basename(f))
        if os.path.exists(dst): dst = os.path.join(IN, datetime.datetime.now().strftime('%H%M%S_') + os.path.basename(f))
        shutil.move(f, dst); moved.append(os.path.basename(dst))
print('다운로드에서 옮긴 기록 파일', len(moved), moved[:10])
print('넣는 곳의 파일', len(glob.glob(os.path.join(IN, '*.csv')) + glob.glob(os.path.join(IN, '*.txt'))))
for tool in ('log-ingest.py', 'act-effect.py'):
    print('──', tool)
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'tools', 'onto', tool)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    print((r.stdout or '').strip()[-1500:] or '(출력 없음)')
    if r.returncode: print('⚠ 끝 코드', r.returncode, (r.stderr or '').strip()[-800:])
print('결과 폴더:', os.path.dirname(IN))
