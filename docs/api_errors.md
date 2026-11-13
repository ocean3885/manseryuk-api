# API 공통 오류 응답

네 조회 API의 400·404·422·500 응답은 다음 공통 구조를 사용한다. 성공 응답과 기존 HTTP 상태 코드는 유지한다. 경로 없음 404, 메서드 오류 405 등 프레임워크 HTTP 오류도 같은 형식이다.

```json
{
  "status": "error",
  "code": "invalid_birth_input",
  "message": "hour는 0~23 범위여야 합니다.",
  "errors": [{
    "field": "hour",
    "location": ["query", "hour"],
    "code": "invalid_birth_input",
    "message": "hour는 0~23 범위여야 합니다.",
    "constraints": {"minimum": 0, "maximum": 23}
  }],
  "detail": "hour는 0~23 범위여야 합니다.",
  "correct_usage": "아래와 같은 형식으로 요청을 보내주세요.",
  "example": "/?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남",
  "required_fields": {
    "year": "int (연도)",
    "month": "str (월, 예: '5')",
    "day": "str (일, 예: '12')",
    "hour": "int (시간, 0-23)",
    "min": "int (분, 0-59)",
    "sl": "str ('sol' ,'lun', 'lun_y')",
    "gen": "str ('남' , '여')"
  }
}
```

## 코드와 사용법

| HTTP | code | 의미 |
| --- | --- | --- |
| 400 | `invalid_birth_input` | 출생 입력의 범위·날짜·선택값 오류 |
| 400 | `invalid_cycle_selection` | 대운 번호·세운 연도 중 하나만 지정해야 함 |
| 400 | `daewoon_index_out_of_range` | 대운 번호가 제공 범위 밖 |
| 400 | `sewoon_year_out_of_range` | 세운 연도가 제공 범위 밖 |
| 400 | `daewoon_unavailable` | 시작 절기 자료 부족 또는 세운 연도에 대응하는 대운이 없음 |
| 404 | `calendar_date_not_found` | 요청한 양력·음력 평달·윤달 레코드 없음 |
| 422 | `request_validation_error` | 필수 인자 누락·자료형 오류 |
| 500 이상 | `internal_error` | 서버 처리 실패 |
| 기타 HTTP 오류 | `http_상태코드` | 예: `http_404`, `http_405` |

클라이언트는 HTTP 상태와 `code`로 분기하고 `errors`를 표시한다. 한 필드 오류는 `field`, `location`을 제공한다. 여러 필드의 조합 문제는 `field=null`이며 `constraints.fields` 또는 `exactly_one_of`로 관련 필드를 명시한다. 범위는 `minimum`·`maximum`, 선택값은 `allowed`, 세운의 실제 제공 목록은 `allowed_years`로 안내한다.

422의 각 항목 `code`는 Pydantic 검증 유형(`missing`, `int_parsing` 등)이다. 제출된 원본 값과 예외 내부 객체는 응답에 복사하지 않는다. 출생 입력의 업무 검증은 첫 오류를 반환하고 FastAPI 자료형 검증은 여러 오류를 반환할 수 있다.

## 호환성과 운영

- 기존 400·404의 문자열 `detail`을 유지한다. 422에는 새 구조화 오류 목록을 `detail`에도 제공한다.
- 기존 422 안내 필드 `status`, `message`, `correct_usage`, `example`, `required_fields`를 유지하며 다른 오류에도 제공한다.
- `example`은 실제 요청 경로를 사용하고 `/cycle-analysis`에는 세운 선택 예제를 포함한다. 예제는 고정된 안내값이며 입력값을 반사하지 않는다.
- `required_fields`는 공통 사주 필수 입력만 나열한다. 운 선택은 둘 중 하나라는 조건을 `correct_usage`와 선택 오류의 제약에 명시한다.
- HTTP 헤더(`Allow`, `Retry-After` 등)는 유지한다. 서버 오류의 상세 예외 메시지는 일반 안내로 대체하며, 예상하지 못한 예외는 서버 로그에 기록한다.
- 각 조회 경로의 OpenAPI에 `ApiErrorResponse` 모델을 등록한다.

테스트는 네 경로의 업무 오류, 선택 범위·윤달 레코드 없음, 422의 실제 오류 필드, 경로별 예제, OpenAPI 모델, 405 헤더 유지, 명시적 503 및 예상하지 못한 500의 내부 메시지 비노출을 검증한다.
