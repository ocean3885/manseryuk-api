from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict, Literal

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
    relation_id: str
    relation_scope: Literal['pairwise', 'group']
    participants: List[str]
    formations: List[List[str]]
    category: str
    type: str
    name: str
    from_pillar: str
    to_pillar: str
    is_adjacent: bool
    weight: float
    score: float
    score_contribution: Optional[float] = None
    score_covered_by: Optional[str] = None
    transformed_element: Optional[str] = None
    candidate_element: Optional[str] = None
    missing_branch: Optional[str] = None
    hidden_stem_pairs: Optional[List[Dict[str, str]]] = None
    candidate_hidden_stem_effects: List[Dict[str, str]] = Field(default_factory=list)
    activation_status: Optional[str] = None
    status_reasons: List[str] = Field(default_factory=list)
    condition_evidence: Dict[str, Any] = Field(default_factory=dict)
    description: str


class InteractionsInfo(BaseModel):
    rule_version: str
    summary_list: List[str]
    matrix: List[InteractionItem]
    tension_score: float
    harmony_score: float
    climate: str


class XuShiInteraction(BaseModel):
    relation_id: Optional[str] = None
    type: str
    name: str
    from_pillar: str
    to_pillar: str
    weight: Optional[float] = None
    is_adjacent: Optional[bool] = None


class XuShiRootEvidence(BaseModel):
    pillar: str
    position: str
    branch_char: str
    score: float
    is_affected: bool
    effective_score: float
    interactions: List[XuShiInteraction]


class XuShiRootStructure(BaseModel):
    primary_root_pillars: List[str]
    remaining_root_pillars: List[str]
    excluded_root_pillars: List[str]
    remaining_support: Literal['none', 'below_threshold', 'meets_threshold']


class XuShiRootDependent(BaseModel):
    stem_pillar: str
    score: float
    effective_score: float
    current_status: str


class XuShiSharedRoot(BaseModel):
    root_pillar: str
    branch_char: str
    is_affected: bool
    interactions: List[XuShiInteraction]
    dependents: List[XuShiRootDependent]


class XuShiImpactGroup(BaseModel):
    interaction: XuShiInteraction
    affected_root_pillars: List[str]
    affected_stem_pillars: List[str]


class PillarXuShi(BaseModel):
    position: str
    char: str
    ten_star: str
    score: float
    effective_score: float
    root_evidence: List[XuShiRootEvidence]
    transition_reasons: List[str]
    original_status: str
    current_status: str
    is_transformed: bool
    transition_code: Literal['maintained', 'real_to_empty']
    root_structure: XuShiRootStructure
    reason: str
    meaning: str


class XuShiDynamics(BaseModel):
    analysis_scope: Literal['natal']
    rule_version: str
    pillars: Dict[str, PillarXuShi]
    shared_roots: List[XuShiSharedRoot]
    impact_groups: List[XuShiImpactGroup]
    real_count: int
    transformed_empty_count: int
    hollow_penetrate_count: int
    weak_count: int
    overall_status: str


class ControlFlow(BaseModel):
    direction: str
    dominant_interaction: Optional[str] = None
    summary_meaning: str
    career_advice: str
    interpretation_notes: Optional[str] = None
    vector: Optional[str] = None
    vector_code: Optional[str] = None
    acquisition_summary: Optional[str] = None


class BinZhuExcludedInteraction(BaseModel):
    relation_id: Optional[str] = None
    participants: List[str]
    category: str
    type: str
    name: str
    from_pillar: Optional[str] = None
    to_pillar: Optional[str] = None
    reason_code: Literal['group_relation_unsupported', 'invalid_endpoint',
                         'unsupported_relation_type', 'candidate_only_relation']


class BinZhuGroupConnection(BaseModel):
    relation_id: Optional[str] = None
    type: str
    participants: List[str]
    guest_participants: List[str]
    host_participants: List[str]
    included_in_score: bool = False
    cohesion_score: Optional[float] = None
    activation_status: Optional[str] = None
    description: str


class BinZhuLink(BaseModel):
    relation_id: Optional[str] = None
    type: str
    detail: str
    target_guest: str
    source_host: str
    mechanism: Optional[str] = None
    flow_direction: Optional[str] = None
    weight: Optional[float] = None


class BinZhuScores(BaseModel):
    combination: float
    conflict: float
    unweighted_combination: Optional[float] = None
    unweighted_conflict: Optional[float] = None


class BinZhuDynamics(BaseModel):
    rule_version: str
    pairwise_scores: BinZhuScores
    group_cohesion_score: Optional[float] = 0.0
    group_connections: List[BinZhuGroupConnection]
    guest_host_links: List[BinZhuLink]
    interaction_scope: Literal['pairwise']
    excluded_interactions: List[BinZhuExcludedInteraction]
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


class BranchHiddenEvidence(BaseModel):
    stem: str
    element: str
    ratio: float
    season_relation: str
    stem_relation: str


class StemBranchRelation(BaseModel):
    stem: str
    stem_element: str
    relation: str
    branch_effect: str
    adjustment: float
    evidence: List[BranchHiddenEvidence]


class BranchStrength(BaseModel):
    branch: str
    element: str
    base_power: float
    stem_branch_relation: StemBranchRelation
    after_stem_power: float
    effective_power: float
    ambient_evidence: List[Dict[str, Any]]
    components: Dict[str, float]
    evidence: List[BranchHiddenEvidence]


class BranchRelationEffect(BaseModel):
    relation_id: str
    type: str
    effect_kind: str
    relation_coefficient: float
    directional_coefficients: Dict[str, float] = Field(default_factory=dict)
    directional_mechanisms: Dict[str, str] = Field(default_factory=dict)
    candidate_hidden_stem_effects: List[Dict[str, str]] = Field(default_factory=list)
    rule_id: Optional[str] = None
    activation_status: Literal['potential', 'conditional', 'suppressed', 'candidate_only'] = 'potential'
    status_reason: Optional[str] = None
    distance_weight: float
    element_relation: str
    element_direction: Optional[str] = None
    power_before: Dict[str, float]
    force: Dict[str, float]
    effect_received: Dict[str, float]
    dominance: str
    force_dominance: Literal['year', 'month', 'day', 'hour', 'tie', 'undetermined']
    roles: Dict[str, str]
    evidence: List[str]


class BranchPairDynamics(BaseModel):
    pair_id: str
    pillars: List[str]
    rule_id: Optional[str] = None
    primary_relation: Optional[str] = None
    relations: List[BranchRelationEffect]
    context_evidence: Dict[str, List[Dict[str, Any]]]
    domain_pair: Literal['guest_guest', 'host_host', 'guest_host']


class BranchGroupPairOverlap(BaseModel):
    relation_id: str
    covered_in_harmony_score: bool


class BranchGroupDirectionCandidate(BaseModel):
    from_pillar: str
    to_pillar: str
    mechanism: str
    activation_status: Literal['candidate_only', 'conditional', 'suppressed']


class BranchGroupRoleEffectCandidate(BaseModel):
    pillar: str
    effect: str
    activation_status: Literal['candidate_only', 'conditional', 'suppressed']


class BranchGroupFormationEvidence(BaseModel):
    pillars: List[str]
    structural_roles: Dict[str, str]
    power_before: Dict[str, float]
    context_evidence: Dict[str, List[Dict[str, Any]]]
    capacity_share: Dict[str, float]
    overlapping_pairs: List[BranchGroupPairOverlap]
    directional_candidates: List[BranchGroupDirectionCandidate]
    role_effect_candidates: List[BranchGroupRoleEffectCandidate]


class BranchGroupDynamics(BaseModel):
    relation_id: str
    type: str
    action_rule_id: Optional[str] = None
    direction_status: Literal['candidate_only', 'conditional', 'suppressed', 'undetermined']
    pair_overlap_policy: Optional[str] = None
    participants: List[str]
    formations: List[List[str]]
    element: Optional[str] = None
    candidate_element: Optional[str] = None
    transformed_element: Optional[str] = None
    status: Literal['not_scored']
    activation_status: Optional[str] = None
    status_reasons: List[str] = Field(default_factory=list)
    condition_evidence: Dict[str, Any] = Field(default_factory=dict)
    formation_evidence: List[BranchGroupFormationEvidence] = Field(default_factory=list)


class BranchDynamics(BaseModel):
    rule_profile: str
    rule_version: str
    scope: Literal['natal']
    score_meaning: Literal['uncalibrated_relative_model_index']
    branch_strengths: Dict[str, BranchStrength]
    pairwise: List[BranchPairDynamics]
    groups: List[BranchGroupDynamics]


class AdvancedAnalysis(BaseModel):
    five_elements: Optional[FiveElementsInfo] = None
    special_stars: Optional[List[SpecialStarItem]] = None
    special_stars_by_pillar: Optional[Dict[str, List[str]]] = None
    interactions: InteractionsInfo
    branch_dynamics: Optional[BranchDynamics] = None
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
