# 지지 관계 성립 판정 단계별 기록

작성일: 2026-10-31. 아래 첫 표는 [실행 규칙](../services/relation_rules.py) v2 `2.14.0`, v3 `3.3.0-draft` 당시 [v3 조립기](../services/branch_dynamics_v3_assembler.py)의 실행 결과를 보존한 **변경 전 기준선**이다. 현재 버전과 출력은 마지막 3단계 기록을 따른다. 모든 사례의 천간은 `甲甲甲甲`이며, 표의 대상 쌍은 연지–월지다. 마지막 寅亥 변형 사례만 월지–일지다. 지지 네 글자의 위치와 동주 천간을 고정한 사례이므로 다른 원국에 그대로 일반화하지 않는다.

`potential`은 관계 후보의 잠재량을 계산했다는 뜻이다. `active`나 실제 적용량을 뜻하지 않는다. `force_dominance`는 방향별 잠재량 우세이며 실제 주작용 선정이 아니다. 아래 다섯 사례 모두 `active_interaction_ids`는 비어 있다.

| 쌍과 원국 지지 | 구조 관계 출력 | 생·극 출력 | 현재 경합 판정 | 확인된 근거와 미결정 사항 |
| --- | --- | --- | --- | --- |
| 子午 / 子午辰寅 | 충 `potential`, 잠재량 子→午 `0.7628`·午→子 `2.4785`, 잠재 우세 `month` | 水克火 `potential`, 子→午 `0.6102` | 충·극 모두 `unresolved` | [子午 조합 규칙](../services/relation_rules.py)의 충·극 계수는 있다. 충의 성립 여부, 충 성립 시 극 억제, 다른 지지 개입 조건은 미정이다. 잠재 우세가 午인 사실은 오행상 극 방향 子→午를 뒤집지 않는다. |
| 寅亥 / 寅亥辰子 | 육합 `potential`, 寅→亥 `1.0450`·亥→寅 `1.9017`, 잠재 우세 `month` | 水生木 `potential`, 亥→寅 `1.1410` | 육합·생 모두 `unresolved` | [寅亥 조합 규칙](../services/relation_rules.py)에 결합·생 후보와 지장간 손상 후보가 있다. 합화 여부는 확정되지 않는다. 합의 실제 성립과 생 억제 여부는 미정이다. |
| 寅巳 / 寅巳申未 | 천 `potential`, 寅→巳 `0.6569`·巳→寅 `1.4052`, 잠재 우세 `month` | 木生火 `potential`, 寅→巳 `0.6064` | 천·생 모두 `unresolved`; 寅巳申 삼형은 `candidate_only` | [寅巳 조합 규칙](../services/relation_rules.py)의 쌍별 세부 작용은 비어 있다. 천의 실제 성립, 삼형 후보가 천의 방향·강도를 바꾸는 조건은 미정이다. |
| 子卯 / 子卯午寅 | 파 `potential`, 子→卯 `0.3343`·卯→子 `1.2101`, 잠재 우세 `month` | 水生木 `suppressed`, 적용량 `0`, 사유 `break_blocks_generation` | 파 `unresolved`, 생 `suppressed` | [子卯 조합 규칙](../services/relation_rules.py)은 파의 `active` 확정 전에 생을 명시적으로 차단한다. 이 선제 억제를 유지할지, 파 성립 후 억제로 바꿀지 결정이 필요하다. |

## 기존 조건부 판정 사례

`申寅亥子`의 월지–일지 寅亥 육합은 `external_adjacent_clash` 때문에 `conditional`이다. 인접한 申이 寅을 충한다. 같은 쌍의 水生木은 `potential`이며, 육합·생 모두 경합 결과가 `unresolved`다. [육합 조건 규칙](../services/relation_rules.py)은 외부 인접 충을 조건부로, 두 합 글자 사이의 인접 충을 억제로 분류한다. 이 조건부 출력은 실제 합 성립이나 생의 실제 적용을 확정하지 않는다.

## 2단계에서 결정할 질문

1. 쌍별 관계를 `active`로 확정하는 **최소 근거**는 무엇인가? 현재의 `potential`·잠재 우세·인접성만으로 확정할지, 외부 충·삼자 구조·월령·동주 천간 등의 조건을 더 확인할지 정해야 한다.
2. 구조 관계가 `conditional`인 동안 생·극은 `unresolved`로 둘지, 별도 조건에서 독립적으로 활성화할지 정해야 한다.
3. 子卯·卯午의 생 선제 억제를 조합별 예외로 유지할지, 공통 정책과 맞춰 파가 `active`일 때만 억제할지 정해야 한다.
4. 寅巳申 삼형의 성립은 각 쌍의 천·충·육합을 어떻게 수정하는가? 삼형의 구조 판단과 쌍별 적용량을 분리해야 한다.

여기까지는 1단계의 관찰 결과다. 아래 2단계 결정 외의 성립 조건은 아직 확정되지 않았다.

## 2단계 결정: 생·극 억제 정책 통일

사용자 결정에 따라 子卯·卯午의 생 선제 억제를 없애고, 다른 파·천·충·육합·쌍별 형과 같은 흐름으로 통일한다. 구조 관계가 `potential`·`conditional`·`candidate_only`이면 생·극은 후보와 잠재량을 유지하고 실제 적용은 미해결이다. 구조 관계가 `active`로 확정되면 같은 쌍의 생·극 후보를 `suppressed`, 독립 적용량 0으로 기록한다. 구조 관계가 `suppressed`라면 그 관계만을 이유로 생·극을 억제하지 않으며 생·극의 실제 성립은 별도로 판정한다. 이 결정은 후보의 존재나 잠재 우세만으로 구조 관계를 `active`로 승격시키지 않는다.

### 기존 구현에 미치는 영향

| 경로 | 현재 확인한 동작 | 3단계 구현 시 필요한 변경 |
| --- | --- | --- |
| [조합별 규칙](../services/relation_rules.py) | 子卯·卯午의 생에 계수 0, `status: suppressed`, `break_blocks_generation`을 명시 | 선제 차단 항목을 제거하고 일반 생 후보의 계수를 사용한다. 파의 후보·계수는 유지한다. |
| [v2 지지 세력](../services/branch_dynamics.py) | 주변 보정의 생 상태를 조합별 규칙에서 읽는다. 실제 확인한 두 쌍의 양방향 `ambient_evidence`는 `suppressed`, 보정률 0이다. | 생을 잠재 배경으로 다시 반영하되, 이후 구조 관계가 실제 `active`일 때 지지 세력에 이미 들어간 생을 어떻게 제거·재계산할지 별도 계약을 둔다. 최종 세력과 쌍별 적용량의 중복을 허용하지 않는다. |
| [v2 쌍별 작용](../services/branch_dynamics.py) | 두 쌍의 생 `directional_coefficients`와 `force`가 양방향 0, 상태가 `suppressed`다. | 생은 오행상 한 방향의 잠재량을 갖는 `potential`로 바뀌며 반대 방향은 계속 0이다. |
| [v3 쌍별·경합](../services/branch_dynamics_v3_assembler.py) | v2의 선제 차단을 `resolved`, 적용량 0으로 옮긴다. 파는 `potential`이라 경합 결과는 미해결이다. | v2 규칙 변경 후 생도 `potential_calculated`, 적용량 `null`과 `unresolved`가 된다. 기존의 **`active`로 확정된 구조 관계에 의한 생·극 억제** 경로는 유지한다. |
| [회귀 테스트](../tests/test_branch_dynamics.py)·[v3 테스트](../tests/test_branch_dynamics_v3_assembler.py) | 두 쌍의 선제 차단, 보정률 0, v3 억제 목록을 기대한다. | 후보·방향·잠재량·주변 보정의 새 기대값과 `active` 구조 관계의 억제 사례를 검증한다. |

### 3단계 구현 제안

1. 子卯·卯午의 `생` 조합별 선제 차단 항목을 제거한다. 두 쌍의 파 후보와 `primary_relation`은 그대로 둔다.
2. v2 세력·쌍별 작용과 v3 경합 출력의 실제 변화를 확인한다. 생의 잠재량이 0보다 크고 적용량은 `null`인지, 파가 후보일 때 생이 자동 억제되지 않는지 검사한다.
3. 관련 회귀 테스트와 [규칙 문서](./mangpa_relation_rulebook.md), [v2 설명](./branch_dynamics_v2.md), [v3 계획](./branch_dynamics_v3_plan.md), [이어받기 메모](./branch_dynamics_handoff.md)를 새 정책에 맞춘다.
4. 관계를 실제 `active`로 판정하는 조건은 다음 결정 단계에서 다룬다. 그 단계에서는 주변 생 보정의 재계산 시점과 쌍별 작용량의 중복 방지를 함께 설계한다.

**2단계 종료 당시:** 정책을 확정했고, 위 1~3을 다음 구현 단계로 제안했다.

## 3단계 구현 결과

[실행 규칙](../services/relation_rules.py) v2 `2.15.0`, v3 `3.4.0-draft`에서 子卯·卯午의 `생` 전용 0 계수와 `break_blocks_generation` 선제 차단을 제거했다. 파의 후보 조합·계수·정적 기본 분류는 유지했다. v2와 v3는 파가 `potential`일 때 생도 `potential`로 출력하며, v3의 생 적용량은 `null`, 경합 판정은 `unresolved`다. `active`로 확정된 파에 의한 생 억제 정책은 유지된다.

실행 확인 사례:

| 원국 지지와 위치 쌍 | 생 후보의 현재 출력 | 주변 세력 보정 |
| --- | --- | --- |
| `子卯辰寅`, 연–월 子卯 | 子→卯 v2 잠재 작용 `0.4341`; v3 `potential_calculated`, 적용량 `null`, 경합 `unresolved` | 子→卯 지원 `+0.034674`, 卯→子 설기 `-0.043516`; 둘 다 `potential` |
| `子卯午寅`, 월–일 卯午 | 卯→午 v2 잠재 작용 `1.6683`; v3 `potential_calculated`, 적용량 `null`, 경합 `unresolved` | 卯→午 지원 `+0.058022`, 午→卯 설기 `-0.037042`; 둘 다 `potential` |

두 쌍 모두 생의 반대 방향 실제 잠재 작용은 0이며, 오행상 생 방향을 바꾸지 않는다. 주변 보정은 현 v2 계산기의 잠재 배경값이다. 앞으로 파의 실제 성립을 자동 판정하게 되면 이미 반영된 주변 생 보정을 재계산하거나 별도 기준값으로 분리해야 한다. **관계의 `active` 성립 조건과 최종 세력 재계산은 아직 구현되지 않았다.**

## 4단계 결정: 파·충의 성립과 거리

사용자 결정에 따라 원국에 해당 지지 쌍이 있으면 파·충은 인접 여부와 관계없이 `active`로 본다. 거리는 관계의 존재를 바꾸지 않고 방향별 작용 강도에 반영한다. 두 지지의 상대 세력은 어느 쪽의 작용이 강한지를 정하는 근거이며, 약한 지지 쪽의 관계 자체를 삭제하지 않는다. 다른 구조가 파·충을 억제한다는 조합별 규칙이 확정되면 해당 규칙에 따라 상태를 다시 판정한다. 현재 그런 일반 차단 규칙은 정의하지 않았다.

이 결정은 **쌍별 관계가 성립한다는 상태**에 관한 것이다. `interaction_intensity`는 미보정 잠재 지표이고, `applied_power_delta`와 최종 지지 세력 증감은 아직 미정이다. 같은 위치 쌍의 파·충을 `active`로 만들 때 생·극은 공통 억제 정책에 따라 `suppressed`로 기록해야 한다. 지지별 `effective_power`에 이미 들어간 그 쌍의 생·극 주변 보정도 같은 판정을 적용해 제거해야 일관된다.

### 다음 구현 단계 제안

1. [관계 매트릭스](../services/interaction_matrix.py)에서 확인된 파·충 쌍에 `activation_status: active`와 적용 규칙 ID를 부여한다. 인접·격위 모두 같은 상태로 두고 기존 거리 가중치를 유지한다.
2. [지지 계산기](../services/branch_dynamics.py)는 해당 위치 쌍의 생·극 후보를 억제하고, 지지별 주변 보정에서 같은 쌍의 생·극 기여를 제외한다. 별도 위치 쌍의 후보에는 이 판정을 전파하지 않는다.
3. [v3 조립기](../services/branch_dynamics_v3_assembler.py)는 파·충을 활성 목록에, 억제된 생·극을 억제 목록에 넣고 규칙·관계 ID를 근거로 남긴다. 활성 상태 자체를 실제 적용량의 숫자로 취급하지 않는다.
4. 子卯·卯午·午酉파와 子午충의 인접·격위 사례, 다중 관계가 있는 원국, 월간 변화에 따른 잠재 강도, 다른 쌍의 생·극 유지, 전체 응답 계약을 검증한다. 적용량과 삼형·자형의 성립은 다음 결정 단계로 남긴다.

**4단계 결정 당시:** 성립 기준을 확정했고 위 자동 판정·주변 보정 변경을 다음 구현 단계로 제안했다.

## 5단계 구현 결과

[실행 규칙](../services/relation_rules.py) v2 `2.16.0`, v3 `3.5.0-draft`에서 파·충이 탐지되면 근접·격위 모두 `active`로 기록한다. [관계 매트릭스](../services/interaction_matrix.py)는 `branch:pair_presence_active_v1`을 성립 근거로 남긴다. 같은 위치 쌍의 생·극 후보는 [지지 계산기](../services/branch_dynamics.py)에서 `suppressed`로 처리하고, 그 쌍의 지지별 주변 보정도 0으로 만든다. 다른 위치 쌍의 생·극 후보에는 이 억제를 전파하지 않는다.

[v3 조립기](../services/branch_dynamics_v3_assembler.py)는 파·충을 `active_interaction_ids`에, 같은 쌍의 생·극을 `suppressed_interaction_ids`에 넣는다. 억제된 생·극의 방향별 잠재량은 근거용으로 유지하고 `applied_power_delta: 0`을 기록한다. 파·충 자체의 방향별 `interaction_intensity`는 잠재량이며 실제 적용량은 `null`이다. 성립과 적용량의 의미를 구분한다.

[매트릭스 테스트](../tests/test_interaction_matrix.py)와 [지지 계산 테스트](../tests/test_branch_dynamics.py)는 인접·격위 파·충, 같은 쌍 생·극 억제, 주변 보정 0, 다른 쌍의 생 유지, 거리 가중치 1.0·0.5를 검증한다. [v3 테스트](../tests/test_branch_dynamics_v3_assembler.py)는 활성·억제 ID와 근거를 검사한다. 천·합·쌍별 형의 자동 성립 조건, 삼형·자형, 파·충의 실제 적용량과 다자 구조가 파·충을 제약하는 규칙은 다음 결정 단계로 남는다.

전체 테스트 107개를 통과했다. [v2 응답 스키마](../schemas/saju_analysis.py)는 `active` 상태와 성립 규칙 ID를 허용한다.

## 6단계 결정과 구현: 천·형·육합 성립

사용자 결정에 따라 천 6쌍과 쌍별 지세형 丑戌·戌未는 두 글자가 함께 있으면 거리와 관계없이 `active`다. 육합은 기존의 인접 충 개입 조건을 유지하여 합 사이의 충은 `suppressed`, 합 밖의 인접 충은 `conditional`로 두고, 그 밖에는 `active`다. 거리 가중치는 세력별 잠재 강도에만 영향을 준다. 삼형 그룹과 자형은 이 변경에 포함하지 않는다.

[관계 탐지기](../services/branch_relations.py)와 [매트릭스](../services/interaction_matrix.py)에 성립 상태를 반영했다. 적용 규칙 ID는 `branch:pair_presence_active_v1`이다. 성립한 쌍의 생·극 억제와 주변 보정 0은 기존의 공통 정책을 사용한다. 육합 후보 오행과 합화 성립 여부는 분리한다. v2 규칙 버전은 `2.17.0`, v3 잠재량 계약 버전은 `3.6.0-draft`다. `active` 관계의 실제 세력 증감 `applied_power_delta`는 아직 미정이다.

## 7단계 결정과 구현: 삼형 그룹 성립

사용자 결정에 따라 寅巳申·丑戌未는 세 지지가 원국에 있으면 떨어져 있어도 `active` 그룹으로 기록한다. 연속된 세 기둥인지는 기존 `is_adjacent` 근거로 유지한다. 성립 규칙 ID는 `branch:triple_punishment_presence_active_v1`이다. 구성 쌍의 천·충·육합·지세형은 각자의 성립 조건을 적용한다. 특히 육합은 인접 충 개입 시 `conditional` 또는 `suppressed`를 유지하며, 삼형 그룹의 `active`가 이를 바꾸지 않는다.

v3 `interaction_resolution.active_interaction_ids`에 삼형 그룹 ID를 넣고, 그룹의 `group_power: null`과 `group_power_status: not_scored`는 유지한다. 쌍별 잠재 강도와 적용량에 삼형 그룹의 독립 점수를 더하지 않는다. v2 규칙 버전은 `2.18.0`, v3 잠재량 계약 버전은 `3.7.0-draft`다.

## 8단계 결정과 구현: 인접 자형

사용자 결정에 따라 辰辰·午午·酉酉·亥亥는 두 글자가 인접한 위치 쌍일 때만 `active`다. 격위의 동일 글자 쌍은 `candidate_only`로 보존한다. 세 글자가 반복되면 각 위치 쌍을 별도로 판정한다. 성립 규칙 ID는 `branch:adjacent_self_punishment_active_v1`이다. 자형은 기존의 긴장 총점에 독립 점수를 추가하지 않고, v3 `metrics: null`·`calculation_status: pending`으로 실제 작용량을 유보한다. v2 규칙 버전은 `2.19.0`, v3 잠재량 계약 버전은 `3.8.0-draft`다.
