# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏛 주민센터 자리(게임 세션 2026-10-10 「agency-pts 의 jumin 에 좌표가 없어 못 그렸다」) — data/agency-pts.json 의 jumin 에 [위도, 경도]를 덧붙인다
#   주소(도로명) → 좌표 = 브이월드 주소 API(getcoord · type road · 키 keys.json vworld) · 하루 한도에 닿으면 멈추고 다음에 이어서(캐시 07_API키/out/govoffice/jumin_ll.json)
#   못 찾은 주소는 좌표를 넣지 않는다(지어 넣지 않는다) · agpts-bake.py 로 agency-pts.json 을 다시 구운 뒤에는 이 도구를 다시 돌린다(캐시가 있어 통신 없이 붙는다)
#   py -3.12 -X utf8 tools/region/jumin-geo.py
import json, os, re, time, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CP = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'govoffice', 'jumin_ll.json')
def main():
    K = json.load(open(os.path.join(os.path.dirname(ROOT), '07_API키', 'keys.json'), encoding='utf-8-sig'))['vworld']
    p = os.path.join(ROOT, 'data', 'agency-pts.json'); D = json.load(open(p, encoding='utf-8')); J = D['jumin']
    C = json.load(open(CP, encoding='utf-8')) if os.path.exists(CP) else {}; n = 0; stop = ''
    for code, v in J.items():
        addr = re.sub(r'\s*\(.*?\)\s*', ' ', v[2]).strip()
        if not addr or addr in C: continue
        q = {'service': 'address', 'request': 'getcoord', 'version': '2.0', 'crs': 'epsg:4326', 'address': addr, 'refine': 'true', 'simple': 'false', 'format': 'json', 'type': 'road', 'key': K}
        try: r = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.vworld.kr/req/address?' + urllib.parse.urlencode(q), headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8', 'replace'), strict=False)['response']
        except Exception as e: stop = type(e).__name__; break
        if r.get('status') == 'OK': pt = r['result']['point']; C[addr] = [round(float(pt['y']), 6), round(float(pt['x']), 6)]
        elif r.get('status') == 'NOT_FOUND': C[addr] = None
        else: stop = json.dumps(r.get('error'), ensure_ascii=False)[:120]; break
        n += 1; time.sleep(0.08)
        if n % 200 == 0: json.dump(C, open(CP, 'w', encoding='utf-8'), ensure_ascii=False); print(n, flush=True)
    json.dump(C, open(CP, 'w', encoding='utf-8'), ensure_ascii=False); got = 0
    for code, v in J.items():
        ll = C.get(re.sub(r'\s*\(.*?\)\s*', ' ', v[2]).strip()); J[code] = v[:3] + (ll if ll else [])
        got += 1 if ll else 0
    f = D.get('fields'); extra = ' · jumin 값 끝의 [위도, 경도] = 주소를 브이월드 주소 API 로 좌표로 바꾼 것(tools/region/jumin-geo.py · 못 찾은 곳은 없음)'
    if isinstance(f, str) and extra not in f: D['fields'] = f + extra
    json.dump(D, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('이번에 부른 수', n, '· 좌표 붙은 주민센터', got, '/', len(J), '· 못 찾은 주소', sum(1 for x in C.values() if x is None), '· 멈춘 까닭', stop or '끝까지')
if __name__ == '__main__': main()
