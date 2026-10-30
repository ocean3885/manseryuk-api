"""v3 설계 샘플의 구조·참조·수치 상태 회귀 검사."""

import copy
import json
import re
import unittest
from pathlib import Path

from schemas.branch_dynamics_v3_contract import validate_branch_dynamics_v3


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'branch_dynamics_v3.json'
DESIGN = ROOT / 'docs' / 'branch_dynamics_v3.json'


def load_fixture():
    return json.loads(FIXTURE.read_text())


def relation(data, relation_id):
    return next(item for pair in data['branch_dynamics']['pairwise']
                for item in pair['relations'] if item['relation_id'] == relation_id)


class BranchDynamicsV3ContractTests(unittest.TestCase):
    def test_fixture_matches_design_and_satisfies_contract(self):
        data = load_fixture()
        design = json.loads(re.sub(r'//[^\n]*', '', DESIGN.read_text()))
        self.assertEqual(data, design)
        validate_branch_dynamics_v3(data)
        self.assertEqual(len(data['branch_dynamics']['pairwise']), 6)
        self.assertEqual(len(data['branch_dynamics']['groups'][0]['formation_candidates']), 2)
        self.assertEqual(sum(item['type'] in ('generate', 'control')
                             for pair in data['branch_dynamics']['pairwise']
                             for item in pair['relations']), 5)

    def test_missing_pair_and_duplicate_relation_are_rejected(self):
        data = load_fixture()
        data['branch_dynamics']['pairwise'].pop()
        with self.assertRaisesRegex(ValueError, '여섯 위치 쌍'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        pair = data['branch_dynamics']['pairwise'][0]
        pair['relations'].append(copy.deepcopy(pair['relations'][0]))
        with self.assertRaisesRegex(ValueError, '중복 관계 ID'):
            validate_branch_dynamics_v3(data)

    def test_broken_group_and_work_references_are_rejected(self):
        data = load_fixture()
        component = data['branch_dynamics']['groups'][0]['formation_candidates'][0]['component_pairs'][0]
        component['relation_id'] = 'branch:half_combine:unknown:pair'
        with self.assertRaisesRegex(ValueError, '존재하지 않는 쌍 관계'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        path = data['work_dynamics']['candidate_paths'][0]
        path['source_interaction_ids'].append('branch:control:unknown:pair')
        with self.assertRaisesRegex(ValueError, '작공 원천'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        data['interaction_resolution']['unresolved_interaction_ids'].append(
            'group:trine:unknown')
        with self.assertRaisesRegex(ValueError, '존재하지 않는 관계'):
            validate_branch_dynamics_v3(data)

    def test_structural_relation_cannot_receive_force_or_become_active(self):
        data = load_fixture()
        half = relation(data, 'branch:half_combine:month:day')
        half['metrics'] = {'applied_power_delta': 0}
        with self.assertRaisesRegex(ValueError, '독립 작용량'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        data['interaction_resolution']['active_interaction_ids'].append(
            'branch:half_combine:month:day')
        with self.assertRaisesRegex(ValueError, '구조 전용'):
            validate_branch_dynamics_v3(data)

    def test_pending_and_conditional_effects_cannot_use_zero_as_unknown(self):
        data = load_fixture()
        candidate = relation(data, 'branch:generate:year:month')
        candidate['metrics'] = {'applied_power_delta': 0}
        with self.assertRaisesRegex(ValueError, 'pending'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        control = relation(data, 'branch:control:month:day')
        control['activation_status'] = 'conditional'
        control['calculation_status'] = 'resolved'
        control['metrics'] = {
            'potential_formula_id': 'test:potential',
            'exposure_formula_id': 'test:exposure',
            'directional_effects': [{
                'from_pillar': 'month', 'to_pillar': 'day',
                'acting_domain': 'guest', 'receiving_domain': 'host',
                'source_capacity': 1.0, 'coefficient': 0.8,
                'distance_weight': 1.0, 'interaction_intensity': 0.8,
                'target_exposure': 0.4, 'applied_power_delta': 0,
            }],
        }
        with self.assertRaisesRegex(ValueError, '조건부 유보'):
            validate_branch_dynamics_v3(data)

    def test_elemental_direction_cannot_be_reversed_by_power(self):
        data = load_fixture()
        control = relation(data, 'branch:control:month:day')
        control['calculation_status'] = 'potential_calculated'
        control['metrics'] = {
            'potential_formula_id': 'test:potential',
            'exposure_formula_id': 'test:exposure',
            'directional_effects': [{
                'from_pillar': 'day', 'to_pillar': 'month',
                'acting_domain': 'host', 'receiving_domain': 'guest',
                'source_capacity': 2.0, 'coefficient': 0.8,
                'distance_weight': 1.0, 'interaction_intensity': 1.6,
                'target_exposure': 0.8, 'applied_power_delta': None,
            }],
        }
        with self.assertRaisesRegex(ValueError, '오행상 방향'):
            validate_branch_dynamics_v3(data)

    def test_group_has_no_independent_power_or_duplicate_sum(self):
        data = load_fixture()
        group = data['branch_dynamics']['groups'][0]
        group['group_power'] = 0
        with self.assertRaisesRegex(ValueError, '독립 작용량'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        group = data['branch_dynamics']['groups'][0]
        group['overlap']['counting_policy'] = 'sum_formations'
        with self.assertRaisesRegex(ValueError, '한 구조망'):
            validate_branch_dynamics_v3(data)

    def test_group_id_uses_its_branch_combination(self):
        data = load_fixture()
        data['branch_dynamics']['groups'][0]['group_id'] = 'group:trine:wood_1'
        with self.assertRaisesRegex(ValueError, '그룹 ID'):
            validate_branch_dynamics_v3(data)


if __name__ == '__main__':
    unittest.main()
