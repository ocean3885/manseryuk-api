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
    대표 오행의 글자 수·비율과 기존 잠정 가중 지표를 제공한다. 실제 세력·보완 필요성은 판정하지 않는다.
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

    # 5. 대표 오행의 다빈도(3글자 이상)·부재. 실제 세력과 보완 필요성이 아니다.
    frequent_list = [elem for elem, count in counts.items() if count >= 3]
    absent_list = [elem for elem, count in counts.items() if count == 0]

    # Report counts only: neither weighted power dominance nor advice is evaluated here.
    distribution = ', '.join(f'{element} {count}개' for element, count in counts.items())
    summary_text = f'원국 8글자의 대표 오행 분포는 {distribution}입니다. 비율은 글자 수 기준이며 실제 세력의 비율이 아닙니다.'

    return {
        "counts": counts,
        "percentages": percentages,
        "scores": scores,
        "frequent_elements": frequent_list,
        "absent_elements": absent_list,
        "summary": summary_text,
        "distribution_basis": "eight_visible_characters",
        "score_meaning": "provisional_weighted_index",
    }
