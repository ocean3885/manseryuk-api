"""기존 탐지 결과를 읽어 원국 8글자의 관계 조회 초안을 조립한다.

현행 API·지지 계산값은 수정하지 않으며, 관계별 작용량도 계산하지 않는다.
"""

from collections import Counter
from itertools import combinations

from schemas.character_relation_index import (
    CHARACTER_IDS, NOT_EVALUATED_MECHANISMS, CharacterRelationIndex, PILLARS,
)
from services.branch_dynamics import _stem_branch_relation
from services.branch_dynamics_v3_assembler import (
    GROUP_TYPES, RELATION_TYPES, assemble_branch_groups_v3, assemble_branch_pairs_v3,
)
from services.five_elements import BRANCH_ELEMENT_MAP, STEM_ELEMENT_MAP
from services.constants import JIJANGGAN_DETAILED
from services.relation_rules import JAHAB_MAP, STEM_RESTRAIN
from services.relations import check_jahab
from services.xu_shi import analyze_xu_shi_dynamics


STEM_MATRIX_TYPES = {'천간합(天干合)': 'combine', '천간충(天干沖)': 'clash'}
STEM_ANALYSIS_KEYS = {'combine': 'combinations', 'clash': 'conflict'}
BRANCH_ANALYSIS_KEYS = {
    'six_haps_all': '육합(六合)', 'chungs': '충(沖)',
    'cheons': '천(穿)', 'breaks': '파(破)',
    'punishments': '형(刑)', 'half_haps': '반합(半合)',
    'gong_haps': '공합(拱合)', 'hidden_stem_haps': '암합(暗合)',
}


def _ref(system, *, relation_id=None, location=None):
    return {'system': system, 'relation_id': relation_id, 'location': location}


def _direction(source, target, basis='elemental'):
    return {'from_character': source, 'to_character': target, 'basis': basis}


def _row(relation_id, kind, participants, status, source_refs, *,
         reason=None, direction=None, element=None, hidden_stem=None,
         formations=(), rule_ids=()):
    return {
        'relation_id': relation_id,
        'type': kind,
        'participants': participants,
        'activation_status': status,
        'status_reason': reason,
        'direction': direction,
        'candidate_element': element,
        'hidden_stem': hidden_stem,
        'formation_candidates': list(formations),
        'rule_ids': list(dict.fromkeys(rule_ids)),
        'source_refs': source_refs,
    }


def _branch_matrix_ids(matrix, branches):
    """기존 매트릭스의 지지 쌍 ID를 v3의 위치별 ID에 대응시킨다."""
    mapping = {}
    for item in matrix:
        if item['category'] != '지지' or item['relation_scope'] == 'group':
            continue
        left, right = item['participants']
        original_type = item['type']
        if original_type not in RELATION_TYPES:
            raise ValueError(f'모르는 지지 관계 유형: {original_type}')
        kind = RELATION_TYPES[original_type][0]
        if kind == 'punishment' and branches[PILLARS.index(left)] == branches[PILLARS.index(right)]:
            kind = 'self_punishment'
        relation_id = f'branch:{kind}:{left}:{right}'
        if relation_id in mapping:
            raise ValueError(f'{relation_id}: 중복된 원본 지지 관계입니다.')
        mapping[relation_id] = item
    return mapping


def _check_branch_analysis(matrix, analysis, branches):
    expected = Counter()
    for item in matrix:
        if item['category'] != '지지' or item['relation_scope'] != 'pairwise':
            continue
        left, right = (PILLARS.index(pillar) for pillar in item['participants'])
        expected[(item['type'], left, right)] += 2
    observed = Counter()
    for index, pillar in enumerate(PILLARS):
        relations = analysis['pillars'][pillar]['branch']['relations']
        for key, kind in BRANCH_ANALYSIS_KEYS.items():
            for item in relations[key] or []:
                other = item['with_index']
                if (other == index or not 0 <= other < 4
                        or item['my'] != branches[index]
                        or item['with'] != branches[other]):
                    raise ValueError(f'{pillar}: 지지 관계의 위치·글자가 다릅니다.')
                left, right = sorted((index, other))
                observed[(kind, left, right)] += 1
    if observed != expected:
        raise ValueError('지지 매트릭스와 글자별 관계 후보가 다릅니다.')


def _stem_matrix_rows(matrix, analysis, stems):
    rows = []
    by_kind = {'combine': set(), 'clash': set()}
    for item in matrix:
        if item['category'] != '천간':
            continue
        kind = STEM_MATRIX_TYPES.get(item['type'])
        if kind is None:
            raise ValueError(f"모르는 천간 관계 유형: {item['type']}")
        left, right = item['participants']
        by_kind[kind].add((left, right))
        rows.append(_row(
            f'stem:{kind}:{left}:{right}', kind,
            [f'{left}.stem', f'{right}.stem'], 'detected',
            [_ref('interaction_matrix', relation_id=item['relation_id'])],
            element=item.get('candidate_element'),
        ))
    for kind, analysis_key in STEM_ANALYSIS_KEYS.items():
        observed = []
        for index, pillar in enumerate(PILLARS):
            matches = analysis['pillars'][pillar]['stem']['relations'][analysis_key] or []
            for match in matches:
                other_index = match['with_index']
                if (other_index == index or not 0 <= other_index < 4
                        or match['my'] != stems[index]
                        or match['with'] != stems[other_index]):
                    raise ValueError(f'{pillar}: 천간 상대의 위치·글자가 다릅니다.')
                observed.append((PILLARS[min(index, other_index)],
                                 PILLARS[max(index, other_index)]))
        expected = by_kind[kind]
        if set(observed) != expected or any(observed.count(pair) != 2 for pair in expected):
            raise ValueError(f'천간 {kind}의 매트릭스와 글자별 분석 결과가 다릅니다.')
    return rows


def _stem_control_rows(stems, analysis):
    expected = {}
    for left_index, right_index in combinations(range(4), 2):
        if (stems[left_index], stems[right_index]) in STEM_RESTRAIN:
            expected[(left_index, right_index)] = left_index
        elif (stems[right_index], stems[left_index]) in STEM_RESTRAIN:
            expected[(left_index, right_index)] = right_index
    observed_to = {}
    observed_me = set()
    for index, pillar in enumerate(PILLARS):
        restrain = analysis['pillars'][pillar]['stem']['relations']['restrain'] or {}
        for match in restrain.get('restrain_to', []):
            other = match['with_index']
            if (not 0 <= other < 4 or other == index
                    or match['my'] != stems[index]
                    or match['with'] != stems[other]):
                raise ValueError(f'{pillar}: 천간 극 상대의 위치·글자가 다릅니다.')
            pair = tuple(sorted((index, other)))
            if pair in observed_to:
                raise ValueError(f'{pillar}: 중복된 천간 극 출처입니다.')
            observed_to[pair] = index
        for match in restrain.get('restrain_me', []):
            other = match['with_index']
            if (not 0 <= other < 4 or other == index
                    or match['my'] != stems[index]
                    or match['with'] != stems[other]):
                raise ValueError(f'{pillar}: 천간 피극 상대의 위치·글자가 다릅니다.')
            key = (index, other)
            if key in observed_me:
                raise ValueError(f'{pillar}: 중복된 천간 피극 출처입니다.')
            observed_me.add(key)
    if observed_to != expected or observed_me != {
            (right if source == left else left, source)
            for (left, right), source in expected.items()}:
        raise ValueError('천간 극 규칙과 글자별 분석의 양방향 결과가 다릅니다.')
    rows = []
    for (left_index, right_index), source_index in expected.items():
        left, right = PILLARS[left_index], PILLARS[right_index]
        target_index = right_index if source_index == left_index else left_index
        source = PILLARS[source_index]
        rows.append(_row(
            f'stem:control:{left}:{right}', 'control',
            [f'{left}.stem', f'{right}.stem'], 'detected',
            [_ref('analysis_details', location=
                  f'analysis.details.{source}.stem.relations.restrain.restrain_to')],
            direction=_direction(f'{source}.stem', f'{PILLARS[target_index]}.stem'),
        ))
    return rows


def _branch_rows(branches, matrix, dynamics):
    pairs = assemble_branch_pairs_v3(branches, dynamics)
    groups = assemble_branch_groups_v3(branches, dynamics, pairs)
    original_pairs = _branch_matrix_ids(matrix, branches)
    original_groups = {}
    for item in matrix:
        if item['category'] != '지지' or item['relation_scope'] != 'group':
            continue
        kind = GROUP_TYPES[item['type']][0]
        key = (kind, tuple(item['participants']))
        if key in original_groups:
            raise ValueError(f'{kind}: 중복된 원본 지지 그룹입니다.')
        original_groups[key] = item

    rows = []
    matched_pairs = set()
    for pair in pairs:
        left, right = pair['pillars']
        for relation in pair['relations']:
            relation_id = relation['relation_id']
            original = original_pairs.get(relation_id)
            if original is not None:
                matched_pairs.add(relation_id)
                if (relation['activation_status'] != original.get('activation_status')
                        and relation.get('effect_status') != 'structural_only'):
                    raise ValueError(f'{relation_id}: 매트릭스와 v3 성립 상태가 다릅니다.')
            elif relation['type'] not in ('generate', 'control', 'same_branch', 'half_combine'):
                raise ValueError(f'{relation_id}: 원본 매트릭스 관계가 없습니다.')
            refs = [_ref('branch_dynamics_v3', relation_id=relation_id)]
            if original is not None:
                refs.append(_ref('interaction_matrix', relation_id=original['relation_id']))
            direction = relation.get('direction')
            direction_data = (_direction(
                f"{direction['from_pillar']}.branch",
                f"{direction['to_pillar']}.branch",
                'elemental' if relation['type'] in ('generate', 'control')
                else 'rule_fixed') if direction else None)
            rows.append(_row(
                relation_id, relation['type'], [f'{left}.branch', f'{right}.branch'],
                relation['activation_status'], refs,
                reason=relation.get('status_reason'), direction=direction_data,
                element=relation.get('candidate_element'),
                rule_ids=[evidence['rule_id'] for evidence in relation.get('evidence', [])],
            ))
    if matched_pairs != set(original_pairs):
        raise ValueError('v3에서 누락된 원본 지지 쌍 관계가 있습니다.')

    matched_groups = set()
    for group in groups:
        kind = group['type']
        members = sorted({pillar for formation in group['formation_candidates']
                          for pillar in formation['pillars']}, key=PILLARS.index)
        key = (kind, tuple(members))
        original = original_groups.get(key)
        if original is None:
            raise ValueError(f"{group['group_id']}: 원본 지지 그룹이 없습니다.")
        matched_groups.add(key)
        formations = [formation['pillars'] for formation in group['formation_candidates']]
        if (group['formation_status'] != original['activation_status']
                or formations != original['formations']):
            raise ValueError(f"{group['group_id']}: 그룹 위치·성립 상태가 다릅니다.")
        rows.append(_row(
            group['group_id'], kind, [f'{pillar}.branch' for pillar in members],
            group['formation_status'],
            [_ref('branch_dynamics_v3', relation_id=group['group_id']),
             _ref('interaction_matrix', relation_id=original['relation_id'])],
            reason=group['status_reasons'][0] if group['status_reasons'] else None,
            element=group.get('candidate_element'),
            formations=[[f'{pillar}.branch' for pillar in formation]
                        for formation in formations],
            rule_ids=group['evidence_rule_ids'],
        ))
    if matched_groups != set(original_groups):
        raise ValueError('v3에서 누락된 원본 지지 그룹이 있습니다.')
    return rows


def _same_pillar_rows(stems, branches, analysis, dynamics):
    directions = {
        'stem_generates_branch': ('stem', 'branch'),
        'branch_generates_stem': ('branch', 'stem'),
        'stem_controls_branch': ('stem', 'branch'),
        'branch_controls_stem': ('branch', 'stem'),
    }
    rows = []
    for index, pillar in enumerate(PILLARS):
        evidence = dynamics['branch_strengths'][pillar]['stem_branch_relation']
        actual = _stem_branch_relation(
            STEM_ELEMENT_MAP[stems[index]], BRANCH_ELEMENT_MAP[branches[index]])
        if evidence['stem'] != stems[index] or evidence['relation'] != actual:
            raise ValueError(f'{pillar}: 동주 오행 근거와 원국이 다릅니다.')
        direction = directions.get(actual)
        rows.append(_row(
            f'same_pillar:element:{pillar}', 'element',
            [f'{pillar}.stem', f'{pillar}.branch'], 'detected',
            [_ref('branch_dynamics', location=
                  f'branch_dynamics.branch_strengths.{pillar}.stem_branch_relation')],
            direction=_direction(f'{pillar}.{direction[0]}',
                                 f'{pillar}.{direction[1]}') if direction else None,
        ))
        jahab = analysis['pillars'][pillar]['jahab']
        rule = JAHAB_MAP.get((stems[index], branches[index]))
        branch_relations = analysis['pillars'][pillar]['branch']['relations']
        expected = check_jahab(stems[index], branches[index], index,
                               branch_relations['chungs'], branch_relations['punishments'])
        if jahab != expected or (rule is None) != (jahab is None):
            raise ValueError(f'{pillar}: 자합 판정과 글자별 분석이 다릅니다.')
        if jahab is None:
            continue
        reason = jahab.get('inactive_reason')
        status = ('active' if jahab['active'] else
                  'suppressed' if reason == 'blocked_by_chen_chung' else
                  'conditional' if reason == 'required_punishment_missing' else None)
        if status is None:
            raise ValueError(f'{pillar}: 모르는 자합 판정 상태입니다.')
        rows.append(_row(
            f'same_pillar:self_combine:{pillar}', 'self_combine',
            [f'{pillar}.stem', f'{pillar}.branch'], status,
            [_ref('analysis_details', location=f'analysis.details.{pillar}.jahab')],
            reason=reason, element=jahab['combined_element'],
        ))
    return rows


def _transmission_rows(stems, branches, analysis):
    """같은 지장간 글자가 여러 천간에 보이면 위치마다 관계를 만든다."""
    rows = []
    for branch_index, branch_pillar in enumerate(PILLARS):
        branch = branches[branch_index]
        observed = analysis['pillars'][branch_pillar]['branch']
        expected_pairs = [
            (stem_index, hidden)
            for hidden in (item['char'] for item in JIJANGGAN_DETAILED[branch])
            for stem_index, visible in enumerate(stems) if visible == hidden
        ]
        actual_pairs = []
        for item in observed['transmitted']:
            stem_index = item['stem_idx']
            if (not 0 <= stem_index < 4 or item['from_idx'] != branch_index
                    or item['from'] != branch or item['stem'] != stems[stem_index]):
                raise ValueError(f'{branch_pillar}: 투출 위치·글자가 다릅니다.')
            actual_pairs.append((stem_index, item['stem']))
        if actual_pairs != expected_pairs or [item['stem'] for item in observed['hidden']] != [
                item['char'] for item in JIJANGGAN_DETAILED[branch]
                if item['char'] not in stems]:
            raise ValueError(f'{branch_pillar}: 지장간 표와 투출 결과가 다릅니다.')
        for stem_index, hidden in expected_pairs:
            stem_pillar = PILLARS[stem_index]
            source = f'{branch_pillar}.branch'
            target = f'{stem_pillar}.stem'
            rows.append(_row(
                f'cross_layer:transmission:{branch_pillar}:{stem_pillar}',
                'transmission',
                sorted((source, target), key=CHARACTER_IDS.index),
                'detected',
                [_ref('analysis_details', location=
                      f'analysis.details.{branch_pillar}.branch.transmitted')],
                direction=_direction(source, target, 'hidden_stem_match'),
                hidden_stem=hidden,
            ))
    return rows


def _stem_states(stems, branches, matrix, analysis, xu_shi):
    roots = [
        {'점수': analysis['pillars'][pillar]['stem']['score'],
         '통근정보': analysis['pillars'][pillar]['stem']['root_info']}
        for pillar in PILLARS
    ]
    calculated = analyze_xu_shi_dynamics(stems, branches, stems[2], roots, matrix)
    if xu_shi is not None and xu_shi['pillars'] != calculated['pillars']:
        raise ValueError('허실 원본과 글자별 통근 근거가 다릅니다.')
    source = xu_shi or calculated
    result = {}
    for pillar in PILLARS:
        item = source['pillars'][pillar]
        original = analysis['pillars'][pillar]['stem']
        if item['char'] != original['char'] or item['score'] != original['score']:
            raise ValueError(f'{pillar}: 천간 허실과 원국의 통근 근거가 다릅니다.')
        result[f'{pillar}.stem'] = {
            'original_status': item['original_status'],
            'current_status': item['current_status'],
            'root_score': item['score'],
            'remaining_score': item['effective_score'],
            'root_branch_ids': [f"{root['pillar']}.branch"
                                for root in item['root_evidence']],
            'affected_root_branch_ids': [f"{root['pillar']}.branch"
                                         for root in item['root_evidence']
                                         if root['is_affected']],
            'source_rule_version': source['rule_version'],
            'root_scope': 'all_four_branches_weighted',
            'validation_status': 'provisional',
        }
    return result


def assemble_character_relation_index(stems, branches, interactions, analysis,
                                      dynamics, xu_shi=None):
    """기존 세 계산 결과를 검증하고 관계 본문·글자별 참조를 재생성한다."""
    if len(stems) != 4 or len(branches) != 4:
        raise ValueError('천간·지지는 각각 네 글자가 필요합니다.')
    if set(analysis['pillars']) != set(PILLARS):
        raise ValueError('글자별 분석에 네 기둥이 모두 필요합니다.')
    for index, pillar in enumerate(PILLARS):
        original = analysis['pillars'][pillar]
        if (original['stem']['char'] != stems[index]
                or original['branch']['char'] != branches[index]):
            raise ValueError(f'{pillar}: 글자별 분석과 원국이 다릅니다.')
    matrix = interactions['matrix']
    _check_branch_analysis(matrix, analysis, branches)
    rows = (
        _branch_rows(branches, matrix, dynamics)
        + _stem_matrix_rows(matrix, analysis, stems)
        + _stem_control_rows(stems, analysis)
        + _same_pillar_rows(stems, branches, analysis, dynamics)
        + _transmission_rows(stems, branches, analysis)
    )
    rows.sort(key=lambda item: item['relation_id'])
    stem_states = _stem_states(stems, branches, matrix, analysis, xu_shi)
    characters = {
        char_id: {'char': (stems if char_id.endswith('.stem') else branches)[
            PILLARS.index(char_id.split('.')[0])], 'relation_ids': [],
                  'stem_state': stem_states.get(char_id)}
        for char_id in CHARACTER_IDS
    }
    for row in rows:
        for participant in row['participants']:
            characters[participant]['relation_ids'].append(row['relation_id'])
    return CharacterRelationIndex.model_validate({
        'schema_version': '1.3-draft', 'characters': characters, 'relations': rows,
        'coverage': {
            'rule_scope': 'registered_rules_partial',
            'transmission_basis': 'jijanggan_detailed_exact_match',
            'detected_only_relation_ids': [row['relation_id'] for row in rows
                                           if row['activation_status'] == 'detected'],
            'not_evaluated_mechanisms': list(NOT_EVALUATED_MECHANISMS),
            'power_effects_included': False,
        },
    }).model_dump()


def assemble_character_relation_index_from_response(response):
    """현행 원국 응답에 이미 있는 탐지 결과를 독립 조회 결과로 옮긴다."""
    pillars = response['four_pillars']
    stems = [pillars[pillar]['gan']['ch'] for pillar in PILLARS]
    branches = [pillars[pillar]['ji']['ch'] for pillar in PILLARS]
    advanced = response['advanced_analysis']
    return assemble_character_relation_index(
        stems, branches, advanced['interactions'],
        {'pillars': response['analysis']['details']},
        advanced['branch_dynamics'],
        advanced['xu_shi_dynamics'],
    )
