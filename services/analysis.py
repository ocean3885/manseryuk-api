from services.constants import ROOT_STRENGTH, UNSEONG_DATA, JIJANGGAN
from services.branch_relations import get_relations_for_branch
from services.constants import ZHI_ZANG
from services.calculator import get_ten_star_stem, get_ten_star_branch
from services.stem_relations import get_relations_for_stem
from services.relations import check_jahab

def get_unseong(cheongan, jiji):
    return UNSEONG_DATA.get(cheongan, {}).get(jiji, "입력 오류")

def get_jijanggan(jiji_ch):
    return JIJANGGAN.get(jiji_ch, [])

def get_transmitted_info(branch, branch_idx, all_stems, day_stem):
    """투간된 지장간과 그렇지 않은 지장간을 분리하여 반환"""
    jijanggan_list = ZHI_ZANG[branch]
    position_labels = ['본기', '중기', '말기']
    
    transmitted = []
    hidden = []
    
    for idx, stem in enumerate(jijanggan_list):
        pos_label = position_labels[idx] if idx < len(position_labels) else f'{idx+1}기'
        ten_star = get_ten_star_stem(day_stem, stem)
        
        info = {
            'stem': stem,
            'stem_pos': pos_label,
            'stem_ten_star': ten_star
        }
        
        if stem in all_stems:
            info['stem_idx'] = all_stems.index(stem)
            info['from'] = branch
            info['from_idx'] = branch_idx
            info['from_ten_star'] = get_ten_star_branch(day_stem, branch)
            transmitted.append(info)
        else:
            hidden.append(info)
    
    return {
        'transmitted': transmitted,
        'hidden': hidden
    }

def analyze_advanced_tonggeun(cheongans, jijis):
    # 1. 지지 위치별 가중치 (연, 월, 일, 시)
    pos_weights = [1.0, 2.0, 1.5, 1.0]
    
    # 2. 거리별 감쇠 비율 (차이 0, 1, 2, 3)
    dist_decay = [1.0, 0.5, 0.2, 0.1]

    positions = ['년', '월', '일', '시']
    results = []
    
    day_stem = cheongans[2]  # 일간 (십성 계산 기준)

    for i in range(4):  # 천간 위치 순회
        target_kan = cheongans[i]
        total_score = 0
        root_details = []  # 이 천간의 통근 상세 정보
        
        for j in range(4):  # 지지 위치 순회
            target_jiji = jijis[j]
            
            # 뿌리가 있는지 확인 (ROOT_STRENGTH는 미리 정의된 딕셔너리)
            base_power = ROOT_STRENGTH.get(target_kan, {}).get(target_jiji, 0)
            
            if base_power > 0:
                distance = abs(i - j)
                calc_score = base_power * pos_weights[j] * dist_decay[distance]
                total_score += calc_score
                
                main_stem = ZHI_ZANG[target_jiji][0]  # 본기
                ten_star = get_ten_star_stem(day_stem, main_stem)
                
                root_details.append({
                    "branch_char": target_jiji,
                    "position": positions[j],
                    "ten_star": ten_star,
                    "score": round(calc_score, 2)
                })
        
        # 맹파식 허실 판정 (임계점 0.5 기준)
        status = "실(實)" if total_score >= 0.5 else "허(虛)"
        
        results.append({
            "위치": positions[i],
            "글자": target_kan,
            "점수": round(total_score, 2),
            "상태": status,
            "통근정보": root_details   
        })

    return results



def analyze_palja_integrated(stems, branches):
    """
    사주 8글자를 통합 분석하여 천간/지지의 상호작용이 반영된 결과를 리턴합니다.
    """
    day_stem = stems[2]
    tonggeun_results = analyze_advanced_tonggeun(stems, branches)
    
    pillers = ['year', 'month', 'day', 'hour']
    position_names = ['년', '월', '일', '시']
    
    pillars_data = {}
    collected_branch_rels = []
    collected_stem_rels = []

    for i, p in enumerate(pillers):
        branch_char = branches[i]
        stem_char = stems[i]
        transmitted_info = get_transmitted_info(branch_char, i, stems, day_stem)
        branch_relations = get_relations_for_branch(branch_char, i, branches, stems)
        stem_relations = get_relations_for_stem(stem_char, i, branches, stems)
        chungs = branch_relations.get('chungs', [])
        punishments = branch_relations.get('punishments', [])
        
        # 지지 주요 형충회합 요약 추출
        for rel_key, rel_val in branch_relations.items():
            if rel_val and isinstance(rel_val, dict):
                target_char = rel_val.get('with', '')
                rel_type = rel_val.get('type', rel_key)
                collected_branch_rels.append(f"{position_names[i]}지 {rel_key}({target_char}, {rel_type})")
            elif rel_val and isinstance(rel_val, list):
                for item in rel_val:
                    if isinstance(item, dict):
                        target_char = item.get('with', '')
                        collected_branch_rels.append(f"{position_names[i]}지 {rel_key}({target_char})")

        # 천간 주요 관계 요약 추출
        for rel_key, rel_val in stem_relations.items():
            if rel_val and isinstance(rel_val, list):
                for item in rel_val:
                    if isinstance(item, dict):
                        target_char = item.get('with', '')
                        collected_stem_rels.append(f"{position_names[i]}간 {rel_key}({target_char})")

        jahab_info = check_jahab(stem_char, branch_char, i, chungs, punishments)
        
        pillars_data[p] = {
            "stem": {
                "char": stem_char,
                "position": tonggeun_results[i]['위치'],
                "score": tonggeun_results[i]['점수'],
                "root_info": tonggeun_results[i]['통근정보'],
                "status": tonggeun_results[i]['상태'],
                "unseong": get_unseong(stem_char, branch_char),
                "relations": stem_relations
            },
            "branch": {
                "char": branch_char,
                "jijanggan": get_jijanggan(branch_char),
                "transmitted": transmitted_info['transmitted'],
                "hidden": transmitted_info['hidden'],
                "relations": branch_relations
            },
            "jahab": jahab_info
        }

    # 전체 통근 점수/상태 바탕 세력 요약
    sil_count = sum(1 for t in tonggeun_results if t['상태'] == '실(實)')
    if sil_count >= 3:
        energy_balance = "신강(身強) 세력 우세"
    elif sil_count == 2:
        energy_balance = "중화(中和) 균형 기세"
    else:
        energy_balance = "신약(身弱) 세력 약화"

    return {
        "summary": {
            "branch_interactions": list(dict.fromkeys(collected_branch_rels)),
            "stem_interactions": list(dict.fromkeys(collected_stem_rels)),
            "total_energy_balance": energy_balance
        },
        "pillars": pillars_data
    }