# -*- coding: utf-8 -*-
"""가르고 「지금 위치」 알약용 서울 행정동 경계 — gargo/dong-seoul.json (2026-10-15 · 코워크 결과 B-2 「내 차 밑 지금 위치 알약 — 출동 무전 보고용」)

원자료 = 통계청 SGIS 행정동 경계를 가공한 vuski/admdongkor HangJeongDong_ver20260701(공공누리 제1유형 · 출처 표시) — 지식베이스/13_관할경계/원자료/hjd20260701.geojson
서울(11) 행정동만 · 꼭짓점 줄이기(Douglas-Peucker 약 8m) · 좌표는 경도·위도 ×1e5 정수
  py -3.12 -X utf8 tools/gargo/dong-bake.py
"""
import os, json, math, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(os.path.dirname(ROOT), '13_관할경계', '원자료', 'hjd20260701.geojson')
OUT = os.path.join(ROOT, 'gargo', 'dong-seoul.json')
TOL = 0.00008


def dp(P, tol):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy) or 1e-12
    best, bi = -1, 0
    for i in range(1, len(P) - 1):
        d = abs(dy * (P[i][0] - a[0]) - dx * (P[i][1] - a[1])) / L
        if d > best:
            best, bi = d, i
    if best <= tol:
        return [a, b]
    return dp(P[:bi + 1], tol)[:-1] + dp(P[bi:], tol)


def main():
    j = json.load(open(SRC, encoding='utf-8'))
    out = []
    for f in j['features']:
        pr = f['properties']; cd = str(pr.get('adm_cd2') or pr.get('adm_cd') or '')
        if not cd.startswith('11'):
            continue
        nm = pr.get('adm_nm', '').replace('서울특별시 ', '')
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        rings = []
        for poly in polys:
            ring = poly[0]; m = max(range(len(ring)), key=lambda i: (ring[i][0] - ring[0][0]) ** 2 + (ring[i][1] - ring[0][1]) ** 2)   # 닫힌 고리는 가장 먼 점에서 둘로 나눠 줄인다(처음 = 끝이라 한 번에 하면 다 사라진다)
            r = dp(ring[:m + 1], TOL)[:-1] + dp(ring[m:], TOL)
            if len(r) >= 4:
                rings.append([v for p in r for v in (round(p[0] * 1e5), round(p[1] * 1e5))])
        if rings:
            out.append([nm, rings])
    doc = {'schema': 'tg-gargo-dong/1', 'made': datetime.date.today().isoformat(),
           'source': '통계청 통계지리정보서비스(SGIS) 행정동 경계를 가공한 vuski/admdongkor HangJeongDong_ver20260701 — 공공누리 제1유형(출처 표시) · 굽는 도구 tools/gargo/dong-bake.py',
           'fields': 'd[[「구 동」 이름, [[경도×1e5, 위도×1e5, …] 고리 …]]] · 꼭짓점 줄임 약 8m(경계 가까이는 틀릴 수 있다)', 'd': out}
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print('→', OUT, len(out), '동', os.path.getsize(OUT), 'B')


if __name__ == '__main__':
    main()
