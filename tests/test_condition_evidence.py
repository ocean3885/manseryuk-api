"""Condition evidence is readable and retains exact causal positions and rules."""
import unittest

from relation_presentation_fixtures import response_for
from services.branch_relations import check_six_haps, check_three_hap
from services.character_details import assemble_character_details
from services.calculator import get_ten_star_branch

PILLARS = ('year', 'month', 'day', 'hour')


class ConditionEvidenceTests(unittest.TestCase):
    def assert_member_matches(self, member, branches, day_stem):
        index = member['index']
        self.assertEqual(member['pillar'], PILLARS[index])
        self.assertEqual(member['char'], branches[index])
        self.assertEqual(member['ten_god'], get_ten_star_branch(day_stem, branches[index]))
        self.assertIn(member['char'], member['display_name'])
        self.assertIn(member['ten_god'], member['display_name'])

    def test_six_hap_explains_clash_location_and_status(self):
        for branches, index, state, location, label in (
            ('午子丑寅', 1, 'conditional', 'outside', '육합 조합 바깥'),
            ('子午丑寅', 0, 'suppressed', 'between', '육합 두 글자 사이'),
        ):
            with self.subTest(branches=branches):
                item = check_six_haps(branches[index], index, list(branches), '甲')[0]
                condition = item['condition_evidence']
                clash = condition['adjacent_clashes'][0]
                self.assertEqual(item['activation_status'], state)
                self.assertEqual(clash['location'], location)
                self.assertEqual(clash['location_label'], label)
                self.assertIn(label, condition['summary'])
                self.assertNotIn('판정', condition['summary'])
                for key, field in (('affected', 'member_index'), ('cause', 'clashing_index')):
                    self.assert_member_matches(clash[key], branches, '甲')
                    self.assertEqual(clash[key]['index'], clash[field])
                    self.assertIn(clash[key]['display_name'], clash['description'])
                    self.assertIn(clash[key]['display_name'], condition['summary'])

    def test_unblocked_hap_summary_does_not_invent_a_clash_or_transformation(self):
        item = check_six_haps('子', 0, list('子丑寅卯'), '甲')[0]
        condition = item['condition_evidence']
        self.assertEqual(condition['adjacent_clashes'], [])
        self.assertEqual(item['activation_status'], 'active')
        self.assertEqual(item['impact_status'], 'not_evaluated')
        self.assertIn('인접 충이 확인되지 않았습니다', condition['summary'])
        self.assertNotIn('판정', condition['summary'])
        self.assertNotIn('합화', condition['summary'])

    def test_duplicate_middle_identifies_each_actual_position(self):
        item = check_three_hap('亥', 0, list('亥卯卯未'), '甲')[0][0]
        condition = item['condition_evidence']
        members = condition['middle_members']
        self.assertEqual([m['index'] for m in members], [1, 2])
        self.assertEqual([m['pillar'] for m in members], ['month', 'day'])
        self.assertEqual([m['char'] for m in members], ['卯', '卯'])
        for member in members:
            self.assertIn(member['display_name'], condition['summary'])
        self.assertIn('중신이 중복', condition['summary'])
        self.assertEqual(item['activation_status'], 'conditional')
        self.assertNotIn('판정', condition['summary'])

    def test_middle_birth_and_tomb_clashes_are_not_confused(self):
        for branches, bucket, role in (
            ('亥卯酉未', 'adjacent_clashes', '중신'),
            ('巳亥卯未', 'adjacent_wing_clashes', '생지'),
            ('亥卯未丑', 'adjacent_wing_clashes', '성지'),
        ):
            with self.subTest(branches=branches):
                index = branches.index('亥')
                item = check_three_hap('亥', index, list(branches), '甲')[0][0]
                condition = item['condition_evidence']
                self.assertIn(f'삼합 {role}의 인접 충', condition['summary'])
                self.assertEqual(item['activation_status'], 'suppressed')
                self.assertNotIn('판정', condition['summary'])
                for clash in condition[bucket]:
                    for key in ('affected', 'cause'):
                        self.assert_member_matches(clash[key], branches, '甲')

    def test_readable_evidence_survives_matrix_graph_and_remaining_half(self):
        for branches in ('午子丑寅', '子午丑寅', '亥卯卯未', '亥卯酉未',
                         '巳亥卯未', '亥卯未丑'):
            with self.subTest(branches=branches):
                response = response_for(branches)
                graph = assemble_character_details(response)
                matrices = response['advanced_analysis']['interactions']['matrix']
                for item in matrices:
                    condition = item.get('condition_evidence', {})
                    if item['type'] not in ('육합(六合)', '삼합(三合)', '반합(半合)') or not condition:
                        continue
                    self.assertTrue(condition['summary'])
                    row = next(r for r in graph['relations'].values()
                               if any(ref['relation_id'] == item['relation_id']
                                      for ref in r['source_refs']))
                    self.assertTrue(any(entry['details'].get('condition_evidence', {}).get('summary')
                                        == condition['summary'] for entry in row['evidence']))
                    self.assertEqual(row['presentation']['explanation_status'], 'complete')
                    if item['type'] == '반합(半合)':
                        fallback = condition['fallback_from']
                        self.assertIn('남은 중신과 날개의 반합 후보', condition['summary'])
                        self.assertEqual(fallback['affected']['pillar'], fallback['clashed_pillar'])
                        self.assertEqual(fallback['cause']['pillar'], fallback['clashing_pillar'])


if __name__ == '__main__':
    unittest.main()
