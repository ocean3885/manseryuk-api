# 자합 매핑에 필요 조건 추가
JAHAB_MAP = {
    ('戊', '子'): {'hidden': '癸', 'element': '火', 'conditional': False, 'required': None},
    ('丁', '亥'): {'hidden': '壬', 'element': '木', 'conditional': False, 'required': None},
    ('己', '亥'): {'hidden': '甲', 'element': '土', 'conditional': False, 'required': None},
    ('辛', '巳'): {'hidden': '丙', 'element': '水', 'conditional': False, 'required': None},
    ('癸', '巳'): {'hidden': '戊', 'element': '火', 'conditional': False, 'required': None},
    ('壬', '午'): {'hidden': '丁', 'element': '木', 'conditional': False, 'required': None},
    ('甲', '午'): {'hidden': '己', 'element': '土', 'conditional': False, 'required': None},
    ('丙', '戌'): {'hidden': '辛', 'element': '水', 'conditional': True, 'required': ('지세형', '未')},
    ('壬', '戌'): {'hidden': '丁', 'element': '木', 'conditional': True, 'required': ('지세형', '未')},
}

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
    else:
        # 비조건부 자합은 항상 활성
        result['active'] = True
    
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