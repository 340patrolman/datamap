# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🎒 「사람 수가 달라지는 날」 가운데 학교 달력(서울 초·중·고) → data/school-cal-seoul.json
#   소유자 2026-10-12 「서로가 서로에게 영향을 미치며 사니」 → 방학·개학·재량휴업·수능 날에는 등하교 시간의 길과 학원가가 달라진다(신호 특수일 sig-special.json · 공휴일 holidays.json 옆에 놓는 표)
#   원자료: 나이스 교육정보 개방 포털 학사일정(SchoolSchedule · 열쇠 neis · 학교 코드마다 한 번) → 07_API키/out/neis_cal/B10_<처음>_<끝>.json = [[날짜, 학교급, 행사 이름, 학교 수]](방학·개학·졸업·입학·재량휴업·수능 낱말이 든 것만)
#   ⚠ 학교가 적은 글이다 — 방학을 날마다 적는 학교와 방학식 하루만 적는 학교가 섞여 있다. 그래서 「방학 중인 학교 몫」은 **적어 둔 학교 가운데서** 의 몫이고 실제보다 낮게 잡힌다(가장 높은 날의 값을 같이 싣는다)
#   py -3.12 -X utf8 tools/region/schoolcal-bake.py
import json, os, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'neis_cal')
K = ['초등학교', '중학교', '고등학교']
def main():
    f = sorted(glob.glob(os.path.join(SRC, 'B10_*.json')))[-1]; d = json.load(open(f, encoding='utf-8')); N = d['schools']
    VAC = collections.defaultdict(collections.Counter); OFF = collections.Counter(); OPEN = collections.Counter(); GRAD = collections.Counter(); ENT = collections.Counter(); CSAT = collections.Counter(); MOCK = collections.Counter()
    for day, kind, nm, n in d['rows']:
        if '방학' in nm and '식' not in nm and '개학' not in nm: VAC[day][kind] += n
        if '재량휴업' in nm: OFF[day] += n
        if '개학' in nm or '시업' in nm: OPEN[day] += n
        if '졸업식' in nm: GRAD[day] += n
        if '입학식' in nm: ENT[day] += n
        if ('수능' in nm or '대학수학능력' in nm):
            if '모의' in nm or '예비' in nm: MOCK[day] += n
            else: CSAT[day] += n
    days = sorted(set(VAC) | set(OFF) | set(OPEN) | set(GRAD) | set(ENT)); peak = {k: max((VAC[x][k] for x in VAC), default=0) for k in K}
    rows = []
    for x in days:
        v = [min(100, round(VAC[x][k] / peak[k] * 100)) if peak[k] else None for k in K]
        if max(t or 0 for t in v) < 3 and OFF[x] < 20 and OPEN[x] < 20 and GRAD[x] < 20 and ENT[x] < 20: continue
        rows.append(['%s-%s-%s' % (x[:4], x[4:6], x[6:])] + v + [OFF[x], OPEN[x], GRAD[x], ENT[x]])
    csat = [['%s-%s-%s' % (x[:4], x[4:6], x[6:]), n] for x, n in CSAT.most_common(3)]
    doc = {'schema': 'tg-school-cal/1', 'made': datetime.date.today().isoformat(), 'source': '나이스 교육정보 개방 포털 학사일정(SchoolSchedule) — 서울특별시교육청 초·중·고 %d곳 · %s' % (d['got'], os.path.basename(f)[4:21]),
           'note': ['**학교가 손으로 적은 일정이다** — 방학을 날마다 적는 학교와 방학식 하루만 적는 학교가 섞여 있다. 방학 몫 = 그 학교급에서 **방학을 가장 많이 적은 날을 100 으로 본** 값(초 %d · 중 %d · 고 %d곳이 꼭대기 · 전체는 %d · %d · %d곳)' % (peak[K[0]], peak[K[1]], peak[K[2]], N[K[0]], N[K[1]], N[K[2]]),
                    '주말·공휴일도 방학 기간에 들어 있으면 그대로 실린다 · 공휴일은 holidays.json · 신호가 달라지는 날은 sig-special.json 을 본다',
                    '수능 날은 학교가 적은 날짜 가운데 가장 많이 적힌 날이다(교육부 시행 공고와 맞대 볼 것) — 시험장 학교 목록은 여기에 없다(서울시교육청 공고)',
                    '급여일·명절 대이동·대학 개강 같은 「사람 수가 달라지는 날」은 여기에 없다(more-sources.json)'],
           'fields': {'days': '[[날짜, 초 방학 몫 %, 중 방학 몫 %, 고 방학 몫 %, 재량휴업 적은 학교 수, 개학·시업식 학교 수, 졸업식 학교 수, 입학식 학교 수]] — 아무 일도 거의 없는 날은 뺐다', 'csat': '[[날짜, 그 날을 수능으로 적은 학교 수]](많은 셋)', 'schools': '{학교급: 학교 수}'},
           'schools': N, 'csat': csat, 'days': rows}
    p = os.path.join(ROOT, 'data', 'school-cal-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '날', len(rows), '꼭대기', peak, '수능', csat, '모의', MOCK.most_common(3))
    print('재량휴업 많은 날', [(x, n) for x, n in OFF.most_common(8)]); print('개학 많은 날', OPEN.most_common(6)); print([r for r in rows if r[0] in ('2026-07-20', '2026-07-27', '2026-08-17', '2026-08-24', '2026-12-28', '2027-01-11')])
if __name__ == '__main__': main()
