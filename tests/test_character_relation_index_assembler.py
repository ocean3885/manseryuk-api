"""기존 관계 생산 경로를 8글자 조회 계약에 연결한 결과를 검증한다."""

import copy
from itertools import combinations_with_replacement
import unittest

from schemas.character_relation_index import CharacterRelationIndex
from services.analysis import analyze_palja_integrated
from services.branch_dynamics import analyze_branch_dynamics
from services.character_relation_index import assemble_character_relation_index
from services.interaction_matrix import build_interaction_matrix
from services.relation_rules import (
    JAHAB_MAP, STEM_COMBINATIONS, STEM_CONFLICTS, STEM_RESTRAIN,
    SQUARE_HAPS, THREE_HAPS, THREE_PUNISHMENTS,
)


def inputs(stem_text, branch_text):
    stems, branches = list(stem_text), list(branch_text)
    interactions = build_interaction_matrix(stems, branches, stems[2])
    analysis = analyze_palja_integrated(stems, branches)
    dynamics = analyze_branch_dynamics(stems, branches, interactions['matrix'])
    return stems, branches, interactions, analysis, dynamics


def assemble(*args):
    return assemble_character_relation_index(*inputs(*args))


class CharacterRelationAssemblerTests(unittest.TestCase):
    def test_a_keeps_two_ji_targets_and_maps_legacy_branch_ids(self):
        source = inputs('乙己己庚', '巳丑未午')
        before = copy.deepcopy(source)
        result = assemble_character_relation_index(*source)
        self.assertEqual(source, before)
        CharacterRelationIndex.model_validate(result)
        relations = {row['relation_id']: row for row in result['relations']}
        self.assertEqual(len(relations), len(result['relations']))
        self.assertEqual({
            'stem:control:year:month', 'stem:control:year:day',
        } & set(relations), {
            'stem:control:year:month', 'stem:control:year:day',
        })
        self.assertEqual(relations['stem:control:year:day']['direction'], {
            'from_character': 'year.stem', 'to_character': 'day.stem',
            'basis': 'elemental',
        })
        self.assertEqual(relations['stem:combine:year:hour']['activation_status'],
                         'detected')
        clash = relations['branch:clash:month:day']
        self.assertEqual(clash['activation_status'], 'active')
        self.assertEqual({ref['system'] for ref in clash['source_refs']},
                         {'interaction_matrix', 'branch_dynamics_v3'})
        self.assertTrue(any(ref['relation_id'] == '지지:충(沖):丑未충:month,day'
                            for ref in clash['source_refs']))
        self.assertEqual(relations['branch:combine:day:hour']['activation_status'],
                         'conditional')
        self.assertEqual(relations['branch:combine:day:hour']['status_reason'],
                         'external_adjacent_clash')
        self.assertEqual(relations['group:square:si_wu_wei']['formation_candidates'],
                         [['year.branch', 'day.branch', 'hour.branch']])
        self.assertTrue(all(f'same_pillar:element:{pillar}' in relations
                            for pillar in ('year', 'month', 'day', 'hour')))
        self.assertFalse(any(row['type'] == 'self_combine'
                             for row in result['relations']))
        from_day = [row for row in result['relations']
                    if row['relation_id'].startswith(
                        'cross_layer:transmission:day:')]
        self.assertEqual([row['relation_id'] for row in from_day], [
            'cross_layer:transmission:day:day',
            'cross_layer:transmission:day:month',
            'cross_layer:transmission:day:year',
        ])
        self.assertEqual(result['characters']['month.stem']['stem_state'][
            'original_status'], '실(實)')
        self.assertEqual(result['characters']['month.stem']['stem_state'][
            'root_score'], 0.2)
        self.assertTrue(result['characters']['month.stem']['stem_state'][
            'has_same_pillar_root'])
        self.assertEqual(result['characters']['month.stem']['stem_state'][
            'current_status'], '실(實)')
        self.assertEqual(result['characters']['month.stem']['stem_state'][
            'external_support_score'], 1.3)
        self.assertEqual(result['characters']['month.stem']['stem_state'][
            'root_scope'], 'same_pillar_only')
        self.assertEqual(result['characters']['year.stem']['stem_state'][
            'original_status'], '허투(虛透)')
        self.assertFalse(result['characters']['year.stem']['stem_state'][
            'has_same_pillar_root'])
        self.assertEqual(result['characters']['year.stem']['stem_state'][
            'external_support_score'], 0.21)

    def test_repeated_and_suppressed_groups_and_ziwu_direction(self):
        for stems, branches in (
            ('己丁辛己', '亥卯未亥'),
            ('甲甲甲甲', '巳亥卯未'),
            ('甲甲甲甲', '寅巳申未'),
            ('甲甲甲甲', '午午辰寅'),
            ('甲甲甲甲', '子午辰寅'),
        ):
            with self.subTest(branches=branches):
                result = assemble(stems, branches)
                CharacterRelationIndex.model_validate(result)
                if branches == '亥卯未亥':
                    trine = next(row for row in result['relations']
                                 if row['type'] == 'trine')
                    self.assertEqual(len(trine['formation_candidates']), 2)
                    self.assertEqual(len(trine['participants']), 4)
                if branches == '巳亥卯未':
                    self.assertTrue(any(row['type'] == 'trine'
                                        and row['activation_status'] == 'suppressed'
                                        for row in result['relations']))
                if branches == '子午辰寅':
                    clash = next(row for row in result['relations']
                                 if row['relation_id'] == 'branch:clash:year:month')
                    self.assertEqual(clash['direction'], {
                        'from_character': 'year.branch',
                        'to_character': 'month.branch', 'basis': 'rule_fixed',
                    })

    def test_same_pillar_self_combination_carries_actual_condition(self):
        for branches, expected in (
            ('戌未寅子', 'active'),
            ('戌子寅卯', 'conditional'),
            ('戌未辰子', 'suppressed'),
        ):
            with self.subTest(branches=branches):
                result = assemble('丙甲甲甲', branches)
                self_combine = next(row for row in result['relations']
                                    if row['relation_id'] ==
                                    'same_pillar:self_combine:year')
                self.assertEqual(self_combine['activation_status'], expected)
                self.assertEqual(self_combine['candidate_element'], '水')
                self.assertEqual(self_combine['status_reason'] is None,
                                 expected == 'active')

    def test_unrooted_stems_keep_hollow_status_separate_from_transmission(self):
        result = assemble('甲甲甲甲', '申酉戌丑')
        for pillar in ('year', 'month', 'day', 'hour'):
            state = result['characters'][f'{pillar}.stem']['stem_state']
            self.assertEqual(state['root_score'], 0)
            self.assertFalse(state['has_same_pillar_root'])
            self.assertEqual(state['original_status'], '허투(虛透)')
            self.assertEqual(state['current_status'], '허투(虛透)')
            self.assertEqual(state['validation_status'], 'provisional')
        self.assertFalse(any(row['type'] == 'transmission'
                             for row in result['relations']))

    def test_literal_transmission_and_modeled_rooting_are_independent(self):
        cases = (
            ('戊甲甲甲', '亥亥亥亥', 4, 0.0, '허투(虛透)', []),
            ('庚甲甲甲', '丑子子子', 0, 0.5, '실(實)', ['year.branch']),
            ('甲甲甲甲', '寅酉酉酉', 1, 1.0, '실(實)', ['year.branch']),
            ('甲甲甲甲', '酉酉酉酉', 0, 0.0, '허투(虛透)', []),
        )
        for stems, branches, link_count, score, status, root_ids in cases:
            with self.subTest(stems=stems, branches=branches):
                index = assemble(stems, branches)
                links = [row for row in index['relations']
                         if row['type'] == 'transmission' and
                         row['direction']['to_character'] == 'year.stem']
                state = index['characters']['year.stem']['stem_state']
                self.assertEqual(len(links), link_count)
                self.assertEqual(state['root_score'], score)
                self.assertEqual(state['original_status'], status)
                self.assertEqual(state['root_branch_ids'], root_ids)
                self.assertEqual(state['has_same_pillar_root'], bool(root_ids))

    def test_mixed_or_changed_source_results_are_rejected(self):
        source = inputs('乙己己庚', '巳丑未午')
        changed = copy.deepcopy(source)
        target = next(row for row in changed[2]['matrix']
                      if row['type'] == '충(沖)' and row['participants'] ==
                      ['month', 'day'])
        target['activation_status'] = 'potential'
        with self.assertRaisesRegex(ValueError, '성립 상태'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[3]['pillars']['year']['stem']['relations']['restrain'][
            'restrain_to'].pop()
        with self.assertRaisesRegex(ValueError, '천간 극 규칙'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[3]['pillars']['year']['stem']['relations']['restrain'][
            'restrain_to'][0]['with'] = '庚'
        with self.assertRaisesRegex(ValueError, '천간 극 상대'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[3]['pillars']['month']['branch']['char'] = '未'
        with self.assertRaisesRegex(ValueError, '원국이 다릅니다'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[3]['pillars']['month']['branch']['relations']['chungs'] = None
        with self.assertRaisesRegex(ValueError, '글자별 관계 후보'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[3]['pillars']['day']['branch']['transmitted'] = [
            row for row in changed[3]['pillars']['day']['branch']['transmitted']
            if not (row['stem'] == '己' and row['stem_idx'] == 2)
        ]
        with self.assertRaisesRegex(ValueError, '투출 결과'):
            assemble_character_relation_index(*changed)

        changed = copy.deepcopy(source)
        changed[2]['matrix'] = [row for row in changed[2]['matrix']
                                if row['type'] != '방합(方合)']
        with self.assertRaisesRegex(ValueError, '원본 지지 그룹'):
            assemble_character_relation_index(*changed)

    def test_all_branch_pairs_in_both_orders_have_valid_index(self):
        symbols = '子丑寅卯辰巳午未申酉戌亥'
        checked = 0
        for first, second in combinations_with_replacement(symbols, 2):
            for left, right in ((first, second), (second, first)):
                with self.subTest(pair=left + right):
                    result = assemble('甲甲甲甲', left + right + '辰酉')
                    CharacterRelationIndex.model_validate(result)
                    checked += 1
        self.assertEqual(checked, 156)

    def test_all_stem_position_pairs_follow_registered_rule_types(self):
        symbols = '甲乙丙丁戊己庚辛壬癸'
        checked = 0
        for first in symbols:
            for second in symbols:
                with self.subTest(pair=first + second):
                    result = assemble(first + second + '丙丁', '子午辰寅')
                    ids = {row['relation_id'] for row in result['relations']}
                    for kind, exists in (
                        ('combine', ((first, second) in STEM_COMBINATIONS or
                                     (second, first) in STEM_COMBINATIONS)),
                        ('clash', ((first, second) in STEM_CONFLICTS or
                                   (second, first) in STEM_CONFLICTS)),
                        ('control', ((first, second) in STEM_RESTRAIN or
                                     (second, first) in STEM_RESTRAIN)),
                    ):
                        self.assertEqual(f'stem:{kind}:year:month' in ids, exists)
                    checked += 1
        self.assertEqual(checked, 100)

    def test_all_registered_same_pillar_self_combinations_are_preserved(self):
        for (stem, branch), rule in JAHAB_MAP.items():
            with self.subTest(stem=stem, branch=branch):
                result = assemble(stem + '甲甲甲', branch + '卯申酉')
                relation = next(row for row in result['relations']
                                if row['relation_id'] ==
                                'same_pillar:self_combine:year')
                self.assertEqual(relation['candidate_element'], rule['element'])
                self.assertEqual(relation['participants'],
                                 ['year.stem', 'year.branch'])

    def test_all_registered_three_branch_groups_are_preserved(self):
        definitions = (
            [(members, 'trine') for members in THREE_HAPS]
            + [(members, 'square') for members in SQUARE_HAPS]
            + [(members, 'triple_punishment') for members in THREE_PUNISHMENTS]
        )
        for members, kind in definitions:
            with self.subTest(members=members, kind=kind):
                result = assemble('甲甲甲甲', ''.join(members) + '子')
                self.assertTrue(any(row['type'] == kind and
                                    {'year.branch', 'month.branch', 'day.branch'}
                                    <= set(row['participants'])
                                    for row in result['relations']))


if __name__ == '__main__':
    unittest.main()
