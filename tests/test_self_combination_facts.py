"""Self-combination presence and surrounding branch facts never decide activation."""
from copy import deepcopy
import unittest

from pydantic import ValidationError
from relation_presentation_fixtures import response_for, links
from schemas.character_details import CharacterDetails
from schemas.character_relation_index import CharacterRelation
from services.character_details import assemble_character_details
from services.relation_rules import JAHAB_MAP, CHUNGS

PILLARS = ('year', 'month', 'day', 'hour')
REMOVED = ('active', 'is_conditional', 'condition_met', 'required_condition',
           'inactive_reason', 'blocking_chung', 'chung_impact')


class SelfCombinationFactsTests(unittest.TestCase):
    def test_all_registered_pairs_at_each_position_keep_clashes_as_facts(self):
        checked = 0
        for (stem, branch), rule in JAHAB_MAP.items():
            opponent = next(b if a == branch else a for a, b in CHUNGS if branch in (a, b))
            for own in range(4):
                for other in range(4):
                    if own == other:
                        continue
                    stems, branches = list('甲甲甲甲'), list('卯卯卯卯')
                    stems[own], branches[own], branches[other] = stem, branch, opponent
                    response = response_for(branches, stems)
                    before = deepcopy(response)
                    graph = assemble_character_details(response)
                    self.assertEqual(response, before)
                    raw = response['analysis']['details'][PILLARS[own]]['jahab']
                    self.assertEqual(raw['activation_status'], 'detected')
                    self.assertEqual(raw['impact_status'], 'not_evaluated')
                    self.assertEqual(raw['hidden_stem'], rule['hidden'])
                    self.assertFalse(any(key in raw for key in REMOVED))
                    context = next(c for c in raw['related_branch_relations']
                                   if c['type'] == 'clash' and c['with_index'] == other)
                    self.assertEqual(context['with'], opponent)
                    self.assertEqual(context['with_ten_star'],
                                     response['four_pillars'][PILLARS[other]]['ji']['ten_god'])
                    self.assertEqual(context['distance'], abs(other - own))
                    row = graph['relations'][f'natal.chart:same_pillar:self_combine:{PILLARS[own]}']
                    self.assertEqual(row['activation_status'], 'detected')
                    self.assertEqual(row['status_reasons'], [])
                    self.assertIn(row['relation_id'], graph['coverage']['detected_only_relation_ids'])
                    self.assertTrue(any(graph['relations'][rid]['type'] == 'clash' and
                                        f'natal.chart.{PILLARS[other]}.branch' in graph['relations'][rid]['participants']
                                        for rid in links(row)))
                    self.assertEqual(row['presentation']['explanation_status'], 'complete')
                    checked += 1
        self.assertEqual(checked, 108)

    def test_wei_chen_presence_does_not_change_self_combination_status(self):
        for stem in ('丙', '壬'):
            for branches, expected in (
                ('戌子寅卯', []),
                ('戌未寅卯', [('punishment', '未', 1)]),
                ('戌辰寅卯', [('clash', '辰', 1)]),
                ('戌未辰卯', [('clash', '辰', 2), ('punishment', '未', 1)]),
                ('戌辰未辰', [('clash', '辰', 1), ('clash', '辰', 3), ('punishment', '未', 2)]),
            ):
                with self.subTest(stem=stem, branches=branches):
                    response = response_for(branches, stem + '甲甲甲')
                    raw = response['analysis']['details']['year']['jahab']
                    self.assertEqual(raw['activation_status'], 'detected')
                    self.assertEqual([(x['type'], x['with'], x['with_index'])
                                      for x in raw['related_branch_relations']], expected)

    def test_no_registered_pair_has_no_self_combination(self):
        response = response_for('戌未辰卯', '甲甲甲甲')
        self.assertIsNone(response['analysis']['details']['year']['jahab'])
        graph = assemble_character_details(response)
        self.assertNotIn('natal.chart:same_pillar:self_combine:year', graph['relations'])

    def test_contracts_reject_reintroducing_activation_judgments(self):
        graph = assemble_character_details(response_for('戌未辰卯', '丙甲甲甲'))
        key = 'natal.chart:same_pillar:self_combine:year'
        for status in ('active', 'conditional', 'suppressed', 'candidate_only'):
            changed = deepcopy(graph)
            changed['relations'][key]['activation_status'] = status
            with self.subTest(status=status), self.assertRaisesRegex(ValidationError, '자합은 조합 존재만'):
                CharacterDetails.model_validate(changed)
            with self.assertRaisesRegex(ValidationError, '자합은 조합 존재만'):
                CharacterRelation.model_validate(dict(
                    relation_id='same_pillar:self_combine:year', type='self_combine',
                    participants=['year.stem', 'year.branch'], activation_status=status,
                    status_reason='test' if status in ('conditional', 'suppressed') else None,
                    source_refs=[dict(system='analysis_details', location='analysis.details.year.jahab')]))


if __name__ == '__main__':
    unittest.main()
