# -*- coding: utf-8 -*-
# 「등기소의 설치와 관할구역에 관한 규칙」 [별표] 등기소의 명칭 및 관할구역표(대법원규칙 · 국가법령정보 DRF 원문 XML 의 고정폭 표) → [(지방법원, 지원, 등기소, 시도, 관할 원문)]
#   juris-bake.py 가 불러 쓴다 · 원문 XML = 07_API키/out/law_reg/reg_<MST>.xml(시행일은 파일의 <시행일자>)
import re, os, glob
def rows(path=None):
    if not path:
        d = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), '07_API키', 'out', 'law_reg'); path = sorted(glob.glob(os.path.join(d, 'reg_*.xml')))[-1]
    t = open(path, encoding='utf-8').read()
    body = re.search(r'<별표내용>(.*?)</별표내용>', t, re.S).group(1)
    lines = [l for l in re.findall(r'<!\[CDATA\[(.*?)\]\]>', body, re.S) if l.strip()]
    out = []; cur = None; court = branch = sido = ''; last_nm = ''
    def flush():
        nonlocal cur, sido, last_nm
        if cur and (cur[2] or cur[4]):
            sd = cur[3].replace(' ', '')
            if sd and sd not in ('〃', '"', '”'): sido = sd
            nm = cur[2] if cur[2] not in ('〃', '"', '”', '') else last_nm
            last_nm = nm; cur[3] = sido; cur[2] = nm
            out.append(tuple(re.sub(r'\s+', ' ', x).strip() for x in cur))
        cur = None
    for l in lines:
        if '│' not in l or '─' in l or '━' in l:
            if '─' in l or '━' in l: flush()
            continue
        c = [x.strip() for x in l.strip().strip('┃').split('│')]
        if len(c) != 5 or c[0] == '지방법원' or c[0].startswith('명칭'): continue
        if cur is None:
            cur = ['', '', '', '', '']; first = True
        else: first = False
        if c[0]: court = (court + c[0]) if not first and cur[0] else c[0]; branch = '' if first else branch
        if c[1]: branch = (branch + c[1]) if not first else c[1]
        cur[0], cur[1] = court, branch
        cur[2] += c[2].replace(' ', ''); cur[3] += c[3]; cur[4] += c[4]
    flush()
    ef = re.search(r'<시행일자>(\d+)', t); pm = re.search(r'<공포번호>(\d+)', t)
    return out, (ef.group(1) if ef else ''), (pm.group(1) if pm else '')
if __name__ == '__main__':
    R, ef, pm = rows(); print(len(R), '시행', ef, '공포번호', pm)
    for r in R: print(r)
