# 지지 작용 v3 단계별 개발 계획

## 기준과 목표

[사용자 목표 출력 트리](./branch_dynamics_v3.json)를 **최신 목표 계약**으로 삼는다. 이 파일은 주석이 들어간 JSONC 형식의 설계 샘플이며, 현재 API 응답은 아니다. [이전 출력 초안](./branch_dynamics_target_contract.md)과 충돌하는 경우 v3를 우선 검토한다. 예시의 `null`, 빈 배열, 관계 ID와 가상 값은 확정된 계산 결과가 아니라 구현할 상태와 자료형을 설명한다.

v3의 범위는 `meta`·`chart_context`·`stem_dynamics`·`branch_dynamics`·`interaction_resolution`·`work_dynamics`·`llm_interpretation_payload`다. 기존 [응답 스키마](../schemas/saju_analysis.py)에는 이 전체 트리가 없고 `advanced_analysis.branch_dynamics`만 일부 구현되어 있다. 기존 [계산기](../services/branch_dynamics.py)는 지지 세력·쌍별 잠재 작용량·삼합/방합 구조를 내지만 경합 판정이나 작공을 계산하지 않는다.

## 구현 전 계약 정합성 확인

| 항목 | v3 샘플과 현재 규칙의 차이 | 첫 결정 제안 |
| --- | --- | --- |
| 완성 삼합의 내부 반합 **결정 완료** | 현재 계산기는 완성 삼합에서 내부 반합을 별도 쌍 관계로 출력하지 않는다. v3에서는 이를 추적하고 `component_pairs[].relation_id`에서 참조한다. | `activation_status: candidate_only`, `formation_status: included_in_complete_group`, `effect_status: structural_only`, `direction: null`, `metrics: null`로 기록한다. 독립 작용량을 산출하지 않고 경합 판정의 선택·억제·미해결 집합에서도 제외한다. 완성 삼합이 깨져 반합만 남으면 별도 쌍 관계의 잠재 작용을 평가한다. |
| 여섯 쌍의 생·극 **결정 완료** | 이전 v3 샘플에는 연–일·일–시의 土克水, 연–월·월–시의 水生木 후보가 빠져 있었다. 현재 계산기는 여섯 위치 쌍의 대표 오행 생·극을 검사한다. | 여섯 쌍을 모두 검사하고, 오행상 경로가 있으면 합·충·형·파·천과 공존해도 `relations[]`에 별도 후보로 기록한다. 이 예시는 생·극 5건, 동기 1쌍이다. 생·극 방향은 오행 관계로 정하고 세력·거리·다른 관계에 따른 작용 강도와 실제 성립은 별도로 판정한다. 후보의 방향을 힘의 우세에 따라 뒤집지 않으며 서로 다른 관계의 힘을 합산하지 않는다. 미판정 후보의 `0`/`null` 및 상태 조합은 다음 항목에서 확정한다. |
| `0`과 `null` **결정 완료** | 현재 계산기는 유보(`conditional`)와 완전 차단(`suppressed`)의 작용량을 모두 0으로 만든다. v3에서는 두 상태를 구별해야 한다. | `0`은 해당 관계·지표에서 규칙상 완전 차단 또는 계산된 결과가 0임을 확인한 경우에만 쓴다. 미계산·조건부 유보·실제 적용 미확정은 `null`이다. 관계의 잠재 강도와 실제 적용량을 분리하고 `calculation_status`로 미계산과 적용 대상 아님을 구분한다. |
| 동일 지지·자형 **결정 완료** | v3는 같은 글자의 반복과 자형을 별도 ID로 기록한다. 현재 코드는 자형을 탐지하지만 동지 표식은 독립 작용으로 계산하지 않는다. | `same_branch`는 위치별 반복을 뜻하는 구조 사실로만 기록한다(`effect_status: structural_only`, `calculation_status: not_applicable`, `metrics: null`). `self_punishment`는 인접한 辰辰·午午·酉酉·亥亥일 때 `active`, 격위면 `candidate_only`다. 두 상태 모두 `calculation_status: pending`, `metrics: null`이며 실제 형 작용량을 부여하지 않는다. |
| 그룹·관계 ID **결정 완료** | 현재 `interactions.matrix`와 v3의 ID 형식이 다르고, 이전 v3의 `group:wood_trine:1`·`wood_trine_a/b`는 출력 순서에 의존할 수 있었다. | 쌍 관계는 관계 유형과 정렬된 두 기둥 위치, 그룹은 종류와 정형 지지 조합, 성립 조합은 종류와 정렬된 실제 기둥 위치로 식별한다. 방향·세력·상태·출력 순번은 ID에 넣지 않는다. 쌍 관계와 그룹을 함께 참조하는 필드는 `interaction_ids` 계열로 명명하고 모든 참조의 존재·종류를 검증한다. |
| 그룹 수치 **결정 완료** | 그룹을 구성한 지지의 세력 비교는 가능하지만 그룹 자체의 독립 작용량 산식은 아직 정의되지 않았다. | `group_power: null`, `group_power_status: not_scored`를 유지한다. 반복 성립 조합은 한 구조망으로 기록하고 `evaluate_as_one_network`는 중복 힘의 합산 금지 정책으로만 쓴다. 참여 지지 세력·비중을 그룹 견인력으로 전환하지 않는다. |

남은 항목을 정하기 전에는 v3 예시를 그대로 스키마나 계산 결과에 복사하지 않는다. 완성 삼합 내부 반합은 구조 근거로만 참조한다. 동일 위치 쌍의 반합이 두 완성 삼합 조합에 속해도 `pairwise`에는 한 번 기록하고 두 `component_pairs`에서 같은 ID를 참조한다.

### 관계 수치의 상태 계약

`activation_status`는 관계의 성립·억제 상태, `calculation_status`는 그 관계의 **독립 작용량 계산 상태**다. 구조 사실에는 `not_applicable`, 계량 후보에는 나머지 상태를 사용한다.

| `calculation_status` | 의미 | `metrics`와 실제 적용량 |
| --- | --- | --- |
| `not_applicable` | 완성 삼합 내부 반합처럼 독립 작용량 대상이 아닌 구조 근거 | `metrics: null`. 수치 0으로 치환하지 않는다. |
| `pending` | 후보를 찾았으나 잠재 강도를 산출할 근거가 없음 | `metrics: null`. 실제 적용량도 미확정이다. |
| `potential_calculated` | 방향별 세력·거리·계수로 잠재 강도는 산출했으나 실제 작용은 미확정 | `metrics.directional_effects`의 잠재 지표는 숫자, 각 방향의 `applied_power_delta: null`. `conditional`도 이 상태일 수 있다. |
| `resolved` | 실제 작용의 성립 또는 완전 차단을 규칙과 함께 판정함 | 방향별 적용량은 계산값. 완전 차단이면 각 방향의 `applied_power_delta: 0`과 차단 사유를 함께 둔다. |

`metrics.directional_effects`는 생·극에 오행상 정해진 방향 하나를, 합·충·형·파·천에는 두 방향을 담는다. 각 항목의 `interaction_intensity`는 **잠재 강도**, `applied_power_delta`는 **실제 적용 변화량**이다. 잠재 강도가 양수라도 완전 차단되면 실제 적용량은 0이 될 수 있다. 조건부 유보나 부분 차단의 적용량은 확정 전까지 null이다. 숫자 0은 그 관계의 해당 방향·지표에만 적용된다. 설계 샘플의 월–일 극은 `pending` 예시지만 실제 조립기는 현재 규칙으로 잠재량을 계산한다. 동일 지지는 계량 대상이 아니며, 자형은 별도 성립 규칙이 검증된 뒤에만 계량 대상으로 승격할 수 있다.

**적용량 의미 확정:** `directional_effects[]`의 `applied_power_delta`는 해당 방향의 `to_pillar`가 받는 세력 변화량이다. 음수는 그 지지의 약화, 양수는 강화, 0은 그 방향의 독립 작용이 없음을 뜻한다. `from_pillar`의 지출이나 세력 변화는 이 필드에 넣지 않는다. `target_exposure`는 잠재 노출 지표이므로 적용량에 그대로 대입하지 않는다. 예를 들어 子午충에서 午→子의 노출 지표 `1.8952`는 子의 기준 세력 `0.7628`보다 크다. 충의 실제 변화량 산식·한도와 여러 활성 관계가 같은 지지에 주는 영향을 합치는 방식은 아직 정하지 않았다. `effective_power`는 주변 영향이 반영된 기준 세력이므로 쌍별 변화량을 중복 가산하지 않도록 계산 순서를 정해야 한다.

현재 계산기의 유보·후보 전용 관계에 기록된 0을 v3로 옮길 때는 원래 상태·규칙을 확인한다. 표시 형식만 바꾸어 null 또는 0으로 변환하지 않는다.

### ID와 그룹 수치 계약

ID는 **동일 분석 응답 안에서 고유**하다. 쌍 관계 ID는 `branch:<type>:<앞기둥>:<뒤기둥>`이며 기둥 순서는 항상 `year → month → day → hour`다. 예를 들어 `branch:control:year:day`의 극 방향이 일지→연지여도 ID 순서는 그대로다. 같은 위치 쌍과 관계 유형에서 규칙상 독립 사건이 여러 개 필요해질 때만 안정적인 변형 코드를 추가한다. 규칙의 `rule_id`와 출력 사건의 ID는 다른 개념이다.

그룹 ID는 `group:<type>:<정형 지지 조합>`이다. 샘플의 亥卯未 삼합은 `group:trine:hai_mao_wei` 하나이며, 亥의 위치가 둘이라도 그룹 ID를 두 개 만들지 않는다. 성립 조합 ID는 `formation:<type>:<정렬된 실제 기둥 위치>`다. 샘플의 두 조합은 `formation:trine:year:month:day`, `formation:trine:month:day:hour`이다. 동일한 `branch:half_combine:month:day`는 두 `component_pairs`에서 공유한다. 출력 순서, 점수, 우세 조합 판정이 바뀌어도 ID는 유지한다.

`relation_id`는 쌍 관계만, `group_id`는 그룹만, `formation_id`는 성립 조합만 가리킨다. 두 종류 이상을 함께 담는 목록은 `interaction_ids`로 명명한다. `component_pairs[].relation_id`는 반드시 존재하는 쌍 관계를 참조하고, `candidate_ids`·`selected_formation_ids`는 해당 그룹의 성립 조합만 참조한다. `active_interaction_ids`·`suppressed_interaction_ids`·`unresolved_interaction_ids`는 존재하는 쌍 관계 또는 그룹을 참조하며 서로 겹치지 않는다. 구조 전용 반합은 이 경합 집합이나 작공의 `source_interaction_ids`에 넣지 않고 `structural_context_relation_ids`에서 참조한다. 경합·작공·LLM의 다른 참조도 존재 여부를 검증한다.

`group_power_status: not_scored`는 그룹 자체에 독립 작용량을 부여하지 않는 정책을 뜻한다. `group_power: null`은 이 상태에서 0으로 치환하지 않는다. 그룹의 `counting_policy: evaluate_as_one_network`는 반복 성립 조합의 힘을 더하지 않는 규칙이며, 조합 중 우세한 하나를 자동 선정하거나 개별 지지의 힘을 더하는 산식이 아니다. 지지별 세력과 관계별 잠재 작용량은 각각의 결과에 남긴다.

### 자동 계약 검사

[주석 없는 v3 검증 샘플](../tests/fixtures/branch_dynamics_v3.json)은 [설계 샘플](./branch_dynamics_v3.json)의 JSON 데이터와 일치해야 한다. [계약 검사기](../schemas/branch_dynamics_v3_contract.py)는 여섯 위치 쌍, ID 형식·고유성·참조, 구조 전용 관계의 독립 작용량 금지, 미계산·조건부·완전 차단의 수치 상태, 그룹의 `not_scored`·한 구조망 정책을 검사한다. [계약 테스트](../tests/test_branch_dynamics_v3_contract.py)는 두 샘플의 동등성과 위반 사례를 확인한다.

검사 명령은 `python3 -m unittest discover -s tests -p test_branch_dynamics_v3_contract.py -v`다. 샘플을 바꾸면 검증용 JSON도 함께 갱신한다. 이 검사는 수치의 명리학적 타당성이나 v3 전체 필드의 상세 자료형을 아직 검증하지 않는다. 후속 단계에서 실제 응답 모델을 만들며 필수·선택 필드와 enum을 확정한다.

[독립 v3 응답 모델](../schemas/branch_dynamics_v3.py)은 현재 API의 v2 응답을 변경하지 않고 필수 필드, 중첩 자료형, 일부 상태 enum을 검증한다. 최상위 모델은 위 계약 검사기를 함께 실행한다. [모델 테스트](../tests/test_branch_dynamics_v3_model.py)는 검증 샘플 왕복, 필수 필드·자료형 오류, 미등록 필드와 잘못된 참조를 확인한다. 천간 분석·작공의 활성 경로·LLM 확정 결과처럼 샘플이 비어 있는 부분은 임시 자료형이며, 해당 계산 단계를 구현할 때 구체화한다.

## 단계와 완료 기준

| 단계 | 작업 | 산출물과 완료 기준 |
| --- | --- | --- |
| 1. 계약 정규화 | 위 차이를 해소하고 필수/선택 필드, enum, `null`/0 의미, ID 규칙을 정의한다. 주석이 있는 설계 샘플과 기계 검증용 JSON 또는 JSON Schema를 분리한다. | 네 지지·여섯 위치 쌍·반복 조합·참조 ID를 검증하는 계약 검사 통과. v3 샘플과 이전 문서의 우선순위 명시. |
| 2. v3 출력 골격 | 버전이 분리된 응답 모델과 조립기를 만든다. `meta`, `chart_context`, `branch_dynamics`를 먼저 채우고 `stem_dynamics`, 경합, 작공, LLM 결과는 계약상 허용된 보류 상태로 둔다. | 기존 API는 그대로 통과하고, v3 응답은 스키마 검증을 통과한다. `rule_version`은 실제 적용 규칙 버전을 가리킨다. |
| 3. 지지별 세력 근거 | 현재 `base_power`·`after_stem_power`·`effective_power`를 v3 `strength_evidence`와 `calculation_trace`로 연결한다. `effective_contribution`, 공식 ID, 조정 내역은 실제 계산식에서 생성한다. | 월간이 월지를 생·극하거나 월지가 월간을 생하는 사례에서 값과 근거가 일치한다. 미검증 계수는 `validation_status: unverified`로 유지한다. |
| 4. 쌍별 관계 | [관계 탐지기](../services/interaction_matrix.py)의 관계를 여섯 쌍에 위치별로 배치한다. 합·충·형·파·천·생·극의 공존, 조건 상태, 방향별 세력, 빈주 방향을 분리한다. v3 `metrics`는 실제 산출 가능한 항목만 채운다. | 子卯·卯午·午酉파, 子卯형 제외, 午未합土, 충과 극의 공존, 거리·월령 변화, `0`/`null` 사례가 검증된다. 두 방향의 주도와 받은 작용을 혼동하지 않는다. |
| 5. 다자 구조 | 삼합·방합·삼형의 `formation_candidates`, `component_pairs`, 중복 지지, 인접 충과 억제 사유를 출력한다. 구성 쌍과 독립 작용을 분리한다. | `亥卯未亥`의 두 위치 조합, `巳亥卯未`의 깨진 삼합과 잔존 반합, `巳午未寅`의 방합·午未 육합이 중복 힘 없이 출력된다. |
| 6. 관계 경합 판정 | `interaction_resolution`을 독립 단계로 만든다. 경쟁 후보마다 적용 규칙과 근거를 남기고, 결정할 근거가 없으면 `unresolved`를 유지한다. | `selected_interaction_ids`, `suppressed_interaction_ids`, `unresolved_interaction_ids`가 실제 후보 ID의 부분집합이며 서로 충돌하지 않는다. `potential`을 자동으로 `active`로 승격하지 않는다. |
| 7. 작공·LLM 자료 | 천간·지지·십신·빈주 및 경합 결과를 참조해 `work_dynamics`를 만든다. 근거가 부족하면 `pending_resolution`과 null을 유지한다. 마지막에 `llm_interpretation_payload`를 검증된 사실과 미해결 사항으로 분리해 조립한다. | 모든 작공 경로의 `source_interaction_ids`가 존재한다. 결과 귀속과 주요 경로는 근거 없이 확정되지 않는다. LLM 자료는 계산 결과를 바꾸지 않는다. |
| 8. 전환 | 기존 응답의 소비자를 확인하고 v3를 별도 버전 또는 명시적 선택 방식으로 제공한다. 새 계약으로 옮긴 뒤 기존 `bin_zhu_dynamics`와 중복된 요약의 사용을 단계적으로 중단한다. | 기존 회귀 테스트와 v3 계약 테스트가 모두 통과하고, 제거 시점과 마이그레이션 경로가 문서화된다. |

## 진행 원칙

1. 각 단계에서 **출력 계약 → 원본 규칙·계산 → 실제 사례 → 스키마/참조 검증** 순으로 마무리한다. 임의의 숫자로 null을 채우지 않는다.
2. `interaction_resolution`은 [지지 작용 결과](../services/branch_dynamics.py)와 구조 규칙을 입력으로 사용하고, `work_dynamics`는 그 판정을 참조한다. `llm_interpretation_payload`는 마지막 표현 계층이다.
3. 새로운 계산 규칙은 [관계 규칙 원본](../services/relation_rules.py)에 두고 조합별 조건·방향·계수의 근거와 잠정 여부를 표시한다.
4. [기존 빈주 분석](../services/bin_zhu.py)의 합·대립 총점이나 단일 벡터를 v3 관계의 주도권으로 재사용하지 않는다. 빈주는 위치와 결과 해석의 보조 맥락이다.

**첫 실행 단위인 계약 정규화의 기준 샘플·검사기·응답 모델을 마련했다.** 다음에는 기존 API와 분리된 v3 조립기를 만들고 실제 계산 결과에서 근거가 확인되는 필드만 채운다. 미구현 분석은 계약상 허용된 null·보류 상태로 남기고, 샘플의 가상 수치를 계산값으로 복사하지 않는다.

### v3 조립기 첫 단위: 개별 지지 세력

[기초 조립기](../services/branch_dynamics_v3_assembler.py)는 기존 계산기의 결과를 입력받아 `meta`, `chart_context`, `branch_strengths`만 만든다. 전체 v3 응답이나 API 엔드포인트를 아직 만들지 않는다. 원국 네 기둥과 계산 결과의 지지·동주 천간이 일치하는지 검사한다.

| v3 필드 | 현재 원본 | 처리 |
| --- | --- | --- |
| `meta.rule_version` | `rule_version` | 실제 계산에 사용한 규칙 버전을 복사 |
| `base_power`, `after_stem_power`, `effective_power` | 같은 이름의 세력 값 | 숫자를 그대로 복사 |
| `season.factor` | `components.seasonal_factor` | 지장간별 월령 계수의 가중평균으로 해석 |
| `season.relation` | 월지·대상 지지의 대표 오행 | 기존 월령 관계 함수로 산출; 지장간 각각의 관계는 `hidden_stems`에 유지 |
| `same_pillar_stem` | `stem_branch_relation` | 월간의 월지 생·극·설기 등을 포함해 관계·효과·보정량 복사 |
| `surroundings` | `ambient_evidence` | 원본의 주변 오행 관계와 조정률 복사; 조건부라서 원본이 0으로 처리한 값은 미확정 `null`로 표시 |
| `calculation_trace.applied_adjustments` | 동주 보정량, 동주 후·주변 반영 후 세력의 차이 | 두 단계의 실제 순변화량만 기록; 주변 지지별 기여도를 역산하지 않음 |
| `hidden_stems[].effective_contribution`, 공식 ID | 현재 원본 없음 | `null` 유지 |

세력은 검증된 절대량이 아닌 잠정 상대 지표이므로 `validation_status: unverified`다. 관계별 잠재 강도나 실제 적용량은 이 세력값에서 자동 생성하지 않는다. [기초 조립기 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 실제 계산 결과와 네 지지의 수치 일치, 월간이 월지를 돕거나 극하거나 설기하는 경우, 다른 원국의 결과 혼입 방지를 검증한다. 다음 단위는 여섯 쌍의 관계 후보를 v3 ID와 상태 계약으로 옮기는 작업이다.

### v3 조립기 두 번째 단위: 여섯 지지 쌍

[기초 조립기](../services/branch_dynamics_v3_assembler.py)의 `assemble_branch_pairs_v3`는 기존 계산 결과의 여섯 위치 쌍을 고정 순서로 배치하고 관계 유형을 v3 명칭과 ID로 옮긴다. 대표 오행의 생·극 방향은 기존 계산 결과의 방향을 사용하고 해당 방향의 빈주 위치 정보를 붙인다. 같은 쌍에서 공존하는 관계의 ID도 연결한다. 형·파·충·합 등 양방향 관계의 주도 정보는 기존의 관계별 `force_dominance`와 `roles`를 잠정 근거로 유지하되, 독립적인 `direction`은 아직 확정하지 않는다. `power_before`는 해당 쌍 밖의 배경을 고려한 기존 세력 값이다.

기존 `force`는 양방향 잠재 값이지만 조건부·차단 상태에서는 0으로 가려진다. v3의 초기 쌍별 조립에서는 일반 관계를 `pending`으로 두었다. 이후 방향별 산식을 추가하여 세력·거리·계수가 있는 관계는 `potential_calculated`로 옮겼다. 규칙상 완전 차단된 관계는 `resolved`와 방향별 `applied_power_delta: 0`, 차단 사유를 함께 기록한다. 조건부 합은 잠재량을 계산하더라도 적용량은 `null`이다. 완성 삼합 내부 반합은 독립 작용이 없는 `structural_only`, 동일 지지는 반복 사실인 `structural_only`, 자형은 인접할 때 `active`로 기록하지만 독립 작용량은 `pending`이다. 삼합이 깨진 뒤 남은 반합은 독립 후보로 유지한다.

[조립기 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 생·극 방향, 완성 삼합의 구성 반합, 자형·동지, 子卯·卯午·午酉파, 子卯형 제외, 午未합土, 충과 극의 공존, 조건부 합과 깨진 삼합의 잔존 반합을 확인한다. **이 결과는 쌍별 부분 조립 결과**이며 그룹·경합·작공을 포함한 전체 v3 응답으로 공개하지 않는다. 다음에는 그룹을 조립하고 내부 반합 참조와 모든 관계 ID의 정합성을 전체 계약에서 검사한다.

### v3 조립기 세 번째 단위: 다자 구조

같은 [조립기](../services/branch_dynamics_v3_assembler.py)의 `assemble_branch_groups_v3`는 기존 삼합·방합·삼형 후보를 정형 지지 순서의 그룹 ID와 위치별 성립 조합 ID로 옮긴다. 하나의 그룹에 여러 성립 조합이 있으면 `formation_candidates`에 각각 넣고, 공통 기둥은 `overlap.shared_pillars`로 기록한다. `evaluate_as_one_network`는 힘을 합산하지 않는 정책이며, 우세 조합은 아직 선정하지 않는다. 그룹의 독립 수치는 항상 `group_power: null`, `group_power_status: not_scored`다.

완성 삼합 후보의 구성 반합만 `component_pairs`로 참조하며, 해당 ID가 실제 쌍 관계에 있고 `structural_only`인지 조립 시 검사한다. 반복되는 `亥卯未亥`의 두 성립 조합은 동일한 `卯未` 반합 ID를 공유한다. 억제된 삼합의 `component_pairs`는 비워 두어 독립적으로 남은 반합을 그룹 내부 작용으로 오인하지 않는다. 삼형은 세 글자가 있으면 `active` 그룹으로 기록하되, 성립 조합별 세력·방향 근거가 아직 없으므로 빈 방향 목록과 `group_power: null`을 유지한다. 구성 쌍의 관계는 각각의 조건에 따라 남긴다. 그룹의 실제 합화와 작용량은 확정하지 않는다.

[조립기 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 반복 삼합의 ID 공유, 억제된 삼합과 잔존 반합, 방합·삼형의 무점수 상태, 누락된 구조 반합 참조를 확인한다. `亥卯未亥`의 실제 조립 결과는 현재 [v3 전체 응답 모델](../schemas/branch_dynamics_v3.py)과 [계약 검사기](../schemas/branch_dynamics_v3_contract.py)에도 통과한다. 전체 응답의 경합·작공 부분은 아직 예시의 보류 상태를 사용해 검증했으므로, 실계산 결과의 최종 v3 응답 생성으로 해석하지 않는다. 다음은 관계 경합과 실제 적용 상태를 판정하는 단계다.

### v3 조립기 네 번째 단위: 관계 경합의 보수적 분류

[조립기](../services/branch_dynamics_v3_assembler.py)의 `assemble_interaction_resolution_v3`는 `pairwise`와 `groups`의 모든 독립 후보를 분류한다. 구조 전용 반합과 동지는 경합 후보에서 제외하고 필요한 경우 `structural_context_relation_ids`로만 연결한다. 입력에서 `active`로 확정된 쌍 관계는 활성 목록에 넣는다. 기존 관계 규칙에 완전 차단이 명시되고 `applied_power_delta: 0`과 사유가 확인된 쌍 관계, 또는 억제 사유가 명시된 그룹은 `suppressed_interaction_ids`에 넣는다. 나머지는 `unresolved_interaction_ids`에 넣으며 잠재량만으로 `active`로 올리지 않는다. 조립기 내부에서 세 목록이 구조 전용을 제외한 모든 후보를 중복 없이 덮는지 검사한다.

한 위치 쌍에 독립 후보가 둘 이상 있으면 `resolve:<두 기둥>` 사례를 만든다. 같은 쌍에 참여하는 그룹도 경합 후보에 포함한다. 그룹의 성립 조합이 여러 개인 경우 별도 중첩 사례를 만들지만 `selected_formation_ids`를 비워 두고 한 구조망 정책을 유지한다. 이미 완전 차단된 후보의 규칙·사유는 해당 사례에 기록한다. 생·극·합·충 등 사이에서 어느 관계가 실제 주작용인지 고르는 규칙과 잠재 강도의 단일 산식은 아직 없으므로 다른 사례는 `unresolved`다. `active_interaction_ids`가 빈 것은 계산 결과의 부재를 뜻하며 관계가 실제로 없다는 판정이 아니다.

이후 확정한 정책에 따라 같은 위치 쌍의 파·천·충·육합·두 지지의 형이 `active`일 때에만 생·극의 독립 적용량을 0으로 처리한다. 억제된 후보에는 규칙 ID와 성립한 구조 관계 ID를 근거로 남긴다. `interaction_resolution`은 입력에 `active`가 명시된 관계를 활성 목록과 해당 사례의 선택 목록에 기록한다. 파·충·천·두 지지의 지세형은 쌍이 있으면 거리와 무관하게 `active`, 육합은 인접 충 개입이 없을 때 `active`로 판정하며, 같은 쌍의 생·극을 억제하고 주변 세력 보정도 0으로 한다. 육합의 인접 충 개입은 기존 `conditional`·`suppressed` 조건을 유지한다. 삼형 그룹은 세 글자가 있으면 `active`로 분류하지만, 쌍별 관계를 억제하거나 독립 작용량을 더하지 않는다. 자형은 같은 辰·午·酉·亥가 인접할 때만 `active`, 격위면 `candidate_only`다. 삼형·자형의 실제 작용량은 별도 과제로 남는다.

[조립기 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 `亥卯未亥`의 모든 후보 포괄, 구조 반합 참조 분리, 중첩 삼합의 우세 미선정, `子卯` 파 활성과 생 억제 및 子卯형 제외, 인접·격위 파·충의 활성, 조건부 합의 미해결 유지를 검사한다. 실제 조립한 경합 결과를 포함한 `亥卯未亥` 데이터가 v3 전체 모델과 참조 계약을 통과한다. 작공·LLM 필드는 여전히 설계 샘플의 보류 상태를 이용한 검증이다. 다음에는 관계별 **잠재 강도 산식과 상태별 적용 판정 기준**을 규칙표에 명시한 뒤 `pending`인 수치의 계산 가능 범위를 좁힌다.

### v3 조립기 다섯 번째 단위: 방향별 잠재 작용량

[v3 관계 모델](../schemas/branch_dynamics_v3.py)의 `metrics`는 관계 전체의 단일 점수 대신 `directional_effects` 목록을 갖는다. 생·극은 오행상 정해진 방향 하나, 합·충·형·파·천과 독립 반합은 두 방향을 기록한다. 강한 지지가 어느 쪽인지에 따라 생·극의 오행 방향을 뒤집지 않는다. 각 방향은 `from_pillar`, `to_pillar`, `acting_domain`, `receiving_domain`, `source_capacity`, `coefficient`, `distance_weight`, `interaction_intensity`, `target_exposure`, `applied_power_delta`를 갖는다. 빈주 위치는 방향별 해석 맥락이며 힘의 산식에 들어가지 않는다.

[규칙 파일](../services/relation_rules.py)에 산식 ID와 v3 규칙 버전을 명시했다. `source_capacity`는 해당 쌍의 상대를 제외하고 계산한 지지 세력이다. `interaction_intensity = round(source_capacity × distance_weight × directional_coefficient, 4)`이며, `target_exposure = round(interaction_intensity × source_capacity ÷ (source_capacity + target_capacity), 4)`다. 분모가 0이면 노출 지표는 계산된 0이다. 두 값은 **미보정 상대 지표**로 실제 피해나 이익의 크기가 아니다. 다른 관계 유형의 강도는 더하지 않는다. v3 `meta.rule_version`에는 기존 세력·계수 규칙 버전과 v3 방향별 산식 버전을 함께 표시한다.

기존 계산기의 조건부·억제 관계는 `force`가 상태에 따라 0으로 가려진다. v3는 가려지기 전의 세력·거리·계수로 잠재량을 다시 산출한다. 조건부 관계의 적용량은 `null`, 완전 차단으로 확인된 관계의 적용량만 양방향 또는 오행상 단일 방향에 `0`으로 기록한다. 자형은 인접 여부로 성립을 판정하지만 독립 계량 규칙은 미정이며, 공합·암합도 `pending`, `metrics: null`을 유지한다. 구조 전용 반합과 동지는 `not_applicable`, `metrics: null`이다. 잠재량 계산만으로 `active_interaction_ids`를 채우거나 실제 결과 귀속을 정하지 않는다.

예를 들어 한 충의 `directional_effects`는 다음 두 항목이 된다. 수치는 사례별 계산값이며 아래 키 구조는 설명용이다.

```json
{
  "potential_formula_id": "branch:potential_source_distance_coefficient_v1",
  "exposure_formula_id": "branch:exposure_source_share_v1",
  "directional_effects": [
    {"from_pillar": "year", "to_pillar": "month", "acting_domain": "guest", "receiving_domain": "guest", "source_capacity": 0.7628, "coefficient": 1.0, "distance_weight": 1.0, "interaction_intensity": 0.7628, "target_exposure": 0.1795, "applied_power_delta": null},
    {"from_pillar": "month", "to_pillar": "year", "acting_domain": "guest", "receiving_domain": "guest", "source_capacity": 2.4785, "coefficient": 1.0, "distance_weight": 1.0, "interaction_intensity": 2.4785, "target_exposure": 1.8952, "applied_power_delta": null}
  ]
}
```

[계약 검사기](../schemas/branch_dynamics_v3_contract.py)는 방향 중복, 생·극 역방향, 미계산 상태의 숫자, 조건부 관계의 적용량 확정, 완전 차단의 0·사유 누락을 거부한다. [조립기 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 월간 변화가 월지→연지의 충 잠재량을 바꾸면서도 子→午 극 방향을 유지하는지 확인한다. 다음 작업은 조합별 **실제 성립·부분 억제**를 판정할 명리 규칙과 근거를 검증하는 것이다. 그 기준이 없는 관계는 계속 미해결로 둔다.
