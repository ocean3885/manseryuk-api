# 만세력 API (Manseryuk API)

문서 우선순위와 현재 개발 범위는 [docs 안내](docs/README.md)를 참고하세요.

> 동주 허실 v4: 통근 여부와 관련 합·충·형·파·천 기록을 분리합니다. 관계의 통근 영향은 미평가이며 자동 변허 판정은 하지 않습니다. 아래 이전 관계 반영 설명보다 [현행 계약](docs/root_relation_separation.md)을 우선합니다.

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

### `GET /analysis-summary` — 선택 전후 비교와 구조 요약

기존 사주 입력만 보내면 원국 구조를, `daewoon_index` 또는 `sewoon_year`를 추가하면 선택한 운에서 새로 생긴 관계를 요약합니다. `comparison`은 추가·유지 관계를 구분하고, `items`는 다자 구조·쌍별 관계·투간·글자별 동시 참여를 근거 ID에 연결합니다. 원본 정보는 `graph`에서 확인할 수 있습니다. 영향·길흉은 판정하지 않습니다. [요약 응답 계약](docs/analysis_summary_contract.md)을 참고하세요.

출생 날짜·시간은 모든 조회 경로에서 공통 검증합니다. 잘못된 날짜·시간 범위는 400, 달력 DB에 없는 평달·윤달 날짜는 404입니다. [입력 검증과 달력 제공 범위](docs/birth_input_validation.md)를 참고하세요.

오류 응답은 공통 `code`, `errors`로 필드·원인·허용 범위를 제공합니다. [오류 응답 계약](docs/api_errors.md)을 참고하세요.

현재 대운과 세운별 대운은 동일한 연도 선택 기준을 사용합니다. 실제 적용 구간은 `selection_start_year` 이상, `selection_end_year_exclusive` 미만입니다. [대운 선택 기준](docs/daewoon_selection_contract.md)을 참고하세요.

### `GET /cycle-analysis` — 선택한 대운·세운 연결

기존 사주 입력에 `daewoon_index` 또는 `sewoon_year` 중 하나를 추가합니다. 대운은 원국+대운 10글자, 세운은 원국+해당 대운+세운 12글자를 반환합니다. 첫 대운 이전에는 원국+세운 10글자입니다. 운의 기본 속성·지장간과 **원국↔대운·원국↔세운·대운↔세운의 쌍별·다자 관계 후보 및 투간**을 제공합니다. 관계 성립·통근 영향은 미평가입니다. 연도 단위 선택이며 정밀 교운 날짜·입춘 시각을 판정하지 않습니다. [선택·기간 계약](docs/cycle_analysis_contract.md)을 참고하세요.

### `GET /character-details` — 글자별 통합 정보

`GET /`와 같은 생년월일·시간·양음력·성별 파라미터를 받습니다. 원국 8글자의 기본 속성·지장간·통근·투간·관계를 `characters`, `relations`, `contexts`로 통합 제공합니다. ID에 소속을 포함하여 이후 대운·세운 어댑터를 확장할 수 있으며, 현재 대운·세운 관계는 미평가입니다. [응답 및 확장 계약](docs/character_details_contract.md)을 참고하세요.

### `GET /` - 사주 만세력 및 AI 분석 데이터 조회

#### 요청 파라미터 (Query Parameters)

| 파라미터 | 타입 | 필수 여부 | 기본값 | 설명 | 예시 |
| :--- | :--- | :---: | :---: | :--- | :--- |
| `year` | `int` | **필수** | - | 태어난 연도 (현재 DB 양력 1900~2100, 음력은 레코드 기준) | `1995` |
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

### `GET /relation-index` - 원국 8글자 관계 조회 (초안)

`GET /`과 같은 `year`, `month`, `day`, `hour`, `min`, `sl`, `gen` 파라미터를 받습니다.

```http
GET http://localhost:8000/relation-index?year=1995&month=5&day=12&hour=14&min=30&sl=sol&gen=남
```

응답에는 `schema_version: "1.7-draft"`, 위치별 여덟 글자의 `characters`, 관계 본문 `relations`, 지원 범위를 설명하는 `coverage`가 있습니다. 각 글자의 `relation_ids`는 관계 본문을 참조합니다. `cross_layer:transmission:*`은 지장간과 실제 천간 글자가 일치해 투출된 **위치별 사실**입니다. 천간의 `stem_state`에는 동주 통근 여부 `has_same_pillar_root`, 원상태·현재상태·위치 가중치 없는 점수·뿌리 지지와 별도 `external_support_score / external_support_branch_ids`를 담습니다. `root_scope: same_pillar_only`는 허실이 **동주 지지**로 판정됐음을 명시합니다. 타주 지원은 허투·실 판정에 합산하지 않습니다. 통근 점수가 양수이면 실이며, 점수 크기는 뿌리 강도 정보로 별도 표시합니다. 통근 강도 계수는 잠정값이며 투간 사실과 구분합니다. 관계로 통근 점수를 자동 제외하거나 변허로 바꾸지 않고 영향은 미평가로 제공합니다. `coverage.detected_only_relation_ids`는 후보만 발견하고 성립 여부를 아직 판정하지 않은 관계 ID입니다. `coverage.not_evaluated_mechanisms`는 현 규칙 범위 밖의 기전을 기록합니다. 관계의 `activation_status`는 탐지·성립 상태이며 세력 변화량이나 피해 확정값이 아닙니다. 이 경로는 기존 원국 분석의 결과로 조회 자료를 만들며, 기존 `GET /` 응답 형식에는 동주 통근 여부 필드가 추가됩니다. [8글자 관계 조회 계약](docs/character_relation_index_contract.md)에 지원 유형과 미지원 범위를 기록했습니다.

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

`details[기둥].branch.jijanggan/transmitted/hidden`은 지지 세력 계산과 같은 상세 지장간 표를 기준으로 합니다. 같은 지장간 글자가 천간의 두 위치에 보이면 `transmitted`에도 위치별 두 항목이 나옵니다. 기존 첫 위치만 표시하던 응답과 결과가 달라질 수 있으며, 투출 사실은 천간의 실·허 판정과 구분합니다.

`details[기둥].stem.score/status/root_info`는 현재 **동주 지지 기준**입니다. `same_pillar_root_exists`는 동주 통근 유무이며, `score`는 위치 가중치를 곱하지 않은 동주 계수입니다. 양의 점수는 크기에 관계없이 실이며, `0`은 허투입니다. 다른 세 지지의 기존 가중 지원은 `external_support_score/external_support_info`로 별도 표시됩니다. 동주 뿌리가 없으면 타주 지원이 있어도 허투입니다. 통근 점수를 입력으로 사용하는 `advanced_analysis.five_elements.scores`도 이전 전주 합산 방식과 값이 달라질 수 있습니다.

`analysis.summary.total_energy_balance`는 동주 통근/무근 개수만 알리고 원국 전체 신강·신약은 미판정으로 표시합니다. 동주 통근이 여러 천간에 있다는 사실만으로 전체 세력을 단정하지 않습니다.

허실의 관계 반영에서는 `active`인 충·천·형만 뿌리 영향으로 봅니다. 격위 자형의 `candidate_only`는 뿌리 점수에서 제외하지 않습니다. 실·허투·변허의 기존 점수 기준과 뿌리 전체 제외 방식은 잠정 모델입니다.

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

#### 4. `xu_shi_dynamics` (동주 통근과 관계 기록)

현행 규칙은 `4.0.0`, 범위는 `same_pillar_only`입니다. 동주 통근 계수가 양수이면 실, 0이면 허투입니다. 타주 지원은 별도 정보이며 통근 점수에 더하지 않습니다.

- `pillars[기둥].root_evidence`: 동주 통근 근거
- `related_interactions`: 통근 유무와 별개로 그 지지가 참여하는 관계와 원본 상태
- `root_impact_status: not_evaluated`, `root_impact_score: null`: 통근 영향 미평가
- `effective_score`: 호환용으로 원점수를 유지하며 검증된 무손상 점수가 아님
- `current_status == original_status`, `is_transformed=false`: 관계로 자동 변허 전환하지 않음
- `impact_groups`, `excluded_root_pillars`: 현행에서는 비어 있으며 영향 없음의 확정값이 아님

[현행 통근·관계 계약](docs/root_relation_separation.md)을 참고하세요. 전주 v1은 명시적 회귀 옵션으로만 유지합니다. [이전 README의 수치·상태 전이 사례](docs/archive/strength-research/xu_shi_legacy_reference.md)는 보관 자료입니다.

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
