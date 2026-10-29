"""원국 지지의 비교 세력과 관계별 양방향 작용 지표.

이 값은 명리 해석 규칙을 명시한 상대 지표이며 실제 피해나 성취의 측정값이 아니다.
관계별 작용은 서로 합산하지 않는다. 중첩 관계의 중복 가산을 피하기 위해서다.
"""

from services.constants import JIJANGGAN_DETAILED
from services.five_elements import BRANCH_ELEMENT_MAP, STEM_ELEMENT_MAP
from services.relation_rules import (
    POSITION_WEIGHTS, GENERATES, DOMINANCE_MARGIN, SEASON_FACTORS,
    STEM_ADJUSTMENTS, AMBIENT_RATES, ATTRACTION_TYPES, PRESSURE_TYPES,
    RELATION_COEFFICIENTS, RULE_PROFILE, RULE_VERSION, PAIR_ACTION_RULES,
    THREE_HAPS, SQUARE_HAPS, GROUP_ROLE_ORDER, HARMONY_GROUP_COVERS_PAIR,
    get_pair_action_rule,
)


PILLARS = ('year', 'month', 'day', 'hour')


def _element_relation(source, target):
    if source == target:
        return 'same_element'
    if GENERATES[source] == target:
        return 'generates'
    if GENERATES[target] == source:
        return 'generated_by'
    if GENERATES[GENERATES[source]] == target:
        return 'controls'
    return 'controlled_by'


def _stem_branch_relation(stem_element, branch_element):
    relation = _element_relation(stem_element, branch_element)
    return {
        'same_element': 'same_element',
        'generates': 'stem_generates_branch',
        'generated_by': 'branch_generates_stem',
        'controls': 'stem_controls_branch',
        'controlled_by': 'branch_controls_stem',
    }[relation]


def _season_relation(season_element, component_element):
    relation = _element_relation(season_element, component_element)
    return {
        'same_element': 'same',
        'generates': 'season_generates_component',
        'generated_by': 'component_generates_season',
        'controls': 'season_controls_component',
        'controlled_by': 'component_controls_season',
    }[relation]


def _element_pair(first_element, second_element, first_pillar, second_pillar):
    relation = _element_relation(first_element, second_element)
    if relation == 'generates':
        return '생', f'{first_pillar}_to_{second_pillar}'
    if relation == 'generated_by':
        return '생', f'{second_pillar}_to_{first_pillar}'
    if relation == 'controls':
        return '극', f'{first_pillar}_to_{second_pillar}'
    if relation == 'controlled_by':
        return '극', f'{second_pillar}_to_{first_pillar}'
    return '동기', None


def _branch_strength(stem, branch, pillar, position_weight, season_element):
    stem_element = STEM_ELEMENT_MAP[stem]
    branch_element = BRANCH_ELEMENT_MAP[branch]
    hidden = []
    seasonal_factor = 0.0
    stem_adjustment_ratio = 0.0

    for item in JIJANGGAN_DETAILED[branch]:
        numerator, denominator = map(int, item['ratio'].split('/'))
        ratio = numerator / denominator
        hidden_element = STEM_ELEMENT_MAP[item['char']]
        season_relation = _season_relation(season_element, hidden_element)
        stem_relation = _stem_branch_relation(stem_element, hidden_element)
        seasonal_factor += ratio * SEASON_FACTORS[season_relation]
        stem_adjustment_ratio += ratio * STEM_ADJUSTMENTS[stem_relation]
        hidden.append({
            'stem': item['char'],
            'element': hidden_element,
            'ratio': ratio,
            'season_relation': season_relation,
            'stem_relation': stem_relation,
        })

    base = position_weight * seasonal_factor
    effective = base * (1 + stem_adjustment_ratio)
    primary_relation = _stem_branch_relation(stem_element, branch_element)
    return {
        'branch': branch,
        'element': branch_element,
        'base_power': round(base, 4),
        'stem_branch_relation': {
            'stem': stem,
            'stem_element': stem_element,
            'relation': primary_relation,
            'branch_effect': {
                'stem_generates_branch': 'support',
                'stem_controls_branch': 'pressure',
                'branch_generates_stem': 'outflow',
                'branch_controls_stem': 'outward_control',
                'same_element': 'peer',
            }[primary_relation],
            'adjustment': round(effective - base, 4),
            'evidence': hidden,
        },
        'after_stem_power': round(effective, 4),
        # 원국의 나머지 지지까지 반영한 개괄 값. 관계별 작용에는 상대를 제외한 값 사용.
        'effective_power': round(effective, 4),
        'ambient_evidence': [],
        'components': {
            'position_weight': position_weight,
            'seasonal_factor': round(seasonal_factor, 4),
            'stem_adjustment_ratio': round(stem_adjustment_ratio, 4),
        },
        'evidence': hidden,
    }


def _dominance(first, second, first_pillar, second_pillar):
    total = first + second
    if total == 0:
        return 'undetermined'
    if abs(first - second) / total <= DOMINANCE_MARGIN:
        return 'tie'
    return first_pillar if first > second else second_pillar


def _distance_weight(first_index, second_index):
    return {1: 1.0, 2: 0.7, 3: 0.5}[abs(first_index - second_index)]


def _context_power(target_index, strengths, matrix_by_pair, excluded_index=None,
                   excluded_indices=()):
    """상대 지지와의 자기 피드백 없이 나머지 원국의 배경 작용을 반영한다."""
    target = strengths[PILLARS[target_index]]
    contributions = []
    adjustment_ratio = 0.0
    excluded = {target_index, excluded_index, *excluded_indices}
    for source_index, source_pillar in enumerate(PILLARS):
        if source_index in excluded:
            continue
        source = strengths[source_pillar]
        relation = _element_relation(source['element'], target['element'])
        element_type = ('생' if relation in ('generates', 'generated_by') else
                        '극' if relation in ('controls', 'controlled_by') else None)
        element_rule = (get_pair_action_rule(source['branch'], target['branch'], element_type)
                        if element_type else None)
        effect = element_rule[1] if element_rule else {}
        element_status = effect.get('status', 'potential')
        element_blocked = element_status in ('suppressed', 'conditional')
        pair = tuple(sorted((source_pillar, PILLARS[target_index]),
                            key=PILLARS.index))
        related_relations = [
            {'relation_id': item['relation_id'], 'type': item['type'],
             'activation_status': item.get('activation_status', 'potential')}
            for item in matrix_by_pair.get(pair, [])
        ]
        # 원천 세력이 클수록 작용이 커지되, 하나가 전체 보정을 무한히 지배하지 않는다.
        source_capacity = source['after_stem_power'] / (1 + source['after_stem_power'])
        ratio = (0.0 if element_blocked else
                 AMBIENT_RATES[relation] *
                 _distance_weight(source_index, target_index) * source_capacity)
        adjustment_ratio += ratio
        contributions.append({
            'source_pillar': source_pillar,
            'relation': relation,
            'element_relation_id': (f'지지:{element_type}:{pair[0]},{pair[1]}'
                                    if element_type else None),
            'related_relations': related_relations,
            'adjustment_ratio': round(ratio, 6),
            'activation_status': element_status,
            'status_reason': effect.get('reason') if element_blocked else None,
        })
    adjustment_ratio = max(-0.35, min(0.35, adjustment_ratio))
    return round(target['after_stem_power'] * (1 + adjustment_ratio), 4), contributions


def _relation_roles(kind, first_pillar, second_pillar,
                    first_to_second, second_to_first):
    """작용량에서 읽을 수 있는 역할만 표시한다. 실제 성립·길흉 판정은 아니다."""
    if first_to_second == second_to_first == 0:
        return {first_pillar: 'inactive', second_pillar: 'inactive'}
    if kind in ('support', 'control'):
        source, target = ((first_pillar, second_pillar) if first_to_second > 0
                          else (second_pillar, first_pillar))
        return {source: kind + 's', target: 'receives_' + kind}
    lead = _dominance(first_to_second, second_to_first,
                      first_pillar, second_pillar)
    if lead == 'tie':
        role = 'mutual_attraction' if kind == 'attraction' else 'mutual_pressure'
        return {first_pillar: role, second_pillar: role}
    leading = ('leads_attraction' if kind == 'attraction'
               else 'delivers_more_pressure')
    receiving = ('drawn_more' if kind == 'attraction'
                 else 'receives_more_pressure')
    return {lead: leading,
            second_pillar if lead == first_pillar else first_pillar: receiving}


def _group_formations(group, branches, strengths, matrix_by_pair):
    """그룹 내부 작용을 더하기 전, 성립 조합별 참여 세력과 겹치는 쌍을 기록한다."""
    role_order = GROUP_ROLE_ORDER.get(group['type'])
    if role_order is None:
        return []
    definitions = THREE_HAPS if group['type'] == '삼합(三合)' else SQUARE_HAPS
    result = []
    for formation in group['formations']:
        indices = [PILLARS.index(pillar) for pillar in formation]
        formation_branches = {branches[index] for index in indices}
        canonical = next(members for members in definitions
                         if set(members) == formation_branches)
        role_by_branch = dict(zip(canonical, role_order))
        power = {}
        context = {}
        for pillar, index in zip(formation, indices):
            power[pillar], context[pillar] = _context_power(
                index, strengths, matrix_by_pair, excluded_indices=indices)
        total = sum(power.values())
        overlapping = [
            {'relation_id': item['relation_id'],
             'covered_in_harmony_score': item.get('score_covered_by') == group['relation_id']}
            for pair_items in matrix_by_pair.values() for item in pair_items
            if item['type'] in HARMONY_GROUP_COVERS_PAIR[group['type']]
            and set(item['participants']) <= set(formation)
        ]
        result.append({
            'pillars': formation,
            'structural_roles': {pillar: role_by_branch[branches[index]]
                                 for pillar, index in zip(formation, indices)},
            'power_before': power,
            'context_evidence': context,
            'capacity_share': {pillar: round(value / total, 4) if total else 0.0
                               for pillar, value in power.items()},
            'overlapping_pairs': overlapping,
        })
    return result


def _event(item, first_pillar, second_pillar, first_branch, second_branch,
           first_power, second_power,
           distance_weight, element_relation, element_direction):
    """같은 쌍의 각 관계를 독립 표시한다. 힘은 관계별 잠재 작용량이다."""
    coefficient = RELATION_COEFFICIENTS[item['type']]
    pair_effect = get_pair_action_rule(first_branch, second_branch, item['type'])
    rule_id, effect = pair_effect if pair_effect else (None, {})
    coefficients = effect.get('coefficients', {})
    first_coefficient = coefficients.get(first_branch, coefficient)
    second_coefficient = coefficients.get(second_branch, coefficient)
    first_to_second = round(first_power * distance_weight * first_coefficient, 4)
    second_to_first = round(second_power * distance_weight * second_coefficient, 4)
    status = item.get('activation_status', effect.get('status', 'potential'))
    if status in ('suppressed', 'conditional'):
        first_to_second = second_to_first = 0.0
    if item['type'] in ('생', '극'):
        # 오행의 생·극 방향은 정해져 있다. 반대 방향의 저항/반격을 생·극으로 위장하지 않는다.
        if element_direction == f'{first_pillar}_to_{second_pillar}':
            second_to_first = 0.0
        else:
            first_to_second = 0.0
    total = first_power + second_power
    first_effect = round(second_to_first * second_power / total, 4) if total else 0.0
    second_effect = round(first_to_second * first_power / total, 4) if total else 0.0
    kind = ('attraction' if item['type'] in ATTRACTION_TYPES else
            'pressure' if item['type'] in PRESSURE_TYPES else
            'support' if item['type'] == '생' else 'control')
    return {
        'relation_id': item['relation_id'],
        'type': item['type'],
        'effect_kind': kind,
        'relation_coefficient': coefficient,
        'directional_coefficients': {
            f'{first_pillar}_to_{second_pillar}': first_coefficient,
            f'{second_pillar}_to_{first_pillar}': second_coefficient,
        },
        'directional_mechanisms': {
            first_pillar: effect.get('mechanisms', {}).get(first_branch, 'generic'),
            second_pillar: effect.get('mechanisms', {}).get(second_branch, 'generic'),
        },
        'rule_id': rule_id,
        'activation_status': status,
        'status_reason': (item.get('status_reasons') or [effect.get('reason')])[0],
        'candidate_hidden_stem_effects': item.get('candidate_hidden_stem_effects', []),
        'distance_weight': distance_weight,
        'element_relation': element_relation,
        'element_direction': element_direction,
        'power_before': {first_pillar: first_power, second_pillar: second_power},
        'force': {
            f'{first_pillar}_to_{second_pillar}': first_to_second,
            f'{second_pillar}_to_{first_pillar}': second_to_first,
        },
        'effect_received': {first_pillar: first_effect, second_pillar: second_effect},
        # 세력 우세와 실제로 계산된 관계별 작용 방향을 분리한다.
        'dominance': _dominance(first_power, second_power, first_pillar, second_pillar),
        'force_dominance': _dominance(first_to_second, second_to_first,
                                      first_pillar, second_pillar),
        'roles': _relation_roles(kind, first_pillar, second_pillar,
                                 first_to_second, second_to_first),
        'evidence': [item['relation_id']],
    }


def analyze_branch_dynamics(stems, branches, interaction_matrix):
    """원국 4지지의 세력과 6쌍의 관계별 잠재 작용을 계산한다."""
    if len(stems) != 4 or len(branches) != 4:
        raise ValueError('천간과 지지는 각각 4개여야 합니다.')

    matrix_by_pair = {}
    groups = []
    for item in interaction_matrix:
        if item.get('category') != '지지':
            continue
        if item.get('relation_scope') == 'group':
            groups.append({
                'relation_id': item['relation_id'],
                'type': item['type'],
                'participants': item['participants'],
                'formations': item['formations'],
                # 기존 element는 후보 오행의 호환 별칭이다. 합화 성립은 별도 판정한다.
                'element': item.get('candidate_element'),
                'candidate_element': item.get('candidate_element'),
                'transformed_element': item.get('transformed_element'),
                'status': 'not_scored',
                'activation_status': item.get('activation_status'),
                'status_reasons': item.get('status_reasons', []),
                'condition_evidence': item.get('condition_evidence', {}),
            })
        else:
            pair = (item['from_pillar'], item['to_pillar'])
            matrix_by_pair.setdefault(pair, []).append(item)

    season_element = BRANCH_ELEMENT_MAP[branches[1]]
    strengths = {
        pillar: _branch_strength(stems[i], branches[i], pillar,
                                 POSITION_WEIGHTS[i], season_element)
        for i, pillar in enumerate(PILLARS)
    }
    for index, pillar in enumerate(PILLARS):
        power, evidence = _context_power(index, strengths, matrix_by_pair)
        strengths[pillar]['effective_power'] = power
        strengths[pillar]['ambient_evidence'] = evidence
    for group in groups:
        group['formation_evidence'] = _group_formations(
            group, branches, strengths, matrix_by_pair)

    pairs = []
    for first_idx in range(4):
        for second_idx in range(first_idx + 1, 4):
            first_pillar, second_pillar = PILLARS[first_idx], PILLARS[second_idx]
            first = strengths[first_pillar]
            second = strengths[second_pillar]
            # 이 쌍의 관계가 스스로의 세력을 미리 올리거나 내리는 순환을 막는다.
            first_power, first_context = _context_power(first_idx, strengths,
                                                         matrix_by_pair, second_idx)
            second_power, second_context = _context_power(second_idx, strengths,
                                                           matrix_by_pair, first_idx)
            element_relation, element_direction = _element_pair(
                first['element'], second['element'], first_pillar, second_pillar)
            events = list(matrix_by_pair.get((first_pillar, second_pillar), []))
            if element_relation in ('생', '극'):
                events.append({
                    'relation_id': f'지지:{element_relation}:{first_pillar},{second_pillar}',
                    'type': element_relation,
                })
            distance_weight = _distance_weight(first_idx, second_idx)
            relations = [
                _event(item, first_pillar, second_pillar,
                       first['branch'], second['branch'],
                       first_power, second_power,
                       distance_weight, element_relation, element_direction)
                for item in events
            ]
            first_guest = first_idx < 2
            second_guest = second_idx < 2
            pair_rule = PAIR_ACTION_RULES.get(frozenset((first['branch'], second['branch'])))
            pairs.append({
                'pair_id': f'{first_pillar}:{second_pillar}',
                'pillars': [first_pillar, second_pillar],
                'rule_id': pair_rule['rule_id'] if pair_rule else None,
                'primary_relation': pair_rule['primary_relation'] if pair_rule else None,
                'relations': relations,
                'context_evidence': {
                    first_pillar: first_context,
                    second_pillar: second_context,
                },
                'domain_pair': ('guest_guest' if first_guest and second_guest else
                                'host_host' if not first_guest and not second_guest else
                                'guest_host'),
            })

    return {
        'rule_profile': RULE_PROFILE,
        'rule_version': RULE_VERSION,
        'scope': 'natal',
        'score_meaning': 'uncalibrated_relative_model_index',
        'branch_strengths': strengths,
        'pairwise': pairs,
        'groups': groups,
    }
