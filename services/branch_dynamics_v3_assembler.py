"""기존 지지 계산 결과를 v3 계약의 검증 가능한 부분에 연결한다.

경합·작공은 아직 조립하지 않는다. 이 모듈은 전체 v3 응답이 아니다.
"""

from itertools import combinations

from schemas.branch_dynamics_v3 import (
    BranchGroupV3, BranchPairV3, BranchStrengthsV3, ChartContextV3,
    InteractionResolutionV3, MetaV3,
)
from schemas.branch_dynamics_v3_contract import BRANCH_CODES
from services.branch_dynamics import PILLARS, _season_relation
from services.five_elements import BRANCH_ELEMENT_MAP
from services.relation_rules import (
    HALF_HAPS, SIX_HAPS, THREE_HAPS, SQUARE_HAPS, THREE_PUNISHMENTS,
    V3_RULE_VERSION, V3_POTENTIAL_FORMULA_ID, V3_EXPOSURE_FORMULA_ID,
    V3_UNSCORED_PAIR_TYPES,
)


ELEMENT_HANJA = {'목': '木', '화': '火', '토': '土', '금': '金', '수': '水'}
ELEMENT_ENGLISH = {'목': 'wood', '화': 'fire', '토': 'earth', '금': 'metal', '수': 'water'}
RELATION_TYPES = {
    '생': ('generate', '생'),
    '극': ('control', '극'),
    '충(沖)': ('clash', '충'),
    '형(刑)': ('punishment', '형'),
    '파(破)': ('break', '파'),
    '해/천(穿/害)': ('harm', '해·천'),
    '육합(六合)': ('combine', '육합'),
    '반합(半合)': ('half_combine', '반합'),
    '공합(拱合)': ('arch_combine', '공합'),
    '암합(暗合)': ('hidden_combine', '암합'),
}
GROUP_TYPES = {
    '삼합(三合)': ('trine', '삼합', THREE_HAPS),
    '방합(方合)': ('square', '방합', SQUARE_HAPS),
    '삼형(三刑)': ('triple_punishment', '삼형', THREE_PUNISHMENTS),
}


def assemble_branch_dynamics_v3_foundation(stems, branches, dynamics_v2):
    """v2 계산 결과에서 v3의 메타·원국·개별 지지 세력만 만든다.

    원본에 없는 관계별 성립 판정과 지장간별 최종 기여도는 추정하지 않는다.
    """
    if len(stems) != 4 or len(branches) != 4:
        raise ValueError('천간과 지지는 각각 4개여야 합니다.')
    source_strengths = dynamics_v2['branch_strengths']
    if set(source_strengths) != set(PILLARS):
        raise ValueError('v2 지지 세력에는 네 기둥이 모두 있어야 합니다.')

    meta = MetaV3.model_validate({
        'schema_version': '3.1-draft',
        'rule_version': f"{dynamics_v2['rule_version']}+{V3_RULE_VERSION}",
        'analysis_school': 'mangpa',
        'score_meaning': 'uncalibrated_relative_index',
        'score_policy': {
            'cross_type_addition': False,
            'zero_means_no_effect': True,
            'null_means_not_calculated': True,
        },
    })
    chart_context = ChartContextV3.model_validate({
        'bin_zhu_rule': 'year_month_guest_day_hour_host',
        'pillars': {
            pillar: {
                'stem': stems[index],
                'branch': branches[index],
                'domain': 'guest' if index < 2 else 'host',
            }
            for index, pillar in enumerate(PILLARS)
        },
    })

    month_element = BRANCH_ELEMENT_MAP[branches[1]]
    strengths = {}
    for index, pillar in enumerate(PILLARS):
        source = source_strengths[pillar]
        if (source['branch'] != branches[index]
                or source['stem_branch_relation']['stem'] != stems[index]):
            raise ValueError(f'{pillar} 지지 세력의 원국과 입력 원국이 다릅니다.')

        stem_evidence = source['stem_branch_relation']
        ambient = source['ambient_evidence']
        # v2의 주변 조정은 여러 근거의 합산·상한 적용 결과다. 개별 기여도를
        # 역산하지 않고, 계산된 최종 차이만 순변화량으로 기록한다.
        adjustments = [
            {
                'stage': 'same_pillar_stem',
                'source': 'stem_branch_relation.adjustment',
                'power_delta': stem_evidence['adjustment'],
            },
            {
                'stage': 'surroundings',
                'source': 'effective_power - after_stem_power',
                'power_delta': round(
                    source['effective_power'] - source['after_stem_power'], 4),
            },
        ]
        strengths[pillar] = {
            'branch': source['branch'],
            'element': ELEMENT_HANJA[source['element']],
            'bin_zhu_domain': 'guest' if index < 2 else 'host',
            'base_power': source['base_power'],
            'after_stem_power': source['after_stem_power'],
            'effective_power': source['effective_power'],
            'strength_evidence': {
                'position_weight': source['components']['position_weight'],
                'season': {
                    'month_branch': branches[1],
                    # 대표 오행의 관계다. factor는 지장간별 월령 계수의 가중평균.
                    'relation': _season_relation(month_element, source['element']),
                    'factor': source['components']['seasonal_factor'],
                },
                'hidden_stems': [
                    {
                        'stem': item['stem'],
                        'element': ELEMENT_HANJA[item['element']],
                        'ratio': item['ratio'],
                        'season_relation': item['season_relation'],
                        'effective_contribution': None,
                    }
                    for item in source['evidence']
                ],
                'same_pillar_stem': {
                    'stem': stem_evidence['stem'],
                    'relation': stem_evidence['relation'],
                    'effect': stem_evidence['branch_effect'],
                    'adjustment': stem_evidence['adjustment'],
                },
                'surroundings': [
                    {
                        'source_pillar': item['source_pillar'],
                        'relation': item['relation'],
                        'adjustment_ratio': (None if item['activation_status'] == 'conditional'
                                             else item['adjustment_ratio']),
                    }
                    for item in ambient
                ],
            },
            'calculation_trace': {
                'base_formula_id': None,
                'stem_formula_id': None,
                'surroundings_formula_id': None,
                'applied_adjustments': adjustments,
                'validation_status': 'unverified',
            },
        }

    branch_strengths = BranchStrengthsV3.model_validate(strengths)
    return {
        'meta': meta.model_dump(),
        'chart_context': chart_context.model_dump(),
        'branch_strengths': branch_strengths.model_dump(),
    }


def _covered_half_combinations(branches, dynamics_v2):
    """완성 삼합 후보의 내부 반합 위치 쌍을 구조 근거로 찾는다."""
    covered = set()
    for group in dynamics_v2['groups']:
        if (group['type'] != '삼합(三合)' or
                group['activation_status'] not in ('potential', 'conditional')):
            continue
        for formation in group['formations']:
            for left, right in combinations(formation, 2):
                pair = tuple(sorted((left, right), key=PILLARS.index))
                members = frozenset(branches[PILLARS.index(pillar)] for pillar in pair)
                if members in (frozenset(item) for item in HALF_HAPS):
                    covered.add(pair)
    return covered


def _element_evidence(event, pair, source_strengths):
    """오행 경로의 고정 방향을 기존 결과의 대표 오행으로 설명한다."""
    direction = event['element_direction']
    if event['type'] not in ('생', '극') or not direction:
        return []
    from_pillar, to_pillar = direction.split('_to_')
    source_element = source_strengths[from_pillar]['element']
    target_element = source_strengths[to_pillar]['element']
    action = 'generates' if event['type'] == '생' else 'controls'
    mark = '生' if event['type'] == '생' else '克'
    return [{
        'rule_id': (f'element:{ELEMENT_ENGLISH[source_element]}_{action}_'
                    f'{ELEMENT_ENGLISH[target_element]}'),
        'basis': (f'{ELEMENT_HANJA[source_element]}{mark}'
                  f'{ELEMENT_HANJA[target_element]}'),
    }]


def _directional_metrics(event, left, right, suppressed):
    """v2의 상태별 0 마스킹 이전 잠재량을 방향마다 재계산한다."""
    directions = [(left, right), (right, left)]
    if event['type'] in ('생', '극'):
        source, target = event['element_direction'].split('_to_')
        directions = [(source, target)]
    effects = []
    for source, target in directions:
        capacity = event['power_before'][source]
        target_capacity = event['power_before'][target]
        coefficient = event['directional_coefficients'][f'{source}_to_{target}']
        distance = event['distance_weight']
        intensity = round(capacity * distance * coefficient, 4)
        total = capacity + target_capacity
        exposure = round(intensity * capacity / total, 4) if total else 0.0
        effects.append({
            'from_pillar': source,
            'to_pillar': target,
            'acting_domain': 'guest' if PILLARS.index(source) < 2 else 'host',
            'receiving_domain': 'guest' if PILLARS.index(target) < 2 else 'host',
            'source_capacity': capacity,
            'coefficient': coefficient,
            'distance_weight': distance,
            'interaction_intensity': intensity,
            'target_exposure': exposure,
            'applied_power_delta': 0.0 if suppressed else None,
        })
    return {
        'potential_formula_id': V3_POTENTIAL_FORMULA_ID,
        'exposure_formula_id': V3_EXPOSURE_FORMULA_ID,
        'directional_effects': effects,
    }


def assemble_branch_pairs_v3(branches, dynamics_v2):
    """네 지지의 여섯 쌍을 v3 관계 후보로 옮긴다.

    v2의 양방향 force는 v3의 단일 intensity나 적용 변화량과 다르므로
    계량 상태는 pending으로 둔다. 완전 차단만 근거와 함께 적용량 0으로 둔다.
    """
    if len(branches) != 4:
        raise ValueError('지지는 4개여야 합니다.')
    source_pairs = {pair['pair_id']: pair for pair in dynamics_v2['pairwise']}
    expected = {f'{left}:{right}' for left, right in combinations(PILLARS, 2)}
    if set(source_pairs) != expected or len(dynamics_v2['pairwise']) != 6:
        raise ValueError('v2 지지 쌍에는 여섯 위치 쌍이 모두 있어야 합니다.')
    covered_halves = _covered_half_combinations(branches, dynamics_v2)
    source_strengths = dynamics_v2['branch_strengths']
    result = []
    for left, right in combinations(PILLARS, 2):
        pair_id = f'{left}:{right}'
        source_pair = source_pairs[pair_id]
        positions = (left, right)
        members = [branches[PILLARS.index(pillar)] for pillar in positions]
        if source_pair['pillars'] != list(positions):
            raise ValueError(f'{pair_id}: v2 지지 쌍의 기둥 위치가 다릅니다.')
        if [source_strengths[pillar]['branch'] for pillar in positions] != members:
            raise ValueError(f'{pair_id}: v2 지지 쌍의 원국이 다릅니다.')
        relations = []
        half_key = next((key for key in HALF_HAPS
                         if frozenset(key) == frozenset(members)), None)
        six_hap_key = next((key for key in SIX_HAPS
                            if frozenset(key) == frozenset(members)), None)
        for event in source_pair['relations']:
            original_type = event['type']
            if original_type not in RELATION_TYPES:
                raise ValueError(f'{pair_id}: 알 수 없는 관계 유형 {original_type}')
            relation_type, label = RELATION_TYPES[original_type]
            self_punishment = original_type == '형(刑)' and members[0] == members[1]
            if self_punishment:
                relation_type, label = 'self_punishment', '자형'
            structural_half = (relation_type == 'half_combine'
                               and positions in covered_halves)
            status = ('candidate_only' if self_punishment or structural_half
                      else event['activation_status'])
            suppressed = status == 'suppressed'
            quantifiable = (not structural_half and not self_punishment and
                            original_type not in V3_UNSCORED_PAIR_TYPES)
            metrics = (_directional_metrics(event, left, right, suppressed)
                       if quantifiable else None)
            reason = ('requires_school_rule' if self_punishment
                      else event['status_reason'])
            direction = None
            if original_type in ('생', '극') and event['element_direction']:
                from_pillar, to_pillar = event['element_direction'].split('_to_')
                direction = {'from_pillar': from_pillar, 'to_pillar': to_pillar}
            evidence = _element_evidence(event, positions, source_strengths)
            if event['rule_id']:
                evidence.append({'rule_id': event['rule_id'], 'basis': ''.join(members)})
            relation = {
                'relation_id': f'branch:{relation_type}:{pair_id}',
                'type': relation_type,
                'label_ko': label,
                'activation_status': status,
                'calculation_status': ('not_applicable' if structural_half else
                                       'pending' if metrics is None else
                                       'resolved' if suppressed else 'potential_calculated'),
                'status_reason': reason,
                'candidate_element': (HALF_HAPS[half_key]['element']
                                      if relation_type == 'half_combine' and half_key else
                                      SIX_HAPS[six_hap_key]
                                      if relation_type == 'combine' and six_hap_key else None),
                'formation_status': ('included_in_complete_group' if structural_half else None),
                'effect_status': 'structural_only' if structural_half else None,
                'direction': None if structural_half else direction,
                'metrics': metrics,
                'power_before': None if structural_half else event['power_before'],
                'force_dominance': None if not quantifiable or status in ('conditional', 'suppressed')
                                   else event['force_dominance'],
                'roles': None if not quantifiable or status in ('conditional', 'suppressed')
                         else event['roles'],
                'evidence': evidence,
            }
            relations.append(relation)
        if positions in covered_halves and not any(
                item['type'] == 'half_combine' for item in relations):
            relations.append({
                'relation_id': f'branch:half_combine:{pair_id}',
                'type': 'half_combine', 'label_ko': '반합',
                'candidate_element': HALF_HAPS[half_key]['element'],
                'activation_status': 'candidate_only',
                'formation_status': 'included_in_complete_group',
                'effect_status': 'structural_only',
                'calculation_status': 'not_applicable',
                'direction': None, 'metrics': None,
            })
        if members[0] == members[1]:
            relations.append({
                'relation_id': f'branch:same_branch:{pair_id}',
                'type': 'same_branch', 'label_ko': '동지',
                'activation_status': 'detected',
                'effect_status': 'structural_only',
                'calculation_status': 'not_applicable',
                'direction': None, 'metrics': None,
            })
        relation_ids = [item['relation_id'] for item in relations]
        for relation in relations:
            if relation.get('effect_status') == 'structural_only':
                continue
            direction = relation.get('direction')
            if direction is not None:
                acting = ('guest' if PILLARS.index(direction['from_pillar']) < 2
                          else 'host')
                receiving = ('guest' if PILLARS.index(direction['to_pillar']) < 2
                             else 'host')
                relation['bin_zhu_context'] = {
                    'acting_domain': acting,
                    'receiving_domain': receiving,
                    'direction': f'{acting}_to_{receiving}',
                }
            relation['interaction_context'] = {
                'coexisting_interaction_ids': [ref for ref in relation_ids
                                               if ref != relation['relation_id']],
                'resolution_status': ('suppressed' if relation['activation_status'] == 'suppressed'
                                      else 'unresolved'),
            }
        distance = PILLARS.index(right) - PILLARS.index(left)
        result.append(BranchPairV3.model_validate({
            'pair_id': pair_id,
            'pillars': list(positions),
            'branches': members,
            'pillar_distance': distance,
            'adjacent': distance == 1,
            'domain_pair': source_pair['domain_pair'],
            'relations': relations,
        }).model_dump())
    return result


def assemble_branch_groups_v3(branches, dynamics_v2, pairs_v3):
    """다자 관계를 한 구조망으로 조립하고 내부 반합 참조를 검증한다."""
    if len(branches) != 4:
        raise ValueError('지지는 4개여야 합니다.')
    relations = {
        relation['relation_id']: relation
        for pair in pairs_v3 for relation in pair['relations']
    }
    if sum(len(pair['relations']) for pair in pairs_v3) != len(relations):
        raise ValueError('v3 쌍 관계 ID가 중복되었습니다.')
    result = []
    for source in dynamics_v2['groups']:
        if source['type'] not in GROUP_TYPES:
            raise ValueError(f"알 수 없는 그룹 유형 {source['type']}")
        group_type, label, definitions = GROUP_TYPES[source['type']]
        if not source['formations']:
            raise ValueError(f"{source['type']}: 성립 조합이 없습니다.")
        first = source['formations'][0]
        first_members = {branches[PILLARS.index(pillar)] for pillar in first}
        canonical = next((members for members in definitions
                          if set(members) == first_members), None)
        if canonical is None:
            raise ValueError(f"{source['type']}: 규칙표에 없는 지지 조합입니다.")
        group_id = (f'group:{group_type}:' +
                    '_'.join(BRANCH_CODES[branch] for branch in canonical))
        positions = source['participants']
        duplicates = [branch for branch in canonical
                      if sum(branches[PILLARS.index(pillar)] == branch
                             for pillar in positions) > 1]
        condition = source['condition_evidence']
        adjacent_clashes = list(condition.get('adjacent_clashes', []))
        adjacent_clashes.extend(condition.get('adjacent_wing_clashes', []))
        source_formations = {tuple(item['pillars']): item
                             for item in source['formation_evidence']}
        formations = []
        for formation in source['formations']:
            formation = sorted(formation, key=PILLARS.index)
            members = {branches[PILLARS.index(pillar)] for pillar in formation}
            if members != set(canonical):
                raise ValueError(f'{group_id}: 성립 조합의 지지가 다릅니다.')
            evidence = source_formations.get(tuple(formation), {})
            components = []
            if group_type == 'trine' and source['activation_status'] in ('potential', 'conditional'):
                for left, right in combinations(formation, 2):
                    pair = [left, right]
                    pair_members = frozenset(branches[PILLARS.index(pillar)] for pillar in pair)
                    if pair_members not in (frozenset(item) for item in HALF_HAPS):
                        continue
                    relation_id = f'branch:half_combine:{left}:{right}'
                    relation = relations.get(relation_id)
                    if relation is None or relation.get('effect_status') != 'structural_only':
                        raise ValueError(f'{group_id}: 구조 전용 반합 {relation_id}가 없습니다.')
                    components.append({
                        'pillars': pair, 'relation_id': relation_id,
                        'effect': 'structural_only',
                    })
            directions = [
                {
                    'from_pillar': item['from_pillar'],
                    'to_pillar': item['to_pillar'],
                    'pillar_distance': abs(PILLARS.index(item['from_pillar']) -
                                           PILLARS.index(item['to_pillar'])),
                    'status': item['activation_status'],
                }
                for item in evidence.get('directional_candidates', [])
            ]
            domains = {pillar: 'guest' if PILLARS.index(pillar) < 2 else 'host'
                       for pillar in formation}
            formations.append({
                'formation_id': f'formation:{group_type}:' + ':'.join(formation),
                'pillars': formation,
                'structural_roles': evidence.get('structural_roles', {}),
                'component_pairs': components,
                'direction_candidates': directions,
                'bin_zhu_context': {
                    'domains': domains,
                    'crosses_domains': len(set(domains.values())) > 1,
                },
            })
        shared = set(formations[0]['pillars'])
        for formation in formations[1:]:
            shared.intersection_update(formation['pillars'])
        overlap = ({
            'shared_pillars': sorted(shared, key=PILLARS.index),
            'counting_policy': 'evaluate_as_one_network',
            'dominant_formation_id': None,
        } if len(formations) > 1 else None)
        result.append(BranchGroupV3.model_validate({
            'group_id': group_id,
            'type': group_type,
            'label_ko': label,
            'branches': list(canonical),
            'candidate_element': source['candidate_element'],
            'transformed_element': source['transformed_element'],
            'formation_status': source['activation_status'] or 'candidate_only',
            'transformation_status': ('transformed' if source['transformed_element']
                                      else 'undetermined'),
            'group_power': None,
            'group_power_status': 'not_scored',
            'status_reasons': source['status_reasons'],
            'condition_evidence': {
                'middle_pillars': condition.get('middle_pillars', []),
                'adjacent_clashes': adjacent_clashes,
                'duplicate_middle': len(condition.get('middle_pillars', [])) > 1,
                'duplicate_components': duplicates,
            },
            'formation_candidates': formations,
            'overlap': overlap,
            'evidence_rule_ids': ([source['action_rule_id']]
                                  if source['action_rule_id'] else []),
        }).model_dump())
    if len({group['group_id'] for group in result}) != len(result):
        raise ValueError('v3 그룹 ID가 중복되었습니다.')
    return result


def assemble_interaction_resolution_v3(pairs_v3, groups_v3):
    """명시적 차단만 확정하고 나머지 경합은 미해결로 분류한다.

    여러 관계가 공존한다는 사실만으로 주작용이나 우세 성립 조합을 고르지 않는다.
    """
    pairs = [BranchPairV3.model_validate(pair).model_dump() for pair in pairs_v3]
    groups = [BranchGroupV3.model_validate(group).model_dump() for group in groups_v3]
    expected_pairs = {f'{left}:{right}' for left, right in combinations(PILLARS, 2)}
    if {pair['pair_id'] for pair in pairs} != expected_pairs or len(pairs) != 6:
        raise ValueError('경합 판정에는 여섯 위치 쌍이 모두 필요합니다.')

    relation_by_id = {}
    pair_by_id = {}
    for pair in pairs:
        pair_by_id[pair['pair_id']] = pair
        for relation in pair['relations']:
            relation_id = relation['relation_id']
            if relation_id in relation_by_id:
                raise ValueError(f'{relation_id}: 중복 관계 ID입니다.')
            relation_by_id[relation_id] = relation
    group_by_id = {group['group_id']: group for group in groups}
    if len(group_by_id) != len(groups):
        raise ValueError('중복 그룹 ID입니다.')

    suppressed = []
    unresolved = []
    structural = set()
    for relation_id, relation in relation_by_id.items():
        if relation['effect_status'] == 'structural_only':
            structural.add(relation_id)
        elif relation['activation_status'] == 'suppressed':
            if (relation['calculation_status'] != 'resolved' or
                    relation['metrics'] is None or
                    not relation['metrics']['directional_effects'] or
                    any(effect['applied_power_delta'] != 0
                        for effect in relation['metrics']['directional_effects']) or
                    not relation['status_reason']):
                raise ValueError(f'{relation_id}: 완전 차단의 상태·근거가 부족합니다.')
            suppressed.append(relation_id)
        else:
            unresolved.append(relation_id)
    for group in groups:
        if group['formation_status'] == 'suppressed':
            if not group['status_reasons']:
                raise ValueError(f"{group['group_id']}: 억제 사유가 없습니다.")
            suppressed.append(group['group_id'])
        else:
            unresolved.append(group['group_id'])

    cases = []
    for pair in pairs:
        pair_id = pair['pair_id']
        pillars = set(pair['pillars'])
        candidates = [relation['relation_id'] for relation in pair['relations']
                      if relation['relation_id'] not in structural]
        context = [relation['relation_id'] for relation in pair['relations']
                   if relation['relation_id'] in structural]
        involved_groups = [
            group for group in groups
            if any(pillars <= set(formation['pillars'])
                   for formation in group['formation_candidates'])
        ]
        candidates.extend(group['group_id'] for group in involved_groups)
        if len(candidates) < 2:
            continue
        case_suppressed = [candidate for candidate in candidates if candidate in suppressed]
        reasons = []
        rule_ids = []
        for relation_id in case_suppressed:
            if relation_id in relation_by_id:
                relation = relation_by_id[relation_id]
                reasons.append(relation['status_reason'])
                rule_ids.extend(item['rule_id'] for item in relation['evidence'])
            else:
                group = group_by_id[relation_id]
                reasons.extend(group['status_reasons'])
                rule_ids.extend(group['evidence_rule_ids'])
        cases.append({
            'case_id': f'resolve:{pair_id}',
            'interaction_ids': candidates,
            'structural_context_relation_ids': context,
            'resolution_status': ('unresolved' if any(candidate in unresolved
                                                      for candidate in candidates)
                                  else 'suppressed'),
            'selected_interaction_ids': [],
            'suppressed_interaction_ids': case_suppressed,
            'rule_ids': list(dict.fromkeys(rule_ids)),
            'reason_codes': list(dict.fromkeys(reasons)),
        })
    for group in groups:
        overlap = group['overlap']
        if overlap is None:
            continue
        group_suppressed = group['group_id'] in suppressed
        cases.append({
            'case_id': f"resolve:{group['group_id']}:overlap",
            'group_id': group['group_id'],
            'candidate_ids': [item['formation_id']
                              for item in group['formation_candidates']],
            'resolution_status': 'suppressed' if group_suppressed else 'unresolved',
            'selected_formation_ids': [],
            'counting_policy': 'evaluate_as_one_network',
            'rule_ids': group['evidence_rule_ids'] if group_suppressed else [],
            'reason_codes': group['status_reasons'] if group_suppressed else [],
        })

    all_candidates = (set(relation_by_id) - structural) | set(group_by_id)
    if set(suppressed) & set(unresolved) or set(suppressed) | set(unresolved) != all_candidates:
        raise ValueError('관계 후보의 억제·미해결 분류가 완전하지 않습니다.')
    return InteractionResolutionV3.model_validate({
        'status': 'unresolved' if unresolved else 'resolved',
        'resolution_cases': cases,
        'active_interaction_ids': [],
        'suppressed_interaction_ids': suppressed,
        'unresolved_interaction_ids': unresolved,
    }).model_dump()
