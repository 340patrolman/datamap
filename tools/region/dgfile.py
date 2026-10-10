# -*- coding: utf-8 -*-
# 공공데이터포털 「파일데이터」 받기(키 없이 · 포털 화면이 하는 순서 그대로) — 2026-10-10
#   상세 화면에서 내려받기 단추의 인자를 읽고 → /tcs/dss/selectFileDataDownload.do(파일 번호) → /cmm/cmm/check-limit.json(자동입력 방지가 뜨면 멈춘다 — 그때는 사람이 브라우저로) → /cmm/cmm/fileDownload.do
#   py -3.12 -X utf8 tools/region/dgfile.py <자료 번호> [받을 폴더]   → 받을 폴더(기본 07_API키/out/dg/<번호>/)에 원래 이름으로 + _meta.json(이름·수정일·이용허락·받은 날)
import json, os, re, sys, html, datetime, urllib.request, urllib.parse, http.cookiejar
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def main(pk, out=None):
    out = out or os.path.join(os.path.dirname(ROOT), '07_API키', 'out', 'dg', pk); os.makedirs(out, exist_ok=True)
    cj = http.cookiejar.CookieJar(); op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); ref = 'https://www.data.go.kr/data/%s/fileData.do' % pk
    H = {'User-Agent': 'Mozilla/5.0', 'Referer': ref, 'X-Requested-With': 'XMLHttpRequest'}
    t = op.open(urllib.request.Request(ref, headers={'User-Agent': 'Mozilla/5.0'}), timeout=60).read().decode('utf-8', 'replace')
    m = re.search(r"fn_fileDataDown\('(\d+)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)", t)
    if not m: print('내려받기 단추를 못 찾음(파일이 포털에 없고 바깥 주소로 가는 자료일 수 있다)', pk); return 1
    def cell(lbl):
        x = re.search(lbl + r'\s*</th>\s*<td[^>]*>(.*?)</td>', t, re.S); return re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', x.group(1)))).strip() if x else None
    title = re.search(r'<title>([^<|]+)', t); meta = {'id': pk, 'title': title.group(1).strip() if title else None, '수정일': cell('수정일'), '등록일': cell('등록일'), '이용허락범위': cell('이용허락범위'), '제공기관': cell('제공기관'), '전체 행': cell('전체 행'), '받은 날': datetime.date.today().isoformat(), 'url': ref}
    d = json.loads(op.open(urllib.request.Request('https://www.data.go.kr/tcs/dss/selectFileDataDownload.do', data=urllib.parse.urlencode({'publicDataDetailPk': m.group(2), 'publicDataPk': m.group(1), 'atchFileId': m.group(3), 'fileDetailSn': m.group(4), 'publicDataTyCode': 'PR0051'}).encode(), headers=H), timeout=60).read().decode('utf-8', 'replace'))
    if not d.get('status'): print('파일 번호를 못 받음', pk, str(d)[:200]); return 1
    a, sn = d['atchFileId'], d['fileDetailSn']
    lim = json.loads(op.open(urllib.request.Request('https://www.data.go.kr/cmm/cmm/check-limit.json', data=urllib.parse.urlencode({'atchFileId': a, 'fileDetailSn': sn}).encode(), headers=H), timeout=60).read().decode('utf-8', 'replace'))
    if lim.get('needCaptcha'): print('자동입력 방지가 떴다 — 브라우저에서 사람이 받아야 한다', ref); return 2
    r = op.open(urllib.request.Request('https://www.data.go.kr/cmm/cmm/fileDownload.do?atchFileId=%s&fileDetailSn=%s&dataNm=x' % (a, sn), headers={'User-Agent': 'Mozilla/5.0', 'Referer': ref}), timeout=600)
    cd = r.headers.get('Content-Disposition') or ''; fn = re.search(r'filename="?([^";]+)', cd); fn = fn.group(1) if fn else pk + '.bin'
    try: fn = fn.encode('latin-1').decode('utf-8')
    except Exception: pass
    fn = re.sub(r'[\\/:*?"<>|]', '_', urllib.parse.unquote(fn)); b = r.read(); open(os.path.join(out, fn), 'wb').write(b)
    meta['file'] = fn; meta['bytes'] = len(b); json.dump(meta, open(os.path.join(out, '_meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(pk, fn, len(b), '|', meta['title'], '| 수정', meta['수정일'], '| 이용허락', meta['이용허락범위']); return 0
if __name__ == '__main__': sys.exit(main(*sys.argv[1:3]))
