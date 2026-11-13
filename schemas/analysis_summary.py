from typing import Literal
from pydantic import Field, model_validator
from schemas.character_details import CharacterDetails, Contract, ACTIVATION_LABELS
from schemas.character_relation_index import ActivationStatus
from schemas.cycle_analysis import CycleSelection

STATUS_LABELS = ACTIVATION_LABELS


class Comparison(Contract):
    baseline: Literal['natal', 'natal_daewoon']
    selected_context_id: str | None
    added_relation_ids: list[str]
    maintained_relation_ids: list[str]
    added_count: int = Field(ge=0)
    maintained_count: int = Field(ge=0)
    total_count: int = Field(ge=0)


class SummaryLine(Contract):
    text: str
    relation_ids: list[str] = Field(min_length=1)
    activation_status: ActivationStatus
    status_label: str
    character_ids: list[str]
    from_character_ids: list[str]
    to_character_ids: list[str]
    change: Literal['added', 'maintained', 'mixed']

    @model_validator(mode='after')
    def check_badge(self):
        if self.status_label != STATUS_LABELS[self.activation_status]:
            raise ValueError('상태 배지와 원본 상태가 다릅니다.')
        return self


class SummaryItem(Contract):
    category: Literal['pair', 'group', 'transmission', 'participation']
    change: Literal['added', 'maintained', 'mixed']
    title: str
    description: str
    character_ids: list[str]
    relation_ids: list[str] = Field(min_length=1)
    related_relation_ids: list[str] = Field(default_factory=list)
    activation_statuses: list[ActivationStatus]
    impact_status: Literal['not_evaluated'] = 'not_evaluated'
    lines: list[SummaryLine] = Field(min_length=1)
    structure_relation_ids: list[str] = Field(default_factory=list)


class AnalysisSummary(Contract):
    schema_version: Literal['1.0-draft']
    summary_rule_version: Literal['1.2.0']
    selection: CycleSelection | None
    comparison: Comparison
    overview: str
    items: dict[str, SummaryItem]
    display_order: list[str]
    character_summary_ids: dict[str, list[str]]
    graph: CharacterDetails

    @model_validator(mode='after')
    def check_evidence(self):
        comparison = self.comparison
        added, maintained = set(comparison.added_relation_ids), set(comparison.maintained_relation_ids)
        relations = self.graph.relations
        selected = comparison.selected_context_id
        expected = {key for key, row in relations.items() if selected in row.context_ids} if selected else set()
        if (added != expected or added & maintained or added | maintained != set(relations)
                or comparison.added_count != len(added) or comparison.maintained_count != len(maintained)
                or comparison.total_count != len(relations)
                or len(comparison.added_relation_ids) != len(added)
                or len(comparison.maintained_relation_ids) != len(maintained)):
            raise ValueError('비교 기준과 추가·유지 관계 수가 맞지 않습니다.')
        scope = self.graph.contexts[selected].scope if selected in self.graph.contexts else None
        if (selected and scope not in ('daewoon', 'sewoon')) or (selected is None) != (self.selection is None):
            raise ValueError('선택 조건과 비교 대상이 맞지 않습니다.')
        if self.selection:
            expected_selected = (f'daewoon.period_{self.selection.daewoon_index}' if self.selection.mode == 'daewoon'
                                 else f'sewoon.year_{self.selection.sewoon_year}')
            if selected != expected_selected:
                raise ValueError('선택한 운과 비교 소속이 다릅니다.')
        expected_baseline = 'natal_daewoon' if scope == 'sewoon' and any(
            c.scope == 'daewoon' for c in self.graph.contexts.values()) else 'natal'
        if comparison.baseline != expected_baseline:
            raise ValueError('운 요약의 비교 기준이 맞지 않습니다.')
        covered = []
        for item in self.items.values():
            refs = item.relation_ids + item.related_relation_ids
            if len(refs) != len(set(refs)) or any(key not in relations for key in refs):
                raise ValueError('요약의 관계 근거가 중복되거나 없습니다.')
            participants = {p for key in refs for p in relations[key].participants}
            if not set(item.character_ids) <= participants or not item.character_ids:
                raise ValueError('요약의 참여 글자 근거가 맞지 않습니다.')
            if len(item.character_ids) != len(set(item.character_ids)):
                raise ValueError('요약의 참여 글자가 중복됩니다.')
            if item.category == 'participation':
                if len(item.character_ids) != 1 or any(
                        item.character_ids[0] not in relations[key].participants for key in refs):
                    raise ValueError('동시 참여 요약의 글자가 모든 근거 관계에 참여해야 합니다.')
            elif set(item.character_ids) != participants:
                raise ValueError('요약의 참여 글자가 누락되었습니다.')
            statuses = {relations[key].activation_status for key in refs}
            if set(item.activation_statuses) != statuses:
                raise ValueError('요약 상태와 원본 관계 상태가 다릅니다.')
            line_refs = []
            for line in item.lines:
                if any(key not in refs for key in line.relation_ids):
                    raise ValueError('표시 문장의 관계 근거가 카드에 없습니다.')
                if any(relations[key].activation_status != line.activation_status for key in line.relation_ids):
                    raise ValueError('표시 문장의 상태가 원본과 다릅니다.')
                expected_members = {p for key in line.relation_ids for p in relations[key].participants}
                expected_sources = {relations[key].direction.from_character for key in line.relation_ids if relations[key].direction}
                expected_targets = {relations[key].direction.to_character for key in line.relation_ids if relations[key].direction}
                for actual, expected_ids in ((line.character_ids, expected_members),
                                             (line.from_character_ids, expected_sources),
                                             (line.to_character_ids, expected_targets)):
                    if len(actual) != len(set(actual)) or set(actual) != expected_ids:
                        raise ValueError('표시 문장의 참여 글자·방향이 원본과 다릅니다.')
                line_change = ('added' if set(line.relation_ids) <= added else
                               'maintained' if set(line.relation_ids) <= maintained else 'mixed')
                if line.change != line_change:
                    raise ValueError('표시 문장의 기존·추가 구분이 다릅니다.')
                line_refs.extend(line.relation_ids)
            if len(line_refs) != len(set(line_refs)) or set(line_refs) != set(refs):
                raise ValueError('표시 문장의 근거가 중복되거나 누락되었습니다.')
            expected_structures = {key for key in refs if relations[key].formation_candidates}
            if len(item.structure_relation_ids) != len(set(item.structure_relation_ids)) or set(item.structure_relation_ids) != expected_structures:
                raise ValueError('주된 구조와 구성 관계가 구분되지 않았습니다.')
            primary = set(item.relation_ids)
            change = 'added' if primary <= added else 'maintained' if primary <= maintained else 'mixed'
            if item.change != change:
                raise ValueError('요약의 추가·유지 분류가 다릅니다.')
            if item.category != 'participation':
                covered.extend(item.relation_ids)
        target = added if selected else maintained
        if len(covered) != len(set(covered)) or set(covered) != target:
            raise ValueError('관계 요약에 누락·중복이 있습니다.')
        if len(self.display_order) != len(set(self.display_order)) or set(self.display_order) != set(self.items):
            raise ValueError('표시 순서에 요약 카드가 누락·중복되었습니다.')
        if set(self.character_summary_ids) != set(self.graph.characters):
            raise ValueError('글자별 요약 참조 대상이 맞지 않습니다.')
        for key, ids in self.character_summary_ids.items():
            expected_ids = {sid for sid, item in self.items.items() if key in item.character_ids}
            if len(ids) != len(set(ids)) or set(ids) != expected_ids:
                raise ValueError('글자별 요약 참조가 맞지 않습니다.')
        return self
