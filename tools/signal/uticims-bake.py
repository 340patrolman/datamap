# -*- coding: utf-8 -*-
# 경찰청 도시교통정보센터(UTIC) 돌발 정보 — 서울 사고·공사·통제(imsOpenData.do · 열쇠 keys.json utic · 이 PC 등록 IP 에서만)
#   (2026-10-15 · 코워크 시험 「서울 76건 · 서울시 AccInfo 보다 사고가 촘촘」) → data/live-ims-seoul.json (tg-live-ims/1)
#   신호 수집기(spat-bake.py livespd)가 10분에 한 번 부른다 · UTIC 준수사항: 1초 5회 넘게 부르지 않기 · 출처 「경찰청 도시교통정보센터(UTIC)」 표기 · 신청 목적 안
#   ⚠ 지금 열쇠(첫 신청 · 목적 「교육·연구용 개인 지도(비영리)」)로는 **데이터지도 표시까지** — 가르고(출동 도구)는 두 번째 신청 승인 뒤(RULE-NAV-5)
#   지난 돌발은 07_API키/out/utic/ims/<날짜>.jsonl.gz 에 쌓인다(저장소 밖)
#   py -3.12 -X utf8 tools/signal/uticims-bake.py
import os, re, json, gzip, datetime, urllib.request, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(os.path.dirname(ROOT), '07_API키')


def main():
    K = json.load(open(os.path.join(RAW, 'keys.json'), encoding='utf-8-sig'))['utic']
    b = urllib.request.urlopen(urllib.request.Request('https://www.utic.go.kr/guide/imsOpenData.do?key=' + K, headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read()
    rows = [{c.tag: (c.text or '').strip() for c in x} for x in ET.fromstring(b).iter('record')]
    now = datetime.datetime.now(); items = []
    for x in rows:
        if not (x.get('addressJibunCd') or '').startswith('11'):
            continue
        t = x.get('incidentTitle') or ''
        m = re.match(r'\[([^\]]+)\]', t)
        try:
            lon, lat = float(x.get('locationDataX') or 0), float(x.get('locationDataY') or 0)
        except ValueError:
            lon = lat = 0
        items.append([x.get('incidentId'), m.group(1) if m else (x.get('incidenteTypeCd') or ''), x.get('incidenteTypeCd'), x.get('incidenteSubTypeCd'),
                      round(lat, 6) if lat else None, round(lon, 6) if lon else None, x.get('addressJibunCd'), x.get('roadName'), x.get('lane'),
                      x.get('startDate'), x.get('endDate'), re.sub(r'\s+', ' ', t).strip(), x.get('linkId')])
    doc = {'schema': 'tg-live-ims/1', 'made': now.strftime('%Y-%m-%d %H:%M'),
           'source': '경찰청 도시교통정보센터(UTIC) 개방데이터 돌발 정보(imsOpenData.do) — 서울(법정동 11…)',
           'credit': '교통정보: 경찰청 도시교통정보센터(UTIC) 제공',
           'fields': 'items[[돌발 ID, 갈래 글(제목 [ ] 안 · 사고·공사·통제 등), 갈래 코드, 세부 코드, 위도, 경도, 법정동 10자리, 도로 이름, 차로, 시작, 끝(예상), 제목 글, 표준 링크 ID]]',
           'note': ['지도 표시용 — 가르고(출동) 쓰임은 UTIC 두 번째 신청 승인 뒤', '실제 상황과 몇 분 차이가 날 수 있다 · 끝 시각은 예상', '서울시 AccInfo(data/live-acc-seoul.json)와 겹치는 공사가 있다 — 사고는 이쪽이 촘촘'],
           'n': len(items), 'items': items}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'live-ims-seoul.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.join(RAW, 'out', 'utic', 'ims'), exist_ok=True)
    with gzip.open(os.path.join(RAW, 'out', 'utic', 'ims', now.strftime('%Y%m%d') + '.jsonl.gz'), 'at', encoding='utf-8') as f:
        f.write(json.dumps({'t': doc['made'], 'items': items}, ensure_ascii=False) + '\n')
    c = {}
    for i in items:
        c[i[1]] = c.get(i[1], 0) + 1
    print('UTIC 서울 돌발', len(items), c)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
