# 지지별 작용 후 세력 집계 추적 계약

> **보관 자료 / 중단 연구 기록** — 이 문서의 개발 순서·다음 작업·계수 제안은 현행 지침이 아닙니다. 2026-11-04 기준 자료를 보존하며, 현재 작업은 [현행 문서 목록](../../README.md)을 따릅니다. 명시적 요청 없이 수치 계산·손상률 연구를 재개하지 않습니다.

상태: **설계안 + 내부 추적 골격**. [작용 후 세력 완성 조건](../../branch_post_effect_completeness.md)의 두 번째 관문인 ‘숫자의 전체 집계 근거’를 정의한다. [내부 조립기](../../../services/branch_post_effect_gate.py)는 현재 출처 경로·차단 근거만 연결한다. [v3 출력 골격](branch_dynamics_v3.json)의 `post_effect_power`는 계속 `null / not_calculated`이며, 새 수치·규칙·API 필드는 발행하지 않는다.

## 집계의 시작점을 정한다

지지별 집계는 `branch_strengths[대상].after_stem_power`를 **참조**하는 단계에서 시작한다. 월령·지장간·동주 천간까지 반영한 값이다. 그다음 출처별 일반 배경 경로를 선택·제외·대체하고, 필요한 구조 기여와 관계 적용량을 각각 한 번씩 처리한다.

현재 `effective_power`는 일반 배경 비율들의 합에 상한 `−0.35 ~ +0.35`를 적용한 값이다. [기존 계산기](../../../services/branch_dynamics.py)는 출처별 비율을 표시할 때 반올림도 한다. 따라서 기존 `effective_power`에서 **표시된 비율만 역산해 빼고** 새 방합 배율을 더하는 방식은 정확한 재계산 경로가 아니다. `effective_power`는 잠정 출력과 비교하는 기준선으로 남기고, 대체가 필요한 최종 집계는 반올림 전 경로값·상한 정책을 바탕으로 다시 계산해야 한다.

쌍별 `power_before`는 관계 상대를 제외한 **관계별 비교 입력**이다. 같은 지지라도 상대가 바뀌면 값이 달라질 수 있으므로 네 지지의 공통 집계 시작값으로 사용하지 않는다. 子午충의 잠정 손실량 역시 이 관계별 세력을 사용해 산출됐으므로, 여러 다른 작용과 합칠 때의 기준 세력·배분 정책을 별도로 검증해야 한다.

## 최소 추적 자료

한 지지의 `post_effect_trace`를 아래 형태로 제안한다. 실제 v3 스키마에 추가하기 전까지는 **내부 골격의 예시**다. 현재 v3 출력에는 추적 필드가 없으며, 지지별 최종 수치는 `null`이다.

```json
{
  "status": "not_calculated",
  "readiness_status": "incomplete",
  "input_power_ref": "branch_strengths.day.after_stem_power",
  "background": {
    "included_path_ids": ["path:background:year:day:branch"],
    "excluded_path_ids": [],
    "replacement_sets": []
  },
  "reconciled_pre_effect_power": null,
  "applied_effect_refs": [],
  "available_provisional_interaction_ids": [],
  "aggregation_formula_id": null,
  "rounding_policy_id": null,
  "model_scope": {
    "profile_id": "mangpa_project_provisional",
    "coverage_status": "not_assessed",
    "unmodeled_mechanism_ids": []
  },
  "unresolved_refs": [
    {"ref_id": "branch:clash:month:day", "reason": "relation_effect_unresolved"}
  ]
}
```

이 예시는 **집계가 완성된 값이 아니다.** `included_path_ids`는 현행 잠정 기준값에 이미 들어간 일반 배경 경로의 일부를 보여주는 가상 입력이며, 최종 재계산의 채택 결정은 아니다. 실제 [내부 추적 골격](../../../services/branch_post_effect_gate.py)은 대상 지지의 모든 기존 일반 배경 경로를 포함·제외 목록으로 채운다. `reconciled_pre_effect_power`, 공식 ID, 반올림 정책 및 적용 효과가 정해지기 전에는 `post_effect_power`를 계산하지 않는다.

| 필드 | 필요한 이유와 검증 조건 |
| --- | --- |
| `status`·`readiness_status` | 내부 골격의 `status`는 현재 항상 `not_calculated`다. `readiness_status`는 알려진 차단 근거가 있으면 `incomplete`, 없으면 `no_known_blockers`다. 후자도 모델 범위나 집계 완료를 뜻하지 않는다. v3의 `post_effect_status`와 혼동하지 않는다. |
| `input_power_ref` | 해당 지지의 `after_stem_power`를 가리킨다. 수치를 다른 곳에 복사해 별도 기준값으로 만들지 않는다. |
| `background.included_path_ids` | **현재 `effective_power`에 이미 사용한** 일반 배경 경로. 각 경로의 단위는 `adjustment_ratio`이며 대상 지지가 같아야 한다. 향후 대체 결정이 나면 재계산 목록을 별도로 확정한다. |
| `background.excluded_path_ids` | 규칙상 차단하거나 구조로 대체해 일반 보정에서 뺀 경로. 기존 경로의 `exclude`와 이후 집계에서 결정한 제외를 구분할 근거 ID가 있어야 한다. |
| `background.replacement_sets` | `{replacement_path_id, replaced_path_ids}`의 목록. 구조 경로가 무엇을 대신하는지 명시한다. 대체된 경로는 포함 목록에 동시에 남길 수 없다. `overlaps_path_ids`만으로 대체를 확정하지 않는다. |
| `reconciled_pre_effect_power` | 선택된 배경 경로와 검증된 구조 기여를 처리한 **관계 적용 전** 지지 세력. 미계산 기여가 있으면 `null`이다. 일반 배경의 상한·반올림은 공식 ID에 맞춰 재현해야 한다. |
| `applied_effect_refs` | 쌍별 `directional_effects`·`self_effects` 또는 검증된 구조 경로의 **기존 적용량**을 가리킨다. 같은 관계의 공격 소모와 자기 손실을 다른 이름으로 두 번 인용하지 않는다. |
| `available_provisional_interaction_ids` | 子午충처럼 잠정 적용량이 **관계에는 존재하지만 최종 집계에는 아직 사용하지 않은** ID. 현재 내부 골격은 `applied_effect_refs: []`를 유지한다. |
| `aggregation_formula_id` | 여러 적용량을 어떤 순서·규칙으로 집계하는지 식별한다. 단순 합산을 암묵적 기본값으로 쓰지 않는다. |
| `rounding_policy_id` | 단계별 소수 처리와 잔차 배분을 식별한다. 소수 4자리 출력이 실제 정확도의 증거는 아니다. |
| `model_scope` | 적용한 규칙 프로필과 이 원국에서 검토한 기전의 범위. `coverage_status: not_assessed | partial | reviewed`를 구분하고, 알려진 미지원 기전을 명시한다. `reviewed`도 학파 전체의 완전성을 뜻하지 않는다. |
| `unresolved_refs` | [차단 근거 수집기](../../../services/branch_post_effect_gate.py)의 지지별 `{ref_id, reason}` 및 아직 탐지하지 못한 기전의 검토 결과. 하나라도 남으면 최종 숫자는 `null`이다. |

`applied_effect_refs`의 최소 단위는 **관계 ID만이 아니다.** 子午충 한 관계에는 午의 방향별 충격과 子의 자기 손실이 따로 있으므로 다음처럼 정확한 항목을 가리켜야 한다.

```json
{"kind": "directional", "relation_id": "branch:clash:year:month",
 "from_pillar": "year", "to_pillar": "month"}
{"kind": "self", "relation_id": "branch:clash:year:month", "pillar": "year"}
{"kind": "path", "path_id": "path:structural:example"}
```

각 참조는 존재하는 적용량 하나만 가리키며, 그 적용량의 대상은 추적 중인 지지여야 한다. 구조 경로를 `path`로 참조하려면 `quantity.unit: power_delta`와 계상 결정이 확정돼야 한다. 보정 버전은 참조한 [관계의 `metrics`](../../../schemas/branch_dynamics_v3.py) 또는 경로 근거에서 추적한다. 임상으로 검증되지 않은 `ziwu_clash_0.1` 같은 값이 하나라도 포함되면 완성된 추적의 상태는 최대 `provisional`이다.

## 상태별 발행 조건

| `post_effect_status` | 추적 조건 | 출력 |
| --- | --- | --- |
| `not_calculated` | 집계기를 실행하지 않음. 현재 상태 | `post_effect_trace: null`, `post_effect_power: null` |
| `incomplete` | 집계를 시도했지만 출처 대체·관계 효과·모델 적용 범위 중 적어도 하나가 미정 | 추적에는 알고 있는 선택·차단과 `unresolved_refs`를 기록. 숫자는 `null` |
| `provisional` | 모든 관련 경로와 작용이 계상되고 범위를 검토했으나 사용한 모델·계수가 잠정 | 공식·반올림·참조·합계가 재현되는 **잠정 숫자**와 근거 |
| `resolved` | 위 조건에 더해 적용 규칙과 기여가 검증 상태이고 미지원 기전이 없음 | 공식·참조·합계가 재현되는 숫자와 근거 |

현행 [계약 검사기](../../../schemas/branch_dynamics_v3_contract.py)가 숫자 상태를 모두 거부하는 정책은 **수치를 재현할 수 있는 집계 추적이 생성되고 검증될 때까지 유지**한다. 내부 골격은 출처 ID와 차단 근거만 만들며 숫자 집계의 증빙이 아니다. `unresolved_refs`가 비어 있어도 공식·반올림·모델 범위가 빠졌다면 `provisional` 또는 `resolved`로 승격할 수 없다.

## A·D에 적용하면

| 원국·대상 | 현재 추적할 수 있는 출처 | 숫자를 막는 항목 |
| --- | --- | --- |
| A `乙己己庚 / 巳丑未午`의 일 未 | 巳→未·午→未 일반 生은 [출처 장부](chouwei_a_d_source_paths.md)에 이미 계상. 丑→未의 동기 보정도 현행 `effective_power`에 있음 | 丑未충과 巳午未 방합의 구조 효과, 일반 生의 유지/대체 여부, 지장간 피해가 미정. `reconciled_pre_effect_power`와 `post_effect_power` 모두 확정 불가 |
| D `庚己丙乙 / 申丑申未`의 월 丑 | 연·일 두 申→丑의 일반 보정은 별도 경로로 이미 계상. 시 未→丑 동기 보정도 있음 | 丑未충 효과와 申入丑庫의 미탐지 기전. `model_scope.unmodeled_mechanism_ids`에 入墓 검토 필요성을 남겨야 함 |

두 원국에서 `effective_power`와 쌍별 `power_before`가 이미 숫자라는 사실은 최종 집계의 완료 근거가 아니다. A의 방합 가산률이나 D의 반복 申 배율을 임의로 넣어 trace의 빈칸을 채우지 않는다.

## 다음 구현 단계

1. **완료:** `not_calculated`용 [내부 추적 골격](../../../services/branch_post_effect_gate.py)은 중앙 경로 ID와 차단 근거를 참조하고, 알려진 누락 기전을 선택 입력으로 표시한다. `readiness_status: incomplete`와 `no_known_blockers`를 구분하지만 새 숫자·공식 ID는 만들지 않는다. [집중 테스트](../../../tests/test_branch_post_effect_gate.py) 7건이 Python 3.12에서 통과했다.
2. **완료:** [주변 보정 재생 검증](../../branch_ambient_replay_audit.md)에서 현행 일반 보정의 소수 6자리 표시 전 값, 출처 합산, 상한과 최종 소수 4자리 반올림을 재생했다. 이어 선택한 현재 일반 배경 경로 ID만으로 같은 계산을 재생하는 진단 함수를 검증했다. 출처의 `after_stem_power`는 이미 4자리 값이며, 표시용 비율을 역산 입력으로 쓰지 않는다. 실제로 어떤 경로를 대체할지는 전문가 사례의 해석 기준을 먼저 확정한다.
3. 모델 적용 범위와 누락 기전의 검토가 가능해진 뒤, 한 지지의 모든 경로를 계상하는 계산기와 등식 검사를 추가한다. 그때 v3 출력 필드·스키마 버전을 결정하고 숫자 상태의 차단을 해제한다.
