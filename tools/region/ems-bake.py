# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚑 서울 119 구급 출동(법정동 × 달) → data/ems119-seoul.json
#   소유자 2026-10-12 「119 출동 112 출동도 들어가면 좋은데 어느 정도까지 공개를 하는지」 → 구급(구급차 · 환자 이송)은 **법정동 × 달**까지 공개된다(시간대·건별은 없다) · 구조 출동은 rescue119.json(동 × 시)
#   원자료: 서울 열린데이터광장 OA-22849 「서울시 소방 구급 출동 현황」(소방재난본부 재난대응과 · 119구급 스마트시스템 · 공공누리 1유형 · xlsx 해마다 시트 2022·2023·2024)
#     받는 법: datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do?&useCache=false 에 POST infId=OA-22849&seq=1&infSeq=1 + Referer → 07_API키/out/ems/ems.xlsx
#   py -3.12 -X utf8 tools/region/ems-bake.py
import json, os, datetime, openpyxl
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'ems', 'ems.xlsx')
def main():
    GN = {g['name']: g['gu'] for g in json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus'] if g['gu'][:2] == '11'}
    B = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a']; BK = {(v['gu'], v['n']): [c, [[a[0], a[2]] for a in v['a'][:3]]] for c, v in B.items()}
    D = {}; GU = {}; years = []
    for ws in openpyxl.load_workbook(SRC, read_only=True).worksheets:
        y = int(ws.title[:4]); years.append(y); gu = None
        for r in ws.iter_rows(values_only=True):
            nm = (r[0] or '').strip() if isinstance(r[0], str) else ''
            if not nm or nm == '구분': continue
            v = [int(x) if isinstance(x, (int, float)) else 0 for x in r[1:13]]
            if nm in GN:
                if gu == nm or (nm in GU and y in GU[nm] and sum(v) < 50): continue
                gu = nm; GU.setdefault(nm, {})[y] = v; continue
            if gu: D.setdefault((gu, nm), {})[y] = v
    years.sort(); items = []; hit = 0
    for (gu, nm), d in sorted(D.items()):
        m = BK.get((GN[gu], nm)); hit += 1 if m else 0
        items.append([gu, nm, m[0] if m else None, m[1] if m else None] + [d.get(y) for y in years])
    doc = {'schema': 'tg-ems119/1', 'made': datetime.date.today().isoformat(), 'source': '서울 열린데이터광장 OA-22849 「서울시 소방 구급 출동 현황」(서울특별시 소방재난본부 · 119구급 스마트시스템 · 공공누리 1유형) — %d~%d' % (years[0], years[-1]),
           'note': ['**구급차 출동 건수**(환자 이송 포함)다 — 구조 출동은 rescue119.json · 시간대·요일·건별은 공개되지 않는다(달 단위까지)',
                    '자리는 **법정동**(출동한 곳)이다 — 행정동이 아니다. 끝 칸의 「걸친 행정동」으로 어림해 붙일 수 있다(넓이 비율 — 근사)',
                    '그 동에 사는 사람의 수요가 아니라 그 동에서 난 출동이다 — 역·유흥가·병원·요양시설이 있는 동이 크게 나온다',
                    '구 합계는 원자료의 구 줄 그대로(gu) · 법정동 이름이 b2a 와 안 맞는 %d곳은 코드가 null' % (len(items) - hit)],
           'fields': {'years': '해(차례)', 'gu': '{구: {해: [1~12월 출동 건수]}}', 'items': '[[구, 법정동, 법정동 8자리 코드|null, [[걸친 행정동 8자리, 넓이 %]…]|null, 해마다 [1~12월 건수]|null …(years 차례)]]'},
           'years': years, 'gu': {g: {str(y): v for y, v in d.items()} for g, d in GU.items()}, 'items': items}
    p = os.path.join(ROOT, 'data', 'ems119-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '법정동', len(items), '코드 붙음', hit, '구', len(GU)); L = years[-1]
    print('서울', {y: sum(sum(GU[g].get(y, [0])) for g in GU) for y in years})
    print('많은 동', sorted(((sum(d.get(L, [0])), g, n) for (g, n), d in D.items()), reverse=True)[:12])
    print('서초', sorted(((sum(d.get(L, [0])), n) for (g, n), d in D.items() if g == '서초구'), reverse=True))
if __name__ == '__main__': main()
