from typing import List, Dict, Any
from services.calculator import get_ten_star_stem, get_ten_star_branch

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']
COMBINATION_TYPES = {'육합(六合)', '반합(半合)', '천간합(天干合)'}
CONFLICT_TYPES = {'충(沖)', '해/천(穿/害)', '천간충(天干沖)'}


def analyze_bin_zhu_dynamics(
    stems: List[str], branches: List[str], day_stem: str,
    interaction_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """빈(년·월)과 주(일·시)의 관계를 집계한다.

    합 2점, 충·해/천 1.5점의 기존 쌍별 가산을 유지한다. 이는 관계 유형의
    비교이며 자원 취득이나 제어 방향 판정이 아니다. 다자 관계는 구조만 기술한다.
    """
    stem_ten_gods = ['일간(본인)' if i == 2 else get_ten_star_stem(day_stem, stems[i]) for i in range(4)]
    branch_ten_gods = [get_ten_star_branch(day_stem, branch) for branch in branches]
    elements = {
        key: {'stem': f'{stems[i]}({stem_ten_gods[i]})',
              'branch': f'{branches[i]}({branch_ten_gods[i]})'}
        for i, key in enumerate(PILLAR_KEYS)
    }
    guest_host_links = []
    excluded_interactions = []
    group_connections = []
    combination_score = 0.0
    conflict_score = 0.0
    for item in interaction_matrix:
        from_pillar, to_pillar = item.get('from_pillar'), item.get('to_pillar')
        is_group = (item.get('relation_scope') == 'group'
                    or 'all' in (from_pillar, to_pillar)
                    or item.get('type') in ('삼합(三合)', '방합(方合)'))
        if is_group or from_pillar not in PILLAR_KEYS or to_pillar not in PILLAR_KEYS:
            participants = [p for p in PILLAR_KEYS if p in item.get('participants', [])]
            excluded = {
                'relation_id': item.get('relation_id'),
                'category': item.get('category', ''), 'type': item.get('type', ''),
                'name': item.get('name', ''), 'from_pillar': from_pillar, 'to_pillar': to_pillar,
                'participants': participants,
                'reason_code': 'group_relation_unsupported' if is_group else 'invalid_endpoint',
            }
            if excluded not in excluded_interactions:
                excluded_interactions.append(excluded)
            # all만 있는 입력에서 참여 기둥을 추측하지 않는다.
            if is_group and len(participants) >= 3:
                group = {
                    'relation_id': item.get('relation_id'), 'type': item['type'],
                    'participants': participants,
                    'guest_participants': [p for p in participants if p in PILLAR_KEYS[:2]],
                    'host_participants': [p for p in participants if p in PILLAR_KEYS[2:]],
                    'included_in_score': False,
                    'description': '빈과 주가 함께 참여하는 다자 관계입니다. 쌍별 점수와 취용 판정에는 반영하지 않습니다.',
                }
                if group not in group_connections:
                    group_connections.append(group)
            continue

        from_idx, to_idx = PILLAR_KEYS.index(from_pillar), PILLAR_KEYS.index(to_pillar)
        if (from_idx < 2) == (to_idx < 2):
            continue
        g_idx, h_idx = (from_idx, to_idx) if from_idx < 2 else (to_idx, from_idx)
        rel_type = item.get('type')
        if rel_type in COMBINATION_TYPES:
            combination_score += 2.0
            link_type = '합(관계)'
        elif rel_type in CONFLICT_TYPES:
            conflict_score += 1.5
            link_type = '충/해(관계)'
        else:
            continue  # 형·파·극 등은 현재 쌍별 점수 규칙에 포함하지 않는다.
        ten_gods = branch_ten_gods if item['category'] == '지지' else stem_ten_gods
        g_pos, h_pos = POSITION_NAMES[g_idx], POSITION_NAMES[h_idx]
        desc = f'빈({g_pos} {ten_gods[g_idx]})과 주({h_pos} {ten_gods[h_idx]}) 사이에 {rel_type} 관계가 있습니다.'
        guest_host_links.append({
            'relation_id': item.get('relation_id'), 'type': link_type, 'detail': desc,
            'target_guest': f'{g_pos}({ten_gods[g_idx]})', 'source_host': f'{h_pos}({ten_gods[h_idx]})',
        })

    if not guest_host_links:
        direction = '평가 가능한 빈-주 통로 없음'
        summary = '현재 쌍별 계산에 반영된 빈-주 통로가 없어 관계 유형의 우세를 판정하지 않습니다.'
    elif combination_score > conflict_score:
        direction = '합 관계 우세'
        summary = '현재 쌍별 규칙에서 빈-주 간 합 관계 점수가 충·해/천 관계 점수보다 높습니다.'
    elif conflict_score > combination_score:
        direction = '충·해 관계 우세'
        summary = '현재 쌍별 규칙에서 빈-주 간 충·해/천 관계 점수가 합 관계 점수보다 높습니다.'
    else:
        direction = '관계 점수 동률'
        summary = '현재 쌍별 규칙에서 두 관계 점수가 같습니다. 생활이나 관계의 균형을 뜻하지 않습니다.'
    career_advice = '전통적 해석 참고: 빈은 사회적 환경, 주는 개인 영역의 상징입니다. 관계 집계만으로 직업 적합성·재물 취득·성과를 판단하지 않습니다.'
    prompts = [f'【빈주 관계】 {direction}: {summary}', f'【빈주 해석 참고】 {career_advice}']
    if excluded_interactions:
        prompts.append(
            f'【빈주 계산 범위】 쌍별 관계만 점수에 반영했습니다. 다자 관계 또는 위치를 확인할 수 없는 '
            f'관계 {len(excluded_interactions)}건은 계산에서 제외했으므로 빈주 점수의 근거로 사용하지 마세요.'
        )
    for group in group_connections:
        positions = ', '.join(POSITION_NAMES[PILLAR_KEYS.index(p)] for p in group['participants'])
        prompts.append(f"【빈주 다자 관계】 {group['type']} 참여 위치: {positions}. {group['description']}")
    for link in guest_host_links[:2]:
        prompts.append(f"【주-빈 통로】 {link['detail']}")
    return {
        'rule_version': '2.0.0',
        'interaction_scope': 'pairwise',
        'pairwise_scores': {'combination': combination_score, 'conflict': conflict_score},
        'excluded_interactions': excluded_interactions,
        'group_connections': group_connections,
        'guest_structure': {'scope': '년주(사회적 환경) + 월주(사회적 환경)',
                            'elements': {p: elements[p] for p in PILLAR_KEYS[:2]}},
        'host_structure': {'scope': '일주(개인 영역) + 시주(개인 영역)',
                           'elements': {p: elements[p] for p in PILLAR_KEYS[2:]}},
        'control_flow': {'direction': direction, 'summary_meaning': summary, 'career_advice': career_advice},
        'guest_host_links': guest_host_links,
        'ai_prompt_bullets': prompts,
    }
