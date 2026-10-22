# -*- coding: utf-8 -*-
# 서울 119안전센터 법정 관할구역 (2026-10-22 소유자 「소방서도 … 모든것은 공공자료임」)
#   원문 = 「서울특별시 행정기구 설치 조례 시행규칙」 [별표 2] 소방서 119안전센터의 명칭ㆍ위치와 관할구역(제59조제2항) ·
#          「서울특별시 행정기구 설치 조례」 [별표1] 소방서의 명칭ㆍ위치 및 관할구역(제37조제2항)
#          국가법령정보 공동활용 DRF target=ordin(MST 2166933 · 2038385) → 별표 hwp(flDownload) → 07_API키/out/fire_jur/{center,station}.hwp
#   관할 글은 원문 그대로 싣고(t), 행정동으로 읽은 것(d)은 따로 둔다 — 법정동으로 적힌 곳은 data/b2a.json 넓이 비율로 행정동에 잇고, 번지로 나눈 곳은 「일부」
# 쓰기: py -3.12 -X utf8 tools/region/firejur-bake.py   →  data/fire-jur-seoul.json
import json, os, re, sys, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT)
SRC = os.path.join(KB, '07_API키', 'out', 'fire_jur')
HJD = os.path.join(KB, '13_관할경계', '원자료', 'hjd20260701.geojson')
OUT = os.path.join(ROOT, 'data', 'fire-jur-seoul.json')
DOT = 'ㆍ·・'


def norm(s):
    s = re.sub(r'\s+', '', s)
    for c in DOT:
        s = s.replace(c, '·')
    return s.replace('∼', '~').replace('～', '~')


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


def expand(name):
    """「반포본ㆍ2ㆍ3동」「방배1∼3동」「명륜동1∼4가」「신문로1ㆍ2가」「일원본동ㆍ1ㆍ2동」 → 이름 목록"""
    n = norm(name)
    m = re.match(r'^(.+?)동(\d+)~(\d+)가$', n)
    if m:
        return ['%s%d가' % (m.group(1), k) for k in range(int(m.group(2)), int(m.group(3)) + 1)] + ['%s동%d가' % (m.group(1), k) for k in range(int(m.group(2)), int(m.group(3)) + 1)]
    m = re.match(r'^(.+?)(\d+)~(\d+)(동|가)$', n)
    if m:
        return ['%s%d%s' % (m.group(1), k, m.group(4)) for k in range(int(m.group(2)), int(m.group(3)) + 1)]
    m = re.match(r'^([^\d·]+?)(본동|본|\d+)((?:·(?:본|\d+)(?:동)?)+)(동|가)?$', n)
    if m:
        base, first, rest, suf = m.group(1), m.group(2), m.group(3), m.group(4) or '동'
        parts = [first.replace('동', '')] + [p.replace('동', '') for p in rest.split('·') if p]
        return ['%s%s%s' % (base, p, suf) for p in parts]
    return [n]


def split_top(s):
    out, dep, cur = [], 0, ''
    for c in s:
        if c in '([':
            dep += 1
        elif c in ')]':
            dep -= 1
        if c == ',' and dep == 0:
            out.append(cur); cur = ''
        else:
            cur += c
    if cur.strip():
        out.append(cur)
    return [x.strip() for x in out if x.strip()]


def main():
    P = [p.strip() for p in hwp_paras(os.path.join(SRC, 'center.hwp'))]
    recs, st, i = [], None, 0
    pend = ''
    while i < len(P):
        p = P[i]
        q = norm(p)
        if q.endswith('소방서') and '119' not in q and len(q) <= 8:
            st = (norm(pend) + q) if not q[:-3] else q
            pend = ''; i += 1; continue
        if q == '소방서' and pend:
            st = norm(pend) + '소방서'; pend = ''; i += 1; continue
        if not q.startswith('비고') and '관할구역' not in q and '119' in q and ('안전센터' in q or (i + 1 < len(P) and norm(P[i + 1]) == '안전센터')):
            nm = q if '안전센터' in q else q + '안전센터'
            if nm == '119안전센터' and i > 0:
                nm = norm(P[i - 1]) + nm
            if '안전센터' not in q:
                i += 1
            addr = P[i + 1].strip(); j = i + 2; jur = []
            while j < len(P):
                r = norm(P[j])
                if ('119' in r and ('안전센터' in r or (j + 1 < len(P) and norm(P[j + 1]) == '안전센터'))) or (r.endswith('소방서') and len(r) <= 8) or r.startswith('비고') or (j + 1 < len(P) and norm(P[j + 1]) == '119안전센터'):
                    break
                if r and not (len(r) <= 4 and j + 1 < len(P) and norm(P[j + 1]) == '소방서'):
                    jur.append(P[j].strip())
                elif r:
                    pend = r
                j += 1
            recs.append({'st': st, 'n': nm.replace('119안전센터', '') + '119안전센터', 'addr': addr, 't': ', '.join(x.rstrip(', ') for x in jur)})
            i = j; continue
        if q and len(q) <= 4 and i + 1 < len(P) and norm(P[i + 1]) == '소방서':
            pend = q
        i += 1
    note = [p for p in P if norm(p).startswith('비고')]
    # 행정동 이름 · 법정동 → 행정동
    G = json.load(open(HJD, encoding='utf-8'))['features']
    GU, ADM = {}, {}
    for f in G:
        pr = f['properties']
        if pr['sido'] != '11':
            continue
        GU[pr['sggnm']] = pr['sgg']
        ADM.setdefault(pr['sgg'], {})[norm(pr['adm_nm'].split(' ')[-1])] = pr['adm_cd2'][:8]
    B = json.load(open(os.path.join(ROOT, 'data', 'b2a.json'), encoding='utf-8'))['b2a']
    BL = {}
    for k, v in B.items():
        BL.setdefault(v['gu'], {})[norm(v['n'])] = v['a']
    dmap, miss = {}, []
    for ci, r in enumerate(recs):
        m = re.search(r'(\S+?구)\s*중\s*:\s*(.*)$', r['t'].replace('[(', '['))
        if not m:
            miss.append((r['n'], r['t'][:40])); continue
        gu = GU.get(m.group(1).strip())
        r['gu'] = gu
        toks, prev = [], ''
        for tok in split_top(m.group(2)):   # 「쌍문1,3,4동」 → 쌍문1동 · 쌍문3동 · 쌍문4동
            tk = norm(tok).replace('일부', '')
            tk += ']' * max(0, tk.count('[') - tk.count(']')) + ')' * max(0, tk.count('(') - tk.count(')'))   # 원문에서 닫는 괄호가 빠진 곳(반포동[ …)
            if re.match(r'^\d+(?:·\d+)*동?$', tk) and prev:
                tk = prev + tk + ('' if tk.endswith('동') else '동')
            else:
                pm = re.match(r'^([^\d\[(]+?)\d', tk)
                prev = pm.group(1) if pm else ''
            toks.append(tk)
        for i0, tok in enumerate(toks):
            if re.match(r'^[^\d\[(]+\d+$', tok) and i0 + 1 < len(toks) and toks[i0 + 1].endswith('동'):
                toks[i0] = tok + '동'
        def parse_tok(tok):
            """한 토막 → [[이름, 일부]…] · 괄호 안에 괄호가 있으면(반포동[…, 방배동(방배본동ㆍ4동)]) 다시 읽는다"""
            mm = re.match(r'^(.*?)\s*[\(\[](.*)[\)\]]\s*$', tok)
            head, par = (mm.group(1), mm.group(2)) if mm else (tok, '')
            hn = norm(head)
            if not par:
                return [[x, 0] for x in expand(head)]
            pn = norm(par)
            if re.match(r'^[\d,~산·\s]+', pn) and not re.match(r'^\D', pn) or pn.startswith(hn + '중') or pn.startswith(hn.replace('동', '') + '동중'):
                return [[hn, 1]]   # 괄호 = 그 동의 번지(제외·포함) — 동 일부
            items = []
            for it in split_top(par):
                itn = norm(it)
                mi = re.match(r'^([^\d(:중]*?(?:\d+(?:·\d+|~\d+)*)?(?:본동|본|동|가)(?:·(?:본|\d+)(?:동)?)*)(.*)$', itn)
                if not mi or not re.search(r'[가-힣]', mi.group(1)):
                    return [[hn, 1]]
                nm0, rest = mi.group(1), mi.group(2)
                if rest.startswith(('(', '[')) and not re.match(r'^[\(\[][\d,~산·\s]', rest):
                    items += parse_tok(itn)
                    continue
                pt = 1 if re.search(r'\d', rest) else 0
                items += [[x, pt] for x in expand(nm0)]
            return items

        for tok in toks:
            names = parse_tok(tok)
            seen = set()
            for nm, part in names:
                nm = re.sub(r'중$', '', nm)
                alts = [nm, re.sub(r'(\D)(\d+가)$', r'\1동\2', nm), re.sub(r'동(\d+가)$', r'\1', nm), re.sub(r'동$', '', nm)]
                hit = None
                for x in alts:
                    if x in ADM.get(gu, {}):
                        hit = ('a', x); break
                    if x in BL.get(gu, {}):
                        hit = ('b', x); break
                if not hit:
                    base = re.sub(r'(?:제)?\d+(?:~\d+)?동$', '동', nm)   # 옛 행정동 이름(신당1동) → 법정동(신당동) 일부
                    if base != nm and base in ADM.get(gu, {}):
                        hit, part = ('a', base), 1
                    elif base != nm and base in BL.get(gu, {}):
                        hit, part = ('b', base), 1
                if not hit:
                    if re.search(r'[가-힣]', nm) and nm.endswith(('동', '가')):
                        miss.append((r['n'], nm))
                    continue
                if hit in seen:
                    continue
                seen.add(hit)
                if hit[0] == 'a':
                    dmap.setdefault(ADM[gu][hit[1]], []).append([ci, 100.0, int(part)])
                else:
                    for a in BL[gu][hit[1]]:
                        dmap.setdefault(a[0], []).append([ci, a[2], int(part)])
    # 같은 센터가 한 동에 여러 번 = 합침 · 동마다 센터 몫 큰 순
    D = {}
    for d8, L in dmap.items():
        acc = {}
        for ci, sh, pt in L:
            a = acc.setdefault(ci, [0.0, 0])
            a[0] = min(100.0, a[0] + sh); a[1] = max(a[1], pt)
        D[d8] = sorted([[ci, round(v[0], 1), v[1]] for ci, v in acc.items()], key=lambda x: -x[1])
    alld = {c for g in ADM.values() for c in g.values()}
    doc = {
        'schema': 'tg-fire-jur-seoul/1', 'made': datetime.date.today().isoformat(),
        'source': '「서울특별시 행정기구 설치 조례 시행규칙」 [별표 2] 소방서 119안전센터의 명칭ㆍ위치와 관할구역(제59조제2항 관련 · 개정 2022.11.30 · 국가법령정보센터 자치법규 MST 2166933 · 시행 2026-09-11 판) · 행정동 = 통계청 SGIS 행정동 경계(vuski/admdongkor 2026-07 · CC BY 4.0) · 법정동 → 행정동 = data/b2a.json(브이월드 법정동 경계 넓이 비율)',
        'fields': 'c[[소방서, 119안전센터 이름, 위치, 관할구역 글(원문 그대로), 시군구 코드]] · d{행정동 8자리: [[c 차례, 그 행정동에 든 몫 %(법정동으로 적힌 곳은 넓이 비율 · 행정동으로 적힌 곳은 100), 일부 1(번지로 나눔 — 그 동 일부만)]…](몫 큰 순)} · miss[[센터, 행정동·법정동으로 못 읽은 이름]]',
        'note': ['관할구역 글(c 넷째 칸)이 정본이다 — d 는 그 글을 행정동으로 읽은 것이고, 번지로 나눈 곳(일부 1)은 어느 쪽인지 지도 점으로는 못 가른다',
                 '법정동으로 적힌 곳은 법정동 → 행정동 넓이 비율로 이었다 — 사람 수 비율이 아니다',
                 '소방서 관할(조례 [별표1])은 「○○구 일원」 — 구마다 한 소방서(서초소방서 = 서초구)'] + note,
        'c': [[r['st'], r['n'], r['addr'], r['t'], r.get('gu')] for r in recs],
        'd': D, 'miss': miss,
        'cover': {'센터': len(recs), '서울 행정동': len(alld), '읽은 행정동': len(set(D) & alld), '못 읽은 행정동': sorted(alld - set(D))}}
    open(OUT, 'w', encoding='utf-8').write(json.dumps(doc, ensure_ascii=False, separators=(',', ':')))
    print('센터', len(recs), '· 행정동', len(set(D) & alld), '/', len(alld), '· 못 읽은 이름', len(miss))
    for m in miss[:40]:
        print('  miss', m)
    print('  못 읽은 행정동', doc['cover']['못 읽은 행정동'][:30])


if __name__ == '__main__':
    main()
