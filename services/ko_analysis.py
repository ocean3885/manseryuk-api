"""辰戌丑未의 기본 고 분류. 기존 지장간 십성을 재사용한다."""
from services.constants import STEM_INFO

# 기존 KO_INFO의 네 저장 오행을 유지한다. 지지 본기의 오행과 구별한다.
STORED_ELEMENTS = {'辰': '水', '戌': '火', '丑': '金', '未': '木'}
ROLE_BY_TEN_STAR = {
    '비견': '비겁고', '겁재': '비겁고',
    '식신': '식상고', '상관': '식상고',
    '편재': '재고', '정재': '재고',
    '편관': '관성고', '정관': '관성고',
    '편인': '인성고', '정인': '인성고',
}


def get_storehouse_info(branch: str, hidden_stem_details: list[dict]) -> dict | None:
    """투간·미투간 목록에 이미 계산된 일간 기준 십성으로 고의 역할을 분류한다.

    같은 지장간이 여러 천간 위치로 투출돼도 하나의 역할로 분류한다.
    고의 크기·개고·폐고·입고 여부와 실제 지장간 작용은 판정하지 않는다.
    """
    element = STORED_ELEMENTS.get(branch)
    if element is None:
        return None
    roles = {ROLE_BY_TEN_STAR[item['stem_ten_star']]
             for item in hidden_stem_details
             if STEM_INFO[item['stem']]['element_ch'] == element}
    if len(roles) != 1:
        raise ValueError(f'{branch}: 저장 오행의 지장간 십성 정보가 없거나 일치하지 않습니다.')
    return {'stored_element': element, 'role': roles.pop()}
