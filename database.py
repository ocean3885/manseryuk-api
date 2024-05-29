# database.py
from sqlalchemy import create_engine, Column, Integer, String, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./manseryuk.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the table structure assuming it matches the existing database
class CalendaData(Base):
    __tablename__ = 'calenda_data'

    cd_no = Column(Integer, primary_key=True, index=True)
    cd_sgi = Column(Integer)
    cd_sy = Column(Integer)
    cd_sm = Column(String)
    cd_sd = Column(String)
    cd_ly = Column(Integer)
    cd_lm = Column(String)
    cd_ld = Column(String)
    cd_hyganjee = Column(String, nullable=True)
    cd_kyganjee = Column(String, nullable=True)
    cd_hmganjee = Column(String, nullable=True)
    cd_kmganjee = Column(String, nullable=True)
    cd_hdganjee = Column(String, nullable=True)
    cd_kdganjee = Column(String, nullable=True)
    cd_hweek = Column(String, nullable=True)
    cd_kweek = Column(String, nullable=True)
    cd_stars = Column(String, nullable=True)
    cd_moon_state = Column(String, nullable=True)
    cd_moon_time = Column(String, nullable=True)
    cd_leap_month = Column(Integer, nullable=True)
    cd_month_size = Column(Integer, nullable=True)
    cd_hterms = Column(String, nullable=True)
    cd_kterms = Column(String, nullable=True)
    cd_terms_time = Column(String, nullable=True)
    cd_keventday = Column(String, nullable=True)
    cd_ddi = Column(String)
    cd_sol_plan = Column(String, nullable=True)
    cd_lun_plan = Column(String, nullable=True)
    holiday = Column(Integer)
