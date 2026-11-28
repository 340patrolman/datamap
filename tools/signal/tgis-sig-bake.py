# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🚦 서울 T-GIS 신호현시도(표준신호제어기DB 출력물) 판독 → data/sig-tgis-plan.json (tg-sig-tgis/2 · ksc-bake.py 의 TG 가 쓰는 sig-tgis-seocho.json 5곳 판과는 다른 파일)
#   소유자 2026-11-28 「지도에 평문 · 서초·방배 관할 전부(신설부터) · 서울 모두 진행」
#   싣는 것 = 요일 계획(그 장의 머리 글 그대로)·패턴(주기·연동·현시값 A/B)·출력물 날짜뿐. 현시도 그림·방향(어느 현시가 어느 쪽)은 읽지 않았고 싣지 않는다. PDF 원본도 올리지 않는다.
#   받아들이는 값 = ① 2차 판독(tgis-pass2.py · ko·en 네 벌에서 두 번 이상 같은 값 · 검산 통과) 이 통과한 장
#                  ② 손 판독 두 번(A_·B_)이 요일 계획·패턴·머리 글까지 같은 장(같은 파일일 때만)
#   그 밖의 장은 싣지 않고 07_API키/신호앱/tgis_read/_실패목록.tsv 에 남긴다
#   py -3.12 -X utf8 tools/signal/tgis-sig-bake.py [--manual <A_B_ 폴더>…]
import json, os, glob, re, sys, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.join(os.path.dirname(ROOT), '07_API키', '신호앱')
# 받은 묶음(구역)마다 원본 폴더 · 2차 판독 폴더를 한 줄씩 늘린다
BATCH = [('tgis_20261128', 'p2_t1128'), ('tgis_20261128_djgn', 'p2_djgn')]
P2 = [os.path.join(KB, 'tgis_read', b[1]) for b in BATCH]
ORIG = [os.path.join(KB, '교통과_원본', b[0]) for b in BATCH]
OUT = os.path.join(ROOT, 'data', 'sig-tgis-plan.json')
FAIL = os.path.join(KB, 'tgis_read', '_실패목록.tsv')
KSC = os.path.join(ROOT, 'data', 'sig-ksc-seocho.json')
# 같은 날짜에 파일이 둘일 때 소유자·이름으로 정한 것 {T-GIS 코드: 쓸 seq} — 1026 서초경찰서 「-1」 시차제 판(소유자 2026-11-27) · 1969 식유촌마을 「(수정)」
PICK = {1026: 94922, 1969: 91635}


def norm_label(t):
    t = re.sub(r'[^가-힣~∼\-]', '', str(t)).replace('∼', '~').replace('-', '~')
    return t


def label_days(t):
    """머리 글 → (요일 0 일~6 토 목록, 특수일·공휴일 몫인가). 모르면 None"""
    t = norm_label(t)
    if t in ('월~목요일', '월~목'): return [1, 2, 3, 4], False
    if t in ('평일',): return [1, 2, 3, 4, 5], False
    if t in ('월요일',): return [1], False
    if t in ('화~금요일', '화~금'): return [2, 3, 4, 5], False
    if t in ('화~목요일', '화~목'): return [2, 3, 4], False
    if t in ('금요일',): return [5], False
    if t in ('토요일',): return [6], False
    if t in ('일요일',): return [0], False
    if t in ('일요일공휴일', '일공휴일', '일,공휴일', '휴일'): return [0], True
    if t in ('공휴일',): return [0], True
    if t in ('특수일',): return [], True
    if t in ('토공휴일', '토요일공휴일'): return [6], True
    return None


def plans_of(labels, tod, special):
    """네 칸 머리 글 → 계획 목록. 요일 일곱이 한 번씩만 덮여야 한다"""
    got = []
    for k in '1234':
        rows = tod.get(k) or []
        if not rows: continue
        lb = None; dd = None
        for c in labels.get(k, []):
            d = label_days(c)
            if d is not None: lb, dd = norm_label(c), d; break
        if dd is None: return None, '머리 글 모름 TOD%s %s' % (k, labels.get(k))
        got.append({'k': int(k), 'label': lb, 'wd': list(dd[0]), 'hol': dd[1], 'rows': rows})
    if not got: return None, '계획 없음'
    for p in got:
        if p['label'] == '평일':
            others = set(w for q in got if q is not p for w in q['wd'])
            p['wd'] = [w for w in p['wd'] if w not in others]
    cover = sorted(w for p in got for w in p['wd'])
    if cover != list(range(7)): return None, '요일이 한 번씩 안 덮임 %s' % [(p['label'], p['wd']) for p in got]
    if not any(p['hol'] for p in got):
        if not special: return None, '특수일 표 못 읽음'
        top = sorted(special.items(), key=lambda x: -x[1])
        if top[0][1] < 20: return None, '특수일 번호가 적게 읽힘 %s' % special
        hit = [p for p in got if p['k'] == int(top[0][0])]
        if not hit: return None, '특수일 TOD%s 가 계획에 없음' % top[0][0]
        hit[0]['hol'] = True
    return got, None


def zcut(v):
    v = list(v)
    while len(v) > 1 and v[-1] == 0: v.pop()
    return v


def manual_pairs(dirs):
    out = {}
    for d in dirs:
        for f in glob.glob(os.path.join(d, 'A_*.json')):
            g = os.path.join(d, 'B_' + os.path.basename(f)[2:])
            if not os.path.exists(g): continue
            a = json.load(open(f, encoding='utf-8')); b = json.load(open(g, encoding='utf-8'))
            if a.get('file') != b.get('file'): continue
            if a['tod'] != b['tod'] or a['pat'] != b['pat'] or a.get('todLabel') != b.get('todLabel'): continue
            sa = a.get('patSicha') or a.get('pat_sicha'); sb = b.get('patSicha') or b.get('pat_sicha')
            if sa or sb:
                # 「일반」·「시차」 두 표인 장 — 시차 표와 적용 시간대까지 적은 셋째 판독(C_)이 두 판독과 같을 때만
                cf = [json.load(open(c, encoding='utf-8')) for c in glob.glob(os.path.join(KB, 'tgis_read', 'hand_*', 'C_*.json'))]
                nz = lambda P: {n: [zcut(q['a']), zcut(q['b']), q.get('off')] for n, q in (P or {}).items()}
                hit = [c for c in cf if c['file'] == a['file'] and c['tod'] == a['tod'] and nz(c['pat']) == nz(a['pat']) and nz(c['alt']['pat']) == nz(sa) == nz(sb)]
                if not hit: continue
                a = dict(a, alt=hit[0]['alt'])
            out[a['file']] = a
    return out


def tdata_match(it, meas):
    """T-Data 실측(sigdir-seoul tod = [요일 갈래 0 평일·1 토·2 일, 시, 주기]) 과 계획 주기(그 시 30분 · 첫 계획 전이면 전날 마지막)가 ±1초인 줄의 몫 — (맞은 수, 본 수)"""
    def plan(wd):
        for p in it['plans']:
            if wd in p['wd']: return p
    ok = n = 0
    for kind, h, cyc in (r[:3] for r in meas):
        wd = {0: 3, 1: 6, 2: 0}.get(kind)
        if wd is None: continue
        p = plan(wd); hm = '%02d30' % h
        rows = [r for r in p['rows'] if r[0] <= hm]
        if rows: v = rows[-1][1]
        else:
            q = plan((wd - 1) % 7); v = q['rows'][-1][1]
        n += 1; ok += abs(v - cyc) <= 1
    return ok, n


def notes(base):
    """출력물 글(한글 판독)에서 운영 조건 — blink 시간제 점멸(그 시간에는 계획값이 틀린다 → 싣지 않는다) · sicha 시차 운영 표기 · ped 보행자 작동 신호기"""
    out = {'blink': None, 'sicha': 0, 'ped': 0, 'read': 0}
    for s in ('3', '4'):
        f = os.path.join(KB, 'tgis_read', 'raw', '%s.ko.s%s.json' % (base, s))
        if not os.path.exists(f): continue
        j = json.load(open(f, encoding='utf-8-sig')); pg = j[0] if isinstance(j, list) else j
        t = ''.join(w[0] for w in sorted(pg['words'], key=lambda w: (w[2] // 30, w[1]))) + '|' + ''.join(w[0] for w in pg['words'])
        out['read'] = 1
        for m in re.finditer(r'점멸(신호)?(운영|제어|시간대)', t):
            tail = t[m.end():m.end() + 30]
            if re.match(r'.{0,12}(해제|삭제)', tail): continue
            ex = t[max(0, m.start() - 8):m.end() + 22].split('|')[0]
            cur = out['blink'] or {'wins': [], 'all': 0, 'txt': ex}
            for w in re.finditer(r'(\d{1,2}):(\d{2})[~∼\-～](?:익일)?(\d{1,2}):(\d{2})', t[m.end():m.end() + 24]):
                h1, h2 = int(w.group(1)), int(w.group(3))
                if h1 < 25 and h2 < 25:
                    win = ['%02d%s' % (h1, w.group(2)), '%02d%s' % (h2, w.group(4))]
                    if win not in cur['wins']: cur['wins'].append(win); cur['txt'] = ex
            if re.search(r'전일|항시|점멸(신호)?(운영|제어)중', ex): cur['all'] = 1
            out['blink'] = cur
        t2 = re.sub(r'시차(제)?(신호)?(운영)?(삭제|해제)', '', t)
        if re.search(r'(?<!현)시차', t2): out['sicha'] = 1
        if '보행자작동' in t: out['ped'] = 1
    return out


# 손 판독과 글자 인식이 어긋난 칸을 원본 그림으로 가린 것(손 판독이 맞음 — 글자 인식이 한 줄 밀림) {파일: 연동(옵셋)을 가린 패턴}
SEEN = {'tg390_20250902_91643': {'11', '14'}}   # 방배역 2026-11-28 그림 확인


def single_reads(done):
    """손 판독 한 번(C_)— 검산(현시 합 = 주기 · 계획 주기 = 패턴 주기)과 글자 인식이 두 번 이상 같게 읽은 칸이 하나도 어긋나지 않을 때만"""
    out = {}
    for cf in glob.glob(os.path.join(KB, 'tgis_read', 'hand_*', 'C_*.json')):
        c = json.load(open(cf, encoding='utf-8')); f = c['file']
        if f in done or c.get('alt') or c.get('sichaje') not in (None, '', [], {}, False): continue
        P = c.get('pat') or {}
        if not P or any(not (sum(q['a']) == sum(q['b']) == q['c']) for q in P.values()): continue
        if any(str(r[2]) not in P or P[str(r[2])]['c'] != r[1] for L in c['tod'].values() for r in L): continue
        bad = 0; seen = 0
        for d in P2:
            jf = os.path.join(d, f + '.json')
            if not os.path.exists(jf): continue
            m = json.load(open(jf, encoding='utf-8'))
            for k, L in (m.get('tod') or {}).items():
                for r in L: seen += 1; bad += r not in c['tod'].get(k, [])
            for n, q in (m.get('pat') or {}).items():
                if n not in P: bad += 1; continue
                seen += 1; bad += zcut(q['a']) != zcut(P[n]['a']) or zcut(q['b']) != zcut(P[n]['b']) or (q.get('off') is not None and q['off'] != P[n]['off'] and n not in SEEN.get(f, ()))
        if bad == 0 and seen >= 8: out[f] = dict(c, checked=seen)
        else: print('손 한 번 판독 보류', f, '어긋남', bad, '맞대 본 칸', seen)
    return out


def main():
    global OUT
    if '--out' in sys.argv: i = sys.argv.index('--out'); OUT = os.path.abspath(sys.argv[i + 1]); del sys.argv[i:i + 2]
    man = []
    if '--manual' in sys.argv: man = sys.argv[sys.argv.index('--manual') + 1:]
    T = json.load(open(os.path.join(ROOT, 'data', 'tgis-seoul.json'), encoding='utf-8'))
    tg = {int(r[0]): r for r in T['items']}
    ksc = {str(x['no']): str(x.get('day') or '').replace('-', '') for x in json.load(open(KSC, encoding='utf-8'))['items']}
    M = manual_pairs(man)
    S1 = single_reads(set(M))
    for f, c in S1.items(): M[f] = dict(c, one=1)
    SD = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))
    files = {}
    for p in [p for d9 in ORIG for p in glob.glob(os.path.join(d9, '*.pdf'))]:
        m = re.match(r'tg(\d+)_(\d{8})_(\d+)\.pdf$', os.path.basename(p))
        if not m: continue
        c, d, seq = int(m.group(1)), m.group(2), int(m.group(3))
        files.setdefault(c, []).append((d, seq, os.path.splitext(os.path.basename(p))[0]))
    items = []; fail = []; how = {'auto': 0, 'hand': 0, 'check': 0}; skip5 = 0
    for c, L in sorted(files.items()):
        L.sort()
        row = tg.get(c)
        if not row: fail.append([c, '', L[-1][2], 'T-GIS 교차로 목록에 없음']); continue
        cits = row[6]; nm = row[1]
        cand = []
        for d, seq, base in L:
            src = None; why = ''
            h = [M[base]] if base in M else [v for k, v in M.items() if k.startswith('tg_') and re.sub(r'^tg_0*(\d+)_.*', r'\1', k) == str(cits) and d in k]
            if h:
                a = h[0]
                src = {'no': a['no'], 'day': a.get('day'), 'tod': a['tod'], 'pat': a['pat'], 'labels': {k: [v] for k, v in a['todLabel'].items()}, 'special': {'4': 30}, 'how': 'check' if a.get('one') else 'hand', 'alt': a.get('alt')}
            else:
                for pd in P2:
                    jf = os.path.join(pd, base + '.json')
                    if os.path.exists(jf):
                        m = json.load(open(jf, encoding='utf-8'))
                        if m['bad']: why = ' ; '.join(m['bad'][:3])
                        else: src = dict(m, how='auto')
                        break
                else:
                    why = '2차 판독 없음'
            if src is None: cand.append((None, d, seq, base, why)); continue
            pl, err = plans_of(src['labels'], src['tod'], src.get('special'))
            if err: cand.append((None, d, seq, base, err)); continue
            no = str(src.get('no') or '')
            if cits and no and str(cits) != no: cand.append((None, d, seq, base, '출력물 번호 %s ≠ 지도 번호 %s' % (no, cits))); continue
            key = str(cits or no)
            if not key or key == '0': key = 'T%d' % c
            used = set(r[2] for p in pl for r in p['rows'])
            nt = notes(base)
            if not nt['read']: cand.append((None, d, seq, base, '참고 글을 읽지 못함')); continue
            mm = [(r[0], r[1], r[2]) for p in pl for r in p['rows'] if str(r[2]) not in src['pat'] or src['pat'][str(r[2])]['c'] != r[1]]
            if mm and src['how'] != 'hand': cand.append((None, d, seq, base, '출력물의 요일 계획 주기 ≠ 패턴 주기 %s' % (mm[:2],))); continue
            hol = [p for p in pl if p['hol']]
            if len(hol) > 1 and any(p['rows'] != hol[0]['rows'] for p in hol):
                sp9 = sorted((src.get('special') or {}).items(), key=lambda x: -x[1])
                win = [p for p in hol if sp9 and p['k'] == int(sp9[0][0]) and sp9[0][1] >= 20]
                if not win: cand.append((None, d, seq, base, '특수일 계획이 둘이고 특수일 표로 못 가림')); continue
                for p in hol: p['hol'] = p is win[0]
            pat = {n: {'c': q['c'], 'off': q['off'], 'a': zcut(q['a']), 'b': zcut(q['b'])} for n, q in src['pat'].items() if int(n) in used}
            it0 = {'no': key, 'c': c, 'nm': nm, 'lat': row[2], 'lon': row[3], 'filed': d, 'day': src.get('day'), 'plans': pl, 'pat': pat, 'how': src['how']}
            if src.get('alt'): it0['alt'] = {'name': src['alt']['name'], 'win': src['alt']['win'], 'pat': {n: {'c': q['c'], 'off': q['off'], 'a': zcut(q['a']), 'b': zcut(q['b'])} for n, q in src['alt']['pat'].items() if int(n) in used}}
            if nt['sicha'] and not src.get('alt'): it0['sicha'] = 1
            if nt['ped']: it0['ped'] = 1
            if nt['blink']: it0['blink'] = nt['blink']
            if mm: it0['mm'] = sorted({'%s/%d/%d' % r for r in mm})
            cand.append((it0, d, seq, base, ''))
        top = max(x[1] for x in cand)
        newest = [x for x in cand if x[1] == top]
        if c in PICK: newest = [x for x in newest if x[2] == PICK[c]] or newest
        good = [x for x in newest if x[0]]
        if len(newest) > 1 and (len(good) != len(newest) or any(json.dumps([g[0]['plans'], g[0]['pat']], sort_keys=True) != json.dumps([good[0][0]['plans'], good[0][0]['pat']], sort_keys=True) for g in good)):
            fail.append([c, cits, newest[-1][3], '같은 날 파일 %d개가 다르거나 일부 못 읽음 — 어느 것이 운영 중인지 확인' % len(newest)]); continue
        if not good: fail.append([c, cits, newest[-1][3], newest[-1][4]]); continue
        it = good[-1][0]
        meas = (SD.get('tod') or {}).get(it['no']) or []
        ok, n = tdata_match(it, meas)
        if n >= 10 and ok < 0.5 * n: fail.append([c, cits, newest[-1][3], 'T-Data 실측 주기와 어긋남 — 맞음 %d/%d' % (ok, n)]); continue
        it['td'] = [ok, n]
        if it['no'] in ksc and it['filed'] <= ksc[it['no']]: skip5 += 1; continue
        if it['no'] in ksc: it['newer'] = 1
        how[it['how']] += 1; items.append(it)
    nos = [x['no'] for x in items]
    dup = set(n for n in nos if nos.count(n) > 1)
    for x in [x for x in items if x['no'] in dup]: fail.append([x['c'], x['no'], x['nm'], '교차로 번호가 두 곳에 겹침'])
    items = sorted([x for x in items if x['no'] not in dup], key=lambda x: int(x['no']) if x['no'].isdigit() else 10 ** 7 + x['c'])
    # 딸린 신호(연등) — T-GIS 연동 부모 코드가 실린 교차로인 것. 부모의 요일 계획·주기만 보인다(현시값은 부모 것이라 싣지 않는다)
    byc = {x['c']: x for x in items}
    kids = []; kid0 = 0
    SD0 = json.load(open(os.path.join(ROOT, 'data', 'sigdir-seoul.json'), encoding='utf-8'))
    SG0 = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']
    oth = [(SD0['pts'][k][0], SD0['pts'][k][1], str(k)) for k in SD0['pts'] if SD0['its'].get(k)] + [(float(x['lat']), float(x['lon']), str(x['no'])) for x in SG0]
    def same_sig(la, lo, pno):
        # 50m 안 다른 자료의 신호가 부모 자신이거나 그 연등의 T-Data 번호(앞자리 하나 + 부모 번호 · 예 21552 = 1552)일 때만 같은 신호로 본다
        pn = str(pno)
        for a, b, n in oth:
            if ((a - la) * 111000) ** 2 + ((b - lo) * 88400) ** 2 > 2500: continue
            if n == pn or (n.isdigit() and pn.isdigit() and len(n) == 5 and n[0] in '23456789' and int(n) % 10000 == int(pn)): return True
        return False
    for r in T['items']:
        c, nm, la, lo, par, cits = r[0], r[1], r[2], r[3], r[4], r[6]
        if par and par != c and par in byc and c not in byc and (not cits or str(cits) not in nos) and '경보' not in nm:
            # 교차로 번호가 빈 연등(T-GIS 코드로) — 다른 자료의 신호가 50m 안에 있으면 같은 신호로 보고 겹쳐 그리지 않는다
            if not cits and same_sig(la, lo, byc[par]['no']): continue
            if not cits: kid0 += 1
            kids.append([str(cits) if cits else 'T%d' % c, c, nm, la, lo, byc[par]['no']])
    # 값이 없는 신호 교차로(받은 구역: 서초·방배서 관할 + 동작·관악구) — 지도에 회색 점과 까닭
    SG = json.load(open(os.path.join(ROOT, 'data', 'signal-tod-seoul.json'), encoding='utf-8'))['spots']
    have = [(x['lat'], x['lon']) for x in items] + [(k[3], k[4]) for k in kids] + [(float(x['lat']), float(x['lon'])) for x in SG] + [(float(x['lat']), float(x['lon'])) for x in json.load(open(KSC, encoding='utf-8'))['items']] + [(SD['pts'][k][0], SD['pts'][k][1]) for k in SD['pts'] if SD['its'].get(k)]
    havec = {x['c'] for x in items} | {k[1] for k in kids}
    haven = set(SD['its']) | {str(x['no']) for x in SG} | set(ksc) | {x['no'] for x in items}
    why_f = {str(r[0]): r[3] for r in fail}
    miss = []
    inv = {}
    for jf in glob.glob(os.path.join(KB, '교통과_원본', 'tgis_*', 'tgis_inventory_*.json')):
        for k, L in json.load(open(jf, encoding='utf-8'))['items'].items():
            if L: inv[int(k)] = len(L)
    for r in T['items']:
        c, nm, la, lo, par, pe, cits, gu = r[:8]
        if not (pe in (340, 380) or gu in (590, 620, 11590, 11620)): continue
        if par and par != c and not cits and par in byc and same_sig(la, lo, byc[par]['no']): continue
        if c in havec or (cits and str(cits) in haven) or any(abs(a - la) < 0.0004 and abs(b - lo) < 0.0005 and ((a - la) * 111000) ** 2 + ((b - lo) * 88400) ** 2 <= 900 for a, b in have): continue
        w = why_f.get(str(c), '')
        if c in files: why = '현시도는 받았으나 값을 확정하지 못함(판독 대기)' if '실측' not in w else '현시도와 실측 주기가 크게 달라 싣지 않음'
        elif inv.get(c): why = 'T-GIS 에 옛 현시도만 있어 싣지 않음 — 교통과 확인 필요'
        elif '경보' in nm: why = '경보(점멸) 신호 — 신호 계획표가 없는 곳'
        elif par and par != c: why = '딸린 신호(연등) — 부모 교차로의 계획을 아직 싣지 못함'
        elif gu in (590, 620, 11590, 11620) and pe not in (340, 380): why = '현시도 판독 대기(받는 중)'
        else: why = 'T-GIS 에 현시도 파일이 없음 — 교통과 확인 필요'
        miss.append([str(cits or ''), c, nm, la, lo, why])
    doc = {'schema': 'tg-sig-tgis/2', 'made': datetime.date.today().isoformat(),
           'source': '서울시 교통안전시설물관리시스템(T-GIS) 교차로별 신호현시도 — 표준신호제어기데이터베이스 출력물 판독(서초·방배서 관할 · 동작·관악구)',
           'note': '계획값이다 — 감응·수동 운영 중에는 실제와 다를 수 있다. 어느 현시가 어느 방향인지는 읽지 않았다. 옵셋만으로 「몇 초 남음」·연동 속도를 계산하지 않는다. filed = T-GIS 에 올라온 파일 날짜 · day = 출력물에 적힌 날짜(못 읽으면 null). how auto = 글자 인식 네 벌에서 두 번 이상 같은 값 · hand = 따로 두 번 손 판독이 같은 값.',
           'fields': 'items[{newer 1 = 교통과 5곳 자료(sig-ksc-seocho)보다 새 파일, no 교차로 번호, c T-GIS 교차로 코드, nm, lat, lon, filed YYYYMMDD, day YYYY-MM-DD|null, plans[{k TOD 번호, label 출력물 머리 글, wd[0 일 … 6 토], hol 공휴일·특수일도 이 계획, rows[[시작 HHMM, 주기, 패턴]]}], pat{패턴: {c 주기, off 연동(옵셋), a[A링 현시별 초], b[B링]}}, how, alt{name, win{TOD 번호:[HHMM 부터, 까지]}, pat} 그 시간대에는 pat 대신 alt.pat, sicha 1 = 출력물에 「시차」 운영 표기가 있고 그 값은 읽지 않음, ped 1 = 보행자 작동 신호기 표기 · blink{wins[[HHMM,HHMM]…], all 1=전일·항시, txt 글자 인식 조각} = 점멸 운영 표기(그 시간대에는 계획값을 보이지 않는다 · 시간을 모르거나 전일이면 늘 보이지 않는다) · miss[[번호|'', T-GIS 코드, 이름, 위도, 경도, 까닭]] = 받은 구역에서 값이 없는 신호 교차로, td[T-Data 실측 주기와 ±1초 맞은 줄, 맞대 본 줄 — 0,0 이면 맞대 보지 못함]}] · 실측 10줄 넘게 보고 절반도 못 맞으면 싣지 않는다(80% 미만은 카드에 경고 · 소유자 2026-11-28 「현시도 날짜대로」) · how check = 손 판독 한 번 + 검산 + 글자 인식과 어긋남 0 · mm[] = 출력물 안에서 계획 주기 ≠ 패턴 주기인 줄(두 번 손 판독이 같은 장만 · 카드에 경고) · kids[[교차로 번호, T-GIS 코드, 이름, 위도, 경도, 부모 교차로 번호]] = 딸린 신호(연등) — 부모의 계획·주기로 돈다',
           'items': items, 'kids': kids, 'miss': miss}
    json.dump(doc, open(OUT, 'w', encoding='utf-8', newline=''), ensure_ascii=False, separators=(',', ':'))
    with open(FAIL, 'w', encoding='utf-8') as f:
        f.write('T-GIS코드\t교차로번호\t파일\t까닭\n')
        for r in fail: f.write('\t'.join(str(v) for v in r) + '\n')
    print('딸린 신호', len(kids), '(번호 없는 연등', kid0, ')', '· 값 없음 표시', len(miss), {m[5][:12]: sum(1 for x in miss if x[5] == m[5]) for m in miss})
    print('실음 %d (자동 %d · 손 %d) · 교통과 5곳 따로 %d · 실패 %d · %d KB' % (len(items), how['auto'], how['hand'] + how['check'], skip5, len(fail), os.path.getsize(OUT) // 1024))


if __name__ == '__main__':
    main()
