from services.constants import ROOT_STRENGTH, UNSEONG_DATA, JIJANGGAN
from services.relations import get_relations_for_branch
from services.constants import ZHI_ZANG
from services.calculator import get_ten_star_stem

def get_unseong(cheongan, jiji):
    return UNSEONG_DATA.get(cheongan, {}).get(jiji, "입력 오류")

def get_jijanggan(jiji_ch):
    return JIJANGGAN.get(jiji_ch, [])

def get_transmitted_info(branch, all_stems, day_stem):
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
            'position': pos_label,
            'ten_star': ten_star
        }
        
        if stem in all_stems:
            info['index'] = all_stems.index(stem)
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

    positions = ['연간', '월간', '일간', '시간']
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
                    "지지글자": target_jiji,
                    "위치": positions[j],
                    "십성": ten_star,
                    "기여점수": round(calc_score, 2)
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
    # 1. 내부 세부 로직 함수들 (별도 파일에서 import 했다고 가정)
    def _get_branch_relations(brs):
        # 예: [['연지-월지', '충'], ['월지-일지', '합']] 등 반환
        return ["월지-일지 육합", "연지-시지 충"] 

    def _get_stem_relations(sts):
        # 예: [['연간-월간', '합']] 등 반환
        return ["연간-월간 합화목"]

    # 2. 핵심 분석 실행
    branch_rels = _get_branch_relations(branches)
    stem_rels = _get_stem_relations(stems)
    
    # 앞서 만든 정밀 통근 점수 계산 (지지의 합충 결과가 가중치로 반영되게 설계 가능)
    tonggeun_results = analyze_advanced_tonggeun(stems, branches)
    
    # 3. 데이터 통합 조립
    pillers = ['year', 'month', 'day', 'hour']
    result_data = {
        "summary": {
            "branch_interactions": branch_rels,
            "stem_interactions": stem_rels,
            "total_energy_balance": "목화통명(木火通明) 기세"
        },
        "pillars": {}
    }

    for i, p in enumerate(pillers):
        branch_char = branches[i]
        transmitted_info = get_transmitted_info(branch_char, stems, day_stem)
        
        result_data["pillars"][p] = {
            "stem": {
                "char": stems[i],
                "position": tonggeun_results[i]['위치'],
                "score": tonggeun_results[i]['점수'],
                "root_info": tonggeun_results[i]['통근정보'],
                "status": tonggeun_results[i]['상태'],
                "unseong": get_unseong(stems[i], branch_char)
            },
            "branch": {
                "char": branch_char,
                "jijanggan": get_jijanggan(branch_char),
                "transmitted": transmitted_info['transmitted'],
                "hidden": transmitted_info['hidden'],
                "relations": get_relations_for_branch(branch_char, i, branches, stems)
            }
        }

    return result_data