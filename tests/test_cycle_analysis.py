"""Cycle selection boundaries and HTTP integration; no cycle relation claims."""
from copy import deepcopy
from pathlib import Path
import unittest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from routers.root import get_calenda_data
from services.character_details import assemble_character_details
from services.cycle_analysis import assemble_cycle_analysis
from schemas.cycle_analysis import CycleAnalysis

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class CycleAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        with Session(cls.engine) as session:
            cls.response = get_calenda_data(**QUERY, db=session)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_daewoon_preserves_natal_and_uses_existing_details(self):
        before = deepcopy(self.response)
        natal = assemble_character_details(self.response)
        for index in (0, 9):
            result = assemble_cycle_analysis(self.response, daewoon_index=index)
            self.assertEqual(len(result['characters']), 10)
            self.assertTrue(all(result['relations'][rid] == row for rid, row in natal['relations'].items()))
            for key, node in natal['characters'].items():
                self.assertEqual({k: v for k, v in result['characters'][key].items() if k not in ('relation_ids', 'transmission_relation_ids')}, {k: v for k, v in node.items() if k not in ('relation_ids', 'transmission_relation_ids')})
            item = self.response['daewoon']['list'][index]
            for kind, field in [('stem', 'gan_detail'), ('branch', 'ji_detail')]:
                node = result['characters'][f'daewoon.period_{index}.cycle.{kind}']
                self.assertEqual(node['attributes'], item[field])
                self.assertTrue(node['relation_ids'])
                self.assertIsNone(node['rooting'])
            self.assertEqual(result['coverage']['not_evaluated_scopes'], ['sewoon'])
            CycleAnalysis.model_validate(result)
        self.assertEqual(self.response, before)

    def test_sewoon_boundaries_use_next_start_not_legacy_end(self):
        # Force overlapping display years to verify the documented selection policy.
        response = deepcopy(self.response)
        for i, item in enumerate(response['daewoon']['list']):
            item['start_year'] = 1998 + 10 * i
            item['end_year'] = item['start_year'] + 10
        for year, expected in [(1997, None), (1998, 0), (2007, 0), (2008, 1), (2094, 9)]:
            with self.subTest(year=year):
                result = assemble_cycle_analysis(response, sewoon_year=year)
                self.assertEqual(result['selection']['daewoon_index'], expected)
                self.assertEqual(len(result['characters']), 10 if expected is None else 12)
                self.assertEqual(result['selection']['daewoon_status'],
                                 'before_first_period' if expected is None else 'selected')
                annual = next(c for c in response['cycles']['future_100'] if c['year'] == year)
                for kind, source in [('stem', 'gan'), ('branch', 'ji')]:
                    node = result['characters'][f'sewoon.year_{year}.cycle.{kind}']
                    self.assertEqual(node['attributes'], annual[source])
                    self.assertEqual(node['analysis']['calculation_status'], 'candidates_detected')
                if expected is not None:
                    selection = result['contexts'][f'daewoon.period_{expected}']['selection']
                    self.assertLessEqual(selection['selection_start_year'], year)
                    self.assertLess(year, selection['selection_end_year_exclusive'])

    def test_invalid_selections_and_missing_period_are_rejected(self):
        for selector in ({}, {'daewoon_index': 0, 'sewoon_year': 2000},
                         {'daewoon_index': -1}, {'daewoon_index': 10},
                         {'sewoon_year': 1994}, {'sewoon_year': 2095}):
            with self.subTest(selector=selector), self.assertRaises(HTTPException) as error:
                assemble_cycle_analysis(self.response, **selector)
            self.assertEqual(error.exception.status_code, 400)
        response = deepcopy(self.response)
        response['daewoon']['list'] = response['daewoon']['list'][:1]
        after = response['daewoon']['list'][0]['start_year'] + 10
        with self.assertRaises(HTTPException):
            assemble_cycle_analysis(response, sewoon_year=after)

    def test_current_daewoon_and_annual_selection_share_all_start_years(self):
        from services.daewoon import build_daewoon
        source = self.response['daewoon']
        data = [source['direction'], [p['gan'] for p in source['list']],
                [p['ji'] for p in source['list']]]
        for item in source['list']:
            year = item['start_year']
            if year not in {a['year'] for a in self.response['cycles']['future_100']}:
                continue
            with self.subTest(year=year):
                built = build_daewoon(data, source['start_age'], 1995,
                                      current_year=year, day_stem='癸')
                response = deepcopy(self.response)
                response['daewoon'] = built
                graph = assemble_cycle_analysis(response, sewoon_year=year)
                self.assertEqual(graph['selection']['daewoon_index'], built['current']['index'])

    def test_http_selection_contract_and_existing_route(self):
        def readonly_db():
            with Session(self.engine) as session:
                yield session
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        try:
            with TestClient(app) as client:
                for selector in [{'daewoon_index': 0}, {'sewoon_year': 2026}]:
                    response = client.get('/cycle-analysis', params={**QUERY, **selector})
                    self.assertEqual(response.status_code, 200)
                    graph = CycleAnalysis.model_validate(response.json())
                    self.assertEqual(graph.selection.cycle_relations_status, 'candidates_detected')
                    cross = [r for r in graph.relations.values() if r.relation_id.startswith('cycle:')]
                    self.assertTrue(cross)
                    for row in cross:
                        self.assertGreater(len(row.context_ids), 1)
                        self.assertNotEqual(row.activation_status, 'active')
                        for participant in row.participants:
                            self.assertIn(row.relation_id, graph.characters[participant].relation_ids)
                    if 'sewoon_year' in selector:
                        self.assertTrue(any(set(row.context_ids) == {
                            f'daewoon.period_{graph.selection.daewoon_index}', 'sewoon.year_2026'
                        } for row in cross))
                for selector in [{}, {'daewoon_index': 0, 'sewoon_year': 2026},
                                 {'daewoon_index': -1}]:
                    self.assertEqual(client.get('/cycle-analysis', params={**QUERY, **selector}).status_code, 400)
                self.assertEqual(client.get('/cycle-analysis', params={**QUERY, 'sewoon_year': 'bad'}).status_code, 422)
                original = client.get('/character-details', params=QUERY)
                self.assertEqual(original.status_code, 200)
                self.assertEqual(len(original.json()['characters']), 8)
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
