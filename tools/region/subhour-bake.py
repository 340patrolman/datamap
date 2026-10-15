# -*- coding: utf-8 -*-
"""역 × 시간대 승하차 몫 — 도착 예측(선착 역) 혼잡 배수의 바탕(2026-10-15 소유자 「도착 예측 ver.1 프롬프트 · 계속 진행」)

원자료 = 서울 열린데이터광장 OA-12252 「서울시 지하철 호선별 역별 시간대별 승하차 인원 정보」(서비스 CardSubwayTime · 교통카드 · 달마다 합계)
  https://data.seoul.go.kr/dataList/OA-12252/S/1/datasetView.do — 2026-10-15 쪽 제목 「시간대별 승하차 인원 정보」 확인 · 칸 USE_MM · SBWY_ROUT_LN_NM · STTN · HR_<시>_GET_ON_NOPE · HR_<시>_GET_OFF_NOPE · JOB_YMD
  받은 달 파일 = ../07_API키/out/subway_month/<연월>.json(이미 받아 둔 것 · 새로 부르지 않는다)
⚠ 달 합계라 평일·주말이 섞여 있다 — 요일 갈래(dayType)는 이 자료로 가를 수 없다(미확인 아님 · 자료에 없음)
  py -3.12 -X utf8 tools/region/subhour-bake.py [연월 연월 …]      (안 적으면 받아 둔 마지막 석 달)
"""
import os, sys, json, glob, calendar, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'subway_month')
OUT = os.path.join(ROOT, 'data', 'subway-hour-seoul.json')
H0, H1 = 5, 24   # 몫의 바탕 = 5~24시(0~4시는 운행이 거의 없어 평균을 끌어내린다)


def main():
    yms = sys.argv[1:] or sorted(os.path.basename(f)[:6] for f in glob.glob(os.path.join(SRC, '2?????.json')))[-3:]
    acc, days = {}, 0
    for ym in yms:
        rows = json.load(open(os.path.join(SRC, ym + '.json'), encoding='utf-8'))
        days += calendar.monthrange(int(ym[:4]), int(ym[4:]))[1]
        for r in rows:
            k = (r['STTN'].strip(), r['SBWY_ROUT_LN_NM'].strip())
            a = acc.setdefault(k, [[0.0] * 24, [0.0] * 24, set()])
            for h in range(24):
                a[0][h] += float(r.get('HR_%d_GET_ON_NOPE' % h) or 0); a[1][h] += float(r.get('HR_%d_GET_OFF_NOPE' % h) or 0)
            a[2].add(ym)
    out, skip = [], 0
    for (nm, ln), (on, off, ms) in sorted(acc.items()):
        if len(ms) < len(yms):
            skip += 1; continue   # 석 달 모두 있는 역만(새로 연 역·이름이 바뀐 역은 뺀다)
        tot = [on[h] + off[h] for h in range(24)]; base = sum(tot[H0:H1]) / (H1 - H0)
        if base < 30:   # 하루 평균 한 시간에 1명 남짓 — 몫이 흔들려 안 낸다
            skip += 1; continue
        out.append([nm, ln, round(sum(tot) / days), round(sum(on) / days), round(sum(off) / days),
                    [round(t / base, 2) for t in tot], [round(off[h] / base, 2) for h in range(24)]])
    doc = {'schema': 'tg-subway-hour/1', 'made': datetime.date.today().isoformat(),
           'source': '서울 열린데이터광장 OA-12252 서울시 지하철 호선별 역별 시간대별 승하차 인원 정보(CardSubwayTime · 교통카드) — ' + ' · '.join(yms) + ' 합계 · 굽는 도구 tools/region/subhour-bake.py',
           'fields': 'stn[[역 이름, 노선, 하루 평균 승하차, 하루 평균 승차, 하루 평균 하차, [0~23시 승하차 몫], [0~23시 하차 몫]]] — 몫 = 그 시간 인원 ÷ 그 역 5~24시 한 시간 평균(1 = 그 역의 보통 · 2 = 보통의 두 배)',
           'note': ['달 합계라 평일·주말이 섞인 값이다 — 평일 출퇴근 몫은 이보다 크고 주말은 작다(이 자료로는 가를 수 없다)',
                    '교통카드 기록만(1회권·우대권 일부 등 빠질 수 있다) · 갈아타는 사람은 개찰구를 안 지나 안 잡힌다',
                    '몫은 그 역 안에서 견준 값이다 — 역끼리 붐비는 정도를 견줄 때는 하루 평균 인원을 같이 본다',
                    '도보 배수로 바꾸는 식(1 + α·(몫−1) 등)은 이 파일에 없다 — 쓰는 쪽에서 가정값으로 두고 실측으로 고친다'],
           'months': yms, 'days': days, 'stn': out}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('역', len(out), '· 뺀 역', skip, '·', os.path.getsize(OUT), 'B')
    for nm in ('강남', '교대', '서초', '방배', '고속터미널', '양재', '남부터미널'):
        for q in out:
            if q[0].startswith(nm) and q[0] in (nm, nm + '(법원.검찰청)', nm + '(서초구청)', nm + '(예술의전당)'):
                pk = max(range(24), key=lambda h: q[5][h]); print(' ', q[0], q[1], '하루', q[2], '· 가장 붐빔', pk, '시 ×', q[5][pk], '· 8시 ×', q[5][8], '· 18시 ×', q[5][18])


if __name__ == '__main__':
    main()
