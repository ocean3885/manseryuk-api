from services.relation_rules import JAHAB_MAP


def check_jahab(stem, branch, idx, chung_list, punish_list):
    """등록 자합 조합과 함께 존재하는 형·충만 기록한다. 성립·영향은 미평가다."""
    jinfo = JAHAB_MAP.get((stem, branch))
    if jinfo is None:
        return None
    context = []
    for kind, matches in (('clash', chung_list or []), ('punishment', punish_list or [])):
        for match in matches:
            context.append({
                'type': ('self_punishment' if kind == 'punishment' and match['type'] == '자형'
                         else kind),
                'with': match['with'],
                'with_index': match['with_index'],
                'with_ten_star': match['with_ten_star'],
                'distance': abs(idx - match['with_index']),
                'is_adjacent': abs(idx - match['with_index']) == 1,
            })
    return {
        'chars': (stem, branch),
        'my_index': idx,
        'exists': True,
        'hidden_stem': jinfo['hidden'],
        'candidate_element': jinfo['element'],
        'activation_status': 'detected',
        'impact_status': 'not_evaluated',
        'related_branch_relations': context,
    }
