# 지지 작용 작업 이어받기

작성일: 2026-10-30

## 현재 기준

- 최종 출력 목표는 [branch_dynamics_v3.json](./branch_dynamics_v3.json), 구현 순서는 [branch_dynamics_v3_plan.md](./branch_dynamics_v3_plan.md)를 따른다. 목표 JSON은 주석이 포함된 설계 샘플이며 현재 API 응답이 아니다.
- 실행 규칙의 원본은 [relation_rules.py](../services/relation_rules.py)다. 현재 v2 규칙 버전은 `2.13.0`, v3 잠재량 규칙 버전은 `3.1.0-draft`다.
- 사용자 최신 결정: 파 후보는 `子卯`, `卯午`, `午酉` 세 쌍이다. `子卯`는 형 후보에서 제외하고 파로만 탐지한다. `子卯`와 `卯午`의 생 후보는 파 규칙에 의해 억제한다.
- 천/해 후보는 `子未`, `丑午`, `寅巳`, `卯辰`, `申亥`, `酉戌` 여섯 쌍이다.
- 삼형은 `寅巳申`, `丑戌未`의 세 지지 구조 후보로 기록한다. 쌍별 형은 `丑戌`, `戌未`와 자형 후보만 남는다. `寅巳申`의 세 쌍은 각각 천·충·육합, `丑未`는 충으로 기록한다.
- `午未` 육합의 후보 오행은 土다. 후보 오행은 실제 합화 판정이 아니다.

## 구현 상태

- [branch_relations.py](../services/branch_relations.py)와 [interaction_matrix.py](../services/interaction_matrix.py)는 관계 후보를 위치별로 탐지한다. 육합·삼합에는 일부 인접 충·중복 조건이 반영되어 있다.
- [branch_dynamics.py](../services/branch_dynamics.py)는 월령·동주 천간·주변 지지를 반영한 지지별 상대 세력과 쌍별 잠재 작용을 산출한다.
- [branch_dynamics_v3_assembler.py](../services/branch_dynamics_v3_assembler.py)는 v2 결과에서 v3의 지지별 근거, 여섯 위치 쌍, 그룹, 경합 후보를 조립한다. 방향별 `interaction_intensity`는 잠재량이다. 실제 성립과 `applied_power_delta`는 대부분 미확정이며 `active_interaction_ids`는 비어 있다. 삼형 그룹의 독립 강도와 방향도 미정이다.
- 변경 후 `.venv312/bin/python -m unittest discover -s tests` 실행 결과 101개 테스트가 통과했다. 가상환경 Python은 일부 샌드박스에서 경로가 보이지 않을 수 있으므로, 그 경우 호스트 실행 권한이 필요하다.

## 내일 시작할 작업

1. [relation_rules.py](../services/relation_rules.py)의 합·충·형·파·천 후보 조합을 전체 점검한다. 각 쌍의 공존 관계와 `primary_relation`을 표로 뽑아 사용자와 확정한다. 최근 `子卯` 수정처럼 분류 변경이 하위 계산을 흔들지 않도록 이 단계를 먼저 마친다.
2. 확정된 조합부터 성립·억제·조건부 기준과 조합별 방향을 규칙으로 추가한다. 근거가 부족한 경우 v3 상태를 `unresolved`로 유지한다.
3. 실제 적용량의 기준값과 부호를 정의한다. 현재 `effective_power`에는 주변 지지 영향이 이미 일부 포함되어 있으므로 쌍별 잠재량을 그대로 더하지 않는다. 월간의 생·극·설기와 주변 지지 효과가 중복 계산되지 않는 사례로 검증한다.

다음 대화에서 “`docs/branch_dynamics_handoff.md`를 기준으로 관계 후보표 전수 검토를 시작해줘”라고 요청하면 1번부터 진행할 수 있다.
