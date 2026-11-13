"""해설 DB 초기화·검색·작성용 내보내기. LLM 호출·API 응답 연결은 하지 않는다."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.interpretation_database import CALENDAR_DATABASE, DEFAULT_DATABASE, seed_database, find_rule
from schemas.interpretation_rule import InterpretationQuery
from services.interpretation_catalog import generate_catalog
from services.interpretation_lookup import queries_for_relation
from services.interpretation_export import authoring_document

DEFAULT_SEED = Path(__file__).resolve().parents[1] / 'data' / 'interpretation_patterns.json'


def checked_seed_output(output: Path, database: Path) -> Path:
    """JSON 출력이 저장소를 덮어쓰지 않도록 DB를 열기 전에 검사한다."""
    output = output.resolve()
    if output.suffix.lower() != '.json':
        raise ValueError('시드 출력 경로는 .json 파일이어야 합니다.')
    for protected in (database.resolve(), CALENDAR_DATABASE):
        if output == protected or (output.exists() and protected.exists() and output.samefile(protected)):
            raise ValueError('시드 출력으로 DB 파일을 덮어쓸 수 없습니다.')
    if output.is_file():
        with output.open('rb') as stream:
            if stream.read(16) == b'SQLite format 3\x00':
                raise ValueError('기존 SQLite 파일을 시드 출력으로 사용할 수 없습니다.')
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    initialize = commands.add_parser('init', help='현재 규칙에서 빈 해설 패턴 생성·저장')
    initialize.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    initialize.add_argument('--seed-output', type=Path, default=DEFAULT_SEED)
    export = commands.add_parser('export', help='현재 DB에서 해설 작성용 JSON 내보내기')
    export.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    export.add_argument('--output', type=Path, required=True, help='새 .json 파일 경로. 기존 파일은 덮어쓰지 않음')
    export.add_argument('--status', choices=['empty', 'draft', 'ready'], default='empty')
    export.add_argument('--layer', choices=['stem', 'branch', 'group', 'same_pillar'])
    export.add_argument('--relation-type')
    export.add_argument('--limit', type=int, help='최대 항목 수. 생략하면 전체')
    export.add_argument('--offset', type=int, default=0)
    lookup = commands.add_parser('lookup', help='패턴으로 검색. 기본은 사용 가능한 해설만 조회')
    lookup.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    lookup.add_argument('--layer', required=True, choices=['stem', 'branch', 'group', 'same_pillar'])
    lookup.add_argument('--relation-type', required=True)
    lookup.add_argument('--participants', nargs='+', required=True)
    lookup.add_argument('--facts', default='{"scope":"natal"}', help='지원 조건의 JSON 객체')
    lookup.add_argument('--include-unwritten', action='store_true', help='빈 해설·초안도 검색')
    graph_lookup = commands.add_parser('lookup-graph', help='기존 글자·운 조회 JSON에서 검색')
    graph_lookup.add_argument('--database', type=Path, default=DEFAULT_DATABASE)
    graph_lookup.add_argument('--graph', type=Path, required=True)
    graph_lookup.add_argument('--relation-id', required=True)
    graph_lookup.add_argument('--include-unwritten', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'init':
            output = checked_seed_output(args.seed_output, args.database)
            catalog = generate_catalog()
            result = seed_database(catalog['rules'], args.database)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            result.update(database=str(args.database.resolve()), counts_by_layer=catalog['counts_by_layer'])
        elif args.command == 'export':
            output = checked_seed_output(args.output, args.database)
            document = authoring_document(args.database, status=args.status, layer=args.layer,
                                          relation_type=args.relation_type, limit=args.limit, offset=args.offset)
            serialized = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open('x', encoding='utf-8') as stream:
                stream.write(serialized)
            result = {key: document[key] for key in ('total_matching', 'exported_count', 'next_offset')}
            result['output'] = str(output)
        else:
            if args.command == 'lookup':
                queries = [InterpretationQuery(layer=args.layer, relation_type=args.relation_type,
                           participant_pattern=args.participants, facts=json.loads(args.facts))]
            else:
                graph = json.loads(args.graph.read_text(encoding='utf-8'))
                queries = queries_for_relation(graph, args.relation_id)
            result = []
            for query in queries:
                rule = find_rule(query, args.database, include_unwritten=args.include_unwritten)
                result.append({'query': query.model_dump(mode='json'),
                               'rule': rule.model_dump(mode='json') if rule is not None else None})
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError, sqlite3.Error) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
