"""v3 기초 조립기는 실제 v2 계산 결과만 옮긴다."""

import unittest
import json
from pathlib import Path

from schemas.branch_dynamics_v3 import (
    BranchDynamicsV3Response, BranchGroupV3, BranchPairV3,
    BranchStrengthsV3, ChartContextV3, MetaV3,
)
from services.branch_dynamics import analyze_branch_dynamics
from services.branch_dynamics_v3_assembler import (
    assemble_branch_dynamics_v3_foundation, assemble_branch_pairs_v3,
    assemble_branch_groups_v3, assemble_interaction_resolution_v3,
)
from services.interaction_matrix import build_interaction_matrix
from services.relation_rules import V3_RULE_VERSION


def assemble(stems, branches):
    matrix = build_interaction_matrix(stems, branches, stems[2])['matrix']
    source = analyze_branch_dynamics(stems, branches, matrix)
    return source, assemble_branch_dynamics_v3_foundation(stems, branches, source)


class BranchDynamicsV3AssemblerTests(unittest.TestCase):
    @staticmethod
    def relation(pairs, pair_id, relation_type):
        pair = next(item for item in pairs if item['pair_id'] == pair_id)
        return next(item for item in pair['relations'] if item['type'] == relation_type)

    def test_all_pillars_use_calculated_strength_and_source_rule_version(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, result = assemble(stems, branches)
        MetaV3.model_validate(result['meta'])
        ChartContextV3.model_validate(result['chart_context'])
        BranchStrengthsV3.model_validate(result['branch_strengths'])
        self.assertEqual(result['meta']['rule_version'],
                         f"{source['rule_version']}+{V3_RULE_VERSION}")
        self.assertEqual(set(result), {'meta', 'chart_context', 'branch_strengths'})
        for index, pillar in enumerate(('year', 'month', 'day', 'hour')):
            with self.subTest(pillar=pillar):
                strength = result['branch_strengths'][pillar]
                original = source['branch_strengths'][pillar]
                self.assertEqual(strength['branch'], branches[index])
                self.assertEqual(strength['base_power'], original['base_power'])
                self.assertEqual(strength['after_stem_power'], original['after_stem_power'])
                self.assertEqual(strength['effective_power'], original['effective_power'])
                self.assertEqual(strength['strength_evidence']['season']['factor'],
                                 original['components']['seasonal_factor'])
                self.assertEqual(strength['strength_evidence']['season']['month_branch'], '卯')
                self.assertTrue(all(item['effective_contribution'] is None
                                    for item in strength['strength_evidence']['hidden_stems']))
                trace = strength['calculation_trace']
                self.assertIsNone(trace['base_formula_id'])
                self.assertEqual(trace['validation_status'], 'unverified')
                self.assertEqual(trace['applied_adjustments'][0]['power_delta'],
                                 original['stem_branch_relation']['adjustment'])

    def test_month_stem_support_pressure_and_outflow_are_preserved(self):
        branches = list('子卯午寅')
        powers = {}
        for stem, relation, effect in [
            ('癸', 'stem_generates_branch', 'support'),
            ('辛', 'stem_controls_branch', 'pressure'),
            ('丁', 'branch_generates_stem', 'outflow'),
        ]:
            with self.subTest(month_stem=stem):
                source, result = assemble(['甲', stem, '甲', '甲'], branches)
                month = result['branch_strengths']['month']
                evidence = month['strength_evidence']['same_pillar_stem']
                self.assertEqual((evidence['relation'], evidence['effect']), (relation, effect))
                self.assertEqual(evidence['adjustment'],
                                 source['branch_strengths']['month']['stem_branch_relation']['adjustment'])
                self.assertEqual(month['base_power'], 2.4)
                powers[stem] = month['after_stem_power']
        self.assertGreater(powers['癸'], powers['丁'])
        self.assertGreater(powers['丁'], powers['辛'])

    def test_rejects_strengths_from_another_chart(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, _ = assemble(stems, branches)
        with self.assertRaisesRegex(ValueError, '원국과 입력 원국이 다릅니다'):
            assemble_branch_dynamics_v3_foundation(stems, list('亥午未亥'), source)

    def test_six_pairs_keep_element_direction_and_completed_trine_halves(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        self.assertEqual(len(pairs), 6)
        self.assertTrue(all(BranchPairV3.model_validate(pair) for pair in pairs))
        self.assertEqual([(pair['pair_id'], pair['pillar_distance']) for pair in pairs], [
            ('year:month', 1), ('year:day', 2), ('year:hour', 3),
            ('month:day', 1), ('month:hour', 2), ('day:hour', 1),
        ])
        generate = self.relation(pairs, 'year:month', 'generate')
        self.assertEqual(generate['relation_id'], 'branch:generate:year:month')
        self.assertEqual(generate['direction'], {'from_pillar': 'year', 'to_pillar': 'month'})
        self.assertEqual(generate['evidence'][0]['basis'], '水生木')
        self.assertEqual(generate['calculation_status'], 'potential_calculated')
        self.assertEqual(len(generate['metrics']['directional_effects']), 1)
        self.assertEqual(generate['metrics']['directional_effects'][0]['from_pillar'], 'year')
        self.assertIsNone(generate['metrics']['directional_effects'][0]['applied_power_delta'])
        control = self.relation(pairs, 'year:day', 'control')
        self.assertEqual(control['direction'], {'from_pillar': 'day', 'to_pillar': 'year'})
        self.assertEqual(control['evidence'][0]['basis'], '土克水')
        self.assertEqual(control['bin_zhu_context']['direction'], 'host_to_guest')
        self.assertEqual((control['metrics']['directional_effects'][0]['acting_domain'],
                          control['metrics']['directional_effects'][0]['receiving_domain']),
                         ('host', 'guest'))
        self.assertIn('branch:half_combine:year:month',
                      generate['interaction_context']['coexisting_interaction_ids'])
        for pair_id in ('year:month', 'month:day', 'month:hour'):
            half = self.relation(pairs, pair_id, 'half_combine')
            self.assertEqual(half['activation_status'], 'candidate_only')
            self.assertEqual(half['effect_status'], 'structural_only')
            self.assertEqual(half['calculation_status'], 'not_applicable')
            self.assertIsNone(half['metrics'])
        self.assertEqual(self.relation(pairs, 'year:hour', 'same_branch')['effect_status'],
                         'structural_only')
        punishment = self.relation(pairs, 'year:hour', 'self_punishment')
        self.assertEqual(punishment['activation_status'], 'candidate_only')
        self.assertIsNone(punishment['force_dominance'])

    def test_adjacent_self_punishment_is_active_without_invented_power(self):
        branches = list('午午午子')
        source, _ = assemble(list('甲甲甲甲'), branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        for pair_id in ('year:month', 'month:day'):
            relation = self.relation(pairs, pair_id, 'self_punishment')
            self.assertEqual(relation['activation_status'], 'active')
            self.assertEqual(relation['calculation_status'], 'pending')
            self.assertIsNone(relation['metrics'])
            self.assertIsNone(relation['force_dominance'])
            self.assertEqual(relation['status_reason'], 'adjacent_self_punishment')
            self.assertIn('branch:adjacent_self_punishment_active_v1',
                          [item['rule_id'] for item in relation['evidence']])
        distant = self.relation(pairs, 'year:day', 'self_punishment')
        self.assertEqual(distant['activation_status'], 'candidate_only')
        self.assertEqual(distant['status_reason'],
                         'nonadjacent_self_punishment_candidate')
        resolution = assemble_interaction_resolution_v3(pairs, [])
        self.assertIn('branch:self_punishment:year:month',
                      resolution['active_interaction_ids'])
        self.assertIn('branch:self_punishment:month:day',
                      resolution['active_interaction_ids'])
        self.assertIn('branch:self_punishment:year:day',
                      resolution['unresolved_interaction_ids'])

    def test_active_clash_break_and_element_suppression_stay_separate(self):
        stems, branches = list('甲甲甲甲'), list('子卯午寅')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        self.assertEqual(self.relation(pairs, 'year:month', 'break')['label_ko'], '파')
        self.assertFalse(any(item['type'] == 'punishment'
                             for item in next(pair for pair in pairs
                                              if pair['pair_id'] == 'year:month')['relations']))
        generation = self.relation(pairs, 'year:month', 'generate')
        self.assertEqual(generation['activation_status'], 'suppressed')
        self.assertEqual(generation['calculation_status'], 'resolved')
        self.assertGreater(generation['metrics']['directional_effects'][0]['interaction_intensity'], 0)
        self.assertEqual(generation['metrics']['directional_effects'][0]['applied_power_delta'], 0)
        self.assertIn('branch:active_pair_structure_overrides_element_v1',
                      [item['rule_id'] for item in generation['evidence']])
        self.assertEqual(self.relation(pairs, 'month:day', 'break')['label_ko'], '파')
        self.assertEqual(self.relation(pairs, 'year:day', 'clash')['calculation_status'],
                         'potential_calculated')
        self.assertEqual(self.relation(pairs, 'year:day', 'control')['calculation_status'],
                         'resolved')

    def test_conditional_combination_and_broken_trine_half_remain_unresolved(self):
        stems = list('甲甲甲甲')
        conditional_branches = list('申寅亥子')
        conditional_source, _ = assemble(stems, conditional_branches)
        conditional = self.relation(
            assemble_branch_pairs_v3(conditional_branches, conditional_source),
            'month:day', 'combine')
        self.assertEqual(conditional['activation_status'], 'conditional')
        self.assertEqual(conditional['calculation_status'], 'potential_calculated')
        self.assertEqual(len(conditional['metrics']['directional_effects']), 2)
        self.assertTrue(all(item['applied_power_delta'] is None
                            for item in conditional['metrics']['directional_effects']))
        self.assertEqual(conditional['candidate_element'], '木')

        broken_branches = list('巳亥卯未')
        broken_source, _ = assemble(stems, broken_branches)
        half = self.relation(assemble_branch_pairs_v3(broken_branches, broken_source),
                             'day:hour', 'half_combine')
        self.assertEqual(half['activation_status'], 'potential')
        self.assertEqual(half['calculation_status'], 'potential_calculated')
        self.assertIsNone(half['effect_status'])

    def test_wu_you_break_and_wu_wei_earth_combination(self):
        stems, branches = list('甲甲甲甲'), list('午辰酉未')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        self.assertEqual(self.relation(pairs, 'year:day', 'break')['relation_id'],
                         'branch:break:year:day')
        self.assertEqual(self.relation(pairs, 'year:hour', 'combine')['candidate_element'],
                         '土')

    def test_cheon_is_pierce_in_v3(self):
        stems, branches = list('甲甲甲甲'), list('寅巳申未')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        relation = self.relation(pairs, 'year:month', 'pierce')
        self.assertEqual(relation['label_ko'], '천')
        self.assertEqual(relation['relation_id'], 'branch:pierce:year:month')
        self.assertEqual(relation['calculation_status'], 'potential_calculated')

    def test_month_stem_changes_clash_potential_without_reversing_control(self):
        branches = list('子午辰寅')
        supported_source, _ = assemble(list('甲甲甲甲'), branches)
        pressured_source, _ = assemble(list('甲壬甲甲'), branches)
        supported = assemble_branch_pairs_v3(branches, supported_source)
        pressured = assemble_branch_pairs_v3(branches, pressured_source)
        strong_clash = self.relation(supported, 'year:month', 'clash')
        weak_clash = self.relation(pressured, 'year:month', 'clash')
        strong = strong_clash['metrics']['directional_effects']
        weak = weak_clash['metrics']['directional_effects']
        self.assertEqual([(item['from_pillar'], item['to_pillar']) for item in strong],
                         [('year', 'month'), ('month', 'year')])
        self.assertGreater(strong[1]['source_capacity'], weak[1]['source_capacity'])
        self.assertGreater(strong[1]['interaction_intensity'],
                           weak[1]['interaction_intensity'])
        self.assertEqual(strong[0]['interaction_intensity'], weak[0]['interaction_intensity'])
        self.assertEqual(strong[1]['interaction_intensity'], round(
            strong[1]['source_capacity'] * strong[1]['distance_weight'] *
            strong[1]['coefficient'], 4))
        self.assertEqual(strong[1]['target_exposure'], round(
            strong[1]['interaction_intensity'] * strong[1]['source_capacity'] /
            (strong[1]['source_capacity'] + strong[0]['source_capacity']), 4))
        self.assertEqual(strong_clash['force_dominance'], 'month')
        control = self.relation(supported, 'year:month', 'control')
        self.assertEqual(control['direction'], {'from_pillar': 'year', 'to_pillar': 'month'})
        self.assertEqual(len(control['metrics']['directional_effects']), 1)
        self.assertEqual(control['metrics']['directional_effects'][0]['from_pillar'], 'year')

    def test_conditional_potential_is_not_treated_as_applied_zero(self):
        stems, branches = list('甲甲甲甲'), list('申寅亥子')
        source, _ = assemble(stems, branches)
        conditional = self.relation(assemble_branch_pairs_v3(branches, source),
                                    'month:day', 'combine')
        self.assertEqual(conditional['activation_status'], 'conditional')
        self.assertTrue(any(item['interaction_intensity'] > 0
                            for item in conditional['metrics']['directional_effects']))
        self.assertTrue(all(item['applied_power_delta'] is None
                            for item in conditional['metrics']['directional_effects']))

    def test_distant_break_preserves_each_v2_potential_direction(self):
        stems, branches = list('甲甲甲甲'), list('午辰酉寅')
        source, _ = assemble(stems, branches)
        original_pair = next(pair for pair in source['pairwise']
                             if pair['pair_id'] == 'year:day')
        original = next(item for item in original_pair['relations'] if item['type'] == '파(破)')
        pair = assemble_branch_pairs_v3(branches, source)
        effects = self.relation(pair, 'year:day', 'break')['metrics']['directional_effects']
        self.assertEqual(len(effects), 2)
        for effect in effects:
            direction = f"{effect['from_pillar']}_to_{effect['to_pillar']}"
            self.assertEqual(effect['distance_weight'], 0.7)
            self.assertEqual(effect['interaction_intensity'], original['force'][direction])
            self.assertIsNone(effect['applied_power_delta'])

    def test_repeated_trine_forms_one_group_and_reuses_structural_pair(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, foundation = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        groups = assemble_branch_groups_v3(branches, source, pairs)
        self.assertEqual(len(groups), 1)
        group = BranchGroupV3.model_validate(groups[0]).model_dump()
        self.assertEqual(group['group_id'], 'group:trine:hai_mao_wei')
        self.assertEqual(group['group_power_status'], 'not_scored')
        self.assertIsNone(group['group_power'])
        self.assertEqual(group['condition_evidence']['duplicate_components'], ['亥'])
        self.assertEqual(len(group['formation_candidates']), 2)
        self.assertEqual(group['overlap']['shared_pillars'], ['month', 'day'])
        self.assertEqual(group['overlap']['counting_policy'], 'evaluate_as_one_network')
        self.assertIsNone(group['overlap']['dominant_formation_id'])
        shared = 'branch:half_combine:month:day'
        self.assertTrue(all(shared in [component['relation_id'] for component in
                                       formation['component_pairs']]
                            for formation in group['formation_candidates']))
        self.assertEqual(group['formation_candidates'][0]['direction_candidates'][0], {
            'from_pillar': 'year', 'to_pillar': 'month',
            'pillar_distance': 1, 'status': 'candidate_only',
        })

        fixture = Path(__file__).resolve().parent / 'fixtures' / 'branch_dynamics_v3.json'
        response = json.loads(fixture.read_text())
        response['meta'] = foundation['meta']
        response['chart_context'] = foundation['chart_context']
        response['branch_dynamics'] = {
            'branch_strengths': foundation['branch_strengths'],
            'pairwise': pairs, 'groups': groups,
        }
        response['interaction_resolution'] = assemble_interaction_resolution_v3(pairs, groups)
        BranchDynamicsV3Response.model_validate(response)

    def test_group_suppression_does_not_erase_surviving_half(self):
        stems, branches = list('甲甲甲甲'), list('巳亥卯未')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        group = assemble_branch_groups_v3(branches, source, pairs)[0]
        self.assertEqual(group['formation_status'], 'suppressed')
        self.assertEqual(group['status_reasons'], ['adjacent_birth_clash'])
        self.assertEqual(group['formation_candidates'][0]['component_pairs'], [])
        self.assertEqual(self.relation(pairs, 'day:hour', 'half_combine')['calculation_status'],
                         'potential_calculated')
        resolution = assemble_interaction_resolution_v3(pairs, [group])
        self.assertIn(group['group_id'], resolution['suppressed_interaction_ids'])
        self.assertIn('branch:half_combine:day:hour',
                      resolution['unresolved_interaction_ids'])

    def test_square_and_triple_punishment_have_no_invented_group_power(self):
        stems = list('甲甲甲甲')
        for branches, expected_type in [(list('巳午未寅'), 'square'),
                                        (list('寅巳申亥'), 'triple_punishment')]:
            with self.subTest(branches=branches):
                source, _ = assemble(stems, branches)
                pairs = assemble_branch_pairs_v3(branches, source)
                group = assemble_branch_groups_v3(branches, source, pairs)[0]
                self.assertEqual(group['type'], expected_type)
                self.assertIsNone(group['group_power'])
                self.assertEqual(group['group_power_status'], 'not_scored')
                self.assertEqual(len(group['formation_candidates']), 1)
        self.assertEqual(group['formation_candidates'][0]['direction_candidates'], [])

    def test_distant_triple_punishment_is_active_alongside_pair_relations(self):
        branches = list('寅巳子申')
        source, _ = assemble(list('甲甲甲甲'), branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        groups = assemble_branch_groups_v3(branches, source, pairs)
        group = next(item for item in groups if item['type'] == 'triple_punishment')
        self.assertEqual(group['formation_status'], 'active')
        self.assertIsNone(group['group_power'])
        self.assertEqual(group['group_power_status'], 'not_scored')
        self.assertEqual(group['formation_candidates'][0]['pillars'],
                         ['year', 'month', 'hour'])
        self.assertIn('branch:triple_punishment_presence_active_v1',
                      group['evidence_rule_ids'])
        resolution = assemble_interaction_resolution_v3(pairs, groups)
        self.assertIn(group['group_id'], resolution['active_interaction_ids'])
        for pair_id, kind in (('year:month', 'pierce'),
                              ('year:hour', 'clash'),
                              ('month:hour', 'combine')):
            relation = self.relation(pairs, pair_id, kind)
            self.assertEqual(relation['activation_status'], 'active')
            self.assertIn(relation['relation_id'], resolution['active_interaction_ids'])

    def test_missing_structural_half_reference_is_rejected(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        pair = next(item for item in pairs if item['pair_id'] == 'month:day')
        pair['relations'] = [relation for relation in pair['relations']
                             if relation['type'] != 'half_combine']
        with self.assertRaisesRegex(ValueError, '구조 전용 반합'):
            assemble_branch_groups_v3(branches, source, pairs)

    def test_resolution_separates_structural_refs_and_tracks_all_candidates(self):
        stems, branches = list('己丁辛己'), list('亥卯未亥')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        groups = assemble_branch_groups_v3(branches, source, pairs)
        resolution = assemble_interaction_resolution_v3(pairs, groups)
        self.assertEqual(resolution['status'], 'unresolved')
        self.assertEqual(resolution['active_interaction_ids'], [])
        self.assertEqual(resolution['suppressed_interaction_ids'], [])
        candidates = {
            relation['relation_id'] for pair in pairs for relation in pair['relations']
            if relation['effect_status'] != 'structural_only'
        } | {group['group_id'] for group in groups}
        self.assertEqual(set(resolution['unresolved_interaction_ids']), candidates)
        case = next(item for item in resolution['resolution_cases']
                    if item['case_id'] == 'resolve:month:day')
        self.assertEqual(case['interaction_ids'], [
            'branch:control:month:day', 'group:trine:hai_mao_wei',
        ])
        self.assertEqual(case['structural_context_relation_ids'],
                         ['branch:half_combine:month:day'])
        overlap = next(item for item in resolution['resolution_cases']
                       if item['case_id'] == 'resolve:group:trine:hai_mao_wei:overlap')
        self.assertEqual(len(overlap['candidate_ids']), 2)
        self.assertEqual(overlap['selected_formation_ids'], [])

    def test_resolution_selects_active_break_and_suppresses_generation(self):
        stems, branches = list('甲甲甲甲'), list('子卯午寅')
        source, _ = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        groups = assemble_branch_groups_v3(branches, source, pairs)
        resolution = assemble_interaction_resolution_v3(pairs, groups)
        self.assertIn('branch:generate:year:month',
                      resolution['suppressed_interaction_ids'])
        self.assertIn('branch:generate:month:day',
                      resolution['suppressed_interaction_ids'])
        self.assertIn('branch:break:year:month',
                      resolution['active_interaction_ids'])
        self.assertIn('branch:clash:year:day',
                      resolution['active_interaction_ids'])
        case = next(item for item in resolution['resolution_cases']
                    if item['case_id'] == 'resolve:year:month')
        self.assertEqual(case['suppressed_interaction_ids'],
                         ['branch:generate:year:month'])
        self.assertEqual(case['selected_interaction_ids'],
                         ['branch:break:year:month'])
        self.assertEqual(case['resolution_status'], 'active')

        conditional_branches = list('申寅亥子')
        conditional_source, _ = assemble(stems, conditional_branches)
        conditional_pairs = assemble_branch_pairs_v3(conditional_branches,
                                                      conditional_source)
        conditional_groups = assemble_branch_groups_v3(
            conditional_branches, conditional_source, conditional_pairs)
        conditional = assemble_interaction_resolution_v3(conditional_pairs,
                                                          conditional_groups)
        self.assertIn('branch:combine:month:day',
                      conditional['unresolved_interaction_ids'])

    def test_confirmed_pair_structure_suppresses_elemental_action(self):
        examples = [
            ('子午辰寅', '충(沖)', 'clash', 'control'),
            ('寅亥辰子', '육합(六合)', 'combine', 'generate'),
            ('寅巳申未', '천(穿)', 'pierce', 'generate'),
            ('子卯辰寅', '파(破)', 'break', 'generate'),
        ]
        for branch_text, source_type, structure_type, element_type in examples:
            with self.subTest(branches=branch_text):
                branches = list(branch_text)
                source, _ = assemble(list('甲甲甲甲'), branches)
                pair = next(item for item in source['pairwise']
                            if item['pair_id'] == 'year:month')
                structure = next(item for item in pair['relations']
                                 if item['type'] == source_type)
                structure['activation_status'] = 'active'
                pairs = assemble_branch_pairs_v3(branches, source)
                element = self.relation(pairs, 'year:month', element_type)
                self.assertEqual(element['activation_status'], 'suppressed')
                self.assertEqual(element['calculation_status'], 'resolved')
                self.assertEqual(element['status_reason'],
                                 'active_pair_structure_overrides_element')
                self.assertTrue(all(effect['applied_power_delta'] == 0
                                    for effect in element['metrics']['directional_effects']))
                self.assertIn('branch:active_pair_structure_overrides_element_v1',
                              [item['rule_id'] for item in element['evidence']])
                resolution = assemble_interaction_resolution_v3(pairs, [])
                self.assertIn(f'branch:{structure_type}:year:month',
                              resolution['active_interaction_ids'])
                self.assertIn(element['relation_id'],
                              resolution['suppressed_interaction_ids'])

    def test_detected_combine_and_pierce_activate_without_manual_override(self):
        for branch_text, structure_type, element_type in (
            ('寅亥辰子', 'combine', 'generate'),
            ('寅巳申未', 'pierce', 'generate'),
        ):
            with self.subTest(branches=branch_text):
                branches = list(branch_text)
                source, _ = assemble(list('甲甲甲甲'), branches)
                pairs = assemble_branch_pairs_v3(branches, source)
                structure = self.relation(pairs, 'year:month', structure_type)
                element = self.relation(pairs, 'year:month', element_type)
                self.assertEqual(structure['activation_status'], 'active')
                self.assertIn('branch:pair_presence_active_v1',
                              [item['rule_id'] for item in structure['evidence']])
                self.assertEqual(element['activation_status'], 'suppressed')
                self.assertTrue(all(effect['applied_power_delta'] == 0
                                    for effect in element['metrics']['directional_effects']))
                resolution = assemble_interaction_resolution_v3(pairs, [])
                self.assertIn(structure['relation_id'], resolution['active_interaction_ids'])
                self.assertIn(element['relation_id'], resolution['suppressed_interaction_ids'])

    def test_active_clash_suppresses_elemental_action(self):
        stems, branches = list('甲甲甲甲'), list('子午辰寅')
        source, foundation = assemble(stems, branches)
        pairs = assemble_branch_pairs_v3(branches, source)
        clash = self.relation(pairs, 'year:month', 'clash')
        self.assertEqual(clash['activation_status'], 'active')
        self.assertIn('branch:pair_presence_active_v1',
                      [item['rule_id'] for item in clash['evidence']])
        self.assertEqual(self.relation(pairs, 'year:month', 'control')['activation_status'],
                         'suppressed')
        self.assertEqual(self.relation(pairs, 'year:month', 'control')
                         ['metrics']['directional_effects'][0]['applied_power_delta'], 0)

        fixture = Path(__file__).resolve().parent / 'fixtures' / 'branch_dynamics_v3.json'
        response = json.loads(fixture.read_text())
        response['meta'] = foundation['meta']
        response['chart_context'] = foundation['chart_context']
        response['branch_dynamics'] = {
            'branch_strengths': foundation['branch_strengths'],
            'pairwise': pairs,
            'groups': assemble_branch_groups_v3(branches, source, pairs),
        }
        response['interaction_resolution'] = assemble_interaction_resolution_v3(
            pairs, response['branch_dynamics']['groups'])
        response['work_dynamics']['candidate_paths'] = []
        response['llm_interpretation_payload']['structural_facts'] = []
        response['llm_interpretation_payload']['unresolved_mechanisms'] = []
        BranchDynamicsV3Response.model_validate(response)


if __name__ == '__main__':
    unittest.main()
