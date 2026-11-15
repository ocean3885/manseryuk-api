# 일주·월지 공통 해설의 점진 생성

2026-11-15. 기본 만세력 조회 `GET /`의 `day_month_interpretation`에만 연결한다.
관계 패턴 565개 해설 생성·승인·API 연결과는 별개다.

## 조회 계약

- 키는 원국의 한자 일주 2글자와 월지 1글자다. 60 × 12 = 최대 720조합이다.
- DB에 `ready` 해설이 있으면 `{day_pillar, month_branch, explanation}`을 반환한다.
- 없으면 `day_month_interpretation: null`을 반환하고 대기 행을 기록한다.
  `DAY_MONTH_INTERPRETATION_ENABLED=1`이면 응답 이후 Gemini 생성 작업을 시작한다.
  성공하면 같은 조합의 다음 조회부터 해설이 나온다.
- 이 문구는 일주·월지 **조합의 일반적 상징 해설**이다. 원국 전체 판정으로 표시하지 않는다.
- `/character-details`, `/relation-index`, `/cycle-analysis`는 이 해설을 조회하거나 생성하지 않는다.
- 해설 DB 오류나 생성 실패가 기본 만세력 응답을 막지 않는다.

## 저장과 운영

`interpretations.db`의 `day_month_interpretations` 테이블에 한 조합당 한 행을 둔다.
기존 v1 DB는 처음 쓰기 조회 또는 `init`에서 v2로 이전하고 관계 패턴 작성본을 유지한다.
파일이 없으면 기본 조회가 빈 v2 DB를 만든다. 관계 패턴 카탈로그를 채우려면
`scripts/interpretation_rules.py init`을 별도로 실행한다. 생성 해설은 JSON 시드에서
복원할 수 없으므로 DB 파일을 백업한다.

상태는 `pending` → `generating` → `ready`이며 실패 시 `failed`로 기록한다.
이 테이블의 `ready`는 생성과 형식 검증 완료를 뜻하며 전문가 검토 완료 상태는 아니다.
DB의 원자적 선점으로 같은 조합에 조회가 몰려도 한 번에 하나의 생성만 진행한다.
실패 후 1시간, 실행 중 작업이 중단되면 2분 후 다음 조회에서 다시 시도한다.
키와 모델 오류는 서버 로그에 종류만 남기고 해설이나 응답에 오류 본문을 싣지 않는다.

프로젝트 루트 `.env` 또는 서버 환경변수에 다음을 설정한다.

```text
GEMINI_API_KEY=<서버의 키>
GEMINI_MODEL=gemini-3.1-flash-lite
DAY_MONTH_INTERPRETATION_ENABLED=1
```

기본값은 기능 비활성이다. 비활성 상태에서는 해설 DB에 접근하지 않는다.
기능을 켠 뒤 조합을 조회하면 누락분을 생성한다. 설정 변경 후 서버를 재시작한다.
LLM에는 일주와 월지만 전달하며 출생일·시각·성별은 보내지 않는다.
응답의 JSON 구조와 길이(500~1200자)를 검증한 뒤 저장한다.
내용 검토가 자동으로 완료되는 것은 아니므로 초기 운영에서는 표본을 읽고
필요한 문구를 DB에서 수정한다.

전체 테스트에서는 외부 생성 작업을 끈다.

```bash
DAY_MONTH_INTERPRETATION_ENABLED=0 .venv312/bin/python -m unittest discover -s tests
```
