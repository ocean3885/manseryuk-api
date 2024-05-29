from sqlalchemy import Column, Integer, String
from database import Base

class CalendaData(Base):
    __tablename__ = "calenda_data"
    
    cd_no = Column(Integer, primary_key=True, index=True)
    cd_sy = Column(Integer, primary_key=True, index=True)
    cd_sm = Column(String, primary_key=True, index=True)
    cd_sd = Column(String, primary_key=True, index=True)
    cd_ly = Column(Integer)
    cd_lm = Column(String)
    cd_ld = Column(String)
    cd_hyganjee = Column(String)
    cd_kyganjee = Column(String)
    cd_hmganjee = Column(String)
    cd_kmganjee = Column(String)
    cd_hdganjee = Column(String)
    cd_kdganjee = Column(String)
    cd_hweek = Column(String)
    cd_kweek = Column(String, nullable=True)  # nullable 설정
    cd_stars = Column(String, nullable=True)
    cd_moon_state = Column(String, nullable=True)
    cd_moon_time = Column(String, nullable=True)
    cd_leap_month = Column(String, nullable=True)
    cd_month_size = Column(String, nullable=True)
    cd_hterms = Column(String, nullable=True)
    cd_kterms = Column(String, nullable=True)
    cd_terms_time = Column(String, nullable=True)
    cd_keventday = Column(String, nullable=True)
    cd_ddi = Column(String, nullable=True)
    cd_sol_plan = Column(String, nullable=True)
    cd_lun_plan = Column(String, nullable=True)
    holiday = Column(String, nullable=True)  # nullable 설정
