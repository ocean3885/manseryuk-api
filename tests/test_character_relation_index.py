"""8글자 조회 계약의 위치·그룹·참조 정합성 검사."""

import copy
import unittest

from pydantic import ValidationError

from schemas.character_relation_index import (
    CHARACTER_IDS, NOT_EVALUATED_MECHANISMS, CharacterRelationIndex,
)


def payload(stems='乙己己庚', branches='巳丑未午', relations=()):
    rows = list(relations)
    characters = {
        f'{pillar}.{component}': {
            'char': (stems if component == 'stem' else branches)[index],
            'relation_ids': [],
            'stem_state': ({
                'original_status': '허투(虛透)',
                'current_status': '허투(虛透)',
                'root_score': 0.0,
                'has_same_pillar_root': False,
                'remaining_score': 0.0,
                'root_branch_ids': [],
                'affected_root_branch_ids': [],
                'external_support_score': 0.0,
                'external_support_branch_ids': [],
                'source_rule_version': '3.0.0',
                'root_scope': 'same_pillar_only',
                'validation_status': 'provisional',
            } if component == 'stem' else None),
        }
        for index, pillar in enumerate(('year', 'month', 'day', 'hour'))
        for component in ('stem', 'branch')
    }
    for row in rows:
        for participant in row['participants']:
            characters[participant]['relation_ids'].append(row['relation_id'])
    assert set(characters) == set(CHARACTER_IDS)
    return {
        'schema_version': '1.7-draft', 'characters': characters, 'relations': rows,
        'coverage': {
            'rule_scope': 'registered_rules_partial',
            'transmission_basis': 'jijanggan_detailed_exact_match',
            'detected_only_relation_ids': [row['relation_id'] for row in rows
                                           if row['activation_status'] == 'detected'],
            'not_evaluated_mechanisms': list(NOT_EVALUATED_MECHANISMS),
            'power_effects_included': False,
        },
    }


def relation(relation_id, kind, participants, *, status='detected',
             reason=None, direction=None, formations=(), sources=None):
    return {
        'relation_id': relation_id, 'type': kind,
        'participants': participants, 'activation_status': status,
        'status_reason': reason, 'direction': direction,
        'formation_candidates': list(formations), 'rule_ids': [],
        'source_refs': sources or [
            {'system': 'interaction_matrix', 'relation_id': 'legacy:example'}],
    }


class CharacterRelationIndexTests(unittest.TestCase):
    def test_same_pillar_root_flag_must_match_root_evidence(self):
        incorrect = payload()
        incorrect['characters']['month.stem']['stem_state'][
            'has_same_pillar_root'] = True
        with self.assertRaisesRegex(ValidationError, '동주 통근 여부'):
            CharacterRelationIndex.model_validate(incorrect)

    def test_same_character_different_positions_have_distinct_relations(self):
        rows = [
            relation('stem:control:year:month', 'control',
                     ['year.stem', 'month.stem'],
                     direction={'from_character': 'year.stem',
                                'to_character': 'month.stem', 'basis': 'elemental'}),
            relation('stem:control:year:day', 'control',
                     ['year.stem', 'day.stem'],
                     direction={'from_character': 'year.stem',
                                'to_character': 'day.stem', 'basis': 'elemental'}),
            relation('branch:clash:month:day', 'clash',
                     ['month.branch', 'day.branch'], status='active'),
            relation('group:square:si_wu_wei', 'square',
                     ['year.branch', 'day.branch', 'hour.branch'],
                     status='potential', formations=[
                         ['year.branch', 'day.branch', 'hour.branch']]),
        ]
        result = CharacterRelationIndex.model_validate(payload(relations=rows))
        self.assertEqual(result.characters['year.stem'].relation_ids,
                         ['stem:control:year:month', 'stem:control:year:day'])
        self.assertEqual(result.characters['day.branch'].relation_ids,
                         ['branch:clash:month:day', 'group:square:si_wu_wei'])
        self.assertEqual(result.characters['hour.stem'].relation_ids, [])

    def test_orphan_reference_and_duplicate_relation_are_rejected(self):
        row = relation('branch:clash:month:day', 'clash',
                       ['month.branch', 'day.branch'], status='active')
        missing = payload(relations=[row])
        missing['characters']['month.branch']['relation_ids'] = []
        with self.assertRaisesRegex(ValidationError, '글자별 참조'):
            CharacterRelationIndex.model_validate(missing)

        duplicate = payload(relations=[row, copy.deepcopy(row)])
        with self.assertRaisesRegex(ValidationError, '중복 관계 ID'):
            CharacterRelationIndex.model_validate(duplicate)

        wrong_character = payload(relations=[row])
        wrong_character['characters']['month.stem']['char'] = '丑'
        with self.assertRaisesRegex(ValidationError, '글자 종류'):
            CharacterRelationIndex.model_validate(wrong_character)

    def test_repeated_group_requires_each_position_formation(self):
        row = relation('group:trine:hai_mao_wei', 'trine',
                       ['year.branch', 'month.branch', 'day.branch', 'hour.branch'],
                       status='detected', formations=[
                           ['year.branch', 'month.branch', 'day.branch'],
                           ['month.branch', 'day.branch', 'hour.branch'],
                       ])
        result = CharacterRelationIndex.model_validate(
            payload('己丁辛己', '亥卯未亥', [row]))
        self.assertEqual(len(result.relations[0].formation_candidates), 2)
        self.assertEqual(result.characters['year.branch'].relation_ids,
                         result.characters['hour.branch'].relation_ids)

        missing = copy.deepcopy(row)
        missing['formation_candidates'].pop()
        with self.assertRaisesRegex(ValidationError, '성립 조합이 없는 위치'):
            CharacterRelationIndex.model_validate(
                payload('己丁辛己', '亥卯未亥', [missing]))

    def test_invalid_status_direction_and_missing_provenance_are_rejected(self):
        stem_hap = relation('stem:combine:year:hour', 'combine',
                            ['year.stem', 'hour.stem'], status='detected',
                            sources=[{'system': 'interaction_matrix',
                                      'relation_id': '천간:천간합:year,hour'}])
        CharacterRelationIndex.model_validate(payload(relations=[stem_hap]))

        conditional = copy.deepcopy(stem_hap)
        conditional['activation_status'] = 'conditional'
        with self.assertRaisesRegex(ValidationError, '상태 이유'):
            CharacterRelationIndex.model_validate(payload(relations=[conditional]))

        unsupported = copy.deepcopy(stem_hap)
        unsupported['activation_status'] = 'unassessed'
        with self.assertRaises(ValidationError):
            CharacterRelationIndex.model_validate(payload(relations=[unsupported]))

        bad_direction = copy.deepcopy(stem_hap)
        bad_direction['direction'] = {
            'from_character': 'year.stem', 'to_character': 'month.stem',
            'basis': 'rule_fixed',
        }
        with self.assertRaisesRegex(ValidationError, '방향의 출처와 대상'):
            CharacterRelationIndex.model_validate(payload(relations=[bad_direction]))

        missing_source = copy.deepcopy(stem_hap)
        missing_source['source_refs'] = []
        with self.assertRaises(ValidationError):
            CharacterRelationIndex.model_validate(payload(relations=[missing_source]))

    def test_pair_ids_and_same_pillar_endpoints_follow_position(self):
        same_pillar = relation('same_pillar:self_combine:year', 'self_combine',
                               ['year.stem', 'year.branch'], status='detected',
                               sources=[{'system': 'analysis_details',
                                         'location': 'analysis.details.year.jahab'}])
        CharacterRelationIndex.model_validate(
            payload('甲己己庚', '午丑未子', [same_pillar]))

        wrong = copy.deepcopy(same_pillar)
        wrong['participants'] = ['year.stem', 'month.branch']
        with self.assertRaisesRegex(ValidationError, '동주 관계 ID'):
            CharacterRelationIndex.model_validate(
                payload('甲己己庚', '午丑未子', [wrong]))

        wrong_pair = relation('branch:clash:year:day', 'clash',
                              ['year.branch', 'month.branch'], status='active')
        with self.assertRaisesRegex(ValidationError, '쌍 관계 ID'):
            CharacterRelationIndex.model_validate(payload(relations=[wrong_pair]))

    def test_coverage_must_match_detected_relations_and_profile(self):
        row = relation('stem:combine:year:hour', 'combine',
                       ['year.stem', 'hour.stem'])
        valid = payload(relations=[row])
        CharacterRelationIndex.model_validate(valid)
        omitted = copy.deepcopy(valid)
        omitted['coverage']['detected_only_relation_ids'] = []
        with self.assertRaisesRegex(ValidationError, '탐지만 한 관계'):
            CharacterRelationIndex.model_validate(omitted)
        omitted = copy.deepcopy(valid)
        omitted['coverage']['not_evaluated_mechanisms'].pop()
        with self.assertRaisesRegex(ValidationError, '미평가 기전'):
            CharacterRelationIndex.model_validate(omitted)

    def test_stem_state_and_transmission_target_are_validated(self):
        row = relation('cross_layer:transmission:day:month', 'transmission',
                       ['month.stem', 'day.branch'],
                       direction={'from_character': 'day.branch',
                                  'to_character': 'month.stem',
                                  'basis': 'hidden_stem_match'})
        row['hidden_stem'] = '己'
        valid = payload(relations=[row])
        CharacterRelationIndex.model_validate(valid)

        wrong = copy.deepcopy(valid)
        wrong['relations'][0]['hidden_stem'] = '乙'
        with self.assertRaisesRegex(ValidationError, '대상 천간 글자'):
            CharacterRelationIndex.model_validate(wrong)

        wrong = copy.deepcopy(valid)
        wrong['characters']['month.stem']['stem_state'] = None
        with self.assertRaisesRegex(ValidationError, '천간 상태의 위치'):
            CharacterRelationIndex.model_validate(wrong)

        wrong = copy.deepcopy(valid)
        wrong['characters']['day.branch']['stem_state'] = valid['characters'][
            'month.stem']['stem_state']
        with self.assertRaisesRegex(ValidationError, '천간 상태의 위치'):
            CharacterRelationIndex.model_validate(wrong)


if __name__ == '__main__':
    unittest.main()
