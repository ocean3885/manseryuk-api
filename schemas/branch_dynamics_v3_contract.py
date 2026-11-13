"""지지 작용 v3 출력의 구조·참조·수치 상태 계약 검사.

설계 샘플의 가상 수치를 실제 계산 결과로 취급하지 않는다. 관계 성립과
계수의 타당성은 별도 규칙/계산 단계에서 검증한다.
"""

from itertools import combinations
from math import isfinite, prod
from numbers import Real

from services.branch_influence_paths import validate_influence_paths
from services.branch_post_effect_gate import assess_post_effect_readiness


PILLARS = ('year', 'month', 'day', 'hour')
PAIR_IDS = {f'{left}:{right}' for left, right in combinations(PILLARS, 2)}
CALCULATION_STATUSES = {
    'not_applicable', 'pending', 'potential_calculated',
    'provisional_calculated', 'resolved',
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
        self_effects = metrics.get('self_effects', [])
        _check(isinstance(self_effects, list),
               f'{relation_id}: 자기 손실은 목록이어야 합니다.')
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
                       f'{relation_id}: 계산된 적용량은 숫자여야 합니다.')
        if status == 'provisional_calculated':
            direction = relation.get('direction')
            _check(relation['type'] == 'clash' and
                   relation.get('activation_status') == 'active' and
                   direction is not None and len(directions) == 1 and
                   directions == {(direction['from_pillar'], direction['to_pillar'])} and
                   len(self_effects) == 1 and
                   isinstance(metrics.get('applied_formula_id'), str) and
                   isinstance(metrics.get('calibration_version'), str) and
                   metrics.get('calibration_status') == 'provisional',
                   f'{relation_id}: 잠정 충 계산의 방향·보정 정보가 부족합니다.')
            impact = metrics['directional_effects'][0]
            own = self_effects[0]
            _check(impact.get('mechanism') == 'primary_shock' and
                   own.get('mechanism') == 'attacker_self_loss' and
                   own.get('pillar') == direction['from_pillar'] and
                   all(_number(effect.get('candidate_loss_rate')) and
                       0 <= effect['candidate_loss_rate'] <= 1
                       for effect in (impact, own)) and
                   _number(own.get('power_delta')),
                   f'{relation_id}: 충격·자기 손실의 근거와 비율이 잘못되었습니다.')
            before = relation.get('power_before') or {}
            target_power = before.get(direction['to_pillar'])
            actor_power = before.get(direction['from_pillar'])
            _check(_number(target_power) and _number(actor_power) and
                   -target_power - 0.0001 <= impact['applied_power_delta'] <= 0 and
                   -actor_power - 0.0001 <= own['power_delta'] <= 0,
                   f'{relation_id}: 잠정 손실이 기준 세력 범위를 벗어났습니다.')
        else:
            _check(not self_effects and metrics.get('applied_formula_id') is None and
                   metrics.get('calibration_version') is None and
                   metrics.get('calibration_status') is None,
                   f'{relation_id}: 잠정 계산 외의 자기 손실을 허용하지 않습니다.')
        if relation['type'] in ('generate', 'control'):
            direction = relation.get('direction')
            _check(direction is not None and directions == {
                (direction['from_pillar'], direction['to_pillar'])},
                f'{relation_id}: 생·극은 오행상 방향 하나만 허용합니다.')
        elif status != 'provisional_calculated':
            _check(len(directions) == 2,
                   f'{relation_id}: 양방향 관계에는 두 방향의 수치가 필요합니다.')
    activation = relation.get('activation_status')
    if activation in ('conditional', 'detected'):
        _check(status not in ('resolved', 'provisional_calculated'),
               f'{relation_id}: 탐지·유보 상태에서 실제 적용량을 확정할 수 없습니다.')
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
    for pillar, strength in dynamics['branch_strengths'].items():
        status = strength.get('post_effect_status')
        power = strength.get('post_effect_power')
        _check(status in ('not_calculated', 'incomplete', 'provisional', 'resolved'),
               f'{pillar}: 작용 후 세력의 계산 상태가 잘못되었습니다.')
        if status in ('not_calculated', 'incomplete'):
            _check(power is None,
                   f'{pillar}: 미완성 작용 후 세력을 숫자로 출력할 수 없습니다.')
        else:
            _check(_number(power) and power >= 0,
                   f'{pillar}: 작용 후 세력은 유한한 0 이상의 숫자여야 합니다.')
    pairs = dynamics['pairwise']
    _check(isinstance(pairs, list) and len(pairs) == 6,
           'pairwise는 여섯 위치 쌍이어야 합니다.')
    _check(_id_set([pair['pair_id'] for pair in pairs], 'pairwise.pair_id') == PAIR_IDS,
           'pairwise의 위치 쌍이 빠지거나 잘못되었습니다.')

    relations = {}
    structural_ids = set()
    provisional_losses = {pillar: [] for pillar in PILLARS}
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
            if relation.get('calculation_status') == 'provisional_calculated':
                direction = relation.get('direction') or {}
                source = direction.get('from_pillar')
                target = direction.get('to_pillar')
                _check(source in PILLARS and target in PILLARS and
                       payload['chart_context']['pillars'][source]['branch'] == '子' and
                       payload['chart_context']['pillars'][target]['branch'] == '午',
                       f'{relation_id}: 子午충의 일차 방향은 子에서 午입니다.')
            if _check_metrics(relation):
                structural_ids.add(relation_id)
            if relation.get('calculation_status') == 'provisional_calculated':
                metrics = relation['metrics']
                for pillar, effect, key in (
                    (target, metrics['directional_effects'][0], 'applied_power_delta'),
                    (source, metrics['self_effects'][0], 'power_delta'),
                ):
                    provisional_losses[pillar].append((
                        relation['power_before'][pillar],
                        effect['candidate_loss_rate'], effect[key],
                    ))

    for pillar, losses in provisional_losses.items():
        if not losses:
            continue
        base = losses[0][0]
        _check(all(abs(item[0] - base) <= 0.00001 for item in losses),
               f'{pillar}: 다중 충의 기준 세력이 일치하지 않습니다.')
        expected = round(base * (1 - prod(1 - rate for _, rate, _ in losses)), 4)
        actual = round(-sum(delta for _, _, delta in losses), 4)
        _check(actual == expected,
               f'{pillar}: 잠정 충 손실의 합계가 집계값과 다릅니다.')

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
    influence_paths = validate_influence_paths(
        dynamics['influence_paths'],
        [payload['chart_context']['pillars'][pillar]['branch'] for pillar in PILLARS],
        interaction_ids=interactions, formation_ids=formations,
    )
    paths_by_target = {pillar: set() for pillar in PILLARS}
    background_by_target = {pillar: {} for pillar in PILLARS}
    for path in influence_paths:
        target = path['target']['pillar']
        paths_by_target[target].add(path['path_id'])
        if path['stage'] == 'pre_relation_background':
            _check(path['target']['component'] == 'branch' and
                   len(path['source_pillars']) == 1,
                   f"{path['path_id']}: 일반 배경은 한 출처에서 지지로 향해야 합니다.")
            source = path['source_pillars'][0]
            _check(path['path_id'] == f'path:background:{source}:{target}:branch' and
                   source not in background_by_target[target],
                   f"{path['path_id']}: 일반 배경 경로 ID가 다르거나 중복됩니다.")
            background_by_target[target][source] = path
    for pillar, strength in dynamics['branch_strengths'].items():
        ids = _id_set(strength['influence_path_ids'], f'{pillar}.influence_path_ids')
        _check(ids == paths_by_target[pillar],
               f'{pillar}: 출처 경로의 대상별 참조가 다릅니다.')
        surroundings = strength['strength_evidence']['surroundings']
        ambient_by_source = {item['source_pillar']: item for item in surroundings}
        _check(len(ambient_by_source) == len(surroundings),
               f'{pillar}: 주변 출처가 중복됩니다.')
        background = background_by_target[pillar]
        _check(set(background) <= set(ambient_by_source),
               f'{pillar}: 주변 근거가 없는 일반 배경 경로가 있습니다.')
        if strength['effective_power'] is not None:
            _check(set(background) == set(ambient_by_source),
                   f'{pillar}: 계산된 잠정 세력의 일반 배경 경로가 빠졌습니다.')
        for source, path in background.items():
            ambient = ambient_by_source[source]
            accounting = ambient['accounting_path']
            if accounting == 'elemental_background':
                expected_decision = 'include'
                expected_value = ambient['adjustment_ratio']
            elif accounting == 'suppressed_by_active_structure':
                expected_decision, expected_value = 'exclude', 0.0
            elif accounting == 'deferred_by_element_rule':
                conditional = ambient['activation_status'] == 'conditional'
                expected_decision = 'undetermined' if conditional else 'exclude'
                expected_value = None if conditional else 0.0
            else:
                raise ValueError(f"{path['path_id']}: 일반 배경 계상 경로가 잘못되었습니다.")
            quantity = path['quantity']
            _check(path['accounting_decision'] == expected_decision and
                   ((quantity is None and expected_value is None) or
                    (quantity is not None and
                     quantity['unit'] == 'adjustment_ratio' and
                     quantity['value'] == expected_value)),
                   f"{path['path_id']}: 주변 근거와 출처 경로의 계상값이 다릅니다.")
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

    for pillar, strength in dynamics['branch_strengths'].items():
        status = strength['post_effect_status']
        readiness = assess_post_effect_readiness(
            pillar, pairs, dynamics['groups'], influence_paths, resolution)
        blockers = readiness['blockers']
        if status == 'incomplete':
            _check(bool(blockers),
                   f'{pillar}: 미완성 상태에는 미해결 작용 근거가 필요합니다.')
        elif status in ('provisional', 'resolved'):
            _check(not blockers,
                   f'{pillar}: 미해결 작용이 있어 작용 후 세력을 확정할 수 없습니다: '
                   + ', '.join(item['ref_id'] for item in blockers))
            raise ValueError(f'{pillar}: 작용 후 집계식과 전체 기여 근거가 아직 없습니다.')

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
