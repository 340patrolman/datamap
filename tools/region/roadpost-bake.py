# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.31.0 — 🔢 도로 번호(코워크 지시 `../코드세션_지시_도로번호위치_20261006.md`)
#   ① 서울 도시고속도로 가로등주 관리번호 = 코워크 07_API키/roadpost_prep.py 정리본(공공데이터포털 15107934 · 2022-11-08 · 이용허락 제한 없음)
#   ② 고속도로 거리표(이정 100m) = 한국도로공사 도로중심선 이정 좌표 2025(data.ex.co.kr · 소유자가 받아 NAS 에 둔 「ETC_도로중심선_1년_1년_2025.zip」 = 실제로는 gzip 한 겹 CSV · cp949)
#      전국 · 도로명 빈 줄·「가/나」 합친 이름 줄은 같은 구간을 한 번 더 적은 것이라 뺀다 · items = [노선 번호(routes 의 자리), km, 위도, 경도]
#   py -3.12 -X utf8 tools/region/roadpost-bake.py [원본 gz/csv]
import csv, gzip, io, json, os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키')
subprocess.run([sys.executable, '-X', 'utf8', os.path.join(KB, 'roadpost_prep.py')], check=True)
j = json.load(open(os.path.join(KB, 'out', 'roadpost', 'prep', 'road-posts.json'), encoding='utf-8'))
for k, v in j['sets'].items(): v.pop('prefixCount', None)
j['sets'].pop('exkm', None)
src = sys.argv[1] if len(sys.argv) > 1 else r'\\NAS-baranno815\home\ETC_도로중심선_1년_1년_2025.zip'
b = open(src, 'rb').read()
if b[:2] == b'\x1f\x8b': b = gzip.decompress(b)
t = None
for e in ('utf-8-sig', 'cp949'):
    try: t = b.decode(e); break
    except UnicodeDecodeError: pass
rd = csv.reader(io.StringIO(t)); hdr = [h.strip() for h in next(rd)]
ir, inm, ik = hdr.index('노선번호'), hdr.index('도로명'), hdr.index('이정'); ila = hdr.index('X좌표값'); ilo = hdr.index('Y좌표값')
routes, RI, items, skip = [], {}, [], 0
for r in rd:
    nm = r[inm].strip()
    if not nm or '/' in nm: skip += 1; continue   # 「논산천안선/호남선」 = 따로 적힌 두 노선과 같은 점
    try: la, lo, km = float(r[ila]), float(r[ilo]), float(r[ik])
    except (ValueError, IndexError): skip += 1; continue
    if la > 100: la, lo = lo, la
    key = r[ir].strip() + '|' + nm
    if key not in RI: RI[key] = len(routes); routes.append([r[ir].strip(), nm])
    items.append([RI[key], round(km, 1), round(la, 6), round(lo, 6)])
j['sets']['exkm'] = {'title': '고속도로 거리표(이정) 100m · 전국', 'source': '한국도로공사 도로중심선 이정 좌표 2025(고속도로 공공데이터 포털 data.ex.co.kr)',
                     'note': '도로 중심선 위 이정점이다. 실제 거리표 기둥은 갓길·중앙분리대에 있어 수 m~수십 m 떨어진다. 상·하행 구분 없음. 도로공사가 관리하지 않는 민자·지자체 고속도로는 없다.',
                     'fields': 'routes = [[노선번호, 도로명]] · items = [routes 자리, km, 위도, 경도]', 'skipped': skip, 'routes': routes, 'items': items}
json.dump(j, open(os.path.join(ROOT, 'data', 'road-posts.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
print('가로등', len(j['sets']['lamp']['items']), '거리표', len(items), '노선', len(routes), '뺌', skip, os.path.getsize(os.path.join(ROOT, 'data', 'road-posts.json')))
