# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🧩 완료된 사건을 뒤돌아 맞대 보기의 재료: 한 시군구의 아파트 매매 실거래를 **여러 해** 받아 둔다(소유자 2026-10-11 「완료 = 사후 검증 · 다음 예측의 학습 자료」)
#   지도의 실거래 층(data/r/<구>/deals.json)은 최근 두 해(202409~)뿐이라 2019년 같은 지난 사건의 앞뒤를 못 잰다 → 사건이 있던 구만 따로 길게 받는다
#   국토교통부 아파트 매매 실거래가(공공데이터포털 RTMSDataSvcAptTrade · 키 keys.json data_go_kr — 찍지 않는다) → ../07_API키/out/home_hist/<구>_<연월>.json(달마다 · 받은 달은 건너뜀)
#   py -3.12 -X utf8 tools/story/eventcheck-fetch.py 11650 201601 202408
import json, os, sys, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'home_hist')
def main(gu, a, b):
    K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['data_go_kr']; os.makedirs(OUT, exist_ok=True); y, m = int(a[:4]), int(a[4:]); n = got = 0
    while '%04d%02d' % (y, m) <= b:
        ym = '%04d%02d' % (y, m); fn = os.path.join(OUT, '%s_%s.json' % (gu, ym))
        if not os.path.exists(fn):
            rows = []; page = 1
            while True:
                u = 'https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade?serviceKey=%s&%s' % (K, urllib.parse.urlencode({'LAWD_CD': gu, 'DEAL_YMD': ym, 'numOfRows': 1000, 'pageNo': page}))
                t = None
                for k in range(4):
                    try: t = urllib.request.urlopen(urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace'); break
                    except Exception as e: err = type(e).__name__ + ' ' + str(getattr(e, 'code', '')); time.sleep(4)
                if t is None: print(ym, '못 받음', err); return 1
                r = ET.fromstring(t); code = (r.findtext('.//resultCode') or '').strip()
                if code not in ('000', '00'): print(ym, '응답 코드', code, (r.findtext('.//resultMsg') or '')[:80]); return 1
                it = r.findall('.//item')
                for x in it:
                    g = lambda k: (x.findtext(k) or '').strip()
                    try: rows.append([g('umdNm'), g('aptNm'), float(g('excluUseAr')), int(g('dealAmount').replace(',', '')), int(g('dealDay') or 0), int(g('buildYear') or 0), 1 if g('cdealType') == 'O' else 0, g('jibun')])
                    except Exception: pass
                tot = int(r.findtext('.//totalCount') or 0)
                if page * 1000 >= tot: break
                page += 1
            json.dump(rows, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':')); got += 1; time.sleep(0.25)
        n += 1; m += 1
        if m > 12: y += 1; m = 1
    print(gu, a, '~', b, '· 달', n, '· 새로 받음', got); return 0
if __name__ == '__main__': sys.exit(main(*sys.argv[1:4]))
