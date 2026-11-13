"""고의 역할은 저장 오행·기존 지장간 십성으로 분류하고 본기 십성과 구별한다."""
from copy import deepcopy
import unittest

from pydantic import TypeAdapter, ValidationError
from schemas.natal_analysis import StorehouseInfo
from services.analysis import analyze_palja_integrated
from services.calculator import get_ten_star_branch
from services.ko_analysis import get_storehouse_info


def analyze(stems, branches):
    return analyze_palja_integrated(list(stems), list(branches))['pillars']


class StorehouseTests(unittest.TestCase):
    def test_all_ten_day_stems_and_four_storehouses(self):
        # 辰·戌·丑·未의 저장 오행은 水·火·金·木이다.
        expected = {
            '甲乙': ('인성고', '식상고', '관성고', '비겁고'),
            '丙丁': ('관성고', '비겁고', '재고', '인성고'),
            '戊己': ('재고', '인성고', '식상고', '관성고'),
            '庚辛': ('식상고', '관성고', '비겁고', '재고'),
            '壬癸': ('비겁고', '재고', '인성고', '식상고'),
        }
        checked = 0
        for day_stems, roles in expected.items():
            for day_stem in day_stems:
                details = analyze(day_stem * 4, '辰戌丑未')
                for pillar, element, role in zip(('year', 'month', 'day', 'hour'), '水火金木', roles):
                    with self.subTest(day_stem=day_stem, pillar=pillar):
                        self.assertEqual(details[pillar]['branch']['storehouse'],
                                         {'stored_element': element, 'role': role})
                        checked += 1
        self.assertEqual(checked, 40)

    def test_other_eight_branches_explicitly_return_null(self):
        for branches in ('子寅卯巳', '午申酉亥'):
            for day_stem in '甲乙丙丁戊己庚辛壬癸':
                with self.subTest(branches=branches, day_stem=day_stem):
                    details = analyze(day_stem * 4, branches)
                    self.assertTrue(all(p['branch']['storehouse'] is None for p in details.values()))

    def test_branch_ten_star_and_storehouse_role_are_different(self):
        self.assertEqual(get_ten_star_branch('甲', '丑'), '정재')
        result = analyze('甲甲甲甲', '丑子寅卯')
        self.assertEqual(result['year']['branch']['storehouse'],
                         {'stored_element': '金', 'role': '관성고'})
        self.assertEqual(result['year']['branch']['relations']['six_haps'][0]['my_ten_star'], '정재')

    def test_repeated_transmission_and_positions_do_not_duplicate_or_change_role(self):
        result = analyze('辛辛甲辛', '丑子寅丑')
        for key in ('year', 'hour'):
            branch = result[key]['branch']
            self.assertEqual(sum(item['stem'] == '辛' for item in branch['transmitted']), 3)
            self.assertEqual(branch['storehouse'], {'stored_element': '金', 'role': '관성고'})

    def test_month_position_and_clash_do_not_add_size_or_open_judgments(self):
        for branches, position in [('丑子寅卯', 'year'), ('子丑未卯', 'month'), ('未卯子丑', 'hour')]:
            with self.subTest(branches=branches):
                info = analyze('甲甲甲甲', branches)[position]['branch']['storehouse']
                self.assertEqual(info, {'stored_element': '金', 'role': '관성고'})
                self.assertEqual(set(info), {'stored_element', 'role'})

    def test_classification_reuses_existing_star_information_without_mutating_it(self):
        details = [{'stem': '辛', 'stem_ten_star': '정관'},
                   {'stem': '癸', 'stem_ten_star': '정인'},
                   {'stem': '己', 'stem_ten_star': '정재'}]
        before = deepcopy(details)
        self.assertEqual(get_storehouse_info('丑', details), {'stored_element': '金', 'role': '관성고'})
        self.assertEqual(details, before)
        for invalid in ([], [{'stem': '辛', 'stem_ten_star': '정관'}, {'stem': '辛', 'stem_ten_star': '정재'}]):
            with self.assertRaisesRegex(ValueError, '지장간 십성 정보'):
                get_storehouse_info('丑', invalid)

    def test_schema_validates_only_the_two_basic_classification_fields(self):
        adapter = TypeAdapter(StorehouseInfo)
        valid = {'stored_element': '金', 'role': '관성고'}
        self.assertEqual(adapter.validate_python(valid), valid)
        for value in (dict(valid, is_open=False), dict(valid, role='미정'), dict(valid, stored_element='土')):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                adapter.validate_python(value)
