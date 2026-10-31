"""단일 관계 규칙 모듈을 탐지기와 자합 판정기가 함께 사용하는지 확인."""

import unittest

from services.branch_relations import (check_break, check_six_haps, check_punishment, check_three_punishment,
                                      check_gong_hap, check_hidden_stem_hap)
from services.bin_zhu import analyze_bin_zhu_dynamics
from services.branch_dynamics import analyze_branch_dynamics
from services.interaction_matrix import build_interaction_matrix
from services.relation_rules import (BREAKS, SIX_HAPS, JAHAB_MAP, STEM_COMBINATIONS,
                                    THREE_PUNISHMENTS, GONG_HAPS, HIDDEN_STEM_HAPS,
                                    THREE_HAPS, THREE_HAPS_KING, SQUARE_HAPS,
                                    THREE_HAP_CONDITIONS, GROUP_ACTION_RULES,
                                    get_group_action_rule)
from services.relations import check_jahab
from services.stem_relations import check_stem_combination


class RelationRulesTests(unittest.TestCase):
    def test_group_action_rules_cover_every_triple_without_forced_square_direction(self):
        expected = ({('삼합(三合)', frozenset(members)) for members in THREE_HAPS} |
                    {('방합(方合)', frozenset(members)) for members in SQUARE_HAPS})
        self.assertEqual(set(GROUP_ACTION_RULES), expected)
        for (kind, members), rule in GROUP_ACTION_RULES.items():
            with self.subTest(kind=kind, members=members):
                self.assertIs(get_group_action_rule(kind, tuple(reversed(tuple(members)))),
                              rule)
                self.assertEqual(rule['pair_overlap_policy'],
                                 'preserve_pair_do_not_sum_group_force')
                if kind == '삼합(三合)':
                    self.assertEqual(rule['direction_candidates'],
                                     (('birth', 'center'), ('storage', 'center')))
                    self.assertIn(rule['center_branch'], members)
                    self.assertEqual(rule['direction_status'], 'candidate_only')
                else:
                    self.assertEqual(rule['direction_candidates'], ())
                    self.assertEqual(rule['direction_status'], 'undetermined')
                    self.assertIsNone(rule['center_branch'])

    def test_wu_wei_six_hap_uses_earth_candidate(self):
        branches = list('午未申亥')
        self.assertEqual(SIX_HAPS[('午', '未')], '土')
        self.assertEqual(check_six_haps('午', 0, branches, '甲')[0]['element'], '土')
        result = build_interaction_matrix(list('甲甲甲甲'), branches, '甲')
        pair = next(r for r in result['matrix']
                    if r['type'] == '육합(六合)' and
                    r['participants'] == ['year', 'month'])
        self.assertEqual(pair['candidate_element'], '土')
        self.assertIsNone(pair['transformed_element'])

    def test_six_hap_clash_position_changes_activation_and_force(self):
        for branches, status, reason, expected_score in (
            ('子午丑寅', 'suppressed', 'intervening_adjacent_clash', 0.0),
            ('午子丑寅', 'conditional', 'external_adjacent_clash', 0.0),
            ('子丑午寅', 'active', None, 1.5),
        ):
            with self.subTest(branches=branches):
                result = build_interaction_matrix(list('甲甲甲甲'), list(branches), '甲')
                item = next(r for r in result['matrix'] if r['type'] == '육합(六合)')
                self.assertEqual(item['activation_status'], status)
                self.assertEqual(item['status_reasons'], [reason] if reason else [])
                self.assertEqual(item['score'], expected_score)
                self.assertEqual(item['candidate_element'], '土')
                self.assertIsNone(item['transformed_element'])
                dynamics = analyze_branch_dynamics(
                    list('甲甲甲甲'), list(branches), result['matrix'])
                effect = next(r for p in dynamics['pairwise'] for r in p['relations']
                              if r['relation_id'] == item['relation_id'])
                self.assertEqual(effect['activation_status'], status)
                self.assertEqual(effect['status_reason'], reason or
                                 'combination_candidate_not_transformation')
                self.assertEqual(effect['directional_mechanisms'][item['participants'][0]],
                                 'bound_water')
                self.assertEqual(effect['directional_mechanisms'][item['participants'][1]],
                                 'closes_hidden_metal')
                self.assertEqual(all(force == 0 for force in effect['force'].values()),
                                 status != 'active')

    def test_each_six_hap_exposes_direction_and_hidden_stem_candidates(self):
        cases = (
            ('子', '丑', '土', '극', 'month', [('month', '辛', 'closure')]),
            ('寅', '亥', '木', '생', 'month', [('year', '丙', 'injury')]),
            ('卯', '戌', '火', '극', 'year', [('month', '丁', 'closure')]),
            ('辰', '酉', '金', '생', 'year', [('year', '癸', 'closure'),
                                         ('year', '乙', 'injury')]),
            ('巳', '申', '水', '극', 'year', [('year', '丙', 'injury')]),
            ('午', '未', '土', '생', 'year', [('month', '乙', 'closure')]),
        )
        for first, second, element, secondary_type, source, hidden in cases:
            with self.subTest(pair=first + second):
                stems = list('甲甲甲甲')
                branches = [first, second, '子', '丑']
                matrix = build_interaction_matrix(stems, branches, '甲')['matrix']
                candidate = next(r for r in matrix
                                 if r['type'] == '육합(六合)' and
                                 r['participants'] == ['year', 'month'])
                self.assertEqual(candidate['candidate_element'], element)
                self.assertIsNone(candidate['transformed_element'])
                self.assertEqual(candidate['activation_status'], 'active')
                self.assertEqual([(h['pillar'], h['stem'], h['effect'])
                                  for h in candidate['candidate_hidden_stem_effects']], hidden)
                self.assertTrue(all(h['activation_status'] == 'candidate_only'
                                    for h in candidate['candidate_hidden_stem_effects']))
                dynamics = analyze_branch_dynamics(stems, branches, matrix)
                relations = next(p['relations'] for p in dynamics['pairwise']
                                 if p['pair_id'] == 'year:month')
                combination = next(r for r in relations if r['type'] == '육합(六合)')
                secondary = next(r for r in relations if r['type'] == secondary_type)
                self.assertEqual(combination['rule_id'], f'branch:{first}{second}')
                self.assertEqual(combination['candidate_hidden_stem_effects'],
                                 candidate['candidate_hidden_stem_effects'])
                self.assertNotIn('generic', combination['directional_mechanisms'].values())
                self.assertNotIn('generic', secondary['directional_mechanisms'].values())
                target = 'month' if source == 'year' else 'year'
                self.assertEqual(secondary['activation_status'], 'suppressed')
                self.assertEqual(secondary['force'][f'{source}_to_{target}'], 0)
                self.assertEqual(secondary['force'][f'{target}_to_{source}'], 0)

    def test_zi_mao_is_break_without_punishment(self):
        branches = list('子卯辰寅')
        punishments = check_punishment('子', 0, branches, '甲')
        self.assertEqual(punishments, [])
        result = build_interaction_matrix(list('甲甲甲甲'), branches, '甲')
        pair_items = [r for r in result['matrix']
                      if r['participants'] == ['year', 'month']]
        self.assertEqual({r['type'] for r in pair_items}, {'파(破)'})
        self.assertTrue(all(item['score'] > 0.0 for item in pair_items))
        dynamics = analyze_branch_dynamics(list('甲甲甲甲'), branches, result['matrix'])
        pair = next(p for p in dynamics['pairwise'] if p['pair_id'] == 'year:month')
        self.assertEqual(pair['primary_relation'], '파(破)')
        self.assertFalse(any(r['type'] == '형(刑)' for r in pair['relations']))
        self.assertTrue(any(r['type'] == '파(破)' for r in pair['relations']))

    def test_three_hap_middle_conditions_control_group_score(self):
        self.assertEqual(THREE_HAP_CONDITIONS['duplicate_middle'], 'conditional')
        self.assertEqual(THREE_HAP_CONDITIONS['adjacent_middle_clash'], 'suppressed')
        opponents = {'午': '子', '卯': '酉', '子': '午', '酉': '卯'}
        for triple, element in THREE_HAPS.items():
            with self.subTest(triple=triple):
                middle = THREE_HAPS_KING[element][0]
                wings = [branch for branch in triple if branch != middle]
                for branches, expected_status, expected_reason, expected_score in (
                    (wings + [middle, opponents[middle]], 'suppressed',
                     'adjacent_middle_clash', 0.0),
                    ([wings[0], middle, middle, wings[1]], 'conditional',
                     'duplicate_middle', 0.0),
                    ([wings[0], middle, wings[1], opponents[middle]], 'potential',
                     None, 3.0),
                ):
                    result = build_interaction_matrix(
                        list('甲甲甲甲'), branches, '甲')
                    group = next(r for r in result['matrix']
                                 if r['type'] == '삼합(三合)' and element in r['name'])
                    self.assertEqual(group['activation_status'], expected_status)
                    self.assertEqual(group['score'], expected_score)
                    self.assertEqual(group['status_reasons'],
                                     [expected_reason] if expected_reason else [])
                    if expected_reason == 'duplicate_middle':
                        self.assertEqual(group['condition_evidence']['middle_pillars'],
                                         ['month', 'day'])
                    elif expected_reason == 'adjacent_middle_clash':
                        self.assertEqual(group['condition_evidence']['adjacent_clashes'],
                                         [{'middle_pillar': 'day',
                                           'clashing_pillar': 'hour'}])
                    dynamics = analyze_branch_dynamics(
                        list('甲甲甲甲'), branches, result['matrix'])
                    matched = next(g for g in dynamics['groups']
                                   if g['relation_id'] == group['relation_id'])
                    self.assertEqual(matched['activation_status'], expected_status)
                    if expected_score == 0:
                        self.assertEqual(result['harmony_score'], 0.0)
                        self.assertFalse(any(r['type'] == '반합(半合)'
                                             for r in result['matrix']))
                        bin_zhu = analyze_bin_zhu_dynamics(
                            list('甲甲甲甲'), branches, '甲', result['matrix'])
                        connection = next(g for g in bin_zhu['group_connections']
                                          if g['relation_id'] == group['relation_id'])
                        self.assertEqual(connection['cohesion_score'], 0.0)

    def test_three_hap_wing_clash_preserves_only_surviving_half(self):
        opponents = {'寅': '申', '戌': '辰', '亥': '巳', '未': '丑',
                     '申': '寅', '辰': '戌', '巳': '亥', '丑': '未'}
        for birth, middle, tomb in THREE_HAPS:
            for branches, reason, pair, clashed, score in (
                ([opponents[birth], birth, middle, tomb],
                 'adjacent_birth_clash', ['day', 'hour'], 'month', 1.1),
                ([birth, middle, tomb, opponents[tomb]],
                 'adjacent_tomb_clash', ['year', 'month'], 'day', 1.3),
            ):
                with self.subTest(branches=''.join(branches)):
                    result = build_interaction_matrix(
                        list('甲甲甲甲'), branches, '甲')
                    group = next(r for r in result['matrix']
                                 if r['type'] == '삼합(三合)')
                    half = [r for r in result['matrix']
                            if r['type'] == '반합(半合)']
                    self.assertEqual(group['activation_status'], 'suppressed')
                    self.assertEqual(group['status_reasons'], [reason])
                    self.assertEqual(group['score'], 0.0)
                    self.assertEqual(len(half), 1)
                    self.assertEqual(half[0]['participants'], pair)
                    self.assertEqual(half[0]['score'], score)
                    self.assertEqual(half[0]['condition_evidence']['fallback_from'], {
                        'group_branches': [birth, middle, tomb],
                        'clashed_branch': birth if clashed == 'month' else tomb,
                        'clashed_pillar': clashed,
                        'clashing_pillar': 'year' if clashed == 'month' else 'hour',
                        'reason': reason,
                    })
                    dynamics = analyze_branch_dynamics(
                        list('甲甲甲甲'), branches, result['matrix'])
                    self.assertEqual(next(g for g in dynamics['groups']
                                          if g['type'] == '삼합(三合)')['activation_status'],
                                     'suppressed')
                    self.assertTrue(any(r['relation_id'] == half[0]['relation_id']
                                        for p in dynamics['pairwise']
                                        for r in p['relations']))

        # 충이 해당 날개와 떨어져 있으면 완전한 삼합 후보를 유지한다.
        intact = build_interaction_matrix(
            list('甲甲甲甲'), list('亥卯未巳'), '甲')['matrix']
        self.assertEqual(next(r for r in intact if r['type'] == '삼합(三合)')['score'],
                         3.0)
        self.assertFalse(any(r['type'] == '반합(半合)' for r in intact))

    def test_gong_hap_is_not_half_hap_and_needs_missing_middle(self):
        for pair, rule in GONG_HAPS.items():
            with self.subTest(pair=pair):
                branches = list(pair) + ['丑', '丑']
                result = build_interaction_matrix(list('甲甲甲甲'), branches, '甲')
                target = [r for r in result['matrix']
                          if r['participants'] == ['year', 'month']]
                self.assertEqual([r['type'] for r in target], ['공합(拱合)'])
                self.assertEqual(target[0]['missing_branch'], rule['missing'])
                self.assertEqual(target[0]['candidate_element'], rule['element'])
                self.assertEqual(target[0]['score'], 0.0)
                self.assertEqual(target[0]['activation_status'], 'candidate_only')
                self.assertEqual(check_gong_hap(pair[1], 1, branches, '甲')[0]['with_index'], 0)
                completed = build_interaction_matrix(
                    list('甲甲甲甲'), list(pair) + [rule['missing'], '丑'], '甲')
                self.assertFalse(any(r['type'] == '공합(拱合)' and
                                     r['participants'] == ['year', 'month']
                                     for r in completed['matrix']))
                self.assertTrue(any(r['type'] == '삼합(三合)'
                                    for r in completed['matrix']))

    def test_hidden_stem_hap_preserves_exact_stem_pairs_and_positions(self):
        for pair, stem_pairs in HIDDEN_STEM_HAPS.items():
            with self.subTest(pair=pair):
                result = build_interaction_matrix(
                    list('甲甲甲甲'), list(pair) + ['子', '子'], '甲')
                hidden = next(r for r in result['matrix']
                              if r['type'] == '암합(暗合)' and
                              r['participants'] == ['year', 'month'])
                self.assertEqual([(s['my'], s['with']) for s in hidden['hidden_stem_pairs']],
                                 list(stem_pairs))
                self.assertTrue(all(s['combined_element_candidate'] in
                                    STEM_COMBINATIONS.values()
                                    for s in hidden['hidden_stem_pairs']))
                self.assertEqual(hidden['score'], 0.0)
                reversed_match = check_hidden_stem_hap(pair[1], 0,
                                                         [pair[1], pair[0]], '甲')[0]
                self.assertEqual([(s['my'], s['with']) for s in
                                  reversed_match['hidden_stem_pairs']],
                                 [(second, first) for first, second in stem_pairs])

        result = build_interaction_matrix(list('甲甲甲甲'), list('寅丑寅子'), '甲')
        self.assertEqual({tuple(r['participants']) for r in result['matrix']
                          if r['type'] == '암합(暗合)'},
                         {('year', 'month'), ('month', 'day')})

    def test_new_candidates_have_no_force_or_bin_zhu_combination_score(self):
        stems, branches = list('甲甲甲甲'), list('寅丑戌子')
        interactions = build_interaction_matrix(stems, branches, '甲')['matrix']
        candidates = [r for r in interactions
                      if r['type'] in {'공합(拱合)', '암합(暗合)'}]
        dynamics = analyze_branch_dynamics(stems, branches, interactions)
        by_id = {r['relation_id']: r for p in dynamics['pairwise']
                 for r in p['relations']}
        for candidate in candidates:
            self.assertEqual(by_id[candidate['relation_id']]['activation_status'],
                             'candidate_only')
            self.assertTrue(all(force == 0 for force in
                                by_id[candidate['relation_id']]['force'].values()))
        bin_zhu = analyze_bin_zhu_dynamics(stems, branches, '甲', interactions)
        self.assertTrue(all(any(e['relation_id'] == r['relation_id'] and
                                e['reason_code'] == 'candidate_only_relation'
                                for e in bin_zhu['excluded_interactions'])
                            for r in candidates if 'day' in r['participants'] or
                            'hour' in r['participants']))

    def test_three_punishment_is_a_group_not_three_extra_pair_scores(self):
        self.assertEqual(THREE_PUNISHMENTS[('寅', '巳', '申')], '무은지형')
        for branches, expected in [('寅巳午未', []), ('寅申午未', []),
                                   ('巳申午未', []), ('寅巳申未', ['무은지형'])]:
            with self.subTest(branches=branches):
                result = build_interaction_matrix(list('甲甲甲甲'), list(branches), '甲')
                self.assertEqual([r['name'] for r in result['matrix']
                                  if r['type'] == '삼형(三刑)'], expected)
                self.assertFalse(any(r['type'] == '형(刑)' for r in result['matrix']))
        result = build_interaction_matrix(list('甲甲甲甲'), list('寅巳申未'), '甲')
        group = next(r for r in result['matrix'] if r['type'] == '삼형(三刑)')
        self.assertEqual(group['participants'], ['year', 'month', 'day'])
        self.assertEqual(group['formations'], [['year', 'month', 'day']])
        self.assertEqual(group['score'], 0.0)
        self.assertEqual(group['activation_status'], 'active')
        self.assertEqual(group['activation_rule_id'],
                         'branch:triple_punishment_presence_active_v1')
        self.assertTrue({'천(穿)', '충(沖)', '육합(六合)'}.issubset(
            {r['type'] for r in result['matrix']}))

    def test_distant_triple_punishment_preserves_each_pair_status(self):
        cases = (
            ('寅巳子申', '무은지형', {
                ('year', 'month'): '천(穿)',
                ('year', 'hour'): '충(沖)',
                ('month', 'hour'): '육합(六合)',
            }),
            ('丑戌子未', '지세형', {
                ('year', 'month'): '형(刑)',
                ('year', 'hour'): '충(沖)',
                ('month', 'hour'): '형(刑)',
            }),
        )
        for branch_text, name, expected_pairs in cases:
            with self.subTest(branches=branch_text):
                result = build_interaction_matrix(
                    list('甲甲甲甲'), list(branch_text), '甲')['matrix']
                group = next(item for item in result if item['type'] == '삼형(三刑)')
                self.assertEqual(group['name'], name)
                self.assertEqual(group['activation_status'], 'active')
                self.assertFalse(group['is_adjacent'])
                self.assertEqual(group['score'], 0.0)
                for pillars, kind in expected_pairs.items():
                    relation = next(item for item in result
                                    if item['type'] == kind
                                    and item['participants'] == list(pillars))
                    self.assertEqual(relation['activation_status'], 'active')

        conditional = build_interaction_matrix(
            list('甲甲甲甲'), list('巳申寅子'), '甲')['matrix']
        self.assertEqual(next(item for item in conditional
                              if item['type'] == '삼형(三刑)')['activation_status'], 'active')
        self.assertEqual(next(item for item in conditional
                              if item['type'] == '육합(六合)' and
                              item['participants'] == ['year', 'month'])
                         ['activation_status'], 'conditional')

    def test_earth_punishment_and_clash_are_distinct(self):
        result = build_interaction_matrix(list('甲甲甲甲'), list('丑未午子'), '甲')
        pair = [r['type'] for r in result['matrix']
                if r['participants'] == ['year', 'month']]
        self.assertIn('충(沖)', pair)
        self.assertNotIn('형(刑)', pair)
        result = build_interaction_matrix(list('甲甲甲甲'), list('丑戌未子'), '甲')
        groups = [r for r in result['matrix'] if r['type'] == '삼형(三刑)']
        self.assertEqual([r['name'] for r in groups], ['지세형'])
        self.assertEqual(groups[0]['score'], 0.0)
        self.assertEqual(len([r for r in result['matrix'] if r['type'] == '형(刑)']), 2)

    def test_pair_primary_relation_and_bin_zhu_do_not_treat_three_punishment_as_hap(self):
        stems, branches = list('甲甲甲甲'), list('寅巳申未')
        interactions = build_interaction_matrix(stems, branches, '甲')['matrix']
        dynamics = analyze_branch_dynamics(stems, branches, interactions)
        primaries = {pair['pair_id']: pair['primary_relation']
                     for pair in dynamics['pairwise']}
        self.assertEqual(primaries['year:month'], '천(穿)')
        self.assertEqual(primaries['year:day'], '충(沖)')
        self.assertEqual(primaries['month:day'], '육합(六合)')
        self.assertEqual([g['type'] for g in dynamics['groups']
                          if g['type'] == '삼형(三刑)'], ['삼형(三刑)'])
        bin_zhu = analyze_bin_zhu_dynamics(stems, branches, '甲', interactions)
        self.assertFalse(any(g['type'] == '삼형(三刑)'
                             for g in bin_zhu['group_connections']))

    def test_repeated_branch_has_each_three_punishment_formation(self):
        groups = check_three_punishment('申', 2, list('寅巳申申'), '甲')
        self.assertEqual(groups[0]['formation_indices'], [[0, 1, 2], [0, 1, 3]])
        result = build_interaction_matrix(list('甲甲甲甲'), list('寅巳申申'), '甲')
        group = next(r for r in result['matrix'] if r['type'] == '삼형(三刑)')
        self.assertEqual(group['participants'], ['year', 'month', 'day', 'hour'])
        self.assertEqual(group['formations'], [['year', 'month', 'day'],
                                                ['year', 'month', 'hour']])

    def test_mangpa_breaks_are_used_by_branch_detector(self):
        self.assertEqual(BREAKS, {('子', '卯'), ('卯', '午'), ('午', '酉')})
        matches = check_break('午', 0, ['午', '酉', '子', '寅'], '甲')
        self.assertEqual([(item['with'], item['with_index']) for item in matches],
                         [('酉', 1)])

    def test_stem_combination_reads_central_rule(self):
        self.assertEqual(STEM_COMBINATIONS[('甲', '己')], '土')
        matches = check_stem_combination('甲', 0, ['甲', '己', '丙', '丁'], '丙')
        self.assertEqual(matches[0]['combined_element'], '土')

    def test_conditional_self_combination_reads_central_rule(self):
        self.assertEqual(JAHAB_MAP[('丙', '戌')]['required'], ('지세형', '未'))
        inactive = check_jahab('丙', '戌', 0, None, [])
        active = check_jahab('丙', '戌', 0, None,
                            [{'type': '지세형', 'with': '未'}])
        self.assertFalse(inactive['active'])
        self.assertTrue(active['active'])
        blocked = check_jahab('丙', '戌', 0, [{
            'with': '辰', 'with_index': 1, 'distance': 1,
            'strength': 1.0, 'is_adjacent': True,
        }], [{'type': '지세형', 'with': '未'}])
        self.assertFalse(blocked['active'])
        self.assertTrue(blocked['condition_met'])
        self.assertEqual(blocked['inactive_reason'], 'blocked_by_chen_chung')


if __name__ == '__main__':
    unittest.main()
