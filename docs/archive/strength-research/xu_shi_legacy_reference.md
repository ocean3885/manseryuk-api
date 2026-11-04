# 허실 v1~v3의 이전 README 설명

> 보관 자료. 동주 v4 이전의 관계 자동 제외·변허 설명과 v1 회귀 사례다. 현행 지침은 [통근 영향 분리 계약](../../root_relation_separation.md)을 따른다. 아래 “현행”은 작성 당시를 뜻한다.

#### 4. `xu_shi_dynamics` (허와 실 및 실자변허 實者變虛)
원국의 **동주 통근 점수**와 지지 충·형·천 관계를 이용한 규칙 기반 분석입니다. 다른 기둥 지지의 지원은 `analysis.details[기둥].stem.external_support_*`와 `relation-index`의 천간 상태에서 별도로 확인합니다. `original_status`와 `current_status`는 **같은 원국의 관계 반영 전후**를 뜻하며, 대운·세운에 따른 시기별 변화가 아닙니다. [동주 기준 전환 기록](../../same_pillar_root_migration.md)에 이전 응답과의 차이를 정리했습니다.

| 필드 | 의미 |
| --- | --- |
| `analysis_scope` | `"natal"`: 원국 분석 |
| `rule_version` | 현행 `"3.0.0"`: 동주 통근 점수 양수면 실, 0이면 허투. 명시적 전주 회귀 입력은 `"1.0.0"` |
| `root_scope` | 현행 `"same_pillar_only"`. 기존 회귀 프로필은 `"all_four_branches_weighted"` |
| `pillars` | `year`, `month`, `day`, `hour` 천간별 분석 |
| `shared_roots` | 현행 동주 기준에서는 각 천간의 뿌리가 자기 지지이므로 빈 배열. 기존 전주 회귀 프로필의 공통 뿌리 설명 필드 유지 |
| `impact_groups` | 충·형·천 관계별로 기여도가 제외된 뿌리 위치와 영향을 받은 천간 목록 |
| `real_count` | 관계 반영 후 실(實)인 천간 수 |
| `transformed_empty_count` | 실에서 변허(變虛)로 분류된 천간 수 |
| `hollow_penetrate_count` | 허투(虛透)인 천간 수 |
| `weak_count` | 기존 전주 회귀 프로필의 허(虛) 천간 수. 현행 동주 프로필에서는 항상 0이며, 네 종류의 개수 합은 4 |
| `overall_status` | 실제 상태 분포와 통근에 영향을 준 관계 요약 |

`pillars.*`의 `position`, `char`, `ten_star`, `score`, `original_status`, `current_status`, `is_transformed`, `reason`, `meaning` 필드는 유지하지만 **점수와 상태는 동주 범위 전환으로 달라질 수 있습니다.** [전환 기록](../../same_pillar_root_migration.md)의 세 달력 원국을 참고하세요.

- `score`: 관계 반영 **전 동주 통근 점수**. 위치 가중치를 곱하지 않은 `ROOT_STRENGTH` 계수이며 타주 지원 점수는 합산하지 않습니다. 확률이나 정규화된 0~1 점수가 아닙니다.
- `effective_score`: 관계에 연결된 뿌리를 제외하고 남은 개별 통근 점수의 합.
- `root_evidence`: 뿌리별 `pillar`, `position`, `branch_char`, `score`, `is_affected`, `effective_score`, `interactions`.
- `root_evidence[].interactions`: 해당 뿌리에 영향을 준 충·형·천의 `type`, `name`, `from_pillar`, `to_pillar`, `weight`, `is_adjacent`. 가중치와 인접성은 근거로 공개하지만 v1 감점에는 사용하지 않습니다. 동일 항목은 중복 표시하지 않습니다.
- `root_evidence[].interactions[].relation_id`: 원본 `interactions.matrix`를 참조합니다. 관계 ID가 없는 직접 함수 입력에서는 `null`입니다. `impact_groups[].interaction`도 같은 ID를 제공합니다.
- `transition_reasons`: 최초 분류, 영향 관계, 최종 분류의 이유 목록. 기존 `reason`은 이 목록을 연결한 문장입니다.
- `meaning`: 계산 결과와 구분된 **전통적 상징 해석 참고**. 실제 능력·성과·재정 상태·직업 적합성을 예측하지 않습니다.
- `transition_code`: `maintained`(기존 분류 유지) 또는 `real_to_empty`(실 → 변허). `is_transformed`와 같은 상태 전이 정보를 코드로 제공합니다.
- `root_structure.primary_root_pillars`: 관계 반영 전 개별 기여도가 가장 큰 뿌리 위치. 동점이면 모두 포함하고 뿌리가 없으면 빈 목록입니다.
- `root_structure.remaining_root_pillars`: 관계 반영 후 양의 기여도가 남은 뿌리 위치.
- `root_structure.excluded_root_pillars`: 충·형·천로 기여도가 제외된 뿌리 위치.
- `root_structure.remaining_support`: 현행 동주 프로필에서 잔여 기여도 `none`(0) 또는 `present`(0 초과). 전주 v1 회귀 프로필에만 `below_threshold`(0 초과 0.5 미만), `meets_threshold`(0.5 이상)를 사용합니다. 변화 이력을 포함하는 `current_status`와 구별합니다.

기존 전주 회귀 프로필의 `shared_roots[]`는 `root_pillar`, `branch_char`, `is_affected`, `interactions`, `dependents`를 제공합니다. 현행 동주 기준의 원국 응답에서는 공유 뿌리로 합산하지 않습니다.

`impact_groups[]`는 `interaction`, `affected_root_pillars`, `affected_stem_pillars`를 제공합니다. 같은 관계의 양쪽에 뿌리가 있거나 여러 천간이 연결돼도 위치 목록은 중복 집계하지 않습니다. 이는 기존 근거의 영향 범위를 모은 것으로, 특정 관계 하나가 단독으로 변허를 일으켰다는 판정이나 새로운 감점이 아닙니다.

다음 점수 사례는 **전주 v1 회귀 입력의 참고 기록**이다. 현행 동주 v3에서는 한 천간에 다른 기둥의 뿌리를 합산하지 않는다.

**현행 동주 v3의 허실 판정**

1. 동주 통근 점수가 `0`이면 허투, 양수면 실입니다. 약한 통근도 실로 분류하고 점수로 강도를 별도 표시합니다.
2. 충·형·천에 연결된 동주 뿌리의 기여도를 잠정 규칙에 따라 전부 제외합니다. 실이었으나 잔여 기여도가 `0`이면 변허입니다.
3. 원래 허투인 천간은 타주 지원이 있더라도 허투를 유지합니다. `weak_count`는 현행 프로필에서 `0`입니다.

**전주 v1 회귀 규칙과 한계(아래 전주 예시는 v1 참고)**

1. 원점수가 `0.5` 이상이면 실, `0`이면 허투, 그 사이이면 허입니다.
2. 지지 충·형·천에 참여한 양쪽 지지의 뿌리 기여도를 모두 `0`으로 취급합니다. 관계 유형별 손상률, 거리별 감점, 합에 따른 회복, 파는 반영하지 않습니다.
3. 원래 실이고 영향을 받은 뿌리가 있을 때만 잔여 점수를 검사합니다. `0.5` 미만이면 변허, 이상이면 실을 유지합니다.
4. 원래 허·허투는 분류를 유지합니다. 따라서 원래 허인 천간의 잔여 점수가 `0`이어도 허투나 변허로 바뀌지 않습니다.
5. 원점수와 개별 뿌리 점수는 상위 통근 계산기에서 각각 소수 둘째 자리로 반올림합니다. 이 때문에 뿌리 점수 합과 원점수가 미세하게 다를 수 있습니다. 기존 판정 호환성을 위해 잔여 합산값은 추가 반올림 없이 비교·반환합니다.

**전주 v1 수치·상태 계약의 회귀 기록 (`rule_version: "1.0.0"`)**

내부 통근 계산은 Python `float`를 사용합니다. 총점은 반올림 전 개별 기여도를 합친 뒤 `round(total, 2)`로 반환하고, 뿌리별 점수는 각각 `round(contribution, 2)`로 반환합니다. 허실의 최초 분류는 반환된 총점으로 판정하고, 잔여 점수는 반환된 개별 점수를 년·월·일·시 순서로 합산합니다. epsilon 보정이나 판정 직전 반올림은 적용하지 않습니다. 예를 들어 계산값 `0.49999999999999994`는 `0.5` 미만입니다. 화면에서 소수 자릿수를 줄여 표시하더라도 상태를 표시값으로 재계산하지 않습니다.

| 최초 상태 | 관계 반영 조건 | 최종 상태 | `transition_code` |
| --- | --- | --- | --- |
| 실 | 제외된 뿌리 없음 | 실 유지(잔여 점수로 재분류하지 않음) | `maintained` |
| 실 | 제외된 뿌리 있음, 잔여 점수 ≥ 0.5 | 실 | `maintained` |
| 실 | 제외된 뿌리 있음, 잔여 점수 < 0.5 | 변허 | `real_to_empty` |
| 허 | 관계 유무·잔여 점수와 무관 | 허 | `maintained` |
| 허투 | 관계 유무·잔여 점수와 무관 | 허투 | `maintained` |

전주 v1의 `remaining_support`는 위 전이표와 독립적으로 잔여 점수를 나타냅니다. 따라서 회귀 프로필에서는 `current_status: "허(虛)"`와 `remaining_support: "none"`이 함께 나올 수 있습니다. 현행 동주 v3에서는 `0.5` 임계값을 사용하지 않습니다.

가상 통근 입력에 대한 `pillars.year`의 점수·근거 예시(일부 필드 발췌):

```json
{
  "score": 1.1,
  "effective_score": 0.3,
  "original_status": "실(實)",
  "current_status": "변허(變虛)",
  "is_transformed": true,
  "transition_code": "real_to_empty",
  "root_structure": {
    "primary_root_pillars": ["month"],
    "remaining_root_pillars": ["hour"],
    "excluded_root_pillars": ["month"],
    "remaining_support": "below_threshold"
  },
  "root_evidence": [
    {
      "pillar": "month",
      "position": "월",
      "branch_char": "午",
      "score": 0.8,
      "is_affected": true,
      "effective_score": 0.0,
      "interactions": [
        {
          "type": "충(沖)",
          "name": "子午충",
          "from_pillar": "year",
          "to_pillar": "month",
          "weight": 1.0,
          "is_adjacent": true
        }
      ]
    },
    {
      "pillar": "hour",
      "position": "시",
      "branch_char": "卯",
      "score": 0.3,
      "is_affected": false,
      "effective_score": 0.3,
      "interactions": []
    }
  ]
}
```

허실 회귀 테스트는 프로젝트 루트에서 실행합니다(의존성이 설치된 Python 3.12 환경):

```bash
python -m unittest discover -s tests -v
```

`tests/fixtures/xu_shi_v1.json`은 변경 전 함수로 확보한 합성 간지 입력 16건의 점수·상태·개수 기준값입니다. 테스트는 이 기준값 외에도 허투·허·실, 잔여 점수 `0.5` 및 인접 float 경계, 총점과 뿌리별 반올림 차이, 공통 뿌리와 서로 다른 잔존 기반, 동점 주요 뿌리, 중첩 관계, 반복 지지, 응답 스키마를 검증합니다. 통합 테스트는 달력 DB를 읽기 전용으로 열어 `1990-01-01 12:00`, 기존 빈주 오류 사례 `1995-05-12 14:30`의 라우터 결과·응답 스키마·상담 프롬프트를 검증합니다.

