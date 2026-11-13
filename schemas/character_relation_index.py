"""원국 8글자의 관계 탐지 결과를 조회하기 위한 독립 초안 계약.

독립 관계 조회 경로에서 사용하며 기존 원국·지지 v3 응답은 변경하지 않는다.
세력 변화량도 담지 않는다.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from services.five_elements import BRANCH_ELEMENT_MAP, STEM_ELEMENT_MAP


PILLARS = ('year', 'month', 'day', 'hour')
CHARACTER_IDS = tuple(
    f'{pillar}.{component}'
    for pillar in PILLARS for component in ('stem', 'branch')
)
CharacterId = Literal[
    'year.stem', 'year.branch', 'month.stem', 'month.branch',
    'day.stem', 'day.branch', 'hour.stem', 'hour.branch',
]
ActivationStatus = Literal[
    'detected', 'candidate_only', 'potential', 'conditional',
    'suppressed', 'active',
]
NOT_EVALUATED_MECHANISMS = (
    'stem_generate', 'stem_same_element', 'cross_pillar_stem_branch_element',
    'general_hidden_stem_damage', 'tomb_entry',
)
STEM_TYPES = {'combine', 'clash', 'control'}
BRANCH_TYPES = {
    'combine', 'clash', 'pierce', 'break', 'punishment',
    'self_punishment', 'half_combine', 'arch_combine',
    'hidden_combine', 'generate', 'control', 'same_branch',
}
GROUP_TYPES = {'trine', 'square', 'triple_punishment'}
SAME_PILLAR_TYPES = {'element', 'self_combine'}


class _ContractModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class CharacterNode(_ContractModel):
    char: str = Field(min_length=1, max_length=1)
    relation_ids: list[str]
    stem_state: 'StemRootingState | None' = None


class StemRootingState(_ContractModel):
    root_impact_status: Literal['not_evaluated'] = 'not_evaluated'
    root_impact_score: None = None
    original_status: Literal['실(實)', '허투(虛透)']
    current_status: Literal['실(實)', '허투(虛透)']
    root_score: float
    has_same_pillar_root: bool
    remaining_score: float
    root_branch_ids: list[CharacterId]
    affected_root_branch_ids: list[CharacterId]
    external_support_score: float
    external_support_branch_ids: list[CharacterId]
    source_rule_version: str
    root_scope: Literal['same_pillar_only']
    validation_status: Literal['provisional']

    @model_validator(mode='after')
    def check_roots(self):
        if (self.root_score < 0 or self.remaining_score < 0
                or self.external_support_score < 0
                or any(not item.endswith('.branch') for item in self.root_branch_ids)
                or any(not item.endswith('.branch')
                       for item in self.external_support_branch_ids)
                or any(item not in self.root_branch_ids
                       for item in self.affected_root_branch_ids)
                or len(self.root_branch_ids) != len(set(self.root_branch_ids))
                or len(self.affected_root_branch_ids) != len(set(self.affected_root_branch_ids))
                or len(self.external_support_branch_ids) != len(
                    set(self.external_support_branch_ids))
                or set(self.root_branch_ids) & set(self.external_support_branch_ids)):
            raise ValueError('천간 통근의 점수·지지 근거가 맞지 않습니다.')
        if (self.has_same_pillar_root != bool(self.root_branch_ids)
                or (self.has_same_pillar_root and self.root_score <= 0)
                or (not self.has_same_pillar_root and self.root_score != 0)):
            raise ValueError('동주 통근 여부와 근거가 맞지 않습니다.')
        if (self.remaining_score != self.root_score
                or self.current_status != self.original_status
                or self.original_status != ('실(實)' if self.has_same_pillar_root else '허투(虛透)')
                or self.affected_root_branch_ids):
            raise ValueError('통근 영향 미평가 상태에서는 점수·허실을 변경할 수 없습니다.')
        return self


class RelationSource(_ContractModel):
    system: Literal[
        'cycle_relation_rules',
        'interaction_matrix', 'branch_dynamics',
        'branch_dynamics_v3', 'analysis_details',
    ]
    relation_id: str | None = None
    location: str | None = None

    @model_validator(mode='after')
    def check_reference(self):
        if not self.relation_id and not self.location:
            raise ValueError('원본 관계 ID 또는 위치가 필요합니다.')
        return self


class RelationDirection(_ContractModel):
    from_character: CharacterId
    to_character: CharacterId
    basis: Literal['elemental', 'rule_fixed', 'hidden_stem_match']


class CharacterRelation(_ContractModel):
    relation_id: str
    type: str
    participants: list[CharacterId] = Field(min_length=2)
    activation_status: ActivationStatus
    status_reason: str | None = None
    direction: RelationDirection | None = None
    candidate_element: str | None = None
    hidden_stem: str | None = None
    formation_candidates: list[list[CharacterId]] = Field(default_factory=list)
    rule_ids: list[str] = Field(default_factory=list)
    source_refs: list[RelationSource] = Field(min_length=1)

    @model_validator(mode='after')
    def check_relation(self):
        if (self.type == 'trine' or self.relation_id.startswith('branch:combine:')) and self.activation_status != 'detected':
            raise ValueError('육합·삼합은 구성의 존재만 탐지하며 성립·차단을 판정하지 않습니다.')
        if self.type == 'self_combine' and (
                self.activation_status != 'detected' or self.status_reason is not None):
            raise ValueError('자합은 조합 존재만 탐지하며 성립·불성립을 판정하지 않습니다.')
        members = self.participants
        if (len(members) != len(set(members))
                or members != sorted(members, key=CHARACTER_IDS.index)):
            raise ValueError('참여 글자는 위치 순서로 중복 없이 기록해야 합니다.')
        if self.activation_status in ('conditional', 'suppressed') and not self.status_reason:
            raise ValueError('조건부·억제 관계에는 상태 이유가 필요합니다.')
        if len(self.rule_ids) != len(set(self.rule_ids)):
            raise ValueError('규칙 ID가 중복됐습니다.')
        if self.direction and (
                self.direction.from_character not in members
                or self.direction.to_character not in members
                or self.direction.from_character == self.direction.to_character):
            raise ValueError('방향의 출처와 대상은 서로 다른 참여 글자여야 합니다.')

        prefix, separator, _ = self.relation_id.partition(':')
        if not separator:
            raise ValueError('관계 ID에 종류 접두사가 필요합니다.')
        if prefix in ('stem', 'branch'):
            allowed = STEM_TYPES if prefix == 'stem' else BRANCH_TYPES
            if (self.type not in allowed or len(members) != 2
                    or any(not member.endswith(f'.{prefix}') for member in members)):
                raise ValueError('쌍 관계의 종류·참여 글자가 맞지 않습니다.')
            left, right = (member.split('.')[0] for member in members)
            if self.relation_id != f'{prefix}:{self.type}:{left}:{right}':
                raise ValueError('쌍 관계 ID와 참여 위치가 다릅니다.')
            if self.type in ('generate', 'control') and prefix == 'branch':
                if self.direction is None:
                    raise ValueError('지지 생·극에는 오행 방향이 필요합니다.')
            if self.type == 'control' and prefix == 'stem' and self.direction is None:
                raise ValueError('천간 극에는 오행 방향이 필요합니다.')
        elif prefix == 'same_pillar':
            if self.type not in SAME_PILLAR_TYPES or len(members) != 2:
                raise ValueError('동주 관계의 종류·참여 글자가 맞지 않습니다.')
            pillar = members[0].split('.')[0]
            if (members != [f'{pillar}.stem', f'{pillar}.branch']
                    or self.relation_id != f'same_pillar:{self.type}:{pillar}'):
                raise ValueError('동주 관계 ID와 천간·지지 위치가 다릅니다.')
        elif prefix == 'group':
            if (self.type not in GROUP_TYPES or len(members) not in (3, 4)
                    or any(not member.endswith('.branch') for member in members)
                    or not self.relation_id.startswith(f'group:{self.type}:')
                    or not self.relation_id.removeprefix(f'group:{self.type}:')):
                raise ValueError('그룹 관계의 종류·참여 지지가 맞지 않습니다.')
            if not self.formation_candidates:
                raise ValueError('그룹에는 위치별 세 글자 조합이 필요합니다.')
            formations = [tuple(formation) for formation in self.formation_candidates]
            if len(formations) != len(set(formations)):
                raise ValueError('그룹 성립 조합이 중복됐습니다.')
            if any(len(formation) != 3 or len(set(formation)) != 3
                   or list(formation) != sorted(formation, key=CHARACTER_IDS.index)
                   or not set(formation) <= set(members)
                   for formation in formations):
                raise ValueError('그룹 성립 조합이 참여 지지와 맞지 않습니다.')
            if set().union(*(set(formation) for formation in formations)) != set(members):
                raise ValueError('그룹의 참여 지지에 성립 조합이 없는 위치가 있습니다.')
        elif prefix == 'cross_layer':
            if (self.type != 'transmission' or len(members) != 2
                    or sum(member.endswith('.stem') for member in members) != 1
                    or self.direction is None
                    or self.direction.basis != 'hidden_stem_match'
                    or not self.direction.from_character.endswith('.branch')
                    or not self.direction.to_character.endswith('.stem')
                    or not self.hidden_stem
                    or self.relation_id != (
                        'cross_layer:transmission:'
                        f"{self.direction.from_character.split('.')[0]}:"
                        f"{self.direction.to_character.split('.')[0]}")):
                raise ValueError('지장간 투출의 출처·대상·ID가 맞지 않습니다.')
        else:
            raise ValueError('지원하지 않는 관계 ID 종류입니다.')
        if prefix != 'cross_layer' and self.hidden_stem is not None:
            raise ValueError('투출 이외의 관계에 지장간 대상을 넣을 수 없습니다.')
        if prefix != 'group' and self.formation_candidates:
            raise ValueError('쌍·동주 관계에 세 글자 조합을 넣을 수 없습니다.')
        return self


class DetectionCoverage(_ContractModel):
    rule_scope: Literal['registered_rules_partial']
    transmission_basis: Literal['jijanggan_detailed_exact_match']
    detected_only_relation_ids: list[str]
    not_evaluated_mechanisms: list[Literal[
        'stem_generate', 'stem_same_element', 'cross_pillar_stem_branch_element',
        'general_hidden_stem_damage', 'tomb_entry',
    ]]
    power_effects_included: Literal[False]


class CharacterRelationIndex(_ContractModel):
    schema_version: Literal['1.7-draft']
    characters: dict[CharacterId, CharacterNode]
    relations: list[CharacterRelation]
    coverage: DetectionCoverage

    @model_validator(mode='after')
    def check_index(self):
        if set(self.characters) != set(CHARACTER_IDS):
            raise ValueError('연·월·일·시 천간·지지 여덟 글자가 모두 필요합니다.')
        for char_id, node in self.characters.items():
            allowed = STEM_ELEMENT_MAP if char_id.endswith('.stem') else BRANCH_ELEMENT_MAP
            if node.char not in allowed:
                raise ValueError(f'{char_id}: 글자 종류가 맞지 않습니다.')
            if (node.stem_state is None) == char_id.endswith('.stem'):
                raise ValueError(f'{char_id}: 천간 상태의 위치가 맞지 않습니다.')
            if node.stem_state is not None:
                root = node.stem_state
                own_branch = char_id.replace('.stem', '.branch')
                if (root.root_branch_ids != ([own_branch] if root.has_same_pillar_root else [])
                        or own_branch in root.external_support_branch_ids):
                    raise ValueError(f'{char_id}: 동주 통근과 타주 지원 위치가 맞지 않습니다.')
        ids = [relation.relation_id for relation in self.relations]
        if len(ids) != len(set(ids)):
            raise ValueError('중복 관계 ID가 있습니다.')
        expected = {char_id: [] for char_id in CHARACTER_IDS}
        for relation in self.relations:
            for char_id in relation.participants:
                expected[char_id].append(relation.relation_id)
            if relation.type == 'transmission' and self.characters[
                    relation.direction.to_character].char != relation.hidden_stem:
                raise ValueError('투출 지장간과 대상 천간 글자가 다릅니다.')
        for char_id, node in self.characters.items():
            if node.relation_ids != expected[char_id]:
                raise ValueError(f'{char_id}: 중앙 관계와 글자별 참조가 다릅니다.')
        detected = [relation.relation_id for relation in self.relations
                    if relation.activation_status == 'detected']
        if self.coverage.detected_only_relation_ids != detected:
            raise ValueError('탐지만 한 관계 ID 목록이 중앙 관계 상태와 다릅니다.')
        if self.coverage.not_evaluated_mechanisms != list(NOT_EVALUATED_MECHANISMS):
            raise ValueError('미평가 기전 목록이 규칙 프로필과 다릅니다.')
        return self
