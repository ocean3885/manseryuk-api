"""조회 경로를 인덱스로 바꾸면서 데이터와 중복 허용을 보존한다."""
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from scripts.add_calendar_lookup_indexes import add_lookup_indexes, LOOKUP_INDEX_NAMES


class CalendarLookupIndexesTests(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database = Path(self.directory.name) / 'calendar.db'
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE TABLE calenda_data (cd_no INTEGER PRIMARY KEY, cd_sy INTEGER, '
                       'cd_sm TEXT, cd_sd TEXT, cd_ly INTEGER, cd_lm TEXT, '
                       'cd_ld TEXT, cd_leap_month TEXT)')
            self.rows = [(1, 2023, '2', '20', 2023, '2', '1', '0'),
                         (2, 2023, '3', '22', 2023, '2', '1', '1'),
                         (3, 2023, '3', '23', 2023, '2', '2', '1')]
            # 인덱스를 UNIQUE로 만들어 기존 중복 날짜 자료를 삭제·거부하면 안 된다.
            self.rows.append((4, *self.rows[-1][1:]))
            db.executemany('INSERT INTO calenda_data VALUES (?,?,?,?,?,?,?,?)', self.rows)

    def test_indexes_are_used_and_all_rows_including_duplicates_are_preserved(self):
        result = add_lookup_indexes(self.database)
        self.assertEqual(result['created'], list(LOOKUP_INDEX_NAMES))
        with sqlite3.connect(self.database) as db:
            self.assertEqual(db.execute('SELECT * FROM calenda_data ORDER BY rowid').fetchall(), self.rows)
            for sql, params, expected in (
                ('SELECT * FROM calenda_data WHERE cd_sy=? AND cd_sm=? AND cd_sd=?',
                 (2023, '3', '22'), 'ix_calenda_data_solar_date'),
                ('SELECT * FROM calenda_data WHERE cd_ly=? AND cd_lm=? AND cd_ld=? AND cd_leap_month=?',
                 (2023, '2', '1', '1'), 'ix_calenda_data_lunar_date'),
                ('SELECT * FROM calenda_data WHERE cd_no>? AND cd_no<? ORDER BY cd_no LIMIT 1',
                 (0, 35), 'INTEGER PRIMARY KEY'),
            ):
                with self.subTest(index=expected):
                    plan = str(db.execute('EXPLAIN QUERY PLAN ' + sql, params).fetchall())
                    self.assertIn(expected, plan)
                    self.assertNotIn('SCAN calenda_data', plan)

    def test_reapplication_does_not_add_more_indexes(self):
        add_lookup_indexes(self.database)
        result = add_lookup_indexes(self.database)
        self.assertEqual(result, {'created': [], 'existing': list(LOOKUP_INDEX_NAMES)})
        with sqlite3.connect(self.database) as db:
            self.assertEqual(len(db.execute('PRAGMA index_list(calenda_data)').fetchall()), 2)

    def test_missing_database_or_table_does_not_create_calendar_data(self):
        missing = self.database.parent / 'missing.db'
        with self.assertRaises(FileNotFoundError):
            add_lookup_indexes(missing)
        self.assertFalse(missing.exists())
        empty = self.database.parent / 'empty.db'
        with sqlite3.connect(empty):
            pass
        with self.assertRaises(ValueError):
            add_lookup_indexes(empty)
        with sqlite3.connect(empty) as db:
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(), [])

    def test_conflicting_index_is_reported_before_other_indexes_are_created(self):
        with sqlite3.connect(self.database) as db:
            db.execute('CREATE INDEX ix_calenda_data_lunar_date ON calenda_data (cd_no)')
        with self.assertRaisesRegex(ValueError, '기존 인덱스 정의'):
            add_lookup_indexes(self.database)
        with sqlite3.connect(self.database) as db:
            self.assertEqual([row[1] for row in db.execute('PRAGMA index_list(calenda_data)')],
                             ['ix_calenda_data_lunar_date'])


if __name__ == '__main__':
    unittest.main()
