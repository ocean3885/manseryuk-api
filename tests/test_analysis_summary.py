from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
import unittest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from schemas.analysis_summary import AnalysisSummary
from services.analysis_summary import assemble_analysis_summary, summarize_graph
from services.character_details import assemble_character_details
from services.cycle_analysis import assemble_cycle_analysis
from services.saju_orchestrator import get_full_saju_data

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class AnalysisSummaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        with Session(cls.engine) as session:
            cls.response = get_full_saju_data(**QUERY, db=session)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def assert_partition(self, result):
        primary = [rid for item in result['items'].values() if item['category'] != 'participation'
                   for rid in item['relation_ids']]
        expected = result['comparison']['added_relation_ids'] if result['selection'] else result['comparison']['maintained_relation_ids']
        self.assertCountEqual(primary, expected)
        self.assertEqual(len(primary), len(set(primary)))
        self.assertEqual(AnalysisSummary.model_validate(result).model_dump(mode='json'), result)

    def test_natal_summary_is_structure_not_new_changes(self):
        result = assemble_analysis_summary(self.response)
        self.assertIsNone(result['selection'])
        self.assertEqual(result['comparison']['added_count'], 0)
        self.assertEqual(result['graph'], assemble_character_details(self.response))
        self.assertTrue(all(item['change'] == 'maintained' for item in result['items'].values()))
        self.assert_partition(result)

    def test_daewoon_and_sewoon_compare_exact_baseline_without_mutation(self):
        before = deepcopy(self.response)
        natal = assemble_character_details(self.response)
        for index in (0, 1, 9):
            year = self.response['daewoon']['list'][index]['start_year']
            dae = assemble_analysis_summary(self.response, daewoon_index=index)
            annual = assemble_analysis_summary(self.response, sewoon_year=year)
            self.assertEqual(set(dae['comparison']['maintained_relation_ids']), set(natal['relations']))
            self.assertEqual(set(annual['comparison']['maintained_relation_ids']), set(dae['graph']['relations']))
            self.assertEqual(annual['comparison']['baseline'], 'natal_daewoon')
            self.assert_partition(dae)
            self.assert_partition(annual)
            self.assertEqual(annual['graph']['relations'],
                             assemble_cycle_analysis(self.response, sewoon_year=year)['relations'])
        self.assertEqual(self.response, before)

    def test_before_first_daewoon_uses_natal_baseline(self):
        response = deepcopy(self.response)
        # Deterministic pre-period selection independent of the real start age.
        for index, period in enumerate(response['daewoon']['list']):
            period['start_year'] = 1998 + index * 10
        result = assemble_analysis_summary(response, sewoon_year=1995)
        self.assertEqual(result['selection']['daewoon_status'], 'before_first_period')
        self.assertEqual(result['comparison']['baseline'], 'natal')
        self.assertEqual(set(result['comparison']['maintained_relation_ids']),
                         set(assemble_character_details(response)['relations']))
        self.assert_partition(result)

    def test_group_components_and_participation_are_evidence_backed(self):
        # This actual calendar sample has three cycle group relations.
        result = assemble_analysis_summary(self.response, sewoon_year=2007)
        groups = [item for item in result['items'].values() if item['category'] == 'group']
        self.assertTrue(groups)
        graph = result['graph']
        self.assertTrue(any(len(item['relation_ids']) > 1 for item in groups))
        for item in groups:
            self.assertTrue(any(graph['relations'][rid]['formation_candidates'] for rid in item['relation_ids']))
        for item in result['items'].values():
            refs = item['relation_ids'] + item['related_relation_ids']
            expected = {graph['relations'][rid]['activation_status'] for rid in refs}
            self.assertEqual(set(item['activation_statuses']), expected)
            self.assertNotIn('미평가', item['description'])
            self.assertNotIn('판정이 아닙니다', item['description'])
            self.assertEqual(item['impact_status'], 'not_evaluated')
            if item['category'] == 'participation':
                self.assertEqual(len(item['character_ids']), 1)
                key = item['character_ids'][0]
                self.assertTrue(all(key in graph['relations'][rid]['participants'] for rid in item['relation_ids']))
                self.assertGreater(len({graph['relations'][rid]['type'] for rid in refs}), 1)
                self.assertTrue(set(refs) <= set(result['comparison']['added_relation_ids']))
        self.assert_partition(result)

    def test_lines_separate_stem_and_branch_pairs_and_preserve_direction(self):
        with Session(self.engine) as session:
            response = get_full_saju_data(1988, '8', '8', 23, 59, 'sol', '남', session)
        result = assemble_analysis_summary(response, daewoon_index=1)
        clashes = [item for item in result['items'].values() if item['category'] == 'pair'
                   and any(result['graph']['relations'][rid]['type'] == 'clash' for rid in item['relation_ids'])]
        self.assertEqual(len(clashes), 2)
        self.assertTrue(any('천간' in item['title'] for item in clashes))
        self.assertTrue(any('지지' in item['title'] for item in clashes))
        for item in result['items'].values():
            for line in item['lines']:
                for rid in line['relation_ids']:
                    row = result['graph']['relations'][rid]
                    self.assertEqual(line['activation_status'], row['activation_status'])
                if item['category'] == 'pair':
                    self.assertEqual(len(line['relation_ids']), 1)
                    row = result['graph']['relations'][line['relation_ids'][0]]
                    self.assertIn('→' if row['direction'] else '↔', line['text'])

    def test_transmission_lines_group_only_complete_source_target_sets(self):
        with Session(self.engine) as session:
            response = get_full_saju_data(1990, '1', '1', 12, 0, 'sol', '남', session)
        graph = assemble_cycle_analysis(response, sewoon_year=2026)
        # Remove one edge to create unequal incoming source sets for repeated 丙 targets.
        removed = next(rid for rid, row in graph['relations'].items() if row['type'] == 'transmission'
                       and row['direction']['from_character'] == 'sewoon.year_2026.cycle.branch'
                       and row['direction']['to_character'] == 'natal.chart.month.stem')
        del graph['relations'][removed]
        graph['coverage']['detected_only_relation_ids'].remove(removed)
        for node in graph['characters'].values():
            for field in ('relation_ids', 'transmission_relation_ids'):
                node[field] = [rid for rid in node[field] if rid != removed]
        result = summarize_graph(graph)
        transmission = [item for item in result['items'].values() if item['category'] == 'transmission']
        self.assertTrue(transmission)
        for item in transmission:
            for line in item['lines']:
                rows = [graph['relations'][rid] for rid in line['relation_ids']]
                sources = {row['direction']['from_character'] for row in rows}
                targets = {row['direction']['to_character'] for row in rows}
                self.assertEqual(len(rows), len(sources) * len(targets))
                self.assertIn('의 지장간', line['text'])
                self.assertIn('→', line['text'])
        self.assert_partition(result)

    def test_group_status_and_component_status_are_shown_on_distinct_lines(self):
        result = assemble_analysis_summary(self.response)
        groups = [item for item in result['items'].values() if item['category'] == 'group']
        self.assertTrue(groups)
        for item in groups:
            self.assertEqual(item['lines'][0]['relation_ids'], item['structure_relation_ids'])
            self.assertNotIn('구성 쌍', item['description'])
            self.assertNotIn('상태:', item['description'])
            primary = [result['graph']['relations'][rid]['activation_status'] for rid in item['structure_relation_ids']]
            self.assertEqual(item['lines'][0]['activation_status'], primary[0])

    def test_new_group_includes_existing_components_without_changing_counts(self):
        with Session(self.engine) as session:
            response = get_full_saju_data(1990, '1', '1', 12, 0, 'sol', '남', session)
        result = assemble_analysis_summary(response, daewoon_index=1)
        group = next(item for item in result['items'].values() if item['category'] == 'group')
        original_pair = 'natal.chart:branch:half_combine:day:hour'
        self.assertIn(original_pair, group['related_relation_ids'])
        self.assertNotIn(original_pair, group['relation_ids'])
        old_line = next(line for line in group['lines'] if original_pair in line['relation_ids'])
        self.assertEqual(old_line['change'], 'maintained')
        self.assertTrue(any(line['change'] == 'added' for line in group['lines']))
        self.assertEqual(group['change'], 'added')
        self.assertEqual(result['comparison']['added_count'], 9)
        self.assertNotIn('유지됩니다', result['overview'])
        self.assert_partition(result)

    def test_line_endpoints_and_explicit_display_order(self):
        result = assemble_analysis_summary(self.response, sewoon_year=2007)
        sections = []
        self.assertEqual(result['display_order'], list(result['items']))
        for sid in result['display_order']:
            item = result['items'][sid]
            if item['category'] == 'group':
                section = 0
            elif item['category'] == 'pair':
                kinds = {result['graph']['characters'][key]['kind'] for key in item['character_ids']}
                section = 1 if kinds == {'stem'} else 2 if kinds == {'branch'} else 3
            else:
                section = 4 if item['category'] == 'transmission' else 5
            sections.append(section)
            for line in item['lines']:
                rows = [result['graph']['relations'][rid] for rid in line['relation_ids']]
                self.assertEqual(set(line['character_ids']), {p for row in rows for p in row['participants']})
                self.assertEqual(set(line['from_character_ids']), {row['direction']['from_character'] for row in rows if row['direction']})
                self.assertEqual(set(line['to_character_ids']), {row['direction']['to_character'] for row in rows if row['direction']})
                added = set(result['comparison']['added_relation_ids'])
                refs = set(line['relation_ids'])
                self.assertEqual(line['change'], 'added' if refs <= added else 'maintained' if not refs & added else 'mixed')
        self.assertEqual(sections, sorted(sections))

    def test_summary_is_order_independent(self):
        graph = assemble_cycle_analysis(self.response, sewoon_year=2007)
        first = summarize_graph(graph)
        graph['relations'] = dict(reversed(list(graph['relations'].items())))
        graph['characters'] = dict(reversed(list(graph['characters'].items())))
        self.assertEqual(summarize_graph(graph), first)

    def test_invalid_counts_evidence_statuses_and_reverse_refs_are_rejected(self):
        source = assemble_analysis_summary(self.response, sewoon_year=2007)
        for defect in ('count', 'evidence', 'status', 'reverse_ref', 'change', 'line_status', 'line_missing', 'structure',
                       'line_change', 'line_members', 'line_direction', 'display_order'):
            bad = deepcopy(source)
            item = next(iter(bad['items'].values()))
            if defect == 'count':
                bad['comparison']['added_count'] += 1
            elif defect == 'evidence':
                item['relation_ids'].append('missing')
            elif defect == 'status':
                item['activation_statuses'] = []
            elif defect == 'change':
                item['change'] = 'maintained'
            elif defect == 'line_status':
                item['lines'][0]['activation_status'] = 'active'
            elif defect == 'line_missing':
                item['lines'] = []
            elif defect == 'structure':
                item['structure_relation_ids'] = []
            elif defect == 'line_change':
                item['lines'][0]['change'] = 'maintained'
            elif defect == 'line_members':
                item['lines'][0]['character_ids'] = []
            elif defect == 'line_direction':
                directed = next(line for card in bad['items'].values() for line in card['lines'] if line['from_character_ids'])
                directed['from_character_ids'] = []
            elif defect == 'display_order':
                bad['display_order'] = []
            else:
                bad['character_summary_ids'][item['character_ids'][0]] = []
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                AnalysisSummary.model_validate(bad)

    def test_http_response_and_single_chart_calculation(self):
        def readonly_db():
            with Session(self.engine) as session:
                yield session
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = readonly_db
        try:
            with TestClient(app) as client:
                for selector in ({}, {'daewoon_index': 1}, {'sewoon_year': 2007}):
                    with patch('routers.root.get_full_saju_data', wraps=get_full_saju_data) as calculate:
                        response = client.get('/analysis-summary', params={**QUERY, **selector})
                    self.assertEqual(response.status_code, 200, response.text)
                    self.assertEqual(calculate.call_count, 1)
                    self.assert_partition(response.json())
                for change, code in [({'hour': 24}, 400), ({'daewoon_index': 1, 'sewoon_year': 2007}, 400),
                                     ({'sewoon_year': 1800}, 400), ({'sewoon_year': 'bad'}, 422)]:
                    self.assertEqual(client.get('/analysis-summary', params={**QUERY, **change}).status_code, code)
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
