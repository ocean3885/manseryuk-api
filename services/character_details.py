"""Adapt existing calculations without recomputing or mutating domain results."""
from copy import deepcopy
from schemas.character_details import CharacterDetails
from services.character_relation_index import assemble_character_relation_index_from_response


def assemble_character_details(response):
    index = assemble_character_relation_index_from_response(response)
    context_id = 'natal.chart'
    qualify = lambda old: f'{context_id}.{old}'
    relation_ids = {r['relation_id']: f'{context_id}:{r["relation_id"]}' for r in index['relations']}
    relations = {}
    for source in index['relations']:
        row = deepcopy(source)
        old_id = row['relation_id']
        row['relation_id'] = relation_ids[old_id]
        row['source_relation_id'] = old_id
        row['context_ids'] = [context_id]
        row['participants'] = [qualify(p) for p in row['participants']]
        row['formation_candidates'] = [[qualify(p) for p in group] for group in row['formation_candidates']]
        if row['direction']:
            for key in ('from_character', 'to_character'):
                row['direction'][key] = qualify(row['direction'][key])
        # source_refs intentionally retain IDs/locations in the original calculation.
        relations[row['relation_id']] = row
    characters = {}
    for old_id, source in index['characters'].items():
        position, kind = old_id.split('.')
        pillar = deepcopy(response['four_pillars'][position])
        attributes = pillar.pop('gan' if kind == 'stem' else 'ji')
        pillar.pop('ji' if kind == 'stem' else 'gan')
        rooting = deepcopy(source['stem_state'])
        if rooting:
            for field in ('root_branch_ids', 'affected_root_branch_ids', 'external_support_branch_ids'):
                rooting[field] = [qualify(p) for p in rooting[field]]
        ids = [relation_ids[rid] for rid in source['relation_ids']]
        characters[qualify(old_id)] = {
            'context_id': context_id, 'position': position, 'kind': kind,
            'char': source['char'], 'attributes': attributes, 'pillar_attributes': pillar,
            'analysis': deepcopy(response['analysis']['details'][position][kind]),
            'rooting': rooting, 'relation_ids': ids,
            'transmission_relation_ids': [rid for rid in ids if relations[rid]['type'] == 'transmission'],
        }
    return CharacterDetails.model_validate({
        'schema_version': '1.0-draft',
        'contexts': {context_id: {'scope': 'natal', 'instance': 'chart', 'label': '원국',
                                 'calculation_status': 'calculated', 'selection': {
                                     'birth_date_solar': response['meta']['birth_date_solar'],
                                     'birth_time': response['meta']['birth_time'],
                                 }}},
        'characters': characters, 'relations': relations,
        'coverage': {**index['coverage'], 'calculated_scopes': ['natal'],
                     'detected_only_relation_ids': [relation_ids[rid] for rid in index['coverage']['detected_only_relation_ids']],
                     'not_evaluated_scopes': ['daewoon', 'sewoon']},
    }).model_dump(mode='json')
