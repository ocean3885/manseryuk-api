"""지지 작용 v3 출력의 구조·참조·수치 상태 계약 검사.

설계 샘플의 가상 수치를 실제 계산 결과로 취급하지 않는다. 관계 성립과
계수의 타당성은 별도 규칙/계산 단계에서 검증한다.
"""

from itertools import combinations
from math import isfinite
from numbers import Real


PILLARS = ('year', 'month', 'day', 'hour')
PAIR_IDS = {f'{left}:{right}' for left, right in combinations(PILLARS, 2)}
CALCULATION_STATUSES = {
    'not_applicable', 'pending', 'potential_calculated', 'resolved',
}
BRANCH_CODES = {
    '子': 'zi', '丑': 'chou', '寅': 'yin', '卯': 'mao',
    '辰': 'chen', '巳': 'si', '午': 'wu', '未': 'wei',
    '申': 'shen', '酉': 'you', '戌': 'xu', '亥': 'hai',
}


def _check(condition, message):
    if not condition:
        raise ValueError(message)


def _id_set(value, label):
    _check(isinstance(value, list), f'{label}: list가 필요합니다.')
    _check(all(isinstance(item, str) for item in value),
           f'{label}: 문자열 ID만 허용합니다.')
    _check(len(value) == len(set(value)), f'{label}: 중복 ID가 있습니다.')
    return set(value)


def _number(value):
    return isinstance(value, Real) and not isinstance(value, bool) and isfinite(value)


def _check_metrics(relation):
    relation_id = relation['relation_id']
    status = relation.get('calculation_status')
    metrics = relation.get('metrics')
    _check(status in CALCULATION_STATUSES,
           f'{relation_id}: calculation_status가 잘못되었습니다.')
    structural = relation.get('effect_status') == 'structural_only'
    if structural:
        _check(status == 'not_applicable' and metrics is None and
               relation.get('direction') is None,
               f'{relation_id}: 구조 전용 관계에 독립 작용량을 줄 수 없습니다.')
        return True
    _check(status != 'not_applicable',
           f'{relation_id}: 계량 후보에 not_applicable을 쓸 수 없습니다.')
    _check(metrics is None or isinstance(metrics, dict),
           f'{relation_id}: metrics는 객체 또는 null이어야 합니다.')
    if status == 'pending':
        _check(metrics is None, f'{relation_id}: pending에는 계산된 수치를 넣을 수 없습니다.')
    else:
        _check(metrics is not None and
               isinstance(metrics.get('potential_formula_id'), str) and
               isinstance(metrics.get('exposure_formula_id'), str) and
               isinstance(metrics.get('directional_effects'), list) and
               bool(metrics['directional_effects']),
               f'{relation_id}: 방향별 잠재 수치와 산식 ID가 필요합니다.')
        directions = set()
        pillars = relation_id.split(':')[-2:]
        for effect in metrics['directional_effects']:
            direction = (effect.get('from_pillar'), effect.get('to_pillar'))
            _check(direction in ((pillars[0], pillars[1]), (pillars[1], pillars[0])) and
                   direction not in directions,
                   f'{relation_id}: 방향이 중복되거나 위치 쌍과 다릅니다.')
            directions.add(direction)
            _check(effect.get('acting_domain') == ('guest' if PILLARS.index(direction[0]) < 2
                                                    else 'host') and
                   effect.get('receiving_domain') == ('guest' if PILLARS.index(direction[1]) < 2
                                                      else 'host'),
                   f'{relation_id}: 방향별 빈주 위치가 기둥과 다릅니다.')
            _check(all(_number(effect.get(key)) and effect[key] >= 0 for key in (
                'source_capacity', 'coefficient', 'distance_weight',
                'interaction_intensity', 'target_exposure',
            )), f'{relation_id}: 방향별 잠재 수치는 유한한 0 이상의 숫자여야 합니다.')
            applied = effect.get('applied_power_delta')
            if status == 'potential_calculated':
                _check(applied is None,
                       f'{relation_id}: 잠재 강도 계산만으로 실제 적용량을 확정할 수 없습니다.')
            else:
                _check(_number(applied),
                       f'{relation_id}: resolved의 실제 적용량은 숫자여야 합니다.')
        if relation['type'] in ('generate', 'control'):
            direction = relation.get('direction')
            _check(direction is not None and directions == {
                (direction['from_pillar'], direction['to_pillar'])},
                f'{relation_id}: 생·극은 오행상 방향 하나만 허용합니다.')
        else:
            _check(len(directions) == 2,
                   f'{relation_id}: 양방향 관계에는 두 방향의 수치가 필요합니다.')
    activation = relation.get('activation_status')
    if activation == 'conditional':
        _check(status != 'resolved',
               f'{relation_id}: 조건부 유보에 실제 적용량을 확정할 수 없습니다.')
    if activation == 'suppressed':
        _check(status == 'resolved' and metrics is not None and
               all(effect['applied_power_delta'] == 0
                   for effect in metrics['directional_effects']) and
               bool(relation.get('status_reason') or relation.get('status_reasons')),
               f'{relation_id}: 완전 차단은 적용량 0과 근거가 필요합니다.')
    return False


def validate_branch_dynamics_v3(payload):
    """계약 위반 시 위치가 포함된 ValueError를 발생시킨다."""
    _check(isinstance(payload, dict), '최상위 응답은 객체여야 합니다.')
    required = {
        'meta', 'chart_context', 'stem_dynamics', 'branch_dynamics',
        'interaction_resolution', 'work_dynamics', 'llm_interpretation_payload',
    }
    _check(required <= payload.keys(), 'v3 최상위 필드가 빠졌습니다.')
    _check(set(payload['chart_context']['pillars']) == set(PILLARS),
           'chart_context.pillars는 네 기둥을 포함해야 합니다.')
    dynamics = payload['branch_dynamics']
    _check(set(dynamics['branch_strengths']) == set(PILLARS),
           'branch_strengths는 네 기둥을 포함해야 합니다.')
    pairs = dynamics['pairwise']
    _check(isinstance(pairs, list) and len(pairs) == 6,
           'pairwise는 여섯 위치 쌍이어야 합니다.')
    _check(_id_set([pair['pair_id'] for pair in pairs], 'pairwise.pair_id') == PAIR_IDS,
           'pairwise의 위치 쌍이 빠지거나 잘못되었습니다.')

    relations = {}
    structural_ids = set()
    for pair in pairs:
        pair_id = pair['pair_id']
        _check(pair['pillars'] == pair_id.split(':'),
               f'{pair_id}: pillars와 pair_id가 다릅니다.')
        _check(pair['branches'] == [payload['chart_context']['pillars'][pillar]['branch']
                                      for pillar in pair['pillars']],
               f'{pair_id}: chart_context의 지지와 다릅니다.')
        for relation in pair['relations']:
            relation_id = relation['relation_id']
            expected_id = f"branch:{relation['type']}:{pair_id}"
            _check(relation_id == expected_id,
                   f'{relation_id}: 쌍 관계 ID 형식이 잘못되었습니다.')
            _check(relation_id not in relations, f'{relation_id}: 중복 관계 ID입니다.')
            relations[relation_id] = relation
            if _check_metrics(relation):
                structural_ids.add(relation_id)

    groups = {}
    formations = {}
    for group in dynamics['groups']:
        group_id = group['group_id']
        branches = group['branches']
        _check(all(branch in BRANCH_CODES for branch in branches),
               f'{group_id}: 알 수 없는 지지 코드가 있습니다.')
        expected_id = (f"group:{group['type']}:" +
                       '_'.join(BRANCH_CODES[branch] for branch in branches))
        _check(group_id == expected_id,
               f'{group_id}: 그룹 ID는 종류·정형 지지 조합을 사용해야 합니다.')
        _check(group_id not in groups, f'{group_id}: 중복 그룹 ID입니다.')
        groups[group_id] = group
        _check(group['group_power_status'] == 'not_scored' and
               group['group_power'] is None,
               f'{group_id}: 그룹에 독립 작용량을 부여할 수 없습니다.')
        for formation in group['formation_candidates']:
            formation_id = formation['formation_id']
            pillars = formation['pillars']
            _check(pillars == sorted(pillars, key=PILLARS.index) and
                   len(pillars) == len(set(pillars)),
                   f'{formation_id}: 기둥 위치는 중복 없이 정렬해야 합니다.')
            _check(formation_id == f"formation:{group['type']}:" + ':'.join(pillars),
                   f'{formation_id}: 성립 조합 ID 형식이 잘못되었습니다.')
            _check(formation_id not in formations,
                   f'{formation_id}: 중복 성립 조합 ID입니다.')
            formations[formation_id] = group_id
            for component in formation['component_pairs']:
                ref = component['relation_id']
                _check(ref in relations, f'{formation_id}: 존재하지 않는 쌍 관계 {ref}')
                if component['effect'] == 'structural_only':
                    _check(ref in structural_ids,
                           f'{formation_id}: 구조 근거의 관계 상태가 다릅니다.')
        overlap = group.get('overlap')
        if overlap is not None:
            _check(overlap['counting_policy'] == 'evaluate_as_one_network',
                   f'{group_id}: 중복 조합은 한 구조망으로 다뤄야 합니다.')
            dominant = overlap.get('dominant_formation_id')
            _check(dominant is None or formations.get(dominant) == group_id,
                   f'{group_id}: 우세 조합 참조가 잘못되었습니다.')

    interactions = set(relations) | set(groups)
    for relation in relations.values():
        context = relation.get('interaction_context') or {}
        refs = _id_set(context.get('coexisting_interaction_ids', []),
                       'coexisting_interaction_ids')
        _check(refs <= interactions, '공존 관계에 존재하지 않는 ID가 있습니다.')

    resolution = payload['interaction_resolution']
    global_sets = []
    for key in ('active_interaction_ids', 'suppressed_interaction_ids',
                'unresolved_interaction_ids'):
        refs = _id_set(resolution[key], key)
        _check(refs <= interactions - structural_ids,
               f'{key}: 구조 전용 또는 존재하지 않는 관계를 포함합니다.')
        global_sets.append(refs)
    _check(not any(left & right for left, right in combinations(global_sets, 2)),
           '경합 결과의 활성·억제·미해결 집합이 겹칩니다.')

    for case in resolution['resolution_cases']:
        case_id = case['case_id']
        candidates = _id_set(case.get('interaction_ids', []),
                             f'{case_id}.interaction_ids')
        _check(candidates <= interactions - structural_ids,
               f'{case_id}: 경합 후보 ID가 잘못되었습니다.')
        for key in ('selected_interaction_ids', 'suppressed_interaction_ids'):
            _check(_id_set(case.get(key, []), f'{case_id}.{key}') <= candidates,
                   f'{case_id}: 선택·억제 ID는 해당 경합 후보여야 합니다.')
        context = _id_set(case.get('structural_context_relation_ids', []),
                          f'{case_id}.structural_context_relation_ids')
        _check(context <= structural_ids,
               f'{case_id}: 구조 맥락 ID가 잘못되었습니다.')
        group_id = case.get('group_id')
        if group_id is not None:
            _check(group_id in groups, f'{case_id}: 그룹 ID가 없습니다.')
        candidates = _id_set(case.get('candidate_ids', []),
                             f'{case_id}.candidate_ids')
        _check(all(formations.get(ref) == group_id for ref in candidates),
               f'{case_id}: 다른 그룹의 성립 조합을 참조합니다.')
        _check(_id_set(case.get('selected_formation_ids', []),
                       f'{case_id}.selected_formation_ids') <= candidates,
               f'{case_id}: 선택된 성립 조합이 후보에 없습니다.')

    for path in payload['work_dynamics']['candidate_paths']:
        path_id = path['path_id']
        sources = _id_set(path['source_interaction_ids'],
                          f'{path_id}.source_interaction_ids')
        _check(sources <= interactions - structural_ids,
               f'{path_id}: 작공 원천에 구조 전용 관계가 있습니다.')
        context = _id_set(path.get('structural_context_relation_ids', []),
                          f'{path_id}.structural_context_relation_ids')
        _check(context <= structural_ids,
               f'{path_id}: 구조 맥락 ID가 잘못되었습니다.')

    llm = payload['llm_interpretation_payload']
    for item in llm['structural_facts'] + llm['unresolved_mechanisms']:
        refs = _id_set(item.get('ref_ids', []), 'llm.ref_ids')
        _check(refs <= interactions | set(formations),
               'LLM 자료에 존재하지 않는 참조 ID가 있습니다.')
