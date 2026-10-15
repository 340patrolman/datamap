# -*- coding: utf-8 -*-
# 반려동물 등록 — 시군구마다 개·고양이 등록 누계(2026-10-15 소유자 「지역별 반려견 반려묘 관련 데이터는 있을지」)
#   원자료 = 공공데이터포털 15125454 「농림축산검역본부_행정구역별 반려동물등록 개체 수 현황」(2022년 말 누계 · 사망 제외 · 이용허락 제한 없음)
#           받기: py -3.12 -X utf8 tools/region/dgfile.py 15125454 → 07_API키/out/dg/15125454/x.csv(cp949)
#   → data/pet-reg.json (tg-pet-reg/1) — 시군구 코드는 data/r/index.json 에 맞춘다 · 시 단위로만 있는 줄(수원시·화성시 등)은 구들을 묶어 「city」로
#   ⚠ 「등록된 수」라 실제 기르는 수보다 적다 · 고양이는 등록 의무가 아니라 훨씬 적게 잡힌다(최소값으로만 읽기)
#   py -3.12 -X utf8 tools/region/petreg-bake.py
import os, json, csv, io, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15125454', 'x.csv')
SIDO = {'서울특별시': '11', '부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '광주광역시': '12', '대전광역시': '30', '울산광역시': '31',
        '세종특별자치시': '36', '경기도': '41', '강원도': '51', '충청북도': '43', '충청남도': '44', '전라북도': '52', '전라남도': '12',
        '경상북도': '47', '경상남도': '48', '제주특별자치도': '50'}


def main():
    raw = open(SRC, 'rb').read()
    try:
        txt = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        txt = raw.decode('cp949')
    rows = list(csv.reader(io.StringIO(txt)))[1:]
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8'))['gus']
    cen = json.load(open(os.path.join(ROOT, 'data', 'gu-census.json'), encoding='utf-8'))['gu']
    nm = lambda s: s.replace(' ', '')
    gu, city, sido, miss, old = {}, {}, {}, [], {}
    for r in rows:
        if len(r) < 5:
            continue
        s, g, dog, cat, tot = r[0].strip(), r[1].strip(), int(r[2] or 0), int(r[3] or 0), int(r[4] or 0)
        if not g:
            sido[s] = {'dog': dog, 'cat': cat, 'all': tot}; continue
        sc = SIDO.get(s)
        cand = [x for x in IX if x['sido'] == sc and nm(x['name']) == nm(g)] or [x for x in IX if nm(x['name']) == nm(g) and sum(1 for y in IX if nm(y['name']) == nm(g)) == 1]
        if len(cand) == 1:
            c = cand[0]['gu']; hh = (cen.get(c) or {}).get('hh')
            gu[c] = {'nm': cand[0]['name'], 'dog': dog, 'cat': cat, 'all': tot, 'per1k_hh': round(tot * 1000 / hh, 1) if hh else None}
            continue
        sub = [x for x in IX if x['sido'] == sc and nm(x['name']).startswith(nm(g))]
        if sub:
            city[sc + ':' + g] = {'nm': g, 'gus': [x['gu'] for x in sub], 'dog': dog, 'cat': cat, 'all': tot}
        elif sc == '36':
            c = [x['gu'] for x in IX if x['sido'] == '36'][0]; o = gu.setdefault(c, {'nm': '세종특별자치시', 'dog': 0, 'cat': 0, 'all': 0, 'per1k_hh': None})
            o['dog'] += dog; o['cat'] += cat; o['all'] += tot   # 세종은 원자료에 「세종특별자치시」·「조치원읍」 두 줄 — 합친다
        else:
            old[s + ' ' + g] = {'dog': dog, 'cat': cat, 'all': tot}; miss.append(s + ' ' + g)   # 2022년 뒤 없어진 이름(인천 중·동·서구 → 제물포·영종·서해·검단 · 옛 군·창원 옛 구) — 지금 구에 나눠 넣지 않는다
    doc = {'schema': 'tg-pet-reg/1', 'made': datetime.date.today().isoformat(),
           'source': '농림축산식품부 농림축산검역본부 「행정구역별 반려동물등록 개체 수 현황」(공공데이터포털 15125454 · 2022년 말 누계 · 사망 제외 · 이용허락 제한 없음)',
           'fields': 'gu{시군구 코드: {nm, dog 개 등록, cat 고양이 등록, all 합, per1k_hh 일반가구 1,000곳당 등록(가구 = 2020 총조사 gu-census)}} · city{시도:시 이름: {nm, gus[그 시의 구 코드], dog, cat, all}} — 시 단위로만 나온 줄 · sido{시도 이름: {dog, cat, all}} · old{옛 이름: {dog, cat, all}} — 2022년 뒤 행정구역이 바뀌어 지금 구에 못 맞춘 줄',
           'note': ['「등록된 수」 — 실제 기르는 수보다 적다(등록 안 한 개는 안 잡힌다)', '고양이는 등록 의무가 아니다 — 최소값으로만 읽는다', '2022년 말 누계 — 그 뒤 새로 생긴 구(화성 등)는 시 단위 city 에', '읍·면·동 단위 공식 자료는 서울에 없다 — 동 단위는 동물병원·미용 등 업소로 어림(따로)'],
           'n': {'gu': len(gu), 'city': len(city), 'old': len(old)}, 'gu': gu, 'city': city, 'old': old, 'sido': sido}
    p = os.path.join(ROOT, 'data', 'pet-reg.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(gu), '· 시 단위', len(city), '· 못 맞춤', miss)
    for c in ('11650', '11680', '11590', '11620', '11170', '11710'):
        print(c, gu.get(c))


if __name__ == '__main__':
    main()
