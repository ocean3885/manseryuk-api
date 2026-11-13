"""오행 개수 목록을 세력 우세·보완 판단과 혼동하지 않는다."""
import unittest
from services.five_elements import analyze_five_elements


class FiveElementCountsTests(unittest.TestCase):
    def test_count_labels_and_existing_weighted_index_have_distinct_meanings(self):
        result = analyze_five_elements(list('甲甲甲丙'), list('子寅午辰'), [{'점수': 0.5}] * 4)
        self.assertEqual(result['counts'], {'목': 4, '화': 2, '토': 1, '금': 0, '수': 1})
        self.assertEqual(result['frequent_elements'], ['목'])
        self.assertEqual(result['absent_elements'], ['금'])
        self.assertEqual(result['percentages'], {'목': 50.0, '화': 25.0, '토': 12.5, '금': 0.0, '수': 12.5})
        self.assertEqual(result['scores'], {'목': 6.5, '화': 3.0, '토': 1.0, '금': 0.0, '수': 1.0})
        self.assertEqual(result['distribution_basis'], 'eight_visible_characters')
        self.assertEqual(result['score_meaning'], 'provisional_weighted_index')
        self.assertTrue({'dominant', 'deficient'}.isdisjoint(result))

    def test_three_characters_is_the_inclusive_frequency_threshold(self):
        result = analyze_five_elements(list('甲乙丙丁'), list('寅辰申子'), [])
        self.assertEqual(result['counts']['목'], 3)
        self.assertEqual(result['counts']['화'], 2)
        self.assertEqual(result['frequent_elements'], ['목'])
        self.assertEqual(result['absent_elements'], [])
