"""반복 글자의 위치별 관계와 다자 관계의 참여/성립 조합 검증."""
from itertools import combinations, permutations
import unittest

from schemas.saju_analysis import InteractionsInfo
from services.branch_relations import check_six_hap, check_six_haps, check_three_hap, check_square_hap, get_relations_for_branch
from services.constants import SIX_HAPS
from services.interaction_matrix import build_interaction_matrix
from services.analysis import analyze_advanced_tonggeun
from services.xu_shi import analyze_xu_shi_dynamics

PILLARS = ['year', 'month', 'day', 'hour']


def matrix(branches, stems='甲甲甲甲'):
    return build_interaction_matrix(list(stems), list(branches), stems[2])


def pairs(result, kind):
    return {(r['from_pillar'], r['to_pillar']) for r in result['matrix'] if r['type'] == kind}


class InteractionMatrixTests(unittest.TestCase):
    def test_six_hap_keeps_legacy_single_and_adds_all_partners(self):
        branches = list('子丑丑子')
        all_haps = check_six_haps('子', 0, branches, '甲')
        self.assertEqual([r['with_index'] for r in all_haps], [1, 2])
        self.assertEqual(check_six_hap('子', 0, branches, '甲'), all_haps[0])
        relations = get_relations_for_branch('子', 0, branches, list('甲甲甲甲'))
        self.assertEqual(relations['six_haps'], all_haps[0])
        self.assertEqual(relations['six_haps_all'], all_haps)
        self.assertEqual(matrix(branches)['harmony_score'], 5.1)

    def test_every_six_hap_position_pair_survives_permutations(self):
        for branches in sorted(set(permutations('子丑丑子'))):
            with self.subTest(branches=branches):
                expected = {(PILLARS[i], PILLARS[j]) for i, j in combinations(range(4), 2)
                            if (branches[i], branches[j]) in SIX_HAPS or (branches[j], branches[i]) in SIX_HAPS}
                self.assertEqual(pairs(matrix(branches), '육합(六合)'), expected)

    def test_half_hap_includes_each_repeated_partner(self):
        result = matrix('寅午午酉')
        self.assertEqual(pairs(result, '반합(半合)'), {('year', 'month'), ('year', 'day')})
        self.assertEqual(result['harmony_score'], 2.2)
        for branches in sorted(set(permutations('寅午午酉'))):
            expected = {(PILLARS[i], PILLARS[j]) for i, j in combinations(range(4), 2)
                        if {branches[i], branches[j]} == {'寅', '午'}}
            self.assertEqual(pairs(matrix(branches), '반합(半合)'), expected)

    def test_punishments_are_deduplicated_by_position_not_character(self):
        self.assertEqual(pairs(matrix('寅巳巳酉'), '형(刑)'), {('year', 'month'), ('year', 'day')})
        self.assertEqual(pairs(matrix('午午午子'), '형(刑)'),
                         {('year', 'month'), ('year', 'day'), ('month', 'day')})

    def test_group_participants_and_formations_preserve_duplicate_positions(self):
        for branches, kind, checker in [('亥卯未亥', '삼합(三合)', check_three_hap),
                                        ('寅卯辰寅', '방합(方合)', check_square_hap)]:
            with self.subTest(branches=branches):
                result = matrix(branches)
                groups = [r for r in result['matrix'] if r['type'] == kind]
                self.assertEqual(len(groups), 1)
                group = groups[0]
                self.assertEqual(group['participants'], PILLARS)
                self.assertEqual(group['formations'], [['year', 'month', 'day'], ['month', 'day', 'hour']])
                self.assertEqual(group['relation_scope'], 'group')
                self.assertEqual(group['from_pillar'], 'all')
                self.assertEqual(group['score'], 3.0 if kind == '삼합(三合)' else 3.5)
                for index in range(4):
                    details = checker(branches[index], index, list(branches), '甲')
                    if checker == check_three_hap:
                        details = details[0]
                    self.assertEqual(details[0]['participant_indices'], [0, 1, 2, 3])
                    self.assertEqual({r['index'] for r in details[0]['with_branches']}, set(range(4)) - {index})

    def test_nonparticipant_is_not_included_in_group(self):
        group = next(r for r in matrix('亥卯未子')['matrix'] if r['type'] == '삼합(三合)')
        self.assertEqual(group['participants'], ['year', 'month', 'day'])
        self.assertEqual(group['formations'], [['year', 'month', 'day']])

    def test_ids_are_unique_repeatable_and_survive_response_schema(self):
        result = matrix('亥卯未亥')
        self.assertEqual(result, matrix('亥卯未亥'))
        ids = [r['relation_id'] for r in result['matrix']]
        self.assertEqual(len(ids), len(set(ids)))
        encoded = InteractionsInfo.model_validate(result).model_dump()
        for raw, output in zip(result['matrix'], encoded['matrix']):
            self.assertEqual(output['relation_id'], raw['relation_id'])
            self.assertEqual(output['participants'], raw['participants'])
            self.assertEqual(output['formations'], raw['formations'])
            if raw['relation_scope'] == 'pairwise':
                self.assertEqual(raw['participants'], [raw['from_pillar'], raw['to_pillar']])
                self.assertEqual(raw['formations'], [])

    def test_missing_punishment_fix_changes_root_evidence_not_xu_shi_rule(self):
        stems, branches = list('癸甲乙丁'), list('巳申巳子')
        result = matrix(branches, ''.join(stems))
        corrected = result['matrix']
        # 구버전은 월지 申에서 일지 巳로 향하는 두 번째 같은 글자의 형을 누락했다.
        legacy = [r for r in corrected if not (r['type'] == '형(刑)' and r['from_pillar'] == 'month' and r['to_pillar'] == 'day')]
        roots = analyze_advanced_tonggeun(stems, branches)
        before = analyze_xu_shi_dynamics(stems, branches, stems[2], roots, legacy)
        after = analyze_xu_shi_dynamics(stems, branches, stems[2], roots, corrected)
        self.assertEqual(before['pillars']['hour']['current_status'], '실(實)')
        self.assertEqual(after['pillars']['hour']['current_status'], '변허(變虛)')
        self.assertEqual(before['rule_version'], after['rule_version'])
        ids = {r['relation_id'] for r in corrected}
        for p in after['pillars'].values():
            for root in p['root_evidence']:
                for relation in root['interactions']:
                    self.assertIn(relation['relation_id'], ids)


if __name__ == '__main__':
    unittest.main()
