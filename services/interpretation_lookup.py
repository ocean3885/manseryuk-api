"""기존 통합 관계 결과를 해설 검색 키로 바꾼다. 탐지·판정·문장은 만들지 않는다."""
from schemas.interpretation_rule import InterpretationQuery, canonical_json, RELATION_TYPES

PILLARS = ('year', 'month', 'day', 'hour')


def queries_for_relation(graph: dict, relation_id: str) -> list[InterpretationQuery]:
    row = graph['relations'][relation_id]
    source_id = row['source_relation_id']
    family = source_id.split(':')[1] if source_id.startswith('cycle:') else source_id.split(':')[0]
    kind = row['type']
    if family not in RELATION_TYPES or kind not in RELATION_TYPES[family]:
        return []  # 투간 등 이번 기본 카탈로그 범위 밖의 관계.
    characters = graph['characters']
    formations = row['formation_candidates'] if family == 'group' else [row['participants']]
    if family == 'group' and not formations:
        raise ValueError('다자 관계에는 실제 세 글자 조합이 필요합니다.')
    queries = {}
    for formation in formations:
        members = list(formation)
        if family == 'same_pillar':
            members.sort(key=lambda key: characters[key]['kind'] != 'stem')
            if [characters[key]['kind'] for key in members] != ['stem', 'branch']:
                raise ValueError('동주 검색에는 천간·지지가 하나씩 필요합니다.')
        elif kind in ('generate', 'control'):
            direction = row.get('direction')
            if not direction or {direction['from_character'], direction['to_character']} != set(members):
                raise ValueError('생·극 검색에 실제 작용 방향이 필요합니다.')
            members = [direction['from_character'], direction['to_character']]
        nodes = [characters[key] for key in members]
        scope = ('natal' if all(graph['contexts'][node['context_id']]['scope'] == 'natal'
                                for node in nodes) else 'cross_context')
        facts = {'scope': scope, 'activation_status': row['activation_status'],
                 'has_day_master': any(node['context_id'] == 'natal.chart' and
                                       node['position'] == 'day' and node['kind'] == 'stem'
                                       for node in nodes)}
        if row.get('element_relation') is not None:
            facts['element_relation'] = row['element_relation']
        if family != 'same_pillar' and len({n['context_id'] for n in nodes}) == 1 and all(
                n['position'] in PILLARS for n in nodes):
            indices = [PILLARS.index(n['position']) for n in nodes]
            facts['is_adjacent'] = max(indices) - min(indices) == len(nodes) - 1
        stars = tuple('비견' if n['attributes']['ten_god'] == '일간' else n['attributes']['ten_god']
                      for n in nodes)
        query = InterpretationQuery(layer=family, relation_type=kind,
                                    participant_pattern=stars, facts=facts)
        queries[canonical_json(query.model_dump())] = query
    return [queries[key] for key in sorted(queries)]
