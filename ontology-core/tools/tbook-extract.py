# -*- coding: utf-8 -*-
"""온톨로지 코어 — T-Book 에서 법령 자료를 **읽기만** 해서 꺼낸다(T-Book 파일은 고치지 않는다).
  T-Book 을 머리 없는 크롬으로 열어 전역 값 LAWS(범칙금 DB) · PRECDOC(원문 대조된 판례) · APP_VERSION 을 JSON 으로 받는다.
  글은 그대로 옮긴다(정리하지 않는다 — T-Book 원칙 「판례·법령을 정리하면서 옮기기 금지」).
  쓰기: py -3.12 -X utf8 ontology-core/tools/tbook-extract.py <T-Book 을 내주는 주소(예 http://127.0.0.1:8791/index.html)>
  결과: ontology-core/src/tbook-law.json
"""
import json, os, sys, time, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); CORE = os.path.dirname(HERE); ROOT = os.path.dirname(CORE)
sys.path.insert(0, os.path.join(ROOT, 'tools', 'check'))
from cdp import Chrome
URL = sys.argv[1]
c = Chrome()
try:
    c.go(URL + '?t=%d' % int(time.time()), 2)
    c.ev("localStorage.setItem('entry_gate_ok','1');localStorage.setItem('lawrev_seen','1');1")
    c.go('about:blank', 0.3); c.go(URL + '?t=%d' % (int(time.time()) + 1), 8)
    raw = c.ev("JSON.stringify({ver: typeof APP_VERSION !== 'undefined' ? APP_VERSION : null, laws: typeof LAWS !== 'undefined' ? LAWS : null, precdoc: typeof PRECDOC !== 'undefined' ? PRECDOC : null, prec: typeof PRECEDENTS !== 'undefined' ? PRECEDENTS.map(function (p) { return { title: p.title, court: p.court, year: p.year, keywords: p.keywords }; }) : null})")
finally:
    c.close()
d = json.loads(raw)
if not d['laws'] or not d['precdoc']: raise SystemExit('LAWS/PRECDOC 를 못 읽었다')
out = {'schema': 'onto-tbook-law/1', 'made': datetime.datetime.now().isoformat(timespec='seconds'), 'source': 'T-Book %s(340patrolman/traffic-app index.html) 의 전역 값 그대로 — LAWS = 범칙금 DB(meta 조문 · penalty 범칙금·벌점 글 · 2026-10-08 월간 법령 점검) · PRECDOC = 원문 대조된 판례(사건번호 열쇠) · PRECEDENTS = 판례 목록(court 글에 법원·날짜·사건번호)' % d['ver'],
       'sha256_of_values': hashlib.sha256(json.dumps([d['laws'], d['precdoc']], ensure_ascii=False, sort_keys=True).encode()).hexdigest(),
       'ver': d['ver'], 'laws': d['laws'], 'precdoc': d['precdoc'], 'prec': d['prec']}
os.makedirs(os.path.join(CORE, 'src'), exist_ok=True)
p = os.path.join(CORE, 'src', 'tbook-law.json'); json.dump(out, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, indent=0)
print('판', d['ver'], '· LAWS', len(d['laws']), '· PRECDOC', len(d['precdoc']), '· PRECEDENTS', len(d['prec'] or []), '→', p, os.path.getsize(p), 'B')
