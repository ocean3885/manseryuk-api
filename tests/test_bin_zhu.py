"""빈주 조회는 실제 연결·십성·다자 구성을 보존하고 점수로 해석하지 않는다."""
from copy import deepcopy
import unittest

from schemas.saju_analysis import BinZhuDynamics
from services.bin_zhu import analyze_bin_zhu_dynamics
from services.interaction_matrix import build_interaction_matrix

STEMS = list('甲丙戊庚')


def analyze(matrix, branches=None):
    return analyze_bin_zhu_dynamics(STEMS, branches or list('子午卯酉'), '戊', matrix)


def relation(kind, **kwargs):
    return dict(category='지지', type=kind, from_pillar='year', to_pillar='day', **kwargs)


class BinZhuTests(unittest.TestCase):
    def test_group_structure_and_formations_survive_schema(self):
        branches = list('亥卯未亥')
        matrix = build_interaction_matrix(STEMS, branches, '戊')['matrix']
        group = next(r for r in matrix if r['type'] == '삼합(三合)')
        result = analyze([group], branches)
        connection = result['group_connections'][0]
        self.assertEqual(connection['relation_id'], group['relation_id'])
        self.assertEqual(connection['guest_participants'], ['year', 'month'])
        self.assertEqual(connection['host_participants'], ['day', 'hour'])
        self.assertEqual(connection['formations'], group['formations'])
        self.assertEqual(connection['activation_status'], 'detected')
        self.assertEqual(BinZhuDynamics.model_validate(result).model_dump(), result)

    def test_all_cross_domain_types_keep_original_status_without_dominance(self):
        for kind, status in [('육합(六合)', 'detected'), ('충(沖)', 'active'),
                             ('형(刑)', 'active'), ('파(破)', 'active'),
                             ('공합(拱合)', 'candidate_only'), ('암합(暗合)', 'candidate_only')]:
            with self.subTest(kind=kind):
                result = analyze([relation(kind, activation_status=status)])
                self.assertEqual(result['rule_version'], '4.0.0')
                self.assertEqual(result['interaction_scope'], 'cross_domain_relations')
                self.assertEqual(result['excluded_interactions'], [])
                link = result['guest_host_links'][0]
                self.assertEqual(link['type'], kind)
                self.assertEqual(link['activation_status'], status)
                self.assertEqual(link['participants'], ['year', 'day'])
                self.assertEqual(link['distance'], 2)
                self.assertFalse(link['is_adjacent'])
                self.assertNotIn('control_flow', result)
                self.assertNotIn('mechanism', link)
                self.assertNotIn('flow_direction', link)
                BinZhuDynamics.model_validate(result)

    def test_combine_and_conflict_coexist_without_overall_verdict(self):
        result = analyze([relation('육합(六合)'), relation('천간충(天干沖)')])
        self.assertEqual(len(result['guest_host_links']), 2)
        for key in ('pairwise_scores', 'group_cohesion_score', 'control_flow', 'ai_prompt_bullets'):
            self.assertNotIn(key, result)

    def test_missing_group_participants_are_reported_without_inference(self):
        groups = [dict(category='지지', type=kind, from_pillar='all', to_pillar='all')
                  for kind in ('삼합(三合)', '방합(方合)')]
        result = analyze(groups)
        self.assertEqual(result['group_connections'], [])
        self.assertEqual(result['guest_host_links'], [])
        self.assertEqual([e['reason_code'] for e in result['excluded_interactions']],
                         ['missing_group_participants'] * 2)
        BinZhuDynamics.model_validate(result)

    def test_invalid_endpoints_and_category_are_reported(self):
        result = analyze([dict(category='지지', type='충(沖)', from_pillar='unknown'),
                          dict(category='지지', type='형(刑)', from_pillar='year', to_pillar='all'),
                          dict(category='unknown', type='충(沖)', from_pillar='year', to_pillar='day')])
        self.assertEqual([x['reason_code'] for x in result['excluded_interactions']],
                         ['invalid_endpoint', 'missing_group_participants', 'invalid_category'])
        BinZhuDynamics.model_validate(result)

    def test_real_groups_preserve_links_and_do_not_mutate_input(self):
        for branches, kind in [('亥卯未亥', '삼합(三合)'), ('寅卯辰寅', '방합(方合)'),
                               ('寅巳申申', '삼형(三刑)')]:
            with self.subTest(branches=branches):
                matrix = build_interaction_matrix(STEMS, list(branches), '戊')['matrix']
                before = deepcopy(matrix)
                pairs = [r for r in matrix if r['relation_scope'] == 'pairwise']
                actual = analyze(matrix, list(branches))
                self.assertEqual(actual['guest_host_links'], analyze(pairs, list(branches))['guest_host_links'])
                self.assertTrue(any(r['type'] == kind for r in actual['group_connections']))
                self.assertEqual(matrix, before)

    def test_repeated_group_is_exposed_once_with_distinct_formations(self):
        matrix = build_interaction_matrix(STEMS, list('亥卯未亥'), '戊')['matrix']
        group = next(r for r in matrix if r['type'] == '삼합(三合)')
        result = analyze([group, group])
        self.assertEqual(len(result['group_connections']), 1)
        self.assertEqual(len(result['group_connections'][0]['formations']), 2)

    def test_zi_mao_break_pairs_keep_all_four_positions(self):
        stems, branches = list('甲甲甲甲'), list('子子卯卯')
        matrix = build_interaction_matrix(stems, branches, '甲')['matrix']
        result = analyze_bin_zhu_dynamics(stems, branches, '甲', matrix)
        self.assertEqual({tuple(link['participants']) for link in result['guest_host_links']},
                         {('year', 'day'), ('year', 'hour'), ('month', 'day'), ('month', 'hour')})
        self.assertTrue(all(link['type'] == '파(破)' for link in result['guest_host_links']))
        self.assertEqual(result['excluded_interactions'], [])

    def test_reverse_endpoints_keep_actual_characters_and_ten_stars(self):
        item = dict(category='천간', type='천간합(天干合)', from_pillar='day', to_pillar='year')
        stems = list('癸丙戊庚')
        result = analyze_bin_zhu_dynamics(stems, list('子午卯酉'), '戊', [item])
        link = result['guest_host_links'][0]
        self.assertEqual(link['guest'], dict(pillar='year', char='癸', ten_god='정재', display_name='년간 癸(정재)'))
        self.assertEqual(link['host'], dict(pillar='day', char='戊', ten_god='일간', display_name='일간 戊(일간)'))
        self.assertNotIn('취용', link['detail'])

    def test_legacy_scores_have_no_effect_and_intradomain_pairs_are_not_links(self):
        pair = relation('육합(六合)')
        noisy = dict(pair, score=999, score_contribution=-999, weight=999)
        intradomain = dict(category='지지', type='충(沖)', from_pillar='year', to_pillar='month')
        self.assertEqual(analyze([pair]), analyze([noisy, intradomain]))


if __name__ == '__main__':
    unittest.main()
