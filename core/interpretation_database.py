"""달력 DB와 분리된 해설 저장소. 초기화는 명시적으로, 검색은 읽기 전용으로 실행한다."""
from contextlib import closing, contextmanager
import json
from pathlib import Path
import sqlite3
from schemas.interpretation_rule import InterpretationQuery, InterpretationRule, canonical_json

DEFAULT_DATABASE = Path(__file__).resolve().parents[1] / 'interpretations.db'
CALENDAR_DATABASE = Path(__file__).resolve().parents[1] / 'manseryuk.db'
DATABASE_VERSION = 1
TABLE = 'interpretation_rules'

DDL = '''CREATE TABLE interpretation_rules (
    rule_id TEXT PRIMARY KEY NOT NULL,
    layer TEXT NOT NULL CHECK(layer IN ('stem','branch','group','same_pillar')),
    relation_type TEXT NOT NULL,
    participant_pattern TEXT NOT NULL,
    conditions_json TEXT NOT NULL,
    explanation TEXT,
    content_status TEXT NOT NULL DEFAULT 'empty' CHECK(content_status IN ('empty','draft','ready')),
    UNIQUE(layer, relation_type, participant_pattern, conditions_json),
    CHECK((content_status='empty' AND explanation IS NULL) OR
          (content_status IN ('draft','ready') AND explanation IS NOT NULL AND length(trim(explanation))>0))
)'''
INDEX_DDL = '''CREATE INDEX IF NOT EXISTS ix_interpretation_lookup
               ON interpretation_rules(layer, relation_type, participant_pattern, content_status)'''


class AmbiguousInterpretationError(ValueError):
    """동일한 우선 수준의 조건이 동시에 일치해 하나를 선택할 수 없다."""


def _checked_path(database) -> Path:
    path = Path(database).resolve()
    if path == CALENDAR_DATABASE or (path.exists() and CALENDAR_DATABASE.exists() and path.samefile(CALENDAR_DATABASE)):
        raise ValueError('달력 DB를 해설 저장소로 사용할 수 없습니다.')
    return path


def _check_database(connection):
    tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    if tables != {TABLE} or connection.execute('PRAGMA user_version').fetchone()[0] != DATABASE_VERSION:
        raise ValueError('지원하는 해설 DB 스키마가 아닙니다.')
    if [r[1] for r in connection.execute(f'PRAGMA table_info({TABLE})')] != [
            'rule_id', 'layer', 'relation_type', 'participant_pattern', 'conditions_json', 'explanation', 'content_status']:
        raise ValueError('해설 테이블의 열 정의가 다릅니다.')


def seed_database(rules, database=DEFAULT_DATABASE) -> dict:
    validated = [InterpretationRule.model_validate(r.model_dump() if isinstance(r, InterpretationRule) else r) for r in rules]
    identities = [r.rule_id for r in validated]
    if len(identities) != len(set(identities)):
        raise ValueError('시드 규칙 ID가 중복됐습니다.')
    path = _checked_path(database)
    with closing(sqlite3.connect(path)) as connection, connection:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
        if not tables and connection.execute('PRAGMA user_version').fetchone()[0] == 0:
            connection.execute(DDL)
            connection.execute(f'PRAGMA user_version={DATABASE_VERSION}')
        _check_database(connection)
        connection.execute(INDEX_DDL)
        before = connection.total_changes
        connection.executemany('''INSERT INTO interpretation_rules
            (rule_id,layer,relation_type,participant_pattern,conditions_json,explanation,content_status)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(layer,relation_type,participant_pattern,conditions_json) DO NOTHING''', [
                (r.rule_id, r.layer, r.relation_type, r.pattern_json, canonical_json(r.conditions_json),
                 r.explanation, r.content_status) for r in validated])
        inserted = connection.total_changes - before
        total = connection.execute('SELECT count(*) FROM interpretation_rules').fetchone()[0]
    return {'inserted': inserted, 'existing': len(validated) - inserted, 'total': total}


@contextmanager
def readonly_database(database=DEFAULT_DATABASE):
    path = _checked_path(database)
    if not path.is_file():
        raise FileNotFoundError(f'해설 DB가 없습니다: {path}')
    connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        _check_database(connection)
        yield connection
    finally:
        connection.close()


def find_rule(query: InterpretationQuery, database=DEFAULT_DATABASE, *, include_unwritten=False) -> InterpretationRule | None:
    query = InterpretationQuery.model_validate(query.model_dump() if isinstance(query, InterpretationQuery) else query)
    with readonly_database(database) as connection:
        rows = connection.execute('''SELECT * FROM interpretation_rules
            WHERE layer=? AND relation_type=? AND participant_pattern=?''' +
            ('' if include_unwritten else " AND content_status='ready'"),
            (query.layer, query.relation_type, query.pattern_json)).fetchall()
    matches = []
    for row in rows:
        data = dict(row)
        data['participant_pattern'] = json.loads(data['participant_pattern'])
        data['conditions_json'] = json.loads(data['conditions_json'])
        rule = InterpretationRule.model_validate(data)
        if all(key in query.facts and query.facts[key] == value for key, value in rule.conditions_json.items()):
            matches.append(rule)
    if not matches:
        return None
    specificity = max(len(r.conditions_json) for r in matches)
    best = [r for r in matches if len(r.conditions_json) == specificity]
    if len(best) != 1:
        raise AmbiguousInterpretationError('같은 구체성의 해설 규칙이 여러 개 일치합니다: ' + ', '.join(sorted(r.rule_id for r in best)))
    return best[0]
