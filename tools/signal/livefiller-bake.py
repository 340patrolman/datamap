# -*- coding: utf-8 -*-
# 데이터 압축지도·가르고 — 🚗 ITS 통행속도의 「채움 값」 링크 찾기(2026-11-10 형님 「가르고네비 고도화」) → data/live-spd-filler.json
#   까닭: 가르고가 밤·저녁마다 올림픽대로(반포~한남)를 피해 강변북로로 한강을 두 번 건넜다(서초→잠실 · 노량진→삼성 등 · 카카오는 올림픽대로).
#         ITS trafficInfo 가 그 링크에 새벽 3시에도 시속 21km 를 낸다 — 두 주 기록(07_API키/out/livespd)에서 새벽 1~4시 값의 97~100% 가 같은 숫자.
#         실측이 없을 때 내는 고정 숫자(채움 값)로 본다: 같은 때 카카오 한 번 맞춰 보기 — 뚝섬로 ITS 11 ↔ 시속 71 · 강남대로 13 ↔ 44 · 동부간선도로 33 ↔ 61(값은 저장하지 않음).
#   규칙: 최근 DAYS 일(기본 14) 기록에서 링크마다 새벽 1~4시 값 가운데 가장 많은 숫자 F 의 몫이 90% 넘고(새벽 표본 40 넘게 · 닷새 넘게)
#         F 가 그 링크 제한속도의 60% 아래면 「채움 값」 — 새벽에 제한의 60% 아래로 내내 같은 속도일 수는 없다.
#         F 가 제한의 60% 넘는 굳은 값은 그대로 둔다(길 고르기를 그르치지 않는다).
#   쓰는 곳: tools/signal/livespd-bake.py 가 data/live-spd-*.json 을 쓸 때 값이 F 와 같은 링크를 뺀다(「값 없음」 — 가르고는 이웃 줄·등급 평균으로 메운다) · 낮에 F 와 다른 값이 오면 그대로 싣는다.
#         쌓아 두는 원자료(out/livespd)는 그대로 둔다(이 도구가 다시 읽는다).
#   py -3.12 -X utf8 tools/signal/livefiller-bake.py [일수]      (data-check 이레마다 · 1분 안쪽)
import gzip, json, glob, os, sys, collections, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT)
AD = os.path.join(KB, '07_API키', 'out', 'livespd')
NIGHT = (1, 2, 3, 4); SHARE = 0.9; MINN = 40; MIND = 5; LOW = 0.6


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 14
    fs = sorted(glob.glob(os.path.join(AD, '2[0-9][0-9][0-9][01][0-9][0-3][0-9].jsonl.gz')))[-days:]
    if len(fs) < MIND:
        print('기록이 닷새가 안 된다', len(fs)); return 1
    cnt = collections.defaultdict(collections.Counter); dd = collections.defaultdict(set); n = 0
    for f in fs:
        day = os.path.basename(f)[:8]
        try:
            for ln in gzip.open(f, 'rt', encoding='utf-8'):
                try:
                    j = json.loads(ln)
                except Exception:
                    continue
                if dt.datetime.fromtimestamp(j['at']).hour not in NIGHT:
                    continue
                n += 1
                for k, v in (j.get('m') or {}).items():
                    cnt[k][v] += 1; dd[k].add(day)
        except Exception as e:   # 오늘 파일이 쓰이는 중이면 끝줄이 잘려 있을 수 있다
            print('읽다 멈춤', day, type(e).__name__)
    nav = {}
    for nm in ('nav-six.json', 'nav-seoul.json', 'nav-seocho.json'):
        p = os.path.join(ROOT, 'data', nm)
        if os.path.exists(p):
            for x in json.load(open(p, encoding='utf-8'))['links']:
                nav.setdefault(str(x[0]), x)
    m = {}; km = 0; nolim = 0; by = collections.Counter()
    for k, c in cnt.items():
        tot = sum(c.values())
        if tot < MINN or len(dd[k]) < MIND:
            continue
        F, mc = c.most_common(1)[0]
        if mc / tot < SHARE:
            continue
        x = nav.get(k); lim = x[4] if x else 0
        if not lim:
            nolim += 1; continue
        if F < lim * LOW:
            m[k] = F; km += x[3]; by[x[7] or '(이름 없음)'] += x[3]
    if not m and n < 100:
        print('새벽 기록이 너무 적다', n); return 1
    doc = {'schema': 'tg-live-filler/1', 'made': dt.date.today().isoformat(), 'days': [os.path.basename(fs[0])[:8], os.path.basename(fs[-1])[:8]],
           'source': '국가교통정보센터(ITS) 실시간 소통정보 trafficInfo 를 이 PC 가 약 11분마다 받아 쌓은 기록(저장소 밖)에서 셈',
           'rule': '새벽 1~4시 값 가운데 가장 많은 숫자 F 의 몫 90% 넘음(표본 40 넘게 · 닷새 넘게) + F 가 제한속도의 60% 아래 → 실측이 없을 때 내는 고정 숫자(채움 값)로 본다',
           'note': ['값이 F 와 같을 때만 「값 없음」으로 친다 — 낮에 다른 값이 오면 그대로 쓴다', '판정은 어림이다(ITS 문서에 채움 값 설명은 못 찾음 · 미확인) — 같은 때 카카오 한 번 맞춰 보기 세 곳에서 실제 흐름은 2~6배 빨랐다',
                    '큰길: ' + ' · '.join('%s %.1fkm' % (a, b / 1000) for a, b in by.most_common(6))],
           'fields': 'm{ITS 링크 ID: 채움 값 km/h} · n 링크 수 · km 길이 합',
           'n': len(m), 'km': round(km / 1000, 1), 'm': dict(sorted(m.items()))}
    p = os.path.join(ROOT, 'data', 'live-spd-filler.json'); tmp = p + '.tmp'
    json.dump(doc, open(tmp, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':')); os.replace(tmp, p)
    print('기록 %s~%s · 새벽 받은 횟수 %d · 본 링크 %d · 채움 값 %d줄 %.1fkm · 제한속도 모름 %d · %s' % (doc['days'][0], doc['days'][1], n, len(cnt), len(m), km / 1000, nolim, doc['note'][2]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
