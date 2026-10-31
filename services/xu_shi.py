from typing import List, Dict, Any
from services.calculator import get_ten_star_stem

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']
REAL_THRESHOLD = 0.5
RULE_VERSION = '1.0.0'  # 기존 판정 규칙을 최초로 명시한 버전
AFFECTING_TYPES = ('충(沖)', '천(穿)', '형(刑)')


def analyze_xu_shi_dynamics(
    stems: List[str],
    branches: List[str],
    day_stem: str,
    tonggeun_results: List[Dict[str, Any]],
    interaction_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """원국의 관계 반영 전후 허실과 판정 근거를 반환한다.

    v1은 기존 규칙을 유지한다. 충·형·천에 연결된 뿌리의 기여도를
    전부 제외하며, 원래 실인 천간만 잔여 점수에 따라 변허로 전이한다.
    대운·세운 또는 관계별 손상률을 계산하지 않는다.
    """
    pillars_xu_shi: Dict[str, Any] = {}
    relations_by_pillar: Dict[str, list] = {key: [] for key in PILLAR_KEYS}
    for item in interaction_matrix:
        if item.get('category') != '지지' or item.get('type') not in AFFECTING_TYPES:
            continue
        from_p = item.get('from_pillar')
        to_p = item.get('to_pillar')
        if from_p not in PILLAR_KEYS or to_p not in PILLAR_KEYS:
            continue
        relation = {
            'relation_id': item.get('relation_id'),
            'type': item['type'],
            'name': item.get('name', ''),
            'from_pillar': from_p,
            'to_pillar': to_p,
            'weight': item.get('weight'),
            'is_adjacent': item.get('is_adjacent'),
        }
        for key in dict.fromkeys((from_p, to_p)):
            if relation not in relations_by_pillar[key]:
                relations_by_pillar[key].append(relation)

    for i, p_key in enumerate(PILLAR_KEYS):
        pos_name = POSITION_NAMES[i]
        stem_char = stems[i]
        tg = tonggeun_results[i]
        base_score = tg.get('점수', 0)
        ten_star = '일간(본인)' if i == 2 else get_ten_star_stem(day_stem, stem_char)
        if base_score >= REAL_THRESHOLD:
            original_status = '실(實)'
        elif base_score == 0:
            original_status = '허투(虛透)'
        else:
            original_status = '허(虛)'

        root_evidence = []
        intact_score = 0.0
        for root in tg.get('통근정보', []):
            position = root.get('position')
            # 통근 계산기가 생성하는 네 위치만 기존 판정과 동일하게 사용한다.
            if position not in POSITION_NAMES:
                continue
            index = POSITION_NAMES.index(position)
            root_pillar = PILLAR_KEYS[index]
            relations = relations_by_pillar[root_pillar]
            score = root.get('score', 0.0)
            effective = 0.0 if relations else score
            intact_score += effective
            root_evidence.append({
                'pillar': root_pillar,
                'position': position,
                'branch_char': root.get('branch_char', branches[index]),
                'score': score,
                'is_affected': bool(relations),
                'effective_score': effective,
                'interactions': relations,
            })

        affected_roots = [root for root in root_evidence if root['is_affected']]
        current_status = original_status
        if original_status == '실(實)' and affected_roots and intact_score < REAL_THRESHOLD:
            current_status = '변허(變虛)'
        is_transformed = current_status != original_status
        root_structure = _describe_pillar_roots(root_evidence, intact_score)

        # 원점수/개별 근 점수는 상위 통근 계산기에서 각각 반올림된다.
        # 판정 호환성을 위해 잔여 합산값에 추가 반올림을 적용하지 않는다.
        transition_reasons = [
            f'관계 반영 전 통근 점수 {base_score}로 {original_status} 분류 '
            f'(실 기준 {REAL_THRESHOLD} 이상, 허투 기준 0).'
        ]
        for root in affected_roots:
            types = ', '.join(dict.fromkeys(rel['type'] for rel in root['interactions']))
            transition_reasons.append(
                f"{root['position']}지({root['branch_char']})의 {types} 관계로 "
                f"해당 뿌리 점수 {root['score']}를 잔여 점수에서 제외합니다(기존 규칙)."
            )
        if not affected_roots:
            transition_reasons.append('통근처에 반영할 충·형·천 관계가 없습니다.')
        if original_status == '실(實)' and affected_roots:
            comparison = '미만' if is_transformed else '이상'
            transition_reasons.append(
                f'잔여 통근 점수 {intact_score}가 기준 {REAL_THRESHOLD} {comparison}이므로 '
                f'{current_status}으로 판정합니다.'
            )
        elif original_status == '허(虛)' and affected_roots:
            transition_reasons.append(
                f'잔여 통근 점수는 {intact_score}입니다. 원래 허인 천간은 '
                '잔여 점수가 0이어도 허를 유지합니다(실에서만 변허로 전이하는 기존 규칙).'
            )
        else:
            transition_reasons.append(f'기존 규칙에 따라 {original_status}을 유지합니다.')

        pillars_xu_shi[p_key] = {
            'position': f'{pos_name}간',
            'char': stem_char,
            'ten_star': ten_star,
            'score': base_score,
            'effective_score': intact_score,
            'root_evidence': root_evidence,
            'transition_reasons': transition_reasons,
            'original_status': original_status,
            'current_status': current_status,
            'is_transformed': is_transformed,
            'transition_code': 'real_to_empty' if is_transformed else 'maintained',
            'root_structure': root_structure,
            'reason': ' '.join(transition_reasons),
            'meaning': _generate_xu_shi_meaning(ten_star, current_status),
        }

    counts = {
        status: sum(p['current_status'] == status for p in pillars_xu_shi.values())
        for status in ('실(實)', '변허(變虛)', '허투(虛透)', '허(虛)')
    }
    counts_summary = ', '.join(f'{status} {count}개' for status, count in counts.items() if count)
    root_groups, impact_groups = _collect_root_groups(pillars_xu_shi)
    shared_roots = [group for group in root_groups if len(group['dependents']) > 1]
    summary_parts = [f'원국 천간 4자의 관계 반영 후 분포는 {counts_summary}입니다.']
    # 관계는 뿌리별로 한 번만 설명하고, 천간별로는 잔존 기반과 결과를 설명한다.
    for group in root_groups:
        names = ', '.join(pillars_xu_shi[d['stem_pillar']]['position'] for d in group['dependents'])
        root_name = f"{POSITION_NAMES[PILLAR_KEYS.index(group['root_pillar'])]}지({group['branch_char']})"
        if len(group['dependents']) > 1:
            summary_parts.append(f'{names}은 {root_name}의 뿌리를 공유합니다.')
        if group['is_affected']:
            types = ', '.join(dict.fromkeys(rel['type'] for rel in group['interactions']))
            summary_parts.append(f'{root_name}의 {types} 관계로 {names}에 대한 해당 뿌리의 기여도를 제외합니다.')
    for pillar in pillars_xu_shi.values():
        affected = [root for root in pillar['root_evidence'] if root['is_affected']]
        if not affected:
            continue
        remaining = [root for root in pillar['root_evidence'] if root['effective_score'] > 0]
        remaining_names = ', '.join(f"{root['position']}지({root['branch_char']})" for root in remaining)
        support = f"잔존 기반 {remaining_names}, 점수 {pillar['effective_score']}" if remaining else '잔존 기반 없음, 점수 0'
        action = '로 분류됩니다' if pillar['is_transformed'] else '을 유지합니다'
        summary_parts.append(
            f"{pillar['position']}({pillar['char']})은 {support}으로 {pillar['current_status']}{action}."
        )
    if not impact_groups:
        summary_parts.append('통근처에 반영할 충·형·천 관계가 없어 원래 분류를 유지합니다.')

    return {
        'analysis_scope': 'natal',
        'rule_version': RULE_VERSION,
        'pillars': pillars_xu_shi,
        'shared_roots': shared_roots,
        'impact_groups': impact_groups,
        'real_count': counts['실(實)'],
        'transformed_empty_count': counts['변허(變虛)'],
        'hollow_penetrate_count': counts['허투(虛透)'],
        'weak_count': counts['허(虛)'],
        'overall_status': ' '.join(summary_parts),
    }


def _describe_pillar_roots(roots: List[Dict[str, Any]], effective_score: float) -> Dict[str, Any]:
    """점수 판정을 바꾸지 않고 주요 뿌리와 잔존 기반을 기술한다."""
    largest = max((root['score'] for root in roots), default=0)
    return {
        'primary_root_pillars': [root['pillar'] for root in roots if root['score'] == largest and largest > 0],
        'remaining_root_pillars': [root['pillar'] for root in roots if root['effective_score'] > 0],
        'excluded_root_pillars': [root['pillar'] for root in roots if root['is_affected']],
        'remaining_support': (
            'meets_threshold' if effective_score >= REAL_THRESHOLD
            else 'below_threshold' if effective_score > 0 else 'none'
        ),
    }


def _collect_root_groups(pillars: Dict[str, Any]):
    """지지 위치를 기준으로 공유 기반과 관계별 영향 범위를 수집한다.

    같은 글자의 지지도 위치가 다르면 다른 뿌리다. 영향 범위는 기존 근거의
    집계이며 각 관계가 단독으로 변허를 일으켰다는 인과 판정은 아니다.
    """
    roots_by_pillar = {}
    impacts = {}
    for stem_pillar, pillar in pillars.items():
        for root in pillar['root_evidence']:
            group = roots_by_pillar.setdefault(root['pillar'], {
                'root_pillar': root['pillar'],
                'branch_char': root['branch_char'],
                'is_affected': root['is_affected'],
                'interactions': root['interactions'],
                'dependents': [],
            })
            group['dependents'].append({
                'stem_pillar': stem_pillar,
                'score': root['score'],
                'effective_score': root['effective_score'],
                'current_status': pillar['current_status'],
            })
            for relation in root['interactions']:
                # 매트릭스 항목의 양쪽 뿌리에 연결되어도 동일 관계는 한 번 집계.
                key = (relation['from_pillar'], relation['to_pillar'], relation['type'], relation['name'])
                impact = impacts.setdefault(key, {
                    'interaction': relation,
                    'affected_root_pillars': set(),
                    'affected_stem_pillars': set(),
                })
                impact['affected_root_pillars'].add(root['pillar'])
                impact['affected_stem_pillars'].add(stem_pillar)
    impact_groups = []
    for key in sorted(impacts):
        impact = impacts[key]
        impact_groups.append({
            'interaction': impact['interaction'],
            'affected_root_pillars': [p for p in PILLAR_KEYS if p in impact['affected_root_pillars']],
            'affected_stem_pillars': [p for p in PILLAR_KEYS if p in impact['affected_stem_pillars']],
        })
    return [roots_by_pillar[p] for p in PILLAR_KEYS if p in roots_by_pillar], impact_groups


def _generate_xu_shi_meaning(ten_star: str, current: str) -> str:
    """계산된 사실과 구분된 전통적 상징 해석. 능력·성과를 예측하지 않는다."""
    domains = {
        '일간(본인)': '자신과 주체성',
        '비견': '동료와 협력 관계', '겁재': '동료와 협력 관계',
        '편재': '재물과 자원', '정재': '재물과 자원',
        '편관': '규율과 역할', '정관': '규율과 역할',
        '식신': '표현과 생산 활동', '상관': '표현과 생산 활동',
        '편인': '학습과 문서', '정인': '학습과 문서',
    }
    # 십성 계산기는 한자 병기 문자열도 반환할 수 있다.
    domain = next((value for key, value in domains.items() if key in ten_star), '해당 십성의 상징 영역')
    interpretations = {
        '실(實)': '통근 기반이 판정 기준을 충족하는 구조로 살펴볼 수 있습니다',
        '변허(變虛)': '관계 반영 전에는 실이었으나 반영 후 통근 기반이 기준에 미달하는 구조로 살펴볼 수 있습니다',
        '허투(虛透)': '계산상 통근 없이 천간에 드러난 상징으로 살펴볼 수 있습니다',
        '허(虛)': '관계 반영 전부터 통근 기반이 기준에 미달하는 구조로 살펴볼 수 있습니다',
    }
    return f'전통적 해석 참고: {domain}의 영역에서 {interpretations[current]}. 실제 능력·성과나 직업 적합성을 뜻하지 않습니다.'
