"""Fixed pillar fixtures use production rules without claiming calendar birth dates."""
from services.analysis import analyze_palja_integrated, analyze_advanced_tonggeun
from services.branch_dynamics import analyze_branch_dynamics
from services.calculator import get_stem_detail, get_branch_detail, get_jijanggan_details
from services.interaction_matrix import build_interaction_matrix
from services.xu_shi import analyze_xu_shi_dynamics

PILLARS = ('year', 'month', 'day', 'hour')


def response_for(branches, stems='甲甲甲甲'):
    stems, branches = list(stems), list(branches)
    analysis = analyze_palja_integrated(stems, branches)
    interactions = build_interaction_matrix(stems, branches, stems[2])
    return dict(
        meta=dict(birth_date_solar='fixture', birth_time='fixture'),
        four_pillars={p: dict(gan=get_stem_detail(stems[2], stems[i], is_day_gan=i == 2),
                             ji=get_branch_detail(stems[2], branches[i]),
                             jijanggan=get_jijanggan_details(stems[2], branches[i]))
                      for i, p in enumerate(PILLARS)},
        analysis=dict(details=analysis['pillars']),
        advanced_analysis=dict(
            interactions=interactions,
            branch_dynamics=analyze_branch_dynamics(stems, branches, interactions['matrix']),
            xu_shi_dynamics=analyze_xu_shi_dynamics(
                stems, branches, stems[2], analyze_advanced_tonggeun(stems, branches), interactions['matrix'])))


def links(row):
    return {rid for e in row['evidence'] for rid in e['related_relation_ids']}


def row_for(graph, kind, left=None, right=None):
    return next(r for r in graph['relations'].values() if r['type'] == kind
                and (left is None or set(r['participants']) == {
                    f'natal.chart.{left}.branch', f'natal.chart.{right}.branch'}))
