# 원국 8글자 관계 조회 최소 계약

> 현행 조회 스키마는 `1.7-draft`, 허실 원본 규칙은 `4.0.0`입니다. `stem_state.root_impact_status=not_evaluated`, `root_impact_score=null`이며 관계로 인한 자동 점수 제외는 하지 않습니다. 관계는 중앙 목록 및 지지 글자의 `relation_ids`에서 조회합니다. 아래 이전 버전의 손상·변허 설명보다 [현행 계약](root_relation_separation.md)을 우선합니다.

작성일: 2026-11-03. [탐지 구현 현황](interaction_detection_implementation_audit.md)과 [실제 원국 조회 비교](eight_character_relation_lookup_example.md)를 바탕으로 만든 **탐지 단계의 독립 계약**이다. [계약 모델](../schemas/character_relation_index.py)과 [읽기 전용 조립기](../services/character_relation_index.py)를 마련했다. 현재 별도 `GET /relation-index` 경로에서 제공한다. 기존 통근 점수·허실 상태는 출처와 함께 읽어오지만 관계별 새 세력 변화량·손상량·빈주 귀속은 계산하지 않는다.

## 자료 형태와 조회 방식

```json
{
  "schema_version": "1.6-draft",
  "characters": {
    "year.stem": {"char": "乙", "relation_ids": ["stem:control:year:month"], "stem_state": {"original_status": "허투(虛透)", "current_status": "허투(虛透)", "root_score": 0.0, "has_same_pillar_root": false, "remaining_score": 0.0, "root_branch_ids": [], "affected_root_branch_ids": [], "external_support_score": 0.21, "external_support_branch_ids": ["day.branch"], "source_rule_version": "3.0.0", "root_scope": "same_pillar_only", "validation_status": "provisional"}},
    "year.branch": {"char": "巳", "relation_ids": []},
    "month.stem": {"char": "己", "relation_ids": ["stem:control:year:month"], "stem_state": {"original_status": "실(實)", "current_status": "변허(變虛)", "root_score": 0.2, "has_same_pillar_root": true, "remaining_score": 0.0, "root_branch_ids": ["month.branch"], "affected_root_branch_ids": ["month.branch"], "external_support_score": 1.3, "external_support_branch_ids": ["year.branch", "day.branch", "hour.branch"], "source_rule_version": "3.0.0", "root_scope": "same_pillar_only", "validation_status": "provisional"}},
    "month.branch": {"char": "丑", "relation_ids": []},
    "day.stem": {"char": "己", "relation_ids": [], "stem_state": {"original_status": "실(實)", "current_status": "변허(變虛)", "root_score": 1.0, "has_same_pillar_root": true, "remaining_score": 0.0, "root_branch_ids": ["day.branch"], "affected_root_branch_ids": ["day.branch"], "external_support_score": 0.84, "external_support_branch_ids": ["year.branch", "month.branch", "hour.branch"], "source_rule_version": "3.0.0", "root_scope": "same_pillar_only", "validation_status": "provisional"}},
    "day.branch": {"char": "未", "relation_ids": []},
    "hour.stem": {"char": "庚", "relation_ids": [], "stem_state": {"original_status": "허투(虛透)", "current_status": "허투(虛透)", "root_score": 0.0, "has_same_pillar_root": false, "remaining_score": 0.0, "root_branch_ids": [], "affected_root_branch_ids": [], "external_support_score": 0.28, "external_support_branch_ids": ["year.branch", "month.branch"], "source_rule_version": "3.0.0", "root_scope": "same_pillar_only", "validation_status": "provisional"}},
    "hour.branch": {"char": "午", "relation_ids": []}
  },
  "relations": [
    {
      "relation_id": "stem:control:year:month",
      "type": "control",
      "participants": ["year.stem", "month.stem"],
      "activation_status": "detected",
      "status_reason": null,
      "direction": {
        "from_character": "year.stem",
        "to_character": "month.stem",
        "basis": "elemental"
      },
      "candidate_element": null,
      "formation_candidates": [],
      "rule_ids": [],
      "source_refs": [{"system": "analysis_details", "location": "analysis.details.year.stem.relations.restrain"}]
    }
  ],
  "coverage": {
    "rule_scope": "registered_rules_partial",
    "transmission_basis": "jijanggan_detailed_exact_match",
    "detected_only_relation_ids": ["stem:control:year:month"],
    "not_evaluated_mechanisms": [
      "stem_generate", "stem_same_element", "cross_pillar_stem_branch_element",
      "general_hidden_stem_damage", "tomb_entry"
    ],
    "power_effects_included": false
  }
}
```

이 예시는 **한 관계의 구조를 설명하는 부분 자료**다. 실제 `乙巳·己丑·己未·庚午` 원국의 관계 전부가 아니다. 그 원국의 실제 연간 乙→일간 己도 추가해야 하며, 다른 글자의 빈 목록은 전체 분석에서 관계가 없다는 뜻이 아니다. 정식 생성기는 중앙 `relations[]`를 만든 뒤 각 참여 글자의 `relation_ids[]`를 역산해야 한다. 글자별 딕셔너리에서 관계를 다시 탐지·복사하지 않는다.

### 필드 의미

| 필드 | 이 단계의 뜻과 검증 |
| --- | --- |
| `schema_version` | 독립 조회 계약의 버전 `1.6-draft`. 동주 통근 여부·무가중 점수와 타주 가중 지원을 분리. 동주 양의 통근은 점수 크기에 관계없이 실로 표시. 지지 v3·현행 API 버전과 혼합하지 않음 |
| `characters` | `year/month/day/hour × stem/branch` 정확히 8개. 실제 천간/지지 한 글자와 중앙 관계 ID 참조 목록. 같은 글자도 위치별로 별개 |
| `characters[천간].stem_state` | 동주 기준 허실의 `original_status / current_status`, 위치 가중치 없는 통근 원점수/잔여점수, 명시적 `has_same_pillar_root`, 동주 뿌리, 별도 `external_support_score / external_support_branch_ids`, 규칙 버전과 `root_scope: same_pillar_only`. 지지 글자에는 `null`. `provisional`은 임시 계수·뿌리 영향 모델의 상태 |
| `relations[].relation_id` | 한 원국 안의 유일한 관계 ID. 쌍·동주 관계는 유형과 위치로 구성; 그룹은 기존 v3 그룹 ID를 재사용할 수 있음 |
| `type`·`participants` | `stem`/`branch` 쌍은 해당 종류 두 글자, `same_pillar`는 같은 기둥의 간·지, `group`은 지지 3~4개. 참여 순서는 연·월·일·시 |
| `activation_status`·`status_reason` | 탐지·후보·성립·조건부·억제 사실. 조건부·억제는 이유 필수. 이 상태는 실제 영향량의 완성 여부가 아님 |
| `direction` | 규칙이나 오행에서 방향이 **확인될 때만** 출처·대상 및 `elemental/rule_fixed` 근거 종류를 기록. 미판정은 `null`; 세력 우세를 방향으로 복사하지 않음 |
| `candidate_element` | 합의 후보 오행 등. 실제 합화 판정이나 작용량은 아님 |
| `hidden_stem` | `cross_layer:transmission:*`에서만 투출된 실제 지장간 글자. 대상 천간 글자와 같아야 함 |
| `formation_candidates` | 그룹에 참여하는 실제 위치별 세 글자 조합. 같은 지지의 반복으로 조합이 둘이면 두 조합 모두 기록 |
| `rule_ids`·`source_refs` | 확인된 규칙 ID와 기존 매트릭스·지지 계산·v3·글자별 분석의 출처. 없는 규칙 ID는 빈 배열로 두고 새 ID를 꾸미지 않음 |
| `coverage` | `registered_rules_partial` 범위, `detected` 상태인 관계 ID, 현재 평가하지 않는 기전 목록, 실제 세력 작용량 미포함 사실. 관계 본문과 ID 목록의 일치를 검사 |

`activation_status`는 기존 지지 v3의 `detected / candidate_only / potential / conditional / suppressed / active`만 사용한다. **천간합·충의 현재 매트릭스 항목에는 상태가 없으므로 `detected`로 옮긴다.** 이는 성립 확정이 아니라 후보 탐지 사실이다. 현재 규칙표의 천간극도 `detected`이며 방향은 극하는 쪽에서 극당하는 쪽으로 기록한다. 동주 일반 오행 관계는 존재 사실을 `detected`로 표시한다. 동주 자합은 [자합 판정기](../services/relations.py)의 실제 `active`·조건 미충족·충 차단을 근거로 `active / conditional / suppressed`로 대응한다. 자합 후보가 없는 동주는 관계 항목을 만들지 않는다. 현재 조립기는 이 대응을 실제 입력과 대조한다.

`coverage.rule_scope: registered_rules_partial`은 **등록된 규칙에 한정한 부분 탐지**라는 뜻이다. `detected_only_relation_ids`는 해당 원국의 관계 본문에서 상태가 `detected`인 ID를 정확히 나열한다. 천간합·충·극, 동주 오행, 투출, 동지 사실 등이 여기에 들어갈 수 있다. `not_evaluated_mechanisms`는 **원국에서 실제 발생했다고 판정한 목록이 아니라** 현 프로필에서 일반적으로 평가하지 않는 기전의 고정 목록이다. 현재는 천간 간 生·동기, 다른 기둥 천간↔지지의 **대표 오행 직접 작용**, 일반 지장간 손상, 入墓다. 지장간의 정확한 글자 일치에 따른 투출은 별도로 탐지한다. `transmission_basis`는 그 판정이 [상세 지장간 표](../services/constants.py)에 기초함을 표시한다. `power_effects_included: false`는 관계별 실제 세력 변화량을 싣지 않음을 명시한다. `stem_state`의 기존 허실 점수는 이 변화량과 다르다.

## 투출과 통근·허실의 분리

[120개 천간·지지 조합의 교차 대조](transmission_rooting_alignment_audit.md)에서 글자 일치만 3쌍, 통근 인정만 16쌍을 확인했다. 네 통제 원국의 `relation-index`에서도 투출 관계와 허실 원상태가 서로 다른 판정으로 유지된다.

[불일치 19쌍 규칙 검토](root_strength_rule_review.md)는 통근만 인정한 16쌍이 모두 **같은 오행의 다른 지장간 글자**를 갖고, 글자 일치만 한 3쌍이 모두 **戊 초기 `7/30`**임을 확인했다. 이는 코드 자료의 분류이지 각 계수의 승인 근거가 아니다. [동주 기준 전환](same_pillar_root_migration.md)에 따라 현재 허실은 동주 지지로 판정하며 타주 지원은 별도 값이다.

- [기존 투출 판정](../services/analysis.py)은 지지의 지장간과 원국 네 천간의 **동일 글자**를 대조한다. 반복된 천간을 `all_stems.index()`로 첫 위치에만 연결하던 문제를 고쳐 **모든 일치 위치**를 기록한다. 지지의 `jijanggan`, `transmitted`, `hidden`은 이제 [지지 세력 계산](../services/branch_dynamics.py)이 사용하는 `JIJANGGAN_DETAILED`의 글자·초기/중기/정기 표기를 함께 사용한다.
- 기존 `ZHI_ZANG`에는 없지만 상세표에는 들어 있는 글자는 **子의 壬, 卯의 甲, 午의 丙, 酉의 庚, 亥의 戊**다. 이 다섯 지지에서 새 투출 후보·기존 원국 응답의 지장간 목록이 달라질 수 있다. 상세표를 프로젝트 내부 기준으로 택한 것이며 학파 전체의 지장간 체계를 검증한 것은 아니다. 응답의 `coverage.transmission_basis`가 적용 표를 드러낸다.
- 투출 관계 `cross_layer:transmission:<지지 위치>:<천간 위치>`는 지지 전체가 해당 천간에 힘을 주었다는 뜻이 아니라, **그 지지의 특정 지장간 글자가 천간에 드러난 사실**이다. `hidden_stem`·출처 지지·대상 천간·원본 분석 위치를 기록한다. 예를 들어 `乙巳·己丑·己未·庚午`의 일지 未 속 己는 **월간 己와 일간 己의 두 위치**를 각각 가리킨다.
- [현재 통근 계산](../services/analysis.py)은 `ROOT_STRENGTH`의 **동주 지지 계수 자체**를 통근 점수로 쓰고, 다른 지지의 기존 위치·거리 가중 지원은 `external_support_*`에 둔다. [허실 분석](../services/xu_shi.py) v3은 동주 원점수 `0`을 허투, 양수는 실로 분류한다. **활성** 충·천·형이 동주 뿌리에 닿아 계산상 잔여 기여도가 `0`이 되면 변허를 표시한다. 격위 자형의 `candidate_only`는 뿌리 영향에서 제외한다. 따라서 **투출 관계 유무, 동주 통근, 타주 지원은 별도 사실**이다. `stem_state.validation_status: provisional`은 계수·전근 제외가 임상 확정 모델이 아님을 표시한다.
- 조회 조립기는 [기존 허실 결과](../services/xu_shi.py)의 네 천간 상태를 글자별 `stem_state`에 옮기며, 원국·통근 근거로 재계산한 값과 다르면 거부한다. 지지 글자의 `stem_state`는 `null`이다. 다음 단계의 새 수치 모델이 검증되기 전에는 이 상태를 관계별 손상량이나 지지 최종 세력으로 합산하지 않는다.

조회 계약에는 `effect_calculation_status`, 잠재 강도, 피해량을 두지 않는다. 이 단계에서 사용자의 관심은 **관계가 어디서 발견되고 어떤 상태인지**이며, 후속 계산 결과는 기존 지지 v3 관계/세력 층위가 맡는다. [원국 비교 예시](eight_character_relation_lookup_example.md)에 있던 `effect_calculation_status`는 설명용이므로 이번 최소 계약에서 제외했다.

## ID와 기존 출력의 대응

| 관계 | 최소 계약의 ID | 현재 출처와 처리 |
| --- | --- | --- |
| 지지 쌍 | `branch:<type>:<앞 기둥>:<뒤 기둥>` | [지지 v3 쌍 ID](../services/branch_dynamics_v3_assembler.py)를 재사용. 현행 매트릭스의 한글 포함 `relation_id`는 `source_refs`로 보존 |
| 천간 쌍 | `stem:<type>:<앞 기둥>:<뒤 기둥>` | 천간합·충은 매트릭스의 위치 쌍을 사용. 천간극은 [기존 개별 탐지](../services/stem_relations.py)의 방향과 상대 위치를 사용 |
| 다자 구조 | `group:<type>:<구조 키>` | [지지 v3 그룹 ID](../services/branch_dynamics_v3_assembler.py)를 재사용하고 위치별 성립 조합을 보존 |
| 동주 간지 | `same_pillar:element:<기둥>` | [지지 기준 세력](../services/branch_dynamics.py)의 동주 관계 사실을 참조. 세력 보정값을 이 조회 계약에 복사하지 않음 |
| 동주 자합 | `same_pillar:self_combine:<기둥>` | [자합 판정](../services/relations.py)의 후보·조건 근거를 참조. 자합 없는 동주에는 없음 |
| 지장간 투출 | `cross_layer:transmission:<지지 기둥>:<천간 기둥>` | [글자별 분석](../services/analysis.py)의 위치별 투출 결과를 상세 지장간 표와 대조. `hidden_stem`은 대상 천간 글자와 같음 |

같은 관계가 현행 매트릭스와 지지 v3에 각각 다른 ID로 실려 있으면, 중앙 ID는 한 번만 기록하고 **원본의 ID를 `source_refs`에 붙인다.** 현행 `GET /`의 `interactions.matrix`와 지지 쌍 본문은 유지한다. 관계 조회는 별도 `GET /relation-index`에서만 제공하며, 더 상세한 기존 관계·수치 필드를 이 최소 목록에 복사하지 않는다.

## 관계 유형별 검증 범위

이 표는 **새 조합별 점수 모델을 만들지 않고**, 규칙표/현재 탐지기의 지원 범위에서 1단계 완료를 평가하는 기준이다. 이미 있는 회귀 사례와 새로운 위치·중복 반례를 함께 사용한다.

| 대상 | 최소 전수 범위 | 조건·반례 검사 | 출력 계약 검사 |
| --- | --- | --- | --- |
| 지지 쌍 구조 | 서로 다른 지지 66쌍·동지 12쌍을 양방향으로 확인. 육합 6, 충 6, 천 6, 파 3, 지세형 2, 자형 4, 반합 8, 공합 4, 지정 암합 3 | 인접/격위, 同字 반복, 합에 끼어든/밖에서 인접한 충, 자형 인접성, 子卯형 부재 | 각 실제 위치 쌍은 중앙 ID 하나; 후보가 없는 쌍에는 가짜 관계를 만들지 않음 |
| 지지 대표 오행 관계 | 네 위치의 여섯 쌍에서 생·극을 판정하고 동기 사실은 현행 배경 근거로 보존 | 구조 관계 `active` 시 생·극 억제, `conditional`이면 선제 억제 금지 | 매트릭스와 v3 생성 경로를 동일 관계로 대조; 오행 방향과 수치 미계산 분리 |
| 다자 구조 | 삼합 4종, 방합 4종, 삼형 2종 | 반복 지지의 두 성립 조합, 중신 중복, 삼합 억제와 잔존 반합, 격위 삼형 | 그룹 한 건과 3~4개 참여 위치, 각 세 글자 조합의 참조 무결성 |
| 천간 쌍 | 규칙표의 천간합 5쌍·충 4쌍·극 11개 방향 규칙을 여섯 위치 쌍의 정·역순에 배치 | 같은 천간 반복, 합과 극 등 복수 후보, 기존 극 목록 밖 조합에 임의 극 생성 금지 | 합·충의 미평가 상태를 `detected`로 보존, 극의 오행 방향과 위치별 ID 검사 |
| 동주 오행·자합 | 네 기둥의 천간·지지 관계와 자합 규칙표 9개 후보 | 자합 조건 未형 충족/미충족, 辰충 차단, 후보 없는 간지 | 같은 기둥의 간·지만 참여; 자합 `active`와 실제 합화/세력 변화 구분 |
| 투출·통근 상태 | 12지지의 상세 지장간과 10천간의 반복 위치 대조 | 한 지장간이 두 천간 위치에 드러나는 경우, 동주 원점수 0/양수 경계, 충·천·형 반영 후 변허; 전주 v1 회귀의 0.5 경계 | 지장간 표·투출 관계·허실 원본 근거 일치. 투출과 통근 상태의 별도 ID/필드 유지 |
| 공통 조회 불변 조건 | 연·월·일·시 × 천간·지지 정확히 8개 | 반복 글자·다중 관계·조건부/억제/후보의 혼재 | 관계 ID 유일, 참여 글자·위치·방향 유효, `relation_ids`가 중앙 목록에서 정확히 역산됨 |

지지 78쌍의 이전 전수 결과는 [별도 감사](branch_relation_candidate_audit.md)에 있지만, **이 8글자 계약을 연결한 뒤 다시 검증해야** 1단계 완료를 주장할 수 있다. 천간 5/4/11과 자합 9는 [현행 규칙 파일](../services/relation_rules.py)의 항목 수이며 교리 전체의 목록이라고 주장하지 않는다. 현행 규칙 밖 천간 生·동기, 다른 기둥 천간↔지지 직접 관계, 일반적인 지장간 피해·入墓는 이 전수 검사로 자동 완성되지 않는다. 필요한 탐지 규칙은 별도 근거 검토 후 확장한다.

## 현재 검증과 다음 구현

- [계약 모델](../schemas/character_relation_index.py)은 8글자 구성, 천간별 `stem_state`, 투출 대상 지장간, 관계 ID·참여 위치, 방향, 그룹의 위치별 조합, 중복 ID, 중앙 관계와 글자별 참조의 일치를 검사한다. `source_refs`의 실제 원본 존재·내용 일치와 규칙표 대비 **후보 누락 여부는 계약 모델 단독으로 검사하지 않는다.** 생산 조립기와 통합 검사에서 원본 결과를 대조한다.
- [계약 집중 테스트](../tests/test_character_relation_index.py) 7건이 Python 3.12에서 통과했다. 서로 다른 위치의 같은 己, 반복 亥 삼합 조합, 투출 대상, 천간 상태, 빠진 참조·중복 ID·잘못된 종류/방향/조건 이유를 다룬다.
- [읽기 전용 조립기](../services/character_relation_index.py)는 기존 `interactions.matrix`, `analysis.details`, `branch_dynamics` 결과를 입력받고 지지 v3 부분 조립으로 정형 지지 ID·상태를 얻는다. 원본 지지 쌍·그룹의 위치·상태와 v3 결과, 천간합·충 및 극의 글자별 결과, 자합·동주 근거를 대조한다. 입력을 수정하거나 새 작용량을 만들지 않는다.
- [조립기 집중 테스트](../tests/test_character_relation_index_assembler.py) 9건에서 지지 쌍 정·역순 **156개 입력**, 천간 첫 두 위치의 **100개 순서 조합**, 자합 규칙표 **9개 후보**, 삼합·방합·삼형 **10개 구조**, 반복·조건부·억제 사례를 확인했다. A 원국에서 연간 乙→월간/일간 己의 두 관계와 일지 未→두 己 투출이 위치별로 분리된다. 통근 점수 0인 원국의 허투도 별도로 확인한다. 원본 위치·상태·관계가 바뀐 입력은 거부한다.
- 이 검증은 **규칙표에 등록된 후보를 해당 입력에서 옮기는 경로**를 확인한다. 천간합/충의 실제 성립이나 새 후보의 명리적 타당성을 증명하지 않으며, 156개 입력을 모든 네 글자 조합으로 확대 해석하지 않는다.

## 실제 응답 연결

- [루트 라우트](../routers/root.py)의 `GET /`는 [기존 응답 모델](../schemas/saju_analysis.py)의 고정된 `advanced_analysis`를 사용한다. 기존 [원국 조립기](../services/saju_orchestrator.py)가 `analysis.details`, `advanced_analysis.interactions`, `advanced_analysis.branch_dynamics`를 각각 반환하고, [허실·빈주 계산](../services/xu_shi.py)과 [빈주 출력](../services/bin_zhu.py)이 기존 매트릭스 관계 ID를 사용한다. 같은 응답에 초안 관계 목록을 무조건 추가하면 기존 형식도 바뀌므로 별도 조회 경로를 선택했다.
- `GET /relation-index`는 루트 라우트의 동일한 날짜·양음력·성별 검증을 거쳐 기존 원국 결과를 얻은 뒤, [응답 조립 함수](../services/character_relation_index.py)로 관계 조회만 반환한다. 전체 원국 분석을 한 번 수행한 후 조회 자료를 만들므로 당장은 계산 경로를 재사용하는 구현이다. 기존 응답에 관계 본문을 하나 더 담지 않는다.
- [투출 위치 테스트](../tests/test_transmission_positions.py) 4건은 12지지×10천간, 반복된 천간의 네 위치, 지장간 목록과 투출/미투출의 일치를 확인한다. [허실 집중 테스트](../tests/test_xu_shi.py)는 격위 자형 후보가 실제 뿌리 손상으로 처리되지 않는 반례를 포함한다. 전체 Python 3.12 회귀 **170건 통과**.
- [읽기 전용 DB·HTTP 통합 테스트](../tests/test_character_relation_index_integration.py) 4건은 새 경로의 응답 계약, 매트릭스 원본 ID의 실제 존재, 네 천간의 기존 허실 결과 일치, 세 날짜의 원본 관계 상태 대조, 새 경로 호출 전후 `GET /` 응답의 동일성, 잘못된 월 입력의 동일한 오류를 확인했다. 기존 [원국 통합 테스트](../tests/test_xu_shi_integration.py) 2건도 통과했다. 지지 v3 응답은 아직 공개되지 않았다.

| 실제 달력 날짜·시간 | 원본 매트릭스 관계 | 독립 조회 관계(투출) | 조회 결과의 상태 분포 |
| --- | ---: | ---: | --- |
| 1990-01-01 12:00 | 4 | 22(8) | `active 3`, `suppressed 2`, `potential 4`, `detected 13` |
| 1995-05-12 14:30 | 4 | 20(3) | `active 2`, `suppressed 2`, `potential 6`, `detected 10` |
| 2000-01-01 08:15 | 5 | 19(4) | `active 4`, `suppressed 4`, `potential 3`, `detected 8` |

독립 조회 관계에는 매트릭스에 없는 지지 생·극, 동주 간지, 천간극 등이 포함되므로 관계 수가 더 많다. 세 날짜 모두 **원본 매트릭스의 각 ID가 조회 결과의 `source_refs`에서 정확히 한 번 등장**했고, 원본에 성립 상태가 있는 관계는 그 상태와 일치했다. 완성 삼합 안의 구조 전용 반합처럼 v3가 성립 상태를 의도적으로 바꾸는 경우만 원본의 `potential`과 다른 `candidate_only`로 보존한다. 이 세 날짜는 상태 매핑의 실제 사례 검증이며 모든 달력 원국의 명리 판정 검증은 아니다.

**현재 개발 기준:** 관계와 통근 영향을 분리하며 자동 제외·변허를 재도입하지 않는다. 수치 연구의 다음 작업은 재개 지시가 아니다. [현행 문서 목록](README.md)을 따른다.
