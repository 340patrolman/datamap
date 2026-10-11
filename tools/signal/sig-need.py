# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 신호값 우선순위표(소유자 2026-10-11 「우선순위표를 화요일까지 만들어서 부족한 부분 신호값 받아올 수 있으면 받아와야지」)
#   서초경찰서 관내 신호제어기 대장(교통과 · 07_API키/신호앱/서초경찰서_관내_신호제어기_20260910.csv — **내부 자료라 저장소에 올리지 않는다**) 178대마다
#     지금 가진 신호 자료(교통과 출력물 · 경찰청 요일·시각 계획 · 서울 T-Data 방향별 초와 채운 시간대 칸)를 맞대어 「교통과에서 받아 와야 할 차례」를 매긴다
#   갈래 A = 교통과 자료가 유일한 길(서울 실시간 장비도 경찰청 계획도 없음) · B = 기다리면 채워짐(T-Data 가 있음 — 요일 4갈래 × 24시 = 96칸 가운데 채운 칸) · C = 이미 계획이 있음(교통과·경찰청)
#   중요도 = 그 자리에서 만나는 큰길의 차로 수 합(표준노드링크 · 55m 안 · 등급 1~4) + 현시 수(3현시 이상은 방향이 복잡해 값이 더 쓸모 있다) — **앱이 매긴 어림**이다(출동 빈도·사고는 넣지 않았다)
#   결과는 저장소 밖에: ../신호값_우선순위_<날>.md(소유자가 들고 갈 표) · ../07_API키/신호앱/신호값_우선순위_<날>.csv
#   py -3.12 -X utf8 tools/signal/sig-need.py
import csv, json, os, math, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
SRC = os.path.join(KB, '07_API키', '신호앱', '서초경찰서_관내_신호제어기_20260910.csv')
def m(a, b): return math.hypot((a[0] - b[0]) * 88400.0, (a[1] - b[1]) * 111000.0)
def place(name, cache):
    """대장에 좌표가 없는 제어기 — 이름의 건물·시설을 브이월드 장소 검색으로 찾아 서초구 안의 첫 결과를 근사 자리로(교차로 자리가 아니라 그 이름의 시설 자리다)"""
    import re, urllib.request, urllib.parse
    q = re.sub(r'\(.*?\)', '', name).strip(); q = re.sub(r'(앞|입구|정문|후문|동측|서측|하단부)$', '', q).strip()
    if not q: return None
    if q not in cache:
        K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['vworld']
        u = 'https://api.vworld.kr/req/search?service=search&request=search&version=2.0&crs=EPSG:4326&size=10&page=1&type=place&format=json&errorformat=json&query=%s&key=%s&domain=https://340patrolman.github.io' % (urllib.parse.quote('서초구 ' + q), K)
        try:
            j = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://340patrolman.github.io/'}), timeout=30).read().decode('utf-8', 'replace'), strict=False)['response']
            it = [x for x in (j.get('result') or {}).get('items', []) if '서초구' in ((x.get('address') or {}).get('road') or '') + ((x.get('address') or {}).get('parcel') or '')]
            cache[q] = [float(it[0]['point']['x']), float(it[0]['point']['y']), it[0]['title']] if it else None
        except Exception: return None
    return cache[q]
def main():
    R = list(csv.DictReader(open(SRC, encoding='utf-8-sig')))
    gp = os.path.join(KB, '07_API키', '신호앱', 'ctl_place_cache.json'); GC = json.load(open(gp, encoding='utf-8')) if os.path.exists(gp) else {}
    sd = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8')); its = sd['its']; pl = sd['pl']; pts = sd['pts']
    tod = {str(x['no']): x for x in json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']}
    ksc = {str(x['no']) for x in json.load(open(os.path.join(ROOT, 'data', 'sig-ksc-seocho.json'), encoding='utf-8'))['items']}
    nav = json.load(open(os.path.join(ROOT, 'data', 'nav-seocho.json'), encoding='utf-8')); N = nav['nodes']; ends = collections.defaultdict(list)
    for L in nav['links']:
        if L[5] <= 4: ends[L[2]].append(L)   # 그 노드로 들어오는 큰길 링크
    def roads(lon, lat, rad=55):
        lanes = 0; names = collections.Counter()
        for k, v in N.items():
            if abs(v[0] - lon) < 0.002 and abs(v[1] - lat) < 0.002 and m((lon, lat), (v[0], v[1])) <= rad:
                for L in ends.get(k, ()): lanes += L[6] or 1; names[L[7]] += L[6] or 1
        return lanes, [n for n, _ in names.most_common(3) if n]
    rows = []
    for r in R:
        no = (r['교차로번호'] or '').strip(); nm = r['제어기명'].strip(); ph = r['현시수'].strip()
        try: lon, lat = float(r['경도']), float(r['위도'])
        except Exception: lon = lat = None
        if lon is None and no in pts: lat, lon = pts[no][0], pts[no][1]
        approx = ''
        if lon is None:
            g = place(nm, GC)
            if g: lon, lat, approx = g[0], g[1], g[2]
        has_k = no in ksc; has_t = no in tod or r['주기자료'].strip() == '있음'; has_d = no in its and bool(its[no])
        cells = len(set((x[0], x[1]) for x in pl.get(no, []))) if no else 0
        kind = 'C' if (has_k or has_t) else ('B' if has_d else 'A')
        lanes, names = roads(lon, lat, 120 if approx else 55) if lon else (0, [])   # 이름으로 찾은 근사 자리는 120m 안의 큰길까지 본다
        ped = '(보)' in nm
        phn = int(ph[0]) if ph[:1].isdigit() else 0
        imp = (min(lanes, 40) + (6 if phn >= 4 else 3 if phn == 3 else 0)) * (0.5 if ped else 1.0)   # 이름에 (보)가 붙은 것은 보행 신호(건널목) — 절반으로
        need = {'A': 1.0, 'B': 0.35 * (1 - cells / 96.0), 'C': 0.0}[kind]
        have = ' · '.join(x for x in ('교통과 출력물' if has_k else '', '경찰청 계획' if has_t else '', ('실시간 방향별 초(%d/96칸)' % cells) if has_d else '') if x) or '없음'
        rows.append({'no': no, 'nm': nm, 'ph': ph, 'sys': r['시스템'].strip(), 'kind': kind, 'lanes': lanes, 'roads': names, 'imp': imp, 'score': round(imp * need, 1), 'have': have, 'xy': bool(lon), 'approx': approx, 'ped': ped, 'll': (lon, lat) if lon else None})
    json.dump(GC, open(gp, 'w', encoding='utf-8'), ensure_ascii=False)
    # 대장에 번호 없는 줄이 번호 있는 줄·이미 자료가 있는 신호와 **같은 교차로**인지 가린다(「서초역」 = 서초역사거리 4039 — 이미 교통과 출력물이 있다 · 소유자 2026-10-11 지적)
    import re
    def nz(x): return re.sub('[(].*?[)]|앞|입구|사거리|삼거리|교차로|역$|[ ]', '', x)
    KN = []   # 자료가 있거나 번호가 있는 신호: (이름, 경도, 위도, 번호, 갈래, 가진 것)
    for x in rows:
        if x['no'] and x.get('ll'): KN.append((x['nm'], x['ll'][0], x['ll'][1], x['no'], x['kind'], x['have']))
    for k, v in pts.items():
        if 37.40 < v[0] < 37.56 and 126.94 < v[1] < 127.13: KN.append((v[2], v[1], v[0], k, 'B', '실시간 방향별 초'))
    for it in json.load(open(os.path.join(ROOT, 'data', 'sig-ksc-seocho.json'), encoding='utf-8'))['items']: KN.append((it['nm'], it['lon'], it['lat'], str(it['no']), 'C', '교통과 출력물'))
    for x in rows:
        if x['no'] or not x.get('ll'): continue
        a0 = nz(x['nm']); best = None
        for nm2, lo, la, no2, kd, hv in KN:
            b0 = nz(nm2); d = m(x['ll'], (lo, la))
            if d <= 250 and a0 and b0 and (a0 == b0 or (min(len(a0), len(b0)) >= 3 and (a0 in b0 or b0 in a0))) and (best is None or d < best[0]): best = (d, nm2, no2, kd, hv)   # 이름이 같거나, 세 글자 넘게 겹칠 때만(「양재」·「반포」 두 글자 겹침으로 다른 곳을 묶지 않게)
        if best: x['same'] = '%s(%s)' % (best[1], best[2]); x['kind'] = 'S'; x['score'] = 0.0; x['have'] = '같은 교차로로 봄 → ' + best[4]
    rows.sort(key=lambda x: (-x['score'], -x['imp'], x['nm'])); day = datetime.date.today().strftime('%Y%m%d'); c = collections.Counter(x['kind'] for x in rows)
    A = [x for x in rows if x['kind'] == 'A']; Axy = [x for x in A if x['xy']]; Ano = [x for x in A if not x['xy']]
    md = ['# 신호값 우선순위표 — 서초경찰서 관내 신호제어기 %d대 (%s 기준)' % (len(rows), datetime.date.today().isoformat()), '',
          '신호 자료를 맞댄 때: 서울 실시간 수집 %s · 대장 = 교통과 2026-09-10.' % sd.get('made'), '',
          '| 갈래 | 뜻 | 대수 |', '|---|---|---|',
          '| A | **교통과 출력물이 유일한 길** — 서울 실시간 장비도 경찰청 공개 계획도 없음 | %d |' % c['A'],
          '| B | 기다리면 채워짐 — 서울 실시간 값이 들어옴(요일 4갈래 × 24시 = 96칸을 채우는 중) | %d |' % c['B'],
          '| C | 이미 요일·시각 계획이 있음(교통과 출력물 5 · 경찰청 공개 계획) | %d |' % c['C'],
          '| (겹침) | 대장에 번호 없이 한 번 더 적힌 줄 — 번호 있는 교차로와 같은 곳으로 봄 | %d |' % c['S'], '',
          '## 1. 교통과에서 받아 올 차례 (갈래 A %d대 가운데 자리를 알거나 찾은 %d대 · 위에서부터 45)' % (len(A), len(Axy)), '',
          '차례는 「그 자리에서 만나는 큰길의 차로 수 + 현시 수」로 매긴 **어림**입니다(출동 빈도·사고는 넣지 않았습니다 — 현장 판단으로 바꾸십시오).', '',
          '| 차례 | 번호 | 제어기 이름 | 현시 | 만나는 큰길 | 큰길 차로 합 | 시스템 |', '|---|---|---|---|---|---|---|']
    for i, x in enumerate(Axy[:45], 1): md.append('| %d | %s | %s | %s | %s | %d | %s |' % (i, x['no'] or '-', x['nm'] + (' ※' if x['approx'] else ''), x['ph'], ' · '.join(x['roads']) or '(큰길 아님)', x['lanes'], x['sys']))
    md.append(''); md.append('※ = 대장에 좌표가 없어 이름의 시설 자리를 찾아 넣은 **근사 자리**(120m 안의 큰길을 봄) — 실제 교차로와 다를 수 있습니다. 이름에 (보)가 붙은 보행 신호는 중요도를 절반으로 낮췄습니다.')
    md += ['', '## 겹친 줄(받을 차례에서 뺌) — 같은 교차로로 본 것이 맞는지 봐 주십시오', '', ', '.join('%s → %s' % (x['nm'], x['same']) for x in rows if x['kind'] == 'S') or '없음']
    md += ['', '## 2. 갈래 A 인데 자리를 못 찾아 중요도를 못 매긴 %d대' % len(Ano), '', '이름을 보고 큰 교차로를 골라 주십시오.', '', ', '.join('%s(%s%s)' % (x['nm'], x['ph'], ' · ' + x['no'] if x['no'] else '') for x in sorted(Ano, key=lambda x: x['nm'])), '',
           '## 3. 기다리면 채워지는 곳 (갈래 B %d대) — 지금 채운 칸이 적은 큰 교차로' % c['B'], '', '| 번호 | 제어기 이름 | 현시 | 만나는 큰길 | 채운 칸 |', '|---|---|---|---|---|']
    for x in sorted([x for x in rows if x['kind'] == 'B'], key=lambda x: -x['imp'])[:25]: md.append('| %s | %s | %s | %s | %s |' % (x['no'], x['nm'], x['ph'], ' · '.join(x['roads']), x['have'].split('(')[-1].rstrip(')')))
    md += ['', '## 4. 이미 계획이 있는 곳 (갈래 C %d대)' % c['C'], '', ', '.join('%s(%s)' % (x['nm'], x['have'].split(' · ')[0]) for x in rows if x['kind'] == 'C'), '',
           '## 읽을 때 주의', '', '- 갈래 B 의 「채운 칸」은 수집을 2026-10-10(토)에 시작해 아직 주말 몇 시간대뿐입니다. 평일 칸은 10-12(월)부터 찹니다.',
           '- 교통과 출력물 한 장이면 그 교차로의 요일·시간대 계획이 한 번에 찹니다(갈래 B 도 받으면 바로 찹니다).', '- 교통과 자료는 지금 5곳까지만 지도에 넣기로 정해져 있습니다 — 더 받은 것을 넣을지는 받은 뒤 다시 정합니다.',
           '- 대장에 번호·좌표가 없는 101대는 이름만으로 맞댔습니다 — 「서초역」「법원검찰청(교대역)」처럼 번호가 있는 다른 줄(서초역사거리 4039 등)과 같은 교차로일 수 있습니다. 받으러 가기 전에 이름을 한 번 훑어 주십시오.',
           '- 화요일(10-13) 아침에 다시 돌리면 월요일 수집분이 들어가 갈래 B 의 채운 칸이 바뀝니다: `py -3.12 -X utf8 tools/signal/sig-need.py`',
           '- 이 표와 대장은 내부 자료입니다(공개 저장소에 올리지 않았습니다).']
    p = os.path.join(KB, '신호값_우선순위_%s.md' % day); open(p, 'w', encoding='utf-8', newline='\n').write('\n'.join(md) + '\n')
    cp = os.path.join(KB, '07_API키', '신호앱', '신호값_우선순위_%s.csv' % day)
    with open(cp, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f); w.writerow(['차례', '갈래', '번호', '제어기명', '현시', '시스템', '만나는 큰길', '큰길 차로 합', '중요도', '점수', '지금 가진 것', '좌표 있음'])
        for i, x in enumerate(rows, 1): w.writerow([i, x['kind'], x['no'], x['nm'], x['ph'], x['sys'], ' · '.join(x['roads']), x['lanes'], x['imp'], x['score'], x['have'], 1 if x['xy'] else 0])
    print('갈래', dict(c), '· A 가운데 좌표 있음', len(Axy), '없음', len(Ano)); print(p); print(cp)
    for i, x in enumerate(Axy[:28], 1): print(' %2d %-6s %-18s %s %s %d %s' % (i, x['no'], x['nm'], x['ph'], ' · '.join(x['roads']), x['lanes'], '※' if x['approx'] else ''))
if __name__ == '__main__': main()
