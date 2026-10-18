# -*- coding: utf-8 -*-
"""T-Book ontology.html ver.4.2 의 「서초 교차로 — 자료로 시작」 시험 — 블록 안 교차로마다
  ontology.html#core=INT-번호 로 열어 저장된 지도(localStorage onto3_state.B)와 화면 글을,
  같은 교차로를 전체 코어(core-seocho.json) + query.js(시험 32/32 통과한 질의)로 물은 답과 맞댄다.
  쓰기: py -3.12 -X utf8 ontology-core/test/tbook-run.py <ontology.html 경로>   (끝 코드 1 = 실패)
"""
import json, os, sys, time, socket, threading, http.server, functools, shutil, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE); ROOT = os.path.dirname(CORE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'check'))
from cdp import Chrome
ONTO = sys.argv[1]
W = tempfile.mkdtemp(prefix='ontot_')
shutil.copy(ONTO, os.path.join(W, 'ontology.html')); shutil.copy(os.path.join(CORE, 'query.js'), os.path.join(W, 'query.js'))
shutil.copy(os.path.join(CORE, 'data', 'core-seocho.json'), os.path.join(W, 'core.json'))
open(os.path.join(W, 'ref.html'), 'w', encoding='utf-8').write('<!doctype html><meta charset="utf-8"><script src="query.js"></script><script>fetch("core.json").then(r=>r.json()).then(c=>{window.Q=new OntoCore(c);window.__ok=1});</script>')
blk = json.load(open(os.path.join(CORE, 'data', 'tbook-block-seocho.json'), encoding='utf-8'))
INTS = [o['id'] for o in blk['objects'] if o['t'] == 'INT']
s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
H = functools.partial(http.server.SimpleHTTPRequestHandler, directory=W); H.log_message = lambda *a: None
srv = http.server.ThreadingHTTPServer(('127.0.0.1', port), H); threading.Thread(target=srv.serve_forever, daemon=True).start()
C = []
def ck(n, ok, got=''): C.append((n, bool(ok), str(got)[:200]))
c = Chrome(); c.phone(375, 812)
B = 'http://127.0.0.1:%d/' % port
NQ = [0]
def U(h=''):
    NQ[0] += 1; return B + 'ontology.html?n=%d' % NQ[0] + h
try:
    c.cmd('Page.addScriptToEvaluateOnNewDocument', source='window.__E=[];addEventListener("error",function(e){__E.push(String(e.message))});')
    c.go(B + 'ref.html', 1.5)
    for i in range(40):
        if c.ev('window.__ok||0'): break
        time.sleep(0.2)
    REF = json.loads(c.ev('JSON.stringify(%s.map(function(i){var a=Q.q1(i),b=Q.q2(i),v=a.mainViolations[0];return{id:i,nm:a.nm,mv:a.mainViolations.slice(0,3).map(function(x){return x.nm}),laws:v?Q.q3(v.id).laws.map(function(l){return{t:l.title,p:l.precedents.map(function(p){return p.court+" "+p.no})}}):[],cams:a.cams.length,zones:Math.min(3,a.zones.length),acts:b.actions.map(function(x){return{w:x.what,ym:x.ym||"",c:x.compare?"사고 앞 2해("+x.compare.before.join("·")+") "+x.compare.beforeN+"건 → 뒤 2해("+x.compare.after.join("·")+") "+x.compare.afterN+"건":"비교 못 함 — "+x.noCompare}}),tot:a.acc?a.acc.total:0}}))' % json.dumps(INTS)))
    # 처음 화면 — 새 단추
    c.go(U(), 1.2); c.ev('localStorage.clear()'); c.go(U(), 1.2)
    ck('처음 화면에 「서초 교차로 — 자료로 시작」 단추', '서초 교차로 — 자료로 시작' in c.ev('document.getElementById("ctlin").innerText'))
    c.go(U('#core'), 1.2)
    lst = c.ev('[].map.call(document.querySelectorAll("#ctlin .ch"),function(b){return b.textContent}).join("\\n")')
    ck('#core — 교차로 %d곳 목록 · 조치 있는 곳(교통과 출력물 2곳 · 2026-10-18)이 먼저' % len(INTS), lst.count('· 10년') == len(INTS) and all('조치' in x for x in lst.split('\n')[:2]) and '조치' not in lst.split('\n')[2], lst.split('\n')[:4])
    ck('#core — 해시를 떼어 낸다', c.ev('location.hash') == '', c.ev('location.hash'))
    bad = []
    for r in REF:
        c.go(U('#core=' + r['id']), 0.6)
        st = json.loads(c.ev('localStorage.getItem("onto3_state")') or '{}'); b = st.get('B') or {}
        T = {t['name']: t for t in b.get('types', [])}
        txt = c.ev('document.getElementById("msgs").innerText')
        nm = [o['name'] for o in T.get('교차로', {}).get('objs', [])]
        mv = [o['name'] for o in T.get('위반유형', {}).get('objs', [])]
        law = [o['name'] for o in T.get('법규 항목', {}).get('objs', [])]
        fac = T.get('시설', {}).get('objs', [])
        acts = [{'w': a['name'], 'ym': a['date'], 'c': a['result']} for a in b.get('actions', [])]
        want_law = list(dict.fromkeys(l['t'] for l in r['laws']))
        e = []
        if nm != [r['nm']]: e.append(('이름', nm))
        if mv != r['mv']: e.append(('주 위반', mv, r['mv']))
        if law[:len(want_law)] != want_law: e.append(('법규', law, want_law))
        if len(fac) != r['cams'] + r['zones']: e.append(('시설', len(fac), r['cams'], r['zones']))
        if acts != r['acts']: e.append(('조치', acts[:2], r['acts'][:2]))
        if ('10년 %d건' % r['tot']) not in txt and r['tot']: e.append(('사고 합 글', r['tot']))
        if st.get('node') != 'grow': e.append(('이어서 키우기로', st.get('node')))
        for l in r['laws']:
            for p in l['p']:
                if p not in txt: e.append(('판례 글', p))
        if e: bad.append((r['nm'], e))
    ck('교차로 %d곳 모두 — 이름·주 위반 3·법규·판례·시설·조치(앞뒤 2해)가 전체 코어 + query.js 답과 같다' % len(REF), not bad, bad[:3])
    c.go(U('#core=INT-548'), 0.8)
    t = c.ev('document.getElementById("msgs").innerText')
    ck('서울성모병원 — 교통과 조치 이력이 나오지 않는다(2026-10-18 공공데이터만 · 교통과 출력물은 2곳)', '꼬리물기 해소' not in t and '서울성모병원' in t, t[:200])
    ob = c.ev('JSON.stringify([].filter.call(document.querySelectorAll(".bub"),function(b){return b.scrollWidth>b.clientWidth+1}).map(function(b){return b.scrollWidth+"/"+b.clientWidth}))')
    ck('말풍선 안 넘침(해마다 사고 표 포함)', ob == '[]', ob)
    ck('375px 가로 넘침 없음', c.ev('document.documentElement.scrollWidth<=document.documentElement.clientWidth+1'), c.ev('document.documentElement.scrollWidth'))
    c.ev('document.querySelector(\'[data-act="save"]\').click()')
    h = json.loads(c.ev('localStorage.getItem("onto3_history")') or '[]')
    ck('「기록에 저장」 → 지난 기록에 남는다(이어서 키우기)', len(h) == 1 and h[0]['title'].startswith('서울성모병원'), [x.get('title') for x in h])
    c.go(U('#field'), 1.0)
    ck('옛 입구 #field 그대로(현장 대응 첫 질문)', '무엇을 정하려고 하나요' in c.ev('document.getElementById("msgs").innerText'))
    c.go(U('#core=INT-999999'), 0.8)
    ck('없는 번호는 목록으로', '자료로 시작' in c.ev('document.getElementById("msgs").innerText'))
    ck('스크립트 오류 0', c.ev('JSON.stringify(window.__E)') == '[]', c.ev('JSON.stringify(window.__E)'))
    req = c.ev('JSON.stringify(performance.getEntriesByType("resource").map(function(x){return x.name}))')
    ck('밖으로 나가는 요청 0', req == '[]', req)
finally:
    c.close(); srv.shutdown(); shutil.rmtree(W, ignore_errors=True)
n = sum(1 for x in C if x[1])
for name, ok, got in C: print(('  ✅ ' if ok else '  ❌ ') + name + (' — ' + got if got and not ok else ''))
print(('✅ ontology.html 코어 시험 통과 %d/%d' if n == len(C) else '❌ ontology.html 코어 시험 실패 %d/%d') % (n, len(C)))
sys.exit(0 if n == len(C) else 1)
