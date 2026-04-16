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

