from pydantic import BaseModel
from typing import Optional

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
        orm_mode = True

from typing import List, Any

class SajuAnalysisResponse(BaseModel):
    s_year: int
    s_month: str
    s_day: str
    l_year: int
    l_month: str
    l_day: str
    year_gan_ch: str
    year_ji_ch: str
    year_gan_kr: str
    year_ji_kr: str
    month_gan_ch: str
    month_ji_ch: str
    month_gan_kr: str
    month_ji_kr: str
    day_gan_ch: str
    day_ji_ch: str
    day_gan_kr: str
    day_ji_kr: str
    ddi_kor: Optional[str] = None
    sol_plan: Optional[str] = None
    lunar_plan: Optional[str] = None
    time_ji_kr: str
    time_gan_kr: str
    time_gan_ch: str
    time_ji_ch: str
    gender: str
    daewoon: List[Any]
    daewoon_num: float
    daewoon_num_list: List[float]
    time_gan10: str
    month_gan10: str
    year_gan10: str
    time_ji10: str
    day_ji10: str
    month_ji10: str
    year_ji10: str
    cycles_100: List[Any]
    baby_10: List[Any]
