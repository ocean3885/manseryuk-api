# 지지 작용 최종 출력 계약 초안

> 이전 설계 초안이다. 최신 사용자 목표 출력은 [v3 트리](./branch_dynamics_v3.json)이며, 구현 순서는 [v3 개발 계획](./branch_dynamics_v3_plan.md)을 따른다.

이 문서는 advanced_analysis.branch_dynamics의 **목표 출력**을 고정하기 위한 설계 초안이다. 아래 JSON은 값과 relation_id까지 모두 설명용 가상 사례이며, 현재 API의 실제 응답이나 검증된 명리 계수가 아니다. 기존 구현은 [v2 명세](./branch_dynamics_v2.md)와 [현재 스키마](../schemas/saju_analysis.py)를 따른다. 변경 시 이 문서의 키 의미와 사례를 함께 수정한다.

## 경계와 불변 조건

- 원국의 네 지지는 branch_strengths의 year·month·day·hour에 각각 한 번 기록한다. pairwise는 위치 기준 여섯 쌍을 모두 기록하며 관계가 없는 쌍의 relations는 빈 배열이다.
- 관계 탐지는 interactions.matrix에서 하고, 각 지지의 세력·관계별 작용은 branch_dynamics에서 계산한다. relation_id는 탐지 결과와 연결한다.
- 합·충·형·파·해·생·극은 같은 쌍에 중첩될 수 있다. 관계마다 성립 상태, 양방향 force, 받은 작용, 역할과 근거를 따로 기록하며 서로 합산한 총점을 만들지 않는다.
- 빈주(년·월=guest, 일·시=host)는 위치와 작용 방향의 해석 맥락이다. 빈주 분류나 기존 bin_zhu_dynamics의 총점으로 관계의 존재·힘·주도자를 결정하지 않는다.
- groups는 탐지된 삼합·방합·삼형의 세 지지 구조를 기록한다. 억제된 후보도 사유와 함께 남긴다. 완성 삼합의 내부 두 쌍은 component_pairs에 구조 근거로 표시하고 별도 반합 force를 만들지 않는다. 깨진 삼합의 잔존 반합은 pairwise 관계로 기록한다. 방합과 삼합의 독립 force는 계산하지 않는다.
- score_meaning은 숫자가 미보정 상대 모델 지표라는 뜻이다. 숫자를 현실의 피해량·길흉 확률로 해석하지 않는다.

## 목표 트리

| 경로 | 자료형·의미 |
| --- | --- |
| schema_version, rule_version | 문자열. 응답 구조 버전과 관계 규칙 버전을 구분한다. |
| branch_strengths.<pillar> | year·month·day·hour별 객체. 지지 자체의 비교 세력과 산출 근거. |
| branch_strengths.<pillar>.bin_zhu_domain | guest 또는 host. 세력 계산에 곱하지 않는다. |
| branch_strengths.<pillar>.strength_evidence | 계절·지장간·동주 천간·주변 지지의 보정 근거. 숫자에 설명 가능한 출처를 붙인다. |
| pairwise[] | 여섯 위치 쌍의 배열. pair_id와 pillars로 쌍을 식별한다. |
| pairwise[].relations[] | 그 쌍에서 탐지된 관계별 객체. 관계가 없으면 빈 배열. |
| relations[].activation_status, status_reasons | potential·conditional·suppressed·candidate_only와 사유 코드 배열. 사유가 없으면 빈 배열. |
| relations[].power_before | 비교 상대의 자기 피드백을 제외한 두 지지 세력. |
| relations[].force | 위치별 양방향 잠재 작용량. 방향이 성립하지 않거나 억제되면 0. |
| relations[].effect_received | 각 위치가 받은 모델상 작용 지표. force와 다른 의미다. |
| relations[].strength_dominance, force_dominance | 관계 전 세력 우세와 관계별 작용량 우세를 구분한다. 동률·판정 불가는 tie·undetermined. |
| relations[].roles | 관계별 작용 주체·피작용 위치. 세력 우세와 자동으로 동일시하지 않는다. |
| relations[].bin_zhu_context | 이미 계산한 작용의 빈·주 방향을 읽는 보조 정보. 주도권 점수가 아니다. |
| groups[] | 탐지된 세 지지 구조. group.status=not_scored이며 독립 force가 없다. |
| groups[].condition_evidence | 중신 중복·인접 충 등 구조 상태를 결정한 위치별 근거. 해당 사항이 없으면 빈 목록을 사용한다. |
| groups[].formation_evidence[] | 같은 글자가 반복될 때도 각 위치별 성립 조합을 구분한다. |
| formation_evidence[].component_pairs[] | 삼합의 생지–중신·중신–묘고 구성 쌍. structural_only이며 독립 반합 관계나 힘이 아니다. 방합·삼형은 규칙이 정해질 때까지 빈 배열을 쓴다. |
| formation_evidence[].direction_candidates[] | 구조상 방향 후보. candidate_only는 실제 견인력이나 우세 판정이 아니다. |
| formation_evidence[].bin_zhu_context | 참여 위치의 빈·주 구분과 두 영역을 함께 잇는지 여부. |

## 설명용 JSON 샘플

예시는 네 위치의 지지가 亥·卯·未·亥인 경우다. 값은 **출력 형태 확인용**이며 실제 계산 결과가 아니다. 반복된 亥는 year와 hour로 구분한다. 이 샘플의 여섯 pairwise 항목은 각 쌍의 관계 표현 방식만 보여주며, 조합별 작용 계수를 확정하지 않는다.

~~~json
{
  "schema_version": "3.0.0-draft",
  "rule_profile": "mangpa_project_provisional",
  "rule_version": "example-only",
  "scope": "natal",
  "score_meaning": "uncalibrated_relative_model_index",
  "branch_strengths": {
    "year": {"branch": "亥", "element": "수", "bin_zhu_domain": "guest", "base_power": 1.10, "after_stem_power": 0.98, "effective_power": 1.04, "strength_evidence": {"season": {"month_branch": "卯", "factor": 0.90}, "hidden_stems": [{"stem": "壬", "ratio": 0.70}, {"stem": "甲", "ratio": 0.30}], "same_pillar_stem": {"stem": "己", "effect": "pressure", "adjustment": -0.12}, "surroundings": [{"source_pillar": "month", "relation": "outflow", "adjustment_ratio": -0.02}]}},
    "month": {"branch": "卯", "element": "목", "bin_zhu_domain": "guest", "base_power": 2.40, "after_stem_power": 2.20, "effective_power": 2.35, "strength_evidence": {"season": {"month_branch": "卯", "factor": 1.20}, "hidden_stems": [{"stem": "乙", "ratio": 1.00}], "same_pillar_stem": {"stem": "丁", "effect": "outflow", "adjustment": -0.20}, "surroundings": [{"source_pillar": "year", "relation": "support", "adjustment_ratio": 0.04}]}},
    "day": {"branch": "未", "element": "토", "bin_zhu_domain": "host", "base_power": 1.50, "after_stem_power": 1.42, "effective_power": 1.45, "strength_evidence": {"season": {"month_branch": "卯", "factor": 0.80}, "hidden_stems": [{"stem": "己", "ratio": 0.60}, {"stem": "丁", "ratio": 0.30}, {"stem": "乙", "ratio": 0.10}], "same_pillar_stem": {"stem": "辛", "effect": "outflow", "adjustment": -0.08}, "surroundings": [{"source_pillar": "month", "relation": "pressure", "adjustment_ratio": -0.04}]}},
    "hour": {"branch": "亥", "element": "수", "bin_zhu_domain": "host", "base_power": 1.10, "after_stem_power": 0.98, "effective_power": 1.09, "strength_evidence": {"season": {"month_branch": "卯", "factor": 0.90}, "hidden_stems": [{"stem": "壬", "ratio": 0.70}, {"stem": "甲", "ratio": 0.30}], "same_pillar_stem": {"stem": "己", "effect": "pressure", "adjustment": -0.12}, "surroundings": [{"source_pillar": "year", "relation": "same_element", "adjustment_ratio": 0.05}]}}
  },
  "pairwise": [
    {"pair_id": "year:month", "pillars": ["year", "month"], "branches": ["亥", "卯"], "domain_pair": "guest_guest", "relations": [{"relation_id": "example:year:month:생", "type": "생", "activation_status": "potential", "status_reasons": [], "power_before": {"year": 1.04, "month": 2.35}, "force": {"year_to_month": 0.62, "month_to_year": 0.0}, "effect_received": {"year": 0.0, "month": 0.19}, "strength_dominance": "month", "force_dominance": "year", "roles": {"year": "supports", "month": "receives_support"}, "bin_zhu_context": {"acting_domain": "guest", "receiving_domain": "guest", "flow": "guest_to_guest"}, "evidence": {"rule_id": "example:water_generates_wood", "distance_weight": 1.0}}]},
    {"pair_id": "year:day", "pillars": ["year", "day"], "branches": ["亥", "未"], "domain_pair": "guest_host", "relations": [{"relation_id": "example:year:day:극", "type": "극", "activation_status": "potential", "status_reasons": [], "power_before": {"year": 1.04, "day": 1.45}, "force": {"year_to_day": 0.0, "day_to_year": 0.81}, "effect_received": {"year": 0.47, "day": 0.0}, "strength_dominance": "day", "force_dominance": "day", "roles": {"year": "receives_control", "day": "controls"}, "bin_zhu_context": {"acting_domain": "host", "receiving_domain": "guest", "flow": "host_to_guest"}, "evidence": {"rule_id": "example:earth_controls_water", "distance_weight": 0.7}}]},
    {"pair_id": "year:hour", "pillars": ["year", "hour"], "branches": ["亥", "亥"], "domain_pair": "guest_host", "relations": [{"relation_id": "example:year:hour:형", "type": "형(刑)", "activation_status": "potential", "status_reasons": [], "power_before": {"year": 1.04, "hour": 1.09}, "force": {"year_to_hour": 0.39, "hour_to_year": 0.41}, "effect_received": {"year": 0.21, "hour": 0.19}, "strength_dominance": "tie", "force_dominance": "tie", "roles": {"year": "mutual_pressure", "hour": "mutual_pressure"}, "bin_zhu_context": {"acting_domain": null, "receiving_domain": null, "flow": "bidirectional"}, "evidence": {"rule_id": "example:self_punishment", "distance_weight": 0.5}}]},
    {"pair_id": "month:day", "pillars": ["month", "day"], "branches": ["卯", "未"], "domain_pair": "guest_host", "relations": [{"relation_id": "example:month:day:극", "type": "극", "activation_status": "potential", "status_reasons": [], "power_before": {"month": 2.35, "day": 1.45}, "force": {"month_to_day": 1.88, "day_to_month": 0.0}, "effect_received": {"month": 0.0, "day": 1.16}, "strength_dominance": "month", "force_dominance": "month", "roles": {"month": "controls", "day": "receives_control"}, "bin_zhu_context": {"acting_domain": "guest", "receiving_domain": "host", "flow": "guest_to_host"}, "evidence": {"rule_id": "example:wood_controls_earth", "distance_weight": 1.0}}]},
    {"pair_id": "month:hour", "pillars": ["month", "hour"], "branches": ["卯", "亥"], "domain_pair": "guest_host", "relations": [{"relation_id": "example:month:hour:생", "type": "생", "activation_status": "potential", "status_reasons": [], "power_before": {"month": 2.35, "hour": 1.09}, "force": {"month_to_hour": 0.0, "hour_to_month": 0.46}, "effect_received": {"month": 0.15, "hour": 0.0}, "strength_dominance": "month", "force_dominance": "hour", "roles": {"month": "receives_support", "hour": "supports"}, "bin_zhu_context": {"acting_domain": "host", "receiving_domain": "guest", "flow": "host_to_guest"}, "evidence": {"rule_id": "example:water_generates_wood", "distance_weight": 0.7}}]},
    {"pair_id": "day:hour", "pillars": ["day", "hour"], "branches": ["未", "亥"], "domain_pair": "host_host", "relations": [{"relation_id": "example:day:hour:극", "type": "극", "activation_status": "potential", "status_reasons": [], "power_before": {"day": 1.45, "hour": 1.09}, "force": {"day_to_hour": 0.84, "hour_to_day": 0.0}, "effect_received": {"day": 0.0, "hour": 0.48}, "strength_dominance": "day", "force_dominance": "day", "roles": {"day": "controls", "hour": "receives_control"}, "bin_zhu_context": {"acting_domain": "host", "receiving_domain": "host", "flow": "host_to_host"}, "evidence": {"rule_id": "example:earth_controls_water", "distance_weight": 1.0}}]}
  ],
  "groups": [
    {
      "relation_id": "example:group:亥卯未",
      "type": "삼합(三合)",
      "participants": ["year", "month", "day", "hour"],
      "activation_status": "potential",
      "status_reasons": [],
      "status": "not_scored",
      "candidate_element": "木",
      "transformed_element": null,
      "condition_evidence": {"middle_pillars": ["month"], "adjacent_clashes": [], "duplicate_middle": false},
      "formation_evidence": [
        {"pillars": ["year", "month", "day"], "structural_roles": {"year": "birth", "month": "center", "day": "storage"}, "component_pairs": [{"pillars": ["year", "month"], "roles": ["birth", "center"], "status": "structural_only"}, {"pillars": ["month", "day"], "roles": ["center", "storage"], "status": "structural_only"}], "direction_candidates": [{"from_pillar": "year", "to_pillar": "month", "activation_status": "candidate_only"}, {"from_pillar": "day", "to_pillar": "month", "activation_status": "candidate_only"}], "overlapping_pairs": [], "bin_zhu_context": {"domains": {"year": "guest", "month": "guest", "day": "host"}, "crosses_domains": true}},
        {"pillars": ["month", "day", "hour"], "structural_roles": {"month": "center", "day": "storage", "hour": "birth"}, "component_pairs": [{"pillars": ["hour", "month"], "roles": ["birth", "center"], "status": "structural_only"}, {"pillars": ["month", "day"], "roles": ["center", "storage"], "status": "structural_only"}], "direction_candidates": [{"from_pillar": "hour", "to_pillar": "month", "activation_status": "candidate_only"}, {"from_pillar": "day", "to_pillar": "month", "activation_status": "candidate_only"}], "overlapping_pairs": [], "bin_zhu_context": {"domains": {"month": "guest", "day": "host", "hour": "host"}, "crosses_domains": true}}
      ]
    }
  ]
}
~~~

## 빈 값과 중복의 의미

| 값 | 의미 |
| --- | --- |
| relations: [] | 두 위치의 탐지된 관계가 없음. 위치 쌍 자체는 pairwise에 남긴다. |
| status_reasons: [] | 검사한 조건에서 억제·유보 사유가 없음. 억제 시 사유 코드를 넣고, 위치별 근거는 condition_evidence에 넣는다. |
| transformed_element: null | 후보 오행은 알지만 실제 합화는 판정하지 않음. |
| bin_zhu_context.acting_domain: null | 양방향이거나 주도 방향을 판정할 수 없음. 빈주 영역으로 우세를 강제하지 않는다. |
| overlapping_pairs: [] | 그룹 안에서 별도로 탐지되어 출력된 쌍 관계가 없음. 완성 삼합의 내부 component_pairs는 이 목록에 넣지 않는다. |
| groups: [] | 탐지된 세 지지 구조가 없음. 네 위치에서 세 위치를 고르는 경우는 네 가지지만 모두 그룹이 되는 것은 아니다. |

## 현재 구현과의 차이 및 개발 순서

현재 응답에는 schema_version, bin_zhu_domain, strength_evidence 객체, relations[].bin_zhu_context, formation_evidence[].component_pairs 및 formation_evidence[].bin_zhu_context가 없다. 기존 branch_strengths의 components·evidence·ambient_evidence와 pairwise의 context_evidence는 목표 구조의 근거 정보에 대응하지만, 필드 통합은 기존 소비자를 확인한 뒤 진행한다. strength_dominance는 현재 dominance의 목표 이름이다. 설명용 샘플의 relation_id와 숫자를 회귀 테스트의 기대값으로 사용하지 않는다.

1. 현재 출력의 사용처와 소비자를 확인하고 목표 키의 이름·필수 여부·상태 어휘를 확정한다.
2. 삼합 component_pairs 및 위치별 빈주 맥락을 **추가 필드**로 구현한다. 기존 force와 그룹 점수 정책은 유지한다.
3. 실제 원국 사례로 값과 중복을 검증하고, 계수 변경은 별도 단계에서 진행한다.
4. 새 계약으로 옮긴 소비자를 확인한 뒤 bin_zhu_dynamics의 사용 중단과 API 버전 변경을 결정한다. 천간 관계나 직업 조언을 지지 작용 객체에 넣지 않는다.
