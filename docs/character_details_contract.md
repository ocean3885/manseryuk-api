# 글자별 통합 조회와 운세 확장 계약

2026-11-13 부가 필드 확장: 관계별 `participant_details`, `status_reasons`,
`element_relation`, `evidence`, `presentation` 및 통근 설명·근거를 제공한다.
십성은 기존 원국 일간 기준 속성에서 복사한다. 기존 필드·판정·ID는 유지한다.
[근거 계약 및 판정 범위](relation_activation_audit.md),
[자연어 표시 계약](relation_presentation_contract.md)을 함께 참조한다.

2026-11-13 원자료 관계 구조 정리: `characters[*].analysis.relations`도
[글자별 원자료 관계 계약](raw_character_relations_contract.md)을 따른다.
`six_haps` 배열 통일, `candidate_element` 이름 변경, `strength` 분리와 빈 배열
통일은 기존 프론트엔드 호환을 유지하지 않는 변경이다. 중앙 관계 ID는 유지한다.

## 현재 API

`GET /character-details`는 기존 `/`와 동일한 `year`, `month`, `day`, `hour`, `min`, `sl`, `gen`을 받는다. 원국 계산을 한 번 실행하고 기존 관계 조회 조립기를 거쳐 통합 결과를 만든다. 기존 `/`, `/relation-index`는 유지한다. 새로운 명리 규칙이나 대운·세운 관계 계산을 추가한 것은 아니다.

응답 `schema_version`은 `1.0-draft`다. 프론트엔드는 이 버전을 확인하고 다음 세 사전을 이용한다.

| 필드 | 역할 |
| --- | --- |
| `contexts` | 원국·대운·세운의 소속, 인스턴스, 선택 조건, 계산 상태 |
| `characters` | 고유 ID별 속성·기둥 정보·기존 분석·통근 및 관계 참조 |
| `relations` | 중복 계산 없이 보존한 중앙 관계 본문 |
| `coverage` | 계산 범위, 미평가 범위·기전, 잠정 규칙 범위 |

현재 `contexts`에는 `natal.chart`만 있고 `coverage.not_evaluated_scopes`는 `daewoon`, `sewoon`이다. 기존 기본 API에 대운 목록이 있더라도 새 통합 조회에서 대운 관계가 계산됐다는 뜻은 아니다. 이 경로는 대운·세운 선택 파라미터를 아직 지원하지 않는다.

## ID와 참조 규칙

글자 ID는 `{context_id}.{position}.{kind}`, 소속 ID는 `{scope}.{instance}`다. 예:

- 원국: `natal.chart.year.stem`, `natal.chart.day.branch`
- 미래 대운 어댑터 예: `daewoon.period_0.cycle.stem`
- 미래 세운 어댑터 예: `sewoon.year_2026.cycle.branch`

뒤의 두 예시는 예약된 실행 결과가 아닌 확장 규칙이다. `instance`에는 안정적인 기간 식별자를 사용한다. 글자가 같아도 소속·위치가 다르면 별개 노드다. 기간의 시작·종료, 절입 기준, 선택 연도 등은 `contexts[*].selection`에 기록하고 실제 경계 계산을 구현할 때 계약을 구체화한다. 인스턴스는 영문·숫자·밑줄을 허용한다.

현재 원국 관계 ID는 `natal.chart:{기존 관계 ID}`다. 기존 ID는 `source_relation_id`에 보존한다. `source_refs`는 기존 계산 결과에 대한 출처이므로 기존 ID와 경로를 유지한다. 관계의 `participants`, `direction`, `formation_candidates`에는 새 글자 ID를 사용한다.

대운·세운 어댑터를 추가할 때에는 그 어댑터의 안정적인 관계 ID를 생성한다. 원국↔대운, 원국↔세운, 대운↔세운 및 세 소속이 함께 참여하는 다자 관계를 모두 같은 `UnifiedRelation`으로 표현할 수 있다. `context_ids`는 참여 글자의 실제 소속 집합과 일치해야 한다. 소속이 다른 글자들을 기존 네 기둥 전용 계산기에 그대로 넣지 않는다. 별도의 탐지 어댑터가 검증된 규칙을 사용하여 공통 계약으로 옮겨야 한다.

## 프론트엔드 사용 기준

| 표시 내용 | 사용할 데이터 |
| --- | --- |
| 달력·성별 등 메타, 원국 표, 대운·세운 선택 목록 | `/`의 `calendar`, `meta`, `four_pillars`, `daewoon`, `cycles` |
| 원국 글자 상세 | `/character-details`의 `characters[ID]` |
| 선택 운의 글자·관계 상세 | `/cycle-analysis`의 `characters[ID]`, `relations[ID]` |
| 한글·한자·오행·음양·십성·색상 | `characters[ID].attributes` |
| 지장간·운성·신살 | `characters[ID].pillar_attributes` (기둥 단위 정보) |
| 관계 제목·배지·본문·이유 | `relations[ID].presentation` |
| 통근과 타주 지원 | `characters[ID].rooting` 및 그 `reason`, `evidence` |
| 계산·미평가 범위 | `coverage`, 운의 `selection`, 글자의 `analysis.calculation_status` |

관계 화면은 `relation_ids`로 중앙 `relations`를 조회하고 `presentation`을 표시한다.
`analysis`는 글자별 원본 분석 자료이므로 그 안의 숫자 인덱스·관계 문장을
새 관계 표시와 섞어 재조립하지 않는다. 같은 관계의 제목·이유를 중복 표시할 필요는 없다.

`rooting=null`만 보고 "통근 없음"으로 표시하지 않는다. 지지는 통근 대상이 아니고,
운 천간은 현재 통근 미평가다. 원국 천간의 동주 통근 여부는
`has_same_pillar_root`로 확인한다. 운에 없는 신살 등 선택적 항목도
명시적인 빈 결과와 미제공/미평가를 구분한다.

`presentation.explanation_status=partial`일 때는 제공된 제목·상태·설명만 표시한다.
`missing_evidence_codes`는 개발용 누락 정보이며 최종 사용자에게 원문 코드나
추정한 판정 이유를 표시하지 않는다. `complete`도 현재 평가 범위 안의 설명 완결성을
뜻하며, 실제 영향까지 전부 평가했다는 의미는 아니다.

2026-11-13 제거한 `/analysis-summary`의 카드 묶음·표시 순서·추가/기존 비교는
이 응답에 추가하지 않는다. 화면 배치와 목록 선택은 기존 글자·관계 참조를 이용한다.

### 글자 선택 순서

1. `characters[선택한 ID]`의 `attributes`에서 오행·음양·십신·표시 색상 등을 읽는다.
2. `pillar_attributes`에서 지장간·운성·신살 등 기둥 공통 정보를 읽는다. 이는 기둥 정보이며 각 글자에 독립 신살이 계산됐다는 뜻은 아니다.
3. 천간이면 `rooting`에서 동주 통근 여부·강도, 타주 지원과 영향 미평가 상태를 읽는다. 지지는 `rooting=null`이다.
4. `relation_ids`로 `relations`의 본문을 조회한다. `transmission_relation_ids`는 투간 관계만 골라 놓은 참조다. 투간 방향은 출처 지지→대상 천간이다.
5. 상대 글자의 `context_id`로 원국·대운·세운 관계를 분류한다. 다자 관계는 참여자가 둘을 넘을 수 있다.

`analysis`는 기존 글자별 분석 원본의 복사본이다. 이 안의 `position`, `from_idx`, 기존 관계 설명 등은 원본 표현을 유지한다. 새 ID로 화면의 관계를 연결할 때에는 중앙 `relations`와 `relation_ids`를 사용한다. 단순 설명 필드에서 관계를 다시 탐지하거나 통근 영향을 계산하지 않는다.

동주 통근 영향은 `root_impact_status=not_evaluated`, `root_impact_score=null`이다. `remaining_score`는 호환용으로 원점수를 유지하며, 무손상 판정값이 아니다. 관련 합·충·형·파·천의 존재와 통근 소멸을 분리한다. 원국과 운의 관계가 생겨도 원국 계산 결과를 덮어쓰지 않는다.

## 검증과 후속 확장

공통 모델은 소속·위치 ID, 중앙 관계와 글자별 역참조, 방향·다자 조합, 투간 참조, 동주·타주 통근 참조, 계산 범위를 검사한다. 기존 관계 모델은 현재 원국 생산 결과의 규칙·출처 정합성을 먼저 검사한다. 공통 모델이 미래 탐지 규칙의 명리적 타당성을 보증하지는 않는다.

테스트는 실제 달력 DB와 HTTP 응답, 원본 비변경, 누락 참조·잘못된 통근 참조 거부, 같은 글자의 서로 다른 소속과 소속 간 관계 수용을 확인한다. 소속 간 관계 테스트는 합성 계약 자료이며 대운·세운 계산의 검증이 아니다.

운 선택·기간 경계와 소속 간 후보 탐지는 별도 [운 조회 API](cycle_analysis_contract.md)에 구현되어 있다. 이 원국 조회 경로는 원국 전용으로 유지한다. 통근 영향은 계속 미평가다. 후속 작업은 [현행 문서 목록](README.md)과 새 요청으로 정하며, 수치 판정 자동 구현으로 이어가지 않는다.
