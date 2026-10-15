# -*- coding: utf-8 -*-
# 데이터 압축지도 — 서울경찰청 「오늘의 주요집회」(www.smpa.go.kr/user/nd54882.do) 날마다 → data/rally-seoul.json
#   소유자 2026-10-13 「집회시위 신고자료는?」 — events-seocho.json 의 rallies 는 손으로 넣은 서초 15건(09-28 에서 멈춤)이라 지도에 오늘 집회가 안 나왔다
#   게시판은 날마다 한 글(전날 올라옴) · 본문이 글: 「일시 : 13:30~16:00 / 장소 : … -> … <성산동 등> / 신고 인원 : 100명 / 관할 : 마포」 · 장소의 「->」 = 행진
#   싣는 것 = 게시판에 공개된 주요 집회의 일시·장소 글·신고 인원·관할서뿐. 주최자는 원문에도 없다. 집회신고서 원문·관서 내부 접수 대장은 싣지 않는다
#   자리 = ① 「○○역 N出」 → OSM 출입구(exits-kr.json) ② 브이월드 장소 검색(관할 구 안에서 찾은 것만 · 캐시 out/rally/geo.json) ③ <동> 가운데(근사 1) ④ 못 찾으면 좌표 없이 글만 — 지어 넣지 않는다
#   받은 글은 07_API키/out/rally/post/<글 번호>.html 에 두고 새 글만 받는다 · 요청 사이 0.7초
#   py -3.12 -X utf8 tools/region/rally-bake.py [거슬러 볼 날 수 · 기본 90]
import json, os, re, sys, time, html, datetime, urllib.request, urllib.parse
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'rally'); POST = os.path.join(OUT, 'post'); GEO = os.path.join(OUT, 'geo.json')
BASE = 'https://www.smpa.go.kr/user/nd54882.do'; UA = {'User-Agent': 'Mozilla/5.0'}
# 관할서 → 자치구(서울 31개 경찰서 · 「경찰청과 그 소속기관 직제 시행규칙」 별표2 의 서 이름)
ST_GU = {'중부': '중구', '남대문': '중구', '종로': '종로구', '혜화': '종로구', '서대문': '서대문구', '용산': '용산구', '성북': '성북구', '종암': '성북구', '동대문': '동대문구', '마포': '마포구', '영등포': '영등포구', '성동': '성동구', '동작': '동작구', '광진': '광진구', '서부': '은평구', '은평': '은평구', '강북': '강북구', '금천': '금천구', '중랑': '중랑구', '강남': '강남구', '수서': '강남구', '관악': '관악구', '강서': '강서구', '강동': '강동구', '구로': '구로구', '서초': '서초구', '방배': '서초구', '양천': '양천구', '송파': '송파구', '노원': '노원구', '도봉': '도봉구'}
def get(url):
    for t in range(3):
        try: b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read(); time.sleep(0.7); return b.decode('utf-8', 'replace')
        except Exception: time.sleep(5 + t * 10)
    return ''
def text_of(s):
    t = html.unescape(re.sub(r'<[^>]+>', '\n', re.sub(r'(?is)<(script|style).*?</\1>', '', s))); return re.sub(r'[ \t\r\xa0]+', ' ', t)
def fetch(days):
    os.makedirs(POST, exist_ok=True); idx_p = os.path.join(OUT, 'index.json'); idx = json.load(open(idx_p, encoding='utf-8')) if os.path.exists(idx_p) else {}
    stop = (datetime.date.today() - datetime.timedelta(days=days)).isoformat(); page = 1; new = 0
    while page <= 40:
        s = get(BASE + '?page=%d' % page); rows = re.findall(r"goBoardView\('[^']*','View','(\d+)'\)[^>]*>\s*(?:<[^>]+>\s*)*([^<]*오늘의 집회[^<]*)", s)
        if not rows: break
        old = 0
        for no, title in rows:
            m = re.search(r'(\d{6})', title)
            if not m: continue
            d = '20%s-%s-%s' % (m.group(1)[:2], m.group(1)[2:4], m.group(1)[4:6])
            if d < stop: old += 1; continue
            if no not in idx or not os.path.exists(os.path.join(POST, no + '.html')):
                b = get(BASE + '?View&boardNo=' + no)
                if '일시' not in b and '장소' not in b and len(b) < 5000: continue
                open(os.path.join(POST, no + '.html'), 'w', encoding='utf-8').write(b); new += 1
            idx[no] = d
        if old == len(rows): break
        page += 1
    json.dump(idx, open(idx_p, 'w', encoding='utf-8'), ensure_ascii=False); print('게시 글', len(idx), '· 새로 받음', new); return idx
def parse(no, d):
    t = text_of(open(os.path.join(POST, no + '.html'), encoding='utf-8').read()); a = t.find('일시'); z = t.find('이전글', a) if a >= 0 else -1
    if a < 0: return []
    body = t[a:z if z > a else a + 6000]; out = []
    for blk in re.split(r'(?=일시\s*:)', body):
        m = re.search(r'일시\s*:\s*([0-9]{1,2})\s*:\s*([0-9]{2})\s*[~∼\-]\s*([0-9]{1,2})\s*:\s*([0-9]{2})', blk); p = re.search(r'장소\s*:\s*([^\n]+(?:\n(?!\s*(?:신고|관할|일시|집회|\d+\.))[^\n]+)*)', blk)
        if not p: continue
        place = re.sub(r'\s+', ' ', p.group(1)).strip(); n = re.search(r'신고\s*인원\s*:\s*([0-9,]+)', blk); st = re.search(r'관할서?\s*:\s*([가-힣·,/ ]+)', blk)
        it = {'d': d, 'from': '%02d:%s' % (int(m.group(1)), m.group(2)) if m else None, 'to': '%02d:%s' % (int(m.group(3)), m.group(4)) if m else None, 'p': place, 'n': int(n.group(1).replace(',', '')) if n else None, 'st': re.sub(r'\s+', ' ', st.group(1)).strip() if st else None, 'march': 1 if '->' in place or '→' in place else 0}
        out.append(it)
    return out
# ── 자리 찾기
def load_ref():
    ex = json.load(open(os.path.join(ROOT, 'data', 'exits-kr.json'), encoding='utf-8'))['pts']; E = {}; S = {}
    for la, lo, no, nm in ex:
        if not nm or not (37.40 < la < 37.72 and 126.75 < lo < 127.20): continue
        k = re.sub(r'역$', '', nm.split('(')[0].strip()); S.setdefault(k, []).append((la, lo))
        if no: E[(k, re.sub(r'\D', '', str(no)))] = (la, lo)
    S = {k: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)) for k, v in S.items()}
    D = {}; CC = {}; GN = {}
    for f in json.load(open(os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson'), encoding='utf-8'))['features']:
        pr = f['properties']
        if not str(pr.get('adm_cd2', '')).startswith('11'): continue
        g = f['geometry']; rings = g['coordinates'] if g['type'] == 'Polygon' else [r for poly in g['coordinates'] for r in poly]; pts = [p for r in rings[:1] for p in r]
        nm = pr['adm_nm'].split(); CC[str(pr['adm_cd2'])[:8]] = (sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)); GN[str(pr['adm_cd2'])[:5]] = nm[1]; D.setdefault((nm[1], re.sub(r'(제?\d+|본)?동$|\d*가$', '', nm[2])), []).append((sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)))
    D = {k: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)) for k, v in D.items()}
    # 장소 글의 <동> 은 법정동일 때가 많다(수송동·효자동·관철동…) — 행정동 이름에 없으면 그 법정동이 가장 넓게 든 행정동 가운데로(data/b2a.json)
    for code, v in json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a'].items():
        if not code.startswith('11') or not v.get('a') or v['a'][0][0] not in CC or v['gu'] not in GN: continue
        k = (GN[v['gu']], re.sub(r'(제?\d+|본)?동$|\d*가$', '', v['n']))
        if k not in D: D[k] = CC[v['a'][0][0]]
    return E, S, D
KEY = None; CACHE = {}; VW_OFF = [False]
def vworld(q, gus):
    global KEY
    k = q + '|' + ','.join(gus)
    if k in CACHE: return CACHE[k]
    if VW_OFF[0]: return None
    if KEY is None: KEY = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['vworld']
    u = 'https://api.vworld.kr/req/search?' + urllib.parse.urlencode(dict(service='search', request='search', version='2.0', crs='EPSG:4326', size=10, page=1, query=q, type='place', format='json', errorformat='json', key=KEY, domain='https://340patrolman.github.io'))
    try: r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8'))['response']
    except Exception: return None
    time.sleep(0.25)
    if 'LIMIT' in json.dumps(r): VW_OFF[0] = True; return None
    hit = None
    for it in (r.get('result') or {}).get('items') or []:
        ad = (it.get('address') or {}); a = (ad.get('road') or '') + ' ' + (ad.get('parcel') or '')
        if '서울' in a and (not gus or any(g in a for g in gus)): hit = [round(float(it['point']['y']), 6), round(float(it['point']['x']), 6), it.get('title', '')]; break
    if r.get('status') in ('OK', 'NOT_FOUND'): CACHE[k] = hit
    return hit
# 게시판이 줄여 쓰는 이름 → 찾을 때 쓰는 정식 이름(좌표를 적어 넣는 것이 아니라 검색어만 바꾼다)
ALIAS = [('사랑채', '청와대사랑채'), ('시의회', '서울특별시의회'), ('한국노총', '한국노동조합총연맹'), ('효자치안센터', '효자치안센터'), ('산업은행', '한국산업은행 본점'), ('국민의힘 당사', '국민의힘 중앙당사'), ('금감원', '금융감독원'), ('민주당사', '더불어민주당'), ('국힘당사', '국민의힘 중앙당사'), ('전쟁기념관', '전쟁기념관'), ('정부서울청사', '정부서울청사'), ('고용노동청', '서울지방고용노동청'), ('교보빌딩', '교보생명빌딩'), ('시청', '서울특별시청'), ('의사당', '국회의사당'), ('대통령실', '대통령실'), ('헌재', '헌법재판소'), ('중앙지검', '서울중앙지방검찰청'), ('중앙지법', '서울중앙지방법원'), ('대검', '대검찰청')]
def clean(seg):
    s = re.sub(r'<[^>]*>|〈[^〉]*〉', ' ', seg); s = re.sub(r'\([^)]*\)', ' ', s)
    s = re.sub(r'(동측|서측|남측|북측|동편|서편|남편|북편|맞은편|건너편|인근|일대|부근|주변|정문|후문|우측|좌측|이면도로|보조도로|상징탑|및|앞|옆|뒤|인도|차도|전\s*차로|\d+개?\s*차로|편도|양방향|~.*$|등$)', ' ', s); return re.sub(r'\s+', ' ', s).strip(' ,·')
def locate(seg, gus, E, S, D):
    m = re.search(r'([가-힣A-Za-z0-9·]+?)역\s*(\d+)\s*(?:出|번\s*출구|번출구|출구)', seg)
    if m:
        k = m.group(1)
        if (k, m.group(2)) in E: la, lo = E[(k, m.group(2))]; return round(la, 6), round(lo, 6), 0, '%s역 %s번 출구(OSM 출입구)' % (k, m.group(2))
        if k in S: la, lo = S[k]; return round(la, 6), round(lo, 6), 1, '%s역 가운데(그 출구 번호가 OSM 에 없음)' % k
    q = clean(seg)
    for a, b in ALIAS:
        if a in q: q = b; break
    if len(q) >= 2:
        h = vworld(q, gus) or (vworld(q.split()[0], gus) if ' ' in q and len(q.split()[0]) >= 3 else None)
        if h: return h[0], h[1], 0 if h[2].replace('(주)', '').replace(' ', '').startswith(q.replace(' ', '')) or h[2].replace(' ', '') in q.replace(' ', '') else 1, '브이월드 장소 검색 「%s」 → %s' % (q, h[2])
    m = re.search(r'([가-힣A-Za-z0-9·]+?)역', seg)
    if m and m.group(1) in S: la, lo = S[m.group(1)]; return round(la, 6), round(lo, 6), 1, '%s역 가운데' % m.group(1)
    m = re.search(r'[<〈]\s*([가-힣0-9]+?)(?:제?\d+)?(?:동|\d*가)\b', seg) or re.search(r'[<〈]\s*([가-힣0-9]+?)(?:제?\d+)?(?:동|\d*가)', seg)
    if m:
        for g in gus or sorted(set(k[0] for k in D)):
            if (g, m.group(1)) in D: la, lo = D[(g, m.group(1))]; return round(la, 6), round(lo, 6), 1, '%s %s동 쪽(장소를 못 찾아 동으로 근사 — 그 동이 든 행정동의 가운데)' % (g, m.group(1))
    return None
def main(days):
    idx = fetch(days); E, S, D = load_ref()
    if os.path.exists(GEO): CACHE.update(json.load(open(GEO, encoding='utf-8')))
    items = []; stop = (datetime.date.today() - datetime.timedelta(days=days)).isoformat()
    for no, d in sorted(idx.items(), key=lambda x: x[1]):
        if d < stop or not os.path.exists(os.path.join(POST, no + '.html')): continue
        for it in parse(no, d):
            gus = sorted(set(ST_GU[s] for s in re.split(r'[·,/ ]+', it['st'] or '') if s in ST_GU)); tail = re.search(r'[<〈][^>〉]*[>〉]\s*$', it['p']); segs = [x.strip() for x in re.split(r'->|→', it['p'])]
            if tail and len(segs) > 1: segs[0] = segs[0] + ' ' + tail.group(0)
            a = locate(segs[0], gus, E, S, D)
            if a: it['lat'], it['lon'], it['approx'], it['note'] = a
            else: it['note'] = '자리를 못 찾음 — 글만'
            if it['march'] and len(segs) > 1:
                b = locate(segs[-1], gus, E, S, D)
                if b: it['dest'] = [b[0], b[1]]; it['note'] += ' · 행진 끝 = ' + b[3]
            items.append(it)
    json.dump(CACHE, open(GEO, 'w', encoding='utf-8'), ensure_ascii=False)
    ds = sorted(set(i['d'] for i in items)); got = sum(1 for i in items if 'lat' in i)
    doc = {'schema': 'tg-rally-seoul/1', 'made': datetime.date.today().isoformat(), 'collected': datetime.date.today().isoformat(),
           'source': '서울특별시경찰청 「오늘의 주요집회」(www.smpa.go.kr/user/nd54882.do · 집회/시위 게시판) 본문 글 · 자리 = OpenStreetMap 지하철 출입구(© OpenStreetMap contributors · ODbL) · 브이월드 장소 검색(국토교통부 공간정보 오픈플랫폼) · 행정동 경계(통계청 SGIS · 가공 vuski/admdongkor)',
           'fields': 'items[{d 날짜, from·to 시각(HH:MM · 원문에 없으면 null), p 장소 글 그대로, n 신고 인원(명 · 없으면 null), st 관할서(원문 그대로), march 행진 1/0(장소에 「->」), lat·lon 시작 자리(못 찾으면 없음), approx 0 찾은 자리 · 1 근사(역 가운데·동 가운데·이름이 딱 맞지 않는 검색 결과), dest 행진 끝 [lat, lon](찾았을 때만), note 자리를 어떻게 잡았나}] · range [첫 날, 끝 날] · days 글이 있는 날 수',
           'note': '날마다 한 글(전날 올라옴)을 받아 쌓는다 — tools/region/rally-bake.py · 지난 %d일 · 자리 찾음 %d / %d건' % (days, got, len(items)),
           'caution': '경찰청이 날마다 올리는 **주요 집회**만이다(모든 집회가 아니다) · 주최자 이름은 원문에도 없고 싣지 않는다 · 신고 인원은 신고한 값이지 실제 모인 수가 아니다 · 신고되고도 열리지 않거나 시각·장소가 바뀔 수 있다 · 받은 날(collected)까지만 있다 · 자리는 장소 글에서 찾은 것이라 approx 1 은 근사, 좌표 없는 것은 글로만 읽는다',
           'range': [ds[0], ds[-1]] if ds else None, 'days': len(ds), 'items': items}
    p = os.path.join(ROOT, 'data', 'rally-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('집회', len(items), '건 ·', doc['range'], '· 날', len(ds), '· 자리 찾음', got, '(정확', sum(1 for i in items if i.get('approx') == 0), '· 근사', sum(1 for i in items if i.get('approx') == 1), ') · 못 찾음', len(items) - got, '·', os.path.getsize(p) // 1024, 'KB', '· 브이월드 한도' if VW_OFF[0] else '')
if __name__ == '__main__':
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 90)
    # (2026-10-15 게임 세션 부탁) 가르고 「열차 안 신고」가 읽는 역 둘레 큰 행사(data/station-events.json)를 이어서 다시 굽는다 — 집회가 바뀌면 같이
    import subprocess
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'tools', 'region', 'stnevent-bake.py')], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    print('역 둘레 행사:', (r.stdout or r.stderr or '').strip()[-200:])
