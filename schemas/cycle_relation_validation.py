"""Structural cycle-edge validation, independent of candidate enumeration."""
from services.constants import JIJANGGAN_DETAILED

TYPES = {
    'stem': {'combine', 'clash', 'control'},
    'branch': {'combine', 'clash', 'pierce', 'break', 'punishment', 'self_punishment',
               'half_combine', 'arch_combine', 'hidden_combine', 'same_branch', 'generate', 'control'},
    'group': {'trine', 'square', 'triple_punishment'},
    'cross_layer': {'transmission'},
}


def validate_cycle_relation(row, characters):
    parts = row.relation_id.split(':', 3)
    if len(parts) != 4 or parts[1] not in TYPES or row.type not in TYPES[parts[1]]:
        raise ValueError('운 관계의 종류·ID가 맞지 않습니다.')
    family = parts[1]
    members = row.participants
    if (parts[2] != row.type or members != sorted(members)
            or parts[3] != '|'.join(members) or len(row.context_ids) < 2
            or row.source_relation_id != row.relation_id):
        raise ValueError('운 관계의 ID·소속·참여 위치가 맞지 않습니다.')
    if len(members) != (3 if family == 'group' else 2):
        raise ValueError('운 관계 참여 글자 수가 맞지 않습니다.')
    kinds = [characters[key].kind for key in members]
    if family in ('stem', 'branch') and any(kind != family for kind in kinds):
        raise ValueError('운 관계의 천간·지지 종류가 맞지 않습니다.')
    if family == 'group' and any(kind != 'branch' for kind in kinds):
        raise ValueError('운 다자 관계는 지지만 참여해야 합니다.')
    if row.formation_candidates != ([members] if family == 'group' else []):
        raise ValueError('운 다자 관계의 위치 조합이 맞지 않습니다.')
    fact = row.type in ('control', 'generate', 'same_branch', 'transmission')
    if row.activation_status != ('detected' if fact else 'candidate_only'):
        raise ValueError('운 후보 탐지를 성립 판정으로 사용할 수 없습니다.')
    if row.status_reason != 'cycle_presence_only_activation_and_impact_not_evaluated':
        raise ValueError('운 관계의 성립·영향 미평가 근거가 필요합니다.')
    needs_direction = row.type in ('control', 'generate', 'transmission')
    if bool(row.direction) != needs_direction:
        raise ValueError('운 관계의 방향 근거가 맞지 않습니다.')
    if row.direction:
        basis = ('hidden_stem_match' if family == 'cross_layer' else
                 'rule_fixed' if family == 'stem' else 'elemental')
        if row.direction.basis != basis:
            raise ValueError('운 관계의 방향 출처가 맞지 않습니다.')
    if family == 'cross_layer':
        source = characters[row.direction.from_character]
        target = characters[row.direction.to_character]
        if (source.kind != 'branch' or target.kind != 'stem'
                or row.hidden_stem != target.char
                or row.hidden_stem not in {h['char'] for h in JIJANGGAN_DETAILED[source.char]}
                or row.direction.basis != 'hidden_stem_match'):
            raise ValueError('운 투간의 출처·대상·지장간 글자가 맞지 않습니다.')
    elif row.hidden_stem is not None:
        raise ValueError('투간 이외의 운 관계에 투간 글자가 있습니다.')
    if row.type == 'same_branch' and len({characters[key].char for key in members}) != 1:
        raise ValueError('동일 지지 관계의 글자가 다릅니다.')
