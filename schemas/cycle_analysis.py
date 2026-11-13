from typing import Literal
from pydantic import model_validator
from schemas.character_details import CharacterDetails, Contract


class CycleSelection(Contract):
    mode: Literal['daewoon', 'sewoon']
    daewoon_index: int | None
    sewoon_year: int | None
    daewoon_status: Literal['selected', 'before_first_period']
    period_basis: Literal['legacy_start_year_half_open'] = 'legacy_start_year_half_open'
    sewoon_basis: Literal['calendar_year_ganzhi_no_ipchun'] = 'calendar_year_ganzhi_no_ipchun'
    cycle_relations_status: Literal['candidates_detected'] = 'candidates_detected'
    cycle_relation_rule_version: Literal['1.0.0-draft'] = '1.0.0-draft'


class CycleAnalysis(CharacterDetails):
    selection: CycleSelection

    @model_validator(mode='after')
    def check_selection(self):
        chosen = self.selection
        expected = {'natal.chart'}
        if chosen.daewoon_status == 'selected':
            if chosen.daewoon_index is None or chosen.daewoon_index < 0:
                raise ValueError('선택한 대운 번호가 필요합니다.')
            expected.add(f'daewoon.period_{chosen.daewoon_index}')
        elif chosen.daewoon_index is not None or chosen.mode != 'sewoon':
            raise ValueError('첫 대운 이전 상태는 세운 조회에만 허용됩니다.')
        if chosen.mode == 'sewoon':
            if chosen.sewoon_year is None:
                raise ValueError('선택한 세운 연도가 필요합니다.')
            expected.add(f'sewoon.year_{chosen.sewoon_year}')
        elif chosen.sewoon_year is not None:
            raise ValueError('대운 조회에 세운 선택이 섞였습니다.')
        if set(self.contexts) != expected:
            raise ValueError('선택한 운과 응답 소속이 일치하지 않습니다.')
        for context_id in expected - {'natal.chart'}:
            if self.contexts[context_id].calculation_status != chosen.cycle_relations_status:
                raise ValueError('선택 운의 후보 탐지 상태와 소속 계산 상태가 다릅니다.')
            nodes = {key for key, node in self.characters.items() if node.context_id == context_id}
            if nodes != {f'{context_id}.cycle.stem', f'{context_id}.cycle.branch'}:
                raise ValueError('선택한 운의 천간·지지가 필요합니다.')
        if chosen.daewoon_status == 'selected':
            context = self.contexts[f'daewoon.period_{chosen.daewoon_index}']
            metadata = context.selection
            start = metadata.get('selection_start_year')
            end = metadata.get('selection_end_year_exclusive')
            if (type(metadata.get('index')) is not int or metadata['index'] != chosen.daewoon_index
                    or type(start) is not int or type(end) is not int or start >= end
                    or metadata.get('period_basis') != chosen.period_basis
                    or (chosen.mode == 'sewoon' and not start <= chosen.sewoon_year < end)):
                raise ValueError('대운 선택 번호·연도 범위·소속 메타데이터가 다릅니다.')
        if chosen.mode == 'sewoon':
            metadata = self.contexts[f'sewoon.year_{chosen.sewoon_year}'].selection
            if (type(metadata.get('year')) is not int or metadata['year'] != chosen.sewoon_year
                    or metadata.get('year_basis') != chosen.sewoon_basis
                    or metadata.get('age_basis') != 'counting_age'):
                raise ValueError('세운 선택 연도·기준과 소속 메타데이터가 다릅니다.')
        return self
