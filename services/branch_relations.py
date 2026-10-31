from itertools import combinations
from services.relation_rules import (SIX_HAPS, CHUNGS, CHEONS, BREAKS, THREE_HAPS,
    HALF_HAPS, GONG_HAPS, HIDDEN_STEM_HAPS, SQUARE_HAPS, PUNISHMENTS,
    THREE_PUNISHMENTS, STEM_COMBINATIONS, THREE_HAPS_KING,
    THREE_HAP_CONDITIONS, SIX_HAP_CONDITIONS)
from services.calculator import get_ten_star_branch


def check_six_haps(target_branch, target_index, all_branches, day_stem):
    """위치별 육합 전체를 반환한다. 같은 글자도 위치가 다르면 별개 관계다."""
    results = []
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        element = SIX_HAPS.get((target_branch, other_branch)) or SIX_HAPS.get((other_branch, target_branch))
        if element:
            is_adjacent = (abs(i - target_index) == 1)
            adjacent_clashes = []
            for clash_index, clash_branch in enumerate(all_branches):
                if clash_index in (target_index, i):
                    continue
                for member_index, member_branch in ((target_index, target_branch),
                                                    (i, other_branch)):
                    if abs(clash_index - member_index) != 1:
                        continue
                    if ((member_branch, clash_branch) not in CHUNGS and
                            (clash_branch, member_branch) not in CHUNGS):
                        continue
                    adjacent_clashes.append({
                        'member_index': member_index,
                        'clashing_index': clash_index,
                        'location': ('between' if min(target_index, i) < clash_index < max(target_index, i)
                                     else 'outside'),
                    })
            if any(clash['location'] == 'between' for clash in adjacent_clashes):
                reason = 'intervening_adjacent_clash'
            elif adjacent_clashes:
                reason = 'external_adjacent_clash'
            else:
                reason = None
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': get_ten_star_branch(day_stem, target_branch),
                'with': other_branch,
                'with_index': i,
                'with_ten_star': get_ten_star_branch(day_stem, other_branch),
                'element': element,
                'type': '근합' if is_adjacent else '원합',
                'strength': 1.0 if is_adjacent else 0.5,
                'is_adjacent': is_adjacent,
                'activation_status': SIX_HAP_CONDITIONS[reason] if reason else 'active',
                'status_reasons': [reason] if reason else [],
                'condition_evidence': {'adjacent_clashes': adjacent_clashes},
            })
    return results


def check_six_hap(target_branch, target_index, all_branches, day_stem):
    """기존 단일 육합 응답 호환용. 전체 결과는 check_six_haps 사용."""
    results = check_six_haps(target_branch, target_index, all_branches, day_stem)
    return results[0] if results else None


def _group_members(group_branches, target_index, all_branches, day_stem):
    positions = [i for i, branch in enumerate(all_branches) if branch in group_branches]
    formations = [list(indices) for indices in combinations(positions, 3)
                  if {all_branches[i] for i in indices} == set(group_branches)]
    others = [{"char": all_branches[i], "index": i,
               "ten_star": get_ten_star_branch(day_stem, all_branches[i])}
              for i in positions if i != target_index]
    return positions, formations, others


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


def _half_hap_matches(target_branch, target_index, other_branch, all_branches,
                      day_stem, element, missing=None, fallback_from=None):
    """반합의 위치별 후보. 깨진 삼합에서 남은 반합은 결손과 구분한다."""
    rule = (HALF_HAPS.get((target_branch, other_branch)) or
            HALF_HAPS.get((other_branch, target_branch)))
    if rule is None:
        return []
    return [{
        'my': target_branch,
        'my_index': target_index,
        'my_ten_star': get_ten_star_branch(day_stem, target_branch),
        'with': other_branch,
        'with_index': other_pos,
        'with_ten_star': get_ten_star_branch(day_stem, other_branch),
        'missing': missing,
        'fallback_from': fallback_from,
        'element': element,
        'type': f"{rule['type']} ({'생+왕' if rule['type'] == '전반합' else '왕+성'})",
        'strength': rule['strength'],
        'is_adjacent': abs(target_index - other_pos) == 1,
    } for other_pos, branch in enumerate(all_branches) if branch == other_branch]


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
            participant_indices, formation_indices, with_branches = _group_members(
                (b1, b2, b3), target_index, all_branches, day_stem
            )
            is_continuous = any(formation[-1] - formation[0] == 2
                                for formation in formation_indices)
            is_adjacent = is_continuous
            candidate_strength = 1.0 if is_continuous else 0.6
            middle = THREE_HAPS_KING[element][0]
            middle_indices = [i for i in participant_indices if all_branches[i] == middle]
            status_reasons = []
            if len(middle_indices) > 1:
                status_reasons.append('duplicate_middle')
            outside_indices = set(range(len(all_branches))) - set(participant_indices)
            adjacent_clashes = [
                {'middle_index': i, 'clashing_index': j}
                for i in middle_indices for j in sorted(outside_indices)
                if abs(i - j) == 1 and
                ((middle, all_branches[j]) in CHUNGS or
                 (all_branches[j], middle) in CHUNGS)
            ]
            if adjacent_clashes:
                status_reasons.append('adjacent_middle_clash')
            adjacent_wing_clashes = [
                {'wing_index': wing_index,
                 'wing_role': 'birth' if all_branches[wing_index] == b1 else 'tomb',
                 'clashing_index': j}
                for wing_index in participant_indices
                if all_branches[wing_index] in (b1, b3)
                for j in sorted(outside_indices)
                if abs(wing_index - j) == 1 and
                ((all_branches[wing_index], all_branches[j]) in CHUNGS or
                 (all_branches[j], all_branches[wing_index]) in CHUNGS)
            ]
            for role in ('birth', 'tomb'):
                if any(clash['wing_role'] == role for clash in adjacent_wing_clashes):
                    status_reasons.append(f'adjacent_{role}_clash')
            status = 'potential'
            for reason in status_reasons:
                if THREE_HAP_CONDITIONS[reason] == 'suppressed':
                    status = 'suppressed'
                    break
                status = THREE_HAP_CONDITIONS[reason]
            
            three_haps.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'branches': [b1, b2, b3],
                'participant_indices': participant_indices,
                'formation_indices': formation_indices,
                'with_branches': with_branches,
                'element': element,
                'strength': candidate_strength if status == 'potential' else 0.0,
                'candidate_strength': candidate_strength,
                'activation_status': status,
                'status_reasons': status_reasons,
                'condition_evidence': {
                    'middle_indices': middle_indices,
                    'adjacent_clashes': adjacent_clashes,
                    'adjacent_wing_clashes': adjacent_wing_clashes,
                },
                'is_continuous': is_continuous,
                'is_adjacent': is_adjacent
            })

            # 생지 또는 성지가 충으로 빠진 경우 중신과 남은 날개만 반합 후보로 남긴다.
            if (status == 'suppressed' and not adjacent_clashes and
                    len(adjacent_wing_clashes) == 1):
                clash = adjacent_wing_clashes[0]
                surviving_wing = b3 if clash['wing_role'] == 'birth' else b1
                if target_branch in (middle, surviving_wing):
                    partner = surviving_wing if target_branch == middle else middle
                    half_haps.extend(_half_hap_matches(
                        target_branch, target_index, partner, all_branches,
                        day_stem, element,
                        fallback_from={
                            'group_branches': [b1, b2, b3],
                            'clashed_branch': all_branches[clash['wing_index']],
                            'clashed_index': clash['wing_index'],
                            'clashing_index': clash['clashing_index'],
                            'reason': f"adjacent_{clash['wing_role']}_clash",
                        },
                    ))
            
        elif len(others_exist) == 1:
            # 중신을 포함한 두 지지만 반합으로 본다. 생지·성지는 공합 후보로 별도 탐지한다.
            third_branch = [b for b in (b1, b2, b3) if b != target_branch and b != others_exist[0]][0]
            if third_branch not in all_branches:
                half_haps.extend(_half_hap_matches(
                    target_branch, target_index, others_exist[0], all_branches,
                    day_stem, element, missing=third_branch))
    
    return three_haps, half_haps


def check_gong_hap(target_branch, target_index, all_branches, day_stem):
    """중신이 빠진 생지·성지의 공합 구조 후보를 위치별로 반환한다."""
    results = []
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        rule = (GONG_HAPS.get((target_branch, other_branch)) or
                GONG_HAPS.get((other_branch, target_branch)))
        if not rule or rule['missing'] in all_branches:
            continue
        results.append({
            'my': target_branch, 'my_index': target_index,
            'my_ten_star': get_ten_star_branch(day_stem, target_branch),
            'with': other_branch, 'with_index': i,
            'with_ten_star': get_ten_star_branch(day_stem, other_branch),
            'missing': rule['missing'], 'element': rule['element'],
            'is_adjacent': abs(i - target_index) == 1,
            'strength': None, 'activation_status': 'candidate_only',
        })
    return results


def check_hidden_stem_hap(target_branch, target_index, all_branches, day_stem):
    """지장간 천간합의 지정 조합을 위치별 후보로 반환한다."""
    results = []
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        pair = (target_branch, other_branch)
        stem_pairs = HIDDEN_STEM_HAPS.get(pair)
        if stem_pairs is None:
            stem_pairs = HIDDEN_STEM_HAPS.get(pair[::-1])
            if stem_pairs is None:
                continue
            stem_pairs = tuple((second, first) for first, second in stem_pairs)
        results.append({
            'my': target_branch, 'my_index': target_index,
            'my_ten_star': get_ten_star_branch(day_stem, target_branch),
            'with': other_branch, 'with_index': i,
            'with_ten_star': get_ten_star_branch(day_stem, other_branch),
            'hidden_stem_pairs': [
                {'my': first, 'with': second,
                 'combined_element_candidate': (STEM_COMBINATIONS.get((first, second)) or
                                                STEM_COMBINATIONS.get((second, first)))}
                for first, second in stem_pairs
            ],
            'is_adjacent': abs(i - target_index) == 1,
            'strength': None, 'activation_status': 'candidate_only',
        })
    return results


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
            participant_indices, formation_indices, with_branches = _group_members(
                (b1, b2, b3), target_index, all_branches, day_stem
            )
            
            results.append({
                'my': target_branch,
                'my_index': target_index,
                'my_ten_star': my_ten_star,
                'branches': [b1, b2, b3],          # 전체 방합 지지
                'participant_indices': participant_indices,
                'formation_indices': formation_indices,
                'with_branches': with_branches,    # 상대 두 지지 상세 정보
                'element': info['element'],
                'season': info['season'],
                'strength': strength,
                'is_adjacent': is_adjacent,
                'distance': distance
            })
    
    return results if results else None


def check_three_punishment(target_branch, target_index, all_branches, day_stem):
    """세 글자가 모두 있을 때만 삼형 구조 후보를 반환한다."""
    results = []
    for group_branches, kind in THREE_PUNISHMENTS.items():
        if target_branch not in group_branches or not set(group_branches).issubset(all_branches):
            continue
        positions, formations, others = _group_members(
            group_branches, target_index, all_branches, day_stem)
        results.append({
            'my': target_branch,
            'my_index': target_index,
            'my_ten_star': get_ten_star_branch(day_stem, target_branch),
            'branches': list(group_branches),
            'type': kind,
            'participant_indices': positions,
            'formation_indices': formations,
            'with_branches': others,
            'is_adjacent': any(indices[-1] - indices[0] == 2 for indices in formations),
        })
    return results


def check_punishment(target_branch, target_index, all_branches, day_stem):
    """쌍별 지세형과 자형 후보를 찾는다."""
    punishments = []
    my_ten_star = get_ten_star_branch(day_stem, target_branch)
    
    for i, other_branch in enumerate(all_branches):
        if i == target_index:
            continue
        
        distance = abs(i - target_index)
        strength = 1.0 if distance == 1 else (0.7 if distance == 2 else 0.5)
        is_adjacent = (distance == 1)

        # 지세형 (丑-戌, 戌-未). 丑未는 충으로만 판정한다.
        if (target_branch, other_branch) in PUNISHMENTS['지세형'] or (other_branch, target_branch) in PUNISHMENTS['지세형']:
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
        key = (p['with_index'], p['type'])
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
        'six_haps_all': check_six_haps(target_branch, target_index, all_branches, day_stem),
        'chungs': check_chung(target_branch, target_index, all_branches, day_stem),
        'cheons': check_cheon(target_branch, target_index, all_branches, day_stem),
        'breaks': check_break(target_branch, target_index, all_branches, day_stem),
        'three_haps': three_haps,
        'half_haps': half_haps,
        'gong_haps': check_gong_hap(target_branch, target_index, all_branches, day_stem),
        'hidden_stem_haps': check_hidden_stem_hap(target_branch, target_index, all_branches, day_stem),
        'square_haps': check_square_hap(target_branch, target_index, all_branches, day_stem),
        'three_punishments': check_three_punishment(target_branch, target_index, all_branches, day_stem),
        'punishments': check_punishment(target_branch, target_index, all_branches, day_stem)
    }
    
    return relations
