"""Cross-context presence detection, without natal adjacency or impact assumptions."""
from itertools import combinations
from services.constants import JIJANGGAN_DETAILED
from services.five_elements import BRANCH_ELEMENT_MAP
from services import relation_rules as rules

CYCLE_RELATION_RULE_VERSION = '1.0.0-draft'
BRANCH_REPEAT_PRESENCE = 'distinct_positions_same_branch'


def detect_cycle_relations(characters):
    """Return stable rows for mixed contexts only; never mutate input nodes."""
    rows = {}
    nodes = sorted(characters)

    def emit(family, kind, members, table, *, element=None, direction=None,
             hidden_stem=None, formation=False):
        members = sorted(members)
        contexts = sorted({characters[key]['context_id'] for key in members})
        if len(contexts) < 2:
            return
        rid = 'cycle:' + family + ':' + kind + ':' + '|'.join(members)
        fact = kind in ('transmission', 'generate', 'control', 'same_branch')
        row = dict(
            relation_id=rid, source_relation_id=rid, type=kind, participants=members,
            context_ids=contexts, activation_status='detected' if fact else 'candidate_only',
            status_reason='cycle_presence_only_activation_and_impact_not_evaluated',
            direction=direction, candidate_element=element, hidden_stem=hidden_stem,
            formation_candidates=[members] if formation else [],
            rule_ids=[f'cycle:presence:{table}:{CYCLE_RELATION_RULE_VERSION}',
                      f'cycle:registered_tables:{rules.RULE_VERSION}'],
            source_refs=[dict(system='cycle_relation_rules', relation_id=None, location=(
                f'services.constants.{table}' if table == 'JIJANGGAN_DETAILED' else
                f'services.cycle_relations.{table}' if table == 'BRANCH_REPEAT_PRESENCE' else
                f'services.relation_rules.{table}'))])
        if rid in rows and rows[rid] != row:
            raise ValueError(f'운 관계 ID에 서로 다른 결과가 겹쳤습니다: {rid}')
        rows[rid] = row

    stems = [key for key in nodes if characters[key]['kind'] == 'stem']
    branches = [key for key in nodes if characters[key]['kind'] == 'branch']
    for left, right in combinations(stems, 2):
        a, b = characters[left]['char'], characters[right]['char']
        pair = frozenset((a, b))
        for registered, element in rules.STEM_COMBINATIONS.items():
            if pair == frozenset(registered):
                emit('stem', 'combine', [left, right], 'STEM_COMBINATIONS', element=element)
        if any(pair == frozenset(p) for p in rules.STEM_CONFLICTS):
            emit('stem', 'clash', [left, right], 'STEM_CONFLICTS')
        for source, target, x, y in [(left, right, a, b), (right, left, b, a)]:
            if (x, y) in rules.STEM_RESTRAIN:
                emit('stem', 'control', [left, right], 'STEM_RESTRAIN',
                     direction=dict(from_character=source, to_character=target, basis='rule_fixed'))

    tables = [('combine', 'SIX_HAPS'), ('clash', 'CHUNGS'), ('pierce', 'CHEONS'),
              ('break', 'BREAKS'), ('half_combine', 'HALF_HAPS'),
              ('arch_combine', 'GONG_HAPS'), ('hidden_combine', 'HIDDEN_STEM_HAPS')]
    for left, right in combinations(branches, 2):
        a, b = characters[left]['char'], characters[right]['char']
        pair = frozenset((a, b))
        for kind, table in tables:
            registered = getattr(rules, table)
            for entry in registered:
                if pair != frozenset(entry):
                    continue
                value = registered[entry] if isinstance(registered, dict) else None
                element = value if isinstance(value, str) else value.get('element') if isinstance(value, dict) else None
                emit('branch', kind, [left, right], table, element=element)
        for category, entries in rules.PUNISHMENTS.items():
            if any(sorted((a, b)) == sorted(entry) for entry in entries):
                emit('branch', 'self_punishment' if category == '자진형' else 'punishment',
                     [left, right], 'PUNISHMENTS')
        if a == b:
            emit('branch', 'same_branch', [left, right], 'BRANCH_REPEAT_PRESENCE')
        for source, target, x, y in [(left, right, a, b), (right, left, b, a)]:
            source_element, target_element = BRANCH_ELEMENT_MAP[x], BRANCH_ELEMENT_MAP[y]
            kind = ('generate' if rules.GENERATES[source_element] == target_element else
                    'control' if rules.GENERATES[rules.GENERATES[source_element]] == target_element else None)
            if kind:
                emit('branch', kind, [left, right], 'GENERATES',
                     direction=dict(from_character=source, to_character=target, basis='elemental'))

    for members in combinations(branches, 3):
        chars = {characters[key]['char'] for key in members}
        if len(chars) != 3:
            continue
        for kind, table in [('trine', 'THREE_HAPS'), ('square', 'SQUARE_HAPS'),
                            ('triple_punishment', 'THREE_PUNISHMENTS')]:
            for entry, value in getattr(rules, table).items():
                if chars == set(entry):
                    element = value.get('element') if isinstance(value, dict) else value if kind == 'trine' else None
                    emit('group', kind, members, table, element=element, formation=True)
    for branch in branches:
        hidden = {entry['char'] for entry in JIJANGGAN_DETAILED[characters[branch]['char']]}
        for stem in stems:
            if characters[stem]['char'] in hidden:
                emit('cross_layer', 'transmission', [branch, stem], 'JIJANGGAN_DETAILED',
                     hidden_stem=characters[stem]['char'],
                     direction=dict(from_character=branch, to_character=stem, basis='hidden_stem_match'))
    return {rid: rows[rid] for rid in sorted(rows)}


def attach_cycle_relations(graph):
    """Attach detected rows once and rebuild reverse references for every participant."""
    detected = detect_cycle_relations(graph['characters'])
    # Reattachment after a context change must not retain old cycle edges.
    graph['relations'] = {rid: row for rid, row in graph['relations'].items()
                          if not rid.startswith('cycle:')}
    graph['relations'].update(detected)
    for key, node in graph['characters'].items():
        node['relation_ids'] = [rid for rid, row in graph['relations'].items() if key in row['participants']]
        node['transmission_relation_ids'] = [rid for rid in node['relation_ids']
                                             if graph['relations'][rid]['type'] == 'transmission']
        if not node['context_id'].startswith('natal.'):
            node['analysis'] = dict(calculation_status='candidates_detected',
                                    root_impact_status='not_evaluated')
    for context in graph['contexts'].values():
        if context['scope'] != 'natal':
            context['calculation_status'] = 'candidates_detected'
    present = {context['scope'] for context in graph['contexts'].values()}
    graph['coverage']['calculated_scopes'] = [scope for scope in ('natal', 'daewoon', 'sewoon') if scope in present]
    graph['coverage']['not_evaluated_scopes'] = [scope for scope in ('natal', 'daewoon', 'sewoon') if scope not in present]
    graph['coverage']['detected_only_relation_ids'] = [rid for rid, row in graph['relations'].items()
                                                      if row['activation_status'] == 'detected']
    graph['coverage']['not_evaluated_mechanisms'] = list(dict.fromkeys(
        graph['coverage']['not_evaluated_mechanisms'] + [
        'cycle_relation_activation', 'cycle_relation_competition', 'cycle_power_effects',
        'cycle_rooting', 'cycle_internal_relations', 'cross_context_stem_branch_element']))
