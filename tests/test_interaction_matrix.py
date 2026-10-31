"""반복 글자의 위치별 관계와 다자 관계의 참여/성립 조합 검증."""
from itertools import combinations, permutations
import unittest

from schemas.saju_analysis import BranchDynamics, InteractionsInfo
from services.branch_dynamics import analyze_branch_dynamics
from services.branch_relations import check_six_hap, check_six_haps, check_three_hap, check_square_hap, get_relations_for_branch
from services.constants import SIX_HAPS
from services.interaction_matrix import build_interaction_matrix

PILLARS = ['year', 'month', 'day', 'hour']


def matrix(branches, stems='甲甲甲甲'):
    return build_interaction_matrix(list(stems), list(branches), stems[2])


def pairs(result, kind):
    return {(r['from_pillar'], r['to_pillar']) for r in result['matrix'] if r['type'] == kind}


class InteractionMatrixTests(unittest.TestCase):
    def test_break_and_clash_are_active_at_adjacent_and_distant_positions(self):
        cases = [
            ('子午辰寅', 'year', 'month', '충(沖)', 1.0),
            ('子辰寅午', 'year', 'hour', '충(沖)', 0.5),
            ('子卯辰寅', 'year', 'month', '파(破)', 1.0),
            ('子辰午卯', 'year', 'hour', '파(破)', 0.5),
        ]
        for branches, left, right, kind, weight in cases:
            with self.subTest(branches=branches, kind=kind):
                relation = next(item for item in matrix(branches)['matrix']
                                if item['type'] == kind
                                and item['from_pillar'] == left
                                and item['to_pillar'] == right)
                self.assertEqual(relation['activation_status'], 'active')
                self.assertEqual(relation['activation_rule_id'],
                                 'branch:pair_presence_active_v1')
                self.assertEqual(relation['weight'], weight)

    def test_pierce_pair_punishment_and_unblocked_combine_are_active_at_any_distance(self):
        cases = [
            ('寅巳午子', 'year', 'month', '천(穿)', 1.0),
            ('寅子午巳', 'year', 'hour', '천(穿)', 0.5),
            ('丑戌辰寅', 'year', 'month', '형(刑)', 1.0),
            ('戌子卯未', 'year', 'hour', '형(刑)', 0.5),
            ('寅亥辰子', 'year', 'month', '육합(六合)', 1.0),
            ('辰寅午酉', 'year', 'hour', '육합(六合)', 0.5),
        ]
        for branches, left, right, kind, weight in cases:
            with self.subTest(branches=branches, kind=kind):
                relation = next(item for item in matrix(branches)['matrix']
                                if item['type'] == kind
                                and item['from_pillar'] == left
                                and item['to_pillar'] == right)
                self.assertEqual(relation['activation_status'], 'active')
                self.assertEqual(relation['activation_rule_id'],
                                 'branch:pair_presence_active_v1')
                self.assertEqual(relation['weight'], weight)

    def test_clash_condition_and_adjacent_self_punishment_remain_separate(self):
        for branches, status in [('子午丑寅', 'suppressed'),
                                 ('午子丑寅', 'conditional')]:
            with self.subTest(branches=branches):
                combination = next(item for item in matrix(branches)['matrix']
                                   if item['type'] == '육합(六合)')
                self.assertEqual(combination['activation_status'], status)
                self.assertIsNone(combination['activation_rule_id'])
        self_punishment = next(item for item in matrix('午午子辰')['matrix']
                               if item['type'] == '형(刑)')
        self.assertEqual(self_punishment['activation_status'], 'active')
        self.assertEqual(self_punishment['activation_rule_id'],
                         'branch:adjacent_self_punishment_active_v1')

    def test_self_punishment_requires_adjacency_for_each_position_pair(self):
        for branch in '辰午酉亥':
            with self.subTest(branch=branch):
                result = matrix(branch * 3 + '子')
                punishments = {
                    tuple(item['participants']): item
                    for item in result['matrix']
                    if item['type'] == '형(刑)' and item['name'] == '자형'
                }
                self.assertEqual(set(punishments), {
                    ('year', 'month'), ('year', 'day'), ('month', 'day')})
                for pair in (('year', 'month'), ('month', 'day')):
                    self.assertEqual(punishments[pair]['activation_status'], 'active')
                    self.assertEqual(punishments[pair]['score'], 0)
                self.assertEqual(punishments[('year', 'day')]['activation_status'],
                                 'candidate_only')
                self.assertIsNone(punishments[('year', 'day')]['activation_rule_id'])

    def test_six_piercing_pairs_use_cheon_type_in_both_orders(self):
        for first, second in [('子', '未'), ('丑', '午'), ('寅', '巳'),
                              ('卯', '辰'), ('申', '亥'), ('酉', '戌')]:
            for left, right in ((first, second), (second, first)):
                with self.subTest(pair=left + right):
                    items = [item for item in matrix(left + right + left + right)['matrix']
                             if item['category'] == '지지' and
                             item['participants'] == ['year', 'month']]
                    self.assertEqual([item['type'] for item in items
                                      if item['type'] == '천(穿)'], ['천(穿)'])
                    self.assertFalse(any('害' in item['type'] for item in items))

    def test_six_hap_keeps_legacy_single_and_adds_all_partners(self):
        branches = list('子丑丑子')
        all_haps = check_six_haps('子', 0, branches, '甲')
        self.assertEqual([r['with_index'] for r in all_haps], [1, 2])
        self.assertEqual(check_six_hap('子', 0, branches, '甲'), all_haps[0])
        relations = get_relations_for_branch('子', 0, branches, list('甲甲甲甲'))
        self.assertEqual(relations['six_haps'], all_haps[0])
        self.assertEqual(relations['six_haps_all'], all_haps)
        self.assertEqual(matrix(branches)['harmony_score'], 5.1)

    def test_six_hap_hidden_stem_candidates_survive_schema(self):
        result = matrix('午未子丑')
        encoded = InteractionsInfo.model_validate(result).model_dump()
        item = next(r for r in encoded['matrix']
                    if r['type'] == '육합(六合)' and
                    r['participants'] == ['year', 'month'])
        self.assertEqual(item['candidate_element'], '土')
        self.assertIsNone(item['transformed_element'])
        self.assertEqual(item['candidate_hidden_stem_effects'], [{
            'pillar': 'month', 'branch': '未', 'stem': '乙',
            'effect': 'closure', 'activation_status': 'candidate_only',
        }])

    def test_combination_elements_are_candidates_until_transformation_is_checked(self):
        cases = (
            ('천간합(天干合)', '甲己丙辛', '寅午戌子', {'土', '水'}),
            ('반합(半合)', '甲甲甲甲', '寅午子丑', {'火'}),
            ('삼합(三合)', '甲甲甲甲', '寅午戌子', {'火'}),
            ('방합(方合)', '甲甲甲甲', '巳午未子', {'火'}),
        )
        for kind, stems, branches, expected_elements in cases:
            with self.subTest(kind=kind):
                result = matrix(branches, stems)
                self.assertEqual(result['rule_version'], '1.3.0')
                encoded = InteractionsInfo.model_validate(result).model_dump()
                items = [r for r in encoded['matrix'] if r['type'] == kind]
                self.assertEqual({r['candidate_element'] for r in items},
                                 expected_elements)
                self.assertTrue(all(r['transformed_element'] is None for r in items))

        suppressed = matrix('亥酉卯未')
        group = next(r for r in suppressed['matrix'] if r['type'] == '삼합(三合)')
        self.assertEqual(group['activation_status'], 'suppressed')
        self.assertEqual(group['candidate_element'], '木')
        self.assertIsNone(group['transformed_element'])
        dynamics = analyze_branch_dynamics(
            list('甲甲甲甲'), list('亥酉卯未'), suppressed['matrix'])
        encoded_dynamics = BranchDynamics.model_validate(dynamics).model_dump()
        dynamics_group = next(g for g in encoded_dynamics['groups']
                              if g['type'] == '삼합(三合)')
        self.assertEqual(dynamics_group['candidate_element'], '木')
        self.assertIsNone(dynamics_group['transformed_element'])
        self.assertEqual(dynamics_group['element'], '木')  # 호환용 후보 별칭

    def test_every_six_hap_position_pair_survives_permutations(self):
        for branches in sorted(set(permutations('子丑丑子'))):
            with self.subTest(branches=branches):
                expected = {(PILLARS[i], PILLARS[j]) for i, j in combinations(range(4), 2)
                            if (branches[i], branches[j]) in SIX_HAPS or (branches[j], branches[i]) in SIX_HAPS}
                self.assertEqual(pairs(matrix(branches), '육합(六合)'), expected)

    def test_group_coverage_keeps_pair_candidate_without_double_counting(self):
        result = matrix('巳午未寅')
        encoded = InteractionsInfo.model_validate(result).model_dump()
        group = next(r for r in encoded['matrix'] if r['type'] == '방합(方合)')
        included = next(r for r in encoded['matrix']
                        if r['type'] == '육합(六合)' and
                        r['participants'] == ['month', 'day'])
        outside = next(r for r in encoded['matrix']
                       if r['type'] == '반합(半合)' and
                       r['participants'] == ['month', 'hour'])
        self.assertEqual((group['score'], group['score_contribution']), (3.5, 3.5))
        self.assertEqual((included['score'], included['score_contribution']),
                         (1.5, 0.0))
        self.assertEqual(included['score_covered_by'], group['relation_id'])
        self.assertEqual((outside['score'], outside['score_contribution']),
                         (0.91, 0.91))
        self.assertIsNone(outside['score_covered_by'])
        self.assertEqual(result['harmony_score'], 4.4)

        repeated = matrix('亥子丑子')
        group = next(r for r in repeated['matrix'] if r['type'] == '방합(方合)')
        covered = [r for r in repeated['matrix'] if r['type'] == '육합(六合)']
        self.assertEqual(len(covered), 2)
        self.assertTrue(all(r['score_contribution'] == 0.0 and
                            r['score_covered_by'] == group['relation_id']
                            for r in covered))
        self.assertEqual(repeated['harmony_score'], 3.5)

        # 깨진 삼합의 점수 0은 남아 있는 반합 후보를 덮지 않는다.
        fallback = matrix('巳亥卯未')
        half = next(r for r in fallback['matrix'] if r['type'] == '반합(半合)')
        self.assertEqual(half['score_contribution'], half['score'])
        self.assertIsNone(half['score_covered_by'])
        self.assertEqual(fallback['harmony_score'], 1.1)

    def test_half_hap_includes_each_repeated_partner(self):
        result = matrix('寅午午酉')
        self.assertEqual(pairs(result, '반합(半合)'), {('year', 'month'), ('year', 'day')})
        self.assertEqual(result['harmony_score'], 2.2)
        for branches in sorted(set(permutations('寅午午酉'))):
            expected = {(PILLARS[i], PILLARS[j]) for i, j in combinations(range(4), 2)
                        if {branches[i], branches[j]} == {'寅', '午'}}
            self.assertEqual(pairs(matrix(branches), '반합(半合)'), expected)

    def test_pair_punishments_are_deduplicated_by_position_not_character(self):
        self.assertEqual(pairs(matrix('寅巳巳酉'), '형(刑)'), set())
        self.assertEqual(pairs(matrix('戌未未子'), '형(刑)'),
                         {('year', 'month'), ('year', 'day')})
        self.assertEqual(pairs(matrix('午午午子'), '형(刑)'),
                         {('year', 'month'), ('year', 'day'), ('month', 'day')})

    def test_group_participants_and_formations_preserve_duplicate_positions(self):
        for branches, kind, checker in [('亥卯未亥', '삼합(三合)', check_three_hap),
                                        ('寅卯辰寅', '방합(方合)', check_square_hap)]:
            with self.subTest(branches=branches):
                result = matrix(branches)
                groups = [r for r in result['matrix'] if r['type'] == kind]
                self.assertEqual(len(groups), 1)
                group = groups[0]
                self.assertEqual(group['participants'], PILLARS)
                self.assertEqual(group['formations'], [['year', 'month', 'day'], ['month', 'day', 'hour']])
                self.assertEqual(group['relation_scope'], 'group')
                self.assertEqual(group['from_pillar'], 'all')
                self.assertEqual(group['score'], 3.0 if kind == '삼합(三合)' else 3.5)
                for index in range(4):
                    details = checker(branches[index], index, list(branches), '甲')
                    if checker == check_three_hap:
                        details = details[0]
                    self.assertEqual(details[0]['participant_indices'], [0, 1, 2, 3])
                    self.assertEqual({r['index'] for r in details[0]['with_branches']}, set(range(4)) - {index})

    def test_nonparticipant_is_not_included_in_group(self):
        group = next(r for r in matrix('亥卯未子')['matrix'] if r['type'] == '삼합(三合)')
        self.assertEqual(group['participants'], ['year', 'month', 'day'])
        self.assertEqual(group['formations'], [['year', 'month', 'day']])

    def test_ids_are_unique_repeatable_and_survive_response_schema(self):
        result = matrix('亥卯未亥')
        self.assertEqual(result, matrix('亥卯未亥'))
        ids = [r['relation_id'] for r in result['matrix']]
        self.assertEqual(len(ids), len(set(ids)))
        encoded = InteractionsInfo.model_validate(result).model_dump()
        for raw, output in zip(result['matrix'], encoded['matrix']):
            self.assertEqual(output['relation_id'], raw['relation_id'])
            self.assertEqual(output['participants'], raw['participants'])
            self.assertEqual(output['formations'], raw['formations'])
            if raw['relation_scope'] == 'pairwise':
                self.assertEqual(raw['participants'], [raw['from_pillar'], raw['to_pillar']])
                self.assertEqual(raw['formations'], [])

    def test_six_hap_with_repeated_branch_has_no_spurious_punishment(self):
        result = matrix('巳申巳子')['matrix']
        self.assertEqual(pairs({'matrix': result}, '육합(六合)'),
                         {('year', 'month'), ('month', 'day')})
        self.assertEqual(pairs({'matrix': result}, '형(刑)'), set())


if __name__ == '__main__':
    unittest.main()
