"""기존 주변 지지 보정의 반올림 전 경로를 재생해 출력값을 검증한다.

검증 전용이다. 지지 세력을 새로 결정하거나 구조 관계를 계량하지 않는다.
"""

from math import isfinite

from services.branch_dynamics import PILLARS, _distance_weight
from services.relation_rules import AMBIENT_RATES


AMBIENT_CAP = 0.35


def _finite_nonnegative(value, label):
    if (not isinstance(value, (int, float)) or isinstance(value, bool)
            or not isfinite(value) or value < 0):
        raise ValueError(f'{label}: 유한한 0 이상의 세력이 필요합니다.')
    return value


def cap_ambient_ratio(raw_total):
    """출처별 보정의 합에 적용하는 기존 상한을 재생한다."""
    if (not isinstance(raw_total, (int, float)) or isinstance(raw_total, bool)
            or not isfinite(raw_total)):
        raise ValueError('주변 보정률 합은 유한한 숫자여야 합니다.')
    return max(-AMBIENT_CAP, min(AMBIENT_CAP, raw_total))


def replay_ambient_power(branch_strengths):
    """v3 주변 근거를 사용해 네 지지의 effective_power를 재생한다.

    raw_ratio는 source의 반올림된 after_stem_power에서 계산하되,
    ambient_evidence의 소수 6자리 표시로 반올림하기 전 값이다.
    """
    if set(branch_strengths) != set(PILLARS):
        raise ValueError('주변 보정 재생에는 네 지지의 세력이 필요합니다.')
    after_stem = {
        pillar: _finite_nonnegative(strength['after_stem_power'], pillar)
        for pillar, strength in branch_strengths.items()
    }
    replay = {}
    for target_index, target in enumerate(PILLARS):
        strength = branch_strengths[target]
        rows = strength['strength_evidence']['surroundings']
        by_source = {row['source_pillar']: row for row in rows}
        expected_sources = set(PILLARS) - {target}
        if len(by_source) != len(rows) or set(by_source) != expected_sources:
            raise ValueError(f'{target}: 주변 출처 세 개가 정확히 한 번씩 필요합니다.')
        contributions = []
        raw_total = 0.0
        for source_index, source in enumerate(PILLARS):
            if source == target:
                continue
            row = by_source[source]
            accounting = row['accounting_path']
            if accounting == 'elemental_background':
                relation = row['relation']
                if relation not in AMBIENT_RATES:
                    raise ValueError(f'{target}: 모르는 주변 오행 관계입니다.')
                capacity = after_stem[source] / (1 + after_stem[source])
                raw_ratio = (AMBIENT_RATES[relation] *
                             _distance_weight(source_index, target_index) * capacity)
            elif accounting in ('suppressed_by_active_structure',
                                'deferred_by_element_rule'):
                raw_ratio = 0.0
            else:
                raise ValueError(f'{target}: 모르는 주변 계상 경로입니다.')
            displayed = (None if row['activation_status'] == 'conditional'
                         else round(raw_ratio, 6))
            if row['adjustment_ratio'] != displayed:
                raise ValueError(f'{target}: {source}의 표시용 주변 보정률이 재생값과 다릅니다.')
            raw_total += raw_ratio
            contributions.append({
                'source_pillar': source,
                'raw_ratio': raw_ratio,
                'displayed_ratio': displayed,
                'accounting_path': accounting,
            })
        capped_total = cap_ambient_ratio(raw_total)
        before_rounding = after_stem[target] * (1 + capped_total)
        calculated = round(before_rounding, 4)
        if strength['effective_power'] != calculated:
            raise ValueError(f'{target}: effective_power가 반올림 전 경로와 다릅니다.')
        replay[target] = {
            'after_stem_power': after_stem[target],
            'contributions': contributions,
            'raw_total_ratio': raw_total,
            'capped_total_ratio': capped_total,
            'cap_applied': capped_total != raw_total,
            'power_before_rounding': before_rounding,
            'effective_power': calculated,
        }
    return replay


def replay_selected_ambient_power(branch_strengths, influence_paths, target,
                                  selected_path_ids):
    """현재 포함된 일반 보정의 일부만 선택한 진단값을 만든다.

    선택 제외는 해석 규칙의 확정이나 구조 효과의 적용을 뜻하지 않는다.
    표시용 경로 비율 대신 replay_ambient_power의 반올림 전 비율을 쓴다.
    """
    if target not in PILLARS:
        raise ValueError('선택 재생의 대상 위치가 잘못되었습니다.')
    if (isinstance(selected_path_ids, (str, bytes)) or
            not isinstance(selected_path_ids, (list, tuple, set, frozenset)) or
            any(not isinstance(item, str) for item in selected_path_ids)):
        raise ValueError('선택 경로 ID 목록이 필요합니다.')
    selected = set(selected_path_ids)
    if len(selected) != len(selected_path_ids):
        raise ValueError('선택 경로 ID가 중복됩니다.')
    by_id = {path['path_id']: path for path in influence_paths}
    if len(by_id) != len(influence_paths):
        raise ValueError('중앙 출처 경로 ID가 중복됩니다.')
    if not selected <= by_id.keys():
        raise ValueError('선택 목록에 없는 출처 경로 ID가 있습니다.')

    current = replay_ambient_power(branch_strengths)[target]
    background = {}
    for path in influence_paths:
        if (path['stage'] != 'pre_relation_background' or
                path['target']['pillar'] != target):
            continue
        if (path['target']['component'] != 'branch' or
                len(path['source_pillars']) != 1):
            raise ValueError('일반 배경은 한 출처에서 대상 지지로 향해야 합니다.')
        source = path['source_pillars'][0]
        if (source in background or
                path['path_id'] != f'path:background:{source}:{target}:branch'):
            raise ValueError('대상 일반 배경 경로의 출처 또는 ID가 중복·불일치합니다.')
        background[source] = path
    if set(background) != set(PILLARS) - {target}:
        raise ValueError('대상 지지의 일반 배경 경로 세 개가 필요합니다.')

    eligible = set()
    unavailable = []
    for row in current['contributions']:
        path = background[row['source_pillar']]
        if row['accounting_path'] == 'elemental_background':
            expected_decision = 'include'
        else:
            expected_decision = ('undetermined' if row['displayed_ratio'] is None
                                 else 'exclude')
        quantity = path['quantity']
        expected_value = row['displayed_ratio']
        quantity_matches = (quantity is None and expected_value is None) or (
            quantity is not None and quantity['unit'] == 'adjustment_ratio' and
            not isinstance(quantity['value'], bool) and
            quantity['value'] == expected_value)
        if (path['evidence_level'] != 'calculated' or
                path['accounting_decision'] != expected_decision or
                not quantity_matches):
            raise ValueError('중앙 경로의 계상 상태·표시값이 현재 주변 근거와 다릅니다.')
        if expected_decision == 'include':
            eligible.add(path['path_id'])
        else:
            unavailable.append(path['path_id'])
    if not selected <= eligible:
        raise ValueError('다른 대상·구조 후보·억제 또는 미정 경로는 선택할 수 없습니다.')

    raw_total = 0.0
    selected_contributions = []
    for row in current['contributions']:
        path_id = background[row['source_pillar']]['path_id']
        if path_id in selected:
            raw_total += row['raw_ratio']
            selected_contributions.append({'path_id': path_id, **row})
    capped_total = cap_ambient_ratio(raw_total)
    before_rounding = current['after_stem_power'] * (1 + capped_total)
    background_power = round(before_rounding, 4)
    return {
        'diagnostic_only': True,
        'target_pillar': target,
        'input_power_ref': f'branch_strengths.{target}.after_stem_power',
        'selected_path_ids': sorted(selected),
        'omitted_path_ids': sorted(eligible - selected),
        'unavailable_path_ids': sorted(unavailable),
        'contributions': selected_contributions,
        'raw_total_ratio': raw_total,
        'capped_total_ratio': capped_total,
        'cap_applied': raw_total != capped_total,
        'power_before_rounding': before_rounding,
        'background_power': background_power,
        'current_effective_power': current['effective_power'],
        'background_power_delta': round(background_power - current['effective_power'], 4),
    }
