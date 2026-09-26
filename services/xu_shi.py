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

    # 지지 중 충(沖)이나 천(穿)을 맞은 지지 인덱스 수집
    for item in interaction_matrix:
        if item.get('category') == '지지' and item.get('type') in ['충(沖)', '해/천(穿/害)']:
            from_idx = PILLAR_KEYS.index(item['from_pillar'])
            to_idx = PILLAR_KEYS.index(item['to_pillar'])
            clashed_branch_indices.add(from_idx)
            clashed_branch_indices.add(to_idx)

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

        # 3. 충/천에 의한 상태 변화(실자변허) 추적
        current_status = original_status
        reason = "뿌리가 지지에 온전하게 보존됨"
        is_transformed = False

        if original_status == "실(實)":
            # 이 천간이 뿌리를 내린 지지들 중 충/천을 맞은 지지가 있는지 확인
            damaged_roots = []
            for r in root_info:
                branch_pos_name = r.get('position')
                if branch_pos_name in POSITION_NAMES:
                    b_idx = POSITION_NAMES.index(branch_pos_name)
                    if b_idx in clashed_branch_indices:
                        damaged_roots.append(f"{branch_pos_name}지({r.get('branch_char')})")

            if damaged_roots:
                current_status = "변허(變虛)"
                is_transformed = True
                reason = f"통근처인 {', '.join(damaged_roots)}가 충·해를 받아 뿌리 손상(실자변허)"
                transformed_empty_count += 1
            else:
                real_count += 1
        elif original_status == "허투(虛透)":
            reason = "지지에 근(뿌리)이 전혀 없어 가볍고 유연하게 천간으로 표출됨"
            hollow_penetrate_count += 1
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

    # 전체 허실 총평 도출
    if transformed_empty_count > 0:
        overall_status = f"충·해로 인해 {transformed_empty_count}개 글자가 실자변허(實者變虛) 상태로 전이되어, 실물 고정 자산보다 유동적/지식 기반 대처가 유리합니다."
    elif real_count >= 3:
        overall_status = "천간의 뿌리가 전반적으로 튼튼한 실(實)한 사주로 현실적 실행력과 기반이 탄탄합니다."
    elif hollow_penetrate_count >= 2:
        overall_status = "허투(虛透)된 글자가 많아 지식, 기획, 아이디어, 명예, 쇼맨십 등 무형의 가치 창출에 탁월합니다."
    else:
        overall_status = "허와 실이 적절히 조화를 이루어 상황에 따른 유연한 대처 능력을 갖추고 있습니다."

    return {
        "pillars": pillars_xu_shi,
        "real_count": real_count,
        "transformed_empty_count": transformed_empty_count,
        "hollow_penetrate_count": hollow_penetrate_count,
        "overall_status": overall_status
    }

def _generate_xu_shi_meaning(ten_star: str, original: str, current: str, pos: str) -> str:
    if "일간" in ten_star:
        if current == "변허(變虛)":
            return "자신의 신체/자존심 뿌리가 흔들릴 수 있어 무리한 독단적 결정 경계"
        elif current == "실(實)":
            return "확고한 자아와 주체성을 바탕으로 환경을 주도함"
        else:
            return "유연하고 적응력이 뛰어나며 타인과의 협력에 능함"

    if "재" in ten_star:  # 편재, 정재
        if current == "변허(變虛)":
            return "재물의 현실적 기반이 흔들릴 수 있으므로 현물 투자나 보증을 피하고 안전 자산 확보 필요"
        elif current == "허투(虛透)":
            return "재성이 허투하여 현실 장사보다 기획, 브랜드, 아이디어, 마케팅 재물운에 최적화"
        elif current == "실(實)":
            return "재물의 뿌리가 튼튼하여 안정적인 현금 흐름과 실물 자산 축적에 유리"
        else:
            return "재물의 유동성이 커서 체계적인 재정 관리가 중요"

    if "관" in ten_star:  # 편관, 정관
        if current == "변허(變虛)":
            return "직책이나 조직 내 자리에 변동수가 따르므로 유연한 직무 전환 및 전문성 확보 권장"
        elif current == "허투(虛透)":
            return "관성이 허투하여 감투, 명예, 유명세, 대외적 브랜드 가치로 발현"
        elif current == "실(實)":
            return "조직의 신임과 실권이 확고하여 책임감 있는 리더십 발휘"
        else:
            return "틀에 얽매이지 않는 자유로운 직업 환경 추구"

    if "식" in ten_star or "상" in ten_star:  # 식신, 상관
        if current == "변허(變虛)":
            return "아이디어나 활동력에 굴곡이 올 수 있어 단계별 실행 점검 필요"
        elif current == "허투(虛透)":
            return "말, 교육, 예술, 기획, 방송 등 언어적·표현적 재능이 빛을 발함"
        elif current == "실(實)":
            return "손재주, 전문 기술, 생산 기반이 강력하여 꾸준한 성과 창출"
        else:
            return "다재다능하나 한 우물을 파는 집중력이 요구됨"

    if "인" in ten_star:  # 편인, 정인
        if current == "변허(變虛)":
            return "계약이나 문서의 변동성이 있으므로 법적 문서 검토에 주의 요망"
        elif current == "허투(虛透)":
            return "학문, 통찰력, 영감, 정신적 가치 탐구에 탁월함"
        elif current == "실(實)":
            return "학위, 자격증, 부동산 등 공인된 실체적 권리 확보에 유리"
        else:
            return "창의적 사고와 새로운 배움에 열려 있음"

    return "형세에 따른 유연한 환경 적응력 발휘"
