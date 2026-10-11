# -*- coding: utf-8 -*-
# 데이터 압축지도 — 🌊 홍수위험지도(환경부 한강홍수통제소 · 홍수위험지도 정보제공포털 data.floodmap.go.kr)를 **저장소 밖**에 받아 두는 도구(소유자 2026-10-11 「저장하고 충분한 지도와 데이터를 만들자」)
#   ⚠ 이 자료는 **공공누리 4유형(출처표시 · 상업적 이용금지 · 변경금지)** — 가공한 결과를 공개 저장소·공개 지도에 싣지 않는다.
#      지도에는 「켜는 층」으로 포털의 그림을 **그대로** 띄운다(열쇠는 기기마다) · 이 도구가 받은 그림과 그것으로 센 값은 ../07_API키/out/floodmap/ 에만 둔다(소유자 업무용)
#   WMS: https://data.floodmap.go.kr/api/wms-service/<서비스>?ServiceKey=…&Freq=…&SAREA_CD=1&Format=image/png&Bbox=…&width=…&height=…&transparent=TRUE&srs=EPSG:4326
#     서비스 = sa-ntn-wms(권역 · 국가하천 범람) · sa-rgn-wms(지방하천 범람) · sa-cty-wms(도시침수) · adm-*(행정구역 STDG_SGG_CD) · rv-*(유역 SBSN_CD)
#     ⚠ 문서는 EPSG:4326 이면 Bbox = (ymin, xmin, ymax, xmax)라고 하지만 **실제로는 (xmin, ymin, xmax, ymax)** 로 보내야 그림이 온다(2026-10-11 실측 — 문서대로 보내면 빈 그림)
#     없는 빈도는 그림 대신 XML(LayerNotDefined)이 온다 — 도시침수 500·기왕최대 · 지방하천 500·기왕최대는 없었다
#   색 = 침수심: N330 0.5m 미만 (253,251,199) · N331 0.5~1m (230,255,153) · N332 1~2m (56,254,253) · N333 2~5m (206,154,254) · N334 5m 이상 (206,63,135) — 원본 범례 색 그대로 읽는다
#   열쇠 = ../07_API키/keys.json 의 "floodmap"(찍지 않는다 · 커밋하지 않는다)
#   py -3.12 -X utf8 tools/region/floodmap-fetch.py            → 서초구 + 2km 상자 · 3.5m 칸
#   py -3.12 -X utf8 tools/region/floodmap-fetch.py seoul      → 서울 전체 상자 · 10m 칸
import json, os, sys, io, time, datetime, urllib.request, urllib.parse
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); KB = os.path.dirname(ROOT); OUT = os.path.join(KB, '07_API키', 'out', 'floodmap')
PAL = [(253, 251, 199), (230, 255, 153), (56, 254, 253), (206, 154, 254), (206, 63, 135)]
LAYERS = [('cty', 'sa-cty-wms', ['030', '050', '080', '100']), ('rgn', 'sa-rgn-wms', ['050', '080', '100', '200']), ('ntn', 'sa-ntn-wms', ['100', '200', '500'])]
AREAS = {'seocho': ((126.955, 37.405, 127.115, 37.545), 0.00004, 0.000032), 'seoul': ((126.76, 37.41, 127.19, 37.71), 0.000112, 0.00009)}
def main(area='seocho'):
    K = json.load(open(os.path.join(KB, '07_API키', 'keys.json'), encoding='utf-8-sig'))['floodmap']; box, dx, dy = AREAS[area]
    W = int(round((box[2] - box[0]) / dx)); H = int(round((box[3] - box[1]) / dy)); T = 2000; os.makedirs(os.path.join(OUT, area), exist_ok=True); meta = {'area': area, 'box': box, 'w': W, 'h': H, 'dx': dx, 'dy': dy, 'got': datetime.date.today().isoformat(), 'layers': {}}
    for tag, svc, freqs in LAYERS:
        for fr in freqs:
            fn = os.path.join(OUT, area, '%s_%s.npz' % (tag, fr))
            if os.path.exists(fn): meta['layers']['%s_%s' % (tag, fr)] = 'ok'; continue
            cls = np.zeros((H, W), dtype=np.uint8); ok = True
            for y0 in range(0, H, T):
                for x0 in range(0, W, T):
                    w = min(T, W - x0); h = min(T, H - y0)
                    bb = (box[0] + x0 * dx, box[3] - (y0 + h) * dy, box[0] + (x0 + w) * dx, box[3] - y0 * dy)
                    q = {'ServiceKey': K, 'Freq': fr, 'SAREA_CD': '1', 'Format': 'image/png', 'Bbox': '%.6f,%.6f,%.6f,%.6f' % bb, 'width': str(w), 'height': str(h), 'transparent': 'TRUE', 'srs': 'EPSG:4326'}
                    b = None
                    for k in range(3):
                        try: b = urllib.request.urlopen(urllib.request.Request('https://data.floodmap.go.kr/api/wms-service/%s?%s' % (svc, urllib.parse.urlencode(q)), headers={'User-Agent': 'Mozilla/5.0'}), timeout=120).read(); break
                        except Exception as e: err = type(e).__name__; time.sleep(5)
                    if b is None: print(tag, fr, '못 받음', err); ok = False; break
                    if b[:4] != b'\x89PNG': print(tag, fr, '그림이 아님:', ('없는 층' if b'LayerNotDefined' in b else b[:120].decode('utf-8', 'replace'))); ok = False; break
                    a = np.asarray(Image.open(io.BytesIO(b)).convert('RGBA')).astype(np.int16); op = a[:, :, 3] > 100
                    d = np.stack([np.abs(a[:, :, :3] - np.array(p, dtype=np.int16)).sum(axis=2) for p in PAL], axis=2); c = d.argmin(axis=2).astype(np.uint8) + 1
                    c[~op] = 0; c[d.min(axis=2) > 60] = 0; cls[y0:y0 + h, x0:x0 + w] = c; time.sleep(0.6)
                if not ok: break
            if not ok: meta['layers']['%s_%s' % (tag, fr)] = 'none'; continue
            np.savez_compressed(fn, cls=cls); cnt = [int((cls == i).sum()) for i in range(1, 6)]; meta['layers']['%s_%s' % (tag, fr)] = 'ok'
            print(tag, fr, '칸 수(0.5m 미만 · 0.5~1 · 1~2 · 2~5 · 5m 이상)', cnt, '· 넓이 km² %.2f' % (sum(cnt) * dx * 88800 * dy * 111000 / 1e6))
    meta['note'] = '공공누리 4유형(출처표시 · 상업적 이용금지 · 변경금지) — 환경부 한강홍수통제소 홍수위험지도. 이 폴더의 것은 공개 저장소·공개 지도에 싣지 않는다. cls 0 = 없음 · 1~5 = 침수심 다섯 단계 · 줄 0 = 북쪽'
    json.dump(meta, open(os.path.join(OUT, area, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1); print('저장', os.path.join(OUT, area))
if __name__ == '__main__': main(*sys.argv[1:2])
