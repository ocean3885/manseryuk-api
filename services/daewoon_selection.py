"""Shared calendar-year selection; this does not calculate exact transition dates."""
PERIOD_BASIS = 'legacy_start_year_half_open'


def period_year_bounds(periods, position):
    start = periods[position]['start_year']
    end = periods[position + 1]['start_year'] if position + 1 < len(periods) else start + 10
    return start, end


def select_daewoon_year(periods, year):
    if not periods:
        return None, 'unavailable'
    if any(period_year_bounds(periods, i)[0] >= period_year_bounds(periods, i)[1]
           for i in range(len(periods))):
        raise ValueError('대운 시작 연도는 증가해야 합니다.')
    if year < periods[0]['start_year']:
        return None, 'before_first_period'
    for i, period in enumerate(periods):
        start, end = period_year_bounds(periods, i)
        if start <= year < end:
            return period, 'selected'
    return None, 'after_last_period'
