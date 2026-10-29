from services.relation_rules import JAHAB_MAP


def check_jahab(stem, branch, idx, chung_list, punish_list):
    """
    간지자합(干支自合) 정보 반환 (활성 여부 포함)
    :param stem: 천간
    :param branch: 지지
    :param idx: 기둥 인덱스
    :param chung_list: 해당 지지의 충 리스트
    :param punish_list: 해당 지지의 형 리스트
    :return: 자합 정보 딕셔너리 (항상 반환, 없으면 None)
    """
    key = (stem, branch)
    if key not in JAHAB_MAP:
        return None

    jinfo = JAHAB_MAP[key]
    
    # 기본 정보
    result = {
        'chars': (stem, branch),  
        'exists': True,                     # 항상 존재 (해당 일주 자체는 자합 후보)
        'active': False,                    # 현재 조건 충족 여부
        'hidden_stem': jinfo['hidden'],
        'combined_element': jinfo['element'],
        'is_conditional': jinfo['conditional'],
    }
    
    # 조건부 자합인 경우 필요 조건 명시
    if jinfo['conditional']:
        required_type, required_branch = jinfo['required']
        result['required_condition'] = {
            'type': required_type,
            'with_branch': required_branch
        }
        # 현재 punish_list에서 필요 조건이 있는지 확인
        condition_met = any(
            p.get('type') == required_type and p.get('with') == required_branch
            for p in punish_list
        )
        result['active'] = condition_met
        result['condition_met'] = condition_met
    else:
        # 비조건부 자합은 항상 활성
        result['active'] = True

    # 戌의 未형은 자합 후보를 열지만, 辰충이 있으면 丙戌·壬戌 자합은 성립하지 않는다.
    blocked_by = jinfo.get('blocked_by_chung')
    blocking_chung = next((c for c in (chung_list or [])
                           if c.get('with') == blocked_by), None) if blocked_by else None
    if blocking_chung:
        result['active'] = False
        result['inactive_reason'] = 'blocked_by_chen_chung'
        result['blocking_chung'] = {
            'with_branch': blocked_by,
            'with_index': blocking_chung['with_index'],
        }
    elif jinfo['conditional'] and not result['active']:
        result['inactive_reason'] = 'required_punishment_missing'
    
    if chung_list:
        strongest_chung = max(chung_list, key=lambda x: x.get('strength', 0))
        result['chung_impact'] = {
            'with_branch': strongest_chung['with'],
            'with_index': strongest_chung['with_index'],
            'distance': strongest_chung['distance'],
            'strength': strongest_chung['strength'],
            'is_adjacent': strongest_chung['is_adjacent']
        }
    else:
        result['chung_impact'] = None
    
    return result
