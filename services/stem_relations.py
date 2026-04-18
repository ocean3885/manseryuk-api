from services.calculator import get_ten_star_branch, get_ten_star_stem

STEM_COMBINATIONS = {
    ('甲', '己'): '土',
    ('乙', '庚'): '金',
    ('丙', '辛'): '水',
    ('丁', '壬'): '木',
    ('戊', '癸'): '火'
}

STEM_CONFLICTS = {
    ('甲', '庚'), ('乙', '辛'), ('丙', '壬'), ('丁', '癸')
}

# 천간 극 관계 및 강도 (극하는 자, 극당하는 자): 강도
STEM_RESTRAIN = {
    ('甲', '戊'): 1.0,
    ('乙', '戊'): 0.5,
    ('乙', '己'): 1.0,
    ('丙', '庚'): 1.0,
    ('丁', '庚'): 0.5,
    ('丁', '辛'): 1.0,
    ('戊', '壬'): 1.0,
    ('己', '壬'): 0.5,
    ('己', '癸'): 1.0,
    ('辛', '甲'): 0.5,
    ('癸', '丙'): 0.5,
}


def check_stem_combination(target_stem, target_index, all_stems, day_stem):
    """천간 합 (五合)"""
    results = []
    
    # my_ten_star: target_index가 2(일간)면 '일간', 아니면 정상 십성
    if target_index == 2:
        my_ten_star = '일간'
    else:
        my_ten_star = get_ten_star_stem(day_stem, target_stem)

    for i, other_stem in enumerate(all_stems):
        if i == target_index:
            continue

        # 합 관계 확인
        combined_element = None
        for (a, b), element in STEM_COMBINATIONS.items():
            if (target_stem == a and other_stem == b) or (target_stem == b and other_stem == a):
                combined_element = element
                break

        if combined_element:
            distance = abs(i - target_index)
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            # with_ten_star: 상대 인덱스가 2면 '일간'
            if i == 2:
                with_ten_star = '일간'
            else:
                with_ten_star = get_ten_star_stem(day_stem, other_stem)

            results.append({
                'my': target_stem,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_stem,
                'with_index': i,
                'with_ten_star': with_ten_star,
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1),
                'combined_element': combined_element
            })
    return results if results else None

def check_stem_restrain(target_stem, target_index, all_stems, day_stem):
    """
    천간 극(克) 관계 확인 - 내가 극하는 대상과 나를 극하는 대상 분리 반환
    :return: {'restrain_to': [...], 'restrain_me': [...]} 또는 빈 딕셔너리
    """
    result = {
        'restrain_to': [],   # 기준 천간이 극하는 대상들
        'restrain_me': []    # 기준 천간을 극하는 대상들
    }
    
    # 기준 천간의 십성 (일간이면 '일간')
    if target_index == 2:
        my_ten_star = '일간'
    else:
        my_ten_star = get_ten_star_stem(day_stem, target_stem)
    
    for i, other_stem in enumerate(all_stems):
        if i == target_index:
            continue
        
        # 극 관계 확인
        if (target_stem, other_stem) in STEM_RESTRAIN:
            base_strength = STEM_RESTRAIN[(target_stem, other_stem)]
            direction = 'target_restrains'
        elif (other_stem, target_stem) in STEM_RESTRAIN:
            base_strength = STEM_RESTRAIN[(other_stem, target_stem)]
            direction = 'target_restrained'
        else:
            continue
        
        distance = abs(i - target_index)
        distance_strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
        total_strength = distance_strength * base_strength
        
        # 상대 천간의 십성
        if i == 2:
            with_ten_star = '일간'
        else:
            with_ten_star = get_ten_star_stem(day_stem, other_stem)
        
        item = {
            'with': other_stem,
            'with_index': i,
            'with_ten_star': with_ten_star,
            'distance': distance,
            'is_adjacent': (distance == 1),
            'distance_strength': distance_strength,
            'restrain_base_strength': base_strength,
            'strength': total_strength,
            'my': target_stem,
            'my_index': target_index,
            'my_ten_star': my_ten_star
        }
        
        if direction == 'target_restrains':
            result['restrain_to'].append(item)
        else:
            result['restrain_me'].append(item)
    
    # 둘 다 비어있으면 None 반환 (또는 빈 딕셔너리, 필요에 따라)
    if not result['restrain_to'] and not result['restrain_me']:
        return None
    return result


def check_stem_conflict(target_stem, target_index, all_stems, day_stem):
    """천간 충 (沖) 관계 확인 - 여러 개 있을 수 있음, 기준/상대 정보 및 십성 포함"""
    results = []
    
    # 기준 천간의 십성 (일간 위치면 '일간')
    if target_index == 2:
        my_ten_star = '일간'
    else:
        my_ten_star = get_ten_star_stem(day_stem, target_stem)
    
    for i, other_stem in enumerate(all_stems):
        if i == target_index:
            continue
        
        # 충 관계 확인 (양방향)
        if (target_stem, other_stem) in STEM_CONFLICTS or (other_stem, target_stem) in STEM_CONFLICTS:
            distance = abs(i - target_index)
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            # 상대 천간의 십성
            if i == 2:
                with_ten_star = '일간'
            else:
                with_ten_star = get_ten_star_stem(day_stem, other_stem)
            
            results.append({
                'my': target_stem,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_stem,
                'with_index': i,
                'with_ten_star': with_ten_star,
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            })
    
    return results if results else None


def get_relations_for_stem(target_stem, target_index, all_branches, all_stems):
    """
    특정 천간 기준으로 다른 천간들과의 관계를 모두 찾는다.
    
    Args:
        target_stem: 관계를 구하려는 천간 (예: '甲')
        target_index: 해당 천간의 위치 (0:년, 1:월, 2:일, 3:시)
        all_branches: 전체 지지 리스트 [년지, 월지, 일지, 시지]
        all_stems:    [년간, 월간, 일간, 시간]  # 일간은 all_stems[2]
    
    Returns:
        dict: 해당 지지의 모든 관계 정보
    """
    day_stem = all_stems[2]   # 일간
    
    relations = {
        'combinations': check_stem_combination(target_stem, target_index, all_stems, day_stem),
        'restrain': check_stem_restrain(target_stem, target_index, all_stems, day_stem),
        'conflict': check_stem_conflict(target_stem, target_index, all_stems, day_stem),
    }
    
    return relations