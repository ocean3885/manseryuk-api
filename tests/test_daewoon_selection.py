import unittest
from copy import deepcopy
from services.daewoon import build_daewoon
from services.daewoon_selection import select_daewoon_year


class DaewoonSelectionTests(unittest.TestCase):
    def test_fractional_start_ages_have_consistent_year_boundaries(self):
        for age in (0.0, 0.1, 2.3, 2.9, 10.0):
            start = 2000 + int(age)
            for year, expected in [(start - 1, None), (start, 0), (start + 9, 0),
                                   (start + 10, 1), (start + 19, 1), (start + 20, None)]:
                with self.subTest(age=age, year=year):
                    result = build_daewoon(['순행', ['甲', '乙'], ['子', '丑']], age, 2000,
                                           current_year=year, day_stem='甲')
                    self.assertEqual(result['current']['index'] if result['current'] else None, expected)
                    self.assertEqual(result['selection_status'], 'selected' if expected is not None else
                                     'before_first_period' if year < start else 'after_last_period')
                    self.assertEqual(result['list'][0]['selection_end_year_exclusive'], start + 10)
                    selected, _ = select_daewoon_year(result['list'], year)
                    self.assertEqual(selected['index'] if selected else None, expected)

    def test_empty_and_unsorted_periods(self):
        self.assertEqual(select_daewoon_year([], 2026), (None, 'unavailable'))
        with self.assertRaises(ValueError):
            select_daewoon_year([dict(start_year=2000), dict(start_year=1999)], 2026)

    def test_display_end_does_not_change_selection_or_mutate_periods(self):
        periods = [dict(index=0, start_year=2000, end_year=2010),
                   dict(index=1, start_year=2010, end_year=2020)]
        before = deepcopy(periods)
        self.assertEqual(select_daewoon_year(periods, 2010)[0]['index'], 1)
        self.assertEqual(select_daewoon_year(periods, 2020), (None, 'after_last_period'))
        self.assertEqual(periods, before)
