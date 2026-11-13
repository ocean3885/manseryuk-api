"""요약은 위치별 상세 사실을 누락·중복·강약 단정 없이 표시한다."""
from copy import deepcopy
from itertools import permutations, product
import unittest

from services.analysis import analyze_palja_integrated, _summarize_pillars
from services.interaction_matrix import build_interaction_matrix
from services.relation_rules import STEM_RESTRAIN


def analyze(stems, branches):
    return analyze_palja_integrated(list(stems), list(branches))


class AnalysisSummaryTests(unittest.TestCase):
    def test_repeated_clashes_keep_all_pairs_and_self_punishment_status(self):
        rows = analyze('甲甲甲甲', '子午午午')['summary']['branch_interactions']
        self.assertEqual(len(rows), 6)
        clashes = [r for r in rows if ': 충 관계' in r]
        self.assertEqual(len(clashes), 3)
        for position in ('월', '일', '시'):
            self.assertTrue(any(f'년지 子(정인) · {position}지 午(상관)' in r for r in clashes))
        self.assertIn('월지 午(상관) · 시지 午(상관): 자형 후보', rows)
        self.assertIn('월지 午(상관) · 일지 午(상관): 자형 관계', rows)

    def test_repeated_six_hap_partners_are_four_distinct_facts(self):
        rows = analyze('甲甲甲甲', '子丑丑子')['summary']['branch_interactions']
        self.assertEqual(len(rows), 4)
        self.assertEqual(len(set(rows)), 4)
        self.assertTrue(all('육합 조합(土 후보)' in r for r in rows))
        self.assertTrue(any('년지 子' in r and '일지 丑' in r for r in rows))
        self.assertTrue(any('월지 丑' in r and '시지 子' in r for r in rows))

    def test_repeated_groups_are_one_summary_with_both_actual_formations(self):
        for branches, label in [('亥卯未亥', '삼합 조합'), ('寅卯辰寅', '방합 후보'),
                                ('寅巳申申', '삼형 구조')]:
            with self.subTest(branches=branches):
                rows = analyze('甲甲甲甲', branches)['summary']['branch_interactions']
                groups = [r for r in rows if label in r]
                self.assertEqual(len(groups), 1)
                self.assertIn('세 자리 조합 2개', groups[0])
                for position in ('년지', '월지', '일지', '시지'):
                    self.assertIn(position, groups[0])
                self.assertNotIn('성립', groups[0])

    def test_stem_control_preserves_direction_and_day_identity(self):
        forward = analyze('甲戊戊戊', '子子子子')['summary']['stem_interactions']
        self.assertEqual(len(forward), 3)
        self.assertIn('년간 甲(편관) → 일간 戊(일간): 천간극 관계', forward)
        self.assertTrue(all(r.startswith('년간 甲(편관) → ') for r in forward))
        reverse = analyze('戊戊戊甲', '子子子子')['summary']['stem_interactions']
        self.assertEqual(len(reverse), 3)
        self.assertIn('시간 甲(편관) → 일간 戊(일간): 천간극 관계', reverse)
        self.assertTrue(all(r.startswith('시간 甲(편관) → ') for r in reverse))

    def test_summary_count_matches_matrix_facts_across_pairs_and_repeated_groups(self):
        branches = {a + b + '子子' for a, b in product('子丑寅卯辰巳午未申酉戌亥', repeat=2)}
        for group in ('寅午戌', '亥卯未', '申子辰', '巳酉丑',
                      '寅卯辰', '巳午未', '申酉戌', '亥子丑', '寅巳申', '丑戌未'):
            branches.update(''.join(p) for p in permutations(group + group[1]))
        branches.update(('午子丑寅', '子午丑寅', '巳亥卯未', '亥卯酉未', '亥卯未丑'))
        cases = [('甲己丙辛', b) for b in sorted(branches)]
        cases.extend((a + '甲甲' + b, '子子子子') for a, b in product('甲乙丙丁戊己庚辛壬癸', repeat=2))
        for stems, branch_text in cases:
            with self.subTest(stems=stems, branches=branch_text):
                result = analyze(stems, branch_text)
                matrix = build_interaction_matrix(list(stems), list(branch_text), stems[2])['matrix']
                summary = result['summary']
                self.assertEqual(len(summary['branch_interactions']),
                                 sum(row['category'] == '지지' for row in matrix))
                controls = sum(i != j and (first, second) in STEM_RESTRAIN
                               for i, first in enumerate(stems) for j, second in enumerate(stems))
                self.assertEqual(len(summary['stem_interactions']),
                                 sum(row['category'] == '천간' for row in matrix) + controls)
                for kind in ('stem_interactions', 'branch_interactions'):
                    self.assertEqual(len(summary[kind]), len(set(summary[kind])))

    def test_summary_uses_details_without_mutation_or_source_order_dependency(self):
        details = analyze('甲己丙辛', '亥卯未亥')['pillars']
        expected = _summarize_pillars(details)
        changed = {k: deepcopy(v) for k, v in reversed(list(details.items()))}
        for pillar in changed.values():
            relations = pillar['branch']['relations']
            pillar['branch']['relations'] = {k: list(reversed(v)) for k, v in reversed(list(relations.items()))}
        before = deepcopy(changed)
        self.assertEqual(_summarize_pillars(changed), expected)
        self.assertEqual(changed, before)

    def test_rooting_summary_counts_same_pillar_flags_and_empty_relations(self):
        for branches, expected in [('子子子子', 0), ('辰子子子', 1), ('辰辰辰辰', 4)]:
            with self.subTest(branches=branches):
                result = analyze('甲甲甲甲', branches)
                summary = result['summary']
                self.assertIn(f'동주 통근 {expected}개', summary['rooting_summary'])
                self.assertIn(f'동주 무근 {4 - expected}개', summary['rooting_summary'])
                self.assertIn('원국 전체 신강·신약 미판정', summary['rooting_summary'])
                self.assertNotIn('total_energy_balance', summary)
        empty = analyze('甲甲甲甲', '子子子子')['summary']
        self.assertEqual(empty['branch_interactions'], [])
        self.assertEqual(empty['stem_interactions'], [])
