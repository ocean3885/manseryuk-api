from pydantic import BaseModel
from typing import Optional, List, Any


# ──────────────────────────────────────────
# 기존 CalendaData ORM 응답용 스키마 (유지)
# ──────────────────────────────────────────
class CalendaDataResponse(BaseModel):
    cd_sy: int
    cd_sm: str
    cd_sd: str
    cd_ly: int
    cd_lm: str
    cd_ld: str
    cd_hyganjee: str
    cd_kyganjee: str
    cd_hmganjee: str
    cd_kmganjee: str
    cd_hdganjee: str
    cd_kdganjee: str
    cd_hweek: str
    cd_kweek: Optional[str] = None
    cd_stars: Optional[str] = None
    cd_moon_state: Optional[str] = None
    cd_moon_time: Optional[str] = None
    cd_leap_month: Optional[int] = None
    cd_month_size: Optional[int] = None
    cd_hterms: Optional[str] = None
    cd_kterms: Optional[str] = None
    cd_terms_time: Optional[str] = None
    cd_keventday: Optional[str] = None
    cd_ddi: Optional[str] = None
    cd_sol_plan: Optional[str] = None
    cd_lun_plan: Optional[str] = None
    cd_holiday: Optional[str] = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────
# 사주 분석 응답용 중첩 스키마 (신규)
# ──────────────────────────────────────────

class GanJi(BaseModel):
    """천간(干)과 지지(支)를 한글/한자 쌍으로 표현"""
    gan: dict  # {"kr": "갑", "ch": "甲"}
    ji: dict   # {"kr": "자", "ch": "子"}


class FourPillars(BaseModel):
    """사주 4주 (년주/월주/일주/시주)"""
    year: GanJi
    month: GanJi
    day: GanJi
    time: GanJi


class TenGods(BaseModel):
    """십신 (천간 + 지지)"""
    year_gan: str
    year_ji: str
    month_gan: str
    month_ji: str
    day_ji: str
    time_gan: str
    time_ji: str


class SolarDate(BaseModel):
    """양력 날짜"""
    year: int
    month: str
    day: str


class LunarDate(BaseModel):
    """음력 날짜"""
    year: int
    month: str
    day: str


class CalendarInfo(BaseModel):
    """달력 정보 (양력 / 음력 / 절기 메모)"""
    solar: SolarDate
    lunar: LunarDate
    solar_plan: Optional[str] = None
    lunar_plan: Optional[str] = None


class DaewoonInfo(BaseModel):
    """대운 정보"""
    direction: List[Any]   # 순행/역행 정보 (기존 daewoon 리스트)
    start_age: float        # 대운 시작 나이
    age_list: List[float]   # [5, 15, 25, ...]


class CyclesInfo(BaseModel):
    """운세 사이클"""
    future_100: List[Any]  # 100년 운세
    baby_10: List[Any]     # 소운 10년


class MetaInfo(BaseModel):
    """기타 기본 정보"""
    gender: str
    ddi: Optional[str] = None  # 띠


class SajuAnalysisResponse(BaseModel):
    """사주 분석 최종 응답 (도메인별 그룹화)"""
    calendar: CalendarInfo
    four_pillars: FourPillars
    ten_gods: TenGods
    daewoon: DaewoonInfo
    cycles: CyclesInfo
    meta: MetaInfo
