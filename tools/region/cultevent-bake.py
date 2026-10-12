# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🎭 공연·행사 일정(서울 문화행사) → data/venue-events-seoul.json
#   소유자 2026-10-12 「서로가 서로에게 영향을 미치며 사니」 → 끝나는 시각에 둘레 역·교차로가 한꺼번에 막히는 것을 보려면 「어디서 · 언제 시작해 · 언제 끝나나」가 있어야 한다
#   원자료: 서울 열린데이터광장 「서울시 문화행사 정보」(culturalEventInfo · 키 seoul · http · 전부 받아 07_API키/out/cultevent/culturalEventInfo_<날짜>.json)
#   ⚠ 이 자료는 서울시·자치구·산하 기관이 올린 행사가 대부분이다 — 큰 민간 공연장·경기장(잠실야구장·고척돔·KSPO돔·상암)의 일정은 거의 없다(more-sources.json 의 공연·경기 줄)
#   ⚠ 시각 칸(PRO_TIME)은 사람이 쓴 글이다 — 「19:30」「오후 7시 30분」처럼 읽히는 것만 시작 시각으로 옮기고, 끝 시각은 「~ 21:00」처럼 적힌 것만 옮긴다. 나머지는 null(모름). 수용 인원은 자료에 없다
#   py -3.12 -X utf8 tools/region/cultevent-bake.py
import json, os, re, glob, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'cultevent')
def hm(s):
    # 글 한 토막 → 'HH:MM' 또는 None
    m = re.match(r'\s*(오전|오후|AM|PM|am|pm)?\s*(\d{1,2})\s*(?::|시)\s*(\d{1,2})?\s*(분)?\s*(AM|PM|am|pm)?', s)
    if not m: return None
    h = int(m.group(2)); mi = int(m.group(3) or 0); ap = (m.group(1) or m.group(5) or '').lower()
    if ap in ('오후', 'pm') and h < 12: h += 12
    if h > 24 or mi > 59: return None
    return '%02d:%02d' % (h, mi)
def times(t):
    t = (t or '').strip()
    if not t or re.search(r'[월화수목금토일]\s*[-~,]|매주|휴관|/|,|회', t): return None, None
    a = re.split(r'\s*[~\-–]\s*', t, maxsplit=1); s = hm(a[0])
    if not s: return None, None
    e = hm(a[1]) if len(a) > 1 else None
    if e and e < s and not re.search(r'오전|오후|AM|PM', a[1], re.I) and int(e[:2]) < 12: e = '%02d%s' % (int(e[:2]) + 12, e[2:])
    return s, (e if e and e > s else None)
def main():
    f = sorted(glob.glob(os.path.join(SRC, 'culturalEventInfo_*.json')))[-1]; rows = json.load(open(f, encoding='utf-8')); today = datetime.date.today(); ahead = (today + datetime.timedelta(days=75)).isoformat(); td = today.isoformat()
    V = collections.OrderedDict(); nolL = 0
    for r in rows:
        try: la = float(r['LAT']); lo = float(r['LOT'])
        except Exception: nolL += 1; continue
        if la > 90: la, lo = lo, la
        if not (37.3 < la < 37.75 and 126.7 < lo < 127.3): nolL += 1; continue
        k = (round(la, 4), round(lo, 4)); v = V.setdefault(k, {'nm': collections.Counter(), 'gu': r['GUNAME'], 'yr': collections.Counter(), 'kind': collections.Counter(), 'day': [], 'up': []})
        v['nm'][r['PLACE'].strip()] += 1; s = r['STRTDATE'][:10]; e = r['END_DATE'][:10]; v['yr'][s[:4]] += 1; v['kind'][r['CODENAME']] += 1; a, b = times(r.get('PRO_TIME'))
        if s == e and a: v['day'].append([s, a, b, r['CODENAME']])
        if e >= td and s <= ahead: v['up'].append([r['TITLE'].strip()[:60], r['CODENAME'], s, e, a, b, (r.get('PRO_TIME') or '').strip()[:40], r.get('HMPG_ADDR') or ''])
    venues = []
    for (la, lo), v in V.items():
        venues.append({'n': v['nm'].most_common(1)[0][0], 'gu': v['gu'], 'lat': la, 'lon': lo, 'yr': dict(sorted(v['yr'].items())), 'kind': dict(v['kind'].most_common(4)), 'day': sorted(v['day'], key=lambda x: (x[0], x[1])), 'up': sorted(v['up'], key=lambda x: x[2])})
    venues.sort(key=lambda v: -sum(v['yr'].values()))
    nd = sum(len(v['day']) for v in venues); ne = sum(1 for v in venues for d in v['day'] if d[2]); nu = sum(len(v['up']) for v in venues)
    doc = {'schema': 'tg-venue-events/1', 'made': td, 'source': '서울 열린데이터광장 「서울시 문화행사 정보」(culturalEventInfo · 서울문화포털) — %s 받음 · %d건' % (os.path.basename(f)[18:26], len(rows)),
           'note': ['**서울시·자치구·산하 기관이 올린 행사가 대부분이다** — 큰 민간 공연장·경기장(야구·축구·농구 · 대형 콘서트)의 일정은 거의 없다. 「이 자리 둘레에 행사가 없다」로 읽으면 안 된다',
                    '시작·끝 시각은 사람이 쓴 글(PRO_TIME)에서 읽히는 것만 옮겼다 — 끝 시각 null = 모름(공연은 흔히 90~150분이지만 이 자료가 말해 주지 않는다 · 지어 넣지 않았다). 하루짜리 %d건 가운데 끝 시각이 적힌 것은 %d건' % (nd, ne),
                    '수용 인원은 자료에 없다 — 사람이 얼마나 몰리는지는 이 파일로 알 수 없다(둘레 역 승하차·생활인구와 날짜를 맞대 봐야 한다)',
                    '여러 날 이어지는 전시·교육·축제는 day 에 넣지 않았다(yr·kind 에는 셌다) · 앞으로 75일 안에 걸치는 것은 up 에 글 그대로',
                    '자리(좌표)가 없거나 서울 밖인 %d건은 뺐다 · 같은 건물의 여러 홀은 좌표가 같으면 한 곳으로 묶였다(이름은 가장 많이 쓰인 것)' % nolL],
           'fields': {'venues': '[{n 장소 이름, gu 자치구, lat, lon, yr {해: 행사 수(시작일 기준)}, kind {갈래: 수}(많은 넷), day [[날짜, 시작 HH:MM, 끝 HH:MM 또는 null, 갈래]](하루짜리 · 시작 시각이 읽힌 것 · 지난 것 포함), up [[제목, 갈래, 시작일, 끝일, 시작 시각 또는 null, 끝 시각 또는 null, 시각 글 그대로, 서울문화포털 주소]](오늘부터 75일 안)}] — 행사 많은 차례'},
           'venues': venues}
    p = os.path.join(ROOT, 'data', 'venue-events-seoul.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('바이트', os.path.getsize(p), '장소', len(venues), '하루짜리', nd, '끝 시각 있음', ne, '앞으로', nu, '뺌', nolL)
    for v in venues[:12]: print(v['n'], v['gu'], sum(v['yr'].values()), len(v['day']), len(v['up']))
    sc = [v for v in venues if v['gu'] == '서초구']; print('서초', len(sc), [(v['n'], sum(v['yr'].values())) for v in sc[:12]])
    import random; random.seed(1); print(random.sample([d for v in venues for d in v['day']], 12))
if __name__ == '__main__': main()
