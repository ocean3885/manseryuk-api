"""관계 전용 조회 경로와 기존 원국 응답의 분리를 검증한다."""

from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from core.dependencies import get_db
from main import app
from schemas.character_relation_index import CharacterRelationIndex
from schemas.saju_analysis import SajuAnalysisResponse


DB_PATH = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = {
    'year': 1995, 'month': '5', 'day': '12',
    'hour': 14, 'min': 30, 'sl': 'sol', 'gen': '남',
}
QUERIES = (
    QUERY,
    {**QUERY, 'year': 1990, 'month': '1', 'day': '1', 'hour': 12, 'min': 0},
    {**QUERY, 'year': 2000, 'month': '1', 'day': '1', 'hour': 8, 'min': 15},
)


@unittest.skipUnless(DB_PATH.is_file(), '통합 검증에 필요한 달력 DB가 없습니다.')
class CharacterRelationIndexIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB_PATH}?mode=ro&uri=true')

        def readonly_db():
            with Session(cls.engine) as session:
                yield session

        cls.previous_override = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        if cls.previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = cls.previous_override
        cls.engine.dispose()

    def test_relation_route_returns_valid_index_with_existing_source_ids(self):
        old = self.client.get('/', params=QUERY)
        new = self.client.get('/relation-index', params=QUERY)
        self.assertEqual(old.status_code, 200)
        self.assertEqual(new.status_code, 200)
        original = SajuAnalysisResponse.model_validate(old.json())
        index = CharacterRelationIndex.model_validate(new.json())
        self.assertEqual(len(index.characters), 8)
        self.assertEqual(index.schema_version, '1.7-draft')
        self.assertNotIn('relation_index', old.json()['advanced_analysis'])
        legacy_ids = {item['relation_id'] for item in
                      old.json()['advanced_analysis']['interactions']['matrix']}
        for relation in index.relations:
            for source in relation.source_refs:
                if source.system == 'interaction_matrix':
                    self.assertIn(source.relation_id, legacy_ids)
        for pillar in ('year', 'month', 'day', 'hour'):
            self.assertIn(f'same_pillar:element:{pillar}',
                          {row.relation_id for row in index.relations})
            stem_state = index.characters[f'{pillar}.stem'].stem_state
            old_state = old.json()['advanced_analysis']['xu_shi_dynamics'][
                'pillars'][pillar]
            self.assertEqual(stem_state.original_status, old_state['original_status'])
            self.assertEqual(stem_state.current_status, old_state['current_status'])
            self.assertEqual(stem_state.root_impact_status, 'not_evaluated')
            self.assertIsNone(stem_state.root_impact_score)
            self.assertEqual(stem_state.remaining_score, stem_state.root_score)
            self.assertEqual(stem_state.affected_root_branch_ids, [])
            self.assertEqual(stem_state.root_score, old_state['score'])
            self.assertEqual(stem_state.has_same_pillar_root,
                             bool(old_state['root_evidence']))
            self.assertEqual(stem_state.remaining_score,
                             old_state['effective_score'])
            self.assertEqual(stem_state.root_scope,
                             'same_pillar_only')
            self.assertEqual(stem_state.external_support_score,
                             old.json()['analysis']['details'][pillar]['stem'][
                                 'external_support_score'])
        self.assertTrue(any(row.type == 'transmission' for row in index.relations))

    def test_querying_index_does_not_change_default_response(self):
        before = self.client.get('/', params=QUERY)
        self.assertEqual(self.client.get('/relation-index', params=QUERY).status_code, 200)
        after = self.client.get('/', params=QUERY)
        self.assertEqual(before.status_code, 200)
        self.assertEqual(before.json(), after.json())
        self.assertEqual(set(before.json()['advanced_analysis']),
                         set(after.json()['advanced_analysis']))

    def test_existing_validation_is_shared(self):
        invalid = {**QUERY, 'month': 'invalid'}
        original = self.client.get('/', params=invalid)
        relation = self.client.get('/relation-index', params=invalid)
        self.assertEqual(original.status_code, 400)
        self.assertEqual(relation.status_code, original.status_code)
        original_error, relation_error = original.json(), relation.json()
        self.assertTrue(original_error.pop('example').startswith('/?'))
        self.assertTrue(relation_error.pop('example').startswith('/relation-index?'))
        self.assertEqual(relation_error, original_error)

    def test_three_calendar_charts_match_all_matrix_ids_and_known_statuses(self):
        for query in QUERIES:
            with self.subTest(date=(query['year'], query['month'], query['day'])):
                original = self.client.get('/', params=query)
                indexed = self.client.get('/relation-index', params=query)
                self.assertEqual(original.status_code, 200)
                self.assertEqual(indexed.status_code, 200)
                raw = original.json()
                result = CharacterRelationIndex.model_validate(indexed.json())
                matrix = {item['relation_id']: item for item in
                          raw['advanced_analysis']['interactions']['matrix']}
                referenced = {}
                for relation in result.relations:
                    for source in relation.source_refs:
                        if source.system != 'interaction_matrix':
                            continue
                        self.assertIn(source.relation_id, matrix)
                        self.assertNotIn(source.relation_id, referenced)
                        referenced[source.relation_id] = relation
                        old_status = matrix[source.relation_id].get('activation_status')
                        if old_status is None:
                            self.assertEqual(relation.activation_status, 'detected')
                        elif (relation.type != 'half_combine' or
                              relation.activation_status != 'candidate_only'):
                            self.assertEqual(relation.activation_status, old_status)
                self.assertEqual(set(referenced), set(matrix))
                detected = [relation.relation_id for relation in result.relations
                            if relation.activation_status == 'detected']
                self.assertEqual(result.coverage.detected_only_relation_ids, detected)
                self.assertEqual(result.coverage.rule_scope,
                                 'registered_rules_partial')
                self.assertEqual(result.coverage.transmission_basis,
                                 'jijanggan_detailed_exact_match')
                self.assertFalse(result.coverage.power_effects_included)


if __name__ == '__main__':
    unittest.main()
