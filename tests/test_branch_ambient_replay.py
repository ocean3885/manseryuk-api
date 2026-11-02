"""표시용 비율의 반올림 전에 주변 보정을 재생한다."""

import copy
import unittest

from services.branch_ambient_replay import (
    AMBIENT_CAP, cap_ambient_ratio, replay_ambient_power, replay_selected_ambient_power,
)
from services.branch_dynamics import PILLARS, _distance_weight, analyze_branch_dynamics
from services.branch_dynamics_v3_assembler import (
    assemble_branch_dynamics_v3_foundation, assemble_branch_pairs_v3,
    assemble_branch_groups_v3, assemble_branch_influence_paths_v3,
)
from services.interaction_matrix import build_interaction_matrix
from services.relation_rules import AMBIENT_RATES


def strengths(stem_text, branch_text):
    stems, branches = list(stem_text), list(branch_text)
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    foundation = assemble_branch_dynamics_v3_foundation(stems, branches, source)
    return foundation['branch_strengths']


def path_context(stem_text, branch_text):
    stems, branches = list(stem_text), list(branch_text)
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    foundation = assemble_branch_dynamics_v3_foundation(stems, branches, source)
    pairs = assemble_branch_pairs_v3(branches, source)
    groups = assemble_branch_groups_v3(branches, source, pairs)
    section = assemble_branch_influence_paths_v3(
        branches, foundation['branch_strengths'], pairs, groups)
    return source, section


def included_ids(section, target):
    return [path['path_id'] for path in section['influence_paths']
            if path['target']['pillar'] == target and
            path['stage'] == 'pre_relation_background' and
            path['accounting_decision'] == 'include']


class BranchAmbientReplayTests(unittest.TestCase):
    def test_full_and_empty_selection_preserve_existing_boundaries(self):
        for stems, branches in (
            ('乙己己庚', '巳丑未午'), ('庚己丙乙', '申丑申未'),
            ('乙己己庚', '亥丑未子'), ('甲甲甲甲', '子午辰寅'),
            ('甲甲甲甲', '子午午午'),
        ):
            with self.subTest(branches=branches):
                _, section = path_context(stems, branches)
                snapshot = copy.deepcopy(section)
                for target, strength in section['branch_strengths'].items():
                    selected = included_ids(section, target)
                    full = replay_selected_ambient_power(
                        section['branch_strengths'], section['influence_paths'],
                        target, selected)
                    reverse = replay_selected_ambient_power(
                        section['branch_strengths'], section['influence_paths'],
                        target, list(reversed(selected)))
                    self.assertEqual(full, reverse)
                    self.assertEqual(full['background_power'], strength['effective_power'])
                    self.assertEqual(full['background_power_delta'], 0)
                    empty = replay_selected_ambient_power(
                        section['branch_strengths'], section['influence_paths'], target, [])
                    self.assertEqual(empty['background_power'], strength['after_stem_power'])
                    self.assertTrue(empty['diagnostic_only'])
                self.assertEqual(section, snapshot)

    def test_a_selection_matches_existing_pair_and_group_exclusions(self):
        source, section = path_context('乙己己庚', '巳丑未午')
        all_ids = included_ids(section, 'day')
        without_si = [ref for ref in all_ids if ref != 'path:background:year:day:branch']
        result = replay_selected_ambient_power(
            section['branch_strengths'], section['influence_paths'], 'day', without_si)
        pair = next(pair for pair in source['pairwise'] if pair['pair_id'] == 'year:day')
        self.assertEqual(result['background_power'], pair['relations'][0]['power_before']['day'])
        self.assertEqual(result['background_power'], 1.7626)

        only_chou = ['path:background:month:day:branch']
        result = replay_selected_ambient_power(
            section['branch_strengths'], section['influence_paths'], 'day', only_chou)
        group = next(group for group in source['groups'] if group['type'] == '방합(方合)')
        self.assertEqual(result['background_power'],
                         group['formation_evidence'][0]['power_before']['day'])
        self.assertEqual(len(result['omitted_path_ids']), 2)

    def test_d_two_shen_sources_are_removed_individually(self):
        source, section = path_context('庚己丙乙', '申丑申未')
        all_ids = included_ids(section, 'month')
        for removed, pair_id in (
            ('path:background:year:month:branch', 'year:month'),
            ('path:background:day:month:branch', 'month:day'),
        ):
            with self.subTest(removed=removed):
                result = replay_selected_ambient_power(
                    section['branch_strengths'], section['influence_paths'], 'month',
                    [ref for ref in all_ids if ref != removed])
                pair = next(pair for pair in source['pairwise'] if pair['pair_id'] == pair_id)
                self.assertEqual(result['background_power'],
                                 pair['relations'][0]['power_before']['month'])
                self.assertGreater(result['background_power_delta'], 0)
                self.assertEqual(result['omitted_path_ids'], [removed])

    def test_selection_rejects_wrong_or_unavailable_paths_and_changed_mirror(self):
        _, section = path_context('乙己己庚', '巳丑未午')
        valid = 'path:background:year:day:branch'
        group_id = next(path['path_id'] for path in section['influence_paths']
                        if path['stage'] == 'structural_context')
        for target, selection in (
            ('day', [valid, valid]), ('day', ['path:missing']),
            ('day', [group_id]), ('month', [valid]),
            ('month', ['path:background:hour:month:branch']),
        ):
            with self.subTest(target=target, selection=selection):
                with self.assertRaises(ValueError):
                    replay_selected_ambient_power(
                        section['branch_strengths'], section['influence_paths'],
                        target, selection)
        changed = copy.deepcopy(section)
        path = next(path for path in changed['influence_paths'] if path['path_id'] == valid)
        path['quantity']['value'] += 0.000001
        with self.assertRaisesRegex(ValueError, '표시값'):
            replay_selected_ambient_power(
                changed['branch_strengths'], changed['influence_paths'], 'day', [valid])

    def test_a_d_and_contrasting_charts_replay_all_four_strengths(self):
        for stems, branches in (
            ('乙己己庚', '巳丑未午'),
            ('庚己丙乙', '申丑申未'),
            ('乙己己庚', '亥丑未子'),
            ('甲甲甲甲', '子午辰寅'),
            ('甲甲甲甲', '子午午午'),
        ):
            with self.subTest(stems=stems, branches=branches):
                source = strengths(stems, branches)
                snapshot = copy.deepcopy(source)
                result = replay_ambient_power(source)
                self.assertEqual(source, snapshot)
                self.assertEqual(set(result), set(source))
                for pillar in source:
                    self.assertEqual(result[pillar]['effective_power'],
                                     source[pillar]['effective_power'])
                    self.assertEqual(len(result[pillar]['contributions']), 3)
                    self.assertFalse(result[pillar]['cap_applied'])

    def test_a_preserves_unrounded_contribution_and_suppressed_zero(self):
        result = replay_ambient_power(strengths('乙己己庚', '巳丑未午'))
        day_from_year = next(row for row in result['day']['contributions']
                             if row['source_pillar'] == 'year')
        self.assertEqual(day_from_year['displayed_ratio'], 0.028735)
        self.assertNotEqual(day_from_year['raw_ratio'],
                            day_from_year['displayed_ratio'])
        month_from_hour = next(row for row in result['month']['contributions']
                               if row['source_pillar'] == 'hour')
        self.assertEqual(month_from_hour['accounting_path'],
                         'suppressed_by_active_structure')
        self.assertEqual(month_from_hour['raw_ratio'], 0)
        self.assertEqual(month_from_hour['displayed_ratio'], 0)

    def test_cap_is_after_raw_sum_and_before_power_rounding(self):
        self.assertEqual(cap_ambient_ratio(0.4), 0.35)
        self.assertEqual(cap_ambient_ratio(-0.4), -0.35)
        self.assertEqual(cap_ambient_ratio(0.12), 0.12)

        largest_distance_sum = max(
            sum(_distance_weight(source, target) for source in range(4)
                if source != target)
            for target in range(4)
        )
        self.assertEqual(len(PILLARS), 4)
        self.assertLess(max(abs(rate) for rate in AMBIENT_RATES.values()) *
                        largest_distance_sum, AMBIENT_CAP)

    def test_tampered_display_or_effective_power_is_rejected(self):
        source = strengths('庚己丙乙', '申丑申未')
        source['month']['strength_evidence']['surroundings'][0][
            'adjustment_ratio'] += 0.000001
        with self.assertRaisesRegex(ValueError, '표시용 주변 보정률'):
            replay_ambient_power(source)

        source = strengths('庚己丙乙', '申丑申未')
        source['month']['effective_power'] += 0.0001
        with self.assertRaisesRegex(ValueError, 'effective_power'):
            replay_ambient_power(source)


if __name__ == '__main__':
    unittest.main()
