"""Raw detector contracts and agreement with the central relation matrix."""
from copy import deepcopy
from itertools import product
import unittest

from services.analysis import analyze_palja_integrated
from services.branch_relations import get_relations_for_branch, check_square_hap
from services.character_relation_index import assemble_character_relation_index
from services.stem_relations import get_relations_for_stem
from tests.test_character_relation_index_assembler import inputs

PILLARS = ('year', 'month', 'day', 'hour')
PAIR_TYPES = {
    'six_haps': '육합(六合)', 'chungs': '충(沖)', 'cheons': '천(穿)',
    'breaks': '파(破)', 'punishments': '형(刑)', 'half_haps': '반합(半合)',
    'gong_haps': '공합(拱合)', 'hidden_stem_haps': '암합(暗合)',
}
GROUP_TYPES = {'three_haps': '삼합(三合)', 'square_haps': '방합(方合)',
               'three_punishments': '삼형(三刑)'}


class RawRelationTests(unittest.TestCase):
    def test_empty_buckets_and_control_directions_have_stable_shapes(self):
        stem = get_relations_for_stem('甲', 0, list('子子子子'), list('甲甲甲甲'))
        self.assertEqual(stem, {'combinations': [], 'conflict': [],
                                'restrain': {'restrain_to': [], 'restrain_me': []}})
        branch = get_relations_for_branch('子', 0, list('子子子子'), list('甲甲甲甲'))
        self.assertNotIn('six_haps_all', branch)
        self.assertTrue(all(value == [] for value in branch.values()))

    def assert_state_matches(self, raw, central):
        for field in ('activation_status', 'status_reasons', 'candidate_element',
                      'activation_rule_id'):
            self.assertEqual(raw.get(field), central.get(field), (field, raw, central))
        self.assertEqual(raw['impact_status'], 'not_evaluated')
        self.assertNotIn('strength', raw)
        self.assertNotIn('element', raw)
        self.assertNotIn('combined_element', raw)

    def test_all_branch_pairs_at_near_and_far_positions_match_matrix(self):
        for left, right in product('子丑寅卯辰巳午未申酉戌亥', repeat=2):
            for other_index in (1, 2, 3):
                branches = list('子子子子')
                branches[0], branches[other_index] = left, right
                source = inputs('甲甲甲甲', branches)
                matrix = source[2]['matrix']
                raw = source[3]['pillars']['year']['branch']['relations']
                with self.subTest(branches=branches, other_index=other_index):
                    for bucket, kind in PAIR_TYPES.items():
                        raw_items = [r for r in raw[bucket] if r['with_index'] == other_index]
                        central = [r for r in matrix if r['type'] == kind
                                   and r['participants'] == ['year', PILLARS[other_index]]]
                        self.assertEqual(len(raw_items), len(central))
                        for item, counterpart in zip(raw_items, central):
                            self.assert_state_matches(item, counterpart)

    def test_all_stem_pairs_match_matrix_and_control_direction(self):
        for left, right in product('甲乙丙丁戊己庚辛壬癸', repeat=2):
            source = inputs(left + '甲甲' + right, '子子子子')
            raw = source[3]['pillars']['year']['stem']['relations']
            with self.subTest(stems=source[0]):
                for bucket, kind in [('combinations', '천간합(天干合)'),
                                     ('conflict', '천간충(天干沖)')]:
                    raw_items = [r for r in raw[bucket] if r['with_index'] == 3]
                    central = [r for r in source[2]['matrix'] if r['type'] == kind
                               and r['participants'] == ['year', 'hour']]
                    self.assertEqual(len(raw_items), len(central))
                    for item, counterpart in zip(raw_items, central):
                        self.assert_state_matches(item, counterpart)
                for bucket in ('restrain_to', 'restrain_me'):
                    for item in raw['restrain'][bucket]:
                        other = source[3]['pillars'][PILLARS[item['with_index']]]['stem']['relations']['restrain']
                        reverse = 'restrain_me' if bucket == 'restrain_to' else 'restrain_to'
                        match = next(r for r in other[reverse] if r['with_index'] == 0)
                        self.assertEqual(item['potential_index'], match['potential_index'])
                        self.assertEqual(item['potential_index'], round(
                            item['distance_weight'] * item['base_coefficient'], 4))
                        self.assertEqual(item['activation_status'], 'detected')
                        self.assertEqual(item['impact_status'], 'not_evaluated')
                        self.assertNotIn('strength', item)

    def test_group_conditions_and_formations_match_matrix(self):
        for branches in ('亥卯未亥', '亥卯卯未', '巳亥卯未', '酉亥卯未',
                         '亥卯未丑', '寅卯辰寅', '寅子卯辰', '寅巳申寅', '丑戌未子'):
            source = inputs('甲甲甲甲', branches)
            for index, pillar in enumerate(PILLARS):
                raw = source[3]['pillars'][pillar]['branch']['relations']
                for bucket, kind in GROUP_TYPES.items():
                    for item in raw[bucket]:
                        central = next(r for r in source[2]['matrix'] if r['type'] == kind
                                       and pillar in r['participants'])
                        self.assert_state_matches(item, central)
                        self.assertEqual(item['is_adjacent'], central['is_adjacent'])
                        self.assertEqual(item['formation_indices'],
                                         [[PILLARS.index(p) for p in formation]
                                          for formation in central['formations']])

    def test_square_adjacency_uses_real_formations_with_repeated_glyphs(self):
        for branches, spans, adjacent, potential in (
            ('寅卯辰寅', [2, 2], True, 1.5),
            ('寅子卯辰', [3], False, 0.9),
        ):
            item = check_square_hap('寅', 0, list(branches), '甲')[0]
            self.assertEqual(item['formation_distances'], spans)
            self.assertEqual(item['distance'], min(spans))
            self.assertEqual(item['is_adjacent'], adjacent)
            self.assertEqual(item['potential_index'], potential)

    def test_nonzero_diagnostics_do_not_claim_activation_or_impact(self):
        raw = analyze_palja_integrated(list('甲甲甲甲'), list('辰子辰寅'))
        item = raw['pillars']['year']['branch']['relations']['punishments'][0]
        self.assertEqual(item['potential_index'], 0.49)
        self.assertEqual(item['activation_status'], 'candidate_only')
        self.assertEqual(item['status_reasons'], ['nonadjacent_self_punishment_candidate'])
        self.assertEqual(item['impact_status'], 'not_evaluated')
        raw = analyze_palja_integrated(list('甲甲甲甲'), list('午子丑寅'))
        item = raw['pillars']['month']['branch']['relations']['six_haps'][0]
        self.assertEqual(item['activation_status'], 'conditional')
        self.assertEqual(item['candidate_element'], '土')
        self.assertEqual(item['distance_weight'], 1.0)
        self.assertEqual(item['impact_status'], 'not_evaluated')

    def test_assembler_rejects_changed_raw_status_reason_or_candidate(self):
        for kind, bucket, field, value in (
            ('branch', 'six_haps', 'activation_status', 'active'),
            ('branch', 'six_haps', 'status_reasons', []),
            ('branch', 'six_haps', 'candidate_element', '金'),
            ('stem', 'combinations', 'activation_status', 'active'),
            ('stem', 'combinations', 'candidate_element', '金'),
        ):
            source = inputs('甲己甲己', '午子丑寅')
            changed = deepcopy(source)
            pillar = 'month' if kind == 'branch' else 'year'
            changed[3]['pillars'][pillar][kind]['relations'][bucket][0][field] = value
            with self.subTest(kind=kind, field=field), self.assertRaises(ValueError):
                assemble_character_relation_index(*changed)


if __name__ == '__main__':
    unittest.main()
