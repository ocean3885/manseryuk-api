"""현재 등록된 관계의 십성 패턴만 생성한다. 해설·성립 조건은 생성하지 않는다."""
from collections import Counter
from itertools import product
from schemas.interpretation_rule import empty_rule
from services.calculator import get_ten_star_stem, get_ten_star_branch
from services.five_elements import STEM_ELEMENT_MAP, BRANCH_ELEMENT_MAP
from services.relation_rules import (
    RULE_PROFILE, RULE_VERSION, STEM_COMBINATIONS, STEM_CONFLICTS, STEM_RESTRAIN,
    SIX_HAPS, CHUNGS, CHEONS, BREAKS, PUNISHMENTS, HALF_HAPS, GONG_HAPS,
    HIDDEN_STEM_HAPS, THREE_HAPS, SQUARE_HAPS, THREE_PUNISHMENTS, JAHAB_MAP,
)

CATALOG_SCHEMA_VERSION = 1


def generate_catalog() -> dict:
    rules = {}

    def add(layer, kind, participants, conditions=None):
        rule = empty_rule(layer, kind, participants, conditions)
        rules[rule.rule_id] = rule

    stem_pairs = {'combine': STEM_COMBINATIONS, 'clash': STEM_CONFLICTS, 'control': STEM_RESTRAIN}
    branch_pairs = {'combine': SIX_HAPS, 'clash': CHUNGS, 'pierce': CHEONS, 'break': BREAKS,
                    'punishment': PUNISHMENTS['지세형'], 'self_punishment': PUNISHMENTS['자진형'],
                    'half_combine': HALF_HAPS, 'arch_combine': GONG_HAPS,
                    'hidden_combine': HIDDEN_STEM_HAPS,
                    'same_branch': [(b, b) for b in BRANCH_ELEMENT_MAP]}
    cycle = '목화토금수'
    elements = {0: 'same_element', 1: 'stem_generates_branch', 2: 'stem_controls_branch',
                3: 'branch_controls_stem', 4: 'branch_generates_stem'}
    for day_stem in STEM_ELEMENT_MAP:
        for kind, pairs in stem_pairs.items():
            for first, second in pairs:
                add('stem', kind, (get_ten_star_stem(day_stem, first), get_ten_star_stem(day_stem, second)))
        for kind, pairs in branch_pairs.items():
            for first, second in pairs:
                add('branch', kind, (get_ten_star_branch(day_stem, first), get_ten_star_branch(day_stem, second)))
        for first, second in product(BRANCH_ELEMENT_MAP, repeat=2):
            offset = (cycle.index(BRANCH_ELEMENT_MAP[second]) - cycle.index(BRANCH_ELEMENT_MAP[first])) % 5
            if offset in (1, 2):
                add('branch', 'generate' if offset == 1 else 'control',
                    (get_ten_star_branch(day_stem, first), get_ten_star_branch(day_stem, second)))
        for kind, groups in [('trine', THREE_HAPS), ('square', SQUARE_HAPS),
                             ('triple_punishment', THREE_PUNISHMENTS)]:
            for members in groups:
                add('group', kind, tuple(get_ten_star_branch(day_stem, b) for b in members))
        for stem, branch in product(STEM_ELEMENT_MAP, BRANCH_ELEMENT_MAP):
            offset = (cycle.index(BRANCH_ELEMENT_MAP[branch]) - cycle.index(STEM_ELEMENT_MAP[stem])) % 5
            add('same_pillar', 'element', (get_ten_star_stem(day_stem, stem), get_ten_star_branch(day_stem, branch)),
                {'scope': 'natal', 'element_relation': elements[offset]})
        for stem, branch in JAHAB_MAP:
            add('same_pillar', 'self_combine',
                (get_ten_star_stem(day_stem, stem), get_ten_star_branch(day_stem, branch)))
    ordered = sorted(rules.values(), key=lambda r: (r.layer, r.relation_type, r.participant_pattern, r.rule_id))
    return {'schema_version': CATALOG_SCHEMA_VERSION, 'rule_profile': RULE_PROFILE,
            'source_rule_version': RULE_VERSION,
            'counts_by_layer': dict(sorted(Counter(r.layer for r in ordered).items())),
            'rules': [r.model_dump(mode='json') for r in ordered]}
