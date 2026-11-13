"""빈(년·월)과 주(일·시)를 잇는 관계의 위치별 사실 조회."""
from services.calculator import get_ten_star_stem, get_ten_star_branch

PILLAR_KEYS = ('year', 'month', 'day', 'hour')
POSITION_NAMES = ('년', '월', '일', '시')


def analyze_bin_zhu_dynamics(
    stems: list[str], branches: list[str], day_stem: str,
    interaction_matrix: list[dict],
) -> dict:
    """기존 관계를 소속별로 연결한다. 점수·우세·취용·성과는 판정하지 않는다."""
    def participant(index, category):
        is_stem = category == '천간'
        char = stems[index] if is_stem else branches[index]
        ten_god = ('일간' if is_stem and index == 2 else
                   get_ten_star_stem(day_stem, char) if is_stem else
                   get_ten_star_branch(day_stem, char))
        suffix = '간' if is_stem else '지'
        return {'pillar': PILLAR_KEYS[index], 'char': char, 'ten_god': ten_god,
                'display_name': f'{POSITION_NAMES[index]}{suffix} {char}({ten_god})'}

    links, groups, excluded = [], [], []
    for item in interaction_matrix:
        left, right = item.get('from_pillar'), item.get('to_pillar')
        is_group = (item.get('relation_scope') == 'group' or 'all' in (left, right)
                    or item.get('type') in ('삼합(三合)', '방합(方合)', '삼형(三刑)'))
        if is_group:
            members = item.get('participants', [])
            valid = (len(members) >= 3 and len(set(members)) == len(members)
                     and all(p in PILLAR_KEYS for p in members))
            if valid:
                members = [p for p in PILLAR_KEYS if p in members]
                group = {'relation_id': item.get('relation_id'), 'type': item['type'],
                         'participants': members,
                         'formations': [list(f) for f in item.get('formations', [])],
                         'guest_participants': [p for p in members if p in PILLAR_KEYS[:2]],
                         'host_participants': [p for p in members if p in PILLAR_KEYS[2:]],
                         'activation_status': item.get('activation_status'),
                         'description': f"빈과 주가 함께 참여하는 {item['type']}의 구성 정보입니다."}
                if group not in groups:
                    groups.append(group)
                continue
            reason = 'missing_group_participants'
        elif left not in PILLAR_KEYS or right not in PILLAR_KEYS or left == right:
            reason = 'invalid_endpoint'
        elif item.get('category') not in ('천간', '지지'):
            reason = 'invalid_category'
        else:
            first, second = PILLAR_KEYS.index(left), PILLAR_KEYS.index(right)
            if (first < 2) == (second < 2):
                continue
            guest_index, host_index = (first, second) if first < 2 else (second, first)
            guest = participant(guest_index, item['category'])
            host = participant(host_index, item['category'])
            link = {'relation_id': item.get('relation_id'), 'category': item['category'],
                    'type': item['type'], 'participants': [guest['pillar'], host['pillar']],
                    'guest': guest, 'host': host,
                    'activation_status': item.get('activation_status'),
                    'distance': abs(first - second), 'is_adjacent': abs(first - second) == 1,
                    'detail': f"빈 {guest['display_name']} ↔ 주 {host['display_name']}: {item['type']} 관계가 있습니다."}
            if link not in links:
                links.append(link)
            continue
        entry = {'relation_id': item.get('relation_id'),
                 'participants': list(item.get('participants', [])),
                 'category': item.get('category', ''), 'type': item.get('type', ''),
                 'name': item.get('name', ''), 'from_pillar': left, 'to_pillar': right,
                 'reason_code': reason}
        if entry not in excluded:
            excluded.append(entry)

    elements = {p: {'stem': participant(i, '천간')['display_name'],
                    'branch': participant(i, '지지')['display_name']}
                for i, p in enumerate(PILLAR_KEYS)}
    return {'rule_version': '4.0.0', 'interaction_scope': 'cross_domain_relations',
            'guest_structure': {'scope': '년주·월주',
                                'elements': {p: elements[p] for p in PILLAR_KEYS[:2]}},
            'host_structure': {'scope': '일주·시주',
                               'elements': {p: elements[p] for p in PILLAR_KEYS[2:]}},
            'guest_host_links': links, 'group_connections': groups,
            'excluded_interactions': excluded}
