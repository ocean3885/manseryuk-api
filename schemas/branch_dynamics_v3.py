"""지지 작용 v3 목표 응답의 독립 Pydantic 모델.

이 모델은 현재 API의 advanced_analysis.branch_dynamics를 변경하지 않는다.
작공·LLM과 천간 분석의 내부 자료형은 해당 계산 단계에서 확장한다.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.branch_dynamics_v3_contract import validate_branch_dynamics_v3


Pillar = Literal['year', 'month', 'day', 'hour']
Domain = Literal['guest', 'host']
CalculationStatus = Literal[
    'not_applicable', 'pending', 'potential_calculated', 'resolved',
]
ActivationStatus = Literal[
    'candidate_only', 'potential', 'conditional', 'suppressed', 'active', 'detected',
]


class V3Model(BaseModel):
    model_config = ConfigDict(extra='forbid')


class ScorePolicyV3(V3Model):
    cross_type_addition: Literal[False]
    zero_means_no_effect: Literal[True]
    null_means_not_calculated: Literal[True]


class MetaV3(V3Model):
    schema_version: str
    rule_version: str | None
    analysis_school: Literal['mangpa']
    score_meaning: Literal['uncalibrated_relative_index']
    score_policy: ScorePolicyV3


class ChartPillarV3(V3Model):
    stem: str
    branch: str
    domain: Domain


class ChartPillarsV3(V3Model):
    year: ChartPillarV3
    month: ChartPillarV3
    day: ChartPillarV3
    hour: ChartPillarV3


class ChartContextV3(V3Model):
    bin_zhu_rule: Literal['year_month_guest_day_hour_host']
    pillars: ChartPillarsV3


class SeasonEvidenceV3(V3Model):
    month_branch: str
    relation: str
    factor: float | None


class HiddenStemEvidenceV3(V3Model):
    stem: str
    element: str
    ratio: float
    season_relation: str
    effective_contribution: float | None


class SamePillarStemEvidenceV3(V3Model):
    stem: str
    relation: str
    effect: str
    adjustment: float | None


class SurroundingEvidenceV3(V3Model):
    source_pillar: Pillar
    relation: str
    adjustment_ratio: float | None


class StrengthEvidenceV3(V3Model):
    position_weight: float
    season: SeasonEvidenceV3
    hidden_stems: list[HiddenStemEvidenceV3]
    same_pillar_stem: SamePillarStemEvidenceV3
    surroundings: list[SurroundingEvidenceV3]


class CalculationTraceV3(V3Model):
    base_formula_id: str | None
    stem_formula_id: str | None
    surroundings_formula_id: str | None
    applied_adjustments: list[dict[str, Any]]
    validation_status: str


class BranchStrengthV3(V3Model):
    branch: str
    element: str
    bin_zhu_domain: Domain
    base_power: float | None
    after_stem_power: float | None
    effective_power: float | None
    strength_evidence: StrengthEvidenceV3
    calculation_trace: CalculationTraceV3


class BranchStrengthsV3(V3Model):
    year: BranchStrengthV3
    month: BranchStrengthV3
    day: BranchStrengthV3
    hour: BranchStrengthV3


class RelationDirectionV3(V3Model):
    from_pillar: Pillar
    to_pillar: Pillar


class DirectionalEffectV3(V3Model):
    from_pillar: Pillar
    to_pillar: Pillar
    acting_domain: Domain
    receiving_domain: Domain
    source_capacity: float | None
    coefficient: float | None
    distance_weight: float | None
    interaction_intensity: float | None
    target_exposure: float | None
    applied_power_delta: float | None


class RelationMetricsV3(V3Model):
    potential_formula_id: str
    exposure_formula_id: str
    directional_effects: list[DirectionalEffectV3]


class RuleEvidenceV3(V3Model):
    rule_id: str
    basis: str


class RelationBinZhuContextV3(V3Model):
    acting_domain: Domain
    receiving_domain: Domain
    direction: str


class RelationInteractionContextV3(V3Model):
    coexisting_interaction_ids: list[str]
    resolution_status: str


class BranchRelationV3(V3Model):
    relation_id: str
    type: str
    label_ko: str
    activation_status: ActivationStatus
    calculation_status: CalculationStatus
    candidate_element: str | None = None
    formation_status: str | None = None
    effect_status: Literal['structural_only'] | None = None
    status_reason: str | None = None
    direction: RelationDirectionV3 | None = None
    metrics: RelationMetricsV3 | None = None
    power_before: dict[Pillar, float | None] | None = None
    force_dominance: Pillar | Literal['tie', 'undetermined'] | None = None
    roles: dict[Pillar, str] | None = None
    bin_zhu_context: RelationBinZhuContextV3 | None = None
    interaction_context: RelationInteractionContextV3 | None = None
    evidence: list[RuleEvidenceV3] = Field(default_factory=list)


class BranchPairV3(V3Model):
    pair_id: str
    pillars: list[Pillar]
    branches: list[str]
    pillar_distance: int
    adjacent: bool
    domain_pair: Literal['guest_guest', 'guest_host', 'host_host']
    relations: list[BranchRelationV3]


class GroupConditionEvidenceV3(V3Model):
    middle_pillars: list[Pillar]
    adjacent_clashes: list[dict[str, Any]]
    duplicate_middle: bool
    duplicate_components: list[str]


class GroupComponentPairV3(V3Model):
    pillars: list[Pillar]
    relation_id: str
    effect: Literal['structural_only']


class GroupDirectionCandidateV3(V3Model):
    from_pillar: Pillar
    to_pillar: Pillar
    pillar_distance: int
    status: ActivationStatus


class GroupBinZhuContextV3(V3Model):
    domains: dict[Pillar, Domain]
    crosses_domains: bool


class GroupFormationV3(V3Model):
    formation_id: str
    pillars: list[Pillar]
    structural_roles: dict[Pillar, str]
    component_pairs: list[GroupComponentPairV3]
    direction_candidates: list[GroupDirectionCandidateV3]
    bin_zhu_context: GroupBinZhuContextV3


class GroupOverlapV3(V3Model):
    shared_pillars: list[Pillar]
    counting_policy: Literal['evaluate_as_one_network']
    dominant_formation_id: str | None


class BranchGroupV3(V3Model):
    group_id: str
    type: str
    label_ko: str
    branches: list[str]
    candidate_element: str | None
    transformed_element: str | None
    formation_status: str
    transformation_status: str
    group_power: None
    group_power_status: Literal['not_scored']
    status_reasons: list[str]
    condition_evidence: GroupConditionEvidenceV3
    formation_candidates: list[GroupFormationV3]
    overlap: GroupOverlapV3 | None = None
    evidence_rule_ids: list[str]


class BranchDynamicsV3(V3Model):
    branch_strengths: BranchStrengthsV3
    pairwise: list[BranchPairV3]
    groups: list[BranchGroupV3]


class ResolutionCaseV3(V3Model):
    case_id: str
    interaction_ids: list[str] = Field(default_factory=list)
    structural_context_relation_ids: list[str] = Field(default_factory=list)
    group_id: str | None = None
    candidate_ids: list[str] = Field(default_factory=list)
    resolution_status: str
    selected_interaction_ids: list[str] = Field(default_factory=list)
    suppressed_interaction_ids: list[str] = Field(default_factory=list)
    selected_formation_ids: list[str] = Field(default_factory=list)
    counting_policy: Literal['evaluate_as_one_network'] | None = None
    rule_ids: list[str]
    reason_codes: list[str]


class InteractionResolutionV3(V3Model):
    status: str
    resolution_cases: list[ResolutionCaseV3]
    active_interaction_ids: list[str]
    suppressed_interaction_ids: list[str]
    unresolved_interaction_ids: list[str]


class WorkEndpointV3(V3Model):
    pillar: Pillar
    component: Literal['branch', 'stem']
    branch: str | None = None
    stem: str | None = None
    domain: Domain


class TenGodContextV3(V3Model):
    source_ten_god: str | None
    target_ten_god: str | None
    affected_hidden_stems: list[str]


class WorkPathV3(V3Model):
    path_id: str
    source: WorkEndpointV3
    target: WorkEndpointV3
    mechanism_candidates: list[str]
    source_interaction_ids: list[str]
    structural_context_relation_ids: list[str]
    bin_zhu_direction: str
    active_mechanism: str | None
    ten_god_context: TenGodContextV3
    work_status: str
    result_ownership: str
    interpretation: str | None


class WorkAssessmentV3(V3Model):
    primary_work_path_id: str | None
    body_use_relation: str | None
    control_transformation: str | None
    result_ownership: str
    analysis_status: str


class WorkDynamicsV3(V3Model):
    status: str
    candidate_paths: list[WorkPathV3]
    active_work_paths: list[dict[str, Any]]
    overall_assessment: WorkAssessmentV3


class StructuralFactV3(V3Model):
    code: str
    summary: str
    ref_ids: list[str] = Field(default_factory=list)


class UnresolvedMechanismV3(V3Model):
    ref_ids: list[str]
    summary: str


class LlmInterpretationPayloadV3(V3Model):
    status: str
    structural_facts: list[StructuralFactV3]
    active_relations: list[dict[str, Any]]
    unresolved_mechanisms: list[UnresolvedMechanismV3]
    confirmed_work_paths: list[dict[str, Any]]
    interpretation_constraints: list[str]


class BranchDynamicsV3Response(V3Model):
    meta: MetaV3
    chart_context: ChartContextV3
    stem_dynamics: dict[str, Any] | None
    branch_dynamics: BranchDynamicsV3
    interaction_resolution: InteractionResolutionV3
    work_dynamics: WorkDynamicsV3
    llm_interpretation_payload: LlmInterpretationPayloadV3

    @model_validator(mode='after')
    def check_contract(self):
        validate_branch_dynamics_v3(self.model_dump())
        return self
