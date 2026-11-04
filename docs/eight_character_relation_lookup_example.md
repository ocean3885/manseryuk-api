# 실제 원국으로 비교한 8글자 관계 조회

검토일: 2026-11-03. 원국 **`乙巳 · 己丑 · 己未 · 庚午`**(연·월·일·시)를 사용했다. 앞서 A라고 부른 교재 원국이지만, 여기서는 축미충의 해석·세력 계산을 검토하지 않는다. [현재 API 조립 경로](../services/saju_orchestrator.py)가 호출하는 [글자별 분석](../services/analysis.py), [관계 매트릭스](../services/interaction_matrix.py), [지지 계산기](../services/branch_dynamics.py)를 프로젝트 Python 3.12에서 직접 실행하고 [v3 지지 부분 조립기](../services/branch_dynamics_v3_assembler.py)의 관계 ID와 대조했다. HTTP API 자체를 호출한 검증은 아니다.

## 현재 실제 출력에서 확인한 관계

`advanced_analysis.interactions.matrix`에 대응하는 매트릭스의 **전체 여섯 항목**은 다음과 같다. 관계 ID는 현행 매트릭스의 원문 ID다.

| 관계 ID | 참여 기둥 | 성립 상태 | 확인할 점 |
| --- | --- | --- | --- |
| `지지:공합(拱合):巳丑공합:year,month` | 연지 巳·월지 丑 | `candidate_only` | 독립 작용 확정이 아님 |
| `지지:충(沖):丑未충:month,day` | 월지 丑·일지 未 | `active` | 충 성립 사실. 피해량은 별개 |
| `지지:천(穿):丑午천:month,hour` | 월지 丑·시지 午 | `active` | 천 성립 사실 |
| `지지:육합(六合):未午합:day,hour` | 일지 未·시지 午 | `conditional` | `external_adjacent_clash`가 이유로 기록됨 |
| `천간:천간합(天干合):乙庚합:year,hour` | 연간 乙·시간 庚 | 상태 필드 없음 | 합화 오행은 후보. 성립 완료로 해석할 수 없음 |
| `지지:방합(方合):방합 여름火:year,day,hour` | 연지 巳·일지 未·시지 午 | `potential` | 세 위치를 잇는 그룹 후보 |

반면 `analysis.details`에 대응하는 [글자별 분석](../services/analysis.py)에는 연간 **乙→월간 己**, **乙→일간 己**의 두 극 관계가 각각 위치별로 있다. 매트릭스는 [천간 극 탐지 함수](../services/stem_relations.py)를 import하지만 호출하지 않으므로 이 두 관계의 중앙 ID는 없다. 같은 己라도 월간과 일간은 다른 대상이다. 이 원국에서 동주 자합 `jahab`은 네 기둥 모두 `null`이다. 자합이 있는 원국에서는 이 값이 글자별 분석에 따로 나타난다.

[v3 지지 부분 조립](../services/branch_dynamics_v3_assembler.py)은 매트릭스의 지지 관계를 `branch:clash:month:day`, `branch:pierce:month:hour`, `branch:combine:day:hour`, `group:square:si_wu_wei` 같은 별도 ID로 옮기고, 매트릭스에 없던 지지 대표 오행의 生 후보도 만든다. 예를 들어 `branch:generate:year:day`는 `potential`, `branch:generate:month:hour`는 활성 丑午천 때문에 `suppressed`다. 따라서 기존 매트릭스 ID와 v3 ID를 같은 관계라고 **문자열 그대로 비교할 수 없다**.

## 글자에서 관계를 찾을 때의 현재 경로

| 조회 대상 | 지금 필요한 조회 | 번거로운 점 |
| --- | --- | --- |
| 연간 乙 | 매트릭스에서 연간–시간의 합을 찾고, 글자별 분석에서 월간·일간을 극하는 두 위치를 찾음 | 천간극은 매트릭스 ID·공통 상태가 없음 |
| 월간 己 / 일간 己 | 각자의 `analysis.details`에서 `restrain_me`를 읽음 | 같은 己를 글자만으로 묶으면 두 관계의 대상을 구별할 수 없음 |
| 월지 丑 | 매트릭스의 공합·충·천, 지지 쌍 결과의 生/極/동기를 따로 찾음 | 다른 출력 경로의 ID·성립 상태를 연결해야 함 |
| 일지 未 | 매트릭스의 충·조건부 육합·방합 참여, 지지 쌍의 生 관계를 따로 찾음 | 그룹 참여를 특정 쌍의 관계로 복사하면 구조를 중복 기록함 |
| 시지 午 | 매트릭스의 천·조건부 육합·방합 참여를 찾음 | 午가 관계의 참여자인 것과 午가 힘을 주거나 받는 것은 서로 다른 정보 |

현행 `analysis.details[기둥].branch.relations`와 `.stem.relations`는 글자 기준 조회를 일부 제공하지만, [매트릭스](../services/interaction_matrix.py)를 **다시 참조해 만든 목록이 아니라 별도 탐지 결과**다. 독립 탐지 결과를 합칠 때 같은 관계의 ID·상태가 항상 일치한다는 계약은 없다.

## 권장 조회 방식: 관계 본문 한 곳, 글자별 위치 참조

아래는 **출력 제안의 일부를 보여 주는 예시**다. 현행 API 응답이 아니며, 이 네 항목 외에도 위 표의 나머지 관계와 동주 관계를 기록해야 한다. `stem:control:*` ID와 `year.stem` 같은 글자 ID는 제안 표기다. `branch:*` ID는 현재 v3 부분 조립의 표기를 사용했다.

**후속 계약:** 현재 `GET /relation-index`의 [정식 조회 형태](character_relation_index_contract.md)는 아래 부분 예시와 달리 `coverage`·천간별 `stem_state`를 필수로 포함하며, 지장간 투출 관계도 기록한다. 버전은 `1.3-draft`다.

```json
{
  "relations": [
    {
      "id": "stem:control:year:month",
      "type": "control",
      "participants": ["year.stem", "month.stem"],
      "direction": {"from": "year.stem", "to": "month.stem"},
      "activation_status": "detected",
      "effect_calculation_status": "not_calculated"
    },
    {
      "id": "stem:control:year:day",
      "type": "control",
      "participants": ["year.stem", "day.stem"],
      "direction": {"from": "year.stem", "to": "day.stem"},
      "activation_status": "detected",
      "effect_calculation_status": "not_calculated"
    },
    {
      "id": "branch:clash:month:day",
      "type": "clash",
      "participants": ["month.branch", "day.branch"],
      "direction": null,
      "activation_status": "active",
      "effect_calculation_status": "not_calculated"
    },
    {
      "id": "group:square:si_wu_wei",
      "type": "square",
      "participants": ["year.branch", "day.branch", "hour.branch"],
      "direction": null,
      "activation_status": "potential",
      "effect_calculation_status": "not_calculated"
    }
  ],
  "character_relation_ids_example": {
    "year.stem": ["stem:control:year:month", "stem:control:year:day"],
    "month.stem": ["stem:control:year:month"],
    "day.stem": ["stem:control:year:day"],
    "hour.stem": [],
    "year.branch": ["group:square:si_wu_wei"],
    "month.branch": ["branch:clash:month:day"],
    "day.branch": ["branch:clash:month:day", "group:square:si_wu_wei"],
    "hour.branch": ["group:square:si_wu_wei"]
  }
}
```

이 예시에서 네 지지·네 천간 모두 **위치별 조회 항목**을 갖는다. 빈 목록은 이 예시에 고른 네 관계에는 참여하지 않는다는 뜻이며, 그 글자에 다른 실제 관계가 없다는 뜻이 아니다. 정식 출력에서는 `relation_ids`를 **중앙 관계 목록 전체에서 자동으로 만들어야** 한다. 연지와 일지의 방합 참여를 두 그룹으로 복사하지 않으며, 연간 乙→월간 己와 乙→일간 己를 하나로 합치지 않는다.

`activation_status`는 글자 조합의 성립·후보 사실, 제안된 `effect_calculation_status`는 실제 세력 변화 계산의 완료 여부다. 예시의 천간극 `detected`는 현재 규칙표에서 쌍을 찾았다는 뜻만 담는다. 위 충의 `active`도 피해량 확정을 뜻하지 않는다. 근거 규칙 ID·조건 이유는 정식 계약에서 **원본에 있는 값을 옮기거나 미정으로 표시**해야 하며, 이 예시가 생성하지 않는다.

## 출력 결정을 위한 비교 결론

1. **새로운 풍부한 관계 본문을 기존 매트릭스·v3 쌍 결과와 나란히 중복 발행하지 않는다.** 첫 구현은 기존 매트릭스를 탐지 원천으로 쓰고, 누락된 천간극·동주 관계·지지 생극을 출처가 분명한 항목으로 보강하는 방향이 단순하다. v3 지지 관계는 이미 정형 ID와 상태를 갖고 있으므로, 버전 간 ID 대응 관계를 정의해야 한다.
2. **글자별 조회는 참조를 계산해서 만드는 뷰다.** 전체 `relations`에서 참여 글자 ID를 읽어 역색인을 만들 수 있다. 소비자가 매번 역색인을 만들기 어렵다는 실제 요구가 확인되면 `character_relation_ids`를 직렬화하되, 동일 본문을 여덟 번 복제하지 않는다.
3. **ID·상태의 단일 계약을 먼저 정한다.** 지지 v2 매트릭스 ID와 v3 지지 ID, 새 천간극·동주 자합 ID를 어떤 네임스페이스로 묶을지 정해야 한다. 천간합·충에 없는 성립 상태를 임의 `active`로 채우지 않는다.
4. **1단계 완료 범위는 탐지·참조 정합성이다.** 후속 세력 산식, 조합별 주도, 특정 지장간 피해와 빈주 귀속은 여기서 계산하지 않는다.

**다음 구현 단위:** 이 비교를 바탕으로 8글자 관계 조회의 최소 계약을 확정한다. 중앙 본문에 필요한 필드, ID 변환, 성립 상태의 출처/미정 표기, 글자별 참조 생성·검증을 정하고 현행 API와 v3 초안 중 연결 시점을 정한다. 수치화 코드는 수정하지 않는다.
