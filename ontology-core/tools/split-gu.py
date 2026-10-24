# -*- coding: utf-8 -*-
# 여섯 구 온톨로지 코어(core-six.json · 7MB)를 구마다 나눈다 → ontology-core/data/core-six/<구>.json + index.json
#   소유자 2026-10-25 「계속 진행」 — 🧩 엮임 보기(js/link.js)를 서초 밖 다섯 구로 넓히려고. 폰은 고른 구 한 장만 받는다.
#   한 구 = 그 구 교차로(INT)·행정동(DNG)에서 시작해 링크를 따라간 것: 1걸음은 모두 · 그다음은 길(접근로 → 구간 → 칸·사고 칸)·사고(→ 위반 → 법규 → 판례)·지구대(→ 경찰서)·조치(→ 기록)·규칙(→ 현장 판단)만
#   다른 구 교차로는 「이웃」으로 들어오되 거기서 더 펼치지 않는다 · 값은 core-six 그대로(고치지 않는다) · 링크 속성 그대로
#   index.json = 고르기 목록과 「자리 → 구」 찾기용(교차로·동·역·상권·지구대의 id·이름·자리·구)
#   py -3.12 -X utf8 ontology-core/tools/split-gu.py   (build.py --area six 다음에)
import json, os, collections
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, 'data', 'core-six.json'); OUT = os.path.join(HERE, 'data', 'core-six')
GO = {'APR': {'이룸'}, 'RD': {'지남', '사고칸'}, 'ACC': {'주요원인'}, 'VIO': {'근거'}, 'LAW': {'해석'}, 'PBX': {'소속'}, 'ACT': {'근거기록'}, 'RULE': set(), 'FK': {'뒷받침'}, 'STA': set(), 'STN': {'가까운교차로'}, 'TRD': {'들어감동', '품음'}, 'EVT': {'근처역'}}
GO_IN = {'STN': {'근처역'}, 'STA': {'소속'}}   # 역 ← 행사(근처역) — q16 · 경찰서 ← 지구대(소속) — q12
DEEP = {'발생', '보유', '가까움', '속함', '관할', '가까운지구대', '들어감'}   # 이 구에 「사는」 역·상권이 품은 이웃 구 교차로는 이만큼 더 펼친다(q16·q17 이 그 교차로 사고를 본다)


def main():
    c = json.load(open(SRC, encoding='utf-8'))
    O = {o['id']: o for o in c['objects']}
    out, inn = collections.defaultdict(list), collections.defaultdict(list)
    for i, e in enumerate(c['edges']):
        out[e[0]].append(i); inn[e[2]].append(i)
    def gu_of(o):
        if o['t'] == 'INT': return str(o.get('dong', ''))[:5]
        if o['t'] == 'DNG': return str(o.get('gu') or o.get('code', '')[:5])
        return None
    gus = sorted({gu_of(o) for o in c['objects'] if o['t'] == 'INT'} - {None, ''})
    os.makedirs(OUT, exist_ok=True); idx = {'schema': 'onto-core-gu/1', 'from': 'core-six.json ' + c.get('made', ''), 'area': c.get('area'), 'gus': {}, 'items': []}
    for g in gus:
        seed = [o['id'] for o in c['objects'] if gu_of(o) == g]
        keep, E = set(seed), set()
        for s in seed:   # 1걸음 — 들고 나는 링크 모두
            for i in out[s] + inn[s]:
                E.add(i); keep.add(c['edges'][i][0]); keep.add(c['edges'][i][2])
        # 이 구에 사는 역·상권·지구대(이어진 교차로 대부분이 이 구) — 그것과 그 교차로를 한 걸음 더(q13·q16·q17)
        for o in c['objects']:
            if o['t'] not in ('STN', 'TRD', 'PBX'): continue
            ints = [c['edges'][i][2] for i in out[o['id']] if c['edges'][i][2] in O and O[c['edges'][i][2]]['t'] == 'INT'] + [c['edges'][i][0] for i in inn[o['id']] if c['edges'][i][0] in O and O[c['edges'][i][0]]['t'] == 'INT']
            gg = collections.Counter(gu_of(O[x]) for x in ints)
            if not gg or gg.most_common(1)[0][0] != g: continue
            keep.add(o['id'])
            for i in out[o['id']] + inn[o['id']]:
                E.add(i); keep.add(c['edges'][i][0]); keep.add(c['edges'][i][2])
            for x in ints:
                for i in out[x]:
                    if c['edges'][i][1] in DEEP: E.add(i); keep.add(c['edges'][i][2])
        fr = [k for k in keep if k not in seed]
        seen = set(seed)
        while fr:   # 그다음 — 정한 갈래만, 다른 구 교차로·동에서는 멈춤
            nx = []
            for k in fr:
                if k in seen: continue
                seen.add(k); o = O.get(k)
                if not o or o['t'] in ('INT', 'DNG'): continue
                rels = GO.get(o['t'])
                if rels is None: continue
                for i in out[k]:
                    e = c['edges'][i]
                    if e[1] in rels:
                        E.add(i); keep.add(e[2]); nx.append(e[2])
                for i in inn[k]:
                    e = c['edges'][i]
                    if e[1] in GO_IN.get(o['t'], ()):
                        E.add(i); keep.add(e[0])
                if o['t'] == 'RULE':
                    for i in inn[k]:
                        e = c['edges'][i]
                        if e[1] == '뒷받침': E.add(i); keep.add(e[0])
            fr = nx
        objs = [O[k] for k in sorted(keep) if k in O]
        doc = {k: c[k] for k in ('schema', 'schema_ext', 'sources', 'asof', 'unverified_precedents', 'unverified_note') if k in c}
        doc.update({'area': '%s(%s) — core-six 를 구로 나눈 것' % (c.get('area', ''), g), 'gu': g, 'made': c.get('made'), 'split': 'ontology-core/tools/split-gu.py',
                    'count': dict(collections.Counter(o['t'] for o in objs)), 'objects': objs, 'edges': [c['edges'][i] for i in sorted(E)]})
        p = os.path.join(OUT, g + '.json'); json.dump(doc, open(p, 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        idx['gus'][g] = {'kb': os.path.getsize(p) // 1024, 'n': len(objs), 'e': len(E)}
        print(g, len(objs), len(E), os.path.getsize(p) // 1024, 'KB')
    for o in c['objects']:
        if o['t'] in ('INT', 'DNG', 'STN', 'TRD', 'PBX') and (o.get('lat') or o['t'] in ('DNG', 'TRD')):
            g = gu_of(o) or (str(o.get('gu')) if o.get('gu') else None)
            if o['t'] in ('STN', 'PBX', 'TRD'):
                g = None   # 역·지구대·상권은 이어진 교차로가 가장 많은 구 — 아래에서(split 의 「사는 구」와 같은 셈)
            idx['items'].append([o['id'], o.get('nm', ''), round(float(o['lat']), 5) if o.get('lat') else None, round(float(o['lon']), 5) if o.get('lon') else None, g])
    gi = {o['id']: gu_of(o) for o in c['objects'] if o['t'] == 'INT'}
    for it in idx['items']:
        if it[4] is None:   # 역 → 가까운교차로 · 지구대 ← 가까운지구대 · 상권 → 품음 · 그래도 없으면 가장 가까운 교차로
            k = it[0]; cand = [c['edges'][i][2] for i in out[k]] + [c['edges'][i][0] for i in inn[k]]
            gg = [gi[x] for x in cand if x in gi]
            if gg: it[4] = collections.Counter(gg).most_common(1)[0][0]
    idx['fields'] = 'items[[id, 이름, 위도, 경도, 구]] · gus{구: {kb, n 객체, e 링크}}'
    json.dump(idx, open(os.path.join(OUT, 'index.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
    print('index', len(idx['items']), os.path.getsize(os.path.join(OUT, 'index.json')) // 1024, 'KB')


if __name__ == '__main__':
    main()
