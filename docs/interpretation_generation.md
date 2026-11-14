# Gemini 해설 작성 명령

작성일: 2026-11-14. 사용자 요청으로 환경변수 `GEMINI_API_KEY`를 사용하는 해설 작성 기능을 추가했다.
기존 [작성용 JSON](interpretation_database_contract.md#작성용-json-내보내기)의 빈 `explanation`만 작성한다.
루트 API·명리 판정·DB·승인 상태는 변경하지 않는다.

## 현재 상태: 실험용, 서비스 적용 보류

2026-11-14 실제 연결과 10개 표본 생성을 확인했다. 하지만 방향이 없는 관계의 방향 오독,
삼합의 세력 형성 확정, 자합의 본기·지장간 혼동을 발견했다.
[소량 검토](explanation_pilot_review.md)에 생성 원문·문제점·수정 예시를 보관한다.
생성 완료와 구조 검증은 해설 내용의 정확성을 보장하지 않는다.

Gemini 연결·구조화 응답 검증·중간 저장·재개 코드는 향후 활용을 위해 보존한다.
현재 패턴 해설의 전체 생성·DB 가져오기·승인·서비스 API 연결은 보류한다.
해설 DB·카탈로그·검색·내보내기도 유지하며, 새 범용 LLM 계층이나 다른 용도는 추가하지 않는다.
검토용 `data/review/`의 입력·결과는 승인된 해설이 아니며 서비스 데이터로 사용하지 않는다.

현재 환경에서 키 전달과 도메인 허용을 확인했다. 모델 목록 조회는 HTTP 200,
기존 기본 모델 `gemini-2.5-flash-lite`의 생성 요청은 HTTP 404였다.
`--model gemini-3.1-flash-lite`로 1개 연결 확인과 10개 표본 생성에 성공했다.
코드의 기본 모델은 변경하지 않았으므로 추후 명시적 실험 시 검증한 모델을 지정한다.
API 키·허용 도메인·모델 이용 가능 여부는 환경과 시점에 따라 다시 확인한다.

## 환경 설정

프로젝트 루트(`main.py`와 같은 폴더)의 `.env`를 CLI와 API 시작 시 자동으로 읽는다.
`.env.example`을 복사해 서버에서 키를 입력하면 별도의 dotenv 실행 명령이 필요 없다.
서버 환경변수 > `.env` 순서로 적용하며, 파일이 없어도 오류가 나지 않는다.
`.env` 변경 후 API 프로세스를 재시작한다. CLI는 다음 실행부터 읽는다.
명시적인 `--model` 옵션은 여전히 `GEMINI_MODEL`보다 우선한다.


- 비밀값: `GEMINI_API_KEY`. 명령 인자로 키 값을 받거나 코드·JSON에 저장하지 않는다.
- 모델: `--model` → 환경변수 `GEMINI_MODEL` → 기본 `gemini-2.5-flash-lite` 순서로 선택한다.
- API 호스트: `generativelanguage.googleapis.com`. 실행환경에서 HTTPS 접속이 허용되어야 한다.
- 기존 `httpx`로 Gemini `v1beta/models/{model}:generateContent`를 호출한다. 추가 SDK 설치는 없다.
- 키는 `x-goog-api-key` 헤더로 전송한다. TLS 검증과 환경의 프록시·CA 설정을 유지하고 리다이렉트는 따르지 않는다.

키를 환경 설정에 등록한 뒤 현재 컴퓨터에도 적용되었는지 확인한다. 키 값 자체를 채팅에 전달하지 않는다.
초기 개발 시점에는 키 부재와 프록시 CONNECT 403으로 호출하지 못했다.
이후 연결 확인 결과와 적용 보류 결정은 위 현재 상태를 우선한다.

## 사용 순서

호출 없이 대상과 키 반영 여부부터 확인한다. 이 단계는 키가 없어도 실행되며 파일을 만들지 않는다.

```bash
.venv312/bin/python scripts/interpretation_rules.py generate \
  --input data/interpretation_authoring_sample20.json \
  --output data/generated/control_first5.json \
  --limit 5 --dry-run
```

실제 작성은 `--dry-run`을 빼고 실행한다.

```bash
.venv312/bin/python scripts/interpretation_rules.py generate \
  --input data/interpretation_authoring_sample20.json \
  --output data/generated/control_first5.json \
  --limit 5
```

- 기본은 미작성 **최대 5개**, 한 요청에 5개다. `--limit`으로 이번 실행의 최대 요청 항목 수를 지정한다.
- `--batch-size`는 1~10, 기본 5다. 예를 들어 20개는 `--limit 20 --batch-size 5`로 네 묶음에 나눠 요청한다.
- 기본 출력 한도는 요청당 4096토큰이며 `--max-output-tokens`로 조절한다.
  한도 초과로 응답이 잘리면 해당 묶음을 적용하지 않는다.
- 이미 문자열 해설이 있는 항목은 건너뛴다. 기존 작성본·초기 입력 파일·출력 파일을 덮어쓰지 않는다.
- `--output`은 반드시 새 JSON 경로여야 한다. 키가 없으면 실제 호출 전에 실패하며 출력 파일도 만들지 않는다.
- 요청 시간 제한은 45초다. HTTP 오류·시간 초과에 자동 재시도하지 않는다.
- 동시 실행 없이 순차 호출한다. 범위를 줄여 먼저 해설 품질을 확인한다.

## 검증과 저장

입력의 형식 버전·목적·필드 구성·ID·참여 패턴·조건·기존 해설·ID 중복을 검사한다.
Gemini에 구조화된 JSON 응답을 요청하고 반환값은 ID와 해설만 받는다.

- 요청한 모든 ID가 정확히 한 번씩 있어야 한다. 누락·중복·미등록 ID와 추가 필드를 거부한다.
- 해설은 공백이 아닌 최대 2000자 문자열 또는 `null`이다.
- JSON 중복 키·NaN·Infinity, 잘린 응답·차단·비정상 종료도 거부한다.
- 묶음 전체를 검증한 후 해당 묶음의 해설만 적용한다. ID·패턴·조건은 모델 응답으로 교체하지 않는다.
- 한국어 2~3문장, 실제 원국 정보 창작 금지, 일간 본인 구분, 합화·손상·길흉 확정 금지를
  시스템 지침으로 적용한다. 이 지침은 내용의 정확성을 자동 보장하지 않으므로 작성본 검토가 필요하다.

새 출력 파일에 최초 상태를 저장하고, 검증된 묶음마다 같은 디렉터리의 임시 파일을 거쳐
원자적으로 교체한다. 후속 요청이 실패해도 앞서 저장한 묶음은 남는다.
실패한 묶음은 반영하지 않으며 명령은 오류 상태로 종료한다.

출력은 기존 작성용 JSON과 같은 `rules`를 유지하고 실행 메타데이터 `generation`을 추가한다.
`provider`, `model`, 처리 상태, 선택·처리·작성 개수, 완료 묶음 수, 토큰 사용량을 기록한다.
사용량은 성공적으로 해석·검증한 응답에서 제공된 수치만 합산하며 실제 청구 내역 전체를 뜻하지 않는다.
키·요청 헤더·원격 오류 본문은 결과와 오류 메시지에 포함하지 않는다.

## 재개

이전 출력 파일을 다음 입력으로 쓰고 새로운 출력 파일명을 지정한다.

```bash
.venv312/bin/python scripts/interpretation_rules.py generate \
  --input data/generated/control_first5.json \
  --output data/generated/control_next5.json \
  --limit 5
```

이미 작성한 해설은 보존하며 남은 NULL 중 처음 다섯 개를 선택한다.
모델이 근거 부족으로 NULL을 반환한 항목도 새 실행에서는 다시 대상이 될 수 있다.
`generation`은 이번 실행의 기록으로 교체한다. 이전 실행 기록이 필요하면 입력 파일도 함께 보관한다.
NULL 항목 수가 0이면 키나 네트워크 없이 복사본과 완료 메타데이터만 저장한다.

생성의 `completed`는 요청 처리가 끝났다는 뜻이며 검토 완료·`ready` 승인 상태가 아니다.
결과 검토 → `draft` 가져오기 → 검토한 해설의 `ready` 전환은 후속 작업이다.
API 응답에는 이번 결과를 자동 연결하지 않는다.

## 검증 범위

`tests/test_interpretation_generation.py`에서 모의 HTTP 응답으로 요청 형식·헤더,
ID·해설 검증, 오류의 키 노출 방지, 기존 작성본 보존, 실제 CLI 중간 저장·재개 대상을 검사한다.
실제 키를 사용하거나 유료 호출하는 테스트는 없다.
