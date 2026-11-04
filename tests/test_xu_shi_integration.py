"""프로젝트 달력 DB를 읽기 전용으로 사용하는 라우터/응답 계약 검증."""
from pathlib import Path
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from routers.root import get_calenda_data
from schemas.saju_analysis import SajuAnalysisResponse
from services.analysis import analyze_advanced_tonggeun
from services.xu_shi import analyze_xu_shi_dynamics

DB_PATH = Path(__file__).resolve().parents[1] / 'manseryuk.db'


@unittest.skipUnless(DB_PATH.is_file(), '통합 검증에 필요한 달력 DB가 없습니다.')
class XuShiIntegrationTests(unittest.TestCase):
    def test_old_cross_pillar_root_is_external_support_in_new_response(self):
        engine = create_engine(f'sqlite:///file:{DB_PATH}?mode=ro&uri=true')
        try:
            with Session(engine) as session:
                response = get_calenda_data(1990, '1', '1', 12, 0, 'sol', '남', session)
            details = response['analysis']['details']
            pillars = ('year', 'month', 'day', 'hour')
            stems = [details[pillar]['stem']['char'] for pillar in pillars]
            branches = [details[pillar]['branch']['char'] for pillar in pillars]
            legacy = analyze_xu_shi_dynamics(
                stems, branches, stems[2],
                analyze_advanced_tonggeun(
                    stems, branches, scope='all_four_branches_weighted'),
                response['advanced_analysis']['interactions']['matrix'],
            )
            current = response['advanced_analysis']['xu_shi_dynamics']
            self.assertEqual(legacy['pillars']['month']['score'], 1.11)
            self.assertEqual(legacy['pillars']['month']['original_status'], '실(實)')
            self.assertEqual(current['pillars']['month']['score'], 0)
            self.assertEqual(current['pillars']['month']['original_status'],
                             '허투(虛透)')
            self.assertEqual(details['month']['stem']['external_support_score'], 1.11)
            self.assertEqual(current['root_scope'], 'same_pillar_only')
        finally:
            engine.dispose()

    def test_previously_failing_group_relation_date_returns_full_response(self):
        engine = create_engine(f'sqlite:///file:{DB_PATH}?mode=ro&uri=true')
        try:
            with Session(engine) as session:
                result = get_calenda_data(1995, '5', '12', 14, 30, 'sol', '남', session)
                response = SajuAnalysisResponse.model_validate(result).model_dump(mode='json')
            advanced = response['advanced_analysis']
            branch_dynamics = advanced['branch_dynamics']
            self.assertEqual(branch_dynamics['scope'], 'natal')
            self.assertEqual(branch_dynamics['score_meaning'], 'uncalibrated_relative_model_index')
            self.assertEqual(branch_dynamics['rule_version'], '2.19.0')
            self.assertEqual(set(branch_dynamics['branch_strengths']), {'year', 'month', 'day', 'hour'})
            self.assertEqual(len(branch_dynamics['pairwise']), 6)
            self.assertTrue(all('force_dominance' in relation
                                for pair in branch_dynamics['pairwise']
                                for relation in pair['relations']))
            self.assertTrue(all('roles' in relation
                                for pair in branch_dynamics['pairwise']
                                for relation in pair['relations']))
            self.assertEqual(branch_dynamics['branch_strengths']['month']['branch'], '巳')
            self.assertEqual(branch_dynamics['branch_strengths']['month']['stem_branch_relation']['stem'], '辛')
            bin_zhu = advanced['bin_zhu_dynamics']
            self.assertEqual(bin_zhu['interaction_scope'], 'pairwise')
            self.assertTrue(bin_zhu['excluded_interactions'])
            self.assertEqual(bin_zhu['excluded_interactions'], result['advanced_analysis']['bin_zhu_dynamics']['excluded_interactions'])
            self.assertEqual(bin_zhu['group_connections'], result['advanced_analysis']['bin_zhu_dynamics']['group_connections'])
            self.assertEqual(bin_zhu['guest_host_links'], result['advanced_analysis']['bin_zhu_dynamics']['guest_host_links'])
            self.assertTrue(bin_zhu['group_connections'])
            self.assertEqual(bin_zhu['rule_version'], '3.0.0')
            interactions = advanced['interactions']
            self.assertEqual(interactions['rule_version'], '1.3.0')
            relation_ids = {r['relation_id'] for r in interactions['matrix']}
            for group in bin_zhu['group_connections']:
                self.assertIn(group['relation_id'], relation_ids)
                self.assertFalse(group['included_in_score'])
            for link in bin_zhu['guest_host_links']:
                self.assertIn(link['relation_id'], relation_ids)
            self.assertTrue(any(p.startswith('【빈주 계산 범위】') for p in advanced['ai_consultation_prompts']))
            xu_shi = advanced['xu_shi_dynamics']
            self.assertEqual(xu_shi, result['advanced_analysis']['xu_shi_dynamics'])
            self.assertEqual(xu_shi['rule_version'], '4.0.0')
            self.assertEqual(xu_shi['root_scope'], 'same_pillar_only')
            self.assertFalse(xu_shi['shared_roots'])
            for pillar, state in xu_shi['pillars'].items():
                self.assertTrue(all(root['pillar'] == pillar
                                    for root in state['root_evidence']))
        finally:
            engine.dispose()

    def test_route_response_preserves_evidence_and_natal_prompt(self):
        engine = create_engine(f'sqlite:///file:{DB_PATH}?mode=ro&uri=true')
        try:
            with Session(engine) as session:
                result = get_calenda_data(1990, '1', '1', 12, 0, 'sol', '남', session)
                response = SajuAnalysisResponse.model_validate(result).model_dump(mode='json')
            advanced = response['advanced_analysis']
            xu_shi = advanced['xu_shi_dynamics']
            self.assertEqual(xu_shi, result['advanced_analysis']['xu_shi_dynamics'])
            self.assertEqual(xu_shi['analysis_scope'], 'natal')
            for state in xu_shi['pillars'].values():
                self.assertEqual(state['root_impact_status'], 'not_evaluated')
                self.assertIsNone(state['root_impact_score'])
                self.assertEqual(state['score'], state['effective_score'])
                self.assertEqual(state['original_status'], state['current_status'])
            self.assertTrue(any(p['related_interactions'] for p in xu_shi['pillars'].values()))
            self.assertTrue(any(p['root_evidence'] for p in xu_shi['pillars'].values()))
            prompts = [p for p in advanced['ai_consultation_prompts'] if p.startswith('【원국 허실】')]
            self.assertEqual(len(prompts), 1)
            self.assertIn(xu_shi['overall_status'], prompts[0])
            self.assertIn('시기별 변화가 아닙니다', prompts[0])
            self.assertIn('단정하지 마세요', prompts[0])
        finally:
            engine.dispose()


if __name__ == '__main__':
    unittest.main()
