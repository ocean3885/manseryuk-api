"""Read-only audit: run from the checkout with .venv312/bin/python scripts/audit_same_pillar_roots.py."""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.constants import ROOT_STRENGTH, JIJANGGAN_DETAILED, STEM_INFO
from services.analysis import analyze_advanced_tonggeun
from services.interaction_matrix import build_interaction_matrix
from services.xu_shi import analyze_xu_shi_dynamics


def main():
    counts = Counter()
    print('| 간지 | 계수 | 정확 일치 지장간 | 동오행 지장간 | 분류 |')
    print('| --- | ---: | --- | --- | --- |')
    for stem in STEM_INFO:
        for branch, hidden in JIJANGGAN_DETAILED.items():
            coefficient = ROOT_STRENGTH.get(stem, {}).get(branch, 0)
            literal = [h for h in hidden if h['char'] == stem]
            same = [h for h in hidden if STEM_INFO[h['char']]['element'] == STEM_INFO[stem]['element']]
            kind = ('정확 일치·양수' if literal else '동오행만·양수') if coefficient > 0 else (
                '정확 일치·0' if literal else '동오행만·0' if same else '동오행 없음·0')
            if coefficient > 0 and not same:
                kind = '동오행 없음·양수'
            counts[kind] += 1
            describe = lambda items: ', '.join(f"{h['char']}({h['type']} {h['ratio']})" for h in items) or '—'
            print(f'| {stem}{branch} | {coefficient:g} | {describe(literal)} | {describe(same)} | {kind} |')
    print('\n집계:', dict(counts))
    print('\n합성 입력 비교: 실제 생년월일 원국이나 명리 타당성의 검증이 아님.')
    for label, stems, branches in [
        ('戊 초기 반례', '戊戊戊戊', '寅申亥巳'),
        ('약근과 타주 지원', '己己己己', '丑卯卯卯'),
        ('충과 타주 지원', '甲甲甲甲', '寅申寅酉'),
        ('격위 자형 후보', '甲甲甲甲', '辰酉辰酉'),
    ]:
        roots = analyze_advanced_tonggeun(list(stems), list(branches))
        matrix = build_interaction_matrix(list(stems), list(branches), stems[2])['matrix']
        result = analyze_xu_shi_dynamics(list(stems), list(branches), stems[2], roots, matrix)
        print(f'\n{label}: {stems}/{branches}')
        for key, root in zip(('year', 'month', 'day', 'hour'), roots):
            state = result['pillars'][key]
            print(key, root['점수'], root['타주지원점수'], state['original_status'], '→', state['current_status'])


if __name__ == '__main__':
    main()
