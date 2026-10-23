# -*- coding: utf-8 -*-
# 데이터 압축지도 — 온톨로지 「사건(EVT)」 한 장 → data/onto-events.json (tg-onto-events/1)
#   소유자 2026-10-23 「권고대로 둘째 — 집회·공연·침수·돌발을 상시 사건 객체로」(엮임 지도 둘째)
#   ontology-core/build.py 가 이 파일만 읽어 사건 객체와 교차로 링크를 만든다(코어는 저장소 안 파일로만 굽는다 — 다시 구워도 같게)
#   원천(값은 그대로 · 범위 = 서초·강남·송파·동작·관악·용산 교차로 둘레 상자):
#     집회 = data/rally-seoul.json(서울경찰청 「오늘의 주요집회」 · 지난 90일 · 주요 집회만 · 신고 인원)
#     공연 = data/venue-events-kopis.json(KOPIS · 좌석 1,000 이상 공연장 · 오늘 앞 90일 ~ 뒤 21일에 걸친 회차 묶음)
#     침수 = data/season-seocho.json(서울시 침수흔적도 · 해마다 · 침수된 건물·필지 가운데 점 · 서초만) — 해 하나가 사건 하나, 점은 traces 로 그대로
#     돌발 = 07_API키/out/liveacc/*.jsonl.gz(서울 TOPIS 실시간 돌발 · 10분마다 받은 한 장들 · 2026-10-15~) + 07_API키/out/utic/ims/*.jsonl.gz(경찰청 UTIC 돌발 · 같은 날부터)
#            — 같은 돌발 ID 는 하나로 · 처음 본 때·마지막 본 때를 적는다 · 글은 원문 앞 160자
#   py -3.12 -X utf8 tools/onto/evt-bake.py
import json, os, glob, gzip, datetime, math, re
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); D = os.path.join(ROOT, 'data')
OUT = os.path.join(os.path.dirname(ROOT), '07_API키', 'out')
def J(f): return json.load(open(os.path.join(D, f), encoding='utf-8'))
GUS = ['11650', '11680', '11710', '11590', '11620', '11170']
R5 = lambda x: round(x, 6)


def box():
    pts = [(r[2], r[3]) for r in J('onto-int.json')['items'] if r[6] in GUS]
    la = [p[0] for p in pts]; lo = [p[1] for p in pts]
    return min(la) - 0.006, max(la) + 0.006, min(lo) - 0.008, max(lo) + 0.008


def main():
    la0, la1, lo0, lo1 = box()
    def inb(la, lo): return la is not None and lo is not None and la0 <= la <= la1 and lo0 <= lo <= lo1
    ev = []; today = datetime.date.today()
    # 집회
    R = J('rally-seoul.json')
    for x in R['items']:
        if 'lat' not in x or not inb(x['lat'], x['lon']): continue
        key = '%s|%s|%s' % (x['d'], x.get('from') or '', x['p'])
        ev.append(dict(id='EVT-RLY-%s-%s' % (x['d'].replace('-', ''), abs(hash_s(key)) % 100000), kind='집회', src='rally-seoul.json',
                       d0=x['d'] + (' ' + x['from'] if x.get('from') else ''), d1=x['d'] + (' ' + x['to'] if x.get('to') else ''), nm=x['p'][:80],
                       lat=R5(x['lat']), lon=R5(x['lon']), n=x.get('n'), march=1 if x.get('march') else 0,
                       dest=[R5(v) for v in x['dest']] if x.get('dest') else None, approx=x.get('approx', 0), st=x.get('st')))
    # 공연(회차 묶음 = 한 공연의 처음~끝 날)
    K = J('venue-events-kopis.json'); lo_d = (today - datetime.timedelta(days=90)).isoformat(); hi_d = (today + datetime.timedelta(days=21)).isoformat()
    for v in K['venues']:
        if not v.get('lat') or not inb(v['lat'], v['lon']): continue
        for s in v.get('shows') or []:
            if (s[7] or 0) < 1000 or s[3] < lo_d or s[2] > hi_d: continue
            ev.append(dict(id='EVT-PRF-%s' % s[8], kind='공연', src='venue-events-kopis.json', d0=s[2], d1=s[3], nm=('%s — %s' % (v['n'], s[0]))[:80],
                           lat=R5(v['lat']), lon=R5(v['lon']), n=s[7], hall=s[6], times=s[4], dur=s[5]))
    # 침수(해 하나 = 사건 하나 · 점은 그대로)
    S = J('season-seocho.json'); tr = {}
    for t in S['traces']:
        lo = 127.01 + t[0] / 88800.0; la = 37.49 - t[1] / 111000.0   # 지도 평면 근사 P(lon,lat) 의 되돌림(MAP2D.md 원칙 2)
        tr.setdefault(t[2], []).append([R5(la), R5(lo), t[3], t[4]])
    for y in sorted(tr):
        ev.append(dict(id='EVT-FLD-%d' % y, kind='침수', src='season-seocho.json', d0=str(y), d1=str(y), nm='%d년 침수 흔적(서초)' % y, n=len(tr[y]), dep=max(t[3] for t in tr[y])))   # 점은 season-seocho.json 그대로 — 코어가 직접 읽는다
    # 돌발 — TOPIS(liveacc) · UTIC(ims) 받은 기록
    seen = {}
    def take(i, kind, la, lo, start, end, title, road, src, t):
        if not inb(la, lo): return
        e = seen.get(i)
        if e: e['last'] = max(e['last'], t); return
        seen[i] = dict(id='EVT-INC-%s' % re.sub(r'[^0-9A-Za-z]', '', i), kind='돌발', sub=kind, src=src, d0=start, d1=end, nm=(title or '')[:120].replace('\r', ' ').replace('\n', ' '),
                       road=road, lat=R5(la), lon=R5(lo), first=t, last=t)
    def ymd(s):
        m = re.match(r'(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})$', s or '')
        if m: return '%s-%s-%s %s:%s' % m.groups()
        m = re.match(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일\s*(\d{1,2})시\s*(\d{1,2})분', s or '')
        return '%s-%02d-%02d %02d:%02d' % (m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))) if m else (s or None)
    for f in sorted(glob.glob(os.path.join(OUT, 'liveacc', '*.jsonl.gz'))):
        for L in gzip.open(f, 'rt', encoding='utf-8'):
            d = json.loads(L)
            for it in d['items']: take('T' + str(it[0]), it[2], it[5], it[6], ymd(it[7]), ymd(it[8]), it[9], None, 'TOPIS 실시간 돌발(liveacc)', d['t'])
    for f in sorted(glob.glob(os.path.join(OUT, 'utic', 'ims', '*.jsonl.gz'))):
        for L in gzip.open(f, 'rt', encoding='utf-8'):
            d = json.loads(L)
            for it in d['items']: take('U' + str(it[0]), it[1], it[4], it[5], ymd(it[9]), ymd(it[10]), it[11], it[7], '경찰청 UTIC 돌발(ims)', d['t'])
    ev += sorted(seen.values(), key=lambda e: (e['first'], e['id']))
    hist = sorted({os.path.basename(f)[:8] for f in glob.glob(os.path.join(OUT, 'liveacc', '*.jsonl.gz')) + glob.glob(os.path.join(OUT, 'utic', 'ims', '*.jsonl.gz'))})
    doc = {'schema': 'tg-onto-events/1', 'made': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'),
           'source': '집회 = 서울경찰청 「오늘의 주요집회」(rally-seoul.json) · 공연 = 공연예술통합전산망 KOPIS(venue-events-kopis.json) · 침수 = 서울시 침수흔적도(season-seocho.json · 공공누리 1유형) · 돌발 = 서울시 TOPIS 실시간 돌발(서울 열린데이터광장 AccInfo) · 교통정보: 경찰청 도시교통정보센터(UTIC) 제공',
           'fields': 'items[{id, kind 집회|공연|침수|돌발, sub 돌발 갈래(공사·사고·차량고장·통제…), src 원천, d0 시작, d1 끝(예정), nm 이름·글(돌발은 원문 앞 120자), lat·lon(침수는 없음 — 점은 season-seocho.json traces · dep 그 해 가장 깊은 침수심 m), n 신고 인원·좌석·흔적 수, march 행진, dest 행진 끝, approx 자리 근사, st 관할서(원문), hall 관·times 시각 글·dur 공연시간 분, road 도로, first·last 처음·마지막으로 받은 때(돌발)}]',
           'note': ['범위 = 서초·강남·송파·동작·관악·용산 교차로 둘레 상자(침수만 서초)', '집회는 주요 집회만 · 신고값 · 공연은 1,000석 이상 공연장 · 오늘 앞 90일~뒤 21일',
                    '돌발은 이 PC 가 10분마다 받은 한 장들을 모은 것(%s~%s · %d일) — 받지 못한 시간의 돌발은 없다 · 같은 ID 는 하나' % (hist[0] if hist else '', hist[-1] if hist else '', len(hist)),
                    '침수 흔적 = 침수된 건물·필지 가운데 점(길이 잠겼다는 기록 아님) · 2015·2021 없음'],
           'box': [la0, la1, lo0, lo1], 'items': ev}
    p = os.path.join(D, 'onto-events.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    from collections import Counter
    print('onto-events.json', Counter(e['kind'] for e in ev), '·', os.path.getsize(p) // 1024, 'KB')


def hash_s(s):
    h = 0
    for ch in s: h = (h * 131 + ord(ch)) & 0x7fffffff
    return h


if __name__ == '__main__':
    main()
