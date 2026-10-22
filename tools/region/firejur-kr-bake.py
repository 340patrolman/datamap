# -*- coding: utf-8 -*-
# 전국 119안전센터 법정 관할구역 — 시·도 「행정기구 설치 조례 시행규칙」 별표(2026-10-22 · 서울은 firejur-bake.py)
#   받기: py -3.12 -X utf8 tools/region/firejur-kr-bake.py fetch   → 국가법령정보 DRF target=ordin 로 시·도마다 「안전센터」 별표를 찾아 hwp/hwpx 를 07_API키/out/fire_jur/<시도>_0.* 로
#   굽기: py -3.12 -X utf8 tools/region/firejur-kr-bake.py         → data/fire-jur/<시도 2자리>.json + index.json
#   관할 글은 원문 그대로(c 넷째 칸) · 행정동(읍·면·동)으로 읽은 것(d)은 따로 — 글 안의 시·군·구 이름을 따라가며 그 안의 읍·면·동 이름을 맞대고,
#   괄호 안에 번지·리(里)가 적힌 곳은 「일부」 · 법정동으로만 적힌 곳은 data/b2a.json(서울·경기)으로 · 못 읽은 이름은 miss
import json, os, re, sys, glob, time, zipfile, datetime, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
SRC = os.path.join(KB, '07_API키', 'out', 'fire_jur')
HJD = os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson')
OUT = os.path.join(ROOT, 'data', 'fire-jur')
SIDO = {'부산광역시': '26', '대구광역시': '27', '인천광역시': '28', '광주광역시': '29', '대전광역시': '30', '울산광역시': '31', '세종특별자치시': '36', '경기도': '41',
        '강원특별자치도': '51', '충청북도': '43', '충청남도': '44', '전북특별자치도': '52', '전라남도': '46', '경상북도': '47', '경상남도': '48', '제주특별자치도': '50'}
DOT = 'ㆍ·・∙․‧'


def norm(s):
    s = re.sub(r'\s+', '', s)
    for c in DOT:
        s = s.replace(c, '·')
    return s.replace('∼', '~').replace('～', '~').replace('〜', '~')


def hwp_paras(path):
    import olefile, zlib, struct
    ole = olefile.OleFileIO(path)
    comp = bool(struct.unpack('<I', ole.openstream('FileHeader').read()[36:40])[0] & 1)
    secs = sorted([s for s in ole.listdir() if s[0] == 'BodyText'], key=lambda s: int(s[1][7:]))
    out = []
    for s in secs:
        d = ole.openstream(s).read()
        if comp:
            d = zlib.decompress(d, -15)
        i = 0
        while i < len(d):
            h = struct.unpack('<I', d[i:i + 4])[0]; i += 4
            tag, size = h & 0x3FF, (h >> 20) & 0xFFF
            if size == 0xFFF:
                size = struct.unpack('<I', d[i:i + 4])[0]; i += 4
            body = d[i:i + size]; i += size
            if tag != 67:
                continue
            t, j = [], 0
            while j < len(body):
                c = struct.unpack('<H', body[j:j + 2])[0]
                if c < 32:
                    j += 16 if c in (1, 2, 3, 11, 12, 14, 15, 16, 17, 18, 21, 22, 23) else 2
                    if c == 9:
                        t.append(' ')
                    continue
                t.append(chr(c)); j += 2
            out.append(''.join(t))
    return out


def hwpx_paras(path):
    z = zipfile.ZipFile(path); out = []
    for n in sorted(x for x in z.namelist() if re.match(r'Contents/section\d+\.xml', x)):
        x = z.read(n).decode('utf-8')
        for p in re.findall(r'<hp:p[ >].*?</hp:p>', x, re.S):
            out.append(re.sub(r'<[^>]+>', '', ''.join(re.findall(r'<hp:t>(.*?)</hp:t>', p, re.S))))
    return out


def fetch():
    oc = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8'))['law_oc']
    got = {}
    for sd in SIDO:
        cand = []
        for q in [sd + ' 행정기구 설치 조례 시행규칙', sd + ' 행정기구 설치 조례', sd + ' 행정기구 및 정원 조례 시행규칙']:
            u = 'http://www.law.go.kr/DRF/lawSearch.do?' + urllib.parse.urlencode({'OC': oc, 'target': 'ordin', 'type': 'XML', 'query': q, 'display': 50})
            x = urllib.request.urlopen(u, timeout=30).read().decode('utf-8')
            for blk in re.findall(r'<law id.*?</law>', x, re.S):
                g = lambda t: (re.search(r'<' + t + r'>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</' + t + '>', blk, re.S) or [None, ''])[1]
                if g('지자체기관명') == sd and '행정기구' in g('자치법규명'):
                    cand.append((g('자치법규일련번호'), g('자치법규명'), g('시행일자'), sd))
        for mst, nm, ef, _ in dict.fromkeys(cand):
            u = 'http://www.law.go.kr/DRF/lawService.do?' + urllib.parse.urlencode({'OC': oc, 'target': 'ordin', 'MST': mst, 'type': 'XML'})
            x = urllib.request.urlopen(u, timeout=60).read().decode('utf-8')
            for b in re.findall(r'<별표단위.*?</별표단위>', x, re.S):
                t = re.search(r'<별표제목><!\[CDATA\[(.*?)\]\]>', b); f = re.search(r'<별표첨부파일명><!\[CDATA\[(.*?)\]\]>', b)
                if t and '안전센터' in t.group(1) and f and sd not in got:
                    bb = urllib.request.urlopen(f.group(1), timeout=60).read()
                    ext = 'hwp' if bb[:4] == b'\xd0\xcf\x11\xe0' else 'hwpx' if bb[:2] == b'PK' else 'pdf' if bb[:4] == b'%PDF' else 'bin'
                    fn = os.path.join(SRC, sd + '_0.' + ext)
                    open(fn, 'wb').write(bb)
                    got[sd] = {'mst': mst, 'law': nm, 'ef': ef, 'title': t.group(1), 'file': os.path.basename(fn)}
            time.sleep(0.3)
        print(sd, got.get(sd, {}).get('title', '못 찾음'))
    json.dump(got, open(os.path.join(SRC, 'sido_got.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def expand(name):
    n = norm(name)
    m = re.match(r'^(.+?)(\d+)~(\d+)(동|가|리)$', n)
    if m:
        return ['%s%d%s' % (m.group(1), k, m.group(4)) for k in range(int(m.group(2)), int(m.group(3)) + 1)]
    m = re.match(r'^([^\d·]+?)(제?\d+|본)((?:·(?:제?\d+|본)(?:동)?)+)(동|가)$', n)
    if m:
        parts = [m.group(2)] + [p.replace('동', '') for p in m.group(3).split('·') if p]
        return ['%s%s%s' % (m.group(1), p, m.group(4)) for p in parts]
    return [n]


def main():
    G = json.load(open(HJD, encoding='utf-8'))['features']
    ADM, SGN = {}, {}
    for f in G:
        p = f['properties']
        ADM.setdefault(p['sgg'], {})[norm(p['adm_nm'].split(' ')[-1])] = p['adm_cd2'][:8]
        nm = norm(p['sggnm'])
        SGN.setdefault(p['sido'], {}).setdefault(nm, set()).add(p['sgg'])
        m = re.match(r'^(.+?[시군])(.+?구)$', nm)
        if m:
            SGN[p['sido']].setdefault(m.group(1), set()).add(p['sgg'])
            SGN[p['sido']].setdefault(m.group(2), set()).add(p['sgg'])
    B = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a']
    BL = {}
    for k, v in B.items():
        BL.setdefault(v['gu'], {})[norm(v['n'])] = v['a']
    got = json.load(open(os.path.join(SRC, 'sido_got.json'), encoding='utf-8')) if os.path.exists(os.path.join(SRC, 'sido_got.json')) else {}
    os.makedirs(OUT, exist_ok=True)
    idx = {}
    for sd, code in SIDO.items():
        fs = glob.glob(os.path.join(SRC, sd + '_0.hwp')) + glob.glob(os.path.join(SRC, sd + '_0.hwpx'))
        if not fs:
            idx[code] = {'n': sd, '없음': '별표를 못 찾음(조례에 「안전센터」 별표가 없거나 이름이 다름)'}
            continue
        P = hwp_paras(fs[0]) if fs[0].endswith('.hwp') else hwpx_paras(fs[0])
        P = [p.strip() for p in P]
        names = SGN.get(code, {})
        starts = []
        for i, p in enumerate(P):
            q = norm(p)
            if ('안전센터' in q or '지역대' in q) and not re.search(r'명칭|관할구역|위치|직급|비고|통할|운영한다', q) and len(q) <= 24:
                starts.append(i)
        recs = []
        for k, s in enumerate(starts):
            q = norm(P[s])
            nm = q
            if re.match(r'^(119)?(안전센터|지역대)$', q) and s > 0:
                nm = norm(P[s - 1]) + q
            e = starts[k + 1] if k + 1 < len(starts) else len(P)
            body = P[s + 1:e]
            if k + 1 < len(starts) and re.match(r'^(119)?(안전센터|지역대)$', norm(P[e])) and body:
                body = body[:-1]   # 다음 센터 이름 줄
            for j, b in enumerate(body):   # 표 다음 칸(구조대·소방정대 줄)부터는 그 센터 글이 아니다
                if re.match(r'^(119)?(특수)?구조대$|^소방정대$|^119구급대$', norm(b)):
                    body = body[:j]; break
            body = [b for b in body if b and not re.match(r'^[가-힣]{1,6}소방서$', norm(b)) and norm(b) not in ('소방서',)]
            # 위치 = 첫 줄부터 「(…동/읍/면/리)」 로 끝나는 줄까지(두 줄까지)
            addr, rest = [], body
            for j in range(min(3, len(body))):
                addr.append(body[j])
                if re.search(r'\)\s*$', body[j]):
                    rest = body[j + 1:]; break
            else:
                addr, rest = body[:1], body[1:]
            recs.append({'n': nm, 'addr': ' '.join(addr), 't': ', '.join(x.rstrip(', ') for x in rest), 'kind': '지역대' if '지역대' in nm else '안전센터'})
        dmap, miss = {}, []
        for ci, r in enumerate(recs):
            am = [g for nmk, gs in names.items() for g in gs if nmk and nmk in norm(r['addr'])]
            ctx = set(am[:1]) if am else set()
            text = norm(r['t'])
            text = re.sub(r'[^,]*?(?:로|길)\d+(?:-\d+)?(?:번길\d+(?:-\d+)?)?(?:\([^)]*\))?', '', text)   # 관할 글에 섞인 센터 주소(○○로 12(○○동))는 빼고 읽는다
            # 「상대·하대·상평동」「금곡·진성면」 → 상대동,하대동,상평동 (숫자 줄임 「조원1·2동」은 expand 가 맡는다)
            text = re.sub(r'((?:[가-힣]+·)+[가-힣]+?)(동|읍|면)', lambda m: ','.join(x if x.endswith(m.group(2)) else x + m.group(2) for x in m.group(1).split('·')[:-1] + [m.group(1).split('·')[-1]]), text)
            pos = 0
            for m in re.finditer(r'([가-힣]+?(?:시|군|구))(?=[가-힣])|([가-힣\d·~]+?(?:동|읍|면|가))(\(([^()]*)\)|중[^,]*)?', text):
                if m.group(1) and m.group(1) in names and not m.group(2):
                    ctx = set(names[m.group(1)]); continue
                if not m.group(2):
                    continue
                tok, par = m.group(2), m.group(3) or ''
                part = 1 if (re.search(r'\d|리|일부|제외|중', par) or '일부' in text[m.end():m.end() + 3]) else 0
                cands = expand(tok)
                for c in cands:
                    hit = []
                    for g in (ctx or set(gg for gs in names.values() for gg in gs)):
                        if c in ADM.get(g, {}):
                            hit.append(('a', g, c))
                        elif c in BL.get(g, {}):
                            hit.append(('b', g, c))
                        elif re.sub(r'제(\d)', r'\1', c) in ADM.get(g, {}):
                            hit.append(('a', g, re.sub(r'제(\d)', r'\1', c)))
                    if not hit:   # 법정동 이름 → 같은 뿌리의 행정동들(동대신동 → 동대신1동·2동 · 중앙동1가 → 중앙동)
                        c2 = re.sub(r'(동)\d+가$', r'\1', c)
                        stem = c2[:-1] if c2.endswith('동') else None
                        for g in (ctx or set()):
                            if c2 in ADM.get(g, {}):
                                hit.append(('a', g, c2)); continue
                            if stem:
                                for an in ADM.get(g, {}):
                                    if re.match('^' + re.escape(stem) + r'제?\d+동$', an):
                                        hit.append(('a', g, an))
                        if hit:
                            for kind, g, x in hit:
                                dmap.setdefault(ADM[g][x], []).append([ci, 100.0, part])
                            continue
                    if len(hit) > 1 and not ctx:
                        hit = []   # 시군구를 모르면 같은 이름이 여럿일 때 안 붙임
                    if not hit:
                        miss.append([r['n'], c]); continue
                    for kind, g, x in hit[:1]:
                        if kind == 'a':
                            dmap.setdefault(ADM[g][x], []).append([ci, 100.0, part])
                        else:
                            for a in BL[g][x]:
                                dmap.setdefault(a[0], []).append([ci, a[2], part])
        D = {}
        for d8, L in dmap.items():
            acc = {}
            for ci, sh, pt in L:
                a = acc.setdefault(ci, [0.0, 0]); a[0] = min(100.0, a[0] + sh); a[1] = max(a[1], pt)
            D[d8] = sorted([[ci, round(v[0], 1), v[1]] for ci, v in acc.items()], key=lambda x: (-x[1], x[0]))
        alld = {c for g in names.values() for gg in g for c in ADM.get(gg, {}).values()}
        g0 = got.get(sd, {})
        doc = {'schema': 'tg-fire-jur/1', 'made': datetime.date.today().isoformat(), 'sido': code, 'n': sd,
               'source': '「%s」 %s(국가법령정보센터 자치법규 MST %s · 시행 %s) · 행정동 = 통계청 SGIS 행정동 경계(vuski/admdongkor 2026-07 · CC BY 4.0)' % (g0.get('law', sd + ' 행정기구 설치 조례 시행규칙'), g0.get('title', ''), g0.get('mst', '?'), g0.get('ef', '?')),
               'fields': 'c[[안전센터·지역대 이름, 위치, 관할구역 글(원문 그대로 · 표 줄을 「, 」로 이음), 갈래(안전센터|지역대)]] · d{행정동 8자리: [[c 차례, 몫 %, 일부 1|0]…]} · miss[[센터, 못 읽은 이름]] · cover',
               'note': ['관할구역 글(c 셋째 칸)이 정본이다 — d 는 글을 기계로 읽은 것이라 틀릴 수 있다(표 모양이 시·도마다 다르다)',
                        '「일부」 = 괄호 안에 번지·리가 적혀 그 읍·면·동의 일부만 맡는 곳 — 어느 쪽인지 지도 점으로는 못 가른다',
                        '지역대는 안전센터에 딸린 작은 대(읍·면) — 같은 동에 안전센터와 지역대가 함께 나올 수 있다'],
               'c': [[r['n'], r['addr'], r['t'], r['kind']] for r in recs], 'd': D, 'miss': miss,
               'cover': {'센터': len(recs), '행정동': len(alld), '읽은 행정동': len(set(D) & alld), '못 읽은 행정동': sorted(alld - set(D))}}
        open(os.path.join(OUT, code + '.json'), 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
        idx[code] = {'n': sd, '센터': len(recs), '행정동': len(alld), '읽은 행정동': len(set(D) & alld), '못 읽은 이름': len(miss)}
        print(sd, idx[code])
    open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8').write(json.dumps({'schema': 'tg-fire-jur-index/1', 'made': datetime.date.today().isoformat(), 'seoul': 'data/fire-jur-seoul.json(별도 도구 firejur-bake.py)', 'sido': idx}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    fetch() if 'fetch' in sys.argv[1:] else main()
