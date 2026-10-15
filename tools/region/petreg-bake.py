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
    # (덧붙임) 동 단위 어림 — 행정동마다 동물병원(M11101) + 애완동물·용품 소매(G22001) 점포 수(data/storecls · 소상공인 상가정보)로 구 등록 수를 나눈다
    import glob
    cls = json.load(open(os.path.join(ROOT, 'data', 'storecls', 'cls.json'), encoding='utf-8'))['cls']
    ih = [i for i, c in enumerate(cls) if c[5] == 'M11101'][0]; ip = [i for i, c in enumerate(cls) if c[5] == 'G22001'][0]
    dong, bygu = {}, {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'storecls', '[0-9]*.json')):
        for dc, v in json.load(open(f, encoding='utf-8'))['dong'].items():
            m = dict((k, n) for k, n in v[2]); h, q = m.get(ih, 0), m.get(ip, 0)
            dong[dc] = [v[0], h, q, None]; bygu.setdefault(dc[:5], 0); bygu[dc[:5]] += h + q
    for dc, v in dong.items():
        g = gu.get(dc[:5]); tb = bygu.get(dc[:5], 0)
        if g and tb:
            v[3] = round(g['all'] * (v[1] + v[2]) / tb)
    # (덧붙임 2026-10-15 소유자 「개도 별로 등록 안 하고 고양이는 등록한 사람을 못 봤다 · 유추로 대략」) 실제 수 추정(E) — 전국 기준점 두 벌로 범위
    #   개 = 등록 ÷ 전국 등록률(전국 등록 누계 ÷ 전국 개 수) · 고양이 = 일반가구 × 전국 가구당 고양이(전국 고양이 ÷ 전국 일반가구 20,926,710 = 2020 총조사)
    #   기준점: 2022 농식품부 국민의식조사 보도 개 544.8만·고양이 254.1만 / 2024 데일리벳 역산 추정 개 499만·고양이 277만(둘 다 국가 승인 통계 아님)
    NAT_HH = 20926710
    dogN = sum(v['dog'] for v in sido.values())
    ANCH = [('2022 조사 보도', 5448000, 2541000), ('2024 언론 역산', 4990000, 2770000)]
    rates = [(lab, dogN / D, C / NAT_HH) for lab, D, C in ANCH]
    for c, v in gu.items():
        hh = (cen.get(c) or {}).get('hh')
        dogs = sorted(round(v['dog'] / r / 100) * 100 for _, r, _ in rates)
        cats = sorted(round(hh * k / 100) * 100 for _, _, k in rates) if hh else None
        v['est'] = {'dog': dogs, 'cat': cats}
    est_note = {'how': '개 = 등록 ÷ 전국 등록률 · 고양이 = 일반가구(2020) × 전국 가구당 고양이 — 두 기준점의 범위 [낮음, 높음]', 'anchors': [[lab, round(r, 3), round(k, 4)] for lab, r, k in rates],
                'grade': 'E 추정', 'caveat': ['등록률을 전국 하나로 씀 — 서울은 등록률이 더 높을 수 있어 실제는 더 적을 수 있다', '고양이는 가구 수만 따라감 — 1인 가구가 많은 곳은 더 많을 수 있다', '기준점(전국 개·고양이 수)은 국가 승인 통계가 아니다']}
    doc = {'schema': 'tg-pet-reg/1', 'made': datetime.date.today().isoformat(),
           'source': '농림축산식품부 농림축산검역본부 「행정구역별 반려동물등록 개체 수 현황」(공공데이터포털 15125454 · 2022년 말 누계 · 사망 제외 · 이용허락 제한 없음)',
           'fields': 'gu{시군구 코드: {nm, dog 개 등록, cat 고양이 등록, all 합, per1k_hh 일반가구 1,000곳당 등록(가구 = 2020 총조사 gu-census), est{dog:[낮음,높음], cat:[낮음,높음]|null} 실제 수 추정(E · 아래 est 설명)}} · city{시도:시 이름: {nm, gus[그 시의 구 코드], dog, cat, all}} — 시 단위로만 나온 줄 · sido{시도 이름: {dog, cat, all}} · old{옛 이름: {dog, cat, all}} — 2022년 뒤 행정구역이 바뀌어 지금 구에 못 맞춘 줄 · dong{행정동 8자리: [이름, 동물병원 수, 애완동물·용품 소매 수, 등록 어림(구 등록 × 이 동 업소 ÷ 구 업소 · 업소 없는 구면 null)]} — **어림(D)**: 업소는 손님이 오는 상권에 몰려 사는 곳과 다를 수 있다',
           'note': ['「등록된 수」 — 실제 기르는 수보다 적다(등록 안 한 개는 안 잡힌다)', '고양이는 등록 의무가 아니다 — 최소값으로만 읽는다', '2022년 말 누계 — 그 뒤 새로 생긴 구(화성 등)는 시 단위 city 에', '읍·면·동 단위 공식 자료는 서울에 없다 — 동 단위는 동물병원·미용 등 업소로 어림(따로)'],
           'n': {'gu': len(gu), 'city': len(city), 'old': len(old), 'dong': len(dong)}, 'gu': gu, 'city': city, 'old': old, 'sido': sido, 'dong': dong, 'est': est_note}
    p = os.path.join(ROOT, 'data', 'pet-reg.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('시군구', len(gu), '· 시 단위', len(city), '· 못 맞춤', miss)
    for c in ('11650', '11680', '11590', '11620', '11170', '11710'):
        print(c, gu.get(c))


if __name__ == '__main__':
    main()
