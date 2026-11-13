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

# 기존 조합표의 출처 기준을 명시한다. 새 학파 규칙을 합성하지 않는다.
BRANCH_STAR_RULES = (
    ('천을귀인', CHEON_EUL_MAP, ((2, 'stem'), (0, 'stem')), '길신(吉神)',
     '조력과 보호의 상징', 'special_star:cheon_eul:year_day_stem_v1'),
    ('문창귀인', MOON_CHANG_MAP, ((2, 'stem'),), '길신(吉神)',
     '학문과 문예의 상징', 'special_star:moon_chang:day_stem_v1'),
    ('도화살', DOHWA_MAP, ((2, 'branch'), (0, 'branch')), '신살(神殺)',
     '교류와 주목의 상징', 'special_star:dohwa:year_day_branch_v2'),
    ('역마살', YEOKMA_MAP, ((2, 'branch'), (0, 'branch')), '신살(神殺)',
     '이동과 활동의 상징', 'special_star:yeokma:year_day_branch_v2'),
    ('화개살', HWAGAE_MAP, ((2, 'branch'), (0, 'branch')), '신살(神殺)',
     '예술과 사색의 상징', 'special_star:hwagae:year_day_branch_v2'),
    ('양인살', YANG_IN_MAP, ((2, 'stem'),), '신살(神殺)',
     '강한 기세와 결단의 상징', 'special_star:yang_in:day_stem_v1'),
    ('홍염살', HONG_YEOM_MAP, ((2, 'stem'),), '신살(神殺)',
     '친화와 매력의 상징', 'special_star:hong_yeom:day_stem_v1'),
)
PILLAR_STAR_RULES = (
    ('백호살', BAEKHO_SET, '강한 기세의 상징', 'special_star:baekho:own_pillar_v1'),
    ('괴강살', GOEGANG_SET, '강한 기세와 독립성의 상징', 'special_star:goegang:own_pillar_v1'),
)


def analyze_special_stars(stems: List[str], branches: List[str]) -> List[Dict[str, Any]]:
    """등록 조합을 탐지하고 기준 글자를 제공한다. 설명은 전통적 상징이다.

    천을은 일간·년간, 도화·역마·화개는 일지·년지를 각각 검사한다.
    문창·양인·홍염은 일간, 백호·괴강은 각 기둥의 간지 조합 기준을 유지한다.
    같은 신살·같은 대상 위치는 한 항목으로 묶고 일치하는 기준은 모두 보존한다.
    """
    def basis(index, kind):
        char = (stems[index] if kind == 'stem' else branches[index]
                if kind == 'branch' else stems[index] + branches[index])
        suffix = {'stem': '간', 'branch': '지', 'pillar': '주'}[kind]
        return {'pillar': PILLAR_KEYS[index], 'kind': kind, 'char': char,
                'display_name': f'{POSITION_NAMES[index]}{suffix} {char}'}

    detected = []
    for i, branch in enumerate(branches):
        for name, mapping, sources, star_type, symbolism, rule_id in BRANCH_STAR_RULES:
            matches = []
            for index, kind in sources:
                source = basis(index, kind)
                targets = mapping.get(source['char'], ())
                if branch in targets:
                    matches.append(source)
            if matches:
                detected.append({
                    'name': name, 'pillar': PILLAR_KEYS[i],
                    'position': f'{POSITION_NAMES[i]}지', 'char': branch,
                    'type': star_type, 'rule_id': rule_id, 'basis': matches,
                    'interpretation_scope': 'traditional_symbolism',
                    'description': f'전통적 상징: {symbolism}.',
                })
        for name, combinations, symbolism, rule_id in PILLAR_STAR_RULES:
            if (stems[i], branch) in combinations:
                detected.append({
                    'name': name, 'pillar': PILLAR_KEYS[i],
                    'position': f'{POSITION_NAMES[i]}주', 'char': stems[i] + branch,
                    'type': '특수신살', 'rule_id': rule_id, 'basis': [basis(i, 'pillar')],
                    'interpretation_scope': 'traditional_symbolism',
                    'description': f'전통적 상징: {symbolism}.',
                })
    return detected
