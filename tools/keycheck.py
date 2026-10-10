# -*- coding: utf-8 -*-
# 커밋 전 열쇠 검사(CLAUDE.md 절대 규칙 「커밋 전에 키 앞 12자로 grep(0 이어야 함)」을 한 번에)
#   py -3.12 -X utf8 tools/keycheck.py        → 올릴 준비가 된 변경(git diff --cached)에 열쇠 앞 12자가 있으면 이름만 찍고 1 로 끝난다(열쇠 값은 찍지 않는다)
import json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KF = os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json')

def vals(o, path=''):
    if isinstance(o, dict):
        for k, v in o.items(): yield from vals(v, path + '/' + str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o): yield from vals(v, path + '/' + str(i))
    elif isinstance(o, str) and len(o) >= 16: yield path, o

def main():
    if not os.path.exists(KF): print('keys.json 없음 — 검사 못 함:', KF); sys.exit(2)
    diff = subprocess.run(['git', '-C', ROOT, 'diff', '--cached'], capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
    bad = [p for p, v in vals(json.load(open(KF, encoding='utf-8-sig'))) if v[:12] in diff]
    if bad: print('⛔ 올릴 변경에 열쇠가 들어 있다 — 커밋하지 말 것:', ', '.join(bad)); sys.exit(1)
    print('✅ 열쇠 검사 통과(' + str(len(diff.splitlines())) + '줄 · 열쇠 0)')

if __name__ == '__main__':
    main()
