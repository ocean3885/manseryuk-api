# 세력 수치 계산 연구 보관소

상태: **중단 연구·과거 설계**. [현행 개발 기준](../../README.md)이 우선한다. 이 폴더의 “다음 작업”, “최신 방향”, “구현 순서”, 계수·손상률 제안은 현재 작업 지시가 아니다.

| 자료 | 보관 이유 |
| --- | --- |
| [과거 인수인계](branch_dynamics_handoff.md) | 변경 과정·사용자 결정·중단 이유 보존 |
| [v3 계획](branch_dynamics_v3_plan.md) | 이전 개발 단계와 폐기된 산식 기록 |
| [목표 계약](branch_dynamics_target_contract.md), [검증표](branch_dynamics_acceptance_matrix.md), [엔진 설계](branch_relation_engine_design.md) | 당시 목표이며 현행 공개 API 계약이 아님 |
| [자오충 설계](ziwu_clash_effect_design.md) | 잠정 손실 산식과 미확정 계수 |
| [축미충 사례](chouwei_clash_analysis.md), [전문가 양식](chouwei_expert_review_sheet.md) | 해석·반례·근거 출처 |
| [축미충 계상 검토](chouwei_a_d_accounting_review.md), [출처 경로](chouwei_a_d_source_paths.md) | 중복 계상과 미해결 경로 검토 |
| [최종 집계 추적 설계](branch_post_effect_trace_contract.md) | 미구현 집계의 과거 제안 |
| [v3 설계 JSON](branch_dynamics_v3.json) | 테스트가 직접 읽는 보관 설계 샘플. 현행 API 응답이 아님 |
| [허실 이전 README 설명](xu_shi_legacy_reference.md) | v1 회귀와 v2~v3 자동 제외·변허 설명. 현행 v4와 구분 |

파일 이동에 맞춰 상대 링크와 테스트의 설계 JSON 경로를 갱신했다. 테스트의 `tests/fixtures/branch_dynamics_v3.json`은 별도 회귀 자료로 유지한다. 관련 모듈은 일부 현행 관계 조회가 사용하므로 보관 문서 이동을 근거로 삭제하지 않는다.
