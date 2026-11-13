# 해설 DB 기본 패턴과 검색 계약

작성일: 2026-11-13. 사용자 요청에 따라 별도 SQLite의 기본 칼럼·빈 해설 패턴·검색 기능을 구현했다.
기존 관계 판정과 십성 결과를 재사용한다. API 응답 연결, 별도 LLM 작성·가져오기,
고 크기·개고 조건과 그 해설은 후속 단계다.

## 저장소와 재생성

```bash
.venv312/bin/python scripts/interpretation_rules.py init
```

- 별도 `interpretations.db`에 `interpretation_rules` 테이블을 생성한다.
- 기존 달력 `manseryuk.db`와 SQLAlchemy 모델을 공유하지 않는다.
- `data/interpretation_patterns.json`은 현재 규칙에서 재생성하는 빈 기본 카탈로그다.
- 런타임 DB와 SQLite 보조 파일은 Git에서 제외한다. 새 작업환경에서는 위 명령을 실행한다.
- 초기화는 같은 패턴·조건의 기존 행을 유지한다. 이미 작성한 해설·상태를 초기화하지 않는다.
- JSON 시드 파일은 항상 빈 기본 카탈로그다. 작성한 DB 해설을 내보내는 파일이 아니므로,
  해설 작성 이후에는 DB 파일을 별도 보관해야 한다. 작성용 내보내기는 아래 명령을 사용한다.
  상태를 포함한 전체 DB 백업과 작성 결과 가져오기는 별도 범위다.
- 서버 시작이나 조회로 DB를 자동 생성하지 않는다. 조회 시 파일이 없으면 오류를 알린다.

선택적으로 `init --database <경로> --seed-output <JSON 경로>`를 쓸 수 있다.
달력 DB를 해설 DB로 사용할 수 없고, JSON 출력으로 DB 파일을 덮어쓸 수 없다.
다른 스키마의 SQLite 파일도 초기화 대상으로 받지 않는다.

## 테이블

| 칼럼 | 의미 |
| --- | --- |
| `rule_id` | 정규화한 패턴·조건의 SHA-256 기반 고정 ID, 기본키 |
| `layer` | `stem`, `branch`, `group`, `same_pillar` |
| `relation_type` | 기존 관계 종류의 코드 |
| `participant_pattern` | 참여 십성의 JSON 배열 |
| `conditions_json` | 검색에 필요한 조건의 JSON 객체 |
| `explanation` | 해설. 초기값 SQL `NULL` |
| `content_status` | `empty`, `draft`, `ready`. 초기값 `empty` |

`layer`·종류·참여 패턴·조건의 조합은 고유하다. 앞의 세 칼럼과 작성 상태에 조회 인덱스를 둔다.
해설 내용 변경으로 ID가 바뀌지 않는다. `empty`는 해설이 NULL이어야 하며,
`draft`·`ready`는 공백이 아닌 해설이 있어야 한다. DB 스키마 버전은 `PRAGMA user_version=1`이다.

## 기본 카탈로그

현재 등록된 관계표와 십성 계산을 열 일간에 적용하고 중복 패턴을 합친 **565개**다.
모든 실제 팔자의 발생 빈도나 조건별 전체 해석 수를 뜻하지 않는다.

| 계층 | 개수 | 관계 |
| --- | ---: | --- |
| 천간 | 40 | 합·충·극 |
| 지지 | 275 | 육합·충·천·파·형·자형·반합·공합·암합·생·극·동지 |
| 다자 | 100 | 삼합·방합·삼형 |
| 동주 | 150 | 오행 관계·자합 |

- 합·충 등 무방향 관계는 참여 십성을 고정 순서로 정렬한다.
- 생·극은 작용 주체 → 대상의 순서를 유지한다.
- 동주는 천간 → 지지 순서다. `element`는 구체적인 오행 관계도 조건에 포함한다.
- 원자료의 `일간`은 검색에서 `비견`으로 변환하고, 본인 참여 여부는 `has_day_master`로 보존한다.
- 삼합 등은 네 글자가 한 관계에 묶여 있어도 실제 세 글자 조합별로 검색한다.
- 투간, 고 역할·크기·개고 등의 전용 패턴은 이번 카탈로그에 없다.

현재 기본 행은 모두 `scope=natal` 조건을 갖는다. 운이 섞인 후보에는 자동 적용하지 않는다.
고의 역할과 같은 추가 검색 차원은 근거와 해설의 단위를 정한 뒤 확장한다.

## 지원 조건과 선택

조건은 허용된 키와 자료형의 정확한 일치만 지원한다. 실행식이나 임의 SQL을 받지 않는다.

| 조건 | 지원 값 |
| --- | --- |
| `scope` | `natal`, `cross_context` |
| `activation_status` | `detected`, `candidate_only`, `potential`, `conditional`, `suppressed`, `active` |
| `element_relation` | `stem_generates_branch`, `branch_generates_stem`, `stem_controls_branch`, `branch_controls_stem`, `same_element` |
| `is_adjacent` | JSON 불리언 |
| `has_day_master` | JSON 불리언 |

조건에 필요한 사실이 검색 입력에 없으면 불일치다. 일치한 행 중 조건 수가 가장 많은 행을 고른다.
같은 수의 조건을 가진 행이 여러 개 남으면 `AmbiguousInterpretationError`로 알린다.
이 경우 해설 검토자가 조건을 정리해야 하며 임의로 하나를 선택하지 않는다.
한 관계에서 같은 패턴·사실의 검색이 중복되면 한 번으로 합친다.

기본 검색은 `ready`만 조회한다. 빈 행·초안을 확인하려면 `include_unwritten=True`를 사용한다.
미작성 행이 더 구체적이어도 기본 검색에서는 제외하므로 일치하는 작성 완료 행을 사용할 수 있다.
조회 연결은 읽기 전용이며 파일이나 내용을 변경하지 않는다.

## 사용 예시

```bash
.venv312/bin/python scripts/interpretation_rules.py lookup \
  --layer stem --relation-type control --participants 식신 편관 \
  --include-unwritten
```

빈 기본 행을 반환하며 핵심 내용은 다음과 같다. `--include-unwritten`을 빼면 초기에는 `rule: null`이다.

```json
{
  "layer": "stem",
  "relation_type": "control",
  "participant_pattern": ["식신", "편관"],
  "conditions_json": {"scope": "natal"},
  "explanation": null,
  "content_status": "empty"
}
```

기존 글자·운 조회 응답을 JSON으로 저장했다면 관계 ID로 검색할 수 있다.

```bash
.venv312/bin/python scripts/interpretation_rules.py lookup-graph \
  --graph /tmp/character-details.json --relation-id '<실제 관계 ID>' --include-unwritten
```

Python에서는 `queries_for_relation(graph, relation_id)`로 검색 입력을 얻고,
각 입력에 `find_rule(query, database, include_unwritten=True)`를 호출한다.
어댑터는 이미 계산된 십성·작용 방향·상태·실제 참여 조합을 사용한다.
운 후보에 원국 인접 조건을 만들어 붙이지 않는다. 지원하지 않는 관계는 빈 검색 목록을 반환한다.

## 작성용 JSON 내보내기

현재 DB를 읽기 전용으로 조회하여 별도 작성 파일을 만든다. 기본 대상은 `empty` 상태 전체다.
초기 카탈로그를 다시 생성하는 동작이 아니므로 `draft`·`ready`를 선택하면 실제 작성한 해설도 포함한다.

```bash
# 미작성 전체
.venv312/bin/python scripts/interpretation_rules.py export \
  --output data/my_authoring_all.json

# 천간극 20개로 작성 기준 점검
.venv312/bin/python scripts/interpretation_rules.py export \
  --output data/my_authoring_sample20.json --layer stem --relation-type control --limit 20

# 같은 필터의 다음 묶음
.venv312/bin/python scripts/interpretation_rules.py export \
  --output data/my_authoring_next.json --limit 20 --offset 20
```

`--database`, `--status empty|draft|ready`, `--layer`, `--relation-type`,
`--limit`, `--offset`으로 대상을 고른다. 기존 출력 파일은 덮어쓰지 않으며 새 파일명을 사용한다.
`limit`은 양의 정수, `offset`은 0 이상의 정수다.
필터 조합이 유효하지 않거나 DB가 없으면 출력 파일을 만들지 않는다.

출력에는 `format_version: 1`, `purpose: interpretation_authoring`, 선택 필터,
일치 개수·추출 개수·다음 offset, `writing_guide`, `rules`가 있다.
각 항목은 ID·계층·종류·참여 십성·조건·해설의 여섯 필드다.
작성 상태는 선택 메타데이터로만 제공하며 LLM에게 승인 상태를 작성시키지 않는다.
정렬은 계층·종류·참여 패턴·조건·ID 순서로 고정한다. DB가 같으면 같은 순서로 나온다.
분할하는 동안 상태나 행이 변경되면 대상 집합도 바뀌므로 한 번에 전체를 내보내거나,
분할 작업이 끝날 때까지 동일한 DB 상태를 유지한다.

이번 작업에서 생성한 파일:

- [미작성 전체 565개](../data/interpretation_authoring_all.json)
- [천간극 검토용 20개](../data/interpretation_authoring_sample20.json)

별도 LLM에 파일과 함께 다음 지시를 전달한다.

> 파일의 writing_guide를 따라 rules의 explanation만 한국어로 작성하고 완성된 JSON을 반환하세요.
> ID·패턴·조건은 유지하세요. 작성 근거가 부족한 항목은 null을 유지하세요.

가이드는 방향·일간 본인 구분과 2~3문장 형식을 설명한다.
이 자료는 특정 개인의 원국이 아니므로 실제 글자·위치·통근·세력·주변 관계를 지어내지 않는다.
관계 존재만으로 합화·실제 손상·길흉·성과를 확정하거나 미평가 판정을 해설로 대체하지 않는다.
작성된 결과는 원본과 다른 파일로 저장한다. 현재는 DB에 가져오거나 API에 자동 적용하지 않는다.

## 검증과 다음 단계

`tests/test_interpretation_store.py`에서 생성의 재현성, 고정 ID, 방향, 미작성 검색,
재초기화 시 작성본 보존, 조건 우선순위·충돌, 달력·DB 출력 보호,
일간 변환·반복 삼합·실제 원국 관계와 운 후보의 검색을 확인한다.
기초 구현 시 신규 18개와 전체 322개 테스트가 통과했다.

`tests/test_interpretation_export.py`에서 실제 저장 행·작성본·ID 보존, 필터·분할,
잘못된 입력·저장 행 검증, 기존 출력·달력·DB 파일 보호를 추가 검증한다.
내보내기 신규 8개, 관련 26개, 전체 330개 테스트가 통과했다.

다음 단계는 작성 결과 가져오기와 검토 절차다. 별도 LLM으로 해설을 작성하고
`draft` 검토 후 `ready`로 승인한다. API 연결은 이 과정을 정한 뒤 진행한다.
현재는 API 필드·기존 설명을 변경하거나 외부 LLM을 호출하지 않는다.
