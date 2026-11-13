# 관계별 자연어 표시 계약

2026-11-13. 설명 규칙 `1.0.0`. 기존 상태·관계·점수는 변경하지 않는 부가 필드 확장이다.
공통 그래프의 schema_version은 `1.0-draft`를 유지한다.

## 제공 위치

- `/character-details`: `relations[ID].presentation`
- `/cycle-analysis`: 같은 위치. 원국 설명은 동일하며 운은 후보/사실 탐지 범위를 설명한다.

`/analysis-summary`는 제거했다. 별도 요약 카드나 그 기능의 이전 없이 위 두 API의
관계별 표시 정보를 사용한다. 기본 `/`의 `analysis.summary`는 별개로 유지한다.

LLM이나 외부 호출 없이 등록 규칙과 기존 근거로 생성한다. 사주를 다시 계산하지 않는다.
전체 구조·글자 선택 화면은 별도 표시 설계 범위이며 이번에는 관계 한 건의 설명을 완성한다.
통근은 기존 reason/transition_reasons를 제공하고 관계에 의한 손상을 추론하지 않는다.

## 필드

| 필드 | 화면 용도 |
| --- | --- |
| title | 위치·소속·십성이 포함된 관계 제목 |
| status_label | 원본 상태의 배지: 탐지·후보·잠재·조건부·억제·성립 |
| description | 참여 글자·오행 방향·투간·동주 자합의 사실 설명 |
| reasons[] | 근거가 연결된 설명 문장 |
| explanation_status | complete / partial |
| missing_evidence_codes | 설명할 근거가 부족하거나 아직 지원하지 않는 코드 |
| rule_version | 표현 규칙 버전 |

reasons 항목은 code, category, text, character_ids, relation_ids, evidence_indices를 갖는다.
category는 decision(판정), notice(주의), scope(평가 범위), structure(구성 관계)다.
프론트엔드는 code로 문장을 조립할 필요 없이 text를 표시하고, ID로 관련 글자를 강조한다.
evidence_indices는 해당 관계의 evidence 배열 위치이며 내부 규칙 경로를 사용자에게 출력할 필요는 없다.

원국의 `evidence[*].details.condition_evidence`에도 `summary`, 충 당사자의
`affected`·`cause` 및 `description`, 삼합 중신의 `middle_members`를 제공한다.
원자료를 직접 확인할 때에도 위치·글자·십성·판정 이유를 읽을 수 있다.
자세한 구조는 [원자료 관계 계약](raw_character_relations_contract.md)을 따른다.
이 근거 표시 확장은 기존 `presentation`의 설명 규칙과 판정을 바꾸지 않는다.

화면은 title → status_label → description → reasons[].text 순으로 표시할 수 있다.
실패 사유가 아닌 notice를 "성립하지 않은 이유"에 넣지 않는다.
여러 관계를 한 화면에 나열할 때 공통 scope 안내는 한 번만 표시해도 된다.

## 완결성의 의미

complete는 **현재 평가한 범위**에서 알려진 설명과 필요한 근거를 제공했다는 뜻이다.
공합 후보나 운 관계도 후보를 찾은 사실과 미평가 범위를 설명하면 complete가 될 수 있다.
성립·손상·실제 영향을 전부 평가했다는 의미가 아니다.

알 수 없는 사유나 누락된 원인 충·필수 근거는 partial과 missing_evidence_codes로 표시한다.
확인 가능한 제목·상태·본문은 유지하고 구체적 원인을 지어내지 않는다.
지장간·동주 오행 세부 유형이 없거나 active의 근거가 없을 때도 partial이다.

## 표시 원칙과 검증

- 십성은 기존 characters의 원국 일간 기준 값을 사용한다. 일간 본인은 `일간`이다.
- 제목은 원국 → 대운 → 세운, 연 → 월 → 일 → 시 → 운 위치 순으로 표시한다.
  원본 participants ID 순서나 방향을 바꾸지 않는다.
- 반복 글자의 다자 구조는 위치 조합별 문장을 따로 제공한다. 조합 수는 작용 횟수나 가산량이 아니다.
- 전체 구조와 구성 반합의 상태를 섞지 않는다. 같은 근거의 중복 문장은 병합한다.
- 원국 육합·삼합은 `탐지` 배지와 구성 사실만 제공한다. 중신 중복·인접 충은 structure, 성립·영향 미확정은 scope로 설명한다. 후보 오행의 합화 미확정은 notice로 구분한다.
- 자합은 조합 존재와 주변 충·형만 설명한다. 성립·불성립을 판정하지 않으며 없는 주변 글자·관계 ID를 만들지 않는다.
- 오행상 지지→천간 극 탐지는 학파의 직접 작용 허용이나 실제 손상을 뜻하지 않는다.

응답 모델은 십성·소속·근거 존재·최종 상태·배지·설명 참조 범위·근거 인덱스를 검사한다.
설명은 자기 관계와 그 근거가 가리키는 글자/관계만 참조할 수 있다.
호환용 직접 모델 자료는 새 목록의 빈 기본값과 presentation=null을 허용하지만,
실제 API 조립기는 모든 관계의 표시 정보를 채운다.

## 실제 응답 사례

[JSON 사례](relation_presentation_examples.json)는 양력 1995-05-12 14:30 남성의
원국과 2007년 세운 조회에서 생성한 표시 필드 발췌다. 전체 응답이 아니므로 관계 본문과
evidence는 API 원본에서 함께 조회한다. 카드 수나 중요도를 판정한 자료가 아니다.

판정 범위와 11개 사유의 근거 요구사항은 [감사 문서](relation_activation_audit.md)를 따른다.
