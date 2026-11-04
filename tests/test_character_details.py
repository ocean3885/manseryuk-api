"""Unified API fidelity, reference integrity and future-context contract checks."""
from copy import deepcopy
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from routers.root import get_calenda_data
from schemas.character_details import CharacterDetails
from services.character_details import assemble_character_details

QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')
DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class CharacterDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        with Session(cls.engine) as session:
            cls.response = get_calenda_data(**QUERY, db=session)
        cls.graph = assemble_character_details(cls.response)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_adapter_preserves_sources_and_repeated_positions(self):
        before = deepcopy(self.response)
        graph = assemble_character_details(self.response)
        self.assertEqual(self.response, before)
        self.assertEqual(len(graph['characters']), 8)
        for position in ('year', 'month', 'day', 'hour'):
            for kind, source in [('stem', 'gan'), ('branch', 'ji')]:
                node = graph['characters'][f'natal.chart.{position}.{kind}']
                self.assertEqual(node['attributes'], self.response['four_pillars'][position][source])
                self.assertEqual(node['analysis'], self.response['analysis']['details'][position][kind])
                for rid in node['relation_ids']:
                    self.assertIn(f'natal.chart.{position}.{kind}', graph['relations'][rid]['participants'])
                if kind == 'stem':
                    self.assertEqual(node['rooting']['root_impact_status'], 'not_evaluated')
                else:
                    self.assertIsNone(node['rooting'])
                    self.assertEqual(node['pillar_attributes']['jijanggan'],
                                     self.response['four_pillars'][position]['jijanggan'])
        self.assertTrue(any(n['transmission_relation_ids'] for n in graph['characters'].values()))
        self.assertEqual(graph['coverage']['not_evaluated_scopes'], ['daewoon', 'sewoon'])

    def test_invalid_references_and_rooting_are_rejected(self):
        for defect in ('reference', 'direction', 'root', 'coverage'):
            graph = deepcopy(self.graph)
            if defect == 'reference':
                graph['characters']['natal.chart.year.stem']['relation_ids'].append('missing')
            elif defect == 'direction':
                row = next(r for r in graph['relations'].values() if r['direction'])
                row['direction']['to_character'] = 'sewoon.year_2026.year.stem'
            elif defect == 'root':
                graph['characters']['natal.chart.year.stem']['rooting']['root_branch_ids'] = ['missing']
            else:
                graph['coverage']['calculated_scopes'].append('sewoon')
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CharacterDetails.model_validate(graph)

    def test_future_context_and_cross_context_relation_do_not_collide(self):
        # Synthetic contract fixture only: no cycle detection or impact is claimed.
        graph = deepcopy(self.graph)
        graph['contexts']['sewoon.year_2026'] = dict(
            scope='sewoon', instance='year_2026', label='2026 세운',
            calculation_status='not_evaluated', selection={'year': 2026})
        original = 'natal.chart.year.branch'
        future = 'sewoon.year_2026.year.branch'
        node = deepcopy(graph['characters'][original])
        node.update(context_id='sewoon.year_2026', relation_ids=[], transmission_relation_ids=[])
        graph['characters'][future] = node
        row = dict(relation_id='fixture:cross_scope', type='same_branch',
                   participants=[original, future], context_ids=['natal.chart', 'sewoon.year_2026'],
                   activation_status='detected', source_relation_id='fixture:original',
                   source_refs=[dict(system='analysis_details', location='synthetic_contract_fixture')])
        graph['relations'][row['relation_id']] = row
        for key in (original, future):
            graph['characters'][key]['relation_ids'].append(row['relation_id'])
        graph['coverage']['detected_only_relation_ids'].append(row['relation_id'])
        # Three-layer groups use the same contract; no four-pillar assumption.
        graph['contexts']['daewoon.period_0'] = dict(
            scope='daewoon', instance='period_0', label='첫 대운',
            calculation_status='not_evaluated', selection={'index': 0})
        daewoon = 'daewoon.period_0.cycle.branch'
        node = deepcopy(graph['characters'][original])
        node.update(context_id='daewoon.period_0', position='cycle',
                    relation_ids=['fixture:group'], transmission_relation_ids=[])
        graph['characters'][daewoon] = node
        group = deepcopy(row)
        group.update(relation_id='fixture:group', type='trine',
                     participants=[original, future, daewoon],
                     context_ids=['natal.chart', 'sewoon.year_2026', 'daewoon.period_0'],
                     formation_candidates=[[original, future, daewoon]])
        graph['relations']['fixture:group'] = group
        graph['coverage']['detected_only_relation_ids'].append('fixture:group')
        for key in (original, future):
            graph['characters'][key]['relation_ids'].append('fixture:group')
        validated = CharacterDetails.model_validate(graph)
        self.assertEqual(validated.characters[original].char, validated.characters[future].char)
        self.assertNotEqual(original, future)

    def test_other_calendar_cases_preserve_relations(self):
        for params in [dict(year=1990, month='1', day='1', hour=12, min=0),
                       dict(year=2000, month='1', day='1', hour=8, min=15)]:
            with self.subTest(params=params), Session(self.engine) as session:
                response = get_calenda_data(**{**QUERY, **params}, db=session)
                graph = assemble_character_details(response)
                self.assertEqual(len(graph['characters']), 8)
                for rid, row in graph['relations'].items():
                    self.assertEqual(row['relation_id'], rid)
                    for participant in row['participants']:
                        self.assertIn(rid, graph['characters'][participant]['relation_ids'])

    def test_http_contract_and_validation(self):
        def readonly_db():
            with Session(self.engine) as session:
                yield session
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        try:
            with TestClient(app) as client:
                result = client.get('/character-details', params=QUERY)
                self.assertEqual(result.status_code, 200)
                self.assertEqual(CharacterDetails.model_validate(result.json()).model_dump(mode='json'), self.graph)
                bad = {**QUERY, 'month': 'bad'}
                self.assertEqual(client.get('/character-details', params=bad).status_code, 400)
                self.assertEqual(client.get('/character-details').status_code, 422)
                self.assertEqual(client.get('/', params=QUERY).json()['four_pillars'], self.response['four_pillars'])
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
