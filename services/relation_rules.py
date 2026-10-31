"""원국의 지지 관계·동주 자합·지지 작용 모델을 위한 단일 규칙 원본.

관계 후보와 조건, 실험적 수치 계수를 한곳에 둔다. 후보 오행과 계수는
합화 성립 또는 사건의 피해량을 의미하지 않는다.
"""

RULE_PROFILE = 'mangpa_project_provisional'
RULE_VERSION = '2.19.0'

# v3 방향별 잠재량은 기존 v2 계수를 재사용하는 잠정 상대 지표다.
# 각 방향: source_capacity = 해당 쌍의 상대를 제외하고 계산한 원천 지지 세력.
# interaction_intensity = round(source_capacity * distance_weight * coefficient, 4).
# target_exposure = round(interaction_intensity * source_capacity /
#                         (source_capacity + target_capacity), 4).
# target_exposure는 잠재 수용 지표이며 실제 손실·피해량이 아니다.
# 작용 성립 판정 전에는 applied_power_delta를 산출하지 않는다.
V3_RULE_VERSION = '3.8.0-draft'
V3_POTENTIAL_FORMULA_ID = 'branch:potential_source_distance_coefficient_v1'
V3_EXPOSURE_FORMULA_ID = 'branch:exposure_source_share_v1'
V3_UNSCORED_PAIR_TYPES = frozenset(('공합(拱合)', '암합(暗合)'))
# 같은 위치 쌍의 구조 관계가 active로 확정되면 생·극은 독립 작용에서 제외한다.
# 삼형은 세 지지 구조다. 자형은 인접한 같은 글자에서만 active지만
# 동일 오행 쌍이므로 독립 생·극 억제 대상이 없다.
# potential/conditional/candidate_only는 성립 확정이 아니다.
V3_ELEMENT_OVERRIDE_PAIR_TYPES = frozenset((
    'break', 'pierce', 'clash', 'combine', 'punishment',
))
V3_ELEMENT_OVERRIDE_RULE_ID = 'branch:active_pair_structure_overrides_element_v1'
PAIR_PRESENCE_ACTIVE_RULE_ID = 'branch:pair_presence_active_v1'
TRIPLE_PUNISHMENT_PRESENCE_RULE_ID = 'branch:triple_punishment_presence_active_v1'
ADJACENT_SELF_PUNISHMENT_RULE_ID = 'branch:adjacent_self_punishment_active_v1'
# 파·충·천·지세형은 쌍의 존재로, 육합은 인접 충 조건이 없을 때 active다.
# 삼형은 세 글자의 존재로, 자형은 인접한 동일 지지의 존재로 active다.
ACTIVE_PAIR_RELATION_TYPES = frozenset((
    '충(沖)', '파(破)', '천(穿)', '육합(六合)', '형(刑)',
))
PAIR_ELEMENT_OVERRIDE_REASON = 'active_pair_structure_overrides_element'

# 천간끼리의 관계 후보와 기존 극 강도.
STEM_COMBINATIONS = {
    ('甲', '己'): '土', ('乙', '庚'): '金', ('丙', '辛'): '水',
    ('丁', '壬'): '木', ('戊', '癸'): '火',
}
STEM_CONFLICTS = {('甲', '庚'), ('乙', '辛'), ('丙', '壬'), ('丁', '癸')}
STEM_RESTRAIN = {
    ('甲', '戊'): 1.0,
    ('乙', '戊'): 0.5,
    ('乙', '己'): 1.0,
    ('丙', '庚'): 1.0,
    ('丁', '庚'): 0.5,
    ('丁', '辛'): 1.0,
    ('戊', '壬'): 1.0,
    ('己', '壬'): 0.5,
    ('己', '癸'): 1.0,
    ('辛', '甲'): 0.5,
    ('癸', '丙'): 0.5,
}

# 지지 관계 후보. 키의 순서는 탐지 결과에 영향을 주지 않는다.
SIX_HAPS = {('子', '丑'): '土', ('寅', '亥'): '木', ('卯', '戌'): '火',
            ('辰', '酉'): '金', ('巳', '申'): '水', ('午', '未'): '土'}
# 충하는 글자가 합 사이에 있으면 합 작용을 억제한다. 합 밖에서 충할 지지에
# 인접하면 충과 합이 병존하므로 작용량을 유보하고, 충 개입이 없으면 합을 성립시킨다.
SIX_HAP_CONDITIONS = {
    'intervening_adjacent_clash': 'suppressed',
    'external_adjacent_clash': 'conditional',
}
CHUNGS = {('子', '午'), ('丑', '未'), ('寅', '申'),
          ('卯', '酉'), ('辰', '戌'), ('巳', '亥')}
SQUARE_HAPS = {
    ('寅', '卯', '辰'): {'element': '木', 'season': '봄', 'power_boost': 1.5},
    ('巳', '午', '未'): {'element': '火', 'season': '여름', 'power_boost': 1.5},
    ('申', '酉', '戌'): {'element': '金', 'season': '가을', 'power_boost': 1.5},
    ('亥', '子', '丑'): {'element': '水', 'season': '겨울', 'power_boost': 1.5},
}
THREE_HAPS = {
    ('寅', '午', '戌'): '火',
    ('亥', '卯', '未'): '木',
    ('申', '子', '辰'): '水',
    ('巳', '酉', '丑'): '金',
}
# 완성 삼합 후보의 구조 판정. 중신 중복은 학파별 해석 차이가 있어 보류한다.
# 중신·생지·성지에 인접한 충은 해당 국의 점수를 억제한다.
THREE_HAP_CONDITIONS = {
    'duplicate_middle': 'conditional',
    'adjacent_middle_clash': 'suppressed',
    'adjacent_birth_clash': 'suppressed',
    'adjacent_tomb_clash': 'suppressed',
}
HALF_HAPS = {
    ('寅', '午'): {'element': '火', 'type': '전반합', 'strength': 0.7},
    ('亥', '卯'): {'element': '木', 'type': '전반합', 'strength': 0.7},
    ('申', '子'): {'element': '水', 'type': '전반합', 'strength': 0.7},
    ('巳', '酉'): {'element': '金', 'type': '전반합', 'strength': 0.7},
    ('午', '戌'): {'element': '火', 'type': '후반합', 'strength': 0.6},
    ('卯', '未'): {'element': '木', 'type': '후반합', 'strength': 0.6},
    ('子', '辰'): {'element': '水', 'type': '후반합', 'strength': 0.6},
    ('酉', '丑'): {'element': '金', 'type': '후반합', 'strength': 0.6},
}
# 삼합의 생지·성지만 있을 때 중신을 사이에 둔 구조 후보.
GONG_HAPS = {
    ('寅', '戌'): {'element': '火', 'missing': '午'},
    ('亥', '未'): {'element': '木', 'missing': '卯'},
    ('申', '辰'): {'element': '水', 'missing': '子'},
    ('巳', '丑'): {'element': '金', 'missing': '酉'},
}
# 두 지지의 지장간 사이 천간합. 각 조합은 실제 합화 판정이 아니다.
HIDDEN_STEM_HAPS = {
    ('寅', '丑'): (('戊', '癸'), ('丙', '辛'), ('甲', '己')),
    ('午', '亥'): (('丁', '壬'), ('己', '甲')),
    ('卯', '申'): (('乙', '庚'),),
}
THREE_PUNISHMENTS = {
    ('寅', '巳', '申'): '무은지형',
    ('丑', '戌', '未'): '지세형',
}
PUNISHMENTS = {
    # 두 글자만 있을 때의 형. 寅巳·寅申·巳申 및 丑未는 각각 천·충·합·충이 주작용이다.
    '지세형': [('丑', '戌'), ('戌', '未')],
    '자진형': [('辰', '辰'), ('午', '午'), ('酉', '酉'), ('亥', '亥')],
}
BREAKS = {('子', '卯'), ('卯', '午'), ('午', '酉')}
TRADITIONAL_BREAKS = {('子', '酉'), ('丑', '辰'), ('寅', '亥'),
                      ('卯', '午'), ('巳', '申'), ('未', '戌')}
CHEONS = {('子', '未'), ('丑', '午'), ('寅', '巳'),
          ('卯', '辰'), ('酉', '戌'), ('申', '亥')}

# 조합별 작용. primary_relation은 명시적으로 검토한 쌍의 정적 기본 분류이며
# 원국에서 실제로 성립하거나 우세한 작용을 확정하지 않는다.
# coefficients는 방향별 잠재 작용량에 곱할 미보정 모델 계수다.
# 0은 관계 후보를 보존하되 실제 생 작용을 억제한다는 뜻이다.
# 다른 관계나 사주 전체 세력에 따른 주도권은 이 표에서 고정하지 않는다.
PAIR_ACTION_RULES = {
    # 검토된 쌍의 기본 분류를 기록한다. 삼형은 세 글자가 모일 때 별도 구조로 기록한다.
    frozenset(('子', '丑')): {
        'rule_id': 'branch:子丑', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'子': 1.0, '丑': 1.0},
                'mechanisms': {'子': 'bound_water', '丑': 'closes_hidden_metal'},
                'hidden_stem_candidates': [
                    {'branch': '丑', 'stem': '辛', 'effect': 'closure'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '극': {'coefficients': {'子': 0.0, '丑': 0.8},
                  'mechanisms': {'子': 'receives_earth_control',
                                 '丑': 'controls_water_candidate'}},
        },
    },
    frozenset(('寅', '亥')): {
        'rule_id': 'branch:寅亥', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'寅': 1.0, '亥': 1.0},
                'mechanisms': {'寅': 'binds_and_receives_support',
                               '亥': 'binds_and_outflows'},
                'hidden_stem_candidates': [
                    {'branch': '寅', 'stem': '丙', 'effect': 'injury'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '생': {'coefficients': {'寅': 0.0, '亥': 0.6},
                  'mechanisms': {'寅': 'receives_water_support',
                                 '亥': 'supports_wood'}},
        },
    },
    frozenset(('卯', '戌')): {
        'rule_id': 'branch:卯戌', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'卯': 1.0, '戌': 1.0},
                'mechanisms': {'卯': 'binds_and_controls_earth',
                               '戌': 'binds_under_wood_control'},
                'hidden_stem_candidates': [
                    {'branch': '戌', 'stem': '丁', 'effect': 'closure'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '극': {'coefficients': {'卯': 0.8, '戌': 0.0},
                  'mechanisms': {'卯': 'controls_earth',
                                 '戌': 'receives_wood_control'}},
        },
    },
    frozenset(('寅', '巳')): {
        'rule_id': 'branch:寅巳', 'primary_relation': '천(穿)', 'effects': {},
    },
    frozenset(('寅', '申')): {
        'rule_id': 'branch:寅申', 'primary_relation': '충(沖)', 'effects': {},
    },
    frozenset(('巳', '申')): {
        'rule_id': 'branch:巳申', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'巳': 1.0, '申': 1.0},
                'mechanisms': {'巳': 'binds_and_controls_metal',
                               '申': 'binds_under_fire_control'},
                'hidden_stem_candidates': [
                    {'branch': '巳', 'stem': '丙', 'effect': 'injury'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '극': {'coefficients': {'巳': 0.8, '申': 0.0},
                  'mechanisms': {'巳': 'controls_metal',
                                 '申': 'receives_fire_control'}},
        },
    },
    frozenset(('午', '未')): {
        'rule_id': 'branch:午未', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'午': 1.0, '未': 1.0},
                'mechanisms': {'午': 'binds_and_outflows',
                               '未': 'binds_and_receives_support'},
                'hidden_stem_candidates': [
                    {'branch': '未', 'stem': '乙', 'effect': 'closure'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '생': {'coefficients': {'午': 0.6, '未': 0.0},
                  'mechanisms': {'午': 'supports_earth',
                                 '未': 'receives_fire_support'}},
        },
    },
    frozenset(('丑', '未')): {
        'rule_id': 'branch:丑未', 'primary_relation': '충(沖)', 'effects': {},
    },
    frozenset(('丑', '戌')): {
        'rule_id': 'branch:丑戌', 'primary_relation': '형(刑)', 'effects': {},
    },
    frozenset(('戌', '未')): {
        'rule_id': 'branch:戌未', 'primary_relation': '형(刑)', 'effects': {},
    },
    frozenset(('子', '午')): {
        'rule_id': 'branch:子午', 'primary_relation': '충(沖)',
        'effects': {
            '충(沖)': {'coefficients': {'子': 1.0, '午': 1.0},
                       'mechanisms': {'子': 'collision', '午': 'collision'}},
            '극': {'coefficients': {'子': 0.8, '午': 0.0},
                  'mechanisms': {'子': 'controls_fire', '午': 'no_element_control'}},
        },
    },
    frozenset(('子', '卯')): {
        'rule_id': 'branch:子卯', 'primary_relation': '파(破)',
        'effects': {
            '파(破)': {'coefficients': {'子': 0.45, '卯': 0.45},
                      'mechanisms': {'子': 'break', '卯': 'break'}},
        },
    },
    frozenset(('卯', '午')): {
        'rule_id': 'branch:卯午', 'primary_relation': '파(破)',
        'effects': {
            '파(破)': {'coefficients': {'卯': 0.45, '午': 0.45},
                       'mechanisms': {'卯': 'break', '午': 'break'}},
        },
    },
    frozenset(('午', '酉')): {
        'rule_id': 'branch:午酉', 'primary_relation': '파(破)',
        'effects': {
            '파(破)': {'coefficients': {'午': 0.45, '酉': 0.45},
                       'mechanisms': {'午': 'break', '酉': 'break'}},
            '극': {'coefficients': {'午': 0.8, '酉': 0.0},
                  'mechanisms': {'午': 'controls_metal', '酉': 'no_element_control'}},
        },
    },
    frozenset(('辰', '酉')): {
        'rule_id': 'branch:辰酉', 'primary_relation': '육합(六合)',
        'effects': {
            '육합(六合)': {
                'coefficients': {'辰': 1.0, '酉': 1.0},
                'mechanisms': {'辰': 'binds_and_outflows', '酉': 'binds_and_receives_support'},
                'hidden_stem_candidates': [
                    {'branch': '辰', 'stem': '癸', 'effect': 'closure'},
                    {'branch': '辰', 'stem': '乙', 'effect': 'injury'},
                ],
                'reason': 'combination_candidate_not_transformation',
            },
            '생': {'coefficients': {'辰': 0.6, '酉': 0.0},
                  'mechanisms': {'辰': 'supports_metal', '酉': 'receives_support'}},
        },
    },
}


def get_pair_action_rule(first_branch, second_branch, relation_type):
    """지지 순서와 무관하게 해당 관계의 조합별 작용 규칙을 찾는다."""
    pair_rule = PAIR_ACTION_RULES.get(frozenset((first_branch, second_branch)))
    if pair_rule is None:
        return None
    effect = pair_rule['effects'].get(relation_type)
    if effect is None:
        return None
    return pair_rule['rule_id'], effect

# 기존 코드가 노출하던 우선순위와 충 조건. 현재 판정기에 일괄 적용되지는 않는다.
PRIORITY_RANK = {
    '삼합': 1, '방합': 2, '육합': 3, '반합': 4,
    '충': 5, '형': 6, '천': 7, '파': 8,
}
# 집계 점수의 중복 방지 정책. 후보와 개별 점수는 남기고, 활성 다자 구조의
# 한 성립 조합 안에 완전히 포함된 쌍의 총점 기여만 0으로 둔다.
HARMONY_SCORE_TYPES = frozenset({
    '천간합(天干合)', '육합(六合)', '반합(半合)',
    '삼합(三合)', '방합(方合)',
})
HARMONY_GROUP_COVERS_PAIR = {
    '삼합(三合)': frozenset({'육합(六合)', '반합(半合)'}),
    '방합(方合)': frozenset({'육합(六合)', '반합(半合)'}),
}
# 완성된 다자 합의 글자별 구조적 위치. 세력이나 실제 견인 방향을 뜻하지 않는다.
GROUP_ROLE_ORDER = {
    '삼합(三合)': ('birth', 'center', 'storage'),
    '방합(方合)': ('season_start', 'season_center', 'season_end'),
}
# 다자 합의 방향은 힘의 우세가 아니라 구조상 작용 후보이다. 실제 견인량과
# 합화 성립을 정할 계수가 없으므로 그룹 작용량은 계산하지 않는다.
# 삼합은 중신으로 모이는 구조 후보만 표시한다. 방합의 개별 방향은 미정이다.
GROUP_ACTION_RULES = {
    ('삼합(三合)', frozenset(('寅', '午', '戌'))): {
        'rule_id': 'group:삼합:寅午戌', 'center_branch': '午',
        'direction_candidates': (('birth', 'center'), ('storage', 'center')),
        'role_effect_candidates': {'storage': 'center_generates_storage_candidate'},
        'direction_status': 'candidate_only',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('삼합(三合)', frozenset(('亥', '卯', '未'))): {
        'rule_id': 'group:삼합:亥卯未', 'center_branch': '卯',
        'direction_candidates': (('birth', 'center'), ('storage', 'center')),
        'role_effect_candidates': {'storage': 'transformation_candidate'},
        'direction_status': 'candidate_only',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('삼합(三合)', frozenset(('申', '子', '辰'))): {
        'rule_id': 'group:삼합:申子辰', 'center_branch': '子',
        'direction_candidates': (('birth', 'center'), ('storage', 'center')),
        'role_effect_candidates': {'storage': 'transformation_candidate'},
        'direction_status': 'candidate_only',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('삼합(三合)', frozenset(('巳', '酉', '丑'))): {
        'rule_id': 'group:삼합:巳酉丑', 'center_branch': '酉',
        'direction_candidates': (('birth', 'center'), ('storage', 'center')),
        'role_effect_candidates': {'storage': 'transformation_candidate'},
        'direction_status': 'candidate_only',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('방합(方合)', frozenset(('寅', '卯', '辰'))): {
        'rule_id': 'group:방합:寅卯辰', 'center_branch': None,
        'direction_candidates': (), 'role_effect_candidates': {},
        'direction_status': 'undetermined',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('방합(方合)', frozenset(('巳', '午', '未'))): {
        'rule_id': 'group:방합:巳午未', 'center_branch': None,
        'direction_candidates': (), 'role_effect_candidates': {},
        'direction_status': 'undetermined',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('방합(方合)', frozenset(('申', '酉', '戌'))): {
        'rule_id': 'group:방합:申酉戌', 'center_branch': None,
        'direction_candidates': (), 'role_effect_candidates': {},
        'direction_status': 'undetermined',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
    ('방합(方合)', frozenset(('亥', '子', '丑'))): {
        'rule_id': 'group:방합:亥子丑', 'center_branch': None,
        'direction_candidates': (), 'role_effect_candidates': {},
        'direction_status': 'undetermined',
        'pair_overlap_policy': 'preserve_pair_do_not_sum_group_force',
    },
}


def get_group_action_rule(group_type, branches):
    """글자 위치 순서와 무관하게 다자 관계의 방향 후보 규칙을 찾는다."""
    return GROUP_ACTION_RULES.get((group_type, frozenset(branches)))

CHUNG_BREAK_CONDITION = {
    '육합': True, '반합': True, '삼합': False, '방합': False,
}
THREE_HAPS_BIRTH = {'火': ['寅'], '木': ['亥'], '水': ['申'], '金': ['巳']}
THREE_HAPS_KING = {'火': ['午'], '木': ['卯'], '水': ['子'], '金': ['酉']}
THREE_HAPS_SUCCESS = {'火': ['戌'], '木': ['未'], '水': ['辰'], '金': ['丑']}

# 같은 기둥의 천간과 지장간 사이 자합 후보.
JAHAB_MAP = {
    ('戊', '子'): {'hidden': '癸', 'element': '火', 'conditional': False, 'required': None},
    ('丁', '亥'): {'hidden': '壬', 'element': '木', 'conditional': False, 'required': None},
    ('己', '亥'): {'hidden': '甲', 'element': '土', 'conditional': False, 'required': None},
    ('辛', '巳'): {'hidden': '丙', 'element': '水', 'conditional': False, 'required': None},
    ('癸', '巳'): {'hidden': '戊', 'element': '火', 'conditional': False, 'required': None},
    ('壬', '午'): {'hidden': '丁', 'element': '木', 'conditional': False, 'required': None},
    ('甲', '午'): {'hidden': '己', 'element': '土', 'conditional': False, 'required': None},
    ('丙', '戌'): {'hidden': '辛', 'element': '水', 'conditional': True,
                'required': ('지세형', '未'), 'blocked_by_chung': '辰'},
    ('壬', '戌'): {'hidden': '丁', 'element': '木', 'conditional': True,
                'required': ('지세형', '未'), 'blocked_by_chung': '辰'},
}

# v2의 미보정 상대 점수 가정. 관계의 성립 규칙과 구별한다.
POSITION_WEIGHTS = (1.0, 2.0, 1.5, 1.0)
GENERATES = {'목': '화', '화': '토', '토': '금', '금': '수', '수': '목'}
DOMINANCE_MARGIN = 0.10
SEASON_FACTORS = {
    'same': 1.20,
    'season_generates_component': 1.10,
    'component_generates_season': 0.90,
    'season_controls_component': 0.80,
    'component_controls_season': 0.95,
}
STEM_ADJUSTMENTS = {
    'stem_generates_branch': 0.20,
    'stem_controls_branch': -0.25,
    'branch_generates_stem': -0.15,
    'branch_controls_stem': -0.05,
    'same_element': 0.10,
}
AMBIENT_RATES = {
    'same_element': 0.05,
    'generates': 0.08,
    'generated_by': -0.06,
    'controls': -0.10,
    'controlled_by': -0.03,
}
ATTRACTION_TYPES = {'육합(六合)', '반합(半合)', '공합(拱合)', '암합(暗合)'}
PRESSURE_TYPES = {'충(沖)', '형(刑)', '파(破)', '천(穿)'}
RELATION_COEFFICIENTS = {
    '육합(六合)': 1.00,
    '반합(半合)': 0.70,
    '공합(拱合)': 0.0,
    '암합(暗合)': 0.0,
    '충(沖)': 1.00,
    '형(刑)': 0.75,
    '파(破)': 0.45,
    '천(穿)': 0.65,
    '생': 0.60,
    '극': 0.80,
}
