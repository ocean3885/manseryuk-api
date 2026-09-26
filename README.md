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

### 2. `four_pillars` (사주 4주 원국)
년주(`year`), 월주(`month`), 일주(`day`), 시주(`hour`)로 구성되며 각 기둥은 한글(`kr`)과 한자(`ch`)를 포함합니다.
```json
{
  "year": { "gan": { "kr": "을", "ch": "乙" }, "ji": { "kr": "해", "ch": "亥" } },
  "month": { "gan": { "kr": "신", "ch": "辛" }, "ji": { "kr": "사", "ch": "巳" } },
  "day": { "gan": { "kr": "계", "ch": "癸" }, "ji": { "kr": "유", "ch": "酉" } },
  "hour": { "gan": { "kr": "기", "ch": "己" }, "ji": { "kr": "미", "ch": "未" } }
}
```

### 3. `ten_gods` (십신/십이운성 정보)
원국 8글자 각각의 십신(비견, 겁재, 식신, 상관, 편재, 정재, 편관, 정관, 편인, 정인) 및 일간(`day_gan`: "일간")을 제공합니다.
- `year_gan`, `year_ji`, `month_gan`, `month_ji`, `day_gan`, `day_ji`, `time_gan`, `time_ji`

### 4. `daewoon` (대운 정보)
10년 주기의 대운 흐름을 제공합니다.
- `direction`: 대운 순행/역행 여부 (`"순행"` 또는 `"역행"`)
- `start_age`: 대운 시작 나이 (대운수, 예: `2.3`)
- `current`: 현재 나이에 해당하는 대운 객체
  - `index`, `year`, `age`, `gan`, `ji`, `gan_ten_god` (천간 십신), `ji_ten_god` (지지 십신), `unseong` (12운성), `start_age`, `end_age`, `start_year`, `end_year`
- `list`: 10개 대운 항목 전체 배열

### 5. `cycles` (세운 및 소운)
- `future_100`: 향후 100년간의 세운 데이터 리스트
- `baby_10`: 1세부터 10세까지의 소운 리스트

### 6. `meta` (메타 정보)
- `gender`: 성별 (`남` / `여`)
- `ddi`: 십이지 띠 (예: `돼지띠`)

### 7. `analysis` (전통 명리 분석 요약)
- `summary`: 천간/지지 상호작용 및 오행 균형 요약 문장 리스트
- `details`: 신살, 형충회합 등의 세부 데이터

---

## 🧠 `advanced_analysis` (AI 상담 특화 고급 명리 분석)

AI 챗봇/상담 에이전트가 풍부한 해석 프롬프트와 정밀한 명리학적 근거를 바탕으로 사주를 풀이할 수 있도록 맹파명리 및 고급 역학 엔진을 통합 제공합니다.

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

#### 3. `interactions` (합·충·형·해·파 6기둥 페어 매트릭스)
년-월, 월-일, 일-시, 년-일, 년-시, 월-시 총 6개 기둥 간의 인접성 가중치 및 상호작용 분석:
- `climate`: 사주 기후 (`조화 안정형`, `역동 발전형`, `긴장 극복형`, `복합형`)
- `tension_score`: 충/형/파/해로 인한 긴장·변동 지수
- `harmony_score`: 육합/삼합/방합으로 인한 결속·안정 지수
- `matrix`: 각 상호작용 항목의 세부 정보 (가중치, 합화 오행, 설명)

#### 4. `xu_shi_dynamics` (허와 실 및 실자변허 實者變虛)
맹파명리의 핵심 이론인 원국의 실(實)과 허(虛), 충·해에 의한 상태 전이(실자변허), 천간 허투(虛透) 분석:
- `pillars`: 각 기둥 글자별 실/허 상태 및 십신 해석 (`original_status`, `current_status`, `is_transformed`, `reason`, `meaning`)
- `real_count`: 실(實) 상태 글자 수
- `transformed_empty_count`: 충·해로 변허된 글자 수
- `overall_status`: 현실적 자산 기반 vs 지식/아이디어/유동성 기반의 라이프스타일 가이드

#### 5. `bin_zhu_dynamics` (빈주 이론 賓主理論)
사회적 환경(년/월: 賓)과 개인/내면(일/시: 主) 간의 에너지 흐름 및 제어/획득 방식 분석:
- `guest_structure`: 빈(외계/사회)의 주요 세력 및 십신
- `host_structure`: 주(자아/가정)의 주요 수단 및 십신
- `control_flow`:
  - `direction`: 관계 유형 (`주가 빈을 제압/획득`, `빈이 주를 통제`, `주-빈 균형 교류형`)
  - `summary_meaning`: 사회적 관계 및 성과 달성 메커니즘
  - `career_advice`: 적합한 직업군 및 비즈니스 모델 권장사항

#### 6. `ai_consultation_prompts` (AI 즉시 주입용 상담 스크립트)
LLM 시스템 프롬프트 또는 RAG 컨텍스트에 그대로 주입할 수 있는 핵심 요약 불릿 리스트를 한국어로 생성하여 반환합니다.

```json
"ai_consultation_prompts": [
  "【오행 분포】 목화토금수 5개 오행이 사주에 골고루 갖추어진 원만한 오행구족(五行具足) 구조입니다.",
  "【주요 신살 및 길신】 천을귀인(월지), 역마살(월지), 천을귀인(일지)",
  "【사주 기후】 긴장과 조화가 공존하는 복합형 (긴장도: 3.5, 조화도: 3.0)",
  "【허실 변화】 충·해로 인해 1개 글자가 실자변허(實者變虛) 상태로 전이되어, 실물 고정 자산보다 유동적/지식 기반 대처가 유리합니다.",
  "【빈주 이론】 주-빈 균형 교류형: 개인의 자율성과 사회적 네트워크가 상호 보완적으로 작동하는 구조입니다.",
  "【진로/재물 권장】 파트너십, 협업, 유연한 프리랜서/조직 겸업 형태에서 최적의 시너지를 낼 수 있습니다.",
  "【주요 상호작용】 년지(亥)-월지(巳) 육충: 기반 변동 및 마찰",
  "【주요 상호작용】 지지 삼합(木): 강력한 국(局) 형성"
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
