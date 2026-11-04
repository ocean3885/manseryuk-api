"""Context-aware graph contract shared by natal and future cycle adapters."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from schemas.character_relation_index import ActivationStatus, RelationSource


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
        calculated = {c.scope for c in self.contexts.values()
                      if c.calculation_status in ('calculated', 'candidates_detected')}
        if (set(self.coverage.calculated_scopes) != calculated
                or set(self.coverage.not_evaluated_scopes) != {'natal', 'daewoon', 'sewoon'} - calculated):
            raise ValueError('계산 범위와 분석 소속이 맞지 않습니다.')
        if set(self.coverage.detected_only_relation_ids) != {
                key for key, row in self.relations.items() if row.activation_status == 'detected'}:
            raise ValueError('탐지만 완료한 관계 목록이 맞지 않습니다.')
        return self
