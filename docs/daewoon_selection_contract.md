# 대운 연도 선택의 공통 기준

`services/daewoon_selection.py`의 `select_daewoon_year`를 기본 응답의 `daewoon.current`와 `/cycle-analysis` 세운 조회가 공유한다. 소수 시작 나이와 정수 나이를 비교하여 전환 연도에 이전 대운이 선택되던 동작을 제거했다.

## 연도 경계

선택 구간은 `[현재 대운 start_year, 다음 대운 start_year)`다. 마지막 대운은 시작 연도부터 10년 미만이다. 예를 들어 시작 연도가 2002, 2012라면 2011년은 첫 대운, 2012년은 두 번째 대운이다. 기존 표시용 `end_year`가 2012여도 선택에 사용하지 않는다.

기존 소수 `start_age`, `end_age`와 표시용 `start_year`, `end_year`는 유지한다. 정확한 구간은 새 `selection_start_year`, `selection_end_year_exclusive`를 사용한다. 두 필드는 `daewoon.list`와 `current`, 운 조회의 대운 소속 선택 정보에 제공한다.

## 기본 응답의 선택 정보

`daewoon`에 다음 필드를 추가한다.

| 필드 | 의미 |
| --- | --- |
| `selection_year` | 현재 대운을 조회한 서버 현재 연도 |
| `period_basis` | `legacy_start_year_half_open` |
| `selection_status` | `selected`, `before_first_period`, `after_last_period`, `unavailable` |

선택된 대운이 없으면 `current=null`이다. 첫 대운 이전과 마지막 대운 이후를 구분하며, 목록 자체가 없으면 `unavailable`이다. `current.age`는 기존처럼 현재연도−출생연도로 유지하고, 대운 선택 조건으로 쓰지 않는다. 시작 연도가 증가하지 않는 목록은 공통 함수가 거부한다.

## 세운 조회

`/cycle-analysis`는 해당 연도의 세운 제공 여부를 확인한 후 같은 함수로 대운을 고른다. 첫 대운 이전에는 대운 없이 원국·세운을 반환한다. 마지막 대운 이후 또는 대운 목록이 없는 경우는 기존 계약대로 HTTP 400이다. 대운 번호 직접 선택은 해당 목록 항목을 반환한다.

이 기준은 연도 단위 연결 정책이다. 출생 시각·절입 시각을 반영하는 실제 교운 날짜와 같다고 해석하지 않는다. 날짜 기반 정밀 조회는 별도 계약으로 구성해야 한다.

검증은 소수 시작 나이 0.0·0.1·2.3·2.9·10.0, 시작/다음 시작/마지막 종료 연도, 빈 목록, 잘못된 순서, 원본 비변경 및 실제 사주의 모든 대운 시작 연도에서 두 조회의 일치를 확인한다.
