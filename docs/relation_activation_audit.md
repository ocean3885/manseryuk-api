# 상태·사유·근거 연결 감사

기준: 2026-11-13, 실행 규칙 2.19.0, 내부 v3 3.9.0-draft, 동주 허실 4.0.0,
운 탐지 1.0.0-draft. 이전 작업의 근거·십성 확장을 복구하고 자연어 표현의 입력을 재검증했다.
이 문서는 현행 실행 범위를 설명하며 보류 규칙의 재개 지시가 아니다.

## 판정 범위

| 대상 | 현재 구현 | 미정·미평가 |
| --- | --- | --- |
| 원국 충·파·천·쌍별 지세형 | 등록된 쌍 존재 시 거리 무관 active | 일반 차단 규칙·실제 영향 |
| 육합 | 충 없음 active, 합 사이 인접 충 suppressed, 바깥 인접 충 conditional | 실제 합화·상세 발현 |
| 자형 | 인접 辰辰·午午·酉酉·亥亥 active, 격위 candidate_only | 독립 작용량 |
| 삼형 | 세 종류 지지가 있으면 active, 구성 쌍 상태 유지 | 복합 작용·독립 영향 |
| 삼합 | 기본 potential, 중신 중복 conditional, 중신/생지/성지 인접 충 suppressed | 합화·주도·경합 |
| 방합 | 구조 potential | 상세 성립·훼손·방향 |
| 반합 | 결손 구조·날개 충 후 잔여 반합 탐지, 완성 그룹 내부는 구조 전용 후보 | 독립 성립·실제 영향 |
| 공합·암합 | 지정 조합 candidate_only | 활성 조건·세부 영향 |
| 지지 생·극 | 오행 방향 potential, 같은 쌍 active 구조로 독립 적용 억제 | 실제 발현·적용량 |
| 천간 합·충·극 | 중앙 조회에서 detected | 종합 성립·억제 |
| 동주 오행·투간 | 오행 사실·지장간 정확 일치 detected | 실제 영향 |
| 자합 | 등록 조합, 丙戌·壬戌의 未형 필요·辰충 차단 | 기타 관계의 일반 개입 |
| 통근 | 동주 점수 양수면 실, 0이면 허투, 타주 지원 분리 | 관계에 의한 손상·소멸 |
| 운 관계 | 후보 또는 구조 사실 탐지 | 성립·경합·억제·통근 영향 |

active는 현행 프로젝트의 성립 조건 충족이며 실제 세력·길흉·손상을 확정하지 않는다.
detected와 candidate_only, potential도 각각 사실 탐지·후보·잠재 상태로 구분한다.

## 사유 13개와 필수 근거

| 코드 | 필수 근거 및 설명 범위 |
| --- | --- |
| intervening_adjacent_clash | 육합 사이의 충 위치와 충 ID |
| external_adjacent_clash | 육합 바깥의 충 위치와 충 ID; 복수 충 보존 |
| duplicate_middle | 모든 중신 위치와 조합; 없는 충을 만들지 않음 |
| adjacent_middle_clash | 중신·충 글자·충 ID |
| adjacent_birth_clash | 생지·충 글자·충 ID |
| adjacent_tomb_clash | 성지·충 글자·충 ID |
| active_pair_structure_overrides_element | 같은 쌍의 active 구조 전체를 overriding_relation_ids로 연결 |
| combination_candidate_not_transformation | 실제 합화 미확정 안내. active 육합에도 나오는 주의 정보 |
| required_punishment_missing | required_condition, condition_met=false. 없는 관계 ID를 만들지 않음 |
| blocked_by_chen_chung | blocking_chung의 위치·충 ID, 충족한 未형도 별도 보존 |
| adjacent_self_punishment | 인접한 두 위치와 성립 규칙 |
| nonadjacent_self_punishment_candidate | 격위 위치와 후보 유지 이유 |
| cycle_presence_only_activation_and_impact_not_evaluated | 참여자·등록 표·탐지 버전, 운 성립·영향 미평가 |

완성 삼합 내부 반합은 `included_in_complete_group` 구조 전용 판정과 포함 그룹 ID를
추가 근거로 제공한다. 잔여 반합의 `fallback_from`은 원래 삼합·원인 충에 연결한다.
원본 상태는 보존하며 `effective_activation_status`로 최종 어댑터 상태를 구분한다.

## 근거 보존 계약

`relations[*].participant_details`는 원래 participants 순서의 글자 ID·소속·위치·글자·
일간 기준 ten_god·display_name을 제공한다. 지지는 기존 대표 십성이며 지장간별 십성과 다르다.
`status_reasons`는 대표 사유와 원본의 전체 사유를 중복 없이 보존한다.
`element_relation`은 동주 생·극·동일 오행의 구체 유형이다.

`evidence[]`는 source, details, characters, related_relation_ids로 구성한다.
details의 원본 좌표는 그대로 유지하고 관련 글자에는 공통 ID와 십성을 붙인다.
역사적인 force·damage·power 수치는 판정 근거에 추가하지 않는다.
기존 글자별 분석 records의 strength나 통근 점수는 원본 수치이며 실제 손상량이 아니다.

통근의 reason·transition_reasons 및 evidence(root_info, external_support_info)는
기존 허실 설명과 근거를 보존한다. remaining_score는 호환용 원점수이며,
root_impact_status=not_evaluated는 손상이 없다는 판정이 아니다.

## 검증과 후속 경계

`test_relation_presentation.py`는 13개 사유의 생산 경로, 위치 순열, 인접/격위,
복수 충, 자합의 필요 형/차단 충, 구조 전용/잔여 반합을 점검한다.
모든 지지 쌍을 인접·격위로 배치한 288개 및 천간 쌍 100개의 고정 간지 사례에서
표시 근거 누락 여부를 검사한다. 고정 간지는 규칙 자료이며 실제 출생일을 주장하지 않는다.
기존 관계 조회와 비교해 ID·수·상태·대표 사유·규칙이 유지되는지 확인한다.
실제 달력 DB 및 HTTP의 원국/대운/세운/요약 그래프 보존도 검사한다.

테스트 통과는 명리적 타당성 전체의 증명이 아니다. 합화·종합 경합·운 관계 성립은
규칙 결정과 검증 사례가 먼저 필요하다. 최종 세력·피해량·작공/LLM 연구는 재개하지 않는다.
