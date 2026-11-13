# 작업 재개 기록 — 2026-11-13

## 재개 시 먼저 확인할 사항

현재 작업 브랜치는 `main`이다. 이 문서를 포함한 커밋은 `8de6921` 이후에 쌓인
API 정리·관계 원자료 개선을 저장하는 체크포인트다. 커밋 번호는 문서 자체에
고정하지 않고 `git log -5 --oneline`으로 확인한다.

[현행 개발 기준](README.md), [원자료 관계 계약](raw_character_relations_contract.md),
[자연어 표시 계약](relation_presentation_contract.md)을 먼저 읽는다.
중단 연구 보관소의 다음 작업을 현행 지시로 사용하지 않는다.

사용자는 기존 프론트엔드 호환 제약 없이 응답 구조를 개선하도록 허용했다.
이전 변경을 다시 적용하지 말고 현재 체크아웃의 코드부터 확인한다.
환경 게시와 Git 커밋·푸시는 별개이며, 이번 저장 작업에는 별도 환경 게시를 포함하지 않는다.

## 완료된 변경

### API 범위 정리

- `/analysis-summary`의 라우트·스키마·조립기·전용 테스트·계약을 제거했다.
- 전용 카드·순서·비교 기능은 다른 API로 이전하지 않았다.
- 기본 `/`의 `analysis.summary`는 유지한다.
- 원국 글자·관계는 `/character-details`, 운 선택은 `/cycle-analysis`를 사용한다.

### 기본 `/` 응답 보강

- 대운 절기 조회를 명시적으로 정렬해 가장 가까운 순행·역행 절기를 선택한다.
- 기존 ±35일 범위와 출생일 당일 절기 제외 정책은 유지한다.
- 절기 자료가 없으면 임의의 1.0세 시작을 만들지 않는다.
  `start_age=null`, `start_age_status=term_data_unavailable`, 빈 대운 목록과
  선택 불가 상태를 반환하며 운 선택 API는 이에 맞는 오류를 반환한다.
- `calendar.lunar.is_leap_month`는 달력 DB의 실제 윤달 표시를 사용한다.
- 기준 날짜는 요청 내에서 한 번 계산하고 `meta.reference_date`로 제공한다.
- 운의 표시 나이는 세는나이이며 `age_basis=counting_age`를 명시한다.
- `cycles.baby_10`을 제거하고 세운 첫 10년인 `cycles.childhood_10`으로 바꿨다.
- 오행 분포의 기준과 잠정 지표 의미를 명시하고, 설명의 과도한 성격·우세 단정을 줄였다.
- 원국 조회 설명에서 관계 적용 전후 통근 변화를 계산했다는 오해를 없앴다.

### `stem.relations`·`branch.relations` 정리

- 관계 목록은 항상 배열이며 관계가 없으면 `[]`다.
- 천간 `restrain`은 항상 `restrain_to`·`restrain_me` 배열을 가진다.
- `six_haps`는 위치별 전체 육합 배열이다. 단일 상대 별칭과 `six_haps_all`을 제거했다.
- 관계별 `activation_status`, `status_reasons`, `impact_status=not_evaluated`를 제공한다.
- 천간합·지지합·자합의 오행은 `candidate_element`로 표시한다.
- 원자료 `strength`는 제거하고 실제 의미에 맞는 거리 가중치·기본 계수·구조 계수·잠정 지표로 나눴다.
- 반복 글자가 있는 방합은 실제 세 자리 조합으로 인접성을 계산한다.
- 매트릭스는 탐지 함수의 상태·사유를 전달하고, 원국 조립기는 쌍별 원자료와의
  상태·사유·후보 오행 불일치를 거부한다.

### 읽기 쉬운 조건 근거

- 육합·삼합 `condition_evidence.summary`에 조건과 근거를 읽을 수 있는 문장으로 제공한다.
- 충 근거의 `affected`·`cause`에 위치·글자·일간 기준 십성·표시명을 제공한다.
- 육합의 충 위치는 `location_label`, 삼합 중신의 위치별 자료는 `middle_members`로 확인한다.
- 삼합 생지·성지 충으로 남은 반합의 `fallback_from`에도 같은 글자 정보와 설명을 제공한다.
- 원자료 → 매트릭스 → 중앙 관계 근거 및 글자 상세까지 정보를 전달한다.
- 사용자 요청에 따라 `summary`의 “현재 판정은 조건부입니다” 같은 상태 반복 문구는 제거했다.
  상태는 `activation_status`와 기존 배지로 확인한다.

예: `년지 午(상관) ↔ 월지 子(정인): 육합 조합 바깥의 인접 충입니다.`

## 마지막 논의와 미완료 사항

### 다음 권장 검토: `conditional`의 의미

사용자는 “추후 구현할 것이 아니면 조건부 상태를 지워도 되는가”를 질문했다.
현재 `conditional`은 구현 대기 표시가 아니라 이미 확인된 조건에 따른 판정이다.

- 육합: `external_adjacent_clash` → `conditional`
- 삼합: `duplicate_middle` → `conditional`
- 동주 자합에도 필수 형 조건 미충족에 따른 조건부 상태가 있다.

**`조건부`를 `성립 유보`로 바꾸자는 제안은 아직 구현하지 않았다.**
`schemas/character_details.py`의 배지와 `services/relation_presentation.py`의
설명은 여전히 `조건부`를 사용한다. 상태 코드 삭제·이름 변경·규칙 변경도 하지 않았다.

재개하면 먼저 다음을 검토하는 것이 좋다.

1. 각 조건부 판정의 규칙 근거와, 현재 확인된 사실·미평가 항목을 구분한다.
2. 무엇을 추가로 확인해야 성립하는지 정의돼 있는지 검토한다. 단순 미구현은
   조건부 판정으로 표현하지 않고 해당 미평가 범위에 맞게 설명한다.
3. 그 결과에 따라 상태 구분 유지 여부와 표시 명칭을 결정한다.
   이름만 바꾸는 작업으로 규칙의 타당성 검토를 대신하지 않는다.
4. 변경한다면 원자료·매트릭스·중앙 관계·설명·응답 검증·회귀 검사를 함께 맞춘다.

핵심 파일: `services/relation_rules.py`, `services/branch_relations.py`,
`services/relations.py`, `services/character_relation_index.py`,
`services/relation_presentation.py`, `schemas/character_details.py`.

### 십성 조합별 해설

관계 유형·방향·양쪽 십성·상태에 맞는 해설 확장을 논의했지만 아직 구현하지 않았다.
기존 위치·십성·근거 표시와 십성 조합의 상징 해설은 별개다.
조건부 판정의 의미부터 정리한 뒤, 관계 유형 하나를 선택해 해설 기준과 사례를
검토하는 방향을 제안했다. 모든 십성 조합 해설이나 예측 문구를 자동 추가하지 않는다.

## 검증과 실행 환경

Python 3.12 환경과 기존 달력 DB를 사용한다.

```bash
git status --short
git log -5 --oneline
.venv312/bin/python -m unittest discover -s tests
git diff --check
```

코드 변경 후 마지막 전체 검사에서 250개 테스트가 통과했고,
이번 문서 저장 체크포인트의 전체 재검사에서도 250개가 통과했다.
기존 AnyIO 스트림의 `ResourceWarning`은 출력될 수 있으나 테스트 실패는 아니다.

주요 추가 검사:

- `tests/test_root_response_contract.py`: 절기·윤달·나이·어린 시절 세운·HTTP 전달
- `tests/test_raw_character_relations.py`: 지지 144쌍의 세 상대 위치, 천간 100쌍,
  반복 다자 조합·상태 정합성·원자료 변조 거부
- `tests/test_condition_evidence.py`: 충 당사자·십성·위치·중신 중복·근거 전달·상태 반복 문구 제거
- 기존 자연어·근거·운 조회 회귀 검사도 유지한다.

`/tmp`의 이전 응답 비교 파일이나 테스트 로그는 새 환경에서 없을 수 있다.
재개에 필요한 계약·사례·회귀 검사는 저장소의 코드와 문서·테스트를 기준으로 한다.

관계 탐지·성립 판정·실제 세력/통근 영향을 계속 분리한다.
최종 강도·손상률·계수 추정·작공/LLM 연구는 재개 범위에 포함하지 않는다.

## 다음 채팅에서 사용할 요청 예시

> `docs/current_work_handoff.md`와 `docs/README.md`를 읽고 현재 main의 작업을
> 이어서 진행해줘. 우선 conditional의 규칙 근거와 의미부터 점검하고,
> 상태 유지 여부와 표시 명칭의 정리안을 제시해줘. 기존 변경을 다시 적용하거나
> 환경을 게시하지 마.
