"""Term lookup and calendar/display contracts for the base API."""
from datetime import date
from pathlib import Path
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from models.calenda_data import CalendaData
from services.daewoon import daewoonNum, build_daewoon

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')


class TermLookupTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        CalendaData.__table__.create(self.engine)
        self.session = Session(self.engine)

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def terms(self, entries):
        for index, name in entries:
            self.session.add(CalendaData(cd_no=index, cd_sy=2020, cd_sm='1',
                                         cd_sd=str(index % 28 + 1), cd_kterms=name))
        self.session.commit()

    def test_nearest_forward_term_is_selected_regardless_of_insertion_order(self):
        self.terms([(120, '경칩'), (105, '입춘'), (96, '소한'), (102, '춘분')])
        self.assertEqual(daewoonNum(100, '순행', self.session), 1.7)

    def test_nearest_backward_term_is_selected(self):
        self.terms([(80, '소한'), (95, '입춘'), (120, '경칩'), (99, '춘분')])
        self.assertEqual(daewoonNum(100, '역행', self.session), 1.7)

    def test_missing_term_does_not_fabricate_one_year_start(self):
        self.terms([(100, '입춘'), (96, '소한'), (140, '경칩')])
        # Same-day terms and terms outside the existing 35-day window remain excluded.
        self.assertIsNone(daewoonNum(100, '순행', self.session))
        self.assertIsNone(daewoonNum(60, '역행', self.session))
        result = build_daewoon(['순행', ['甲'], ['子']], None, 2000,
                               current_year=2026, day_stem='甲')
        self.assertIsNone(result['start_age'])
        self.assertEqual(result['start_age_status'], 'term_data_unavailable')
        self.assertEqual(result['selection_status'], 'unavailable')
        self.assertIsNone(result['current'])
        self.assertEqual(result['list'], [])

    def test_genuine_one_year_start_is_still_a_calculated_result(self):
        self.terms([(103, '입춘')])
        age = daewoonNum(100, '순행', self.session)
        self.assertEqual(age, 1.0)
        result = build_daewoon(['순행', ['甲'], ['子']], age, 2000,
                               current_year=2001, day_stem='甲')
        self.assertEqual(result['start_age_status'], 'calculated')
        self.assertEqual(result['current']['age'], 2)
        self.assertEqual(result['current']['age_basis'], 'counting_age')


class ReferenceDate(date):
    @classmethod
    def today(cls):
        return date(2026, 11, 13)


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class RootResponseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def setUp(self):
        def readonly_db():
            with Session(self.engine) as db:
                yield db
        self.previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        self.clock = patch('services.saju_orchestrator.date', ReferenceDate)
        self.clock.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.clock.stop()
        if self.previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = self.previous

    def get(self, **changes):
        result = self.client.get('/', params={**QUERY, **changes})
        self.assertEqual(result.status_code, 200, result.text)
        return result.json()

    def test_relation_scores_and_derived_judgments_are_absent_from_http(self):
        advanced = self.get()['advanced_analysis']
        interactions = advanced['interactions']
        self.assertEqual(set(interactions), {'rule_version', 'matrix'})
        removed = {'score', 'score_contribution', 'score_covered_by'}
        self.assertTrue(interactions['matrix'])
        for row in interactions['matrix']:
            self.assertTrue(removed.isdisjoint(row))
        for state in advanced['xu_shi_dynamics']['pillars'].values():
            # 통근 점수는 유지하고, 원본 관계를 전달하는 곳에서도 관계 점수는 제거한다.
            self.assertIn('score', state)
            self.assertIn('effective_score', state)
            for row in state['related_interactions']:
                self.assertTrue(removed.isdisjoint(row))
        bin_zhu = advanced['bin_zhu_dynamics']
        self.assertTrue({'pairwise_scores', 'group_cohesion_score', 'control_flow',
                         'ai_prompt_bullets'}.isdisjoint(bin_zhu))
        by_id = {r['relation_id']: r for r in interactions['matrix']}
        for row in bin_zhu['guest_host_links']:
            self.assertEqual(row['activation_status'], by_id[row['relation_id']]['activation_status'])
            self.assertEqual(row['type'], by_id[row['relation_id']]['type'])
            for member in ('guest', 'host'):
                self.assertTrue({'pillar', 'char', 'ten_god', 'display_name'} <= row[member].keys())
        self.assertTrue(advanced['five_elements']['scores'])
        for prompt in advanced['ai_consultation_prompts']:
            self.assertFalse(prompt.startswith(('【사주 기후】', '【빈주', '【주-빈 통로】')))

    def test_openapi_matches_retired_relation_score_contract(self):
        schemas = self.client.get('/openapi.json').json()['components']['schemas']
        for model, removed in {
            'InteractionsInfo': {'tension_score', 'harmony_score', 'climate', 'summary_list'},
            'AnalysisSummary': {'total_energy_balance'},
            'InteractionItem': {'score', 'score_contribution', 'score_covered_by'},
            'BinZhuDynamics': {'pairwise_scores', 'group_cohesion_score', 'control_flow'},
            'BinZhuLink': {'mechanism', 'flow_direction', 'weight', 'target_guest', 'source_host'},
            'BinZhuGroupConnection': {'cohesion_score', 'included_in_score'},
            'BranchGroupPairOverlap': {'covered_in_harmony_score'},
        }.items():
            with self.subTest(model=model):
                self.assertTrue(removed.isdisjoint(schemas[model]['properties']))
        self.assertNotIn('ControlFlow', schemas)
        self.assertNotIn('BinZhuScores', schemas)
        self.assertIn('rooting_summary', schemas['AnalysisSummary']['required'])

    def test_summary_matches_relation_and_rooting_facts_without_duplicate_copy(self):
        body = self.get()
        summary = body['analysis']['summary']
        advanced = body['advanced_analysis']
        matrix = advanced['interactions']['matrix']
        self.assertEqual(set(summary), {'branch_interactions', 'stem_interactions', 'rooting_summary'})
        self.assertEqual(len(summary['branch_interactions']),
                         sum(item['category'] == '지지' for item in matrix))
        for field in ('branch_interactions', 'stem_interactions'):
            self.assertEqual(len(summary[field]), len(set(summary[field])))
        rooted = advanced['xu_shi_dynamics']['real_count']
        self.assertIn(f'동주 통근 {rooted}개', summary['rooting_summary'])
        self.assertIn(f'동주 무근 {4 - rooted}개', summary['rooting_summary'])
        self.assertNotIn('summary_list', advanced['interactions'])
        prompts = [p for p in advanced['ai_consultation_prompts'] if p.startswith('【주요 상호작용】')]
        self.assertEqual(prompts, [f"【주요 상호작용】 {r['description']}" for r in matrix[:3]])

    def test_special_star_basis_and_count_labels_survive_http(self):
        body = self.get()
        advanced = body['advanced_analysis']
        stars = advanced['special_stars']
        self.assertTrue(stars)
        for item in stars:
            self.assertTrue(item['basis'])
            self.assertTrue(item['rule_id'].startswith('special_star:'))
            self.assertEqual(item['interpretation_scope'], 'traditional_symbolism')
            for basis in item['basis']:
                pillar = body['four_pillars'][basis['pillar']]
                expected = (pillar['gan']['ch'] if basis['kind'] == 'stem' else
                            pillar['ji']['ch'] if basis['kind'] == 'branch' else
                            pillar['gan']['ch'] + pillar['ji']['ch'])
                self.assertEqual(basis['char'], expected)
        self.assertEqual(len({(r['name'], r['pillar']) for r in stars}), len(stars))
        for pillar in ('year', 'month', 'day', 'hour'):
            expected = [r['name'] for r in stars if r['pillar'] == pillar]
            self.assertEqual(body['four_pillars'][pillar]['special_stars'], expected)
            self.assertEqual(advanced['special_stars_by_pillar'][pillar], expected)
        elements = advanced['five_elements']
        self.assertNotIn('dominant', elements)
        self.assertNotIn('deficient', elements)
        self.assertEqual(elements['frequent_elements'], [e for e, n in elements['counts'].items() if n >= 3])
        self.assertEqual(elements['absent_elements'], [e for e, n in elements['counts'].items() if n == 0])

    def test_basic_storehouse_classification_survives_http_and_natal_adapters(self):
        body = self.get()
        details = body['analysis']['details']
        storehouses = {p: d['branch']['storehouse'] for p, d in details.items()}
        self.assertTrue(any(value is not None for value in storehouses.values()))
        self.assertTrue(any(value is None for value in storehouses.values()))
        for path, selector in [('/character-details', {}),
                               ('/cycle-analysis', {'daewoon_index': 1})]:
            response = self.client.get(path, params={**QUERY, **selector})
            self.assertEqual(response.status_code, 200, response.text)
            graph = response.json()
            for pillar, expected in storehouses.items():
                analysis = graph['characters'][f'natal.chart.{pillar}.branch']['analysis']
                self.assertEqual(analysis['storehouse'], expected)
                self.assertEqual(analysis, details[pillar]['branch'])
                if expected is not None:
                    self.assertEqual(set(expected), {'stored_element', 'role'})

    def test_openapi_describes_nested_analysis_and_symbolic_scope(self):
        schemas = self.client.get('/openapi.json').json()['components']['schemas']
        self.assertTrue(schemas['AnalysisInfo']['properties']['details']['$ref'].endswith('/NatalAnalysisDetails'))
        details = schemas['NatalAnalysisDetails']
        self.assertEqual(set(details['required']), {'year', 'month', 'day', 'hour'})
        self.assertFalse(details['additionalProperties'])
        for value in schemas['RawBranchRelations']['properties'].values():
            self.assertEqual(value['type'], 'array')
            self.assertIn('$ref', value['items'])
        self.assertTrue({'rule_id', 'basis', 'interpretation_scope'} <=
                        set(schemas['SpecialStarItem']['required']))
        self.assertIn('storehouse', schemas['RawBranchAnalysis']['required'])
        self.assertEqual(set(schemas['StorehouseInfo']['properties']), {'stored_element', 'role'})
        self.assertFalse(schemas['StorehouseInfo']['additionalProperties'])

    def test_raw_relations_survive_http_and_unified_character_adapters(self):
        base = self.get()
        for path, selector in [('/character-details', {}),
                               ('/cycle-analysis', {'daewoon_index': 1})]:
            result = self.client.get(path, params={**QUERY, **selector})
            self.assertEqual(result.status_code, 200, result.text)
            graph = result.json()
            for pillar in ('year', 'month', 'day', 'hour'):
                for kind in ('stem', 'branch'):
                    raw = base['analysis']['details'][pillar][kind]
                    node = graph['characters'][f'natal.chart.{pillar}.{kind}']
                    self.assertEqual(node['analysis'], raw)
                    relations = raw['relations']
                    self.assertNotIn('six_haps_all', relations)
                    for bucket, value in relations.items():
                        lists = value.values() if bucket == 'restrain' else [value]
                        for entries in lists:
                            self.assertIsInstance(entries, list)
                            for item in entries:
                                self.assertIn('activation_status', item)
                                self.assertIsInstance(item['status_reasons'], list)
                                self.assertEqual(item['impact_status'], 'not_evaluated')
                                self.assertNotIn('strength', item)
                                self.assertNotIn('combined_element', item)

    def test_lunar_flag_comes_from_calendar_record_for_lunar_and_solar_requests(self):
        normal = self.get(year=2023, month='2', day='1', sl='lun')
        leap = self.get(year=2023, month='2', day='1', sl='lun_y')
        self.assertFalse(normal['calendar']['lunar']['is_leap_month'])
        self.assertTrue(leap['calendar']['lunar']['is_leap_month'])
        self.assertEqual(normal['calendar']['solar'], dict(year=2023, month='2', day='20'))
        self.assertEqual(leap['calendar']['solar'], dict(year=2023, month='3', day='22'))
        solar = self.get(year=2023, month='3', day='22')
        self.assertEqual(solar['calendar']['lunar'], leap['calendar']['lunar'])
        self.assertEqual(solar['four_pillars'], leap['four_pillars'])

    def test_self_combination_facts_survive_all_http_paths(self):
        base = self.get()
        registered = {p: details['jahab'] for p, details in base['analysis']['details'].items()
                      if details['jahab'] is not None}
        self.assertTrue(registered)
        for path, selector in [('/character-details', {}),
                               ('/cycle-analysis', {'daewoon_index': 1})]:
            response = self.client.get(path, params={**QUERY, **selector})
            self.assertEqual(response.status_code, 200, response.text)
            graph = response.json()
            for pillar, raw in registered.items():
                self.assertEqual(raw['activation_status'], 'detected')
                self.assertEqual(raw['impact_status'], 'not_evaluated')
                self.assertNotIn('active', raw)
                self.assertNotIn('condition_met', raw)
                row = graph['relations'][f'natal.chart:same_pillar:self_combine:{pillar}']
                self.assertEqual(row['activation_status'], 'detected')
                self.assertEqual(row['status_reasons'], [])
                self.assertTrue(any(entry['details'].get('records') == raw for entry in row['evidence']))

    def test_duplicate_middle_trine_facts_survive_http_paths(self):
        query = {**QUERY, 'year': 1990, 'month': '1', 'day': '8', 'hour': 18, 'min': 0}
        response = self.client.get('/', params=query)
        self.assertEqual(response.status_code, 200, response.text)
        base = response.json()
        raw = base['analysis']['details']['year']['branch']['relations']['three_haps'][0]
        self.assertEqual(raw['activation_status'], 'detected')
        self.assertEqual(raw['condition_evidence']['middle_count'], 2)
        self.assertEqual(len(raw['formation_indices']), 2)
        for path, selector in [('/character-details', {}),
                               ('/cycle-analysis', {'daewoon_index': 1})]:
            result = self.client.get(path, params={**query, **selector})
            self.assertEqual(result.status_code, 200, result.text)
            graph = result.json()
            row = next(r for r in graph['relations'].values()
                       if r['type'] == 'trine' and r['context_ids'] == ['natal.chart'])
            self.assertEqual(row['activation_status'], 'detected')
            self.assertEqual(row['presentation']['status_label'], '탐지')
            self.assertFalse(any(r['category'] == 'decision' for r in row['presentation']['reasons']))
            self.assertEqual(graph['characters']['natal.chart.year.branch']['analysis']['relations']['three_haps'][0], raw)

    def test_age_reference_and_counting_age_are_consistent_before_birthday(self):
        body = self.get(month='12', day='31')
        self.assertEqual(body['meta']['reference_date'], '2026-11-13')
        self.assertEqual(body['meta']['age_man'], 30)
        self.assertEqual(body['meta']['age_korean'], 32)
        self.assertEqual(body['daewoon']['selection_year'], 2026)
        self.assertEqual(body['daewoon']['current']['age'], 32)
        self.assertEqual(body['daewoon']['current']['age_basis'], 'counting_age')
        annual = next(c for c in body['cycles']['future_100'] if c['year'] == 2026)
        self.assertEqual(annual['age'], 32)
        self.assertEqual(annual['age_basis'], 'counting_age')
        graph = self.client.get('/cycle-analysis', params={**QUERY, 'sewoon_year': 2007}).json()
        self.assertEqual(graph['contexts']['sewoon.year_2007']['selection']['age_basis'], 'counting_age')

    def test_childhood_list_is_a_view_of_annual_cycles_not_a_second_small_cycle(self):
        cycles = self.get()['cycles']
        self.assertNotIn('baby_10', cycles)
        self.assertEqual(len(cycles['future_100']), 100)
        self.assertEqual(len(cycles['childhood_10']), 10)
        self.assertEqual(cycles['childhood_10'], cycles['future_100'][:10])
        self.assertEqual([c['year'] for c in cycles['childhood_10']], list(range(1995, 2005)))
        self.assertEqual([c['age'] for c in cycles['childhood_10']], list(range(1, 11)))

    def test_boundary_missing_term_is_reported_without_breaking_natal_queries(self):
        for year, month, day, gender in [(1900, '1', '1', '남'), (2100, '12', '31', '남')]:
            params = dict(year=year, month=month, day=day, gen=gender)
            body = self.get(**params)
            self.assertIsNone(body['daewoon']['start_age'])
            self.assertEqual(body['daewoon']['start_age_status'], 'term_data_unavailable')
            self.assertEqual(body['daewoon']['selection_status'], 'unavailable')
            self.assertEqual(body['daewoon']['list'], [])
            self.assertEqual(len(body['cycles']['future_100']), 100)
            for path in ('/character-details', '/relation-index'):
                response = self.client.get(path, params={**QUERY, **params})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(len(response.json()['characters']), 8)
            for selector in ({'daewoon_index': 0}, {'sewoon_year': year}):
                response = self.client.get('/cycle-analysis', params={**QUERY, **params, **selector})
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response.json()['code'], 'daewoon_unavailable')
        available = self.get(year=1900, month='1', day='1', gen='여')
        self.assertEqual(available['daewoon']['start_age_status'], 'calculated')
        self.assertEqual(available['daewoon']['start_age'], 1.7)

    def test_distribution_text_describes_counts_without_strength_or_advice_claims(self):
        for params in ({}, dict(year=2023, month='2', day='1', sl='lun')):
            body = self.get(**params)
            elements = body['advanced_analysis']['five_elements']
            self.assertEqual(sum(elements['counts'].values()), 8)
            self.assertEqual(sum(elements['percentages'].values()), 100)
            self.assertEqual(elements['distribution_basis'], 'eight_visible_characters')
            self.assertEqual(elements['score_meaning'], 'provisional_weighted_index')
            for element, count in elements['counts'].items():
                self.assertIn(f'{element} {count}개', elements['summary'])
            for phrase in ('보완이 필요', '주도적인 성향', '가장 우세', '원만한'):
                self.assertNotIn(phrase, elements['summary'])
            prompt = next(p for p in body['advanced_analysis']['ai_consultation_prompts'] if p.startswith('【원국 허실】'))
            self.assertNotIn('관계 반영 전후 비교', prompt)
            self.assertIn('관계 적용 후 통근 변화는 계산하지 않았습니다', prompt)
            for pillar in body['advanced_analysis']['xu_shi_dynamics']['pillars'].values():
                self.assertEqual(pillar['root_impact_status'], 'not_evaluated')
