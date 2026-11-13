"""실제 저장소 기반 작성용 내보내기·분할·원본 보존을 검증한다."""
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from core.interpretation_database import seed_database
from services.interpretation_catalog import generate_catalog
from services.interpretation_export import authoring_document


class InterpretationExportTests(unittest.TestCase):
    root = Path(__file__).resolve().parents[1]

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.database = self.directory / 'interpretations.db'
        self.catalog = generate_catalog()
        seed_database(self.catalog['rules'], self.database)

    def command(self, *arguments):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / 'interpretation_rules.py'),
                               'export', '--database', str(self.database), *map(str, arguments)],
                              cwd=self.root, capture_output=True, text=True, encoding='utf-8', check=False)

    def test_exports_actual_rows_with_stable_identity_and_guide_without_modifying_database(self):
        before = self.database.read_bytes()
        document = authoring_document(self.database)
        self.assertEqual(document, authoring_document(self.database))
        self.assertEqual(document['total_matching'], 565)
        self.assertEqual(document['exported_count'], 565)
        self.assertIsNone(document['next_offset'])
        self.assertEqual(document['writing_guide']['editable_fields'], ['explanation'])
        self.assertEqual(document['writing_guide']['relation_labels']['stem']['combine'], '천간합')
        self.assertEqual(document['writing_guide']['relation_labels']['branch']['combine'], '육합')
        expected = {r['rule_id']: {k: v for k, v in r.items() if k != 'content_status'}
                    for r in self.catalog['rules']}
        self.assertEqual({r['rule_id']: r for r in document['rules']}, expected)
        self.assertEqual(self.database.read_bytes(), before)

    def test_filtering_uses_current_database_status_and_preserves_authored_text(self):
        first, second = self.catalog['rules'][:2]
        with closing(sqlite3.connect(self.database)) as db, db:
            for rule, status in ((first, 'draft'), (second, 'ready')):
                db.execute('UPDATE interpretation_rules SET explanation=?,content_status=? WHERE rule_id=?',
                           ('DB에 작성한 해설', status, rule['rule_id']))
        self.assertEqual(authoring_document(self.database)['total_matching'], 563)
        for status, rule in (('draft', first), ('ready', second)):
            document = authoring_document(self.database, status=status)
            self.assertEqual(document['exported_count'], 1)
            self.assertEqual(document['rules'][0]['rule_id'], rule['rule_id'])
            self.assertEqual(document['rules'][0]['explanation'], 'DB에 작성한 해설')
        control = authoring_document(self.database, layer='stem', relation_type='control')
        self.assertEqual(control['exported_count'], 20)
        self.assertTrue(all(r['layer'] == 'stem' and r['relation_type'] == 'control' for r in control['rules']))

    def test_pagination_is_ordered_without_overlap_and_reports_remaining_offset(self):
        complete = authoring_document(self.database)['rules']
        first = authoring_document(self.database, limit=7)
        second = authoring_document(self.database, limit=7, offset=first['next_offset'])
        self.assertEqual(first['rules'] + second['rules'], complete[:14])
        self.assertEqual(second['next_offset'], 14)
        last = authoring_document(self.database, offset=560, limit=10)
        self.assertEqual(last['exported_count'], 5)
        self.assertIsNone(last['next_offset'])
        exhausted = authoring_document(self.database, offset=999, limit=10)
        self.assertEqual(exhausted['rules'], [])
        self.assertIsNone(exhausted['next_offset'])

    def test_cli_writes_utf8_json_and_does_not_overwrite_existing_authoring_file(self):
        output = self.directory / 'writing' / 'sample.json'
        result = self.command('--output', output, '--limit', 20)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['exported_count'], 20)
        self.assertEqual(json.loads(output.read_text(encoding='utf-8')), authoring_document(self.database, limit=20))
        output.write_text('작성이 진행 중인 파일', encoding='utf-8')
        result = self.command('--output', output, '--limit', 20)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_text(encoding='utf-8'), '작성이 진행 중인 파일')

    def test_cli_protects_database_alias_and_seed_files(self):
        alias = self.directory / 'alias.json'
        alias.hardlink_to(self.database)
        seed = self.directory / 'patterns.json'
        seed.write_text(json.dumps(self.catalog, ensure_ascii=False), encoding='utf-8')
        for output in (alias, seed, self.database, self.root / 'manseryuk.db'):
            with self.subTest(output=output):
                before = output.read_bytes()
                result = self.command('--output', output)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(output.read_bytes(), before)

    def test_invalid_selection_fails_before_writing_output(self):
        output = self.directory / 'invalid.json'
        for arguments in (('--limit', 0), ('--offset', -1), ('--layer', 'stem', '--relation-type', 'trine'),
                          ('--relation-type', 'opening')):
            with self.subTest(arguments=arguments):
                result = self.command('--output', output, *arguments)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())

    def test_missing_database_is_not_created(self):
        self.database.unlink()
        output = self.directory / 'missing.json'
        result = self.command('--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.database.exists())
        self.assertFalse(output.exists())

    def test_invalid_stored_rule_is_not_exported_as_authoring_input(self):
        with closing(sqlite3.connect(self.database)) as db, db:
            db.execute('UPDATE interpretation_rules SET rule_id=? WHERE rule_id=?',
                       ('corrupted', self.catalog['rules'][0]['rule_id']))
        output = self.directory / 'invalid.json'
        result = self.command('--output', output)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())
