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
)
from services.relation_rules import get_pair_action_rule

POSITION_NAMES = ['년', '월', '일', '시']
PILLAR_KEYS = ['year', 'month', 'day', 'hour']

def build_interaction_matrix(stems: List[str], branches: List[str], day_stem: str) -> Dict[str, Any]:
    """
    4개 기둥 간의 모든 천간/지지 상호작용(합, 충, 형, 천, 파, 극)을 분석하고
    위치별 관계 매트릭스와 각 관계의 설명을 반환합니다. 점수·총계·기후 유형은 산출하지 않습니다.
    """
    matrix: List[Dict[str, Any]] = []
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
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 육충 관계가 있습니다."
                        matrix.append({
                            "category": "지지",
                            "type": "충(沖)",
                            "name": f"{b1}{b2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "activation_status": c['activation_status'],
                            "activation_rule_id": c['activation_rule_id'],
                            "status_reasons": c['status_reasons'],
                            "description": desc
                        })

            # (2) 육합 (六合)
            six_hap = next((hap for hap in check_six_haps(b1, i, branches, day_stem)
                            if hap['with_index'] == j), None)
            if six_hap and six_hap.get('with_index') == j:
                status = six_hap['activation_status']
                pair_rule = get_pair_action_rule(b1, b2, '육합(六合)')
                effect = pair_rule[1] if pair_rule else {}
                hidden_candidates = [
                    {'pillar': pos_from if candidate['branch'] == b1 else pos_to,
                     **candidate, 'activation_status': 'candidate_only'}
                    for candidate in effect.get('hidden_stem_candidates', [])
                ]
                desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                        f"육합 조합({six_hap['candidate_element']} 후보): "
                        '조합과 주변 충의 존재를 기록함')
                matrix.append({
                    "category": "지지",
                    "type": "육합(六合)",
                    "name": f"{b1}{b2}합",
                    "from_pillar": pos_from,
                    "to_pillar": pos_to,
                    "is_adjacent": (dist == 1),
                    "weight": weight,
                    "candidate_element": six_hap['candidate_element'],
                    "transformed_element": None,
                    "activation_status": status,
                    "activation_rule_id": six_hap['activation_rule_id'],
                    "status_reasons": six_hap['status_reasons'],
                    "condition_evidence": {
                        'summary': six_hap['condition_evidence']['summary'],
                        'adjacent_clashes': [
                            {**clash,
                             'member_pillar': PILLAR_KEYS[clash['member_index']],
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
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 천(穿) 관계가 있습니다."
                        matrix.append({
                            "category": "지지",
                            "type": "천(穿)",
                            "name": f"{b1}{b2}천",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "activation_status": c['activation_status'],
                            "activation_rule_id": c['activation_rule_id'],
                            "status_reasons": c['status_reasons'],
                            "description": desc
                        })

            # (4) 형 (刑)
            punishments = check_punishment(b1, i, branches, day_stem)
            if punishments:
                for p in punishments:
                    if p.get('with_index') == j:
                        is_self_punishment = p.get('type') == '자형'
                        candidate_only = p['activation_status'] == 'candidate_only'
                        desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                                f"형({p.get('type', '')}): " +
                                ("격위 자형 후보" if candidate_only else
                                 "인접 자형 성립" if is_self_punishment else "형 관계가 있습니다."))
                        matrix.append({
                            "category": "지지",
                            "type": "형(刑)",
                            "name": f"{p.get('type', '')}",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "activation_status": p['activation_status'],
                            "activation_rule_id": p['activation_rule_id'],
                            "status_reasons": p['status_reasons'],
                            "description": desc
                        })

            # (5) 파 (破)
            breaks = check_break(b1, i, branches, day_stem)
            if breaks:
                for b in breaks:
                    if b.get('with_index') == j:
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 파 관계가 있습니다."
                        matrix.append({
                            "category": "지지",
                            "type": "파(破)",
                            "name": f"{b1}{b2}파",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "activation_status": b['activation_status'],
                            "activation_rule_id": b['activation_rule_id'],
                            "status_reasons": b['status_reasons'],
                            "description": desc
                        })

            # (6) 반합 (半合)
            _, half_haps = check_three_hap(b1, i, branches, day_stem)
            if half_haps:
                for hh in half_haps:
                    if hh.get('with_index') == j:
                        h_type = hh.get('type', '반합')
                        h_elem = hh['candidate_element']
                        fallback = hh.get('fallback_from')
                        desc = (f"{name_from}지({b1})-{name_to}지({b2}) "
                                f"{h_type}({h_elem}): " +
                                ('삼합 날개 인접 충과 함께 있는 반합 후보' if fallback else
                                 '두 지지의 반합 후보'))
                        matrix.append({
                            "category": "지지",
                            "type": "반합(半合)",
                            "name": f"{b1}{b2}반합",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "candidate_element": h_elem,
                            "transformed_element": None,
                            "activation_status": hh['activation_status'],
                            "status_reasons": hh['status_reasons'],
                            "condition_evidence": ({
                                'summary': fallback['description'],
                                'fallback_from': {
                                    **fallback,
                                    'group_branches': fallback['group_branches'],
                                    'clashed_branch': fallback['clashed_branch'],
                                    'clashed_pillar': PILLAR_KEYS[fallback['clashed_index']],
                                    'clashing_pillar': PILLAR_KEYS[fallback['clashing_index']],
                                    'reason': fallback['reason'],
                                },
                            } if fallback else {}),
                            "description": desc
                        })

            # (7) 공합: 중신이 없는 생지·성지 구조 후보.
            gong = next((item for item in check_gong_hap(b1, i, branches, day_stem)
                         if item['with_index'] == j), None)
            if gong:
                desc = (f"{name_from}지({b1})-{name_to}지({b2}) 공합 후보: "
                        f"중신 {gong['missing']} 부재")
                matrix.append({
                    'category': '지지', 'type': '공합(拱合)', 'name': f'{b1}{b2}공합',
                    'from_pillar': pos_from, 'to_pillar': pos_to,
                    'is_adjacent': dist == 1, 'weight': weight,
                    'candidate_element': gong['candidate_element'],
                    'missing_branch': gong['missing'],
                    'activation_status': gong['activation_status'], 'status_reasons': gong['status_reasons'], 'description': desc,
                })

            # (8) 암합: 두 지지의 지장간 천간합. 합화 오행을 확정하지 않는다.
            hidden_hap = next((item for item in check_hidden_stem_hap(
                b1, i, branches, day_stem) if item['with_index'] == j), None)
            if hidden_hap:
                desc = f"{name_from}지({b1})-{name_to}지({b2}) 지장간 암합 후보"
                matrix.append({
                    'category': '지지', 'type': '암합(暗合)', 'name': f'{b1}{b2}암합',
                    'from_pillar': pos_from, 'to_pillar': pos_to,
                    'is_adjacent': dist == 1, 'weight': weight,
                    'hidden_stem_pairs': hidden_hap['hidden_stem_pairs'],
                    'activation_status': hidden_hap['activation_status'], 'status_reasons': hidden_hap['status_reasons'], 'description': desc,
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
                        desc = (f"{name_from}간({s1})-{name_to}간({s2}) "
                                f"천간합 조합({h['candidate_element']} 후보)")
                        matrix.append({
                            "category": "천간",
                            "type": "천간합(天干合)",
                            "name": f"{s1}{s2}합",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "candidate_element": h['candidate_element'],
                            "activation_status": h['activation_status'],
                            "status_reasons": h['status_reasons'],
                            "transformed_element": None,
                            "description": desc
                        })

            # 천간충
            stem_conflicts = check_stem_conflict(s1, i, stems, day_stem)
            if stem_conflicts:
                for c in stem_conflicts:
                    if c.get('with_index') == j:
                        desc = f"{name_from}간({s1})-{name_to}간({s2}) 천간충 관계가 있습니다."
                        matrix.append({
                            "category": "천간",
                            "type": "천간충(天干沖)",
                            "name": f"{s1}{s2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "activation_status": c['activation_status'],
                            "status_reasons": c['status_reasons'],
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
                'activation_status': group['activation_status'],
                'activation_rule_id': group['activation_rule_id'],
                'status_reasons': group['status_reasons'],
                'description': desc,
            })

    seen_three_haps = set()
    for i in range(4):
        three_haps, _ = check_three_hap(branches[i], i, branches, day_stem)
        for th in three_haps:
            elem = th['candidate_element']
            if elem not in seen_three_haps:
                seen_three_haps.add(elem)
                status = th['activation_status']
                desc = f"지지 삼합({elem}국 후보): 구성·중신 위치·주변 충을 기록함"
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
                    "candidate_element": elem,
                    "transformed_element": None,
                    "activation_status": status,
                    "status_reasons": th['status_reasons'],
                    "condition_evidence": {
                        'summary': th['condition_evidence']['summary'],
                        'middle_members': th['condition_evidence']['middle_members'],
                        'middle_count': th['condition_evidence']['middle_count'],
                        'middle_pillars': [PILLAR_KEYS[p] for p in
                                           th['condition_evidence']['middle_indices']],
                        'adjacent_clashes': [
                            {**pair,
                             'middle_pillar': PILLAR_KEYS[pair['middle_index']],
                             'clashing_pillar': PILLAR_KEYS[pair['clashing_index']]}
                            for pair in th['condition_evidence']['adjacent_clashes']
                        ],
                        'adjacent_wing_clashes': [
                            {**pair,
                             'wing_pillar': PILLAR_KEYS[pair['wing_index']],
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
                elem = sq['candidate_element']
                season = sq.get('season', '')
                if elem not in seen_square_haps:
                    seen_square_haps.add(elem)
                    desc = f"지지 방합({season} {elem}방): 방합 구성 후보"
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
                        "candidate_element": elem,
                        "transformed_element": None,
                        "activation_status": sq['activation_status'],
                        "status_reasons": sq['status_reasons'],
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

    return {
        "rule_version": "3.0.0",
        "matrix": matrix,
    }
