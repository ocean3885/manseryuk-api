"""Selection adapter with cross-context candidate detection; impact stays unevaluated."""
from copy import deepcopy
from fastapi import HTTPException
from schemas.cycle_analysis import CycleAnalysis
from services.character_details import assemble_character_details
from services.calculator import get_jijanggan_details
from services.cycle_relations import attach_cycle_relations


def assemble_cycle_analysis(response, *, daewoon_index=None, sewoon_year=None):
    if (daewoon_index is None) == (sewoon_year is None):
        raise HTTPException(400, 'daewoon_index 또는 sewoon_year 중 하나만 지정하세요.')
    periods = response['daewoon']['list']
    annual = None
    if sewoon_year is not None:
        annual = next((item for item in response['cycles']['future_100']
                       if item['year'] == sewoon_year), None)
        if annual is None:
            raise HTTPException(400, '제공되는 세운 연도 범위를 벗어났습니다.')
        # Existing display end_year can overlap the next period. Use start boundaries.
        selected = next((item for i, item in enumerate(periods)
                         if item['start_year'] <= sewoon_year < (
                             periods[i + 1]['start_year'] if i + 1 < len(periods)
                             else item['start_year'] + 10)), None)
        if selected is None and (not periods or sewoon_year >= periods[0]['start_year']):
            raise HTTPException(400, '해당 연도를 포함하는 대운이 없습니다.')
    else:
        selected = next((item for item in periods if item['index'] == daewoon_index), None)
        if selected is None:
            raise HTTPException(400, '제공되는 대운 번호 범위를 벗어났습니다.')

    graph = assemble_character_details(response)
    day_stem = response['four_pillars']['day']['gan']['ch']

    def add_context(scope, instance, label, stem, branch, metadata, unseong):
        context_id = f'{scope}.{instance}'
        graph['contexts'][context_id] = dict(
            scope=scope, instance=instance, label=label,
            calculation_status='not_evaluated', selection=metadata)
        for kind, attributes in [('stem', stem), ('branch', branch)]:
            graph['characters'][f'{context_id}.cycle.{kind}'] = dict(
                context_id=context_id, position='cycle', kind=kind, char=attributes['ch'],
                attributes=deepcopy(attributes),
                pillar_attributes=dict(unseong=unseong,
                                       jijanggan=get_jijanggan_details(day_stem, branch['ch'])),
                analysis={'calculation_status': 'not_evaluated'}, rooting=None,
                relation_ids=[], transmission_relation_ids=[])

    if selected is not None:
        index = periods.index(selected)
        end_exclusive = (periods[index + 1]['start_year'] if index + 1 < len(periods)
                         else selected['start_year'] + 10)
        add_context('daewoon', f'period_{selected["index"]}', '선택 대운',
                    selected['gan_detail'], selected['ji_detail'],
                    {**deepcopy(selected), 'direction': response['daewoon']['direction'],
                     'selection_start_year': selected['start_year'],
                     'selection_end_year_exclusive': end_exclusive,
                     'period_basis': 'legacy_start_year_half_open'}, selected['unseong'])
    if annual is not None:
        add_context('sewoon', f'year_{annual["year"]}', f'{annual["year"]} 세운',
                    annual['gan'], annual['ji'],
                    {'year': annual['year'], 'age': annual['age'],
                     'year_basis': 'calendar_year_ganzhi_no_ipchun'}, annual['unseong'])
    graph['selection'] = dict(
        mode='sewoon' if annual is not None else 'daewoon',
        daewoon_index=selected['index'] if selected is not None else None,
        sewoon_year=sewoon_year,
        daewoon_status='selected' if selected is not None else 'before_first_period')
    attach_cycle_relations(graph)
    return CycleAnalysis.model_validate(graph).model_dump(mode='json')
