# 문서 안내와 현행 개발 기준

갱신일: 2026-11-13. 현행 API 계약을 먼저 읽고, 과거 설계의 다음 작업을 현재 개발 지시로 사용하지 않는다.

현재 사용자는 프론트엔드 연동을 보류하고 루트 API 개선에 집중하도록 요청했다.
[루트 조회 인덱스와 측정](root_api_lookup_performance.md)에 첫 개선과 검증을 기록했다.
이후 [요약·상세 정합성 계약](root_summary_contract.md)에 따라 반복 관계의 누락·중복을 정리하고
통근 요약 이름과 매트릭스의 중복 설명 목록을 정리했다.

최근 작업과 재개 지점은 [2026-11-13 작업 재개 기록](current_work_handoff.md)을 참조한다.
재개 후 확인한 조건부 판정의 세 가지 의미와 후속 정리안은
[`conditional` 의미 검토](conditional_state_review.md)에 정리했다.
이후 사용자 결정으로 자합은 조합·주변 관계의 사실 조회로 정리했다.
자합에 대해서는 [자료 대조와 현행 계약](self_combination_source_review.md)을 우선한다.
이후 육합·삼합도 전체 존재 정보로 통일했다.
[변경 계약과 수치 영향](hap_presence_migration.md)을 함께 참조한다.
이후 관계 총계·개별 점수와 빈주의 점수·취용 판정을 제거했다.
[현행 관계 점수 제거 계약](relation_score_retirement.md)을 우선한다.
[기존 점수 총계 검토](relation_score_audit.md)는 제거 결정의 근거 기록이다.

최근에는 신살의 년지 기준 누락을 수정하고 탐지 기준을 명시했다.
오행 개수 목록의 이름과 설명을 정리했으며 원국 상세·관찰 근거의 응답 타입을 구체화했다.
[루트 표시·신살·타입 계약](root_display_contract.md)을 함께 읽는다.

이후 사용자 요청으로 辰戌丑未의 저장 오행·고 역할만 추가했다.
[고 기본 분류 계약](storehouse_contract.md)을 따르며 크기·개고는 후속 범위다.

이후 루트 기반 관계·글자·운 조회의 전달과 검증을 점검했다.
[조회 API 정합성 감사](api_projection_audit.md)에 정상 응답 보존과 검증 보강을 기록했다.

이후 별도 해설 DB의 빈 기본 카탈로그와 검색 기능을 추가했다.
[해설 DB 계약](interpretation_database_contract.md)에 초기화·565개 패턴·조건 검색·작성본 보존을 정리했다.
작성용 JSON 내보내기와 전체 565개·검토용 천간극 20개 파일도 같은 문서에서 안내한다.
API 연결과 외부 LLM 해설 작성은 아직 포함하지 않는다.

## 현행 API 계약

| 문서 | 기준 |
| --- | --- |
| [조회 API 정합성](api_projection_audit.md) | 원국 자료 전달·고 분류 타입·통근 미평가·운 메타데이터 검증 |
| [고 기본 분류](storehouse_contract.md) | 원국 `branch.storehouse`, 저장 오행·일간 기준 역할 |
| [루트 요약·상세 정합성](root_summary_contract.md) | 위치별 관계 요약·`rooting_summary`·매트릭스 `3.0.0` |
| [루트 조회 성능](root_api_lookup_performance.md) | 달력 인덱스·기존 DB 적용·실제 응답 보존·측정 도구 |
| [루트 표시·신살·타입](root_display_contract.md) | 신살 기준·상징 설명·오행 목록·상세 응답 타입 |
| [출생 입력·달력 조회](birth_input_validation.md) | 날짜·시간 검증, 음력 평달·윤달 선택 |
| [대운 선택](daewoon_selection_contract.md) | 현재 대운·선택 세운의 공통 연도 경계 |
| [오류 응답](api_errors.md) | HTTP 상태·오류 코드·필드·허용 범위 |
| [통근과 관계 영향 분리](root_relation_separation.md) | 동주 허실 v4, 관계 영향 미평가 |
| [원국 관계 조회](character_relation_index_contract.md) | `/relation-index`, 현행 `1.7-draft` |
| [글자별 통합 조회](character_details_contract.md) | `/character-details`, 소속·글자·중앙 관계 |
| [글자별 원자료 관계](raw_character_relations_contract.md) | `stem.relations`·`branch.relations` 배열·상태·후보·수치 의미 |
| [관계 점수 제거](relation_score_retirement.md) | 점수 제거 당시 매트릭스 `2.0.0`, 빈주 `4.0.0`; 매트릭스 현행은 위 요약 계약 우선 |
| [상태·사유·근거 감사](relation_activation_audit.md) | 판정 범위·근거 연결·미평가 항목 |
| [관계별 자연어 표시](relation_presentation_contract.md) | 근거·십성이 연결된 제목·본문·사유·평가 범위 |
| [운 선택 조회](cycle_analysis_contract.md) | `/cycle-analysis`, 대운 또는 세운 선택 |
| [운 관계 탐지](cycle_relation_detection.md) | 소속 간 쌍별·다자 후보와 투간 |
| [운 관계 감사](cycle_relation_audit.md) | 누락·중복·조회 일관성·재조립 검증 |

`/analysis-summary`는 2026-11-13 제거했다. 관계·설명은 `/character-details`와
`/cycle-analysis`에서 조회한다. 전용 카드·순서·비교 기능은 이전하지 않았으며,
기본 `/` 응답의 `analysis.summary`는 유지한다.

## 현재 우선 원칙

- 통근은 동주만 판정하고 타주 지원은 분리한다. 현행 API에서 합·충·형·파·천으로 통근 점수를 자동 제외하거나 변허로 바꾸지 않는다.
- 관계 탐지, 성립 상태, 실제 세력·통근 영향을 구분한다. 운 후보를 원국의 인접·거리 규칙으로 자동 성립시키지 않는다.
- 대운·세운은 선택 시 조회한다. 원국 기본 판정을 덮어쓰지 않는다.
- 미평가는 `null`·명시적 상태로 제공한다. 기존 잠정 세력 지표를 완성된 최종 세력이나 검증된 손상량으로 해석하지 않는다.
- 수치 모델·피해량·계수 추정·작공/LLM 출력 확장은 현재 개발 계획에 포함하지 않는다. 재개하려면 명시적 작업 범위와 근거 검토가 먼저다.

원국 상세·매트릭스 관찰 근거·빈주 영역의 타입 보강은 적용했다. 보존된 실험 모델의 유연한 근거 구조는 이번 범위 밖이다. 루트 조회 성능과 요약 정합성 보강을 적용했고 프론트엔드 연동은 사용자 요청으로 보류 중이다. 이후 작업 범위는 새 요청에 따라 정한다.

## 현행 코드 이해를 위한 참고 자료

[관계 규칙표](mangpa_relation_rulebook.md), [원국 지지 v2](branch_dynamics_v2.md), [잠정 세력의 의미](branch_strength_accounting.md), [성립 판정 기록](branch_relation_activation_review.md)은 기존 출력과 구현을 이해하기 위해 유지한다.

[최종 세력 출력 차단](branch_post_effect_completeness.md), [출처 경로](branch_influence_path_contract.md), [그룹 출처](branch_group_source_ledger.md), [주변 보정 감사](branch_ambient_replay_audit.md)는 보존된 내부 모델·회귀 검사 참고다. 수치화 재개 지침이 아니다.

`same_pillar_*`, `root_strength_rule_review.md`, `transmission_rooting_alignment_audit.md`, `interaction_detection_implementation_audit.md`, `eight_character_relation_lookup_example.md`, `branch_relation_candidate_audit.md`는 특정 시점의 검토·이행 기록이다. 버전·다음 작업·과거 테스트 수는 그 시점의 기록이며 위 현행 계약을 우선한다.

## 중단 연구 보관소

[세력 수치 연구 보관 목록](archive/strength-research/README.md)에 이전 계획·축미충/자오충 사례·설계 JSON을 모았다. 과거 사용자 결정과 폐기 이유를 보존하지만 현행 개발 방향으로 적용하지 않는다. 현재 사용되는 코드·테스트는 제거하지 않았다.
