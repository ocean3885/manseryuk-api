from services.constants import SIX_HAPS, CHUNGS, CHEONS, BREAKS, THREE_HAPS, THREE_HAPS_BIRTH, THREE_HAPS_KING, THREE_HAPS_SUCCESS, SQUARE_HAPS, PUNISHMENTS
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


def check_chung(target_branch, target_index, all_branches, day_stem):
    """충 (沖) 관계 확인 - 여러 개 있을 수 있음, 기준/상대 지지 정보 및 십성 포함"""
    results = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in CHUNGS or (other_branch, target_branch) in CHUNGS:
            distance = abs(i - target_index)
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            })
    return results if results else None


def check_cheon(target_branch, target_index, all_branches, day_stem):
    """천 (穿) 관계 확인 - 여러 개 있을 수 있음, 기준/상대 지지 정보 및 십성 포함"""
    results = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in CHEONS or (other_branch, target_branch) in CHEONS:
            distance = abs(i - target_index)
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            })
    return results if results else None


def check_break(target_branch, target_index, all_branches, day_stem):
    """파 (破) 관계 확인 - 여러 개 있을 수 있음, 기준/상대 지지 정보 및 십성 포함"""
    results = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in BREAKS or (other_branch, target_branch) in BREAKS:
            distance = abs(i - target_index)
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            })
    return results if results else None


def check_three_hap(target_branch, target_index, all_branches, day_stem):
    """삼합 (三合) 및 반합 관계 확인"""
    three_haps = []
    half_haps = []
    
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for (b1, b2, b3), element in THREE_HAPS.items():
        if target_branch not in (b1, b2, b3):
            continue
        
        others = [b for b in (b1, b2, b3) if b != target_branch]
        others_exist = [other for other in others if other in all_branches]
        
        if len(others_exist) == 2:
            # 완전 삼합 - 여러 상대 → with_branches 리스트
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
            
            with_branches = []
            for other in others_exist:
                other_idx = all_branches.index(other)
                with_branches.append({
                    'char': other,
                    'index': other_idx,
                    'ten_star': get_ten_star_branch(day_stem, other)
                })
            
            three_haps.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'branches': [b1, b2, b3],
                'with_branches': with_branches,
                'element': element,
                'strength': 1.0 if is_continuous else (0.8 if is_adjacent else 0.6),
                'is_continuous': is_continuous,
                'is_adjacent': is_adjacent
            })
            
        elif len(others_exist) == 1:
            # 반합 - 단일 상대 → with, with_position, with_ten_star
            third_branch = [b for b in (b1, b2, b3) if b != target_branch and b != others_exist[0]][0]
            third_exists = third_branch in all_branches
            
            if not third_exists:
                other_pos = [i for i, b in enumerate(all_branches) if b == others_exist[0]][0]
                is_adjacent = (abs(target_index - other_pos) == 1)
                
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
                    'my': target_branch,
                    'my_index': target_index,
                    'my_ten_star': my_ten_star,
                    'with': others_exist[0],
                    'with_index': other_pos,
                    'with_ten_star': get_ten_star_branch(day_stem, others_exist[0]),
                    'missing': third_branch,
                    'element': element,
                    'type': hab_type,
                    'strength': strength,
                    'is_adjacent': is_adjacent
                })
    
    return three_haps, half_haps


def check_square_hap(target_branch, target_index, all_branches, day_stem):
    """방합 (方合) 관계 확인 - 완전한 방합만 반환, check_chung과 유사한 구조"""
    results = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
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
            
            # 거리 계산 (첫 지지와 마지막 지지 간격)
            distance = positions[-1] - positions[0]
            is_adjacent = (distance <= 2)
            
            # strength: 방합 고유 파워 부스트에 위치 기반 가중치 적용
            strength = info['power_boost'] if is_adjacent else info['power_boost'] * 0.6
            
            # with_branches 리스트 생성
            with_branches = []
            for other in others_exist:
                other_idx = all_branches.index(other)
                with_branches.append({
                    'char': other,
                    'index': other_idx,
                    'ten_star': get_ten_star_branch(day_stem, other)
                })
            
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'branches': [b1, b2, b3],          # 전체 방합 지지
                'with_branches': with_branches,    # 상대 두 지지 상세 정보
                'element': info['element'],
                'season': info['season'],
                'strength': strength,
                'is_adjacent': is_adjacent,
                'distance': distance
            })
    
    return results if results else None


def check_punishment(target_branch, target_index, all_branches, day_stem):
    """형 (刑) 관계 확인 - check_chung과 동일한 반환 구조"""
    punishments = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        distance = abs(i - target_index)
        strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
        is_adjacent = (distance == 1)
        
        # 무은지형 (寅-巳, 巳-申, 申-寅)
        if (target_branch, other_branch) in PUNISHMENTS['무은지형'] or (other_branch, target_branch) in PUNISHMENTS['무은지형']:
            third_map = {
                frozenset(['寅','巳']): '申',
                frozenset(['巳','申']): '寅',
                frozenset(['申','寅']): '巳'
            }
            third_needed = third_map.get(frozenset([target_branch, other_branch]))
            is_complete = third_needed and third_needed in all_branches
            
            # 완전한 무은지형은 strength 보정 (1.2배, 최대 1.0)
            final_strength = min(strength * 1.2, 1.0) if is_complete else strength * 0.8
            
            punishments.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': final_strength,
                'is_adjacent': is_adjacent,
                'type': '무은지형',
                'is_complete': is_complete
            })
        
        # 지세형 (丑-戌, 戌-未, 丑-未)
        elif (target_branch, other_branch) in PUNISHMENTS['지세형'] or (other_branch, target_branch) in PUNISHMENTS['지세형']:
            # 지세형은 기본 strength에 0.9 가중치 (선택)
            final_strength = strength * 0.9
            punishments.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': final_strength,
                'is_adjacent': is_adjacent,
                'type': '지세형'
            })
        
        # 자묘형 (子-卯)
        elif (target_branch, other_branch) in PUNISHMENTS['자묘형'] or (other_branch, target_branch) in PUNISHMENTS['자묘형']:
            final_strength = strength * 0.85
            punishments.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': final_strength,
                'is_adjacent': is_adjacent,
                'type': '자묘형'
            })
        
        # 자형 (辰-辰, 午-午, 酉-酉, 亥-亥)
        elif target_branch == other_branch and target_branch in ['辰', '午', '酉', '亥']:
            final_strength = strength * 0.7
            punishments.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'distance': distance,
                'strength': final_strength,
                'is_adjacent': is_adjacent,
                'type': '자형'
            })
    
    # 중복 제거 (같은 상대, 같은 형 타입이 두 번 들어갈 가능성은 거의 없으나 안전하게)
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
    
    three_haps, half_haps = check_three_hap(target_branch, target_index, all_branches, day_stem)
    
    relations = {
        'six_haps': check_six_hap(target_branch, target_index, all_branches, day_stem),
        'chungs': check_chung(target_branch, target_index, all_branches, day_stem),
        'cheons': check_cheon(target_branch, target_index, all_branches, day_stem),
        'breaks': check_break(target_branch, target_index, all_branches, day_stem),
        'three_haps': three_haps,
        'half_haps': half_haps,
        'square_haps': check_square_hap(target_branch, target_index, all_branches, day_stem),
        'punishments': check_punishment(target_branch, target_index, all_branches, day_stem)
    }
    
    return relations