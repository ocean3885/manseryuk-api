"""신살의 기준 누락·중복과 기준 글자의 위치를 검증한다."""
from copy import deepcopy
import unittest

from schemas.saju_analysis import SpecialStarItem
from services.special_stars import analyze_special_stars


def stars(stems, branches, name):
    return [r for r in analyze_special_stars(list(stems), list(branches)) if r['name'] == name]


class SpecialStarsTests(unittest.TestCase):
    def test_year_and_day_branch_are_evaluated_independently(self):
        for name, branches, targets in (
            ('도화살', '申卯寅酉', {'month': ('day', '寅'), 'hour': ('year', '申')}),
            ('역마살', '申寅亥巳', {'month': ('year', '申'), 'hour': ('day', '亥')}),
            ('화개살', '申辰亥未', {'month': ('year', '申'), 'hour': ('day', '亥')}),
        ):
            with self.subTest(name=name):
                rows = stars('甲丙戊庚', branches, name)
                self.assertEqual({r['pillar'] for r in rows}, set(targets))
                for row in rows:
                    pillar, char = targets[row['pillar']]
                    self.assertEqual(row['basis'], [dict(pillar=pillar, kind='branch', char=char,
                        display_name=f"{'일' if pillar == 'day' else '년'}지 {char}")])

    def test_same_target_combines_both_bases_but_preserves_repeated_positions(self):
        rows = stars('甲丙戊庚', '申酉子酉', '도화살')
        self.assertEqual([r['pillar'] for r in rows], ['month', 'hour'])
        for row in rows:
            self.assertEqual([(b['pillar'], b['char']) for b in row['basis']],
                             [('day', '子'), ('year', '申')])
        self.assertEqual(len({(r['name'], r['pillar']) for r in rows}), len(rows))

    def test_cheon_eul_keeps_both_stem_bases_including_same_glyphs(self):
        rows = stars('丙乙甲戊', '亥丑寅未', '천을귀인')
        self.assertEqual({r['pillar']: [b['pillar'] for b in r['basis']] for r in rows},
                         {'year': ['year'], 'month': ['day'], 'hour': ['day']})
        same = stars('甲乙甲戊', '丑子寅未', '천을귀인')
        self.assertTrue(all([b['pillar'] for b in r['basis']] == ['day', 'year'] for r in same))

    def test_day_stem_only_rules_do_not_acquire_year_stem_targets(self):
        # 년간 丙의 문창 申·양인 午·홍염 寅을 일간 甲의 규칙에 섞지 않는다.
        self.assertEqual(stars('丙乙甲戊', '申子寅酉', '문창귀인'), [])
        self.assertEqual(stars('丙乙甲戊', '午子寅酉', '양인살'), [])
        self.assertEqual(stars('丙乙甲戊', '寅子辰酉', '홍염살'), [])
        for name, branches in [('문창귀인', '巳子寅酉'), ('양인살', '卯子寅酉'), ('홍염살', '午子寅酉')]:
            rows = stars('丙乙甲戊', branches, name)
            self.assertEqual([r['pillar'] for r in rows], ['year'])
            self.assertEqual([(b['pillar'], b['kind'], b['char']) for b in rows[0]['basis']],
                             [('day', 'stem', '甲')])

    def test_pair_stars_identify_the_actual_own_pillar(self):
        stems, branches = '甲庚庚壬', '辰辰戌辰'
        for name, expected in [('백호살', {'year'}), ('괴강살', {'month', 'day', 'hour'})]:
            rows = stars(stems, branches, name)
            self.assertEqual({r['pillar'] for r in rows}, expected)
            for row in rows:
                self.assertEqual(row['basis'][0]['pillar'], row['pillar'])
                self.assertEqual(row['basis'][0]['kind'], 'pillar')
                self.assertEqual(row['basis'][0]['char'], row['char'])

    def test_every_detection_has_preserved_basis_and_symbolic_scope(self):
        stems, branches = list('甲庚庚壬'), list('辰辰戌辰')
        before = deepcopy((stems, branches))
        rows = analyze_special_stars(stems, branches)
        for row in rows:
            self.assertTrue(row['rule_id'].startswith('special_star:'))
            self.assertEqual(row['interpretation_scope'], 'traditional_symbolism')
            self.assertTrue(row['description'].startswith('전통적 상징:'))
            self.assertEqual(SpecialStarItem.model_validate(row).model_dump(), row)
        self.assertEqual((stems, branches), before)
