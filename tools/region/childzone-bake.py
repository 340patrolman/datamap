# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚸 어린이보호구역(전국) → data/child-zone/<시도 코드>.json  (학교 코드와 이음 — 서울·경기·인천)
#   소유자 2026-10-12 「학교 담당 경찰관이 공공데이터를 충분히 이용할 수 있게」 → 학교 카드에서 그 학교의 보호구역(관할 경찰서 · CCTV 대수 · 도로 폭)을 본다
#   원자료: 전국어린이보호구역표준데이터(행정안전부 공공데이터 표준 · 공공데이터포털 15012891 · 제공 = 각 지자체 · 오픈API api.data.go.kr/openapi/tn_pubr_public_child_prtc_zn_api · 열쇠 data_go_kr)
#     받은 것 = 07_API키/out/childzone/all_<날짜>.json(다시 받으려면 fetch)
#   시도 파일: 지도의 시도 코드대로(광주·전남 = 12 한 파일) + 옛 꼴 29·46 도 같이 낸다
#   학교 잇기: 학교알리미 학교기본정보의 학교 자리(07_API키/out/schoolinfo/api/<해>_0_<학교급>_<구>.json)와 300m 안에서 이름이 맞는 초·중·고 → 정보공시 학교코드. 이름이 안 맞으면 잇지 않는다(null)
#   ⚠ 이 자료의 자리는 **대상 시설의 점**이다 — 구역의 경계선(도로 구간)·제한속도·단속 카메라는 없다. CCTV 대수는 지자체가 적은 값(빈칸 = 모름)
#   py -3.12 -X utf8 tools/region/childzone-bake.py [fetch]
import json, os, re, sys, glob, time, math, datetime, collections, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.join(os.path.dirname(ROOT), '07_API키'); SRC = os.path.join(KB, 'out', 'childzone'); API = os.path.join(KB, 'out', 'schoolinfo', 'api')
SD = {'서울': '11', '부산': '26', '대구': '27', '인천': '28', '광주': '29', '대전': '30', '울산': '31', '세종': '36', '경기': '41', '강원': '51', '충청북': '43', '충북': '43', '충청남': '44', '충남': '44', '전라북': '52', '전북': '52', '전라남': '46', '전남': '46', '경상북': '47', '경북': '47', '경상남': '48', '경남': '48', '제주': '50'}
def fetch():
    k = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; os.makedirs(SRC, exist_ok=True); rows = []; pg = 1
    while True:
        u = 'http://api.data.go.kr/openapi/tn_pubr_public_child_prtc_zn_api?serviceKey=%s&pageNo=%d&numOfRows=1000&type=json' % (k, pg)
        for t in range(4):
            try: d = json.loads(urllib.request.urlopen(u, timeout=90).read().decode('utf-8', 'replace')); break
            except Exception: time.sleep(4); d = None
        it = (((d or {}).get('response') or d or {}).get('body') or {}).get('items') or []
        it = it.get('item', it) if isinstance(it, dict) else it
        rows += it; print(pg, len(rows)); sys.stdout.flush()
        if len(it) < 1000: break
        pg += 1
    json.dump(rows, open(os.path.join(SRC, 'all_%s.json' % datetime.date.today().isoformat()), 'w', encoding='utf-8'), ensure_ascii=False)
def norm(s): return re.sub(r'(서울|초등학교|중학교|고등학교|초교|학교|부설|병설유치원|\s|\(.*?\))', '', s or '')
def dist(a, b, c, d): return math.hypot((a - c) * 88800, (b - d) * 111000)
def main():
    f = sorted(glob.glob(os.path.join(SRC, 'all_*.json')))[-1]; rows = json.load(open(f, encoding='utf-8')); S = []
    yr = max(int(os.path.basename(x)[:4]) for x in glob.glob(os.path.join(API, '*_0_*.json')))
    for x in glob.glob(os.path.join(API, '%d_0_*.json' % yr)):
        for r in json.load(open(x, encoding='utf-8'))['list']:
            if r.get('LGTUD'): S.append([float(r['LGTUD']), float(r['LTTUD']), r['SCHUL_NM'], r['SCHUL_CODE'], r['SCHUL_KND_SC_CODE']])
    G = collections.defaultdict(list)
    for s in S: G[(round(s[0] * 100), round(s[1] * 100))].append(s)
    OUT = collections.defaultdict(list); bad = 0; link = collections.Counter(); KN = {'초등학교': '02', '중학교': '03', '고등학교': '04'}
    for r in rows:
        try: lo = float(r['longitude']); la = float(r['latitude'])
        except Exception: bad += 1; continue
        if not (33 < la < 39 and 124 < lo < 132): bad += 1; continue
        a = (r.get('rdnmadr') or r.get('lnmadr') or r.get('insttNm') or '').strip(); sd = next((v for k, v in SD.items() if a.startswith(k)), None)
        if not sd: sd = next((v for k, v in SD.items() if (r.get('insttNm') or '').replace('전남광주통합특별시', '전남').startswith(k)), '00')
        code = None; kind = (r.get('fcltyKnd') or '').strip(); nm = (r.get('trgetFcltyNm') or '').strip()
        if kind in KN:
            best = None
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for s in G.get((round(lo * 100) + dx, round(la * 100) + dy), []):
                        if s[4] != KN[kind]: continue
                        d = dist(lo, la, s[0], s[1]); a1 = norm(nm); b1 = norm(s[2])
                        if d <= 300 and a1 and (a1 == b1 or a1 in b1 or b1 in a1) and (best is None or d < best[0]): best = (d, s[3])
            if best: code = best[1]; link[sd] += 1
        cc = r.get('cctvNumber'); cn = int(cc) if str(cc or '').strip().isdigit() else (0 if (r.get('cctvYn') or '').strip() == 'N' else None)
        rw = r.get('prtcareaRw');
        try: rw = float(rw) if str(rw or '').strip() else None
        except Exception: rw = None
        OUT[sd].append([round(lo, 5), round(la, 5), kind, nm, (r.get('cmptncPolcsttnNm') or '').strip(), cn, rw, (r.get('referenceDate') or '').strip(), code])
    os.makedirs(os.path.join(ROOT, 'data', 'child-zone'), exist_ok=True); td = datetime.date.today().isoformat()
    OUT['12'] = OUT.get('29', []) + OUT.get('46', []); link['12'] = link.get('29', 0) + link.get('46', 0)   # 지도의 시도 코드(전남광주통합특별시 12) — 옛 꼴 29·46 파일도 그대로 둔다
    for sd, items in sorted(OUT.items()):
        if sd == '00': continue
        items.sort(key=lambda x: (x[4], x[3])); kc = collections.Counter(i[2] for i in items)
        doc = {'schema': 'tg-child-zone/1', 'made': td, 'sido': sd, 'source': '전국어린이보호구역표준데이터(행정안전부 공공데이터 표준 · 제공 각 지자체 · 공공데이터포털 15012891 오픈API · %s 받음)' % os.path.basename(f)[4:14],
               'note': ['자리는 **대상 시설(학교·유치원·어린이집 등)의 점**이다 — 구역의 경계선(도로 구간)은 이 자료에 없다. 제한속도·단속 카메라도 없다(카메라는 카메라 층)',
                        'CCTV 대수는 지자체가 적은 값이다 — null = 적지 않음(없다는 뜻이 아니다) · 도로 폭은 m(null = 모름) · 기준일은 지자체마다 다르다(오래된 곳이 있다)',
                        '학교 코드는 학교알리미 학교 자리와 300m 안에서 이름이 맞는 초·중·고에만 붙였다(전국 · 2026-10-12) — 안 붙은 곳은 이름이 달리 적혔거나 유치원·어린이집·학원이다',
                        '지정이 풀렸거나 새로 지정된 곳이 반영되지 않았을 수 있다 — 정본은 지자체·경찰서의 지정 대장'],
               'fields': {'kinds': '{시설 종류: 곳 수}', 'items': '[[경도, 위도, 시설 종류, 대상 시설 이름, 관할 경찰서, CCTV 대수|null, 보호구역 도로 폭 m|null, 기준일, 정보공시 학교코드|null]] — 관할 경찰서·이름 차례'},
               'kinds': dict(kc.most_common()), 'items': items}
        p = os.path.join(ROOT, 'data', 'child-zone', sd + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
        print(sd, len(items), os.path.getsize(p), '학교 이음', link.get(sd, 0), dict(kc.most_common(4)))
    print('좌표 없음', bad, '시도 모름', len(OUT.get('00', [])), '학교', len(S)); sc = [i for i in OUT['11'] if i[4].startswith('서초') or i[4].startswith('방배')]; print('서초·방배', len(sc), collections.Counter(i[4] for i in sc), sc[:3])
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'fetch': fetch()
    main()
