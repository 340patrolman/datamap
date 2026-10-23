# -*- coding: utf-8 -*-
# 데이터 압축지도 — 서초·방배 관할 주요집회를 폰 캘린더 구독 파일로 → data/rally-seocho.ics
#   소유자 2026-10-23 「서초경찰서 관내 집회신고된 내용을 티북 교대근무표에 넣을 수 있을까」 → 권고 「T-Book 은 손대지 않고 캘린더 구독」 승인
#   T-Book 교대근무표는 폰 캘린더로 내보낼 수 있다(v23.76) — 같은 폰 캘린더에서 근무와 집회가 나란히 보인다
#   원자료 = data/rally-seoul.json(서울경찰청 「오늘의 주요집회」 · rally-bake.py 가 날마다) — 관할서 글에 「서초」·「방배」가 든 것만
#   싣는 것 = 게시판에 공개된 일시·장소 글·신고 인원·관할서뿐(주최자 없음 · 지어 넣지 않음) · 지난 30일 + 앞으로
#   RFC 5545 · 시각은 UTC(Z) · UID 고정(같은 집회는 다시 받아도 덮임) · 줄 75바이트 접기(한글이 안 잘리게)
#   py -3.12 -X utf8 tools/region/rally-ics.py      (rally-bake.py 끝에서도 부른다)
import json, os, hashlib, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'data', 'rally-seoul.json'); OUT = os.path.join(ROOT, 'data', 'rally-seocho.ics')
KEEP_DAYS = 30


def esc(s):
    return str(s).replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\n', '\\n')


def fold(line):
    b = line.encode('utf-8'); out = []; cur = b''; first = True
    for ch in line:
        c = ch.encode('utf-8'); lim = 75 if first else 74
        if len(cur) + len(c) > lim:
            out.append(cur); cur = b''; first = False
        cur += c
    out.append(cur)
    return b'\r\n '.join(out).decode('utf-8')


def utc(d, hm):
    t = datetime.datetime.strptime(d + ' ' + hm, '%Y-%m-%d %H:%M') - datetime.timedelta(hours=9)
    return t.strftime('%Y%m%dT%H%M%SZ')


def build():
    doc = json.load(open(SRC, encoding='utf-8'))
    since = (datetime.date.fromisoformat(doc['collected']) - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    its = [x for x in doc['items'] if x['d'] >= since and any(k in (x.get('st') or '') for k in ('서초', '방배'))]
    its.sort(key=lambda x: (x['d'], x.get('from') or '', x['p']))
    now = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    L = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//340patrolman//datamap rally-seocho//KO', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH',
         'X-WR-CALNAME:서초·방배 주요집회(경찰청 공개)', 'X-WR-TIMEZONE:Asia/Seoul',
         'X-WR-CALDESC:' + esc('서울경찰청 「오늘의 주요집회」 게시판 글 중 관할서에 서초·방배가 든 것 · 받은 날 %s · 주요 집회만(모든 집회 아님) · 인원은 신고값 · 바뀌거나 안 열릴 수 있음' % doc['collected']),
         'REFRESH-INTERVAL;VALUE=DURATION:PT6H', 'X-PUBLISHED-TTL:PT6H']
    for x in its:
        uid = 'rally-%s-%s@340patrolman.datamap' % (x['d'], hashlib.sha1((x['p'] + (x.get('from') or '')).encode('utf-8')).hexdigest()[:10])
        place = x['p']
        title = '집회 %s%s(%s명)' % ('행진 ' if x.get('march') else '', place.split('<')[0].strip()[:30], format(x['n'], ',') if x.get('n') else '인원 미기재')
        desc = ['장소(원문): ' + place, '신고 인원: %s' % (('%s명' % format(x['n'], ',')) if x.get('n') else '원문에 없음'),
                '관할(원문): %s' % (x.get('st') or '원문에 없음'), '시각(원문): %s~%s' % (x.get('from') or '?', x.get('to') or '?')]
        if x.get('march'): desc.append('행진(장소 글에 「->」)')
        desc += ['출처: 서울경찰청 「오늘의 주요집회」 www.smpa.go.kr/user/nd54882.do', '주요 집회만 · 신고값 · 바뀌거나 안 열릴 수 있음']
        L += ['BEGIN:VEVENT', 'UID:' + uid, 'DTSTAMP:' + now]
        if x.get('from'):
            L.append('DTSTART:' + utc(x['d'], x['from']))
            if x.get('to') and x['to'] > x['from']: L.append('DTEND:' + utc(x['d'], x['to']))
            else: L.append('DURATION:PT1H'); desc.append('끝 시각이 원문에 없어 1시간으로 둠')
        else:
            d0 = datetime.date.fromisoformat(x['d'])
            L += ['DTSTART;VALUE=DATE:' + d0.strftime('%Y%m%d'), 'DTEND;VALUE=DATE:' + (d0 + datetime.timedelta(days=1)).strftime('%Y%m%d')]
            desc.append('시각이 원문에 없어 하루 일정으로 둠')
        L += ['SUMMARY:' + esc(title), 'LOCATION:' + esc(place), 'DESCRIPTION:' + esc('\n'.join(desc)), 'TRANSP:TRANSPARENT']
        if 'lat' in x: L.append('GEO:%.6f;%.6f' % (x['lat'], x['lon']))
        L.append('END:VEVENT')
    L.append('END:VCALENDAR')
    body = '\r\n'.join(fold(l) for l in L) + '\r\n'
    open(OUT, 'w', encoding='utf-8', newline='').write(body)
    print('rally-seocho.ics 일정', len(its), '건 ·', since, '~', doc['range'][1] if doc.get('range') else '', '·', len(body.encode('utf-8')) // 1024, 'KB')
    return len(its)


if __name__ == '__main__':
    build()
