from typing import List, Dict, Any
from services.calculator import get_ten_star_stem

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']

def analyze_xu_shi_dynamics(
    stems: List[str],
    branches: List[str],
    day_stem: str,
    tonggeun_results: List[Dict[str, Any]],
    interaction_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    맹파명리 허실(虛實) 동적 분석 엔진:
    각 천간의 기본 통근 상태(실/허/허투)를 분석하고, 지지의 충·형·해(천)에 의한 
    실자변허(實者變虛) 상태 전이 및 십성별 물상적 의미를 도출합니다.
    """
    pillars_xu_shi: Dict[str, Any] = {}
    clashed_branch_indices = set()

    # 지지 중 충(沖), 천/해(穿/害), 형(刑)을 맞은 지지 인덱스 안전 수집
    for item in interaction_matrix:
        if item.get('category') == '지지' and item.get('type') in ['충(沖)', '해/천(穿/害)', '형(刑)']:
            from_p = item.get('from_pillar')
            to_p = item.get('to_pillar')
            if from_p in PILLAR_KEYS and to_p in PILLAR_KEYS:
                clashed_branch_indices.add(PILLAR_KEYS.index(from_p))
                clashed_branch_indices.add(PILLAR_KEYS.index(to_p))

    real_count = 0
    transformed_empty_count = 0
    hollow_penetrate_count = 0

    for i in range(4):
        p_key = PILLAR_KEYS[i]
        pos_name = POSITION_NAMES[i]
        stem_char = stems[i]
        tg = tonggeun_results[i]
        base_score = tg.get('점수', 0)
        root_info = tg.get('통근정보', [])
        
        # 1. 십성 파악
        ten_star = "일간(본인)" if i == 2 else get_ten_star_stem(day_stem, stem_char)

        # 2. 원래 허실 상태 판정
        if base_score >= 0.5:
            original_status = "실(實)"
        elif base_score == 0:
            original_status = "허투(虛透)"
        else:
            original_status = "허(虛)"

        # 3. 충/형/천에 의한 상태 변화(실자변허) 추적 (잔여 통근 점수 반영)
        current_status = original_status
        reason = "뿌리가 지지에 온전하게 보존됨"
        is_transformed = False

        damaged_roots = []
        intact_roots = []
        damaged_score = 0.0
        intact_score = 0.0

        for r in root_info:
            branch_pos_name = r.get('position')
            r_score = r.get('score', 0.0)
            if branch_pos_name in POSITION_NAMES:
                b_idx = POSITION_NAMES.index(branch_pos_name)
                if b_idx in clashed_branch_indices:
                    damaged_roots.append(f"{branch_pos_name}지({r.get('branch_char')})")
                    damaged_score += r_score
                else:
                    intact_roots.append(f"{branch_pos_name}지({r.get('branch_char')})")
                    intact_score += r_score

        if original_status == "실(實)":
            if damaged_roots:
                # 손상 후 잔여 점수가 기준치(0.5) 미만이면 실자변허, 여전히 0.5 이상이면 실 유지
                if intact_score < 0.5:
                    current_status = "변허(變虛)"
                    is_transformed = True
                    reason = f"주요 통근처인 {', '.join(damaged_roots)}가 충·형·해로 손상되어 뿌리 약화(실자변허)"
                    transformed_empty_count += 1
                else:
                    current_status = "실(實)"
                    is_transformed = False
                    reason = f"일부 통근처({', '.join(damaged_roots)})가 충·형·해를 입었으나 {', '.join(intact_roots)}의 근(점수 {round(intact_score, 2)})이 건재하여 실(實) 유지"
                    real_count += 1
            else:
                real_count += 1
        elif original_status == "허투(虛透)":
            reason = "지지에 근(뿌리)이 전혀 없어 가볍고 유연하게 천간으로 표출됨"
            hollow_penetrate_count += 1
        else:
            # 원래 허(虛)인 경우
            if damaged_roots:
                reason = f"지지의 미약한 통근처({', '.join(damaged_roots)})마저 충·형·해를 받아 기반이 더욱 불안정함"
            else:
                reason = "지지의 근이 미약하여 주변 세력에 쉽게 동조함"

        # 4. 십성 및 허실 결합 물상적 의미 도출
        meaning = _generate_xu_shi_meaning(ten_star, original_status, current_status, pos_name)

        pillars_xu_shi[p_key] = {
            "position": f"{pos_name}간",
            "char": stem_char,
            "ten_star": ten_star,
            "score": base_score,
            "original_status": original_status,
            "current_status": current_status,
            "is_transformed": is_transformed,
            "reason": reason,
            "meaning": meaning
        }

    # 전체 허실 상태 요약 (과도한 인생 단정 배제, 명리학적 팩트 프로필 구성)
    status_parts = []
    if real_count > 0:
        status_parts.append(f"실(實) {real_count}개")
    if transformed_empty_count > 0:
        status_parts.append(f"실자변허(變虛) {transformed_empty_count}개")
    if hollow_penetrate_count > 0:
        status_parts.append(f"허투(虛透) {hollow_penetrate_count}개")
    
    weak_count = 4 - (real_count + transformed_empty_count + hollow_penetrate_count)
    if weak_count > 0:
        status_parts.append(f"허(虛) {weak_count}개")

    counts_summary = ", ".join(status_parts)

    if transformed_empty_count >= 2:
        overall_status = f"천간 4자 중 {counts_summary}로, 지지 충·형·해에 의한 실자변허가 두드러져 고정된 환경보다 유동적 환경에서의 전환 적응력이 강점으로 작용합니다."
    elif transformed_empty_count == 1:
        if real_count >= 2:
            overall_status = f"천간 4자 중 {counts_summary}로, 실체적 실행 기반이 중심을 잡고 있으며 국소적 변허 글자를 통해 유연한 전략 수정 능력이 함께 발휘됩니다."
        else:
            overall_status = f"천간 4자 중 {counts_summary}로, 유연한 지식·기획적 기운을 바탕으로 상황 변화에 기민하게 대처하는 동적 구조입니다."
    elif real_count >= 3:
        overall_status = f"천간 4자 중 {counts_summary}로, 천간의 뿌리가 전반적으로 견고하여 실무 추진력과 실체적 기반이 확고하게 유지되는 구조입니다."
    elif hollow_penetrate_count >= 2:
        overall_status = f"천간 4자 중 {counts_summary}로, 허투된 기운이 주도하여 지식, 기획, 아이디어, 브랜드, 명예 등 무형 가치 창출에 최적화된 구조입니다."
    else:
        overall_status = f"천간 4자 중 {counts_summary}로, 실체적 기반(실)과 유연한 기획력(허)이 조화를 이루는 균형 잡힌 구조입니다."

    return {
        "pillars": pillars_xu_shi,
        "real_count": real_count,
        "transformed_empty_count": transformed_empty_count,
        "hollow_penetrate_count": hollow_penetrate_count,
        "overall_status": overall_status
    }

def _generate_xu_shi_meaning(ten_star: str, original: str, current: str, pos: str) -> str:
    """
    각 천간 십성의 허실 상태별 객관적 물상(物象) 및 에너지 발현 특성을 반환합니다.
    (단정적 길흉이나 섣부른 조언을 배제하고, LLM 및 프론트엔드가 활용할 수 있는 핵심 물상 팩트 제공)
    """
    if "일간" in ten_star:
        if current == "변허(變虛)":
            return "상황 변화에 맞춘 전략적 유연성과 신속한 처세 감각"
        elif current == "실(實)":
            return "확고한 자아 주체성과 환경에 대한 자립적 주도력"
        else:
            return "부드러운 친화력과 타인과의 원활한 협력·소통 능력"

    if "비" in ten_star or "겁" in ten_star:  # 비견, 겁재
        if current == "변허(變虛)":
            return "고정된 동업보다 독립적 역할 분담 기반의 유연한 파트너십에 적합"
        elif current == "허투(虛透)":
            return "폭넓은 대인 인맥 네트워크, 친화력 및 대외적 교류·협력에 최적화"
        elif current == "실(實)":
            return "독립적 자립심, 추진력 및 실질적인 동료·팀워크 기반 확보"
        else:
            return "주변 인연과의 관계에서 유연한 소통과 조율 감각"

    if "재" in ten_star:  # 편재, 정재
        if current == "변허(變虛)":
            return "고정 자산의 고착화보다 유동 자금 운용 및 유연한 수익 모델에 적합"
        elif current == "허투(虛透)":
            return "기획, 마케팅, 브랜드, 플랫폼 등 무형의 부가가치를 통한 재물 창출"
        elif current == "실(實)":
            return "실물 자산, 안정적인 현금 흐름 및 실체적 비즈니스 기반 운용"
        else:
            return "환경 변화에 유연하게 대응하는 유동적 재정 운용 감각"

    if "관" in ten_star:  # 편관, 정관
        if current == "변허(變虛)":
            return "경직된 조직 규율보다 전문직, 프로젝트 TF, 유연한 직무 환경에서 강점 발휘"
        elif current == "허투(虛透)":
            return "대외적 명예, 유명세, 브랜드 가치, 감투 및 전문 자문 역할로 발현"
        elif current == "실(實)":
            return "조직 내 실권, 관리자 리더십 및 확고한 직무 권한 발휘"
        else:
            return "틀에 얽매이지 않는 자유롭고 유연한 직업 환경 지향"

    if "식" in ten_star or "상" in ten_star:  # 식신, 상관
        if current == "변허(變虛)":
            return "정형화된 방식보다 트렌드에 민감한 창의적 기획 및 신속한 직무 전환"
        elif current == "허투(虛透)":
            return "언어, 교육, 예술, 기획, 미디어 등 무형의 표현·아이디어 창출에 탁월"
        elif current == "실(實)":
            return "제조, 생산, 기술력, 실제적 손재주 및 구체적 실무 실행력"
        else:
            return "다방면의 호기심과 유연한 재능 표출력"

    if "인" in ten_star:  # 편인, 정인
        if current == "변허(變虛)":
            return "기존 지식에 안주하지 않는 실용적 지식 갱신 및 창의적 응용 능력"
        elif current == "허투(虛透)":
            return "학문적 영감, 통찰력, 정신적 가치 및 기획·학술 탐구에 최적화"
        elif current == "실(實)":
            return "공인 자격증, 학위, 문서, 지적재산권 등 실체적 권리 확보에 유리"
        else:
            return "창의적 사고와 새로운 학문에 대한 유연한 수용성"

    return "형세에 따른 유연한 환경 적응 및 조율 능력"
