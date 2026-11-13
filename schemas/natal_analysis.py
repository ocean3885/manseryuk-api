"""원국 상세 원자료의 타입. 키와 부재/null을 보존하며 미등록 필드는 거부한다."""
from typing import Annotated, Literal
from typing_extensions import NotRequired, TypedDict
from pydantic import ConfigDict, Field, with_config

PillarKey = Literal['year', 'month', 'day', 'hour']
PillarIndex = Annotated[int, Field(ge=0, le=3)]
Element = Literal['木', '火', '土', '金', '水']


class RawContract(TypedDict):
    __pydantic_config__ = ConfigDict(extra='forbid')


class ConditionCharacter(RawContract):
    index: PillarIndex
    pillar: PillarKey
    char: str
    ten_god: str
    display_name: str


class ClashObservation(RawContract):
    affected: ConditionCharacter
    cause: ConditionCharacter
    description: str
    clashing_index: PillarIndex
    clashing_pillar: NotRequired[PillarKey]


class SixHapClash(ClashObservation):
    member_index: PillarIndex
    member_pillar: NotRequired[PillarKey]
    location: Literal['between', 'outside']
    location_label: str


class MiddleClash(ClashObservation):
    middle_index: PillarIndex
    middle_pillar: NotRequired[PillarKey]


class WingClash(ClashObservation):
    wing_index: PillarIndex
    wing_pillar: NotRequired[PillarKey]
    wing_role: Literal['birth', 'tomb']


class SixHapCondition(RawContract):
    summary: str
    adjacent_clashes: list[SixHapClash]


class TrineCondition(RawContract):
    summary: str
    middle_indices: list[PillarIndex]
    middle_members: list[ConditionCharacter]
    middle_count: int
    adjacent_clashes: list[MiddleClash]
    adjacent_wing_clashes: list[WingClash]


class MatrixTrineCondition(RawContract):
    summary: str
    middle_members: list[ConditionCharacter]
    middle_count: int
    middle_pillars: list[PillarKey]
    adjacent_clashes: list[MiddleClash]
    adjacent_wing_clashes: list[WingClash]


class HalfHapContext(RawContract):
    group_branches: list[str]
    clashed_branch: str
    clashed_index: PillarIndex
    clashing_index: PillarIndex
    clashed_pillar: NotRequired[PillarKey]
    clashing_pillar: NotRequired[PillarKey]
    reason: Literal['adjacent_birth_clash', 'adjacent_tomb_clash']
    affected: ConditionCharacter
    cause: ConditionCharacter
    description: str


class MatrixHalfHapCondition(RawContract):
    summary: str
    fallback_from: HalfHapContext


class EmptyCondition(RawContract):
    pass


InteractionCondition = SixHapCondition | MatrixTrineCondition | MatrixHalfHapCondition | EmptyCondition


class RawRelation(RawContract):
    my: str
    my_index: PillarIndex
    my_ten_star: str
    status_reasons: list[str]
    impact_status: Literal['not_evaluated']


# `with`는 JSON 계약의 키이며 Python 예약어이므로 함수형 선언을 사용한다.
RawPeer = TypedDict('RawPeer', {'with': str, 'with_index': PillarIndex, 'with_ten_star': str})


class RawPair(RawRelation, RawPeer):
    is_adjacent: bool


class RawDistancePair(RawPair):
    distance: int
    distance_weight: float


class RawStemPair(RawDistancePair):
    activation_status: Literal['detected']


class RawStemCombination(RawStemPair):
    candidate_element: Element


class RawStemControl(RawStemPair):
    base_coefficient: float
    potential_index: float


class RawStemControls(RawContract):
    restrain_to: list[RawStemControl]
    restrain_me: list[RawStemControl]


class RawStemRelations(RawContract):
    combinations: list[RawStemCombination]
    restrain: RawStemControls
    conflict: list[RawStemPair]


class RawActivePair(RawDistancePair):
    activation_status: Literal['active']
    activation_rule_id: str


class RawSixHap(RawDistancePair):
    activation_status: Literal['detected']
    activation_rule_id: None
    candidate_element: Element
    type: Literal['근합', '원합']
    proximity_coefficient: float
    condition_evidence: SixHapCondition


class RawHalfHap(RawPair):
    distance: int
    activation_status: Literal['potential']
    missing: str | None
    fallback_from: HalfHapContext | None
    candidate_element: Element
    type: str
    structure_coefficient: float


class RawGongHap(RawPair):
    activation_status: Literal['candidate_only']
    missing: str
    candidate_element: Element


HiddenStemPair = with_config(ConfigDict(extra='forbid'))(TypedDict('HiddenStemPair', {
    'my': str, 'with': str, 'combined_element_candidate': Element,
}))


class RawHiddenStemHap(RawPair):
    activation_status: Literal['candidate_only']
    hidden_stem_pairs: list[HiddenStemPair]


class RawPunishment(RawDistancePair):
    activation_status: Literal['active', 'candidate_only']
    activation_rule_id: str | None
    base_coefficient: float
    potential_index: float
    type: Literal['지세형', '자형']


class RawGroupMember(RawContract):
    char: str
    index: PillarIndex
    ten_star: str


class RawGroup(RawRelation):
    branches: list[str]
    participant_indices: list[PillarIndex]
    formation_indices: list[list[PillarIndex]]
    with_branches: list[RawGroupMember]
    is_adjacent: bool


class RawTrine(RawGroup):
    activation_status: Literal['detected']
    candidate_element: Element
    structure_coefficient: float
    condition_evidence: TrineCondition
    is_continuous: bool


class RawSquare(RawGroup):
    activation_status: Literal['potential']
    candidate_element: Element
    season: str
    base_coefficient: float
    proximity_coefficient: float
    potential_index: float
    formation_distances: list[int]
    distance: int


class RawTriplePunishment(RawGroup):
    activation_status: Literal['active']
    activation_rule_id: str
    type: Literal['무은지형', '지세형']


class RawBranchRelations(RawContract):
    six_haps: list[RawSixHap]
    chungs: list[RawActivePair]
    cheons: list[RawActivePair]
    breaks: list[RawActivePair]
    three_haps: list[RawTrine]
    half_haps: list[RawHalfHap]
    gong_haps: list[RawGongHap]
    hidden_stem_haps: list[RawHiddenStemHap]
    square_haps: list[RawSquare]
    three_punishments: list[RawTriplePunishment]
    punishments: list[RawPunishment]


class RootSupport(RawContract):
    branch_char: str
    position: Literal['년', '월', '일', '시']
    ten_star: str
    score: float


class RawStemAnalysis(RawContract):
    char: str
    position: Literal['년', '월', '일', '시']
    score: float
    root_info: list[RootSupport]
    status: Literal['실(實)', '허투(虛透)']
    unseong: str
    relations: RawStemRelations
    root_scope: Literal['same_pillar_only']
    same_pillar_root_exists: bool
    external_support_score: float
    external_support_info: list[RootSupport]


class HiddenStemInfo(RawContract):
    stem: str
    stem_pos: Literal['초기', '중기', '정기']
    stem_ten_star: str


TransmissionSource = TypedDict('TransmissionSource', {
    'from': str, 'from_idx': PillarIndex, 'from_ten_star': str,
})


class TransmittedStem(HiddenStemInfo, TransmissionSource):
    stem_idx: PillarIndex


class StorehouseInfo(RawContract):
    stored_element: Literal['木', '火', '金', '水']
    role: Literal['비겁고', '식상고', '재고', '관성고', '인성고']


class RawBranchAnalysis(RawContract):
    char: str
    storehouse: StorehouseInfo | None
    jijanggan: list[str]
    transmitted: list[TransmittedStem]
    hidden: list[HiddenStemInfo]
    relations: RawBranchRelations


class SelfCombinationContext(RawContract, RawPeer):
    type: Literal['clash', 'punishment', 'self_punishment']
    distance: int
    is_adjacent: bool


class RawSelfCombination(RawContract):
    chars: tuple[str, str]
    my_index: PillarIndex
    exists: Literal[True]
    hidden_stem: str
    candidate_element: Element
    activation_status: Literal['detected']
    impact_status: Literal['not_evaluated']
    related_branch_relations: list[SelfCombinationContext]


class RawPillarAnalysis(RawContract):
    stem: RawStemAnalysis
    branch: RawBranchAnalysis
    jahab: RawSelfCombination | None


class NatalAnalysisDetails(RawContract):
    year: RawPillarAnalysis
    month: RawPillarAnalysis
    day: RawPillarAnalysis
    hour: RawPillarAnalysis


class BinZhuElementLabels(RawContract):
    stem: str
    branch: str


class BinZhuDomainStructure(RawContract):
    scope: str
    elements: dict[PillarKey, BinZhuElementLabels]
