"""Independent presence oracles and lifecycle/contract audits."""
from copy import deepcopy
from importlib import import_module
from itertools import permutations, product
from pathlib import Path
import unittest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from services.constants import JIJANGGAN_DETAILED
from services.cycle_relations import detect_cycle_relations, attach_cycle_relations
from services.character_details import assemble_character_details
from services.cycle_analysis import assemble_cycle_analysis
from services.saju_orchestrator import get_full_saju_data
from schemas.cycle_analysis import CycleAnalysis

DB = Path(__file__).resolve().parents[1] / 'manseryuk.db'
CONTEXTS = ('natal.chart', 'daewoon.period_0', 'sewoon.year_2026')


def node(context, char, kind='branch'):
    return dict(context_id=context, char=char, kind=kind)


class PresenceAuditTests(unittest.TestCase):
    def test_transmission_all_120_pairs_in_six_scope_directions(self):
        checks = 0
        for source_context, target_context in permutations(CONTEXTS, 2):
            source = source_context + '.year.branch'
            target = target_context + '.year.stem'
            for branch, stem in product('子丑寅卯辰巳午未申酉戌亥', '甲乙丙丁戊己庚辛壬癸'):
                graph = {source: node(source_context, branch), target: node(target_context, stem, 'stem')}
                rows = [r for r in detect_cycle_relations(graph).values() if r['type'] == 'transmission']
                expected = stem in {h['char'] for h in JIJANGGAN_DETAILED[branch]}
                self.assertEqual(len(rows), int(expected))
                if rows:
                    self.assertEqual(rows[0]['direction'], dict(from_character=source,
                                                               to_character=target, basis='hidden_stem_match'))
                checks += 1
        self.assertEqual(checks, 720)

    def test_repeated_stems_preserve_every_transmission_position(self):
        graph = {
            'natal.chart.year.branch': node('natal.chart', '寅'),
            'natal.chart.hour.branch': node('natal.chart', '寅'),
            'daewoon.period_0.cycle.stem': node('daewoon.period_0', '甲', 'stem'),
            'sewoon.year_2026.cycle.stem': node('sewoon.year_2026', '甲', 'stem'),
        }
        rows = [r for r in detect_cycle_relations(graph).values() if r['type'] == 'transmission']
        self.assertEqual(len(rows), 4)
        self.assertEqual(len({r['relation_id'] for r in rows}), 4)

    def test_group_oracle_all_ordered_branch_triples(self):
        # Explicit structural fixtures independent of production rule iteration.
        expected = {
            'trine': {'寅午戌', '亥卯未', '申子辰', '巳酉丑'},
            'square': {'寅卯辰', '巳午未', '申酉戌', '亥子丑'},
            'triple_punishment': {'寅巳申', '丑戌未'},
        }
        expected = {kind: {frozenset(chars) for chars in groups} for kind, groups in expected.items()}
        for contexts in [('natal.chart', 'natal.chart', 'daewoon.period_0'), CONTEXTS]:
            ids = [f'{context}.p{i}.branch' for i, context in enumerate(contexts)]
            for letters in product('子丑寅卯辰巳午未申酉戌亥', repeat=3):
                nodes = {key: node(context, char) for key, context, char in zip(ids, contexts, letters)}
                groups = [r for r in detect_cycle_relations(nodes).values() if ':group:' in r['relation_id']]
                wanted = {kind for kind, sets in expected.items() if len(set(letters)) == 3
                          and frozenset(letters) in sets}
                self.assertEqual({r['type'] for r in groups}, wanted)
                self.assertEqual(len(groups), len(wanted))

    def test_overlap_enumerates_all_position_products_without_natal_duplicates(self):
        nodes = {f'natal.chart.{p}.branch': node('natal.chart', char)
                 for p, char in zip(('year', 'month', 'day', 'hour'), '亥亥卯未')}
        nodes['daewoon.period_0.cycle.branch'] = node('daewoon.period_0', '卯')
        nodes['sewoon.year_2026.cycle.branch'] = node('sewoon.year_2026', '未')
        buckets = [[key for key, n in nodes.items() if n['char'] == char] for char in '亥卯未']
        wanted = {tuple(sorted(members)) for members in product(*buckets)
                  if len({nodes[key]['context_id'] for key in members}) > 1}
        rows = detect_cycle_relations(nodes)
        groups = [r for r in rows.values() if r['type'] == 'trine']
        self.assertEqual(len(groups), 6)
        self.assertEqual({tuple(r['participants']) for r in groups}, wanted)
        self.assertEqual(rows, detect_cycle_relations(dict(reversed(list(nodes.items())))))


@unittest.skipUnless(DB.is_file(), '달력 DB가 필요합니다.')
class GraphLifecycleAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(f'sqlite:///file:{DB}?mode=ro&uri=true')
        cls.responses = []
        for year, month, day in [(1990, '1', '1'), (1995, '5', '12'), (2000, '1', '1')]:
            with Session(cls.engine) as db:
                cls.responses.append(get_full_saju_data(year, month, day, 14, 30, 'sol', '남', db))

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()

    def test_adding_sewoon_preserves_every_existing_relation_and_rooting(self):
        for response in self.responses:
            before = deepcopy(response)
            natal = assemble_character_details(response)
            for index in (0, 1, 9):
                period = response['daewoon']['list'][index]
                dae = assemble_cycle_analysis(response, daewoon_index=index)
                for year in (period['start_year'], min(period['start_year'] + 9,
                                                       response['cycles']['future_100'][-1]['year'])):
                    full = assemble_cycle_analysis(response, sewoon_year=year)
                    self.assertEqual(full['selection']['daewoon_index'], index)
                    for rid, row in dae['relations'].items():
                        self.assertEqual(full['relations'][rid], row)
                    for rid, row in natal['relations'].items():
                        self.assertEqual(full['relations'][rid], row)
                    for key, item in natal['characters'].items():
                        self.assertEqual(full['characters'][key]['rooting'], item['rooting'])
                    CycleAnalysis.model_validate(full)
            self.assertEqual(response, before)

    def test_reattachment_is_idempotent_and_removes_stale_edges(self):
        response = self.responses[1]
        year = response['daewoon']['list'][1]['start_year']
        graph = assemble_cycle_analysis(response, sewoon_year=year)
        before = deepcopy(graph)
        attach_cycle_relations(graph)
        self.assertEqual(graph, before)
        dae_index = graph['selection']['daewoon_index']
        context = f'sewoon.year_{year}'
        graph['characters'] = {key: item for key, item in graph['characters'].items()
                               if item['context_id'] != context}
        del graph['contexts'][context]
        attach_cycle_relations(graph)
        expected = assemble_cycle_analysis(response, daewoon_index=dae_index)
        for key in ('characters', 'contexts', 'relations', 'coverage'):
            self.assertEqual(graph[key], expected[key])

    def test_sources_resolve_and_mutated_cycle_contracts_are_rejected(self):
        response = self.responses[1]
        graph = assemble_cycle_analysis(response, sewoon_year=response['daewoon']['list'][1]['start_year'])
        cycles = [r for r in graph['relations'].values() if r['relation_id'].startswith('cycle:')]
        for row in cycles:
            for ref in row['source_refs']:
                module, name = ref['location'].rsplit('.', 1)
                self.assertTrue(hasattr(import_module(module), name))
        for defect in ('id', 'status', 'hidden_stem', 'missing_ref', 'duplicate_coverage',
                       'reverse_direction', 'missing_reason'):
            bad = deepcopy(graph)
            row = next(r for r in bad['relations'].values() if r['relation_id'].startswith('cycle:')
                       and r['type'] == 'transmission')
            if defect == 'id':
                row['source_relation_id'] = 'incorrect'
            elif defect == 'status':
                row['activation_status'] = 'active'
                bad['coverage']['detected_only_relation_ids'].remove(row['relation_id'])
            elif defect == 'hidden_stem':
                row['hidden_stem'] = 'incorrect'
            elif defect == 'missing_ref':
                bad['characters'][row['participants'][0]]['relation_ids'].remove(row['relation_id'])
            elif defect == 'reverse_direction':
                direction = row['direction']
                direction['from_character'], direction['to_character'] = direction['to_character'], direction['from_character']
            elif defect == 'missing_reason':
                row['status_reason'] = None
            else:
                bad['coverage']['not_evaluated_mechanisms'].append(bad['coverage']['not_evaluated_mechanisms'][0])
            with self.subTest(defect=defect), self.assertRaises(ValidationError):
                CycleAnalysis.model_validate(bad)
