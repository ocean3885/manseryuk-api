from pydantic import BaseModel
from typing import Optional, List, Any, Dict

# ──────────────────────────────────────────
# 사주 분석 응답용 중첩 스키마 (프론트엔드 최적화)
# ──────────────────────────────────────────

class StemDetail(BaseModel):
    """천간(干) 상세 정보 (한글/한자, 오행, 음양, 색상, 십신)"""
    kr: str
    ch: str
    element: str
    element_ch: str
    yin_yang: str
    color: str
    ten_god: str


class BranchDetail(BaseModel):
    """지지(支) 상세 정보 (한글/한자, 오행, 음양, 색상, 십신)"""
    kr: str
    ch: str
    element: str
    element_ch: str
    yin_yang: str
    color: str
    ten_god: str


class JijangganDetail(BaseModel):
    """지장간(地藏干) 상세 정보 (초기/중기/정기 및 십신)"""
    kr: str
    ch: str
    element: str
    element_ch: str
    yin_yang: str
    color: str
    ten_god: str
    type: str
    ratio: Optional[str] = None


class PillarDetail(BaseModel):
    """기둥별 일원화 완성형 모델 (천간, 지지, 12운성, 지장간, 신살)"""
    gan: StemDetail
    ji: BranchDetail
    unseong: Optional[str] = None
    unseong_self: Optional[str] = None
    jijanggan: List[JijangganDetail] = []
    special_stars: List[str] = []


class FourPillars(BaseModel):
    """사주 4주 원국 (년주/월주/일주/시주)"""
    year: PillarDetail
    month: PillarDetail
    day: PillarDetail
    hour: PillarDetail


class TenGods(BaseModel):
    """십신 (천간 + 지지) - 기존 호환성 유지"""
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
    gan_detail: Optional[StemDetail] = None
    ji_detail: Optional[BranchDetail] = None
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
    gan_detail: Optional[StemDetail] = None
    ji_detail: Optional[BranchDetail] = None
    gan_ten_god: Optional[str] = None
    ji_ten_god: Optional[str] = None
    unseong: Optional[str] = None


class Daewoon(BaseModel):
    direction: str
    start_age: float

    current: Optional[CurrentDaewoon]

    list: List[DaewoonItem]


class CycleItem(BaseModel):
    """세운 / 소운 단일 연도 상세 항목"""
    year: int
    age: int
    gan: StemDetail
    ji: BranchDetail
    unseong: Optional[str] = None


class CyclesInfo(BaseModel):
    """운세 사이클 (세운 100년, 소운 10년)"""
    future_100: List[CycleItem]  # 100년 세운 객체 리스트
    baby_10: List[CycleItem]     # 소운 10년 객체 리스트


class MetaInfo(BaseModel):
    """사용자 메타 정보"""
    gender: str
    ddi: Optional[str] = None  # 띠
    birth_date_solar: Optional[str] = None  # YYYY-MM-DD
    birth_time: Optional[str] = None        # HH:MM
    age_man: Optional[int] = None           # 만 나이
    age_korean: Optional[int] = None        # 세는 나이
    birth_weekday: Optional[str] = None     # 태어난 요일


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
    special_stars_by_pillar: Optional[Dict[str, List[str]]] = None
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

