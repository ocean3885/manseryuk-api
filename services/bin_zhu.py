from typing import List, Dict, Any
from services.calculator import get_ten_star_stem, get_ten_star_branch

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']
COMBINATION_TYPES = {'육합(六合)', '반합(半合)', '천간합(天干合)'}
CONFLICT_TYPES = {'충(沖)', '천(穿)', '천간충(天干沖)', '형(刑)'}
UNSCORED_PAIRWISE_TYPES = {'파(破)', '공합(拱合)', '암합(暗合)'}

RESOURCES = {'정인', '편인'}
WEALTH_AND_OFFICER = {'정재', '편재', '정관', '편관'}
OUTPUTS = {'식신', '상관'}
SIBLINGS = {'비견', '겁재', '일간(본인)'}


def _classify_mechanism_and_flow(
    rel_type: str, g_star: str, h_star: str, is_day_stem: bool
) -> tuple[str, str]:
    """십성과 관계 유형에 따른 취용 메커니즘과 역학 방향(flow)을 판정한다."""
    if '합' in rel_type:
        if is_day_stem:
            if g_star in ('정재', '편재'):
                return ('일간합재(合財)', 'host_takes_guest')
            elif g_star in ('정관', '편관'):
                return ('일간합관(合官)', 'host_takes_guest')
            else:
                return ('일간유화(合化)', 'mutual_cooperation')
        if g_star in WEALTH_AND_OFFICER and h_star in (RESOURCES | OUTPUTS | SIBLINGS):
            return ('합취(合取)', 'host_takes_guest')
        elif g_star in ('비견', '겁재') and h_star in ('정재', '편재'):
            return ('합거/탈재(合去)', 'guest_pressures_host')
        else:
            return ('상호유대(有情)', 'mutual_cooperation')

    if any(k in rel_type for k in ('충', '천', '해', '형')):
        if g_star in ('편관', '칠살') and h_star in (SIBLINGS | RESOURCES):
            return ('환경압박(沖破)', 'guest_pressures_host')
        elif g_star in WEALTH_AND_OFFICER and h_star in OUTPUTS:
            return ('제용(制用)', 'host_takes_guest')
        elif g_star in ('정재', '편재') and h_star in SIBLINGS:
            return ('제용(制用)', 'host_takes_guest')
        elif g_star in ('비견', '겁재') and h_star in ('정재', '편재'):
            return ('군겁쟁재(爭財)', 'guest_pressures_host')
        elif g_star in WEALTH_AND_OFFICER and h_star in RESOURCES:
            return ('재관마찰', 'guest_pressures_host')
        else:
            return ('대립조율', 'neutral')

    return ('상호작용', 'neutral')


def analyze_bin_zhu_dynamics(
    stems: List[str], branches: List[str], day_stem: str,
    interaction_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """빈(년·월)과 주(일·시)의 체용(體用) 및 취용(取用) 관계를 분석한다.

    거리 가중치 및 십성 기반 취용 메커니즘(합취, 제용, 환경압박 등)을 도출하고,
    빈과 주의 제어 방향성(Vector: 주➔빈 vs 빈➔주 vs 상호연대)을 판정한다.
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
    unweighted_combination_score = 0.0
    unweighted_conflict_score = 0.0

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
            if is_group and len(participants) >= 3 and item.get('type') != '삼형(三刑)':
                g_participants = [p for p in participants if p in PILLAR_KEYS[:2]]
                h_participants = [p for p in participants if p in PILLAR_KEYS[2:]]
                g_cnt = len(g_participants)
                h_cnt = len(h_participants)
                p_cnt = len(participants)
                base = (0.0 if item.get('activation_status') in ('conditional', 'suppressed') else
                        3.5 if '방합' in item.get('type', '') else 3.0)
                cohesion = round(base * (g_cnt * h_cnt) / p_cnt, 2) if p_cnt > 0 else 0.0
                group = {
                    'relation_id': item.get('relation_id'), 'type': item['type'],
                    'participants': participants,
                    'guest_participants': g_participants,
                    'host_participants': h_participants,
                    'included_in_score': False,
                    'cohesion_score': cohesion,
                    'activation_status': item.get('activation_status'),
                    'description': (f"빈과 주가 함께 참여하는 다자 관계({item['type']})입니다. "
                                    f"빈 {g_cnt}위치, 주 {h_cnt}위치가 참여하며 결합도 {cohesion}점입니다."),
                }
                if group not in group_connections:
                    group_connections.append(group)
            continue

        from_idx, to_idx = PILLAR_KEYS.index(from_pillar), PILLAR_KEYS.index(to_pillar)
        if (from_idx < 2) == (to_idx < 2):
            continue
        g_idx, h_idx = (from_idx, to_idx) if from_idx < 2 else (to_idx, from_idx)
        dist = abs(to_idx - from_idx)
        default_weight = 1.0 if dist == 1 else (0.7 if dist == 2 else 0.5)
        weight = item.get('weight', default_weight)
        rel_type = item.get('type')

        if item.get('activation_status') == 'candidate_only':
            excluded = {
                'relation_id': item.get('relation_id'),
                'category': item.get('category', ''), 'type': rel_type,
                'name': item.get('name', ''),
                'from_pillar': from_pillar, 'to_pillar': to_pillar,
                'participants': [from_pillar, to_pillar],
                'reason_code': 'candidate_only_relation',
            }
            if excluded not in excluded_interactions:
                excluded_interactions.append(excluded)
            continue

        if rel_type in COMBINATION_TYPES:
            unweighted_combination_score += 2.0
            if 'score' in item:
                score = float(item['score'])
            elif rel_type == '천간합(天干合)':
                score = round(1.8 * weight, 2)
            elif rel_type == '육합(六合)':
                score = round(1.5 * weight, 2)
            elif rel_type == '반합(半合)':
                score = round(1.2 * weight, 2)
            else:
                score = round(2.0 * weight, 2)
            combination_score += score
            link_type = '합(관계)'
        elif rel_type in CONFLICT_TYPES:
            unweighted_conflict_score += 1.5
            if 'score' in item:
                score = float(item['score'])
            elif rel_type == '충(沖)':
                score = round(2.0 * weight, 2)
            elif rel_type in ('천간충(天干沖)', '천(穿)', '형(刑)'):
                score = round(1.5 * weight, 2)
            else:
                score = round(1.5 * weight, 2)
            conflict_score += score
            link_type = '형(관계)' if rel_type == '형(刑)' else '충/천(관계)'
        elif rel_type in UNSCORED_PAIRWISE_TYPES:
            excluded = {
                'relation_id': item.get('relation_id'),
                'category': item.get('category', ''), 'type': rel_type,
                'name': item.get('name', ''), 'from_pillar': from_pillar, 'to_pillar': to_pillar,
                'participants': [from_pillar, to_pillar],
                'reason_code': ('candidate_only_relation' if rel_type in
                                {'공합(拱合)', '암합(暗合)'} else 'unsupported_relation_type'),
            }
            if excluded not in excluded_interactions:
                excluded_interactions.append(excluded)
            continue
        else:
            continue  # 극 등 미지원 관계

        ten_gods = branch_ten_gods if item['category'] == '지지' else stem_ten_gods
        g_pos, h_pos = POSITION_NAMES[g_idx], POSITION_NAMES[h_idx]
        g_star = ten_gods[g_idx]
        h_star = ten_gods[h_idx]
        is_day_stem = (item['category'] == '천간' and h_idx == 2)
        mechanism, flow_dir = _classify_mechanism_and_flow(rel_type, g_star, h_star, is_day_stem)

        desc = f'빈({g_pos} {g_star})과 주({h_pos} {h_star}) 사이에 {rel_type} 관계가 있습니다.'
        guest_host_links.append({
            'relation_id': item.get('relation_id'),
            'type': link_type,
            'detail': desc,
            'target_guest': f'{g_pos}({g_star})',
            'source_host': f'{h_pos}({h_star})',
            'mechanism': mechanism,
            'flow_direction': flow_dir,
            'weight': weight,
        })

    has_bridging_group = any(g['guest_participants'] and g['host_participants']
                             and g['cohesion_score'] > 0 for g in group_connections)
    total_group_cohesion = round(sum(g.get('cohesion_score', 0.0) for g in group_connections), 2)
    comb_score = round(combination_score, 2)
    conf_score = round(conflict_score, 2)

    # 1. 상호작용 우열 판정
    if not guest_host_links:
        if has_bridging_group:
            direction = '다자 합 결합(삼합/방합) 형성'
            dominant_interaction = 'group_bridging'
            summary = f'쌍별 통로는 없으나, 빈과 주가 함께 참여하는 다자 합(삼합/방합) 관계({group_connections[0]["type"]}, 결합도: {total_group_cohesion}점)가 형성되어 있습니다.'
        else:
            direction = '평가 가능한 빈-주 통로 없음'
            dominant_interaction = 'none'
            summary = '현재 쌍별 계산에 반영된 빈-주 통로가 없어 관계 유형의 우세를 판정하지 않습니다.'
    elif has_bridging_group:
        if conf_score > comb_score:
            direction = '다자 합 결합 및 대립(충·형·천) 공존'
            dominant_interaction = 'group_bridging_with_conflict'
            summary = f'빈과 주를 잇는 다자 합(결합도: {total_group_cohesion}점)이 형성되어 있으며, 동시에 쌍별 대립 점수({conf_score}점)가 합 점수({comb_score}점)보다 높은 상태로 공존합니다.'
        elif comb_score > conf_score:
            direction = '합 관계 우세 (다자 합 결합 포함)'
            dominant_interaction = 'group_bridging_with_combination'
            summary = f'빈과 주 간에 다자 합(결합도: {total_group_cohesion}점) 및 쌍별 합 점수({comb_score}점)가 대립 점수({conf_score}점)보다 우세합니다.'
        else:
            direction = '다자 합 결합 및 동률 관계'
            dominant_interaction = 'group_bridging_balanced'
            summary = f'빈과 주를 잇는 다자 합(결합도: {total_group_cohesion}점)이 형성되어 있으며, 쌍별 합과 대립 점수가 {comb_score}점으로 동률입니다.'
    elif comb_score > conf_score:
        direction = '합 관계 우세'
        dominant_interaction = 'combination_dominant'
        summary = f'거리 가중치가 반영된 빈-주 간 합 관계 점수({comb_score}점)가 충·형·천 관계 점수({conf_score}점)보다 높습니다.'
    elif conf_score > comb_score:
        direction = '충·형·천 관계 우세'
        dominant_interaction = 'conflict_dominant'
        summary = f'거리 가중치가 반영된 빈-주 간 충·형·천 관계 점수({conf_score}점)가 합 관계 점수({comb_score}점)보다 높습니다.'
    else:
        direction = '관계 점수 동률'
        dominant_interaction = 'balanced'
        summary = f'거리 가중치가 반영된 두 관계 점수가 {comb_score}점으로 같습니다. 생활이나 관계의 균형을 뜻하지 않습니다.'

    # 2. 십성 기반 체용·취용 역학 벡터(Vector) 분석
    take_weight = sum(l.get('weight', 1.0) for l in guest_host_links if l.get('flow_direction') == 'host_takes_guest')
    pressure_weight = sum(l.get('weight', 1.0) for l in guest_host_links if l.get('flow_direction') == 'guest_pressures_host')
    coop_weight = sum(l.get('weight', 1.0) for l in guest_host_links if l.get('flow_direction') == 'mutual_cooperation') + total_group_cohesion * 0.5

    if take_weight > pressure_weight and take_weight >= 0.7:
        vector = '주 ➔ 빈 (자원 취용/주도형)'
        vector_code = 'host_takes_guest'
        acquisition_summary = '개인의 역량과 수단(일·시주)을 바탕으로 외부 사회의 기회와 재관(년·월주)을 내 영역으로 견인·취용하는 동력이 우세합니다.'
    elif pressure_weight > take_weight and pressure_weight >= 0.7:
        vector = '빈 ➔ 주 (환경 조율/적응형)'
        vector_code = 'guest_pressures_host'
        acquisition_summary = '외부 조직 규율이나 환경적 요구(년·월주)가 개인 영역(일·시주)에 강하게 작용하여, 시스템에 유연하게 적응하고 마찰을 조율하는 과정이 핵심입니다.'
    elif coop_weight >= 1.0 or has_bridging_group:
        vector = '주 ⇄ 빈 (상호 연대/협력형)'
        vector_code = 'mutual_cooperation'
        acquisition_summary = '개인과 외부 사회 환경이 다자 합이나 상호 유대로 연결되어, 파트너십과 네트워크를 통해 발전하는 구조입니다.'
    else:
        vector = '주 ∥ 빈 (독립 영역 유지형)'
        vector_code = 'independent_parallel'
        acquisition_summary = '사회적 환경(빈)과 개인 영역(주) 간에 과도한 종속이나 충돌 없이 비교적 독립적인 영역을 유지합니다.'

    career_advice = '전통적 해석 참고: 빈은 사회적 환경, 주는 개인 영역의 상징입니다. 관계 집계만으로 직업 적합성·재물 취득·성과를 판단하지 않습니다.'
    interpretation_notes = '빈은 사회적 환경(국가·직장), 주는 개인 영역(자아·수단)의 상징입니다. 관계 집계는 기둥 간 거리와 결합 구조를 나타내며, 직업 적합성이나 성과를 단정하지 않습니다.'

    guest_stars = [stem_ten_gods[0], branch_ten_gods[0], stem_ten_gods[1], branch_ten_gods[1]]
    host_stars = [branch_ten_gods[2], stem_ten_gods[3], branch_ten_gods[3]]
    guest_forces = list(dict.fromkeys(s for s in guest_stars if s in (WEALTH_AND_OFFICER | OUTPUTS | RESOURCES | SIBLINGS)))
    host_means = list(dict.fromkeys(s for s in host_stars if s in (OUTPUTS | RESOURCES | SIBLINGS | WEALTH_AND_OFFICER)))

    prompts = [
        f'【빈주 관계】 {direction}: {summary}',
        f'【빈주 역학 흐름】 {vector}: {acquisition_summary}',
        f'【빈주 해석 참고】 {interpretation_notes}'
    ]
    if excluded_interactions:
        prompts.append(
            f'【빈주 계산 범위】 쌍별 관계만 점수에 반영했습니다. 다자 관계 또는 위치를 확인할 수 없거나 '
            f'미가산된 관계 {len(excluded_interactions)}건은 계산에서 제외했으므로 빈주 점수의 근거로 사용하지 마세요.'
        )
    for group in group_connections:
        positions = ', '.join(POSITION_NAMES[PILLAR_KEYS.index(p)] for p in group['participants'])
        prompts.append(f"【빈주 다자 관계】 {group['type']} 참여 위치: {positions}. {group['description']}")
    for link in guest_host_links[:2]:
        prompts.append(f"【주-빈 통로】 {link['detail']} (작용: {link.get('mechanism', '관계')})")

    return {
        'rule_version': '3.0.0',
        'interaction_scope': 'pairwise',
        'pairwise_scores': {
            'combination': comb_score,
            'conflict': conf_score,
            'unweighted_combination': round(unweighted_combination_score, 2),
            'unweighted_conflict': round(unweighted_conflict_score, 2),
        },
        'group_cohesion_score': total_group_cohesion,
        'excluded_interactions': excluded_interactions,
        'group_connections': group_connections,
        'guest_structure': {
            'scope': '년주(국가/조상/대외환경) + 월주(직장/사회활동/사회환경)',
            'dominant_forces': guest_forces,
            'elements': {p: elements[p] for p in PILLAR_KEYS[:2]}
        },
        'host_structure': {
            'scope': '일주(자아/배우자/개인영역) + 시주(수단/도구/말년/귀숙처)',
            'dominant_means': host_means,
            'elements': {p: elements[p] for p in PILLAR_KEYS[2:]}
        },
        'control_flow': {
            'direction': direction,
            'dominant_interaction': dominant_interaction,
            'summary_meaning': summary,
            'career_advice': career_advice,
            'interpretation_notes': interpretation_notes,
            'vector': vector,
            'vector_code': vector_code,
            'acquisition_summary': acquisition_summary,
        },
        'guest_host_links': guest_host_links,
        'ai_prompt_bullets': prompts,
    }
