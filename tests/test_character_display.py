"""Compact display fidelity and selection refresh, without new interpretation."""
from copy import deepcopy
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from core.dependencies import get_db
from main import app
from services.character_display import attach_character_displays
from services.character_details import assemble_character_details
from services.cycle_analysis import assemble_cycle_analysis
from services.saju_orchestrator import get_full_saju_data
from services.cycle_relations import attach_cycle_relations

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
QUERY = dict(year=1995, month='5', day='12', hour=14, min=30, sl='sol', gen='남')


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class CharacterDisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        with Session(cls.engine) as db:
            cls.response = get_full_saju_data(**QUERY, db=db)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def check_display(self, graph):
        for key, node in graph['characters'].items():
            display = node['display']
            self.assertTrue(display['title'])
            rows = [item for group in display['relation_groups'] for item in group['items']]
            ids = [rid for item in rows for rid in item['relation_ids']]
            self.assertCountEqual(ids, node['relation_ids'])
            self.assertEqual(len(ids), len(set(ids)))
            for item in rows:
                self.assertNotIn('후보', item['text'])
                self.assertNotIn('미평가', item['text'])
                for rid in item['relation_ids']:
                    row = graph['relations'][rid]
                    self.assertEqual(set(item['character_ids']), set(row['participants']) - {key})
            for group in display['relation_groups'] + display['sections']:
                for item in group['items']:
                    self.assertTrue(set(item['character_ids']) <= graph['characters'].keys())
                    self.assertTrue(set(item['relation_ids']) <= graph['relations'].keys())

    def test_every_relation_appears_once_for_every_character_and_all_selections(self):
        before = deepcopy(self.response)
        self.check_display(assemble_character_details(self.response))
        for selector in ({'daewoon_index': 0}, {'daewoon_index': 9},
                         {'sewoon_year': 1995}, {'sewoon_year': 2026}):
            self.check_display(assemble_cycle_analysis(self.response, **selector))
        self.assertEqual(self.response, before)

    def test_directions_same_peer_merge_and_multicontext_groups(self):
        graph = assemble_cycle_analysis(self.response, sewoon_year=2026)
        # Fixed cross-context transmission: natal 未 contains 乙, natal 乙 receives it.
        branch = graph['characters']['natal.chart.hour.branch']['display']
        row = next(i for g in branch['relation_groups'] for i in g['items']
                   if i['character_ids'] == ['natal.chart.year.stem'])
        self.assertEqual(row['text'], '년간 乙 · 투간 →')
        target = graph['characters']['natal.chart.year.stem']['display']
        row = next(i for g in target['relation_groups'] for i in g['items']
                   if i['character_ids'] == ['natal.chart.hour.branch'])
        self.assertEqual(row['text'], '시지 未 · 투간 ←')
        merged = [i for n in graph['characters'].values() for g in n['display']['relation_groups']
                  for i in g['items'] if len(i['relation_ids']) > 1]
        self.assertTrue(merged)
        self.assertTrue(any(g['key'] == 'mixed' for n in graph['characters'].values()
                            for g in n['display']['relation_groups']))

    def test_storehouse_uses_hidden_stem_and_preserves_repeated_targets(self):
        graph = assemble_cycle_analysis(self.response, sewoon_year=2026)
        sections = graph['characters']['natal.chart.hour.branch']['display']['sections']
        store = next(g for g in sections if g['key'] == 'storehouse')['items'][0]
        self.assertEqual(store['text'], '식상고 · 저장 오행 木')
        self.assertEqual(store['detail_lines'][0], '지장간 乙 · 식신')
        self.assertIn('natal.chart.year.stem', store['character_ids'])
        self.assertFalse(any(g['key'] == 'rooting' for g in graph['characters']['sewoon.year_2026.cycle.stem']['display']['sections']))

    def test_repeated_positions_and_group_formations_stay_clickable(self):
        from services.character_display import _relations
        nodes = {
            'natal.chart.year.branch': dict(context_id='natal.chart', position='year', kind='branch', char='寅'),
            'natal.chart.hour.branch': dict(context_id='natal.chart', position='hour', kind='branch', char='寅'),
            'daewoon.period_0.cycle.stem': dict(context_id='daewoon.period_0', position='cycle', kind='stem', char='甲'),
            'daewoon.period_0.cycle.branch': dict(context_id='daewoon.period_0', position='cycle', kind='branch', char='午'),
        }
        from services.cycle_relations import detect_cycle_relations
        graph = dict(characters=nodes, relations=detect_cycle_relations(nodes), contexts={
            'natal.chart': dict(scope='natal'),
            'daewoon.period_0': dict(scope='daewoon', selection={})})
        key = 'daewoon.period_0.cycle.stem'
        nodes[key]['relation_ids'] = [rid for rid, r in graph['relations'].items() if key in r['participants']]
        items = [i for group in _relations(graph, key) for i in group['items']]
        self.assertEqual([i['text'] for i in items], ['년지 寅 · 투간 ←', '시지 寅 · 투간 ←'])
        self.assertNotEqual(items[0]['character_ids'], items[1]['character_ids'])
        full = assemble_cycle_analysis(self.response, sewoon_year=2026)
        groups = [i for n in full['characters'].values() for g in n['display']['relation_groups'] for i in g['items']
                  if any(len(full['relations'][rid]['participants']) > 2 for rid in i['relation_ids'])]
        self.assertTrue(groups)
        self.assertTrue(all(i['detail_lines'] for i in groups))

    def test_display_refreshes_and_reattachment_is_stable(self):
        natal = assemble_character_details(self.response)
        full = assemble_cycle_analysis(self.response, sewoon_year=2026)
        self.assertNotEqual(natal['characters']['natal.chart.year.branch']['display'],
                            full['characters']['natal.chart.year.branch']['display'])
        before = deepcopy(full)
        attach_cycle_relations(full)
        self.assertEqual(before, full)
        attach_character_displays(full)
        self.assertEqual(before, full)

    def test_http_provides_display_for_all_eight_ten_and_twelve_nodes(self):
        def db():
            with Session(self.engine) as session:
                yield session
        old = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = db
        try:
            with TestClient(app) as client:
                for path, selector, count in [('/character-details', {}, 8),
                        ('/cycle-analysis', {'daewoon_index': 0}, 10),
                        ('/cycle-analysis', {'sewoon_year': 2026}, 12)]:
                    r = client.get(path, params=QUERY | selector)
                    self.assertEqual(r.status_code, 200, r.text)
                    graph = r.json()
                    self.assertEqual(len(graph['characters']), count)
                    self.check_display(graph)
        finally:
            if old is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = old
