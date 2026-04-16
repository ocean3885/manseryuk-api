from services.constants import SIX_HAPS, CHUNGS, HARMS, BREAKS, THREE_HAPS, THREE_HAPS_BIRTH, THREE_HAPS_KING, THREE_HAPS_SUCCESS, SQUARE_HAPS, PUNISHMENTS

def get_relations_for_branch(target_branch, target_index, all_branches):
    """
    특정 지지 기준으로 다른 지지들과의 관계를 모두 찾는다.
    
    Args:
        target_branch: 관계를 구하려는 지지 (예: '戌')
        target_index: 해당 지지의 위치 (0:년, 1:월, 2:일, 3:시)
        all_branches: 전체 지지 리스트 [년지, 월지, 일지, 시지]
    
    Returns:
        dict: 해당 지지의 모든 관계 정보
    """
    
    relations = {
        'six_haps': None,
        'chungs': None,
        'harms': None,
        'breaks': None,
        'three_haps': [],
        'square_haps': [],
        'half_haps': [],
        'punishments': []
    }
    
    # ========== 1. 육합 (6合) ==========
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        # 육합 체크
        if (target_branch, other_branch) in SIX_HAPS:
            pair = (target_branch, other_branch)
            element = SIX_HAPS[pair]
            is_adjacent = (abs(i - target_index) == 1)
            
            relations['six_haps'] = {
                'with': other_branch,
                'with_index': i,
                'element': element,
                'type': '근합' if is_adjacent else '원합',
                'strength': 1.0 if is_adjacent else 0.5,
                'is_adjacent': is_adjacent
            }
        elif (other_branch, target_branch) in SIX_HAPS:
            pair = (other_branch, target_branch)
            element = SIX_HAPS[pair]
            is_adjacent = (abs(i - target_index) == 1)
            
            relations['six_haps'] = {
                'with': other_branch,
                'with_index': i,
                'element': element,
                'type': '근합' if is_adjacent else '원합',
                'strength': 1.0 if is_adjacent else 0.5,
                'is_adjacent': is_adjacent
            }
    
    # ========== 2. 충 (沖) ==========
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in CHUNGS or (other_branch, target_branch) in CHUNGS:
            distance = abs(i - target_index)
            # 인접 충(1)이 가장 강력, 멀수록 약화
            strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
            
            relations['chungs'] = {
                'with': other_branch,
                'with_index': i,
                'distance': distance,
                'strength': strength,
                'is_adjacent': (distance == 1)
            }
    
    # ========== 3. 해 (害) ==========
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in HARMS or (other_branch, target_branch) in HARMS:
            relations['harms'] = {
                'with': other_branch,
                'with_index': i
            }
    
    # ========== 4. 파 (破) ==========
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        if (target_branch, other_branch) in BREAKS or (other_branch, target_branch) in BREAKS:
            relations['breaks'] = {
                'with': other_branch,
                'with_index': i
            }
    
    # ========== 5. 삼합 (三合) - target_branch 포함된 조합 ==========
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
            
            relations['three_haps'].append({
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
                
                relations['half_haps'].append({
                    'branches': [target_branch, others_exist[0]],
                    'with': others_exist[0],
                    'with_position': other_pos,
                    'missing': third_branch,
                    'element': element,
                    'type': hab_type,
                    'strength': strength,
                    'is_adjacent': is_adjacent
                })
    
    # ========== 6. 방합 (方合) ==========
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
            
            relations['square_haps'].append({
                'branches': [b1, b2, b3],
                'with': others_exist,
                'with_positions': [i for i, b in enumerate(all_branches) if b in others_exist],
                'element': info['element'],
                'season': info['season'],
                'is_complete': True,
                'strength': info['power_boost'] if is_adjacent else info['power_boost'] * 0.6,
                'is_adjacent': is_adjacent
            })
    
    # ========== 7. 형 (刑) ==========
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
            
            relations['punishments'].append({
                'with': other_branch,
                'with_index': i,
                'type': '무은지형',
                'is_complete': is_complete,
                'strength': 1.0 if is_complete else 0.5
            })
        
        # 지세형 (丑-戌, 戌-未, 丑-未)
        elif (target_branch, other_branch) in PUNISHMENTS['지세형'] or (other_branch, target_branch) in PUNISHMENTS['지세형']:
            relations['punishments'].append({
                'with': other_branch,
                'with_index': i,
                'type': '지세형',
                'strength': 0.8
            })
        
        # 자묘형 (子-卯)
        elif (target_branch, other_branch) in PUNISHMENTS['자묘형'] or (other_branch, target_branch) in PUNISHMENTS['자묘형']:
            relations['punishments'].append({
                'with': other_branch,
                'with_index': i,
                'type': '자묘형',
                'strength': 0.7
            })
        
        # 자형 (辰-辰, 午-午, 酉-酉, 亥-亥) - 같은 글자
        elif target_branch == other_branch and target_branch in ['辰', '午', '酉', '亥']:
            relations['punishments'].append({
                'with': other_branch,
                'with_index': i,
                'type': '자형',
                'strength': 0.6
            })
    
    # ========== 중복 제거 및 정리 ==========
    # punishments 중복 제거 (같은 대상과 여러 형이 있을 수 있음)
    seen = set()
    unique_punishments = []
    for p in relations['punishments']:
        key = (p['with'], p['type'])
        if key not in seen:
            seen.add(key)
            unique_punishments.append(p)
    relations['punishments'] = unique_punishments
    
    return relations