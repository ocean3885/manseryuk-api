# 문서 안내와 현행 개발 기준

갱신일: 2026-11-04. 현행 API 계약을 먼저 읽고, 과거 설계의 다음 작업을 현재 개발 지시로 사용하지 않는다.

## 현행 API 계약

| 문서 | 기준 |
| --- | --- |
| [출생 입력·달력 조회](birth_input_validation.md) | 날짜·시간 검증, 음력 평달·윤달 선택 |
| [대운 선택](daewoon_selection_contract.md) | 현재 대운·선택 세운의 공통 연도 경계 |
| [오류 응답](api_errors.md) | HTTP 상태·오류 코드·필드·허용 범위 |
| [통근과 관계 영향 분리](root_relation_separation.md) | 동주 허실 v4, 관계 영향 미평가 |
| [원국 관계 조회](character_relation_index_contract.md) | `/relation-index`, 현행 `1.7-draft` |
| [글자별 통합 조회](character_details_contract.md) | `/character-details`, 소속·글자·중앙 관계 |
| [운 선택 조회](cycle_analysis_contract.md) | `/cycle-analysis`, 대운 또는 세운 선택 |
| [운 관계 탐지](cycle_relation_detection.md) | 소속 간 쌍별·다자 후보와 투간 |
| [운 관계 감사](cycle_relation_audit.md) | 누락·중복·조회 일관성·재조립 검증 |
| [선택 비교·구조 요약](analysis_summary_contract.md) | `/analysis-summary`, 추가·유지 관계와 근거 연결 문장 |

## 현재 우선 원칙

- 통근은 동주만 판정하고 타주 지원은 분리한다. 현행 API에서 합·충·형·파·천으로 통근 점수를 자동 제외하거나 변허로 바꾸지 않는다.
- 관계 탐지, 성립 상태, 실제 세력·통근 영향을 구분한다. 운 후보를 원국의 인접·거리 규칙으로 자동 성립시키지 않는다.
- 대운·세운은 선택 시 조회한다. 원국 기본 판정을 덮어쓰지 않는다.
- 미평가는 `null`·명시적 상태로 제공한다. 기존 잠정 세력 지표를 완성된 최종 세력이나 검증된 손상량으로 해석하지 않는다.
- 수치 모델·피해량·계수 추정·작공/LLM 출력 확장은 현재 개발 계획에 포함하지 않는다. 재개하려면 명시적 작업 범위와 근거 검토가 먼저다.

다음 API 보강 후보는 응답 타입 구체화와 성능 측정이다. 이는 자동 실행 지시가 아니며 새 사용자 요청에 따라 범위를 정한다.

## 현행 코드 이해를 위한 참고 자료

[관계 규칙표](mangpa_relation_rulebook.md), [원국 지지 v2](branch_dynamics_v2.md), [잠정 세력의 의미](branch_strength_accounting.md), [성립 판정 기록](branch_relation_activation_review.md)은 기존 출력과 구현을 이해하기 위해 유지한다.

[최종 세력 출력 차단](branch_post_effect_completeness.md), [출처 경로](branch_influence_path_contract.md), [그룹 출처](branch_group_source_ledger.md), [주변 보정 감사](branch_ambient_replay_audit.md)는 보존된 내부 모델·회귀 검사 참고다. 수치화 재개 지침이 아니다.

`same_pillar_*`, `root_strength_rule_review.md`, `transmission_rooting_alignment_audit.md`, `interaction_detection_implementation_audit.md`, `eight_character_relation_lookup_example.md`, `branch_relation_candidate_audit.md`는 특정 시점의 검토·이행 기록이다. 버전·다음 작업·과거 테스트 수는 그 시점의 기록이며 위 현행 계약을 우선한다.

## 중단 연구 보관소

[세력 수치 연구 보관 목록](archive/strength-research/README.md)에 이전 계획·축미충/자오충 사례·설계 JSON을 모았다. 과거 사용자 결정과 폐기 이유를 보존하지만 현행 개발 방향으로 적용하지 않는다. 현재 사용되는 코드·테스트는 제거하지 않았다.
