"""子午충의 잠정 손실률과 지지별 다중 충 배분.

보존된 잠정 수치 연구·회귀용 모듈이다. 현행 통근 영향 및 운 관계 API의 손상 판정에 적용하지 않는다. 수치화 재개 지침은 docs/archive의 과거 계획이 아니라 새 작업 범위로 정한다.
"""

from math import floor, isfinite, prod


def ziwu_loss_rates(zi_power, wu_power, distance_weight, calibration):
    """충 이전 세력으로 午 충격률과 子의 단일 자기 손실률을 구한다."""
    values = (zi_power, wu_power, distance_weight,
              calibration['k_shock'], calibration['k_base'],
              calibration['k_resist'])
    if any(not isinstance(value, (int, float)) or isinstance(value, bool)
           or not isfinite(value) for value in values):
        raise ValueError('子午충 세력·거리·계수는 유한한 숫자여야 합니다.')
    shock, base, resist = (calibration[key] for key in
                           ('k_shock', 'k_base', 'k_resist'))
    if (zi_power < 0 or wu_power < 0 or not 0 <= distance_weight <= 1
            or not 0 <= shock <= 1 or not 0 < base <= 1
            or resist < 0 or base + resist > 1):
        raise ValueError('子午충 세력·거리·계수의 범위가 잘못되었습니다.')
    attack = zi_power * distance_weight
    share = attack / (attack + wu_power) if attack + wu_power else 0.0
    if attack == 0:
        return 0.0, 0.0
    wu_loss_rate = shock * share ** 2
    zi_loss_rate = distance_weight * (base + resist * (1 - share))
    return wu_loss_rate, zi_loss_rate


def allocate_branch_losses(base_power, candidates):
    """같은 지지의 손실률을 곱셈 집계하고 4자리 총손실을 쌍별 배분한다.

    candidates는 (관계 ID, 손실률)의 목록이다. 반올림 잔차는 소수부가
    큰 순서, 동률이면 관계 ID 순서로 0.0001씩 배분한다.
    """
    if not isinstance(base_power, (int, float)) or isinstance(base_power, bool) \
            or not isfinite(base_power) or base_power < 0:
        raise ValueError('기준 세력은 유한한 0 이상의 숫자여야 합니다.')
    ids = [relation_id for relation_id, _ in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError('동일한 관계 손실을 두 번 배분할 수 없습니다.')
    if any(not isinstance(rate, (int, float)) or isinstance(rate, bool)
           or not isfinite(rate) or not 0 <= rate <= 1
           for _, rate in candidates):
        raise ValueError('손실률은 0 이상 1 이하의 유한한 숫자여야 합니다.')
    if not candidates:
        return {}
    rates = [rate for _, rate in candidates]
    rate_sum = sum(rates)
    if rate_sum == 0:
        return {relation_id: 0.0 for relation_id in ids}
    total_loss = base_power * (1 - prod(1 - rate for rate in rates))
    total_units = round(total_loss * 10000)
    raw_units = [total_units * rate / rate_sum for rate in rates]
    units = [floor(value) for value in raw_units]
    remainder = total_units - sum(units)
    order = sorted(range(len(ids)), key=lambda i: (-(raw_units[i] - units[i]), ids[i]))
    for index in order[:remainder]:
        units[index] += 1
    return {relation_id: -count / 10000 for relation_id, count in zip(ids, units)}
