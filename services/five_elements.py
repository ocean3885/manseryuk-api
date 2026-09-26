from typing import List, Dict, Any

STEM_ELEMENT_MAP = {
    '甲': '목', '乙': '목',
    '丙': '화', '丁': '화',
    '戊': '토', '己': '토',
    '庚': '금', '辛': '금',
    '壬': '수', '癸': '수'
}

BRANCH_ELEMENT_MAP = {
    '寅': '목', '卯': '목',
    '巳': '화', '午': '화',
    '辰': '토', '戌': '토', '丑': '토', '未': '토',
    '申': '금', '酉': '금',
    '亥': '수', '子': '수'
}

def analyze_five_elements(stems: List[str], branches: List[str], tonggeun_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    오행(五行: 목, 화, 토, 금, 수) 분포 및 비율, 강도 점수, 과다/결핍 분석 엔진
    """
    counts = {'목': 0, '화': 0, '토': 0, '금': 0, '수': 0}
    scores = {'목': 0.0, '화': 0.0, '토': 0.0, '금': 0.0, '수': 0.0}

    # 1. 천간 4글자 오행 집계
    for i, s in enumerate(stems):
        elem = STEM_ELEMENT_MAP.get(s, '')
        if elem in counts:
            counts[elem] += 1
            # 통근 점수를 천간 오행 강도로 반영
            tg_score = tonggeun_results[i].get('점수', 1.0) if i < len(tonggeun_results) else 1.0
            scores[elem] += (1.0 + tg_score)

    # 2. 지지 4글자 오행 집계
    # 지지 가중치: 년(1.0), 월(2.0), 일(1.5), 시(1.0)
    pos_weights = [1.0, 2.0, 1.5, 1.0]
    for i, b in enumerate(branches):
        elem = BRANCH_ELEMENT_MAP.get(b, '')
        if elem in counts:
            counts[elem] += 1
            scores[elem] += pos_weights[i]

    # 3. 백분율(Percentages) 계산 (단순 개수 기준 8글자 100%)
    percentages = {elem: round((count / 8.0) * 100.0, 1) for elem, count in counts.items()}

    # 4. 점수 정규화 및 반올림
    scores = {elem: round(score, 1) for elem, score in scores.items()}

    # 5. 과다(Dominant) 및 결핍(Deficient) 판정
    dominant_list = [elem for elem, count in counts.items() if count >= 3 or percentages[elem] >= 35.0]
    deficient_list = [elem for elem, count in counts.items() if count == 0]

    dominant_str = ", ".join([f"{e}({counts[e]}개)" for e in dominant_list]) if dominant_list else "골고루 균형"
    deficient_str = ", ".join(deficient_list) if deficient_list else "없음 (모두 보유)"

    # 6. 설명 텍스트
    if dominant_list and deficient_list:
        summary_text = f"{dominant_str} 기운이 가장 우세하며, {deficient_str} 기운이 결핍되어 있어 오행의 보완이 필요합니다."
    elif dominant_list:
        summary_text = f"{dominant_str} 기운이 발달하여 주도적인 성향을 띱니다."
    elif deficient_list:
        summary_text = f"전반적으로 완만하나 {deficient_str} 기운이 부족하여 후천적 보완이 유리합니다."
    else:
        summary_text = "목화토금수 5개 오행이 사주에 골고루 갖추어진 원만한 오행구족(五行具足) 구조입니다."

    return {
        "counts": counts,
        "percentages": percentages,
        "scores": scores,
        "dominant": dominant_list,
        "deficient": deficient_list,
        "summary": summary_text
    }
