"""기존 세력 보정을 출처 경로로 옮기되 미계산 구조를 수치화하지 않는다."""

import copy
import unittest

from services.branch_dynamics import analyze_branch_dynamics
from services.branch_dynamics_v3_assembler import (
    assemble_branch_dynamics_v3_foundation, assemble_branch_pairs_v3,
    assemble_branch_groups_v3,
)
from services.branch_influence_paths import build_influence_paths
from services.interaction_matrix import build_interaction_matrix


def chart(stem_text, branch_text, **kwargs):
    stems, branches = list(stem_text), list(branch_text)
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    foundation = assemble_branch_dynamics_v3_foundation(stems, branches, source)
    pairs = assemble_branch_pairs_v3(branches, source)
    groups = assemble_branch_groups_v3(branches, source, pairs)
    original_strengths = copy.deepcopy(foundation['branch_strengths'])
    paths = build_influence_paths(
        branches, foundation['branch_strengths'], pairs, groups, **kwargs)
    assert original_strengths == foundation['branch_strengths']
    return {item['path_id']: item for item in paths}


def interpretation_candidates():
    tomb_id = 'path:structural:tomb_entry:year:day:month:branch'
    return [
        {
            'path_id': tomb_id,
            'source_pillars': ['year', 'day'],
            'target': {'pillar': 'month', 'component': 'branch', 'stem': None},
            'stage': 'structural_context',
            'mechanism': 'tomb_entry_candidate',
            'evidence_level': 'source_interpretation',
            'accounting_decision': 'undetermined',
            'quantity': None,
            'evidence_refs': [{'kind': 'case', 'id': 'D'}],
            'overlaps_path_ids': [
                'path:background:year:month:branch',
                'path:background:day:month:branch',
            ],
            'replaces_path_ids': [],
            'depends_on_path_ids': [],
        },
        {
            'path_id': 'path:effect:month:hour:hidden_stem:乙',
            'source_pillars': ['month'],
            'target': {'pillar': 'hour', 'component': 'hidden_stem', 'stem': '乙'},
            'stage': 'relation_effect',
            'mechanism': 'clash_hidden_damage_candidate',
            'evidence_level': 'source_interpretation',
            'accounting_decision': 'undetermined',
            'quantity': None,
            'evidence_refs': [
                {'kind': 'interaction', 'id': 'branch:clash:month:hour'},
                {'kind': 'case', 'id': 'D'},
            ],
            'overlaps_path_ids': [],
            'replaces_path_ids': [],
            'depends_on_path_ids': [tomb_id],
        },
    ]


class BranchInfluencePathTests(unittest.TestCase):
    def test_a_preserves_background_and_keeps_square_unscored(self):
        paths = chart('乙己己庚', '巳丑未午')
        si_to_wei = paths['path:background:year:day:branch']
        wu_to_wei = paths['path:background:hour:day:branch']
        self.assertEqual(si_to_wei['quantity'],
                         {'unit': 'adjustment_ratio', 'value': 0.028735})
        self.assertEqual(wu_to_wei['quantity']['value'], 0.038133)
        self.assertEqual(si_to_wei['accounting_decision'], 'include')
        self.assertEqual(wu_to_wei['accounting_decision'], 'include')
        self.assertEqual(si_to_wei['mechanism'], 'element_generate')

        square = paths['path:group:formation:square:year:day:hour:day:branch']
        self.assertEqual(square['source_pillars'], ['year', 'day', 'hour'])
        self.assertEqual(square['accounting_decision'], 'undetermined')
        self.assertIsNone(square['quantity'])
        self.assertEqual(set(square['overlaps_path_ids']), {
            si_to_wei['path_id'], wu_to_wei['path_id'],
        })
        self.assertEqual(square['replaces_path_ids'], [])

        suppressed = paths['path:background:hour:month:branch']
        self.assertEqual(suppressed['accounting_decision'], 'exclude')
        self.assertEqual(suppressed['quantity']['value'], 0)
        self.assertTrue(any(item['kind'] == 'interaction'
                            for item in suppressed['evidence_refs']))
        self.assertTrue(any(item['target'] == {
            'pillar': 'month', 'component': 'branch', 'stem': None,
        } and item['quantity'] is None and
            item['stage'] == 'structural_context'
            for item in paths.values()))

    def test_d_keeps_two_shen_separate_and_accepts_unscored_case_paths(self):
        base = chart('庚己丙乙', '申丑申未')
        self.assertFalse(any(item['mechanism'] == 'tomb_entry_candidate'
                             for item in base.values()))
        paths = chart('庚己丙乙', '申丑申未',
                      interpretation_candidates=interpretation_candidates(),
                      case_ids={'D'})
        year = paths['path:background:year:month:branch']
        day = paths['path:background:day:month:branch']
        self.assertEqual(year['quantity']['value'], -0.031722)
        self.assertEqual(day['quantity']['value'], -0.035254)
        self.assertEqual(year['source_pillars'], ['year'])
        self.assertEqual(day['source_pillars'], ['day'])

        tomb = paths['path:structural:tomb_entry:year:day:month:branch']
        damage = paths['path:effect:month:hour:hidden_stem:乙']
        self.assertEqual(set(tomb['overlaps_path_ids']),
                         {year['path_id'], day['path_id']})
        self.assertIsNone(tomb['quantity'])
        self.assertIsNone(damage['quantity'])
        self.assertEqual(damage['depends_on_path_ids'], [tomb['path_id']])
        self.assertEqual(damage['target']['stem'], '乙')

    def test_missing_evidence_wrong_hidden_stem_and_cycle_are_rejected(self):
        candidates = interpretation_candidates()
        candidates[1]['target']['stem'] = '甲'
        with self.assertRaisesRegex(ValueError, '지장간'):
            chart('庚己丙乙', '申丑申未',
                  interpretation_candidates=candidates, case_ids={'D'})

        candidates = interpretation_candidates()
        candidates[0]['quantity'] = {'unit': 'power_delta', 'value': 0}
        with self.assertRaisesRegex(ValueError, '미정 경로'):
            chart('庚己丙乙', '申丑申未',
                  interpretation_candidates=candidates, case_ids={'D'})

        candidates = interpretation_candidates()
        candidates[0]['accounting_decision'] = 'exclude'
        candidates[0]['quantity'] = {'unit': 'power_delta', 'value': 0}
        with self.assertRaisesRegex(ValueError, '교재·가설 경로'):
            chart('庚己丙乙', '申丑申未',
                  interpretation_candidates=candidates, case_ids={'D'})

        candidates = interpretation_candidates()
        candidates[0]['depends_on_path_ids'] = [candidates[1]['path_id']]
        with self.assertRaisesRegex(ValueError, '순환'):
            chart('庚己丙乙', '申丑申未',
                  interpretation_candidates=candidates, case_ids={'D'})

        candidates = interpretation_candidates()
        with self.assertRaisesRegex(ValueError, '없는 근거 참조'):
            chart('庚己丙乙', '申丑申未',
                  interpretation_candidates=candidates)

    def test_repeated_and_clashed_trines_keep_unquantified_paths(self):
        repeated = chart('己丁辛己', '亥卯未亥')
        trine = [item for item in repeated.values()
                 if item['mechanism'] == 'trine_participation_candidate']
        self.assertEqual(len(trine), 6)
        self.assertEqual(len({item['path_id'] for item in trine}), 6)
        self.assertTrue(all(item['quantity'] is None for item in trine))

        suppressed = chart('甲甲甲甲', '巳亥卯未')
        trine = [item for item in suppressed.values()
                 if item['mechanism'] == 'trine_participation_candidate']
        self.assertTrue(trine)
        self.assertTrue(all(item['quantity'] is None for item in trine))

        punished = chart('甲甲甲甲', '寅巳申未')
        triple = [item for item in punished.values()
                  if item['mechanism'] == 'triple_punishment_participation_candidate']
        self.assertEqual(len(triple), 3)
        self.assertTrue(all(item['quantity'] is None for item in triple))

    def test_same_background_cannot_be_included_twice(self):
        base = chart('乙己己庚', '巳丑未午')
        duplicate = copy.deepcopy(base['path:background:year:day:branch'])
        duplicate['path_id'] = 'path:other-name:year:day:branch'
        with self.assertRaisesRegex(ValueError, '중복 계상'):
            chart('乙己己庚', '巳丑未午',
                  interpretation_candidates=[duplicate])

        square = copy.deepcopy(
            base['path:group:formation:square:year:day:hour:day:branch'])
        square['path_id'] = 'path:other-name:group:day:branch'
        square['accounting_decision'] = 'include'
        square['quantity'] = {'unit': 'power_delta', 'value': 0.1}
        with self.assertRaisesRegex(ValueError, '겹치는 기여'):
            chart('乙己己庚', '巳丑未午',
                  interpretation_candidates=[square])


if __name__ == '__main__':
    unittest.main()
