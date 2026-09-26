from typing import List, Dict, Any
from services.branch_relations import (
    check_six_hap,
    check_three_hap,
    check_square_hap,
    check_chung,
    check_cheon,
    check_break,
    check_punishment
)
from services.stem_relations import (
    check_stem_combination,
    check_stem_conflict,
    check_stem_restrain
)

POSITION_NAMES = ['년', '월', '일', '시']
PILLAR_KEYS = ['year', 'month', 'day', 'hour']

def build_interaction_matrix(stems: List[str], branches: List[str], day_stem: str) -> Dict[str, Any]:
    """
    4개 기둥 간의 모든 천간/지지 상호작용(합, 충, 형, 해/천, 파, 극)을 분석하고
    상세 매트릭스, 요약 목록, 긴장도(Tension) 및 조화도(Harmony) 점수를 산출합니다.
    """
    matrix: List[Dict[str, Any]] = []
    summary_list: List[str] = []
    
    tension_score = 0.0
    harmony_score = 0.0

    # 거리별 가중치 (차이 1: 1.0, 차이 2: 0.7, 차이 3: 0.5)
    def get_dist_weight(dist: int) -> float:
        if dist == 1:
            return 1.0
        elif dist == 2:
            return 0.7
        return 0.5

    # 1. 지지 간 6개 페어 조합 분석 (년-월, 년-일, 년-시, 월-일, 월-시, 일-시)
    for i in range(4):
        for j in range(i + 1, 4):
            dist = j - i
            weight = get_dist_weight(dist)
            pos_from = PILLAR_KEYS[i]
            pos_to = PILLAR_KEYS[j]
            name_from = POSITION_NAMES[i]
            name_to = POSITION_NAMES[j]
            b1 = branches[i]
            b2 = branches[j]

            # (1) 육충 (沖)
            chungs = check_chung(b1, i, branches, day_stem)
            if chungs:
                for c in chungs:
                    if c.get('with_index') == j:
                        score = 2.0 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 육충: 기반 변동 및 마찰"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "충(沖)",
                            "name": f"{b1}{b2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

            # (2) 육합 (六合)
            six_hap = check_six_hap(b1, i, branches, day_stem)
            if six_hap and six_hap.get('with_index') == j:
                score = 1.5 * weight
                harmony_score += score
                desc = f"{name_from}지({b1})-{name_to}지({b2}) 육합({six_hap.get('element', '')}): 유대감 및 결합"
                summary_list.append(desc)
                matrix.append({
                    "category": "지지",
                    "type": "육합(六合)",
                    "name": f"{b1}{b2}합",
                    "from_pillar": pos_from,
                    "to_pillar": pos_to,
                    "is_adjacent": (dist == 1),
                    "weight": weight,
                    "score": score,
                    "transformed_element": six_hap.get('element'),
                    "description": desc
                })

            # (3) 천/해 (穿/害)
            cheons = check_cheon(b1, i, branches, day_stem)
            if cheons:
                for c in cheons:
                    if c.get('with_index') == j:
                        score = 1.5 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 육해(천): 암묵적 갈등 및 손상"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "해/천(穿/害)",
                            "name": f"{b1}{b2}천",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

            # (4) 형 (刑)
            punishments = check_punishment(b1, i, branches, day_stem)
            if punishments:
                for p in punishments:
                    if p.get('with_index') == j:
                        score = 1.5 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 형({p.get('type', '')}): 조정 및 압박"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "형(刑)",
                            "name": f"{p.get('type', '')}",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

            # (5) 파 (破)
            breaks = check_break(b1, i, branches, day_stem)
            if breaks:
                for b in breaks:
                    if b.get('with_index') == j:
                        score = 1.0 * weight
                        tension_score += score
                        desc = f"{name_from}지({b1})-{name_to}지({b2}) 파: 미세한 균열 및 파괴"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "지지",
                            "type": "파(破)",
                            "name": f"{b1}{b2}파",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

    # 2. 천간 간 조합 분석
    for i in range(4):
        for j in range(i + 1, 4):
            dist = j - i
            weight = get_dist_weight(dist)
            pos_from = PILLAR_KEYS[i]
            pos_to = PILLAR_KEYS[j]
            name_from = POSITION_NAMES[i]
            name_to = POSITION_NAMES[j]
            s1 = stems[i]
            s2 = stems[j]

            # 천간합 (五合)
            stem_haps = check_stem_combination(s1, i, stems, day_stem)
            if stem_haps:
                for h in stem_haps:
                    if h.get('with_index') == j:
                        score = 1.8 * weight
                        harmony_score += score
                        desc = f"{name_from}간({s1})-{name_to}간({s2}) 천간합({h.get('element', '')}): 유화 및 의기투합"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "천간",
                            "type": "천간합(天干合)",
                            "name": f"{s1}{s2}합",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "transformed_element": h.get('element'),
                            "description": desc
                        })

            # 천간충
            stem_conflicts = check_stem_conflict(s1, i, stems, day_stem)
            if stem_conflicts:
                for c in stem_conflicts:
                    if c.get('with_index') == j:
                        score = 1.5 * weight
                        tension_score += score
                        desc = f"{name_from}간({s1})-{name_to}간({s2}) 천간충: 직접적인 대립 및 표출"
                        summary_list.append(desc)
                        matrix.append({
                            "category": "천간",
                            "type": "천간충(天干沖)",
                            "name": f"{s1}{s2}충",
                            "from_pillar": pos_from,
                            "to_pillar": pos_to,
                            "is_adjacent": (dist == 1),
                            "weight": weight,
                            "score": score,
                            "description": desc
                        })

    # 삼합 / 방합 확인
    for i in range(4):
        three_haps, half_haps = check_three_hap(branches[i], i, branches, day_stem)
        for th in three_haps:
            desc = f"지지 삼합({th.get('element', '')}): 강력한 국(局) 형성"
            if desc not in summary_list:
                summary_list.append(desc)
                harmony_score += 3.0

        square_haps = check_square_hap(branches[i], i, branches, day_stem)
        if square_haps and isinstance(square_haps, list):
            for sq in square_haps:
                desc = f"지지 방합({sq.get('element', '')}): 강력한 방위 계절 세력 형성"
                if desc not in summary_list:
                    summary_list.append(desc)
                    harmony_score += 3.5


    return {
        "summary_list": list(dict.fromkeys(summary_list)),
        "matrix": matrix,
        "tension_score": round(tension_score, 1),
        "harmony_score": round(harmony_score, 1),
        "climate": "격렬한 변동과 도전형" if tension_score > harmony_score + 2 else (
            "유화적이고 안정적인 조화형" if harmony_score > tension_score + 2 else "긴장과 조화가 공존하는 복합형"
        )
    }
