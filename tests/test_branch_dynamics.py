"""지지 세력, 동주 천간, 관계별 방향의 회귀 검증."""

import unittest

from schemas.saju_analysis import BranchDynamics
from services.branch_dynamics import analyze_branch_dynamics
from services.interaction_matrix import build_interaction_matrix
from services.constants import JIJANGGAN_DETAILED


def analyze(stems, branches):
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    return analyze_branch_dynamics(stems, branches, matrix)


def pair(result, first, second):
    return next(p for p in result['pairwise'] if p['pair_id'] == f'{first}:{second}')


class BranchDynamicsTests(unittest.TestCase):
    def test_all_twelve_branches_have_complete_hidden_stem_ratios(self):
        for branch, hidden in JIJANGGAN_DETAILED.items():
            with self.subTest(branch=branch):
                self.assertEqual(sum(int(h['ratio'].split('/')[0]) for h in hidden), 30)
                result = analyze(list('甲乙丙丁'), [branch, '卯', '午', '酉'])
                self.assertGreater(result['branch_strengths']['year']['effective_power'], 0)
                self.assertEqual(len(result['pairwise']), 6)

    def test_month_stem_changes_month_branch_power_and_is_explained(self):
        branches = list('子卯午寅')
        powers = {}
        for stem, relation, effect in [
            ('癸', 'stem_generates_branch', 'support'),
            ('辛', 'stem_controls_branch', 'pressure'),
            ('丁', 'branch_generates_stem', 'outflow'),
        ]:
            result = analyze(['甲', stem, '甲', '甲'], branches)
            month = result['branch_strengths']['month']
            self.assertEqual(month['stem_branch_relation']['relation'], relation)
            self.assertEqual(month['stem_branch_relation']['branch_effect'], effect)
            self.assertEqual(month['base_power'], 2.4)
            self.assertEqual(len(month['stem_branch_relation']['evidence']), 2)
            powers[stem] = month['after_stem_power']
        self.assertGreater(powers['癸'], powers['丁'])
        self.assertGreater(powers['丁'], powers['辛'])

    def test_other_pillars_affect_pair_power_without_self_feedback(self):
        branches = list('子寅午辰')
        supported = analyze(['甲', '癸', '甲', '甲'], branches)
        pressured = analyze(['甲', '辛', '甲', '甲'], branches)
        first = pair(supported, 'year', 'day')
        second = pair(pressured, 'year', 'day')
        self.assertEqual(first['pillars'], ['year', 'day'])
        self.assertNotEqual(first['relations'][0]['power_before'],
                            second['relations'][0]['power_before'])
        self.assertTrue(first['context_evidence']['year'])
        self.assertFalse(any(e['source_pillar'] == 'day'
                             for e in first['context_evidence']['year']))

    def test_strength_and_relation_force_leads_are_distinct(self):
        result = analyze(list('甲甲甲甲'), list('子寅午辰'))
        self.assertEqual(result['rule_version'], '2.11.0')
        generation = next(r for r in pair(result, 'year', 'month')['relations']
                          if r['type'] == '생')
        self.assertEqual(generation['dominance'], 'month')
        self.assertEqual(generation['force_dominance'], 'year')
        self.assertEqual(generation['roles'],
                         {'year': 'supports', 'month': 'receives_support'})
        self.assertGreater(generation['force']['year_to_month'], 0)
        self.assertEqual(generation['force']['month_to_year'], 0)

        suppressed = analyze(list('甲辛甲甲'), list('子卯午寅'))
        generation = next(r for r in pair(suppressed, 'year', 'month')['relations']
                          if r['type'] == '생')
        self.assertEqual(generation['dominance'], 'month')
        self.assertEqual(generation['force_dominance'], 'undetermined')
        self.assertEqual(generation['roles'],
                         {'year': 'inactive', 'month': 'inactive'})

    def test_month_stem_changes_clash_capacity_without_changing_relation(self):
        branches = list('子午辰寅')
        supported = analyze(list('甲甲甲甲'), branches)
        pressured = analyze(list('甲壬甲甲'), branches)
        supported_clash = next(r for r in pair(supported, 'year', 'month')['relations']
                               if r['type'] == '충(沖)')
        pressured_clash = next(r for r in pair(pressured, 'year', 'month')['relations']
                               if r['type'] == '충(沖)')
        self.assertEqual(supported_clash['relation_id'], pressured_clash['relation_id'])
        self.assertEqual(supported_clash['force']['year_to_month'],
                         pressured_clash['force']['year_to_month'])
        self.assertGreater(supported['branch_strengths']['month']['after_stem_power'],
                           pressured['branch_strengths']['month']['after_stem_power'])
        self.assertGreater(supported_clash['force']['month_to_year'],
                           pressured_clash['force']['month_to_year'])
        self.assertEqual(supported_clash['roles'],
                         {'year': 'receives_more_pressure',
                          'month': 'delivers_more_pressure'})

    def test_other_branch_changes_same_pair_context_without_changing_type(self):
        chen = analyze(list('甲甲甲甲'), list('子寅午辰'))
        shen = analyze(list('甲甲甲甲'), list('子寅午申'))
        chen_clash = next(r for r in pair(chen, 'year', 'day')['relations']
                          if r['type'] == '충(沖)')
        shen_clash = next(r for r in pair(shen, 'year', 'day')['relations']
                          if r['type'] == '충(沖)')
        self.assertEqual(chen_clash['relation_id'], shen_clash['relation_id'])
        self.assertNotEqual(chen_clash['power_before'], shen_clash['power_before'])
        self.assertGreater(shen_clash['force']['year_to_day'],
                           chen_clash['force']['year_to_day'])
        self.assertGreater(shen_clash['force']['day_to_year'],
                           chen_clash['force']['day_to_year'])

    def test_chung_and_element_control_keep_distinct_directions(self):
        for guest, host, direction in [('子', '午', 'year_to_day'),
                                       ('午', '子', 'day_to_year')]:
            with self.subTest(guest=guest):
                result = analyze(list('甲甲甲甲'), [guest, '辰', host, '寅'])
                relations = pair(result, 'year', 'day')['relations']
                self.assertEqual({r['type'] for r in relations}, {'충(沖)', '극'})
                self.assertTrue(all(r['element_direction'] == direction for r in relations))
                control = next(r for r in relations if r['type'] == '극')
                opposite = ('day_to_year' if direction == 'year_to_day'
                            else 'year_to_day')
                self.assertEqual(control['force'][opposite], 0.0)
                self.assertGreater(control['force'][direction], 0.0)
                source = direction.split('_to_')[0]
                target = direction.split('_to_')[1]
                self.assertEqual(control['roles'][source], 'controls')
                self.assertEqual(control['roles'][target], 'receives_control')

    def test_project_break_pairs_include_mao_wu_and_wu_you(self):
        for branches, first, second in [
            (list('午子酉寅'), 'year', 'day'),
            (list('子卯午寅'), 'month', 'day'),
        ]:
            with self.subTest(branches=branches, pair=(first, second)):
                result = analyze(list('甲甲甲甲'), branches)
                types = {r['type'] for r in pair(result, first, second)['relations']}
                self.assertIn('파(破)', types)

        result = analyze(list('甲甲甲甲'), list('子酉辰寅'))
        self.assertNotIn('파(破)',
                         {r['type'] for r in pair(result, 'year', 'month')['relations']})
        result = analyze(list('甲甲甲甲'), list('子卯辰寅'))
        self.assertNotIn('파(破)',
                         {r['type'] for r in pair(result, 'year', 'month')['relations']})

    def test_break_suppresses_generation_in_pair_and_ambient_power(self):
        for branches, first, second, structural_type, reason in [
            (list('子卯辰寅'), 'year', 'month', '형(刑)', 'punishment_blocks_generation'),
            (list('子卯午寅'), 'month', 'day', '파(破)', 'break_blocks_generation'),
        ]:
            with self.subTest(branches=branches):
                result = analyze(list('甲甲甲甲'), branches)
                relations = pair(result, first, second)['relations']
                self.assertIn(structural_type, {r['type'] for r in relations})
                self.assertNotIn('파(破)' if structural_type == '형(刑)' else '형(刑)',
                                 {r['type'] for r in relations})
                generation = next(r for r in relations if r['type'] == '생')
                self.assertEqual(generation['activation_status'], 'suppressed')
                self.assertEqual(set(generation['force'].values()), {0.0})
                self.assertEqual(generation['status_reason'], reason)
                for pillar in (first, second):
                    other = second if pillar == first else first
                    evidence = next(e for e in result['branch_strengths'][pillar]['ambient_evidence']
                                    if e['source_pillar'] == other)
                    self.assertEqual(evidence['adjustment_ratio'], 0.0)
                    self.assertEqual(evidence['status_reason'], reason)
                    generation_id = generation['relation_id']
                    self.assertEqual(evidence['element_relation_id'], generation_id)

    def test_conditional_combination_does_not_suppress_separate_generation(self):
        result = analyze(list('甲甲甲甲'), list('申寅亥子'))
        pair_result = pair(result, 'month', 'day')
        combination = next(r for r in pair_result['relations']
                           if r['type'] == '육합(六合)')
        generation = next(r for r in pair_result['relations'] if r['type'] == '생')
        self.assertEqual(combination['activation_status'], 'conditional')
        self.assertEqual(set(combination['force'].values()), {0.0})
        self.assertEqual(generation['activation_status'], 'potential')
        evidence = next(e for e in result['branch_strengths']['month']['ambient_evidence']
                        if e['source_pillar'] == 'day')
        self.assertGreater(evidence['adjustment_ratio'], 0)
        self.assertEqual(evidence['element_relation_id'], generation['relation_id'])
        self.assertIn({'relation_id': combination['relation_id'],
                       'type': '육합(六合)', 'activation_status': 'conditional'},
                      evidence['related_relations'])
        self.assertEqual(evidence['activation_status'], 'potential')

    def test_wu_you_break_and_control_have_distinct_directions(self):
        for branches, control_direction in [
            (list('午辰酉寅'), 'year_to_day'),
            (list('酉辰午寅'), 'day_to_year'),
        ]:
            with self.subTest(branches=branches):
                relations = pair(analyze(list('甲甲甲甲'), branches),
                                 'year', 'day')['relations']
                by_type = {r['type']: r for r in relations}
                self.assertEqual(set(by_type), {'파(破)', '극'})
                self.assertTrue(all(v > 0 for v in by_type['파(破)']['force'].values()))
                self.assertGreater(by_type['극']['force'][control_direction], 0)
                opposite = ('day_to_year' if control_direction == 'year_to_day'
                            else 'year_to_day')
                self.assertEqual(by_type['극']['force'][opposite], 0.0)

    def test_chen_you_combination_exposes_asymmetric_mechanisms(self):
        result = analyze(list('甲甲甲甲'), list('辰子酉寅'))
        pair_result = pair(result, 'year', 'day')
        self.assertEqual(pair_result['primary_relation'], '육합(六合)')
        combination = next(r for r in pair_result['relations']
                           if r['type'] == '육합(六合)')
        self.assertEqual(combination['activation_status'], 'potential')
        self.assertEqual(combination['status_reason'],
                         'combination_candidate_not_transformation')
        self.assertEqual(combination['directional_mechanisms']['year'],
                         'binds_and_outflows')
        self.assertEqual(combination['directional_mechanisms']['day'],
                         'binds_and_receives_support')
        self.assertEqual(combination['roles'],
                         {'year': 'drawn_more', 'day': 'leads_attraction'})

    def test_group_is_separate_from_pairwise_events(self):
        result = analyze(list('甲丙戊庚'), list('亥卯未亥'))
        group = next(g for g in result['groups'] if g['type'] == '삼합(三合)')
        self.assertEqual(group['participants'], ['year', 'month', 'day', 'hour'])
        self.assertEqual(group['status'], 'not_scored')
        self.assertEqual(len(result['pairwise']), 6)
        self.assertTrue(all(r['type'] != '삼합(三合)'
                            for p in result['pairwise'] for r in p['relations']))

    def test_group_formations_expose_each_participant_capacity_without_peer_feedback(self):
        result = BranchDynamics.model_validate(
            analyze(list('甲甲甲甲'), list('巳午未寅'))).model_dump()
        group = next(g for g in result['groups'] if g['type'] == '방합(方合)')
        self.assertEqual(group['status'], 'not_scored')
        self.assertEqual(group['activation_status'], 'potential')
        self.assertNotIn('force', group)
        self.assertEqual(group['action_rule_id'], 'group:방합:巳午未')
        self.assertEqual(group['direction_status'], 'undetermined')
        self.assertEqual(len(group['formation_evidence']), 1)
        formation = group['formation_evidence'][0]
        self.assertEqual(formation['pillars'], ['year', 'month', 'day'])
        self.assertEqual(formation['structural_roles'], {
            'year': 'season_start', 'month': 'season_center', 'day': 'season_end',
        })
        self.assertAlmostEqual(sum(formation['capacity_share'].values()), 1.0,
                               places=3)
        self.assertGreater(formation['power_before']['month'],
                           formation['power_before']['year'])
        for pillar, evidence in formation['context_evidence'].items():
            self.assertEqual([item['source_pillar'] for item in evidence], ['hour'])
            self.assertIn(pillar, formation['power_before'])
        six_hap = next(r for r in pair(result, 'month', 'day')['relations']
                       if r['type'] == '육합(六合)')
        self.assertGreater(six_hap['force']['month_to_day'], 0)
        self.assertGreater(six_hap['force']['day_to_month'], 0)
        self.assertEqual(formation['overlapping_pairs'], [{
            'relation_id': six_hap['relation_id'],
            'covered_in_harmony_score': True,
        }])
        self.assertEqual(formation['directional_candidates'], [])
        self.assertEqual(group['pair_overlap_policy'],
                         'preserve_pair_do_not_sum_group_force')

    def test_repeated_group_formations_keep_position_specific_shares(self):
        result = analyze(list('甲甲甲甲'), list('亥子丑子'))
        group = next(g for g in result['groups'] if g['type'] == '방합(方合)')
        formations = group['formation_evidence']
        self.assertEqual([f['pillars'] for f in formations],
                         [['year', 'month', 'day'], ['year', 'day', 'hour']])
        self.assertNotEqual(formations[0]['power_before']['year'],
                            formations[1]['power_before']['year'])
        self.assertEqual([len(f['overlapping_pairs']) for f in formations], [1, 1])
        self.assertNotEqual(formations[0]['overlapping_pairs'][0]['relation_id'],
                            formations[1]['overlapping_pairs'][0]['relation_id'])

    def test_suppressed_group_preserves_uncovered_fallback_half_hap(self):
        result = analyze(list('甲甲甲甲'), list('巳亥卯未'))
        group = next(g for g in result['groups'] if g['type'] == '삼합(三合)')
        self.assertEqual(group['activation_status'], 'suppressed')
        self.assertEqual(group['status'], 'not_scored')
        self.assertNotIn('force', group)
        formation = group['formation_evidence'][0]
        self.assertEqual(formation['structural_roles'], {
            'month': 'birth', 'day': 'center', 'hour': 'storage',
        })
        half = next(r for r in pair(result, 'day', 'hour')['relations']
                    if r['type'] == '반합(半合)')
        self.assertGreater(half['force']['day_to_hour'], 0)
        self.assertEqual(formation['overlapping_pairs'], [{
            'relation_id': half['relation_id'],
            'covered_in_harmony_score': False,
        }])
        self.assertEqual(group['direction_status'], 'suppressed')
        self.assertTrue(all(candidate['activation_status'] == 'suppressed'
                            for candidate in formation['directional_candidates']))

    def test_three_hap_direction_candidates_follow_center_position(self):
        result = BranchDynamics.model_validate(
            analyze(list('甲甲甲甲'), list('亥卯未亥'))).model_dump()
        group = next(g for g in result['groups'] if g['type'] == '삼합(三合)')
        self.assertEqual(group['action_rule_id'], 'group:삼합:亥卯未')
        self.assertEqual(group['direction_status'], 'candidate_only')
        self.assertEqual(group['activation_status'], 'potential')
        self.assertEqual(group['status'], 'not_scored')
        self.assertNotIn('force', group)
        first, second = group['formation_evidence']
        self.assertEqual([f['pillars'] for f in (first, second)],
                         [['year', 'month', 'day'], ['month', 'day', 'hour']])
        self.assertEqual(len(result['pairwise']), 6)
        self.assertFalse(any(r['type'] == '반합(半合)'
                             for p in result['pairwise'] for r in p['relations']))
        self.assertTrue(all(not formation['overlapping_pairs']
                            for formation in (first, second)))
        self.assertEqual({(c['from_pillar'], c['to_pillar'])
                          for c in first['directional_candidates']},
                         {('year', 'month'), ('day', 'month')})
        self.assertEqual({(c['from_pillar'], c['to_pillar'])
                          for c in second['directional_candidates']},
                         {('hour', 'month'), ('day', 'month')})
        self.assertTrue(all(c['activation_status'] == 'candidate_only'
                            for formation in (first, second)
                            for c in formation['directional_candidates']))
        self.assertEqual(first['role_effect_candidates'][0]['effect'],
                         'transformation_candidate')

        fire = analyze(list('甲甲甲甲'), list('寅午戌子'))
        group = next(g for g in fire['groups'] if g['type'] == '삼합(三合)')
        self.assertEqual(group['formation_evidence'][0]['role_effect_candidates'], [{
            'pillar': 'day', 'effect': 'center_generates_storage_candidate',
            'activation_status': 'candidate_only',
        }])


if __name__ == '__main__':
    unittest.main()
