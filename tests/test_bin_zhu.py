"""빈주 다자 관계 제외와 쌍별 계산의 회귀 검증."""
import unittest

from schemas.saju_analysis import BinZhuDynamics
from services.bin_zhu import analyze_bin_zhu_dynamics
from services.interaction_matrix import build_interaction_matrix

STEMS = list('甲丙戊庚')


def analyze(matrix, branches=None):
    return analyze_bin_zhu_dynamics(STEMS, branches or list('子午卯酉'), '戊', matrix)


class BinZhuTests(unittest.TestCase):
    def test_group_structure_is_exposed_without_score_or_acquisition(self):
        matrix = build_interaction_matrix(STEMS, list('亥卯未亥'), '戊')['matrix']
        group = next(r for r in matrix if r['type'] == '삼합(三合)')
        result = analyze([group])
        self.assertEqual(result['pairwise_scores'], {'combination': 0, 'conflict': 0})
        connection = result['group_connections'][0]
        self.assertEqual(connection['relation_id'], group['relation_id'])
        self.assertEqual(connection['guest_participants'], ['year', 'month'])
        self.assertEqual(connection['host_participants'], ['day', 'hour'])
        self.assertFalse(connection['included_in_score'])
        encoded = BinZhuDynamics.model_validate(result).model_dump()
        self.assertEqual(encoded['group_connections'], result['group_connections'])
        self.assertTrue(any('참여 위치: 년, 월, 일, 시' in p for p in result['ai_prompt_bullets']))

    def test_pairwise_scores_describe_relations_without_career_claims(self):
        def rel(kind):
            return dict(category='지지', type=kind, from_pillar='year', to_pillar='day')
        # 십성의 취용 조건 없이 관계 유형만 가산하는 규칙이다.
        for relations, direction, scores in [
            ([rel('육합(六合)')], '합 관계 우세', {'combination': 2, 'conflict': 0}),
            ([rel('충(沖)')], '충·해 관계 우세', {'combination': 0, 'conflict': 1.5}),
            ([rel('형(刑)'), rel('파(破)')], '평가 가능한 빈-주 통로 없음', {'combination': 0, 'conflict': 0}),
        ]:
            result = analyze(relations)
            self.assertEqual(result['control_flow']['direction'], direction)
            self.assertEqual(result['pairwise_scores'], scores)
            self.assertEqual(result['rule_version'], '2.0.0')
            text = ' '.join(result['ai_prompt_bullets'])
            for claim in ('큰 성취', '자원취용형', '최적의 시너지', '대기업', '전문직'):
                self.assertNotIn(claim, text)
            self.assertIn('판단하지 않습니다', result['control_flow']['career_advice'])

    def test_nonzero_equal_scores_do_not_imply_life_balance(self):
        endpoints = [('year', 'day'), ('year', 'hour'), ('month', 'day'), ('month', 'hour')]
        combinations = [dict(category='천간', type='천간합(天干合)', from_pillar=a, to_pillar=b)
                        for a, b in endpoints[:3]]
        conflicts = [dict(category='지지', type='충(沖)', from_pillar=a, to_pillar=b)
                     for a, b in endpoints]
        result = analyze(combinations + conflicts)
        self.assertEqual(result['pairwise_scores'], {'combination': 6, 'conflict': 6})
        self.assertEqual(result['control_flow']['direction'], '관계 점수 동률')
        self.assertIn('균형을 뜻하지 않습니다', result['control_flow']['summary_meaning'])

    def test_group_only_does_not_imply_balance_or_acquisition(self):
        groups = [dict(category='지지', type=kind, name=kind, from_pillar='all', to_pillar='all')
                  for kind in ('삼합(三合)', '방합(方合)')]
        result = analyze(groups)
        self.assertEqual(result['guest_host_links'], [])
        self.assertEqual(result['control_flow']['direction'], '평가 가능한 빈-주 통로 없음')
        self.assertEqual(result['interaction_scope'], 'pairwise')
        self.assertEqual(len(result['excluded_interactions']), 2)
        encoded = BinZhuDynamics.model_validate(result).model_dump()
        self.assertEqual(encoded['excluded_interactions'], result['excluded_interactions'])
        self.assertTrue(all(x['reason_code'] == 'group_relation_unsupported' for x in encoded['excluded_interactions']))
        self.assertTrue(any('2건은 계산에서 제외' in p for p in result['ai_prompt_bullets']))

    def test_invalid_or_missing_endpoints_are_reported(self):
        result = analyze([dict(category='지지', type='충(沖)', from_pillar='unknown'),
                          dict(category='지지', type='형(刑)', from_pillar='year', to_pillar='all')])
        self.assertEqual([x['reason_code'] for x in result['excluded_interactions']],
                         ['invalid_endpoint', 'group_relation_unsupported'])
        BinZhuDynamics.model_validate(result)

    def test_three_and_square_groups_with_duplicate_branches_preserve_pairwise_results(self):
        for branches, kind in [('亥卯未亥', '삼합(三合)'), ('寅卯辰寅', '방합(方合)')]:
            with self.subTest(branches=branches):
                matrix = build_interaction_matrix(STEMS, list(branches), '戊')['matrix']
                self.assertTrue(any(r['type'] == kind for r in matrix))
                pairs = [r for r in matrix if r['from_pillar'] != 'all' and r['to_pillar'] != 'all']
                expected = analyze(pairs, list(branches))
                actual = analyze(matrix, list(branches))
                self.assertEqual(actual['control_flow'], expected['control_flow'])
                self.assertEqual(actual['guest_host_links'], expected['guest_host_links'])
                self.assertTrue(any(r['type'] == kind for r in actual['excluded_interactions']))

    def test_repeated_group_is_excluded_once_and_does_not_change_direction(self):
        pair = dict(category='지지', type='충(沖)', from_pillar='year', to_pillar='day')
        group = dict(category='지지', type='삼합(三合)', from_pillar='all', to_pillar='all')
        expected = analyze([pair])
        result = analyze([pair, group, group])
        self.assertEqual(result['control_flow'], expected['control_flow'])
        self.assertEqual(len(result['excluded_interactions']), 1)


if __name__ == '__main__':
    unittest.main()
