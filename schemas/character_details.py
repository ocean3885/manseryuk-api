"""Context-aware graph contract shared by natal and future cycle adapters."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from schemas.character_relation_index import ActivationStatus, RelationSource
from schemas.cycle_relation_validation import validate_cycle_relation

ACTIVATION_LABELS = dict(detected='탐지', candidate_only='후보', potential='잠재',
                         conditional='조건부', suppressed='억제', active='성립')


class Contract(BaseModel):
    model_config = ConfigDict(extra='forbid')


class AnalysisContext(Contract):
    scope: Literal['natal', 'daewoon', 'sewoon']
    instance: str = Field(pattern=r'^[A-Za-z0-9_]+$')
    label: str
    calculation_status: Literal['calculated', 'candidates_detected', 'not_evaluated']
    selection: dict[str, Any] = Field(default_factory=dict)


class Direction(Contract):
    from_character: str
    to_character: str
    basis: str


class ParticipantDetail(Contract):
    character_id: str
    context_id: str
    scope: Literal['natal', 'daewoon', 'sewoon']
    position: str
    kind: Literal['stem', 'branch']
    char: str
    ten_god: str
    display_name: str


class RelationEvidence(Contract):
    source: RelationSource
    details: dict[str, Any]
    characters: list[ParticipantDetail] = Field(default_factory=list)
    related_relation_ids: list[str] = Field(default_factory=list)


class ExplanationLine(Contract):
    code: str
    category: Literal['decision', 'notice', 'scope', 'structure']
    text: str
    character_ids: list[str]
    relation_ids: list[str]
    evidence_indices: list[int] = Field(default_factory=list)


class RelationPresentation(Contract):
    rule_version: Literal['1.0.0'] = '1.0.0'
    title: str
    status_label: str
    description: str
    reasons: list[ExplanationLine]
    explanation_status: Literal['complete', 'partial']
    missing_evidence_codes: list[str]


class UnifiedRelation(Contract):
    relation_id: str
    type: str
    participants: list[str] = Field(min_length=2)
    context_ids: list[str] = Field(min_length=1)
    activation_status: ActivationStatus
    status_reason: str | None = None
    direction: Direction | None = None
    candidate_element: str | None = None
    hidden_stem: str | None = None
    formation_candidates: list[list[str]] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    source_refs: list[RelationSource] = Field(min_length=1)
    source_relation_id: str
    participant_details: list[ParticipantDetail] = Field(default_factory=list)
    status_reasons: list[str] = Field(default_factory=list)
    element_relation: Literal['stem_generates_branch', 'branch_generates_stem',
                              'stem_controls_branch', 'branch_controls_stem', 'same_element'] | None = None
    evidence: list[RelationEvidence] = Field(default_factory=list)
    presentation: RelationPresentation | None = None


class CharacterDetail(Contract):
    context_id: str
    position: str = Field(pattern=r'^[A-Za-z0-9_]+$')
    kind: Literal['stem', 'branch']
    char: str = Field(min_length=1, max_length=1)
    attributes: dict[str, Any]
    pillar_attributes: dict[str, Any]
    analysis: dict[str, Any]
    rooting: 'Rooting | None' = None
    relation_ids: list[str]
    transmission_relation_ids: list[str]


class Rooting(Contract):
    original_status: Literal['실(實)', '허투(虛透)']
    current_status: Literal['실(實)', '허투(虛透)']
    root_score: float = Field(ge=0)
    remaining_score: float = Field(ge=0)
    has_same_pillar_root: bool
    root_branch_ids: list[str]
    affected_root_branch_ids: list[str]
    external_support_score: float = Field(ge=0)
    external_support_branch_ids: list[str]
    source_rule_version: str
    root_scope: Literal['same_pillar_only']
    validation_status: Literal['provisional']
    root_impact_status: Literal['not_evaluated']
    root_impact_score: None
    reason: str | None = None
    transition_reasons: list[str] = Field(default_factory=list)
    evidence: list[RelationEvidence] = Field(default_factory=list)


class Coverage(Contract):
    transmission_basis: Literal['jijanggan_detailed_exact_match']
    detected_only_relation_ids: list[str]
    calculated_scopes: list[Literal['natal', 'daewoon', 'sewoon']]
    not_evaluated_scopes: list[Literal['natal', 'daewoon', 'sewoon']]
    not_evaluated_mechanisms: list[str]
    power_effects_included: Literal[False]
    rule_scope: Literal['registered_rules_partial']


class CharacterDetails(Contract):
    schema_version: Literal['1.0-draft']
    contexts: dict[str, AnalysisContext]
    characters: dict[str, CharacterDetail]
    relations: dict[str, UnifiedRelation]
    coverage: Coverage

    @model_validator(mode='after')
    def check_graph(self):
        def check_details(details, expected=None):
            ids = [d.character_id for d in details]
            if len(ids) != len(set(ids)) or (expected is not None and ids != expected):
                raise ValueError('참여 글자 상세 참조가 맞지 않습니다.')
            for detail in details:
                node = self.characters.get(detail.character_id)
                if (node is None or detail.context_id != node.context_id
                        or detail.scope != self.contexts[node.context_id].scope
                        or detail.position != node.position or detail.kind != node.kind
                        or detail.char != node.char or detail.ten_god != node.attributes.get('ten_god')):
                    raise ValueError('참여 글자 상세와 일간 기준 십성이 원본과 다릅니다.')

        def check_evidence(entries):
            for entry in entries:
                check_details(entry.characters)
                ids = entry.related_relation_ids
                if len(ids) != len(set(ids)) or any(rid not in self.relations for rid in ids):
                    raise ValueError('판정 근거 관계 참조가 맞지 않습니다.')

        for key, context in self.contexts.items():
            if key != f'{context.scope}.{context.instance}':
                raise ValueError('분석 소속 ID가 맞지 않습니다.')
        for key, node in self.characters.items():
            if node.context_id not in self.contexts or key != f'{node.context_id}.{node.position}.{node.kind}':
                raise ValueError('글자 ID와 소속·위치가 맞지 않습니다.')
            if node.attributes.get('ch') != node.char:
                raise ValueError('글자 속성과 글자가 다릅니다.')
            if node.rooting:
                root = node.rooting
                check_evidence(root.evidence)
                own_branch = f'{node.context_id}.{node.position}.branch'
                if (node.kind != 'stem'
                        or root.root_branch_ids != ([own_branch] if root.has_same_pillar_root else [])
                        or root.has_same_pillar_root != (root.root_score > 0)
                        or root.remaining_score != root.root_score
                        or root.current_status != root.original_status
                        or root.original_status != ('실(實)' if root.has_same_pillar_root else '허투(虛透)')
                        or root.affected_root_branch_ids):
                    raise ValueError('동주 통근과 미평가 상태가 맞지 않습니다.')
                for ref in root.root_branch_ids + root.external_support_branch_ids:
                    if (ref not in self.characters or self.characters[ref].kind != 'branch'
                            or self.characters[ref].context_id != node.context_id):
                        raise ValueError('통근·타주 지원 참조가 잘못됐습니다.')
                if own_branch in root.external_support_branch_ids:
                    raise ValueError('동주 통근이 타주 지원에 섞였습니다.')
                if len(root.external_support_branch_ids) != len(set(root.external_support_branch_ids)):
                    raise ValueError('타주 지원 참조가 중복됐습니다.')
            expected = [rid for rid, row in self.relations.items() if key in row.participants]
            if len(node.relation_ids) != len(set(node.relation_ids)) or set(node.relation_ids) != set(expected):
                raise ValueError('글자별 관계 참조가 맞지 않습니다.')
            if node.transmission_relation_ids != [rid for rid in node.relation_ids if self.relations[rid].type == 'transmission']:
                raise ValueError('투간 참조가 맞지 않습니다.')
        for key, row in self.relations.items():
            if row.participant_details:
                check_details(row.participant_details, row.participants)
            check_evidence(row.evidence)
            if (len(row.status_reasons) != len(set(row.status_reasons))
                    or (row.status_reasons and row.status_reason and row.status_reason not in row.status_reasons)):
                raise ValueError('판정 사유 목록과 대표 사유가 다릅니다.')
            if any(e.details.get('effective_activation_status', row.activation_status) != row.activation_status
                   for e in row.evidence):
                raise ValueError('근거의 최종 상태가 관계 상태와 다릅니다.')
            if row.presentation:
                display = row.presentation
                if display.status_label != ACTIVATION_LABELS[row.activation_status]:
                    raise ValueError('설명 상태 배지와 관계 상태가 다릅니다.')
                if (display.explanation_status == 'complete') != (not display.missing_evidence_codes):
                    raise ValueError('설명 완결 상태와 근거 누락 목록이 다릅니다.')
                allowed_characters = set(row.participants) | {d.character_id for e in row.evidence for d in e.characters}
                allowed_relations = {key} | {rid for e in row.evidence for rid in e.related_relation_ids}
                for line in display.reasons:
                    for ids, allowed in ((line.character_ids, allowed_characters), (line.relation_ids, allowed_relations)):
                        if len(ids) != len(set(ids)) or any(ref not in allowed for ref in ids):
                            raise ValueError('설명 근거 참조가 맞지 않습니다.')
                    if (len(line.evidence_indices) != len(set(line.evidence_indices))
                            or any(i < 0 or i >= len(row.evidence) for i in line.evidence_indices)):
                        raise ValueError('설명의 원본 근거 위치가 맞지 않습니다.')
            if key != row.relation_id or len(set(row.participants)) != len(row.participants):
                raise ValueError('관계 ID 또는 참여 위치가 중복됩니다.')
            if any(p not in self.characters for p in row.participants):
                raise ValueError('관계의 참여 글자가 없습니다.')
            if (len(row.context_ids) != len(set(row.context_ids))
                    or set(row.context_ids) != {self.characters[p].context_id for p in row.participants}):
                raise ValueError('관계 소속이 참여 글자의 소속과 다릅니다.')
            if row.direction and (row.direction.from_character not in row.participants
                                  or row.direction.to_character not in row.participants
                                  or row.direction.from_character == row.direction.to_character):
                raise ValueError('관계 방향이 참여 글자와 맞지 않습니다.')
            if any(len(group) < 2 or len(group) != len(set(group))
                   or not set(group) <= set(row.participants) for group in row.formation_candidates):
                raise ValueError('다자 조합이 참여 글자를 벗어났습니다.')
            if row.activation_status in ('conditional', 'suppressed') and not row.status_reason:
                raise ValueError('조건부·억제 사유가 필요합니다.')
            if key.startswith('cycle:'):
                validate_cycle_relation(row, self.characters)
        calculated = {c.scope for c in self.contexts.values()
                      if c.calculation_status in ('calculated', 'candidates_detected')}
        if (set(self.coverage.calculated_scopes) != calculated
                or set(self.coverage.not_evaluated_scopes) != {'natal', 'daewoon', 'sewoon'} - calculated):
            raise ValueError('계산 범위와 분석 소속이 맞지 않습니다.')
        if set(self.coverage.detected_only_relation_ids) != {
                key for key, row in self.relations.items() if row.activation_status == 'detected'}:
            raise ValueError('탐지만 완료한 관계 목록이 맞지 않습니다.')
        for values in (self.coverage.detected_only_relation_ids, self.coverage.calculated_scopes,
                       self.coverage.not_evaluated_scopes, self.coverage.not_evaluated_mechanisms):
            if len(values) != len(set(values)):
                raise ValueError('탐지 범위 목록이 중복됐습니다.')
        return self
