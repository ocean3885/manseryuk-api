from pathlib import Path
import unittest
from unittest.mock import Mock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from services.saju_orchestrator import get_full_saju_data
from services.birth_input import validate_birth_input

QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')
ROUTES = ('/', '/character-details', '/relation-index', '/cycle-analysis')
DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'


class BirthInputTests(unittest.TestCase):
    def test_invalid_inputs_fail_before_database_access(self):
        for change in [dict(hour=-1), dict(hour=24), dict(min=-1), dict(min=60),
                       dict(year=0), dict(year=10000), dict(month='0'), dict(month='13'),
                       dict(day='0'), dict(day='32'), dict(month='bad'),
                       dict(year=2023, month='2', day='29'), dict(month='4', day='31'),
                       dict(sl='lun', month='13'), dict(sl='lun_y', day='31'),
                       dict(sl='invalid'), dict(gen='invalid')]:
            db = Mock()
            with self.subTest(change=change), self.assertRaises(HTTPException) as error:
                get_full_saju_data(**{**QUERY, **change}, db=db)
            self.assertEqual(error.exception.status_code, 400)
            db.query.assert_not_called()

    def test_calendar_specific_validation_and_leading_zeroes(self):
        self.assertEqual(validate_birth_input(2024, '02', '29', 0, 0, 'sol', '여'), ('2', '29'))
        # Lunar dates cannot be validated with Gregorian month lengths.
        self.assertEqual(validate_birth_input(2023, '02', '30', 23, 59, 'lun', '남'), ('2', '30'))


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class CalendarLookupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def lookup(self, **change):
        with Session(self.engine) as session:
            return get_full_saju_data(**{**QUERY, **change}, db=session)

    def test_normal_and_leap_lunar_months_select_explicit_records(self):
        for sl, solar in [('lun', (2023, '2', '20')), ('lun_y', (2023, '3', '22'))]:
            with self.subTest(sl=sl):
                lunar = self.lookup(year=2023, month='02', day='01', sl=sl)
                expected = self.lookup(year=solar[0], month=solar[1], day=solar[2])
                self.assertEqual(lunar['calendar']['solar'], expected['calendar']['solar'])
                self.assertEqual(lunar['four_pillars'], expected['four_pillars'])

    def test_nonexistent_leap_month_does_not_fall_back_to_normal(self):
        self.assertIsNotNone(self.lookup(year=2024, month='2', day='1', sl='lun'))
        for change in [dict(year=2024, month='2', day='1', sl='lun_y'),
                       dict(year=2023, month='1', day='30', sl='lun'),
                       dict(year=2023, month='2', day='30', sl='lun_y'),
                       dict(year=1899, month='1', day='1'),
                       dict(year=2101, month='1', day='1')]:
            with self.subTest(change=change), self.assertRaises(HTTPException) as error:
                self.lookup(**change)
            self.assertEqual(error.exception.status_code, 404)

    def test_database_solar_boundaries_are_available(self):
        for year, month, day in [(1900, '1', '1'), (2100, '12', '31')]:
            with self.subTest(year=year):
                result = self.lookup(year=year, month=month, day=day)
                self.assertEqual(result['calendar']['solar'], dict(year=year, month=month, day=day))

    def test_valid_time_edges_and_calendar_leap_day(self):
        for hour, minute, branch in [(0, 0, '子'), (23, 59, '子'), (1, 30, '子'), (1, 31, '丑')]:
            with self.subTest(hour=hour, minute=minute):
                result = self.lookup(year=2024, month='2', day='29', hour=hour, min=minute)
                self.assertEqual(result['four_pillars']['hour']['ji']['ch'], branch)

    def test_all_http_routes_share_validation(self):
        def readonly_db():
            with Session(self.engine) as session:
                yield session
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        try:
            with TestClient(app) as client:
                for route in ROUTES:
                    params = {**QUERY, **({'daewoon_index': 0} if route == '/cycle-analysis' else {})}
                    for change, code in [(dict(hour=24), 400), (dict(min=60), 400),
                                         (dict(year=2023, month='2', day='29'), 400),
                                         (dict(year=2024, month='2', day='1', sl='lun_y'), 404),
                                         (dict(hour='bad'), 422)]:
                        with self.subTest(route=route, change=change):
                            self.assertEqual(client.get(route, params={**params, **change}).status_code, code)
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
