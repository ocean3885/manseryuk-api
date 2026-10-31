"""허실 v1: 기존 판정 호환성, 경계값, 설명 근거와 응답 직렬화 검증."""
import json
import math
from pathlib import Path
import unittest

from schemas.saju_analysis import XuShiDynamics
from services.analysis import analyze_advanced_tonggeun
from services.interaction_matrix import build_interaction_matrix
from services.xu_shi import analyze_xu_shi_dynamics

PILLARS = ('year', 'month', 'day', 'hour')
POSITIONS = ('년', '월', '일', '시')
BRANCHES = list('子午卯酉')


def root(index, score):
    return {'position': POSITIONS[index], 'branch_char': BRANCHES[index], 'score': score}


def relation(kind='충(沖)', source='year', target='month', **overrides):
    return dict(category='지지', type=kind, from_pillar=source, to_pillar=target, **overrides)


def analyze(score, roots, interactions=(), repeat=False):
    tg = {'점수': score, '통근정보': roots}
    tgs = [tg] * 4 if repeat else [tg] + [{'점수': 0, '통근정보': []} for _ in range(3)]
    return analyze_xu_shi_dynamics(list('甲丙戊庚'), BRANCHES, '戊', tgs, list(interactions))


class XuShiTests(unittest.TestCase):
    def test_shared_root_has_different_outcomes_with_remaining_support(self):
        tgs = [
            {'점수': 1.4, '통근정보': [root(1, 0.8), root(2, 0.6)]},
            {'점수': 1.1, '통근정보': [root(1, 0.8), root(3, 0.3)]},
            {'점수': 0, '통근정보': []}, {'점수': 0, '통근정보': []},
        ]
        result = analyze_xu_shi_dynamics(list('甲丙戊庚'), BRANCHES, '戊', tgs, [relation()])
        year, month = result['pillars']['year'], result['pillars']['month']
        self.assertEqual(year['root_structure'], {
            'primary_root_pillars': ['month'], 'remaining_root_pillars': ['day'],
            'excluded_root_pillars': ['month'], 'remaining_support': 'meets_threshold',
        })
        self.assertEqual(month['root_structure']['remaining_support'], 'below_threshold')
        self.assertEqual(year['transition_code'], 'maintained')
        self.assertEqual(month['transition_code'], 'real_to_empty')
        self.assertEqual(len(result['shared_roots']), 1)
        group = result['shared_roots'][0]
        self.assertEqual(group['root_pillar'], 'month')
        self.assertEqual([d['current_status'] for d in group['dependents']], ['실(實)', '변허(變虛)'])
        self.assertEqual([d['effective_score'] for d in group['dependents']], [0, 0])
        self.assertEqual(result['impact_groups'][0]['affected_stem_pillars'], ['year', 'month'])
        self.assertIn('년간, 월간은 월지(午)의 뿌리를 공유', result['overall_status'])
        self.assertIn('잔존 기반 일지(卯), 점수 0.6', result['overall_status'])
        self.assertIn('잔존 기반 시지(酉), 점수 0.3', result['overall_status'])

    def test_primary_roots_include_ties_and_no_roots_have_no_primary(self):
        result = analyze(1.0, [root(0, 0.5), root(2, 0.5)])
        self.assertEqual(result['pillars']['year']['root_structure']['primary_root_pillars'], ['year', 'day'])
        empty = result['pillars']['month']['root_structure']
        self.assertEqual(empty['primary_root_pillars'], [])
        self.assertEqual(empty['remaining_root_pillars'], [])
        self.assertEqual(empty['remaining_support'], 'none')
        self.assertEqual(result['shared_roots'], [])
        self.assertEqual(result['impact_groups'], [])

    def test_same_branch_character_at_different_positions_is_not_shared(self):
        roots = [dict(root(0, 0.8), branch_char='午'), root(1, 0.8)]
        tgs = [{'점수': 0.8, '통근정보': [r]} for r in roots] + [{'점수': 0, '통근정보': []}] * 2
        result = analyze_xu_shi_dynamics(list('甲丙戊庚'), list('午午卯酉'), '戊', tgs, [])
        self.assertEqual(result['shared_roots'], [])

    def test_impact_collects_both_endpoints_once_and_is_order_independent(self):
        first = relation()
        second = relation('형(刑)', target='day')
        roots = [root(0, 0.4), root(1, 0.4)]
        result = analyze(0.8, roots, [first, first, second], repeat=True)
        reordered = analyze(0.8, roots, [second, first], repeat=True)
        self.assertEqual(result['impact_groups'], reordered['impact_groups'])
        self.assertEqual(len(result['impact_groups']), 2)
        clash = next(g for g in result['impact_groups'] if g['interaction']['type'] == '충(沖)')
        self.assertEqual(clash['affected_root_pillars'], ['year', 'month'])
        self.assertEqual(clash['affected_stem_pillars'], list(PILLARS))

    def test_remaining_support_does_not_reclassify_originally_weak_stem(self):
        pillar = analyze(0.3, [root(0, 0.3)], [relation()])['pillars']['year']
        self.assertEqual(pillar['root_structure']['remaining_support'], 'none')
        self.assertEqual(pillar['transition_code'], 'maintained')
        self.assertEqual(pillar['current_status'], '허(虛)')

    def test_raw_float_boundary_is_not_rounded_before_comparison(self):
        for score, status, support in [
            (math.nextafter(0.5, 0), '변허(變虛)', 'below_threshold'),
            (0.5, '실(實)', 'meets_threshold'),
            (math.nextafter(0.5, 1), '실(實)', 'meets_threshold'),
        ]:
            with self.subTest(score=score):
                pillar = analyze(0.8 + score, [root(0, 0.8), root(2, score)], [relation()])['pillars']['year']
                self.assertEqual(pillar['effective_score'], score)
                self.assertEqual(pillar['current_status'], status)
                self.assertEqual(pillar['root_structure']['remaining_support'], support)

    def test_upstream_total_and_root_rounding_are_preserved(self):
        stems, branches = list('己甲癸辛'), list('子寅卯寅')
        tgs = analyze_advanced_tonggeun(stems, branches)
        result = analyze_xu_shi_dynamics(stems, branches, stems[2], tgs, [])
        pillar = result['pillars']['month']
        self.assertEqual(pillar['score'], 2.73)
        self.assertEqual(pillar['effective_score'], 2.72)
        self.assertEqual(pillar['current_status'], '실(實)')

    def test_original_status_thresholds(self):
        for score, status in [(0, '허투(虛透)'), (0.49, '허(虛)'), (0.5, '실(實)'), (0.51, '실(實)')]:
            with self.subTest(score=score):
                result = analyze(score, [root(0, score)] if score else [])
                pillar = result['pillars']['year']
                self.assertEqual(pillar['original_status'], status)
                self.assertEqual(pillar['current_status'], status)
                self.assertFalse(pillar['is_transformed'])
                self.assertEqual(pillar['effective_score'], score)

    def test_remaining_root_thresholds(self):
        for remaining, expected in [(0, '변허(變虛)'), (0.49, '변허(變虛)'), (0.5, '실(實)'), (0.51, '실(實)')]:
            with self.subTest(remaining=remaining):
                roots = [root(0, 0.8)] + ([root(2, remaining)] if remaining else [])
                result = analyze(0.8 + remaining, roots, [relation()])
                pillar = result['pillars']['year']
                self.assertEqual(pillar['current_status'], expected)
                self.assertEqual(pillar['effective_score'], remaining)
                self.assertEqual(pillar['score'], 0.8 + remaining)
                self.assertEqual(pillar['root_evidence'][0]['effective_score'], 0)
                self.assertEqual(pillar['is_transformed'], expected == '변허(變虛)')

    def test_weak_with_no_remaining_roots_stays_weak(self):
        pillar = analyze(0.3, [root(0, 0.3)], [relation()])['pillars']['year']
        self.assertEqual(pillar['effective_score'], 0)
        self.assertEqual(pillar['current_status'], '허(虛)')
        self.assertFalse(pillar['is_transformed'])
        self.assertIn('잔여 점수가 0이어도 허를 유지', pillar['reason'])

    def test_all_weak_summary_matches_distribution(self):
        result = analyze(0.3, [root(0, 0.3)], repeat=True)
        self.assertEqual(result['weak_count'], 4)
        self.assertIn('허(虛) 4개', result['overall_status'])
        self.assertNotIn('균형', result['overall_status'])

    def test_each_affecting_type_and_both_endpoints(self):
        for kind in ('충(沖)', '형(刑)', '천(穿)'):
            for index in (0, 1):
                with self.subTest(kind=kind, endpoint=index):
                    pillar = analyze(0.8, [root(index, 0.8)], [relation(kind)])['pillars']['year']
                    self.assertEqual(pillar['current_status'], '변허(變虛)')
                    self.assertIn(kind, pillar['reason'])
                    self.assertNotIn('충·형·천으로 손상', pillar['reason'])
                    self.assertEqual(pillar['root_evidence'][0]['interactions'][0]['type'], kind)

    def test_unrelated_or_unsupported_interactions_do_not_remove_roots(self):
        interactions = [
            relation('육합(六合)'), relation('파(破)'),
            relation(source='day', target='hour'),
            relation(source='all', target='all'),
            dict(category='천간', type='충(沖)', from_pillar='year', to_pillar='month'),
        ]
        pillar = analyze(0.8, [root(0, 0.8)], interactions)['pillars']['year']
        self.assertEqual(pillar['current_status'], '실(實)')
        self.assertEqual(pillar['effective_score'], 0.8)
        self.assertEqual(pillar['root_evidence'][0]['interactions'], [])

    def test_overlapping_interactions_keep_evidence_without_double_subtraction(self):
        clash = relation(weight=0.5, is_adjacent=False, name='자오충')
        punishment = relation('형(刑)', target='day')
        pillar = analyze(1.4, [root(0, 0.8), root(3, 0.6)], [clash, clash, punishment])['pillars']['year']
        self.assertEqual(pillar['effective_score'], 0.6)
        evidence = pillar['root_evidence'][0]
        self.assertEqual(len(evidence['interactions']), 2)
        self.assertEqual(evidence['interactions'][0]['weight'], 0.5)
        self.assertEqual(evidence['effective_score'], 0)
        self.assertEqual(pillar['reason'], ' '.join(pillar['transition_reasons']))

    def test_shared_root_explains_each_affected_stem(self):
        result = analyze(0.8, [root(1, 0.8)], [relation('형(刑)')], repeat=True)
        self.assertEqual(result['transformed_empty_count'], 4)
        self.assertEqual(result['weak_count'], 0)
        for pillar in result['pillars'].values():
            self.assertEqual(pillar['root_evidence'][0]['pillar'], 'month')
            self.assertIn('월지(午)', pillar['reason'])
            self.assertIn(pillar['position'], result['overall_status'])

    def test_schema_preserves_new_fields_and_separates_interpretation(self):
        result = analyze(0.8, [root(0, 0.8)], [relation()])
        encoded = XuShiDynamics.model_validate(result).model_dump(mode='json')
        self.assertEqual(encoded, result)
        self.assertEqual(encoded['analysis_scope'], 'natal')
        self.assertEqual(encoded['rule_version'], '1.0.0')
        self.assertEqual(sum(encoded[k] for k in ('real_count', 'transformed_empty_count', 'hollow_penetrate_count', 'weak_count')), 4)
        for pillar in encoded['pillars'].values():
            self.assertTrue(pillar['meaning'].startswith('전통적 해석 참고:'))
            self.assertNotIn('최적화', pillar['meaning'])
            self.assertNotIn('탁월', pillar['meaning'])

    def test_pre_change_regression_fixtures(self):
        path = Path(__file__).parent / 'fixtures' / 'xu_shi_v1.json'
        for case in json.loads(path.read_text()):
            with self.subTest(stems=case['stems'], branches=case['branches']):
                stems, branches = list(case['stems']), list(case['branches'])
                result = analyze_xu_shi_dynamics(
                    stems, branches, stems[2], analyze_advanced_tonggeun(stems, branches),
                    build_interaction_matrix(stems, branches, stems[2])['matrix'],
                )
                pillars = [result['pillars'][key] for key in PILLARS]
                self.assertEqual([p['score'] for p in pillars], case['scores'])
                self.assertEqual([p['original_status'] for p in pillars], case['original'])
                self.assertEqual([p['current_status'] for p in pillars], case['current'])
                self.assertEqual([result[k] for k in ('real_count', 'transformed_empty_count', 'hollow_penetrate_count')], case['counts'])
                for pillar in pillars:
                    self.assertEqual(pillar['is_transformed'], pillar['original_status'] != pillar['current_status'])
                    self.assertEqual(pillar['effective_score'], sum(root['effective_score'] for root in pillar['root_evidence']))
                XuShiDynamics.model_validate(result)


if __name__ == '__main__':
    unittest.main()
