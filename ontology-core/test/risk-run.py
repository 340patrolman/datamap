# -*- coding: utf-8 -*-
"""네비 가르고 risk-six.json 시험 — 표의 줄마다 같은 교차로를 전체 코어(core-six.json) + query.js 의 q1 으로 물은 답과 맞댄다
  (표는 파이썬 tools/gargo-risk.py 가 뽑고 · 답은 브라우저에서 돈 query.js — 서로 다른 코드).
  또 여섯 구 코어의 서초 교차로가 서초 코어(core-seocho.json)와 같은지 — 경계 칸 때문에 다를 수 있는 곳은 「둘레 구 칸이 더해진 것」만 허용.
  쓰기: py -3.12 -X utf8 ontology-core/test/risk-run.py   (끝 코드 1 = 실패)
"""
import json, os, sys, time, socket, threading, http.server, functools
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE); ROOT = os.path.dirname(CORE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'check'))
from cdp import Chrome
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
C = []
def ck(n, ok, got=''): C.append((n, bool(ok), str(got)[:220]))
c = Chrome()
JS = r'''(async function(){ var g=function(u){return fetch(u).then(function(r){return r.json()})};
 var six=new OntoCore(await g('/ontology-core/data/core-six.json')), sc=new OntoCore(await g('/ontology-core/data/core-seocho.json')), rk=await g('/gargo/risk-six.json'), bad=[], n=0, diff=[];
 rk.rows.forEach(function(q){ var a=six.q1('INT-'+q[0]); n++; var mv=a&&a.mainViolations[0];
   var want=[a.nm,a.acc.total,a.acc.dead,a.acc.serious,a.acc.ped,a.acc.night,mv?mv.id.slice(4):'',mv?mv.n:0,a.cams.length,a.actions.length,a.acc.years.slice(-3).join(',')];
   var got=[q[1],q[4],q[5],q[6],q[7],q[8],q[9],q[10],q[11],q[12],q[13].join(',')];
   if(JSON.stringify(want)!==JSON.stringify(got)) bad.push(q[0]+' '+JSON.stringify(got)+' / '+JSON.stringify(want)); });
 var miss=six.core.objects.filter(function(o){ if(o.t!=='INT')return false; var a=six.q1(o.id); return a.acc&&a.acc.total>0&&!rk.rows.some(function(q){return 'INT-'+q[0]===o.id}); }).length;
 sc.core.objects.forEach(function(o){ if(o.t!=='INT')return; var a=sc.q1(o.id), b=six.q1(o.id); var ya=a.acc?a.acc.years:null, yb=b.acc?b.acc.years:null;
   if(JSON.stringify(ya)!==JSON.stringify(yb)) diff.push({id:o.id, nm:o.nm, more: !ya || ya.every(function(v,i){return yb[i]>=v}), a:ya, b:yb}); });
 return JSON.stringify({n:n, bad:bad.slice(0,5), nbad:bad.length, miss:miss, diff:diff}); })()'''
try:
    c.go('http://127.0.0.1:%d/ontology-core/test/test.html' % port, 1.5)
    R = None
    for i in range(3):
        try: R = json.loads(c.cmd('Runtime.evaluate', expression=JS, awaitPromise=True, returnByValue=True)['result']['value']); break
        except Exception as e: time.sleep(1)
finally:
    c.close(); srv.shutdown()
if not R: print('❌ 답을 못 받았다'); sys.exit(1)
ck('표의 %d줄 모두 — 이름·10년 사고·사망·중상·보행자·밤·주 위반(코드·건수)·카메라·조치 수·최근 3해가 query.js q1 답과 같다' % R['n'], R['nbad'] == 0, R['bad'])
ck('사고 칸이 있는 교차로는 표에 다 있다', R['miss'] == 0, R['miss'])
ck('여섯 구 코어의 서초 교차로 = 서초 코어(다르면 둘레 구 칸이 더해진 것만 · 줄지 않음)', all(d['more'] for d in R['diff']), [(d['nm'], d['a'], d['b']) for d in R['diff'] if not d['more']][:3])
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got if got and not ok else ''))
print('  (경계에서 둘레 구 사고 칸이 더해진 서초 교차로 %d곳: %s)' % (len(R['diff']), ', '.join(d['nm'] for d in R['diff'][:8])))
print(('✅ 위험 표 시험 통과 %d/%d' if n == len(C) else '❌ 위험 표 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
