# -*- coding: utf-8 -*-
# 반포 블록 시뮬레이터 엔진 검사(1단계) — 머리 없는 크롬에서 js/sim.js 를 data/sim-banpo.json 으로 돌려 정답을 아는 값을 맞대 본다
#   ① 4031 현시가 현시도와 1초 단위로 같다(토 패턴 15 · 주기 180 · 49·43·48·40 / 일 16시 패턴 14 의 dir 줄)
#   ② 차가 사라지거나 생기지 않는다(만든 차 = 끝난 차 + 망 안 + 망 밖 대기)
#   ③ 넘침이 수요에서 온다 — 신세계·분수를 끄면 정점 대기가 작다
#   ④ 두 판(같은 씨앗)은 같은 차를 쓴다 · 16~22시 한 판이 폰에서도 견딜 시간 안에 끝난다
#   ⑥ 자동으로 엮은 구역(data/sim-<이름>.json · area-bake.py)마다 — 차 보존 · 길 못 찾은 차 0 · 신호 계획이 있다
#   ⑤ 재현 — 10/18 설정은 블록 둘레가 막혔다가 21~22시대에 풀리고, 10/11 설정은 막히지 않는다(실측 속도와 맞대 본 표는 diag)
# 쓰기: py -3.12 -X utf8 tools/sim/sim-check.py   (끝 코드 1 이면 실패)
#       py -3.12 -X utf8 tools/sim/sim-check.py diag   → 실측 속도와 맞대 본 표만
import os, sys, json, subprocess, tempfile, re, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
DIAG = 'diag' in sys.argv[1:]
TEST = open(os.path.join(HERE, 'sim-diag.js'), encoding='utf-8').read() + ('' if DIAG else open(os.path.join(HERE, 'sim-test.js'), encoding='utf-8').read())


def main():
    M = open(os.path.join(ROOT, 'data', 'sim-banpo.json'), encoding='utf-8').read()
    js = open(os.path.join(ROOT, 'js', 'sim.js'), encoding='utf-8').read()
    AR = {os.path.basename(f)[4:-5]: json.load(open(f, encoding='utf-8')) for f in glob.glob(os.path.join(ROOT, 'data', 'sim-*.json')) if not f.endswith('sim-banpo.json')}
    html = ('<!doctype html><meta charset="utf-8"><body><pre id="out">running</pre><script>window.__DIAG=' + ('1' if DIAG else '0') + ';window.__M=' + M.replace('</', '<\\/') +
            ';window.__AREAS=' + json.dumps(AR, ensure_ascii=False).replace('</', '<\\/') + ';</script><script>' + js +
            '</script><script>' + TEST + '</script>')
    d = tempfile.mkdtemp()
    f = os.path.join(d, 'simcheck.html'); open(f, 'w', encoding='utf-8').write(html)
    exe = [c for c in CHROME if os.path.exists(c)][0]
    r = subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=120000', '--run-all-compositor-stages-before-draw',
                        '--user-data-dir=' + os.path.join(d, 'u'), '--dump-dom', 'file:///' + f.replace('\\', '/')], capture_output=True, timeout=300)
    dom = r.stdout.decode('utf-8', 'replace')
    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    txt = m.group(1) if m else dom[:2000]
    txt = txt.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    print(txt)
    sys.exit(0 if 'ALL_OK' in txt else 1)


if __name__ == '__main__':
    main()
