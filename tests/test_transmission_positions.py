"""지장간 투출이 반복된 천간의 모든 위치를 보존하는지 검증한다."""

import unittest

from services.analysis import (
    analyze_palja_integrated, get_jijanggan, get_transmitted_info,
)
from services.constants import JIJANGGAN_DETAILED
from services.five_elements import STEM_ELEMENT_MAP


class TransmissionPositionTests(unittest.TestCase):
    def test_repeated_visible_stem_has_two_position_links(self):
        info = get_transmitted_info('未', 2, list('乙己己庚'), '己')
        ji = [item for item in info['transmitted'] if item['stem'] == '己']
        self.assertEqual([item['stem_idx'] for item in ji], [1, 2])
        self.assertEqual([item['from_idx'] for item in ji], [2, 2])

        chart = analyze_palja_integrated(list('乙己己庚'), list('巳丑未午'))
        day = chart['pillars']['day']['branch']['transmitted']
        self.assertEqual([item['stem_idx'] for item in day
                          if item['stem'] == '己'], [1, 2])

    def test_no_visible_match_remains_hidden_once(self):
        info = get_transmitted_info('未', 2, list('甲甲甲甲'), '甲')
        self.assertFalse(info['transmitted'])
        self.assertEqual([item['stem'] for item in info['hidden']], ['丁', '乙', '己'])

    def test_detailed_hidden_stems_are_consistent_with_pillar_list(self):
        chart = analyze_palja_integrated(list('壬甲甲甲'), list('子午辰寅'))
        year = chart['pillars']['year']['branch']
        self.assertEqual(year['jijanggan'], ['壬', '癸'])
        self.assertEqual([(item['stem'], item['stem_idx'], item['stem_pos'])
                          for item in year['transmitted']], [('壬', 0, '초기')])
        self.assertEqual([item['stem'] for item in year['hidden']], ['癸'])

    def test_all_branches_use_the_same_hidden_stem_catalog(self):
        for branch, detailed in JIJANGGAN_DETAILED.items():
            expected_chars = [item['char'] for item in detailed]
            self.assertEqual(get_jijanggan(branch), expected_chars)
            for stem in STEM_ELEMENT_MAP:
                with self.subTest(branch=branch, stem=stem):
                    info = get_transmitted_info(branch, 0, [stem] * 4, stem)
                    self.assertEqual(
                        [(item['stem'], item['stem_idx'])
                         for item in info['transmitted']],
                        [(stem, index) for hidden in expected_chars
                         if hidden == stem for index in range(4)],
                    )
                    self.assertEqual([item['stem'] for item in info['hidden']],
                                     [hidden for hidden in expected_chars
                                      if hidden != stem])


if __name__ == '__main__':
    unittest.main()
