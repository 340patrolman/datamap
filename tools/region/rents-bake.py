# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🔑 전월세 건별(국토교통부 실거래가 · 아파트·오피스텔·연립다세대 전월세 12개월) → data/r/<구>/rents.json
#   (소유자 2026-11-17 「부동산을 네이버 부동산급으로 · 권고대로 모두」 — home.json 은 단지마다 묶은 값뿐이라 단지 카드에서 건별을 못 봤다)
#   원자료 = home-bake.py fetch 가 받아 둔 07_API키/out/home/{AptRent,OffiRent,RHRent}_<구>_<연월>.json — 다시 받지 않는다
#   싣는 것: 단지(종류·이름·법정동·지번) · 계약 연월 · 전용면적 · 보증금 · 월세(0 = 전세)
#   버리는 것: 계약 일 · 층 · 계약 기간 · 갱신 여부·종전 금액(원자료에 받지 않음)
#   py -3.12 -X utf8 tools/region/rents-bake.py build 11 41 28   (구 코드 또는 시도)
import json, os, sys, time, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키'); OUT = os.path.join(KB, 'out', 'home')
sp = importlib.util.spec_from_file_location('hb', os.path.join(ROOT, 'tools', 'region', 'home-bake.py')); HB = importlib.util.module_from_spec(sp); sp.loader.exec_module(HB)
SV = [('AptRent', 0, 'aptNm'), ('OffiRent', 1, 'offiNm'), ('RHRent', 2, 'mhouseNm')]

def num(s):
    try: return float(str(s).replace(',', ''))
    except Exception: return None

def build(args):
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); gb = {}
    for g in IX['gus']:
        if not any(g['gu'] == a or (len(a) == 2 and g['gu'][:2] == a) for a in args): continue
        umds = []; cx = {}; c = []; d = []; ms = set()
        for svc, ty, nk in SV:
            for ym in HB.months(HB.SVC[svc]):
                fn = os.path.join(OUT, '%s_%s_%s.json' % (svc, g['gu'], ym))
                if not os.path.exists(fn): continue
                ms.add(ym)
                for r in json.load(open(fn, encoding='utf-8')):
                    ar = num(r.get('excluUseAr')); dep = num(r.get('deposit')); mo = num(r.get('monthlyRent')) or 0
                    if not ar or dep is None: continue
                    um = r.get('umdNm') or '-'
                    if um not in umds: umds.append(um)
                    k = (ty, r.get(nk) or '', um, r.get('jibun') or '')
                    if k not in cx: cx[k] = len(c); c.append([ty, k[1], umds.index(um), k[3]])
                    d.append([cx[k], int(r['dealYear']) * 100 + int(r['dealMonth']), round(ar * 100), int(dep), int(mo)])
        if not d: continue
        doc = {'schema': 'tg-rents/1', 'gu': g['gu'], 'source': '국토교통부 실거래가(공공데이터포털 · 아파트·오피스텔·연립다세대 전월세 %s~%s 계약)' % (min(ms), max(ms)),
               'fields': 'c = [0 아파트·1 오피스텔·2 연립다세대, 단지 이름, 법정동(umds 자리), 지번] · d = [c 자리, 계약 연월, 전용㎡×100, 보증금(만 원), 월세(만 원 · 0 = 전세)]',
               'note': '계약 일·층·계약 기간·갱신 여부는 원자료에서 받지 않았다 · 단지는 deals.json 의 c 와 「종류 + 법정동 + 지번」으로 맞댄다 · 마지막 달은 신고 기한이 안 지나 덜 찼을 수 있다 · 단독·다가구 전월세는 지번이 가려져 여기 없다(home.json sh 의 법정동 묶은 값)',
               'made': time.strftime('%Y-%m-%d'), 'umds': umds, 'c': c, 'd': d}
        pth = os.path.join(ROOT, 'data', 'r', g['gu'], 'rents.json')
        json.dump(doc, open(pth, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); gb[g['gu']] = os.path.getsize(pth)
        print(g['gu'], g['name'], '단지', len(c), '계약', len(d), '크기', gb[g['gu']], flush=True)
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))
    for g in IX['gus']:
        if g['gu'] in gb: g.setdefault('bytes', {})['rents'] = gb[g['gu']]
    IX['layers']['rents'] = '전월세 건별(국토부 실거래 · 아파트·오피스텔·연립다세대 · 12개월)'
    json.dump(IX, open(os.path.join(ROOT, 'data', 'r', 'index.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('구', len(gb), '합계', round(sum(gb.values()) / 1e6, 1), 'MB')

if __name__ == '__main__':
    build(sys.argv[2:])
