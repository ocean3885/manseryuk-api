# 만세력 API (Manseryuk API)

전통 사주명리학 및 맹파명리(盲派命理) 이론을 기반으로, AI 사주 상담 서비스 및 운세 플랫폼에 최적화된 고도화 만세력 분석 데이터를 제공하는 FastAPI 백엔드 서비스입니다.

---

## 🚀 빠른 시작 (Quick Start)

### 1. 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
.\venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 서버 실행
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API 엔드포인트 규격 (API Reference)

### `GET /` - 사주 만세력 및 AI 분석 데이터 조회

#### 요청 파라미터 (Query Parameters)

| 파라미터 | 타입 | 필수 여부 | 기본값 | 설명 | 예시 |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `year` | `int` | **필수** | - | 태어난 연도 (1900 ~ 2050) | `1995` |
| `month` | `str` | **필수** | - | 태어난 월 (1~12 또는 '01'~'12') | `5` 또는 `05` |
| `day` | `str` | **필수** | - | 태어난 일 (1~31 또는 '01'~'31') | `12` 또는 `12` |
| `hour` | `int` | **필수** | - | 태어난 시 (0 ~ 23) | `14` |
| `min` | `int` | **필수** | - | 태어난 분 (0 ~ 59) | `30` |
| `sl` | `str` | **필수** | - | 양력/음력 구분 (`sol`: 양력, `lun`: 음력 평달, `lun_y`: 음력 윤달) | `sol` |
| `gen` | `str` | **필수** | - | 성별 (`남` 또는 `여`) | `남` |

##### 요청 예시 (Example Request)
```http
GET http://localhost:8000/?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남
```

---

## 📊 응답 데이터 구조 (Response Structure)

응답은 도메인별로 체계적으로 그룹화되어 제공됩니다:

```json
{
  "calendar": { ... },
  "four_pillars": { ... },
  "ten_gods": { ... },
  "daewoon": { ... },
  "cycles": { ... },
  "meta": { ... },
  "analysis": { ... },
  "advanced_analysis": { ... }
}
```

### 1. `calendar` (달력 일자 정보)
- `solar`: 양력 일자 (`year`, `month`, `day`)
- `lunar`: 음력 일자 (`year`, `month`, `day`)
- `solar_plan`: 양력 절기/기념일 정보
- `lunar_plan`: 음력 절기/기념일 정보

### 2. `four_pillars` (사주 4주 완성형 원국)
년주(`year`), 월주(`month`), 일주(`day`), 시주(`hour`)로 구성되며 각 기둥은 프론트엔드 원국표 렌더링에 필요한 모든 메타데이터(천간/지지 오행·음양·색상·십신, 12운성, 지장간 상세, 기둥별 신살)를 일원화하여 포함합니다.
```json
{
  "year": {
    "gan": { "kr": "을", "ch": "乙", "element": "목", "element_ch": "木", "yin_yang": "음", "color": "#2E7D32", "ten_god": "식신" },
    "ji": { "kr": "해", "ch": "亥", "element": "수", "element_ch": "水", "yin_yang": "음", "color": "#1565C0", "ten_god": "겁재" },
    "unseong": "제왕",
    "unseong_self": "사",
    "jijanggan": [
      { "kr": "무", "ch": "戊", "element": "토", "element_ch": "土", "yin_yang": "양", "color": "#E65100", "ten_god": "정관", "type": "초기", "ratio": "7/30" },
      { "kr": "갑", "ch": "甲", "element": "목", "element_ch": "木", "yin_yang": "양", "color": "#2E7D32", "ten_god": "상관", "type": "중기", "ratio": "7/30" },
      { "kr": "임", "ch": "壬", "element": "수", "element_ch": "水", "yin_yang": "양", "color": "#1565C0", "ten_god": "겁재", "type": "정기", "ratio": "16/30" }
    ],
    "special_stars": []
  },
  "month": { ... },
  "day": { ... },
  "hour": { ... }
}
```

### 3. `ten_gods` (십신 정보 - 하위 호환)
원국 8글자 각각의 십신 및 일간(`day_gan`: "일간")을 제공합니다.
- `year_gan`, `year_ji`, `month_gan`, `month_ji`, `day_gan`, `day_ji`, `time_gan`, `time_ji`

### 4. `daewoon` (대운 정보)
10년 주기의 대운 흐름을 제공합니다.
- `direction`: 대운 순행/역행 여부 (`"순행"` 또는 `"역행"`)
- `start_age`: 대운 시작 나이 (대운수, 예: `2.3`)
- `current`: 현재 나이에 해당하는 대운 객체
  - `index`, `year`, `age`, `gan`, `ji`, `gan_detail`, `ji_detail`, `gan_ten_god` (천간 십신), `ji_ten_god` (지지 십신), `unseong` (12운성), `start_age`, `end_age`, `start_year`, `end_year`
- `list`: 10개 대운 항목 전체 배열

### 5. `cycles` (세운 및 소운)
프론트엔드 타임라인/카드 UI에 최적화된 객체 리스트 형식으로 제공됩니다.
- `future_100`: 향후 100년간의 세운 상세 리스트 (`year`, `age`, `gan`, `ji`, `unseong`)
- `baby_10`: 1세부터 10세까지의 소운 리스트 (`year`, `age`, `gan`, `ji`, `unseong`)

### 6. `meta` (메타 정보)
- `gender`: 성별 (`남` / `여`)
- `ddi`: 십이지 띠 (예: `돼지`)
- `birth_date_solar`: 양력 생년월일 (`YYYY-MM-DD`)
- `birth_time`: 출생 시간 (`HH:MM`)
- `age_man`: 만 나이
- `age_korean`: 세는 나이
- `birth_weekday`: 태어난 요일 (예: `금요일`)

### 7. `analysis` (전통 명리 분석 요약)
- `summary`: 천간/지지 상호작용 및 오행 균형 요약 문장 리스트
- `details`: 신살, 형충회합 등의 세부 데이터

---

## 🧠 `advanced_analysis` (AI 상담 특화 고급 명리 분석)

AI 챗봇/상담 에이전트가 풍부한 해석 프롬프트와 정밀한 명리학적 근거를 바탕으로 사주를 풀이할 수 있도록 맹파명리 및 고급 역학 엔진을 통합 제공합니다.

`branch_dynamics`는 지지 간 작용 분석의 초기 결과입니다. `branch_strengths`는 월령·지장간·동주 천간·다른 지지의 배경 효과를 분리해 네 지지의 상대 세력을 보여줍니다. `pairwise`는 여섯 지지 쌍의 합·충·형·파·천과 오행 생·극을 보존하고, 관계마다 양쪽 잠재 작용량(`force`), 받는 효과(`effect_received`), 관계 전 세력 우세(`dominance`), 해당 관계의 작용량 우세(`force_dominance`), 작용 종류에 따른 양쪽 역할(`roles`)을 제공합니다. `groups`에는 삼합·방합 참여 위치를 담되 아직 작용량은 매기지 않습니다. 이 수치는 검증된 절대 세력이나 현실 피해량이 아닌 `uncalibrated_relative_model_index`이며, 계산 규칙은 [지지 작용 분석 명세](docs/branch_dynamics_v2.md)에 있습니다. 기존 `bin_zhu_dynamics`는 호환을 위해 제공되며 새 지지 작용 계산의 근거로 쓰지 않습니다.

`branch_dynamics.groups[]`의 `candidate_element`는 삼합·방합의 후보 오행이고, `transformed_element`는 실제 합화 판정 전에는 `null`입니다. 기존 `element`는 호환을 위한 후보 오행 별칭입니다.

삼합·방합의 `formation_evidence[]`에는 성립 조합별 참여 지지의 관계 전 세력(`power_before`), 상대 비중(`capacity_share`), 구조적 자리, 겹치는 육합·반합의 참조가 들어갑니다. 비중은 참여 지지 간 비교값이며 실제 합 작용량이나 세력 증가분은 아닙니다. 그룹의 `status`는 작용 계수를 확정하기 전까지 `not_scored`입니다.

삼합의 `directional_candidates`는 중신을 향한 구조상 방향 후보입니다. 방합은 개별 방향을 `undetermined`로 표시합니다. 두 경우 모두 세력 비중만으로 실제 견인 방향·합화 성립을 확정하지 않습니다. 조합별 후보와 중첩 처리는 [관계 규칙표](docs/mangpa_relation_rulebook.md)에 설명합니다.

`branch_strengths[].ambient_evidence`와 `pairwise[].context_evidence`에는 주변 지지의 생·극 보정과 같은 쌍의 합·충·형 등 관계 상태를 별도 근거로 기록합니다. 생·극 규칙에 명시된 억제는 보정량 0으로 반영합니다. 합이 조건부라는 이유만으로 별개의 생·극 보정을 자동 제거하지 않습니다.

합·충·형·파·천, 천간 관계, 동주 자합 후보와 실험적 작용 계수의 실행 규칙은 [단일 관계 규칙 모듈](services/relation_rules.py)에서 관리합니다. 맹파 해석상의 성립 조건과 검토 상태는 [관계 규칙표](docs/mangpa_relation_rulebook.md)에 기록합니다.

조합별 작용 규칙은 현재 子午·子卯·卯午·午酉·辰酉부터 적용됩니다. `pairwise[].relations[]`의 `directional_coefficients`, `directional_mechanisms`, `activation_status`로 후보의 방향과 상태를 확인할 수 있습니다. 파·충·천·쌍별 지세형은 해당 두 지지가 있으면 거리와 무관하게 `active`이며, 육합은 인접 충 개입이 없을 때 `active`입니다. 같은 쌍의 생·극은 독립 작용과 주변 세력 보정에서 억제됩니다. `active`는 관계 성립 상태이고 `force`와 v3 `interaction_intensity`는 미보정 잠재 강도입니다. 실제 세력 증감인 `applied_power_delta`는 아직 계산하지 않습니다.

### 구성 요소:

#### 1. `five_elements` (오행 분포 및 세력 분석)
- `counts`: 목/화/토/금/수 글자 수 카운트 (`{"목": 2, "화": 1, "토": 2, "금": 1, "수": 2}`)
- `percentages`: 오행별 백분율 (%)
- `scores`: 월령 및 지지 가중치가 반영된 정밀 세력 점수
- `dominant`: 강한 주도 오행 리스트
- `deficient`: 부족하거나 결핍된 오행 리스트
- `summary`: 오행 구족 및 편중 요약 설명

#### 2. `special_stars` (주요 신살 및 길신/흉신)
천을귀인(天乙貴人), 문창귀인, 도화살, 역마살, 화개살, 백호대살, 괴강살, 양인살, 홍염살을 정확히 추출합니다.
- `name`: 신살 명칭
- `pillar`: 위치한 기둥 (`년주`, `월주`, `일주`, `시주`)
- `position`: `천간` 또는 `지지`
- `char`: 해당 한자
- `type`: `길신`, `흉신`, `특수성`
- `description`: 상담용 신살 해석 가이드

#### 3. `interactions` (합·충·형·천·파 6기둥 페어 매트릭스)
년-월, 월-일, 일-시, 년-일, 년-시, 월-시 총 6개 기둥 간의 인접성 가중치 및 상호작용 분석:
- `climate`: 사주 기후 (`조화 안정형`, `역동 발전형`, `긴장 극복형`, `복합형`)
- `tension_score`: 충/형/파/해로 인한 긴장·변동 지수
- `harmony_score`: 천간합·육합·반합·삼합·방합의 잠정 점수 합계. 활성 다자 합의 같은 성립 조합에 포함된 육합·반합은 한 번만 집계
- `matrix`: 각 상호작용 항목의 세부 정보 (가중치, 합 후보 오행, 설명)
- `rule_version`: `"1.3.0"`. 다자 합에 포함된 쌍의 조화 점수 중복 집계를 방지한 버전입니다.

각 `matrix[]` 항목에는 다음 참조 정보가 포함됩니다.

| 필드 | 의미 |
| --- | --- |
| `relation_id` | 같은 원국·규칙 버전에서 관계 종류·이름·참여 위치로 결정되는 식별자. 목록 순서나 점수에 의존하지 않음 |
| `relation_scope` | 두 기둥 관계는 `pairwise`, 삼합·방합은 `group` |
| `participants` | 실제 참여 기둥을 년·월·일·시 순서로 나열 |
| `formations` | 다자 관계를 성립시키는 서로 다른 세 지지의 위치 조합. 쌍별 관계는 빈 목록 |
| `candidate_element` | 육합·반합·삼합·방합·천간합의 관습적 오행 후보. 실제 합화 판정이 아님 |
| `transformed_element` | 실제 합화가 별도로 확인된 경우의 오행. 현재 판정기에서는 `null` |
| `score` | 관계 자체의 잠정 점수. 다자 합에 포함된 쌍에서도 보존 |
| `score_contribution` | `harmony_score` 또는 `tension_score` 집계에 반영한 점수 |
| `score_covered_by` | 다자 합이 쌍의 조화 점수를 포함할 때 해당 다자 관계의 `relation_id`; 그 외에는 `null` |

예를 들어 지지가 `亥卯未亥`인 삼합의 참여 정보는 다음과 같습니다(발췌).

```json
{
  "relation_scope": "group",
  "from_pillar": "all",
  "to_pillar": "all",
  "participants": ["year", "month", "day", "hour"],
  "formations": [
    ["year", "month", "day"],
    ["month", "day", "hour"]
  ]
}
```

기존 `from_pillar`/`to_pillar`의 `all`은 호환용으로 유지합니다. 참여 위치는 `participants`로 확인합니다. 성립 조합이 여러 개여도 동일 삼합·방합의 조화 점수는 한 번만 가산합니다. 기존 다자 관계의 `is_adjacent`는 참여 위치 전체의 범위가 2 이내인지를 뜻하며, 개별 성립 조합의 인접성을 뜻하지 않습니다.

`巳午未寅`에서 午未 육합은 `score: 1.5`인 후보로 남지만, 巳午未 방합의 성립 조합에 포함되어 `score_contribution: 0`입니다. 해당 방합 3.5점과 조합 밖 寅午 반합 0.91점만 조화 총점에 반영합니다(`harmony_score: 4.4`, 소수 첫째 자리 반올림). 이 중복 집계 방지는 프로젝트의 점수 정책이며 실제 합화·작용의 확정 판정이 아닙니다.

반복 지지는 글자가 같아도 위치별로 별도 관계입니다. `寅午午酉`의 년–월·년–일 반합, `子丑丑子`의 네 육합 쌍, 반복 상대의 형을 모두 반환합니다. 기존 상세 분석의 단일 `six_haps`는 유지하고 전체 육합 목록은 `six_haps_all`로 제공합니다. 충·천·파와 천간 합·충은 기존에도 상대 위치를 순회하므로 해당 수집 규칙을 유지했습니다.

**누락 수정에 따른 결과 변경:** 관계 점수와 이를 사용하는 허실·빈주 결과가 일부 달라질 수 있습니다. 수정 전 합성 입력 200건과 비교했을 때 31건의 긴장/조화 점수가 변했고, 2건에서 천간 3개의 허실 판정이 바뀌었습니다. 아래 변경은 누락된 형 복원에 따른 것으로, 허실 감점 계수나 임계값 변경이 아닙니다.

| 천간 / 지지(년·월·일·시 순) | 위치 | 수정 전 → 후 |
| --- | --- | --- |
| 癸甲乙丁 / 巳申巳子 | 시간 | 실 → 변허 |
| 丁庚丙丁 / 巳午午午 | 일간·시간 | 실 → 변허 |

#### 4. `xu_shi_dynamics` (허와 실 및 실자변허 實者變虛)
원국의 통근 점수와 지지 충·형·천 관계를 이용한 규칙 기반 분석입니다. `original_status`와 `current_status`는 **같은 원국의 관계 반영 전후**를 뜻하며, 대운·세운에 따른 시기별 변화가 아닙니다.

| 필드 | 의미 |
| --- | --- |
| `analysis_scope` | `"natal"`: 원국 분석 |
| `rule_version` | `"1.0.0"`: 기존 판정 규칙을 최초로 명시한 버전 |
| `pillars` | `year`, `month`, `day`, `hour` 천간별 분석 |
| `shared_roots` | 둘 이상의 천간이 공유하는 지지별 뿌리와 각 천간의 기여도·최종 상태 |
| `impact_groups` | 충·형·천 관계별로 기여도가 제외된 뿌리 위치와 영향을 받은 천간 목록 |
| `real_count` | 관계 반영 후 실(實)인 천간 수 |
| `transformed_empty_count` | 실에서 변허(變虛)로 분류된 천간 수 |
| `hollow_penetrate_count` | 허투(虛透)인 천간 수 |
| `weak_count` | 허(虛)인 천간 수. 네 종류의 개수 합은 4 |
| `overall_status` | 실제 상태 분포와 통근에 영향을 준 관계 요약 |

`pillars.*`의 기존 `position`, `char`, `ten_star`, `score`, `original_status`, `current_status`, `is_transformed`, `reason`, `meaning` 필드는 유지합니다. 동일한 통근·관계 입력에서 허실 점수와 판정 규칙은 기존과 동일하며, 설명 문구는 구조와 근거 중심으로 변경했습니다. 관계 수집의 누락 수정으로 입력 근거가 달라지는 경우는 위 변경 내역을 참고하세요.

- `score`: 관계 반영 **전** 통근 총점. 확률이나 정규화된 0~1 점수가 아닙니다.
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
- `root_structure.remaining_support`: 잔여 점수만으로 분류한 `none`(0), `below_threshold`(0 초과 0.5 미만), `meets_threshold`(0.5 이상). 변화 이력을 포함하는 `current_status`와 구별합니다.

`shared_roots[]`는 `root_pillar`, `branch_char`, `is_affected`, `interactions`, `dependents`를 제공합니다. `dependents[]`의 `stem_pillar`, `score`, `effective_score`, `current_status`로 같은 뿌리가 각 천간에 기여한 정도와 최종 결과를 확인합니다. 같은 지지 글자가 반복되어도 **위치가 다르면 다른 뿌리**입니다.

`impact_groups[]`는 `interaction`, `affected_root_pillars`, `affected_stem_pillars`를 제공합니다. 같은 관계의 양쪽에 뿌리가 있거나 여러 천간이 연결돼도 위치 목록은 중복 집계하지 않습니다. 이는 기존 근거의 영향 범위를 모은 것으로, 특정 관계 하나가 단독으로 변허를 일으켰다는 판정이나 새로운 감점이 아닙니다.

예를 들어 년간·월간이 월지 뿌리를 공유하고 해당 뿌리가 제외되었을 때, 년간은 일지에 잔여 점수 `0.6`이 있어 실을 유지하고 월간은 시지에 `0.3`만 남아 변허로 분류될 수 있습니다. `overall_status`는 공통 뿌리를 먼저 설명하고 각 천간의 잔존 기반과 결과를 이어서 요약합니다.

**v1 판정 규칙과 한계**

1. 원점수가 `0.5` 이상이면 실, `0`이면 허투, 그 사이이면 허입니다.
2. 지지 충·형·천에 참여한 양쪽 지지의 뿌리 기여도를 모두 `0`으로 취급합니다. 관계 유형별 손상률, 거리별 감점, 합에 따른 회복, 파는 반영하지 않습니다.
3. 원래 실이고 영향을 받은 뿌리가 있을 때만 잔여 점수를 검사합니다. `0.5` 미만이면 변허, 이상이면 실을 유지합니다.
4. 원래 허·허투는 분류를 유지합니다. 따라서 원래 허인 천간의 잔여 점수가 `0`이어도 허투나 변허로 바뀌지 않습니다.
5. 원점수와 개별 뿌리 점수는 상위 통근 계산기에서 각각 소수 둘째 자리로 반올림합니다. 이 때문에 뿌리 점수 합과 원점수가 미세하게 다를 수 있습니다. 기존 판정 호환성을 위해 잔여 합산값은 추가 반올림 없이 비교·반환합니다.

**수치·상태 계약 (`rule_version: "1.0.0"` 유지)**

내부 통근 계산은 Python `float`를 사용합니다. 총점은 반올림 전 개별 기여도를 합친 뒤 `round(total, 2)`로 반환하고, 뿌리별 점수는 각각 `round(contribution, 2)`로 반환합니다. 허실의 최초 분류는 반환된 총점으로 판정하고, 잔여 점수는 반환된 개별 점수를 년·월·일·시 순서로 합산합니다. epsilon 보정이나 판정 직전 반올림은 적용하지 않습니다. 예를 들어 계산값 `0.49999999999999994`는 `0.5` 미만입니다. 화면에서 소수 자릿수를 줄여 표시하더라도 상태를 표시값으로 재계산하지 않습니다.

| 최초 상태 | 관계 반영 조건 | 최종 상태 | `transition_code` |
| --- | --- | --- | --- |
| 실 | 제외된 뿌리 없음 | 실 유지(잔여 점수로 재분류하지 않음) | `maintained` |
| 실 | 제외된 뿌리 있음, 잔여 점수 ≥ 0.5 | 실 | `maintained` |
| 실 | 제외된 뿌리 있음, 잔여 점수 < 0.5 | 변허 | `real_to_empty` |
| 허 | 관계 유무·잔여 점수와 무관 | 허 | `maintained` |
| 허투 | 관계 유무·잔여 점수와 무관 | 허투 | `maintained` |

`remaining_support`는 위 전이표와 독립적으로 잔여 점수를 나타냅니다. 따라서 `current_status: "허(虛)"`와 `remaining_support: "none"`이 함께 나올 수 있습니다. 점수 정밀도, 임계값 또는 전이 규칙 변경은 향후 판정 버전 변경으로 다루며, 이번 구조 정보 추가는 기존 판정 버전을 유지합니다.

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

#### 5. `bin_zhu_dynamics` (빈주 이론 賓主理論)
사회적 환경(년/월: 賓)과 개인 영역(일/시: 主) 사이의 관계 유형, 참여 구조 및 체용(體用)·취용(取用) 역학을 분석합니다.

- `rule_version`: `"3.0.0"`. 맹파명리 체용·취용 원리에 기반한 십성별 취용 메커니즘(`일간합재`, `합취`, `제용`, `환경압박`, `군겁쟁재` 등) 및 역학 벡터(`host_takes_guest`, `guest_pressures_host`, `mutual_cooperation`, `independent_parallel`), 거리 가중치 및 다자 결합도 연동이 완비된 버전입니다.
- `interaction_scope`: `"pairwise"`. **점수 계산**은 기둥 쌍별 관계에 한정됩니다.
- `pairwise_scores`: 
  - `combination`: 거리 가중치가 반영된 합 관계 점수 (천간합 1.8, 육합 1.5, 반합 1.2 등 × 가중치)
  - `conflict`: 거리 가중치가 반영된 대립 관계 점수 (충 2.0, 천간충 1.5, 형 1.5, 천 1.5 등 × 가중치)
  - `unweighted_combination`: 가중치 없는 기본 합 점수 (합마다 2.0점)
  - `unweighted_conflict`: 가중치 없는 기본 대립 점수 (충·형·천마다 1.5점)
- `group_cohesion_score`: 빈-주를 연계하는 삼합·방합의 다자 결합 점수 합계. 기둥 참여도 기반 공식 산출 ($$\text{Base} \times \frac{|G| \times |H|}{|P|}$$)
- `guest_host_links`: 점수에 반영한 쌍별 관계의 `relation_id`, `type`, `detail`, `target_guest`, `source_host`, `mechanism`, `flow_direction`, `weight`.
  - `mechanism`: `일간합재(合財)`, `합취(合取)`, `제용(制用)`, `환경압박(沖破)`, `군겁쟁재(爭財)`, `재관마찰`, `대립조율`, `상호유대(有情)` 등
  - `flow_direction`: `host_takes_guest` (주➔빈), `guest_pressures_host` (빈➔주), `mutual_cooperation` (상호협력), `neutral` (중립)
- `excluded_interactions`: 점수에서 제외한 다자 관계, 미가산 쌍별 관계(파 등) 또는 유효하지 않은 위치 항목의 `relation_id`, `participants`, `category`, `type`, `name`, `from_pillar`, `to_pillar`, `reason_code`.
- `group_connections`: 참여 정보가 있는 다자 관계의 `relation_id`, `type`, `participants`, `guest_participants`, `host_participants`, `cohesion_score`, `included_in_score: false`, `description`.
- `guest_structure`: 빈(외계/사회)의 주요 세력 및 십신. 
  - `scope`: `"년주(국가/조상/대외환경) + 월주(직장/사회활동/사회환경)"`
  - `dominant_forces`: 빈 영역에 포진한 주요 십신 세력 목록 (재관, 인성, 식상 등)
- `host_structure`: 주(자아/가정)의 주요 수단 및 십신. 
  - `scope`: `"일주(자아/배우자/개인영역) + 시주(수단/도구/말년/귀숙처)"`
  - `dominant_means`: 주 영역에 위치한 주요 수단·도구 십신 목록 (식상, 비겁, 인성 등)
- `control_flow`:
  - `direction`: `합 관계 우세`, `충·형·천 관계 우세`, `다자 합 결합(삼합/방합) 형성`, `다자 합 결합 및 대립(충·형·천) 공존`, `합 관계 우세 (다자 합 결합 포함)`, `다자 합 결합 및 동률 관계`, `관계 점수 동률`, `평가 가능한 빈-주 통로 없음`
  - `dominant_interaction`: 기계 판독용 관계 식별자 (`combination_dominant`, `conflict_dominant`, `group_bridging`, `group_bridging_with_conflict`, `group_bridging_with_combination`, `group_bridging_balanced`, `balanced`, `none`)
  - `vector`: 한국어 역학 벡터 명칭 (`주 ➔ 빈 (자원 취용/주도형)`, `빈 ➔ 주 (환경 조율/적응형)`, `주 ⇄ 빈 (상호 연대/협력형)`, `주 ∥ 빈 (독립 영역 유지형)`)
  - `vector_code`: 기계 판독용 벡터 코드 (`host_takes_guest`, `guest_pressures_host`, `mutual_cooperation`, `independent_parallel`)
  - `acquisition_summary`: 체용 및 취용 관점에서의 동력 요약 해설
  - `summary_meaning`: 어떤 관계가 형성/우세한지 가중치 점수 및 결합도를 포함하여 상세 설명
  - `career_advice`: 호환용 키 (전통적 상징 및 한계 기술)
  - `interpretation_notes`: 신규 권장 안내 필드 (기둥 간 거리와 결합 구조의 상징적 의미 및 판정 주의사항 기술)

삼합·방합은 전체 `interactions.matrix`에 보존되며 `group_connections`와 `group_cohesion_score`를 통해 빈·주의 공동 결합도를 명확히 정량화합니다. 또한 십성 역학에 따른 `vector`와 `mechanism`을 제공하여 맹파명리의 핵심인 "내가 사회의 재관을 취하는가(주➔빈), 외부 환경의 규율과 압박에 적응하는가(빈➔주), 상호 협력하는가"를 명확히 판별합니다.

#### 6. `ai_consultation_prompts` (AI 즉시 주입용 상담 스크립트)
LLM 시스템 프롬프트 또는 RAG 컨텍스트에 그대로 주입할 수 있는 핵심 요약 불릿 리스트를 한국어로 생성하여 반환합니다.

```json
"ai_consultation_prompts": [
  "【오행 분포】 목화토금수 5개 오행이 사주에 골고루 갖추어진 원만한 오행구족(五行具足) 구조입니다.",
  "【주요 신살 및 길신】 천을귀인(월지), 역마살(월지), 천을귀인(일지)",
  "【사주 기후】 긴장과 조화가 공존하는 복합형 (긴장도: 3.5, 조화도: 3.0)",
  "【원국 허실】 원국 천간 4자의 관계 반영 후 분포는 실(實) 3개, 변허(變虛) 1개입니다. (뿌리별 근거 요약 생략) 원국의 관계 반영 전후 비교이며, 대운·세운에 따른 시기별 변화가 아닙니다. 십성의 상징 해석은 참고로 구분하고, 능력·성과·직업 적합성으로 단정하지 마세요.",
  "【빈주 관계】 다자 합 결합 및 대립(충·형·천) 공존: 빈과 주를 잇는 다자 합(결합도: 3.0점)이 형성되어 있으며, 동시에 쌍별 대립 점수(1.2점)가 합 점수(0.0점)보다 높은 상태로 공존합니다.",
  "【빈주 역학 흐름】 주 ➔ 빈 (자원 취용/주도형): 개인의 역량과 수단(일·시주)을 바탕으로 외부 사회의 기회와 재관(년·월주)을 내 영역으로 견인·취용하는 동력이 우세합니다.",
  "【빈주 해석 참고】 빈은 사회적 환경(국가·직장), 주는 개인 영역(자아·수단)의 상징입니다. 관계 집계는 기둥 간 거리와 결합 구조를 나타내며, 직업 적합성이나 성과를 단정하지 않습니다.",
  "【빈주 계산 범위】 쌍별 관계만 점수에 반영했습니다. 다자 관계 또는 위치를 확인할 수 없거나 미가산된 관계 1건은 계산에서 제외했으므로 빈주 점수의 근거로 사용하지 마세요.",
  "【빈주 다자 관계】 삼합(三合) 참여 위치: 년, 월, 일. 빈과 주가 함께 참여하는 다자 관계입니다. (삼합 木국, 결합도: 3.0점)",
  "【주-빈 통로】 빈(년 편관)과 주(시 식신) 사이에 천간충(天干沖) 관계가 있습니다. (작용: 제용(制用))"
]
```

---

## ⚠️ 오류 응답 형식 (Error Handling)

요청 파라미터가 누락되었거나 유효하지 않은 경우 `400 Bad Request` 또는 `422 Unprocessable Entity`와 함께 안내 메시지를 반환합니다.

```json
{
  "status": "error",
  "message": "필수 입력 값이 누락되었거나 형식이 올바르지 않습니다.",
  "correct_usage": "아래와 같은 형식으로 요청을 보내주세요.",
  "example": "/?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남",
  "required_fields": {
    "year": "int (연도)",
    "month": "str (월, 예: '5')",
    "day": "str (일, 예: '12')",
    "hour": "int (시간, 0-23)",
    "min": "int (분, 0-59)",
    "sl": "str ('sol' ,'lun', 'lun_y')",
    "gen": "str ('남' , '여')"
  }
}
```
