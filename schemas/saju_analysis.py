from pydantic import BaseModel
from typing import Optional, List, Any, Dict

# ──────────────────────────────────────────
# 사주 분석 응답용 중첩 스키마
# ──────────────────────────────────────────

class GanJi(BaseModel):
    """천간(干)과 지지(支)를 한글/한자 쌍으로 표현"""
    gan: dict  # {"kr": "갑", "ch": "甲"}
    ji: dict   # {"kr": "자", "ch": "子"}


class FourPillars(BaseModel):
    """사주 4주 (년주/월주/일주/시주)"""
    year: GanJi
    month: GanJi
    day: GanJi
    hour: GanJi


class TenGods(BaseModel):
    """십신 (천간 + 지지)"""
    year_gan: str
    year_ji: str
    month_gan: str
    month_ji: str
    day_gan: str = "일간"
    day_ji: str
    time_gan: str
    time_ji: str



class SolarDate(BaseModel):
    """양력 날짜"""
    year: int
    month: str
    day: str


class LunarDate(BaseModel):
    """음력 날짜"""
    year: int
    month: str
    day: str


class CalendarInfo(BaseModel):
    """달력 정보 (양력 / 음력 / 절기 메모)"""
    solar: SolarDate
    lunar: LunarDate
    solar_plan: Optional[str] = None
    lunar_plan: Optional[str] = None

class CurrentDaewoon(BaseModel):
    index: int
    year: int
    age: int

    gan: str
    ji: str
    gan_ten_god: Optional[str] = None
    ji_ten_god: Optional[str] = None
    unseong: Optional[str] = None

    start_age: float
    end_age: float

    start_year: int
    end_year: int


class DaewoonItem(BaseModel):
    index: int

    start_age: float
    end_age: float

    start_year: int
    end_year: int

    gan: str
    ji: str
    gan_ten_god: Optional[str] = None
    ji_ten_god: Optional[str] = None
    unseong: Optional[str] = None


class Daewoon(BaseModel):
    direction: str
    start_age: float

    current: Optional[CurrentDaewoon]

    list: List[DaewoonItem]



class CyclesInfo(BaseModel):
    """운세 사이클"""
    future_100: List[Any]  # 100년 운세
    baby_10: List[Any]     # 소운 10년


class MetaInfo(BaseModel):
    """기타 기본 정보"""
    gender: str
    ddi: Optional[str] = None  # 띠


class AnalysisSummary(BaseModel):
    """분석 요약 (합충 등)"""
    branch_interactions: List[str]
    stem_interactions: List[str]
    total_energy_balance: str


class AnalysisInfo(BaseModel):
    """최종 분석 결과 그룹"""
    summary: AnalysisSummary
    details: dict  # 개발 단계에서는 유연함을 위해 dict 사용


# ──────────────────────────────────────────
# 고급 명리학 AI 분석 스키마 (합충형해파, 허실, 빈주)
# ──────────────────────────────────────────

class InteractionItem(BaseModel):
    category: str
    type: str
    name: str
    from_pillar: str
    to_pillar: str
    is_adjacent: bool
    weight: float
    score: float
    transformed_element: Optional[str] = None
    description: str


class InteractionsInfo(BaseModel):
    summary_list: List[str]
    matrix: List[InteractionItem]
    tension_score: float
    harmony_score: float
    climate: str


class PillarXuShi(BaseModel):
    position: str
    char: str
    ten_star: str
    score: float
    original_status: str
    current_status: str
    is_transformed: bool
    reason: str
    meaning: str


class XuShiDynamics(BaseModel):
    pillars: dict
    real_count: int
    transformed_empty_count: int
    hollow_penetrate_count: int
    overall_status: str


class ControlFlow(BaseModel):
    direction: str
    summary_meaning: str
    career_advice: str


class BinZhuDynamics(BaseModel):
    guest_structure: dict
    host_structure: dict
    control_flow: ControlFlow
class FiveElementsInfo(BaseModel):
    counts: Dict[str, int]
    percentages: Dict[str, float]
    scores: Dict[str, float]
    dominant: List[str]
    deficient: List[str]
    summary: str


class SpecialStarItem(BaseModel):
    name: str
    pillar: str
    position: str
    char: str
    type: str
    description: str


class AdvancedAnalysis(BaseModel):
    five_elements: Optional[FiveElementsInfo] = None
    special_stars: Optional[List[SpecialStarItem]] = None
    interactions: InteractionsInfo
    xu_shi_dynamics: XuShiDynamics
    bin_zhu_dynamics: BinZhuDynamics
    ai_consultation_prompts: List[str]



class SajuAnalysisResponse(BaseModel):
    """사주 분석 최종 응답 (도메인별 그룹화)"""
    calendar: CalendarInfo
    four_pillars: FourPillars
    ten_gods: TenGods
    daewoon: Daewoon
    cycles: CyclesInfo
    meta: MetaInfo
    analysis: AnalysisInfo
    advanced_analysis: Optional[AdvancedAnalysis] = None

