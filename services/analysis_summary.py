"""Evidence-backed templates; no scoring, causal interpretation or extra chart calculation."""
from collections import defaultdict
from hashlib import sha256
from schemas.analysis_summary import AnalysisSummary, STATUS_LABELS
from services.character_details import assemble_character_details
from services.cycle_analysis import assemble_cycle_analysis
from core.api_errors import selection_error

NAMES = dict(combine='합', clash='충', control='극', pierce='천', break_='파',
             punishment='형', self_punishment='자형', half_combine='반합', arch_combine='공합',
             hidden_combine='암합', generate='생', same_branch='동일 지지', trine='삼합',
             square='방합', triple_punishment='삼형', transmission='투간', element='동주 오행 관계',
             self_combine='자합')
NAMES['break'] = NAMES.pop('break_')
STATUS_NAMES = STATUS_LABELS
SCOPE_NAMES = dict(natal='원국', daewoon='대운', sewoon='세운')
POSITIONS = dict(year='연', month='월', day='일', hour='시', cycle='')


def summarize_graph(graph):
    """Accept an existing graph, allowing deterministic unit tests without calendar I/O."""
    selection = graph.get('selection')
    mode = selection['mode'] if selection else None
    selected = next((key for key, context in graph['contexts'].items() if context['scope'] == mode), None)
    relations, characters = graph['relations'], graph['characters']
    added = {key for key, row in relations.items() if selected in row['context_ids']} if selected else set()
    maintained = set(relations) - added
    target = added if selected else maintained
    baseline = 'natal_daewoon' if mode == 'sewoon' and any(
        c['scope'] == 'daewoon' for c in graph['contexts'].values()) else 'natal'

    def order(key):
        node = characters[key]
        return (('natal', 'daewoon', 'sewoon').index(graph['contexts'][node['context_id']]['scope']),
                ('year', 'month', 'day', 'hour', 'cycle').index(node['position']), node['kind'], key)

    def label(key):
        node = characters[key]
        scope = graph['contexts'][node['context_id']]['scope']
        return SCOPE_NAMES[scope] + ' ' + POSITIONS[node['position']] + (
            ('천간' if node['kind'] == 'stem' else '지지') if scope != 'natal' else ('간' if node['kind'] == 'stem' else '지')) + f" {node['char']}"

    groups = sorted(key for key in target if relations[key]['formation_candidates'])
    owners, related = {}, defaultdict(set)
    component_types = {'trine': {'half_combine'}, 'triple_punishment': {'punishment'}}
    for gid in groups:
        group = relations[gid]
        for rid in sorted(relations):
            row = relations[rid]
            if row['type'] in component_types.get(group['type'], set()) and len(row['participants']) == 2 and any(
                set(row['participants']) <= set(formation) for formation in group['formation_candidates']):
                if rid not in target:
                    related[gid].add(rid)
                elif rid not in owners:
                    owners[rid] = gid
                else:
                    related[gid].add(rid)

    items = {}

    def add(category, ids, related_ids=(), focal=None):
        ids, related_ids = sorted(ids), sorted(related_ids)
        refs = ids + related_ids
        participants = sorted({p for rid in refs for p in relations[rid]['participants']}, key=order)
        statuses = sorted({relations[rid]['activation_status'] for rid in refs})
        change = 'added' if set(ids) <= added else 'maintained' if set(ids) <= maintained else 'mixed'
        prefix = '추가' if change == 'added' else '기존' if change == 'maintained' else '기존·추가'
        primary_types = sorted({relations[rid]['type'] for rid in ids})
        names = '·'.join(NAMES.get(kind, kind) for kind in primary_types)
        def relation_text(rid):
            row = relations[rid]
            if row['formation_candidates']:
                return ' / '.join('·'.join(label(key) for key in sorted(formation, key=order))
                                  for formation in row['formation_candidates']) + f" — {NAMES[row['type']]}"
            if row['direction']:
                direction = row['direction']
                return label(direction['from_character']) + ' → ' + label(direction['to_character']) + f" — {NAMES.get(row['type'], row['type'])}"
            return ' ↔ '.join(label(key) for key in sorted(row['participants'], key=order)) + f" — {NAMES.get(row['type'], row['type'])}"

        lines = []
        transmissions = defaultdict(list)
        for rid in refs:
            row = relations[rid]
            if row['type'] == 'transmission':
                transmissions[(row['direction']['to_character'], row['hidden_stem'], row['activation_status'])].append(rid)
            else:
                lines.append(dict(text=relation_text(rid), relation_ids=[rid],
                                  activation_status=row['activation_status'], status_label=STATUS_NAMES[row['activation_status']]))
        # Merge targets only when every target has exactly the same source positions.
        complete = defaultdict(list)
        for (target, hidden, status), tids in sorted(transmissions.items()):
            sources = tuple(sorted({relations[rid]['direction']['from_character'] for rid in tids}, key=order))
            complete[(sources, characters[target]['context_id'], hidden, status)].append((target, tids))
        for (sources, target_context, hidden, status), targets in sorted(complete.items()):
            text = '·'.join(label(key) for key in sources) + f'의 지장간 {hidden} → ' + '·'.join(
                label(key) for key, _ in sorted(targets, key=lambda entry: order(entry[0])))
            lines.append(dict(text=text, relation_ids=sorted(rid for _, tids in targets for rid in tids),
                              activation_status=status, status_label=STATUS_NAMES[status]))
        for line in lines:
            rows = [relations[rid] for rid in line['relation_ids']]
            line['character_ids'] = sorted({p for row in rows for p in row['participants']}, key=order)
            line['from_character_ids'] = sorted({row['direction']['from_character'] for row in rows if row['direction']}, key=order)
            line['to_character_ids'] = sorted({row['direction']['to_character'] for row in rows if row['direction']}, key=order)
            line['change'] = ('added' if set(line['relation_ids']) <= added else
                              'maintained' if set(line['relation_ids']) <= maintained else 'mixed')
        structure_ids = sorted(rid for rid in refs if relations[rid]['formation_candidates'])
        if category == 'participation':
            title = f'{label(focal)}에 추가된 관계' if selected else f'{label(focal)}의 관계'
            description = f'{names} 관계에 참여합니다.'
            display_participants = [focal]
        elif category == 'group':
            structures = [relations[rid] for rid in structure_ids]
            structure_names = '·'.join(sorted({NAMES.get(row['type'], row['type']) for row in structures}))
            title = f'{prefix} {structure_names} 구조'
            description = '·'.join(label(key) for key in participants) + f' — {structure_names}'
            # The main structure is shown first; component statuses stay on their own lines.
            lines.sort(key=lambda line: (not bool(set(line['relation_ids']) & set(structure_ids)), line['relation_ids']))
            display_participants = participants
        else:
            family = '천간' if all(characters[key]['kind'] == 'stem' for key in participants) else '지지' if all(characters[key]['kind'] == 'branch' for key in participants) else ''
            title = f'{prefix} {family + " " if family and category == "pair" else ""}{names} {len(ids)}건'
            description = lines[0]['text'] if len(lines) == 1 else f'{names} {len(ids)}건'
            display_participants = participants
        identity = category + ':' + (focal or '') + ':' + '|'.join(ids)
        sid = 'summary:' + sha256(identity.encode()).hexdigest()[:20]
        items[sid] = dict(category=category, change=change, title=title, description=description,
                          character_ids=display_participants, relation_ids=ids, related_relation_ids=related_ids,
                          activation_statuses=statuses, impact_status='not_evaluated',
                          lines=lines, structure_relation_ids=structure_ids)

    # Group structures first; attached pairs remain traceable without separate repeated cards.
    for gid in groups:
        children = [rid for rid, owner in owners.items() if owner == gid]
        add('group', [gid, *children], related[gid])
    buckets = defaultdict(list)
    for rid in sorted(target - set(groups) - set(owners)):
        row = relations[rid]
        category = 'transmission' if row['type'] == 'transmission' else 'pair'
        family = tuple(sorted(characters[key]['kind'] for key in row['participants']))
        buckets[(category, row['type'], tuple(sorted(row['context_ids'])), family)].append(rid)
    for (category, kind, contexts, family), ids in sorted(buckets.items()):
        add(category, ids)
    for key in sorted(characters, key=order):
        ids = sorted(rid for rid in target if key in relations[rid]['participants'])
        if len({relations[rid]['type'] for rid in ids}) >= 2 and (not selected or set(ids) & added):
            add('participation', ids, focal=key)
    if selected:
        overview = f'{SCOPE_NAMES[mode]} 관련 관계 {len(added)}건을 추가로 확인했습니다. 기존 관계 {len(maintained)}건도 함께 제공합니다.'
    else:
        overview = f'원국의 등록된 관계 {len(maintained)}건을 구조별로 정리했습니다.'
    def card_order(sid):
        item = items[sid]
        if item['category'] == 'group':
            section = 0
        elif item['category'] == 'pair':
            kinds = {characters[key]['kind'] for key in item['character_ids']}
            section = 1 if kinds == {'stem'} else 2 if kinds == {'branch'} else 3
        else:
            section = 4 if item['category'] == 'transmission' else 5
        return (section, tuple(order(key) for key in item['character_ids']), item['relation_ids'], sid)

    display_order = sorted(items, key=card_order)
    items = {sid: items[sid] for sid in display_order}
    return AnalysisSummary.model_validate(dict(
        schema_version='1.0-draft', summary_rule_version='1.2.0', selection=selection,
        comparison=dict(baseline=baseline, selected_context_id=selected,
                        added_relation_ids=sorted(added), maintained_relation_ids=sorted(maintained),
                        added_count=len(added), maintained_count=len(maintained), total_count=len(relations)),
        overview=overview, items=items, display_order=display_order,
        character_summary_ids={key: [sid for sid, item in items.items() if key in item['character_ids']]
                               for key in sorted(characters, key=order)},
        graph={key: value for key, value in graph.items() if key != 'selection'},
    )).model_dump(mode='json')


def assemble_analysis_summary(response, *, daewoon_index=None, sewoon_year=None):
    if daewoon_index is not None and sewoon_year is not None:
        raise selection_error()
    graph = assemble_character_details(response) if daewoon_index is None and sewoon_year is None else assemble_cycle_analysis(
        response, daewoon_index=daewoon_index, sewoon_year=sewoon_year)
    return summarize_graph(graph)
