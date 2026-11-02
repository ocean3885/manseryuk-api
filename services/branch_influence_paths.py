"""지지별 출처 경로의 내부 자료형과 읽기 전용 조립기.

기존 세력 계산을 다시 수행하거나 구조 후보를 수치화하지 않는다.
"""

from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from services.constants import JIJANGGAN_DETAILED


PILLARS = ('year', 'month', 'day', 'hour')
Pillar = Literal['year', 'month', 'day', 'hour']
BACKGROUND_MECHANISMS = {
    'same_element': 'same_element',
    'generates': 'element_generate',
    'generated_by': 'element_outflow',
    'controls': 'element_control',
    'controlled_by': 'element_outward_control',
}


class _PathModel(BaseModel):
    model_config = ConfigDict(extra='forbid')


class PathTarget(_PathModel):
    pillar: Pillar
    component: Literal['branch', 'hidden_stem']
    stem: str | None

    @model_validator(mode='after')
    def check_component(self):
        if (self.component == 'branch') != (self.stem is None):
            raise ValueError('지지 대상은 stem=null, 지장간 대상은 stem이 필요합니다.')
        return self


class PathQuantity(_PathModel):
    unit: Literal['adjustment_ratio', 'power_delta']
    value: float

    @field_validator('value', mode='before')
    @classmethod
    def check_value(cls, value):
        if (not isinstance(value, (int, float)) or isinstance(value, bool)
                or not isfinite(value)):
            raise ValueError('경로 수치는 유한해야 합니다.')
        return value


class PathEvidenceRef(_PathModel):
    kind: Literal['interaction', 'formation', 'rule', 'case']
    id: str


class BranchInfluencePath(_PathModel):
    path_id: str
    source_pillars: list[Pillar] = Field(min_length=1)
    target: PathTarget
    stage: Literal['pre_relation_background', 'structural_context', 'relation_effect']
    mechanism: str
    evidence_level: Literal['calculated', 'source_interpretation', 'expert_hypothesis']
    accounting_decision: Literal[
        'include', 'exclude', 'replace', 'separate_effect', 'undetermined',
    ]
    quantity: PathQuantity | None
    evidence_refs: list[PathEvidenceRef]
    overlaps_path_ids: list[str]
    replaces_path_ids: list[str]
    depends_on_path_ids: list[str]

    @model_validator(mode='after')
    def check_accounting(self):
        if (not self.path_id.startswith('path:') or not self.mechanism
                or self.source_pillars != sorted(set(self.source_pillars),
                                                 key=PILLARS.index)):
            raise ValueError('경로 ID·기전·출처 위치가 잘못되었습니다.')
        if self.accounting_decision == 'undetermined':
            if self.quantity is not None:
                raise ValueError('미정 경로의 수치는 null이어야 합니다.')
        elif self.quantity is None:
            raise ValueError('계상 경로에는 수치가 필요합니다.')
        if self.quantity is not None and self.evidence_level != 'calculated':
            raise ValueError('교재·가설 경로에 계산된 수치를 줄 수 없습니다.')
        if self.accounting_decision == 'exclude' and self.quantity.value != 0:
            raise ValueError('차단 경로의 수치는 0이어야 합니다.')
        if self.accounting_decision == 'replace' and not self.replaces_path_ids:
            raise ValueError('대체 경로에는 대체 대상 ID가 필요합니다.')
        if (self.stage == 'pre_relation_background' and self.quantity is not None
                and self.quantity.unit != 'adjustment_ratio'):
            raise ValueError('일반 배경의 단위는 adjustment_ratio입니다.')
        if (self.stage == 'relation_effect' and self.quantity is not None
                and self.quantity.unit != 'power_delta'):
            raise ValueError('관계 적용량의 단위는 power_delta입니다.')
        return self


def validate_influence_paths(paths, branches, *, interaction_ids=(),
                             formation_ids=(), rule_ids=(), case_ids=()):
    """경로의 대상·근거·겹침·대체·의존 참조를 원국 안에서 검증한다."""
    if len(branches) != 4:
        raise ValueError('원국에는 지지 네 개가 필요합니다.')
    items = [BranchInfluencePath.model_validate(item) for item in paths]
    by_id = {item.path_id: item for item in items}
    if len(by_id) != len(items):
        raise ValueError('중복된 출처 경로 ID가 있습니다.')
    allowed_refs = {
        'interaction': set(interaction_ids),
        'formation': set(formation_ids),
        'rule': set(rule_ids),
        'case': set(case_ids),
    }
    included_keys = set()
    for item in items:
        branch = branches[PILLARS.index(item.target.pillar)]
        if item.target.component == 'hidden_stem' and item.target.stem not in {
                hidden['char'] for hidden in JIJANGGAN_DETAILED[branch]}:
            raise ValueError(f'{item.path_id}: 대상 지지에 없는 지장간입니다.')
        for ref in item.evidence_refs:
            if ref.id not in allowed_refs[ref.kind]:
                raise ValueError(f'{item.path_id}: 없는 근거 참조 {ref.kind}:{ref.id}')
        for field in ('overlaps_path_ids', 'replaces_path_ids', 'depends_on_path_ids'):
            refs = getattr(item, field)
            if len(refs) != len(set(refs)) or item.path_id in refs:
                raise ValueError(f'{item.path_id}: {field}가 중복되거나 자기 자신을 가리킵니다.')
            if any(ref not in by_id for ref in refs):
                raise ValueError(f'{item.path_id}: {field}에 없는 경로가 있습니다.')
        if item.accounting_decision != 'replace' and item.replaces_path_ids:
            raise ValueError(f'{item.path_id}: replace가 아닌 경로에 대체 대상이 있습니다.')
        for ref in item.replaces_path_ids:
            if by_id[ref].target != item.target:
                raise ValueError(f'{item.path_id}: 다른 대상을 대체할 수 없습니다.')
            if ref not in item.overlaps_path_ids:
                raise ValueError(f'{item.path_id}: 대체 대상은 겹침 경로에도 있어야 합니다.')
        if item.accounting_decision == 'include':
            key = (item.stage, tuple(item.source_pillars), item.target.pillar,
                   item.target.component, item.target.stem, item.mechanism)
            if key in included_keys:
                raise ValueError(f'{item.path_id}: 같은 출처·대상의 보정을 중복 계상합니다.')
            included_keys.add(key)
            if any(by_id[ref].accounting_decision == 'include'
                   for ref in item.overlaps_path_ids):
                raise ValueError(f'{item.path_id}: 겹치는 기여를 중복 계상합니다.')
    visiting = set()
    visited = set()

    def visit(path_id):
        if path_id in visiting:
            raise ValueError('출처 경로의 의존·대체 참조에 순환이 있습니다.')
        if path_id in visited:
            return
        visiting.add(path_id)
        item = by_id[path_id]
        for ref in item.depends_on_path_ids + item.replaces_path_ids:
            visit(ref)
        visiting.remove(path_id)
        visited.add(path_id)

    for path_id in by_id:
        visit(path_id)
    return [item.model_dump() for item in items]


def build_influence_paths(branches, branch_strengths, pairs, groups=(),
                          *, interpretation_candidates=(), case_ids=()):
    """기존 일반 보정과 구조 후보를 경로로 옮기되 새 세력은 계산하지 않는다."""
    interaction_ids = {relation['relation_id'] for pair in pairs
                       for relation in pair['relations']}
    interaction_ids.update(group['group_id'] for group in groups)
    formation_ids = {formation['formation_id'] for group in groups
                     for formation in group['formation_candidates']}
    paths = []
    for index, target in enumerate(PILLARS):
        strength = branch_strengths[target]
        if strength['branch'] != branches[index]:
            raise ValueError(f'{target}: 세력 근거와 원국의 지지가 다릅니다.')
        for ambient in strength['strength_evidence']['surroundings']:
            source = ambient['source_pillar']
            background_id = f'path:background:{source}:{target}:branch'
            accounting = ambient['accounting_path']
            if accounting == 'elemental_background':
                decision = 'include'
                value = ambient['adjustment_ratio']
            elif accounting == 'suppressed_by_active_structure':
                decision, value = 'exclude', 0.0
            elif accounting == 'deferred_by_element_rule':
                decision = ('undetermined' if ambient['activation_status'] == 'conditional'
                            else 'exclude')
                value = None if decision == 'undetermined' else 0.0
            else:
                raise ValueError(f'{background_id}: 모르는 배경 계상 경로입니다.')
            if decision == 'include' and value is None:
                raise ValueError(f'{background_id}: 이미 계상한 보정값이 없습니다.')
            evidence_ids = ambient['accounting_relation_ids']
            paths.append({
                'path_id': background_id,
                'source_pillars': [source],
                'target': {'pillar': target, 'component': 'branch', 'stem': None},
                'stage': 'pre_relation_background',
                'mechanism': BACKGROUND_MECHANISMS[ambient['relation']],
                'evidence_level': 'calculated',
                'accounting_decision': decision,
                'quantity': ({'unit': 'adjustment_ratio', 'value': value}
                             if value is not None else None),
                'evidence_refs': [{'kind': 'interaction', 'id': ref}
                                  for ref in evidence_ids],
                'overlaps_path_ids': [],
                'replaces_path_ids': [],
                'depends_on_path_ids': [],
            })
            if ambient['structural_effect_status'] == 'unresolved':
                for relation in ambient['related_relations']:
                    if relation['activation_status'] != 'active':
                        continue
                    paths.append({
                        'path_id': (f"path:structural:{relation['relation_id']}:"
                                    f'{source}:{target}:branch'),
                        'source_pillars': [source],
                        'target': {'pillar': target, 'component': 'branch',
                                   'stem': None},
                        'stage': 'structural_context',
                        'mechanism': 'active_pair_structure_candidate',
                        'evidence_level': 'calculated',
                        'accounting_decision': 'undetermined',
                        'quantity': None,
                        'evidence_refs': [{'kind': 'interaction',
                                           'id': relation['relation_id']}],
                        'overlaps_path_ids': [background_id],
                        'replaces_path_ids': [],
                        'depends_on_path_ids': [],
                    })
    for group in groups:
        if group['formation_status'] == 'suppressed':
            continue
        for formation in group['formation_candidates']:
            members = formation['pillars']
            for target in members:
                paths.append({
                    'path_id': f"path:group:{formation['formation_id']}:{target}:branch",
                    'source_pillars': members,
                    'target': {'pillar': target, 'component': 'branch', 'stem': None},
                    'stage': 'structural_context',
                    'mechanism': f"{group['type']}_participation_candidate",
                    'evidence_level': 'calculated',
                    'accounting_decision': 'undetermined',
                    'quantity': None,
                    'evidence_refs': [
                        {'kind': 'interaction', 'id': group['group_id']},
                        {'kind': 'formation', 'id': formation['formation_id']},
                    ],
                    'overlaps_path_ids': [
                        f'path:background:{source}:{target}:branch'
                        for source in members if source != target
                    ],
                    'replaces_path_ids': [],
                    'depends_on_path_ids': [],
                })
    paths.extend(interpretation_candidates)
    return validate_influence_paths(paths, branches, interaction_ids=interaction_ids,
                                    formation_ids=formation_ids, case_ids=case_ids)
