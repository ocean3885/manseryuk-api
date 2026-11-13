"""현재 해설 DB의 내용을 별도 작성용 JSON으로 구성한다. DB는 변경하지 않는다."""
import json

from core.interpretation_database import DEFAULT_DATABASE, readonly_database
from schemas.interpretation_rule import InterpretationRule, RELATION_TYPES
from services.relation_presentation import RELATION_NAMES


def authoring_document(database=DEFAULT_DATABASE, *, status='empty', layer=None,
                       relation_type=None, limit=None, offset=0) -> dict:
    if status not in ('empty', 'draft', 'ready'):
        raise ValueError('지원하지 않는 작성 상태입니다.')
    if layer is not None and layer not in RELATION_TYPES:
        raise ValueError('지원하지 않는 관계 계층입니다.')
    allowed = RELATION_TYPES[layer] if layer else set().union(*RELATION_TYPES.values())
    if relation_type is not None and relation_type not in allowed:
        raise ValueError('해당 계층에서 지원하지 않는 관계 종류입니다.')
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ValueError('limit은 양의 정수여야 합니다.')
    if type(offset) is not int or offset < 0:
        raise ValueError('offset은 0 이상의 정수여야 합니다.')
    clauses, values = ['content_status=?'], [status]
    for column, value in (('layer', layer), ('relation_type', relation_type)):
        if value is not None:
            clauses.append(f'{column}=?')
            values.append(value)
    where = ' AND '.join(clauses)
    with readonly_database(database) as connection:
        connection.execute('BEGIN')  # 개수와 행을 같은 읽기 스냅샷에서 조회한다.
        total = connection.execute(f'SELECT count(*) FROM interpretation_rules WHERE {where}', values).fetchone()[0]
        rows = connection.execute(f'''SELECT * FROM interpretation_rules WHERE {where}
            ORDER BY layer,relation_type,participant_pattern,conditions_json,rule_id LIMIT ? OFFSET ?''',
            [*values, limit if limit is not None else -1, offset]).fetchall()
    rules = []
    for row in rows:
        data = dict(row)
        data['participant_pattern'] = json.loads(data['participant_pattern'])
        data['conditions_json'] = json.loads(data['conditions_json'])
        rule = InterpretationRule.model_validate(data)
        rules.append(rule.model_dump(mode='json', exclude={'content_status'}))
    next_offset = offset + len(rules)
    return {
        'format_version': 1,
        'purpose': 'interpretation_authoring',
        'selection': {'content_status': status, 'layer': layer, 'relation_type': relation_type,
                      'limit': limit, 'offset': offset},
        'total_matching': total,
        'exported_count': len(rules),
        'next_offset': next_offset if next_offset < total else None,
        'writing_guide': {
            'language': 'ko',
            'editable_fields': ['explanation'],
            'instructions': [
                '각 조합이 관찰될 때의 일반 해설을 한국어 2~3문장으로 작성하세요.',
                '관계의 구조, 십성의 상징적 해석 관점, 추가 확인할 조건 순서로 서술하세요.',
                'rule_id·layer·relation_type·participant_pattern·conditions_json은 그대로 유지하고 explanation만 작성하세요.',
                '생·극의 참여 순서는 작용 주체→대상입니다. 동주는 천간→지지입니다. 나머지 순서는 작용 방향이 아닙니다.',
                '이 자료는 실제 개인의 원국이 아닙니다. 실제 글자·위치·통근·세력·주변 관계·시기를 만들어 넣지 마세요.',
                '비견 표기만으로 일간 본인이라고 간주하지 마세요. has_day_master=true 조건이 있는 경우에만 본인 참여가 명시됩니다.',
                '합의 존재로 성립·합화를, 생·극의 존재로 실제 우열·손상·길흉·성과를 확정하지 마세요.',
                '고 크기·개고·관계의 세력 영향 등 미평가 판정을 해설로 대신 만들지 마세요.',
                '근거가 불충분해 작성할 수 없으면 explanation을 null로 유지하세요.',
                '완성된 JSON을 반환하세요. 작성 결과는 이후 draft로 가져와 검토하며 자동 승인하지 않습니다.',
            ],
            'relation_labels': {
                family: {kind: ('천간합' if family == 'stem' and kind == 'combine' else RELATION_NAMES[kind])
                         for kind in sorted(kinds)} for family, kinds in RELATION_TYPES.items()
            },
        },
        'rules': rules,
    }
