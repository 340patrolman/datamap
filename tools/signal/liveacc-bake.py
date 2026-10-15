# -*- coding: utf-8 -*-
# 서울 실시간 돌발(공사·통제·사고) 한 장 — 서울 열린데이터 AccInfo(키 keys.json seoul · http 만 · xml 만 받아짐 — json 은 ERROR-301)
#   (2026-10-15 소유자 「골목 소로의 상황 · 이삿짐 차량이나 공사중이라면 시간이 더 걸릴 수도 · 공사는 서초구에서 미리 알림」)
#   → data/live-acc-seoul.json (tg-live-acc/1) · 받을 때마다 07_API키/out/liveacc/<날짜>.jsonl.gz 에 한 줄(지난 공사 · 「평소」 바탕)
#   신호 수집기(spat-bake.py livespd)가 통행속도와 같이 10분에 한 번 부른다 · 가르고가 그 링크를 느리게/막힘으로 본다
#   ⚠ 큰길(ITS 링크)에 걸린 것만 온다 — 골목 공사·이사 차량은 이 자료에 없다
#   py -3.12 -X utf8 tools/signal/liveacc-bake.py
import os, json, gzip, datetime, urllib.request, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')
TYPE = {'A01': '사고', 'A02': '차량고장', 'A03': '집회·행사', 'A04': '공사', 'A05': '기상', 'A06': '재난', 'A07': '기타', 'A08': '통제', 'A09': '행사', 'A10': '기타', 'A11': '정체'}   # 갈래 이름은 받은 값에서 보이는 것만 확인됨(A04 공사) — 나머지는 서울 열린데이터 명세 기준 · 모르는 코드는 코드 그대로


def tm2ll(x, y):
    try:
        from pyproj import Transformer
        return Transformer.from_crs('EPSG:5181', 'EPSG:4326', always_xy=True).transform(x, y)
    except Exception:
        return None, None


def main():
    K = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig'))['seoul']
    b = urllib.request.urlopen('http://openapi.seoul.go.kr:8088/%s/xml/AccInfo/1/1000/' % K, timeout=60).read()
    root = ET.fromstring(b)
    code = (root.findtext('RESULT/CODE') or '')
    if code and code != 'INFO-000':
        print('받지 못함', code); return 1
    rows = [{c.tag: (c.text or '').strip() for c in r} for r in root.findall('row')]
    now = datetime.datetime.now()
    items = []
    for r in rows:
        try:
            x, y = float(r.get('grs80tm_x') or 0), float(r.get('grs80tm_y') or 0)
        except ValueError:
            x = y = 0
        lon, lat = tm2ll(x, y) if x and y else (None, None)
        items.append([r.get('acc_id'), r.get('acc_type'), TYPE.get(r.get('acc_type'), r.get('acc_type')), r.get('acc_dtype'), r.get('link_id'),
                      round(lat, 6) if lat else None, round(lon, 6) if lon else None,
                      (r.get('occr_date') or '') + (r.get('occr_time') or '')[:4], (r.get('exp_clr_date') or '') + (r.get('exp_clr_time') or '')[:4], r.get('acc_info')])
    doc = {'schema': 'tg-live-acc/1', 'made': now.strftime('%Y-%m-%d %H:%M'),
           'source': '서울 열린데이터광장 「서울시 실시간 돌발 정보」(AccInfo · TOPIS) — 큰길(ITS 링크)에 걸린 공사·통제·사고',
           'fields': 'items[[돌발 ID, 갈래 코드, 갈래 이름, 세부 코드, ITS 링크 ID, 위도, 경도, 시작 YYYYMMDDhhmm, 끝(예상) YYYYMMDDhhmm, 내용 글]]',
           'note': ['골목 공사·이삿짐 차량은 이 자료에 없다 — 큰길만', '끝 시각은 예상 · 받은 그대로', '좌표 = GRS80 중부원점(EPSG:5181) → WGS84'],
           'n': len(items), 'items': items}
    p = os.path.join(ROOT, 'data', 'live-acc-seoul.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.join(RAW, 'out', 'liveacc'), exist_ok=True)
    with gzip.open(os.path.join(RAW, 'out', 'liveacc', now.strftime('%Y%m%d') + '.jsonl.gz'), 'at', encoding='utf-8') as f:
        f.write(json.dumps({'t': doc['made'], 'items': items}, ensure_ascii=False) + '\n')
    print('돌발', len(items), '·', dict((t, sum(1 for i in items if i[2] == t)) for t in set(i[2] for i in items)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
