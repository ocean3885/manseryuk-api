# 동주 통근과 관계 영향의 분리

2026-11-04 사용자 결정에 따른 현행 계약. 동주 허실 규칙 `4.0.0`, 관계 조회 `1.7-draft`.

## 판정과 기록

- 동주 `ROOT_STRENGTH > 0`은 실, 0은 허투다. 강도 계수와 타주 지원 계산은 유지한다.
- `xu_shi_dynamics.pillars[기둥].related_interactions`는 그 기둥의 **지지**가 참여하는 매트릭스 관계 원본을 보존한다. 합·충·형·파·천뿐 아니라 현재 생산되는 다른 지지 관계도 포함한다. 후보·조건부·억제 상태, 관계 ID, 상대 위치, 다자 참여 위치와 원본 근거를 버리지 않는다. 무근 기둥에도 기록한다.
- 천간 관계는 기존 중앙 관계 조회에서 계속 제공한다. 이 필드는 천간 관계까지 새로 탐지하는 기능이 아니다.
- `root_impact_status: not_evaluated`, `root_impact_score: null`은 통근 영향 규칙을 아직 적용하지 않았다는 의미다. 영향 없음이나 손상량 0의 판정이 아니다.
- 관련 관계가 있어도 통근 점수를 제외하거나 변허로 전환하지 않는다. `current_status == original_status`, `is_transformed=false`다.

## 기존 필드의 해석

호환 필드 `effective_score`와 조회의 `remaining_score`는 현행에서 원점수를 그대로 제공한다. 관계 적용 후 잔존량이 검증됐다는 뜻이 아니다. 영향 해석에는 반드시 `root_impact_status`를 함께 확인한다.

`root_evidence`는 동주 통근 근거다. 기존 손상용 `interactions`는 비우고 `is_affected=false`로 둔다. 관계는 `related_interactions`로 이동한다. `excluded_root_pillars`, `affected_root_branch_ids`, `impact_groups`는 비어 있으며 이는 영향 없음의 확정값이 아니다. 조회의 관련 관계는 같은 기둥 지지 노드의 `relation_ids`와 중앙 `relations`를 통해 확인한다.

현재 요약과 AI 프롬프트는 관계에 의한 통근 약화·소멸을 미평가라고 설명한다. 지지 세력 산식과 관계 자체의 성립 판정은 바꾸지 않는다.

## 이전 규칙과 검증

명시적 `all_four_branches_weighted` v1은 기존 회귀 비교용이며 자동 제외·변허 동작을 유지한다. 이 경우 `root_impact_status=legacy_evaluated`다. 현행 API의 동주 v4와 섞지 않는다.

테스트는 활성 충·천·파, 후보 형, 조건부 합, 억제 반합, 다자 관계 보존, 무근 위치의 관계 기록, 원점수 유지와 직렬화를 확인한다. 기존 v1 회귀도 유지한다.

다음 단계는 관계 유형·상태별 통근 영향 조건을 근거 사례와 함께 정의하는 것이다. 그전까지 관련 관계의 존재를 통근 소멸의 근거로 사용하지 않는다.
