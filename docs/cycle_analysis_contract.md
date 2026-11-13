# 선택형 대운·세운 조회 계약

## API

`GET /cycle-analysis`는 기존 생년월일 파라미터 `year`, `month`, `day`, `hour`, `min`, `sl`, `gen`과 다음 선택 조건 중 **하나**를 받는다.

| 선택 | 추가 파라미터 | 반환 글자 |
| --- | --- | --- |
| 대운 클릭 | `daewoon_index=0` | 원국 8 + 대운 2 |
| 세운 클릭 | `sewoon_year=2026` | 원국 8 + 해당 대운 2 + 세운 2 |
| 첫 대운 이전의 세운 | `sewoon_year=출생연도` 등 | 원국 8 + 세운 2 |

예: `/cycle-analysis?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남&sewoon_year=2026`.

선택 목록은 기존 `/`의 `daewoon.list`와 `cycles.future_100`을 사용한다. 대운 번호는 응답의 0부터 시작하는 `index`다. 세운 조회에 대운 번호를 함께 보내지 않는다. 백엔드가 세운 연도에 대응하는 대운을 선택한다. 기존 `/`와 `/character-details`의 형식과 계산은 변경하지 않는다.

## 기존 계산 조사와 기간 선택 정책

- `daewoonNum`은 출생일 레코드와 순행·역행 방향의 절기 레코드 간 일수 차를 3으로 나누고 소수 한 자리로 반올림한다. 절입 시각과 출생 시각을 사용한 정밀 교운 시점 계산은 아니다.
- 필요한 방향의 가장 가까운 절기를 명시적으로 정렬해 선택한다. 자료 부족이면
  기본 API의 대운은 `start_age=null`, `start_age_status=term_data_unavailable`이고 목록은 빈 배열이다.
  이때 대운·세운 선택 API는 `daewoon_unavailable` 400을 반환한다. 원국 조회는 정상 제공한다.
- `build_daewoon`은 10개 대운을 생성하고, 시작 나이에 10을 더해 다음 대운을 구성한다. 기존 표시 연도는 `출생연도 + int(나이)`로 계산한다.
- 소수 나이에 따라 기존 `end_year`가 다음 대운 `start_year`와 겹칠 수 있다. 새 API의 **연도 단위 선택**은 `[start_year, 다음 start_year)`로 처리한다. 마지막 대운은 `[start_year, start_year+10)`이다. 따라서 다음 대운의 시작 연도는 새 대운에 속한다.
- 응답 소속의 `selection_start_year`, `selection_end_year_exclusive`가 실제 선택 범위다. 기존 `start_age`, `end_age`, `start_year`, `end_year`는 원본 표시값으로 보존한다. `period_basis=legacy_start_year_half_open`이 이 정책을 식별한다.
- `daewoon.current`와 세운 조회는 공통 `select_daewoon_year` 함수를 사용한다. 현재 대운은 서버 현재 연도, 세운 조회는 선택한 연도를 같은 반열린 구간에 대입한다. `daewoon.selection_year`, `selection_status`, `period_basis`와 각 항목의 `selection_start_year`, `selection_end_year_exclusive`를 제공한다. 실제 교운 날짜를 확정한 것은 아니다. [공통 선택 계약](daewoon_selection_contract.md)을 참고한다.
- `generate_future_cycles`는 출생 연도부터 출생 연도+99까지 제공한다. 1984년 甲子를 기준으로 연도 간지를 계산하고 원국 일간 기준 십신·운성을 붙인다. `age`는 세는 나이다. `daeun` 인자는 현재 이 연도 계산에 사용되지 않는다.
- 운의 연도 항목과 세운 소속 `selection`에 `age_basis=counting_age`를 제공한다.
  기본 응답의 `daewoon.current.age`도 같은 세는나이다. `cycles.childhood_10`은
  세운 목록의 첫 10개이며, 기존 `baby_10` 필드와 소운 명칭은 제거했다.
- 세운은 **달력 연도 단위 간지**를 재사용하며 입춘 전후 날짜·시각을 구분하지 않는다. `sewoon_basis=calendar_year_ganzhi_no_ipchun`으로 명시한다. 날짜 기반 운 분석은 이후 별도 계약이 필요하다.

## 응답 의미

기존 통합 구조 `contexts`, `characters`, `relations`, `coverage`에 선택 결과 `selection`을 추가한다. 공통 그래프 버전은 `1.0-draft`다.

- 원국 관계 본문과 기본 정보·통근 판정은 유지한다. 글자별 참조에는 운이 참여하는 관계가 추가된다.
- 대운 글자 ID: `daewoon.period_0.cycle.stem`, `daewoon.period_0.cycle.branch`.
- 세운 글자 ID: `sewoon.year_2026.cycle.stem`, `sewoon.year_2026.cycle.branch`.
- 운 글자의 기본 속성·십신은 기존 결과를 재사용한다. 지장간은 기존 상세표로 구성하고 운성은 기존 일간 기준 값을 사용한다.
- 운 소속과 글자의 `calculation_status=candidates_detected`는 **소속 간 관계 후보 탐지 완료**를 의미한다. 성립·경합·통근 영향까지 확정한 상태는 아니다.
- 운의 `relation_ids`와 `transmission_relation_ids`에 소속 간 관계 참조를 제공한다. 운의 동주 통근은 아직 평가하지 않아 `rooting=null`이다. 운 한 기둥 내부 관계는 이번 탐지 범위에 포함하지 않는다.
- `coverage.calculated_scopes`는 이번 응답에서 탐지에 참여한 소속을 포함한다. `not_evaluated_scopes`는 응답에 없는 소속이다. 세부 미평가 기전은 `not_evaluated_mechanisms`에 별도로 명시한다. `selection.cycle_relations_status=candidates_detected`, 운 탐지 규칙 버전은 `1.0.0-draft`다.
- 첫 대운 이전의 연도는 `selection.daewoon_status=before_first_period`, `daewoon_index=null`이고 대운 소속을 넣지 않는다.

## 오류 및 검증

선택 조건 누락·동시 지정, 대운 번호 범위 밖, 세운 제공 연도 범위 밖, 첫 대운 이후인데 대응 대운이 없는 경우는 HTTP 400이다. 자료형 오류와 필수 사주 입력 누락은 기존 FastAPI 검증에 따라 422다. 기존 사주 입력 검증·달력 DB 조회 오류도 그대로 적용한다.

테스트는 첫·마지막 대운, 첫 대운 이전, 시작·끝 연도의 반열린 구간, 겹치는 기존 표시 연도, 세운 제공 범위, 잘못된 선택, DB·HTTP 응답 및 원국 기본 판정 비변경을 확인한다. [소속 간 관계 탐지 계약](cycle_relation_detection.md)에 탐지 종류·상태·미평가 범위를 기록한다.
