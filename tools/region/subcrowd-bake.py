# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚇 지하철 차 안이 얼마나 붐비나(소유자 2026-10-10 「9호선은 심각한 밀집 혼잡 상태 · 이런 것도 표현이 될까」) → data/subway-crowd.json
#   재료 ① 서울교통공사_지하철혼잡도정보(공공데이터포털 15071311 · 1~8호선 · 30분 단위 · 평일·토·일) = 07_API키/out/dg/15071311/x.csv(tools/region/dgfile.py 15071311)
#        ② 서울특별시_9호선 혼잡도 정보(서울 열린데이터광장 OA-22197 · 공공누리 1유형 · 일반·급행 × 평일·휴일) = 07_API키/out/dg/15112492/line9_2026.xlsx
#            (받는 법: 화면의 파일 번호 seq 로 datafile.seoul.go.kr/bigfile/iot/inf/nio_download.do 에 POST infId=OA-22197&seq=5&infSeq=1 + Referer)
#   값 = 제공기관이 낸 혼잡도(%) 그대로 — 평일만 싣는다. 고치거나 채우지 않는다(0 은 원자료 0 — 운행이 없는 시간·방향)
#   py -3.12 -X utf8 tools/region/subcrowd-bake.py
import csv, json, os, datetime, io
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DG = os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg')
def hm(s):
    s = s.replace('시', ':').replace('분', '').split('~')[0].strip(); h, m = s.split(':'); return '%02d:%02d' % (int(h), int(m))
def pack(nm, line, ud, kind, slots, vals):
    v = [round(float(x or 0)) for x in vals]
    if not any(v): return None
    def mx(a, b):
        c = [(v[i], slots[i]) for i in range(len(v)) if a <= slots[i] < b]; return max(c) if c else (0, '')
    top = max(range(len(v)), key=lambda i: v[i])
    return [nm, line, ud, kind, v[top], slots[top], mx('07:00', '09:30')[0], mx('18:00', '20:00')[0], v]
def main():
    rows = []; slots1 = slots9 = None
    t = open(os.path.join(DG, '15071311', 'x.csv'), 'rb').read().decode('cp949'); R = list(csv.reader(io.StringIO(t))); slots1 = [hm(x) for x in R[0][5:]]
    for r in R[1:]:
        if r[0] != '평일': continue
        p = pack(r[3].strip(), r[1].strip(), {'상선': 'U', '하선': 'D', '내선': 'I', '외선': 'O'}.get(r[4].strip(), r[4].strip()), '', slots1, [x.strip() for x in r[5:]])
        if p: rows.append(p)
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(DG, '15112492', 'line9_2026.xlsx'), read_only=True, data_only=True)
    for ws in wb.worksheets:
        if '평일' not in ws.title: continue
        ud = 'U' if ws.title.startswith('상선') else 'D'; kind = '급행' if '급행' in ws.title else '일반'; hd = None
        for r in ws.iter_rows(values_only=True):
            if r and r[0] == '구분': hd = [hm(str(x)) for x in r[1:] if x]; slots9 = slots9 or hd; continue
            if not hd or not r or not r[0]: continue
            p = pack(str(r[0]).strip(), '9호선', ud, kind, hd, list(r[1:1 + len(hd)]))
            if p: p[8] = p[8] + [0] * (len(slots9) - len(p[8])); rows.append(p)
    line = {}
    for p in rows:
        k = p[1] + (' ' + p[3] if p[3] else ''); e = line.setdefault(k, [0, '', '', '']);
        if p[4] > e[0]: line[k] = [p[4], p[0], p[2], p[5]]
    doc = {'schema': 'tg-subway-crowd/1', 'made': datetime.date.today().isoformat(),
           'source': '서울교통공사_지하철혼잡도정보(공공데이터포털 15071311 · 2026-06-30판 · 1~8호선) · 서울특별시_9호선 혼잡도 정보(서울 열린데이터광장 OA-22197 · 2026년 종합 · 공공누리 1유형 출처표시)',
           'note': ['혼잡도(%) = 제공기관이 낸 값 그대로(열차 정원에 견준 탄 사람 — 100 을 넘으면 정원보다 많이 탄 것) · 30분 단위 평균이라 가장 붐비는 한 대는 이보다 높다',
                    '평일 값만 실었다(원자료에는 토·일·휴일도 있다) · 0 은 원자료 0(그 시간·방향에 운행이 없음)',
                    '방향 U 상선·D 하선·I 내선·O 외선(2호선) — 원자료 표기 그대로 · 역에서 그 방향 열차가 떠날 때의 값',
                    '9호선은 일반·급행이 따로다 — 급행이 서는 역만 급행 줄이 있다',
                    '1~9호선(서울교통공사·9호선)뿐이다 — 경의중앙·수인분당·신분당·공항철도 등 다른 운영사 노선은 이 자료에 없다(한국철도공사 수도권 전철 혼잡도는 2018년 선별 최고값 13줄뿐이라 싣지 않았다)',
                    '역 좌표는 싣지 않았다 — 역 이름 + 노선으로 맞댄다'],
           'fields': 'slots1 1~8호선 시각 눈금 · slots9 9호선 시각 눈금 · stn[[역 이름, 노선, 방향, 일반·급행(9호선만), 하루 가장 높은 %, 그 시각, 출근 07:00~09:30 가장 높은 %, 퇴근 18~20시 가장 높은 %, [눈금마다 %]]] · line{노선: [가장 높은 %, 역, 방향, 시각]}',
           'slots1': slots1, 'slots9': slots9, 'line': line, 'stn': rows}
    p = os.path.join(ROOT, 'data', 'subway-crowd.json')
    json.dump(doc, open(p, 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))
    print('줄', len(rows), '· 바이트', os.path.getsize(p))
    for k, v in sorted(line.items(), key=lambda kv: -kv[1][0]): print('  %-10s %4d%% %s %s %s' % (k, v[0], v[1], v[2], v[3]))
if __name__ == '__main__': main()
