# -*- coding: utf-8 -*-
# 전국 CCTV 표준데이터 → 시·도마다 한 장 (2026-10-23 · 레시피 「학교 둘레」의 보호구역 CCTV 칸이 서초구 원자료에서 비어 있어 · 소유자 「권고대로」)
#   원자료 = 행정안전부 「전국CCTV표준데이터」(공공데이터포털 15013094 · 실제 파일은 LOCALDATA file.localdata.go.kr/file/cctv_info/info — 받는 법: memory localdata-referer · cp949 · WGS84 위경도)
#   받기(한 줄씩): curl -A Mozilla/5.0 -e https://www.data.go.kr/data/15013094/standard.do -c jar https://file.localdata.go.kr/file/cctv_info/info
#                  curl -b jar -A Mozilla/5.0 -e https://file.localdata.go.kr/file/cctv_info/info -o x.csv https://file.localdata.go.kr/file/download/cctv_info/info   → 07_API키/out/dg/15013094/x.csv
#   광주·전남 = 전남광주통합특별시 12(학교·관할 파일과 같은 코드)
#   싣는 것 = 자리·설치목적·카메라 대수·설치연월·관리기관 이름(시군구청) — 관리번호·전화·주소 글은 싣지 않는다
# 쓰기: py -3.12 -X utf8 tools/region/cctvstd-bake.py   →  data/cctv-std/<시도 2자리>.json + index.json
import csv, io, json, os, datetime, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', '15013094', 'x.csv')
OUT = os.path.join(ROOT, 'data', 'cctv-std')
SIDO = {'서울': '11', '부산': '26', '대구': '27', '인천': '28', '광주': '12', '대전': '30', '울산': '31', '세종': '36', '경기': '41', '강원': '51', '충청북': '43', '충북': '43', '충청남': '44', '충남': '44', '전북': '52', '전라북': '52', '전라남': '12', '전남': '12', '경상북': '47', '경북': '47', '경상남': '48', '경남': '48', '제주': '50'}


def sido_of(addr, org):
    s = (addr or org or '').strip()
    for k, v in SIDO.items():
        if s.startswith(k):
            return v
    return None


def main():
    b = open(SRC, 'rb').read()
    try:
        t = b.decode('utf-8-sig')
    except UnicodeDecodeError:
        t = b.decode('cp949')
    rd = csv.reader(io.StringIO(t)); h = next(rd); I = {c: i for i, c in enumerate(h)}
    PUR = []; P = {}
    by = collections.defaultdict(list); bad = 0; base = ''
    for r in rd:
        try:
            la, lo = float(r[I['WGS84위도']]), float(r[I['WGS84경도']])
        except (ValueError, IndexError):
            bad += 1; continue
        if not (33 < la < 39 and 124 < lo < 132):
            bad += 1; continue
        sd = sido_of(r[I['소재지도로명주소']] or r[I['소재지지번주소']], r[I['관리기관명']])
        if not sd:
            bad += 1; continue
        pu = r[I['설치목적구분']].strip() or '기타'
        if pu not in P:
            P[pu] = len(PUR); PUR.append(pu)
        try:
            n = int(r[I['카메라대수']] or 0)
        except ValueError:
            n = None
        ym = (r[I['설치연월']] or '').strip()[:6] or None
        base = max(base, r[I['데이터기준일자']] or '')
        by[sd].append([round(lo, 5), round(la, 5), P[pu], n, ym, r[I['관리기관명']].strip()])
    os.makedirs(OUT, exist_ok=True)
    made = datetime.date.today().isoformat(); idx = {}
    for sd, rows in sorted(by.items()):
        orgs = sorted(set(x[5] for x in rows)); oi = {o: i for i, o in enumerate(orgs)}
        items = [x[:5] + [oi[x[5]]] for x in rows]
        cnt = collections.Counter(PUR[x[2]] for x in rows)
        doc = {'schema': 'tg-cctv-std/1', 'made': made, 'sido': sd, 'base': base,
               'source': '행정안전부 전국CCTV표준데이터(공공데이터포털 15013094 · LOCALDATA cctv_info · 데이터 기준 %s) — 전국 자치단체가 관리하는 실외 공공 CCTV' % base,
               'fields': 'purposes[설치목적…] · orgs[관리기관…] · items[[경도, 위도, 설치목적 차례, 카메라 대수|null, 설치연월 YYYYMM|null, 관리기관 차례]]',
               'note': ['자치단체가 표준데이터로 낸 것만 — 경찰 단속카메라·민간 CCTV 는 없다(교통단속 목적은 자치단체 관리분)', '한 줄 = 한 설치 자리(카메라 여러 대일 수 있다 — 대수 칸)', '관리번호·전화·주소 글은 싣지 않았다'],
               'purposes': PUR, 'orgs': orgs, 'count': dict(cnt.most_common()), 'items': items}
        open(os.path.join(OUT, sd + '.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
        idx[sd] = {'자리': len(rows), '카메라': sum(x[3] or 0 for x in rows), '어린이보호': cnt.get('어린이보호', 0)}
    open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8').write(json.dumps({'schema': 'tg-cctv-std-index/1', 'made': made, 'base': base, 'purposes': PUR, 'sido': idx, 'dropped': bad}, ensure_ascii=False, indent=1))
    print('시도', len(by), '· 자리', sum(len(v) for v in by.values()), '· 버림', bad, '· 기준', base)
    for sd, v in idx.items():
        print(' ', sd, v)


if __name__ == '__main__':
    main()
