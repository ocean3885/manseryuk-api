"""루트 결과의 API별 전달, 미평가 정책, 선택 메타데이터의 일관성."""
from copy import deepcopy
from pathlib import Path
import unittest

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from schemas.character_details import CharacterDetails
from schemas.character_relation_index import CharacterRelationIndex
from schemas.cycle_analysis import CycleAnalysis

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class ApiProjectionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        def readonly_db():
            with Session(self.engine) as session:
                yield session
        self.previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        if self.previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = self.previous

    def get(self, path, query=None, **selector):
        response = self.client.get(path, params={**(query or QUERY), **selector})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def test_six_calendar_inputs_preserve_root_facts_across_all_projections(self):
        for changes in ({}, dict(year=1990, month='1', day='8', hour=18, min=0),
                        dict(year=2023, month='2', day='1', hour=0, min=0, sl='lun_y', gen='여'),
                        dict(year=2000, month='2', day='29', hour=23, min=59),
                        dict(year=1990, month='1', day='1', hour=12, min=0, gen='여'),
                        dict(year=2023, month='2', day='1', hour=0, min=0, sl='lun')):
            query = {**QUERY, **changes}
            with self.subTest(query=query):
                root = self.get('/', query)
                index = self.get('/relation-index', query)
                natal = self.get('/character-details', query)
                self.assertEqual({r['relation_id'] for r in index['relations']},
                                 {r['source_relation_id'] for r in natal['relations'].values()})
                for pillar, details in root['analysis']['details'].items():
                    for kind in ('stem', 'branch'):
                        key = f'natal.chart.{pillar}.{kind}'
                        self.assertEqual(natal['characters'][key]['analysis'], details[kind])
                        field = 'gan' if kind == 'stem' else 'ji'
                        self.assertEqual(natal['characters'][key]['attributes'], root['four_pillars'][pillar][field])
                    state = index['characters'][f'{pillar}.stem']['stem_state']
                    source = root['advanced_analysis']['xu_shi_dynamics']['pillars'][pillar]
                    self.assertEqual(state['root_score'], source['score'])
                    self.assertEqual(state['current_status'], source['current_status'])
                for selector in ({'daewoon_index': 0}, {'daewoon_index': 9},
                                 {'sewoon_year': query['year']},
                                 {'sewoon_year': root['daewoon']['list'][1]['selection_start_year']}):
                    cycle = self.get('/cycle-analysis', query, **selector)
                    for key, node in natal['characters'].items():
                        for field in ('analysis', 'attributes', 'pillar_attributes', 'rooting'):
                            self.assertEqual(cycle['characters'][key][field], node[field])
                    for key, relation in natal['relations'].items():
                        self.assertEqual(cycle['relations'][key], relation)
                    for node in cycle['characters'].values():
                        if node['context_id'] != 'natal.chart':
                            self.assertEqual(node['analysis'], dict(calculation_status='candidates_detected',
                                                                   root_impact_status='not_evaluated'))
                            self.assertIsNone(node['rooting'])

    def test_relation_index_rejects_unevaluated_root_changes_and_foreign_own_root(self):
        original = self.get('/relation-index')
        key = next(key for key, node in original['characters'].items()
                   if node['stem_state'] and node['stem_state']['has_same_pillar_root'])
        for defect in ('remaining', 'status', 'affected', 'own_root', 'external_root'):
            changed = deepcopy(original)
            state = changed['characters'][key]['stem_state']
            own = key.replace('.stem', '.branch')
            if defect == 'remaining':
                state['remaining_score'] = 0
            elif defect == 'status':
                state['current_status'] = '변허(變虛)'
            elif defect == 'affected':
                state['affected_root_branch_ids'] = [own]
            elif defect == 'own_root':
                state['root_branch_ids'] = [next(k for k in changed['characters'] if k.endswith('.branch') and k != own)]
                state['external_support_branch_ids'] = []
            else:
                state['external_support_branch_ids'] = [own]
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CharacterRelationIndex.model_validate(changed)

    def test_natal_analysis_rejects_missing_or_inconsistent_typed_data(self):
        original = self.get('/character-details')
        branch_key = next(k for k, n in original['characters'].items()
                          if n['kind'] == 'branch' and n['analysis']['storehouse'])
        for defect in ('storehouse', 'role', 'extra', 'analysis_char', 'missing_root', 'root_score'):
            graph = deepcopy(original)
            branch = graph['characters'][branch_key]['analysis']
            if defect == 'storehouse':
                del branch['storehouse']
            elif defect == 'role':
                role = branch['storehouse']['role']
                branch['storehouse']['role'] = '비겁고' if role != '비겁고' else '재고'
            elif defect == 'extra':
                branch['storehouse']['is_open'] = True
            elif defect == 'analysis_char':
                branch['char'] = '子' if branch['char'] != '子' else '午'
            elif defect == 'missing_root':
                graph['characters']['natal.chart.day.stem']['rooting'] = None
            else:
                graph['characters']['natal.chart.day.stem']['analysis']['score'] += 1
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CharacterDetails.model_validate(graph)

    def test_empty_or_incomplete_natal_context_is_rejected(self):
        graph = self.get('/character-details')
        graph['relations'] = {}
        graph['characters'] = {}
        graph['coverage']['detected_only_relation_ids'] = []
        with self.assertRaises(ValidationError):
            CharacterDetails.model_validate(graph)
        graph['contexts'] = {}
        graph['coverage']['calculated_scopes'] = []
        graph['coverage']['not_evaluated_scopes'] = ['natal', 'daewoon', 'sewoon']
        with self.assertRaises(ValidationError):
            CharacterDetails.model_validate(graph)

    def test_cycle_rejects_selection_metadata_and_calculation_scope_mismatches(self):
        root = self.get('/')
        year = root['daewoon']['list'][1]['selection_start_year']
        original = self.get('/cycle-analysis', sewoon_year=year)
        dae_id = f"daewoon.period_{original['selection']['daewoon_index']}"
        for defect in ('index', 'range', 'year', 'year_basis', 'analysis', 'rooting', 'scope_status'):
            graph = deepcopy(original)
            if defect == 'index':
                graph['contexts'][dae_id]['selection']['index'] += 1
            elif defect == 'range':
                graph['contexts'][dae_id]['selection']['selection_end_year_exclusive'] = year
            elif defect == 'year':
                graph['contexts'][f'sewoon.year_{year}']['selection']['year'] += 1
            elif defect == 'year_basis':
                graph['contexts'][f'sewoon.year_{year}']['selection']['year_basis'] = 'unimplemented_ipchun'
            elif defect == 'analysis':
                graph['characters'][f'{dae_id}.cycle.branch']['analysis']['calculation_status'] = 'not_evaluated'
            elif defect == 'scope_status':
                graph['contexts'][dae_id]['calculation_status'] = 'not_evaluated'
                for node in graph['characters'].values():
                    if node['context_id'] == dae_id:
                        node['analysis'] = {'calculation_status': 'not_evaluated'}
                graph['coverage']['calculated_scopes'].remove('daewoon')
                graph['coverage']['not_evaluated_scopes'].append('daewoon')
            else:
                graph['characters'][f'{dae_id}.cycle.stem']['rooting'] = deepcopy(graph['characters']['natal.chart.day.stem']['rooting'])
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CycleAnalysis.model_validate(graph)

    def test_openapi_exposes_typed_natal_and_cycle_analysis(self):
        schemas = self.client.get('/openapi.json').json()['components']['schemas']
        alternatives = schemas['CharacterDetail']['properties']['analysis']['anyOf']
        self.assertEqual({item['$ref'].rsplit('/', 1)[1] for item in alternatives},
                         {'RawStemAnalysis', 'RawBranchAnalysis', 'CycleCharacterAnalysis'})
        self.assertIn('storehouse', schemas['RawBranchAnalysis']['required'])
        self.assertEqual(set(schemas['StemRootingState']['properties']['current_status']['enum']),
                         {'실(實)', '허투(虛透)'})
