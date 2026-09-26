from typing import List, Dict, Any
from services.calculator import get_ten_star_stem, get_ten_star_branch

PILLAR_KEYS = ['year', 'month', 'day', 'hour']
POSITION_NAMES = ['년', '월', '일', '시']

def analyze_bin_zhu_dynamics(
    stems: List[str],
    branches: List[str],
    day_stem: str,
    interaction_matrix: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    맹파명리 빈주(賓主: 손님과 주인) 분석 엔진:
    - 주(主: 주인/나의 영역) = 일주(2) + 시주(3)
    - 빈(賓: 손님/사회 영역) = 년주(0) + 월주(1)
    
    주와 빈 사이의 상호작용 통로(합, 충, 극)를 추적하여 재관의 취용(내 것으로 만듦) 여부와
    사회적 성취 경로를 판정합니다.
    """
    # 1. 십성 매핑
    stem_ten_gods = [
        "일간(본인)" if i == 2 else get_ten_star_stem(day_stem, stems[i])
        for i in range(4)
    ]
    branch_ten_gods = [
        get_ten_star_branch(day_stem, branches[i])
        for i in range(4)
    ]

    # 주(Host) & 빈(Guest) 구성 분석
    guest_elements = {
        "year": {"stem": f"{stems[0]}({stem_ten_gods[0]})", "branch": f"{branches[0]}({branch_ten_gods[0]})"},
        "month": {"stem": f"{stems[1]}({stem_ten_gods[1]})", "branch": f"{branches[1]}({branch_ten_gods[1]})"}
    }
    host_elements = {
        "day": {"stem": f"{stems[2]}({stem_ten_gods[2]})", "branch": f"{branches[2]}({branch_ten_gods[2]})"},
        "hour": {"stem": f"{stems[3]}({stem_ten_gods[3]})", "branch": f"{branches[3]}({branch_ten_gods[3]})"}
    }

    # 2. 빈-주 간 연결 통로(Interactions between Host and Guest) 분석
    # Guest indices: {0, 1}, Host indices: {2, 3}
    guest_host_links = []
    host_takes_guest_score = 0
    guest_pressures_host_score = 0

    for item in interaction_matrix:
        from_idx = PILLAR_KEYS.index(item['from_pillar'])
        to_idx = PILLAR_KEYS.index(item['to_pillar'])

        # 한쪽은 빈(0, 1)이고 다른 쪽은 주(2, 3)인 경우 탐색
        is_guest_from = from_idx in [0, 1]
        is_host_from = from_idx in [2, 3]
        is_guest_to = to_idx in [0, 1]
        is_host_to = to_idx in [2, 3]

        if (is_guest_from and is_host_to) or (is_host_from and is_guest_to):
            g_idx = from_idx if is_guest_from else to_idx
            h_idx = to_idx if is_guest_from else from_idx
            
            g_pos = POSITION_NAMES[g_idx]
            h_pos = POSITION_NAMES[h_idx]
            g_char = branches[g_idx] if item['category'] == '지지' else stems[g_idx]
            h_char = branches[h_idx] if item['category'] == '지지' else stems[h_idx]
            g_tg = branch_ten_gods[g_idx] if item['category'] == '지지' else stem_ten_gods[g_idx]
            h_tg = branch_ten_gods[h_idx] if item['category'] == '지지' else stem_ten_gods[h_idx]

            rel_type = item.get('type')
            
            # (1) 합(合) 관계: 주(Host)가 빈(Guest)의 재/관을 취함
            if '합' in rel_type:
                host_takes_guest_score += 2
                desc = f"주({h_pos} {h_tg})가 빈({g_pos} {g_tg})과 {rel_type}하여 사회적 자원/관계를 내 영역으로 견인함"
                guest_host_links.append({
                    "type": "합(취용)",
                    "detail": desc,
                    "target_guest": f"{g_pos}({g_tg})",
                    "source_host": f"{h_pos}({h_tg})"
                })
            # (2) 충(沖) / 천(穿) 관계: 주와 빈의 대립 및 변동
            elif '충' in rel_type or '해' in rel_type or '천' in rel_type:
                guest_pressures_host_score += 1.5
                desc = f"빈({g_pos} {g_tg})과 주({h_pos} {h_tg}) 간의 {rel_type}으로 인한 외부 환경과의 마찰 및 이동수"
                guest_host_links.append({
                    "type": "충/해(마찰)",
                    "detail": desc,
                    "target_guest": f"{g_pos}({g_tg})",
                    "source_host": f"{h_pos}({h_tg})"
                })

    # 3. 빈주 제어 방향성(Control Flow) 판정
    if host_takes_guest_score > guest_pressures_host_score:
        direction = "주 ➔ 빈 (주통빈/자원취용형)"
        summary_meaning = "자신의 역량과 수단(일/시주)으로 사회와 시장(년/월주)의 기회와 자원을 적극적으로 내 것으로 만드는 구조입니다."
        career_advice = "전문성이나 독자적인 수단을 무기로 독립 사업, 전문직, 성과형 프로젝트에서 큰 성취를 이룰 수 있습니다."
    elif guest_pressures_host_score > host_takes_guest_score:
        direction = "빈 ➔ 주 (빈통주/환경적응형)"
        summary_meaning = "외부 사회 조직이나 국가적 규율(년/월주)의 흐름에 맞춰 협력하고 적응하는 과정에서 성장하는 구조입니다."
        career_advice = "탄탄한 공공기관, 대기업, 대형 플랫폼 등 안정적인 시스템의 우산 아래에서 역량을 펼치는 것이 안전합니다."
    else:
        direction = "주-빈 균형 교류형"
        summary_meaning = "개인의 자율성과 사회적 네트워크가 상호 보완적으로 작동하는 구조입니다."
        career_advice = "파트너십, 협업, 유연한 프리랜서/조직 겸업 형태에서 최적의 시너지를 낼 수 있습니다."

    # 4. AI 상담 프롬프트 전용 핵심 가이드 생성
    ai_prompt_bullets = [
        f"【빈주 이론】 {direction}: {summary_meaning}",
        f"【진로/재물 권장】 {career_advice}"
    ]
    for link in guest_host_links[:2]:
        ai_prompt_bullets.append(f"【주-빈 통로】 {link['detail']}")

    return {
        "guest_structure": {
            "scope": "년주(국가/원거리시장) + 월주(직장/사회환경)",
            "elements": guest_elements
        },
        "host_structure": {
            "scope": "일주(나/배우자) + 시주(수단/소유처/말년)",
            "elements": host_elements
        },
        "control_flow": {
            "direction": direction,
            "summary_meaning": summary_meaning,
            "career_advice": career_advice
        },
        "guest_host_links": guest_host_links,
        "ai_prompt_bullets": ai_prompt_bullets
    }
