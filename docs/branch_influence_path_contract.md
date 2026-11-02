# 지지 작용 출처 경로의 최소 자료 구조

상태: **설계 계약 + v3 초안 연결**. [A·D 출처 추적](./chouwei_a_d_source_paths.md)과 [방합 내부 출처 장부](./branch_group_source_ledger.md)의 관측·미해결 항목을 한 형태로 표현한다. [내부 경로 조립기·검증기](../services/branch_influence_paths.py)가 현재 일반 보정과 관계·그룹 후보를 읽어 이 계약을 검증하고, [v3 조립기](../services/branch_dynamics_v3_assembler.py)가 중앙 경로 목록과 지지별 참조 ID를 만든다. 산식·계수·관계 판정 및 현재 API는 변경하지 않았다.

## 왜 한 방향의 경로가 필요한가

현재 [v3 지지 모델](../schemas/branch_dynamics_v3.py)의 `strength_evidence.surroundings[]`는 **한 출처 지지 → 한 대상 지지**의 일반 배경 보정을 기록한다. [v2 계산기](../services/branch_dynamics.py)는 같은 위치 쌍에서도 양방향 보정률을 각각 산출한다. 반면 방합은 여러 지지가 한 구조를 이루고, 입묘·충제의 대상은 지지 전체가 아니라 특정 지장간일 수도 있다. 이 둘을 쌍별 보정률 하나로 합치면 출처와 피해 대상을 잃는다.

따라서 장부의 기본 단위는 **원국의 특정 출처 집합이 특정 대상 하나에 미치는 한 경로**다. 출처는 `year`와 `day`의 같은 申처럼 위치별로 구분한다. 경로가 존재한다는 사실과 그 경로의 수치가 세력에 이미 들어갔는지는 별도 필드다.

## 제안하는 한 행의 형태

```json
{
  "path_id": "path:background:year:day:branch",
  "source_pillars": ["year"],
  "target": {"pillar": "day", "component": "branch", "stem": null},
  "stage": "pre_relation_background",
  "mechanism": "element_generate",
  "evidence_level": "calculated",
  "accounting_decision": "include",
  "quantity": {"unit": "adjustment_ratio", "value": 0.028735},
  "evidence_refs": [
    {"kind": "interaction", "id": "branch:generate:year:day"}
  ],
  "overlaps_path_ids": [],
  "replaces_path_ids": [],
  "depends_on_path_ids": []
}
```

이 예시는 A의 연 巳→일 未 **기존 일반 生 보정**을 나타낸다. `value`는 표시용 반올림 비율이며 독립 방합 점수나 未의 세력 절대 변화량이 아니다. 실제 집계는 [기존 계산기](../services/branch_dynamics.py)의 반올림 전 조정률과 상한 정책을 따라야 한다.

| 필드 | 의미와 최소 제약 |
| --- | --- |
| `path_id` | 원국 응답 안에서 고유한 경로 ID. 단계·출처 위치·대상 위치/지장간·기전으로 안정적으로 만든다. 지지 글자나 결과 숫자만으로 식별하지 않는다. |
| `source_pillars` | 출처 위치의 정렬된 목록. 보통 한 위치이며, 그룹·반복 출처망은 여러 위치다. **그룹의 참여 목록이지 자동 공격 방향은 아니다.** |
| `target` | `pillar`와 `component: branch | hidden_stem`. 지장간 대상일 때만 `stem`에 해당 지지의 실제 지장간을 넣는다. |
| `stage` | `pre_relation_background`(현재 일반 보정), `structural_context`(방합·입묘 등의 후보 경로), `relation_effect`(충격·손상 등 실제 작용 단계). 단계가 다르면 값의 합산 정책도 다르다. |
| `mechanism` | 생·설기·동기·방합 참여·입묘 후보·충의 지장간 손상 후보 등 경로의 의미. 이름은 유형별 공통 평가기에서 해석하며 조합별 Python 분기를 만들지 않는다. |
| `evidence_level` | `calculated`(현행 코드 관측), `source_interpretation`(교재 서술), `expert_hypothesis`(추후 검증 가설). **코드가 계산했다는 사실은 명리 해석의 검증 완료를 뜻하지 않는다.** |
| `accounting_decision` | `include`(해당 단계의 기준값에 이미 반영), `exclude`(규칙상 차단), `replace`(다른 출처 경로를 대체), `separate_effect`(다른 단계의 독립 작용), `undetermined`(계상 판단 유보). 결정은 **대상별·방향별**로 한다. |
| `quantity` | 계산 가능한 경로면 `unit: adjustment_ratio | power_delta`와 유한한 값. 미계산 경로는 `null`. `adjustment_ratio`와 `power_delta`를 직접 더하지 않는다. |
| `evidence_refs` | `kind: interaction | formation | rule | case`와 ID. 내부 관계·그룹·성립 조합 ID는 실제 출력에 존재해야 하고, 교재 사례 ID는 해석 근거로만 쓴다. |
| `overlaps_path_ids` | 같은 출처를 사용할 **가능성이 있는** 기존 경로. 기록만으로 대체나 합산을 확정하지 않는다. |
| `replaces_path_ids` | `replace`로 확정할 때 실제로 대체하는 기존 경로. 대상·단계의 계상 경계를 확인한 뒤 채운다. |
| `depends_on_path_ids` | 앞 구조가 성립해야 뒤 손상·활용 후보를 판단할 수 있는 경로. **인과 선후 관계**이며 같은 값을 소비한다는 뜻은 아니다. |

`accounting_decision`은 현재 출력의 `activation_status`와 다르다. 예를 들어 충이 `active`여도 충 손실 경로는 `undetermined`와 `quantity: null`일 수 있다. `evidence_level: source_interpretation`도 계산된 `include`로 자동 승격하지 않는다.

## A·D에 대입한 경로 예

아래 예시의 짧은 ID는 읽기 위한 표기다. 실제 구현 시에는 같은 출처·대상에서 기전이 둘 이상인 경우에도 고유한 정형 ID를 사용한다. `null`은 미계산이고, 부호 있는 수치는 [실행으로 확인한 일반 보정](./chouwei_a_d_source_paths.md)만 적었다.

| 사례·경로 | 출처 → 대상 | 단계·기전 | 계상·수치 | 근거와 겹침 |
| --- | --- | --- | --- | --- |
| A `a1` | 연 巳 → 일 未 지지 | 일반 배경 生 | `include`, `adjustment_ratio +0.028735` | `branch:generate:year:day` |
| A `a2` | 시 午 → 일 未 지지 | 일반 배경 生 | `include`, `adjustment_ratio +0.038133` | `branch:generate:day:hour`; 午未합은 `conditional` |
| A `a3` | 연 巳·일 未·시 午의 구조망 → 일 未 지지 | 巳午未 방합 참여 후보 | `undetermined`, `quantity: null` | `group:square:si_wu_wei`, `formation:square:year:day:hour`; `overlaps: [a1, a2]`. 추가 지원이 **있다는 뜻은 아님** |
| A `a4` | 일 未 → 월 丑의 癸 | 축미충 제압 대상 후보 | `undetermined`, `quantity: null` | `branch:clash:month:day`, 교재 A. 지장간 손상은 코드 미계산; `a3`과의 필요 관계도 미확정 |
| D `d1` | 연 申 → 월 丑 지지 | 일반 오행 배경 | `include`, `adjustment_ratio −0.031722` | `branch:generate:year:month`의 위치 쌍. 여기서의 음수는 入墓 효과가 아님 |
| D `d2` | 일 申 → 월 丑 지지 | 일반 오행 배경 | `include`, `adjustment_ratio −0.035254` | `branch:generate:month:day`의 위치 쌍. 같은 申 글자여도 `d1`과 다른 출처 |
| D `d3` | 연·일 두 申의 출처망 → 월 丑 지지 | 入墓·창고 연결 후보 | `undetermined`, `quantity: null` | 교재 D; `overlaps: [d1, d2]`. 현행 관계 ID만으로 入墓를 확정할 수 없음 |
| D `d4` | 월 丑 → 시 未의 乙 | 축미충 제압 대상 후보 | `undetermined`, `quantity: null` | `branch:clash:month:hour`, 교재 D; `depends_on: [d3]`는 교재 경로를 **가설로 기록**한 것이며 코드 결론이 아님 |

`a3`이나 `d3`의 `overlaps`를 **즉시 `replaces`로 바꾸지 않는다.** 구조 경로의 성립·대상·기전이 검증되어야 일반 보정을 유지할지 대체할지 결정할 수 있다. D의 두 申은 별도 배경 출처로 보존하면서, 하나의 入墓 구조망 후보로 연결할 수 있다. 이 구조망을 두 번 합산하거나 이미 음수인 배경값을 임의 양수로 뒤집지 않는다.

D의 `d3`을 실제 형태로 쓰면 다음과 같다. 교재의 구조 설명을 **후보 경로로 보존**하며 적용 수치로 인정하지 않는다.

```json
{
  "path_id": "path:structural:tomb_entry:year:day:month:branch",
  "source_pillars": ["year", "day"],
  "target": {"pillar": "month", "component": "branch", "stem": null},
  "stage": "structural_context",
  "mechanism": "tomb_entry_candidate",
  "evidence_level": "source_interpretation",
  "accounting_decision": "undetermined",
  "quantity": null,
  "evidence_refs": [{"kind": "case", "id": "D"}],
  "overlaps_path_ids": [
    "path:background:year:month:branch",
    "path:background:day:month:branch"
  ],
  "replaces_path_ids": [],
  "depends_on_path_ids": []
}
```

## 집계·검증 불변 조건

1. 한 경로는 정확히 한 대상 지지 또는 지장간을 가리킨다. 같은 위치 쌍의 양방향 보정은 **서로 다른 경로**다.
2. `include`는 계산된 수치와 현재 기준값에 실제 반영된 출처만 사용한다. `undetermined`의 `quantity`는 `null`, `exclude`의 0은 규칙상 차단 근거가 있을 때만 허용한다.
3. 그룹·입묘 후보가 배경 경로와 겹쳐도, `overlaps`는 중복 경고일 뿐 계상 명령이 아니다. `replace`로 확정한 뒤에는 대체된 경로와 새 경로를 같은 단계에서 함께 더하지 않는다.
4. `depends_on_path_ids`는 순환을 허용하지 않는다. 지장간 손상 후보가 구조 후보에 의존해도 구조 후보의 세력은 같은 계산 차례의 손상 결과를 다시 입력받지 않는다.
5. `source_pillars`는 네 실제 기둥 위치를 구분하고, `target.stem`은 대상 지지의 지장간에 속해야 한다. 내부 `evidence_refs`·경로 간 참조는 모두 존재해야 한다.
6. `pre_relation_background`의 비율과 `relation_effect`의 절대 변화량은 서로 다른 단위다. 기존 `effective_power`의 합산·상한을 보존한 뒤, 적용 후 세력을 별도 단계에서 계산한다.
7. 십신·빈주·결과 귀속은 이 경로를 **해석**하는 층위다. 출처·대상 위치를 바꾸거나 세력 비율에 빈주 가중치를 곱하지 않는다.

## v3로 옮기는 순서

1. **완료:** [내부 조립기](../services/branch_influence_paths.py)는 [현행 `surroundings`](../schemas/branch_dynamics_v3.py)의 일반 보정률을 방향별 경로로 옮긴다. 활성 쌍별 구조와 억제되지 않은 그룹의 참여는 `undetermined / null` 후보로 만든다. 새 가산량을 만들지 않는다. 교재 A·D의 입묘·지장간 후보는 생산 규칙에 고정하지 않고 외부 검토 후보로만 받는다.
2. **완료:** [집중 테스트](../tests/test_branch_influence_paths.py)는 A의 巳·午→未 기존 보정과 방합의 겹침, D의 두 申 위치별 음의 보정과 검토 후보, 반복·억제된 그룹, 잘못된 지장간·근거 참조·순환·중복 계상을 검사한다. Python 3.12에서 5건 통과했다.
3. **완료(3.4-draft):** [v3 출력 골격](./branch_dynamics_v3.json)에 중앙 `branch_dynamics.influence_paths[]`와 각 지지의 `influence_path_ids[]`를 추가했다. [계약 검사기](../schemas/branch_dynamics_v3_contract.py)는 대상별 참조의 완전성, 계산된 `effective_power`의 일반 배경 3경로, 기존 `surroundings`와 경로 수치의 일치, 근거 ID를 검증한다. 같은 숫자가 두 보기에 있더라도 **같은 출처의 한 기여**이며 합산 대상 두 건이 아니다. 현재 API와 기존 세력값은 바꾸지 않았다.
4. 구조 경로가 어느 대상에 실제 작용하는지 전문가 사례로 확정된 뒤에만 `replace`·`separate_effect`와 수치 모델을 활성화한다. [작용 후 세력 상태](./branch_dynamics_v3_plan.md)는 미해결 경로가 남으면 `incomplete`·`null`을 유지한다. 기존 `surroundings`와 중앙 경로의 중복 직렬화는 v3 소비자를 확인한 뒤 정리한다.
