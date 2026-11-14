"""기존 글자·관계를 화면용 문구로 변환한다. 새 명리 판정은 하지 않는다."""
from services.relation_presentation import RELATION_NAMES
from services.constants import STEM_INFO

SCOPES = ('natal', 'daewoon', 'sewoon')
SCOPE_NAMES = dict(natal='원국', daewoon='대운', sewoon='세운')
POSITIONS = dict(year='년', month='월', day='일', hour='시')
KINDS = dict(stem='천간', branch='지지')
PILLARS = ('year', 'month', 'day', 'hour', 'cycle')


def _order(graph, key):
    n = graph['characters'][key]
    return (SCOPES.index(graph['contexts'][n['context_id']]['scope']),
            n['context_id'], PILLARS.index(n['position']), n['kind'] == 'branch', key)


def _label(graph, key, full=False):
    n = graph['characters'][key]
    position = (POSITIONS[n['position']] + ('간' if n['kind'] == 'stem' else '지')
                if n['position'] in POSITIONS else KINDS[n['kind']])
    prefix = SCOPE_NAMES[graph['contexts'][n['context_id']]['scope']] + ' ' if full else ''
    return f"{prefix}{position} {n['char']}"


def _context_title(graph, context_id):
    c = graph['contexts'][context_id]
    if c['scope'] == 'natal':
        return '원국'
    nodes = [n for n in graph['characters'].values() if n['context_id'] == context_id]
    chars = ''.join(next((n['char'] for n in nodes if n['kind'] == kind), '') for kind in ('stem', 'branch'))
    year = f" {c['selection']['year']}" if c['scope'] == 'sewoon' and 'year' in c.get('selection', {}) else ''
    return f"{SCOPE_NAMES[c['scope']]}{year} {chars}"


def _item(text, characters=(), relations=(), details=()):
    return dict(text=text, character_ids=list(characters), relation_ids=list(relations), detail_lines=list(details))


def _relations(graph, key):
    buckets = {}
    for rid in graph['characters'][key]['relation_ids']:
        row = graph['relations'][rid]
        peers = tuple(sorted((p for p in row['participants'] if p != key), key=lambda p: _order(graph, p)))
        contexts = {graph['characters'][p]['context_id'] for p in peers}
        group = next(iter(contexts)) if len(contexts) == 1 else 'mixed'
        buckets.setdefault((group, peers), []).append(row)
    groups = {}
    for (group, peers), rows in sorted(buckets.items(), key=lambda pair: tuple(_order(graph, p) for p in pair[0][1])):
        labels, details = [], []
        for row in sorted(rows, key=lambda r: (r['type'], r['relation_id'])):
            name = RELATION_NAMES.get(row['type'], row['type'])
            if row['type'] == 'combine' and all(graph['characters'][p]['kind'] == 'stem' for p in row['participants']):
                name = '천간합'
            if row['type'] == 'element' and row.get('element_relation') == 'same_element':
                name = '동오행'
            for formation in row.get('formation_candidates', []):
                if len(row['participants']) > 2:
                    details.append(' + '.join(_label(graph, p, True) for p in sorted(formation, key=lambda p: _order(graph, p))))
            direction = row.get('direction')
            if direction and row['type'] in ('generate', 'control', 'transmission', 'element'):
                if row['type'] == 'element':
                    name = '생' if 'generates' in (row.get('element_relation') or '') else '극' if 'controls' in (row.get('element_relation') or '') else name
                name += ' →' if direction['from_character'] == key else ' ←'
                details.append(f"{_label(graph, direction['from_character'], True)} → {_label(graph, direction['to_character'], True)}" +
                               (f" · 지장간 {row['hidden_stem']}" if row.get('hidden_stem') else ''))
            if name not in labels:
                labels.append(name)
        text = ' + '.join(_label(graph, p, group == 'mixed') for p in peers) + ' · ' + ' · '.join(labels)
        groups.setdefault(group, []).append(_item(text, peers, sorted(r['relation_id'] for r in rows), dict.fromkeys(details)))
    def group_order(group):
        return (3, group) if group == 'mixed' else (SCOPES.index(graph['contexts'][group]['scope']), group)
    return [dict(key=group, title='복합 관계' if group == 'mixed' else _context_title(graph, group), items=groups[group])
            for group in sorted(groups, key=group_order)]


def _sections(graph, key):
    n = graph['characters'][key]
    sections = []
    root = n.get('rooting')
    if root:
        items = [_item('동주 통근 · ' + ('있음' if root['has_same_pillar_root'] else '없음'), root['root_branch_ids'])]
        peers = sorted(root['external_support_branch_ids'], key=lambda p: _order(graph, p))
        if peers:
            items.append(_item('타주 지원 · ' + ' · '.join(_label(graph, p) for p in peers), peers))
        sections.append(dict(key='rooting', title='통근', items=items))
    if n['kind'] != 'branch':
        return sections
    branch = n['analysis']
    hidden = n['pillar_attributes'].get('jijanggan', [])
    transmissions = [graph['relations'][rid] for rid in n['transmission_relation_ids']
                     if graph['relations'][rid]['direction']['from_character'] == key]
    items = []
    for h in hidden:
        rows = [r for r in transmissions if r['hidden_stem'] == h['ch']]
        targets = sorted({r['direction']['to_character'] for r in rows}, key=lambda p: _order(graph, p))
        text = f"{h['ch']} {h['ten_god']}"
        if targets:
            text += ' → ' + ' · '.join(_label(graph, p, graph['characters'][p]['context_id'] != n['context_id']) for p in targets)
        elif graph['contexts'][n['context_id']]['scope'] == 'natal':
            text += ' · 원국 미투간'
        items.append(_item(text, targets, sorted(r['relation_id'] for r in rows)))
    store = branch.get('storehouse')
    if store:
        source = next(h for h in hidden if STEM_INFO[h['ch']]['element_ch'] == store['stored_element'])
        rows = [r for r in transmissions if r['hidden_stem'] == source['ch']]
        targets = sorted({r['direction']['to_character'] for r in rows}, key=lambda p: _order(graph, p))
        text = f"{store['role']} · 저장 오행 {store['stored_element']}"
        details = [f"지장간 {source['ch']} · {source['ten_god']}"]
        if targets:
            details.append('투간 → ' + ' · '.join(_label(graph, p, True) for p in targets))
        else:
            details.append('원국 미투간')
        sections.append(dict(key='storehouse', title='고', items=[_item(text, targets, sorted(r['relation_id'] for r in rows), details)]))
    if items:
        sections.append(dict(key='hidden_stems', title='지장간', items=items))
    extra = []
    if n['pillar_attributes'].get('unseong'):
        extra.append(_item('운성 · ' + n['pillar_attributes']['unseong']))
    if n['pillar_attributes'].get('special_stars'):
        extra.append(_item('신살 · ' + ' · '.join(n['pillar_attributes']['special_stars'])))
    if extra:
        sections.append(dict(key='pillar', title='기둥 정보', items=extra))
    return sections


def attach_character_displays(graph):
    for key, node in graph['characters'].items():
        attrs = node['attributes']
        node['display'] = dict(version='1.0.0', title=_label(graph, key, True),
                               subtitle=' · '.join(str(attrs[field]) for field in ('element', 'yin_yang', 'ten_god') if attrs.get(field)),
                               relation_groups=_relations(graph, key), sections=_sections(graph, key))
