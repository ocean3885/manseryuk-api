from services.constants import SIX_HAPS, CHUNGS, HARMS, BREAKS, THREE_HAPS, THREE_HAPS_BIRTH, THREE_HAPS_KING, THREE_HAPS_SUCCESS, SQUARE_HAPS, PUNISHMENTS
from services.calculator import get_ten_star_branch


def check_six_hap(target_branch, target_index, all_branches, day_stem):
    """육합 (6合) 관계 확인"""
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        sorted_pair = tuple(sorted([target_branch, other_branch]))
        if sorted_pair in SIX_HAPS:
            element = SIX_HAPS[sorted_pair]
            is_adjacent = (abs(i - target_index) == 1)
            return {
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': get_ten_star_branch(day_stem, target_branch),
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'element': element,
                'type': '근합' if is_adjacent else '원합',
                'strength': 1.0 if is_adjacent else 0.5,
                'is_adjacent': is_adjacent
            }
    return None


def check_chung(target_branch, target_index, all_branches):
    """충 (沖) 관계 확인"""
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in CHUNGS or (other_branch, target_branch) in CHUNGS:
            distance = abs(i - target_index)
            # 인접 충(1)이 가장 강력, 멀수록 약화
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            return {
                'with': other_branch,
                'with_index': i,
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            }
    return None


def check_harm(target_branch, target_index, all_branches):
    """해 (害) 관계 확인"""
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in HARMS or (other_branch, target_branch) in HARMS:
            return {
                'with': other_branch,
                'with_index': i
            }
    return None


def check_break(target_branch, target_index, all_branches):
    """파 (破) 관계 확인"""
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in BREAKS or (other_branch, target_branch) in BREAKS:
            return {
                'with': other_branch,
                'with_index': i
            }
    return None


def check_three_hap(target_branch, target_index, all_branches):
    """삼합 (三合) 및 반합 관계 확인"""
    three_haps = []
    half_haps = []
    
    for (b1, b2, b3), element in THREE_HAPS.items():
        if target_branch not in (b1, b2, b3):
            continue
        
        others = [b for b in (b1, b2, b3) if b != target_branch]
        # 다른 두 개가 모두 all_branches에 있는지 확인
        others_exist = [other for other in others if other in all_branches]
        
        if len(others_exist) == 2:
            # 완전 삼합 (3개 모두 존재)
            positions = []
            for idx, branch in enumerate(all_branches):
                if branch in (b1, b2, b3):
                    positions.append(idx)
            positions.sort()
            
            max_gap = positions[-1] - positions[0]
            is_adjacent = (max_gap <= 2)
            is_continuous = (max_gap == 2 and 
                            positions[2] - positions[1] == 1 and 
                            positions[1] - positions[0] == 1)
            
            three_haps.append({
                'branches': [b1, b2, b3],
                'with': others_exist,
                'with_positions': [i for i, b in enumerate(all_branches) if b in others_exist],
                'element': element,
                'is_complete': True,
                'strength': 1.0 if is_continuous else (0.8 if is_adjacent else 0.6),
                'is_continuous': is_continuous,
                'is_adjacent': is_adjacent
            })
        elif len(others_exist) == 1:
            # 반합 (2개만 존재, 나머지 하나는 없음)
            third_branch = [b for b in (b1, b2, b3) if b != target_branch and b != others_exist[0]][0]
            third_exists = third_branch in all_branches
            
            if not third_exists:
                # 반합 유형 판단
                positions = [target_index]
                other_pos = [i for i, b in enumerate(all_branches) if b == others_exist[0]][0]
                positions.append(other_pos)
                positions.sort()
                is_adjacent = (positions[1] - positions[0] == 1)
                
                # 생지/왕지/성지 판단
                b_set = {b1, b2, b3}
                birth = [b for b in THREE_HAPS_BIRTH.get(element, []) if b in b_set]
                king = [b for b in THREE_HAPS_KING.get(element, []) if b in b_set]
                success = [b for b in THREE_HAPS_SUCCESS.get(element, []) if b in b_set]
                
                if target_branch in king and others_exist[0] in birth:
                    hab_type = '전반합 (생+왕)'
                    strength = 0.7
                elif target_branch in birth and others_exist[0] in king:
                    hab_type = '전반합 (생+왕)'
                    strength = 0.7
                elif target_branch in king and others_exist[0] in success:
                    hab_type = '후반합 (왕+성)'
                    strength = 0.6
                elif target_branch in success and others_exist[0] in king:
                    hab_type = '후반합 (왕+성)'
                    strength = 0.6
                else:
                    hab_type = '암합 (생+성)'
                    strength = 0.3
                
                half_haps.append({
                    'branches': [target_branch, others_exist[0]],
                    'with': others_exist[0],
                    'with_position': other_pos,
                    'missing': third_branch,
                    'element': element,
                    'type': hab_type,
                    'strength': strength,
                    'is_adjacent': is_adjacent
                })
    return three_haps, half_haps


def check_square_hap(target_branch, target_index, all_branches):
    """방합 (方合) 관계 확인"""
    square_haps = []
    for (b1, b2, b3), info in SQUARE_HAPS.items():
        if target_branch not in (b1, b2, b3):
            continue
        
        others = [b for b in (b1, b2, b3) if b != target_branch]
        others_exist = [other for other in others if other in all_branches]
        
        if len(others_exist) == 2:
            # 방합 완성 (3개 모두 존재)
            positions = []
            for idx, branch in enumerate(all_branches):
                if branch in (b1, b2, b3):
                    positions.append(idx)
            positions.sort()
            
            is_adjacent = (positions[-1] - positions[0] <= 2)
            
            square_haps.append({
                'branches': [b1, b2, b3],
                'with': others_exist,
                'with_positions': [i for i, b in enumerate(all_branches) if b in others_exist],
                'element': info['element'],
                'season': info['season'],
                'is_complete': True,
                'strength': info['power_boost'] if is_adjacent else info['power_boost'] * 0.6,
                'is_adjacent': is_adjacent
            })
    return square_haps


def check_punishment(target_branch, target_index, all_branches):
    """형 (刑) 관계 확인"""
    punishments = []
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        # 무은지형 (寅-巳, 巳-申, 申-寅)
        if (target_branch, other_branch) in PUNISHMENTS['무은지형'] or (other_branch, target_branch) in PUNISHMENTS['무은지형']:
            # 세 번째 지지가 있는지 확인 (완전한 무은지형)
            third_map = {
                frozenset(['寅','巳']): '申',
                frozenset(['巳','申']): '寅',
                frozenset(['申','寅']): '巳'
            }
            third_needed = third_map.get(frozenset([target_branch, other_branch]))
            is_complete = third_needed and third_needed in all_branches
            
            punishments.append({
                'with': other_branch,
                'with_index': i,
                'type': '무은지형',
                'is_complete': is_complete,
                'strength': 1.0 if is_complete else 0.5
            })
        
        # 지세형 (丑-戌, 戌-未, 丑-未)
        elif (target_branch, other_branch) in PUNISHMENTS['지세형'] or (other_branch, target_branch) in PUNISHMENTS['지세형']:
            punishments.append({
                'with': other_branch,
                'with_index': i,
                'type': '지세형',
                'strength': 0.8
            })
        
        # 자묘형 (子-卯)
        elif (target_branch, other_branch) in PUNISHMENTS['자묘형'] or (other_branch, target_branch) in PUNISHMENTS['자묘형']:
            punishments.append({
                'with': other_branch,
                'with_index': i,
                'type': '자묘형',
                'strength': 0.7
            })
        
        # 자형 (辰-辰, 午-午, 酉-酉, 亥-亥) - 같은 글자
        elif target_branch == other_branch and target_branch in ['辰', '午', '酉', '亥']:
            punishments.append({
                'with': other_branch,
                'with_index': i,
                'type': '자형',
                'strength': 0.6
            })
    
    # 중복 제거 (같은 대상과 여러 형이 있을 수 있음)
    seen = set()
    unique_punishments = []
    for p in punishments:
        key = (p['with'], p['type'])
        if key not in seen:
            seen.add(key)
            unique_punishments.append(p)
    return unique_punishments


def get_relations_for_branch(target_branch, target_index, all_branches, all_stems):
    """
    특정 지지 기준으로 다른 지지들과의 관계를 모두 찾는다.
    
    Args:
        target_branch: 관계를 구하려는 지지 (예: '戌')
        target_index: 해당 지지의 위치 (0:년, 1:월, 2:일, 3:시)
        all_branches: 전체 지지 리스트 [년지, 월지, 일지, 시지]
        all_stems:    [년간, 월간, 일간, 시간]  # 일간은 all_stems[2]
    
    Returns:
        dict: 해당 지지의 모든 관계 정보
    """
    day_stem = all_stems[2]   # 일간
    
    three_haps, half_haps = check_three_hap(target_branch, target_index, all_branches)
    
    relations = {
        'six_haps': check_six_hap(target_branch, target_index, all_branches, day_stem),
        'chungs': check_chung(target_branch, target_index, all_branches),
        'harms': check_harm(target_branch, target_index, all_branches),
        'breaks': check_break(target_branch, target_index, all_branches),
        'three_haps': three_haps,
        'half_haps': half_haps,
        'square_haps': check_square_hap(target_branch, target_index, all_branches),
        'punishments': check_punishment(target_branch, target_index, all_branches)
    }
    
    return relations