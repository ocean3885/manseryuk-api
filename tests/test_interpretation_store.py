"""기본 패턴·빈 해설 DB·검색 계약과 기존 결과의 재사용을 검증한다."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from core.interpretation_database import (
    seed_database, find_rule, readonly_database, AmbiguousInterpretationError,
)
from schemas.interpretation_rule import InterpretationQuery, empty_rule
from services.interpretation_catalog import generate_catalog
from services.interpretation_lookup import queries_for_relation
from services.character_details import assemble_character_details
from relation_presentation_fixtures import response_for


class InterpretationCatalogTests(unittest.TestCase):
    def test_catalog_contains_565_stable_empty_patterns_from_registered_rules(self):
        catalog = generate_catalog()
        self.assertEqual(catalog, generate_catalog())
        self.assertEqual(catalog['counts_by_layer'], {'branch': 275, 'group': 100, 'same_pillar': 150, 'stem': 40})
        self.assertEqual(len(catalog['rules']), 565)
        self.assertEqual(len({r['rule_id'] for r in catalog['rules']}), 565)
        self.assertTrue(all(r['explanation'] is None and r['content_status'] == 'empty' for r in catalog['rules']))

    def test_committed_seed_matches_current_rule_catalog(self):
        seed = Path(__file__).resolve().parents[1] / 'data' / 'interpretation_patterns.json'
        self.assertEqual(json.loads(seed.read_text()), generate_catalog())

    def test_undirected_patterns_normalize_but_control_direction_is_preserved(self):
        first = empty_rule('stem', 'combine', ['식신', '정인'])
        reverse = empty_rule('stem', 'combine', ['정인', '식신'])
        self.assertEqual(first.rule_id, reverse.rule_id)
        forward = empty_rule('stem', 'control', ['식신', '편관'])
        backward = empty_rule('stem', 'control', ['편관', '식신'])
        self.assertNotEqual(forward.rule_id, backward.rule_id)
        self.assertEqual(empty_rule('group', 'trine', ['비견', '상관', '편재']).rule_id,
                         empty_rule('group', 'trine', ['편재', '비견', '상관']).rule_id)

    def test_invalid_patterns_and_unsupported_conditions_are_rejected(self):
        for layer, kind, members, conditions in (
            ('stem', 'opening', ['식신', '편관'], {}),
            ('group', 'trine', ['비견', '상관'], {}),
            ('stem', 'control', ['일간', '정재'], {}),
            ('stem', 'control', ['식신', '편관'], {'is_adjacent': 1}),
            ('stem', 'control', ['식신', '편관'], {'eval': 'True'}),
            ('stem', 'control', ['식신', '편관'], {'scope': None}),
        ):
            with self.subTest(kind=kind, conditions=conditions), self.assertRaises(ValueError):
                empty_rule(layer, kind, members, conditions)


class InterpretationDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'interpretations.db'
        self.basic = empty_rule('stem', 'control', ['식신', '편관'])

    def query(self, **facts):
        return InterpretationQuery(layer='stem', relation_type='control',
                                   participant_pattern=['식신', '편관'], facts={'scope': 'natal', **facts})

    def ready(self, rule, status='ready', text='검증용 해설'):
        with sqlite3.connect(self.database) as db:
            db.execute('UPDATE interpretation_rules SET explanation=?,content_status=? WHERE rule_id=?',
                       (text, status, rule.rule_id))

    def test_initialization_is_idempotent_and_keeps_authored_explanations(self):
        self.assertEqual(seed_database([self.basic], self.database), {'inserted': 1, 'existing': 0, 'total': 1})
        self.ready(self.basic)
        self.assertEqual(seed_database([self.basic], self.database), {'inserted': 0, 'existing': 1, 'total': 1})
        self.assertEqual(find_rule(self.query(), self.database).explanation, '검증용 해설')

    def test_empty_and_draft_rows_are_only_available_in_preview(self):
        seed_database([self.basic], self.database)
        self.assertIsNone(find_rule(self.query(), self.database))
        self.assertEqual(find_rule(self.query(), self.database, include_unwritten=True), self.basic)
        self.ready(self.basic, status='draft')
        self.assertIsNone(find_rule(self.query(), self.database))
        self.assertEqual(find_rule(self.query(), self.database, include_unwritten=True).content_status, 'draft')

    def test_more_specific_match_wins_and_missing_facts_do_not_satisfy_conditions(self):
        specific = empty_rule('stem', 'control', ['식신', '편관'], {'scope': 'natal', 'is_adjacent': True})
        seed_database([self.basic, specific], self.database)
        self.ready(self.basic)
        self.ready(specific, text='인접 조건 검증용 해설')
        self.assertEqual(find_rule(self.query(is_adjacent=True), self.database).rule_id, specific.rule_id)
        self.assertEqual(find_rule(self.query(), self.database).rule_id, self.basic.rule_id)
        self.assertEqual(find_rule(self.query(is_adjacent=False), self.database).rule_id, self.basic.rule_id)
        reverse = InterpretationQuery(layer='stem', relation_type='control', participant_pattern=['편관', '식신'])
        self.assertIsNone(find_rule(reverse, self.database))

    def test_equal_specificity_conflict_is_reported_instead_of_chosen_arbitrarily(self):
        adjacent = empty_rule('stem', 'control', ['식신', '편관'], {'scope': 'natal', 'is_adjacent': True})
        day = empty_rule('stem', 'control', ['식신', '편관'], {'scope': 'natal', 'has_day_master': True})
        seed_database([adjacent, day], self.database)
        self.ready(adjacent)
        self.ready(day)
        with self.assertRaises(AmbiguousInterpretationError):
            find_rule(self.query(is_adjacent=True, has_day_master=True), self.database)

    def test_missing_database_is_not_created_and_lookup_connection_is_readonly(self):
        with self.assertRaises(FileNotFoundError):
            find_rule(self.query(), self.database)
        self.assertFalse(self.database.exists())
        seed_database([self.basic], self.database)
        with readonly_database(self.database) as db:
            with self.assertRaises(sqlite3.OperationalError):
                db.execute('DELETE FROM interpretation_rules')
            plan = db.execute('EXPLAIN QUERY PLAN SELECT * FROM interpretation_rules '
                                  'WHERE layer=? AND relation_type=? AND participant_pattern=? AND content_status=?',
                                  ('stem', 'control', self.basic.pattern_json, 'ready')).fetchall()
            self.assertTrue(any('INDEX' in row['detail'] for row in plan), [tuple(row) for row in plan])

    def test_calendar_database_and_foreign_or_incompatible_schema_are_rejected(self):
        calendar = Path(__file__).resolve().parents[1] / 'manseryuk.db'
        with self.assertRaisesRegex(ValueError, '달력 DB'):
            seed_database([self.basic], calendar)
        foreign = self.database.parent / 'calendar_copy.db'
        with sqlite3.connect(foreign) as db:
            db.execute('CREATE TABLE calenda_data (cd_no INTEGER)')
        with self.assertRaises(ValueError):
            seed_database([self.basic], foreign)
        with sqlite3.connect(foreign) as db:
            self.assertEqual([r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")], ['calenda_data'])
        seed_database([self.basic], self.database)
        with sqlite3.connect(self.database) as db:
            db.execute('PRAGMA user_version=99')
        with self.assertRaises(ValueError):
            find_rule(self.query(), self.database)

    def test_duplicate_seed_and_blank_ready_content_are_rejected(self):
        with self.assertRaises(ValueError):
            seed_database([self.basic, self.basic], self.database)
        self.assertFalse(self.database.exists())
        seed_database([self.basic], self.database)
        with sqlite3.connect(self.database) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("UPDATE interpretation_rules SET content_status='ready' WHERE rule_id=?", (self.basic.rule_id,))


class InterpretationCommandTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def run_command(self, *arguments):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / 'interpretation_rules.py'),
                               *map(str, arguments)], cwd=self.root, capture_output=True,
                              text=True, encoding='utf-8', check=False)

    def test_initialize_and_lookup_commands_keep_empty_content_out_of_default_results(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            seed = Path(directory) / 'patterns.json'
            command = ('init', '--database', database, '--seed-output', seed)
            initialized = self.run_command(*command)
            self.assertEqual(initialized.returncode, 0, initialized.stderr)
            self.assertEqual(json.loads(initialized.stdout)['inserted'], 565)
            self.assertEqual(json.loads(seed.read_text(encoding='utf-8')), generate_catalog())
            repeated = self.run_command(*command)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(json.loads(repeated.stdout)['inserted'], 0)
            lookup = ('lookup', '--database', database, '--layer', 'stem',
                      '--relation-type', 'control', '--participants', '식신', '편관')
            result = self.run_command(*lookup)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIsNone(json.loads(result.stdout)[0]['rule'])
            preview = self.run_command(*lookup, '--include-unwritten')
            self.assertEqual(preview.returncode, 0, preview.stderr)
            self.assertEqual(json.loads(preview.stdout)[0]['rule']['content_status'], 'empty')

    def test_invalid_seed_destination_is_rejected_before_database_creation(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'new.json'
            for destination in (database, Path(directory) / 'patterns.db', self.root / 'manseryuk.db'):
                with self.subTest(destination=destination):
                    result = self.run_command('init', '--database', database, '--seed-output', destination)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertFalse(database.exists())

    def test_seed_output_cannot_overwrite_database_through_hardlink(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            seed_database([empty_rule('stem', 'control', ['식신', '편관'])], database)
            alias = Path(directory) / 'alias.json'
            alias.hardlink_to(database)
            before = database.read_bytes()
            result = self.run_command('init', '--database', database, '--seed-output', alias)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(database.read_bytes(), before)


class ExistingRelationLookupTests(unittest.TestCase):
    def test_day_master_alias_and_actual_control_direction_are_preserved(self):
        graph = assemble_character_details(response_for('子子子子', '甲戊戊戊'))
        relation = next(r for r in graph['relations'].values() if r['type'] == 'control' and
                        set(r['participants']) == {'natal.chart.year.stem', 'natal.chart.day.stem'})
        query = queries_for_relation(graph, relation['relation_id'])[0]
        self.assertEqual(query.participant_pattern, ('편관', '비견'))
        self.assertTrue(query.facts['has_day_master'])
        self.assertEqual(query.facts['scope'], 'natal')
        self.assertFalse(query.facts['is_adjacent'])

    def test_repeated_trine_uses_actual_three_member_formations(self):
        graph = assemble_character_details(response_for('亥卯未亥'))
        relation = next(r for r in graph['relations'].values() if r['type'] == 'trine')
        before = deepcopy(graph)
        queries = queries_for_relation(graph, relation['relation_id'])
        self.assertEqual(len(queries), 1)
        self.assertEqual(len(queries[0].participant_pattern), 3)
        self.assertEqual(graph, before)

    def test_all_supported_natal_relations_find_a_seed_without_recalculating_rules(self):
        catalog = generate_catalog()
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            seed_database(catalog['rules'], database)
            for stems, branches in [('甲己丙辛', '亥卯未亥'), ('甲戊戊戊', '寅巳申丑'),
                                    ('辛辛甲辛', '丑戌未丑'), ('癸丙戊庚', '巳午未寅')]:
                graph = assemble_character_details(response_for(branches, stems))
                for key, relation in graph['relations'].items():
                    queries = queries_for_relation(graph, key)
                    if relation['type'] == 'transmission':
                        self.assertEqual(queries, [])
                    else:
                        self.assertTrue(queries, (stems, branches, key))
                        for query in queries:
                            self.assertIsNotNone(find_rule(query, database, include_unwritten=True), (key, query))
                            self.assertIsNone(find_rule(query, database))

    def test_natal_only_seed_does_not_match_cross_context_candidates(self):
        graph = assemble_character_details(response_for('子子子子', '甲己甲己'))
        original = next(r for r in graph['relations'].values() if r['source_relation_id'].startswith('stem:combine:'))
        row = deepcopy(original)
        first, second = row['participants']
        foreign = 'daewoon.period_0.cycle.stem'
        graph['contexts']['daewoon.period_0'] = {'scope': 'daewoon'}
        graph['characters'][foreign] = {**graph['characters'][second], 'context_id': 'daewoon.period_0', 'position': 'cycle'}
        row.update(source_relation_id='cycle:stem:combine:fixture', participants=[first, foreign], formation_candidates=[])
        graph['relations']['fixture'] = row
        query = queries_for_relation(graph, 'fixture')[0]
        self.assertEqual(query.facts['scope'], 'cross_context')
        self.assertNotIn('is_adjacent', query.facts)
        with TemporaryDirectory() as directory:
            database = Path(directory) / 'interpretations.db'
            seed_database(generate_catalog()['rules'], database)
            self.assertIsNone(find_rule(query, database, include_unwritten=True))
