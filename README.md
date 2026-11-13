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

| 화면에서 필요한 정보 | API |
| --- | --- |
| 달력·사용자 정보·원국 기본 표·대운/세운 선택 목록 | `GET /` |
| 원국 글자·통근·관계·자연어 설명 | `GET /character-details` |
| 선택한 대운/세운의 글자·관계·자연어 설명 | `GET /cycle-analysis` |
| 원국 관계의 독립 조회 | `GET /relation-index` |

2026-11-13: `GET /analysis-summary`는 제거되어 일반 404를 반환합니다.
전용 카드 묶음·표시 순서·추가/기존 비교는 다른 API로 이전하지 않았습니다.
기존 `GET /`의 `analysis.summary`는 유지합니다. 관계 설명은 상세 API의
`relations[ID].presentation`을 사용합니다.

출생 날짜·시간은 모든 조회 경로에서 공통 검증합니다. 잘못된 날짜·시간 범위는 400, 달력 DB에 없는 평달·윤달 날짜는 404입니다. [입력 검증과 달력 제공 범위](docs/birth_input_validation.md)를 참고하세요.

오류 응답은 공통 `code`, `errors`로 필드·원인·허용 범위를 제공합니다. [오류 응답 계약](docs/api_errors.md)을 참고하세요.

현재 대운과 세운별 대운은 동일한 연도 선택 기준을 사용합니다. 실제 적용 구간은 `selection_start_year` 이상, `selection_end_year_exclusive` 미만입니다. [대운 선택 기준](docs/daewoon_selection_contract.md)을 참고하세요.

### `GET /cycle-analysis` — 선택한 대운·세운 연결

기존 사주 입력에 `daewoon_index` 또는 `sewoon_year` 중 하나를 추가합니다. 대운은 원국+대운 10글자, 세운은 원국+해당 대운+세운 12글자를 반환합니다. 첫 대운 이전에는 원국+세운 10글자입니다. 운의 기본 속성·지장간과 **원국↔대운·원국↔세운·대운↔세운의 쌍별·다자 관계 후보 및 투간**을 제공합니다. 관계 성립·통근 영향은 미평가입니다. 연도 단위 선택이며 정밀 교운 날짜·입춘 시각을 판정하지 않습니다. [선택·기간 계약](docs/cycle_analysis_contract.md)을 참고하세요.

### `GET /character-details` — 글자별 통합 정보

`GET /`와 같은 생년월일·시간·양음력·성별 파라미터를 받습니다. 원국 8글자의 기본 속성·지장간·통근·투간·관계를 `characters`, `relations`, `contexts`로 통합 제공합니다. ID에 소속을 포함하여 이후 대운·세운 어댑터를 확장할 수 있으며, 현재 대운·세운 관계는 미평가입니다. [응답 및 확장 계약](docs/character_details_contract.md)을 참고하세요.

글자 상세와 화면 표시용 설명의 필드 선택·미평가 처리는
[프론트엔드 사용 기준](docs/character_details_contract.md#프론트엔드-사용-기준)을 따릅니다.

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
- `lunar`: 음력 일자 (`year`, `month`, `day`, `is_leap_month`). 윤달 여부는 입력 방식과 무관하게 DB 레코드에서 제공합니다.
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
- `start_age`: 날짜 단위 절기 간격으로 계산한 대운수 (예: `2.3`). 필요한 절기 자료가 없으면 `null`입니다.
- `start_age_status`: `calculated` 또는 `term_data_unavailable`
- `current`: `selection_year`에 해당하는 대운 객체
  - `index`, `year`, `age`, `age_basis`, `gan`, `ji`, `gan_detail`, `ji_detail`, `gan_ten_god` (천간 십신), `ji_ten_god` (지지 십신), `unseong` (12운성), `start_age`, `end_age`, `start_year`, `end_year`
  - `age`는 세는나이이며 `age_basis=counting_age`입니다. 기간 선택에 사용하지 않습니다.
- `list`: 계산 가능하면 10개 대운 항목. 절기 자료 부족이면 `[]`, `current=null`, `selection_status=unavailable`입니다.

`start_age`가 `null`이면 임의의 1세 시작으로 대체하지 않습니다. 소수 대운수와 기간 표시의
`start_age/end_age`는 기존 계산 기준을 유지하며 `current.age`의 세는나이와 구분합니다.
정밀 교운 시각을 계산한 값은 아닙니다.

### 5. `cycles` (세운과 어린 시절 세운)
프론트엔드 타임라인/카드 UI에 최적화된 객체 리스트 형식으로 제공됩니다.
- `future_100`: 출생연도부터 100년간의 세운 상세 리스트 (`year`, `age`, `age_basis`, `gan`, `ji`, `unseong`)
- `childhood_10`: 위 목록의 첫 10개. 1~10세의 세운이며 별도 소운 계산이 아닙니다.
- 모든 `age`는 `age_basis=counting_age`인 세는나이입니다.

2026-11-13 연동 변경: `baby_10`을 `childhood_10`으로 교체했습니다. 기존 필드명은
반환하지 않으므로 프론트엔드 참조를 변경해야 합니다. 출생 이전이나 DB 경계 때문에
대운을 선택할 수 없더라도 연도별 세운 목록은 제공합니다.

### 6. `meta` (메타 정보)
- `gender`: 성별 (`남` / `여`)
- `reference_date`: 나이·현재 대운 계산에 사용한 서버 기준 날짜 (`YYYY-MM-DD`)
- `ddi`: 십이지 띠 (예: `돼지`)
- `birth_date_solar`: 양력 생년월일 (`YYYY-MM-DD`)
- `birth_time`: 출생 시간 (`HH:MM`)
- `age_man`: 만 나이
- `age_korean`: 세는 나이
- `birth_weekday`: 태어난 요일 (예: `금요일`)

`age_man`은 만 나이, `age_korean`과 운 목록의 `age`는 세는나이입니다.
기존 `daewoon.current.age`의 연 나이(현재연도−출생연도)는 세는나이로 변경했습니다.
입력 날짜가 기준 날짜보다 미래인 경우 나이 수치가 음수가 될 수 있으며 출생 완료를 의미하지 않습니다.

오행 분포의 `counts/percentages`는 대표 오행의 글자 수 통계입니다.
`advanced_analysis.five_elements.distribution_basis=eight_visible_characters`,
`score_meaning=provisional_weighted_index`로 통계와 기존 잠정 가중 점수를 구분합니다.
`frequent_elements`는 대표 오행 3글자 이상 목록, `absent_elements`는 대표 오행 0개 목록이며
실제 세력 우세·지장간 오행 부재·보완 필요성의 판정으로 해석하지 않습니다.

### 7. `analysis` (전통 명리 분석 요약)
- `summary`: 천간·지지 관계 요약과 동주 통근/무근 개수.
- `details`: 년·월·일·시의 천간 통근, 지장간·투간, 글자별 관계와 자합.

`details`는 `year`, `month`, `day`, `hour`를 모두 요구하는 구체적인 응답 타입입니다.
관계 종류별 참여 글자·십성·관찰 근거까지 OpenAPI에 정의했습니다. 빈 배열·`null`과
원자료 키는 유지하며, 잘못된 필드·상태·위치를 응답 검증에서 거부합니다.

`details[기둥].branch.jijanggan/transmitted/hidden`은 지지 세력 계산과 같은 상세 지장간 표를 기준으로 합니다. 같은 지장간 글자가 천간의 두 위치에 보이면 `transmitted`에도 위치별 두 항목이 나옵니다. 기존 첫 위치만 표시하던 응답과 결과가 달라질 수 있으며, 투출 사실은 천간의 실·허 판정과 구분합니다.

`details[기둥].stem.score/status/root_info`는 현재 **동주 지지 기준**입니다. `same_pillar_root_exists`는 동주 통근 유무이며, `score`는 위치 가중치를 곱하지 않은 동주 계수입니다. 양의 점수는 크기에 관계없이 실이며, `0`은 허투입니다. 다른 세 지지의 기존 가중 지원은 `external_support_score/external_support_info`로 별도 표시됩니다. 동주 뿌리가 없으면 타주 지원이 있어도 허투입니다. 통근 점수를 입력으로 사용하는 `advanced_analysis.five_elements.scores`도 이전 전주 합산 방식과 값이 달라질 수 있습니다.

`analysis.summary.total_energy_balance`는 동주 통근/무근 개수만 알리고 원국 전체 신강·신약은 미판정으로 표시합니다. 동주 통근이 여러 천간에 있다는 사실만으로 전체 세력을 단정하지 않습니다.

현행 허실은 관계로 뿌리를 자동 제외하거나 변허로 바꾸지 않습니다. 관련 관계는 별도로 기록하고 실제 통근 영향은 미평가로 제공합니다.

---

## 🧠 `advanced_analysis` (AI 상담 특화 고급 명리 분석)

오행 분포, 등록 신살, 관계, 통근과 빈주 연결을 제공합니다. 관계 탐지·성립·실제 영향을 구분하고 기존 잠정 수치는 계산 의미를 명시합니다.

`branch_dynamics`는 지지 간 작용 분석의 초기 결과입니다. `branch_strengths`는 월령·지장간·동주 천간·다른 지지의 배경 효과를 분리해 네 지지의 상대 세력을 보여줍니다. `pairwise`는 여섯 지지 쌍의 합·충·형·파·천과 오행 생·극을 보존하고, 관계마다 양쪽 잠재 작용량(`force`), 받는 효과(`effect_received`), 관계 전 세력 우세(`dominance`), 해당 관계의 작용량 우세(`force_dominance`), 작용 종류에 따른 양쪽 역할(`roles`)을 제공합니다. `groups`에는 삼합·방합 참여 위치를 담되 아직 작용량은 매기지 않습니다. 이 수치는 검증된 절대 세력이나 현실 피해량이 아닌 `uncalibrated_relative_model_index`이며, 계산 규칙은 [지지 작용 분석 명세](docs/branch_dynamics_v2.md)에 있습니다. 기존 `bin_zhu_dynamics`는 호환을 위해 제공되며 새 지지 작용 계산의 근거로 쓰지 않습니다.

`branch_dynamics.groups[]`의 `candidate_element`는 삼합·방합의 후보 오행이고, `transformed_element`는 실제 합화 판정 전에는 `null`입니다. 기존 `element`는 호환을 위한 후보 오행 별칭입니다.

삼합·방합의 `formation_evidence[]`에는 성립 조합별 참여 지지의 관계 전 세력(`power_before`), 상대 비중(`capacity_share`), 구조적 자리, 겹치는 실제 지지 쌍 관계의 참조가 들어갑니다. 비중은 참여 지지 간 비교값이며 실제 합 작용량이나 세력 증가분은 아닙니다. 그룹의 `status`는 작용 계수를 확정하기 전까지 `not_scored`입니다.

삼합의 `directional_candidates`는 중신을 향한 구조상 방향 후보입니다. 방합은 개별 방향을 `undetermined`로 표시합니다. 두 경우 모두 세력 비중만으로 실제 견인 방향·합화 성립을 확정하지 않습니다. 조합별 후보와 중첩 처리는 [관계 규칙표](docs/mangpa_relation_rulebook.md)에 설명합니다.

`branch_strengths[].ambient_evidence`와 `pairwise[].context_evidence`에는 주변 지지의 생·극 보정과 같은 쌍의 합·충·형 등 관계 상태를 별도 근거로 기록합니다. 생·극 규칙에 명시된 억제는 보정량 0으로 반영합니다. 합이 조건부라는 이유만으로 별개의 생·극 보정을 자동 제거하지 않습니다.

합·충·형·파·천, 천간 관계, 동주 자합 후보와 실험적 작용 계수의 실행 규칙은 [단일 관계 규칙 모듈](services/relation_rules.py)에서 관리합니다. 맹파 해석상의 성립 조건과 검토 상태는 [관계 규칙표](docs/mangpa_relation_rulebook.md)에 기록합니다.

조합별 작용 규칙은 현재 子午·子卯·卯午·午酉·辰酉부터 적용됩니다. `pairwise[].relations[]`의 `directional_coefficients`, `directional_mechanisms`, `activation_status`로 후보의 방향과 상태를 확인할 수 있습니다. 파·충·천·쌍별 지세형은 해당 두 지지가 있으면 거리와 무관하게 `active`이며, 육합은 주변 충 유무와 무관하게 존재 정보 `detected`입니다. 성립한 다른 구조의 규칙에 따른 생·극 억제는 유지하지만 육합의 존재만으로 자동 억제하지 않습니다. `active`는 관계 성립 상태이고 `force`와 v3 `interaction_intensity`는 미보정 잠재 강도입니다. 실제 세력 증감인 `applied_power_delta`는 아직 계산하지 않습니다.

### 구성 요소:

#### 1. `five_elements` (대표 오행 분포와 잠정 지표)
- `counts`: 목/화/토/금/수 글자 수 카운트 (`{"목": 2, "화": 1, "토": 2, "금": 1, "수": 2}`)
- `percentages`: 오행별 백분율 (%)
- `scores`: 기존 동주 통근·지지 위치 가중치의 잠정 지표. 실제 세력 비율이 아님.
- `frequent_elements`: 대표 오행 3글자 이상 목록.
- `absent_elements`: 대표 오행 0개 목록. 지장간 부재·보완 필요성의 판정이 아님.
- `summary`: 대표 오행별 글자 수 설명.

기존 `dominant`·`deficient`는 제거했습니다. 개수·백분율·잠정 점수의 계산값은 유지했습니다.

#### 2. `special_stars` (등록 신살과 탐지 근거)

등록한 천을·문창·도화·역마·화개·양인·홍염·백호·괴강 조합을 위치별로 탐지합니다.

| 신살 | 검사 기준 |
| --- | --- |
| 천을 | 일간·년간 각각 |
| 도화·역마·화개 | 일지·년지 각각 |
| 문창·양인·홍염 | 일간 |
| 백호·괴강 | 해당 기둥의 간지 |

- `name`, `pillar`, `position`, `char`, `type`: 신살 이름과 실제 대상 위치·글자·기존 분류.
- `rule_id`: 적용한 등록 규칙 ID.
- `basis[]`: 탐지 기준의 `pillar`, `kind`(`stem`, `branch`, `pillar`), `char`, `display_name`.
- `interpretation_scope: traditional_symbolism`: 설명은 전통적 상징.
- `description`: 능력·성과·사건을 확정하지 않는 상징 설명.

같은 신살·같은 대상 위치는 한 항목으로 묶고, 일간/년간 또는 일지/년지 양쪽에
해당하면 두 기준을 모두 `basis`에 담습니다. 반복 글자는 위치별로 구분합니다.
일지 값이 항상 우선하던 오류를 수정해 년지 기준 항목이 추가될 수 있습니다.
신살의 이름 목록은 원국표·위치별 맵에도 같은 결과로 전달합니다.
[현행 표시·탐지·타입 계약](docs/root_display_contract.md)을 참고하세요.

#### 3. `interactions` (위치별 관계 매트릭스)

년·월·일·시의 여섯 위치 쌍과 다자 관계를 제공합니다. 버전은 `2.0.0`입니다.
관계 총계와 기후 분류를 제거했고, 개별 관계 점수·중복 집계 필드도 반환하지 않습니다.

- `rule_version`: 관계 매트릭스 응답 계약 버전.
- `summary_list`: 관계별 요약 목록.
- `matrix`: 위치별 관계와 관찰 근거.

| 필드 | 의미 |
| --- | --- |
| `relation_id` | 종류·이름·참여 위치로 결정되는 식별자 |
| `relation_scope` | 쌍 관계 `pairwise`, 삼합·방합·삼형 `group` |
| `participants` | 실제 참여 기둥을 년·월·일·시 순서로 나열 |
| `formations` | 다자 관계를 구성하는 실제 세 위치 조합. 쌍은 `[]` |
| `activation_status` | 관계별 상태. 육합·삼합은 항상 `detected` |
| `status_reasons`, `condition_evidence` | 관찰 코드와 글자·십성이 포함된 근거 |
| `weight`, `is_adjacent` | 기존 거리 가중치와 인접 여부. 관계 점수나 성립 확률이 아님 |
| `candidate_element` | 관습적 오행 후보. 합화 판정이 아님 |
| `transformed_element` | 실제 합화 오행. 현재 `null` |

지지 `亥卯未亥`의 삼합은 참여 위치 네 개와 실제 세 위치 조합 두 개를 함께 반환합니다.

```json
{
  "relation_scope": "group",
  "from_pillar": "all",
  "to_pillar": "all",
  "participants": ["year", "month", "day", "hour"],
  "formations": [["year", "month", "day"], ["month", "day", "hour"]],
  "activation_status": "detected"
}
```

다자 관계 안에 포함된 쌍도 별도 사실로 남습니다. 예를 들어 `巳午未寅`은 巳午未 방합,
午未 육합, 寅午 반합을 함께 제공합니다. 점수로 중복 기여를 제거하지 않습니다.
반복 글자도 위치별로 구분하므로 `子丑丑子`의 육합 네 쌍을 모두 반환합니다.

`stem.relations`·`branch.relations`는 관계가 없으면 `[]`이며 천간 극은
`restrain_to`·`restrain_me` 배열을 항상 포함합니다. 기존 원자료 `strength`는
거리 가중치·구조 계수·잠정 지표로 나눴습니다.
[원자료 계약](docs/raw_character_relations_contract.md)과
[관계 점수 제거 계약](docs/relation_score_retirement.md)을 참고하세요.

#### 4. `xu_shi_dynamics` (동주 통근과 관계 기록)

현행 규칙은 `4.0.0`, 범위는 `same_pillar_only`입니다. 동주 통근 계수가 양수이면 실, 0이면 허투입니다. 타주 지원은 별도 정보이며 통근 점수에 더하지 않습니다.

- `pillars[기둥].root_evidence`: 동주 통근 근거
- `related_interactions`: 통근 유무와 별개로 그 지지가 참여하는 관계와 원본 상태
- `root_impact_status: not_evaluated`, `root_impact_score: null`: 통근 영향 미평가
- `effective_score`: 호환용으로 원점수를 유지하며 검증된 무손상 점수가 아님
- `current_status == original_status`, `is_transformed=false`: 관계로 자동 변허 전환하지 않음
- `impact_groups`, `excluded_root_pillars`: 현행에서는 비어 있으며 영향 없음의 확정값이 아님

[현행 통근·관계 계약](docs/root_relation_separation.md)을 참고하세요. 전주 v1은 명시적 회귀 옵션으로만 유지합니다. [이전 README의 수치·상태 전이 사례](docs/archive/strength-research/xu_shi_legacy_reference.md)는 보관 자료입니다.

#### 5. `bin_zhu_dynamics` (빈·주 사이의 관계 조회)

빈(년·월)과 주(일·시)를 잇는 실제 관계와 참여 글자·십성을 제공합니다.
버전 `4.0.0`, `interaction_scope: cross_domain_relations`입니다.

- `guest_structure`, `host_structure`: 각 영역의 위치·글자·십성 표시 정보.
- `guest_host_links`: 빈·주 사이 쌍 관계의 `relation_id`, 원본 `type`,
  `participants`, `activation_status`, `guest`, `host`, `distance`, `is_adjacent`, `detail`.
  `guest`·`host`는 `pillar`, `char`, `ten_god`, `display_name`을 가집니다.
- `group_connections`: 삼합·방합·삼형의 실제 `participants`, `formations`,
  빈/주 참여 위치와 원본 상태. 관계 ID로 매트릭스와 연결합니다.
- `excluded_interactions`: 참여 위치나 분류가 유효하지 않아 연결할 수 없는 입력.
  파·공합·암합과 `candidate_only` 관계는 원본 상태로 연결 목록에 포함합니다.

빈·주 내부의 쌍은 이 연결 목록에서 생략하며 전체 `interactions.matrix`에는 남습니다.
빈주 점수·결속도·전체 우세·취용 방향·성과 판정은 제거했습니다.
십성은 참여 글자의 정보로 제공하며 합·충만으로 자원 취용이나 환경 압박을 확정하지 않습니다.

#### 6. `ai_consultation_prompts` (AI 즉시 주입용 상담 스크립트)
LLM 시스템 프롬프트 또는 RAG 컨텍스트에 그대로 주입할 수 있는 핵심 요약 불릿 리스트를 한국어로 생성하여 반환합니다.

```json
"ai_consultation_prompts": [
  "【오행 분포】 원국 8글자의 대표 오행 분포는 목 2개, 화 1개, 토 2개, 금 1개, 수 2개입니다. 비율은 글자 수 기준이며 실제 세력의 비율이 아닙니다.",
  "【주요 신살 및 길신】 천을귀인(월지), 역마살(월지), 천을귀인(일지)",
  "【원국 허실】 동주 통근 기준 실(實) 1개, 허투(虛透) 3개입니다. 합·충·형·파·천 등 관련 관계를 별도로 기록했습니다. 관계에 의한 통근 약화·소멸은 미평가이며 변허를 자동 판정하지 않습니다. 원국 동주 통근과 관련 관계를 구분한 조회이며, 관계 적용 후 통근 변화는 계산하지 않았습니다. 대운·세운에 따른 시기별 변화가 아닙니다. 십성의 상징 해석은 참고로 구분하고, 능력·성과·직업 적합성으로 단정하지 마세요."
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
