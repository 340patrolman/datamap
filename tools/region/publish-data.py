# -*- coding: utf-8 -*-
# 데이터 압축지도 v2.6.0 — 지역 자료를 권역별 저장소로 내보낸다(전국 확장 설계서 · 소유자 2026-10-05 「분리하자」)
#   굽는 도구들은 지금처럼 datamap/data/r/<구>/ 에 굽는다(이 폴더는 이제 git 에 안 올림 — .gitignore) → 이 도구가
#   ① data/r/manifest-<시도>.json (이 PC 시험용) · data/regions.json(지도 저장소에 올라감) 을 만들고
#   ② ../datamap-data-<권역>/ (저장소 클론)에 r/<구>/ 를 그대로 복사 + manifest.json · index.html(noindex) · robots.txt · .nojekyll · README.md
#   ③ 기록을 쌓지 않는다 — 고아 커밋 하나로 갈아 끼우고 강제 푸시(자료를 다시 구울 때마다 git 이 불어나지 않게 · 지난 판은 남지 않는다)
#   GitHub Pages 한도(공식 문서 2026-10-05 확인): 저장소 권장 1GB · 게시 사이트 최대 1GB · 대역폭 월 100GB(느슨) · 빌드 시간당 10번(느슨) · 배포 10분
#   py -3.12 -X utf8 tools/region/publish-data.py manifest        → 목록만
#   py -3.12 -X utf8 tools/region/publish-data.py push 11 41      → 그 시도 저장소로 내보내기(저장소가 없으면 만들고 Pages 를 켠다)
import json, os, sys, shutil, subprocess, time
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KB = os.path.dirname(ROOT); R = os.path.join(ROOT, 'data', 'r'); OWNER = '340patrolman'
REG = {'12': ('전남광주', 'jeolla'), '11': ('서울', 'seoul'), '41': ('경기', 'gyeonggi'), '28': ('인천', 'incheon'), '51': ('강원', 'gangwon'), '30': ('대전', 'chungcheong'), '36': ('세종', 'chungcheong'),
       '43': ('충북', 'chungcheong'), '44': ('충남', 'chungcheong'), '26': ('부산', 'gyeongsang'), '27': ('대구', 'gyeongsang'), '31': ('울산', 'gyeongsang'), '47': ('경북', 'gyeongsang'),
       '48': ('경남', 'gyeongsang'), '29': ('광주', 'jeolla'), '46': ('전남', 'jeolla'), '52': ('전북', 'jeolla'), '50': ('제주', 'jeju')}

def layer_meta(IX, sido):
    meta = {}
    for g in IX['gus']:
        if g['gu'][:2] != sido: continue
        for k in (g.get('bytes') or {}):
            if k in meta: continue
            f = os.path.join(R, g['gu'], k + '.json'); src = asof = ''
            try:
                j = json.load(open(f, encoding='utf-8')); s = j.get('source')
                src = (s if isinstance(s, str) else json.dumps(s, ensure_ascii=False))[:240] if s else ''
                asof = j.get('baked') or j.get('stdrYm') or j.get('ym') or j.get('collected') or ''
            except Exception: pass
            meta[k] = {'d': IX['layers'].get(k, k), 'src': src, 'asof': asof}
    return meta

def manifest():
    IX = json.load(open(os.path.join(R, 'index.json'), encoding='utf-8')); regs = []
    for sido in sorted({g['gu'][:2] for g in IX['gus']}):
        gus = [g for g in IX['gus'] if g['gu'][:2] == sido]; nm, rp = REG[sido]
        box = [min(g['box'][0] for g in gus), min(g['box'][1] for g in gus), max(g['box'][2] for g in gus), max(g['box'][3] for g in gus)]
        tot = sum(sum((g.get('bytes') or {}).values()) for g in gus)
        m = {'schema': 'tg-manifest/1', 'sido': sido, 'name': nm, 'built': time.strftime('%Y-%m-%d'), 'note': IX.get('note', ''), 'layers': layer_meta(IX, sido), 'gus': gus, 'bytes': tot}
        json.dump(m, open(os.path.join(R, 'manifest-%s.json' % sido), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        regs.append({'sido': sido, 'name': nm, 'repo': 'datamap-data-' + rp, 'box': [round(x, 4) for x in box], 'gus': len(gus), 'bytes': tot})
        print(sido, nm, len(gus), '구', round(tot / 1048576, 1), 'MB')
    json.dump({'schema': 'tg-regions/1', 'note': '권역 → 자료 저장소(https://340patrolman.github.io/<repo>/) · 지도는 manifest.json 을 읽고 화면에 걸린 구의 r/<구>/<층>.json 을 받는다', 'regions': regs},
              open(os.path.join(ROOT, 'data', 'regions.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    return regs

README = '''# {repo}

데이터 압축지도(https://340patrolman.github.io/datamap/)가 읽는 **{name} 지역 자료**다. 사람이 볼 페이지가 아니다(검색 차단).
- 구성: `manifest.json`(시군구 → 층 · 바이트 · 상자) · `r/<시군구 5자리>/<층>.json`
- 출처·라이선스: 파일마다 `source` 칸에 적었다(공공데이터포털·서울 열린데이터광장·경기데이터드림·통계청 SGIS·국토교통부·도로교통공단 TAAS·OpenStreetMap(ODbL) 등). 공공누리 표시 조건을 따른다.
- 기록을 쌓지 않는다: 자료를 다시 구우면 커밋 하나로 갈아 끼운다(지난 판은 지도 저장소 `tools/` 로 다시 구울 수 있다).
'''

def git(cwd, *a, check=True):
    r = subprocess.run(['git'] + list(a), cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    if check and r.returncode: raise RuntimeError('git %s: %s' % (' '.join(a), r.stderr[-400:]))
    return r.stdout

def push(sidos):
    regs = {x['sido']: x for x in manifest()}
    repos = {}
    for sd in sidos: repos.setdefault(regs[sd]['repo'], []).append(sd)
    for repo in repos:   # v2.39.0 한 저장소에 시도가 여럿(충청·경상·전라)이면 늘 다 같이 — 하나만 올리면 고아 커밋이 나머지 시도를 지운다(2026-10-06 공시지가 큐에서 실제로 일어남)
        repos[repo] = sorted(x for x in regs if regs[x]['repo'] == repo)
    for repo, sds in repos.items():
        d = os.path.join(KB, repo)
        ex = subprocess.run(['gh', 'repo', 'view', OWNER + '/' + repo], capture_output=True, text=True).returncode == 0
        if not ex:
            subprocess.run(['gh', 'repo', 'create', OWNER + '/' + repo, '--public', '--description', '데이터 압축지도 지역 자료(%s) — 지도 앱이 읽는 자료 · 검색 차단' % '·'.join(regs[s]['name'] for s in sds)], check=True)
        if not os.path.isdir(os.path.join(d, '.git')):
            os.makedirs(d, exist_ok=True); git(d, 'init', '-q'); git(d, 'remote', 'add', 'origin', 'https://github.com/%s/%s.git' % (OWNER, repo))
            git(d, 'config', 'core.autocrlf', 'false')
        for kk in ('user.name', 'user.email'):   # 작성자 = 지도 저장소와 같은 사람
            v = git(ROOT, 'config', kk, check=False).strip()
            if v: git(d, 'config', kk, v)
        for x in os.listdir(d):
            if x == '.git': continue
            p = os.path.join(d, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
        gus = []; layers = {}; tot = 0
        for sd in sds:
            m = json.load(open(os.path.join(R, 'manifest-%s.json' % sd), encoding='utf-8')); gus += m['gus']; layers.update(m['layers']); tot += m['bytes']
            for g in m['gus']: shutil.copytree(os.path.join(R, g['gu']), os.path.join(d, 'r', g['gu']))
        if len(sds) == 1: shutil.copy(os.path.join(R, 'manifest-%s.json' % sds[0]), os.path.join(d, 'manifest.json'))
        else: json.dump({'schema': 'tg-manifest/1', 'sido': '+'.join(sds), 'built': time.strftime('%Y-%m-%d'), 'layers': layers, 'gus': gus, 'bytes': tot}, open(os.path.join(d, 'manifest.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, separators=(',', ':'))
        name = '·'.join(regs[s]['name'] for s in sds)
        open(os.path.join(d, 'README.md'), 'w', encoding='utf-8', newline='\n').write(README.format(repo=repo, name=name))
        open(os.path.join(d, 'robots.txt'), 'w', encoding='utf-8', newline='\n').write('User-agent: *\nDisallow: /\n')
        open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n').write('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>%s</title><p>데이터 압축지도 지역 자료(%s) — <a href="https://340patrolman.github.io/datamap/">지도</a></p>' % (repo, name))
        open(os.path.join(d, '.nojekyll'), 'w').close()
        git(d, 'checkout', '-q', '--orphan', 'tmp_pub'); git(d, 'add', '-A')
        git(d, 'commit', '-q', '-m', '%s 지역 자료 %s (%.0fMB · 기록을 쌓지 않는 커밋 하나)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' % (name, time.strftime('%Y-%m-%d'), tot / 1048576))
        git(d, 'branch', '-D', 'main', check=False); git(d, 'branch', '-m', 'main'); git(d, 'push', '-q', '-f', 'origin', 'main')
        if not ex or subprocess.run(['gh', 'api', 'repos/%s/%s/pages' % (OWNER, repo)], capture_output=True).returncode:
            subprocess.run(['gh', 'api', '-X', 'POST', 'repos/%s/%s/pages' % (OWNER, repo), '-f', 'source[branch]=main', '-f', 'source[path]=/'], capture_output=True)
        print('올림', repo, name, len(gus), '구', round(tot / 1048576, 1), 'MB')

def tiles():   # v2.8.0 바탕 조각(data/base/t/ · 전국 1,996장 136MB) → datamap-tiles 저장소 · 목록·개관·시군구는 지도 저장소에 남김
    repo = 'datamap-tiles'; d = os.path.join(KB, repo); src = os.path.join(ROOT, 'data', 'base', 't')
    if subprocess.run(['gh', 'repo', 'view', OWNER + '/' + repo], capture_output=True).returncode:
        subprocess.run(['gh', 'repo', 'create', OWNER + '/' + repo, '--public', '--description', '데이터 압축지도 바탕 지도 조각(OpenStreetMap · ODbL) — 지도 앱이 읽는 자료 · 검색 차단'], check=True); new = True
    else: new = False
    if not os.path.isdir(os.path.join(d, '.git')):
        os.makedirs(d, exist_ok=True); git(d, 'init', '-q'); git(d, 'remote', 'add', 'origin', 'https://github.com/%s/%s.git' % (OWNER, repo)); git(d, 'config', 'core.autocrlf', 'false')
        for kk in ('user.name', 'user.email'):
            v = git(ROOT, 'config', kk, check=False).strip()
            if v: git(d, 'config', kk, v)
    for x in os.listdir(d):
        if x == '.git': continue
        p = os.path.join(d, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    shutil.copytree(src, os.path.join(d, 't')); shutil.copy(os.path.join(ROOT, 'data', 'base', 'index.json'), os.path.join(d, 'index.json'))
    open(os.path.join(d, 'README.md'), 'w', encoding='utf-8', newline='\n').write('# datamap-tiles\n\n데이터 압축지도(https://340patrolman.github.io/datamap/) 바탕 지도 8km 조각 — © OpenStreetMap contributors (ODbL) · Geofabrik south-korea · 교차로 이름 일부 서울 C-ITS. 사람이 볼 페이지가 아니다(검색 차단). 기록을 쌓지 않는 커밋 하나로 갈아 끼운다.\n')
    open(os.path.join(d, 'robots.txt'), 'w', encoding='utf-8', newline='\n').write('User-agent: *\nDisallow: /\n')
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8', newline='\n').write('<!doctype html><meta charset="utf-8"><meta name="robots" content="noindex,nofollow"><title>datamap-tiles</title><p>데이터 압축지도 바탕 조각 — <a href="https://340patrolman.github.io/datamap/">지도</a></p>')
    open(os.path.join(d, '.nojekyll'), 'w').close()
    git(d, 'checkout', '-q', '--orphan', 'tmp_pub'); git(d, 'add', '-A')
    n = len(os.listdir(src)); b = sum(os.path.getsize(os.path.join(src, f)) for f in os.listdir(src))
    git(d, 'commit', '-q', '-m', '바탕 조각 %d장 %s (%.0fMB · 기록을 쌓지 않는 커밋 하나)\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>' % (n, time.strftime('%Y-%m-%d'), b / 1048576))
    git(d, 'branch', '-D', 'main', check=False); git(d, 'branch', '-m', 'main'); git(d, 'push', '-q', '-f', 'origin', 'main')
    if new or subprocess.run(['gh', 'api', 'repos/%s/%s/pages' % (OWNER, repo)], capture_output=True).returncode:
        subprocess.run(['gh', 'api', '-X', 'POST', 'repos/%s/%s/pages' % (OWNER, repo), '-f', 'source[branch]=main', '-f', 'source[path]=/'], capture_output=True)
    print('올림', repo, n, '장', round(b / 1048576, 1), 'MB')

if __name__ == '__main__':
    {'manifest': lambda: manifest(), 'tiles': tiles}.get(sys.argv[1], lambda: push(sys.argv[2:]))()
