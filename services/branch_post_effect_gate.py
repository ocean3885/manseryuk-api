"""지지별 작용 후 세력의 계산 가능 여부를 보수적으로 점검한다.

이 모듈은 손실·지원량을 계산하지 않는다. 미해결 근거만 수집한다.


기존 내부 모델의 출력 차단과 회귀 검증용이다. 통과 여부를 수치화 재개 지시로 사용하지 않는다.
"""

from math import isfinite

from services.branch_influence_paths import PILLARS
from services.relation_rules import RULE_PROFILE


def assess_post_effect_readiness(pillar, pairs, groups, influence_paths,
                                 resolution=None):
    """지지 하나의 차단 근거와 잠정 관계 ID를 돌려준다.

    후보 전용·구조 전용 관계는 독립 작용량의 차단 근거로 세지 않는다.
    현재 규칙에서 성립·조건부·잠재 상태인 관계는 실제 적용량이 확정되지
    않았다면 두 참여 지지 모두의 최종 세력을 유보한다.
    """
    suppressed_ids = set((resolution or {}).get('suppressed_interaction_ids', []))
    blockers = {}
    provisional_ids = set()
    for pair in pairs:
        if pillar not in pair['pillars']:
            continue
        for relation in pair['relations']:
            relation_id = relation['relation_id']
            if (relation_id in suppressed_ids or
                    relation.get('effect_status') == 'structural_only'):
                continue
            activation = relation['activation_status']
            if activation in ('suppressed', 'candidate_only', 'detected'):
                continue
            calculation = relation['calculation_status']
            if activation == 'active' and calculation == 'provisional_calculated':
                provisional_ids.add(relation_id)
            elif activation != 'active' or calculation != 'resolved':
                blockers[relation_id] = 'relation_effect_unresolved'
    for group in groups:
        group_id = group['group_id']
        if group_id in suppressed_ids or group['formation_status'] == 'suppressed':
            continue
        if any(pillar in formation['pillars']
               for formation in group['formation_candidates']):
            blockers[group_id] = 'group_effect_unresolved'
    for path in influence_paths:
        if path['target']['pillar'] != pillar:
            continue
        interaction_refs = [ref['id'] for ref in path['evidence_refs']
                            if ref['kind'] == 'interaction']
        if interaction_refs and all(ref in suppressed_ids for ref in interaction_refs):
            continue
        decision = path['accounting_decision']
        if decision == 'undetermined':
            blockers[path['path_id']] = 'path_accounting_unresolved'
        elif decision in ('replace', 'separate_effect'):
            # 현재 지지별 최종 집계기는 대체·독립 작용량을 계상하지 않는다.
            blockers[path['path_id']] = 'path_aggregation_unverified'
    return {
        'blockers': [{'ref_id': ref_id, 'reason': blockers[ref_id]}
                     for ref_id in sorted(blockers)],
        'provisional_interaction_ids': sorted(provisional_ids),
    }


def build_post_effect_trace_skeleton(pillar, strength, pairs, groups,
                                     influence_paths, resolution=None,
                                     *, known_unmodeled_mechanism_ids=()):
    """현재 출처와 차단 근거를 참조한다. 최종 세력은 계산하지 않는다."""
    if pillar not in PILLARS:
        raise ValueError('알 수 없는 지지 위치입니다.')
    value = strength.get('after_stem_power')
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not isfinite(value) or value < 0):
        raise ValueError(f'{pillar}: 동주 천간 후 기준 세력이 필요합니다.')
    target_paths = [path for path in influence_paths
                    if path['target']['pillar'] == pillar]
    expected_ids = {path['path_id'] for path in target_paths}
    if (len(expected_ids) != len(target_paths) or
            set(strength['influence_path_ids']) != expected_ids or
            len(strength['influence_path_ids']) != len(expected_ids)):
        raise ValueError(f'{pillar}: 출처 경로 참조가 다릅니다.')
    readiness = assess_post_effect_readiness(
        pillar, pairs, groups, influence_paths, resolution)
    if isinstance(known_unmodeled_mechanism_ids, (str, bytes)) or any(
            not isinstance(item, str) or not item
           for item in known_unmodeled_mechanism_ids):
        raise ValueError('미지원 기전 ID는 비어 있지 않은 문자열이어야 합니다.')
    known_missing = sorted(set(known_unmodeled_mechanism_ids))
    unresolved = readiness['blockers'] + [
        {'ref_id': f'mechanism:{mechanism}', 'reason': 'unmodeled_mechanism'}
        for mechanism in known_missing
    ]
    included = []
    excluded = []
    replacements = []
    for path in target_paths:
        decision = path['accounting_decision']
        if path['stage'] == 'pre_relation_background':
            if decision == 'include':
                included.append(path['path_id'])
            elif decision == 'exclude':
                excluded.append(path['path_id'])
        if decision == 'replace':
            replacements.append({
                'replacement_path_id': path['path_id'],
                'replaced_path_ids': sorted(path['replaces_path_ids']),
            })
    return {
        'status': 'not_calculated',
        'readiness_status': ('incomplete' if unresolved else 'no_known_blockers'),
        'input_power_ref': f'branch_strengths.{pillar}.after_stem_power',
        'background': {
            'included_path_ids': sorted(included),
            'excluded_path_ids': sorted(excluded),
            'replacement_sets': sorted(replacements,
                                       key=lambda item: item['replacement_path_id']),
        },
        'reconciled_pre_effect_power': None,
        'applied_effect_refs': [],
        'available_provisional_interaction_ids': readiness[
            'provisional_interaction_ids'],
        'aggregation_formula_id': None,
        'rounding_policy_id': None,
        'model_scope': {
            'profile_id': RULE_PROFILE,
            'coverage_status': 'partial' if known_missing else 'not_assessed',
            'unmodeled_mechanism_ids': known_missing,
        },
        'unresolved_refs': sorted(unresolved, key=lambda item: item['ref_id']),
    }
