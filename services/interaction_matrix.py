from typing import List, Dict, Any
from services.branch_relations import (
    check_six_haps,
    check_three_hap,
    check_square_hap,
    check_chung,
    check_cheon,
    check_break,
    check_punishment,
    check_three_punishment,
    check_gong_hap,
    check_hidden_stem_hap,
)
from services.stem_relations import (
    check_stem_combination,
    check_stem_conflict,
    check_stem_restrain
)
from services.relation_rules import (
    get_pair_action_rule, HARMONY_SCORE_TYPES, HARMONY_GROUP_COVERS_PAIR,
    PAIR_PRESENCE_ACTIVE_RULE_ID, TRIPLE_PUNISHMENT_PRESENCE_RULE_ID,
    ADJACENT_SELF_PUNISHMENT_RULE_ID,
)

POSITION_NAMES = ['년', '월', '일', '시']
PILLAR_KEYS = ['year', 'month', 'day', 'hour']

def build_interaction_matrix(stems: List[str], branches: List[str], day_stem: str) -> Dict[str, Any]:
    """
    4개 기둥 간의 모든 천간/지지 상호작용(합, 충, 형, 천, 파, 극)을 분석하고
    상세 매트릭스, 요약 목록, 긴장도(Tension) 및 조화도(Harmony) 점수를 산출합니다.
    """
    matrix: List[Dict[str, Any]] = []
    summary_list: List[str] = []
    
    tension_score = 0.0

    # 거리별 가중치 (차이 1: 1.0, 차이 2: 0.7, 차이 3: 0.5)
    def get_dist_weight(dist: int) -> float:
        if dist == 1:
            return 1.0
        elif dist == 2:
            return 0.7
        return 0.5

    # 1. 지지 간 6개 페어 조합 분석 (년-월, 년-일, 년-시, 월-일, 월-시, 일-시)
    for i in range(4):
        for j in range(i + 1, 4):
            dist = j - i
            weight = get_dist_weight(dist)
            pos_from = PILLAR_KEYS[i]
            pos_to = PILLAR_KEYS[j]
            name_from = POSITION_NAMES[i]
            name_to = POSITION_NAMES[j]
            b1 = branches[i]
            b2 = branches[j]

            # (1) 육충 (沖)
            chungs = check_chung(b1, i, branches, day_stem)
            if chungs:
                for c in chungs:
                    if c.get('with_index') == j:
                        score = 2.0 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 육충: 기반 변동 및 마찰"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "충(沖)",
                            "name": f"{b1}{b2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "activation_status": "active",
                            "activation_rule_id": PAIR_PRESENCE_ACTIVE_RULE_ID,
                            "description": desc
                        })

            # (2) 육합 (六合)
            six_hap = next((hap for hap in check_six_haps(b1, i, branches, day_stem)
                            if hap['with_index'] == j), None)
            if six_hap and six_hap.get('with_index') == j:
                status = six_hap['activation_status']
                score = 1.5 * weight if status == 'active' else 0.0
                pair_rule = get_pair_action_rule(b1, b2, '육합(六合)')
                effect = pair_rule[1] if pair_rule else {}
                hidden_candidates = [
                    {'pillar': pos_from if candidate['branch'] == b1 else pos_to,
                     **candidate, 'activation_status': 'candidate_only'}
                    for candidate in effect.get('hidden_stem_candidates', [])
                ]
                desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                        f"육합({six_hap['element']} 후보): " +
                        ('결합 성립' if status == 'active' else '인접 충으로 작용 유보'))
                summary_list.append(desc)
                matrix.append({
                    "category": "지지",
                    "type": "육합(六合)",
                    "name": f"{b1}{b2}합",
                    "from_pillar": pos_from,
                    "to_pillar": pos_to,
                    "is_adjacent": (dist == 1),
                    "weight": weight,
                    "score": score,
                    "candidate_element": six_hap['element'],
                    "transformed_element": None,
                    "activation_status": status,
                    "activation_rule_id": (PAIR_PRESENCE_ACTIVE_RULE_ID
                                           if status == 'active' else None),
                    "status_reasons": six_hap['status_reasons'],
                    "condition_evidence": {
                        'adjacent_clashes': [
                            {'member_pillar': PILLAR_KEYS[clash['member_index']],
                             'clashing_pillar': PILLAR_KEYS[clash['clashing_index']],
                             'location': clash['location']}
                            for clash in six_hap['condition_evidence']['adjacent_clashes']
                        ],
                    },
                    "candidate_hidden_stem_effects": hidden_candidates,
                    "description": desc
                })

            # (3) 천 (穿)
            cheons = check_cheon(b1, i, branches, day_stem)
            if cheons:
                for c in cheons:
                    if c.get('with_index') == j:
                        score = 1.5 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 천(穿): 암묵적 갈등 및 손상"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "천(穿)",
                            "name": f"{b1}{b2}천",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "activation_status": "active",
                            "activation_rule_id": PAIR_PRESENCE_ACTIVE_RULE_ID,
                            "description": desc
                        })

            # (4) 형 (刑)
            punishments = check_punishment(b1, i, branches, day_stem)
            if punishments:
                for p in punishments:
                    if p.get('with_index') == j:
                        is_self_punishment = p.get('type') == '자형'
                        candidate_only = is_self_punishment and dist != 1
                        # 자형의 독립 강도는 미정이다. 기존 긴장 총점에 합산하지 않는다.
                        score = 0.0 if is_self_punishment else 1.5 * weight
                        tension_score += score
                        desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                                f"형({p.get('type', '')}): " +
                                ("격위 자형 후보" if candidate_only else
                                 "인접 자형 성립" if is_self_punishment else "조정 및 압박"))
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "형(刑)",
                            "name": f"{p.get('type', '')}",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "activation_status": ('candidate_only' if candidate_only else 'active'),
                            "activation_rule_id": (None if candidate_only else
                                                   ADJACENT_SELF_PUNISHMENT_RULE_ID
                                                   if is_self_punishment else
                                                   PAIR_PRESENCE_ACTIVE_RULE_ID),
                            "status_reasons": (["nonadjacent_self_punishment_candidate"]
                                               if candidate_only else
                                               ["adjacent_self_punishment"]
                                               if is_self_punishment else []),
                            "description": desc
                        })

            # (5) 파 (破)
            breaks = check_break(b1, i, branches, day_stem)
            if breaks:
                for b in breaks:
                    if b.get('with_index') == j:
                        score = 1.0 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 파: 미세한 균열 및 파괴"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "파(破)",
                            "name": f"{b1}{b2}파",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "activation_status": "active",
                            "activation_rule_id": PAIR_PRESENCE_ACTIVE_RULE_ID,
                            "description": desc
                        })

            # (6) 반합 (半合)
            _, half_haps = check_three_hap(b1, i, branches, day_stem)
            if half_haps:
                for hh in half_haps:
                    if hh.get('with_index') == j:
                        h_type = hh.get('type', '반합')
                        h_elem = hh.get('element', '')
                        fallback = hh.get('fallback_from')
                        base_score = 1.3 if '전반합' in h_type else (1.1 if '후반합' in h_type else 0.6)
                        score = round(base_score * weight, 2)
                        desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                                f"{h_type}({h_elem}): " +
                                ('삼합 훼손 후 남은 반합 후보' if fallback else
                                 '협력 및 발전적 결합'))
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "반합(半合)",
                            "name": f"{b1}{b2}반합",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "candidate_element": h_elem,
                            "transformed_element": None,
                            "activation_status": "potential",
                            "condition_evidence": ({
                                'fallback_from': {
                                    'group_branches': fallback['group_branches'],
                                    'clashed_branch': fallback['clashed_branch'],
                                    'clashed_pillar': PILLAR_KEYS[fallback['clashed_index']],
                                    'clashing_pillar': PILLAR_KEYS[fallback['clashing_index']],
                                    'reason': fallback['reason'],
                                },
                            } if fallback else {}),
                            "description": desc
                        })

            # (7) 공합: 중신이 없는 생지·성지 구조 후보. 점수는 아직 보정하지 않는다.
            gong = next((item for item in check_gong_hap(b1, i, branches, day_stem)
                         if item['with_index'] == j), None)
            if gong:
                desc = (f"{name_from}지({b1})-{name_to}지({b2}) 공합 후보: "
                        f"중신 {gong['missing']} 부재")
                summary_list.append(desc)
                matrix.append({
                    'category': '지지', 'type': '공합(拱合)', 'name': f'{b1}{b2}공합',
                    'from_pillar': pos_from, 'to_pillar': pos_to,
                    'is_adjacent': dist == 1, 'weight': weight, 'score': 0.0,
                    'candidate_element': gong['element'],
                    'missing_branch': gong['missing'],
                    'activation_status': 'candidate_only', 'description': desc,
                })

            # (8) 암합: 두 지지의 지장간 천간합. 합화 오행을 확정하지 않는다.
            hidden_hap = next((item for item in check_hidden_stem_hap(
                b1, i, branches, day_stem) if item['with_index'] == j), None)
            if hidden_hap:
                desc = f"{name_from}지({b1})-{name_to}지({b2}) 지장간 암합 후보"
                summary_list.append(desc)
                matrix.append({
                    'category': '지지', 'type': '암합(暗合)', 'name': f'{b1}{b2}암합',
                    'from_pillar': pos_from, 'to_pillar': pos_to,
                    'is_adjacent': dist == 1, 'weight': weight, 'score': 0.0,
                    'hidden_stem_pairs': hidden_hap['hidden_stem_pairs'],
                    'activation_status': 'candidate_only', 'description': desc,
                })

    # 2. 천간 간 조합 분석
    for i in range(4):
        for j in range(i + 1, 4):
            dist = j - i
            weight = get_dist_weight(dist)
            pos_from = PILLAR_KEYS[i]
            pos_to = PILLAR_KEYS[j]
            name_from = POSITION_NAMES[i]
            name_to = POSITION_NAMES[j]
            s1 = stems[i]
            s2 = stems[j]

            # 천간합 (五合)
            stem_haps = check_stem_combination(s1, i, stems, day_stem)
            if stem_haps:
                for h in stem_haps:
                    if h.get('with_index') == j:
                        score = 1.8 * weight
                        desc = (f"{name_from}간({s1})-{name_to}간({s2}) "
                                f"천간합 후보({h['combined_element']}): 유화 및 의기투합")
                        summary_list.append(desc)
                        matrix.append({
                            "category": "천간",
                            "type": "천간합(天干合)",
                            "name": f"{s1}{s2}합",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "candidate_element": h['combined_element'],
                            "transformed_element": None,
                            "description": desc
                        })

            # 천간충
            stem_conflicts = check_stem_conflict(s1, i, stems, day_stem)
            if stem_conflicts:
                for c in stem_conflicts:
                    if c.get('with_index') == j:
                        score = 1.5 * weight
                        tension_score += score
                        desc = f"{name_from}간({s1})-{name_to}간({s2}) 천간충: 직접적인 대립 및 표출"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "천간",
                            "type": "천간충(天干沖)",
                            "name": f"{s1}{s2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

    # 3. 삼합 / 방합 / 삼형 구조 확인
    seen_three_punishments = set()
    for i in range(4):
        for group in check_three_punishment(branches[i], i, branches, day_stem):
            kind = group['type']
            if kind in seen_three_punishments:
                continue
            seen_three_punishments.add(kind)
            desc = f"지지 삼형({kind}): 세 지지의 형 구조 성립"
            summary_list.append(desc)
            matrix.append({
                'category': '지지',
                'type': '삼형(三刑)',
                'name': kind,
                'participants': [PILLAR_KEYS[p] for p in group['participant_indices']],
                'formations': [[PILLAR_KEYS[p] for p in formation]
                               for formation in group['formation_indices']],
                'from_pillar': 'all', 'to_pillar': 'all',
                'is_adjacent': group['is_adjacent'],
                'weight': 1.0,
                # 각 쌍의 천·충·육합 또는 지세형·충과 중복 가산하지 않는다.
                'score': 0.0,
                'activation_status': 'active',
                'activation_rule_id': TRIPLE_PUNISHMENT_PRESENCE_RULE_ID,
                'description': desc,
            })

    seen_three_haps = set()
    for i in range(4):
        three_haps, _ = check_three_hap(branches[i], i, branches, day_stem)
        for th in three_haps:
            elem = th.get('element', '')
            if elem not in seen_three_haps:
                seen_three_haps.add(elem)
                status = th['activation_status']
                score = 3.0 if status == 'potential' else 0.0
                desc = (f"지지 삼합({elem}국): " +
                        ("국(局) 형성 후보" if status == 'potential' else
                         "구조 조건으로 국(局) 형성 유보"))
                summary_list.append(desc)
                matrix.append({
                    "category": "지지",
                    "type": "삼합(三合)",
                    "name": f"삼합 {elem}국",
                    "participants": [PILLAR_KEYS[p] for p in th["participant_indices"]],
                    "formations": [[PILLAR_KEYS[p] for p in formation] for formation in th["formation_indices"]],
                    "from_pillar": "all",
                    "to_pillar": "all",
                    "is_adjacent": th.get('is_adjacent', True),
                    "weight": 1.0,
                    "score": score,
                    "candidate_element": elem,
                    "transformed_element": None,
                    "activation_status": status,
                    "status_reasons": th['status_reasons'],
                    "condition_evidence": {
                        'middle_pillars': [PILLAR_KEYS[p] for p in
                                           th['condition_evidence']['middle_indices']],
                        'adjacent_clashes': [
                            {'middle_pillar': PILLAR_KEYS[pair['middle_index']],
                             'clashing_pillar': PILLAR_KEYS[pair['clashing_index']]}
                            for pair in th['condition_evidence']['adjacent_clashes']
                        ],
                        'adjacent_wing_clashes': [
                            {'wing_pillar': PILLAR_KEYS[pair['wing_index']],
                             'wing_role': pair['wing_role'],
                             'clashing_pillar': PILLAR_KEYS[pair['clashing_index']]}
                            for pair in th['condition_evidence']['adjacent_wing_clashes']
                        ],
                    },
                    "description": desc
                })

    seen_square_haps = set()
    for i in range(4):
        square_haps = check_square_hap(branches[i], i, branches, day_stem)
        if square_haps and isinstance(square_haps, list):
            for sq in square_haps:
                elem = sq.get('element', '')
                season = sq.get('season', '')
                if elem not in seen_square_haps:
                    seen_square_haps.add(elem)
                    desc = f"지지 방합({season} {elem}방): 강력한 방위 계절 세력 형성"
                    summary_list.append(desc)
                    matrix.append({
                        "category": "지지",
                        "type": "방합(方合)",
                        "name": f"방합 {season}{elem}",
                        "participants": [PILLAR_KEYS[p] for p in sq["participant_indices"]],
                        "formations": [[PILLAR_KEYS[p] for p in formation] for formation in sq["formation_indices"]],
                        "from_pillar": "all",
                        "to_pillar": "all",
                        "is_adjacent": sq.get('is_adjacent', True),
                        "weight": 1.0,
                        "score": 3.5,
                        "candidate_element": elem,
                        "transformed_element": None,
                        "activation_status": "potential",
                        "description": desc
                    })


    # IDs depend on relation identity and positions, never list order or scores.
    for item in matrix:
        is_group = item['from_pillar'] == 'all'
        item['relation_scope'] = 'group' if is_group else 'pairwise'
        if not is_group:
            item['participants'] = [item['from_pillar'], item['to_pillar']]
            item['formations'] = []
        item['relation_id'] = ':'.join((item['category'], item['type'], item['name'],
                                        ','.join(item['participants'])))

    # 서로 다른 관계 후보는 보존한다. 총점에는 활성 다자 구조 안의 같은 쌍을
    # 한 번만 반영하고, 쌍의 개별 잠재 점수와 방향별 작용은 그대로 남긴다.
    for item in matrix:
        item['score_contribution'] = item['score']
        item['score_covered_by'] = None
    for group in matrix:
        covered_types = HARMONY_GROUP_COVERS_PAIR.get(group['type'])
        if not covered_types or group['score'] <= 0:
            continue
        formations = [set(formation) for formation in group['formations']]
        for item in matrix:
            if (item['type'] in covered_types and item['score_contribution'] > 0 and
                    any(set(item['participants']) <= formation
                        for formation in formations)):
                item['score_contribution'] = 0.0
                item['score_covered_by'] = group['relation_id']
    harmony_score = sum(item['score_contribution'] for item in matrix
                        if item['type'] in HARMONY_SCORE_TYPES)

    return {
        "rule_version": "1.3.0",
        "summary_list": list(dict.fromkeys(summary_list)),
        "matrix": matrix,
        "tension_score": round(tension_score, 1),
        "harmony_score": round(harmony_score, 1),
        "climate": "격렬한 변동과 도전형" if tension_score > harmony_score + 2 else (
            "유화적이고 안정적인 조화형" if harmony_score > tension_score + 2 else "긴장과 조화가 공존하는 복합형"
        )
    }
