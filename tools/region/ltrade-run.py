# -*- coding: utf-8 -*-
# 토지·공장창고 실거래 전국 받기 — 날마다 이어서(소유자 2026-11-16 「서울 경기 인천 순으로 전국을 커버한다」)
#   공공데이터포털 하루 한도(토지 약 1,000번 — 429)에 걸리면 멈추고 다음 날 이어 받는다(받은 달은 건너뛴다)
#   시도 하나를 다 받으면(토지·공장창고 모두) 굽고 권역 저장소에 올린다(publish-data push) · 진행은 07_API키/out/ltrade/_run.json
#   py -3.12 -X utf8 tools/region/ltrade-run.py          → 차례대로 받을 수 있는 만큼
#   py -3.12 -X utf8 tools/region/ltrade-run.py status   → 어디까지 왔나
import json, os, sys, subprocess, time, importlib.util
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sp = importlib.util.spec_from_file_location('lt', os.path.join(ROOT, 'tools', 'region', 'ltrade-bake.py')); LT = importlib.util.module_from_spec(sp); sp.loader.exec_module(LT)
ORDER = ['11', '41', '28', '51', '44', '43', '30', '36', '26', '27', '31', '47', '48', '12', '52', '50']   # 서울 · 경기 · 인천 → 강원·충청 → 경상 → 전라 → 제주(r/index.json 의 시도 코드)
RUN = os.path.join(LT.OUT, '_run.json')

def have(gu, pre): return sum(1 for ym in LT.months() if os.path.exists(os.path.join(LT.OUT, pre + '%s_%s.json' % (gu, ym))))
def status():
    IX = json.load(open(os.path.join(ROOT, 'data', 'r', 'index.json'), encoding='utf-8')); o = {}
    for sd in ORDER:
        G = [g['gu'] for g in IX['gus'] if g['gu'][:2] == sd]
        if G: o[sd] = [len(G), sum(1 for g in G if have(g, '') == LT.NM), sum(1 for g in G if have(g, 'ind_') == LT.NM)]
    return o

def prog():   # 공개 진행표 — 지도·data-check 가 읽는다(시도마다 구 수 · 다 받은 구 수 · 올렸나)
    st0 = json.load(open(RUN, encoding='utf-8')) if os.path.exists(RUN) else {'pub': []}
    doc = {'schema': 'tg-ltrade-progress/1', 'source': '국토교통부 토지 매매·공장 및 창고 등 매매 실거래가(공공데이터포털) — 받는 진행표', 'fields': 'sido = {시도 코드: [구 수, 토지 다 받은 구, 공장창고 다 받은 구, 권역 저장소에 올렸나 1|0]}', 'note': '하루 호출 한도 때문에 날마다 이어 받는다 · 차례 = order · 덜 받은 구는 지도에서 「아직 받지 않았습니다」', 'made': time.strftime('%Y-%m-%d'), 'order': ORDER, 'sido': {sd: v + [1 if sd in st0['pub'] else 0] for sd, v in status().items()}}
    json.dump(doc, open(os.path.join(ROOT, 'data', 'ltrade-progress.json'), 'w', encoding='utf-8', newline=chr(10)), ensure_ascii=False, separators=(',', ':'))

def main():
    st0 = json.load(open(RUN, encoding='utf-8')) if os.path.exists(RUN) else {'pub': []}
    if len(sys.argv) > 1 and sys.argv[1] == 'prog': prog(); return
    if len(sys.argv) > 1 and sys.argv[1] == 'status':
        for sd, v in status().items(): print(sd, '구', v[0], '토지', v[1], '공장창고', v[2], '올림' if sd in st0['pub'] else '')
        return
    stop = {}
    for pre, svc, fn in (('', 'LandTrade', 'fetch'), ('ind_', 'InduTrade', 'fetchind')):
        for sd in ORDER:
            s = status().get(sd)
            if not s or s[1 if pre == '' else 2] == s[0]: continue
            try: LT.fetch([sd], svc, pre)
            except Exception as e: stop[svc] = '%s 에서 멈춤: %s' % (sd, str(e)[:60]); print(stop[svc], flush=True); break
    done = status()
    for sd in ORDER:
        s = done.get(sd)
        if not s or sd in st0['pub'] or s[1] != s[0] or s[2] != s[0]: continue
        LT.build([sd])
        r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(ROOT, 'tools', 'region', 'publish-data.py'), 'push', sd], capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(sd, '올림' if r.returncode == 0 else '올리기 실패', (r.stdout or '').strip().split('\n')[-1][:120], flush=True)
        if r.returncode == 0: st0['pub'].append(sd)
        else: break
    st0['last'] = time.strftime('%Y-%m-%d %H:%M'); st0['stop'] = stop
    json.dump(st0, open(RUN, 'w', encoding='utf-8'), ensure_ascii=False)
    prog()
    for sd, v in status().items(): print(sd, '구', v[0], '토지', v[1], '공장창고', v[2], '올림' if sd in st0['pub'] else '')

if __name__ == '__main__':
    main()
