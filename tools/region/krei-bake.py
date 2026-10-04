# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.0.0 — 💰 손익 계산의 업종 기본값: 「2025 외식업체 경영실태 조사 통계보고서」(농림축산식품부·한국농촌경제연구원 · C2025-46 · 2025-12 · 공공누리 출처표시)
#   PDF = 농식품부 누리집 https://www.mafra.go.kr/bbs/home/798/577154/artclView.do 첨부(통계보고서 · 323쪽)
#   표마다 줄 = 「구분 · 사례수 · 구간별 비율 … · 평균」 → 업종 18 + 한식 세분류 4 + 업종 중분류 + 지역(서울권·수도권) + 운영형태 줄의 숫자를 그대로 옮긴다(계산 없음)
#   py -3.12 -X utf8 tools/region/krei-bake.py <통계보고서.pdf>   (pypdf 필요)  →  data/biz-krei.json
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PDF = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/knpth/regionwork/krei_595247.pdf'
WANT = {12: 'area', 18: 'lease_cond', 19: 'deposit', 20: 'rent', 21: 'fee', 22: 'premium', 24: 'hours', 25: 'days', 26: 'holiday', 28: 'tables', 29: 'seats', 30: 'optype',
        31: 'invest', 32: 'interior', 33: 'kitchen', 48: 'dlvapp', 51: 'dlvapp_cost', 53: 'dlvagent', 54: 'dlvagent_cost', 58: 'channel', 60: 'cust', 61: 'cust_dlv', 62: 'cust_to',
        63: 'cust_age', 64: 'cust_sex', 65: 'cust_src', 66: 'dow', 67: 'price', 95: 'sales', 96: 'opex', 97: 'food', 98: 'wage', 99: 'rentcost', 100: 'tax', 101: 'family', 102: 'owner',
        103: 'other', 104: 'profit', 115: 'workers', 119: 'work_hours', 123: 'work_days', 130: 'empins', 133: 'pain_food', 134: 'pain_rent', 135: 'pain_wage', 136: 'pain_comp',
        141: 'switch', 163: 'yoy'}
LABELS = ['전체', '일반음식점', '일반음식점 외', '일반음식점업', '기관 구내식다업', '출장 및 이동 음식업', '기타 음식점업', '주점업', '비알콜 음료점업', '한식', '중식 음식점업', '일식 음식점업', '서양식 음식점업',
          '기타 외국식 음식점업', '기관 구내식당업', '출장·이동음식점업', '제과', '피자·햄버거·샌드위치 및 유사음식점업', '치킨 전문점', '김밥 및 기타 간이음식점업', '간이 음식 포장 판매 전문점',
          '일반 유흥주점업', '무도 유흥주점업', '생맥주 전문점', '기타 주점업', '커피 전문점', '기타 비알코올 음료점업', '한식 일반음식점업', '한식 면 요리 전문점', '한식 육류 요리 전문점',
          '한식 해산물 요리 전문점', '서울권', '수도권', '충청권', '호남권', '경남권', '경북권', '프랜차이즈', '비프랜차이즈']
NUM = r'-?[\d,]+(?:\.\d+)?|-'
ROW = re.compile(r'^(.*?)\s+((?:(?:' + NUM + r')\s+)*(?:' + NUM + r'))\s*$')
nz = lambda s: re.sub(r'\s+', '', s)
LN = sorted(((nz(l), l) for l in LABELS), key=lambda x: -len(x[0]))

def main():
    from pypdf import PdfReader
    P = [(p.extract_text() or '') for p in PdfReader(PDF).pages]
    body = P[14:]
    out = {'schema': 'tg-krei/1', 'source': '농림축산식품부·한국농촌경제연구원 「2025 외식업체 경영실태 조사 통계보고서」(2025-12 · 공공누리 출처표시) — 표 번호는 보고서 그대로',
           'note': '표본 조사(전국 3,138곳)의 평균이다. 업종 표본이 작은 줄(유흥주점 35~41곳 등)은 흔들림이 크다. 금액은 대개 만 원 · 매출·비용은 연간.', 'tables': {}}
    for n, key in WANT.items():
        tag = '<표 %d>' % n; pages = [i for i, p in enumerate(body) if tag in p]
        if not pages: print('없음', n); continue
        txt = '\n'.join(body[i] for i in pages)
        m = re.search(re.escape(tag) + r'\s*([^\n]+)', txt); title = m.group(1).strip() if m else ''
        u = re.search(r'\(단위:\s*([^)]+)\)', txt); unit = u.group(1).strip() if u else ''
        hdr = txt[txt.find('구분'):txt.find('■ 전체')] if '■ 전체' in txt else ''
        rows, buf = {}, ''
        for line in txt.split('\n'):
            line = line.replace('■', '').strip()
            if not line or line.startswith('2025 외식업체') or line.startswith('<표') or line.startswith('(단위'): buf = ''; continue
            mm = ROW.match(line)
            if not mm or not re.search(r'[가-힣A-Za-z]', mm.group(1) + buf): buf = (buf + ' ' + line) if len(buf) < 60 else line; continue
            lab = nz(buf + ' ' + mm.group(1)); buf = ''
            hit = next((orig for k, orig in LN if lab.endswith(k)), None)
            if not hit or hit in rows: continue
            rows[hit] = [None if x == '-' else float(x.replace(',', '')) for x in mm.group(2).split()]
        out['tables'][key] = {'no': n, 'title': title, 'unit': unit, 'header': re.sub(r'\s+', ' ', hdr).strip()[:400], 'rows': rows}
        print(n, key, title, unit, len(rows))
    fn = os.path.join(ROOT, 'data', 'biz-krei.json')
    json.dump(out, open(fn, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('bytes', os.path.getsize(fn))

if __name__ == '__main__':
    main()
