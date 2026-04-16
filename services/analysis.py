from services.constants import ROOT_STRENGTH, UNSEONG_DATA, JIJANGGAN
from services.relations import get_relations_for_branch

def get_unseong(cheongan, jiji):
    return UNSEONG_DATA.get(cheongan, {}).get(jiji, "입력 오류")

def get_jijanggan(jiji_ch):
    return JIJANGGAN.get(jiji_ch, [])


def analyze_advanced_tonggeun(cheongans, jijis):
    # 1. 지지 위치별 가중치 (연, 월, 일, 시)
    pos_weights = [1.0, 2.0, 1.5, 1.0]
    
    # 2. 거리별 감쇠 비율 (차이 0, 1, 2, 3)
    dist_decay = [1.0, 0.5, 0.2, 0.1]

    positions = ['연간', '월간', '일간', '시간']
    results = []

    for i in range(4):  # 천간 위치 순회
        target_kan = cheongans[i]
        total_score = 0
        
        for j in range(4):  # 지지 위치 순회
            target_jiji = jijis[j]
            
            # 뿌리가 있는지 확인
            base_power = ROOT_STRENGTH.get(target_kan, {}).get(target_jiji, 0)
            
            if base_power > 0:
                distance = abs(i - j)
                # 최종 점수 = 기본강도 * 지지가중치 * 거리감쇠
                calc_score = base_power * pos_weights[j] * dist_decay[distance]
                total_score += calc_score
        
        # 맹파식 허실 판정 (임계점 0.5 기준)
        status = "실(實)" if total_score >= 0.5 else "허(虛)"
        
        results.append({
            "위치": positions[i],
            "글자": target_kan,
            "점수": round(total_score, 2),
            "상태": status
        })

    return results



def analyze_palja_integrated(stems, branches):
    """
    사주 8글자를 통합 분석하여 천간/지지의 상호작용이 반영된 결과를 리턴합니다.
    """
    
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
        
        result_data["pillars"][p] = {
            "stem": {
                "char": stems[i],
                "score": tonggeun_results[i]['점수'],
                "status": tonggeun_results[i]['상태'],
                "unseong": get_unseong(stems[i], branch_char)
            },
            "branch": {
                "char": branch_char,
                "jijanggan": get_jijanggan(branch_char),
                "relations": get_relations_for_branch(branch_char, i, branches)
            }
        }

    return result_data