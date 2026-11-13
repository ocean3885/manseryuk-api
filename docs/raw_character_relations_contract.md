# 글자별 원자료 관계 계약

2026-11-13. 기존 프론트엔드 호환 제약 없이 탐지 함수의 반환 계약을 정리했다.
새 API나 호환용 변환 계층은 추가하지 않는다.
원국 상세 원자료의 네 기둥·관계별 타입과 매트릭스 관찰 근거는
[`schemas/natal_analysis.py`](../schemas/natal_analysis.py)에 정의했다.
타입 검증은 기존 키와 빈 배열·`null`을 보존한다.
[루트 표시·타입 정리](root_display_contract.md)를 함께 참조한다.

## 적용 경로와 자료형

- `/`: `analysis.details[year|month|day|hour].stem.relations` 및 `branch.relations`
- `/character-details`, `/cycle-analysis`: 원국 글자의 `characters[ID].analysis.relations`

천간 `combinations`, `conflict`는 항상 배열이다. `restrain`은 항상
`{"restrain_to": [], "restrain_me": []}` 형태의 사전이다.
지지의 모든 관계 항목은 항상 배열이며, 관계가 없으면 `[]`다.

`six_haps`는 위치별 육합 전체 배열이다. 첫 상대만 담던 사전과 별도
`six_haps_all` 별칭은 제거했다. `子丑丑子`의 년지에서는 월지·일지와의 육합을
모두 반환한다. 같은 글자도 위치가 다르면 별개 관계다.

## 공통 판정 정보

관계마다 `activation_status`, `status_reasons` 배열,
`impact_status: "not_evaluated"`를 제공한다.

| 관계 | 상태 |
| --- | --- |
| 천간 합·충·극 | `detected`: 해당 글자 관계 탐지 |
| 지지 충·천·파·지세형 | `active`: 존재 규칙으로 성립 |
| 자형 | 인접하면 `active`, 비인접이면 `candidate_only` |
| 육합 | 충의 유무·위치와 무관하게 조합 존재 `detected` |
| 삼합 | 중신 중복·인접 충과 무관하게 구성 존재 `detected` |
| 반합·방합 | `potential` |
| 공합·지장간 암합 | `candidate_only` |
| 삼형 | 세 글자 존재 시 `active` |

`active`는 해당 성립 규칙의 충족을 뜻한다. 실제 피해·세력 변화·통근 손상이나
합화 확정은 평가하지 않는다. 비인접 자형에도 잠정 수치가 남을 수 있으므로
0이 아닌 숫자로 성립·영향을 역산하지 않는다.

존재·인접 규칙이 있는 관계는 `activation_rule_id`도 제공한다. 육합은 성립을
판정하지 않으므로 해당 ID가 항상 `null`이다. 비인접 자형도 `null`이다. 사유가 없는 관계의
`status_reasons`는 빈 배열이다. 육합·삼합의 `condition_evidence`는 아래의
읽기 쉬운 근거 표현을 함께 제공한다.
매트릭스는 탐지 함수가 산출한 상태·사유를 사용하며, 원국 관계 조립 시
쌍별 원자료와 매트릭스의 상태·사유·후보 오행 불일치를 거부한다.

### 읽기 쉬운 조건 근거

`condition_evidence.summary`는 관찰한 조건과 근거를 설명한다. 판정 문구를
덧붙이지 않으며, 판정 상태는 `activation_status`와 상태 배지로 표시한다.
육합·삼합 원자료와 중앙 매트릭스에서 제공하고, `/character-details`와
`/cycle-analysis`의 원국 글자 분석 및 중앙 관계 `evidence[*].details`에도 전달한다.

충 항목은 기존 위치 식별자에 다음 정보를 함께 제공한다.

| 필드 | 의미 |
| --- | --- |
| `affected` | 충 조건에 해당하는 육합 구성원 또는 삼합 중신·생지·성지 |
| `cause` | 해당 구성원과 충하는 외부 지지 |
| `description` | 두 위치·글자·십성과 충의 역할을 표시하는 문장 |
| `location_label` | 육합의 `between` / `outside`를 설명하는 한글 표기 |

`affected`, `cause`는 `index`, `pillar`, `char`, `ten_god`, `display_name`을 갖는다.
십성은 원국 일간 기준이며 지지에는 일간 본인 표기를 사용하지 않는다.
`affected`와 `cause`는 판정 조건 안의 역할이며 실제 작용의 일방향성·피해를 뜻하지 않는다.
같은 글자가 반복되어도 `pillar`와 `index`로 서로 다른 위치를 구분한다.

삼합은 `middle_members`에 중신의 위치·글자·십성을 담는다. `summary`는 중신
중복, 중신 충, 생지 충, 성지 충을 구분한다. 조건이 없으면 인접 충·중신 중복이
확인되지 않았음을 설명한다.
합화·통근 손상·실제 세력 변화는 설명에서 추론하지 않는다.

삼합 날개 충으로 남은 반합의 원자료 `fallback_from`에도 `affected`, `cause`,
`description`을 제공한다. 매트릭스에서는 이를 `condition_evidence.fallback_from`과
`condition_evidence.summary`로 전달한다. 삼합의 존재·날개의 충·반합 후보를 함께 보존한다.
기존 인덱스·위치 코드는 내부 규칙 연결과 검증에 사용하므로 유지한다.

화면에서는 우선 `summary`를 표시하고, 상세 펼침이나 글자 강조에는
`affected`·`cause`·`middle_members`를 사용한다. 전체 관계 화면의 제목·본문은
기존 중앙 `presentation`을 사용하며 같은 근거 설명을 중복 표시할 필요는 없다.

## 후보 오행과 수치

육합·삼합 전체는 성립을 판단하지 않는 사실 조회다. `status_reasons`의 중신 중복·충
코드는 구성 관찰 정보이며 조건부·억제 판정이 아니다. 삼합은 `middle_count`도 제공한다.
자동 육합 성립에 따른 생·극 억제는 제거했다.
[존재 정보 계약과 당시 계산 영향](hap_presence_migration.md)을 따른다.
이후 매트릭스의 개별 관계 점수·총계와 빈주 점수는 [별도 제거](relation_score_retirement.md)했다.
원자료의 거리 가중치·기본/구조 계수·`potential_index`와 실제 적용량 `null`은 유지한다.
통근·오행 등 다른 분석의 수치를 일괄 폐기한 것은 아니다.

### 자합은 조합과 주변 관계의 사실만 제공

2026-11-13 사용자 결정에 따라 `analysis.details[기둥].jahab`과 중앙
`self_combine`은 자합 성립을 자동 판단하지 않는다. 등록된 9개 조합을 유지하고
모두 `detected`로 제공한다. 未형·辰충 등 해당 지지의 충·형은
`related_branch_relations` 배열로 따로 기록한다.
각 항목에는 `type`, `with`, `with_index`, `with_ten_star`, `distance`,
`is_adjacent`가 있다. 반복 글자도 위치별로 보존하고 주변 관계가 없으면 `[]`다.

`active`, `is_conditional`, `condition_met`, `required_condition`, `inactive_reason`,
`blocking_chung`, `chung_impact`는 제거했다. 자합의 실제 영향은
`impact_status=not_evaluated`이며 성립·불성립 판단은 별도다.
원자료의 `chars`, `my_index`, `exists`, `hidden_stem`, `candidate_element`는
조합 식별에 사용한다. 중앙 관계 ID와 지장간 후보는 유지한다.
주변 충·형 자체의 기존 상태·수치는 바꾸지 않는다.
이론 자료와의 대조는 [자합 자료 검토](self_combination_source_review.md)를 따른다.

### 합의 오행과 잠정 수치

천간합의 `combined_element`, 육합·삼합·반합·공합·방합의 `element`는
`candidate_element`로 바꿨다. 동주 `jahab.combined_element`도
`jahab.candidate_element`로 바꿨다. 합화가 확정됐다는 뜻이 아니다.
지장간 암합 내부의 `hidden_stem_pairs[*].combined_element_candidate`는
지장간 조합별 후보 오행이므로 그대로 유지한다.

관계 원자료에서 의미가 혼재하던 `strength`는 제거했다.

| 필드 | 의미·적용 |
| --- | --- |
| `distance` | 쌍의 위치 인덱스 차이. 방합에서는 가장 짧은 성립 조합의 범위 |
| `distance_weight` | 천간 합·충·극, 지지 충·천·파·형, 육합의 거리 가중치: 1 / 0.7 / 0.5 |
| `base_coefficient` | 천간 극·형·방합의 기존 규칙 계수 |
| `structure_coefficient` | 반합·삼합의 기존 구조 계수 |
| `proximity_coefficient` | 육합의 근합 1·원합 0.5, 방합의 인접 1·비인접 0.6 |
| `potential_index` | 천간 극·형의 거리 가중치 × 기본 계수, 방합의 인접 계수 × 기본 계수 |

천간 극의 `distance_strength`, `restrain_base_strength`도 각각
`distance_weight`, `base_coefficient`로 바꿨다. 삼합의 `candidate_strength`는
`structure_coefficient`로 통일했다. 공합·암합의 `strength: null`은 제거했다.
자합의 기존 `chung_impact`는 제거하고 위 주변 관계 사실 배열로 대체했다.
`potential_index`는 소수 넷째 자리로 반올림한다.

이 값들은 검증된 강도·확률·손상률이나 서로 다른 관계 간 순위 점수가 아니다.
기존 계수의 의미를 구분한 것이며 계수 추정이나 세력 모델 확장은 하지 않았다.
중앙 매트릭스의 `weight`·`score`와 내부 세력 모델 수치 계약은 별개다.

## 방합의 중복 글자와 인접성

`formation_indices`의 실제 세 자리 조합마다 범위를 계산해
`formation_distances`에 같은 순서로 제공한다. 하나라도 범위 2이면
`is_adjacent=true`다. 참여 위치 전체의 합집합 범위로 판정하지 않는다.

- `寅卯辰寅`: 조합 `[0,1,2]`, `[1,2,3]`, 범위 `[2,2]`, 거리 2, 인접, 잠정 지표 1.5.
- `寅子卯辰`: 조합 `[0,2,3]`, 범위 `[3]`, 거리 3, 비인접, 잠정 지표 0.9.

매트릭스 다자 관계의 `is_adjacent`도 탐지 함수의 판정을 사용한다.
개별 조합은 `formations`로 확인한다.

## 조회 범위와 검증

이 자료는 기존 등록 관계만 담는다. 지지 오행 생·극·동일 지지 관계까지
추가로 복제하지 않는다. 투간은 `branch.transmitted`, 동주 자합은 기둥의
`jahab`에 있다. 전체 관계의 ID·참여자·설명은 중앙 `relations`로 조회한다.

회귀 검사는 지지 144쌍의 세 상대 위치, 천간 100쌍, 중복·억제 다자 관계,
방합 실제 조합, 비인접 자형, 원자료 변조 거부와 세 HTTP 경로의 자료 보존을
확인한다. 중앙 자연어·십성·근거와 기존 통근·운 계산 회귀 검사도 함께 실행한다.
