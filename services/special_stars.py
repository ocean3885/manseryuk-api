from typing import List, Dict, Any

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']

# 천을귀인
CHEON_EUL_MAP = {
    '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
    '乙': ['子', '申'], '己': ['子', '申'],
    '丙': ['亥', '酉'], '丁': ['亥', '酉'],
    '壬': ['巳', '卯'], '癸': ['巳', '卯'],
    '辛': ['午', '寅']
}

# 문창귀인
MOON_CHANG_MAP = {
    '甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申',
    '己': '酉', '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'
}

# 삼합 기준 도화/역마/화개
DOHWA_MAP = {
    '申': '酉', '子': '酉', '辰': '酉',
    '寅': '卯', '午': '卯', '戌': '卯',
    '巳': '午', '酉': '午', '丑': '午',
    '亥': '子', '卯': '子', '未': '子'
}

YEOKMA_MAP = {
    '申': '寅', '子': '寅', '辰': '寅',
    '寅': '申', '午': '申', '戌': '申',
    '巳': '亥', '酉': '亥', '丑': '亥',
    '亥': '巳', '卯': '巳', '未': '巳'
}

HWAGAE_MAP = {
    '申': '辰', '子': '辰', '辰': '辰',
    '寅': '戌', '午': '戌', '戌': '戌',
    '巳': '丑', '酉': '丑', '丑': '丑',
    '亥': '未', '卯': '未', '未': '未'
}

# 양인살
YANG_IN_MAP = {
    '甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子'
}

# 홍염살
HONG_YEOM_MAP = {
    '甲': ['午'], '乙': ['午', '申'], '丙': ['寅'], '丁': ['未'],
    '戊': ['辰'], '己': ['辰'], '庚': ['戌'], '辛': ['酉'],
    '壬': ['子'], '癸': ['申']
}

# 백호살 및 괴강살 (간지 쌍)
BAEKHO_SET = {('甲', '辰'), ('乙', '未'), ('丙', '戌'), ('丁', '丑'), ('戊', '辰'), ('壬', '戌'), ('癸', '丑')}
GOEGANG_SET = {('戊', '戌'), ('庚', '辰'), ('庚', '戌'), ('壬', '辰')}

def analyze_special_stars(stems: List[str], branches: List[str]) -> List[Dict[str, Any]]:
    """
    일간/년간 및 일지/년지 기준으로 주요 길신(천을귀인, 문창귀인) 및
    핵심 신살(도화, 역마, 화개, 백호, 양인, 괴강, 홍염)을 추출합니다.
    """
    detected_stars: List[Dict[str, Any]] = []
    day_stem = stems[2]
    day_branch = branches[2]
    year_stem = stems[0]
    year_branch = branches[0]

    for i in range(4):
        p_key = PILLAR_KEYS[i]
        pos_name = f"{POSITION_NAMES[i]}지"
        stem_pos_name = f"{POSITION_NAMES[i]}주"
        b = branches[i]
        s = stems[i]

        # 1. 천을귀인 (天乙貴人)
        ce_targets = CHEON_EUL_MAP.get(day_stem, []) + CHEON_EUL_MAP.get(year_stem, [])
        if b in ce_targets:
            detected_stars.append({
                "name": "천을귀인",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "길신(吉神)",
                "description": "최고의 길신으로 위기 극복, 귀인의 조력, 명예와 신뢰를 상징"
            })

        # 2. 문창귀인 (文昌貴人)
        if b == MOON_CHANG_MAP.get(day_stem):
            detected_stars.append({
                "name": "문창귀인",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "길신(吉神)",
                "description": "총명함, 학문적 성취, 글재주 및 지적 창작 능력 우수"
            })

        # 3. 도화살 (桃花殺)
        dohwa_target = DOHWA_MAP.get(day_branch) or DOHWA_MAP.get(year_branch)
        if b == dohwa_target:
            detected_stars.append({
                "name": "도화살",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "신살(神殺)",
                "description": "사람을 끄는 대중적 매력, 예술적 끼, 인기와 화제성"
            })

        # 4. 역마살 (驛馬殺)
        yeokma_target = YEOKMA_MAP.get(day_branch) or YEOKMA_MAP.get(year_branch)
        if b == yeokma_target:
            detected_stars.append({
                "name": "역마살",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "신살(神殺)",
                "description": "활동 반경의 확장, 이동/이직운, 해외 교류 및 적극적 추진력"
            })

        # 5. 화개살 (華蓋殺)
        hwagae_target = HWAGAE_MAP.get(day_branch) or HWAGAE_MAP.get(year_branch)
        if b == hwagae_target:
            detected_stars.append({
                "name": "화개살",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "신살(神殺)",
                "description": "예술적 감수성, 철학·인문학적 통찰, 전문 기술 및 재생/복구 능력"
            })

        # 6. 양인살 (羊刃殺)
        if b == YANG_IN_MAP.get(day_stem):
            detected_stars.append({
                "name": "양인살",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "신살(神殺)",
                "description": "강력한 결단력과 카리스마, 전문 분야의 독보적 칼자루를 쥠"
            })

        # 7. 홍염살 (紅艶殺)
        if b in HONG_YEOM_MAP.get(day_stem, []):
            detected_stars.append({
                "name": "홍염살",
                "pillar": p_key,
                "position": pos_name,
                "char": b,
                "type": "신살(神殺)",
                "description": "자연스러운 친화력과 다정한 이성 매력, 호감형 인상"
            })

        # 8. 백호살 (白虎殺)
        if (s, b) in BAEKHO_SET:
            detected_stars.append({
                "name": "백호살",
                "pillar": p_key,
                "position": stem_pos_name,
                "char": f"{s}{b}",
                "type": "특수신살",
                "description": "강한 집중력과 프로페셔널한 돌파력, 위기를 기회로 바꾸는 힘"
            })

        # 9. 괴강살 (魁罡殺)
        if (s, b) in GOEGANG_SET:
            detected_stars.append({
                "name": "괴강살",
                "pillar": p_key,
                "position": stem_pos_name,
                "char": f"{s}{b}",
                "type": "특수신살",
                "description": "엄청난 총명함과 리더십, 대담한 배포와 독립적 추진력"
            })

    return detected_stars
