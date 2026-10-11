# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🍺 구마다 「밤 사고 가운데 음주 사고의 몫(위쪽 끝)」(소유자 2026-10-11 「밤에 나는 교통사고 중 절반, 적어도 30% 는 음주와 관련」을 통계로 어림) → data/dui-share-seoul.json
#   음주운전 사고(구 × 해 · data/gen-trend.json 의 TAAS 표) ÷ 밤 20~6시 사고(data/dui-ref-seoul.json 의 동 값을 구로 더함) · 2016~2025 열 해
#   음주 사고의 시간대를 구마다 모르므로 「음주 사고가 전부 밤에 났다」고 친 위쪽 끝이다 — 전국으로는 61~70% 가 밤이라 실제는 이 값의 0.6~0.7배쯤
#   py -3.12 -X utf8 tools/region/duishare-bake.py   (gen-trend 나 dui-ref-seoul 을 다시 구우면 같이 다시)
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def main():
    F = json.load(open(os.path.join(ROOT, 'data', 'gen-trend.json'), encoding='utf-8'))['files']['4_음주사고_서울구별']['series']; dui = {}
    for k, v in F.items():
        a = k.split('|')
        if a[0] == '음주운전 교통사고 건수': dui[a[3]] = {y: x for y, x in v}
    R = json.load(open(os.path.join(ROOT, 'data', 'dui-ref-seoul.json'), encoding='utf-8'))['items']; G = collections.defaultdict(lambda: [0, 0, 0, True])
    for r in R:
        g = G[r[2]]
        if r[12] is None: g[3] = False; continue
        g[0] += r[12]; g[1] += r[13]; g[2] += r[14]
    names = {os.path.basename(os.path.dirname(p)): json.load(open(p, encoding='utf-8')).get('name') for p in glob.glob(os.path.join(ROOT, 'data', 'r', '11*', 'dong.json'))}; items = []; T = [0, 0, 0, 0]
    for gu in sorted(names):
        nm = names[gu]; d = dui.get('서울 ' + nm) or {}; dd = sum(d.get(y, 0) for y in range(2016, 2026)); g = G[gu]; ys = [d.get(y) for y in range(2016, 2026)]
        if not g[3] or not g[0]: items.append([gu, nm, None, None, None, dd, None, None, ys]); continue
        items.append([gu, nm, g[0], g[1], g[2], dd, round(dd / g[1] * 100, 1), round(dd / g[0] * 100, 1), ys]); T[0] += g[0]; T[1] += g[1]; T[2] += g[2]; T[3] += dd
    doc = {'schema': 'tg-dui-share/1', 'made': datetime.date.today().isoformat(), 'area': '서울 25구 · 2016~2025 열 해',
           'source': '음주운전 교통사고 = 도로교통공단 TAAS 「시도 시군구별 (음주운전) 교통사고」(data/gen-trend.json — 코워크가 조회 화면에서 옮김) · 모든 사고·밤 사고 = TAAS 사고 10년 100m 칸을 행정동 경계로 센 것(data/dui-ref-seoul.json)',
           'note': ['**「밤 사고 가운데 음주 사고의 몫」을 재려는 표다 — 그런데 음주 사고의 시간대를 구마다 모른다.** 그래서 「음주 사고(모든 시간) ÷ 밤 20~6시 사고」를 실었다 = 음주 사고가 전부 밤에 났다고 쳤을 때의 **위쪽 끝**이다. 전국으로는 음주 사고의 61~70% 가 밤 20~6시에 난다(같은 TAAS · data/gen-trend.json) → 실제 몫은 이 값의 0.6~0.7배쯤',
                    '소유자 현장 지식(2026-10-11): 「밤에 나는 교통사고 가운데 절반, 적어도 30% 는 음주와 관련」 — 통계는 음주로 적발·기록된 사고만 센다(측정 전 달아남 · 숙취 · 피해자 쪽 음주는 빠진다). 현장 감각이 통계보다 높은 까닭으로 보인다',
                    '두 자료의 사고 범위가 꼭 같지는 않다(지도 사고 자료는 좌표가 있는 인적 피해 사고 · 음주 사고 표는 경찰 DB 집계) — 비율은 어림이다 · 중구·서대문구는 지도 사고 자료가 비어 null',
                    '구는 사고가 난 곳이다(마신 곳·사는 곳이 아니다)'],
           'fields': 'items[[구 코드, 이름, 모든 사고 10년, 밤 20~6시 사고, 새벽 0~6시 사고, 음주운전 사고 10년, 음주 사고 ÷ 밤 사고 %(위쪽 끝), 음주 사고 ÷ 모든 사고 %, [2016…2025 해마다 음주 사고]]] · seoul = 서울 합[모든 사고, 밤, 새벽, 음주, 음주 ÷ 밤 %, 음주 ÷ 모든 사고 %](null 인 구 제외)',
           'seoul': [T[0], T[1], T[2], T[3], round(T[3] / T[1] * 100, 1), round(T[3] / T[0] * 100, 1)], 'items': items}
    p = os.path.join(ROOT, 'data', 'dui-share-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); print('서울', doc['seoul'], '· 바이트', os.path.getsize(p))
if __name__ == '__main__': main()
