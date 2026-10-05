# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.6.2 — 층 목록 한 표(전국 확장 S1 · 설계서 5장 메타데이터의 뼈대) → data/layers.json
#   map2d.js 의 LAYERS(키·이름·기본·갈래)를 읽고, 이 파일의 표로 파일·종류·지역 범위·출처 계열·이용허락·추정 여부를 붙인다
#   이용허락은 **확인한 것만** 적고 나머지는 「확인 필요」(설계서: 확인 필요 층은 유료 기능에서 자동 제외) — 지어내지 않는다
#   py -3.12 -X utf8 tools/region/layers-bake.py
import json, os, re, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 층 → (지역 파일 r/<구>/… 또는 서초 바탕 파일, 종류 point·grid·poly·line·live, 범위 national·seoul·gyeonggi·seoul+gg·seocho, 출처 계열, 추정)
T = {
 'dong': ('dong.json · dong-seocho.json', 'poly', 'seoul+gg', 'mois', 0), 'live': ('dong.json(live)', 'poly', 'seoul', 'seoul', 0), 'sales': ('dong.json(sales)', 'poly', 'seoul', 'seoul', 1),
 'live250': ('live250.json', 'grid', 'seoul', 'seoul250', 0), 'crowd': ('서울시 실시간 도시데이터(받은 때)', 'point', 'seoul', 'seoul', 0), 'profile': ('profile.json', 'table', 'national', 'mixed', 1), 'fl250': ('forn250.json', 'grid', 'seoul', 'seoul', 0), 'jurk': ('police.json(dong)', 'poly', 'national', 'police', 1), 'pbox': ('police.json(pbox)', 'point', 'national', 'police', 0), 'g250': ('grid.json', 'grid', 'seoul+gg', 'sgis', 0), 'acc250': ('taas250.json', 'grid', 'seoul+gg', 'taas', 0),
 'acc10': ('taas10.json', 'grid', 'seoul+gg', 'taas', 0), 'fatal10': ('taas10.json(fatal)', 'point', 'seoul+gg', 'taas', 0), 'fatal': ('taas10.json(fatal)', 'point', 'seoul+gg', 'taas', 0),
 'jct': ('jct.json', 'point', 'seoul+gg', 'taas', 1), 'hot10': ('hot10.json', 'point', 'seoul+gg', 'koroad', 0), 'acc': ('taas-nodes-seocho.json', 'point', 'seocho', 'taas', 1),
 'home': ('home.json', 'grid', 'seoul+gg', 'molit', 1), 'rtc': ('rtms.json', 'grid', 'seoul+gg', 'molit', 0), 'rent': ('rent.json', 'point', 'seoul+gg', 'reb', 0),
 'trd': ('trdar.json · ggtrd.json', 'poly', 'seoul+gg', 'seoul', 1), 'szone': ('szone.json', 'poly', 'seoul+gg', 'sbiz', 0), 'jgg': ('jgg.json', 'poly', 'seoul+gg', 'sgis', 0),
 'jcnm': ('jcnm.json', 'point', 'seoul+gg', 'its', 0), 'lspd': ('itsl.json + ITS API', 'live', 'national', 'its', 0), 'lcc': ('itscctv.json + ITS API', 'live', 'national', 'its', 0),
 'lev': ('ITS API', 'live', 'national', 'its', 0), 'lwx': ('Open-Meteo', 'live', 'national', 'openmeteo', 1), 'lair': ('Open-Meteo', 'live', 'national', 'openmeteo', 1), 'lrad': ('RainViewer', 'live', 'national', 'rainviewer', 0),
 'lak': ('에어코리아 API', 'live', 'national', 'datagokr', 0), 'lkma': ('기상청 API', 'live', 'national', 'datagokr', 0), 'lbus': ('경기 버스 API', 'live', 'gyeonggi', 'datagokr', 0), 'vw': ('브이월드 WMTS', 'live', 'national', 'vworld', 0),
 'bus': ('transit.json', 'point', 'seoul+gg', 'seoul', 0), 'subr': ('transit.json', 'point', 'seoul+gg', 'seoul', 0), 'season': ('season.json', 'point', 'seoul', 'seoul', 0),
 'govr': ('fac.json(gov)', 'point', 'seoul+gg', 'osm', 0), 'edu': ('fac.json(edu)', 'point', 'seoul+gg', 'mixed', 0), 'kyr': ('fac.json(kyr)', 'point', 'seoul+gg', 'mixed', 0), 'kg': ('fac.json(kg)', 'point', 'seoul+gg', 'mixed', 0), 'cc': ('fac.json(cc)', 'point', 'seoul+gg', 'mixed', 0), 'aca': ('fac.json(aca)', 'point', 'seoul+gg', 'mixed', 0),
 'road': ('base/t', 'line', 'seoul+gg', 'osm', 0), 'base': ('base/t', 'poly', 'seoul+gg', 'osm', 0), 'bld': ('maps/seocho-full-buildings.json', 'poly', 'seocho', 'osm', 0),
}
for k in ['cam', 'sz', 'srbell', 'srcctv', 'srlamp', 'sr112', 'srsvc', 'aed', 'fw', 'tow', 'wc2', 'box', 'dem']: T.setdefault(k, ('safety.json', 'point', 'seoul+gg', 'mixed', 0))
for k in ['gpark', 'gev', 'ger', 'gfest', 'glamp']: T.setdefault(k, ('safety.json · lamp.json', 'point', 'gyeonggi', 'ggdata', 0))
for k in ['flt', 'flr', 'und', 'ice', 'hcab', 'advb']: T.setdefault(k, ('season.json · season-seocho.json', 'point', 'seoul', 'seoul', 0))
SRC = {'mois': ('행정안전부 주민등록 인구통계', '확인 필요'), 'seoul': ('서울 열린데이터광장', '확인 필요(데이터셋마다 — 대부분 공공누리 1유형)'),
       'seoul250': ('서울 열린데이터광장 OA-22784', '공공누리 1유형(출처표시 · 상업적 이용·변경 가능 — 데이터셋 화면 2026-10-05 확인)'),
       'sgis': ('통계청 SGIS(경계 가공 vuski/admdongkor)', 'CC BY 4.0(admdongkor) · SGIS 통계는 확인 필요'), 'taas': ('도로교통공단 TAAS', '확인 필요'), 'koroad': ('도로교통공단 오픈API', '확인 필요'),
       'molit': ('국토교통부 실거래가(공공데이터포털)', '확인 필요'), 'reb': ('한국부동산원', '확인 필요'), 'sbiz': ('소상공인시장진흥공단', '확인 필요'), 'its': ('국가교통정보센터 ITS', '확인 필요'),
       'openmeteo': ('Open-Meteo', 'CC BY 4.0(Open-Meteo 자료 — 원문 확인 필요)'), 'rainviewer': ('RainViewer', '확인 필요'), 'datagokr': ('공공데이터포털 OpenAPI', '확인 필요'), 'vworld': ('국토교통부 브이월드', '확인 필요(이용약관)'),
       'osm': ('OpenStreetMap', 'ODbL(© OpenStreetMap contributors)'), 'mixed': ('공공데이터포털·서울시·경기도·교육청·OSM 섞임', '확인 필요'), 'ggdata': ('경기데이터드림', '확인 필요'), 'police': ('경찰청 직제 시행규칙 별표2(국가법령정보) × 행정동 · 경찰청 지구대 파출소 주소 현황(공공데이터포털)', '확인 필요')}
def main():
    s = open(os.path.join(ROOT, 'js', 'map2d.js'), encoding='utf-8').read(); i = s.index('var LAYERS = ['); j = s.index('];', i)
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); SN = {}
    import importlib.util
    sp = importlib.util.spec_from_file_location('rc', os.path.join(ROOT, 'tools', 'region', 'regcfg.py')); RC = importlib.util.module_from_spec(sp); sp.loader.exec_module(RC)
    for g in IX['gus']:
        for f in (g.get('bytes') or {}): SN.setdefault(f, set()).add(g['gu'][:2])
    def cover(t):   # v2.10.0 범위를 실제 구운 파일에서 센다(전국 확장 뒤 표의 scope 가 낡았다)
        if re.search(r'\((live|sales)\)', t[0]): return None   # 동 파일 안 서울만 있는 칸
        fs = [f for f in re.findall(r'([a-z0-9]+)\.json', t[0]) if f in SN]
        if not fs: return None
        sd = set().union(*[SN[f] for f in fs])
        if len(sd) >= len(RC.SIDOS): return '전국'
        return '·'.join(RC.SHORT.get(x, x) for x in RC.SIDOS if x in sd)
    L = re.findall(r"\['([a-z0-9]+)', '([^']*)', (true|false), '([^']*)', (\d)\]", s[i:j]); out = []; miss = []
    for k, nm, on, grp, pr in L:
        t = T.get(k)
        if not t: t = ('*-seocho.json / pubdata(OSM·서울시)', 'point', 'seocho', 'mixed', 0); miss.append(k)
        src, lic = SRC[t[3]]
        out.append({'key': k, 'name': nm, 'group': grp, 'default': on == 'true', 'file': t[0], 'kind': t[1], 'scope': t[2], 'cover': cover(t) or {'national': '전국', 'seoul': '서울', 'gyeonggi': '경기', 'seoul+gg': '서울·경기', 'seocho': '서초 둘레'}.get(t[2], t[2]), 'src': src, 'license': lic, 'estimate': bool(t[4]),
                    'paid_ok': not lic.startswith('확인 필요') and 'ODbL' not in lic})
    doc = {'schema': 'tg-layers/1', 'built': time.strftime('%Y-%m-%d'), 'note': '층 목록 한 표(설계서 5장) — scope: national 전국 공통 · seoul+gg · seoul · gyeonggi · seocho(서초 바탕만) · license 「확인 필요」 = 유료 기능 자동 제외(paid_ok false) · ODbL 은 공유 조건 때문에 false · estimate = 화면에 「추정」',
           'layers': out}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'layers.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=0)
    print('층', len(out), '서초 바탕만(표 밖)', len(miss), miss[:30])
if __name__ == '__main__': main()
