"""해설 검색 패턴·조건 계약. 명리 판정이나 실행할 조건식을 저장하지 않는다."""
from hashlib import sha256
import json
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator, model_validator

TEN_STARS = ('비견', '겁재', '식신', '상관', '편재', '정재', '편관', '정관', '편인', '정인')
RELATION_TYPES = {
    'stem': {'combine', 'clash', 'control'},
    'branch': {'combine', 'clash', 'pierce', 'break', 'punishment', 'self_punishment',
               'half_combine', 'arch_combine', 'hidden_combine', 'generate', 'control', 'same_branch'},
    'group': {'trine', 'square', 'triple_punishment'},
    'same_pillar': {'element', 'self_combine'},
}
FACT_VALUES = {
    'scope': ('natal', 'cross_context'),
    'activation_status': ('detected', 'candidate_only', 'potential', 'conditional', 'suppressed', 'active'),
    'element_relation': ('stem_generates_branch', 'branch_generates_stem', 'stem_controls_branch',
                         'branch_controls_stem', 'same_element'),
    'is_adjacent': bool,
    'has_day_master': bool,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def validate_facts(value: dict) -> dict:
    for key, item in value.items():
        allowed = FACT_VALUES.get(key)
        if allowed is None:
            raise ValueError(f'지원하지 않는 검색 조건: {key}')
        if (allowed is bool and type(item) is not bool) or (
                allowed is not bool and (not isinstance(item, str) or item not in allowed)):
            raise ValueError(f'{key}: 검색 조건의 값이나 자료형이 잘못됐습니다.')
    return dict(value)


class InterpretationPattern(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    layer: Literal['stem', 'branch', 'group', 'same_pillar']
    relation_type: str
    participant_pattern: tuple[str, ...]

    @field_validator('participant_pattern')
    @classmethod
    def normalize(cls, value: tuple[str, ...], info: ValidationInfo):
        layer, kind = info.data.get('layer'), info.data.get('relation_type')
        if layer not in RELATION_TYPES or kind not in RELATION_TYPES[layer]:
            raise ValueError('지원하지 않는 관계 계층·종류입니다.')
        if len(value) != (3 if layer == 'group' else 2) or any(s not in TEN_STARS for s in value):
            raise ValueError('참여 십성의 개수·이름이 잘못됐습니다. 일간 본인은 비견과 별도 조건으로 조회합니다.')
        if layer != 'same_pillar' and kind not in ('generate', 'control'):
            return tuple(sorted(value, key=TEN_STARS.index))
        return value

    @property
    def pattern_json(self) -> str:
        return canonical_json(self.participant_pattern)


class InterpretationRule(InterpretationPattern):
    rule_id: str
    conditions_json: dict[str, Any] = Field(default_factory=dict)
    explanation: str | None = None
    content_status: Literal['empty', 'draft', 'ready'] = 'empty'

    @field_validator('conditions_json')
    @classmethod
    def check_conditions(cls, value):
        return validate_facts(value)

    @model_validator(mode='after')
    def check_content_and_identity(self):
        if self.rule_id != rule_id_for(self.layer, self.relation_type,
                                       self.participant_pattern, self.conditions_json):
            raise ValueError('규칙 ID와 정규화된 검색 패턴·조건이 다릅니다.')
        if ((self.content_status == 'empty' and self.explanation is not None) or
                (self.content_status != 'empty' and
                 (not isinstance(self.explanation, str) or not self.explanation.strip()))):
            raise ValueError('해설 내용과 작성 상태가 맞지 않습니다.')
        return self


class InterpretationQuery(InterpretationPattern):
    facts: dict[str, Any] = Field(default_factory=lambda: {'scope': 'natal'})

    @field_validator('facts')
    @classmethod
    def check_facts(cls, value):
        return validate_facts(value)


def rule_id_for(layer, kind, participants, conditions) -> str:
    pattern = InterpretationPattern(layer=layer, relation_type=kind, participant_pattern=participants)
    identity = {**pattern.model_dump(), 'conditions_json': validate_facts(conditions)}
    return 'interpretation:' + sha256(canonical_json(identity).encode()).hexdigest()


def empty_rule(layer, kind, participants, conditions=None) -> InterpretationRule:
    conditions = {'scope': 'natal'} if conditions is None else conditions
    return InterpretationRule(layer=layer, relation_type=kind, participant_pattern=participants,
                              conditions_json=conditions,
                              rule_id=rule_id_for(layer, kind, participants, conditions))
