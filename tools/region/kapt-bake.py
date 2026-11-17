# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🏢 공동주택 단지 정보(국토교통부 K-apt · 공공데이터포털 15057332 단지 목록 · 15058453 기본 정보 · 활용 승인 2026-11-17) → data/r/<구>/kapt.json
#   (소유자 2026-11-17 「부동산을 눌러 보면 네이버 부동산급으로」 — 단지 카드에 세대수·동수·사용승인·주차·난방·복도·면적별 세대 · 지하철)
#   받기: AptListService4/getSigunguAptList4(sigunguCode = r/index.json 의 구 코드) → 단지마다 AptBasisInfoServiceV5/getAphusBassInfoV5 · getAphusDtlInfoV5(kaptCode)
#   싣는 것: 단지 이름·법정동·지번(실거래 단지와 맞대는 열쇠)·세대수·동수·사용승인 연월·최고층·난방·복도·분양형태·단지분류·시공사·전용면적별 세대(60 이하·85 이하·135 이하·초과)·주차(지상·지하)·승강기·전기차 충전기·지하철(호선·역·걸리는 시간 글)·버스 정류장까지 글
#   버리는 것: 관리사무소 전화·팩스·누리집 · 관리·경비·청소 업체 이름 · 우편번호
#   의무관리 대상 단지(대개 150세대 이상 등)만 K-apt 에 있다 — 없는 단지는 「없음」이지 0세대가 아니다
#   py -3.12 -X utf8 tools/region/kapt-bake.py fetch 11 41 28   (구 코드 또는 시도 · 하루 한도에 걸리면 멈춤 — 다시 돌리면 이어서)
#   py -3.12 -X utf8 tools/region/kapt-bake.py build 11 41 28
import json, os, sys, time, re, urllib.request, urllib.error
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'kapt')
B = 'https://apis.data.go.kr/1613000/'

def gus(args):
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    return IX, [g for g in IX['gus'] if any(g['gu'] == a or (len(a) == 2 and g['gu'][:2] == a) for a in args)]

def get(path, key, tries=3):
    for i in range(tries):
        try:
            t = urllib.request.urlopen(urllib.request.Request(B + path + ('&' if '?' in path else '?') + 'serviceKey=' + key, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
            j = json.loads(t)
            if 'response' not in j:   # 제공기관(K-apt) 쪽 오류 — { OpenAPI_ServiceResponse: { cmmMsgHeader: { errMsg, returnReasonCode } } } · 2026-11-17 약 120번 잇달아 부른 뒤 04 HTTP_ERROR 가 이어졌다
                hd = (j.get('OpenAPI_ServiceResponse') or {}).get('cmmMsgHeader') or {}
                if i == tries - 1: raise RuntimeError('제공기관 오류 %s %s' % (hd.get('returnReasonCode'), hd.get('errMsg')))
                time.sleep(20 * (i + 1)); continue
            h = j['response']['header']
            if h.get('resultCode') not in ('00', '000'): raise RuntimeError('code %s %s' % (h.get('resultCode'), h.get('resultMsg')))
            return j['response']['body']
        except urllib.error.HTTPError as e:
            if e.code == 429 or i == tries - 1: raise RuntimeError('HTTPError %s' % e.code)   # 주소(열쇠)는 오류 글에 싣지 않는다
            time.sleep(3 * (i + 1))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if i == tries - 1: raise RuntimeError(type(e).__name__)
            time.sleep(3 * (i + 1))

def fetch(args):
    os.makedirs(os.path.join(OUT, 'c'), exist_ok=True); key = json.load(open(os.path.join(KB, 'keys.json'), encoding='utf-8-sig'))['data_go_kr']
    IX, G = gus(args); n = 0
    for g in G:
        lf = os.path.join(OUT, 'list_%s.json' % g['gu'])
        if os.path.exists(lf): L = json.load(open(lf, encoding='utf-8'))
        else:
            L = []; page = 1
            while True:
                b = get('AptListService4/getSigunguAptList4?sigunguCode=%s&pageNo=%d&numOfRows=1000' % (g['gu'], page), key); it = b.get('items') or []; L += it
                if page * 1000 >= int(b.get('totalCount') or 0) or not it: break
                page += 1
            json.dump(L, open(lf, 'w', encoding='utf-8'), ensure_ascii=False); time.sleep(0.05)
        m = 0
        for x in L:
            cf = os.path.join(OUT, 'c', x['kaptCode'] + '.json')
            if os.path.exists(cf): continue
            a = get('AptBasisInfoServiceV5/getAphusBassInfoV5?kaptCode=' + x['kaptCode'], key).get('item') or {}
            d = get('AptBasisInfoServiceV5/getAphusDtlInfoV5?kaptCode=' + x['kaptCode'], key).get('item') or {}
            json.dump({'b': a, 'd': d}, open(cf, 'w', encoding='utf-8'), ensure_ascii=False); n += 1; m += 1; time.sleep(2.5)
        print(g['gu'], g['name'], '단지', len(L), '새로 받음', m, flush=True)
    print('새로 받은 단지', n, flush=True)

def iv(x):
    try: return int(float(x))
    except Exception: return None

def jibun(addr, name):
    # 「경기도 화성만세구 새솔동 163 단지이름」 → 163 · 「… 반포동 18-1 …」 → 18-1 · 산 번지는 「산12-3」
    for tok in (addr or '').split(' '):
        if re.match(r'^산?\d+(-\d+)?$', tok): return tok
    return None

def build(args):
    IX, G = gus(args); gb = {}
    for g in G:
        lf = os.path.join(OUT, 'list_%s.json' % g['gu'])
        if not os.path.exists(lf): continue
        L = json.load(open(lf, encoding='utf-8')); items = []; miss = 0
        for x in L:
            cf = os.path.join(OUT, 'c', x['kaptCode'] + '.json')
            if not os.path.exists(cf): miss += 1; continue
            c = json.load(open(cf, encoding='utf-8')); b = c['b']; d = c['d']
            um = ' '.join(t for t in (x.get('as3'), x.get('as4')) if t)
            ud = str(b.get('kaptUsedate') or '')
            sub = ' · '.join(t for t in ((d.get('subwayLine') or '').strip(), (d.get('subwayStation') or '').strip(), (d.get('kaptdWtimesub') or '').strip()) if t)
            items.append([b.get('kaptName') or x.get('kaptName'), um, jibun(b.get('kaptAddr'), b.get('kaptName')), iv(b.get('kaptdaCnt')), iv(b.get('kaptDongCnt')), iv(ud[:6]) if len(ud) >= 6 else None, iv(b.get('kaptTopFloor')),
                          (b.get('codeHeatNm') or '').strip() or None, (b.get('codeHallNm') or '').strip() or None, (b.get('codeSaleNm') or '').strip() or None, (b.get('codeAptNm') or '').strip() or None, (b.get('kaptBcompany') or '').strip() or None,
                          [iv(b.get('kaptMparea60')), iv(b.get('kaptMparea85')), iv(b.get('kaptMparea135')), iv(b.get('kaptMparea136'))], [iv(d.get('kaptdPcnt')), iv(d.get('kaptdPcntu'))], iv(d.get('kaptdEcnt')),
                          (iv(d.get('groundElChargerCnt')) or 0) + (iv(d.get('undergroundElChargerCnt')) or 0), sub or None, (d.get('kaptdWtimebus') or '').strip() or None])
        if not items: continue
        doc = {'schema': 'tg-kapt/1', 'gu': g['gu'], 'source': '국토교통부 공동주택 단지 목록·기본 정보(K-apt 공동주택관리정보시스템 · 공공데이터포털 15057332·15058453) · %s 받음' % time.strftime('%Y-%m-%d'),
               'fields': 'items = [단지 이름, 법정동(읍면 리), 지번(실거래 단지와 맞대는 열쇠 · 없으면 null), 세대수, 동수, 사용승인 연월(YYYYMM), 최고층, 난방, 복도, 분양형태, 단지분류, 시공사, [전용 60㎡ 이하·85 이하·135 이하·135 초과 세대], [주차 지상·지하 대수], 승강기 대수, 전기차 충전기 대수, 지하철(호선 · 역 · 걸리는 시간 글), 버스 정류장까지 걸리는 시간 글]',
               'note': 'K-apt 에 올라온 단지(의무관리 대상 — 대개 150세대 이상 등)만 있다 · 없는 단지는 「정보 없음」이지 0세대가 아니다 · 값은 단지 관리주체가 넣은 것이라 비어 있거나 낡은 칸이 있다(null = 안 적힘) · 관리사무소 전화·관리업체 이름은 싣지 않음' + (' · 이 구는 %d단지를 아직 덜 받음' % miss if miss else ''),
               'made': time.strftime('%Y-%m-%d'), 'items': items}
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'kapt.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); gb[g['gu']] = os.path.getsize(pth)
        print(g['gu'], g['name'], '단지', len(items), '덜 받음', miss, '지번 없음', sum(1 for i in items if not i[2]), '크기', gb[g['gu']], flush=True)
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['kapt'] = gb[g['gu']]
    IX['layers']['kapt'] = '공동주택 단지 정보(국토부 K-apt · 세대수·동수·사용승인·주차·난방)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))

if __name__ == '__main__':
    (fetch if sys.argv[1] == 'fetch' else build)(sys.argv[2:])
