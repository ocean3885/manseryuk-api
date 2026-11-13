"""상세 타입을 적용해도 원자료를 잃거나 선택 키를 생성하지 않아야 한다."""
from copy import deepcopy
from itertools import permutations, product
import unittest

from pydantic import TypeAdapter, ValidationError
from schemas.natal_analysis import NatalAnalysisDetails
from schemas.saju_analysis import InteractionsInfo
from services.analysis import analyze_palja_integrated
from services.interaction_matrix import build_interaction_matrix

DETAILS = TypeAdapter(NatalAnalysisDetails)


class NatalAnalysisContractTests(unittest.TestCase):
    def test_all_pair_types_and_group_formations_roundtrip_without_data_loss(self):
        cases = {a + b + '子子' for a, b in product('子丑寅卯辰巳午未申酉戌亥', repeat=2)}
        for group in ('寅午戌', '亥卯未', '申子辰', '巳酉丑',
                      '寅卯辰', '巳午未', '申酉戌', '亥子丑', '寅巳申', '丑戌未'):
            for repeated in group:
                cases.update(''.join(p) for p in permutations(group + repeated))
        cases.update(('巳亥卯未', '亥卯酉未', '亥卯未丑', '午子丑寅', '子午丑寅'))
        for branches in sorted(cases):
            with self.subTest(branches=branches):
                stems = list('甲己丙辛')
                raw = analyze_palja_integrated(stems, list(branches))['pillars']
                self.assertEqual(DETAILS.validate_python(raw), raw)
                matrix = build_interaction_matrix(stems, list(branches), stems[2])
                encoded = InteractionsInfo.model_validate(matrix).model_dump()
                for original, row in zip(matrix['matrix'], encoded['matrix']):
                    self.assertEqual(row['condition_evidence'], original.get('condition_evidence', {}))

    def test_missing_pillar_wrong_relation_types_and_unknown_fields_are_rejected(self):
        raw = analyze_palja_integrated(list('甲己丙辛'), list('午未子丑'))['pillars']
        for path, value in (
            (('year', 'stem', 'relations', 'combinations'), {}),
            (('year', 'branch', 'relations', 'six_haps', 0, 'activation_status'), 'active'),
            (('year', 'stem', 'external_support_score'), 'not-a-number'),
            (('year', 'branch', 'relations', 'unknown_bucket'), []),
        ):
            with self.subTest(path=path):
                changed = deepcopy(raw)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                with self.assertRaises(ValidationError):
                    DETAILS.validate_python(changed)
        missing = deepcopy(raw)
        del missing['hour']
        with self.assertRaises(ValidationError):
            DETAILS.validate_python(missing)

    def test_empty_relations_and_null_self_combination_remain_explicit(self):
        raw = analyze_palja_integrated(list('甲甲甲甲'), list('子子子子'))['pillars']
        actual = DETAILS.validate_python(raw)
        self.assertEqual(actual, raw)
        for pillar in actual.values():
            self.assertIsNone(pillar['jahab'])
            self.assertTrue(all(items == [] for items in pillar['branch']['relations'].values()))
