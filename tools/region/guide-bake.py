# -*- coding: utf-8 -*-
# 데이터 압축지도 — 📖 사용설명서 자료 data/guide.json (소유자 2026-10-18 「사용설명서를 시각적으로 · 뭘 알 수 있는지 뭘 할 수 있는지 먼저 · 사용법을 찾게 · 자료를 나열하고 어떻게 만들고 무슨 자료를 썼고 뭘 알 수 있는지」)
#   지도 코드(js/map2d.js)에서 그대로 뽑는다 — 레이어 목록(이름·기본 켜짐) · 레이어 메뉴 차례(CATS: 탭 › 묶음 › 갈래) · ❓ 설명(LHELP) · 🧰 도구(TOOLS) — 그래서 설명서가 지도와 어긋나지 않는다
#   + data/ai-catalog.json(자료 파일마다 출처·칸·비고 — ai-guide-bake 가 만든 것) + 아래 TASKS(할 수 있는 일 · 사람이 쓴 것)
#   지도를 고치거나 자료를 더하면 ai-guide-bake 다음에 이것을 돌린다(1초) — guide.html 이 이 파일을 읽는다
#   py -3.12 -X utf8 tools/region/guide-bake.py
import io, os, re, json, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 할 수 있는 일 — [그림, 이름, 무엇을 알 수 있나, 어디서(차례), 켜 볼 레이어 키(없으면 빈칸)]
TASKS = [
    ['🗺', '지역 고르기 · 찾기', '전국 시도·시군구·동 어디든 그 자리로 간다. 장소·교차로·나들목 이름으로도 찾는다.', ['위 「📍 지역 고르기」', '또는 🔍 찾기'], ''],
    ['🏘', '이 동네 한눈에', '동을 누르면 주민·가구·연령, 가게 구성, 사고, 대중교통, 반려동물 업체, 구의 집값·구매력까지 한 카드에 모아 보인다. 「📝 이 지역 설명」은 숫자를 글로 풀어 읽는다.', ['지도에서 동(행정동)을 누른다'], 'dong'],
    ['🚦', '교차로 신호 보기', '교차로마다 방향별 녹색·적색 초, 주기, 지금 몇 초 남았는지(받은 값으로 이어 센 추정)를 본다. 받은 값이 없는 시각은 경찰청 계획으로 대신하고 그렇다고 밝힌다.', ['레이어', '🚓 경찰업무', '🚦 교통', '신호·교차로', '🚦 신호 주기'], 'sig'],
    ['🚗', '사고가 많은 곳', '교차로별 사고, 10년 사고 칸, 사망사고, 도로교통공단 다발지·음주 다발지를 겹쳐 본다. 순찰·단속 자리를 고를 때 쓴다.', ['레이어', '🚓 경찰업무', '🚦 교통', '교통사고'], 'acc'],
    ['📸', '단속 카메라 · 주정차 CCTV', '무인 단속 카메라(과속·신호)와 불법주정차 단속 CCTV 자리를 본다.', ['레이어', '🚓 경찰업무', '🚦 교통'], 'cam'],
    ['👮', '관할 · 관서', '경찰서 관할 경계(반포동은 현장 기준), 지구대·파출소, 소방서·응급실을 본다.', ['레이어', '🚓 경찰업무', '👮 지역경찰', '관할·관서'], 'jurk'],
    ['🌙', '야간 순찰 참고', '주점·노래방·숙박과 안심귀갓길(CCTV·비상벨·보안등)을 겹쳐 밤에 볼 자리를 고른다.', ['레이어', '🚓 경찰업무', '👮 지역경찰', '야간 순찰'], 'bar'],
    ['🚌', '사람 · 차 흐름', '버스·지하철 시간대 승하차, 역 붐빔, 실시간 인파, 교통량 지점의 도심 쪽·바깥 쪽 대수를 지도 시각에 맞춰 본다.', ['레이어', '👥 인구·생활', '🚶 이동·동선'], 'volp'],
    ['📡', '지금 교통 · 날씨', '실시간 돌발·소통·CCTV·날씨·레이더(켜는 층 — 켤 때만 바깥 서비스에 묻는다).', ['레이어', '⛅ 날씨·실시간'], ''],
    ['🌧', '큰비 · 눈 · 더위', '침수 흔적·침수 이력 도로·지하차도, 결빙 우려·제설함, 무더위·한파 쉼터를 본다.', ['레이어', '⛅ 날씨·실시간', '⛅ 계절 위험'], 'flt'],
    ['💳', '상권 · 부동산 · 세금 통계', '카드 매출, 상권 분석, 실거래·공시지가, 집값 흐름, 시군구 생활업종 증감·구매력(시군구 배경값)을 본다.', ['레이어', '💳 상권·부동산'], 'rone'],
    ['📐', '반경 분석', '한 자리 둘레(반경)의 사람·가게·사고를 잰다.', ['🧰 도구', '📐 반경 분석'], ''],
    ['🏪', '창업 자리 찾기 · 손익 계산', '업종을 골라 자리마다 견주고, 매출·비용을 넣어 손익을 어림한다.', ['🧰 도구', '🏪 창업 자리 찾기'], ''],
    ['🚨', '신고 차량 예측', '신고 시각·방향을 넣으면 그 차가 1·2·3·5분 안에 닿을 수 있는 길을 색으로 보인다(일반·도주 가정).', ['🧰 도구', '🚨 신고 차량 예측'], ''],
    ['🔒', '중요업무 시각표', '출발·경유·도착을 찍으면 길을 따라 교차로마다 통과 예정 시각(예상·가장 이른)을 낸다. 이 기기 안에서만 셈하고 저장·전송하지 않는다.', ['🧰 도구', '🚨 신고 차량 예측', '🔒 중요업무'], ''],
    ['🍺', '음주운전 흐름', '술자리에서 집으로 가는 길목을 어림해 단속 자리를 고르는 참고로 쓴다.', ['🧰 도구', '🍺 음주운전 흐름'], ''],
    ['🧾', '세금 계산', '부동산 보유세·양도세를 어림한다(참고용).', ['🧰 도구', '🧾 세금 계산'], ''],
    ['📥', '지역 받기(통신 없을 때)', '미리 지역 자료를 받아 두면 통신이 안 되는 곳에서도 지도를 쓴다.', ['🧰 도구', '📥 지역 받기'], ''],
    ['🧭', '네비 가르고', '신호를 아는 길 안내(서초 등 시험판) — 교차로 신호·통과 가능 속도를 함께 본다.', ['🧰 도구', '🧭 네비 가르고'], ''],
    ['❓', '이 레이어가 뭐지?', '레이어 이름 옆 ❓ 를 누르면 무엇을 보여 주고 어떻게 읽는지, 출처와 한계가 나온다. 범례(📖)는 색과 크기의 뜻.', ['레이어', '이름 옆 ❓'], ''],
]


def js_list(src, start_pat):
    i = src.index(start_pat); j = i + len(start_pat) - 1; d = 0
    for k in range(j, len(src)):
        if src[k] == '[': d += 1
        elif src[k] == ']':
            d -= 1
            if d == 0: return src[j:k + 1]
    raise ValueError(start_pat)


def to_json(js):
    t = re.sub(r"/\*.*?\*/", '', js, flags=re.S)
    t = re.sub(r"'((?:[^'\\]|\\.)*)'", lambda m: json.dumps(m.group(1).replace("\\'", "'")), t)
    t = re.sub(r",\s*\]", ']', t)
    return json.loads(t)


def main():
    s = io.open(os.path.join(ROOT, 'js', 'map2d.js'), encoding='utf-8').read()
    L = re.findall(r"\['([a-zA-Z0-9]+)', '([^']+)', (true|false), '([^']+)', \d\]", s)
    layers = {k: {'nm': n, 'on': on == 'true', 'grp': g} for k, n, on, g in L}
    i = s.index('  var LHELP = {'); k = s.find('\n  };', i)
    helps = dict((a, b.replace("\\'", "'")) for a, b in re.findall(r"\n\s+([a-zA-Z0-9]+): '((?:[^'\\]|\\.)*)'", s[i:k]))
    cats = to_json(js_list(s, 'var CATS = ['))
    tools = [t for t in to_json(js_list(s, 'var TOOLS = [')) if t[0] != 'g']
    ver = re.findall(r"map2d\.js\?v=([0-9.]+)", io.open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read())[0]
    cat = json.load(open(os.path.join(ROOT, 'data', 'ai-catalog.json'), encoding='utf-8'))
    files = [{'f': x.get('file'), 's': x.get('source') or '', 'k': x.get('fields') or '', 'n': x.get('note') if isinstance(x.get('note'), str) else ' · '.join(x.get('note') or []) if isinstance(x.get('note'), list) else '', 'b': x.get('bytes') or 0, 'm': x.get('made') or ''} for x in cat['files']]
    where = {}
    cats = [t for t in cats if t[2]]   # 「전체」 탭(목록 없음)은 뺀다
    for top in cats:
        for grp in top[2]:
            for sub in grp[2]:
                for key in sub[1]: where.setdefault(key, []).append([top[1], grp[1], sub[0]])
    out = {'schema': 'tg-guide/1', 'made': datetime.date.today().isoformat(), 'ver': ver, 'tasks': TASKS, 'tools': tools, 'cats': cats, 'layers': layers, 'help': helps, 'where': where, 'files': files,
           'n': {'layers': len(layers), 'help': sum(1 for k2 in layers if k2 in helps), 'files': len(files)}}
    json.dump(out, open(os.path.join(ROOT, 'data', 'guide.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    miss = [k2 for k2 in layers if k2 not in helps]
    print('레이어', len(layers), '· 설명 있음', out['n']['help'], '· 설명 없음', len(miss), miss[:12], '· 자료', len(files), '· 도구', len(tools), '· 판', ver)


if __name__ == '__main__':
    main()
