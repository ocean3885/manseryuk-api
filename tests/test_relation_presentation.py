from copy import deepcopy
from itertools import permutations, product
import unittest

from pydantic import ValidationError
from relation_presentation_fixtures import response_for, row_for, links
from schemas.character_details import CharacterDetails
from services.character_details import assemble_character_details
from services.character_relation_index import assemble_character_relation_index_from_response
from services.cycle_relations import attach_cycle_relations
from services.relation_presentation import build_relation_presentation, REASON_CODES


class RelationPresentationTests(unittest.TestCase):
    def test_all_branch_pairs_and_stem_pairs_have_complete_scoped_explanations(self):
        for left, right in product('子丑寅卯辰巳午未申酉戌亥', repeat=2):
            for branches in (left + right + '寅辰', left + '寅辰' + right):
                graph = assemble_character_details(response_for(branches))
                for row in graph['relations'].values():
                    self.assertEqual(row['presentation']['missing_evidence_codes'], [],
                                     (branches, row['source_relation_id'], row['presentation']))
        for left, right in product('甲乙丙丁戊己庚辛壬癸', repeat=2):
            graph = assemble_character_details(response_for('寅丑未亥', left + '丙丁' + right))
            for row in graph['relations'].values():
                self.assertEqual(row['presentation']['missing_evidence_codes'], [],
                                 (left, right, row['source_relation_id']))

    def test_reason_inventory_has_complete_explanations_and_source_links(self):
        reasons = set()
        for branches in ('子丑寅辰', '子午丑寅', '午子丑寅', '子卯辰寅', '亥卯未卯',
                         '亥卯酉未', '巳亥卯未', '亥卯未丑', '戌子卯酉', '戌未辰酉',
                         '辰辰寅卯', '辰寅卯辰', '酉卯戌辰', '寅巳申未', '寅卯辰子', '寅丑子辰'):
            with self.subTest(branches=branches):
                graph = assemble_character_details(response_for(branches, '丙甲甲甲'))
                for row in graph['relations'].values():
                    reasons.update(row['status_reasons'])
                    display = row['presentation']
                    self.assertEqual(display['explanation_status'], 'complete', (row['source_relation_id'], display))
                    self.assertEqual(display['missing_evidence_codes'], [])
                    for participant in row['participant_details']:
                        self.assertIn(participant['display_name'], display['title'])
                    for code in row['status_reasons']:
                        self.assertIn(code, [r['code'] for r in display['reasons']])
                    for line in display['reasons']:
                        for rid in line['relation_ids']:
                            self.assertIn(rid, graph['relations'])
        self.assertEqual(reasons, REASON_CODES - {'cycle_presence_only_activation_and_impact_not_evaluated'})

    def test_trine_clash_has_causal_positions_ten_gods_and_no_duplicate_reasons(self):
        graph = assemble_character_details(response_for('巳亥卯未', '乙辛癸己'))
        group = row_for(graph, 'trine')
        line = next(r for r in group['presentation']['reasons'] if r['code'] == 'adjacent_birth_clash')
        self.assertEqual(line['character_ids'], ['natal.chart.month.branch', 'natal.chart.year.branch'])
        self.assertEqual(line['relation_ids'], ['natal.chart:branch:clash:year:month'])
        self.assertIn('겁재', line['text'])
        self.assertIn('정재', line['text'])
        self.assertGreater(len(line['evidence_indices']), 1)
        self.assertEqual(len([r for r in group['presentation']['reasons'] if r['code'] == line['code']]), 1)
        half = row_for(graph, 'half_combine')
        self.assertIn(group['relation_id'], links(half))
        self.assertIn('remaining_half_combine', [r['code'] for r in half['presentation']['reasons']])

    def test_structure_only_halves_are_not_presented_as_independent_effects(self):
        graph = assemble_character_details(response_for('亥卯未亥'))
        group = row_for(graph, 'trine')
        formations = [r for r in group['presentation']['reasons'] if r['code'] == 'formation']
        self.assertEqual(len(formations), 2)
        self.assertNotEqual(formations[0]['character_ids'], formations[1]['character_ids'])
        for row in graph['relations'].values():
            if row['type'] == 'half_combine':
                self.assertEqual(row['activation_status'], 'candidate_only')
                self.assertIn(group['relation_id'], links(row))
                self.assertIn('독립 작용으로 확정하지 않습니다', ' '.join(r['text'] for r in row['presentation']['reasons']))

    def test_override_is_linked_only_to_active_structure_on_same_pair(self):
        graph = assemble_character_details(response_for('子卯辰寅'))
        row = row_for(graph, 'generate', 'year', 'month')
        line = next(r for r in row['presentation']['reasons'] if r['code'] == 'active_pair_structure_overrides_element')
        self.assertEqual(line['relation_ids'], ['natal.chart:branch:break:year:month'])
        self.assertEqual(links(row), set(line['relation_ids']))

    def test_self_combine_absence_satisfaction_and_blocking(self):
        for branches, state, cause_types in [('戌子卯酉', 'conditional', set()),
                                            ('戌未卯酉', 'active', {'punishment'}),
                                            ('戌未辰酉', 'suppressed', {'punishment', 'clash'}),
                                            ('戌辰卯酉', 'suppressed', {'clash'})]:
            graph = assemble_character_details(response_for(branches, '丙甲甲甲'))
            row = next(r for r in graph['relations'].values() if r['source_relation_id'] == 'same_pillar:self_combine:year')
            self.assertEqual(row['activation_status'], state)
            self.assertEqual({graph['relations'][rid]['type'] for rid in links(row)}, cause_types)
            self.assertEqual(row['presentation']['explanation_status'], 'complete')
            if state == 'conditional':
                self.assertFalse(row['presentation']['reasons'][0]['relation_ids'])
                self.assertIn('확인되지 않아', row['presentation']['reasons'][0]['text'])

    def test_active_combination_carries_transformation_notice_separately(self):
        graph = assemble_character_details(response_for('子丑寅辰'))
        row = row_for(graph, 'combine', 'year', 'month')
        self.assertEqual(row['presentation']['status_label'], '성립')
        notice = next(r for r in row['presentation']['reasons'] if r['code'] == 'combination_candidate_not_transformation')
        self.assertEqual(notice['category'], 'notice')
        self.assertTrue(any(r['category'] == 'decision' for r in row['presentation']['reasons']))

    def test_missing_or_unknown_evidence_is_explicit_and_does_not_invent_cause(self):
        graph = assemble_character_details(response_for('巳亥卯未'))
        row = deepcopy(row_for(graph, 'trine'))
        row['evidence'] = []
        result = build_relation_presentation(graph, row)
        self.assertEqual(result['explanation_status'], 'partial')
        self.assertIn('adjacent_birth_clash', result['missing_evidence_codes'])
        self.assertFalse(result['reasons'])
        row['status_reasons'] = ['future_rule']
        row['status_reason'] = 'future_rule'
        result = build_relation_presentation(graph, row)
        self.assertEqual(result['missing_evidence_codes'], ['future_rule'])
        self.assertFalse(result['reasons'])

    def test_transmission_and_element_descriptions_keep_direction(self):
        graph = assemble_character_details(response_for('亥卯未亥', '己丁辛己'))
        for row in graph['relations'].values():
            if row['type'] in ('transmission', 'element'):
                text = row['presentation']['description']
                if row['direction']:
                    a, b = row['direction']['from_character'], row['direction']['to_character']
                    labels = {p['character_id']: p['display_name'] for p in row['participant_details']}
                    self.assertLess(text.index(labels[a]), text.index(labels[b]))
                    if row['type'] == 'transmission':
                        self.assertIn(f"지장간 {row['hidden_stem']}", text)
        same = assemble_character_details(response_for('巳亥卯未', '乙辛癸己'))
        self.assertEqual(same['relations']['natal.chart:same_pillar:element:hour']['element_relation'], 'same_element')

    def test_cycle_presence_never_inherits_natal_active_or_impact(self):
        graph = assemble_character_details(response_for('子丑寅辰'))
        graph['contexts']['sewoon.year_2026'] = dict(scope='sewoon', instance='year_2026', label='2026 세운',
                                                  calculation_status='not_evaluated', selection={})
        node = deepcopy(graph['characters']['natal.chart.year.branch'])
        node.update(context_id='sewoon.year_2026', position='cycle', relation_ids=[], transmission_relation_ids=[])
        graph['characters']['sewoon.year_2026.cycle.branch'] = node
        attach_cycle_relations(graph)
        CharacterDetails.model_validate(graph)
        for rid, row in graph['relations'].items():
            if rid.startswith('cycle:'):
                self.assertNotEqual(row['activation_status'], 'active')
                self.assertEqual(row['presentation']['explanation_status'], 'complete')
                self.assertTrue(any(r['category'] == 'scope' for r in row['presentation']['reasons']))
        before = deepcopy(graph)
        attach_cycle_relations(graph)
        self.assertEqual(graph, before)

    def test_rendering_is_deterministic_and_preserves_existing_decisions(self):
        for branches in sorted(set(permutations('亥卯未亥')) | set(permutations('子午丑未'))):
            response = response_for(branches)
            before = deepcopy(response)
            original = assemble_character_relation_index_from_response(response)
            graph = assemble_character_details(response)
            self.assertEqual(response, before)
            self.assertEqual(len(graph['relations']), len(original['relations']))
            for source in original['relations']:
                row = graph['relations']['natal.chart:' + source['relation_id']]
                for field in ('activation_status', 'status_reason', 'rule_ids', 'candidate_element'):
                    self.assertEqual(row[field], source[field])
            shuffled = deepcopy(graph)
            shuffled['relations'] = dict(reversed(list(shuffled['relations'].items())))
            shuffled['characters'] = dict(reversed(list(shuffled['characters'].items())))
            for rid, row in shuffled['relations'].items():
                self.assertEqual(build_relation_presentation(shuffled, row), graph['relations'][rid]['presentation'])

    def test_invalid_ten_gods_effective_status_and_explanation_refs_are_rejected(self):
        source = assemble_character_details(response_for('巳亥卯未'))
        for defect in ('ten_god', 'effective_status', 'character_ref', 'relation_ref', 'unrelated_ref',
                       'evidence_index', 'complete', 'badge'):
            graph = deepcopy(source)
            row = row_for(graph, 'trine')
            line = row['presentation']['reasons'][0]
            if defect == 'ten_god':
                row['participant_details'][0]['ten_god'] = 'invalid'
            elif defect == 'effective_status':
                row['evidence'][0]['details']['effective_activation_status'] = 'active'
            elif defect == 'character_ref':
                line['character_ids'].append('missing')
            elif defect == 'relation_ref':
                line['relation_ids'].append('missing')
            elif defect == 'unrelated_ref':
                line['relation_ids'].append('natal.chart:same_pillar:element:day')
            elif defect == 'evidence_index':
                line['evidence_indices'].append(1000)
            elif defect == 'badge':
                row['presentation']['status_label'] = '성립'
            else:
                row['presentation']['missing_evidence_codes'] = ['missing']
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CharacterDetails.model_validate(graph)
