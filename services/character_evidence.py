"""Adapt existing decision evidence without calculating activation or impact."""
from copy import deepcopy
from services.branch_dynamics_v3_assembler import RELATION_TYPES
from services.relation_rules import V3_ELEMENT_OVERRIDE_PAIR_TYPES, PAIR_ELEMENT_OVERRIDE_REASON

PILLARS = ('year', 'month', 'day', 'hour')
POSITIONS = dict(year='연', month='월', day='일', hour='시', cycle='')
SCOPES = dict(natal='원국', daewoon='대운', sewoon='세운')


def participant_detail(graph, key):
    node = graph['characters'][key]
    scope = graph['contexts'][node['context_id']]['scope']
    suffix = ('간' if node['kind'] == 'stem' else '지') if scope == 'natal' else (
        '천간' if node['kind'] == 'stem' else '지지')
    ten_god = node['attributes']['ten_god']
    return dict(character_id=key, context_id=node['context_id'], scope=scope,
                position=node['position'], kind=node['kind'], char=node['char'], ten_god=ten_god,
                display_name=f"{SCOPES[scope]} {POSITIONS[node['position']]}{suffix} {node['char']}({ten_god})")


def attach_participant_details(graph):
    for row in graph['relations'].values():
        row['participant_details'] = [participant_detail(graph, p) for p in row['participants']]


def walk_records(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_records(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_records(child)


def _evidence(graph, source, details, members, related_ids=()):
    keys, related = set(members), set(related_ids)
    for record in walk_records(details):
        for field, value in record.items():
            if field == 'pillar' or field.endswith('_pillar') or field.endswith('_pillars'):
                for position in value if isinstance(value, list) else [value]:
                    if isinstance(position, str) and position in PILLARS:
                        keys.add(f'natal.chart.{position}.branch')
        attacker = record.get('clashing_pillar')
        victim = next((record[k] for k in ('clashed_pillar', 'wing_pillar', 'middle_pillar', 'member_pillar')
                       if k in record), None)
        if attacker in PILLARS and victim in PILLARS:
            pair = {f'natal.chart.{p}.branch' for p in (attacker, victim)}
            related.update(rid for rid, r in graph['relations'].items()
                           if r['type'] == 'clash' and set(r['participants']) == pair)
        fallback = record.get('fallback_from')
        if isinstance(fallback, dict):
            related.update(rid for rid, r in graph['relations'].items()
                           if r['type'] == 'trine' and {graph['characters'][p]['char'] for p in r['participants']}
                           == set(fallback['group_branches']))
    for rid in related:
        keys.update(graph['relations'][rid]['participants'])
    return dict(source=deepcopy(source), details=deepcopy(details),
                characters=[participant_detail(graph, p) for p in sorted(keys)],
                related_relation_ids=sorted(related))


def _decision_details(source):
    fields = ('activation_status', 'status_reason', 'status_reasons', 'condition_evidence',
              'activation_rule_id', 'action_rule_id', 'rule_id', 'is_adjacent',
              'element_relation', 'element_direction')
    result = {k: deepcopy(source[k]) for k in fields if k in source}
    if 'formation_evidence' in source:
        result['formation_evidence'] = [
            {k: deepcopy(f[k]) for k in ('pillars', 'structural_roles') if k in f}
            for f in source['formation_evidence']]
    return result


def _self_combine_links(graph, row, source):
    branch = next(p for p in row['participants'] if p.endswith('.branch'))
    return sorted({rid for context in source['related_branch_relations']
                   for rid, relation in graph['relations'].items()
                   if relation['type'] == context['type'] and set(relation['participants']) ==
                   {branch, f"natal.chart.{PILLARS[context['with_index']]}.branch"}})


def attach_natal_evidence(graph, response):
    advanced = response['advanced_analysis']
    dynamics = advanced['branch_dynamics']
    matrix = {r['relation_id']: r for r in advanced['interactions']['matrix']}
    group_sources = {r['relation_id']: (i, r) for i, r in enumerate(dynamics['groups'])}
    for row in graph['relations'].values():
        row['evidence'] = []
        reasons = [row['status_reason']] if row.get('status_reason') else []
        for ref in row['source_refs']:
            source, evidence_ref, related = None, ref, []
            system = ref['system']
            if system == 'interaction_matrix':
                source = matrix[ref['relation_id']]
            elif system == 'branch_dynamics_v3':
                group_id = next((r['relation_id'] for r in row['source_refs']
                                 if r['system'] == 'interaction_matrix' and r['relation_id'] in group_sources), None)
                if group_id:
                    index, source = group_sources[group_id]
                    evidence_ref = dict(system='branch_dynamics', relation_id=group_id,
                                        location=f'advanced_analysis.branch_dynamics.groups[{index}]')
                else:
                    positions = {graph['characters'][p]['position'] for p in row['participants']}
                    for i, pair in enumerate(dynamics['pairwise']):
                        if set(pair['pillars']) != positions:
                            continue
                        for j, event in enumerate(pair['relations']):
                            kind = RELATION_TYPES[event['type']][0]
                            if kind == row['type'] or (row['type'] == 'self_punishment' and kind == 'punishment'):
                                source = event
                                evidence_ref = dict(system='branch_dynamics', relation_id=event['relation_id'],
                                                    location=f'advanced_analysis.branch_dynamics.pairwise[{i}].relations[{j}]')
                                break
            elif system in ('branch_dynamics', 'analysis_details') and ref.get('location'):
                source = advanced if system == 'branch_dynamics' else response
                for part in ref['location'].split('.'):
                    source = source[part]
            if source is None:
                continue
            if system in ('interaction_matrix', 'branch_dynamics_v3'):
                details = _decision_details(source)
                reasons.extend(source.get('status_reasons', []))
                if source.get('status_reason'):
                    reasons.append(source['status_reason'])
            elif system == 'branch_dynamics':
                row['element_relation'] = source['relation']
                details = {k: source[k] for k in ('stem', 'relation')}
            else:
                details = {'records': deepcopy(source)}
                if row['type'] == 'self_combine':
                    related = _self_combine_links(graph, row, source)
            if row.get('status_reason') == PAIR_ELEMENT_OVERRIDE_REASON:
                related = [rid for rid, r in graph['relations'].items()
                           if r['type'] in V3_ELEMENT_OVERRIDE_PAIR_TYPES and r['activation_status'] == 'active'
                           and set(r['participants']) == set(row['participants'])]
                details['overriding_relation_ids'] = related
            details['effective_activation_status'] = row['activation_status']
            row['evidence'].append(_evidence(graph, evidence_ref, details, row['participants'], related))
        row['status_reasons'] = list(dict.fromkeys(reasons))
        if row['type'] == 'half_combine' and row['activation_status'] == 'candidate_only':
            groups = [rid for rid, r in graph['relations'].items() if r['type'] == 'trine'
                      and r['activation_status'] in ('potential', 'conditional', 'detected')
                      and any(set(row['participants']) <= set(f) for f in r['formation_candidates'])]
            if groups:
                row['evidence'].append(_evidence(
                    graph, dict(system='branch_dynamics_v3', relation_id=row['source_relation_id'],
                                location='services.branch_dynamics_v3_assembler.assemble_branch_pairs_v3'),
                    dict(activation_status='candidate_only', effective_activation_status='candidate_only',
                         formation_status='included_in_complete_group', effect_status='structural_only',
                         calculation_status='not_applicable'), row['participants'], groups))
    for key, node in graph['characters'].items():
        if node['rooting'] is None:
            continue
        root, position = node['rooting'], node['position']
        source = advanced['xu_shi_dynamics']['pillars'][position]
        root['reason'], root['transition_reasons'] = source['reason'], deepcopy(source['transition_reasons'])
        root['evidence'] = [_evidence(
            graph, dict(system='analysis_details', location=f'analysis.details.{position}.stem.{field}'),
            {'records': response['analysis']['details'][position]['stem'][field]}, [key, *refs])
            for field, refs in [('root_info', root['root_branch_ids']),
                                ('external_support_info', root['external_support_branch_ids'])]]
