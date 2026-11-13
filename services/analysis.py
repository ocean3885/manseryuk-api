from services.constants import ROOT_STRENGTH, UNSEONG_DATA, JIJANGGAN_DETAILED
from services.branch_relations import get_relations_for_branch
from services.calculator import get_ten_star_stem, get_ten_star_branch
from services.stem_relations import get_relations_for_stem
from services.relations import check_jahab
from services.ko_analysis import get_storehouse_info

def get_unseong(cheongan, jiji):
    return UNSEONG_DATA.get(cheongan, {}).get(jiji, "입력 오류")

def get_jijanggan(jiji_ch):
    return [item['char'] for item in JIJANGGAN_DETAILED.get(jiji_ch, [])]

def get_transmitted_info(branch, branch_idx, all_stems, day_stem):
    """투간된 지장간과 그렇지 않은 지장간을 분리하여 반환"""
    jijanggan_list = JIJANGGAN_DETAILED[branch]
    
    transmitted = []
    hidden = []
    
    for hidden_stem in jijanggan_list:
        stem = hidden_stem['char']
        pos_label = hidden_stem['type']
        ten_star = get_ten_star_stem(day_stem, stem)
        
        info = {
            'stem': stem,
            'stem_pos': pos_label,
            'stem_ten_star': ten_star
        }
        
        matching_indices = [i for i, visible_stem in enumerate(all_stems)
                            if visible_stem == stem]
        if matching_indices:
            for stem_idx in matching_indices:
                transmitted.append({
                    **info,
                    'stem_idx': stem_idx,
                    'from': branch,
                    'from_idx': branch_idx,
                    'from_ten_star': get_ten_star_branch(day_stem, branch),
                })
        else:
            hidden.append(info)
    
    return {
        'transmitted': transmitted,
        'hidden': hidden
    }

def analyze_advanced_tonggeun(cheongans, jijis, *, scope='same_pillar_only'):
    """동주 통근을 판정하고 타주 지지의 기존 가중 지원은 별도로 기록한다.

    all_four_branches_weighted는 기존 허실 v1 자료의 회귀 비교용이다.
    """
    if scope not in ('same_pillar_only', 'all_four_branches_weighted'):
        raise ValueError('지원하지 않는 통근 판정 범위입니다.')
    # 전주 회귀 계산과 타주 지원에만 적용하는 지지 위치별 가중치 (연, 월, 일, 시)
    pos_weights = [1.0, 2.0, 1.5, 1.0]
    
    # 2. 거리별 감쇠 비율 (차이 0, 1, 2, 3)
    dist_decay = [1.0, 0.5, 0.2, 0.1]

    positions = ['년', '월', '일', '시']
    results = []
    
    day_stem = cheongans[2]  # 일간 (십성 계산 기준)

    for i in range(4):  # 천간 위치 순회
        target_kan = cheongans[i]
        same_pillar_root_exists = ROOT_STRENGTH.get(target_kan, {}).get(jijis[i], 0) > 0
        total_score = 0
        root_details = []  # 이 천간의 통근 상세 정보
        external_score = 0.0
        external_details = []
        
        for j in range(4):  # 지지 위치 순회
            target_jiji = jijis[j]
            
            # 뿌리가 있는지 확인 (ROOT_STRENGTH는 미리 정의된 딕셔너리)
            base_power = ROOT_STRENGTH.get(target_kan, {}).get(target_jiji, 0)
            
            if base_power > 0:
                distance = abs(i - j)
                calc_score = (base_power if scope == 'same_pillar_only' and j == i
                              else base_power * pos_weights[j] * dist_decay[distance])
                
                main_stem = next(item['char'] for item in JIJANGGAN_DETAILED[target_jiji]
                                 if item['type'] == '정기')
                ten_star = get_ten_star_stem(day_stem, main_stem)
                
                detail = {
                    "branch_char": target_jiji,
                    "position": positions[j],
                    "ten_star": ten_star,
                    "score": round(calc_score, 2)
                }
                if j != i:
                    external_score += calc_score
                    external_details.append(detail)
                if scope == 'all_four_branches_weighted' or j == i:
                    total_score += calc_score
                    root_details.append(detail)
        
        if scope == 'same_pillar_only':
            status = '실(實)' if same_pillar_root_exists else '허투(虛透)'
        else:
            status = ('실(實)' if total_score >= 0.5 else
                      '허투(虛透)' if total_score == 0 else '허(虛)')
        
        results.append({
            "위치": positions[i],
            "글자": target_kan,
            "점수": round(total_score, 2),
            "상태": status,
            "통근정보": root_details,
            "통근범위": scope,
            "동주통근여부": same_pillar_root_exists,
            "타주지원점수": round(external_score, 2),
            "타주지원정보": external_details,
        })

    return results



def analyze_palja_integrated(stems, branches):
    """
    사주 8글자를 통합 분석하여 천간/지지의 상호작용이 반영된 결과를 리턴합니다.
    """
    day_stem = stems[2]
    tonggeun_results = analyze_advanced_tonggeun(stems, branches)
    
    pillar_keys = ['year', 'month', 'day', 'hour']
    
    pillars_data = {}
    for i, p in enumerate(pillar_keys):
        branch_char = branches[i]
        stem_char = stems[i]
        transmitted_info = get_transmitted_info(branch_char, i, stems, day_stem)
        branch_relations = get_relations_for_branch(branch_char, i, branches, stems)
        stem_relations = get_relations_for_stem(stem_char, i, branches, stems)
        chungs = branch_relations.get('chungs', [])
        punishments = branch_relations.get('punishments', [])
        
        jahab_info = check_jahab(stem_char, branch_char, i, chungs, punishments)
        
        pillars_data[p] = {
            "stem": {
                "char": stem_char,
                "position": tonggeun_results[i]['위치'],
                "score": tonggeun_results[i]['점수'],
                "root_info": tonggeun_results[i]['통근정보'],
                "status": tonggeun_results[i]['상태'],
                "unseong": get_unseong(stem_char, branch_char),
                "relations": stem_relations,
                "root_scope": tonggeun_results[i]['통근범위'],
                "same_pillar_root_exists": tonggeun_results[i]['동주통근여부'],
                "external_support_score": tonggeun_results[i]['타주지원점수'],
                "external_support_info": tonggeun_results[i]['타주지원정보'],
            },
            "branch": {
                "char": branch_char,
                "storehouse": get_storehouse_info(
                    branch_char, transmitted_info['transmitted'] + transmitted_info['hidden']),
                "jijanggan": get_jijanggan(branch_char),
                "transmitted": transmitted_info['transmitted'],
                "hidden": transmitted_info['hidden'],
                "relations": branch_relations
            },
            "jahab": jahab_info
        }

    return {
        "summary": _summarize_pillars(pillars_data),
        "pillars": pillars_data,
    }


def _summarize_pillars(pillars):
    """상세 원자료를 위치별 관계 하나당 한 줄로 요약한다. 판정·수치를 재계산하지 않는다."""
    keys = ('year', 'month', 'day', 'hour')
    names = ('년', '월', '일', '시')
    day_stem = pillars['day']['stem']['char']

    def member(index, kind):
        char = pillars[keys[index]][kind]['char']
        star = ('일간' if kind == 'stem' and index == 2 else
                get_ten_star_stem(day_stem, char) if kind == 'stem' else
                get_ten_star_branch(day_stem, char))
        return f"{names[index]}{'간' if kind == 'stem' else '지'} {char}({star})"

    def branch_label(bucket, item):
        if bucket == 'six_haps':
            return f"육합 조합({item['candidate_element']} 후보)"
        if bucket == 'three_haps':
            return f"삼합 조합({item['candidate_element']} 후보)"
        if bucket == 'square_haps':
            return f"방합 후보({item['season']}·{item['candidate_element']})"
        if bucket == 'half_haps':
            return f"반합 후보({item['candidate_element']}, {item['type'].split()[0]})"
        if bucket == 'gong_haps':
            return f"공합 후보({item['candidate_element']}, 중신 {item['missing']} 부재)"
        if bucket == 'hidden_stem_haps':
            return '지장간 암합 후보'
        if bucket == 'three_punishments':
            return f"삼형 구조({item['type']})"
        if bucket == 'punishments':
            return item['type'] + (' 후보' if item['activation_status'] == 'candidate_only' else ' 관계')
        return {'chungs': '충 관계', 'cheons': '천(穿) 관계', 'breaks': '파 관계'}[bucket]

    branch_rows, stem_rows = {}, {}
    for pillar in pillars.values():
        for bucket, items in pillar['branch']['relations'].items():
            for item in items:
                group = 'participant_indices' in item
                indices = (tuple(sorted(item['participant_indices'])) if group else
                           tuple(sorted((item['my_index'], item['with_index']))))
                identity = (indices, bucket, tuple(item.get('branches', [])))
                participants = ' · '.join(member(index, 'branch') for index in indices)
                suffix = f", 세 자리 조합 {len(item['formation_indices'])}개" if group else ''
                branch_rows[identity] = f'{participants}: {branch_label(bucket, item)}{suffix}'
        relations = pillar['stem']['relations']
        for bucket in ('combinations', 'conflict'):
            for item in relations[bucket]:
                indices = tuple(sorted((item['my_index'], item['with_index'])))
                label = (f"천간합 조합({item['candidate_element']} 후보)"
                         if bucket == 'combinations' else '천간충 관계')
                participants = ' · '.join(member(index, 'stem') for index in indices)
                stem_rows[(indices, bucket)] = f'{participants}: {label}'
        for bucket, items in relations['restrain'].items():
            for item in items:
                source, target = (item['my_index'], item['with_index'])
                if bucket == 'restrain_me':
                    source, target = target, source
                stem_rows[((source, target), 'restrain')] = (
                    f"{member(source, 'stem')} → {member(target, 'stem')}: 천간극 관계")
    rooted = sum(p['stem']['same_pillar_root_exists'] for p in pillars.values())
    return {
        'branch_interactions': [branch_rows[key] for key in sorted(branch_rows)],
        'stem_interactions': [stem_rows[key] for key in sorted(stem_rows)],
        'rooting_summary': (f'천간 동주 통근 {rooted}개·동주 무근 {len(keys) - rooted}개 '
                            '(원국 전체 신강·신약 미판정)'),
    }
