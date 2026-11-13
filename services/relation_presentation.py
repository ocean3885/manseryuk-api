"""Deterministic Korean descriptions of existing decisions, never new judgments."""
from services.character_evidence import participant_detail, walk_records, PILLARS
from schemas.character_details import ACTIVATION_LABELS

RULE_VERSION = '1.0.0'
STATUS_LABELS = ACTIVATION_LABELS
RELATION_NAMES = dict(combine='육합', clash='충', control='극', pierce='천',
                      punishment='형', self_punishment='자형', half_combine='반합',
                      arch_combine='공합', hidden_combine='암합', generate='생',
                      same_branch='동일 지지', trine='삼합', square='방합',
                      triple_punishment='삼형', transmission='투간', element='동주 오행 관계',
                      self_combine='자합')
RELATION_NAMES['break'] = '파'
REASON_CODES = frozenset((
    'intervening_adjacent_clash', 'external_adjacent_clash', 'duplicate_middle',
    'adjacent_middle_clash', 'adjacent_birth_clash', 'adjacent_tomb_clash',
    'active_pair_structure_overrides_element', 'combination_candidate_not_transformation',
    'adjacent_self_punishment',
    'nonadjacent_self_punishment_candidate',
    'cycle_presence_only_activation_and_impact_not_evaluated'))


def _label(graph, key):
    return participant_detail(graph, key)['display_name']


def _join(graph, keys):
    def order(key):
        node = graph['characters'][key]
        scope = graph['contexts'][node['context_id']]['scope']
        return (('natal', 'daewoon', 'sewoon').index(scope),
                ('year', 'month', 'day', 'hour', 'cycle').index(node['position']),
                ('stem', 'branch').index(node['kind']), key)
    return ' · '.join(_label(graph, key) for key in sorted(keys, key=order))


def _name(row, graph):
    name = RELATION_NAMES.get(row['type'], '등록 관계')
    if row['type'] in ('combine', 'clash', 'control') and all(
            graph['characters'][p]['kind'] == 'stem' for p in row['participants']):
        return '천간합' if row['type'] == 'combine' else '천간 ' + name
    return name


def _line(code, category, text, characters, relations=(), evidence=()):
    return dict(code=code, category=category, text=text,
                character_ids=sorted(set(characters)), relation_ids=sorted(set(relations)),
                evidence_indices=sorted(set(evidence)))


def _clash_reason(graph, row, code):
    field = dict(intervening_adjacent_clash='member_pillar', external_adjacent_clash='member_pillar',
                 adjacent_middle_clash='middle_pillar', adjacent_birth_clash='wing_pillar',
                 adjacent_tomb_clash='wing_pillar')[code]
    matches = {}
    for index, entry in enumerate(row['evidence']):
        for record in walk_records(entry['details'].get('condition_evidence', {})):
            victim, attacker = record.get(field), record.get('clashing_pillar')
            if victim not in PILLARS or attacker not in PILLARS:
                continue
            if code == 'intervening_adjacent_clash' and record.get('location') != 'between':
                continue
            if code == 'external_adjacent_clash' and record.get('location') != 'outside':
                continue
            if code in ('adjacent_birth_clash', 'adjacent_tomb_clash') and record.get('wing_role') != (
                    'birth' if code == 'adjacent_birth_clash' else 'tomb'):
                continue
            members = (f'natal.chart.{victim}.branch', f'natal.chart.{attacker}.branch')
            refs = [rid for rid in entry['related_relation_ids']
                    if graph['relations'][rid]['type'] == 'clash'
                    and set(graph['relations'][rid]['participants']) == set(members)]
            if refs:
                data = matches.setdefault(members, (set(), set()))
                data[0].update(refs)
                data[1].add(index)
    if not matches:
        return None
    causes = ' / '.join(f'{_label(graph, a)} ↔ {_label(graph, b)}의 인접 충' for a, b in sorted(matches))
    endings = dict(
        intervening_adjacent_clash='이 육합 조합의 두 글자 사이에 있습니다.',
        external_adjacent_clash='이 육합 조합의 바깥에 함께 있습니다.',
        adjacent_middle_clash='이 삼합 중신에 함께 있습니다.',
        adjacent_birth_clash='이 삼합 생지에 함께 있습니다.',
        adjacent_tomb_clash='이 삼합 성지에 함께 있습니다.')
    return _line(code, 'structure', causes + endings[code],
                 [p for pair in matches for p in pair],
                 [rid for refs, _ in matches.values() for rid in refs],
                 [i for _, indices in matches.values() for i in indices])


def _explain_reason(graph, row, code):
    members = row['participants']
    if code in ('intervening_adjacent_clash', 'external_adjacent_clash', 'adjacent_middle_clash',
                'adjacent_birth_clash', 'adjacent_tomb_clash'):
        return _clash_reason(graph, row, code)
    if code == 'duplicate_middle':
        keys, indices = set(), []
        for i, entry in enumerate(row['evidence']):
            positions = entry['details'].get('condition_evidence', {}).get('middle_pillars', [])
            if len(positions) > 1:
                keys.update(f'natal.chart.{p}.branch' for p in positions)
                indices.append(i)
        if keys:
            return _line(code, 'structure', f'{_join(graph, sorted(keys))}에 삼합 중신이 중복되어 있습니다.', keys, evidence=indices)
    elif code == 'active_pair_structure_overrides_element':
        ids, indices = set(), []
        for i, entry in enumerate(row['evidence']):
            refs = entry['details'].get('overriding_relation_ids', [])
            if refs:
                ids.update(refs)
                indices.append(i)
        if ids:
            names = ' · '.join(sorted({_name(graph['relations'][rid], graph) for rid in ids}))
            return _line(code, 'decision', f'같은 위치 쌍의 {names} 관계가 성립하여 이 {_name(row, graph)} 관계의 독립 적용을 억제합니다.',
                         members, ids, indices)
    elif code == 'combination_candidate_not_transformation':
        return _line(code, 'notice', '후보 오행은 합의 오행 표기이며, 실제 합화가 성립했다는 판정은 아닙니다.', members,
                     evidence=[i for i, e in enumerate(row['evidence'])
                               if code == e['details'].get('status_reason') or code in e['details'].get('status_reasons', [])])
    elif code in ('adjacent_self_punishment', 'nonadjacent_self_punishment_candidate'):
        indices = [i for i, e in enumerate(row['evidence']) if code in e['details'].get('status_reasons', [])
                   or e['details'].get('status_reason') == code]
        if indices:
            text = ('같은 자형 글자가 인접한 두 위치에 있어 현재 원국 규칙에서 자형으로 성립합니다.'
                    if code == 'adjacent_self_punishment' else
                    '같은 자형 글자가 떨어진 위치에 있어 자형 후보로 기록합니다.')
            return _line(code, 'decision', text, members, evidence=indices)
    elif code == 'cycle_presence_only_activation_and_impact_not_evaluated':
        return _line(code, 'scope', '원국·대운·세운 사이의 등록 관계를 탐지한 결과입니다. 운 관계의 성립·경합·실제 영향은 평가하지 않았습니다.', members)
    return None


def _active_basis(graph, row):
    indices = [i for i, e in enumerate(row['evidence']) if e['details'].get('activation_rule_id') in (
        'branch:pair_presence_active_v1', 'branch:triple_punishment_presence_active_v1')]
    if indices:
        text = ('삼형을 구성하는 세 종류 지지가 원국에 함께 있어 현행 성립 규칙을 충족합니다.'
                if row['type'] == 'triple_punishment' else
                '등록된 관계의 두 지지가 원국에 함께 있고 현행 성립 조건을 충족합니다.')
        return _line('registered_presence', 'decision', text, row['participants'], evidence=indices)
    return None


def build_relation_presentation(graph, row):
    members, kind = row['participants'], row['type']
    name = _name(row, graph)
    title = f'{_join(graph, members)}의 {name}'
    description = f'{_join(graph, members)} 사이의 {name} 관계를 기록했습니다.'
    direction = row.get('direction')
    if kind == 'transmission' and direction and row.get('hidden_stem'):
        description = (f"{_label(graph, direction['from_character'])}의 지장간 {row['hidden_stem']}이 "
                       f"{_label(graph, direction['to_character'])}에 같은 글자로 드러나 투간으로 기록됩니다.")
    elif kind == 'self_combine':
        source = next((e['details']['records'] for e in row.get('evidence', [])
                       if isinstance(e['details'].get('records'), dict)
                       and e['details']['records'].get('hidden_stem')), None)
        if source:
            stem = next(p for p in members if graph['characters'][p]['kind'] == 'stem')
            branch = next(p for p in members if graph['characters'][p]['kind'] == 'branch')
            description = (f"{_label(graph, stem)} ↔ {_label(graph, branch)}의 지장간 {source['hidden_stem']}: "
                           '같은 기둥의 자합 조합이 있습니다.')
    elif kind == 'element':
        subtype = row.get('element_relation')
        if subtype == 'same_element':
            description = f'{_join(graph, members)}의 오행은 서로 같습니다.'
        elif subtype and direction:
            verb = '생하는' if 'generates' in subtype else '극하는'
            description = (f"{_label(graph, direction['from_character'])} → "
                           f"{_label(graph, direction['to_character'])}: 오행상 {verb} 방향입니다.")
    elif kind in ('generate', 'control') and direction:
        description = (f"{_label(graph, direction['from_character'])} → "
                       f"{_label(graph, direction['to_character'])}: 오행상 {name}의 방향입니다.")
    elif kind == 'same_branch':
        description = '같은 지지가 서로 다른 위치에 존재합니다.'

    lines, missing = [], []
    if len(row.get('formation_candidates', [])) > 1:
        count = len(row['formation_candidates'])
        title += f' (위치 조합 {count}개)'
        description = f'반복 글자를 위치별로 구분한 {count}개의 {name} 조합이 기록돼 있습니다.'
        for formation in row['formation_candidates']:
            lines.append(_line('formation', 'structure', f'{_join(graph, formation)}의 {name} 위치 조합입니다.',
                               formation, [row['relation_id']]))
    codes = list(dict.fromkeys([*row.get('status_reasons', []), *([row['status_reason']] if row.get('status_reason') else [])]))
    for code in codes:
        reason = _explain_reason(graph, row, code) if code in REASON_CODES else None
        if reason:
            lines.append(reason)
        else:
            missing.append(code)
    if kind not in RELATION_NAMES:
        missing.append('unknown_relation_type')
    if row['activation_status'] in ('suppressed', 'conditional') and not codes:
        missing.append('missing_status_reason')
    if kind == 'element' and not row.get('element_relation'):
        missing.append('missing_element_relation')
    if kind == 'transmission' and (not direction or not row.get('hidden_stem')):
        missing.append('missing_transmission_basis')
    if kind == 'self_combine' and not any(isinstance(e['details'].get('records'), dict)
                                         and e['details']['records'].get('hidden_stem')
                                         for e in row.get('evidence', [])):
        missing.append('missing_self_combine_hidden_stem')
    if row['activation_status'] == 'active' and not any(line['category'] == 'decision' for line in lines):
        basis = _active_basis(graph, row)
        if basis:
            lines.append(basis)
        else:
            missing.append('missing_activation_basis')
    if row['activation_status'] == 'potential' and not codes:
        lines.append(_line('potential_structure', 'scope',
                           '등록된 구성 또는 오행 경로가 확인된 잠재 관계입니다. 실제 성립과 적용은 확정하지 않았습니다.', members))
    if row['activation_status'] == 'detected':
        lines.append(_line('detected_fact', 'scope',
                           ('자합 조합의 존재를 확인했으며, 성립 여부와 실제 영향은 평가하지 않았습니다.'
                            if kind == 'self_combine' else
                            '조합의 존재와 제공된 구성 근거를 확인했으며, 실제 성립과 작용은 확정하지 않았습니다.'
                            if kind in ('combine', 'trine') else
                            '글자 일치 또는 등록 규칙으로 확인한 관계 사실이며, 실제 영향량을 판정한 결과는 아닙니다.'), members))

    for i, entry in enumerate(row.get('evidence', [])):
        details = entry['details']
        if kind == 'self_combine':
            for rid in entry['related_relation_ids']:
                context = graph['relations'][rid]
                lines.append(_line('self_combine_context', 'structure',
                                   f"{_join(graph, context['participants'])}의 {_name(context, graph)} 관계가 함께 있습니다.",
                                   context['participants'], [rid], [i]))
        if details.get('formation_status') == 'included_in_complete_group':
            lines.append(_line('included_in_complete_group', 'structure',
                               '삼합 구성 안의 두 지지를 연결한 반합 후보입니다. 독립 작용으로 확정하지 않습니다.',
                               members, entry['related_relation_ids'], [i]))
        if any(isinstance(record.get('fallback_from'), dict) for record in walk_records(details)):
            group_ids = [rid for rid in entry['related_relation_ids'] if graph['relations'][rid]['type'] == 'trine']
            if group_ids:
                lines.append(_line('remaining_half_combine', 'structure',
                                   '삼합 날개의 인접 충과 함께, 다른 날개와 중신의 반합 후보를 기록합니다.',
                                   members, entry['related_relation_ids'], [i]))
            else:
                missing.append('missing_fallback_group')
    if row['activation_status'] == 'candidate_only' and not codes and not lines:
        lines.append(_line('candidate_structure', 'scope',
                           '등록된 글자 조합에 따른 후보입니다. 실제 성립과 작용은 확정하지 않았습니다.', members))
    # One source fact may be carried by both matrix and dynamics evidence.
    unique = {}
    for line in lines:
        identity = (line['code'], line['text'], tuple(line['character_ids']), tuple(line['relation_ids']))
        if identity in unique:
            unique[identity]['evidence_indices'] = sorted(set(unique[identity]['evidence_indices'] + line['evidence_indices']))
        else:
            unique[identity] = line
    return dict(rule_version=RULE_VERSION, title=title, status_label=STATUS_LABELS[row['activation_status']],
                description=description, reasons=list(unique.values()),
                explanation_status='partial' if missing else 'complete', missing_evidence_codes=sorted(set(missing)))


def attach_relation_presentations(graph):
    for row in graph['relations'].values():
        row['presentation'] = build_relation_presentation(graph, row)
