from copy import deepcopy
from itertools import product
import unittest

from services.cycle_relations import detect_cycle_relations
from services import relation_rules as rules


def node(context, char, kind='branch'):
    return dict(context_id=context, char=char, kind=kind)


class CycleRelationTests(unittest.TestCase):
    def test_all_stem_pairs_keep_registered_candidates_and_direction(self):
        left, right = 'daewoon.period_0.cycle.stem', 'sewoon.year_2026.cycle.stem'
        for a, b in product('甲乙丙丁戊己庚辛壬癸', repeat=2):
            rows = list(detect_cycle_relations({left: node('daewoon.period_0', a, 'stem'),
                                               right: node('sewoon.year_2026', b, 'stem')}).values())
            with self.subTest(a=a, b=b):
                kinds = {r['type'] for r in rows}
                self.assertEqual('combine' in kinds, any(set(p) == {a, b} for p in rules.STEM_COMBINATIONS))
                self.assertEqual('clash' in kinds, any(set(p) == {a, b} for p in rules.STEM_CONFLICTS))
                controls = [r for r in rows if r['type'] == 'control']
                self.assertEqual(len(controls), int((a, b) in rules.STEM_RESTRAIN) + int((b, a) in rules.STEM_RESTRAIN))
                for row in controls:
                    expected = left if (a, b) in rules.STEM_RESTRAIN else right
                    self.assertEqual(row['direction']['from_character'], expected)

    def test_all_branch_pairs_against_registered_structural_tables(self):
        left, right = 'natal.chart.year.branch', 'daewoon.period_0.cycle.branch'
        for a, b in product('子丑寅卯辰巳午未申酉戌亥', repeat=2):
            rows = list(detect_cycle_relations({left: node('natal.chart', a),
                                               right: node('daewoon.period_0', b)}).values())
            kinds = {r['type'] for r in rows}
            with self.subTest(a=a, b=b):
                for kind, table in [('combine', rules.SIX_HAPS), ('clash', rules.CHUNGS),
                                    ('pierce', rules.CHEONS), ('break', rules.BREAKS),
                                    ('half_combine', rules.HALF_HAPS), ('arch_combine', rules.GONG_HAPS),
                                    ('hidden_combine', rules.HIDDEN_STEM_HAPS)]:
                    self.assertEqual(kind in kinds, any(set(p) == {a, b} for p in table))
                for row in rows:
                    self.assertNotIn(row['activation_status'], ('active', 'suppressed'))
                    self.assertNotIn('applied_power_delta', row)

    def test_groups_span_three_scopes_and_repeated_positions_stay_separate(self):
        for table, kind in [(rules.THREE_HAPS, 'trine'), (rules.SQUARE_HAPS, 'square'),
                            (rules.THREE_PUNISHMENTS, 'triple_punishment')]:
            for letters in table:
                nodes = {
                    'natal.chart.year.branch': node('natal.chart', letters[0]),
                    'natal.chart.hour.branch': node('natal.chart', letters[0]),
                    'daewoon.period_0.cycle.branch': node('daewoon.period_0', letters[1]),
                    'sewoon.year_2026.cycle.branch': node('sewoon.year_2026', letters[2]),
                }
                original = deepcopy(nodes)
                rows = detect_cycle_relations(nodes)
                groups = [r for r in rows.values() if r['type'] == kind]
                self.assertEqual(len(groups), 2)
                self.assertTrue(all(len(r['context_ids']) == 3 for r in groups))
                self.assertTrue(all(r['activation_status'] == 'candidate_only' for r in groups))
                self.assertTrue(all(r['formation_candidates'] == [r['participants']] for r in groups))
                self.assertEqual(rows, detect_cycle_relations(dict(reversed(list(nodes.items())))))
                self.assertEqual(nodes, original)

    def test_transmission_is_exact_match_and_cross_context_only(self):
        nodes = {
            'natal.chart.year.branch': node('natal.chart', '寅'),
            'natal.chart.year.stem': node('natal.chart', '甲', 'stem'),
            'daewoon.period_0.cycle.stem': node('daewoon.period_0', '甲', 'stem'),
            'sewoon.year_2026.cycle.stem': node('sewoon.year_2026', '乙', 'stem'),
        }
        rows = list(detect_cycle_relations(nodes).values())
        transmitted = [r for r in rows if r['type'] == 'transmission']
        self.assertEqual(len(transmitted), 1)
        self.assertEqual(transmitted[0]['hidden_stem'], '甲')
        self.assertEqual(transmitted[0]['direction']['to_character'], 'daewoon.period_0.cycle.stem')
        self.assertTrue(all(len(r['context_ids']) > 1 for r in rows))
