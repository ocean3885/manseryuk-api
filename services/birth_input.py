"""Common validation before calendar lookup, including non-HTTP callers."""
from datetime import date
from core.api_errors import ApiError


def validate_birth_input(year, month, day, hour, minute, sl, gen):
    if sl not in ('sol', 'lun', 'lun_y'):
        raise ApiError(400, 'invalid_birth_input', "sl 파라미터는 'sol', 'lun', 'lun_y' 중 하나이어야 합니다.", field="sl", constraints={"allowed": ["sol", "lun", "lun_y"]})
    if gen not in ('남', '여'):
        raise ApiError(400, 'invalid_birth_input', "gen 파라미터는 '남' 또는 '여' 이어야 합니다.", field="gen", constraints={"allowed": ["남", "여"]})
    try:
        month_number = int(month)
    except (ValueError, TypeError):
        raise ApiError(400, 'invalid_birth_input', '월(month)은 숫자 형식이어야 합니다.', field='month', constraints={'type': 'integer'})
    try:
        day_number = int(day)
    except (ValueError, TypeError):
        raise ApiError(400, 'invalid_birth_input', '일(day)은 숫자 형식이어야 합니다.', field='day', constraints={'type': 'integer'})
    if not 1 <= year <= 9999:
        raise ApiError(400, 'invalid_birth_input', 'year는 1~9999 범위여야 합니다.', field='year', constraints={'minimum': 1, 'maximum': 9999})
    if not 0 <= hour <= 23:
        raise ApiError(400, 'invalid_birth_input', 'hour는 0~23 범위여야 합니다.', field='hour', constraints={'minimum': 0, 'maximum': 23})
    if not 0 <= minute <= 59:
        raise ApiError(400, 'invalid_birth_input', 'min은 0~59 범위여야 합니다.', field='min', constraints={'minimum': 0, 'maximum': 59})
    if sl == 'sol':
        try:
            date(year, month_number, day_number)
        except ValueError:
            raise ApiError(400, 'invalid_birth_input', '존재하지 않는 양력 날짜입니다.', constraints={'fields': ['year', 'month', 'day'], 'calendar': 'solar', 'valid_date_required': True})
    elif not (1 <= month_number <= 12 and 1 <= day_number <= 30):
        raise ApiError(400, 'invalid_birth_input', '음력 월은 1~12, 일은 1~30 범위여야 합니다.', field='month' if not 1 <= month_number <= 12 else 'day', constraints={'minimum': 1, 'maximum': 12 if not 1 <= month_number <= 12 else 30})
    return str(month_number), str(day_number)
