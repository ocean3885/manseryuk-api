# 관계 점수 제거와 빈주 사실 조회 계약

2026-11-13. 사용자는 관계 총계의 필요성을 재검토한 뒤 추천 방향으로 정리하도록 요청했다.
기존 프론트엔드 호환 없이 응답을 정리하며 새로운 API·대체 점수·이전 필드 별칭은 만들지 않는다.

## 결정

관계 존재·참여 위치·십성·관찰 근거를 직접 제공한다.
관계 종류별 임의 가중치를 합산해 안정성·긴장·전체 우세·취용 방향을 단정하는 경로를 제거했다.
검토 근거는 [제거 전 감사](relation_score_audit.md)와 그 문서의 역사적 JSON이다.

| 범위 | 현행 버전 |
| --- | --- |
| `advanced_analysis.interactions` | `2.0.0` |
| `advanced_analysis.bin_zhu_dynamics` | `4.0.0` |
| 지지 실행 규칙 | `2.22.0` |

## 삭제한 필드와 종속 계산

아래 경로는 기본 `/` 응답의 `advanced_analysis`를 기준으로 한다.

| 경로 | 삭제한 내용 |
| --- | --- |
| `interactions` | `tension_score`, `harmony_score`, `climate`와 계산식·임계값 |
| `interactions.matrix[]` | `score`, `score_contribution`, `score_covered_by`와 중복 점수 차감 |
| `bin_zhu_dynamics` | `pairwise_scores`, `group_cohesion_score`, `control_flow` |
| `bin_zhu_dynamics.guest_host_links[]` | `target_guest`, `source_host`, `mechanism`, `flow_direction`, `weight` |
| `bin_zhu_dynamics.group_connections[]` | `cohesion_score`, `included_in_score` |
| `bin_zhu_dynamics.guest_structure` / `host_structure` | `dominant_forces`, `dominant_means` 등 십성 분류를 우세·수단으로 해석하던 요약 |
| `branch_dynamics.groups[].formation_evidence[].overlapping_pairs[]` | `covered_in_harmony_score` |
| `ai_consultation_prompts` | 기후·빈주 점수·우세·취용 방향·점수 제외 안내와 종속 문구 |

스키마와 OpenAPI에서도 제거했다. `0`이나 `null`인 호환 필드로 남기지 않는다.
허실의 `related_interactions`처럼 매트릭스 원본을 전달하는 곳에서도 관계 점수는 사라진다.
빈주의 `ai_prompt_bullets` 내부 생성 경로도 제거했다.

점수와 무관하게 합·십성만으로 취용·압박 방향을 단정하던 메커니즘도 함께 제거했다.
빈주에 남는 십성은 참여 글자의 정보다. 자동 취용·직업·성과 판단의 입력으로 확정하지 않는다.

## 현재 제공하는 자료

### 관계 매트릭스

`interactions`는 `rule_version`, `summary_list`, `matrix`를 반환한다.
각 관계의 ID·유형·참여 위치·실제 조합·원본 상태·관찰 근거·후보 오행·거리 가중치는 유지한다.
육합·삼합의 상태는 모두 `detected`이며 충·중신 중복의 존재를 별도 근거로 보여준다.

다자 관계에 포함되는 육합·반합 등도 독립적인 관계 사실로 남긴다.
집계 대상 여부에 따라 관계를 숨기거나 0점을 불성립으로 읽을 여지가 없도록 했다.
관계가 없으면 빈 목록만 반환하며 기후 유형을 임의 생성하지 않는다.

그룹 중첩은 `overlapping_pairs: [{relation_id, participants}]`로 제공한다.
해당 실제 세 위치 조합 안에 들어가는 **모든 매트릭스 지지 쌍 관계**가 대상이다.
이전 조화 집계 유형인 육합·반합으로 제한하지 않는다. 이는 위치 연결이며 수치 차감이 아니다.

### 빈·주 관계

`interaction_scope: cross_domain_relations`다.
빈은 년·월, 주는 일·시로 분류하고 실제로 두 영역을 잇는 쌍을 `guest_host_links`에 반환한다.

- 쌍: `relation_id`, 원본 `category`·`type`·`activation_status`, `participants`,
  `guest`, `host`, `distance`, `is_adjacent`, 사실 설명 `detail`.
- 각 `guest`·`host`: `pillar`, `char`, 일간 기준 `ten_god`, `display_name`.
  일간 자신은 `일간`으로 표시한다.
- 다자: 삼합·방합·삼형의 `relation_id`, `type`, `participants`, `formations`,
  `guest_participants`, `host_participants`, 원본 상태와 구성 설명.
- 영역: `guest_structure`·`host_structure`에 범위와 위치별 글자·십성 표시 정보.

파·공합·암합과 `candidate_only` 관계도 사실 목록에 포함한다.
빈 내부·주 내부의 쌍은 이 조회 범위 밖이며 전체 매트릭스에는 남는다.
`excluded_interactions`는 위치나 분류가 유효하지 않은 입력만 기록한다.
사유 코드는 `missing_group_participants`, `invalid_endpoint`, `invalid_category`다.
`all`만 있고 실제 참여 위치가 없는 다자 입력에서 위치를 추측하지 않는다.

[실제 규칙으로 생성한 응답 발췌](relation_score_retirement_examples.json)를 참고한다.
예시는 `亥卯未亥`·`巳午未寅`·`子子卯卯`의 합성 원국이며 달력 날짜를 주장하지 않는다.

## 유지한 수치와 계약

동주 통근·타주 지원, 오행 글자 수·별도 잠정 분포, 지지 배경과 쌍별 잠정 `force`는 유지했다.
원자료의 거리 가중치·기본/구조 계수·`potential_index`도 별도 용도이므로 유지한다.
이 수치들을 최종 세력·실제 피해·합화 판정으로 승격하지 않는다.
실제 영향 미평가·실제 적용량 `null`, 실험 v3와 기존 회귀 검사를 유지했다.

`/character-details`·`/relation-index`·`/cycle-analysis`에 새로운 API나 점수 대체 구조를 추가하지 않았다.
이번 삭제 대상은 기본 응답의 관계 총계와 종속 해석이다.

## 검증

- `.venv312/bin/python -m unittest discover -s tests`: **265개 통과**.
- HTTP 기본 응답·글자 조회·운 조회와 OpenAPI에서 삭제 필드가 재도입되지 않는지 확인했다.
- 반복 글자, 합·충 공존, 삼형, 파·공합·암합, 역순 참여 위치의 글자·십성 보존을 검사했다.
- 점수 제거 직전 12개 원국과 비교해 글자·십성·원자료·동주 통근 판정/수치,
  지지 배경·쌍별 잠정량·그룹 수치·중앙 글자 조회 결과가 모두 동일했다.
  원본 관계를 복사한 근거에서 삭제된 점수·바뀐 요약 표현은 비교에서 제외했다.
  중첩 메타데이터와 규칙 버전도 의도된 변경으로 구분했다.
- 비교 지지: `子丑寅辰`, `午子丑寅`, `子午丑寅`, `亥卯未亥`, `亥卯卯未`, `巳亥卯未`,
  `亥子丑子`, `巳午未寅`, `丑戌未丑`, `子子子子`, `午午午午`, `戌未辰卯`.
  천간은 모두 `甲甲甲甲`으로 고정했다.

프론트엔드는 삭제한 점수·기후·벡터 필드 참조를 제거하고 관계 목록·상태·참여 글자·십성을 표시한다.
별도 프론트엔드 저장소의 실행 검증은 이번 백엔드 작업 범위에 포함되지 않는다.
커밋·푸시·환경 게시는 별도로 요청받기 전까지 수행하지 않는다.
