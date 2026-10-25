# -*- coding: utf-8 -*-
# 자동 구역을 평소 속도로 맞추기 — 머리 없는 크롬에서 tgSim.calibrate 를 돌려 결과(설계값 배율)를 구역 자료 cal 칸에 적는다
#   쓰기: py -3.12 -X utf8 tools/sim/sim-cal.py <이름>…   (area-bake.py 로 다시 구우면 다시 돌린다)
import os, sys, json, subprocess, tempfile, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
CHROME = [r'C:\Program Files\Google\Chrome\Application\chrome.exe', r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe']
js = open(os.path.join(ROOT, 'js', 'sim.js'), encoding='utf-8').read()
for nm in sys.argv[1:]:
    f = os.path.join(ROOT, 'data', 'sim-' + nm + '.json')
    M = json.load(open(f, encoding='utf-8'))
    M.pop('cal', None)
    html = ('<!doctype html><meta charset="utf-8"><pre id="out">x</pre><script>window.__M=' + json.dumps(M, ensure_ascii=False).replace('</', '<\\/') + ';</script><script>' + js +
            '</script><script>try{document.getElementById("out").textContent=JSON.stringify(tgSim.calibrate(__M,{}));}catch(e){document.getElementById("out").textContent="ERR "+e.stack;}</script>')
    d = tempfile.mkdtemp()
    p = os.path.join(d, 'cal.html')
    open(p, 'w', encoding='utf-8').write(html)
    exe = [c for c in CHROME if os.path.exists(c)][0]
    r = subprocess.run([exe, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=300000', '--user-data-dir=' + os.path.join(d, 'u'),
                        '--dump-dom', 'file:///' + p.replace(os.sep, '/')], capture_output=True, timeout=600)
    t = re.search(r'<pre id="out">(.*?)</pre>', r.stdout.decode('utf-8', 'replace'), re.S).group(1).replace('&quot;', '"').replace('&amp;', '&')
    if t.startswith('ERR'):
        print(nm, t)
        sys.exit(1)
    cal = json.loads(t)
    M['cal'] = cal
    json.dump(M, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(nm, '맞춤', ' → '.join('%d/%d' % (h['hit'], h['n']) for h in cal['hist']), '· 전체 배율', cal['all'], '· 들어오는 길 배율', cal['scale'])
