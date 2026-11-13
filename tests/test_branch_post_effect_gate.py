"""미해결 관계가 지지별 최종 세력으로 위장되지 않도록 검증한다."""

import json
import unittest
from pathlib import Path

from schemas.branch_dynamics_v3_contract import validate_branch_dynamics_v3
from services.branch_dynamics import analyze_branch_dynamics
from services.branch_dynamics_v3_assembler import (
    assemble_branch_dynamics_v3_foundation, assemble_branch_pairs_v3,
    assemble_branch_groups_v3, assemble_branch_influence_paths_v3,
    assemble_interaction_resolution_v3,
)
from services.branch_post_effect_gate import (
    assess_post_effect_readiness, build_post_effect_trace_skeleton,
)
from services.interaction_matrix import build_interaction_matrix


FIXTURE = Path(__file__).resolve().parent / 'fixtures' / 'branch_dynamics_v3.json'


def payload(stem_text, branch_text):
    stems, branches = list(stem_text), list(branch_text)
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    foundation = assemble_branch_dynamics_v3_foundation(stems, branches, source)
    pairs = assemble_branch_pairs_v3(branches, source)
    groups = assemble_branch_groups_v3(branches, source, pairs)
    data = json.loads(FIXTURE.read_text())
    data['meta'] = foundation['meta']
    data['chart_context'] = foundation['chart_context']
    data['branch_dynamics'] = {
        **assemble_branch_influence_paths_v3(
            branches, foundation['branch_strengths'], pairs, groups),
        'pairwise': pairs,
        'groups': groups,
    }
    data['interaction_resolution'] = assemble_interaction_resolution_v3(pairs, groups)
    data['work_dynamics']['candidate_paths'] = []
    data['llm_interpretation_payload']['structural_facts'] = []
    data['llm_interpretation_payload']['unresolved_mechanisms'] = []
    return data


def readiness(data, pillar):
    dynamics = data['branch_dynamics']
    return assess_post_effect_readiness(
        pillar, dynamics['pairwise'], dynamics['groups'],
        dynamics['influence_paths'], data['interaction_resolution'])


def trace(data, pillar, **kwargs):
    dynamics = data['branch_dynamics']
    return build_post_effect_trace_skeleton(
        pillar, dynamics['branch_strengths'][pillar], dynamics['pairwise'],
        dynamics['groups'], dynamics['influence_paths'],
        data['interaction_resolution'], **kwargs)


class BranchPostEffectGateTests(unittest.TestCase):
    def test_trace_keeps_current_background_and_unknown_structure_separate(self):
        a = payload('乙己己庚', '巳丑未午')
        day = trace(a, 'day')
        self.assertEqual(day['status'], 'not_calculated')
        self.assertEqual(day['readiness_status'], 'incomplete')
        self.assertEqual(day['input_power_ref'],
                         'branch_strengths.day.after_stem_power')
        self.assertIn('path:background:year:day:branch',
                      day['background']['included_path_ids'])
        self.assertIn('path:background:hour:day:branch',
                      day['background']['included_path_ids'])
        self.assertIn('group:square:si_wu_wei',
                      {item['ref_id'] for item in day['unresolved_refs']})
        self.assertIsNone(day['reconciled_pre_effect_power'])
        self.assertEqual(day['applied_effect_refs'], [])
        self.assertIsNone(day['aggregation_formula_id'])

        month = trace(a, 'month')
        self.assertIn('path:background:hour:month:branch',
                      month['background']['excluded_path_ids'])

        d = payload('庚己丙乙', '申丑申未')
        month = trace(d, 'month',
                      known_unmodeled_mechanism_ids=['tomb_entry'])
        self.assertIn('path:background:year:month:branch',
                      month['background']['included_path_ids'])
        self.assertIn('path:background:day:month:branch',
                      month['background']['included_path_ids'])
        self.assertEqual(month['model_scope']['coverage_status'], 'partial')
        self.assertEqual(month['model_scope']['unmodeled_mechanism_ids'],
                         ['tomb_entry'])
        self.assertIn({'ref_id': 'mechanism:tomb_entry',
                       'reason': 'unmodeled_mechanism'},
                      month['unresolved_refs'])

    def test_trace_does_not_apply_ziwu_provisional_loss(self):
        data = payload('甲甲甲甲', '子午辰寅')
        year = trace(data, 'year')
        self.assertIn('branch:clash:year:month',
                      year['available_provisional_interaction_ids'])
        self.assertEqual(year['applied_effect_refs'], [])
        self.assertIsNone(year['reconciled_pre_effect_power'])
        self.assertEqual(data['branch_dynamics']['branch_strengths']['year'][
            'post_effect_status'], 'not_calculated')

    def test_no_known_blockers_still_has_no_final_number(self):
        data = payload('甲甲甲甲', '丑丑丑丑')
        year = trace(data, 'year')
        self.assertEqual(year['readiness_status'], 'no_known_blockers')
        self.assertEqual(year['model_scope']['coverage_status'], 'not_assessed')
        self.assertEqual(year['unresolved_refs'], [])
        self.assertIsNone(year['aggregation_formula_id'])
        self.assertIsNone(data['branch_dynamics']['branch_strengths']['year'][
            'post_effect_power'])

        data['branch_dynamics']['branch_strengths']['year'][
            'influence_path_ids'].pop()
        with self.assertRaisesRegex(ValueError, '출처 경로 참조'):
            trace(data, 'year')

        data = payload('甲甲甲甲', '丑丑丑丑')
        with self.assertRaisesRegex(ValueError, '미지원 기전 ID'):
            trace(data, 'year', known_unmodeled_mechanism_ids='tomb_entry')

    def test_a_and_d_keep_clash_and_unscored_structure_as_blockers(self):
        a = payload('乙己己庚', '巳丑未午')
        day_blockers = {item['ref_id'] for item in readiness(a, 'day')['blockers']}
        month_blockers = {item['ref_id'] for item in readiness(a, 'month')['blockers']}
        self.assertIn('branch:clash:month:day', day_blockers)
        self.assertIn('branch:clash:month:day', month_blockers)
        self.assertIn('group:square:si_wu_wei', day_blockers)
        self.assertNotIn('group:square:si_wu_wei', month_blockers)
        self.assertTrue(any(ref.startswith('path:group:') for ref in day_blockers))

        d = payload('庚己丙乙', '申丑申未')
        month_blockers = {item['ref_id'] for item in readiness(d, 'month')['blockers']}
        hour_blockers = {item['ref_id'] for item in readiness(d, 'hour')['blockers']}
        self.assertIn('branch:clash:month:hour', month_blockers)
        self.assertIn('branch:clash:month:hour', hour_blockers)
        self.assertFalse(any(ref.startswith('group:') for ref in month_blockers))
        validate_branch_dynamics_v3(a)
        validate_branch_dynamics_v3(d)

    def test_provisional_ziwu_is_tracked_without_making_final_power(self):
        data = payload('甲甲甲甲', '子午辰寅')
        year = readiness(data, 'year')
        self.assertIn('branch:clash:year:month',
                      year['provisional_interaction_ids'])
        blocker_ids = {item['ref_id'] for item in year['blockers']}
        self.assertNotIn('branch:clash:year:month', blocker_ids)
        self.assertNotIn('branch:control:year:month', blocker_ids)
        self.assertTrue(blocker_ids)
        self.assertIsNone(data['branch_dynamics']['branch_strengths']['year'][
            'post_effect_power'])

        data['branch_dynamics']['branch_strengths']['year'].update({
            'post_effect_power': 0.5,
            'post_effect_status': 'provisional',
        })
        with self.assertRaisesRegex(ValueError, '미해결 작용'):
            validate_branch_dynamics_v3(data)

    def test_detected_group_remains_unresolved_blocker(self):
        data = payload('甲甲甲甲', '巳亥卯未')
        group = data['branch_dynamics']['groups'][0]
        self.assertEqual(group['formation_status'], 'detected')
        blockers = {item['ref_id'] for item in readiness(data, 'month')['blockers']}
        self.assertIn(group['group_id'], blockers)

    def test_even_without_blockers_final_number_needs_aggregation_trace(self):
        data = payload('甲甲甲甲', '丑丑丑丑')
        self.assertEqual(readiness(data, 'year')['blockers'], [])
        validate_branch_dynamics_v3(data)
        data['branch_dynamics']['branch_strengths']['year'].update({
            'post_effect_power': 1.0,
            'post_effect_status': 'resolved',
        })
        with self.assertRaisesRegex(ValueError, '집계식과 전체 기여 근거'):
            validate_branch_dynamics_v3(data)


if __name__ == '__main__':
    unittest.main()
