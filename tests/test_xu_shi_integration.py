"""프로젝트 달력 DB를 읽기 전용으로 사용하는 라우터/응답 계약 검증."""
from pathlib import Path
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from routers.root import get_calenda_data
from schemas.saju_analysis import SajuAnalysisResponse

DB_PATH = Path(__file__).resolve().parents[1] / 'manseryuk.db'


@unittest.skipUnless(DB_PATH.is_file(), '통합 검증에 필요한 달력 DB가 없습니다.')
class XuShiIntegrationTests(unittest.TestCase):
    def test_previously_failing_group_relation_date_returns_full_response(self):
        engine = create_engine(f'sqlite:///file:{DB_PATH}?mode=ro&uri=true')
        try:
            with Session(engine) as session:
                result = get_calenda_data(1995, '5', '12', 14, 30, 'sol', '남', session)
                response = SajuAnalysisResponse.model_validate(result).model_dump(mode='json')
            advanced = response['advanced_analysis']
            bin_zhu = advanced['bin_zhu_dynamics']
            self.assertEqual(bin_zhu['interaction_scope'], 'pairwise')
            self.assertTrue(bin_zhu['excluded_interactions'])
            self.assertEqual(bin_zhu['excluded_interactions'], result['advanced_analysis']['bin_zhu_dynamics']['excluded_interactions'])
            self.assertEqual(bin_zhu['group_connections'], result['advanced_analysis']['bin_zhu_dynamics']['group_connections'])
            self.assertEqual(bin_zhu['guest_host_links'], result['advanced_analysis']['bin_zhu_dynamics']['guest_host_links'])
            self.assertTrue(bin_zhu['group_connections'])
            self.assertEqual(bin_zhu['rule_version'], '2.0.0')
            interactions = advanced['interactions']
            self.assertEqual(interactions['rule_version'], '1.1.0')
            relation_ids = {r['relation_id'] for r in interactions['matrix']}
            for group in bin_zhu['group_connections']:
                self.assertIn(group['relation_id'], relation_ids)
                self.assertFalse(group['included_in_score'])
            for link in bin_zhu['guest_host_links']:
                self.assertIn(link['relation_id'], relation_ids)
            self.assertTrue(any(p.startswith('【빈주 계산 범위】') for p in advanced['ai_consultation_prompts']))
            xu_shi = advanced['xu_shi_dynamics']
            self.assertEqual(xu_shi, result['advanced_analysis']['xu_shi_dynamics'])
            self.assertTrue(xu_shi['shared_roots'])
            for group in xu_shi['shared_roots']:
                for dependent in group['dependents']:
                    pillar = xu_shi['pillars'][dependent['stem_pillar']]
                    self.assertTrue(any(root['pillar'] == group['root_pillar'] for root in pillar['root_evidence']))
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
