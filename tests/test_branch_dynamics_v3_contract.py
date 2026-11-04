"""v3 설계 샘플의 구조·참조·수치 상태 회귀 검사."""

import copy
import json
import re
import unittest
from pathlib import Path

from schemas.branch_dynamics_v3_contract import validate_branch_dynamics_v3
from schemas.branch_dynamics_v3 import BranchDynamicsV3Response
from services.branch_dynamics import analyze_branch_dynamics
from services.branch_dynamics_v3_assembler import (
    assemble_branch_dynamics_v3_foundation, assemble_branch_pairs_v3,
    assemble_branch_groups_v3, assemble_branch_influence_paths_v3,
    assemble_interaction_resolution_v3,
)
from services.interaction_matrix import build_interaction_matrix


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests' / 'fixtures' / 'branch_dynamics_v3.json'
DESIGN = ROOT / 'docs' / 'archive' / 'strength-research' / 'branch_dynamics_v3.json'


def load_fixture():
    return json.loads(FIXTURE.read_text())


def relation(data, relation_id):
    return next(item for pair in data['branch_dynamics']['pairwise']
                for item in pair['relations'] if item['relation_id'] == relation_id)


def ziwu_payload(stem_text='甲甲甲甲', branch_text='子午辰寅'):
    stems, branches = list(stem_text), list(branch_text)
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    foundation = assemble_branch_dynamics_v3_foundation(stems, branches, source)
    pairs = assemble_branch_pairs_v3(branches, source)
    groups = assemble_branch_groups_v3(branches, source, pairs)
    data = load_fixture()
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


class BranchDynamicsV3ContractTests(unittest.TestCase):
    def test_provisional_ziwu_effects_validate_as_one_direction_and_one_self_loss(self):
        for branches in ('子午辰寅', '午子辰寅', '子午午午'):
            with self.subTest(branches=branches):
                data = ziwu_payload(branch_text=branches)
                BranchDynamicsV3Response.model_validate(data)
                validate_branch_dynamics_v3(data)

    def test_provisional_ziwu_rejects_duplicate_loss_and_wrong_direction(self):
        data = ziwu_payload()
        clash = relation(data, 'branch:clash:year:month')
        clash['metrics']['self_effects'].append(copy.deepcopy(
            clash['metrics']['self_effects'][0]))
        with self.assertRaisesRegex(ValueError, '잠정 충 계산'):
            validate_branch_dynamics_v3(data)

        data = ziwu_payload()
        clash = relation(data, 'branch:clash:year:month')
        clash['metrics']['self_effects'][0]['power_delta'] -= 0.0001
        with self.assertRaisesRegex(ValueError, '합계'):
            validate_branch_dynamics_v3(data)

        data = ziwu_payload()
        clash = relation(data, 'branch:clash:year:month')
        clash['direction'] = {'from_pillar': 'month', 'to_pillar': 'year'}
        with self.assertRaisesRegex(ValueError, '일차 방향'):
            validate_branch_dynamics_v3(data)

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

    def test_post_effect_power_cannot_disguise_missing_calculation_as_zero(self):
        data = load_fixture()
        strength = data['branch_dynamics']['branch_strengths']['month']
        strength['post_effect_power'] = 0
        with self.assertRaisesRegex(ValueError, '미완성 작용 후 세력'):
            validate_branch_dynamics_v3(data)

        data = load_fixture()
        strength = data['branch_dynamics']['branch_strengths']['month']
        strength['post_effect_status'] = 'resolved'
        with self.assertRaisesRegex(ValueError, '유한한 0 이상의 숫자'):
            validate_branch_dynamics_v3(data)

    def test_influence_paths_are_one_indexed_view_of_surroundings(self):
        data = ziwu_payload()
        dynamics = data['branch_dynamics']
        background = [path for path in dynamics['influence_paths']
                      if path['stage'] == 'pre_relation_background']
        self.assertEqual(len(background), 12)
        for pillar, strength in dynamics['branch_strengths'].items():
            self.assertEqual(set(strength['influence_path_ids']), {
                path['path_id'] for path in dynamics['influence_paths']
                if path['target']['pillar'] == pillar
            })
        validate_branch_dynamics_v3(data)

        changed = ziwu_payload()
        path = next(path for path in changed['branch_dynamics']['influence_paths']
                    if path['accounting_decision'] == 'include')
        path['quantity']['value'] += 0.1
        with self.assertRaisesRegex(ValueError, '계상값이 다릅니다'):
            validate_branch_dynamics_v3(changed)

        changed = ziwu_payload()
        changed['branch_dynamics']['branch_strengths']['year'][
            'influence_path_ids'].pop()
        with self.assertRaisesRegex(ValueError, '대상별 참조'):
            validate_branch_dynamics_v3(changed)

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
