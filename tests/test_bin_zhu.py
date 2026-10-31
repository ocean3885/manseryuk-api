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
        self.assertEqual(result['pairwise_scores']['combination'], 0)
        self.assertEqual(result['pairwise_scores']['conflict'], 0)
        connection = result['group_connections'][0]
        self.assertEqual(connection['relation_id'], group['relation_id'])
        self.assertEqual(connection['guest_participants'], ['year', 'month'])
        self.assertEqual(connection['host_participants'], ['day', 'hour'])
        self.assertEqual(connection['cohesion_score'], 3.0)
        self.assertEqual(result['group_cohesion_score'], 3.0)
        self.assertFalse(connection['included_in_score'])
        encoded = BinZhuDynamics.model_validate(result).model_dump()
        self.assertEqual(encoded['group_connections'], result['group_connections'])
        self.assertTrue(any('참여 위치: 년, 월, 일, 시' in p for p in result['ai_prompt_bullets']))

    def test_pairwise_scores_describe_relations_without_career_claims(self):
        def rel(kind):
            return dict(category='지지', type=kind, from_pillar='year', to_pillar='day')
        # 십성의 취용 조건 없이 거리 가중치 및 상호작용 강도를 반영한다.
        for relations, direction, w_scores, unw_scores in [
            ([rel('육합(六合)')], '합 관계 우세', {'combination': 1.05, 'conflict': 0.0}, {'unweighted_combination': 2.0, 'unweighted_conflict': 0.0}),
            ([rel('충(沖)')], '충·형·천 관계 우세', {'combination': 0.0, 'conflict': 1.4}, {'unweighted_combination': 0.0, 'unweighted_conflict': 1.5}),
            ([rel('형(刑)')], '충·형·천 관계 우세', {'combination': 0.0, 'conflict': 1.05}, {'unweighted_combination': 0.0, 'unweighted_conflict': 1.5}),
            ([rel('파(破)')], '평가 가능한 빈-주 통로 없음', {'combination': 0.0, 'conflict': 0.0}, {'unweighted_combination': 0.0, 'unweighted_conflict': 0.0}),
        ]:
            result = analyze(relations)
            self.assertEqual(result['control_flow']['direction'], direction)
            self.assertEqual(result['pairwise_scores']['combination'], w_scores['combination'])
            self.assertEqual(result['pairwise_scores']['conflict'], w_scores['conflict'])
            self.assertEqual(result['pairwise_scores']['unweighted_combination'], unw_scores['unweighted_combination'])
            self.assertEqual(result['pairwise_scores']['unweighted_conflict'], unw_scores['unweighted_conflict'])
            self.assertEqual(result['rule_version'], '3.0.0')
            self.assertIn('dominant_interaction', result['control_flow'])
            self.assertIn('interpretation_notes', result['control_flow'])
            text = ' '.join(result['ai_prompt_bullets'])
            for claim in ('큰 성취', '자원취용형', '최적의 시너지', '대기업', '전문직'):
                self.assertNotIn(claim, text)
            self.assertIn('판단하지 않습니다', result['control_flow']['career_advice'])

    def test_nonzero_equal_scores_do_not_imply_life_balance(self):
        # 인접한 월(month)-일(day)의 육합(1.5)과 천간충(1.5)으로 동률 구성
        combinations = [dict(category='지지', type='육합(六合)', from_pillar='month', to_pillar='day')]
        conflicts = [dict(category='천간', type='천간충(天干沖)', from_pillar='month', to_pillar='day')]
        result = analyze(combinations + conflicts)
        self.assertEqual(result['pairwise_scores']['combination'], 1.5)
        self.assertEqual(result['pairwise_scores']['conflict'], 1.5)
        self.assertEqual(result['control_flow']['direction'], '관계 점수 동률')
        self.assertEqual(result['control_flow']['dominant_interaction'], 'balanced')
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
                self.assertEqual(actual['pairwise_scores'], expected['pairwise_scores'])
                self.assertEqual(actual['guest_host_links'], expected['guest_host_links'])
                self.assertEqual(actual['control_flow']['direction'], '다자 합 결합 및 대립(충·형·천) 공존')
                self.assertTrue(any(r['type'] == kind for r in actual['excluded_interactions']))

    def test_repeated_group_is_excluded_once_and_does_not_change_direction(self):
        pair = dict(category='지지', type='충(沖)', from_pillar='year', to_pillar='day')
        group = dict(category='지지', type='삼합(三合)', from_pillar='all', to_pillar='all')
        expected = analyze([pair])
        result = analyze([pair, group, group])
        self.assertEqual(result['control_flow'], expected['control_flow'])
        self.assertEqual(len(result['excluded_interactions']), 1)

    def test_zi_mao_break_is_excluded_from_bin_zhu_scores(self):
        # 子卯는 파로만 탐지한다. 빈주 집계는 파를 미지원 관계로 분리한다.
        matrix = build_interaction_matrix(list('甲甲甲甲'), list('子子卯卯'), '甲')['matrix']
        result = analyze_bin_zhu_dynamics(list('甲甲甲甲'), list('子子卯卯'), '甲', matrix)
        self.assertEqual(result['pairwise_scores']['conflict'], 0)
        self.assertEqual(result['pairwise_scores']['unweighted_conflict'], 0)
        self.assertEqual(result['guest_host_links'], [])
        self.assertEqual(len(result['excluded_interactions']), 4)
        self.assertTrue(all(item['type'] == '파(破)' and
                            item['reason_code'] == 'unsupported_relation_type'
                            for item in result['excluded_interactions']))

        # 파(破) 관계는 excluded_interactions에 unsupported_relation_type으로 보존
        break_item = dict(category='지지', type='파(破)', name='자유파', from_pillar='year', to_pillar='day')
        res_break = analyze([break_item])
        self.assertEqual(res_break['pairwise_scores']['conflict'], 0)
        self.assertEqual(len(res_break['excluded_interactions']), 1)
        self.assertEqual(res_break['excluded_interactions'][0]['reason_code'], 'unsupported_relation_type')
        BinZhuDynamics.model_validate(res_break)

    def test_bridging_group_without_pairwise_links(self):
        group_item = {
            'relation_id': '지지:삼합(三合):삼합 木국:year,day,hour',
            'category': '지지', 'type': '삼합(三合)', 'name': '삼합 木국',
            'from_pillar': 'all', 'to_pillar': 'all',
            'participants': ['year', 'day', 'hour'],
            'relation_scope': 'group'
        }
        res = analyze([group_item])
        self.assertEqual(res['control_flow']['direction'], '다자 합 결합(삼합/방합) 형성')
        self.assertIn('다자 합(삼합/방합) 관계', res['control_flow']['summary_meaning'])
        self.assertIn('형성되어 있습니다', res['control_flow']['summary_meaning'])
        self.assertIn('국가/조상/대외환경', res['guest_structure']['scope'])
        self.assertIn('자아/배우자/개인영역', res['host_structure']['scope'])

    def test_phase3_ten_god_vector_and_mechanisms(self):
        # 1) 주가 빈의 재성을 일간합으로 취용하는 경우 (일간합재 / host_takes_guest)
        # year stem: 癸(정재) vs day stem: 戊 -> 무계합(戊癸合)
        stem_hap = dict(category='천간', type='천간합(天干合)', from_pillar='year', to_pillar='day', weight=0.7, score=1.26)
        res = analyze_bin_zhu_dynamics(['癸', '丙', '戊', '庚'], list('子午卯酉'), '戊', [stem_hap])
        self.assertEqual(res['control_flow']['vector_code'], 'host_takes_guest')
        self.assertEqual(res['guest_host_links'][0]['mechanism'], '일간합재(合財)')
        self.assertEqual(res['guest_host_links'][0]['flow_direction'], 'host_takes_guest')
        self.assertTrue(any('【빈주 역학 흐름】' in p for p in res['ai_prompt_bullets']))

        # 2) 삼합(결합도 3.0)으로 결합된 경우 (mutual_cooperation)
        matrix = build_interaction_matrix(STEMS, list('亥卯未亥'), '戊')['matrix']
        res_group = analyze_bin_zhu_dynamics(STEMS, list('亥卯未亥'), '戊', matrix)
        self.assertEqual(res_group['control_flow']['vector_code'], 'mutual_cooperation')
        self.assertIn('dominant_forces', res_group['guest_structure'])
        self.assertIn('dominant_means', res_group['host_structure'])

        # 3) 순수 다자 합으로 연결된 경우 (mutual_cooperation: 상호 연대/협력형)
        group_only = [{
            'relation_id': '지지:삼합(三合):삼합 木국:year,day,hour',
            'category': '지지', 'type': '삼합(三合)', 'name': '삼합 木국',
            'from_pillar': 'all', 'to_pillar': 'all',
            'participants': ['year', 'day', 'hour'],
            'relation_scope': 'group'
        }]
        res_coop = analyze_bin_zhu_dynamics(STEMS, list('亥卯未亥'), '戊', group_only)
        self.assertEqual(res_coop['control_flow']['vector_code'], 'mutual_cooperation')

        # 4) 외부 편관/칠살의 충극으로 환경 압박이 발생하는 경우 (guest_pressures_host: 환경 적응/조율형)
        stem_press = dict(category='천간', type='천간충(天干沖)', from_pillar='year', to_pillar='day', weight=0.7, score=1.05)
        res_press = analyze_bin_zhu_dynamics(['庚', '丙', '甲', '乙'], list('子午卯酉'), '甲', [stem_press])
        self.assertEqual(res_press['control_flow']['vector_code'], 'guest_pressures_host')


if __name__ == '__main__':
    unittest.main()
