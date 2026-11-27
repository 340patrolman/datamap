# -*- coding: utf-8 -*-
# 가르고 길 묶음에 빠진 좌회전 금지를 덧붙인다(현장 확인한 곳만 · 2026-11-28 검수 뒤) — data/gargo-turnfix.json(자리·들어오는 방향·나가는 방향 · 길 묶음의 번호와 무관) → 각 묶음의 turns 에 [마디, 들어오는 길(way), 나가는 길(way), 0]
#   소유자 2026-11-28 「좌회전 없는 곳에서 하라고 하더라 · 서초3동사거리가 그 예」 — OSM 에 회전 제한이 빠진 곳. 근거는 목록 파일의 source.
#   길 묶음을 다시 구우면(pack-bake.py · pack-tile.py) 이 도구를 다시 돌린다(이미 막힌 곳은 건너뜀).
#   덧붙이는 제한은 「그 좌회전만 사라지고 다른 들어오는 길·나가는 길은 그대로」인 것만 — 아니면 넣지 않고 알린다.
#   py -3.12 -X utf8 tools/gargo/turnfix.py [--dry]
import json, math, os, sys, glob, heapq, collections
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); G = os.path.join(ROOT, 'gargo')
KX, KY, R = 88400.0, 111000.0, 45.0
DRY = '--dry' in sys.argv


def load(p):
    return json.load(open(p, encoding='utf-8'))


def brg(a, b):
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360


def diff(a, b):
    return abs((a - b + 180) % 360 - 180)


class Pack:
    def __init__(self, main):
        self.main = main; j = load(main); self.j = j; self.tiled = 'segs' in j
        files = [j] + ([load(f) for f in sorted(glob.glob(os.path.join(os.path.dirname(main), 't', '*.json')))] if self.tiled else [])
        bx, by = j['base']; self.N = {}; segs = {}; turns = set()
        for f in files:
            if self.tiled:
                for r in f['nodes']: self.N.setdefault(r[0], ((bx + r[1]) / 1e6 * KX, (by + r[2]) / 1e6 * KY))
                rows = [(r[0], r[1:10]) for r in f['segs']]
            else:
                for i, (x, y) in enumerate(zip(f['nx'], f['ny'])): self.N[i] = ((bx + x) / 1e6 * KX, (by + y) / 1e6 * KY)
                rows = list(enumerate(f['seg']))
            for sid, r in rows:
                if sid in segs: continue
                a, b, ln, v, cls, nm, way, d, g = r[:9]
                if a not in self.N or b not in self.N: continue
                P = [self.N[a]]
                if g >= 0:
                    gg = f['geo'][g]; lon, lat = self.N[a][0] / KX * 1e6, self.N[a][1] / KY * 1e6
                    for k in range(0, len(gg), 2):
                        lon += gg[k]; lat += gg[k + 1]; P.append((lon / 1e6 * KX, lat / 1e6 * KY))
                P.append(self.N[b]); segs[sid] = (a, b, ln, way, d, P)
            for t in f['turns']: turns.add(tuple(t))
        self.E = []
        for sid, (a, b, ln, way, d, P) in segs.items():
            if d & 1: self.E.append((a, b, sid, way, ln, P))
            if d & 2: self.E.append((b, a, sid, way, ln, P[::-1]))
        self.out = collections.defaultdict(list); self.inn = collections.defaultdict(list)
        for i, e in enumerate(self.E): self.out[e[0]].append(i); self.inn[e[1]].append(i)
        self.ban = collections.defaultdict(set); self.only = collections.defaultdict(set)
        for v, fw, tw, k in turns: (self.only if k else self.ban)[(v, fw)].add(tw)
        self.grid = collections.defaultdict(set); self.ngrid = collections.defaultdict(list)
        for i, e in enumerate(self.E):
            for (x1, y1), (x2, y2) in zip(e[5], e[5][1:]):
                n = int(math.hypot(x2 - x1, y2 - y1) // 20) + 1
                for k in range(n + 1): self.grid[(int((x1 + (x2 - x1) * k / n) // 50), int((y1 + (y2 - y1) * k / n) // 50))].add(i)
        for n, p in self.N.items(): self.ngrid[(int(p[0] // 50), int(p[1] // 50))].append(n)
        self.add = []

    def near(self, p, h, dmax=14):
        got = {}; gx, gy = int(p[0] // 50), int(p[1] // 50)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in self.grid.get((gx + dx, gy + dy), ()):
                    for a, b in zip(self.E[i][5], self.E[i][5][1:]):
                        vx, vy = b[0] - a[0], b[1] - a[1]; l2 = vx * vx + vy * vy
                        if not l2: continue
                        t = max(0, min(1, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2)); d = math.hypot(a[0] + vx * t - p[0], a[1] + vy * t - p[1])
                        if d <= dmax and diff(brg(a, b), h) < 30 and (i not in got or d < got[i]): got[i] = d
        return got

    def nxt(self, i):
        e = self.E[i]; nd = e[1]; bn = self.ban.get((nd, e[3])); on = self.only.get((nd, e[3]))
        for f in self.out[nd]:
            w = self.E[f][3]
            if (bn and w in bn) or (on and w not in on): continue
            if self.E[f][1] == e[0] and self.E[f][2] == e[2]: continue
            yield f

    def path(self, start, goals, c):
        q = [(0, start, (start,))]; seen = set()
        while q:
            d, i, p = heapq.heappop(q)
            if i in goals and len(p) > 1: return p
            if i in seen: continue
            seen.add(i); nd = self.E[i][1]
            if math.hypot(self.N[nd][0] - c[0], self.N[nd][1] - c[1]) > 70: continue
            for f in self.nxt(i):
                if d + self.E[f][4] <= 160: heapq.heappush(q, (d + self.E[f][4], f, p + (f,)))
        return None

    def dist(self, n, c):
        return math.hypot(self.N[n][0] - c[0], self.N[n][1] - c[1])

    def around(self, c):
        ins = []
        gx, gy = int(c[0] // 50), int(c[1] // 50)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for n in self.ngrid.get((gx + dx, gy + dy), ()):
                    if self.dist(n, c) <= R:
                        ins += [i for i in self.inn[n] if self.dist(self.E[i][0], c) > R]
        return ins

    def reach(self, i, c):
        got = set(); st = [i]; seen = {i}
        while st:
            k = st.pop()
            for f in self.nxt(k):
                if f in seen: continue
                seen.add(f)
                if self.dist(self.E[f][1], c) > R: got.add(f)
                else: st.append(f)
        return got

    def fix(self, it):
        c = (it['lon'] * KX, it['lat'] * KY)
        A = self.near(tuple((it['pin'][0] * KX, it['pin'][1] * KY)), it['in_brg']); B = self.near((it['pout'][0] * KX, it['pout'][1] * KY), it['out_brg'])
        if not A or not B: return '길 없음'
        a0 = min(A, key=A.get); p = self.path(a0, set(B), c)
        if p is None: return '이미 막힘'
        start = a0
        for k in p:
            if self.dist(self.E[k][0], c) > R: start = k
        ins = set(self.around(c)) | {start}; before = {i: self.reach(i, c) for i in ins}
        mine = []   # 한 번의 제한으로 길이 남으면(나란한 길이 둘 이상) 남은 길에서 하나씩 더(많아야 6) — 끝까지 못 막으면 모두 되돌린다
        while p is not None and len(mine) < 6:
            for x, y in zip(p, p[1:]):
                key = (self.E[x][1], self.E[x][3]); w = self.E[y][3]
                if w in self.ban[key]: continue
                self.ban[key].add(w)
                ok = True
                for i in ins:
                    after = self.reach(i, c); lost = before[i] - after
                    if i == start or diff(brg(self.E[i][5][-2], self.E[i][5][-1]), it['in_brg']) < 30:
                        ok = all(diff(brg(c, self.N[self.E[f][1]]), it['out_brg']) < 40 for f in lost) and (not lost or len(after) >= 1)
                    elif lost: ok = False
                    if not ok: break
                if ok:
                    mine.append([key[0], key[1], w, 0]); break
                self.ban[key].discard(w)
            else:
                break
            p = self.path(a0, set(B), c)
        if p is None:
            self.add.extend(mine); return '넣음'
        for v, fw, tw, _ in mine: self.ban[(v, fw)].discard(tw)
        return '다른 길까지 막혀 안 넣음'

    def save(self):
        if not self.add: return
        raw = open(self.main, encoding='utf-8', newline='').read(); i = raw.index('"turns":'); a = raw.index('[', i); depth = 0
        for z in range(a, len(raw)):
            depth += (raw[z] == '[') - (raw[z] == ']')
            if depth == 0: break
        old = raw[a + 1:z].strip(); more = ','.join(json.dumps(t, separators=(',', ':')) for t in self.add)
        new = raw[:a] + '[' + (old + ',' if old else '') + more + ']' + raw[z + 1:]
        if 'turns_total' in self.j: new = new.replace('"turns_total":%d' % self.j['turns_total'], '"turns_total":%d' % (self.j['turns_total'] + len(self.add)), 1)
        k = json.loads(new)   # 칸 묶음은 core 의 turns_total(원본 전체 수)도 같이 — 관문 「회전 금지 수가 원본과 같다」
        assert len(k['turns']) == len(self.j['turns']) + len(self.add) and k.get('turns_total', 0) == self.j.get('turns_total', -len(self.add)) + len(self.add)
        open(self.main, 'w', encoding='utf-8', newline='').write(new)


def main():
    items = [i for i in load(os.path.join(ROOT, 'data', 'gargo-turnfix.json'))['items'] if (i.get('ok') or '--all' in sys.argv) and not i.get('no')]   # 넣는 것은 현장 확인(ok)만 · --all 은 후보 점검용(--dry 와 함께)
    assert DRY or '--all' not in sys.argv
    packs = [os.path.join(G, 'pk-six', 'core.json'), os.path.join(G, 'pk-seoul', 'core.json'), os.path.join(G, 'pack-six.json'), os.path.join(G, 'pack-seocho.json'), os.path.join(G, 'pack-seoul.json')]
    for main_ in packs:
        if not os.path.exists(main_): continue
        P = Pack(main_); res = collections.Counter(); left = []
        for it in items:
            r = P.fix(it); res[r] += 1
            if '서초' in it['name']: left.append('%s — %s %s→%s' % (r, it['name'], it['from'], it['to']))
        if not DRY: P.save()
        print(os.path.relpath(main_, ROOT), dict(res))
        for s in left: print('   ', s)


if __name__ == '__main__': main()
