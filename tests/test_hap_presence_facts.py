"""Combine/trine facts remain independent of activation and numerical policy."""
from copy import deepcopy
from itertools import permutations
import unittest
from pydantic import ValidationError
from relation_presentation_fixtures import response_for
from schemas.character_details import CharacterDetails
from schemas.character_relation_index import CharacterRelation
from services.branch_dynamics_v3_assembler import assemble_branch_pairs_v3
from services.character_details import assemble_character_details
from services.relation_rules import SIX_HAPS, THREE_HAPS, THREE_HAPS_KING

PILLARS = ('year', 'month', 'day', 'hour')


class HapPresenceFactsTests(unittest.TestCase):
    def test_all_repeated_trines_keep_counts_positions_and_formations(self):
        checked = 0
        for triple, element in THREE_HAPS.items():
            middle = THREE_HAPS_KING[element][0]
            for repeated in triple:
                for branches in sorted(set(permutations((*triple, repeated)))):
                    response = response_for(branches)
                    before = deepcopy(response)
                    graph = assemble_character_details(response)
                    self.assertEqual(response, before)
                    group = next(r for r in graph['relations'].values() if r['type'] == 'trine')
                    self.assertEqual(group['activation_status'], 'detected')
                    self.assertEqual(len(group['formation_candidates']), 2)
                    self.assertEqual(len(group['participants']), 4)
                    self.assertEqual(group['presentation']['explanation_status'], 'complete')
                    self.assertIn(group['relation_id'], graph['coverage']['detected_only_relation_ids'])
                    for pillar in PILLARS:
                        raw = response['analysis']['details'][pillar]['branch']['relations']['three_haps'][0]
                        condition = raw['condition_evidence']
                        self.assertEqual(raw['activation_status'], 'detected')
                        self.assertEqual(condition['middle_count'], 2 if repeated == middle else 1)
                        self.assertEqual(len(condition['middle_members']), condition['middle_count'])
                        self.assertEqual(condition['middle_indices'], [i for i, b in enumerate(branches) if b == middle])
                    checked += 1
        self.assertEqual(checked, 144)

    def test_all_six_haps_keep_each_repeated_pair_as_a_fact(self):
        checked = 0
        for first, second in SIX_HAPS:
            for branches in sorted(set(permutations((first, second, first, second)))):
                response = response_for(branches)
                graph = assemble_character_details(response)
                rows = [r for r in graph['relations'].values() if r['type'] == 'combine']
                self.assertEqual(len(rows), 4)
                for row in rows:
                    self.assertEqual(row['activation_status'], 'detected')
                    self.assertEqual(row['presentation']['explanation_status'], 'complete')
                    self.assertFalse(any(r['category'] == 'decision' for r in row['presentation']['reasons']))
                for pillar in PILLARS:
                    for raw in response['analysis']['details'][pillar]['branch']['relations']['six_haps']:
                        self.assertEqual(raw['activation_status'], 'detected')
                        self.assertIsNone(raw['activation_rule_id'])
                checked += 1
        self.assertEqual(checked, 36)

    def test_clashes_remain_visible_without_judgment_language(self):
        for branches in ('午子丑寅', '子午丑寅', '亥卯酉未', '巳亥卯未', '亥卯未丑'):
            graph = assemble_character_details(response_for(branches))
            for row in graph['relations'].values():
                if row['type'] not in ('combine', 'trine'):
                    continue
                self.assertEqual(row['activation_status'], 'detected')
                self.assertEqual(row['presentation']['explanation_status'], 'complete')
                for line in row['presentation']['reasons']:
                    self.assertNotEqual(line['category'], 'decision')
                    self.assertNotIn('조건부', line['text'])
                    self.assertNotIn('억제합니다', line['text'])
                    self.assertTrue(all(rid in graph['relations'] for rid in line['relation_ids']))

    def test_presence_without_scores_keeps_applied_delta_unevaluated(self):
        for branches, kind in (
            ('子丑寅辰', '육합(六合)'), ('午子丑寅', '육합(六合)'),
            ('子午丑寅', '육합(六合)'), ('亥卯未亥', '삼합(三合)'),
            ('亥卯卯未', '삼합(三合)'), ('巳亥卯未', '삼합(三合)'),
        ):
            response = response_for(branches)
            item = next(r for r in response['advanced_analysis']['interactions']['matrix'] if r['type'] == kind)
            self.assertEqual(item['activation_status'], 'detected')
            self.assertNotIn('score', item)
            if kind == '육합(六合)':
                pairs = assemble_branch_pairs_v3(list(branches), response['advanced_analysis']['branch_dynamics'])
                row = next(r for p in pairs for r in p['relations'] if r['type'] == 'combine')
                self.assertEqual(row['calculation_status'], 'potential_calculated')
                self.assertTrue(all(e['applied_power_delta'] is None for e in row['metrics']['directional_effects']))

    def test_combine_presence_does_not_suppress_a_separate_elemental_route(self):
        for first, second in SIX_HAPS:
            graph = assemble_character_details(response_for(first + second + '子丑'))
            rows = [r for r in graph['relations'].values()
                    if set(r['participants']) == {'natal.chart.year.branch', 'natal.chart.month.branch'}]
            self.assertEqual(next(r for r in rows if r['type'] == 'combine')['activation_status'], 'detected')
            elemental = next(r for r in rows if r['type'] in ('generate', 'control'))
            self.assertEqual(elemental['activation_status'], 'potential')
            self.assertNotEqual(elemental['status_reason'], 'active_pair_structure_overrides_element')

    def test_contracts_reject_reintroducing_natal_activation_judgments(self):
        for branches, kind in (('子丑寅辰', 'combine'), ('亥卯卯未', 'trine')):
            graph = assemble_character_details(response_for(branches))
            row = next(r for r in graph['relations'].values() if r['type'] == kind)
            for status in ('active', 'conditional', 'suppressed', 'potential'):
                changed = deepcopy(graph)
                changed['relations'][row['relation_id']]['activation_status'] = status
                with self.assertRaisesRegex(ValidationError, '육합·삼합은 구성의 존재만'):
                    CharacterDetails.model_validate(changed)
                with self.assertRaisesRegex(ValidationError, '육합·삼합은 구성의 존재만'):
                    CharacterRelation.model_validate(dict(
                        relation_id=row['source_relation_id'], type=kind,
                        participants=[p.removeprefix('natal.chart.') for p in row['participants']],
                        activation_status=status, source_refs=row['source_refs']))


if __name__ == '__main__':
    unittest.main()
